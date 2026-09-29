"""Fill four Verdant Valley side pockets while preserving their travel lanes.

Run on the owner's VerdantValley_Extra_Details_Backup.blend. Re-running replaces
only this script's named scenery. Temp remains the reusable prop source.
"""

import bpy
import math
import random
from mathutils import Vector
from mathutils.bvhtree import BVHTree


SCENE = "VerdantValley_Extra_Details_Backup.blend"
TAG = "__detail_scatter_"
OLD_TAG = "__temp_scatter_"
TARGETS = {
    "chunk_side_treasure_hollow": {
        "patches": [(-49, 76), (-51, 35), (-45, -12), (48, -23), (55, -59)],
        "logs": [(-64, 14), (72, -38)],
        "trees": [(-58, 6), (61, -72)],
        "seed": 2001,
    },
    "chunk_longgrass_meadow": {
        "patches": [(-53, 61), (-52, 8), (-56, -57), (54, 60), (53, 2), (53, -57)],
        "logs": [(-78, -17), (77, 30)],
        "trees": [(-77, -18), (72, 2), (70, -74)],
        "seed": 2002,
    },
    "chunk_deep_clearing": {
        "patches": [(-58, 57), (-55, -22), (-53, -69), (55, 65), (58, -65)],
        "logs": [(-76, -49), (78, 75)],
        "trees": [(-76, -13), (64, 76)],
        "seed": 2003,
    },
    "chunk_side_wardens_clearing": {
        "patches": [(-53, 64), (53, 62), (-53, 12), (53, 2), (-52, -59), (52, -66)],
        "logs": [(-78, -37), (73, -36)],
        "trees": [(-52, -24), (50, -18), (-48, -68)],
        "seed": 2004,
    },
}

# Two anchor bushes, uneven offspring, and a few stone accents per patch.
# Each patch is rotated and slightly warped so repeated groups do not read as a stamp.
PATTERN = [
    ("flowering_bush", 0, 0, 1.7),
    ("Star_bush", -6, 5, 1.3),
    ("flowering_bush", 7, -3, 1.15),
    ("grass_tuft", -11, -5, 1.55),
    ("grass_tuft", 2, 10, 1.25),
    ("grass_tuft", 11, 7, 1.4),
    ("Star_bush", -12, 11, 0.9),
    ("grass_tuft", 13, -9, 1.05),
    ("rock", -15, -10, 0.73),
    ("grass_tuft", 18, 2, 1.15),
]


def terrain_hit(bvh, x, y, radius):
    checks = [(0, 0), (-radius, 0), (radius, 0), (0, -radius), (0, radius)]
    center = None
    for dx, dy in checks:
        hit, normal, _, _ = bvh.ray_cast(Vector((x + dx, y + dy, 150)), Vector((0, 0, -1)), 300)
        if hit is None or normal.z < 0.75:
            return None
        if dx == 0 and dy == 0:
            center = hit
    return center


def path_clear(name, x, y, radius):
    if abs(x) - radius < 35 or abs(x) + radius > 111 or abs(y) + radius > 111:
        return False
    if name == "chunk_deep_clearing" and x > 0 and abs(y) - radius < 35:
        return False  # east branch
    return True


