"""Sky Citadel chunk kit -- generator.

Run inside Blender (tested on 5.2 LTS):

    exec(open(r"<repo>/assets/source/worlds/sky_citadel/build_sky_citadel_kit.py").read())

or from a shell:

    blender --background --python build_sky_citadel_kit.py -- --export

It rebuilds the whole kit from scratch every time, so the .blend next to this
file is an OUTPUT, not a source. Change the look here, re-run, re-export.
docs/biomes/SKY_CITADEL.md is the art direction this script implements, and
docs/CHUNK_AUTHORING.md is the contract every piece has to satisfy.

What it guarantees, and checks before it will export (`validate()`):

* Every piece is ONE mesh object whose bounding box is exactly
  256 x 256 (footprint) x 256 (height: keel tip at -96, crown at +160).
  ChunkLoader sets `mesh.Size = SizeX, SizeY, SizeZ`, so a piece whose box is
  any other size is STRETCHED to fit. Four edge pins (edge_pins()) hold X/Y
  and the bottom at -96; one 160-stud landmark per piece holds the top.
* Nothing that floats clips anything, and nothing that floats comes within
  FLOAT_EDGE_MARGIN of the tile edge -- so neighbours' floats never meet.
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
# Palette. docs/biomes/SKY_CITADEL.md explains each role. sRGB 0-255.
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
        self.up = set()     # single-sided floor panels: forced to face up
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
        return ("cyl", c.x, c.y, r, z0 + c.z, z1 + c.z)

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
    n = len(pts)
    if shape[0] == "cyl":
        cx, cy, r = shape[1], shape[2], shape[3]
        worst = math.inf   # signed distance to the polygon, + inside
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            ex, ey = bx - ax, by - ay
            L = math.hypot(ex, ey)
            worst = min(worst, ((cx - ax) * -ey + (cy - ay) * ex) / L)   # CCW: + is inside
        return worst > -(r + gap)
    # A box: separating-axis test against the convex deck, so a long thin
    # float (a skiff) is not treated as the circle round it.
    x0, x1, y0, y1 = _xy_extent(shape)
    corners = [(x0 - gap, y0 - gap), (x1 + gap, y0 - gap), (x1 + gap, y1 + gap), (x0 - gap, y1 + gap)]
    if max(q[0] for q in pts) <= corners[0][0] or min(q[0] for q in pts) >= corners[1][0]:
        return False
    if max(q[1] for q in pts) <= corners[0][1] or min(q[1] for q in pts) >= corners[2][1]:
        return False
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        if all(((qx - ax) * -ey + (qy - ay) * ex) / L <= 0 for qx, qy in corners):
            return False   # every corner outside this edge: separated
    return True


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
# "What floats on purpose" in docs/biomes/SKY_CITADEL.md.
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
    with frame(p, xf(x, y, z, rz)):
        p.float_box("skiff", -13.5, 16, -6, 6, -4.5, 13)
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
    _dish(p, x, y, h, rz, tilt, R)


def _dish(p, x, y, h, rz, tilt, R):
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
# Variety toolkit (pass 3, 2026-09-22)
#
# Owner review of the 12-piece kit: "each piece is very similar to the next."
# It was: every piece was one white slab on the same cone keel, ringed by the
# same parapet, lit by the same lamps, marked by the same needle spire. The
# pieces below are built from FIVE independent axes, and no two neighbours in
# the table in docs/biomes/SKY_CITADEL.md share more than two:
#
#   shape     one deck, or an archipelago of islands joined by short bridges
#   floor     radial gold, planks, checker, lawn, night sky, slate yard,
#             compass rose, hazard stripes, gold grid, glass
#   edge      parapet, railing, glowing kerb, hedge
#   keel      cone, stepped ziggurat, twin cones, crystal roots, engine,
#             cone with floating rings
#   landmark  needle spire, spired keep, lighthouse, sky tree, floating
#             prism, banner mast, turbine, observatory mast, signal mast
# --------------------------------------------------------------------------


def panel(p, mat, cx, cy, sx, sy, z=0.06, rz=0.0):
    """A single-faced floor decal, forced to face up. 2 triangles, where a
    box would be 12 -- which is what makes whole patterned floors affordable."""
    hx, hy = sx / 2, sy / 2
    p.up.add(len(p.faces))
    p.add([(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0)], [(0, 1, 2, 3)], mat,
          xf(cx, cy, z, rz))


def tri_panel(p, mat, a, b, c, z=0.06):
    p.up.add(len(p.faces))
    p.add([(a[0], a[1], z), (b[0], b[1], z), (c[0], c[1], z)], [(0, 1, 2)], mat, Matrix.Identity(4))


def inside(pts, x, y, margin=0.0):
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        if ((x - ax) * -ey + (y - ay) * ex) / L < margin:
            return False
    return True


def moved(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


# ---- floors ----------------------------------------------------------------


def floor_checker(p, pts, mat, tile=10.0, margin=5.0, keep=None, z=0.06):
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    for i in range(int(min(xs) // tile) - 1, int(max(xs) // tile) + 1):
        for j in range(int(min(ys) // tile) - 1, int(max(ys) // tile) + 1):
            if (i + j) % 2:
                continue
            cx, cy = (i + 0.5) * tile, (j + 0.5) * tile
            h = tile / 2
            if all(inside(pts, cx + dx, cy + dy, margin) for dx in (-h, h) for dy in (-h, h)):
                if keep is None or keep(cx, cy):
                    panel(p, mat, cx, cy, tile - 0.5, tile - 0.5, z=z)


def floor_planks(p, x0, x1, y0, y1, mat, step=5.0, width=2.2):
    y = y0 + step / 2
    while y < y1:
        panel(p, mat, (x0 + x1) / 2, y, x1 - x0, width)
        y += step


def floor_radial(p, cx, cy, r0, r1, n, mat, width=2.0, z=0.06, phase=0.0):
    for k in range(n):
        a = math.radians(phase + 360.0 * k / n)
        rm = (r0 + r1) / 2
        panel(p, mat, cx + math.cos(a) * rm, cy + math.sin(a) * rm, r1 - r0, width, z=z,
              rz=math.degrees(a))


def floor_stars(p, cx, cy, rmin, rmax, count, seed, keep=None):
    rng = random.Random(seed)
    placed = 0
    while placed < count:
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(rmin, rmax)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if keep and not keep(x, y):
            continue
        s = rng.uniform(0.6, 1.4)
        panel(p, "AzureNeon" if rng.random() < 0.6 else "SunGold", x, y, s, s, rz=45)
        placed += 1


def floor_grid(p, pts, mat, step=16.0, w=0.8, margin=4.0):
    """Grid lines clipped to a convex deck."""
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    x = (min(xs) // step + 1) * step
    while x < max(xs):
        span = [y for y in _frange(min(ys), max(ys), 1.0) if inside(pts, x, y, margin)]
        if len(span) > 2:
            panel(p, mat, x, (span[0] + span[-1]) / 2, w, span[-1] - span[0])
        x += step
    y = (min(ys) // step + 1) * step
    while y < max(ys):
        span = [x_ for x_ in _frange(min(xs), max(xs), 1.0) if inside(pts, x_, y, margin)]
        if len(span) > 2:
            panel(p, mat, (span[0] + span[-1]) / 2, y, span[-1] - span[0], w, z=0.07)
        y += step


def _frange(a, b, st):
    v = a
    while v <= b:
        yield v
        v += st


def compass_rose(p, cx, cy, r_long, r_short):
    """A four-point gold star on an eight-point pale one."""
    for k in range(8):
        a = math.radians(45 * k)
        rl = r_long if k % 2 == 0 else r_long * 0.62
        tip = (cx + math.cos(a) * rl, cy + math.sin(a) * rl)
        for side in (-1, 1):
            b = math.radians(45 * k + side * 22.5)
            mid = (cx + math.cos(b) * r_short, cy + math.sin(b) * r_short)
            mat = ("SunGold" if side < 0 else "PaleAlloy") if k % 2 == 0 else "AzureDim"
            tri_panel(p, mat, (cx, cy), tip, mid, z=0.08 if k % 2 == 0 else 0.07)


def hazard_pad(p, cx, cy, R):
    frustum(p, "HullSlate", 12, R, R - 0.6, 0, 0.4, cx, cy)
    for k in range(12):
        a = 15 + 30 * k
        r = math.radians(a)
        panel(p, "SunGold" if k % 2 else "DeepAlloy", cx + math.cos(r) * (R - 3), cy + math.sin(r) * (R - 3),
              4.2, 2.2, z=0.46, rz=a + 90)
    torus(p, "AzureNeon", R * 0.55, 0.25, cx, cy, 0.5, n=16)
    panel(p, "PaleAlloy", cx, cy, 1.6, R * 0.7, z=0.47)
    panel(p, "PaleAlloy", cx, cy, R * 0.45, 1.6, z=0.48)


# ---- edges -----------------------------------------------------------------


def open_segments(pts, openings):
    """Edges of a convex deck, split round its openings. openings: list of
    (side, width) or (side, width, centre) -- side in 'NSEW', centre is the
    mouth's position along that edge (default 0)."""
    n = len(pts)
    ymax, ymin = max(q[1] for q in pts), min(q[1] for q in pts)
    xmax, xmin = max(q[0] for q in pts), min(q[0] for q in pts)
    out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        inward = (-ey / L, ex / L)
        segs = [(a, b)]
        for op in openings:
            side, w = op[0], op[1]
            c = op[2] if len(op) > 2 else 0.0
            hw = w / 2
            new = []
            for s0, s1 in segs:
                if side in "NS":
                    yl = ymax if side == "N" else ymin
                    if abs(s0[1] - yl) < 1e-3 and abs(s1[1] - yl) < 1e-3:
                        lo, hi = sorted((s0[0], s1[0]))
                        for x0, x1 in ((lo, min(hi, c - hw)), (max(lo, c + hw), hi)):
                            if x1 - x0 > 2:
                                new.append(((x0, yl), (x1, yl)))
                        continue
                else:
                    xl = xmax if side == "E" else xmin
                    if abs(s0[0] - xl) < 1e-3 and abs(s1[0] - xl) < 1e-3:
                        lo, hi = sorted((s0[1], s1[1]))
                        for y0, y1 in ((lo, min(hi, c - hw)), (max(lo, c + hw), hi)):
                            if y1 - y0 > 2:
                                new.append(((xl, y0), (xl, y1)))
                        continue
                new.append((s0, s1))
            segs = new
        for s0, s1 in segs:
            if (s1[0] - s0[0]) * ex + (s1[1] - s0[1]) * ey < 0:
                s0, s1 = s1, s0
            out.append((s0, s1, inward))
    return out


