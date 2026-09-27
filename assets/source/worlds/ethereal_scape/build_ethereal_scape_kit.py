# LUCKBOUND - Ethereal Scape 30-piece base chunk kit. FIRST PASS (2026-09-26),
# same status Verdant Valley's 30-piece kit started at: validated geometrically,
# not yet uploaded or walked in Studio. See docs/biomes/ETHEREAL_SCAPE.md for
# the schema this generates against (footprint, connection vocabulary, the
# piece table, the five-axis variety pattern, palette).
#
# Round, organic sky-temple islands above the cloud deck - mint grass and gold
# soil, ivory-and-gold temple architecture, sky crystal, soft portal glow.
# Every piece: 256 x 256 x 256 (footprint +-128, keel -96, crown +160), one
# mesh, <10,000 tris, flat shaded with baked vertex colour (CHUNK_AUTHORING.md).
#
# Run:
#   blender -b --factory-startup --python assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- --export --render
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "assets", "export", "worlds", "ethereal_scape")
RENDER_DIR = os.path.join(HERE, "renders")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DO_EXPORT = "--export" in ARGV
DO_RENDER = "--render" in ARGV

FOOTPRINT = 128.0          # half-extent: every piece is 256 x 256 in plan
KEEL_BOTTOM = -96.0
CROWN_TOP = 160.0
TRI_LIMIT = 10000
GRID_GAP = 320.0           # review-layout spacing; each piece is exported at the origin

# ---------------------------------------------------------------------------
# Palette - exactly the materials named in Content/Worlds/EtherealScape.luau's
# header, read off aether_environment_refined.blend. Nothing invented.
# ---------------------------------------------------------------------------
PALETTE = {
    "AetherMintGrass": (150, 214, 168),
    "PaleGoldSoil":    (214, 188, 132),
    "GoldenPath":      (232, 196, 110),
    "CloudWhite":      (238, 240, 244),
    "Cloudstone":      (198, 202, 212),
    "DeepTealLeaves":  (56, 122, 108),
    "IndigoLeaves":    (86, 92, 158),
    "TempleIvory":     (236, 230, 214),
    "TempleGold":      (222, 178, 96),
    "SkyCrystal":      (182, 224, 236),
    "PortalGlow":      (196, 236, 255),
    "Underside":       (70, 78, 92),   # not in the palette table: keel/underside only, never player-facing
}
EMISSIVE = {"PortalGlow"}
MAT_ORDER = list(PALETTE.keys())


def make_materials():
    mats = {}
    for name, rgb in PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        col = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1)
        b.inputs["Base Color"].default_value = col
        b.inputs["Roughness"].default_value = 0.55
        b.inputs["Metallic"].default_value = 0.0
        if name in EMISSIVE:
            b.inputs["Emission Color"].default_value = col
            b.inputs["Emission Strength"].default_value = 2.2
        mats[name] = m
    return mats


# ---------------------------------------------------------------------------
# Piece: one chunk's geometry soup. One mesh per piece (CHUNK_AUTHORING.md #5).
# ---------------------------------------------------------------------------
class Piece:
    def __init__(self, name, sockets):
        self.name = name
        self.sockets = sockets      # [(id, kind, facing_deg, width)]
        self.verts = []
        self.faces = []
        self.fmat = []
        self.up = set()             # single-sided floor decals: force +Z

    def add(self, verts, faces, matname, M=Matrix()):
        base = len(self.verts)
        self.verts.extend(M @ Vector(v) for v in verts)
        self.faces.extend([base + i for i in f] for f in faces)
        self.fmat.extend([matname] * len(faces))
        return base

    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)


def name_seed(name):
    """Deterministic per-piece seed. Python's hash() is randomised per process,
    so seeding from it made every rebuild differ."""
    import zlib
    return zlib.crc32(name.encode()) % 10000


def TR(loc=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0):
    return Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X") @ Matrix.Rotation(ry, 4, "Y")


