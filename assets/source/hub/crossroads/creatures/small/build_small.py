"""Crossroads V2 sky ecosystem, group SMALL: four little flyers.

    skyfinch      TINY   Verdant Valley accent   songbird, flits and perches
    lumen_moth    TINY   Ethereal Scape accent   broad pearly wings, glow veins
    cinderkite    SMALL  Emberfall accent        slim raptor, ember streamers
    prism_darter  SMALL  Astral Reach accent     star-glass dragonfly, 4 wings

Contract: docs/design/SKY_ECOSYSTEM_CONTRACT.md sections 2, 3, 4.1. Helpers and the
palette are reused READ-ONLY from build_crossroads_hub.py (runpy, as check_walkways.py
does). Orientation as the sky whale: head +X, up +Z, Y lateral.

Each creature is one body mesh `hubprop_<id>` plus rigid hinged parts
`hubprop_<id>__<part>_<n>`, every one at the body's frame (origin = body bounding-box
centre). Wings are flat at rest (mid-stroke); a positive turn about a wing's axis lifts
its tip, and the left wing's axis is mirrored so both beat together.

    python tools/run_blender.py -b --factory-startup --python build_small.py -- --export --render
"""

import json
import math
import os
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = ["x"]                       # the hub script reads argv in main() only, but be safe

g = runpy.run_path(os.path.join(HUB_DIR, "build_crossroads_hub.py"), run_name="lib")
K = g["K"]
Piece, tube, orb, box, frustum = g["Piece"], g["tube"], g["orb"], g["box"], g["frustum"]
lathe_x, part_of, tris, SUBS = g["lathe_x"], g["part_of"], g["tris"], g["SUBS"]

EXPORT_DIR = os.path.join(REPO, "assets", "export", "hub", "crossroads")
RENDER_DIR = os.path.join(HERE, "renders")
SCRATCH = os.environ.get("SMALL_SCRATCH", os.path.join(HERE, "_scratch"))
TRI_LIMIT = 10000

# New palette entries, local to this group (appended: existing indices unchanged).
K["PALETTE"].update({
    "Moss": ((100, 146, 94), False),         # Verdant accent
    "Leaf": ((150, 196, 112), False),
    "Ash": ((46, 41, 56), False),            # Emberfall: charred plate
    "EmberDeep": ((235, 104, 52), True),     # Emberfall: ember glow, deeper than Ember
    "StarGlass": ((178, 206, 255), False),   # Astral Reach: pale star-glass
    "PearlViolet": ((206, 180, 244), False), # Ethereal Scape: twilight pearl
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())
K["REFINISH"] = False                  # the Citadel detail pass needs its own palette; the hub never uses it

PM = {}                                # part name -> chain / lag / gait
SPEC = {}                              # creature id -> class, biome, target length range, built pieces


# ---- helpers ---------------------------------------------------------------------

def part(p, suffix, kind, hinge, axis, amp, rate, phase=0.0, chain=None, lag=0.0, gait="Flight"):
    q = part_of(p, suffix, kind, axis=axis, hinge=hinge, amp=amp, rate=rate, phase=phase)
    PM[q.name] = {"chain": chain.name if chain else None, "lag": lag, "gait": gait}
    return q


def prism(p, mat, pts, t=0.05):
    """A convex (or simple) polygon extruded +-t along its own normal: a wing panel."""
    pts = [Vector(q) for q in pts]
    n = Vector()
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    n.normalize()
    k = len(pts)
    verts = [tuple(q + n * t) for q in pts] + [tuple(q - n * t) for q in pts]
    faces = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))]
    for i in range(k):
        j = (i + 1) % k
        faces.append((i, j, k + j, k + i))
    p.add(verts, faces, mat, Matrix.Identity(4))


def inset(pts, f):
    c = sum((Vector(q) for q in pts), Vector()) / len(pts)
    return [c + (Vector(q) - c) * f for q in pts]


def feather(p, mat, r0, r1, w0, w1, t=0.04, tipmat=None, split=0.7):
    """A tapering blade in the XY plane from r0 to r1, optionally with a coloured tip."""
    r0, r1 = Vector(r0), Vector(r1)
    d = r1 - r0
    side = d.cross(Vector((0, 0, 1))).normalized()

    def quad(a, b, wa, wb):
        return [a + side * wa / 2, b + side * wb / 2, b - side * wb / 2, a - side * wa / 2]

    if tipmat:
        m = r0 + d * split
        wm = w0 + (w1 - w0) * split
        prism(p, mat, quad(r0, m, w0, wm), t)
        prism(p, tipmat, quad(m, r1, wm, w1), t)
    else:
        prism(p, mat, quad(r0, r1, w0, w1), t)


