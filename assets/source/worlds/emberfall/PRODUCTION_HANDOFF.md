# Emberfall production handoff — authoritative consolidated baseline

2026-10-08. **Stage2 locally consolidated; owner acceptance pending.**
Integration branch `integration/emberfall-production`, worktree
`E:/BlenderAIProjects/Worktrees/emberfall-production`, pinned main `34f6c1e`.
Shared runtime/schema/config/AssetManifest remain newer-main authority and unchanged.

Read the [main reconciliation](../../../../docs/audits/EMBERFALL_MAIN_RECONCILIATION.md),
[stage record](../../../../docs/audits/EMBERFALL_INTEGRATION_STATUS.md), and
[execution/validation result](../../../../docs/audits/EMBERFALL_CONSOLIDATION_RESULT.md).
The [Stage1 audit](../../../../docs/audits/EMBERFALL_CONSOLIDATION_AUDIT.md) remains
historical ancestry/authority evidence; its old main and proposed-stage language is superseded
by these current records. Scoped integration copied167 donor paths, preserving their bytes;
six shared document overlaps were reconciled without replacing main behavior.

## 1. Current approved state

Area I:17 authored Burned Plains sources (Batch1 nine + Batch2 eight), plus four
Batch2 dressing alternatives. Accepted authored edge/socket/collision contracts,
vegetation/scenery improvements and imported walkthrough evidence remain preserved.
The Batch2 delivery report's historical status is READY FOR OWNER REVIEW following
automated imported traversal; do not fabricate an additional manual acceptance event.

Area II: approved continuous settlement blockout, outer wall → village/market/streets
→ inner-wall transition → one selected complete castle. B is the damaged/burning
architectural baseline with enclosed boss/reward rooms; A is its catastrophe counterpart
with broad shallow arena. The entire castle is one oversized logical finale chunk.
Preserve this continuous scene and both variants; no splitting or redesign.

Overall target is approximately20 minutes including traversal, combat, exploration,
loot and finale. Exact timer behavior remains open. Existing runtime720-second metadata
is legacy; consolidation is not authorization to change it.

The [Area II production plan](../../../../docs/biomes/EMBERFALL_AREA_II_PRODUCTION_PLAN.md)
at `079882bbbcc389c82099f54dd6ef5fd6de2d5aeb` is owner-approved **planning authority**.
Exact boundaries/socket proofs and production work remain unimplemented.

## 2. Git authority and current locations

| Role | Branch / checkpoint | Current worktree |
|---|---|---|
| Committed content donor containing all production descendants | `agent/emberfall-area2-plan` / `079882b` | `E:/BlenderAIProjects/Worktrees/emberfall-area2-plan` |
| Final structural geometry/reference evidence | `agent/emberfall-area2-blockout` / `54668c5` | `C:/Users/jhpel/branch/emberfall-area2` |
| Recovered Batch2 delivery | `agent/emberfall-batch2-production` / `313e259` | `E:/BlenderAIProjects/Worktrees/emberfall-batch2-production` |
| Accepted scenery / walkthrough checkpoints | `3e15bc4` / `73b918b` | `E:/BlenderAIProjects/Worktrees/emberfall-scenery-scaling`; `C:/Users/jhpel/branch/emberfall-walkthrough` |
| Final Batch1 source checkpoint | `agent/emberfall-batch1` / `36b719c` | `C:/Users/jhpel/branch/emberfall-batch1` |
| Approved grassland reset and proof docs | `agent/emberfall-burned-plains` / `b09a496` **plus48 dirty entries** | `C:/Users/jhpel/LUCKBOUND` |
| Historical terrain-foundation experiment | `b09a496` plus11 dirty entries | `C:/Users/jhpel/branch/emberfall-terrain-foundation` |
| Stage1 report only | `agent/emberfall-consolidation-audit`, from `origin/main aa22e3d` | `E:/BlenderAIProjects/Worktrees/emberfall-consolidation-audit` |

