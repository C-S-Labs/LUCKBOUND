# LUCKBOUND — Project Status

**Last updated:** 2026-09-23 · **Phase 1 complete · expedition entry opened (build spec §7.1) · parties + expeditions as their own server (§7.2) · the scenario layer (§7.3) · caps (§7.4) · both chunk kits uploaded · the hub is authored art · the hub has a UI**

> **New conversation?** Read `WORKLOG.md`'s top entry first for where the last
> session stopped, then this file. `CLAUDE.md` has the rules.

Start here. This is the handoff document: what exists, what is decided, what is
open, and where to pick up.

---

## 1. Where the project stands

Phase 1's goal was one sentence: *you can walk around a recognizable LUCKBOUND
hub and press ROLL.* That is done, running in Roblox Studio, and playtested.

**As of 2026-09-22 there are parties, and the portal opens a new server.**
Owner-directed (build spec §7.2). The Party panel is live — invite, accept,
leave, kick, promote — and entering the centre portal reserves a fresh Roblox
server for the expedition. A party leader entering brings the whole party into
that same server on the leader's world, seed and timer; everyone keeps their
own profile, and comes home together to the hub server they left. In Studio,
where teleports cannot run, the same party logic builds the map in place, so
it is testable with a 3-client session. **Neither half has been walked** —
`TESTING.md` tests O (Studio) and P (published, two accounts).

**As of 2026-09-20 the hub has a player UI.** A loading screen with a camera
tour and a PLAY button, a collapsible side rail with seven panels (three live,
four designed-but-labelled), travel to all five Crossroads locations, code
redemption, saved settings, and two player abilities: sprint and double jump.
None of it has been seen in Studio — see `docs/PLAYER_UI.md` §5 and
`TESTING.md` tests I, J and K.

**As of 2026-09-18 the hub is authored art.** The generated blockout
Crossroads no longer runs: a 225-MeshPart authored plaza, four districts, four
walkways and a 4096-stud mountain horizon replace it, with the Fate Engine
still loading at the centre on the footprint the art reserves for it. None of
it has been seen in Studio — see §4.

**As of 2026-09-16 the roll has somewhere to go.** Owner-directed amendment
§7.1 lifted expedition entry out of the Phase 1 exclusion list: you can roll
Ethereal Scape, walk through the Expedition Gate, and stand in a map generated
from its chunk kit. **Combat, enemies, bosses and loot were NOT lifted and
remain excluded.** An expedition today is: arrive, walk a generated map, come
home.

**It has now been walked twice**, on 2026-09-16.

The **first** walk found four things 276 green tests had not: the hub had **no
floor**, two walkways stopped short of their platforms, the Observatory ramp
was 70 floating tiles, and the Expedition Gate's prompt could not be reached
from on top of its own plinth.

The **second** walk confirmed all four fixed, and **completed the expedition
loop end to end** — roll → Gate → generated map → return → Fate awarded. It
found one further problem: the Observatory's spiral ramp, now continuous,
encircled the Fate Engine and blocked the walk up to it. Also fixed; the
access is now a straight processional on the empty 45° diagonal.

§4 records what the tests were missing each time.

**The Design North Star (Master Spec §25) has been answered.** After playing the
roll loop with no combat, no loot, no art and grey blockout geometry, the
owner's verdict was: *"these rolls alone were fun."* Nothing was propping it up,
which makes that the strongest possible signal the core premise works.

### Verified working in Studio

| | Evidence |
|---|---|
| Server boots clean | `[LUCKBOUND] boot 11/11` → `server ready` |
| Hub generates procedurally | `[HubBuilder] built Crossroads: 5 zones, 436 instances` |
| 15-roll onboarding, exact order | Full arc logged, Epic at roll 8 |
| True RNG hands over at roll 16 | Roll 16 logged with no `(onboarding)` tag |
| ProximityPrompt roll interaction | `[E] ROLL` at the Fate Engine |
| Reveal pacing scales with rarity | Measured 9.4 s (Rare) vs 12.2 s (Mythic) |
| Runs without DataStores | Volatile-mode fallback, no crash |
| Rolls reach Ethereal Scape at slot 5 | Full arc logged 2026-09-16 |
| Portal recolours to the rolled rarity | Verified visually |
| **Expedition loop, end to end** | `-> ETHEREAL_SCAPE seed 107807269 5 chunks … left after 55s (RETURNED)` |
| Map generation builds a walkable layout | 5 chunks, 0 mesh / 5 blockout, attempt 1 |
| Per-client biome lighting applies and reverts | Verified across entry and return |
| Fate awarded on completion | +25, logged |
| Developer commands | All of `/fly /speed /tp /roll /enter /leave` verified |

**436 instances** is the current mobile-budget baseline for the hub.

### Expedition entry — new 2026-09-16

| | |
|---|---|
| Enterable worlds | **Verdant Valley, Ethereal Scape, Sky Citadel** (all three on real meshes since 2026-09-23; no enemies) |
| Rollable but NOT enterable | Emberfall (15%), Astral Reach (3%) |
| Entry point | Expedition Gate `ProximityPrompt`, server-side `Triggered` |
| Destination | the player's **last roll** — no new state, survives rejoin |
| Map | a kit assembled by `ChunkCore`/`ChunkLoader`, **or** one authored scene cloned by `PrebuiltLoader` — the world declares which |
| Seed | `(userId, TotalRolls, worldId)` — logged, so any map can be rebuilt |
| Lighting | applied **per client**, restored on exit. Never bleeds |
| Return | a small rarity-coloured portal on the arrival chunk, or the timer |
| Reward | +25 Fate on completion or return; **nothing for dying** |
| Switch | `GameConfig.Expedition.Enabled` — one boolean back to Phase 1 |

**25% of honest rolls currently land on a world with no map.** Those players are
told *"That world has no map yet."* and stay in the hub. It is handled, not
solved — see §4.

### World scale — rescaled 2026-09-16, tuned after the first walk

The hub was 120 studs across: 24 character-heights, with a 5×5 Discovery
Archive. It read as a room.

| | Original | Rescale | After playtest |
|---|---|---|---|
| Hub playable Ø | 120 | 1200 | **1150** |
| Zone ring radius | 46 | 420 | **400** |
| Zone platforms | 26–56 | 230–360 | **210–320** |
| Fate Engine platform r | 24 | 140 | **120** |
| Portal scale (Engine / Gate) | 1.5 / 2 | 9 / 12 | **6 / 8** |
| WalkSpeed | 16 (default) | **32** | 32 |
| Visual extent | ~420 | **4000** | 4000 |
| Chunk grid | 48 | **256** | 256 |

The owner's verdict on walking 1200 was *"much better, could be slightly
smaller, perhaps just a tad"* and *"structures now shifted to be a bit too
large"* — so the footprint lost 50 studs and the structures on it came down
about 10%. **The portal scales came down for a harder reason than taste:** a
plinth is `PlinthDiameter × scale` across, and the prompt on it only reaches
`UI.PromptActivationDistance`, so at 12× the Gate's plinth was wider than its
own prompt's range and could not be used at all.

**Playable footprint and perceived size are separate numbers.** 4000 studs is
not walkable — 43.8s to a zone even at double speed. 1200 at WalkSpeed 32 gives
13.1s centre-to-centre, ~4.4s edge-to-edge, and scenery reaching 4000 makes the
world read as vast anyway.

Both halves are **enforced by test**: no zone may exceed
`Scale.MaxTraversalSeconds` (20s), every zone must be ≥40 characters across, and
expedition walking must stay under 35% of expedition duration.

⏳ **Not yet seen in Studio.** Verified by test; nobody has walked it.

### Modular map system

**Drop-in chunk kits (2026-09-24, not walked).** A world with no
`Content/Chunks` module gets its kit from the `.rbxmx` files in
`assets/rbxm/chunks/<world>/`, measured at boot. `docs/CHUNK_DROP_IN.md`.


