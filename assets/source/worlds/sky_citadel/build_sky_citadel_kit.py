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
import random
from contextlib import contextmanager

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
    """One chunk being built. Besides the geometry soup it keeps lists of
    axis-aligned boxes, used ONLY for validation:

    * `solids` -- the big fixed things (spires, towers, gates, buildings).
    * `floats` -- everything that hangs in the air on purpose (crystals,
      pylons, beacons, skiffs, hoops).
    * `slabs`  -- deck outlines, so a float can be kept off the deck.

    `validate()` fails a piece if two floats intersect, if a float intersects
    a solid or a deck, or if a float comes within FLOAT_EDGE_MARGIN of the
    tile edge -- the last is what guarantees two neighbouring pieces' floating
    objects can never clip into each other, whatever the rotation."""

    def __init__(self, name, kind_notes):
        self.name = name
        self.notes = kind_notes
        self.verts = []
        self.faces = []
        self.fmat = []
        self.base = Matrix.Identity(4)
        self.solids = []
        self.floats = []
        self.slabs = []
        self.rng = random.Random(name)   # seeded by name: rebuilds are identical

    def add(self, verts, faces, mat, M):
        base = len(self.verts)
        W = self.base @ M
        self.verts.extend(W @ Vector(v) for v in verts)
        self.faces.extend([base + i for i in f] for f in faces)
        self.fmat.extend([mat] * len(faces))

    def world_box(self, x0, x1, y0, y1, z0, z1):
        pts = [self.base @ Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        return (min(q.x for q in pts), max(q.x for q in pts), min(q.y for q in pts),
                max(q.y for q in pts), min(q.z for q in pts), max(q.z for q in pts))

    def _cyl(self, x, y, r, z0, z1):
        c = self.base @ Vector((x, y, 0))
        return ("cyl", c.x, c.y, r, z0, z1)

    def solid(self, label, x, y, r, z0, z1):
        self.solids.append((label, self._cyl(x, y, r, z0, z1)))

    def solid_box(self, label, x0, x1, y0, y1, z0, z1):
        self.solids.append((label, ("box",) + self.world_box(x0, x1, y0, y1, z0, z1)))

    def float_(self, label, x, y, r, z0, z1):
        self.floats.append((label, self._cyl(x, y, r, z0, z1)))

    def float_box(self, label, x0, x1, y0, y1, z0, z1):
        self.floats.append((label, ("box",) + self.world_box(x0, x1, y0, y1, z0, z1)))

    def slab_area(self, pts, z0=-40.0, z1=1.0):
        w = [tuple((self.base @ Vector((x, y, 0)))[:2]) for x, y in pts]
        self.slabs.append((w, z0, z1))


@contextmanager
def oriented(p, rz):
    """Build inside this block as if facing north; it lands rotated by rz
    degrees about the origin. -90 turns a north opening into an east one."""
    saved = p.base
    p.base = saved @ xf(rz=rz)
    try:
        yield
    finally:
        p.base = saved


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
    p.slab_area(pts)
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


def keel(p, pts, profile, centre=(0.0, 0.0)):
    """The floating hull under a deck. profile: list of (z, scale, twist_deg,
    band_material). The band material colours the faces from the PREVIOUS ring
    down to this one. A scale of 0 is the apex. Rings scale toward `centre`."""
    ox, oy = centre
    pts = [(x - ox, y - oy) for x, y in pts]
    rings = []
    verts, faces, mats = [], [], []
    for z, s, twist, _ in profile:
        if s <= 1e-6:
            verts.append((ox, oy, z))
            rings.append([len(verts) - 1])
            continue
        c, sn = math.cos(math.radians(twist)), math.sin(math.radians(twist))
        idx = []
        for x, y in pts:
            verts.append((ox + (x * c - y * sn) * s, oy + (x * sn + y * c) * s, z))
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
    p.verts.extend(p.base @ Vector(v) for v in verts)
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
# Clearance tests for the float checks
# --------------------------------------------------------------------------

FLOAT_EDGE_MARGIN = 4.0   # a float stays this far inside the tile edge
FLOAT_GAP = 1.0           # and this far from anything else


def _xy_extent(shape):
    if shape[0] == "cyl":
        _, x, y, r, _, _ = shape
        return x - r, x + r, y - r, y + r
    return shape[1], shape[2], shape[3], shape[4]


def _z(shape):
    return (shape[4], shape[5]) if shape[0] == "cyl" else (shape[5], shape[6])


def shapes_clash(a, b, gap=FLOAT_GAP):
    az, bz = _z(a), _z(b)
    if az[1] + gap <= bz[0] or bz[1] + gap <= az[0]:
        return False
    if a[0] == "cyl" and b[0] == "cyl":
        return math.hypot(a[1] - b[1], a[2] - b[2]) < a[3] + b[3] + gap
    if a[0] == "box" and b[0] == "box":
        return not (a[2] + gap <= b[1] or b[2] + gap <= a[1] or a[4] + gap <= b[3] or b[4] + gap <= a[3])
    c, bx = (a, b) if a[0] == "cyl" else (b, a)
    nx = min(max(c[1], bx[1]), bx[2])
    ny = min(max(c[2], bx[3]), bx[4])
    return math.hypot(c[1] - nx, c[2] - ny) < c[3] + gap


def shape_over_slab(shape, slab_entry, gap=FLOAT_GAP):
    """Does a float sit over/inside a deck (its upper keel included)?"""
    pts, z0, z1 = slab_entry
    sz = _z(shape)
    if sz[1] + gap <= z0 or z1 + gap <= sz[0]:
        return False
    x0, x1, y0, y1 = _xy_extent(shape)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = max(x1 - x0, y1 - y0) / 2
    n = len(pts)
    worst = math.inf   # signed distance to the polygon, + inside
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        d = ((cx - ax) * -ey + (cy - ay) * ex) / L   # CCW: + is inside
        worst = min(worst, d)
    return worst > -(r + gap)


def shape_fits_tile(shape):
    x0, x1, y0, y1 = _xy_extent(shape)
    lim = HALF - FLOAT_EDGE_MARGIN
    return x0 >= -lim and x1 <= lim and y0 >= -lim and y1 <= lim


def free_for_float(p, shape):
    if not shape_fits_tile(shape):
        return False
    if any(shapes_clash(shape, s) for _, s in p.solids + p.floats):
        return False
    return not any(shape_over_slab(shape, sl) for sl in p.slabs)


# --------------------------------------------------------------------------
# Set pieces. Every one of these stands on z = 0 unless it is one of the
# deliberately floating anti-grav elements (halos, crystals, beacons) -- see
# "What floats on purpose" in docs/SKY_CITADEL.md.
# --------------------------------------------------------------------------


def spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    """A needle spire standing on z0 (0 = the deck; higher = on a roof), its
    needle reaching z = H. Proportions are taken over the span H - z0."""
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "PaleAlloy", 8, r * 1.5, r * 1.35, z0, z0 + 4, x, y)
    frustum(p, "DeepAlloy", 8, r * 1.35, r * 1.2, z0 + 4, z0 + 6, x, y)
    h1 = z0 + L * 0.5
    frustum(p, "CitadelWhite", 8, r, r * 0.78, z0 + 6, h1, x, y)
    frustum(p, "AzureDim", 8, r * 0.84, r * 0.84, h1, h1 + 2, x, y)
    h2 = z0 + L * 0.78
    frustum(p, "CitadelWhite", 8, r * 0.78, r * 0.5, h1 + 2, h2, x, y)
    frustum(p, "SunGold", 8, r * 0.58, r * 0.58, h2, h2 + 2, x, y)
    frustum(p, "PaleAlloy", 8, r * 0.5, 0, h2 + 2, H, x, y)
    if fins:
        # buttress fins: pale, slim, and short, so the shaft still reads white
        fin_h = L * 0.18
        for k in range(4):
            a = 45 + 90 * k
            fx = x + math.cos(math.radians(a)) * r * 1.02
            fy = y + math.sin(math.radians(a)) * r * 1.02
            box(p, "PaleAlloy", fx, fy, z0 + 6 + fin_h / 2, r * 0.55, 0.7, fin_h, rz=a)
            frustum(p, "AzureNeon", 4, 0.35, 0, z0 + 6 + fin_h, z0 + 6 + fin_h + 1.2, fx, fy)
    if halo:
        torus(p, "AzureNeon", r * 1.9, 0.45, x, y, z0 + L * 0.62, n=16)
    for k in range(extra_halos):
        torus(p, "AzureNeon", r * (1.5 + 0.35 * k), 0.4, x, y, z0 + L * (0.3 + 0.12 * k), n=16)