def gem(p, mat, c, d, r, up, down, n=5):
    """A bipyramid along direction d: a shard, a bead of glass, a flat eye-spot."""
    d = Vector(d).normalized()
    rot = d.to_track_quat("Z", "X" if abs(d.y) > 0.99 else "Y").to_matrix().to_4x4()
    verts = [(0, 0, up), (0, 0, -down)]
    verts += [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0) for i in range(n)]
    faces = []
    for i in range(n):
        a, b = 2 + i, 2 + (i + 1) % n
        faces += [(0, a, b), (1, b, a)]
    p.add(verts, faces, mat, Matrix.Translation(Vector(c)) @ rot)


def paint(p, f0, rule):
    """Recolour faces added since f0 by their centroid."""
    for i in range(f0, len(p.faces)):
        f = p.faces[i]
        c = sum((p.verts[j] for j in f), Vector()) / len(f)
        m = rule(c)
        if m:
            p.fmat[i] = m


def mirror(s, pts):
    return [(x, y * s, z) for x, y, z in pts]


def bbox(verts):
    mn = [min(v[i] for v in verts) for i in range(3)]
    mx = [max(v[i] for v in verts) for i in range(3)]
    return mn, mx


# ---- skyfinch: songbird -----------------------------------------------------------

def build_skyfinch():
    p = Piece("hubprop_skyfinch", "a songbird, head along +X; Verdant moss on cap, wing tips and tail")
    f0 = len(p.faces)
    lathe_x(p, "Basalt", [(0, -1.15), (0.2, -1.0), (0.42, -0.7), (0.6, -0.3), (0.66, 0.1), (0.58, 0.5),
                          (0.4, 0.8), (0, 0.95)], 8, "finch", sy=0.85, jitter=0.0)
    paint(p, f0, lambda c: "Marble" if c.z < -0.14 and c.x > -0.8 else (
        "Moss" if c.z > 0.34 and -0.55 < c.x < 0.25 else ("BasaltLight" if c.z > 0.1 else None)))
    for s in (-1, 1):                                                # legs and feet
        tube(p, "Gold", [(0.05, s * 0.22, -0.45), (0.1, s * 0.22, -0.85)], [0.06, 0.045], n=3)
        tube(p, "Gold", [(0.0, s * 0.22, -0.85), (0.45, s * 0.22, -0.9)], [0.045, 0.0], n=3)
    # the head: round skull, gold bill, glowing eyes
    h = part(p, "head", "Flap", hinge=(0.8, 0, 0.1), axis=(0, 1, 0), amp=0.14, rate=1.1, gait="Idle")
    orb(h, "Basalt", 0.88, 0, 0.2, 0.42, n=8)
    orb(h, "Marble", 0.98, 0, 0.0, 0.3, n=6)                         # pale cheeks and throat
    tube(h, "Gold", [(1.18, 0, 0.17), (1.62, 0, 0.07)], [0.17, 0.0], n=4)
    tube(h, "Gold", [(1.16, 0, 0.0), (1.5, 0, 0.03)], [0.11, 0.0], n=4)
    for s in (-1, 1):
        orb(h, "Shard", 1.02, s * 0.3, 0.3, 0.1, n=6)
    # crystal crest (Flicker, rides the head)
    cr = part(p, "crest", "Flicker", hinge=(0.78, 0, 0.55), axis=(0, 0, 1), amp=0.3, rate=1.3,
              chain=h, gait="Always")
    for k, (m, a) in enumerate((("Violet", 0.0), ("Rose", 0.22), ("Shard", 0.44))):
        gem(cr, m, (0.74 - a * 0.9, 0, 0.56 - a * 0.25), (-0.5 - a, 0, 1.0), 0.09, 0.4 - a * 0.3, 0.05, n=4)
    # breathing breast patch
    ch = part(p, "chest", "Pulse", hinge=(0.3, 0, -0.26), axis=(0, 0, 1), amp=0.06, rate=1.0, gait="Idle")
    f1 = len(ch.faces)
    lathe_x(ch, "Marble", [(0, -0.2), (0.3, -0.05), (0.38, 0.15), (0.3, 0.38), (0, 0.5)], 8, "chest",
            sy=0.8, x0=0.3, z0=-0.3, jitter=0.0)
    # wings: inner panel + three primaries, tips in moss
    inner, outer = {}, {}
    for s in (-1, 1):
        ax = (s, 0, 0)
        wi = part(p, "wing_in", "Flap", hinge=(0.15, s * 0.4, 0.3), axis=ax, amp=0.55, rate=6.5,
                  phase=0.0, gait="Flight")
        prism(wi, "BasaltLight", mirror(s, [(0.6, 0.35, 0.3), (0.45, 1.1, 0.33), (-0.4, 1.15, 0.33), (-0.55, 0.35, 0.3)]), 0.04)
        prism(wi, "Moss", mirror(s, [(0.55, 0.5, 0.345), (0.45, 1.05, 0.36), (0.15, 1.08, 0.36), (0.15, 0.5, 0.345)]), 0.03)
        wo = part(p, "wing_out", "Flap", hinge=(0.1, s * 1.1, 0.33), axis=ax, amp=0.4, rate=6.5,
                  phase=0.0, chain=wi, lag=0.55, gait="Flight")
        for r0, r1, w0, w1, m in (((0.35, 1.05, 0.34), (0.55, 1.85, 0.4), 0.4, 0.2, "Basalt"),
                                  ((0.05, 1.05, 0.33), (-0.05, 1.9, 0.38), 0.4, 0.2, "BasaltLight"),
                                  ((-0.3, 1.05, 0.33), (-0.55, 1.7, 0.36), 0.36, 0.16, "Basalt")):
            feather(wo, m, (r0[0], r0[1] * s, r0[2]), (r1[0], r1[1] * s, r1[2]), w0, w1, 0.035, "Moss", 0.68)
        inner[s], outer[s] = wi, wo
    # tail: a fan of three, then moss-tipped ends
    t1 = part(p, "tail", "Flap", hinge=(-1.0, 0, 0.05), axis=(0, 1, 0), amp=0.16, rate=6.5, phase=0.6,
              gait="Flight")
    t2 = part(p, "tail_tip", "Flap", hinge=(-1.7, 0, 0.05), axis=(0, 0, 1), amp=0.22, rate=1.8,
              chain=t1, lag=0.6, gait="Turn")
    for y, rz in ((0.0, 0.0), (0.16, 0.18), (-0.16, -0.18)):
        a0 = Vector((-1.0, y * 0.4, 0.05))
        a1 = Vector((-1.7 - abs(y) * 0.2, y * 1.6, 0.05))
        a2 = Vector((-2.2 - abs(y) * 0.1, y * 2.0, 0.05))
        feather(t1, "Basalt", a0, a1, 0.3, 0.26, 0.035)
        feather(t2, "Moss", a1, a2, 0.26, 0.04, 0.035)
    return p


