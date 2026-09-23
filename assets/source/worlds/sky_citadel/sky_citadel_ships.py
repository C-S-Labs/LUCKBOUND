"""Raider warships -- five designs, one per mesh, 2,500-5,000 triangles each.

Executed by build_sky_citadel_scenarios.py into its namespace (it needs the
kit's primitives: box, frustum, torus, crystal, tube, lump, add_faces).

Owner, 2026-09-23: "the raider boats have no variation." A moored warship is
now one of five ships, and the game picks which per run (the prop row carries
the others as `Alt`, PropController draws one by the run's seed), so the same
dock holds a different ship in different runs.

Every design shares one frame and one envelope, so any of them fits wherever
the scenario moored a warship:
  * prow toward +X, the deck at z = 0 amidships;
  * inside x -40..44, y -10.5..10.5, z -10.5..33 (the float the scenario
    registers for the berth);
  * the boarding rail -- where the gangway lands -- at |y| = 8.2, z ~ 0.5,
    between x -6 and 6.
Every part is joined to the hull (geometry_checks runs on each design), and
nothing is single-sided: bulwarks have an inner face, sails both.
"""

import math
import random

from mathutils import Vector


SHIP_ENVELOPE = (-40.0, 44.0, -10.5, 10.5, -10.5, 33.0)
BOARD_Y = 8.2


# ==========================================================================
# Shipwright's tools
# ==========================================================================

def loft_hull(p, stations, bands, deck_mat="Twig", rail_mat="DeepAlloy", inset=0.5, deck_drop=0.8):
    """A closed hull through stations (x, half-beam, depth, sheer): the outer
    skin from gunwale to keel, a bulwark with its inner face, and the deck.
    `bands` maps the outer skin's segments (top to keel, 0-based) to materials.
    A station with half-beam 0 is the prow's point."""
    # the cross-section, port gunwale round the keel to starboard, then in and
    # down to the deck, which closes the loop
    outer = [(1.0, 0.0), (1.0, -0.18), (0.97, -0.38), (0.88, -0.6), (0.7, -0.8), (0.42, -0.94), (0.0, -1.0)]
    verts, faces, mats, rings = [], [], [], []
    for x, hw, d, sh in stations:
        s = len(verts)
        if hw <= 1e-6:
            verts.append((x, 0.0, sh - d * 0.35))
            rings.append([s])
            continue
        ring = []
        port = [(x, fy * hw, sh + fz * d) for fy, fz in outer]            # gunwale -> keel
        star = [(x, -fy * hw, sh + fz * d) for fy, fz in reversed(outer[:-1])]  # keel -> gunwale
        ins = min(inset, hw * 0.3)
        inner = [(x, -(hw - ins), sh), (x, -(hw - ins), sh - deck_drop),
                 (x, hw - ins, sh - deck_drop), (x, hw - ins, sh)]
        for q in port + star + inner:
            verts.append(q)
            ring.append(len(verts) - 1)
        rings.append(ring)
    n = len(rings[0])
    nseg = len(outer) - 1

    def seg_mat(j):
        if j < nseg:
            return bands[min(j, len(bands) - 1)]
        if j < 2 * nseg:
            return bands[min(2 * nseg - 1 - j, len(bands) - 1)]
        k = j - 2 * nseg
        return (rail_mat, rail_mat, deck_mat, rail_mat, rail_mat)[k] if k < 5 else rail_mat

    for A, B in zip(rings, rings[1:]):
        for j in range(n):
            j2 = (j + 1) % n
            if len(B) == 1:
                faces.append((A[j], A[j2], B[0]))
            elif len(A) == 1:
                faces.append((A[0], B[j2], B[j]))
            else:
                faces.append((A[j], A[j2], B[j2], B[j]))
            mats.append(seg_mat(j))
    if len(rings[0]) > 1:
        faces.append(tuple(reversed(rings[0])))
        mats.append(bands[0])
    if len(rings[-1]) > 1:
        faces.append(tuple(rings[-1]))
        mats.append(bands[0])
    add_faces(p, verts, faces, mats)


