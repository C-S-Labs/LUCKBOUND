"""Generate adaptive walk-collider FBXs for the joined Verdant Valley kit.

Run with the current saved Blender scene open. Stone Sentinels and Cliff Passage
are deliberately excluded. This is an import package, not an uploaded Roblox
asset: Studio must assign MeshIds before the models can be activated.
"""

import bmesh
import bpy
import hashlib
import json
import os
import sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(REPO, "assets/export/worlds/verdant_valley/walk_collision_kit")
TILE = 16
STEP = 4
SHELL = 0.05
MAX_EDGE_RISE = 4.0
MIN_UP = 0.35
MAX_PLANE_RESIDUAL = 0.22
MAX_SLOPE_DELTA = 0.04
EXCLUDED = {"chunk_stone_sentinels", "chunk_path_cliff_passage"}
HALF_EXTENTS = {"chunk_boss_sanctuary": (192, 128)}
FERN_UNMERGED = {(x, y) for x in range(-32, 32, TILE) for y in range(-16, 16, TILE)}
NARROW_PASS_UNMERGED = {(x, y) for x in range(-16, 16, TILE) for y in range(64, 128, TILE)}
ENTRY_DAWN_UNMERGED = NARROW_PASS_UNMERGED
BLOSSOM_UNMERGED = {(x, y) for x in range(-128, -48, TILE) for y in range(-16, 16, TILE)}
TREASURE_UNMERGED = {(x, y) for x in range(-16, 16, TILE) for y in range(80, 128, TILE)}
HIGH_LEDGE_UNMERGED = {(x, y) for x in range(-128, -112, TILE) for y in range(-16, 16, TILE)}
SHADED_GROVE_UNMERGED = {(x, y) for x in range(96, 128, TILE) for y in range(-16, 16, TILE)}
FORGOTTEN_TRIAL_UNMERGED = (
    {(x, y) for x in range(-16, 16, TILE) for y in range(32, 128, TILE)}
    | {(x, y) for x in range(-64, 64, TILE) for y in range(-48, 32, TILE)}
)
BOSS_SANCTUARY_UNMERGED = (
    {(x, y) for x in range(-32, 64, TILE) for y in range(16, 96, TILE)}
    | {(x, y) for x in range(-80, 80, TILE) for y in range(-48, 16, TILE)}
)
FORCED_UNMERGED = {
    "chunk_fern_hollow": FERN_UNMERGED,
    "chunk_path_narrow_pass": NARROW_PASS_UNMERGED,
    "chunk_entry_dawn_meadow": ENTRY_DAWN_UNMERGED,
    "chunk_boss_sanctuary": BOSS_SANCTUARY_UNMERGED,
    "chunk_blossom_terrace": BLOSSOM_UNMERGED,
    "chunk_side_treasure_hollow": TREASURE_UNMERGED,
    "chunk_high_ledge_gate": HIGH_LEDGE_UNMERGED,
    "chunk_path_crossroads_copse": NARROW_PASS_UNMERGED,
    "chunk_path_split_meadow": NARROW_PASS_UNMERGED,
    "chunk_shaded_grove": SHADED_GROVE_UNMERGED,
    "chunk_side_forgotten_trial": FORGOTTEN_TRIAL_UNMERGED,
}
FINE_TILES = {
    "chunk_path_narrow_pass": {(0, 112)},
    "chunk_entry_dawn_meadow": {(-16, 112)},
    "chunk_boss_sanctuary": {(48, 48)},
    "chunk_side_treasure_hollow": {(0, 112)},
    "chunk_path_crossroads_copse": {(-16, 112), (0, 112)},
    "chunk_path_split_meadow": {(-16, 112)},
    "chunk_side_forgotten_trial": {(-16, 32), (0, 32), (-16, 48), (-64, -32), (-64, 16)},
}
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None


