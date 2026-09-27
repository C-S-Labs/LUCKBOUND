# Ethereal Scape kit -- the ATMOSPHERE: ambient props (CHUNK_AUTHORING.md convention 6).
#
# Everything that drifts, hovers or flies is a prop, never part of a chunk's mesh: one library
# mesh per kind, a placement per copy. This world's set is its own -- no birds, no halos, no
# hoops (Sky Citadel's) -- chosen for a cloudscape above the weather:
#   drifting cloud puffs (Float), sky lanterns rising over the clearings (Float), hovering
#   sky-crystal shards (Hover), satellite islets high above (Float), and skyrays -- manta-like
#   gliders circling each clearing (Bird).
# Every placement is proven clear of the piece's REAL mesh (BVH), >= 4 studs inside the tile,
# and clear of every other prop; a skyray's whole orbit is proven, not just its resting spot.
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
    "prop_es_skyray": ("Bird", 2),
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
        # a flat manta: diamond body, swept wings, a whip tail. Indigo back, pale belly glow.
        v = [(0, 5, 0.3), (7, -1, 0), (0, -3, 0.2), (-7, -1, 0), (0, 0.5, 0.9), (0, 0.5, -0.5),
             (0, -3, 0.2), (0, -9, 0.0)]
        p.add(v, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], "IndigoLeaves")
        p.add(v, [[1, 0, 5], [2, 1, 5], [3, 2, 5], [0, 3, 5]], "CloudWhite")
        rod(p, "IndigoLeaves", (0, -2.8, 0.2), (0, -9, 0.0), 0.35, 0.05, n=4)
        gem(p, "PortalGlow", 0, 2.6, 0.55, 0.35, 0.2, 0.2, n=4)
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
    for k in ("prop_es_isle_grove", "prop_es_isle_crystal", "prop_es_isle_ruin"):
        if rng.random() < (0.9 if big else 0.55):
            scatter(k, 1, (100, 150), (0.9, 1.4), outer=True)
    lanterns = 3
    if tags & {"shrine", "gate-court", "arrival", "arena", "crossroads", "fork"}:
        lanterns = 9 if big else 7
    scatter("prop_es_lantern", lanterns, (16, 48), (1.0, 1.4), region=(0, 0, H * 0.7))
    if tags & {"crystal", "falls"} or "CRYSTAL_WARDEN" in spec.get("enemies", []):
        scatter("prop_es_shard", 6, (10, 34), (0.9, 1.6))
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
