# Procedural generation: first production migration

Implemented on `agent/procgen-production`, based on production `714fa33`.
The completion commit is reported in the handoff and available through `git log`.
Ready for owner traversal, **pending manual acceptance and published-server validation**.
No push, merge, publish or Studio save. Original Edit sources were restored and verified.

## Evidence and scope

The immutable experiment is `bb47f91` on `agent/procgen-performance`:
`docs/GENERATION_PERFORMANCE.md` and
`docs/benchmarks/generation_consolidated_summary.json`. Its worktree and every
A–M result remain unchanged. Those experiments were not restarted.

Historical live control: grounded-player median **22.248 s**, worst **46.600 s**.
Historical final prototype: **1.333 / 6.215 s**; completion **1.349 / 6.633 s**.
Across that original cohort, creation/Precise calls fell **1,452 → 119** (91.80%),
visual-only Precise **672 → 0**, and duplicate preparation **1,233 → 0**.
These are historical benchmark results, not new production measurements.

This migration adopts I, G/H, K/M6 and F. Manifest lookup remains direct table
lookup; J supplied no measured performance benefit and was not adopted. Direct socket placement, Normal/Wide
compatibility, overlap checks, chunk selection, scenario selection and authored
content remain unchanged. No world registry, Props migration, full-biome preload,
automatic collision conversion, Blender edit, enemy director, NPC population or
enemy asset preparation was added.

## Runtime architecture

`ExpeditionSystem.init` owns one `AssetPreparation` instance. Its canonical
MeshParts live under **ServerStorage.PreparedChunkAssets**, never Workspace or
ReplicatedStorage. A group owns its placed clones; destroying a group does not
invalidate other groups' templates. Server shutdown destroys the captured owner;
reinitialization destroys its predecessor and clears the presentation cache.
Successful templates persist for server lifetime. The cache grows with actually
used content, including role variants; it does not retain invisible assembled maps.

The owner API is `prepare`, `prepareMany`, `get`, `clone`, `proxy`, `hasProxy`,
`stats`, and `destroy`. `ChunkAssetCore` collects requests; `ChunkLoader.prepare`
prepares their templates; `ChunkLoader.build` places clones, authored collision,
props and existing gameplay structures. Expected preparation/clone failures use
Results. ChunkLoader retains whole-chunk blockout and authoritative collision
fallbacks; multipart failures destroy the partial assembly.

### Single-flight and resolution

The cache identity is **AssetKey + collision role + manifest asset ID**.
This prevents a cheap visual template being reused as authoritative collision.
One asset used in both roles can therefore have two canonical templates.

The first caller installs a flight record before yielding. Other callers await
its BindableEvent and receive the same Result. Successful canonical templates
are cached; failed flights wake their waiters and are removed so a later request
can retry. Creator exceptions release their worker slot. Queue exceptions finish
their workers and return failure instead of hanging the waiting caller.

Resolution order is cached canonical → safe authored MeshPart → AssetService.
At owner construction, ServerStorage chunk-kit descendants are indexed once by
numeric MeshId. Only archivable parts qualify. Conflicting texture/color/material
configurations for an ID are treated as ambiguous and use the fallback.
Current multipart content resolves each component MeshPart; it does not clone an
unverified entire imported Model. Imported local templates are accepted only for
visual-only geometry. Default-fidelity SC/ES templates never supply authoritative
collision. Failed local cloning falls back to AssetService.

### Collision roles and orientation

| Contract | Preparation | Placement semantics |
|---|---|---|
| Visual-only | authored clone, otherwise Box fallback | final flags preserve existing content behavior |
| Authored collision proxy | existing nonempty, archivable CollisionTemplate cloned separately | invisible, anchored, collidable/queryable, non-touchable; terrain visual has all three physics flags false |
| Authoritative mesh collision | AssetService PreciseConvexDecomposition, then canonical clones | collidable/queryable/touchable unless existing component data says otherwise |

