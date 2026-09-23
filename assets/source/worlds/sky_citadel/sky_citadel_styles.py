"""Scenario ARCHITECTURE STYLES -- each scenario builds the citadel in its own
language.

Owner, 2026-09-23: "a lot of the chunks are straight copy and paste designs
but recoloured ... Pieces can be similar, but identical defeats the entire
purpose." A scenario piece used to be its base piece rebuilt, recoloured, with
things added. Now, while a scenario's pieces are built, the base builders'
VOCABULARY is swapped for the scenario's own: what a tower is, what a spire is,
what stands at the crown, what runs round the rim, what is painted on the
floor. The base builder still decides WHERE things go -- so sockets, the
walking line, the 256^3 box and every registered footprint are the base
piece's -- but what stands there is the scenario's. A siege tower is a raider
keep, a lockdown tower a bunker, a rime tower a tower frozen inside ice.

Every part below registers exactly the solid the base part registered, so the
structure hooks, the scatter's spawn points and validate() treat it the same.
Every style draws its own randomness from the piece and the spot, so no two
towers of one scenario are identical either.

Executed by build_sky_citadel_scenarios.py into its namespace; applied by
`styled(scenario)` round each scenario's build.
"""

import math
import random
from contextlib import contextmanager

panel, tri_panel, inside = K["panel"], K["tri_panel"], K["inside"]
K["PROP_KINDS"]["hover segment"] = ("segment", "Float", 1)

STYLES = {}                     # scenario -> {kit name: replacement}
EDGE_STYLES = {}                # scenario -> {edge style: fn(p, a, b, inward)}


def style(scenario, name):
    """Register fn as `scenario`'s version of the kit's `name`. Its faces are
    tagged as the base part's (geometry_checks), because it IS that part."""
    def deco(fn):
        fn.__code__ = fn.__code__.replace(co_name=name)
        STYLES.setdefault(scenario, {})[name] = fn
        return fn
    return deco


def edge(scenario, *kinds):
    def deco(fn):
        fn.__code__ = fn.__code__.replace(co_name="edge_ring")
        for k in kinds:
            EDGE_STYLES.setdefault(scenario, {})[k] = fn
        return fn
    return deco


def part(fn):
    """A helper: never a tag of its own (its caller is the part)."""
    K["PRIMITIVES"].add(fn.__name__)
    return fn


@contextmanager
def styled(scenario):
    saved = {n: K[n] for n in STYLES.get(scenario, {})}
    saved_edges = dict(K["EDGES"])
    K.update(STYLES.get(scenario, {}))
    K["EDGES"].update(EDGE_STYLES.get(scenario, {}))
    try:
        yield
    finally:
        K.update(saved)
        K["EDGES"].clear()
        K["EDGES"].update(saved_edges)


def _rng(p, *key):
    return random.Random("%s|%s" % (p.name, "|".join(str(round(k, 1)) if isinstance(k, float) else str(k)
                                                     for k in key)))


def _roof_h(r, roof_h):
    return roof_h if roof_h is not None else r * 2.4


ORIG = {}                       # the kit's own parts, for styles that build on them


def _orig(name):
    return ORIG[name]


# ==========================================================================
# helpers shared by the styles
# ==========================================================================

@part
def _ring_of(p, mat, n, R, z, sx, sy, sz, x, y, phase=0.0, jitter=None, rng=None):
    for k in range(n):
        a = phase + 360.0 * k / n
        if jitter and rng:
            a += rng.uniform(-jitter, jitter)
        box(p, mat, x + math.cos(math.radians(a)) * R, y + math.sin(math.radians(a)) * R, z, sx, sy, sz, rz=a)


@part
def _jagged_top(p, mat, x, y, r, z, rng, n=10, hmax=4.5):
    for k in range(n):
        a = math.radians(360.0 * k / n + rng.uniform(-8, 8))
        h = rng.uniform(0.8, hmax)
        box(p, mat, x + math.cos(a) * r * 0.86, y + math.sin(a) * r * 0.86, z + h / 2 - 0.3, r * 0.6, 1.0, h,
            rz=math.degrees(a) + 90, rx=rng.uniform(-10, 10))


@part
def _lean_tube(p, mat, x0, y0, z0, x1, y1, z1, r0, r1, n=6):
    tube(p, mat, [(x0, y0, z0), (x1, y1, z1)], [r0, r1], n=n)


@part
def _ivy(p, x, y, r, z0, z1, rng, turns=1.5, mat="Verdure"):
    pts, rad = [], []
    k = max(5, int((z1 - z0) / 5))
    a0 = rng.uniform(0, 2 * math.pi)
    for j in range(k + 1):
        f = j / k
        a = a0 + f * turns * 2 * math.pi
        pts.append((x + math.cos(a) * (r + 0.15), y + math.sin(a) * (r + 0.15), z0 + (z1 - z0) * f))
        rad.append(0.35)
    tube(p, mat, pts, rad, n=4)


@part
def _crystal_burst(p, x, y, z, rng, tall, spread, n, mats=("AetherBloom", "Pearl", "SkyGlass")):
    for k in range(n):
        a = rng.uniform(0, 2 * math.pi)
        d = 0 if k == 0 else rng.uniform(0.3, 1.0) * spread
        tilt = 0 if k == 0 else rng.uniform(10, 28)
        h = tall * (1.0 if k == 0 else rng.uniform(0.35, 0.7))
        w = max(0.8, h * rng.uniform(0.12, 0.18))
        with frame(p, xf(x + math.cos(a) * d, y + math.sin(a) * d, z, math.degrees(a), 0, tilt)):
            crystal(p, mats[k % len(mats)], 0, 0, 0, w, h, 0.6, n=5)


@part
def _panel_ring(p, mats, cx, cy, r, n, w, l, z=0.07, phase=0.0):
    for k in range(n):
        a = phase + 360.0 * k / n
        panel(p, mats[k % len(mats)], cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r,
              l, w, z=z, rz=a)


@part
def _zigzag(p, mat, x0, y0, x1, y1, rng, w=0.7, n=5, amp=2.5, z=0.08):
    px, py = x0, y0
    for k in range(1, n + 1):
        f = k / n
        tx, ty = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        if k < n:
            nx, ny = -(y1 - y0), (x1 - x0)
            L = math.hypot(nx, ny) or 1.0
            o = rng.uniform(-amp, amp)
            tx, ty = tx + nx / L * o, ty + ny / L * o
        L = math.hypot(tx - px, ty - py)
        if L > 0.3:
            panel(p, mat, (px + tx) / 2, (py + ty) / 2, L + w * 0.5, w, z=z,
                  rz=math.degrees(math.atan2(ty - py, tx - px)))
        px, py = tx, ty


def _seg(a, b, inward, off=0.0):
    ix, iy = inward
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return x0 + ix * off, y0 + iy * off, x1 + ix * off, y1 + iy * off, L, ang


# ==========================================================================
# SIEGE -- the raiders' citadel: timber, scrap, rust and stolen stone
# ==========================================================================

@style("siege", "tower")
def siege_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "keep", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    cut = H * rng.uniform(0.45, 0.6)                   # the stone stump the raiders took
    frustum(p, "CitadelWhite", 8, r * 1.1, r * 0.98, 0, cut, x, y)
    _jagged_top(p, "CitadelWhite", x, y, r * 0.98, cut, rng, n=9, hmax=2.2)
    # the timber keep built on it: planked walls, a jutting hoard, a rust roof
    frustum(p, "Bark", 8, r * 0.94, r * 0.9, cut - 0.5, H, x, y)
    for z in range(int(cut) + 2, int(H), 3):
        frustum(p, "Twig", 8, r * 0.96, r * 0.96, z, z + 0.4, x, y)
    frustum(p, "Twig", 8, r * 1.05, r * 1.2, H - 0.2, H + 1.2, x, y)
    for k in range(8):                                 # hoard brackets
        a = math.radians(22.5 + 45 * k)
        with frame(p, xf(x + math.cos(a) * r * 0.95, y + math.sin(a) * r * 0.95, H - 1.6, math.degrees(a), 0, 40)):
            box(p, "Bark", 0, 0, 0, 0.5, 0.5, 2.6)
    frustum(p, "RaiderRust", 4, r * 1.25, 0.2, H + 1.2, H + 1.2 + rh * 0.75, x, y, rot=45)
    frustum(p, "DeepAlloy", 4, 0.25, 0.1, H + 1.2 + rh * 0.7, min(H + 6 + rh - 0.2, H + 3.2 + rh * 0.75), x, y)
    for k in range(rng.randint(2, 4)):                 # slit windows, lit
        a = math.radians(rng.uniform(0, 360))
        box(p, "EmberGlow", x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, rng.uniform(cut + 2, H - 2),
            0.3, 0.8, 1.8, rz=math.degrees(a))


