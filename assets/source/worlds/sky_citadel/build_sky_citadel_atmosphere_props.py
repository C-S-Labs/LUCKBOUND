"""Sky Citadel ATMOSPHERE PROPS -- the things each scenario atmosphere's
effects come out of (owner, 2026-09-23: "Red laser for lockdown should come out
of something ... Siege's smoke plume is coming out of nowhere").

Each is one library mesh, placed at run time by AtmosphereEffects.luau round
the map (never on a chunk): client-side sky scenery, like the cloud sea.

  Lockdown      atm_security_probe  hovering drone; the searchlight beam comes out of its lens
                atm_dome_pylon      the emitter the aegis dome is raised from
  Siege         atm_burning_wreck   a crashed raider hull, burning; the smoke plume rises from it
                atm_wreck_stern     a second wreck, stern up
  Stormhawk     atm_storm_conductor an iron rod on a storm-stone pinnacle; lightning strikes it
                atm_stormhawk       the raptor itself, circling the map
  Rime          atm_ice_floe        a drifting slab of ice, snow on top, icicles under
  Reclaimed     atm_seed_pod        a drifting seed pod trailing leaves
  Aether Surge  atm_aurora_prism    a floating crystal the aurora curtains stream from
  Unmooring     atm_falling_masonry a chunk of the citadel falling away
                atm_broken_ring     a snapped anti-grav ring fragment, still glowing

Run headless:
    blender -b --factory-startup --python build_sky_citadel_atmosphere_props.py -- --export --save
--export writes assets/export/worlds/sky_citadel/sky_citadel_atmosphere_props.fbx;
--save adds the props to sky_citadel_kit.blend (collection AtmosphereProps).
"""

import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_PATH = os.path.join(HERE, "build_sky_citadel_kit.py")
K = {"__name__": "sky_citadel_kit", "__file__": KIT_PATH}
exec(open(KIT_PATH, encoding="utf-8").read(), K)

K["PALETTE"].update({
    "Soot": ((40, 38, 48), False), "Char": ((64, 54, 52), False), "Snow": ((244, 248, 255), False),
    "Frost": ((196, 214, 232), False), "Ice": ((150, 200, 230), False), "AlarmRed": ((255, 70, 80), True),
    "EmberGlow": ((255, 150, 60), True), "RaiderRust": ((158, 74, 52), False), "Twig": ((110, 90, 70), False),
    "Bark": ((92, 70, 52), False), "Moss": ((70, 112, 66), False), "MossLight": ((118, 160, 86), False),
    "AetherBloom": ((190, 150, 255), True), "Pearl": ((236, 228, 246), False), "Gunmetal": ((70, 76, 88), False),
    "Steel": ((104, 112, 126), False), "Hazard": ((232, 188, 40), False), "StormStone": ((140, 148, 164), False),
    "StormSlate": ((84, 92, 110), False), "Bone": ((226, 220, 200), False),
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())

box, frustum, crystal, torus, tube, orb, xf, frame = (K[n] for n in ("box", "frustum", "crystal", "torus", "tube",
                                                                      "orb", "xf", "frame"))
EXPORT = os.path.join(K["REPO"], "assets", "export", "worlds", "sky_citadel", "sky_citadel_atmosphere_props.fbx")


def lump(p, mat, profile, n=7, seed="lump", jitter=0.2, cx=0.0, cy=0.0, sx=1.0, sy=1.0):
    rng = random.Random(seed)
    cols = [1.0 + rng.uniform(-jitter, jitter) for _ in range(n)]
    verts, faces, idx = [], [], []
    for r, z in profile:
        ring = []
        if r <= 1e-6:
            verts.append((cx, cy, z))
            ring.append(len(verts) - 1)
        else:
            for i in range(n):
                a = 2 * math.pi * i / n
                verts.append((cx + math.cos(a) * r * cols[i] * sx, cy + math.sin(a) * r * cols[i] * sy, z))
                ring.append(len(verts) - 1)
        idx.append(ring)
    for A, B in zip(idx, idx[1:]):
        if len(A) > 1 and len(B) > 1:
            faces += [(A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]) for i in range(n)]
        elif len(B) == 1:
            faces += [(A[i], A[(i + 1) % n], B[0]) for i in range(n)]
        else:
            faces += [(A[0], B[(i + 1) % n], B[i]) for i in range(n)]
    if len(idx[0]) > 1:
        faces.append(tuple(reversed(idx[0])))
    if len(idx[-1]) > 1:
        faces.append(tuple(idx[-1]))
    p.add(verts, faces, mat, K["Matrix"].Identity(4))


