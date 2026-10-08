# Batch 2 delivery recovery and imported review

Status: **READY FOR OWNER REVIEW**. Single agent; isolated
`agent/emberfall-batch2-production`, resumed from `67c806d`.
Accepted Gate A `2af9994`, production HOLD `4bdc59d`, index `67c806d`,
planning `eacdb24`, Batch 1 and owner checkout are preserved.

## Original export 8 failure

Read-only reinspection of operation `fea2f937-03a8-4978-8c70-27d22ddf4c2d`
still returned done/Unknown Error, with no response or asset ID to recover.
The original operation/log and `upload_hold.json` remain historical evidence.
Failed file8: 18 meshes,153,000 triangles,8,085,372 bytes; successful files3–7
have the same mesh/triangle counts and comparable or larger files/bounds.
Its local round-trip had passed; its SHA was unchanged for the single controlled
new-only retry. That retry succeeded. This supports transient Roblox processing;
the service's precise internal cause is unknown. No deterministic defect or
metadata/request difference was established. Successful exports0–7 were not retried.

| Delivery | New Model ID | Result |
|---|---:|---|
| Review8, unchanged controlled retry | 77627139767340 | PASS,18 meshes |
| Review9, first delivery | 84606504499635 | PASS,19 meshes |
| Review10, first delivery | 101975381652352 | PASS,13 meshes |
| Scenery bounds0 | 75950126993814 | PASS,76 meshes |
| Scenery bounds1 | 117153955200676 | PASS,28 meshes |
| One scenery cell partition | 72653471665682 | PASS,2 meshes |

Reusable source Models88065938858510/88157428738073/108592230513646 and their
602 mappings are unchanged. Original review0–7 Models/mappings remain exact.
`asset_mapping.json` preserves all323 review mesh IDs, including inactive recovery
provenance; ReviewData selects299 active presentation parts. Existing Roblox assets
were never updated/replaced/deleted. Six new Models were created in this recovery.
Approved external tool remained unmodified; credentials were never inspected.

## Narrow imported-artifact corrections

First imported review exposed23 scenery objects beyond Roblox's2048-stud part
dimension: CreateMeshPartAsync succeeded, but instance sizes clamped, visibly
distorting continuation land. This concerns the bounded assembled export, not
canonical playable sources. Spatially partitioned ONLY those scenery face batches:
23→104 pieces,187,898 triangles unchanged, original coordinates/colors unchanged.
Two FBX round-trips passed; `review_bounds_manifest.json` records replacements.

One new cell mesh129911637407003 still failed two targeted Studio acquisition
attempts despite a successful upload and read-only asset delivery returning154,187
bytes without delivery errors. Internal content-processing cause remains unknown.
Partitioned ONLY its2458 faces into two1229-face meshes; one additional round-trip
passed. New meshes118200763683119/70949029507308 load successfully.
`review_cell_manifest.json` records this replacement. Original failed cell is retained
inactive. No canonical source geometry, sockets, collision or accepted Batch1 changed.
Final299 presentation meshes retain the original1,634,590 visual triangles.

## Real loader and walkthrough — PASS

Fresh separate local PlaceId0, normal LUCKBOUND tree plus explicit review adapter:
unchanged AssetPreparation→ChunkLoader. All44 reusable source/variant visuals
resolve through final mappings. Cook907 unique authored collision meshes once;
clone1675 placed colliders.24 actual terrain placements, zero fallback floors,
299 presentation parts, zero scenery EditableMeshes or runtime recolouring.
No unknown-kit warning: cook templates remain in ServerStorage until preparation.
368 interior safety segments removed;400 outer boundary parts retained.

162 bounded centre/socket/±12 shoulder rays: zero misses; max socket/seam difference
0.0001220703125stud. Collider centre error0; size error0.0000431584stud. All275
non-terrain presentation dimensions now match, with zero clamping error. H/H,C/C,
H/C and all four yaws occur in this route. `studio_validation.json` records results.

