"""Checks on a piece's REAL geometry, not its registered shapes.

The kit's validate() reasons about the boxes and cylinders each builder
registers (solids, floats, slabs). That kept floats apart, but it could not see
two things the owner found walking the third pass (2026-09-23):

  * DETACHED geometry -- an icicle hung a stud outside the rim it was meant to
    hang from, a root that missed the keel: parts that touch nothing and are not
    meant to float;
  * CLIPPING -- one part passing through another that it was never meant to
    meet (a palisade through a turret, a crystal through a railing).

Both are measured here from the mesh itself. Every face is tagged with the
builder that made it (Piece.add records the nearest caller that is not a
primitive), so a report names the builders involved, and a rule can tell an
authored joint (a rail through its posts, a tower sunk into its deck -- both
made by one builder) from a collision between two builders' work.

Executed into the kit namespace by build_sky_citadel_kit.py.
"""

import sys

from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOUCH = 0.12          # studs: closer than this counts as touching
PRIMITIVES = {
    "add", "add_faces", "box", "box_span", "frustum", "torus", "torus_arc", "crystal", "slab", "orb", "lump",
    "half_barrel", "hinge_knuckle", "panel", "tri_panel", "cyl", "lay", "spine", "_slice", "keel",
    "wrapper", "<lambda>", "<genexpr>", "<listcomp>", "__exit__", "__enter__", "helper", "tube", "crystal_spire",
}


def caller_tag(depth=2):
    """The first function up the stack that is not a geometry primitive."""
    f = sys._getframe(depth)
    while f is not None:
        name = f.f_code.co_name
        if name not in PRIMITIVES:
            return name
        f = f.f_back
    return "?"


def _shells(p):
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
        vs = sorted({i for fi in fl for i in p.faces[fi]})
        pts = [p.verts[i] for i in vs]
        mn = [min(v[k] for v in pts) for k in range(3)]
        mx = [max(v[k] for v in pts) for k in range(3)]
        remap = {v: i for i, v in enumerate(vs)}
        tri = [[remap[i] for i in p.faces[fi]] for fi in fl]
        tags = getattr(p, "ftag", None)
        tag = tags[fl[0]] if tags and len(tags) > fl[0] else "?"
        out.append({"faces": fl, "verts": vs, "pts": pts, "tri": tri, "min": mn, "max": mx, "tag": tag,
                    "bvh": None})
    return out


def _bvh(s):
    if s["bvh"] is None:
        s["bvh"] = BVHTree.FromPolygons(s["pts"], s["tri"], epsilon=0.0)
    return s["bvh"]


def _near(a, b, tol):
    return all(a["min"][k] - tol <= b["max"][k] and b["min"][k] - tol <= a["max"][k] for k in range(3))


def _face_normal(pts, poly):
    a, b, c = pts[poly[0]], pts[poly[1]], pts[poly[2]]
    n = (b - a).cross(c - a)
    return n.normalized() if n.length > 1e-9 else n


def _samples(s):
    """Points that must lie on a surface this shell rests against: its
    corners, its face centres and its edge midpoints (a box standing on a beam
    shares a face with it without either's corners being near the other)."""
    if "samples" not in s:
        pts = list(s["pts"])
        for poly in s["tri"]:
            vs = [s["pts"][i] for i in poly]
            c = vs[0].copy()
            for v in vs[1:]:
                c += v
            pts.append(c / len(vs))
            for i in range(len(vs)):
                pts.append((vs[i] + vs[(i + 1) % len(vs)]) / 2)
        s["samples"] = pts
    return s["samples"]


def _close(a, b, tol):
    bb = _bvh(b)
    lo = [b["min"][k] - tol for k in range(3)]
    hi = [b["max"][k] + tol for k in range(3)]
    for v in _samples(a):
        if lo[0] <= v.x <= hi[0] and lo[1] <= v.y <= hi[1] and lo[2] <= v.z <= hi[2]:
            if bb.find_nearest(v, tol)[0] is not None:
                return True
    return False


