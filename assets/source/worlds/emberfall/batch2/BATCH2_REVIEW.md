# Burned Plains Batch 2 production review

**Delivery/Studio HOLD resolved:** final imported review passes; see
[DELIVERY_STUDIO_REVIEW.md](DELIVERY_STUDIO_REVIEW.md) and `studio_validation.json`.
The historical HOLD below records the original failure and remains provenance.
All missing deliveries complete; no canonical reauthor or existing asset replacement.

Production worktree: `E:/BlenderAIProjects/Worktrees/emberfall-batch2-production`,
branch `agent/emberfall-batch2-production`, based on approved plan `eacdb24`.
Single agent; no orchestration, accepted-source writes, push, merge, PR or main changes.

## First-three gate — PASS, 2026-10-07

| Source | Role/profile | Rise | Visual triangles/objects | Terrain colliders |
|---|---|---:|---:|---:|
| Quiet Hollow Bend | Low; S→W HOLLOW/HOLLOW, late sweep | 0 | 21,146 / 28 | 69 |
| Raised Pasture Bend | Low; S→E CREST/CREST, early turn | 0 | 20,210 / 20 | 69 |
| Low Shoulder Climb | Low; S→N HOLLOW/CREST, shallow reversible slope | +12 | 21,173 / 28 | 70 |

Three independently authored 256×256 centre-ground sources. Closed terrain and
collision; 24-stud mouths, canonical samples and forty-stud source transitions.
Maximum mesh 8,958 triangles. Quiet bend road229.479 studs, raised bend207.173,
compared with Batch1's repeated201.057-stud quarter arc. Interior road ranges
3.968/2.180/12.088 studs. Sparse asymmetric ordinary trees, no gate/marker/wagon.

Read-only Batch1 neighbors: Windward → Quiet → Clearing → Shoulder → Raised →
Fenceline → Waymark → reverse Switchback → Drainage. Actual unchanged ChunkCore
fits four rotated recipes. Frozen sampled joins max0.000006579 stud at four yaws;
the assembled semantic field retains the accepted green/stressed/char proportions.
Inspected source top/overview/eye plus assembled overview/elevated evidence.
These satisfy quiet connector roles and distinct turn timing. Source-only tiles
show their perimeter deliberately; assembled terrain is reviewed separately.

Separate normal-project Rojo-built `Batch2ProductionReview.rbxlx`, PlaceId0:
208 exact authored collider meshes cooked using requested Hull/interior precise
fidelity.114 bounded height rays per yaw0/90, zero misses, maxedge error0.000007629
stud. Interior8-stud collision approximation differs from visual4-stud terrain
by up to0.352524 stud at sampled guides; existing terrain-collision principle is
unchanged, not a new exact-interior-surface claim.

Normal Play, actual ControllerManager input, no translation after each start:
all three roads reached the penultimate sampled exit at health100, in
9.600/8.598/10.834s. Initial test collider-centre placement was corrected before
measurements. This is source traversal, not a final assembled socket crossing.

## Evidence and reproducibility

External `E:/BlenderAIProjects/Runtime/Emberfall_Batch2/`:
`BurnedPlainsBatch2_GateA.blend`, `BurnedPlainsBatch2_Review.blend`,
`gate_a_sheet.jpg`, individual overview/eye/top PNGs, `GateA1/` assembled views,
`gate_a_studio_results.json`, source/rotation/collision payload reports and generated
cook/verify/walk Luau. Scripts here regenerate only new Batch2 outputs through
the shared Blender launcher. Accepted Batch1 geometry hashes remain exact.

## Eight-source delivery — HOLD, 2026-10-07

All eight source terrains and four approved dressings are authored. GateA local
checkpoint is `2af9994`. The remaining five followed that gate without changing
Batch1, the accepted architecture or the approved plan.

| Source | Role/profile | Net rise / road range | Recognizable composition | Visual tris / source objects | Collision |
|---|---|---:|---|---:|---:|
| Quiet Hollow Bend | LOW, S→W H/H; late sweep | 0 / 3.97 | Damp lee, sparse outer pasture trees | 21,146 / 28 | 69 |
| Raised Pasture Bend | LOW, S→E C/C; early sweep | 0 / 2.18 | Raised open pasture, restrained shoulder | 20,210 / 20 | 69 |
| Low Shoulder Climb | LOW, S→N H/C | +12 / 12.09 | Oblique drift, shallow drainage, lee trees | 21,173 / 28 | 70 |
| Swale Drift | LOW, S→N H/H | 0 / 3.57 | Opposing lateral drift, shallow swale, loose bank trees | 21,000 / 27 | 70 |
| Pasture Saddle | LOW, S→N C/C | −8 / 8.00 | Broad falling saddle, off-axis road, few exposed stones | 20,310 / 22 | 70 |
| Long Ditch Verge | LOW, S→N H/H | 0 / 1.24 | Longitudinal erosion ditch beside an almost treeless road | 19,198 / 13 | 70 |
| Leeward Grove | MEDIUM, S→N C/C | 0 / 0.86 | Irregular seven-tree lee cluster, sheltered pocket/open opposite flank | 25,052 / 60 | 70 |
| Abandoned Fieldstead | HIGH, S→N C/C | 0 / 0.96 | Modest 18×14 footing, broken uprights/timbers, agricultural yard | 21,711 / 52 | 70 |

