# Emberfall production consolidation — local execution result

2026-10-08. Branch `integration/emberfall-production`, isolated worktree
`E:/BlenderAIProjects/Worktrees/emberfall-production`. **Owner acceptance pending.**
Main is pinned34f6c1ea81f6825b4f0a251e9c13623d532b1c44; donor079882bbbcc389c82099f54dd6ef5fd6de2d5aeb.
No donor ancestry merge; no push/PR/main merge, Studio changes, export/upload, source moves or AreaII production.

## Revised authority and exclusions

[Main reconciliation](EMBERFALL_MAIN_RECONCILIATION.md) and [revised groups](EMBERFALL_RECONCILED_FILE_GROUPS.json)
record all137 changed paths sinceaa22e3d. Main's expedition rifts/arrival/payout,
hub sky ecosystem and movement/animation implementations remain intact. Chunk loader/
chunk schemas/content used by review fixtures remain compatible; portal and sky validators
are preserved. No Emberfall-specific donor content was superseded or already present.

167 scoped source/evidence/fixture paths remain byte-identical to079882b. The129 unrelated
paths remain excluded. Shared src/tests/config/default.project/AssetManifest/AGENTS and
index generator have zero diff against34f6c1e. INDEX/INDEX_MAP/STATUS/WORKLOG/ART_DIRECTION/
PROTOTYPE_BUILD_SPEC were reconciled rather than replaced. Main §7.8 is preserved.
Owner grassland design/frozen contract documents take precedence over early volcanic/AreaIV
proposals. AreaII plan is approved planning authority, not permission for implementation.

## Preservation and stages

Verified backup: `E:/BlenderAIProjects/Backups/Emberfall_Consolidation_20261008`.
1168 read-only files,1,943,438,153 bytes; all copied-file SHA256s reverified after integration.
Includes external accepted sources, exports, renders, place evidence, recovery variants,
66 relevant dirty entries, donor files and audit evidence. [Backup summary](EMBERFALL_PRESERVATION_SUMMARY.json)
pins the full manifest.75 total protected dirty entries and historical HEAD/status snapshots
remain unchanged.272 external hashes (95 blend/blend1 +177 artifacts) still match Stage1.

Local completed stage checkpoints:

| Stage | Commit |
|---|---|
| Reconciliation/preservation |576b89e|
| Approved foundation/frozen contracts |95feaf1|
| Final Batch1/2 source manifests/evidence |c1c74ce|
| Existing mappings/isolated fixtures |a55c499|
| AreaII structural references/approved plan |0d4b22e|
| Linked review master/registry |7a9fd79|
| Current documentation/handoff |678d681|

Final validation is separately checkpointed after this table;
use branch log for its exact HEAD.
[Changed-file ledger](EMBERFALL_CONSOLIDATION_CHANGED_FILES.json) lists every integrated path
and the seven preceding checkpoints. Final commit adds this ledger and updates this record/index;
production changes are confined to Emberfall sources/evidence, opt-in fixtures and reconciled docs. [Production handoff](../../assets/source/worlds/emberfall/PRODUCTION_HANDOFF.md)
is the current entry point; historical reports retain original acceptance dates/statuses.
[Validation JSON](EMBERFALL_CONSOLIDATION_VALIDATION.json) provides machine-readable gate results.

## Source/master architecture

Editable authorities remain at their original paths: Runtime/Emberfall_Batch1/BurnedPlainsBatch1.blend
(nine frozen sources), Runtime/Emberfall_Batch2/BurnedPlainsBatch2.blend (eight+four alternatives),
Runtime/Emberfall_SceneryScaling/SceneryScaling.blend (scenery authority), and
Runtime/Emberfall_AreaII/EmberfallAreaII.blend (continuous settlement/shared architecture/B+A).
Shared palette/foundation source remains Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend.
Full paths/hashes and evidence are in the handoff and pinned source registry.

