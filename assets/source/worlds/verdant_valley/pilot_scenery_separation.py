"""Separate three representative Verdant Valley chunks in the saved Blender scene.

Classification uses connected geometry, materials, dimensions and height. Run
only on the owner's current four-collection scene; collision is never touched.
"""

import bmesh
import bpy
import json
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCENE = "VerdantValley_CliffPassage_SeparateCollisionDeck.blend"
PILOT = ("chunk_wetland_pools", "chunk_cutbank_ford", "chunk_mushroom_glen")
if Path(bpy.data.filepath).name != SCENE:
    raise RuntimeError(f"Open {SCENE} first")
structure = bpy.data.collections["VV_STRUCTURE"]
solid = bpy.data.collections["VV_PROPS_SOLID"]
nonsolid = bpy.data.collections["VV_PROPS_NONSOLID"]
collision = bpy.data.collections["VV_COLLISION"]
if len(collision.all_objects) != 4032:
    raise RuntimeError("Unexpected collision collection state")
for name in PILOT:
    if structure.objects.get(name) is None:
        raise RuntimeError(f"Missing joined pilot chunk: {name}")
    if any(obj.name.startswith(name + "__") for obj in bpy.data.objects):
        raise RuntimeError(f"Pilot already separated: {name}")


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
        coords = [mesh.vertices[i].co for i in indices]
        low = tuple(min(co[axis] for co in coords) for axis in range(3))
        high = tuple(max(co[axis] for co in coords) for axis in range(3))
        rows.append({"indices": indices, "materials": dict(materials[key]), "low": low,
                     "high": high, "vertices": len(indices), "root": key})
    return rows


def classify(chunk, row, base):
    mats = set(row["materials"])
    size = tuple(row["high"][axis] - row["low"][axis] for axis in range(3))
    center_z = (row["low"][2] + row["high"][2]) / 2
    if row is base:
        return "structure", "terrain", "full footprint ground body"
    if (chunk == "chunk_wetland_pools" and
            mats == {"VV_Earth", "VV_Grass", "VV_GrassLight", "VV_Rock"} and
            size[0] > 40 and size[1] > 40 and size[2] < 10):
        return "structure", "island", "broad grass/earth/rock ground island"
    if mats == {"VV_Water"}:
        return "nonsolid", "water", "water material on a broad shallow surface"
    if mats == {"VV_DetailFoam"}:
        return "nonsolid", "water_foam", "foam detail beside wetland water"
    if mats == {"VV_GrassLight"} and size[0] < 7 and size[1] < 7 and size[2] < 10:
        kind = "grass_tuft" if max(size[0], size[1]) < 4 else "grass_clump"
        return "nonsolid", kind, "detached upright grass detail"
    if mats == {"VV_Bark"} and size[0] < 7 and size[1] < 7 and size[2] > 8:
        return "solid", "tree_trunk", "tall narrow bark body below foliage"
    if mats == {"VV_Bark"} and max(size[0], size[1]) > 10 and size[2] < 5:
        return "solid", "woody_piece", "substantial low horizontal bark body"
    if mats in ({"VV_Leaf"}, {"VV_LeafLight"}) and center_z > 8:
        return "nonsolid", "tree_canopy", "elevated foliage near tree trunks"
    if mats == {"VV_LeafLight"} and center_z <= 8 and size[2] < 8:
        return "nonsolid", "bush", "low foliage without a trunk at its center"
    if mats in ({"VV_Rock"}, {"VV_RockLight"}) and max(size[0], size[1]) < 25:
        return "solid", "rock", "detached compact rock body"
    if all(mat.startswith("VVBridge_") for mat in mats) and max(size) < 100:
        return "solid", "bridge_piece", "detached shaped timber in bridge span"
    if len(mats) == 1 and next(iter(mats)).startswith("VVFix_MushroomStem"):
        return "solid", "mushroom_stem", "upright mushroom stem material and shape"
    if len(mats) == 1 and next(iter(mats)).startswith("VVFix_MushroomCap"):
        return "solid", "mushroom_cap", "mushroom cap material and broad cap shape"
    return "structure", "unclassified", "materials/shape do not identify terrain or prop confidently"


def subset(original, indices, name, collection):
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = name
    collection.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    remove = [bm.verts[i] for i in range(len(original.data.vertices)) if i not in indices]
    bmesh.ops.delete(bm, geom=remove, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


report = {"source_scene": bpy.data.filepath, "pilot_chunks": list(PILOT), "chunks": {}, "ambiguities": []}
for name in PILOT:
    original = structure.objects[name]
    mesh = original.data
    parts = components(mesh)
    base = max(parts, key=lambda row: row["vertices"])
    labeled = []
    for row in parts:
        category, kind, reason = classify(name, row, base)
        labeled.append((row, category, kind, reason))
    # Spatial order makes names deterministic without using Blender's .001 suffixes.
    labeled.sort(key=lambda item: (item[2],
                round((item[0]["low"][0] + item[0]["high"][0]) / 2, 5),
                round((item[0]["low"][1] + item[0]["high"][1]) / 2, 5),
                round((item[0]["low"][2] + item[0]["high"][2]) / 2, 5),
                item[0]["root"]))
    serial = Counter()
    outputs = []
    counts = Counter()
    for row, category, kind, reason in labeled:
        serial[kind] += 1
        final_name = name if row is base else f"{name}__{kind}_{serial[kind]:02d}"
        target = {"structure": structure, "solid": solid, "nonsolid": nonsolid}[category]
        obj = subset(original, row["indices"], f"__pilot_work_{name}_{len(outputs):03d}", target)
        outputs.append((obj, final_name, row, category, kind, reason))
        counts[category] += 1
        if kind == "unclassified":
            size = [round(row["high"][axis] - row["low"][axis], 2) for axis in range(3)]
            report["ambiguities"].append({"chunk": name, "object": final_name,
                                          "materials": row["materials"], "dimensions": size,
                                          "reason": reason})
    for field in ("vertices", "edges", "polygons", "loops"):
        before = len(getattr(mesh, field))
        after = sum(len(getattr(obj.data, field)) for obj, *_ in outputs)
        if before != after:
            raise RuntimeError(f"{name}: {field} changed {before} -> {after}")
    for obj, *_ in outputs:
        if (list(obj.data.uv_layers.keys()) != list(mesh.uv_layers.keys()) or
                list(obj.data.color_attributes.keys()) != list(mesh.color_attributes.keys()) or
                obj.matrix_world != original.matrix_world):
            raise RuntimeError(f"{name}: attributes or transform changed on {obj.name}")
    bpy.data.objects.remove(original, do_unlink=True)
    for obj, final_name, *_ in outputs:
        if bpy.data.objects.get(final_name):
            raise RuntimeError(f"Name collision: {final_name}")
        obj.name = final_name
    report["chunks"][name] = {"components": len(parts), "counts": dict(counts),
                              "types": dict(Counter(kind for _, _, _, _, kind, _ in outputs)),
                              "source_vertices": len(mesh.vertices), "source_faces": len(mesh.polygons)}
    print("PILOT_CHUNK", name, report["chunks"][name], flush=True)

if len(collision.all_objects) != 4032 or len(collision.children) != 30:
    raise RuntimeError("VV_COLLISION changed during separation")
out = HERE / "PILOT_SCENERY_CLASSIFICATION.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("PILOT_COMPLETE", str(out), len(report["ambiguities"]), flush=True)
