"""Sky Citadel scenario kits -- generator.

Run inside Blender (headless is the tested route):

    blender --background --factory-startup --python build_sky_citadel_scenarios.py -- --export

WHAT A SCENARIO KIT IS
The same 36 pieces as the base kit (build_sky_citadel_kit.py, executed here as
a module and never edited by this file), built again with a SCENARIO_HOOK that
changes them for one Fate profile: recolours, grounded dressing, floating
dressing, and route blockers. The geometry a player walks is the base kit's
own, so "I know this place" survives; what is happening on it does not.

WHAT MAKES IT A FATE LEVER, NOT SCENERY (owner direction 2026-09-23)
Every scenario piece also records ANCHORS -- marked spots, per piece, that the
Fate systems can use:
    RESOURCE    a node the Opportunity system may fill (what grows here)
    DISCOVERY   a site for a rare find, shrine or secret
    ENEMY_POST  a place an occupying force can hold
    NPC_POST    a place a faction/NPC presence can stand
    EVENT       a site a mid-run event can play out on
    BLOCKER     one per opening: the game may close that socket this run,
                which is what turns a layout into alternate routes
They are written next to the kit's FBX as data (Anchors_<scenario>.luau).
Nothing reads them yet: that is the code step the owner approves separately.

Outputs (per scenario, under assets/export/worlds/sky_citadel/scenarios/):
    <scenario>/sky_citadel_<scenario>_structure.fbx   36 meshes, each at the origin
    sky_citadel_scenario_props.fbx                    every prop kind, all scenarios
    Props_Scenarios.luau / Fixtures_Scenarios.luau    placements (staged, not in src/)
    <scenario>/Anchors_<scenario>.luau
and assets/source/worlds/sky_citadel/sky_citadel_scenarios.blend: the base kit
plus one collection per scenario, a row each.
"""

import math
import os
import random

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
KIT_PATH = os.path.join(HERE, "build_sky_citadel_kit.py")
K = {"__name__": "sky_citadel_kit", "__file__": KIT_PATH}
exec(open(KIT_PATH, encoding="utf-8").read(), K)

REPO = K["REPO"]
SCEN_EXPORT = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "scenarios")
BLEND_OUT = os.path.join(HERE, "sky_citadel_scenarios.blend")

HALF, DECK_T, CROWN_TOP = K["HALF"], K["DECK_T"], K["CROWN_TOP"]
box, frustum, crystal, torus = K["box"], K["frustum"], K["crystal"], K["torus"]
xf, frame, as_prop, as_fixture, fixture_part = K["xf"], K["frame"], K["as_prop"], K["as_fixture"], K["fixture_part"]
shapes_clash, shape_fits_tile, free_for_float, _inside = (
    K["shapes_clash"], K["shape_fits_tile"], K["free_for_float"], K["_inside"])

# --------------------------------------------------------------------------
# Palette additions, in the kit's style. Added to the module's own PALETTE
# only here, so the base kit's materials are unchanged when it runs alone.
# --------------------------------------------------------------------------
EXTRA_PALETTE = {
    "Soot": ((40, 38, 48), False),         # scorch, cracks, char
    "Snow": ((244, 248, 255), False),      # drifts
    "Ice": ((150, 200, 230), False),       # icicles, ice walls
    "AlarmRed": ((255, 70, 80), True),     # lockdown: small emissive
    "AlarmDim": ((170, 50, 64), True),     # lockdown: large emissive
    "EmberGlow": ((255, 150, 60), True),   # fires
    "RaiderRust": ((158, 74, 52), False),  # raider sails and plates
    "Twig": ((110, 90, 70), False),        # the stormhawk's nest
    "AetherBloom": ((190, 150, 255), True),  # aether surge crystals
}
K["PALETTE"].update(EXTRA_PALETTE)
K["MAT_ORDER"] = list(K["PALETTE"].keys())

# New floating things, so they become props like the kit's own.
K["PROP_KINDS"].update({
    "drifting fragment": ("fragment", "Tumble", 1),
    "storm feather": ("feather", "Tumble", 2),
    "aether shard": ("aether_shard", "Hover", 1),
    "blocker": ("blocker", "Blocker", 1),
})

# --------------------------------------------------------------------------
# The seven scenarios (docs/biomes/SKY_CITADEL.md > Scenario kits)
# --------------------------------------------------------------------------
SCENARIOS = ["unmooring", "siege", "lockdown", "stormhawk", "rime", "reclaimed", "aether_surge"]


# ---- reading a finished piece -------------------------------------------------

