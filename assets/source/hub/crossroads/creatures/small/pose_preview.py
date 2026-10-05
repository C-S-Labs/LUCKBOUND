"""Pose preview for the SMALL group: poses every part with the SAME maths as the game client.

    python tools/run_blender.py -b --factory-startup --python pose_preview.py -- [ids] [--phases 4]

SkyTraffic: hingeAbout(h, axis, a) = T(h) * R(axis, a) * T(-h); acc = chain.acc * hinge;
part CFrame = body * acc * T(offset). The sidecar is in Blender axes and the game frame is the
orbiter frame (-x, z, y) (tools/gen_sky_creatures.py to_orbiter), so the maths runs in the orbiter
frame and the result is mapped back with Q^-1 * acc * Q to pose the Blender meshes.
Flap angle = sin(clock*rate*2pi + phase) * amp (Flight/Idle/Always at gate 1; Turn uses bank).
A chained part's phase = parent.phase - lag. Pulse = uniform scale about the part centre.
Sheets: renders/pose_<id>.jpg, rows = beat phases, columns = front, side, top.
"""
import json
import math
import os
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ns = runpy.run_path(os.path.join(HERE, "build_small.py"), run_name="lib")
bpy.ops.wm.read_factory_settings(use_empty=True)

Q = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # blender -> orbiter
QI = Q.inverted()


def to_o(v):
    return Vector((-v[0], v[2], v[1]))


def hinge_about(h, axis, ang):
    if axis.length < 1e-3:
        axis = Vector((1, 0, 0))
    return Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis.normalized()) @ Matrix.Translation(-h)


def pose(parts, clock, bank=0.0):
    """Returns {part: (acc_o matrix, pulse scale)} in the orbiter frame."""
    phase, acc, out = {}, {}, {}

    def ph(n):
        if n in phase:
            return phase[n]
        p = parts[n]
        v = p["phase"]
        if p.get("chain"):
            v = ph(p["chain"]) - p.get("lag", 0)
        phase[n] = v
        return v

    def get(n):
        if n in acc:
            return acc[n]
        p = parts[n]
        wave = math.sin(clock * p["rate"] * 2 * math.pi + ph(n))
        h, ax = to_o(p["hinge"]), to_o(p["axis"])
        m, sc = Matrix.Identity(4), 1.0
        if p["kind"] == "Flap":
            ang = bank * p["amp"] if p.get("gait") == "Turn" else wave * p["amp"]
            m = hinge_about(h, ax, ang)
        elif p["kind"] == "Spin":
            m = hinge_about(h, ax, clock * p["rate"] + ph(n))
        elif p["kind"] == "Pulse":
            sc = 1 + p["amp"] * wave
        a = get(p["chain"]) @ m if p.get("chain") else m
        acc[n] = a
        out[n] = (a, sc)
        return a

    for n in parts:
        get(n)
    return out


def apply(objs_by_name, parts, clock, bank=0.0):
    pz = pose(parts, clock, bank)
    for n, (a, sc) in pz.items():
        o = objs_by_name[n]
        m = QI @ a @ Q
        if sc != 1.0:
            c = Vector(parts[n]["offset"])
            m = m @ Matrix.Translation(c) @ Matrix.Scale(sc, 4) @ Matrix.Translation(-c)
        o.matrix_world = m


def main():
    objs, side, by_creature = ns["build_all"]()
    ids = [a for a in ARGV if a in side["creatures"]] or list(side["creatures"])
    nph = 4
    if "--phases" in ARGV:
        nph = int(ARGV[ARGV.index("--phases") + 1])
    rr = runpy.run_path(os.path.join(ns["HUB_DIR"], "render_crossroads.py"), run_name="rr")
    rr["setup_world"]()
    bpy.data.worlds["Hub_Sky"].node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.36, 0.62, 1)
    sc = bpy.context.scene
    cw, ch = 420, 300
    sc.render.resolution_x, sc.render.resolution_y = cw, ch
    scratch = ns["SCRATCH"]
    os.makedirs(scratch, exist_ok=True)
    os.makedirs(ns["RENDER_DIR"], exist_ok=True)
    import numpy as np
    for cid in ids:
        group, size, total = by_creature[cid]
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.hide_render = o not in group
        parts = side["creatures"][cid]["parts"]
        by_name = {o.name: o for o in group}
        L = max(size)
        apply(by_name, parts, 0.0)                    # rest pose: frame the whole creature
        pts = [o.matrix_world @ v.co for o in group for v in o.data.vertices]
        ctr = Vector([(min(q[i] for q in pts) + max(q[i] for q in pts)) / 2 for i in range(3)])
        rows = []
        rate = max(p["rate"] for p in parts.values() if p["kind"] == "Flap" and p["gait"] == "Flight")
        for k in range(nph + 1):
            # beat phase k/nph of the fastest Flight part's cycle; the last row is a hard bank (Turn parts)
            apply(by_name, parts, (min(k, nph - 1) / nph) / rate, bank=1.0 if k == nph else 0.0)
            cells = []
            for vn, off, ortho in (("front", (1, 0, 0.05), L * 1.4), ("side", (0.0, -1, 0.15), L * 1.4),
                                   ("top", (0, 0.001, 1), L * 1.4)):
                d = Vector(off).normalized()
                rr["shot"](f"p_{cid}_{k}_{vn}", ctr + d * L * 3, ctr, 50, scratch, ortho=ortho)
                cells.append(os.path.join(scratch, f"p_{cid}_{k}_{vn}.jpg"))
            rows.append(cells)
        sheet = np.ones((ch * (nph + 1), cw * 3, 4), dtype=np.float32)
        for ri, cells in enumerate(rows):
            for ci, path in enumerate(cells):
                im = bpy.data.images.load(path)
                a = np.empty(im.size[0] * im.size[1] * 4, dtype=np.float32)
                im.pixels.foreach_get(a)
                a = a.reshape(im.size[1], im.size[0], 4)
                y0 = (nph - ri) * ch
                sheet[y0:y0 + ch, ci * cw:(ci + 1) * cw] = a
        out = bpy.data.images.new("sheet_" + cid, cw * 3, ch * (nph + 1))
        out.pixels.foreach_set(sheet.ravel())
        out.filepath_raw = os.path.join(ns["RENDER_DIR"], f"pose_{cid}.jpg")
        out.file_format = "JPEG"
        out.save()
        print("POSESHEET", out.filepath_raw)
        apply(by_name, parts, 0.0)


main()
