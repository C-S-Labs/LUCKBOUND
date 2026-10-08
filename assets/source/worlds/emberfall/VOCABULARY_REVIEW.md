# Emberfall — current-scene foundation variety review

2026-10-05. Continued the same [Blender scene](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/EmberfallFoundation.blend).
The exact live input is retained as `Input_Vocabulary.blend`. Revised EMBERFALL.md
and all three reference images were reread. No new zones, bosses, chunk inventory,
runtime changes, collision, Studio import, export, upload, commit or push.

## Review package

Actual saved-scene renders; galleries use temporary copies of current art,
removed before saving. Source libraries stay hidden; normal materials restored.

| Evidence | Full-size views |
|---|---|
| Assembled top-down and seams | [Top](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/assembled_top.png) |
| Existing six-chunk terrain lineup | [Lineup](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/chunk_lineup.png) |
| Eight lava/heat categories | [Heat sheet](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/heat_vocabulary_sheet.png) |
| Baseline seam at player eye / shallow oblique | [Eye](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/baseline_player_eye.png), [oblique](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/baseline_shallow_oblique.png) |
| Raised seam at player eye / shallow oblique | [Eye](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/raised_player_eye.png), [oblique](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/raised_shallow_oblique.png) |
| Recent-disaster ruins | [Eight archetypes](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/ruin_variety.png) |
| Integrated basalt formation vocabulary | [Eight archetypes](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/basalt_variety.png) |
| Flora infection ladder | [Four states / eight variants](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/flora_infection_ladder.png) |
| Overview / terrain drama | [Overview](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/overview.png), [entry lookahead](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/route_drama.png), [raised lookback](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/raised_lookback.png) |
| Glow minimized | [No emission](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/glow_minimized_overview.png), [top](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/glow_minimized_assembled_top.png), [molten color also muted](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/heat_muted_identity.png) |

[Combined review sheet](E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview/vocabulary_contact_sheet.png).
Eight individual heat close-ups accompany the heat sheet. Glow-minimized views
disable all material emission; the extra heat-muted view also removes main
molten/crack orange base colors. Normal shader links/strengths are restored.

## Terrain and seams

Six playable compositions: interrupted open basin, asymmetrical cut shelf,
broad combat plateau with slumped rear rise, shallow shrine depression, broken
causeway ascent with tilted shoulder, raised ruin terrace above a lower field.
Useful old shelves/cavities contribute to the mesh. Scenery includes low ruin
terraces and shallow fault ground alongside stronger elevated shelves. Not every
chunk receives the same parallel bands or the same height/complexity.

Constrained geological foot/lip/top outlines replace raster stair-stepping and
repeated longitudinal channel recipes. Broad faces and localized height breaks
retain depth. Some scenery still shares stepped polygon syntax; this is an
angular prototype requiring visual acceptance, not finished geology.

Edges have **41 matched stations**, a **24-stud controlled band**, and a short
interior ease. Shared ramp datum and low ash relief meet across the assembled
ring, including its rotated instances. Existing authoring profiles remain
BASELINE_ROUTE, RAISED_ROUTE, OPEN_COMBAT, LAVA_ADJACENT and SCENERY_OUTER.
The exterior backdrop excludes occupied footprints and meets the ring perimeter,
removing intersecting underlay outlines and exposed tile skirts.

**37 neighboring pairs × 41 actual border vertices:** maximum height gap
**0.000003815 stud**. All **32 source/placed terrains are closed**. Initial
exact-edge raycasts had false misses; final checks compare real border vertices.
This is a cheap assembled-layout check, not exhaustive rotations or traversal.

Reviewed baseline/raised player-eye route joins no longer show a hard handoff.
No particular route join remains an identified open gap. From above, broad
slope shading, shoulder rhythm and repeated scenery silhouettes can still expose
modular composition. The ring contour field is authoring data for this study;
arbitrary future layouts/runtime scenery compatibility remain unvalidated.
No loader special case or new runtime socket Kind was added.

## Feature vocabulary

