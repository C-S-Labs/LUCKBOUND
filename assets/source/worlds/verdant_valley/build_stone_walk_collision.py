"""Build a segmented Stone Sentinels walk collider from the reviewed scene.

Run in background Blender with verdant_valley_30_cleanup_review.blend open.
The source file is read only; output is an FBX and a height-check report.
"""

import bmesh
import bpy
import hashlib
import json
import os
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(REPO, "assets/export/worlds/verdant_valley")
SOURCE_NAME = "verdant_valley_30_cleanup_review.blend"
CHUNK = "chunk_stone_sentinels"
TILE = 16
STEP = 4
SHELL = 0.35
MAX_EDGE_RISE = 4.0
MIN_UP = 0.35

if os.path.basename(bpy.data.filepath) != SOURCE_NAME:
    raise SystemExit(f"Open {SOURCE_NAME}; got {bpy.data.filepath}")
source = bpy.data.objects[CHUNK]
if source.type != "MESH":
    raise SystemExit("Stone Sentinels is not a mesh")

# Work entirely in the chunk's local coordinates, excluding detached art.
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
    raise SystemExit("No convincing connected terrain component")
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in terrain], context="FACES")
bm.normal_update()
bvh = BVHTree.FromBMesh(bm)

def height(x, y):
    origin = Vector((x, y, 100))
    while origin.z > -60:
        hit, normal, _, distance = bvh.ray_cast(origin, Vector((0, 0, -1)))
        if hit is None:
            return None
        if normal.z >= MIN_UP:
            return hit.z
        origin.z = hit.z - 0.02
    return None

def grid_height(x, y):
    # The authored socket reaches the exact chunk edge. A vertical perimeter
    # face can make a ray on that mathematical edge ambiguous in the BVH.
    return height(max(-127.99, min(127.99, x)), max(-127.99, min(127.99, y)))

def valid_triangle(indices, heights):
    if any(heights[index] is None for index in indices):
        return False
    return max(heights[index] for index in indices) - min(heights[index] for index in indices) <= MAX_EDGE_RISE

os.makedirs(OUT, exist_ok=True)
collection = bpy.data.collections.new("StoneWalkCollision")
bpy.context.scene.collection.children.link(collection)
pieces = []
skipped = 0
samples = []
collision_vertices = []
collision_faces = []
for ty in range(-128, 128, TILE):
    for tx in range(-128, 128, TILE):
        count = TILE // STEP + 1
        coords = [(tx + ix * STEP, ty + iy * STEP)
                  for iy in range(count) for ix in range(count)]
        heights = [grid_height(x, y) for x, y in coords]
        triangles = []
        for iy in range(count - 1):
            for ix in range(count - 1):
                a = iy * count + ix
                b = a + 1
                c = a + count
                d = c + 1
                for triangle in ((a, b, d), (a, d, c)):
                    if valid_triangle(triangle, heights):
                        triangles.append(triangle)
                    else:
                        skipped += 1
        if not triangles:
            continue
        used = sorted({i for triangle in triangles for i in triangle})
        index = {old: new for new, old in enumerate(used)}
        top = [(coords[i][0], coords[i][1], heights[i] - SHELL)
               for i in used]
        # Each tile is a thin, closed mesh. Short tiles keep convex decomposition
        # from spanning broad dips; the bottom follows the top rather than
        # forming a thick flat block under the island.
        verts = top + [(x, y, z - SHELL) for x, y, z in top]
        n = len(top)
        faces = []
        edge_counts = {}
        for triangle in triangles:
            a, b, c = (index[i] for i in triangle)
            faces.extend(((a, b, c), (c + n, b + n, a + n)))
            offset = len(collision_vertices)
            collision_vertices.extend((top[a], top[b], top[c]))
            collision_faces.append((offset, offset + 1, offset + 2))
            for edge in ((a, b), (b, c), (c, a)):
                key = tuple(sorted(edge))
                edge_counts[key] = edge_counts.get(key, 0) + 1
        for (a, b), count_edge in edge_counts.items():
            if count_edge == 1:
                faces.append((a, a + n, b + n, b))
        mesh = bpy.data.meshes.new(f"walk_{tx}_{ty}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        check = bmesh.new()
        check.from_mesh(mesh)
        if any(not edge.is_manifold for edge in check.edges):
            raise SystemExit(f"Non-manifold collision tile at {tx}, {ty}")
        check.free()
        obj = bpy.data.objects.new(f"walk_{tx:+04d}_{ty:+04d}", mesh)
        collection.objects.link(obj)
        pieces.append(obj)
        for triangle in triangles:
            x = sum(coords[i][0] for i in triangle) / 3
            y = sum(coords[i][1] for i in triangle) / 3
            intended = height(x, y)
            interpolated = sum(heights[i] for i in triangle) / 3
            if intended is not None:
                samples.append(abs(interpolated - intended))

if not pieces:
    raise SystemExit("No collider pieces built")
# Importing many meshes can give the model an arbitrary bounding-box pivot.
# This small disposable marker preserves the chunk's walk-plane origin.
bpy.ops.mesh.primitive_cube_add(size=0.25, location=(0, 0, 0))
origin_marker = bpy.context.object
origin_marker.name = "CollisionOrigin"
collision_bvh = BVHTree.FromPolygons(collision_vertices, collision_faces)
coverage = {"regular_hits": 0, "regular_misses": 0, "north_hits": 0, "north_misses": 0}
errors = []
north_misses = []
for y in range(-126, 128, 4):
    for x in range(-126, 128, 4):
        intended = height(x, y)
        if intended is None:
            continue
        hit, _, _, _ = collision_bvh.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
        region = "north" if y >= 64 and abs(x) <= 48 else "regular"
        coverage[f"{region}_{'hits' if hit is not None else 'misses'}"] += 1
        if hit is None and region == "north":
            north_misses.append([x, y, round(intended, 2)])
        if hit is not None:
            errors.append(abs((hit.z + SHELL) - intended))
fbx = os.path.join(OUT, "stone_sentinels_walk_collision.fbx")
bpy.ops.object.select_all(action="DESELECT")
for obj in pieces:
    obj.select_set(True)
origin_marker.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]
bpy.ops.export_scene.fbx(
    filepath=fbx, use_selection=True, object_types={"MESH"},
    axis_forward="-Z", axis_up="Y", global_scale=1.0,
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
    bake_space_transform=True, use_mesh_modifiers=True,
    mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
)
before_import = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=fbx)
imported = [obj for obj in bpy.data.objects if obj not in before_import and obj.type == "MESH"]
if len(imported) != len(pieces) + 1:
    raise SystemExit(f"FBX reimport has {len(imported)} meshes; expected {len(pieces) + 1}")