# ---------------------------------------------------------------------------
# Primitives - each returns nothing, appends straight into the Piece.
# ---------------------------------------------------------------------------
def box(p, mat, loc, size, rz=0.0, bev=0.0):
    """size = (length, width, height) full extents."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    if bev > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, offset_type="OFFSET", segments=2, profile=0.5, affect="EDGES")
    bm.verts.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    p.add(verts, faces, mat, TR(loc, rz))


def island(p, cx, cy, r, top_z, thickness, floor_mat, side_mat, sides=28, seed=0, wobble=0.06):
    """A round, slightly organic deck: flat floor cap, sloped side wall, capped underside."""
    # Built as explicit lists, not bmesh: reading .index off freshly created
    # BMVerts returns stale indices, which silently turned every floor into a
    # degenerate face that mesh.validate() then deleted (2026-09-26).
    rng = random.Random(seed)
    verts = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        rr = r * (1.0 + rng.uniform(-wobble, wobble))
        dx, dy = rr * math.cos(a), rr * math.sin(a)
        verts.append((cx + dx, cy + dy, top_z))                       # top ring: index 2i
        verts.append((cx + dx * 0.94, cy + dy * 0.94, top_z - thickness))  # bottom ring: 2i + 1
    top = [2 * i for i in range(sides)]
    bot = [2 * i + 1 for i in reversed(range(sides))]
    sides_f = [[2 * i, 2 * ((i + 1) % sides), 2 * ((i + 1) % sides) + 1, 2 * i + 1] for i in range(sides)]
    base = len(p.verts)
    p.verts.extend(Vector(v) for v in verts)
    for f, m in ([top, floor_mat], [bot, "Underside"]):
        p.faces.append([base + i for i in f]); p.fmat.append(m)
    p.up.add(len(p.faces) - 2)                                        # the floor faces up, always
    for f in sides_f:
        p.faces.append([base + i for i in f]); p.fmat.append(side_mat)


def cone(p, mat, loc, r0, r1, height, sides=12, rz=0.0, rx=0.0, cap_bottom=True, cap_top=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=sides, radius1=r0, radius2=r1, depth=height)
    bm.verts.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    p.add(verts, faces, mat, TR((loc[0], loc[1], loc[2] + height / 2), rz, rx))


def sphere(p, mat, loc, r, segs=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(6, segs // 2), radius=r)
    bm.verts.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    p.add(verts, faces, mat, TR(loc))


def tube(p, mat, a, b, r0, r1, sides=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    n = d.length
    if n < 1e-6:
        return
    z = d.normalized()
    hint = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((1, 0, 0))
    x = hint.cross(z).normalized()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=sides, radius1=r0, radius2=r1, depth=n)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, n / 2))
    bm.verts.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    p.add(verts, faces, mat, M)


# ---------------------------------------------------------------------------
# Facing / socket geometry
# ---------------------------------------------------------------------------
FACING = {"N": (0.0, (0.0, -1.0)), "S": (180.0, (0.0, 1.0)), "E": (90.0, (1.0, 0.0)), "W": (270.0, (-1.0, 0.0))}
KIND_WIDTH = {"SPAN": 44.0, "COMMUNION": 64.0}


def pier(p, cardinal, kind, floor_mat, side_mat, inner_r, top_z=0.0, thickness=10.0):
    """A straight causeway stub from just inside the island's rim (so it
    fuses, not gaps) out to EXACTLY the tile edge, so every opening arrives
    level and at the kind's fixed width with nothing overhanging the tile."""
    facing, (dx, dy) = FACING[cardinal]
    width = KIND_WIDTH[kind]
    near, far = inner_r * 0.6, FOOTPRINT
    length = far - near
    cx, cy = dx * (near + far) / 2, dy * (near + far) / 2
    rz = math.atan2(dy, dx)
    box(p, floor_mat, (cx, cy, top_z - 0.6), (length, width, 1.2), rz=rz)
    for s in (-1, 1):
        ex, ey = -math.sin(rz) * s * width / 2, math.cos(rz) * s * width / 2
        box(p, side_mat, (cx + ex, cy + ey, top_z - thickness * 0.4), (length, 1.2, thickness * 0.8), rz=rz)


def edge_pins(p):
    """Four 0.3-stud pins at the midpoint of each tile edge, keel line
    (z = -96): pins the footprint exactly regardless of the organic outline,
    same trick Sky Citadel's kit uses."""
    for cx, cy in ((FOOTPRINT, 0), (-FOOTPRINT, 0), (0, FOOTPRINT), (0, -FOOTPRINT)):
        box(p, "Underside", (cx, cy, KEEL_BOTTOM), (0.3, 0.3, 0.3))


# ---------------------------------------------------------------------------
# Axis builders: EDGE trim, KEEL underside, LANDMARK (pins the crown)
# ---------------------------------------------------------------------------
def edge_trim(p, style, cx, cy, r, skip_deg, seed=0, count=16):
    if style == "none":
        return
    rng = random.Random(seed + 1)
    for i in range(count):
        a = 2 * math.pi * i / count
        deg = math.degrees(a)
        if any(min((deg - s) % 360, (s - deg) % 360) < 22 for s in skip_deg):
            continue
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        rz = a + math.pi / 2
        if style == "curb":
            box(p, "TempleIvory", (x, y, -0.3), (3.0, 3.0, 1.6), rz=rz)
            sphere(p, "PortalGlow", (x, y, 0.6), 0.35)
        elif style == "trellis":
            box(p, "TempleGold", (x, y, 1.6), (0.5, 0.5, 3.2), rz=rz)
            if i % 2 == 0:
                box(p, "IndigoLeaves", (x, y, 3.2), (2.4, 0.6, 0.8), rz=rz)
        elif style == "balustrade":
            box(p, "TempleIvory", (x, y, 1.7), (0.7, 0.7, 3.4), rz=rz)
            box(p, "TempleGold", (x, y, 3.4), (3.0, 0.5, 0.4), rz=rz)
        elif style == "hedge":
            box(p, "DeepTealLeaves", (x, y, 1.2), (3.4, 2.2, 2.4), rz=rz, bev=0.3)


