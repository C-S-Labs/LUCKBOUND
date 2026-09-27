# Ethereal Scape -- the HYBRID kit's building blocks (owner pick, 2026-09-27: "the hybrid for sure").
#
#   A  Floating Isles is the base: every walkable surface is an isle hung in open sky -- meadow top,
#      the original scene's gold rim band, a deep faceted rock underside with roots and crystal.
#   C  Temple City supplies the architecture for combat pieces, the minibosses and the Sanctum.
#   B  Lush Cloudscape supplies the dressing ON the isles: carpets, groves, blossoms, pools.
#
# HEIGHT VARIATION. Isles sit at different heights inside a piece (terraces, sunken courts, high
# perches) and a piece's mouths may sit at different heights too: a socket's z is its OffsetY, so
# a rise or a descent carries the whole map up or down. Every mouth is still the standard landing,
# exactly the kind's width, level at its own z -- any two pieces meet cleanly.
import math

from es_features import FLOOR_Z, flagstones, guide_stone, puff
from es_features import column
from es_geometry import CROWN_TOP, DIRS, KIND_WIDTH, beam, box, decal_strip, frustum, gem, prism, ring_pts, rod

TEAL, INDIGO = "DeepTealLeaves", "IndigoLeaves"
KEEL_SAFE = -93.0


# ---------------------------------------------------------------------------
# outlines
# ---------------------------------------------------------------------------
def circle(p, cx, cy, r, sides=12, jit=(0.9, 1.07)):
    rng = p.rng
    out = []
    for i in range(sides):
        a = 2 * math.pi * (i + rng.uniform(-0.2, 0.2)) / sides
        rr = r * rng.uniform(*jit)
        out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return out


def rsquare(cx, cy, hx, hy, ch, per_edge=3):
    """A chamfered rectangle, its long edges subdivided so the underside rings stay faceted."""
    corners = [(hx - ch, -hy), (hx, -hy + ch), (hx, hy - ch), (hx - ch, hy), (-hx + ch, hy), (-hx, hy - ch),
               (-hx, -hy + ch), (-hx + ch, -hy)]
    out = []
    for i, a in enumerate(corners):
        b = corners[(i + 1) % len(corners)]
        n = 1 if i % 2 == 0 else per_edge
        for k in range(n):
            u = k / n
            out.append((cx + a[0] + (b[0] - a[0]) * u, cy + a[1] + (b[1] - a[1]) * u))
    return out


def inside(pts, x, y, margin=0.0):
    """Point in polygon, at least `margin` in from every edge."""
    n = len(pts)
    ok = False
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            ok = not ok
        if margin:
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy or 1e-9
            t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
            if math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)) < margin:
                return False
    return ok


def centroid(pts):
    return sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)


def face(x, y, tx, ty):
    """The rz that turns a building's FRONT (its door or open side, local -Y in every builder here: the
    shrine hall's porch, the hut's doorway) toward (tx, ty) -- the road or court it serves."""
    return math.atan2(ty - y, tx - x) + math.pi / 2


# ---------------------------------------------------------------------------
# isles
# ---------------------------------------------------------------------------
def isle(p, pts, z=FLOOR_Z, depth=70, floor="AetherMintGrass", roots=True, chandelier=True, skirt=False):
    """An isle hung in open sky at height z: meadow top, the gold rim band, three jagged tiers of
    rock underneath (never past the keel), hanging roots, a crystal chandelier out of the tip."""
    rng = p.rng
    depth = min(depth, z - KEEL_SAFE)
    cx, cy = centroid(pts)
    prism(p, pts, z - 2.5, z, floor, side=floor)
    rim = [(cx + (x - cx) * 1.04, cy + (y - cy) * 1.04) for x, y in pts]
    prism(p, rim, z - 6.0, z - 1.4, "TempleGold")
    n = len(pts)
    prev = None
    for k, (s, dz) in enumerate(((1.04, -6.0), (0.86, -depth * 0.3), (0.55, -depth * 0.64), (0.22, -depth * 0.9))):
        ring = [(cx + (x - cx) * s * rng.uniform(0.93, 1.05), cy + (y - cy) * s * rng.uniform(0.93, 1.05), z + dz)
                for x, y in pts]
        if prev is not None:
            p.add(prev + ring, [[n + i, n + (i + 1) % n, (i + 1) % n, i] for i in range(n)],
                  "PaleGoldSoil" if k == 1 else "Cloudstone")
        prev = ring
    p.add(prev + [(cx + rng.uniform(-3, 3), cy + rng.uniform(-3, 3), z - depth)],
          [[(i + 1) % n, i, n] for i in range(n)], "Cloudstone")
    if roots:
        for i in range(0, n, 2 if n <= 14 else 3):
            x, y = pts[i]
            mx, my = cx + (x - cx) * 0.86, cy + (y - cy) * 0.86
            a = math.atan2(my - cy, mx - cx)
            rod(p, "SoftWood", (mx - math.cos(a) * 3, my - math.sin(a) * 3, z - depth * 0.3 + 2),
                (mx + math.cos(a) * 4, my + math.sin(a) * 4, max(KEEL_SAFE, z - depth * 0.3 - rng.uniform(10, 22))),
                1.5, 0.3, n=5)
    if chandelier:
        r = min(math.hypot(x - cx, y - cy) for x, y in pts)
        for k in range(5):
            a = k * 1.26 + rng.uniform(-0.3, 0.3)
            bx, by = cx + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2
            rod(p, "SkyCrystal", (bx, by, z - depth * 0.5),
                (bx + math.cos(a) * 5, by + math.sin(a) * 5, max(KEEL_SAFE, z - depth * 0.9 - rng.uniform(4, 12))),
                2.2, 0.0, n=5)
    if skirt:
        cloud_skirt(p, pts, z)
    p.tops.append((pts, z))
    return pts


