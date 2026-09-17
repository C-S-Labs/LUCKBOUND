# LUCKBOUND — Testing Guide

Two layers: automated tests that run headlessly with no Roblox, and a manual
Studio pass for what only a running game can tell you.

---

## 1. Automated tests

**208 tests. No Roblox required.** They run against the real `src/` modules,
not copies.

```bash
# one-time: get the Luau CLI from https://github.com/luau-lang/luau/releases
./tests/run.sh
```

Expected tail:

```
============================================================
208 passed, 0 failed, 208 total
```

CI runs them on every push, plus a syntax check and the forbidden-module-name
scan (`*_Final`, `*_NEW`, `*_FIXED`, …) from build spec P1-12.

### Coverage

| Group | Tests | The question it answers |
|---|---|---|
| Schema validation | 8 | Does the server refuse to boot on broken content? |
| Scripted onboarding | 17 | Is the 15-roll arc exact, and does it never hand out a Mythic? |
| **True RNG** | 16 | **Is the roll genuinely unweighted by player state?** |
| WeightedRandom | 6 | Zero weights, boundaries, single entry |
| Fate progression | 11 | Is the level curve monotonic and invertible? |
| Profile & migration | 10 | Does data survive, migrate, stay in DataStore limits? |
| **Late-joiner visibility** | 17 | **Does someone joining mid-event see the right thing?** |
| Hub layout & scale | 43 | Blueprint dimensions, compass anchors, the traversal budget |
| PortalRig & rarity | 25 | Rig spec, 2.5 s spin-up, rarity-vs-biome colour contract |
| Biome lighting | 15 | Per-world Brightness/Fog per Blueprint §3.3/§4.3/§5.3 |
| Constants | 12 | Frozen, unique orders, sane reveal durations |
| **Map assembly** | 33 | **Does a map actually build from the chunk pieces?** |
| **Ethereal Scape** | 23 | **Does the grammar work on a second, independent kit?** |
| **Expedition entry** | 40 | **Who may enter, where do they go, can it be replayed?** |

**276 total.**

### The three that matter most

**True RNG is proven, not asserted.** 400,000 draws:

```
VERDANT_VALLEY  expected 60.00%  observed 59.96%  drift 0.037pp
ETHEREAL_SCAPE  expected 15.00%  observed 15.02%  drift 0.016pp
EMBERFALL       expected 15.00%  observed 15.06%  drift 0.062pp
SKY_CITADEL     expected  7.00%  observed  6.95%  drift 0.047pp
ASTRAL_REACH    expected  3.00%  observed  3.01%  drift 0.006pp
```

And the guarantee itself: a level-90 veteran and a level-1 newcomer fed the same
random stream produce **identical results across 50,000 rolls**. If anyone adds a
Fate term to the weighting, that test goes red immediately.

**Onboarding never hands out a Mythic.** A guaranteed top tier would devalue it
permanently and break the Fatebreak announcement that depends on it. The arc
also has to approximate real odds — tests enforce that the scripted Common rate
stays within 12pp of the true rate and that no run of Commons exceeds three, so
roll 16 is not a cliff.

**Late joiners.** A player joining 4 minutes into a 5-minute Fatebreak gets
`RemainingSeconds = 60`, the triggering player's name, and elapsed time for
animation sync. Expired events vanish; stale announcements age out at 5 minutes.

### A caution about the harness

The headless harness shims Roblox types. **An unfaithful shim can pass a test
against code that cannot boot** — this happened: `Vector3` was shimmed as a
plain table, so a `type()`-vs-`typeof()` bug passed 152 tests and still failed
in Studio.

The harness now provides a `typeof()` that distinguishes `Vector3`, `Color3` and
`UDim` the way the engine does. **When adding a shim, make it behave like the
real type, not merely enough to pass.**

Nothing that touches `DataStoreService`, `MessagingService`, `Players` or
`Workspace` is unit-tested. Those are verified in Studio, below.

**This is why `ExpeditionCore` exists.** Entry eligibility, seed derivation,
destination lookup and the timer are all pure, so the 40 tests above run
headlessly — while `ExpeditionSystem`'s teleports, geometry and remotes are
only ever proven by Test C2 in Studio. If you are about to put a decision in
`ExpeditionSystem`, put it in `ExpeditionCore` instead.

---

## 2. Sync to Studio with Rojo

