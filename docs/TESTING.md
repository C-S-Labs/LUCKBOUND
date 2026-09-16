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
| Schema validation | 10 | Does the server refuse to boot on broken content? |
| Scripted onboarding | 17 | Is the 15-roll arc exact, and does it never hand out a Mythic? |
| **True RNG** | 17 | **Is the roll genuinely unweighted by player state?** |
| WeightedRandom | 6 | Zero weights, boundaries, single entry |
| Fate progression | 11 | Is the level curve monotonic and invertible? |
| Profile & migration | 11 | Does data survive, migrate, stay in DataStore limits? |
| **Late-joiner visibility** | 21 | **Does someone joining mid-event see the right thing?** |
| Hub layout | 21 | Blueprint dimensions, compass anchors, the MeshId seam |
| PortalRig & rarity | 22 | Rig spec, 2.5 s spin-up, rarity-vs-biome colour contract |
| Biome lighting | 11 | Per-world Brightness/Fog per Blueprint §3.3/§4.3/§5.3 |
| Constants | 12 | Frozen, unique orders, sane reveal durations |
| **Map assembly** | 32 | **Does a map actually build from the chunk pieces?** |
| **Scale budget** | 12 | **Is the world big enough, and still walkable?** |

### The three that matter most

**True RNG is proven, not asserted.** 400,000 draws:

```
VERDANT_VALLEY  expected 70.00%  observed 69.91%  drift 0.088pp
EMBERFALL       expected 20.00%  observed 20.11%  drift 0.113pp
SKY_CITADEL     expected  7.00%  observed  6.97%  drift 0.031pp
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

## 3. Manual Studio pass

### Test A — the server boots (1 min)

Press **Play**. Output should show every step:

```
[LUCKBOUND] boot 1/9: validating content
...
[LUCKBOUND] boot 7/9: building the Crossroads
[HubBuilder] built Crossroads: 5 zones, 436 instances
[LUCKBOUND] boot 8/9: binding players
[LUCKBOUND] server ready -- phase 1, true RNG, 15-roll onboarding
[LUCKBOUND] client ready
```

**The boot numbers are the diagnostic.** If the server stops partway, the last
`boot N/9` names the step that failed or hung. A stall with no error means a
yielding call inside that step, not a crash.

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
| 4–5 | Verdant Valley | `(onboarding)` |
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