def tower(p, x, y, r, H, roof_h=None, roof=True):
    """A castle turret: white octagonal shaft, crenellated walk, violet cone."""
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + (roof_h if roof_h is not None else r * 2.4))
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
    if not roof:
        frustum(p, "PaleAlloy", 8, r * 1.05, r * 1.05, H + 2, H + 3, x, y)   # a flat roof to stand a spire on
        return
    rh = roof_h if roof_h is not None else r * 2.4
    frustum(p, "CitadelViolet", 8, r * 0.9, 0, H + 3, H + 3 + rh, x, y)
    crystal(p, "SunGold", x, y, H + 3 + rh + 1.2, 0.8, 1.6, 1.2)


def gate(p, cx, cy, width, height, depth=8.0, pylon=10.0):
    """A futurist castle gate. The opening spans cx +/- width/2, passage along Y."""
    span_ = width / 2 + pylon + 1
    p.solid_box("gate", cx - span_, cx + span_, cy - depth / 2 - 1, cy + depth / 2 + 1,
                0, height + math.tan(math.radians(16)) * span_ + 9)
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


def float_crystal(p, mat, x, y, z, r, up, down, n=6, rz=0.0):
    """A crystal that hangs in the air on purpose. Registered, so validate()
    can prove it clips into nothing -- not a neighbour, not a spire."""
    p.float_("floating crystal", x, y, r, z - down, z + up)
    crystal(p, mat, x, y, z, r, up, down, n=n, rz=rz)


def holo_pedestal(p, x, y):
    p.solid("pedestal", x, y, 2.4, 0, 8)
    frustum(p, "DeepAlloy", 8, 2.2, 1.6, 0, 3.2, x, y)
    frustum(p, "AzureDim", 8, 1.6, 1.6, 3.2, 3.5, x, y)
    crystal(p, "AzureNeon", x, y, 6.2, 0.9, 1.6, 1.6)
    torus(p, "AzureNeon", 2.0, 0.15, x, y, 6.2, n=12)


def obelisk(p, x, y, h=26.0):
    p.solid("obelisk", x, y, 4.6, 0, h + 11)
    frustum(p, "DeepAlloy", 4, 4.6, 4.2, 0, 1.5, x, y, rot=45)
    frustum(p, "PaleAlloy", 4, 3.6, 1.9, 1.5, h, x, y, rot=45)
    frustum(p, "SunGold", 4, 1.9, 0, h, h + 4, x, y, rot=45)
    crystal(p, "AzureNeon", x, y, h + 8.5, 1.2, 2.2, 2.2)


def anti_grav_pylon(p, x, y, z):
    p.float_("anti-grav pylon", x, y, 8.8, z - 10, z + 14)
    crystal(p, "SkyGlass", x, y, z, 5.0, 14.0, 10.0, n=6)
    torus(p, "AzureNeon", 7.0, 0.4, x, y, z, n=16)
    torus(p, "DeepAlloy", 8.2, 0.6, x, y, z - 3.0, n=16)


def _beacon_post(p, x, y, z, k, rz):
    box(p, "PaleAlloy", x, y, z, 6 * k, 6 * k, 12 * k, rz=rz)
    box(p, "AzureDim", x, y, z + 7 * k, 6 * k, 6 * k, 2 * k, rz=rz)
    frustum(p, "PaleAlloy", 4, 3 * math.sqrt(2) * k, 0, z + 8 * k, z + 14 * k, x, y, rot=45 + rz)
    frustum(p, "PaleAlloy", 4, 0, 3 * math.sqrt(2) * k, z - 12 * k, z - 6 * k, x, y, rot=45 + rz)
    return 3 * math.sqrt(2) * k, z - 12 * k, z + 14 * k


def _beacon_shard(p, x, y, z, k, rz):
    crystal(p, "SkyGlass", x, y, z, 3.2 * k, 11 * k, 8 * k, n=4, rz=rz)
    torus(p, "AzureNeon", 4.4 * k, 0.3 * k, x, y, z, n=12)
    torus(p, "DeepAlloy", 5.2 * k, 0.45 * k, x, y, z - 2.5 * k, n=12)
    return 5.7 * k, z - 8 * k, z + 11 * k


def _beacon_lantern(p, x, y, z, k, rz):
    frustum(p, "PaleAlloy", 8, 1.2 * k, 3.4 * k, z - 7 * k, z - 3 * k, x, y, rot=rz)
    frustum(p, "AzureDim", 8, 3.0 * k, 3.0 * k, z - 3 * k, z + 3 * k, x, y, rot=rz)
    frustum(p, "PaleAlloy", 8, 3.4 * k, 1.2 * k, z + 3 * k, z + 7 * k, x, y, rot=rz)
    crystal(p, "SunGold", x, y, z + 8.2 * k, 0.8 * k, 1.8 * k, 1.2 * k)
    crystal(p, "DeepAlloy", x, y, z - 8.2 * k, 0.8 * k, 1.2 * k, 2.4 * k)
    return 3.5 * k, z - 10.6 * k, z + 10 * k


BEACON_STYLES = (_beacon_post, _beacon_shard, _beacon_lantern)


def corner_beacons(p):
    """Four floating beacons, one per corner, each placed differently.

    Owner-directed 2026-09-22: where four tiles meet, identical flush beacons
    fused into one block. Each beacon now picks its own style, size, height,
    turn and inset from the corner -- seeded from the piece's name, so a
    rebuild is identical -- and is placed only where validate() will accept it:
    at least FLOAT_EDGE_MARGIN inside the tile (so it can never touch a
    neighbour's), clear of every other float, solid and deck. A corner with no
    legal spot after 60 tries goes without; nothing depends on the beacons any
    more -- edge_pins() pins the bounding box instead."""
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        for _ in range(60):
            style = p.rng.choice(BEACON_STYLES)
            k = p.rng.uniform(0.75, 1.3)
            ix, iy = p.rng.uniform(12, 36), p.rng.uniform(12, 36)
            x, y = sx * (HALF - ix), sy * (HALF - iy)
            z = p.rng.uniform(-18, 26)
            rz = p.rng.uniform(0, 90)
            # measure the style without building it, then test the spot
            probe = Piece("_probe", "")
            r, z0, z1 = style(probe, x, y, z, k, rz)
            shape = ("cyl", x, y, r, z0, z1)
            if free_for_float(p, shape):
                style(p, x, y, z, k, rz)
                p.floats.append(("corner beacon", shape))
                break


