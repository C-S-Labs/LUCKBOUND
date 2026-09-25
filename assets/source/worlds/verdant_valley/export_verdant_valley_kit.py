"""Verdant Valley base kit (30 pieces) -> one FBX + chunk-loader content.

Run headless (never in the live session -- see WORKLOG 2026-09-22):

    blender -b --factory-startup <kit.blend> --python export_verdant_valley_kit.py -- \
        [--out DIR] [--ids ids.json]

<kit.blend> is the delivered art, kept here as verdant_valley_30_base_kit.blend
(delivered as verdant_valley_30_5x6_arch_vine_normals_review.blend, 2026-09-24):
30 collections named "NN Name", each holding loose meshes parented to a
"NN Name_REVIEW_OFFSET" empty on a 400-stud review grid.

What this does, per piece:
  1. evaluates every mesh (modifiers applied), moves it into the piece's own frame
     (review offset removed -> origin at the centre of the footprint, on the ground),
     bakes each material's colour into a "Col" vertex colour and joins it all into
     ONE object named for the piece (CHUNK_AUTHORING conventions 2 and 5);
  2. MEASURES the openings: ray-casts down along each edge and finds the flat
     mouth pad at walk height. A pad >= 50 studs wide is WIDE, >= 40 is PATH,
     narrower is terrain. The result must equal EXPECTED below or the run fails.
     (The .blend's own "sockets" properties label N as Blender -Y but E as +X --
     a mirror, which no mesh turn can satisfy on the asymmetric pieces. That is
     why the sockets were redone from the geometry instead of copied.)
  3. checks the engine contract: exact footprint, triangle budget, every mouth
     at the same ground height.
Then it writes:
  assets/export/worlds/verdant_valley/verdant_valley_structure.fbx
                                 30 pieces, one mesh each, all at the origin
  verdant_valley_kit.blend       the same objects laid out on a review grid
  generated/ (or --out):
    VerdantValley.luau           -> src/shared/Content/Chunks/VerdantValley.luau
    AssetManifest_VV.luau        -> the VV block of Content/AssetManifest.luau
                                    (AssetIds from --ids {name: rbxassetid},
                                    else PLACEHOLDER = blockout until uploaded)
    kit_report.json              every measured number
and re-imports the FBX to confirm 30 objects at the right sizes.

Axes: Blender +Y is game NORTH (-Z) under the -Z Forward / Y Up export, +X is
east. Roblox's importer lands that a half turn out, exactly as it did for Sky
Citadel, so the content sets MeshYawOffset = 180 as the tie-break hint.
ChunkLoader.calibrateYaw measures the true turn per piece anyway.
"""

import json
import os
import re
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
FBX_PATH = os.path.join(REPO, "assets", "export", "worlds", "verdant_valley", "verdant_valley_structure.fbx")
KIT_BLEND = os.path.join(HERE, "verdant_valley_kit.blend")

FOOT = 256.0
TRI_BUDGET = 10000
PAD_TOL = 0.35  # studs: how flat a mouth pad must be
PATH_MIN, WIDE_MIN = 40.0, 50.0
WIDTH = {"PATH": 48, "WIDE": 52}  # measured pad widths -> socket Width
FACING = {"N": 0, "E": 90, "S": 180, "W": 270}
EDGE_DIR = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}  # Blender XY

