# Ethereal Scape kit -- terrain, architecture and flora builders.
#
# THE LOOK (owner-directed revamp, 2026-09-26): a GROUNDED cloudscape, not floating islands.
# Sky Citadel owns "islands over a void"; Verdant Valley owns "forest valley". Here the ground
# itself is walkable cloud; the original scene's meadow islands become MESAS rising out of it
# (gold rim band, faceted rock sides), clearings are walled by billowing cloud banks, and the
# verticality comes from gem-cut trees, great sky trees, crystal colossi, crags, bell towers
# and ruined colossal arches -- never needle spires.
import math

from mathutils import Vector

from es_geometry import (CROWN_TOP, DIRS, KEEL_BOTTOM, KIND_WIDTH, beam, blob, box, decal, decal_ring, decal_strip,
                         frustum, gem, gem2, prism, ring_pts, rod)

FLOOR_Z = 0.0


# ---------------------------------------------------------------------------
# Ground: the cloud floor, cloud banks, mesas
# ---------------------------------------------------------------------------
def pins(p):
    """0.3-stud pins at the midpoint of each tile edge on the keel line: they pin the
    mesh's box to exactly +-H and -96 whatever the terrain does (ChunkLoader stretches a
    mesh to its declared size, so the box must be exact)."""
    H = p.H
    for x, y in ((H - 0.15, 0), (-H + 0.15, 0), (0, H - 0.15), (0, -H + 0.15)):
        box(p, "Cloudstone", x, y, KEEL_BOTTOM + 0.15, 0.3, 0.3, 0.3)


def rift_rim(p, cx, cy, r):
    """Billows heaped round a rift's edge, so the cut reads as torn cloud rather than a box."""
    rng = p.rng
    # two staggered rings: the inner one lips over the cut edge (hiding the floor grid's square
    # steps), the outer one heaps behind it
    for ring_r, step, size in ((r + 1, 8.0, (8, 11)), (r + 11, 11.0, (7, 10))):
        n = max(8, int(2 * math.pi * ring_r / step))
        for i in range(n):
            a = 2 * math.pi * (i + (0.5 if size[0] == 7 else 0)) / n + rng.uniform(-0.08, 0.08)
            x, y = cx + math.cos(a) * ring_r, cy + math.sin(a) * ring_r
            if abs(x) > p.H - 14 or abs(y) > p.H - 14 or near_corridor(p, x, y, 8):
                continue
            puff(p, x, y, FLOOR_Z - 3, rng.uniform(*size), rng.uniform(4, 7), rng)


def near_corridor(p, x, y, pad=4.0):
    """Is (x, y) within `pad` of any path, bridge or ramp corridor?"""
    for ax, ay, bx, by, hw in p.corridors:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-6 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        if math.hypot(x - (ax + t * dx), y - (ay + t * dy)) < hw + pad:
            return True
    return False


def cloud_floor(p, holes=()):
    """The walk plane: a continuous cloud-top slab over the whole tile, billowing underneath.
    `holes` are (cx, cy, r) regions left open (a real drop: the broken-bridge cap)."""
    H = p.H
    p.holes.extend(holes)
    n = 12 if holes else 8                    # finer only where a hole needs a rounder rim (billows hide the rest)
    # A square slab built as a grid of quads so billows underneath can vary; top is flat (walkable).
    step = 2 * H / n
    verts, top_faces, side_faces, bot_faces = [], [], [], []
    idx = {}

    def open_at(x, y):
        return any(math.hypot(x - hx, y - hy) < hr for hx, hy, hr in holes)

    for i in range(n + 1):
        for j in range(n + 1):
            x, y = -H + i * step, -H + j * step
            idx[(i, j, 0)] = len(verts); verts.append((x, y, FLOOR_Z))
            # underside billows: deeper toward the middle, lumpy
            d = 10 + 8 * math.sin(i * 1.7 + j * 0.9) ** 2 + (6 if 0 < i < n and 0 < j < n else 0)
            idx[(i, j, 1)] = len(verts); verts.append((x, y, FLOOR_Z - d))
    for i in range(n):
        for j in range(n):
            cx, cy = -H + (i + 0.5) * step, -H + (j + 0.5) * step
            if open_at(cx, cy):
                continue
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            top_faces.append([idx[a + (0,)], idx[b + (0,)], idx[c + (0,)], idx[d + (0,)]])
            bot_faces.append([idx[d + (1,)], idx[c + (1,)], idx[b + (1,)], idx[a + (1,)]])
            # side walls on the tile boundary and around holes
            for (u, v), open_side in (((a, b), j == 0 or open_at(cx, cy - step)), ((b, c), i == n - 1 or open_at(cx + step, cy)),
                                      ((c, d), j == n - 1 or open_at(cx, cy + step)), ((d, a), i == 0 or open_at(cx - step, cy))):
                if open_side:
                    side_faces.append([idx[u + (0,)], idx[u + (1,)], idx[v + (1,)], idx[v + (0,)]])
    base_f = len(p.faces)
    p.add(verts, top_faces, "CloudWhite")
    for k in range(len(top_faces)):
        p.up.add(base_f + k)
    p.add(verts, side_faces, "CloudWhite")
    p.add(verts, bot_faces, "CloudWhite")


def puff(p, x, y, z, r, h, rng, mat="CloudWhite"):
    """One billow of cloud. Never taller than 0.9 of its radius: tall and narrow reads as a spike."""
    # never stretched wider than r: the bank's back row is sized to stay 1 stud inside the tile
    blob(p, mat, x, y, z, r, min(h, r * 0.9), n=6, a0=rng.uniform(0, 6.28), sx=rng.uniform(0.85, 1.0))


