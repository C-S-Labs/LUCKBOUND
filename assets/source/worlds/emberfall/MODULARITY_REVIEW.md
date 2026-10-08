# Burned Plains — modular continuity recommendation

2026-10-05. The visual foundation is **owner-approved**. This pass tests its
technical decomposition; it does not replace the visual design or create a kit.

**Recommendation:** authored chunks plus a deterministic assembly appearance plan,
authored road guides with joined presentation, and explicitly non-playable
continuation scenery. The Blender proof supports this division of responsibility.
**Do not propagate it into production yet:** the Roblox appearance backend and a
bending/branching layout still need a bounded proof. No production code changed.

## What the repository actually supports

| Contract | Actual implementation / implication |
|---|---|
| Layout | `src/shared/Util/ChunkCore.luau` is pure numerical assembly. `worldSocket`, `placeAgainst`, `overlaps` and `yawRadians` support 0/90/180/270 and socket `OffsetY`. Rectangular X/Z bounds drive overlap rejection; height does not permit overlapping stacked footprints. |
| Chunk import | `ChunkLoader.luau` supports single or multipart uploaded meshes, walking-origin correction using `GroundOffsetY`, art-only yaw correction and socket-ground probes. The measured/corrected art transform must also transform appearance samples and road guides. A square grassy deck is ambiguous to automatic yaw detection; export orientation must be explicit and consistent. |
| Assets | `AssetManifest.luau` maps logical keys to uploaded Roblox mesh IDs. `ChunkAssetCore.luau` and `AssetPreparation.luau` prepare canonical templates by asset/role; cloning does not confer different baked vertex colours. Never recolour a shared cached template for one placement. |
| Props | Solid props are server-loaded by ChunkLoader; ambient props are client-loaded by PropController. Both use authored chunk-local placements and yaw. Neither currently selects a burn stage from an assembly field. |
| World planning | ExpeditionSystem assembles the layout, then scenarios/atmosphere and assets. Existing atmosphere mesh suffixes select a whole static asset; they cannot create an irregular field across differently rotated pieces. GenerationAnchors supplies placement/presentation samples, not an ordered connective-road graph. |
| Scenery | §7.7 and ChunkCore support budgeted BACKDROP placement with zero sockets, seeded selection/yaw and size-aware bounding boxes. This is not a grounded terrain-edge stitching system and does not automatically disable collision. |
| Connections | Layout rows contain placements and Index, but no explicit consumed-socket edge graph. Index alone is insufficient for branching roads; entry/branch/backdrop indices are not a simple universal route order. Preserve actual socket connections in a future plan rather than guessing from nearest centers. |

No existing continuous burn mask, terrain shader hook, road spline builder or
general connective-feature plan was found in the relevant contracts. Production
assembly currently requires its normal entry/path/boss library; this test uses
the real numerical socket helpers for a three-piece Area I segment, not a fake
complete expedition with a boss.

`MODULAR_MAPS.md` currently requires independent chunk art with nothing crossing
boundaries. An optional assembly-owned visual layer needs a reviewed amendment
to that rule and the build spec before production adoption; it does not waive
independent traversal or socket compatibility. Its warning against flattening
every perimeter remains valid. The proof's two connected-edge collars are a
bounded experiment, not a new all-edge flattening contract.

## Burn-state ownership and practical backend

Chunks retain terrain/collision, combat shape, authored blade/prop/tree anchors,
protected pockets, landmarks and local road guides. An assembly plan supplies the
broad progression, coherent irregular front, seed, transformed refuge anchors
and low-frequency appearance parameters. It can choose a stage at an authored
anchor; it must not scatter replacements over the authored composition.

Evaluate the field at **final assembled positions**, after placement and art
orientation corrections. One position has one answer on both sides of a boundary.
Sample corresponding terrain-edge vertices consistently and blend the approved
palette in a small transition band. Preserve matching geometry and shading too:
a colour mask cannot repair geometric or normal discontinuities. Sample fire and
distant smoke from the same field, outside roads/refuges, rather than independently
sprinkling flames in each chunk. Vertical changes do not reset progression;
height/drainage can influence authored protection without creating elevation bands.

