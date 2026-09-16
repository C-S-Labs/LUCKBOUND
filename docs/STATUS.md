# LUCKBOUND — Project Status

**Last updated:** 2026-09-16 · **Phase 1 complete · expedition entry opened (build spec §7.1)**

> **New conversation?** Read `WORKLOG.md`'s top entry first for where the last
> session stopped, then this file. `CLAUDE.md` has the rules.

Start here. This is the handoff document: what exists, what is decided, what is
open, and where to pick up.

---

## 1. Where the project stands

Phase 1's goal was one sentence: *you can walk around a recognizable LUCKBOUND
hub and press ROLL.* That is done, running in Roblox Studio, and playtested.

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
| Map | `ChunkCore` assembles, `ChunkLoader` builds, seeded per expedition |
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

**Two kits now exist, and the second one is the interesting result.** Ethereal
Scape's was authored against the checklist rather than against Verdant Valley,
with its own socket vocabulary (`SPAN`/`RITE` vs `PATH`/`WIDE`) — and the same
emergent gate-to-the-boss property fell out of it. Nobody wrote that rule; it is
the reserved-Kind rule generalising. See `MODULAR_MAPS.md`.

All 16 pieces are `PLACEHOLDER`, so the loader draws **labelled blockout** —
each platform carries its ChunkId and Role, with a neon post at every socket
coloured by Kind. **A generated map is verifiable by eye before any mesh
exists.**

### Test suite

**301 tests, all passing.** Headless — no Roblox required.

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
                     ExpeditionCore
src/shared/Util/     WeightedRandom, Schema, PortalRig, ChunkCore, ChunkLoader
src/shared/Content/  Worlds/ (6), Hub/Crossroads, Chunks/ (2 kits), AssetManifest
src/server/          init.server + Systems/ (Save, Progression, Fate, Event,
                                             Expedition, HubBuilder)
src/client/          init.client + Controllers/ (State, Proximity, HubEffects,
                                                 Expedition)
                                 + UI/ (FateRoll, GlobalAnnouncements, ExpeditionHud)
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

