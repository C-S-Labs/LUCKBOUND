# Ethereal Scape -- three DIRECTION SAMPLES for the owner to choose between (2026-09-27).
# Each is one combat room with N/S SPAN mouths, same footprint, same rules, so they compare
# like for like. Not part of the kit; rendered by build_ethereal_scape_kit.py -- --samples.
#   A  Floating Isles     -- the original scene's language: isles hung in open sky, deep rock
#                            undersides, hanging roots and crystal, gold plank bridges, falls
#   B  Lush Cloudscape    -- the current grounded direction pushed hard: meadow over most of
#                            the cloud, dense groves, a pond, ruins, flowers everywhere
#   C  Temple City        -- a quarter of a sprawling ruined temple complex set in cloud:
#                            plazas, a colonnaded avenue, a shrine hall, terraces and stairs
import math

from es_features import (FLOOR_Z, aether_pool, arch, balustrade, bell_tower, blossoms, column, crag, crystal_cluster,
                         crystal_colossus, fountain, grass_tufts, great_tree, guide_stone, lantern_post, meadow_carpet,
                         mesa, mouth, mushroom, path, pavilion, perimeter_banks, pins, puff, ramp, rock, ruin_wall, stairs,
                         tree, waystone, cloud_floor, flagstones)
from es_geometry import CROWN_TOP, DIRS, KIND_WIDTH, beam, box, decal, decal_ring, decal_strip, frustum, gem, prism, ring_pts, rod
from es_pieces import aether_fall, hub_plaza, meadow_dress, plank_bridge, scatter
from es_isles import shrine_hall, statue

TEAL, INDIGO = "DeepTealLeaves", "IndigoLeaves"


# ---------------------------------------------------------------------------
# A: floating isles
# ---------------------------------------------------------------------------
def float_isle(p, cx, cy, r, depth=70, sides=12, floor="AetherMintGrass", roots=True, chandelier=True):
    """An isle hung in open sky: meadow top, the gold rim band, and a deep faceted rock underside in
    three jagged tiers -- the original scene's islands, not a flat deck."""
    rng = p.rng
    top = []
    for i in range(sides):
        a = 2 * math.pi * (i + rng.uniform(-0.25, 0.25)) / sides
        rr = r * rng.uniform(0.88, 1.1)
        top.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    prism(p, top, -2.5, 0.0, floor, side=floor)
    rim = [(cx + (x - cx) * 1.05, cy + (y - cy) * 1.05) for x, y in top]
    prism(p, rim, -6.0, -1.4, "TempleGold")
    rings = [(1.05, -6.0), (0.86, -depth * 0.28), (0.55, -depth * 0.62), (0.22, -depth * 0.9)]
    prev = None
    n = len(top)
    for k, (s, z) in enumerate(rings):
        ring = [(cx + (x - cx) * s * rng.uniform(0.92, 1.06), cy + (y - cy) * s * rng.uniform(0.92, 1.06), z) for x, y in top]
        if prev is not None:
            verts = prev + ring
            p.add(verts, [[n + i, n + (i + 1) % n, (i + 1) % n, i] for i in range(n)],
                  "PaleGoldSoil" if k == 1 else "Cloudstone")
        prev = ring
    tip = (cx + rng.uniform(-4, 4), cy + rng.uniform(-4, 4), -depth)
    p.add(prev + [tip], [[(i + 1) % n, i, n] for i in range(n)], "Cloudstone")
    if roots:                                  # roots hang from the upper flank, never past the keel line
        mid = [(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86, -depth * 0.28) for x, y in top]
        for i in range(0, n, 2):
            x, y, z = mid[i]
            a = math.atan2(y - cy, x - cx)
            rod(p, "SoftWood", (x - math.cos(a) * 3, y - math.sin(a) * 3, z + 2),
                (x + math.cos(a) * 5, y + math.sin(a) * 5, max(-94.0, z - rng.uniform(12, 24))), 1.6, 0.3, n=5)
    if chandelier:                              # rooted INSIDE the rock, hanging out of its underside
        for k in range(5):
            a = k * 1.26 + rng.uniform(-0.3, 0.3)
            bx, by = cx + math.cos(a) * r * 0.22, cy + math.sin(a) * r * 0.22
            rod(p, "SkyCrystal", (bx, by, -depth * 0.45),
                (bx + math.cos(a) * 5, by + math.sin(a) * 5, max(-94.0, -depth * 0.9 - rng.uniform(4, 14))), 2.4, 0.0, n=5)
    p.keepout.append((cx, cy, 0))            # (its top is ground; features are placed on it explicitly)
    return top