@style("siege", "spire")
def siege_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    rng = _rng(p, "spire", x, y)
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "PaleAlloy", 8, r * 1.5, r * 1.3, z0, z0 + 4, x, y)
    frustum(p, "CitadelWhite", 8, r * 1.05, r * 0.55, z0 + 4, z0 + L * 0.75, x, y)
    frustum(p, "RaiderRust", 8, r * 0.58, r * 0.58, z0 + L * 0.75, z0 + L * 0.77, x, y)
    frustum(p, "DeepAlloy", 8, r * 0.52, 0.0, z0 + L * 0.77, H, x, y)
    # raider scaffolding climbing it: four poles, lashed decks, a crow's nest
    top = z0 + L * rng.uniform(0.35, 0.5)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        px, py = x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2
        frustum(p, "Bark", 4, 0.3, 0.25, z0, top, px, py)
    for z in (z0 + 8, top - 0.3):
        frustum(p, "Twig", 4, r * 1.75, r * 1.75, z, z + 0.35, x, y, rot=45)
    frustum(p, "Bark", 8, r * 0.95, r * 0.95, top + 3, top + 4.2, x, y)
    cloth_banner(p, x + r * 0.9, y, top + 3.5, rng)


@part
def cloth_banner(p, x, y, z, rng, w=3.0, h=5.0):
    box(p, "DeepAlloy", x + w / 2, y, z, w + 0.4, 0.2, 0.2)
    box(p, rng.choice(("RaiderRust", "Char")), x + w / 2, y, z - h / 2 - 0.1, w, 0.15, h)


def _crown_siege(p, x, y, top, R, label):
    """WAR TOTEM: a lashed timber mast, cross-trees hung with cages and
    trophies, a torn war banner, a spike at the very top."""
    rng = _rng(p, "totem", x, y)
    p.solid(label, x, y, R, 0, top)
    frustum(p, "Bark", 8, min(R * 0.6, 3.2), min(R * 0.5, 2.6), 0, 3, x, y)
    frustum(p, "Twig", 8, 1.4, 0.7, 3, top - 6, x, y)
    for z in (38, 70, 102, 130):
        w = rng.uniform(R * 0.9, R * 1.7)
        box(p, "Bark", x, y, z, min(w, R * 1.9), 0.6, 0.6, rz=rng.uniform(0, 180))
        frustum(p, "DeepAlloy", 8, 1.2, 1.2, z - 0.6, z + 0.6, x, y)
    for z in (60, 112):                               # a hanging cage off a cross-tree
        cx = x + min(R - 1.4, 3.6)
        tube(p, "DeepAlloy", [(x, y, z + 2.0), (cx, y, z + 2.0), (cx, y, z - 1.0)], [0.12, 0.12, 0.12], n=3)
        frustum(p, "DeepAlloy", 6, 1.1, 1.1, z - 4.0, z - 1.0, cx, y)
        frustum(p, "Soot", 6, 1.2, 1.2, z - 4.2, z - 4.0, cx, y)
    cloth_banner(p, x + 0.6, y, 92, rng, w=min(R * 1.4, 7.0), h=18.0)
    frustum(p, "DeepAlloy", 6, 0.6, 0.0, top - 6, top, x, y)
    lump(p, "Bone", [(0.9, top - 12), (1.1, top - 11), (0, top - 10)], n=6, seed="totem skull", cx=x, cy=y)


# ==========================================================================
# LOCKDOWN -- the citadel's own defences: bunkers, masts, blast walls
# ==========================================================================

@style("lockdown", "tower")
def lockdown_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "bunker", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    frustum(p, "Gunmetal", 8, r * 1.2, r * 1.1, 0, 4, x, y)
    frustum(p, "Steel", 8, r * 1.02, r * 0.96, 4, H, x, y)
    for z in (H * 0.35, H * 0.7):
        frustum(p, "Gunmetal", 8, r * 1.08, r * 1.08, z, z + 1.2, x, y)
        frustum(p, "Hazard", 8, r * 1.1, r * 1.1, z + 1.2, z + 1.5, x, y)
    for k in range(4):                                 # slits, alarm-lit
        a = 45 + 90 * k
        d = r * 0.97
        box(p, "AlarmRed", x + math.cos(math.radians(a)) * d, y + math.sin(math.radians(a)) * d, H * 0.55,
            0.4, 1.0, H * 0.25, rz=a)
    # the turret: a squat armoured drum, a dome, twin guns on a random bearing
    frustum(p, "Gunmetal", 8, r * 1.22, r * 1.2, H, H + 2.6, x, y)
    frustum(p, "Steel", 12, r * 1.0, r * 0.4, H + 2.6, H + 2.6 + min(rh * 0.5, r * 1.2), x, y)
    b = rng.uniform(0, 360)
    with frame(p, xf(x, y, H + 3.2, b)):
        for s in (-0.9, 0.9):
            with frame(p, xf(r * 0.6, s, 0, 0, 0, 84)):
                frustum(p, "Gunmetal", 8, 0.45, 0.38, 0, r * 0.9)
    frustum(p, "Steel", 6, 0.2, 0.1, H + 2.6, min(H + 6 + rh - 0.3, H + 2.6 + rh * 0.95), x + r * 0.5, y)
    crystal(p, "AlarmRed", x + r * 0.5, y, min(H + 6 + rh - 0.3, H + 2.6 + rh * 0.95) - 0.2, 0.4, 0.5, 0.4)


@style("lockdown", "spire")
def lockdown_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "Gunmetal", 8, r * 1.5, r * 1.3, z0, z0 + 5, x, y)
    frustum(p, "Steel", 8, r * 0.9, r * 0.35, z0 + 5, H - 3, x, y)
    for k, f in enumerate((0.3, 0.5, 0.68, 0.84)):     # sensor dishes stacked up the mast
        z = z0 + L * f
        rr = r * (0.9 - 0.55 * f)
        frustum(p, "Gunmetal", 12, rr * 2.1, rr * 1.1, z, z + 1.0, x, y)
        frustum(p, "AlarmRed", 12, rr * 2.15, rr * 2.15, z + 1.0, z + 1.2, x, y)
    frustum(p, "Steel", 6, r * 0.35, 0.0, H - 3, H, x, y)


def _crown_lockdown(p, x, y, top, R, label):
    """AEGIS PYLON: a braced lattice mast, emitter rings, a red beacon."""
    p.solid(label, x, y, R, 0, top)
    s = min(R * 0.7, 3.4)
    frustum(p, "Gunmetal", 4, s * 1.3, s * 1.2, 0, 3, x, y, rot=45)
    legs = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        legs.append((math.cos(a), math.sin(a)))
    for cx, cy in legs:
        tube(p, "Steel", [(x + cx * s, y + cy * s, 2.5), (x + cx * 0.6, y + cy * 0.6, top - 10)], [0.45, 0.25], n=4)
    for z in range(12, int(top) - 16, 14):             # cross-bracing
        f = (z - 2.5) / (top - 12.5)
        w = s + (0.6 - s) * f
        for i in range(4):
            (ax, ay), (bx, by) = legs[i], legs[(i + 1) % 4]
            tube(p, "Gunmetal", [(x + ax * w, y + ay * w, z), (x + bx * w, y + by * w, z + 7)], [0.18, 0.18], n=3)
    for z in (60, 104):
        f = (z - 2.5) / (top - 12.5)
        w = s + (0.6 - s) * f
        torus(p, "AlarmRed", w + 1.2, 0.25, x, y, z, n=16)
        for cx, cy in legs:
            box(p, "Gunmetal", x + cx * (w + 0.6), y + cy * (w + 0.6), z, 1.4, 0.3, 0.3,
                rz=math.degrees(math.atan2(cy, cx)))
    frustum(p, "Steel", 6, 0.9, 0.5, top - 10.5, top - 2, x, y)
    crystal(p, "AlarmRed", x, y, top - 1.2, 0.9, 1.2, 0.8)