All routes reverse with geometry/socket/collision rotation together. The ditch
ground depression is separate from the road range. Swale's first road dip was
only 2.66 studs; deepened it to 3.57 before final export to satisfy the planned
3–5-stud swale vocabulary. No other library-role redesign.

Each source passes closed geometry, origin/256×256 footprint, socket width/kind,
canonical edge and Hull half-space checks. Maximum profile error0.000000565 stud,
maximum single visual mesh8,958 tris. These are Blender/source checks: final
uploaded collision cooking and traversal for all eight have NOT been validated.
GateA's three generated exact cooks/traversals are the only actual Studio
collision/traversal passes this task.

## Controlled dressing alternatives

Exactly four, separate scenes in `BurnedPlainsBatch2.blend`; not extra terrain
sources. Geometry hashes, sockets and terrain collision are identical to their
canonical source. Quiet B trades the three-tree framing for a short transverse
stone trace and one distant opposite tree. Raised B uses a broken distant fence
and opposite sparse tree. Swale B is nearly treeless with restrained agricultural
stone strips. Ditch B replaces the almost treeless bank with a loose three-tree
group. Grass placement is reseeded; traversal and edge profiles are unchanged.
No grove/fieldstead variants or new landmarks were added to inflate the count.

## Combined 17-source library

Actual unchanged ChunkCore fits; frozen geometry assembled in Blender:

| Layout | Placements / route length | Repeated canonical sources | Maximum sampled seam |
|---|---:|---:|---:|
| Combined1, hollow countryside | 16 / 3,997 studs | 4 | 0.00000996 |
| Combined2, deliberately long/repetition-heavy | 24 / 6,030 studs | 8 | 0.00001653 |
| Combined3, mixed elevation/landmarks | 20 / 4,947 studs | 5 | 0.00000621 |

Combined2 uses Swale/Shoulder/Saddle three times each, Quiet/Ditch/Clearing/Grove/
Raised twice each. Four suitable repeats use their B dressing; third Swale use
returns to A deliberately. Fieldstead occurs at11, Orchard at18: six ordinary
pieces separate them. Grove repeats at8/22. Combined3 includes reverse shoulder
transition, Switchback, Waymark and Burn Front; across all three every accepted
Batch1 and new Batch2 source is exercised. Source hashes remain unchanged.

Inspected top/overview, player-eye and elevated views. Different turn timing and
straight drifts reduce the repeated quarter-circle gesture. Sparse connectors
support quieter intervals; grove framing contrasts with open ditch/saddle. The
same-source family remains recognizable on a diagnostic map; dressings, rotation
and changing semantic burn state reduce gameplay recognition cues. This is a
Blender visual assessment, not an owner acceptance or imported Studio result.
Repeated-source resistance in actual Play remains unproven beyond GateA sources.

Semantic route-depth/refuge fields retain approximately18.88% surviving,
31.05% stressed,50.07% charred in all three layouts. Tree state/root anchors follow
the transformed field, not a permanently directional source burn gradient.
Active fire/smoke accompanies damaged countryside. No volcanic geometry added.

The final Combined2 review applies the frozen accepted scenery-scaling algorithm:
4-stud boundary samples, underlap and terrain-grounded baked grass clumps. No
playable terrain edits or runtime scenery EditableMesh recolouring. This removes
the coarse continuation's close turf-wall appearance in the inspected review.

## Area I assessment

Seventeen sources appear sufficient for initial Area I authoring, provisionally.
This task demonstrated 16/20/24-placement routes with intentional reuse; it does
not assume all20 minutes occur in countryside. No Batch3 started or recommended
as an automatic requirement. A small later batch remains conditional on actual
owner traversal exposing an opposite-handed quiet bend or other specific gap
that spacing, rotation and the four dressings cannot reasonably resolve. Imported
walkthrough must pass before confirming sufficiency.

## Exports, new assets and upload blocker

`source_export_manifest.json` records three reusable source FBXs; all round-trip
checks passed names/counts/dimensions/UV/Col, size and SHA256. No existing Roblox
asset was modified. New Models, owner21985283:

| Export | New Model ID | MeshParts |
|---|---:|---:|
| EF_BATCH2_SOURCE_VISUAL_0 | 88065938858510 | 29 |
| EF_BATCH2_SOURCE_VISUAL_1 | 88157428738073 | 15 |
| EF_BATCH2_SOURCE_COLLISION_0 | 108592230513646 | 558 |

`asset_mapping.json` contains all602 source names→MeshIds, centres, sizes, roles,
collision fidelities and operation/Model ledger. Four alternative dressings share
source terrain/collision exports. Imported source integration is still pending.

