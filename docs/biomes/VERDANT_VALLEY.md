# Verdant Valley — biome design schema

**Rarity:** Common · **Roll weight:** 5000 (60% of the Phase 1 pool)
**Map route:** chunk kit · **Blueprint:** §3.2

The starting world and the one every player sees first. A sunlit temperate
forest valley — open meadows, a stream, dense groves — that reads as safe and
becomes less so toward the north. It is the world the onboarding arc returns to
between lifts, so it has to be pleasant to be in repeatedly rather than
striking once.

---

## 1. Palette and light

Lives in `Content/Worlds/VerdantValley.luau` → `Environment`. Blueprint §3.3:
soft midday, dappled canopy light.

| | |
|---|---|
| Ambient | `90, 100, 70` |
| Outdoor ambient | `120, 130, 100` |
| Sky shift | `150, 170, 120` |
| Fog | `180, 200, 160`, 100 → 400 |
| Brightness / clock | 2.5 · 13:00 |

Mesh materials in the delivered kit: `Verdant_Grass`, `Path_Stone`,
`Tree_Trunk`, `Canopy_Light`, `Canopy_Leaf`, `Wildflower`. Flat colour, no
textures — the house low-poly style in `ART_DIRECTION.md`.

**Modifiers:** `NORMAL` and `NIGHT`. Night re-tints; it does not build separate
geometry. This world's `ModifierOverrides` is the reference example.

---

## 2. The kinds of place

**This is the section that decides how varied a run feels**, and it is
deliberately open-ended. Twelve to sixteen distinct kinds of place is the
target. A new kind of place is welcome at any time and needs no permission —
it is a piece of content, and adding one changes no System.

