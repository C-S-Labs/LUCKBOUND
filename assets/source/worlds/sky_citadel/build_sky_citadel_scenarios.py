"""Sky Citadel scenario kits -- generator.

Run inside Blender (headless is the tested route):

    blender --background --factory-startup --python build_sky_citadel_scenarios.py -- --export

WHAT A SCENARIO KIT IS
The same 36 pieces as the base kit (build_sky_citadel_kit.py, executed here as
a module and never edited by this file), built again with a SCENARIO_HOOK that
changes them for one Fate profile. The walkable layout is the base kit's own,
so "I know this place" survives; what is happening on it does not.

A hook does four things:
  1. STRUCTURE  crumbling (breached walls, broken tower tops, islets coming
                loose), whole-surface looks (snow on every upward face, moss on
                wall tops, violet seams), and surface paint (cracks, scorch,
                moss carpets, glowing fissures). Stays in the structure mesh.
  2. PROPS      everything that can animate or be interacted with -- a large
                vocabulary per scenario, two or three variants of most things.
                Each variant is one fixed shape placed at a size, so every copy
                shares one library mesh. Each carries an `Interact` the game
                wires (`PROP_INTERACT`, overridable per placement).
  3. BLOCKERS   one per opening, a prop the run may enable to close that socket.
  4. ANCHORS    RESOURCE / DISCOVERY / ENEMY_POST / NPC_POST / EVENT spots the
                Fate systems place things on (Anchors_<scenario>.luau).

HOW THINGS ARE PLACED (owner direction 2026-09-23: nothing floats by accident,
and no two chunks are dressed alike)
* Every grounded prop is ray-cast onto the real walk surface, and its whole
  footprint must be flat deck: nothing hovers, nothing sinks into a terrace,
  nothing hangs over an edge.
* Each scenario has its own spatial logic -- moss creeps along the foot of the
  walls and up the turrets, snow piles against the lee of the walls from a
  per-piece wind, aether erupts from one to three epicentres, raiders make one
  camp and face their defences at the openings -- and every piece draws its own
  density, wind, epicentres and camp site.
* The only things that float are the ones meant to (drifting fragments, drones,
  feathers on the wind, aether shards, moored warships), and they pass the
  kit's own float rules.

Outputs (under assets/export/worlds/sky_citadel/scenarios/):
    <scenario>/sky_citadel_<scenario>_structure.fbx   36 meshes, each at the origin
    sky_citadel_scenario_props.fbx                    every prop kind, all scenarios
    Props_Scenarios.luau / Fixtures_Scenarios.luau    placements (staged, not in src/)
    <scenario>/Anchors_<scenario>.luau
and assets/source/worlds/sky_citadel/sky_citadel_scenarios.blend: the base kit
plus one collection per scenario, a row each, with every prop drawn in place in
Preview_Props_NotExported.
"""

import math
import os
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

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
shapes_clash, free_for_float, _inside = K["shapes_clash"], K["free_for_float"], K["_inside"]
I4 = Matrix.Identity(4)

# --------------------------------------------------------------------------
# Palette additions, in the kit's style. Added to the module's own PALETTE
# only here, so the base kit's materials are unchanged when it runs alone.
# --------------------------------------------------------------------------
EXTRA_PALETTE = {
    "Soot": ((40, 38, 48), False),          # cracks, char, keels
    "Char": ((64, 54, 52), False),          # burnt ground, scorched cloth
    "Snow": ((244, 248, 255), False),
    "Frost": ((196, 214, 232), False),      # frosted white stone
    "FrostDeep": ((150, 172, 198), False),  # frosted alloy
    "Ice": ((150, 200, 230), False),
    "AlarmRed": ((255, 70, 80), True),      # lockdown: small emissive
    "AlarmDim": ((170, 50, 64), True),      # lockdown: large emissive
    "EmberGlow": ((255, 150, 60), True),    # fire, raider drives
    "Smoke": ((104, 104, 116), False),
    "RaiderRust": ((158, 74, 52), False),   # raider hulls, sails, tents
    "Twig": ((110, 90, 70), False),         # nests, planks, ship decks
    "Bark": ((92, 70, 52), False),          # trunks, roots, logs
    "Bone": ((226, 220, 200), False),
    "Moss": ((70, 112, 66), False),
    "MossLight": ((118, 160, 86), False),
    "AetherBloom": ((190, 150, 255), True),   # aether: small emissive
    "AetherDim": ((120, 90, 190), True),      # aether: large emissive
}
K["PALETTE"].update(EXTRA_PALETTE)
K["MAT_ORDER"] = list(K["PALETTE"].keys())

# label -> (library base name, animation class, detail tier)
K["PROP_KINDS"].update({
    # floating, on purpose
    "drifting fragment": ("fragment", "Tumble", 1),
    "storm feather": ("feather", "Tumble", 2),
    "aether shard": ("aether_shard", "Hover", 1),
    "security drone": ("drone", "Hover", 1),
    "raider warship": ("warship", "Moored", 1),
    # grounded
    "blocker": ("blocker", "Blocker", 1),
    "rubble": ("rubble", "Static", 1),
    "fallen roof": ("fallen_roof", "Static", 1),
    "gangway": ("gangway", "Static", 1),
    "raider tent": ("raider_tent", "Static", 1),
    "raider yurt": ("raider_yurt", "Static", 1),
    "stake wall": ("stake_wall", "Static", 1),
    "barricade": ("barricade", "Static", 1),
    "barrel": ("barrel", "Static", 1),
    "loot pile": ("loot_pile", "Static", 1),
    "campfire": ("campfire", "Flicker", 1),
    "bonfire": ("bonfire", "Flicker", 1),
    "raider banner": ("raider_banner", "Sway", 2),
    "ballista": ("ballista", "Static", 1),
    "sentinel pylon": ("sentinel", "Static", 1),
    "sentinel turret": ("turret", "Static", 1),
    "alarm post": ("alarm_post", "Strobe", 1),
    "laser fence": ("laser_fence", "Pulse", 1),
    "console": ("console", "Static", 1),
    "nest": ("nest", "Static", 1),
    "egg shells": ("egg_shells", "Static", 2),
    "bone pile": ("bone_pile", "Static", 2),
    "fallen feather": ("fallen_feather", "Static", 2),
    "snow drift": ("snow_drift", "Static", 2),
    "ice spikes": ("ice_spikes", "Static", 1),
    "frost crystals": ("frost_crystals", "Static", 2),
    "frozen figure": ("frozen_figure", "Static", 1),
    "moss mound": ("moss_mound", "Static", 2),
    "bush": ("bush", "Sway", 2),
    "fern": ("fern", "Sway", 2),
    "flowers": ("flowers", "Sway", 2),
    "sapling": ("sapling", "Sway", 1),
    "mushrooms": ("mushrooms", "Static", 2),
    "aether cluster": ("aether_cluster", "Pulse", 1),
    "aether geode": ("aether_geode", "Pulse", 1),
    "stabilizer": ("stabilizer", "Pulse", 1),
    "hazard beacon": ("hazard_beacon", "Strobe", 1),
})
K["PROP_INTERACT"].update({
    "blocker": "Blocker",
    "raider warship": "Board",
    "raider tent": "Loot", "raider yurt": "Loot", "loot pile": "Loot",
    "barricade": "Destroy", "stake wall": "Destroy", "barrel": "Breakable",
    "campfire": "Hazard", "bonfire": "Hazard", "ballista": "Use",
    "sentinel pylon": "Destroy", "sentinel turret": "Destroy", "security drone": "Destroy",
    "laser fence": "Hazard", "console": "Override",
    "nest": "Event", "egg shells": "Pickup", "bone pile": "Loot",
    "fallen feather": "Pickup", "storm feather": "Pickup",
    "ice spikes": "Break", "frost crystals": "Break", "frozen figure": "Break",
    "bush": "Cut", "sapling": "Cut", "flowers": "Pickup", "mushrooms": "Harvest",
    "aether cluster": "Harvest", "aether geode": "Harvest", "aether shard": "Harvest",
    "stabilizer": "Repair",
})

SCENARIOS = ["unmooring", "siege", "lockdown", "stormhawk", "rime", "reclaimed", "aether_surge"]


# ==========================================================================
# Reading a finished piece
# ==========================================================================

def openings(p):
    head = p.notes.split("--")[0].upper()
    found = set()
    for word, d in (("NORTH", "N"), ("SOUTH", "S"), ("EAST", "E"), ("WEST", "W")):
        if word in head:
            found.add(d)
    for token in head.replace("|", " ").replace("+", " ").replace(",", " ").split():
        if token in ("N", "S", "E", "W"):
            found.add(token)
    return found


def role(p):
    return p.notes.split("|")[0].strip().split()[0]


def mouth(d, inset=10.0):
    return {"N": (0, HALF - inset, 0), "S": (0, -HALF + inset, 0),
            "E": (HALF - inset, 0, 90), "W": (-HALF + inset, 0, 90)}[d]


def deck_polys(p):
    return [w for w, _, _ in p.slabs]


def in_corridor(p, x, y, half=20.0):
    """The walking line between openings stays clear of dressing."""
    o = openings(p)
    if o & {"N", "S"} and abs(x) < half:
        if ("N" in o and y > -half) or ("S" in o and y < half):
            return True
    if o & {"E", "W"} and abs(y) < half:
        if ("E" in o and x > -half) or ("W" in o and x < half):
            return True
    return False


def poly_area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def edge_dist(poly, x, y):
    best = 1e9
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        best = min(best, math.hypot(x - (ax + dx * t), y - (ay + dy * t)))
    return best


class Ground:
    """The piece's real surface, for honest placement."""

    def __init__(self, p):
        self.bvh = BVHTree.FromPolygons([tuple(v) for v in p.verts], [tuple(f) for f in p.faces])

    def z_at(self, x, y, top=14.0):
        hit = self.bvh.ray_cast(Vector((x, y, top)), Vector((0, 0, -1)), 60.0)
        if hit[0] is None:
            return None
        return hit[0].z, abs(hit[1].z)

    def flat(self, x, y, r, tol=0.3):
        """The surface height if the whole disc of radius r is flat deck."""
        h = self.z_at(x, y)
        if h is None or h[1] < 0.95 or not (-1.0 < h[0] < 8.0):
            return None
        z0 = h[0]
        for k in range(10):
            a = 2 * math.pi * k / 10
            for f in (0.5, 1.0):
                hk = self.z_at(x + math.cos(a) * r * f, y + math.sin(a) * r * f)
                if hk is None or abs(hk[0] - z0) > tol or hk[1] < 0.95:
                    return None
        return z0