def hull_at(stations, x):
    """Half-beam, depth and sheer of a lofted hull at x (linear between stations)."""
    for (x0, w0, d0, s0), (x1, w1, d1, s1) in zip(stations, stations[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return w0 + (w1 - w0) * t, d0 + (d1 - d0) * t, s0 + (s1 - s0) * t
    x0, w0, d0, s0 = stations[0] if x < stations[0][0] else stations[-1]
    return w0, d0, s0


def cloth(p, mats, c00, c10, c01, c11, bulge, nu=6, nv=6, seed="sail", patch=0.18):
    """A sail: a bilinear sheet between four corners, bellied out along its
    normal by `bulge` at the middle, both sides faced, with patched panels."""
    rng = random.Random(seed)
    c00, c10, c01, c11 = Vector(c00), Vector(c10), Vector(c01), Vector(c11)
    nrm = (c10 - c00).cross(c01 - c00).normalized()
    verts = []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            q = c00 * (1 - u) * (1 - v) + c10 * u * (1 - v) + c01 * (1 - u) * v + c11 * u * v
            q = q + nrm * bulge * math.sin(math.pi * u) * math.sin(math.pi * v)
            verts.append(tuple(q))
    faces, fm = [], []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b, c, d = a + 1, a + nu + 2, a + nu + 1
            m = mats[1] if (len(mats) > 1 and rng.random() < patch) else mats[0]
            faces += [(a, b, c, d), (a, d, c, b)]
            fm += [m, m]
    add_faces(p, verts, faces, fm)


def ellipsoid(p, mats, cx, cy, cz, rx, ry, rz, nu=20, nv=10, seed="bag", patch=0.2):
    """A gas envelope: lat-long ellipsoid, long along x, in patched panels."""
    rng = random.Random(seed)
    verts = [(cx - rx, cy, cz)]
    for j in range(1, nv):
        a = math.pi * j / nv
        x = cx - rx * math.cos(a)
        s = math.sin(a)
        for i in range(nu):
            b = 2 * math.pi * i / nu
            verts.append((x, cy + ry * s * math.cos(b), cz + rz * s * math.sin(b)))
    verts.append((cx + rx, cy, cz))
    faces, fm = [], []
    last = len(verts) - 1
    for i in range(nu):
        faces.append((0, 1 + (i + 1) % nu, 1 + i))
        fm.append(mats[0])
    for j in range(nv - 2):
        r0, r1 = 1 + j * nu, 1 + (j + 1) * nu
        for i in range(nu):
            i2 = (i + 1) % nu
            faces.append((r0 + i, r0 + i2, r1 + i2, r1 + i))
            fm.append(mats[1] if (len(mats) > 1 and rng.random() < patch) else mats[0])
    r0 = 1 + (nv - 2) * nu
    for i in range(nu):
        faces.append((r0 + i, r0 + (i + 1) % nu, last))
        fm.append(mats[0])
    add_faces(p, verts, faces, fm)


def rope(p, a, b, r=0.09, mat="Twig"):
    tube(p, mat, [a, b], [r, r], n=3)


def mast(p, x, h, r0=0.9, r1=0.45, mat="DeepAlloy", z0=-0.9):
    frustum(p, mat, 10, r0, r1, z0, h, x, 0)
    for z in (h * 0.25, h * 0.55):
        frustum(p, "RaiderRust", 10, r0 * 1.15, r0 * 1.15, z, z + 0.6, x, 0)


def yard(p, x, z, span, mat="DeepAlloy"):
    frustum(p, mat, 8, 0.32, 0.32, -span / 2, span / 2, M=xf(x, 0, z, 0, -90, 0))


def cannon(p, x, y, z, side, L=3.2):
    """A deck gun: carriage and barrel, run out through the bulwark."""
    box(p, "Twig", x, y - side * 0.4, z + 0.45, 1.6, 1.8, 0.9)
    for dx in (-0.6, 0.6):
        frustum(p, "Soot", 8, 0.35, 0.35, -0.3, 0.3, M=xf(x + dx, y - side * 0.4, z + 0.3, 0, 0, 90))
    with frame(p, xf(x, y, z + 1.1, 0 if side > 0 else 180, 0, 0)):
        frustum(p, "Soot", 10, 0.42, 0.34, -0.8, L, M=xf(rx=-90))
        frustum(p, "DeepAlloy", 10, 0.5, 0.5, L - 0.4, L, M=xf(rx=-90))


def lantern(p, x, y, z):
    frustum(p, "DeepAlloy", 6, 0.12, 0.12, z, z + 1.6, x, y)
    frustum(p, "EmberGlow", 6, 0.35, 0.35, z + 1.6, z + 2.3, x, y)
    frustum(p, "DeepAlloy", 6, 0.45, 0.0, z + 2.3, z + 2.8, x, y)


def rail_posts(p, pts, h=1.2, mat="DeepAlloy"):
    """Posts along a polyline and a rail along their tops."""
    for q in pts:
        frustum(p, mat, 4, 0.12, 0.12, q[2] - 0.2, q[2] + h, q[0], q[1])
    tube(p, mat, [(q[0], q[1], q[2] + h) for q in pts], [0.1] * len(pts), n=4)


def thruster(p, x, y, z, r=2.0, L=4.0):
    with frame(p, xf(x, y, z, 0, 0, -90)):
        frustum(p, "DeepAlloy", 12, r, r * 0.8, 0, L)
        frustum(p, "RaiderRust", 12, r * 1.08, r * 1.08, L * 0.3, L * 0.45)
        frustum(p, "EmberGlow", 12, r * 0.7, r * 0.7, L, L + 0.4)


def flag(p, x, z, w=4.0, h=2.4, seed="flag", y=0.0):
    cloth(p, ("RaiderRust", "Soot"), (x, y, z), (x - w, y, z + 0.3), (x, y, z - h), (x - w, y, z - h + 0.6),
          0.5, nu=5, nv=3, seed=seed, patch=0.3)


def strakes(p, st, fzs=(-0.18, -0.6), r=0.16, mat="Soot", y_scale=1.0, x_from=None, x_to=None):
    """Rub rails along both flanks, riding the hull's own curve."""
    pts_x = [x for x, hw, d, sh in st if hw > 0.5 and (x_from is None or x >= x_from) and (x_to is None or x <= x_to)]
    for fz in fzs:
        fy = {-0.18: 1.0, -0.38: 0.97, -0.6: 0.88, -0.8: 0.7}.get(fz, 0.9)
        for sy in (-1, 1):
            path, rad = [], []
            for x in pts_x:
                hw, d, sh = hull_at(st, x)
                path.append((x, sy * (hw * fy * y_scale + r * 0.3), sh + fz * d))
                rad.append(r)
            if len(path) > 1:
                tube(p, mat, path, rad, n=4)


def portholes(p, st, xs, fz=-0.38, r=0.55, mat="EmberGlow", rim="DeepAlloy"):
    """Round ports along both flanks, their rims standing proud of the skin."""
    for x in xs:
        hw, d, sh = hull_at(st, x)
        z = sh + fz * d
        for sy in (-1, 1):
            y = sy * hw * 0.97
            with frame(p, xf(x, y, z, 0, -90 * sy, 0)):
                frustum(p, rim, 8, r * 1.35, r * 1.2, -0.3, 0.35)
                frustum(p, mat, 8, r, r, 0.3, 0.42)


# ==========================================================================
# The five ships
# ==========================================================================

def ship_reaver(p):
    """REAVER: the classic -- a patched galleon, two masts of square sail, a
    stern castle, a gun deck, and a ram."""
    st = [(-34, 5.2, 5.5, 3.2), (-31, 6.8, 7.0, 2.6), (-26, 7.8, 8.5, 1.4), (-18, 8.2, 9.5, 0.5), (-8, 8.2, 9.8, 0.0),
          (2, 8.2, 9.8, 0.0), (12, 7.9, 9.5, 0.2), (20, 7.0, 8.6, 0.7), (27, 5.6, 7.0, 1.4), (32, 3.8, 5.0, 2.2),
          (36, 2.0, 3.2, 3.0), (38.5, 0.0, 1.6, 3.6)]
    loft_hull(p, st, ["RaiderRust", "RaiderRust", "DeepAlloy", "Soot", "Soot", "Char"])
    # keel fin and the ram
    box(p, "DeepAlloy", 0, 0, -9.9, 60, 0.6, 1.2)
    with frame(p, xf(38.0, 0, 2.2, 0, 0, 90)):
        frustum(p, "Soot", 6, 1.3, 0.0, 0, 5.8)
    for k in (-1, 1):
        crystal(p, "Soot", 36.5, k * 1.3, 3.2, 0.35, 0.3, 0.3, rz=0)
    # stern castle, two storeys, lit windows, a railed roof
    box(p, "RaiderRust", -27, 0, 2.6, 11, 12.0, 5.2)
    box(p, "Twig", -27, 0, 5.4, 11.8, 12.8, 0.5)
    box(p, "DeepAlloy", -28, 0, 7.3, 7, 9, 3.4)
    box(p, "Twig", -28, 0, 9.2, 7.6, 9.6, 0.4)
    for sy in (-1, 1):
        for x in (-31, -27, -23):
            box(p, "EmberGlow", x, sy * 6.02, 3.0, 1.4, 0.1, 1.3)
        for x in (-30, -26):
            box(p, "EmberGlow", x, sy * 4.52, 7.4, 1.2, 0.1, 1.0)
    rail_posts(p, [(-32.6, -6.2, 5.65), (-27, -6.2, 5.65), (-21.4, -6.2, 5.65)])
    rail_posts(p, [(-32.6, 6.2, 5.65), (-27, 6.2, 5.65), (-21.4, 6.2, 5.65)])
    for sy in (-1, 1):
        lantern(p, -32.4, sy * 5.4, 5.65)
    # forecastle
    box(p, "RaiderRust", 26, 0, 1.2, 9, 9.5, 2.4)
    box(p, "Twig", 26, 0, 2.5, 9.6, 10.0, 0.3)
    # masts, yards, square sails, a crow's nest
    for mx, h, spans in ((-6, 31.0, (17, 14, 10)), (13, 27.0, (15, 12, 8))):
        mast(p, mx, h)
        zs = (h * 0.34, h * 0.6, h * 0.84)
        for z, sp in zip(zs, spans):
            yard(p, mx, z, sp)
        for (za, sa), (zb, sb) in zip(zip(zs, spans), zip(zs[1:], spans[1:])):
            cloth(p, ("RaiderRust", "Char"), (mx + 0.45, -sa / 2 + 0.3, za - 0.25), (mx + 0.45, sa / 2 - 0.3, za - 0.25),
                  (mx + 0.45, -sb / 2 + 0.3, zb + 0.25), (mx + 0.45, sb / 2 - 0.3, zb + 0.25), 1.6,
                  seed="reaver sail %d %d" % (mx, za))
        cloth(p, ("RaiderRust", "Char"), (mx + 0.45, -spans[0] / 2 + 0.6, 2.6), (mx + 0.45, spans[0] / 2 - 0.6, 2.6),
              (mx + 0.45, -spans[0] / 2 + 0.3, zs[0] - 0.25), (mx + 0.45, spans[0] / 2 - 0.3, zs[0] - 0.25), 1.2,
              seed="reaver course %d" % mx)
        for sy in (-1, 1):
            hw, d, sh = hull_at(st, mx - 3)
            rope(p, (mx, 0, h - 1.5), (mx - 3, sy * (hw - 0.3), sh))
            hw, d, sh = hull_at(st, mx + 3)
            rope(p, (mx, 0, h * 0.6), (mx + 3, sy * (hw - 0.3), sh))
    frustum(p, "Twig", 10, 1.9, 2.2, 25.4, 26.8, -6, 0)
    for k in range(8):
        a = math.radians(45 * k)
        frustum(p, "Twig", 4, 0.1, 0.1, 26.8, 27.8, -6 + math.cos(a) * 2.0, math.sin(a) * 2.0)
    torus(p, "Twig", 2.0, 0.1, -6, 0, 27.8, n=12)
    flag(p, -6.4, 33.0, seed="reaver flag")
    rope(p, (-6, 0, 30.5), (13, 0, 26.5))
    rope(p, (13, 0, 26.0), (37.5, 0, 3.6))
    # guns, three a side, and the hull's own detail
    for sy in (-1, 1):
        for gx in (-12, -2, 8):
            cannon(p, gx, sy * 6.9, -0.8, sy)
    strakes(p, st, fzs=(-0.18, -0.38, -0.6))
    portholes(p, st, (-22, -16, -10, -4, 2, 8, 14, 20))
    for k in range(6):                                  # barrels and a shot rack on the deck
        frustum(p, "Twig", 8, 0.7, 0.7, -0.8, 0.9, 20 - k * 1.5, -3.6 + (k % 2) * 1.4)
    box(p, "DeepAlloy", 4, 3.4, -0.4, 3.0, 1.0, 0.8)
    for k in range(5):
        frustum(p, "Soot", 6, 0.35, 0.35, 0.0, 0.7, 2.8 + k * 0.6, 3.4)
    # drives under the transom
    for sy in (-1, 1):
        thruster(p, -32.8, sy * 3.0, -1.2, r=1.8, L=5.5)
        box(p, "DeepAlloy", -33.8, sy * 3.0, -0.9, 2.4, 1.0, 2.4)


def ship_gasbag(p):
    """CORSAIR: a lean hull slung under a patched gas envelope on cables,
    finned at the tail, driven by twin props."""
    st = [(-26, 4.8, 4.2, 1.8), (-22, 6.6, 5.6, 1.0), (-14, 7.8, 6.6, 0.3), (-6, 8.2, 7.0, 0.0), (6, 8.2, 7.0, 0.0),
          (14, 7.6, 6.6, 0.3), (22, 6.0, 5.4, 1.0), (28, 3.8, 3.8, 1.8), (32, 1.6, 2.2, 2.6), (34.5, 0.0, 1.0, 3.0)]
    loft_hull(p, st, ["DeepAlloy", "RaiderRust", "RaiderRust", "Soot", "Soot", "Char"])
    box(p, "DeepAlloy", 2, 0, -7.0, 44, 0.5, 1.0)
    ellipsoid(p, ("RaiderRust", "Twig"), 0, 0, 22.5, 31, 8.8, 8.2, nu=28, nv=16, seed="corsair bag")
    for x in (-20, -10, 0, 10, 20):                     # girdle bands round the bag
        t = x / 31.0
        s = math.sqrt(max(0.0, 1 - t * t))
        with frame(p, xf(x, 0, 22.5, 0, 0, 90)):
            torus(p, "DeepAlloy", 8.45 * s, 0.24, 0, 0, 0, n=24)
    # tail fins, their roots sunk in the bag's taper
    box(p, "DeepAlloy", -28.5, 0, 27.2, 5, 0.4, 5.0)
    box(p, "DeepAlloy", -28.5, 0, 22.5, 5, 13.6, 0.4)
    box(p, "DeepAlloy", -28.5, 0, 17.8, 5, 0.4, 5.0)
    # the keel boom under the bag, and the cables down to the gunwales
    frustum(p, "DeepAlloy", 8, 0.45, 0.45, -22, 22, M=xf(0, 0, 14.6, 0, 0, 90))
    for x in (-18, -8, 2, 12, 20):
        hw, d, sh = hull_at(st, x)
        for sy in (-1, 1):
            rope(p, (x, 0, 14.4), (x, sy * (hw - 0.25), sh), r=0.1, mat="DeepAlloy")
    for x in (-14, 16):
        frustum(p, "DeepAlloy", 8, 0.35, 0.35, -0.9, 14.6, x, 0)
    # the gondola cabin amidships, standing on the deck
    box(p, "RaiderRust", -4, 0, 1.4, 14, 8.6, 4.4)
    box(p, "Twig", -4, 0, 3.8, 15, 9.4, 0.4)
    for sy in (-1, 1):
        for x in (-9, -5, -1, 3):
            box(p, "EmberGlow", x, sy * 4.32, 1.8, 1.6, 0.1, 1.2)
    strakes(p, st, fzs=(-0.18, -0.6))
    portholes(p, st, (-16, -10, 10, 16, 22))
    # twin props on outrigger struts
    for sy in (-1, 1):
        box(p, "DeepAlloy", -22, sy * 6.0, 1.0, 1.0, 3.2, 0.8)
        with frame(p, xf(-24.2, sy * 7.3, 1.0, 0, 0, -90)):
            frustum(p, "DeepAlloy", 10, 0.9, 0.6, -2.4, 2.6)
            for k in range(4):
                with frame(p, xf(0, 0, 2.4, 45 + 90 * k, 0, 18)):
                    box(p, "Twig", 0, 1.5, 0, 0.9, 3.0, 0.2)
    # a harpoon ballista on the bow
    box(p, "Twig", 24, 0, 1.4, 2.4, 2.4, 1.6)
    with frame(p, xf(24, 0, 2.5, 0, -8, 0)):
        box(p, "DeepAlloy", 2.0, 0, 0, 6, 0.6, 0.6)
        box(p, "Twig", 0.6, 0, 0.2, 0.6, 7.2, 0.5)
        crystal(p, "Soot", 5.4, 0, 0, 0.5, 0.1, 0.1)
    for sy in (-1, 1):
        lantern(p, -21.0, sy * 3.2, 0.1)
    for x in (-16, -12, 8, 12, 16):                      # cargo lashed on deck
        box(p, "Twig", x, 2.4 if x % 8 else -2.4, 0.3, 2.2, 2.2, 2.2, rz=8)


def ship_dreadnought(p):
    """DREADNOUGHT: a scrap ironclad -- slab hull hung with armour plates,
    two gun turrets, smokestacks, a spiked ram, a bridge at the stern."""
    st = [(-35, 7.2, 6.0, 2.4), (-32, 8.0, 7.5, 1.4), (-24, 8.2, 8.0, 0.4), (-10, 8.2, 8.2, 0.0), (10, 8.2, 8.2, 0.0),
          (22, 8.0, 8.0, 0.3), (30, 7.0, 7.0, 0.9), (35, 5.0, 5.0, 1.6), (38, 2.6, 3.0, 2.0), (39.5, 0.0, 1.5, 2.2)]
    loft_hull(p, st, ["Soot", "DeepAlloy", "DeepAlloy", "RaiderRust", "Char", "Char"], deck_mat="DeepAlloy",
              rail_mat="Soot", inset=0.7, deck_drop=1.1)
    rng = random.Random("dreadnought plates")
    for sy in (-1, 1):                                  # armour, bolted in two courses
        for x in range(-28, 30, 5):
            hw, d, sh = hull_at(st, x)
            for course, zc in enumerate((-2.0, -4.6)):
                box(p, rng.choice(("RaiderRust", "Soot", "DeepAlloy")), x + rng.uniform(-0.5, 0.5),
                    sy * (hw * (0.99 if course == 0 else 0.93) - 0.05), sh + zc, 4.4, 0.5, 2.3,
                    rz=rng.uniform(-3, 3), rx=sy * (4 if course == 0 else 16))
    # the ram: a crown of spikes on the prow
    for k, (dy, dz) in enumerate(((0, 1.8), (-1.2, 0.9), (1.2, 0.9), (0, 0.6))):
        with frame(p, xf(38.6, dy, dz, 0, 0, 90)):
            frustum(p, "Soot", 6, 0.8 if k == 0 else 0.55, 0.0, 0, 5.2 if k == 0 else 3.4)
    # turrets fore and aft of amidships
    for tx, rz in ((16, 10), (-14, 170)):
        frustum(p, "DeepAlloy", 12, 4.0, 3.6, -1.1, 1.2, tx, 0)
        frustum(p, "Soot", 12, 3.4, 2.6, 1.2, 3.6, tx, 0)
        with frame(p, xf(tx, 0, 2.6, rz)):
            for sy in (-0.8, 0.8):
                with frame(p, xf(2.4, sy, 0, 0, 0, 86)):
                    frustum(p, "Soot", 10, 0.5, 0.42, 0, 7.5)
                    frustum(p, "DeepAlloy", 10, 0.62, 0.62, 6.8, 7.5)
    # smokestacks with bands and soot at the lip
    for sx, h in ((-2, 17.0), (4, 19.0)):
        frustum(p, "RaiderRust", 12, 1.9, 1.6, -1.1, h, sx, 0)
        for z in (h * 0.3, h * 0.65):
            frustum(p, "DeepAlloy", 12, 2.05, 2.05, z, z + 0.7, sx, 0)
        frustum(p, "Soot", 12, 1.8, 2.2, h, h + 1.2, sx, 0)
        frustum(p, "EmberGlow", 12, 1.3, 1.3, h + 0.6, h + 1.25, sx, 0)
    # the bridge at the stern: a stepped block with a window band and an aerial
    box(p, "DeepAlloy", -27, 0, 3.2, 10, 11, 6.4)
    box(p, "Soot", -27.5, 0, 8.0, 7, 8, 3.2)
    for sy in (-1, 1):
        box(p, "EmberGlow", -27.5, sy * 4.02, 8.2, 5.6, 0.1, 1.1)
    box(p, "EmberGlow", -23.98, 0, 8.2, 0.1, 6.2, 1.1)
    frustum(p, "DeepAlloy", 6, 0.2, 0.08, 9.6, 21.0, -29, 2.5)
    frustum(p, "DeepAlloy", 6, 0.2, 0.08, 9.6, 16.0, -29, -2.5)
    flag(p, -29.1, 20.6, w=3.4, h=2.0, seed="dread flag", y=2.5)
    strakes(p, st, fzs=(-0.18, -0.8), r=0.2)
    portholes(p, st, (-20, -14, 22, 28), fz=-0.18, r=0.45)
    for x in (-10, 10, 24):                              # deck vents
        frustum(p, "Soot", 10, 0.9, 0.9, -1.1, 1.6, x, 4.5)
        frustum(p, "DeepAlloy", 10, 1.1, 0.4, 1.6, 2.4, x, 4.5)
    rail_posts(p, [(-20, 7.3, -0.1), (-12, 7.3, -0.1), (-4, 7.3, -0.1)])
    rail_posts(p, [(-20, -7.3, -0.1), (-12, -7.3, -0.1), (-4, -7.3, -0.1)])
    frustum(p, "DeepAlloy", 8, 0.3, 0.3, 9.6, 12.4, -25, 0)   # a searchlight on the bridge
    with frame(p, xf(-25, 0, 12.8, 0, 0, 80)):
        frustum(p, "DeepAlloy", 10, 0.9, 1.1, -0.9, 0.9)
        frustum(p, "EmberGlow", 10, 0.95, 0.95, 0.9, 1.0)
    # chains to the anchors, hawse pipes at the bow
    for sy in (-1, 1):
        box(p, "Soot", 30, sy * 7.2, -1.0, 1.4, 0.8, 1.4)
        tube(p, "DeepAlloy", [(30, sy * 7.5, -1.4), (31.5, sy * 8.4, -5.0), (32.5, sy * 8.6, -8.0)],
             [0.25, 0.25, 0.25], n=4)
        box(p, "Soot", 32.5, sy * 8.6, -8.8, 1.8, 0.5, 1.8)
    # drives
    for sy in (-2.8, 2.8):
        thruster(p, -33.8, sy, -0.6, r=2.2, L=5.0)


def ship_clipper(p):
    """WING CLIPPER: a knife of a hull under a single tall mast and a lateen
    sail, bat-wing sails spread from its flanks, sponsons to board by."""
    st = [(-30, 3.2, 4.0, 2.0), (-26, 4.6, 5.2, 1.2), (-16, 5.4, 6.0, 0.4), (-4, 5.6, 6.2, 0.0), (8, 5.4, 6.0, 0.2),
          (18, 4.6, 5.2, 0.8), (26, 3.2, 4.0, 1.6), (32, 1.6, 2.6, 2.4), (35.5, 0.0, 1.2, 3.0)]
    loft_hull(p, st, ["Char", "RaiderRust", "RaiderRust", "DeepAlloy", "Soot", "Soot"])
    box(p, "DeepAlloy", 2, 0, -6.6, 50, 0.4, 1.4)
    # sponsons: the boarding decks amidships, railed fore and aft
    for sy in (-1, 1):
        box(p, "Twig", 0, sy * 6.9, -0.4, 13, 2.8, 0.5)
        box(p, "RaiderRust", 0, sy * 6.9, -1.6, 12, 2.6, 1.9)
        for x in (-6.2, 6.2):
            frustum(p, "DeepAlloy", 4, 0.12, 0.12, -0.2, 1.1, x, sy * 7.9)
        box(p, "DeepAlloy", -6.2, sy * 7.9, 1.1, 0.2, 0.2, 0.2)
    # bowsprit
    frustum(p, "DeepAlloy", 8, 0.45, 0.2, -3.0, 8.0, M=xf(34.0, 0, 2.3, 0, 0, 80))
    # the tall mast and its lateen yard
    mast(p, 4, 32.0, r0=0.8, r1=0.35)
    with frame(p, xf(4, 0, 17, 0, 0, 0)):
        frustum(p, "DeepAlloy", 8, 0.3, 0.3, -20, 18, M=xf(0, 0, 0, 0, 0, -58))
    cloth(p, ("Twig", "RaiderRust"), (-15.0, 0.5, 6.8), (22.0, 0.5, 4.6), (-8.0, 0.5, 23.5), (4.4, 0.5, 30.5),
          1.4, nu=8, nv=6, seed="clipper lateen")
    # the bat wings: ribs from the hull out to the envelope, cloth between
    for sy in (-1, 1):
        root = [(-18, sy * 4.9, 0.1), (-6, sy * 5.2, -0.1), (6, sy * 5.0, 0.0)]
        tips = [(-22, sy * 10.2, 13.5), (-8, sy * 10.3, 16.5), (8, sy * 10.1, 11.0)]
        for a, b in zip(root, tips):
            tube(p, "DeepAlloy", [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sy * 0.5, (a[2] + b[2]) / 2 + 1.0), b],
                 [0.35, 0.28, 0.18], n=5)
        for (a0, b0), (a1, b1) in zip(zip(root, tips), zip(root[1:], tips[1:])):
            cloth(p, ("Char", "RaiderRust"), a0, a1, b0, b1, 0.9 * sy, nu=5, nv=5, seed="wing %d %d" % (sy, a0[0]))
    # stern cabin and drive
    box(p, "RaiderRust", -24, 0, 1.6, 8, 7, 3.2)
    box(p, "Twig", -24, 0, 3.4, 8.6, 7.6, 0.4)
    for sy in (-1, 1):
        box(p, "EmberGlow", -24, sy * 3.52, 1.8, 4, 0.1, 1.0)
    thruster(p, -29.0, 0, 0.2, r=1.6, L=5.0)
    rope(p, (4, 0, 31.0), (34.8, 0, 4.0))
    rope(p, (4, 0, 31.0), (-29.0, 0, 2.2))
    for sy in (-1, 1):
        rope(p, (4, 0, 24.0), (2.0, sy * 5.2, 0.1))
    flag(p, 3.9, 31.8, w=3.0, h=1.8, seed="clipper flag")
    cannon(p, 20, 1.0, -0.8, 1, L=3.8)
    cannon(p, 20, -1.0, -0.8, -1, L=3.8)
    strakes(p, st, fzs=(-0.18, -0.38, -0.6), r=0.14)
    portholes(p, st, (-18, -12, 12, 18), r=0.45)
    cloth(p, ("Twig", "RaiderRust"), (33.8, 0.3, 3.6), (4.6, 0.3, 1.2), (33.8, 0.3, 3.9), (4.6, 0.3, 26.0), 0.8,
          nu=6, nv=4, seed="clipper jib")
    for k in range(4):                                   # water casks and a crate on the deck
        frustum(p, "Twig", 8, 0.6, 0.6, -0.8, 0.8, 12 + k * 1.3, -2.8)
    box(p, "RaiderRust", 14, 2.6, 0.1, 2.0, 2.0, 1.8, rz=12)


def ship_barge(p):
    """RAIDER BARGE: twin hulls under one deck -- a floating raider camp:
    a prisoner cage, a loot crane, a tent, stacked plunder, a war banner."""
    for sy in (-1, 1):
        st = [(-32, 1.6, 3.0, 1.2), (-28, 2.8, 4.6, 0.4), (-16, 3.2, 5.4, 0.0), (10, 3.2, 5.4, 0.0),
              (24, 2.8, 4.6, 0.4), (32, 1.4, 3.0, 1.2), (35.0, 0.0, 1.4, 1.8)]
        with frame(p, xf(0, sy * 5.8, 0)):
            loft_hull(p, st, ["RaiderRust", "DeepAlloy", "Soot", "Soot", "Char", "Char"], inset=0.35, deck_drop=0.5)
            strakes(p, st, fzs=(-0.38, -0.6), r=0.14)
            portholes(p, st, (-20, -10, 0, 10, 20), r=0.4)
    # the platform across both hulls
    box(p, "Twig", -1, 0, 0.3, 58, 17.0, 0.8)
    for x in range(-28, 28, 4):
        box(p, "Bark", x, 0, 0.72, 3.6, 16.6, 0.08)
    for sy in (-1, 1):
        box(p, "DeepAlloy", -1, sy * 8.3, 0.9, 58, 0.4, 0.5)
        for x in range(-28, 29, 7):
            frustum(p, "DeepAlloy", 4, 0.12, 0.12, 0.7, 2.0, x, sy * 8.3)
        tube(p, "DeepAlloy", [(-28, sy * 8.3, 2.0), (28, sy * 8.3, 2.0)], [0.1, 0.1], n=4)
    # prisoner cage
    cx = 14
    box(p, "DeepAlloy", cx, 0, 0.9, 7, 7, 0.4)
    box(p, "DeepAlloy", cx, 0, 6.1, 7, 7, 0.4)
    for k in range(12):
        t = k / 12.0
        per = t * 4
        side = int(per)
        f = per - side
        pos = [(-3.3 + 6.6 * f, -3.3), (3.3, -3.3 + 6.6 * f), (3.3 - 6.6 * f, 3.3), (-3.3, 3.3 - 6.6 * f)][side]
        frustum(p, "Soot", 6, 0.14, 0.14, 1.1, 5.9, cx + pos[0], pos[1])
    # the loot crane
    frustum(p, "DeepAlloy", 8, 0.8, 0.5, 0.7, 16.0, -6, -5)
    with frame(p, xf(-6, -5, 15.2, 30, 0, 0)):
        box(p, "DeepAlloy", 5.5, 0, 0, 13, 0.8, 0.8)
        box(p, "Soot", -1.8, 0, 0, 2.6, 1.6, 1.6)
        tube(p, "Twig", [(11.5, 0, -0.3), (11.5, 0, -9.0)], [0.08, 0.08], n=3)
        box(p, "RaiderRust", 11.5, 0, -10.2, 2.4, 2.4, 2.4)
    # a raider tent
    lump(p, "RaiderRust", [(4.2, 0.7), (4.4, 2.0), (3.2, 4.2), (0.6, 6.2), (0, 6.6)], n=8,
         seed="barge tent", jitter=0.08, cx=-18, cy=2.5)
    frustum(p, "DeepAlloy", 4, 0.12, 0.12, 6.2, 9.0, -18, 2.5)
    # plunder: crates and barrels, stacked against the rail
    rng = random.Random("barge plunder")
    for k in range(6):
        x = 0 + (k % 3) * 2.7
        box(p, rng.choice(("Twig", "RaiderRust")), x, 6.2, 1.9 + (k // 3) * 2.4, 2.4, 2.4, 2.4,
            rz=rng.uniform(-8, 8))
    for k in range(4):
        frustum(p, "Soot", 8, 1.0, 1.0, 0.7, 2.9, 24 - k * 2.3, -6.2)
        frustum(p, "DeepAlloy", 8, 1.05, 1.05, 1.5, 1.8, 24 - k * 2.3, -6.2)
    # the war banner
    frustum(p, "DeepAlloy", 8, 0.45, 0.25, 0.7, 30.0, -28, 0)
    yard(p, -28, 28.5, 10)
    cloth(p, ("RaiderRust", "Soot"), (-27.6, -4.7, 28.2), (-27.6, 4.7, 28.2), (-27.6, -4.2, 14.0), (-27.6, 4.2, 14.0),
          0.9, nu=4, nv=8, seed="barge banner")
    for sy in (-1, 1):
        thruster(p, -30.8, sy * 5.8, -0.2, r=1.4, L=5.0)
    for k in range(4):                                   # spikes along the cage roof
        crystal(p, "Soot", cx - 3 + k * 2, 0, 6.4, 0.3, 1.2, 0.2)
    lump(p, "Twig", [(3.2, 0.7), (3.4, 1.8), (2.4, 3.4), (0.4, 4.8), (0, 5.0)], n=7,
         seed="barge tent 2", jitter=0.08, cx=-12, cy=-3.5)
    for k in range(5):                                   # a bone pile by the cage
        with frame(p, xf(20 + (k % 3) * 0.8, 4.5 - k * 0.5, 0.9, k * 37, 0, 90)):
            frustum(p, "Bone", 6, 0.18, 0.14, -0.9, 0.9)
    lantern(p, 28, 5.0, 0.7)
    lantern(p, 28, -5.0, 0.7)


SHIPS = [ship_reaver, ship_gasbag, ship_dreadnought, ship_clipper, ship_barge]