def _edge_parapet(p, a, b, inward):
    parapet(p, a, b, inward)


def _edge_railing(p, a, b, inward):
    ix, iy = inward
    railing(p, a[0] + ix * 0.8, a[1] + iy * 0.8, b[0] + ix * 0.8, b[1] + iy * 0.8)


def _edge_kerb(p, a, b, inward):
    ix, iy = inward
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    mx, my = (a[0] + b[0]) / 2 + ix * 0.8, (a[1] + b[1]) / 2 + iy * 0.8
    box(p, "PaleAlloy", mx, my, 0.45, L, 1.4, 0.9, rz=ang)
    box(p, "AzureDim", mx, my, 0.95, L, 0.6, 0.12, rz=ang)


def _edge_hedge(p, a, b, inward):
    ix, iy = inward
    hedge(p, a[0] + ix * 1.2, a[1] + iy * 1.2, b[0] + ix * 1.2, b[1] + iy * 1.2, h=2.6)


EDGES = {"parapet": _edge_parapet, "railing": _edge_railing, "kerb": _edge_kerb, "hedge": _edge_hedge}


def edge_ring(p, pts, openings, style):
    for a, b, inward in open_segments(pts, openings):
        EDGES[style](p, a, b, inward)


# ---- keels -----------------------------------------------------------------


def stepped_keel(p, pts, centre=(0.0, 0.0), steps=5):
    """An inverted ziggurat: terraces shrinking downward."""
    prof = [(-DECK_T + 0.5, 0.98, 0, "HullSlate")]
    z, sc = -DECK_T + 0.5, 0.98
    for k in range(steps):
        zn = z - 9.0
        prof.append((zn, sc, 0, "HullSlate"))
        sc2 = sc * 0.74
        prof.append((zn, sc2, 0, "PaleAlloy" if k % 2 == 0 else "DeepAlloy"))
        z, sc = zn, sc2
    prof.append((z - 16, 0.0, 0, "AzureDim"))
    keel(p, pts, prof, centre=centre)


def shallow_hull(p, pts, centre=(0.0, 0.0), depth=16.0):
    keel(p, pts, [(-DECK_T + 0.5, 0.98, 0, "HullSlate"), (-10, 0.9, 3, "HullSlate"),
                  (-12, 0.91, 3, "AzureDim"), (-depth, 0.7, 0, "HullSlate"),
                  (-depth - 3, 0.0, 0, "DeepAlloy")], centre=centre)


def twin_keel(p, pts, c1, c2, r, depth=80.0):
    shallow_hull(p, pts)
    for i, (cx, cy) in enumerate((c1, c2)):
        d = depth - 14 * i
        frustum(p, "HullSlate", 8, r, r * 0.8, -12, -12 - d * 0.35, cx, cy)
        frustum(p, "AzureDim", 8, r * 0.82, r * 0.82, -12 - d * 0.35, -15 - d * 0.35, cx, cy)
        frustum(p, "DeepAlloy", 8, r * 0.8, 0, -15 - d * 0.35, -12 - d, cx, cy)


def crystal_root_keel(p, pts, seed, centre=(0.0, 0.0), spread=0.55, count=11):
    """A shallow hull with crystals hanging from it like roots."""
    shallow_hull(p, pts, centre=centre, depth=14)
    rng = random.Random(seed)
    cx0, cy0 = centre
    for i in range(count):
        x, y = rng.choice(pts)
        t = rng.uniform(0.0, spread)
        x, y = cx0 + (x - cx0) * t, cy0 + (y - cy0) * t
        length = 84 if i == 0 else rng.uniform(18, 60)
        mat = ("SkyGlass", "HullSlate", "CitadelViolet")[i % 3]
        crystal(p, mat, x, y, -12, rng.uniform(2.5, 5.5), 5, length, n=5, rz=rng.uniform(0, 72))


def engine_keel(p, pts, centre=(0.0, 0.0), R=30.0):
    """A hull with a drive underneath: drum, glowing ring, four nozzles."""
    cx, cy = centre
    keel(p, pts, [(-DECK_T + 0.5, 0.98, 0, "HullSlate"), (-14, 0.86, 0, "HullSlate"),
                  (-17, 0.87, 0, "DeepAlloy"), (-30, 0.5, 0, "HullSlate"),
                  (-32, 0.0, 0, "HullSlate")], centre=centre)
    frustum(p, "DeepAlloy", 12, R * 0.34, R * 0.34, -44, -28, cx, cy)
    torus(p, "AzureNeon", R * 0.38, 0.5, cx, cy, -40, n=20)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        nx, ny = cx + math.cos(a) * R * 0.3, cy + math.sin(a) * R * 0.3
        frustum(p, "PaleAlloy", 8, R * 0.09, R * 0.13, -30, -52, nx, ny)
        frustum(p, "AzureNeon", 8, R * 0.12, R * 0.12, -52, -53, nx, ny)
    frustum(p, "HullSlate", 8, R * 0.16, 0, -44, -70, cx, cy)


def ring_keel(p, pts, R):
    standard_keel(p, pts)
    for z, rr in ((-50, R * 0.62), (-72, R * 0.38)):
        p.float_("keel ring", 0, 0, rr + 1.2, z - 1.2, z + 1.2)
        torus(p, "AzureNeon", rr, 0.6, 0, 0, z, n=24)
        torus(p, "PaleAlloy", rr + 1.2, 0.5, 0, 0, z, n=24)


def vines(p, pts, seed, count=10):
    """Green strands hanging from a deck's rim -- garden islands only."""
    rng = random.Random(seed)
    n = len(pts)
    for _ in range(count):
        i = rng.randrange(n)
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        t = rng.uniform(0.2, 0.8)
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        L = rng.uniform(6, 18)
        box(p, "Verdure", x * 0.985, y * 0.985, -DECK_T - L / 2, 0.8, 0.8, L)


# ---- lights ----------------------------------------------------------------


def brazier(p, x, y):
    p.solid("brazier", x, y, 2.4, 0, 8)
    frustum(p, "DeepAlloy", 6, 1.2, 0.8, 0, 3.2, x, y)
    frustum(p, "PaleAlloy", 8, 0.8, 2.2, 3.2, 4.4, x, y)
    frustum(p, "AzureDim", 8, 1.9, 1.9, 4.2, 4.5, x, y)
    crystal(p, "AzureNeon", x, y, 6.2, 0.9, 1.6, 1.4)


def light_pillar(p, x, y, h=7.0):
    frustum(p, "PaleAlloy", 4, 1.0, 0.9, 0, 0.8, x, y, rot=45)
    frustum(p, "AzureDim", 4, 0.55, 0.55, 0.8, h, x, y, rot=45)
    frustum(p, "PaleAlloy", 4, 0.9, 0, h, h + 1.2, x, y, rot=45)


# ---- landmarks -------------------------------------------------------------


def lighthouse(p, x, y, top=CROWN_TOP):
    p.solid("lighthouse", x, y, 10, 0, top)
    frustum(p, "PaleAlloy", 12, 10, 9.4, 0, 2, x, y)
    bands = [(2, 18, "CitadelWhite"), (18, 22, "CitadelViolet"), (22, 38, "CitadelWhite"),
             (38, 42, "CitadelViolet"), (42, 58, "CitadelWhite")]
    for z0, z1, mat in bands:
        r0 = 8.0 - z0 * 0.03
        r1 = 8.0 - z1 * 0.03
        frustum(p, mat, 12, r0, r1, z0, z1, x, y)
    frustum(p, "PaleAlloy", 12, 6.4, 8.6, 58, 60, x, y)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        frustum(p, "DeepAlloy", 4, 0.4, 0.4, 60, 68, x + math.cos(a) * 5.4, y + math.sin(a) * 5.4)
    frustum(p, "AzureNeon", 8, 3.0, 3.0, 61, 67, x, y)
    frustum(p, "PaleAlloy", 12, 6.6, 0.8, 68, 75, x, y)
    frustum(p, "DeepAlloy", 4, 0.8, 0, 75, top, x, y)
    for z in (95, 118):
        box(p, "SunGold", x, y, z, 5, 0.4, 0.4)