def cloud_bank(p, a, b, outward, depth=24, height=(10, 16), rng=None, density=1.0):
    """A billowing wall of cloud from a to b: low puffs on the clearing side, tall puffs behind
    them (toward `outward`, the tile edge). Every puff stays inside the tile."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 4:
        return
    t = d.normalized()
    out = Vector(outward).normalized()
    count = max(2, int(L / 19 * density))
    for k in range(count):
        c = a + d * ((k + 0.5) / count)
        # a low billow in front, a tall heaped one behind, and a small one riding on it
        for row, (off, hs, rr) in enumerate(((0.0, 0.45, 11.0), (1.0, 1.0, 12.5))):
            r = rng.uniform(rr * 0.85, rr * 1.12)        # back row max 14.0 at H-16: >= 1 stud inside
            h = rng.uniform(*height) * hs
            q = c + out * (off * depth * 0.5) + t * rng.uniform(-3, 3)
            puff(p, q.x, q.y, FLOOR_Z - 2, r, h, rng)
            if row == 1 and rng.random() < 0.35:
                puff(p, q.x + t.x * rng.uniform(-4, 4), q.y + t.y * rng.uniform(-4, 4), FLOOR_Z - 2 + min(h, r * 0.9) * 0.55,
                     r * 0.6, r * 0.5, rng)
        # a low filler billow in each gap, so the bank reads as one heaped mass, not a row of boulders
        if k < count - 1:
            g = a + d * ((k + 1.0) / count) + out * (depth * 0.25)
            puff(p, g.x, g.y, FLOOR_Z - 2.5, rng.uniform(9, 11), rng.uniform(5, 7), rng)


def mouth_gap(p, cardinal, extra=17):
    """(lo, hi) along the edge that must stay clear of banks for this socket's opening."""
    w = KIND_WIDTH[dict(p.sockets)[cardinal]]
    return (-w / 2 - extra, w / 2 + extra)


def perimeter_banks(p, skip=(), density=1.0):
    """Cloud banks along every tile edge that is not a mouth -- the clearing's walls. The back
    row's outer puff edge stays >= 1 stud inside the tile (nothing crosses the boundary), the
    ends stop short of the corners, and each mouth is left open."""
    H = p.H
    inset = 28.0                       # front-row line; back row sits 12 further out
    reach = H - inset - 6              # along-edge extent, clear of the perpendicular edges
    sock = dict(p.sockets)
    for side in ("N", "S", "E", "W"):
        if side in skip:
            continue
        dx, dy = DIRS[side]
        e = H - inset
        segs = [(-reach, reach)]
        if side in sock:
            lo, hi = mouth_gap(p, side)
            segs = [(-reach, lo), (hi, reach)]
        for s0, s1 in segs:
            if s1 - s0 < 6:
                continue
            a, b = ((s0, dy * e), (s1, dy * e)) if dx == 0 else ((dx * e, s0), (dx * e, s1))
            cloud_bank(p, a, b, (dx, dy), rng=p.rng, density=density)
    # corners: a heap each, so the banks read as one continuous wall
    for sx in (-1, 1):
        for sy in (-1, 1):
            puff(p, sx * (H - 22), sy * (H - 22), FLOOR_Z - 2, 14, p.rng.uniform(10, 13), p.rng)
            puff(p, sx * (H - 24), sy * (H - 24), FLOOR_Z + 6, 8, 7, p.rng)


def mesa(p, cx, cy, r, top=8.0, floor="AetherMintGrass", sides=13, jitter=0.12, sx=1.0, sy=1.0, collar=True):
    """A meadow island risen out of the cloud: meadow cap, the original's GOLD RIM band, faceted
    rock flanks sinking into the cloud floor, a collar of cloud puffs round its foot.
    Returns the rim outline (for ramps and edge dressing)."""
    rng = p.rng
    outline = []
    for i in range(sides):
        a = 2 * math.pi * (i + rng.uniform(-0.25, 0.25)) / sides
        rr = r * (1 + rng.uniform(-jitter, jitter))
        outline.append((cx + rr * sx * math.cos(a), cy + rr * sy * math.sin(a)))
    prism(p, outline, top - 2.5, top, floor, side=floor)
    rim = [(cx + (x - cx) * 1.035 + 0.8 * math.copysign(1, x - cx), cy + (y - cy) * 1.035 + 0.8 * math.copysign(1, y - cy))
           for x, y in outline]
    prism(p, rim, top - 5.5, top - 1.4, "TempleGold")
    # faceted flanks: widen as they go down into the cloud (a butte, not a keel)
    foot = [(cx + (x - cx) * 1.12, cy + (y - cy) * 1.12) for x, y in outline]
    n = len(outline)
    verts = [(x, y, top - 5.5) for x, y in outline] + [(x, y, FLOOR_Z - 3) for x, y in foot]
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    p.add(verts, [f[::-1] for f in faces], "Cloudstone")
    # strata stripe of pale soil across the flank
    sv = [(cx + (x - cx) * 1.06, cy + (y - cy) * 1.06, top - 5.5 - (top - 2.5) * 0.45) for x, y in outline]
    if top > 7:
        verts2 = [(x, y, top - 5.6) for x, y in outline] + sv
        p.add(verts2, [[n + (i + 1) % n, (i + 1) % n, i, n + i] for i in range(n)][::2], "PaleGoldSoil")
    if collar:
        for i in range(0, n, 2):
            x, y = foot[i]
            puff(p, x + rng.uniform(-3, 3), y + rng.uniform(-3, 3), FLOOR_Z - 1.5, rng.uniform(6, 10), rng.uniform(4, 8), rng)
    p.islands.append((cx, cy, r * max(sx, sy) * 1.2, FLOOR_Z, top))
    return outline