# ==========================================================================
# STORMHAWK -- storm-broken heights: sheared turrets, struck spires, roosts
# ==========================================================================

@style("stormhawk", "tower")
def stormhawk_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "sheared", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    frustum(p, "PaleAlloy", 8, r * 1.15, r * 1.1, 0, 3, x, y)
    top = H * rng.uniform(0.72, 0.95)
    frustum(p, "StormStone", 8, r, r * 0.95, 3, top, x, y)
    _jagged_top(p, "StormStone", x, y, r * 0.95, top, rng, n=11, hmax=5.5)
    for k in range(rng.randint(2, 3)):                 # blackened streaks from strikes
        a = rng.uniform(0, 360)
        d = r * 0.97
        box(p, "Soot", x + math.cos(math.radians(a)) * d, y + math.sin(math.radians(a)) * d,
            top * rng.uniform(0.4, 0.7), 0.25, rng.uniform(1.0, 2.2), top * rng.uniform(0.3, 0.5), rz=a,
            rx=rng.uniform(-8, 8))
    # the sheared-off roof, fallen and leaning on its own stump
    a = rng.uniform(0, 360)
    with frame(p, xf(x + math.cos(math.radians(a)) * r * 0.7, y + math.sin(math.radians(a)) * r * 0.7, top - 1.0,
                     a, 0, rng.uniform(28, 48))):
        frustum(p, "CitadelViolet", 8, r * 0.85, 0.0, 0, rh * 0.8)


@style("stormhawk", "spire")
def stormhawk_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    rng = _rng(p, "struck", x, y)
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "StormSlate", 8, r * 1.5, r * 1.3, z0, z0 + 4, x, y)
    # a shaft in stacked, slightly skewed drums, struck black in bands
    z, rr, k = z0 + 4, r * 1.02, 0
    while z < H - 6:
        h = min(rng.uniform(8, 16), H - 6 - z)
        r2 = max(0.4, rr * (1 - h / (L * 1.25)))
        frustum(p, "StormStone" if k % 3 else "Soot", 7, rr, r2, z, z + h, x + rng.uniform(-0.2, 0.2),
                y + rng.uniform(-0.2, 0.2), rot=rng.uniform(0, 50))
        z, rr, k = z + h, r2, k + 1
    frustum(p, "DeepAlloy", 6, max(rr, 0.3), 0.0, z, H, x, y)
    for k in range(5):                                 # fulgurite spurs where it was struck
        a = rng.uniform(0, 2 * math.pi)
        zz = z0 + L * rng.uniform(0.3, 0.75)
        with frame(p, xf(x, y, zz, math.degrees(a), 0, rng.uniform(50, 75))):
            crystal(p, "SkyGlass", 0, 0, 0, 0.35, rng.uniform(2.5, 4.5), 0.3, n=4)


def _crown_stormhawk(p, x, y, top, R, label):
    """ROOST PINNACLE: a pinnacle of storm-stone boulders heaped by the
    raptor, an iron rod driven through it to the crown."""
    rng = _rng(p, "pinnacle", x, y)
    p.solid(label, x, y, R, 0, top)
    z, rr = 0.0, min(R * 0.85, 4.4)
    while z < 104:
        h = rng.uniform(7, 12)
        lump(p, rng.choice(("StormStone", "StormSlate")), [(rr, z), (rr * 1.08, z + h * 0.4), (rr * 0.8, z + h),
                                                         (0, z + h + 0.4)],
             n=7, seed="pin %s %.0f" % (p.name, z), jitter=0.18, cx=x + rng.uniform(-0.4, 0.4),
             cy=y + rng.uniform(-0.4, 0.4))
        z, rr = z + h - 0.6, max(1.6, rr * rng.uniform(0.86, 0.96))
    frustum(p, "DeepAlloy", 6, 0.55, 0.2, z - 3, top - 1.5, x, y)
    torus(p, "SunGold", 1.1, 0.15, x, y, z + 12, n=10)
    frustum(p, "SunGold", 6, 0.25, 0.0, top - 1.5, top, x, y)
    for k in range(9):                                 # the roost's twigs round the top boulder
        a = 40 * k
        box(p, "Twig", x + math.cos(math.radians(a)) * rr * 0.8, y + math.sin(math.radians(a)) * rr * 0.8, z - 0.8,
            rr * 1.2, 0.5, 0.5, rz=a + 90, rx=rng.uniform(-15, 15))


# ==========================================================================
# RIME -- a citadel frozen inside its own ice
# ==========================================================================

@style("rime", "tower")
def rime_tower(p, x, y, r, H, roof_h=None, roof=True):
    rng = _rng(p, "frozen", x, y)
    _orig("tower")(p, x, y, r, H, roof_h, roof)       # the tower is still there, under the ice
    # an ice sheath climbing the lower shaft: lumpy, clear, thicker at the foot
    lump(p, "Ice", [(r * 1.22, -0.2), (r * 1.18, H * 0.22), (r * 1.06, H * rng.uniform(0.4, 0.55)),
                    (r * 0.9, H * rng.uniform(0.6, 0.7))], n=9, seed="sheath %s %.0f" % (p.name, x),
         jitter=0.06, cx=x, cy=y)
    if roof:
        rh = _roof_h(r, roof_h)
        # snow heaped on the roof's lower half
        frustum(p, "Snow", 8, r * 0.98, r * 0.55, H + 3, H + 3 + rh * 0.42, x, y)
    for k in range(rng.randint(2, 3)):                 # frozen buttresses
        a = math.radians(rng.uniform(0, 360))
        with frame(p, xf(x + math.cos(a) * r * 1.05, y + math.sin(a) * r * 1.05, 0, math.degrees(a), 0, -8)):
            crystal(p, "Ice", 0, 0, 0, r * 0.3, H * rng.uniform(0.35, 0.55), 0.3, n=5)


@style("rime", "spire")
def rime_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    """ICE NEEDLE: the spire gone to a faceted column of ice, snow-collared."""
    rng = _rng(p, "needle", x, y)
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "FrostDeep", 6, r * 1.5, r * 1.3, z0, z0 + 4, x, y)
    lump(p, "Snow", [(r * 1.7, z0 - 0.2), (r * 1.5, z0 + 2.2), (r * 0.9, z0 + 4.4), (0, z0 + 4.8)], n=9,
         seed="collar %s %.0f" % (p.name, x), jitter=0.1, cx=x, cy=y)
    frustum(p, "Ice", 6, r * 1.05, r * 0.3, z0 + 4, H - 2, x, y, rot=rng.uniform(0, 60))
    crystal(p, "SkyGlass", x, y, H - 2.2, r * 0.35, 2.2, 0.2, n=6)
    for f in (0.35, 0.62):
        z = z0 + L * f
        rr = r * (1.05 - 0.75 * f)
        lump(p, "Snow", [(rr * 1.35, z - 0.4), (rr * 1.3, z + 0.6), (rr * 0.8, z + 1.2), (0, z + 1.3)], n=8,
             seed="band %s %.0f %.2f" % (p.name, x, f), jitter=0.12, cx=x, cy=y)
    for k in range(4):                                 # ice shards leaning off the column
        a = rng.uniform(0, 2 * math.pi)
        zz = z0 + L * rng.uniform(0.15, 0.5)
        rr = r * (1.05 - 0.75 * (zz - z0) / L)
        with frame(p, xf(x + math.cos(a) * rr * 0.8, y + math.sin(a) * rr * 0.8, zz, math.degrees(a), 0,
                         rng.uniform(25, 40))):
            crystal(p, "Ice", 0, 0, 0, r * 0.25, rng.uniform(4, 8), 0.4, n=4)


