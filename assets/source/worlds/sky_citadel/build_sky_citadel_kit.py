"""Sky Citadel chunk kit -- generator.

Run inside Blender (tested on 5.2 LTS):

    exec(open(r"<repo>/assets/source/worlds/sky_citadel/build_sky_citadel_kit.py").read())

or from a shell:

    blender --background --python build_sky_citadel_kit.py -- --export

It rebuilds the whole kit from scratch every time, so the .blend next to this
file is an OUTPUT, not a source. Change the look here, re-run, re-export.
docs/SKY_CITADEL.md is the art direction this script implements, and
docs/CHUNK_AUTHORING.md is the contract every piece has to satisfy.

What it guarantees, and checks before it will export (`validate()`):

* Every piece is ONE mesh object whose bounding box is exactly
  256 x 256 (footprint) x 256 (height: keel tip at -96, crown at +160).
  ChunkLoader sets `mesh.Size = SizeX, SizeY, SizeZ`, so a piece whose box is
  any other size is STRETCHED to fit. The four corner beacons pin X/Y; the
  keel apex and one 160-stud spire pin Z.
* The origin is the centre of the footprint, on the walking surface (z = 0).
* Every opening's deck top is at z = 0, and every opening of one Kind has the
  same width: SKYWAY 40 studs, ASCENT 72 studs.
* Nothing crosses +/-128.
* Under 10,000 triangles per piece (one Roblox MeshPart).
* Flat shading, one flat colour per face (material + baked vertex colour),
  no textures.

Axes: Blender +Y is Roblox NORTH (-Z) under the -Z Forward / Y Up export.
Blender +X is Roblox +X (east).
"""

import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

# --------------------------------------------------------------------------
# Kit-wide numbers. Every one of these is mirrored in
# src/shared/Content/Chunks/SkyCitadel.luau -- change both together.
# --------------------------------------------------------------------------

HALF = 128.0            # half the 256 footprint
KEEL_BOTTOM = -96.0     # every piece's lowest point
CROWN_TOP = 160.0       # every piece's highest point
DECK_T = 3.0            # deck slab thickness; the walk plane is z = 0
SKYWAY_W = 40.0         # connective opening width
ASCENT_W = 72.0         # arena-only opening width
REVIEW_GAP = 128.0      # half a piece of clear air between pieces on review
TRI_LIMIT = 10000

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")) \
    if "__file__" in globals() else r"C:\Dev\LUCKBOUND_v1.0"
SOURCE_DIR = os.path.join(REPO, "assets", "source", "worlds", "sky_citadel")
EXPORT_DIR = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel")

# --------------------------------------------------------------------------
# Palette. docs/SKY_CITADEL.md explains each role. sRGB 0-255.
# (rgb, emissive)
# --------------------------------------------------------------------------

PALETTE = {
    "CitadelWhite": ((232, 236, 244), False),  # decks, walls, spire shafts
    "PaleAlloy": ((176, 188, 210), False),     # trim, railings, plinths, caps
    "DeepAlloy": ((92, 104, 134), False),      # structural dark: bands, fins, poles
    "HullSlate": ((118, 124, 156), False),     # the floating keel under every deck
    "SunGold": ((236, 190, 92), False),        # the one warm accent -- sparingly
    "AzureNeon": ((120, 210, 255), True),      # SMALL emissive accents only
    "AzureDim": ((70, 128, 168), True),        # large emissive strips and inlays
    "CitadelViolet": ((138, 96, 210), False),  # roofs and banners
    "SkyGlass": ((178, 222, 242), False),      # floating crystals, fountain water
    "Verdure": ((96, 156, 124), False),        # clipped topiary in planters
}
MAT_ORDER = list(PALETTE.keys())


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def ensure_materials():
    mats = {}
    for name, (rgb, emissive) in PALETTE.items():
        mname = "SC_" + name
        m = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        lin = [srgb_to_linear(v) for v in rgb] + [1.0]
        bsdf.inputs["Base Color"].default_value = lin
        bsdf.inputs["Roughness"].default_value = 0.75
        emit_in = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if emissive:
            emit_in.default_value = lin
            bsdf.inputs["Emission Strength"].default_value = 2.5
        else:
            bsdf.inputs["Emission Strength"].default_value = 0.0
        m.diffuse_color = lin
        mats[name] = m
    return mats


# --------------------------------------------------------------------------
# Geometry accumulation. A piece is built as one vertex/face soup, then
# turned into ONE mesh object -- one MeshPart in Roblox.
# --------------------------------------------------------------------------


def xf(x=0.0, y=0.0, z=0.0, rz=0.0, rx=0.0, ry=0.0):
    rot = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ").to_matrix().to_4x4()
    return Matrix.Translation((x, y, z)) @ rot


class Piece:
    def __init__(self, name, kind_notes):
        self.name = name
        self.notes = kind_notes
        self.verts = []
        self.faces = []
        self.fmat = []

    def add(self, verts, faces, mat, M):
        base = len(self.verts)
        self.verts.extend(M @ Vector(v) for v in verts)
        self.faces.extend([base + i for i in f] for f in faces)
        self.fmat.extend([mat] * len(faces))