# Per piece: object name, role, measured openings (game frame, Kind), content.
# Openings are what the geometry has; the run fails if a measurement disagrees.
P = lambda *a: set(a)  # noqa: E731
EXPECTED = {
    "01": ("chunk_path_sunwash_fork", "PATH", {"N": "PATH", "S": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=20,
                EnemyTags=["MOSS_SLIME", "FOREST_WOLF"], Tags=["junction", "sunlit"])),
    "02": ("chunk_cutbank_ford", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush", "Event"), Weight=20, MaxPerLayout=1,
                EnemyTags=["THORN_GOBLIN"], Tags=["water", "ford"])),
    "03": ("chunk_windward_ridge_gate", "COMBAT", {"W": "PATH", "E": "WIDE"},
           dict(Supports=P("Combat", "Traversal", "Ambush", "Shrine", "MiniBoss"), Weight=25, MaxPerLayout=1,
                EnemyTags=["ELDER_TREANT"], Tags=["gate-to-boss", "high-ground"])),
    "04": ("chunk_forgotten_orchard_gate", "COMBAT", {"W": "PATH", "S": "WIDE"},
           dict(Supports=P("Combat", "Treasure", "Secret", "Shrine"), Weight=25, MaxPerLayout=1,
                EnemyTags=["FOREST_WOLF", "ELDER_TREANT"], Tags=["gate-to-boss", "turn"])),
    "05": ("chunk_longgrass_meadow", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "MiniBoss", "Treasure", "Ambush"), Weight=30,
                EnemyTags=["FOREST_WOLF"], Tags=["open", "pack-combat"])),
    "06": ("chunk_shaded_grove", "COMBAT", {"W": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Ambush", "Secret"), Weight=25,
                EnemyTags=["ELDER_TREANT", "MOSS_SLIME"], Tags=["enclosed", "shade"])),
    "07": ("chunk_fern_hollow", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Puzzle", "Treasure", "Secret", "Ambush"), Weight=20,
                EnemyTags=["THORN_GOBLIN"], Tags=["enclosed", "risk-reward"])),
    "08": ("chunk_path_cliff_passage", "PATH", {"W": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=30,
                EnemyTags=["FOREST_WOLF"], Tags=["cliff", "narrow"])),
    "09": ("chunk_stone_sentinels", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Shrine", "Puzzle", "Event"), Weight=20, MaxPerLayout=1,
                EnemyTags=["MOSS_SLIME", "THORN_GOBLIN"], Tags=["landmark", "stones"])),
    "10": ("chunk_mossbound_ruins", "COMBAT", {"W": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Puzzle", "Treasure", "Secret", "Event"), Weight=20, MaxPerLayout=1,
                EnemyTags=["THORN_GOBLIN", "ELDER_TREANT"], Tags=["ruin"])),
    "11": ("chunk_ancient_oak", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Shrine", "Event", "MiniBoss"), Weight=15, MaxPerLayout=1,
                EnemyTags=["ELDER_TREANT"], Tags=["landmark"])),
    "12": ("chunk_wetland_pools", "COMBAT", {"W": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush", "Event"), Weight=20,
                EnemyTags=["THORN_GOBLIN", "MOSS_SLIME"], Tags=["water"])),
    "13": ("chunk_path_narrow_pass", "PATH", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=35,
                EnemyTags=["FOREST_WOLF"], Tags=["narrow"])),
    "14": ("chunk_blossom_terrace", "COMBAT", {"W": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Shrine", "Treasure", "Event"), Weight=20,
                EnemyTags=["MOSS_SLIME"], Tags=["terrace", "blossom"])),
    "15": ("chunk_rock_garden", "COMBAT", {"N": "PATH", "S": "PATH"},
           dict(Supports=P("Combat", "Puzzle", "Secret", "Ambush"), Weight=20,
                EnemyTags=["THORN_GOBLIN"], Tags=["cover"])),
    "16": ("chunk_crystal_spring_gate", "COMBAT", {"W": "PATH", "E": "WIDE"},
           dict(Supports=P("Combat", "Shrine", "Event", "Secret"), Weight=25, MaxPerLayout=1,
                EnemyTags=["ELDER_TREANT"], Tags=["gate-to-boss", "water"])),
    "17": ("chunk_overgrown_causeway_gate", "COMBAT", {"S": "PATH", "N": "WIDE"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=25, MaxPerLayout=1,
                EnemyTags=["FOREST_WOLF", "ELDER_TREANT"], Tags=["gate-to-boss"])),
    "18": ("chunk_high_ledge_gate", "COMBAT", {"W": "PATH", "E": "WIDE"},
           dict(Supports=P("Combat", "Traversal", "MiniBoss", "Ambush"), Weight=25, MaxPerLayout=1,
                EnemyTags=["ELDER_TREANT"], Tags=["gate-to-boss", "high-ground"])),
    "19": ("chunk_cliff_overlook_gate", "COMBAT", {"S": "PATH", "N": "WIDE"},
           dict(Supports=P("Combat", "Traversal", "Shrine", "MiniBoss"), Weight=25, MaxPerLayout=1,
                EnemyTags=["ELDER_TREANT"], Tags=["gate-to-boss", "vista"])),
    "20": ("chunk_deep_clearing", "COMBAT", {"N": "PATH", "S": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "MiniBoss", "Ambush", "Treasure"), Weight=20,
                EnemyTags=["FOREST_WOLF"], Tags=["open", "junction"])),
    "21": ("chunk_path_split_meadow", "PATH", {"W": "PATH", "E": "PATH", "N": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=20,
                EnemyTags=["FOREST_WOLF", "MOSS_SLIME"], Tags=["junction"])),
    "22": ("chunk_mushroom_glen", "COMBAT", {"N": "PATH", "S": "PATH", "E": "PATH"},
           dict(Supports=P("Combat", "Shrine", "Event", "Secret", "Puzzle"), Weight=18, MaxPerLayout=1,
                EnemyTags=["THORN_GOBLIN", "MOSS_SLIME"], Tags=["strange", "junction"])),
    "23": ("chunk_path_crossroads_copse", "PATH", {"N": "PATH", "S": "PATH", "E": "PATH", "W": "PATH"},
           dict(Supports=P("Combat", "Traversal", "Ambush"), Weight=12, MaxPerLayout=1,
                EnemyTags=["FOREST_WOLF"], Tags=["junction", "four-way"])),
    "24": ("chunk_cap_cave_mouth", "CAP", {"N": "PATH"},
           dict(Supports=P("Treasure", "Secret"), Weight=1,
                EnemyTags=["MOSS_SLIME"], Tags=["dead-end", "cave"])),
    "25": ("chunk_entry_dawn_meadow", "ENTRY", {"N": "PATH"},
           dict(Weight=1, MaxPerLayout=1, EnemyTags=["MOSS_SLIME"], Tags=["tutorial", "low-density"])),
    "26": ("chunk_entry_woodland_refuge", "ENTRY", {"N": "PATH"},
           dict(Weight=1, MaxPerLayout=1, EnemyTags=["MOSS_SLIME"], Tags=["tutorial", "low-density"])),
    "27": ("chunk_boss_sanctuary", "BOSS", {"N": "WIDE"},
           dict(Weight=1, MaxPerLayout=1, EnemyTags=[], Tags=["arena"])),
    "28": ("chunk_side_treasure_hollow", "SIDE", {"N": "PATH"},
           dict(Supports=P("Treasure", "Secret"), Weight=1, MaxPerLayout=1,
                EnemyTags=["THORN_GOBLIN"], Tags=["pocket", "treasure"])),
    "29": ("chunk_side_wardens_clearing", "SIDE", {"N": "PATH"},
           dict(Supports=P("Combat", "MiniBoss"), Weight=1, MaxPerLayout=1,
                EnemyTags=["FOREST_WOLF", "ELDER_TREANT"], Tags=["pocket", "mini-boss"])),
    "30": ("chunk_side_forgotten_trial", "SIDE", {"N": "PATH"},
           dict(Supports=P("Puzzle", "Treasure"), Weight=1, MaxPerLayout=1,
                EnemyTags=["MOSS_SLIME"], Tags=["pocket", "puzzle"])),
}


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out, ids = os.path.join(HERE, "generated"), None
    for i, a in enumerate(argv):
        if a == "--out":
            out = argv[i + 1]
        elif a == "--ids":
            ids = argv[i + 1]
    os.makedirs(out, exist_ok=True)
    return out, (json.load(open(ids)) if ids else {})


