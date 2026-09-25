# Build every enemy of a tier into ONE review .blend, side by side (each in its own collection, rigged).
#   blender -b --factory-startup --python assets/source/enemies/_framework/lineup.py -- <world> <tier|all> <out.blend>
import bpy, sys, os, importlib.util
FW = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(FW)
argv = sys.argv[sys.argv.index("--") + 1:]
WORLD, TIER, OUT = argv[0], argv[1], argv[2]
HERE = os.path.join(ROOT, WORLD)
spec = importlib.util.spec_from_file_location("manifest", os.path.join(HERE, "manifest.py"))
MAN = importlib.util.module_from_spec(spec); spec.loader.exec_module(MAN)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
x = 0.0
for eid, e in MAN.ENEMIES.items():
    if TIER != "all" and e["tier"] != TIER: continue
    before = set(bpy.data.objects)
    G = {"__name__": eid, "FW": FW, "HERE": HERE, "OUT_DIR": HERE, "RENDER_DIR": HERE, "bpy": bpy}
    exec(open(os.path.join(HERE, e["script"])).read(), G)
    for extra in e.get("extras", []): exec(open(os.path.join(HERE, extra)).read(), G)
    new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new(eid); bpy.context.scene.collection.children.link(col)
    rig = G["rig"]; off = rig.location.copy()
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    rig.location = (x, 0, off.z)                                  # line them up along +X, 3.5 m apart
    x += 3.5
    print("LINEUP", eid)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
