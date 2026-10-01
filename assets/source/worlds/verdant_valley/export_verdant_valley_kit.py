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
    "28": ("chunk_cap_treasure_hollow", "CAP", {"N": "PATH"},
           dict(Supports=P("Treasure", "Secret"), Weight=1,
                EnemyTags=["THORN_GOBLIN"], Tags=["pocket", "treasure"])),
    "29": ("chunk_cap_wardens_clearing", "CAP", {"N": "PATH"},
           dict(Supports=P("Combat", "MiniBoss"), Weight=1,
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
        if r["id"] == "VV_STONE_SENTINELS":
            L.append('\t\tCollisionTemplate = "VV_STONE_SENTINELS_COLLISION_MERGED",')
        elif r["id"] != "VV_PATH_CLIFF_PASSAGE":
            L.append(f'\t\tCollisionTemplate = "{r["id"]}_COLLISION_MERGED",')
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


def prop_mesh_size(obj):
    """Bounds in Roblox X/Y/Z order, from vertices rather than stale dimensions."""
    coords = [vertex.co for vertex in obj.data.vertices]
    return [round(max(v[0] for v in coords) - min(v[0] for v in coords), 3),
            round(max(v[2] for v in coords) - min(v[2] for v in coords), 3),
            round(max(v[1] for v in coords) - min(v[1] for v in coords), 3)]


def export_props(objects, placements, fbx_path, content_path):
    """Export PropLibrary meshes and their chunk-relative placement rows."""
    objects = sorted(objects, key=lambda obj: obj.name)
    if not objects:
        return
    if len({obj.name for obj in objects}) != len(objects):
        raise SystemExit("PropLibrary contains duplicate prop names")
    for obj in objects:
        if obj.type != "MESH" or not obj.name.startswith("prop_"):
            raise SystemExit(f"PropLibrary object must be a prop_* mesh: {obj.name}")
        if "solid" in obj and not isinstance(obj["solid"], bool):
            raise SystemExit(f"{obj.name}: solid tag must be a boolean")
        color = obj.data.color_attributes.get("Col")
        if color is None or color.domain != "CORNER" or color.data_type != "BYTE_COLOR":
            raise SystemExit(f"{obj.name}: missing BYTE_COLOR/CORNER Col attribute")
        for polygon in obj.data.polygons:
            expected = (*material_rgb(obj.data.materials[polygon.material_index]), 1.0)
            for loop_index in polygon.loop_indices:
                if any(abs(a - b) > 0.02 for a, b in zip(color.data[loop_index].color, expected)):
                    raise SystemExit(f"{obj.name}: Col differs from material at face {polygon.index}")
    export_fbx(fbx_path, objects)
    errors = verify_fbx(fbx_path, [{"name": obj.name,
                                    "size": prop_mesh_size(obj)}
                                   for obj in objects])
    if errors:
        raise SystemExit("\n".join(errors))
    lines = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/verdant_valley/export_verdant_valley_kit.py",
        "-- Change Blender's PropLibrary objects and re-export; do not hand-edit.",
        "return {",
        '\tId = "VERDANT_VALLEY",',
        "\tLibrary = { " + ", ".join(f'"{obj.name}"' for obj in objects) + " },",
        "\tPlacements = {",
    ]
    names = {obj.name: obj for obj in objects}
    for chunk_id, rows in sorted(placements.items()):
        lines.append(f"\t\t{chunk_id} = {{")
        for row in rows:
            obj = names[row["prop"]]
            fmt = lambda values: "{ " + ", ".join(f"{value:g}" for value in values) + " }"  # noqa: E731
            lines.extend([
                "\t\t\t{",
                f'\t\t\t\tProp = "{obj.name}",',
                f'\t\t\t\tP = {fmt(row["position"])},',
                f'\t\t\t\tR = {fmt(row["rotation"])},',
                f'\t\t\t\tS = {fmt(row["size"])},',
                '\t\t\t\tAnim = "Static",',
                "\t\t\t\tTier = 1,",
                f'\t\t\t\tCollide = {str(obj.get("solid", False)).lower()},',
                "\t\t\t},",
            ])
        lines.append("\t\t},")
    lines.extend(["\t},", "}", ""])
    os.makedirs(os.path.dirname(content_path), exist_ok=True)
    with open(content_path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))


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


