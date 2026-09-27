# Ethereal Scape kit -- the 36 HYBRID piece recipes (owner pick 2026-09-27). docs/biomes/ETHEREAL_SCAPE.md
# has the table. Blender +Y is NORTH.
#
# Every walkable piece is an ISLAND WEB (es_isles.py): named isles at their own heights, joined by gold
# plank bridges (level or sloped), the standard landing on every mouth. Temple architecture carries the
# combat rooms, the two miniboss arenas and the Sanctum; meadow dressing carries the rest. Three BACKDROP
# pieces -- cloud banks, drifting isles, a crystal spire -- have no sockets: the §7.7 generator rings
# them round a finished map so it never ends at a bare horizon.
import math

from mathutils import Vector

from es_features import (FLOOR_Z, aether_pool, arch, balustrade, bell_tower, blossoms, column, crag, crystal_cluster,
                         crystal_colossus, flagstones, fountain, grass_tufts, great_tree, hut, lantern_post, meadow_carpet,
                         mesa, mushroom, near_corridor, path, pavilion, pins, puff, ramp, rock, ruin_wall, stairs, tree,
                         waystone)
from es_geometry import CROWN_TOP, DIRS, KIND_WIDTH, beam, blob, box, decal, decal_ring, decal_strip, frustum, gem, prism, ring_pts, rod
from es_isles import (bridge, circle, face, inside, isle, landing, rsquare, shrine_hall, sky_spire, statue)

TEAL, INDIGO = "DeepTealLeaves", "IndigoLeaves"


# ---------------------------------------------------------------------------
# shared compositions (hub_plaza / scatter / plank_bridge / aether_fall / meadow_dress are also used by
# the direction samples)
# ---------------------------------------------------------------------------
def hub_plaza(p, x, y, r, star=True, z=FLOOR_Z):
    decal(p, "GoldenPath", ring_pts(x, y, r, 18), z + 0.04)
    decal_ring(p, "TempleGold", x, y, r - 1.5, r, z + 0.06, n=18)
    decal_ring(p, "CloudWhite", x, y, r * 0.55, r * 0.6, z + 0.06, n=18)
    if star:
        for k in range(8):
            a = k * math.pi / 4
            tip = r * (0.95 if k % 2 == 0 else 0.7)
            decal(p, "TempleGold" if k % 2 == 0 else "CloudWhite",
                  [(x + math.cos(a - 0.12) * r * 0.2, y + math.sin(a - 0.12) * r * 0.2),
                   (x + math.cos(a) * tip, y + math.sin(a) * tip),
                   (x + math.cos(a + 0.12) * r * 0.2, y + math.sin(a + 0.12) * r * 0.2)], z + 0.07)
        decal(p, "PortalGlow", ring_pts(x, y, r * 0.16, 10), z + 0.08)


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
        if abs(x) > p.H - 44 or abs(y) > p.H - 44:
            continue
        own = kw.get("clear", 4.0)
        if any(math.hypot(x - ax, y - ay) < ar + own for ax, ay, ar in list(avoid) + placed + p.keepout):
            continue
        if clear_paths and near_corridor(p, x, y, kw.get("clear", 4.0)):
            continue
        fn(p, x, y, **{k: v for k, v in kw.items() if k != "clear"})
        placed.append((x, y, 2.0))
    return placed


def plank_bridge(p, a, b, width=20.0, z=FLOOR_Z):
    bridge(p, a, b, z - 0.06, z - 0.06, width)


def aether_fall(p, x, y, z_top, out_dir, width=12.0, drop=None, z_bottom=FLOOR_Z, pool=True):
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
    if not pool:                       # off an isle's rim the water simply falls away into the cloud
        return
    fx, fy = x + dx * 9, y + dy * 9
    aether_pool(p, fx + dx * 6, fy + dy * 6, 11, z_bottom)
    for k in range(3):
        puff(p, fx + dx * 6 + p.rng.uniform(-6, 6), fy + dy * 6 + p.rng.uniform(-6, 6), z_bottom - 1, 4, 3, p.rng)


def meadow_dress(p, region, trees=6, blossom=40, tufts=16, mush=4, avoid=(), crowns=(TEAL, INDIGO), z=FLOOR_Z):
    rng = p.rng
    if z == FLOOR_Z and trees:
        meadow_carpet(p, region[0], region[1], region[2] * 0.9)
    scatter(p, lambda p_, x, y: tree(p_, x, y, z=z, h=rng.uniform(16, 26), crown=crowns[rng.randrange(len(crowns))],
                                    style=rng.randrange(3)), trees, region, avoid=avoid, clear=8)
    scatter(p, lambda p_, x, y: mushroom(p_, x, y, z=z, s=rng.uniform(0.8, 1.6)), mush, region, avoid=avoid, clear=3)
    cx, cy, r = region
    blossoms(p, cx, cy, r, blossom, z=z, avoid=avoid)
    grass_tufts(p, cx, cy, r, tufts, z=z, avoid=avoid)


# ---------------------------------------------------------------------------
# the island web
# ---------------------------------------------------------------------------
def web(p, nodes, links, width=16.0):
    """Build named isles, then bridge every link. `nodes`: name -> (x, y, r, z) or a dict with
    x/y/r/z and optional `pts` (an explicit outline) plus isle() kwargs. A link end may be a
    cardinal: it lands on that mouth's landing (built here, at the socket's lift). Asserts the
    layout is sane -- isles clear of each other and of every landing -- so a bad coordinate
    fails at build time, not in the renders."""
    H = p.H
    built = {}
    for name, spec in nodes.items():
        if not isinstance(spec, dict):
            x, y, r, z = spec
            spec = dict(x=x, y=y, r=r, z=z)
        spec = dict(spec)
        pts = spec.pop("pts", None) or circle(p, spec["x"], spec["y"], spec["r"], sides=spec.pop("sides", 12))
        kw = {k: spec[k] for k in ("depth", "floor", "roots", "chandelier", "skirt") if k in spec}
        isle(p, pts, spec["z"], **kw)
        built[name] = dict(x=spec["x"], y=spec["y"], r=spec["r"], z=spec["z"], pts=pts)
    names = list(built)
    for n_ in built.values():                   # the real reach of each outline, rim included
        n_["reach"] = 1.04 * max(math.hypot(x - n_["x"], y - n_["y"]) for x, y in n_["pts"])
    for i, a in enumerate(names):
        A = built[a]
        for b in names[i + 1:]:
            B = built[b]
            gap = math.hypot(A["x"] - B["x"], A["y"] - B["y"]) - (A["reach"] + B["reach"])
            assert gap > 2, f"{p.name}: isles {a} and {b} overlap ({gap:.1f})"
        for card, kind in p.sockets:
            dx, dy = DIRS[card]
            for x, y in A["pts"]:
                x, y = A["x"] + (x - A["x"]) * 1.04, A["y"] + (y - A["y"]) * 1.04
                along, lateral = x * dx + y * dy, abs(x * -dy + y * dx)
                if along > H - 36 and lateral < KIND_WIDTH[kind] / 2 + 9:
                    raise AssertionError(f"{p.name}: isle {a} runs into the {card} landing")
    for card, _kind in p.sockets:
        landing(p, card, p.lift.get(card, FLOOR_Z))
    for a, b in links:
        ends = []
        for end, other in ((a, b), (b, a)):
            if end in DIRS:
                dx, dy = DIRS[end]
                ends.append(((dx * (H - 30), dy * (H - 30)), p.lift.get(end, FLOOR_Z), (dx * (H - 34), dy * (H - 34))))
            else:
                N = built[end]
                ox, oy = _centre(built, other, H)
                d = math.hypot(ox - N["x"], oy - N["y"])
                ux, uy = (ox - N["x"]) / d, (oy - N["y"]) / d
                t = 0.0                       # walk out to the outline's edge, then back 5 studs onto it
                while inside(N["pts"], N["x"] + ux * (t + 1), N["y"] + uy * (t + 1)):
                    t += 1
                edge = (N["x"] + ux * t, N["y"] + uy * t)
                t = max(4.0, t - 5.0)
                ends.append(((N["x"] + ux * t, N["y"] + uy * t), N["z"], edge))
        (pa, za, ea), (pb, zb, eb) = ends
        if za == zb:
            bridge(p, pa, pb, za, zb, width)
        else:                                   # the slope spans exactly edge to edge; a level stub lies on
            bridge(p, pa, ea, za, za, width)    # each top -- a deck that dove into a rim was a wall
            bridge(p, ea, eb, za, zb, width)
            bridge(p, eb, pb, zb, zb, width)
    p.nodes = built
    return built


def _centre(built, name, H):
    if name in DIRS:
        dx, dy = DIRS[name]
        return dx * (H - 17), dy * (H - 17)
    return built[name]["x"], built[name]["y"]


def at(n, dx=0.0, dy=0.0):
    """A point on isle n, offset from its centre."""
    return n["x"] + dx, n["y"] + dy


