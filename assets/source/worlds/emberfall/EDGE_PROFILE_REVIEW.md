# Burned Plains authored edge / collision contract — 2026-10-05

**Geometry/collision gate passes. Stop for owner review before Area I authoring.**
This supersedes only the previous rising-turn blocker. All accepted appearance,
burn progression, vegetation, road, footprint and visual decisions remain locked.
There are six isolated test sources, not a production chunk library.

## Root cause of the previous correction

`edge_profile_audit.py` reads the prior production-gate file without changing it.
`edge_profile_root_cause.json` records original versus corrected vertices.
Socket centres and opposing transforms already matched. The failure was the
**absolute shoulder/corner heights of straight climbing terrain reused at turns**.

At the first three-way corner, Blender world (128, -128), the incoming two
corners were 14.518518925 studs high; the third was 41.481479645. Averaging these
to 23.506170750 lowered the third by 17.975307465 studs. The second similar
corner required 17.975310326. Chunk 3's affected source vertex was local
(128, -128, -13.481483459), far from its road mouth. The socket was not 18 studs
wrong. The old `make_edge_profiles()` solved an incompatible corner after
learning the layout, then `local_height()` spread this change through a collar.
No reusable independently validated collision accompanied those corrections.

## Minimum profile contract

Use the existing 256 × 256 footprint, centre-at-ground origin, socket `OffsetY`,
`Facing`, `Width` and exact `Kind` matching. Blender (x,y,z) maps to Roblox
(x,z,-y). **Do not infer a profile from north/east/world coordinates.**

Two self-compatible, symmetric profiles suffice for this proof:

| Profile | Mouth relative to socket | Shoulders at both side endpoints | Prototype Kind |
|---|---:|---:|---|
| HOLLOW | 0 | +12 studs | BP_EDGE_HOLLOW |
| CREST | 0 | -12 studs | BP_EDGE_CREST |

They describe the connected terrain side, not a biome stage or compulsory hill
through the whole chunk. Standardize only connected sides. Other sides remain
authored, with compatible corners where applicable and separate exterior scenery.

- Socket at the centre of its side, outward normal, **24-stud clear mouth**.
- Canonical transverse domain -128…128; **33 height samples at 8-stud spacing**.
  Between samples, interpolate linearly. Visual 4-stud vertices use that same
  interpolation; collision does not substitute a different analytic curve.
- Samples derive from ±12 × smoothstep((abs(s)-16)/112), clamped 0…1.
  The first/last pair share the endpoint value, giving zero endpoint derivative.
  The cross-section is level within ±16 at the boundary; it curves into shoulders.
  This is a boundary cross-section, not a broad level platform inside the chunk.
- At the boundary, source design has zero normal derivative. Preserve the edge
  and its tangent; freely compose rolling interior landforms away from it.
- Use a **40-stud source-authored transition budget**, measured inward. This
  establishes the terrain when authored, never corrects an assembled neighbour.
  Only actual connected sides need this constraint. It is not a runtime collar.
  Two adjacent bands leave about 71% of the footprint outside their union.
- At adjacent connected sides, require **socket datum + endpoint height** to
  agree at their shared corner, within **0.01 stud**. Reject inconsistent source
  sockets before generating/sculpting terrain. Do not average across neighbours.
- Centre-ground rebasing happens once per source, including all socket datums,
  visual/collision meshes and local anchors. It is not a per-layout adjustment.

Example: HOLLOW arrival at datum 0 and CREST departure at datum 24 share a
12-stud corner: 0+12 = 24-12. This makes a meaningful rising turn possible without
flattening its shoulders. A reverse traversal falls by 24; no fixed-axis rule is
involved. The two-class vocabulary deliberately limits *adjacent* corner heights;
it does not promise arbitrary grades/cross-slopes at any socket. Future classes
require a concrete need and the same validator, not a taxonomy invented now.

## Compatibility and rotations

Opposing socket frames reverse transverse coordinates. Both profiles are even:
h(s)=h(-s), so their existing exact Kind matches are sufficient. HOLLOW cannot
connect directly to CREST. If an asymmetric profile is ever approved, it needs an
explicit complementary/mirror rule; none is hidden in this proof.

Use actual `ChunkCore.worldSocket`, `placeAgainst` and `overlaps`. Roblox quarter
yaw rotates local offsets; Blender applies the opposite signed Z rotation.
Centre offsets, transverse profiles, road guides and collision all travel with the
same chunk transform. No world-X/world-Z branch or normal-direction guess exists.

Names alone are insufficient: validate metadata **and sampled source geometry**.
Corner agreement is an authoring restriction, not a new runtime deformation step.

## Frozen-source interchangeability results

Sources are authored before loading any assembled poses. `height(name,x,y)` takes
only a source identifier/local coordinates. Independent hills, drainage, grass
anchors, walls/fences, trees and guide curves give the sources different identities.
Their shared boundary samples are deliberately identical under the contract.