def cloud_skirt(p, pts, z, every=2):
    """Cloud clinging under an isle's rim: billows just outside the rock, a little below the deck.
    declip() removes any the rock still touches."""
    rng = p.rng
    cx, cy = centroid(pts)
    lim = p.H - 10
    for i in range(0, len(pts), every):
        x, y = pts[i]
        px, py = cx + (x - cx) * 1.2, cy + (y - cy) * 1.2
        if abs(px) > lim or abs(py) > lim:
            continue
        r = rng.uniform(5, 8)
        puff(p, px, py, z - rng.uniform(12, 20), r, r * 0.7, rng)


def landing(p, cardinal, z=FLOOR_Z, depth=40, length=34.0):
    """The standard mouth, hung in the sky: a flagstone landing exactly the kind's width, level at
    its socket's z, running to the tile edge, guide stones either side. Returns its inner end."""
    kind = dict(p.sockets)[cardinal]
    w = KIND_WIDTH[kind]
    H = p.H
    dx, dy = DIRS[cardinal]
    nx, ny = -dy, dx
    a0, a1 = H - length, H
    pts = [(dx * a0 + nx * (w / 2 + 7), dy * a0 + ny * (w / 2 + 7)), (dx * a1 + nx * (w / 2 + 2), dy * a1 + ny * (w / 2 + 2)),
           (dx * a1 - nx * (w / 2 + 2), dy * a1 - ny * (w / 2 + 2)), (dx * a0 - nx * (w / 2 + 7), dy * a0 - ny * (w / 2 + 7))]
    prism(p, pts, z - 3.0, z, "GoldenPath", side="TempleGold")
    cx, cy = dx * (H - length / 2), dy * (H - length / 2)
    d = min(depth, z - KEEL_SAFE)
    p.add([(x, y, z - 3.0) for x, y in pts] + [(cx - dx * 4, cy - dy * 4, z - d)], [[1, 0, 4], [2, 1, 4], [3, 2, 4], [0, 3, 4]],
          "Cloudstone")
    flagstones(p, (dx * a0, dy * a0), (dx * (a1 - 0.5), dy * (a1 - 0.5)), w, z + 0.045, course=7.0)
    for s in (-1, 1):
        decal_strip(p, "TempleGold", (dx * a0 + nx * s * (w / 2 - 0.6), dy * a0 + ny * s * (w / 2 - 0.6)),
                    (dx * a1 + nx * s * (w / 2 - 0.6), dy * a1 + ny * s * (w / 2 - 0.6)), 1.2, z + 0.05)
        guide_stone(p, dx * (a0 + 6) + nx * s * (w / 2 + 3.5), dy * (a0 + 6) + ny * s * (w / 2 + 3.5), z)
    p.corridors.append((dx * a0, dy * a0, dx * a1, dy * a1, w / 2 + 4))
    p.tops.append((pts, z))
    return (dx * a0, dy * a0)