An explicit multipart `CanCollide=false` component is visual-only and remains
non-queryable/non-touchable. Other multipart terrain remains precise. Existing
single-mesh collision templates are verified before classifying their visuals.
Missing/empty/uncloneable proxies retain authoritative collision. If attachment
fails after validation, the visual is removed and a precise fallback is prepared;
the rejected proxy is not retried during installation.

VV uses its saved `MeshYawOffset` with its verified collision template, avoiding
using a Box visual hull as an orientation oracle. **All 30 VV definitions were
compared against the production calibration path.** SC/ES retain the existing
socket/physics art calibration and per-server yaw cache. No authoritative fidelity
was downgraded. A missing asset still uses the original blockout geometry.

### Seed working set and workers

After layout/scenario/atmosphere selection, `ChunkRuntimeCore.expand` supplies
ordinary rows and conditional attached rooms. Each used single-mesh/recolour or
multipart component contributes an AssetKey/role request. Requests are deduplicated
and sorted, including ENTRY, boss approaches, BOSS and dependent room content.
Unused biome assets and enemy definitions are never enumerated for preparation.
The collector consumes no random stream and does not mutate layout/content.

`GameConfig.Expedition.AssetPreparationWorkers = 6` bounds the queue. A second
owner-wide gate also bounds overlapping preparation calls to six active runtime
API calls. Cached/local requests resolve immediately; only missing runtime
templates invoke AssetService. Internal completion order cannot select content.
`AssetPreparationEnabled=false` retains the original synchronous loader route.
Diagnostics are off by default; `AssetPreparationDiagnostics=true` exposes quiet
snapshot counters. Config validation rejects invalid limits/flags.

### Atmosphere

Geometry, collision, transit and existing gameplay fixtures are prepared before
placement. Group creation supplies pending empty anchor arrays and bounds so the
client need not rediscover them. `GenerationAnchors` computes presentation samples
afterward, yielding per `AtmosphereRayBudget=128`. Its 128-entry FIFO stores
chunk-local hits and normals, keyed by world/chunk/atmosphere/asset/art orientation,
collision/blockout state and relative floor height. Quarter-turn reuse restores
legacy acquisition order. Dynamic EncounterGate chunks stay on runtime discovery.

Destroyed groups cancel work and cannot publish results. Existing
`Expedition_Atmosphere` carries `AnchorsOnly`, `StageName`, `GenerationToken` and
`Anchors`; the client rejects a different stage/token and updates the existing
effects without resetting movers. Repeated anchor packets do not duplicate lights.
`Expedition_Started` includes the token and pending or completed anchors. Setting
`DeferredAtmosphere=false` restores blocking discovery with the same sampling rules.
This is a modest presentation cleanup; atmosphere was not the measured bottleneck.

## Targeted production verification

One fresh **Play server/application cache** per world, seed 1 twice, six actual
production build/group/member placements. The timer begins immediately before
`buildStage`, following destination/seed selection; it includes preparation,
installation, placement and a real Humanoid grounding check (two grounded frames).
Completion waits for both grounding and optional anchor readiness. Temporary hooks
use BindableFunctions in the actual initialized server/client contexts, rather
than requiring an uninitialized MCP copy. Hooks are not in production sources.

This is not a CDN/device-cold published-server test: Studio's process/native asset
cache can survive Play restarts. Request validation, client-to-server network
latency and reserved-server launch are outside this generation timer. There is
only one cold run per world; do not infer a new broad-cohort percentile from it.

