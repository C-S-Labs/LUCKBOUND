# Emberfall representative full-map scale review — 2026-10-06

## Decision
PASS for continuing production at the measured scenery/geometry cost envelope on this PC. No production content was authored or installed. This is not mobile, cold-cache, arbitrary-seed appearance or complete gameplay certification. Follow-up profiling belongs at production packaging/device validation; no speculative loader redesign is justified by these results.

## Scale and composition
9 real chunks versus36 equivalents: four isolated copies of accepted Layout1, with20 additional visual meshes and20 collision meshes per later-half chunk. Two8500-triangle prop assemblies and18 237-triangle assemblies add21,266tris per affected chunk (~83% of average source playable triangles). Actual accepted meshes provide geometry/object cost proxies, not settlement/castle designs. All627 source colliders retain mapped fidelity; frozen sources, HOLLOW/CREST and authored collision were not changed.

Route2140.458studs/9 chunks, current walk16.8studs/s:36 equivalents imply8.49min walking and11.51min other activity under the requested20min target.27–54 remains a plausible duration uncertainty range. No final map count or production timer decision was made. Repeated packages are disconnected to preserve accepted internal joins and give a bounded cost fixture; no full-map route or Batch2 was authored.

Scenery coverage repeats the accepted61-part ring, with baked three-blade clumps, distance thinning, terrain/underlap, trees and all baked burn states. All content is NON-PRODUCTION and excluded from default.project.json/AssetManifest/generator content.

## Load definition and sessions
Zero is benchmark server-script start; excludes Studio Play launcher time. Server-ready = entire fixture instantiated, including collision/scenery. Client asset-ready = full expected MeshPart count received, PreloadAsync completed, two frames rendered. This is a useful readiness proxy, not pixel/GPU residency certification. Player-ready = authored entry raycast succeeds and character is teleported after1s settle; actual onboarding/avatar/controller readiness can add time. Effective ready = maximum of player and client asset readiness. No progressive readiness/deferred scenery was implemented.

Fresh sessions mean stop/start Play, not restarting Studio or clearing asset caches. Cache warmth and avatar timing varied. First serial server-only observation40.81s is retained in the session evidence; its client profiler initially failed on an unavailable streaming property. Corrected serial repeat below provides valid client data. Intermediate18 over-stress had an excessively heavy153,474-tri uplift/chunk: kept as extra stress evidence, excluded from calibrated linear comparisons.

| Configuration | Server-ready | Player-ready | Client all-assets-ready | Client preload |
| --- | ---: | ---: | ---: | ---: |
|9 accepted serial adapter repeat|32.53s|52.98s|33.18s|0.450s|
|9 parallel run1|18.02s|19.04s|18.37s|0.266s|
|9 parallel run2, large viewport|19.02s|20.03s|19.60s|0.545s|
|18 over-stress|19.05s|36.84s|19.59s|0.444s|
|36 calibrated + second bank run1|19.63s|20.64s|20.29s|0.477s|
|36 repeat, large viewport|22.45s|25.19s|23.56s|0.897s|

Slow serial/intermediate player readiness contains extra character availability delay beyond server loading; do not attribute it to scenery.

## Stage breakdown
| Stage |9 parallel runs|36 calibrated runs|
| --- | ---: | ---: |
|627 unique collision acquisitions,6 workers|15.22–16.58s|15.26–17.79s|
|39 playable visual preparations,6 workers|0.97–1.63s|1.10–1.72s|
|61 accepted scenery preparations,6 workers|1.12–1.42s|1.25–1.31s|
|First scenery cloning/placement|0.00118s|0.00118–0.00127s|
|First9 ChunkLoader build|0.0110s|0.0107–0.0116s|
|Additional27 chunks/dressing/structural proxies|none|0.0533–0.0547s|
|Second scenery-ID bank preparation|none|1.30–2.15s|

Appearance copying/recolour/EditableMesh allocations:zero. Client environment setup uses accepted lighting. All acquisition stages call real AssetPreparation; chunk assembly calls real ChunkLoader with exact templates. Preparation stats show six active workers, zero duplicate preparations and zero visual precise-collision requests. Serialization/replication/client preload remain distinct from server instantiation.

## Counts and scaling
| Metric |9 real|36 calibrated|
| --- | ---: | ---: |
|Visual triangles|488,940|2,338,548|
|Visual MeshParts|100|760|
|All MeshParts|727|3,628|
|Collision MeshParts|627|2,868|
|Safety segments|160|640|
|All BaseParts|905|4,340|
|Descendant instances|933|4,457|
|Scenery MeshParts|61|244|
|Scenery grass triangles|175,263|701,052|
|Scenery clumps|58,421|233,684|
|Unique rendered/collision MeshIds received|727|786|

Triangle count grows4.78×, MeshParts4.99×; prepared library remains mostly shared, so server loading does not grow4×. Nine mean server18.52s versus36 mean21.04s (+13.6%); two-run ranges are more useful than a precise mean. No superlinear instance/assembly cliff was observed. Collision counts include360 additional authored-shape proxies;200,064 reported authored collision triangles excludes added proxy triangles. Physical active NPC/hero-prop collisions are not fabricated.

## What8.22seconds meant
The previous timer wrapped61 sequential cache-miss clone calls, each lazily invoking CreateMeshPartAsync, plus placement. It did not isolate grass processing, recolouring, Blender import or a platform-required scenery delay. Reproduction7.24s (another observation9.57s); MaximumActiveWorkers=1 despite configured6. Existing prepareMany makes the same scenery1.16–1.46s including preparation; placement ~1ms. Change is confined to this opt-in benchmark; original accepted adapter and original measurements are preserved. Production ExpeditionSystem already calls ChunkLoader.prepare/prepareMany.

