# Ethereal Scape kit -- geometry core: palette, the Piece soup, and low-poly primitives.
#
# Every primitive appends explicit vertex/face lists. No bmesh index reading: the first pass
# of this kit lost every island floor to stale BMVert indices (2026-09-26).
import math
import random
import zlib

from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# Palette: the ORIGINAL scene's materials, read off aether_environment_refined.blend
# (sRGB 0-255). The first pass guessed pale values; these are the real ones.
# ---------------------------------------------------------------------------
PALETTE = {
    "AetherMintGrass": (79, 148, 115),
    "CloudWhite": (212, 224, 235),
    "Cloudstone": (107, 122, 140),
    "DeepTealLeaves": (20, 59, 51),
    "GoldenPath": (209, 184, 87),
    "IndigoLeaves": (31, 41, 92),
    "PaleGoldSoil": (189, 171, 82),
    "PortalGlow": (94, 46, 178),
    "SkyCrystal": (46, 168, 235),
    "SoftWood": (77, 56, 31),
    "TempleGold": (184, 133, 38),
    "TempleIvory": (194, 191, 158),
}
EMISSIVE = {"PortalGlow": 2.4, "SkyCrystal": 0.35}
MAT_ORDER = list(PALETTE)

KEEL_BOTTOM = -96.0
CROWN_TOP = 160.0
KIND_WIDTH = {"SPAN": 44.0, "COMMUNION": 64.0}
# Blender +Y is the layout's NORTH (-Z in game) under -Z Forward / Y Up -- the same
# authoring convention as Sky Citadel, whose export measured MeshYawOffset = 180.
DIRS = {"N": (0.0, 1.0), "S": (0.0, -1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0)}


def name_seed(name):
    return zlib.crc32(name.encode()) % 100000


# Geometry primitives: a face's TAG is the first function up the stack that is not one of these,
# so a clip report names the two builders involved (tree vs column), as Sky Citadel's does.
PRIMITIVES = {"add", "prism", "frustum", "box", "rod", "beam", "gem", "gem2", "blob", "decal", "decal_ring", "decal_strip",
              "wall", "<lambda>", "<genexpr>", "<listcomp>", "_isle"}


def caller_tag():
    import sys
    f = sys._getframe(2)
    while f is not None:
        if f.f_code.co_name not in PRIMITIVES:
            return f.f_code.co_name
        f = f.f_back
    return "?"


class Piece:
    """One chunk being built: a geometry soup plus the bookkeeping validation needs."""

    def __init__(self, pid, half, sockets):
        self.name = pid
        self.H = half                      # half footprint: 128, or bigger for entry / boss
        self.sockets = sockets             # [(dir, kind)]
        self.verts, self.faces, self.fmat = [], [], []
        self.ftag = []                     # per face: the builder that made it (clip reports)
        self.slabs = []                    # geometry_checks compatibility (decks are found by area)
        self.up = set()                    # single-sided decals: force +Z
        self.islands = []                  # (cx, cy, r, bottom_z, top_z) for float clearance
        self.corridors = []                # (ax, ay, bx, by, half_width): bridges and paths
        self.keepout = []                  # (x, y, r): every big feature's footprint; scatter never lands in one
        self.holes = []                    # (x, y, r): open drops in the cloud floor
        self.props = []                    # placed ambient props (convention 6)
        self.rng = random.Random(name_seed(pid))

    def add(self, verts, faces, mat, M=None):
        base = len(self.verts)
        if M is None:
            self.verts.extend(Vector(v) for v in verts)
        else:
            self.verts.extend(M @ Vector(v) for v in verts)
        self.faces.extend([base + i for i in f] for f in faces)
        self.fmat.extend([mat] * len(faces))
        self.ftag.extend([caller_tag()] * len(faces))
        return base

    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)

    def top(self):
        return max(v.z for v in self.verts) if self.verts else 0.0


def rot_z(a):
    return Matrix.Rotation(a, 4, "Z")