def _touching(a, b, tol=TOUCH):
    """-> (touch, crossings): whether two shells meet at all, and the pairs of
    their faces that pass through each other."""
    ov = _bvh(a).overlap(_bvh(b))
    if ov:
        return True, ov
    if _close(a, b, tol) or _close(b, a, tol):
        return True, []
    if _enclosed(a, b) or _enclosed(b, a):
        return True, []
    return False, []


def _enclosed(a, b):
    """a sits wholly inside b's volume (a collar buried in a mast): hidden,
    and held by it."""
    if not all(b["min"][k] <= a["min"][k] and a["max"][k] <= b["max"][k] for k in range(3)):
        return False
    c = a["pts"][0]
    bb = _bvh(b)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        if bb.ray_cast(c, Vector(d), 1e4)[0] is None:
            return False
    return True


def analyse(p, float_shapes=(), exempt=lambda s: False):
    """-> dict(detached=[...], clips=[...], shells=n).

    detached: clusters of touching shells not joined to the piece's main body
    (the cluster holding its largest shell, and any cluster holding a deck),
    and not inside a registered float. Each entry: (tags, centre, size).
    clips: pairs of shells from DIFFERENT builders whose faces pass through
    each other, where neither of the crossing faces is a floor or ceiling (a
    thing standing on a deck crosses the deck's top face -- that is contact,
    not clipping). Each: (tagA, tagB, centre, crossings)."""
    S = _shells(p)
    n = len(S)
    parent = list(range(n))
    decks = _deck_centres(p)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    order = sorted(range(n), key=lambda i: S[i]["min"][0])
    clips = []
    for oi, i in enumerate(order):
        a = S[i]
        for j in order[oi + 1:]:
            b = S[j]
            if b["min"][0] > a["max"][0] + TOUCH:
                break
            if not _near(a, b, TOUCH):
                continue
            touch, ov = _touching(a, b)
            if not touch:
                continue
            parent[find(i)] = find(j)
            if not ov or a["tag"] == b["tag"]:
                continue
            if a["max"][2] - a["min"][2] < 0.35 or b["max"][2] - b["min"][2] < 0.35:
                continue        # a floor decal (crack, blot, band): its edges are slivers
            steep = 0
            where = None
            for fa, fb in ov:
                na = _face_normal(a["pts"], a["tri"][fa])
                nb = _face_normal(b["pts"], b["tri"][fb])
                if abs(na.z) > 0.9 or abs(nb.z) > 0.9:
                    continue
                steep += 1
                if where is None:
                    where = a["pts"][a["tri"][fa][0]]
            if steep:
                clips.append((a["tag"], b["tag"], tuple(round(c, 1) for c in where), steep, i, j))
    # the main body: the cluster of the largest shell, plus every cluster with a deck
    def area(s):
        return (s["max"][0] - s["min"][0]) * (s["max"][1] - s["min"][1])

    big = max(range(n), key=lambda i: area(S[i])) if n else None
    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    detached = []
    for root, members in clusters.items():
        if big is not None and find(big) == root:
            continue
        mn = [min(S[i]["min"][k] for i in members) for k in range(3)]
        mx = [max(S[i]["max"][k] for i in members) for k in range(3)]
        if _islet(S, members, decks):      # its own deck: an islet, a stepping plate
            continue
        if any(exempt(S[i]) for i in members):
            continue
        if any(_inside_shape(mn, mx, sh) for sh in float_shapes):
            continue
        tags = sorted({S[i]["tag"] for i in members})
        c = tuple(round((mn[k] + mx[k]) / 2, 1) for k in range(3))
        size = tuple(round(mx[k] - mn[k], 1) for k in range(3))
        detached.append((tags, c, size, [fi for i in members for fi in S[i]["faces"]]))
    return {"detached": detached, "clips": clips, "shells": n, "S": S, "find": find}


