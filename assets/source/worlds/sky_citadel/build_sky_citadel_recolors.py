"""Sky Citadel RECOLOURS -- the 36 base pieces in each scenario atmosphere's
palette. Same geometry, same names plus `__<SCENARIO>`: only the baked colours
differ (owner, 2026-09-23: "I'd much rather prefer recolors").

A mesh's colours are baked per face, so a real recolour is a recoloured copy.
The game swaps one in per run: a run that draws the SIEGE atmosphere builds
each chunk from `SC_CHUNK_<X>__SIEGE` when that mesh is uploaded, else the base.

Palettes are the scenario kits' looks (tag sky-citadel-scenarios-v1,
sky_citadel_structures.py), applied to the base pieces as they are.

    blender -b --factory-startup --python build_sky_citadel_recolors.py -- --export
writes assets/export/worlds/sky_citadel/import/SC_RECOLOR_<SCENARIO>.fbx: seven
files of 36 bare meshes (no parent empties -- those tipped every piece over).
"""

import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_PATH = os.path.join(HERE, "build_sky_citadel_kit.py")
K = {"__name__": "sky_citadel_kit", "__file__": KIT_PATH}
exec(open(KIT_PATH, encoding="utf-8").read(), K)

K["PALETTE"].update({
    "Soot": ((40, 38, 48), False), "Char": ((64, 54, 52), False), "Snow": ((244, 248, 255), False),
    "Frost": ((196, 214, 232), False), "FrostDeep": ((150, 172, 198), False), "Ice": ((150, 200, 230), False),
    "AlarmRed": ((255, 70, 80), True), "AlarmDim": ((170, 50, 64), True), "EmberGlow": ((255, 150, 60), True),
    "RaiderRust": ((158, 74, 52), False), "AetherBloom": ((190, 150, 255), True),
    "AetherDim": ((120, 90, 190), True), "Steel": ((104, 112, 126), False), "Gunmetal": ((70, 76, 88), False),
    "Hazard": ((232, 188, 40), False), "Pearl": ((236, 228, 246), False), "Lavender": ((178, 160, 214), False),
    "Weathered": ((178, 176, 162), False), "Lichen": ((136, 148, 112), False), "Scorched": ((128, 118, 112), False),
    "StormStone": ((140, 148, 164), False), "StormSlate": ((84, 92, 110), False), "Plating": ((150, 156, 168), False),
    "Moss": ((70, 112, 66), False), "MossLight": ((118, 160, 86), False),
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())

# scenario -> (colour map, floor colour, which old floor colours the floor rule repaints, tops colour)
LOOKS = {
    "UNMOORING": ({"AzureDim": "DeepAlloy", "CitadelViolet": "StormSlate"}, None, None, None),
    "SIEGE": ({"CitadelViolet": "RaiderRust", "AzureDim": "Char", "AzureNeon": "EmberGlow"},
              "Scorched", ("CitadelWhite", "PaleAlloy"), None),
    "LOCKDOWN": ({"CitadelWhite": "Gunmetal", "PaleAlloy": "Steel", "CitadelViolet": "Gunmetal", "SunGold": "Hazard",
                  "AzureNeon": "AlarmRed", "AzureDim": "AlarmDim", "Verdure": "Gunmetal"}, "Plating", ("Gunmetal",),
                 None),
    "STORMHAWK": ({"CitadelWhite": "StormStone", "PaleAlloy": "StormSlate", "CitadelViolet": "DeepAlloy"},
                  "StormSlate", ("StormStone",), None),
    "RIME": ({"CitadelWhite": "Frost", "PaleAlloy": "FrostDeep", "Verdure": "Snow", "AzureDim": "Ice",
              "SkyGlass": "Ice", "CitadelViolet": "Snow"}, "Snow", ("Frost",), "Snow"),
    "RECLAIMED": ({"CitadelWhite": "Weathered", "PaleAlloy": "Lichen", "CitadelViolet": "HullSlate",
                   "AzureNeon": "DeepAlloy", "AzureDim": "HullSlate", "SunGold": "Lichen"}, "Lichen", None, None),
    "AETHER_SURGE": ({"CitadelWhite": "Pearl", "PaleAlloy": "Lavender", "AzureNeon": "AetherBloom",
                      "AzureDim": "AetherDim", "DeepAlloy": "HullSlate"}, "Pearl", None, None),
}
EXPORT_DIR = os.path.join(K["REPO"], "assets", "export", "worlds", "sky_citadel", "import")


def normal_z(p, f):
    a, b, c = p.verts[f[0]], p.verts[f[1]], p.verts[f[2]]
    n = (b - a).cross(c - a)
    return n.z / n.length if n.length > 1e-9 else 0.0


def recolour(p, look):
    mapping, floor, only, tops = look
    out = []
    for fi, f in enumerate(p.faces):
        m = p.fmat[fi]
        new = mapping.get(m, m)
        up = normal_z(p, f) > 0.9
        if up and floor:
            zc = sum(p.verts[i].z for i in f) / len(f)
            xs, ys = [p.verts[i].x for i in f], [p.verts[i].y for i in f]
            if -0.2 < zc < 6.5 and (max(xs) - min(xs)) * (max(ys) - min(ys)) >= 300 and (only is None or new in only):
                new = floor
        if up and tops and new != "Ice":
            zc = sum(p.verts[i].z for i in f) / len(f)
            if zc > 0.4:
                new = tops
        out.append(new)
    return out


def main(export=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pieces = [b() for b in K["BUILDERS"]]
    mats = K["ensure_materials"]()
    groups = []
    for scen, look in LOOKS.items():
        coll = bpy.data.collections.new("Recolor_" + scen)
        bpy.context.scene.collection.children.link(coll)
        objs = []
        for i, p in enumerate(pieces):
            q = K["Piece"]("%s__%s" % (p.name, scen.lower()), p.notes)
            q.verts, q.faces, q.fmat = p.verts, p.faces, recolour(p, look)
            q.up = p.up
            o = K["to_object"](q, mats, coll)
            o.location = (i * 300.0, -600.0 * len(groups), 0)
            objs.append(o)
        groups.append((scen.title().replace("_", ""), objs))
        print("RECOLOR", scen, len(objs))
    if export:
        # ONE FILE PER SCENARIO, meshes only, exactly as the base kit exports.
        # The first export parented the meshes under empties; the FBX axis
        # conversion then turned every piece 90 degrees on its side in Roblox.
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for f in os.listdir(EXPORT_DIR):
            if f.startswith("SkyCitadel_Recolors"):
                os.remove(os.path.join(EXPORT_DIR, f))
        for (gname, objs), scen in zip(groups, LOOKS):
            path = os.path.join(EXPORT_DIR, "SC_RECOLOR_%s.fbx" % scen)
            K["_export_selected"](objs, path)
            v = K["verify_exports"]([path])[0]
            wrong = [k for k, s in v["sizes"].items() if any(abs(c - 256) > 0.01 for c in s)]
            print("EXPORTED", v["file"], v["meshes"], "not 256^3:", wrong[:3])

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(export="--export" in argv)
