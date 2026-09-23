"""Sky Citadel scatter props -- the library the game scatters at run time.

Executed by build_sky_citadel_scenarios.py into its own namespace (it needs
box, frustum, crystal, torus, lump, blot, frame, xf, add_faces from there).

A FAMILY is one kind of thing (a tent, a moss mound, a turret) with several
seeded VARIANTS. Every variant is one fixed shape -- built at the origin, on
z = 0, facing +X -- so it is exactly one library mesh however often a run
places it. Size, turn and position are chosen by the game when it scatters.

Each family says where it belongs and how it is placed:
  sets      which prop sets (base world, or a scenario) may use it
  rule      the spawn points it needs: Any, Wall (the foot of a wall), Open
            (away from walls), Lee (walls facing this run's wind), Base (at a
            tower's foot)
  align     Wall = turned to run along the wall; Random = any turn
  anim      the PropCore animation class; interact = what the game wires
  tier      detail tier (2 = dropped on low graphics)
  air       floats in open air instead of standing on the deck

A family's footprint radius and height are MEASURED from its shape, never
typed in, so the scatter can never be told a prop is smaller than it is.
"""

FAMILIES = {}


def family(name, sets, n, anim="Static", tier=1, interact=None, rule="Any", align="Random",
           scale=(850, 1150), air=False, weight=4):
    def deco(fn):
        FAMILIES[name] = {"name": name, "sets": sets, "n": n, "fn": fn, "anim": anim, "tier": tier,
                          "interact": interact, "rule": rule, "align": align, "scale": scale, "air": air,
                          "weight": weight}
        return fn
    return deco


def R(name, v):
    return random.Random("%s/%d" % (name, v))


def cyl(p, mat, r0, r1, z0, z1, x=0.0, y=0.0, n=8, rot=None):
    frustum(p, mat, n, r0, r1, z0, z1, x, y, rot=rot)


def lay(p, M):
    """Build in a local frame (a shorthand for `with frame`)."""
    return frame(p, M)


# ==========================================================================
# BASE -- the citadel going about its day
# ==========================================================================

@family("supply_crates", ["base", "siege", "unmooring"], 4, interact="Breakable", rule="Wall", align="Wall")
def f_supply_crates(p, v):
    r = R("crates", v)
    stacks = [[(0, 0, 0, 3.0)], [(0, 0, 0, 3.0), (3.2, 0.2, 0, 2.6)], [(0, 0, 0, 3.0), (0.2, 0.1, 3.0, 2.6)],
              [(0, 0, 0, 3.0), (3.1, -0.3, 0, 3.0), (1.5, 0, 3.0, 2.6)]][v]
    for (x, y, z, s) in stacks:
        rz = r.uniform(-12, 12)
        box(p, "PaleAlloy", x, y, z + s / 2, s, s, s, rz=rz)
        box(p, "DeepAlloy", x, y, z + s / 2, s + 0.2, s + 0.2, s * 0.22, rz=rz)
        if r.random() < 0.5:
            box(p, "SunGold", x, y - s / 2 - 0.06, z + s * 0.62, 0.8, 0.12, 0.8, rz=rz)


@family("casks", ["base"], 3, interact="Breakable", rule="Wall")
def f_casks(p, v):
    spots = [[(0, 0)], [(0, 0), (2.0, 0.3)], [(0, 0), (1.9, 0.5), (0.8, 1.8)]][v]
    for x, y in spots:
        cyl(p, "CitadelWhite", 0.9, 0.95, 0, 2.2, x, y)
        for z in (0.4, 1.7):
            cyl(p, "AzureDim", 0.97, 0.97, z, z + 0.14, x, y)


@family("planter", ["base"], 3, rule="Open")
def f_planter(p, v):
    if v == 0:
        box(p, "PaleAlloy", 0, 0, 0.7, 3.6, 3.6, 1.4)
        lump(p, "Verdure", [(1.4, 1.4), (1.6, 2.6), (0.9, 3.7), (0, 4.2)], n=8, seed="planter topiary")
    elif v == 1:
        cyl(p, "PaleAlloy", 1.8, 1.6, 0, 1.2, n=8)
        cyl(p, "SunGold", 1.85, 1.85, 1.0, 1.2, n=8)
        frustum(p, "Verdure", 7, 1.5, 0.0, 1.2, 5.2)
    else:
        box(p, "DeepAlloy", 0, 0, 0.6, 7.0, 2.2, 1.2)
        for k in range(5):
            lump(p, "Verdure" if k % 2 else "Moss", [(0.8, 1.2), (0.9, 1.8), (0, 2.3)], n=6, seed="planter row %d" % k,
                 cx=-2.8 + 1.4 * k)


@family("lantern", ["base"], 2, rule="Wall", tier=2)
def f_lantern(p, v):
    h = 4.0 if v == 0 else 6.0
    cyl(p, "DeepAlloy", 0.6, 0.5, 0, 0.4, n=6)
    cyl(p, "PaleAlloy", 0.18, 0.18, 0.4, h, n=6)
    box(p, "DeepAlloy", 0, 0, h + 0.1, 1.0, 1.0, 0.2)
    crystal(p, "AzureNeon", 0, 0, h + 1.0, 0.45, 0.8, 0.7, n=4)


@family("statue", ["base", "reclaimed"], 3, rule="Open", interact="Use")
def f_statue(p, v):
    box(p, "PaleAlloy", 0, 0, 0.8, 3.0, 3.0, 1.6)
    box(p, "SunGold", 0, 0, 1.65, 3.1, 3.1, 0.12)
    if v == 0:      # a knight at rest on a sword
        box(p, "CitadelWhite", 0, 0, 3.4, 1.3, 0.9, 3.4)
        lump(p, "CitadelWhite", [(0.5, 5.1), (0.55, 5.6), (0, 6.2)], n=6, seed="statue head")
        box(p, "SunGold", 0.9, 0, 3.0, 0.2, 0.2, 3.2)
    elif v == 1:    # an orb held up
        frustum(p, "CitadelWhite", 6, 0.9, 0.5, 1.7, 5.2)
        lump(p, "SkyGlass", [(0.6, 5.2), (1.0, 5.9), (0.6, 6.7), (0, 7.0)], n=7, seed="statue orb", jitter=0.0)
    else:           # a winged figure
        box(p, "CitadelWhite", 0, 0, 3.3, 1.0, 0.8, 3.2)
        for s in (-1, 1):
            box(p, "CitadelWhite", 0, s * 1.3, 4.3, 0.2, 2.4, 1.6, rx=s * 25)
        lump(p, "CitadelWhite", [(0.45, 4.9), (0.5, 5.4), (0, 5.9)], n=6, seed="statue head b")


@family("hand_cart", ["base", "siege"], 2, interact="Loot", rule="Open")
def f_hand_cart(p, v):
    box(p, "Twig" if v else "PaleAlloy", 0, 0, 1.4, 4.0, 2.2, 1.0)
    for s in (-1, 1):
        with lay(p, xf(0.4, s * 1.2, 0.9, 0, 90, 0)):
            torus(p, "DeepAlloy", 0.8, 0.12, 0, 0, 0, n=10)
    box(p, "DeepAlloy", -2.8, 0, 1.6, 2.0, 0.2, 0.2)
    box(p, "PaleAlloy", 0.6, 0.2, 2.5, 1.4, 1.4, 1.2, rz=12)
    if v:
        box(p, "RaiderRust", -0.8, -0.3, 2.3, 1.2, 1.2, 0.8, rz=-20)