def openings(p):
    """The piece's openings, from its description: a set of N/S/E/W."""
    head = p.notes.split("--")[0].upper()
    found = set()
    for word, d in (("NORTH", "N"), ("SOUTH", "S"), ("EAST", "E"), ("WEST", "W")):
        if word in head:
            found.add(d)
    for token in head.replace("|", " ").replace("+", " ").replace(",", " ").split():
        if token in ("N", "S", "E", "W"):
            found.add(token)
    return found


def mouth(d, inset=10.0):
    """A point on the opening's deck, `inset` in from the tile edge, and the
    turn that faces across it."""
    return {"N": (0, HALF - inset, 0), "S": (0, -HALF + inset, 0),
            "E": (HALF - inset, 0, 90), "W": (-HALF + inset, 0, 90)}[d]


def deck_polys(p):
    return [w for w, _, _ in p.slabs]


def in_corridor(p, x, y, half=24.0):
    """Keep the walking line between openings clear of dressing."""
    o = openings(p)
    if o & {"N", "S"} and abs(x) < half:
        if ("N" in o and y > -half) or ("S" in o and y < half):
            return True
    if o & {"E", "W"} and abs(y) < half:
        if ("E" in o and x > -half) or ("W" in o and x < half):
            return True
    return False


class Placer:
    """Finds free spots on a piece's decks, clear of everything registered."""

    def __init__(self, p, rng):
        self.p, self.rng = p, rng
        self.polys = deck_polys(p)

    def ground(self, r, h, label, tries=120, corridor=True, margin=2.0):
        # the aviary's birds circle low over its decks, and the kit proves
        # every orbit clear afterwards (clear_bird_orbits): keep it flat there
        if "aviary" in self.p.name and h > 1.0:
            return None
        for _ in range(tries):
            if not self.polys:
                return None
            poly = self.rng.choice(self.polys)
            xs, ys = [q[0] for q in poly], [q[1] for q in poly]
            x, y = self.rng.uniform(min(xs), max(xs)), self.rng.uniform(min(ys), max(ys))
            rim = [(x + (r + margin) * math.cos(a), y + (r + margin) * math.sin(a))
                   for a in (2 * math.pi * k / 12 for k in range(12))]
            if not all(_inside(q, poly) for q in rim + [(x, y)]):
                continue
            if corridor and in_corridor(self.p, x, y):
                continue
            shape = ("cyl", x, y, r, 0.0, h)
            if any(shapes_clash(shape, s, gap=1.0) for _, s in self.p.solids + self.p.floats):
                continue
            self.p.solid(label, x, y, r, 0, h)
            return x, y
        return None

    def air(self, r, z0, z1, label, tries=160, near_deck=40.0):
        """A spot in open air beside the decks, clear by the float rules."""
        for _ in range(tries):
            x, y = self.rng.uniform(-HALF + 12, HALF - 12), self.rng.uniform(-HALF + 12, HALF - 12)
            shape = ("cyl", x, y, r, z0, z1)
            if not free_for_float(self.p, shape):
                continue
            if near_deck and self.polys and not any(
                    min(math.hypot(x - q[0], y - q[1]) for q in poly) < near_deck for poly in self.polys):
                continue
            self.p.float_(label, x, y, r, z0, z1)
            return x, y
        return None


def recolour(p, mapping, fraction=1.0, rng=None, props_too=True):
    """Swap palette colours on the piece's faces (and its props')."""
    rng = rng or random.Random(0)
    for i, m in enumerate(p.fmat):
        if m in mapping and (fraction >= 1.0 or rng.random() < fraction):
            p.fmat[i] = mapping[m]
    if props_too:
        for prop in p.props:
            prop["mats"] = [mapping.get(m, m) if fraction >= 1.0 else m for m in prop["mats"]]


def add_anchor(p, kind, x, y, z=0.0, note=""):
    p.anchors.append({"kind": kind, "pos": (x, y, z), "note": note})


def anchors_on_decks(p, pl, kinds, rng):
    """Every piece gets its gameplay anchors, by what the piece is for."""
    role = p.notes.split("|")[0].strip().split()[0]
    counts = {"COMBAT": {"ENEMY_POST": 4, "RESOURCE": 2, "EVENT": 1},
              "PATH": {"ENEMY_POST": 1, "RESOURCE": 1},
              "SIDE": {"DISCOVERY": 2, "RESOURCE": 2},
              "CAP": {"DISCOVERY": 1, "RESOURCE": 1},
              "BOSS": {"EVENT": 2},
              "ENTRY": {"NPC_POST": 2}}.get(role, {})
    for kind, n in counts.items():
        n = kinds.get(kind, n)
        for _ in range(n):
            spot = pl.ground(2.0, 3.0, "anchor " + kind.lower())
            if spot:
                add_anchor(p, kind, spot[0], spot[1])
    for d in sorted(openings(p)):
        x, y, _ = mouth(d)
        add_anchor(p, "BLOCKER", x, y, note=d)