def edge_pins(p):
    """Four 0.3-stud pins at the midpoint of each tile edge, at the keel line
    (z = -96). They are what holds every piece's bounding box to exactly
    256 x 256, centred on the origin -- which matters twice over: ChunkLoader
    stretches a mesh to SizeX/Z, and a Roblox MeshPart pivots on its bounding
    box centre, so a lopsided box moves the piece. Each pin lies wholly on its
    own side of the edge, so two neighbours' pins touch face to face and never
    interpenetrate. 96 studs under the deck and a third of a stud across, they
    are invisible in play."""
    t = 0.3
    z0 = KEEL_BOTTOM
    box_span(p, "HullSlate", HALF - t, HALF, -t / 2, t / 2, z0, z0 + t)
    box_span(p, "HullSlate", -HALF, -HALF + t, -t / 2, t / 2, z0, z0 + t)
    box_span(p, "HullSlate", -t / 2, t / 2, HALF - t, HALF, z0, z0 + t)
    box_span(p, "HullSlate", -t / 2, t / 2, -HALF, -HALF + t, z0, z0 + t)


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
    float_crystal(p, "SkyGlass", -34, 50, 20, 2.4, 5, 4, n=6)
    float_crystal(p, "SkyGlass", 34, 50, 26, 2.0, 4, 3.5, n=6)
    finish(p)
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
    p.solid_box("gatehouse lintel", -30, 30, -4, 4, 28, 48)
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
    finish(p)
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
    p.solid("fountain", 0, 0, 16, 0, 24)
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
    float_crystal(p, "SkyGlass", -66, 58, 30, 2.8, 6, 4.5, n=6)
    float_crystal(p, "SkyGlass", 66, 58, 24, 2.4, 5, 4, n=6)
    finish(p)
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
        float_crystal(p, "SkyGlass", math.cos(a) * 30, 70 + math.sin(a) * 30, 52, 3.2, 7, 5, n=6)

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
        float_crystal(p, "SkyGlass", math.cos(a) * 72, math.sin(a) * 72, 36, 5, 12, 10, n=6)
    finish(p)
    return p


# --------------------------------------------------------------------------
# Kit expansion props (2026-09-22). Same hand as the set pieces above.
# --------------------------------------------------------------------------


@contextmanager
def frame(p, M):
    """Build in a local frame: everything inside lands transformed by M."""
    saved = p.base
    p.base = saved @ M
    try:
        yield
    finally:
        p.base = saved


def torus_arc(p, mat, R, r, cx, cy, cz, a0, a1, n=16, m=4, rx=0.0, ry=0.0, rz=0.0):
    """Part of a ring, a0..a1 degrees in its own plane, ends capped."""
    verts, faces = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        for j in range(m):
            b = 2 * math.pi * j / m + math.pi / m
            d = R + r * math.cos(b)
            verts.append((d * math.cos(a), d * math.sin(a), r * math.sin(b)))
    for i in range(n):
        for j in range(m):
            j2 = (j + 1) % m
            faces.append((i * m + j, (i + 1) * m + j, (i + 1) * m + j2, i * m + j2))
    faces.append(tuple(range(m)))
    faces.append(tuple(reversed(range(n * m, n * m + m))))
    p.add(verts, faces, mat, xf(cx, cy, cz, rz, rx, ry))


def orb(p, mat, x, y, z, r, n=8):
    """A low-poly ball: three frustums. Topiary, planets, lamp globes."""
    frustum(p, mat, n, r * 0.5, r, z - r, z - r * 0.35, x, y)
    frustum(p, mat, n, r, r, z - r * 0.35, z + r * 0.35, x, y)
    frustum(p, mat, n, r, r * 0.5, z + r * 0.35, z + r, x, y)


