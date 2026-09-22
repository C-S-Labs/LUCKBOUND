# LUCKBOUND — Project Status

**Last updated:** 2026-09-22 · **Phase 1 complete · expedition entry opened (build spec §7.1) · parties + expeditions as their own server (§7.2) · the hub is authored art · the hub has a UI**

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
| Enterable worlds | **Verdant Valley, Ethereal Scape** |
| Rollable but NOT enterable | Emberfall (15%), Sky Citadel (7%), Astral Reach (3%) |
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

**639 tests, all passing.** 65 arrived with parties and expedition instances (§7.2): every party rule, request parsing, who goes through the portal, rebuilding a party after the trip home, and the expedition manifest. Before that: Headless — no Roblox required. 136 of them arrived
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
| **`ChunkCore.exitFor` takes the FIRST valid socket, not a random one** | **High** | A piece with four sockets leaves through the same one every seed, and the entry chunk is hard-coded to `entry.Sockets[1]`. So **authoring more sockets currently buys no extra variety** — what varies is which piece is drawn and which yaw the join implies. Owner-raised 2026-09-22, wanting layouts that differ genuinely per run. The fix is a weighted random pick among the valid exits: small, contained, and it wants its own tests. Not done here — this pass was documentation. |
| **`IncludeSide` is declared and never read** | Medium | `AssembleOptions.IncludeSide` exists and `ChunkCore.assemble`'s own docstring promises "optionally hanging one SIDE pocket off a spare socket". Nothing consumes the field. **`VV_HOLLOW` is authored, validated, and never placed** — the Biome Blueprint §6 side-pocket checklist item is satisfied on paper only. Found 2026-09-22 while answering a question about socket counts. |
| **Unused sockets are never capped** | Medium | The generator consumes one socket to arrive and one to leave; every other opening on the piece faces nothing, and the loader does not close them. With high socket counts — which is what gives a run variety — that is several openings per piece looking onto the void. Today the art has to solve it (`CHUNK_AUTHORING.md`: an opening must read as plausible unattached). A cap piece placed by the loader at unused sockets is the systematic fix and would need a schema field for it. |
| **A chunk's mesh origin must be its footprint centre, and nothing enforces it** | **High** | `ChunkLoader` puts the mesh's origin at the layout centre and rotates about it by a seed-derived `Yaw`, and `ChunkCore.overlaps` checks collisions against centre ± half-size. A corner or edge origin therefore lands the art half a chunk out, by a different amount per rotation, and the generator still certifies the layout as collision-free. It is a **data contract with the Blender file that no test can see** — the origin is invisible metadata, exactly the failure mode that produced the "register a prefab from a NAMED PART, not from its pivot" rule for the hub. Documented in `CHUNK_AUTHORING.md`; the first uploaded mesh is where it gets proven. |
| **A brief that specifies the piece gets the piece it specified** | **Process** | Recorded 2026-09-22 after it happened. The first `CHUNK_AUTHORING.md` was handed to the modeller's AI engine carrying a table of eight footprints (512–1024), a 32-stud flat weld band on every edge, and a 13-item checklist. All three were read as targets: the kit came back at roughly 10× the area with terrain flattened to the boundary and the scatter lost in it, and the better earlier iteration had to be restored from backup. **A number stated in a brief is a number that gets built.** The rewrite states only what breaks the game and says outright that everything else is the modeller's. The general rule for any art brief on this project: **specify the seam, not the piece.** |
| **FBX exported at 1000× — millimetres, not metres** | **Closed 2026-09-22, in the brief** | The first Verdant Valley batch imported at **256,000 studs** against a declared 256. Exactly 1000×, so the FBX was written in millimetres. The brief now names both settings that have to agree (Blender units Metric/Metres/1.0; FBX Transform → Scale 1.00, Apply Scalings `FBX All`) and, more usefully, tells the modeller to **measure one piece in Studio rather than trust the export** — a 256 piece must read 256. The compensating-factor workaround (FBX export scale 0.001) is named and discouraged, because a compensating factor is a thing someone later removes for looking wrong. |
| **Kit target raised to 12–16 pieces** | **Content** | Owner-directed 2026-09-22. This file declares 8 — one per role in the Blueprint progression — and the variety of a run is the variety of the kit, so 8 repeats itself. Extra pieces arrive as **variants of existing roles**, not new roles: several meadows, several groves, weighted so one is common and another rare. Entries get added as each piece is authored; declaring chunks with no art would have the blockout drawing pieces nobody meant. **First delivery is 4** — ENTRY, PATH_STRAIGHT, GROVE, BOSS_CLEARING — the smallest set that assembles a complete walkable map. The Grove has to be among them: the WIDE reservation makes it the only piece offering the exit the arena accepts. |
| **The kit was generated stacked at one point** | Low | Every Verdant Valley piece came back occupying the same spot in the Blender scene. Nothing was broken by it — the exports were correct — but it made the kit impossible to review without hiding objects one at a time, and a piece nobody can see is a piece nobody checks. The brief now asks for a spaced review layout, with the catch stated: **the review position and the export position are different things**, and a piece exported while parked on the review grid arrives that far off in game. |
| **`GroundOffsetY` — the loader needs a ground-level origin and does not have one** | **High** | `ChunkLoader` sets `mesh.Size = (SizeX, SizeY, SizeZ)` and puts that box's **centre** at the layout Y, while the blockout puts the **walking surface** there. The first version of the brief closed the gap by requiring the art to centre its walk plane inside `SizeY` — 170 studs of ground body under the player's feet at `SizeY = 340`. That was the wrong side to bend: **`CHUNK_AUTHORING.md` now asks for a ground-level origin**, which is what an artist would author anyway and what the blockout already assumes. The loader owes a `GroundOffsetY` on the chunk schema to consume it. **This is now a prerequisite for the first mesh upload**, not deferrable debt — nothing is uploaded yet, so there is time, but a piece imported before it lands will sit half-sunk. |
| **Portal plane is still above head height** | Medium | You reach the prompt and the rig springs from the floor, but the walk-through *plane* sits inside the inner ring, ~30 studs up. Blueprint §1.3's concentric rings make that inherent. Irrelevant once the rig is authored in Blender. |
| **25% of rolls land on a world with no map** | **High** | Emberfall 15%, Sky Citadel 7%, Astral Reach 3%. Refused politely at the Gate; printed as a boot warning and asserted by test. Emberfall and Astral Reach need only a chunk kit; Sky Citadel needs a blueprint section first. |
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
| All 8 chunks are `PLACEHOLDER` | Expected | Blockout is deliberate; upload is a per-piece change |
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
10. **Sky Citadel biome** — largest content debt.

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
| `PROTOTYPE_BUILD_SPEC.md` | **Canonical.** Architecture, schemas, remotes, tasks |
| `STATUS.md` | This file — current state and handoff |
| `TESTING.md` | Running tests, and the Studio manual pass |
| `BLUEPRINT_RECONCILIATION.md` | How the Biome Blueprint merged; open sign-offs |
| `ART_DIRECTION.md` | How to describe the look so it becomes code |
| `TOOLCHAIN_ACCESS.md` | Studio MCP, Rojo, Blender, assets, setup |
| `WORKLOG.md` | **Session history and handoff points — read the top entry** |
| `MODULAR_MAPS.md` | The chunk system: how biome maps assemble from pieces |
| `CHUNK_AUTHORING.md` | **Give this to whoever models a kit.** Origin, scale, sockets, independence, export |
| `../assets/README.md` | Blender → Roblox asset workflow |
| `ADDENDUM_ASSET_PIPELINE.md` | Future asset/procgen architecture — target design |
| `MODELLER_HANDOFF.pdf` | **Give this to an artist.** Deliverable formats, export settings, how to build a prefab we can animate |
| `LUCKBOUND_Master_Spec_v0.2.pdf` | Master design spec, updated with build reality |
| `../LUCKBOUND_...v0.1 (1).pdf` | Original vision. **Authoritative on intent.** |

`CLAUDE.md` in the repo root holds the rules every AI agent must follow.
