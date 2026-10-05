"""CROSSROADS V2 SKY ECOSYSTEM, group `mid`: four flying creatures.

    citadel_falcon  MEDIUM  Sky Citadel   marble-armoured raptor, gold trim
    canopy_drake    MEDIUM  Verdant       leaf-finned drake: wings, neck and tail chains
    aether_manta    LARGE   Ethereal      pearl-finned manta, slow undulation
    ashen_roc       LARGE   Emberfall     great ember-lit bird, charred plates

Contract: docs/design/SKY_ECOSYSTEM_CONTRACT.md sections 2, 3 and 4.1. Every
creature is ONE body mesh `hubprop_<id>` plus rigid hinged parts
`hubprop_<id>__<part>_<n>` (the sky whale paradigm). Head along +X, up +Z, FBX
settings as the existing export. The hub generator is imported READ-ONLY (runpy,
as check_walkways.py does); nothing outside this folder and the two export files
is written.

    python tools/run_blender.py -b --factory-startup --python <this file> -- --export --render
    (flags: --export, --render, --only <id>[,<id>])
"""

import json
import math
import os
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
HUB_SCRIPT = os.path.normpath(os.path.join(HERE, "..", "..", "build_crossroads_hub.py"))
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = ["x"]
G = runpy.run_path(HUB_SCRIPT, run_name="lib")          # helpers only; hub main() does not run
K = G["K"]
Piece, box, frustum, crystal, tube, orb, xf = (G[n] for n in ("Piece", "box", "frustum", "crystal", "tube", "orb", "xf"))
part_of, SUBS = G["part_of"], G["SUBS"]
REPO = G["REPO"]
EXPORT_DIR = G["EXPORT_DIR"]
RENDER_DIR = os.path.join(HERE, "renders")
SCRATCH = os.environ.get("MID_SCRATCH", os.path.join(os.environ.get("TEMP", HERE), "mid_scratch"))
TRI_LIMIT = G["TRI_LIMIT"]

