# Burned Plains Batch 1 bounded authoring API

Approved contract snapshots: `E:/BlenderAIProjects/Runtime/Emberfall_Batch1/inputs`.
Current authoritative design/reviews remain in the owner checkout; read them there.
Production changes live in separate Batch 1 worktrees, never that checkout.

Use `batch1_shared.py`: init(), build(spec,dress), finish_lane(lane,rows,contexts).
Spec keys: id/title/purpose/seed/edges/land/guide, optional landmark/grass_filter/grass_count.
Edges insertion order is arrival then departure, S first. Values (HOLLOW|CREST,datum).
land(x,y) is YOUR distinct source-local hills/drainage composition. It is faded
inside source transition bands; no layout or neighbour input is ever accepted.
guide is straight(amplitude) or turn(E|W), or an authored sampled XY guide with
the same endpoints and outward tangents. Keep sharp deviations out of mouth.

dress(ctx) authors composition with tree/wall/fence/rock/beam/box/refuge methods.
Use ctx.ground(x,y) for prop roots, ctx.c for meshes and ctx.rng for deterministic
variation. Local road width is 8.4; place deliberate roadside props outside ±7.
Do not block a 24-stud socket mouth. Trees must have StateAnchor/StateRole;
custom wooden hero props should carry equivalent local root metadata.
No fixed chunk burn stage: previews are stressed; assembly assigns all stages.
Preserve local storytelling through justified ctx.refuge(...,reason).

Terrain has a closed 4-stud visual grid, <10,000 triangles, active Col BYTE_COLOR
CORNER data. Exact 8-stud canonical edge samples and shared corner datums remain.
Eight studs inward are a curved extrusion, not a flat socket pad. The remaining
40-stud source transition smoothly approaches unique terrain. Edge collision uses
closed transverse prisms with flat bottoms and only-collinear canonical merges;
curved intervals must remain separate because Studio Hull cooking altered the
first merged candidate. Final counts are 69–70 terrain colliders per source;
16 clipped interior tiles use PreciseConvexDecomposition. Cook verification is
the lead's responsibility. No runtime geometry correction; 0.01 tolerance.

Workers own only their lane Python source and E:/.../Emberfall_Batch1/<lane>/.
No common API changes. Report defects to lead. Never edit another lane, approved
proofs, owner source files, production runtime or manifests. Stop on ambiguity.


## Rebuild and delivery boundary

Preserved dependencies: inputs/edge_profile_contract.py, inputs/build_burned_plains.py
and approved BurnedPlains.blend materials. authority_manifest.json names current
owner documents; never replace them from this older isolated branch.

Run each lane source, then assemble_batch1.py, then check_and_export.py, then
final_evidence.py through the shared tools/run_blender.py launcher. Run
contact_sheets.py with the bundled Python/Pillow runtime. The three lane sources
import the sibling shared API; assembly uses real ChunkCore in this task worktree.
Evidence/check scripts read the external root declared in batch1_shared.py; keep
its current shared API/assembly copies synchronized when rebuilding evidence.
check_and_export.py exports ONE disposable representative terrain only, without
uploading. Do not run these jobs over approved inputs or an unsaved live scene.

Boundary metadata uses existing Height=64 / Thickness=2 / Segments, 32 source-local
segments per chunk, with mouths excluded and existing camera exclusion tags.
No production content/runtime is wired. Source profile/collision validation and a
targeted Studio cook check protect authoring; offline convexity alone is inadequate.