def gap_to_rest(p, faces):
    """-> (gap, move): how far the given faces are from the rest of the
    piece, and the translation that would bring them into contact."""
    fs = set(faces)
    rest = [f for i, f in enumerate(p.faces) if i not in fs]
    if not rest:
        return 1e9, None
    used = sorted({v for f in rest for v in f})
    remap = {v: i for i, v in enumerate(used)}
    bvh = BVHTree.FromPolygons([p.verts[v] for v in used], [[remap[v] for v in f] for f in rest])
    best, move = 1e9, None
    pts = set()
    for fi in faces:
        f = p.faces[fi]
        vs = [p.verts[i] for i in f]
        c = sum(vs, Vector()) / len(vs)
        pts.add(tuple(c))
        for v in vs:
            pts.add(tuple(v))
    for q in pts:
        q = Vector(q)
        hit = bvh.find_nearest(q)
        if hit[0] is not None and hit[3] < best:
            best, move = hit[3], hit[0] - q
    return best, move


def _inside_shape(mn, mx, sh, pad=1.5):
    if sh[0] == "cyl":
        _, x, y, r, z0, z1 = sh
        x0, x1, y0, y1 = x - r, x + r, y - r, y + r
    else:
        _, x0, x1, y0, y1, z0, z1 = sh
    return (mn[0] >= x0 - pad and mx[0] <= x1 + pad and mn[1] >= y0 - pad and mx[1] <= y1 + pad
            and mn[2] >= z0 - pad and mx[2] <= z1 + pad)


# ==========================================================================
# Settling a piece: every part attached, or deliberately afloat as a prop
# ==========================================================================

SNAP = 1.5            # a part this close to the piece was meant to touch it
# The builders whose detached parts are the citadel's deliberate anti-grav
# accents -- only these are ever lifted into props. Anything else that touches
# nothing is a fault: dropped from a scenario's additions, reported in the base.
LIFTABLE = {
    "spire", "obelisk", "orrery", "clock_tower", "light_obelisk", "build_spire_court", "build_spire_court_b",
    "build_turbine_hall", "build_cap_crumbling", "lighthouse", "holo_pedestal", "gate", "build_archive",
    "build_side_chapel", "build_path_straight",
}
LIFT_MAX = 32.0       # a part larger than this is architecture, never a prop

# Base-kit tags a scenario's additions may be sunk into: the big masses (a
# crystal growing out of a turret, a root gripping a keel). Anything else a
# scenario part passes through -- a rail, a parapet, a hedge, a bench -- is a
# clip, and the part goes.
EMBED_OK = {
    "tower", "spire", "island", "keel", "standard_keel", "stepped_keel", "shallow_hull", "twin_keel",
    "crystal_root_keel", "engine_keel", "ring_keel", "terrace", "ramp", "skyway_deck", "ascent_deck",
    "bridge_x", "lighthouse", "clock_tower", "light_obelisk", "banner_mast", "signal_mast", "sky_tree",
    "cascade_tower", "holed_block", "arcane_prism", "stepped", "dome", "barracks", "gate",
}
# Scenario parts that HANG (icicles, roots, vines): held at their top, and
# clear of everything below it.
HANGING = {"icicle_ring", "rim_icicles", "frozen_fall", "keel_roots", "vines", "hang_crystals"}
# Scenario builds that STAND on the deck (a palisade, a watchtower, a blast
# wall, a heaved plate): they may cross nothing but the deck they stand on.
FREESTANDING = {"palisade", "watchtower", "blast_wall", "s_unmooring"}
DECKS = {"island", "skyway_deck", "ascent_deck", "terrace", "bridge_x", "ramp", "border_band"}
# What each hanging part may be sunk into at its top (anything else it meets
# on the way down is a clip).
_KEELS = {"keel", "standard_keel", "stepped_keel", "shallow_hull", "twin_keel", "crystal_root_keel",
          "engine_keel", "ring_keel"}
