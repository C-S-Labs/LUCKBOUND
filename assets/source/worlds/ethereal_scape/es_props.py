# Ethereal Scape kit -- the ATMOSPHERE: ambient props (CHUNK_AUTHORING.md convention 6).
#
# Everything that drifts, hovers or flies is a prop, never part of a chunk's mesh: one library
# mesh per kind, a placement per copy. This world's set is its own -- no birds, no halos, no
# hoops (Sky Citadel's) -- chosen for a cloudscape above the weather:
#   drifting cloud puffs (Float), sky lanterns rising over the clearings (Float), hovering
#   sky-crystal shards (Hover), satellite islets high above (Float), and skyrays -- manta-like
#   gliders roaming the whole map high above every crown (Glide).
# Every placement is proven clear of the piece's REAL mesh (BVH), >= 4 studs inside the tile,
# and clear of every other prop. A skyray is placed like the rest, then flies the whole map (Glide).
import math

from mathutils import Matrix, Vector

import random

from es_geometry import Piece, blob, frustum, gem, gem2, prism, ring_pts, rod

EDGE_MARGIN = 4.0

# kind -> (animation class, detail tier)
KINDS = {
    "prop_es_cloud_a": ("Float", 1),
    "prop_es_cloud_b": ("Float", 1),
    # the surround (owner 2026-09-27: the baked cloudbank "looks too unnatural" -- clouds are props now, so
    # they drift, and every BACKDROP piece arranges them its own way)
    "prop_es_cumulus_a": ("Float", 1),
    "prop_es_cumulus_b": ("Float", 1),
    "prop_es_cumulus_c": ("Float", 1),
    "prop_es_lantern": ("Float", 2),
    "prop_es_shard": ("Hover", 2),
    "prop_es_isle_grove": ("Float", 1),
    "prop_es_isle_crystal": ("Float", 1),
    "prop_es_isle_ruin": ("Float", 1),
    # Glide (owner 2026-09-27): skyrays roam the WHOLE map above every crown, not their own chunk
    "prop_es_skyray": ("Glide", 2),
    # variety for the air (owner 2026-09-27: "a few more props ... there are a LOT of floating island bits")
    "prop_es_petals": ("Float", 2),      # a loose swirl of blossom petals drifting over the meadows
    "prop_es_lotus": ("Hover", 2),       # a floating aether lotus, glowing heart on a dark pad
    "prop_es_kite": ("Sway", 2),         # a pilgrim's prayer kite, ribbons trailing
}


def _isle(p, r, top_mat="AetherMintGrass"):
    pts = ring_pts(0, 0, r, 9, a0=0.3)
    prism(p, pts, -1.5, 0, top_mat)
    prism(p, [(x * 1.07, y * 1.07) for x, y in pts], -3.2, -1.0, "TempleGold")
    verts = [(x * 1.05, y * 1.05, -3.2) for x, y in pts] + [(0.1 * r, -0.05 * r, -r * 1.4)]
    p.add(verts, [[(i + 1) % 9, i, 9] for i in range(9)], "Cloudstone")


def _cloud(p, seed, w, d, h, towers=3, anvil=False):
    """A natural cloud: a flattened base of wide billows along an ellipse (w x d), then towers of
    rounder billows heaped on it, each smaller and a little off-centre from the one below -- lumpy,
    never stacked like stones. `anvil` spreads the top out flat, the cumulonimbus shape."""
    rng = random.Random(seed)
    for k in range(max(5, int(w / 9))):
        a = rng.uniform(0, 6.28)
        u = rng.uniform(0, 1) ** 0.6
        x, y = math.cos(a) * w / 2 * u * 0.8, math.sin(a) * d / 2 * u * 0.8
        r = rng.uniform(0.16, 0.26) * w * (1.1 - 0.5 * u)
        blob(p, "CloudWhite", x, y, 0, r, r * rng.uniform(0.35, 0.5), n=9, sx=rng.uniform(1.0, 1.4),
             a0=rng.uniform(0, 6.28), below=r * 0.08)
    for t in range(towers):
        tx, ty = rng.uniform(-w, w) * 0.22, rng.uniform(-d, d) * 0.22
        r = rng.uniform(0.26, 0.34) * min(w, h * 1.4)
        z = r * 0.15
        while z < h - r * 0.7 and r > 3:
            # a tier is a CLUSTER of overlapping billows round the tower's axis -- they merge into one
            # soft mass instead of reading as stones stacked on stones
            for _ in range(rng.randint(3, 5)):
                a = rng.uniform(0, 6.28)
                off = r * rng.uniform(0.25, 0.7)
                blob(p, "CloudWhite", tx + math.cos(a) * off, ty + math.sin(a) * off, z + rng.uniform(-0.15, 0.15) * r,
                     r * rng.uniform(0.6, 0.9), r * rng.uniform(0.55, 0.8), n=10, a0=a, below=r * 0.15)
            z += r * rng.uniform(0.3, 0.4)
            r *= rng.uniform(0.84, 0.92)
            tx += rng.uniform(-r, r) * 0.35
            ty += rng.uniform(-r, r) * 0.35
        if anvil:
            for _ in range(6):
                a = rng.uniform(0, 6.28)
                R = rng.uniform(0.15, 0.4) * w
                rr = rng.uniform(0.18, 0.25) * w
                blob(p, "CloudWhite", tx + math.cos(a) * R, ty + math.sin(a) * R, z - rr * 0.2, rr, rr * 0.3, n=9,
                     sx=1.3, a0=a, below=rr * 0.05)