@family("toolkit", ["base", "unmooring", "lockdown"], 2, tier=2, rule="Wall", align="Wall", interact="Loot")
def f_toolkit(p, v):
    box(p, "DeepAlloy", 0, 0, 0.45, 1.8, 0.9, 0.9)
    box(p, "SunGold", 0, 0, 0.95, 0.6, 0.12, 0.12)
    if v:
        with lay(p, xf(1.8, 0.4, 0.55, 0, 90, 0)):
            cyl(p, "AzureDim", 0.55, 0.55, -0.4, 0.4, n=10)
            cyl(p, "DeepAlloy", 0.25, 0.25, -0.5, 0.5, n=6)


# ==========================================================================
# SIEGE -- raiders dug in on the decks
# ==========================================================================

@family("raider_tent", ["siege"], 4, interact="Loot", rule="Open", scale=(900, 1150), weight=2)
def f_raider_tent(p, v):
    if v in (0, 1):     # A-frames, short and long
        L = 8.0 if v == 0 else 13.0
        box(p, "RaiderRust", 0, -2.2, 2.6, L, 0.4, 6.4, rx=-35)
        box(p, "RaiderRust" if v == 0 else "Char", 0, 2.2, 2.6, L, 0.4, 6.4, rx=35)
        box(p, "DeepAlloy", 0, 0, 5.3, L + 0.6, 0.5, 0.5)
        box(p, "Char", L / 2 + 0.05, 0, 1.6, 0.2, 2.2, 3.0)
        for sx in (-L / 2 - 0.2, L / 2 + 0.2):
            cyl(p, "DeepAlloy", 0.3, 0.3, 0, 5.6, sx, 0, n=4)
    elif v == 2:        # a lean-to against whatever is behind it
        box(p, "RaiderRust", 0, 0.3, 2.3, 9.0, 0.35, 5.6, rx=-55)
        for sx in (-4.2, 0, 4.2):
            cyl(p, "Twig", 0.25, 0.25, 0, 4.4, sx, -1.4, n=4)
            box(p, "Twig", sx, 0.6, 2.1, 0.35, 4.4, 0.35, rx=-55)
        box(p, "Char", 0, -0.8, 0.06, 8.0, 3.5, 0.1)
    else:               # a round yurt with a smoke-hole
        cyl(p, "RaiderRust", 4.2, 4.0, 0, 3.0)
        cyl(p, "Char", 4.6, 0.6, 3.0, 5.6)
        cyl(p, "DeepAlloy", 0.7, 0.3, 5.6, 7.0)
        box(p, "Twig", 4.0, 0, 1.2, 0.6, 2.0, 2.4)


@family("stake_wall", ["siege"], 3, interact="Destroy", rule="Any", align="Wall", weight=2)
def f_stake_wall(p, v):
    n = (5, 7, 4)[v]
    r = R("stakes", v)
    for k in range(n):
        x = (k - (n - 1) / 2) * 2.0
        with lay(p, xf(x, 0, 0, 0, r.uniform(-24, -10), r.uniform(-6, 6))):
            cyl(p, "Twig", 0.35, 0.0, 0, r.uniform(3.8, 5.2), n=4, rot=45)
    box(p, "Bark", 0, 0.6, 1.2, n * 2.0, 0.4, 0.4)
    if v != 2:
        box(p, "Bark", 0, 0.9, 2.4, n * 2.0, 0.4, 0.4)


@family("scrap_wall", ["siege", "unmooring"], 3, interact="Destroy", rule="Any", align="Wall", weight=2)
def f_scrap_wall(p, v):
    r = R("scrap wall", v)
    x = -4.5
    for k in range(4 + v):
        w = r.uniform(1.8, 3.0)
        h = r.uniform(2.2, 3.8)
        box(p, r.choice(("RaiderRust", "DeepAlloy", "PaleAlloy")), x + w / 2, r.uniform(-0.2, 0.2), h / 2,
            w, 0.35, h, rz=r.uniform(-8, 8), ry=r.uniform(-6, 6))
        x += w * 0.85
    for k in range(3):
        cyl(p, "DeepAlloy", 0.25, 0.25, 0, 3.4, -4 + k * 4.0, -0.5, n=4)


@family("barricade", ["siege"], 3, interact="Destroy", rule="Any", align="Wall", weight=2)
def f_barricade(p, v):
    box(p, "PaleAlloy", -3, 0, 1.3, 3, 3, 2.6)
    box(p, "PaleAlloy", 3, 0, 1.3, 3, 3, 2.6, rz=8)
    box(p, "RaiderRust", 0, 0.4, 2.8, 9, 0.5, 1.2, rx=10)
    if v >= 1:
        box(p, "Twig", 0, -0.8, 1.0, 8, 0.3, 1.8, rx=-20)
    if v == 2:
        for k in range(3):
            with lay(p, xf(-3 + 3 * k, -1.2, 0.6, 0, 0, -55)):
                cyl(p, "Twig", 0.25, 0.0, 0, 3.2, n=4)


@family("barrels", ["siege"], 3, interact="Breakable", rule="Wall")
def f_barrels(p, v):
    spots = [[(0, 0, 0)], [(0, 0, 0), (1.9, 0.4, 0)], [(0, 0, 0), (1.9, 0.4, 0), (0.9, 1.7, 0), (1.0, 0.7, 2.2)]][v]
    for (x, y, z) in spots:
        cyl(p, "RaiderRust", 0.9, 0.9, z, z + 2.1, x, y)
        for hz in (0.35, 1.75):
            cyl(p, "DeepAlloy", 0.95, 0.95, z + hz, z + hz + 0.15, x, y)


@family("raider_crates", ["siege"], 3, interact="Loot", rule="Wall", align="Wall")
def f_raider_crates(p, v):
    r = R("raider crates", v)
    for k in range(v + 1):
        s = r.uniform(2.2, 3.0)
        x = k * 2.6
        rz = r.uniform(-15, 15)
        box(p, "Twig", x, 0, s / 2, s, s * 0.8, s, rz=rz)
        box(p, "Bark", x, 0, s / 2, s + 0.1, s * 0.8 + 0.1, 0.3, rz=rz)
        box(p, "Bark", x, 0, s / 2, 0.3, s * 0.8 + 0.1, s + 0.1, rz=rz)


@family("loot_pile", ["siege", "stormhawk"], 3, interact="Loot", rule="Open", weight=1)
def f_loot_pile(p, v):
    r = R("loot", v)
    if v != 2:
        box(p, "Twig", 0, 0, 0.7, 3.4, 2.2, 1.4)
        box(p, "DeepAlloy", 0, 0, 0.7, 3.5, 2.3, 0.3)
    for k in range(9 + 4 * v):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0.6 if v == 2 else 1.8, 3.2)
        crystal(p, "SunGold", math.cos(a) * d, math.sin(a) * d, 0.25, r.uniform(0.3, 0.6), 0.5, 0.25, n=5)
    crystal(p, "SunGold" if v != 1 else "SkyGlass", 0, 0, 1.9 if v != 2 else 0.9, 0.9, 1.0, 0.5, n=6)


