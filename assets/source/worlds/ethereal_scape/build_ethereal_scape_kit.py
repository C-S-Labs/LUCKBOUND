# LUCKBOUND - Ethereal Scape 41-piece hybrid chunk kit.
#
# Floating isles, temple architecture and lush meadows: docs/biomes/ETHEREAL_SCAPE.md.
#   es_geometry.py  palette (the ORIGINAL scene's values), Piece, primitives
#   es_features.py  cloud floor, cloud banks, mesas, mouths, flora, temple architecture
#   es_pieces.py    the 41 recipes and the kit table
#   es_props.py     the atmosphere: prop library + placement (CHUNK_AUTHORING.md convention 6)
#
# Run (headless; the .blend is an OUTPUT, edit the scripts):
#   blender -b --factory-startup --python assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- --export --render
#
# validate() refuses a piece unless: its box is exactly (2H x 2H) x 256 about the origin; solids are
# closed and outward; no face degenerated; a WALK GRAPH (2-stud heightfield, 1.6-stud steps, 5-stud
# headroom) connects every mouth to every other; every mouth is level ground at z = 0 across its width;
# nothing detached floats in the structure; props are clear of the real mesh; the entry's landing and
# return-portal pad are open to the sky; the Sanctum's hall is clear for the fight.
# Exports then split complete assemblies so every individual mesh stays below 10,000 triangles.
import math
import json
import re
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "_framework"))
for m in ("es_geometry", "es_features", "es_isles", "es_pieces", "es_props", "es_mapgen"):
    sys.modules.pop(m, None)
import es_geometry as G           # noqa: E402
import es_features as F           # noqa: E402
import es_pieces as P             # noqa: E402
import es_props as PR             # noqa: E402
import es_mapgen as MG            # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DO_EXPORT = "--export" in ARGV
DO_RENDER = "--render" in ARGV
ONLY = next((a.split("=", 1)[1].split(",") for a in ARGV if a.startswith("--only=")), None)
SAMPLES = "--samples" in ARGV          # the direction samples (es_samples.py) instead of the kit
if SAMPLES:                            # samples never write kit outputs, and render to their own folder
    ONLY = ["SAMPLES"]
if ONLY and DO_EXPORT:
    raise SystemExit("--only/--samples are review modes; export the complete kit so meshes and content remain in sync")
for m in ("es_samples",):
    sys.modules.pop(m, None)

EXPORT_DIR = os.path.join(REPO, "assets", "export", "worlds", "ethereal_scape")
RENDER_DIR = os.path.join(HERE, "renders", "samples") if "--samples" in ARGV else os.path.join(HERE, "renders")
CHUNKS_LUAU = os.path.join(REPO, "src", "shared", "Content", "Chunks", "EtherealScape.luau")
PROPS_LUAU = os.path.join(REPO, "src", "shared", "Content", "Props", "EtherealScape.luau")
TRI_LIMIT = 10000
GRID = 560.0

# walkable floor a piece must offer (sq studs), by role
MIN_WALK = {"ENTRY": 40000, "BOSS": 60000, "PATH": 9000, "COMBAT": 14000, "MINIBOSS": 16000, "SIDE": 7000, "CAP": 4000,
            "BACKDROP": 0}
# Flat or ground-level things whose contact is never a visible clip. CLOUD IS NOT SOFT any more
# (owner, 2026-09-27): declip() removes cloud through solids, and anything left is reported.
SOFT_TAGS = {"mesa", "crag", "rock", "cloud_floor", "meadow_carpet", "flagstones", "pins", "isle", "landing"}
# Authored joints between two builders -- things built INTO each other on purpose, not clips:
# crystals growing out of a colossus, a stair set against its podium, planks hanging off a broken span.
JOINTS = {frozenset(("crystal_colossus", "crystal_cluster")), frozenset(("es_sanctum", "stairs")),
          frozenset(("plank_bridge", "es_cap_broken_bridge")), frozenset(("es_ruin_stair", "stairs")),
          frozenset(("float_isle", "plank_bridge")), frozenset(("stairs", "sample_temple_city")),
          frozenset(("landing_isle", "plank_bridge")), frozenset(("landing_isle", "guide_stone")),
          frozenset(("float_isle", "aether_fall")), frozenset(("bridge", "es_cap_broken_bridge")),
          frozenset(("bridge", "guide_stone")), frozenset(("bridge", "stairs")),
          frozenset(("shrine_hall", "column")), frozenset(("es_rooted_hollow", "great_tree")),
          frozenset(("es_sky_observatory", "stairs")), frozenset(("es_sky_aqueduct", "_arc")),
          frozenset(("es_sky_aqueduct", "aether_fall"))}


# ---------------------------------------------------------------------------
# Scene objects
# ---------------------------------------------------------------------------
def materials():
    mats = {}
    for name, rgb in G.PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        col = tuple((c / 255) ** 2.2 for c in rgb) + (1.0,)
        b.inputs["Base Color"].default_value = col
        b.inputs["Roughness"].default_value = 0.6
        if name in G.EMISSIVE:
            b.inputs["Emission Color"].default_value = col
            b.inputs["Emission Strength"].default_value = G.EMISSIVE[name]
        m.diffuse_color = col             # Workbench review renders read this
        mats[name] = m
    return mats


