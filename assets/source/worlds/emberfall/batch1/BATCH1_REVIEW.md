# Burned Plains production Batch 1 review

**2026-10-06 — nine playable sources, three frozen layouts; ready for owner review.**
This is the first production-intent authoring batch, not a production rollout or
the full Area I library. No Area II, settlement, castle or boss/source work.

## Authority and preservation

The owner-approved current design, modularity, appearance, route-depth and edge
contracts were consumed without reopening them. `authority_manifest.json` records
the current owner-checkout authorities and hashes. This task branch starts at
`b09a496`, before those mixed, uncommitted owner/prior-session documents. Its narrow
Batch 1 handoff addenda do not absorb or replace that work. Reconcile the current
approved documents when the owner later integrates this batch; historical opening
wasteland language on the older branch is superseded for Area I.

The approved BurnedPlains.blend, BurnedPlainsModularity.blend,
BurnedPlainsProductionGate.blend and BurnedPlainsEdgeProfiles.blend remain unchanged.
Baseline hashes and the 47-path owner baseline are retained externally under
`E:/BlenderAIProjects/Runtime/Emberfall_Batch1/inputs/`. The live owner Blender session
was not overwritten. No production manifest, IDs, runtime code or loader changed.

## Playable kit

All nine playable footprints are **256×256**, with centre-ground origins, two
documented sockets, active `Col` BYTE_COLOR/CORNER data, authored road intent,
transformed prop/refuge anchors and simplified traversal collision. Source datum
values below are **before centre-ground rebasing**; actual engine OffsetY values,
offsets/facings/24-stud widths and local guides are in `batch1_report.json`.

| Identity / purpose | Source sockets/profile datums | Landmark | Tris / visual objects / terrain collision |
|---|---|---|---|
| `EF_ENTRY_WINDWARD_MEADOW` — **Windward Meadow**: Quiet maintained-field entry protected by wall and gate | S HOLLOW 0 → N HOLLOW 0 | Windward field wall and surviving meadow | 28,117 / 132 / 70 |
| `EF_DRAINAGE_CROSSING` — **Drainage Crossing**: Shallow wet drainage with compact roadside stone culvert mouths | S HOLLOW 0 → N HOLLOW 0 | Low stone-lintel culvert crossing | 23,992 / 88 / 70 |
| `EF_ORCHARD_BEND` — **Orchard Bend**: Level right bend framed by cultivated orchard rows and short inside grove | S HOLLOW 0 → E HOLLOW 0 | Orchard rows framing road bend | 34,580 / 176 / 69 |
| `EF_RIDGE_ASCENT` — **Ridge Ascent**: Broad +24 straight ridge; west roadside windbreak and open east overlook combat zone | S HOLLOW −24 → N HOLLOW 0 | Uneven field windbreak along the rising ridge | 24,236 / 61 / 70 |
| `EF_SWITCHBACK_BANK` — **Switchback Bank**: Gradual +24 right turn beneath an earthen cutbank and tree line; open outside bend | S HOLLOW 0 → E CREST +24 | Rising cutbank and curved countryside tree line | 26,199 / 76 / 69 |
| `EF_WAYMARK_TERRACE` — **Waymark Terrace**: Level ridgebench with a single modest stone waymark and broad west combat meadow | S CREST 0 → N CREST 0 | {'type': 'stone_waymark', 'x': 24, 'y': 28, 'height': 7.55} | 22,985 / 54 / 70 |
| `EF_OPEN_FIELD_CLEARING` — **Open Field Clearing**: Quiet ordinary connective and open combat field; boundary frames empty space | S HOLLOW 0 → N HOLLOW 0 | Quiet connective piece | 23,260 / 76 / 70 |
| `EF_BURN_FRONT_VERGE` — **Burn Front Verge**: Rising left bend with damaged wagon and roadside stubble opportunities; assembly assigns front | S HOLLOW 0 → W CREST +24 | Broken roadside farm wagon | 25,272 / 165 / 69 |
| `EF_FENCELINE_RISE` — **Fenceline Rise**: Straight low +16 rise through dry pasture gaps, roadside fence and distant countryside | S CREST 0 → N CREST +16 | Quiet connective piece | 21,804 / 74 / 70 |

HOLLOW and CREST are edge metadata, not place identities. Windward Meadow is the
entry composition; quiet Clearing/Fenceline pieces balance the orchard, wagon and
single modest waymark. All sources can receive assembled appearance. No fixed
green/yellow/black chunk classes were authored.

