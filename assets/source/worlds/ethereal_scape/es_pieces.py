# Ethereal Scape kit -- the 30 piece recipes. docs/biomes/ETHEREAL_SCAPE.md has the table.
# Blender +Y is NORTH. Every piece: pins, the cloud floor, cloud-bank walls, standard mouths.
import math

from es_features import (meadow_carpet, near_corridor, rift_rim)  # noqa: F401
from es_features import (FLOOR_Z, aether_pool, arch, balustrade, bell_tower, blossoms, cloud_bank, cloud_floor, column,
                         crag, crystal_cluster, crystal_colossus, fountain, grass_tufts, great_tree, guide_stone, hut,
                         lantern_post, mesa, mouth, mushroom, path, pavilion, perimeter_banks, pins, puff, ramp, rock,
                         ruin_wall, stairs, tree, waystone)
from es_geometry import (CROWN_TOP, DIRS, beam, box, decal, decal_ring, decal_strip, frustum, gem, prism, ring_pts, rod)

TEAL, INDIGO = "DeepTealLeaves", "IndigoLeaves"


# ---------------------------------------------------------------------------
# shared compositions
# ---------------------------------------------------------------------------
def base(p, holes=(), density=1.0, skip_banks=()):
    pins(p)
    cloud_floor(p, holes=holes)
    perimeter_banks(p, skip=skip_banks, density=density)


def connect(p, hub=(0.0, 0.0), inner=None, style="flag"):
    """Mouths on every socket, each joined to the hub by a golden path."""
    for cardinal, kind in p.sockets:
        dx, dy = DIRS[cardinal]
        inn = inner if inner is not None else p.H * 0.45
        mouth(p, cardinal, inner=inn)
        w = 44 * (0.6 if kind == "SPAN" else 0.75)
        path(p, [hub, (dx * inn, dy * inn)], width=w)


def hub_plaza(p, x, y, r, star=True):
    decal(p, "GoldenPath", ring_pts(x, y, r, 18), FLOOR_Z + 0.04)
    decal_ring(p, "TempleGold", x, y, r - 1.5, r, FLOOR_Z + 0.06, n=18)
    decal_ring(p, "CloudWhite", x, y, r * 0.55, r * 0.6, FLOOR_Z + 0.06, n=18)
    if star:
        for k in range(8):
            a = k * math.pi / 4
            tip = r * (0.95 if k % 2 == 0 else 0.7)
            decal(p, "TempleGold" if k % 2 == 0 else "CloudWhite",
                  [(x + math.cos(a - 0.12) * r * 0.2, y + math.sin(a - 0.12) * r * 0.2),
                   (x + math.cos(a) * tip, y + math.sin(a) * tip),
                   (x + math.cos(a + 0.12) * r * 0.2, y + math.sin(a + 0.12) * r * 0.2)], FLOOR_Z + 0.07)
        decal(p, "PortalGlow", ring_pts(x, y, r * 0.16, 10), FLOOR_Z + 0.08)


def scatter(p, fn, n, region, avoid=(), clear_paths=True, **kw):
    """Place n things in region (cx, cy, r) away from `avoid` discs and from every corridor."""
    cx, cy, r = region
    rng = p.rng
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 40:
        tries += 1
        a, rr = rng.uniform(0, 6.28), r * math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if abs(x) > p.H - 44 or abs(y) > p.H - 44:     # clear of the perimeter cloud banks
            continue
        own = kw.get("clear", 4.0)             # the thing's own radius (a tree's crown, not just its trunk)
        if any(math.hypot(x - ax, y - ay) < ar + own for ax, ay, ar in list(avoid) + placed + p.keepout):
            continue
        if clear_paths and near_corridor(p, x, y, kw.get("clear", 4.0)):
            continue
        fn(p, x, y, **{k: v for k, v in kw.items() if k != "clear"})
        placed.append((x, y, 2.0))
    return placed