def reserve_blockers(p):
    """Claim every opening's blocker space before any dressing is placed."""
    for d in openings(p):
        x, y, _ = mouth(d)
        p.solid("blocker", x, y, 8, 0, 14)


def blocker(p, d, builder):
    """A route blocker at one opening, as a prop: the game decides per run
    which sockets it closes. Its space was reserved by reserve_blockers().
    Every blocker of a scenario is the same shape (seeded by the scenario, not
    the piece), so a kit adds one prop mesh for them, not one per opening."""
    x, y, rz = mouth(d)
    with frame(p, xf(x, y, 0, rz)):
        with as_prop(p, "blocker", Matrix.Identity(4)):
            builder(p, random.Random(CURRENT[0]))


# ---- dressing vocabulary --------------------------------------------------------
#
# TWO KINDS OF DRESSING (owner direction 2026-09-23: props and chunks separate)
#   surface  cracks, scorch, moss, snow: paint on the walk plane. Stays in the
#            structure mesh -- nothing to animate or use.
#   props    everything else. Each is ONE fixed shape (seeded by its kind, not
#            the piece) placed at a size, so a kind is one library mesh however
#            many times it appears. Each carries an interaction the game wires:
#            PROP_INTERACT below, overridable per placement.

K["PROP_KINDS"].update({
    "raider tent": ("raider_tent", "Static", 1),
    "barricade": ("barricade", "Static", 1),
    "fire": ("fire", "Flicker", 1),
    "sentinel pylon": ("sentinel", "Static", 1),
    "nest": ("nest", "Static", 1),
    "aether cluster": ("aether_cluster", "Pulse", 1),
    "ice spike": ("ice_spike", "Static", 1),
    "overgrowth": ("overgrowth", "Sway", 2),
    "snow drift": ("snow_drift", "Static", 2),
})
K["PROP_INTERACT"].update({
    "raider tent": "Loot",          # the raiders' stores
    "barricade": "Destroy",
    "fire": "Hazard",
    "sentinel pylon": "Destroy",    # lockdown turret: break it to thin the defence
    "nest": "Event",                # the stormhawk dives here
    "aether cluster": "Harvest",
    "aether shard": "Harvest",
    "ice spike": "Break",
    "overgrowth": "Cut",
    "storm feather": "Pickup",
    "blocker": "Blocker",           # closes its socket when the run says so
})


def place(p, label, x, y, rz, s, shape):
    """One prop: anchored at (x, y, 0) turned rz, drawn at scale s. The scale
    goes into the geometry and the turn into the placement, which is what
    lets every copy of a kind share one mesh."""
    with frame(p, xf(x, y, 0, rz)):
        with as_prop(p, label, Matrix.Identity(4)):
            with frame(p, Matrix.Diagonal((s, s, s, 1.0))):
                shape(p)


def crack(p, x, y, rng, L=None, w=1.2):
    L = L or rng.uniform(18, 36)
    a = rng.uniform(0, 180)
    px, py = x, y
    for _ in range(3):
        seg = L / 3
        a += rng.uniform(-35, 35)
        dx, dy = math.cos(math.radians(a)) * seg, math.sin(math.radians(a)) * seg
        box(p, "Soot", px + dx / 2, py + dy / 2, 0.06, seg, w, 0.06, rz=a)
        px, py = px + dx, py + dy


def surface_crack(p, pl, rng, L, w=1.2):
    """A crack reserves its whole reach, so it can never leave its deck."""
    spot = pl.ground(L * 0.55, 0.2, "crack", corridor=False, margin=1.0)
    if spot:
        crack(p, spot[0], spot[1], rng, L=L, w=w)


# fixed shapes, built at the origin, one unit of size each
def shape_tent(p):
    box(p, "RaiderRust", 0, -2.2, 2.6, 10, 0.4, 6.4, rx=35)
    box(p, "RaiderRust", 0, 2.2, 2.6, 10, 0.4, 6.4, rx=-35)
    box(p, "DeepAlloy", 0, 0, 5.3, 10.6, 0.6, 0.6)
    for sx in (-5.2, 5.2):
        frustum(p, "DeepAlloy", 4, 0.3, 0.3, 0, 5.6, sx, 0)


