# Emberfall consolidation — reconciliation against main34f6c1e

2026-10-08. Owner authorizes updated-main reconciliation and continuation if no unresolved high-risk conflict.

## Decision

Proceed from pinned main `34f6c1ea81f6825b4f0a251e9c13623d532b1c44`, donor `079882bbbcc389c82099f54dd6ef5fd6de2d5aeb`.
The original167 source/evidence/opt-in-fixture paths remain safe: zero are present on newer main, zero were changed there.
No accepted Emberfall-specific geometry/content is superseded by the newer runtime work.
No unresolved high-risk conflict requires an owner design decision.

## Main changes and authority

137 changed paths since aa22e3d: expedition rifts and payout/arrival authority (PR158), living hub sky/creature libraries (PR159), and owner-accepted movement/animation baseline (PR160).
All shared runtime, schemas, configuration, AssetManifest, tests, normal Rojo project, tooling and repository-wide guidance remain byte-identical to34f6c1e.
ChunkCore, ChunkLoader, AssetPreparation, ChunkAssetCore and ChunkKitCore did not change; review adapters use these existing APIs.
Schema adds portals and skyCreatures validators without altering existing chunk validation. Types expands ExpeditionEndPayload; the isolated review adapters do not construct it.
New portals/movement/sky behaviors supersede older shared claims in donor history, not accepted Emberfall geometry.
Do not copy donor runtime/config/mapping implementations, inherited VV enemy work or donor global documents wholesale.

## Overlap and file treatment

| Group | Treatment |
|---|---|
|138 Emberfall source/evidence +29 review/project paths|Pinned donor copies; maps/manifests/fixture behavior retained exactly|
|INDEX, INDEX_MAP, STATUS, WORKLOG|Keep newer-main facts/history; add scoped current handoff; regenerate map|
|ART_DIRECTION, PROTOTYPE_BUILD_SPEC|Keep main portal/sky/movement text; add current Emberfall-specific contract/plan pointers. Preserve main §7.8; claim no amendment|
|CHUNK_AUTHORING, CHUNK_DROP_IN, MODULAR_MAPS|Keep main general contract; add bounded Emberfall frozen-profile/oversized-finale/urban-planning guidance|
|EMBERFALL.md/reference01|Accepted dirty grassland owner authority, reconciled with later approved settlement/castle decisions. Retain old reference bytes as historical; no inferred deletion|
|AreaII production plan|Preserve proposal/evidence, update approved-planning status only; no implementation|
|129 original excluded donor paths|Still excluded; no VV enemy import. New main content remains inherited unchanged|

Exact137 changed paths, six overlaps, safe paths and exclusions: [revised groups](EMBERFALL_RECONCILED_FILE_GROUPS.json).
Original [branch matrix](EMBERFALL_CONSOLIDATION_AUDIT.md#3-branch-and-worktree-integration-matrix) remains accurate for donors; replace its base/ancestry conclusion with this reconciliation.
Main and donor now diverge:75 main-only commits/31 donor-only; common ancestor aa22e3d. File integration avoids importing that divergence.

## Preservation and revised gates

Original protected75 dirty entries and272 external hashes pass unchanged. Verified read-only backups:1168 files including66 relevant dirty status entries, all named external source/evidence families,167 donor files and original audit.
Backup root: `E:/BlenderAIProjects/Backups/Emberfall_Consolidation_20261008`.
[preservation summary](EMBERFALL_PRESERVATION_SUMMARY.json) pins the full external preservation manifest hash.

Retain original audit §8–9 gates. Use current1299-unit suite, current loader differential/portal checks, current formatter/Selene, and current Rojo/index tooling.
Check normal plus three opt-in builds against current rift/sky/movement modules; do not invoke Studio or re-export/upload.
Hash-check all shared src/tests/default project/tooling against pinned main, all donor IDs/manifests against donor, and accepted external files after master creation.
Source roots remain stable. Master-only provisional transforms require owner visual acceptance.
No new schema/runtime capability or timer change is introduced. Remaining AreaII cuts/sockets, A rewards, device budgets and arbitrary-route appearance stay HOLD.

No production source was replaced by this reconciliation. Keep all donor/historical worktrees and recovery until final acceptance/CI gates; no cleanup authorized.
