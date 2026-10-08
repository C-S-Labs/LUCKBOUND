# Burned Plains scenery scaling review — 2026-10-06

## Baseline and authority

New isolated branch agent/emberfall-scenery-scaling starts exactly at owner-accepted 73b918b. C:/Users/jhpel/branch/emberfall-walkthrough remains at that checkpoint. The owner checkout C:/Users/jhpel/LUCKBOUND is on agent/emberfall-burned-plains at b09a496 with prior mixed changes; it was not edited. Existing authority_manifest.json identifies its newer proof documents. This task inspected those separately instead of assuming they were committed in the walkthrough lane.

No Batch2, new playable chunks, AreaII, full-map proxy, main changes, push, merge or PR. Nine frozen terrain hashes match batch1_report.json. Original .blend, FBX, collision export and data module are unchanged. 627 exact authored colliders, 128 omitted interior safety segments and160 outer segments remain.

## Actual API failure

A bounded fresh Studio **client** LocalScript called AssetService:CreateEditableMeshAsync(Content.fromUri(snapshotId), {FixedSize=true}), retained each result, measured GetVertices/GetFaces/GetColors, destroyed all results between groups, and waited one second for release. Current accepted snapshot IDs were used; the historical failed neutral/compact strategy is retained externally under Emberfall_Walkthrough and is not silently conflated with this reproduction.

Observed warning: “Failed to create EditableMesh that was requested due to reaching memory budget limits.” The allocation returned nil, rather than failing permission or the per-mesh face/vertex ceiling.

| Retained working set | Results | Vertices / colors | Faces | Time |
| --- | --- | ---: | ---: | ---: |
| Terrain alone | 9/9 allocated |221,363 each aggregate|80,622|3.333 s|
| Grass alone |18/18 allocated|226,845 each aggregate|75,615|3.233 s|
| Terrain then grass, warmed assets |9 terrain succeeded; first grass returned nil|221,363 retained before failure|80,622 retained|0.833 s total; failed call0.115 s|

The failed grass request contained6000 faces/18,000 imported vertices. There is **no measured universal nine-mesh ceiling**: eighteen grass meshes fit alone. Imported corner normals/colors greatly expand editable storage relative to shared source-grid vertices. Grass pushed an already expensive terrain working set over this client's budget. Earlier compact code additionally retained source, mutable rebuilt and fixed conversion meshes during conversion, which raises peak allocation; its exact historical numerical failure point was not retained in available evidence.