def shape_barricade(p):
    box(p, "PaleAlloy", -3, 0, 1.3, 3, 3, 2.6)
    box(p, "PaleAlloy", 3, 0, 1.3, 3, 3, 2.6, rz=8)
    box(p, "RaiderRust", 0, 0.4, 2.8, 9, 0.5, 1.2, rx=10)


def shape_fire(p):
    frustum(p, "Soot", 8, 2.6, 2.2, 0.0, 0.12, 0, 0)
    for k, (a, h) in enumerate(((0.3, 3.4), (2.2, 2.4), (4.1, 3.0), (5.4, 2.0))):
        crystal(p, "EmberGlow", math.cos(a) * 0.8, math.sin(a) * 0.8, 0.12, 0.7, h, 0.01, n=4, rz=30 * k)


def shape_sentinel(p):
    frustum(p, "DeepAlloy", 6, 1.8, 1.4, 0, 1.2, 0, 0)
    frustum(p, "PaleAlloy", 4, 1.1, 0.7, 1.2, 7.5, 0, 0, rot=45)
    crystal(p, "AlarmRed", 0, 0, 8.6, 0.9, 1.3, 1.0, n=4)


def shape_nest(p):
    R = 7.0
    for k in range(18):
        a = 20 * k
        box(p, "Twig", math.cos(math.radians(a)) * R, math.sin(math.radians(a)) * R, 1.0,
            7.5, 0.6, 0.6, rz=a + 90 + (k % 3 - 1) * 14, rx=(k % 2) * 16 - 8)
    frustum(p, "Twig", 10, R - 1.5, R + 0.5, 0.0, 1.2, 0, 0)
    for k in range(3):
        a = math.radians(120 * k + 20)
        crystal(p, "Snow", math.cos(a) * 1.4, math.sin(a) * 1.4, 1.6, 0.9, 1.1, 0.9, n=6)


def shape_aether(p):
    for k, (a, d, r, h) in enumerate(((0.0, 0.0, 1.1, 6.0), (1.3, 1.8, 0.8, 4.2), (2.8, 2.0, 0.7, 3.4),
                                      (4.2, 1.6, 0.9, 4.8), (5.5, 2.1, 0.6, 2.8))):
        crystal(p, "AetherBloom" if k % 2 == 0 else "SkyGlass", math.cos(a) * d, math.sin(a) * d, 0.0,
                r, h, 0.01, n=5, rz=17 * k)


def shape_ice_spike(p):
    crystal(p, "Ice", 0, 0, 0.0, 1.0, 5.0, 0.01, n=5)
    crystal(p, "Ice", 0.9, 0.4, 0.0, 0.5, 2.4, 0.01, n=5, rz=30)


def shape_overgrowth(p):
    frustum(p, "Verdure", 7, 2.4, 1.0, 0, 2.9, 0, 0)
    frustum(p, "Verdure", 7, 1.7, 0, 2.4, 4.6, 0, 0)


def shape_drift(p):
    frustum(p, "Snow", 7, 1.0, 0.55, 0.0, 0.22, 0, 0)


def scatter(p, pl, rng, label, shape, count, r_unit, h_unit, s_range, corridor=True, interact=None):
    """Place `count` props of one kind at random free spots and sizes."""
    placed = []
    for _ in range(count):
        s = rng.uniform(*s_range)
        spot = pl.ground(r_unit * s, h_unit * s, label, corridor=corridor)
        if spot:
            place(p, label, spot[0], spot[1], rng.uniform(0, 360), s, shape)
            if interact:
                p.props[-1]["interact"] = interact
            placed.append(spot)
    return placed


# ---- the seven hooks ------------------------------------------------------------