**Ethereal Scape** is the first world with authored art behind it —
`assets/source/worlds/ethereal_scape/aether_environment_refined.blend`, a sky
temple above the cloud deck: eight gold-rimmed meadow islands, bridges between
them, seven waystones, and an R6 rig in a `Scale_Reference` collection so the
metre-to-stud conversion can be checked rather than assumed. Its eight chunks
map 1:1 onto those eight islands. It declares **no enemies, boss or loot on
purpose** — it is the map-generation test biome, and giving it combat content
would make it a worse test.

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
| — | **Expedition entry is open; combat/loot are not** | spec §7.1 |
| — | Destination = the player's last roll. No new state, no schema bump | `ExpeditionCore` |
| — | Biome lighting is applied **per client**, never by the server | Blueprint §6 |
| — | Rarity colour is a UI/portal contract; biome palette is set dressing | Blueprint §4.1 |
| — | Compass mapping N=-Z, E=+X, S=+Z, W=-X, up=+Y | GameConfig.HubLayout |

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
| **Portal plane is still above head height** | Medium | You reach the prompt and the rig springs from the floor, but the walk-through *plane* sits inside the inner ring, ~30 studs up. Blueprint §1.3's concentric rings make that inherent. Irrelevant once the rig is authored in Blender. |
| **25% of rolls land on a world with no map** | **High** | Emberfall 15%, Sky Citadel 7%, Astral Reach 3%. Refused politely at the Gate; printed as a boot warning and asserted by test. Emberfall and Astral Reach need only a chunk kit; Sky Citadel needs a blueprint section first. |
| **The Observatory's purpose is undecided** | **Design** | Its only content is the orrery — a global-state display. If expeditions move to separate places (below), the hub becomes a lobby and that display arguably matters *more*. But 145 studs of climb for a look-out is a poor trade, and it cannot simply be lowered: sitting above the Engine forces it above the rig's 111-stud crown. **Recommendation: if it survives, move it off-centre to a sixth compass point rather than lowering it.** |
| **Expeditions are to become a separate place/instance** | **Architecture** | Owner-stated 2026-09-16: worlds will be rendered in a separate instance and reached by `TeleportService`, for performance and to isolate parties and solo queues. The current in-place `ExpeditionStage` is therefore a **prototype of the loop, not of the deployment**. `ExpeditionCore` is unaffected — it decides destination, seed and eligibility, none of which care where the map is built. `ExpeditionSystem` and `ChunkLoader` are what would move. |
| Fate-on-completion may become currency or loot | Design | Owner-flagged: a completion bonus drawn from an item pool, or a currency for upgrades, rather than flat Fate. `ProgressionSystem.award` is the single seam. |
| `UNCOMMON` colour unsanctioned | Medium | Now shipping — see above |
| Chunk collision is XZ-only | Medium | Blocks any kit that climbs. `MODULAR_MAPS.md` |
| No pathfinding validation | Medium | Non-overlapping ≠ walkable between. Addendum §A4 step 4 |
| All 16 chunks are `PLACEHOLDER` | Expected | Blockout is deliberate; upload is a per-piece change |
| **First authored asset delivered, not yet wired** | **Open** | `assets/rbxm/worlds/ethereal_scape/` — 699 MeshParts, all with real uploaded mesh ids. Needs anchoring, a PrimaryPart, a scale confirmation, and a decision on one-scene-vs-eight-chunks. See the README beside it. |
| **Ethereal Scape: one scene or eight chunks?** | **Design** | The kit was built for eight generator-fed pieces; the delivery is one pre-arranged scene. Both work. Picking the first retires the socket grammar for this world. |
| UI needs resize/layout pass | Cosmetic | Owner-flagged |
| Placeholder text | Cosmetic | Flavour lines, labels, result card |
| Octagonal plinth is a cylinder | Cosmetic | First thing an authored mesh replaces |
| Training dummies inert | By design | Combat is Phase 2; tagged `Phase = 2` |

---

## 5. Next session — pick up here

**The core loop is proven.** Roll → Gate → generated map → return → Fate,
walked end to end in Studio on 2026-09-16. What is left is art, content and
two design decisions.

1. **Walk the hub once.** Three changes landed untested: the Observatory
   approach (NE diagonal, crosses no walkway, Engine plaza clear), the
   brightness pass (`ClockTime` 22 → 4.5), and a non-colliding SpawnLocation.
   `TESTING.md` Test C3.
2. **Answer the two open questions** in §4 — the Observatory's purpose, and
   one-scene-vs-eight-chunks for Ethereal Scape. Both gate real work.
3. **Confirm the Ethereal Scape scale** with the modeller (the R6 proxy reads
   12× oversized; the evidence says the proxy is wrong, not the scene).
4. **Wire the authored asset in** — now unblocked: `meshOrNil` works and
   `ensureContract` protects the hub. Needs `assets/rbxm` in
   `default.project.json` and the shape decision from (2).
5. **`UNCOMMON`'s colour needs blessing.** On screen inside the first minute.
6. **A chunk kit for Emberfall** — 15pp off the "no map" number.
7. **Placeholder text, UI pass** — unchanged.
8. **Sky Citadel biome** — largest content debt.

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
- The Crossroads becomes a lobby, which is what makes the Observatory question
  in §4 worth answering first.

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
| `../assets/README.md` | Blender → Roblox asset workflow |
| `ADDENDUM_ASSET_PIPELINE.md` | Future asset/procgen architecture — target design |
| `MODELLER_HANDOFF.pdf` | **Give this to an artist.** Deliverable formats, export settings, how to build a prefab we can animate |
| `LUCKBOUND_Master_Spec_v0.2.pdf` | Master design spec, updated with build reality |
| `../LUCKBOUND_...v0.1 (1).pdf` | Original vision. **Authoritative on intent.** |

`CLAUDE.md` in the repo root holds the rules every AI agent must follow.