def box(p, mat, cx, cy, cz, sx, sy, sz, rz=0.0, rx=0.0, ry=0.0):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    p.add(v, f, mat, xf(cx, cy, cz, rz, rx, ry))


def box_span(p, mat, x0, x1, y0, y1, z0, z1):
    box(p, mat, (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0)


def frustum(p, mat, n, r0, r1, z0, z1, cx=0.0, cy=0.0, rot=None, M=None):
    """n-sided prism/cone/pyramid from z0 (radius r0) to z1 (radius r1).
    rot defaults to half a step, so n = 4 and n = 8 have flat faces on the
    axes. A radius of 0 makes an apex."""
    if rot is None:
        rot = 180.0 / n
    verts, faces = [], []

    def ring(r, z):
        if r <= 1e-6:
            verts.append((0.0, 0.0, z))
            return [len(verts) - 1]
        idx = []
        for i in range(n):
            a = math.radians(rot + 360.0 * i / n)
            verts.append((r * math.cos(a), r * math.sin(a), z))
            idx.append(len(verts) - 1)
        return idx

    A, B = ring(r0, z0), ring(r1, z1)
    if len(A) > 1 and len(B) > 1:
        for i in range(n):
            j = (i + 1) % n
            faces.append((A[i], A[j], B[j], B[i]))
        faces.append(tuple(reversed(A)))
        faces.append(tuple(B))
    elif len(A) == 1:
        for i in range(n):
            faces.append((A[0], B[(i + 1) % n], B[i]))
        faces.append(tuple(B))
    else:
        for i in range(n):
            faces.append((A[i], A[(i + 1) % n], B[0]))
        faces.append(tuple(reversed(A)))
    p.add(verts, faces, mat, (M or Matrix.Identity(4)) @ xf(cx, cy))


def torus(p, mat, R, r, cx, cy, cz, n=16, m=4, rx=0.0, ry=0.0):
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        for j in range(m):
            b = 2 * math.pi * j / m + math.pi / m
            d = R + r * math.cos(b)
            verts.append((d * math.cos(a), d * math.sin(a), r * math.sin(b)))
    for i in range(n):
        for j in range(m):
            i2, j2 = (i + 1) % n, (j + 1) % m
            faces.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    p.add(verts, faces, mat, xf(cx, cy, cz, 0, rx, ry))


def crystal(p, mat, cx, cy, cz, r, up, down, n=4, rz=0.0):
    verts = [(0, 0, up), (0, 0, -down)]
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((r * math.cos(a), r * math.sin(a), 0))
    faces = []
    for i in range(n):
        a, b = 2 + i, 2 + (i + 1) % n
        faces.append((0, a, b))
        faces.append((1, b, a))
    p.add(verts, faces, mat, xf(cx, cy, cz, rz))


def slab(p, mat, pts, z0, z1):
    """Convex polygon (CCW, XY) extruded from z0 to z1."""
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    p.add(verts, faces, mat, Matrix.Identity(4))


def spine(p, mat, y0, y1, half_w, depth):
    """Triangular keel under a bridge deck, running along Y."""
    zt = -DECK_T + 0.5
    verts = [(-half_w, y0, zt), (half_w, y0, zt), (0, y0, -depth),
             (-half_w, y1, zt), (half_w, y1, zt), (0, y1, -depth)]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    p.add(verts, faces, mat, Matrix.Identity(4))


def keel(p, pts, profile):
    """The floating hull under a deck. profile: list of (z, scale, twist_deg,
    band_material). The band material colours the faces from the PREVIOUS ring
    down to this one. A scale of 0 is the apex."""
    rings = []
    verts, faces, mats = [], [], []
    for z, s, twist, _ in profile:
        if s <= 1e-6:
            verts.append((0.0, 0.0, z))
            rings.append([len(verts) - 1])
            continue
        c, sn = math.cos(math.radians(twist)), math.sin(math.radians(twist))
        idx = []
        for x, y in pts:
            verts.append(((x * c - y * sn) * s, (x * sn + y * c) * s, z))
            idx.append(len(verts) - 1)
        rings.append(idx)
    n = len(pts)
    faces.append(tuple(rings[0]))
    mats.append(profile[0][3])
    for k in range(1, len(rings)):
        A, B, mat = rings[k - 1], rings[k], profile[k][3]
        if len(B) == 1:
            for i in range(n):
                faces.append((A[i], A[(i + 1) % n], B[0]))
                mats.append(mat)
        else:
            for i in range(n):
                j = (i + 1) % n
                faces.append((A[i], A[j], B[j], B[i]))
                mats.append(mat)
    base = len(p.verts)
    p.verts.extend(Vector(v) for v in verts)
    p.faces.extend([base + i for i in f] for f in faces)
    p.fmat.extend(mats)


def standard_keel(p, pts):
    keel(p, pts, [
        (-DECK_T + 0.5, 0.98, 0, "HullSlate"),
        (-14.0, 0.90, 4, "HullSlate"),
        (-17.0, 0.91, 4, "DeepAlloy"),
        (-40.0, 0.66, -6, "HullSlate"),
        (-58.0, 0.44, 3, "HullSlate"),
        (-61.0, 0.45, 3, "AzureDim"),
        (-78.0, 0.22, -4, "DeepAlloy"),
        (KEEL_BOTTOM, 0.0, 0, "DeepAlloy"),
    ])


def ngon(n, R, rot=None):
    if rot is None:
        rot = 180.0 / n
    return [(R * math.cos(math.radians(rot + 360.0 * i / n)),
             R * math.sin(math.radians(rot + 360.0 * i / n))) for i in range(n)]


# --------------------------------------------------------------------------
# Set pieces. Every one of these stands on z = 0 unless it is one of the
# deliberately floating anti-grav elements (halos, crystals, beacons) -- see
# "What floats on purpose" in docs/SKY_CITADEL.md.
# --------------------------------------------------------------------------


def spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0):
    frustum(p, "PaleAlloy", 8, r * 1.5, r * 1.35, 0, 4, x, y)
    frustum(p, "DeepAlloy", 8, r * 1.35, r * 1.2, 4, 6, x, y)
    h1 = H * 0.5
    frustum(p, "CitadelWhite", 8, r, r * 0.78, 6, h1, x, y)
    frustum(p, "AzureDim", 8, r * 0.84, r * 0.84, h1, h1 + 2, x, y)
    h2 = H * 0.78
    frustum(p, "CitadelWhite", 8, r * 0.78, r * 0.5, h1 + 2, h2, x, y)
    frustum(p, "SunGold", 8, r * 0.58, r * 0.58, h2, h2 + 2, x, y)
    frustum(p, "PaleAlloy", 8, r * 0.5, 0, h2 + 2, H, x, y)
    if fins:
        # buttress fins: pale, slim, and short, so the shaft still reads white
        fin_h = H * 0.18
        for k in range(4):
            a = 45 + 90 * k
            fx = x + math.cos(math.radians(a)) * r * 1.02
            fy = y + math.sin(math.radians(a)) * r * 1.02
            box(p, "PaleAlloy", fx, fy, 6 + fin_h / 2, r * 0.55, 0.7, fin_h, rz=a)
            frustum(p, "AzureNeon", 4, 0.35, 0, 6 + fin_h, 6 + fin_h + 1.2, fx, fy)
    if halo:
        torus(p, "AzureNeon", r * 1.9, 0.45, x, y, H * 0.62, n=16)
    for k in range(extra_halos):
        torus(p, "AzureNeon", r * (1.5 + 0.35 * k), 0.4, x, y, H * (0.3 + 0.12 * k), n=16)


