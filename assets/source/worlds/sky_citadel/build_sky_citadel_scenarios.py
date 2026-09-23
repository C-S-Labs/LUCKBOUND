"""Sky Citadel scenario kits -- generator.

Run inside Blender (headless is the tested route):

    blender --background --factory-startup --python build_sky_citadel_scenarios.py -- --export

WHAT A SCENARIO KIT IS
The same 36 pieces as the base kit (build_sky_citadel_kit.py, executed here as
a module and never edited by this file), rebuilt through a SCENARIO_HOOK that
changes their ARCHITECTURE for one Fate profile: palette, structure (crumbling,
additions, loosened islets), surface paint, and the few props that are part of
the architecture (a moored warship, forcefields at the openings).

PROPS ARE NOT BAKED INTO CHUNKS (owner direction, 2026-09-23)
A chunk ships no dressing. It ships SPAWN POINTS -- where a prop could stand,
ray-cast on the real deck, never in the walking line -- and the game scatters
props from the prop library (sky_citadel_props.py) when a map is generated,
seeded by the run, so no two runs dress a chunk alike and nothing is placed
twice. scatter_core.py is the algorithm; src/shared/Core/ScatterCore.luau is its
exact twin in the game. The .blend previews two seeds of a run.

Outputs (under assets/export/worlds/sky_citadel/scenarios/):
    <scenario>/sky_citadel_<scenario>_structure.fbx   36 meshes, each at the origin
    sky_citadel_scenario_props.fbx                    fixed architecture props
    sky_citadel_scatter_props.fbx                     the scatter library + blockers
    Props_Scenarios.luau / Fixtures_Scenarios.luau    fixed placements (staged)
    <scenario>/Anchors_<scenario>.luau                gameplay anchors + blockers
and, in the game, src/shared/Content/Scatter/SkyCitadel/ (kinds, pools, points).
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
SC = {"__name__": "scatter_core"}
exec(open(os.path.join(HERE, "..", "_framework", "scatter_core.py"), encoding="utf-8").read(), SC)

REPO = K["REPO"]
SCEN_EXPORT = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "scenarios")
SCATTER_LUAU = os.path.join(REPO, "src", "shared", "Content", "Scatter", "SkyCitadel")
BLEND_OUT = os.path.join(HERE, "sky_citadel_scenarios.blend")

HALF, DECK_T, CROWN_TOP = K["HALF"], K["DECK_T"], K["CROWN_TOP"]
box, frustum, crystal, torus = K["box"], K["frustum"], K["crystal"], K["torus"]
xf, frame, as_prop, as_fixture, fixture_part = K["xf"], K["frame"], K["as_prop"], K["as_fixture"], K["fixture_part"]
shapes_clash, free_for_float, _inside = K["shapes_clash"], K["free_for_float"], K["_inside"]
tube, poly_radius, piece_bvh, hang_clear, path_clear, face_dist = (
    K["tube"], K["poly_radius"], K["piece_bvh"], K["hang_clear"], K["path_clear"], K["face_dist"])
I4 = Matrix.Identity(4)
PREVIEW_SEEDS = (20260923, 7)

# --------------------------------------------------------------------------
# Palette additions, in the kit's style. Only in this module's copy of the
# kit, so the base kit's own materials are unchanged when it runs alone.
# --------------------------------------------------------------------------
EXTRA_PALETTE = {
    "Soot": ((40, 38, 48), False),
    "Char": ((64, 54, 52), False),
    "Snow": ((244, 248, 255), False),
    "Frost": ((196, 214, 232), False),
    "FrostDeep": ((150, 172, 198), False),
    "Ice": ((150, 200, 230), False),
    "AlarmRed": ((255, 70, 80), True),
    "AlarmDim": ((170, 50, 64), True),
    "EmberGlow": ((255, 150, 60), True),
    "Smoke": ((104, 104, 116), False),
    "RaiderRust": ((158, 74, 52), False),
    "Twig": ((110, 90, 70), False),
    "Bark": ((92, 70, 52), False),
    "Bone": ((226, 220, 200), False),
    "Moss": ((70, 112, 66), False),
    "MossLight": ((118, 160, 86), False),
    "AetherBloom": ((190, 150, 255), True),
    "AetherDim": ((120, 90, 190), True),
    "Steel": ((104, 112, 126), False),
    "Gunmetal": ((70, 76, 88), False),
    "Hazard": ((232, 188, 40), False),
    "Pearl": ((236, 228, 246), False),
    "Lavender": ((178, 160, 214), False),
    "Weathered": ((178, 176, 162), False),
    "Lichen": ((136, 148, 112), False),
    "Scorched": ((128, 118, 112), False),
    "StormStone": ((140, 148, 164), False),
    "StormSlate": ((84, 92, 110), False),
    "Plating": ((150, 156, 168), False),
}
K["PALETTE"].update(EXTRA_PALETTE)
K["MAT_ORDER"] = list(K["PALETTE"].keys())

K["PROP_KINDS"].update({
    "raider warship": ("warship", "Moored", 1),
    "gangway": ("gangway", "Static", 1),
    "blocker": ("blocker", "Blocker", 1),
    "rubble": ("rubble", "Static", 1),
    "fallen roof": ("fallen_roof", "Static", 1),
    "sentinel pylon": ("sentinel", "Static", 1),
})
K["PROP_INTERACT"].update({"raider warship": "Board", "blocker": "Blocker", "sentinel pylon": "Destroy"})

SCENARIOS = ["unmooring", "siege", "lockdown", "stormhawk", "rime", "reclaimed", "aether_surge"]


# ==========================================================================
# Shared geometry helpers
# ==========================================================================

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


# The prop library: families of seeded variants (see its docstring).
exec(open(os.path.join(HERE, "sky_citadel_props.py"), encoding="utf-8").read(), globals())


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


def in_corridor(p, x, y, half=20.0, o=None):
    """The walking line between openings, which no prop may ever stand in."""
    o = openings(p) if o is None else o
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


def edge_near(poly, x, y):
    """(distance to the polygon's nearest edge, that edge's inward normal)."""
    best, nrm = 1e9, (0.0, 0.0)
    n = len(poly)
    cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        d = math.hypot(x - (ax + dx * t), y - (ay + dy * t))
        if d < best:
            L = math.sqrt(L2)
            nx, ny = dy / L, -dx / L
            if (cx - (ax + bx) / 2) * nx + (cy - (ay + by) / 2) * ny < 0:
                nx, ny = -nx, -ny
            best, nrm = d, (nx, ny)
    return best, nrm


def edge_dist(poly, x, y):
    return edge_near(poly, x, y)[0]


class Ground:
    """The piece's real surface."""

    def __init__(self, p):
        self.bvh = BVHTree.FromPolygons([tuple(v) for v in p.verts], [tuple(f) for f in p.faces])

    def z_at(self, x, y, top=14.0):
        hit = self.bvh.ray_cast(Vector((x, y, top)), Vector((0, 0, -1)), 60.0)
        if hit[0] is None:
            return None
        return hit[0].z, abs(hit[1].z)

    def up(self, x, y, z):
        hit = self.bvh.ray_cast(Vector((x, y, z + 0.5)), Vector((0, 0, 1)), 60.0)
        return 60.0 if hit[0] is None else hit[0].z - z

    def flat(self, x, y, r, tol=0.3):
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
    """What a structure hook needs about one piece."""

    def __init__(self, p, scenario):
        self.p = p
        self.scenario = scenario
        self.rng = random.Random("%s|%s" % (p.name, scenario))
        self.open = openings(p)
        self.flat_only = "aviary" in p.name      # birds circle low there; keep it clear
        self.refresh()

    def refresh(self):
        self.polys = deck_polys(self.p)
        self.areas = [poly_area(q) for q in self.polys]
        self.ground = Ground(self.p)

    def uniform(self):
        if not self.polys:
            return None
        poly = self.rng.choices(self.polys, weights=self.areas)[0]
        xs, ys = [q[0] for q in poly], [q[1] for q in poly]
        return self.rng.uniform(min(xs), max(xs)), self.rng.uniform(min(ys), max(ys))

    def near(self, cx, cy, r0, r1):
        a = self.rng.uniform(0, 2 * math.pi)
        d = r0 + (r1 - r0) * math.sqrt(self.rng.random())
        return cx + math.cos(a) * d, cy + math.sin(a) * d

    def clear(self, x, y, r, h=0.3, corridor=True):
        """Flat deck of radius r, clear of everything registered."""
        if corridor and in_corridor(self.p, x, y, o=self.open):
            return None
        z0 = self.ground.flat(x, y, r, tol=0.2)
        if z0 is None:
            return None
        if any(shapes_clash(("cyl", x, y, r, z0, z0 + h), s, gap=0.5) for _, s in self.p.solids + self.p.floats):
            return None
        return z0


def place(p, label, x, y, z, rz, s, shape):
    """A fixed prop (architecture): anchored at (x, y, z), turned rz, scale s
    in the geometry so copies of a shape share one mesh."""
    with frame(p, xf(x, y, z, rz)):
        with as_prop(p, label, I4):
            with frame(p, Matrix.Diagonal((s, s, s, 1.0))):
                shape(p)


def surface_crack(ctx, L, w=1.0, mat="Soot"):
    for _ in range(40):
        c = ctx.uniform()
        if c is None:
            return
        if ctx.clear(c[0], c[1], L * 1.02, corridor=False) is not None:
            crack(ctx.p, c[0], c[1], ctx.rng, L=L, w=w, mat=mat)
            return


def surface_blot(ctx, mat, r, where=None, sx=1.0, n=9, jitter=0.35):
    for _ in range(40):
        c = (where or ctx.uniform)()
        if c is None:
            return
        if ctx.clear(c[0], c[1], r * max(sx, 1.0), corridor=False) is None:
            continue
        blot(ctx.p, mat, c[0], c[1], r, "blot %s %.1f %.1f" % (ctx.p.name, c[0], c[1]), sx=sx, n=n, jitter=jitter,
             rz=ctx.rng.uniform(0, 180))
        return


# ==========================================================================
# Structure edits: shells, crumbling, whole-surface looks
# ==========================================================================

