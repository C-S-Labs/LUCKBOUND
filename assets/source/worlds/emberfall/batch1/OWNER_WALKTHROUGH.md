# Burned Plains Batch 1 â€” owner walkthrough

This is an isolated Studio-only fixed Layout1 adapter, on agent/emberfall-batch1-walkthrough, based on frozen Batch1 checkpoint 36b719c. It does not register a complete expedition kit, modify production Systems/content IDs, or author Batch2. AssetPreparation and ChunkLoader are the existing unchanged modules in the local LUCKBOUND testing place; the adapter supplies approved fixed layout/content and exact imported collision templates.

## Launch

Complete local place copy: E:/BlenderAIProjects/Runtime/Emberfall_Walkthrough/BurnedPlainsOwnerWalkthrough.rbxl. Open it in Studio and press Play. It preserves the full local testing place plus the isolated adapter; no publish occurred.

The current luckbound local testing Studio place has the overlay connected on localhost:34873. Press Play (not Run); click BEGIN if the existing intro appears. Wait for exact collision preparation and the walkthrough status. The character spawns automatically in Windward Meadow, on authored collision, at approximately (19920,1003,1). Follow the dirt road. Existing movement/camera controls remain active. Stop/Play returns to entry. DataStore API warnings only mean this test does not persist profiles.

To restore the overlay, run rojo serve emberfall-walkthrough.project.json --port 34873 from C:/Users/jhpel/branch/emberfall-walkthrough and connect the Studio Rojo plugin to that port. The overlay preserves unknown instances and adds three task-owned modules to the existing complete game. WalkthroughOverlay.rbxlx is only the overlay, not a standalone game. No manual asset uploads/ID replacements or Mesh API settings are needed for the approved snapshot. Studio-only guards prevent this adapter running in published servers.

## What is loaded

Approved Layout1, unchanged nine-piece order: Windward Meadow (90), Orchard Bend (90), Open Field Clearing (180), Drainage Crossing (180), Switchback Bank (180), Fenceline Rise (270), Waymark Terrace (270), Burn Front Verge (180), Ridge Ascent (0). This bending return route exercises HOLLOW/CREST, ascent, rotated turns, road continuity and semantic-depth fire progression. Origin (20000,1000,0) separates it from the existing hub/probes. Model is under Workspace.ExpeditionStage for the existing controller's expedition profile. The model is persistent for this bounded walkthrough; this is not a production streaming budget decision.

Nine terrain meshes, 18 grass meshes, eight batched prop meshes, two road meshes, seven non-playable scenery meshes, one fire and one smoke batch; 627 exact authored MeshPart colliders plus 160 outer safety segments through ChunkLoader. No fallback terrain floors. Dressing/scenery is non-collidable; terrain uses exact authored collision and required Hull/PreciseConvexDecomposition. No geometry was reshaped after assembly.

## Appearance exception explicitly approved by owner

Nine-chunk client EditableMesh allocation exceeded Studio's budget. Fixed-size and compact-copy experiments did not close the full-run budget. Studio rejects CreateAssetAsync publishing in this context. Production reusable appearance allocation remains OPEN.

The owner authorized a Layout1-only appearance snapshot baked from the exact approved semantic assembled field and transformed refuges. Only export-copy color attributes changed; frozen geometry, normals, topology, collision and sources stayed untouched. Terrain/grass use snapshot IDs; local vegetation/wooden props retain the already-approved assembled stages. This is not a reusable permanent green/yellow/black variant library. Other layouts require their own authorized assembly snapshots or a solved runtime appearance budget. Approved assembled balance stays 18.88/31.05/50.07.

## Import correction