@family("campfire", ["siege", "rime"], 2, anim="Flicker", interact="Lightable", rule="Open")
def f_campfire(p, v):
    blot(p, "Char", 0, 0, 2.6, "campfire char %d" % v, h=0.04)
    for k in range(8):
        a = math.radians(45 * k)
        box(p, "HullSlate", math.cos(a) * 2.2, math.sin(a) * 2.2, 0.35, 0.9, 0.7, 0.7, rz=45 * k)
    for k in range(3):
        box(p, "Bark", 0, 0, 0.35 + 0.1 * k, 3.2, 0.5, 0.5, rz=60 * k)
    for k, (a, h) in enumerate(((0.3, 2.2), (2.3, 1.5), (4.2, 1.9), (5.5, 1.2))):
        crystal(p, "EmberGlow", math.cos(a) * 0.5, math.sin(a) * 0.5, 0.5, 0.45, h, 0.01, n=4, rz=30 * k)
    if v:   # a cookpot on a tripod
        for k in range(3):
            a = math.radians(120 * k)
            with lay(p, xf(math.cos(a) * 1.6, math.sin(a) * 1.6, 0, math.degrees(a) + 180, 0, 25)):
                cyl(p, "DeepAlloy", 0.15, 0.12, 0, 4.2, n=4)
        cyl(p, "DeepAlloy", 0.9, 1.1, 2.0, 3.2, n=8)


@family("bonfire", ["siege"], 1, anim="Flicker", interact="Hazard", rule="Open", weight=1)
def f_bonfire(p, v):
    f_campfire(p, 0)
    for k in range(4):
        lump(p, "Smoke", [(1.6 + k * 0.5, 0), (1.9 + k * 0.6, 1.4 + k * 0.3), (0, 2.6 + k * 0.5)], n=7,
             seed="smoke %d" % k, cx=0.9 * k, cy=0.2 * k, cz=3.0 + k * 3.0)


@family("raider_banner", ["siege"], 3, anim="Sway", tier=2, rule="Any")
def f_raider_banner(p, v):
    h = (11, 9, 13)[v]
    cyl(p, "DeepAlloy", 0.3, 0.25, 0, h, n=6)
    box(p, "DeepAlloy", 1.6, 0, h - 0.5, 3.6, 0.3, 0.3)
    box(p, "RaiderRust" if v != 1 else "Char", 1.6, 0, h - 3.0, 3.2, 0.2, 4.6)
    box(p, "RaiderRust", 2.6, 0, h - 5.8, 1.2, 0.2, 1.2)
    if v == 2:
        lump(p, "Bone", [(0.5, h), (0.6, h + 0.6), (0, h + 1.1)], n=6, seed="pike skull")
    else:
        crystal(p, "Bone", 0, 0, h + 0.4, 0.5, 0.8, 0.3)


@family("trophy_pike", ["siege"], 2, tier=2, rule="Any")
def f_trophy_pike(p, v):
    cyl(p, "Twig", 0.25, 0.2, 0, 6.5, n=5)
    if v == 0:
        lump(p, "PaleAlloy", [(0.9, 6.4), (1.0, 7.1), (0.8, 7.8), (0, 8.0)], n=7, seed="helm", jitter=0.05)
        box(p, "SunGold", 0, 0, 7.2, 2.2, 0.25, 0.25)
    else:
        lump(p, "Bone", [(0.7, 6.4), (0.8, 7.0), (0, 7.6)], n=7, seed="skull pike")
        box(p, "RaiderRust", 0.3, 0, 5.4, 0.2, 1.4, 1.8)


@family("ballista", ["siege"], 2, interact="Use", rule="Wall", weight=1)
def f_ballista(p, v):
    box(p, "DeepAlloy", 0, 0, 0.6, 3.2, 3.2, 1.2)
    cyl(p, "DeepAlloy", 0.6, 0.5, 1.2, 2.6, n=6)
    if v == 0:
        with lay(p, xf(0, 0, 2.8, 0, -12, 0)):
            box(p, "Twig", 1.0, 0, 0, 5.2, 0.6, 0.6)
            box(p, "Twig", 1.4, 0, 0, 0.5, 6.4, 0.5)
            box(p, "RaiderRust", 3.8, 0, 0.1, 2.4, 0.25, 0.25)
    else:           # a scrap cannon
        with lay(p, xf(0, 0, 3.0, 0, 78, 0)):
            cyl(p, "DeepAlloy", 0.8, 0.6, 0, 4.4, n=8)
            cyl(p, "RaiderRust", 0.9, 0.9, 0.6, 1.0, n=8)
        for s in (-1, 1):
            with lay(p, xf(0, s * 1.5, 0.9, 0, 90, 90)):
                torus(p, "Twig", 0.9, 0.18, 0, 0, 0, n=10)


@family("prisoner_cage", ["siege"], 2, interact="Open", rule="Open", weight=1)
def f_cage(p, v):
    s = 1.0 if v == 0 else 1.3
    box(p, "Twig", 0, 0, 0.2, 3.4 * s, 3.4 * s, 0.4)
    box(p, "Twig", 0, 0, 4.2 * s, 3.4 * s, 3.4 * s, 0.4)
    for k in range(12):
        side, t = k // 3, (k % 3 + 0.5) / 3
        x = (-1.6 + 3.2 * t) * s if side in (0, 2) else (1.6 if side == 1 else -1.6) * s
        y = (1.6 if side == 0 else -1.6) * s if side in (0, 2) else (-1.6 + 3.2 * t) * s
        cyl(p, "DeepAlloy", 0.12, 0.12, 0.4, 4.0 * s, x, y, n=4)
    if v:
        lump(p, "Bone", [(0.5, 0.4), (0.6, 1.0), (0, 1.5)], n=6, seed="caged")


@family("scrap_heap", ["siege", "unmooring"], 3, rule="Wall", interact="Loot")
def f_scrap_heap(p, v):
    r = R("scrap heap", v)
    for k in range(6 + 2 * v):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.8 + 0.4 * v)
        box(p, r.choice(("RaiderRust", "DeepAlloy", "PaleAlloy", "Soot")), math.cos(a) * d, math.sin(a) * d,
            r.uniform(0.2, 0.9), r.uniform(0.8, 2.6), r.uniform(0.6, 1.6), r.uniform(0.2, 0.6),
            rz=r.uniform(0, 180), rx=r.uniform(-25, 25), ry=r.uniform(-25, 25))


# ==========================================================================
# LOCKDOWN -- the citadel's defences turned on everyone
# ==========================================================================

@family("sentinel_turret", ["lockdown"], 3, interact="Destroy", rule="Wall", weight=2)
def f_turret(p, v):
    cyl(p, "DeepAlloy", 2.4, 2.0, 0, 1.4)
    cyl(p, "Steel", 1.2, 1.0, 1.4, 3.4 + v * 0.8)
    top = 3.4 + v * 0.8
    lump(p, "Steel", [(2.0, top), (1.8, top + 1.2), (1.0, top + 2.1), (0, top + 2.4)], n=8, seed="turret dome", jitter=0.0)
    for s in ((0,) if v != 1 else (-0.5, 0.5)):
        box(p, "DeepAlloy", 2.4, s, top + 1.0, 3.2, 0.6, 0.6)
    crystal(p, "AlarmRed", 1.6, 0, top + 1.6, 0.35, 0.45, 0.3, n=4)
    if v == 2:
        box(p, "Hazard", 0, 0, 0.7, 5.0, 0.3, 0.5, rz=45)
        box(p, "Hazard", 0, 0, 0.7, 5.0, 0.3, 0.5, rz=-45)