def shells(p):
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
    drop = set(drop)
    keep = [i for i in range(len(p.faces)) if i not in drop]
    newidx = {old: new for new, old in enumerate(keep)}
    p.up = {newidx[i] for i in p.up if i in newidx}
    faces = [p.faces[i] for i in keep]
    fmat = [p.fmat[i] for i in keep]
    p.ftag = [p.ftag[i] for i in keep] if len(p.ftag) == len(p.faces) else p.ftag
    used = sorted({v for f in faces for v in f})
    vmap = {old: new for new, old in enumerate(used)}
    p.verts = [p.verts[i] for i in used]
    p.faces = [[vmap[v] for v in f] for f in faces]
    p.fmat = fmat


def _cut_box(p, s, lo, hi, ox, oy, tx, ty):
    """A box-shaped rim part (a rail bar, a kerb) crossing [lo, hi] along the
    rim: replaced by the pieces of it outside that stretch."""
    vs = sorted(s["verts"])
    ts = {v: (p.verts[v].x - ox) * tx + (p.verts[v].y - oy) * ty for v in vs}
    tmin, tmax = min(ts.values()), max(ts.values())
    mid = (tmin + tmax) / 2
    f0 = s["faces"]
    tag = p.ftag[f0[0]] if len(p.ftag) == len(p.faces) else "?"
    mats = [p.fmat[fi] for fi in f0]
    remap = {v: i for i, v in enumerate(vs)}
    faces = [[remap[v] for v in p.faces[fi]] for fi in f0]
    for keep_low in (True, False):
        end = lo if keep_low else hi
        if keep_low and end - tmin < 0.8:
            continue
        if not keep_low and tmax - end < 0.8:
            continue
        verts = []
        for v in vs:
            q = p.verts[v].copy()
            moving = ts[v] > mid if keep_low else ts[v] < mid
            if moving:
                q = q + Vector((tx, ty, 0)) * (end - ts[v])
            verts.append(q)
        n0 = len(p.faces)
        p.add([tuple(q) for q in verts], faces, mats[0], I4)
        for k, m in enumerate(mats):
            p.fmat[n0 + k] = m
            p.ftag[n0 + k] = tag
    return f0


def clear_rim(ctx, ox, oy, tx, ty, nx, ny, t0, t1, band=3.0, margin=1.5):
    """Open a gap in a deck's rim between t0 and t1 along the line through
    (ox, oy) with tangent (tx, ty): every parapet block, rail post and kerb in
    the stretch goes, and a rail bar or kerb running on past it is cut clean
    at the gap -- never left hanging where its posts were."""
    p = ctx.p
    lo, hi = t0 - margin, t1 + margin
    drop = []
    for sh in shells(p):
        if sh["min"].z < -0.8 or sh["max"].z > 7.5 or sh["max"].z < 0.35 or sh["max"].z - sh["min"].z < 0.3:
            continue
        pts = [p.verts[v] for v in sh["verts"]]
        ds = [(q.x - ox) * nx + (q.y - oy) * ny for q in pts]
        if min(ds) < -band or max(ds) > band:
            continue
        ts = [(q.x - ox) * tx + (q.y - oy) * ty for q in pts]
        if max(ts) < lo or min(ts) > hi:
            continue
        if min(ts) >= lo and max(ts) <= hi:
            drop += sh["faces"]
        elif len(sh["verts"]) == 8 and len(sh["faces"]) == 6:
            drop += _cut_box(p, sh, lo, hi, ox, oy, tx, ty)
        else:
            drop += sh["faces"]
    remove_faces(p, drop)
    ctx.refresh()


def breach_walls(ctx, count, rubble=True):
    """Knock gaps in the parapets and railings; a chunk of rim hangs below."""
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
    done, gaps = [], []
    for _ in range(count * 3):
        if not rim or len(done) >= count:
            break
        centre = ctx.rng.choice(rim)
        cx, cy = centre["c"].x, centre["c"].y
        if any(math.hypot(cx - a, cy - b) < 30 for a, b in done):
            continue
        R_ = ctx.rng.uniform(6, 12)
        poly = min(ctx.polys, key=lambda q: edge_dist(q, cx, cy))
        _d, (nx, ny) = edge_near(poly, cx, cy)
        gaps.append((cx, cy, -ny, nx, nx, ny, R_))
        rim = [s for s in rim if math.hypot(s["c"].x - cx, s["c"].y - cy) >= R_]
        done.append((cx, cy))
    if not done:
        return []
    for cx, cy, tx, ty, nx, ny, R_ in gaps:
        clear_rim(ctx, cx, cy, tx, ty, nx, ny, -R_, R_, margin=0.0)
    for cx, cy in done:
        box(p, "CitadelWhite", cx, cy, -DECK_T - 1.2, 5, 3, 3.2, rz=ctx.rng.uniform(0, 90), rx=ctx.rng.uniform(-18, 18))
    ctx.refresh()
    if rubble:
        for cx, cy in done:
            poly = min(ctx.polys, key=lambda q: edge_dist(q, cx, cy))
            n = len(poly)
            mx, my = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
            L = math.hypot(mx - cx, my - cy) or 1
            tx, ty = cx + (mx - cx) / L * 6, cy + (my - cy) / L * 6
            z0 = ctx.clear(tx, ty, 3.4, corridor=False)
            if z0 is not None:
                p.solid("rubble", tx, ty, 3.4, z0, z0 + 3)
                place(p, "rubble", tx, ty, z0, ctx.rng.uniform(0, 360), 1.0, lambda q: f_rubble(q, 1))
    return done


def crumble_tower(ctx, fallen=True, cut=None):
    """Break the top off one turret: walk and roof go, a jagged rim is left,
    and the roof lies where it fell. Never a turret carrying a spire. With
    `cut` (0..1) the shaft is snapped that far up instead of at its walk."""
    if ctx.flat_only:
        return False
    p = ctx.p
    towers = [s for lab, s in p.solids if lab == "tower" and s[0] == "cyl"]
    ctx.rng.shuffle(towers)
    sh = shells(p)
    for (_, x, y, R_, z0, z1) in towers:
        r = R_ / 1.25
        H = z1 - 6 - 2.4 * r
        near = [s for s in sh if math.hypot(s["c"].x - x, s["c"].y - y) < r * 1.3]
        if any(s["max"].z >= CROWN_TOP - 0.01 or s["max"].z > z1 + 1.0 for s in near):
            continue
        top = [s for s in near if s["min"].z >= H - 0.5]
        if not top:
            continue
        drop = [fi for s in top for fi in s["faces"]]
        Hc = H
        if cut is not None:
            # snap the shaft itself: squash its top ring of verts down to the cut
            Hc = max(8.0, H * cut)
            for s in near:
                if s["min"].z < H - 0.5 and s["max"].z > Hc:
                    if s["max"].z - s["min"].z > 6:       # the shaft
                        for v in s["verts"]:
                            if p.verts[v].z > Hc:
                                p.verts[v] = Vector((p.verts[v].x, p.verts[v].y, Hc))
                    else:                                  # a window slit above the break
                        drop += s["faces"]
        remove_faces(p, drop)
        for k in range(10):
            a = math.radians(36 * k + ctx.rng.uniform(-8, 8))
            hgt = ctx.rng.uniform(0.8, 4.5)
            box(p, "CitadelWhite", x + math.cos(a) * r * 0.86, y + math.sin(a) * r * 0.86, Hc + hgt / 2 - 0.3,
                r * 0.55, 1.0, hgt, rz=math.degrees(a) + 90, rx=ctx.rng.uniform(-10, 10))
        box(p, "Soot", x, y, Hc - 0.4, r * 1.5, r * 1.5, 0.3, rz=22.5)
        ctx.refresh()
        if fallen:
            for _ in range(40):
                tx, ty = ctx.near(x, y, r * 1.8, r * 3.4)
                z0 = ctx.clear(tx, ty, 6.5 * r / 6.0, corridor=True)
                if z0 is not None:
                    p.solid("fallen roof", tx, ty, 6.5 * r / 6.0, z0, z0 + 6)
                    place(p, "fallen roof", tx, ty, z0, ctx.rng.uniform(0, 360), r / 6.0, shape_fallen_roof)
                    break
        return True
    return False


def shape_fallen_roof(p):
    with frame(p, xf(0, 0, 2.6, 0, 0, 78)):
        frustum(p, "CitadelViolet", 8, 5.4, 0, -2, 12)
    crystal(p, "SunGold", 12.5, 0, 1.0, 0.8, 1.6, 1.0)


def loosen_islet(ctx):
    """One of the piece's own low islets has come loose: sunk and tilted, its
    bridge no longer meeting it, everything on it gone with it."""
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
        if not group or any(s["max"].z > 60 for s in group):
            continue
        # a keel reaching the bottom of the box stays where it is: the islet
        # lifts off it instead of sinking, so the break shows as open air
        deep = [s for s in group if s["min"].z < -80]
        group = [s for s in group if s["min"].z >= -80]
        vs = sorted({v for s in group for v in s["verts"]})
        axis = ctx.rng.uniform(0, 360)
        tilt, sink = ctx.rng.uniform(6, 10), ctx.rng.uniform(4.0, 7.0)
        if deep:
            sink = -sink
        M = None
        for _try in range(4):   # as far as the piece's box allows: its keel must stay above -96
            T = xf(cx, cy, -sink) @ xf(rz=axis) @ xf(rx=tilt) @ xf(rz=-axis) @ xf(-cx, -cy, 0)
            pts = [T @ p.verts[v] for v in vs]
            if min(q.z for q in pts) > -95.5 and max(max(abs(q.x), abs(q.y)) for q in pts) < HALF - 0.5:
                M = T
                break
            tilt, sink = tilt * 0.6, sink * 0.6
        if M is None or tilt < 2.5:
            continue
        for v in vs:
            p.verts[v] = M @ p.verts[v]
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
    """Faces that are the upward top of their shell above the floor."""
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
    """Knock standing architecture props over, resting on the deck."""
    for prop in ctx.p.props:
        if prop["label"] not in labels or ctx.rng.random() > chance:
            continue
        t = prop["matrix"].translation
        Rm = (xf(rz=ctx.rng.uniform(0, 360)) @ xf(rx=90)).to_3x3()
        pts = [Rm @ v for v in prop["verts"]]
        reach = max(math.hypot(q.x, q.y) for q in pts)
        z0 = ctx.ground.flat(t.x, t.y, reach + 0.5, tol=0.3)
        if z0 is None or any(shapes_clash(("cyl", t.x, t.y, reach, z0, z0 + 2), s, gap=0.3)
                             for lab, s in ctx.p.solids if lab not in ("tower", "spire")):
            continue
        prop["matrix"] = Matrix.Translation((t.x, t.y, z0 - min(q.z for q in pts))) @ Rm.to_4x4()
        if prop["label"] in ("lamp", "light pillar"):
            prop["interact"] = "Repair"