Added 2026-09-16. `assets/` holds Blender sources; `AssetManifest` maps logical
names to Roblox asset ids; `Content/Chunks/` holds authored pieces; `ChunkCore`
assembles them into a seeded, collision-free, deterministic layout; and
`ChunkLoader` turns that layout into walkable geometry.

**There are now two routes to a map, and a world declares which by data.** A
kit is assembled (`ChunkCore` + `ChunkLoader`); a `PrebuiltMap` is one authored
scene cloned whole (`PrebuiltLoader`). Declaring both is a boot error.
`ExpeditionSystem` has exactly one branch on it and it reads a field, never a
world id. Build spec §2.2.

A second kit existed briefly, for Ethereal Scape, authored against the
checklist rather than against Verdant Valley and with its own socket vocabulary
(`SPAN`/`RITE` vs `PATH`/`WIDE`) — and the same emergent gate-to-the-boss
property fell out of it, which was the thing being tested. It was retired
2026-09-17 when the delivered art turned out to be a composed traverse rather
than eight interchangeable pieces (§4). The grammar result stands; the kit had
no art to describe.

**Verdant Valley is the kit being built for testing** (owner-directed
2026-09-22). Its art is in authoring now. The intent while it is the only kit
with a map: **gate the roll to it for the duration of testing**, then restore
the pool as each biome lands. Two knobs do that and both are data:

- `GameConfig.Fate.PrototypeWeights` — the Phase 1 pool. `FateCore.effectiveWeight`
  prefers it over each world's `RollWeight` while `CurrentPhase == 1`, so this
  is the one that actually governs today. `VERDANT_VALLEY = 10000` with the
  rest at 0 keeps the set summing to 10000, which is what makes those numbers
  readable as percentages.
- `GameConfig.Fate.OnboardingSequence` — rolls 1–8 are **forced** regardless of
  weights, and four of them are not Verdant Valley. A weight change alone will
  not stop a fresh profile landing in Emberfall on roll 3.

No System changes either way, which is the point: this is the cheap answer to
the "25% of rolls land on a world with no map" row below, and it reverses by
editing the same two tables back.

All 8 remaining pieces are `PLACEHOLDER`, so the loader draws **labelled blockout** —
each platform carries its ChunkId and Role, with a neon post at every socket
coloured by Kind. **A generated map is verifiable by eye before any mesh
exists.**

### Test suite

**788 tests, all passing.** 35 arrived with loot, fixtures and vault keys (build spec §7.5). 28 arrived with ambient props (placements inside their pieces, tiers, and what each kind of prop may and may not do). 65 arrived with parties and expedition instances (§7.2), and the scenario layer (§7.3) added its own: compatibility, pacing bands, anti-repetition and determinism. Headless — no Roblox required. 136 of them arrived
with the player UI and the live palette: the menu reducer, travel authorisation, code redemption,
settings validation, the stamina curve and the coyote window.

**17 of them exist because the test suite was green while the hub had no
floor.** The group `Hub geometry a player can actually touch` asserts the
relationships two Studio walks found to be silently false — see §4.

```bash
./tests/run.sh
```

CI runs them on every push, plus a syntax check and the forbidden-module-name
scan (build spec P1-12).

---

## 2. What is built

```
src/shared/Core/     Types, Constants, GameConfig, Net, UITheme, Result,
                     FateCore, ProgressionCore, ProfileSchema, EventCore,
                     ExpeditionCore, HubMenuCore, SettingsCore, CodeCore,
                     LocomotionCore
src/shared/Util/     WeightedRandom, Schema, PortalRig, ChunkCore, ChunkLoader
src/shared/Content/  Worlds/ (6), Hub/Crossroads, Hub/Menu, Hub/Cinematics,
                     Codes, Chunks/ (2 kits), AssetManifest
assets/rbxm/prefabs/ HUB_FATE_ENGINE, HUB_CROSSROADS, HUB_BACKDROP
src/server/          init.server + Systems/ (Save, Progression, Fate, Event,
                                             Expedition, HubBuilder, HubUI)
src/client/          init.client + Controllers/ (State, Proximity, HubEffects,
                                                 Expedition, Locomotion)
                                 + UI/ (FateRoll, GlobalAnnouncements, ExpeditionHud,
                                        UIKit, HubMenu, LoadingScreen)
```

**Pure cores are the reason the test suite exists.** `FateCore`,
`ProgressionCore`, `ProfileSchema`, `EventCore` and `ExpeditionCore` hold every
decision with no Roblox globals, so they run headlessly. Systems hold only
plumbing.

`ChunkCore` / `ChunkLoader` is the same split applied to geometry: the first
decides what goes where and is pure, the second turns plain numbers into
Instances and knows no rules. **The seam between them is a list of numbers, and
that seam is why map generation is testable at all.**

### Worlds

| Id | Rarity | Weight | Phase | Biome? | Enterable? |
|---|---|---|---|---|---|
| `VERDANT_VALLEY` | Common | 6000 (60%) | 1 | blueprint written | ✅ kit |
| `ETHEREAL_SCAPE` | Uncommon | 1500 (15%) | 1 | **authored art** | ✅ kit |
| `EMBERFALL` | Rare | 1500 (15%) | 1 | blueprint written | ❌ no kit |
| `SKY_CITADEL` | Epic | 700 (7%) | 1 | ⚠️ **none — data only** | ❌ no kit |
| `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written | ❌ no kit |
| `THE_UNKNOWN` | Unknown | 5 | 3 | none | ❌ no kit |

Weights sum to 10000 so they read directly as percentages. Verified at 400,000
draws, worst drift 0.062pp.

**Ethereal Scape** is the first world with authored art behind it, and the
first **prebuilt** world: a sky temple above the cloud deck, eight gold-rimmed
meadow islands climbing toward it, six bridges, fourteen satellite islands as
backdrop, 699 MeshParts, all uploaded. It ships whole rather than as a kit,
because the art is composed: the route climbs 58 studs an island, each bridge
is cut to its own gap, the landings are authored in matched pairs, and the
islands grow toward the temple. Shuffling them breaks all four at once. The
measurements are in `assets/rbxm/maps/README.md`.

It declares **no enemies, boss or loot on purpose** — it is the map test biome,
and giving it combat content would make it a worse test.

---

## 3. Decisions locked in

These are settled. Do not relitigate without a deliberate reversal.

| # | Decision | Where |
|---|---|---|
| **D-8** | **Fate is TRUE RNG.** No player state ever changes the odds of any world. | spec §3.3 |
| **D-9** | **15-roll scripted onboarding**, peaking on Epic at roll 8, never Mythic. Slot 5 extended to Uncommon 2026-09-16 — arc unchanged in shape. | spec §3.3.1 |
| D-3 | Roll cooldown 3.0 s, enforced server-side, silent on rejection | spec §3.4 |
| D-4 | Reveal duration scales with rarity (2.5 s → 7.0 s) | Constants |
| D-6 | Roll history capped at 50 entries | GameConfig |
| D-7 | Expedition 720 s default — **still flagged as too long**; a world may override it and Ethereal Scape runs 300 s | spec §6 |
| **D-10** | **A rift reward is permanent; only the WINDOW is temporary.** No decay, no charge, no expiry attribute. Fair only while events recur — that is a commitment, not a preference | `EVENTS.md` §5.4, §6 |
| **D-11** | **The finder gets the unique item; everyone gets the event.** Ten Catalyst Stars produce ten game-wide occasions, not ten private ones | `EVENTS.md` §5.5 |
| **D-12** | **A failed rift run costs the attempt, not the event.** The rift stays open to all until the event ends; no per-player attempt counter | `EVENTS.md` §5.3 |
| **D-13** | **Event access never depends on the roll pool.** A biome with a live event is directly enterable by anyone, regardless of what their pool contains — otherwise pool progression locks high-tier players out of the events they have earned | `EVENTS.md` §5.4b |
| **D-14** | **Events are tiered AMBIENT / MODIFIER / WORLD**, enforced by the validator. Only WORLD may open a rift or grant a unique | `EVENTS.md` §4.0 |
| — | **Expedition entry is open; combat/loot are not** | spec §7.1 |
| — | Destination = the player's last roll. No new state, no schema bump | `ExpeditionCore` |
| — | Biome lighting is applied **per client**, never by the server | Blueprint §6 |
| — | Rarity colour is a UI/portal contract; biome palette is set dressing | Blueprint §4.1 |
| — | Compass mapping N=-Z, E=+X, S=+Z, W=-X, up=+Y | GameConfig.HubLayout |
| — | **A prefab is registered from a NAMED PART, not from its model pivot.** A pivot is invisible metadata an FBX chain mangles quietly; a part name is already the contract with the artist | `Util/PrefabLoader` |
| — | **Scale and compass corrections are content, never re-exports.** An importer setting is fixed by a number in `Prefab` | `Content/Hub/Crossroads` |

### Why true RNG matters downstream

With no odds tilting, **a player at roll 200 faces identical odds to one at roll
16.** "Stuck in Commons" is a permanent condition, not an early-game phase.
Fate cannot weight its way out of it.

The lever that stays consistent: **Fate unlocks which pools you draw from,
never how the draw resolves.** Higher Fate grants access to a pool that has no
Common in it. That is the Phase 3 design, and it is the answer to the
progression-feel problem.

---

## 4. Open items

### Needs the owner's sign-off

Four items in `BLUEPRINT_RECONCILIATION.md`. The significant one:

**Blueprint §1.1's Usage column contradicts §4.4 and §5.4** over which world
carries Mythic orange. Resolved in favour of §4.4/§5.4 (Emberfall = Rare blue,
Astral Reach = Mythic orange) and locked by test. Confirming closes it for every
future world's asset prompts.

Also open: rarity ordering (Mythic above Legendary) and formal confirmation of
the theme-vs-rarity rule.

⚠️ **The `UNCOMMON` colour just became urgent.** It was theoretical while
Uncommon belonged to a Phase 3 world nobody could roll. Ethereal Scape is
Uncommon, live at 15%, and guaranteed at onboarding roll 5 — so the
unsanctioned green `#5FD97A` is now on screen for every player within a minute
of joining. Bless it or replace it **before** people learn it.