def to_object(name, verts, faces, fmat, up, mats, coll, recalculate=True):
    me = bpy.data.meshes.get(name)
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in G.MAT_ORDER:
        me.materials.append(mats[m])
    me.validate(verbose=False)
    dropped = len(faces) - len(me.polygons)
    for poly, mname in zip(me.polygons, fmat):
        poly.material_index = G.MAT_ORDER.index(mname)
        poly.use_smooth = mname == "CloudWhite"          # clouds are soft; everything else keeps its facets
    bm = bmesh.new()
    bm.from_mesh(me)
    if recalculate:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    if not dropped:
        for i in up:
            f = bm.faces[i]
            f.normal_update()
            if f.normal.z < 0:
                f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in me.polygons:
        rgb = G.PALETTE[G.MAT_ORDER[poly.material_index]]
        c = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
        for li in poly.loop_indices:
            col.data[li].color_srgb = c
    me.color_attributes.active_color = col
    me.update()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj, dropped


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def mesh_bvh(obj):
    me = obj.data
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(pl.vertices) for pl in me.polygons])


def column_tops(bvh, x, y, z_start=172.0):
    """Every walkable surface in one column: up-facing, with >= 5 studs of headroom."""
    tops, above, z = [], 1e9, z_start
    for _ in range(10):
        hit = bvh.ray_cast(Vector((x, y, z)), Vector((0, 0, -1)), 400)
        if hit[0] is None:
            break
        loc, nrm = hit[0], hit[1]
        if abs(nrm.z) > 0.7 and nrm.z > 0 and above - loc.z >= 5.0 and loc.z > G.KEEL_BOTTOM + 4:
            tops.append(loc.z)
        above = loc.z
        z = loc.z - 0.05
    return tops


def walk_graph(p, bvh, step=2.0):
    H = p.H
    n = int(2 * H / step)
    cells = {}
    for i in range(n):
        x = -H + (i + 0.5) * step
        for j in range(n):
            y = -H + (j + 0.5) * step
            t = column_tops(bvh, x, y)
            if t:
                cells[(i, j)] = t

    def cell(x, y):
        return int((x + H) / step), int((y + H) / step)

    mouths = {}
    for card, kind in p.sockets:
        w = G.KIND_WIDTH[kind]
        dx, dy = G.DIRS[card]
        sz = p.lift.get(card, 0.0)                  # the socket's own height (its OffsetY)
        seeds, total = [], 0
        k = -w / 2 + 3
        while k <= w / 2 - 3:
            total += 1
            x, y = dx * (H - 1.5) + (-dy) * k, dy * (H - 1.5) + dx * k
            c = cell(x, y)
            zs = [z for z in cells.get(c, []) if abs(z - sz) < 0.5]
            if zs:
                seeds.append((c, zs[0]))
            k += step
        mouths[card] = (seeds, total)
    start = next((s for s, t in mouths.values() if s), None)
    reached = set()
    if start:
        frontier = [(c, z) for c, z in start]
        for c, z in frontier:
            reached.add((c, round(z, 2)))
        while frontier:
            (i, j), z = frontier.pop()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc = (i + di, j + dj)
                for z2 in cells.get(nc, []):
                    key = (nc, round(z2, 2))
                    if key not in reached and abs(z2 - z) <= 1.6:
                        reached.add(key)
                        frontier.append((nc, z2))
    reached_cells = {c for c, _ in reached}
    result = {}
    for card, (seeds, total) in mouths.items():
        result[card] = (len(seeds) / max(1, total), any(c in reached_cells for c, _ in seeds))
    return result, len(reached) * step * step


def detached(p):
    """Structure parts touching nothing (Sky Citadel's real-mesh check, reused)."""
    try:
        import geometry_checks as GC
    except ImportError:
        return [], []
    GC.PRIMITIVES.update(G.PRIMITIVES)
    r = GC.analyse(p, [], exempt=lambda s: max(s["max"][k] - s["min"][k] for k in range(3)) < 1.0 and s["min"][2] < -95)
    out = [("+".join(tags), c, size) for tags, c, size, _f in r["detached"]]
    clips = [(a, b, where, n) for a, b, where, n, _i, _j in r["clips"]
             if a not in SOFT_TAGS and b not in SOFT_TAGS and frozenset((a, b)) not in JOINTS
             and not ({a, b} & F.CLOUD_TAGS and {a, b} & F.CLOUD_MAY_TOUCH)
             and not {a, b} <= (F.CLOUD_TAGS - {"cloud_tufts"})]      # billows heaped on billows ARE the bank
    return out, clips


def surface_errors(p, obj):
    """Every solid connected surface must be closed and outward-facing.

    Only explicitly marked floor inlays may be single-sided. Check each
    component separately: an island's valid cap cannot hide an open rock band.
    """
    from collections import Counter
    parents = list(range(len(obj.data.vertices)))
    def root(v):
        while parents[v] != v:
            parents[v] = parents[parents[v]]
            v = parents[v]
        return v
    for face in obj.data.polygons:
        first = root(face.vertices[0])
        for v in face.vertices[1:]:
            parents[root(v)] = first
    components = {}
    for face in obj.data.polygons:
        components.setdefault(root(face.vertices[0]), []).append(face.index)
    obj.data.calc_loop_triangles()
    volumes, degenerate = Counter(), Counter()
    for tri in obj.data.loop_triangles:
        a, b, c = [obj.data.vertices[v].co for v in tri.vertices]
        key = root(tri.vertices[0])
        volumes[key] += a.dot(b.cross(c)) / 6
        if (b-a).cross(c-a).length < 1e-7:
            degenerate[key] += 1
    errors = []
    for key, indices in components.items():
        if all(i in p.up for i in indices):
            continue
        edges = Counter()
        for i in indices:
            vs = list(obj.data.polygons[i].vertices)
            for a, b in zip(vs, vs[1:]+vs[:1]):
                edges[tuple(sorted((a, b)))] += 1
        tag = p.ftag[indices[0]]
        bad = sum(count != 2 for count in edges.values())
        if bad:
            errors.append(f"open/nonmanifold {tag}: {bad} edge(s)")
        elif volumes[key] <= 0:
            errors.append(f"inward/flat solid {tag}: volume {volumes[key]:.6f}")
        if degenerate[key]:
            errors.append(f"collapsed surface {tag}: {degenerate[key]} triangle(s)")
    return errors