def _skyray(p):
    """A manta, nose +Y (owner 2026-09-27: "the underside looks under detailed, players will not be
    able to tell what they are" -- they are seen from BELOW, so the belly carries the read).
    A lofted body: 11 stations across the span, each a chord from the leading edge's swept curve to
    the trailing edge's, domed on the back and flatter underneath. Back indigo with a crystal ridge;
    belly pale with the manta's five pairs of gill slits, a wide mouth between two curled cephalic
    horns, a glowing spot pattern and glowing wingtips; a long whip tail with a small dorsal fin."""
    span, n = 8.0, 11
    top, bot = [], []
    for i in range(n):
        u = -1 + 2 * i / (n - 1)
        x = u * span
        au = abs(u)
        lead = 3.4 * (1 - au ** 1.6) - 1.4 * au          # swept leading edge
        trail = -3.2 * (1 - au) ** 0.8 - 0.3 * au        # the trailing edge sweeps back to the body
        if au > 0.95:
            trail = lead - 0.4                            # a pointed tip
        th = 1.1 * (1 - au) ** 1.3 + 0.08
        # the wings arch: tips curl slightly down, the body highest
        droop = -0.9 * au ** 2
        for j, v in enumerate((0.0, 0.3, 0.65, 1.0)):     # chordwise stations, leading to trailing
            y = lead + (trail - lead) * v
            bump = math.sin(math.pi * min(1.0, 0.15 + v * 0.85))
            top.append((x, y, droop + th * bump))
            bot.append((x, y, droop - th * 0.45 * bump))
    m = 4
    ft, fb = [], []
    for i in range(n - 1):
        for j in range(m - 1):
            a, b, c, d = i * m + j, (i + 1) * m + j, (i + 1) * m + j + 1, i * m + j + 1
            ft.append([a, b, c, d])
            fb.append([d, c, b, a])
    # seal the leading and trailing edges between back and belly
    off = len(top)
    edge = []
    for i in range(n - 1):
        a, b = i * m, (i + 1) * m
        edge.append([b, a, off + a, off + b])
        a, b = i * m + m - 1, (i + 1) * m + m - 1
        edge.append([a, b, off + b, off + a])
    for side in (0, n - 1):
        for j in range(m - 1):
            a, b = side * m + j, side * m + j + 1
            edge.append([a, b, off + b, off + a] if side == 0 else [b, a, off + a, off + b])
    p.add(top, ft, "IndigoLeaves")
    p.add(bot, fb, "CloudWhite")
    p.add(top + bot, edge, "IndigoLeaves")
    under = -0.5                                          # just under the belly at the body's centre line
    # gill slits: five pairs curving across the belly behind the mouth
    for k in range(5):
        yy = 1.2 - k * 0.55
        for sx in (-1, 1):
            rod(p, "Cloudstone", (sx * 1.0, yy, under - 0.02), (sx * 1.8, yy - 0.25, under + 0.05), 0.09, 0.09, n=4)
    # the mouth: a wide dark slot at the front of the belly, lipped in pale gold
    frustum(p, "Cloudstone", 0, 2.75, under - 0.05, under + 0.25, 0.9, 0.9, n=6)
    rod(p, "TempleGold", (-1.0, 2.95, under + 0.05), (1.0, 2.95, under + 0.05), 0.12, 0.12, n=4)
    # cephalic horns: two curled lobes either side of the mouth
    for sx in (-1, 1):
        rod(p, "IndigoLeaves", (sx * 1.2, 2.9, 0.1), (sx * 1.5, 4.3, -0.35), 0.35, 0.12, n=5)
        rod(p, "IndigoLeaves", (sx * 1.5, 4.3, -0.35), (sx * 1.15, 4.8, -0.75), 0.12, 0.05, n=4)
        gem(p, "PortalGlow", sx * 1.55, 2.2, 0.55, 0.28, 0.2, 0.2, n=5)              # eyes, on the head's flanks
    # a glowing spot pattern on the belly and glowing wingtips -- the read from below
    for sx in (-1, 1):
        for (ex, ey) in ((2.6, 0.6), (3.6, -0.4), (4.6, 0.2), (3.0, -1.4)):
            u = ex / span
            gem(p, "PortalGlow", sx * ex, ey, -0.9 * u * u - 0.35, 0.3, 0.05, 0.12, n=5)
        gem(p, "PortalGlow", sx * span * 0.93, -1.2, -0.85, 0.35, 0.15, 0.15, n=5)
    # the crystal ridge along the spine
    for k in range(4):
        gem(p, "SkyCrystal", 0, 1.6 - k * 1.1, 1.05 - k * 0.12, 0.3 - k * 0.04, 0.4, 0.1, n=4)
    # pelvic fins and the whip tail with its little dorsal fin
    for sx in (-1, 1):
        p.add([(sx * 0.5, -2.6, 0.1), (sx * 1.6, -3.6, -0.1), (sx * 0.4, -3.4, 0.0)], [[0, 1, 2] if sx > 0 else [0, 2, 1]],
              "IndigoLeaves")
    rod(p, "IndigoLeaves", (0, -2.8, 0.25), (0, -7.0, 0.1), 0.35, 0.14, n=5)
    rod(p, "IndigoLeaves", (0, -7.0, 0.1), (0, -11.0, -0.3), 0.14, 0.03, n=4)
    p.add([(0, -3.2, 0.5), (0, -4.6, 0.3), (0, -3.6, 1.3)], [[0, 1, 2]], "IndigoLeaves")