# ---- lumen_moth: pearly wings, glow veins -----------------------------------------

def moth_wing(q, s, poly, z, veins, spot):
    pts = mirror(s, [(x, y, z) for x, y in poly])
    prism(q, "Violet", pts, 0.035)                                   # twilight border
    prism(q, "PearlViolet", inset(pts, 0.8), 0.05)                   # pearl field
    for tx, ty in veins:                                              # glowing veins
        a = (poly[0][0] * 0.3 + poly[-1][0] * 0.3, 0.25 * s, z)
        tube(q, "Shard", [a, (tx * 0.9, ty * s * 0.9, z)], [0.055, 0.035], n=3)
    gem(q, "Rose", (spot[0], spot[1] * s, z), (0, 0, 1), 0.26, 0.07, 0.07, n=6)
    gem(q, "Shard", (spot[0], spot[1] * s, z), (0, 0, 1), 0.12, 0.09, 0.09, n=5)


def build_lumen_moth():
    p = Piece("hubprop_lumen_moth", "a moth, head along +X; pearl wings, glow veins")
    f0 = len(p.faces)
    lathe_x(p, "Marble", [(0, -0.35), (0.3, -0.25), (0.5, 0.05), (0.56, 0.5), (0.46, 0.85), (0.26, 1.1), (0, 1.2)],
            8, "moth", sy=0.9, jitter=0.0,
            bands=["Cloud", "PearlViolet", "Marble", "PearlViolet", "Cloud", "Marble"])
    for s in (-1, 1):                                                # folded legs
        tube(p, "Gold", [(0.5, s * 0.25, -0.35), (0.8, s * 0.4, -0.75)], [0.045, 0.03], n=3)
        tube(p, "Gold", [(0.15, s * 0.25, -0.4), (0.15, s * 0.45, -0.8)], [0.045, 0.03], n=3)
    gem(p, "Violet", (0.45, 0, 0.55), (0.0, 0, 1.0), 0.14, 0.28, 0.0, n=5)      # a mantle shard
    h = part(p, "head", "Flap", hinge=(1.15, 0, 0.1), axis=(0, 1, 0), amp=0.12, rate=0.9, gait="Idle")
    orb(h, "PearlViolet", 1.32, 0, 0.12, 0.3, n=8)
    for s in (-1, 1):
        orb(h, "Shard", 1.5, s * 0.2, 0.2, 0.12, n=6)
    for s in (-1, 1):                                                # feathered antennae
        an = part(p, "antenna", "Flap", hinge=(1.4, s * 0.1, 0.35), axis=(0, 0, 1), amp=0.28, rate=1.4,
                  phase=0.0 if s > 0 else 1.6, chain=h, lag=0.3, gait="Idle")
        tube(an, "Gold", [(1.4, s * 0.1, 0.35), (1.85, s * 0.45, 0.8), (2.2, s * 1.0, 1.0)], [0.05, 0.04, 0.0], n=3)
        for k, (x, y, z) in enumerate(((1.7, 0.3, 0.65), (1.95, 0.55, 0.85))):
            gem(an, "Cosmic", (x, y * s, z), (0.3, s * 0.5, 0.6), 0.07, 0.28, 0.0, n=4)
    ab = part(p, "abdomen", "Pulse", hinge=(-0.35, 0, 0), axis=(0, 0, 1), amp=0.05, rate=0.8, gait="Idle")
    lathe_x(ab, "Marble", [(0, -1.7), (0.16, -1.5), (0.3, -1.0), (0.38, -0.55), (0.34, -0.2), (0, 0.0)], 8, "moth2",
            sy=0.9, jitter=0.0, bands=["Cloud", "PearlViolet", "Marble", "PearlViolet", "Cloud"])
    lan = part(p, "lantern", "Flicker", hinge=(-1.45, 0, -0.1), axis=(0, 0, 1), amp=0.3, rate=0.8,
               chain=ab, gait="Always")
    orb(lan, "Cosmic", -1.55, 0, -0.1, 0.2, n=6)
    fw = [(0.7, 0.2), (0.95, 1.1), (0.55, 2.0), (-0.3, 2.7), (-1.1, 2.0), (-1.0, 0.2)]
    hw = [(0.25, 0.2), (0.3, 0.9), (-0.4, 1.6), (-1.5, 1.7), (-2.4, 1.35), (-1.45, 0.8), (-0.95, 0.2)]
    for s in (-1, 1):
        ax = (s, 0, 0)
        w1 = part(p, "wing_fore", "Flap", hinge=(0.3, s * 0.2, 0.32), axis=ax, amp=0.6, rate=3.2, gait="Flight")
        moth_wing(w1, s, fw, 0.32, [(-0.3, 2.7), (0.55, 2.0), (-1.1, 2.0)], (-0.1, 1.5))
        w2 = part(p, "wing_hind", "Flap", hinge=(-0.1, s * 0.2, 0.2), axis=ax, amp=0.5, rate=3.2,
                  chain=w1, lag=0.5, gait="Flight")
        moth_wing(w2, s, hw, 0.2, [(-1.5, 1.7), (-2.4, 1.35), (-0.4, 1.6)], (-1.0, 1.2))
    return p