def validate(p, obj, dropped, spec):
    fails, notes = [], []
    fails.extend(surface_errors(p, obj))
    H = p.H
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    for label, lo, hi, want_lo, want_hi in (("X", min(xs), max(xs), -H, H), ("Y", min(ys), max(ys), -H, H),
                                            ("Z", min(zs), max(zs), G.KEEL_BOTTOM, G.CROWN_TOP)):
        if abs(lo - want_lo) > 0.05 or abs(hi - want_hi) > 0.05:
            fails.append(f"box {label} {lo:.2f}..{hi:.2f}, want {want_lo}..{want_hi}")
    if dropped:
        fails.append(f"{dropped} degenerate face(s)")
    bvh = mesh_bvh(obj)
    # Cosmetic foliage must not be treated as a movement obstacle.
    solid_indices = [i for i in range(len(p.faces)) if p.fexport[i] != "foliage"]
    solid = BVHTree.FromPolygons(p.verts, [p.faces[i] for i in solid_indices])
    for a, b, floor_z, radius, label in p.clearances:
        length = math.dist(a, b)
        for k in range(math.ceil(length) + 1):
            u = k / max(1, math.ceil(length))
            z = floor_z[0] + (floor_z[1]-floor_z[0])*u if isinstance(floor_z, tuple) else floor_z
            point = Vector((a[0]+(b[0]-a[0])*u, a[1]+(b[1]-a[1])*u, z+3))
            hit = solid.find_nearest(point, min(radius, 2.4))
            if hit[0] is not None:
                fails.append(f"blocked {label} by {p.ftag[solid_indices[hit[2]]]} at ({point.x:.1f}, {point.y:.1f}, {point.z:.1f}); surface {tuple(round(v, 1) for v in hit[0])}")
                break
    if spec["role"] == "BACKDROP":               # scenery: never walked, nothing to connect
        return fails, notes, 0.0, bvh
    mouths, area = walk_graph(p, bvh)
    for card, (cover, reached) in mouths.items():
        if cover < 0.95:
            fails.append(f"mouth {card} only {cover:.0%} level ground across its width")
        if not reached:
            fails.append(f"mouth {card} not connected to the others (walk graph)")
    if area < MIN_WALK[spec["role"]]:
        fails.append(f"walkable area {area:.0f} < {MIN_WALK[spec['role']]}")
    if spec["id"] == "ES_ENTRY":
        for x, y in [(0, 0)] + [(math.cos(a) * 24, -110 + math.sin(a) * 24) for a in [k * 0.785 for k in range(8)]] + [(0, -110)]:
            hit = bvh.ray_cast(Vector((x, y, 172)), Vector((0, 0, -1)), 400)
            if hit[0] is None or hit[0].z > 1.0:
                fails.append(f"entry sky column not clear at ({x:.0f},{y:.0f})")
    if spec["id"] == "ES_SANCTUM":
        blocked = 0
        for x in range(-108, 109, 12):
            for y in range(-84, 118, 12):
                for z in (10, 24, 40, 56):
                    if bvh.find_nearest(Vector((x, y, z)), 1.5)[0] is not None:
                        blocked += 1
        for x in range(-28, 29, 8):                  # the great door
            for z in (8, 20, 40):
                if bvh.find_nearest(Vector((x, -96, z)), 1.0)[0] is not None:
                    blocked += 1
        if blocked:
            fails.append(f"sanctum hall/door obstructed at {blocked} sample(s)")
    # GROUNDED (owner 2026-09-27: "all decorative pillars and columns are connected to the ground, not
    # floating"). Every column, tower, waystone, statue, beacon and lantern post registers its footing;
    # terrain-only rays cast down from above its base, at the centre and round its rim, must meet ground within
    # 10 studs (a podium can be thick). Owner 2026-09-27 ("the spires are hanging off the edge of the chunk
    # still"): EVERY rim point, at the footing's FULL radius, must land -- 4 of 5 at 0.7r let a beacon's
    # base hang half off an isle. A crag's own base ring sits 2 studs under the floor, so its rays start
    # below that, inside the isle it stands on.
    for fx, fy, fz, fr, what in p.footings:
        # +3 studs for a big base: the isle's gold rim band juts past its floor, so a ray at the bare radius
        # could land on the band while the base itself overhangs the edge (a lantern post's is too small to)
        m = 3.0 if fr >= 4 else 0.0
        pts = [(fx, fy)] + [(fx + math.cos(a) * (fr + m), fy + math.sin(a) * (fr + m))
                            for a in [0.3 + k * math.pi / 4 for k in range(8)]]
        # Cast onto terrain only, from ABOVE its surface. Starting inside the
        # old island's hidden grass slab accepted buried geometry and breaks
        # completely when the island becomes a proper closed shell.
        ground_faces = [face for i, face in enumerate(p.faces)
                        if p.ftag[i] in {"isle", "landing", "mesa", "cloud_floor", "stairs"}
                        or (p.ftag[i].startswith("es_") and max(p.verts[v].z for v in face) <= fz + 0.1)]
        ground_bvh = BVHTree.FromPolygons(p.verts, ground_faces)
        hits = sum(ground_bvh.ray_cast(Vector((qx, qy, fz + 0.25)), Vector((0, 0, -1)), 10.25)[0] is not None for qx, qy in pts)
        if hits < len(pts):
            fails.append(f"overhanging {what} at ({fx:.0f}, {fy:.0f}, {fz:.0f}): ground under {hits}/{len(pts)} of its base")
    det, clips = detached(p)
    for tags, c, size in det:
        fails.append(f"detached {tags} at {c} size {size}")
    for a, b, where, n in clips:
        notes.append(f"clip {a} x {b} at {where} ({n})")
    return fails, notes, area, bvh