# ==========================================================================
# Architecture props: the few things that ARE the scenario's architecture
# ==========================================================================

def shape_gangway(p, L=10.0):
    """A plank bridge from the rail down onto a moored ship's deck, L long."""
    drop = math.radians(6)
    box(p, "Twig", L / 2, 0, -0.55 - math.sin(drop) * L / 2, L, 3.2, 0.35, ry=6)
    for sy in (-1.5, 1.5):
        box(p, "DeepAlloy", L / 2, sy, 0.35 - math.sin(drop) * L / 2, L, 0.2, 0.2, ry=6)
        for gx in (1, L / 2, L - 1):
            box(p, "DeepAlloy", gx, sy, -0.1 - math.sin(drop) * gx, 0.2, 0.2, 1.1)


_SHIP_CACHE = {}


def ship_geometry(i):
    """Design i built once, in its own frame: (verts, faces, mats)."""
    if i not in _SHIP_CACHE:
        q = K["Piece"]("_ship_%d" % i, "ship")
        SHIPS[i](q)
        _SHIP_CACHE[i] = ([Vector((round(v.x, 4), round(v.y, 4), round(v.z, 4))) for v in q.verts],
                          [list(f) for f in q.faces], list(q.fmat))
    return _SHIP_CACHE[i]


def warship(ctx, n=1):
    """Moor raider warships alongside the decks, a gangway to the rail -- only
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
            if side in ("E", "W"):
                edge = max(xs) if side == "E" else min(xs)
                cx, cy, rz = edge + (gap + 10.8) * sgn, along, 90
                blocked = side in ctx.open and abs(cy) < 66
                rail = (cx - (gap + 12.3) * sgn, cy)
                behind = (rail[0] - 6.0 * sgn, cy)
            else:
                edge = max(ys) if side == "N" else min(ys)
                cx, cy, rz = along, edge + (gap + 10.8) * sgn, 0
                blocked = side in ctx.open and abs(cx) < 66
                rail = (cx, cy - (gap + 12.3) * sgn)
                behind = (cx, rail[1] - 6.0 * sgn)
            if blocked:
                continue
            z0 = ctx.ground.flat(behind[0], behind[1], 3.0)
            top = ctx.ground.z_at(rail[0], rail[1])
            if z0 is None or top is None or top[1] < 0.9 or not (z0 - 0.5 < top[0] < z0 + 4.0):
                continue
            # the berth: room for every one of the five designs (SHIP_ENVELOPE)
            zb = z0 - 1.2
            if side in ("E", "W"):
                shape = ("box", cx - 10.8, cx + 10.8, cy - 44, cy + 44, zb - 11.0, zb + 33.6)
            else:
                shape = ("box", cx - 44, cx + 44, cy - 10.8, cy + 10.8, zb - 11.0, zb + 33.6)
            if not free_for_float(p, shape):
                continue
            p.floats.append(("raider warship", shape))
            # one of the five ships moors here in the preview; the game draws
            # any of them per run (the row's Alt list, PropController)
            primary = ctx.rng.randrange(len(SHIPS))
            place(p, "raider warship", cx, cy, zb, rz + ctx.rng.choice((0, 180)), 1.0, SHIPS[primary])
            p.props[-1]["alts"] = [ship_geometry(i) for i in range(len(SHIPS)) if i != primary]
            to_ship = math.degrees(math.atan2(cy - rail[1], cx - rail[0]))
            gx0 = rail[0] - math.cos(math.radians(to_ship)) * 1.5
            gy0 = rail[1] - math.sin(math.radians(to_ship)) * 1.5
            L = gap + 6.6                              # rail to the ship's boarding rail, and onto it
            place(p, "gangway", gx0, gy0, top[0], to_ship, 1.0, lambda q, L=L: shape_gangway(q, L))
            p.solid("gangway", gx0, gy0, 2.0, z0, z0 + 3)
            placed += 1
            break
    return placed


def forcefields(ctx):
    p = ctx.p
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


# ==========================================================================
# Blockers and anchors
# ==========================================================================

BLOCKER_SHAPES = {
    "unmooring": lambda p: _row(p, lambda q: f_rubble(q, 3), (-11, -2, 8)),
    "siege": lambda p: _row(p, lambda q: f_stake_wall(q, 1), (-6, 7)),
    "stormhawk": lambda p: (frustum(p, "DeepAlloy", 6, 1.2, 0.8, 0, 14, -8, 0, M=xf(z=1.2, ry=86)),
                            _row(p, lambda q: f_fallen_feather(q, 0), (-6, 4))),
    "rime": lambda p: _row(p, lambda q: f_ice(q, 2), (-12, -4, 4, 12)),
    "reclaimed": lambda p: _row(p, lambda q: f_bush(q, 2), (-12, -4, 4, 12)),
    "aether_surge": lambda p: _row(p, lambda q: f_aether(q, 1), (-12, -4, 4, 12)),
}


def _row(p, shape, xs):
    for x in xs:
        with frame(p, xf(x, 0, 0)):
            shape(p)


def reserve_blockers(p):
    for d in openings(p):
        x, y, _ = mouth(d)
        p.solid("blocker", x, y, 8, 0, 14)


def build_blockers(ctx):
    """One per opening. NOT a placement: the run enables a blocker only when a
    Fate profile closes that socket, so they are listed with the anchors and
    never drawn by default."""
    shape = BLOCKER_SHAPES.get(ctx.scenario)
    if shape is None:
        return
    for d in sorted(ctx.open):
        x, y, rz = mouth(d)
        before = len(ctx.p.props)
        with frame(ctx.p, xf(x, y, 0, rz)):
            with as_prop(ctx.p, "blocker", I4):
                shape(ctx.p)
        prop = ctx.p.props.pop(before)
        prop["socket"] = d
        ctx.p.blockers.append(prop)


def add_anchor(p, kind, x, y, z=0.0, note=""):
    p.anchors.append({"kind": kind, "pos": (x, y, z), "note": note})


ANCHOR_NOTES = {
    "unmooring": {"RESOURCE": "exposed aether core -- harvesting speeds the collapse",
                  "EVENT": "a failing stabiliser: repair it before the deck lets go"},
    "siege": {"NPC_POST": "citadel defenders hold here, or a captive to free"},
    "lockdown": {"EVENT": "a field generator: shut it down to open the fields"},
    "stormhawk": {"EVENT": "the stormhawk dives here", "RESOURCE": "stormhawk feathers"},
    "rime": {"DISCOVERY": "something frozen in the ice"},
    "reclaimed": {"RESOURCE": "wild growth: herbs and seeds"},
    "aether_surge": {"RESOURCE": "the surge's richest aether", "DISCOVERY": "the surge has uncovered something old"},
}
ANCHOR_EXTRA = {
    "unmooring": {"RESOURCE": 2, "EVENT": 1}, "siege": {"ENEMY_POST": 6, "NPC_POST": 2},
    "lockdown": {"ENEMY_POST": 5, "EVENT": 2}, "stormhawk": {"RESOURCE": 2, "EVENT": 1},
    "rime": {"RESOURCE": 1, "DISCOVERY": 1}, "reclaimed": {"RESOURCE": 3, "DISCOVERY": 1},
    "aether_surge": {"DISCOVERY": 2, "RESOURCE": 2},
}


def anchors_on_decks(ctx):
    counts = {"COMBAT": {"ENEMY_POST": 4, "RESOURCE": 2, "EVENT": 1},
              "PATH": {"ENEMY_POST": 1, "RESOURCE": 1},
              "SIDE": {"DISCOVERY": 2, "RESOURCE": 2},
              "CAP": {"DISCOVERY": 1, "RESOURCE": 1},
              "BOSS": {"EVENT": 2},
              "ENTRY": {"NPC_POST": 2}}.get(role(ctx.p), {})
    extra = ANCHOR_EXTRA.get(ctx.scenario, {})
    notes = ANCHOR_NOTES.get(ctx.scenario, {})
    for kind, n in counts.items():
        for _ in range(extra.get(kind, n)):
            for _t in range(40):
                c = ctx.uniform()
                if c is None:
                    break
                z0 = ctx.clear(c[0], c[1], 2.0, 3.0)
                if z0 is not None:
                    ctx.p.solid("anchor " + kind.lower(), c[0], c[1], 2.0, z0, z0 + 3.0)
                    add_anchor(ctx.p, kind, c[0], c[1], z0, notes.get(kind, ""))
                    break
    for d in sorted(ctx.open):
        x, y, _ = mouth(d)
        add_anchor(ctx.p, "BLOCKER", x, y, note=d)
        if BLOCKER_SHAPES.get(ctx.scenario):
            ctx.p.anchors[-1]["mesh"] = "scn_prop_blocker_%s" % ctx.scenario


# ==========================================================================
# The seven structure hooks (architecture only -- props are scattered)
# ==========================================================================
# Filled in by sky_citadel_structures.py below; each is fn(ctx).
STRUCTURES = {}
exec(open(os.path.join(HERE, "sky_citadel_ships.py"), encoding="utf-8").read(), globals())
exec(open(os.path.join(HERE, "sky_citadel_styles.py"), encoding="utf-8").read(), globals())
exec(open(os.path.join(HERE, "sky_citadel_structures.py"), encoding="utf-8").read(), globals())


def make_hook(scenario):
    def hook(p):
        p.anchors = []
        p.blockers = []
        reserve_blockers(p)
        ctx = Ctx(p, scenario)
        STRUCTURES[scenario](ctx)
        LOOKS[scenario](ctx)
        # the scenario's own parts: attached or gone, and none through a rail
        tags = K["kit_tags"]()
        K["settle"](p, tags, K["SETTLE_LOG"], scenario=True)
        K["unclip"](p, tags, K["SETTLE_LOG"])
        K["settle"](p, tags, K["SETTLE_LOG"], scenario=True)
        ctx.refresh()
        build_blockers(ctx)
        anchors_on_decks(ctx)
        for prop in p.props + p.blockers:   # last-digit noise off, so copies share a mesh
            prop["verts"] = [Vector((round(v.x, 4), round(v.y, 4), round(v.z, 4))) for v in prop["verts"]]
    return hook


# ==========================================================================
# Spawn points: where the game may stand a scattered prop on this piece
# ==========================================================================

RING_RADII = (1.5, 2.5, 3.5, 5.0, 6.5, 8.0, 10.0, 12.0, 15.0)
FOOT_LABELS = ("tower", "spire", "turbine", "lighthouse", "light obelisk", "banner mast", "signal mast",
               "tree trunk", "colonnade", "dome", "obelisk")


def _footprints(p):
    """2D obstacles on or near the deck: (kind, shape-or-bounds, z0, z1)."""
    obs = []
    for lab, s in p.solids:
        obs.append((lab, s))
    for prop in p.props:
        pts = [prop["matrix"] @ v for v in prop["verts"]]
        if not pts:
            continue
        mn = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
        mx = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
        obs.append(("prop " + prop["label"], ("box", mn.x - 0.5, mx.x + 0.5, mn.y - 0.5, mx.y + 0.5, mn.z, mx.z)))
    for fx in p.fixtures:
        for part in fx["parts"]:
            pts = [fx["matrix"] @ v for v in part["verts"]]
            mn = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
            mx = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
            obs.append(("fixture", ("box", mn.x - 0.5, mx.x + 0.5, mn.y - 0.5, mx.y + 0.5, mn.z, mx.z)))
    return obs


def _clearance(shape, x, y):
    """Distance from (x, y) to the footprint (negative inside)."""
    if shape[0] == "cyl":
        return math.hypot(x - shape[1], y - shape[2]) - shape[3]
    _, x0, x1, y0, y1 = shape[:5]
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    if dx == 0 and dy == 0:
        return -min(x - x0, x1 - x, y - y0, y1 - y)
    return math.hypot(dx, dy)


def spawn_points(p):
    """-> (encoded ground points, encoded air points, count)."""
    ground = Ground(p)
    o = openings(p)
    polys = deck_polys(p)
    obs = _footprints(p)
    feet = [s for lab, s in p.solids if s[0] == "cyl" and lab in FOOT_LABELS]
    G, O = SC["GRID"], SC["ORIGIN"]
    enc, n = [], 0
    for gz in range(0, 43):
        for gx in range(0, 43):
            x, y = O + G * gx, O + G * gz
            if abs(x) > HALF - 4 or abs(y) > HALF - 4 or in_corridor(p, x, y, o=o):
                continue
            h = ground.z_at(x, y)
            if h is None or h[1] < 0.95 or not (-1.0 < h[0] < 8.0):
                continue
            z = h[0]
            # obstacles standing in the prop's height band
            rob = 99.0
            for lab, s in obs:
                sz0, sz1 = (s[4], s[5]) if s[0] == "cyl" else (s[5], s[6])
                if sz1 < z + 0.2 or sz0 > z + 6.0:
                    continue
                rob = min(rob, _clearance(s, x, y))
            if rob < 1.5:
                continue
            r = 0.0
            for rad in RING_RADII:
                if rad > rob:
                    break
                ok = True
                for k in range(12):
                    a = 2 * math.pi * k / 12
                    qx, qy = x + math.cos(a) * rad, y + math.sin(a) * rad
                    if in_corridor(p, qx, qy, o=o):
                        ok = False
                        break
                    hk = ground.z_at(qx, qy)
                    if hk is None or hk[1] < 0.95 or abs(hk[0] - z) > 0.3:
                        ok = False
                        break
                if not ok:
                    break
                r = rad
            if r < 1.5:
                continue
            # headroom: structure above, or anything afloat over this spot
            head = ground.up(x, y, z)
            for lab, s in p.floats:
                if (_clearance(s, x, y) < 1.0) and (s[4] if s[0] == "cyl" else s[5]) > z:
                    head = min(head, (s[4] if s[0] == "cyl" else s[5]) - z)
            wall, direction = 0, 0
            if polys:
                d, (nx, ny) = min((edge_near(q, x, y) for q in polys), key=lambda t: t[0])
                if d < SC["WALL"]:
                    wall = 1
                    direction = int(round(math.degrees(math.atan2(ny, nx)) / 45.0)) % 8
            tower = int(any(math.hypot(x - s[1], y - s[2]) < s[3] + 6 for s in feet))
            enc.append(SC["encode_point"](gx, gz, z, int(r), wall, direction, tower, int(min(head, 30) // 2)))
            n += 1
    air = []
    A = SC["AIR_GRID"]
    for gz in range(0, 16):
        for gx in range(0, 16):
            x, y = O + A * gx, O + A * gz
            if abs(x) > HALF - 12 or abs(y) > HALF - 12:
                continue
            h = ground.z_at(x, y, top=60)
            if h is None:
                if not polys or min(edge_dist(q, x, y) for q in polys) > 26:
                    continue
                base = 0.0
            else:
                base = h[0]
            lo, hi = None, None
            for zz in range(int(base) + 8, int(base) + 26, 2):
                ok = free_for_float(p, ("cyl", x, y, SC["AIR_R"], zz - 4, zz + 4))
                if ok and lo is None:
                    lo = zz
                if ok:
                    hi = zz
                elif lo is not None:
                    break
            if lo is not None and hi - lo >= 2:
                air.append(SC["encode_air"](gx, gz, lo, hi))
    return "".join(enc), "".join(air), n


# ==========================================================================
# Prop library and pools
# ==========================================================================

def _letters(n):
    s = ""
    while True:
        s = chr(97 + n % 26) + s
        n = n // 26 - 1
        if n < 0:
            return s


def build_library():
    """Every family variant built once at the origin: its mesh soup and its
    measured footprint. -> {kind name: {...}}"""
    lib = {}
    for fam in FAMILIES.values():
        kept = []       # (faces, mats, size) of the variants this family keeps
        for v in range(fam["n"]):
            shell = K["Piece"]("%s/%d" % (fam["name"], v), "scatter")
            shell.cur_family = fam
            with as_prop(shell, "scatter", I4):
                fam["fn"](shell, v)
            prop = shell.props[0]
            # A variant built the same way as one already kept, in proportions
            # the game's own scale and turn cover, is not a new prop: drop it
            # (owner, 2026-09-23 -- no near-duplicates in the library).
            vmn, vmx = K["_bounds"](prop["verts"])
            sig = (tuple(tuple(f) for f in prop["faces"]), tuple(prop["mats"]))
            if any(s == sig and K["_stretchable"](sz, vmx - vmn) for s, sz in kept):
                continue
            kept.append((sig, vmx - vmn))
            name = "sct_%s_%s" % (fam["name"], _letters(len(kept) - 1))   # sct_: scattered, never a fixed prop
            r0 = max(math.hypot(q.x, q.y) for q in prop["verts"])
            dv, df, dm = K["detail"](prop["verts"], prop["faces"], prop["mats"], name, r0)
            prop = {"verts": dv, "faces": df, "mats": dm}
            verts = [Vector((round(q.x, 4), round(q.y, 4), round(q.z, 4))) for q in prop["verts"]]
            mn = Vector((min(q.x for q in verts), min(q.y for q in verts), min(q.z for q in verts)))
            mx = Vector((max(q.x for q in verts), max(q.y for q in verts), max(q.z for q in verts)))
            radius = max(math.hypot(q.x, q.y) for q in verts) + 0.3
            centre = (mn + mx) / 2
            lib[name] = {
                "family": fam["name"], "verts": verts, "faces": prop["faces"], "mats": prop["mats"],
                "R": round(radius, 2), "H": round(mx.z, 2), "min": mn, "max": mx, "centre": centre,
                "anim": fam["anim"], "tier": fam["tier"], "interact": fam["interact"], "air": fam["air"],
            }
    return lib


def kinds_of(family, lib):
    return sorted(k for k, v in lib.items() if v["family"] == family)


def single(family, weight=None, rule=None, scale=None, align=None):
    fam = FAMILIES[family]
    return {"Family": family, "Weight": weight if weight is not None else fam["weight"],
            "Rule": rule or fam["rule"], "Scale": list(scale or fam["scale"]), "Align": align or fam["align"]}


def member(family, count, ring, rule=None, scale=None, align=None):
    e = single(family, 1, rule, scale, align)
    e.update({"Count": list(count), "Ring": list(ring)})
    return e


# Groups make a run coherent: a raider camp, a nest site, an epicentre. Singles
# fill in around them. Density is per mille; PointsPer is how many spawn
# points each prop is budgeted (fewer props on small pieces, never a wall).
POOLS = {
    "base": {"Density": [500, 1100], "PointsPer": 34, "Min": 0, "Max": 14,
             "Groups": [
                 {"Id": "Supplies", "Chance": 45, "Core": single("supply_crates"),
                  "Members": [member("casks", (1, 2), (4, 10)), member("hand_cart", (0, 1), (5, 12)),
                              member("toolkit", (0, 1), (3, 8))]},
                 {"Id": "Garden", "Chance": 35, "Core": single("planter", rule="Open"),
                  "Members": [member("flowers", (1, 3), (4, 12)), member("statue", (0, 1), (8, 16))]}],
             "Singles": [single("supply_crates", 3), single("casks", 2), single("planter", 2), single("lantern", 3),
                         single("statue", 1), single("flowers", 2), single("console", 1)],
             "Air": []},
    "siege": {"Density": [700, 1300], "PointsPer": 24, "Min": 2, "Max": 30,
              "Groups": [
                  {"Id": "RaiderCamp", "Chance": 75, "Core": single("bonfire", scale=(1100, 1400)),
                   "Members": [member("raider_tent", (2, 4), (8, 22)), member("barrels", (1, 3), (4, 14)),
                               member("loot_pile", (0, 1), (3, 10)), member("raider_banner", (1, 2), (5, 14)),
                               member("prisoner_cage", (0, 1), (8, 18)), member("trophy_pike", (0, 2), (6, 16)),
                               member("campfire", (0, 1), (14, 26))]},
                  {"Id": "Checkpoint", "Chance": 55, "Core": single("barricade"),
                   "Members": [member("stake_wall", (1, 2), (6, 14), align="Random"),
                               member("raider_crates", (1, 2), (4, 10)), member("ballista", (0, 1), (6, 14))]},
                  {"Id": "Scrapyard", "Chance": 35, "Core": single("scrap_heap", scale=(1100, 1500)),
                   "Members": [member("scrap_wall", (1, 2), (5, 12)), member("broken_rail", (0, 2), (4, 10)),
                               member("hand_cart", (0, 1), (4, 10))]}],
              "Singles": [single("barrels", 3), single("raider_crates", 3), single("campfire", 2),
                          single("raider_banner", 2), single("rubble", 2), single("scrap_heap", 1),
                          single("supply_crates", 1), single("trophy_pike", 1)],
              "Air": []},
    "lockdown": {"Density": [600, 1200], "PointsPer": 26, "Min": 2, "Max": 26,
                 "Groups": [
                     {"Id": "DefencePost", "Chance": 70, "Core": single("sentinel_turret"),
                      "Members": [member("laser_fence", (1, 2), (5, 12)), member("barrier_block", (2, 3), (4, 12)),
                                  member("alarm_post", (0, 1), (3, 9))]},
                     {"Id": "Checkpoint", "Chance": 50, "Core": single("console"),
                      "Members": [member("barrier_block", (1, 3), (4, 10)), member("security_crate", (1, 2), (4, 10)),
                                  member("floor_emitter", (0, 1), (6, 12))]},
                     {"Id": "Watch", "Chance": 35, "Core": single("searchlight"),
                      "Members": [member("cable_spool", (1, 2), (3, 8)), member("toolkit", (0, 1), (3, 8))]}],
                 "Singles": [single("barrier_block", 3), single("sentinel_pylon", 2), single("alarm_post", 2),
                             single("security_crate", 2), single("floor_emitter", 2), single("laser_fence", 1),
                             single("cable_spool", 1)],
                 "Air": [{"Family": "drone", "Count": [1, 3]}]},
    "stormhawk": {"Density": [600, 1200], "PointsPer": 28, "Min": 2, "Max": 22,
                  "Groups": [
                      {"Id": "NestSite", "Chance": 60, "Core": single("nest"),
                       "Members": [member("bone_pile", (2, 4), (16, 34)), member("egg_shells", (1, 2), (14, 28)),
                                   member("fallen_feather", (2, 5), (10, 32)), member("rubble", (0, 2), (14, 30))]},
                      {"Id": "StrikeSite", "Chance": 50, "Core": single("lightning_rod"),
                       "Members": [member("smashed_crate", (1, 2), (4, 12)), member("fallen_feather", (1, 3), (4, 14)),
                                   member("pillar_segment", (0, 1), (6, 14))]}],
                  "Singles": [single("fallen_feather", 4), single("bone_pile", 2), single("smashed_crate", 2),
                              single("rubble", 2), single("perch", 1), single("mossy_rock", 1), single("loot_pile", 1)],
                  "Air": [{"Family": "storm_feather", "Count": [1, 4]}]},
    "rime": {"Density": [700, 1300], "PointsPer": 22, "Min": 3, "Max": 30,
             "Groups": [
                 {"Id": "Camp", "Chance": 45, "Core": single("warming_brazier"),
                  "Members": [member("frozen_crate", (1, 2), (4, 10)), member("snow_drift", (1, 3), (6, 16), rule="Any"),
                              member("campfire", (0, 1), (8, 16))]},
                 {"Id": "IceField", "Chance": 60, "Core": single("ice_spikes", scale=(2000, 2600)),
                  "Members": [member("ice_spikes", (2, 4), (6, 18), scale=(900, 1600)),
                              member("ice_boulder", (1, 2), (6, 16)), member("frost_crystals", (1, 3), (4, 12), rule="Any")]},
                 {"Id": "FrozenFind", "Chance": 30, "Core": single("frozen_figure"),
                  "Members": [member("icicle_pile", (1, 2), (4, 10), rule="Any")]}],
             "Singles": [single("snow_drift", 8), single("ice_spikes", 2), single("frost_crystals", 3),
                         single("ice_boulder", 2), single("icicle_pile", 2)],
             "Air": []},
    "reclaimed": {"Density": [700, 1300], "PointsPer": 20, "Min": 3, "Max": 34,
                  "Groups": [
                      {"Id": "Grove", "Chance": 65, "Core": single("sapling", scale=(1300, 1700)),
                       "Members": [member("bush", (2, 4), (5, 14)), member("fern", (2, 4), (3, 10), rule="Any"),
                                   member("flowers", (1, 2), (4, 12)), member("grass_tuft", (2, 5), (3, 12))]},
                      {"Id": "MossBank", "Chance": 60, "Core": single("moss_mound", scale=(1200, 1500)),
                       "Members": [member("moss_mound", (1, 3), (4, 12), scale=(700, 1000)),
                                   member("mushrooms", (0, 2), (3, 8), rule="Any"), member("grass_tuft", (1, 3), (3, 8))]},
                      {"Id": "Ruin", "Chance": 40, "Core": single("pillar_segment"),
                       "Members": [member("rubble", (1, 2), (4, 12)), member("overgrown_crate", (0, 1), (4, 10), rule="Any"),
                                   member("fallen_log", (0, 1), (6, 14)), member("stump", (0, 1), (6, 14))]}],
                  "Singles": [single("moss_mound", 5), single("bush", 4), single("grass_tuft", 4), single("fern", 3),
                              single("mossy_rock", 2), single("mushrooms", 2), single("stump", 1),
                              single("smashed_crate", 1), single("statue", 1)],
                  "Air": []},
    "aether_surge": {"Density": [700, 1300], "PointsPer": 24, "Min": 3, "Max": 28,
                     "Groups": [
                         {"Id": "Epicentre", "Chance": 85, "Core": single("aether_cluster", scale=(2600, 3400)),
                          "Members": [member("aether_cluster", (3, 6), (8, 30), scale=(900, 1800)),
                                      member("crystal_rubble", (1, 3), (6, 20)), member("aether_geode", (0, 1), (10, 26)),
                                      member("glow_pool", (0, 1), (8, 20))]},
                         {"Id": "Resonance", "Chance": 40, "Core": single("resonator"),
                          "Members": [member("aether_cluster", (1, 3), (5, 12), scale=(800, 1300))]}],
                     "Singles": [single("aether_cluster", 4), single("crystal_rubble", 3), single("aether_geode", 1),
                                 single("glow_pool", 1)],
                     "Air": [{"Family": "aether_shard", "Count": [2, 4]}, {"Family": "floating_rock", "Count": [0, 2]}]},
    "unmooring": {"Density": [600, 1200], "PointsPer": 26, "Min": 2, "Max": 24,
                  "Groups": [
                      {"Id": "CollapseSite", "Chance": 65, "Core": single("rubble", scale=(1300, 1600)),
                       "Members": [member("rubble", (1, 3), (4, 12), scale=(700, 1100)),
                                   member("broken_rail", (1, 2), (4, 12)), member("pillar_segment", (0, 1), (6, 14)),
                                   member("cracked_plate", (0, 1), (6, 16))]},
                      {"Id": "RepairPost", "Chance": 50, "Core": single("stabilizer"),
                       "Members": [member("hazard_beacon", (1, 3), (4, 12)), member("toolkit", (0, 1), (3, 8)),
                                   member("cable_spool", (0, 1), (3, 8))]}],
                  "Singles": [single("rubble", 3), single("hazard_beacon", 3), single("broken_rail", 2),
                              single("cracked_plate", 2), single("supply_crates", 1), single("scrap_heap", 1)],
                  "Air": [{"Family": "fragment", "Count": [1, 3]}, {"Family": "floating_rock", "Count": [0, 2]}]},
}


def resolve_pool(pool, lib):
    """Expand family names into kind lists, for scatter_core and the game."""
    def entry(e):
        out = dict(e)
        out["Kinds"] = kinds_of(e["Family"], lib)
        return out
    return {"Density": pool["Density"], "PointsPer": pool["PointsPer"], "Min": pool["Min"], "Max": pool["Max"],
            "Groups": [{"Id": g["Id"], "Chance": g["Chance"], "Core": entry(g["Core"]),
                        "Members": [entry(m) for m in g["Members"]]} for g in pool["Groups"]],
            "Singles": [entry(s) for s in pool["Singles"]],
            "Air": [{"Kinds": kinds_of(a["Family"], lib), "Count": a["Count"]} for a in pool["Air"]]}


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
        if scenario:
            # the scenario's own architecture: its towers, spires, crowns,
            # rims and floors in place of the base kit's (sky_citadel_styles.py)
            with styled(scenario):
                p = builder()
        else:
            p = builder()
        if scenario:
            p.name = "%s__%s" % (p.name, scenario)
        if not hasattr(p, "anchors"):
            p.anchors, p.blockers = [], []
        K["PIECES_BY_NAME"][p.name] = p
        p.spawn, p.air, p.nspawn = spawn_points(p)
        obj = K["to_object"](p, mats, coll)
        obj["scenario"] = scenario or "base"
        obj.location = (i * ROW, -row_i * ROW * 1.25, 0)
        pieces.append(p)
        objs.append(obj)
    K["SCENARIO_HOOK"] = None
    return pieces, objs


def _kind_mesh(name, k, mats):
    me = bpy.data.meshes.get("lib_" + name)
    if me:
        return me
    shell = K["Piece"]("lib_" + name, "library")
    shell.verts, shell.faces, shell.fmat = list(k["verts"]), k["faces"], k["mats"]
    obj = K["to_object"](shell, mats, bpy.context.scene.collection)
    me = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    return me


def preview_fixed(pieces, objs, mats, coll):
    """Every fixed (architecture) prop and fixture drawn in place."""
    for p, obj in zip(pieces, objs):
        parts = [(prop["matrix"], prop["verts"], prop["faces"], prop["mats"]) for prop in p.props]
        for fx in p.fixtures:
            parts += [(fx["matrix"], part["verts"], part["faces"], part["mats"]) for part in fx["parts"]]
        for i, (M, verts, faces, fmats) in enumerate(parts):
            shell = K["Piece"]("%s__fixed%03d" % (p.name, i), "preview")
            shell.verts, shell.faces, shell.fmat = list(verts), faces, fmats
            o = K["to_object"](shell, mats, coll)
            o.matrix_world = obj.matrix_world @ M
            o.parent = obj
            o.matrix_parent_inverse = obj.matrix_world.inverted()


def preview_scatter(pieces, objs, pool, lib, mats, coll, seed):
    """One run's scatter, exactly as the game would place it for this seed."""
    total = 0
    for p, obj in zip(pieces, objs):
        # the key a chunk copy standing at the layout's origin gets in the game
        # (ScatterCore.keyFor), so the preview IS that run's scatter
        rows = SC["scatter"](p.spawn, p.air, pool, lib, seed, K["_content_id"](p.name) + "@0,0")
        for i, r in enumerate(rows):
            me = _kind_mesh(r["kind"], lib[r["kind"]], mats)
            o = bpy.data.objects.new("%s__s%d_%03d" % (p.name, seed % 1000, i), me)
            coll.objects.link(o)
            o.matrix_world = obj.matrix_world @ xf(r["x"], r["y"], r["z"], r["yaw"]) @ \
                Matrix.Diagonal((r["scale"], r["scale"], r["scale"], 1.0))
            o.parent = obj
            o.matrix_parent_inverse = obj.matrix_world.inverted()
        total += len(rows)
    return total