def landing_isle(p, cardinal, depth=40):
    """The standard mouth, but hung in the sky: a flagstone landing isle reaching exactly to the edge."""
    kind = dict(p.sockets)[cardinal]
    w = KIND_WIDTH[kind]
    H = p.H
    dx, dy = DIRS[cardinal]
    nx, ny = -dy, dx
    L = 34.0
    a0, a1 = H - L, H
    pts = [(dx * a0 + nx * (w / 2 + 6), dy * a0 + ny * (w / 2 + 6)), (dx * a1 + nx * (w / 2 + 2), dy * a1 + ny * (w / 2 + 2)),
           (dx * a1 - nx * (w / 2 + 2), dy * a1 - ny * (w / 2 + 2)), (dx * a0 - nx * (w / 2 + 6), dy * a0 - ny * (w / 2 + 6))]
    prism(p, pts, -3.0, 0.0, "GoldenPath", side="TempleGold")
    cx, cy = dx * (H - L / 2), dy * (H - L / 2)
    verts = [(x, y, -3.0) for x, y in pts] + [(cx - dx * 4, cy - dy * 4, -depth)]
    p.add(verts, [[1, 0, 4], [2, 1, 4], [3, 2, 4], [0, 3, 4]], "Cloudstone")
    flagstones(p, (dx * a0, dy * a0), (dx * (a1 - 0.5), dy * (a1 - 0.5)), w, 0.045, course=7.0)
    for s in (-1, 1):
        guide_stone(p, dx * (a0 + 6) + nx * s * (w / 2 + 3), dy * (a0 + 6) + ny * s * (w / 2 + 3), FLOOR_Z)
    return (dx * a0, dy * a0)


def sample_floating_isles(p):
    pins(p)
    s_end = landing_isle(p, "S")
    n_end = landing_isle(p, "N")
    top = float_isle(p, 0, 0, 62, depth=92)
    float_isle(p, -70, 58, 26, depth=46, chandelier=False)
    float_isle(p, 74, -40, 22, depth=40, roots=False)
    plank_bridge(p, (0, -95), (0, -52), width=16)
    plank_bridge(p, (0, 52), (0, 95), width=16)
    plank_bridge(p, (-26, 22), (-54, 44), width=8)
    plank_bridge(p, (28, -14), (58, -32), width=8)
    path(p, [(0, -50), (0, -12), (0, 12), (0, 50)], width=12)
    hub_plaza(p, 0, 0, 18, star=False)
    pavilion(p, 32, 20, FLOOR_Z, 14, 14, 11, rz=0.4)
    for k, (x, y) in enumerate(((-30, -26), (-38, 6), (26, -38), (-14, 40))):
        tree(p, x, y, h=[22, 26, 20, 24][k], crown=TEAL if k % 2 else INDIGO, style=k % 3)
    for a in (0.3, 1.2, 3.6, 5.0):                  # clear of both side bridges and the trees
        waystone(p, math.cos(a) * 46, math.sin(a) * 46, rz=a)
    great_tree(p, -70, 58, trunk=6)
    crystal_cluster(p, 74, -40, s=1.4, n=6)
    aether_fall(p, 58, 24, FLOOR_Z - 1.4, (0.9, 0.44), width=10, drop=80, z_bottom=-80)
    blossoms(p, 0, 0, 55, 50)
    grass_tufts(p, 0, 0, 55, 16)
    for k in range(4):
        mushroom(p, -22 + k * 5, 30 - k * 3, s=1.2)


# ---------------------------------------------------------------------------
# B: lush cloudscape
# ---------------------------------------------------------------------------
def sample_lush_cloudscape(p):
    pins(p)
    cloud_floor(p)
    perimeter_banks(p, density=0.8)
    for card in ("N", "S"):
        mouth(p, card)
    path(p, [(0, -57), (-10, -20), (8, 20), (0, 57)], width=14)
    for cx, cy, r in ((-58, 34, 44), (56, -38, 44), (60, 58, 30), (-60, -62, 30)):
        meadow_carpet(p, cx, cy, r)
    meadow_carpet(p, 0, 0, 36)
    # a pond with stepping stones and a little footbridge
    aether_pool(p, 52, 30, 18)
    plank_bridge(p, (34, 30), (70, 30), width=6)
    great_tree(p, -60, 38, trunk=7)
    mesa(p, 62, -52, 26, top=6)
    pavilion(p, 62, -52, 6, 10, 10, 9, rz=0.3, roof="slab")
    ramp(p, (40, -34), (48, -40), 8, FLOOR_Z, 6)
    for x, y in ((-30, 70), (-80, -10), (30, 76), (-20, -80)):
        ruin_wall(p, (x - 8, y), (x + 8, y + 4), h=6)
    for k in range(3):
        column(p, 26 + k * 10, -80, FLOOR_Z, 18, broken=k != 1)
    scatter(p, lambda p_, x, y: tree(p_, x, y, h=p.rng.uniform(16, 28), crown=TEAL if p.rng.random() < .55 else INDIGO,
                                     style=p.rng.randrange(3)), 14, (0, 0, 104), clear=8)
    scatter(p, lambda p_, x, y: mushroom(p_, x, y, s=p.rng.uniform(1, 1.8)), 16, (0, 0, 100), clear=2)
    scatter(p, lambda p_, x, y: rock(p_, x, y, s=p.rng.uniform(1.5, 3)), 8, (0, 0, 100), clear=3)
    blossoms(p, 0, 0, 104, 220)
    grass_tufts(p, 0, 0, 104, 60)
    for k in range(4):
        lantern_post(p, 18, -40 + k * 26, rz=0)