@family("sentinel_pylon", ["lockdown"], 3, interact="Destroy", rule="Any")
def f_sentinel(p, v):
    cyl(p, "DeepAlloy", 1.8, 1.4, 0, 1.2, n=6)
    h = (7.5, 9.5, 6.0)[v]
    cyl(p, "Steel", 1.1, 0.7, 1.2, h, n=4, rot=45)
    crystal(p, "AlarmRed", 0, 0, h + 1.1, 0.9, 1.3, 1.0, n=4)
    if v == 1:
        torus(p, "AlarmDim", 1.4, 0.15, 0, 0, h * 0.6, n=10)


@family("laser_fence", ["lockdown"], 2, anim="Pulse", interact="Hazard", rule="Any", align="Wall", weight=2)
def f_laser_fence(p, v):
    L = 4.0 if v == 0 else 6.0
    for x in (-L, L):
        cyl(p, "DeepAlloy", 0.7, 0.5, 0, 5, x, 0, n=4, rot=45)
        crystal(p, "AlarmRed", x, 0, 5.4, 0.4, 0.6, 0.3, n=4)
    for z in (1.2, 2.6, 4.0):
        box(p, "AlarmRed", 0, 0, z, 2 * L - 0.4, 0.12, 0.12)


@family("alarm_post", ["lockdown"], 2, anim="Strobe", rule="Wall", tier=2)
def f_alarm_post(p, v):
    cyl(p, "DeepAlloy", 0.9, 0.7, 0, 0.6, n=6)
    h = 7.5 if v == 0 else 5.0
    cyl(p, "Steel", 0.35, 0.3, 0.6, h, n=6)
    cyl(p, "DeepAlloy", 0.8, 0.8, h, h + 0.3, n=6)
    crystal(p, "AlarmRed", 0, 0, h + 1.1, 0.7, 1.0, 0.8, n=6)
    cyl(p, "DeepAlloy", 0.8, 0.2, h + 2.1, h + 2.7, n=6)


@family("console", ["lockdown", "base"], 3, interact="Override", rule="Wall", align="Wall", weight=1)
def f_console(p, v):
    box(p, "DeepAlloy", 0, 0, 0.6, 2.4 + v * 0.8, 1.6, 1.2)
    box(p, "Steel", 0, 0, 1.6, 2.2 + v * 0.8, 1.2, 0.8, rx=-25)
    box(p, "AlarmDim", 0, -0.35, 2.05, 1.8 + v * 0.8, 0.1, 0.6, rx=-25)
    for k in range(3 + v):
        box(p, "AlarmRed", -0.6 + 0.6 * k, 0.4, 1.3, 0.3, 0.3, 0.15)
    if v == 2:
        box(p, "Steel", 0, 0.6, 3.2, 3.8, 0.3, 2.2)
        box(p, "AlarmDim", 0, 0.42, 3.2, 3.4, 0.05, 1.8)