### What 276 green tests missed — and what now covers it

The first Studio walk of the rescaled hub found four bugs the suite could not
see. Three shared one cause and it is worth naming precisely:

**`HubBuilder.cylinder()` built a `Part` wearing a `CylinderMesh`.** Two things
were wrong with that, and each alone would have been enough:

1. **A `CylinderMesh` is visual only.** The part keeps its *block* collision
   hull, so an invisible square corner juts past every visible round edge.
   Reported as *"I cannot walk near the portal, the mesh is too large but not
   visible"*.
2. **`CylinderMesh`'s axis is Y; `PartType.Cylinder`'s axis is X.** Every
   caller passed `(thickness, diameter, diameter)` — the X convention — so a
   *thin disc* was built as a *diameter-tall column*. The 1150-stud plaza was
   a 1150-stud **wall**. The hub had no ground, and the player spawned on top
   of it.

The others: two walkways used the platform's **X** half-extent regardless of
which axis they approached along, leaving 30–40 stud holes; the Observatory
ramp used a fixed 5-stud step depth that at the new radius left 21-stud gaps
between steps; and the Gate's prompt lived on a plinth wider than its own
reach.

| Why the suite missed it | What covers it now |
|---|---|
| No test rendered geometry — only data was asserted | `the plaza is a disc, not a column` asserts the *shape ratio* the bug inverted |
| The prompt-reach test carried a `* 2` fudge and covered only the Engine | Generalised to **every portal**, fudge removed, and the return portal added |
| Nothing asserted a plinth could be jumped onto | `MaxPlinthHeight` capped and asserted against jump height |
| Walkway geometry was untested | Approach-axis half-extent asserted per zone |
| Ramp step depth was a literal inside a System | Moved to `HubLayout.RampStepOverlap`, asserted > 1 |
| Nothing checked the spawn was in open space | Asserted above the walkway deck |

**The lesson, which is the same one §6.1 of the build spec already records in a
different form:** a test that asserts a *number* proves nothing about the
*shape* that number produces. These new ones assert relationships — is it
thinner than it is wide, can it be jumped onto, does it reach — because those
survive a rescale and a literal does not.

### Known debt