def plank_bridge(p, a, b, width=20.0, z=FLOOR_Z):
    """The original's gold plank bridge: a gold deck, soft-wood planks, posts and rope rails,
    stringers and cross-bracing underneath."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    tx, ty = (bx - ax) / L, (by - ay) / L
    nx, ny = -ty, tx
    beam(p, "GoldenPath", (ax, ay, z - 0.6), (bx, by, z - 0.6), width, 1.2)
    n = int(L / 3.2)
    for k in range(n):
        u = (k + 0.5) / n
        cx, cy = ax + (bx - ax) * u, ay + (by - ay) * u
        decal_strip(p, "SoftWood", (cx + nx * width * 0.49, cy + ny * width * 0.49), (cx - nx * width * 0.49, cy - ny * width * 0.49),
                    0.7, z + 0.03)
    for s in (-1, 1):
        prev = None
        m = max(2, int(L / 8))
        for k in range(m + 1):
            u = k / m
            px, py = ax + (bx - ax) * u + nx * s * (width / 2 - 0.4), ay + (by - ay) * u + ny * s * (width / 2 - 0.4)
            box(p, "SoftWood", px, py, z + 2.0, 0.7, 0.7, 4.2)
            if prev:
                beam(p, "TempleGold", (prev[0], prev[1], z + 3.7), (px, py, z + 3.7), 0.35, 0.35)
                beam(p, "TempleGold", (prev[0], prev[1], z + 2.0), (px, py, z + 2.0), 0.25, 0.25)
            prev = (px, py)
        beam(p, "SoftWood", (ax + nx * s * width * 0.3, ay + ny * s * width * 0.3, z - 2.4),
             (bx + nx * s * width * 0.3, by + ny * s * width * 0.3, z - 2.4), 1.2, 2.4)
    m = max(2, int(L / 12))
    for k in range(m):
        u0, u1 = k / m, (k + 1) / m
        p0 = (ax + (bx - ax) * u0 + nx * width * 0.3, ay + (by - ay) * u0 + ny * width * 0.3, z - 3.4)
        p1 = (ax + (bx - ax) * u1 - nx * width * 0.3, ay + (by - ay) * u1 - ny * width * 0.3, z - 3.4)
        beam(p, "SoftWood", p0, p1, 0.6, 0.6)
    p.corridors.append((ax, ay, bx, by, width / 2 + 2))


def aether_fall(p, x, y, z_top, out_dir, width=12.0, drop=None, z_bottom=FLOOR_Z):
    """A ribbon of glowing sky-crystal water spilling from a rim, curving outward as it falls,
    into a pool at its foot."""
    dx, dy = out_dir
    nx, ny = -dy, dx
    drop = drop if drop is not None else z_top - z_bottom
    steps = 5
    verts, faces = [], []
    for k in range(steps + 1):
        u = k / steps
        out = 1.0 + 7.0 * u ** 1.6
        zz = z_top - drop * u
        cx, cy = x + dx * out, y + dy * out
        w = width * (1 - 0.15 * u)
        verts += [(cx + nx * w / 2, cy + ny * w / 2, zz), (cx - nx * w / 2, cy - ny * w / 2, zz),
                  (cx - nx * w / 2 + dx * 0.8, cy - ny * w / 2 + dy * 0.8, zz), (cx + nx * w / 2 + dx * 0.8, cy + ny * w / 2 + dy * 0.8, zz)]
    for k in range(steps):
        a = 4 * k
        b = a + 4
        for i in range(4):
            j = (i + 1) % 4
            faces.append([a + i, a + j, b + j, b + i])
    p.add(verts, faces, "SkyCrystal")
    fx, fy = x + dx * 9, y + dy * 9
    aether_pool(p, fx + dx * 6, fy + dy * 6, 11, z_bottom)
    for k in range(3):
        puff(p, fx + dx * 6 + p.rng.uniform(-6, 6), fy + dy * 6 + p.rng.uniform(-6, 6), z_bottom - 1, 4, 3, p.rng)


def meadow_dress(p, region, trees=6, blossom=40, tufts=16, mush=4, avoid=(), crowns=(TEAL, INDIGO), z=FLOOR_Z):
    rng = p.rng
    if z == FLOOR_Z and trees:                 # a grove stands on its own patch of meadow
        meadow_carpet(p, region[0], region[1], region[2] * 0.9)
    scatter(p, lambda p_, x, y: tree(p_, x, y, z=z, h=rng.uniform(16, 26), crown=crowns[rng.randrange(len(crowns))],
                                    style=rng.randrange(3)), trees, region, avoid=avoid, clear=8)
    scatter(p, lambda p_, x, y: mushroom(p_, x, y, z=z, s=rng.uniform(0.8, 1.6)), mush, region, avoid=avoid, clear=3)
    cx, cy, r = region
    blossoms(p, cx, cy, r, blossom, z=z, avoid=avoid)
    grass_tufts(p, cx, cy, r, tufts, z=z, avoid=avoid)


# ---------------------------------------------------------------------------
# ENTRY and BOSS
# ---------------------------------------------------------------------------
def es_entry(p):
    """Arrival Meadow (384): a gold mosaic landing ringed by crystal-topped spawn columns; the
    original's shrine pavilion on a mesa to the west, a great sky tree to the east. The column
    above the landing and the south quarter (the game's return portal) are kept clear."""
    base(p, density=0.6)
    H = p.H
    hub_plaza(p, 0, 0, 34)
    mouth(p, "N", inner=H * 0.5)
    path(p, [(0, 34), (0, H * 0.5)], width=26)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = math.cos(a) * 46, math.sin(a) * 46
        column(p, x, y, FLOOR_Z, 22, r=2.4)
        rod(p, "SkyCrystal", (x, y, FLOOR_Z + 22), (x, y, FLOOR_Z + 30), 1.8, 0.0, n=5)
    # the return-portal pad, south: a ring of low stones, nothing standing
    decal_ring(p, "TempleGold", 0, -110, 26, 27.5, FLOOR_Z + 0.05, n=24)
    for k in range(10):
        a = k * 0.628
        rock(p, math.cos(a) * 31, -110 + math.sin(a) * 31, s=1.2)
    path(p, [(0, -34), (0, -84)], width=14)
    # west mesa with the shrine pavilion
    mesa(p, -118, 48, 46, top=8)
    ramp(p, (-66, 28), (-84, 36), 12, FLOOR_Z, 8)
    pavilion(p, -122, 52, 8, 16, 16, 12, rz=0.3)
    meadow_dress(p, (-118, 48, 34), trees=5, blossom=30, tufts=10, mush=3, avoid=[(-122, 52, 16), (-84, 36, 10)], z=8)
    # east: the great sky tree over a flower meadow
    great_tree(p, 118, 64, FLOOR_Z, top=CROWN_TOP, trunk=8)
    blossoms(p, 110, 40, 44, 50, avoid=[(118, 64, 22)])
    aether_pool(p, 88, -64, 16)
    for s in (-1, 1):
        for k in range(3):
            lantern_post(p, s * 18, 60 + k * 30, rz=0 if s > 0 else math.pi)
        waystone(p, s * 24, H * 0.5 + 18, rz=0.2 * s)
    meadow_dress(p, (0, 0, H * 0.72), trees=12, blossom=60, tufts=24, mush=6,
                 avoid=[(0, 0, 58), (0, -110, 38), (-118, 48, 54), (118, 64, 40), (88, -64, 22)])


def es_sanctum(p):
    """The Sanctum (512): the grand temple that HOUSES the boss. A podium climbed by the
    ceremonial stair, a colonnaded portico, walls of crystal windows between pilasters, an open
    hall 240 x 230 under a flat ribbed roof with a crystal-windowed lantern over the centre, and
    four corner towers whose crystal tips pin the crown."""
    base(p, density=0.3)
    H = p.H
    mouth(p, "S", inner=124)
    z = 6.0
    X0, X1, Y0, Y1 = -138.0, 138.0, -110.0, 154.0
    prism(p, [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], FLOOR_Z - 0.5, z, "TempleIvory", side="Cloudstone")
    for (ax, ay), (bx, by) in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
        beam(p, "TempleGold", (ax, ay, z - 1.2), (bx, by, z - 1.2), 1.4, 1.2)
    stairs(p, 0, Y0 - 12, FLOOR_Z, z, 90, math.pi / 2)
    # --- walls -------------------------------------------------------------
    WX, WY0, WY1, T, WH = 124.0, -96.0, 142.0, 4.0, 64.0
    door = 32.0

    def wall(a, b, z0, z1):
        beam(p, "TempleIvory", (a[0], a[1], (z0 + z1) / 2), (b[0], b[1], (z0 + z1) / 2), T, z1 - z0)

    wall((-WX, WY0), (-door, WY0), z, WH)
    wall((door, WY0), (WX, WY0), z, WH)
    wall((-door, WY0), (door, WY0), 50, WH)                 # lintel over the great door
    beam(p, "TempleGold", (-door, WY0 - 2.2, 50.5), (door, WY0 - 2.2, 50.5), 1.2, 1.6)
    wall((WX, WY0), (WX, WY1), z, WH)
    wall((WX, WY1), (-WX, WY1), z, WH)
    wall((-WX, WY1), (-WX, WY0), z, WH)
    # pilasters and crystal windows along the three solid walls (outside faces)
    for sx in (-1, 1):
        y = WY0 + 12
        while y < WY1 - 8:
            box(p, "TempleIvory", sx * (WX + 2.6), y, (z + WH) / 2, 2.6, 4.0, WH - z)
            box(p, "TempleGold", sx * (WX + 2.6), y, z + 1.0, 3.4, 4.8, 2.0)
            box(p, "TempleGold", sx * (WX + 2.6), y, WH - 1.0, 3.4, 4.8, 2.0)
            if y + 12 < WY1 - 8:
                box(p, "SkyCrystal", sx * WX, y + 12, 34, T + 0.5, 9, 20)     # through the wall: lit inside too
                box(p, "TempleGold", sx * (WX + 2.2), y + 12, 23.5, 1.0, 11, 1.0)
                box(p, "TempleGold", sx * (WX + 2.2), y + 12, 44.5, 1.0, 11, 1.0)
            y += 24
    x = -WX + 12
    while x < WX - 8:
        box(p, "TempleIvory", x, WY1 + 2.6, (z + WH) / 2, 4.0, 2.6, WH - z)
        if x + 12 < WX - 8:
            box(p, "SkyCrystal", x + 12, WY1, 34, 9, T + 0.5, 20)
        x += 24
    # --- the portico: eight columns before the south wall, an entablature -------
    for cx in (-108, -80, -52, 52, 80, 108):
        column(p, cx, WY0 - 8, z, WH - z, r=3.2)
    beam(p, "TempleIvory", (-126, WY0 - 8, WH + 1.5), (126, WY0 - 8, WH + 1.5), 9, 3)
    beam(p, "TempleGold", (-126, WY0 - 12.6, WH + 3.4), (126, WY0 - 12.6, WH + 3.4), 1.0, 1.0)
    # pediment over the portico
    p.add([(-100, WY0 - 12, WH + 3), (100, WY0 - 12, WH + 3), (0, WY0 - 12, WH + 24),
           (-100, WY0 - 4, WH + 3), (100, WY0 - 4, WH + 3), (0, WY0 - 4, WH + 24)],
          [[0, 1, 2], [4, 3, 5], [0, 3, 4, 1]], "TempleIvory")
    p.add([(-104, WY0 - 13, WH + 2.6), (0, WY0 - 13, WH + 25.5), (0, WY0 - 3, WH + 25.5), (-104, WY0 - 3, WH + 2.6),
           (104, WY0 - 13, WH + 2.6), (104, WY0 - 3, WH + 2.6)],
          [[0, 1, 2, 3], [1, 4, 5, 2]], "TempleGold")
    gem(p, "PortalGlow", 0, WY0 - 12.2, WH + 12, 4.0, 3.0, 3.0, n=8)
    # --- the roof: a flat ribbed deck around a central lantern ---------------
    RZ = WH
    cx0, cy0 = 0.0, (WY0 + WY1) / 2
    hole = 36.0
    for (ax, ay, bx, by) in ((-WX - 2, WY0 - 2, WX + 2, cy0 - hole), (-WX - 2, cy0 + hole, WX + 2, WY1 + 2),
                             (-WX - 2, cy0 - hole, -hole, cy0 + hole), (hole, cy0 - hole, WX + 2, cy0 + hole)):
        prism(p, [(ax, ay), (bx, ay), (bx, by), (ax, by)], RZ, RZ + 4, "TempleGold", side="TempleIvory")
    for k in range(-4, 5):
        beam(p, "SoftWood", (k * 27, WY0, RZ + 4.6), (k * 27, WY1, RZ + 4.6), 2.2, 1.2) if abs(k * 27) > hole + 2 else None
    # the lantern: crystal-windowed walls around the opening, a gold hip roof
    LZ1 = RZ + 30
    for (a, b) in (((-hole, cy0 - hole), (hole, cy0 - hole)), ((hole, cy0 - hole), (hole, cy0 + hole)),
                   ((hole, cy0 + hole), (-hole, cy0 + hole)), ((-hole, cy0 + hole), (-hole, cy0 - hole))):
        beam(p, "TempleIvory", (a[0], a[1], RZ + 4 + 13), (b[0], b[1], RZ + 4 + 13), 3.0, 26)
        for u in (0.25, 0.5, 0.75):
            q = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            beam(p, "SkyCrystal", (q[0] - (b[0] - a[0]) * 0.08, q[1] - (b[1] - a[1]) * 0.08, RZ + 17),
                 (q[0] + (b[0] - a[0]) * 0.08, q[1] + (b[1] - a[1]) * 0.08, RZ + 17), 3.4, 14)
    verts = [(-hole - 4, cy0 - hole - 4, LZ1), (hole + 4, cy0 - hole - 4, LZ1), (hole + 4, cy0 + hole + 4, LZ1),
             (-hole - 4, cy0 + hole + 4, LZ1), (0, cy0, LZ1 + 26)]
    p.add(verts, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [3, 2, 1, 0]], "TempleGold")
    for k in range(4):
        a = verts[k]
        rod(p, "TempleIvory", (a[0], a[1], LZ1 + 0.3), (0, cy0, LZ1 + 26.3), 0.6, 0.6, n=4)
    frustum(p, "SkyCrystal", 0, cy0, LZ1 + 25, LZ1 + 34, 2.4, 0.0, n=6)
    # --- four corner towers (their crystal tips pin +160) -------------------
    for tx in (-127, 127):                      # engaged in the wall corners, wholly on the podium
        for ty in (-99, 143):
            frustum(p, "TempleIvory", tx, ty, z - 0.5, 108, 11, 9.5, n=8)
            for zz in (30, 64, 96):
                frustum(p, "TempleGold", tx, ty, zz, zz + 2, 11.2, 11.0, n=8)
            for k in range(8):                   # windows set INTO the face (the 8-gon's apothem, ~9.1)
                a = k * math.pi / 4 + math.pi / 8
                box(p, "SkyCrystal", tx + math.cos(a) * 9.0, ty + math.sin(a) * 9.0, 82, 0.6, 3, 9, rz=a)
            frustum(p, "TempleGold", tx, ty, 108, 150, 12.5, 0.8, n=8)
            frustum(p, "SkyCrystal", tx, ty, 148, CROWN_TOP, 2.6, 0.0, n=6)
    # --- inside: the arena floor and the boss dais -------------------------
    decal_ring(p, "GoldenPath", cx0, cy0, 64, 70, z + 0.05, n=32)
    decal_ring(p, "PortalGlow", cx0, cy0, 44, 45.5, z + 0.06, n=32)
    decal_ring(p, "TempleGold", cx0, cy0, 20, 22, z + 0.06, n=24)
    decal(p, "PortalGlow", ring_pts(cx0, cy0, 7, 12), z + 0.07)
    for k in range(12):
        a = k * math.pi / 6
        decal_strip(p, "TempleGold", (cx0 + math.cos(a) * 22, cy0 + math.sin(a) * 22),
                    (cx0 + math.cos(a) * 64, cy0 + math.sin(a) * 64), 1.2, z + 0.055)
    box(p, "TempleIvory", 0, WY1 - 14, z + 0.75, 70, 18, 1.5)
    box(p, "TempleGold", 0, WY1 - 5, z + 2.5, 30, 3, 5)
    # --- the grounds: processional lanterns, waystones, pools, groves ------
    for k in range(3):                              # processional lanterns (fewer, wider-spaced: tri budget)
        y = -142 - k * 34
        for s in (-1, 1):
            lantern_post(p, s * 34, y, rz=0 if s > 0 else math.pi, h=10)
    for s in (-1, 1):
        waystone(p, s * 44, -128, rz=0.2 * s, h=20)
        aether_pool(p, s * 170, -170, 22)
        crystal_cluster(p, s * 196, -120, s=1.4, n=6)
        tree(p, s * 186, 40, h=30, crown=TEAL, style=1)
        tree(p, s * 196, 110, h=26, crown=INDIGO)
        tree(p, s * 170, -30, h=22, crown=INDIGO, style=2)
    # the temple gardens: a meadow either side of the processional road, groves at their far ends
    for s in (-1, 1):
        meadow_carpet(p, s * 110, -185, 46)
        for k in range(3):
            tree(p, s * (92 + k * 22), -214 + (k % 2) * 16, h=24 - k * 2, crown=TEAL if k % 2 else INDIGO, style=k % 3)
        blossoms(p, s * 110, -185, 40, 12)