def keel(p, style, cx, cy, r, seed=0):
    rng = random.Random(seed + 2)
    if style == "cloud_wisp":
        return
    if style == "root_tangle":
        for i in range(6):
            a = 2 * math.pi * i / 6
            x0, y0 = cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a)
            x1, y1 = cx + r * 1.05 * math.cos(a + 0.3), cy + r * 1.05 * math.sin(a + 0.3)
            tube(p, "DeepTealLeaves", (x0, y0, -6), (x1, y1, -22 - rng.uniform(0, 10)), 2.4, 0.6)
    elif style == "crystal_stalactite":
        for i in range(5):
            a = 2 * math.pi * i / 5 + rng.uniform(-0.2, 0.2)
            x, y = cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a)
            cone(p, "SkyCrystal", (x, y, -8), 2.2, 0.1, 14 + rng.uniform(0, 10), sides=5, rz=rng.uniform(0, 6), rx=0.25)
    elif style == "temple_blocks":
        for i in range(4):
            a = 2 * math.pi * i / 4 + math.pi / 4
            x, y = cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a)
            box(p, "TempleIvory", (x, y, -10), (10, 10, 16), rz=a)
    elif style == "mote_ring":
        for i in range(10):
            a = 2 * math.pi * i / 10
            x, y = cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a)
            sphere(p, "PortalGlow", (x, y, -14 - 3 * math.sin(a * 3)), 0.9)


def landmark(p, style, cx, cy, base_z, seed=0):
    """Every landmark reaches exactly CROWN_TOP: it pins the top of the box."""
    rng = random.Random(seed + 3)
    if style == "waystone":
        h = CROWN_TOP - base_z
        cone(p, "TempleIvory", (cx, cy, base_z), 4.5, 3.2, h * 0.85, sides=6)
        box(p, "PortalGlow", (cx, cy, base_z + h * 0.5), (0.4, 4.6, 3.0), bev=0.05)
        cone(p, "TempleGold", (cx, cy, base_z + h * 0.85), 3.2, 0.4, h * 0.15, sides=6)
    elif style == "temple_finial":
        h = CROWN_TOP - base_z
        box(p, "TempleIvory", (cx, cy, base_z), (10, 10, h * 0.3), bev=0.4)
        cone(p, "CloudWhite", (cx, cy, base_z + h * 0.3), 5.5, 2.0, h * 0.45, sides=8)
        cone(p, "TempleGold", (cx, cy, base_z + h * 0.75), 2.0, 0.1, h * 0.25, sides=8)
    elif style == "portal_arch":
        h = CROWN_TOP - base_z
        for s in (-1, 1):
            tube(p, "TempleIvory", (cx + s * 9, cy, base_z), (cx + s * 9, cy, base_z + h * 0.72), 2.4, 2.0)
            tube(p, "TempleIvory", (cx + s * 9, cy, base_z + h * 0.72), (cx + s * 3, cy, base_z + h), 2.0, 1.6)
        box(p, "PortalGlow", (cx, cy, base_z + h * 0.55), (1.0, 12, h * 0.55), bev=0.1)
        box(p, "TempleGold", (cx, cy, base_z + h * 0.98), (14, 3.0, 2.0))
    elif style == "sky_tree":
        h = CROWN_TOP - base_z
        tube(p, "TempleIvory", (cx, cy, base_z), (cx, cy, base_z + h * 0.55), 4.0, 2.4)
        for i in range(9):
            a = rng.uniform(0, 6.28)
            rr = rng.uniform(6, 16)
            z = base_z + h * (0.55 + 0.4 * rng.random())
            sphere(p, "DeepTealLeaves" if i % 2 else "IndigoLeaves", (cx + rr * math.cos(a), cy + rr * math.sin(a), z), rng.uniform(4, 7))
    elif style == "crystal_obelisk":
        h = CROWN_TOP - base_z
        cone(p, "SkyCrystal", (cx, cy, base_z), 6, 0.2, h, sides=5, rz=rng.uniform(0, 6))
        for i in range(3):
            a = rng.uniform(0, 6.28)
            cone(p, "SkyCrystal", (cx + 5 * math.cos(a), cy + 5 * math.sin(a), base_z), 2.4, 0.1, h * rng.uniform(0.3, 0.6), sides=5, rz=a)
    elif style == "shrine_bell":
        h = CROWN_TOP - base_z
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            tube(p, "TempleIvory", (cx + 6 * math.cos(a), cy + 6 * math.sin(a), base_z), (cx + 6 * math.cos(a), cy + 6 * math.sin(a), base_z + h * 0.75), 1.6, 1.3)
        cone(p, "TempleGold", (cx, cy, base_z + h * 0.75), 8, 7, h * 0.1, sides=4)
        cone(p, "TempleGold", (cx, cy, base_z + h * 0.4), 3.5, 2.0, 5, sides=8)
        cone(p, "CloudWhite", (cx, cy, base_z + h * 0.85), 7, 0.4, h * 0.15, sides=4)
    elif style == "aether_beacon":
        h = CROWN_TOP - base_z
        tube(p, "TempleIvory", (cx, cy, base_z), (cx, cy, base_z + h * 0.8), 3.0, 1.2)
        sphere(p, "PortalGlow", (cx, cy, base_z + h * 0.92), 6.5)
    # Every landmark pins the crown exactly, whatever its own shape's random
    # variation did: a small accent, imperceptible against the main form.
    sphere(p, "PortalGlow", (cx, cy, CROWN_TOP - 0.25), 0.5)