| World | Layout solved | Layout → assets | Assets → grounded | Request → grounded | Request → completion | Seed keys/roles | API / Precise | Local templates | Max active API workers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VV cold | 0.0002 s | 0.0006 s | 0.3650 s | **0.366 s** | 1.516 s | 11 | 0 / 0 | 11 | 0 |
| SC cold | <0.001 s | 5.683 s | 1.516 s | **7.199 s** | 7.634 s | 13 | 13 / 13 | 0 | 6 |
| ES cold | <0.001 s | 5.749 s | 1.568 s | **7.317 s** | 8.166 s | 102 | 51 / 51 | 51 | 6 |
| VV reuse | <0.001 s | <0.001 s | 0.366 s | **0.366 s** | 0.366 s | 11 | 0 / 0 | 0 | 0 new |
| SC reuse | <0.001 s | <0.001 s | 1.315 s | **1.315 s** | 1.315 s | 13 | 0 / 0 | 0 | 0 new |
| ES reuse | <0.001 s | <0.001 s | 1.317 s | **1.317 s** | 1.317 s | 102 | 0 / 0 | 0 | 0 new |

Across these six maps: median **1.316 s**, worst **7.317 s**. The matched preserved
control layouts made **310 creation / 310 Precise / 140 visual-only Precise** calls;
this migration made **64 / 64 / 0**. These counts belong to the six-map cohort,
not the original 1,452-call cohort. There were 64 unique runtime preparations,
zero duplicates, 62 authored resolutions and 126 cold cache misses/canonical entries.
The warm runs had **281 hits, zero misses, zero API calls**: all preparation and
placement requests hit cache. The warm hit count includes both preparation checks
and placement clones. Working-set deduplication meant zero observed production
in-flight waits; the real-scheduler duplicate-caller invariant separately proved
one preparation and one in-flight deduplication.

Observed total Studio memory after placement: VV 3,350.6 → 3,380.3 reported MB,
SC 3,552.0 → 3,554.4 reported MB, ES 3,606.0 → 3,612.8 reported MB. These include the hub,
geometry, clients, engine caches and asynchronous GC; **they do not isolate native
template-cache cost**. Cache ownership is explicit and the retained instance counts
are measured, but published-server/native-memory profiling remains open. Boot only
indexes local references; boot-time impact was not separately timed and is not
credited as a generation improvement.

## Automated validation and differences from the prototype

- 1,063 unit assertions pass, including 300 VV/SC/ES working-set determinism comparisons.
- 4,280 legacy loader comparisons, multipart rotations and atomic failure tests pass.
- 32 focused real-Studio asset/worker/fidelity/fallback assertions, 10 anchor cache
  assertions and 9 client late-effect assertions pass. Synthetic workers reached
  the configured maximum of 3; production reached its configured maximum of 6.
- All six players grounded; all six actual clients received completed anchors.
- Six paired maps: zero collision differences above 0.05 stud, identical recorded
  visual signatures and art yaw; maximum query float variation 0.004 stud.
- Full VV catalogue: 30 prepared clones, matching rotations/render signatures,
  4,033 collider parts with preserved flags; zero sampled collision differences
  above 0.05 stud. Samples include ray/body casts and socket/inset positions.
- StyLua passes; all 140 runtime/test files compile; Rojo 7.7 build passes.
  Full-source Selene has zero errors and 20 existing warnings (using
  `--allow-warnings`); focused migration/test lint has zero errors. Remote CI has not run.

Production replaces prototype-global caches/registries with explicit owners,
keeps authoritative calibration, retains safety switches/fallbacks and does not
bring experiment-only profiling, proxy generation or world registries into runtime.
Cold SC/ES results are slower than the historical prototype's fastest cohort;
AssetService latency/native caches vary, and authoritative calibration is retained.
The remaining cold bottleneck is **precise SC/ES preparation (~5.7 s)**; after reuse,
physical landing/client delivery dominate. No additional layout optimization is indicated.

Samples and signatures are not exhaustive collision traversal or rendered-image
acceptance. ES's previously recorded remotely positioned decorations/streaming
limitations remain unchanged. Cold anchors finished 0.435–1.150 s after grounding;
actual visual pop-in acceptance remains pending. No broad proxy migration is allowed
on the strength of these tests.

## Exact owner Studio acceptance checklist

Serve **this worktree** with Rojo, review its sync preview, and use a fresh Play.
Studio was restored to its original Edit sources; the migration is not saved in
the open place. Test normal maps and `/roll <world> test` catalogues, then `/enter`.
Repeat entry in one server to inspect reuse. Use fly only to reach test areas;
disable fly for collision checks. Keep existing rollback assets and benchmark evidence.