class Ctx:
    """Everything a hook needs about one piece -- decks, surface, openings, a
    per-piece random stream -- and the tools that place things honestly."""

    def __init__(self, p, scenario):
        self.p = p
        self.scenario = scenario
        self.rng = random.Random("%s|%s" % (p.name, scenario))
        self.open = openings(p)
        # the aviary's birds circle low over its decks, and the kit proves every
        # orbit clear afterwards (clear_bird_orbits): nothing tall, nothing afloat
        self.flat_only = "aviary" in p.name
        # per-piece character, so no two pieces are dressed alike
        self.density = self.rng.uniform(0.7, 1.35)
        self.wind = self.rng.uniform(0, 2 * math.pi)
        self.refresh()

    def refresh(self):
        self.polys = deck_polys(self.p)
        self.areas = [poly_area(q) for q in self.polys]
        self.ground = Ground(self.p)

    def n(self, lo, hi):
        return max(0, int(round(self.rng.uniform(lo, hi) * self.density)))

    # ---- candidate points ----------------------------------------------
    def uniform(self):
        if not self.polys:
            return None
        poly = self.rng.choices(self.polys, weights=self.areas)[0]
        xs, ys = [q[0] for q in poly], [q[1] for q in poly]
        return self.rng.uniform(min(xs), max(xs)), self.rng.uniform(min(ys), max(ys))

    def edge(self, d0, d1, facing=None):
        """A point d0..d1 in from a deck edge -- the foot of a wall -- and the
        edge's angle. With `facing`, only edges whose outside faces that way."""
        edges = []
        for poly in self.polys:
            n = len(poly)
            cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
            for i in range(n):
                (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
                L = math.hypot(bx - ax, by - ay)
                if L < 4:
                    continue
                nx, ny = (by - ay) / L, -(bx - ax) / L
                mx, my = (ax + bx) / 2, (ay + by) / 2
                if (cx - mx) * nx + (cy - my) * ny < 0:
                    nx, ny = -nx, -ny                      # inward
                if facing is not None and -(nx * math.cos(facing) + ny * math.sin(facing)) < 0.35:
                    continue
                edges.append((ax, ay, bx, by, nx, ny, L))
        if not edges:
            return None
        ax, ay, bx, by, nx, ny, L = self.rng.choices(edges, weights=[e[6] for e in edges])[0]
        t = self.rng.uniform(0.08, 0.92)
        d = self.rng.uniform(d0, d1)
        return ax + (bx - ax) * t + nx * d, ay + (by - ay) * t + ny * d, math.degrees(math.atan2(by - ay, bx - ax))

    def near(self, cx, cy, r0, r1):
        a = self.rng.uniform(0, 2 * math.pi)
        d = r0 + (r1 - r0) * math.sqrt(self.rng.random())
        return cx + math.cos(a) * d, cy + math.sin(a) * d

    # ---- the test every grounded prop passes --------------------------------
    def spot(self, x, y, r, h, corridor=True):
        if corridor and in_corridor(self.p, x, y):
            return None
        z0 = self.ground.flat(x, y, r)
        if z0 is None:
            return None
        shape = ("cyl", x, y, r, z0, z0 + h)
        if any(shapes_clash(shape, s, gap=0.8) for _, s in self.p.solids + self.p.floats):
            return None
        return z0

    def claim(self, label, x, y, r, z0, h):
        self.p.solid(label, x, y, r, z0, z0 + h)

    def put(self, label, shape_fn, r, h, where, s=1.0, rz=None, tries=60, corridor=True, interact=None):
        """Try `where()` candidates until one fits; place the prop there."""
        if self.flat_only and h * s > 1.0:
            return None
        for _ in range(tries):
            c = where()
            if c is None:
                return None
            x, y = c[0], c[1]
            if rz is not None:
                turn = rz
            elif len(c) > 2:
                turn = c[2]
            else:
                turn = self.rng.uniform(0, 360)
            z0 = self.spot(x, y, r * s, h * s, corridor)
            if z0 is None:
                continue
            self.claim(label, x, y, r * s, z0, h * s)
            place(self.p, label, x, y, z0, turn, s, shape_fn)
            if interact is not None:
                self.p.props[-1]["interact"] = interact
            return x, y, z0
        return None

    def air(self, label, r, h, above, around=None, tries=60):
        """A spot `above` studs over the real surface, clear by the float rules."""
        if self.flat_only:
            return None
        for _ in range(tries):
            if around:
                x, y = self.near(*around)
            else:
                x, y = self.rng.uniform(-HALF + 12, HALF - 12), self.rng.uniform(-HALF + 12, HALF - 12)
            g = self.ground.z_at(x, y)
            if g is None:
                continue
            z = g[0] + self.rng.uniform(*above)
            shape = ("cyl", x, y, r, z - h / 2, z + h / 2)
            if free_for_float(self.p, shape):
                self.p.float_(label, x, y, r, z - h / 2, z + h / 2)
                return x, y, z
        return None


def place(p, label, x, y, z, rz, s, shape):
    """One prop: anchored at (x, y, z) turned rz, drawn at scale s. The scale
    goes into the geometry and the turn into the placement, so every copy of a
    shape shares one library mesh."""
    with frame(p, xf(x, y, z, rz)):
        with as_prop(p, label, I4):
            with frame(p, Matrix.Diagonal((s, s, s, 1.0))):
                shape(p)


def add_faces(p, verts, faces, mats, M=I4):
    """Like Piece.add, but one material per face."""
    f0 = len(p.faces)
    p.add(verts, faces, mats[0], M)
    for k, m in enumerate(mats):
        p.fmat[f0 + k] = m


def lump(p, mat, profile, n=7, seed="lump", jitter=0.22, sx=1.0, sy=1.0, cx=0.0, cy=0.0, cz=0.0):
    """A low-poly organic mound: rings through (r, z) stations, each column
    pushed in or out by a fixed seeded jitter so it reads grown, not turned."""
    rng = random.Random(seed)
    cols = [1.0 + rng.uniform(-jitter, jitter) for _ in range(n)]
    rot = rng.uniform(0, 2 * math.pi)
    verts, idx = [], []
    for r, z in profile:
        s = len(verts)
        if r <= 1e-6:
            verts.append((cx, cy, cz + z))
        else:
            for i in range(n):
                a = rot + 2 * math.pi * i / n
                rr = r * cols[i] * (1.0 + rng.uniform(-jitter / 3, jitter / 3))
                verts.append((cx + math.cos(a) * rr * sx, cy + math.sin(a) * rr * sy, cz + z))
        idx.append(list(range(s, len(verts))))
    faces = []
    for A, B in zip(idx, idx[1:]):
        if len(A) > 1 and len(B) > 1:
            faces += [(A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]) for i in range(n)]
        elif len(B) == 1:
            faces += [(A[i], A[(i + 1) % n], B[0]) for i in range(n)]
        else:
            faces += [(A[0], B[(i + 1) % n], B[i]) for i in range(n)]
    if len(idx[0]) > 1:
        faces.append(tuple(reversed(idx[0])))
    if len(idx[-1]) > 1:
        faces.append(tuple(idx[-1]))
    p.add(verts, faces, mat, I4)


def blot(p, mat, x, y, r, seed, z=0.04, h=0.05, n=9, jitter=0.35, sx=1.0, rz=0.0):
    """An irregular flat patch on the deck -- scorch, moss carpet, frost."""
    with frame(p, xf(x, y, 0, rz)):
        lump(p, mat, [(r, z), (r, z + h)], n=n, seed=seed, jitter=jitter, sx=sx)


def row(builder, xs):
    """A blocker: one shape repeated across the 40-stud opening."""
    def shape(p):
        for x in xs:
            with frame(p, xf(x, 0, 0)):
                builder(p)
    return shape


def crack(p, x, y, rng, L=None, w=1.0, mat="Soot", branches=1):
    L = L or rng.uniform(18, 34)
    a = rng.uniform(0, 360)
    px, py = x, y
    for k in range(4):
        seg = L / 4
        a += rng.uniform(-40, 40)
        dx, dy = math.cos(math.radians(a)) * seg, math.sin(math.radians(a)) * seg
        box(p, mat, px + dx / 2, py + dy / 2, 0.07, seg + w * 0.5, w * (1.0 - 0.18 * k), 0.06, rz=a)
        if branches and k == 1:
            crack(p, px, py, rng, L=L * 0.4, w=w * 0.6, mat=mat, branches=0)
        px, py = px + dx, py + dy


def clear_disc(ctx, x, y, r):
    return ctx.ground.flat(x, y, r, tol=0.2) is not None and \
        not any(shapes_clash(("cyl", x, y, r, 0, 0.3), s, gap=0.2) for _, s in ctx.p.solids)


def surface_crack(ctx, L, w=1.0, mat="Soot", near=None):
    """A crack reserves its whole reach on flat deck, so it cannot leave it."""
    for _ in range(40):
        c = near() if near else ctx.uniform()
        if c is None:
            return
        if clear_disc(ctx, c[0], c[1], L * 1.02):   # a crack can wander its full length
            crack(ctx.p, c[0], c[1], ctx.rng, L=L, w=w, mat=mat)
            return


def surface_blot(ctx, mat, r, where, sx=1.0, n=9, jitter=0.35):
    for _ in range(40):
        c = where()
        if c is None:
            return
        if not clear_disc(ctx, c[0], c[1], r * max(sx, 1.0)):
            continue
        blot(ctx.p, mat, c[0], c[1], r, "blot %s %.1f %.1f" % (ctx.p.name, c[0], c[1]), sx=sx, n=n, jitter=jitter,
             rz=c[2] if len(c) > 2 else ctx.rng.uniform(0, 180))
        return


# ==========================================================================
# Structure edits: shells, crumbling, whole-surface looks
# ==========================================================================