## Worker ownership and integration

- `/root/countryside`: Windward Meadow, Drainage Crossing, Orchard Bend;
  `countryside.py` and its external lane outputs only.
- `/root/elevations`: Ridge Ascent, Switchback Bank, Waymark Terrace;
  `elevations.py` and its external lane outputs only.
- `/root/fields`: Open Field Clearing, Burn Front Verge, Fenceline Rise;
  `fields.py` and its external lane outputs only.
- Lead: shared API/contracts, freeze, collision correction, integration, layouts,
  necessary scenery, evidence, Studio checks and documentation.

Three non-overlapping lanes completed after the owner explicitly restored capacity.
No worker Git lifecycle operations or source-ownership conflicts. Accepted owned
files were copied into `agent/emberfall-batch1`; no Git merge. Earlier worker counts
of 42–46 collision pieces are superseded by the lead's cooked-collision correction.

## Edge/collision and freeze

The locked HOLLOW/CREST, 24-stud mouths, shared corner datums, canonical 8-stud
transverse samples, symmetric quarter-yaw semantics and **40-stud source-authored
transition** remain. The first eight studs inward extrude the curved edge profile;
they are not a broad flat pad. No runtime repair collar. The 0.01-stud tolerance
only permits tiny seam/dressing differences, never neighbour-dependent reshaping.

Each source uses 16 closed interior tiles with PreciseConvexDecomposition plus
53–54 closed seam prisms with Hull fidelity: **69–70 terrain collision parts**.
Only **collinear** canonical intervals may merge. The first 42–46-part attempt
merged curved intervals; despite an offline convexity check, Studio Hull cooking
introduced a **0.139069-stud** shoulder step. It was rejected. Revised source
collision was refrozen before layout testing; visual terrain hashes stayed exact.
The same rotated Switchback + Waymark cook now gives **139 parts, 28 bounded rays,
zero misses and zero measured cross-seam step**. This is a targeted physics query,
not a character traversal certification. `studio_collision_result.json` is raw
evidence; `studio_review.json` records context and limitations.

Saved-source checks: nine closed terrains, **8,958 triangles per terrain / maximum
mesh**, canonical profile error ≤0.000000881 stud, closed colliders, Hull halfspace
error ≤0.000000477 stud, 32 safety-boundary segments per source (24-stud mouths
excluded). Existing Boundary/CollisionTemplate schema and camera exclusion tags
are sufficient; no runtime refactor required. All 24 layout joins sampled at 129
transverse stations; maximum **0.000009225 stud**. No source terrain or collision
vertices were edited after freezing for any layout.

## Three-layout review

These are three deterministic review layouts generated and checked with the real
`ChunkCore.worldSocket/placeAgainst/overlaps`, not fabricated production seeds.
They use the **same nine frozen sources once each**. All quarter yaws occur across
the layouts. Full poses/order/socket selections are in `layouts.json` externally
and `batch1_report.json`. The isolated `actual_chunkcore_layouts.luau` harness is
external review tooling, not a production generation change.

- **Layout1:** Windward Meadow (90°) → Orchard Bend (90°) → Open Field Clearing (180°) → Drainage Crossing (180°) → Switchback Bank (180°) → Fenceline Rise (270°) → Waymark Terrace (270°) → Burn Front Verge (180°) → Ridge Ascent (0°). Max sampled edge error **0.000006779 stud**; 27 non-playable continuation tiles. PASS for this bounded review.
- **Layout2:** Windward Meadow (270°) → Ridge Ascent (270°) → Burn Front Verge (270°) → Fenceline Rise (180°) → Waymark Terrace (180°) → Switchback Bank (270°) → Orchard Bend (90°) → Drainage Crossing (180°) → Open Field Clearing (180°). Max sampled edge error **0.000009225 stud**; 31 non-playable continuation tiles. PASS for this bounded review.
- **Layout3:** Windward Meadow (180°) → Burn Front Verge (180°) → Fenceline Rise (90°) → Waymark Terrace (90°) → Switchback Bank (180°) → Orchard Bend (0°) → Ridge Ascent (90°) → Open Field Clearing (90°) → Drainage Crossing (90°). Max sampled edge error **0.000005411 stud**; 27 non-playable continuation tiles. PASS for this bounded review.

