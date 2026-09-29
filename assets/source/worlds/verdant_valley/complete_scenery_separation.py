"""Classify the 27 still-joined Verdant Valley chunks in the current Blender scene.

The reviewed three-chunk pilot and VV_COLLISION are read-only. Pass --dry-run
after the Blender -- separator to inspect decisions without saving the scene.
"""

import bmesh
import bpy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCENE = "VerdantValley_CliffPassage_SeparateCollisionDeck.blend"
PILOT = {"chunk_wetland_pools", "chunk_cutbank_ford", "chunk_mushroom_glen"}
DRY_RUN = "--dry-run" in sys.argv
if Path(bpy.data.filepath).name != SCENE:
    raise RuntimeError(f"Open {SCENE} first")
structure = bpy.data.collections["VV_STRUCTURE"]
solid = bpy.data.collections["VV_PROPS_SOLID"]
nonsolid = bpy.data.collections["VV_PROPS_NONSOLID"]
collision = bpy.data.collections["VV_COLLISION"]
joined = sorted((obj for obj in structure.objects if obj.name.startswith("chunk_")
                 and "__" not in obj.name and obj.name not in PILOT), key=lambda obj: obj.name)
if len(joined) != 27 or len(collision.all_objects) != 4032:
    raise RuntimeError(f"Expected 27 joined chunks and 4,032 colliders; got {len(joined)}, {len(collision.all_objects)}")
collision_objects = set(collision.all_objects)
protected = {obj: (obj.name, obj.data, obj.matrix_world.copy(), tuple(obj.users_collection))
             for obj in bpy.data.objects if obj in collision_objects or
             any(obj.name == chunk or obj.name.startswith(chunk + "__") for chunk in PILOT)}


