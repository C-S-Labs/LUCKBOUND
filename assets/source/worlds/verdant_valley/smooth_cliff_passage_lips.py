"""Soften only Cliff Passage's two grass crest lines in the saved scene.

The joined visual mesh and all other chunk objects remain in place. This edits
the existing mesh vertices, saves the current scene, and exports one replacement
Cliff Passage visual FBX for manual Studio import.
"""

import bpy
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(REPO, "assets/export/worlds/verdant_valley/cliff_passage_collision")


def main():
    if not bpy.data.filepath:
        raise SystemExit("Open the current saved Verdant Valley scene first")
    obj = bpy.data.objects["chunk_path_cliff_passage"]
    mesh = obj.data
    points = [vertex.co.copy() for vertex in mesh.vertices]
    eligible = set()
    for polygon in mesh.polygons:
        material = mesh.materials[polygon.material_index].name
        if material in {"VV_Grass", "VV_GrassLight"}:
            eligible.update(polygon.vertices)
    chosen = [index for index in eligible
              if abs(points[index].x) <= 86
              and 36 <= abs(points[index].y) <= 58
              and points[index].z >= 15]
    changes = []
    for index in chosen:
        point = points[index]
        side = 1 if point.y > 0 else -1
        neighbors = [(other, math.exp(-((point.x - other.x) / 10) ** 2))
                     for candidate in chosen for other in [points[candidate]]
                     if candidate != index and other.y * side > 0
                     and abs(point.x - other.x) <= 14
                     and abs(point.y - other.y) <= 7
                     and abs(point.z - other.z) <= 8]
        if len(neighbors) < 2:
            continue
        weight = sum(w for _, w in neighbors)
        target_y = sum(other.y * w for other, w in neighbors) / weight
        target_z = sum(other.z * w for other, w in neighbors) / weight
        dy = max(-1.5, min(1.5, (target_y - point.y) * 0.55))
        dz = max(-0.8, min(0.8, (target_z - point.z) * 0.35))
        if abs(dy) + abs(dz) >= 0.01:
            changes.append((index, dy, dz))
    if len(changes) < 20:
        raise RuntimeError(f"Expected a visible crest on both sides; only {len(changes)} vertices changed")
    for index, dy, dz in changes:
        mesh.vertices[index].co.y += dy
        mesh.vertices[index].co.z += dz
    mesh.update()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    # The review scene lays chunks out on a grid; kit meshes export at origin.
    obj.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    os.makedirs(OUT, exist_ok=True)
    fbx = os.path.join(OUT, "path_cliff_passage_visual.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
    )
    print("CLIFF_LIP", json.dumps({
        "changed_vertices": len(changes),
        "max_horizontal_shift": max(abs(dy) for _, dy, _ in changes),
        "max_vertical_shift": max(abs(dz) for _, _, dz in changes),
        "scene": bpy.data.filepath, "fbx": fbx,
    }), flush=True)


if __name__ == "__main__":
    main()