def parapet_open(p, pts, openings):
    """parapet_ring, but leaving gaps for deck mouths. openings: list of
    (side, width), side in 'NSEW'. An edge that lies on the piece's extreme
    in that direction is split round the mouth."""
    n = len(pts)
    ymax = max(q[1] for q in pts)
    ymin = min(q[1] for q in pts)
    xmax = max(q[0] for q in pts)
    xmin = min(q[0] for q in pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        inward = (-ey / L, ex / L)
        segs = [(a, b)]
        for side, w in openings:
            hw = w / 2
            if side in "NS":
                yline = ymax if side == "N" else ymin
                if abs(a[1] - yline) < 1e-3 and abs(b[1] - yline) < 1e-3:
                    lo, hi = sorted((a[0], b[0]))
                    parts = [(lo, -hw), (hw, hi)]
                    segs = [((x0, yline), (x1, yline)) for x0, x1 in parts if x1 - x0 > 2]
            else:
                xline = xmax if side == "E" else xmin
                if abs(a[0] - xline) < 1e-3 and abs(b[0] - xline) < 1e-3:
                    lo, hi = sorted((a[1], b[1]))
                    parts = [(lo, -hw), (hw, hi)]
                    segs = [((xline, y0), (xline, y1)) for y0, y1 in parts if y1 - y0 > 2]
        for s0, s1 in segs:
            # keep the original edge direction so "inward" stays inward
            if (s1[0] - s0[0]) * ex + (s1[1] - s0[1]) * ey < 0:
                s0, s1 = s1, s0
            parapet(p, s0, s1, inward)


def skiff(p, x, y, z, rz=0.0):
    """A moored sky-skiff: white hull, violet sails, azure drive. Floats."""
    p.float_("skiff", x, y, 16.5, z - 4.5, z + 13)
    with frame(p, xf(x, y, z, rz)):
        hull = xf(ry=90)
        frustum(p, "CitadelWhite", 6, 3.4, 3.4, -8, 8, M=hull)
        frustum(p, "CitadelWhite", 6, 3.4, 0, 8, 15, M=hull)
        frustum(p, "PaleAlloy", 6, 3.4, 2.0, -8, -12, M=hull)
        frustum(p, "AzureNeon", 6, 1.8, 1.8, -12, -13, M=hull)
        box(p, "PaleAlloy", 0, 0, 3.3, 20, 4.2, 0.6)
        box(p, "SunGold", 14, 0, 0, 2.0, 0.6, 0.6)
        frustum(p, "DeepAlloy", 6, 0.35, 0.3, 3.3, 12.5, 2, 0)
        box(p, "CitadelViolet", 2, 0, 8.4, 7.5, 0.3, 6.5)
        box(p, "CitadelViolet", -6, 0, 6.2, 4.5, 0.3, 4.0)
        for sy in (-1, 1):
            box(p, "DeepAlloy", -4, sy * 4.4, 0.6, 6, 2.4, 0.5, rx=sy * 20)
            box(p, "AzureDim", -4, sy * 5.5, 0.2, 5, 0.4, 0.4)


def crane(p, x, y, rz=0.0, h=22.0):
    p.solid("crane", x, y, 3.0, 0, h + 3)
    frustum(p, "DeepAlloy", 4, 2.2, 1.8, 0, 1.2, x, y, rot=45)
    frustum(p, "PaleAlloy", 4, 1.2, 0.9, 1.2, h, x, y, rot=45)
    with frame(p, xf(x, y, 0, rz)):
        box(p, "PaleAlloy", 6, 0, h + 0.8, 18, 1.2, 1.2)
        box(p, "DeepAlloy", -3.5, 0, h + 0.8, 3, 2.2, 2.2)
        box(p, "SunGold", 0, 0, h + 1.9, 1.6, 1.6, 1.0)
        box(p, "DeepAlloy", 13.5, 0, h - 5, 0.2, 0.2, 11)
        crate(p, 13.5, 0, 2.6, z=h - 13)


def hoop(p, y, R=34.0, zc=6.0):
    """A great floating ring the skyway passes through."""
    p.float_box("hoop", -R - 2, R + 2, y - 2, y + 2, zc - R - 2, zc + R + 2)
    torus(p, "PaleAlloy", R, 1.6, 0, y, zc, n=28, rx=90)
    torus(p, "AzureNeon", R - 2.2, 0.35, 0, y, zc, n=28, rx=90)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        crystal(p, "SunGold", math.cos(a) * (R + 1.2), y, zc + math.sin(a) * (R + 1.2), 1.2, 2.2, 2.2)


def dome(p, x, y, R, drum_h=8.0):
    """Observatory dome on a drum, with a glowing slit."""
    p.solid("dome", x, y, R + 1.5, 0, drum_h + R + 1)
    frustum(p, "PaleAlloy", 12, R + 1.2, R + 1.0, 0, 1.5, x, y)
    frustum(p, "CitadelWhite", 12, R + 0.6, R + 0.6, 1.5, drum_h, x, y)
    frustum(p, "AzureDim", 12, R + 0.8, R + 0.8, drum_h - 1.2, drum_h - 0.4, x, y)
    steps = [0, 22.5, 45, 67.5, 90]
    for a0, a1 in zip(steps, steps[1:]):
        r0 = R * math.cos(math.radians(a0))
        r1 = R * math.cos(math.radians(a1))
        z0 = drum_h + R * math.sin(math.radians(a0))
        z1 = drum_h + R * math.sin(math.radians(a1))
        frustum(p, "CitadelWhite", 12, r0, max(r1, 0.0), z0, z1, x, y)
    for a in (-8, 8):
        with frame(p, xf(x, y, drum_h, a + 30)):
            torus_arc(p, "AzureDim", R + 0.1, 0.35, 0, 0, 0, 5, 85, n=6, rx=90)
    return drum_h + R


def telescope(p, x, y, z, rz, elev=40.0):
    with frame(p, xf(x, y, z, rz)):
        M = xf(rx=-(90 - elev))
        frustum(p, "DeepAlloy", 8, 2.4, 2.0, 0, 6, M=M)
        frustum(p, "PaleAlloy", 8, 2.0, 1.5, 6, 20, M=M)
        frustum(p, "SunGold", 8, 1.7, 1.7, 20, 21, M=M)
        frustum(p, "SkyGlass", 8, 1.4, 1.4, 21, 21.3, M=M)


def dish(p, x, y, h, rz=0.0, tilt=35.0, R=7.0):
    p.solid("dish", x, y, R + 0.5, 0, h + R + 2)
    frustum(p, "DeepAlloy", 6, 1.4, 1.0, 0, 1.2, x, y)
    frustum(p, "PaleAlloy", 6, 0.7, 0.5, 1.2, h, x, y)
    with frame(p, xf(x, y, h, rz, rx=tilt)):
        frustum(p, "CitadelWhite", 10, 0.8, R, 0, 2.6)
        frustum(p, "AzureDim", 10, R, R, 2.6, 2.9)
        frustum(p, "DeepAlloy", 4, 0.3, 0.2, 0.5, 6)
        crystal(p, "AzureNeon", 0, 0, 6.6, 0.5, 0.8, 0.6)


def orrery(p, x, y):
    """An orrery of halos -- the observatory's centrepiece."""
    p.solid("orrery", x, y, 12.0, 0, 17)
    frustum(p, "DeepAlloy", 8, 5, 4, 0, 1.6, x, y)
    frustum(p, "PaleAlloy", 8, 0.7, 0.5, 1.6, 9.6, x, y)
    orb(p, "SunGold", x, y, 11.8, 2.2)
    rings = ((7.0, 14, 0, "SkyGlass", 30), (10.5, -9, 22, "CitadelViolet", 200))
    for R, rx, ry, pmat, t in rings:
        torus(p, "AzureNeon", R, 0.2, x, y, 11.8, n=20, rx=rx, ry=ry)
        v = Euler((math.radians(rx), math.radians(ry), 0), "XYZ").to_matrix() @ Vector(
            (R * math.cos(math.radians(t)), R * math.sin(math.radians(t)), 0))
        orb(p, pmat, x + v.x, y + v.y, 11.8 + v.z, 1.1, n=6)


def weapon_rack(p, x, y, rz=0.0):
    p.solid("weapon rack", x, y, 3.4, 0, 4.5)
    with frame(p, xf(x, y, 0, rz)):
        for sx in (-2.6, 2.6):
            box(p, "DeepAlloy", sx, 0, 1.7, 0.4, 0.8, 3.4)
        box(p, "PaleAlloy", 0, 0, 3.3, 5.8, 0.9, 0.35)
        box(p, "PaleAlloy", 0, 0, 0.9, 5.8, 0.9, 0.3)
        for k, bx in enumerate((-1.8, -0.6, 0.6, 1.8)):
            blade = "SkyGlass" if k % 2 == 0 else "PaleAlloy"
            box(p, blade, bx, 0.25, 2.3, 0.35, 0.12, 3.6, rx=8)
            box(p, "SunGold", bx, 0.35, 0.7, 0.9, 0.25, 0.25)


def shield_rack(p, x, y, rz=0.0):
    p.solid("shield rack", x, y, 3.4, 0, 4.2)
    with frame(p, xf(x, y, 0, rz)):
        box(p, "DeepAlloy", 0, 0, 1.6, 6.0, 0.5, 0.4)
        for sx in (-2.6, 2.6):
            box(p, "DeepAlloy", sx, 0, 1.0, 0.4, 0.8, 2.0)
        for bx in (-1.8, 0, 1.8):
            frustum(p, "CitadelViolet", 6, 1.05, 1.05, 0.3, 0.55, M=xf(bx, 0, 2.2, rx=90))
            crystal(p, "SunGold", bx, 0.75, 2.2, 0.35, 0.3, 0.3)


def target(p, x, y, rz=0.0):
    p.solid("target", x, y, 2.2, 0, 6.2)
    frustum(p, "DeepAlloy", 6, 0.9, 0.7, 0, 0.5, x, y)
    frustum(p, "DeepAlloy", 6, 0.25, 0.25, 0.5, 3.4, x, y)
    with frame(p, xf(x, y, 4.6, rz)):
        torus(p, "PaleAlloy", 1.6, 0.25, 0, 0, 0, n=12, rx=90)
        frustum(p, "AzureDim", 12, 1.3, 1.3, -0.1, 0.1, M=xf(rx=90))
        frustum(p, "AzureNeon", 8, 0.45, 0.45, -0.2, 0.2, M=xf(rx=90))


def forge(p, x, y, rz=0.0):
    p.solid("forge", x, y, 6.5, 0, 22)
    with frame(p, xf(x, y, 0, rz)):
        box(p, "DeepAlloy", 0, 0, 2.5, 9, 7, 5)
        box(p, "PaleAlloy", 0, 0, 5.2, 9.6, 7.6, 0.4)
        box(p, "AzureNeon", 0, -3.55, 2.0, 4.0, 0.2, 2.2)
        frustum(p, "HullSlate", 6, 1.8, 1.3, 5.4, 20, 2.2, 1.5)
        frustum(p, "AzureDim", 6, 1.45, 1.45, 17, 18, 2.2, 1.5)
        box(p, "DeepAlloy", -1.5, -7.0, 0.9, 3.2, 1.4, 1.8)     # anvil
        box(p, "PaleAlloy", -1.5, -7.0, 2.0, 4.0, 1.6, 0.5)


def barracks(p, x, y, lx=40.0, ly=14.0, h=9.0, rz=0.0):
    """A long hall under a violet pitched roof."""
    with frame(p, xf(x, y, 0, rz)):
        p.solid_box("barracks", -lx / 2 - 1, lx / 2 + 1, -ly / 2 - 1, ly / 2 + 1, 0, h + ly * 0.5 + 1)
        box(p, "PaleAlloy", 0, 0, 0.6, lx + 1.5, ly + 1.5, 1.2)
        box(p, "CitadelWhite", 0, 0, 1.2 + (h - 1.2) / 2, lx, ly, h - 1.2)
        hw, rh = ly / 2 + 0.8, ly * 0.45
        v = [(-lx / 2 - 0.8, -hw, h), (lx / 2 + 0.8, -hw, h), (lx / 2 + 0.8, hw, h), (-lx / 2 - 0.8, hw, h),
             (-lx / 2 - 0.8, 0, h + rh), (lx / 2 + 0.8, 0, h + rh)]
        p.add(v, [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)], "CitadelViolet",
              Matrix.Identity(4))
        n = int(lx // 7)
        for i in range(n):
            wx = -lx / 2 + (i + 0.5) * lx / n
            for sy in (-1, 1):
                box(p, "AzureDim", wx, sy * (ly / 2 + 0.05), h * 0.55, 1.2, 0.3, 3.2)
        box(p, "DeepAlloy", lx / 2 + 0.1, 0, 2.8, 0.4, 3.2, 4.4)
        box(p, "SunGold", lx / 2 + 0.3, 0, 5.4, 0.3, 3.6, 0.4)


def hedge(p, x0, y0, x1, y1, h=2.4, t=1.4):
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box(p, "PaleAlloy", mx, my, 0.3, L + 0.4, t + 0.4, 0.6, rz=ang)
    box(p, "Verdure", mx, my, 0.6 + (h - 0.6) / 2, L, t, h - 0.6, rz=ang)


def topiary_orb(p, x, y, r=2.2):
    p.solid("topiary", x, y, r + 1.2, 0, 4 + 2 * r)
    box(p, "DeepAlloy", x, y, 0.7, 3.2, 3.2, 1.4)
    frustum(p, "DeepAlloy", 6, 0.3, 0.3, 1.4, 3.0, x, y)
    orb(p, "Verdure", x, y, 3.0 + r, r)


def pool(p, x, y, lx, ly):
    """A reflecting pool: alloy rim, glass water, flush with the deck."""
    p.solid_box("pool", x - lx / 2 - 1, x + lx / 2 + 1, y - ly / 2 - 1, y + ly / 2 + 1, 0, 1)
    t = 1.2
    box_span(p, "DeepAlloy", x - lx / 2 - t, x + lx / 2 + t, y + ly / 2, y + ly / 2 + t, 0, 0.8)
    box_span(p, "DeepAlloy", x - lx / 2 - t, x + lx / 2 + t, y - ly / 2 - t, y - ly / 2, 0, 0.8)
    box_span(p, "DeepAlloy", x - lx / 2 - t, x - lx / 2, y - ly / 2, y + ly / 2, 0, 0.8)
    box_span(p, "DeepAlloy", x + lx / 2, x + lx / 2 + t, y - ly / 2, y + ly / 2, 0, 0.8)
    box_span(p, "SkyGlass", x - lx / 2, x + lx / 2, y - ly / 2, y + ly / 2, 0, 0.4)


def pergola(p, x, y0, y1, width=12.0, h=8.0, step=10.0):
    """A colonnaded walk with a slatted roof and trailing green."""
    p.solid_box("pergola", x - width / 2 - 1, x + width / 2 + 1, y0 - 1, y1 + 1, 0, h + 1.5)
    n = max(1, int((y1 - y0) // step))
    for i in range(n + 1):
        yy = y0 + (y1 - y0) * i / n
        for sx in (-1, 1):
            frustum(p, "CitadelWhite", 6, 0.6, 0.5, 0, h, x + sx * width / 2, yy)
        box(p, "PaleAlloy", x, yy, h + 0.4, width + 1.6, 0.6, 0.6)
    for sx in (-1, 1):
        box_span(p, "PaleAlloy", x + sx * width / 2 - 0.4, x + sx * width / 2 + 0.4, y0, y1, h + 0.8, h + 1.4)
    box_span(p, "Verdure", x - width / 2 + 0.6, x - width / 2 + 2.4, y0, y1, h + 0.8, h + 1.2)


def gazebo(p, x, y, r=10.0, h=8.0):
    p.solid("gazebo", x, y, r + 1.5, 0, h + r + 3)
    frustum(p, "PaleAlloy", 8, r + 1, r + 0.6, 0, 0.8, x, y)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        frustum(p, "CitadelWhite", 6, 0.55, 0.5, 0.8, h, x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9)
    frustum(p, "PaleAlloy", 8, r * 1.05, r * 1.1, h, h + 1, x, y)
    frustum(p, "CitadelViolet", 8, r * 1.1, 0, h + 1, h + 1 + r * 0.9, x, y)
    crystal(p, "SunGold", x, y, h + 1 + r * 0.9 + 1.0, 0.7, 1.6, 1.0)


def flower_bed(p, x, y, lx=8.0, ly=3.0, seed=0):
    box(p, "DeepAlloy", x, y, 0.5, lx, ly, 1.0)
    box(p, "Verdure", x, y, 1.1, lx - 0.6, ly - 0.6, 0.3)
    rng = random.Random(seed)
    for i in range(int(lx)):
        mat = rng.choice(("SunGold", "CitadelViolet", "SkyGlass"))
        crystal(p, mat, x - lx / 2 + 0.6 + i * (lx - 1.2) / max(1, int(lx) - 1),
                y + rng.uniform(-ly / 4, ly / 4), 1.6, 0.35, 0.5, 0.3)


def vault_door(p, x, y, z, R=8.0):
    """A round vault door set into a south-facing (-Y) wall at y."""
    frustum(p, "DeepAlloy", 12, R, R, 0, 1.2, M=xf(x, y, z, rx=90))
    frustum(p, "PaleAlloy", 12, R * 0.7, R * 0.7, 1.2, 1.6, M=xf(x, y, z, rx=90))
    torus(p, "SunGold", R + 0.3, 0.55, x, y - 1.2, z, n=16, rx=90)
    for k in range(4):
        box(p, "AzureNeon", x, y - 1.7, z, R * 1.1, 0.2, 0.4, ry=45 * k)
    crystal(p, "SunGold", x, y - 2.0, z, 0.9, 0.9, 0.9)


def chest(p, x, y, rz=0.0):
    with frame(p, xf(x, y, 0, rz)):
        box(p, "DeepAlloy", 0, 0, 0.8, 3.2, 2.0, 1.6)
        box(p, "SunGold", 0, 0, 1.85, 3.4, 2.2, 0.5)
        box(p, "AzureNeon", 0, -1.05, 1.3, 0.6, 0.15, 0.6)


def crystal_cluster(p, x, y, seed, scale=1.0):
    """Crystals growing out of the deck -- half-sunk on purpose."""
    rng = random.Random(seed)
    p.solid("crystal cluster", x, y, 3.5 * scale, 0, 9 * scale)
    for i in range(5):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1.8) * scale
        mat = "SkyGlass" if i % 3 else "CitadelViolet"
        crystal(p, mat, x + math.cos(a) * d, y + math.sin(a) * d, 0.2,
                rng.uniform(0.6, 1.2) * scale, rng.uniform(3, 8) * scale, 1.0, n=5,
                rz=rng.uniform(0, 72))


def turbine(p, x, y, hub, blade, rz=0.0, needle_to=None):
    """A wind turbine: white mast, three alloy blades facing along local Y."""
    top = needle_to if needle_to else hub + blade + 1
    p.solid("turbine", x, y, blade + 1.5, 0, top)
    frustum(p, "PaleAlloy", 8, 3.2, 2.9, 0, 2, x, y)
    frustum(p, "CitadelWhite", 8, 2.2, 1.3, 2, hub, x, y)
    frustum(p, "AzureDim", 8, 1.9, 1.9, hub * 0.45, hub * 0.45 + 1.5, x, y)
    with frame(p, xf(x, y, hub, rz)):
        box(p, "PaleAlloy", 0, 0.5, 0, 2.6, 6, 2.6)
        frustum(p, "SunGold", 8, 1.3, 0, 3.5, 5.5, M=xf(rx=-90))
        for k in range(3):
            a = 90 + 120 * k
            with frame(p, xf(0, -2.2, 0, 0, 0, -a)):
                box(p, "CitadelWhite", blade / 2 + 1.2, 0, 0, blade, 0.35, 2.0, rx=12)
                box(p, "AzureDim", blade + 0.9, 0, 0, 1.2, 0.4, 2.1)
    if needle_to:
        frustum(p, "PaleAlloy", 6, 0.6, 0, hub + 1.3, needle_to, x, y + 0.5)


def colonnade(p, x, y0, y1, n, H=28.0):
    p.solid_box("colonnade", x - 4, x + 4, y0 - 4, y1 + 4, 0, H + 4)
    for i in range(n):
        yy = y0 + (y1 - y0) * i / (n - 1)
        frustum(p, "PaleAlloy", 8, 3.0, 2.8, 0, 2, x, yy)
        frustum(p, "CitadelWhite", 8, 2.2, 1.8, 2, H, x, yy)
        frustum(p, "AzureDim", 8, 2.1, 2.1, H * 0.6, H * 0.6 + 1, x, yy)
        frustum(p, "PaleAlloy", 8, 1.9, 3.0, H, H + 1.5, x, yy)
    box_span(p, "CitadelWhite", x - 3, x + 3, y0 - 3, y1 + 3, H + 1.5, H + 3.5)
    box_span(p, "AzureDim", x - 3.1, x + 3.1, y0 - 3.1, y1 + 3.1, H + 2.2, H + 2.6)


def container(p, x, y, rz=0.0, mat="PaleAlloy"):
    with frame(p, xf(x, y, 0, rz)):
        box(p, mat, 0, 0, 1.6, 7, 3.2, 3.2)
        for dx in (-3.2, 0, 3.2):
            box(p, "DeepAlloy", dx, 0, 1.6, 0.35, 3.4, 3.4)


def skyway_deck_x(p, x0, x1, rail_from, rail_to):
    """A SKYWAY running along X (an east or west opening)."""
    with oriented(p, -90):
        skyway_deck(p, x0, x1, rail_from, rail_to)


def chamfer_rect(hx, hy, c):
    return [(-hx + c, -hy), (hx - c, -hy), (hx, -hy + c), (hx, hy - c),
            (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c)]


# --------------------------------------------------------------------------
# The eight new pieces (kit expansion, 2026-09-22)
# --------------------------------------------------------------------------


def build_path_bend():
    p = Piece("chunk_path_bend", "PATH | openings: south SKYWAY, east SKYWAY -- the quarter turn")
    R = 58.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck_x(p, apo, HALF, apo + 1, HALF - 0.4)
    parapet_open(p, pts, [("S", SKYWAY_W), ("E", SKYWAY_W)])
    torus(p, "AzureDim", 40, 0.3, 0, 0, 0.05, n=24)

    # the Spired Keep -- the corner the skyway turns round; pins +160
    tower(p, 0, 0, 13, 56, roof=False)
    spire(p, 0, 0, 5.5, CROWN_TOP, fins=False, z0=59)
    for k in range(4):
        a = math.radians(135 + 90 * k)
        banner(p, math.cos(a) * 20, math.sin(a) * 20, rz=math.degrees(a) + 90)

    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        if -1 < math.cos(a) * 44 and math.cos(a) > 0.5 and math.sin(a) < 0.5 and math.sin(a) > -0.5:
            continue
        lamp(p, math.cos(a) * 44, math.sin(a) * 44)
    holo_pedestal(p, -36, -28)
    planter(p, -30, 36)
    planter(p, 30, 36)
    bench(p, -40, 10, rz=90)
    crate(p, 34, -36, 3.0, rz=15)
    crate(p, 37, -33, 2.6, rz=-10)
    crate(p, 35, -35, 2.4, z=3.0, rz=40)
    anti_grav_pylon(p, -86, 72, 4)
    float_crystal(p, "SkyGlass", -64, -60, 18, 2.6, 6, 4.5)
    float_crystal(p, "SkyGlass", 70, 66, 24, 2.2, 5, 4)
    finish(p)
    return p


def build_path_skyport():
    p = Piece("chunk_path_skyport", "PATH | openings: north SKYWAY, south SKYWAY -- a skiff dock")
    pts = [(-20, -60), (60, -60), (84, -36), (84, 36), (60, 60), (-20, 60)]
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    keel(p, pts, [
        (-DECK_T + 0.5, 0.98, 0, "HullSlate"), (-14, 0.9, 3, "HullSlate"), (-17, 0.91, 3, "DeepAlloy"),
        (-44, 0.6, -5, "HullSlate"), (-48, 0.61, -5, "AzureDim"), (-72, 0.25, 4, "DeepAlloy"),
        (KEEL_BOTTOM, 0.0, 0, "DeepAlloy")], centre=(28, 0))
    border_band(p, pts)
    skyway_deck(p, -HALF, -60, -HALF + 0.4, -61)
    skyway_deck(p, 60, HALF, 61, HALF - 0.4)
    railing(p, -19.4, -60, -19.4, 60)
    # parapets on the chamfers and the dock's flanks; a gap on the east edge for the gangway
    parapet(p, (20, -60), (60, -60), (0, 1))
    parapet(p, (60, -60), (84, -36), (-0.707, 0.707))
    parapet(p, (84, -36), (84, -8), (-1, 0))
    parapet(p, (84, 8), (84, 36), (-1, 0))
    parapet(p, (84, 36), (60, 60), (-0.707, -0.707))
    parapet(p, (60, 60), (20, 60), (0, -1))
    box_span(p, "AzureDim", -1.5, 1.5, -60, 60, 0, 0.12)

    # landing pad, gangway, the moored skiff
    frustum(p, "PaleAlloy", 12, 20, 19, 0, 0.4, 46, 0)
    torus(p, "AzureNeon", 17, 0.3, 46, 0, 0.45, n=24)
    for dx in (-5, 5):
        box(p, "AzureDim", 46 + dx, 0, 0.45, 1.4, 12, 0.15)
    box(p, "AzureDim", 46, 0, 0.45, 10, 1.4, 0.15)
    box_span(p, "PaleAlloy", 84, 99, -3, 3, -0.6, -0.1)
    for sy in (-1, 1):
        box_span(p, "DeepAlloy", 84, 99, sy * 3 - 0.2, sy * 3 + 0.2, -0.1, 1.2)
    skiff(p, 104, 2, -2.2, rz=90)

    crane(p, 70, -40, rz=20)
    for (x, y, r) in ((30, -44, 0), (30, -36, 6), (40, 44, 90), (32, 46, 84)):
        container(p, x, y, rz=r, mat="PaleAlloy" if r < 45 else "HullSlate")
    crate(p, 44, -44, 3.0, rz=14)
    crate(p, 44, -44, 2.6, z=3.0, rz=-4)
    # control tower with an antenna spire -- pins +160
    tower(p, 64, 38, 7, 34, roof=False)
    spire(p, 64, 38, 3.2, CROWN_TOP, fins=False, halo=True, z0=37)
    for y in (-40, 0, 40):
        lamp(p, -16, y)
    anti_grav_pylon(p, -70, -40, 6)
    float_crystal(p, "SkyGlass", -64, 52, 22, 2.4, 5.5, 4)
    finish(p)
    return p


def build_path_hoops():
    p = Piece("chunk_path_hoops", "PATH | openings: north SKYWAY, south SKYWAY -- a bare span through three rings")
    skyway_deck(p, -HALF, HALF, -HALF + 0.4, HALF - 0.4)
    # a plumb-bob keel under the span's midpoint
    frustum(p, "HullSlate", 8, 9, 7, -DECK_T + 0.5, -20, 0, 0)
    frustum(p, "AzureDim", 8, 7.2, 7.2, -20, -23, 0, 0)
    frustum(p, "DeepAlloy", 8, 7, 0, -23, -64, 0, 0)
    for y in (-78, 0, 78):
        hoop(p, y)
    for y in (-40, 40):
        lamp(p, 17, y)
        lamp(p, -17, y)

    # two satellite islands the span passes between; the west one pins +160
    for (cx, cy, R, rot) in ((-74, 34, 22, 0), (72, -44, 17, 30)):
        spts = [(cx + x, cy + y) for x, y in ngon(6, R, rot=rot)]
        slab(p, "CitadelWhite", spts, -DECK_T, 0)
        keel(p, spts, [(-DECK_T + 0.5, 0.97, 0, "HullSlate"), (-10, 0.85, 5, "HullSlate"),
                       (-12, 0.86, 5, "AzureDim"), (-30, 0.45, -4, "HullSlate"),
                       (-56, 0.0, 0, "DeepAlloy")], centre=(cx, cy))
        parapet_ring(p, spts)
    spire(p, -74, 34, 6, CROWN_TOP, extra_halos=1)
    obelisk(p, 72, -44, h=18)
    banner(p, 66, -38)
    crystal_cluster(p, 78, -50, seed=7)
    anti_grav_pylon(p, 64, 72, 10)
    anti_grav_pylon(p, -66, -70, 2)
    finish(p)
    return p


def build_garden_terrace():
    p = Piece("chunk_garden_terrace", "COMBAT | openings: north SKYWAY, south SKYWAY -- gardens")
    pts = chamfer_rect(92, 96, 26)
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts, width=7)
    skyway_deck(p, -HALF, -96, -HALF + 0.4, -97)
    skyway_deck(p, 96, HALF, 97, HALF - 0.4)
    parapet_open(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)])

    # hedged avenue, broken by a cross walk
    for sx in (-1, 1):
        for y0, y1 in ((-90, -12), (12, 90)):
            hedge(p, sx * 22, y0, sx * 22, y1)
    box_span(p, "PaleAlloy", -88, 88, -5, 5, 0, 0.1)
    # west: a long reflecting pool under a pergola walk
    pool(p, -52, 36, 22, 40)
    pergola(p, -76, -60, 64)
    for y in (-32, -52):
        topiary_orb(p, -52, y)
    float_crystal(p, "SkyGlass", -52, 36, 16, 2.6, 5.5, 4.5)
    # east: a gazebo in a ring of flower beds, orbs, benches
    gazebo(p, 56, 44)
    for k, a in enumerate((200, 250, 290, 340)):
        r = math.radians(a)
        flower_bed(p, 56 + math.cos(r) * 22, 44 + math.sin(r) * 22, seed=k)
    for y in (-26, -44, -62):
        topiary_orb(p, 36, y, r=2.0)
    bench(p, 34, 12, rz=0)
    bench(p, -34, -12, rz=0)
    # the Sun Spire -- pins +160
    spire(p, 64, -58, 6, CROWN_TOP, extra_halos=1)
    for y in (-70, -40, 40, 70):
        lamp(p, -17, y)
        lamp(p, 17, y)
    float_crystal(p, "SkyGlass", 64, 4, 26, 2.2, 5, 4)
    finish(p)
    return p