Current authoritative repository workspace: **integration/emberfall-production** from
main34f6c1e. Historical worktrees in the table are recovery/evidence, not alternate current
production handoffs. Main's75 new commits and137 changed paths were reconciled first.
129 unrelated donor paths remain excluded. No donor branch merge was performed.

Verified preservation backup: `E:/BlenderAIProjects/Backups/Emberfall_Consolidation_20261008`
(1168 read-only files, full `preservation_manifest.json` with per-file SHA256).
[Backup summary](../../../../docs/audits/EMBERFALL_PRESERVATION_SUMMARY.json) pins its manifest hash.
Owner/historical checkout HEADs and dirty bytes remain intact; no stash/reset/cleanup.

## 3. Editable source registry

Full source hashes: [blend inventory](../../../../docs/audits/EMBERFALL_BLEND_INVENTORY.json).
Collection/layer structure: [readback](../../../../docs/audits/EMBERFALL_BLEND_READBACK.json).

| Owned source | Exact file / selected content |
|---|---|
| Batch1 frozen playable geometry | [BurnedPlainsBatch1.blend](E:/BlenderAIProjects/Runtime/Emberfall_Batch1/BurnedPlainsBatch1.blend): nine EF_* source scenes/collections and matching COLLISION_EF_*; Layout1/2/3 are derived review |
| Batch2 new geometry and alternatives | [BurnedPlainsBatch2.blend](E:/BlenderAIProjects/Runtime/Emberfall_Batch2/BurnedPlainsBatch2.blend): eight canonical EF_* sources, four DRESSING_B alternatives |
| Accepted scenery representation | [SceneryScaling.blend](E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling/SceneryScaling.blend): scenery collections only; its copied playable sources are not a second editable authority |
| Shared visual/material foundation | [BurnedPlains.blend](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend), source BP_* material palette, preserved input helpers |
| Settlement, outer/inner wall, castle grounds and B/A | [EmberfallAreaII.blend](E:/BlenderAIProjects/Runtime/Emberfall_AreaII/EmberfallAreaII.blend): AREA_II_SHARED, INNER_WALL_SHARED, CASTLE_GROUNDS_SHARED, CASTLE_EXTERIOR_SHARED and selected CASTLE_B_STRONGHOLD or CASTLE_A_CATASTROPHE |

AreaII exact SHA256:
`b2b3e160efb6d30db4831448ebf540f2c13ae79d25b09d5e37c2fbc5a5e9e49d`.
View layers: `VARIANT_B_STRONGHOLD` / `VARIANT_A_CATASTROPHE`.
Exclude all hidden retained/proxy/correction alternatives from selected assembly/export.

Batch1 lane .blend files remain original authoring/rebuild inputs; final aggregate owns
frozen accepted source state. GateA/CombinedReview/ProductionReview are evidence and
derived packaging, not additional editable libraries. Keep all blend1/Input_/Before*
copies. Existing files are appended copies with no library links; the master links collections without local overrides.
[EmberfallMaster.blend](E:/BlenderAIProjects/Projects/Emberfall/EmberfallMaster.blend)
has six review scenes,60 linked collection selections, four resolved libraries,
zero local meshes/overrides plus an empty Blender startup scene.
[Master instructions](master/README.md), [source registry](master/source_registry.json) and
[build/reopen validation](master/master_validation.json) own exact links/hashes.
WholeWorld B/A use a clearly provisional side-by-side AreaI translation(-2200,0,0);
this is not an approved route/seam. Source catalogue contains all17+4; Layout1 is a
selected accepted review, not a final17-chunk whole-session recipe.

## 4. Contracts, production evidence and mapping links

Current accepted grassland design and frozen proof contracts are preserved here:

- [EMBERFALL.md](../../../../docs/biomes/EMBERFALL.md)
- [EDGE_PROFILE_REVIEW.md](EDGE_PROFILE_REVIEW.md)
- [BURNED_PLAINS_REVIEW.md](BURNED_PLAINS_REVIEW.md)

Consolidated production evidence (dated reports remain historical):

- [Batch1 authoring](batch1/AUTHORING.md),
  [Batch1 review](batch1/BATCH1_REVIEW.md),
  [owner walkthrough](batch1/OWNER_WALKTHROUGH.md).