def ramp(p, a, b, width, z0, z1, mat="GoldenPath", side="Cloudstone"):
    """A walkable sloped path from ground level to a mesa top (slope kept under ~30 degrees)."""
    a, b = Vector((a[0], a[1])), Vector((b[0], b[1]))
    d = b - a
    L = d.length
    t = d.normalized()
    nrm = Vector((-t.y, t.x)) * (width / 2)
    pa0, pa1, pb0, pb1 = a - nrm, a + nrm, b - nrm, b + nrm
    verts = [(pa0.x, pa0.y, z0), (pa1.x, pa1.y, z0), (pb1.x, pb1.y, z1), (pb0.x, pb0.y, z1),
             (pa0.x, pa0.y, min(z0, z1) - 2), (pa1.x, pa1.y, min(z0, z1) - 2), (pb1.x, pb1.y, min(z0, z1) - 2),
             (pb0.x, pb0.y, min(z0, z1) - 2)]
    base_f = len(p.faces)
    p.add(verts, [[0, 3, 2, 1]], mat)
    p.up.add(base_f)
    p.add(verts, [[0, 4, 7, 3], [2, 6, 5, 1], [3, 7, 6, 2], [1, 5, 4, 0], [4, 5, 6, 7]], side)
    # step lines across the ramp so it reads as a stair
    steps = max(2, int(L / 3))
    for k in range(1, steps):
        u = k / steps
        c = a + d * u
        z = z0 + (z1 - z0) * u + 0.04
        decal_strip(p, "TempleGold" if k % 2 else mat, tuple(c - nrm * 0.98), tuple(c + nrm * 0.98), 0.5, z)
    p.corridors.append((a.x, a.y, b.x, b.y, width / 2 + 2))


# ---------------------------------------------------------------------------
# Paths and mouths
# ---------------------------------------------------------------------------
def path(p, pts, width=10, z=FLOOR_Z, mat="GoldenPath", edge="TempleGold"):
    """A golden flagstone path laid on the cloud (decals: flush, walkable), with flagstone seams."""
    for a, b in zip(pts, pts[1:]):
        decal_strip(p, mat, a, b, width, z + 0.03)
        decal_strip(p, edge, a, b, width + 1.2, z + 0.015)
        flagstones(p, a, b, width, z + 0.045)
        p.corridors.append((a[0], a[1], b[0], b[1], width / 2 + 2))
    for q in pts[1:-1]:                         # round the joints so bends read as one road
        decal(p, mat, ring_pts(q[0], q[1], width / 2, 10), z + 0.035)