def build_observatory():
    p = Piece("chunk_observatory", "COMBAT | openings: north SKYWAY, south SKYWAY -- stargazers' deck")
    R = 84.0
    pts = ngon(12, R)
    apo = R * math.cos(math.radians(15))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    parapet_open(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)])

    # star-map floor: a ring and constellations of inlaid points
    torus(p, "AzureDim", 34, 0.3, 0, -4, 0.05, n=28)
    rng = random.Random("observatory stars")
    for _ in range(26):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(16, 32)
        box(p, "AzureNeon", math.cos(a) * d, -4 + math.sin(a) * d, 0.05, 0.9, 0.9, 0.2, rz=45)
    orrery(p, 0, -4)

    # the great dome and its mast -- pins +160
    top = dome(p, -44, 30, 18)
    telescope(p, -44, 30, 16, rz=-30, elev=38)
    spire(p, -44, 30, 2.6, CROWN_TOP, fins=False, halo=True, z0=top - 0.5)
    # the dish array
    dish(p, 50, 40, 12, rz=200, tilt=38)
    dish(p, 60, 2, 16, rz=160, tilt=30, R=8)
    dish(p, 46, -38, 10, rz=230, tilt=42, R=6)
    for x, y in ((-30, -50), (-50, -24)):
        holo_pedestal(p, x, y)
    bench(p, -26, -30, rz=60)
    crate(p, 30, -62, 2.8, rz=10)
    crate(p, 33, -60, 2.4, rz=-18)
    for y in (-60, -30, 30, 60):
        lamp(p, 17, y)
    float_crystal(p, "SkyGlass", 64, 58, 30, 2.2, 5, 4)
    float_crystal(p, "SkyGlass", -66, -60, 22, 2.6, 6, 4.5)
    finish(p)
    return p