def shells(p):
    """Connected pieces of the soup, each with its faces, verts and box."""
    parent = list(range(len(p.verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for f in p.faces:
        r0 = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != r0:
                parent[ri] = r0
    groups = {}
    for fi, f in enumerate(p.faces):
        groups.setdefault(find(f[0]), []).append(fi)
    out = []
    for fl in groups.values():
        vs = {i for fi in fl for i in p.faces[fi]}
        pts = [p.verts[i] for i in vs]
        mn = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
        mx = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
        out.append({"faces": fl, "verts": vs, "min": mn, "max": mx, "c": (mn + mx) / 2})
    return out


def remove_faces(p, drop):
    """Delete faces (and the vertices only they used), keeping p.up in step."""
    drop = set(drop)
    keep = [i for i in range(len(p.faces)) if i not in drop]
    newidx = {old: new for new, old in enumerate(keep)}
    p.up = {newidx[i] for i in p.up if i in newidx}
    faces = [p.faces[i] for i in keep]
    fmat = [p.fmat[i] for i in keep]
    used = sorted({v for f in faces for v in f})
    vmap = {old: new for new, old in enumerate(used)}
    p.verts = [p.verts[i] for i in used]
    p.faces = [[vmap[v] for v in f] for f in faces]
    p.fmat = fmat


def breach_walls(ctx, count):
    """Knock gaps in the parapets and railings, rubble fallen inside and a
    broken chunk of rim hanging from the deck's edge beneath each gap."""
    if ctx.flat_only or count <= 0:
        return []
    p = ctx.p
    rim = []
    for s in shells(p):
        size = s["max"] - s["min"]
        if s["min"].z < -0.3 or s["max"].z > 6.5 or max(size.x, size.y) > 16:
            continue
        cx, cy = s["c"].x, s["c"].y
        if in_corridor(p, cx, cy, half=26) or max(abs(cx), abs(cy)) > HALF - 12:
            continue
        if any(edge_dist(q, cx, cy) < 3.5 for q in ctx.polys):
            rim.append(s)
    drop, done = [], []
    for _ in range(count * 3):
        if not rim or len(done) >= count:
            break
        centre = ctx.rng.choice(rim)
        cx, cy = centre["c"].x, centre["c"].y
        if any(math.hypot(cx - a, cy - b) < 30 for a, b in done):
            continue
        R = ctx.rng.uniform(6, 12)
        hit = [s for s in rim if math.hypot(s["c"].x - cx, s["c"].y - cy) < R]
        for s in hit:
            drop += s["faces"]
            rim.remove(s)
        done.append((cx, cy))
    if not drop:
        return []
    remove_faces(p, drop)
    for cx, cy in done:
        box(p, "CitadelWhite", cx, cy, -DECK_T - 1.2, 5, 3, 3.2, rz=ctx.rng.uniform(0, 90), rx=ctx.rng.uniform(-18, 18))
    ctx.refresh()
    for cx, cy in done:
        poly = min(ctx.polys, key=lambda q: edge_dist(q, cx, cy))
        n = len(poly)
        mx, my = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
        L = math.hypot(mx - cx, my - cy) or 1
        for k in range(ctx.rng.randint(2, 3)):
            d = 5 + 4 * k
            tx, ty = cx + (mx - cx) / L * d, cy + (my - cy) / L * d
            ctx.put("rubble", RUBBLE[ctx.rng.randrange(len(RUBBLE))], 3.2, 3.0,
                    lambda: ctx.near(tx, ty, 0, 3), s=ctx.rng.uniform(0.8, 1.3), corridor=False)
    return done


def crumble_tower(ctx):
    """Break the top off one turret: its walk and roof go, a jagged rim is
    left, and the roof lies where it fell. Never a turret carrying a spire."""
    if ctx.flat_only:
        return False
    p = ctx.p
    towers = [s for lab, s in p.solids if lab == "tower" and s[0] == "cyl"]
    ctx.rng.shuffle(towers)
    sh = shells(p)
    for (_, x, y, R, z0, z1) in towers:
        r = R / 1.25
        H = z1 - 6 - 2.4 * r
        near = [s for s in sh if math.hypot(s["c"].x - x, s["c"].y - y) < r * 1.3]
        if any(s["max"].z >= CROWN_TOP - 0.01 or s["max"].z > z1 + 1.0 for s in near):
            continue
        top = [s for s in near if s["min"].z >= H - 0.5]
        if not top:
            continue
        remove_faces(p, [fi for s in top for fi in s["faces"]])
        for k in range(10):   # the jagged rim of the break
            a = math.radians(36 * k + ctx.rng.uniform(-8, 8))
            hgt = ctx.rng.uniform(0.8, 4.5)
            box(p, "CitadelWhite", x + math.cos(a) * r * 0.86, y + math.sin(a) * r * 0.86, H + hgt / 2 - 0.3,
                r * 0.55, 1.0, hgt, rz=math.degrees(a) + 90, rx=ctx.rng.uniform(-10, 10))
        box(p, "Soot", x, y, H - 0.4, r * 1.5, r * 1.5, 0.3, rz=22.5)
        ctx.refresh()
        ctx.put("fallen roof", shape_fallen_roof, 6.5, 5.5, lambda: ctx.near(x, y, r * 1.8, r * 3.4),
                s=r / 6.0, corridor=False)
        for _ in range(2):
            ctx.put("rubble", RUBBLE[ctx.rng.randrange(len(RUBBLE))], 3.2, 3.0,
                    lambda: ctx.near(x, y, r * 1.3, r * 2.6), s=ctx.rng.uniform(0.9, 1.4), corridor=False)
        return True
    return False


def loosen_islet(ctx):
    """Unmooring: one of the piece's own islets has come loose -- sunk a little
    and tilted, so its bridge no longer meets it. Everything on it goes with it.
    Never the main deck, and never an islet holding the crown landmark."""
    if ctx.flat_only or len(ctx.polys) < 2:
        return False
    p = ctx.p
    main = max(range(len(ctx.polys)), key=lambda i: ctx.areas[i])
    sh = shells(p)
    cands = [i for i in range(len(ctx.polys)) if i != main and ctx.areas[i] > 400]
    ctx.rng.shuffle(cands)
    for i in cands:
        poly = ctx.polys[i]
        n = len(poly)
        cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
        grow = [(cx + (q[0] - cx) * 1.08, cy + (q[1] - cy) * 1.08) for q in poly]
        group = [s for s in sh if _inside((s["c"].x, s["c"].y), grow)]
        # only low islets come loose: a tall landmark tipping would leave the
        # piece's 256-stud box, and the crown must stay where it is
        if any(s["max"].z > 60 or s["min"].z < -80 for s in group):
            continue
        axis = ctx.rng.uniform(0, 360)
        tilt = ctx.rng.uniform(4, 7)
        M = xf(cx, cy, -ctx.rng.uniform(2.0, 3.5)) @ xf(rz=axis) @ xf(rx=tilt) @ xf(rz=-axis) @ xf(-cx, -cy, 0)
        moved = set()
        for s in group:
            for v in s["verts"]:
                if v not in moved:
                    p.verts[v] = M @ p.verts[v]
                    moved.add(v)
        for prop in p.props:
            t = prop["matrix"].translation
            if _inside((t.x, t.y), grow):
                prop["matrix"] = M @ prop["matrix"]
        for fx in p.fixtures:
            t = fx["matrix"].translation
            if _inside((t.x, t.y), grow):
                fx["matrix"] = M @ fx["matrix"]
        ctx.refresh()
        return True
    return False


def face_normal(p, f):
    nx = ny = nz = 0.0
    for i in range(len(f)):
        a, b = p.verts[f[i]], p.verts[f[(i + 1) % len(f)]]
        nx += (a.y - b.y) * (a.z + b.z)
        ny += (a.z - b.z) * (a.x + b.x)
        nz += (a.x - b.x) * (a.y + b.y)
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / L, ny / L, nz / L


def tops(p, zmin=0.4):
    """Faces that are the upward top of their shell, above the floor: wall
    copings, rail tops, tower walks, lintels -- where snow and moss settle."""
    out = []
    for si, s in enumerate(shells(p)):
        if s["max"].z < zmin:
            continue
        for fi in s["faces"]:
            f = p.faces[fi]
            zc = sum(p.verts[i].z for i in f) / len(f)
            if abs(zc - s["max"].z) < 0.02 and abs(face_normal(p, f)[2]) > 0.9:
                out.append((fi, si))
    return out


def recolour(p, mapping, fraction=1.0, rng=None, props_too=True):
    rng = rng or random.Random(0)
    for i, m in enumerate(p.fmat):
        if m in mapping and (fraction >= 1.0 or rng.random() < fraction):
            p.fmat[i] = mapping[m]
    if props_too:
        for prop in p.props:
            prop["mats"] = [mapping.get(m, m) for m in prop["mats"]]


def topple(ctx, labels, chance):
    """Knock standing props over: laid on their side, resting on the deck."""
    for prop in ctx.p.props:
        if prop["label"] not in labels or ctx.rng.random() > chance:
            continue
        t = prop["matrix"].translation
        R = (xf(rz=ctx.rng.uniform(0, 360)) @ xf(rx=90)).to_3x3()
        pts = [R @ v for v in prop["verts"]]
        reach = max(math.hypot(q.x, q.y) for q in pts)
        z0 = ctx.ground.flat(t.x, t.y, reach + 0.5, tol=0.3)
        if z0 is None or any(shapes_clash(("cyl", t.x, t.y, reach, z0, z0 + 2), s, gap=0.3)
                             for lab, s in ctx.p.solids if lab not in ("tower", "spire")):
            continue
        prop["matrix"] = Matrix.Translation((t.x, t.y, z0 - min(q.z for q in pts))) @ R.to_4x4()
        if prop["label"] in ("lamp", "light pillar"):
            prop["interact"] = "Repair"


# ==========================================================================
# The prop vocabulary. Every shape is built at the origin on z = 0 and is
# fixed (any randomness seeded by its own name), so a shape is one mesh.
# ==========================================================================

def _rubble(seed, n):
    def shape(p):
        rng = random.Random(seed)
        for k in range(n):
            sx, sy, sz = rng.uniform(1.2, 3.0), rng.uniform(1.0, 2.4), rng.uniform(0.8, 1.8)
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(0, 1.8)
            box(p, rng.choice(("CitadelWhite", "CitadelWhite", "PaleAlloy")), math.cos(a) * d, math.sin(a) * d,
                sz / 2 + (0.6 if k > n // 2 else 0), sx, sy, sz, rz=rng.uniform(0, 90), rx=rng.uniform(-12, 12))
    return shape


RUBBLE = [_rubble("rubble a", 5), _rubble("rubble b", 7), _rubble("rubble c", 4)]


def shape_fallen_roof(p):
    with frame(p, xf(0, 0, 2.6, 0, 0, 78)):
        frustum(p, "CitadelViolet", 8, 5.4, 0, -2, 12)
    crystal(p, "SunGold", 12.5, 0, 1.0, 0.8, 1.6, 1.0)


# ---- siege ---------------------------------------------------------------

def shape_warship(p):
    """A raider warship, ~72 long: rust hull, two masts, tattered sails, a
    stern castle, a ram, and ember drives -- the raiders' answer to the
    citadel's azure. Prow toward +X; the frame's z = 0 is its deck."""
    xs = [-34, -28, -16, 0, 14, 24, 31, 36]
    ws = [5.6, 7.4, 8.2, 8.2, 7.6, 5.8, 3.2, 0.0]
    ds = [6.0, 8.5, 9.5, 9.5, 9.0, 7.5, 4.5, 1.5]
    prof = [(-1.0, 0.0), (-0.92, -0.45), (-0.5, -0.85), (0.0, -1.0), (0.5, -0.85), (0.92, -0.45), (1.0, 0.0)]
    verts, faces, mats, rings = [], [], [], []
    for x, w, d in zip(xs, ws, ds):
        s = len(verts)
        if w <= 1e-6:
            verts.append((x, 0.0, -0.6))
        else:
            verts += [(x, fy * w, fz * d) for fy, fz in prof]
        rings.append(list(range(s, len(verts))))
    band = {0: "RaiderRust", 5: "RaiderRust", 1: "DeepAlloy", 4: "DeepAlloy", 2: "Soot", 3: "Soot", 6: "Twig"}
    n = len(prof)
    for A, B in zip(rings, rings[1:]):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((A[j], A[j2], B[0]) if len(B) == 1 else (A[j], A[j2], B[j2], B[j]))
            mats.append(band[j])
    faces.append(tuple(reversed(rings[0])))
    mats.append("RaiderRust")
    add_faces(p, verts, faces, mats)
    for sy in (-1, 1):
        box(p, "Twig", 0, sy * 7.4, 0.6, 50, 0.5, 1.2)
    box(p, "RaiderRust", -24, 0, 3.0, 12, 12.5, 6)
    box(p, "Twig", -24, 0, 6.2, 12.6, 13.1, 0.5)
    for sy in (-1, 1):
        for x in (-28, -24, -20):
            box(p, "EmberGlow", x, sy * 6.3, 3.4, 1.6, 0.2, 1.4)
    for mx, h in ((-6, 30.0), (14, 26.0)):
        frustum(p, "DeepAlloy", 8, 0.9, 0.5, 0, h, mx, 0)
        frustum(p, "Twig", 8, 1.8, 1.8, h * 0.78, h * 0.78 + 1.2, mx, 0)
        box(p, "DeepAlloy", mx, 0, h * 0.9, 0.6, 17, 0.6)
        box(p, "DeepAlloy", mx, 0, h * 0.45, 0.6, 15, 0.6)
        box(p, "RaiderRust", mx + 0.4, 0, h * 0.675, 0.3, 15.5, h * 0.42)
        box(p, "Char", mx + 0.45, -4, h * 0.5, 0.3, 3.0, 2.2, rx=12)            # a patched tear
    box(p, "RaiderRust", -6, 0, 31.5, 0.3, 0.3, 3.0)
    box(p, "RaiderRust", -6, 2.2, 32.4, 0.2, 4.4, 1.6)                          # the pennant
    with frame(p, xf(35.5, 0, -1.6, 0, 0, 90)):
        frustum(p, "Soot", 4, 1.9, 0.0, 0, 7.0, rot=45)                         # the ram
    for sy in (-3.2, 3.2):
        with frame(p, xf(-34.5, sy, -3.4, 0, 0, -90)):
            frustum(p, "DeepAlloy", 8, 2.0, 1.6, 0, 3.0)
            frustum(p, "EmberGlow", 8, 1.5, 1.5, 3.0, 3.4)
    for sy in (-1, 1):
        for gx in (-8, 2, 12):
            with frame(p, xf(gx, sy * 7.8, 1.3, 0, sy * -90, 0)):
                frustum(p, "DeepAlloy", 8, 0.55, 0.45, 0, 2.6)


def shape_gangway(p):
    box(p, "Twig", 5, 0, -0.55, 10, 3.2, 0.35, ry=6)
    for sy in (-1.5, 1.5):
        box(p, "DeepAlloy", 5, sy, 0.35, 10, 0.2, 0.2, ry=6)
        for gx in (1, 5, 9):
            box(p, "DeepAlloy", gx, sy, -0.1 - gx * 0.1, 0.2, 0.2, 1.1)


def shape_tent(p):
    box(p, "RaiderRust", 0, -2.2, 2.6, 10, 0.4, 6.4, rx=-35)
    box(p, "RaiderRust", 0, 2.2, 2.6, 10, 0.4, 6.4, rx=35)
    box(p, "DeepAlloy", 0, 0, 5.3, 10.6, 0.6, 0.6)
    box(p, "Char", 5.05, 0, 1.6, 0.2, 2.2, 3.0)            # the door flap
    for sx in (-5.2, 5.2):
        frustum(p, "DeepAlloy", 4, 0.3, 0.3, 0, 5.6, sx, 0)


def shape_yurt(p):
    frustum(p, "RaiderRust", 8, 4.2, 4.0, 0, 3.0)
    frustum(p, "Char", 8, 4.6, 0.6, 3.0, 5.6)
    frustum(p, "DeepAlloy", 8, 0.7, 0.3, 5.6, 7.0)
    box(p, "Twig", 4.0, 0, 1.2, 0.6, 2.0, 2.4)


def shape_stake_wall(p):
    for k in range(7):
        with frame(p, xf(-6 + 2 * k, 0, 0, 0, -18 + (k % 2) * 6, 0)):
            frustum(p, "Twig", 4, 0.35, 0.0, 0, 4.2 + (k % 3) * 0.5, rot=45)
    box(p, "Bark", 0, 0.6, 1.2, 14, 0.4, 0.4)
    box(p, "Bark", 0, 0.9, 2.4, 14, 0.4, 0.4)


def shape_barricade(p):
    box(p, "PaleAlloy", -3, 0, 1.3, 3, 3, 2.6)
    box(p, "PaleAlloy", 3, 0, 1.3, 3, 3, 2.6, rz=8)
    box(p, "RaiderRust", 0, 0.4, 2.8, 9, 0.5, 1.2, rx=10)
    box(p, "Twig", 0, -0.8, 1.0, 8, 0.3, 1.8, rx=-20)


def shape_barrels(p):
    for (x, y, z) in ((0, 0, 0), (1.9, 0.4, 0), (0.9, 1.7, 0), (1.0, 0.7, 2.2)):
        frustum(p, "RaiderRust", 8, 0.9, 0.9, z, z + 2.1, x, y)
        for hz in (0.35, 1.75):
            frustum(p, "DeepAlloy", 8, 0.95, 0.95, z + hz, z + hz + 0.15, x, y)


def shape_loot(p):
    box(p, "Twig", 0, 0, 0.7, 3.4, 2.2, 1.4)
    box(p, "DeepAlloy", 0, 0, 0.7, 3.5, 2.3, 0.3)
    rng = random.Random("loot")
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(1.8, 3.2)
        crystal(p, "SunGold", math.cos(a) * d, math.sin(a) * d, 0.25, rng.uniform(0.3, 0.6), 0.5, 0.25, n=5)
    crystal(p, "SunGold", 0, 0, 1.9, 0.9, 1.0, 0.5, n=6)


def shape_campfire(p):
    blot(p, "Char", 0, 0, 2.6, "campfire char", h=0.04)
    for k in range(8):
        a = math.radians(45 * k)
        box(p, "HullSlate", math.cos(a) * 2.2, math.sin(a) * 2.2, 0.35, 0.9, 0.7, 0.7, rz=45 * k)
    for k in range(3):
        box(p, "Bark", 0, 0, 0.35 + 0.1 * k, 3.2, 0.5, 0.5, rz=60 * k)
    for k, (a, h) in enumerate(((0.3, 2.2), (2.3, 1.5), (4.2, 1.9), (5.5, 1.2))):
        crystal(p, "EmberGlow", math.cos(a) * 0.5, math.sin(a) * 0.5, 0.5, 0.45, h, 0.01, n=4, rz=30 * k)


def shape_bonfire(p):
    shape_campfire(p)
    for k in range(4):   # the smoke column, leaning downwind, thinning as it climbs
        lump(p, "Smoke", [(1.6 + k * 0.5, 0), (1.9 + k * 0.6, 1.4 + k * 0.3), (0, 2.6 + k * 0.5)], n=7,
             seed="smoke %d" % k, cx=0.9 * k, cy=0.2 * k, cz=3.0 + k * 3.0)


def shape_raider_banner(p):
    frustum(p, "DeepAlloy", 6, 0.3, 0.25, 0, 11, 0, 0)
    box(p, "DeepAlloy", 1.6, 0, 10.5, 3.6, 0.3, 0.3)
    box(p, "RaiderRust", 1.6, 0, 8.0, 3.2, 0.2, 4.6)
    box(p, "RaiderRust", 2.6, 0, 5.2, 1.2, 0.2, 1.2)          # the torn tail
    crystal(p, "Bone", 0, 0, 11.4, 0.5, 0.8, 0.3)


def shape_ballista(p):
    box(p, "DeepAlloy", 0, 0, 0.6, 3.2, 3.2, 1.2)
    frustum(p, "DeepAlloy", 6, 0.6, 0.5, 1.2, 2.6, 0, 0)
    with frame(p, xf(0, 0, 2.8, 0, -12, 0)):
        box(p, "Twig", 1.0, 0, 0, 5.2, 0.6, 0.6)
        box(p, "Twig", 1.4, 0, 0, 0.5, 6.4, 0.5)
        box(p, "RaiderRust", 3.8, 0, 0.1, 2.4, 0.25, 0.25)


# ---- lockdown ---------------------------------------------------------------

def shape_sentinel(p):
    frustum(p, "DeepAlloy", 6, 1.8, 1.4, 0, 1.2, 0, 0)
    frustum(p, "PaleAlloy", 4, 1.1, 0.7, 1.2, 7.5, 0, 0, rot=45)
    crystal(p, "AlarmRed", 0, 0, 8.6, 0.9, 1.3, 1.0, n=4)


def shape_turret(p):
    frustum(p, "DeepAlloy", 8, 2.4, 2.0, 0, 1.4)
    frustum(p, "PaleAlloy", 8, 1.2, 1.0, 1.4, 3.4)
    lump(p, "PaleAlloy", [(2.0, 3.4), (1.8, 4.6), (1.0, 5.5), (0, 5.8)], n=8, seed="turret dome", jitter=0.0)
    box(p, "DeepAlloy", 2.4, 0, 4.4, 3.2, 0.7, 0.7)
    crystal(p, "AlarmRed", 1.6, 0, 5.0, 0.35, 0.45, 0.3, n=4)


def shape_alarm_post(p):
    frustum(p, "DeepAlloy", 6, 0.9, 0.7, 0, 0.6)
    frustum(p, "PaleAlloy", 6, 0.35, 0.3, 0.6, 7.5)
    frustum(p, "DeepAlloy", 6, 0.8, 0.8, 7.5, 7.8)
    crystal(p, "AlarmRed", 0, 0, 8.6, 0.7, 1.0, 0.8, n=6)
    frustum(p, "DeepAlloy", 6, 0.8, 0.2, 9.6, 10.2)


def shape_laser_fence(p):
    for x in (-4, 4):
        frustum(p, "DeepAlloy", 4, 0.7, 0.5, 0, 5, x, 0, rot=45)
        crystal(p, "AlarmRed", x, 0, 5.4, 0.4, 0.6, 0.3, n=4)
    for z in (1.2, 2.6, 4.0):
        box(p, "AlarmRed", 0, 0, z, 7.6, 0.12, 0.12)


def shape_console(p):
    box(p, "DeepAlloy", 0, 0, 0.6, 2.4, 1.6, 1.2)
    box(p, "PaleAlloy", 0, 0, 1.6, 2.2, 1.2, 0.8, rx=-25)
    box(p, "AlarmDim", 0, -0.35, 2.05, 1.8, 0.1, 0.6, rx=-25)
    for k in range(3):
        box(p, "AlarmRed", -0.6 + 0.6 * k, 0.4, 1.3, 0.3, 0.3, 0.15)


def shape_drone(p):
    lump(p, "DeepAlloy", [(0.5, -0.9), (1.1, -0.3), (1.1, 0.3), (0.5, 0.9)], n=8, seed="drone", jitter=0.0)
    torus(p, "PaleAlloy", 1.4, 0.15, 0, 0, 0, n=12)
    crystal(p, "AlarmRed", 1.0, 0, 0, 0.3, 0.35, 0.3, n=4)


# ---- stormhawk --------------------------------------------------------------

def shape_nest(p):
    R = 7.0
    for k in range(20):
        a = 18 * k
        box(p, "Twig", math.cos(math.radians(a)) * R, math.sin(math.radians(a)) * R, 1.0 + (k % 3) * 0.35,
            7.5, 0.6, 0.6, rz=a + 90 + (k % 3 - 1) * 14, rx=(k % 2) * 16 - 8)
    for k in range(12):
        a = 30 * k + 9
        box(p, "Bark", math.cos(math.radians(a)) * (R + 1.2), math.sin(math.radians(a)) * (R + 1.2), 0.5,
            6.0, 0.5, 0.5, rz=a + 70, rx=10)
    frustum(p, "Twig", 10, R - 1.5, R + 0.5, 0.0, 1.2, 0, 0)
    for k in range(3):
        a = math.radians(120 * k + 20)
        lump(p, "Bone", [(0.8, 1.2), (1.0, 1.9), (0.6, 2.7), (0, 3.0)], n=7, seed="egg %d" % k, jitter=0.05,
             cx=math.cos(a) * 1.5, cy=math.sin(a) * 1.5)


def shape_eggshells(p):
    for k, (x, y) in enumerate(((0, 0), (1.3, 0.6), (0.4, 1.4))):
        lump(p, "Bone", [(0.9, 0), (0.95, 0.5), (0.7, 0.9)], n=7, seed="shell %d" % k, jitter=0.25, cx=x, cy=y)


def shape_bones(p):
    rng = random.Random("bones")
    for k in range(7):
        box(p, "Bone", rng.uniform(-2, 2), rng.uniform(-1.5, 1.5), 0.25, rng.uniform(1.8, 3.4), 0.4, 0.4,
            rz=rng.uniform(0, 180))
    lump(p, "Bone", [(0.9, 0), (1.1, 0.8), (0.8, 1.4), (0, 1.6)], n=7, seed="skull", jitter=0.12, cx=1.4, cy=-0.8)


def shape_fallen_feather(p):
    box(p, "DeepAlloy", 0, 0, 0.08, 6.0, 1.0, 0.14)
    box(p, "SunGold", 2.1, 0, 0.1, 1.8, 1.05, 0.14)
    box(p, "DeepAlloy", 0.5, 1.2, 0.08, 4.0, 0.8, 0.14, rz=18)


# ---- rime -----------------------------------------------------------------

def _drift(seed, sx):
    def shape(p):
        lump(p, "Snow", [(3.0, 0), (2.6, 1.1), (1.6, 2.1), (0, 2.6)], n=8, seed=seed, jitter=0.28, sx=sx)
    return shape


DRIFTS = [_drift("drift a", 2.0), _drift("drift b", 1.4), _drift("drift c", 2.6)]


def _ice(seed, n):
    def shape(p):
        rng = random.Random(seed)
        for k in range(n):
            a = rng.uniform(0, 2 * math.pi)
            d = 0 if k == 0 else rng.uniform(0.8, 2.2)
            lean = rng.uniform(-14, 14) if k else 0.0
            with frame(p, xf(math.cos(a) * d, math.sin(a) * d, 0, rng.uniform(0, 72), lean, lean * 0.6)):
                crystal(p, "Ice", 0, 0, 0, rng.uniform(0.5, 1.1) * (1.4 if k == 0 else 1.0),
                        rng.uniform(2.5, 6.0) * (1.6 if k == 0 else 1.0), 0.01, n=5)
    return shape


ICE_SPIKES = [_ice("ice a", 5), _ice("ice b", 3), _ice("ice c", 7)]
FROST = _ice("frost a", 4)


def shape_frozen_figure(p):
    lump(p, "Ice", [(2.2, 0), (2.4, 2.0), (1.8, 4.2), (0.9, 5.4), (0, 5.8)], n=7, seed="ice block", jitter=0.15)
    box(p, "DeepAlloy", 0.9, 1.9, 4.6, 0.8, 0.8, 0.9)                       # a head breaking the surface
    box(p, "DeepAlloy", -1.7, 1.2, 3.4, 0.5, 0.5, 2.2, rx=30, ry=-20)       # a reaching arm
    crystal(p, "SunGold", 1.9, -1.2, 2.2, 0.3, 0.5, 0.3)                    # something gold, frozen in


# ---- reclaimed --------------------------------------------------------------

def _moss(seed):
    def shape(p):
        lump(p, "Moss", [(3.2, 0), (3.0, 0.4), (2.0, 0.9), (0, 1.1)], n=9, seed=seed, jitter=0.3, sx=1.3)
        lump(p, "MossLight", [(1.6, 0.5), (1.4, 1.1), (0, 1.5)], n=7, seed=seed + " top", jitter=0.3, cx=0.8, cy=0.3)
        lump(p, "MossLight", [(1.0, 0.2), (0.8, 0.7), (0, 0.9)], n=6, seed=seed + " side", jitter=0.3, cx=-2.4, cy=-0.6)
    return shape


MOSS = [_moss("moss a"), _moss("moss b"), _moss("moss c")]


def _bush(seed, lobes):
    def shape(p):
        rng = random.Random(seed)
        for k in range(lobes):
            a = rng.uniform(0, 2 * math.pi)
            d = 0 if k == 0 else rng.uniform(0.9, 1.8)
            r = rng.uniform(1.2, 1.9)
            lump(p, "Moss" if k % 2 else "Verdure", [(r * 0.6, 0), (r, r * 0.7), (r * 0.8, r * 1.4), (0, r * 1.7)],
                 n=7, seed="%s %d" % (seed, k), jitter=0.2, cx=math.cos(a) * d, cy=math.sin(a) * d,
                 cz=0 if k == 0 else rng.uniform(0, 0.6))
    return shape


BUSHES = [_bush("bush a", 4), _bush("bush b", 3), _bush("bush c", 6)]


def shape_fern(p):
    for k in range(9):
        with frame(p, xf(0, 0, 0.2, 40 * k)):
            box(p, "MossLight" if k % 2 else "Verdure", 1.4, 0, 0.9, 3.0, 0.5, 0.12, ry=-38)


def shape_flowers(p):
    rng = random.Random("flowers")
    blot(p, "Moss", 0, 0, 2.0, "flower bed", h=0.1)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1.8)
        x, y = math.cos(a) * d, math.sin(a) * d
        frustum(p, "Verdure", 4, 0.08, 0.06, 0.1, 0.9, x, y)
        crystal(p, rng.choice(("SunGold", "CitadelViolet", "Snow")), x, y, 1.0, 0.3, 0.2, 0.15, n=5)


def shape_sapling(p):
    frustum(p, "Bark", 6, 0.6, 0.35, 0, 5.5)
    box(p, "Bark", 0.8, 0, 4.2, 2.0, 0.3, 0.3, ry=-40)
    lump(p, "Verdure", [(1.8, 4.6), (2.6, 6.0), (2.0, 7.6), (0, 8.4)], n=8, seed="sapling crown", jitter=0.2)
    lump(p, "Moss", [(1.2, 5.2), (1.6, 6.0), (0, 7.0)], n=7, seed="sapling side", jitter=0.2, cx=1.6, cy=0.4)


def shape_mushrooms(p):
    for k, (x, y, h, r) in enumerate(((0, 0, 1.6, 1.0), (1.1, 0.5, 1.0, 0.6), (-0.8, 0.9, 1.3, 0.7),
                                       (0.3, -1.0, 0.8, 0.5))):
        frustum(p, "Bone", 6, r * 0.3, r * 0.25, 0, h, x, y)
        lump(p, "Snow" if k % 2 else "CitadelViolet", [(r, h), (r * 0.8, h + r * 0.4), (0, h + r * 0.6)], n=7,
             seed="cap %d" % k, jitter=0.1, cx=x, cy=y)


def roots(ctx, count):
    """Roots crawling in across the deck from its edge -- surface, structure."""
    for _ in range(count):
        c = ctx.edge(0.5, 1.5)
        if c is None:
            return
        x, y, a = c
        heading = a + 90 + ctx.rng.uniform(-35, 35)
        # point the root inward
        if not any(_inside((x + math.cos(math.radians(heading)) * 3, y + math.sin(math.radians(heading)) * 3), q)
                   for q in ctx.polys):
            heading += 180
        for k in range(ctx.rng.randint(3, 6)):
            L = ctx.rng.uniform(2.5, 4.5)
            nx, ny = x + math.cos(math.radians(heading)) * L, y + math.sin(math.radians(heading)) * L
            mx, my = (x + nx) / 2, (y + ny) / 2
            if not clear_disc(ctx, mx, my, 0.8):
                break
            box(ctx.p, "Bark", mx, my, 0.22, L + 0.4, 0.55 - 0.06 * k, 0.4, rz=heading)
            heading += ctx.rng.uniform(-30, 30)
            x, y = nx, ny


def ivy(ctx, chance=0.7):
    """Ivy climbing the turrets, pressed to their walls (structure)."""
    for lab, s in list(ctx.p.solids):
        if lab != "tower" or s[0] != "cyl" or ctx.rng.random() > chance:
            continue
        _, x, y, R, z0, z1 = s
        r = R / 1.25
        Hbody = z1 - 6 - 2.4 * r
        H = min(Hbody - 1, ctx.rng.uniform(12, 30))
        for _k in range(ctx.rng.randint(2, 4)):
            a = ctx.rng.uniform(0, 2 * math.pi)
            for j in range(int((H - 3) / 2.2)):
                z = 4.2 + j * 2.2
                rr = r * (1.0 - 0.06 * z / max(Hbody, 1)) + 0.2
                aj = a + ctx.rng.uniform(-0.08, 0.08)
                box(ctx.p, "Moss" if j % 3 else "MossLight", x + math.cos(aj) * rr, y + math.sin(aj) * rr, z,
                    ctx.rng.uniform(1.2, 2.6), 0.3, 2.4, rz=math.degrees(aj) + 90)


# ---- aether -------------------------------------------------------------------

def _aether(seed, n, tall, spread, outward):
    def shape(p):
        rng = random.Random(seed)
        for k in range(n):
            a = rng.uniform(0, 2 * math.pi)
            d = 0 if k == 0 else rng.uniform(0.6, spread)
            tilt = outward * (d / spread) * 28
            with frame(p, xf(math.cos(a) * d, math.sin(a) * d, 0, math.degrees(a), 0, tilt)):
                crystal(p, "AetherBloom" if k % 2 == 0 else "SkyGlass", 0, 0, 0,
                        rng.uniform(0.6, 1.1) * (1.5 if k == 0 else 1.0),
                        rng.uniform(2.5, 5.0) * (tall if k == 0 else 1.0), 0.01, n=5)
    return shape


AETHER = [_aether("aether a", 6, 2.2, 2.2, 1.0), _aether("aether b", 9, 1.3, 3.0, 1.6),
          _aether("aether c", 4, 3.4, 1.6, 0.6)]


def shape_geode(p):
    blot(p, "AetherDim", 0, 0, 2.4, "geode core", h=0.12)
    for k in range(9):
        a = 40 * k
        with frame(p, xf(math.cos(math.radians(a)) * 2.6, math.sin(math.radians(a)) * 2.6, 0, a, 0, 32)):
            crystal(p, "AetherBloom" if k % 2 else "SkyGlass", 0, 0, 0, 0.6, 2.6 + (k % 3) * 0.8, 0.01, n=5)


# ---- unmooring ----------------------------------------------------------------

def shape_stabilizer(p):
    frustum(p, "DeepAlloy", 8, 2.2, 1.8, 0, 1.2)
    frustum(p, "PaleAlloy", 8, 0.8, 0.7, 1.2, 7.0)
    for z in (2.6, 4.2, 5.8):
        torus(p, "AzureDim", 1.6, 0.25, 0, 0, z, n=12)
    crystal(p, "AzureNeon", 0, 0, 8.0, 0.9, 1.6, 1.0, n=6)


def shape_hazard_beacon(p):
    frustum(p, "DeepAlloy", 4, 0.8, 0.6, 0, 0.5, rot=45)
    frustum(p, "SunGold", 4, 0.3, 0.3, 0.5, 4.0, rot=45)
    crystal(p, "EmberGlow", 0, 0, 4.6, 0.5, 0.8, 0.5, n=4)


def shape_fragment(p):
    box(p, "CitadelWhite", 0, 0, 0, 7.0, 4.2, 2.2)
    box(p, "AzureDim", 0, 0, -1.3, 4, 2.5, 0.6)
    frustum(p, "HullSlate", 5, 2.0, 0, -1.4, -5, 0, 0)


# ==========================================================================
# Anchors and blockers
# ==========================================================================

def add_anchor(p, kind, x, y, z=0.0, note=""):
    p.anchors.append({"kind": kind, "pos": (x, y, z), "note": note})


def anchors_on_decks(ctx, kinds, notes=None):
    counts = {"COMBAT": {"ENEMY_POST": 4, "RESOURCE": 2, "EVENT": 1},
              "PATH": {"ENEMY_POST": 1, "RESOURCE": 1},
              "SIDE": {"DISCOVERY": 2, "RESOURCE": 2},
              "CAP": {"DISCOVERY": 1, "RESOURCE": 1},
              "BOSS": {"EVENT": 2},
              "ENTRY": {"NPC_POST": 2}}.get(role(ctx.p), {})
    notes = notes or {}
    for kind, n in counts.items():
        for _ in range(kinds.get(kind, n)):
            for _t in range(40):
                c = ctx.uniform()
                if c is None:
                    break
                z0 = ctx.spot(c[0], c[1], 2.0, 3.0)
                if z0 is not None:
                    ctx.claim("anchor " + kind.lower(), c[0], c[1], 2.0, z0, 3.0)
                    add_anchor(ctx.p, kind, c[0], c[1], z0, notes.get(kind, ""))
                    break
    for d in sorted(ctx.open):
        x, y, _ = mouth(d)
        add_anchor(ctx.p, "BLOCKER", x, y, note=d)


def reserve_blockers(p):
    for d in openings(p):
        x, y, _ = mouth(d)
        p.solid("blocker", x, y, 8, 0, 14)


def blockers(ctx, shape):
    """One per opening, as a prop: the run decides which sockets it closes.
    Every blocker of a scenario is the same shape."""
    for d in ctx.open:
        x, y, rz = mouth(d)
        with frame(ctx.p, xf(x, y, 0, rz)):
            with as_prop(ctx.p, "blocker", I4):
                shape(ctx.p)


def float_prop(ctx, label, shape, r, h, above, around=None, tilt=0.0):
    at = ctx.air(label, r, h, above, around)
    if at:
        x, y, z = at
        with frame(ctx.p, xf(x, y, z, ctx.rng.uniform(0, 360), rx=ctx.rng.uniform(-tilt, tilt))):
            with as_prop(ctx.p, label, I4):
                shape(ctx.p)
    return at


# ==========================================================================
# The seven hooks
# ==========================================================================

def warship(ctx, n=1):
    """Moor raider warships alongside the decks, gangway to the rail -- only
    where one really fits, by the kit's own float rules, clear of skyways."""
    p = ctx.p
    if ctx.flat_only or not ctx.polys:
        return 0
    xs = [q[0] for poly in ctx.polys for q in poly]
    ys = [q[1] for poly in ctx.polys for q in poly]
    sides = ["E", "W", "N", "S"]
    ctx.rng.shuffle(sides)
    placed = 0
    for side in sides:
        if placed >= n:
            break
        for _t in range(30):
            along = ctx.rng.uniform(-44, 44)
            gap = ctx.rng.uniform(3.0, 6.0)
            sgn = 1 if side in ("E", "N") else -1
            # the hull runs along the deck edge (its prow is +X in its own
            # frame); its guns reach 10.4 either side of the keel line
            if side in ("E", "W"):
                edge = max(xs) if side == "E" else min(xs)
                cx, cy, rz = edge + (gap + 10.8) * sgn, along, 90
                shape = ("box", cx - 10.8, cx + 10.8, cy - 44, cy + 44, -11.0, 34.0)
                blocked = side in ctx.open and abs(cy) < 66
                rail = (cx - (gap + 12.3) * sgn, cy)
                behind = (rail[0] - 6.0 * sgn, cy)
            else:
                edge = max(ys) if side == "N" else min(ys)
                cx, cy, rz = along, edge + (gap + 10.8) * sgn, 0
                shape = ("box", cx - 44, cx + 44, cy - 10.8, cy + 10.8, -11.0, 34.0)
                blocked = side in ctx.open and abs(cx) < 66
                rail = (cx, cy - (gap + 12.3) * sgn)
                behind = (cx, rail[1] - 6.0 * sgn)
            if blocked or not free_for_float(p, shape):
                continue
            # the deck behind the rail must be real, flat deck; the gangway then
            # rests on whatever the rail is -- wall top, kerb or open edge
            z0 = ctx.ground.flat(behind[0], behind[1], 3.0)
            top = ctx.ground.z_at(rail[0], rail[1])
            if z0 is None or top is None or top[1] < 0.9 or not (z0 - 0.5 < top[0] < z0 + 4.0):
                continue
            p.floats.append(("raider warship", shape))
            place(p, "raider warship", cx, cy, z0 - 1.2, rz + ctx.rng.choice((0, 180)), 1.0, shape_warship)
            to_ship = math.degrees(math.atan2(cy - rail[1], cx - rail[0]))
            place(p, "gangway", rail[0] - math.cos(math.radians(to_ship)) * 1.5,
                  rail[1] - math.sin(math.radians(to_ship)) * 1.5, top[0], to_ship, 1.0, shape_gangway)
            placed += 1
            break
    return placed


def dress_siege(ctx):
    p, rng = ctx.p, ctx.rng
    breach_walls(ctx, rng.randint(1, 2))
    if rng.random() < 0.6:
        crumble_tower(ctx)
    for _ in range(ctx.n(4, 7)):   # ragged burns, with the camp's fires nearby
        surface_blot(ctx, "Char", rng.uniform(1.8, 3.6), ctx.uniform, sx=rng.uniform(1.0, 1.5), n=11, jitter=0.5)
    if role(p) in ("COMBAT", "PATH", "BOSS", "ENTRY"):
        warship(ctx, n=2 if role(p) == "COMBAT" and rng.random() < 0.35 else 1)
    camp = None   # the raiders' camp: one site per piece, everything round it
    for _ in range(60):
        c = ctx.uniform()
        if c and not in_corridor(p, c[0], c[1]) and ctx.ground.flat(c[0], c[1], 6.0) is not None:
            camp = c
            break
    if camp:
        cx, cy = camp
        ctx.put("bonfire", shape_bonfire, 2.8, 16.0, lambda: ctx.near(cx, cy, 0, 4), s=1.3, corridor=False)
        for _ in range(ctx.n(2, 4)):
            ctx.put("raider tent", shape_tent, 5.6, 5.8, lambda: ctx.near(cx, cy, 8, 22))
        for _ in range(ctx.n(0, 2)):
            ctx.put("raider yurt", shape_yurt, 4.8, 7.0, lambda: ctx.near(cx, cy, 8, 24))
        for _ in range(ctx.n(2, 4)):
            ctx.put("barrel", shape_barrels, 2.4, 4.4, lambda: ctx.near(cx, cy, 4, 16))
        ctx.put("loot pile", shape_loot, 3.4, 2.6, lambda: ctx.near(cx, cy, 3, 10))
        ctx.put("raider banner", shape_raider_banner, 1.2, 12.0, lambda: ctx.near(cx, cy, 5, 12))
    for _ in range(ctx.n(2, 4)):
        ctx.put("campfire", shape_campfire, 2.8, 3.0, ctx.uniform)
    for d in ctx.open:   # defences face the openings
        mx, my, _ = mouth(d, inset=60)
        turn = 0 if d in ("N", "S") else 90
        ctx.put("stake wall", shape_stake_wall, 7.2, 5.0, lambda: ctx.near(mx, my, 6, 26), rz=turn + rng.uniform(-15, 15))
        ctx.put("barricade", shape_barricade, 5.0, 3.2, lambda: ctx.near(mx, my, 4, 24), rz=turn + rng.uniform(-25, 25))
    for _ in range(ctx.n(0, 2)):
        ctx.put("ballista", shape_ballista, 2.8, 4.0, lambda: ctx.edge(4, 10))
    for prop in p.props:
        if prop["label"] in ("crate", "container"):
            prop["interact"] = "Loot"
    topple(ctx, ("banner", "lamp", "crate"), 0.3)
    recolour(p, {"CitadelViolet": "Char"}, fraction=0.35, rng=rng, props_too=False)
    blockers(ctx, lambda p: (shape_stake_wall(p), row(shape_barrels, (-12, 10))(p)))
    anchors_on_decks(ctx, {"ENEMY_POST": 6, "NPC_POST": 2},
                     {"NPC_POST": "citadel defenders hold here, or a captive to free"})


def dress_lockdown(ctx):
    p, rng = ctx.p, ctx.rng
    recolour(p, {"AzureNeon": "AlarmRed", "AzureDim": "AlarmDim"})
    for d in ctx.open:
        x, y, rz = mouth(d, inset=14)
        p.solid("lockdown field", x, y, 22, 0, 20)
        with frame(p, xf(x, y, 0, rz)):
            with as_fixture(p, "FORCEFIELD", I4):
                with fixture_part(p, "Field"):
                    box(p, "SkyGlass", 0, 0, 9, 40, 0.6, 18)
            for sx in (-21, 21):
                with as_prop(p, "sentinel pylon", xf(sx, 0, 0)):
                    frustum(p, "PaleAlloy", 4, 1.4, 1.2, 0, 19, sx, 0, rot=45)
                    crystal(p, "AlarmRed", sx, 0, 20.5, 0.8, 1.4, 0.8)
                p.props[-1]["interact"] = "Destroy"
    for d in ctx.open:   # red warning chevrons painted toward every opening
        for k in range(3):
            mx, my, turn = mouth(d, inset=40 + 9 * k)
            if ctx.ground.flat(mx, my, 6.0, tol=0.2) is None:
                continue
            for sd in (-1, 1):
                box(p, "AlarmDim", mx + (sd * 3.5 if turn == 0 else 0), my + (sd * 3.5 if turn else 0), 0.07,
                    8, 1.0, 0.06, rz=turn + sd * 30)
    for _ in range(ctx.n(2, 4)):
        ctx.put("sentinel turret", shape_turret, 2.6, 6.0, lambda: ctx.edge(5, 14))
    for _ in range(ctx.n(1, 3)):
        ctx.put("sentinel pylon", shape_sentinel, 2.0, 9.0, ctx.uniform)
    for _ in range(ctx.n(2, 4)):
        ctx.put("alarm post", shape_alarm_post, 1.0, 10.3, lambda: ctx.edge(2, 6))
    for _ in range(ctx.n(1, 3)):
        ctx.put("laser fence", shape_laser_fence, 4.6, 5.6, lambda: ctx.edge(6, 18))
    ctx.put("console", shape_console, 1.6, 2.6, ctx.uniform)
    for _ in range(ctx.n(1, 3)):
        float_prop(ctx, "security drone", shape_drone, 1.6, 2.4, (9, 14))
    for prop in p.props:
        if prop["label"] == "holo pedestal":
            prop["interact"] = "Override"
    anchors_on_decks(ctx, {"ENEMY_POST": 5, "EVENT": 2},
                     {"EVENT": "a field generator: shut it down to open the fields"})


def dress_stormhawk(ctx):
    p, rng = ctx.p, ctx.rng
    if role(p) in ("COMBAT", "BOSS", "SIDE"):
        nest_at = ctx.put("nest", shape_nest, 9.5, 3.5, ctx.uniform, s=rng.uniform(1.6, 2.1))
        if nest_at:
            nx, ny, nz = nest_at
            add_anchor(p, "EVENT", nx, ny, nz, "the stormhawk's nest: it dives here")
            for _ in range(ctx.n(2, 4)):
                ctx.put("bone pile", shape_bones, 2.8, 1.6, lambda: ctx.near(nx, ny, 22, 36))
            ctx.put("egg shells", shape_eggshells, 1.8, 1.0, lambda: ctx.near(nx, ny, 20, 30))
    for _ in range(ctx.n(2, 4)):   # claw gouges: three parallel furrows
        for _t in range(40):
            c = ctx.uniform()
            if c is None or not clear_disc(ctx, c[0], c[1], 7.0):
                continue
            a = rng.uniform(0, 180)
            for k in (-1, 0, 1):
                ox, oy = -math.sin(math.radians(a)) * k * 1.6, math.cos(math.radians(a)) * k * 1.6
                box(p, "Soot", c[0] + ox, c[1] + oy, 0.07, 11 - abs(k) * 2, 0.7, 0.06, rz=a)
            break
    for _ in range(ctx.n(2, 4)):   # lightning glass: fulgurite cracks that glow
        surface_crack(ctx, rng.uniform(16, 30), w=0.8, mat="AzureNeon")
    for _ in range(ctx.n(3, 6)):
        ctx.put("fallen feather", shape_fallen_feather, 3.2, 0.3, ctx.uniform, corridor=False)
    for _ in range(ctx.n(2, 4)):
        float_prop(ctx, "storm feather", shape_fallen_feather, 3.2, 2.0, (7, 13), tilt=30)
    topple(ctx, ("lamp", "light pillar", "banner"), 0.35)
    blockers(ctx, lambda p: (frustum(p, "DeepAlloy", 6, 1.2, 0.8, 0, 14, -8, 0, M=xf(z=1.2, ry=86)),
                             [box(p, "Twig", k * 4 - 8, 1, 0.4, 5, 0.5, 0.5, rz=k * 40) for k in range(5)]))
    anchors_on_decks(ctx, {"RESOURCE": 2}, {"RESOURCE": "stormhawk feathers"})


def dress_rime(ctx):
    p, rng = ctx.p, ctx.rng
    # the whole citadel frosts blue-grey, so what is white is snow
    recolour(p, {"CitadelWhite": "Frost", "PaleAlloy": "FrostDeep", "Verdure": "Snow", "AzureDim": "Ice",
                 "SkyGlass": "Ice"}, props_too=False)
    recolour(p, {"CitadelViolet": "Snow"}, fraction=0.45, rng=rng, props_too=False)
    for fi, _si in tops(p):   # snow settles on every upward face above the floor
        p.fmat[fi] = "Snow"
    for _ in range(ctx.n(8, 14)):   # drifts against the lee of the walls, from this piece's wind
        ctx.put("snow drift", DRIFTS[rng.randrange(3)], 4.2, 2.6, lambda: ctx.edge(3, 7, facing=ctx.wind),
                s=rng.uniform(1.0, 2.0), corridor=False)
    for _ in range(ctx.n(3, 6)):
        ctx.put("snow drift", DRIFTS[rng.randrange(3)], 4.2, 2.6, ctx.uniform, s=rng.uniform(0.6, 1.1))
    for _ in range(ctx.n(6, 10)):   # snow lying across the open deck
        surface_blot(ctx, "Snow", rng.uniform(4, 9), ctx.uniform, sx=rng.uniform(1.0, 1.8))
    for _ in range(ctx.n(2, 4)):
        ctx.put("ice spikes", ICE_SPIKES[rng.randrange(3)], 3.2, 9.0, ctx.uniform, s=rng.uniform(1.2, 2.4))
    for _ in range(ctx.n(2, 5)):
        ctx.put("frost crystals", FROST, 2.8, 5.0, lambda: ctx.edge(2, 5), s=rng.uniform(0.6, 1.0))
    if role(p) in ("SIDE", "CAP", "COMBAT") and rng.random() < 0.6:
        at = ctx.put("frozen figure", shape_frozen_figure, 2.6, 6.0, ctx.uniform)
        if at:
            add_anchor(p, "DISCOVERY", at[0], at[1], at[2], "someone frozen in the ice, holding something gold")
    for prop in p.props:
        if prop["label"] == "brazier":
            prop["interact"] = "Lightable"
    for poly in ctx.polys:   # icicles along the deck rims
        n = len(poly)
        cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
        for _ in range(max(6, 2 * n)):
            i = rng.randrange(n)
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            t = rng.uniform(0.1, 0.9)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            x, y = x + (cx - x) * 0.02, y + (cy - y) * 0.02
            crystal(p, "Ice", x, y, -DECK_T + 0.05, rng.uniform(0.4, 0.8), 0.01, rng.uniform(2.5, 8), n=4)
    blockers(ctx, row(ICE_SPIKES[2], (-12, -4, 4, 12)))
    anchors_on_decks(ctx, {"RESOURCE": 1, "DISCOVERY": 1}, {"DISCOVERY": "something frozen in the ice"})


def dress_reclaimed(ctx):
    p, rng = ctx.p, ctx.rng
    recolour(p, {"AzureNeon": "DeepAlloy", "AzureDim": "HullSlate"}, props_too=False)
    by_shell = {}
    for fi, si in tops(p):   # moss on the tops of walls and rails, by whole runs
        by_shell.setdefault(si, []).append(fi)
    for fl in by_shell.values():
        if rng.random() < 0.45:
            m = rng.choice(("Moss", "MossLight"))
            for fi in fl:
                p.fmat[fi] = m
    breach_walls(ctx, rng.randint(0, 2))
    if rng.random() < 0.4:
        crumble_tower(ctx)
    for poly in ctx.polys:
        K["vines"](p, poly, "reclaimed %s %d" % (p.name, len(poly)), count=max(8, 2 * len(poly)))
    ivy(ctx, chance=rng.uniform(0.4, 0.9))
    for _ in range(ctx.n(8, 14)):   # moss creeps along the foot of every wall
        surface_blot(ctx, rng.choice(("Moss", "MossLight")), rng.uniform(2.5, 5.0), lambda: ctx.edge(1.5, 5),
                     sx=rng.uniform(1.4, 2.4))
    for _ in range(ctx.n(6, 10)):
        ctx.put("moss mound", MOSS[rng.randrange(3)], 4.2, 1.6, lambda: ctx.edge(2, 7), s=rng.uniform(0.7, 1.4),
                corridor=False)
    for _ in range(ctx.n(4, 7)):
        ctx.put("bush", BUSHES[rng.randrange(3)], 3.2, 3.6, lambda: ctx.edge(3, 10), s=rng.uniform(1.0, 1.8))
    for _ in range(ctx.n(3, 6)):
        ctx.put("fern", shape_fern, 2.6, 2.0, lambda: ctx.edge(2, 8), s=rng.uniform(0.9, 1.5), corridor=False)
    for _ in range(ctx.n(2, 4)):
        ctx.put("flowers", shape_flowers, 2.2, 1.3, ctx.uniform, corridor=False)
    for _ in range(ctx.n(1, 3)):
        ctx.put("sapling", shape_sapling, 3.0, 8.5, ctx.uniform, s=rng.uniform(1.0, 1.6))
    for _ in range(ctx.n(1, 3)):
        ctx.put("mushrooms", shape_mushrooms, 1.8, 2.4, lambda: ctx.edge(2, 6), s=rng.uniform(1.0, 1.8))
    roots(ctx, ctx.n(2, 5))
    for _ in range(ctx.n(2, 4)):
        surface_crack(ctx, rng.uniform(14, 26))
    for prop in p.props:
        if prop["label"] in ("lamp", "light pillar", "brazier", "holo pedestal"):
            prop["interact"] = None
        if prop["label"] in ("crate", "container"):
            prop["interact"] = "Loot"
    topple(ctx, ("lamp", "banner", "light pillar"), 0.3)
    blockers(ctx, row(BUSHES[2], (-12, -4, 4, 12)))
    anchors_on_decks(ctx, {"RESOURCE": 3, "DISCOVERY": 1}, {"RESOURCE": "wild growth: herbs and seeds"})


def dress_aether_surge(ctx):
    p, rng = ctx.p, ctx.rng
    recolour(p, {"AzureNeon": "AetherBloom", "AzureDim": "AetherDim"}, props_too=True)
    centres = []   # one to three epicentres; the surge breaks out and fades outward
    for _ in range(rng.randint(1, 3)):
        for _t in range(40):
            c = ctx.uniform()
            # an epicentre may be anywhere flat; the crystals keep off the walking line
            if c and ctx.ground.flat(c[0], c[1], 6.0) is not None and \
                    all(math.hypot(c[0] - a, c[1] - b) > 40 for a, b in centres):
                centres.append(c)
                break
    for cx, cy in centres:
        for _k in range(rng.randint(4, 7)):   # glowing fissures radiate from it
            a = math.radians(rng.uniform(0, 360))
            L = rng.uniform(14, 34)
            mx, my = cx + math.cos(a) * (5 + L / 2), cy + math.sin(a) * (5 + L / 2)
            if clear_disc(ctx, mx, my, L * 0.5):
                box(p, "AetherDim", mx, my, 0.07, L, 1.0, 0.06, rz=math.degrees(a))
        big = ctx.put("aether cluster", AETHER[rng.randrange(3)], 2.6, 8.0, lambda: ctx.near(cx, cy, 0, 3),
                      s=rng.uniform(2.8, 3.8))
        if big:
            add_anchor(p, "RESOURCE", big[0], big[1], big[2], "the surge's heart: the richest aether")
        for _ in range(ctx.n(4, 8)):
            d0 = rng.uniform(8, 34)
            at = ctx.put("aether cluster", AETHER[rng.randrange(3)], 2.6, 8.0,
                         lambda: ctx.near(cx, cy, d0 - 3, d0 + 3), s=max(0.8, 2.6 - d0 / 18))
            if at and rng.random() < 0.4:
                add_anchor(p, "RESOURCE", at[0], at[1], at[2], "aether crystal")
        ctx.put("aether geode", shape_geode, 3.2, 3.2, lambda: ctx.near(cx, cy, 10, 30), s=rng.uniform(1.0, 1.6))
        for _ in range(rng.randint(2, 4)):   # shards thrown up round the epicentre
            float_prop(ctx, "aether shard", lambda p: crystal(p, "AetherBloom", 0, 0, 0, 1.4, 4.5, 3.5, n=5),
                       2.0, 8.0, (14, 22), around=(cx, cy, 8, 20), tilt=20)
    for prop in p.props:
        if prop["label"] == "holo pedestal":
            prop["interact"] = "Attune"
    blockers(ctx, row(AETHER[1], (-12, -4, 4, 12)))
    anchors_on_decks(ctx, {"DISCOVERY": 2, "RESOURCE": 1}, {"DISCOVERY": "the surge has uncovered something old"})


def dress_unmooring(ctx):
    p, rng = ctx.p, ctx.rng
    loosen_islet(ctx)
    breach_walls(ctx, rng.randint(1, 3))
    if rng.random() < 0.5:
        crumble_tower(ctx)
    recolour(p, {"AzureDim": "DeepAlloy", "AzureNeon": "DeepAlloy"}, fraction=0.5, rng=rng, props_too=False)
    for _ in range(ctx.n(4, 7)):
        surface_crack(ctx, rng.uniform(20, 38), w=1.3)
    for _ in range(ctx.n(2, 4)):   # the seams leak light where the deck has split
        surface_crack(ctx, rng.uniform(14, 26), w=0.7, mat="AzureNeon")
    for prop in p.props:
        if prop["label"] in ("floating crystal", "anti-grav pylon"):
            prop["matrix"] = prop["matrix"] @ xf(rx=rng.uniform(12, 28), ry=rng.uniform(-15, 15))
    topple(ctx, ("lamp", "light pillar", "crate"), 0.3)
    for prop in p.props:
        if prop["label"] in ("lamp", "light pillar") and prop.get("interact") is None:
            prop["interact"] = "Repair"
    at = ctx.put("stabilizer", shape_stabilizer, 2.4, 9.6, ctx.uniform)
    if at:
        add_anchor(p, "EVENT", at[0], at[1], at[2], "a failing stabiliser: repair it before the deck lets go")
    for _ in range(ctx.n(2, 4)):
        ctx.put("hazard beacon", shape_hazard_beacon, 1.0, 5.2, lambda: ctx.edge(3, 8))
    for _ in range(ctx.n(2, 4)):
        ctx.put("rubble", RUBBLE[rng.randrange(3)], 3.2, 3.0, ctx.uniform, s=rng.uniform(0.8, 1.3))
    for _ in range(ctx.n(3, 6)):   # pieces of the citadel drifting off, on purpose
        for _t in range(60):
            if ctx.flat_only:
                break
            x, y = rng.uniform(-HALF + 12, HALF - 12), rng.uniform(-HALF + 12, HALF - 12)
            z = rng.uniform(-14, 10)
            if not any(edge_dist(q, x, y) < 30 for q in ctx.polys):
                continue
            if not free_for_float(p, ("cyl", x, y, 5.0, z - 5, z + 1.5)):
                continue
            p.float_("drifting fragment", x, y, 5.0, z - 5, z + 1.5)
            with frame(p, xf(x, y, z, rng.uniform(0, 90), rx=rng.uniform(-20, 20))):
                with as_prop(p, "drifting fragment", I4):
                    shape_fragment(p)
            break
    blockers(ctx, row(RUBBLE[1], (-11, -2, 8)))
    anchors_on_decks(ctx, {"RESOURCE": 2}, {"RESOURCE": "exposed aether core -- harvesting speeds the collapse"})


HOOKS = {
    "unmooring": dress_unmooring, "siege": dress_siege, "lockdown": dress_lockdown,
    "stormhawk": dress_stormhawk, "rime": dress_rime, "reclaimed": dress_reclaimed,
    "aether_surge": dress_aether_surge,
}


def make_hook(scenario):
    def hook(p):
        p.anchors = []
        reserve_blockers(p)
        HOOKS[scenario](Ctx(p, scenario))
        # A prop's vertices come back from world space through its placement's
        # inverse, which leaves last-digit noise; rounding it away lets every
        # copy of a shape match, so a shape stays one library mesh.
        for prop in p.props:
            prop["verts"] = [Vector((round(v.x, 4), round(v.y, 4), round(v.z, 4))) for v in prop["verts"]]
    return hook


# ==========================================================================
# Assembly, preview, export
# ==========================================================================

ROW = 2 * HALF + K["REVIEW_GAP"]


def build_set(scenario, mats, row_i):
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
        obj.location = (i * ROW, -row_i * ROW * 1.25, 0)
        pieces.append(p)
        objs.append(obj)
    K["SCENARIO_HOOK"] = None
    return pieces, objs


def preview_props(pieces, objs, mats, coll):
    """Review only: every prop and fixture drawn in place on its piece, in a
    collection that is never exported."""
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


def main(export=False, save=True, preview=True):
    K["reset_scene"]()
    mats = K["ensure_materials"]()
    report, all_pieces, sets = {}, [], {}
    prev = bpy.data.collections.new("Preview_Props_NotExported")
    bpy.context.scene.collection.children.link(prev)
    for row_i, scen in enumerate([None] + SCENARIOS):
        pieces, objs = build_set(scen, mats, row_i)
        bpy.context.view_layer.update()
        if preview:
            preview_props(pieces, objs, mats, prev)
        ok, rep = K["validate"](objs)
        report[scen or "base"] = {"ok": ok, "failed": [(r["piece"], r["failed"], r["float_problems"][:2],
                                                         r["ground_problems"][:2]) for r in rep if not r["ok"]],
                                  "tris_max": max(r["tris"] for r in rep),
                                  "props": sum(len(p.props) for p in pieces)}
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
            K["_export_selected"](objs, path)
            paths.append(path)
            anchors[scen] = write_anchors(os.path.join(d, "Anchors_%s.luau" % scen), scen, pieces)
        props_path = os.path.join(SCEN_EXPORT, "sky_citadel_scenario_props.fbx")
        K["_export_selected"](prop_objs, props_path)
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