def flagstones(p, a, b, width, z, course=5.0):
    """Seams across a road every `course` studs, staggered joints along it: laid stone, not paint."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    if L < course:
        return
    tx, ty = (bx - ax) / L, (by - ay) / L
    nx, ny = -ty, tx
    n = int(L / course)
    for k in range(1, n):
        cx, cy = ax + tx * k * course, ay + ty * k * course
        decal_strip(p, "PaleGoldSoil", (cx + nx * width * 0.48, cy + ny * width * 0.48), (cx - nx * width * 0.48, cy - ny * width * 0.48),
                    0.35, z)
        off = (width * 0.25) * (1 if k % 2 else -1)
        jx, jy = cx + nx * off, cy + ny * off
        decal_strip(p, "PaleGoldSoil", (jx, jy), (jx + tx * course, jy + ty * course), 0.3, z)


def meadow_carpet(p, cx, cy, r, z=FLOOR_Z, mat="AetherMintGrass", sides=14):
    """An organic patch of meadow lying on the cloud -- a grove stands on grass, not on bare cloud."""
    rng = p.rng
    pts = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        rr = r * rng.uniform(0.82, 1.08)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    decal(p, mat, pts, z + 0.015)
    # a scattered soil fringe round its edge
    for i in range(0, sides, 3):
        a = 2 * math.pi * (i + 0.5) / sides
        q = (cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a))
        decal(p, "PaleGoldSoil", ring_pts(q[0], q[1], r * 0.12, 7), z + 0.02)


def cloud_tufts(p, n, region, z=FLOOR_Z):
    """Low billows lying on the cloud floor: its texture, so open ground reads as cloud."""
    rng = p.rng
    cx, cy, r = region
    for _ in range(n * 6):
        if n <= 0:
            break
        a, rr = rng.uniform(0, 6.28), r * math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        s = rng.uniform(4, 8)
        if abs(x) > p.H - 44 or abs(y) > p.H - 44:
            continue
        if any(math.hypot(x - kx, y - ky) < kr + s for kx, ky, kr in p.keepout) or near_corridor(p, x, y, s + 2):
            continue
        if any(math.hypot(x - hx, y - hy) < hr + s + 12 for hx, hy, hr in p.holes):
            continue
        blob(p, "CloudWhite", x, y, z - 0.6, s, s * 0.3, n=5, a0=rng.uniform(0, 6))
        p.keepout.append((x, y, s))
        n -= 1


def mouth(p, cardinal, style="flag", inner=None):
    """Every opening arrives the same way: a landing of golden flagstone exactly the kind's width,
    level at z = 0 and running to the tile edge, flanked by a pair of guide stones. `style`
    dresses the approach; the landing itself never varies, so any two pieces meet cleanly."""
    kind = dict(p.sockets)[cardinal]
    w = KIND_WIDTH[kind]
    H = p.H
    dx, dy = DIRS[cardinal]
    inner = inner if inner is not None else H * 0.45
    ax, ay = dx * inner, dy * inner
    ex, ey = dx * H, dy * H
    nx, ny = -dy, dx
    # the landing: last 14 studs to the edge, exact width
    l0x, l0y = dx * (H - 14), dy * (H - 14)
    decal(p, "GoldenPath", [(l0x + nx * w / 2, l0y + ny * w / 2), (ex + nx * w / 2, ey + ny * w / 2),
                            (ex - nx * w / 2, ey - ny * w / 2), (l0x - nx * w / 2, l0y - ny * w / 2)], FLOOR_Z + 0.03)
    flagstones(p, (l0x, l0y), (ex - dx * 0.5, ey - dy * 0.5), w, FLOOR_Z + 0.045, course=7.0)
    for s in (-1, 1):
        decal_strip(p, "TempleGold", (l0x + nx * s * (w / 2 - 0.6), l0y + ny * s * (w / 2 - 0.6)),
                    (ex + nx * s * (w / 2 - 0.6), ey + ny * s * (w / 2 - 0.6)), 1.2, FLOOR_Z + 0.05)
    # guide stones either side of the landing (squat, rounded: not pylons)
    for s in (-1, 1):
        gx, gy = l0x + nx * s * (w / 2 + 5), l0y + ny * s * (w / 2 + 5)
        guide_stone(p, gx, gy, FLOOR_Z)
    # the approach from the landing inward
    pw = w * (0.6 if kind == "SPAN" else 0.75)
    path(p, [(ax, ay), (l0x, l0y)], width=pw)
    p.corridors.append((ax, ay, ex, ey, w / 2 + 4))


def guide_stone(p, x, y, z):
    p.keepout.append((x, y, 4.0))
    frustum(p, "TempleIvory", x, y, z - 0.5, z + 5.5, 2.4, 1.8, n=6, top_mat="TempleIvory")
    frustum(p, "TempleGold", x, y, z + 5.5, z + 6.8, 1.8, 0.2, n=6)
    box(p, "PortalGlow", x, y, z + 3.2, 0.5, 3.7, 1.2, rz=0.0)


# ---------------------------------------------------------------------------
# Flora
# ---------------------------------------------------------------------------
def tree(p, x, y, z=FLOOR_Z, h=20, crown="DeepTealLeaves", style=0):
    rng = p.rng
    lean = rng.uniform(-0.08, 0.08)
    tx, ty = x + lean * h, y + lean * h * 0.5
    p.keepout.append((x, y, max(3.0, h * 0.28)))
    trunk_top = h * (0.66 if style == 2 else 0.48)      # the umbrella's crown sits higher: its trunk reaches it
    frustum(p, "SoftWood", x, y, z - 0.5, z + trunk_top, h * 0.07, h * 0.045, n=6, a0=rng.uniform(0, 1))
    if style == 0:        # the original's gem crown
        gem2(p, crown, tx, ty, z + h * 0.55, h * 0.34, h * 0.45, h * 0.18, n=7, a0=rng.uniform(0, 6))
    elif style == 1:      # stacked twin crowns
        gem2(p, crown, tx, ty, z + h * 0.48, h * 0.34, h * 0.3, h * 0.14, n=7, a0=rng.uniform(0, 6))
        gem2(p, crown, tx, ty, z + h * 0.72, h * 0.24, h * 0.28, h * 0.1, n=6, a0=rng.uniform(0, 6))
    else:                 # umbrella crown
        gem(p, crown, tx, ty, z + h * 0.72, h * 0.45, h * 0.16, h * 0.12, n=8, a0=rng.uniform(0, 6))


def great_tree(p, x, y, z=FLOOR_Z, top=CROWN_TOP, trunk=7.0):
    """The ancient sky tree: flared roots, a leaning trunk, three limbs, layered crowns. Its
    highest crown's apex is EXACTLY `top` (it pins the box)."""
    p.keepout.append((x, y, trunk * 2.8))
    rng = p.rng
    for i in range(6):                       # root flares
        a = i * 1.047 + rng.uniform(-0.2, 0.2)
        rod(p, "SoftWood", (x + math.cos(a) * trunk * 0.4, y + math.sin(a) * trunk * 0.4, z + 6),
            (x + math.cos(a) * trunk * 2.3, y + math.sin(a) * trunk * 2.3, z - 1.5), trunk * 0.45, trunk * 0.15, n=5)
    frustum(p, "SoftWood", x, y, z - 1, z + 96, trunk, trunk * 0.55, n=8)
    ch = top - 24                             # the top crown's centre: apex = ch + 24 = top
    crowns = [(x, y, ch, 30, 24, "DeepTealLeaves")]
    # a heavy canopy: five limbs at staggered heights, each carrying a big crown; the crowns overlap
    # into one mass (the first pass read as a lollipop)
    lim = p.H - 3
    for i, a in enumerate((0.3, 1.55, 2.8, 4.05, 5.3)):
        L = rng.uniform(26, 36)
        sz = z + 62 + (i % 3) * 12
        ex, ey = x + math.cos(a) * L, y + math.sin(a) * L
        # a limb never carries its crown past the tile edge (nothing crosses the boundary)
        r_max = 25
        ex, ey = max(-lim + r_max, min(lim - r_max, ex)), max(-lim + r_max, min(lim - r_max, ey))
        rod(p, "SoftWood", (x, y, sz), (ex, ey, sz + 20), trunk * 0.45, trunk * 0.2, n=5)
        crowns.append((ex, ey, sz + 27, rng.uniform(19, 25), rng.uniform(15, 20), "IndigoLeaves" if i % 2 else "DeepTealLeaves"))
    for cx, cy, cz, r, up, mat in crowns:
        gem2(p, mat, cx, cy, cz, r, up, r * 0.5, n=8, a0=rng.uniform(0, 6))
    rod(p, "SoftWood", (x, y, z + 92), (x, y, ch - 10), trunk * 0.55, trunk * 0.35, n=6)