- [Scenery review](batch1/SCENERY_SCALING_REVIEW.md),
  [scale fixture review](batch1/FULL_MAP_SCALE_REVIEW.md).
- [Batch2 plan](batch2/BATCH2_PLAN.md),
  [recovered delivery/Studio review](batch2/DELIVERY_STUDIO_REVIEW.md).
- [Castle actual-B correspondence](area2/CONSISTENCY_REVIEW.md).

Preserve these JSONs byte-for-byte at their existing repository-relative paths:

| Preserved repository path | Status |
|---|---|
| `tools/studio/emberfall_walkthrough/asset_mapping.json` |673 accepted-review/provenance entries; retain active and neutral IDs, importYaw180, center/size/fidelity |
| `tools/studio/emberfall_walkthrough/scenery_asset_mapping.json` |61 accepted baked-layout scenery records; zero EditableMesh |
| `assets/source/worlds/emberfall/batch2/source_export_manifest.json` |602 source assets,44 visuals+558 collision; exact exported hash/transform provenance |
| `assets/source/worlds/emberfall/batch2/asset_mapping.json` |602 source IDs,323 review provenance IDs,17 delivered Models;299 active presentation parts |
| `assets/source/worlds/emberfall/batch2/review_bounds_manifest.json`, `review_cell_manifest.json` |Final bounds/cell replacement selections, original failed entries kept inactive |
| `tools/studio/emberfall_scale_test/unique_asset_mapping.json` |Diagnostic only; keep effective fallback selection and quarantine |

External exports/evidence/place snapshots are indexed by exact path/hash in the
[external ledger](../../../../docs/audits/EMBERFALL_EXTERNAL_LEDGER.json). Keep stable
Runtime/Emberfall_Batch1, Batch2, Walkthrough, SceneryScaling, ScaleTest and AreaII paths.
No exports or uploads are required simply to establish a unified handoff.

Ordinary default.project and AssetManifest still do **not** register this as an Emberfall
expedition kit. The three `emberfall-*.project.json` overlays are opt-in reviews/diagnostics.
Parked Default-fidelity Batch1 collision is not the accepted Hull/Precise template.

## 5. Validation, open decisions and next task

Preservation,17-source counts/contracts, mapping byte equality, master links/hash checks,
current-main unit/loader/syntax/lint and four Rojo builds are recorded in the result report.
No geometry was re-exported and no ID/upload/Studio changes occurred. Existing accepted
collision/geometry correspondence evidence remains valid because source/manifest bytes
are unchanged; no expensive recooking or repeated walkthrough was performed.

Open for subsequent production: AreaII exact boundaries/socket/common interface proof,
A reward provision, full-session timer, target devices/published readiness, final AreaI
recipe, arbitrary-route baked-state selection and collision packaging. None permits
silent implementation during consolidation. New master global placement remains a
provisional reference until owner reviews it.

**Next task: owner accepts consolidated handoff/master, including A/B views and provisional
montage.** Then a separately authorized bounded AreaII modular-production proof may begin
from the approved plan; do not start it by inference. Normal expedition registration,
collision packaging and timer decisions remain separate runtime/content tasks.

Historical generator/export scripts often pin former worktree paths and may overwrite
external outputs. They are evidence/rebuild recipes, not safe rerun instructions for
this consolidation. Do not rerun authoring/export/upload scripts; use the linked master
recipe and read-only validator only. Review project overlays retain existing repo-relative
paths and newer main modules. Source directories remain stable. New master is derived:
rollback Git by choosing a local stage checkpoint/new branch; retain external sources,
backup and master evidence, never reset dirty historical worktrees.

No authoritative geometry, production exports or existing IDs were replaced in Stage2. Retain all sources, old studies, exported
FBX/asset IDs, failed delivery/bounds/cell evidence, diagnostic fixtures and hidden recovery.
Recommend archiving obsolete active-navigation iterations only after consolidated owner
acceptance and applicable CI/targeted Studio validation; do not delete referenced/kept files.
