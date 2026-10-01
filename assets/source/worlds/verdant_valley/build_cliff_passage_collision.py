"""Export Cliff Passage's terrain floor and two broad boundary walls.

Run in background Blender with the owner's current saved Verdant Valley scene.
Only chunk_path_cliff_passage is read. The joined visual loses physical collision
when ChunkLoader finds this template, replacing the embedded old deck collider.
"""

import bmesh
import bpy
import hashlib
import json
import os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(REPO, "assets/export/worlds/verdant_valley/cliff_passage_collision")
SHELL = 0.05
TILE = 16
STEP = 4
MIN_UP = 0.35
MAX_EDGE_RISE = 4.0
FLOOR_Y = 32
SAMPLE_Y = 28  # Repeat the edge height under each cliff face.
WALL_Y = 30
WALL_THICKNESS = 4
WALL_BOTTOM = -8
WALL_TOP = 52


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
        raise RuntimeError("Cliff Passage terrain body is missing")
    # The old deck remains part of the visible joined mesh. Read its path
    # surface to match what players see, but do not export it as a collider.
    deck = next((component for component in components
                 if 100 <= len(component) <= 200
                 and all(source.data.materials[face.material_index].name == "VV_Path"
                         for face in component)
                 and max(vertex.co.x for face in component for vertex in face.verts) >= 127), None)
    if deck is None:
        raise RuntimeError("Cliff Passage visible path deck is missing")
    deck_bm = bmesh.new()
    deck_bm.from_mesh(source.data)
    deck_indices = {face.index for face in deck}
    bmesh.ops.delete(deck_bm,
                     geom=[face for face in deck_bm.faces if face.index not in deck_indices],
                     context="FACES")
    deck_bm.normal_update()
    bmesh.ops.delete(bm, geom=[face for face in bm.faces if face not in terrain], context="FACES")
    bm.normal_update()
    return bm, BVHTree.FromBMesh(bm), deck_bm, BVHTree.FromBMesh(deck_bm), len(components) - 2


def closed_mesh(name, top, triangles):
    count = len(top)
    vertices = top + [(x, y, z - SHELL) for x, y, z in top]
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
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    check = bmesh.new()
    check.from_mesh(mesh)
    if any(not edge.is_manifold for edge in check.edges):
        raise RuntimeError(f"Non-manifold collider: {name}")
    check.free()
    return mesh


def wall_mesh(name, y):
    low_y, high_y = y - WALL_THICKNESS / 2, y + WALL_THICKNESS / 2
    vertices = [(x, yy, z) for z in (WALL_BOTTOM, WALL_TOP)
                for yy in (low_y, high_y) for x in (-128, 128)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], [
        (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
        (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3),
    ])
    mesh.update()
    return mesh


def main():
    if not bpy.data.filepath:
        raise SystemExit("Open the current saved Verdant Valley scene first")
    source = bpy.data.objects["chunk_path_cliff_passage"]
    bm, bvh, deck_bm, deck_bvh, detached = terrain_bvh(source)
    collection = bpy.data.collections.new("CliffPassageCollisionExport")
    bpy.context.scene.collection.children.link(collection)
    pieces = []

    def height(x, y):
        sample_y = max(-SAMPLE_Y, min(SAMPLE_Y, y))
        origin = Vector((max(-127.99, min(127.99, x)), sample_y, 100))
        while origin.z > -60:
            hit, normal, _, _ = bvh.ray_cast(origin, Vector((0, 0, -1)))
            if hit is None:
                return None
            if normal.z >= MIN_UP:
                z = hit.z
                if abs(sample_y) <= 28:
                    deck_hit, deck_normal, _, _ = deck_bvh.ray_cast(
                        Vector((origin.x, sample_y, 100)), Vector((0, 0, -1)))
                    if deck_hit is not None and deck_normal.z >= MIN_UP:
                        blend = min(1.0, max(0.0, (28 - abs(sample_y)) / 4))
                        z = max(z, z + (deck_hit.z - z) * blend)
                return z - SHELL
            origin.z = hit.z - 0.02
        return None

    incomplete = []
    for ty in range(-FLOOR_Y, FLOOR_Y, TILE):
        for tx in range(-128, 128, TILE):
            count = TILE // STEP + 1
            coordinates = [(tx + ix * STEP, ty + iy * STEP)
                           for iy in range(count) for ix in range(count)]
            heights = [height(x, y) for x, y in coordinates]
            triangles = []
            for iy in range(count - 1):
                for ix in range(count - 1):
                    a = iy * count + ix
                    for triangle in ((a, a + 1, a + count + 1),
                                     (a, a + count + 1, a + count)):
                        values = [heights[index] for index in triangle]
                        if all(value is not None for value in values) and max(values) - min(values) <= MAX_EDGE_RISE:
                            triangles.append(triangle)
            if len(triangles) != 2 * (count - 1) ** 2:
                incomplete.append((tx, ty, len(triangles)))
            if not triangles:
                continue
            used = sorted({index for triangle in triangles for index in triangle})
            mapping = {old: new for new, old in enumerate(used)}
            top = [(coordinates[i][0], coordinates[i][1], heights[i]) for i in used]
            name = f"walk_{tx:+04d}_{ty:+04d}"
            mesh = closed_mesh(name, top,
                               [tuple(mapping[i] for i in triangle) for triangle in triangles])
            obj = bpy.data.objects.new(name, mesh)
            collection.objects.link(obj)
            pieces.append(obj)
    if incomplete:
        raise RuntimeError(f"Cliff Passage floor has incomplete tiles: {incomplete}")
    for side, y in (("left", -WALL_Y), ("right", WALL_Y)):
        name = f"barrier_{side}"
        obj = bpy.data.objects.new(name, wall_mesh(name, y))
        collection.objects.link(obj)
        pieces.append(obj)

    bpy.ops.mesh.primitive_cube_add(size=0.25, location=(0, 0, 0))
    marker = bpy.context.object
    marker.name = "CollisionOrigin"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in pieces + [marker]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    os.makedirs(OUT, exist_ok=True)
    fbx = os.path.join(OUT, "path_cliff_passage_walk_collision.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
    )
    with open(bpy.data.filepath, "rb") as stream:
        source_hash = hashlib.sha256(stream.read()).hexdigest()
    report = {
        "source": bpy.data.filepath, "source_sha256": source_hash,
        "chunk": source.name, "model": "VV_PATH_CLIFF_PASSAGE_COLLISION_MERGED",
        "floor_tiles": len(pieces) - 2, "barriers": 2,
        "parts_after_marker_removal": len(pieces),
        "floor_bounds_xy": [-128, 128, -FLOOR_Y, FLOOR_Y],
        "barrier_centres_y": [-WALL_Y, WALL_Y],
        "barrier_height": [WALL_BOTTOM, WALL_TOP],
        "detached_visual_components_excluded": detached,
        "fbx": os.path.relpath(fbx, REPO).replace("\\", "/"),
    }
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print("CLIFF_COLLISION", json.dumps(report), flush=True)
    bm.free()
    deck_bm.free()


if __name__ == "__main__":
    main()