def mushroom(p, x, y, z=FLOOR_Z, s=1.0):
    frustum(p, "TempleIvory", x, y, z - 0.2, z + 2.2 * s, 0.45 * s, 0.35 * s, n=5)
    gem(p, "TempleGold", x, y, z + 2.2 * s, 1.5 * s, 1.1 * s, 0.35 * s, n=6)


def blossoms(p, cx, cy, r, n, z=FLOOR_Z, avoid=()):
    """Glowing aether blossoms scattered in a disc: tiny faceted buds on the grass."""
    rng = p.rng
    mats = ("TempleGold", "SkyCrystal", "PortalGlow", "CloudWhite", "TempleGold")
    for _ in range(n):
        a, rr = rng.uniform(0, 6.28), r * math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in list(avoid) + p.keepout):
            continue
        gem(p, mats[rng.randrange(len(mats))], x, y, z + 0.55, 0.5, 0.45, 0.55, n=4, a0=rng.uniform(0, 1))


def grass_tufts(p, cx, cy, r, n, z=FLOOR_Z, avoid=()):
    rng = p.rng
    for _ in range(n):
        a, rr = rng.uniform(0, 6.28), r * math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in list(avoid) + p.keepout):
            continue
        for k in range(3):
            # a thin three-sided blade (a sliver tetrahedron): solid from every side, no duplicate faces
            b = rng.uniform(0, 6.28)
            h = rng.uniform(1.2, 2.2)
            c, s = math.cos(b), math.sin(b)
            p.add([(x + c * 0.35, y + s * 0.35, z - 0.1), (x - c * 0.35, y - s * 0.35, z - 0.1),
                   (x - s * 0.12, y + c * 0.12, z - 0.1), (x + math.cos(b + 1.4) * 0.5, y + math.sin(b + 1.4) * 0.5, z + h)],
                  [[0, 1, 3], [1, 2, 3], [2, 0, 3]], "AetherMintGrass")


def rock(p, x, y, z=FLOOR_Z, s=3.0):
    gem(p, "Cloudstone", x, y, z + s * 0.2, s, s * 0.8, s * 0.6, n=5, a0=p.rng.uniform(0, 6))


# ---------------------------------------------------------------------------
# Architecture (the temple vocabulary: columns, pavilions, arches, towers)
# ---------------------------------------------------------------------------
def column(p, x, y, z, h, r=2.6, broken=False, drum_fall=False):
    p.keepout.append((x, y, r * 2.2 + (r * 4.5 if drum_fall else 0)))
    rng = p.rng
    box(p, "TempleGold", x, y, z + 0.6, r * 2.6, r * 2.6, 1.2)
    box(p, "TempleIvory", x, y, z + 1.6, r * 2.3, r * 2.3, 0.8)
    if broken:
        hb = h * rng.uniform(0.3, 0.7)
        frustum(p, "TempleIvory", x, y, z + 2, z + hb, r, r * 0.95, n=10)
        gem(p, "TempleIvory", x, y, z + hb, r * 0.95, rng.uniform(0.6, 1.6), 0.01, n=10)
        if drum_fall:
            # a fallen drum on the floor: its flattest side (the 10-gon's apothem, 0.95 r) sunk in
            a = rng.uniform(0, 6.28)
            fx, fy = x + math.cos(a) * r * 3.5, y + math.sin(a) * r * 3.5
            rod(p, "TempleIvory", (fx - math.cos(a + 1.3) * 3, fy - math.sin(a + 1.3) * 3, z + r * 0.9),
                (fx + math.cos(a + 1.3) * 3, fy + math.sin(a + 1.3) * 3, z + r * 0.9), r, r, n=10)
        return z + hb
    frustum(p, "TempleIvory", x, y, z + 2, z + h - 2.2, r, r * 0.9, n=10)
    frustum(p, "TempleGold", x, y, z + h - 2.2, z + h - 1.0, r * 0.9, r * 1.35, n=10)
    box(p, "TempleGold", x, y, z + h - 0.5, r * 2.8, r * 2.8, 1.0)
    return z + h


def pavilion(p, x, y, z, w, d, h, rz=0.0, roof="hip", altar=True):
    """The original island's shrine: four ivory columns, a stepped plinth, a roof, an altar
    holding a golden orb."""
    p.keepout.append((x, y, max(w, d) * 0.72 + 4))          # the roof's corners, not just its sides
    c, s = math.cos(rz), math.sin(rz)

    def at(u, v):
        return x + u * c - v * s, y + u * s + v * c

    pts = [at(-w / 2 - 2, -d / 2 - 2), at(w / 2 + 2, -d / 2 - 2), at(w / 2 + 2, d / 2 + 2), at(-w / 2 - 2, d / 2 + 2)]
    prism(p, pts, z - 0.5, z + 0.9, "TempleIvory", side="TempleGold")
    for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        cx, cy = at(u, v)
        column(p, cx, cy, z + 0.9, h, r=1.4)
    top = z + 0.9 + h
    roofp = [at(-w / 2 - 3, -d / 2 - 3), at(w / 2 + 3, -d / 2 - 3), at(w / 2 + 3, d / 2 + 3), at(-w / 2 - 3, d / 2 + 3)]
    prism(p, roofp, top, top + 1.4, "SoftWood", side="TempleGold")
    if roof == "hip":
        n = 4
        verts = [(q[0], q[1], top + 1.4) for q in roofp] + [(x, y, top + 1.4 + max(w, d) * 0.45)]
        p.add(verts, [[i, (i + 1) % n, n] for i in range(n)], "TempleGold")
        box(p, "SkyCrystal", x, y, top + 1.4 + max(w, d) * 0.45 + 1.0, 1.2, 1.2, 2.0, rz=rz + 0.785)
    if altar:
        cx, cy = at(0, 0)
        box(p, "TempleIvory", cx, cy, z + 2.4, 3.2, 2.2, 3.0, rz=rz)
        gem(p, "TempleGold", cx, cy, z + 4.8, 1.2, 1.1, 0.9, n=8)
    return top