def tower(p, x, y, r, H, roof_h=None):
    """A castle turret: white octagonal shaft, crenellated walk, violet cone."""
    frustum(p, "PaleAlloy", 8, r * 1.15, r * 1.1, 0, 3, x, y)
    frustum(p, "CitadelWhite", 8, r, r * 0.94, 3, H, x, y)
    apothem = r * 0.97 * math.cos(math.radians(22.5))
    for k in range(4):
        a = math.radians(90 * k)
        box(p, "AzureDim", x + math.cos(a) * apothem, y + math.sin(a) * apothem, H * 0.62,
            0.8, 1.4, 6, rz=90 * k)
    frustum(p, "PaleAlloy", 8, r * 0.95, r * 1.2, H, H + 2, x, y)
    frustum(p, "DeepAlloy", 8, r * 1.2, r * 1.2, H + 2, H + 3, x, y)
    edge = 2 * r * 1.2 * math.sin(math.radians(22.5))
    ap = r * 1.2 * math.cos(math.radians(22.5)) - 0.8
    for k in range(8):
        a = math.radians(45 * k)
        box(p, "PaleAlloy", x + math.cos(a) * ap, y + math.sin(a) * ap, H + 4.2,
            1.6, edge * 0.55, 2.4, rz=45 * k)
    rh = roof_h if roof_h is not None else r * 2.4
    frustum(p, "CitadelViolet", 8, r * 0.9, 0, H + 3, H + 3 + rh, x, y)
    crystal(p, "SunGold", x, y, H + 3 + rh + 1.2, 0.8, 1.6, 1.2)


def gate(p, cx, cy, width, height, depth=8.0, pylon=10.0):
    """A futurist castle gate. The opening spans cx +/- width/2, passage along Y."""
    for s in (-1, 1):
        px = cx + s * (width / 2 + pylon / 2)
        box(p, "PaleAlloy", px, cy, 1.5, pylon + 2, depth + 2, 3)
        box(p, "CitadelWhite", px, cy, height / 2, pylon, depth, height)
        box(p, "AzureDim", cx + s * (width / 2 - 0.1), cy, height * 0.42, 0.8, depth * 0.5, height * 0.72)
        frustum(p, "PaleAlloy", 4, pylon * 0.72, 0, height, height + pylon * 1.6, px, cy, rot=45)
    span = width / 2 + pylon
    box(p, "PaleAlloy", cx, cy, height - 2, 2 * span, depth, 4)
    box(p, "AzureDim", cx, cy, height - 4.3, width, depth * 0.5, 0.6)
    tilt = 16.0
    L = span / math.cos(math.radians(tilt))
    rise = math.tan(math.radians(tilt)) * span
    for s in (-1, 1):
        box(p, "CitadelWhite", cx + s * span / 2, cy, height + rise / 2 + 1.0, L, depth * 0.8, 3,
            ry=s * tilt)
    crystal(p, "SunGold", cx, cy, height + rise + 4.5, 2.2, 4.0, 2.5)