```bash
# once
rokit install          # rojo 7.6.0, stylua, selene from rokit.toml
rojo plugin install    # skip if the Studio plugin is already installed

# every session
rojo serve
```

In Studio: open the place → **Rojo** panel → **Connect** → **Accept** the sync
preview (Rojo 7.7+ asks before touching the place).

You should see `ReplicatedStorage.Luckbound`,
`ServerScriptService.LuckboundServer` (a **Script**, not a Folder — the icon
matters) and `StarterPlayer.StarterPlayerScripts.LuckboundClient`.

---

## 2.5 Developer commands

On for the current testing phase (`GameConfig.Debug.AllowCommands`). They need
the **modern chat** — if `TextChatService.ChatVersion` is `LegacyChatService`
the Output window says so on join and nothing registers.

Replies print to **Output**, prefixed `[cmd]`, not to the chat window: that is
where the `[Roll]` and `[Expedition]` lines already are.

| Command | Side | What it does |
|---|---|---|
| `/fly` | client | Toggle. WASD relative to camera, Space up, Shift down, 120 studs/s. Cancels on respawn. |
| `/speed <n>` | client | Set walk speed, clamped 1–500. No argument prints the current value. |
| `/tp <place>` | client | `engine` `gate` `hall` `archive` `training` `observatory` `spawn`. Arrives 20 studs up and drops, so it cannot land you inside a platform. |
| `/where` | client | Print your position. |
| `/worlds` | client | List rollable world ids with their rarities. |
| `/roll <WORLD_ID>` | **server** | Force your next destination. No argument lists the valid ids. |
| `/enter` | **server** | Enter your destination from anywhere — skips the distance check only. |
| `/leave` | **server** | End the current expedition (counts as RETURNED, so it pays Fate). |
| `/help` | client | List all of the above. |

**Why the split.** Your own character's velocity, speed and CFrame are already
yours — Roblox gives the client network ownership of its own rig — so routing
those through the server would buy nothing. Roll results, expedition entry and
Fate awards are the opposite: the client must not be trusted with any of them,
debug build or not.

### The three gates on the server-side commands

1. `GameConfig.Debug.AllowCommands` — if false, no handler is connected at all.
2. **Studio, or the place's creator.** Checked per command, every time.
3. `/roll` additionally needs `GameConfig.Debug.AllowForcedRolls`.

Gate 2 is the one that matters: a config flag left true by accident should not
by itself hand a stranger the ability to roll themselves a Mythic. **Turn both
flags off before the place goes public anyway** — defence in depth is not a
reason to leave the front door open.

A forced roll is recorded, logged and sent through the real pipeline — that is
the point, it has to exercise the real path to be worth testing with — but it
is **never announced server-wide**, for the same reason a scripted onboarding
roll is not.

---

## 3. Manual Studio pass

### Test A — the server boots (1 min)

Press **Play**. Output should show every step:

```
[LUCKBOUND] boot 1/11: validating content
[LUCKBOUND] assets: 0 uploaded, 17 placeholder (placeholders render as primitives)
[LUCKBOUND] 3 rollable world(s) have no chunk kit and cannot be entered: ASTRAL_REACH, EMBERFALL, SKY_CITADEL
...
[LUCKBOUND] boot 7/11: ExpeditionSystem
[LUCKBOUND] boot 8/11: DebugSystem
[LUCKBOUND] boot 9/11: building the Crossroads
[HubBuilder] built Crossroads: 5 zones, 436 instances
[LUCKBOUND] boot 10/11: binding players
[LUCKBOUND] server ready -- phase 1, true RNG, 15-roll onboarding, expeditions ENABLED
[LUCKBOUND] client ready
```

**The boot numbers are the diagnostic.** If the server stops partway, the last
`boot N/11` names the step that failed or hung. A stall with no error means a
yielding call inside that step, not a crash.

You will also see a loud orange `[DebugSystem] DEVELOPER COMMANDS ARE ON`.
That one is meant to be impossible to miss.

Two of the other lines are **warnings that are meant to be there.** The asset count
says how much of the art is still placeholder; the "no chunk kit" line is the
gap between rollable and enterable, printed every boot so it cannot quietly
grow. Neither is a failure.

On an unpublished place you will also see three orange `SaveSystem` warnings.
**Those are correct** — they report that saving is off, not that anything failed.