def xf(x=0.0, y=0.0, z=0.0, rz=0.0, rx=0.0, ry=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ \
        Matrix.Rotation(rx, 4, "X")


def _ccw(pts):
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    return pts if area >= 0 else list(reversed(pts))


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def prism(p, pts, z0, z1, top, side=None, bottom=None):
    """Vertical extrusion of a 2D outline (any simple polygon; fan-capped from its centroid)."""
    pts = _ccw(list(pts))
    n = len(pts)
    cx = sum(q[0] for q in pts) / n
    cy = sum(q[1] for q in pts) / n
    verts = [(x, y, z1) for x, y in pts] + [(x, y, z0) for x, y in pts] + [(cx, cy, z1), (cx, cy, z0)]
    ct, cb = 2 * n, 2 * n + 1
    p.add(verts, [[ct, i, (i + 1) % n] for i in range(n)], top)
    p.add(verts, [[cb, n + (i + 1) % n, n + i] for i in range(n)], bottom or side or top)
    p.add(verts, [[i, n + i, n + (i + 1) % n, (i + 1) % n] for i in range(n)], side or top)


def ring_pts(cx, cy, r, n, a0=0.0, sx=1.0, sy=1.0):
    return [(cx + r * sx * math.cos(a0 + 2 * math.pi * i / n), cy + r * sy * math.sin(a0 + 2 * math.pi * i / n))
            for i in range(n)]


def frustum(p, mat, cx, cy, z0, z1, r0, r1, n=8, a0=0.0, top_mat=None, bottom_mat=None, M=None):
    """n-gon frustum; r1 ~ 0 makes a cone with a true apex."""
    verts, faces = [], []
    b = [(cx + r0 * math.cos(a0 + 2 * math.pi * i / n), cy + r0 * math.sin(a0 + 2 * math.pi * i / n), z0) for i in range(n)]
    verts += b
    if r1 < 1e-3:
        verts.append((cx, cy, z1))
        apex = len(verts) - 1
        side = [[i, (i + 1) % n, apex] for i in range(n)]
        topf = []
    else:
        verts += [(cx + r1 * math.cos(a0 + 2 * math.pi * i / n), cy + r1 * math.sin(a0 + 2 * math.pi * i / n), z1)
                  for i in range(n)]
        side = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        topf = [[n + i for i in range(n)]]
    botf = [list(reversed(range(n)))]
    p.add(verts, side, mat, M)
    if topf:
        p.add(verts, topf, top_mat or mat, M)
    p.add(verts, botf, bottom_mat or mat, M)


def box(p, mat, cx, cy, cz, sx, sy, sz, rz=0.0, top=None, M=None):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    T = xf(cx, cy, cz, rz)
    if M is not None:
        T = M @ T
    p.add(v, [[3, 2, 1, 0], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat, T)
    p.add(v, [[4, 5, 6, 7]], top or mat, T)


def _frame(a, b):
    a, b = Vector(a), Vector(b)
    z = (b - a)
    L = z.length
    z = z.normalized()
    hint = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
    x = hint.cross(z).normalized()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = a
    return M, L


def rod(p, mat, a, b, r0, r1, n=6):
    """A frustum along an arbitrary segment (branches, roots, rails, shards)."""
    M, L = _frame(a, b)
    if L < 1e-4:
        return
    frustum(p, mat, 0, 0, 0, L, r0, r1, n=n, M=M)


def beam(p, mat, a, b, w, h, top=None):
    """A rectangular beam from a to b (planks, rails, lintels), level across its width."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-4:
        return
    yaw = math.atan2(d.y, d.x)
    pitch = math.atan2(d.z, math.hypot(d.x, d.y))
    c = (a + b) / 2
    M = xf(c.x, c.y, c.z, rz=yaw) @ Matrix.Rotation(-pitch, 4, "Y")
    box(p, mat, 0, 0, 0, L, w, h, top=top, M=M)


def gem(p, mat, cx, cy, cz, r, up, down, n=7, a0=0.0, sx=1.0, sy=1.0, top_mat=None):
    """A faceted crown: a belt ring with an apex above and below. Trees, crystals, orbs, clouds."""
    verts = [(cx + r * sx * math.cos(a0 + 2 * math.pi * i / n), cy + r * sy * math.sin(a0 + 2 * math.pi * i / n), cz)
             for i in range(n)]
    verts += [(cx, cy, cz + up), (cx, cy, cz - down)]
    t, b = n, n + 1
    p.add(verts, [[i, (i + 1) % n, t] for i in range(n)], top_mat or mat)
    p.add(verts, [[(i + 1) % n, i, b] for i in range(n)], mat)


def gem2(p, mat, cx, cy, cz, r, up, down, n=7, a0=0.0, belt=0.35, top_mat=None):
    """A two-belt crown (rounder, reads as foliage rather than crystal)."""
    r2 = r * 0.72
    h2 = up * belt
    verts = [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n), cz) for i in range(n)]
    verts += [(cx + r2 * math.cos(a0 + math.pi / n + 2 * math.pi * i / n), cy + r2 * math.sin(a0 + math.pi / n + 2 * math.pi * i / n),
               cz + h2) for i in range(n)]
    verts += [(cx, cy, cz + up), (cx, cy, cz - down)]
    t, b = 2 * n, 2 * n + 1
    faces_mid = []
    for i in range(n):
        j = (i + 1) % n
        faces_mid += [[i, j, n + i], [j, n + j, n + i]]
    p.add(verts, faces_mid, mat)
    p.add(verts, [[n + i, n + (i + 1) % n, t] for i in range(n)], top_mat or mat)
    p.add(verts, [[(i + 1) % n, i, b] for i in range(n)], mat)


def blob(p, mat, cx, cy, z, r, h, n=7, a0=0.0, sx=1.0, sy=1.0, below=None):
    """A rounded billow: a low dome of three rings (belly, shoulder, crown) and a soft cap -- the cloud
    shape. Wider than tall, so it reads as cloud, never as a spike."""
    below = r * 0.25 if below is None else below
    rings = [(1.0, 0.0), (0.86, 0.45), (0.52, 0.82)]
    verts = []
    for k, (rs, hs) in enumerate(rings):
        off = a0 + (math.pi / n) * k
        verts += [(cx + r * rs * sx * math.cos(off + 2 * math.pi * i / n), cy + r * rs * sy * math.sin(off + 2 * math.pi * i / n),
                   z + h * hs) for i in range(n)]
    verts += [(cx, cy, z + h), (cx, cy, z - below)]
    top, bot = 3 * n, 3 * n + 1
    faces = []
    for k in range(2):
        for i in range(n):
            j = (i + 1) % n
            a, b = k * n + i, k * n + j
            c_, d = (k + 1) * n + i, (k + 1) * n + j
            faces += [[a, b, c_], [b, d, c_]]
    faces += [[2 * n + i, 2 * n + (i + 1) % n, top] for i in range(n)]
    faces += [[(i + 1) % n, i, bot] for i in range(n)]
    p.add(verts, faces, mat)


def decal(p, mat, pts, z):
    """A flat, single-sided floor inlay lying on a floor at height z (faces up, walkable)."""
    pts = _ccw(list(pts))
    base = p.add([(x, y, z) for x, y in pts], [list(range(len(pts)))], mat)
    p.up.add(len(p.faces) - 1)
    return base


def decal_ring(p, mat, cx, cy, r0, r1, z, n=24, a0=0.0, a1=2 * math.pi):
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    steps = n
    verts = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        verts += [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z)]
    faces = []
    for i in range(steps):
        if full and i == steps - 1:
            faces.append([2 * i, 2 * i + 1, 1, 0])
        else:
            faces.append([2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2])
    base_f = len(p.faces)
    p.add(verts, faces, mat)
    for k in range(len(faces)):
        p.up.add(base_f + k)


def decal_strip(p, mat, a, b, w, z):
    a, b = Vector((a[0], a[1])), Vector((b[0], b[1]))
    d = b - a
    if d.length < 1e-4:
        return
    n = Vector((-d.y, d.x)).normalized() * (w / 2)
    decal(p, mat, [tuple(a - n), tuple(b - n), tuple(b + n), tuple(a + n)], z)