def write_anchors(path, scenario, pieces):
    lines = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py.",
        "-- Do not edit by hand. Gameplay anchors for the '%s' scenario kit:" % scenario,
        "-- where the Fate systems may place resources, discoveries, enemy and NPC",
        "-- posts and events, and the blocker each socket may be closed with. Positions",
        "-- are the chunk's local studs (x east, y up, z south), like the prop placements.",
        "return {",
    ]
    for p in pieces:
        lines.append('\t["%s"] = {' % K["_content_id"](p.name))
        for a in p.anchors:
            x, y, z = a["pos"]
            mesh = (', Mesh = "%s"' % a["mesh"]) if a.get("mesh") else ""
            lines.append('\t\t{ Kind = "%s", Pos = { %.2f, %.2f, %.2f }, Note = %s%s },'
                         % (a["kind"], x, z, -y, '"%s"' % a["note"].replace('"', "'"), mesh))
        lines.append("\t},")
    lines.append("}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return sum(len(p.anchors) for p in pieces)


# ---- the game's scatter data -----------------------------------------------------

def _lua(v, ind=""):
    if isinstance(v, dict):
        inner = ", ".join("%s = %s" % (k, _lua(x)) for k, x in v.items())
        return "{ %s }" % inner
    if isinstance(v, (list, tuple)):
        return "{ %s }" % ", ".join(_lua(x) for x in v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return '"%s"' % v
    if isinstance(v, float):
        return ("%.3f" % v).rstrip("0").rstrip(".")
    if v is None:
        return "nil"
    return str(v)


def write_scatter_luau(lib, pools, sets):
    """src/shared/Content/Scatter/SkyCitadel/: init.luau (kinds, pools) and
    one Points_<Set>.luau per set of pieces."""
    os.makedirs(SCATTER_LUAU, exist_ok=True)
    to_game = K["_TO_GAME"]
    lines = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py.",
        "-- Do not edit by hand. Sky Citadel's scatter: the prop library the game",
        "-- scatters at map generation (Kinds), the pools each set draws from (Pools),",
        "-- and per chunk the spawn points it may use (the Points_* children).",
        "-- ScatterCore reads it; scatter_core.py is the same algorithm in the kit.",
        "",
        "local Points = {}",
        "for _, module in script:GetChildren() do",
        "\tif module:IsA(\"ModuleScript\") then",
        "\t\tfor id, row in require(module) :: any do",
        "\t\t\tPoints[id] = row",
        "\t\tend",
        "\tend",
        "end",
        "",
        "return {",
        '\tId = "SKY_CITADEL",',
        "\tGrid = %d, Origin = %d, AirGrid = %d, Gap = %s," % (SC["GRID"], SC["ORIGIN"], SC["AIR_GRID"], _lua(SC["GAP"])),
        "\tKinds = {",
    ]
    for name in sorted(lib):
        k = lib[name]
        size = to_game @ (k["max"] - k["min"])
        off = to_game @ k["centre"]
        lines.append("\t\t%s = { R = %s, H = %s, Anim = \"%s\", Tier = %d%s, Size = { %s }, Offset = { %s } }," % (
            name, _lua(float(k["R"])), _lua(float(k["H"])), k["anim"], k["tier"],
            (', Interact = "%s"' % k["interact"]) if k["interact"] else "",
            ", ".join(_lua(abs(float(c))) for c in size), ", ".join(_lua(float(c)) for c in off)))
    lines.append("\t},")
    lines.append("\tPools = {")
    for set_name, pool in pools.items():
        lines.append("\t\t%s = %s," % (set_name.title().replace("_", ""), _lua(pool)))
    lines.append("\t},")
    lines.append("\tPoints = Points,")
    lines.append("}")
    with open(os.path.join(SCATTER_LUAU, "init.luau"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    for set_name, pieces in sets.items():
        out = ["--!strict", "-- GENERATED. Spawn points per chunk: see scatter_core.py for the encoding.", "return {"]
        for p in pieces:
            out.append('\t["%s"] = { Pool = "%s", Ground = "%s", Air = "%s" },' % (
                K["_content_id"](p.name), set_name.title().replace("_", ""), p.spawn, p.air))
        out.append("}")
        with open(os.path.join(SCATTER_LUAU, "Points_%s.luau" % set_name.title().replace("_", "")), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")


PARITY = os.path.join(REPO, "tests", "scatter_parity.luau")
MANIFEST = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "IMPORT_MANIFEST.md")
MANIFEST_JSON = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "import_manifest.json")


def _tri_count(verts_faces):
    return sum(len(f) - 2 for f in verts_faces)


# ---- the grouped export: two files, everything in folders ---------------------

IMPORT_DIR = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "import")
CHUNKS_FBX = "SkyCitadel_Chunks.fbx"
PROPS_FBX = "SkyCitadel_Props.fbx"


def export_grouped(path, root, groups):
    """One FBX: an empty `root`, a child empty per group, and each group's
    meshes under it at the origin -- so the import is ONE Model holding one
    folder per set, every MeshPart keeping its own name."""
    made, saved = [], []
    top = bpy.data.objects.new(root, None)
    bpy.context.scene.collection.objects.link(top)
    made.append(top)
    for gname, objs in groups:
        g = bpy.data.objects.new(gname, None)
        bpy.context.scene.collection.objects.link(g)
        g.parent = top
        made.append(g)
        for o in objs:
            saved.append((o, o.parent, o.location.copy(), o.matrix_parent_inverse.copy()))
            o.parent = g
            o.matrix_parent_inverse.identity()
            o.location = (0, 0, 0)
    bpy.context.view_layer.update()
    sel = made + [o for _, objs in groups for o in objs]
    bpy.ops.object.select_all(action="DESELECT")
    for o in sel:
        o.select_set(True)
    bpy.context.view_layer.objects.active = top
    with K["_ui_override"](selected_objects=sel, active_object=top, object=top):
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"EMPTY", "MESH"},
                                 axis_forward="-Z", axis_up="Y", global_scale=1.0, apply_unit_scale=True,
                                 apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True,
                                 use_mesh_modifiers=True, mesh_smooth_type="FACE", colors_type="SRGB",
                                 add_leaf_bones=False, bake_anim=False, path_mode="AUTO")
    for o, par, loc, inv in saved:
        o.parent = par
        o.matrix_parent_inverse = inv
        o.location = loc
    for o in made:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    return path