# ---------------------------------------------------------------------------
# PATH: straights
# ---------------------------------------------------------------------------
def es_meadow_walk(p):
    base(p)
    connect(p, hub=(10, 0))
    great_tree(p, -66, -18)
    mesa(p, 74, 34, 30, top=6)
    for k in range(3):
        tree(p, 70 + math.cos(k * 2.1) * 14, 34 + math.sin(k * 2.1) * 14, z=6, h=20, crown=INDIGO if k else TEAL)
    for s in (-1, 1):
        for k in range(3):
            lantern_post(p, s * 16 + 10, -60 + k * 60, rz=0 if s > 0 else math.pi)
    meadow_dress(p, (0, 0, 104), trees=10, blossom=70, tufts=22, mush=5, avoid=[(-66, -18, 26), (74, 34, 38)])


def es_ruin_stair(p):
    """The path climbs onto a ruined temple terrace, under a colossal gate, and down again."""
    base(p)
    for cardinal in ("N", "S"):
        mouth(p, cardinal, inner=78)          # the path reaches the stair foot, not under the terrace
    tz = 6.0
    prism(p, [(-44, -64), (44, -64), (44, 64), (-44, 64)], FLOOR_Z - 0.5, tz, "TempleIvory", side="Cloudstone")
    stairs(p, 0, -76, FLOOR_Z, tz, 30, math.pi / 2)
    stairs(p, 0, 76, FLOOR_Z, tz, 30, -math.pi / 2)
    for gx in range(-40, 41, 10):
        decal_strip(p, "CloudWhite", (gx, -62), (gx, 62), 0.4, tz + 0.03)
    for gy in range(-60, 61, 10):
        decal_strip(p, "CloudWhite", (-42, gy), (42, gy), 0.4, tz + 0.03)
    for s in (-1, 1):
        for k, y in enumerate((-46, -26, 22, 44)):
            column(p, s * 34, y, tz, 30, r=2.6, broken=(k + (s > 0)) % 2 == 0)   # no drums: they'd roll off the terrace
    arch(p, 0, 0, tz, 56, 0, rz=0.0, thick=6, top=CROWN_TOP)
    ruin_wall(p, (-80, 40), (-60, 88), h=9)
    ruin_wall(p, (70, -90), (92, -52), h=7)
    meadow_dress(p, (-80, -40, 36), trees=3, blossom=18, tufts=8)
    meadow_dress(p, (80, 40, 36), trees=3, blossom=18, tufts=8)