| Item | Severity | Notes |
|---|---|---|
| **`main` could not boot — two green branches, one red merge** | **Fixed 2026-09-23** | The `Supports` requirement (§7.3) and the 19-piece Sky Citadel kit landed from different branches; neither diff touched the other's files, so neither branch's CI could see it. `Schema.validateAll` — boot step 1 — errored on all 19 chunks. Separately, merge `f9dec00` silently deleted three `GameConfig` scenario dials, so `ScenarioCore.assign` compared a number against nil and **crashed the suite 210 checks into a 640-check run**, printing no summary. Both fixed; a test now validates the whole assembled content bundle exactly as boot does, which is the only level at which this class of defect is visible. |
| ~~`ScenarioCore` is implemented, tested and never called~~ | **Fixed 2026-09-23** | Wired into `ExpeditionSystem` at its §7.3 position: after `ChunkCore.assembleWithRetry`, before `ChunkLoader.build`. The plan rides on the layout, and `ChunkLoader` writes `Scenario`, `ScenarioBand` and `FateTouched` onto each chunk folder — reusing the attribute channel that already carries `Role` and `Yaw`, so a generated map is readable in Studio. **It still spawns nothing**; encounter and reward configuration remain behind §7. It draws from its own seeded stream (`ScenarioStreamOffset`), so adding a scenario can never shift which chunks a seed picks. |
| ~~`GameConfig.Expedition.IncludeSide` was never passed~~ | **Fixed 2026-09-23** | `ChunkCore` treats nil as "on", which happened to match the config value, so a designer turning it off would have been ignored in silence. Now passed by `ExpeditionSystem`. |
| ~~Two Sky Citadel documents disagreed~~ | **Fixed 2026-09-23** | `docs/SKY_CITADEL.md` held the real design while `docs/biomes/SKY_CITADEL.md` declared the world had none. Consolidated into `biomes/`, the location `biomes/README.md` defines and Verdant Valley already uses. Ten references updated. |
| ~~`Schema.validateAll` took 11 positional parameters~~ | **Fixed 2026-09-23** | A registry of validators keyed by content kind. Adding a content kind was five files; it is now one registry entry plus one line at the boot call. The test harness also discovers content registries by walking `Content/` instead of enumerating three of them by hand. |
| **Reserved declarations are now registered** | **New 2026-09-23** | `docs/RESERVED.md` classifies every declared-but-unread field, remote and option as CONSUMED, RESERVED, OBSOLETE or ORPHANED, with the consumer named. **A declaration that is unread and absent from that register is a defect, not a decision.** Sites carry a `RESERVED:` tag pointing at it. Nothing is currently orphaned. |
| ~~`ChunkCore.exitFor` takes the FIRST valid socket~~ | **Fixed 2026-09-22** | A seeded pick among valid exits, drawn only when there is a choice. Needed for the Sky Citadel crossroads; asserted (the crossroads leaves by more than one mouth across seeds). `MODULAR_MAPS.md` → *Exits and side pockets*. |
| ~~`IncludeSide` is declared and never read~~ | **Fixed 2026-09-22** | Consumed: one SIDE chunk hung off a spare socket after the arena, if one fits. `GameConfig.Expedition.IncludeSide = true`, passed by `ExpeditionSystem`. Sky Citadel's lookout hangs off a crossroads branch. **Verdant Valley cannot host one** — every VV piece has exactly two openings and the critical path spends both, so no seed leaves a spare socket. Its Fern Hollow is a `COMBAT` piece, and `Schema.validateChunks` refuses a kit that declares `SIDE` without a 3-socket piece. Asserted as a property over every world, not one world's claim. |
| **Unused sockets are never capped** | Medium | The generator consumes one socket to arrive and one to leave; every other opening on the piece faces nothing, and the loader does not close them. With high socket counts — which is what gives a run variety — that is several openings per piece looking onto the void. Today the art has to solve it (`CHUNK_AUTHORING.md`: an opening must read as plausible unattached). A cap piece placed by the loader at unused sockets is the systematic fix and would need a schema field for it. |
| **A chunk's mesh origin must be its footprint centre, and nothing enforces it** | **High** | `ChunkLoader` puts the mesh's origin at the layout centre and rotates about it by a seed-derived `Yaw`, and `ChunkCore.overlaps` checks collisions against centre ± half-size. A corner or edge origin therefore lands the art half a chunk out, by a different amount per rotation, and the generator still certifies the layout as collision-free. It is a **data contract with the Blender file that no test can see** — the origin is invisible metadata, exactly the failure mode that produced the "register a prefab from a NAMED PART, not from its pivot" rule for the hub. Documented in `CHUNK_AUTHORING.md`; the first uploaded mesh is where it gets proven. |
| ~~The 12-piece test kit measures correct, with four problems~~ | **Superseded 2026-09-22** | Delivered 2026-09-22 and inspected from the FBXs. **Right:** all 12 at exactly 256 × 256 (the millimetre bug is gone), origin centred at (0,0) with ground at 0.0 and a 4-stud skirt, **every edge on every piece at exactly 0.0**, openings centred on edge midpoints 42–50 wide. **Wrong:** `chunk_grove` is 14,448 triangles against Roblox's 10,000 cap; Apply Transform was off so every file carries `Lcl Rotation = (-90,0,0)` with Z-up data; six material slots on one joined mesh where a MeshPart has one colour; and our `SizeY = 340` against real heights of 42–77, which `ChunkLoader` would stretch 5–7× vertically. |
| **Docs told the modeller not to build variety** | **Closed 2026-09-22** | Found by asking what in the repo conflicted with a varied kit. Four statements did: `CHUNK_AUTHORING.md` said extra pieces should be "variants of existing roles, not new roles" (read as *only build more meadows*); `MODULAR_MAPS.md` said "one SIDE pocket per world" and "one `ENTRY`, one `BOSS`" as caps when the schema only requires a floor of one; and the Verdant Valley progression read as a fixed running order rather than a difficulty curve. All four corrected. The root cause was structural — **one document was trying to be both the engine contract and the description of a world** — which is what `docs/biomes/` now fixes. |
| ~~A Kind offered by exactly one piece is a gate AND a sameness~~ | **Resolved 2026-09-22** | The reserved-arena-Kind rule made the Grove precede the boss on every seed, because it was the only `WIDE` provider — the intent at 8 pieces, the largest limit on variety at 12. Fixed in content: `WIDE` now sits on Ruins, Waterfall and Ridge Overlook, and the approach splits roughly 35/35/30. The gate survives; the sameness does not. Sky Citadel was authored against the same lesson, with two ASCENT providers. |
| **Runs were a single straight shot** | **Fix pushed 2026-09-23, unproven** | Owner-directed after two walks. Two causes, one in each half. **The assembler**: a spare mouth was capped where it stood, so an intersection was a junction with two visible walls — a mouth now grows a spur of up to `BranchLength` pieces before the cap closes it (spec §7.4, extended). **The content**: the crossroads is the only piece with a mouth to spare and sat at weight 14, one per layout — about one run in six had any branch at all. Now weight 30, two per layout. With `PathLength` 5 → 8 a map runs ~12.6 pieces against ~7.3 before, and 300 of 300 seeds still assemble. |
| **World ambience** | **Built 2026-09-23, unwalked** | Data-driven per world (`Environment` blocks: Atmosphere, Sky, Bloom, SunRays, Grade, CloudSea, Motes), drawn client-side by `AmbienceController`, scaled by graphics quality. Sky Citadel is now **sunrise above the cloud sea**. Also fixes a leak: the hub's `Atmosphere` stayed in `Lighting` on entry, and while one exists Roblox ignores fog — so every world wore the hub's purple haze. `TESTING.md` Test R. |
| **Ambient props** | **Live 2026-09-23, unwalked** | Floating scenery split out of the Sky Citadel pieces: 168 placements of 22 prop kinds (`Content/Props/SkyCitadel.luau`), drawn and animated client-side by `PropController` from `assets/rbxm/props/SC_PROP_LIBRARY.rbxmx`, thinned by graphics tier. The 22 Sky Citadel AssetIds are now the structure-only meshes (`SC_STRUCTURE.rbxmx`). Each prop kind has the motion that fits it (`CHUNK_AUTHORING.md` convention 6). `TESTING.md` Test S. |
| **Loot, fixtures, vault keys** | **Live 2026-09-23, unwalked** | Build spec §7.5. Chests (5), the treasury vault door and the sealed gate's forcefield are server-placed fixtures; birds have flapping wings. Chests open once per party with each member's own roll, from pools that are **empty by design**. **The vault is per player:** whoever uses their own key opens it for themselves, and only their key is spent. The Sky Citadel Vault Key drops only from the Sky Citadel boss stand-in (reaching the arena), at 20%, in any Sky Citadel map, treasury or not. It is shared to the party, saved (profile v3), max 1 per kind. The treasury is in about 1 map in 5. Re-import done (3 structure ids changed). `TESTING.md` Test T. |
| **Sky Citadel generation — walked and verified** | **Closed 2026-09-23** | Owner walk, two Studio sessions, four maps: all correct in orientation and placement, four distinct seeds. Root cause of every earlier misfacing was `ChunkCore` and `CFrame.Angles` turning opposite ways (fixed via `ChunkCore.yawRadians`); seeds now carry `Random.new()` entropy per entry. Every piece measured facing 180 at maximum probe score. |
| ~~The art's north is not the layout's north~~ | **Fix pushed 2026-09-23, unproven** | First Studio walk: every piece loaded, every socket lined up in the layout, and **the bridges met nothing** — the art is authored Z-up with +Y north and the FBX axis conversion lands it a half turn out. A 256³ box hides this completely: bounding box, sockets and collision are identical at every yaw, so nothing headless can see it. Fixed as data — `MeshYawOffset = 180` on the kit, applied by `ChunkLoader` to the **mesh only**, never to sockets or collision. If the next walk shows a quarter turn rather than a half, that one number becomes 90 or 270. |
| **The Sky Citadel kit is IN** | **Closed 2026-09-23** | 22 `.rbxmx` models, same shape as the Verdant Valley delivery: one Model around one MeshPart already carrying its `rbxassetid`. Every size read off the delivered mesh — exactly 256³ on all 22 — and every piece arrived with `PivotOffset.Y = −32`, which **confirms `GroundOffsetY = 96` from the art rather than from the generator alone**. Three of the 22 are the CAP pieces that landed separately in PR #40 the same day; the role and the sealing pass are theirs, and §7.4 now records the amendment neither branch claimed. Untextured (`TextureID` null): flat vertex colour is the intended look. **Not yet walked in Studio** — `TESTING.md` Test Q. |
| **Verdant Valley 30-piece kit exported** | **Open 2026-09-24** | Redelivered as 30 pieces. `export_verdant_valley_kit.py` joins, centres and measures each one, then writes one FBX plus the content module. The sockets were redone from the geometry, because the file's labels were mirrored. 2 entries, 6 `WIDE` gates, 5 junctions, 1 cap, 3 side pockets. 200/200 seeds assemble. **Waiting on Studio upload**: every new key is `PLACEHOLDER` (blockout) until `--ids` is run. `assets/source/worlds/verdant_valley/IMPORT_STEPS.md`. |
| **The Verdant Valley kit is IN** | **Closed 2026-09-22** | 11 `.rbxmx` models, each a Model wrapping one MeshPart carrying a real `rbxassetid` — the meshes were uploaded on the modeller's side, so the asset ids were the whole integration. Every number in `Content/Chunks/VerdantValley.luau` was read off the delivered geometry rather than typed. 200/200 seeds assemble, 174 distinct layouts. **Not yet walked in Studio** — that is the next real gate. |
| **The Grove did not survive the upload** | Medium | 14,448 triangles against Roblox's 10,000 cap for one MeshPart, so 11 pieces arrived, not 12. It was the only `WIDE` provider and its absence alone would have made every assembly fail. `WIDE` moved to Ruins, Waterfall and Ridge Overlook — which was the variety fix already owed. Needs decimating and re-uploading; costs a kind of place, not a working kit. |
| **`GroundOffsetY` — done** | **Closed 2026-09-22** | A layout's Y is the walking surface, but setting `mesh.Size`/`CFrame` puts the bounding-box centre there, so every delivered piece would have sat ~20 studs into the floor. `GroundOffsetY` is the studs from the bottom of the box up to the walk plane; absent it defaults to `SizeY/2`, which is the old behaviour exactly. Schema refuses a value outside the piece. |
| **`IncludeSide` — implemented, and revealed why it never worked** | **Closed 2026-09-22** | Declared and unread since 2026-09-16. Now hangs a pocket off a socket the critical path did not spend, which required tracking spent sockets per placement. Best-effort by design: a pocket that will not fit is a pocket this seed does not get, never a failed expedition. **It also surfaced the real reason no pocket had ever appeared:** every delivered piece has exactly two openings, the path spends both, so no seed leaves a spare socket. A pocket needs a 3-opening piece and this kit has none — `Schema.validateChunks` now refuses that combination rather than letting a SIDE piece validate and never appear. |
| **The scenario layer** | **New 2026-09-22, headless only** | Build spec §7.3, from the *Procedural Biome Design Brief*. A chunk is physical space; a scenario is what happens inside it. `Content/Scenarios` is the library, chunks declare `Supports`, `Util/ScenarioCore` assigns one per room from the run seed — pure and headless like `ChunkCore`, so pacing is testable in CI. **It spawns nothing:** encounter and reward configuration stay behind the §7 exclusions, deliberately. Measured: **50 distinct chunk/scenario rooms from 11 pieces**, bands at 51/37/11% ordinary/uncommon/rare, Fate touching ~4%. Never walked. |
| **Two generated PDFs removed** | **Closed 2026-09-22** | `LUCKBOUND_Master_Spec_v0.2.pdf` and `MODELLER_HANDOFF.pdf` were agent-generated binary snapshots that could not be diffed or reviewed, drifted the moment anything shipped, and had begun to contradict the living markdown — a second source of truth, which is what CLAUDE.md rule 1 exists to prevent. Replaced by `MASTER_DESIGN.md` and `CHUNK_AUTHORING.md` + `biomes/`. **The owner's v0.1 PDF at the repository root stays** and remains authoritative on intent. |
| **A brief that specifies the piece gets the piece it specified** | **Process** | Recorded 2026-09-22 after it happened. The first `CHUNK_AUTHORING.md` was handed to the modeller's AI engine carrying a table of eight footprints (512–1024), a 32-stud flat weld band on every edge, and a 13-item checklist. All three were read as targets: the kit came back at roughly 10× the area with terrain flattened to the boundary and the scatter lost in it, and the better earlier iteration had to be restored from backup. **A number stated in a brief is a number that gets built.** The rewrite states only what breaks the game and says outright that everything else is the modeller's. The general rule for any art brief on this project: **specify the seam, not the piece.** |
| **FBX exported at 1000× — millimetres, not metres** | **Closed 2026-09-22, in the brief** | The first Verdant Valley batch imported at **256,000 studs** against a declared 256. Exactly 1000×, so the FBX was written in millimetres. The brief now names both settings that have to agree (Blender units Metric/Metres/1.0; FBX Transform → Scale 1.00, Apply Scalings `FBX All`) and, more usefully, tells the modeller to **measure one piece in Studio rather than trust the export** — a 256 piece must read 256. The compensating-factor workaround (FBX export scale 0.001) is named and discouraged, because a compensating factor is a thing someone later removes for looking wrong. |
| **Kit target raised to 12–16 pieces** | **Content** | Owner-directed 2026-09-22. This file declares 8 — one per role in the Blueprint progression — and the variety of a run is the variety of the kit, so 8 repeats itself. Extra pieces arrive as **variants of existing roles**, not new roles: several meadows, several groves, weighted so one is common and another rare. Entries get added as each piece is authored; declaring chunks with no art would have the blockout drawing pieces nobody meant. **First delivery is 4** — ENTRY, PATH_STRAIGHT, GROVE, BOSS_CLEARING — the smallest set that assembles a complete walkable map. The Grove has to be among them: the WIDE reservation makes it the only piece offering the exit the arena accepts. |
| **The kit was generated stacked at one point** | Low | Every Verdant Valley piece came back occupying the same spot in the Blender scene. Nothing was broken by it — the exports were correct — but it made the kit impossible to review without hiding objects one at a time, and a piece nobody can see is a piece nobody checks. The brief now asks for a spaced review layout, with the catch stated: **the review position and the export position are different things**, and a piece exported while parked on the review grid arrives that far off in game. |
| ~~`GroundOffsetY` — the loader needs a ground-level origin and does not have one~~ | **Built 2026-09-23, unproven in Studio** | Built in session 47 and applied to Sky Citadel at 96; the delivered meshes then came back carrying `PivotOffset.Y = −32`, which is the same number from the other side. It is still a claim about geometry nobody has stood on — `TESTING.md` Test Q step 2 is where it is settled. Original note follows. |
| *(original)* | |  `ChunkLoader` sets `mesh.Size = (SizeX, SizeY, SizeZ)` and puts that box's **centre** at the layout Y, while the blockout puts the **walking surface** there. The first version of the brief closed the gap by requiring the art to centre its walk plane inside `SizeY` — 170 studs of ground body under the player's feet at `SizeY = 340`. That was the wrong side to bend: **`CHUNK_AUTHORING.md` now asks for a ground-level origin**, which is what an artist would author anyway and what the blockout already assumes. The loader owes a `GroundOffsetY` on the chunk schema to consume it. **This is now a prerequisite for the first mesh upload**, not deferrable debt — nothing is uploaded yet, so there is time, but a piece imported before it lands will sit half-sunk. |
| **Portal plane is still above head height** | Medium | You reach the prompt and the rig springs from the floor, but the walk-through *plane* sits inside the inner ring, ~30 studs up. Blueprint §1.3's concentric rings make that inherent. Irrelevant once the rig is authored in Blender. |
| **18% of rolls land on a world with no map** | **High** | Emberfall 15%, Astral Reach 3%. Refused politely at the Gate; printed as a boot warning and asserted by test. Both need only a chunk kit. **Sky Citadel left this list 2026-09-22** — `docs/biomes/SKY_CITADEL.md` is its section, `Content/Chunks/SkyCitadel.luau` its kit. |
| **A chunk mesh is stretched to its declared size** | **High — narrowed 2026-09-23** | Both delivered kits measure exactly what their content declares (Sky Citadel 256³ on all 22, read off the files), so nothing is stretched today. The loader behaviour is unchanged, so the trap is still open for the next kit. Original note follows. |
| *(original)* | |  Found 2026-09-22 generating the Sky Citadel kit. `ChunkLoader.tryMesh` sets `mesh.Size = (SizeX, SizeY, SizeZ)`, so a mesh whose bounding box is not exactly that box is **silently distorted** — a round arena that does not reach the tile corners would be stretched into them. Sky Citadel works round it by pinning every piece to exactly 256³ (edge pins at −96, a landmark at +160). The brief does not say this, and Verdant Valley's `SizeY = 340` is a guess the first mesh will not match. Either the brief says "fill the box" or the loader sizes the mesh from its own bounds and uses `SizeX/Y/Z` only for collision rejection. |
| **Chunk colour on a single MeshPart is unverified** | **High — testable now** | The Sky Citadel delivery has `TextureID` null on all 22 and relies on vertex colour, so whether `CreateMeshPartAsync` preserves it is now a question a Studio walk answers — Test Q step 6. Original note follows. |
| *(original)* | |  A chunk loads as one `MeshPart` via `CreateMeshPartAsync`, so it has one `Color`; the hub's paint-by-part-name does not exist for chunks. Sky Citadel bakes its palette into **vertex colours** as well as material slots. Whether Studio keeps vertex colours on the imported MeshPart is the first thing to check on import. If not: a multi-part `.rbxmx` delivery (a loader change) or one colour per piece. |
| ~~Chunk collision is default fidelity on one mesh~~ | **Fixed 2026-09-23, unproven** | Confirmed by the first Studio walk: the player stood on an invisible shell above the deck, because a 256³ piece with a spire gets a hull close to its whole box. `tryMesh` now passes `CollisionFidelity = PreciseConvexDecomposition` **at creation** — assigning it afterwards does not re-cook the geometry. Needs a second walk. |
| *(original)* | Medium | `tryMesh` sets `CanCollide = true` and nothing else, so railings, parapets and gate arches seal into coarse hulls — the invisible-wall failure `ART_DIRECTION.md` documents for the hub. `CreateMeshPartAsync` takes a `CollisionFidelity` option; chunks should pass `PreciseConvexDecomposition`. |
| **Expedition spawn uses the mesh's top, not its ground** | Medium | `entryPosition` is the surface's top face. With a mesh that is the bounding-box top: +160 for a Sky Citadel piece, so a 128-stud drop onto the landing pad (the entry keeps (0, 0) clear for exactly this). Fixed by the same `GroundOffsetY` that fixes the placement. |
| **The authored Crossroads is in, and has been walked once** | **Open** | Delivered 2026-09-18: 225 MeshParts, all 10 contract names present, 225 of 225 painted, Scale 2.0 with a 180° compass correction. **Walked 2026-09-18** and the owner's verdict was *"looks very nice in general"*, with seven specific faults — all fixed the same day (§1). `assets/rbxm/prefabs/README.md` has the measurements. **Its south district is a Shop**, while Content still calls that zone `EXPEDITION_GATE` — see the portal-as-entry row below. |
| **The authored hub's collision set, take two** | Medium | The first pass granted collision to **57 of 225** and left every merged or hollow mesh pass-through — safe against invisible walls, and the walk found the opposite cost: players sank into platform flanks and walked through railings. It is now **91 of 225, with 30 at `PreciseConvexDecomposition`** for the meshes whose openings matter. That fidelity is **baked into the `.rbxmx`**, because it cannot be assigned at runtime — see the row below. Still unverified in-engine; the risk has moved from "walls where there should be none" to "the precise hulls cost more at load than budgeted". |
| **A re-delivered prefab loses its baked `CollisionFidelity`** | Medium | A fresh export from Studio carries none, so all 30 precise parts would silently drop to `Default` and seal their own openings. `PrefabLoader` warns by name when the file disagrees with what content declares, which is the only thing standing between a re-delivery and a hub full of invisible walls. The bake step is documented in `assets/rbxm/prefabs/README.md`. |
| **Scaling the horizon cannot change its apparent size** | Note | A uniform scale moves the ring closer as it shrinks, so height and radius fall together and the mountains subtend the same angle from the hub's centre at any scale. Only DISTANCE changes. Learned by scaling it down and finding it clipped the plaza instead of looking smaller. |
| **The horizon wants a purpose-built chunk** | Low | Owner-stated 2026-09-18. `Backdrop_Mountain` is a whole ring being used as a chunk, which works but is not what it was authored for. The intent is to replace `HUB_BACKDROP` with a **single massif** designed to be cloned. Nothing in code changes when that lands — `Ring.Part` already names the mesh, and the count, radius and jitter stay as they are. |
| **Trees on the bordering floating islands are malformed** | Low | Owner-observed 2026-09-18, deliberately deferred. The tree geometry on the islands ringing the plaza is wrong in the delivered mesh. Cosmetic, far from the player, and a re-export fixes it rather than any code here. |
| **The portal's stop has nothing to lead to yet** | **Open** | The Engine's portal now turns and locks on a quarter-turn slot, which was built so a staircase could land on it. The staircase itself is not built: the owner asked whether to author it in Blender or generate it in Studio. **Recommended: one authored step, cloned and stacked by code** — the same authored-look / procedural-placement split the mountain ring just proved, and the only version that adapts to the height and slot the portal actually stops at. |
| **The mountain horizon is built, not placed** | Low | Three attempts to scale the delivered ring into position failed — the hub-to-peak distance is a property of a mesh asset nothing here can measure, so every scale was a guess. It is now **14 clones of one chunk at radius 2400**, leaving 723 studs of clear sky past the plaza edge and 279 past the ground skirt. Retune with `Ring.Radius`, never `Ring.Scale`. |
| **First-join intro screen** | **Built, unwalked** | Built 2026-09-20 — `client/UI/LoadingScreen`, shots in `Content/Hub/Cinematics`, `docs/PLAYER_UI.md` §2. The design note that produced it follows. Owner-stated 2026-09-18. On a player's first join to a server, show a title screen over slow cinematic shots of the map until they press **Play**. The stated purpose is as much technical as aesthetic: it gives the client time to render and replicate before the player is standing in the hub. Directly relevant — the hub animator already has to wait for ~450 instances to arrive, and that wait is currently invisible and unexplained to the player. Not built. |
| ~~There is no in-world way into an expedition~~ | **Closed 2026-09-21, unwalked** | The Fate Engine carries entry: an `ENTER` prompt on the dais, on `F` so it does not fight `ROLL` on `E`. The staircase is still unmodelled and no longer blocks testing. `ExpeditionSystem` now finds the entry anchor by NAME anywhere in the hub, so moving it again (to the top of the stairs) is a placement change, not a system change. `TESTING.md` test C2b | Owner-directed 2026-09-18: the `ENTER` prompt standing in the middle of the authored market was not where a biome should be entered, so the gate anchor and prompt were removed outright rather than relocated. `ExpeditionSystem` tolerates the absence — it warns that entry is remote-only and carries on — so `/enter` still works for testing. **This is a deliberate gap and it closes when the Fate Engine carries entry**, which is the next piece of work. A test pins the absence so it cannot be closed by accident. |
| **The Engine portal is to become the way into biomes** | **Architecture** | Owner-stated 2026-09-18. The rolled world would be entered through the Fate Engine itself, not the Expedition Gate — roll, react, then a prompt to keep the biome, then a **staircase generates from the portal's centre down to the base** and the player walks up it. The staircase animates as if building itself. **This is not only art:** "keep this biome?" is new state between rolling and entering, where today the destination is implicitly the last roll. It also makes the Expedition Gate district redundant, the way the Observatory became. Needs a spec amendment before any of it is built. |
| **The authored Fate Engine is wired but unwalked** | **Open** | Delivered 2026-09-18 and in the game: 78 MeshParts, all 46 contract names present, painted from the palette, rings counter-rotating, shards on the rarity cycle. Never seen in Studio. `assets/rbxm/prefabs/README.md` has the measurements. |
| **Ethereal Scape's `Scale_Reference` proxy is loose** | Low | The v2 R6 proxy measures 13.2 studs against a real 5, but the rest of the scene reads correctly at `Scale = 1.0`. So the proxy is a stand-in, not a live reference. Worth tightening before the next world, or dropping — measuring it alone is what produced the ~10× v1. |
| **The scene has no `EntryAnchor` / `ReturnAnchor`** | Medium | The loader derives both from the bounding box and warns, so the map loads and walks. Arrival lands on top of the bounding box rather than on `Spawn_Platform` (44 × 44, under the colonnade). Two named parts in Studio fix it — the only thing left on that file. |
| ~~Expeditions are to become a separate place/instance~~ | **Built 2026-09-22, unwalked** — build spec §7.2. A reserved server of the same place, manifest via MemoryStore, parties travel together. `TESTING.md` Test P. The note that follows is the original | Owner-stated 2026-09-16: worlds will be rendered in a separate instance and reached by `TeleportService`, for performance and to isolate parties and solo queues. The current in-place `ExpeditionStage` is therefore a **prototype of the loop, not of the deployment**. `ExpeditionCore` is unaffected — it decides destination, seed and eligibility, none of which care where the map is built. `ExpeditionSystem` and `ChunkLoader` are what would move. |
| Fate-on-completion may become currency or loot | Design | Owner-flagged: a completion bonus drawn from an item pool, or a currency for upgrades, rather than flat Fate. `ProgressionSystem.award` is the single seam. |
| `UNCOMMON` colour unsanctioned | Medium | Now shipping — see above |
| Chunk collision is XZ-only | Medium | Blocks any kit that climbs. `MODULAR_MAPS.md` |
| No pathfinding validation | Medium | Non-overlapping ≠ walkable between. Addendum §A4 step 4 |
| ~~All 27 chunks are `PLACEHOLDER`~~ | **Closed 2026-09-23** | Both kits are uploaded: Verdant Valley's 11 (2026-09-22) and Sky Citadel's 22 (2026-09-23). The blockout fallback stays for anything added later |
| **Ethereal Scape: one whole map, not eight chunks** | Decided 2026-09-17 | The art is a composed traverse and cannot be shuffled — evidence in `assets/rbxm/maps/README.md`. Wired: `assets/rbxm/maps/` → `ServerStorage.LuckboundMaps` → `PrebuiltLoader`. **Walked in Studio 2026-09-17** — v1 at `Scale = 0.1` read too small, modeller re-delivered at play scale, now `Scale = 1.0`. |
| UI needs resize/layout pass | Cosmetic | Owner-flagged. The new hub UI is built to `UITheme`'s scale/offset caps from the start; the older three screens are not |
| ~~The hub is twice player scale~~ | **Fixed 2026-09-21, unwalked** | Halved through one number, `HubLayout.WorldScale = 0.5`. Counters are now 3.0 studs and railings 3.35 against a ~5-stud player. WalkSpeed 32 → 24 with it. **Nobody has walked the half-size hub** — judge the plaza, the district distances and whether 24 feels right |
| **The Crossroads wants a revamp after testing** | **Design** | Owner-proposed 2026-09-21 and agreed: rebuild the structures and level of detail properly, then drop a new `.rbxmx` in once testing is done. The contract that makes that a drop-in is in `ART_DIRECTION.md` — the 10 named parts, the `EngineReserve` anchor, the collision bake, and measuring against a player rather than a brief |
| **Staircase clipping at the walkway junctions** | Medium | Seen 2026-09-21. The stairs and walkways are **entirely authored mesh** — with a shell present `HubBuilder` generates no walkways at all — so no code number can fix it. It is a Studio edit plus a re-export, and the re-export must re-bake `CollisionFidelity` (see `assets/rbxm/prefabs/README.md`) or 30 precise parts silently seal their own openings |
| **The live menu tint is unseen** | **High** | The menu leans toward the district you are in and toward any live event. Hue-shift-at-constant-luminance is correct on paper and has never been looked at; on dark surfaces it is subtle by construction and may want to be stronger. `TESTING.md` test L, `Content/Hub/Palettes` is the dial |
| **Rifts: event-gated dungeons** | **Design** | Owner-directed 2026-09-20. A biome event opens a portal in a generated map; through it is a far harder dungeon with rewards obtainable nowhere else. Fully designed in `docs/EVENTS.md` §5, including where the portal attaches for both map routes and the reward-permanence question. **Blocked on combat and items (Phase 2)** — but the portal, the gating and the timer can be prototyped with an empty room behind them |
| **The event sky is built and unwalked** | **High** | Three authored events (Aurora Veil, Starfall, Catalyst Star), per-client lighting, a mote layer and a colour grade, reverting to the hub's own light exactly. Never rendered. `TESTING.md` test M — and step 5, the expedition collision, is the one most likely to be wrong |
| **The event catalogue is a proposal, not a plan** | **Design** | `docs/EVENTS.md` §4 lists 15 candidate events across the three scopes with triggers, rarity and durations. §6 holds five questions for the owner; the biggest is whether a rift reward is permanent, temporary, or split (a permanent look with a rechargeable power, which is the recommendation) |
| **Global scarcity (Catalyst Star)** | **Built, unproven under concurrency** | `LedgerCore` (pure) + `LedgerSystem` claim a number from a single DataStore key with `UpdateAsync` before anything is announced, and **fail closed**: an unreachable ledger grants nothing, which is the opposite of SaveSystem's instinct and deliberately so. Concurrency cannot be tested headlessly or by eye — it needs the two-instance Studio test in `EVENTS.md`/`TESTING.md` |
| **The hub UI has been walked twice** | Medium | Walks on 2026-09-21. The rail draws, in the right order, and the hub reads well. Three bugs found and fixed the same day: a hotkey name that threw on every keystroke, a loading gate that could never complete, and two glyphs that rendered as empty boxes. The second walk found three more: a button that ate its own label after one click, a camera release that lost a race to the tour thread, and a Settings panel that saved everything and applied nothing. See the WORKLOG entries |
| ~~**The hub UI has never been rendered**~~ | Superseded | Every pixel of the rail, the panels and the loading screen is reasoned rather than observed. `TESTING.md` tests I, J and K are the first walk |
| **Three panels are designed, not implemented** | Expected | Party went LIVE 2026-09-22 (§7.2). Shop, Fate Tree and Rebirth draw their real screen over placeholder copy with an IN DESIGN badge. Owner-directed: designed now, built after testing. Branch-level ideas for the tree are in `docs/PLAYER_ABILITIES.md` §3 |
| **Five settings are stored and honoured by nothing** | Medium | `MusicVolume`, `SfxVolume`, `UiScale`, `ScreenShake`, `ShowGlobalAnnouncements` persist but drive no system, because those systems do not exist. `ReduceMotion` and `AutoHideMenu` do work |
| **Travel landings are guesses with a safety net** | Medium | Content names an X/Z per district and the server rays down for the Y. Watch the output for `no floor under landing` on the first walk |
| **`TextMuted` was below the contrast floor** | Fixed 2026-09-20 | It shipped at 3.40:1 against a raised row — under WCAG's 4.5:1 for body text, which a 13px row subtitle is. Found by the new contrast test, not by eye, which is the point. Now 5.06:1 at worst. It is now closer in value to `TextSecondary`, so the two roles lean more on size and letter-spacing than before — worth a look in Studio |
| **Profile schema is now v2** | Note | `RedeemedCodes` and `Settings` were added with a migration. Every existing test save is v1 and migrates on load |
| Placeholder text | Cosmetic | Flavour lines, labels, result card |
| Octagonal plinth is a cylinder | Cosmetic | First thing an authored mesh replaces |
| Training dummies inert | By design | Combat is Phase 2; tagged `Phase = 2` |