# ---- the import contract: what the owner imports, names and hands back -------

WORLD_ID = "SKY_CITADEL"
WORLD_TAG = "SC"                      # prefixes every model file name
INCOMING = "assets/rbxm/incoming/sky_citadel"


def model_files(sets):
    """(fbx under assets/export/worlds/sky_citadel/, model name to save it as).
    The model name is the .rbxmx file name AND the name of the Model inside."""
    return [("import/" + CHUNKS_FBX, "SkyCitadel_Chunks"), ("import/" + PROPS_FBX, "SkyCitadel_Props")]


def write_registry(sets, blockers):
    """scenarios/ScenarioKits.luau: ONE place that ties each scenario to its
    pieces, props, scatter pool, anchors, route blocker and atmosphere -- the
    table the loader and FateCore read once the scenario layer is wired."""
    path = os.path.join(SCEN_EXPORT, "ScenarioKits.luau")
    L = ["--!strict",
         "-- GENERATED by assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py.",
         "-- STAGED (not in src/ until the scenario layer is wired). Everything a rolled",
         "-- Sky Citadel scenario needs, by scenario id:",
         "--   Chunks        base chunk id -> this scenario's version of it",
         "--   Model         the imported model holding those chunk meshes",
         "--   ScatterPool   the pool in Content/Scatter/SkyCitadel",
         "--   Props         rows keyed by the scenario chunk ids in Props_Scenarios.luau",
         "--   Anchors       the gameplay anchors file for this kit",
         "--   Blocker       the mesh a closed socket is filled with",
         "--   Environment   the key in Environments_Scenarios.luau (its atmosphere)",
         "return {",
         '	WorldId = "%s",' % WORLD_ID,
         "\t-- Chunk meshes: SkyCitadel_Chunks/<Model>/<mesh>. Props: SkyCitadel_Props/<folder>/<mesh>.",
         '\tChunkModel = "SkyCitadel_Chunks",',
         '\tPropModel = "SkyCitadel_Props",',
         '\tPropFolders = { "Base", "Scenarios", "Scatter" },',
         '\tBase = { Model = "Base", ScatterPool = "Base" },',
         "	Kits = {"]
    base_ids = [K["_content_id"](p.name) for p in sets["base"]]
    for s in SCENARIOS:
        key = s.upper()
        L.append("		%s = {" % key)
        L.append('			Name = "%s",' % s.replace("_", " ").title())
        L.append('\t\t\tModel = "%s",' % s.title().replace("_", ""))
        L.append('			ScatterPool = "%s",' % s.title().replace("_", ""))
        L.append('			Props = "Props_Scenarios",')
        L.append('			Anchors = "Anchors_%s",' % s)
        if s in blockers:
            L.append('			Blocker = "%s",' % blockers[s])
        L.append('			Environment = "%s",' % key)
        L.append("			Chunks = {")
        for bid in base_ids:
            L.append('				%s = "%s__%s",' % (bid, bid, key))
        L.append("			},")
        L.append("		},")
    L.append("	},")
    L.append("}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return path


def write_import_steps(sets):
    """IMPORT_STEPS.md: the owner's checklist, nothing else in it."""
    path = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "IMPORT_STEPS.md")
    files = model_files(sets)
    L = ["# Sky Citadel: import steps",
         "",
         "GENERATED on every export. Follow top to bottom. Nothing else is needed.",
         "",
         "Two files: every chunk in one, every prop in the other. Each imports as one Model",
         "with a folder per set inside (chunks: Base + the seven scenarios; props: Base,",
         "Scenarios, Scatter).",
         "",
         "## 1. Import into Roblox Studio (twice)",
         "",
         "For **each of the two rows** below:",
         "",
         "1. Studio: **File > Import 3D**. Pick the FBX from `C:\\Dev\\luckbound\\assets\\export\\worlds\\sky_citadel\\import\\`.",
         "2. Import settings: **Anchored ON**, **Merge Meshes OFF** (every object must stay its own MeshPart),",
         "   **Rig: none**. Leave names alone.",
         "3. It lands as one Model in Workspace. Check its name matches the right column (rename if not).",
         "4. Right-click the Model > **Save to File...** > type **.rbxmx** > save it into",
         "   `C:\\Dev\\luckbound\\%s\\` with that same name." % INCOMING.replace("/", "\\"),
         "5. Delete the Model from Workspace before the next row.",
         "",
         "| # | Import this FBX | Save the Model as |",
         "|---|---|---|"]
    for i, (fbx, name) in enumerate(files, 1):
        L.append("| %d | `%s` | `%s.rbxmx` |" % (i, fbx.split("/")[-1], name))
    L += ["",
          "**Never rename a MeshPart inside a Model.** Their names are how the game finds them",
          "(every one is listed in `IMPORT_MANIFEST.md`).",
          "",
          "## 2. Hand back",
          "",
          "When all %d files are in `%s\\`, tell Claude:" % (len(files), INCOMING.replace("/", "\\")),
          "",
          "> The Sky Citadel import is in `%s`." % INCOMING,
          "",
          "Claude then checks every file against `IMPORT_MANIFEST.md` (nothing missing, nothing",
          "renamed, every MeshPart has a real mesh id), moves each into place, and wires the kit.",
          "Do not put these files anywhere else, and do not edit the ones already in",
          "`assets/rbxm/props` or `assets/rbxm/maps` -- the live game uses those until the switch.",
          ""]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return path