# ---------------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------------
def _num(v):
    r = round(v, 3)
    return "0" if r == 0 else ("%g" % r)


GAME_SOCKET = {"N": (0, -1, 0), "S": (0, 1, 180), "E": (1, 0, 90), "W": (-1, 0, 270)}


def write_chunks_luau(specs, asset_parts):
    out = ["--!strict",
           "-- GENERATED by assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- do not edit by hand.",
           "-- Ethereal Scape's 41-piece hybrid kit: floating isles, gold rims, lush meadows and classical temples.",
           "-- Large assemblies use MeshParts: the 10k triangle ceiling is per exported mesh. docs/biomes/ETHEREAL_SCAPE.md.",
           "--",
           "-- CONNECTION VOCABULARY (disjoint from every other world's -- a test asserts it):",
           "--   SPAN       connective, a 44-stud golden landing at z = 0.",
           "--   COMMUNION  arena-only, 64 studs; only the two Temple Gates offer one, so a gate precedes the Sanctum.",
           "-- Sockets: Facing degrees, 0 = -Z (north), 90 = +X, 180 = +Z, 270 = -X; offsets local to the piece.",
           "-- Every box is (2H x 2H) x 256: keel -96, crown +160, walk plane 32 below the box centre.",
           "-- The Entry is 384 square and the Sanctum 512 square; their mouths are the same size as everyone's.",
           "-- HYBRID (owner pick 2026-09-27): floating isles + temple architecture + meadow dressing. A socket's",
           "-- OffsetY is its height: rises and descents carry the map up and down. MINIBOSS arenas end side",
           "-- branches and are NOT the boss arena; BACKDROP pieces have no sockets and ring the map (spec §7.7).",
           "local WIDTH = { SPAN = 44, COMMUNION = 64 }",
           "",
           "local function socket(id: string, kind: string, x: number, z: number, facing: number, y: number?)",
           "\treturn {",
           "\t\tId = id,",
           "\t\tKind = kind,",
           "\t\tOffsetX = x,",
           "\t\tOffsetY = y or 0, -- a rise or a descent carries the map up or down",
           "\t\tOffsetZ = z,",
           "\t\tFacing = facing,",
           "\t\tWidth = WIDTH[kind],",
           "\t}",
           "end",
           "",
           "local CHUNKS = {"]
    names = {"N": "north", "S": "south", "E": "east", "W": "west"}
    for s in specs:
        H = s["half"]
        socks = []
        for card, kind in s["sockets"]:
            gx, gz, facing = GAME_SOCKET[card]
            lift = s.get("lift", {}).get(card, 0)
            socks.append('socket("%s", "%s", %d, %d, %d%s)' % (names[card], kind, gx * H, gz * H, facing,
                                                             ", %d" % lift if lift else ""))
        out.append("\t{")
        out.append('\t\tId = "%s",' % s["id"])
        out.append('\t\tRole = "%s" :: any,' % s["role"])
        out.append('\t\tAssetKey = "ES_CHUNK_%s",' % s["id"][3:])
        if s["id"] in asset_parts:
            out.append("\t\tMeshParts = {")
            for part in asset_parts[s["id"]]:
                fields = ['AssetKey = "%s"' % part["AssetKey"]]
                fields += [f"{k} = {_num(part[k])}" for k in ("SizeX", "SizeY", "SizeZ", "OffsetX", "OffsetY", "OffsetZ")]
                if part.get("CanCollide") is False:
                    fields.append("CanCollide = false")
                out.append("\t\t\t{ " + ", ".join(fields) + " },")
            out.append("\t\t},")
        out.append("\t\t-- %s" % s["desc"])
        if socks:
            out.append("\t\tSockets = {")
            for sk in socks:
                out.append("\t\t\t%s," % sk)
            out.append("\t\t},")
        else:
            out.append("\t\tSockets = {}, -- BACKDROP: surround scenery, ringed round the map by the §7.7 generator")
        if s.get("supports"):
            out.append("\t\tSupports = { %s }," % ", ".join("%s = true" % k for k in s["supports"]))
        out.append("\t\tWeight = %d," % s["weight"])
        if s.get("max"):
            out.append("\t\tMaxPerLayout = %d," % s["max"])
        out.append("\t\tEnemyTags = { %s }," % ", ".join('"%s"' % e for e in s["enemies"]) if s["enemies"] else "\t\tEnemyTags = {},")
        out.append("\t\tTags = { %s }," % ", ".join('"%s"' % t for t in s["tags"]))
        out.append("\t\tSize = %d," % (2 * H))
        out.append("\t},")
    out += ["}",
            "",
            "local out = {}",
            "for _, chunk in CHUNKS do",
            "\tlocal c = table.clone(chunk) :: any",
            '\tc.WorldId = "ETHEREAL_SCAPE"',
            "\tc.SizeX = c.Size",
            "\tc.SizeY = 256",
            "\tc.SizeZ = c.Size",
            "\tc.Size = nil",
            "\t-- keel -96, crown +160: the walk plane sits 96 up from the bottom of the box.",
            "\tc.GroundOffsetY = 96",
            "\t-- Authored +Y = north with the -Z-forward FBX export, exactly as Sky Citadel, which measured 180 in",
            "\t-- Studio. ChunkLoader.calibrateYaw still measures each mesh at load; this is the tie-break hint.",
            "\tc.MeshYawOffset = 180",
            "\ttable.insert(out, c)",
            "end",
            "return out",
            ""]
    with open(CHUNKS_LUAU, "w", newline="\n") as fh:
        fh.write("\n".join(out))