def build_armory():
    p = Piece("chunk_armory", "COMBAT | openings: north SKYWAY, south SKYWAY -- a training yard")
    pts = chamfer_rect(90, 90, 20)
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts)
    skyway_deck(p, -HALF, -90, -HALF + 0.4, -91)
    skyway_deck(p, 90, HALF, 91, HALF - 0.4)
    parapet_open(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)])

    # the sparring ring
    torus(p, "AzureDim", 22, 0.35, -48, 14, 0.05, n=24)
    torus(p, "AzureDim", 8, 0.3, -48, 14, 0.05, n=12)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        frustum(p, "PaleAlloy", 6, 0.6, 0.5, 0, 3.4, -48 + math.cos(a) * 24, 14 + math.sin(a) * 24)
        crystal(p, "AzureNeon", -48 + math.cos(a) * 24, 14 + math.sin(a) * 24, 3.9, 0.45, 0.6, 0.5)
    # the target line and the racks along the avenue
    for y in (-60, -46, -32):
        target(p, -76, y, rz=90)
    for y in (-66, -30, 30, 66):
        weapon_rack(p, -30, y, rz=90)
    for y in (-50, 50):
        shield_rack(p, 30, y, rz=90)
    # barracks, forge, watch turret, and the spire -- pins +160
    barracks(p, 62, 38, lx=40, ly=16, rz=90)
    forge(p, 58, -32)
    tower(p, -70, -70, 8, 38)
    spire(p, -68, 66, 6, CROWN_TOP, extra_halos=1)
    banner(p, -26, 14)
    banner(p, 40, 0)
    for x, y in ((74, -62), (78, -58), (70, -58)):
        crate(p, x, y, 3.0, rz=x)
    crate(p, 74, -60, 2.8, z=3.0, rz=33)
    container(p, 38, -64, rz=10)
    for y in (-66, -20, 20, 66):
        lamp(p, 17, y)
    float_crystal(p, "SkyGlass", -46, 14, 24, 2.4, 5.5, 4.5)
    finish(p)
    return p