---

## 5. Next session — pick up here

> **2026-09-24: enemies have a framework.** `docs/ENEMY_FRAMEWORK.md` +
> `assets/source/enemies/_framework/` build, validate, pose, animate and export every enemy in every biome.
> Sky Citadel's 16 enemies are built and exported (`assets/export/enemies/sky_citadel/`); the Winged Sentinel has
> Idle, the P2 transition and the first moveset attack. Studio wiring (`EnemyDef` + services) awaits the owner's OK.

> **2026-09-23: Sky Citadel is 36 real pieces; atmospheres are live.** All 36
> meshes uploaded and in `AssetManifest`; props and fixtures switched to the
> 36-piece placements (`assets/rbxm/props/SC_PROP_LIBRARY.rbxmx`).
> Every run draws one of seven scenario atmospheres from its seed, or the base
> air (`GameConfig.Ambience.Atmospheres`). In Studio: `/atmosphere <ID|BASE|RANDOM>`.
> The scenario kits themselves are saved, not live: tag `sky-citadel-scenarios-v1`.

> **2026-09-23: the Sky Citadel kit is uploaded and unwalked.** `TESTING.md`
> Test Q is the first time any of those 22 meshes will be stood on, and it is
> where `GroundOffsetY`, the joins and the vertex colours stop being claims.