def _crown_rime(p, x, y, top, R, label):
    """FROST OBELISK: a column of ice to the crown, skirted with icicles."""
    rng = _rng(p, "frost", x, y)
    p.solid(label, x, y, R, 0, top)
    b = min(R * 0.8, 4.6)
    lump(p, "Snow", [(b * 1.1, -0.2), (b, 3.0), (b * 0.6, 5.0), (0, 5.4)], n=9, seed="fo base %s" % p.name,
         jitter=0.1, cx=x, cy=y)
    frustum(p, "Ice", 4, b * 0.75, 0.6, 4, top - 3, x, y, rot=45)
    frustum(p, "SkyGlass", 4, b * 0.55, 0.4, 20, top - 6, x, y, rot=0)
    for z in (44, 84, 118):
        f = (z - 4) / (top - 7)
        w = b * 0.75 + (0.6 - b * 0.75) * f
        frustum(p, "Snow", 8, w * 1.3, w * 1.3, z, z + 0.8, x, y)
        for k in range(8):
            a = math.radians(45 * k + 12)
            crystal(p, "Ice", x + math.cos(a) * w * 1.15, y + math.sin(a) * w * 1.15, z + 0.1, 0.25, 0.01,
                    rng.uniform(1.5, 5.0), n=4)
    crystal(p, "SkyGlass", x, y, top - 3.2, 0.9, 3.2, 0.5, n=6)


# ==========================================================================
# RECLAIMED -- the green took it back: ruins, ivy, trees through the stone
# ==========================================================================

@style("reclaimed", "tower")
def reclaimed_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "ruin", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    frustum(p, "PaleAlloy", 8, r * 1.15, r * 1.1, 0, 3, x, y)
    top = H * rng.uniform(0.55, 0.8)
    frustum(p, "Weathered", 8, r, r * 0.96, 3, top, x, y)
    _jagged_top(p, "Weathered", x, y, r * 0.96, top, rng, n=10, hmax=4.0)
    _ivy(p, x, y, r * 0.97, 1.0, top * 0.9, rng, turns=rng.uniform(1.0, 2.0))
    _ivy(p, x, y, r * 0.97, 1.0, top * 0.7, rng, turns=-rng.uniform(0.8, 1.6), mat="Moss")
    # a tree grown up through the broken top
    trunk = min(rh * 1.3, H + 6 + rh - top - 6)
    frustum(p, "Bark", 7, r * 0.45, r * 0.28, top - 2, top + trunk, x, y)
    for k in range(rng.randint(3, 4)):
        a = rng.uniform(0, 360)
        with frame(p, xf(x, y, top + trunk * rng.uniform(0.5, 0.8), a, 0, rng.uniform(45, 65))):
            frustum(p, "Bark", 5, r * 0.2, r * 0.08, 0, r * 1.1)
    for k in range(rng.randint(3, 4)):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.0, 0.55) * r
        rr = rng.uniform(r * 0.5, r * 0.75)
        cz = top + trunk * rng.uniform(0.62, 0.9)
        lump(p, ("Verdure", "Moss", "MossLight")[k % 3], [(rr * 0.6, cz), (rr, cz + rr * 0.5), (rr * 0.8, cz + rr),
                                                          (0, cz + rr * 1.2)], n=7,
             seed="crown %s %.0f %d" % (p.name, x, k), jitter=0.2, cx=x + math.cos(a) * d, cy=y + math.sin(a) * d)


@style("reclaimed", "spire")
def reclaimed_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    rng = _rng(p, "choked", x, y)
    _orig("spire")(p, x, y, r, H, False, fins, 0, z0)   # the old spire, halo long gone
    L = H - z0
    _ivy(p, x, y, r * 1.0, z0 + 3, z0 + L * rng.uniform(0.45, 0.6), rng, turns=2.5)
    _ivy(p, x, y, r * 0.95, z0 + 3, z0 + L * rng.uniform(0.3, 0.4), rng, turns=-2.0, mat="Moss")
    lump(p, "Moss", [(r * 1.6, z0 - 0.2), (r * 1.55, z0 + 2.4), (r * 1.2, z0 + 4.3), (0, z0 + 4.6)], n=9,
         seed="moss foot %s %.0f" % (p.name, x), jitter=0.15, cx=x, cy=y)


def _crown_reclaimed(p, x, y, top, R, label):
    """WORLD TREE: a tree taller than the spires it replaced."""
    rng = _rng(p, "worldtree", x, y)
    p.solid(label, x, y, R, 0, top)
    b = min(R * 0.55, 3.6)
    frustum(p, "Bark", 8, b * 1.5, b, 0, 4, x, y)
    for k in range(5):                                 # roots gripping the deck
        a = rng.uniform(0, 2 * math.pi)
        tube(p, "Bark", [(x + math.cos(a) * b * 0.6, y + math.sin(a) * b * 0.6, 3.0),
                         (x + math.cos(a) * b * 1.5, y + math.sin(a) * b * 1.5, 0.6),
                         (x + math.cos(a) * min(R - 0.6, b * 2.4), y + math.sin(a) * min(R - 0.6, b * 2.4), 0.1)],
             [0.7, 0.5, 0.15], n=5)
    z, rr = 4.0, b
    pts, rad = [], []
    for j in range(9):
        pts.append((x + math.sin(j * 1.3) * 0.6, y + math.cos(j * 0.9) * 0.6, z))
        rad.append(rr)
        z += (top - 16) / 8                         # the trunk runs up into the canopy
        rr = max(0.9, rr * 0.9)
    tube(p, "Bark", pts, rad, n=7)
    for k in range(7):                                 # boughs and their foliage
        zz = 40 + k * (top - 70) / 6
        a = rng.uniform(0, 2 * math.pi)
        reach = min(R - 2.0, rng.uniform(4, 8))
        ex, ey = x + math.cos(a) * reach, y + math.sin(a) * reach
        tube(p, "Bark", [(x, y, zz), (ex, ey, zz + 4)], [0.8, 0.3], n=5)
        s = rng.uniform(2.6, 3.6)
        lump(p, ("Verdure", "Moss", "MossLight")[k % 3], [(s * 0.6, zz + 2.5), (s, zz + 4), (s * 0.7, zz + 6),
                                                          (0, zz + 7)], n=8, seed="bough %s %d" % (p.name, k),
             jitter=0.2, cx=ex, cy=ey)
    s = min(R - 1.0, 6.0)
    lump(p, "Verdure", [(s * 0.7, top - 14), (s, top - 10), (s * 0.8, top - 5), (0, top)], n=9,
         seed="canopy %s" % p.name, jitter=0.15, cx=x, cy=y)


# ==========================================================================
# AETHER SURGE -- crystal has come up through the stone
# ==========================================================================

@style("aether_surge", "tower")
def aether_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "burst", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    frustum(p, "Lavender", 8, r * 1.15, r * 1.1, 0, 3, x, y)
    top = H * rng.uniform(0.6, 0.8)
    frustum(p, "Pearl", 8, r, r * 0.95, 3, top, x, y)
    _jagged_top(p, "Pearl", x, y, r * 0.95, top, rng, n=9, hmax=2.5)
    for k in range(3):                                 # glowing seams up the shaft
        a = rng.uniform(0, 360)
        d = r * 0.97
        box(p, "AetherBloom", x + math.cos(math.radians(a)) * d, y + math.sin(math.radians(a)) * d, top * 0.5,
            0.2, 0.6, top * rng.uniform(0.6, 0.9), rz=a, rx=rng.uniform(-6, 6))
    # the crystal that broke it open, erupting from the top
    _crystal_burst(p, x, y, top - 1.0, rng, min(H + 6 + rh - top - 1.0, rh * 1.3 + 6), r * 0.7, 7)
    for k in range(rng.randint(3, 5)):                 # and shards out through the walls
        a = rng.uniform(0, 360)
        z = rng.uniform(4, top * 0.85)
        with frame(p, xf(x + math.cos(math.radians(a)) * r * 0.8, y + math.sin(math.radians(a)) * r * 0.8, z, a, 0,
                         rng.uniform(55, 75))):
            crystal(p, rng.choice(("AetherBloom", "SkyGlass")), 0, 0, 0, rng.uniform(0.7, 1.3), rng.uniform(3, 6),
                    0.5, n=5)


