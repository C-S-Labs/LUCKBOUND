"""The detail pass: every prop mesh finished before it is exported.

Owner, 2026-09-23: "aiming for 2500-5000 tris will add more detail to props
and give the game a more complete feel." Props are built from blocky
primitives (a crate is a box); this pass finishes them, shell by shell, by
what each shell is made of:

  HARD      metal, timber, stone blocks  -> every edge bevelled (rounded in
            segments), so a crate reads as a crate, not a cube
  ORGANIC   moss, snow, foliage, bone, rock -> subdivided and pushed by a
            seeded noise, so it reads grown, not turned
  CRYSTAL   ice and aether               -> each facet split and nudged, so a
            crystal catches light on many small planes

How far each prop goes is set by its size (its bounding radius): a pebble or
a feather is not given 3,000 triangles nobody can see. The budgets:
  small  (radius < 1.6)   ~300-900
  medium (radius < 3.5)   ~900-2,500
  large                   ~2,500-5,000, never over 8,000
A prop already at or over its budget (the warships) is left as built.

The pass never grows a prop past its bounding box (a bevel cuts inward,
subdivision shrinks toward the middle), so the measured footprint the scatter
uses stays true; the game draws each copy at its own size anyway.
"""

import math
import random

import bmesh

HARD_MATS = {
    "CitadelWhite", "PaleAlloy", "DeepAlloy", "SunGold", "CitadelViolet", "Gunmetal", "Steel", "Plating",
    "Hazard", "AlarmRed", "AlarmDim", "RaiderRust", "Twig", "Bark", "Char", "Soot", "HullSlate", "EmberGlow",
    "AzureDim", "AzureNeon", "Weathered", "VaultDark", "Scorched", "StormSlate", "Lavender",
}
ORGANIC_MATS = {"Moss", "MossLight", "Verdure", "Snow", "Frost", "FrostDeep", "Bone", "Lichen", "StormStone",
                "Petal", "Mushroom", "Leaf", "Smoke"}
CRYSTAL_MATS = {"Ice", "SkyGlass", "AetherBloom", "Pearl", "AetherDim"}

BUDGET = ((1.6, 300, 900), (3.5, 900, 2500), (1e9, 2500, 5000))
HARD_CAP = 8000


def _dtris(faces):
    return sum(len(f) - 2 for f in faces)


def _dstyle(mats):
    count = {"hard": 0, "organic": 0, "crystal": 0}
    for m in mats:
        if m in ORGANIC_MATS:
            count["organic"] += 1
        elif m in CRYSTAL_MATS:
            count["crystal"] += 1
        else:
            count["hard"] += 1
    return max(count, key=count.get)


def _to_bm(verts, faces, mats, names):
    bm = bmesh.new()
    bv = [bm.verts.new(v) for v in verts]
    idx = {n: i for i, n in enumerate(names)}
    seen = set()
    for f, m in zip(faces, mats):
        key = frozenset(f)
        if key in seen or len(set(f)) < 3:
            return None                 # a double-sided sheet: leave it as built
        seen.add(key)
        try:
            face = bm.faces.new([bv[i] for i in f])
        except ValueError:
            return None
        face.material_index = idx[m]
    bm.normal_update()
    return bm


def _from_bm(bm, names):
    bm.verts.index_update()
    verts = [v.co.copy() for v in bm.verts]
    faces, mats = [], []
    for f in bm.faces:
        faces.append([v.index for v in f.verts])
        mats.append(names[f.material_index])
    return verts, faces, mats


def _bm_shells(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        stack, group = [f], []
        seen.add(f)
        while stack:
            g = stack.pop()
            group.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(group)
    return out


def _bevel(bm, faces, width, segments):
    edges = list({e for f in faces for e in f.edges})
    if not edges:
        return
    bmesh.ops.bevel(bm, geom=edges + list({v for e in edges for v in e.verts}), offset=width,
                    offset_type='OFFSET', segments=segments, profile=0.5, affect='EDGES', clamp_overlap=True)


def _subdivide(bm, faces, cuts, smooth, jitter, rng):
    edges = list({e for f in faces for e in f.edges})
    if not edges:
        return
    res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True, smooth=smooth)
    new = [g for g in res.get("geom_inner", []) + res.get("geom_split", []) if isinstance(g, bmesh.types.BMVert)]
    for v in new:
        n = v.normal
        v.co += n * rng.uniform(-jitter, jitter)


def detail(verts, faces, mats, seed, radius):
    """-> (verts, faces, mats): the finished mesh (or the input, unchanged,
    when it is double-sided or already at its budget)."""
    lo, hi = next((a, b) for r, a, b in BUDGET if radius < r)
    if _dtris(faces) >= lo:
        return verts, faces, mats
    names = sorted(set(mats))
    rng = random.Random(seed)
    best = (verts, faces, mats)
    # try increasing strength until the prop reaches its budget's floor
    for level in (1, 2, 3, 4, 5, 6):
        bm = _to_bm(verts, faces, mats, names)
        if bm is None:
            return verts, faces, mats
        for group in _bm_shells(bm):
            gm = [names[f.material_index] for f in group]
            style = _dstyle(gm)
            pts = [v.co for f in group for v in f.verts]
            size = min(max(q[k] for q in pts) - min(q[k] for q in pts) for k in range(3))
            if style == "hard":
                w = max(0.02, min(0.22, size * 0.12))
                _bevel(bm, group, w, 1 + level)
            elif style == "organic":
                _subdivide(bm, group, level, 1.0, max(0.02, size * 0.05), rng)
            else:
                _subdivide(bm, group, level, 0.0, max(0.01, size * 0.03), rng)
        out = _from_bm(bm, names)
        bm.free()
        t = _dtris(out[1])
        if t > min(HARD_CAP, hi * 1.3) and best is not None and _dtris(best[1]) >= lo * 0.5:
            break                       # the last level overshot: keep the one before
        best = out
        if t >= lo or t > HARD_CAP:
            break
    return best
