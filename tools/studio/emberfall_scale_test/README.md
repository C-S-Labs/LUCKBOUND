# Emberfall representative scale benchmark — NON-PRODUCTION

Starts from accepted scenery checkpoint 3e15bc4 (descends from 73b918b). Reuses frozen sources and real AssetPreparation/ChunkLoader. This is a cost fixture; replicas are disconnected accepted-layout packages, not canonical area designs or a generated route.

## Run
Open a copy of E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling/BurnedPlainsSceneryScaling.rbxl. Sync emberfall-scale-test.project.json (port34874) over the complete game. Overlay alone is not a standalone game. Original walkthrough scripts are disabled by overlay, preserved rather than deleted.
In Edit set Workspace attributes:
- EmberfallBenchmarkGroups:1 baseline,2 intermediate,4 full (9 chunks/package).
- EmberfallBenchmarkParallel:true uses existing prepareMany;false reproduces serial accepted adapter acquisition.
- EmberfallBenchmarkUniqueBank:true adds the second scenery bank;false uses accepted bank only.

Stop/start Play for each run. Keep Studio foreground during camera samples. ServerReport is on Workspace.ExpeditionStage.EmberfallScaleBenchmark. Client report is local Workspace.EmberfallBenchmarkClientReport. No new RemoteEvents or published content registration; both scripts refuse to run outside Studio.

## Scope and scale
Accepted route2140.458studs /9 chunks. Current expedition walk16.8studs/s gives127.4s walking/package.36 equivalents give8.49min walking plus11.51min encounters/exploration/stops under the requested20min target. Plausible uncertainty27–54 chunks. Production timer remains unchanged.

Later half receives20 extra ordinary visual MeshParts and20 authored collision clones per chunk. Two visual batches have8500triangles each;18 have237 each:21,266 additional triangles/chunk, about83% of average source playable triangles. These are compressed accepted prop assemblies used solely as structural/object/physics cost proxies, not buildings. No empty-cube visual proxy. Additional18 chunks add360 visual/360 collision MeshParts and382,788triangles. An earlier18-chunk over-stress fixture accidentally used153,474 added tris/chunk; retained separately and excluded from calibrated scaling comparisons.

Four scenery rings deliberately repeat61 meshes/257,807tris each;701,052 grass triangles/233,684 clumps total. This is pessimistic ring coverage compared with a contiguous route. Frozen geometry/collision and scenery boundary adaptation remain intact inside each package.

## Readiness
Zero is benchmark server script start, after Studio has launched Play; Studio launcher time is excluded. ServerReady means all tested models, scenery and collision are instantiated. ExpectedMeshParts gates client replication completeness. PreloadAsync plus two rendered frames is a full-asset readiness proxy, not proof of every pixel or GPU residency. PlayerReadyAt means the character has an authored entry ray hit and has been teleported after the accepted1second settle delay; first-join/avatar/UI/controller completion is not certified by this timestamp. Effective readiness is max(player-ready, client full-asset-ready).

All tested content eagerly blocks readiness. Persistent models override distance streaming in this fixture even though StreamingEnabled is true. No streaming optimization is implemented.

## Asset bank
New non-production Models97791787380183 (55 continuation/grass meshes) and111177488181002 (6 trees). FBX copies are byte-identical to accepted exports; all geometry/baked colors inherited unchanged. Two newly uploaded tree IDs125951556096146 and94233156691610 failed AssetService acquisition, including a bounded second probe. Effective mapping preserves those uploads as quarantined provenance and substitutes the identical accepted tree IDs.59 new IDs are exercised. Asset permission/moderation/delivery root cause is undetermined; no blind upload retry or overwriting of existing assets.

Raw uploads, FBX copies, validation and run JSON live in E:/BlenderAIProjects/Runtime/Emberfall_ScaleTest. unique_asset_mapping.json records effective runtime mapping. Raw mappings retain all61 uploaded IDs.

## Measurement limits
Fresh Play creates a new runtime, not a cold Studio/asset cache. Repeated packages share playable assets; second bank tests some extra unique acquisition, not the finished unique library. Equal source bytes under different IDs may be deduplicated internally; no distinct physical storage claim. Stats memory includes Studio/editor/server/client/plugin/base-game overhead and is not a published-client map-only budget. RenderStepped measures frame cadence and caps, not CPU/GPU work. Privileged Studio counters are collected separately because LocalScript StatsItem access is restricted. No enemies, combat AI, pathfinding, loot or future particle systems are fabricated. No low-end/mobile guarantee.