@family("barrier_block", ["lockdown"], 3, rule="Any", align="Wall", weight=3)
def f_barrier(p, v):
    L = (4.0, 6.0, 3.0)[v]
    verts = [(-L / 2, -0.9, 0), (L / 2, -0.9, 0), (L / 2, 0.9, 0), (-L / 2, 0.9, 0),
             (-L / 2, -0.4, 2.0), (L / 2, -0.4, 2.0), (L / 2, 0.4, 2.0), (-L / 2, 0.4, 2.0)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    add_faces(p, verts, faces, ["Steel"] * 6)
    box(p, "Hazard", 0, 0, 1.2, L + 0.02, 1.25, 0.35)
    if v == 2:
        crystal(p, "AlarmRed", 0, 0, 2.2, 0.3, 0.4, 0.2, n=4)


@family("security_crate", ["lockdown"], 2, interact="Loot", rule="Wall", align="Wall")
def f_security_crate(p, v):
    box(p, "Steel", 0, 0, 1.3, 3.4, 2.4, 2.6)
    box(p, "DeepAlloy", 0, 0, 1.3, 3.5, 2.5, 0.4)
    box(p, "AlarmDim", 0, -1.22, 1.9, 0.8, 0.05, 0.5)
    if v:
        box(p, "Steel", 0.3, 0.1, 3.4, 3.0, 2.0, 1.6, rz=8)
        box(p, "Hazard", 0.3, 0.1, 3.4, 3.05, 2.05, 0.3, rz=8)


@family("cable_spool", ["lockdown", "unmooring"], 2, tier=2, rule="Any")
def f_cable_spool(p, v):
    with lay(p, xf(0, 0, 1.4, 0, 90, 0)):
        cyl(p, "Twig" if v else "DeepAlloy", 1.4, 1.4, -1.0, -0.8, n=10)
        cyl(p, "Twig" if v else "DeepAlloy", 1.4, 1.4, 0.8, 1.0, n=10)
        cyl(p, "AlarmDim" if not v else "Soot", 1.0, 1.0, -0.8, 0.8, n=10)


@family("floor_emitter", ["lockdown"], 2, anim="Pulse", interact="Hazard", rule="Open", tier=1)
def f_emitter(p, v):
    cyl(p, "DeepAlloy", 1.8 + v, 1.6 + v, 0, 0.3, n=10)
    torus(p, "AlarmRed", 1.2 + v * 0.8, 0.12, 0, 0, 0.32, n=12)
    cyl(p, "AlarmDim", 0.5, 0.4, 0.3, 0.7, n=6)


@family("searchlight", ["lockdown"], 2, anim="Spin", rule="Wall", weight=1)
def f_searchlight(p, v):
    for k in range(3):
        a = math.radians(120 * k)
        with lay(p, xf(math.cos(a) * 1.0, math.sin(a) * 1.0, 0, math.degrees(a) + 180, 0, 18)):
            cyl(p, "DeepAlloy", 0.18, 0.15, 0, 4.2, n=4)
    with lay(p, xf(0, 0, 4.4, 0, 70 - v * 20, 0)):
        cyl(p, "Steel", 0.9, 1.2, 0, 1.8, n=8)
        cyl(p, "AlarmRed" if v else "Snow", 1.15, 1.15, 1.8, 1.95, n=8)


@family("drone", ["lockdown"], 2, anim="Hover", interact="Destroy", air=True)
def f_drone(p, v):
    lump(p, "DeepAlloy", [(0.5, -0.9), (1.1, -0.3), (1.1, 0.3), (0.5, 0.9)], n=8, seed="drone", jitter=0.0)
    if v == 0:
        torus(p, "Steel", 1.4, 0.15, 0, 0, 0, n=12)
    else:
        for s in (-1, 1):
            box(p, "Steel", 0, s * 1.4, 0, 1.6, 0.6, 0.12)
    crystal(p, "AlarmRed", 1.0, 0, 0, 0.3, 0.35, 0.3, n=4)


# ==========================================================================
# STORMHAWK -- a raptor's hunting ground
# ==========================================================================

@family("nest", ["stormhawk"], 2, interact="Event", rule="Open", scale=(1500, 2100), weight=1)
def f_nest(p, v):
    Rr = 7.0
    for k in range(20):
        a = 18 * k
        box(p, "Twig", math.cos(math.radians(a)) * Rr, math.sin(math.radians(a)) * Rr, 1.0 + (k % 3) * 0.35,
            7.5, 0.6, 0.6, rz=a + 90 + (k % 3 - 1) * 14, rx=(k % 2) * 16 - 8)
    for k in range(12):
        a = 30 * k + 9
        box(p, "Bark", math.cos(math.radians(a)) * (Rr + 1.2), math.sin(math.radians(a)) * (Rr + 1.2), 0.5,
            6.0, 0.5, 0.5, rz=a + 70, rx=10)
    cyl(p, "Twig", Rr - 1.5, Rr + 0.5, 0.0, 1.2, n=10)
    for k in range(3 - v):
        a = math.radians(120 * k + 20)
        lump(p, "Bone", [(0.8, 1.2), (1.0, 1.9), (0.6, 2.7), (0, 3.0)], n=7, seed="egg %d" % k, jitter=0.05,
             cx=math.cos(a) * 1.5, cy=math.sin(a) * 1.5)
    if v:
        for k in range(4):
            box(p, "DeepAlloy", math.cos(k) * 2.5, math.sin(k) * 2.5, 1.3, 4.5, 0.8, 0.12, rz=k * 50)


@family("bone_pile", ["stormhawk"], 3, tier=2, interact="Loot", rule="Any")
def f_bones(p, v):
    r = R("bones", v)
    for k in range(5 + 2 * v):
        box(p, "Bone", r.uniform(-2, 2), r.uniform(-1.5, 1.5), 0.25, r.uniform(1.8, 3.4), 0.4, 0.4,
            rz=r.uniform(0, 180))
    if v != 1:
        lump(p, "Bone", [(0.9, 0), (1.1, 0.8), (0.8, 1.4), (0, 1.6)], n=7, seed="skull %d" % v, jitter=0.12,
             cx=1.4, cy=-0.8)
    if v == 2:
        for k in range(5):      # a ribcage
            with lay(p, xf(-1.5 + k * 0.7, 0, 0.2, 0, 90, 0)):
                torus(p, "Bone", 1.1, 0.12, 0, 0, 0, n=8)


@family("egg_shells", ["stormhawk"], 2, tier=2, interact="Pickup", rule="Any")
def f_eggshells(p, v):
    for k, (x, y) in enumerate(((0, 0), (1.3, 0.6), (0.4, 1.4))[: 2 + v]):
        lump(p, "Bone", [(0.9, 0), (0.95, 0.5), (0.7, 0.9)], n=7, seed="shell %d %d" % (v, k), jitter=0.25,
             cx=x, cy=y)


@family("fallen_feather", ["stormhawk"], 4, tier=2, interact="Pickup", rule="Any")
def f_fallen_feather(p, v):
    L = (6.0, 4.5, 7.5, 5.0)[v]
    box(p, "DeepAlloy" if v != 3 else "Snow", 0, 0, 0.08, L, 1.0, 0.14)
    box(p, "SunGold", L * 0.35, 0, 0.1, 1.8, 1.05, 0.14)
    if v % 2 == 0:
        box(p, "DeepAlloy", 0.5, 1.2, 0.08, L * 0.66, 0.8, 0.14, rz=18)


@family("storm_feather", ["stormhawk"], 2, anim="Tumble", interact="Pickup", air=True, tier=2)
def f_storm_feather(p, v):
    box(p, "DeepAlloy", 0, 0, 0, 5.5 + v, 0.9, 0.12)
    box(p, "SunGold", 1.8, 0, 0.02, 1.6, 0.95, 0.12)


@family("smashed_crate", ["stormhawk", "unmooring", "reclaimed"], 2, tier=2, interact="Loot", rule="Any")
def f_smashed_crate(p, v):
    r = R("smashed", v)
    for k in range(6):
        box(p, "PaleAlloy" if k % 2 else "DeepAlloy", r.uniform(-1.6, 1.6), r.uniform(-1.4, 1.4), 0.2,
            r.uniform(1.0, 3.0), r.uniform(0.3, 1.2), 0.3, rz=r.uniform(0, 180), rx=r.uniform(-15, 15))
    if v:
        box(p, "PaleAlloy", 0, 0, 1.0, 2.6, 2.6, 2.0, rz=20, ry=18)


@family("lightning_rod", ["stormhawk"], 2, rule="Wall", weight=1)
def f_lightning_rod(p, v):
    cyl(p, "DeepAlloy", 1.0, 0.8, 0, 0.8, n=6)
    h = 12.0 if v == 0 else 9.0
    cyl(p, "SunGold", 0.25, 0.1, 0.8, h, n=5)
    for z in (h * 0.5, h * 0.7):
        torus(p, "AzureNeon", 0.7, 0.12, 0, 0, z, n=8)
    if v:
        box(p, "Soot", 0, 0, 0.04, 6.0, 1.0, 0.06, rz=30)


@family("perch", ["stormhawk"], 2, rule="Open", weight=1)
def f_perch(p, v):
    cyl(p, "Bark", 0.8, 0.5, 0, 7.0 + v * 2, n=6)
    for k, (a, z, L) in enumerate(((20, 5.5, 4.0), (160, 6.5, 3.2), (260, 4.2, 3.5))[: 2 + v]):
        with lay(p, xf(0, 0, z, a, 0, 60)):
            cyl(p, "Bark", 0.3, 0.12, 0, L, n=5)
    for k in range(3):
        box(p, "Soot", 0.4, 0, 3 + k, 0.1, 0.9, 0.3)          # talon gouges in the wood


# ==========================================================================
# RIME -- frozen at altitude
# ==========================================================================

@family("snow_drift", ["rime"], 5, tier=2, rule="Lee", align="Wall", scale=(900, 2000), weight=6)
def f_drift(p, v):
    sx = (2.0, 1.4, 2.6, 1.7, 3.0)[v]
    h = (2.6, 2.0, 3.2, 1.6, 2.4)[v]
    lump(p, "Snow", [(3.0, 0), (2.6, h * 0.42), (1.6, h * 0.8), (0, h)], n=8, seed="drift %d" % v, jitter=0.28, sx=sx)
    if v == 4:
        lump(p, "Snow", [(1.6, 0), (1.3, 1.0), (0, 1.6)], n=7, seed="drift tail", cx=4.0, cy=1.0)


@family("ice_spikes", ["rime"], 5, interact="Break", rule="Any", scale=(1000, 2300))
def f_ice(p, v):
    r = R("ice", v)
    n = (5, 3, 7, 4, 6)[v]
    for k in range(n):
        a = r.uniform(0, 2 * math.pi)
        d = 0 if k == 0 else r.uniform(0.8, 2.2)
        lean = r.uniform(-16, 16) if k else 0.0
        with lay(p, xf(math.cos(a) * d, math.sin(a) * d, 0, r.uniform(0, 72), lean, lean * 0.6)):
            crystal(p, "Ice" if k % 3 else "SkyGlass", 0, 0, 0, r.uniform(0.5, 1.1) * (1.4 if k == 0 else 1.0),
                    r.uniform(2.5, 6.0) * (1.6 if k == 0 else 1.0), 0.01, n=5)


@family("frost_crystals", ["rime"], 3, tier=2, interact="Break", rule="Wall")
def f_frost(p, v):
    r = R("frost", v)
    for k in range(4 + v):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.5)
        with lay(p, xf(math.cos(a) * d, math.sin(a) * d, 0, r.uniform(0, 72), r.uniform(-30, 30), 0)):
            crystal(p, "Ice", 0, 0, 0, r.uniform(0.3, 0.6), r.uniform(1.0, 2.6), 0.01, n=4)