# ---- cinderkite: slim raptor with ember streamers --------------------------------

def build_cinderkite():
    p = Piece("hubprop_cinderkite", "a slim raptor, head along +X; ash plates, ember streamers")
    f0 = len(p.faces)
    lathe_x(p, "Basalt", [(0, -2.6), (0.18, -2.3), (0.4, -1.6), (0.62, -0.6), (0.78, 0.3), (0.72, 1.2),
                          (0.5, 2.0), (0.3, 2.5), (0, 2.7)], 8, "kite", sy=0.8, jitter=0.0,
            bands=["Basalt", "Ash", "Basalt", "Ash", "Basalt", "Gold", "Basalt", "Ash"])
    paint(p, f0, lambda c: "BasaltLight" if c.z < -0.25 and c.x > -1.5 else None)
    for s in (-1, 1):                                                # tucked talons
        tube(p, "Gold", [(0.2, s * 0.35, -0.55), (0.45, s * 0.35, -1.15), (0.85, s * 0.35, -1.3)],
             [0.09, 0.07, 0.0], n=3)
    for k in range(4):                                               # charred back plates
        x = -1.2 + k * 0.85
        prism(p, "Ash", [(x + 0.55, -0.32, 0.72 - k * 0.04), (x + 0.55, 0.32, 0.72 - k * 0.04),
                         (x - 0.25, 0.4, 0.74 - k * 0.04), (x - 0.25, -0.4, 0.74 - k * 0.04)], 0.05)
    h = part(p, "head", "Flap", hinge=(2.55, 0, 0.1), axis=(0, 1, 0), amp=0.12, rate=0.8, gait="Idle")
    lathe_x(h, "Basalt", [(0, 2.45), (0.4, 2.7), (0.5, 3.1), (0.42, 3.5), (0.2, 3.8), (0, 3.9)], 8, "kitehead",
            sy=0.85, z0=0.15, jitter=0.0)
    tube(h, "Gold", [(3.55, 0, 0.18), (4.2, 0, 0.12), (4.62, 0, -0.32)], [0.27, 0.17, 0.0], n=4)
    tube(h, "Gold", [(3.5, 0, 0.0), (4.1, 0, -0.1)], [0.14, 0.0], n=4)
    for s in (-1, 1):
        orb(h, "Shard", 3.15, s * 0.42, 0.34, 0.1, n=6)
        prism(h, "Ash", [(3.5, s * 0.35, 0.52), (3.1, s * 0.5, 0.58), (2.8, s * 0.45, 0.4), (3.2, s * 0.3, 0.4)], 0.05)
        prism(h, "Marble", [(2.75, s * 0.4, 0.25), (3.3, s * 0.48, 0.1), (3.2, s * 0.4, -0.2), (2.75, s * 0.35, -0.1)], 0.04)
    gl = part(p, "glow", "Flicker", hinge=(0, 0, 0.8), axis=(0, 0, 1), amp=0.3, rate=1.6, gait="Always")
    for k, (x, m) in enumerate(((1.3, "Shard"), (0.55, "Violet"), (-0.2, "Rose"), (-0.95, "Violet"))):
        gem(gl, m, (x, 0, 0.78 - k * 0.04), (-0.6, 0, 1.0), 0.17, 0.75 - k * 0.1, 0.05, n=4)
    ch = part(p, "chest", "Pulse", hinge=(1.0, 0, -0.35), axis=(0, 0, 1), amp=0.05, rate=0.9, gait="Idle")
    lathe_x(ch, "BasaltLight", [(0, 0.1), (0.5, 0.45), (0.6, 1.0), (0.45, 1.6), (0, 1.9)], 8, "kitechest", sy=0.78,
            z0=-0.3, jitter=0.0, bands=["BasaltLight", "Gold", "BasaltLight", "BasaltLight"])
    for s in (-1, 1):
        ax = (s, 0, 0)
        wi = part(p, "wing_in", "Flap", hinge=(0.6, s * 0.6, 0.35), axis=ax, amp=0.34, rate=2.2, gait="Flight")
        prism(wi, "Basalt", mirror(s, [(1.3, 0.5, 0.35), (1.1, 2.4, 0.4), (-0.7, 2.5, 0.4), (-1.3, 0.5, 0.35)]), 0.05)
        prism(wi, "Ash", mirror(s, [(0.8, 0.6, 0.4), (0.7, 2.2, 0.45), (-0.3, 2.3, 0.45), (-0.7, 0.6, 0.4)]), 0.04)
        prism(wi, "Gold", mirror(s, [(1.3, 0.5, 0.35), (1.1, 2.4, 0.4), (0.95, 2.4, 0.4), (1.1, 0.5, 0.35)]), 0.06)
        wo = part(p, "wing_out", "Flap", hinge=(0.6, s * 2.4, 0.4), axis=ax, amp=0.28, rate=2.2,
                  chain=wi, lag=0.5, gait="Flight")
        roots = [(0.9, 2.4), (0.4, 2.4), (-0.1, 2.4), (-0.6, 2.4), (-1.0, 2.4)]
        tips = [(-0.1, 5.7), (-0.7, 5.5), (-1.3, 5.1), (-1.9, 4.5), (-2.4, 3.9)]
        for i, ((rx, ry), (tx, ty)) in enumerate(zip(roots, tips)):
            feather(wo, "Basalt" if i % 2 == 0 else "BasaltLight", (rx, ry * s, 0.4), (tx, ty * s, 0.55 + 0.04 * (4 - i)),
                    0.5, 0.2, 0.04, "EmberDeep" if i < 4 else "Ember", 0.66)
    tail = part(p, "tail", "Flap", hinge=(-2.3, 0, 0.1), axis=(0, 1, 0), amp=0.14, rate=2.2, phase=0.5, gait="Flight")
    prism(tail, "Basalt", [(-2.2, -0.2, 0.1), (-2.2, 0.2, 0.1), (-3.4, 0.2, 0.1), (-3.4, -0.2, 0.1)], 0.05)
    for s in (-1, 1):
        prism(tail, "Basalt", [(-2.2, s * 0.15, 0.1), (-4.2, s * 1.0, 0.1), (-4.4, s * 0.7, 0.1), (-2.5, s * 0.1, 0.1)], 0.05)
        prism(tail, "Gold", [(-3.4, s * 0.55, 0.12), (-4.0, s * 0.95, 0.12), (-4.1, s * 0.8, 0.12), (-3.6, s * 0.5, 0.12)], 0.05)
    for s in (-1, 1):
        sa = part(p, "streamer_a", "Flap", hinge=(-4.3, s * 0.85, 0.1), axis=(0, 0, 1), amp=0.3, rate=1.7,
                  phase=0.0 if s > 0 else 0.8, chain=tail, lag=0.5, gait="Always")
        feather(sa, "Ember", (-4.3, s * 0.85, 0.1), (-5.7, s * 1.15, 0.1), 0.32, 0.26, 0.035)
        sb = part(p, "streamer_b", "Flap", hinge=(-5.7, s * 1.15, 0.1), axis=(0, 0, 1), amp=0.4, rate=1.7,
                  phase=0.0 if s > 0 else 0.8, chain=sa, lag=0.6, gait="Always")
        feather(sb, "EmberDeep", (-5.7, s * 1.15, 0.1), (-7.1, s * 1.5, 0.1), 0.26, 0.03, 0.035)
    em = part(p, "ember", "Flicker", hinge=(-2.5, 0, 0.2), axis=(0, 0, 1), amp=0.3, rate=2.3, chain=tail, gait="Always")
    for s in (-1, 1):
        gem(em, "EmberDeep", (-2.6, s * 0.18, 0.2), (-1.0, 0, 0.4), 0.15, 0.35, 0.1, n=4)
    return p


