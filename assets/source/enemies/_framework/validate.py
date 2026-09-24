# Enemy validation (run by run.py --validate, or exec'd after any build). Prints VALIDATE lines and a PASS/FAIL summary.
# Hard rules (fail): every mesh < 10k tris; R15 core bones present; minibosses/bosses have finger bones;
#                    nothing below the floor (z < -5 mm) in the posed state.
# Soft report: piece-vs-piece overlaps (designed joins such as neck-in-collar also show up; read them, don't chase zero).
import bpy
from mathutils.bvhtree import BVHTree
TRI_CAP = 10000
R15 = ["HumanoidRootNode", "LowerTorso", "UpperTorso", "Head"]
_fails = []
_dg = bpy.context.evaluated_depsgraph_get()
_meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(PREFIX) and "_Break" not in o.name]
_trees = {}
_minz = 1e9
for o in _meshes:
    oe = o.evaluated_get(_dg); m = oe.to_mesh()
    tris = sum(len(p.vertices) - 2 for p in m.polygons)
    if tris >= TRI_CAP:
        _fails.append(f"{o.name}: {tris} tris >= {TRI_CAP}")
    v = [o.matrix_world @ x.co for x in m.vertices]
    if v and not o.hide_render:
        _minz = min(_minz, min(p.z for p in v))
        _trees[o.name[len(PREFIX):]] = BVHTree.FromPolygons(v, [tuple(p.vertices) for p in m.polygons])
    oe.to_mesh_clear()
_bones = {b.name for b in rig.data.bones}
_humanoid = ENTRY.get("body", "humanoid") == "humanoid"
if _humanoid:
    for b in R15:
        if b not in _bones: _fails.append(f"missing R15 bone {b}")
if TIER in ("miniboss", "boss") and _humanoid:
    if not any("Index1" in b for b in _bones): _fails.append("miniboss/boss without finger bones")
_ground = 0.0
if _minz < _ground - 0.005 and not ENTRY.get("sunk"):      # "sunk": emerges from the ground by design
    _fails.append(f"below floor: min z {_minz:.3f}")
_names = sorted(_trees)
for i, a in enumerate(_names):
    for b in _names[i + 1:]:
        if a.replace("Glow", "") == b.replace("Glow", ""): continue
        n = len(_trees[a].overlap(_trees[b]))
        if n: print(f"VALIDATE overlap {a} x {b}: {n}")
print(f"VALIDATE {NAME} tier={TIER} meshes={len(_meshes)} tris={sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in _meshes)}")
print("VALIDATE " + ("PASS" if not _fails else "FAIL: " + "; ".join(_fails)))