# ---- Lockdown -------------------------------------------------------------------

def atm_security_probe(p):
    orb(p, "Gunmetal", 0, 0, 0, 2.4, n=10)
    torus(p, "AlarmRed", 2.7, 0.22, 0, 0, 0, n=16)
    for k in range(3):
        a = math.radians(120 * k)
        with frame(p, xf(math.cos(a) * 2.2, math.sin(a) * 2.2, 0.4, math.degrees(a), 0, 0)):
            box(p, "Steel", 1.2, 0, 0, 2.6, 0.3, 1.4)
            frustum(p, "Gunmetal", 8, 0.45, 0.35, -0.6, 0.6, 2.5, 0)
    frustum(p, "Steel", 10, 1.1, 0.8, -2.4, -1.6, 0, 0)
    frustum(p, "AlarmRed", 10, 0.75, 0.75, -2.7, -2.4, 0, 0)     # the lens: the beam starts here
    frustum(p, "Steel", 6, 0.12, 0.05, 2.2, 4.2, 0, 0)
    crystal(p, "AlarmRed", 0, 0, 4.3, 0.25, 0.3, 0.2)


def atm_dome_pylon(p):
    frustum(p, "Gunmetal", 8, 6.0, 4.6, 0, 3, 0, 0)
    frustum(p, "Steel", 4, 2.6, 1.0, 3, 46, 0, 0, rot=45)
    for z in (14, 26, 38):
        frustum(p, "Hazard", 4, 2.6 - z * 0.034, 2.6 - z * 0.034, z, z + 0.8, 0, 0, rot=45)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        tube(p, "Gunmetal", [(math.cos(a) * 5.5, math.sin(a) * 5.5, 1.5), (math.cos(a) * 1.6, math.sin(a) * 1.6, 20)],
             [0.5, 0.3], n=5)
    torus(p, "AlarmRed", 1.15, 0.35, 0, 0, 44, n=16)
    crystal(p, "AlarmRed", 0, 0, 47.5, 1.4, 3.5, 1.6, n=6)


# ---- Siege ------------------------------------------------------------------------

def _hull(p, L, w, d, mats):
    xs = [-L / 2, -L / 4, 0, L / 4, L / 2]
    ws = [w * 0.7, w, w, w * 0.8, 0.2]
    for (x0, w0), (x1, w1) in zip(zip(xs, ws), zip(xs[1:], ws[1:])):
        with frame(p, xf((x0 + x1) / 2, 0, 0, 0, 0, 90)):
            frustum(p, mats[0], 8, w0, max(w1, 0.2), -(x1 - x0) / 2, (x1 - x0) / 2)
    box(p, mats[1], 0, 0, w * 0.55, L * 0.8, w * 1.5, 0.5)


def atm_burning_wreck(p):
    with frame(p, xf(0, 0, 3, 20, 14, -9)):
        _hull(p, 44, 6, 6, ("RaiderRust", "Char"))
        frustum(p, "Bark", 8, 0.8, 0.5, 3, 20, -6, 0)                       # the snapped mast
        box(p, "Char", -6, 0, 12, 0.4, 9, 7, rx=10)                         # the burnt sail
        for k in range(9):                                                   # the fire
            crystal(p, "EmberGlow", -18 + k * 4.2, (k % 3 - 1) * 2.2, 3.6, 1.1 + (k % 2) * 0.6, 3.5 + (k % 3) * 1.8,
                    0.5, n=5, rz=k * 23)
    lump(p, "Soot", [(9, 6), (11, 10), (8, 15), (0, 17)], n=8, seed="wreck smoke", jitter=0.25, cx=-4)


def atm_wreck_stern(p):
    with frame(p, xf(0, 0, 0, 0, 0, -58)):
        _hull(p, 34, 5.5, 5, ("RaiderRust", "Soot"))
        box(p, "RaiderRust", -13, 0, 4.8, 8, 9.5, 5)
        for k in range(3):
            box(p, "EmberGlow", -13, (k - 1) * 3, 4.9, 0.3, 1.4, 1.2)
    for k in range(6):
        crystal(p, "EmberGlow", -2 + k * 1.6, (k % 2) * 2 - 1, -6 + k * 2.5, 1.0, 3.0, 0.4, n=5, rz=k * 31)


# ---- Stormhawk --------------------------------------------------------------------