def material_rgb(mat):
    if mat is None:
        return (0.5, 0.5, 0.5)
    if mat.use_nodes and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                inp = n.inputs["Base Color"]
                if not inp.is_linked:
                    return tuple(inp.default_value[:3])
                break
    return tuple(mat.diffuse_color[:3])


def build_piece(coll, empty, name, dg):
    """Evaluated copies of every mesh in the piece, in the piece's frame, joined."""
    off = empty.matrix_world.translation.copy()
    parts = []
    for o in coll.all_objects:
        if o.type != "MESH":
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        for v in me.vertices:
            v.co -= off
        for attr in list(me.color_attributes):
            me.color_attributes.remove(attr)
        col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        rgb = [material_rgb(m) for m in me.materials] or [(0.5, 0.5, 0.5)]
        for poly in me.polygons:
            c = (*rgb[min(poly.material_index, len(rgb) - 1)], 1.0)
            for li in poly.loop_indices:
                col.data[li].color = c
        ob = bpy.data.objects.new(name + "_part", me)
        bpy.context.scene.collection.objects.link(ob)
        parts.append(ob)
    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts,
                                   selected_objects=parts):
        bpy.ops.object.join()
    ob = parts[0]
    ob.name = ob.data.name = name
    ob.data.color_attributes.active_color = ob.data.color_attributes["Col"]
    return ob