def sky_tree(p, x, y, top=CROWN_TOP):
    """A white-barked tree with a canopy of green and glass -- the garden's
    landmark, and the only living thing in the world taller than a person."""
    p.solid("tree trunk", x, y, 9.5, 0, 90)
    p.solid("tree canopy", x, y, 34, 90, top)
    frustum(p, "PaleAlloy", 8, 9, 8, 0, 1.2, x, y)
    frustum(p, "DeepAlloy", 8, 8, 7.5, 1.2, 2.2, x, y)
    for k in range(5):
        a = math.radians(20 + 72 * k)
        box(p, "CitadelWhite", x + math.cos(a) * 5, y + math.sin(a) * 5, 1.2, 7, 1.6, 2.2, rz=math.degrees(a))
    trunk = [(0, 5.2), (30, 4.4), (60, 3.8), (95, 3.0)]
    for (z0, r0), (z1, r1) in zip(trunk, trunk[1:]):
        frustum(p, "CitadelWhite", 8, r0, r1, 2.2 if z0 == 0 else z0, z1, x, y)
    rng = random.Random("sky tree")
    blobs = []
    for k in range(6):
        a = math.radians(15 + 60 * k)
        L = rng.uniform(16, 22)
        z = 72 + 5 * (k % 3)
        box(p, "CitadelWhite", x + math.cos(a) * L / 2, y + math.sin(a) * L / 2, z + L * 0.25, L, 1.8, 1.8,
            rz=math.degrees(a), ry=-25)
        blobs.append((x + math.cos(a) * L, y + math.sin(a) * L, z + L * 0.5 + 12))
    blobs.append((x, y, 128))
    blobs.append((x + 6, y - 5, 110))
    for i, (bx, by, bz) in enumerate(blobs):
        r = 13 if i < 6 else 17
        orb(p, "Verdure" if i % 3 else "SkyGlass", bx, by, bz, r)
    crystal(p, "SkyGlass", x, y, 150, 4.5, top - 150, 6, n=6)


def arcane_prism(p, x, y, top=CROWN_TOP):
    """A great glass prism hanging over the crossroads, ringed, held by four
    gold-tipped pylons that stop short of it."""
    for k in range(4):
        a = math.radians(45 + 90 * k)
        px, py = x + math.cos(a) * 36, y + math.sin(a) * 36
        p.solid("prism pylon", px, py, 3.4, 0, 80)
        frustum(p, "DeepAlloy", 4, 3.4, 3.0, 0, 2, px, py, rot=45)
        frustum(p, "PaleAlloy", 4, 2.6, 1.1, 2, 72, px, py, rot=45)
        frustum(p, "AzureDim", 4, 2.0, 2.0, 40, 42, px, py, rot=45)
        crystal(p, "SunGold", px, py, 75, 1.1, 4.5, 3.0)
    p.float_("arcane prism", x, y, 23.5, 100, top)
    crystal(p, "SkyGlass", x, y, 128, 12, top - 128, 26, n=6)
    torus(p, "AzureNeon", 17, 0.6, x, y, 128, n=24)
    torus(p, "PaleAlloy", 21.5, 0.7, x, y, 122, n=24, rx=24)


def banner_mast(p, x, y, top=CROWN_TOP):
    p.solid("banner mast", x, y, 9, 0, top)
    frustum(p, "DeepAlloy", 8, 6, 5, 0, 3, x, y)
    frustum(p, "PaleAlloy", 6, 1.7, 0.7, 3, 150, x, y)
    for z, w, h in ((42, 14, 18), (84, 10, 13), (120, 7, 9)):
        box(p, "SunGold", x, y, z, w, 0.6, 0.6)
        for s in (-1, 1):
            box(p, "CitadelViolet", x + s * w * 0.28, y, z - 0.8 - h / 2, w * 0.36, 0.3, h)
        frustum(p, "AzureDim", 6, 1.3, 1.3, z - 3, z - 2, x, y)
    crystal(p, "SunGold", x, y, 153, 1.6, top - 153, 3)


def signal_mast(p, x, y, top=CROWN_TOP):
    p.solid("signal mast", x, y, 5, 0, top)
    frustum(p, "PaleAlloy", 4, 3.4, 3.0, 0, 3, x, y, rot=45)
    frustum(p, "CitadelWhite", 4, 1.6, 0.4, 3, top - 4, x, y, rot=45)
    for z in (40, 70, 100, 128):
        box(p, "CitadelViolet", x + 3, y, z, 6, 0.25, 2.4)
        frustum(p, "AzureDim", 4, 1.2, 1.2, z + 3, z + 4, x, y, rot=45)
    crystal(p, "AzureNeon", x, y, top - 2.5, 1.0, 2.5, 1.5)


# ---- structure -------------------------------------------------------------


def bridge_x(p, x0, x1, yc, w=12.0):
    """A short internal bridge along X between two of a piece's own islands."""
    hw = w / 2
    box_span(p, "CitadelWhite", x0, x1, yc - hw, yc + hw, -DECK_T, 0)
    for sy in (-1, 1):
        box_span(p, "AzureDim", x0, x1, yc + sy * hw - (0.5 if sy < 0 else 0), yc + sy * hw + (0.5 if sy > 0 else 0),
                 -2.2, -0.9)
        railing(p, x0 + 0.5, yc + sy * (hw - 0.6), x1 - 0.5, yc + sy * (hw - 0.6), spacing=8)


def terrace(p, pts, h, mat="CitadelWhite"):
    """A raised, walkable deck standing on the main one."""
    slab_raised = [(x, y) for x, y in pts]
    n = len(pts)
    verts = [(x, y, 0.0) for x, y in slab_raised] + [(x, y, h) for x, y in slab_raised]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    p.add(verts, faces, mat, Matrix.Identity(4))
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        box(p, "AzureDim", (ax + bx) / 2, (ay + by) / 2, h - 0.6, L + 0.1, 0.25, 0.4, rz=ang)
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    p.solid_box("terrace", min(xs), max(xs), min(ys), max(ys), 0, h)


def ramp(p, x, y, w, L, h, facing, mat="PaleAlloy"):
    """A walkable wedge: foot at (x, y), rising h over L toward `facing`
    ('N', 'S', 'E', 'W'). Kept under 30 degrees."""
    rz = {"N": 0, "W": 90, "S": 180, "E": -90}[facing]
    hw = w / 2
    v = [(-hw, 0, 0), (hw, 0, 0), (hw, L, 0), (-hw, L, 0), (hw, L, h), (-hw, L, h)]
    f = [(0, 3, 2, 1), (0, 1, 4, 5), (2, 3, 5, 4), (1, 2, 4), (0, 5, 3)]
    p.add(v, f, mat, xf(x, y, 0, rz))
    for sx in (-1, 1):
        box(p, "AzureDim", 0, 0, 0, 0.3, 0.3, 0.3)   # (no-op spacer kept tiny)
    with frame(p, xf(x, y, 0, rz)):
        for sx in (-1, 1):
            box(p, "AzureDim", sx * (hw - 0.3), L / 2, h / 2 * 0.5 + 0.2, 0.3, L, 0.3, rx=-math.degrees(math.atan2(h, L)))


def island(p, pts, floor_mat="CitadelWhite"):
    slab(p, floor_mat, pts, -DECK_T, 0)


# --------------------------------------------------------------------------
# The fifteen pieces
# --------------------------------------------------------------------------


def build_entry():
    p = Piece("chunk_entry", "ENTRY | one opening: north SKYWAY -- arrival plaza")
    R = 84.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts)
    standard_keel(p, pts)
    border_band(p, pts)
    floor_radial(p, 0, 0, 26, 60, 16, "SunGold", width=1.6, phase=11.25)
    torus(p, "AzureDim", 62, 0.35, 0, 0, 0.05, n=24)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("N", SKYWAY_W)], "parapet")

    # arrival pad -- the spawn falls onto it; the column above (0,0) stays clear
    frustum(p, "PaleAlloy", 16, 22, 21, 0, 0.5, 0, 0)
    torus(p, "AzureNeon", 19, 0.3, 0, 0, 0.55, n=24)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        box(p, "AzureDim", math.cos(a) * 12, math.sin(a) * 12, 0.55, 6, 0.8, 0.2, rz=45 * k + 22.5)

    spire(p, -50, 30, 7, CROWN_TOP, extra_halos=1)    # the Beacon
    spire(p, 50, 30, 6, 118)
    tower(p, -54, -46, 9, 30)
    tower(p, 54, -46, 9, 30)
    banner(p, -26, apo - 8)
    banner(p, 26, apo - 8)
    for x, y in ((-30, -26), (30, -26), (-30, 14), (30, 14)):
        lamp(p, x, y)
    holo_pedestal(p, -24, -62)    # the return portal lands near (0, -64)
    holo_pedestal(p, 24, -62)
    for x, y in ((-40, -6), (40, -6), (-16, 50), (16, 50)):
        planter(p, x, y)
    bench(p, -40, 4, rz=90)
    bench(p, 40, 4, rz=90)
    crate(p, -66, -18, 3.2, rz=10)
    crate(p, -62, -20, 3.2, rz=-6)
    crate(p, -64, -19, 3.0, z=3.2, rz=25)
    float_crystal(p, "SkyGlass", -34, 50, 20, 2.4, 5, 4)
    float_crystal(p, "SkyGlass", 34, 50, 26, 2.0, 4, 3.5)
    finish(p)
    return p


def build_path_straight():
    p = Piece("chunk_path_straight", "PATH | N + S SKYWAY -- the gatehouse pier")
    R = 44.0
    pts = ngon(6, R, rot=0)
    apo = R * math.cos(math.radians(30))
    island(p, pts, "PaleAlloy")
    twin_keel(p, pts, (0, 22), (0, -22), 13)
    floor_planks(p, -20, 20, -apo + 1, apo - 1, "CitadelWhite", step=4.5, width=2.6)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    edge_ring(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)], "railing")

    tower(p, -32, 0, 6, 64)
    tower(p, 32, 0, 6, 64)
    p.solid_box("gatehouse lintel", -30, 30, -4, 4, 28, 48)
    box(p, "PaleAlloy", 0, 0, 32, 52, 7, 4)
    box(p, "AzureDim", 0, 0, 29.7, 50, 3.5, 0.6)
    for s_ in (-1, 1):
        box(p, "CitadelWhite", s_ * 13, 0, 37.2, 27.5, 5.6, 3, ry=s_ * 16)
    crystal(p, "SunGold", 0, 0, 45.5, 2.0, 3.6, 2.2)

    spire(p, -30, -24, 5, CROWN_TOP)
    spire(p, 30, 24, 4.5, 104, fins=False)
    for x, y in ((17, 62), (-17, 102), (-17, -62), (17, -102)):
        lamp(p, x, y)
    banner(p, -24, 22)
    banner(p, 24, -22)
    crate(p, 26, -28, 3.0, rz=12)
    anti_grav_pylon(p, -76, 70, 6)
    anti_grav_pylon(p, 76, -70, 10)
    finish(p)
    return p