def build_kind(kind):
    """Each library mesh, built in its own frame. Returns (verts, faces, mats)."""
    p = Piece(kind, 0, [])
    if kind == "prop_es_cloud_a":                       # a small fair-weather puff
        _cloud(p, 11, 26, 18, 12, towers=1)
    elif kind == "prop_es_cloud_b":                     # a flat wisp
        _cloud(p, 12, 38, 16, 6, towers=0)
    elif kind == "prop_es_cumulus_a":                   # towering cumulus
        _cloud(p, 21, 64, 52, 78, towers=3)
    elif kind == "prop_es_cumulus_b":                   # a long low shelf
        _cloud(p, 22, 120, 44, 24, towers=4)
    elif kind == "prop_es_cumulus_c":                   # an anvil
        _cloud(p, 23, 76, 60, 86, towers=1, anvil=True)
    elif kind == "prop_es_lantern":
        frustum(p, "TempleGold", 0, 0, -1.4, 1.2, 0.9, 1.25, n=6)
        gem(p, "PortalGlow", 0, 0, 0, 0.75, 0.9, 0.9, n=6)
        frustum(p, "TempleGold", 0, 0, 1.2, 1.7, 1.25, 0.2, n=6)
        rod(p, "TempleGold", (0, 0, -1.4), (0, 0, -2.6), 0.12, 0.05, n=4)
    elif kind == "prop_es_shard":
        gem(p, "SkyCrystal", 0, 0, 0, 1.2, 4.5, 2.5, n=5)
    elif kind == "prop_es_isle_grove":
        _isle(p, 12)
        rod(p, "SoftWood", (2, 1, 0), (2, 1, 5), 0.8, 0.5, n=5)
        gem2(p, "DeepTealLeaves", 2, 1, 6, 4.5, 6, 2, n=7)
        gem2(p, "IndigoLeaves", -5, -2, 3, 3, 4, 1.4, n=6)
    elif kind == "prop_es_isle_crystal":
        _isle(p, 9, "Cloudstone")
        for a, L in ((0, 9), (2.1, 6), (4.2, 7)):
            rod(p, "SkyCrystal", (math.cos(a) * 1.2, math.sin(a) * 1.2, -0.5),
                (math.cos(a) * 3.2, math.sin(a) * 3.2, L), 1.3, 0.0, n=5)
    elif kind == "prop_es_isle_ruin":
        _isle(p, 10)
        for s in (-1, 1):
            p_ = p
            from es_geometry import box
            box(p_, "TempleIvory", s * 4, 0, 3.5, 1.8, 1.8, 7)
        from es_geometry import box
        box(p, "TempleIvory", 0, 0, 7.6, 10, 2.2, 1.4)
        box(p, "TempleGold", 0, 0, 8.6, 2, 2.4, 0.8)
    elif kind == "prop_es_skyray":
        _skyray(p)
    elif kind == "prop_es_petals":
        rng = random.Random(31)
        mats = ("TempleGold", "CloudWhite", "PortalGlow", "TempleGold", "SkyCrystal")
        for k in range(22):
            a = k * 0.55
            r = 1.2 + k * 0.28
            gem(p, mats[k % len(mats)], math.cos(a) * r, math.sin(a) * r, math.sin(k * 0.9) * 1.4 + k * 0.08,
                rng.uniform(0.35, 0.6), 0.08, 0.08, n=4, a0=rng.uniform(0, 3))
    elif kind == "prop_es_lotus":
        # never a wisp: AETHER_WISP is an enemy, so floating light must not read as one
        for ring, (n_, r_, lift, mat) in enumerate(((8, 2.4, 0.2, "CloudWhite"), (6, 1.5, 0.7, "TempleGold"))):
            for k in range(n_):
                a = k * 2 * math.pi / n_ + ring * 0.3
                rod(p, mat, (math.cos(a) * 0.4, math.sin(a) * 0.4, lift), (math.cos(a) * r_, math.sin(a) * r_, lift + 1.1),
                    0.5, 0.05, n=4)
        gem(p, "PortalGlow", 0, 0, 0.9, 0.6, 0.7, 0.3, n=6)
        gem(p, "IndigoLeaves", 0, 0, 0.1, 2.0, 0.1, 0.35, n=8)                # the pad beneath
    elif kind == "prop_es_kite":
        from es_geometry import box
        p.add([(0, 0, 3.2), (1.8, 0, 0.4), (0, 0, -2.6), (-1.8, 0, 0.4)], [[0, 1, 2, 3], [3, 2, 1, 0]], "CloudWhite")
        box(p, "TempleGold", 0, 0.08, 0.3, 0.15, 0.15, 5.8)
        box(p, "TempleGold", 0, 0.08, 0.4, 3.6, 0.15, 0.15)
        gem(p, "PortalGlow", 0, 0.12, 0.4, 0.5, 0.1, 0.1, n=4)
        for k, (dx, mat) in enumerate(((-0.3, "PortalGlow"), (0.3, "TempleGold"))):
            prev = (0, 0, -2.6)
            for j in range(1, 5):
                q = (dx * j + math.sin(j * 1.3 + k) * 0.5, 0.2 * j, -2.6 - j * 1.4)
                rod(p, mat, prev, q, 0.14, 0.12, n=3)
                prev = q
    else:
        raise KeyError(kind)
    # recentre on the box centre: the game scales and places the mesh by its box
    mn = Vector((min(q.x for q in p.verts), min(q.y for q in p.verts), min(q.z for q in p.verts)))
    mx = Vector((max(q.x for q in p.verts), max(q.y for q in p.verts), max(q.z for q in p.verts)))
    c = (mn + mx) / 2
    return [q - c for q in p.verts], p.faces, p.fmat, mx - mn