# ---- prism_darter: star-glass dragonfly -------------------------------------------

DART_L = [(1.2, 0.4), (1.3, 2.0), (1.0, 4.0), (0.4, 5.2)]
DART_T = [(-0.5, 0.4), (-0.5, 2.0), (-0.3, 4.2), (0.4, 5.2)]


def darter_wing(q, s, dx, dy, z, k=1.0):
    L = [(x * k + dx, y * dy) for x, y in DART_L]
    T = [(x * k + dx, y * dy) for x, y in DART_T]
    mats = ["StarGlass", "Cloud", "Violet"]
    for i in range(3):
        poly = [L[i], L[i + 1], T[i + 1], T[i]] if i < 2 else [L[2], L[3], T[2]]
        prism(q, mats[i], mirror(s, [(x, y, z) for x, y in poly]), 0.035)
    tube(q, "Gold", mirror(s, [(x, y, z + 0.0) for x, y in L]), [0.07, 0.07, 0.06, 0.02], n=3)    # costa
    for i in (1, 2):                                                  # prismatic cross seams
        tube(q, "Shard", mirror(s, [(L[i][0], L[i][1], z), (T[i][0], T[i][1], z)]), [0.045, 0.04], n=3)
    gem(q, "Rose", (L[2][0] - 0.05, L[2][1] * s + 0.0, z), (0, 0, 1), 0.2, 0.08, 0.08, n=5)          # stigma