# ---------------------------------------------------------------------------
# links between isles
# ---------------------------------------------------------------------------
def bridge(p, a, b, za=FLOOR_Z, zb=None, width=16.0):
    """The original's gold plank bridge -- level, or sloped between isles at different heights
    (never steeper than ~37 degrees, which the walk graph and a Humanoid both climb). Deck tops sit a hair over the isle tops they land on."""
    zb = za if zb is None else zb
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    assert abs(zb - za) <= L * 0.77 + 0.01, f"bridge too steep: {za}->{zb} over {L:.0f}"   # <= ~37 deg: walkable
    tx, ty = (bx - ax) / L, (by - ay) / L
    nx, ny = -ty, tx
    za, zb = za + 0.06, zb + 0.06

    def at(u, off=0.0, dz=0.0):
        return (ax + (bx - ax) * u + nx * off, ay + (by - ay) * u + ny * off, za + (zb - za) * u + dz)

    beam(p, "GoldenPath", at(0, 0, -0.6), at(1, 0, -0.6), width, 1.2)
    n = int(L / 3.2)
    for k in range(n):                                # plank seams, laid on the deck
        u = (k + 0.5) / n
        c = at(u)
        if za == zb:
            decal_strip(p, "SoftWood", (c[0] + nx * width * 0.49, c[1] + ny * width * 0.49),
                        (c[0] - nx * width * 0.49, c[1] - ny * width * 0.49), 0.7, c[2] + 0.03)
        else:                                         # on a slope a seam is a low slat, not a decal
            beam(p, "SoftWood", at(u, width * 0.48, 0.05), at(u, -width * 0.48, 0.05), 0.7, 0.1)
    for s in (-1, 1):
        prev = None
        m = max(2, int(L / 8))
        for k in range(m + 1):
            q = at(k / m, s * (width / 2 - 0.4))
            box(p, "SoftWood", q[0], q[1], q[2] + 2.0, 0.7, 0.7, 4.2)
            if prev:
                beam(p, "TempleGold", (prev[0], prev[1], prev[2] + 3.7), (q[0], q[1], q[2] + 3.7), 0.35, 0.35)
                beam(p, "TempleGold", (prev[0], prev[1], prev[2] + 2.0), (q[0], q[1], q[2] + 2.0), 0.25, 0.25)
            prev = q
        beam(p, "SoftWood", at(0, s * width * 0.3, -2.4), at(1, s * width * 0.3, -2.4), 1.2, 2.4)
    m = max(2, int(L / 12))
    for k in range(m):
        beam(p, "SoftWood", at(k / m, width * 0.3, -3.4), at((k + 1) / m, -width * 0.3, -3.4), 0.6, 0.6)
    p.corridors.append((ax, ay, bx, by, width / 2 + 2))


def stair_link(p, x, y, z0, z1, rz, width=16.0):
    """Ivory temple steps from the isle at z0 up to the isle at z1 (1-stud risers, 2-stud treads).
    Returns where they arrive."""
    from es_features import stairs
    return stairs(p, x, y, z0, z1, width, rz)


# ---------------------------------------------------------------------------
# crown pins (every piece's box must reach exactly +160)
# ---------------------------------------------------------------------------
def sky_spire(p, x, y, z=FLOOR_Z, r=5.0):
    """An AETHER BEACON: a stout stepped pagoda of three octagonal ivory tiers, each with a gold eave and
    crystal windows, crowned by a sky-crystal cluster whose tip is EXACTLY the crown. (Not a needle: the
    first pass read as Sky Citadel's spires, which the owner already rejected once.)"""
    p.keepout.append((x, y, r * 2.8))
    p.footings.append((x, y, z, r * 2.3, "sky_spire"))   # its WHOLE base plate (half-width 2.2r) must be on ground
    box(p, "Cloudstone", x, y, z + 0.5, r * 4.4, r * 4.4, 2.0)
    box(p, "TempleIvory", x, y, z + 2.2, r * 3.6, r * 3.6, 1.6)
    crown = CROWN_TOP - 20
    z0 = z + 3.0
    h = (crown - z0) / 3
    for k, rr in enumerate((r * 1.9, r * 1.5, r * 1.15)):
        za, zb = z0 + k * h, z0 + (k + 1) * h
        frustum(p, "TempleIvory", x, y, za - 0.2, zb - 2.0, rr, rr * 0.9, n=8, a0=math.pi / 8)
        frustum(p, "TempleGold", x, y, zb - 2.2, zb, rr * 1.25, rr * 0.8, n=8, a0=math.pi / 8)     # the eave
        for j in range(4):                                  # crystal windows set into the drum's faces
            a = j * math.pi / 2 + math.pi / 4 + math.pi / 8
            box(p, "SkyCrystal", x + math.cos(a) * rr * 0.9, y + math.sin(a) * rr * 0.9, za + h * 0.55, 0.8, rr * 0.35,
                h * 0.3, rz=a)
    gem(p, "SkyCrystal", x, y, crown + 4, r * 0.9, 6, 4.2, n=6)
    for j in range(3):                                      # side shards leaning out of the cluster
        a = j * 2.09 + 0.4
        rod(p, "SkyCrystal", (x + math.cos(a) * r * 0.3, y + math.sin(a) * r * 0.3, crown + 1),
            (x + math.cos(a) * r * 1.1, y + math.sin(a) * r * 1.1, crown + 9), r * 0.3, 0.0, n=5)
    frustum(p, "SkyCrystal", x, y, crown + 8, CROWN_TOP, r * 0.45, 0.0, n=6)