Combined2 long repeated24 route (~6030stud): all8 new sources plus Windward,
Clearing,Fenceline,Orchard,Ridge. Swale/Shoulder/Saddle×3;
Quiet/Ditch/Clearing/Grove/Raised×2; Fieldstead/Orchard once. Four approved dressing
alternatives are placed. Normal ControllerManager movement reached waypoint1551
of1553 (penultimate exit), all24 placements visited, health100,372.002s, no
translation after entry. Roads and collision cross imported seams continuously.
Quiet bend timing and lateral drift differ; terrain repeats remain discernible
from overview but do not add repeated landmarks at gameplay height. Grove framing,
rare fieldstead and burn-state spacing preserve quiet→moderate→memorable pacing.
This supports repeated-source resistance in this bounded route, not arbitrary seeds.

First client preload stalled with25 IDs Loading (including older terrain/collision),
empty queue; one targeted client ID returned Failure. Preserved that evidence,
then ran ONE fresh Play session, without upload changes. All1974 MeshParts,
1074 unique IDs preloaded successfully with zero failures. No new import/error
messages in the final session. Existing unpublished-place DataStore/ledger warnings,
unregistered production world maps, legacy-chat dev-command limitation and debug/
placeholder messages remain; no API settings were changed to suppress them.

## Owner launch and scope

Open `E:/BlenderAIProjects/Runtime/Emberfall_Batch2/EmberfallBatch2Walkthrough.rbxlx`
in Roblox Studio. Press Play. Wait for **READY — Batch 2 • 24-placement
repeated-source review**; character is automatically placed at the route entry.
Use normal WASD/mouse controls and follow the dirt road. No commands, uploads,
manual reconstruction, Rojo connection or benchmark setup are needed.
This is a separate local review copy, not the main LUCKBOUND testing place.

Rebuild from this worktree with `rojo build emberfall-batch2-review.project.json -o
E:/BlenderAIProjects/Runtime/Emberfall_Batch2/EmberfallBatch2Walkthrough.rbxlx`.
Optional Studio commands under `tools/studio/emberfall_batch2/`: ValidateImported
(Server), ClientLoadCheck (Client), WalkImported (Client); not auto-run for the owner.
Default Rojo project contains none of the three opt-in review scripts/data.
Runtime review trees disappear on Stop; dedicated copy/versioned fixture persists.
The main testing place, normal runtime modules and place settings were untouched.

Seventeen sources remain sufficient for initial Area I authoring. No specific
library deficiency emerged that requires Batch3. This is not a claim that Area I
alone supplies the complete twenty-minute Emberfall runtime. Next: owner walkthrough;
apply only concrete feedback, then consider Area II planning.

## Checks, evidence and cleanup

Carried forward unchanged: source/profile/collision audits,14 original FBX
round-trips,1063 repository tests and GateA traversal. Not rerun unnecessarily.
This recovery:3 corrective FBX round-trips;17 export SHA/byte checks; Python compile/
JSON/mapping sanity; targeted opt-in StyLua/Selene (zero errors/warnings/parse errors);
normal and review Rojo builds; actual imported loader/seams/full traversal/fresh preload.
Prior unrelated PropController StyLua and broad Selene75errors/161warnings remain.
No full-map benchmark, source reauthor, Batch3, performance architecture or src edits.

Evidence root: `E:/BlenderAIProjects/Runtime/Emberfall_Batch2/`:
`studio_combined_overview.png`, `studio_quiet_bend_eye.png`,
`studio_fieldstead_elevated.png`; existing source/variant/combined Blender evidence
remains. Screenshots precede the corrected Batch2 status-label text.
Upload/reinspection logs and export recovery reports remain in that same external
root; versioned manifests and `studio_validation.json` supply compact provenance.

Cleanup recommendation: final fresh-session checks now allow older *review copies*
Batch2OwnerReview.rbxlx and EmberfallBatch2OwnerReview.rbxlx, oversized review
scenery and the failed single-cell artifact to retire from active review use.
They and their mappings/logs remain preserved for recovery; do not delete assets
or evidence automatically. Keep canonical reusable/source exports and accepted
Batch1/test copies. The main place acquired no temporary fixtures.