# ---------------------------------------------------------------------------
# Piece assembly
# ---------------------------------------------------------------------------
def build_island_piece(p, spec):
    seed = name_seed(p.name)
    r = spec.get("radius", 100)
    cx, cy = spec.get("centre", (0, 0))
    edge_pins(p)
    island(p, cx, cy, r, 0.0, spec.get("thickness", 12), spec["floor"], "Cloudstone", seed=seed)
    skip = [FACING[cardinal][0] for cardinal, kind in spec["sockets"]]
    edge_trim(p, spec["edge"], cx, cy, r * 1.02, skip, seed=seed)
    keel(p, spec["keel"], cx, cy, r, seed=seed)
    for cardinal, kind in spec["sockets"]:
        pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=r)
    if spec.get("landmark"):
        lcx, lcy = spec.get("landmark_at", (cx, cy))
        landmark(p, spec["landmark"], lcx, lcy, 0.0, seed=seed)
    if spec.get("landmark2"):
        landmark(p, spec["landmark2"], cx + spec.get("landmark2_off", (24, -24))[0], cy + spec.get("landmark2_off", (24, -24))[1], 0.0, seed=seed + 500)
    for extra in spec.get("waystones_extra", []):
        cone(p, "TempleIvory", (cx + extra[0], cy + extra[1], 0), 3.5, 2.6, 20, sides=6)


def build_archipelago_piece(p, spec):
    seed = name_seed(p.name)
    edge_pins(p)
    islets = spec["islets"]  # list of (cx, cy, r)
    for i, (icx, icy, ir) in enumerate(islets):
        island(p, icx, icy, ir, 0.0, spec.get("thickness", 10), spec["floor"], "Cloudstone", seed=seed + i)
        edge_trim(p, spec["edge"], icx, icy, ir * 1.02, [], seed=seed + i, count=10)
        keel(p, spec["keel"], icx, icy, ir, seed=seed + i)
    for (a, b) in spec["bridges"]:
        (ax, ay, ar), (bx, by, br) = islets[a], islets[b]
        d = Vector((bx - ax, by - ay))
        rz = math.atan2(d.y, d.x)
        length = d.length - (ar + br) * 0.75
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        box(p, spec["floor"], (cx, cy, -0.5), (length, 10, 1.0), rz=rz)
        for s in (-1, 1):
            ex, ey = -math.sin(rz) * s * 5, math.cos(rz) * s * 5
            box(p, "Cloudstone", (cx + ex, cy + ey, -1.5), (length, 0.8, 2.0), rz=rz)
    for cardinal, kind in spec["sockets"]:
        end = islets[spec["socket_islet"][cardinal]]
        pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=end[2])
    if spec.get("landmark"):
        icx, icy, _ir = islets[spec.get("landmark_islet", 0)]
        landmark(p, spec["landmark"], icx, icy, 0.0, seed=seed)
        if spec.get("landmark_dup"):
            icx2, icy2, _ir2 = islets[spec.get("landmark_islet2", -1)]
            landmark(p, spec["landmark"], icx2, icy2, 0.0, seed=seed + 7)