| Option | Verdict for this pipeline |
|---|---|
| Ordinary world-space shader | Not an available custom shader hook in the inspected pipeline. Roblox UV/PBR materials do not by themselves evaluate an arbitrary assembly mask. Do not promise Blender nodes will export as runtime shader logic. |
| Baked per-chunk gradient | Reject as the general solution: yaw moves the colours with the chunk, and independent variants cannot guarantee all irregular edge matches. |
| Authored whole-chunk variants | Useful for exceptional local silhouettes or a deliberately curated layout catalogue. Multiple independent boundary signatures create a combinatorial library; not the preferred broad field. |
| One colour per MeshPart / many overlay plates | Too coarse, or too many parts and overlapping surfaces. Can supplement local damage; do not replace the terrain field with visible square dressing. |
| Assembly-derived vertex colours | Preferred **candidate backend** for the broad flat-palette ground. Fixed geometry, per-placement visual instances, deterministic field sampled once. Existing authoritative terrain/proxy collision stays unchanged. Imported corner-colour IDs must be authored independently enough for distinct samples; shared colour IDs cannot simultaneously hold different colours. |
| Assembly-derived textures | Alternative if texture authoring proves superior, but needs per-placement UV/world mapping and editable/baked texture handling. An atlas alone does not solve rotated mappings. Adds texture memory and another permission/backend path. |