def es_rift_bridge(p):
    """A rift tears through the cloud; the gold plank bridge crosses it beside a crag that rises
    out of the depths."""
    base(p, holes=[(0, 0, 62)])
    mouth(p, "S", inner=74)                   # no path over the rift: the bridge is the way across
    mouth(p, "N", inner=74)
    plank_bridge(p, (0, -76), (0, 76), width=20)
    crag(p, 44, 14, z=-92, r=20, top=CROWN_TOP)
    rift_rim(p, 0, 0, 62)
    # (the mist drifting in the rift is atmosphere: props, placed by es_props -- not baked in here)
    for s in (-1, 1):
        guide_stone(p, s * 14, -76, FLOOR_Z)
        guide_stone(p, s * 14, 76, FLOOR_Z)
    meadow_dress(p, (-80, -80, 34), trees=3, blossom=16, tufts=8)
    meadow_dress(p, (80, 84, 30), trees=3, blossom=16, tufts=8)


def es_crystal_field(p):
    base(p)
    connect(p, hub=(-14, 0))
    crystal_colossus(p, 62, 40)
    scatter(p, lambda p_, x, y: crystal_cluster(p_, x, y, s=p.rng.uniform(0.7, 1.3), n=4), 9, (0, 0, 100),
            avoid=[(62, 40, 34)], clear=7)
    blossoms(p, -60, -30, 40, 40)
    for k in range(5):
        rock(p, -70 + k * 8, 60 - k * 6, s=2 + k % 2)


def es_lily_terraces(p):
    """Low meadow mesas stepping away from the path, a crag rising from the highest."""
    base(p)
    connect(p, hub=(0, 0))
    mesa(p, -62, 48, 34, top=10)
    crag(p, -66, 52, z=10, r=15, top=CROWN_TOP)
    mesa(p, 60, -44, 30, top=5)
    ramp(p, (20, -37), (36, -40), 10, FLOOR_Z, 5)
    pavilion(p, 64, -44, 5, 12, 12, 9, rz=-0.4, roof="slab")
    mesa(p, 64, 56, 22, top=3)
    tree(p, 64, 56, z=3, h=22, crown=TEAL, style=1)
    mesa(p, -60, -58, 24, top=4)
    for k in range(3):
        tree(p, -60 + math.cos(k * 2) * 10, -58 + math.sin(k * 2) * 10, z=4, h=16, crown=INDIGO)
    blossoms(p, 0, 0, 100, 40, avoid=[(-62, 48, 40), (60, -44, 36), (64, 56, 28), (-60, -58, 30)])


# ---------------------------------------------------------------------------
# PATH: bends
# ---------------------------------------------------------------------------
def es_bend_east_grove(p):
    base(p)
    connect(p, hub=(0, 0))
    great_tree(p, -54, 56)
    meadow_dress(p, (-50, 50, 64), trees=9, blossom=36, tufts=16, mush=6, avoid=[(-54, 56, 26)],
                 crowns=(TEAL, TEAL, INDIGO))
    for k in range(9):                                     # fairy ring of mushrooms
        a = k * 0.698
        mushroom(p, 52 + math.cos(a) * 12, -52 + math.sin(a) * 12, s=1.3)
    blossoms(p, 52, -52, 9, 14)


def es_bend_east_terrace(p):
    base(p)
    connect(p, hub=(0, 0))
    mesa(p, -52, 52, 46, top=10)
    ramp(p, (-14, 14), (-28, 26), 12, FLOOR_Z, 10)
    bell_tower(p, -62, 62, z=10, rz=0.3)
    for k in range(4):
        lantern_post(p, -20 - k * 12, 30 - k * 3 + 12, z=10 if k else 10, rz=math.pi / 2)
    meadow_dress(p, (-52, 52, 40), trees=4, blossom=20, tufts=8, avoid=[(-62, 62, 20), (-28, 26, 12)])
    meadow_dress(p, (50, -50, 44), trees=4, blossom=24, tufts=10, mush=3)


def es_bend_west_shrine(p):
    base(p)
    connect(p, hub=(0, 0))
    bell_tower(p, 60, 60, rz=-0.4)
    pavilion(p, -48, -48, FLOOR_Z, 14, 14, 11, rz=0.785)
    for k in range(4):
        a = k * math.pi / 2 + 0.3
        waystone(p, -48 + math.cos(a) * 20, -48 + math.sin(a) * 20, rz=a)
    meadow_dress(p, (40, 40, 60), trees=6, blossom=36, tufts=12, avoid=[(60, 60, 22)])