with open(bpy.data.filepath, "rb") as stream:
    source_hash = hashlib.sha256(stream.read()).hexdigest()
report = {
    "source": os.path.relpath(bpy.data.filepath, REPO).replace("\\", "/"),
    "source_sha256": source_hash,
    "chunk": CHUNK,
    "connected_terrain_faces": len(terrain),
    "detached_components_excluded": len(components) - 1,
    "tile_studs": TILE,
    "sample_step_studs": STEP,
    "surface_offset_studs": SHELL,
    "pieces": len(pieces),
    "fbx_reimport_meshes_including_origin": len(imported),
    "triangles_skipped_at_open_or_steep_areas": skipped,
    "interpolation_samples": len(samples),
    "interpolation_max_error_studs": round(max(samples), 3),
    "interpolation_mean_error_studs": round(sum(samples) / len(samples), 3),
    "coverage_4_stud_grid": coverage,
    "collision_surface_max_error_studs": round(max(errors), 3),
    "north_miss_locations_blender_xy_height": north_misses,
}
with open(os.path.join(OUT, "stone_sentinels_walk_collision.json"), "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
reference = []
positions = {(x, y) for y in range(-120, 121, 16) for x in range(-120, 121, 16)}
positions |= {(x, y) for y in range(64, 125, 8) for x in range(-48, 49, 8)}
for x, y in sorted(positions):
    intended = height(x, y)
    hit, _, _, _ = collision_bvh.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
    if intended is not None and hit is not None:
        reference.append((x, -y, round(intended, 3)))
lines = [
    "-- Run in Studio Edit mode after importing VV_STONE_SENTINELS_COLLISION.rbxmx.",
    "-- Generated from the reviewed Blender source; coordinates are chunk local.",
    "local kit = game.ServerStorage.LuckboundChunkKits",
    "local template = kit:FindFirstChild('VV_STONE_SENTINELS_COLLISION', true) or workspace:FindFirstChild('VV_STONE_SENTINELS_COLLISION')",
    "assert(template and template:IsA('Model'), 'Stone collision model is missing')",
    "local samples = {",
]
lines.extend(f"    {{{x}, {z}, {h}}}," for x, z, h in reference)
lines += [
    "}",
    "local rotations = {0, 90, 180, 270}",
    "local results = {}",
    "for index, degrees in rotations do",
    "    local clone = template:Clone()",
    "    clone.Parent = workspace",
    "    local origin = Vector3.new((index - 1) * 400, 1000, 0)",
    "    local cf = CFrame.new(origin) * CFrame.Angles(0, math.rad(degrees), 0)",
    "    clone:PivotTo(cf)",
    "    local params = RaycastParams.new()",
    "    params.FilterType = Enum.RaycastFilterType.Include",
    "    params.FilterDescendantsInstances = {clone}",
    "    local misses, overOne, maxError = 0, 0, 0",
    "    for _, sample in samples do",
    "        -- FBX import rotates Blender chunk-local X/Z by 180 degrees.",
    "        local point = cf:PointToWorldSpace(Vector3.new(-sample[1], sample[3] + 50, -sample[2]))",
    "        local hit = workspace:Raycast(point, Vector3.new(0, -100, 0), params)",
    "        if hit then",
    "            local errorStuds = math.abs(hit.Position.Y - (origin.Y + sample[3]))",
    "            maxError = math.max(maxError, errorStuds)",
    "            if errorStuds > 1 then overOne += 1 end",
    "        else misses += 1 end",
    "    end",
    "    print(string.format('STONE %d degrees: %d samples, %d misses, %d >1 stud, max %.3f',",
    "        degrees, #samples, misses, overOne, maxError))",
    "    table.insert(results, {yaw=degrees, samples=#samples, misses=misses, overOne=overOne, maxError=maxError})",
    "    clone:Destroy()",
    "end",
    "return results",
]
with open(os.path.join(OUT, "StoneSentinelsValidation.luau"), "w", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
print("STONE_COLLISION", json.dumps(report))
bm.free()
