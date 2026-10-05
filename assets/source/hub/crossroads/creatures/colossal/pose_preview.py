"""Pose-preview harness for the colossal rigs (contract SKY_ECOSYSTEM_CONTRACT.md 4.1 / 6.5).

Applies the SAME maths as the game client (src/client/Controllers/SkyTraffic.luau, `place`):

    hingeAbout(hinge, axis, angle) = T(hinge) * R(axis, angle) * T(-hinge)
    Flap  : angle = sin(clock * rate * 2pi + phase + lag) * amp * gate
    Spin  : angle = t * rate + phase
    Pulse : uniform scale (1 + amp * wave * gate) about the PART (its bbox centre; Size scales about the CFrame)
    acc   = chain.acc * hinge (chained) or hinge;   part CFrame = body * acc * T(offset)

in the sidecar's OrbiterParts frame, i.e. it reads hinge/axis/offset/amp/rate/phase/chain/lag/gait from the EXPORTED
creatures_colossal.json (so it proves the data the owner will import), converts the build's meshes into that frame,
poses them, and renders them back in Blender space.

    python tools/run_blender.py -b --factory-startup --python pose_preview.py -- [--sheets] [--extents] [--attach]

Outputs (scratch, or renders/ with --final): pose_<id>_<view>.jpg contact sheets, pose_starweaver_burst.jpg.
"""

import json
import math
import os
import random
import runpy
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
_saved = list(sys.argv)
BC = runpy.run_path(os.path.join(HERE, "build_colossal.py"), run_name="cc")
sys.argv = _saved
K = BC["K"]

S = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))      # Blender -> OrbiterParts frame
SI = S.inverted()


def T(v):
    return Matrix.Translation(Vector(v))


def hinge_about(h, ax, ang):
    ax = Vector(ax)
    if ax.length < 1e-3:
        ax = Vector((1, 0, 0))
    return T(h) @ Matrix.Rotation(ang, 4, ax.normalized()) @ T(-Vector(h))


def build_all():
    creatures = [BC["build_starweaver"](), BC["build_turtle"]()]
    for c in creatures:
        BC["finalize"](c)
    return creatures


class Rig:
    def __init__(self, c, entry, objs):
        self.id = c.id
        self.parts = {}
        self.objs = {}
        self.body = objs[0]
        for (q, _m), o in zip(c.parts, objs[1:]):
            P = entry["parts"][q.name]
            self.parts[q.name] = P
            self.objs[q.name] = o
        self.verts = {c.body.name: [Vector(v) for v in c.body.verts]}
        for q, _m in c.parts:
            self.verts[q.name] = [Vector(v) for v in q.verts]
        self.body_name = c.body.name

    def pose(self, t, fclock, gates=None, bank=0.0, angle_override=None, pulse_override=None):
        """-> {part: obj matrix in Blender space}. gates: gait -> 0..1 (Flight default 1)."""
        gates = gates or {}
        accs, out = {}, {}
        for name, P in self.parts.items():
            g = P["gait"]
            gate = gates.get(g, 1.0)
            clock = fclock if g == "Flight" else t
            wave = math.sin(clock * P["rate"] * math.pi * 2 + P["phase"] + P.get("lag", 0.0))
            hinge = Matrix.Identity(4)
            scale = 1.0
            if P["kind"] == "Spin":
                hinge = hinge_about(P["hinge"], P["axis"], t * P["rate"] + P["phase"])
            elif P["kind"] == "Flap":
                ang = bank * P["amp"] if g == "Turn" else wave * P["amp"] * gate
                if angle_override is not None:
                    ang = angle_override.get(name, ang)
                hinge = hinge_about(P["hinge"], P["axis"], ang)
            elif P["kind"] == "Pulse":
                w = wave if pulse_override is None else pulse_override.get(name, wave)
                scale = 1.0 + P["amp"] * w * gate
            acc = accs[P["chain"]] @ hinge if P["chain"] else hinge
            accs[name] = acc
            off = Vector(P["offset"])
            cb = SI @ off
            Sc = Matrix.Diagonal((scale, scale, scale, 1.0))
            out[name] = SI @ acc @ T(off) @ Sc @ S @ T(-cb)
        return out

    def apply(self, mats):
        self.body.matrix_world = Matrix.Identity(4)
        for n, m in mats.items():
            self.objs[n].matrix_world = m


