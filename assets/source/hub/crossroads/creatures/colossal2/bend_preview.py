"""Cinder wyrm trail-following bend check (contract section 7 item 4).

The runtime places each `body_a_*` segment on the trail the head has travelled and orients it to the path tangent
there, with a travelling lateral wave (sidecar `spine`).  This harness does the same at the wave's MAXIMUM curvature
and measures whether consecutive segments stay closed at their joints: from points all round the joint circle it
casts a ray inward to the hinge; a ray that reaches the hinge without hitting either segment is a see-through gap.

    python tools/run_blender.py -b --factory-startup --python bend_preview.py -- [--final] [--plane vertical]

Prints, per joint, the worst bend angle and the open fraction / opening, and writes a sheet to renders/.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_colossal2 as B   # noqa: E402

K = B.K
WAVELENGTH = 350.0
AMP = 32.0


def path_points(vertical, n=4000, length=1000.0):
    """Arc-length parameterised trail: head at u=0 travelling +X; the trail trails toward -X along the wave."""
    pts = []
    x = 0.0
    dx = length / n
    for i in range(n):
        s = AMP * math.sin(2 * math.pi * x / WAVELENGTH + math.pi / 2)    # max curvature region of the wave
        pts.append(Vector((-x, 0.0, s)) if vertical else Vector((-x, s, 0.0)))
        x += dx
    # re-sample by arc length
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + (b - a).length)
    return pts, cum


def at(pts, cum, u):
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if cum[m] <= u:
            lo = m
        else:
            hi = m
    t = (u - cum[lo]) / max(1e-9, cum[hi] - cum[lo])
    p = pts[lo].lerp(pts[hi], t)
    tg = (pts[hi] - pts[lo]).normalized()
    return p, tg


def place(piece, hinge, p, tg):
    """Rigid placement: the segment's hinge goes to p, its +X axis (head direction) to the path direction towards the head."""
    head = -tg                                  # path runs from head to tail, the head direction is back along it
    ang = math.atan2(head.y, head.x)
    elev = math.asin(max(-1, min(1, head.z)))
    r = Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(-elev, 4, "Y")
    m = Matrix.Translation(p) @ r @ Matrix.Translation(-Vector(hinge))
    return [m @ v for v in piece.verts], m


def run(vertical, out_dir):
    c = B.build_wyrm()
    B.finalize(c)
    segs = [(q, m) for q, m in c.parts if q.name.startswith("hubprop_cinder_wyrm__body_a_")]
    segs.sort(key=lambda t: int(t[0].name.rsplit("_", 1)[1]))
    pts, cum = path_points(vertical)
    posed = []
    for i, (q, m) in enumerate(segs):
        s0 = segs[0][1]["hinge"][0] - m["hinge"][0]     # arc distance behind the first segment's hinge
        p, tg = at(pts, cum, s0)
        vs, mat = place(q, m["hinge"], p, tg)
        posed.append((vs, mat, s0, p))
    trees = [BVHTree.FromPolygons(vs, [tuple(f) for f in q.faces], epsilon=0.0) for (vs, _m, _s, _p), (q, _mm) in zip(posed, segs)]
    worst_open = 0.0
    print("joint  bend_deg  open_frac  max_open_studs")
    for i in range(1, len(segs)):
        (_vs, mat, s0, p) = posed[i]
        (_vs0, mat0, _s00, _p0) = posed[i - 1]
        ax_dir = (mat.to_3x3() @ Vector((1, 0, 0))).normalized()
        prev_dir = (mat0.to_3x3() @ Vector((1, 0, 0))).normalized()
        bend = math.degrees(ax_dir.angle(prev_dir))
        ref = (ax_dir + prev_dir).normalized()
        u = ref.cross(Vector((0, 0, 1) if not vertical else (0, 1, 0)))
        u = u.normalized() if u.length > 1e-6 else Vector((0, 1, 0))
        v = ref.cross(u).normalized()
        rad = B.wr(s0) * 1.3 + 30
        n_open = 0
        opening = 0.0
        N = 72
        for k in range(N):
            a = 2 * math.pi * k / N
            d = (u * math.cos(a) + v * math.sin(a))
            o = p + d * rad
            # cast along -d toward the hinge; closed if either neighbour is hit before the axis
            hit = False
            for t in (trees[i], trees[i - 1]):
                loc, _n, _i, dist = t.ray_cast(o, -d, rad)
                if loc is not None:
                    hit = True
                    break
            if not hit:
                n_open += 1
                # opening size: distance along the seam direction where a parallel ray first hits
                best = 1e9
                for off in range(1, 40):
                    for sgn in (-1, 1):
                        o2 = o + ref * (off * 0.5 * sgn)
                        for t in (trees[i], trees[i - 1]):
                            loc, _n, _i, dist = t.ray_cast(o2, -d, rad)
                            if loc is not None:
                                best = min(best, off * 0.5)
                opening = max(opening, best if best < 1e9 else 20.0)
        worst_open = max(worst_open, n_open / N)
        print("%2d-%2d  %7.1f  %8.3f  %8.1f" % (i, i + 1, bend, n_open / N, opening))
    print("WORST open fraction", round(worst_open, 3))
    # render the posed chain
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K["ensure_materials"]()
    C1 = B.C1
    C1["_scene_setup"]()
    coll = bpy.context.scene.collection
    objs = []
    for (vs, _m, _s, _p), (q, _mm) in zip(posed, segs):
        piece = K["Piece"](q.name + "_bend", "bend")
        piece.verts = vs
        piece.faces = [list(f) for f in q.faces]
        piece.fmat = list(q.fmat)
        piece.ftag = list(q.ftag)
        objs.append(K["to_object"](piece, mats, coll))
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in objs:
        for cn in o.bound_box:
            for i in range(3):
                lo[i] = min(lo[i], cn[i])
                hi[i] = max(hi[i], cn[i])
    cen = (lo + hi) * 0.5
    bpy.context.scene.render.resolution_x = 1000
    bpy.context.scene.render.resolution_y = 420
    tag = "vertical" if vertical else "lateral"
    top = (0, 0, -1.0) if not vertical else (0, -1.0, 0)
    tiles = [C1["_shot"]("bend_%s_full" % tag, cen + Vector(top).normalized() * 1500 + Vector((0.0, -0.001, 0.0)), cen, out_dir, lens=35)]
    # close-up on the sharpest joint
    pc = posed[6][3]
    tiles.append(C1["_shot"]("bend_%s_close" % tag, pc + Vector(top).normalized() * 330 + Vector((0.0, -0.001, 0.0)), pc, out_dir, lens=35))
    side = (0.35, -0.35, 0.8) if not vertical else (0.35, -0.8, 0.35)
    tiles.append(C1["_shot"]("bend_%s_3q" % tag, pc + Vector(side).normalized() * 420, pc, out_dir, lens=35))
    C1["_sheet"](tiles, 1, os.path.join(out_dir, "cinder_wyrm_bend_%s.jpg" % tag))
    print("BENDSHEET", os.path.join(out_dir, "cinder_wyrm_bend_%s.jpg" % tag))


def main(argv):
    final = "--final" in argv
    out_dir = B.RENDER_DIR if final else B.SCRATCH
    os.makedirs(out_dir, exist_ok=True)
    run("vertical" in argv or ("--plane" in argv and argv[argv.index("--plane") + 1] == "vertical"), out_dir)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