def components(mesh):
    parent = list(range(len(mesh.vertices)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in mesh.edges:
        a, b = edge.vertices
        parent[root(b)] = root(a)
    groups = defaultdict(set)
    for vertex in mesh.vertices:
        groups[root(vertex.index)].add(vertex.index)
    materials = defaultdict(Counter)
    for polygon in mesh.polygons:
        materials[root(polygon.vertices[0])][mesh.materials[polygon.material_index].name] += 1
    rows = []
    for key, indices in groups.items():
        coords = [mesh.vertices[index].co for index in indices]
        low = tuple(min(co[axis] for co in coords) for axis in range(3))
        high = tuple(max(co[axis] for co in coords) for axis in range(3))
        rows.append({"indices": indices, "materials": dict(materials[key]),
                     "low": low, "high": high, "vertices": len(indices), "root": key})
    return rows


def classify(chunk, row, base):
    mats = set(row["materials"])
    size = tuple(row["high"][axis] - row["low"][axis] for axis in range(3))
    center_z = (row["low"][2] + row["high"][2]) / 2
    if row is base:
        return "structure", "terrain", "largest connected ground body"
    if mats & {"VV_Path", "VV_Grass", "VV_Earth", "VV_CaveFloor"}:
        return "structure", "ground", "detached path/grass/earth ground surface"
    if mats == {"VV_Water"}:
        return "nonsolid", "water", "water material and broad shallow surface"
    if mats == {"VV_DetailFoam"}:
        return "nonsolid", "water_foam", "foam detail next to water"
    if mats == {"VV_GrassLight"}:
        if max(size[0], size[1]) <= 15 and size[2] <= 12:
            kind = "grass_tuft" if max(size[0], size[1]) < 4 else "grass_clump"
            return "nonsolid", kind, "detached light-grass foliage of tuft/clump size"
    if mats == {"VV_Bark"}:
        if size[2] >= 8 and size[2] > max(size[0], size[1]):
            return "solid", "tree_trunk", "upright bark body under canopy"
        if max(size[0], size[1]) >= 10:
            return "solid", "woody_piece", "substantial horizontal bark body"
        return "solid", "wood_piece", "detached bark geometry"
    if mats <= {"VV_Leaf", "VV_LeafLight", "VV_Blossom"} and mats:
        kind = "tree_canopy" if center_z > 8 else "bush"
        return "nonsolid", kind, "foliage material and height relative to ground"
    if mats <= {"VV_Flower", "VV_DetailBloom", "VV_DetailMoss"} and mats:
        kind = "moss_detail" if mats == {"VV_DetailMoss"} else "flower_detail"
        return "nonsolid", kind, "soft decorative vegetation with no supporting body"
    if mats == {"VV_DetailFungus"}:
        return "solid", "fungus", "detached mushroom/fungus body"
    if mats <= {"VV_RockFracture_0", "VV_RockFracture_1", "VV_RockFracture_2"} and mats:
        return "structure", "cliff", "fractured cliff geometry in pass/overlook"
    if chunk == "chunk_path_cliff_passage" and mats <= {"VV_Rock", "VV_RockLight"} and size[0] > 100:
        return "structure", "cliff", "long side cliff enclosing the passage"
    if mats <= {"VV_Rock", "VV_RockLight"} and mats:
        if min(size[0], size[1]) > 40 and size[2] > 20:
            return "structure", "unclassified", "large rock may be cliff or detached boulder"
        return "solid", "rock", "detached rock/boulder shape"
    if mats <= {"VV_Ruin", "VV_RockLight", "VV_Rock"} and "VV_Ruin" in mats:
        return "solid", "ruin_piece", "detached ruin masonry or structure"
    if all(mat.startswith("VVBridge_") for mat in mats) and mats:
        return "solid", "bridge_piece", "detached bridge timber"
    if mats == {"VV_CrystalBlue"}:
        return "solid", "crystal", "substantial detached crystal"
    if mats <= {"VV_RockLight", "VV_CaveStoneLight"} and "VV_CaveStoneLight" in mats:
        return "solid", "cave_rock", "compact detached cave stone/rock body"
    if mats == {"VV_CaveWoodDark"}:
        return "solid", "wood_piece", "detached cave wood"
    if mats == {"VV_CaveMetal"}:
        return "solid", "metal_piece", "detached cave metal fitting"
    if mats <= {"VV_CaveFlame", "VV_CaveFlameCore"} and mats:
        return "nonsolid", "flame", "visual flame geometry"
    if all(mat.startswith("VV_Cave") and ("Rock" in mat or "Stone" in mat) for mat in mats) and mats:
        if max(size[0], size[1]) > 30 and size[2] > 20:
            return "structure", "cave_structure", "large cave wall/arch body"
        return "solid", "cave_rock", "detached cave rock/stone body"
    return "structure", "unclassified", "material and shape do not establish gameplay solidity"


def subset(original, indices, name, collection):
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = name
    collection.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    remove = [bm.verts[index] for index in range(len(original.data.vertices)) if index not in indices]
    bmesh.ops.delete(bm, geom=remove, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


report = {"source_scene": bpy.data.filepath, "preserved_pilot_chunks": sorted(PILOT),
          "processed_chunks": [], "chunks": {}, "ambiguities": []}
prepared = []
for original in joined:
    name = original.name
    parts = components(original.data)
    base = max(parts, key=lambda row: row["vertices"])
    labeled = [(row, *classify(name, row, base)) for row in parts]
    labeled.sort(key=lambda item: (item[2],
                 round((item[0]["low"][0] + item[0]["high"][0]) / 2, 5),
                 round((item[0]["low"][1] + item[0]["high"][1]) / 2, 5),
                 round((item[0]["low"][2] + item[0]["high"][2]) / 2, 5),
                 item[0]["root"]))
    counts = Counter(category for _, category, _, _ in labeled)
    kinds = Counter(kind for _, _, kind, _ in labeled)
    report["processed_chunks"].append(name)
    report["chunks"][name] = {"components": len(parts), "counts": dict(counts),
                              "types": dict(kinds), "source_vertices": len(original.data.vertices),
                              "source_faces": len(original.data.polygons)}
    serial = Counter()
    assignments = []
    for row, category, kind, reason in labeled:
        serial[kind] += 1
        final_name = name if row is base else f"{name}__{kind}_{serial[kind]:02d}"
        if kind == "unclassified":
            dims = [round(row["high"][axis] - row["low"][axis], 2) for axis in range(3)]
            report["ambiguities"].append({"chunk": name, "object": final_name,
                                          "materials": row["materials"], "dimensions": dims,
                                          "reason": reason})
        assignments.append((row, category, final_name))
    if not DRY_RUN:
        outputs = []
        for row, category, final_name in assignments:
            target = {"structure": structure, "solid": solid, "nonsolid": nonsolid}[category]
            outputs.append((subset(original, row["indices"], f"__complete_work_{name}_{len(outputs):03d}", target), final_name))
        for field in ("vertices", "edges", "polygons", "loops"):
            before = len(getattr(original.data, field))
            after = sum(len(getattr(obj.data, field)) for obj, _ in outputs)
            if before != after:
                raise RuntimeError(f"{name}: {field} changed {before} -> {after}")
        for obj, _ in outputs:
            if (list(obj.data.uv_layers.keys()) != list(original.data.uv_layers.keys()) or
                    list(obj.data.color_attributes.keys()) != list(original.data.color_attributes.keys()) or
                    obj.matrix_world != original.matrix_world):
                raise RuntimeError(f"{name}: UV/color attributes or transform changed")
        prepared.append((original, outputs))
    print("CHUNK", name, len(parts), dict(counts), kinds.get("unclassified", 0), flush=True)

if not DRY_RUN:
    for original, outputs in prepared:
        bpy.data.objects.remove(original, do_unlink=True)
        for obj, final_name in outputs:
            if bpy.data.objects.get(final_name):
                raise RuntimeError(f"Name collision: {final_name}")
            obj.name = final_name
    for obj, (name, mesh, transform, collections) in protected.items():
        if (obj.name != name or obj.data is not mesh or obj.matrix_world != transform or
                tuple(obj.users_collection) != collections):
            raise RuntimeError(f"Protected pilot/collision object changed: {name}")
    report_path = HERE / "SCENERY_CLASSIFICATION_REMAINING.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print("COMPLETE_SCENE_SAVED", len(joined), len(report["ambiguities"]), str(report_path), flush=True)
else:
    print("CLASSIFICATION_PREVIEW", len(joined), sum(v["components"] for v in report["chunks"].values()),
          Counter(category for v in report["chunks"].values() for category, count in v["counts"].items() for _ in range(count)),
          "ambiguities", len(report["ambiguities"]), flush=True)
    print("AMBIGUITY_PREVIEW", json.dumps(report["ambiguities"][:40]), flush=True)