@style("aether_surge", "spire")
def aether_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    """A spire of solid crystal: a faceted shaft, a cage of shards at its foot."""
    rng = _rng(p, "cryspire", x, y)
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "Lavender", 6, r * 1.5, r * 1.3, z0, z0 + 3, x, y)
    frustum(p, "AetherBloom", 5, r * 1.1, r * 0.35, z0 + 3, H - 4, x, y, rot=rng.uniform(0, 72))
    frustum(p, "Pearl", 5, r * 0.6, r * 0.2, z0 + L * 0.3, H - 8, x, y, rot=rng.uniform(0, 72))
    crystal(p, "SkyGlass", x, y, H - 4.2, r * 0.36, 4.2, 0.3, n=5)
    for k in range(6):
        a = math.radians(60 * k + rng.uniform(-12, 12))
        with frame(p, xf(x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2, z0 + 2.5, math.degrees(a), 0,
                         rng.uniform(15, 30))):
            crystal(p, rng.choice(("AetherBloom", "Pearl", "SkyGlass")), 0, 0, 0, r * 0.3, rng.uniform(4, 9), 0.5,
                    n=5)


def _crown_aether(p, x, y, top, R, label):
    """RESONANCE CRYSTAL: one crystal from the deck to the crown, girdled."""
    rng = _rng(p, "resonance", x, y)
    p.solid(label, x, y, R, 0, top)
    b = min(R * 0.8, 4.2)
    frustum(p, "Lavender", 6, b * 1.3, b * 1.1, 0, 3, x, y)
    frustum(p, "AetherBloom", 6, b, 0.8, 3, top - 5, x, y, rot=rng.uniform(0, 60))
    frustum(p, "SkyGlass", 6, b * 0.55, 0.4, 14, top - 12, x, y, rot=rng.uniform(0, 60))
    for z in (48, 90, 124):
        f = (z - 3) / (top - 8)
        w = b + (0.8 - b) * f
        torus(p, "Pearl", w * 1.05 + 0.3, 0.3, x, y, z, n=12)
    crystal(p, "Pearl", x, y, top - 5.2, 0.8, 5.2, 0.3, n=6)
    _crystal_burst(p, x, y, 2.5, rng, 9.0, b * 0.8, 6)


# ==========================================================================
# UNMOORING -- held together by failing anti-grav: split, tethered, cracked
# ==========================================================================

@style("unmooring", "tower")
def unmooring_tower(p, x, y, r, H, roof_h=None, roof=True):
    if not roof:
        return _orig("tower")(p, x, y, r, H, roof_h, roof)
    rng = _rng(p, "split", x, y)
    rh = _roof_h(r, roof_h)
    p.solid("tower", x, y, r * 1.25, 0, H + 6 + rh)
    frustum(p, "PaleAlloy", 8, r * 1.15, r * 1.1, 0, 3, x, y)
    cut = H * rng.uniform(0.45, 0.6)
    frustum(p, "CitadelWhite", 8, r, r * 0.96, 3, cut, x, y)
    _jagged_top(p, "CitadelWhite", x, y, r * 0.96, cut, rng, n=9, hmax=1.6)
    # the anti-grav ring still holding what broke off: the upper tower floats
    # a few studs clear, turning slightly (a prop: it moves)
    frustum(p, "DeepAlloy", 8, r * 0.7, r * 0.7, cut, cut + 0.8, x, y)
    torus(p, "AzureNeon", r * 0.72, 0.3, x, y, cut + 0.9, n=12)
    gap = rng.uniform(2.5, 4.0)
    z1 = cut + gap
    tilt = rng.uniform(4, 9)
    with frame(p, xf(x, y, z1, rng.uniform(0, 360), tilt, 0)):
        with as_prop(p, "hover segment", I4):
            frustum(p, "AzureDim", 8, r * 0.7, r * 0.9, -0.8, 0, 0, 0)
            frustum(p, "CitadelWhite", 8, r * 0.93, r * 0.9, 0, H - cut - gap, 0, 0)
            frustum(p, "PaleAlloy", 8, r * 0.95, r * 1.18, H - cut - gap, H - cut - gap + 2, 0, 0)
            frustum(p, "CitadelViolet", 8, r * 0.9, 0.0, H - cut - gap + 2, H - cut - gap + 2 + rh * 0.9, 0, 0)


@style("unmooring", "spire")
def unmooring_spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
    """A spire in sleeves round a glowing tension core, the gaps between them
    showing it: the thing holding the spire together, visibly."""
    rng = _rng(p, "tension", x, y)
    p.solid("spire", x, y, r * (1.9 if (halo or extra_halos) else 1.5) + 0.5, z0, H)
    L = H - z0
    frustum(p, "PaleAlloy", 8, r * 1.5, r * 1.3, z0, z0 + 4, x, y)
    frustum(p, "AzureNeon", 8, r * 0.3, r * 0.12, z0 + 3, H - 2, x, y)
    z = z0 + 4
    while z < H - 8:
        h = min(rng.uniform(9, 16), H - 8 - z)
        f0, f1 = (z - z0) / L, (z + h - z0) / L
        frustum(p, "CitadelWhite", 8, r * (1.02 - 0.75 * f0), r * (1.02 - 0.75 * f1), z + 0.6, z + h - 0.6,
                x + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.3, 0.3), rot=rng.uniform(-8, 8))
        z += h
    frustum(p, "PaleAlloy", 8, r * 0.3, 0.0, H - 8, H, x, y)


def _crown_unmooring(p, x, y, top, R, label):
    """TETHERED BEACON: a mast of stacked anti-grav stages, glowing between."""
    rng = _rng(p, "tether", x, y)
    p.solid(label, x, y, R, 0, top)
    b = min(R * 0.7, 3.6)
    frustum(p, "DeepAlloy", 8, b * 1.3, b * 1.1, 0, 3, x, y)
    frustum(p, "AzureNeon", 8, 0.45, 0.3, 2, top - 3, x, y)
    z = 3.0
    while z < top - 12:
        h = rng.uniform(10, 18)
        w = b * (1 - 0.7 * z / top)
        frustum(p, "CitadelWhite", 6, w, w * 0.85, z + 1.5, min(z + h, top - 12), x, y, rot=rng.uniform(0, 60))
        torus(p, "AzureNeon", w * 0.95, 0.22, x, y, z + 0.8, n=12)
        z += h
    frustum(p, "PaleAlloy", 6, 0.5, 0.0, top - 12, top, x, y)


# ==========================================================================
# CROWNS: the tall landmark masts, one scenario design each
# ==========================================================================

CROWNS = {"siege": _crown_siege, "lockdown": _crown_lockdown, "stormhawk": _crown_stormhawk, "rime": _crown_rime,
          "reclaimed": _crown_reclaimed, "aether_surge": _crown_aether, "unmooring": _crown_unmooring}
MASTS = {"signal_mast": ("signal mast", 5.0), "banner_mast": ("banner mast", 9.0),
         "light_obelisk": ("light obelisk", 6.0)}


def _install_crowns():
    for scen, fn in CROWNS.items():
        for mast, (label, R) in MASTS.items():
            def make(fn=fn, label=label, R=R, mast=mast):
                def crown(p, x, y, top=CROWN_TOP):
                    fn(p, x, y, top, R, label)
                crown.__code__ = crown.__code__.replace(co_name=mast)
                return crown
            STYLES.setdefault(scen, {})[mast] = make()
        # a crown SPIRE (the spire that reaches the top of the box) is the
        # scenario's own crown landmark too, on the spire's own footprint
        spire_style = STYLES[scen]["spire"]

        def make_spire(fn=fn, spire_style=spire_style):
            def spire(p, x, y, r, H, halo=True, fins=True, extra_halos=0, z0=0.0):
                if H >= CROWN_TOP - 0.01 and z0 < 1.0:
                    R = r * (1.9 if (halo or extra_halos) else 1.5) + 0.5
                    frustum(p, "PaleAlloy" if scen != "lockdown" else "Gunmetal", 8, r * 1.5, r * 1.3, 0, 4, x, y)
                    fn(p, x, y, H, R, "spire")
                else:
                    spire_style(p, x, y, r, H, halo, fins, extra_halos, z0)
            spire.__code__ = spire.__code__.replace(co_name="spire")
            return spire
        STYLES[scen]["spire"] = make_spire()


# ==========================================================================
# RIMS -- what runs round each deck's edge
# ==========================================================================