def write_manifest(sets, objs_by_set, kinds, placements, fixtures, lib, blockers):
    """IMPORT_MANIFEST.md + import_manifest.json: every mesh in every FBX the
    Sky Citadel exports, what it is, and which game data names it -- so an
    import can be checked name by name."""
    import json
    base_props = []
    staged = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "staged_luau", "Props_SkyCitadel.luau")
    if os.path.exists(staged):
        import re
        body = open(staged, encoding="utf-8").read()
        lib_block = body.split("Library = {", 1)[1].split("},", 1)[0]
        base_props = re.findall(r'"([^"]+)"', lib_block)
    kits = []
    for set_name, pieces in sets.items():
        objs = objs_by_set[set_name]
        rows = []
        for p, o in zip(pieces, objs):
            rows.append({"mesh": p.name, "id": K["_content_id"](p.name), "role": role(p),
                         "openings": "".join(sorted(openings(p))), "tris": len(o.data.polygons) and
                         sum(len(f.vertices) - 2 for f in o.data.polygons)})
        fbx = ("sky_citadel_structure.fbx" if set_name == "base"
               else "scenarios/%s/sky_citadel_%s_structure.fbx" % (set_name, set_name))
        kits.append({"set": set_name, "fbx": fbx, "pieces": rows})
    usage = {}
    for piece, rows in placements.items():
        for r in rows:
            u = usage.setdefault(r["prop"], {"anim": r["anim"], "tier": r["tier"], "interact": r.get("interact"),
                                             "copies": 0})
            u["copies"] += 1
            for a in r.get("alts", ()):
                ua = usage.setdefault(a["prop"], {"anim": r["anim"], "tier": r["tier"],
                                                  "interact": r.get("interact"), "copies": 0, "alternate": True})
                ua["copies"] += 1
    fixed = []
    for k in kinds:
        u = usage.get(k["name"], {})
        fixed.append({"mesh": k["name"], "kind": "prop" if k.get("is_prop") else "fixture",
                      "anim": u.get("anim", "-"), "tier": u.get("tier", "-"), "interact": u.get("interact") or "-",
                      "copies": u.get("copies", 0), "alternate": bool(u.get("alternate")),
                      "tris": _tri_count(k["faces"])})
    scatter = []
    for name in sorted(lib):
        k = lib[name]
        fam = FAMILIES[k["family"]]
        scatter.append({"mesh": name, "family": k["family"], "sets": ",".join(fam["sets"]), "anim": k["anim"],
                        "tier": k["tier"], "interact": k["interact"] or "-", "tris": _tri_count(k["faces"])})
    data = {"kits": kits, "base_props": base_props, "scenario_props": fixed, "scatter_props": scatter,
            "blockers": blockers}
    with open(MANIFEST_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)

    L = []
    L.append("# Sky Citadel -- import manifest")
    L.append("")
    L.append("GENERATED by `assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py` on every export.")
    L.append("Do not edit by hand. The same data, machine-readable: `import_manifest.json`.")
    L.append("")
    L.append("Every mesh name below is what the game looks up. Import each FBX so its objects become")
    L.append("MeshParts **named exactly as listed**; nothing here is renamed on import.")
    L.append("")
    L.append("**The steps are in `IMPORT_STEPS.md`.** This file is the reference that checks them.")
    L.append("")
    L.append("| FBX | Saved as (in `%s/`) |" % INCOMING)
    L.append("|---|---|")
    for fbx, name in model_files(sets):
        L.append("| `%s` | `%s.rbxmx` |" % (fbx, name))
    L.append("")
    L.append("## What each file holds, and where it goes after the check")
    L.append("")
    L.append("| File (under `assets/export/worlds/sky_citadel/`) | Meshes | Goes to | Named in |")
    L.append("|---|---|---|---|")
    L.append("| `sky_citadel_structure.fbx` | %d chunk pieces | the chunk library (as the 22 today) | "
             "`Content/Chunks/SkyCitadel.luau` (`Mesh`/asset ids -- 14 pieces not yet listed) |"
             % len(sets["base"]))
    L.append("| `sky_citadel_props.fbx` | %d | `ReplicatedStorage.LuckboundProps` | "
             "`staged_luau/Props_SkyCitadel.luau` -> replaces `Content/Props/SkyCitadel.luau` |" % len(base_props))
    for kit in kits:
        if kit["set"] != "base":
            L.append("| `%s` | %d chunk pieces | the chunk library, as a variant set | "
                     "`scenarios/%s/Anchors_%s.luau` (ids `<BASE>__%s`) |"
                     % (kit["fbx"], len(kit["pieces"]), kit["set"], kit["set"], kit["set"].upper()))
    L.append("| `scenarios/sky_citadel_scenario_props.fbx` | %d | `ReplicatedStorage.LuckboundProps` | "
             "`scenarios/Props_Scenarios.luau`, `Fixtures_Scenarios.luau` |" % len(kinds))
    L.append("| `scenarios/sky_citadel_scatter_props.fbx` | %d | `ReplicatedStorage.LuckboundProps` | "
             "`src/shared/Content/Scatter/SkyCitadel/` (live) |" % (len(lib) + len(blockers)))
    L.append("")
    L.append("Name families never overlap, so all three prop files can share one folder:")
    L.append("`prop_*`/`fix_*` base kit (the live names), `scn_prop_*`/`scn_fix_*` scenario kits,")
    L.append("`sct_*` scattered scenery, `scn_prop_blocker_<scenario>` the route blockers.")
    L.append("")
    L.append("## Chunk pieces")
    L.append("")
    L.append("Role and openings are what the generator matches on (`N/S/E/W` sockets).")
    L.append("Scenario pieces share their base piece's sockets exactly; only what stands on them differs.")
    L.append("")
    for kit in kits:
        L.append("### %s -- `%s`" % (kit["set"], kit["fbx"]))
        L.append("")
        L.append("| Mesh | Content id | Role | Openings | Tris |")
        L.append("|---|---|---|---|---|")
        for r in kit["pieces"]:
            L.append("| `%s` | `%s` | %s | %s | %s |" % (r["mesh"], r["id"], r["role"], r["openings"] or "-", r["tris"]))
        L.append("")
    L.append("## Scenario fixed props and fixtures -- `scenarios/sky_citadel_scenario_props.fbx`")
    L.append("")
    L.append("`Alternate` = a version the game may draw in place of a row's own mesh (the five raider ships).")
    L.append("")
    L.append("| Mesh | Kind | Anim | Tier | Interact | Copies | Alternate | Tris |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in fixed:
        L.append("| `%s` | %s | %s | %s | %s | %d | %s | %d |" % (r["mesh"], r["kind"], r["anim"], r["tier"],
                                                              r["interact"], r["copies"],
                                                              "yes" if r["alternate"] else "", r["tris"]))
    L.append("")
    L.append("## Scattered scenery -- `scenarios/sky_citadel_scatter_props.fbx`")
    L.append("")
    L.append("| Mesh | Family | Sets | Anim | Tier | Interact | Tris |")
    L.append("|---|---|---|---|---|---|---|")
    for r in scatter:
        L.append("| `%s` | %s | %s | %s | %s | %s | %d |" % (r["mesh"], r["family"], r["sets"], r["anim"], r["tier"],
                                                          r["interact"], r["tris"]))
    L.append("")
    L.append("Route blockers (one per scenario, placed only when a run closes a socket; see each kit's")
    L.append("`Anchors_<scenario>.luau`, `Kind = \"BLOCKER\"`, `Mesh = ...`): " +
             ", ".join("`%s`" % b for b in sorted(blockers.values())))
    L.append("")
    L.append("## Base kit props -- `sky_citadel_props.fbx`")
    L.append("")
    L.append(", ".join("`%s`" % n for n in base_props) or "(run the base kit export first)")
    L.append("")
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return MANIFEST


def write_parity(lib, pools, sets):
    """tests/scatter_parity.luau: a few real chunks' spawn points, the pools and
    kinds they use, and what scatter_core.py placed for some seeds and keys.
    The Luau suite runs ScatterCore on the same input and must match it."""
    picks = []
    for set_name, pieces in sets.items():
        for i in (1, 9, 23):
            if i < len(pieces) and pieces[i].spawn:
                picks.append((set_name, pieces[i]))
    used_pools = sorted({sn for sn, _ in picks})
    lines = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/sky_citadel/build_sky_citadel_scenarios.py",
        "-- (write_parity). scatter_core.py's placements for real Sky Citadel chunks:",
        "-- ScatterCore must reproduce every one (tests/cases.luau, 'Scatter').",
        "return {",
        "\tSet = {",
        "\t\tGrid = %d, Origin = %d, AirGrid = %d, Gap = %s," % (SC["GRID"], SC["ORIGIN"], SC["AIR_GRID"], _lua(SC["GAP"])),
        "\t\tKinds = {",
    ]
    for name in sorted(lib):
        k = lib[name]
        lines.append("\t\t\t%s = { R = %s, H = %s, Anim = \"%s\", Tier = %d, Size = { 1, 1, 1 }, Offset = { 0, 0, 0 } }," % (
            name, _lua(float(k["R"])), _lua(float(k["H"])), k["anim"], k["tier"]))
    lines.append("\t\t},")
    lines.append("\t\tPools = {")
    for sn in used_pools:
        lines.append("\t\t\t%s = %s," % (sn.title().replace("_", ""), _lua(pools[sn])))
    lines.append("\t\t},")
    lines.append("\t\tPoints = {")
    for sn, pc in picks:
        lines.append('\t\t\t["%s"] = { Pool = "%s", Ground = "%s", Air = "%s" },' % (
            K["_content_id"](pc.name), sn.title().replace("_", ""), pc.spawn, pc.air))
    lines.append("\t\t},")
    lines.append("\t},")
    lines.append("\tCases = {")
    total = 0
    for sn, pc in picks:
        cid = K["_content_id"](pc.name)
        for seed, key in ((20260923, cid + "@0,0"), (7, cid + "@-256,512"), (4000000000, cid + "@1024,-768")):
            rows = SC["scatter"](pc.spawn, pc.air, pools[sn], lib, seed, key)
            total += len(rows)
            lines.append('\t\t{ Chunk = "%s", Seed = %d, Key = "%s", Expect = {' % (cid, seed, key))
            for r in rows:
                lines.append('\t\t\t{ "%s", %.4f, %.4f, %.4f, %d, %.4f },' % (
                    r["kind"], r["x"], r["y"], r["z"], r["yaw"], r["scale"]))
            lines.append("\t\t} },")
    lines.append("\t},")
    lines.append("}")
    with open(PARITY, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total


def main(export=False, save=True, preview=True, sets_only=None):
    K["reset_scene"]()
    mats = K["ensure_materials"]()
    lib = build_library()
    pools = {k: resolve_pool(v, lib) for k, v in POOLS.items()}
    report, all_pieces, sets = {}, [], {}
    fixed = bpy.data.collections.new("Preview_FixedProps")
    bpy.context.scene.collection.children.link(fixed)
    scat = [bpy.data.collections.new("Preview_Scatter_Seed_%d" % s) for s in PREVIEW_SEEDS]
    for c in scat:
        bpy.context.scene.collection.children.link(c)
    for row_i, scen in enumerate([None] + SCENARIOS):
        if sets_only and (scen or "base") not in sets_only:
            continue
        pieces, objs = build_set(scen, mats, row_i)
        bpy.context.view_layer.update()
        set_name = scen or "base"
        counts = []
        if preview:
            preview_fixed(pieces, objs, mats, fixed)
            for c, s in zip(scat, PREVIEW_SEEDS):
                counts.append(preview_scatter(pieces, objs, pools[set_name], lib, mats, c, s))
        ok, rep = K["validate"](objs)
        report[set_name] = {"ok": ok, "failed": [(r["piece"], r["failed"], r["float_problems"][:2],
                                                   r["ground_problems"][:2], r["geometry_problems"][:3])
                                                  for r in rep if not r["ok"]],
                            "tris_max": max(r["tris"] for r in rep),
                            "fixed_props": sum(len(p.props) for p in pieces),
                            "spawn_points": sum(p.nspawn for p in pieces),
                            "scattered": counts}
        sets[set_name] = (pieces, objs)
        if scen:
            all_pieces += pieces
    # the second seed starts hidden: switch collections to compare two runs
    if len(scat) > 1:
        bpy.context.view_layer.layer_collection.children[scat[1].name].hide_viewport = True
    out = {"report": report, "kinds": len(lib)}
    if export:
        bad = {k: v["failed"] for k, v in report.items() if not v["ok"]}
        if bad:
            raise RuntimeError("validation failed; not exporting: %r" % bad)
        os.makedirs(SCEN_EXPORT, exist_ok=True)
        kinds, placements, fixtures = K["prop_library"](all_pieces, prefix="scn_prop_", fix_prefix="scn_fix_")
        libc = bpy.data.collections.new("ScenarioPropLibrary")
        bpy.context.scene.collection.children.link(libc)
        prop_objs = K["props_to_objects"](kinds, mats, libc)
        for o in prop_objs:
            o.location.y -= (len(SCENARIOS) + 2) * ROW * 1.25
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
        # the scatter library: every variant, plus every scenario's blocker shape
        scatter_objs = []
        sc_coll = bpy.data.collections.new("ScatterLibrary")
        bpy.context.scene.collection.children.link(sc_coll)
        for i, name in enumerate(sorted(lib)):
            k = lib[name]
            shell = K["Piece"](name, "scatter")
            shell.verts = [v - k["centre"] for v in k["verts"]]
            shell.faces, shell.fmat = k["faces"], k["mats"]
            o = K["to_object"](shell, mats, sc_coll)
            o.location = ((i % 16) * 30.0, -(len(SCENARIOS) + 4) * ROW * 1.25 - (i // 16) * 30.0, 0)
            scatter_objs.append(o)
        blockers = {}
        for scen in SCENARIOS:
            for p in sets[scen][0]:
                if p.blockers and scen not in blockers:
                    b = p.blockers[0]
                    shell = K["Piece"]("scn_prop_blocker_%s" % scen, "blocker")
                    pts = b["verts"]
                    mn = Vector((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
                    mx = Vector((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
                    shell.verts = [q - (mn + mx) / 2 for q in pts]
                    shell.faces, shell.fmat = b["faces"], b["mats"]
                    o = K["to_object"](shell, mats, sc_coll)
                    o.location = (len(blockers) * 40.0, -(len(SCENARIOS) + 7) * ROW * 1.25, 0)
                    scatter_objs.append(o)
                    blockers[scen] = o.name
        scatter_path = os.path.join(SCEN_EXPORT, "sky_citadel_scatter_props.fbx")
        K["_export_selected"](scatter_objs, scatter_path)
        verified = K["verify_exports"](paths + [props_path, scatter_path])
        for v in verified[:len(paths)]:
            wrong = {k: s for k, s in v["sizes"].items() if any(abs(c - 256) > 0.01 for c in s)}
            if v["meshes"] != len(K["BUILDERS"]) or wrong:
                raise RuntimeError("%s did not come back %d x 256^3: %r" % (v["file"], len(K["BUILDERS"]), wrong))
        if verified[-2]["meshes"] != len(kinds):
            raise RuntimeError("scenario prop export came back with %d meshes" % verified[-2]["meshes"])
        if verified[-1]["meshes"] != len(scatter_objs):
            raise RuntimeError("scatter export came back with %d meshes" % verified[-1]["meshes"])
        out["exported"] = [(v["file"], v["meshes"]) for v in verified]
        out["anchors"] = anchors
        out["placements"] = K["write_props_luau"](kinds, placements, os.path.join(SCEN_EXPORT, "Props_Scenarios.luau"))
        out["fixtures"] = K["write_fixtures_luau"](kinds, fixtures, os.path.join(SCEN_EXPORT, "Fixtures_Scenarios.luau"))
        write_scatter_luau(lib, pools, {k: v[0] for k, v in sets.items()})
        # the two files the owner imports: every chunk, every prop, in folders
        os.makedirs(IMPORT_DIR, exist_ok=True)
        base_pieces, base_objs = sets["base"]
        bkinds, bplace, bfix = K["prop_library"](base_pieces)
        bcoll = bpy.data.collections.new("BasePropLibrary")
        bpy.context.scene.collection.children.link(bcoll)
        base_prop_objs = K["props_to_objects"](bkinds, mats, bcoll)
        stage = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "staged_luau")
        os.makedirs(stage, exist_ok=True)
        K["write_props_luau"](bkinds, bplace, os.path.join(stage, "Props_SkyCitadel.luau"))
        K["write_fixtures_luau"](bkinds, bfix, os.path.join(stage, "Fixtures_SkyCitadel.luau"))
        chunk_groups = [("Base", base_objs)] + [(s.title().replace("_", ""), sets[s][1]) for s in SCENARIOS]
        export_grouped(os.path.join(IMPORT_DIR, CHUNKS_FBX), "SkyCitadel_Chunks", chunk_groups)
        export_grouped(os.path.join(IMPORT_DIR, PROPS_FBX), "SkyCitadel_Props",
                       [("Base", base_prop_objs), ("Scenarios", prop_objs), ("Scatter", scatter_objs)])
        vg = K["verify_exports"]([os.path.join(IMPORT_DIR, CHUNKS_FBX), os.path.join(IMPORT_DIR, PROPS_FBX)])
        n_chunks = sum(len(objs) for _, objs in chunk_groups)
        n_props = len(base_prop_objs) + len(prop_objs) + len(scatter_objs)
        if vg[0]["meshes"] != n_chunks or vg[1]["meshes"] != n_props:
            raise RuntimeError("grouped export came back %r, expected %d chunks, %d props"
                               % ([(v["file"], v["meshes"]) for v in vg], n_chunks, n_props))
        wrong = {k: s for k, s in vg[0]["sizes"].items() if any(abs(c - 256) > 0.01 for c in s)}
        if wrong:
            raise RuntimeError("grouped chunks not 256^3: %r" % list(wrong)[:5])
        out["grouped"] = [(v["file"], v["meshes"]) for v in vg]
        out["registry"] = write_registry({k: v[0] for k, v in sets.items()}, blockers)
        out["steps"] = write_import_steps({k: v[0] for k, v in sets.items()})
        out["manifest"] = write_manifest({k: v[0] for k, v in sets.items()}, {k: v[1] for k, v in sets.items()},
                                         kinds, placements, fixtures, lib, blockers)
        out["parity_rows"] = write_parity(lib, pools, {k: v[0] for k, v in sets.items()})
        out["fixed_kinds"] = len(kinds)
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    return out


if __name__ == "__main__":
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    print(main(export="--export" in argv))