def dress_unmooring(p, rng, pl):
    recolour(p, {"AzureDim": "DeepAlloy", "AzureNeon": "DeepAlloy"}, fraction=0.5, rng=rng, props_too=False)
    for _ in range(rng.randint(6, 10)):
        surface_crack(p, pl, rng, rng.uniform(18, 36))
    for prop in p.props:   # the anti-grav is failing: what floated now lists
        if prop["label"] in ("floating crystal", "anti-grav pylon"):
            prop["matrix"] = prop["matrix"] @ xf(rx=rng.uniform(12, 28), ry=rng.uniform(-15, 15))
        if prop["label"] in ("lamp", "light pillar"):
            prop["interact"] = "Repair"      # dead lights you can bring back
    for _ in range(rng.randint(3, 5)):
        spot = pl.air(5.0, -14.0, 10.0, "drifting fragment")
        if spot:
            x, y = spot
            with frame(p, xf(x, y, -2, rng.uniform(0, 90), rx=rng.uniform(-20, 20))):
                with as_prop(p, "drifting fragment", Matrix.Identity(4)):
                    fx, fy = rng.choice(((6.0, 4.0), (8.0, 3.5), (5.0, 5.0)))
                    box(p, "CitadelWhite", 0, 0, 0, fx, fy, 2.2)
                    box(p, "AzureDim", 0, 0, -1.3, 4, 2.5, 0.6)
                    frustum(p, "HullSlate", 5, 2.0, 0, -1.4, -5, 0, 0)
    for d in openings(p):
        blocker(p, d, lambda p, r: (
            [box(p, "CitadelWhite", k * 5 - 7.5, 0, 1.2, 6, 5, 2.4, rz=k * 17, rx=8 * (k - 1)) for k in range(4)],
            [box(p, "AzureDim", k * 9 - 9, 2.8, 0.4, 3, 0.4, 0.8) for k in range(3)]))
    anchors_on_decks(p, pl, {"RESOURCE": 2}, rng)
    for a in p.anchors:
        if a["kind"] == "RESOURCE":
            a["note"] = "exposed aether core -- harvesting speeds the collapse"


def dress_siege(p, rng, pl):
    scatter(p, pl, rng, "raider tent", shape_tent, rng.randint(3, 5), 7.5, 6.0, (1.0, 1.3))
    scatter(p, pl, rng, "barricade", shape_barricade, rng.randint(4, 7), 5.0, 3.0, (1.4, 2.2))
    scatter(p, pl, rng, "fire", shape_fire, rng.randint(3, 5), 2.8, 3.6, (1.8, 2.8), corridor=False)
    for _ in range(rng.randint(4, 7)):
        spot = pl.ground(6.0, 0.2, "scorch", corridor=False)
        if spot:
            frustum(p, "Soot", 9, rng.uniform(4, 6), rng.uniform(3, 5), 0.0, 0.07, spot[0], spot[1])
    for prop in p.props:
        if prop["label"] in ("crate", "container"):
            prop["interact"] = "Loot"        # the raiders' plunder, stacked to carry off
    if "SIDE" not in p.notes and "CAP" not in p.notes:
        for _ in range(rng.randint(1, 2)):   # raider skiffs moored off the decks
            for _t in range(60):
                x, y = rng.uniform(-100, 100), rng.uniform(-100, 100)
                probe = ("cyl", x, y, 19.0, -8.0, 14.0)
                if free_for_float(p, probe):
                    before = len(p.props)
                    K["skiff"](p, x, y, -2.2, rz=rng.uniform(0, 360))
                    for prop in p.props[before:]:
                        prop["mats"] = ["RaiderRust" if m == "CitadelViolet" else m for m in prop["mats"]]
                        prop["interact"] = "Board"
                    break
    recolour(p, {"CitadelViolet": "Soot"}, fraction=0.4, rng=rng, props_too=False)
    for d in openings(p):
        blocker(p, d, lambda p, r: (shape_barricade(p), [box(p, "RaiderRust", k * 7 - 7, -2, 2.0, 4, 0.5, 4, rz=k * 20)
                                                           for k in range(3)]))
    anchors_on_decks(p, pl, {"ENEMY_POST": 6, "NPC_POST": 2}, rng)
    for a in p.anchors:
        if a["kind"] == "NPC_POST":
            a["note"] = "citadel defenders hold here, or a captive to free"


def dress_lockdown(p, rng, pl):
    recolour(p, {"AzureNeon": "AlarmRed", "AzureDim": "AlarmDim"})
    scatter(p, pl, rng, "sentinel pylon", shape_sentinel, rng.randint(3, 5), 2.2, 9.0, (1.0, 1.6))
    for prop in p.props:
        if prop["label"] == "holo pedestal":
            prop["interact"] = "Override"    # a console that opens one field
    for d in openings(p):
        x, y, rz = mouth(d, inset=14)
        p.solid("lockdown field", x, y, 22, 0, 20)
        with frame(p, xf(x, y, 0, rz)):
            with as_fixture(p, "FORCEFIELD", Matrix.Identity(4)):
                with fixture_part(p, "Field"):
                    box(p, "SkyGlass", 0, 0, 9, 40, 0.6, 18)
            for sx in (-21, 21):   # the emitters are the posts' own props
                with as_prop(p, "sentinel pylon", xf(sx, 0, 0)):
                    frustum(p, "PaleAlloy", 4, 1.4, 1.2, 0, 19, sx, 0, rot=45)
                    crystal(p, "AlarmRed", sx, 0, 20.5, 0.8, 1.4, 0.8)
                p.props[-1]["interact"] = "Destroy"
    anchors_on_decks(p, pl, {"ENEMY_POST": 5, "EVENT": 2}, rng)
    for a in p.anchors:
        if a["kind"] == "EVENT":
            a["note"] = "a field generator: shut it down to open the fields"


