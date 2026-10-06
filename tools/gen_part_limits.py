"""Self-clip limits for the sky creature sidecars (contract section 7 item 5).

For every Flap part of every creature in assets/export/hub/crossroads/creatures_*.json this imports the group FBX,
sweeps the part's hinge angle through its declared swing (-amp .. +amp) with the SAME maths as the game client
SkyTraffic, and writes the largest clash-free swing in each direction into the sidecar as  "limit": [min, max]
(radians, same sign convention as the driver).

    hingeAbout(hinge, axis, a) = T(hinge) * R(axis, a) * T(-hinge)
    part CFrame                = body * acc * T(offset)        acc = chain.acc * hinge     (orbiter frame)

The FBX is read back as Blender-frame world vertices and converted exactly like tools/gen_sky_creatures.py
`to_orbiter` (x, y, z) -> (-x, z, y).  Parts that live in the sidecar's "blender" frame (small group) have their
offset / hinge / axis converted the same way, so everything is compared in the orbiter frame.

Clash test (BVH): a part's vertices are tested against the body mesh and against every part that is neither one of
its chain ancestors nor one of its chain descendants (those ride with it).  A vertex clashes when it was OUTSIDE the
other mesh at the neutral pose and is now inside it by more than a tolerance (3 percent of the
part's longest extent, never below 0.02 studs); vertices within 22 percent of the part's extent of its hinge are not judged: joints are meant to overlap, growth of the overlap is the clipping.
Ancestors are swept over {-a, 0, +a} of their own (already limited) swing, so the limit holds at both ends of the
chain swing.  Idempotent: limits are recomputed from the declared amps every run and replace the old value.

    python tools/run_blender.py -b --factory-startup --python tools/gen_part_limits.py -- [--only ID] [--dry]
"""
import json
import math
import os
import statistics
import sys
from itertools import product
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

REPO = Path(__file__).resolve().parent.parent
EXPORT = REPO / "assets" / "export" / "hub" / "crossroads"
STEPS = 10          # per direction
MAX_VERTS = 700     # sample cap for the moving part
TOL_FRAC = 0.03
JOINT_ZONE = 0.22   # fraction of the part's longest extent around its hinge that may overlap freely


def to_orb(v):
    return Vector((-v[0], v[2], v[1]))


def hinge_about(h, axis, a):
    return Matrix.Translation(h) @ Matrix.Rotation(a, 4, axis) @ Matrix.Translation(-h)


class Mesh:
    def __init__(self, obj):
        mw = obj.matrix_world
        self.verts = [to_orb(mw @ v.co) for v in obj.data.vertices]
        self.polys = [tuple(p.vertices) for p in obj.data.polygons]
        lo = Vector([min(v[i] for v in self.verts) for i in range(3)])
        hi = Vector([max(v[i] for v in self.verts) for i in range(3)])
        self.centre = (lo + hi) * 0.5
        self.extent = max(hi - lo)


class Rig:
    def __init__(self, cid, entry, conv, body, meshes):
        self.cid = cid
        self.parts = entry["parts"]
        self.conv = conv
        self.meshes = meshes
        self.body = body
        self.d = {}
        for n, p in self.parts.items():
            self.d[n] = dict(
                kind=p["kind"], chain=p.get("chain"),
                off=Vector(conv(p["offset"])), hinge=Vector(conv(p["hinge"])),
                axis=Vector(conv(p["axis"])).normalized() if Vector(conv(p["axis"])).length > 1e-9 else Vector((0, 1, 0)),
                amp=p["amp"])
        shifts = [self.d[n]["off"] - meshes[n].centre for n in self.parts if self.d[n]["kind"] != "Pulse"]
        self.shift = Vector([statistics.median(s[i] for s in shifts) for i in range(3)])
        self.shift_spread = max((s - self.shift).length for s in shifts)
        self.body_verts = [v + self.shift for v in body.verts]
        self.body_bvh = BVHTree.FromPolygons(self.body_verts, body.polys, epsilon=0.0)
        self.body_box = box(self.body_verts)
        self.cache = {}

    def anc(self, n):
        out = []
        c = self.d[n]["chain"]
        while c:
            out.append(c)
            c = self.d[c]["chain"]
        return out[::-1]   # root first

    def acc(self, n, ang):
        """acc matrix of part n; ang maps part name -> hinge angle (missing = 0)."""
        chain = [n] + self.anc(n)[::-1]
        m = Matrix.Identity(4)
        for q in chain[::-1]:
            d = self.d[q]
            if d["kind"] == "Flap":
                m = m @ hinge_about(d["hinge"], d["axis"], ang.get(q, 0.0))
        return m

    def verts(self, n, ang, sample=None):
        d = self.d[n]
        m = self.acc(n, ang)
        mesh = self.meshes[n]
        vs = mesh.verts if sample is None else [mesh.verts[i] for i in sample]
        return [m @ (d["off"] + (v - mesh.centre)) for v in vs]

    def obstacle(self, q, ang):
        anc = self.anc(q)
        key = (q, tuple(round(ang.get(a, 0.0), 6) for a in anc + [q] if self.d[a]["kind"] == "Flap"))
        hit = self.cache.get(key)
        if hit is None:
            vs = self.verts(q, ang)
            hit = (BVHTree.FromPolygons(vs, self.meshes[q].polys, epsilon=0.0), box(vs))
            if len(self.cache) > 400:
                self.cache.clear()
            self.cache[key] = hit
        return hit


def box(vs):
    return (Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)]))


def overlaps(a, b, pad):
    return all(a[0][i] - pad <= b[1][i] and b[0][i] - pad <= a[1][i] for i in range(3))