### Test B — validation blocks a bad boot (2 min)

Break something deliberately: in `VerdantValley.luau` change `Rarity = "COMMON"`
to `Rarity = "SUPER_RARE"`, save.

✅ Pass: the server **refuses to start** and names the exact field. Revert it.

### Test C — the 15-roll arc (5 min)

Walk to the Fate Engine; the **[E] ROLL** prompt appears within ~12 studs. Roll
16 times, watching the server log:

| Rolls | Expected | |
|---|---|---|
| 1–2 | Verdant Valley | `(onboarding)` |
| 3 | Emberfall | `(onboarding)` |
| 4 | Verdant Valley | `(onboarding)` |
| **5** | **Ethereal Scape (UNCOMMON)** | `(onboarding)` |
| 6 | Emberfall | `(onboarding)` |
| 7 | Verdant Valley | `(onboarding)` |
| **8** | **Sky Citadel (EPIC)** | `(onboarding)` |
| 9–10 | Verdant Valley | `(onboarding)` |
| 11 | Emberfall | `(onboarding)` |
| 12–13 | Verdant Valley | `(onboarding)` |
| 14 | Emberfall | `(onboarding)` |
| 15 | Verdant Valley | `(onboarding)` |
| **16** | **random** | **no tag** |

✅ Pass: exact order, and roll 16 has no `(onboarding)` marker.

Studio's Output collapses identical consecutive lines as `(x2)` — that is not a
bug.

### Test D — the cooldown holds (1 min)

Press **E** repeatedly as fast as you can.

✅ Pass: at most one roll per 3 seconds, and **no error is shown to the client**.
Silence is deliberate — an error tells an exploiter where the boundary is.

### Test C2 — the expedition, end to end ⭐ (6 min)

**Passed 2026-09-16.** Kept as the regression pass — it is the test the whole
§7.1 amendment exists for, and every future change to generation or entry
should be walked through it again. Roll 5 hands you
Ethereal Scape, so you can run it inside the first minute of a fresh profile.

1. **Roll until you hold Ethereal Scape.** It is guaranteed at roll 5, and is
   15% of honest rolls after that. The reveal card names it.
2. **Walk south to the Expedition Gate.** The largest portal in the hub. Or
   `/tp gate` if you are testing something else and do not want the walk.
3. Look at the prompt before pressing anything. It should read
   **ENTER · Ethereal Scape** — that text is set *on your client only*, from
   your last roll, so two players standing at the same gate see different
   destinations. Check that with a second player if you have one.
4. **Hold E.** The server log prints one line with everything needed to rebuild
   the map:

```
[Expedition] Player1 -> ETHEREAL_SCAPE  seed 1443871209  5 chunks (0 mesh, 5 blockout)  attempt 1  300s
```

✅ **Pass conditions, in order of what they tell you:**

| | What it proves |
|---|---|
| You arrive standing on a labelled platform reading `ES_ARRIVAL_SHELF` | the layout built and you are on the ENTRY piece |
| The sky turns bright and near-white | per-client biome lighting applied |
| The banner top-centre counts down from 5:00 | the timer is live |
| The pieces form a connected run, each labelled | generation produced a *place*, not a pile |
| Neon posts of matching colour meet where pieces join | the socket grammar held |
| **The piece before `ES_SKY_TEMPLE` is always `ES_WAYSTONE_RING`** | the reserved-Kind rule is working, on a kit it was not designed against |

5. **Walk the whole map to the temple.** It is 1152–2432 studs depending on
   seed — 40–80 seconds at WalkSpeed 32. Time it. If it feels like a slog, the
   world's `MapPathLength` is the knob, not the walk speed.
6. **Return.** Walk back to the arrival shelf; a small green portal sits a
   quarter of the way back from where you spawned. Hold E. (`/leave` does the
   same thing from anywhere.)

✅ Pass: you are back at the Crossroads spawn, **the hub's dark purple lighting
is exactly as it was**, and you gained +25 Fate.

> Lighting not restoring is the bug to watch for here. If the hub stays bright
> after you return, `ExpeditionController.TRACKED` is missing a property.

7. **Roll Emberfall or Sky Citadel and try the Gate.** (`/roll EMBERFALL`.) ✅ Pass: *"That world has
   no map yet."* and you stay in the hub. Those worlds have no kit — that is the
   honest current state, not a crash.