def railing(p, x0, y0, x1, y1, h=3.2, spacing=12.0):
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, round(L / spacing))
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    for i in range(n + 1):
        t = i / n
        box(p, "PaleAlloy", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, h / 2, 0.7, 0.7, h)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box(p, "PaleAlloy", mx, my, h - 0.3, L, 0.5, 0.6, rz=ang)
    box(p, "AzureDim", mx, my, 1.1, L, 0.3, 0.3, rz=ang)


def parapet(p, a, b, inset_dir, h=2.2, t=1.6, every=6.0):
    """Crenellated wall along edge a->b, pushed inward by t/2."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    ix, iy = inset_dir
    ox, oy = ix * t / 2, iy * t / 2
    mx, my = (x0 + x1) / 2 + ox, (y0 + y1) / 2 + oy
    box(p, "CitadelWhite", mx, my, h / 2, L, t, h, rz=ang)
    box(p, "AzureDim", mx, my, h - 0.25, L + 0.02, t + 0.1, 0.25, rz=ang)
    n = int(L // every)
    for i in range(n):
        t_ = (i + 0.5) / n
        box(p, "PaleAlloy", x0 + (x1 - x0) * t_ + ox, y0 + (y1 - y0) * t_ + oy, h + 0.6,
            every * 0.5, t, 1.2, rz=ang)


def parapet_ring(p, pts, skip=lambda a, b: False):
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if skip(a, b):
            continue
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        # CCW polygon: inward is the left-hand normal.
        parapet(p, a, b, (-ey / L, ex / L))


def border_band(p, pts, width=6.0):
    """A pale paved strip just inside the parapet: breaks up an all-white deck
    and reads as a walkway round the edge. 0.1 proud, so it never z-fights."""
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        L = math.hypot(ex, ey)
        ix, iy = -ey / L, ex / L
        off = 1.6 + width / 2
        ang = math.degrees(math.atan2(ey, ex))
        box(p, "PaleAlloy", (x0 + x1) / 2 + ix * off, (y0 + y1) / 2 + iy * off, 0.05,
            max(L - 2 * width, 1.0), width, 0.1, rz=ang)


def lamp(p, x, y, h=9.0):
    frustum(p, "DeepAlloy", 6, 0.9, 0.7, 0, 0.6, x, y)
    frustum(p, "DeepAlloy", 6, 0.3, 0.3, 0.6, h, x, y)
    frustum(p, "PaleAlloy", 6, 0.9, 0.5, h, h + 0.6, x, y)
    crystal(p, "AzureNeon", x, y, h + 1.8, 0.7, 1.2, 1.2)


def banner(p, x, y, rz=0.0, h=12.0):
    frustum(p, "DeepAlloy", 6, 0.3, 0.3, 0, h, x, y)
    box(p, "SunGold", x, y, h - 0.5, 4.2, 0.4, 0.4, rz=rz)
    box(p, "CitadelViolet", x, y, h - 1.0 - 3.6, 3.6, 0.25, 7.2, rz=rz)
    box(p, "SunGold", x, y, h - 3.8, 1.2, 0.4, 1.2, rz=rz)
    crystal(p, "SunGold", x, y, h + 0.6, 0.5, 1.0, 0.4)


def crate(p, x, y, s=3.0, z=0.0, rz=0.0):
    box(p, "PaleAlloy", x, y, z + s / 2, s, s, s, rz=rz)
    box(p, "DeepAlloy", x, y, z + s / 2, s + 0.2, s + 0.2, s * 0.22, rz=rz)


def planter(p, x, y):
    box(p, "DeepAlloy", x, y, 0.8, 4, 4, 1.6)
    box(p, "PaleAlloy", x, y, 1.7, 4.4, 4.4, 0.2)
    frustum(p, "Verdure", 6, 1.7, 0.9, 1.8, 4.2, x, y)
    frustum(p, "Verdure", 6, 1.3, 0, 4.2, 7.0, x, y)


def bench(p, x, y, rz=0.0):
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    box(p, "PaleAlloy", x, y, 1.45, 5, 1.6, 0.5, rz=rz)
    for d in (-1.8, 1.8):
        box(p, "DeepAlloy", x + c * d, y + s * d, 0.6, 0.5, 1.4, 1.2, rz=rz)


def holo_pedestal(p, x, y):
    frustum(p, "DeepAlloy", 8, 2.2, 1.6, 0, 3.2, x, y)
    frustum(p, "AzureDim", 8, 1.6, 1.6, 3.2, 3.5, x, y)
    crystal(p, "AzureNeon", x, y, 6.2, 0.9, 1.6, 1.6)
    torus(p, "AzureNeon", 2.0, 0.15, x, y, 6.2, n=12)


def obelisk(p, x, y, h=26.0):
    frustum(p, "DeepAlloy", 4, 4.6, 4.2, 0, 1.5, x, y, rot=45)
    frustum(p, "PaleAlloy", 4, 3.6, 1.9, 1.5, h, x, y, rot=45)
    frustum(p, "SunGold", 4, 1.9, 0, h, h + 4, x, y, rot=45)
    crystal(p, "AzureNeon", x, y, h + 8.5, 1.2, 2.2, 2.2)


def anti_grav_pylon(p, x, y, z):
    crystal(p, "SkyGlass", x, y, z, 5.0, 14.0, 10.0, n=6)
    torus(p, "AzureNeon", 7.0, 0.4, x, y, z, n=16)
    torus(p, "DeepAlloy", 8.2, 0.6, x, y, z - 3.0, n=16)


def corner_beacons(p):
    """Four beacons whose outer faces sit EXACTLY on the tile edge. They are
    what pins the mesh's X/Z bounding box to 256 -- see the module docstring."""
    c = HALF - 3.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * c, sy * c
            box(p, "PaleAlloy", x, y, 2.0, 6, 6, 12)
            box(p, "AzureDim", x, y, 9.0, 6, 6, 2)
            frustum(p, "PaleAlloy", 4, 3 * math.sqrt(2), 0, 10, 16, x, y, rot=45)
            frustum(p, "PaleAlloy", 4, 0, 3 * math.sqrt(2), -10, -4, x, y, rot=45)