def es_bend_west_falls(p):
    """Aether Falls: a mesa's rim spills a glowing fall into a pool; crystal colossus on top."""
    base(p)
    connect(p, hub=(0, 0))
    rim = mesa(p, 54, 50, 42, top=14)
    crystal_colossus(p, 58, 56, z=14, spread=10)
    d = (-0.78, -0.62)
    fx, fy = max(rim, key=lambda q: (q[0] - 54) * d[0] + (q[1] - 50) * d[1])   # the rim vertex facing the fall
    aether_fall(p, fx, fy, 14 - 1.4, d, width=12)
    meadow_dress(p, (-50, 50, 40), trees=5, blossom=30, tufts=10)
    meadow_dress(p, (50, -50, 40), trees=4, blossom=24, tufts=10, mush=4)


# ---------------------------------------------------------------------------
# PATH: intersections
# ---------------------------------------------------------------------------
def es_fork_wayshrine(p):
    """A three-way fork round a waystone circle, a signpost at its heart, a great tree behind."""
    base(p)
    connect(p, hub=(0, 0))
    hub_plaza(p, 0, 0, 26)
    for a in (45, 90, 135, -45, -135):
        r = math.radians(a)
        waystone(p, math.cos(r) * 36, math.sin(r) * 36, rz=r)
    frustum(p, "SoftWood", 14, 14, FLOOR_Z - 0.3, 9, 0.5, 0.4, n=5)
    for k, a in enumerate((0, math.pi, -math.pi / 2)):
        beam(p, "GoldenPath", (14, 14, 7.6 - k * 1.3), (14 + math.cos(a) * 4, 14 + math.sin(a) * 4, 7.6 - k * 1.3), 1.0, 0.8)
    great_tree(p, 0, 74)
    meadow_dress(p, (-60, 60, 44), trees=5, blossom=26, tufts=10, avoid=[(0, 74, 26)])
    meadow_dress(p, (60, 60, 44), trees=5, blossom=26, tufts=10, avoid=[(0, 74, 26)])
    meadow_dress(p, (0, -80, 30), trees=0, blossom=20, tufts=8)


def es_fork_three_trees(p):
    """A three-way fork under three ancient trees -- the tallest pins the crown."""
    base(p)
    connect(p, hub=(0, 0))
    great_tree(p, -64, 10, trunk=8)
    tree(p, -40, -62, h=44, crown=INDIGO, style=1)
    tree(p, 56, 62, h=40, crown=TEAL, style=0)
    for k in range(10):
        a = k * 0.628
        mushroom(p, -64 + math.cos(a) * 22, 10 + math.sin(a) * 22, s=1.1)
    meadow_dress(p, (50, -50, 40), trees=4, blossom=30, tufts=10, mush=3)
    lantern_post(p, 14, 14, rz=0.8)


def es_convergence(p):
    """The crossroads: a great compass court with a fountain at its heart, four golden roads."""
    base(p)
    connect(p, hub=(0, 0), inner=58)
    hub_plaza(p, 0, 0, 46)
    fountain(p, 0, 0)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        lantern_post(p, math.cos(a) * 50, math.sin(a) * 50, rz=a)
    crystal_colossus(p, 70, 70)
    mesa(p, -70, 72, 26, top=6)
    for k in range(3):
        tree(p, -70 + math.cos(k * 2.1) * 12, 72 + math.sin(k * 2.1) * 12, z=6, h=18, crown=TEAL)
    aether_pool(p, -70, -70, 20)
    for k in range(4):
        column(p, 62 + k * 7, -64 + k * 5, FLOOR_Z, 22, broken=k % 2 == 0)


# ---------------------------------------------------------------------------
# COMBAT
# ---------------------------------------------------------------------------
def es_meadow_of_blooms(p):
    base(p)
    connect(p, hub=(0, 0))
    great_tree(p, 62, -30)
    blossoms(p, 0, 0, 104, 160, avoid=[(62, -30, 22)])
    grass_tufts(p, 0, 0, 100, 30)
    scatter(p, lambda p_, x, y: tree(p_, x, y, h=p.rng.uniform(16, 24), crown=TEAL if p.rng.random() < .6 else INDIGO),
            7, (0, 0, 100), avoid=[(0, 0, 50), (62, -30, 30)], clear=10)
    scatter(p, lambda p_, x, y: rock(p_, x, y, s=p.rng.uniform(1.5, 3)), 6, (0, 0, 100), clear=4)


def es_terraced_gardens(p):
    base(p)
    connect(p, hub=(0, 0))
    mesa(p, -62, 4, 42, top=6)
    mesa(p, 62, 22, 38, top=12)
    ramp(p, (-16, -6), (-30, -4), 10, FLOOR_Z, 6)
    ramp(p, (16, 6), (36, 12), 10, FLOOR_Z, 12)
    crag(p, 72, 34, z=12, r=15, top=CROWN_TOP)
    for s, (cx, cy, top) in ((-1, (-62, 4, 6)), (1, (62, 22, 12))):
        for k in range(4):
            decal_strip(p, "PaleGoldSoil", (cx - 26, cy - 22 + k * 11), (cx + 12 * s, cy - 22 + k * 11), 4, top + 0.04)
            for m in range(3):
                mushroom(p, cx - 20 + m * 11, cy - 22 + k * 11, z=top, s=0.9)
    for k in range(3):
        lantern_post(p, -62 + 20, 4 - 20 + k * 20, z=6, rz=math.pi)
    meadow_dress(p, (0, -80, 30), trees=2, blossom=20, tufts=8)
    meadow_dress(p, (0, 84, 28), trees=2, blossom=20, tufts=8)


def es_crystal_hollow(p):
    base(p)
    connect(p, hub=(-12, 0))
    aether_pool(p, 30, 0, 20)
    for k in range(7):
        a = k * 0.9 - 1.6
        crystal_cluster(p, 30 + math.cos(a) * 32, math.sin(a) * 32, s=1.1, n=5)
    crystal_colossus(p, -62, 50)
    blossoms(p, 30, 0, 40, 30, avoid=[(30, 0, 22)])
    meadow_dress(p, (-60, -60, 34), trees=3, blossom=16, tufts=8)


def es_fallen_colonnade(p):
    base(p)
    connect(p, hub=(0, 0))
    decal(p, "TempleIvory", [(-52, -66), (52, -66), (52, 66), (-52, 66)], FLOOR_Z + 0.02)
    for gx in range(-48, 49, 12):
        decal_strip(p, "CloudWhite", (gx, -64), (gx, 64), 0.5, FLOOR_Z + 0.04)
    for s in (-1, 1):
        for k, y in enumerate(range(-54, 60, 18)):
            standing = k in (1, 2, 5)
            column(p, s * 38, y, FLOOR_Z, 34, r=3.0, broken=not standing, drum_fall=(k == 3))
        beam(p, "TempleIvory", (s * 38, -36, 35.5), (s * 38, 0, 35.5), 7, 3)
    ruin_wall(p, (-52, 66), (-10, 66), h=10)
    ruin_wall(p, (52, -66), (20, -66), h=8)
    bell_tower(p, -80, -46, rz=0.2)
    meadow_dress(p, (76, 50, 30), trees=3, blossom=16, tufts=8)