8. **Fall off the edge.** ✅ Pass: the expedition ends, you respawn at the hub,
   and you gain **no** Fate. Dying is not completing.

#### Determinism, if you want to check it

The seed in that log line is derived from `(userId, TotalRolls, worldId)`, so
re-entering on the same roll count rebuilds the identical map. Two different
players never get the same one.

### Test C3 — the hub is walkable (3 min)

Added after two playtests found geometry that tests could not see. Do this
before anything else after a scale or layout change.

1. **Stand anywhere on the plaza.** It is a disc 1150 studs across. If you are
   on top of a wall or falling, `cylinder()` has regressed.
2. **Walk all four spokes** — Hall (N), Archive (E), Gate (S), Training (W).
   ✅ Pass: no gap between walkway and platform, no step you have to jump.
3. **Stand at the Fate Engine and turn a full circle.** ✅ Pass: nothing
   encircles it and nothing blocks the approach from any of the four spokes.
   The Global Observatory and its ramp were cut on 2026-09-17; if you see a
   staircase wrapping the Engine, the sync did not take.

### Test E — a tampered client is rejected (1 min)

From the **client** console:

```lua
local Net = require(game.ReplicatedStorage.Luckbound.Core.Net)
Net.get("Fate_RequestRoll"):FireServer({ WorldId = "ASTRAL_REACH" })
```

✅ Pass: server logs `sent arguments with Fate_RequestRoll; discarded` and **no
roll happens**. The client cannot choose its destination.

### Test F — data persists (3 min) — **published places only**

DataStores do not work on a local place. To test saving you must publish first,
then enable **Game Settings → Security → Studio Access to API Services**.

Roll a few times, note `TotalRolls`, **Stop**, **Play** again:

```lua
-- server console
local S = require(game.ServerScriptService.LuckboundServer.Systems.SaveSystem)
print(S.get(game.Players:GetPlayers()[1]).TotalRolls)
```

✅ Pass: the count carried over, and onboarding resumed where it left off.

### Test G — late joiners see a live event ⭐ (5 min)

Needs two clients: **Test → Clients and Servers → 2 players → Start**.

1. In the **server** console:

```lua
local E = require(game.ServerScriptService.LuckboundServer.Systems.EventSystem)
E.triggerFatebreak({ Id = "STARFALL_1", Name = "The Eternal Star",
	Rarity = "UNKNOWN", TriggeredBy = "Player1", Duration = 300 })
```

2. Confirm both clients show the banner.
3. Start a **third** player mid-event.
4. Check the snapshot that player receives:

```lua
local EventCore = require(game.ReplicatedStorage.Luckbound.Core.EventCore)
local E = require(game.ServerScriptService.LuckboundServer.Systems.EventSystem)
local GameConfig = require(game.ReplicatedStorage.Luckbound.Core.GameConfig)
print(EventCore.snapshot(E._state(), os.time(), GameConfig))
```

✅ Pass: the event is still active with a **partial** `RemainingSeconds` — not a
fresh 300. After expiry, a joiner must see `ActiveEvents = {}` with no ghost.

> Cross-server Fatebreaks use `MessagingService`, which needs a published place.
> In Studio you will see `cross-server subscribe unavailable` — expected.

### Test H — announcements reach everyone, onboarding does not (2 min)

✅ Pass: a genuine Mythic roll banners on **both** clients.
✅ Pass: a *scripted* onboarding roll produces **no** announcement — otherwise
every new player would spam banners and the signal would mean nothing.

---

## 4. What to report back

The automated suite covers correctness. It cannot answer the only question that
decides the project (Master Spec §25):

**After a rare roll, did you want to roll again?**

Currently worth watching:

- Is the 3-second cooldown invisible, or annoying?
- Does the Epic at roll 8 land as a peak, or pass unnoticed?
- Does roll 16 — the first honest roll — feel like freedom or like a letdown?
- Does the Uncommon at roll 5 read as a lift, or as "still not a Rare"?
- **Is walking through the Gate a payoff, or an anticlimax?** The roll used to
  be the end of the sentence. It now has a destination attached, and whether
  that helps or dilutes it is the thing to watch.
- Is 1200 studs and WalkSpeed 32 right, now that there is somewhere to walk to?
  Both are one line in `GameConfig`.
