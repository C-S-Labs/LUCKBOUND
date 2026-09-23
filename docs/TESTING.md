# LUCKBOUND — Testing Guide

Two layers: automated tests that run headlessly with no Roblox, and a manual
Studio pass for what only a running game can tell you.

---

## 1. Automated tests

**No Roblox required.** `./tests/run.sh` prints the totals — this file
deliberately does not repeat the number, because a count written into prose
drifts the moment anyone adds a test, and it had drifted to four different
values across four documents before anyone noticed. They run against the real `src/` modules,
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
| **Ethereal Scape** | 15 | **Is the prebuilt map's scale honest against the art?** |
| **Expedition entry** | 46 | **Who may enter, where do they go, can it be replayed?** |

**295 total.** Run `./tests/run.sh`; the suite prints the count.

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

### The untested boundary — named, so it cannot be mistaken for covered

**A green suite does NOT mean the Roblox runtime path works.** These modules
are the seam between the pure logic the harness can run and the engine it
cannot, and they carry little or no direct coverage *by design* — a shim
faithful enough to test them would be a reimplementation of Roblox.

| Module | Coverage | What could break without a test noticing | Verified by |
|---|---|---|---|
| `Util/ChunkLoader` | indirect | A piece placed at the wrong height or rotation; a mesh stretched by a wrong `SizeY`; scenario attributes missing | Studio walk — **E** below |
| `Util/PrebuiltLoader` | none | A scene cloned unanchored, at the wrong scale, or without its anchors | Studio walk — **D** |
| `Util/PrefabLoader` | partial | A prefab registered from the wrong part; a lost `CollisionFidelity` bake | Studio walk — **B** |
| `Util/PortalRig` | partial | A portal plane above head height, or a collision hull that blocks the walk-through | Studio walk — **B** |
| `Core/Net` | none | A remote missing, misnamed, or created twice | Boot — the server errors on a missing remote |
| `Core/Result` | none | Nothing realistic — it is eight lines with no branches | — |

**What CAN be pulled back across the line, and has been:** every decision
these modules act on is computed by a pure module that *is* tested.
`ChunkCore` decides placement, `ScenarioCore` decides what happens in a room,
`ExpeditionCore` decides timing and slots. `ChunkLoader` only turns those
numbers into Instances. That split is deliberate: it is what keeps the
untestable surface thin.

**What cannot:** whether the Instances that come out look and behave right.
There is no substitute for the Studio pass, and a change to any module above
should not be called done until it has had one.

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

### Test C2b — entering from the Fate Engine ⭐ NEW (3 min)

The portal is enterable from the dais while its staircase is unmodelled, so
the teleport and the biome scripts can be tested now.

1. **Walk onto the dais.** ✅ Pass: **two** prompts — `[E] ROLL` and
   `[F] ENTER`, stacked, both reachable, neither fighting the other for E.
2. **Roll first**, so you have a destination. `/roll VERDANT_VALLEY` or
   `ETHEREAL_SCAPE` if you want a specific one.
3. **Hold F.** ✅ Pass: you are teleported into the biome, its lighting
   applies, and the expedition banner and timer appear.
4. **Return through the portal on the arrival chunk**, or `/leave`. ✅ Pass:
   the hub's own lighting comes back exactly, Fate is awarded, and the menu
   reappears.