def depths(vs, bvh, bx):
    """Per vertex (inside, distance to the nearest surface); inside by the nearest face normal (reliable near surfaces)."""
    out = []
    lo, hi = bx
    for v in vs:
        if all(lo[i] - 1e-6 <= v[i] <= hi[i] + 1e-6 for i in range(3)):
            loc, nor, _i, dist = bvh.find_nearest(v)
            if loc is not None:
                out.append(((v - loc).dot(nor) < 0, dist))
                continue
        out.append((False, 1e9))
    return out


def crossed(vs, dd, base, rest):
    """A vertex clips when it was outside at the neutral pose and is now inside by more than the tolerance,
    having moved no farther than it is deep (so the sign test only ever runs close to a surface)."""
    for v, (ins, dist), (ins0, _d0), r in zip(vs, dd, base, rest):
        if ins and not ins0 and dist > crossed.tol and dist <= (v - r).length + crossed.tol:
            return True
    return False


crossed.tol = 0.0


def clash(rig, n, ang, base, sample, rest, others):
    """The name of the obstacle that part n clips into at pose `ang` (or None)."""
    vs = rig.verts(n, ang, sample)
    pb = box(vs)
    if overlaps(pb, rig.body_box, 0):
        if crossed(vs, depths(vs, rig.body_bvh, rig.body_box), base["body"], rest):
            return "body"
    for q in others:
        bvh, bx = rig.obstacle(q, ang)
        if overlaps(pb, bx, 0):
            if crossed(vs, depths(vs, bvh, bx), base[q], rest):
                return q
    return None


def part_limit(rig, n, limits):
    d = rig.d[n]
    amp = abs(d["amp"])
    mesh = rig.meshes[n]
    nv = len(mesh.verts)
    stride = max(1, nv // MAX_VERTS)
    # joint zone: vertices within JOINT_ZONE of the hinge are meant to overlap the parent and are not judged
    hw = d["hinge"]
    rest = rig.verts(n, {})
    jz = JOINT_ZONE * mesh.extent
    sample = [i for i in range(0, nv, stride) if (rest[i] - hw).length > jz]
    if not sample:
        sample = list(range(0, nv, stride))
    tol = max(0.02, TOL_FRAC * mesh.extent)
    crossed.tol = tol
    anc = [a for a in rig.anc(n)]
    desc = {q for q in rig.parts if n in rig.anc(q)}
    others = [q for q in rig.parts if q != n and q not in anc and q not in desc]
    zero = {}
    rest_s = rig.verts(n, zero, sample)
    base = {"body": depths(rest_s, rig.body_bvh, rig.body_box)}
    for q in others:
        bvh, bx = rig.obstacle(q, zero)
        base[q] = depths(rest_s, bvh, bx)
    # ancestor combos over their (already limited) swing
    choices = []
    for a in anc:
        if rig.d[a]["kind"] != "Flap" or rig.d[a]["amp"] <= 0:
            choices.append([0.0])
            continue
        lo, hi = limits.get(a, (-abs(rig.d[a]["amp"]), abs(rig.d[a]["amp"])))
        choices.append(sorted({lo, 0.0, hi}))
    combos = [dict(zip(anc, c)) for c in product(*choices)]
    res = []
    culprit = {}
    for sign in (-1, 1):
        best = 0.0
        for k in range(1, STEPS + 1):
            th = sign * amp * k / STEPS
            bad = None
            for cb in combos:
                a2 = dict(cb)
                a2[n] = th
                bad = clash(rig, n, a2, base, sample, rest_s, others)
                if bad:
                    break
            if bad:
                culprit[sign] = bad
                break
            best = th
        res.append(best)
    return res, culprit, amp


def main(argv):
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    dry = "--dry" in argv
    rows = []
    for jpath in sorted(EXPORT.glob("creatures_*.json")):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        conv = (lambda v: [-v[0], v[2], v[1]]) if data.get("frame") == "blender" else (lambda v: list(v))
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(jpath.with_suffix(".fbx")))
        objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
        changed = False
        for cid, entry in data["creatures"].items():
            if only and cid != only:
                continue
            body = Mesh(objs[entry["model"]])
            meshes = {n: Mesh(objs[n]) for n in entry["parts"]}
            rig = Rig(cid, entry, conv, body, meshes)
            if rig.shift_spread > 2.0:
                print("WARN %s: part offsets vs mesh centres disagree by up to %.2f (shift %s)" % (cid, rig.shift_spread, tuple(round(x, 2) for x in rig.shift)))
            limits = {}
            order = sorted(entry["parts"], key=lambda n: len(rig.anc(n)))
            for n in order:
                p = entry["parts"][n]
                if p["kind"] != "Flap" or p["amp"] <= 0:
                    p.pop("limit", None)
                    continue
                (lo, hi), culprit, amp = part_limit(rig, n, limits)
                limits[n] = (lo, hi)
                lim = [round(lo, 4), round(hi, 4)]
                if p.get("limit") != lim:
                    changed = True
                p["limit"] = lim
                flag = ""
                if lo == 0.0 and hi == 0.0:
                    flag = "CANNOT SWING (%s)" % ",".join(sorted(set(culprit.values())))
                elif abs(lo) < amp - 1e-9 or hi < amp - 1e-9:
                    flag = "limited by " + ",".join(sorted(set(culprit.values())))
                rows.append((cid, n.split("__", 1)[1], p["amp"], lim, flag))
        if changed and not dry:
            jpath.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print("%-18s %-22s %7s  %-20s %s" % ("creature", "part", "amp", "limit [min,max]", "note"))
    for cid, n, amp, lim, flag in rows:
        print("%-18s %-22s %7.3f  [%7.4f, %7.4f]  %s" % (cid, n, amp, lim[0], lim[1], flag))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