Layout1 forms a hooked return with orchard first, later crest rise and final fall.
Layout2 climbs early, reaches the wagon/waymark before a reversed Switchback, and
finishes via orchard, drainage and clearing. Layout3 turns early, returns through
the crest landmarks and orchard, then rises into a different long countryside tail.
Order, yaws, elevation rhythm, sightlines and front/landmark sequence differ.

Reviewed per layout: broad overview, diagnostic top, baseline eye, raised gameplay,
ridge view, camera at a sampled highest playable point +5 studs, road seam and
active front. No modular boundary was identified in these plausible gameplay
views. Minor top-down shading/density bands remain non-blocking polish under the
accepted rule. This bounded camera evidence does not claim every possible camera
position or a full in-game character walkthrough.

## Appearance, burn and vegetation

One assembly field follows **ordered route-guide arclength / semantic depth**,
extended continuously off the path with a harmonic field. It is not a world-axis
gradient or independent chunk quotas. Transformed justified local refuges modify
the same field used by terrain, grass, staged trees and wooden props. Source-local
root metadata transforms with quarter yaw; no stale north/south stage assumption.
Assembly uses each source object's unparented `matrix_basis` rather than inactive
scene `matrix_world`, preventing detached crowns/props. Hero anchors permit explicit
local stage overrides without procedural tree scattering.

All three playable-area samples measure **18.8794% green / 31.0522% stressed /
50.0683% charred**. Active front crosses Drainage→Switchback in Layout1 and
Switchback→Orchard in Layout3; Layout2 places the front differently within the run.
Irregular refuges, continuously sampled state and restrained flame/smoke preserve
the countryside under an active burn. State agreement is visible in inspected
player views. No emissive lava terrain or volcanic shelf forms were introduced.

Bounded **actual FBX → Studio importer → AssetPreparation → ChunkLoader → Play
client EditableMesh** verification used only Switchback terrain. Final FBX uses
the established FBX_SCALE_ALL / unit / SRGB export settings. Blender reimport:
256×29×256, source/import origin zero, 8,958 triangles, Col BYTE_COLOR/CORNER.
Studio import: scale 1, same dimensions, 24,680 imported vertex/color entries,
8,958 faces, source-pivot offset Y −7.82643127. Real Play server loaded one scratch
manifest visual at yaw90, **69 walk collision +32 safety boundaries**. Play client
created/recoloured one fixed-size copy with unchanged dimensions/counts. Production
asset IDs/content remained untouched. First disposable exporter-scale and Edit-only
server-context attempts were corrected before the final successful check.

## Hybrid road

Each chunk owns local guides, grade/bend intent and aligned roadside compositions.
Assembly orders/transforms/reverses them as needed, preserving continuous distance
UVs, sensible roughly 7.7–9.1-stud width and road flow through every socket.
The review road conforms to the **frozen visual triangles**, with a tiny lift,
instead of changing terrain. Local bend framing, culverts, fence, wagon and wall
remain chunk-owned. Final runtime road construction remains a separately gated
implementation; review geometry is not automatically a production runtime asset.
No observed road cracks/grid reset from reviewed gameplay views. The three curved
pieces still share a fairly regular quarter-turn gesture: a Batch2 variety issue.

## Required scenery/shared dressing

Only layout-derived, **non-playable continuation fields/hills** were built:
27/31/27 placed review tiles for Layout1/2/3, surrounding the playable footprint,
plus 65 staged peripheral trees per layout and restrained distant smoke. These
tiles have no route sockets or traversal collision and do not count toward nine.
They hide playable edges from inspected gameplay views; the outside of the whole
review land remains visible from diagnostic broad views. No oversized playable
piece or settlement was created. `interior_continuation` remains preserved scenery.

Approved foundation materials/grass/tree helpers were reused. Necessary new local
dressing comprises dry-stone field walls/gates, low culvert mouths, ordinary fences,
a modest waymark and one damaged farm wagon, assembled from shared source helpers.
No large speculative scenery/prop library was built. These are source-authored
assets; final packaging/prop-template content is not installed in production.

## Repetition and missing vocabulary

Each current layout uses each source once. Distinct places and ordinary connectors
read separately, but this does **not** prove repeated-source resistance in a longer
run. Observable repetition: the shared grass/stubble mesh language, basic crown and
skeletal tree family, fairly regular peripheral tree spacing, dry-stone modules and
similar quarter-turn road arcs. Orchard's 16-tree pattern and wagon/waymark should
remain limited landmarks; do not repeat them adjacent. Clearing and Fenceline are
intentionally quieter, not redundant hero scenes. No chunk is rejected in this
bounded Batch1 review; final artistic acceptance belongs to the owner.