def skyway_deck(p, y0, y1, rail_from, rail_to):
    """The SKYWAY opening: 40 wide, top at z = 0, running along Y from y0 to y1.
    rail_from/rail_to: the Y range the railings cover."""
    hw = SKYWAY_W / 2
    box_span(p, "CitadelWhite", -hw, hw, y0, y1, -DECK_T, 0)
    for s in (-1, 1):
        box_span(p, "AzureDim", s * hw - (0.6 if s < 0 else 0), s * hw + (0.6 if s > 0 else 0),
                 y0, y1, -2.2, -0.8)
        railing(p, s * (hw - 0.6), rail_from, s * (hw - 0.6), rail_to)
    spine(p, "HullSlate", y0, y1, hw - 2, 22)


def ascent_deck(p, y0, y1):
    """The ASCENT opening: 72 wide, top at z = 0. A grand approach, so no
    railings -- low glowing kerbs instead."""
    hw = ASCENT_W / 2
    box_span(p, "CitadelWhite", -hw, hw, y0, y1, -DECK_T, 0)
    for s in (-1, 1):
        box_span(p, "AzureDim", s * hw - (0.6 if s < 0 else 0), s * hw + (0.6 if s > 0 else 0),
                 y0, y1, -2.2, -0.8)
        box_span(p, "PaleAlloy", s * (hw - 1.2) - 0.6, s * (hw - 1.2) + 0.6, y0, y1, 0, 0.8)
    # inlaid chevrons on the approach, pointing north (toward the arena)
    for k in range(3):
        yc = y0 + (y1 - y0) * (0.25 + 0.25 * k)
        for s in (-1, 1):
            box(p, "AzureDim", s * 7, yc, 0.05, 16, 1.2, 0.3, rz=-s * 30)
    spine(p, "HullSlate", y0, y1, hw - 3, 26)


# --------------------------------------------------------------------------
# The four pieces
# --------------------------------------------------------------------------


def build_entry():
    p = Piece("chunk_entry", "ENTRY | one opening: north SKYWAY")
    R = 84.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts)
    torus(p, "AzureDim", 62, 0.35, 0, 0, 0.05, n=24)

    # north SKYWAY, abutting the octagon's north flat edge
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    parapet_ring(p, pts, skip=lambda a, b: a[1] > apo - 1 and b[1] > apo - 1)

    # arrival pad -- the spawn falls onto this; keep the column above (0,0) clear
    frustum(p, "PaleAlloy", 16, 22, 21, 0, 0.5, 0, 0)
    torus(p, "AzureNeon", 19, 0.3, 0, 0, 0.55, n=24)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        box(p, "AzureDim", math.cos(a) * 12, math.sin(a) * 12, 0.55, 6, 0.8, 0.2, rz=45 * k + 22.5)

    # the Beacon -- tallest point, pins the crown to +160
    spire(p, -50, 30, 7, CROWN_TOP, extra_halos=1)
    spire(p, 50, 30, 6, 118)
    tower(p, -54, -46, 9, 30)
    tower(p, 54, -46, 9, 30)

    banner(p, -26, apo - 8, rz=0)
    banner(p, 26, apo - 8, rz=0)
    for x, y in ((-30, -26), (30, -26), (-30, 14), (30, 14)):
        lamp(p, x, y)
    holo_pedestal(p, -24, -62)   # return portal lands near (0, -64): keep it clear
    holo_pedestal(p, 24, -62)
    for x, y in ((-40, -6), (40, -6), (-16, 50), (16, 50)):
        planter(p, x, y)
    bench(p, -40, 4, rz=90)
    bench(p, 40, 4, rz=90)
    # cargo stack by the west turret
    crate(p, -66, -18, 3.2, rz=10)
    crate(p, -62, -20, 3.2, rz=-6)
    crate(p, -64, -19, 3.0, z=3.2, rz=25)
    crate(p, 66, -16, 2.6, rz=-14)
    # floating crystals over the plaza's shoulders
    crystal(p, "SkyGlass", -34, 50, 20, 2.4, 5, 4, n=6)
    crystal(p, "SkyGlass", 34, 50, 26, 2.0, 4, 3.5, n=6)
    corner_beacons(p)
    return p