def write_props_luau(pieces):
    out = ["--!strict",
           "-- GENERATED by assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- do not edit by hand.",
           "-- CHUNK_AUTHORING.md convention 6: Ethereal Scape's ATMOSPHERE -- drifting cloud puffs, sky lanterns,",
           "-- hovering crystal shards, satellite islets, petals, lotuses, kites, and skyrays gliding over the whole map. Positions and rotations",
           "-- are in the piece's layout frame (origin on the walk plane, -Z north); Size is the copy's own size.",
           "",
           "return {",
           '\tId = "ETHEREAL_SCAPE",',
           "\tLibrary = {"]
    for k in PR.KINDS:
        out.append('\t\t"%s",' % k)
    out.append("\t},")
    out.append("\tPlacements = {")
    for p in pieces:
        if not p.props:
            continue
        out.append("\t\t%s = {" % p.name)
        for prop in p.props:
            r = PR.game_row(prop)
            out.append('\t\t\t{ Prop = "%s", Anim = "%s", Tier = %d, P = { %s }, R = { %s }, S = { %s } },' % (
                r["prop"], r["anim"], r["tier"], ", ".join(_num(v) for v in r["pos"]),
                ", ".join(_num(v) for v in r["rot"]), ", ".join(_num(v) for v in r["size"])))
        out.append("\t\t},")
    out += ["\t},", "}", ""]
    with open(PROPS_LUAU, "w", newline="\n") as fh:
        fh.write("\n".join(out))


def split_piece(p, mats, coll, source=None):
    """Partition semantic groups into whole primitive shells, preserving exact authored coordinates."""
    groups = {}
    # Reuse the validated source's oriented triangles. Even an oversized individual
    # primitive can then be split without changing surfaces or recomputing seam normals.
    if source is None:
        source, dropped = to_object("SPLIT_SOURCE_" + p.name, p.verts, p.faces, p.fmat, p.up, mats, coll)
        assert not dropped
    source.data.calc_loop_triangles()
    triangles = list(source.data.loop_triangles)
    faces = [list(t.vertices) for t in triangles]
    materials = [p.fmat[t.polygon_index] for t in triangles]
    up = {i for i, t in enumerate(triangles) if t.polygon_index in p.up}
    for i, tri in enumerate(triangles):
        groups.setdefault(p.fexport[tri.polygon_index], {}).setdefault(p.fshell[tri.polygon_index], []).append(i)
    batches = []
    for group, shells in groups.items():
        indices, tris = [], 0
        for shell_faces in shells.values():
            for start in range(0, len(shell_faces), TRI_LIMIT - 1):
                subset = shell_faces[start:start + TRI_LIMIT - 1]
                if tris + len(subset) >= TRI_LIMIT and indices:
                    batches.append((group, indices))
                    indices, tris = [], 0
                indices.extend(subset)
                tris += len(subset)
        if indices:
            batches.append((group, indices))
    objects, parts = [], []
    counts = {}
    all_indices = []
    for index, (group, indices) in enumerate(batches):
        counts[group] = counts.get(group, 0) + 1
        name = p.name if index == 0 else f"{p.name}_{group.upper()}_{counts[group]:02d}"
        used = sorted({v for i in indices for v in faces[i]})
        remap = {old: new for new, old in enumerate(used)}
        obj, dropped = to_object(name, [p.verts[v] for v in used],
                                 [[remap[v] for v in faces[i]] for i in indices],
                                 [materials[i] for i in indices], {j for j, i in enumerate(indices) if i in up}, mats, coll,
                                 recalculate=False)
        assert not dropped, f"{name}: degenerate split faces"
        obj.data.calc_loop_triangles()
        assert len(obj.data.loop_triangles) < TRI_LIMIT, name
        lo = [min(v.co[a] for v in obj.data.vertices) for a in range(3)]
        hi = [max(v.co[a] for v in obj.data.vertices) for a in range(3)]
        centre = [(a + b) / 2 for a, b in zip(lo, hi)]
        # Studio's uploaded mesh axes map Blender (X,Y,Z) to (-X,Z,Y).
        # MeshYawOffset=180 restores authored orientation for the entire assembly.
        # Offsets must use the SAME imported axes as the individual mesh geometry.
        parts.append(dict(AssetKey="ES_CHUNK_" + name[3:],
                          SizeX=hi[0]-lo[0], SizeY=hi[2]-lo[2], SizeZ=hi[1]-lo[1],
                          OffsetX=-centre[0], OffsetY=centre[2]-(G.KEEL_BOTTOM+G.CROWN_TOP)/2,
                          OffsetZ=centre[1], Triangles=len(obj.data.loop_triangles), Object=name))
        if group == "foliage":
            parts[-1]["CanCollide"] = False
        objects.append(obj)
        all_indices.extend(indices)
    assert sorted(all_indices) == list(range(len(faces))), f"{p.name}: missing or duplicated faces"
    return objects, parts