def build_prism_darter():
    p = Piece("hubprop_prism_darter", "a star-glass dragonfly, head along +X; four glass wings")
    f0 = len(p.faces)
    lathe_x(p, "Basalt", [(0, -0.9), (0.4, -0.75), (0.7, -0.35), (0.84, 0.2), (0.72, 0.75), (0.4, 1.05), (0, 1.15)],
            8, "darter", sy=0.85, jitter=0.0)
    paint(p, f0, lambda c: "StarGlass" if c.z < -0.3 else ("BasaltLight" if c.z > 0.4 and abs(c.y) > 0.25 else None))
    for s in (-1, 1):                                                # three pairs of folded legs
        for k, x in enumerate((0.7, 0.25, -0.2)):
            tube(p, "Gold", [(x, s * 0.35, -0.5), (x + 0.35, s * 0.55, -1.0), (x + 0.85, s * 0.5, -1.2)],
                 [0.06, 0.05, 0.0], n=3)
    h = part(p, "head", "Flap", hinge=(1.1, 0, 0.1), axis=(0, 0, 1), amp=0.25, rate=0.9, gait="Idle")
    orb(h, "Basalt", 1.45, 0, 0.0, 0.5, n=8)
    for s in (-1, 1):
        orb(h, "Shard", 1.62, s * 0.55, 0.2, 0.52, n=8)              # the compound eyes
        orb(h, "StarGlass", 1.72, s * 0.7, 0.32, 0.18, n=6)
    tube(h, "Gold", [(1.85, 0, -0.2), (2.15, 0, -0.35)], [0.17, 0.0], n=4)
    ch = part(p, "chest", "Pulse", hinge=(0.2, 0, -0.5), axis=(0, 0, 1), amp=0.05, rate=1.0, gait="Idle")
    lathe_x(ch, "StarGlass", [(0, -0.55), (0.45, -0.3), (0.55, 0.2), (0.4, 0.65), (0, 0.9)], 8, "dchest", sy=0.8,
            z0=-0.45, jitter=0.0, bands=["StarGlass", "Gold", "StarGlass", "StarGlass"])
    star = part(p, "star", "Flicker", hinge=(0.1, 0, 0.8), axis=(0, 0, 1), amp=0.3, rate=1.2, gait="Always")
    for x, m, r, up in ((0.6, "Violet", 0.17, 0.6), (0.0, "Shard", 0.2, 0.75), (-0.5, "Rose", 0.15, 0.5)):
        gem(star, m, (x, 0, 0.78), (-0.4, 0, 1.0), r, up, 0.05, n=5)
    # abdomen: three chained segments, gold-banded, with an inlay ridge
    prev, x0 = None, -0.8
    segs = [("abd_a", -0.8, -3.6, 0.38), ("abd_b", -3.6, -6.2, 0.31), ("abd_c", -6.2, -8.4, 0.26)]
    for name, xa, xb, r in segs:
        a = part(p, name, "Flap", hinge=(xa, 0, 0.05), axis=(0, 1, 0), amp=0.1, rate=1.0,
                 phase=0.0, chain=prev, lag=0.45 if prev else 0.0, gait="Flight")
        a0 = len(a.faces)
        lathe_x(a, "Basalt", [(0, xa + 0.15), (r * 0.8, xa), (r, xa - 0.5), (r * 0.9, (xa + xb) / 2),
                              (r * 0.82, xb + 0.5), (r * 0.7, xb), (0, xb - 0.1)], 6, name,
                sy=0.9, jitter=0.0, bands=["Gold", "Basalt", "Basalt", "Basalt", "Gold", "Basalt"])
        paint(a, a0, lambda c: "Inlay" if c.z > 0.26 * r and abs(c.y) < 0.06 else ("Gold" if c.z < -0.2 * r else None))
        prev = a
    tip = part(p, "tip", "Flicker", hinge=(-8.4, 0, 0.05), axis=(0, 0, 1), amp=0.3, rate=1.8, chain=prev, gait="Always")
    for s in (-1, 1):
        gem(tip, "Violet", (-8.5, s * 0.15, 0.05), (-1.0, s * 0.35, 0.0), 0.1, 0.55, 0.05, n=4)
    gem(tip, "Shard", (-8.5, 0, 0.05), (-1.0, 0, 0.0), 0.13, 0.5, 0.05, n=4)
    fores, hinds = {}, {}
    for s in (-1, 1):
        ax = (s, 0, 0)
        w1 = part(p, "wing_fore", "Flap", hinge=(0.7, s * 0.5, 0.55), axis=ax, amp=0.3, rate=8.0, gait="Flight")
        darter_wing(w1, s, 0.8, 1.0, 0.55)
        w2 = part(p, "wing_hind", "Flap", hinge=(-0.4, s * 0.5, 0.45), axis=ax, amp=0.3, rate=8.0,
                  phase=3.14159, gait="Flight")
        darter_wing(w2, s, -1.7, 0.95, 0.45, k=1.12)
    return p