def build_path_straight():
    p = Piece("chunk_path_straight", "PATH | openings: north SKYWAY, south SKYWAY")
    R = 44.0
    pts = ngon(6, R, rot=0)     # flat edges north and south
    apo = R * math.cos(math.radians(30))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    torus(p, "AzureDim", 26, 0.3, 0, 0, 0.05, n=18)

    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)

    # railings on the hex's four slanted edges
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if abs(a[1] - b[1]) < 1e-3:     # the flat north/south edges carry the deck
            continue
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        ix, iy = -ey / L * 0.8, ex / L * 0.8
        railing(p, a[0] + ix, a[1] + iy, b[0] + ix, b[1] + iy)

    # the gatehouse the skyway passes under
    tower(p, -32, 0, 6, 64)
    tower(p, 32, 0, 6, 64)
    box(p, "PaleAlloy", 0, 0, 32, 52, 7, 4)
    box(p, "AzureDim", 0, 0, 29.7, 50, 3.5, 0.6)
    for s in (-1, 1):
        box(p, "CitadelWhite", s * 13, 0, 37.2, 27.5, 5.6, 3, ry=s * 16)
    crystal(p, "SunGold", 0, 0, 45.5, 2.0, 3.6, 2.2)

    # the mast -- pins the crown to +160
    spire(p, -30, -24, 5, CROWN_TOP)
    spire(p, 30, 24, 4.5, 104, fins=False)

    for x, y in ((17, 62), (-17, 102), (-17, -62), (17, -102)):
        lamp(p, x, y)
    banner(p, -24, 22)
    banner(p, 24, -22)
    holo_pedestal(p, -34, 12)
    crate(p, 26, -28, 3.0, rz=12)
    crate(p, 29, -31, 2.6, rz=-20)
    anti_grav_pylon(p, -76, 70, 6)
    anti_grav_pylon(p, 76, -70, 10)
    corner_beacons(p)
    return p


def build_spire_court():
    p = Piece("chunk_spire_court", "COMBAT (grove role) | openings: south SKYWAY, north ASCENT")
    h, c = 100.0, 24.0
    pts = [(-h + c, -h), (h - c, -h), (h, -h + c), (h, h - c),
           (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c)]
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts, width=8.0)

    skyway_deck(p, -HALF, -h, -HALF + 0.4, -h - 1)
    ascent_deck(p, h, HALF)

    def skip(a, b):
        return abs(a[1] - b[1]) < 1e-3 and abs(a[1]) > h - 1   # north and south edges are split below

    parapet_ring(p, pts, skip=skip)
    for x0, x1 in ((-h + c, -SKYWAY_W / 2), (SKYWAY_W / 2, h - c)):
        parapet(p, (x0, -h), (x1, -h), (0, 1))
    for x0, x1 in ((h - c, ASCENT_W / 2), (-ASCENT_W / 2, -h + c)):
        parapet(p, (x0, h), (x1, h), (0, -1))

    # avenue inlay: from the south skyway to the Ascent Gate
    box_span(p, "AzureDim", -1.5, 1.5, -h, -20, 0, 0.12)
    box_span(p, "AzureDim", -1.5, 1.5, 20, 86, 0, 0.12)
    torus(p, "AzureDim", 22, 0.3, 0, 0, 0.05, n=24)

    # the Sky Fountain
    frustum(p, "DeepAlloy", 12, 16, 16, 0, 1.2, 0, 0)
    frustum(p, "SkyGlass", 12, 14.5, 14.5, 1.2, 1.5, 0, 0)
    frustum(p, "PaleAlloy", 8, 3, 2, 1.5, 10, 0, 0)
    frustum(p, "SunGold", 8, 2, 5, 10, 11.5, 0, 0)
    crystal(p, "AzureNeon", 0, 0, 17, 2.2, 4.5, 3.5, n=6)
    torus(p, "AzureNeon", 5.5, 0.3, 0, 0, 17, n=16)
    torus(p, "AzureNeon", 7.5, 0.3, 0, 0, 21, n=16, rx=20)

    # corner turrets, twin crown spires (pin +160), lesser spires
    for sx in (-1, 1):
        for sy in (-1, 1):
            tower(p, sx * 76, sy * 76, 10, 52)
    spire(p, -42, 58, 7, CROWN_TOP, extra_halos=1)
    spire(p, 42, 58, 7, CROWN_TOP, extra_halos=1)
    spire(p, -58, -40, 5, 96, fins=False)
    spire(p, 58, -40, 5, 96, fins=False)

    # the Ascent Gate -- the arena lies beyond it
    gate(p, 0, 92, ASCENT_W, 58)
    banner(p, -30, 82)
    banner(p, 30, 82)

    for y in (-84, -56, -30):
        lamp(p, -16, y)
        lamp(p, 16, y)
    for y in (30, 58):
        lamp(p, -16, y)
        lamp(p, 16, y)
    for x, y in ((-64, 14), (-64, -8), (64, 14), (64, -8), (-30, -74), (30, -74)):
        planter(p, x, y)
    bench(p, -32, 0, rz=90)
    bench(p, 32, 0, rz=90)
    holo_pedestal(p, -24, 78)
    holo_pedestal(p, 24, 78)
    crate(p, 74, 30, 3.2, rz=8)
    crate(p, 70, 34, 3.0, rz=-12)
    crate(p, 72, 32, 2.8, z=3.2, rz=30)
    crate(p, -74, 30, 3.0, rz=-5)
    crystal(p, "SkyGlass", -66, 58, 30, 2.8, 6, 4.5, n=6)
    crystal(p, "SkyGlass", 66, 58, 24, 2.4, 5, 4, n=6)
    corner_beacons(p)
    return p


