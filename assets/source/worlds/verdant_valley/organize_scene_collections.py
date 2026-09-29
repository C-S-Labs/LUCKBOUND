"""Organize the owner's saved Verdant Valley scene using the tested collision FBXs.

Run with the saved scene open in background Blender. This imports existing FBXs;
it does not generate or alter collision mesh geometry.
"""

import bpy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EXPORT = REPO / "assets/export/worlds/verdant_valley"
COUNTS = EXPORT / "walk_collision_kit/KIT_COUNTS.md"
EXPECTED_SCENE = "VerdantValley_CliffPassage_SeparateCollisionDeck.blend"
ROOT_NAMES = ("VV_STRUCTURE", "VV_COLLISION", "VV_PROPS_SOLID", "VV_PROPS_NONSOLID")

if Path(bpy.data.filepath).name != EXPECTED_SCENE:
    raise RuntimeError(f"Open {EXPECTED_SCENE} first: {bpy.data.filepath}")
if set(bpy.data.collections) and bpy.data.collections.get("VV_COLLISION"):
    raise RuntimeError("VV_COLLISION already exists; refusing a second import")

structure = bpy.data.collections.get("VerdantValley_Structure")
if structure is None or len(structure.objects) != 30:
    raise RuntimeError("Expected the original 30 joined visual chunks")
structure.name = "VV_STRUCTURE"
collision = bpy.data.collections.new("VV_COLLISION")
bpy.context.scene.collection.children.link(collision)
for name in ROOT_NAMES[2:]:
    bpy.context.scene.collection.children.link(bpy.data.collections.new(name))

rows = []
for line in COUNTS.read_text(encoding="utf-8").splitlines():
    if not line.startswith("| chunk_"):
        continue
    cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
    rows.append((cells[0], int(cells[2]), cells[3]))
if len(rows) != 28:
    raise RuntimeError(f"Expected 28 kit entries, got {len(rows)}")

sources = []
for chunk, count, model in rows:
    stem = chunk.removeprefix("chunk_")
    sources.append((EXPORT / "walk_collision_kit" / f"{stem}_walk_collision.fbx", count, model, 0.0, chunk))
sources.extend((
    (EXPORT / "stone_sentinels_walk_collision_merged.fbx", 118,
     "VV_STONE_SENTINELS_COLLISION_MERGED", 0.30, "chunk_stone_sentinels"),
    (EXPORT / "cliff_passage_collision/path_cliff_passage_walk_collision.fbx", 66,
     "VV_PATH_CLIFF_PASSAGE_COLLISION_MERGED", 0.0, "chunk_path_cliff_passage"),
))

report = []
for path, expected, model, lift, chunk in sources:
    if not path.is_file():
        raise RuntimeError(f"Missing finalized collision FBX: {path}")
    visual = structure.objects.get(chunk)
    if visual is None:
        raise RuntimeError(f"Missing visual chunk for {model}: {chunk}")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), axis_forward="-Z", axis_up="Y")
    imported = [obj for obj in bpy.data.objects if obj not in before]
    markers = [obj for obj in imported if obj.name.startswith("CollisionOrigin")]
    pieces = [obj for obj in imported if obj.type == "MESH" and obj not in markers]
    if len(markers) != 1 or len(pieces) != expected:
        raise RuntimeError(f"{model}: {len(pieces)} pieces, {len(markers)} markers; expected {expected}, 1")
    group = bpy.data.collections.new(model)
    collision.children.link(group)
    for obj in pieces:
        for parent in tuple(obj.users_collection):
            parent.objects.unlink(obj)
        group.objects.link(obj)
        # Studio raised the merged Stone template 0.30 stud without changing its meshes.
        obj.location.z += lift
        obj.matrix_world = visual.matrix_world @ obj.matrix_world
        obj.display_type = "WIRE"
        obj.hide_render = True
        obj["collision_source_fbx"] = str(path.relative_to(REPO)).replace("\\", "/")
        obj["studio_z_adjustment_studs"] = lift
    for marker in markers:
        bpy.data.objects.remove(marker, do_unlink=True)
    report.append({"model": model, "visual_chunk": chunk, "pieces": len(pieces), "fbx": str(path.relative_to(REPO)).replace("\\", "/"), "studio_z_adjustment_studs": lift})
    print("IMPORTED", model, len(pieces), flush=True)

roots = {item.name for item in bpy.context.scene.collection.children}
if roots != set(ROOT_NAMES) or len(collision.all_objects) != 4032:
    raise RuntimeError(f"Unexpected collection state: roots={roots}, collision={len(collision.all_objects)}")
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("VV_SCENE_REPORT", json.dumps({"roots": sorted(roots), "visual_chunks": len(structure.objects), "collision_models": len(report), "collision_pieces": len(collision.all_objects), "models": report}), flush=True)
