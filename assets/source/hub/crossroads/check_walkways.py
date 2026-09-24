"""Walk every route (plaza -> bridges -> districts, the promenade ring, the overlooks)
and report any gap or lip over 0.55 studs. District interiors are skipped.
Overlook routes hit the beacon pylons by design.

    blender -b --factory-startup --python check_walkways.py
"""
import bpy, sys, runpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.argv = ["x"]
g = runpy.run_path(r"C:\Dev\luckbound\assets\source\hub\crossroads\build_crossroads_hub.py", run_name="lib")
groups = g["build_all"]()
dg = bpy.context.evaluated_depsgraph_get()
trees = [BVHTree.FromObject(o, dg) for o in groups["Hub"]]
def ground(x, y):
    best = None
    for t in trees:
        h = t.ray_cast(Vector((x, y, 8)), Vector((0, 0, -1)), 30)
        if h[0] is not None and (best is None or h[0].z > best):
            best = h[0].z
    return best
DA, PR = g["DISTRICT_AT"], g["PLAZA_R"]
routes = {}
for k in range(4):                                   # engine edge -> plaza -> bridge -> district centre
    a = math.radians(90 * k)
    for off in (-10, 0, 10):                         # the bridge's left, middle, right
        routes[f"bridge{k}_{off}"] = [(math.cos(a) * r - math.sin(a) * off, math.sin(a) * r + math.cos(a) * off)
                                      for r in [35 + i * 0.5 for i in range(int((DA - 64 - 35) / 0.5))]]
for k in range(4):                                   # district -> ring arc -> overlook -> next district
    for dr in (-7, 0, 7):
        pts = []
        for i in range(0, 901):
            a = math.radians(90 * k + 90 * i / 900)
            pts.append((math.cos(a) * (DA + dr), math.sin(a) * (DA + dr)))
        routes[f"ring{k}_{dr}"] = pts
    am = math.radians(45 + 90 * k)
    routes[f"overlook{k}"] = [(math.cos(am) * r, math.sin(am) * r) for r in [DA + i * 0.5 for i in range(60)]]
bad = 0
for name, pts in routes.items():
    prev = None
    cents = [(0, DA), (DA, 0), (0, -DA), (-DA, 0)]
    for x, y in pts:
        if any(math.hypot(x - cx, y - cy) < 64 for cx, cy in cents):
            prev = None
            continue
        z = ground(x, y)
        if z is None:
            print("GAP", name, round(x, 1), round(y, 1)); bad += 1; break
        if prev is not None and abs(z - prev) > 0.55:
            print("STEP", name, round(x, 1), round(y, 1), round(prev, 2), "->", round(z, 2)); bad += 1
        prev = z
print("WALK CHECK", len(routes), "routes,", bad, "problems")