def atm_storm_conductor(p):
    rng = random.Random("conductor")
    z, r = 0.0, 9.0
    while z < 40:
        h = rng.uniform(6, 10)
        lump(p, rng.choice(("StormStone", "StormSlate")), [(r, z), (r * 1.08, z + h * 0.45), (r * 0.82, z + h),
                                                          (0, z + h + 0.4)], n=7,
             seed="cond %.0f" % z, jitter=0.18)
        z, r = z + h - 0.6, max(2.4, r * 0.8)
    frustum(p, "Gunmetal", 6, 0.9, 0.3, z - 3, z + 34, 0, 0)
    for k in range(5):
        torus(p, "Hazard", 0.9 - k * 0.1, 0.18, 0, 0, z + 4 + k * 5.5, n=12)
    crystal(p, "Hazard", 0, 0, z + 34.2, 0.5, 1.6, 0.2)


def atm_stormhawk(p):
    with frame(p, xf(0, 0, 0, 0, 0, 90)):              # the body lies along the flight line (+x)
        lump(p, "StormSlate", [(0, -7), (1.6, -4), (2.2, 0), (1.8, 3), (1.1, 5.5), (0, 7)], n=8, seed="hawk body",
             jitter=0.05, sx=0.8, sy=1.0)
    for s in (-1, 1):
        pts = [(0, s * 1.5, 0.8), (-1, s * 7, 1.8), (-3, s * 13, 1.2), (-6, s * 18, -0.2)]
        tube(p, "StormSlate", pts, [0.9, 0.7, 0.45, 0.1], n=5)
        for k in range(5):
            a = pts[1 + k % 3]
            box(p, "Soot", a[0] - 1.0, a[1], a[2], 3.4, 1.4, 0.2, rz=s * 12 + k * 4)
    frustum(p, "Hazard", 5, 0.5, 0.0, 7.0, 9.4, 0, 0, M=xf(0, 0, 0, 0, 0, 90))
    for s in (-1, 1):
        box(p, "Soot", -6.4, s * 0.6, 0, 3.2, 1.0, 0.25, rz=s * 18)


# ---- Rime -------------------------------------------------------------------------

def atm_ice_floe(p):
    rng = random.Random("floe")
    lump(p, "Ice", [(14, -3), (15, -1), (14.5, 0.8), (0, 1.0)], n=11, seed="floe", jitter=0.22, sx=1.0, sy=0.75)
    lump(p, "Snow", [(12.5, 0.6), (11, 1.6), (6, 2.4), (0, 2.6)], n=11, seed="floe snow", jitter=0.25, sy=0.72)
    for k in range(12):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(4, 12)
        crystal(p, "Ice", math.cos(a) * d, math.sin(a) * d * 0.7, -2.4, rng.uniform(0.6, 1.3), 0.01,
                rng.uniform(3, 8), n=4)


# ---- Reclaimed --------------------------------------------------------------------

def atm_seed_pod(p):
    lump(p, "MossLight", [(0, -3), (1.6, -1.5), (2.0, 0.5), (1.2, 2.5), (0, 3.6)], n=8, seed="pod", jitter=0.08)
    for k in range(5):
        a = math.radians(72 * k)
        with frame(p, xf(math.cos(a) * 1.2, math.sin(a) * 1.2, 2.4, math.degrees(a), 0, 55)):
            box(p, "Moss", 0, 0, 1.0, 0.8, 0.12, 3.4)
    tube(p, "Bark", [(0, 0, -2.8), (0.6, 0.3, -5), (0.2, 0.9, -7.5)], [0.25, 0.18, 0.05], n=4)
    for k in range(6):
        a = math.radians(60 * k + 20)
        crystal(p, "Bone", math.cos(a) * 0.3, math.sin(a) * 0.3, 3.3, 0.12, 2.2, 0.4, n=4)


# ---- Aether Surge -----------------------------------------------------------------