| Source | Local composition / route | Connection types |
|---|---|---|
| A | Rising straight, maintained field wall | HOLLOW → HOLLOW, +24 |
| A2 | Level alternate predecessor, different hills | HOLLOW → HOLLOW |
| B1 | Level straight, shallow drainage / damaged fence | HOLLOW → HOLLOW |
| B2 | Rising quarter-circle right turn | HOLLOW → CREST, +24 |
| B3 | Level left turn, different arrival face | HOLLOW → HOLLOW |
| C | Ridge continuation after rising turn | CREST → CREST |

Actual measured matrix, with both A **and A2** as predecessor:

| Predecessor yaw | B1 | B2 | B3 |
|---|---|---|---|
| 0° | PASS | PASS | PASS |
| 90° | PASS | PASS | PASS |
| 180° | PASS | PASS | PASS |
| 270° | PASS | PASS | PASS |

That is 24 alternate-neighbour pairs. The additional A → B2 → C route tests two
more joins and the three-way corner, using 0°/0°/90°. B3 arrives on its west face;
its actual yaws are 270°/0°/90°/180° as predecessor yaw advances through the matrix.
This is not just rotating an already hand-fitted assembly.

Each join is measured at **129 transverse stations**, including interpolated
points, from both actual mesh grids. Maximum visual/collision mismatch:
**0.000001046 studs**. Three-way corner spread: **0.000000385 studs**.
There are **zero neighbour-specific vertex or collision edits**.
The real layout helpers also reject overlap and confirm opposing socket facings.
Saved readback checks six sources, twelve assembled visual copies and 860 actual
closed collision objects. All assembled vertex arrays remain identical to source.

## Collision and Studio result

Visual top surface uses a 4-stud grid. Simplified traversal uses an 8-stud grid,
with the **same boundary samples**. Maximum visual/collision deviation in the
40-stud authored band is 0.285378 studs; seam mismatch is below 0.000001046.
This approximation allowance is not permission for a seam step.

Initial 64-stud closed collision tiles passed source geometry, but Studio
`PreciseConvexDecomposition` introduced a ~0.22-stud artificial shoulder step.
The failed cooked-collision evidence is retained in
`edge_profile_collision_decomposition.json`; do not rely on matching FBX vertices
alone to promise matching Roblox collision.

**Selected representation:** the outermost 8-stud row on each connected side
uses individually closed **convex triangular prisms**, baked with `Hull` fidelity.
Each prism has six vertices and eight triangles. This partitions the already
authored surface; it does not flatten, warp or replace it. Deduplicate overlapping
corner cells. Interior tiles remain closed simplified terrain with precise
decomposition. Use non-collidable visual terrain plus the existing
`CollisionTemplate` / `ChunkLoader.attachWalkCollision` model route.

In the local testing place, 254 unchanged source seam prisms covered the two
representative full-width joins, including the rotated C. **84/84 bounded rays
hit**. Largest height difference across the ±0.05-stud samples was
**0.005448 studs**, including the genuine approach slope and world-coordinate
precision. **Two R15 walks passed**, crossing A/B2 and B2/rotated C without
catching/falling. The source-centred final geometry was the tested geometry.
Temporary characters/meshes were removed; Studio is back in Edit. No save, asset
upload, production IDs or place security changes occurred during this task.

The conservative proof has 144 collision pieces for a straight, 142 for a turn.
These are static, anchored, server-authoritative colliders. Do not enable collision
on editable appearance copies. Instance cost is real: retain measurement and allow
only validated convex merging/authoring simplification that keeps boundary planes.
Production import must bake fidelity correctly and preserve source pivots; the
loader already clones these model parts without recooking them. A final exported
production piece still needs the normal Studio import/walk check. No production
export, whole-run performance test or published-server test was attempted here.

## Visual quality / collars

Normal eye (+5), raised plausible view (+12) and reachable ridge eye (+5) show
rolling land, a continuous curved road and no identifiable socket pads/terrain
cracks. The collision diagnostic deliberately shows its topology. Separate,
explicitly non-playable scenery hides the kit extent; it never alters the frozen
playable pieces. This is a geometry study, not a replacement visual foundation.
Approved 18.88/31.05/50.07 composition remains unchanged in the preserved gate.

**Replace the experimental 24-stud repair collar with the source-authored profile
region.** There is no runtime collar and no post-layout correction here. The
40-stud budget is for shaping a source, not burying an incompatible edge. Allowed
future seam dressing/tolerance is at most 0.01 stud, never ~18-stud sculpting.
Do not add a repeated visible road flange, strip or level socket apron.

## Validator and authoring safeguards