def build_span_piece(p, spec):
    """A bare span or stepping-stones: no big deck, just the crossing itself."""
    seed = name_seed(p.name)
    edge_pins(p)
    kind_a, kind_b = spec["sockets"][0][1], spec["sockets"][1][1]
    if spec["mode"] == "arch":
        box(p, spec["floor"], (0, 0, -0.6), (KIND_WIDTH[kind_a] + 4, FOOTPRINT * 2 - 20, 1.2))
        for s in (-1, 1):
            box(p, "Cloudstone", (s * (KIND_WIDTH[kind_a] / 2 + 1), 0, -2), (2, FOOTPRINT * 2 - 20, 3))
        landmark(p, spec["landmark"], 0, 0, -6, seed=seed)
    else:  # stepping
        n = spec.get("steps", 5)
        for i in range(n):
            t = (i + 0.5) / n
            y = -100 + t * 200
            wob = 6 * math.sin(i * 2.1)
            r = 16 + 2 * (i % 3)
            island(p, wob, y, r, -1.0 - 1.5 * (i % 2), 6, spec["floor"], "Cloudstone", seed=seed + i, sides=14)
        landmark(p, spec["landmark"], FOOTPRINT * 0.4, 0, 0, seed=seed)
    for cardinal, kind in spec["sockets"]:
        pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=FOOTPRINT - 24)


def build_convergence(p, spec):
    seed = name_seed(p.name)
    edge_pins(p)
    r = 108
    island(p, 0, 0, r, 0.0, 14, spec["floor"], "Cloudstone", seed=seed, sides=32)
    edge_trim(p, spec["edge"], 0, 0, r * 1.02, [FACING[c][0] for c, _k in spec["sockets"]], seed=seed, count=20)
    keel(p, spec["keel"], 0, 0, r, seed=seed)
    for cardinal, kind in spec["sockets"]:
        pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=r)
    landmark(p, spec["landmark"], 0, 0, 0, seed=seed)


def build_boss_arena(p, spec):
    seed = name_seed(p.name)
    edge_pins(p)
    r = 130
    island(p, 0, 0, r, 0.0, 16, spec["floor"], "Cloudstone", seed=seed, sides=36, wobble=0.02)
    edge_trim(p, "balustrade", 0, 0, r * 1.01, [FACING["S"][0]], seed=seed, count=28)
    keel(p, spec["keel"], 0, 0, r, seed=seed)
    for cardinal, kind in spec["sockets"]:
        pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=r)
    landmark(p, spec["landmark"], 0, 0, 0, seed=seed)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        cone(p, "TempleIvory", (r * 0.72 * math.cos(a), r * 0.72 * math.sin(a), 0), 4, 3, 24, sides=8)


def build_cap_span(p, spec):
    """A one-socket ending: the causeway simply stops, mid-construction."""
    seed = name_seed(p.name)
    edge_pins(p)
    cardinal, kind = spec["sockets"][0]
    pier(p, cardinal, kind, spec["floor"], "Cloudstone", inner_r=FOOTPRINT - 60)
    rng = random.Random(seed)
    for i in range(5):
        x = rng.uniform(-30, 30)
        y = -FOOTPRINT * 0.3 - i * 14
        z = -2 - i * 3
        island(p, x, y, 10 - i, z, 4, spec["floor"], "Cloudstone", seed=seed + i, sides=10)
    cone(p, "SkyCrystal", (10, -FOOTPRINT * 0.35, -20), 3, 0.2, 18, sides=5, rz=1.1, rx=0.6)
    landmark(p, spec.get("landmark", "crystal_obelisk"), 0, FOOTPRINT * 0.55, 0, seed=seed)


def build_cap_shrine(p, spec):
    build_island_piece(p, spec)
    door_c = (0, -spec.get("radius", 80) * 0.75)
    box(p, "TempleGold", (door_c[0], door_c[1], 9), (10, 2.0, 18), bev=0.2)
    box(p, "PortalGlow", (door_c[0], door_c[1], 9), (0.6, 2.2, 16))


BUILDERS = {
    "island": build_island_piece,
    "archipelago": build_archipelago_piece,
    "span": build_span_piece,
    "convergence": build_convergence,
    "boss": build_boss_arena,
    "cap_span": build_cap_span,
    "cap_shrine": build_cap_shrine,
}