def build_path_bend():
    p = Piece("chunk_path_bend", "PATH | S + E SKYWAY -- turns right round the Spired Keep")
    R = 58.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts)
    crystal_root_keel(p, pts, seed="bend roots")
    floor_checker(p, pts, "PaleAlloy", tile=9, margin=4, keep=lambda x, y: math.hypot(x, y) > 20)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck_x(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("S", SKYWAY_W), ("E", SKYWAY_W)], "railing")

    tower(p, 0, 0, 13, 56, roof=False)
    spire(p, 0, 0, 5.5, CROWN_TOP, fins=False, z0=59)
    for k in range(4):
        a = math.radians(135 + 90 * k)
        banner(p, math.cos(a) * 20, math.sin(a) * 20, rz=math.degrees(a) + 90)
    for a in (100, 160, 200, 250):
        r = math.radians(a)
        brazier(p, math.cos(r) * 42, math.sin(r) * 42)
    planter(p, 30, 36)
    crate(p, 34, -36, 3.0, rz=15)
    crate(p, 37, -33, 2.6, rz=-10)
    anti_grav_pylon(p, -86, 72, 4)
    float_crystal(p, "SkyGlass", -64, -60, 18, 2.6, 6, 4.5)
    finish(p)
    return p


def build_path_bend_west():
    p = Piece("chunk_path_bend_west", "PATH | S + W SKYWAY -- turns left past the lighthouse")
    R = 58.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts, "DeepAlloy")
    engine_keel(p, pts, R=52)
    border_band(p, pts, width=5)
    torus(p, "AzureDim", 30, 0.3, 0, 0, 0.05, n=24)
    torus(p, "AzureDim", 44, 0.3, 0, 0, 0.05, n=28)
    floor_radial(p, 0, 0, 30, 44, 24, "PaleAlloy", width=1.0)
    compass_rose(p, 0, 0, 22, 6)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    with oriented(p, 90):
        skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("S", SKYWAY_W), ("W", SKYWAY_W), ("E", 12)], "kerb")

    # the lighthouse stands on its own islet, reached by a short bridge east
    ipts = moved(ngon(12, 24), 90, 0)
    island(p, ipts)
    keel(p, ipts, [(-DECK_T + 0.5, 0.97, 0, "HullSlate"), (-10, 0.8, 0, "HullSlate"),
                   (-12, 0.81, 0, "AzureDim"), (-40, 0.0, 0, "DeepAlloy")], centre=(90, 0))
    bridge_x(p, apo, 90 - 24 * math.cos(math.radians(15)), 0, w=12)
    edge_ring(p, ipts, [("W", 12)], "railing")
    lighthouse(p, 92, 0)
    for x, y in ((-26, 26), (26, 26), (26, -26), (-26, -26)):
        light_pillar(p, x, y)
    bench(p, 30, 40, rz=-45)
    holo_pedestal(p, -34, 38)
    float_crystal(p, "SkyGlass", 70, 70, 22, 2.4, 5.5, 4)
    float_crystal(p, "SkyGlass", -70, -72, 30, 2.0, 4.5, 3.5)
    finish(p)
    return p


def build_path_skyport():
    p = Piece("chunk_path_skyport", "PATH | N + S SKYWAY -- the skiff dock")
    mpts = chamfer_rect(26, 62, 6)
    island(p, mpts, "PaleAlloy")
    stepped_keel(p, mpts, steps=4)
    floor_planks(p, -20, 20, -56, 56, "CitadelWhite", step=6, width=3.2)
    skyway_deck(p, -HALF, -62, -HALF + 0.4, -63)
    skyway_deck(p, 62, HALF, 63, HALF - 0.4)
    edge_ring(p, mpts, [("N", SKYWAY_W), ("S", SKYWAY_W), ("E", 12)], "railing")
    for (x, y, r) in ((-12, -40, 90), (-12, 30, 90)):
        container(p, x - 8, y, rz=r)
    crate(p, 14, -46, 3.0, rz=14)
    crate(p, 14, -46, 2.6, z=3.0, rz=-4)

    # the dock islet: hazard pad, crane, control tower, and the skiff beyond
    dpts = moved(ngon(12, 34), 76, 0)
    island(p, dpts, "HullSlate")
    engine_keel(p, dpts, centre=(76, 0), R=34)
    bridge_x(p, 26, 76 - 34 * math.cos(math.radians(15)), 0, w=12)
    edge_ring(p, dpts, [("W", 12), ("E", 12)], "kerb")
    hazard_pad(p, 72, -8, 16)
    crane(p, 94, -20, rz=10)
    tower(p, 86, 20, 6, 30, roof=False)
    signal_mast(p, 86, 20)
    box_span(p, "PaleAlloy", 76 + 33, 76 + 44, -3, 3, -0.6, -0.1)
    skiff(p, 117, 0, -2.2, rz=90)
    anti_grav_pylon(p, -70, -40, 6)
    float_crystal(p, "SkyGlass", -64, 56, 22, 2.4, 5.5, 4)
    finish(p)
    return p


def build_path_hoops():
    p = Piece("chunk_path_hoops", "PATH | N + S SKYWAY -- a bare span through three rings")
    skyway_deck(p, -HALF, HALF, -HALF + 0.4, HALF - 0.4)
    for y in range(-120, 121, 12):
        panel(p, "SkyGlass", 0, y, 10, 8)
    frustum(p, "HullSlate", 8, 9, 7, -DECK_T + 0.5, -20, 0, 0)
    frustum(p, "AzureDim", 8, 7.2, 7.2, -20, -23, 0, 0)
    frustum(p, "DeepAlloy", 8, 7, 0, -23, -64, 0, 0)
    for y in (-78, 0, 78):
        hoop(p, y)
    for y in (-40, 40):
        light_pillar(p, 17, y, h=5)
        light_pillar(p, -17, y, h=5)
    for (cx, cy, R, rot) in ((-74, 34, 22, 0), (72, -44, 17, 30)):
        spts = moved(ngon(6, R, rot=rot), cx, cy)
        island(p, spts)
        crystal_root_keel(p, spts, seed="hoops %d" % cx, centre=(cx, cy), count=5)
        edge_ring(p, spts, [], "parapet")
    spire(p, -74, 34, 6, CROWN_TOP, extra_halos=1)
    obelisk(p, 72, -44, h=18)
    crystal_cluster(p, 78, -50, seed=7)
    anti_grav_pylon(p, 64, 72, 10)
    anti_grav_pylon(p, -66, -70, 2)
    finish(p)
    return p


def build_crossroads():
    p = Piece("chunk_crossroads", "PATH | N + S + E + W SKYWAY -- the intersection")
    R = 56.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts)
    stepped_keel(p, pts, steps=5)
    compass_rose(p, 0, 0, 34, 9)
    torus(p, "AzureDim", 40, 0.35, 0, 0, 0.05, n=28)
    torus(p, "SunGold", 44, 0.25, 0, 0, 0.05, n=28)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck_x(p, apo, HALF, apo + 1, HALF - 0.4)
    with oriented(p, 90):
        skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W), ("E", SKYWAY_W), ("W", SKYWAY_W)], "kerb")
    arcane_prism(p, 0, 0)
    # a signpost at each mouth, a lantern at each diagonal
    for k, (x, y, rz) in enumerate(((26, 44, 0), (-26, -44, 180), (44, -26, -90), (-44, 26, 90))):
        banner(p, x, y, rz=rz, h=10)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        brazier(p, math.cos(a) * 48, math.sin(a) * 48)
    finish(p)
    return p


def build_garden_terrace():
    p = Piece("chunk_garden_terrace", "COMBAT | N + S SKYWAY -- the hanging gardens")
    cpts = chamfer_rect(34, 100, 10)
    island(p, cpts)
    crystal_root_keel(p, cpts, seed="garden roots", count=8)
    vines(p, cpts, "garden vines", 12)
    floor_checker(p, cpts, "Verdure", tile=8, margin=4,
                  keep=lambda x, y: abs(x) > 12 and math.hypot(x, y - 44) > 12)
    skyway_deck(p, -HALF, -100, -HALF + 0.4, -101)
    skyway_deck(p, 100, HALF, 101, HALF - 0.4)
    edge_ring(p, cpts, [("N", SKYWAY_W), ("S", SKYWAY_W), ("W", 12, 26), ("E", 12, -30)], "hedge")
    sky_tree(p, 0, 44)
    for y in (-80, -56, -32, -8):
        topiary_orb(p, -24, y, r=2.0)
        topiary_orb(p, 24, y, r=2.0)

    # the west islet: a reflecting pool under a pergola
    wpts = moved(ngon(12, 36), -84, 26)
    island(p, wpts)
    crystal_root_keel(p, wpts, seed="west islet", centre=(-84, 26), count=6)
    vines(p, wpts, "west vines", 8)
    bridge_x(p, -84 + 36 * math.cos(math.radians(15)), -34, 26, w=12)
    edge_ring(p, wpts, [("E", 12)], "hedge")
    pool(p, -86, 26, 20, 30)
    pergola(p, -104, 8, 44, width=8, h=8)
    float_crystal(p, "SkyGlass", -86, 26, 16, 2.4, 5, 4)

    # the east islet: a gazebo in flower beds
    epts = moved(ngon(8, 34), 80, -30)
    island(p, epts)
    crystal_root_keel(p, epts, seed="east islet", centre=(80, -30), count=6)
    vines(p, epts, "east vines", 8)
    bridge_x(p, 34, 80 - 34 * math.cos(math.radians(22.5)), -30, w=12)
    edge_ring(p, epts, [("W", 12)], "hedge")
    gazebo(p, 84, -30)
    for k, a in enumerate((60, 120, 240, 300)):
        r = math.radians(a)
        flower_bed(p, 84 + math.cos(r) * 20, -30 + math.sin(r) * 20, lx=7, seed=k)
    bench(p, 62, -14, rz=0)
    finish(p)
    return p