HANG_FROM = {
    "icicle_ring": {"tower"},
    "rim_icicles": DECKS | {"_edge_kerb", "edge_ring", "slab", "build_path_shattered"},
    "frozen_fall": DECKS | {"_edge_kerb", "edge_ring", "rim_icicles", "build_path_shattered"},
    "keel_roots": DECKS | {"_edge_kerb", "edge_ring"},
    "vines": DECKS | {"_edge_kerb", "edge_ring", "build_path_shattered"},
    "hang_crystals": _KEELS | DECKS,
}
# Scenario parts that may bury what they meet: snow drifts over a rail's foot,
# a hedge grown through a fallen parapet's stumps, paint and cracks.
SOFT = {"snow_banks", "overgrown_rim", "blot", "crack", "surface_blot", "surface_crack"}


def drop_faces(p, drop):
    drop = set(drop)
    if not drop:
        return
    keep = [i for i in range(len(p.faces)) if i not in drop]
    newidx = {old: new for new, old in enumerate(keep)}
    p.up = {newidx[i] for i in p.up if i in newidx}
    faces = [p.faces[i] for i in keep]
    p.fmat = [p.fmat[i] for i in keep]
    if len(p.ftag) == len(p.faces):
        p.ftag = [p.ftag[i] for i in keep]
    used = sorted({v for f in faces for v in f})
    vmap = {old: new for new, old in enumerate(used)}
    p.verts = [p.verts[i] for i in used]
    p.faces = [[vmap[v] for v in f] for f in faces]


def _lift(p, faces, label):
    """Faces -> one placed prop, anchored at their box centre, unturned (so
    two identical accents share a mesh)."""
    vs = sorted({v for fi in faces for v in p.faces[fi]})
    pts = [p.verts[v] for v in vs]
    c = Vector(((min(q.x for q in pts) + max(q.x for q in pts)) / 2,
                (min(q.y for q in pts) + max(q.y for q in pts)) / 2,
                (min(q.z for q in pts) + max(q.z for q in pts)) / 2))
    remap = {v: i for i, v in enumerate(vs)}
    verts = [Vector((round(q.x - c.x, 4), round(q.y - c.y, 4), round(q.z - c.z, 4))) for q in pts]
    p.props.append({"label": label, "matrix": Matrix.Translation(c), "verts": verts,
                    "faces": [[remap[v] for v in p.faces[fi]] for fi in faces],
                    "mats": [p.fmat[fi] for fi in faces], "attached": []})
    drop_faces(p, faces)


def _islet(S, members, decks=()):
    """A cluster holding its own deck -- a floating islet, a stepping plate
    of a broken span: afloat by design, and walked on."""
    if any((S[i]["max"][0] - S[i]["min"][0]) * (S[i]["max"][1] - S[i]["min"][1]) > 400
           and S[i]["max"][2] > -1.0 for i in members):
        return True
    for cx, cy in decks:
        for i in members:
            s = S[i]
            if s["min"][0] <= cx <= s["max"][0] and s["min"][1] <= cy <= s["max"][1] and -1.0 < s["max"][2] < 1.0:
                return True
    return False


def _deck_centres(p):
    out = []
    for w, _z0, _z1 in p.slabs:
        n = len(w)
        out.append((sum(q[0] for q in w) / n, sum(q[1] for q in w) / n))
    return out


def _pin(s):
    size = [s["max"][k] - s["min"][k] for k in range(3)]
    return max(size) < 1.0 and s["min"][2] < -95