def split_causeway(original):
    """Keep the connected terrain; move loose scenery into one static prop."""
    import bmesh

    mesh = original.data
    parents = list(range(len(mesh.vertices)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for edge in mesh.edges:
        a, b = edge.vertices
        parents[root(b)] = root(a)
    groups = {}
    for vertex in mesh.vertices:
        groups.setdefault(root(vertex.index), set()).add(vertex.index)
    terrain_indices = max(groups.values(), key=len)
    if len(groups) < 2:
        raise SystemExit("causeway has no detached scenery to split")

    def subset(name, keep_terrain):
        obj = original.copy()
        obj.data = mesh.copy()
        obj.name = name
        bpy.context.scene.collection.objects.link(obj)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        remove = [bm.verts[i] for i in range(len(mesh.vertices))
                  if (i in terrain_indices) != keep_terrain]
        bmesh.ops.delete(bm, geom=remove, context="VERTS")
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        return obj

    terrain = subset(original.name, True)
    decor = subset("prop_overgrown_causeway_scenery", False)
    decor["solid"] = True
    if (len(terrain.data.polygons) + len(decor.data.polygons) != len(mesh.polygons)
            or len(terrain.data.vertices) + len(decor.data.vertices) != len(mesh.vertices)):
        raise SystemExit("causeway split lost geometry")
    bpy.data.objects.remove(original, do_unlink=True)
    terrain.name = "chunk_overgrown_causeway_gate"
    # Roblox's prop controller positions a MeshPart by its local bounding box.
    # Centre the prop's geometry and record that centre in the layout frame.
    coords = [v.co for v in decor.data.vertices]
    centre = Vector(tuple((min(v[i] for v in coords) + max(v[i] for v in coords)) / 2
                          for i in range(3)))
    for vertex in decor.data.vertices:
        vertex.co -= centre
    decor.location = centre
    decor.data.update()
    return terrain, decor, centre, len(groups) - 1


AMBIENT_MATERIALS = {
    "VV_Water", "VV_DetailFoam", "VV_Leaf", "VV_LeafLight",
    "VV_Flower", "VV_Blossom", "VV_DetailMoss", "VV_DetailBloom",
    "VV_DetailFungus", "VV_CaveFlame", "VV_CaveFlameCore",
    "VV_Gold", "VV_CaveGold", "VV_CaveGoldLight",
}


def split_remaining_piece(original, terrain_name):
    """Partition one reviewed chunk into terrain and tagged PropLibrary meshes.

    The largest connected component owns the full footprint. Detached path,
    bridge and grass/earth islands are kept as solid walkable surfaces, rather
    than folded into the scenery collider. The remaining static obstacles and
    ambient details are grouped independently per chunk.
    """
    import bmesh

    mesh = original.data
    parents = list(range(len(mesh.vertices)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for edge in mesh.edges:
        a, b = edge.vertices
        parents[root(b)] = root(a)
    components = {}
    for vertex in mesh.vertices:
        components.setdefault(root(vertex.index), set()).add(vertex.index)
    if len(components) < 2:
        raise SystemExit(f"{original.name}: no detachable scenery")
    terrain_indices = max(components.values(), key=len)
    materials = {key: set() for key in components}
    for polygon in mesh.polygons:
        materials[root(polygon.vertices[0])].add(mesh.materials[polygon.material_index].name)

    def subset(name, keep):
        obj = original.copy()
        obj.data = mesh.copy()
        obj.name = name
        bpy.context.scene.collection.objects.link(obj)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        remove = [bm.verts[i] for i in range(len(mesh.vertices)) if i not in keep]
        bmesh.ops.delete(bm, geom=remove, context="VERTS")
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        return obj

    base = terrain_name.removeprefix("chunk_")
    terrain = subset(terrain_name, terrain_indices)
    grouped = {"surface": [], "scenery": [], "ambient": []}
    for key, indices in components.items():
        if indices is terrain_indices:
            continue
        mats = materials[key]
        if ({"VV_Path", "VV_Grass", "VV_Earth"} & mats
                or any(mat.startswith("VVBridge") for mat in mats)):
            category = "surface"
        elif all(mat in AMBIENT_MATERIALS or mat.startswith("VVFix_MushroomCap")
                 for mat in mats):
            category = "ambient"
        else:
            category = "scenery"
        grouped[category].append(indices)

    selections = []
    for category, groups in grouped.items():
        if category == "surface" and base == "wetland_pools":
            selections.extend((f"surface_{i:02d}", group, True)
                              for i, group in enumerate(groups, 1))
        elif groups:
            selections.append((category, set().union(*groups), category != "ambient"))

    props = []
    for label, indices, solid in selections:
        prop = subset(f"prop_{base}_{label}", indices)
        coords = [v.co for v in prop.data.vertices]
        centre = Vector(tuple((min(v[i] for v in coords) + max(v[i] for v in coords)) / 2
                              for i in range(3)))
        for vertex in prop.data.vertices:
            vertex.co -= centre
        prop.location = centre
        prop.data.update()
        prop["solid"] = solid
        props.append((prop, centre, len(indices)))

    if (len(terrain.data.polygons) + sum(len(p.data.polygons) for p, _, _ in props)
            != len(mesh.polygons)
            or len(terrain.data.vertices) + sum(len(p.data.vertices) for p, _, _ in props)
            != len(mesh.vertices)):
        raise SystemExit(f"{original.name}: split lost geometry")
    bpy.data.objects.remove(original, do_unlink=True)
    terrain.name = terrain_name
    return terrain, props, len(components) - 1


def write_split_chunk_candidate(rows, path):
    """Stage new terrain bounds without changing the live chunk content."""
    source_path = os.path.join(REPO, "src", "shared", "Content", "Chunks", "VerdantValley.luau")
    lines = open(source_path, encoding="utf-8").read().splitlines()
    by_id = {"VV_" + row["name"].removeprefix("chunk_").upper(): row for row in rows}
    seen = set()
    current = None
    out = []
    for line in lines:
        match = re.match(r'\s*Id = "(VV_[A-Z_]+)",', line)
        if match:
            current = match.group(1)
            if current in by_id:
                seen.add(current)
        if current in by_id and "SizeX = " in line and "SizeY = " in line:
            row = by_id[current]
            line = re.sub(r"SizeY = [0-9.]+", f"SizeY = {row['size'][1]:.2f}", line)
        if current in by_id and "GroundOffsetY = " in line:
            row = by_id[current]
            old = float(re.search(r"GroundOffsetY = ([0-9.]+)", line).group(1))
            if abs(old - row["ground"]) > 0.02:
                raise SystemExit(f"{current}: ground offset moved from {old} to {row['ground']}")
        out.append(line)
    if seen != set(by_id):
        raise SystemExit(f"split candidate missing chunk ids: {set(by_id) - seen}")
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("-- STAGED terrain bounds; activate only with all new MeshIds.\n")
        stream.write("\n".join(out) + "\n")


def export_joined_scene():
    """Export the reviewed 30-mesh scene without regenerating or renaming pieces.

    This path is for a joined cleanup .blend. The original generator path below
    remains the source for authoring a new kit from the loose source collection.
    """
    argv = sys.argv[sys.argv.index("--") + 1:]
    if "--out-fbx" not in argv:
        raise SystemExit("--joined-scene requires --out-fbx PATH")
    fbx = os.path.abspath(argv[argv.index("--out-fbx") + 1])
    report_path = os.path.join(os.path.dirname(fbx), "kit_report.json")
    os.makedirs(os.path.dirname(fbx), exist_ok=True)

    source = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    names = [o.name for o in source]
    if len(source) != 30 or len(set(names)) != 30 or any(not n.startswith("chunk_") for n in names):
        raise SystemExit("joined scene must contain exactly 30 uniquely named chunk_* meshes")

    # The review scene retains its own names for these two chunks. Keep them;
    # existing content keys can still map to the uploaded MeshIds independently.
    expected_names = {row[0] for row in EXPECTED.values()}
    expected_names -= {"chunk_cap_treasure_hollow", "chunk_cap_wardens_clearing"}
    expected_names |= {"chunk_side_treasure_hollow", "chunk_side_wardens_clearing"}
    if set(names) != expected_names:
        raise SystemExit(f"joined scene names differ: missing {expected_names - set(names)}, extra {set(names) - expected_names}")

    split = "--split-causeway" in argv
    split_all = "--split-all" in argv
    if split and split_all:
        raise SystemExit("choose one split mode")
    rows = []
    export_objects = []
    prop = None
    all_props = []
    placements = {}
    split_report = {}
    review_props = {}
    canonical_names = {
        "chunk_side_treasure_hollow": "chunk_cap_treasure_hollow",
        "chunk_side_wardens_clearing": "chunk_cap_wardens_clearing",
    }
    expected_openings = {name: openings for name, _, openings, _ in EXPECTED.values()}
    for original in sorted(source, key=lambda o: o.name):
        # The background process is disposable; reset only its review-grid offsets.
        original_name = original.name
        terrain_name = canonical_names.get(original_name, original_name)
        original.location = (0, 0, 0)
        obj = original
        if split_all and original_name != "chunk_overgrown_causeway_gate":
            obj, piece_props, detached = split_remaining_piece(original, terrain_name)
            all_props.extend(p for p, _, _ in piece_props)
            review_props[terrain_name] = [p for p, _, _ in piece_props]
            chunk_id = "VV_" + terrain_name.removeprefix("chunk_").upper()
            placements[chunk_id] = []
            for piece_prop, centre, count in piece_props:
                placements[chunk_id].append({
                    "prop": piece_prop.name,
                    "position": [round(centre[0], 3), round(centre[2], 3), round(-centre[1], 3)],
                    "rotation": [1, 0, 0, 0, 1, 0, 0, 0, 1],
                    "size": prop_mesh_size(piece_prop),
                })
            split_report[terrain_name] = {"source_name": original_name,
                                           "detached_components": detached,
                                           "props": [{"name": p.name, "solid": p["solid"],
                                                      "vertices": count}
                                                     for p, _, count in piece_props]}
            print(f"[vv] {original_name}: {detached} detached components -> {len(piece_props)} props")
        elif (split or split_all) and original_name == "chunk_overgrown_causeway_gate":
            obj, prop, centre, detached = split_causeway(original)
            print(f"[vv] causeway: separated {detached} scenery components")
            if split_all:
                all_props.append(prop)
                review_props[original_name] = [prop]
                placements["VV_OVERGROWN_CAUSEWAY_GATE"] = [{
                    "prop": prop.name,
                    "position": [round(centre[0], 3), round(centre[2], 3), round(-centre[1], 3)],
                    "rotation": [1, 0, 0, 0, 1, 0, 0, 0, 1],
                    "size": prop_mesh_size(prop),
                }]
                split_report[original_name] = {"detached_components": detached,
                                               "props": [{"name": prop.name,
                                                          "solid": True,
                                                          "vertices": len(prop.data.vertices)}]}
        export_objects.append(obj)
        mesh = obj.data
        color = mesh.color_attributes.get("Col")
        if color is None or color.domain != "CORNER" or color.data_type != "BYTE_COLOR":
            raise SystemExit(f"{original_name}: missing BYTE_COLOR/CORNER Col attribute")
        for polygon in mesh.polygons:
            expected = (*material_rgb(mesh.materials[polygon.material_index]), 1.0)
            for loop_index in polygon.loop_indices:
                if any(abs(a - b) > 0.02 for a, b in zip(color.data[loop_index].color, expected)):
                    raise SystemExit(f"{original_name}: Col differs from material at face {polygon.index}")
        ms = measure(obj)
        if split_all and ms["openings"] != expected_openings[terrain_name]:
            raise SystemExit(f"{terrain_name}: split changed socket openings to {ms['openings']}")
        mn, mx = ms["min"], ms["max"]
        size = [round(mx[0] - mn[0], 3), round(mx[2] - mn[2], 3), round(mx[1] - mn[1], 3)]
        if abs(mn[0] + mx[0]) > 0.01 or abs(mn[1] + mx[1]) > 0.01:
            raise SystemExit(f"{original_name}: footprint is not centered")
        if round(size[2]) != FOOT or round(size[0]) not in (FOOT, 384):
            raise SystemExit(f"{obj.name}: incompatible footprint {size}")
        if ms["tris"] > TRI_BUDGET:
            raise SystemExit(f"{obj.name}: {ms['tris']} triangles exceed the {TRI_BUDGET} budget")
        rows.append(dict(name=obj.name, size=size, triangles=ms["tris"],
                         openings=ms["openings"], pads=ms["pads"],
                         ground=round(-mn[2], 3)))

    export_fbx(fbx, export_objects)
    errors = verify_fbx(fbx, rows)
    if errors:
        raise SystemExit("\n".join(errors))
    if split:
        if prop is None:
            raise SystemExit("causeway was not found")
        terrain = next(o for o in export_objects if o.name == "chunk_overgrown_causeway_gate")
        terrain_fbx = os.path.join(os.path.dirname(fbx), "verdant_valley_causeway_terrain.fbx")
        export_fbx(terrain_fbx, [terrain])
        errors = verify_fbx(terrain_fbx, [next(r for r in rows if r["name"] == terrain.name)])
        if errors:
            raise SystemExit("\n".join(errors))
        prop_color = prop.data.color_attributes.get("Col")
        if prop_color is None or prop_color.domain != "CORNER" or prop_color.data_type != "BYTE_COLOR":
            raise SystemExit("causeway scenery lost its vertex colors")
        for polygon in prop.data.polygons:
            expected = (*material_rgb(prop.data.materials[polygon.material_index]), 1.0)
            for loop_index in polygon.loop_indices:
                if any(abs(a - b) > 0.02 for a, b in zip(prop_color.data[loop_index].color, expected)):
                    raise SystemExit(f"causeway scenery color differs at face {polygon.index}")
        prop_fbx = os.path.join(os.path.dirname(fbx), "verdant_valley_props.fbx")
        prop_size = [round(prop.dimensions[0], 3), round(prop.dimensions[2], 3),
                     round(prop.dimensions[1], 3)]
        prop_library = bpy.data.collections.new("PropLibrary")
        bpy.context.scene.collection.children.link(prop_library)
        prop_library.objects.link(prop)
        placements = {"VV_OVERGROWN_CAUSEWAY_GATE": [{
            "prop": prop.name,
            "position": [round(centre[0], 3), round(centre[2], 3), round(-centre[1], 3)],
            "rotation": [1, 0, 0, 0, 1, 0, 0, 0, 1],
            "size": prop_size,
        }]}
        export_props(prop_library.objects, placements, prop_fbx,
                     os.path.join(REPO, "src", "shared", "Content", "Props", "VerdantValley.luau"))
        pilot = {"chunk": "VV_OVERGROWN_CAUSEWAY_GATE", "prop": prop.name,
                 "position": [round(centre[0], 3), round(centre[2], 3),
                              round(-centre[1], 3)], "size": prop_size,
                 "terrain_size": next(r["size"] for r in rows if r["name"] == "chunk_overgrown_causeway_gate"),
                 "ground_offset_y": 39.0,
                 "detached_components": detached}
        with open(os.path.join(os.path.dirname(fbx), "causeway_split_report.json"), "w", encoding="utf-8") as stream:
            json.dump(pilot, stream, indent=2)
        print(f"[vv] causeway pilot prop -> {prop_fbx}: {pilot}")
    if split_all:
        prop_library = bpy.data.collections.new("PropLibrary")
        bpy.context.scene.collection.children.link(prop_library)
        for item in all_props:
            for collection in list(item.users_collection):
                collection.objects.unlink(item)
            prop_library.objects.link(item)
        prop_fbx = os.path.join(os.path.dirname(fbx), "verdant_valley_props.fbx")
        candidate = os.path.join(os.path.dirname(fbx), "VerdantValleyPropsCandidate.luau")
        export_props(prop_library.objects, placements, prop_fbx, candidate)
        write_split_chunk_candidate(
            rows, os.path.join(os.path.dirname(fbx), "VerdantValleyChunksCandidate.luau"))
        with open(os.path.join(os.path.dirname(fbx), "split_report.json"), "w", encoding="utf-8") as stream:
            json.dump(split_report, stream, indent=2)
        terrain_collection = bpy.data.collections.new("Terrain")
        bpy.context.scene.collection.children.link(terrain_collection)
        for index, terrain in enumerate(export_objects):
            offset = Vector(((index % 6) * 400 - 1000, 800 - (index // 6) * 400, 0))
            for collection in list(terrain.users_collection):
                collection.objects.unlink(terrain)
            terrain_collection.objects.link(terrain)
            terrain.location = offset
            for item in review_props[terrain.name]:
                item.location += offset
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(
            filepath=os.path.join(HERE, "verdant_valley_separated.blend"), compress=True)
        print(f"[vv] separated {len(export_objects)} terrain meshes and {len(all_props)} props; candidate {candidate}")
    with open(report_path, "w", encoding="utf-8") as stream:
        json.dump(rows, stream, indent=2)
    print(f"[vv] Joined scene OK: {len(rows)} chunks -> {fbx}")


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


def prepare_production_colors(obj):
    """Encode existing face colors on a disposable export mesh only.

    Keep painted corners. Fill an absent layer or entirely zero-color faces
    from their constant material color, as in the legacy build_piece path.
    Mixed painted/zero faces and linked shader inputs are never guessed.
    """
    mesh = obj.data
    attr = mesh.color_attributes.get("Col")
    missing = attr is None
    if missing:
        if mesh.color_attributes:
            raise RuntimeError(f"Unexpected color layers on {obj.name}; review required")
        attr = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    if attr.domain != "CORNER" or attr.data_type != "BYTE_COLOR":
        raise RuntimeError(f"Unsupported Col format on {obj.name}")
    changed_faces = changed_corners = 0
    for polygon in mesh.polygons:
        zeros = sum(max(attr.data[i].color[:3]) == 0 for i in polygon.loop_indices)
        if not missing and zeros == 0:
            continue
        if not missing and zeros != polygon.loop_total:
            raise RuntimeError(f"Mixed painted/zero corners on {obj.name}, face {polygon.index}")
        if polygon.material_index >= len(obj.material_slots):
            raise RuntimeError(f"Missing face material on {obj.name}, face {polygon.index}")
        material = obj.material_slots[polygon.material_index].material
        if material is None:
            raise RuntimeError(f"Empty material slot on {obj.name}, face {polygon.index}")
        if material.use_nodes:
            shaders = [n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
            if len(shaders) != 1 or shaders[0].inputs["Base Color"].is_linked:
                raise RuntimeError(f"Nonconstant face material {material.name} on {obj.name}; review required")
        rgb = material_rgb(material)
        # An authored black material remains black. Other zero-valued faces
        # have no usable paint data and follow their existing face material.
        if missing or max(rgb) > 0:
            for index in polygon.loop_indices:
                attr.data[index].color = (*rgb, 1.0)
                changed_corners += 1
            changed_faces += 1
    mesh.color_attributes.active_color = attr
    mesh.color_attributes.render_color_index = list(mesh.color_attributes).index(attr)
    return {"created_layer": missing, "material_encoded_faces": changed_faces,
            "material_encoded_corners": changed_corners,
            "black_corners_after": sum(max(c.color[:3]) == 0 for c in attr.data)}


def export_production_scene():
    """Staging-only export of disposable copies; never save the source scene."""
    import hashlib
    from pathlib import Path
    from io_scene_fbx import parse_fbx as fbx_parse

    if not bpy.app.background:
        raise RuntimeError("Run production export in background Blender only")
    # libraries.write snapshots retain the source Scene but open with an empty
    # active scene. Select the unique production scene in this disposable process.
    candidates = [s for s in bpy.data.scenes if s.collection.children.get("VV_STRUCTURE")]
    if len(candidates) != 1:
        raise RuntimeError("Expected exactly one production scene")
    bpy.context.window.scene = candidates[0]
    base = Path(FBX_PATH).parent
    out = base.with_name("verdant_valley_staging")
    if "--staging-dir" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--staging-dir") + 1]).resolve()
    if out.parent.resolve() != base.parent.resolve() or "staging" not in out.name or out == base:
        raise RuntimeError("Output must be a sibling staging directory")
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"Refusing to overwrite nonempty staging: {out}")
    roots = ["VV_STRUCTURE", "VV_COLLISION", "VV_PROPS_SOLID", "VV_PROPS_NONSOLID"]
    collections = {n: bpy.data.collections.get(n) for n in roots}
    if any(c is None for c in collections.values()):
        raise RuntimeError("Missing production collection")
    expected = {r[0] for r in EXPECTED.values()}
    expected -= {"chunk_cap_treasure_hollow", "chunk_cap_wardens_clearing"}
    expected |= {"chunk_side_treasure_hollow", "chunk_side_wardens_clearing"}
    structures = {o.name:o for o in collections[roots[0]].all_objects}
    errors = []
    if set(structures) != expected:
        errors.append(f"Structure mismatch: missing {expected-set(structures)}, extra {set(structures)-expected}")
    mapping = {}
    for line in (base / "walk_collision_kit/KIT_COUNTS.md").read_text().splitlines():
        if line.startswith("| chunk_"):
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            mapping[cells[3]] = cells[0]
    mapping.update({"VV_STONE_SENTINELS_COLLISION_MERGED":"chunk_stone_sentinels",
                    "VV_PATH_CLIFF_PASSAGE_COLLISION_MERGED":"chunk_path_cliff_passage"})
    if len(mapping) != 30 or set(mapping.values()) != expected:
        errors.append("Collision mapping does not cover all chunks")
    buckets = {n:{k:[] for k in ("structure", "collision", "solid_props", "nonsolid_props", "wind_canopies", "special")} for n in expected}
    assigned = {}
    for root, collection in collections.items():
        for obj in collection.all_objects:
            if obj in assigned:
                errors.append(f"Duplicate production membership: {obj.name}")
                continue
            if obj.type != "MESH" or not obj.data.polygons:
                errors.append(f"Invalid production mesh: {obj.name}")
            if any(re.search(r"temp|backup|reference", c.name, re.I) for c in obj.users_collection):
                errors.append(f"Nonproduction membership: {obj.name}")
            if root == roots[0]:
                chunk, category = obj.name, "structure"
            elif root == roots[1]:
                matches = [mapping[c.name] for c in collection.children if c.name in mapping and obj.name in c.all_objects]
                chunk, category = (matches[0] if len(matches)==1 else None), "collision"
            else:
                matches = [n for n in expected if obj.name.startswith(n + "__")]
                chunk = matches[0] if len(matches)==1 else None
                suffix = obj.name.split("__",1)[-1]
                category = "solid_props" if root == roots[2] else "nonsolid_props"
                if "canopy" in suffix.lower():
                    category = "wind_canopies"
                elif suffix not in ("PropsSolid", "PropsNonSolid"):
                    category = "special"
            if chunk not in buckets:
                errors.append(f"Unassociated production object: {root}/{obj.name}")
                continue
            assigned[obj] = (chunk,category)
            buckets[chunk][category].append(obj)
    for chunk, categories in buckets.items():
        for category in ("structure", "collision", "solid_props", "nonsolid_props"):
            if not categories[category]:
                errors.append(f"Missing category: {chunk}/{category}")
        for category in ("structure", "solid_props", "nonsolid_props"):
            if len(categories[category]) != 1:
                errors.append(f"Expected one joined mesh: {chunk}/{category}")
    if errors:
        raise RuntimeError("Production preflight failed:\n" + "\n".join(errors))

    def digest(obj):
        h = hashlib.sha256()
        h.update(str([list(r) for r in obj.matrix_world]).encode())
        for v in obj.data.vertices:
            h.update(str(tuple(v.co)).encode())
        for face in obj.data.polygons:
            h.update(str((tuple(face.vertices),face.material_index,face.use_smooth)).encode())
        return h.hexdigest()

    jobs = []
    for chunk, categories in sorted(buckets.items()):
        stem = chunk.removeprefix("chunk_")
        for category, objects in categories.items():
            if not objects:
                continue
            relative = f"{stem}_{category}.fbx"
            if category == "collision":
                relative = f"walk_collision_kit/{stem}_walk_collision.fbx"
                if chunk == "chunk_stone_sentinels":
                    relative = "stone_sentinels_walk_collision_merged.fbx"
                elif chunk == "chunk_path_cliff_passage":
                    relative = "cliff_passage_collision/path_cliff_passage_walk_collision.fbx"
            jobs.append((chunk,category,sorted(objects,key=lambda o:o.name),relative))
    only_chunk = only_categories = None
    if "--only-chunk" in sys.argv:
        only_chunk = sys.argv[sys.argv.index("--only-chunk") + 1]
        if only_chunk not in expected:
            raise RuntimeError(f"Unknown chunk filter: {only_chunk}")
    if "--only-category" in sys.argv:
        only_categories = set(sys.argv[sys.argv.index("--only-category") + 1].split(','))
        if not only_categories <= set(next(iter(buckets.values()))):
            raise RuntimeError(f"Unknown category filter: {only_categories}")
    if only_chunk or only_categories:
        jobs = [j for j in jobs if (not only_chunk or j[0] == only_chunk) and (not only_categories or j[1] in only_categories)]
        if not jobs:
            raise RuntimeError("No exports match requested filters")
    else:
        jobs.append((None,"structure",[structures[n] for n in sorted(expected)],"verdant_valley_structure.fbx"))
        jobs.append((None,"props",sorted([o for o,(_,c) in assigned.items() if c not in ('structure','collision')],key=lambda o:o.name),"verdant_valley_props.fbx"))
    out.mkdir(parents=True,exist_ok=True)
    manifest = {"source_blend":bpy.data.filepath,"source_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
                "status":"exporting","collision_source":"Current VV_COLLISION meshes; no generation",
                "scope":{"only_chunk":only_chunk,"only_categories":sorted(only_categories) if only_categories else None},
                "units":{"system":bpy.context.scene.unit_settings.system,"scale_length":bpy.context.scene.unit_settings.scale_length},
                "coordinate_handling":"Inverse chunk structure matrix on temporary copies; relative pivots retained",
                "excluded_objects":sorted(o.name for o in bpy.context.scene.objects if o not in assigned),
                "chunks":{n:{k:len(v) for k,v in c.items()} for n,c in sorted(buckets.items())},"files":[]}
    before = {o:digest(o) for o in assigned}
    source_scene = bpy.context.window.scene
    export_scene = bpy.data.scenes.new("VV_EXPORT_DISPOSABLE")
    export_scene.unit_settings.system = source_scene.unit_settings.system
    export_scene.unit_settings.scale_length = source_scene.unit_settings.scale_length
    try:
        bpy.context.window.scene = export_scene
        for chunk,category,objects,relative in jobs:
            copies, names, records = [], {}, []
            try:
                for obj in objects:
                    owner = chunk or assigned[obj][0]
                    name = obj.name
                    names[obj] = name
                    obj.name = "EXPORT_SOURCE_" + name
                    copy = obj.copy()
                    # FBX material mapping keys on mesh datablocks. Linked source
                    # instances may have different slot layouts; isolate export
                    # datablocks without changing any source vertex or attribute.
                    copy.data = obj.data.copy()
                    copy.parent = None
                    copy.name = name
                    copy.matrix_world = structures[owner].matrix_world.inverted() @ obj.matrix_world
                    copy.hide_viewport = False
                    copy.hide_render = False
                    export_scene.collection.objects.link(copy)
                    copy.hide_set(False)
                    copies.append(copy)
                    colors = prepare_production_colors(copy) if assigned[obj][1] != 'collision' else None
                    records.append({"name":name,"chunk":owner,"source_collections":[c.name for c in obj.users_collection],"source_digest":before[obj],"matrix_world":[list(r) for r in obj.matrix_world],"export_matrix":[list(r) for r in copy.matrix_world],"vertices":len(obj.data.vertices),"faces":len(obj.data.polygons),"chest_role":obj.get('chest_role'),"materials":[m.name if m else None for m in obj.data.materials],"export_color_preparation":colors})
                destination = out / relative
                destination.parent.mkdir(parents=True,exist_ok=True)
                export_fbx(str(destination),copies)
                if not destination.is_file() or destination.stat().st_size < 100:
                    raise RuntimeError(f"Missing/malformed export: {destination}")
                tree, version = fbx_parse.parse(str(destination))
                entities = next(e for e in tree.elems if e.id == b'Objects')
                exported_names = {e.props[1].split(b'\x00\x01')[0].decode() for e in entities.elems if e.id == b'Model' and e.props[2] == b'Mesh'}
                expected_names = {r['name'] for r in records}
                if exported_names != expected_names:
                    raise RuntimeError(f"FBX object mismatch in {relative}: missing {expected_names-exported_names}, extra {exported_names-expected_names}")
                manifest['files'].append({"chunk":chunk,"category":category,"filename":relative,"destination":str(destination.resolve()),"sources":records,"sha256":hashlib.sha256(destination.read_bytes()).hexdigest()})
                print(f"[vv production] {relative}: {len(copies)} meshes",flush=True)
            finally:
                for copy in copies:
                    mesh = copy.data
                    bpy.data.objects.remove(copy,do_unlink=True)
                    bpy.data.meshes.remove(mesh)
                for obj,name in names.items():
                    obj.name = name
        if any(digest(o)!=h for o,h in before.items()):
            raise RuntimeError("Source invariant failed")
        manifest['source_objects_unchanged'] = True
        manifest['status'] = "exported; Studio validation pending"
    finally:
        bpy.context.window.scene = source_scene
        bpy.data.scenes.remove(export_scene)
        (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    lines = ['# Verdant Valley staging export manifest','','Studio validation pending. Working exports untouched.','','| Chunk | Category | Objects | Full destination |','|---|---|---:|---|']
    for row in manifest['files']:
        lines.append(f"| {row['chunk'] or 'all chunks'} | {row['category']} | {len(row['sources'])} | `{row['destination']}` |")
    (out/'EXPORT_MANIFEST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    exported_objects = {o for _,_,objects,_ in jobs for o in objects}
    print(f"[vv production] COMPLETE: {len(jobs)} FBXs, {len(exported_objects)} exported objects of {len(assigned)} production objects",flush=True)


if "--production-scene" in sys.argv:
    export_production_scene()
elif "--joined-scene" in sys.argv:
    export_joined_scene()
else:
    main()
