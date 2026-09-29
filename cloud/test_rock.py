"""
Procedural rock generator - test script.

Works two ways:
  1. Inside Blender: Scripting tab -> Open -> Run Script. Adds a rock to your scene.
  2. Headless (cloud / terminal):  python test_rock.py
     Builds the rock in an empty scene and exports exports/test_rock.fbx
"""
import os
import random
import bpy
import bmesh
from mathutils import Vector, noise

# ---- Settings ------------------------------------------------------------
SEED = 42
SUBDIVISIONS = 4        # detail level of the base sphere
RADIUS = 1.0
NOISE_SCALE = 1.6       # bigger = more, smaller lumps
NOISE_STRENGTH = 0.35   # how bumpy the rock is
FLATTEN_BOTTOM = True   # flat base so it sits on terrain
EXPORT_DIR = "exports"
# -------------------------------------------------------------------------


def make_rock(name="Rock", seed=SEED):
    random.seed(seed)
    offset = Vector((random.uniform(-100, 100) for _ in range(3)))

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=SUBDIVISIONS, radius=RADIUS)

    # Stretch slightly so it isn't a perfect ball
    stretch = Vector((random.uniform(0.8, 1.3), random.uniform(0.8, 1.3), random.uniform(0.6, 1.0)))

    for v in bm.verts:
        n = noise.fractal(v.co * NOISE_SCALE + offset, 0.5, 2.0, 4)
        v.co += v.normal * n * NOISE_STRENGTH
        v.co = Vector((v.co.x * stretch.x, v.co.y * stretch.y, v.co.z * stretch.z))
        if FLATTEN_BOTTOM and v.co.z < -0.3:
            v.co.z = -0.3 + (v.co.z + 0.3) * 0.15

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = False  # faceted low-poly look; set True for smooth
    return obj


def main():
    headless = bpy.app.background
    if headless:
        # Start from an empty scene
        bpy.ops.wm.read_factory_settings(use_empty=True)

    rock = make_rock()
    me = rock.data
    print(f"Created '{rock.name}': {len(me.vertices)} verts, {len(me.polygons)} faces")

    if headless:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        path = os.path.join(EXPORT_DIR, "test_rock.fbx")
        bpy.ops.object.select_all(action="DESELECT")
        rock.select_set(True)
        bpy.context.view_layer.objects.active = rock
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True)
        print(f"Exported {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
