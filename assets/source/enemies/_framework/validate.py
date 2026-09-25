# Enemy validation (run by run.py --validate, or exec'd after any build). Prints VALIDATE lines and a PASS/FAIL summary.
# Hard rules (fail): every mesh < 10k tris; R15 core bones present; minibosses/bosses have finger bones;
#                    nothing below the floor (z < -5 mm) in the posed state.
# Soft report: piece-vs-piece overlaps (designed joins such as neck-in-collar also show up; read them, don't chase zero).
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
TRI_CAP = 10000                                   # Studio per-mesh limit: split bigger enemies into pieces
TIER_BUDGET = {"basic": (10000, 12500), "miniboss": (None, 35000), "boss": (None, 75000), "legendary": (None, 100000)}
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
_total = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in _meshes)
_lo, _hi = TIER_BUDGET.get(TIER, (None, None))
if _hi and _total > _hi: _fails.append(f"{_total} tris over the {TIER} budget {_hi}")
if _lo and _total < _lo: print(f"VALIDATE note: {_total} tris is under the {TIER} target {_lo}-{_hi} (room for more character)")
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
# FLOATING PARTS: every loose mesh island (across ALL of the enemy's meshes, glow included) must touch another
# island's SURFACE (within 4 mm) or cross it. Reports islands that touch nothing = visibly floating parts.
import bmesh as _bm
_V, _F, _own = [], [], []
_isl_verts = []
for o in _meshes:
    if o.hide_render: continue
    b = _bm.new(); b.from_mesh(o.evaluated_get(_dg).to_mesh()); o.evaluated_get(_dg).to_mesh_clear()
    b.verts.ensure_lookup_table(); base = len(_V); seen = {}
    for v in b.verts:
        if v.index in seen: continue
        iid = len(_isl_verts); comp = []; stack = [v]
        while stack:
            x = stack.pop()
            if x.index in seen: continue
            seen[x.index] = iid; comp.append(base + x.index)
            stack.extend(e.other_vert(x) for e in x.link_edges)
        _isl_verts.append(comp)
    _V += [o.matrix_world @ v.co for v in b.verts]
    for f in b.faces:
        _F.append(tuple(base + v.index for v in f.verts)); _own.append(seen[f.verts[0].index])
    b.free()
_T = BVHTree.FromPolygons(_V, _F)
_float = []
for iid, comp in enumerate(_isl_verts):
    if len(comp) < 4 or len(_isl_verts) < 2: continue
    ok = False
    for vi in comp[::max(1, len(comp)//80)]:
        for (co, n, fi, d) in _T.find_nearest_range(_V[vi], 0.004):
            if _own[fi] != iid: ok = True; break
        if ok: break
    if not ok:
        mine = [f for f, w in zip(_F, _own) if w == iid]; rest = [f for f, w in zip(_F, _own) if w != iid]
        if mine and rest and BVHTree.FromPolygons(_V, mine).overlap(BVHTree.FromPolygons(_V, rest)): ok = True
    if not ok:
        c = sum((_V[vi] for vi in comp), Vector())/len(comp)
        _float.append(("island", tuple(round(x, 2) for x in c), len(comp)))
for f in _float: print(f"VALIDATE floating? {f[0]} part near {f[1]} ({f[2]} verts)")
_names = sorted(_trees)
for i, a in enumerate(_names):
    for b in _names[i + 1:]:
        if a.replace("Glow", "") == b.replace("Glow", ""): continue
        n = len(_trees[a].overlap(_trees[b]))
        if n: print(f"VALIDATE overlap {a} x {b}: {n}")
print(f"VALIDATE {NAME} tier={TIER} meshes={len(_meshes)} tris={sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in _meshes)}")
print("VALIDATE " + ("PASS" if not _fails else "FAIL: " + "; ".join(_fails)))