def es_mirror_pool(p):
    base(p)
    connect(p, hub=(0, 0))
    aether_pool(p, 0, 0, 38)
    for k in range(-5, 6):
        decal(p, "TempleIvory", ring_pts(0, k * 7, 3.2, 8), FLOOR_Z + 0.09)
    balustrade(p, ring_pts(0, 0, 41, 20), FLOOR_Z, closed=True, spacing=5, gaps=[(0, 41, 14), (0, -41, 14)])
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        lantern_post(p, math.cos(a) * 46, math.sin(a) * 46, rz=a)
    crag(p, 70, -52, r=18)
    meadow_dress(p, (-66, 52, 40), trees=5, blossom=24, tufts=10)


def es_shrine_of_winds(p):
    base(p)
    connect(p, hub=(0, 0))
    hub_plaza(p, 0, 0, 22, star=False)
    box(p, "TempleIvory", 0, 0, FLOOR_Z + 1.5, 4, 4, 3)
    gem(p, "TempleGold", 0, 0, FLOOR_Z + 3.8, 1.4, 1.2, 1.0, n=8)      # seated in the altar top, not above it
    p.keepout.append((0, 0, 6))
    for k, a in enumerate((math.radians(30), math.radians(150), math.radians(-30))):
        pavilion(p, math.cos(a) * 52, math.sin(a) * 52, FLOOR_Z, 12, 12, 10, rz=a, roof=("hip", "slab", "hip")[k])
    bell_tower(p, -62, -60, rz=0.4)
    meadow_dress(p, (60, -60, 36), trees=3, blossom=24, tufts=8)


def es_rooted_hollow(p):
    """A great tree whose roots arch over the path; mushrooms and soil in its shade."""
    base(p)
    connect(p, hub=(0, 0))
    great_tree(p, 48, 12, trunk=9)
    for dy in (-10, 26):                                   # root arches over the path (headroom >= 10)
        pts = [(36, dy, 1), (18, dy + 2, 13), (0, dy + 3, 15), (-18, dy + 4, 12), (-30, dy + 5, -1)]
        for a, b in zip(pts, pts[1:]):
            rod(p, "SoftWood", a, b, 2.2, 1.8, n=6)
    decal(p, "PaleGoldSoil", ring_pts(36, 10, 30, 12), FLOOR_Z + 0.02)
    scatter(p, lambda p_, x, y: mushroom(p_, x, y, s=p.rng.uniform(1, 2)), 14, (20, 10, 50), avoid=[(48, 12, 16)], clear=3)
    meadow_dress(p, (-60, -50, 40), trees=5, blossom=24, tufts=10, crowns=(INDIGO,))


def es_twin_mesas(p):
    """Two mesas flank the path, joined over it by a high plank bridge."""
    base(p)
    connect(p, hub=(0, 0))
    mesa(p, -56, 24, 36, top=10)
    mesa(p, 56, -18, 36, top=10)
    plank_bridge(p, (-32, 14), (32, -8), width=10, z=10)      # ends well inside both rims
    ramp(p, (-56, -24), (-56, -6), 10, FLOOR_Z, 10)
    ramp(p, (56, 22), (56, 4), 10, FLOOR_Z, 10)
    bell_tower(p, -66, 38, z=10, rz=0.5)
    for k, y in enumerate((8, 20)):
        column(p, -40, y, 10, 20, broken=k == 0)
    pavilion(p, 62, -22, 10, 12, 12, 9, rz=-0.3)
    meadow_dress(p, (-60, -70, 30), trees=3, blossom=16, tufts=8)
    meadow_dress(p, (60, 70, 30), trees=3, blossom=16, tufts=8)


def es_temple_gate_a(p):
    """The common gate-court: a forecourt, waystones lining the road, two bell towers flanking the
    arch that frames the COMMUNION road north."""
    base(p)
    connect(p, hub=(0, -10))
    hub_plaza(p, 0, -10, 28)
    for s in (-1, 1):
        bell_tower(p, s * 50, 62, rz=0.0)
        for k in range(3):
            waystone(p, s * 30, 14 + k * 17, rz=0.0)          # stops short of the arch piers at y = 59
        lantern_post(p, s * 24, -34, rz=0 if s > 0 else math.pi)
    arch(p, 0, 62, FLOOR_Z, 60, 58, rz=0.0, thick=6)
    meadow_dress(p, (-66, -60, 36), trees=4, blossom=20, tufts=8)
    meadow_dress(p, (66, -60, 36), trees=4, blossom=20, tufts=8)


def es_temple_gate_b(p):
    """The rare gate-court: a propylaeum -- a columned, roofed gate hall the road passes through."""
    base(p)
    connect(p, hub=(0, -40))
    for s in (-1, 1):
        for k in range(5):
            column(p, s * 30, 6 + k * 16, FLOOR_Z, 30, r=2.8)
    prism(p, [(-36, 0), (36, 0), (36, 76), (-36, 76)], 30, 33, "TempleIvory", side="TempleGold")
    verts = [(-38, -2, 33), (38, -2, 33), (38, 78, 33), (-38, 78, 33), (0, -2, 46), (0, 78, 46)]
    p.add(verts, [[0, 1, 4], [2, 3, 5], [1, 2, 5, 4], [3, 0, 4, 5]], "TempleGold")
    for k in range(6):
        beam(p, "TempleIvory", (-38, k * 15.6, 33.2), (0, k * 15.6, 46.2), 0.8, 0.8)
        beam(p, "TempleIvory", (38, k * 15.6, 33.2), (0, k * 15.6, 46.2), 0.8, 0.8)
    decal_ring(p, "PortalGlow", 0, 38, 10, 11, FLOOR_Z + 0.07, n=16)
    crystal_colossus(p, -72, -52)
    crystal_colossus(p, 72, -52, top=118)
    meadow_dress(p, (-70, 60, 30), trees=3, blossom=16, tufts=8)
    meadow_dress(p, (70, 60, 30), trees=3, blossom=16, tufts=8)


# ---------------------------------------------------------------------------
# SIDE pockets and CAPs
# ---------------------------------------------------------------------------
def es_side_hermit_grove(p):
    base(p)
    connect(p, hub=(0, 10))
    hut(p, 0, 36, rz=math.pi / 2)
    great_tree(p, -52, 44)
    meadow_dress(p, (40, 40, 44), trees=6, blossom=30, tufts=12, mush=6)
    lantern_post(p, 10, 22, rz=0.4)


def es_side_crystal_grotto(p):
    base(p)
    connect(p, hub=(0, 0))
    crag(p, 0, 56, r=30)
    for k in range(6):
        a = math.pi + 0.3 + k * 0.5
        crystal_cluster(p, math.cos(a) * 30 + 0, 56 + math.sin(a) * 30 - 6, s=1.2, n=5)
    aether_pool(p, 40, -30, 16)
    meadow_dress(p, (-60, -40, 34), trees=3, blossom=24, tufts=8)