def measure(ob):
    me = ob.data
    verts = [v.co.copy() for v in me.vertices]
    bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in me.polygons])
    mn = Vector((min(v[i] for v in verts) for i in range(3)))
    mx = Vector((max(v[i] for v in verts) for i in range(3)))

    def ground(x, y):
        hit = bvh.ray_cast(Vector((x, y, 500)), Vector((0, 0, -1)), 2000)
        return None if hit[0] is None else hit[0].z

    openings, pads = {}, {}
    for side, (ex, ey) in EDGE_DIR.items():
        half = mx.x if ex else mx.y
        lx, ly = abs(ey), abs(ex)
        ts = [t * 0.5 for t in range(-200, 201)]
        ok = [(z is not None and abs(z) < PAD_TOL)
              for z in (ground(ex * (half - 2) + lx * t, ey * (half - 2) + ly * t) for t in ts)]
        width, c = 0.0, len(ts) // 2
        if ok[c]:
            a = b = c
            while a > 0 and ok[a - 1]:
                a -= 1
            while b < len(ok) - 1 and ok[b + 1]:
                b += 1
            width = (b - a) * 0.5
        pads[side] = width
        if width >= WIDE_MIN:
            openings[side] = "WIDE"
        elif width >= PATH_MIN:
            openings[side] = "PATH"
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    return dict(min=list(mn), max=list(mx), tris=tris, openings=openings, pads=pads,
                ground_centre=ground(0, 0))


def socket_line(side, kind, hx, hz):
    off = {"N": (0, -hz), "S": (0, hz), "E": (hx, 0), "W": (-hx, 0)}[side]
    name = {"N": "north", "S": "south", "E": "east", "W": "west"}[side]
    fmt = lambda v: str(int(v)) if v == int(v) else f"{v:g}"  # noqa: E731
    return f'socket("{name}", "{kind}", {fmt(off[0])}, {fmt(off[1])}, {FACING[side]})'


def luau_list(xs):
    return "{ " + ", ".join(f'"{x}"' for x in xs) + " }" if xs else "{}"