def dress_stormhawk(p, rng, pl):
    role = p.notes.split("|")[0].strip().split()[0]
    if role in ("COMBAT", "BOSS"):
        for spot in scatter(p, pl, rng, "nest", shape_nest, 1, 11.0, 2.5, (2.0, 2.0)):
            add_anchor(p, "EVENT", spot[0], spot[1], note="the stormhawk's nest: it dives here")
    for _ in range(rng.randint(3, 6)):
        surface_crack(p, pl, rng, rng.uniform(24, 40), w=1.6)
    for _ in range(rng.randint(3, 5)):
        spot = pl.air(1.5, 8.0, 14.0, "storm feather", near_deck=30)
        if spot:
            x, y = spot
            with frame(p, xf(x, y, 11, rng.uniform(0, 180), rx=rng.uniform(-30, 30))):
                with as_prop(p, "storm feather", Matrix.Identity(4)):
                    box(p, "DeepAlloy", 0, 0, 0, 5.5, 0.9, 0.12)
                    box(p, "SunGold", 1.8, 0, 0.02, 1.6, 0.95, 0.12)
    for prop in p.props:
        if prop["label"] == "banner":
            prop["interact"] = None
    for d in openings(p):
        blocker(p, d, lambda p, r: (
            frustum(p, "DeepAlloy", 6, 1.2, 0.8, 0, 12, -8, 0, M=xf(ry=70)),
            [box(p, "Twig", k * 4 - 8, 1, 0.6, 5, 0.5, 0.5, rz=k * 40) for k in range(5)]))
    anchors_on_decks(p, pl, {"RESOURCE": 2}, rng)
    for a in p.anchors:
        if a["kind"] == "RESOURCE":
            a["note"] = "stormhawk feathers"


def dress_rime(p, rng, pl):
    recolour(p, {"Verdure": "Snow", "AzureDim": "Ice", "PaleAlloy": "Snow"}, props_too=False)
    scatter(p, pl, rng, "snow drift", shape_drift, rng.randint(10, 16), 1.0, 0.25, (6.0, 13.0), corridor=False)
    scatter(p, pl, rng, "ice spike", shape_ice_spike, rng.randint(3, 6), 1.5, 5.2, (2.4, 4.6))
    for prop in p.props:
        if prop["label"] == "brazier":
            prop["interact"] = "Lightable"   # warmth: the rime's safe spots
    for poly in deck_polys(p):               # icicles: part of the deck rim
        n = len(poly)
        cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
        for _ in range(max(4, n)):
            i = rng.randrange(n)
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            t = rng.uniform(0.15, 0.85)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            x, y = x + (cx - x) * 0.02, y + (cy - y) * 0.02
            crystal(p, "Ice", x, y, -DECK_T, 0.6, 0.01, rng.uniform(2.5, 7), n=4)
    for d in openings(p):
        blocker(p, d, lambda p, r: [crystal(p, "Ice", k * 4.5 - 9, (k % 2) - 0.5, 0.0, 2.4, 6 + (k * 7) % 5, 0.01, n=5)
                                    for k in range(5)])
    anchors_on_decks(p, pl, {"RESOURCE": 1, "DISCOVERY": 1}, rng)
    for a in p.anchors:
        if a["kind"] == "DISCOVERY":
            a["note"] = "something frozen in the ice"