@family("frozen_figure", ["rime"], 2, interact="Break", rule="Open", weight=1)
def f_frozen(p, v):
    lump(p, "Ice", [(2.2, 0), (2.4, 2.0), (1.8, 4.2), (0.9, 5.4), (0, 5.8)], n=7, seed="ice block %d" % v, jitter=0.15)
    if v == 0:
        box(p, "DeepAlloy", 0.9, 1.9, 4.6, 0.8, 0.8, 0.9)
        box(p, "DeepAlloy", -1.7, 1.2, 3.4, 0.5, 0.5, 2.2, rx=30, ry=-20)
        crystal(p, "SunGold", 1.9, -1.2, 2.2, 0.3, 0.5, 0.3)
    else:
        box(p, "RaiderRust", 1.6, -1.6, 3.8, 0.6, 2.6, 0.6, rx=-35)     # a raider's arm, reaching
        lump(p, "Bone", [(0.5, 4.8), (0.55, 5.3), (0, 5.8)], n=6, seed="frozen head", cx=-0.4, cy=1.9)


@family("frozen_crate", ["rime"], 2, interact="Break", rule="Wall", align="Wall")
def f_frozen_crate(p, v):
    box(p, "PaleAlloy", 0, 0, 1.4, 2.8, 2.8, 2.8, rz=10)
    lump(p, "Ice", [(2.4, 0), (2.4, 2.2), (1.8, 3.4), (0, 3.8)], n=7, seed="crate ice %d" % v, jitter=0.2, sx=1.1)
    if v:
        crystal(p, "Ice", 1.8, 0.6, 0, 0.6, 3.0, 0.01, n=5)


@family("ice_boulder", ["rime"], 3, rule="Any", scale=(900, 1800))
def f_ice_boulder(p, v):
    lump(p, "Ice" if v != 1 else "FrostDeep", [(1.8, 0), (2.2, 1.0), (1.6, 2.2), (0, 2.6)], n=7,
         seed="ice boulder %d" % v, jitter=0.3)
    lump(p, "Snow", [(1.3, 2.1), (1.0, 2.5), (0, 2.8)], n=7, seed="boulder cap %d" % v)


@family("icicle_pile", ["rime"], 2, tier=2, interact="Break", rule="Wall")
def f_icicle_pile(p, v):
    r = R("icicle pile", v)
    for k in range(6 + 3 * v):
        a = r.uniform(0, 2 * math.pi)
        with lay(p, xf(math.cos(a) * r.uniform(0, 1.8), math.sin(a) * r.uniform(0, 1.8), 0.3, r.uniform(0, 180), 90, 0)):
            crystal(p, "Ice", 0, 0, 0, 0.3, r.uniform(1.2, 2.6), 0.3, n=4)


@family("warming_brazier", ["rime"], 2, anim="Flicker", interact="Lightable", rule="Open", weight=2)
def f_warm(p, v):
    cyl(p, "DeepAlloy", 1.2, 0.9, 0, 0.5, n=8)
    cyl(p, "FrostDeep", 0.4, 0.4, 0.5, 2.6, n=6)
    cyl(p, "DeepAlloy", 1.0, 1.6, 2.6, 3.4, n=8)
    for k, (a, h) in enumerate(((0.3, 1.8), (2.3, 1.3), (4.2, 1.6))):
        crystal(p, "EmberGlow", math.cos(a) * 0.5, math.sin(a) * 0.5, 3.3, 0.45, h, 0.01, n=4)
    if v:
        blot(p, "Frost", 0, 0, 3.0, "brazier thaw", h=0.03)


# ==========================================================================
# RECLAIMED -- the green took the citadel back
# ==========================================================================

@family("moss_mound", ["reclaimed"], 5, tier=2, rule="Wall", scale=(700, 1500), weight=6)
def f_moss(p, v):
    seed = "moss %d" % v
    sx = (1.3, 1.0, 1.6, 1.2, 2.0)[v]
    lump(p, "Moss", [(3.2, 0), (3.0, 0.4), (2.0, 0.9), (0, 1.1)], n=9, seed=seed, jitter=0.3, sx=sx)
    lump(p, "MossLight", [(1.6, 0.5), (1.4, 1.1), (0, 1.5)], n=7, seed=seed + " top", jitter=0.3, cx=0.8, cy=0.3)
    if v % 2 == 0:
        lump(p, "MossLight", [(1.0, 0.2), (0.8, 0.7), (0, 0.9)], n=6, seed=seed + " side", jitter=0.3, cx=-2.4, cy=-0.6)
    if v == 3:
        for k in range(4):
            crystal(p, "SunGold", math.cos(k * 1.7) * 1.8, math.sin(k * 1.7) * 1.2, 1.0, 0.2, 0.2, 0.1, n=5)


@family("bush", ["reclaimed"], 5, anim="Sway", tier=1, interact="Cut", rule="Wall", scale=(900, 1800), weight=4)
def f_bush(p, v):
    r = R("bush", v)
    lobes = (4, 3, 6, 5, 2)[v]
    for k in range(lobes):
        a = r.uniform(0, 2 * math.pi)
        d = 0 if k == 0 else r.uniform(0.9, 1.8)
        rr = r.uniform(1.2, 1.9)
        lump(p, "Moss" if k % 2 else "Verdure", [(rr * 0.6, 0), (rr, rr * 0.7), (rr * 0.8, rr * 1.4), (0, rr * 1.7)],
             n=7, seed="bush %d %d" % (v, k), jitter=0.2, cx=math.cos(a) * d, cy=math.sin(a) * d,
             cz=0 if k == 0 else r.uniform(0, 0.6))
    if v == 3:
        for k in range(6):
            crystal(p, "CitadelViolet", r.uniform(-1.5, 1.5), r.uniform(-1.5, 1.5), r.uniform(1.8, 2.8), 0.25, 0.2, 0.15, n=5)


@family("fern", ["reclaimed"], 3, anim="Sway", tier=2, rule="Wall")
def f_fern(p, v):
    for k in range(7 + 2 * v):
        with lay(p, xf(0, 0, 0.2, (360 / (7 + 2 * v)) * k)):
            box(p, "MossLight" if k % 2 else "Verdure", 1.4 + 0.3 * v, 0, 0.9, 3.0 + 0.6 * v, 0.5, 0.12, ry=-38 + 6 * v)


@family("flowers", ["reclaimed", "base"], 4, anim="Sway", tier=2, interact="Pickup", rule="Open")
def f_flowers(p, v):
    r = R("flowers", v)
    blot(p, "Moss", 0, 0, 2.0, "flower bed %d" % v, h=0.1)
    colours = [("SunGold", "Snow"), ("CitadelViolet", "Snow"), ("SunGold", "CitadelViolet"), ("AzureNeon", "Snow")][v]
    for k in range(10):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.8)
        x, y = math.cos(a) * d, math.sin(a) * d
        cyl(p, "Verdure", 0.08, 0.06, 0.1, 0.9, x, y, n=4)
        crystal(p, colours[k % 2], x, y, 1.0, 0.3, 0.2, 0.15, n=5)