def write_content(out, rows, ids):
    L = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/verdant_valley/export_verdant_valley_kit.py",
        "-- from the 30-piece base kit. Do not hand-edit: change the script's EXPECTED",
        "-- table and re-run it. docs/biomes/VERDANT_VALLEY.md has the design.",
        "--",
        "-- Every socket below was MEASURED off the delivered geometry (flat mouth pad",
        "-- at walk height on that edge; 48 studs = PATH, 52 = WIDE). Facing: 0 = -Z",
        "-- (north), 90 = +X, 180 = +Z, 270 = -X. The arena accepts only WIDE, and six",
        "-- pieces offer it, so the approach to the boss differs per run.",
        "--",
        "-- GroundOffsetY = studs from the bottom of the piece's box up to the walk plane.",
        "-- MeshYawOffset = 180: the same half turn the Sky Citadel export landed at;",
        "-- ChunkLoader.calibrateYaw measures the real turn, this is only its tie-break.",
        "",
        "local function socket(id: string, kind: string, x: number, z: number, facing: number)",
        "\treturn { Id = id, Kind = kind, OffsetX = x, OffsetY = 0, OffsetZ = z, Facing = facing,",
        "\t\tWidth = if kind == \"WIDE\" then %d else %d }" % (WIDTH["WIDE"], WIDTH["PATH"]),
        "end",
        "",
        "local CHUNKS = {",
    ]
    for r in rows:
        meta = r["meta"]
        sx, sz = r["size"][0], r["size"][2]
        L.append("\t{")
        L.append(f'\t\tId = "{r["id"]}",')
        L.append(f'\t\tRole = "{r["role"]}" :: any,')
        L.append(f'\t\tAssetKey = "{r["key"]}",')
        L.append(f"\t\tSizeX = {sx:g}, SizeY = {r['size'][1]:.2f}, SizeZ = {sz:g},")
        L.append(f"\t\tGroundOffsetY = {r['ground']:.2f},")
        socks = ", ".join(socket_line(s, k, sx / 2, sz / 2) for s, k in r["sockets"])
        L.append(f"\t\tSockets = {{ {socks} }},")
        if "Supports" in meta:
            L.append("\t\tSupports = { " + ", ".join(f"{s} = true" for s in sorted(meta["Supports"])) + " },")
        L.append(f"\t\tWeight = {meta['Weight']},")
        if "MaxPerLayout" in meta:
            L.append(f"\t\tMaxPerLayout = {meta['MaxPerLayout']},")
        L.append(f"\t\tEnemyTags = {luau_list(meta['EnemyTags'])},")
        L.append(f"\t\tTags = {luau_list(meta['Tags'])},")
        L.append("\t},")
    L += [
        "}",
        "",
        "local out = {}",
        "for _, chunk in CHUNKS do",
        "\tlocal c = table.clone(chunk) :: any",
        '\tc.WorldId = "VERDANT_VALLEY"',
        "\tc.MeshYawOffset = 180",
        "\ttable.insert(out, c)",
        "end",
        "return out",
        "",
    ]
    open(os.path.join(out, "VerdantValley.luau"), "w", newline="\n").write("\n".join(L))

    M = ["\t-- Verdant Valley base kit, 30 pieces. GENERATED by export_verdant_valley_kit.py;",
         "\t-- PLACEHOLDER draws the blockout until the piece is uploaded (re-run with --ids)."]
    for r in rows:
        aid = ids.get(r["name"]) or ids.get(r["key"])
        M += [f"\t{r['key']} = {{",
              f'\t\tAssetId = "{aid if aid else "PLACEHOLDER"}",',
              f'\t\tStatus = "{"UPLOADED" if aid else "PLACEHOLDER"}",',
              '\t\tSource = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",',
              f'\t\tNotes = "{r["title"]}. {r["role"]}, opens {"+".join(s for s, _ in r["sockets"])}. '
              f'{r["size"][1]:.1f} studs tall.",',
              "\t},"]
    open(os.path.join(out, "AssetManifest_VV.luau"), "w", newline="\n").write("\n".join(M) + "\n")


def export_fbx(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", colors_type="SRGB",
        add_leaf_bones=False, bake_anim=False, path_mode="AUTO",
    )


def verify_fbx(path, rows):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name.split(".")[0]: o for o in set(bpy.data.objects) - before if o.type == "MESH"}
    errs = []
    if len(got) != len(rows):
        errs.append(f"re-import has {len(got)} meshes, expected {len(rows)}")
    for r in rows:
        o = got.get(r["name"])
        if o is None:
            errs.append(f"{r['name']} missing from re-import")
            continue
        # Dimensions are in the object's own frame, which is the FBX's Y-up
        # frame -- the one Roblox reads: (X, height, Z).
        d = o.dimensions
        want = Vector(r["size"])
        if (Vector(d) - want).length > 0.5:
            errs.append(f"{r['name']} re-imports at {tuple(round(x, 2) for x in d)}, expected {tuple(want)}")
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    return errs