def build_observatory():
    p = Piece("chunk_observatory", "COMBAT | N + S SKYWAY -- the stargazers' deck, at night")
    R = 84.0
    pts = ngon(12, R)
    apo = R * math.cos(math.radians(15))
    island(p, pts, "DeepAlloy")
    ring_keel(p, pts, R)
    border_band(p, pts, width=5)
    floor_stars(p, 0, 0, 8, 76, 60, "night sky",
                keep=lambda x, y: not (26 < x < 80 and -52 < y < 52) and abs(x) > 3)
    torus(p, "AzureDim", 34, 0.3, 0, -4, 0.05, n=28)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)], "railing")
    orrery(p, 0, -4)

    # the upper deck: dishes six studs up, reached by a ramp
    tpts = [(30, -48), (72, -40), (72, 40), (30, 48)]
    terrace(p, tpts, 6.0, "CitadelWhite")
    ramp(p, 18, 0, 12, 12, 6.0, "E")
    for a, b in ((tpts[1], tpts[2]), (tpts[2], tpts[3]), (tpts[0], tpts[1])):
        with frame(p, xf(z=6)):
            railing(p, a[0], a[1], b[0], b[1])
    with frame(p, xf(z=6)):
        dish(p, 52, 26, 10, rz=200, tilt=38)
        dish(p, 60, -2, 14, rz=160, tilt=30, R=8)
        dish(p, 48, -30, 8, rz=230, tilt=42, R=6)

    top = dome(p, -44, 30, 18)
    telescope(p, -44, 30, 16, rz=-30, elev=38)
    spire(p, -44, 30, 2.6, CROWN_TOP, fins=False, halo=True, z0=top - 0.5)
    for x, y in ((-30, -50), (-54, -20)):
        holo_pedestal(p, x, y)
    for y in (-60, -30, 30, 60):
        light_pillar(p, 17, y)
        light_pillar(p, -17, y)
    float_crystal(p, "SkyGlass", -66, -60, 22, 2.6, 6, 4.5)
    finish(p)
    return p


def build_armory():
    p = Piece("chunk_armory", "COMBAT | N + S SKYWAY -- the barracks yard")
    ypts = moved(chamfer_rect(60, 90, 20), -20, 0)
    island(p, ypts, "HullSlate")
    twin_keel(p, ypts, (-20, 40), (-20, -40), 22)
    floor_grid(p, ypts, "PaleAlloy", step=18, w=0.9)
    skyway_deck(p, -HALF, -90, -HALF + 0.4, -91)
    skyway_deck(p, 90, HALF, 91, HALF - 0.4)
    edge_ring(p, ypts, [("N", SKYWAY_W), ("S", SKYWAY_W), ("E", 12)], "parapet")

    torus(p, "AzureDim", 20, 0.35, -50, 20, 0.05, n=24)
    torus(p, "SunGold", 8, 0.3, -50, 20, 0.05, n=12)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        frustum(p, "PaleAlloy", 6, 0.6, 0.5, 0, 3.4, -50 + math.cos(a) * 22, 20 + math.sin(a) * 22)
    for y in (-66, -52, -38):
        target(p, -70, y, rz=90)
    for y in (-66, -30, 30, 66):
        weapon_rack(p, -30, y, rz=90)
    tower(p, -64, -70, 8, 38)
    banner_mast(p, -62, 68)
    for x, y in ((24, -60), (28, -56)):
        crate(p, x, y, 3.0, rz=x)
    for y in (-66, -20, 20, 66):
        brazier(p, 22, y)

    # the barracks islet, over a short bridge east
    bpts = moved(chamfer_rect(22, 52, 8), 82, 0)
    island(p, bpts)
    standard_keel(p, [(x - 82, y) for x, y in bpts]) if False else keel(
        p, bpts, [(-DECK_T + 0.5, 0.97, 0, "HullSlate"), (-16, 0.8, 0, "HullSlate"),
                  (-19, 0.81, 0, "AzureDim"), (-54, 0.0, 0, "DeepAlloy")], centre=(82, 0))
    bridge_x(p, 40, 60, 0, w=12)
    edge_ring(p, bpts, [("W", 12)], "parapet")
    barracks(p, 84, 24, lx=36, ly=16, rz=90)
    forge(p, 84, -30, rz=180)
    shield_rack(p, 70, -8, rz=90)
    shield_rack(p, 96, -8, rz=90)
    float_crystal(p, "SkyGlass", 84, -2, 26, 2.2, 5, 4)
    finish(p)
    return p


def build_vault_turn():
    p = Piece("chunk_vault_turn", "COMBAT | S + E SKYWAY -- the treasury, passed through on a turn")
    R = 66.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts)
    crystal_root_keel(p, pts, seed="vault roots", count=13)
    floor_grid(p, pts, "SunGold", step=12, w=0.5)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck_x(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("S", SKYWAY_W), ("E", SKYWAY_W)], "parapet")

    # the keep sits in the north-west; the path turns across its door
    kx, ky = -22, 30
    p.solid_box("vault keep", kx - 19, kx + 19, ky - 15, ky + 15, 0, 26)
    box_span(p, "PaleAlloy", kx - 18, kx + 18, ky - 14, ky + 14, 0, 1.5)
    box_span(p, "CitadelWhite", kx - 16, kx + 16, ky - 12, ky + 12, 1.5, 20)
    box_span(p, "PaleAlloy", kx - 17, kx + 17, ky - 13, ky + 13, 20, 21.5)
    box_span(p, "CitadelWhite", kx - 12, kx + 12, ky - 8, ky + 8, 21.5, 24)
    for sx in (-1, 1):
        box_span(p, "AzureDim", kx + sx * 16 - 0.2, kx + sx * 16 + 0.2, ky - 6, ky + 6, 5, 15)
    tower(p, kx - 16, ky - 12, 3.2, 22)
    tower(p, kx + 16, ky - 12, 3.2, 22)
    vault_door(p, kx, ky - 12, 10)
    spire(p, kx, ky + 2, 3.8, CROWN_TOP, fins=False, z0=24)
    for x, rz in ((-28, 10), (-20, -6), (-12, 4)):
        chest(p, x, 10, rz=rz)
    for x, y, r in ((-36, 6, 2.2), (-6, 8, 1.6)):
        frustum(p, "SunGold", 8, r, r * 0.3, 0, r * 0.9, x, y)
    crystal_cluster(p, -48, 44, seed=11, scale=1.2)
    crystal_cluster(p, 20, 44, seed=12)
    crystal_cluster(p, -44, -30, seed=13, scale=0.9)
    obelisk(p, 30, -30, h=16)
    for x, y in ((12, -12), (-14, -40), (40, 12)):
        brazier(p, x, y)
    float_crystal(p, "CitadelViolet", 40, 46, 24, 2.0, 4.5, 3.5)
    finish(p)
    return p


def build_spire_court():
    p = Piece("chunk_spire_court", "COMBAT (gate-court) | S SKYWAY, N ASCENT -- the Ascent Gate")
    h, c = 100.0, 24.0
    pts = chamfer_rect(h, h, c)
    island(p, pts)
    standard_keel(p, pts)
    border_band(p, pts, width=8.0)
    skyway_deck(p, -HALF, -h, -HALF + 0.4, -h - 1)
    ascent_deck(p, h, HALF)
    edge_ring(p, pts, [("S", SKYWAY_W), ("N", ASCENT_W)], "parapet")
    box_span(p, "AzureDim", -1.5, 1.5, -h, -20, 0, 0.12)
    box_span(p, "AzureDim", -1.5, 1.5, 20, 86, 0, 0.12)
    torus(p, "AzureDim", 22, 0.3, 0, 0, 0.05, n=24)

    p.solid("fountain", 0, 0, 16, 0, 24)
    frustum(p, "DeepAlloy", 12, 16, 16, 0, 1.2, 0, 0)
    frustum(p, "SkyGlass", 12, 14.5, 14.5, 1.2, 1.5, 0, 0)
    frustum(p, "PaleAlloy", 8, 3, 2, 1.5, 10, 0, 0)
    frustum(p, "SunGold", 8, 2, 5, 10, 11.5, 0, 0)
    crystal(p, "AzureNeon", 0, 0, 17, 2.2, 4.5, 3.5, n=6)
    torus(p, "AzureNeon", 5.5, 0.3, 0, 0, 17, n=16)
    torus(p, "AzureNeon", 7.5, 0.3, 0, 0, 21, n=16, rx=20)

    for sx in (-1, 1):
        for sy in (-1, 1):
            tower(p, sx * 76, sy * 76, 10, 52)
    spire(p, -42, 58, 7, CROWN_TOP, extra_halos=1)
    spire(p, 42, 58, 7, CROWN_TOP, extra_halos=1)
    spire(p, -58, -40, 5, 96, fins=False)
    spire(p, 58, -40, 5, 96, fins=False)
    gate(p, 0, 92, ASCENT_W, 58)
    banner(p, -30, 82)
    banner(p, 30, 82)
    for y in (-84, -56, -30, 30, 58):
        lamp(p, -16, y)
        lamp(p, 16, y)
    for x, y in ((-64, 14), (-64, -8), (64, 14), (64, -8), (-30, -74), (30, -74)):
        planter(p, x, y)
    bench(p, -32, 0, rz=90)
    bench(p, 32, 0, rz=90)
    holo_pedestal(p, -24, 78)
    holo_pedestal(p, 24, 78)
    float_crystal(p, "SkyGlass", -66, 58, 30, 2.8, 6, 4.5)
    float_crystal(p, "SkyGlass", 66, 58, 24, 2.4, 5, 4)
    finish(p)
    return p


