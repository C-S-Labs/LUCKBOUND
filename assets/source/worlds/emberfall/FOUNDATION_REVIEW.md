# Emberfall — revised terrain foundation prototype

**Historical input review:** the same saved scene now has the focused
naturalization pass described in `NATURALIZATION_REVIEW.md`. The counts and
images below describe the retained `Input_Naturalization.blend` baseline.

Owner-directed small Blender study, 2026-10-03. The revised
`docs/biomes/EMBERFALL.md` is authoritative; the old scene is a reuse source.
**Visual result is partial. Ready for Blender review; not ready for Studio.**

## Open the result

- Scene: `E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/EmberfallFoundation.blend`
- Contact sheet: same folder, `foundation_contact_sheet.png`; 17 individual views.
- Reproducible build: `build_emberfall_foundation.py`, then
  `review_emberfall_foundation.py`, both through `tools/run_blender.py`.
- Counts and saved geometry: `foundation_technical_report.json` here and beside
  the scene. All numbers below come from the saved study, not production assets.

## Requested design review

| Topic | What this study establishes |
|---|---|
| Old assets reused | Four original flora species, surviving rosette, 30/50/70% rosettes, partial seed shrub and invasive root bloom: ten mesh assets, exact fingerprints retained. Six connected basalt-column components extracted from the saved PATH mesh; selected components reused at reduced scale. Local-origin collections and separation of solid decoration/flora retained as lessons. |
| Old terrain rejected | No old warped-plane foundation, smooth hills/bowls, fractured-crust overlay fields, debug route strips, prior lava shader or prior pool-per-major-chunk arrangement. The old source was not edited. |
| New construction | Unequal authored cross-sections form a welded solid mesh. Shelf tops, paired lips/feet, steep exposed faces, lower ledges, slumped sections and peeled shoulders are topology in that mesh. No smoothing modifier or terrain displacement shader. This is a new method study, not a final authoring standard. |
| Macro | Broad ash route, interrupted ridges and shelves, a 56-stud causeway ascent and continuing raised gateworks. Combat keeps a broad apron; the side entrance is level and points into its pocket. |
| Meso | Partial ledges, unequal shelf-height sequences, exposed strata, asymmetric bank breaks and uplifted crust edges in the terrain mesh. Rooted basin remnants continue down below the molten surface. |
| Micro | Sparse reused plants, roadside masonry, broken paving and fence remnants. No additional scatter carpet to conceal terrain. |
| Lava mix | ENTRY, COMBAT and first FORTRESS chunk: no open lava. PATH: narrow channel. SIDE: small vent pocket. Transition: heat seam under a lip. Exactly one broader basin in the visible scenery arrangement. |
| Lava material | Object-space, directionally stretched low-frequency flow forms, restrained color bands from cool red-brown to hot amber, and vertex-painted dark edge cooling. No image tiling or fine noisy bump. Close, bank-distance and overview views provided. Material remains a Blender-only study and needs owner review; it can read too flat/graphic. |
| No-open-lava example | `entry_wasteland_waystone`: ash, sparse stressed/drained plants, basalt shelves, broken road and leaning marker. |
| Narrow feature | `path_wasteland_fault`: lava traces the embedded irregular trench; banks are terrain faces rather than separate wall props. Corrected review camera frames the actual surface. |
| Broad feature | `scenery_low_lava_terrain`, instanced east of the SIDE: asymmetric widened trench/basin with cooled perimeter and three buried-root crust remnants. Only one visible broad instance. This still needs more local bank interruption and overhang work. |
| Civilization foreshadowing | Leaning waystone, fallen marker, short half-buried foundations/walls, charred fence remains and intermittent paving. Architecture increases toward the ascent. |
| Middle-zone choice | FALLEN FORTRESS only. Wasteland remains lead to broken causeway walls, fallen lintel/stairs and then unequal, heavily incomplete gateworks. No whole castle, village or boss arena. |
| Persistent elevation | Transition origin is at +28; local entrance/exit are -28/+28, giving world 0→56. Next chunk stays at +56. Broad ramp spans approximately 208 studs, about 15 degrees. |
| Scenery transition | Eight source families reused in 18 local ring placements. Lower ashland/ruined outskirts become elevated shelves, masonry and fortress silhouettes toward the raised zone. Ring cells alongside the ascent follow its datum. Distant apron/ridges are contextual review scenery, not a complete production ring. |
| Glow minimized | Four matched views disable all Principled emission; lava/heat-seam base color is also changed to charcoal temporarily. Original shader connections, colors and emission restored before final save. Broken geology, ruins and infected flora remain readable locally. **Macro identity gate is partial:** repeated longitudinal shelf rhythm and plain aprons still look synthetic and generic in the overview. |
| Before Studio | Reduce the remaining ribbon-like geology, refine overly planar banks/coarse masonry and review lava color bands. Then establish simplified walk collision and resolve the existing generic vertical-socket measurement limitation. No Studio import or traversal claimed. |