# ---------------------------------------------------------------------------
# C: temple city
# ---------------------------------------------------------------------------
def sample_temple_city(p):
    pins(p)
    cloud_floor(p)
    perimeter_banks(p, density=0.6)
    for card in ("N", "S"):
        mouth(p, card)
    # the avenue: a broad flagstone road lined by a colonnade, under an arch
    decal(p, "TempleIvory", [(-30, -114), (30, -114), (30, 114), (-30, 114)], FLOOR_Z + 0.02)
    for gy in range(-110, 111, 8):
        decal_strip(p, "CloudWhite", (-29, gy), (29, gy), 0.4, FLOOR_Z + 0.04)
    decal_strip(p, "GoldenPath", (0, -114), (0, 114), 6, FLOOR_Z + 0.05)
    for s in (-1, 1):
        for k in range(-4, 5):
            y = k * 22
            if abs(y) < 10:
                continue
            column(p, s * 26, y, FLOOR_Z, 26, r=2.2, broken=(k * s) % 3 == 0)
        beam(p, "TempleIvory", (s * 26, -88, 27.5), (s * 26, -22, 27.5), 5, 3)
        beam(p, "TempleIvory", (s * 26, 22, 27.5), (s * 26, 88, 27.5), 5, 3)
    arch(p, 0, 0, FLOOR_Z, 40, 40, rz=0.0, thick=6)
    # east quarter: a raised plaza terrace with a shrine hall, reached by stairs
    prism(p, [(40, -20), (100, -20), (100, 70), (40, 70)], FLOOR_Z - 0.5, 6, "TempleIvory", side="Cloudstone")
    for (ax, ay), (bx, by) in (((40, -20), (100, -20)), ((100, -20), (100, 70)), ((100, 70), (40, 70)), ((40, 70), (40, -20))):
        beam(p, "TempleGold", (ax, ay, 4.8), (bx, by, 4.8), 1.2, 1.2)
    stairs(p, 28, 33, FLOOR_Z, 6, 14, 0.0)          # between the colonnade's columns at y 22 and 44
    shrine_hall(p, 72, 40, 6, 30, 26, rz=math.pi / 2 + math.pi)
    for y in (-10, 66):
        statue(p, 46, y, 6, rz=math.pi)
    # west quarter: a sunken court with a fountain, statues and a bell tower
    fountain(p, -66, -20)
    for a in (0.5, 2.1, 3.7, 5.3):
        statue(p, -66 + math.cos(a) * 20, -20 + math.sin(a) * 20, rz=a + math.pi)
    decal_ring(p, "GoldenPath", -66, -20, 12, 14, FLOOR_Z + 0.05, n=20)
    bell_tower(p, -72, 52, rz=0.2)
    ruin_wall(p, (-100, -70), (-50, -84), h=9)
    ruin_wall(p, (60, -84), (98, -70), h=7)
    for x, y in ((-40, 84), (40, 88), (-40, -96), (70, -100)):
        lantern_post(p, x, y, rz=0)
    for x, y in ((-96, 20), (96, -50), (-90, -50)):
        tree(p, x, y, h=22, crown=TEAL, style=1)


SAMPLES = [
    dict(id="SAMPLE_A_FLOATING_ISLES", fn=sample_floating_isles, desc="Floating isles in open sky"),
    dict(id="SAMPLE_B_LUSH_CLOUDSCAPE", fn=sample_lush_cloudscape, desc="Lush meadow cloudscape"),
    dict(id="SAMPLE_C_TEMPLE_CITY", fn=sample_temple_city, desc="Ruined temple city in cloud"),
]