def build_spire_court_b():
    p = Piece("chunk_spire_court_b", "COMBAT (gate-court, rare) | S SKYWAY, N ASCENT -- the Hall of Winds")
    pts = [(-60, -100), (60, -100), (96, -40), (96, 40), (60, 100), (-60, 100), (-96, 40), (-96, -40)]
    island(p, pts, "PaleAlloy")
    twin_keel(p, pts, (0, 44), (0, -44), 24)
    skyway_deck(p, -HALF, -100, -HALF + 0.4, -101)
    ascent_deck(p, 100, HALF)
    edge_ring(p, pts, [("S", SKYWAY_W), ("N", ASCENT_W)], "railing")

    # the raised nave between the colonnades, ramped at both ends
    npts = [(-30, -56), (30, -56), (30, 56), (-30, 56)]
    terrace(p, npts, 3.0, "CitadelWhite")
    with frame(p, xf(z=3)):
        floor_checker(p, npts, "PaleAlloy", tile=10, margin=2)
    ramp(p, 0, -72, 40, 16, 3.0, "N")
    ramp(p, 0, 72, 40, 16, 3.0, "S")
    colonnade(p, -44, -72, 54, 6)
    colonnade(p, 44, -72, 54, 6)
    for sx in (-1, 1):
        for y in (-46, 2, 50):
            banner(p, sx * 36, y, rz=90)
    with frame(p, xf(z=3)):
        p.solid("wind altar", 0, -24, 10.5, 0, 4)
        frustum(p, "PaleAlloy", 8, 10, 9, 0, 1.2, 0, -24)
        frustum(p, "DeepAlloy", 8, 6, 5, 1.2, 3.2, 0, -24)
        torus(p, "AzureNeon", 7.5, 0.3, 0, -24, 3.4, n=16)
        for k in range(3):
            a = math.radians(90 + 120 * k)
            float_crystal(p, "SkyGlass", 8 * math.cos(a), -24 + 8 * math.sin(a), 12 + 3 * k, 1.6, 4, 3)
    zc, RG = 8.0, 44.0
    a0 = math.degrees(math.asin(-zc / RG)) + 1.0
    p.solid_box("moon gate", -RG - 4, RG + 4, 86, 94, 0, zc + RG + 8)
    torus_arc(p, "CitadelWhite", RG, 3.0, 0, 90, zc, a0, 180 - a0, n=28, rx=90)
    torus_arc(p, "AzureNeon", RG - 3.4, 0.4, 0, 90, zc, a0 + 3, 177 - a0, n=28, rx=90)
    crystal(p, "SunGold", 0, 90, zc + RG + 5.2, 2.2, 4, 2.4)
    turbine(p, 74, -10, 132, 17, rz=0, needle_to=CROWN_TOP)
    turbine(p, -74, 20, 64, 12, rz=0)
    for y in (-86, 80):
        light_pillar(p, -24, y)
        light_pillar(p, 24, y)
    finish(p)
    return p


def build_side_lookout():
    p = Piece("chunk_side_lookout", "SIDE | one opening: south SKYWAY -- a lookout on a branch")
    R = 46.0
    pts = ngon(12, R)
    apo = R * math.cos(math.radians(15))
    island(p, pts)
    crystal_root_keel(p, pts, seed="lookout roots", count=9)
    floor_radial(p, 0, 6, 10, 38, 12, "PaleAlloy", width=1.4)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    edge_ring(p, pts, [("S", 24)], "railing")
    # the lookout faces north over the drop
    signal_mast(p, 0, 22)
    telescope(p, -14, 32, 2.5, rz=0, elev=20)
    frustum(p, "DeepAlloy", 6, 1.6, 1.0, 0, 2.5, -14, 32)
    telescope(p, 14, 32, 2.5, rz=0, elev=28)
    frustum(p, "DeepAlloy", 6, 1.6, 1.0, 0, 2.5, 14, 32)
    for x, rz in ((-10, 8), (-4, -6)):
        chest(p, x, 2, rz=rz)
    crystal_cluster(p, 26, 0, seed=21)
    crystal_cluster(p, -28, -4, seed=22, scale=0.8)
    bench(p, 0, -12)
    brazier(p, -20, -24)
    brazier(p, 20, -24)
    float_crystal(p, "SkyGlass", -24, 16, 34, 2.6, 6, 4.5)
    finish(p)
    return p


def build_boss_clearing():
    p = Piece("chunk_boss_clearing", "BOSS | one opening: south ASCENT -- the Crown Spire")
    R = 112.0
    ring = ngon(16, R)
    chord_y = -math.sqrt(R * R - (ASCENT_W / 2) ** 2)
    pts = [v for v in ring if v[1] > chord_y + 0.01]
    pts += [(-ASCENT_W / 2, chord_y), (ASCENT_W / 2, chord_y)]
    pts.sort(key=lambda v: math.atan2(v[1], v[0]))
    island(p, pts)
    engine_keel(p, pts, R=100)
    border_band(p, pts, width=8.0)
    ascent_deck(p, -HALF, chord_y)
    edge_ring(p, pts, [("S", ASCENT_W)], "parapet")
    torus(p, "AzureDim", 64, 0.35, 0, 0, 0.05, n=32)
    torus(p, "AzureDim", 34, 0.35, 0, 0, 0.05, n=24)
    for k in range(8):
        a = 22.5 + 45 * k
        box(p, "AzureDim", math.cos(math.radians(a)) * 49, math.sin(math.radians(a)) * 49, 0.05, 30, 0.8, 0.3, rz=a)

    frustum(p, "PaleAlloy", 8, 26, 24, 0, 1.5, 0, 70)
    frustum(p, "DeepAlloy", 8, 24, 23, 1.5, 3, 0, 70)
    spire(p, 0, 70, 13, CROWN_TOP, extra_halos=2)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        float_crystal(p, "SkyGlass", math.cos(a) * 30, 70 + math.sin(a) * 30, 52, 3.2, 7, 5)
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
        a = math.radians(90 * k + 45)
        float_crystal(p, "SkyGlass", math.cos(a) * 72, math.sin(a) * 72, 36, 5, 12, 10)
    finish(p)
    return p


# --------------------------------------------------------------------------
# Four more (pass 3, 2026-09-22): each brings a kind of thing no other piece
# has -- a broken floor, water, a roof, and living things.
# --------------------------------------------------------------------------


def scatter_floats(p, label, count, sampler, maker, tries=60):
    """Place up to `count` floating things, each only where validate() will
    accept it: probe the shape first, build only if the spot is free."""
    placed = 0
    for _ in range(count * tries):
        if placed >= count:
            break
        args = sampler(p.rng)
        shape = maker(Piece("_probe", ""), *args)
        if free_for_float(p, shape):
            maker(p, *args)
            p.floats.append((label, shape))
            placed += 1
    return placed


def bird(p, x, y, z, rz, mat):
    """A low-poly bird in flight: a glass body, two raised wings, a tail."""
    with frame(p, xf(x, y, z, rz)):
        crystal(p, mat, 0, 0, 0, 0.8, 1.2, 0.9, n=4, rz=45)
        frustum(p, mat, 4, 0.7, 0, 0, 2.2, M=xf(0.6, 0, 0, ry=90))
        frustum(p, "SunGold", 4, 0.3, 0, 0, 0.8, M=xf(2.7, 0, 0, ry=90))
        for s in (-1, 1):
            box(p, "PaleAlloy", 0, s * 1.9, 0.5, 1.6, 3.2, 0.15, rx=s * 24)
        box(p, mat, -1.8, 0, 0.1, 1.4, 1.1, 0.15)
    return ("cyl", x, y, 3.4, z - 1.2, z + 1.9)


def tome(p, x, y, z, rz):
    """A floating open book: gold covers in a shallow V, pale pages."""
    with frame(p, xf(x, y, z, rz)):
        for s in (-1, 1):
            box(p, "SunGold", s * 0.8, 0, 0, 1.7, 2.3, 0.15, ry=s * 14)
            box(p, "CitadelWhite", s * 0.78, 0, 0.14, 1.5, 2.1, 0.12, ry=s * 14)
        crystal(p, "AzureNeon", 0, 0, 1.3, 0.25, 0.4, 0.3)
    return ("cyl", x, y, 1.9, z - 0.8, z + 1.8)


def debris(p, x, y, z, rz, sz):
    """A fragment of the broken span, tumbling slowly in place."""
    with frame(p, xf(x, y, z, rz, rx=sz * 3)):
        box(p, "CitadelWhite", 0, 0, 0, sz, sz * 0.7, 1.2)
        box(p, "AzureDim", 0, 0, -0.75, sz * 0.9, sz * 0.62, 0.3)
        crystal(p, "HullSlate", 0, 0, -0.8, sz * 0.25, 0.2, sz * 0.6, n=4)
    return ("cyl", x, y, sz * 0.8, z - sz * 0.6 - 2, z + sz * 0.5 + 1)