Roblox documents strict device-specific client editable memory, FixedSize savings and shared references; server/Studio/plugin editing budgets differ from the Play client. See [EditableMesh](https://create.roblox.com/docs/reference/engine/classes/EditableMesh) and [AssetService](https://create.roblox.com/docs/reference/engine/classes/AssetService). The documented per-mesh60,000 vertices/20,000 triangles are different constraints and do not explain this reproduction. Neither an exact device budget in MB nor remaining editable MB was exposed/measured. No per-place object limit, MeshPart cap or asset-permission failure was observed. “Mesh API limit” was directionally correct but too vague: **client editable-memory working-set exhaustion** is the evidenced mechanism.

## Accepted runtime baseline versus counterfactual copies

The accepted73b918b walkthrough already uses ordinary baked appearance assets, not live client EditableMeshes. Terrain9/80,622 triangles; grass18/75,615 triangles (25,205 three-blade clumps); props8/59,737; roads2/11,559; fire1/1200; smoke1/2400. Playable/near visual total39 MeshParts. Scenery7/56,104 triangles mixes27 continuation surfaces13,824 triangles with65 peripheral trees42,280 triangles. Total46 visual MeshParts, plus627 authored collision MeshParts/50,016 triangles. Individual source grass blades are geometry inside18 batches, not75,615 Instances.

Actual accepted runtime appearance copies/recolour passes/EditableMesh allocations: **zero**, in both groups. The preceding table measures the proposed dynamic-copy cost, not hidden ongoing allocations in the accepted walkthrough. Original client failure timing/recolour timing is unavailable; no retrospective timing is invented. AssetPreparation caches ordinary immutable MeshParts on the server; ChunkLoader clones/places the real assets and colliders. Those reusable modules were inspected and left unchanged.

## Approaches actually compared

1. Smooth material/color-only continuation: existing accepted before images; zero editable cost but plainly missing blade silhouettes. Rejected as the shipped appearance target.
2. Imported full vertex-color editable copies: bounded real client probe above. Terrain+grass failed before any scenery allocation. Rejected for distant scenery regardless of object batching.
3. Batched baked single blades:55 surface/grass plus6 tree MeshParts,175,596 grass triangles; zero editable allocations. Studio stressed view read too dense because single blades were uniformly scattered. Rejected visually; candidate_single_blades_*.jpg and its profile retained.
4. Batched baked three-blade clumps: selected implementation.61 ordinary scenery MeshParts,175,263 grass triangles/58,421 clumps,40,264 ground/underlap triangles,42,280 preserved tree triangles. Maximum grass batch7806 triangles. Uses accepted clump dimensions .55–1.45 height/.17 half-width/.22,.12 lean, identical field/palette semantics and surface-seated geometry.

No invented texture system or open-ended LOD research. All replacement scenery IDs are attributable in scenery_asset_mapping.json. Original seven mixed batches stay in the old mapping for recovery but the adapter excludes their scenery role from preparation/placement and prepares61 new assets through the same AssetPreparation interface.

## Selected representation and burn behaviour

Playable/near: retain all18 frozen authored grass batches and9 terrain snapshots; no playable simplification or collision changes.

Near scenery: three-blade clumps baked into one ordinary mesh per256x256 continuation sector. Stratified placement has near-edge expected .0427 clumps/.128 triangles per square stud, matching accepted playable frequency before path/authoring exclusions. Blade bases are seated on the *actual exported triangles* through a tile-local BVH, not only an analytic surface.

Far scenery: same sparse silhouette representation, smoothly reducing occupancy from full at96studs distance from playable footprint to half at256studs. This is spatial authored density, not camera-driven popping. Keep real geometry across the entire existing ring, with coarse interior terrain and edge refinement. Very distant scenery beyond this ring is not authored or claimed tested; there is no additional hidden representation implemented.

Surviving/stressed/charred are baked per vertex from the exact assembled harmonic semantic-depth field, route length, approved thresholds, roughness and refuge influence. State counts20961/58389/95913 grass triangles. Trees preserve approved source placements and colors. An initial tree-only export lost canopy positioning because source transforms were not evaluated in the owning Layout1 scene; corrected export explicitly updates that scene before reading matrices. Earlier canopy-regression imports are retained for recovery, not used. No distant blade participates in runtime editable recolouring. This produces coherent fixed Layout1 scenery now. **A shipped arbitrary-seed deployment remains open**: it must select/export coherent scenery sectors or use finite palette-state grouping against its assembled field. This task does not claim that the pre-existing general playable appearance allocation problem is solved, or that fixed Layout1 IDs can be reused for different burn fields unchanged. The chosen geometry/resource representation can be used in a representative full-map snapshot without adding editable pressure.

## Scenery-side seam correction

Old continuation edges used16stud cells; frozen playable edges use4stud samples. Independent triangulation bridges the intermediate edge heights with a different chord. Read-only edge fixture compared652 overlapping exposed samples: old maximum vertical discrepancy0.3323631287stud; replacement0.0000877380stud. Coverage is bounded to points hit by both source surfaces, not an exhaustive all-corner proof.

New continuation samples the frozen edge at4stud spacing within24studs of the playable boundary, with shared perimeter samples on adjacent coarse fan cells. A scenery-only two-stud ribbon extends one stud under the frozen terrain and one stud outward, lowered .04stud. It covers import rounding without coplanar overlap. No frozen vertex, HOLLOW/CREST rule, shoulder, mouth, transition depth or collider changes. Matched charred/stressed Studio views show no former bright crack at the reviewed joins. No new profile system or broad terrain reshaping.

## Studio verification and cost

Final fresh Play session rebuilt the nine chunks via real AssetPreparation/ChunkLoader:39 playable visual +61 scenery +627 collision MeshParts. New scenery preparation/create/clone/placement total8.2205676seconds, including61 unique asynchronous asset creations. Recolour and editable allocation times are0. MeshPart count increases54 relative to seven old batches; batching solves editable memory, not by pretending total visual objects decreased. Added grass geometry is the required visible coverage.

Client bounded stress: eight extra copies of27 grass meshes =216 MeshParts/1,402,104 triangles; cloning/parenting0.0030633seconds; fixture destroyed afterwards. Assets shared, fixture offscreen. This does **not** establish GPU headroom or unique-asset streaming memory. runtime_profile.json records measurements.

Fresh means stop/start Play and a new client runtime, not restarting the Studio application or clearing asset caches. Final log has no new mesh/appearance errors. Existing DataStore403/profile fallback warnings remain because Studio API persistence is disabled; those are unrelated. Mesh APIs were available for the diagnostic probe; the selected scenery rendering requires no EditableMesh permission/setting. Local importer preset No upload, Anchored creates mesh IDs but did not publish a model/place. Studio Download a Copy unexpectedly also saved the current testing-place draft to Roblox (Output confirmed Saved new changes); no Publish action was invoked. The accepted external baseline place was not overwritten. Camera inspection used fixed callbacks and was cleared by stopping Play.

Reviewed views: matched charred/stressed elevated boundaries, grounded normal player eye, raised Waymark gameplay camera, ridge broad/high-point camera, diagnostic overview. The chosen implementation removes the obvious missing-vegetation line in those views. Diagnostic terrain banding remains accepted polish; universal every-camera/mobile acceptance is not asserted from six desktop captures. New saved local copy BurnedPlainsSceneryScaling.rbxl isa separate local file; original walkthrough place stays intact.

## Scaling and next test

Current ring covers1,769,472square studs =27 sector equivalents, three times nine playable footprints. Grass is175,263triangles/27 parts over that area; approximate per playable footprint at this3:1 ratio19,474 scenery grass triangles,3 grass MeshParts and6.78 total scenery MeshParts including terrain/trees. For illustration,50 comparable playable chunks imply about974k scenery grass triangles/150 grass batches/339 total scenery parts. This is linear geometry/object arithmetic, **not a promised frame rate, approved final area count or unique-memory estimate**.

Zero scenery editable allocation removes this representation from the client editable budget entirely. The ordinary eight-copy stress demonstrates repeatable cloning, not a quantified remaining memory percentage. Next representative full-map test must measure unique asset loading/cache cost, GraphicsMeshParts/total client memory, frame time/GPU/overdraw at broad views, streaming, low-end/mobile published-client behaviour, collider/instance counts and the retained near/playable appearance strategy. No full-map prototype constructed here. Arbitrary-route field/asset selection needs separate implementation before production rollout.

## Evidence and reproducibility

All external artifacts: E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling/.
- before_charred.jpg / after_charred.jpg; before_stressed.jpg / after_stressed.jpg: same camera pairs.
- after_player_eye.jpg, after_elevated.jpg, after_high_point.jpg, after_overview.jpg; scenery_comparison.jpg is the compact contact sheet.
- allocation_baseline.json; runtime_profile.json; studio_console.json; scenery_edge_measurement.json.
- EF_SCENERY_CONTINUATION.fbx, EF_SCENERY_TREES.fbx, SceneryScaling.blend, manifests and both candidate/final ID captures.
- BurnedPlainsSceneryScaling.rbxl: independent local Studio place with mapped assets/scripts.

After imports, map_scenery_imports.py records each source FBX, ID and exact destination and regenerates SceneryData. Run build_scenery_scaling.py and measure_scenery_edges.py only through tools/run_blender.py with a normal Windows token (restricted-token profile validation rejects launch). They read the frozen source/external assembly helpers and write only the new external task directory. AllocationProbe.client.luau is opt-in and intentionally excluded from the overlay; do not leave it enabled during performance runs. Overlay34873 includes SceneryData and the isolated adapter. No production AssetManifest replacement.

Whole src/tests formatter check initially rejected Windows CRLF line endings. With Windows endings it reports one pre-existing unchanged file, src/client/Controllers/PropController.luau. No unrelated formatting rewrite was made; applicable CI remains pending before integration. Task-file formatting passes repository settings.

Cheap checks passed: Python AST parsing and61 exact mapping references, pinned StyLua, Selene0 errors/0 warnings/0 parse errors, Rojo overlay build, regenerated INDEX_MAP. Broad1063-test gameplay regression suite was not repeated because src/tests and frozen collision were unchanged; no push/merge was requested.

## Cleanup recommendation

Retain accepted neutral/snapshot imports, original seven scenery IDs/batches, original place, source studies, recovery files, candidate single-blade imports/evidence and Blender .blend1 recovery. Their replacement is limited to this adapter. Only after owner visual acceptance and applicable CI/Studio validation should the task-created rejected single-blade imports and unused export recovery be removed. Never delete assets referenced by the accepted baseline/old mapping or owner-kept proofs. No cleanup deletion performed.