# ---------------------------------------------------------------------------
# The 30-piece kit. Matches docs/biomes/ETHEREAL_SCAPE.md's piece table.
# ---------------------------------------------------------------------------
PIECES = [
    dict(id="ES_ENTRY", role="ENTRY", kind="island", radius=90,
         sockets=[("N", "SPAN")], floor="PaleGoldSoil", edge="curb", keel="temple_blocks", landmark="waystone"),

    dict(id="ES_PATH_STRAIGHT", role="PATH", kind="archipelago",
         islets=[(0, -55, 55), (0, 55, 55)], bridges=[(0, 1)],
         sockets=[("N", "SPAN"), ("S", "SPAN")], socket_islet={"N": 0, "S": 1},
         floor="AetherMintGrass", edge="balustrade", keel="root_tangle", landmark="sky_tree", landmark_islet=0),

    dict(id="ES_PATH_ARCWAY", role="PATH", kind="span", mode="arch",
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="Cloudstone", landmark="portal_arch"),

    dict(id="ES_PATH_STEPPING", role="PATH", kind="span", mode="stepping", steps=6,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="Cloudstone", landmark="crystal_obelisk"),

    dict(id="ES_PATH_BEND_EAST", role="PATH", kind="island", radius=95,
         sockets=[("S", "SPAN"), ("E", "SPAN")], floor="GoldenPath", edge="hedge", keel="root_tangle", landmark="waystone"),

    dict(id="ES_PATH_BEND_WEST", role="PATH", kind="island", radius=95,
         sockets=[("S", "SPAN"), ("W", "SPAN")], floor="IndigoLeaves", edge="trellis", keel="cloud_wisp", landmark="shrine_bell"),

    dict(id="ES_PATH_LANTERN_ROW", role="PATH", kind="archipelago",
         islets=[(0, -80, 42), (0, 0, 42), (0, 80, 42)], bridges=[(0, 1), (1, 2)],
         sockets=[("N", "SPAN"), ("S", "SPAN")], socket_islet={"N": 0, "S": 2},
         floor="PaleGoldSoil", edge="curb", keel="temple_blocks", landmark="portal_arch", landmark_islet=1),

    dict(id="ES_CONVERGENCE", role="PATH", kind="convergence",
         sockets=[("N", "SPAN"), ("S", "SPAN"), ("E", "SPAN"), ("W", "SPAN")],
         floor="IndigoLeaves", edge="balustrade", keel="mote_ring", landmark="aether_beacon"),

    dict(id="ES_PATH_ORCHARD", role="PATH", kind="island", radius=100,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="IndigoLeaves", edge="hedge", keel="root_tangle", landmark="sky_tree"),

    dict(id="ES_MEADOW_BLOOM", role="COMBAT", kind="island", radius=112,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="AetherMintGrass", edge="none", keel="cloud_wisp", landmark="waystone"),

    dict(id="ES_MEADOW_TERRACE", role="COMBAT", kind="island", radius=116,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="AetherMintGrass", edge="curb", keel="temple_blocks", landmark="sky_tree"),

    dict(id="ES_CRYSTAL_GROVE", role="COMBAT", kind="island", radius=100,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="Cloudstone", edge="none", keel="crystal_stalactite", landmark="crystal_obelisk"),

    dict(id="ES_WAYSTONE_RING", role="COMBAT", kind="island", radius=104,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="GoldenPath", edge="curb", keel="temple_blocks",
         landmark="waystone", waystones_extra=[(42, 40), (-42, 40), (0, -52)]),

    dict(id="ES_CLOUDSTONE_YARD", role="COMBAT", kind="island", radius=104,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="Cloudstone", edge="balustrade", keel="temple_blocks", landmark="shrine_bell"),

    dict(id="ES_HANGING_GARDEN", role="COMBAT", kind="archipelago",
         islets=[(0, -50, 60), (0, 50, 50)], bridges=[(0, 1)],
         sockets=[("N", "SPAN"), ("S", "SPAN")], socket_islet={"N": 0, "S": 1},
         floor="IndigoLeaves", edge="trellis", keel="root_tangle", landmark="sky_tree", landmark_islet=0),

    dict(id="ES_SHRINE_COURT", role="COMBAT", kind="island", radius=98,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="TempleIvory", edge="balustrade", keel="temple_blocks", landmark="shrine_bell"),

    dict(id="ES_AETHER_FALLS", role="COMBAT", kind="island", radius=106,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="PortalGlow", edge="curb", keel="crystal_stalactite", landmark="portal_arch"),

    dict(id="ES_SKY_ORCHARD", role="COMBAT", kind="island", radius=116,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="IndigoLeaves", edge="hedge", keel="root_tangle",
         landmark="sky_tree", landmark2="sky_tree", landmark2_off=(30, -30)),

    dict(id="ES_MIRROR_POOL", role="COMBAT", kind="island", radius=100,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="TempleIvory", edge="none", keel="cloud_wisp", landmark="aether_beacon"),

    dict(id="ES_RELIQUARY_COURT", role="COMBAT", kind="island", radius=104,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="TempleIvory", edge="balustrade", keel="temple_blocks", landmark="portal_arch"),

    dict(id="ES_STARFIELD_TERRACE", role="COMBAT", kind="island", radius=104,
         sockets=[("N", "SPAN"), ("S", "SPAN")], floor="IndigoLeaves", edge="curb", keel="mote_ring", landmark="crystal_obelisk"),

    dict(id="ES_TEMPLE_GATE_A", role="COMBAT", kind="island", radius=112,
         sockets=[("S", "SPAN"), ("N", "COMMUNION")], floor="GoldenPath", edge="balustrade", keel="temple_blocks",
         landmark="waystone", waystones_extra=[(34, 10), (-34, 10)]),

    dict(id="ES_TEMPLE_GATE_B", role="COMBAT", kind="island", radius=115,
         sockets=[("S", "SPAN"), ("N", "COMMUNION")], floor="GoldenPath", edge="balustrade", keel="temple_blocks",
         landmark="portal_arch"),

    dict(id="ES_SIDE_OVERLOOK", role="SIDE", kind="island", radius=68,
         sockets=[("S", "SPAN")], floor="Cloudstone", edge="balustrade", keel="cloud_wisp", landmark="waystone"),

    dict(id="ES_SIDE_HERMITAGE", role="SIDE", kind="island", radius=68,
         sockets=[("S", "SPAN")], floor="IndigoLeaves", edge="hedge", keel="root_tangle", landmark="shrine_bell"),

    dict(id="ES_SIDE_TREASURY", role="SIDE", kind="island", radius=68,
         sockets=[("S", "SPAN")], floor="TempleIvory", edge="curb", keel="temple_blocks", landmark="crystal_obelisk"),

    dict(id="ES_CAP_UNFINISHED_SPAN", role="CAP", kind="cap_span",
         sockets=[("S", "SPAN")], floor="Cloudstone"),

    dict(id="ES_CAP_OVERLOOK", role="CAP", kind="island", radius=70,
         sockets=[("S", "SPAN")], floor="Cloudstone", edge="balustrade", keel="temple_blocks", landmark="aether_beacon"),

    dict(id="ES_CAP_SEALED_SHRINE", role="CAP", kind="cap_shrine", radius=80,
         sockets=[("S", "SPAN")], floor="TempleIvory", edge="balustrade", keel="temple_blocks", landmark="shrine_bell"),

    dict(id="ES_SANCTUM", role="BOSS", kind="boss",
         sockets=[("S", "COMMUNION")], floor="GoldenPath", keel="temple_blocks", landmark="temple_finial"),
]