**Eight heat categories / ten visible events:** tiny crack, medium crack, narrow
lava seam, buried vent/glow slit, small molten pocket, one-sided fissure,
contained channel, broad basin. Six playable-local events and one ring vent
complement three retained molten cavities. The original contained channel and
rare broad scenery basin remain; major open lava was not multiplied.
Banks have buried roots, the vent a cooled roof, the pocket a crust remnant,
and the fissure unequal banks. New molten surfaces carry the existing cooled-edge
attribute. Small lips and some angular footprints are still material/shape studies.

**Eight ruin archetypes across 21 source/placed groups:** snapped corner,
collapsed gateway, broken stair, shattered barricade, buried foundation, split
facade, toppled wall mass, burned structural remnant. Shared masonry proportions,
fresh fracture faces and concentrated debris relate them to one failing roadside
defensive precinct. Wasteland traces remain sparse; causeway and gateworks carry
the architectural escalation. Earlier good fallen masses/debris remain useful.
Fragment pivots sit at their own foundations.

Ruin gallery front row: corner, gateway, stair, barricade. Back row: foundation,
facade, toppled mass, burned remnant.

**Eight basalt archetypes across 20 source/placed formations:** fractured wall,
broken cluster, stump field, buried column line, shattered ridge, leaning outcrop,
shelf support, collapsed fan. Height, connectedness, burial and failure direction
vary. Buried roots sit beside/inside geological faces. Hexagonal column language
is still evident; the gallery proves archetypes, not every placement's acceptance.

Basalt gallery front row: wall, cluster, stumps, buried line. Back row: ridge,
leaning outcrop, support, fallen fan.

**Four infection states × two shapes = eight rosette variants.** Reused family
with spread/curled shapes, irregular partial boundaries and fully black corrupted
tissue, internal ember accents and rooted forks. Healthy groups, healthy/early
groups and partial/corrupted pockets are placed. Original sources remain intact
in the reuse library.

Flora gallery front row: healthy spread/curled, early spread/curled. Back row:
partial spread/curled, fully corrupted spread/curled.

Count stays **54**: 6 healthy, 19 early, 22 partial, 7 corrupted. Average placement
scale **0.6393 → 0.5916**; max height **2.50 → 2.45 studs**. No density increase.
Cool ash/graphite/blue-black materials remain. Three local smoke proxies reinforce
active heat/failure; future ambience implementation is outside this pass.

## Inventory, limits and next gate

| Measure | Current |
|---|---:|
| Playable / source scenery / ring placements | 6 / 8 / 18 |
| Scene objects, including hidden sources/cameras | 531 |
| Visible mesh objects | 340 (input 386) |
| Evaluated visible triangles, including review land | 141,392 (input 104,322) |
| Largest local visible terrain mesh | 3,328 triangles |
| Collections | 67; existing organization plus hidden FloraInfection_SOURCE_ONLY |
| Footprint | 256 × 256 studs |
| Persistent climb | 56 studs |

Triangle growth is mainly matching terrain borders and conforming exterior review
land, not dense micro clutter. Full collection counts, origins, per-chunk triangles,
height ranges and checks are in `vocabulary_technical_report.json`.

Preserved playable roots: ENTRY `(0,-512,0)`, PATH `(0,-256,0)`, COMBAT `(0,0,0)`,
SIDE `(256,0,0)` at90°, causeway `(0,256,28)`, gateworks `(0,512,56)`.
Six center walking datums match these origins. Transition mouths remain lower/upper
and the route continues at the raised level.

**Not Studio-import/walk-test ready yet.** Ready for this focused Blender review,
with stronger local drama and a wider vocabulary. Fully heat-muted distant views
still show plain ash stretches and coarse polygonal landmarks. Scenery shoulder
composition needs owner acceptance. Then prepare broad simplified route/ramp/combat
collision, simplify stair/bank movement, and address the documented generic vertical
socket measurement limitation. No collision tuning against changing terrain.

Keep `Input_Vocabulary.blend`, `Input_Naturalization.blend`, earlier recovery
scenes/reports and `.blend1` files until Blender acceptance and applicable Studio/CI
replacement checks. Naturalization is the historical input; this report owns the
current continuation. Nothing referenced by game code was removed. Stop after
this pass; no full biome production.