def main():
    out, ids = args()
    dg = bpy.context.evaluated_depsgraph_get()
    rows, errors, objs = [], [], []
    for coll in sorted(bpy.data.collections, key=lambda c: c.name):
        m = re.match(r"^(\d\d) (.+)$", coll.name)
        if not m:
            continue
        num, title = m.groups()
        name, role, want, meta = EXPECTED[num]
        empty = next(o for o in coll.objects if o.type == "EMPTY" and o.name.endswith("_REVIEW_OFFSET"))
        ob = build_piece(coll, empty, name, dg)
        objs.append(ob)
        ms = measure(ob)
        label = f"{num} {title} ({name})"
        mn, mx = ms["min"], ms["max"]
        size = [round(mx[0] - mn[0], 3), round(mx[2] - mn[2], 3), round(mx[1] - mn[1], 3)]  # game X, Y, Z
        if abs(mn[0] + mx[0]) > 0.01 or abs(mn[1] + mx[1]) > 0.01:
            errors.append(f"{label}: footprint not centred on the origin ({mn[0]:.2f}..{mx[0]:.2f}, {mn[1]:.2f}..{mx[1]:.2f})")
        if round(size[2]) != FOOT or round(size[0]) not in (FOOT, 384):
            errors.append(f"{label}: footprint {size[0]} x {size[2]}, kit is 256 (boss 384 x 256)")
        if ms["tris"] > TRI_BUDGET:
            errors.append(f"{label}: {ms['tris']} triangles, budget {TRI_BUDGET}")
        if ms["openings"] != want:
            errors.append(f"{label}: measured openings {ms['openings']} (pads {ms['pads']}), expected {want}")
        order = [s for s in ("N", "E", "S", "W") if s in want]
        rows.append(dict(
            num=num, title=title, name=name, role=role, meta=meta,
            id="VV_" + name[len("chunk_"):].upper(), key="VV_CHUNK_" + name[len("chunk_"):].upper(),
            size=size, ground=round(-mn[2], 3), tris=ms["tris"], pads=ms["pads"],
            sockets=[(s, want[s]) for s in order], materials=len(ob.data.materials),
        ))
        print(f"[vv] {label}: {ms['tris']} tris, {size[0]:g}x{size[1]:.1f}x{size[2]:g}, "
              f"ground {-mn[2]:.2f}, opens {ms['openings']}")

    if errors:
        print("\n".join("[vv] ERROR " + e for e in errors))
        raise SystemExit(1)

    # Drop the source art; keep only the 30 export objects.
    keep = set(objs)
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    kit = bpy.data.collections.new("VerdantValley_Structure")
    bpy.context.scene.collection.children.link(kit)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        kit.objects.link(o)
        o["kit"] = "VERDANT_VALLEY"
    bpy.ops.outliner.orphans_purge(do_recursive=True)

    fbx = FBX_PATH
    export_fbx(fbx, objs)  # every piece at the world origin (CHUNK_AUTHORING convention 2)
    errs = verify_fbx(fbx, rows)
    if errs:
        print("\n".join("[vv] ERROR " + e for e in errs))
        raise SystemExit(1)

    # Review layout: same 5 x 6 grid as the delivered file, 400 studs apart.
    for i, o in enumerate(objs):
        o.location = ((i % 6) * 400 - 1000, 800 - (i // 6) * 400, 0)
    bpy.ops.wm.save_as_mainfile(filepath=KIT_BLEND, compress=True)

    write_content(out, rows, ids)
    json.dump(rows, open(os.path.join(out, "kit_report.json"), "w"), indent=1,
              default=lambda s: sorted(s) if isinstance(s, set) else str(s))
    print(f"[vv] OK: {len(rows)} pieces -> {fbx}")


main()
