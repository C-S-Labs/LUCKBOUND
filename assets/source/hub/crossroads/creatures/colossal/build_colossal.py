"""Crossroads V2 sky ecosystem: the two COLOSSAL hero creatures.

    starweaver         Astral Reach jelly-like celestial: stepped star-glass bell, halo ring, a pulsing skirt and
                       heart, four chained tendrils.
    elder_greatturtle  Verdant island-backed sky turtle: a breathing scute shell carrying a grove and a ruin,
                       crystal growth, head on a jointed neck, four paddle flippers.

Contract: docs/design/SKY_ECOSYSTEM_CONTRACT.md sections 2, 3, 4.1. Built at FINAL stud size (the Roblox side
scales nothing). Orientation: head +X, up +Z (as the whale). Every mesh sits at its own origin in body-local
coordinates, the body's bounding-box centre is the creature's origin, and each creature is ONE body mesh
`hubprop_<id>` plus rigid hinged parts `hubprop_<id>__<part>_<n>`.

Helpers (palette, Piece, box, crystal, torus, tube, ...) come from build_crossroads_hub.py read-only, by runpy,
exactly as check_walkways.py does. Nothing outside this folder and the two export files is written.

    python tools/run_blender.py -b --factory-startup --python build_colossal.py -- --export --render
    (--render writes scratch renders to the scratchpad; add --final to write renders/ into this folder)
"""

import json
import math
import os
import random
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
EXPORT_DIR = os.path.join(REPO, "assets", "export", "hub", "crossroads")
FBX_PATH = os.path.join(EXPORT_DIR, "creatures_colossal.fbx")
JSON_PATH = os.path.join(EXPORT_DIR, "creatures_colossal.json")

_saved_argv = list(sys.argv)
sys.argv = ["x"]
G = runpy.run_path(os.path.join(HUB_DIR, "build_crossroads_hub.py"), run_name="lib")   # read-only helper import
sys.argv = _saved_argv
K = G["K"]
Piece, box, frustum, crystal, torus, torus_arc, tube, orb, xf, frame = (
    K[n] for n in ("Piece", "box", "frustum", "crystal", "torus", "torus_arc", "tube", "orb", "xf", "frame"))

TRI_LIMIT = 10000
ROBLOX_MESH_LIMIT = 2048