## Runtime and memory
PC: Intel i9-14900K, RTX4080,32GB RAM, driver32.0.15.9159; Studio Level21. Small runs use713x500 viewport, matching large9/36 runs use1993x978. Foreground9 and36 views average~60FPS. Large36 p95 frame17.72–18.13ms, max20.80ms across player-eye/elevated/overview/later-half views; no frames over33ms. Early serial diagnostic15FPS was background throttling, not a map bottleneck; it is not included in runtime pass evidence.

Privileged Studio overview samples for large36:~1,427,568 opaque rendered tris/265 draws, CPU counter16.0–17.4ms, GPU counter0.71–0.98ms. These are bounded live counters, not a MicroProfiler trace or isolated script CPU measurement; frame cap/waits affect CPU interpretation. Camera jumps are bounded view probes, not gameplay traversal/pathfinding validation. No low-end guarantee follows from an RTX4080 run.

Stats startup-to-final deltas: GraphicsMeshParts ~61.3MB for9,~61.5MB for36; PhysicsParts ~5.6MB for9 versus19.2MB for36; Instances ~40MB both. Studio process total~4GB includes editor/server/client/plugins/base game, not map-only memory. Repeated geometry and byte-identical second-bank geometry may be deduplicated:786 IDs do not prove786 physically unique allocations. Roblox cautions that Studio memory exceeds published-client memory because both server and client run: https://create.roblox.com/docs/performance-optimization/design . No reliable absolute low-end memory budget was established.

StreamingEnabled=true, but TestMode/Persistent holds the entire fixture on the client. All627 unique collision assets, playable visuals, distant chunks and scenery load before server readiness. Ordinary production ChunkLoader can consume already packaged collision templates; current diagnostic adapter instead reacquires627 shapes every Play. Parked EF_BATCH1_COLLISION has627 matching IDs but Default fidelity rather than required authored fidelities, so it was deliberately NOT substituted as a faster collision solution. Packaging the exact reviewed templates is a clear integration follow-up, not proof that production inherently needs15–18s for collision.

## Bottlenecks and remaining uncertainty
1. Collision acquisition:15–18s, approximately78–87% of parallel load. Bound to unique API requests in this diagnostic delivery path, not cloning thousands of instances. No evidence of a universal MeshPart ceiling.
2. Sequential visual preparation in accepted adapter:~16s combined visual/scenery repeat, reduced to~2.5–3s with existing worker path. No broad optimization rewrite.
3. Character readiness:extra~0–20s observed independently of fixture instantiation. Published onboarding/profile/teleport timing still needs a real entry test.
4. Unique library/network/device memory: only59 added unique IDs and identical source bytes tested. Each additional627-asset collision library could add~15–18s if acquired similarly; this linear estimate is not measured and packaged-template delivery differs. Final distinct-area libraries/particles/AI/multiplayer require later profiling.

Scenery strategy remains viable in this cost fixture:244 meshes/701,052 grass triangles, zero editable allocation, no preload failure in final runs. Arbitrary-route coherent baked state selection is still the separately documented production appearance gate.

## Assets, evidence and repository
New Models97791787380183 and111177488181002; raw mappings and SHA256-identical NON_PRODUCTION FBX copies under E:/BlenderAIProjects/Runtime/Emberfall_ScaleTest. Automated approved uploader used once per file, no existing Roblox assets replaced. Two tree IDs125951556096146/94233156691610 failed initial acquisition and a bounded probe; cause unresolved (not identified as a resource ceiling). Effective mapping quarantines them and uses identical accepted tree assets;59 new IDs remain. Final36 runs preload3628/3628 successfully with786 unique IDs.

Raw9_serial.json,9_parallel_1/2.json,18_overstress.json,36_parallel_unique_1/2.json,36_counters_1/2.json,unique_first_run_failure.json and full_fixture_overview_maximized.png live in that external folder. BenchmarkBase.rbxl is a COPY of the accepted place; apply BenchmarkOverlay.rbxlx/Rojo overlay to run. It is not a saved canonical full-map place. Run/export/mapping instructions: tools/studio/emberfall_scale_test/README.md. Small measured summary is committed with fixture. No source Blender authoring or production content additions.

Scoped StyLua/Selene, generated mapping consistency, Rojo build, index generation/check and protected-path diff checks apply. No gameplay regression suite repeated because src/tests/frozen assets were unchanged. No push/merge/PR/main modification. Owner checkout remains on its original branch with pre-existing mixed work; accepted worktrees remain clean.

## Cleanup and next step
Keep all accepted proofs/imports/recovery assets. Keep the two unavailable uploaded IDs/raw mappings and18 over-stress evidence until asset-delivery investigation and owner review establish safe retirement; they are isolated from production. Benchmark scripts/assets replace no production files. Retire only task-owned fixtures after later production/package/device profiling and applicable CI/Studio confirmation. Do not delete assets referenced by older accepted mappings.

Continue production within the measured envelope. Profile again after exact collision-template packaging, genuinely distinct later-area assets, published entry and representative target-device gameplay. Do not redesign loading or begin extra content during this task.

FULL-MAP SCALE TEST PASS — performance is sufficient to continue Emberfall production.
