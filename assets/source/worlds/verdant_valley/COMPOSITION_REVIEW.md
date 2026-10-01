# Verdant Valley — composition review (2026-09-29)

Current live source: `E:/BlenderAIProjects/Projects/VerdantValley_Cleanup.blend`.
The original broad composition pass used `VerdantValley_Extra_Details_Backup.blend`.
This authoring pass changes no production exports, Studio assets, collision, sockets or terrain.

## Current distribution revision

### Cliff Passage final zoning revision — 2026-09-30

The new owner overhead annotation explicitly permits nonsolid detail in yellow.
Local X is travel; red protects local Y ±21 for the complete chunk length, yellow
extends to ±40. Full new object bounds are checked, including tree canopies.
Eight unequal yellow pockets contain 26 linked grass/bush/small-stone props,
all in `VV_PROPS_NONSOLID` with `CanCollide=false`. No continuous path border.
Upper/rear slopes gain six linked tree assemblies from Deep Clearing and Warden's
Clearing, plus 27 supporting rock/vegetation props in asymmetric compositions.
The prior pass's nineteen appropriate Temp-derived additions remain. Its three
oak-derived trees were already removed by the owner; none are recreated.

There was no suitable existing vine/hanging asset in the scene. Owner explicitly
allowed one reusable vine in that case: `VV_Vine` in Temp is the only new mesh.
Five linked instances form one stronger three-strand feature and a shorter
two-strand accent on the opposite wall. Lengths, widths and spacing differ.
All foliage vertices with a face beneath them sit 0.04–0.503 stud in front of
the wall; no wall geometry was changed. Nonsolid classification is explicit.

All 7,916 original objects match hashes of geometry, materials, transforms and
collections. All new ordinary props/trees share their reference's exact mesh
data. `cliff_environment.py` refuses repeat application over owner edits;
its `--review` runs in a background copy without saving review settings.
Eleven saved-source views cover overhead, both passage directions, both yellow
strips, both vine features and four neighboring-chunk angles. Record:
`Cliff_Zones_Record.json`; comparison/contact sheets: `Cliff_Zones_Review/`.
Owner Blender review and production export/Studio collision verification remain.
Keep `VerdantValley_Cliff_Zones_Input.blend` and earlier environmental input,
record and review artifacts until those checks pass; then remove obsolete reviews
if unneeded. No production exports, asset IDs or manifest entries were replaced.

The owner found the initial 360-object pass too tightly clustered, leaving accidental dead
shoulders. Redistributed 319 existing added plants/stones across wider uneven shoulder areas;
added 386 small Temp-derived props in linking gaps. Current result: 746 dressing objects
across 24 chunks (19–37 each). Counts describe the result, not a universal placement target.

Inspected the eight Temp sources; normal dressing reuses rock, log, Star_bush,
flowering_bush and grass_tuft. Unique features and their immediate supporting props stayed
fixed in this revision. Large trees and landmarks remain original. Treasure Hollow,
Longgrass Meadow, Deep Clearing and Warden's Clearing are finished, protected references.
Cliff Passage was unchanged in that original pass; the later zoned revision above
supersedes that assessment. Cave Mouth remains unchanged by the composition tools.

## Per-chunk record

Later owner-authorized reference exception: Longgrass Meadow's flowering tree now has
seven canopy lobes, 49 larger pink/cream blooms and a tapered branching pale trunk with
roots. Its two existing objects retain placement and solid/nonsolid classification;
all other 8,021 objects are unchanged. Removed only the two Temp tree sources (six
sources remain). Reviewed saved-source feature, whole-chunk and overhead images in
`Flowering_Tree_After/`; geometry is finite and stays outside the route/boundary margins.
No collision or production exports changed. Keep `VerdantValley_Flowering_Tree_Input.blend`
and `Flowering_Tree_Before/` until owner visual and eventual Studio checks pass, then
remove these superseded tree references if unneeded.

The owner reference images govern density and negative space. Current planting follows
wide irregular shoulder areas with rotation/scale/spacing variety; open grass remains.