# Species-only palette entries (the contract allows these in the species' own script). Everything else is the
# existing hub table (Marble, Gold, Shard, Violet, Rose, Cosmic, Inlay, Basalt, Wood, Water, Sand ...).
K["PALETTE"].update({
    "StarGlass": ((142, 148, 238), False),      # Astral Reach: pale prismatic glass
    "StarGlassDeep": ((92, 84, 186), False),
    "Moss": ((92, 132, 66), False),             # Verdant accent
    "MossDark": ((60, 96, 54), False),
    "Leaf": ((118, 172, 86), False),
    "LeafDark": ((66, 118, 70), False),
    "TurtleSkin": ((88, 116, 100), False),
    "TurtleBelly": ((196, 188, 150), False),
    "Bark": ((98, 72, 54), False),
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())
K["REFINISH"] = False    # the Sky Citadel refinish pass is keyed to the Citadel palette; the hub script never reaches it


# ---------------------------------------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------------------------------------
def tris(p):
    return sum(len(f) - 2 for f in p.faces)


def soup(p, verts, faces, mats):
    base = len(p.verts)
    p.verts.extend(p.base @ Vector(v) for v in verts)
    p.faces.extend([base + i for i in f] for f in faces)
    p.fmat.extend(mats)
    p.ftag.extend(["colossal"] * len(faces))


def ell(a, r, sy=1.0):
    return (r * math.cos(a), r * sy * math.sin(a))


def lathe(p, prof, n, matfn, sx=1.0, sy=1.0, cx=0.0, cy=0.0, jit=0.0, seed="", cap_bottom="Basalt", cap_top=True):
    """Lathe about Z. prof: [(r, z, tag)] with the tag naming the segment that ENDS at that point.
    matfn(tag, k, c) -> palette name for ring-pair k, column c."""
    rng = random.Random(seed)
    cols = [1.0 + rng.uniform(-jit, jit) for _ in range(n)]
    verts, rings = [], []
    for r, z, _t in prof:
        if r <= 1e-6:
            verts.append((cx, cy, z))
            rings.append([len(verts) - 1])
            continue
        ring = []
        for c in range(n):
            a = 2 * math.pi * c / n
            verts.append((cx + math.cos(a) * r * cols[c] * sx, cy + math.sin(a) * r * cols[c] * sy, z))
            ring.append(len(verts) - 1)
        rings.append(ring)
    faces, mats = [], []
    for k, (A, B) in enumerate(zip(rings, rings[1:])):
        tag = prof[k + 1][2]
        if len(A) > 1 and len(B) > 1:
            for c in range(n):
                faces.append((A[c], A[(c + 1) % n], B[(c + 1) % n], B[c]))
                mats.append(matfn(tag, k, c))
        elif len(B) == 1:
            for c in range(n):
                faces.append((A[c], A[(c + 1) % n], B[0]))
                mats.append(matfn(tag, k, c))
        else:
            for c in range(n):
                faces.append((A[0], B[(c + 1) % n], B[c]))
                mats.append(matfn(tag, k, c))
    if len(rings[0]) > 1 and cap_bottom:
        faces.append(tuple(reversed(rings[0])))
        mats.append(cap_bottom)
    if len(rings[-1]) > 1 and cap_top:
        faces.append(tuple(rings[-1]))
        mats.append(matfn(prof[-1][2], len(rings) - 2, 0))
    soup(p, verts, faces, mats)


def ellipsoid(p, mat, cx, cy, cz, rx, ry, rz, n=8, steps=4):
    prof = [(0.0, rz, "e")]
    for i in range(1, steps):
        th = math.pi * i / steps
        prof.append((math.sin(th) * rx, math.cos(th) * rz, "e"))
    prof.append((0.0, -rz, "e"))
    prof.reverse()
    lathe(p, prof, n, lambda t, k, c: mat, sy=ry / rx, cx=cx, cy=cy, cap_bottom=mat)


def ell_solid(p, mat, cx, cy, cz, rx, ry, rz, n=8, steps=4):
    before = len(p.verts)
    ellipsoid(p, mat, 0.0, 0.0, 0.0, rx, ry, rz, n, steps)
    off = p.base @ Vector((cx, cy, cz)) - p.base @ Vector((0, 0, 0))
    for i in range(before, len(p.verts)):
        p.verts[i] = p.verts[i] + off


def shard(p, mat, x, y, z, r, up, down=0.0, n=5, a=0.0, tilt=0.0):
    """A crystal leaning `tilt` degrees toward heading `a` (degrees about Z)."""
    with frame(p, xf(x, y, z, rz=a, ry=tilt)):
        crystal(p, mat, 0, 0, 0, r, up, down, n)


def blade(p, mat, pts, widths, thicks, up=(0, 0, 1)):
    """A flat lens-section ribbon along a path (paddles, frills, veils)."""
    pts = [Vector(q) for q in pts]
    n = len(pts)
    verts, faces, rings = [], [], []
    for i, c in enumerate(pts):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        t.normalize()
        s = t.cross(Vector(up))
        if s.length < 1e-6:
            s = t.orthogonal()
        s.normalize()
        u = s.cross(t).normalized()
        w, h = max(widths[i], 0.4), max(thicks[i], 0.25)
        ring = []
        for a, b in ((-w, 0), (-w * 0.5, h), (w * 0.5, h), (w, 0), (w * 0.5, -h), (-w * 0.5, -h)):
            verts.append(tuple(c + s * a + u * b))
            ring.append(len(verts) - 1)
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for k in range(6):
            faces.append((A[k], A[(k + 1) % 6], B[(k + 1) % 6], B[k]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))
    soup(p, verts, faces, [mat] * len(faces))


def anchor(p, centre):
    """Make the mesh bbox centre exactly `centre` by adding two 0.4-stud hidden tetrahedra at mirrored extremes.
    The client scales a Pulse part about its bbox centre, so this fixes WHERE a pulse scales from."""
    lo, hi = bbox(p)
    c = Vector(centre)
    nlo = Vector((min(lo[i], 2 * c[i] - hi[i]) for i in range(3)))
    nhi = Vector((max(hi[i], 2 * c[i] - lo[i]) for i in range(3)))
    for tgt0, bound, sg in ((nlo, lo, 1), (nhi, hi, -1)):
        tgt = Vector((tgt0[i] if abs(tgt0[i] - bound[i]) > 1e-6 else c[i] for i in range(3)))
        e = 0.4 * sg
        v = [tuple(tgt), (tgt.x + e, tgt.y, tgt.z), (tgt.x, tgt.y + e, tgt.z), (tgt.x, tgt.y, tgt.z + e)]
        soup(p, v, [(0, 2, 1), (0, 1, 3), (1, 2, 3), (0, 3, 2)], ["Basalt"] * 4)


def lerp(a, b, t):
    return a + (b - a) * t


def basis_ring(p, mat, pos, tangent, axis, R, r, n=8, m=4):
    """A torus whose ring axis is `axis`, centred at pos (a chain link)."""
    x = Vector(tangent).normalized()
    z = Vector(axis).normalized()
    y = z.cross(x).normalized()
    x = y.cross(z).normalized()
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(pos)
    with frame(p, M):
        torus(p, mat, R, r, 0, 0, 0, n=n, m=m)


# ---------------------------------------------------------------------------------------------------------
# Creature record
# ---------------------------------------------------------------------------------------------------------
class Creature:
    def __init__(self, cid, cls, biome, notes):
        self.id, self.cls, self.biome = cid, cls, biome
        self.body = Piece(f"hubprop_{cid}", notes)
        self.parts = []          # (Piece, meta)
        self._n = {}

    def part(self, suffix, kind, hinge, axis, amp, rate, phase=0.0, chain=None, lag=0.0, gait="Always"):
        self._n[suffix] = self._n.get(suffix, 0) + 1
        q = Piece(f"{self.body.name}__{suffix}_{self._n[suffix]}", kind)
        ax = Vector(axis).normalized()
        self.parts.append((q, {"kind": kind, "hinge": Vector(hinge), "axis": ax, "amp": amp, "rate": rate,
                               "phase": phase, "chain": chain.name if chain else None, "lag": lag,
                               "gait": gait}))
        return q


# ---------------------------------------------------------------------------------------------------------
# STARWEAVER
# ---------------------------------------------------------------------------------------------------------
SY = 0.84                        # the bell is longer than it is wide (head +X)
BELL_N = 32


def star_matfn(seed):
    rng = random.Random(seed)

    def f(tag, k, c):
        if tag in ("t1", "t2", "t3"):
            r = rng.random()
            if r < 0.07:
                return "Shard"
            if r < 0.12:
                return "Violet"
            return "StarGlass" if c % 2 == 0 else "StarGlassDeep"
        if tag in ("l1", "l2"):
            return "Marble" if c % 2 == 0 else "MarbleDim"
        if tag == "lip":
            return "Gold"
        return "StarGlassDeep" if c % 2 == 0 else "Violet"
    return f


BELL = [(270, -12, "x"), (282, -2, "lip"), (284, 14, "lip"), (276, 44, "t1"), (262, 72, "t1"), (262, 76, "l1"),
        (240, 80, "l1"), (236, 100, "t2"), (214, 126, "t2"), (200, 138, "t2"), (200, 141, "l2"), (176, 146, "l2"),
        (170, 160, "t3"), (140, 180, "t3"), (104, 194, "t3"), (76, 200, "cap"), (44, 208, "cap"), (0, 214, "cap")]
GLOW = ("Shard", "Violet", "Rose")


def starweaver_body(c):
    p = c.body
    lathe(p, BELL, BELL_N, star_matfn("starweaver bell"), sy=SY, cap_bottom="Basalt")
    # sixteen meridian ribs of marble, every fourth in gold, lying over the steps
    for j in range(16):
        a = 2 * math.pi * (j + 0.0) / 16
        pts = [(*ell(a, r * 1.025, SY), z) for r, z, _t in BELL[2:-1]] + [(0, 0, 217)]
        rad = [7.0 - 3.0 * i / len(pts) for i in range(len(pts) - 1)] + [0.5]
        tube(p, "Gold" if j % 4 == 0 else "Marble", pts, rad, n=4)
    # glow diamonds set flush in every panel of the three tiers
    for tier, (r, z, up) in enumerate(((272, 56, 14), (224, 112, 12), (156, 168, 10))):
        for j in range(BELL_N):
            if j % 2:
                continue
            a = 2 * math.pi * (j + 0.5) / BELL_N
            x, y = ell(a, r * 1.01, SY)
            shard(p, GLOW[(j // 2 + tier) % 3], x, y, z, 6.5, up, 3, n=4, a=math.degrees(a), tilt=70)
    # crystal growth along both ledges, and on the crown shoulder
    for j in range(16):
        a = 2 * math.pi * (j + 0.5) / 16
        x, y = ell(a, 252, SY)
        shard(p, GLOW[j % 3], x, y, 78, 8, 26 + (j % 3) * 8, 6, n=5, a=math.degrees(a), tilt=24)
        x, y = ell(a, 190, SY)
        shard(p, GLOW[(j + 1) % 3], x, y, 144, 7, 22 + (j % 2) * 10, 5, n=5, a=math.degrees(a), tilt=18)
    for j in range(8):
        a = 2 * math.pi * j / 8 + 0.2
        x, y = ell(a, 62, SY)
        shard(p, GLOW[(j + 2) % 3], x, y, 204, 10, 62 + (j % 2) * 20, 6, n=5, a=math.degrees(a), tilt=14)
    # the crown: a great spear of star-glass in a gold collar, ringed by lesser spears
    shard(p, "Shard", 0, 0, 210, 30, 125, 18, n=6)
    shard(p, "Violet", 0, 0, 226, 20, 150, 10, n=6, a=30, tilt=0)
    frustum(p, "Gold", 12, 46, 36, 208, 222)
    for j in range(6):
        a = math.radians(60 * j + 15)
        shard(p, GLOW[j % 3], math.cos(a) * 36, math.sin(a) * 36, 214, 14, 92 + (j % 2) * 24, 6, n=5,
              a=math.degrees(a), tilt=22)
    # the prow: two swept spears and a gold brow horn, so the heading reads at distance
    for s, col in ((1, "Violet"), (-1, "Rose")):
        shard(p, col, 262, s * 62, 44, 15, 130, 10, n=5, a=-s * 12, tilt=72)
    tube(p, "Gold", [(268, 0, 34), (306, 0, 50), (336, 0, 70), (352, 0, 92)], [15, 12, 7, 1], n=6)
    shard(p, "Cosmic", 350, 0, 96, 9, 26, 6, n=5, tilt=40)
    # the underside: radial inlay spokes, a collar for the heart, sockets for the four tendrils
    for j in range(8):
        a = 2 * math.pi * j / 8
        L = 250 * math.hypot(math.cos(a), SY * math.sin(a))
        mid = (L + 70) / 2
        box(p, "Inlay", math.cos(a) * mid, math.sin(a) * mid * SY, -13.5, L - 70, 7, 3,
            rz=math.degrees(math.atan2(SY * math.sin(a), math.cos(a))))
    frustum(p, "Gold", 12, 52, 36, -12, -40)
    frustum(p, "Marble", 12, 36, 26, -40, -64)
    for az in TEND_AZ:
        a = math.radians(az)
        frustum(p, "Gold", 8, 20, 14, -12, -24, math.cos(a) * 150, math.sin(a) * 150)
        orb(p, "Cosmic", math.cos(a) * 150, math.sin(a) * 150, -24, 7, n=6)


def starweaver_skirt(c):
    # THRUST BELL: contracts and relaxes in bursts (Flight gait: rate and depth follow speed). Scales about the
    # bell/skirt junction (anchor), so the top stays tucked under the lip and the rim breathes in and out.
    q = c.part("skirt", "Pulse", hinge=(0, 0, 0), axis=(0, 0, 1), amp=0.14, rate=0.22, phase=0.0, gait="Flight")
    band = [(246, 12, "x"), (262, -8, "b"), (280, -34, "b"), (292, -60, "b"), (296, -66, "r")]
    lathe(q, band, 32, lambda t, k, cc: "Gold" if t == "r" else ("StarGlassDeep" if cc % 2 == 0 else "Violet"),
          sy=SY, cap_bottom="StarGlassDeep")
    for j in range(32):
        a = 2 * math.pi * j / 32
        long_ = j % 2 == 0
        L = 1.0 if long_ else 0.58
        bx, by = ell(a, 294, SY)
        pts = [(bx, by, -62)]
        for t in (0.25, 0.5, 0.75, 1.0):
            rr = 294 + 8 * math.sin(t * math.pi) - 14 * t * t
            x, y = ell(a, rr, SY)
            pts.append((x, y, -62 - 172 * L * t))
        rad = [17, 16, 12, 7, 0.8]
        mat = "Gold" if j % 4 == 0 else ("Marble" if long_ else "StarGlass")
        tube(q, mat, pts, rad, n=4)
        ex, ey, ez = pts[-1]
        orb(q, "Cosmic" if j % 4 == 0 else GLOW[j % 3], ex, ey, ez - 3, 5.5, n=6)
    for j in range(16):
        a = 2 * math.pi * (j + 0.5) / 16
        pts = [(*ell(a, 286 + 6 * t, SY), -64 - 100 * t) for t in (0, 0.5, 1.0)]
        blade(q, "StarGlass", pts, [26, 22, 6], [1.2, 1.0, 0.6], up=(math.cos(a), math.sin(a), 0))
    anchor(q, (0, 0, 0))
    return q


def starweaver_fringe(c, skirt):
    # RIM FRINGE: 72 short thin tentacles on a gold cuff, chained to the skirt, pulsing a short beat behind it (0.4 rad: the cuff
    # slips at most ~14 studs off the rim) so the contraction visibly travels down the bell. Same scale centre as the skirt (anchor) so the cuff stays on the rim.
    q = c.part("fringe", "Pulse", hinge=(0, 0, 0), axis=(0, 0, 1), amp=0.14, rate=0.22, phase=-0.4, chain=skirt,
               gait="Flight")
    cuff = [(289, -46, "x"), (298, -58, "c"), (300, -76, "c"), (292, -88, "c")]
    lathe(q, cuff, 36, lambda t, k, cc: "Gold" if cc % 3 == 0 else "Marble", sy=SY, cap_bottom=None, cap_top=False)
    n = 72
    for j in range(n):
        a = 2 * math.pi * (j + 0.25) / n
        L = (86, 118, 100, 132)[j % 4]
        sway = 0.10 * math.sin(j * 1.3)
        pts = []
        for t in (0.0, 0.33, 0.66, 1.0):
            x, y = ell(a + sway * t, 294 + 9 * math.sin(t * math.pi) - 12 * t * t, SY)
            pts.append((x, y, -76 - L * t))
        tube(q, "StarGlass" if j % 2 else "Violet", pts, [3.4, 3.0, 2.2, 0.7], n=4)
        ex, ey, ez = pts[-1]
        orb(q, GLOW[j % 3] if j % 3 else "Cosmic", ex, ey, ez - 2, 4.4, n=6)
    anchor(q, (0, 0, 0))
    return q


def starweaver_halo(c):
    M = xf(0, 0, 124, rx=7, ry=-5)
    n0 = M.to_3x3() @ Vector((0, 0, 1))
    side = M.to_3x3() @ Vector((1, 0, 0))
    # PRECESSION: the spin axis is leaned 6 degrees off the ring's own normal, so the ring wobbles as it turns
    ax = Matrix.Rotation(math.radians(6.0), 3, side) @ n0
    q = c.part("halo", "Spin", hinge=(0, 0, 124), axis=tuple(ax), amp=0.0, rate=0.11, phase=0.0, gait="Always")
    with frame(q, M):
        R = 316
        for i in range(32):
            torus_arc(q, "Gold" if (i // 2) % 4 == 0 else ("Marble" if i % 2 == 0 else "MarbleDim"), R, 11, 0, 0, 0,
                      i * 11.25, (i + 1) * 11.25 + 0.4, n=2, m=6)
        for i in range(48):
            torus_arc(q, "Cosmic" if i % 3 == 0 else "Inlay", 292, 4, 0, 0, 0, i * 7.5, (i + 1) * 7.5 + 0.2, n=1, m=4)
        for i in range(12):
            a = math.radians(30 * i)
            box(q, "Gold", math.cos(a) * 304, math.sin(a) * 304, 0, 28, 7, 7, rz=math.degrees(a))
            shard(q, GLOW[i % 3], math.cos(a) * R, math.sin(a) * R, 8, 13, 78 + (i % 2) * 28, 44, n=6)
            frustum(q, "Gold", 8, 18, 14, 4, 16, math.cos(a) * R, math.sin(a) * R)
        for i in range(24):
            a = math.radians(15 * i + 7.5)
            box(q, "Cosmic", math.cos(a) * R, math.sin(a) * R, 11, 15, 8, 3, rz=math.degrees(a) + 90)
        for i in range(6):
            a = math.radians(60 * i + 30)
            tube(q, "Gold", [(math.cos(a) * 290, math.sin(a) * 290, 0), (math.cos(a) * 262, math.sin(a) * 262, 2),
                             (math.cos(a) * 240, math.sin(a) * 240, 0)], [9, 6, 0.8], n=4)
    return q


def starweaver_heart(c):
    zc = -108
    # HEART GLOW: a strong slow beat (+-18% in scale), always on
    q = c.part("heart", "Pulse", hinge=(0, 0, zc), axis=(0, 0, 1), amp=0.18, rate=0.12, phase=math.pi * 0.35,
               gait="Always")
    shard(q, "Cosmic", 0, 0, zc, 52, 80, 80, n=8)
    shard(q, "Violet", 0, 0, zc, 34, 100, 100, n=4, a=45)
    for j in range(6):
        a = math.radians(60 * j)
        shard(q, GLOW[j % 3], math.cos(a) * 38, math.sin(a) * 38, zc, 6, 96, 4, n=4, a=math.degrees(a), tilt=90)
    for tilt in (0, 60, 120):
        with frame(q, xf(0, 0, zc, rz=tilt, rx=65)):
            torus(q, "Gold", 82, 3.6, 0, 0, 0, n=24, m=4)
    for j in range(8):
        a = math.radians(45 * j)
        orb(q, GLOW[j % 3], math.cos(a) * 82 * 0.7, math.sin(a) * 82 * 0.7, zc + 58 * math.sin(j * 1.7), 7, n=6)
    anchor(q, (0, 0, zc))
    return q


# three tendrils x three chained segments: a swing about a root/joint hinge, each segment rides on its parent
# (acc = parent.acc * hinge) and beats a little later and a little deeper than the one above it.
TEND_AZ = (60, 180, 300)      # degrees about the bell axis from +X: two forward sides and one trailing
TEND_LEN = 450.0              # total hang below the bell underside
TEND_SEG = 3


def tpath(a, h):
    r = 150 + 70 * h + 14 * math.sin(2 * math.pi * h)
    return Vector((r * math.cos(a), r * math.sin(a), -14 - TEND_LEN * h))


def tendril_segment(q, a, h0, h1, links, first, last):
    ts = [h0 + (h1 - h0) * i / links for i in range(links + 1)]
    pts = [tpath(a, t) for t in ts]
    rad = [4.8 - 2.0 * t for t in ts]
    if last:
        rad[-1] = 1.4
    tube(q, "Gold", pts, rad, n=4)
    for i in range(links + (1 if last else 0)):
        pos = pts[i]
        t = (pts[min(i + 1, links)] - pts[max(i - 1, 0)]).normalized()
        perp1 = t.cross(Vector((0, 0, 1)))
        if perp1.length < 1e-6:
            perp1 = Vector((1, 0, 0))
        perp1.normalize()
        perp2 = t.cross(perp1).normalized()
        axis = perp1 if i % 2 else perp2
        basis_ring(q, ("Marble", "Gold", "StarGlass")[i % 3], pos, t, axis, 13.0 - 6.0 * ts[i], 2.8)
        if i < links:
            mid = (pts[i] + pts[i + 1]) * 0.5
            shard(q, GLOW[(i + int(h0 * 9)) % 3], mid.x, mid.y, mid.z, 7, 12, 12, n=6)
    radial = (math.cos(a), math.sin(a), 0)
    tang = (-math.sin(a), math.cos(a), 0)
    ws = [26 * (1 - 0.62 * t) for t in ts]
    if last:
        ws[-1] = 3
    blade(q, "StarGlass", pts, ws, [1.2] * (links + 1), up=radial)
    blade(q, "Violet", pts, [w * 0.8 for w in ws], [1.0] * (links + 1), up=tang)
    for ph in (0.0, math.pi):
        sp = []
        for i in range(links * 2 + 1):
            tt = i / (links * 2)
            g = h0 + (h1 - h0) * tt
            base = tpath(a, g)
            tn = tpath(a, min(g + 0.01, 1.0)) - tpath(a, max(g - 0.01, 0.0))
            tn.normalize()
            u = tn.cross(Vector(radial)).normalized()
            v = tn.cross(u).normalized()
            ang = ph + tt * 4.0 + h0 * 12.0
            sp.append(tuple(base + (u * math.cos(ang) + v * math.sin(ang)) * (15 - 5 * g)))
        tube(q, "Rose" if ph == 0 else "Shard", sp, [2.4] * (len(sp) - 1) + [0.8], n=3)
    j0 = pts[0]
    if first:
        # root stem running up INTO the bell: the swing pivots at the underside and the stem stays buried
        tube(q, "Gold", [(j0.x, j0.y, j0.z + 46), (j0.x, j0.y, j0.z + 14), (j0.x, j0.y, j0.z - 6)], [9, 9, 6], n=6)
        orb(q, "Gold", j0.x, j0.y, j0.z - 2, 12, n=6)
    else:
        orb(q, "Gold", j0.x, j0.y, j0.z, 11, n=6)           # joint bead: overlaps the parent's last link
    e = pts[-1]
    if not last:
        orb(q, "Gold", e.x, e.y, e.z, 9.5, n=6)
    else:
        shard(q, "Cosmic", e.x, e.y, e.z - 8, 18, 34, 46, n=6)
        with frame(q, xf(e.x, e.y, e.z - 6)):
            torus(q, "Gold", 22, 2.8, 0, 0, 0, n=12, m=4)
        for k in range(3):
            aa = math.radians(120 * k)
            orb(q, GLOW[k], e.x + math.cos(aa) * 22, e.y + math.sin(aa) * 22, e.z - 30, 5, n=6)


def starweaver_tendrils(c, skirt):
    # Root + middle links swing in/out (tangent axis), the tip link swings sideways (radial axis), so the tip draws
    # a loop. Rates differ per link (0.085/0.10/0.125 Hz) so the whip never settles into a metronome. The per-link
    # LAG is carried by `phase` (explicit); the `lag` field stays 0 so any driver reading it adds nothing.
    names = ("tendril", "tendriltip", "tendriltail")
    amps = (0.09, 0.13, 0.18)           # round 3: calmer (was 0.17/0.26/0.36); the runtime damps inertia
    rates = (0.05, 0.055, 0.06)         # slower (was 0.085/0.10/0.125)
    for k, az in enumerate(TEND_AZ):
        a = math.radians(az)
        tang = (-math.sin(a), math.cos(a), 0)
        radial = (math.cos(a), math.sin(a), 0)
        parent = None
        for s in range(TEND_SEG):
            h0, h1 = s / TEND_SEG, (s + 1) / TEND_SEG
            ax = tang if s < 2 else radial
            hp = tpath(a, h0)
            ph = k * 2.09 + s * 0.95
            q = c.part(names[s], "Flap", hinge=tuple(hp), axis=ax, amp=amps[s], rate=rates[s], phase=ph,
                       chain=parent, lag=0.0, gait="Always")
            tendril_segment(q, a, h0, h1, 6, s == 0, s == TEND_SEG - 1)
            parent = q


def build_starweaver():
    c = Creature("starweaver", "COLOSSAL", ["ASTRAL_REACH"], "star-glass jelly celestial, head along +X")
    starweaver_body(c)
    skirt = starweaver_skirt(c)
    starweaver_halo(c)
    starweaver_heart(c)
    starweaver_fringe(c, skirt)
    starweaver_tendrils(c, skirt)
    return c


# ---------------------------------------------------------------------------------------------------------
# ELDER GREATTURTLE
# ---------------------------------------------------------------------------------------------------------
TSY = 0.86
TN = 32
SHELL = [(256, 34, "x"), (262, 42, "rim"), (258, 58, "marg"), (250, 66, "marg"), (244, 68, "ledge"),
         (238, 88, "s1"), (226, 104, "s1"), (220, 106, "ledge"), (212, 122, "s2"), (196, 138, "s2"),
         (190, 140, "ledge"), (180, 152, "s3"), (162, 164, "s3"), (156, 166, "ledge"), (140, 174, "s4"),
         (110, 181, "s4"), (80, 184, "top"), (0, 186, "top")]
HINGE_SHELL = (0, 0, 34)


def shell_matfn(seed):
    rng = random.Random(seed)

    def f(tag, k, c):
        if tag in ("rim",):
            return "Gold"
        if tag == "marg":
            return "MarbleDim" if c % 2 == 0 else "BasaltLight"
        if tag == "ledge":
            return "Gold" if c % 4 == 0 else "MarbleDim"
        if c % 4 == 0:
            return "Gold"                                       # the seams between scutes
        r = rng.random()
        if tag in ("s1", "s2") and r < 0.22:
            return "Moss" if r < 0.12 else "MossDark"
        return ("Basalt", "BasaltLight", "Rock")[(c // 4 + k) % 3]
    return f


TAIL_HINGE = (-262, 0, 8)
NECK_HINGE = (240, 0, 26)
HEAD_HINGE = (300, 0, 41)
FORE_HINGE_X, FORE_HINGE_Y = 118, 208
HIND_HINGE_X, HIND_HINGE_Y = -172, 188


def turtle_body(c):
    p = c.body
    body = [(250, 38, "x"), (254, 28, "gold"), (248, 10, "flank"), (232, -8, "flank"), (205, -22, "belly"),
            (160, -32, "belly"), (100, -38, "belly"), (0, -40, "belly")]

    def mf(tag, k, cc):
        if tag == "gold":
            return "Gold"
        if tag == "flank":
            return "TurtleSkin" if cc % 2 == 0 else "Moss" if cc % 8 == 3 else "BasaltLight"
        return "TurtleBelly" if cc % 4 else "Gold"
    lathe(p, body, TN, mf, sy=TSY, cap_bottom="TurtleBelly")
    # limb masses where the four flippers and the neck join the body (the paddle hinges sit at their centres)
    for s in (-1, 1):
        ell_solid(p, "TurtleSkin", FORE_HINGE_X, s * FORE_HINGE_Y, 4, 74, 62, 48, n=10)
        ell_solid(p, "TurtleSkin", HIND_HINGE_X, s * HIND_HINGE_Y, 0, 62, 54, 40, n=10)
        for x, y in ((FORE_HINGE_X, s * FORE_HINGE_Y), (HIND_HINGE_X, s * HIND_HINGE_Y)):
            with frame(p, xf(x, y, 6)):
                torus(p, "Gold", 56 if x > 0 else 48, 4.5, 0, 0, 0, n=14, m=4)
    ell_solid(p, "TurtleSkin", 244, 0, 24, 40, 62, 38, n=10)
    with frame(p, xf(252, 0, 26, ry=90)):
        torus(p, "Gold", 50, 5.5, 0, 0, 0, n=14, m=4)
    # tail root: a fat stub the moving tail overlaps (keeps the body 560+ long)
    tube(p, "TurtleSkin", [(-230, 0, 12), (-258, 0, 8), (-286, 0, -2), (-306, 0, -12), (-318, 0, -22)],
         [34, 28, 20, 11, 0.8], n=8)
    # hanging crystals under the plastron, and a ring of inlay light
    rng = random.Random("turtle belly")
    for i in range(12):
        a = 2 * math.pi * i / 12 + 0.3
        rr = 70 + (i % 3) * 38
        x, y = ell(a, rr, TSY)
        crystal(p, GLOW[i % 3], x, y, -38, 9 + (i % 2) * 3, 4, 40 + rng.uniform(0, 50), n=5, rz=i * 17)
    with frame(p, xf(0, 0, -38)):
        torus(p, "Inlay", 150, 3.5, 0, 0, 0, n=40, m=4)
    # moss roots hanging from the rim, like a beard
    for i in range(14):
        a = 2 * math.pi * i / 14 + 0.1
        x, y = ell(a, 250, TSY)
        x2, y2 = ell(a, 246, TSY)
        tube(p, "MossDark", [(x, y, 26), (x2, y2, 4), (x2 * 0.99, y2 * 0.99, -22 - (i % 3) * 8)], [5, 3.6, 0.6], n=4)


def turtle_shell(c):
    # BREATHING: the whole shell swells and settles (+-2.2% about its own centre, ~11 s) so the grove rides up and down
    q = c.part("shell", "Pulse", hinge=HINGE_SHELL, axis=(0, 0, 1), amp=0.0, rate=0.09, phase=0.0, gait="Always")   # round 3: rigid shell, no breathing
    lathe(q, SHELL, TN, shell_matfn("elder shell"), sy=TSY, cap_bottom="Basalt")
    for j in range(TN):
        a = 2 * math.pi * (j + 0.5) / TN
        x, y = ell(a, 258, TSY)
        shard(q, "Marble" if j % 2 == 0 else "MarbleDim", x, y, 44, 9, 26, 2, n=4, a=math.degrees(a), tilt=62)
    for j in range(8):
        a = 2 * math.pi * j / 8
        pts = [(*ell(a, r * 1.02, TSY), z) for r, z, _t in SHELL[4:14:2]]
        tube(q, "Gold", pts, [4.5, 4, 3.5, 3, 2.5][: len(pts)], n=4)
    return q


def tz(rn):
    """Island top height at normalised radius (the profile ring heights)."""
    prof = ISLE_TOP
    for (r1, z1), (r2, z2) in zip(prof, prof[1:]):
        if r2 <= rn <= r1:
            t = (rn - r2) / max(r1 - r2, 1e-6)
            return lerp(z2, z1, t)
    return prof[-1][1] if rn < prof[-1][0] else prof[0][1]


ISLE_TOP = [(160, 192), (130, 200), (95, 212), (60, 225), (30, 233), (0, 236)]
ISLE_HINGE = (0, 0, 150)        # buried in the shell: the island rocks about a point inside the carapace
GROVE_HINGE = (0, 0, 228)       # ground level of the meadow: the trees lean about their feet
SINK = 7.0                      # trunks are planted this deep so a leaning grove never lifts a root clear of the turf


def rn_of(x, y):
    return math.hypot(x, y / TSY)


def top(x, y):
    return tz(rn_of(x, y))


def tree(q, x, y, h, kind, rng):
    z = top(x, y) - SINK
    h2 = h + SINK
    if kind == 0:                                                   # pine
        frustum(q, "Bark", 5, 2.2, 1.6, z, z + h2 * 0.3, x, y)
        for i in range(3):
            r0 = (h * 0.34) * (1 - i * 0.26)
            frustum(q, "LeafDark" if i != 1 else "Moss", 6, r0, 0.0 if i == 2 else r0 * 0.42,
                    z + SINK + h * (0.2 + 0.26 * i), z + SINK + h * (0.5 + 0.26 * i), x, y)
    else:                                                           # broadleaf
        frustum(q, "Bark", 5, 2.6, 1.8, z, z + SINK + h * 0.45, x, y)
        orb(q, "Leaf" if rng.random() < 0.6 else "Moss", x, y, z + SINK + h * 0.7, h * 0.34, n=6)


RUIN_C, POND_C = (74, -38), (-92, -62)
GREAT = (-34, 22)


def turtle_isle(c, shell_part):
    # ISLAND ROCK: the whole island sways +-1.9 deg about a point buried in the shell (slow, ~16 s)
    q = c.part("isle", "Flap", hinge=ISLE_HINGE, axis=(0.8, 0.6, 0), amp=0.034, rate=0.062, phase=0.4, chain=shell_part,
               lag=0.0, gait="Always")
    rng = random.Random("elder isle")
    prof = [(160, 135, "x"), (172, 158, "cliff"), (172, 176, "cliff"), (160, 192, "lip")] + \
           [(r, z, "grass") for r, z in ISLE_TOP[1:]]

    def mf(tag, k, cc):
        if tag == "cliff":
            return ("Rock", "RockLight", "RockDeep")[(cc + k) % 3]
        if tag == "lip":
            return "Moss" if cc % 3 else "MossDark"
        return ("Moss", "Leaf", "MossDark")[(cc * 7 + k * 3) % 3]
    lathe(q, prof, TN, mf, sy=TSY, cx=0.0, jit=0.07, seed="elder terrain", cap_bottom="Rock")
    for i in range(16):
        a = 2 * math.pi * i / 16 + 0.2
        pts = []
        for r, z in ((168, 178), (176, 160), (190, 144), (204, 124), (214, 106)):
            x, y = ell(a, r, TSY)
            pts.append((x, y, z))
        tube(q, "Bark", pts, [7, 6, 5, 3.5, 0.8], n=5)
    for i in range(18):
        a = 2 * math.pi * i / 18 + rng.uniform(-0.1, 0.1)
        x, y = ell(a, 166, TSY)
        shard(q, "RockLight", x, y, 168, rng.uniform(8, 14), rng.uniform(8, 18), 6, n=5, a=math.degrees(a), tilt=10)
    # pond with a waterfall down the cliff beside it
    pond_c = POND_C
    pz = top(*pond_c) + 0.3
    frustum(q, "Water", 10, 30, 30, pz, pz + 0.8, *pond_c)
    frustum(q, "MarbleDim", 10, 34, 32, pz - 1, pz + 0.2, *pond_c)
    a_fall = math.atan2(pond_c[1] / TSY, pond_c[0])
    wp = []
    for r, z in ((120, pz + 0.5), (160, top(*ell(a_fall, 160, TSY)) + 0.2), (170, 176), (176, 150), (188, 130)):
        x, y = ell(a_fall, r, TSY)
        wp.append((x, y, z))
    blade(q, "Water", wp, [9, 9, 10, 10, 6], [0.9] * 5, up=(-math.sin(a_fall), math.cos(a_fall), 0))
    # the ruin: a stepped terrace, a broken colonnade, an altar, an obelisk
    rx, ry = RUIN_C
    z0 = top(rx, ry) - 1.5
    frustum(q, "MarbleDim", 10, 56, 52, z0, z0 + 5, rx, ry)
    frustum(q, "Marble", 10, 46, 44, z0 + 5, z0 + 9, rx, ry)
    frustum(q, "Gold", 10, 44.5, 44.5, z0 + 8.5, z0 + 10, rx, ry)
    cols = []
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.4
        cx, cy = rx + math.cos(a) * 34, ry + math.sin(a) * 34
        h = (40, 30, 18, 40, 40, 24, 40, 12)[i]
        frustum(q, "Marble", 6, 4.6, 3.6, z0 + 10, z0 + 10 + h, cx, cy)
        box(q, "Gold", cx, cy, z0 + 10 + h + 1.5, 10, 10, 3)
        cols.append((cx, cy, h))
    for i in (0, 3, 4, 6):
        (x1, y1, h1), (x2, y2, h2) = cols[i], cols[(i + 1) % 8]
        if h1 > 30 and h2 > 30:
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            box(q, "Marble", (x1 + x2) / 2, (y1 + y2) / 2, z0 + 10 + 40 + 6, math.hypot(x2 - x1, y2 - y1) + 6, 7, 6, rz=ang)
            box(q, "Gold", (x1 + x2) / 2, (y1 + y2) / 2, z0 + 10 + 40 + 10.5, math.hypot(x2 - x1, y2 - y1) + 7, 8, 2, rz=ang)
    box(q, "MarbleDim", rx, ry, z0 + 13, 14, 10, 8)
    box(q, "Gold", rx, ry, z0 + 17.5, 15.5, 11.5, 1.5)
    shard(q, "Shard", rx, ry, z0 + 30, 7, 16, 8, n=6)
    ox, oy = rx - 62, ry + 18
    frustum(q, "MarbleDim", 4, 9, 7, z0 + 1, z0 + 18, ox, oy)
    frustum(q, "Marble", 4, 6.5, 2.2, z0 + 18, z0 + 82, ox, oy)
    frustum(q, "Gold", 4, 3.2, 3.2, z0 + 82, z0 + 86, ox, oy)
    shard(q, "Violet", ox, oy, z0 + 98, 6, 14, 8, n=5)
    for i in range(5):
        box(q, "MarbleDim" if i % 2 else "Marble", rx + 60 + i * 5, ry + 6, z0 + 5 - i * 1.0, 6, 28 - i * 3, 3.2 + 0.0)
    ax_, ay_ = 36, 100
    az = top(ax_, ay_) - 1.5
    for s in (-1, 1):
        frustum(q, "Marble", 6, 5, 4, az, az + 34, ax_ + s * 15, ay_)
        box(q, "Gold", ax_ + s * 15, ay_, az + 35.5, 11, 11, 3)
    box(q, "Marble", ax_, ay_, az + 40, 40, 8, 7)
    box(q, "Gold", ax_, ay_, az + 44.5, 41, 9, 2)
    for i in range(46):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.1, 0.95) * 150
        x, y = d * math.cos(a), d * TSY * math.sin(a)
        if math.hypot(x - pond_c[0], y - pond_c[1]) < 34:
            continue
        shard(q, ("Rose", "Violet", "Gold", "Shard")[i % 4], x, y, top(x, y) - 0.5, 1.7, 3.2, 0.5, n=4)
    return q


def turtle_grove(c, isle_part):
    # GROVE SWAY: the great tree and the woods are their own part, chained to the island and leaning a little
    # later and deeper than it, about the meadow's ground level (the trunks are planted deep, so nothing floats)
    q = c.part("grove", "Flap", hinge=GROVE_HINGE, axis=(0.6, -0.8, 0), amp=0.05, rate=0.095, phase=1.7, chain=isle_part,
               lag=0.0, gait="Always")
    rng = random.Random("elder grove")
    gx, gy = GREAT
    gz = top(gx, gy) - SINK
    tube(q, "Bark", [(gx, gy, gz), (gx + 3, gy - 2, gz + 40 + SINK), (gx + 1, gy + 4, gz + 80 + SINK),
                     (gx - 4, gy + 2, gz + 112 + SINK)], [17, 14, 10, 7], n=7)
    for bi, (dx, dy, dz) in enumerate(((46, 10, 90), (-40, 22, 94), (10, -44, 100), (-6, 44, 96), (34, -30, 110))):
        tube(q, "Bark", [(gx + 2, gy, gz + 80 + SINK), (gx + dx * 0.5, gy + dy * 0.5, gz + SINK + dz * 0.95),
                         (gx + dx, gy + dy, gz + SINK + dz + 18)], [7, 5, 2.4], n=5)
    gz2 = gz + SINK
    for (dx, dy, dz, rr, col) in ((0, 0, 140, 58, "Leaf"), (46, 10, 118, 40, "Moss"), (-40, 22, 120, 42, "Leaf"),
                                  (10, -44, 124, 40, "LeafDark"), (-6, 44, 118, 38, "Moss"),
                                  (34, -30, 138, 34, "Leaf"), (-24, -10, 178, 36, "Moss")):
        orb(q, col, gx + dx, gy + dy, gz2 + dz, rr, n=8)
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(26, 56)
        orb(q, "Rose", gx + math.cos(a) * d, gy + math.sin(a) * d, gz2 + 100 + rng.uniform(0, 70), 4.2, n=5)
    placed = 0
    tries = 0
    while placed < 70 and tries < 800:
        tries += 1
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.08, 0.94) * 150
        x, y = d * math.cos(a), d * TSY * math.sin(a)
        if math.hypot(x - gx, y - gy) < 62 or math.hypot(x - RUIN_C[0], y - RUIN_C[1]) < 64 \
                or math.hypot(x - POND_C[0], y - POND_C[1]) < 38:
            continue
        tree(q, x, y, rng.uniform(26, 56), rng.randrange(2), rng)
        placed += 1
    return q


def turtle_crystals(c, shell_part):
    q = c.part("crystals", "Flicker", hinge=HINGE_SHELL, axis=(0, 0, 1), amp=0.0, rate=0.11, phase=0.0,
               chain=shell_part, lag=0.0, gait="Always")
    rng = random.Random("elder crystals")
    for j in range(18):
        a = 2 * math.pi * (j + 0.3) / 18
        for k, (rr, z, up, rad, tilt) in enumerate(((210, 120, 52, 11, 26), (194, 140, 34, 8, 18))):
            if k == 1 and j % 2:
                continue
            x, y = ell(a, rr, TSY)
            shard(q, GLOW[(j + k) % 3], x, y, z, rad, up * rng.uniform(0.8, 1.25), 10, n=5, a=math.degrees(a),
                  tilt=tilt)
    for j in range(6):
        a = math.radians(45 + 60 * j)
        x, y = ell(a, 236, TSY)
        for m in range(5):
            aa = a + (m - 2) * 0.09
            xx, yy = ell(aa, 236 + (m % 2) * 6, TSY)
            shard(q, GLOW[m % 3], xx, yy, 96 + (m % 2) * 6, 10 + (2 - abs(m - 2)) * 3, 40 + (2 - abs(m - 2)) * 28, 14,
                  n=6, a=math.degrees(aa), tilt=34 - abs(m - 2) * 6)
    for j in range(7):
        a = 2 * math.pi * j / 7 + 0.5
        d = 38 + (j % 3) * 28
        x, y = d * math.cos(a), d * TSY * math.sin(a)
        shard(q, "Cosmic" if j % 2 else "Shard", x, y, top(x, y) + 4, 6, 70 + (j % 3) * 36, 4, n=5)
    return q


def turtle_neck_head(c):
    # NECK: two links. The neck nods about its root (slow, ~14 s), the head link carries the distal neck, the head
    # and the eyes and nods a beat later and deeper, so the head reaches out and eases back like a living thing.
    neck = c.part("neck", "Flap", hinge=NECK_HINGE, axis=(0, 1, 0), amp=0.10, rate=0.07, phase=0.0, gait="Always")
    tube(neck, "TurtleSkin", [(226, 0, 22), (262, 0, 30), (292, 0, 39), (306, 0, 43)], [46, 44, 42, 41], n=8)
    for i, x in enumerate((256, 280)):
        with frame(neck, xf(x, 0, 28 + i * 6, ry=90)):
            torus(neck, "Gold" if i % 2 == 0 else "Marble", 43 - i * 1.5, 4.2, 0, 0, 0, n=12, m=4)
    for i in range(3):
        x = 252 + i * 14
        box(neck, "MarbleDim" if i % 2 else "Marble", x, 0, 30 + i * 3 + 40, 11, 24, 5, ry=-12)
    for s in (-1, 1):
        tube(neck, "MossDark", [(262, s * 38, 14), (286, s * 38, 22), (300, s * 37, 26)], [6, 5, 0.8], n=4)
    head = c.part("head", "Flap", hinge=HEAD_HINGE, axis=(0, 1, 0), amp=0.16, rate=0.07, phase=0.9, chain=neck,
                  lag=0.0, gait="Always")
    tube(head, "TurtleSkin", [(296, 0, 41), (318, 0, 45), (336, 0, 47)], [42, 40, 38], n=8)
    for i, x in enumerate((312, 328)):
        with frame(head, xf(x, 0, 42 + i * 3, ry=90)):
            torus(head, "Gold" if i % 2 == 0 else "Marble", 41.5 - i * 1.5, 4.2, 0, 0, 0, n=12, m=4)
    for i in range(3):
        x = 306 + i * 14
        box(head, "MarbleDim" if i % 2 else "Marble", x, 0, 30 + i * 3 + 52, 11, 24, 5, ry=-12)
    for s in (-1, 1):
        tube(head, "MossDark", [(300, s * 36, 26), (318, s * 36, 30)], [5, 0.8], n=4)
    ell_solid(head, "TurtleSkin", 374, 0, 50, 50, 42, 34, n=10)
    tube(head, "BasaltLight", [(398, 0, 56), (416, 0, 50), (430, 0, 40), (436, 0, 34)], [24, 18, 10, 1.4], n=6)     # beak
    tube(head, "Marble", [(396, 0, 40), (412, 0, 34), (424, 0, 30)], [17, 11, 1.5], n=6)                           # jaw
    for s in (-1, 1):
        orb(head, "TurtleBelly", 394, s * 31, 58, 8.4, n=8)
        orb(head, "Cosmic", 399, s * 33, 59, 5.0, n=6)
        orb(head, "Cosmic", 396, s * 31.5, 59, 7.2, n=6)                                                         # eye glow
        tube(head, "Gold", [(360, s * 26, 70), (384, s * 33, 72), (404, s * 36, 66)], [5.5, 5, 2], n=4)
        shard(head, "Violet" if s > 0 else "Rose", 352, s * 24, 66, 12, 62, 6, n=5, a=0, tilt=-55)
        shard(head, "Shard", 366, s * 34, 62, 8, 34, 4, n=5, a=s * 90, tilt=50)
        for i in range(2):
            orb(head, "MossDark", 372 + i * 12, s * (20 + i * 4), 78 - i * 2, 7, n=6)
    for i in range(3):
        shard(head, GLOW[i], 350 + i * 12, 0, 80 - i * 3, 8 - i, 30 - i * 6, 4, n=5, tilt=-30)
    box(head, "Gold", 422, 0, 52, 8, 24, 3, ry=-18)
    return neck, head


def turtle_tail(c):
    # TAIL: a long slow sweep behind the turn, fat root buried in the body stub
    q = c.part("tail", "Flap", hinge=TAIL_HINGE, axis=(0, 0, 1), amp=0.24, rate=0.065, phase=2.2, gait="Always")
    tube(q, "TurtleSkin", [(-246, 0, 10), (-290, 0, 5), (-330, 0, -6), (-362, 0, -17), (-384, 0, -26), (-394, 0, -30)],
         [37, 31, 23, 14, 6, 0.8], n=8)
    for i in range(6):
        x = -258 - i * 20
        shard(q, GLOW[i % 3], x, 0, 38 - i * 8, 6.5 - i * 0.7, 24 - i * 2.4, 3, n=4, tilt=-20)
    for i, x in enumerate((-270, -300, -328)):
        with frame(q, xf(x, 0, 8 - i * 6, ry=90)):
            torus(q, "Gold", 31 - i * 7, 3, 0, 0, 0, n=10, m=4)
    return q


def paddle(c, name, s, pts, widths, thicks, hinge, axis, amp, rate, phase, chain, extra=None):
    q = c.part(name, "Flap", hinge=hinge, axis=axis, amp=amp, rate=rate, phase=phase, chain=chain, lag=0.0,
               gait="Flight")
    blade(q, "TurtleSkin", pts, widths, thicks, up=(0, 0, 1))
    blade(q, "Inlay", [(x, y, z + t + 0.8) for (x, y, z), t in zip(pts, thicks)],
          [w * 0.12 for w in widths], [0.7] * len(pts), up=(0, 0, 1))
    blade(q, "Gold", [(x + w * 0.9, y, z + 0.2) for (x, y, z), w in zip(pts, widths)], [w * 0.1 for w in widths],
          [t * 1.1 for t in thicks], up=(0, 0, 1))
    for i in range(1, len(pts) - 1):
        x, y, z = pts[i]
        shard(q, "Moss" if i % 2 else "MossDark", x - widths[i] * 0.3, y, z + thicks[i] + 0.6, widths[i] * 0.38, 2.4, 0.5, n=5)
        shard(q, GLOW[i % 3], x + widths[i] * 0.35, y, z + thicks[i], 4.2, 11, 2, n=4, a=-s * 20, tilt=-18)
    if extra:
        extra(q, pts)
    return q


def turtle_flippers(c):
    for s in (1, -1):
        # FORE PADDLES (symmetric): a slow deep stroke. The root link beats +-0.45 rad about the body axis; the tip
        # link is chained, beats a beat later and deeper, and its axis is turned 22 degrees toward the paddle's long
        # axis so it also FEATHERS (the leading edge dips on the downstroke) like a real flipper.
        ph = 0.0
        hx, hy = FORE_HINGE_X, s * FORE_HINGE_Y
        root_pts = [(hx, hy, 4), (hx - 8, s * 262, -1), (hx - 18, s * 318, -6)]
        tip_pts = [(hx - 18, s * 318, -6), (hx - 56, s * 354, -12), (hx - 108, s * 384, -22), (hx - 156, s * 402, -33),
                   (hx - 186, s * 410, -44)]
        up = paddle(c, "flipper", s, root_pts, [64, 80, 76], [20, 17, 14], (hx, hy, 4), (s, 0, 0), 0.42, 0.14, ph, None)
        # joint bead hides the seam when the tip link bends against the root link
        orb(up, "TurtleSkin", hx - 18, s * 318, -6, 19, n=8)

        def claws(q, pts, s=s):
            ex, ey, ez = pts[-1]
            for i in range(3):
                tube(q, "Marble", [(ex + 22 - i * 20, ey - 3 * s, ez - 2), (ex - 6 - i * 20, ey + s * 14, ez - 8)],
                     [6, 0.8], n=4)
        tip = paddle(c, "flippertip", s, tip_pts, [74, 86, 74, 46, 12], [14, 12, 9, 6, 3], (hx - 18, s * 318, -6),
                     (s * math.cos(math.radians(22)), math.sin(math.radians(22)), 0), 0.50, 0.14, ph - 0.9, up, claws)
        orb(tip, "TurtleSkin", hx - 18, s * 318, -6, 19, n=8)
    # HIND PADDLES: one broad blade each, rowing against each other, half a beat behind the fore pair
    for s in (1, -1):
        hx, hy = HIND_HINGE_X, s * HIND_HINGE_Y
        pts = [(hx, hy, 0), (hx - 34, s * 246, -8), (hx - 72, s * 296, -18), (hx - 108, s * 332, -30),
               (hx - 128, s * 348, -38)]
        paddle(c, "hindflipper", s, pts, [52, 68, 68, 50, 10], [15, 13, 10, 8, 3], (hx, hy, 0), (s, 0, 0), 0.34, 0.14,
               math.pi * 0.5 + (0.0 if s > 0 else math.pi), None)


def build_turtle():
    c = Creature("elder_greatturtle", "COLOSSAL", ["VERDANT"], "island-backed sky turtle, head along +X")
    turtle_body(c)
    shell = turtle_shell(c)
    isle = turtle_isle(c, shell)
    turtle_grove(c, isle)
    turtle_crystals(c, shell)
    turtle_neck_head(c)
    turtle_tail(c)
    turtle_flippers(c)
    return c


# ---------------------------------------------------------------------------------------------------------
# Assembly, checks, sidecar, export
# ---------------------------------------------------------------------------------------------------------
def bbox(p):
    xs = [v.x for v in p.verts]
    ys = [v.y for v in p.verts]
    zs = [v.z for v in p.verts]
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def finalize(c):
    """Shift everything so the body's bounding-box centre is the origin, return the shift."""
    lo, hi = bbox(c.body)
    shift = (lo + hi) * 0.5
    for p in [c.body] + [q for q, _m in c.parts]:
        for i, v in enumerate(p.verts):
            p.verts[i] = v - shift
    for _q, m in c.parts:
        m["hinge"] = m["hinge"] - shift
    return shift


def to_sidecar_frame(v):
    """Blender (x, y, z) -> the OrbiterParts frame of make_layout_luau.local(): (-x, z, y)."""
    return [-v.x, v.z, v.y]


def build_sidecar(creatures):
    out = {"group": "colossal", "creatures": {}}
    for c in creatures:
        blo, bhi = bbox(c.body)
        bc = (blo + bhi) * 0.5
        size_bl = bhi - blo
        entry = {"model": c.body.name, "class": c.cls,
                 "size": [round(size_bl.x, 2), round(size_bl.z, 2), round(size_bl.y, 2)],
                 "tris": tris(c.body) + sum(tris(q) for q, _m in c.parts), "biome": c.biome, "parts": {}}
        for q, m in c.parts:
            lo, hi = bbox(q)
            qc = (lo + hi) * 0.5
            ax = m["axis"]
            entry["parts"][q.name] = {
                "kind": m["kind"],
                "offset": [round(x, 3) for x in to_sidecar_frame(qc - bc)],
                "hinge": [round(x, 3) for x in to_sidecar_frame(m["hinge"] - bc)],
                "axis": [round(-ax.x, 4), round(ax.z, 4), round(ax.y, 4)],
                "amp": m["amp"], "rate": m["rate"], "phase": round(m["phase"], 4),
                "chain": m["chain"], "lag": m["lag"], "gait": m["gait"]}
        out["creatures"][c.id] = entry
    return out


def check(creatures):
    ok = True
    for c in creatures:
        allp = [c.body] + [q for q, _m in c.parts]
        total = 0
        alo = Vector((1e9,) * 3)
        ahi = Vector((-1e9,) * 3)
        for p in allp:
            n = tris(p)
            total += n
            lo, hi = bbox(p)
            alo = Vector((min(alo[i], lo[i]) for i in range(3)))
            ahi = Vector((max(ahi[i], hi[i]) for i in range(3)))
            ext = max(hi - lo)
            flag = "ok" if n < TRI_LIMIT and ext < ROBLOX_MESH_LIMIT else "OVER"
            if flag != "ok":
                ok = False
            print(f"MESH {p.name:46s} {n:6d} tris  ext {ext:7.1f}  {flag}")
        blo, bhi = bbox(c.body)
        print(f"CREATURE {c.id}: {len(allp)} meshes, {total} tris, body bbox {[round(x, 1) for x in (bhi - blo)]}, "
              f"assembly bbox {[round(x, 1) for x in (ahi - alo)]}")
        if len(allp) > 14:       # round 2: up to 14 meshes per creature, body included
            ok = False
    return ok


def to_objects(creatures):
    mats = K["ensure_materials"]()
    coll = bpy.data.collections.new("Colossal")
    bpy.context.scene.collection.children.link(coll)
    objs = {}
    for c in creatures:
        objs[c.id] = []
        for p in [c.body] + [q for q, _m in c.parts]:
            o = K["to_object"](p, mats, coll)
            o["kit"] = "CROSSROADS"
            o["tris"] = tris(p)
            objs[c.id].append(o)
    return objs


# ---------------------------------------------------------------------------------------------------------
# Review renders (scratch by default; --final writes renders/ in this folder)
# ---------------------------------------------------------------------------------------------------------
RENDER_DIR = os.path.join(HERE, "renders")
SCRATCH = os.environ.get("COLOSSAL_SCRATCH", os.path.join(os.environ.get("TEMP", HERE), "colossal_renders"))
VIEWS = {
    "starweaver": [("3q", (0.85, -1.0, 0.32)), ("side", (0.0, -1.0, 0.04)), ("below", (0.55, -0.85, -0.55))],
    "elder_greatturtle": [("3q", (0.85, -1.0, 0.38)), ("side", (0.0, -1.0, 0.06)), ("above", (0.35, -0.55, 1.0))],
}


def _scene_setup():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.10, 0.08, 0.22, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    for nm, en, col, rot in (("Sun", 3.4, (1.0, 0.86, 0.7), (60, 0, -40)), ("Fill", 1.2, (0.62, 0.56, 1.0), (-50, 0, 140))):
        l = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN"))
        scene.collection.objects.link(l)
        l.data.energy = en
        l.data.color = col
        l.rotation_euler = tuple(math.radians(a) for a in rot)
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = 900, 560
    scene.render.image_settings.file_format = "JPEG"
    scene.view_settings.view_transform = "Standard"
    for m in bpy.data.materials:
        if m.use_nodes:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and b.inputs["Emission Strength"].default_value > 0:
                b.inputs["Emission Strength"].default_value = 1.2


def _shot(name, loc, target, out, lens=35):
    scene = bpy.context.scene
    cam = bpy.data.objects.get("Cam") or bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    cam.data.clip_end = 20000
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    path = os.path.join(out, name + ".jpg")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def _sheet(paths, cols, out_path):
    import numpy as np
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    big = np.zeros((h * rows, w * cols, 4), dtype=np.float32)
    for i, im in enumerate(imgs):
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, cc = divmod(i, cols)
        y0 = h * (rows - 1 - r)
        big[y0:y0 + h, cc * w:(cc + 1) * w] = a
    out = bpy.data.images.new("sheet", w * cols, h * rows)
    out.pixels = big.ravel().tolist()
    out.filepath_raw = out_path
    out.file_format = "JPEG"
    out.save()


def render_all(creatures, objs, argv):
    final = "--final" in argv
    out = RENDER_DIR if final else SCRATCH
    os.makedirs(out, exist_ok=True)
    _scene_setup()
    tiles = []
    for c in creatures:
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.hide_render = o not in objs[c.id]
        lo = Vector((1e9,) * 3)
        hi = Vector((-1e9,) * 3)
        for o in objs[c.id]:
            for cn in o.bound_box:
                for i in range(3):
                    lo[i] = min(lo[i], cn[i])
                    hi[i] = max(hi[i], cn[i])
        cen = (lo + hi) * 0.5
        d = max(hi - lo) * 1.9
        for vname, dirv in VIEWS[c.id]:
            loc = cen + Vector(dirv).normalized() * d
            tiles.append(_shot(f"{c.id}_{vname}", loc, cen, out))
    sheet = os.path.join(out, "colossal_contact_sheet.jpg")
    _sheet(tiles, 3, sheet)
    print("SHEET", sheet)
    if "--closeups" in argv:
        specs = {"starweaver": ((120, -330, -170), (20, 0, -140), 60),
                 "elder_greatturtle": ((330, -300, 330), (20, 0, 180), 45)}
        for c in creatures:
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o not in objs[c.id]
            lc, tc, lens = specs[c.id]
            _shot(f"{c.id}_closeup", lc, tc, out, lens=lens)



def main(argv):
    creatures = [build_starweaver(), build_turtle()]
    for c in creatures:
        finalize(c)
    # round 2 contract: up to 14 meshes per creature (body counts)
    for c in creatures:
        assert 1 + len(c.parts) <= 14, f"{c.id}: {1 + len(c.parts)} meshes"
    ok = check(creatures)
    sidecar = build_sidecar(creatures)
    for c in creatures:
        print(f"SIDECAR {c.id}: tris {sidecar['creatures'][c.id]['tris']} size {sidecar['creatures'][c.id]['size']}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = to_objects(creatures)
    if "--export" in argv:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        flat = [o for c in creatures for o in objs[c.id]]
        K["_export_selected"](flat, FBX_PATH)
        print("EXPORTED", FBX_PATH)
        with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(sidecar, fh, indent=1)
            fh.write("\n")
        print("SIDECAR", JSON_PATH)
    if "--render" in argv:
        render_all(creatures, objs, argv)
    print("RESULT", "OK" if ok else "FAILED")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