> **2026-09-22: parties and expedition instances are built and unwalked.**
> Walk `TESTING.md` Test O in Studio (3 clients) first — it needs nothing
> published. Test P needs the place published with API Services on and two
> accounts; it is the only way to see the teleport, the save hand-off and the
> party coming home together.

> **There is a plan now.** `docs/DEVELOPMENT_PLAN.md` lays out the path to a
> real playtest in five phases with exit gates, and says what is deliberately
> being left alone until then. The headline: **the first playtest does not wait
> for combat** — expeditions get a non-combat objective so the loop closes, and
> the biggest single risk to a playtest is that 25% of rolls still land on a
> world with no map. The list below is the pre-plan list and is superseded by
> Phase 0 of that document.

**The core loop is proven.** Roll → Gate → generated map → return → Fate,
walked end to end in Studio on 2026-09-16. What is left is art, content and
two design decisions.

0. **Walk the new UI first — it is the largest unrendered thing in the repo.**
   `TESTING.md` tests I (loading screen), J (hub menu) and K (run + double
   jump), in that order. The three questions that matter most:
   - **Do the five travel destinations land you on the deck?** The Y comes
     from a ray, so watch the server output for `no floor under landing`.
   - **Does the collapse arrow feel like getting your screen back?** That is
     the whole point of it.
   - **Is the rail readable on a phone?** It starts collapsed there on
     purpose; judge whether that is right.

