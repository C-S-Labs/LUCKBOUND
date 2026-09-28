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
import numpy as np
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
MERGE_COMPATIBLE = "--merge-compatible" in sys.argv
MAX_PLANE_RESIDUAL = 0.22

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
tile_records = {}
grid_heights = {}
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
        grid_heights.update(zip(coords, heights))
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
        tile_records[(tx, ty)] = {"object": obj, "full": len(triangles) == 2 * (count - 1) ** 2}
        for triangle in triangles:
            x = sum(coords[i][0] for i in triangle) / 3
            y = sum(coords[i][1] for i in triangle) / 3
            intended = height(x, y)
            interpolated = sum(heights[i] for i in triangle) / 3
            if intended is not None:
                samples.append(abs(interpolated - intended))

if not pieces:
    raise SystemExit("No collider pieces built")
baseline_count = len(pieces)
merged_regions = []
if MERGE_COMPATIBLE:
    # Only complete neighboring tiles may join. Missing triangles encode
    # cliffs/open space and must never be filled by a fitted rectangle.
    full = np.array([[bool(tile_records.get((x, y), {}).get("full"))
                      for x in range(-128, 128, TILE)]
                     for y in range(-128, 128, TILE)], dtype=np.int32)
    prefix = np.pad(full.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def full_count(ix, iy, width, depth):
        x1, y1 = ix + width, iy + depth
        return int(prefix[y1, x1] - prefix[iy, x1] - prefix[y1, ix] + prefix[iy, ix])

    def plane_fit(coords):
        xy = np.asarray(coords, dtype=np.float64)
        z = np.asarray([grid_heights[tuple(point)] for point in coords], dtype=np.float64)
        matrix = np.column_stack((xy[:, 0], xy[:, 1], np.ones(len(xy))))
        coeff = np.linalg.lstsq(matrix, z, rcond=None)[0]
        return coeff, float(np.max(np.abs(matrix @ coeff - z)))

    tile_slopes = {}
    for (tx, ty), record in tile_records.items():
        if record["full"]:
            coords = [(x, y) for y in range(ty, ty + TILE + 1, STEP)
                      for x in range(tx, tx + TILE + 1, STEP)]
            tile_slopes[(tx, ty)] = plane_fit(coords)[0][:2]

    candidates = []
    side = 256 // TILE
    for iy in range(side):
        for ix in range(side):
            if not full[iy, ix]:
                continue
            for depth in range(1, side - iy + 1):
                for width in range(1, side - ix + 1):
                    area = width * depth
                    if area < 2 or full_count(ix, iy, width, depth) != area:
                        continue
                    tx, ty = -128 + ix * TILE, -128 + iy * TILE
                    coords = [(x, y)
                              for y in range(ty, ty + depth * TILE + 1, STEP)
                              for x in range(tx, tx + width * TILE + 1, STEP)]
                    coeff, residual = plane_fit(coords)
                    if residual > MAX_PLANE_RESIDUAL:
                        continue
                    cells = [(tx + dx * TILE, ty + dy * TILE)
                             for dy in range(depth) for dx in range(width)]
                    slope_delta = max(float(np.linalg.norm(tile_slopes[cell] - coeff[:2]))
                                      for cell in cells)
                    if slope_delta > 0.04:
                        continue
                    candidates.append((area, max(width, depth), -residual,
                                       tx, ty, width, depth, cells, residual, slope_delta))

    occupied = set()
    for area, long_side, _, tx, ty, width, depth, cells, residual, slope_delta in sorted(candidates, reverse=True):
        if any(cell in occupied for cell in cells):
            continue
        occupied.update(cells)
        for cell in cells:
            obj = tile_records[cell]["object"]
            pieces.remove(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
        nx, ny = width * TILE // STEP + 1, depth * TILE // STEP + 1
        coords = [(tx + ix * STEP, ty + iy * STEP)
                  for iy in range(ny) for ix in range(nx)]
        top = [(x, y, grid_heights[(x, y)] - SHELL) for x, y in coords]
        count = len(top)
        verts = top + [(x, y, z - SHELL) for x, y, z in top]
        faces = []
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                a = iy * nx + ix
                b, c, d = a + 1, a + nx, a + nx + 1
                faces.extend(((a, b, d), (a, d, c),
                              (d + count, b + count, a + count),
                              (c + count, d + count, a + count)))
        for ix in range(nx - 1):
            a, b = ix, ix + 1
            c, d = (ny - 1) * nx + ix, (ny - 1) * nx + ix + 1
            faces.extend(((b, a, a + count, b + count),
                          (c, d, d + count, c + count)))
        for iy in range(ny - 1):
            a, b = iy * nx, (iy + 1) * nx
            c, d = iy * nx + nx - 1, (iy + 1) * nx + nx - 1
            faces.extend(((a, b, b + count, a + count),
                          (d, c, c + count, d + count)))
        mesh = bpy.data.meshes.new(f"walk_patch_{tx}_{ty}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        check = bmesh.new()
        check.from_mesh(mesh)
        if any(not edge.is_manifold for edge in check.edges):
            raise SystemExit(f"Non-manifold merged patch at {tx}, {ty}")
        check.free()
        obj = bpy.data.objects.new(f"walk_patch_{tx:+04d}_{ty:+04d}_{width}x{depth}", mesh)
        collection.objects.link(obj)
        pieces.append(obj)
        merged_regions.append({"x": tx, "y": ty, "width_studs": width * TILE,
                               "depth_studs": depth * TILE, "tiles": area,
                               "plane_max_residual": round(residual, 4),
                               "max_slope_delta": round(slope_delta, 4)})

# Importing many meshes can give the model an arbitrary bounding-box pivot.
# This small disposable marker preserves the chunk's walk-plane origin.
bpy.ops.mesh.primitive_cube_add(size=0.25, location=(0, 0, 0))
origin_marker = bpy.context.object
origin_marker.name = "CollisionOrigin"
collision_bvh = BVHTree.FromPolygons(collision_vertices, collision_faces)
surface_equivalence = None
if MERGE_COMPATIBLE:
    merged_vertices, merged_faces = [], []
    for obj in pieces:
        for polygon in obj.data.polygons:
            if len(polygon.vertices) != 3 or polygon.normal.z <= 0:
                continue
            offset = len(merged_vertices)
            merged_vertices.extend(tuple(obj.data.vertices[index].co) for index in polygon.vertices)
            merged_faces.append((offset, offset + 1, offset + 2))
    merged_bvh = BVHTree.FromPolygons(merged_vertices, merged_faces)
    mismatched_hits, maximum_difference = 0, 0.0
    for y in range(-126, 128, 2):
        for x in range(-126, 128, 2):
            origin = Vector((x, y, 100))
            direction = Vector((0, 0, -1))
            baseline_hit, _, _, _ = collision_bvh.ray_cast(origin, direction)
            merged_hit, _, _, _ = merged_bvh.ray_cast(origin, direction)
            if (baseline_hit is None) != (merged_hit is None):
                mismatched_hits += 1
            elif baseline_hit is not None:
                maximum_difference = max(maximum_difference, abs(baseline_hit.z - merged_hit.z))
    surface_equivalence = {"grid_step_studs": 2, "hit_mismatches": mismatched_hits,
                           "max_height_difference_studs": round(maximum_difference, 6)}
    if mismatched_hits or maximum_difference > 0.0001:
        raise SystemExit(f"Merged surface differs from known-good tiles: {surface_equivalence}")
    collision_bvh = merged_bvh
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
stem = "stone_sentinels_walk_collision_merged" if MERGE_COMPATIBLE else "stone_sentinels_walk_collision"
fbx = os.path.join(OUT, stem + ".fbx")
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
    "baseline_pieces": baseline_count,
    "merged_region_count": len(merged_regions),
    "merged_regions": merged_regions,
    "surface_equivalence": surface_equivalence,
    "fbx_reimport_meshes_including_origin": len(imported),
    "triangles_skipped_at_open_or_steep_areas": skipped,
    "interpolation_samples": len(samples),
    "interpolation_max_error_studs": round(max(samples), 3),
    "interpolation_mean_error_studs": round(sum(samples) / len(samples), 3),
    "coverage_4_stud_grid": coverage,
    "collision_surface_max_error_studs": round(max(errors), 3),
    "north_miss_locations_blender_xy_height": north_misses,
}
with open(os.path.join(OUT, stem + ".json"), "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
reference = []
positions = {(x, y) for y in range(-120, 121, 16) for x in range(-120, 121, 16)}
positions |= {(x, y) for y in range(64, 125, 8) for x in range(-48, 49, 8)}
for x, y in sorted(positions):
    intended = height(x, y)
    hit, _, _, _ = collision_bvh.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
    if intended is not None and hit is not None:
        reference.append((x, -y, round(intended, 3)))
template_name = ("VV_STONE_SENTINELS_COLLISION_MERGED" if MERGE_COMPATIBLE
                 else "VV_STONE_SENTINELS_COLLISION")
lines = [
    "-- Run in Studio Edit mode after importing the Stone Sentinels collider.",
    "-- Generated from the reviewed Blender source; coordinates are chunk local.",
    "local kit = game.ServerStorage.LuckboundChunkKits",
    f"local template = kit:FindFirstChild('{template_name}', true) or workspace:FindFirstChild('{template_name}')",
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
validation_name = "StoneSentinelsMergedValidation.luau" if MERGE_COMPATIBLE else "StoneSentinelsValidation.luau"
if MERGE_COMPATIBLE:
    lines = [
        "-- Compare the preserved 202-piece model with the compatible-patch candidate.",
        "-- Run in Studio Edit after importing the merged FBX and setting its origin.",
        "local kit = game.ServerStorage.LuckboundChunkKits",
        "local names = {'VV_STONE_SENTINELS_COLLISION', 'VV_STONE_SENTINELS_COLLISION_MERGED'}",
        "local samples = {",
    ]
    lines.extend(f"    {{{x}, {z}, {h}}}," for x, z, h in reference)
    lines += ["}", "local cliffProbes = {"]
    lines.extend(f"    {{{-x}, {y}}}," for x, y, _ in north_misses)
    lines += [
        "}",
        "local results = {}",
        "for _, name in names do",
        "    local template = kit:FindFirstChild(name, true) or workspace:FindFirstChild(name)",
        "    assert(template and template:IsA('Model'), name .. ' is missing')",
        "    for index, degrees in {0, 90, 180, 270} do",
        "        local clone = template:Clone()",
        "        clone.Parent = workspace",
        "        local origin = Vector3.new((index - 1) * 400, 1000, 0)",
        "        local cf = CFrame.new(origin) * CFrame.Angles(0, math.rad(degrees), 0)",
        "        clone:PivotTo(cf)",
        "        local params = RaycastParams.new()",
        "        params.FilterType = Enum.RaycastFilterType.Include",
        "        params.FilterDescendantsInstances = {clone}",
        "        local errors, misses, overOne, bridges = {}, 0, 0, 0",
        "        for _, sample in samples do",
        "            local point = cf:PointToWorldSpace(Vector3.new(-sample[1], sample[3] + 50, -sample[2]))",
        "            local hit = workspace:Raycast(point, Vector3.new(0, -100, 0), params)",
        "            if hit then",
        "                local difference = math.abs(hit.Position.Y - (origin.Y + sample[3]))",
        "                table.insert(errors, difference)",
        "                if difference > 1 then overOne += 1 end",
        "            else misses += 1 end",
        "        end",
        "        for _, probe in cliffProbes do",
        "            local point = cf:PointToWorldSpace(Vector3.new(probe[1], 50, probe[2]))",
        "            if workspace:Raycast(point, Vector3.new(0, -100, 0), params) then bridges += 1 end",
        "        end",
        "        table.sort(errors)",
        "        local sum = 0",
        "        for _, difference in errors do sum += difference end",
        "        table.insert(results, {model=name, yaw=degrees, pieces=#clone:GetDescendants(),",
        "            samples=#samples, misses=misses, overOne=overOne, bridgedCliffs=bridges,",
        "            mean=#errors > 0 and sum / #errors or 0,",
        "            p95=#errors > 0 and errors[math.ceil(#errors * 0.95)] or 0,",
        "            max=#errors > 0 and errors[#errors] or 0})",
        "        clone:Destroy()",
        "    end",
        "end",
        "return results",
    ]
with open(os.path.join(OUT, validation_name), "w", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
print("STONE_COLLISION", json.dumps(report))
bm.free()