**The kit as built: 30 pieces** (2026-09-24, PR #105) — walked in Studio, but the owner has flagged the kit for a
revamp pass (see `docs/STATUS.md` §4). All pieces are in one file,
`assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx`. The code entries are in `src/shared/Content/Chunks/VerdantValley.luau`
(ids `VV_<NAME>`, asset keys `VV_CHUNK_<NAME>`), and the exporter is
`assets/source/worlds/verdant_valley/export_verdant_valley_kit.py`. The 2026-09-22 first-pass test kit
(`chunk_path_straight`, `chunk_meadow_a`, `chunk_waterfall`…) was retired in the 2026-09-25 audit.

**Current Verdant Valley collision architecture (2026-09-30):** all 30 chunks
use saved separated structure, solid/nonsolid props and dedicated walk collision.
`VV_COLLISION.rbxmx` contains 29 named child templates with 3,915 MeshParts,
including Cliff Passage (66) and Cutbank Ford (137). Stone Sentinels uses its
separate 118-part merged template: 4,033 active colliders in total. The original
202-part Stone template is rollback material, outside the active selection.
`CollisionTemplate` lookup disables visual terrain collision only when the named
model is found; cloned colliders rotate with each chunk's calibrated art frame.
ChunkLoader sets the clone's transparency and physics flags at runtime.

The prop library contains 823 meshes: 30 solid groups, 30 nonsolid groups,
746 canopies and 17 specials. The 39 colliding placements are server-owned
Static/Tier 1 props; nonsolid groups and canopies remain client ambience.
Saved per-chunk yaw and placement corrections are authoritative. Old exporter
or collision-generator defaults cannot reconstruct this production snapshot.

The 28-template generation reports, Stone pilot and first Cliff candidate below
in the import history describe earlier iterations. Current counts come from the
refreshed export ledger and saved templates. Run the read-only collision verifier;
serialized physical configuration without explicit fidelity tokens requires
Studio inspection and traversal after Rojo sync. Retain earlier assets until
those checks and CI establish safe replacement.

| Role | Pieces |
|---|---|
| `ENTRY` (2) | `chunk_entry_dawn_meadow` · `chunk_entry_woodland_refuge` |
| `PATH` (5) | `chunk_path_sunwash_fork` · `chunk_path_cliff_passage` · `chunk_path_narrow_pass` · `chunk_path_split_meadow` · `chunk_path_crossroads_copse` |
| `COMBAT` (18) | `chunk_cutbank_ford` · `chunk_windward_ridge_gate` · `chunk_forgotten_orchard_gate` · `chunk_longgrass_meadow` · `chunk_shaded_grove` · `chunk_fern_hollow` · `chunk_stone_sentinels` · `chunk_mossbound_ruins` · `chunk_ancient_oak` · `chunk_wetland_pools` · `chunk_blossom_terrace` · `chunk_rock_garden` · `chunk_crystal_spring_gate` · `chunk_overgrown_causeway_gate` · `chunk_high_ledge_gate` · `chunk_cliff_overlook_gate` · `chunk_deep_clearing` · `chunk_mushroom_glen` |
| `SIDE` (1) | `chunk_side_forgotten_trial` |
| `CAP` (3) | `chunk_cap_cave_mouth` · `chunk_cap_treasure_hollow` · `chunk_cap_wardens_clearing` |
| `BOSS` (1) | `chunk_boss_sanctuary` |

**Roles are a routing concept, not a design one.** Every piece carries one of
`ENTRY` / `PATH` / `COMBAT` / `SIDE` / `CAP` / `BOSS` so the assembler knows where it is
allowed to put it. That is all a role means. A ruin and a mushroom glen can both
be `COMBAT` and be nothing alike, and the world is more varied for it.

The only counts the engine insists on: **at least one `ENTRY`, at least one
`BOSS`**, and at least one connective piece. Everything else is free.

**2026-09-27 cap variety:** Treasure Hollow and Warden's Clearing are now caps,
alongside Cave Mouth; Forgotten Trial remains the optional side pocket. All three
caps are equally weighted and unlimited per layout, following the owner's corrected
direction. Their geometry, sockets, scenario support and mesh IDs are unchanged.

**Historical 2026-09-28 separated candidate (superseded by the saved production set above):** the reviewed 30-piece source has been
partitioned into 30 connected terrain meshes and 66 tagged prop meshes in
`verdant_valley_separated.blend`. Props use `prop_*` names; the two former
`chunk_side_*` cap meshes use their current `chunk_cap_*` names. Solid scenery
and detached walkable surfaces are server placements; water, foliage and small
details remain client ambience. New FBXs and candidate placement/size tables
are staged under `assets/export/worlds/verdant_valley/`. At that stage no new IDs or live
chunk sizes were active. This candidate is not an instruction to replace the
current saved production assets.

---

## 3. How pieces connect

Verdant Valley's connection types:

| Type | Meaning |
|---|---|
| `PATH` | An ordinary forest opening. The connective type — most pieces offer it |
| `WIDE` | A broad approach. **The arena accepts only this** |

Openings are centred on an edge midpoint and are 42–50 studs across in the
delivered kit. A piece may have an opening on any side it leaves open, and no
opening on a side the art closes.

Wetland Pools' reviewed Blender mesh has both mouth surfaces at the same
walk-plane height. Keep both socket `OffsetY` values at zero: unequal values
move every later chunk vertically. Studio raycasts on the uploaded MeshPart can
hit its convex collision hull above the visible path; check the visible mesh
and collision separately before changing socket positions.

### The consequence worth understanding

Because the arena accepts only `WIDE`, any piece that offers a `WIDE` exit
becomes a possible approach to the boss — and a piece offering `WIDE` is never
spent mid-path, because the assembler reserves arena types. Today the Grove is
the only `WIDE` provider, so **the Grove precedes the boss on every single
seed.** That was the intent when the kit was eight pieces and the Blueprint
called for Elder Treants gating the approach.

**With twelve pieces it is now the single largest limit on variety**, and the
fix is content: give `WIDE` to two or three pieces that deserve to be the last
thing before a boss — the Grove, the Ridge Overlook, the Ruins — and the
approach varies per run while still always being a deliberate one.

---

## 4. Inhabitants

`Content/Worlds/VerdantValley.luau` → `Enemies`, `BossId`.

| Enemy | Where it belongs |
|---|---|
| `MOSS_SLIME` | Entry, early path — the tutorial enemy |
| `THORN_GOBLIN` | Stream, hollow — camps and ambushes |
| `FOREST_WOLF` | Meadows — packs, open ground |
| `ELDER_TREANT` | Grove — slow, heavy, gates the approach |
| `ROOTBOUND_GUARDIAN` | Boss clearing |

Declared per piece as `EnemyTags`. **Nothing consumes them yet** — enemy
population is not built. The tags are the design being recorded ahead of the
system that will read them.

Loot `LOOT_VERDANT` · discoveries `DISC_VERDANT`.

---

## 5. Piece size and count

| | |
|---|---|
| Piece footprint | **256 × 256 studs**, uniform |
| Height | Free. Delivered kit runs 42–77 studs |
| Kit size | 12 delivered; 12–16 is the target |
| Path length | 5 (`GameConfig.Expedition.PathLength`) |

256 was arrived at by bracketing: an earlier iteration at ~100 studs read too
tight to be a place, and one at ~1024 was so open the scatter disappeared into
it. **It is a number in a content file and it is meant to move** if a real
piece reads wrong on the ground.

At 256 and path length 5 a map spans ~1536 studs — about 48 s of walking in a
720 s expedition, which is a lot of slack. `PathLength` is the knob and is worth
retuning once a real piece has been walked, not before.

---

## 6. What each piece can support

The scenario-compatibility gate (build spec §7.3). Deliberately not universal —
a traversal challenge in a flat meadow is not a challenge, and a mini-boss in a
corridor is not an arena.

| Piece | Supports |
|---|---|
| `VV_PATH_STRAIGHT` | Combat, Traversal, Ambush |
| `VV_MEADOW_A` | Combat, MiniBoss, Treasure, Ambush |
| `VV_MEADOW_B` | Combat, MiniBoss, Ambush, Shrine |
| `VV_STREAM_CROSSING` | Combat, Traversal, Ambush, Event |
| `VV_MUSHROOM_GLEN` | Combat, Shrine, Event, Secret, Puzzle |
| `VV_FERN_HOLLOW` | Combat, Puzzle, Treasure, Secret, Ambush |
| `VV_RUINS` | Combat, Puzzle, Treasure, MiniBoss, Secret, Event |
| `VV_WATERFALL` | Combat, Traversal, Secret, Shrine, Event |
| `VV_RIDGE_OVERLOOK` | Combat, Traversal, Ambush, Shrine, MiniBoss |

`VV_ENTRY` and `VV_BOSS_CLEARING` declare none and are never assigned a
scenario — arrival should be calm and the arena is already the biggest thing in
the run.

**Measured: 50 distinct chunk/scenario rooms from 11 pieces**, across 174
distinct layouts in 200 seeds.

---

## 7. Settled, and what is still open

### Settled 2026-09-22, when the kit was delivered

- **`WIDE` now sits on Ruins, Waterfall and Ridge Overlook.** The Grove was the
  only provider and did not survive the upload (14,448 triangles against a
  10,000 cap). Three providers keep the gate — the arena is still only
  approached deliberately — and the approach now varies ~35/35/30 per seed
  instead of being the same room every time.
- **The entry opens south.** The art decided; the data moved to match.
- **There is no side pocket, and there cannot be one yet.** Every delivered
  piece has exactly two openings, the critical path spends both, so no seed
  leaves a spare socket for a branch. Fern Hollow became a `COMBAT` piece.
  `Schema.validateChunks` now refuses a kit that declares `SIDE` without a
  3-socket piece, rather than letting a pocket validate and never appear.

### Still open

- **The Grove.** It needs decimating under 10,000 triangles and re-uploading.
  Its absence costs a kind of place, not a working kit.
- **A three-opening piece**, if this world is to have the optional branch
  Blueprint §6 asks for. A T-junction or a crossroads clearing. This is a
  request for the modeller, not a code change.
- **Encounter and reward configuration.** A plan says a room is an Ambush;
  nothing spawns it. Build spec §7 still excludes that.

---

## 8. The 30-piece base kit (2026-09-24)

The kit was redelivered as 30 pieces in one `.blend`, laid out 5 × 6. It is exported and wired by
`assets/source/worlds/verdant_valley/export_verdant_valley_kit.py`. That folder's
[`IMPORT_STEPS.md`](../../assets/source/worlds/verdant_valley/IMPORT_STEPS.md) has the piece table and upload steps.

- **The sockets were redone from the geometry.** The .blend's own socket labels put N on Blender −Y but E on +X.
  That is a mirror, not a rotation, so on the bends (Orchard, the six gates) no turn of the mesh could match them.
  The script ray-casts each edge for the flat mouth pad instead (48 studs wide = `PATH`, 52 = `WIDE`).
  It refuses to export if a measurement disagrees with its table.
  After the N/S flip, every piece's openings matched what the art intended.
- **Roles.** 2 ENTRY (Dawn Meadow, Woodland Refuge), 1 BOSS (Sanctuary, 384 × 256),
  1 CAP (Cave Mouth), 3 SIDE (Treasure Hollow, Warden's Clearing, Forgotten Trial),
  6 PATH, 17 COMBAT.
  **Six pieces offer `WIDE`**, so a run's arena approach is spread evenly between them.
  Five pieces are 3- or 4-way junctions, so side pockets now actually attach.
  That closes §7's "Verdant Valley cannot host a SIDE pocket".
- **Names follow `CHUNK_DROP_IN.md`** (`chunk_entry_*`, `chunk_side_*`, `chunk_cap_*`, `chunk_path_*`, `*_gate`),
  so the same FBX would also load as a drop-in kit.
  The hand-written module is kept because drop-in collapses every opening to one Kind,
  and that would lose the `WIDE` gate.
- **Engine contract, checked by the script:**
  - every footprint is exactly 256 (the boss 384 × 256), centred on the origin
  - every mouth sits at ground height 0 ± 0.35
  - 7,288–9,970 triangles per piece, under the 10k cap
  - material colours are baked to vertex colour (one mesh per piece)
  - `MeshYawOffset = 180`, the half turn Sky Citadel's identical export landed at;
    `calibrateYaw` measures the real turn per piece
- **Supports, EnemyTags and Weights are proposals.** They are read from each piece's theme and live in the script's `EXPECTED` table.
- 200/200 seeds assemble into 200 distinct layouts, and every one of the 30 pieces appears.
  **Not yet uploaded or walked in Studio.**



## 9. Composition review (2026-09-29)

**Export preparation (2026-09-30):** ordinary props are now consolidated by
their existing chunk-name prefixes into one `PropsSolid` and one `PropsNonSolid`
per chunk, inside the original collections. All 749 canopy objects and the
12 components of the three openable chests retain their geometry, transforms
and pivots. Six concrete review objects remain separate. Structure, dedicated
collision and Temp are unchanged. See
[`PROPS_EXPORT_REVIEW.md`](../../assets/source/worlds/verdant_valley/PROPS_EXPORT_REVIEW.md)
for all 30 chunk counts and outputs; the adjacent JSON accounts for every source.
Keep `VerdantValley_Props_Export_Input.blend` until owner Blender and Studio
import/material/pivot checks pass. Production exports have not been replaced.

The current live authoring source is `E:/BlenderAIProjects/Projects/VerdantValley_Cleanup.blend`.
The following composition record describes the earlier `VerdantValley_Extra_Details_Backup.blend` pass.
Treasure Hollow, Longgrass Meadow, Deep Clearing and Warden's Clearing are finished,
protected density/style references. The remaining 26 chunks were reviewed individually;
24 received restrained Temp-based shoulder/landmark dressing and minor identifying
features. Cliff Passage and Cave Mouth already read intentionally and remain unchanged.
Large uninterrupted grass areas are deliberate. Collision, terrain, sockets, connectivity
and primary landmarks were preserved. Owner Blender review precedes production export.

The per-chunk record, verification and cleanup handoff live in
[`COMPOSITION_REVIEW.md`](../../assets/source/worlds/verdant_valley/COMPOSITION_REVIEW.md).

Owner review corrected the too-compact initial planting: 319 props redistributed into
wider uneven shoulder groups and 386 linking props added (746 total across 24 chunks).
Original geometry and identifying details stayed fixed. Current renders: `Composition_Spread/`
beside the live source; clustered rollback retained pending review.

Owner-authorized exception to reference protection: refine only Longgrass Meadow's
flowering tree into a secondary centerpiece. Its seven-lobed crown carries 49 readable
muted pink/cream flowers; tapered pale branches and roots replace the simple beams.
Original placement, surrounding dressing, terrain and collision stay fixed. Removed
the two flowering-tree sources from Temp (six props remain). `refine_flowering_tree.py`
seats bark marks on the actual tapered trunk faces, avoiding detached floating etchings, and
records the targeted operation; `Flowering_Tree_After/` contains overhead/feature/whole
chunk previews. Keep `VerdantValley_Flowering_Tree_Input.blend` until owner visual and
eventual Studio checks confirm replacement; then remove that rollback if unneeded.

Earlier owner-edited reference (2026-09-29): `VerdantValley_Geometry_Review_Reference.blend`.
Read-only review of all 30 chunks is recorded in
[`GEOMETRY_REVIEW.md`](../../assets/source/worlds/verdant_valley/GEOMETRY_REVIEW.md).
Four floating details and solid prop intersections are pending owner-directed correction;
no scene geometry changed during this review. Preserve current owner edits when fixing
findings; earlier generated placements are historical rather than the current reference.

Owner manual cleanup and landmark refinement (2026-09-29): retained the owner's latest
7,946-object scene as `VerdantValley_Landmark_Refinement_Input.blend`, with an input manifest.
The earlier geometry report predates these manual adjustments and must not be treated as
the current placement reference. `refine_chunk_landmarks.py` made only the requested changes:

| Chunk | Changes |
|---|---|
| Ancient Oak | Tapered aged trunk, branching forks and short broken limb, ten varied canopy lobes, bark seams/knot seated on trunk faces, small moss patches on existing roots. Existing root meshes and surrounding composition retained. |
| Treasure Hollow | Rebuilt its plain chest as a planked wooden chest with domed lid, continuous metal hoops, corner shoes, hinges, side carry rings, rivets and brass lock. This is the owner's explicit exception to finished-reference protection. |
| Cave Mouth | Same chest model as Treasure Hollow, feet seated into ground. Reassigned 167 covered ground faces to `VV_CaveFloor`; terrain vertices/topology and cave structure unchanged. |
| Crossroads Copse | Removed center obstacle and marked northeast props (16 objects total). Added open timber roof shelter, low broken stone walls, grounded footings/step, and the same chest facing west toward the route. All structure/chest bounds lie within the non-path shoulder. |

Final source has 7,937 objects. All 7,920 unrelated input objects match their geometry,
transform, materials and collection hashes; collision and sockets are unchanged. The cave
floor's exact vertex/face data also match. `Landmark_Refinement_Record.json` beside the source
records edits/removals/additions, protected count and chest seating. `Landmarks_After/` contains
saved-source overhead and feature renders. Owner Blender review and later Studio checks
remain. Retain the landmark input, earlier review references and automatic `.blend1` rollback
until approved replacement and Studio checks; then remove obsolete previews/backups if unneeded.
Production meshes, exports and manifest entries were not replaced in this pass.

Owner chest/shelter follow-up: all three chests now use 0.7912 scale (14% reduction,
then another 8% on the owner's follow-up; approximately 21% smaller overall). Their side-end lid
panels have horizontal planks, metal edge trim and a riveted cross strip. The body is
a hollow four-wall box with a plank floor; the lid is a hollow arch shell, not a solid
filled volume. A small tied sack sits on the floor. Every moving lid detail is in its
lid mesh, whose origin is the rear hinge (local X; -105 degrees for the reviewed open
pose). Closed source is saved; animations, rigging and runtime loot integration remain
for later as requested. Existing locations were retained and feet regrounded.

Crossroads' shelter now sits at chunk-local (56,56), rotated -45 degrees so the entrance
faces southwest toward the junction, matching the marked reference orientation. Its
footings and entry step were refitted to existing terrain. Two varied existing tree
assemblies and 13 reused Temp rock/bush/tuft props frame the sides and back; the front
approach and four paths stay clear. Final count is 7,959 objects; all 7,925 unrelated
input objects match hashes, including Ancient Oak, all terrain/collision and sockets.
`VerdantValley_Loot_Chest_Input.blend`, `Loot_Chest_Refinement_Input_Manifest.json`,
`Loot_Chest_Refinement_Record.json` and `Loot_Chest_After/` preserve this iteration's
input, operation and closed/open/overhead evidence. Keep those and earlier rollback
sources until owner review and later Studio checks, then remove superseded artifacts
if unneeded. No production files, exports or manifest entries were superseded.

Interior-only follow-up: added 20 broad inner wall planks using the exterior's
spacing and wood tones. The sack retains its geometry, but is rotated onto its
side, shifted off-center and settled 0.02 canonical stud into the plank floor.
Only three body meshes and three sack meshes changed. All old body vertices/faces
and outer bounds, lids/pivots/hardware and 7,953 unrelated objects remain unchanged;
the approved closed exterior render is pixel-identical. `--interior-refinement`
records this targeted edit; `Chest_Interior_After/` has open/closed previews and
`Chest_Interior_Refinement_Record.json` the preservation result. Keep the new
`VerdantValley_Chest_Interior_Input.blend` rollback and earlier references until
owner review and eventual Studio checks, then remove obsolete artifacts if unneeded.
No production assets, exports or manifest entries were replaced.

Lid seam correction: closed the five narrow gaps between roof planks on each of
the three chests, extending only their internal X edges by 0.02 canonical unit.
Outer dimensions, all remaining lid vertices, bodies, interiors, hinges and other
7,956 scene objects are unchanged. The original generator now uses touching panel
edges. `Lid_Seam_Refinement_Record.json` and `Lid_Seam_After/lid_closed.png` record
the correction; keep `VerdantValley_Lid_Seam_Input.blend` until owner approval and
eventual Studio checks, then remove obsolete rollback/previews if unneeded.

Crossroads shelter support/stone correction: extended its four upright posts into
the rafters and added front/back king posts between headers and ridge. Roof and
all original timber geometry/placement remain fixed. Replaced plain stone boxes
with seated courses and softened corners, flagstone paving, segmented step and
layered footings, preserving wall/footing envelopes and finished floor elevation.
Only two meshes changed; all other 7,949 objects in the owner's latest 7,951-object
scene match hashes. `--shelter-support` records the operation; close/front evidence
is in `Shelter_Support_After/` and `Shelter_Support_Refinement_Record.json` beside
the source. Retain `VerdantValley_Shelter_Support_Input.blend` and earlier rollbacks
until owner review and eventual Studio checks, then remove obsolete artifacts if
unneeded. No production assets, exports or manifest entries were replaced.

Windward Ridge patch correction: the central fan pinched uneven boundary heights
into radiating humps. `--windward-patch` adjusts 527 local terrain vertices onto a
fitted ridge slope within radius 16 and feathers to unchanged terrain at radius
32, retaining topology, materials and transforms. All 7,932 unrelated objects
match the owner's retained input; close render reviewed. Blender approval and
eventual Studio/export/collision alignment checks remain. Keep
`VerdantValley_Windward_Patch_Input.blend` and `Windward_Patch_After.png` until
those pass, then remove obsolete rollback/previews if unneeded. Production
exports and manifest entries were not replaced.