def settle(p, base_tags, log=None, scenario=False):
    """Attach or lift everything that touches nothing.

    * within SNAP of the piece: moved into contact (a sign a hair off its
      wall, a lantern a stud above its floor);
    * a base-kit part further off and small enough: lifted into an animated
      prop -- the citadel's anti-grav accents (halos, hovering crystals, an
      orrery's rings) are props, which is what lets them move;
    * a scenario's part further off: removed -- it was meant to hang from
      something that is not there.
    Returns the number of parts changed."""
    changed = 0
    decks = _deck_centres(p)
    for _round in range(4):
        r = analyse(p, [s for _, s in p.floats], exempt=_pin)
        if not r["detached"]:
            break
        S, find = r["S"], r["find"]
        clusters = {}
        for i in range(len(S)):
            clusters.setdefault(find(i), []).append(i)
        todo_lift, todo_drop, moved = [], [], False
        for tags, c, size, faces in r["detached"]:
            members = clusters[find(next(i for i in range(len(S)) if S[i]["faces"][0] == faces[0]))]
            if _islet(S, members, decks):
                continue
            gap, move = gap_to_rest(p, faces)
            added = any(t not in base_tags for t in tags)
            liftable = not added and all(t in LIFTABLE for t in tags) and max(size) <= LIFT_MAX
            if gap <= SNAP and move is not None and move.length > 1e-6:
                step = move * ((gap + 0.06) / gap)
                for v in {v for fi in faces for v in p.faces[fi]}:
                    p.verts[v] = p.verts[v] + step
                moved, act = True, "snap"
            elif liftable:
                todo_lift.append((faces, "hover halo" if size[2] < 0.3 * max(size[0], size[1]) else "hover crystal"))
                act = "lift"
            elif added or scenario:
                todo_drop += faces
                act = "drop"
            else:
                act = "KEEP-FAULT"
            changed += 1
            if log is not None:
                log.append((p.name, tags, c, size, round(gap, 2), act))
        # lift from the highest face index down, so indices stay valid
        for faces, label in sorted(todo_lift, key=lambda t: -max(t[0])):
            _lift(p, faces, label)
        drop_faces(p, todo_drop)
        if not (todo_lift or todo_drop or moved):
            break
    return changed


def unclip(p, base_tags, log=None):
    """Remove a scenario's parts that pass through base-kit parts they may not
    be sunk into, and hanging parts that pass through anything below their top.
    The whole touching group of that builder goes (a watchtower, not a leg)."""
    removed = 0
    for _round in range(3):
        r = analyse(p, [s for _, s in p.floats], exempt=_pin)
        S = r["S"]
        bad = bad_clips(r, base_tags)
        if not bad:
            break
        # grow each bad shell to its touching same-tag group
        group = set(bad)
        frontier = list(bad)
        while frontier:
            i = frontier.pop()
            for j in range(len(S)):
                if j in group or S[j]["tag"] != S[i]["tag"] or not _near(S[i], S[j], TOUCH):
                    continue
                if _touching(S[i], S[j])[0]:
                    group.add(j)
                    frontier.append(j)
        faces = [fi for i in group for fi in S[i]["faces"]]
        if log is not None:
            for i, hit in bad.items():
                log.append((p.name, S[i]["tag"], tuple(round(v, 1) for v in S[i]["min"]), hit, "unclip"))
        drop_faces(p, faces)
        removed += len(group)
    return removed


def bad_clips(r, base_tags):
    """-> {shell index: what it runs into} for every scenario part passing
    through a base-kit part it may not be sunk into (see unclip)."""
    S = r["S"]
    bad = {}
    for ta, tb, where, steep, i, j in r["clips"]:
        for x, y in ((i, j), (j, i)):
            a, b = S[x], S[y]
            if a["tag"] in base_tags or a["tag"] in SOFT:
                continue
            if b["tag"] not in base_tags:
                continue        # two of the scenario's own parts: its call
            if a["tag"] in HANGING or a["tag"] in HANG_FROM:
                if b["tag"] not in HANG_FROM.get(a["tag"], DECKS):
                    bad[x] = b["tag"]
            elif a["tag"] in FREESTANDING:
                if b["tag"] not in DECKS:
                    bad[x] = b["tag"]
            elif b["tag"] not in EMBED_OK:
                bad[x] = b["tag"]
    return bad


def geometry_faults(p, base_tags):
    """What validate() checks on the real mesh: every part attached (or a
    registered float, an islet, a stepping plate), and no scenario part
    through a rail, a wall or a keel."""
    r = analyse(p, [s for _, s in p.floats], exempt=_pin)
    out = ["%s detached at %s" % ("+".join(tags), c) for tags, c, size, _f in r["detached"]]
    for i, hit in bad_clips(r, base_tags).items():
        out.append("%s passes through %s at %s" % (r["S"][i]["tag"], hit,
                                                  tuple(round(v, 1) for v in r["S"][i]["min"])))
    return out
