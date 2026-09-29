"""
Procedural crystal cluster generator.

Works two ways:
  1. Inside Blender: Scripting tab -> Open -> Run Script. Adds the cluster to your scene.
  2. Headless (cloud / terminal):  python gen_crystal_cluster.py
     Builds the cluster in an empty scene and exports exports/crystal_cluster.fbx
"""
import os
import random
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

# ---- Settings ------------------------------------------------------------
SEED = 7
MIN_CRYSTALS = 5
MAX_CRYSTALS = 9
SEGMENTS = 6             # hexagonal prism
CLUSTER_RADIUS = 0.9     # how far crystal bases spread from center
BASE_RADIUS_RANGE = (0.12, 0.28)
TIP_RADIUS_RATIO = (0.05, 0.2)   # tip radius as a fraction of base radius (tapered, not pointed)
HEIGHT_RANGE = (0.6, 1.8)
TILT_RANGE_DEG = (0, 18)          # lean away from vertical
FLATTEN_BOTTOM = True
EXPORT_DIR = "exports"
# -------------------------------------------------------------------------


def make_crystal(bm, base_radius, tip_radius, height, position, tilt_deg, twist_deg):
    """Adds one tapered hexagonal prism into bm, transformed in place."""
    verts_bottom = []
    verts_top = []
    for i in range(SEGMENTS):
        angle = (2 * math.pi / SEGMENTS) * i
        bx = math.cos(angle) * base_radius
        by = math.sin(angle) * base_radius
        verts_bottom.append(bm.verts.new((bx, by, 0.0)))

        top_angle = angle + math.radians(twist_deg)
        tx = math.cos(top_angle) * tip_radius
        ty = math.sin(top_angle) * tip_radius
        verts_top.append(bm.verts.new((tx, ty, height)))

    bm.verts.ensure_lookup_table()

    # bottom cap (flat base, facing down)
    bm.faces.new(list(reversed(verts_bottom)))
    # top cap (small flat tip)
    bm.faces.new(verts_top)
    # side quads
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        bm.faces.new((verts_bottom[i], verts_bottom[j], verts_top[j], verts_top[i]))

    # transform: tilt then move to position
    tilt_axis = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized()
    tilt_mat = Matrix.Rotation(math.radians(tilt_deg), 4, tilt_axis)
    translate_mat = Matrix.Translation(position)
    xform = translate_mat @ tilt_mat

    all_verts = verts_bottom + verts_top
    for v in all_verts:
        v.co = xform @ v.co


def make_crystal_cluster(name="CrystalCluster", seed=SEED):
    random.seed(seed)
    count = random.randint(MIN_CRYSTALS, MAX_CRYSTALS)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    for _ in range(count):
        base_radius = random.uniform(*BASE_RADIUS_RANGE)
        tip_radius = base_radius * random.uniform(*TIP_RADIUS_RATIO)
        height = random.uniform(*HEIGHT_RANGE)
        tilt_deg = random.uniform(*TILT_RANGE_DEG)
        twist_deg = random.uniform(0, 360)

        r = random.uniform(0, CLUSTER_RADIUS)
        theta = random.uniform(0, 2 * math.pi)
        position = Vector((math.cos(theta) * r, math.sin(theta) * r, 0.0))

        make_crystal(bm, base_radius, tip_radius, height, position, tilt_deg, twist_deg)

    # Merge coincident verts where crystal bases touch, then re-flatten to z=0.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

    if FLATTEN_BOTTOM:
        for v in bm.verts:
            if v.co.z < 0.001:
                v.co.z = 0.0

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = False  # faceted low-poly look
    return obj, count


def main():
    headless = bpy.app.background
    if headless:
        # Start from an empty scene
        bpy.ops.wm.read_factory_settings(use_empty=True)

    cluster, count = make_crystal_cluster()
    me = cluster.data
    print(f"Created '{cluster.name}': {count} crystals, {len(me.vertices)} verts, {len(me.polygons)} faces")

    if headless:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        path = os.path.join(EXPORT_DIR, "crystal_cluster.fbx")
        bpy.ops.object.select_all(action="DESELECT")
        cluster.select_set(True)
        bpy.context.view_layer.objects.active = cluster
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True)
        print(f"Exported {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
