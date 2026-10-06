"""Starweaver tendril before/after sheet (round 3): worst-case chain poses, old amps vs new calmer amps + limits.

    python tools/run_blender.py -b --factory-startup --python tendril_compare.py -- [--final]
Row 1 = round 2 data (amps .17/.26/.36, no limit); row 2 = round 3 (amps .09/.13/.18, clamped to `limit`).
Columns = every link at +max, at -max, and the alternating (+,-,+) combination, seen from the side.
"""
import copy
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pose_preview as PP   # noqa: E402

BC = PP.BC
OLD = {"tendril": 0.17, "tendriltip": 0.26, "tendriltail": 0.36}


def main(argv):
    creatures = PP.build_all()
    sc = json.load(open(os.path.join(BC["EXPORT_DIR"], "creatures_colossal.json"), encoding="utf-8"))
    c = [x for x in creatures if x.id == "starweaver"][0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = BC["to_objects"](creatures)
    rig = PP.Rig(c, sc["creatures"]["starweaver"], objs["starweaver"])
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in objs["starweaver"]
    out = BC["RENDER_DIR"] if "--final" in argv else BC["SCRATCH"]
    os.makedirs(out, exist_ok=True)
    BC["_scene_setup"]()
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 520, 520
    links = [n for n in rig.parts if "__tendril" in n]

    def angles(new, pattern):
        res = {}
        for n in links:
            base = n.split("__")[1].rsplit("_", 1)[0]
            sgn = pattern(n, base)
            a = sgn * (rig.parts[n]["amp"] if new else OLD[base])
            if new:
                lo, hi = rig.parts[n].get("limit", (-9, 9))
                a = max(lo, min(hi, a))
            res[n] = a
        return res

    pats = [lambda n, b: 1, lambda n, b: -1, lambda n, b: (1, -1, 1)[("tendril", "tendriltip", "tendriltail").index(b)]]
    cen = Vector((0, 0, -150))
    paths = []
    for new in (False, True):
        for pat in pats:
            rig.apply(rig.pose(0, 0, angle_override=angles(new, pat)))
            paths.append(BC["_shot"]("tend_%d_%d" % (new, len(paths)), cen + Vector((0.0, -1.0, 0.12)).normalized() * 1500, cen, out, lens=35))
    sheet = os.path.join(out, "starweaver_tendrils_before_after.jpg")
    BC["_sheet"](paths, 3, sheet)
    print("SHEET", sheet)


main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