def export(objs, prop_objs):
    os.makedirs(EXPORT_DIR, exist_ok=True)

    def fbx(objects, name):
        saved = [(o, o.location.copy()) for o in objects]
        for o in objects:
            o.location = (0, 0, 0)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.export_scene.fbx(filepath=os.path.join(EXPORT_DIR, name), use_selection=True, apply_unit_scale=True,
                                 apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                                 object_types={"MESH"}, use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False,
                                 bake_space_transform=True)
        for o, loc in saved:
            o.location = loc

    fbx(objs, "ethereal_scape_structure.fbx")
    fbx(prop_objs, "ethereal_scape_props.fbx")


# ---------------------------------------------------------------------------
# Review renders (Workbench: flat material colour, shadows and cavity -- reads like the game)
# ---------------------------------------------------------------------------
def render_setup():
    s = bpy.context.scene
    s.render.engine = "BLENDER_WORKBENCH"
    sh = s.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.studiolight_rotate_z = math.radians(25)
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    sh.show_cavity = True
    sh.show_backface_culling = True
    sh.cavity_type = "BOTH"
    sh.background_type = "WORLD"
    s.world.color = (0.66, 0.78, 0.92)
    sh.background_color = (0.66, 0.78, 0.92)
    s.display.light_direction = (0.45, -0.35, 0.82)
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 85
    cd = bpy.data.cameras.new("Review")
    cd.clip_end = 30000
    cam = bpy.data.objects.new("Review", cd)
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def shot(s, cam, path, target, offset, lens=28, res=(1280, 800)):
    s.render.resolution_x, s.render.resolution_y = res
    cam.data.lens = lens
    t = Vector(target)
    cam.location = t + Vector(offset)
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


def review_visibility(scene, visible):
    """Keep catalogue, assembled-map and individual-piece review geometry separate."""
    visible = set(visible)
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in visible


def place_prop_copies(pieces, prop_objs, coll):
    """Review only: linked copies of the prop library where the placements say (never exported)."""
    lib = {o.name: o for o in prop_objs}
    copies = {}
    for p, obj in pieces:
        copies[p.name] = []
        for prop in p.props:
            src = lib[prop["kind"]]
            o = bpy.data.objects.new("REVIEW_" + prop["kind"], src.data)
            o.location = obj.location + prop["pos"]
            o.rotation_euler = (0, 0, prop["yaw"])
            o.scale = (prop["scale"],) * 3
            coll.objects.link(o)
            copies[p.name].append(o)
    return copies


def chain_preview(objs_by_id, coll):
    """The CHUNK_AUTHORING 'place a copy beside itself' check, as a real route: entry -> walk ->
    convergence -> gate -> sanctum, joined mouth to mouth."""
    route = ["ES_ENTRY", "ES_PATH_GROVE_ISLE", "ES_CONVERGENCE", "ES_TEMPLE_GATE_A", "ES_SANCTUM"]
    y = 0.0
    origin = Vector((0, -6000, 0))
    placed = []
    prev_half = None
    for pid in route:
        src, half = objs_by_id[pid]
        if prev_half is not None:
            y += prev_half + half
        o = bpy.data.objects.new("CHAIN_" + pid, src.data)
        o.location = origin + Vector((0, y, 0))
        coll.objects.link(o)
        placed.append(o)
        prev_half = half
    return origin, y