def build_boss_clearing():
    p = Piece("chunk_boss_clearing", "BOSS | one opening: south ASCENT")
    R = 112.0
    ring = ngon(16, R)
    chord_y = -math.sqrt(R * R - (ASCENT_W / 2) ** 2)
    pts = [v for v in ring if v[1] > chord_y + 0.01]
    # insert the flat south throat so the ASCENT deck abuts a straight edge
    i_insert = next(i for i in range(len(pts)) if pts[i][1] < 0 and pts[i][0] > 0)
    pts = pts[:i_insert] + [(-ASCENT_W / 2, chord_y), (ASCENT_W / 2, chord_y)] + pts[i_insert:]
    # ngon() is CCW; re-sort by angle to be safe
    pts.sort(key=lambda v: math.atan2(v[1], v[0]))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts, width=8.0)

    ascent_deck(p, -HALF, chord_y)
    parapet_ring(p, pts, skip=lambda a, b: abs(a[1] - chord_y) < 1e-3 and abs(b[1] - chord_y) < 1e-3)

    # arena floor inlay
    torus(p, "AzureDim", 64, 0.35, 0, 0, 0.05, n=32)
    torus(p, "AzureDim", 34, 0.35, 0, 0, 0.05, n=24)
    for k in range(8):
        a = 22.5 + 45 * k
        rr = 49
        box(p, "AzureDim", math.cos(math.radians(a)) * rr, math.sin(math.radians(a)) * rr, 0.05,
            30, 0.8, 0.3, rz=a)

    # the Crown Spire -- the boss's throne, pins +160
    frustum(p, "PaleAlloy", 8, 26, 24, 0, 1.5, 0, 70)
    frustum(p, "DeepAlloy", 8, 24, 23, 1.5, 3, 0, 70)
    spire(p, 0, 70, 13, CROWN_TOP, extra_halos=2)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        crystal(p, "SkyGlass", math.cos(a) * 30, 70 + math.sin(a) * 30, 52, 3.2, 7, 5, n=6)

    # obelisk ring, open to the south
    for k in range(12):
        a = 30 * k
        if 225 <= a <= 315:
            continue
        obelisk(p, math.cos(math.radians(a)) * 96, math.sin(math.radians(a)) * 96)

    tower(p, -50, -88, 8, 44)
    tower(p, 50, -88, 8, 44)
    banner(p, -34, -94)
    banner(p, 34, -94)
    banner(p, -28, 44)
    banner(p, 28, 44)
    for k in range(4):
        a = math.radians(0 + 90 * k + 45)
        crystal(p, "SkyGlass", math.cos(a) * 72, math.sin(a) * 72, 36, 5, 12, 10, n=6)
    corner_beacons(p)
    return p


BUILDERS = [build_entry, build_path_straight, build_spire_court, build_boss_clearing]


# --------------------------------------------------------------------------
# Scene assembly
# --------------------------------------------------------------------------


def to_object(p, mats, collection):
    mesh = bpy.data.meshes.get(p.name)
    if mesh:
        bpy.data.meshes.remove(mesh)
    mesh = bpy.data.meshes.new(p.name)
    mesh.from_pydata([tuple(v) for v in p.verts], [], p.faces)
    for name in MAT_ORDER:
        mesh.materials.append(mats[name])
    for poly, mname in zip(mesh.polygons, p.fmat):
        poly.material_index = MAT_ORDER.index(mname)
        poly.use_smooth = False

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in mesh.polygons:
        rgb = PALETTE[MAT_ORDER[poly.material_index]][0]
        c = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
        for li in poly.loop_indices:
            col.data[li].color_srgb = c
    mesh.color_attributes.active_color = col
    mesh.update()

    obj = bpy.data.objects.new(p.name, mesh)
    obj["kit"] = "SKY_CITADEL"
    obj["openings"] = p.notes
    collection.objects.link(obj)
    return obj