def es_side_relic_altar(p):
    base(p)
    connect(p, hub=(0, 0))
    pavilion(p, 0, 34, FLOOR_Z, 16, 14, 12, rz=0.0)
    for s in (-1, 1):
        waystone(p, s * 18, 12, rz=0.2 * s)
    crystal_colossus(p, -60, 60)
    meadow_dress(p, (60, 20, 40), trees=5, blossom=30, tufts=10, mush=3)


def es_cap_broken_bridge(p):
    """A plank bridge that runs out over a rift and snaps; a lone crag stands in the void."""
    base(p, holes=[(0, 50, 86)], skip_banks=("N",))
    connect(p, hub=(0, -40), inner=50)
    plank_bridge(p, (0, -40), (0, 18), width=16)
    for k in range(4):                                      # the broken end: planks hanging at angles
        rod(p, "SoftWood", (-5 + k * 3.3, 18, -0.5), (-7 + k * 4, 22 + k * 0.5, -6 - k * 3), 0.5, 0.5, n=4)
    crag(p, 0, 74, z=-92, r=24, top=CROWN_TOP)
    rift_rim(p, 0, 50, 86)
    for s in (-1, 1):
        guide_stone(p, s * 12, -44, FLOOR_Z)
    meadow_dress(p, (-72, -80, 30), trees=3, blossom=16, tufts=8)
    meadow_dress(p, (72, -80, 30), trees=3, blossom=16, tufts=8)


def es_cap_overlook(p):
    base(p, density=0.6)
    connect(p, hub=(0, -30))
    mesa(p, 0, 42, 58, top=10, sx=1.2)
    ramp(p, (0, -22), (0, -2), 14, FLOOR_Z, 10)
    balustrade(p, ring_pts(0, 42, 46, 18, sx=1.2), 10, gaps=[(0, -4, 12)])   # inside the rim, never over the edge
    great_tree(p, -20, 52, z=10)                               # roots wholly inside the balustrade
    box(p, "TempleIvory", 20, 70, 11.2, 14, 3, 1.2)
    box(p, "TempleIvory", 15, 70, 10.6, 1.4, 2.6, 1.2)
    box(p, "TempleIvory", 25, 70, 10.6, 1.4, 2.6, 1.2)
    lantern_post(p, 34, 62, z=10, rz=2.0)
    blossoms(p, 10, 40, 40, 30, z=10)


def es_cap_sealed_shrine(p):
    """A crag cliff with a sealed shrine door set into its face: gold ring, a glowing seal."""
    base(p)
    connect(p, hub=(0, -20))
    n0 = len(p.verts)
    crag(p, 0, 62, r=32, ledges=True)
    # seat the door IN the crag's real south face (its outline is jittered, so measure it, don't guess)
    face = min((v.y for v in p.verts[n0:] if abs(v.x) < 9 and 1 < v.z < 26), default=30.0)
    fy = face + 2.0
    box(p, "TempleIvory", 0, fy, 12, 22, 5, 24)
    box(p, "TempleGold", 0, fy - 2.6, 12, 16, 1.0, 20)
    box(p, "PortalGlow", 0, fy - 3.4, 11, 12, 0.6, 16)
    rod(p, "TempleGold", (0, fy - 3.3, 11), (0, fy - 3.9, 11), 5, 5, n=12)
    for s in (-1, 1):
        waystone(p, s * 20, 8, rz=0.2 * s)
        lantern_post(p, s * 14, -6, rz=0 if s > 0 else math.pi)
    meadow_dress(p, (-70, -60, 34), trees=4, blossom=20, tufts=8)
    meadow_dress(p, (70, -60, 34), trees=4, blossom=20, tufts=8)