def dress(p, n, trees=4, blossom=30, tufts=10, mush=3, avoid=(), crowns=(TEAL, INDIGO), carpet=False):
    """Meadow dressing that stands ON isle n: every tree and mushroom is checked inside its outline."""
    rng = p.rng
    x0, y0, r, z, pts = n["x"], n["y"], n["r"], n["z"], n["pts"]
    if carpet:
        meadow_carpet(p, x0, y0, r * 0.7, z=z + 0.02)

    def put(fn, count, clear):
        got, tries = 0, 0
        while got < count and tries < count * 60:
            tries += 1
            a, rr = rng.uniform(0, 6.28), r * 0.85 * math.sqrt(rng.random())
            x, y = x0 + math.cos(a) * rr, y0 + math.sin(a) * rr
            if not inside(pts, x, y, clear + 1.5):
                continue
            if any(math.hypot(x - ax, y - ay) < ar + clear for ax, ay, ar in list(avoid) + p.keepout):
                continue
            if near_corridor(p, x, y, clear):
                continue
            if abs(x) > p.H - clear - 2 or abs(y) > p.H - clear - 2:
                continue
            fn(x, y)
            got += 1

    put(lambda x, y: tree(p, x, y, z=z, h=rng.uniform(15, 25), crown=crowns[rng.randrange(len(crowns))],
                          style=rng.randrange(3)), trees, 8)
    put(lambda x, y: mushroom(p, x, y, z=z, s=rng.uniform(0.8, 1.6)), mush, 3)
    put(lambda x, y: rock(p, x, y, z=z, s=rng.uniform(1.2, 2.4)), max(1, trees // 2), 3)
    blossoms(p, x0, y0, r * 0.66, blossom, z=z, avoid=avoid)
    grass_tufts(p, x0, y0, r * 0.66, tufts, z=z, avoid=avoid)


def road(p, pts, z=FLOOR_Z, width=12):
    path(p, pts, width=width, z=z)


def temple_floor(p, n, inset=0.82):
    """An ivory flagstone court laid on isle n -- the temple language (sample C)."""
    x0, y0, z = n["x"], n["y"], n["z"]
    pts = [(x0 + (x - x0) * inset, y0 + (y - y0) * inset) for x, y in n["pts"]]
    decal(p, "TempleIvory", pts, z + 0.08)
    decal(p, "TempleGold", [(x0 + (x - x0) * (inset + 0.03), y0 + (y - y0) * (inset + 0.03)) for x, y in n["pts"]], z + 0.04)
    for gy in range(int(y0 - n["r"]), int(y0 + n["r"]), 8):     # course seams, only where the court is
        if inside(pts, x0 - n["r"] * 0.55, gy, 1) and inside(pts, x0 + n["r"] * 0.55, gy, 1):
            decal_strip(p, "CloudWhite", (x0 - n["r"] * 0.55, gy), (x0 + n["r"] * 0.55, gy), 0.35, z + 0.12)


# ---------------------------------------------------------------------------
# ENTRY and BOSS
# ---------------------------------------------------------------------------
def es_entry(p):
    """Arrival Isle (384): a great chamfered isle -- the gold mosaic landing ringed by crystal-topped
    spawn columns, the return-portal pad to the south, a shrine terrace to the west, the great sky tree
    to the east, and two perches off its flanks at their own heights."""
    pins(p)
    H = p.H
    n = web(p, {"main": dict(x=0, y=-6, r=150, z=0, pts=rsquare(0, -6, 156, 150, 46, per_edge=4), depth=92),
                "perch_w": (-150, 158, 18, 14), "perch_e": (160, -164, 18, -16)},
            [("main", "N"), ("main", "perch_w"), ("main", "perch_e")])
    m = n["main"]
    hub_plaza(p, 0, 0, 34)
    road(p, [(0, 34), (0, 138)], width=26)
    road(p, [(0, -34), (0, -84)], width=14)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = math.cos(a) * 46, math.sin(a) * 46
        column(p, x, y, FLOOR_Z, 22, r=2.4)
        rod(p, "SkyCrystal", (x, y, FLOOR_Z + 22), (x, y, FLOOR_Z + 30), 1.8, 0.0, n=5)
    decal_ring(p, "TempleGold", 0, -110, 26, 27.5, FLOOR_Z + 0.05, n=24)
    for k in range(10):
        a = k * 0.628
        rock(p, math.cos(a) * 31, -110 + math.sin(a) * 31, s=1.2)
    # west: a raised shrine terrace (mesa) climbed by a ramp
    mesa(p, -96, 52, 40, top=8)
    ramp(p, (-50, 30), (-66, 38), 12, FLOOR_Z, 8)
    pavilion(p, -100, 56, 8, 16, 16, 12, rz=face(-100, 56, 0, 0))
    # east: the great sky tree (crown pin) over a flower meadow and a pool
    great_tree(p, 100, 70, FLOOR_Z, top=CROWN_TOP, trunk=8)
    blossoms(p, 96, 40, 40, 50, avoid=[(100, 70, 22)])
    aether_pool(p, 84, -64, 16)
    for s in (-1, 1):
        for k in range(3):
            lantern_post(p, s * 18, 60 + k * 30, rz=0 if s > 0 else math.pi)
        waystone(p, s * 30, H - 60, rz=0.2 * s)
    meadow_dress(p, (0, 0, 118), trees=10, blossom=50, tufts=20, mush=6,
                 avoid=[(0, 0, 58), (0, -110, 38), (-96, 52, 50), (100, 70, 40), (84, -64, 22)])
    lantern_post(p, *at(n["perch_w"], 2, -4), z=14)
    sky_spire(p, *at(n["perch_e"], 0, -2), z=-16, r=3.6)


def es_sanctum(p):
    """The Sanctum (512): the grand temple that HOUSES the boss, on the greatest isle in the sky. A
    podium climbed by the ceremonial stair, a colonnaded portico, walls of crystal windows between
    pilasters, an open hall under a ribbed roof with a crystal-windowed lantern, and four corner
    towers whose crystal tips pin the crown."""
    pins(p)
    H = p.H
    web(p, {"grounds": dict(x=0, y=0, r=220, z=0, pts=rsquare(0, 12, 238, 222, 70, per_edge=4), depth=92, roots=False)},
        [("grounds", "S")], width=24)
    road(p, [(0, -124), (0, -204)], width=26)
    z = 6.0
    X0, X1, Y0, Y1 = -138.0, 138.0, -110.0, 154.0
    prism(p, [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], FLOOR_Z - 0.5, z, "TempleIvory", side="Cloudstone")
    for (ax, ay), (bx, by) in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
        beam(p, "TempleGold", (ax, ay, z - 1.2), (bx, by, z - 1.2), 1.4, 1.2)
    stairs(p, 0, Y0 - 12, FLOOR_Z, z, 90, math.pi / 2)
    WX, WY0, WY1, T, WH = 124.0, -96.0, 142.0, 4.0, 64.0
    door = 32.0

    def wall(a, b, z0, z1):
        beam(p, "TempleIvory", (a[0], a[1], (z0 + z1) / 2), (b[0], b[1], (z0 + z1) / 2), T, z1 - z0)

    wall((-WX, WY0), (-door, WY0), z, WH)
    wall((door, WY0), (WX, WY0), z, WH)
    wall((-door, WY0), (door, WY0), 50, WH)
    beam(p, "TempleGold", (-door, WY0 - 2.2, 50.5), (door, WY0 - 2.2, 50.5), 1.2, 1.6)
    wall((WX, WY0), (WX, WY1), z, WH)
    wall((WX, WY1), (-WX, WY1), z, WH)
    wall((-WX, WY1), (-WX, WY0), z, WH)
    for sx in (-1, 1):
        y = WY0 + 12
        while y < WY1 - 8:
            box(p, "TempleIvory", sx * (WX + 2.6), y, (z + WH) / 2, 2.6, 4.0, WH - z)
            box(p, "TempleGold", sx * (WX + 2.6), y, WH - 1.0, 3.4, 4.8, 2.0)
            if y + 12 < WY1 - 8:
                box(p, "SkyCrystal", sx * WX, y + 12, 34, T + 0.5, 9, 20)
                box(p, "TempleGold", sx * (WX + 2.2), y + 12, 23.5, 1.0, 11, 1.0)
                box(p, "TempleGold", sx * (WX + 2.2), y + 12, 44.5, 1.0, 11, 1.0)
            y += 24
    x = -WX + 12
    while x < WX - 8:
        box(p, "TempleIvory", x, WY1 + 2.6, (z + WH) / 2, 4.0, 2.6, WH - z)
        if x + 12 < WX - 8:
            box(p, "SkyCrystal", x + 12, WY1, 34, 9, T + 0.5, 20)
        x += 24
    for cx in (-108, -80, -52, 52, 80, 108):
        column(p, cx, WY0 - 8, z, WH - z, r=3.2)
    beam(p, "TempleIvory", (-126, WY0 - 8, WH + 1.5), (126, WY0 - 8, WH + 1.5), 9, 3)
    beam(p, "TempleGold", (-126, WY0 - 12.6, WH + 3.4), (126, WY0 - 12.6, WH + 3.4), 1.0, 1.0)
    p.add([(-100, WY0 - 12, WH + 3), (100, WY0 - 12, WH + 3), (0, WY0 - 12, WH + 24),
           (-100, WY0 - 4, WH + 3), (100, WY0 - 4, WH + 3), (0, WY0 - 4, WH + 24)],
          [[0, 1, 2], [4, 3, 5], [0, 3, 4, 1]], "TempleIvory")
    p.add([(-104, WY0 - 13, WH + 2.6), (0, WY0 - 13, WH + 25.5), (0, WY0 - 3, WH + 25.5), (-104, WY0 - 3, WH + 2.6),
           (104, WY0 - 13, WH + 2.6), (104, WY0 - 3, WH + 2.6)],
          [[0, 1, 2, 3], [1, 4, 5, 2]], "TempleGold")
    gem(p, "PortalGlow", 0, WY0 - 12.2, WH + 12, 4.0, 3.0, 3.0, n=8)
    RZ = WH
    cx0, cy0 = 0.0, (WY0 + WY1) / 2
    hole = 36.0
    for (ax, ay, bx, by) in ((-WX - 2, WY0 - 2, WX + 2, cy0 - hole), (-WX - 2, cy0 + hole, WX + 2, WY1 + 2),
                             (-WX - 2, cy0 - hole, -hole, cy0 + hole), (hole, cy0 - hole, WX + 2, cy0 + hole)):
        prism(p, [(ax, ay), (bx, ay), (bx, by), (ax, by)], RZ, RZ + 4, "TempleGold", side="TempleIvory")
    for k in range(-4, 5):
        if abs(k * 27) > hole + 2:
            beam(p, "SoftWood", (k * 27, WY0, RZ + 4.6), (k * 27, WY1, RZ + 4.6), 2.2, 1.2)
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
    for tx in (-127, 127):
        for ty in (-99, 143):
            frustum(p, "TempleIvory", tx, ty, z - 0.5, 108, 11, 9.5, n=8)
            for zz in (30, 64, 96):
                frustum(p, "TempleGold", tx, ty, zz, zz + 2, 11.2, 11.0, n=8)
            for k in range(8):
                a = k * math.pi / 4 + math.pi / 8
                box(p, "SkyCrystal", tx + math.cos(a) * 9.0, ty + math.sin(a) * 9.0, 82, 0.6, 3, 9, rz=a)
            frustum(p, "TempleGold", tx, ty, 108, 150, 12.5, 0.8, n=8)
            frustum(p, "SkyCrystal", tx, ty, 148, CROWN_TOP, 2.6, 0.0, n=6)
    decal_ring(p, "GoldenPath", cx0, cy0, 64, 70, z + 0.05, n=32)
    decal_ring(p, "PortalGlow", cx0, cy0, 44, 45.5, z + 0.06, n=32)
    decal_ring(p, "TempleGold", cx0, cy0, 20, 22, z + 0.06, n=24)
    decal(p, "PortalGlow", ring_pts(cx0, cy0, 7, 12), z + 0.07)
    for k in range(12):
        a = k * math.pi / 6
        decal_strip(p, "TempleGold", (cx0 + math.cos(a) * 22, cy0 + math.sin(a) * 22),
                    (cx0 + math.cos(a) * 64, cy0 + math.sin(a) * 64), 1.2, z + 0.055)
    # --- the interior (owner 2026-09-27: "the sanctum interior needs a polish and detail pass") -----
    # Everything below keeps out of the fight: the hall is validated clear at |x| <= 109.5,
    # -85.5 <= y <= 119.5, 8.5 <= z <= 57.5, and the great door's span.
    IW = WX - T / 2                              # the walls' inner face
    # engaged pilasters down both side walls and across the north wall, gold bases and capitals
    for sx in (-1, 1):
        y = WY0 + 12
        while y < WY1 - 6:
            box(p, "TempleIvory", sx * (IW - 1.3), y, (z + WH) / 2, 2.6, 4.0, WH - z)
            box(p, "TempleGold", sx * (IW - 1.6), y, z + 1.0, 3.2, 5.0, 2.0)
            box(p, "TempleGold", sx * (IW - 1.6), y, WH - 3.0, 3.2, 5.2, 2.2)
            y += 24
    for x in range(-108, 109, 24):
        if abs(x) > 44:                          # leave the throne wall's centre for the sun disc
            box(p, "TempleIvory", x, WY1 - T / 2 - 1.3, (z + WH) / 2, 4.0, 2.6, WH - z)
            box(p, "TempleGold", x, WY1 - T / 2 - 1.6, WH - 3.0, 5.2, 3.2, 2.2)
    # crystal sconces between the pilasters, set into the side walls
    for sx in (-1, 1):
        y = WY0 + 24
        while y < WY1 - 18:
            box(p, "TempleGold", sx * (IW - 0.9), y, 24, 1.8, 3.0, 1.2)
            gem(p, "PortalGlow", sx * (IW - 1.6), y, 25.2, 1.1, 1.6, 1.0, n=6)
            y += 24
    # guardian statues standing along the side walls, facing the floor
    for sx in (-1, 1):
        for y in (-60, -12, 36, 84):
            if y in (-12, 84):
                statue(p, sx * 114, y + 12, z, rz=face(sx * 114, y + 12, 0, y + 12))
    # a gold-and-ivory border round the floor, and corner mosaics
    for (ax, ay), (bx, by) in (((-104, -88), (104, -88)), ((104, -88), (104, 116)), ((104, 116), (-104, 116)),
                               ((-104, 116), (-104, -88))):
        decal_strip(p, "TempleGold", (ax, ay), (bx, by), 3.0, z + 0.05)
        decal_strip(p, "SkyCrystal", (ax, ay), (bx, by), 0.8, z + 0.08)
    for cx, cy in ((-88, -72), (88, -72), (-88, 100), (88, 100)):
        decal(p, "TempleGold", ring_pts(cx, cy, 9, 8, a0=math.pi / 8), z + 0.05)
        decal(p, "PortalGlow", ring_pts(cx, cy, 4, 8, a0=math.pi / 8), z + 0.08)
    # the coffered ceiling: gold beams hung under the roof, broken round the lantern opening
    for y in range(-84, 133, 24):
        if abs(y - cy0) < hole + 2:
            for sx in (-1, 1):
                beam(p, "TempleGold", (sx * (hole + 2), y, RZ - 1.2), (sx * IW, y, RZ - 1.2), 2.0, 2.4)
        else:
            beam(p, "TempleGold", (-IW, y, RZ - 1.2), (IW, y, RZ - 1.2), 2.0, 2.4)
    for x in (-96, -60, 60, 96):
        beam(p, "SoftWood", (x, WY0 + T / 2, RZ - 1.0), (x, WY1 - T / 2, RZ - 1.0), 1.6, 2.0)
    # four crystal chandeliers hung from the coffers (their lowest point stays above the fight)
    for x in (-60, 60):
        for y in (cy0 - 72, cy0 + 72):
            rod(p, "TempleGold", (x, y, RZ - 0.4), (x, y, 60.5), 0.25, 0.25, n=4)   # hung from the x-beam
            frustum(p, "TempleGold", x, y, 59.4, 60.6, 5.0, 3.2, n=8)
            for k in range(5):
                a = k * math.pi * 0.4
                rod(p, "SkyCrystal", (x + math.cos(a) * 4.0, y + math.sin(a) * 4.0, 59.6),
                    (x + math.cos(a) * 4.4, y + math.sin(a) * 4.4, 58.2), 0.5, 0.0, n=4)
            gem(p, "PortalGlow", x, y, 60.0, 1.8, 1.6, 1.4, n=6)
    # a crystal ring hung inside the lantern, held by four gold rods from its walls
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        rod(p, "TempleGold", (math.cos(a) * (hole - 1.6) * 1.41, cy0 + math.sin(a) * (hole - 1.6) * 1.41, RZ + 22),
            (math.cos(a) * 16, cy0 + math.sin(a) * 16, RZ + 12), 0.3, 0.3, n=4)
    for k in range(8):
        a0, a1 = k * math.pi / 4, (k + 1) * math.pi / 4
        rod(p, "SkyCrystal", (math.cos(a0) * 16, cy0 + math.sin(a0) * 16, RZ + 12),
            (math.cos(a1) * 16, cy0 + math.sin(a1) * 16, RZ + 12), 0.8, 0.8, n=4)
    # --- the throne dais at the north end: three steps, a crystal-backed throne, braziers, a sun disc
    for k, (w_, d_) in enumerate(((96, 30), (72, 22), (44, 14))):
        box(p, "TempleIvory" if k % 2 == 0 else "TempleGold", 0, WY1 - T / 2 - d_ / 2 - 0.5, z + 0.6 + k * 1.2, w_, d_, 1.2 + k * 0.0)
    tz = z + 3.0
    box(p, "TempleGold", 0, WY1 - 12, tz + 1.5, 12, 7, 3.0)                     # the seat
    box(p, "TempleIvory", 0, WY1 - 9.5, tz + 8, 12, 2.0, 13)                    # its back
    gem(p, "SkyCrystal", 0, WY1 - 9.5, tz + 16, 5.0, 9.0, 4.0, n=6)            # a crystal crest rising out of it
    for sx in (-1, 1):
        box(p, "TempleGold", sx * 6.8, WY1 - 12, tz + 4.5, 1.6, 7, 3.0)          # armrests
        bz = z + 2.2                                                           # on the second step
        frustum(p, "TempleIvory", sx * 30, WY1 - 16, bz, bz + 8, 2.4, 1.8, n=8)  # braziers
        frustum(p, "TempleGold", sx * 30, WY1 - 16, bz + 8, bz + 10, 1.8, 3.6, n=8)
        gem(p, "PortalGlow", sx * 30, WY1 - 16, bz + 11.2, 2.4, 3.2, 1.2, n=7)
        p.footings.append((sx * 30, WY1 - 16, bz + 0.2, 2.0, "brazier"))
    # the sun disc on the north wall: a gold wheel with crystal rays, fixed to the wall face
    M_z = 38.0
    wy = WY1 - T / 2 - 0.4
    for k in range(8):
        a = k * math.pi / 4
        beam(p, "SkyCrystal", (math.cos(a) * 11, wy, M_z + math.sin(a) * 11), (math.cos(a) * 22, wy, M_z + math.sin(a) * 22),
             1.6, 0.8)
    for k in range(10):
        a0, a1 = k * math.pi / 5, (k + 1) * math.pi / 5
        beam(p, "TempleGold", (math.cos(a0) * 10, wy, M_z + math.sin(a0) * 10), (math.cos(a1) * 10, wy, M_z + math.sin(a1) * 10),
             2.0, 1.4)
    box(p, "PortalGlow", 0, wy, M_z, 8, 0.8, 8)
    # the great door: gold jambs, and its two leaves swung open against the outer wall
    for sx in (-1, 1):
        box(p, "TempleGold", sx * (door + 1.2), WY0, 28, 2.4, T + 1.2, 44)
        box(p, "SoftWood", sx * (door + 16), WY0 - T / 2 - 0.5, 27, 30, 1.0, 40)
        box(p, "TempleGold", sx * (door + 16), WY0 - T / 2 - 1.1, 27, 22, 0.4, 3)
    for k in range(3):
        y = -142 - k * 26
        for s in (-1, 1):
            lantern_post(p, s * 34, y, rz=0 if s > 0 else math.pi, h=10)
    for s in (-1, 1):
        waystone(p, s * 44, -128, rz=0.2 * s, h=20)
        aether_pool(p, s * 162, -140, 20)
        crystal_cluster(p, s * 190, -84, s=1.4, n=6)
        tree(p, s * 186, 40, h=30, crown=TEAL, style=1)
        tree(p, s * 186, 110, h=26, crown=INDIGO)
        statue(p, s * 60, -150, rz=math.pi / 2 - s * math.pi / 2)
    for s in (-1, 1):
        meadow_carpet(p, s * 100, -174, 32)
        for k in range(3):
            tree(p, s * (86 + k * 20), -190 + (k % 2) * 14, h=22 - k * 2, crown=TEAL if k % 2 else INDIGO, style=k % 3)
        blossoms(p, s * 100, -174, 28, 12)


# ---------------------------------------------------------------------------
# PATH: straights (two of them climb or descend a full storey)
# ---------------------------------------------------------------------------
def es_plank_crossing(p):
    pins(p)
    n = web(p, {"a": (-10, -50, 28, 0), "b": (24, 10, 28, 8), "c": (-8, 62, 24, 0), "perch": (-82, 4, 18, -10)},
            [("S", "a"), ("a", "b"), ("b", "c"), ("c", "N"), ("b", "perch")])
    pavilion(p, *at(n["b"], 8, 4), 8, 12, 12, 10, rz=face(*at(n["b"], 8, 4), *at(n["b"])))
    for k, (dx, dy) in enumerate(((-12, -6), (8, 8))):
        tree(p, *at(n["a"], dx, dy), h=20 + k * 4, crown=TEAL if k else INDIGO, style=k)
    dress(p, n["a"], trees=1, blossom=16, tufts=6, mush=2)
    for s in (-1, 1):
        lantern_post(p, *at(n["c"], s * 11, -2), rz=0 if s > 0 else math.pi)
    waystone(p, *at(n["c"], 0, 12), rz=0.2)
    sky_spire(p, *at(n["perch"], 0, 0), z=-10, r=3.6)


def es_grove_isle(p):
    pins(p)
    n = web(p, {"g": dict(x=0, y=0, r=72, z=0, sides=16)}, [("S", "g"), ("g", "N")])
    g = n["g"]
    road(p, [(0, -50), (10, -10), (-6, 30), (0, 50)], width=12)
    great_tree(p, -36, 14, trunk=7)
    decal_ring(p, "TempleGold", 34, -28, 9, 10, 0.05, n=12)          # the fairy ring
    for k in range(9):
        a = k * 0.7
        mushroom(p, 34 + math.cos(a) * 11, -28 + math.sin(a) * 11, s=1.3)
    dress(p, g, trees=7, blossom=60, tufts=20, mush=4, avoid=[(-36, 14, 24), (34, -28, 14)], carpet=True)
    aether_fall(p, 66, 20, -1.4, (1, 0.1), width=10, drop=70, pool=False)
    for s in (-1, 1):
        lantern_post(p, s * 14, -64 + 10, rz=0 if s > 0 else math.pi)


def es_skystair_up(p):
    """A full storey UP (+24): three isles climbing west then back, a shrine arch at the top."""
    pins(p)
    n = web(p, {"a": (0, -60, 26, 0), "b": (-36, 6, 28, 12), "c": (14, 62, 26, 24)},
            [("S", "a"), ("a", "b"), ("b", "c"), ("c", "N")])
    for k in range(3):
        column(p, *at(n["a"], 12 + k * 4, 8 - k * 5), 0, 14 + k * 4, broken=k != 1)
    great_tree(p, *at(n["b"], -8, 4), z=12, trunk=6)
    arch(p, *at(n["c"], -2, 6), 24, 26, 22, rz=math.atan2(40, -14), thick=4)
    for s in (-1, 1):
        lantern_post(p, *at(n["c"], s * 14, -6), z=24)
    dress(p, n["a"], trees=1, blossom=18, tufts=8, mush=2)


def es_skystair_down(p):
    """A full storey DOWN (-24): three isles stepping east into the cloud, a crystal colossus on the
    middle one."""
    pins(p)
    n = web(p, {"a": (0, -60, 26, 0), "b": (36, 6, 28, -12), "c": (-14, 62, 26, -24)},
            [("S", "a"), ("a", "b"), ("b", "c"), ("c", "N")])
    crystal_colossus(p, *at(n["b"], 10, 2), z=-12, spread=12)
    pavilion(p, *at(n["c"], -8, 6), -24, 11, 11, 9, rz=face(*at(n["c"], -8, 6), *at(n["c"])), roof="slab")
    dress(p, n["a"], trees=3, blossom=20, tufts=8, mush=2)
    dress(p, n["c"], trees=1, blossom=12, tufts=6, mush=2, avoid=[(n["c"]["x"] - 8, n["c"]["y"] + 6, 10)])


# ---------------------------------------------------------------------------
# PATH: bends (one climbs, one descends)
# ---------------------------------------------------------------------------
def es_bend_east_grove(p):
    pins(p)
    n = web(p, {"a": (-18, -28, 44, 0), "perch": (-52, 70, 24, 14)}, [("S", "a"), ("a", "E"), ("a", "perch")])
    great_tree(p, *at(n["perch"], 0, 2), z=14, trunk=6)
    for k in range(8):
        a = k * 0.78
        mushroom(p, -40 + math.cos(a) * 8, -44 + math.sin(a) * 8, s=1.2)
    dress(p, n["a"], trees=5, blossom=40, tufts=14, mush=3, avoid=[(-40, -44, 12)], carpet=True)


def es_bend_east_ascent(p):
    """Bend and climb (+16): a ruined stair isle, a bell-tower isle over the east mouth, a hut perch."""
    pins(p)
    n = web(p, {"a": (-8, -50, 30, 0), "b": (40, 22, 32, 16), "hut": (-62, 44, 22, 24)},
            [("S", "a"), ("a", "b"), ("b", "E"), ("a", "hut")])
    bell_tower(p, *at(n["b"], -6, 16), z=16, w=12, rz=0.3)
    for k in range(3):
        column(p, *at(n["a"], 14, -10 + k * 7), 0, 10 + k * 5, broken=True)
    waystone(p, *at(n["a"], -14, -6), rz=0.4)
    hut(p, *at(n["hut"], 0, 2), z=24, rz=face(*at(n["hut"], 0, 2), *at(n["a"])))
    dress(p, n["a"], trees=1, blossom=14, tufts=6, mush=2)


def es_bend_west_falls(p):
    """Bend and descend (-16): aether falls pour off the upper isle past the path to a pool isle."""
    pins(p)
    n = web(p, {"a": (10, -44, 32, 0), "b": (-40, 26, 30, -16), "c": (62, 52, 22, 10)},
            [("S", "a"), ("a", "b"), ("b", "W"), ("a", "c")])
    aether_fall(p, 38, -38, -1.4, (0.95, -0.3), width=9, drop=60, pool=False)
    sky_spire(p, *at(n["a"], -12, -10), r=4)
    pavilion(p, *at(n["c"], 2, 2), 10, 11, 11, 9, rz=face(*at(n["c"], 2, 2), *at(n["a"])))
    aether_pool(p, *at(n["b"], -6, 10), 12, z=-16)
    dress(p, n["b"], trees=2, blossom=18, tufts=6, mush=2, avoid=[(n["b"]["x"] - 6, n["b"]["y"] + 10, 14)])


def es_bend_west_shrine(p):
    pins(p)
    n = web(p, {"a": dict(x=0, y=-2, r=62, z=0, sides=14)}, [("S", "a"), ("a", "W")])
    road(p, [(0, -60), (0, -12), (-12, 0), (-60, 0)], width=12)
    shrine_hall(p, 22, 22, 0, 22, 18, rz=face(22, 22, 0, 0))
    sky_spire(p, -30, 32, r=4)
    for a in (4.1, 4.7, 5.3):
        waystone(p, math.cos(a) * 40, -2 + math.sin(a) * 40 + 4, rz=a)
    dress(p, n["a"], trees=3, blossom=30, tufts=10, mush=2, avoid=[(22, 22, 30), (-30, 32, 12)])


# ---------------------------------------------------------------------------
# PATH: junctions -- every mouth of these is filled by the §7.7 generator
# ---------------------------------------------------------------------------
def es_fork_wayshrine(p):
    pins(p)
    n = web(p, {"hub": (0, -6, 50, 0), "rear": (0, 82, 24, 14)}, [("S", "hub"), ("hub", "E"), ("hub", "W"), ("hub", "rear")])
    hub_plaza(p, 0, -6, 20)
    for a in (0.6, 1.4, 2.5, 3.9, 5.5):
        waystone(p, math.cos(a) * 32, -6 + math.sin(a) * 32, rz=a, h=14)
    beam(p, "SoftWood", (-18, 18, 0), (-18, 18, 9), 0.8, 0.8)                     # the signpost
    for k, a in enumerate((0.0, 3.14, -1.57)):
        box(p, "TempleGold", -18 + math.cos(a) * 3, 18 + math.sin(a) * 3, 7 - k * 1.2, 6, 1.4, 1.0, rz=a)
    great_tree(p, *at(n["rear"], 0, 4), z=14, trunk=6)
    dress(p, n["hub"], trees=2, blossom=24, tufts=8, mush=2, avoid=[(0, -6, 36), (-18, 18, 5)])


def es_fork_three_trees(p):
    pins(p)
    n = web(p, {"hub": (-10, 0, 52, 0), "crag": (-86, -44, 22, -12)},
            [("S", "hub"), ("hub", "N"), ("hub", "E"), ("hub", "crag")])
    for k, (dx, dy) in enumerate(((-24, 18), (16, 28), (-26, -22))):
        tree(p, *at(n["hub"], dx, dy), h=34 - k * 3, crown=(TEAL, INDIGO)[k % 2], style=k)
    for k in range(10):
        a = k * 0.63
        mushroom(p, -10 + math.cos(a) * 10, math.sin(a) * 10, s=1.1)
    crag(p, *at(n["crag"], 0, -2), z=-12, r=9, top=CROWN_TOP)
    dress(p, n["hub"], trees=0, blossom=30, tufts=10, mush=0, avoid=[(-10, 0, 14)])


def es_fork_twin_span(p):
    """A fork on two isles: the lower court sends a road west, the upper (+10) carries a bell tower
    and the north mouth."""
    pins(p)
    n = web(p, {"a": (0, -30, 36, 0), "b": (0, 52, 34, 10)}, [("S", "a"), ("a", "W"), ("a", "b"), ("b", "N")])
    bell_tower(p, *at(n["b"], -20, 2), z=10, w=12, rz=0.1)
    for s in (-1, 1):
        column(p, *at(n["a"], 18, s * 12), 0, 16, broken=s > 0)
    dress(p, n["a"], trees=1, blossom=20, tufts=8, mush=2)
    dress(p, n["b"], trees=1, blossom=12, tufts=4, mush=1, avoid=[(-20, 54, 14)])


def es_convergence(p):
    pins(p)
    n = web(p, {"c": dict(x=0, y=0, r=64, z=0, sides=16)}, [("S", "c"), ("c", "N"), ("c", "E"), ("c", "W")])
    hub_plaza(p, 0, 0, 30, star=False)
    fountain(p, 0, 0)
    for k in range(4):
        a = k * math.pi / 2
        road(p, [(math.cos(a) * 28, math.sin(a) * 28), (math.cos(a) * 60, math.sin(a) * 60)], width=12)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        lantern_post(p, math.cos(a) * 36, math.sin(a) * 36, rz=a)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        if k == 0:
            sky_spire(p, math.cos(a) * 50, math.sin(a) * 50, r=3.6)
        else:
            crystal_cluster(p, math.cos(a) * 48, math.sin(a) * 48, s=1.0, n=4)
    dress(p, n["c"], trees=0, blossom=40, tufts=12, mush=0)


# ---------------------------------------------------------------------------
# COMBAT
# ---------------------------------------------------------------------------
def es_meadow_of_blooms(p):
    pins(p)
    n = web(p, {"m": dict(x=0, y=0, r=78, z=0, sides=16)}, [("S", "m"), ("m", "N")])
    great_tree(p, -42, 30, trunk=7)
    aether_pool(p, 38, -30, 14)
    mesa(p, 40, 36, 16, top=5)
    tree(p, 40, 36, z=5, h=18, crown=INDIGO, style=2)
    dress(p, n["m"], trees=6, blossom=120, tufts=30, mush=6, avoid=[(-42, 30, 26), (38, -30, 18), (40, 36, 20)], carpet=True)


def es_terraced_gardens(p):
    pins(p)
    n = web(p, {"a": (0, -40, 37, 0), "b": (-40, 40, 30, 10), "c": (60, 48, 24, 20)},
            [("S", "a"), ("a", "b"), ("b", "N"), ("b", "c")])
    for nd, z in ((n["a"], 0), (n["b"], 10)):
        for k in range(-2, 3):
            x0, y0 = nd["x"] + k * 7, nd["y"]
            decal_strip(p, "PaleGoldSoil", (x0, y0 - nd["r"] * 0.45), (x0, y0 + nd["r"] * 0.2), 3.2, z + 0.03)
            for j in range(4):
                mushroom(p, x0, y0 - nd["r"] * 0.4 + j * 6, z=z, s=0.7)
    crag(p, *at(n["c"], 0, 2), z=20, r=10, top=CROWN_TOP)
    dress(p, n["a"], trees=2, blossom=20, tufts=6, mush=0)


def es_crystal_hollow(p):
    pins(p)
    n = web(p, {"h": dict(x=0, y=0, r=72, z=0, sides=16), "shard": (80, -70, 16, -10)},
            [("S", "h"), ("h", "N"), ("h", "shard")])
    aether_pool(p, 18, 0, 18)
    for k in range(7):
        a = k * 0.9
        crystal_cluster(p, 18 + math.cos(a) * 26, math.sin(a) * 26, s=1.1, n=4)
    crystal_colossus(p, -42, 34, spread=12)
    crystal_cluster(p, *at(n["shard"], 0, 0), z=-10, s=1.3, n=6)
    dress(p, n["h"], trees=2, blossom=20, tufts=8, mush=2, avoid=[(18, 0, 34), (-42, 34, 30)])


def es_fallen_colonnade(p):
    pins(p)
    n = web(p, {"t": dict(x=0, y=0, r=80, z=0, pts=rsquare(0, 0, 76, 84, 24))}, [("S", "t"), ("t", "N")])
    temple_floor(p, n["t"])
    for s in (-1, 1):
        for k in range(-3, 4):
            column(p, s * 26, k * 20, 0, 24, r=2.2, broken=(k + s) % 3 == 0, drum_fall=(k + s) % 3 == 0)
    beam(p, "TempleIvory", (26, -60, 25.5), (26, -20, 25.5), 5, 3)
    ruin_wall(p, (-66, -40), (-50, -60), h=8)
    ruin_wall(p, (54, 40), (66, 58), h=6)
    bell_tower(p, -52, 50, w=14, rz=0.2)
    for x, y in ((50, -54), (-54, -10)):
        statue(p, x, y, rz=math.pi / 2)


def es_mirror_pool(p):
    pins(p)
    n = web(p, {"m": dict(x=0, y=0, r=72, z=0, sides=16), "low": (-88, -80, 16, -14)},
            [("S", "m"), ("m", "N"), ("m", "low")])
    aether_pool(p, 0, 4, 30)
    balustrade(p, ring_pts(0, 4, 33, 16), 0, closed=True, gaps=((0, -29, 10), (0, 37, 10)))
    for a in (0.8, 2.3, 3.9, 5.5):
        statue(p, math.cos(a) * 46, 4 + math.sin(a) * 46, rz=a + math.pi)
    sky_spire(p, 48, 44, r=4)
    lantern_post(p, *at(n["low"], 0, 4), z=-14)
    dress(p, n["m"], trees=2, blossom=24, tufts=8, mush=2, avoid=[(0, 4, 40), (48, 44, 12)])


def es_shrine_of_winds(p):
    pins(p)
    n = web(p, {"s": dict(x=0, y=4, r=70, z=0, pts=rsquare(0, 4, 72, 70, 26))}, [("S", "s"), ("s", "N")])
    temple_floor(p, n["s"])
    for sx in (-1, 1):
        pavilion(p, sx * 40, 4, 0, 14, 14, 11, rz=face(sx * 40, 4, 0, 4))
    box(p, "TempleIvory", 0, 4, 1.2, 6, 6, 2.4)
    gem(p, "PortalGlow", 0, 4, 4.8, 2.2, 2.2, 1.8, n=8)
    frustum(p, "TempleGold", 0, 4, 2.4, 3.4, 2.6, 1.6, n=8)
    bell_tower(p, 42, 50, w=12, rz=0.1)
    for s in (-1, 1):
        for k in range(3):
            lantern_post(p, s * 14, -50 + k * 22, rz=0 if s > 0 else math.pi)


def es_rooted_hollow(p):
    pins(p)
    n = web(p, {"r": dict(x=0, y=0, r=74, z=0, sides=16)}, [("S", "r"), ("r", "N")])
    great_tree(p, 22, 8, trunk=9)
    for a in (2.4, 3.2, 4.0):
        rod(p, "SoftWood", (22 + math.cos(a) * 8, 8 + math.sin(a) * 8, 20), (22 + math.cos(a) * 44, 8 + math.sin(a) * 44, -0.5),
            3.0, 1.2, n=5)
    for k in range(14):
        a = p.rng.uniform(0, 6.28)
        rr = p.rng.uniform(24, 34)
        mushroom(p, 22 + math.cos(a) * rr, 8 + math.sin(a) * rr, s=p.rng.uniform(1.0, 2.0))
    dress(p, n["r"], trees=3, blossom=30, tufts=10, mush=0, avoid=[(22, 8, 48)], carpet=True)


def es_twin_isles(p):
    pins(p)
    n = web(p, {"a": (-36, -22, 40, 0), "b": (42, 32, 38, 12)}, [("S", "a"), ("a", "b"), ("b", "N")])
    sky_spire(p, *at(n["a"], -18, -8), r=4)
    pavilion(p, *at(n["b"], 14, 6), 12, 14, 14, 11, rz=face(*at(n["b"], 14, 6), *at(n["b"])))
    dress(p, n["a"], trees=3, blossom=30, tufts=10, mush=3, avoid=[(n["a"]["x"] - 18, n["a"]["y"] - 8, 12)])
    dress(p, n["b"], trees=2, blossom=20, tufts=6, mush=2, avoid=[(n["b"]["x"] + 14, n["b"]["y"] + 6, 14)])


def es_temple_gate_a(p):
    pins(p)
    n = web(p, {"g": dict(x=0, y=-4, r=80, z=0, pts=rsquare(0, -4, 80, 84, 26))}, [("S", "g"), ("g", "N")], width=24)
    temple_floor(p, n["g"])
    road(p, [(0, -80), (0, 90)], width=20)
    for s in (-1, 1):
        bell_tower(p, s * 52, 44, w=14, rz=0.0)
        for k in range(3):
            waystone(p, s * 22, -54 + k * 26, rz=0.0, h=14)
    arch(p, 0, 62, 0, 72, 44, rz=0.0, thick=6)


def es_temple_gate_b(p):
    pins(p)
    n = web(p, {"g": dict(x=0, y=-4, r=80, z=0, pts=rsquare(0, -4, 82, 84, 28))}, [("S", "g"), ("g", "N")], width=24)
    temple_floor(p, n["g"])
    for s in (-1, 1):
        for k in range(5):
            column(p, s * 22, -30 + k * 20, 0, 30, r=2.6)
        beam(p, "TempleIvory", (s * 22, -32, 31.5), (s * 22, 52, 31.5), 5, 3)
        crystal_colossus(p, s * 56, -34, spread=9)
    for k in range(4):
        beam(p, "TempleGold", (-22, -24 + k * 22, 33.4), (22, -24 + k * 22, 33.4), 1.2, 1.0)


# ---------------------------------------------------------------------------
# LANDMARKS (owner 2026-09-27: "one to two more large structures could be cool"): 384-stud pieces,
# standard mouths, so they drop into any layout like any other tile
# ---------------------------------------------------------------------------
def _arc(p, mat, y0, y1, z_spring, x, w, h, n=8):
    """A semicircular arch of stone segments under a deck, springing from y0 to y1 at z_spring."""
    R = (y1 - y0) / 2
    cy = (y0 + y1) / 2
    prev = None
    for k in range(n + 1):
        a = math.pi * k / n
        q = (x, cy - math.cos(a) * R, z_spring + math.sin(a) * R * 0.85)
        if prev:
            beam(p, mat, prev, q, w, h)
        prev = q


def es_sky_aqueduct(p):
    """The Sky Aqueduct (384): a stone aqueduct carries the road across open sky between two isles --
    three piers on their own low rock isles, arcades between them, a channel of sky-crystal water that
    spills over the side mid-span, parapets and lanterns, a bell tower at the south abutment."""
    pins(p)
    n = web(p, {"s": (0, -114, 34, 0), "n": (0, 114, 34, 0), "p1": (0, -46, 12, -70), "p2": (0, 0, 12, -70),
                "p3": (0, 46, 12, -70)}, [("S", "s"), ("n", "N")], width=24)
    DW = 26.0
    # the deck: one long stone span, its ends resting on both isles
    box(p, "TempleIvory", 0, 0, -1.45, DW, 196, 3.0, top="GoldenPath")
    for sx in (-1, 1):                               # coping and parapets (gaps every 20 studs)
        beam(p, "TempleGold", (sx * (DW / 2 - 0.4), -98, -2.6), (sx * (DW / 2 - 0.4), 98, -2.6), 0.9, 0.9)
        for y0 in range(-90, 90, 20):
            box(p, "TempleIvory", sx * (DW / 2 - 1.0), y0 + 8, 1.6, 2.0, 14, 3.2)
            box(p, "TempleGold", sx * (DW / 2 - 1.0), y0 + 8, 3.4, 2.4, 14.4, 0.4)
    # the water channel along the east side, with a spill over the edge at mid-span
    decal_strip(p, "SkyCrystal", (DW / 2 - 4.5, -94), (DW / 2 - 4.5, 94), 3.2, 0.08)
    decal_strip(p, "TempleGold", (DW / 2 - 6.4, -94), (DW / 2 - 6.4, 94), 0.6, 0.1)
    aether_fall(p, DW / 2 - 1.5, 0, -1.0, (1, 0), width=6, drop=60, pool=False)
    # piers down to their isles, gold bands; arcades spring between them
    for y in (-46, 0, 46):
        box(p, "TempleIvory", 0, y, -36.5, 22, 12, 67)
        for zz in (-60, -40, -20):
            box(p, "TempleGold", 0, y, zz, 22.8, 12.8, 1.4)
        box(p, "TempleGold", 0, y, -4.5, 24, 14, 2.0)
    for sx in (-1, 1):
        for y0, y1 in ((-40, -6), (6, 40)):          # arcades between the piers (the end spans rest on the isles)
            _arc(p, "TempleIvory", y0, y1, -30, sx * (DW / 2 - 3), 3.0, 3.0)
            for yy in (y0, y1):                      # the arch's feet rest on a corbel in the pier or isle
                box(p, "TempleIvory", sx * (DW / 2 - 3), yy, -30, 3.4, 3.4, 3.0)
            beam(p, "TempleIvory", (sx * (DW / 2 - 3), (y0 + y1) / 2, -30 + (y1 - y0) * 0.425 + 1.4),
                 (sx * (DW / 2 - 3), (y0 + y1) / 2, -3.0), 2.4, 2.4)   # spandrel post up to the deck
    for y in (-72, -32, 28, 68):                     # in the parapet gaps
        for sx in (-1, 1):
            lantern_post(p, sx * (DW / 2 - 1.5), y, rz=math.pi if sx > 0 else 0)
    bell_tower(p, *at(n["s"], 22, -2), w=12, rz=0.0)
    waystone(p, *at(n["n"], -18, -4), rz=0.3)
    waystone(p, *at(n["n"], 18, -4), rz=-0.3)
    dress(p, n["s"], trees=1, blossom=18, tufts=6, mush=2, avoid=[(22, -116, 16)])
    dress(p, n["n"], trees=2, blossom=18, tufts=6, mush=2)


def es_sky_observatory(p):
    """The Sky Observatory (384): a round colonnaded hall on a raised podium, climbed from north and
    south; gold dome ribs rising to an armillary sphere whose crystal tip is the crown; the great
    telescope under the dome; gardens, statues and orreries round it."""
    pins(p)
    n = web(p, {"o": dict(x=0, y=0, r=128, z=0, sides=20, roots=False)}, [("S", "o"), ("o", "N")], width=24)
    PZ, PR = 4.0, 68.0
    prism(p, ring_pts(0, 0, PR, 24), -0.5, PZ, "TempleIvory", side="Cloudstone")
    decal_ring(p, "TempleGold", 0, 0, PR - 3, PR - 1, PZ + 0.05, n=24)
    decal_ring(p, "PortalGlow", 0, 0, 20, 21.5, PZ + 0.06, n=24)
    for k in range(12):                              # a star-map inlaid in the floor
        a = k * math.pi / 6
        decal_strip(p, "TempleGold", (math.cos(a) * 22, math.sin(a) * 22), (math.cos(a) * 58, math.sin(a) * 58), 0.8, PZ + 0.07)
    for y0, rz in ((-PR - 8, math.pi / 2), (PR + 8, -math.pi / 2)):
        stairs(p, 0, y0, 0, PZ, 24, rz)
    road(p, [(0, -PR - 9), (0, -150)], width=16)
    road(p, [(0, PR + 9), (0, 150)], width=16)
    CR, CH = 60.0, 40.0
    tops = []
    for k in range(16):
        a = k * math.pi / 8 + math.pi / 16
        x, y = math.cos(a) * CR, math.sin(a) * CR
        column(p, x, y, PZ, CH, r=2.4)
        tops.append((x, y, PZ + CH))
    for k in range(16):                              # the entablature ring on the columns
        a0, a1 = tops[k], tops[(k + 1) % 16]
        beam(p, "TempleIvory", (a0[0], a0[1], a0[2] + 1.5), (a1[0], a1[1], a1[2] + 1.5), 4.0, 3.0)
    ez = PZ + CH + 3.0
    apex = ez + 46.0
    for k in range(0, 16, 2):                        # eight gold ribs rising to the apex
        a = k * math.pi / 8 + math.pi / 16
        prev = None
        for j in range(7):
            t = j / 6 * math.pi / 2
            q = (math.cos(a) * CR * math.cos(t), math.sin(a) * CR * math.cos(t), ez + (apex - ez) * math.sin(t))
            if prev:
                beam(p, "TempleGold", prev, q, 2.2, 2.2)
            prev = q
    frustum(p, "TempleGold", 0, 0, apex - 3, apex + 2, 6, 3.5, n=8)
    # the armillary sphere on its mast; the mast's crystal tip is EXACTLY the crown
    mz = apex + 26
    rod(p, "TempleGold", (0, 0, apex + 1), (0, 0, CROWN_TOP - 8), 1.0, 0.7, n=6)
    frustum(p, "SkyCrystal", 0, 0, CROWN_TOP - 8.2, CROWN_TOP, 1.6, 0.0, n=6)
    gem(p, "PortalGlow", 0, 0, mz, 4.0, 4.0, 4.0, n=8)
    for tilt, spin in ((0.0, 0.0), (math.pi / 2, 0.0), (math.pi / 2, math.pi / 2), (0.41, 0.8)):
        prev = None
        for k in range(17):
            a = k * math.pi / 8
            v = (math.cos(a) * 16, math.sin(a) * 16, 0.0)
            v = (v[0], v[1] * math.cos(tilt), v[1] * math.sin(tilt))
            v = (v[0] * math.cos(spin) - v[1] * math.sin(spin), v[0] * math.sin(spin) + v[1] * math.cos(spin), v[2])
            q = (v[0], v[1], mz + v[2])
            if prev:
                beam(p, "TempleGold", prev, q, 0.9, 0.9)
            prev = q
    for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):   # spokes tie the rings to the mast
        rod(p, "TempleGold", (0, 0, mz), (math.cos(a) * 16, math.sin(a) * 16, mz), 0.35, 0.35, n=4)
    # the great telescope on its mount, aimed out between the ribs
    frustum(p, "TempleIvory", 30, 12, PZ - 0.2, PZ + 6, 5, 3.5, n=8)
    p.footings.append((30, 12, PZ, 3.5, "telescope"))
    frustum(p, "TempleGold", 30, 12, PZ + 6, PZ + 8, 3.5, 2.5, n=8)
    rod(p, "TempleGold", (24, 9, PZ + 5), (44, 19, PZ + 34), 3.2, 2.4, n=10)
    frustum(p, "SkyCrystal", 44, 19, PZ + 34 - 0.5, PZ + 35.5, 2.6, 2.6, n=10)
    # round the podium: statues at the stairs, orrery pedestals, lanterns, gardens
    for sx in (-1, 1):
        for y in (-PR - 14, PR + 14):
            statue(p, sx * 18, y, rz=face(sx * 18, y, 0, y + (40 if y < 0 else -40)))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 96, math.sin(a) * 96
        frustum(p, "TempleIvory", x, y, -0.5, 5, 3.2, 2.2, n=8)
        p.footings.append((x, y, 0, 2.5, "orrery"))
        p.keepout.append((x, y, 9.0))
        rod(p, "TempleGold", (x, y, 5), (x, y, 9), 0.3, 0.3, n=4)
        gem(p, "SkyCrystal", x, y, 10.5, 2.0, 1.8, 1.8, n=8)
        for j in range(3):
            b = j * 2.09
            rod(p, "TempleGold", (x, y, 9.6), (x + math.cos(b) * 4, y + math.sin(b) * 4, 10.2), 0.2, 0.2, n=4)
            gem(p, "IndigoLeaves" if j else "TempleGold", x + math.cos(b) * 4, y + math.sin(b) * 4, 10.2, 0.8, 0.8, 0.8, n=6)
        lantern_post(p, math.cos(a + 0.35) * 104, math.sin(a + 0.35) * 104, rz=a)
    dress(p, n["o"], trees=8, blossom=60, tufts=18, mush=4, avoid=[(0, 0, PR + 12)], carpet=False)


# ---------------------------------------------------------------------------
# MINIBOSS arenas (§7.7): one mouth, a branch always ends at one
# ---------------------------------------------------------------------------
def es_miniboss_waystone_ring(p):
    """The Waystone Sentinel's ring: a wide arena isle, eight waystones round a gold ring, twin
    spires behind, a gallery perch looking down on the fight."""
    pins(p)
    n = web(p, {"ring": dict(x=0, y=6, r=84, z=0, sides=18), "gallery": (-84, 88, 18, 10)},
            [("S", "ring"), ("ring", "gallery")])
    decal_ring(p, "TempleGold", 0, 6, 54, 57, 0.05, n=32)
    decal_ring(p, "PortalGlow", 0, 6, 30, 31, 0.06, n=24)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        waystone(p, math.cos(a) * 64, 6 + math.sin(a) * 64, rz=a, h=18)
    for s in (-1, 1):
        sky_spire(p, s * 40, 70, r=4)
    lantern_post(p, *at(n["gallery"], 0, 0), z=10)


def es_miniboss_reliquary_court(p):
    """The Reliquary Keeper's court: a balustraded temple court, the reliquary hall at its head,
    statues round the floor, spires either side of the hall."""
    pins(p)
    n = web(p, {"c": dict(x=0, y=8, r=84, z=0, pts=rsquare(0, 8, 84, 88, 28))}, [("S", "c")])
    temple_floor(p, n["c"])
    shrine_hall(p, 0, 66, 0, 30, 20, rz=face(0, 66, 0, 8))   # its porch opens onto the court
    for a in (0.3, 1.2, 1.95, 2.85):
        statue(p, math.cos(a + math.pi) * 52, 8 + math.sin(a + math.pi) * 40 + 20, rz=a)
    for s in (-1, 1):
        sky_spire(p, s * 54, 66, r=4)
        balustrade(p, [(s * 74, -60), (s * 74, 40)], 0, closed=False)


# ---------------------------------------------------------------------------
# SIDE pockets
# ---------------------------------------------------------------------------
def es_side_hermit_grove(p):
    pins(p)
    n = web(p, {"g": (0, -16, 48, 0), "perch": (56, 64, 20, 12)}, [("S", "g"), ("g", "perch")])
    hut(p, 24, -26, rz=face(24, -26, 0, -16))
    great_tree(p, -20, 10, trunk=6)
    for k in range(3):
        decal_strip(p, "PaleGoldSoil", (-30 + k * 6, -40), (-30 + k * 6, -26), 3, 0.03)
    lantern_post(p, *at(n["perch"], 0, 0), z=12)
    dress(p, n["g"], trees=2, blossom=24, tufts=8, mush=4, avoid=[(24, -26, 12), (-20, 10, 22), (-24, -33, 12)])


def es_side_crystal_grotto(p):
    pins(p)
    n = web(p, {"g": (0, -8, 50, 0)}, [("S", "g")])
    crag(p, 0, 22, r=14, top=CROWN_TOP)
    for k in range(6):
        a = 3.4 + k * 0.5
        crystal_cluster(p, math.cos(a) * 30, 22 + math.sin(a) * 30 + 6, s=1.2, n=4)
    aether_pool(p, -22, -30, 10)
    dress(p, n["g"], trees=1, blossom=16, tufts=6, mush=2, avoid=[(0, 22, 34), (-22, -30, 14)])


def es_side_relic_altar(p):
    pins(p)
    n = web(p, {"a": (0, -12, 48, 0), "col": (60, 62, 24, 10)}, [("S", "a"), ("a", "col")])
    pavilion(p, -8, 6, 0, 16, 16, 12, rz=face(-8, 6, 0, -60))
    crystal_colossus(p, *at(n["col"], 0, 0), z=10, spread=8)
    for s in (-1, 1):
        lantern_post(p, s * 12, -40, rz=0 if s > 0 else math.pi)
    dress(p, n["a"], trees=2, blossom=20, tufts=6, mush=2, avoid=[(-8, 6, 16)])


# ---------------------------------------------------------------------------
# CAPS: a branch that leads nowhere ends at one of these, never at open sky
# ---------------------------------------------------------------------------
def es_cap_broken_bridge(p):
    pins(p)
    n = web(p, {"a": (0, -40, 36, 0)}, [("S", "a")])
    bridge(p, (0, -18), (0, 18), 0, 0, 16)
    for k in range(4):                       # the snapped end: planks hanging into the void
        rod(p, "SoftWood", (-6 + k * 4, 17.5, -0.6), (-7 + k * 4.5, 22, -9 - k * 3), 0.5, 0.4, n=4)
    crag(p, 10, 76, z=-94, r=12, top=CROWN_TOP, ledges=True)
    dress(p, n["a"], trees=2, blossom=16, tufts=6, mush=2)


def es_cap_overlook(p):
    pins(p)
    n = web(p, {"o": (0, -28, 48, 0)}, [("S", "o")])
    balustrade(p, [(math.cos(a) * 42, -28 + math.sin(a) * 42) for a in [0.2 + k * 0.34 for k in range(9)]], 0, closed=False)
    box(p, "SoftWood", 0, 0, 1.6, 10, 2.2, 0.6)
    for s in (-1, 1):
        box(p, "SoftWood", s * 4.2, 0, 0.6, 0.8, 2.0, 1.4)
    great_tree(p, -22, -34, trunk=6)
    dress(p, n["o"], trees=1, blossom=16, tufts=6, mush=2, avoid=[(-22, -34, 22), (0, 0, 8)])


def es_cap_sealed_shrine(p):
    pins(p)
    web(p, {"s": (0, -22, 50, 0)}, [("S", "s")])
    crag(p, 0, 20, r=18, top=CROWN_TOP)
    box(p, "TempleIvory", 0, 0.5, 9, 18, 3, 18)
    box(p, "PortalGlow", 0, -1.2, 9, 10, 0.6, 12)
    for s in (-1, 1):
        column(p, s * 12, -3, 0, 18, r=1.8)
        lantern_post(p, s * 18, -24, rz=0 if s > 0 else math.pi)


def es_cap_falls_ledge(p):
    pins(p)
    n = web(p, {"l": (0, -36, 44, 0)}, [("S", "l")])
    balustrade(p, [(-30, -8), (-12, 2), (12, 2), (30, -8)], 0, closed=False)
    aether_fall(p, 0, 4, -1.4, (0, 1), width=16, drop=70, pool=False)
    sky_spire(p, -26, -46, r=4)
    dress(p, n["l"], trees=2, blossom=20, tufts=8, mush=2, avoid=[(-26, -46, 12)])


# ---------------------------------------------------------------------------
# BACKDROP (§7.7): socketless surround scenery, never walked
# ---------------------------------------------------------------------------
def _crown_pin(p):
    """Backdrop pieces are mostly props (drifting clouds), so a 0.3-stud pin marks the crown: the box
    must still be exactly (2H x 2H) x 256 for the loader to scale it right."""
    box(p, "CloudWhite", 0, 0, CROWN_TOP - 0.15, 0.3, 0.3, 0.3)


def cloud_props(p, plan):
    """Drop drifting cloud PROPS (es_props: Float) into a backdrop piece. `plan` is a list of
    (kind, count, (zlo, zhi), (slo, shi)); every copy gets its own seeded spot, height, size and turn,
    kept inside the tile and the box. Clouds may overlap clouds -- that is how a bank reads -- but never
    stack dead-centre on one another."""
    import es_props as PR
    lib = PR.library()
    rng = p.rng
    H = p.H
    got = []
    for kind, count, (zlo, zhi), (slo, shi) in plan:
        placed = 0
        for _ in range(count * 80):
            if placed >= count:
                break
            sc = rng.uniform(slo, shi)
            size = lib[kind][3] * sc
            half = max(size.x, size.y) / 2
            x, y = rng.uniform(-H + half + 4, H - half - 4), rng.uniform(-H + half + 4, H - half - 4)
            z = rng.uniform(zlo, zhi)
            if z + size.z / 2 > CROWN_TOP - 1 or z - size.z / 2 < -94:
                continue
            if any(math.hypot(x - q[0], y - q[1]) < (half + q[2]) * 0.45 and abs(z - q[3]) < 20 for q in got):
                continue
            got.append((x, y, half, z))
            p.props.append(dict(kind=kind, pos=Vector((x, y, z)), yaw=rng.uniform(0, 6.28), scale=sc, size=size))
            placed += 1


def es_backdrop_cloudbank(p):
    """Towering: one or two great cumulus over a low shelf, fair-weather puffs round their feet."""
    pins(p)
    _crown_pin(p)
    cloud_props(p, [("prop_es_cumulus_a", p.rng.choice((1, 2)), (10, 55), (1.1, 1.7)),
                    ("prop_es_cumulus_b", 1, (-60, -30), (0.8, 1.05)),
                    ("prop_es_cloud_a", 5, (-50, 40), (0.8, 1.6)),
                    ("prop_es_cloud_b", 3, (-70, 90), (0.8, 1.5))])


def es_backdrop_cloud_shelf(p):
    """A long low shelf of stratocumulus, layered at two heights, wisps trailing above."""
    pins(p)
    _crown_pin(p)
    cloud_props(p, [("prop_es_cumulus_b", 3, (-70, -10), (0.8, 1.0)),
                    ("prop_es_cloud_b", 6, (0, 100), (0.9, 1.8)),
                    ("prop_es_cloud_a", 2, (-40, 20), (0.8, 1.3))])


def es_backdrop_cloud_drift(p):
    """Open sky: a loose drift of small clouds at every height -- the gaps are the point."""
    pins(p)
    _crown_pin(p)
    cloud_props(p, [("prop_es_cloud_a", 8, (-80, 120), (0.7, 1.9)),
                    ("prop_es_cloud_b", 6, (-70, 130), (0.8, 2.0))])


def es_backdrop_storm_anvil(p):
    """A single great anvil cloud rising out of the deck, darker sky-crystal lightning shards hovering
    in its shadow (props), a shelf at its foot."""
    pins(p)
    _crown_pin(p)
    cloud_props(p, [("prop_es_cumulus_c", 1, (20, 40), (1.3, 1.55)),
                    ("prop_es_cumulus_b", 1, (-75, -45), (0.8, 1.0)),
                    ("prop_es_cloud_b", 3, (-60, 30), (1.0, 1.6)),
                    ("prop_es_shard", 4, (-30, 30), (1.2, 2.0))])


def es_backdrop_drift_isles(p):
    pins(p)
    rng = p.rng
    for (x, y, r, z) in ((-56, -50, 26, -20), (54, -10, 20, 18), (-30, 60, 18, 44)):
        isle(p, circle(p, x, y, r), z, depth=50)
        for k in range(2):
            tree(p, x + rng.uniform(-r * 0.4, r * 0.4), y + rng.uniform(-r * 0.4, r * 0.4), z=z, h=rng.uniform(14, 20),
                 crown=(TEAL, INDIGO)[k])
    isle(p, circle(p, 64, 72, 16), -30, depth=40)
    sky_spire(p, 64, 72, z=-30, r=3.4)
    cloud_props(p, [("prop_es_cloud_b", 4, (-85, -60), (1.0, 1.8)), ("prop_es_cloud_a", 3, (60, 120), (0.8, 1.4))])


def es_backdrop_crystal_spire(p):
    pins(p)
    isle(p, circle(p, 0, 0, 40, sides=14), -30, depth=60)
    crag(p, 0, 0, z=-30, r=16, top=CROWN_TOP)
    for k in range(6):
        a = k * 1.05
        crystal_cluster(p, math.cos(a) * 28, math.sin(a) * 28, z=-30, s=1.3, n=4)
    cloud_props(p, [("prop_es_cumulus_b", 1, (-85, -70), (0.7, 0.85)), ("prop_es_cloud_a", 4, (-20, 110), (0.8, 1.5))])


# ---------------------------------------------------------------------------
# The kit table: id, role, half-footprint, sockets, builder, and content metadata. `lift` gives a
# socket's height (its OffsetY) where it is not the walk plane.
# ---------------------------------------------------------------------------
S, C = "SPAN", "COMMUNION"
SN = [("S", S), ("N", S)]
PIECES = [
    dict(id="ES_ENTRY", role="ENTRY", half=192, sockets=[("N", S)], fn=es_entry,
         weight=1, max=1, tags=["arrival", "low-density"], enemies=["AETHER_WISP"],
         desc="Arrival Isle: gold mosaic landing, crystal-topped spawn columns, a shrine terrace, the great sky tree, two perches."),
    # PATH -- straights
    dict(id="ES_PATH_PLANK_CROSSING", role="PATH", half=128, sockets=SN, fn=es_plank_crossing,
         weight=24, supports=["Combat", "Traversal", "Ambush"], tags=["bridge", "isles"], enemies=["SKYBORNE_HARRIER", "AETHER_WISP"],
         desc="Three isles strung on plank bridges, the middle one raised under a pavilion; a spire on a low perch."),
    dict(id="ES_PATH_GROVE_ISLE", role="PATH", half=128, sockets=SN, fn=es_grove_isle,
         weight=20, supports=["Combat", "Traversal", "Secret"], tags=["meadow", "grove"], enemies=["MEADOW_STAG"],
         desc="One broad meadow isle: a great tree, a fairy ring, aether falls pouring off its east rim."),
    dict(id="ES_PATH_SKYSTAIR_UP", role="PATH", half=128, sockets=SN, fn=es_skystair_up, lift={"N": 24},
         weight=12, supports=["Traversal", "Ambush"], tags=["rise", "isles"], enemies=["TEMPLE_ACOLYTE"],
         desc="A full storey UP (+24): three isles climbing past ruined columns and a great tree to a shrine arch."),
    dict(id="ES_PATH_SKYSTAIR_DOWN", role="PATH", half=128, sockets=SN, fn=es_skystair_down, lift={"N": -24},
         weight=12, supports=["Traversal", "Ambush", "Secret"], tags=["descent", "crystal"], enemies=["CRYSTAL_WARDEN"],
         desc="A full storey DOWN (-24): three isles stepping into the cloud past a crystal colossus."),
    dict(id="ES_SKY_AQUEDUCT", role="PATH", half=192, sockets=SN, fn=es_sky_aqueduct,
         weight=6, max=1, supports=["Combat", "Traversal", "Event"], tags=["landmark", "bridge", "falls"],
         enemies=["SKYBORNE_HARRIER", "TEMPLE_ACOLYTE"],
         desc="Landmark (384): a stone aqueduct carries the road across open sky on three piers and arcades."),
    # PATH -- bends
    dict(id="ES_PATH_BEND_EAST_GROVE", role="PATH", half=128, sockets=[("S", S), ("E", S)], fn=es_bend_east_grove,
         weight=12, supports=["Combat", "Ambush"], tags=["bend", "grove"], enemies=["MEADOW_STAG"],
         desc="A bend on a grove isle, a mushroom ring, a great tree on a raised perch."),
    dict(id="ES_PATH_BEND_EAST_ASCENT", role="PATH", half=128, sockets=[("S", S), ("E", S)], fn=es_bend_east_ascent,
         lift={"E": 16}, weight=10, supports=["Combat", "Traversal"], tags=["bend", "rise"], enemies=["TEMPLE_ACOLYTE"],
         desc="Bend and climb (+16): a ruin isle, a bell-tower isle over the east mouth, a hermit's hut perch."),
    dict(id="ES_PATH_BEND_WEST_FALLS", role="PATH", half=128, sockets=[("S", S), ("W", S)], fn=es_bend_west_falls,
         lift={"W": -16}, weight=10, supports=["Combat", "Traversal", "Event"], tags=["bend", "descent", "falls"],
         enemies=["CRYSTAL_WARDEN"], desc="Bend and descend (-16): aether falls, a spire, a pavilion perch, a pool isle."),
    dict(id="ES_PATH_BEND_WEST_SHRINE", role="PATH", half=128, sockets=[("S", S), ("W", S)], fn=es_bend_west_shrine,
         weight=12, supports=["Combat", "Shrine"], tags=["bend", "shrine"], enemies=["TEMPLE_ACOLYTE"],
         desc="A bend past a small shrine hall and a waystone arc, a spire over the corner."),
    # PATH -- junctions
    dict(id="ES_FORK_WAYSHRINE", role="PATH", half=128, sockets=[("S", S), ("E", S), ("W", S)], fn=es_fork_wayshrine,
         weight=5, max=2, supports=["Combat", "Shrine", "Event"], tags=["fork"], enemies=["AETHER_WISP"],
         desc="A three-way fork round a waystone circle and a signpost, a great tree on a perch behind."),
    dict(id="ES_FORK_THREE_TREES", role="PATH", half=128, sockets=[("S", S), ("N", S), ("E", S)], fn=es_fork_three_trees,
         weight=5, max=2, supports=["Combat", "Ambush"], tags=["fork", "grove"], enemies=["MEADOW_STAG"],
         desc="A three-way fork under three ancient trees and a mushroom ring; a crag isle below."),
    dict(id="ES_FORK_TWIN_SPAN", role="PATH", half=128, sockets=[("S", S), ("N", S), ("W", S)], fn=es_fork_twin_span,
         lift={"N": 10}, weight=5, max=2, supports=["Combat", "Traversal"], tags=["fork", "rise"], enemies=["SKYBORNE_HARRIER"],
         desc="A fork on two isles: the lower sends a road west, the upper (+10) carries a bell tower and the north mouth."),
    dict(id="ES_CONVERGENCE", role="PATH", half=128, sockets=[("N", S), ("S", S), ("E", S), ("W", S)], fn=es_convergence,
         weight=3, max=1, supports=["Combat", "Traversal", "Event"], tags=["crossroads"], enemies=[],
         desc="The crossroads isle: a compass court with a fountain, eight lanterns, four golden roads."),
    # COMBAT
    dict(id="ES_MEADOW_OF_BLOOMS", role="COMBAT", half=128, sockets=SN, fn=es_meadow_of_blooms,
         weight=12, supports=["Combat", "Ambush", "Treasure"], tags=["meadow", "open"], enemies=["MEADOW_STAG"],
         desc="An open meadow isle drifted with blossoms under a great tree, a pool and a tree mesa."),
    dict(id="ES_TERRACED_GARDENS", role="COMBAT", half=128, sockets=SN, fn=es_terraced_gardens,
         weight=10, supports=["Combat", "Traversal", "Puzzle"], tags=["garden", "rise"], enemies=["MEADOW_STAG"],
         desc="Garden isles terraced +10 and +20, soil rows and mushrooms, a crag on the highest."),
    dict(id="ES_CRYSTAL_HOLLOW", role="COMBAT", half=128, sockets=SN, fn=es_crystal_hollow,
         weight=10, supports=["Combat", "Puzzle", "Secret"], tags=["crystal", "pool"], enemies=["CRYSTAL_WARDEN"],
         desc="An aether pool ringed by crystal clusters under a crystal colossus; a shard isle below."),
    dict(id="ES_FALLEN_COLONNADE", role="COMBAT", half=128, sockets=SN, fn=es_fallen_colonnade,
         weight=10, supports=["Combat", "MiniBoss", "Secret"], tags=["temple", "ruin"], enemies=["TEMPLE_ACOLYTE"],
         desc="A temple-floor isle, its colonnade half fallen, statues, a bell tower still standing."),
    dict(id="ES_MIRROR_POOL", role="COMBAT", half=128, sockets=SN, fn=es_mirror_pool,
         weight=10, supports=["Combat", "Puzzle", "Shrine"], tags=["pool", "temple"], enemies=["TEMPLE_ACOLYTE"],
         desc="A balustraded mirror pool watched by four statues, a spire beyond, a lantern perch below."),
    dict(id="ES_SHRINE_OF_WINDS", role="COMBAT", half=128, sockets=SN, fn=es_shrine_of_winds,
         weight=10, supports=["Combat", "Shrine", "Event"], tags=["temple", "shrine"], enemies=["TEMPLE_ACOLYTE"],
         desc="A temple court: twin pavilions round an orb altar, a bell tower, a lantern avenue."),
    dict(id="ES_ROOTED_HOLLOW", role="COMBAT", half=128, sockets=SN, fn=es_rooted_hollow,
         weight=10, supports=["Combat", "Ambush", "Secret"], tags=["grove"], enemies=["MEADOW_STAG"],
         desc="A great tree whose roots arch down across the isle, mushrooms in its shade."),
    dict(id="ES_TWIN_ISLES", role="COMBAT", half=128, sockets=SN, fn=es_twin_isles,
         weight=10, supports=["Combat", "Traversal", "MiniBoss"], tags=["isles", "bridge", "rise"], enemies=["SKYBORNE_HARRIER"],
         desc="Two isles joined by a climbing bridge (+12): a spire on the low one, a pavilion on the high."),
    dict(id="ES_SKY_OBSERVATORY", role="COMBAT", half=192, sockets=SN, fn=es_sky_observatory,
         weight=6, max=1, supports=["Combat", "MiniBoss", "Puzzle", "Event"], tags=["landmark", "temple", "shrine"],
         enemies=["TEMPLE_ACOLYTE", "CRYSTAL_WARDEN"],
         desc="Landmark (384): a domed colonnade on a podium, an armillary sphere at its crown, the great telescope."),
    dict(id="ES_TEMPLE_GATE_A", role="COMBAT", half=128, sockets=[("S", S), ("N", C)], fn=es_temple_gate_a,
         weight=20, supports=["Combat", "MiniBoss"], tags=["gate-court", "temple"], enemies=["GATEWARDEN"],
         desc="Gate-court: bell towers flank the great arch over the COMMUNION road; waystones line it."),
    dict(id="ES_TEMPLE_GATE_B", role="COMBAT", half=128, sockets=[("S", S), ("N", C)], fn=es_temple_gate_b,
         weight=10, supports=["Combat", "MiniBoss"], tags=["gate-court", "temple", "rare"], enemies=["GATEWARDEN"],
         desc="Gate-court, rare: a roofed colonnade the road passes through, crystal colossi either side."),
    # MINIBOSS (§7.7)
    dict(id="ES_MINIBOSS_WAYSTONE_RING", role="MINIBOSS", half=128, sockets=[("S", S)], fn=es_miniboss_waystone_ring,
         weight=1, max=1, supports=["MiniBoss"], tags=["miniboss", "arena"], enemies=["WAYSTONE_SENTINEL"],
         desc="The Waystone Sentinel's arena: eight waystones round a gold ring, twin spires, a gallery perch."),
    dict(id="ES_MINIBOSS_RELIQUARY_COURT", role="MINIBOSS", half=128, sockets=[("S", S)], fn=es_miniboss_reliquary_court,
         weight=1, max=1, supports=["MiniBoss"], tags=["miniboss", "arena", "temple"], enemies=["RELIQUARY_KEEPER"],
         desc="The Reliquary Keeper's court: a balustraded temple court before the reliquary hall."),
    # SIDE
    dict(id="ES_SIDE_HERMIT_GROVE", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_hermit_grove,
         weight=6, supports=["Combat", "Secret", "Treasure"], tags=["side", "grove"], enemies=[],
         desc="A hermit's hut and garden under a great tree, a lantern perch."),
    dict(id="ES_SIDE_CRYSTAL_GROTTO", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_crystal_grotto,
         weight=6, supports=["Combat", "Puzzle", "Secret"], tags=["side", "crystal"], enemies=["CRYSTAL_WARDEN"],
         desc="A crag with crystal clusters crowding its foot, an aether pool."),
    dict(id="ES_SIDE_RELIC_ALTAR", role="SIDE", half=128, sockets=[("S", S)], fn=es_side_relic_altar,
         weight=6, supports=["Combat", "Treasure"], tags=["side", "treasure"], enemies=[],
         desc="A pavilion altar holding a relic, a crystal colossus on a raised isle behind."),
    # CAP
    dict(id="ES_CAP_BROKEN_BRIDGE", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_broken_bridge,
         weight=1, tags=["cap", "dead-end"], enemies=[],
         desc="A plank bridge that snaps over the void; a lone crag rises from the depths beyond."),
    dict(id="ES_CAP_OVERLOOK", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_overlook,
         weight=1, tags=["cap", "dead-end", "lookout"], enemies=[],
         desc="A balustraded lookout isle with a sky seat under a great tree."),
    dict(id="ES_CAP_SEALED_SHRINE", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_sealed_shrine,
         weight=1, tags=["cap", "dead-end", "sealed"], enemies=[],
         desc="A shrine door sealed in a crag's face, its seal still glowing."),
    dict(id="ES_CAP_FALLS_LEDGE", role="CAP", half=128, sockets=[("S", S)], fn=es_cap_falls_ledge,
         weight=1, tags=["cap", "dead-end", "falls"], enemies=[],
         desc="A ledge where aether falls pour off the isle's rim, a spire over it."),
    # BOSS
    dict(id="ES_SANCTUM", role="BOSS", half=256, sockets=[("S", C)], fn=es_sanctum,
         weight=1, max=1, tags=["arena"], enemies=["THE_ASCENDANT"],
         desc="The Sanctum: the grand temple that houses the boss, on the greatest isle in the sky."),
    # BACKDROP (§7.7)
    dict(id="ES_BACKDROP_CLOUDBANK", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_cloudbank,
         weight=3, tags=["backdrop", "cloud"], enemies=[],
         desc="Surround: towering cumulus over a low shelf, puffs round their feet (drifting props)."),
    dict(id="ES_BACKDROP_CLOUD_SHELF", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_cloud_shelf,
         weight=3, tags=["backdrop", "cloud"], enemies=[],
         desc="Surround: a long layered shelf of cloud, wisps trailing above (drifting props)."),
    dict(id="ES_BACKDROP_CLOUD_DRIFT", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_cloud_drift,
         weight=3, tags=["backdrop", "cloud"], enemies=[],
         desc="Surround: open sky, a loose drift of small clouds at every height (drifting props)."),
    dict(id="ES_BACKDROP_STORM_ANVIL", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_storm_anvil,
         weight=1, tags=["backdrop", "cloud"], enemies=[],
         desc="Surround: one great anvil cloud with hovering crystal shards in its shadow (props)."),
    dict(id="ES_BACKDROP_DRIFT_ISLES", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_drift_isles,
         weight=3, tags=["backdrop", "isles"], enemies=[],
         desc="Surround: small isles drifting at their own heights, one carrying a spire."),
    dict(id="ES_BACKDROP_CRYSTAL_SPIRE", role="BACKDROP", half=128, sockets=[], fn=es_backdrop_crystal_spire,
         weight=2, tags=["backdrop", "crystal"], enemies=[],
         desc="Surround: a crystal-ringed crag spire on a sunken isle."),
]
assert len(PIECES) == 41