def build_side_vault():
    p = Piece("chunk_side_vault", "SIDE | one opening: south SKYWAY -- a sealed treasury")
    R = 66.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    parapet_open(p, pts, [("S", SKYWAY_W)])

    # the vault keep, its round door facing the skyway
    p.solid_box("vault keep", -24, 24, 9, 45, 0, 26)
    box_span(p, "PaleAlloy", -23, 23, 10, 44, 0, 1.5)
    box_span(p, "CitadelWhite", -20, 20, 12, 42, 1.5, 21)
    box_span(p, "PaleAlloy", -21, 21, 11, 43, 21, 22.5)
    box_span(p, "CitadelWhite", -16, 16, 16, 38, 22.5, 25)
    for sx in (-1, 1):
        box_span(p, "AzureDim", sx * 20 - 0.2, sx * 20 + 0.2, 16, 38, 6, 16)
        tower(p, sx * 20, 12, 3.6, 24)
    vault_door(p, 0, 12, 10)
    spire(p, 0, 27, 4.2, CROWN_TOP, fins=False, z0=25)     # pins +160

    obelisk(p, -30, -8, h=16)
    obelisk(p, 30, -8, h=16)
    for x, rz in ((-10, 10), (-5, -6), (8, 4)):
        chest(p, x, 2, rz=rz)
    crystal_cluster(p, -38, 20, seed=11, scale=1.2)
    crystal_cluster(p, 40, 16, seed=12)
    crystal_cluster(p, 26, -30, seed=13, scale=0.8)
    for x in (-15, 15):
        lamp(p, x, -40)
    float_crystal(p, "SkyGlass", -40, 44, 30, 2.6, 6, 4.5)
    float_crystal(p, "CitadelViolet", 42, 46, 24, 2.0, 4.5, 3.5)
    finish(p)
    return p