def terrain_bvh(source):
    bm = bmesh.new()
    bm.from_mesh(source.data)
    seen = set()
    components = []
    for face in bm.faces:
        if face in seen:
            continue
        stack = [face]
        seen.add(face)
        component = set()
        while stack:
            current = stack.pop()
            component.add(current)
            for edge in current.edges:
                for neighbor in edge.link_faces:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
        components.append(component)
    terrain = max(components, key=len)
    if len(terrain) < 1000:
        raise RuntimeError(f"{source.name}: no convincing connected terrain body")
    bmesh.ops.delete(bm, geom=[face for face in bm.faces if face not in terrain], context="FACES")
    bm.normal_update()
    return bm, BVHTree.FromBMesh(bm), len(terrain), len(components) - 1


def closed_mesh(name, top, triangles):
    count = len(top)
    verts = top + [(x, y, z - SHELL) for x, y, z in top]
    faces = []
    edges = {}
    for a, b, c in triangles:
        faces.extend(((a, b, c), (c + count, b + count, a + count)))
        for edge in ((a, b), (b, c), (c, a)):
            key = tuple(sorted(edge))
            edges[key] = edges.get(key, 0) + 1
    for (a, b), frequency in edges.items():
        if frequency == 1:
            faces.append((a, a + count, b + count, b))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    check = bmesh.new()
    check.from_mesh(mesh)
    if any(not edge.is_manifold for edge in check.edges):
        raise RuntimeError(f"Non-manifold collider: {name}")
    check.free()
    return mesh