Roblox EditableMesh permits attribute editing and fixed-size imports, but has
published-game enablement/asset permission requirements, strict client memory
budgets and a 20,000-triangle/60,000-vertex limit per mesh. See the
[official EditableMesh documentation](https://create.roblox.com/docs/reference/engine/classes/EditableMesh).
These constraints make it a **candidate requiring a scratch-place test**, not a
production commitment. Each 8,958-triangle terrain fits the per-mesh triangle
limit; the large review grass/scenery batches do not all fit and must not be
ported wholesale. Use small authored flora clusters with discrete stage assets
and tint, keeping their positions. A visual client backend would receive a small
plan and reproduce it locally; verify multiplayer presentation and lifecycle
rather than assuming editable content will replicate like ordinary uploaded meshes.

The current VV production exporter is also a concrete constraint:
`prepare_production_colors` in `export_verdant_valley_kit.py` expects a `Col`
BYTE_COLOR/CORNER layer and refuses unexpected layers or unresolved linked colour
nodes. This proof's `AssemblyColour` FLOAT_COLOR/POINT layer and Blender node are
**not directly export-ready**. A disposable export adapter would create suitable
corner data and independently editable colour samples, retain source coordinates
and guides in content, and verify Roblox import colour/orientation once. Existing
FBX export uses SRGB colours, -Z forward/Y up and baked space transforms; colour
space and final art yaw are part of that verification, not assumptions.

Fallback on allocation/permission failure must be deliberate: an approved curated
appearance/layout, not a silent return to independently baked gradients. Resolve
that policy before production adoption. Cache immutable source topology, not a
single mutable appearance shared across different placements.

**Layout limitation:** the proof uses a straight ordered route in two orientations.
For an Area I route that bends or doubles back, a nearest-segment arclength lookup
can jump at projection switches. Before supporting those layouts, construct a
continuous area field from connected route/progression anchors, or constrain this
area's layout to a monotonic directional corridor. Test adjacent branches and
folds explicitly. The current random assembler does not enforce that constraint.
Do not bake permanent world north into the schema or claim arbitrary layouts are
already solved. Transformed damp/wall protection anchors must follow their local
terrain; the proof retains the approved global refuge pattern, so it does not yet
validate that semantic alignment after independent rotation.

## Road: hybrid, with authored control

The approved `old_winding_field_track` is one **review presentation mesh**, not a
runtime connective feature. Its world bounds are approximately **33.255 × 1,176 ×
56 studs** in Blender X/Y/Z, from Y -560 to 616. Curvature accounts for the wide
bounding box; actual track width is about 7–10 studs. It spans three studies and
their scenery. Collection membership `Countryside_SOLID_DECOR` does not establish
production collision. It demonstrates visual continuity, not a loader precedent.

Recommendation **D: hybrid**. Chunks author local centerline/width/height controls,
mandatory gates/bridges/crossings and composition constraints. Assembly transforms
those guides, uses actual connected mouths, reconciles width/tangent/elevation
at the joints, and presents a continuous track. Keep roadside walls, wagons,
milestones and local damage chunk-owned. Do not route a free spline through
authored combat or landmark space merely because centers connect.

For production, start with authored road meshes whose mouths match, plus a small
visual join strip where needed. A single generated visual strip from joined guides
is a candidate if the EditableMesh backend is accepted; it need not be one huge
asset or one collider. Both presentations share one world/route-distance colour
and texture plan, avoiding width or UV resets. Terrain provides walking collision
for an ordinary dirt track. Bridges require their own authored colliders and
constraints. Generate once per seeded layout, not every frame; client presentation
must not alter server traversal. Preserve matching tangents and draped heights,
not just coincident road endpoints.

This Blender test joins 297 guide samples including scenery extensions into one
strip. It validates transformed local guides and consistent width/colour across
two joins; it does not implement a runtime spline, texture transport or bridge.

## Footprints and interior_continuation

The approved object is **256 × 360 × 107.834 studs** in Blender X/Y/Z, bounds
X [-128,128], Y [384,744], Z [-40,67.834]. Much of its height is buried shell.
It belongs to `Surrounding_Continuous_Grassland_REVIEW_ONLY`, has no sockets or
playable Role, and was created by the foundation generator's scenery loop.
**It is non-playable continuation terrain**, not a CAP chunk or secret fourth
playable study. Preserve it in the approved scene; replace its fixed straight
placement with explicit scenery planning when a final layout needs a different edge.

Standard playable Burned Plains pieces remain **256 × 256**. The repository does
not universally mandate that size: for example VV_BOSS_SANCTUARY declares
384 × 256, and Types/Schema accept positive rectangular dimensions. That supports
deliberately declared special rectangular pieces, not arbitrary irregular collision
or overlapping multi-cell chunks. Audit bounds-dependent consumers and author
matching sockets/proxies before any new special transition/arena. No such piece
was created here.

Scenery may be larger and have zero sockets, with explicit visual-only/query/
collision policy, no traversal role, and continued hills/materials matched to the
exposed assembled edges. Current BACKDROP placement is useful for distant objects;
grounded grassland aprons need an additional edge-aware scenery plan. They must
not conceal holes in playable terrain or replace the required invisible safety
boundaries (owner's 64-stud requirement remains in force).

## Isolated prototype and results

- Exact live approved state checkpointed before experimentation:
  `E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/Input_ApprovedBurnedPlains.blend`.
  Original `BurnedPlains.blend` is untouched; the review file also retains its scene.
- Review file: `E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/BurnedPlainsModularity.blend`.
  Three 256-square pieces, yaws **0/180/0**; secondary scene turns the entire
  assembly to **90/270/90**. This is not an independently selected elbow layout.
- Actual ChunkCore helper probe establishes coincident opposing sockets,
  elevation placement, non-overlapping footprints and all four yaw transforms.
  The reversed middle piece creates a dip; it does not preserve the original
  56-stud monotonic ascent. The route goes from ground 0 to 2.074 studs, with
  join datums 14.519 and -12.444 studs. Authored interior relief remains.
- First attempt exposed slope discontinuity and grass-stage silhouettes. Final
  isolated meshes add 24-stud matching join collars, max adjustment **2.402 studs**;
  interior vertices outside the collars remain unchanged. Existing grass anchors
  select half/full-height burned/surviving stages rather than carrying old heights.
  These are prospective authoring requirements, not runtime terrain warping.
  Future authoritative terrain/proxy collision must match those authored collars;
  the colour/road presentation backend must not move collision at runtime.
- Two 65-station saved joins: maximum height gap **0.000003815 stud**; maximum
  edge colour-channel difference **0.000000030**. Three terrain meshes remain
  closed, 8,958 triangles each. Road has one common sample row at each join.
- Approved planar field is unchanged: playable **18.88% green / 31.05% stressed /
  50.07% charred**, the same as the approved three-study aggregate. The approved
  full-land 18/31/51 target is not replaced by per-chunk quotas. Fire follows the
  same irregular interface, including a tongue across the opening/mid boundary.
- 355 existing local objects retained and transformed, including walls/fences,
  staged tree parts, flowers, rosettes, milestone, gates and interior footings.
  No generic prop scattering or new landmarks. Scenery is explicitly separated.
- Countryside, fire direction, long views and continuous road survive the test.
  The mask has no tile colour reset. Some surface shading/density bands remain
  visible in the top view; C0 numerical agreement is not final normal/LOD proof.
  Tree silhouette variants and refuge/terrain semantics need a production sample.

Evidence directory: `E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/`.
`modularity_contact_sheet.png` contains broad overview, ownership-marked top,
baseline player eye, raised boundary/fire view, interior road and quarter-turn top.
Individual renders `01_assembled_overview.png` through `06_quarter_turn_top.png`;
`07_ownership_overlay.png` explicitly shows playable squares and exterior scenery.
The cyan boxes are a diagnostic overlay, not scene geometry.

## Repository implications and readiness

Eventually, after owner review, a generic optional continuity plan would touch
Types/Schema and the build spec; ChunkCore's connection records/layout planning;
ExpeditionSystem's post-layout planning; World/Chunk/Props content for parameters,
guides and anchors; client appearance/prop presentation; ChunkLoader's presentation
integration and transform handoff; AssetPreparation/ChunkAssetCore caching and
AssetManifest/export tooling for suitable assets. GenerationAnchors can consume
the same guide/ground data if useful. Do not add Emberfall-specific behaviour to
a System. None of these production files changed in this pass.

Actual additions: `modularity_probe.py`, `build_modularity_study.py`,
`review_modularity.py`, `modularity_report.json` and this report. Updated the owning
Emberfall doc, approved foundation review status, STATUS/WORKLOG and index.
Blender files/screenshots remain in the external Runtime review directory.

Checks: Python compilation/JSON parsing; actual Luau socket/yaw probe; saved
Blender readback of footprints/closed terrain/road strip; evidence inspection;
generated index freshness and diff whitespace checks. Shared Blender launcher
used throughout, with normal-token retry for profile access. No connected Studio,
upload/export, mobile budget, multiplayer, production collision or broad suite.

**Ready for owner architecture review, not mass production.** Resolve the small
Roblox rendering/memory/permission probe, one bending-layout progression test,
matching edge normals/LOD, and transformed refuge/tree-stage semantics before
propagating across Area I. Those are technical continuity tests, not a request to
redesign the approved biome or start another area.

Git remains `agent/emberfall-burned-plains`, local/uncommitted; owner-owned design
and reference changes preserved. No main changes, push, PR or merge. Retain all
approved/historical scenes and first-pass sources. Recommend retiring experimental
review outputs only after owner acceptance and applicable CI/Studio/reference
checks; no assets, exports or manifest entries were replaced or deleted here.

## Owner acceptance and final technical gate — 2026-10-05

Owner approved this modularity proof. Top-down bands are polish unless identifiable
from plausible gameplay or reachable elevated cameras. Subsequent
[PRODUCTION_READINESS_REVIEW.md](PRODUCTION_READINESS_REVIEW.md) closes the bounded
Studio colour/cache/loader/client test, returning-route progression and transformed
refuge/tree-state questions. It identifies a remaining production blocker: rising
turns currently close full edges using layout-specific height changes up to ~18
studs. Reusable fixed edge profiles and matching collision must be proved before
kit expansion; the straight proof's 24-stud collar is not automatic authority for
runtime reshaping. Approved inputs remain preserved; no later area is opened.

The subsequent [EDGE_PROFILE_REVIEW.md](EDGE_PROFILE_REVIEW.md) closes that blocker:
fixed curved profiles and corner datums, unchanged alternate neighbours at all
quarter yaws, convex seam collision and two bounded Studio character crossings.
The original collar proof remains preserved; no production kit is authored here.