5. **Roll a world with no map** (Emberfall, Sky Citadel, Astral Reach) and
   press F. ✅ Pass: refused politely, and you stay in the hub.

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
[Expedition] Player1 -> ETHEREAL_SCAPE  seed 1443871209  prebuilt ES_ENVIRONMENT_FULL  925 parts at 1.00 scale  derived arrival  300s
```

That line says which route built the map. A kitted world prints
`5 chunks (0 mesh, 5 blockout) attempt 1` instead — same slot, different
summary. `derived arrival` means the scene has no `EntryAnchor` yet and the
loader guessed; it will read `authored` once one is added.

✅ **Pass conditions, in order of what they tell you:**

| | What it proves |
|---|---|
| You arrive standing on the authored islands, not a grey blockout platform | the prebuilt map cloned out of `ServerStorage.LuckboundMaps` |
| A character reaches a doorway's handle-height, not its skirting | `PrebuiltMap.Scale` is right. v1 shipped ~10× oversized and `0.1` then read too small; v2 is authored at play scale and runs at `1.0` |
| Nothing falls | the scene is anchored (v2 ships that way; the loader also anchors on clone) |
| The walk to the temple takes about 70 seconds | the traverse budget. If it drags, `DurationSeconds` is the knob — not `Scale`, which would shrink the art |
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

### Test H2 — the half-size world (4 min) ⭐ NEW

The biggest unverified change in the project. `HubLayout.WorldScale` is 0.5;
setting it to 1.0 restores the old world exactly, so this is cheap to A/B.

1. **Stand at a shop counter.** ✅ Pass: your head and the top of your torso
   clear it. That was the whole point — it used to stand a stud over your head.
2. **Stand at a district railing.** ✅ Pass: it is about waist height.
3. **Walk the Engine → a district.** ✅ Pass: about 8 seconds at WalkSpeed 24.
   If it feels like a jog rather than a walk, `Scale.WalkSpeed` is the dial.
4. **Look at the horizon.** ✅ Pass: the mountains still ring the hub with
   clear sky between, and do not cut through the plaza.
5. **Walk all four walkways to the dais.** ✅ Pass: they still MEET the dais —
   no step up, no gap. This is the coupling four tests pin; a failure here
   means the authored mesh and the layout numbers have come apart.

### Test I — the loading screen (3 min) ⭐ NEW

The first thing anyone sees.

1. **Press Play in Studio.** ✅ Pass: a blurred camera arc over the Crossroads
   behind the LUCKBOUND title, a caption naming the district on screen, and a
   progress bar that moves.
2. **Watch the camera.** ✅ Pass: it arcs steadily the whole time. If it stops
   partway, Roblox's camera script has taken it back and the per-frame
   re-assert has regressed.
3. **Watch the PLAY button** — the only button on the screen. ✅ Pass: the bar
   reaches 100% and it lights gold. It must never light instantly
   (`MinimumSeconds` is 3.5s) and, now that readiness is a settle rather than a
   count, should never say *"Taking longer than usual"* on a normal load.
4. **Look for your character.** ✅ Pass: **there isn't one.** Nobody spawns
   until PLAY, so nothing can be prompting you behind the screen.
5. **Let it loop.** Six shots at 9s each. ✅ Pass: each drifts rather than
   orbits, and the captions crossfade rather than cut.
6. **Press PLAY.** ✅ Pass, all of it:
   - You spawn ~110 studs from the Engine with **no ROLL prompt** until you
     walk in. That gap is where a first-join tutorial goes.
   - The blur clears and the camera follows you **on a first join**, not only
     after a respawn — that was the bug three sessions running.
   - You can walk **and sprint**. Walk but no sprint means
     `LoadingScreen.onFinished` never fired.

### Test J — the hub menu (5 min) ⭐ NEW

1. **The rail is there, on the left.** ✅ Pass: a Fate card, an arrow against
   its edge, and seven buttons in this order — **Travel, Party, Fate Tree,
   Rebirth, Shop, Codes, Settings**.
2. **Press the arrow.** ✅ Pass: the whole rail slides off the left edge and
   only the arrow remains. Press again to bring it back. **This is the noise
   control the whole rail is judged on — if it feels slow or sticky, say so.**
3. **Open Travel, then Shop.** ✅ Pass: opening the second closes the first.
   Never two panels at once.
4. **Travel to each of the five destinations.** ✅ Pass: the screen fades, you
   arrive **on the deck** (not inside it, not under it, not on the skirt), and
   you are facing the Fate Engine. ⚠️ Check the server output for
   `no floor under landing for '<Id>'` — that means the ray missed and the
   landing is a guess.
5. **Travel again immediately, and again.** ✅ Pass: it just works, every
   time — there is no cooldown. The whole fade is about half a second; **if it
   feels like a wait rather than a cut, say so** and `TeleportFade*Seconds`
   comes down.
6. **Codes.** Enter `LUCKBOUND`. ✅ Pass: +150 Fate and a message. Enter it
   again: *"You have already redeemed that code."* Enter nonsense: *"That code
   is not valid."*
7. **Settings.** ✅ Pass, one at a time:
   - **Interface size** — the whole UI grows and shrinks as you drag, live.
   - **Reduce motion** — panels snap rather than slide. **The roll reveal is
     unchanged**, deliberately.
   - **Music / Effects** — nothing audible yet (the game has no sound), but
     `SoundService.LuckboundMusic.Volume` should track the slider. Check it in
     the Explorer.
   - **Others' rolls** — needs a second player, or `/roll` from another client.
     Off: their banner does not appear. Yours still does.
   - **Screen shake** — stored only; nothing shakes yet, by design.
   - Rejoin. ✅ Pass: everything you set is still set.
8. **Roll at the Engine with the menu open.** ✅ Pass: the whole menu
   disappears for the reveal and comes back after the card.
9. **Enter an expedition.** ✅ Pass: the menu is **gone** — rail, arrow and
   all — and returns when you do.
10. **On a phone (or Studio's device emulator).** ✅ Pass: the rail starts
    collapsed, the panel is readable, and nothing is cut off at the edges.

### Test K — run and double jump (2 min) ⭐ NEW

1. **Hold Shift and run.** ✅ Pass: you accelerate over ~0.25s rather than
   snapping, and a small bar appears above the roll prompt.
2. **Keep running.** ✅ Pass: about 8 seconds later you drop back to walking
   and the bar is empty and amber. You cannot immediately sprint again.
3. **Stand still and hold Shift.** ✅ Pass: the bar does not move.
4. **Jump, then jump again in the air.** ✅ Pass: a second, smaller jump with a
   gold spark ring at your feet. A third press does nothing.
5. **Walk off the edge of a walkway and press jump immediately.** ✅ Pass: you
   get a **full** jump, not the weaker air one — that is the coyote window. You
   should then still have the air jump available.

### Test L — the menu follows the world (4 min) ⭐ NEW

The tint is subtle on purpose. Judge whether it is *too* subtle.

1. **Stand at the Fate Engine, open Travel.** ✅ Pass: the base look — deep
   purple, gold accents. The centre is deliberately untinted.
2. **Walk to the Discovery Archive** (or `/tp`). ✅ Pass: over about a second,
   the panel and rail shift toward the Archive's teal and the 1px edge picks
   it up more strongly. **The panel must not get lighter** — only change hue.
   If it looks washed out, the luminance-preserving mix has regressed.
3. **Walk back onto the open plaza.** ✅ Pass: it returns to base. The plaza
   belongs to no district.
4. **`/event FATEBREAK SERVER 60`.** ✅ Pass: the menu shifts toward Mythic
   orange within a second, over the top of whatever district you are in.
   `/endevents` clears it.
5. **`/event CATALYST_STAR GLOBAL 60`.** ✅ Pass: cold starlight, the
   strongest tint in the game. This is the one to judge hardest — it should
   read as *an event*, not as a different app.
6. **Start both at once.** ✅ Pass: the Catalyst Star wins, because GLOBAL
   outranks SERVER. It keeps winning until it expires.
7. **Read the Settings panel during each.** ✅ Pass: every label is readable.
   This is enforced by test, so a failure here means the test's model of the
   screen is wrong — report it.
8. **Let an event expire on its own.** ✅ Pass: the menu returns to base
   without anyone pressing anything — the client expires it locally.
9. **Turn on Reduce Motion, then walk between districts.** ✅ Pass: the tint
   snaps instead of fading.

### Test M — an event changes the world (4 min) ⭐ NEW

Commands reply **in chat** now, not only in the Output window — if you type one
and see nothing at all, it is not registered.

1. **`/event AURORA_VEIL`.** ✅ Pass: over about a second the hub's light goes
   blue-green, slow motes drift down over the plaza, and the menu's panel and
   stroke shift with it. The plaza stays **readable** — an AMBIENT event
   deliberately does not touch Brightness or ClockTime.
2. **`/endevents`.** ✅ Pass: the sky returns to exactly the hub's own light
   and the motes are gone. ⚠️ Look at the fog and the ambient colour
   specifically — a property that does not return is the bug this whole
   design is built to prevent.
3. **`/event STARFALL`.** ✅ Pass: Mythic-orange sky, heavier motes, the
   announcement banner, the menu tint following it.
4. **Start `AURORA_VEIL` while `STARFALL` runs.** ✅ Pass: nothing visibly
   changes — the Starfall outranks it. Now `/endevents` and start only the
   Veil: it takes over. Precedence is working.
5. **Enter an expedition during an event.** ✅ Pass: the biome's own lighting
   applies cleanly, with no orange left over. Return: the event's sky comes
   back if it is still running, the hub's own if it is not. **This is the
   collision most likely to be wrong — look carefully.**
6. **Let an event expire.** ✅ Pass: it ends on its own, on time, without
   `/endevents`.

### Test N — the ledger holds under a race ⭐ NEW — **two instances, 10 min**

The one test that cannot be done headlessly *or* by eye, because it is about
two servers doing the same thing at the same moment. Needs a **published**
place with API services enabled.

1. **`/ledger CATALYST_STAR`.** ✅ Pass: `0 of 10 claimed`. If it says the
   ledger is unavailable, the place is not published or API access is off —
   and note that **no unique can be granted in that state, by design**.
2. **`/event CATALYST_STAR`.** ✅ Pass: the starlight sky, the announcement,
   and `/ledger` now reads `1 of 10 claimed` with your name against #1.
3. **Open a second Studio instance on the same published place** (Test > Start
   Server, or two clients). Run `/event CATALYST_STAR` in **both at once**.
   ✅ Pass: the ledger's count rises by exactly the number of successful
   claims — never more. Two claims must never both report the same number.
4. **Claim until ten are gone.** ✅ Pass: the eleventh refuses with
   `EXHAUSTED`, and refuses on **every** server, forever.
5. **Turn off Studio's API access and try again.** ✅ Pass: it refuses with
   `UNAVAILABLE` and grants nothing. **Fail-closed is the whole point** — a
   Star handed out while the ledger was unreachable could never be counted or
   taken back.

⚠️ Claims made while testing are **permanent**. Ten is ten. Test on a separate
published place, or accept that the production ledger starts partly spent.

### Test O — parties, in Studio ⭐ NEW — **3 clients, 10 min**

Build spec §7.2. Studio cannot teleport, so here the portal builds the map
in the same server (`Expedition.InstanceMode = "AUTO"`) — **the party logic
is identical to the live path**, only the hop is missing. Test > Clients and
Servers > **3 players** > Start.

1. **Player1: rail → Party (P).** ✅ Pass: "Your party", "You are not in a
   party", and Player2 and Player3 listed under *Players here* with INVITE.
2. **Player1 invites Player2.** ✅ Pass: toast `Invited Player2.`; Player2
   gets a Roblox notification with **Accept / Decline** *even with the panel
   closed*, and the invite is listed in their Party panel.
3. **Player2 accepts** (either the notification or the panel). ✅ Pass: both
   panels show `Your party 2 / 4`, Player1 tagged *Leader*. Player3's list now
   shows both as *In a party* with INVITE greyed.
4. **Player2 tries to invite Player3.** ✅ Pass: the INVITE button is greyed —
   only the leader invites.
5. **Player1 invites Player3; Player3 declines.** ✅ Pass: nothing changes for
   the party; the invite disappears from Player3's panel.
6. **Everyone rolls. Player2 walks to the Fate Engine and presses ENTER (F).**
   ✅ Pass: *"Your party leader opens the portal."* Nobody moves.
7. **Player1 presses ENTER.** ✅ Pass: Player1 **and Player2** arrive on the
   same map, a few studs apart, with the same banner and the same countdown.
   The server log has one `-> <WORLD> seed N ... (party of 2)` line **per
   player with the same seed**. Player3 stays in the hub.
8. **Player2 uses the RETURN portal.** ✅ Pass: Player2 home with +25 Fate;
   Player1 still on the map, which is still there.
9. **Player1 returns.** ✅ Pass: map destroyed (no `ExpeditionStage` child
   left), party still intact in both panels.
10. **Player1 → LEAD on Player2**, then **Player2 → REMOVE Player1**.
    ✅ Pass: lead passes; after the removal the party disbands (a party of one
    is not a party) and both panels read "not in a party".
11. **Invite someone and wait 60 s without answering.** ✅ Pass: the invite
    drops off their list on its own.

Also worth a look: leaving the game (stop one client) while in a party — the
others' panels update and the lead passes on if it was the leader.

### Test P — the portal opens a new server ⭐ NEW — **published place, 2 accounts, 10 min**

The teleport half of §7.2, which **cannot run in Studio**. Needs the place
published, API Services enabled (DataStore + MemoryStore), and two Roblox
accounts in a live server.

1. **Solo: roll, press ENTER.** ✅ Pass: a Roblox teleport screen, then you
   arrive **straight on the map — no title card, no PLAY button** — with the
   banner and timer. The hub's output shows `opens <WORLD> for 1 ... ->
   reserved server <id>`; the developer console on the new server shows
   `this is an expedition server` and `hosting <WORLD> seed N`.
2. **Your Fate and level came with you.** Open the rail? It is hidden on an
   expedition server by design — check instead that the RETURN reward
   (step 3) lands on top of your real total, not on a fresh profile. If the
   output says `could not acquire profile ... will not persist`, the save
   hand-off lost its race — report it.
3. **RETURN.** ✅ Pass: teleported back **into the same hub server you
   left**, again with no title card, +25 Fate.
4. **Party of two: A invites B, B accepts, both roll *different* worlds, A
   presses ENTER.** ✅ Pass: both land in the **same new server**, on **A's**
   world, same map. B's own roll is untouched and still waiting for them.
5. **Let the timer run out.** ✅ Pass: both teleported home together, into the
   hub server they left, and **the party is still formed** when they land.
6. **B returns early via the portal, A stays.** ✅ Pass: B home; A still on the
   map. When A comes back, the party re-forms (within
   `Party.ReuniteWindowSeconds`, 120 s).

If any step lands you in a *different* hub server than the one you left, that
is the fallback working (the old one filled or closed) — note it, not a fail.

### Test Q — the Sky Citadel kit, in the world ⭐ NEW (8 min)

The 22 pieces were uploaded on 2026-09-23 and **not one has been stood on**.
Everything below is a claim the test suite cannot make: it checks numbers, and
these are all claims about what the meshes actually do.

1. **Roll until you get Sky Citadel, enter, and read the output.** ✅ Pass:
   the summary says `N chunks (N mesh, 0 blockout)`. **Any blockout at all
   means an asset id failed to load** — the seam is working, the art is not.
2. **Stand still and look at your feet.** ✅ Pass: you are standing *on* the
   deck, not in it and not above it. This is `GroundOffsetY = 96` meeting a
   real mesh for the first time; if you are 32 studs under the floor or
   hovering over it, that number is what to suspect.
3. **Walk the whole route to the arena.** ✅ Pass: no gap at any join, no step
   up or down between pieces, and the skyway decks line up edge to edge.
4. **Find a crossroads and look down its unused mouth.** ✅ Pass: it ends in a
   cap — an overlook, a broken span or a shut gate (§7.4) — not in open sky.
   Sealing is mandatory in this world, so **an opening onto nothing anywhere on
   the map is a failure**, and worth a screenshot with the seed from the output.
5. **Walk into the cap.** ✅ Pass: it is somewhere you can stand — a dead end
   authored as a dead end, per §7.4 — and its chunk folder in the Explorer
   carries `Role`, `Yaw`, `Scenario`, `ScenarioBand` and `FateTouched` like
   any other placeable piece.
6. **Look at the piece from a distance.** The meshes are untextured — flat
   vertex colour is expected, not a fault. What to report is anything that
   reads wrong at scale: a piece that looks the wrong size next to your
   character, or a landmark clipping its neighbour.

Report `PathLength` feel here too: this is the first walk that can say whether
the route is too short, too long, or about right.

### Test R — a world's ambience ⭐ NEW (5 min)

1. **Roll Sky Citadel and enter.** ✅ Pass: **sunrise**, not the purple dusk of
   earlier walks: a low gold sun, white faces lit gold, shadows blue-violet, a
   cobalt-to-rose sky, a few fading stars.
2. **Look down off an edge.** ✅ Pass: a sea of cloud below — a nearer warm
   layer and a farther bluer one — drifting slowly, at different speeds.
3. **Fly (`/fly`) a long way in one direction.** ✅ Pass: the sea never runs
   out; puffs keep appearing ahead of you.
4. **Look around at head height.** ✅ Pass: faint gold motes drifting past.
5. **Drop Roblox graphics to 1, leave, re-enter.** ✅ Pass: a visibly thinner
   sea and fewer motes, but never none. Frame rate should hold on low.
6. **`/leave`.** ✅ Pass: the hub looks exactly as it did before (its purple
   sky back, no clouds left behind).

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