def build_spire_court_b():
    p = Piece("chunk_spire_court_b", "COMBAT (grove role, rare) | openings: south SKYWAY, north ASCENT -- the Hall of Winds")
    pts = [(-60, -100), (60, -100), (96, -40), (96, 40), (60, 100), (-60, 100), (-96, 40), (-96, -40)]
    slab(p, "CitadelWhite", pts, -DECK_T, 0)
    standard_keel(p, pts)
    border_band(p, pts, width=7)
    skyway_deck(p, -HALF, -100, -HALF + 0.4, -101)
    ascent_deck(p, 100, HALF)
    parapet_open(p, pts, [("S", SKYWAY_W), ("N", ASCENT_W)])

    colonnade(p, -44, -72, 54, 6)
    colonnade(p, 44, -72, 54, 6)
    for sx in (-1, 1):
        for y in (-46, 2, 50):
            banner(p, sx * 36, y, rz=90)
    # the Wind Altar and its orbiting shards
    frustum(p, "PaleAlloy", 8, 10, 9, 0, 1.2, 0, -24)
    frustum(p, "DeepAlloy", 8, 6, 5, 1.2, 3.2, 0, -24)
    torus(p, "AzureNeon", 7.5, 0.3, 0, -24, 3.4, n=16)
    p.solid("wind altar", 0, -24, 10.5, 0, 4)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        float_crystal(p, "SkyGlass", 8 * math.cos(a), -24 + 8 * math.sin(a), 12 + 3 * k, 1.6, 4, 3)
    # the Moon Gate: a ring standing in the deck, 72 clear at the ground
    zc, RG = 8.0, 44.0
    a0 = math.degrees(math.asin(-zc / RG)) + 1.0
    p.solid_box("moon gate", -RG - 4, RG + 4, 86, 94, 0, zc + RG + 8)
    torus_arc(p, "CitadelWhite", RG, 3.0, 0, 90, zc, a0, 180 - a0, n=28, rx=90)
    torus_arc(p, "AzureNeon", RG - 3.4, 0.4, 0, 90, zc, a0 + 3, 177 - a0, n=28, rx=90)
    crystal(p, "SunGold", 0, 90, zc + RG + 5.2, 2.2, 4, 2.4)
    # the Great Turbine pins +160; a lesser one to the west
    turbine(p, 74, -10, 132, 17, rz=0, needle_to=CROWN_TOP)
    turbine(p, -74, 20, 64, 12, rz=0)
    for y in (-80, -50, 30, 70):
        lamp(p, -17, y)
        lamp(p, 17, y)
    finish(p)
    return p


def finish(p):
    """Every piece ends here: beacons last (they fit round everything else),
    then the bounding-box pins."""
    corner_beacons(p)
    edge_pins(p)


BUILDERS = [
    # first delivery
    build_entry, build_path_straight, build_spire_court, build_boss_clearing,
    # kit expansion, 2026-09-22
    build_path_bend, build_path_skyport, build_path_hoops, build_garden_terrace,
    build_observatory, build_armory, build_side_vault, build_spire_court_b,
]


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
        PIECES_BY_NAME[p.name] = p
        obj = to_object(p, mats, kit)
        # review layout: rows of four, half a piece of clear air between.
        # This offset lives on the OBJECT; export_kit() zeroes it per piece.
        obj.location = ((i % 4) * (2 * HALF + REVIEW_GAP), -(i // 4) * (2 * HALF + REVIEW_GAP), 0)
        reference_person(obj, 6, 8, refs, mats)
        pieces.append(p)
        objs.append(obj)
    return pieces, objs


# --------------------------------------------------------------------------
# Validation -- the conventions, checked rather than trusted
# --------------------------------------------------------------------------


def float_report(p):
    """Every floating object: inside the tile margin, clear of every other
    float, every solid, and every deck."""
    problems = []
    for i, (la, a) in enumerate(p.floats):
        if not shape_fits_tile(a):
            problems.append("%s at (%.0f, %.0f) is within %g of the tile edge"
                            % (la, (_xy_extent(a)[0] + _xy_extent(a)[1]) / 2,
                               (_xy_extent(a)[2] + _xy_extent(a)[3]) / 2, FLOAT_EDGE_MARGIN))
        for lb, b in p.floats[i + 1:]:
            if shapes_clash(a, b):
                problems.append("%s clips %s" % (la, lb))
        for lb, b in p.solids:
            if shapes_clash(a, b):
                problems.append("%s clips %s" % (la, lb))
        if any(shape_over_slab(a, sl) for sl in p.slabs):
            problems.append("%s clips a deck" % la)
    return problems


PIECES_BY_NAME = {}


def validate(objs):
    report, ok = [], True
    for obj in objs:
        vs = [v.co for v in obj.data.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        size = mx - mn
        centre_xy = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2)
        p = PIECES_BY_NAME.get(obj.name)
        float_problems = float_report(p) if p else ["no build record"]
        checks = {
            "floats clear (no clipping, inside the tile)": not float_problems,
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
            "floats": len(p.floats) if p else 0,
            "float_problems": float_problems[:6],
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