def dress_reclaimed(p, rng, pl):
    recolour(p, {"AzureNeon": "DeepAlloy", "AzureDim": "HullSlate"}, props_too=False)
    recolour(p, {"PaleAlloy": "Verdure", "CitadelViolet": "HullSlate"}, fraction=0.35, rng=rng, props_too=False)
    for poly in deck_polys(p):
        K["vines"](p, poly, "reclaimed %s %d" % (p.name, len(poly)), count=max(6, len(poly)))
    for _ in range(rng.randint(10, 16)):
        spot = pl.ground(8.0, 0.2, "moss", corridor=False)
        if spot:
            box(p, "Verdure", spot[0], spot[1], 0.05, rng.uniform(6, 12), rng.uniform(4, 9), 0.08, rz=rng.uniform(0, 180))
    for _ in range(rng.randint(3, 6)):
        surface_crack(p, pl, rng, rng.uniform(16, 30))
    scatter(p, pl, rng, "overgrowth", shape_overgrowth, rng.randint(5, 9), 2.6, 4.8, (2.0, 3.2))
    for prop in p.props:
        if prop["label"] in ("lamp", "light pillar", "brazier", "holo pedestal"):
            prop["interact"] = None          # long dead
        if prop["label"] in ("crate", "container"):
            prop["interact"] = "Loot"        # left behind when they went
    for d in openings(p):
        blocker(p, d, lambda p, r: [frustum(p, "Verdure", 7, 2.6, 0, 0, 6 + k % 2 * 2, k * 5 - 10, 0) for k in range(5)])
    anchors_on_decks(p, pl, {"RESOURCE": 3, "DISCOVERY": 1}, rng)
    for a in p.anchors:
        if a["kind"] == "RESOURCE":
            a["note"] = "wild growth: herbs and seeds"


def dress_aether_surge(p, rng, pl):
    recolour(p, {"AzureNeon": "AetherBloom"}, props_too=True)
    for spot in scatter(p, pl, rng, "aether cluster", shape_aether, rng.randint(5, 9), 3.0, 6.2, (2.0, 4.0)):
        add_anchor(p, "RESOURCE", spot[0], spot[1], note="aether crystal: the surge's resource")
    for _ in range(rng.randint(3, 5)):
        spot = pl.air(2.0, 10.0, 22.0, "aether shard", near_deck=36)
        if spot:
            x, y = spot
            with as_prop(p, "aether shard", xf(x, y, 16)):
                crystal(p, "AetherBloom", x, y, 16, 1.4, 4.5, 3.5, n=5)
    for prop in p.props:
        if prop["label"] == "holo pedestal":
            prop["interact"] = "Attune"      # read the surge: where it breaks next
    for d in openings(p):
        blocker(p, d, lambda p, r: [crystal(p, "AetherBloom", k * 5 - 10, 0, 0.0, 1.8, 7 + (k * 3) % 4, 0.01, n=5)
                                    for k in range(5)])
    anchors_on_decks(p, pl, {"DISCOVERY": 2, "RESOURCE": 1}, rng)
    for a in p.anchors:
        if a["kind"] == "DISCOVERY" and not a["note"]:
            a["note"] = "the surge has uncovered something old"


HOOKS = {
    "unmooring": dress_unmooring, "siege": dress_siege, "lockdown": dress_lockdown,
    "stormhawk": dress_stormhawk, "rime": dress_rime, "reclaimed": dress_reclaimed,
    "aether_surge": dress_aether_surge,
}


CURRENT = [None]   # the scenario being built, for blocker shapes


def make_hook(scenario):
    def hook(p):
        p.anchors = []
        CURRENT[0] = scenario
        reserve_blockers(p)
        rng = random.Random("%s|%s" % (p.name, scenario))
        HOOKS[scenario](p, rng, Placer(p, rng))
    return hook


# ---- assembly ---------------------------------------------------------------------

ROW = 2 * HALF + K["REVIEW_GAP"]


def build_set(scenario, mats, row):
    """All 36 pieces for one scenario (None = the base kit), in one row."""
    K["SCENARIO_HOOK"] = make_hook(scenario) if scenario else None
    name = "SkyCitadel_Kit" if not scenario else "SkyCitadel_%s" % scenario.title().replace("_", "")
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    pieces, objs = [], []
    for i, builder in enumerate(K["BUILDERS"]):
        p = builder()
        if scenario:
            p.name = "%s__%s" % (p.name, scenario)
        if not hasattr(p, "anchors"):
            p.anchors = []
        K["PIECES_BY_NAME"][p.name] = p
        obj = K["to_object"](p, mats, coll)
        obj["scenario"] = scenario or "base"
        obj.location = (i * ROW, -row * ROW * 1.25, 0)
        pieces.append(p)
        objs.append(obj)
    K["SCENARIO_HOOK"] = None
    return pieces, objs


def preview_props(pieces, objs, mats, coll):
    """Review only: every prop and fixture drawn in place on its piece, in a
    collection that is never exported. The game places them from the
    placement files; this is so the kit can be judged whole in Blender."""
    n = 0
    for p, obj in zip(pieces, objs):
        parts = [(prop["matrix"], prop["verts"], prop["faces"], prop["mats"]) for prop in p.props]
        for fx in p.fixtures:
            parts += [(fx["matrix"], part["verts"], part["faces"], part["mats"]) for part in fx["parts"]]
        for i, (M, verts, faces, fmats) in enumerate(parts):
            shell = K["Piece"]("%s__prop%03d" % (p.name, i), "preview")
            shell.verts, shell.faces, shell.fmat = list(verts), faces, fmats
            o = K["to_object"](shell, mats, coll)
            o.matrix_world = obj.matrix_world @ M
            o.parent = obj
            o.matrix_parent_inverse = obj.matrix_world.inverted()
            n += 1
    return n


