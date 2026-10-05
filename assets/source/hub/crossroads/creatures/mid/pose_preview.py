"""POSE PREVIEW HARNESS for the Crossroads V2 sky creatures (reusable by every creature group).

Loads an exported creature FBX + its sidecar JSON and poses every part with the SAME maths as the game
(src/client/Controllers/SkyTraffic.luau, the sub-part block of `place`):

    hingeAbout(hinge, axis, angle) = T(hinge) * R(axis, angle) * T(-hinge)         (OrbiterParts frame)
    acc  = chain.acc * hingeAbout(...)   for a chained part, else hingeAbout(...)
    part CFrame = body * acc * T(offset)          (mesh centred on its own origin; body is the identity here)
    Flap angle  = sin(clock * rate * 2pi + phase) * amp * gate     (gate: Flight=FlapAmp, Idle=Idle, Always=1)
                  Turn gait:  BankNorm * amp                       (no wave)
    chained part phase = parent.phase - lag                        (SkyTraffic depthOf: a child's own phase is ignored)
    Flight clock = GaitClock/2pi (here: seconds of an ideal steady beat); everything else runs on real time
    Pulse  = scale (1 + amp * wave * gate) about the part's own centre (Part.Size scales about the part CFrame)
    Spin   = rotation t*rate + phase about the hinge

The sidecar frame is the OrbiterParts frame, g = (-bx, bz, by) of Blender coordinates relative to the body bbox
centre (a proper rotation, so angles keep their sign). Poses are computed in that game frame and mapped back
to Blender only to draw them.

Usage (always through the shared launcher):
    python tools/run_blender.py -b --factory-startup --python <abs>/pose_preview.py -- \
        --fbx <abs>.fbx --json <abs>.json --ids citadel_falcon,canopy_drake --out <abs dir> [options]
Options:
    --poses beat:6,glide,turn,idle,rest   (default). beat:N = N phases of one Flight beat; turn = bank +1;
                                          turn- = bank -1; glide = flight gate 0; idle = Idle gate 1
    --views front,side,top                columns of the sheet (orthographic)
    --res 280x280                         per-cell size
    --tag name                            file name prefix (default: the id)
    --no-render                           numeric report only
    --ref-hz H                            beat reference rate (default: rate of the first Flight Flap part)
    --join PART                           ALSO write <tag><id>_join.png: close-ups (top, front) of the named part's
                                          hinge (suffix match, e.g. `fin_1`) at each pose, to inspect a joint
Outputs <out>/<tag><id>_posesheet.png (rows = poses top to bottom in the order given, columns = views) and a
text attach report on stdout: for every chained part / body-mounted part, the fraction of its ROOT vertices
(within a radius of the hinge) that stay inside, or within 0.5 studs of, its hinge parent at every pose.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


# ----------------------------------------------------------------------------- frames
# game = (-bx, bz, by)  ->  blender = (-gx, gz, gy)
M_G = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # blender -> game
M_B = M_G.inverted()                                                      # game -> blender


def hinge_about(hinge, axis, angle):
    axis = Vector(axis)
    if axis.length < 1e-3:
        axis = Vector((1, 0, 0))
    return Matrix.Translation(hinge) @ Matrix.Rotation(angle, 4, axis.normalized()) @ Matrix.Translation(-Vector(hinge))


# ----------------------------------------------------------------------------- loading
def load_creature(fbx, data, cid):
    """Import the FBX once; return {name: {obj, verts(game frame), offset, ...}} for creature `cid`."""
    spec = data["creatures"][cid]
    names = [spec["model"]] + list(spec["parts"].keys())
    parts = {}
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None or o.type != "MESH":
            raise RuntimeError(f"{n} missing from the FBX")
        me = o.data
        me.transform(o.matrix_world)           # bake the importer's transform: mesh now in the Blender frame
        o.matrix_world = Matrix.Identity(4)
        o.parent = None
        parts[n] = {"obj": o, "base": [v.co.copy() for v in me.vertices],
                    "polys": [tuple(p.vertices) for p in me.polygons]}
    body = parts[spec["model"]]
    bb = [v for v in body["base"]]
    bc = Vector(((min(v.x for v in bb) + max(v.x for v in bb)) / 2, (min(v.y for v in bb) + max(v.y for v in bb)) / 2,
                 (min(v.z for v in bb) + max(v.z for v in bb)) / 2))
    for n, p in parts.items():                 # body centre -> origin (the sidecar is relative to it)
        for v in p["base"]:
            v -= bc
        for vtx, v in zip(p["obj"].data.vertices, p["base"]):
            vtx.co = v
    return spec, parts


def part_table(spec, parts):
    """Resolve chain order and the effective phase; returns the ordered list of part records."""
    tab = {}
    for n, s in spec["parts"].items():
        tab[n] = {"name": n, "kind": s["kind"], "offset": Vector(s["offset"]), "hinge": Vector(s["hinge"]),
                  "axis": Vector(s["axis"]), "amp": s["amp"], "rate": s["rate"], "phase": s["phase"],
                  "lag": s.get("lag", 0.0), "gait": s["gait"], "chain": s.get("chain")}
    depth = {}

    def eff(n, guard=0):
        r = tab[n]
        if n in depth:
            return
        up = tab.get(r["chain"]) if r["chain"] else None
        d = 0
        if up and guard < 16:
            eff(up["name"], guard + 1)
            r["up"] = up
            r["phase_eff"] = up["phase_eff"] - r["lag"]
            d = depth[up["name"]] + 1
        else:
            r["up"] = None
            r["phase_eff"] = r["phase"]
        depth[n] = d

    for n in tab:
        eff(n)
    order = sorted(tab.values(), key=lambda r: depth[r["name"]])
    return order


def pose_matrices(order, spec_parts, parts, t, gates):
    """t: seconds. gates: dict FlapAmp, Idle, Bank. Returns {name: (acc, scale)} in the GAME frame."""
    accs = {}
    for r in order:
        g = r["gait"]
        gate = 1.0
        if g == "Flight":
            gate = gates["FlapAmp"]
        elif g == "Idle":
            gate = gates["Idle"]
        elif g == "Turn":
            gate = abs(gates["Bank"])
        clock = gates["clock"] if g == "Flight" else t
        wave = math.sin(clock * r["rate"] * 2 * math.pi + r["phase_eff"])
        hinge = Matrix.Identity(4)
        scale = 1.0
        if r["kind"] == "Spin":
            hinge = hinge_about(r["hinge"], r["axis"], t * r["rate"] + r["phase"])
        elif r["kind"] == "Flap":
            ang = gates["Bank"] * r["amp"] if g == "Turn" else wave * r["amp"] * gate
            hinge = hinge_about(r["hinge"], r["axis"], ang)
        elif r["kind"] == "Pulse":
            scale = 1 + r["amp"] * wave * gate
        acc = accs[r["up"]["name"]][0] @ hinge if r["up"] else hinge
        accs[r["name"]] = (acc, scale)
    return accs


def apply_pose(order, parts, accs):
    """Set every part object's matrix (Blender frame) from the game-frame accumulators."""
    for r in order:
        acc, scale = accs[r["name"]]
        # world_g = acc * T(off) * S * (M v - off)  with the mesh centred on its bbox centre at the sidecar offset
        # the stored mesh is in the Blender frame, so: B = M_B * acc * T(off) * S * T(-off) * M_G
        T = Matrix.Translation(r["offset"])
        S = Matrix.Scale(scale, 4)
        parts[r["name"]]["obj"].matrix_world = M_B @ acc @ T @ S @ T.inverted() @ M_G
        parts[r["name"]]["mw"] = parts[r["name"]]["obj"].matrix_world.copy()