def reference_person(parent, x, y, collection, mats):
    """5-stud reference, parented to the piece so it rides the review layout.
    Named REF_ and never exported."""
    name = "REF_Person_5m_" + parent.name
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new(name)
    p = Piece(name, "")
    box(p, "SunGold", 0, 0, 1.5, 1.4, 0.8, 3.0)
    box(p, "SunGold", 0, 0, 4.25, 1.0, 1.0, 1.5)
    mesh.from_pydata([tuple(v) for v in p.verts], [], p.faces)
    mesh.materials.append(mats["SunGold"])
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x, y, 0)
    obj.parent = parent
    obj.hide_render = False
    collection.objects.link(obj)
    return obj


def reset_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    us = bpy.context.scene.unit_settings
    us.system = "METRIC"
    us.scale_length = 1.0
    us.length_unit = "METERS"


def build_kit():
    reset_scene()
    mats = ensure_materials()
    scene = bpy.context.scene
    kit = bpy.data.collections.new("SkyCitadel_Kit")
    refs = bpy.data.collections.new("Reference_NotExported")
    scene.collection.children.link(kit)
    scene.collection.children.link(refs)
    pieces, objs = [], []
    for i, builder in enumerate(BUILDERS):
        p = builder()
        obj = to_object(p, mats, kit)
        # review layout: a row, half a piece of clear air between neighbours.
        # This offset lives on the OBJECT; export_kit() zeroes it per piece.
        obj.location = (i * (2 * HALF + REVIEW_GAP), 0, 0)
        reference_person(obj, 6, 8, refs, mats)
        pieces.append(p)
        objs.append(obj)
    return pieces, objs


# --------------------------------------------------------------------------
# Validation -- the conventions, checked rather than trusted
# --------------------------------------------------------------------------


def validate(objs):
    report, ok = [], True
    for obj in objs:
        vs = [v.co for v in obj.data.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        size = mx - mn
        centre_xy = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2)
        checks = {
            "footprint 256x256": abs(size.x - 256) < 0.01 and abs(size.y - 256) < 0.01,
            "height 256 (-96..+160)": abs(mn.z - KEEL_BOTTOM) < 0.01 and abs(mx.z - CROWN_TOP) < 0.01,
            "origin centred": abs(centre_xy[0]) < 0.01 and abs(centre_xy[1]) < 0.01,
            "under 10k tris": tris < TRI_LIMIT,
            "flat shaded": not any(p.use_smooth for p in obj.data.polygons),
        }
        piece_ok = all(checks.values())
        ok = ok and piece_ok
        report.append({
            "piece": obj.name,
            "ok": piece_ok,
            "tris": tris,
            "min": [round(c, 3) for c in mn],
            "max": [round(c, 3) for c in mx],
            "failed": [k for k, v in checks.items() if not v],
        })
    return ok, report


# --------------------------------------------------------------------------
# Export -- one FBX per piece, parked at the origin
# --------------------------------------------------------------------------


def _ui_override(**extra):
    """Operators like the FBX exporter read context.selected_objects, which a
    script run from a timer (the Blender MCP bridge) does not have. Borrow the
    first window/area so the same code works from the UI, a timer, or
    --background (where there is no window and the plain context suffices)."""
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                return bpy.context.temp_override(window=window, area=area, **extra)
    return bpy.context.temp_override(**extra)


def export_kit(objs):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    written = []
    for obj in objs:
        saved = obj.location.copy()
        obj.location = (0, 0, 0)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        path = os.path.join(EXPORT_DIR, obj.name + ".fbx")
        with _ui_override(selected_objects=[obj], active_object=obj, object=obj):
            _export_fbx(path)
        obj.location = saved
        written.append(path)
    bpy.context.view_layer.update()
    return written


def _export_fbx(path):
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        colors_type="SRGB",
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )


def verify_exports(paths):
    """Re-import every FBX into a throwaway scene and measure it. A 256 piece
    must come back 256 -- this is the millimetre check from CHUNK_AUTHORING.md,
    done here rather than trusted."""
    results = []
    coll = bpy.data.collections.new("_fbx_verify")
    bpy.context.scene.collection.children.link(coll)
    try:
        for path in paths:
            before = set(bpy.data.objects)
            with _ui_override():
                bpy.ops.import_scene.fbx(filepath=path)
            new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
            pts = [o.matrix_world @ v.co for o in new for v in o.data.vertices]
            mn = [min(p[i] for p in pts) for i in range(3)]
            mx = [max(p[i] for p in pts) for i in range(3)]
            results.append({
                "file": os.path.basename(path),
                "meshes": len(new),
                "size": [round(mx[i] - mn[i], 3) for i in range(3)],
                "min_z": round(mn[2], 3),
            })
            for o in new:
                bpy.data.objects.remove(o, do_unlink=True)
    finally:
        bpy.data.collections.remove(coll)
    return results


def main(export=False, save=True):
    pieces, objs = build_kit()
    ok, report = validate(objs)
    out = {"valid": ok, "pieces": report}
    if export:
        if not ok:
            raise RuntimeError("validation failed; not exporting: %r" % report)
        paths = export_kit(objs)
        out["exported"] = verify_exports(paths)
    if save:
        os.makedirs(SOURCE_DIR, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE_DIR, "sky_citadel_kit.blend"))
    return out


if __name__ == "__main__":
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    print(main(export="--export" in argv))