def perch_tree(p, x, y):
    p.solid("perch tree", x, y, 4.2, 0, 16)
    frustum(p, "DeepAlloy", 6, 1.8, 1.6, 0, 0.8, x, y)
    frustum(p, "CitadelWhite", 6, 0.8, 0.5, 0.8, 11, x, y)
    box(p, "CitadelWhite", x + 1.6, y, 8, 3.4, 0.4, 0.4, ry=-30)
    orb(p, "Verdure", x, y, 12.5, 3.4)
    orb(p, "Verdure", x + 2.8, y + 0.6, 10.2, 2.0, n=6)


def birdbath(p, x, y):
    p.solid("birdbath", x, y, 3.4, 0, 4)
    frustum(p, "PaleAlloy", 8, 1.6, 0.8, 0, 2.6, x, y)
    frustum(p, "PaleAlloy", 8, 1.2, 3.2, 2.6, 3.4, x, y)
    frustum(p, "SkyGlass", 8, 2.9, 2.9, 3.4, 3.55, x, y)


def bookshelf(p, x, y0, y1, H=10.0, depth=2.4, face=1, seed=0):
    """A shelf wall along Y; `face` is the side the spines show on (+1 = +X)."""
    p.solid_box("bookshelf", x - depth / 2 - 0.3, x + depth / 2 + 0.3, y0, y1, 0, H + 0.6)
    L = y1 - y0
    yc = (y0 + y1) / 2
    box(p, "DeepAlloy", x, yc, H / 2, depth, L, H)
    box(p, "PaleAlloy", x, yc, H + 0.3, depth + 0.4, L + 0.4, 0.6)
    rng = random.Random(seed)
    rows = 3
    for r in range(rows):
        z = 0.8 + r * (H - 1.2) / rows
        box(p, "PaleAlloy", x + face * (depth / 2 + 0.05), yc, z, 0.2, L, 0.25)
        yy = y0 + 0.5
        while yy < y1 - 1.5:
            w = rng.uniform(4.0, 9.0)
            w = min(w, y1 - 0.5 - yy)
            hgt = rng.uniform(1.2, (H - 1.2) / rows - 0.3)
            mat = rng.choice(("CitadelViolet", "SkyGlass", "SunGold", "HullSlate", "Verdure"))
            box(p, mat, x + face * (depth / 2 + 0.12), yy + w / 2, z + 0.12 + hgt / 2, 0.35, w - 0.2, hgt)
            yy += w


def clock_tower(p, x, y, top=CROWN_TOP):
    p.solid("clock tower", x, y, 11, 0, top)
    box(p, "PaleAlloy", x, y, 1.5, 17, 17, 3)
    box(p, "CitadelWhite", x, y, 3 + 40, 13, 13, 80)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(p, "PaleAlloy", x + sx * 6.5, y + sy * 6.5, 43, 2, 2, 80)
    box(p, "PaleAlloy", x, y, 83.5, 15, 15, 1.5)
    for k in range(4):
        a = 90 * k
        r = math.radians(a)
        cx, cy = x + math.cos(r) * 6.6, y + math.sin(r) * 6.6
        with frame(p, xf(cx, cy, 68, a - 90)):
            frustum(p, "CitadelWhite", 12, 5, 5, 0, 0.5, M=xf(rx=90))
            torus(p, "SunGold", 5.1, 0.35, 0, -0.5, 0, n=16, rx=90)
            box(p, "DeepAlloy", 0.9, -0.7, 1.4, 0.4, 0.2, 3.4, ry=-30)
            box(p, "DeepAlloy", -1.1, -0.7, 0.2, 2.6, 0.2, 0.4, ry=10)
            crystal(p, "AzureNeon", 0, -0.8, 0, 0.4, 0.4, 0.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(p, "CitadelWhite", x + sx * 6, y + sy * 6, 91, 1.6, 1.6, 14)
    crystal(p, "AzureNeon", x, y, 91, 2.2, 3, 3, n=6)
    box(p, "PaleAlloy", x, y, 98.5, 15, 15, 1)
    frustum(p, "CitadelViolet", 4, 11, 0.8, 99, 120, x, y, rot=45)
    frustum(p, "SunGold", 4, 1.0, 1.0, 120, 122, x, y, rot=45)
    frustum(p, "PaleAlloy", 4, 0.8, 0, 122, top, x, y, rot=45)


def cascade_tower(p, x, y, top=CROWN_TOP):
    """Tiered bowls on a white column, each spilling a glass sheet of water
    into the one below."""
    p.solid("cascade tower", x, y, 16.5, 0, top)
    frustum(p, "DeepAlloy", 12, 16, 16, 0, 1.0, x, y)
    frustum(p, "SkyGlass", 12, 14.6, 14.6, 1.0, 1.3, x, y)
    frustum(p, "CitadelWhite", 8, 3.0, 1.8, 1.3, 128, x, y)
    tiers = [(24, 12.0), (50, 10.0), (76, 8.0), (100, 6.2), (122, 4.6)]
    for i, (z, r) in enumerate(tiers):
        frustum(p, "PaleAlloy", 12, r * 0.35, r, z - 2.4, z, x, y)
        frustum(p, "SunGold", 12, r, r, z - 0.4, z, x, y)
        frustum(p, "SkyGlass", 12, r * 0.9, r * 0.9, z, z + 0.2, x, y)
        lower = tiers[i - 1] if i else (1.3, 14.0)
        frustum(p, "SkyGlass", 12, lower[1] * 0.82, r * 0.96, lower[0] + 0.2, z - 2.4, x, y)
    crystal(p, "AzureNeon", x, y, 136, 3.0, top - 136, 8, n=6)


def light_fall(p, x, y0, y1, depth=58.0):
    """Water spilling off the east rim of a deck and falling out of sight."""
    box_span(p, "SkyGlass", x, x + 0.6, y0, y1, -depth, 0.1)
    box_span(p, "AzureDim", x + 0.6, x + 0.8, (y0 + y1) / 2 - 1, (y0 + y1) / 2 + 1, -depth, -1)
    panel(p, "SkyGlass", x - 7, (y0 + y1) / 2, 14, y1 - y0 - 1)


def build_path_shattered():
    p = Piece("chunk_path_shattered", "PATH | N + S SKYWAY -- a broken span, crossed on floating plates")
    skyway_deck(p, -HALF, -69, -HALF + 0.4, -69.4)
    skyway_deck(p, 69, HALF, 69.4, HALF - 0.4)
    for y in (-69, 69):
        light_pillar(p, -16, y - 4 * (1 if y > 0 else -1), h=6)
        light_pillar(p, 16, y - 4 * (1 if y > 0 else -1), h=6)
    rng = random.Random("shattered plates")
    for i, yc in enumerate((-59.5, -42.5, -25.5, -8.5, 8.5, 25.5, 42.5, 59.5)):
        xc = 3.0 if i % 2 else -3.0
        pts = moved(ngon(6, 9.0, rot=0), xc, yc)
        slab(p, "CitadelWhite" if i % 3 else "PaleAlloy", pts, -DECK_T, 0)
        p.slabs[-1] = (p.slabs[-1][0], -26.0, 1.0)
        frustum(p, "AzureDim", 6, 9.25, 9.25, -2.2, -0.8, xc, yc, rot=0)
        crystal(p, "HullSlate", xc, yc, -DECK_T, 5.0, 1.0, rng.uniform(10, 22), n=6, rz=rng.uniform(0, 60))
    scatter_floats(p, "span debris", 7,
                   lambda r: (r.uniform(-60, 60) * r.choice((-1, 1)) + r.choice((-38, 38)), r.uniform(-90, 90),
                              r.uniform(-22, 18), r.uniform(0, 90), r.uniform(4, 9)),
                   debris)

    # the Sundered Spire: its crown hangs, cut clean, above its own stump
    wpts = moved(ngon(6, 21, rot=0), -74, 18)
    island(p, wpts)
    crystal_root_keel(p, wpts, seed="sundered", centre=(-74, 18), count=6)
    edge_ring(p, wpts, [], "kerb")
    p.solid("spire stump", -74, 18, 9.5, 0, 72)
    frustum(p, "PaleAlloy", 8, 9, 8, 0, 4, -74, 18)
    frustum(p, "CitadelWhite", 8, 6, 4.8, 4, 64, -74, 18)
    frustum(p, "AzureDim", 8, 5.3, 5.3, 30, 32, -74, 18)
    for k, h in enumerate((6, 4, 7.5)):
        a = math.radians(40 + 120 * k)
        crystal(p, "CitadelWhite", -74 + math.cos(a) * 2.2, 18 + math.sin(a) * 2.2, 64, 2.2, h, 0.5, n=4)
    p.float_("spire crown", -74, 18, 9.0, 76, CROWN_TOP)
    torus(p, "AzureNeon", 7.5, 0.4, -74, 18, 78, n=16)
    for k, h in enumerate((5, 7, 4)):
        a = math.radians(100 + 120 * k)
        crystal(p, "CitadelWhite", -74 + math.cos(a) * 2, 18 + math.sin(a) * 2, 86, 2.1, 0.5, h, n=4)
    frustum(p, "CitadelWhite", 8, 4.6, 3.4, 86, 124, -74, 18)
    frustum(p, "SunGold", 8, 3.8, 3.8, 124, 126, -74, 18)
    frustum(p, "PaleAlloy", 8, 3.3, 0, 126, CROWN_TOP, -74, 18)

    # a broken arch on the east islet, its lintel adrift
    epts = moved(ngon(8, 16), 74, -44)
    island(p, epts)
    keel(p, epts, [(-DECK_T + 0.5, 0.95, 0, "HullSlate"), (-12, 0.7, 0, "AzureDim"),
                   (-34, 0.0, 0, "DeepAlloy")], centre=(74, -44))
    edge_ring(p, epts, [], "kerb")
    for sx in (-1, 1):
        p.solid("arch pylon", 74 + sx * 8, -44, 3.2, 0, 22)
        box(p, "CitadelWhite", 74 + sx * 8, -44, 10, 4, 4, 20)
        crystal(p, "CitadelWhite", 74 + sx * 8, -44, 20, 2.2, 2.5, 0.2, n=4)
    p.float_box("drifting lintel", 62, 86, -48, -40, 26, 33)
    box(p, "PaleAlloy", 74, -44, 29, 20, 4.4, 3.6, rz=8, ry=-6)
    crystal(p, "SunGold", 74, -44, 32, 1.2, 2.2, 0.8)
    finish(p)
    return p


def build_aether_springs():
    p = Piece("chunk_aether_springs", "COMBAT | S + W SKYWAY -- terraced pools, a left turn")
    pts = chamfer_rect(92, 92, 22)
    apo = 92.0
    island(p, pts)
    standard_keel(p, pts)
    floor_checker(p, pts, "SkyGlass", tile=12, margin=5, keep=lambda x, y: x < 0 or y < 0)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    with oriented(p, 90):
        skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("S", SKYWAY_W), ("W", SKYWAY_W), ("E", 70)], "kerb")
    for y0, y1 in ((-60, -46), (-8, 8), (40, 54)):
        light_fall(p, 92, y0, y1)

    # two terraces in the north-east, pools on each, spilling down
    ta = [(4, 12), (86, 12), (86, 64), (64, 86), (4, 86)]
    tb = [(30, 40), (80, 40), (80, 62), (62, 80), (30, 80)]
    terrace(p, ta, 3.0)
    terrace(p, tb, 6.0, "PaleAlloy")
    ramp(p, 40, -2, 14, 14, 3.0, "N")
    with frame(p, xf(z=3)):
        ramp(p, 18, 58, 12, 12, 3.0, "E")
        pool(p, 18, 38, 16, 24)
        for x, y in ((8, 80), (20, 80)):
            light_pillar(p, x, y, h=5)
    with frame(p, xf(z=6)):
        pool(p, 56, 60, 28, 22)
        bench(p, 70, 48, rz=0)
    box_span(p, "SkyGlass", 46, 66, 39.3, 39.8, 3.0, 6.3)
    box_span(p, "SkyGlass", 50, 70, 11.3, 11.8, 0.0, 3.3)
    pool(p, 60, 4, 18, 8)
    float_crystal(p, "SkyGlass", 56, 60, 22, 2.4, 5, 4)

    cascade_tower(p, 58, -46)
    for x, y in ((-30, -30), (-60, 30), (20, -70)):
        light_pillar(p, x, y)
    bench(p, -40, -60, rz=90)
    planter(p, -70, -70)
    crystal_cluster(p, -66, 60, seed=31)
    finish(p)
    return p


