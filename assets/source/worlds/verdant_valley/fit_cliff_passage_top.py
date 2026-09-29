"""Smooth Cliff Passage's grass crest and tuck low terrain behind the rock.

Run against the owner's current saved scene. The edit is restricted to the
existing Cliff Passage structure mesh; separated scenery and collision remain
unchanged. Exports only the revised visual chunk for Studio review.
"""

import bpy
import json
from pathlib import Path


SCENE = "VerdantValley_CliffPassage_SeparateCollisionDeck.blend"
CHUNK = "chunk_path_cliff_passage"
OUT = Path(__file__).resolve().parents[3] / "export/worlds/verdant_valley/cliff_passage_collision"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def main():
    if Path(bpy.data.filepath).name != SCENE:
        raise RuntimeError(f"Open {SCENE} first")
    obj = bpy.data.objects[CHUNK]
    mesh = obj.data
    grass = set()
    for face in mesh.polygons:
        if mesh.materials[face.material_index].name in {"VV_Grass", "VV_GrassLight"}:
            grass.update(face.vertices)

    original = {i: mesh.vertices[i].co.copy() for i in grass}
    crest = {}
    for side in (-1, 1):
        candidates = [(i, p) for i, p in original.items()
                      if p.y * side > 0 and abs(p.x) <= 75
                      and 39 <= abs(p.y) <= 59 and p.z >= 10]
        for index, point in original.items():
            if point.y * side <= 0 or abs(point.x) > 75:
                continue
            nearby = [(candidate, other) for candidate, other in candidates
                      if abs(other.x - point.x) <= 9]
            if not nearby:
                continue
            high = max(other.z for _, other in nearby)
            top = [(candidate, other) for candidate, other in nearby
                   if other.z >= high - 2.5]
            weights = [1 / (1 + ((other.x - point.x) / 5) ** 2)
                       for _, other in top]
            crest[index] = sum(other.z * weight for (_, other), weight in zip(top, weights)) / sum(weights)

    smoothed = []
    tucked = []
    for index, point in original.items():
        if index not in crest:
            continue
        x, y, z = point
        side = abs(y)
        if abs(x) > 72 or not 32 <= side <= 57:
            continue
        along = smoothstep((75 - abs(x)) / 12)
        top = crest[index]
        gap = top - z
        vertex = mesh.vertices[index]
        if 38 <= side <= 53 and -1.0 <= gap <= 3.0:
            blend = 0.72 * along * (1 - smoothstep((side - 48) / 5))
            dz = max(-2.0, min(2.0, (top - z) * blend))
            if abs(dz) > 0.02:
                vertex.co.z += dz
                smoothed.append((index, dz))
        elif 32 <= side < 50 and gap > 4.0 and z > 9:
            # The original terrain has long green triangular skirts dipping
            # through the wall. Retract their tips and bring them up to the
            # crest underside so the lip reads as one continuous band.
            target_side = max(side, 44.0)
            shift = (target_side - side) * along
            rise = (gap - 2.5) * along
            vertex.co.y += shift if y > 0 else -shift
            vertex.co.z += rise
            tucked.append((index, shift, rise))

    if len(smoothed) < 20:
        raise RuntimeError(f"Unexpected crest selection: {len(smoothed)} smoothed, {len(tucked)} tucked")
    rock_index = mesh.materials.find("VV_Rock")
    rock_faces = 0
    for face in mesh.polygons:
        material = mesh.materials[face.material_index].name
        if material not in {"VV_Grass", "VV_GrassLight"}:
            continue
        points = [mesh.vertices[i].co for i in face.vertices]
        center_x = sum(point.x for point in points) / len(points)
        center_side = abs(sum(point.y for point in points) / len(points))
        if abs(center_x) > 72 or not 31 < center_side < 52:
            continue
        nearby_top = [crest[i] for i in face.vertices if i in crest]
        if not nearby_top:
            continue
        top = max(nearby_top)
        low = min(point.z for point in points)
        high = max(point.z for point in points)
        if (low < top - 2.5 and high > top - 10) or (face.normal.z < 0.55 and high > top - 10):
            face.material_index = rock_index
            rock_faces += 1
    mesh.update()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

    # The review scene lays chunks out on a grid; the kit FBX uses its origin.
    obj.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    OUT.mkdir(parents=True, exist_ok=True)
    fbx = OUT / "path_cliff_passage_visual.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
    )
    print("CLIFF_TOP", json.dumps({"smoothed_vertices": len(smoothed),
        "tucked_vertices": len(tucked),
        "max_vertical_shift": max(abs(shift) for _, shift in smoothed),
        "max_outward_shift": max(shift for _, shift, _ in tucked),
        "max_tip_rise": max(rise for _, _, rise in tucked),
        "rock_skirt_faces": rock_faces,
        "scene": bpy.data.filepath, "fbx": str(fbx)}), flush=True)


if __name__ == "__main__":
    main()