@family("sapling", ["reclaimed"], 3, anim="Sway", interact="Cut", rule="Open", scale=(900, 1700), weight=2)
def f_sapling(p, v):
    h = (5.5, 7.0, 4.5)[v]
    cyl(p, "Bark", 0.6, 0.35, 0, h, n=6)
    box(p, "Bark", 0.8, 0, h * 0.76, 2.0, 0.3, 0.3, ry=-40)
    lump(p, "Verdure", [(1.8, h - 0.9), (2.6 + v * 0.3, h + 0.5), (2.0, h + 2.1), (0, h + 2.9)], n=8,
         seed="sapling crown %d" % v, jitter=0.2)
    lump(p, "Moss", [(1.2, h - 0.3), (1.6, h + 0.5), (0, h + 1.5)], n=7, seed="sapling side %d" % v, jitter=0.2,
         cx=1.6, cy=0.4)
    if v == 2:
        for k in range(5):
            crystal(p, "SunGold", math.cos(k * 1.3) * 2.0, math.sin(k * 1.3) * 2.0, h + 1.0, 0.25, 0.25, 0.2, n=5)


@family("mushrooms", ["reclaimed"], 3, tier=2, interact="Harvest", rule="Base")
def f_mushrooms(p, v):
    sets = [((0, 0, 1.6, 1.0), (1.1, 0.5, 1.0, 0.6), (-0.8, 0.9, 1.3, 0.7), (0.3, -1.0, 0.8, 0.5)),
            ((0, 0, 2.4, 1.4), (1.6, 0.3, 1.2, 0.7)),
            ((0, 0, 0.9, 0.5), (0.7, 0.4, 0.7, 0.4), (-0.6, 0.5, 1.1, 0.6), (0.2, -0.7, 0.6, 0.35), (-0.9, -0.4, 0.8, 0.45))][v]
    for k, (x, y, h, rr) in enumerate(sets):
        cyl(p, "Bone", rr * 0.3, rr * 0.25, 0, h, x, y, n=6)
        lump(p, ("Snow", "CitadelViolet", "SunGold")[(k + v) % 3], [(rr, h), (rr * 0.8, h + rr * 0.4), (0, h + rr * 0.6)],
             n=7, seed="cap %d %d" % (v, k), jitter=0.1, cx=x, cy=y)


@family("fallen_log", ["reclaimed"], 2, rule="Open", align="Random", weight=1)
def f_log(p, v):
    with lay(p, xf(0, 0, 0.9, 0, 90, 0)):
        cyl(p, "Bark", 0.9, 0.75, -4.0 - v, 4.0 + v, n=7)
    lump(p, "Moss", [(1.2, 1.4), (1.0, 1.9), (0, 2.1)], n=7, seed="log moss %d" % v, sx=2.0)
    if v:
        with lay(p, xf(1.5, 0.6, 1.3, 40, 0, 50)):
            cyl(p, "Bark", 0.3, 0.1, 0, 2.2, n=5)


@family("mossy_rock", ["reclaimed", "stormhawk"], 3, rule="Any", scale=(800, 1800))
def f_rock(p, v):
    lump(p, "HullSlate", [(1.8, 0), (2.1, 0.9), (1.5, 2.0), (0, 2.4)], n=7, seed="rock %d" % v, jitter=0.35,
         sx=(1.0, 1.4, 0.9)[v])
    lump(p, "Moss", [(1.4, 1.8), (1.0, 2.3), (0, 2.6)], n=7, seed="rock moss %d" % v, jitter=0.3)


@family("grass_tuft", ["reclaimed"], 4, anim="Sway", tier=2, rule="Any")
def f_grass(p, v):
    r = R("grass", v)
    for k in range(9 + 3 * v):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.2 + 0.3 * v)
        with lay(p, xf(math.cos(a) * d, math.sin(a) * d, 0, r.uniform(0, 180), r.uniform(-20, 20), r.uniform(-20, 20))):
            box(p, r.choice(("Verdure", "MossLight", "Moss")), 0, 0, 0.8 + v * 0.2, 0.25, 0.08, 1.6 + v * 0.4)


@family("overgrown_crate", ["reclaimed"], 2, interact="Loot", rule="Wall", align="Wall")
def f_overgrown_crate(p, v):
    box(p, "PaleAlloy", 0, 0, 1.4, 2.8, 2.8, 2.8, rz=8)
    lump(p, "Moss", [(1.8, 2.6), (1.6, 3.0), (0, 3.4)], n=7, seed="crate moss %d" % v, sx=1.2)
    for k in range(4 + 2 * v):
        box(p, "Verdure", math.cos(k) * 1.45, math.sin(k) * 1.45, 1.4, 0.3, 0.3, 2.8, rz=k * 30)


@family("stump", ["reclaimed"], 2, rule="Open")
def f_stump(p, v):
    cyl(p, "Bark", 1.4 + v * 0.5, 1.1 + v * 0.4, 0, 1.4 + v, n=7)
    cyl(p, "Twig", 1.1 + v * 0.4, 0.9 + v * 0.3, 1.4 + v, 1.5 + v, n=7)
    for k in range(4):
        with lay(p, xf(0, 0, 0.3, 90 * k + 20, 0, 70)):
            cyl(p, "Bark", 0.4, 0.1, 0, 2.2, n=5)


# ==========================================================================
# AETHER SURGE -- crystal growth erupting through the citadel
# ==========================================================================

@family("aether_cluster", ["aether_surge"], 6, anim="Pulse", interact="Harvest", rule="Any", scale=(900, 3200), weight=6)
def f_aether(p, v):
    r = R("aether", v)
    n, tall, spread, outward = [(6, 2.2, 2.2, 1.0), (9, 1.3, 3.0, 1.6), (4, 3.4, 1.6, 0.6), (7, 1.8, 2.6, 1.2),
                                (3, 4.0, 1.2, 0.4), (11, 1.0, 3.4, 1.8)][v]
    for k in range(n):
        a = r.uniform(0, 2 * math.pi)
        d = 0 if k == 0 else r.uniform(0.6, spread)
        tilt = outward * (d / spread) * 28
        with lay(p, xf(math.cos(a) * d, math.sin(a) * d, 0, math.degrees(a), 0, tilt)):
            crystal(p, "AetherBloom" if k % 2 == 0 else "SkyGlass", 0, 0, 0,
                    r.uniform(0.6, 1.1) * (1.5 if k == 0 else 1.0),
                    r.uniform(2.5, 5.0) * (tall if k == 0 else 1.0), 0.01, n=5)


@family("aether_geode", ["aether_surge"], 2, anim="Pulse", interact="Harvest", rule="Open", weight=2)
def f_geode(p, v):
    blot(p, "AetherDim", 0, 0, 2.4 + v, "geode core %d" % v, h=0.12)
    for k in range(9 + 3 * v):
        a = (360 / (9 + 3 * v)) * k
        with lay(p, xf(math.cos(math.radians(a)) * (2.6 + v), math.sin(math.radians(a)) * (2.6 + v), 0, a, 0, 32)):
            crystal(p, "AetherBloom" if k % 2 else "SkyGlass", 0, 0, 0, 0.6, 2.6 + (k % 3) * 0.8, 0.01, n=5)


@family("crystal_rubble", ["aether_surge"], 3, rule="Any", tier=2)
def f_crystal_rubble(p, v):
    r = R("crystal rubble", v)
    for k in range(5 + v):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.8)
        box(p, "Pearl", math.cos(a) * d, math.sin(a) * d, 0.5, r.uniform(0.8, 1.8), r.uniform(0.7, 1.4),
            r.uniform(0.6, 1.2), rz=r.uniform(0, 90), rx=r.uniform(-15, 15))
        crystal(p, "AetherBloom", math.cos(a) * d, math.sin(a) * d, 0.9, 0.3, r.uniform(0.8, 1.8), 0.01, n=4)