def generate(source, source_hash):
    bm, bvh, terrain_faces, detached = terrain_bvh(source)
    half_x, half_y = HALF_EXTENTS.get(source.name, (128, 128))
    x_tiles = range(-half_x, half_x, TILE)
    y_tiles = range(-half_y, half_y, TILE)

    def height(x, y):
        origin = Vector((max(-half_x + 0.01, min(half_x - 0.01, x)),
                         max(-half_y + 0.01, min(half_y - 0.01, y)), 100))
        while origin.z > -60:
            hit, normal, _, _ = bvh.ray_cast(origin, Vector((0, 0, -1)))
            if hit is None:
                return None
            if normal.z >= MIN_UP:
                return hit.z
            origin.z = hit.z - 0.02
        return None

    collection = bpy.data.collections.new(f"WalkCollision_{source.name}")
    bpy.context.scene.collection.children.link(collection)
    pieces = []
    records = {}
    grid = {}
    side_x, side_y = 2 * half_x // TILE, 2 * half_y // TILE
    for ty in y_tiles:
        for tx in x_tiles:
            count = TILE // STEP + 1
            coords = [(tx + ix * STEP, ty + iy * STEP)
                      for iy in range(count) for ix in range(count)]
            heights = [height(x, y) for x, y in coords]
            grid.update(zip(coords, heights))
            triangles = []
            for iy in range(count - 1):
                for ix in range(count - 1):
                    a = iy * count + ix
                    b, c, d = a + 1, a + count, a + count + 1
                    for triangle in ((a, b, d), (a, d, c)):
                        values = [heights[index] for index in triangle]
                        if all(value is not None for value in values) and max(values) - min(values) <= MAX_EDGE_RISE:
                            triangles.append(triangle)
            if not triangles:
                continue
            if (tx, ty) in FINE_TILES.get(source.name, set()):
                for iy in range(TILE // STEP):
                    for ix in range(TILE // STEP):
                        a = iy * count + ix
                        corners = (a, a + 1, a + count + 1, a + count)
                        values = [heights[index] for index in corners]
                        if any(value is None for value in values) or max(values) - min(values) > MAX_EDGE_RISE:
                            continue
                        top = [(coords[index][0], coords[index][1], heights[index] - SHELL)
                               for index in corners]
                        name = f"walk_fine_{tx:+04d}_{ty:+04d}_{ix}_{iy}"
                        mesh = closed_mesh(name, top, ((0, 1, 2), (0, 2, 3)))
                        obj = bpy.data.objects.new(name, mesh)
                        collection.objects.link(obj)
                        pieces.append(obj)
                continue
            used = sorted({index for triangle in triangles for index in triangle})
            index = {old: new for new, old in enumerate(used)}
            top = [(coords[i][0], coords[i][1], heights[i] - SHELL) for i in used]
            mesh = closed_mesh(f"walk_{tx}_{ty}", top,
                               [tuple(index[i] for i in triangle) for triangle in triangles])
            obj = bpy.data.objects.new(f"walk_{tx:+04d}_{ty:+04d}", mesh)
            collection.objects.link(obj)
            pieces.append(obj)
            records[(tx, ty)] = {"object": obj, "full": len(triangles) == 2 * (count - 1) ** 2}
    if not pieces:
        raise RuntimeError(f"{source.name}: no collision cells")
    initial_count = len(pieces)

    forced_unmerged = FORCED_UNMERGED.get(source.name, set())
    full = np.array([[bool(records.get((x, y), {}).get("full")) and (x, y) not in forced_unmerged
                      for x in x_tiles]
                     for y in y_tiles], dtype=np.int32)
    prefix = np.pad(full.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def full_count(ix, iy, width, depth):
        x1, y1 = ix + width, iy + depth
        return int(prefix[y1, x1] - prefix[iy, x1] - prefix[y1, ix] + prefix[iy, ix])

    def plane_fit(coords):
        xy = np.asarray(coords, dtype=np.float64)
        z = np.asarray([grid[point] for point in coords], dtype=np.float64)
        matrix = np.column_stack((xy[:, 0], xy[:, 1], np.ones(len(xy))))
        coeff = np.linalg.lstsq(matrix, z, rcond=None)[0]
        return coeff, float(np.max(np.abs(matrix @ coeff - z)))

    slopes = {}
    for (tx, ty), record in records.items():
        if record["full"]:
            coords = [(x, y) for y in range(ty, ty + TILE + 1, STEP)
                      for x in range(tx, tx + TILE + 1, STEP)]
            slopes[(tx, ty)] = plane_fit(coords)[0][:2]
    candidates = []
    for iy in range(side_y):
        for ix in range(side_x):
            if not full[iy, ix]:
                continue
            for depth in range(1, side_y - iy + 1):
                for width in range(1, side_x - ix + 1):
                    area = width * depth
                    if area < 2 or full_count(ix, iy, width, depth) != area:
                        continue
                    tx, ty = -half_x + ix * TILE, -half_y + iy * TILE
                    coords = [(x, y) for y in range(ty, ty + depth * TILE + 1, STEP)
                              for x in range(tx, tx + width * TILE + 1, STEP)]
                    coeff, residual = plane_fit(coords)
                    if residual > MAX_PLANE_RESIDUAL:
                        continue
                    cells = [(tx + dx * TILE, ty + dy * TILE)
                             for dy in range(depth) for dx in range(width)]
                    if max(float(np.linalg.norm(slopes[cell] - coeff[:2])) for cell in cells) > MAX_SLOPE_DELTA:
                        continue
                    candidates.append((area, max(width, depth), -residual, tx, ty, width, depth, cells))

    occupied = set()
    merged_regions = 0
    for _, _, _, tx, ty, width, depth, cells in sorted(candidates, reverse=True):
        if any(cell in occupied for cell in cells):
            continue
        occupied.update(cells)
        for cell in cells:
            obj = records[cell]["object"]
            pieces.remove(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
        nx, ny = width * TILE // STEP + 1, depth * TILE // STEP + 1
        coords = [(tx + ix * STEP, ty + iy * STEP)
                  for iy in range(ny) for ix in range(nx)]
        top = [(x, y, grid[(x, y)] - SHELL) for x, y in coords]
        triangles = []
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                a = iy * nx + ix
                triangles.extend(((a, a + 1, a + nx + 1), (a, a + nx + 1, a + nx)))
        mesh = closed_mesh(f"walk_patch_{tx}_{ty}", top, triangles)
        obj = bpy.data.objects.new(f"walk_patch_{tx:+04d}_{ty:+04d}_{width}x{depth}", mesh)
        collection.objects.link(obj)
        pieces.append(obj)
        merged_regions += 1

    bpy.ops.mesh.primitive_cube_add(size=0.25, location=(0, 0, 0))
    marker = bpy.context.object
    marker.name = "CollisionOrigin"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in pieces:
        obj.select_set(True)
    marker.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    stem = source.name.removeprefix("chunk_")
    suffix = "_targeted" if ONLY else ""
    fbx = os.path.join(OUT, f"{stem}_walk_collision{suffix}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
    )
    model_stem = {"side_treasure_hollow": "CAP_TREASURE_HOLLOW",
                  "side_wardens_clearing": "CAP_WARDENS_CLEARING"}.get(stem, stem.upper())
    covered_x = [vertex.co.x for obj in pieces for vertex in obj.data.vertices]
    covered_y = [vertex.co.y for obj in pieces for vertex in obj.data.vertices]
    report = {"chunk": source.name, "model": f"VV_{model_stem}_COLLISION_MERGED",
              "source_sha256": source_hash,
              "half_extents_studs": [half_x, half_y],
              "covered_bounds_xy": [min(covered_x), max(covered_x), min(covered_y), max(covered_y)],
              "surface_offset_studs": SHELL, "forced_unmerged_tiles": len(forced_unmerged),
              "terrain_faces": terrain_faces, "detached_components_excluded": detached,
              "initial_cells": initial_count, "merged_colliders": len(pieces),
              "merged_regions": merged_regions, "fbx": os.path.relpath(fbx, REPO).replace("\\", "/")}
    for obj in pieces:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.objects.remove(marker, do_unlink=True)
    bpy.data.collections.remove(collection)
    bm.free()
    return report


def main():
    if not bpy.data.filepath:
        raise SystemExit("Open the current saved Verdant Valley scene first")
    with open(bpy.data.filepath, "rb") as stream:
        source_hash = hashlib.sha256(stream.read()).hexdigest()
    chunks = sorted((obj for obj in bpy.data.objects
                     if obj.type == "MESH" and obj.name.startswith("chunk_") and obj.name not in EXCLUDED),
                    key=lambda obj: obj.name)
    if ONLY:
        chunks = [obj for obj in chunks if obj.name == ONLY]
        if len(chunks) != 1:
            raise SystemExit(f"Included chunk not found: {ONLY}")
    elif len(chunks) != 28:
        raise SystemExit(f"Expected 28 included chunks; found {len(chunks)}")
    os.makedirs(OUT, exist_ok=True)
    reports = []
    for chunk in chunks:
        report = generate(chunk, source_hash)
        reports.append(report)
        print("COLLISION_CHUNK", json.dumps(report), flush=True)
    if ONLY:
        with open(os.path.join(OUT, f"{ONLY.removeprefix('chunk_')}_targeted_report.json"), "w", encoding="utf-8") as stream:
            json.dump(reports[0], stream, indent=2)
        return
    try:
        source_path = os.path.relpath(bpy.data.filepath, REPO).replace("\\", "/")
    except ValueError:
        source_path = bpy.data.filepath
    result = {"source": source_path,
              "source_sha256": source_hash, "excluded": sorted(EXCLUDED),
              "chunks": reports, "generated_colliders": sum(item["merged_colliders"] for item in reports)}
    with open(os.path.join(OUT, "kit_report.json"), "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    lines = ["# Verdant Valley adaptive walk collision", "",
             f"Source: `{result['source']}` (`{source_hash}`)", "",
             "| Chunk | Initial cells | Merged colliders | Studio model |",
             "|---|---:|---:|---|"]
    for item in sorted(reports, key=lambda entry: entry["chunk"]):
        lines.append(f"| {item['chunk']} | {item['initial_cells']} | {item['merged_colliders']} | `{item['model']}` |")
    lines += [f"| **28 generated chunks** | **{sum(item['initial_cells'] for item in reports)}** | **{result['generated_colliders']}** | |",
              "", "Stone Sentinels stays at 202 initial cells and 118 merged colliders.",
              "Cliff Passage retains its existing joined visual collision and was not generated.",
              f"Kit total after Studio import: {result['generated_colliders'] + 118 + 1} collider parts "
              "(28 generated chunks + Stone Sentinels + Cliff Passage's existing one visual MeshPart).",
              ""]
    with open(os.path.join(OUT, "KIT_COUNTS.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print("COLLISION_KIT", json.dumps({"chunks": len(reports), "colliders": result["generated_colliders"]}), flush=True)


if __name__ == "__main__":
    main()