# ----------------------------------------------------------------------------------------------------------------
# numeric checks
# ----------------------------------------------------------------------------------------------------------------
def extents(rig, n_random=900, seed=7):
    """Union bbox and bounding-sphere radius (about the body centre) over the full range of motion: every Flap at
    +-amp (random sign vectors + all-zero + all-max), Pulse at +-amp, Spin sampled round."""
    import numpy as np
    rnd = random.Random(seed)
    arrs = {n: np.array([[v.x, v.y, v.z, 1.0] for v in vs]) for n, vs in rig.verts.items()}
    lo = np.full(3, 1e9)
    hi = np.full(3, -1e9)
    rmax = 0.0
    flaps = [n for n, P in rig.parts.items() if P["kind"] == "Flap"]
    pulses = [n for n, P in rig.parts.items() if P["kind"] == "Pulse"]

    def eat(mats):
        nonlocal lo, hi, rmax
        for n, a in arrs.items():
            m = mats.get(n)
            w = a @ np.array(m).T if m is not None else a
            lo = np.minimum(lo, w[:, :3].min(0))
            hi = np.maximum(hi, w[:, :3].max(0))
            rmax = max(rmax, float(np.sqrt((w[:, :3] ** 2).sum(1)).max()))
    for i in range(n_random + 3):
        if i == 0:
            ov = {n: 0.0 for n in flaps}
            pv = {n: 0.0 for n in pulses}
        elif i == 1:
            ov = {n: rig.parts[n]["amp"] for n in flaps}
            pv = {n: 1.0 for n in pulses}
        elif i == 2:
            ov = {n: -rig.parts[n]["amp"] for n in flaps}
            pv = {n: -1.0 for n in pulses}
        else:
            ov = {n: rnd.choice((-1, 1)) * rig.parts[n]["amp"] for n in flaps}
            pv = {n: rnd.choice((-1.0, 1.0)) for n in pulses}
        mats = rig.pose(rnd.uniform(0, 80), 0.0, angle_override=ov, pulse_override=pv)
        eat(mats)
    return lo, hi, rmax


def attach_report(rig):
    """At rest: distance from each chained/hinged part's hinge to the nearest vertex of the part itself and of what it
    hangs on (its chain parent, else the body). A hinge that sits off its joint shows as a large number."""
    out = []
    for n, P in rig.parts.items():
        if P["kind"] != "Flap":
            continue
        h = SI @ Vector(P["hinge"])
        dself = min((v - h).length for v in rig.verts[n])
        par = P["chain"] or rig.body_name
        dpar = min((v - h).length for v in rig.verts[par])
        out.append((n.split("__")[1], round(dself, 1), par.split("__")[-1], round(dpar, 1)))
    return out


# ----------------------------------------------------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------------------------------------------------
def frame_box(rig, lo, hi):
    cen = (Vector(lo) + Vector(hi)) * 0.5
    return cen, max(Vector(hi) - Vector(lo))


def render_set(rig, creature_objs, tiles, view, cen, size, out, tag, lens=35, dist=1.9):
    paths = []
    d = Vector(view).normalized() * size * dist
    for k, (mats, label) in enumerate(tiles):
        rig.apply(mats)
        paths.append(BC["_shot"](f"{tag}_{k}", cen + d, cen, out, lens=lens))
    return paths