| Chunk | Initial weak area | Current distribution correction | Unique detail preserved | Dressing objects |
|---|---|---|---|---|
| Ancient Oak | Bare west mid-shoulder and unsupported oak base | 13 existing props spread; 20 added in linking gaps | Fallen forked oak bough | 34 |
| Blossom Terrace | Empty upper terrace and isolated lower tree group | 13 existing props spread; 18 added in linking gaps | Pale stones half enclosed by blossoms | 35 |
| Boss Sanctuary | Repeated perimeter rocks without lower growth | 11 existing props spread; 8 added in linking gaps | Small weathered offering bowl beside perimeter stone | 20 |
| Cliff Overlook Gate | Two bare middle shoulders between corner groups | 13 existing props spread; 18 added in linking gaps | Low uneven three-stone cairn | 34 |
| Crystal Spring Gate | Lower bank detached from spring composition | 14 existing props spread; 12 added in linking gaps | One weathered blue shard in grass | 27 |
| Cutbank Ford | Bare southern approach shoulders below the river | 14 existing props spread; 19 added in linking gaps | Two discarded bridge timbers | 34 |
| Entry Dawn Meadow | Upper-left shoulder and repeated isolated grass cones | 14 existing props spread; 20 added in linking gaps | Small abandoned wooden meadow stool | 35 |
| Entry Woodland Refuge | Unconnected west tree base and lower-right grove | 13 existing props spread; 21 added in linking gaps | Three uneven cut logs tucked into grove | 37 |
| Fern Hollow | Bare right middle shoulder opposite dense grove | 13 existing props spread; 17 added in linking gaps | Large asymmetric fern fan against rock | 34 |
| Forgotten Orchard Gate | Upper-left orchard shoulder and unsupported southeast trees | 12 existing props spread; 21 added in linking gaps | Short collapsed orchard fence | 34 |
| High Ledge Gate | Bare ledge tops away from east-west route | 14 existing props spread; 12 added in linking gaps | Wind-stripped branch beside two stones | 27 |
| Mossbound Ruins | Blank lower ruin terrace and isolated northeast grove | 13 existing props spread; 19 added in linking gaps | Small mossy collapsed wall fragment | 33 |
| Mushroom Glen | Middle-west shoulder and bare northeast tree base | 10 existing props spread; 13 added in linking gaps | Small lilac fungi growing along fallen log | 25 |
| Overgrown Causeway Gate | Bare central shoulders between repeating corner ruins | 14 existing props spread; 18 added in linking gaps | Exposed angular roots over a small stone | 34 |
| Crossroads Copse | Northeast copse has a lone tree with no secondary growth | 14 existing props spread; 16 added in linking gaps | Two leaning young shoots beside older tree | 31 |
| Narrow Pass | Wide bare east recess between boulder groups | 12 existing props spread; 17 added in linking gaps | Split stone with growth in its gap | 32 |
| Split Meadow | Bare northeast shoulder and unsupported southwest trees | 17 existing props spread; 16 added in linking gaps | Partly grass-covered log with one lifted end | 35 |
| Sunwash Fork | Empty west middle shoulder and thin northeast cluster | 14 existing props spread; 17 added in linking gaps | Three tall golden seedheads in a sunny grass pocket | 32 |
| Rock Garden | Blank east recess and repetition of isolated rock piles | 15 existing props spread; 17 added in linking gaps | Two broad leaning stone slabs | 33 |
| Shaded Grove | Open upper/lower shoulders disconnected from tree canopies | 16 existing props spread; 14 added in linking gaps | New shoots growing beside a decaying log | 32 |
| Forgotten Trial | Bare outer approach shelves around established trial ruins | 11 existing props spread; 7 added in linking gaps | Half-buried broken stone plinth | 19 |
| Stone Sentinels | Empty northeast shelf and weak west mid-shoulder | 13 existing props spread; 19 added in linking gaps | Pale lichen on a small fallen standing-stone chip | 33 |
| Wetland Pools | Dry southeast bank and empty gap above the small pool | 13 existing props spread; 13 added in linking gaps | Uneven short reed bank beside a mossy rock | 28 |
| Windward Ridge Gate | Bare southwest ridge shoulder and unsupported north stones | 13 existing props spread; 14 added in linking gaps | Leaning weathered survey stake | 28 |

## Review and inexpensive verification

Individual overhead, route and low feature views plus whole-kit overhead reviewed after
spreading. Tight islands now connect to existing tree/rock shoulders; Boss, Mushroom Glen,
Wetland and Trial receive less growth than open meadows/groves. No new primary forms.
New bounds stay 22.73 studs inside rectangular footprints and 35.56 studs from socket
route centerlines. Local grass-material, support and slope checks keep placements off
routes, unsupported rims and water. Finite vertices and Python syntax checks pass.
Saved-scene background reopen/render passes; these checks do not substitute for Studio review.

All 7,279 original objects match the pre-pass SHA-256 digest of names, transforms,
collection membership, vertices, face indices, material assignments and shading flags:
`b41e55f65faf230b41280c0ecbc5f96a95c1d085c0be35fd5e07a130173cd73b`.
Every existing signature feature and its immediate supporting props also matches the
before/after digest for this distribution correction.

Current renders: `E:/BlenderAIProjects/Projects/Composition_Spread/`.
Current JSON record: `Composition_Record.json`; revision checks: `Composition_Spread_Verification.json`.
These sit beside the live source. Owner Blender review is next; Studio export/import remains pending.

## Tool operation

`detail_composition.py` contains initial authored plans, `refine_review()` and
`spread_review()` for the owner distribution correction. Each pass is one-time and refuses
repeat application. Never rerun over owner placement edits; current live placements are authoritative.
`review_composition.py` uses a separate background process and saves no camera/render/visibility
changes into the authoring source. The legacy exporter runs on import: socket data is
extracted without executing it. An initial import during the first pass cleared the unsaved
scene; immediate saved-scene recovery matched the independent pre-pass snapshot exactly.

## Cleanup recommendation

Keep `VerdantValley_Composition_Clustered.blend`, `VerdantValley_Clustered_Overview.png`
and `Composition_After/` as the superseded tight-distribution rollback until owner Blender
review and eventual Studio visual checks confirm replacement. Then remove if unneeded.
Retain the original `VerdantValley_Composition_Input.blend`, `Composition_Before/` and earlier
Blender/collision references pending validation. Temporary external helpers
`check_composition_input.py`, `composition_sheets.py` and `composition_detail_sheets.py`
can also be removed after review if no longer used. No production assets or manifest entries
were replaced. Keep Temp, all four references and owner-kept recolours.