@edge("siege", "parapet", "hedge")
def siege_palisade(p, a, b, inward):
    rng = _rng(p, "pal", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(2, int(L / 1.6))
    for i in range(n + 1):
        t = i / n
        h = rng.uniform(3.4, 5.2)
        with frame(p, xf(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, -0.2, ang, rng.uniform(-3, 3), rng.uniform(-4, 4))):
            frustum(p, "Twig", 4, 0.45, 0.0, 0, h, rot=45)
    ix, iy = inward
    for z in (1.1, 2.6):
        box(p, "Bark", (x0 + x1) / 2 + ix * 0.3, (y0 + y1) / 2 + iy * 0.3, z, max(1.0, L - 0.4), 0.45, 0.45, rz=ang)


@edge("siege", "railing", "kerb")
def siege_scrap_wall(p, a, b, inward):
    rng = _rng(p, "scrap", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.9)
    n = max(1, int(L / 3.2))
    for i in range(n):
        t = (i + 0.5) / n
        h = rng.uniform(1.4, 2.6)
        box(p, rng.choice(("RaiderRust", "DeepAlloy", "Soot")), x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, h / 2 - 0.1,
            L / n + 0.3, 0.5, h, rz=ang + rng.uniform(-6, 6), rx=rng.uniform(-6, 6))


@edge("lockdown", "parapet", "hedge")
def lockdown_blast(p, a, b, inward):
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box(p, "Steel", mx, my, 1.7, L, 1.4, 3.4, rz=ang)
    box(p, "Hazard", mx, my, 3.5, L + 0.02, 1.5, 0.3, rz=ang)
    n = max(1, int(L / 7))
    for i in range(n + 1):
        t = i / n
        box(p, "Gunmetal", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.9, 1.0, 1.9, 3.8, rz=ang)


@edge("lockdown", "railing", "kerb")
def lockdown_fence(p, a, b, inward):
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, round(L / 8))
    for i in range(n + 1):
        t = i / n
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        frustum(p, "Gunmetal", 4, 0.45, 0.35, 0, 3.4, px, py, rot=45)
        crystal(p, "AlarmRed", px, py, 3.6, 0.3, 0.3, 0.2)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    for z in (1.0, 2.0, 3.0):
        box(p, "AlarmRed", mx, my, z, L, 0.12, 0.12, rz=ang)


@edge("stormhawk", "parapet", "hedge", "kerb")
def stormhawk_wall(p, a, b, inward):
    """A parapet the storm has been at: merlons gone, the wall uneven."""
    rng = _rng(p, "worn", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, int(L / 4.0))
    for i in range(n):
        t = (i + 0.5) / n
        h = rng.uniform(1.0, 2.6) if rng.random() > 0.12 else 0.5
        box(p, rng.choice(("StormStone", "StormSlate", "CitadelWhite")), x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
            h / 2, L / n + 0.05, 1.6, h, rz=ang)


@edge("stormhawk", "railing")
def stormhawk_rail(p, a, b, inward):
    rng = _rng(p, "bent", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, round(L / 10))
    posts = []
    for i in range(n + 1):
        t = i / n
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        box(p, "StormSlate", px, py, 1.5, 0.6, 0.6, 3.0)
        posts.append((px, py))
    for (ax, ay), (bx, by) in zip(posts, posts[1:]):
        if rng.random() < 0.25:
            continue                                   # a bar torn away by the wind
        dip = rng.uniform(0.2, 1.2)                    # the rest bent where something struck
        tube(p, "PaleAlloy", [(ax, ay, 2.8), ((ax + bx) / 2, (ay + by) / 2, 2.8 - dip), (bx, by, 2.8)],
             [0.2, 0.2, 0.2], n=4)