assert len(PIECES) == 30, f"expected 30 pieces, got {len(PIECES)}"


# ---------------------------------------------------------------------------
# Finalise: mesh, flat shading, baked vertex colour (CHUNK_AUTHORING.md).
# ---------------------------------------------------------------------------
def to_object(p, mats, collection):
    mesh = bpy.data.meshes.get(p.name)
    if mesh:
        bpy.data.meshes.remove(mesh)
    mesh = bpy.data.meshes.new(p.name)
    mesh.from_pydata([tuple(v) for v in p.verts], [], p.faces)
    for name in MAT_ORDER:
        mesh.materials.append(mats[name])
    mesh.validate(verbose=False)
    dropped = len(p.faces) - len(mesh.polygons)
    for poly, mname in zip(mesh.polygons, p.fmat):
        poly.material_index = MAT_ORDER.index(mname)
        poly.use_smooth = False

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    if len(bm.faces) == len(p.faces):          # validate() dropped nothing, so indices still line up
        for i in p.up:
            f = bm.faces[i]
            f.normal_update()
            if f.normal.z < 0:
                f.normal_flip()
    bm.to_mesh(mesh)
    bm.free()

    col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in mesh.polygons:
        rgb = PALETTE[MAT_ORDER[poly.material_index]]
        c = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
        for li in poly.loop_indices:
            col.data[li].color_srgb = c
    mesh.color_attributes.active_color = col
    mesh.update()

    obj = bpy.data.objects.new(p.name, mesh)
    obj["kit"] = "ETHEREAL_SCAPE"
    collection.objects.link(obj)
    return obj, dropped


# Minimum walkable floor (sq studs) per build kind. Spans and caps are narrow by
# design; everything else is a real island and must have one.
MIN_WALK = {"span": 3000.0, "cap_span": 2000.0, "archipelago": 8000.0, "island": 10000.0,
            "convergence": 20000.0, "boss": 30000.0, "cap_shrine": 10000.0}