# ----------------------------------------------------------------------------- attach audit
def posed_verts(p):
    return [p["mw"] @ v for v in p["base"]]


def inside(bvh, pt):
    hits = 0
    for d in (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))):
        n = 0
        o = pt.copy()
        for _ in range(64):
            loc, nrm, idx, dist = bvh.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-4
        hits += n % 2
    return hits >= 2


def attach_audit(order, parts, spec, accs, body_name):
    """For one pose: {part: (fraction attached, worst distance of an unattached root vertex)}."""
    out = {}
    cache = {}

    def bvh_of(n):
        if n not in cache:
            p = parts[n]
            vs = posed_verts(p)
            cache[n] = (BVHTree.FromPolygons([tuple(v) for v in vs], p["polys"]), vs)
        return cache[n][0]

    for r in order:
        parent = r["chain"] if r["chain"] else body_name
        if parent not in parts or r["kind"] in ("Pulse", "Flicker"):
            continue
        p = parts[r["name"]]
        hpos = (accs[r["chain"]][0] if r["chain"] else Matrix.Identity(4)) @ r["hinge"]    # game frame
        hb = M_B @ hpos
        vs = posed_verts(p)
        ext = max(max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3))
        rad = max(1.2, 0.08 * ext)
        ax_b = (M_B.to_3x3() @ (accs[r["chain"]][0].to_3x3() if r["chain"] else Matrix.Identity(3)) @ r["axis"]).normalized()
        reach = max(4.0, 0.25 * ext)                      # ...and within `reach` of the hinge point
        for grow in (1, 2, 3, 4, 6):
            root = [v for v in vs if ((v - hb) - ax_b * (v - hb).dot(ax_b)).length <= rad * grow
                    and (v - hb).length <= reach * grow]    # near the hinge AXIS line
            if root:
                break
        if not root:
            out[r["name"]] = (0.0, 99.0)
            continue
        bvh = bvh_of(parent)
        ok, worst = 0, 0.0
        for v in root:
            loc, nrm, idx, dist = bvh.find_nearest(v)
            if dist is not None and dist <= 0.5 or inside(bvh, v):
                ok += 1
            elif dist is not None:
                worst = max(worst, dist)
        out[r["name"]] = (ok / len(root), worst)
    return out