## Measured playable assets

All footprints are **256 × 256 studs**. Every terrain object has local origin
`(0,0,0)` under its centered ground-datum parent. Coordinates below are Blender
`X,Y,Z` (Z is up); the SIDE parent turns 90 degrees to face its west join.
Object counts include the parent empty; triangle totals include all local flora
and decoration before bevel evaluation, not a proposed joined export.

| Chunk | Parent origin X,Y,Z | Delta | Objects | Base triangles | Terrain triangles |
|---|---|---:|---:|---:|---:|
| ENTRY waystone | 0,-512,0 | 0 | 23 | 8,070 | 578 |
| PATH fault | 0,-256,0 | 0 | 26 | 8,154 | 578 |
| COMBAT broken road | 0,0,0 | 0 | 38 | 26,514 | 578 |
| SIDE outskirts pocket | 256,0,0 | 0 | 39 | 26,534 | 578 |
| Transition causeway | 0,256,28 | +56 | 61 | 26,790 | 578 |
| FORTRESS gateworks | 0,512,56 | 0 | 129 | 16,416 | 578 |

## Scenery source assets

Each source footprint is 256 × 256 at local origin `(0,0,0)`, in a disabled
library collection. Placement parents provide rotation and ground datum; ascent
placements adapt their terrain and decoration to the shared elevation profile.

| Family | Objects | Base triangles |
|---|---:|---:|
| Open ashland | 10 | 5,374 |
| Ruined outskirts | 15 | 5,434 |
| Broken ridge/shelf | 10 | 5,374 |
| Low lava terrain | 14 | 5,530 |
| Ash faultland | 10 | 5,374 |
| Infected outskirts | 14 | 17,082 |
| Fortress silhouette | 49 | 10,610 |
| Elevated shelf | 16 | 17,106 |

Saved scene: **933 total objects including source libraries; 779 visible
objects, 732 visible mesh objects; 315,730 evaluated visible triangles**.
Largest individual visible base mesh: 3,724 triangles. Separate plants/decoration
make some collection totals exceed 10,000; they are not single export meshes.

Top-level collections: `Playable_6_FOUNDATION_STUDY`,
`Scenery_8_SOURCE_LIBRARY`, `SceneryRing_REVIEW_ONLY`,
`DistantGround_REVIEW_ONLY`, `ReuseLibrary_SOURCE_ONLY`,
`Cameras_Lights_Scale_REVIEW_ONLY`.

## Cheap checks and limits

- Python parsing and actual Blender saved readback passed.
- Six playable terrain meshes are closed, with zero nonmanifold edges and exact
  256 × 256 world footprints. Thirty targeted central floor samples are below
  25 degrees; this is not a walkability proof.
- Five authored joins, three samples each: maximum measured height difference
  0.0000458 stud. No exhaustive scenery/quarter-turn/collision sweep performed.
- Ten reused flora mesh/material-slot fingerprints match their loaded sources.
- Seventeen render outputs inspected, including the four no-heat-color views.
- Hidden collision is likely needed beneath ash routes, ascent and combat
  aprons. Simplify masonry/shelf blocking, leave plants and decorative cracks
  nonsolid. Collision has not been authored or tested.
- Vertical drop-in probing and fitted scenery remain generic integration work,
  already documented in CHUNK_DROP_IN/MODULAR_MAPS; no loader hacks added.

## Stop and cleanup

Stop for owner Blender review. No full kit, zone system, boss/enemy assets,
runtime changes, exports, uploads, publishing, commit or push.

The old `Emberfall_ArchitectureReview/EmberfallPrototype.blend`, its independent
assets, Input_LavaGeology/Input_Continuity/Input_ArtDirection, previous render
reports, debug guides and older prototype files remain historical reuse/recovery
sources. This study supersedes their terrain direction, not their production
status. Keep them and the new `.blend1` recovery file until owner acceptance and
applicable Studio/CI checks establish a safe replacement; only then recommend
removing obsolete terrain/debug snapshots. No exports/manifests were replaced,
and nothing was deleted.