For **Batch2 planning only**, consider a quieter level left bend, a differently
framed sheltered grove and alternate road rhythm / crest descent. Stay with existing
HOLLOW/CREST. First test repeated-source placement and owner feedback; do not solve
every repetition concern by generating more chunks now.

## Production cost observations

Nine sources total **230,445 visual triangles / 902 visual source objects**,
excluding review roads, collision and scenery. Maximum mesh 8,958; grass is batched
into two meshes per source, about 3,500 authored clumps each. **56 playable tree
anchors**. Terrain collision **627 parts** total; separate safety boundaries **288**.
This is roughly a 51% reduction from the conservative proof's 142–144 per source,
not a certified mobile budget. Hero-prop/vegetation physical blockers still require
final package classification; terrain-collision counts are not total runtime physics.

Orchard is largest at 34,580 tris/176 objects; Verge has 165 objects due to wagon/
stubble detail. Reuse/packing should reduce instance cost without sacrificing local
identity. Current terrain+grass require at least **27 per-placement appearance
copies** across nine chunks, plus whichever tree/prop appearances use recolouring
rather than authored state variants. Actual Studio representative allocation is one
terrain mesh; do not extrapolate a measured full-run memory budget. Offline field
arrays are ~199–232KB/layout; this is not Roblox memory. Blender scenery density is
not a deployed instance budget. Mobile/published-place API budgets, allocation time,
full prop import/fidelity and full-run memory remain later rollout checks.

## Evidence and rebuild

External root: `E:/BlenderAIProjects/Runtime/Emberfall_Batch1/`.

- `BurnedPlainsBatch1.blend`: nine independent source scenes plus three assembled
  review scenes. Three lane `.blend` sources remain recoverable separately.
- `kit_contact_sheet.jpg`, `kit_player_views.jpg`: nine named playable pieces.
- `layouts_contact_sheet.jpg`: five comparative views for all three layouts.
- `technical_contact_sheet.jpg`, `Layout1/collision_seam.png`,
  `collision_overview.png`: frozen visual/road/collision joins and burn presentation.
- `Layout1/`, `Layout2/`, `Layout3/`: overview, route_top, player_eye,
  raised_gameplay, ridge_gameplay, reachable_high_point, seam_road, active_front PNGs.
- `individual/`: final per-source overview/player-eye road presentation.
- `studio_import.png`, `studio_review.json`, `studio_collision_result.json`,
  `fbx_result.json`, disposable `RepresentativeSwitchback.fbx`: bounded import proof.
  `studio_collision.png` is an unsuccessful blank capture and is not evidence.
- `artifact_inventory.json`: exact external path/size/hash inventory.

Rebuild only through `tools/run_blender.py`; normal-user profile approval may be
required under the shared launch policy. `AUTHORING.md` defines helper inputs and
ordered commands. The source API deliberately references preserved approved helper
snapshots and materials; those dependencies must remain available. This is a local
reproducible authoring package, not a portable deployed kit.

## Repository and next step

Changed task paths are listed exactly in `changed_files.json`. Lead source/check/
evidence scripts and reports live only under this `batch1/` folder, with narrow
INDEX/WORKLOG/STATUS/biome addenda. Original owner checkout remains at b09a496 with
its original **13 tracked changes +34 untracked paths**; none were staged, overwritten
or included in this task checkpoint. Worker branches retain owned uncommitted
sources and common lead-applied API changes. No push, merge, PR or main changes.

No production loader/schema change is needed for geometry. Future reviewed delivery
will register chunk/socket/profile data, collision templates, safety boundaries,
road intent, anchors and explicit scenery content; integrate the already-proven
assembly appearance lifecycle/road logic generically. Do not introduce content
special cases into Systems. No such production integration was performed here.

Stop for owner visual/Studio review. Keep all approved studies. Keep Batch1 .blend1,
rejected curved-Hull fixture and initial exporter-scale fixture until owner review
and applicable replacement/CI checks establish safe retirement; failed screenshots
may then be removed. No production assets/IDs/manifests were superseded.

PASS — Burned Plains Batch 1 is ready for owner review and Batch 2 planning.