**Verdant Valley**

- [ ] Spawn is correctly oriented; player grounds and return portal works.
- [ ] Normal paths and socket joins are continuous; elevations remain walkable.
- [ ] Dedicated collision templates exist; terrain visuals do not supply collision.
- [ ] Stairs, ledges, solid props and intended holes behave correctly.
- [ ] Boss approach/Wide joins and boss area are reachable and correctly bounded.

**Sky Citadel — prioritize invisible-shell risks**

- [ ] Walk under arches and through intended gaps; no invisible shells over decks/openings.
- [ ] Railings/barriers block only where intended.
- [ ] Bridges, stairs and raised platforms have correct collision and seamless joins.
- [ ] Boss approach and boss area are reachable, bounded and correctly oriented.
- [ ] Authoritative parts retain PreciseConvexDecomposition; no Default import was substituted.

**Ethereal Scape**

- [ ] Multipart chunks are complete, aligned and correctly oriented.
- [ ] Foliage/decorations remain non-colliding and do not intercept gameplay queries.
- [ ] Streaming delivers required client geometry before use; player grounds correctly.
- [ ] Inspect distant decorative pieces at their authored locations and across streaming transitions.
- [ ] Stairs/ramps, raised islands, barriers, socket joins and intended gaps remain correct.
- [ ] Boss approach/area and the conditional shrine room/transit/gate retain existing behavior.

**General**

- [ ] No missing visuals, missing collision, unexpected fall-through or orientation regressions.
- [ ] Intended holes/gaps stay open; no invisible collision shell returns.
- [ ] Compare server/client geometry; repeat with StreamingEnabled and representative quality settings.
- [ ] Atmosphere/weather/moving scenery do not reset or visibly break on late anchors.
- [ ] Accept cold-entry presentation arrival and pop-in; test exit/re-entry before scans finish.
- [ ] Existing projectiles/raycasts and any already available enemy/combat checks behave correctly.
- [ ] Confirm published fresh-server/CDN/network behavior and memory before production adoption.

Enemy spawning is not part of this acceptance pass; it has not been implemented.

## Future designer-authored collision pilot contract — proposal only

Start with **5–8 manually selected complex SC/ES chunks**, covering arches, gaps,
stairs, platforms and a boss boundary. Extend to other worlds only after acceptance.
No Blender migration or pilot assets were created in this task.

1. **Naming/pairing:** keep existing UPPER_SNAKE AssetKeys and chunk IDs. Use a
   named collision Model under the existing `ServerStorage.LuckboundChunkKits`
   mount, referenced by existing `CollisionTemplate` data. Follow current
   `<chunk identity>_COLLISION…` names and world `*_STRUCTURE.rbxmx` / `*_COLLISION.rbxmx`
   exports; decide the exact new names in the pilot, not a parallel registry.
2. **Visual identity:** `AssetKey` or existing `MeshParts` continues to identify
   visual content. If uploaded proxy meshes are needed, they get separate manifest
   keys referenced by the authored collision export; Spawn/ENTRY, approach and BOSS
   assets use the same content contract, outside ordinary random pools as today.
3. **Coordinates:** one metre = one stud; apply scale/transforms. Visual and collision
   share the authored ground-centred origin, pivot and imported axes. Record offsets
   relative to that frame, preserving existing `GroundOffsetY`/bounds-centre handling.
   Collision rotates/translates with the visual art frame, including its saved yaw.
   Do not bake assembled-map world coordinates into a proxy.
4. **Geometry:** author floors, walls, meaningful barriers, cliffs, stairs/ramps,
   holes/gaps and boss boundaries. Omit decorative detail. Prefer primitives or
   separate convex pieces for each solid region. A single Default hull around a
   concave arch/gap is not acceptable; any concave collider needs verified authored
   fidelity. Never replace an opening with an automatic object-bounds box.