def write_anchors(path, scenario, pieces):
    lines = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py.",
        "-- Do not edit by hand. Gameplay anchors for the '%s' scenario kit:" % scenario,
        "-- where the Fate systems may place resources, discoveries, enemy and NPC",
        "-- posts, events, and which sockets a run may block. Positions are in the",
        "-- chunk's local studs (x east, y up, z south), like the prop placements.",
        "return {",
    ]
    for p in pieces:
        lines.append('\t["%s"] = {' % K["_content_id"](p.name))
        for a in p.anchors:
            x, y, z = a["pos"]
            lines.append('\t\t{ Kind = "%s", Pos = { %.2f, %.2f, %.2f }, Note = %s },'
                         % (a["kind"], x, z, -y, '"%s"' % a["note"].replace('"', "'")))
        lines.append("\t},")
    lines.append("}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return sum(len(p.anchors) for p in pieces)


def export_structure(objs, path):
    K["_export_selected"](objs, path)


def main(export=False, save=True):
    K["reset_scene"]()
    mats = K["ensure_materials"]()
    report = {}
    all_pieces = []
    sets = {}
    preview = bpy.data.collections.new("Preview_Props_NotExported")
    bpy.context.scene.collection.children.link(preview)
    for row, scen in enumerate([None] + SCENARIOS):
        pieces, objs = build_set(scen, mats, row)
        bpy.context.view_layer.update()
        preview_props(pieces, objs, mats, preview)
        ok, rep = K["validate"](objs)
        report[scen or "base"] = {"ok": ok, "failed": [(r["piece"], r["failed"], r["float_problems"][:2],
                                                         r["ground_problems"][:2]) for r in rep if not r["ok"]],
                                  "tris_max": max(r["tris"] for r in rep)}
        sets[scen] = (pieces, objs)
        if scen:
            all_pieces += pieces
    kinds, placements, fixtures = K["prop_library"](all_pieces)
    lib = bpy.data.collections.new("ScenarioPropLibrary")
    bpy.context.scene.collection.children.link(lib)
    prop_objs = K["props_to_objects"](kinds, mats, lib)
    for o in prop_objs:
        o.location.y -= (len(SCENARIOS) + 2) * ROW * 1.25
    out = {"report": report, "prop_kinds": len(kinds)}
    if export:
        bad = {k: v["failed"] for k, v in report.items() if not v["ok"]}
        if bad:
            raise RuntimeError("validation failed; not exporting: %r" % bad)
        os.makedirs(SCEN_EXPORT, exist_ok=True)
        paths, anchors = [], {}
        for scen in SCENARIOS:
            pieces, objs = sets[scen]
            d = os.path.join(SCEN_EXPORT, scen)
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "sky_citadel_%s_structure.fbx" % scen)
            export_structure(objs, path)
            paths.append(path)
            anchors[scen] = write_anchors(os.path.join(d, "Anchors_%s.luau" % scen), scen, pieces)
        props_path = os.path.join(SCEN_EXPORT, "sky_citadel_scenario_props.fbx")
        export_structure(prop_objs, props_path)
        verified = K["verify_exports"](paths + [props_path])
        for v in verified[:-1]:
            wrong = {k: s for k, s in v["sizes"].items() if any(abs(c - 256) > 0.01 for c in s)}
            if v["meshes"] != len(K["BUILDERS"]) or wrong:
                raise RuntimeError("%s did not come back %d x 256^3: %r" % (v["file"], len(K["BUILDERS"]), wrong))
        if verified[-1]["meshes"] != len(kinds):
            raise RuntimeError("scenario prop export came back with %d meshes" % verified[-1]["meshes"])
        out["exported"] = [(v["file"], v["meshes"]) for v in verified]
        out["anchors"] = anchors
        out["placements"] = K["write_props_luau"](kinds, placements, os.path.join(SCEN_EXPORT, "Props_Scenarios.luau"))
        out["fixtures"] = K["write_fixtures_luau"](kinds, fixtures, os.path.join(SCEN_EXPORT, "Fixtures_Scenarios.luau"))
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    return out


if __name__ == "__main__":
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    print(main(export="--export" in argv))