# ----------------------------------------------------------------------------- poses
def parse_poses(spec_s, ref_hz):
    poses = []
    for tok in spec_s.split(","):
        tok = tok.strip()
        if tok.startswith("beat"):
            n = int(tok.split(":")[1]) if ":" in tok else 6
            for k in range(n):
                poses.append((f"beat{k}", {"FlapAmp": 1.0, "Idle": 0.0, "Bank": 0.0, "clock": (k / n) / ref_hz,
                                           "t": (k / n) / ref_hz}))
        elif tok == "glide":
            poses.append(("glide", {"FlapAmp": 0.0, "Idle": 0.0, "Bank": 0.0, "clock": 0.0, "t": 0.3}))
        elif tok in ("turn", "turn+"):
            poses.append(("turn+", {"FlapAmp": 0.0, "Idle": 0.0, "Bank": 1.0, "clock": 0.0, "t": 0.3}))
        elif tok == "turn-":
            poses.append(("turn-", {"FlapAmp": 0.0, "Idle": 0.0, "Bank": -1.0, "clock": 0.0, "t": 0.3}))
        elif tok == "idle":
            poses.append(("idle", {"FlapAmp": 0.0, "Idle": 1.0, "Bank": 0.0, "clock": 0.0, "t": 0.9}))
        elif tok == "rest":
            poses.append(("rest", {"FlapAmp": 0.0, "Idle": 0.0, "Bank": 0.0, "clock": 0.0, "t": 0.0, "rest": True}))
    return poses