1. **Walk the Crossroads.** The whole hub is now authored and none of it has
   been rendered. In priority order:
   - **Does the floor hold, and do the stairs climb?** The collision set is a
     reasoned guess that cannot be checked headlessly (§4).
   - **Can you reach the market's ENTER prompt?** It sits at `(0, 14, 250)`,
     at the head of the stairs, because its district is a Shop now.
   - **Does anything invisible stop you?** Especially at the four walkway
     mouths, on the spawn approach, and anywhere on the open plaza — those are
     the three places a filled collision hull would do most damage.
   - Then the Engine: the dais landing flush with the walkways, the rings
     counter-rotating, the portal pulsing, and a `/roll` turning the inner
     ring, plane, glyphs and shards to the rolled rarity.
2. **Then colour and animate the Crossroads to match the Engine.**
   Owner-stated as the next step once it is placed. `Crossroads.Shell.Styles`
   is the entire dial — 184 keys, longest-prefix matched — and needs no code.
3. **Walk Ethereal Scape v2.** Entry, lighting, the timer and the return are
   proven — the whole path was walked on v1. What is new is 925 anchored PBR
   parts at play scale. The thing to judge is the traverse: 71 seconds one way,
   142 there and back of a 300-second expedition. If that reads as too much
   walking, `DurationSeconds` is the knob, not `Scale`.