def main(argv):
    creatures = build_all()
    sidecar_mem = BC["build_sidecar"](creatures)
    disk = os.path.join(BC["EXPORT_DIR"], "creatures_colossal.json")
    sidecar = json.load(open(disk, encoding="utf-8")) if os.path.exists(disk) else sidecar_mem
    if sidecar != json.loads(json.dumps(sidecar_mem)):
        print("WARNING: exported JSON differs from the in-memory build (re-run build_colossal.py --export)")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = BC["to_objects"](creatures)
    rigs = {c.id: Rig(c, sidecar["creatures"][c.id], objs[c.id]) for c in creatures}
    final = "--final" in argv
    out = BC["RENDER_DIR"] if final else BC["SCRATCH"]
    os.makedirs(out, exist_ok=True)

    if "--attach" in argv or "--extents" in argv:
        for cid, rig in rigs.items():
            if "--attach" in argv:
                print(f"ATTACH {cid} (part, d_self, parent, d_parent) at rest")
                for r in attach_report(rig):
                    print("   ", r)
            if "--extents" in argv:
                lo, hi, rmax = extents(rig)
                ex = [round(float(hi[i] - lo[i]), 1) for i in range(3)]
                print(f"EXTENTS {cid}: swept bbox (Blender x,y,z) {ex}  lo {[round(float(v),1) for v in lo]} "
                      f"hi {[round(float(v),1) for v in hi]}  sphere radius about body centre {rmax:.1f}")

    if "--sheets" in argv:
        BC["_scene_setup"]()
        scene = bpy.context.scene
        scene.render.resolution_x, scene.render.resolution_y = 640, 400
        times = [0.0, 1.8, 3.6, 5.4, 7.2, 9.0]
        for cid, rig in rigs.items():
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o not in objs[cid]
            lo, hi, _r = extents(rig, n_random=120)
            cen, size = frame_box(rig, lo, hi)
            views = {"starweaver": [("side", (0.0, -1.0, 0.05)), ("3q", (0.8, -1.0, 0.3)), ("below", (0.5, -0.9, -0.55))],
                     "elder_greatturtle": [("front", (1.0, -0.15, 0.2)), ("3q", (0.8, -1.0, 0.35)),
                                           ("top", (0.2, -0.45, 1.0))]}[cid]
            for vname, vdir in views:
                tiles = [(rig.pose(t, t), f"t={t}") for t in times]
                paths = render_set(rig, objs[cid], tiles, vdir, cen, size, out, f"pose_{cid}_{vname}")
                BC["_sheet"](paths, 3, os.path.join(out, f"pose_{cid}_{vname}.jpg"))
                print("SHEET", os.path.join(out, f"pose_{cid}_{vname}.jpg"))
            if cid == "starweaver":
                # an acceleration burst: Flight gait at full gate; the bell at expanded / mid / contracted / mid
                sk = rig.parts["hubprop_starweaver__skirt_1"]
                tiles = []
                for k in range(4):
                    fc = (0.25 + 0.25 * k) / sk["rate"] - sk["phase"] / (2 * math.pi * sk["rate"])
                    tiles.append((rig.pose(3.0, fc, gates={"Flight": 1.0}), f"burst {k}"))
                for vname, vdir in (("side", (0.0, -1.0, 0.05)), ("below", (0.5, -0.9, -0.55))):
                    paths = render_set(rig, objs[cid], tiles, vdir, cen, size, out, f"burst_{vname}")
                    BC["_sheet"](paths, 2, os.path.join(out, f"pose_starweaver_burst_{vname}.jpg"))
                    print("SHEET", os.path.join(out, f"pose_starweaver_burst_{vname}.jpg"))

    if "--extreme" in argv:
        BC["_scene_setup"]()
        scene = bpy.context.scene
        scene.render.resolution_x, scene.render.resolution_y = 800, 500
        for cid, rig in rigs.items():
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o not in objs[cid]
            flaps = [n for n, P in rig.parts.items() if P["kind"] == "Flap"]
            pulses = [n for n, P in rig.parts.items() if P["kind"] == "Pulse"]
            rnd = random.Random(3)
            tiles = []
            for sg in (1, -1):
                tiles.append((rig.pose(0, 0, angle_override={n: sg * rig.parts[n]["amp"] for n in flaps},
                                       pulse_override={n: float(sg) for n in pulses}), f"all {sg}"))
            for _ in range(2):
                tiles.append((rig.pose(0, 0, angle_override={n: rnd.choice((-1, 1)) * rig.parts[n]["amp"] for n in flaps},
                                       pulse_override={n: rnd.choice((-1.0, 1.0)) for n in pulses}), "rnd"))
            lo, hi, _r = extents(rig, n_random=60)
            cen, size = frame_box(rig, lo, hi)
            for vname, vdir in (("3q", (0.8, -1.0, 0.35)), ("rear", (-0.8, -1.0, 0.25))):
                paths = render_set(rig, objs[cid], tiles, vdir, cen, size, out, f"ext_{cid}_{vname}", dist=1.25)
                BC["_sheet"](paths, 2, os.path.join(out, f"pose_{cid}_extreme_{vname}.jpg"))
                print("SHEET", os.path.join(out, f"pose_{cid}_extreme_{vname}.jpg"))
    print("PREVIEW DONE")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