# ---------------------------------------------------------------------------
# temple pieces (from direction sample C; shared by the kit and the samples)
# ---------------------------------------------------------------------------
def statue(p, x, y, z=FLOOR_Z, rz=0.0):
    """A robed guardian on a plinth: stepped base, draped body, a gold-crowned head, a raised staff."""
    p.footings.append((x, y, z, 2.5, "statue"))
    box(p, "Cloudstone", x, y, z + 1.0, 6, 6, 2, rz=rz)
    box(p, "TempleIvory", x, y, z + 2.6, 4.6, 4.6, 1.2, rz=rz)
    frustum(p, "TempleIvory", x, y, z + 3.2, z + 11, 2.2, 1.3, n=8)
    gem(p, "TempleIvory", x, y, z + 11.7, 1.2, 1.0, 1.0, n=8)             # the head sits ON the body
    frustum(p, "TempleGold", x, y, z + 12.8, z + 13.8, 1.0, 0.5, n=8)
    c, s = math.cos(rz), math.sin(rz)
    sx, sy = x + c * 2.4, y + s * 2.4
    rod(p, "TempleGold", (sx, sy, z + 3.2), (sx, sy, z + 16), 0.3, 0.3, n=5)
    gem(p, "PortalGlow", sx, sy, z + 16.6, 0.7, 0.8, 0.6, n=6)
    p.keepout.append((x, y, 5))


def shrine_hall(p, x, y, z, w, d, rz=0.0):
    """A small temple: podium, walls with crystal windows, a four-column porch, a gold hip roof."""
    c, s = math.cos(rz), math.sin(rz)

    def at(u, v):
        return x + u * c - v * s, y + u * s + v * c

    prism(p, [at(-w / 2 - 3, -d / 2 - 8), at(w / 2 + 3, -d / 2 - 8), at(w / 2 + 3, d / 2 + 3), at(-w / 2 - 3, d / 2 + 3)],
          z - 0.5, z + 2, "TempleIvory", side="Cloudstone")
    h = 22
    for (u0, v0, u1, v1) in ((-w / 2, -d / 2, -5, -d / 2), (5, -d / 2, w / 2, -d / 2), (w / 2, -d / 2, w / 2, d / 2),
                             (w / 2, d / 2, -w / 2, d / 2), (-w / 2, d / 2, -w / 2, -d / 2)):
        a, b = at(u0, v0), at(u1, v1)
        beam(p, "TempleIvory", (a[0], a[1], z + 2 + h / 2), (b[0], b[1], z + 2 + h / 2), 2.4, h)
    for u in (-w / 2 - 1.3, w / 2 + 1.3):
        for v in (-d / 4, d / 4):
            q = at(u, v)
            box(p, "SkyCrystal", q[0], q[1], z + 13, 0.8 if True else 0, 5, 9, rz=rz)
    a, b = at(-5, -d / 2), at(5, -d / 2)
    beam(p, "TempleIvory", (a[0], a[1], z + 2 + h - 3), (b[0], b[1], z + 2 + h - 3), 2.4, 6)
    for u in (-w / 2 + 2, -6, 6, w / 2 - 2):
        q = at(u, -d / 2 - 6)
        column(p, q[0], q[1], z + 2, h, r=1.6)
    roof = [at(-w / 2 - 3, -d / 2 - 8), at(w / 2 + 3, -d / 2 - 8), at(w / 2 + 3, d / 2 + 3), at(-w / 2 - 3, d / 2 + 3)]
    prism(p, roof, z + 2 + h, z + 4 + h, "TempleIvory", side="TempleGold")
    cx, cy = at(0, -2.5)
    verts = [(q[0], q[1], z + 4 + h) for q in roof] + [(cx, cy, z + 4 + h + 14)]
    p.add(verts, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], "TempleGold")
    rod(p, "SkyCrystal", (cx, cy, z + 4 + h + 13), (cx, cy, z + 4 + h + 20), 1.2, 0.0, n=5)
    p.keepout.append((x, y, max(w, d) * 0.75 + 6))
