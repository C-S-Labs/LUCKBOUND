"""Place existing VV_COLLISION objects over their saved VV_STRUCTURE chunks.

Run once with the owner's authoritative Verdant Valley scene open in Blender.
Only object transforms are changed; mesh datablocks remain untouched.
"""

import bpy
from mathutils import Vector
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COUNTS = REPO / "assets/export/worlds/verdant_valley/walk_collision_kit/KIT_COUNTS.md"
SCENE = "VerdantValley_CliffPassage_SeparateCollisionDeck.blend"

if Path(bpy.data.filepath).name != SCENE:
    raise RuntimeError(f"Open {SCENE} first")
structure = bpy.data.collections["VV_STRUCTURE"]
collision = bpy.data.collections["VV_COLLISION"]

mapping = {}
for line in COUNTS.read_text(encoding="utf-8").splitlines():
    if line.startswith("| chunk_"):
        chunk, _, count, model = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        mapping[model] = (chunk, int(count))
mapping.update({
    "VV_STONE_SENTINELS_COLLISION_MERGED": ("chunk_stone_sentinels", 118),
    "VV_PATH_CLIFF_PASSAGE_COLLISION_MERGED": ("chunk_path_cliff_passage", 66),
})

visual_names = {obj.name for obj in structure.objects}
groups = {group.name: group for group in collision.children}
chunks = [chunk for chunk, _ in mapping.values()]
if (len(mapping) != 30 or len(chunks) != len(set(chunks)) or
        set(chunks) != visual_names or set(mapping) != set(groups)):
    raise RuntimeError("Collision model names do not form a one-to-one mapping to visual chunks")
if len(collision.all_objects) != 4032:
    raise RuntimeError(f"Expected 4,032 collision pieces; found {len(collision.all_objects)}")

for model, (chunk, expected) in mapping.items():
    group = groups[model]
    visual = structure.objects[chunk]
    if len(group.objects) != expected:
        raise RuntimeError(f"{model}: expected {expected} pieces, found {len(group.objects)}")
    for obj in group.objects:
        if obj.type != "MESH" or obj.parent is not None:
            raise RuntimeError(f"Unexpected collision object: {obj.name}")
        if abs(obj.matrix_world.translation.x) > 1 or abs(obj.matrix_world.translation.y) > 1:
            raise RuntimeError(f"{obj.name} is already placed; refusing to apply placement twice")

for model, (chunk, _) in mapping.items():
    visual = structure.objects[chunk]
    for obj in groups[model].objects:
        obj.matrix_world = visual.matrix_world @ obj.matrix_world

# Basic transform/overlay checks; no raycasts or geometry modifications.
for model, (chunk, _) in mapping.items():
    visual = structure.objects[chunk]
    pieces = groups[model].objects
    if any((obj.matrix_world.translation.xy - visual.matrix_world.translation.xy).length > 1e-5 for obj in pieces):
        raise RuntimeError(f"{model}: object origins do not match {chunk}")
    corners = [visual.matrix_world @ Vector(corner) for corner in visual.bound_box]
    min_x, max_x = min(p.x for p in corners), max(p.x for p in corners)
    min_y, max_y = min(p.y for p in corners), max(p.y for p in corners)
    collision_corners = [obj.matrix_world @ Vector(corner) for obj in pieces for corner in obj.bound_box]
    center_x = (min(p.x for p in collision_corners) + max(p.x for p in collision_corners)) / 2
    center_y = (min(p.y for p in collision_corners) + max(p.y for p in collision_corners)) / 2
    if not (min_x <= center_x <= max_x and min_y <= center_y <= max_y):
        raise RuntimeError(f"{model}: collision bounds do not overlay {chunk}")
    print("PLACED", model, "->", chunk, tuple(round(v, 3) for v in visual.location), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("PLACEMENT_VERIFIED", len(mapping), len(collision.all_objects), flush=True)