def scatter_chunk(name, config, templates, solid, nonsolid):
    rng = random.Random(config["seed"])
    chunk = bpy.data.objects[name]
    bvh = BVHTree.FromObject(chunk, bpy.context.evaluated_depsgraph_get())
    made = []
    skipped = 0
    specs = []
    for patch_index, (px, py) in enumerate(config["patches"], 1):
        turn = rng.uniform(-math.pi, math.pi)
        stretch = rng.uniform(0.82, 1.18)
        for kind, dx, dy, size in PATTERN:
            x = px + stretch * (dx * math.cos(turn) - dy * math.sin(turn)) + rng.uniform(-2.4, 2.4)
            y = py + stretch * (dx * math.sin(turn) + dy * math.cos(turn)) + rng.uniform(-2.4, 2.4)
            specs.append((kind, x, y, size * rng.uniform(0.88, 1.12), patch_index))
    for index, (x, y) in enumerate(config["logs"], 1):
        specs.append(("log", x, y, 0.9 + 0.12 * index, 90 + index))

    for kind, x, y, size, patch_index in specs:
        radius = 6 if kind in {"log", "rock"} else 3
        if not path_clear(name, x, y, radius):
            skipped += 1
            continue
        hit = terrain_hit(bvh, x, y, radius)
        if hit is None:
            skipped += 1
            continue
        template = templates[kind]
        obj = template.copy()
        obj.data = template.data.copy()
        obj.name = f"{name}{TAG}{patch_index:02d}_{kind.lower()}_{len(made)+1:03d}"
        (solid if kind in {"rock", "log"} else nonsolid).objects.link(obj)
        obj.location = chunk.location + Vector((x, y, hit.z))
        obj.rotation_euler = (0, 0, rng.uniform(-math.pi, math.pi))
        obj.scale = tuple(s * size for s in template.scale)
        bpy.context.view_layer.update()
        bottom = min((obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box)
        obj.location.z += chunk.location.z + hit.z - bottom - (0.2 if kind == "rock" else 0.04)
        made.append(obj)
    return bvh, made, skipped


def material(name, rgba, emission=False):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        if emission:
            bsdf.inputs["Emission Color"].default_value = rgba
            bsdf.inputs["Emission Strength"].default_value = 2.0
    return mat


def lantern_post(name, chunk, bvh, solid):
    x, y = 45.0, -42.0
    hit = terrain_hit(bvh, x, y, 5)
    if hit is None or not path_clear(name, x, y, 9):
        raise RuntimeError("Lantern post site is not suitable ground")

    verts, faces, material_ids = [], [], []

    def box(x0, x1, y0, y1, z0, z1, mat):
        start = len(verts)
        verts.extend([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                      (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(start + v for v in f))
            material_ids.append(mat)

    # Dark wood post and outward hook; the warm glass hangs below the hook.
    box(-0.7, 0.7, -0.7, 0.7, -0.2, 13.0, 0)
    box(-1.1, 6.4, -0.55, 0.55, 11.4, 12.3, 0)
    box(5.55, 6.05, -0.25, 0.25, 9.4, 11.5, 1)
    box(4.7, 6.9, -1.1, 1.1, 7.3, 9.4, 2)
    box(4.4, 7.2, -1.35, 1.35, 9.25, 9.65, 1)
    box(4.8, 6.8, -1.0, 1.0, 7.0, 7.3, 1)
    for fx in (4.6, 6.85):
        for fy in (-1.2, 1.0):
            box(fx, fx + 0.25, fy, fy + 0.25, 7.3, 9.4, 1)
    mesh = bpy.data.meshes.new("TreasureHollowLanternPostMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(material("VV_ScatterDarkWood", (0.18, 0.12, 0.08, 1)))
    mesh.materials.append(material("VV_ScatterLanternIron", (0.14, 0.13, 0.09, 1)))
    mesh.materials.append(material("VV_ScatterLanternAmber", (1.0, 0.58, 0.15, 1), True))
    for face, mat in zip(mesh.polygons, material_ids):
        face.material_index = mat
    obj = bpy.data.objects.new(f"{name}{TAG}lantern_post", mesh)
    solid.objects.link(obj)
    obj.location = chunk.location + Vector((x, y, hit.z))
    obj.rotation_euler.z = math.pi  # hook faces the clear path
    return obj


def make_sapling(name, chunk, bvh, solid, nonsolid, index, x, y, rng):
    if not path_clear(name, x, y, 11):
        return []
    hit = terrain_hit(bvh, x, y, 9)
    if hit is None:
        return []
    height = rng.uniform(12.0, 15.0)
    spread = rng.uniform(7.5, 10.0)
    trunk_vertices = []
    for z, radius in ((-0.2, 1.25), (height, 0.62)):
        trunk_vertices.extend((math.cos(i * math.tau / 7) * radius,
                               math.sin(i * math.tau / 7) * radius, z) for i in range(7))
    trunk_faces = [tuple(range(6, -1, -1)), tuple(range(7, 14))]
    trunk_faces.extend((i, (i + 1) % 7, (i + 1) % 7 + 7, i + 7) for i in range(7))
    trunk_mesh = bpy.data.meshes.new(f"VVScatterSaplingTrunk{index}")
    trunk_mesh.from_pydata(trunk_vertices, [], trunk_faces)
    trunk_mesh.materials.append(material("VV_ScatterTreeBark", (0.29, 0.22, 0.14, 1)))
    trunk = bpy.data.objects.new(f"{name}{TAG}tree_{index:02d}_trunk", trunk_mesh)
    solid.objects.link(trunk)

    golden = (1 + math.sqrt(5)) / 2
    ico_vertices = [(-1, golden, 0), (1, golden, 0), (-1, -golden, 0), (1, -golden, 0),
                    (0, -1, golden), (0, 1, golden), (0, -1, -golden), (0, 1, -golden),
                    (golden, 0, -1), (golden, 0, 1), (-golden, 0, -1), (-golden, 0, 1)]
    ico_faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
                 (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
                 (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                 (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    canopy_vertices, canopy_faces = [], []
    for dx, dy, dz, radius in ((0, 0, height + 4.5, spread),
                               (spread * 0.25, -spread * 0.18, height + 9.0, spread * 0.78)):
        start = len(canopy_vertices)
        canopy_vertices.extend(tuple(Vector(vertex).normalized() * radius + Vector((dx, dy, dz)))
                               for vertex in ico_vertices)
        canopy_faces.extend(tuple(start + v for v in face) for face in ico_faces)
    canopy_mesh = bpy.data.meshes.new(f"VVScatterSaplingCanopy{index}")
    canopy_mesh.from_pydata(canopy_vertices, [], canopy_faces)
    canopy_mesh.materials.append(material("VV_ScatterLeafDark", (0.20, 0.34, 0.18, 1)))
    canopy_mesh.materials.append(material("VV_ScatterLeafLight", (0.29, 0.43, 0.23, 1)))
    for face in canopy_mesh.polygons:
        face.material_index = int(face.index % 7 == 0)
    canopy = bpy.data.objects.new(f"{name}{TAG}tree_{index:02d}_canopy", canopy_mesh)
    nonsolid.objects.link(canopy)
    origin = chunk.location + Vector((x, y, hit.z))
    trunk.location = origin
    canopy.location = origin
    canopy.rotation_euler.z = rng.uniform(-math.pi, math.pi)
    return [trunk, canopy]


def main():
    if bpy.path.basename(bpy.data.filepath) != SCENE:
        raise RuntimeError(f"Open {SCENE} first")
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(name + tag) for name in TARGETS for tag in (TAG, OLD_TAG)):
            bpy.data.objects.remove(obj, do_unlink=True)
    templates = bpy.data.collections["Temp"].objects
    solid = bpy.data.collections["VV_PROPS_SOLID"]
    nonsolid = bpy.data.collections["VV_PROPS_NONSOLID"]
    report = {}
    for name, config in TARGETS.items():
        bvh, made, skipped = scatter_chunk(name, config, templates, solid, nonsolid)
        rng = random.Random(config["seed"] + 100)
        for index, (x, y) in enumerate(config["trees"], 1):
            trees = make_sapling(name, bpy.data.objects[name], bvh, solid, nonsolid, index, x, y, rng)
            made.extend(trees)
            if not trees:
                skipped += 1
        if name == "chunk_side_treasure_hollow":
            made.append(lantern_post(name, bpy.data.objects[name], bvh, solid))
        report[name] = {"added": len(made), "skipped": skipped}
        if len(made) < 25:
            raise RuntimeError(f"Too few suitable placements: {name} {report[name]}")
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print("SCATTER_REPORT", report)


if __name__ == "__main__":
    main()