def map_preview(specs, objs_by_id, pieces_by_id=None, prop_objs=()):
    """A whole assembled map (the §7.7 scheme, es_mapgen.py mirroring ChunkCore) as linked copies in its own
    collection, so the owner can open the .blend and walk a real layout: branches, a miniboss arena, caps,
    rises and descents, and the backdrop ring."""
    gen = dict(BranchLength=2, Minibosses=1, MaxSides=2, Backdrop=18)
    layout, best, seed = None, -1, None
    for sd in range(1, 120):                    # the seed that shows the scheme off best: most branching
        lay = MG.assemble(specs, 5, gen, sd)
        if not lay:
            continue
        score = sum(pl["role"] in ("CAP", "SIDE", "MINIBOSS") for pl in lay) * 2 +             sum(len(SPEC_BY_ID[pl["id"]]["sockets"]) >= 3 for pl in lay) * 3 +             sum(bool(SPEC_BY_ID[pl["id"]].get("lift")) for pl in lay)
        if score > best:
            layout, best, seed = lay, score, sd
    if not layout:
        print("MAP PREVIEW: no seed assembled")
        return None
    coll = bpy.data.collections.new("MAP_PREVIEW")
    bpy.context.scene.collection.children.link(coll)
    origin = Vector((0, 9000, 0))
    counts = {}
    if any(pl["id"] not in objs_by_id for pl in layout):
        print("MAP PREVIEW: a piece failed to build; skipped")
        return None
    for pl in layout:
        src = objs_by_id[pl["id"]]
        o = bpy.data.objects.new("MAP_" + pl["id"], src.data)
        o.location = origin + Vector((pl["x"], -pl["z"], pl["y"]))
        o.rotation_euler = (0, 0, -math.radians(pl["yaw"]))
        coll.objects.link(o)
        lib = {q.name: q for q in prop_objs}
        pc = pieces_by_id.get(pl["id"]) if pieces_by_id else None
        rot = Matrix.Rotation(-math.radians(pl["yaw"]), 3, "Z")
        for prop in (pc.props if pc else []):          # the piece's drifting clouds, lanterns, isles
            c = bpy.data.objects.new("MAPPROP_" + prop["kind"], lib[prop["kind"]].data)
            c.location = o.location + rot @ prop["pos"]
            c.rotation_euler = (0, 0, prop["yaw"] - math.radians(pl["yaw"]))
            c.scale = (prop["scale"],) * 3
            coll.objects.link(c)
        counts[pl["role"]] = counts.get(pl["role"], 0) + 1
    print(f"MAP PREVIEW seed {seed}: {len(layout)} pieces " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    xs = [pl["x"] for pl in layout]
    zs = [pl["z"] for pl in layout]
    return origin + Vector(((min(xs) + max(xs)) / 2, -(min(zs) + max(zs)) / 2, 0)), max(max(xs) - min(xs), max(zs) - min(zs))


# ---------------------------------------------------------------------------
def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    mats = materials()
    coll = bpy.context.scene.collection
    specs = [s for s in P.PIECES if not ONLY or s["id"] in ONLY]
    if SAMPLES:
        import es_samples
        specs = [dict(id=s["id"], role="COMBAT", half=128, sockets=[("S", "SPAN"), ("N", "SPAN")], fn=s["fn"],
                      tags=["shrine"], enemies=[]) for s in es_samples.SAMPLES]
    global SPEC_BY_ID
    SPEC_BY_ID = {s["id"]: s for s in specs}
    pieces, objs, rows = [], [], []
    for idx, spec in enumerate(specs):
        p = G.Piece(spec["id"], spec["half"], spec["sockets"])
        p.lift = dict(spec.get("lift", {}))
        try:
            spec["fn"](p)
        except Exception as e:                  # noqa: BLE001            # a layout mistake in a recipe: report it with the rest
            rows.append((spec, p, [f"layout: {e}"], [], 0.0))
            continue
        # last: low billows on whatever open cloud floor is left (never on a path or a feature)
        if "cloud_floor" in p.ftag:            # only where there IS a cloud floor to lie on
            F.cloud_tufts(p, 16 if p.H > 150 else 12, (0, 0, p.H * 0.85))
        p.declipped = F.declip(p)
        obj, dropped = to_object(spec["id"], p.verts, p.faces, p.fmat, p.up, mats, coll)
        fails, notes, area, bvh = validate(p, obj, dropped, spec)
        PR.place_all(p, bvh, spec)
        col, row = idx % 6, idx // 6
        obj.location = (col * GRID, row * GRID, 0)
        pieces.append((p, obj))
        objs.append(obj)
        rows.append((spec, p, fails, notes, area))
    prop_objs = []
    for i, (kind, (verts, faces, fmat, size)) in enumerate(PR.library().items()):
        o, _d = to_object(kind, verts, faces, fmat, set(), mats, coll)
        o.location = (i * 60.0, -900.0, 0)
        prop_objs.append(o)

    print("\n=== ETHEREAL SCAPE KIT (revamp) ===")
    n_fail = 0
    for spec, p, fails, notes, area in rows:
        status = "PASS" if not fails else "FAIL"
        n_fail += bool(fails)
        print(f"PIECE {spec['id']:26s} {spec['role']:7s} {p.tri_count():5d} tris  walk {area:7.0f}  props {len(p.props):2d}  "
              f"declipped {getattr(p, 'declipped', 0):3d}  {status}")
        for f in fails:
            print(f"      FAIL {f}")
        for nt in notes[:12]:
            print(f"      note {nt}")
    print(f"=== {len(rows) - n_fail}/{len(rows)} PASS ===")

    preview = None
    # Never publish failed geometry or generated content, even for a render-only build.
    if n_fail:
        return n_fail
    export_coll = bpy.data.collections.new("EXPORT_PARTS")
    coll.children.link(export_coll)
    export_coll.hide_render = True
    export_objs, asset_parts = [], {}
    for p, obj in pieces:
        if p.tri_count() >= TRI_LIMIT or len(set(p.fexport)) > 1:
            # Avoid name suffixes: the review mesh is never exported.
            obj.name = "REVIEW_" + p.name
            obj.data.name = "REVIEW_" + p.name
            split, metadata = split_piece(p, mats, export_coll, source=obj)
            for part in split:
                part.location = obj.location
            export_objs.extend(split)
            asset_parts[p.name] = metadata
            print(f"EXPORT {p.name}: " + ", ".join(f"{q['Object']} {q['Triangles']} tris" for q in metadata))
        else:
            export_objs.append(obj)
    for obj in [*export_objs, *prop_objs]:
        obj.data.calc_loop_triangles()
        if len(obj.data.loop_triangles) >= TRI_LIMIT:
            raise ValueError(f"{obj.name}: exported mesh exceeds per-mesh triangle limit")
    if not ONLY:
        preview = map_preview(specs, {spec["id"]: obj for spec, (p, obj) in ((SPEC_BY_ID[p_.name], (p_, o_)) for p_, o_ in pieces)},
                              {p_.name: p_ for p_, _o in pieces}, prop_objs)
        write_chunks_luau(specs, asset_parts)
        write_props_luau([p for p, _o in pieces])
        # Register new mesh keys once; never erase uploaded IDs on rebuild.
        manifest_path = os.path.join(REPO, "src", "shared", "Content", "AssetManifest.luau")
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = fh.read()
        for metadata in asset_parts.values():
            for part in metadata:
                key = part["AssetKey"]
                if re.search(r"\b" + re.escape(key) + r"\s*=\s*\{", manifest):
                    continue
                entry = ('\t%s = {\n\t\tAssetId = "",\n\t\tStatus = "PLACEHOLDER",\n'
                         '\t\tSource = "assets/export/worlds/ethereal_scape/ethereal_scape_structure.fbx",\n'
                         '\t\tNotes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",\n\t},\n') % key
                marker = "}\n\nAssetManifest.ENTRIES = ENTRIES"
                assert marker in manifest
                manifest = manifest.replace(marker, entry + marker, 1)
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(manifest)
        print("WROTE", CHUNKS_LUAU)
        print("WROTE", PROPS_LUAU)
    if DO_EXPORT:
        export(export_objs, prop_objs)
        with open(os.path.join(EXPORT_DIR, "ethereal_scape_structure.json"), "w", encoding="utf-8") as fh:
            json.dump(asset_parts, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("EXPORTED structure + props FBX to", EXPORT_DIR)
    blend = os.path.join(HERE, "ethereal_scape_kit.blend")
    if DO_RENDER:
        os.makedirs(RENDER_DIR, exist_ok=True)
        # A focused review must not erase the other pieces' existing renders.
        copies = place_prop_copies(pieces, prop_objs, coll)
        s, cam = render_setup()
        for spec, (p, obj) in ((SPEC_BY_ID[p_.name], (p_, o_)) for p_, o_ in pieces):
            review_visibility(s, [obj, *copies[p.name]])
            H = p.H
            c = obj.location
            k = H / 128
            shot(s, cam, os.path.join(RENDER_DIR, f"{spec['id'].lower()}.jpg"), c + Vector((0, 0, 30 * k)),
                 (230 * k, -300 * k, 210 * k), lens=26)
            if not p.sockets:                    # a backdrop: no ground shot
                continue
            card = p.sockets[0][0]
            dx, dy = G.DIRS[card]
            eye = c + Vector((dx * (H - 20), dy * (H - 20), 6 + p.lift.get(card, 0.0)))
            shot(s, cam, os.path.join(RENDER_DIR, f"{spec['id'].lower()}_ground.jpg"), c + Vector((0, 0, 14)),
                 tuple(eye - (c + Vector((0, 0, 14)))), lens=22)
            if spec["id"] == "ES_SANCTUM":           # the hall the boss lives in, from just inside the door
                tgt = c + Vector((0, 90, 30))
                shot(s, cam, os.path.join(RENDER_DIR, "es_sanctum_interior.jpg"), tgt,
                     tuple((c + Vector((0, -86, 14))) - tgt), lens=18)
        if not ONLY:
            byid = {spec["id"]: (obj, spec["half"]) for spec, (p, obj) in ((SPEC_BY_ID[p_.name], (p_, o_)) for p_, o_ in pieces)}
            origin, length = chain_preview(byid, coll)
            review_visibility(s, [o for o in s.objects if o.name.startswith("CHAIN_")])
            mid = origin + Vector((0, length / 2, 0))
            shot(s, cam, os.path.join(RENDER_DIR, "preview_chain.jpg"), mid, (900, -700, 900), lens=24, res=(1600, 900))
            grid_c = Vector((2.5 * GRID, 2 * GRID, 0))
            review_visibility(s, [*objs, *(o for group in copies.values() for o in group)])
            shot(s, cam, os.path.join(RENDER_DIR, "kit_overview.jpg"), grid_c, (0, -2600, 2600), lens=30, res=(1600, 1100))
            if preview:
                review_visibility(s, [o for o in s.objects if o.name.startswith(("MAP_", "MAPPROP_"))])
                c, span = preview
                shot(s, cam, os.path.join(RENDER_DIR, "map_preview.jpg"), c, (span * 0.35, -span * 0.75, span * 0.7), lens=28,
                     res=(1920, 1080))
                shot(s, cam, os.path.join(RENDER_DIR, "map_preview_top.jpg"), c, (0, -1, span * 1.25), lens=30, res=(1600, 1600))
        review_visibility(s, [*objs, *prop_objs, *(o for group in copies.values() for o in group),
                              *(o for o in s.objects if o.name.startswith(("MAP_", "MAPPROP_", "CHAIN_")))])
        print("RENDERED to", RENDER_DIR)
    if not ONLY:
        export_coll.hide_viewport = True
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        print("SAVED", blend)
    return n_fail


if __name__ == "__main__":
    fails = main()
    if fails:
        raise SystemExit(f"{fails} piece(s) failed validation")