5. **Sockets:** preserve existing IDs, Kinds, widths, heights and layout-frame transforms.
   Proxy walk surfaces must meet every socket landing; rendering art offsets do not
   change layout sockets. Keep authored future marker data independent of collision meshes.
6. **Runtime gate:** only an approved complete proxy permits visual-only preparation.
   Missing/incomplete proxies retain precise visual collision. Current generic
   multipart content still uses authoritative components; the pilot must explicitly
   extend/validate proxy installation for an entire multipart assembly before ES adoption.
7. **Acceptance:** compare all four rotations to current precise collision with dense
   downward/body/horizontal casts, seam pairs, stairs, holes and boss boundaries;
   traverse with a real player, camera and gameplay queries. Reload the saved export
   to verify serialized fidelity. Record allowed intentional differences; owner approval
   precedes turning off authoritative visual collision. Retain rollback content until
   CI, fresh Studio and published checks pass.

## Future enemy-spawn authoring contract — proposal only

The integration seam is the expanded layout rows and their chunk definitions,
before/alongside instantiation. Future chunk-local marker data belongs in content
beside sockets, boundaries and presentation metadata; a future helper can transform
it using the existing **layout-frame** centre and `ChunkCore.yawRadians(placed.Yaw)`.
Do not apply visual-only art yaw a second time. The exporter must convert authored
coordinates into this frame, just as sockets and boundaries already do.

The chunk owns **eligible locations**; a future encounter director owns **which
positions are used and what enemies appear**. A minimal future marker would identify
itself, a local position and optional facing/category (ground/flying/elevated).
Only add footprint/size class, allowed archetype category, group, minimum entry
distance, reuse policy, elite capability, scripted/scenario restrictions or
biome/Fate compatibility when a real encounter requires them. Ordinary markers
must not hard-code enemy identities. Fixed bosses/scripted encounters may retain
dedicated markers/rules.

Future flow: solve layout → transform/register eligible marker positions → playable
geometry → encounter population by triggers/director. Pre-entry enemy requirements
must be explicit encounter rules. Map asset preparation remains separate from
enemy preparation. Avoid large rediscovery scans for authored marker positions.

No enemy markers, runtime fields/types, new remotes or director were declared here;
there are consequently no new unread enemy fields to register in RESERVED.md.
The proposed hierarchy is conceptual, not a required replacement of current kits.

## Reproduction, files and cleanup

Production files: `Util/AssetPreparation`, `ChunkAssetCore`, `GenerationAnchors`,
`ChunkLoader`, `Schema`; `Core/GameConfig`, `Types`, `Net`; server `ExpeditionSystem`;
client `ExpeditionController`, `AtmosphereEffects`. `CharacterAnimator` only adds
a missing assertion message to clear a pre-existing lint error. Focused tests and the existing
suite are under `tests/`. Docs/spec/index/handoff changes accompany them.

Raw verification: [summary](benchmarks/generation_migration_summary.json),
[six placements](benchmarks/generation_migration_studio.json),
[paired comparisons](benchmarks/generation_migration_comparison.json),
[contracts/catalogue](benchmarks/generation_migration_contracts.json),
[actual clients](benchmarks/generation_migration_client.json).
`tools/verify_generation_migration.py` preserves a completed cohort;
`verify_generation_contracts.py --invariants-only` reuses its completed catalogue.
`summarize_generation_migration.py` reads evidence commit bb47f91 without running tests.
`studio_mcp.py` is the local stdio transport. The Studio instance can be selected
through `LUCKBOUND_STUDIO_ID`; connect the MCP before running these temporary checks.

Recommend retaining the original synchronous route, precise collision, all rollback
exports, parked recolours and the benchmark branch until acceptance. No assets,
manifest entries or older iterations were deleted. Only the superseded inline
anchor scan was factored into the owned utility; its original is preserved in git.
Temporary `.tools` profiling outputs are ignored. Supported runners/test evidence
remain for review; no noisy benchmark hooks ship in the runtime.