def atm_aurora_prism(p):
    rng = random.Random("prism")
    crystal(p, "AetherBloom", 0, 0, 0, 3.6, 12, 9, n=6)
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi)
        with frame(p, xf(math.cos(a) * 1.8, math.sin(a) * 1.8, rng.uniform(-3, 3), math.degrees(a), 0,
                         rng.uniform(25, 50))):
            crystal(p, rng.choice(("Pearl", "AetherBloom")), 0, 0, 0, 1.0, rng.uniform(4, 7), 0.6, n=5)
    torus(p, "Pearl", 5.2, 0.35, 0, 0, 1.0, n=18)
    torus(p, "AetherBloom", 6.4, 0.25, 0, 0, -1.0, n=18, rx=20)
    for k in range(3):
        a = math.radians(120 * k)
        tube(p, "Pearl", [(math.cos(a) * 1.4, math.sin(a) * 1.4, 1.0), (math.cos(a) * 5.2, math.sin(a) * 5.2, 1.0)],
             [0.2, 0.2], n=4)
    tube(p, "AetherBloom", [(0, 0, -0.5), (math.cos(0.3) * 6.2, math.sin(0.3) * 6.2, -1.0 - 6.2 * math.sin(0.35))],
         [0.18, 0.18], n=4)


# ---- Unmooring --------------------------------------------------------------------

def atm_falling_masonry(p):
    box(p, "CitadelWhite", 0, 0, 0, 12, 4, 7, rx=6)
    box(p, "PaleAlloy", 0, 0, 3.9, 12.4, 4.4, 0.8, rx=6)
    for k in range(3):
        box(p, "PaleAlloy", -4 + k * 4, 0.2, 5.2, 2.4, 3.8, 1.8, rx=6)
    box(p, "AzureDim", 0, -2.05, 1.6, 11, 0.12, 0.5, rx=6)
    for k in range(5):
        crystal(p, "CitadelWhite", -5 + k * 2.5, (k % 2 - 0.5) * 2.4, -3.2, 1.0, 0.6, 2.2 + k % 3, n=4, rz=k * 17)
    box(p, "HullSlate", 1, 0, -4.4, 9, 3.6, 2.2, rx=6, rz=8)


def atm_broken_ring(p):
    K["torus_arc"](p, "PaleAlloy", 14, 1.1, 0, 0, 0, 0, 140, n=14)
    K["torus_arc"](p, "AzureNeon", 14, 0.55, 0, 0, 0.9, 4, 136, n=14)
    for a in (0, 140):
        r = math.radians(a)
        for k in range(4):
            crystal(p, "PaleAlloy", math.cos(r) * 14, math.sin(r) * 14, (k - 1.5) * 0.7, 0.6, 0.8, 0.6, n=4,
                    rz=k * 30)
        crystal(p, "AzureNeon", math.cos(r) * 14, math.sin(r) * 14, 0, 0.5, 1.8, 1.8, n=5)


PROPS = [atm_security_probe, atm_dome_pylon, atm_burning_wreck, atm_wreck_stern, atm_storm_conductor,
         atm_stormhawk, atm_ice_floe, atm_seed_pod, atm_aurora_prism, atm_falling_masonry, atm_broken_ring]


def build(collection, mats):
    objs, report = [], []
    for i, fn in enumerate(PROPS):
        p = K["Piece"](fn.__name__, "atmosphere prop")
        fn(p)
        faults = K["analyse"](p)["detached"]
        vs = p.verts
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        c = (mn + mx) / 2
        verts = [v - c for v in vs]
        radius = max(math.hypot(v.x, v.y) for v in verts)
        verts, faces, fmat = K["detail"](verts, p.faces, p.fmat, fn.__name__, radius)
        shell = K["Piece"](fn.__name__, "atmosphere prop")
        shell.verts, shell.faces, shell.fmat = list(verts), faces, fmat
        o = K["to_object"](shell, mats, collection)
        o.location = ((i % 6) * 70.0, -2200.0 - (i // 6) * 80.0, 0)
        objs.append(o)
        report.append((fn.__name__, sum(len(f) - 2 for f in faces), len(faults),
                       tuple(round(x, 1) for x in (mx - mn))))
    return objs, report


def main(export=False, save=False):
    if save:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "sky_citadel_kit.blend"))
        old = bpy.data.collections.get("AtmosphereProps")
        if old:
            for o in list(old.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(old)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K["ensure_materials"]()
    coll = bpy.data.collections.new("AtmosphereProps")
    bpy.context.scene.collection.children.link(coll)
    objs, report = build(coll, mats)
    for r in report:
        print("ATMPROP", *r)
    bad = [r[0] for r in report if r[2]]
    if bad:
        raise RuntimeError("detached parts in: %r" % bad)
    if export:
        K["_export_selected"](objs, EXPORT)
        v = K["verify_exports"]([EXPORT])[0]
        print("EXPORTED", v["file"], v["meshes"])
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "sky_citadel_kit.blend"))
        print("SAVED sky_citadel_kit.blend")
    return objs


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(export="--export" in argv, save="--save" in argv)
