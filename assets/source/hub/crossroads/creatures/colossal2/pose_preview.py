"""Pose-preview harness: applies the SAME maths as the game client SkyTraffic to the colossal2 rig data.

    hingeAbout(h, axis, a) = T(h) * R(axis, a) * T(-h)
    part CFrame            = body * acc * T(offset)      acc = chain.acc * hinge   (chained)
    Flap angle             = sin(clock*rate*2pi + phase_eff) * amp ; phase_eff = parent phase_eff - lag
    Spin angle             = clock*rate + phase_eff ; Pulse = uniform scale 1 + amp*wave about the part centre

The rig is read back from the SIDECAR dict (offset/hinge/axis in the orbiter frame), the meshes from the build, so the
exported numbers themselves are what gets proven. Gates are 1 (full amplitude).

    python tools/run_blender.py -b --factory-startup --python pose_preview.py -- [--final]
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_colossal2 as B   # noqa: E402

K = B.K


def S(v):
    return Vector((-v.x, v.z, v.y))


def hinge_about(h, axis, a):
    return Matrix.Translation(h) @ Matrix.Rotation(a, 4, axis) @ Matrix.Translation(-h)


def pose(c, entry, clock):
    """Return {part name: (world matrix list verts in orbiter frame)} plus hinge world points."""
    bc = (B.bbox(c.body)[0] + B.bbox(c.body)[1]) * 0.5
    parts = entry["parts"]
    objs = {q.name: q for q, _m in c.parts}
    eff, acc, out, hpt = {}, {}, {}, {}

    def resolve(name):
        if name in acc:
            return
        d = parts[name]
        up = d["chain"]
        if up:
            resolve(up)
            eff[name] = eff[up] - d["lag"] + 0.0
            # runtime: sub.Phase = up.Phase - sub.Lag ; own SubPhase only for unchained parts
        else:
            eff[name] = d["phase"]
        if up and d["phase"]:
            eff[name] = eff[up] - d["lag"]
        wave = math.sin(clock * d["rate"] * 2 * math.pi + eff[name])
        h = Vector(d["hinge"])
        ax = Vector(d["axis"])
        hm = Matrix.Identity(4)
        scale = 1.0
        if d["kind"] == "Spin":
            hm = hinge_about(h, ax, clock * d["rate"] + eff[name])
        elif d["kind"] == "Flap":
            hm = hinge_about(h, ax, wave * d["amp"])
        elif d["kind"] == "Pulse":
            scale = 1 + d["amp"] * wave
        a = acc[up] @ hm if up else hm
        acc[name] = a
        hpt[name] = (acc[up] if up else Matrix.Identity(4)) @ h
        q = objs[name]
        lo, hi = B.bbox(q)
        qc = S((lo + hi) * 0.5)
        off = Vector(d["offset"])
        # Roblox: part centre at `offset`, mesh vertices relative to the centre (pulse scales them)
        out[name] = [a @ (off + (S(v) - qc) * scale) for v in q.verts]
    for n in parts:
        resolve(n)
    body = [S(v - bc) for v in c.body.verts]
    return body, out, hpt


def to_blender_piece(name, verts_orb, src):
    p = K["Piece"](name, "pose")
    p.verts = [S(v) for v in verts_orb]
    p.faces = [list(f) for f in src.faces]
    p.fmat = list(src.fmat)
    p.ftag = list(src.ftag)
    return p


def gap_report(c, entry, clock_list):
    """Largest closest-vertex distance between a chained part and its parent, per phase, vs the neutral pose."""
    worst = 0.0
    base = {}
    for ci, clock in enumerate([None] + clock_list):
        body, out, hpt = pose(c, entry, 0.0 if clock is None else clock) if clock is not None else pose_neutral(c, entry)
        for q, m in c.parts:
            up = m["chain"]
            ref = out[up] if up else body
            kd = KDTree(len(ref))
            for i, v in enumerate(ref):
                kd.insert(v, i)
            kd.balance()
            hw = hpt[q.name]
            d = kd.find(hw)[2]
            if clock is None:
                base[q.name] = d
            else:
                worst = max(worst, d - base[q.name])
    return worst


def pose_neutral(c, entry):
    saved = {n: (d["amp"], d["lag"]) for n, d in entry["parts"].items()}
    for d in entry["parts"].values():
        d["amp"] = 0.0
    r = pose(c, entry, 0.0)
    for n, d in entry["parts"].items():
        d["amp"] = saved[n][0]
    return r


def main(argv):
    creatures = B.build_all()
    sidecar = B.build_sidecar(creatures)
    final = "--final" in argv
    out_dir = B.RENDER_DIR if final else B.SCRATCH
    os.makedirs(out_dir, exist_ok=True)
    periods = {"cinder_wyrm": 1 / 0.075, "aether_nautilus": 1 / 0.10}
    cams = {"cinder_wyrm": [((0.0, -1.0, 0.05), 1.05)], "aether_nautilus": [((-0.15, -1.0, 0.1), 1.35)]}
    for c in creatures:
        entry = sidecar["creatures"][c.id]
        T = periods[c.id]
        clocks = [T * k / 6 for k in range(6)]
        print("GAP", c.id, "max extra closest-vertex distance chained part->parent over 12 phases:",
              round(gap_report(c, entry, [T * k / 12 for k in range(12)]), 2))
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mats = K["ensure_materials"]()
        B.C1["_scene_setup"]()
        tiles = []
        for ti, clock in enumerate(clocks):
            body, out, _h = pose(c, entry, clock)
            coll = bpy.data.collections.new(f"pose{ti}")
            bpy.context.scene.collection.children.link(coll)
            objs = [K["to_object"](to_blender_piece(c.body.name + f"_p{ti}", body, c.body), mats, coll)]
            # body verts are orbiter-frame already: to_blender_piece applies S again to get back to Blender
            for q, _m in c.parts:
                objs.append(K["to_object"](to_blender_piece(q.name + f"_p{ti}", out[q.name], q), mats, coll))
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o not in objs
            lo = Vector((1e9,) * 3)
            hi = Vector((-1e9,) * 3)
            for o in objs:
                for cn in o.bound_box:
                    for i in range(3):
                        lo[i] = min(lo[i], cn[i])
                        hi[i] = max(hi[i], cn[i])
            if ti == 0:
                cen = (lo + hi) * 0.5
                dim = max(hi - lo)
            dv, k = cams[c.id][0]
            bpy.context.scene.render.resolution_x = 1000
            bpy.context.scene.render.resolution_y = 380 if c.id == "cinder_wyrm" else 600
            tiles.append(B.C1["_shot"](f"{c.id}_pose{ti}", cen + Vector(dv).normalized() * dim * k, cen, out_dir,
                                       lens=35))
            for o in objs:
                bpy.data.objects.remove(o)
        cols = 1 if c.id == "cinder_wyrm" else 3
        B.C1["_sheet"](tiles, cols, os.path.join(out_dir, f"{c.id}_pose_sheet.jpg"))
        print("POSESHEET", os.path.join(out_dir, f"{c.id}_pose_sheet.jpg"))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