@family("glow_pool", ["aether_surge"], 2, anim="Pulse", rule="Open", weight=1)
def f_glow_pool(p, v):
    blot(p, "AetherDim", 0, 0, 3.0 + v, "glow pool %d" % v, h=0.08, n=11)
    blot(p, "AetherBloom", 0.4, 0.2, 1.6 + v * 0.6, "glow pool core %d" % v, z=0.09, h=0.04, n=9)
    for k in range(5):
        a = k * 1.25
        crystal(p, "SkyGlass", math.cos(a) * (3.2 + v), math.sin(a) * (3.2 + v), 0, 0.35, 1.2, 0.01, n=4)


@family("resonator", ["aether_surge"], 2, anim="Hover", interact="Attune", rule="Open", weight=1)
def f_resonator(p, v):
    cyl(p, "Lavender", 1.6, 1.3, 0, 1.0, n=6)
    cyl(p, "Pearl", 0.5, 0.4, 1.0, 3.5, n=6)
    for k in range(3):
        a = math.radians(120 * k)
        crystal(p, "AetherBloom", math.cos(a) * 1.1, math.sin(a) * 1.1, 3.6, 0.3, 1.4, 0.3, n=4)
    crystal(p, "AetherBloom" if v else "SkyGlass", 0, 0, 5.2, 0.7, 1.4, 1.0, n=6)


@family("aether_shard", ["aether_surge"], 3, anim="Hover", interact="Harvest", air=True)
def f_aether_shard(p, v):
    crystal(p, "AetherBloom" if v != 1 else "SkyGlass", 0, 0, 0, 1.0 + v * 0.3, 3.0 + v, 2.4 + v * 0.6, n=5)
    if v == 2:
        crystal(p, "AetherBloom", 1.4, 0.4, 0.8, 0.5, 1.4, 1.0, n=5)


@family("floating_rock", ["aether_surge", "unmooring"], 2, anim="Tumble", air=True)
def f_floating_rock(p, v):
    lump(p, "Pearl" if v == 0 else "CitadelWhite", [(0, -2.6), (1.4, -1.6), (1.8, -0.2), (1.2, 0.6), (0, 0.9)], n=7,
         seed="float rock %d" % v, jitter=0.3)
    crystal(p, "AetherBloom" if v == 0 else "AzureNeon", 0, 0, 0.8, 0.4, 1.4, 0.2, n=5)


# ==========================================================================
# UNMOORING -- the anti-grav failing under the citadel
# ==========================================================================

@family("rubble", ["unmooring", "siege", "stormhawk", "reclaimed"], 5, rule="Any", scale=(800, 1400))
def f_rubble(p, v):
    r = R("rubble", v)
    n = (5, 7, 4, 9, 6)[v]
    for k in range(n):
        sx, sy, sz = r.uniform(1.2, 3.0), r.uniform(1.0, 2.4), r.uniform(0.8, 1.8)
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0, 1.8 + 0.3 * (v == 3))
        box(p, r.choice(("CitadelWhite", "CitadelWhite", "PaleAlloy")), math.cos(a) * d, math.sin(a) * d,
            sz / 2 + (0.6 if k > n // 2 else 0), sx, sy, sz, rz=r.uniform(0, 90), rx=r.uniform(-12, 12))


@family("hazard_beacon", ["unmooring"], 2, anim="Strobe", rule="Wall", tier=2)
def f_hazard_beacon(p, v):
    cyl(p, "DeepAlloy", 0.8, 0.6, 0, 0.5, n=4, rot=45)
    cyl(p, "SunGold", 0.3, 0.3, 0.5, 4.0 - v, n=4, rot=45)
    crystal(p, "EmberGlow", 0, 0, 4.6 - v, 0.5, 0.8, 0.5, n=4)
    if v:
        box(p, "SunGold", 0, 0, 0.3, 3.0, 0.3, 0.3, rz=45)


@family("stabilizer", ["unmooring"], 2, anim="Pulse", interact="Repair", rule="Open", weight=1)
def f_stabilizer(p, v):
    cyl(p, "DeepAlloy", 2.2, 1.8, 0, 1.2)
    cyl(p, "PaleAlloy", 0.8, 0.7, 1.2, 7.0 - v)
    for z in (2.6, 4.2, 5.8)[: 3 - v]:
        torus(p, "AzureDim", 1.6, 0.25, 0, 0, z, n=12)
    crystal(p, "AzureNeon" if not v else "DeepAlloy", 0, 0, 8.0 - v, 0.9, 1.6, 1.0, n=6)
    if v:
        with lay(p, xf(1.6, 0, 0.6, 0, 70, 0)):
            cyl(p, "PaleAlloy", 0.5, 0.5, 0, 3.0, n=6)


@family("broken_rail", ["unmooring", "siege"], 3, tier=2, rule="Wall", align="Wall")
def f_broken_rail(p, v):
    r = R("broken rail", v)
    for k in range(2 + v):
        with lay(p, xf(k * 3.0, 0, 0, r.uniform(-20, 20), r.uniform(-50, 50) if k else 0, 0)):
            cyl(p, "PaleAlloy", 0.25, 0.25, 0, 3.2, n=4)
    with lay(p, xf(1.5, 0, 0.3, r.uniform(-10, 10), 0, 12)):
        box(p, "PaleAlloy", 0, 0, 0, 3.0 * (1 + v), 0.3, 0.3)
    box(p, "AzureDim", 1.0, 0.8, 0.12, 2.5, 0.3, 0.2, rz=30)


@family("pillar_segment", ["unmooring", "reclaimed", "stormhawk"], 2, rule="Open")
def f_pillar(p, v):
    with lay(p, xf(0, 0, 1.8, 0, 90, 0)):
        cyl(p, "CitadelWhite", 1.8, 1.8, -3.0, 3.0 - v, n=8)
        cyl(p, "AzureDim", 1.85, 1.85, 0.4, 1.0, n=8)
    if v:
        cyl(p, "CitadelWhite", 1.8, 1.8, 0, 2.2, 5.0, 0.4, n=8)


@family("cracked_plate", ["unmooring"], 2, rule="Open", tier=1)
def f_cracked_plate(p, v):
    with lay(p, xf(0, 0, 0.8 + v * 0.4, 20 * v, 14 + 6 * v, 0)):
        box(p, "CitadelWhite", 0, 0, 0, 7.0, 5.0, 1.2)
        box(p, "AzureDim", 0, -2.5, -0.3, 6.5, 0.2, 0.5)
    crystal(p, "AzureNeon", -3.0, 1.0, 0, 0.4, 1.0, 0.01, n=4)


@family("fragment", ["unmooring"], 3, anim="Tumble", air=True)
def f_fragment(p, v):
    fx, fy = ((6.0, 4.0), (8.0, 3.5), (5.0, 5.0))[v]
    box(p, "CitadelWhite", 0, 0, 0, fx, fy, 2.2)
    box(p, "AzureDim", 0, 0, -1.3, fx * 0.6, fy * 0.6, 0.6)
    frustum(p, "HullSlate", 5, 2.0, 0, -1.4, -5, 0, 0)