def build_archive():
    p = Piece("chunk_archive", "COMBAT | N + S SKYWAY -- a roofed hall of shelves")
    pts = chamfer_rect(70, 100, 16)
    island(p, pts, "PaleAlloy")
    stepped_keel(p, pts, steps=4)
    floor_checker(p, pts, "DeepAlloy", tile=8, margin=4, keep=lambda x, y: abs(x) > 22)
    panel(p, "CitadelViolet", 0, 0, 14, 196)
    for sx in (-1, 1):
        panel(p, "SunGold", sx * 7.6, 0, 1.0, 196, z=0.07)
    skyway_deck(p, -HALF, -100, -HALF + 0.4, -101)
    skyway_deck(p, 100, HALF, 101, HALF - 0.4)
    edge_ring(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)], "kerb")

    for sx in (-1, 1):
        for i, (y0, y1) in enumerate(((-84, -44), (-32, 8), (20, 60))):
            bookshelf(p, sx * 30, y0, y1, face=-sx, seed=10 * i + sx)
            bookshelf(p, sx * 54, y0 + 4, y1 - 4, H=8, face=-sx, seed=10 * i + sx + 5)
        for yy in (-38, 14):
            box(p, "DeepAlloy", sx * 41, yy, 1.3, 6, 2.6, 2.6)
            box(p, "PaleAlloy", sx * 41, yy, 2.7, 6.4, 3.0, 0.3)
            crystal(p, "AzureNeon", sx * 41, yy, 3.9, 0.4, 0.8, 0.3)
    # ribbed vaults over the aisle, springing from the shelf tops
    for y in (-72, -48, -24, 0, 24, 48):
        p.solid_box("vault rib", -30, 30, y - 1.6, y + 1.6, 9, 39)
        torus_arc(p, "CitadelWhite", 28, 1.1, 0, y, 10, 0, 180, n=16, rx=90)
        torus_arc(p, "AzureDim", 26.6, 0.3, 0, y, 10, 3, 177, n=16, rx=90)
    p.solid_box("ridge", -2, 2, -74, 50, 36, 40)
    box_span(p, "PaleAlloy", -0.8, 0.8, -73, 49, 37.2, 38.6)
    # the map table under the crossing
    p.solid("map table", 0, 0, 7.5, 0, 10)
    frustum(p, "DeepAlloy", 12, 5, 6.5, 0, 3.0, 0, 0)
    frustum(p, "AzureDim", 12, 6.5, 6.5, 3.0, 3.3, 0, 0)
    orb(p, "AzureNeon", 0, 0, 7.4, 1.8)
    torus(p, "SunGold", 2.8, 0.15, 0, 0, 7.4, n=12, rx=70)
    scatter_floats(p, "floating tome", 9,
                   lambda r: (r.uniform(-16, 16), r.uniform(-80, 60), r.uniform(14, 28), r.uniform(0, 360)),
                   tome)
    clock_tower(p, -52, 80)
    for x, y in ((-16, -92), (16, -92), (-16, 76), (16, 76)):
        brazier(p, x, y)
    finish(p)
    return p


def build_path_aviary():
    p = Piece("chunk_path_aviary", "PATH | N + S SKYWAY -- through a gilded birdcage")
    R = 62.0
    pts = ngon(8, R)
    apo = R * math.cos(math.radians(22.5))
    island(p, pts)
    crystal_root_keel(p, pts, seed="aviary roots", count=9)
    vines(p, pts, "aviary vines", 10)
    floor_checker(p, pts, "Verdure", tile=7, margin=4, keep=lambda x, y: abs(x) > 12)
    for y in range(-54, 55, 9):
        panel(p, "PaleAlloy", 0, y, 8, 6)
    skyway_deck(p, -HALF, -apo, -HALF + 0.4, -apo - 1)
    skyway_deck(p, apo, HALF, apo + 1, HALF - 0.4)
    edge_ring(p, pts, [("N", SKYWAY_W), ("S", SKYWAY_W)], "railing")

    # the cage: five meridian ribs (none lands on the path), two hoops, a crown
    RC = 50.0
    p.solid("cage crown", 0, 0, 8, 46, 56)
    for rz in (0, 30, 60, 120, 150):
        torus_arc(p, "PaleAlloy", RC, 0.9, 0, 0, 0, 0, 180, n=24, rx=90, rz=rz)
        for s in (-1, 1):
            a = math.radians(rz)
            frustum(p, "SunGold", 8, 2.0, 1.4, 0, 1.6, s * math.cos(a) * RC, s * math.sin(a) * RC)
    for z in (20.0, 38.0):
        torus(p, "PaleAlloy", math.sqrt(RC * RC - z * z), 0.6, 0, 0, z, n=32)
    torus(p, "SunGold", 6, 0.8, 0, 0, RC, n=16)
    spire(p, 0, 0, 3.4, CROWN_TOP, fins=False, halo=True, z0=RC)

    for k in range(4):
        a = math.radians(45 + 90 * k)
        perch_tree(p, math.cos(a) * 32, math.sin(a) * 32)
    birdbath(p, -34, 0)
    birdbath(p, 34, 0)
    for y in (-40, 40):
        bench(p, -24, y, rz=90)

    def inside_cage(r):
        z = r.uniform(12, 34)
        rmax = math.sqrt(RC * RC - z * z) - 6
        a, d = r.uniform(0, 2 * math.pi), r.uniform(10, rmax)
        return (math.cos(a) * d, math.sin(a) * d, z, r.uniform(0, 360),
                r.choice(("SkyGlass", "CitadelViolet", "SkyGlass", "PaleAlloy")))

    def outside_cage(r):
        a, d = r.uniform(0, 2 * math.pi), r.uniform(66, 104)
        return (math.cos(a) * d, math.sin(a) * d, r.uniform(10, 60), r.uniform(0, 360),
                r.choice(("SkyGlass", "CitadelViolet")))

    scatter_floats(p, "bird", 10, inside_cage, bird)
    scatter_floats(p, "bird", 5, outside_cage, bird)
    finish(p)
    return p


def finish(p):
    """Every piece ends here: beacons last (they fit round everything else),
    then the bounding-box pins."""
    corner_beacons(p)
    edge_pins(p)


BUILDERS = [
    # row 1: arrival and the straight connectives
    build_entry, build_path_straight, build_path_skyport, build_path_hoops,
    # row 2: more straights, each a different crossing
    build_path_shattered, build_path_aviary, build_crossroads, build_side_lookout,
    # row 3: the turns
    build_path_bend, build_path_bend_west, build_vault_turn, build_aether_springs,
    # row 4: the combat decks
    build_garden_terrace, build_observatory, build_armory, build_archive,
    # row 5: the arena approach and the arena
    build_spire_court, build_spire_court_b, build_boss_clearing,
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
    # Floor panels are single faces, which recalc cannot orient by volume.
    # They are decals on a deck: they face up, always.
    bm.faces.ensure_lookup_table()
    for i in p.up:
        face = bm.faces[i]
        face.normal_update()
        if face.normal.z < 0:
            face.normal_flip()
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
