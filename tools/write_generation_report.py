"""Render the consolidated local experiment report from preserved measurements."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/benchmarks'


def main():
    results=json.loads((DATA/'generation_consolidated_summary.json').read_text())
    def number(value): return f'{value:.3f}'
    def pct(before,after): return f'{100*(1-after/before):.2f}%'
    report=['''# Generation and asset performance experiments — consolidated results

Completed locally on `agent/procgen-performance`, based on main `714fa33`.
No push, merge, production switch, place save or publication. Original assets and
production-policy loading remain available. All earlier raw results are retained.

Runtime asset materialization dominates. Layout/socket/overlap computation is
already cheap and deterministic. The best measured configuration combines safe
visual template cloning, fidelity-aware fallback, single-flight caching, seed
working-set preparation, six bounded workers, and deferred/cached anchors.
The automatic Sky Citadel collision-proxy sample is **rejected**.

## Method and timing boundaries

A has 90 original Studio maps. The paired A–F table uses the existing 30-map
subset: seeds 1, 997, 65537, 999983, 1704274940; three worlds; two repeats.
Each G–K/M/combined/live policy uses the same 30-map cohort. L has 48 builds:
two SC chunks × four rotations × three repeats × control/proxy. Total: 660
completed full-map measurements, plus 48 collision sample builds and one
additional ES replication diagnostic. Duplicate paired files/partial A files
are preserved but not counted twice. The 18,000 headless layout comparisons are
correctness evidence, not Studio latency measurements. A–F were not restarted.

Caches start cold per policy and remain alive across seeds/repeats. These mixed
cohort medians include cache reuse. **Reserved expedition servers normally build
one world/map: cold first-map results are the relevant production comparison.**
Studio/Roblox's underlying downloaded-asset caches were not purged; these are
cold prototype caches, not fresh-device/network-download benchmarks. Policies
ran sequentially, not randomized, so small differences are not causal evidence.

Map-ready includes layout, chunks, collision, required solid props, return portal,
transit and loot preparation. Complete additionally waits for server anchors.
It does not mean every optional client visual has appeared. Live tests use a real
Studio player, the production rig-placement helper and two grounded frames;
they restore the character after each scratch map. They do not replay private
server teleport, party entry or the complete expedition UI/remotes flow.

CollisionReady is the end of synchronous materialization, corroborated by engine
queries and player grounding. The public mesh API exposes no independent cooking
completion signal here; cumulative CreateMeshPartAsync wall time includes that
work. Post-build heartbeat observation is not a collision-cooking measurement.

## A–F and asset experiment matrix

Seconds. Raycasts are cohort totals from generation instrumentation, excluding
the additional verification queries. Memory is observed total server-memory
delta per map; negative values/large ranges expose GC and shared-engine noise.
It is not an attributed cache allocation measurement. Zero geometry/signature
differences below apply to asset-policy comparisons; A–F use layout/loader checks.

| Stage | Map-ready median / worst | Complete median / worst | Placement / atmosphere rays | Memory delta median / maximum MB | Mesh API / Precise calls |
|---|---:|---:|---:|---:|---:|''']
    names=['A','B','C','D','E','F','ASSET_CONTROL','G','H','I','J','K_SEED','K_WORLD','GHIK','M2','M4','M6','FINAL']
    for name in names:
        r=results[name]; c=r['Counters']; mem=r['MemoryDeltaMb']
        report.append(f"| {name} | {number(r['Playable']['Median'])} / {number(r['Playable']['Worst'])} | {number(r['Complete']['Median'])} / {number(r['Complete']['Worst'])} | {c.get('PlacementRaycasts',0):,} / {c.get('AtmosphereRaycasts',0):,} | {number(mem['Median'])} / {number(mem['Worst'])} | {c.get('CreateMeshPartAsyncCalls','not instrumented')} / {c.get('PreciseRequests','not instrumented')} |")
    a90=json.loads((DATA/'generation_studio_A.json').read_text())
    report.append(f"\nOriginal A (all 90): median **{number(statistics.median(r['PlayableSeconds'] for r in a90))} s**, worst **{number(max(r['PlayableSeconds'] for r in a90))} s**. Paired A is **20.264 / 47.941 s**.\n")
    before=results['A']['Playable']; after=results['FINAL']['Playable']
    report.append(f"Final server map-ready is **{number(after['Median'])} / {number(after['Worst'])} s**, reductions of **{pct(before['Median'],after['Median'])} median / {pct(before['Worst'],after['Worst'])} worst** against paired A. This is a cache-reusing map-ready comparison, not the complete player-entry metric.\n")
    report.append('''
Stages are isolated: G only local templates; H only visual fidelity; I only cache;
J only world metadata views. K_SEED/K_WORLD add preparation to I. GHIK adds G/H/I
with seed preparation, worker 1. M2/4/6 change only that worker limit. FINAL adds
stage F prop/definition/anchor behavior to the measured M6 configuration.

B replaces imported-art orientation probing with authored yaw hints; it does not
invent direct socket placement. C caches the existing occupancy predicate, not a
new overlap representation. Neither reduced measured map latency. B eliminated
1,352 calibration raycasts in the paired A cohort; socket placement eliminated
**zero new layout raycasts**, because production already uses direct sockets.
Occupancy eliminated **zero raycasts** for the same reason. Asset control has
2,022 calibration rays; its independent cohort had fresh yaw caches.

E moves all 536,576 anchor rays off entry but spreads processing over heartbeats:
complete median 24.790 s, about 3 s later than ready. F performs 97,280 rays on
cache misses and mathematically transforms cached local samples on reuse:
**439,296 eliminated**, remaining 97,280 deferred. Baseline atmosphere CPU median
0.068 s (range 0.038–0.090 s), versus asset initialization median 20.189 s.
Cacheable samples exclude dynamic encounter gates and invalidate by world,
chunk, atmosphere, asset/yaw, floor/blockout/proxy configuration.

## Cold first map by world

Each cell is the first map for that world in a fresh policy context. These are
three observations per policy, not a statistically robust independent cold-run
distribution; repeated warm maps must not be presented as repeated cold samples.

| Policy | Verdant Valley | Sky Citadel | Ethereal Scape |
|---|---:|---:|---:|''')
    for name in ['ASSET_CONTROL','G','H','I','K_SEED','K_WORLD','GHIK','M2','M4','M6','FINAL','LIVE_CONTROL','LIVE_FINAL']:
        cold=results[name]['ColdFirstMapByWorld']
        report.append('| '+name+' | '+' | '.join(number(cold[w]) for w in ['VERDANT_VALLEY','SKY_CITADEL','ETHEREAL_SCAPE'])+' |')
    report.append('''
Do not prepare the whole world on the entry path: K_WORLD loads 293 assets rather
than the seed cohort's 219, including 74 not used. Its first ES map takes 88.063 s.
Lazy I and serial K_SEED are similar; seed preparation is useful mainly because
it enables bounded parallelism. Worker 6 wins measured cold/worst latency over
1/2/4; all have 119 runtime creations, zero real API errors/throttling reports.
Peak memory observations are noisy and do not establish a monotonic worker-cost
relationship. Six is a Studio result, not a universal platform guarantee.

## Player entry and client observation

| Live cohort | Server safe-play median / worst | Server complete median / worst | Grounding failures |
|---|---:|---:|---:|''')
    for name in ['LIVE_CONTROL','LIVE_FINAL']:
        r=results[name]; rows=json.loads((DATA/f'asset_{name}.json').read_text())
        report.append(f"| {name} | {number(r['Playable']['Median'])} / {number(r['Playable']['Worst'])} | {number(r['Complete']['Median'])} / {number(r['Complete']['Worst'])} | {sum(not row['PlayerGrounded'] for row in rows)} / 30 |")
    b=results['LIVE_CONTROL']['Playable']; f=results['LIVE_FINAL']['Playable']
    report.append(f"\nServer safe-play reduction: **{pct(b['Median'],f['Median'])} median / {pct(b['Worst'],f['Worst'])} worst**. Original A did not place a player, so compare live control to live final for this metric.\n")
    for name in ['LIVE_CONTROL','LIVE_FINAL']:
        r=results[name]; client=r['ClientAndGroundedReady']
        report.append(f"{name}: **{r['ClientValidatedSamples']}/30** entry-folder visual/preload observations valid; median/worst of simultaneous client-and-grounded readiness for those **20 VV/SC maps**: **{number(client['Median'])}/{number(client['Worst'])} s**.\n")
    report.append('''
The 10 ES observer failures occur in both policies. All expected spawn collision
parts replicate and the player grounds; only 3 of 37 entry MeshParts are streamed
at spawn. The additional diagnostic confirms 34 non-colliding authored parts
are far away: foliage around (-1791,20002,1796), portal decoration around
(3150,20008,-1580), while the character stands at the entry. They are outside
the spawn working set, not new missing optimized meshes. The observer incorrectly
required every descendant of that folder, including remote decorations. Its
post-destruction timeout timestamps are **excluded from valid ready metrics**.
Review these existing content offsets in the production scene before certifying
ES entry appearance. No unrelated content transform repair was made here.

Live final cold safe-play: VV 0.433 s, SC 6.215 s, ES 5.750 s. Warm SC/ES entry
still spends roughly 1.3 s waiting for physical landing, which the millisecond
layout/map-ready timing alone would hide. Client preload is sampled in Studio
with already used assets, not a fresh published client/network measurement.

## Asset attribution, cache and collision fidelity

Across the same 30-map asset cohort: 524 runtime chunks, 1,452 mesh placements,
1,214 multipart components and 114 existing collision-proxy clones.

- Control: 1,452 CreateMeshPartAsync calls, 219 unique keys, **1,233 duplicate
  expensive preparations**; all 1,452 request Precise, including 672 visual-only.
- G: 672 authored visual clones, 780 runtime precise calls. VV first map falls
  from 25.036 s to 0.147 s. Template indexing costs at most 0.00583 s; resolution
  median 0.000031 s and total clone time per map median 0.000417 s. Control asset
  API median 21.611 s. Authoritative SC geometry retains exact precise fallback.
- H: still 1,452 API calls, but only 780 Precise; 672 explicit visual-only meshes
  use Box. VV first map is 3.356 s. ES multipart non-colliding components are
  included. Collision remains precise for authoritative components without proxies.
- I: 219 creations, no duplicate preparations; 1,233 placement cache hits (84.92%).
  Nine scheduler/API invariants cover in-flight deduplication, error wake/retry,
  and distinct precise/visual fidelity entries. One overlapping test request is
  deduplicated; the sequential layout does not naturally exercise this race.
- Final: **119 API calls / 119 Precise / zero visual-only Precise**, no duplicate
  runtime preparations; 100 unique authored template references plus 119 runtime
  MeshParts make 219 cached entries. 672 local visual placements remain clones.
  **91.80% fewer API/Precise calls** than control. Remaining calls all retain
  authoritative collision fidelity. Cache is per server/context, not persistent
  across places or Studio sessions. Authored ServerStorage assets persist through
  the place/project, not through a Lua cache.

Parallel cumulative API wall time sums overlapping loads; do not confuse it with
elapsed preparation duration. Per-call maximum/individual loads, hits/misses and
observed memory are preserved in raw rows, along with working-set cardinality.

## Server boot, registries and props

AssetManifest already uses direct `ENTRIES[key]` hash/table lookup. J adds cached
world views and easy role-inclusive enumeration, not faster lookup or a fully
lazy manifest migration. Spawn, boss approach, boss and attached-room keys stay
in the registry even when excluded from ordinary random candidates.

Five fresh Play starts per mode measured script bootstrap/content-ready separately:

| Mode | Content-ready median / worst | Bootstrap-ready median / worst |
|---|---:|---:|''')
    for mode,r in results['SERVER_BOOT'].items():
        report.append(f"| {mode} | {number(r['ContentReady']['Median'])} / {number(r['ContentReady']['Worst'])} | {number(r['Ready']['Median'])} / {number(r['Ready']['Worst'])} |")
    report.append('''
J provides no material boot or entry improvement (bootstrap median +0.0009 s).
These timers start at script execution, not place deserialization or platform
server allocation, and do not wait for asynchronous user profiles. The separate
10 module/content microbenchmarks are retained, not substituted for these starts.
Original Studio bootstrap Source was restored exactly; no place save/publish.

D's first VV prop require is about 0.0138 s instead of A's eager-root cold require
0.0377 s, but production schema boot already requires every Props child. **No
proven expedition-entry saving** can be attributed to avoiding that already-paid
cost. D loads only requested world modules in its isolated context (three across
the whole three-world cohort), caches results, and preserves deterministic content.
There is no Shared folder in current content; the API supports it if authored.
Solid props already use chunk-local data and remain blocking. Their initialization
median is ~0.00005 s; no global spatial-discovery rewrite is warranted.

## Memory and static definitions

Final retains 119 unparented runtime MeshPart templates plus 100 references to
existing authored templates, not full invisible maps. Definitions cache authored
socket/bounds data; occupied bounds rotate mathematically. This does not loosen
the conservative production overlap predicate or introduce a grid.

F anchor cache: 95 definitions / 39,804 samples; float64 position/normal payload
**1,910,592 bytes (1.82 MiB)**. This is a serialized payload estimate, not real Lua
table allocation. Final total-memory per-map median delta 0.094 MB, maximum
3.910 MB; minimum -31.516 MB. Cache destruction after one heartbeat showed no
measurable total-memory release and a noisy Instances-tag change. Native mesh
data is engine-shared/cached and GC delayed: **exact cache memory cost remains
unresolved**, not zero. The full-world policy retains more assets. A dedicated
fresh-server memory profiler and idle/GC observation are required before sizing
production limits. Avoid an unbounded cache across unrelated expeditions.

## Collision proxy sample L and authoring recommendation

Blender generated simple boxes/floor prisms for SC Hoops (115 shapes) and Shattered
(82 shapes), with no whole-biome rebuild or production asset replacement. Across
48 sample builds, current materialization median/worst 0.544/0.562 s; proposed
0.007/0.009 s. **15,474 differing ray/body-cast samples: reject these proxies.**
Bounding boxes around decorative/arched geometry do not preserve gaps and walk
surfaces. They cannot safely replace PreciseConvexDecomposition. No player walk
approval is claimed for the failed sample, and L is excluded from final selection.

Recommend visual-only + designer-reviewed collision proxies as a future chunk
authoring contract for SC/ES and future Emberfall/Astral Reach/worlds. Proxies must
explicitly preserve floors, walls, barriers, cliffs, stairs/ramps, fall-through
holes, socket seams and boss boundaries. Author gameplay surfaces directly in
Blender; do not infer safety from decorative object bounds. VV's existing verified
nonempty CollisionTemplate contract remains the current example. Each role,
including Spawn/BossApproach/Boss, needs the same asset/metadata contract.
Do not make new proxy schemas mandatory until a representative manually reviewed
sample passes dense geometry queries and player traversals.

## Correctness and visual limits

- 1,047/1,047 Luau tests, 4,280 legacy loader comparisons and 18,000 headless
  staged layout comparisons pass. No new overlap/role/socket/determinism failures.
  Rejected candidate placements are normal retry counters, not correctness failures.
- Real Studio anchor, prop registry, asset/single-flight and client late-update
  invariants: nine each pass. Late anchors preserve existing actor instances and
  motion, initialize lights once and reject stale/duplicate delivery. A pending
  empty-path client graph bug was found and fixed before final validation.
- All G–K/M/final live cohorts: zero sampled collision differences above 0.05 stud,
  zero mesh-property signature mismatches, zero recorded art-yaw mismatches,
  zero blockout fallbacks/structural failures. Maximum tiny query float variance
  is approximately 0.004 stud. Queries include 9×9 per-chunk casts and socket
  samples; they are not exhaustive stair/wall/gap player traversal tests.
- 85 used authored yaw definitions compare to measured controls, zero mismatches
  or missing hints. Unused kit definitions are not thereby certified.
- ServerStorage's 4,780 MeshParts include 293 matching visuals; imported templates
  all report Default fidelity. They are **not** accepted for authoritative SC
  collision. Only safe visual-only components clone those templates.
- Full live grounding passes; VV/SC client spawn geometry/preload passes. ES
  folder-wide visual validation is limited as described above. Mesh signatures
  omit a full rendered-image comparison, and no complete manual visual walkthrough
  or fresh-device network/quality-level check was performed.
- Deferred anchors can appear later: E spreads processing over seconds; F cold
  completion can trail entry by roughly two seconds. Existing weather actors do
  not reset on late delivery, but aesthetic pop-in acceptance remains an owner
  Studio review item. Do not claim zero visible atmosphere regressions.

## Adoption decisions and production migration order

1. Keep instrumentation and the existing socket/occupancy solver. Preserve the
   synchronous production route and add a reversible asset-policy switch.
2. Adopt I single-flight caching for identical AssetKey/fidelity preparations;
   impose world/server lifetime limits and preserve precise authoritative collision.
3. Adopt G for verified visual-only authored templates (VV first), then H for
   explicit non-colliding ES components. Require proxy validation and measured
   authored yaw calibration; never make Default SC imports collision-authoritative.
4. Adopt K seed working sets including all roles/rooms, then trial measured M6
   behind a limit with errors/backoff. Rebenchmark fresh published servers and
   clients; 2/4 workers remain fallbacks if real service limits differ.
5. Trial F's cached/local metadata and cancellable deferred atmosphere with token
   validation; retain dynamic fallbacks. Review visual arrival/pop-in and preserve
   client actors. This saves ~0.07 s once assets are fast; it was not the original
   bottleneck. C/static definitions are reasonable small caches, not major wins.
6. J/world registries and D/props are architecture improvements only without a
   boot-schema/lazy-content design migration. Do not claim current entry savings.
7. Author/review one true SC collision sample, then ES stairs/gaps sample, before
   migrating remaining chunks or adopting a mandatory proxy standard.

Reject blocking K_WORLD preparation and the L automatic collision conversion.
Revise B's blanket art-probe bypass until every relevant asset yaw is certified;
direct socket placement itself is already production. E alone creates unnecessary
late scan latency when F metadata/cache is available. Do not optimize query count
in isolation. Remaining cold bottleneck is precise authoritative SC/ES mesh
preparation; after cache/template reuse, physical landing/client delivery dominate.

## Files, reproduction and preserved comparison

Implementation: `Util/AssetPreparation`, `AssetRegistry`, `AssetGeometryCheck`,
`CollisionProxySample`, `GenerationBenchmark`, `GenerationProfile`,
`GenerationAnchors`, `ChunkDefinitionCache`, `PropRegistry`; opt-in hooks in
ChunkCore/ChunkLoader/ExpeditionSystem and late-anchor client handling. Content
`CollisionSamples` is an isolated test fixture, not a replacement kit.

Raw evidence: [consolidated JSON](benchmarks/generation_consolidated_summary.json),
`benchmarks/generation_studio_*`, `generation_paired_*`, `asset_*`, invariants,
template/yaw inventories and headless CSV. Preserve every raw/partial file.
`python tools/summarize_generation_results.py` then
`python tools/write_generation_report.py` regenerates this report without tests.
The generation/asset/collision/final runners preserve completed outputs on resume;
**do not restart A–F**. `measure_server_boot.py` preserves saved boot results.
`check_entry_replication.py` is a separate scratch diagnostic, not a new matrix.

Studio is left in Edit; experimental runtime roots/maps disappear with Stop.
Owned Edit instrumentation roots are removed at cleanup. Production-main source
bundle for analysis is retained at ignored `.tools/production-generation-main-714fa33.zip`.
No owner files, collision rollbacks or parked recolours are removed. Obsolete
one-time patch-generation helpers are removed after checks; supported runners and
all benchmark evidence remain. Production cleanup awaits CI, published cold-load
checks and owner traversal/visual acceptance. No production iterations were replaced.
''')
    (ROOT/'docs/GENERATION_PERFORMANCE.md').write_text('\n'.join(report),encoding='utf-8')


if __name__=='__main__': main()