@edge("rime", "parapet", "hedge", "kerb")
def rime_wall(p, a, b, inward):
    """The parapet, drifted over: snow banked along it, ice along its top."""
    rng = _rng(p, "drift", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box(p, "Frost", mx, my, 1.1, L, 1.6, 2.2, rz=ang)
    with frame(p, xf(mx, my, 0, ang)):
        lump(p, "Snow", [(2.4, -0.1), (2.2, 1.2), (1.4, 2.6), (0, 3.0)], n=7, seed="rw %s %.0f" % (p.name, mx),
             jitter=0.2, sx=max(1.0, L / 4.6), sy=0.9)
    n = max(1, int(L / 3.4))
    ix, iy = inward
    for i in range(n):
        t = (i + 0.5) / n
        crystal(p, "Ice", x0 + (x1 - x0) * t - ix * 0.9, y0 + (y1 - y0) * t - iy * 0.9, 2.1, rng.uniform(0.2, 0.35),
                0.01, rng.uniform(0.8, 2.0), n=4)


@edge("rime", "railing")
def rime_rail(p, a, b, inward):
    rng = _rng(p, "icerail", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    _orig_rail(p, x0, y0, x1, y1)
    n = max(2, int(L / 1.8))
    for i in range(n):
        t = (i + 0.5) / n
        crystal(p, "Ice", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 2.62, rng.uniform(0.15, 0.3), 0.01,
                rng.uniform(0.6, 1.9), n=4)
    with frame(p, xf((x0 + x1) / 2, (y0 + y1) / 2, 2.95, ang)):
        box(p, "Snow", 0, 0, 0, L, 0.8, 0.35)


@edge("reclaimed", "parapet", "kerb")
def reclaimed_ruin(p, a, b, inward):
    """A ruined wall: stretches fallen, what stands mossed along its top."""
    rng = _rng(p, "ruinwall", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, int(L / 6.5))
    for i in range(n):
        t = (i + 0.5) / n
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if rng.random() < 0.3:                          # fallen: a mossy heap where it stood
            lump(p, "Moss", [(1.6, -0.1), (1.5, 0.6), (0.8, 1.2), (0, 1.4)], n=5, seed="rr %s %.1f" % (p.name, cx),
                 jitter=0.25, cx=cx, cy=cy)
            continue
        h = rng.uniform(1.2, 2.6)
        box(p, "Weathered", cx, cy, h / 2, L / n + 0.05, 1.6, h, rz=ang)
        box(p, rng.choice(("Moss", "MossLight")), cx, cy, h + 0.12, L / n * rng.uniform(0.6, 1.0), 1.75, 0.3,
            rz=ang + rng.uniform(-3, 3))


@edge("reclaimed", "railing", "hedge")
def reclaimed_hedge(p, a, b, inward):
    """A hedge gone wild: a clipped body long since lost under bulges."""
    rng = _rng(p, "wild", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 1.3)
    box(p, "Verdure", (x0 + x1) / 2, (y0 + y1) / 2, 1.1, max(1.0, L - 0.6), 2.2, 2.2, rz=ang)
    n = max(1, int(L / 7.0))
    for i in range(n):
        t = (i + rng.uniform(0.3, 0.7)) / n
        r = rng.uniform(1.4, 1.9)
        lump(p, rng.choice(("Moss", "MossLight")), [(r, 1.2), (r * 1.1, 1.2 + r * 0.8), (r * 0.6, 1.2 + r * 1.4),
                                                    (0, 1.2 + r * 1.6)], n=5,
             seed="rh %s %.1f %d" % (p.name, x0, i), jitter=0.22, cx=x0 + (x1 - x0) * t, cy=y0 + (y1 - y0) * t)


@edge("aether_surge", "parapet", "hedge", "kerb")
def aether_wall(p, a, b, inward):
    """The parapet run through with crystal: shards up through its top."""
    rng = _rng(p, "cryw", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    box(p, "Pearl", mx, my, 0.9, L, 1.6, 1.8, rz=ang)
    box(p, "AetherDim", mx, my, 1.85, L + 0.02, 1.7, 0.2, rz=ang)
    n = max(1, int(L / 3.0))
    for i in range(n):
        t = (i + rng.uniform(0.2, 0.8)) / n
        crystal(p, rng.choice(("AetherBloom", "SkyGlass", "Pearl")), x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.2,
                rng.uniform(0.35, 0.6), rng.uniform(1.6, 4.2), 0.6, n=5, rz=rng.uniform(0, 72))


@edge("aether_surge", "railing")
def aether_fence(p, a, b, inward):
    rng = _rng(p, "cryf", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(2, int(L / 2.4))
    for i in range(n + 1):
        t = i / n
        crystal(p, rng.choice(("AetherBloom", "SkyGlass")), x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.0,
                rng.uniform(0.3, 0.5), rng.uniform(2.2, 3.6), 0.4, n=4, rz=rng.uniform(0, 90))
    box(p, "AetherDim", (x0 + x1) / 2, (y0 + y1) / 2, 0.15, L, 0.9, 0.3, rz=ang)


@edge("unmooring", "parapet", "hedge", "kerb")
def unmooring_wall(p, a, b, inward):
    """A parapet in blocks that have shifted: out of line, off level, gaps."""
    rng = _rng(p, "shift", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, int(L / 3.6))
    ix, iy = inward
    for i in range(n):
        if rng.random() < 0.1:
            continue
        t = (i + 0.5) / n
        off = rng.uniform(-0.35, 0.35)
        h = rng.uniform(1.8, 2.6)
        box(p, "CitadelWhite", x0 + (x1 - x0) * t + ix * off, y0 + (y1 - y0) * t + iy * off, h / 2 - 0.15,
            L / n - 0.25, 1.6, h, rz=ang + rng.uniform(-4, 4), rx=rng.uniform(-3, 3))
        if rng.random() < 0.5:
            box(p, "AzureNeon", x0 + (x1 - x0) * t + ix * off, y0 + (y1 - y0) * t + iy * off, h - 0.2,
                L / n - 0.2, 1.7, 0.15, rz=ang)


@edge("unmooring", "railing")
def unmooring_rail(p, a, b, inward):
    rng = _rng(p, "sag", a[0], a[1])
    x0, y0, x1, y1, L, ang = _seg(a, b, inward, 0.8)
    n = max(1, round(L / 12))
    pts = []
    for i in range(n + 1):
        t = i / n
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        box(p, "PaleAlloy", px, py, 1.6, 0.7, 0.7, 3.2)
        pts.append((px, py))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        sag = rng.uniform(0.3, 1.4)
        tube(p, "PaleAlloy", [(ax, ay, 2.9), ((ax + bx) / 2, (ay + by) / 2, 2.9 - sag), (bx, by, 2.9)],
             [0.22, 0.22, 0.22], n=4)


def _orig_edge(kind):
    return ORIG["EDGES"][kind]


def _orig_rail(p, x0, y0, x1, y1):
    ORIG["railing"](p, x0, y0, x1, y1)


# ==========================================================================
# FLOORS -- what is painted, laid or grown on the deck
# ==========================================================================

FLOOR_MATS = {
    "siege": ("Bark", "Twig", "Char"),
    "lockdown": ("Hazard", "Gunmetal", "AlarmDim"),
    "stormhawk": ("StormSlate", "Soot", "AzureNeon"),
    "rime": ("Snow", "FrostDeep", "Ice"),
    "reclaimed": ("Moss", "MossLight", "Verdure"),
    "aether_surge": ("AetherDim", "AetherBloom", "Pearl"),
    "unmooring": ("DeepAlloy", "AzureNeon", "PaleAlloy"),
}


def _make_floors(scen):
    m0, m1, m2 = FLOOR_MATS[scen]

    def floor_checker(p, pts, mat, tile=10.0, margin=5.0, keep=None, z=0.06):
        """The scenario's own floor: a scattered, broken field of its tiles
        (planks, plates, slabs, frost, moss, crystal), never a clean grid."""
        rng = _rng(p, "floor", tile, len(pts))
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        step = tile * rng.uniform(0.9, 1.4)
        y = min(ys) + step / 2
        row = 0
        while y < max(ys):
            x = min(xs) + step / 2 + (step / 2 if row % 2 else 0)
            while x < max(xs):
                if rng.random() < 0.55 and inside(pts, x, y, margin + step / 2):
                    if keep is None or keep(x, y):
                        s = step * rng.uniform(0.5, 0.9)
                        panel(p, rng.choice((m0, m0, m1)), x, y, s, s * rng.uniform(0.4, 1.0), z=z,
                              rz=rng.uniform(-25, 25) if scen in ("siege", "stormhawk", "reclaimed", "unmooring")
                              else (45 if scen == "aether_surge" else 0))
                x += step
            y += step
            row += 1

    def floor_radial(p, cx, cy, r0, r1, n, mat, width=2.0, z=0.06, phase=0.0):
        rng = _rng(p, "radial", cx, cy, r0)
        for k in range(n):
            if rng.random() < 0.25:
                continue
            a = math.radians(phase + 360.0 * k / n + rng.uniform(-6, 6))
            _zigzag(p, m1 if k % 2 else m2, cx + math.cos(a) * r0, cy + math.sin(a) * r0,
                    cx + math.cos(a) * r1 * rng.uniform(0.7, 1.0), cy + math.sin(a) * r1 * rng.uniform(0.7, 1.0), rng,
                    w=width * 0.7, n=4, amp=(r1 - r0) * 0.05, z=z)

    def floor_grid(p, pts, mat, step=16.0, w=0.8, margin=4.0):
        rng = _rng(p, "grid", step, len(pts))
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        for _ in range(int((max(xs) - min(xs)) * (max(ys) - min(ys)) / (step * step * 3))):
            x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
            if inside(pts, x, y, margin + 3):
                L = step * rng.uniform(0.4, 0.9)
                panel(p, rng.choice((m1, m2)), x, y, L, w, z=0.07, rz=rng.choice((0, 90)) + rng.uniform(-10, 10))

    def floor_planks(p, x0, x1, y0, y1, mat, step=5.0, width=2.2):
        rng = _rng(p, "planks", x0, y0)
        y = y0 + step / 2
        while y < y1:
            if rng.random() < 0.75:
                L = (x1 - x0) * rng.uniform(0.55, 1.0)
                cx = x0 + L / 2 + rng.uniform(0, (x1 - x0) - L)
                panel(p, rng.choice((m0, m1)), cx, y, L, width, rz=rng.uniform(-3, 3))
            y += step

    def floor_stars(p, cx, cy, rmin, rmax, count, seed, keep=None):
        rng = random.Random("%s %s" % (seed, scen))
        placed, tries = 0, 0
        while placed < count and tries < count * 20:
            tries += 1
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(rmin, rmax)
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
            if keep and not keep(x, y):
                continue
            s = rng.uniform(0.8, 1.8)
            panel(p, m2 if rng.random() < 0.5 else m1, x, y, s, s * rng.uniform(0.4, 1.0), rz=rng.uniform(0, 90))
            placed += 1

    def compass_rose(p, cx, cy, r_long, r_short):
        """The scenario's own sigil where the base kit laid its compass."""
        rng = _rng(p, "sigil", cx, cy)
        if scen == "lockdown":                          # a targeting reticle
            _panel_ring(p, (m0, m2), cx, cy, r_long * 0.8, 16, 0.7, r_long * 0.28)
            for k in range(4):
                a = math.radians(90 * k)
                panel(p, m0, cx + math.cos(a) * r_long * 0.45, cy + math.sin(a) * r_long * 0.45, r_long * 0.5, 1.0,
                      z=0.08, rz=90 * k)
        elif scen == "aether_surge":                    # a hexagram of light
            for k in range(6):
                a = math.radians(60 * k)
                b2 = math.radians(60 * k + 120)
                tri_panel(p, m1 if k % 2 else m2, (cx, cy),
                          (cx + math.cos(a) * r_long, cy + math.sin(a) * r_long),
                          (cx + math.cos(b2) * r_long * 0.5, cy + math.sin(b2) * r_long * 0.5), z=0.08)
        elif scen == "rime":                            # a snowflake
            for k in range(6):
                a = math.radians(60 * k)
                panel(p, m0, cx + math.cos(a) * r_long / 2, cy + math.sin(a) * r_long / 2, r_long, 1.2, z=0.08,
                      rz=60 * k)
                for f in (0.45, 0.75):
                    for s in (-1, 1):
                        bx, by = cx + math.cos(a) * r_long * f, cy + math.sin(a) * r_long * f
                        panel(p, m2, bx + math.cos(a + s * 0.8) * 1.6, by + math.sin(a + s * 0.8) * 1.6, 3.4, 0.8,
                              z=0.09, rz=math.degrees(a + s * 0.8))
        elif scen == "siege":                           # a raider brand, burnt in
            for k in range(3):
                a = math.radians(120 * k + 90)
                _zigzag(p, m2, cx, cy, cx + math.cos(a) * r_long, cy + math.sin(a) * r_long, rng, w=2.2, n=3,
                        amp=2.0, z=0.08)
            lump(p, "Char", [(r_short, 0.04), (r_short, 0.1)], n=9, seed="brand %s" % p.name, jitter=0.3,
                 cx=cx, cy=cy)
        elif scen == "stormhawk":                       # a strike scar: a starburst of zigzags
            for k in range(7):
                a = math.radians(rng.uniform(0, 360))
                _zigzag(p, m1 if k % 2 else m2, cx, cy, cx + math.cos(a) * r_long, cy + math.sin(a) * r_long, rng,
                        w=1.0, n=5, amp=1.8, z=0.08)
        elif scen == "reclaimed":                       # moss grown over the old rose
            for k in range(9):
                a = rng.uniform(0, 2 * math.pi)
                d = rng.uniform(0, r_long * 0.8)
                lump(p, rng.choice((m0, m1)), [(rng.uniform(1.6, 3.4), 0.03), (rng.uniform(1.4, 3.0), 0.12)], n=8,
                     seed="rose moss %s %d" % (p.name, k), jitter=0.3, cx=cx + math.cos(a) * d,
                     cy=cy + math.sin(a) * d)
        else:                                           # unmooring: the rose, split by a fault
            ORIG["compass_rose"](p, cx, cy, r_long, r_short)
            a = rng.uniform(0, 180)
            _zigzag(p, m1, cx - math.cos(math.radians(a)) * r_long, cy - math.sin(math.radians(a)) * r_long,
                    cx + math.cos(math.radians(a)) * r_long, cy + math.sin(math.radians(a)) * r_long, rng, w=1.4,
                    n=6, amp=2.2, z=0.09)

    def border_band(p, pts, width=6.0):
        rng = _rng(p, "band", width, len(pts))
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            ex, ey = x1 - x0, y1 - y0
            L = math.hypot(ex, ey)
            ix, iy = -ey / L, ex / L
            off = 1.6 + width / 2
            ang = math.degrees(math.atan2(ey, ex))
            k = max(1, int((L - 2 * width) / 6))
            for j in range(k):
                if rng.random() < 0.35:
                    continue
                t = (j + 0.5) / k
                px = x0 + ex * (width / L + t * (1 - 2 * width / L)) + ix * off
                py = y0 + ey * (width / L + t * (1 - 2 * width / L)) + iy * off
                panel(p, rng.choice((m0, m1)), px, py, (L - 2 * width) / k * 0.8, width * rng.uniform(0.5, 0.9),
                      z=0.05, rz=ang + rng.uniform(-4, 4))

    out = {"floor_checker": floor_checker, "floor_radial": floor_radial, "floor_grid": floor_grid,
           "floor_planks": floor_planks, "floor_stars": floor_stars, "compass_rose": compass_rose,
           "border_band": border_band}
    for name, fn in out.items():
        fn.__code__ = fn.__code__.replace(co_name=name)
        STYLES.setdefault(scen, {})[name] = fn


# ==========================================================================
# OBELISKS and CRYSTAL CLUSTERS -- the smaller set pieces
# ==========================================================================

def _make_small(scen):
    def obelisk(p, x, y, h=26.0):
        rng = _rng(p, "obelisk", x, y)
        p.solid("obelisk", x, y, 4.6, 0, h + 11)
        if scen == "siege":                             # a trophy pole
            frustum(p, "Bark", 4, 1.2, 0.9, 0, h, x, y, rot=45)
            box(p, "Bark", x, y, h * 0.8, 6, 0.5, 0.5, rz=rng.uniform(0, 180))
            lump(p, "Bone", [(1.1, h), (1.3, h + 1.0), (0, h + 1.9)], n=6, seed="trophy", cx=x, cy=y)
            cloth_banner(p, x + 0.8, y, h * 0.8 - 0.4, rng, w=2.6, h=5.0)
        elif scen == "lockdown":                        # a sentinel mast
            frustum(p, "Gunmetal", 4, 3.6, 3.0, 0, 2, x, y, rot=45)
            frustum(p, "Steel", 6, 0.8, 0.5, 2, h, x, y)
            frustum(p, "Gunmetal", 8, 2.2, 1.0, h, h + 1.4, x, y)
            crystal(p, "AlarmRed", x, y, h + 2.2, 0.8, 1.0, 0.8)
        elif scen == "stormhawk":                       # a struck, split stone
            frustum(p, "StormSlate", 4, 4.2, 3.4, 0, 1.5, x, y, rot=45)
            for s in (-1, 1):
                with frame(p, xf(x + s * 0.9, y, 1.5, 0, 0, s * rng.uniform(4, 9))):
                    frustum(p, "StormStone", 4, 1.7, 0.6, 0, h * rng.uniform(0.55, 0.85), 0, 0, rot=45)
        elif scen == "rime":
            _orig("obelisk")(p, x, y, h)
            lump(p, "Ice", [(3.4, -0.2), (3.0, h * 0.35), (2.2, h * 0.55), (0, h * 0.62)], n=8,
                 seed="iced %s %.0f" % (p.name, x), jitter=0.08, cx=x, cy=y)
        elif scen == "reclaimed":                       # toppled, broken in two, mossed
            frustum(p, "DeepAlloy", 4, 4.6, 4.2, 0, 1.5, x, y, rot=45)
            frustum(p, "Weathered", 4, 3.6, 2.8, 1.5, h * 0.4, x, y, rot=45)
            _jagged_top(p, "Weathered", x, y, 2.8, h * 0.4, rng, n=6, hmax=1.6)
            lump(p, "Moss", [(3.8, 1.3), (3.4, 2.4), (2.2, 3.4), (0, 3.8)], n=8, seed="ob moss %s %.0f" % (p.name, x),
                 jitter=0.2, cx=x, cy=y)
        elif scen == "aether_surge":
            frustum(p, "Lavender", 4, 4.6, 4.2, 0, 1.5, x, y, rot=45)
            _crystal_burst(p, x, y, 1.2, rng, h * 0.9, 2.2, 5)
        else:                                           # unmooring: the needle, lifted off its plinth
            frustum(p, "DeepAlloy", 4, 4.6, 4.2, 0, 1.5, x, y, rot=45)
            torus(p, "AzureNeon", 2.4, 0.3, x, y, 1.9, n=12)
            with frame(p, xf(x, y, 3.0, rng.uniform(0, 90), rng.uniform(3, 7), 0)):
                with as_prop(p, "hover segment", I4):
                    frustum(p, "PaleAlloy", 4, 3.6, 1.9, 0, h - 1.5, 0, 0, rot=45)
                    frustum(p, "SunGold", 4, 1.9, 0, h - 1.5, h + 2.5, 0, 0, rot=45)

    def crystal_cluster(p, x, y, seed, scale=1.0):
        rng = random.Random("%s %s" % (seed, scen))
        p.solid("crystal cluster", x, y, 3.5 * scale, 0, 9 * scale)
        mats = {"siege": ("Soot", "RaiderRust"), "lockdown": ("AlarmRed", "Steel"),
                "stormhawk": ("StormStone", "SkyGlass"), "rime": ("Ice", "SkyGlass"),
                "reclaimed": ("MossLight", "SkyGlass"), "aether_surge": ("AetherBloom", "Pearl"),
                "unmooring": ("AzureNeon", "SkyGlass")}[scen]
        for i in range(rng.randint(4, 7)):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(0, 1.9) * scale
            crystal(p, mats[i % 2], x + math.cos(a) * d, y + math.sin(a) * d, 0.2,
                    rng.uniform(0.5, 1.2) * scale, rng.uniform(2.5, 8.5) * scale, 1.0, n=rng.choice((4, 5, 6)),
                    rz=rng.uniform(0, 72))

    for name, fn in (("obelisk", obelisk), ("crystal_cluster", crystal_cluster)):
        fn.__code__ = fn.__code__.replace(co_name=name)
        STYLES.setdefault(scen, {})[name] = fn


# the kit's own parts, before any style is installed
for _n in ("tower", "spire", "obelisk", "compass_rose", "railing"):
    ORIG[_n] = K[_n]
ORIG["EDGES"] = dict(K["EDGES"])
for _s in CROWNS:
    _make_floors(_s)
    _make_small(_s)
_install_crowns()
for _n in ("_seg", "_orig_edge", "_orig_rail", "_rng", "_roof_h", "_orig", "crown", "make_spire", "make",
           "_crown_siege", "_crown_lockdown", "_crown_stormhawk", "_crown_rime", "_crown_reclaimed",
           "_crown_aether", "_crown_unmooring"):
    K["PRIMITIVES"].add(_n)