LIBRARY = {}


def library():
    if not LIBRARY:
        for k in KINDS:
            LIBRARY[k] = build_kind(k)
    return LIBRARY


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
def _clear(bvh, pos, radius, gap=1.5):
    hit = bvh.find_nearest(Vector(pos), radius + gap)
    return hit[0] is None


def place_all(p, bvh, spec):
    """Dress one piece's air. Counts follow the piece: lanterns over shrines and gates, shards
    over crystal pieces, isles and skyrays everywhere."""
    lib = library()
    rng = p.rng
    H = p.H
    tags = set(spec.get("tags", []))
    if "backdrop" in tags:           # a BACKDROP piece arranges its own clouds (es_pieces.cloud_props)
        return
    placed = []   # (x, y, z, r)

    def ok(x, y, z, r):
        if abs(x) + r > H - EDGE_MARGIN or abs(y) + r > H - EDGE_MARGIN:
            return False
        if any(math.dist((x, y, z), q[:3]) < r + q[3] + 2 for q in placed):
            return False
        return _clear(bvh, (x, y, z), r)

    def put(kind, x, y, z, scale, yaw):
        size = lib[kind][3] * scale
        r = size.length / 2
        placed.append((x, y, z, r))
        p.props.append(dict(kind=kind, pos=Vector((x, y, z)), yaw=yaw, scale=scale, size=size))

    def scatter(kind, n, zr, sr, region=None, tries=60, outer=False):
        got = 0
        for _ in range(n * tries):
            if got >= n:
                break
            scale = rng.uniform(*sr)
            size = lib[kind][3] * scale
            r = size.length / 2
            if region:
                cx, cy, rr = region
                a, d = rng.uniform(0, 6.28), rr * math.sqrt(rng.random())
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
            else:
                x, y = rng.uniform(-H, H), rng.uniform(-H, H)
            if outer and max(abs(x), abs(y)) < H * 0.55:
                continue
            z = rng.uniform(*zr)
            if ok(x, y, z, r):
                put(kind, x, y, z, scale, rng.uniform(0, 6.28))
                got += 1
        return got

    big = H > 150
    # clouds ride high, well over head height (low ones hung over the paths like rocks)
    scatter("prop_es_cloud_a", 3 if big else 2, (70, 115), (0.9, 1.3))
    scatter("prop_es_cloud_b", 2 if big else 1, (80, 125), (0.9, 1.3))
    # satellite isles live in the outer sky of the tile, never over its middle
    # thinned (owner 2026-09-27: "a LOT of floating island bits"); petals, lotuses and kites fill the air instead
    for k in ("prop_es_isle_grove", "prop_es_isle_crystal", "prop_es_isle_ruin"):
        if rng.random() < (0.55 if big else 0.3):
            scatter(k, 1, (100, 150), (0.9, 1.4), outer=True)
    lanterns = 3
    if tags & {"shrine", "gate-court", "arrival", "arena", "crossroads", "fork"}:
        lanterns = 9 if big else 7
    scatter("prop_es_lantern", lanterns, (16, 48), (1.0, 1.4), region=(0, 0, H * 0.7))
    if tags & {"crystal", "falls"} or "CRYSTAL_WARDEN" in spec.get("enemies", []):
        scatter("prop_es_shard", 6, (10, 34), (0.9, 1.6))
    # petals drift low over the meadows, lotuses hang above head height, kites fly high
    scatter("prop_es_petals", rng.choice((1, 2, 3)), (8, 22), (0.9, 1.4), region=(0, 0, H * 0.75))
    scatter("prop_es_lotus", rng.choice((1, 2, 3)) + (2 if tags & {"shrine", "crystal", "arena"} else 0),
            (12, 30), (0.8, 1.3), region=(0, 0, H * 0.75))
    if rng.random() < 0.6:
        scatter("prop_es_kite", rng.choice((1, 2)), (50, 80), (1.2, 1.8), region=(0, 0, H * 0.7))
    # skyrays: prove every orbit clear, and the flock's radii distinct
    rays = 3 if big else rng.choice((1, 2, 2))
    for _ in range(rays):
        for _t in range(40):
            R = rng.uniform(0.35, 0.8) * H
            z = rng.uniform(70, 140)
            scale = rng.uniform(1.0, 1.5)
            r = lib["prop_es_skyray"][3].length * scale / 2
            if R + r > H - EDGE_MARGIN:
                continue
            if any(abs(math.hypot(q[0], q[1]) - R) < r + q[3] + 3 and abs(q[2] - z) < r + q[3] + 3 for q in placed):
                continue
            if all(_clear(bvh, (R * math.cos(a), R * math.sin(a), z), r, gap=3)
                   for a in [k * 2 * math.pi / 48 for k in range(48)]):
                a0 = rng.uniform(0, 6.28)
                x, y = R * math.cos(a0), R * math.sin(a0)
                placed.append((x, y, z, r))
                # it flies nose-first round the centre: face the tangent
                p.props.append(dict(kind="prop_es_skyray", pos=Vector((x, y, z)), yaw=a0 + math.pi, scale=scale,
                                    size=lib["prop_es_skyray"][3] * scale, orbit=R))
                break


# ---------------------------------------------------------------------------
# To the game's frame: Blender (x, y, z) -> game (x, z, -y), the same as Sky Citadel.
# ---------------------------------------------------------------------------
TO_GAME = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))


def game_row(prop):
    anim, tier = KINDS[prop["kind"]]
    pos = TO_GAME @ prop["pos"]
    rotb = Matrix.Rotation(prop["yaw"], 3, "Z")
    rot = TO_GAME @ rotb @ TO_GAME.transposed()
    s = prop["size"]
    return dict(prop=prop["kind"], anim=anim, tier=tier, pos=[pos.x, pos.y, pos.z],
                rot=[rot[r][c] for r in range(3) for c in range(3)], size=[s.x, s.z, s.y])