def validate_piece(p, obj, spec, dropped):
    fails = []
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs, ys, zs = [v.x for v in verts], [v.y for v in verts], [v.z for v in verts]
    if not verts:
        return [f"{p.name}: no geometry"]
    if abs(min(xs) + FOOTPRINT) > 1.0 or abs(max(xs) - FOOTPRINT) > 1.0:
        fails.append(f"footprint X {min(xs):.1f}..{max(xs):.1f}, want +-{FOOTPRINT}")
    if abs(min(ys) + FOOTPRINT) > 1.0 or abs(max(ys) - FOOTPRINT) > 1.0:
        fails.append(f"footprint Y {min(ys):.1f}..{max(ys):.1f}, want +-{FOOTPRINT}")
    if abs(min(zs) - KEEL_BOTTOM) > 1.0:
        fails.append(f"keel bottom {min(zs):.1f}, want {KEEL_BOTTOM}")
    if abs(max(zs) - CROWN_TOP) > 1.0:
        fails.append(f"crown top {max(zs):.1f}, want {CROWN_TOP}")
    tris = p.tri_count()
    if tris >= TRI_LIMIT:
        fails.append(f"{tris} tris >= {TRI_LIMIT}")
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    if abs(cx) > 2.0 or abs(cy) > 2.0:
        fails.append(f"bbox centre ({cx:.2f},{cy:.2f}) not at origin")
    # THE CHECK THAT WAS MISSING: the pins alone satisfy every bbox rule above,
    # so a piece with no floor at all used to PASS. Measure the walkable area:
    # up-facing faces at the walk plane (z ~ 0, stepping stones sit a stud or two lower).
    me = obj.data
    walk = sum(poly.area for poly in me.polygons if poly.normal.z > 0.9 and -4.0 < poly.center.z < 0.5)
    need = MIN_WALK.get(spec["kind"], 8000.0)
    if walk < need:
        fails.append(f"walkable floor {walk:.0f} sq studs < {need:.0f}")
    if dropped:
        fails.append(f"mesh.validate() removed {dropped} degenerate face(s) -- geometry bug")
    return fails


# ---------------------------------------------------------------------------
# Boss arena is 320 x 256 (per the schema doc), so its footprint pins differ.
# ---------------------------------------------------------------------------
def footprint_for(spec):
    return 160.0 if spec["role"] == "BOSS" else FOOTPRINT


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    mats = make_materials()
    coll = bpy.context.scene.collection

    results = []
    cols = 6
    for idx, spec in enumerate(PIECES):
        global FOOTPRINT
        FOOTPRINT = footprint_for(spec)
        p = Piece(spec["id"], spec["sockets"])
        BUILDERS[spec["kind"]](p, spec)
        obj, dropped = to_object(p, mats, coll)
        fails = validate_piece(p, obj, spec, dropped)
        row, col = divmod(idx, cols)
        obj.location = (col * GRID_GAP, row * GRID_GAP, 0)
        tris = p.tri_count()
        walk = sum(poly.area for poly in obj.data.polygons if poly.normal.z > 0.9 and -4.0 < poly.center.z < 0.5)
        results.append((spec["id"], spec["role"], tris, fails, walk))
        FOOTPRINT = 128.0

    print("\n=== ETHEREAL SCAPE KIT ===")
    n_fail = 0
    for name, role, tris, fails, walk in results:
        status = "PASS" if not fails else "FAIL"
        if status == "FAIL":
            n_fail += 1
        print(f"PIECE {name:26s} {role:8s} {tris:5d} tris  floor {walk:7.0f} sq studs  {status}" + (f"  :: {'; '.join(fails)}" if fails else ""))
    print(f"=== {len(results) - n_fail}/{len(results)} PASS ===")

    if DO_EXPORT:
        export_all(coll, mats)
    if DO_RENDER:
        render_overview()

    blend_path = os.path.join(HERE, "ethereal_scape_kit.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("SAVED", blend_path)
    return n_fail


def export_all(coll, mats):
    for obj in list(coll.objects):
        saved_loc = obj.location.copy()
        obj.location = (0, 0, 0)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        path = os.path.join(OUT_DIR, f"chunk_{obj.name.lower()}.fbx")
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True, apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
            object_types={"MESH"}, use_mesh_modifiers=True, add_leaf_bones=False,
            bake_anim=False,
        )
        obj.location = saved_loc
    print(f"EXPORTED {len(coll.objects)} FBX to {OUT_DIR}")


def render_overview():
    import mathutils
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1200
    scene.view_settings.view_transform = "Standard"
    n = len(PIECES)
    cols = 6
    rows = -(-n // cols)
    cx, cy = (cols - 1) * GRID_GAP / 2, (rows - 1) * GRID_GAP / 2
    cam_data = bpy.data.cameras.new("ReviewCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(cols * GRID_GAP, rows * GRID_GAP * 1.6) * 1.05
    cam_data.clip_start = 1.0
    cam_data.clip_end = 20000.0
    cam = bpy.data.objects.new("ReviewCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (cx, cy - rows * GRID_GAP * 0.9, rows * GRID_GAP * 1.05)
    direction = mathutils.Vector((0, rows * GRID_GAP * 0.9, -rows * GRID_GAP * 1.05))
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.0
    sun_data.color = (1.0, 0.98, 0.92)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.context.scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new("W") if scene.world is None else scene.world
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.55, 0.68, 0.86, 1)
        bg.inputs[1].default_value = 1.1
    try:
        scene.eevee.use_bloom = True
    except AttributeError:
        pass
    out_path = os.path.join(RENDER_DIR, "kit_overview.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out_path)


if __name__ == "__main__":
    n_fail = main()
    if DO_EXPORT and n_fail:
        raise SystemExit(f"{n_fail} piece(s) failed validation; export completed anyway for inspection")
