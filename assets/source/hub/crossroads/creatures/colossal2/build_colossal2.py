"""Crossroads V2 sky ecosystem, round 2: the two NEW COLOSSAL hero creatures.

    cinder_wyrm       Emberfall: a vast sinuous ash-and-ember sky serpent. The head is the body root; the jaw is a
                      hinged part; 15 chained trunk/tail segments carry a travelling wave; two pairs of ember fins
                      (Flap chains on segments 3 and 10); crown of spines, glowing seams, ember belly.
    aether_nautilus   Ethereal Scape: a colossal pearl nautilus. A chambered spiral shell is the body root; a head
                      part (hood, eyes) with a drifting fin halo and a pulsing jet funnel chained to it; three
                      trailing tentacle chains of 4, 3 and 3 segments.

Contract: docs/design/SKY_ECOSYSTEM_CONTRACT.md sections 2, 3, 4.1, 6. Built at FINAL stud size, head +X, up +Z,
the body mesh's bounding-box centre at the origin. Parts are rigid meshes at their own origin (body-local coords)
named `hubprop_<id>__<part>_<n>`. Helpers come read-only from build_colossal.py / build_crossroads_hub.py (runpy).

    python tools/run_blender.py -b --factory-startup --python build_colossal2.py -- --export --render [--final]

Sidecar frame key "orbiter": offset/hinge/axis use the OrbiterParts frame, Blender (x, y, z) -> (-x, z, y).
Importable (main is guarded); pose_preview.py imports build_all() to prove the rig data.
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
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
EXPORT_DIR = os.path.join(REPO, "assets", "export", "hub", "crossroads")
FBX_PATH = os.path.join(EXPORT_DIR, "creatures_colossal2.fbx")
JSON_PATH = os.path.join(EXPORT_DIR, "creatures_colossal2.json")

_saved_argv = list(sys.argv)
sys.argv = ["x"]
C1 = runpy.run_path(os.path.join(HERE, "..", "colossal", "build_colossal.py"), run_name="lib")   # read-only
sys.argv = _saved_argv
K = C1["K"]
Piece, box, frustum, crystal, torus, tube, orb, xf, frame = (
    K[n] for n in ("Piece", "box", "frustum", "crystal", "torus", "tube", "orb", "xf", "frame"))
blade, shard, soup, tris, bbox = (C1[n] for n in ("blade", "shard", "soup", "tris", "bbox"))
Creature = C1["Creature"]

TRI_LIMIT = 10000
ROBLOX_MESH_LIMIT = 2048

# Drop the other group's species palette entries, add ours (the contract allows species-only entries).
for _n in ("StarGlass", "StarGlassDeep", "Moss", "MossDark", "Leaf", "LeafDark", "TurtleSkin", "TurtleBelly", "Bark"):
    K["PALETTE"].pop(_n, None)
K["PALETTE"].update({
    "Char": ((46, 40, 50), False),              # Emberfall: charred plate
    "CharDark": ((28, 24, 34), False),
    "CharLight": ((86, 74, 80), False),
    "Ash": ((104, 96, 106), False),
    "EmberDeep": ((214, 88, 38), True),
    "EmberHot": ((255, 130, 52), True),
    "Magma": ((255, 206, 118), True),
    "Pearl": ((240, 232, 246), False),          # Ethereal Scape: nacre and twilight
    "PearlViolet": ((190, 164, 234), False),
    "PearlRose": ((238, 192, 226), False),
    "DeepPearl": ((116, 96, 168), False),
    "Opal": ((206, 190, 255), True),            # translucent-look chamber glow (no real alpha)
    "Mantle": ((82, 68, 128), False),
    "MantleLight": ((150, 126, 202), False),
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())
K["REFINISH"] = False
GLOW = ("Shard", "Violet", "Rose")


# ---------------------------------------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def loft(p, rings, matfn, n=12, cap0=False, cap1=False, cap_mat="Char"):
    """rings: [(centre, u, v, a, b)] ; ring point = centre + u*a*cos + v*b*sin. matfn(k, c) -> palette name of the
    quad between ring k and k+1, column c. a == b == 0 collapses the ring to its centre (an apex)."""
    verts, rs = [], []
    for c, u, v, a, b in rings:
        c, u, v = Vector(c), Vector(u), Vector(v)
        if a <= 1e-6 and b <= 1e-6:
            verts.append(tuple(c))
            rs.append([len(verts) - 1])
            continue
        ring = []
        for k in range(n):
            t = 2 * math.pi * k / n
            verts.append(tuple(c + u * (a * math.cos(t)) + v * (b * math.sin(t))))
            ring.append(len(verts) - 1)
        rs.append(ring)
    faces, mats = [], []
    for k, (A, B) in enumerate(zip(rs, rs[1:])):
        for c in range(n):
            c2 = (c + 1) % n
            if len(A) > 1 and len(B) > 1:
                faces.append((A[c], A[c2], B[c2], B[c]))
            elif len(B) == 1:
                faces.append((A[c], A[c2], B[0]))
            else:
                faces.append((A[0], B[c2], B[c]))
            mats.append(matfn(k, c))
    if cap0 and len(rs[0]) > 1:
        faces.append(tuple(reversed(rs[0])))
        mats.append(cap_mat)
    if cap1 and len(rs[-1]) > 1:
        faces.append(tuple(rs[-1]))
        mats.append(cap_mat)
    soup(p, verts, faces, mats)


def xloft(p, specs, matfn, n=12, cap0=False, cap1=False, cap_mat="Char"):
    """Loft along +X: specs [(x, a_halfwidth_y, b_halfheight_z, zc)] (a ring ordered by decreasing/increasing x)."""
    rings = [((x, 0.0, zc), (0, 1, 0), (0, 0, 1), a, b) for x, a, b, zc in specs]
    loft(p, rings, matfn, n, cap0, cap1, cap_mat)


def interp(table, s):
    if s <= table[0][0]:
        return table[0][1]
    for (s0, r0), (s1, r1) in zip(table, table[1:]):
        if s <= s1:
            return lerp(r0, r1, (s - s0) / (s1 - s0))
    return table[-1][1]


def lean_spike(p, mat, x, y, z, r, up, lean=-30.0, roll=0.0, n=4, down=2.0):
    """A crystal/horn leaning `lean` degrees about Y (negative = swept back toward -X), `roll` about X (outward)."""
    with frame(p, xf(x, y, z, rx=roll, ry=lean)):
        crystal(p, mat, 0, 0, 0, r, up, down, n)


# ---------------------------------------------------------------------------------------------------------
# CINDER WYRM
# ---------------------------------------------------------------------------------------------------------
SEG = 46.0                  # trunk/tail segment length
NSEG = 15
HEAD_FRONT = 140.0
PROFILE = [(0, 30), (40, 38), (150, 46), (330, 41), (520, 27), (660, 12), (SEG * NSEG, 4)]
FIN_SEGS = (3, 10)          # fin pairs ride on these segments


def wr(s):
    return interp(PROFILE, s)


def wyrm_seg_mat(rng, i):
    belly_hot = ("EmberDeep", "EmberHot")

    def f(k, c):
        if c in (2, 3, 4):                                 # dorsal armour
            return "Char" if (c + k + i) % 2 == 0 else "CharDark"
        if c in (8, 9, 10):                                # glowing belly
            return belly_hot[(c + i) % 2]
        r = rng.random()
        if r < 0.10:
            return "EmberDeep"                             # crack
        return "Ash" if (k + c) % 2 == 0 else "CharLight"
    return f


def wyrm_head(c):
    p = c.body
    rng = random.Random("wyrm_head")
    specs = [(-6, 33, 33, 0), (24, 42, 38, 3), (58, 40, 32, 2), (92, 30, 22, -2), (122, 17, 12, -6),
             (HEAD_FRONT, 6, 6, -8)]

    def f(k, col):
        if col in (2, 3, 4):
            return "Char" if (col + k) % 2 == 0 else "CharDark"
        if col in (8, 9, 10):
            return "CharLight" if col != 9 else "Ash"
        return "Ash" if rng.random() > 0.15 else "EmberDeep"
    xloft(p, specs, f, n=12, cap1=True)
    # glowing seams down the skull and along the jaw line
    tube(p, "EmberHot", [(4, 0, 36), (40, 0, 41), (78, 0, 35), (112, 0, 20)], [2.4, 2.6, 2.2, 1.2], n=3)
    for s in (-1, 1):
        tube(p, "EmberDeep", [(30, s * 38, 14), (60, s * 36, 8), (90, s * 28, 0), (118, s * 16, -6)],
             [2.2, 2.2, 1.8, 1.0], n=3)
    # brow ridges, nostrils, gold trim
    for s in (-1, 1):
        box(p, "CharDark", 84, s * 24, 28, 54, 12, 8, rz=s * -14)
        box(p, "Gold", 70, s * 30, 30, 8, 8, 5, rz=s * -10)
        orb(p, "Magma", 86, s * 28, 14, 6.5, n=6)                       # eyes
        orb(p, "EmberHot", 93, s * 25, 12, 3.2, n=5)
        orb(p, "EmberHot", 130, s * 5, -1, 2.6, n=5)                    # nostrils
        tube(p, "Gold", [(54, s * 37, 24), (82, s * 31, 22), (108, s * 20, 8)], [3.2, 3.2, 1.6], n=4)
        tube(p, "Marble", [(100, s * 12, -12), (106, s * 14, -20), (110, s * 13, -27)], [2.8, 2.4, 0.5], n=4)  # fangs
    # crown of spines, fanning back over the neck; two great horns
    for j, (x, y, up, lean) in enumerate([(14, 0, 118, -62), (22, 18, 100, -58), (22, -18, 100, -58),
                                          (30, 33, 84, -55), (30, -33, 84, -55), (6, 26, 92, -66), (6, -26, 92, -66),
                                          (38, 12, 70, -50), (38, -12, 70, -50)]):
        mat = ("Char", "Basalt", "Char", "BasaltLight")[j % 4]
        lean_spike(p, mat, x, y, 36 - abs(y) * 0.25, 9.5 - abs(y) * 0.06, up, lean, roll=(y / 40) * 18, n=5)
        lean_spike(p, GLOW[j % 3], x + 3, y, 38 - abs(y) * 0.25, 4.0, up * 0.62, lean, roll=(y / 40) * 18, n=4, down=1)
    for s in (-1, 1):
        tube(p, "Basalt", [(34, s * 36, 22), (4, s * 62, 40), (-26, s * 92, 56), (-60, s * 110, 56)],
             [11, 9, 6, 1.2], n=5)
        tube(p, "Gold", [(30, s * 38, 24), (6, s * 62, 41), (-24, s * 91, 56)], [3.2, 2.8, 1.6], n=4)
        shard(p, "Rose" if s > 0 else "Violet", -20, s * 90, 58, 6, 22, 4, n=4, a=0, tilt=-60)
    # frill plates behind the jaw hinge
    for s in (-1, 1):
        blade(p, "CharDark", [(34, s * 38, 6), (14, s * 70, 4), (-14, s * 96, 6)], [20, 26, 8], [2, 2, 1.2], up=(0, 0, 1))
        blade(p, "EmberDeep", [(36, s * 40, 5), (16, s * 70, 3), (-10, s * 94, 5)], [3, 4, 1.5], [1.6, 1.6, 1.0], up=(0, 0, 1))


def wyrm_jaw(c):
    q = c.part("jaw", "Flap", hinge=(8, 0, -30), axis=(0, 1, 0), amp=0.14, rate=0.07, phase=0.0, gait="Flight")
    specs = [(2, 26, 9, -32), (40, 28, 8, -32), (80, 20, 6, -27), (112, 10, 4, -20), (126, 4, 3, -17)]
    xloft(q, specs, lambda k, col: ("Ash", "CharLight")[(k + col) % 2] if col not in (2, 3, 4) else "Marble", n=10,
          cap1=True)
    for s in (-1, 1):
        for i in range(7):
            x = 30 + i * 13
            r = 3.4 - i * 0.28
            tube(q, "Marble", [(x, s * (24 - i * 2.2), -26), (x + 2, s * (23 - i * 2.2), -26 + 9 - i * 0.5)],
                 [r, 0.4], n=4)
        tube(q, "Gold", [(4, s * 26, -34), (50, s * 28, -36), (100, s * 12, -22)], [3.2, 3.0, 1.4], n=4)
    tube(q, "EmberHot", [(8, 0, -40), (60, 0, -40), (110, 0, -27)], [2.4, 2.4, 1.2], n=3)
    tube(q, "EmberDeep", [(10, 0, -24), (60, 0, -23), (100, 0, -18)], [3, 3, 1.5], n=3)       # throat glow


def wyrm_segment(c, i, prev, rng):
    s0, s1 = (i - 1) * SEG, i * SEG
    sm = (s0 + s1) * 0.5
    last = i == NSEG
    hinge = (-s0, 0, 0)
    amp = lerp(0.09, 0.24, (i - 1) / (NSEG - 1))
    q = c.part("body_a", "Flap", hinge=hinge, axis=(0, 1, 0), amp=amp, rate=0.075, phase=0.0, chain=prev,
               lag=0.5, gait="Always")
    rings = [((-(s0 - 9), 0, 0), (0, 1, 0), (0, 0, 1), wr(s0) * 0.93, wr(s0) * 0.93),
             ((-s0, 0, 0), (0, 1, 0), (0, 0, 1), wr(s0) * 1.0, wr(s0) * 1.0),
             ((-sm, 0, 0), (0, 1, 0), (0, 0, 1), wr(sm) * 1.07, wr(sm) * 1.07),
             ((-s1, 0, 0), (0, 1, 0), (0, 0, 1), wr(s1), wr(s1))]
    if last:
        rings.append(((-(s1 + 34), 0, 0), (0, 1, 0), (0, 0, 1), 0.0, 0.0))
    loft(q, rings, wyrm_seg_mat(rng, i), n=12, cap1=False)
    r1 = wr(s1)
    rm = wr(sm) * 1.07
    # glowing seam ring and a gold band on the joints
    with frame(q, xf(-s1 + 2, 0, 0, ry=90)):
        torus(q, "EmberHot" if i % 2 else "EmberDeep", r1 * 1.0 + 1.0, 2.6, 0, 0, 0, n=12, m=4)
    if i % 3 == 0:
        with frame(q, xf(-(s0 + 6), 0, 0, ry=90)):
            torus(q, "Gold", wr(s0) * 1.0 + 2.4, 3.0, 0, 0, 0, n=12, m=4)
    # charred dorsal plates over the back, and spines (crown continues down the trunk)
    for k, f in enumerate((0.25, 0.55, 0.85)):
        s = lerp(s0, s1, f)
        r = wr(s) * (1.07 if abs(f - 0.55) < 0.2 else 1.0)
        box(q, "CharDark" if k % 2 else "Char", -s, 0, r * 0.97, 14, r * 1.1, 5, ry=-8 + k * 4)
        box(q, "EmberDeep", -s - 6, 0, r * 0.99 + 0.3, 3, r * 0.5, 4.2, ry=-8 + k * 4)
    spine_h = max(10, 66 - 3.4 * i) if not last else 22
    lean_spike(q, ("Basalt", "Char", "BasaltLight")[i % 3], -sm, 0, rm * 0.96, spine_h, -34, n=5)
    lean_spike(q, GLOW[i % 3], -sm - 1, 0, rm * 0.98, spine_h * 0.58, -34, n=4, down=1)
    for s in (-1, 1):
        lean_spike(q, "CharDark", -sm + 8, s * rm * 0.66, rm * 0.74, spine_h * 0.42, -30, roll=s * 30, n=4)
    # ember cracks running down the flanks, belly line
    for s in (-1, 1):
        for k in range(2):
            ph = rng.uniform(0, 6)
            pts = []
            for m in range(5):
                f = m / 4
                sx = lerp(s0 + 3, s1 - 3, f)
                ang = math.radians(-8 + 34 * k + 16 * math.sin(ph + f * 5))
                rr = wr(sx) * 1.03
                pts.append((-sx, s * rr * math.cos(ang), rr * math.sin(ang)))
            tube(q, "EmberHot" if (k + i) % 2 else "EmberDeep", pts, [1.5, 2.2, 2.6, 2.0, 1.2], n=3)
    if last:
        tip = -(s1 + 34)
        for s in (-1, 1):
            blade(q, "CharDark", [(-s1 + 4, 0, 0), (tip + 14, s * 20, 0), (tip - 22, s * 38, 0)], [10, 14, 3], [1.6, 1.6, 1.0],
                  up=(0, 0, 1))
            blade(q, "EmberHot", [(-s1 + 2, 0, 0.8), (tip + 10, s * 19, 0.8), (tip - 16, s * 36, 0.8)], [2.2, 3, 1], [1.2, 1.2, 0.8],
                  up=(0, 0, 1))
        blade(q, "CharDark", [(-s1 + 4, 0, 4), (tip + 6, 0, 28), (tip - 24, 0, 52)], [10, 14, 3], [1.4, 1.4, 1.0], up=(0, 1, 0))
        orb(q, "Magma", tip + 12, 0, 0, 5, n=6)
    return q


def wyrm_fins(c, segs):
    for fi, sidx in enumerate(FIN_SEGS):
        parent = segs[sidx - 1]
        sf = (sidx - 0.5) * SEG
        r = wr(sf) * 1.03
        scale = 1.0 if fi == 0 else 1.12
        for s in (-1, 1):
            q = c.part("fin_%s" % ("fore" if fi == 0 else "rear"), "Flap", hinge=(-sf, s * r * 0.55, -r * 0.22),
                       axis=(1, 0, 0), amp=0.42, rate=0.16, phase=0.0 if s > 0 else math.pi, chain=parent,
                       lag=0.0, gait="Flight")
            L = 80 * scale
            base = [(-sf + 14, s * r * 0.5, -r * 0.2), (-sf - 6, s * (r + 26 * scale), -r * 0.22 - 4),
                    (-sf - 34 * scale, s * (r + 54 * scale), -r * 0.2 - 6), (-sf - 68 * scale, s * (r + L), -r * 0.2 - 8)]
            blade(q, "CharDark", base, [24 * scale, 30 * scale, 24 * scale, 9], [4, 3.2, 2.4, 1.2], up=(0, 0, 1))
            blade(q, "EmberDeep", [(x - 6, y, z + 1.2) for x, y, z in base[1:]], [4.5, 4, 2],
                  [2.4, 2.0, 1.2], up=(0, 0, 1))
            blade(q, "Gold", [(x + 16 * scale, y, z + 0.6) for x, y, z in base[:3]], [2.6, 3, 2.4], [3.2, 2.8, 2.4], up=(0, 0, 1))
            for k in range(3):                          # bone rays
                tube(q, "BasaltLight", [(x, y * (1 - 0.0), z + 1.6) for (x, y, z) in
                                        (base[0], base[1], (base[2][0] - k * 10 + 10, base[2][1] + s * 0 + k * s * 4, base[2][2]))],
                     [2.0, 1.8, 0.4], n=3)
            shard(q, GLOW[(fi + (0 if s > 0 else 1)) % 3], base[2][0], base[2][1], base[2][2] + 3, 5, 18, 2, n=4, tilt=0)
            orb(q, "EmberHot", base[3][0], base[3][1], base[3][2], 3.5, n=5)


def build_wyrm():
    c = Creature("cinder_wyrm", "COLOSSAL", ["EMBERFALL"], "ash-and-ember sky serpent, head along +X")
    wyrm_head(c)
    wyrm_jaw(c)
    rng = random.Random("wyrm")
    segs = []
    prev = None
    for i in range(1, NSEG + 1):
        prev = wyrm_segment(c, i, prev, rng)
        segs.append(prev)
    wyrm_fins(c, segs)
    return c


# ---------------------------------------------------------------------------------------------------------
# AETHER NAUTILUS
# ---------------------------------------------------------------------------------------------------------
G_TURN = 3.2                                  # whorl growth per turn
B_LOG = math.log(G_TURN) / (2 * math.pi)
R0 = 15.5
TH0, TH1 = 0.9, 2 * math.pi * 1.78            # spiral start (apex) and aperture
PSI_END = -math.pi / 2 - 0.30                 # aperture angle (bottom, a little toward -X) ; clockwise coil
PHI0 = TH1 + PSI_END
WIDTH = 1.12                                  # half-width (y) over radial half-height
RHO = 0.60                                    # tube radius over centreline radius
STEPS = 58


def spi(th):
    psi = -th + PHI0
    R = R0 * math.exp(B_LOG * th)
    c = Vector((R * math.cos(psi), 0.0, R * math.sin(psi)))
    radial = Vector((math.cos(psi), 0.0, math.sin(psi)))
    return c, radial, R, psi


def nautilus_shell(c):
    p = c.body
    ths = [lerp(TH0, TH1, i / STEPS) for i in range(STEPS + 1)]
    rings = []
    for th in ths:
        cc, radial, R, psi = spi(th)
        rho = RHO * R
        rings.append((cc, (0, 1, 0), radial, rho * WIDTH, rho))
    rings.insert(0, (spi(TH0 - 0.35)[0], (0, 1, 0), spi(TH0 - 0.35)[1], 0.0, 0.0))     # apex point
    rng = random.Random("naut")
    N = 14

    def f(k, col):
        step = max(k - 1, 0)
        chamber = step // 2
        side = col in (2, 3, 4, 9, 10, 11)                 # ellipse sides (+-Y), a flatter wall
        # col angle t = 2*pi*col/N ; u=Y so cos -> side, sin -> radial. sides: col near 0 and N/2
        side = col in (0, 1, 6, 7, 8, 13)
        if side:
            if step % 2 == 0:
                return "Opal" if chamber % 2 == 0 else "PearlViolet"
            return "Pearl" if chamber % 3 else "PearlRose"
        if col in (3, 4):                                   # outer ridge: gold keel and growth bands
            return "Gold" if chamber % 4 == 0 else ("DeepPearl" if chamber % 2 else "Pearl")
        if col in (10, 11):
            return "DeepPearl" if chamber % 2 else "Mantle"
        return "PearlViolet" if (chamber + col) % 2 else "Pearl"
    loft(p, rings, f, n=N, cap1=True, cap_mat="Mantle")
    # septa ribs on both flanks (chamber walls), raised, with a marble/gold cadence
    for i in range(2, STEPS, 2):
        th = ths[i]
        cc, radial, R, psi = spi(th)
        rho = RHO * R
        for s in (-1, 1):
            if rho < 7:
                continue
            ang = -math.degrees(psi)
            mat = "Gold" if (i // 2) % 4 == 0 else "Marble"
            box(p, mat, cc.x, s * rho * WIDTH * 0.985, cc.z, rho * 1.35, 2.4, 2.8, ry=ang)
    # spiral growth ridges: glowing crystals along the outer keel
    for i in range(6, STEPS + 1, 4):
        cc, radial, R, psi = spi(ths[i])
        rho = RHO * R
        tip = cc + radial * rho * 1.0
        ang = math.degrees(psi)
        with frame(p, xf(tip.x, 0, tip.z, ry=-(ang - 90))):
            crystal(p, GLOW[(i // 4) % 3], 0, 0, 0, max(rho * 0.12, 3), rho * 0.5, 2, 4)
    # the aperture lip: a gold collar
    cc, radial, R, psi = spi(TH1)
    rho = RHO * R
    tang = Vector((math.sin(psi), 0, -math.cos(psi)))      # direction of travel at the aperture (clockwise)
    return cc, radial, tang, rho


def naut_head(c, ap, rho):
    """Hood, mantle, eyes. The head overlaps the aperture; hinge at the aperture (nod)."""
    zc = ap.z
    xa = ap.x
    q = c.part("head", "Flap", hinge=(xa + 10, 0, zc), axis=(0, 1, 0), amp=0.06, rate=0.06, phase=0.0, gait="Always")
    a0, b0 = rho * WIDTH * 0.93, rho * 0.93
    specs = [(xa + 22, a0 * 0.96, b0 * 0.96, zc), (xa - 30, a0 * 1.04, b0 * 1.02, zc + 2), (xa - 90, a0 * 0.92, b0 * 0.9, zc),
             (xa - 150, a0 * 0.66, b0 * 0.68, zc - 4), (xa - 190, a0 * 0.40, b0 * 0.44, zc - 8)]

    def f(k, col):
        if col in (2, 3, 4, 5):
            return "Mantle" if (k + col) % 2 else "DeepPearl"
        if col in (9, 10, 11, 12):
            return "MantleLight"
        return "MantleLight" if (k + col) % 2 else "Mantle"
    xloft(q, specs, f, n=14, cap1=True, cap_mat="MantleLight")
    # hood: a thick leathery pad over the aperture with gold and crystal trim
    C1["ell_solid"](q, "DeepPearl", xa - 56, 0, zc + b0 * 0.74, 92, a0 * 0.9, b0 * 0.42, n=10, steps=3)
    for s in (-1, 1):
        tube(q, "Gold", [(xa - 8, s * a0 * 0.8, zc + b0 * 0.9), (xa - 70, s * a0 * 0.92, zc + b0 * 0.78),
                         (xa - 130, s * a0 * 0.6, zc + b0 * 0.5)], [4.2, 3.8, 2.4], n=4)
        # eyes: a gold ring, a glowing orb, a dark pupil
        ex, ey, ez = xa - 108, s * a0 * 0.80, zc + b0 * 0.30
        orb(q, "Cosmic", ex, ey, ez, 15, n=8)
        orb(q, "Basalt", ex - 7, ey + s * 4, ez, 7.5, n=6)
        with frame(q, xf(ex, ey, ez, rx=90)):
            torus(q, "Gold", 17, 2.8, 0, 0, 0, n=14, m=4)
        shard(q, "Violet" if s > 0 else "Rose", xa - 44, s * a0 * 0.74, zc + b0 * 1.0, 10, 40, 4, n=5, a=0, tilt=-62)
    for k in range(5):
        shard(q, GLOW[k % 3], xa - 36 - k * 14, 0, zc + b0 * (1.02 - k * 0.04), 7 - k * 0.5, 30 - k * 3, 3, n=4, tilt=-50)
    # glowing mantle seam
    tube(q, "Opal", [(xa + 10, 0, zc + b0 * 1.02), (xa - 60, 0, zc + b0 * 1.06), (xa - 130, 0, zc + b0 * 0.7)], [3, 3.4, 2.4], n=3)
    return q, (xa - 180, zc)


def naut_funnel(c, head, ap, rho):
    zc, xa = ap.z, ap.x
    b0 = rho * 0.93
    base = (xa - 54, 0, zc - b0 * 0.74)
    hinge = (xa - 100, 0, zc - b0 * 0.86)
    q = c.part("funnel", "Pulse", hinge=hinge, axis=(0, 1, 0), amp=0.22, rate=0.13, phase=0.0, chain=head, gait="Always")
    pts = [base, (xa - 80, 0, zc - b0 * 0.92), (xa - 118, 0, zc - b0 * 1.02), (xa - 168, 0, zc - b0 * 1.06),
           (xa - 190, 0, zc - b0 * 1.02)]
    tube(q, "DeepPearl", pts, [34, 30, 24, 17, 14], n=10)
    for i, (x, z) in enumerate(((xa - 80, zc - b0 * 0.92), (xa - 118, zc - b0 * 1.02), (xa - 168, zc - b0 * 1.06))):
        with frame(q, xf(x, 0, z, ry=90 - 6)):
            torus(q, "Gold" if i != 1 else "Marble", [31, 25, 16][i], 3.6, 0, 0, 0, n=12, m=4)
    with frame(q, xf(xa - 190, 0, zc - b0 * 1.02, ry=90)):
        torus(q, "Gold", 15, 4.2, 0, 0, 0, n=12, m=4)
    orb(q, "Opal", xa - 188, 0, zc - b0 * 1.02, 8.5, n=6)                # the glow of the jet
    for s in (-1, 1):
        tube(q, "Opal", [(xa - 66, s * 25, zc - b0 * 0.80), (xa - 120, s * 20, zc - b0 * 0.92), (xa - 166, s * 13, zc - b0 * 0.98)],
             [2.2, 2.2, 1.6], n=3)
    return q


def naut_halo(c, head, ap, rho, hx):
    zc = ap.z
    xa = ap.x
    cx = xa - 70
    q = c.part("halo", "Spin", hinge=(cx, 0, zc), axis=(1, 0, 0), amp=0.0, rate=0.05, phase=0.0, chain=head, gait="Always")
    R_in = rho * 0.7
    for layer in range(2):
        nb = 12
        for k in range(nb):
            a = 2 * math.pi * (k + layer * 0.5) / nb
            dy, dz = math.cos(a), math.sin(a)
            r0 = R_in if layer == 0 else R_in + 14
            r1 = (rho * 2.55) if layer == 0 else (rho * 2.05)
            pts = []
            for m in range(5):
                f = m / 4
                rr = lerp(r0, r1, f)
                pts.append((cx - 26 * f * f - 12 * layer, dy * rr, zc + dz * rr))
            w = [14, 24, 28, 22, 6] if layer == 0 else [10, 17, 19, 14, 4]
            blade(q, ("PearlViolet", "Opal", "PearlRose")[(k + layer) % 3] if layer == 0 else ("Pearl", "Opal")[k % 2],
                  pts, w, [1.6, 1.4, 1.2, 1.0, 0.8], up=(1, 0, 0))
            if layer == 0:
                e = pts[-1]
                orb(q, GLOW[k % 3], e[0], e[1], e[2], 4.2, n=5)
    with frame(q, xf(cx, 0, zc, ry=90)):
        torus(q, "Gold", R_in + 1, 4.6, 0, 0, 0, n=24, m=4)
        torus(q, "Marble", rho * 2.0, 2.2, 0, 0, 0, n=28, m=4)
    # spokes tying the collar to the head
    for k in range(6):
        a = 2 * math.pi * k / 6
        tube(q, "Gold", [(cx, math.cos(a) * (R_in - 22), zc + math.sin(a) * (R_in - 22)),
                         (cx - 6, math.cos(a) * (R_in + 8), zc + math.sin(a) * (R_in + 8))], [3.4, 3.0], n=4)
    return q


def naut_tentacles(c, head, ap, rho, hx):
    zc = ap.z
    xa = ap.x
    root_x = hx[0] + 18
    specs = [("tent_c", 4, 0.0, (-1.0, 0.0, -0.20), 86.0, 0.10, 0.0, (0, 1, 0)),
             ("tent_l", 3, -34.0, (-1.0, -0.18, -0.36), 92.0, 0.11, 2.1, (0, 1, 0.45)),
             ("tent_r", 3, 34.0, (-1.0, 0.18, -0.36), 92.0, 0.11, 4.2, (0, 1, -0.45))]
    for name, nseg, dy, d0, L, rate, ph, axis in specs:
        d = Vector(d0).normalized()
        P = [Vector((root_x, dy, zc - 4 + (4 if dy else 0)))]
        for k in range(nseg):
            d = (d + Vector((0, 0, -0.10))).normalized()
            P.append(P[-1] + d * L * (1.0 - 0.06 * k))
        prev = head
        for k in range(nseg):
            tip = k == nseg - 1
            ax = Vector(axis).normalized()
            q = c.part(name, "Flap", hinge=tuple(P[k]), axis=tuple(ax), amp=0.16 + 0.07 * k, rate=rate, phase=ph,
                       chain=prev, lag=0.6, gait="Always")
            prev = q
            r_h = 13.0 - 2.4 * k
            r_t = 3.0 if tip else 13.0 - 2.4 * (k + 1)
            dirv = (P[k + 1] - P[k]).normalized()
            pa = dirv.cross(Vector((0, 1, 0)))
            if pa.length < 1e-4:
                pa = Vector((1, 0, 0))
            pa.normalize()
            pb = dirv.cross(pa).normalized()
            nstr = 5 if k < 2 else 4
            for si in range(nstr):
                ang = 2 * math.pi * si / nstr + k * 0.9
                off0 = (pa * math.cos(ang) + pb * math.sin(ang)) * (r_h * 0.85)
                off1 = (pa * math.cos(ang + 0.7) + pb * math.sin(ang + 0.7)) * (r_t * 0.9 + 1)
                mid = (P[k] + P[k + 1]) * 0.5 + (off0 + off1) * 0.55
                rr0 = 5.2 - 0.6 * k
                rr1 = 0.8 if tip else 5.2 - 0.6 * (k + 1)
                tube(q, ("MantleLight", "Mantle", "PearlViolet")[(si + k) % 3],
                     [P[k] + off0 * 0.5, mid, P[k + 1] + off1 + dirv * (6 if tip else 0)],
                     [rr0, (rr0 + rr1) * 0.5 + 0.6, rr1], n=4)
                if si % 2 == 0:
                    pos = mid + (pa * 0 + pb * 0)
                    orb(q, GLOW[(si + k) % 3], pos.x, pos.y, pos.z, 3.0, n=5)
            # joint: ball + collar ring, so the chain never opens
            orb(q, "Pearl", P[k + 1].x, P[k + 1].y, P[k + 1].z, r_t * 1.15 + 3.0 if not tip else 3.5, n=6)
            ry = math.degrees(math.atan2(-dirv.z, dirv.x)) + 0
            with frame(q, xf(P[k].x + dirv.x * 6, P[k].y + dirv.y * 6, P[k].z + dirv.z * 6, ry=ry)):
                torus(q, "Gold", r_h * 1.05 + 3, 2.8, 0, 0, 0, n=10, m=4, ry=90)
            if tip:
                e = P[k + 1]
                shard(q, "Opal", e.x - 4, e.y, e.z, 5, 16, 6, n=4, tilt=90)
    return


def build_nautilus():
    c = Creature("aether_nautilus", "COLOSSAL", ["ETHEREAL_SCAPE"], "pearl chambered nautilus, travel along +X")
    ap, radial, tang, rho = nautilus_shell(c)
    head, hx = naut_head(c, ap, rho)
    naut_funnel(c, head, ap, rho)
    naut_halo(c, head, ap, rho, hx)
    naut_tentacles(c, head, ap, rho, hx)
    return c


# ---------------------------------------------------------------------------------------------------------
# Assembly, checks, sidecar, export (same conventions as the colossal group)
# ---------------------------------------------------------------------------------------------------------
def finalize(c):
    lo, hi = bbox(c.body)
    shift = (lo + hi) * 0.5
    for p in [c.body] + [q for q, _m in c.parts]:
        for i, v in enumerate(p.verts):
            p.verts[i] = v - shift
    for _q, m in c.parts:
        m["hinge"] = m["hinge"] - shift
    return shift


def to_sidecar_frame(v):
    return [-v.x, v.z, v.y]


def build_sidecar(creatures):
    out = {"group": "colossal2", "frame": "orbiter", "creatures": {}}
    for c in creatures:
        blo, bhi = bbox(c.body)
        bc = (blo + bhi) * 0.5
        sz = bhi - blo
        entry = {"model": c.body.name, "class": c.cls, "size": [round(sz.x, 2), round(sz.z, 2), round(sz.y, 2)],
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


def extents(c):
    alo = Vector((1e9,) * 3)
    ahi = Vector((-1e9,) * 3)
    for p in [c.body] + [q for q, _m in c.parts]:
        lo, hi = bbox(p)
        for i in range(3):
            alo[i] = min(alo[i], lo[i])
            ahi[i] = max(ahi[i], hi[i])
    return alo, ahi


def check(creatures, limits):
    ok = True
    for c in creatures:
        allp = [c.body] + [q for q, _m in c.parts]
        total = 0
        for p in allp:
            n = tris(p)
            total += n
            lo, hi = bbox(p)
            ext = max(hi - lo)
            good = n < TRI_LIMIT and ext < ROBLOX_MESH_LIMIT
            ok &= good
            print(f"MESH {p.name:50s} {n:6d} tris  ext {ext:7.1f}  {'ok' if good else 'OVER'}")
        alo, ahi = extents(c)
        ext = ahi - alo
        lim = limits[c.id]
        good = total <= lim[0] and lim[1][0] <= max(ext) <= lim[1][1] and max(ext) < ROBLOX_MESH_LIMIT * 4
        ok &= good
        print(f"CREATURE {c.id}: {len(allp)} meshes, {total} tris, assembly extent (Blender x,y,z) "
              f"{[round(x, 1) for x in ext]}, assembly bbox lo {[round(x, 1) for x in alo]} hi {[round(x, 1) for x in ahi]} "
              f"{'ok' if good else 'LIMIT'}")
    return ok


def to_objects(creatures):
    mats = K["ensure_materials"]()
    coll = bpy.data.collections.new("Colossal2")
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


def build_all():
    creatures = [build_wyrm(), build_nautilus()]
    for c in creatures:
        finalize(c)
    return creatures


LIMITS = {"cinder_wyrm": (32000, (700, 900)), "aether_nautilus": (32000, (520, 700))}

# ---------------------------------------------------------------------------------------------------------
# Review renders
# ---------------------------------------------------------------------------------------------------------
RENDER_DIR = os.path.join(HERE, "renders")
SCRATCH = os.environ.get("COLOSSAL2_SCRATCH", os.path.join(os.environ.get("TEMP", HERE), "colossal2_renders"))
VIEWS = {
    "cinder_wyrm": [("3q_head", (0.55, -1.0, 0.30)), ("side", (-0.05, -1.0, 0.06)), ("below", (0.1, -0.5, -0.85))],
    "aether_nautilus": [("3q", (-0.55, -1.0, 0.28)), ("side", (0.0, -1.0, 0.04)), ("front", (-1.0, -0.35, 0.12))],
}


def render_all(creatures, objs, argv):
    final = "--final" in argv
    out = RENDER_DIR if final else SCRATCH
    os.makedirs(out, exist_ok=True)
    C1["_scene_setup"]()
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
        d = max(hi - lo) * 1.15
        for vname, dirv in VIEWS[c.id]:
            loc = cen + Vector(dirv).normalized() * d
            tiles.append(C1["_shot"](f"{c.id}_{vname}", loc, cen, out))
    sheet = os.path.join(out, "colossal2_contact_sheet.jpg")
    C1["_sheet"](tiles, 3, sheet)
    print("SHEET", sheet)
    if "--closeups" in argv:
        specs = {"cinder_wyrm": ((330, -330, 190), (30, 0, 20), 42),
                 "aether_nautilus": ((-380, -420, 90), (-60, 0, -60), 38)}
        for c in creatures:
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o not in objs[c.id]
            lc, tc, lens = specs[c.id]
            C1["_shot"](f"{c.id}_closeup", lc, tc, out, lens=lens)


def main(argv):
    creatures = build_all()
    ok = check(creatures, LIMITS)
    sidecar = build_sidecar(creatures)
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