# ----------------------------------------------------------------------------- rendering
def setup_scene(here):
    import runpy
    sc = bpy.context.scene
    path = os.path.normpath(os.path.join(here, "..", "..", "render_crossroads.py"))
    ns = {"__name__": "crossroads_render", "__file__": path}
    if os.path.exists(path):
        exec(open(path, encoding="utf-8").read(), ns)
        ns["setup_world"]()
    else:
        for rot in ((62, 0, -40), (-50, 0, 140)):
            sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
            sc.collection.objects.link(sun)
            sun.rotation_euler = [math.radians(a) for a in rot]
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    return sc


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    fbx, jp = arg("--fbx"), arg("--json")
    out = arg("--out", os.path.join(here, "renders"))
    os.makedirs(out, exist_ok=True)
    data = json.load(open(jp, encoding="utf-8"))
    ids = arg("--ids", ",".join(data["creatures"])).split(",")
    res = [int(v) for v in arg("--res", "280x280").split("x")]
    views = arg("--views", "front,side,top").split(",")
    render = "--no-render" not in ARGV
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    sc = setup_scene(here) if render else bpy.context.scene
    cam = None
    if render:
        sc.render.resolution_x, sc.render.resolution_y = res
        cam = bpy.data.objects.new("PP_Cam", bpy.data.cameras.new("PP_Cam"))
        sc.collection.objects.link(cam)
        sc.camera = cam
        cam.data.type = "ORTHO"
        cam.data.clip_end = 5000
    import numpy as np
    for cid in ids:
        spec, parts = load_creature(fbx, data, cid)
        order = part_table(spec, parts)
        flight = [r for r in order if r["gait"] == "Flight" and r["kind"] == "Flap"]
        ref_hz = float(arg("--ref-hz", flight[0]["rate"] if flight else 1.0))
        poses = parse_poses(arg("--poses", "beat:6,glide,turn,idle,rest"), ref_hz)
        body = spec["model"]
        # visibility: only this creature
        for n, o in bpy.data.objects.items():
            if o.type == "MESH":
                o.hide_render = n not in parts
                o.hide_viewport = n not in parts
        rows = []
        jrows = []
        worst = {}
        allv = [v for p in parts.values() for v in p["base"]]
        span = max(max(v[i] for v in allv) - min(v[i] for v in allv) for i in range(3))
        for label, g in poses:
            if g.get("rest"):
                accs = {r["name"]: (Matrix.Identity(4), 1.0) for r in order}
            else:
                accs = pose_matrices(order, spec["parts"], parts, g["t"], g)
            apply_pose(order, parts, accs)
            # the body is static; make sure it carries the identity
            parts[body]["mw"] = Matrix.Identity(4)
            for n, (f, w) in attach_audit(order, parts, spec, accs, body).items():
                cur = worst.get(n, (1.0, 0.0))
                worst[n] = (min(cur[0], f), max(cur[1], w))
            if not render:
                continue
            cells = []
            for vn in views:
                ctr = Vector((0, 0, 0))
                if vn == "front":
                    cam.location = ctr + Vector((span * 2, 0, 0))
                    cam.rotation_euler = (math.radians(90), 0, math.radians(90))
                    cam.data.ortho_scale = span * 1.15
                elif vn == "side":
                    cam.location = ctr + Vector((0, -span * 2, 0))
                    cam.rotation_euler = (math.radians(90), 0, 0)
                    cam.data.ortho_scale = span * 1.15
                elif vn == "top":
                    cam.location = ctr + Vector((0, 0, span * 2))
                    cam.rotation_euler = (0, 0, 0)
                    cam.data.ortho_scale = span * 1.15
                fp = os.path.join(out, f"_pp_{cid}_{label}_{vn}.png")
                sc.render.filepath = fp
                bpy.ops.render.render(write_still=True)
                im = bpy.data.images.load(fp)
                w, h = im.size
                cells.append(np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4))
                bpy.data.images.remove(im)
                os.remove(fp)
            rows.append(np.concatenate(cells, axis=1))
            jn = arg("--join")
            if jn:
                tgt = next(r for r in order if r["name"].endswith(jn))
                hp = accs[tgt["chain"]][0] @ tgt["hinge"] if tgt["chain"] else tgt["hinge"]
                hb = M_B @ hp
                jc = []
                for vn in ("top", "front"):
                    cam.data.ortho_scale = max(24.0, span * 0.3)
                    if vn == "top":
                        cam.location = hb + Vector((0, 0, span))
                        cam.rotation_euler = (0, 0, 0)
                    else:
                        cam.location = hb + Vector((span, 0, 0))
                        cam.rotation_euler = (math.radians(90), 0, math.radians(90))
                    fp = os.path.join(out, f"_pj_{cid}_{label}_{vn}.png")
                    sc.render.filepath = fp
                    bpy.ops.render.render(write_still=True)
                    im = bpy.data.images.load(fp)
                    w, h = im.size
                    jc.append(np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4))
                    bpy.data.images.remove(im)
                    os.remove(fp)
                jrows.append(np.concatenate(jc, axis=1))
            print("POSED", cid, label)
        print(f"ATTACH REPORT {cid}: part -> (min fraction of root vertices attached, worst gap studs)")
        for n, (f, w) in sorted(worst.items(), key=lambda kv: kv[1][0]):
            if f < 0.999:
                print(f"   {n:44s} {f:5.2f}  gap {w:5.2f}")
        bad = [n for n, (f, w) in worst.items() if f < 0.999]
        print(f"ATTACH {cid}: {len(worst) - len(bad)}/{len(worst)} parts fully attached at every pose")
        # offset consistency (sidecar vs the FBX geometry)
        for r in order:
            vs = [M_G @ v for v in parts[r["name"]]["base"]]
            c = Vector([(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)])
            if (c - r["offset"]).length > 0.1:
                print(f"   OFFSET MISMATCH {r['name']}: sidecar {tuple(round(x, 2) for x in r['offset'])} "
                      f"mesh {tuple(round(x, 2) for x in c)}")
        if render and jrows:
            sheet = np.concatenate(jrows[::-1], axis=0)
            h, w = sheet.shape[:2]
            im = bpy.data.images.new("join", w, h)
            im.pixels = sheet.ravel().tolist()
            im.filepath_raw = os.path.join(out, f"{arg('--tag', '')}{cid}_join.png")
            im.file_format = "PNG"
            im.save()
            print("JOIN", im.filepath_raw)
        if render and rows:
            sheet = np.concatenate(rows[::-1], axis=0)       # pixel arrays are bottom-up: first pose ends up on top
            h, w = sheet.shape[:2]
            im = bpy.data.images.new("sheet", w, h)
            im.pixels = sheet.ravel().tolist()
            im.filepath_raw = os.path.join(out, f"{arg('--tag', '')}{cid}_posesheet.png")
            im.file_format = "PNG"
            im.save()
            print("SHEET", im.filepath_raw, [l for l, _ in poses])


run()