Measured FBX imports reverse local X and Z (180-degree yaw) relative to Blender authored coordinates. The initial adapter failed to compensate, creating floating roads, visual walls and misoriented collision. A measured Switchback CREST vertex appeared at the opposite edge: imported X=-128 represented authored X=+128. Apply a single 180-degree mesh-local rotation around each bounding-box centre after loader placement to ALL imported visual/collision meshes. Keep authored centre translations, sockets and chunk yaws unchanged. The fixed data importYaw=180 records this conversion; it is not terrain deformation or a new profile. Diagnostic socket markers are hidden and non-queryable. The approved source dirt-road material tint is restored in the adapter.

## Asset mapping / preserved files

All IDs created during this task are mapped asset-by-asset in tools/studio/emberfall_walkthrough/asset_mapping.json: source export, key, source dimensions, fidelity, assetId and precise WalkthroughData.luau ids destination. neutralAssetId preserves pre-snapshot provenance. New IDs do not overwrite production AssetManifest entries.

External exports, IDs, evidence and allocation experiments: E:/BlenderAIProjects/Runtime/Emberfall_Walkthrough. Frozen source: E:/BlenderAIProjects/Runtime/Emberfall_Batch1/BurnedPlainsBatch1.blend. Approved foundation/modularity/production-gate/edge proofs remain preserved. Existing Studio fixtures remain separate. Initial unevaluated export is retained under ServerStorage.EmberfallWalkthrough_UnevaluatedExport and is not referenced. Final imports are parked in ServerStorage; runtime is built from IDs and source templates, not scratch geometry.

## Validation and owner review

Fresh Rojo overlay build and formatting; 1063 existing tests passed. Full run loads nine exact terrain meshes, all intended visual batches and 627 authored colliders with FloorCount=0. Quarter-yaw transforms are approved Layout1. Actual-controller short crossing checks distinguish physical movement from the Studio assistant navigation tool, whose Humanoid MoveTo does not drive LUCKBOUND's ControllerManager. Corrected CREST crossing moved from x20155 to x20076, health100. Corrected eight-join/48-ray probe: no misses, maximum sampled cooked step 0.00006103515625 stud; runtime_validation.json and corrected entry/crest screenshots are beside the exports. The initial misoriented collision catch was an import error, not a frozen source defect, and disappeared after correcting all mesh frames.

Please inspect road grades, shoulder/seam catches, ridge traversal, camera-height joins, grass density, burn readability, scenery edges, repeated tree groups and pacing. Diagnostic banding remains accepted polish. Smoke/fire are source mesh representations, not final particle/performance polish. Props are visual dressing here, not an added prop collision system. Mobile/published-place performance and full-run EditableMesh allocation remain unverified/open. No Batch2 expansion.

Keep the neutral imports, snapshots, original proofs and unused first export until the owner accepts the replacement walkthrough. No obsolete files have been deleted; no unrelated production world was changed.

## Owner feedback — shared-border fix, 2026-10-06

Owner accepted the walk after one major correction: per-source safety segments were blocking shared playable borders outside the central socket mouth. The isolated adapter now filters cloned Boundary metadata against the final rotated playable footprint before ChunkLoader builds it. All128 interior segments are omitted; all160 exposed outer segments remain. No terrain/collision mesh or frozen source data changes. The live session was corrected directly, and the same rule is persisted for future launches. Owner explicitly waived a repeat walkthrough; only cheap build/format/count checks were run. Props without collision and slight character floating are accepted for this test and deferred. Do not begin Batch2.

## Scenery continuity candidate — 2026-10-06

Separate saved place: E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling/BurnedPlainsSceneryScaling.rbxl. This branch overlay adds SceneryData.luau and replaces only old scenery role assets with mapped baked clumps/continuation/trees. Original walkthrough place and data stay intact. Review/profile/evidence/limitations: SCENERY_SCALING_REVIEW.md. AllocationProbe.client.luau is opt-in diagnostics, excluded from the overlay. Keep it disabled during visual/load tests. No new EditableMesh setting required for rendering. Current continuity candidate has fresh Play validation, not owner acceptance or production rollout.