`validate_edge_profiles.py` rejects wrong socket metadata/Width, footprint/grid
coordinates, centre datum, visual/collision edge heights and inconsistent adjacent
corners. It checks all quarter rotations via actual placement output and tests four
negative controls: visual +0.25, collision +0.25, Width 25, corner datum +18.
All four are rejected. `review_edge_profiles.py` reads the saved file, verifies
actual collision top vertices, convex seam-cell tags and frozen assembled copies.
The builder checks closed manifold collision and recalculates face normals.

For production authoring: import these canonical edge samples as guides; compose
the interior independently; keep mouth approach clear; derive collision from the
same traversable surface; preserve exact convex outer cells; validate before
export and retain cheap cooked-collision/walk acceptance after import. The small
validator currently consumes the isolated heightfield payload and saved naming
contract. Supporting arbitrary sculpted topology requires a narrow Blender
sampling adapter before that authoring method is used, not an unimplemented
runtime framework. Existing safety-boundary requirements still apply to real
playable pieces and must leave valid sockets open.

## Architecture impact and repository state

**No production schema/runtime changes required for this geometry contract.**
Existing socket Kind/OffsetY/Facing/Width, quarter yaw, overlap policy and authored
collision models are enough. Future source exporter/import packaging must preserve
the profile certificate and correct per-part fidelity/pivot. World content can
declare the appropriate Kinds when the owner authorizes the kit. No new unread
field, remote, manifest entry or runtime special-case was introduced.

The previously proposed appearance/route/prop integration remains separately
review-gated in `PRODUCTION_READINESS_REVIEW.md`; it is not reimplemented here.
Generation must choose compatible Kinds; no neighbours may request terrain repair.
Shared corner validation protects rising turns before any route is generated.

This task added `edge_profile_*` audit/contract/layout/evidence/Studio probes and
reports, `build_edge_profile_study.py`, `validate_edge_profiles.py`,
`review_edge_profiles.py` and this document. Updated the biome, modular/authoring
addenda, build-spec investigation, prior review status links, STATUS/WORKLOG/index.
No `src/`, production assets/IDs, runtime systems or exports changed.

Exact new files under `assets/source/worlds/emberfall/`:
`EDGE_PROFILE_REVIEW.md`, `build_edge_profile_study.py`, `edge_profile_audit.py`,
`edge_profile_contract.py`, `edge_profile_layout.py`, `validate_edge_profiles.py`,
`review_edge_profiles.py`, `edge_profile_evidence.py`, `edge_profile_studio_probe.py`,
`edge_profile_character_probe.luau`, `edge_profile_root_cause.json`,
`edge_profile_report.json`, `edge_profile_saved_readback.json`,
`edge_profile_collision_decomposition.json`, `edge_profile_studio_report.json`,
`edge_profile_character_report.json`.
Exact updated paths: `docs/biomes/EMBERFALL.md`, `docs/MODULAR_MAPS.md`,
`docs/CHUNK_AUTHORING.md`, `docs/PROTOTYPE_BUILD_SPEC.md`, `docs/STATUS.md`,
`docs/WORKLOG.md`, `INDEX.md`, `INDEX_MAP.md`, and the existing uncommitted
`MODULARITY_REVIEW.md` / `PRODUCTION_READINESS_REVIEW.md` in this source folder.

Branch remains `agent/emberfall-burned-plains`. No commit: owner/prior-session
changes already share the branch, including reference image replacements and
uncommitted approved proof files. Do not stage that mixed work by inference.
Approved foundation, modularity and production-gate input hashes are unchanged;
the exact dirty live scene is checkpointed as `Input_ApprovedLive.blend` below.

## Evidence / repeatability

External directory: `E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview/`.
Proof: `BurnedPlainsEdgeProfiles.blend`. Comparison: `contact_sheet.jpg`.
Individual images: 01 overview, 02 source A, 03 A/B1, 04 A/B2, 05 A/B3,
06 rotated A/B2, 07 visual seam, 08 collision topology, 09 player eye,
10 elevated gameplay, 11 reachable ridge. `layouts.json`, `source_meshes.json`,
`validation.json` and generated transient Studio command are beside the scene.
All approved files remain at their original paths.

Run `edge_profile_layout.py` with the installed Luau wrapper under a normal user
profile. Run build/readback through `tools/run_blender.py`, never Blender directly.
Pure Python validator can run against the external payload. Regenerate the contact
sheet with `edge_profile_evidence.py`. Studio probes are manually invoked isolated
commands, never placed in production startup or shipped content.

**Retirement:** keep the old 24-stud-collar modularity file, the ~18-stud correction
gate and the failed decomposition report as historical evidence. No production
asset/export/manifest was replaced. Remove superseded experimental copies only
after owner acceptance and relevant CI/Studio checks; approved originals remain kept.

GO — Burned Plains architecture is ready for production Area I chunk authoring.