BUILDERS = (
    ("skyfinch", build_skyfinch, "TINY", ["VERDANT_VALLEY"], (3.0, 4.0), 900),
    ("lumen_moth", build_lumen_moth, "TINY", ["ETHEREAL_SCAPE"], (4.0, 6.0), 1000),
    ("cinderkite", build_cinderkite, "SMALL", ["EMBERFALL"], (9.0, 12.0), 1800),
    ("prism_darter", build_prism_darter, "SMALL", ["ASTRAL_REACH"], (10.0, 14.0), 1800),
)
TARGET = {"skyfinch": 3.6, "lumen_moth": 5.4, "cinderkite": 11.0, "prism_darter": 12.0}


# ---- assembly --------------------------------------------------------------------

def finish(cid, builder, cls, biome, rng, tri_cap):
    before = len(SUBS)
    p = builder()
    subs = SUBS[before:]
    allp = [p] + subs
    # scale so the whole creature at rest has its longest dimension at TARGET
    mn, mx = bbox([v for q in allp for v in q.verts])
    k = TARGET[cid] / max(mx[i] - mn[i] for i in range(3))
    bmn, bmx = bbox(p.verts)
    c = Vector([(bmn[i] + bmx[i]) / 2 for i in range(3)])          # body bounding-box centre = pivot
    for q in allp:
        q.verts = [(v - c) * k for v in q.verts]
        if q is not p:
            q.meta["hinge"] = [round(float((Vector(q.meta["hinge"]) - c)[i] * k), 3) for i in range(3)]
    mn, mx = bbox([v for q in allp for v in q.verts])
    size = [round(mx[i] - mn[i], 3) for i in range(3)]
    assert rng[0] <= max(size) <= rng[1], f"{cid} longest {max(size):.2f} outside {rng}"
    total = sum(tris(q) for q in allp)
    assert total <= tri_cap, f"{cid} {total} tris over {tri_cap}"
    assert all(tris(q) < TRI_LIMIT for q in allp)
    return p, subs, size, total, k


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K["ensure_materials"]()
    coll = bpy.data.collections.new("Crossroads_Small")
    bpy.context.scene.collection.children.link(coll)
    objs, side = [], {"group": "small", "creatures": {}}
    by_creature = {}
    for cid, builder, cls, biome, rng, cap in BUILDERS:
        p, subs, size, total, k = finish(cid, builder, cls, biome, rng, cap)
        bo = K["to_object"](p, mats, coll)
        bo["tris"] = tris(p)
        group = [bo]
        parts = {}
        for q in subs:
            o = K["to_object"](q, mats, coll)
            o["tris"] = tris(q)
            group.append(o)
            mn, mx = bbox(q.verts)
            m = q.meta
            parts[q.name] = {
                "kind": m["kind"],
                "offset": [round((mn[i] + mx[i]) / 2, 3) for i in range(3)],
                "hinge": m["hinge"], "axis": m["axis"],
                "amp": m["amp"], "rate": m["rate"], "phase": round(m["phase"], 4),
                "chain": PM[q.name]["chain"], "lag": PM[q.name]["lag"], "gait": PM[q.name]["gait"]}
        objs += group
        by_creature[cid] = (group, size, total)
        side["creatures"][cid] = {"model": p.name, "class": cls, "size": size, "tris": total,
                                  "biome": biome, "parts": parts}
        print(f"CREATURE {cid:13s} {cls:6s} size {size} tris {total} (body {tris(p)}) parts {len(subs)} scale {k:.3f}")
        for o in group:
            print(f"   {o.name:46s} {o['tris']:5d}")
    if "--export" in ARGV:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        K["_export_selected"](objs, os.path.join(EXPORT_DIR, "creatures_small.fbx"))
        with open(os.path.join(EXPORT_DIR, "creatures_small.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(side, fh, indent=1)
            fh.write("\n")
        print("EXPORTED creatures_small.fbx / .json")
    if "--render" in ARGV:
        render(by_creature)


# ---- review renders --------------------------------------------------------------

def render(by_creature):
    import numpy as np
    ns = runpy.run_path(os.path.join(HUB_DIR, "render_crossroads.py"), run_name="rr")
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)
    ns["setup_world"]()
    bpy.data.worlds["Hub_Sky"].node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.36, 0.62, 1)
    sc = bpy.context.scene
    cw, ch = 600, 420
    sc.render.resolution_x, sc.render.resolution_y = cw, ch
    views = []
    for cid, (group, size, total) in by_creature.items():
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.hide_render = o not in group
        L = max(size)
        ctr = Vector((0, 0, 0))
        cells = []
        for vi, (name, off, ortho) in enumerate((("iso", (0.55, -0.75, 0.42), None), ("top", (0, 0.001, 1), True),
                                                 ("front", (1, 0.0, 0.12), None))):
            d = Vector(off).normalized()
            if ortho:
                ns["shot"](f"{cid}_{name}", d * L * 3, ctr, 50, SCRATCH, ortho=L * 1.35)
            else:
                ns["shot"](f"{cid}_{name}", d * L * 1.75, ctr, 50, SCRATCH)
            cells.append(os.path.join(SCRATCH, f"{cid}_{name}.jpg"))
        views.append(cells)
    sheet = np.ones((ch * 3, cw * len(views), 4), dtype=np.float32)
    for ci, cells in enumerate(views):
        for ri, path in enumerate(cells):
            im = bpy.data.images.load(path)
            a = np.empty(im.size[0] * im.size[1] * 4, dtype=np.float32)
            im.pixels.foreach_get(a)
            a = a.reshape(im.size[1], im.size[0], 4)
            y0 = (2 - ri) * ch                                     # image rows are bottom-up
            sheet[y0:y0 + ch, ci * cw:(ci + 1) * cw] = a
    out = bpy.data.images.new("sheet", cw * len(views), ch * 3)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = os.path.join(RENDER_DIR, "contact_sheet.jpg")
    out.file_format = "JPEG"
    out.save()
    print("SHEET", out.filepath_raw)


if __name__ == "__main__":
    main()