# ---------------------------------------------------------------------------
# The kit table: id, role, half-footprint, sockets, builder, and content metadata.
# ---------------------------------------------------------------------------
S, C = "SPAN", "COMMUNION"
PIECES = [
    dict(id="ES_ENTRY", role="ENTRY", half=192, sockets=[("N", S)], fn=es_entry,
         weight=1, max=1, tags=["arrival", "low-density"], enemies=["AETHER_WISP"],
         desc="Arrival Meadow: gold mosaic landing, crystal-topped spawn columns, a shrine mesa, a great sky tree."),
    dict(id="ES_PATH_MEADOW_WALK", role="PATH", half=128, sockets=[("S", S), ("N", S)], fn=es_meadow_walk,
         weight=26, supports=["Combat", "Traversal", "Ambush"], tags=["meadow"], enemies=["MEADOW_STAG", "AETHER_WISP"],
         desc="A lantern-lined golden path across a meadow, a great tree and a small tree mesa beside it."),
    dict(id="ES_PATH_RUIN_STAIR", role="PATH", half=128, sockets=[("S", S), ("N", S)], fn=es_ruin_stair,
         weight=16, supports=["Combat", "Traversal", "Ambush", "Secret"], tags=["ruin", "stair"], enemies=["TEMPLE_ACOLYTE"],
         desc="Up onto a ruined temple terrace, under a colossal gate, and down again."),
    dict(id="ES_PATH_RIFT_BRIDGE", role="PATH", half=128, sockets=[("S", S), ("N", S)], fn=es_rift_bridge,
         weight=14, supports=["Traversal", "Ambush"], tags=["bridge", "rift", "exposed"], enemies=["SKYBORNE_HARRIER"],
         desc="A gold plank bridge over a rift in the cloud, beside a crag rising from the depths."),
    dict(id="ES_PATH_CRYSTAL_FIELD", role="PATH", half=128, sockets=[("S", S), ("N", S)], fn=es_crystal_field,
         weight=16, supports=["Combat", "Ambush", "Secret"], tags=["crystal"], enemies=["CRYSTAL_WARDEN"],
         desc="A field of sky-crystal clusters under a crystal colossus."),
    dict(id="ES_PATH_LILY_TERRACES", role="PATH", half=128, sockets=[("S", S), ("N", S)], fn=es_lily_terraces,
         weight=14, supports=["Combat", "Traversal", "Treasure"], tags=["mesa"], enemies=["MEADOW_STAG"],
         desc="Low meadow mesas stepping away from the path; a crag rises from the highest."),
    dict(id="ES_PATH_BEND_EAST_GROVE", role="PATH", half=128, sockets=[("S", S), ("E", S)], fn=es_bend_east_grove,
         weight=12, supports=["Combat", "Ambush"], tags=["bend", "grove"], enemies=["MEADOW_STAG"],
         desc="A bend under an ancient grove, a fairy ring of gold mushrooms in the corner."),
    dict(id="ES_PATH_BEND_EAST_TERRACE", role="PATH", half=128, sockets=[("S", S), ("E", S)], fn=es_bend_east_terrace,
         weight=12, supports=["Combat", "Traversal"], tags=["bend", "mesa"], enemies=["TEMPLE_ACOLYTE"],
         desc="A bend below a bell-tower mesa reached by a lantern-lit ramp."),
    dict(id="ES_PATH_BEND_WEST_SHRINE", role="PATH", half=128, sockets=[("S", S), ("W", S)], fn=es_bend_west_shrine,
         weight=12, supports=["Combat", "Shrine"], tags=["bend", "shrine"], enemies=["TEMPLE_ACOLYTE"],
         desc="A bend past a waystone-ringed pavilion and a bell tower."),
    dict(id="ES_PATH_BEND_WEST_FALLS", role="PATH", half=128, sockets=[("S", S), ("W", S)], fn=es_bend_west_falls,
         weight=12, supports=["Combat", "Traversal", "Event"], tags=["bend", "falls"], enemies=["CRYSTAL_WARDEN"],
         desc="A bend below Aether Falls: a mesa's rim spills glowing water into a pool."),
    dict(id="ES_FORK_WAYSHRINE", role="PATH", half=128, sockets=[("S", S), ("E", S), ("W", S)], fn=es_fork_wayshrine,
         weight=4, max=1, supports=["Combat", "Shrine", "Event"], tags=["fork"], enemies=["AETHER_WISP"],
         desc="A three-way fork round a waystone circle and a signpost, a great tree behind."),
    dict(id="ES_FORK_THREE_TREES", role="PATH", half=128, sockets=[("S", S), ("N", S), ("E", S)], fn=es_fork_three_trees,
         weight=4, max=1, supports=["Combat", "Ambush"], tags=["fork", "grove"], enemies=["MEADOW_STAG"],
         desc="A three-way fork under three ancient trees and a mushroom ring."),
    dict(id="ES_CONVERGENCE", role="PATH", half=128, sockets=[("N", S), ("S", S), ("E", S), ("W", S)], fn=es_convergence,
         weight=2, max=1, supports=["Combat", "Traversal", "Event"], tags=["crossroads"], enemies=[],
         desc="The crossroads: a compass court with a fountain, eight lanterns, four golden roads."),
    dict(id="ES_MEADOW_OF_BLOOMS", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_meadow_of_blooms,
         weight=12, supports=["Combat", "MiniBoss", "Ambush", "Treasure"], tags=["meadow", "open"], enemies=["MEADOW_STAG"],
         desc="An open meadow drifted with glowing blossoms under a great tree."),
    dict(id="ES_TERRACED_GARDENS", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_terraced_gardens,
         weight=10, supports=["Combat", "Traversal", "Puzzle"], tags=["mesa", "garden"], enemies=["MEADOW_STAG"],
         desc="Two garden mesas of soil rows and mushrooms, a crag above the higher."),
    dict(id="ES_CRYSTAL_HOLLOW", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_crystal_hollow,
         weight=10, supports=["Combat", "Puzzle", "Secret"], tags=["crystal", "pool"], enemies=["CRYSTAL_WARDEN"],
         desc="An aether pool ringed by crystal clusters; a crystal colossus stands over it."),
    dict(id="ES_FALLEN_COLONNADE", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_fallen_colonnade,
         weight=10, supports=["Combat", "MiniBoss", "Secret"], tags=["ruin"], enemies=["TEMPLE_ACOLYTE"],
         desc="An old temple floor, its colonnade half fallen, its bell tower still standing."),
    dict(id="ES_MIRROR_POOL", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_mirror_pool,
         weight=10, supports=["Combat", "Puzzle", "Shrine"], tags=["pool"], enemies=["TEMPLE_ACOLYTE"],
         desc="A balustraded mirror pool crossed on stepping stones, a crag beyond."),
    dict(id="ES_SHRINE_OF_WINDS", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_shrine_of_winds,
         weight=10, supports=["Combat", "Shrine", "Event"], tags=["shrine"], enemies=["TEMPLE_ACOLYTE"],
         desc="Three pavilions round an orb altar, a bell tower over them."),
    dict(id="ES_ROOTED_HOLLOW", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_rooted_hollow,
         weight=10, supports=["Combat", "Ambush", "Secret"], tags=["grove"], enemies=["MEADOW_STAG"],
         desc="A great tree whose roots arch over the path, mushrooms in its shade."),
    dict(id="ES_TWIN_MESAS", role="COMBAT", half=128, sockets=[("S", S), ("N", S)], fn=es_twin_mesas,
         weight=10, supports=["Combat", "Traversal", "MiniBoss"], tags=["mesa", "bridge"], enemies=["SKYBORNE_HARRIER"],
         desc="Two mesas flank the path, joined over it by a high plank bridge."),
    dict(id="ES_TEMPLE_GATE_A", role="COMBAT", half=128, sockets=[("S", S), ("N", C)], fn=es_temple_gate_a,
         weight=20, supports=["Combat", "MiniBoss"], tags=["gate-court"], enemies=["GATEWARDEN"],
         desc="Gate-court: bell towers flank the arch over the COMMUNION road; waystones line it."),
    dict(id="ES_TEMPLE_GATE_B", role="COMBAT", half=128, sockets=[("S", S), ("N", C)], fn=es_temple_gate_b,
         weight=10, supports=["Combat", "MiniBoss"], tags=["gate-court", "rare"], enemies=["GATEWARDEN"],
         desc="Gate-court, rare: a columned gate hall the road passes through, crystal colossi either side."),
    dict(id="ES_SIDE_HERMIT_GROVE", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_hermit_grove,
         weight=6, supports=["Combat", "Secret", "Treasure"], tags=["side", "grove"], enemies=[],
         desc="A hermit's hut in a grove under a great tree."),
    dict(id="ES_SIDE_CRYSTAL_GROTTO", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_crystal_grotto,
         weight=6, supports=["Combat", "Puzzle", "Secret"], tags=["side", "crystal"], enemies=["CRYSTAL_WARDEN"],
         desc="A crag with crystal clusters crowding its foot, an aether pool."),
    dict(id="ES_SIDE_RELIC_ALTAR", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_relic_altar,
         weight=6, supports=["Combat", "Treasure", "MiniBoss"], tags=["side", "treasure"], enemies=["RELIQUARY_KEEPER"],
         desc="A pavilion altar holding a golden orb, a crystal colossus behind."),
    dict(id="ES_CAP_BROKEN_BRIDGE", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_broken_bridge,
         weight=1, tags=["cap", "dead-end"], enemies=[],
         desc="A plank bridge that snaps over a rift; a lone crag stands in the void."),
    dict(id="ES_CAP_OVERLOOK", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_overlook,
         weight=1, tags=["cap", "dead-end", "lookout"], enemies=[],
         desc="A balustraded mesa lookout with a sky seat under a great tree."),
    dict(id="ES_CAP_SEALED_SHRINE", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_sealed_shrine,
         weight=1, tags=["cap", "dead-end", "sealed"], enemies=[],
         desc="A shrine door sealed in a crag's face, its seal still glowing."),
    dict(id="ES_SANCTUM", role="BOSS", half=256, sockets=[("S", C)], fn=es_sanctum,
         weight=1, max=1, tags=["arena"], enemies=["THE_ASCENDANT"],
         desc="The Sanctum: a grand temple that houses the boss -- portico, crystal windows, an open hall, four towers."),
]
assert len(PIECES) == 30