def arch(p, x, y, z, span, h, rz=0.0, thick=5.0, ruined=False, top=None):
    """A stone arch: two piers, a semicircle of voussoirs, a gold keystone. `top` forces the
    keystone's crown to an exact height (the colossal arch pins the box)."""
    c, s = math.cos(rz), math.sin(rz)
    rng = p.rng
    pier_w = max(4.0, span * 0.14)
    ar = span / 2 + pier_w / 2
    for side in (-1, 1):
        p.keepout.append((x + c * side * ar, y + s * side * ar, pier_w + 4))
    spring = (top - thick * 1.2 - ar) if top is not None else z + h - ar
    for side in (-1, 1):
        px, py = x + c * side * (span / 2 + pier_w / 2), y + s * side * (span / 2 + pier_w / 2)
        ph = spring - z
        if ruined and side == 1:
            ph *= rng.uniform(0.45, 0.7)
        box(p, "TempleIvory", px, py, z + ph / 2, pier_w, thick, ph, rz=rz)
        for k in range(1, int(ph // 18) + 1):
            box(p, "TempleGold", px, py, z + k * 18, pier_w + 0.8, thick + 0.8, 1.0, rz=rz)
    segs = 11
    for k in range(segs):
        if ruined and k < 4:
            continue
        a0, a1 = math.pi * k / segs, math.pi * (k + 1) / segs
        am = (a0 + a1) / 2
        u, zz = -math.cos(am) * ar, spring + math.sin(am) * ar
        seg_len = ar * (a1 - a0) * 1.08
        mat = "TempleGold" if k == segs // 2 else "TempleIvory"
        cx, cy = x + c * u, y + s * u
        # a voussoir: a block tangent to the curve
        from mathutils import Matrix
        # local x runs along the curve (tangent), local z is the voussoir's radial depth
        M = Matrix.Translation((cx, cy, zz)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(am - math.pi / 2, 4, "Y")
        box(p, mat, 0, 0, 0, seg_len, thick, pier_w * 0.9, M=M)
    if top is not None and not ruined:
        # the keystone's finial meets the crown exactly
        frustum(p, "TempleGold", x, y, top - thick * 1.2 - 0.5, top, 1.6, 0.05, n=6)


def waystone(p, x, y, z=FLOOR_Z, rz=0.0, h=18.0):
    p.keepout.append((x, y, 7.0))
    """The original's waystone: a squat tapering rune stone (7.8 x 7.8 x 18) with a glowing band
    and a gold cap -- chunky, never a spire."""
    frustum(p, "Cloudstone", x, y, z - 0.5, z + 1.5, 5.2, 4.8, n=4, a0=rz + 0.785)
    frustum(p, "TempleIvory", x, y, z + 1.5, z + h - 3, 3.9, 3.0, n=4, a0=rz + 0.785)
    frustum(p, "PortalGlow", x, y, z + h * 0.45, z + h * 0.55, 4.0, 3.8, n=4, a0=rz + 0.785)
    frustum(p, "TempleGold", x, y, z + h - 3, z + h, 3.3, 0.3, n=4, a0=rz + 0.785)


def lantern_post(p, x, y, z=FLOOR_Z, h=9.0, rz=0.0):
    p.keepout.append((x, y, 3.5))
    frustum(p, "SoftWood", x, y, z - 0.3, z + h, 0.45, 0.35, n=5)
    ax, ay = x + math.cos(rz) * 2.2, y + math.sin(rz) * 2.2
    beam(p, "SoftWood", (x, y, z + h - 0.4), (ax, ay, z + h - 0.4), 0.5, 0.5)
    rod(p, "TempleGold", (ax, ay, z + h - 0.6), (ax, ay, z + h - 2.0), 0.08, 0.08, n=4)
    frustum(p, "TempleGold", ax, ay, z + h - 3.6, z + h - 2.0, 0.9, 0.6, n=6)
    gem(p, "PortalGlow", ax, ay, z + h - 2.9, 0.7, 0.6, 0.6, n=6)


def bell_tower(p, x, y, z=FLOOR_Z, top=CROWN_TOP, w=16.0, rz=0.0):
    """A square ivory bell tower: gold bands, an open belfry with a hanging bell, a gold hip roof,
    a sky crystal whose tip is EXACTLY `top`."""
    p.keepout.append((x, y, w * 0.72 + 5))
    body_top = z + (top - z) * 0.64
    box(p, "Cloudstone", x, y, z + 1, w + 4, w + 4, 3, rz=rz)
    box(p, "TempleIvory", x, y, (z + body_top) / 2, w, w, body_top - z, rz=rz)
    for k in range(1, int((body_top - z) // 22) + 1):
        box(p, "TempleGold", x, y, z + k * 22, w + 1, w + 1, 1.2, rz=rz)
    # crystal windows
    c, s = math.cos(rz), math.sin(rz)
    for side in range(4):
        a = rz + side * math.pi / 2
        ox, oy = math.cos(a) * (w / 2 + 0.05), math.sin(a) * (w / 2 + 0.05)
        box(p, "SkyCrystal", x + ox, y + oy, body_top - 12, 0.4 if side % 2 == 0 else w * 0.3,
            w * 0.3 if side % 2 == 0 else 0.4, 8, rz=rz)
    bel_top = body_top + (top - z) * 0.14
    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px, py = x + (u * c - v * s) * (w / 2 - 1.5), y + (u * s + v * c) * (w / 2 - 1.5)
        box(p, "TempleIvory", px, py, (body_top + bel_top) / 2, 3, 3, bel_top - body_top, rz=rz)
    box(p, "TempleIvory", x, y, bel_top + 0.8, w + 2, w + 2, 1.6, rz=rz)
    bell_z = body_top + (bel_top - body_top) * 0.35
    gem(p, "TempleGold", x, y, bell_z, w * 0.22, (bel_top - body_top) * 0.4, 0.8, n=8)
    rod(p, "TempleGold", (x, y, bell_z + (bel_top - body_top) * 0.38), (x, y, bel_top + 0.1), 0.3, 0.3, n=4)  # hangs from the roof
    roof_top = top - (top - z) * 0.07
    # the roof's eaves sit INSIDE the belfry slab (half-width w/2 + 1, bel_top .. bel_top + 1.6) so the
    # roof is seated in it; eaves outside the slab left the whole roof floating a stud clear
    verts = [(x + (u * c - v * s) * (w / 2 + 0.5), y + (u * s + v * c) * (w / 2 + 0.5), bel_top + 1.0)
             for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))] + [(x, y, roof_top)]
    p.add(verts, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], "TempleGold")
    frustum(p, "SkyCrystal", x, y, roof_top - 1.5, top, 1.4, 0.0, n=5)


def crystal_cluster(p, x, y, z=FLOOR_Z, s=1.0, n=5, tall=None):
    p.keepout.append((x, y, 6.0 * s))
    rng = p.rng
    gem(p, "Cloudstone", x, y, z, 3.2 * s, 1.6 * s, 1.0 * s, n=6)
    for k in range(n):
        a = rng.uniform(0, 6.28)
        tilt = rng.uniform(0.1, 0.45) if k else 0.05
        L = (tall if (tall and k == 0) else rng.uniform(6, 14) * s)
        bx, by = x + math.cos(a) * 1.4 * s * (k > 0), y + math.sin(a) * 1.4 * s * (k > 0)
        ex = bx + math.cos(a) * math.sin(tilt) * L
        ey = by + math.sin(a) * math.sin(tilt) * L
        rod(p, "SkyCrystal", (bx, by, z - 0.5), (ex, ey, z + math.cos(tilt) * L), rng.uniform(1.2, 2.0) * s, 0.0, n=5)


def crystal_colossus(p, x, y, z=FLOOR_Z, top=CROWN_TOP, spread=22.0):
    """A mountain of sky crystal: a rock mound and seven great shards; the central one's tip is
    EXACTLY `top`. `spread` is how far the small clusters sit from its foot (smaller on a mesa)."""
    p.keepout.append((x, y, spread + 12))
    rng = p.rng
    gem(p, "Cloudstone", x, y, z, min(20, spread + 4), 10, 2, n=7)
    rod(p, "SkyCrystal", (x, y, z), (x, y, top), 9.0, 0.0, n=6)
    for k in range(6):
        a = k * 1.047 + rng.uniform(-0.3, 0.3)
        L = rng.uniform(40, 75) * min(1.0, (top - z) / 150)
        tilt = rng.uniform(0.25, 0.5)
        bx, by = x + math.cos(a) * 8, y + math.sin(a) * 8
        rod(p, "SkyCrystal", (bx, by, z - 1), (bx + math.cos(a) * math.sin(tilt) * L, by + math.sin(a) * math.sin(tilt) * L,
                                                z + math.cos(tilt) * L), rng.uniform(4, 6.5), 0.0, n=5)
    for k in range(5):
        a = rng.uniform(0, 6.28)
        crystal_cluster(p, x + math.cos(a) * spread, y + math.sin(a) * spread, z, s=0.8, n=3)


def crag(p, x, y, z=FLOOR_Z, r=18.0, top=CROWN_TOP, ledges=True):
    """A pinnacle of faceted rock rising out of the cloud, grass on its ledges, a tiny shrine near
    its summit; its apex is EXACTLY `top`."""
    p.keepout.append((x, y, r + 6))
    rng = p.rng
    tiers = 7
    prev = None
    for k in range(tiers + 1):
        u = k / tiers
        zz = z - 2 + (top - z + 2) * u
        # a butte, not a needle: it stays broad most of the way, then breaks into a blunt summit
        rr = r * 1.35 * (1 - u) ** 0.45 + (0 if k == tiers else 1.5)
        pts = ring_pts(x + rng.uniform(-3, 3) * (1 - u), y + rng.uniform(-3, 3) * (1 - u), rr * rng.uniform(0.82, 1.12), 7, a0=k * 0.4)
        ring = [(q[0], q[1], zz) for q in pts]
        if prev is not None:
            if k == tiers:
                verts = prev + [(x, y, top)]
                p.add(verts, [[i, (i + 1) % 7, 7] for i in range(7)], "Cloudstone")
            else:
                verts = prev + ring
                p.add(verts, [[i, (i + 1) % 7, 7 + (i + 1) % 7, 7 + i] for i in range(7)],
                      "PaleGoldSoil" if k == 2 else "Cloudstone")
        prev = ring
        if ledges and 1 <= k <= 3:
            a = rng.uniform(0, 6.28)
            lx, ly = x + math.cos(a) * rr * 0.9, y + math.sin(a) * rr * 0.9
            gem(p, "AetherMintGrass", lx, ly, zz, rr * 0.45, 1.5, 3.0, n=6)
            if k == 2:
                tree(p, lx, ly, zz + 1, h=12, crown="IndigoLeaves")
    if z > -10:                                 # a cloud collar only where it stands on the cloud
        puff(p, x, y, z - 1, r * 1.3, 7, rng)


def aether_pool(p, cx, cy, r, z=FLOOR_Z):
    """A shallow basin of sky crystal water with an ivory lip and a glowing ring (walkable)."""
    p.keepout.append((cx, cy, r + 3))
    decal(p, "SkyCrystal", ring_pts(cx, cy, r, 20), z + 0.04)
    decal_ring(p, "PortalGlow", cx, cy, r * 0.55, r * 0.6, z + 0.06, n=20)
    decal_ring(p, "TempleIvory", cx, cy, r, r + 1.6, z + 0.05, n=20)


def fountain(p, x, y, z=FLOOR_Z):
    p.keepout.append((x, y, 11.0))
    pts = ring_pts(x, y, 9, 12)
    prism(p, pts, z - 0.5, z + 1.6, "TempleIvory", side="TempleIvory")
    decal(p, "SkyCrystal", ring_pts(x, y, 7.6, 12), z + 1.65)
    frustum(p, "TempleIvory", x, y, z + 1.6, z + 6, 1.4, 1.0, n=8)
    frustum(p, "TempleGold", x, y, z + 6, z + 7.5, 1.0, 3.2, n=8)
    gem(p, "PortalGlow", x, y, z + 8.6, 1.6, 1.5, 1.2, n=8)


def ruin_wall(p, a, b, z=FLOOR_Z, h=8.0, thick=2.4):
    """A broken ivory wall: courses of blocks, the top course ragged."""
    rng = p.rng
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    n = max(1, int(L / 5))
    for k in range(n):
        u0, u1 = k / n, (k + 1) / n
        hh = h * rng.uniform(0.35, 1.0)
        c = a + d * ((u0 + u1) / 2)
        beam(p, "TempleIvory" if k % 3 else "Cloudstone", (c.x - d.x / n / 2, c.y - d.y / n / 2, z + hh / 2),
             (c.x + d.x / n / 2, c.y + d.y / n / 2, z + hh / 2), thick, hh)
    beam(p, "TempleGold", (a.x, a.y, z + 0.4), (b.x, b.y, z + 0.4), thick + 0.6, 0.8)


def balustrade(p, pts, z, closed=True, spacing=4.0, gaps=()):
    """Ivory posts and a gold rail along a polyline, leaving `gaps` [(x, y, r)] open."""
    seq = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(seq, seq[1:]):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        n = max(1, int(L / spacing))
        prev = None
        for k in range(n + 1):
            q = a + (b - a) * (k / n)
            blocked = any(math.hypot(q.x - gx, q.y - gy) < gr for gx, gy, gr in gaps)
            if blocked:
                prev = None
                continue
            box(p, "TempleIvory", q.x, q.y, z + 1.6, 0.9, 0.9, 3.2)
            if prev is not None:
                beam(p, "TempleGold", (prev.x, prev.y, z + 3.4), (q.x, q.y, z + 3.4), 0.7, 0.5)
            prev = q


def hut(p, x, y, z=FLOOR_Z, rz=0.0):
    p.keepout.append((x, y, 11.0))
    """A hermit's hut: soft-wood walls with a doorway, an ivory hip roof, a crystal on top."""
    c, s = math.cos(rz), math.sin(rz)

    def at(u, v):
        return x + u * c - v * s, y + u * s + v * c

    w, d, h = 12, 10, 7
    for (u0, v0, u1, v1) in ((-w / 2, -d / 2, -2, -d / 2), (2, -d / 2, w / 2, -d / 2),
                             (w / 2, -d / 2, w / 2, d / 2), (w / 2, d / 2, -w / 2, d / 2), (-w / 2, d / 2, -w / 2, -d / 2)):
        a, b = at(u0, v0), at(u1, v1)
        beam(p, "SoftWood", (a[0], a[1], z + h / 2), (b[0], b[1], z + h / 2), 0.8, h)
    a, b = at(-2, -d / 2), at(2, -d / 2)
    beam(p, "SoftWood", (a[0], a[1], z + h - 1), (b[0], b[1], z + h - 1), 0.8, 2)
    verts = [(at(u, v)[0], at(u, v)[1], z + h) for u, v in ((-w / 2 - 1.5, -d / 2 - 1.5), (w / 2 + 1.5, -d / 2 - 1.5),
                                                              (w / 2 + 1.5, d / 2 + 1.5), (-w / 2 - 1.5, d / 2 + 1.5))]
    verts.append((x, y, z + h + 6))
    p.add(verts, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [3, 2, 1, 0]], "TempleIvory")
    rod(p, "SkyCrystal", (x, y, z + h + 5.5), (x, y, z + h + 8.5), 0.7, 0.0, n=4)


def stairs(p, x, y, z0, z1, width, rz, tread=2.0, mat="TempleIvory"):
    """Real steps (1-stud risers) from z0 up to z1, climbing along +u (rotated by rz)."""
    n = max(1, int(round((z1 - z0) / 1.0)))
    rise = (z1 - z0) / n
    c, s = math.cos(rz), math.sin(rz)
    for k in range(n):
        u = (k + 0.5) * tread
        cx, cy = x + u * c, y + u * s
        top = z0 + (k + 1) * rise
        box(p, mat if k % 2 == 0 else "TempleGold" if mat == "TempleIvory" else mat, cx, cy, (z0 - 1 + top) / 2,
            tread, width, top - z0 + 1, rz=rz, top=mat)
    p.corridors.append((x, y, x + n * tread * c, y + n * tread * s, width / 2 + 2))
    return x + n * tread * c, y + n * tread * s