Master: `E:/BlenderAIProjects/Projects/Emberfall/EmberfallMaster.blend`, SHA256
`e80900b51d6d723df893f511b2005a0889573c3e8da61eca9705bad36f77f493`.
Six selectable review scenes plus empty startup Scene;60 collection selections and four
resolved libraries;0 local meshes or overrides. Separate AreaII B/A scenes retain exactly
selected shared roots plus one castle; hidden recovery/proxies are excluded. WholeWorld
B/A are explicitly PROVISIONAL side-by-side montages, AreaI(-2200,0,0), not an approved
seam or route. SourceCatalogue has17 sources plus4 dressing alternatives; AreaI uses
accepted Layout1/scenery. No claim of final17-chunk gameplay recipe or duration.

[Master README](../../assets/source/worlds/emberfall/master/README.md) gives review/rebuild
instructions; [registry](../../assets/source/worlds/emberfall/master/source_registry.json)
and [reopen checks](../../assets/source/worlds/emberfall/master/master_validation.json)
verify link resolution, source hashes and B/A exclusivity. Review contact sheet is
`E:/BlenderAIProjects/Projects/Emberfall/CastleVariantsContactSheet.png`.

## Validation and practical limits

- PASS: all167 donor files byte equality;1168 backup hashes/read-only attributes;
  historical worktree preservation;272 external hashes; four approved proof hashes
  and authority-document checks retained.
- PASS:9+8 unique playable sources, four alternatives,24-wide HOLLOW/CREST sockets;
 602 Batch2 assets44 visual+558 collision;673 walkthrough mappings,61 scenery records,
 602 source IDs and17 model records, no pending review files. Existing mappings unchanged.
- PASS: source Blender hashes unchanged, thus accepted terrain/collider mesh signatures,
  frozen socket profiles and AreaII/B/A structural correspondence preserved. Existing
 collision and imported walkthrough evidence reused; no cook/FBX/upload/Studio rerun.
- PASS:1299 units;4280 loader differential cases with multipart/yaw/portal/atomic-failure checks.
- PASS: Luau syntax parse via uncalled-function compilation for src/tests/review fixtures
 (installed CLI lacks luau-analyze); all Emberfall Python parses. Forbidden module scan clear.
- PASS: default project and three isolated Emberfall overlays build with Rojo7.7.
- PASS: pinned StyLua2.0.2 against LF materialization matching Git/CI. Raw Windows CRLF
 checkout check reports newline diffs; no code reformatted. Generated test bundle retained
 externally, not committed or linted as source.
- BASELINE FINDINGS: Selene0.28 reports83 errors/96 warnings/0 parse errors in unchanged
 main src/tests (including standalone test __require shim names). Selene is not a CI gate
 in current main; consolidation does not alter these files or fix unrelated findings.
- PASS final gates: repository index current,42 current handoff/report links resolve, protected
 shared-main paths unchanged, excluded donor paths absent from diff, clean local checkpoint.

No remote CI run was requested or possible without pushing. Automated checks establish
preservation and integration compatibility, not an additional owner visual acceptance event.

## HOLDs, next task and rollback

No unresolved high-risk content/runtime conflict blocks this local consolidation.
Owner must accept master B/A scenes and provisional montage. Placement/seam/final AreaI
recipe, ~20-minute timer behavior (legacy720s untouched), A reward provision, common inner-wall
production socket, device budgets/published readiness and arbitrary-route baked-state
selection remain HOLDs. Ordinary runtime does not register the authored Emberfall kit.
Next separately authorized task: bounded AreaII modular-production proof from approved plan.

Rollback by selecting any local stage checkpoint on a new review branch/worktree; never
reset owner/historical worktrees. Source rollback uses verified manifest-addressed backup
only if an actual source corruption occurs. Master is derived and can be recreated from
pinned recipe after explicitly handling existing output; source libraries must never be saved.
Retain every historical source/blend1/review/failed mapping/delivery/export and new master
artifact. Recommend future archival/navigation cleanup only after owner acceptance and
applicable validation; no deletion or cleanup was performed or is authorized here.