Separately exported11 baked Combined2 appearance FBXs for the bounded real-loader
production review, explicitly review-only. These are not replacement source assets,
benchmark proxies or an arbitrary-seed appearance solution. All11 round-trip checks
passed. First eight new review Models uploaded:

`139712835647313`, `129641798175330`, `79656345119842`, `112864973724944`,
`136262450851398`, `124914370627829`, `83612230158373`, `75116781971033`.

**STOP:** Roblox terminal processing failure for `EF_BATCH2_REVIEW_VISUAL_8.fbx`:
operation `fea2f937-03a8-4978-8c70-27d22ddf4c2d`, response
`{"code":"Unknown","message":"Unknown Error","details":[]}`. No Model ID
or mapping was returned for that file; whether an inaccessible partial asset
exists is unknown. Files9/10 were not attempted. No blind retry or asset deletion.
Eight mappings preserve167 of217 review MeshParts. The complete asset-path Studio
review cannot be constructed honestly from partial delivery.

`integrate_review.py` writes the partial ledger and refuses fixture generation
while mappings are missing. Its adapter-generation branch is NOT executed or
Studio-validated. It is pending tooling, not a completed runtime integration.
`upload_review.py` refuses a second attempt when a failed log exists, so a future
session must inspect the recorded terminal operation and decide on a bounded
re-export/new upload; never erase evidence just to bypass that guard.

## Cost and validation

Canonical eight:169,800 visual tris/250 source visual objects/558 terrain collision
parts. Including four alternative dressings, source export44 visual MeshParts/
212,850 tris, plus558 collision MeshParts/44,464 tris. Grove is the largest new
source at25,052tris/60objects, below Batch1's accepted per-source upper envelope.

Combined2 bounded review:217 batched visual MeshParts/1,634,590 visual tris;
907 unique collision source meshes,1,675 placed collision clones expected.
Scenery alone337 authored meshes/1,057,198 tris, including853,830 grass tris,
batched into the217 presentation parts. Its24-piece bounding region is larger
than the accepted nine-piece scenery comparison; these are exported counts,
not new measured Studio performance results. Performance architecture gate stays
closed; no loader/collision acquisition optimization or playable quality reduction.

- Blender source/profile/manifold/Hull, variants, rotations/combined sampled seams,
  semantic balance and all14 FBX round-trips: PASS.
- Delivery audit: Python parse/allJSON, exact export bytes/SHA,602 source mappings,
  four matching terrain/collision identities,17 canonical sources: PASS;
  missing review mappings8/9/10 explicitly HOLD.
- Luau repository suite:1,063 passed/0 failed. Normal default Rojo build: PASS.
- StyLua with Windows endings reports unchanged `PropController.luau` differences.
  Selene `src tests`:75 errors/161 warnings/0 parse errors in unchanged Luau,
  including the generated suite. No unrelated formatting/refactor performed.
- GateA fresh normal-project Studio Play/cook/three source traversals: PASS as
  documented above. Full final AssetPreparation/ChunkLoader review, imported
  source collision, all-eight traversal, assembled socket crossings and final
  fresh-session visual review: NOT RUN due upload failure.
- Studio Output: normal hub boot/client ready; expected unpublished PlaceId0
  DataStore/ledger unavailability, missing EMBERFALL/ASTRAL_REACH production maps,
  legacy-chat debug warning. No claim these were repaired or are Batch2 errors.

## Final evidence / resume

External output root above owns `BurnedPlainsBatch2.blend`,
`BurnedPlainsCombinedReview.blend`, `BurnedPlainsProductionReview.blend`,
`batch2_source_sheet.jpg`, `combined_layout_sheet.jpg`, individual eight-source
top/eye/overview and four dressing views; `Combined1/2/3/` player-eye/elevated/
road/front views. Final accepted scenery comparison is
`Combined2/scenery_eye.png` and `Combined2/scenery_elevated.png`; the older combined
sheet deliberately retains the coarse-continuation evidence, not final scenery.
`exports/`, per-upload logs/mappings and raw GateA Studio results are preserved.

Next: resolve the recorded Roblox import; finish only missing review delivery;
generate opt-in fixture, then real AssetPreparation/ChunkLoader fresh Play,
uploaded collision/character/seam/visual tests and owner walkthrough. Do not
repeat terrain authoring, start Batch3 or move to AreaII before that gate.

## Cleanup

Main testing place untouched. The separate unpublished `Batch2ProductionReview.rbxlx`
was stopped and its task-owned208-mesh `Workspace.EmberfallBatch2GateCook` explicitly
removed; normal Rojo server/shared tree remains present. No final diagnostic
adapter or partially delivered scene was inserted. Accepted copies/recovery,
GateA evidence and external `.blend1` recovery remain intact. Keep intermediate
coarse-scenery evidence and partial successful uploads until the final test and
owner acceptance establish what can safely be retired. No older production assets
or manifests are superseded; no broad cleanup or existing-asset deletion.