4. **Walk the hub's lighting.** Untested: the brightness pass (`ClockTime`
   22 → 4.5) and the non-colliding SpawnLocation — both now seen against
   authored art rather than grey blockout, which is the first time the
   `ClockTime` choice can actually be judged. `TESTING.md` Test C3.
5. **Add `EntryAnchor` and `ReturnAnchor`** to the scene in Studio. Until then
   the loader guesses the arrival point from the bounding box and warns on
   every entry. (v2 already ships anchored, so that half is done.)
6. **Profile on a real low-end device.** Still never measured, and 225
   MeshParts plus 57 generated collision hulls were just added on top of four
   sessions of animation. `GameConfig.Effects` is reasoned, not measured.
7. **`UNCOMMON`'s colour needs blessing.** On screen inside the first minute.
8. **A chunk kit for Emberfall** — 15pp off the "no map" number.
9. **Placeholder text, UI pass** — unchanged.
10. **Sky Citadel** — art direction and a **22-piece kit**, delivered and uploaded 2026-09-23 (`SKY_CITADEL.md`): turns both ways, one crossroads, a side pocket, no dead ends, and three caps that seal whatever a route leaves open (§7.4). Next: **walk it** — `TESTING.md` Test Q. The open questions are all mesh questions: does `GroundOffsetY = 96` put your feet on the deck, do the joins line up, and do the vertex colours survive `CreateMeshPartAsync`?

### When expeditions move to a separate place

Owner-stated direction, not yet built. When it happens:

- `ExpeditionCore` is **unaffected** — destination, seed, eligibility and
  timer decide the same things wherever the map is built. That is the payoff
  of having kept it pure.
- `ExpeditionSystem.requestEnter` becomes a `TeleportService:TeleportAsync`
  with the seed and world id in `TeleportData`; the map is built by the
  destination place from exactly those two values. Determinism already
  guarantees both ends produce the same layout.
- `ChunkLoader` moves to the expedition place unchanged.
- The Crossroads becomes a lobby. That is part of why the Global Observatory
  was cut: a monument you climb on the way to nowhere is harder to justify in a
  lobby, not easier.

> Before launch, turn **`GameConfig.Debug.AllowCommands`** and
> **`AllowForcedRolls`** off. They are on for testing and the server shouts
> about it on every boot.

### Working agreement that emerged this session

- Small steps with a checkpoint, not ten instructions at once.
- Verify CI is green **before** merging. This was violated once (PR #7) and
  shipped an unbootable `main`.
- `git add` new files explicitly. `git commit -am` silently skips untracked
  files — that is exactly how PR #7 broke.

---

## 6. Environment

- Code: `C:\Dev\luckbound` (not OneDrive — must stay outside it)
- Place: `LUCKBOUND_dev.rbxl`, local, unpublished
- Rojo CLI 7.6.0 via Rokit; Studio plugin 7.7.0
- **Unpublished means no DataStores.** Expected; the server runs in volatile
  mode and says so. Publishing is what enables saving.

### Startup

```powershell
cd C:\Dev\luckbound
git pull
rojo serve
```

Studio → open `LUCKBOUND_dev` → Rojo panel **Connect** → **Accept** → **▶ Play**

---

## 7. Document map

| Document | Purpose |
|---|---|
| `PROTOTYPE_BUILD_SPEC.md` | **Canonical on architecture.** Schemas, remotes, tasks, §7 exclusions and their amendments |
| `STATUS.md` | This file — current state and handoff |
| `TESTING.md` | Running tests, and the Studio manual pass |
| `BLUEPRINT_RECONCILIATION.md` | How the Biome Blueprint merged; open sign-offs |
| `ART_DIRECTION.md` | How to describe the look so it becomes code |
| `TOOLCHAIN_ACCESS.md` | Studio MCP, Rojo, Blender, assets, setup |
| `WORKLOG.md` | **Session history and handoff points — read the top entry** |
| `MODULAR_MAPS.md` | The chunk system: how biome maps assemble from pieces |
| `CHUNK_AUTHORING.md` | **Give this to whoever models a kit.** The engine contract only — universal, no world in it |
| `biomes/<WORLD>.md` | **Give this alongside it.** What that world IS — piece size, kinds of place, connection types, inhabitants |
| `../assets/README.md` | Blender → Roblox asset workflow |
| `ADDENDUM_ASSET_PIPELINE.md` | Future asset/procgen architecture — target design |
| `MASTER_DESIGN.md` | **The design source of truth** — the game, Fate, worlds, the generation layers, what is built vs planned |
| `design/LUCKBOUND_MGD_Original_v0.1.pdf` | Original vision. **Authoritative on intent.** |

`CLAUDE.md` in the repo root holds the rules every AI agent must follow.