# Species-local palette entries (existing names are reused untouched).
K["PALETTE"].update({
    "VerdMoss": ((78, 120, 76), False),      # drake: moss on the back plates
    "VerdLeaf": ((124, 176, 92), False),     # drake: leaf membranes and fins
    "VerdDeep": ((52, 84, 62), False),       # drake: shaded leaf, bark-green scales
    "AshPlate": ((84, 76, 86), False),       # roc: charred plates
    "AshChar": ((40, 34, 44), False),        # roc: char and soot
    "AshLight": ((136, 124, 134), False),    # roc: ash-pale feathers
    "PearlFin": ((218, 210, 240), False),    # manta: pearl fin
    "PearlDeep": ((150, 138, 206), False),   # manta: violet twilight shading
    "Dusk": ((74, 62, 128), False),          # manta: dusk edge
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())
K["REFINISH"] = False       # the Sky Citadel kit's bevel/trim pass is for deck pieces, not creature meshes

Z = Vector((0, 0, 1))


# =============================================================================
#  GEOMETRY HELPERS (all in the creature's own frame; pieces are identity-based)
# =============================================================================

def tris(p):
    return sum(len(f) - 2 for f in p.faces)


def _put(p, verts, faces, mats):
    base = len(p.verts)
    p.verts.extend(Vector(v) for v in verts)
    p.faces.extend([base + i for i in f] for f in faces)
    p.fmat.extend(mats)
    p.ftag.extend(["mid"] * len(faces))


def prism(p, mat, pts, thick):
    """A convex or star-shaped (from pts[0]) polygon extruded `thick` along its
    plane normal's vertical axis (a vector, centred on the polygon)."""
    pts = [Vector(q) for q in pts]
    if not isinstance(thick, Vector):
        thick = Vector((0, 0, thick))
    n = len(pts)
    top = [q + thick * 0.5 for q in pts]
    bot = [q - thick * 0.5 for q in pts]
    verts = top + bot
    faces = [(0, i, i + 1) for i in range(1, n - 1)]
    faces += [(n, n + i + 1, n + i) for i in range(1, n - 1)]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    _put(p, verts, faces, [mat] * len(faces))


def feather(p, mat, root, d, length, width, thick, tip=None, peak=0.65, lift=0.0):
    """A pentagonal feather/leaf blade lying along direction d from root."""
    root, d = Vector(root), Vector(d).normalized()
    nrm = Z.cross(d)
    nrm = nrm.normalized() if nrm.length > 1e-6 else Vector((0, 1, 0))
    a = root - nrm * width * 0.38
    b = root + nrm * width * 0.38
    f = root + d * length * peak - nrm * width * 0.5
    c = root + d * length * peak + nrm * width * 0.5
    e = root + d * length + Vector((0, 0, lift))
    prism(p, mat, [a, f, e, c, b], thick)
    if tip:
        g = f.lerp(e, 0.5)
        h = c.lerp(e, 0.5)
        prism(p, tip, [g, e + d * 0.0, h], thick * 1.3)


def shard(p, mat, base, tip, r, n=4, back=0.2, mid=0.35):
    """A crystal along an arbitrary axis (base -> tip): a bipyramid."""
    base, tip = Vector(base), Vector(tip)
    ax = tip - base
    L = ax.length
    a = ax / L
    u = a.cross(Z if abs(a.z) < 0.95 else Vector((1, 0, 0))).normalized()
    v = a.cross(u)
    ring = [base + a * (L * mid) + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r
            for k in range(n)]
    verts = [tip, base - a * (L * back)] + ring
    faces = []
    for k in range(n):
        i, j = 2 + k, 2 + (k + 1) % n
        faces += [(0, i, j), (1, j, i)]
    _put(p, verts, faces, [mat] * len(faces))


def loft(p, rings, mat_fn, cap_start=True, cap_end=True):
    """Skin a list of rings (each a list of n Vectors, or a single Vector apex)."""
    verts, faces, mats, idx = [], [], [], []
    for r in rings:
        if isinstance(r, Vector):
            verts.append(r)
            idx.append([len(verts) - 1])
        else:
            ids = []
            for q in r:
                verts.append(q)
                ids.append(len(verts) - 1)
            idx.append(ids)
    for ri, (A, B) in enumerate(zip(idx, idx[1:])):
        n = max(len(A), len(B))
        for k in range(n):
            k2 = (k + 1) % n
            if len(A) == 1:
                f = (A[0], B[k2], B[k])
            elif len(B) == 1:
                f = (A[k], A[k2], B[0])
            else:
                f = (A[k], A[k2], B[k2], B[k])
            c = sum((verts[i] for i in f), Vector()) / len(f)
            faces.append(f)
            mats.append(mat_fn(ri, k, c))
    if cap_start and len(idx[0]) > 2:
        faces.append(tuple(reversed(idx[0])))
        mats.append(mat_fn(0, -1, sum((verts[i] for i in idx[0]), Vector()) / len(idx[0])))
    if cap_end and len(idx[-1]) > 2:
        faces.append(tuple(idx[-1]))
        mats.append(mat_fn(len(idx) - 2, -2, sum((verts[i] for i in idx[-1]), Vector()) / len(idx[-1])))
    _put(p, verts, faces, mats)


def ring_x(x, cy, cz, ry, rz, n=8, sq=0.0):
    """A cross-section ring (normal along X), flat top and bottom at n=8."""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n + math.pi / n
        c, s = math.cos(a), math.sin(a)
        f = 1.0 - sq + sq / max(abs(c), abs(s))
        out.append(Vector((x, cy + ry * c * f, cz + rz * s * f)))
    return out


def loft_x(p, secs, n=8, top="Marble", under=None, bands=None, under_at=-0.4, sq=0.0, cap_start=True, cap_end=True):
    """secs: (x, cy, cz, ry, rz) from tail to head or head to tail; a section
    with ry == rz == 0 becomes an apex. bands: material per segment."""
    rings = []
    for (x, cy, cz, ry, rz) in secs:
        rings.append(Vector((x, cy, cz)) if ry <= 1e-6 else ring_x(x, cy, cz, ry, rz, n, sq))

    def mat_fn(ri, k, c):
        if k < 0:
            return (bands[ri if k == -1 else -1] if bands else top)
        if under and math.sin(2 * math.pi * k / n + 2 * math.pi / n) < under_at:
            return under
        return bands[ri] if bands else top

    loft(p, rings, mat_fn, cap_start, cap_end)


def ring_lens(y, le, te, zc, th, sq=0.0):
    """A thin wing/fin section (normal along Y): leading edge at x = le."""
    c = le - te
    return [Vector((le, y, zc)), Vector((le - c * 0.22, y, zc + th * 0.5)), Vector((le - c * 0.7, y, zc + th * 0.3)),
            Vector((te, y, zc)), Vector((le - c * 0.7, y, zc - th * 0.3)), Vector((le - c * 0.22, y, zc - th * 0.5))]


def loft_y(p, secs, top, bottom, edge=None):
    """secs: (y, le, te, zc, th). top = [mat per segment], etc, or one string."""
    rings = [ring_lens(*s) for s in secs]
    nseg = len(secs) - 1

    def pick(m, ri):
        return m[ri] if isinstance(m, (list, tuple)) else m

    def mat_fn(ri, k, c):
        ri = min(max(ri, 0), nseg - 1)
        if k in (0, 3) and edge:
            return pick(edge, ri)
        return pick(top, ri) if k in (0, 1, 2) or k < 0 else pick(bottom, ri)

    loft(p, rings, mat_fn)


def interp(table, x):
    """Piecewise-linear lookup in a list of (x, value) sorted by x ascending."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, v0), (x1, v1) in zip(table, table[1:]):
        if x <= x1:
            return v0 + (v1 - v0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def new_part(p, suffix, kind, axis, hinge, amp, rate, phase=0.0, chain=None, lag=0.0, gait="Flight"):
    q = part_of(p, suffix, kind, axis=axis, hinge=hinge, amp=amp, rate=rate, phase=phase)
    q.cm = {"kind": kind, "axis": Vector(axis).normalized(), "hinge": Vector(hinge), "amp": amp, "rate": rate,
            "phase": phase, "chain": chain.name if chain else None, "lag": lag, "gait": gait}
    return q


def eye(p, x, y, z, r=0.5, rim="Gold"):
    orb(p, rim, x, y * 0.94, z, r * 1.25, n=6)
    orb(p, "Cosmic", x, y, z, r, n=6)


# =============================================================================
#  CITADEL FALCON  (MEDIUM, Sky Citadel)
# =============================================================================

def build_falcon():
    p = Piece("hubprop_citadel_falcon", "a marble-armoured raptor, head along +X, gold trim, violet crest")
    body = [(7.8, 0.0, 0.7, 1.3, 1.4), (5.6, 0.0, 0.5, 2.1, 2.3), (3.0, 0.0, 0.2, 2.8, 3.0),
            (0.0, 0.0, 0.0, 2.8, 2.8), (-3.5, 0.0, 0.1, 2.1, 2.2), (-6.3, 0.0, 0.3, 1.4, 1.4), (-8.6, 0.0, 0.4, 0.9, 0.9)]
    loft_x(p, body, n=8, top="MarbleDim", under="Basalt", under_at=-0.3)
    zt = [(s[0], s[2] + s[4] * 0.92) for s in sorted(body, key=lambda s: s[0])]
    wid = [(s[0], s[3]) for s in sorted(body, key=lambda s: s[0])]
    # armour plates down the back: marble shields rimmed in gold, pointing aft
    for i in range(5):
        x = 5.4 - i * 2.9
        w = interp(wid, x) * 0.78
        z = interp(zt, x)
        for mat, sc, dz in (("Gold", 1.14, -0.06), ("Marble", 1.0, 0.1)):
            ww, ll = w * sc, 2.5 * sc
            prism(p, mat, [Vector((x + ll * 0.55, 0, z + dz)), Vector((x + ll * 0.3, -ww, z + dz)),
                           Vector((x - ll * 0.55, -ww * 0.55, z + dz)), Vector((x - ll * 0.85, 0, z + dz)),
                           Vector((x - ll * 0.55, ww * 0.55, z + dz)), Vector((x + ll * 0.3, ww, z + dz))], 0.5)
    # gorget collar and breastplate, cyan inlay down the keel
    frustum(p, "Gold", 8, 1.55, 2.5, 0.0, 1.0, M=xf(6.6, 0, 0.5, ry=90))
    box(p, "Gold", 3.6, 0, -2.5, 3.6, 1.1, 0.6)
    box(p, "Inlay", 2.5, 0, -3.0, 7.0, 0.45, 0.35)
    for k in range(3):
        box(p, "Cosmic", 4.8 - k * 2.4, 0, -3.2, 0.7, 0.8, 0.3)
    # tucked legs and gold talons
    for s in (-1, 1):
        tube(p, "BasaltLight", [(-0.5, s * 1.9, -2.0), (-3.4, s * 1.9, -3.3), (-6.0, s * 1.9, -3.7)], [1.0, 0.75, 0.5], n=5)
        for t in (-0.45, 0.0, 0.45):
            shard(p, "Gold", (-6.0, s * 1.9 + t, -3.7), (-8.0, s * 1.9 + t * 1.5, -4.3), 0.28, n=3)
    # cyan inlay and a violet crystal at each shoulder
    for s in (-1, 1):
        shard(p, "Violet", (2.4, s * 2.4, 3.0), (0.4, s * 2.9, 5.6), 0.55)
        shard(p, "Shard", (1.6, s * 2.7, 2.7), (-0.8, s * 3.3, 4.2), 0.35)
    # a violet pennant at the tail root
    prism(p, "Canvas", [(-6.2, 0, 2.2), (-6.4, 0, 4.0), (-11.0, 0, 3.4), (-9.6, 0, 2.3)], Vector((0, 0.18, 0)))
    box(p, "Gold", -6.2, 0, 3.0, 0.4, 0.5, 2.2)

    # head: its own part, nodding on a pitch hinge at the neck
    hq = new_part(p, "head", "Flap", (0, 1, 0), (7.4, 0, 0.8), 0.12, 0.35, phase=0.0, gait="Idle")
    loft_x(hq, [(6.8, 0, 0.7, 1.3, 1.4), (8.2, 0, 1.1, 1.75, 1.7), (9.7, 0, 1.2, 1.6, 1.6), (10.7, 0, 1.0, 1.0, 1.1)],
           n=8, top="MarbleDim", under="BasaltLight", under_at=-0.1)
    tube(hq, "Gold", [(10.3, 0, 1.1), (11.9, 0, 0.8), (12.6, 0, -0.3)], [1.05, 0.7, 0.0], n=5)
    tube(hq, "Basalt", [(10.3, 0, 0.3), (11.6, 0, 0.1)], [0.55, 0.0], n=4)
    for s in (-1, 1):
        eye(hq, 9.5, s * 1.5, 1.6, 0.42)
        prism(hq, "Gold", [(10.3, s * 0.6, 2.4), (10.3, s * 1.7, 2.0), (8.3, s * 1.9, 2.5), (8.6, s * 0.7, 2.9)], 0.35)
    shard(hq, "Violet", (8.0, 0, 2.6), (5.2, 0, 4.4), 0.5)
    shard(hq, "Rose", (8.6, 0, 2.6), (6.6, 0, 4.9), 0.35)

    # wings: inner + hand, each side; the hand is chained to the inner
    inner = {}
    for s in (1, -1):
        ph = 0.0 if s > 0 else math.pi

        def wp(x, y, s=s):
            return Vector((x, s * (2.0 + (y - 2.0) * 0.86), 1.3 + 0.12 * (y - 2.0)))

        w = new_part(p, "wing", "Flap", (1, 0, 0), wp(3.0, 2.0), 0.55, 0.9, phase=ph, gait="Flight")
        inner[s] = w
        tube(w, "Marble", [wp(3.0, 2.0), wp(1.5, 5.5), wp(0.0, 9.0)], [1.1, 0.9, 0.7], n=6)
        prism(w, "Marble", [wp(3.0, 2.0), wp(0.0, 9.0), wp(-2.8, 8.6), wp(-0.8, 2.0)], 0.5)
        prism(w, "Gold", [wp(3.1, 2.0), wp(0.1, 9.0), wp(-0.5, 9.0), wp(2.6, 2.0)], 0.62)
        prism(w, "Gold", [wp(3.4, 1.6), wp(3.5, 3.2), wp(0.8, 3.4), wp(0.6, 1.6)], 0.8)
        for i in range(7):
            u = 0.06 + 0.9 * i / 6
            r0 = wp(-0.8, 2.0).lerp(wp(-2.8, 8.6), u)
            feather(w, "Marble" if i % 2 else "MarbleDim", r0 + Vector((0.4, 0, 0.12 * (i % 2))),
                    (-0.97, s * (0.1 + 0.04 * i), 0.0), 5.6 - 0.15 * i, 1.9, 0.26, tip="Gold" if i == 6 else None)
        t = new_part(p, "wingtip", "Flap", (1, 0, 0), wp(0.0, 9.0), 0.45, 0.9, phase=ph, chain=w, lag=0.5, gait="Flight")
        tube(t, "Marble", [wp(0.0, 9.0), wp(-1.0, 11.0), wp(-2.0, 12.6)], [0.75, 0.55, 0.3], n=5)
        prism(t, "Marble", [wp(0.3, 8.8), wp(-1.8, 12.8), wp(-3.2, 11.8), wp(-2.8, 8.8)], 0.45)
        prism(t, "Gold", [wp(0.4, 8.8), wp(-1.6, 12.8), wp(-2.0, 12.6), wp(0.0, 8.8)], 0.58)
        shard(t, "Violet", wp(-0.3, 9.1) + Vector((0, 0, 0.3)), wp(-0.9, 9.6) + Vector((0, 0, 1.9)), 0.4)
        for i in range(6):
            r0 = wp(-2.4 - 0.15 * i, 8.7 + 0.6 * i)
            d = Vector((-1.0 + 0.11 * i * 1.5, s * (0.55 + 0.25 * i), 0.0))
            feather(t, "Marble" if i % 2 else "MarbleDim", r0, d, 4.4 + 0.1 * i, 1.55, 0.24, tip="Gold" if i >= 4 else None)

    # tail: a two-segment chain (pitch), fanned feathers
    t1 = new_part(p, "tail", "Flap", (0, 1, 0), (-8.2, 0, 0.4), 0.16, 0.9, phase=0.0, gait="Flight")
    loft_x(t1, [(-7.8, 0, 0.4, 0.95, 0.9), (-9.4, 0, 0.4, 0.8, 0.5), (-10.8, 0, 0.4, 0.7, 0.3)], n=8, top="Marble")
    for i, a in enumerate((-26, -13, 0, 13, 26)):
        r = math.radians(a)
        feather(t1, "MarbleDim" if i % 2 else "Marble", Vector((-8.8, 0, 0.35 + 0.1 * (i % 2))),
                (-math.cos(r), math.sin(r), 0), 4.6 - abs(a) * 0.02, 1.9, 0.24)
    t2 = new_part(p, "tail", "Flap", (0, 1, 0), (-11.4, 0, 0.4), 0.2, 0.9, phase=0.0, chain=t1, lag=0.45, gait="Flight")
    for i, a in enumerate((-18, -9, 0, 9, 18)):
        r = math.radians(a)
        feather(t2, "Marble" if i % 2 else "MarbleDim", Vector((-11.4, 0, 0.35 + 0.1 * (i % 2))),
                (-math.cos(r), math.sin(r), 0), 5.5 - abs(a) * 0.03, 1.8, 0.22, tip="Gold")
    # breastplate breathing and a flickering crown of crystal
    br = new_part(p, "breath", "Pulse", (1, 1, 1), (3.0, 0, -0.2), 0.04, 0.3, gait="Always")
    box(br, "Gold", 4.6, 0, -1.2, 2.6, 4.2, 0.9)
    box(br, "Cosmic", 4.6, 0, -1.7, 1.4, 1.4, 0.3)
    gl = new_part(p, "glow", "Flicker", (1, 0, 0), (0, 0, 0), 0.3, 1.6, gait="Always")
    for s in (-1, 1):
        shard(gl, "Cosmic", (-2.0, s * 1.6, 2.5), (-3.6, s * 1.8, 4.0), 0.3)
    return p



def fin(p, mat, x, z, length, height, y=0.0, thick=0.3, back=1.0):
    """A vertical swept fin / leaf (in the XZ plane) rooted at (x, z)."""
    prism(p, mat, [Vector((x, y, z)), Vector((x - length * 0.35 * back, y, z + height)),
                   Vector((x - length * back, y, z + height * 0.25)), Vector((x - length * 0.8 * back, y, z))],
          Vector((0, thick, 0)))


def seg_tube(p, mat, a, b, ra, rb, n=6):
    tube(p, mat, [a, (Vector(a) + Vector(b)) * 0.5, b], [ra, (ra + rb) * 0.5, rb], n=n)


# =============================================================================
#  CANOPY DRAKE  (MEDIUM, Verdant)
# =============================================================================

def build_drake():
    p = Piece("hubprop_canopy_drake", "a leaf-finned drake, head along +X; back kept flat between the shoulders")
    body = [(6.2, 0, 0.5, 1.5, 1.6), (4.0, 0, 0.3, 2.4, 2.5), (1.0, 0, 0.0, 2.9, 2.8), (-2.0, 0, 0.1, 2.5, 2.4),
            (-5.0, 0, 0.3, 1.7, 1.7), (-6.6, 0, 0.35, 1.3, 1.3)]
    loft_x(p, body, n=8, top="Basalt", under="MarbleDim", under_at=-0.2)
    box(p, "VerdMoss", 0.5, 0, 2.7, 6.0, 3.4, 0.35)                       # a flat mossy saddle-space, left clear
    box(p, "VerdLeaf", 0.5, 0, 2.95, 5.0, 2.6, 0.2)
    box(p, "Inlay", 1.0, 0, -2.85, 7.0, 0.5, 0.35)
    for k in range(4):
        box(p, "Cosmic", 3.4 - k * 2.2, 0, -3.0, 0.7, 0.9, 0.3)
    for x, hgt, m in ((4.6, 3.6, "Violet"), (-3.8, 3.2, "Rose"), (-5.2, 2.4, "Shard")):
        shard(p, m, (x, 0, 2.5), (x - 1.2, 0, 2.5 + hgt), 0.5)
    for x in (4.2, -4.4):
        for s in (-1, 1):
            fin(p, "VerdLeaf", x, 2.6, 2.6, 1.8, y=s * 1.2, thick=0.25)
    for s in (-1, 1):                                                       # tucked legs with gold talons
        tube(p, "VerdDeep", [(3.0, s * 2.4, -1.6), (1.6, s * 2.8, -3.2), (3.2, s * 2.6, -4.4)], [1.1, 0.8, 0.5], n=5)
        for t in (-0.4, 0.0, 0.4):
            shard(p, "Gold", (3.2, s * 2.6 + t, -4.4), (4.4, s * 2.6 + t * 1.5, -5.0), 0.25, n=3)
        tube(p, "VerdDeep", [(-3.0, s * 1.9, -1.6), (-4.4, s * 2.4, -3.0), (-2.6, s * 2.3, -4.2)], [1.0, 0.7, 0.45], n=5)
        for t in (-0.4, 0.0, 0.4):
            shard(p, "Gold", (-2.6, s * 2.3 + t, -4.2), (-1.4, s * 2.3 + t * 1.5, -4.8), 0.25, n=3)

    # neck: three chained pitch segments; head chained on the last
    prev = None
    rows = [(5.8, 0.5, 1.35), (8.8, 1.2, 1.2), (11.8, 2.0, 1.05)]
    for i, (x0, z0, r0) in enumerate(rows):
        q = new_part(p, "neck", "Flap", (0, 1, 0), (x0, 0, z0), 0.14, 0.4, phase=0.0, chain=prev, lag=0.45, gait="Idle")
        z1 = rows[i + 1][1] if i + 1 < len(rows) else 2.6
        r1 = rows[i + 1][2] if i + 1 < len(rows) else 0.95
        loft_x(q, [(x0 - 0.4, 0, z0, r0 * 1.05, r0 * 1.05), (x0 + 3.4, 0, z1, r1, r1)], n=8, top="Basalt", under="MarbleDim", under_at=-0.2)
        box(q, "Inlay", x0 + 1.5, 0, (z0 + z1) / 2 + r0 * 0.95, 2.2, 0.45, 0.3)
        fin(q, "VerdLeaf", x0 + 2.8, (z0 + z1) / 2 + r0 * 0.9, 2.2, 1.7, thick=0.25)
        prev = q
    hq = new_part(p, "head", "Flap", (0, 1, 0), (14.8, 0, 2.6), 0.16, 0.4, phase=0.5, chain=prev, lag=0.45, gait="Idle")
    loft_x(hq, [(14.4, 0, 2.6, 1.0, 1.0), (15.8, 0, 2.7, 1.7, 1.6), (17.4, 0, 2.5, 1.25, 1.1), (18.8, 0, 2.3, 0.7, 0.7)],
           n=8, top="Basalt", under="MarbleDim", under_at=-0.1)
    for s in (-1, 1):
        eye(hq, 16.4, s * 1.55, 3.3, 0.4)
        tube(hq, "Marble", [(15.4, s * 0.9, 3.7), (13.6, s * 1.5, 5.3), (12.0, s * 1.5, 6.3)], [0.55, 0.38, 0.0], n=5)
        orb(hq, "Rose", 13.9, s * 1.5, 5.4, 0.35, n=6)
        fin(hq, "VerdLeaf", 15.6, 3.6, 2.4, 1.6, y=s * 1.5, thick=0.2)
    shard(hq, "Violet", (15.0, 0, 3.8), (13.0, 0, 6.4), 0.45)
    box(hq, "Gold", 18.4, 0, 2.2, 0.6, 1.4, 0.35)

    # tail: four chained lateral segments
    prev = None
    tx = [(-6.0, 1.25, 0.35), (-9.0, 1.0, 0.35), (-12.0, 0.75, 0.3), (-15.0, 0.5, 0.25)]
    for i, (x0, r0, z0) in enumerate(tx):
        q = new_part(p, "tail", "Flap", (0, 0, 1), (x0, 0, z0), 0.22, 0.5, phase=0.0, chain=prev, lag=0.5, gait="Always")
        r1 = tx[i + 1][1] if i + 1 < len(tx) else 0.3
        loft_x(q, [(x0 + 0.4, 0, z0, r0, r0), (x0 - 3.2, 0, z0, r1, r1)], n=8, top="Basalt", under="MarbleDim", under_at=-0.2)
        fin(q, "VerdLeaf" if i % 2 else "VerdMoss", x0 - 0.2, z0 + r0 * 0.9, 2.6, 1.4 + 0.3 * (3 - i), thick=0.22)
        if i == 3:
            feather(q, "VerdLeaf", (x0 - 2.6, 0, z0), (-1, 0.3, 0), 3.4, 2.6, 0.2, peak=0.5)
            feather(q, "VerdLeaf", (x0 - 2.6, 0, z0), (-1, -0.3, 0), 3.4, 2.6, 0.2, peak=0.5)
            shard(q, "Rose", (x0 - 2.6, 0, z0), (x0 - 4.2, 0, z0 + 1.2), 0.3)
        prev = q

    # wings: inner arm + membrane, then a three-finger hand chained to it
    for s in (1, -1):
        ph = 0.0 if s > 0 else math.pi

        def wp(x, y, s=s):
            return Vector((x, s * y, 1.2 + 0.18 * (y - 2.4)))

        w = new_part(p, "wing", "Flap", (1, 0, 0), wp(1.5, 2.4), 0.5, 0.7, phase=ph, gait="Flight")
        seg_tube(w, "Gold", wp(1.5, 2.4), wp(0.0, 10.0), 0.8, 0.55)
        prism(w, "VerdLeaf", [wp(1.4, 2.4), wp(0.0, 10.0), wp(-2.6, 8.6), wp(-4.4, 6.0), wp(-5.6, 4.0), wp(-6.4, 2.4)], 0.22)
        prism(w, "VerdDeep", [wp(1.0, 2.4), wp(-0.2, 7.0), wp(-1.6, 6.4), wp(-2.0, 2.4)], 0.34)
        tube(w, "Gold", [wp(-0.6, 3.2), wp(-3.0, 4.6), wp(-5.0, 5.2)], [0.3, 0.25, 0.0], n=4)
        shard(w, "Violet", wp(1.3, 3.0) + Vector((0, 0, 0.2)), wp(0.8, 3.4) + Vector((0, 0, 2.0)), 0.4)
        t = new_part(p, "wingtip", "Flap", (1, 0, 0), wp(0.0, 10.0), 0.45, 0.7, phase=ph, chain=w, lag=0.55, gait="Flight")
        F = [wp(-2.2, 17.2), wp(-7.2, 15.0), wp(-9.8, 11.2)]
        for f in F:
            seg_tube(t, "Gold", wp(0.0, 10.0), f, 0.5, 0.0, n=5)
        pts = [wp(0.0, 10.0)]
        for i, f in enumerate(F):
            if i:
                nb = (F[i - 1] + f) * 0.5
                pts.append(wp(0.0, 10.0).lerp(nb, 0.82))
            pts.append(f)
        prism(t, "VerdLeaf", pts, 0.2)                       # star-shaped from the wrist: tips and scalloped notches
        prism(t, "VerdDeep", [wp(0.0, 10.0), wp(-1.6, 14.0), wp(-3.4, 12.4), wp(-3.0, 10.4)], 0.32)
        for f in F:
            feather(t, "VerdMoss", f + Vector((0.5, 0, 0)), (-0.6, s * 0.8, 0), 1.8, 1.2, 0.2, peak=0.5)
        shard(t, "Rose", wp(-0.4, 10.4) + Vector((0, 0, 0.2)), wp(-0.8, 10.8) + Vector((0, 0, 1.6)), 0.3)
    br = new_part(p, "breath", "Pulse", (1, 1, 1), (1.0, 0, -0.3), 0.04, 0.25, gait="Always")
    box(br, "Gold", 1.0, 0, -2.4, 5.0, 3.6, 0.5)
    box(br, "Cosmic", 1.0, 0, -2.75, 2.2, 1.2, 0.25)
    gl = new_part(p, "glow", "Flicker", (1, 0, 0), (0, 0, 0), 0.3, 1.4, gait="Always")
    for x in (2.0, -0.5, -3.0):
        shard(gl, "Cosmic", (x, 0, 3.0), (x - 0.8, 0, 4.2), 0.25)
    return p


# =============================================================================
#  AETHER MANTA  (LARGE, Ethereal Scape)
# =============================================================================

def build_manta():
    p = Piece("hubprop_aether_manta", "a pearl-finned manta, head along +X, three chained fin segments a side")
    body = [(14, 0, 0, 3, 2.2), (9, 0, 0.2, 10, 3.5), (2, 0, 0.3, 18, 4.6), (-6, 0, 0.2, 17, 4.0),
            (-14, 0, 0, 10, 3.0), (-21, 0, -0.2, 3.5, 1.6), (-24, 0, -0.3, 1.3, 1.0)]
    loft_x(p, body, n=8, top="PearlFin", under="Marble", under_at=-0.3, sq=0.3)
    box(p, "Dusk", 14.0, 0, -0.9, 1.6, 4.2, 0.5)                          # the mouth
    for s in (-1, 1):
        eye(p, 10.5, s * 8.2, 2.0, 0.9, rim="Marble")
        for k in range(5):                                                  # gill slits, cyan, on the belly
            box(p, "Inlay", 6.0 - k * 2.0, s * (6.0 + k * 0.5), -4.0, 0.5, 3.0, 0.3, rz=s * 18)
    box(p, "Inlay", -4, 0, -3.95, 22, 0.6, 0.3)
    for x, h, m in [(9, 5, "Violet"), (5, 6.5, "Shard"), (1, 7.5, "Rose"), (-3, 6.5, "Violet"), (-7, 5.0, "Shard"), (-11, 4.0, "Rose")]:
        shard(p, m, (x, 0, 3.6), (x - 1.8, 0, 3.6 + h), 0.9 if h > 5 else 0.7)
    for s in (-1, 1):
        for x, h, m in ((4, 4, "Rose"), (-2, 3.4, "Violet"), (-8, 3, "Shard")):
            shard(p, m, (x, s * 8, 3.0), (x - 1.2, s * 8.6, 3.0 + h), 0.55)

    spec = [
        ([(16, 3, -17, 0.2, 4.2), (23, 0, -18, -0.2, 2.6), (30, -3, -19, -0.6, 1.8)], "PearlFin", 0.32),
        ([(30, -3, -19, -0.6, 1.8), (35, -5.5, -19.5, -0.9, 1.4), (40, -8, -20, -1.2, 1.1)], "PearlFin", 0.30),
        ([(40, -8, -20, -1.2, 1.1), (44, -12, -21, -1.5, 0.8), (48, -17, -22, -1.8, 0.4)], "PearlDeep", 0.28),
    ]
    for s in (1, -1):
        ph = 0.0 if s > 0 else math.pi
        prev = None
        for i, (secs, topm, amp) in enumerate(spec):
            y0, y1 = secs[0][0], secs[-1][0]
            q = new_part(p, "fin", "Flap", (1, 0, 0), (0, s * y0, 0.0), amp, 0.18, phase=ph, chain=prev, lag=0.6, gait="Flight")
            loft_y(q, [(s * y, le, te, zc, th) for (y, le, te, zc, th) in secs], topm, "Marble" if i < 2 else "PearlFin",
                   edge="Dusk" if i == 2 else "PearlDeep")
            ym = s * (y0 + y1) * 0.5
            zt = secs[1][3] + secs[1][4] * 0.45
            box(q, "Inlay", (secs[1][1] + secs[1][2]) * 0.5 - 1.0, ym, zt, 0.5, (y1 - y0) * 0.9, 0.25)
            box(q, "Cosmic", secs[1][2] + 1.5, ym, zt - 0.1, 0.8, (y1 - y0) * 0.6, 0.22)
            prev = q
        lobe = new_part(p, "lobe", "Flap", (0, 1, 0), (13.0, s * 3.0, -0.5), 0.25, 0.25, phase=ph, gait="Idle")
        tube(lobe, "PearlDeep", [(13.0, s * 3.0, -0.5), (17.0, s * 4.6, -0.8), (21.0, s * 4.0, -1.8)], [1.5, 1.0, 0.2], n=6)
    prev = None
    for i, x0 in enumerate((-23, -34, -45, -56)):
        q = new_part(p, "tail", "Flap", (0, 1, 0), (x0, 0, -0.3), 0.22, 0.18, phase=0.0, chain=prev, lag=0.55, gait="Always")
        r0 = (1.9, 1.5, 1.1, 0.8)[i]
        r1 = (1.5, 1.1, 0.8, 0.15)[i]
        tube(q, "Marble" if i % 2 else "PearlFin", [(x0 + 0.5, 0, -0.3), (x0 - 5.5, 0, -0.3), (x0 - 11, 0, -0.3)], [r0, (r0 + r1) / 2, r1], n=6)
        if i < 3:
            box(q, "Inlay", x0 - 5.5, 0, -0.3 + r0 * 0.8, 6.0, 0.4, 0.25)
        prev = q
    shard(prev, "Violet", (-66, 0, -0.3), (-69.5, 0, 0.2), 0.3)
    br = new_part(p, "gills", "Pulse", (1, 1, 1), (2, 0, -3.0), 0.05, 0.2, gait="Always")
    box(br, "Cosmic", 2, 0, -4.35, 8.0, 1.1, 0.25)
    box(br, "Inlay", 2, 0, -4.6, 5.0, 0.6, 0.2)
    gl = new_part(p, "glow", "Flicker", (1, 0, 0), (0, 0, 0), 0.3, 1.0, gait="Always")
    for x, h in ((7, 2.4), (-1, 3.0), (-9, 2.2)):
        shard(gl, "Cosmic", (x, 0, 4.2), (x - 1, 0, 4.2 + h), 0.35)
    return p


# =============================================================================
#  ASHEN ROC  (LARGE, Emberfall)
# =============================================================================

def build_roc():
    p = Piece("hubprop_ashen_roc", "a great ember-lit bird, head along +X, charred plates, cyan-violet crystal ridge")
    body = [(26, 0, 1.0, 3.5, 3.8), (21, 0, 1.5, 6, 6.5), (12, 0, 0.5, 9.5, 10), (0, 0, 0, 10, 10.5),
            (-12, 0, 0.3, 7.5, 7.5), (-21, 0, 0.5, 4.5, 4.5), (-25, 0, 0.6, 2.8, 2.8)]
    loft_x(p, body, n=8, top="AshPlate", under="AshLight", under_at=-0.3)
    zt = [(s[0], s[2] + s[4] * 0.92) for s in sorted(body, key=lambda s: s[0])]
    wid = [(s[0], s[3]) for s in sorted(body, key=lambda s: s[0])]
    for i in range(6):                                                      # charred back plates, gold-rimmed
        x = 19.0 - i * 6.8
        w = interp(wid, x) * 0.8
        z = interp(zt, x)
        for mat, sc, dz in (("Gold", 1.1, -0.15), ("AshChar", 1.0, 0.25)):
            ww, ll = w * sc, 6.0 * sc
            prism(p, mat, [Vector((x + ll * 0.55, 0, z + dz)), Vector((x + ll * 0.3, -ww, z + dz)),
                           Vector((x - ll * 0.55, -ww * 0.55, z + dz)), Vector((x - ll * 0.85, 0, z + dz)),
                           Vector((x - ll * 0.55, ww * 0.55, z + dz)), Vector((x + ll * 0.3, ww, z + dz))], 1.2)
        box(p, "Ember", x - 0.5, 0, z + 0.9, 3.0, 0.5, 0.2)
    for s in (-1, 1):
        for x, h, m in ((16, 8, "Violet"), (9, 10, "Shard"), (2, 8, "Rose")):
            shard(p, m, (x, s * 5.0, 9.0), (x - 3, s * 6.0, 9.0 + h), 1.5)
        tube(p, "AshChar", [(2, s * 4.5, -8), (-4, s * 5, -11), (-10, s * 5, -12.5)], [2.6, 1.9, 1.3], n=6)
        for t in (-1.2, 0, 1.2):
            shard(p, "Gold", (-10, s * 5 + t, -12.5), (-14.5, s * 5 + t * 1.6, -14.0), 0.7, n=3)
    box(p, "Inlay", 6, 0, -10.2, 24, 1.2, 0.5)

    nq = new_part(p, "neck", "Flap", (0, 1, 0), (24, 0, 1.5), 0.1, 0.14, phase=0.0, gait="Idle")
    loft_x(nq, [(22, 0, 2.0, 5.5, 6.0), (29.5, 0, 3.5, 4.2, 4.5)], n=8, top="AshPlate", under="AshLight", under_at=-0.3)
    for k in range(3):
        fin(nq, "AshChar", 27.5 - k * 2.0, 7.2 - k * 0.4, 3.2, 2.6, thick=0.7)
    box(nq, "Ember", 26, 0, -0.4, 5, 3.0, 0.4)
    hq = new_part(p, "head", "Flap", (0, 1, 0), (29, 0, 3.5), 0.14, 0.14, phase=0.6, chain=nq, lag=0.5, gait="Idle")
    loft_x(hq, [(28.5, 0, 3.5, 4.2, 4.5), (32, 0, 3.8, 4.7, 4.4), (36, 0, 3.4, 3.4, 3.3), (38.5, 0, 3.2, 2.0, 2.0)],
           n=8, top="AshPlate", under="AshLight", under_at=-0.1)
    tube(hq, "Gold", [(36, 0, 3.6), (41, 0, 2.8), (45, 0, 0.4)], [3.1, 2.1, 0.0], n=6)
    tube(hq, "AshChar", [(36, 0, 1.8), (40, 0, 1.4)], [1.6, 0.0], n=4)
    for s in (-1, 1):
        eye(hq, 34.5, s * 4.0, 4.6, 0.95, rim="AshChar")
        prism(hq, "AshChar", [(36.5, s * 1.4, 6.6), (36.5, s * 4.2, 5.8), (32.0, s * 4.8, 6.6), (32.0, s * 1.8, 7.4)], 0.9)
    for k, (m, h) in enumerate((("Ember", 6), ("Violet", 8), ("Ember", 6))):
        shard(hq, m, (31.0 - k * 1.8, 0, 7.2), (26.5 - k * 3.2, 0, 7.2 + h), 1.1)

    for s in (1, -1):
        ph = 0.0 if s > 0 else math.pi

        def wp(x, y, s=s):
            return Vector((x, s * (8.0 + (y - 8.0) * 0.9), 4.0 + 0.1 * (y - 8.0)))

        w = new_part(p, "wing", "Flap", (1, 0, 0), wp(10, 8), 0.5, 0.22, phase=ph, gait="Flight")
        seg_tube(w, "AshChar", wp(10, 8), wp(-2, 30), 3.2, 1.8, n=6)
        prism(w, "AshPlate", [wp(10, 8), wp(-2, 30), wp(-17, 29), wp(-19, 8)], 1.4)
        prism(w, "AshChar", [wp(6, 9), wp(-3, 28), wp(-10, 27.5), wp(-12, 9)], 1.9)
        prism(w, "Gold", [wp(10.2, 8), wp(-1.8, 30), wp(-3.8, 30), wp(8, 8)], 1.7)
        for i in range(8):
            u = 0.04 + 0.92 * i / 7
            r0 = wp(-19, 8).lerp(wp(-17, 29), u)
            feather(w, "AshLight" if i % 2 else "AshPlate", r0 + Vector((1.5, 0, 0.3 * (i % 2))),
                    (-0.97, s * (0.08 + 0.03 * i), 0), 17.5 - 0.5 * i, 5.0, 0.8, tip="Ember" if i % 3 == 2 else None)
        for k in range(3):
            shard(w, ("Violet", "Shard", "Rose")[k], wp(8 - k * 4, 10 + k * 3) + Vector((0, 0, 1)),
                  wp(6 - k * 4, 10.6 + k * 3) + Vector((0, 0, 6 - k)), 1.0)
        t = new_part(p, "wingtip", "Flap", (1, 0, 0), wp(-2, 30), 0.42, 0.22, phase=ph, chain=w, lag=0.6, gait="Flight")
        seg_tube(t, "AshChar", wp(-2, 30), wp(-9, 41), 1.8, 0.6, n=5)
        prism(t, "AshPlate", [wp(-1, 29.5), wp(-9, 41), wp(-14, 39), wp(-14, 29.5)], 1.1)
        prism(t, "Gold", [wp(-1, 29.5), wp(-9, 41), wp(-10.6, 40.4), wp(-2.4, 29.5)], 1.4)
        for i in range(8):
            r0 = wp(-12 + 0.5 * i, 29.8 + 1.4 * i)
            d = Vector((-0.95 + 0.095 * i, s * (0.35 + 0.075 * i), 0))
            feather(t, "AshLight" if i % 2 else "AshPlate", r0, d, 14.5 + 0.4 * i, 4.0, 0.7,
                    tip="Ember" if i % 2 == 0 else "AshChar")

    prev = None
    for i, (x0, nf, L, wd) in enumerate(((-23, 5, 11, 6.0), (-31, 5, 12, 5.6), (-40, 3, 13, 4.2))):
        q = new_part(p, "tail", "Flap", (0, 1, 0), (x0, 0, 0.6), 0.14, 0.22, phase=0.0, chain=prev, lag=0.5, gait="Flight")
        loft_x(q, [(x0 + 1.5, 0, 0.6, (2.6, 2.0, 1.4)[i], (2.4, 1.8, 1.2)[i]), (x0 - 4, 0, 0.6, (2.0, 1.4, 0.9)[i], (1.6, 1.0, 0.5)[i])],
               n=8, top="AshPlate")
        for j in range(nf):
            a = math.radians((j - (nf - 1) / 2) * (14 if nf > 3 else 12))
            feather(q, "AshLight" if j % 2 else "AshPlate", (x0 - 1.5, 0, 0.5 + 0.2 * (j % 2)),
                    (-math.cos(a), math.sin(a), 0), L - abs(j - (nf - 1) / 2) * 1.0, wd, 0.7,
                    tip="Ember" if i == 2 or j % 2 == 0 else None)
        prev = q
    br = new_part(p, "core", "Pulse", (1, 1, 1), (14, 0, -4), 0.05, 0.2, gait="Always")
    orb(br, "Ember", 14, 0, -7.5, 2.4, n=8)
    box(br, "Gold", 14, 0, -9.6, 6.0, 5.0, 0.7)
    gl = new_part(p, "glow", "Flicker", (1, 0, 0), (0, 0, 0), 0.3, 1.8, gait="Always")
    for s in (-1, 1):
        for x in (14, 6, -2):
            shard(gl, "Ember", (x, s * 8.6, 6.5), (x - 1.5, s * 9.6, 9.5), 0.7)
    return p


# =============================================================================
#  BUILD / CHECK / EXPORT / RENDER
# =============================================================================

BUILDERS = {"citadel_falcon": build_falcon, "canopy_drake": build_drake, "aether_manta": build_manta, "ashen_roc": build_roc}
INFO = {
    "citadel_falcon": ("MEDIUM", ["SKY_CITADEL"], (24, 30), 3500),
    "canopy_drake": ("MEDIUM", ["VERDANT"], (28, 36), 4000),
    "aether_manta": ("LARGE", ["ETHEREAL_SCAPE"], (80, 100), 5000),
    "ashen_roc": ("LARGE", ["EMBERFALL"], (90, 110), 6000),
}


def bbox(pieces):
    pts = [v for q in pieces for v in q.verts]
    mn = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
    mx = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
    return mn, mx


SCALE = {"citadel_falcon": 0.97, "canopy_drake": 0.88}     # final fit into the contract's size classes


def rescale(p, subs, k):
    for q in [p] + subs:
        for v in q.verts:
            v *= k
    for q in subs:
        q.cm["hinge"] = q.cm["hinge"] * k


def recentre(p, subs):
    """Pivot = body centre: the body mesh's own bounding-box centre is the origin."""
    mn, mx = bbox([p])
    c = (mn + mx) * 0.5
    for q in [p] + subs:
        for v in q.verts:
            v -= c
    for q in subs:
        q.cm["hinge"] = q.cm["hinge"] - c


def build_all(only=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K["ensure_materials"]()
    coll = bpy.data.collections.new("Creatures_Mid")
    bpy.context.scene.collection.children.link(coll)
    out = {}
    for cid, fn in BUILDERS.items():
        if only and cid not in only:
            continue
        SUBS.clear()
        p = fn()
        subs = list(SUBS)
        SUBS.clear()
        if cid in SCALE:
            rescale(p, subs, SCALE[cid])
        recentre(p, subs)
        objs = []
        for q in [p] + subs:
            o = K["to_object"](q, mats, coll)
            o["kit"] = "CROSSROADS"
            o["tris"] = tris(q)
            objs.append(o)
        out[cid] = {"piece": p, "subs": subs, "objs": objs}
    return out


def local(c, body):
    """Same maths as make_layout_luau.local: importer half-turn, as OrbiterParts."""
    dx, dy, dz = c[0] - body[0], c[2] - body[2], -(c[1] - body[1])
    return (-dx, dy, -dz)


def sidecar(res):
    data = {"group": "mid", "creatures": {}}
    report = []
    for cid, r in res.items():
        cls, biome, (lo, hi), budget = INFO[cid]
        p, subs = r["piece"], r["subs"]
        bmn, bmx = bbox([p])
        amn, amx = bbox([p] + subs)
        body_c = [(a + b) / 2 for a, b in zip(bmn, bmx)]
        ext = [b - a for a, b in zip(amn, amx)]
        total = tris(p) + sum(tris(q) for q in subs)
        parts = {}
        for q in subs:
            qmn, qmx = bbox([q])
            qc = [(a + b) / 2 for a, b in zip(qmn, qmx)]
            cm = q.cm
            ax = cm["axis"]
            parts[q.name] = {
                "kind": cm["kind"],
                "offset": [round(v, 3) for v in local(qc, body_c)],
                "hinge": [round(v, 3) for v in local(cm["hinge"], body_c)],
                "axis": [round(-ax.x, 4), round(ax.z, 4), round(ax.y, 4)],
                "amp": cm["amp"], "rate": cm["rate"], "phase": round(cm["phase"], 5),
                "chain": cm["chain"], "lag": cm["lag"], "gait": cm["gait"]}
        data["creatures"][cid] = {
            "model": p.name, "class": cls,
            "size": [round(ext[0], 3), round(ext[2], 3), round(ext[1], 3)],
            "tris": total, "biome": biome, "parts": parts}
        meshes = [tris(p)] + [tris(q) for q in subs]
        longest = max(ext)
        report.append((cid, cls, ext, longest, (lo, hi), total, budget, max(meshes), len(subs),
                       [round(v, 2) for v in (bmx - bmn)], body_c))
    return data, report


def export(res, data):
    objs = [o for r in res.values() for o in r["objs"]]
    path = os.path.join(EXPORT_DIR, "creatures_mid.fbx")
    K["_export_selected"](objs, path)
    print("EXPORTED", path)
    jp = os.path.join(EXPORT_DIR, "creatures_mid.json")
    with open(jp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    print("SIDECAR", jp)


def render(res):
    import numpy as np
    os.makedirs(SCRATCH, exist_ok=True)
    ns = {"__name__": "crossroads_render", "__file__": os.path.join(G["HERE"], "render_crossroads.py")}
    exec(open(ns["__file__"], encoding="utf-8").read(), ns)
    ns["setup_world"]()
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 560, 340
    sc.render.film_transparent = False
    cam = bpy.data.objects.new("MID_Cam", bpy.data.cameras.new("MID_Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 5000
    rows = []
    for cid, r in res.items():
        for c2 in res.values():
            for o in c2["objs"]:
                o.hide_render = c2 is not r
        mn, mx = bbox([r["piece"]] + r["subs"])
        ctr = (mn + mx) * 0.5
        span = max(mx - mn)
        views = {
            "persp": (ctr + Vector((0.95, -1.5, 0.75)).normalized() * span * 1.55, ctr, None),
            "side": (ctr + Vector((0, -span * 3, 0)), ctr, span * 1.6),
            "top": (ctr + Vector((0, 0, span * 3)), ctr, span * 1.9),
            "under": (ctr + Vector((0.8, -1.2, -0.85)).normalized() * span * 1.55, ctr, None),
        }
        row = []
        for vn, (loc, tgt, ortho) in views.items():
            cam.data.type = "ORTHO" if ortho else "PERSP"
            if ortho:
                cam.data.ortho_scale = ortho
            else:
                cam.data.lens = 38
            cam.location = loc
            cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y" if vn != "top" else "Y").to_euler()
            fp = os.path.join(SCRATCH, f"{cid}_{vn}.png")
            sc.render.image_settings.file_format = "PNG"
            sc.render.filepath = fp
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(fp)
            w, h = im.size
            row.append(np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4))
            bpy.data.images.remove(im)
        rows.append(np.concatenate(row, axis=1))
        print("RENDERED", cid)
    sheet = np.concatenate(rows, axis=0)
    h, w = sheet.shape[:2]
    im = bpy.data.images.new("sheet", w, h)
    im.pixels = sheet.ravel().tolist()
    im.filepath_raw = os.path.join(RENDER_DIR, "contact_sheet.png")
    im.file_format = "PNG"
    im.save()
    print("SHEET", im.filepath_raw)


def main():
    only = None
    if "--only" in ARGV:
        only = ARGV[ARGV.index("--only") + 1].split(",")
    res = build_all(only)
    data, report = sidecar(res)
    for (cid, cls, ext, longest, rng, total, budget, mesh_max, nparts, bsize, bc) in report:
        ok = rng[0] <= longest <= rng[1] and total <= budget and mesh_max < TRI_LIMIT
        print(f"{cid:15s} {cls:7s} extent {[round(v, 1) for v in ext]} longest {longest:6.1f} (want {rng}) "
              f"tris {total} (<= {budget}) max mesh {mesh_max} parts {nparts} body {bsize} -> {'OK' if ok else 'CHECK'}")
    if "--export" in ARGV:
        export(res, data)
    if "--render" in ARGV:
        render(res)


main()
