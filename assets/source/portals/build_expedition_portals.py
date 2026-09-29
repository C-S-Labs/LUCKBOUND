"""THE EXPEDITION RIFTS (build spec §7.8): the ENTRANCE and the EXIT.

Owner, 2026-09-28: the first cut was a mechanical ring portal; it was out of
place in a floating biome. Both doors are now RIFTS, tears in the air, and the
exit materialises out of nothing when the boss falls.

Each rift is ONE model of separate named meshes. The mesh carries the SHAPE
(the tear, its jagged lips, the floating rock); code carries the MOTION and
the light (Beams with the flow texture, particles, tweening, the colour), so
the same meshes serve a calm entrance and an exit that opens in five seconds.

    ENTRANCE  always open, the way home. Coloured by the biome's rarity.
    EXIT      opens where the boss fell. Always crimson.

Authored in STUDS (1 Blender unit = 1 stud; the export lands 1:1). The walk
plane is z = 0 at the rift's centre. The tear lies in the XZ plane and players
come and go along Y.

FLUSH AND WALKABLE (owner, 2026-09-28): nothing here is collidable and nothing
stands above z = 0.12. The tear's tip touches the deck, so the way through is
level ground; there is no platform to climb.

CONTRACT (one flat model; names are exact, no .001 suffixes)
    Scar         PrimaryPart: the cracked ground the rift stands in. Thin,
                 dark, NOT collidable. Carries the prompt.
    ScarGlow     TINTED. Glowing cracks laid just over Scar.
    RiftCore     TINTED. The bright inner tear.
    RiftMid      TINTED. A translucent shell round the core.
    RiftHalo     TINTED. The widest, softest shell.
    Edge1..N     TINTED. Crystal spikes lining the lips of the tear.
    FragRock1..N static dark rock, floating round the tear.
    FragGem1..N  TINTED. A crystal set in each rock.
    Debris       static. Loose stones on the ground round the scar.
    LightAnchor  a tiny marker the code hangs the point light from.

TINTED parts are near-white and untextured on purpose: a SurfaceAppearance
overrides Color and would kill the per-rarity colour.

Run headless (bpy 4.x/5.x):
    blender -b --factory-startup --python build_expedition_portals.py -- --variant BOTH --export --save
    (or: python build_expedition_portals.py --variant EXIT with the `bpy` wheel)
"""

import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EXPORT_DIR = os.path.join(REPO, "assets", "export", "portals")

# The owner accepted a lower count than the mechanical version (10-25k): a
# rift's richness is in its animation. The per-mesh cap is the house rule.
TRI_MIN, TRI_MAX = 3_000, 25_000
MESH_MAX = 10_000

GROUND_MAX = 0.12  # nothing sits higher than this above the deck

# (rgb 0-255, emissive). House palette: the Fate Engine as painted in game.
PALETTE = {
    "Basalt": ((64, 58, 78), False),
    "Rock": ((70, 62, 92), False),
    # Near-white so a rarity Color on the part is the colour you see.
    "Tint": ((240, 240, 246), True),
}

# Per-variant dimensions, in studs.
VARIANTS = {
    "ENTRANCE": {
        "height": 15.0, "width": 6.4, "thick": 1.1,
        "edges": 12, "frags": 7, "frag_r": (0.6, 1.2), "debris": 22,
        "scar_r": 6.5, "cracks": 9, "seed": 7,
    },
    "EXIT": {
        "height": 21.0, "width": 9.0, "thick": 1.5,
        "edges": 18, "frags": 10, "frag_r": (0.8, 1.7), "debris": 34,
        "scar_r": 9.5, "cracks": 13, "seed": 11,
    },
}


class Mesh:
    """One named object's geometry, built from primitives into one bmesh."""

    def __init__(self, name, mat):
        self.name, self.mat = name, mat
        self.bm = bmesh.new()

    def face(self, pts):
        vs = [self.bm.verts.new(p) for p in pts]
        try:
            self.bm.faces.new(vs)
        except ValueError:
            pass

    def crystal(self, base, direction, radius, length, sides, lean=0.0):
        """A faceted crystal from `base` along `direction`: a hexagonal-style
        prism that narrows slightly, then is cut to a point that sits a little
        off-axis (`lean`, a fraction of the radius), so the tip reads as a
        cleaved facet, not a cone. 2 * sides + sides + (sides - 2) triangles."""
        d = Vector(direction).normalized()
        rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix()
        base = Vector(base)

        def ring(rad, z, phase):
            return [rot @ Vector((rad * math.cos(2 * math.pi * i / sides + phase), rad * math.sin(2 * math.pi * i / sides + phase), z)) + base for i in range(sides)]

        ring0 = ring(radius, 0.0, 0.0)
        ring1 = ring(radius * 0.9, length * 0.72, 0.0)
        tip = base + rot @ Vector((radius * lean, 0.0, length))
        for i in range(sides):
            j = (i + 1) % sides
            self.face([ring0[i], ring0[j], ring1[j], ring1[i]])
            self.face([ring1[i], ring1[j], tip])
        self.face(list(reversed(ring0)))

    def rock(self, centre, radius, rng, subdiv=1, squash=(1.0, 1.0, 0.8)):
        """A faceted, chipped stone: an icosphere pushed about by the seeded
        rng so no two fragments match."""
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=1.0)
        for v in res["verts"]:
            jitter = 0.78 + 0.42 * rng.random()
            v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2])) * (radius * jitter) + Vector(centre)

    def lens(self, half_h, z0, half_w, half_t, stacks, sides, rng, jag):
        """A vertical almond: pointed top and bottom, widest at the middle,
        thin along Y. Its lips are jittered by `jag`. Tip at z0, top at
        z0 + 2 * half_h."""
        rings = []
        for k in range(stacks + 1):
            t = k / stacks
            z = z0 + 2 * half_h * t
            envelope = (4 * t * (1 - t)) ** 0.75
            w = half_w * envelope * (1 + jag * (rng.random() - 0.5))
            th = half_t * envelope
            rings.append([(w * math.cos(2 * math.pi * i / sides), th * math.sin(2 * math.pi * i / sides), z) for i in range(sides)])
        for k in range(stacks):
            for i in range(sides):
                j = (i + 1) % sides
                a, b, c, d = rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]
                if k == 0:
                    self.face([b, c, d])  # the bottom ring is a point
                elif k == stacks - 1:
                    self.face([a, b, d])  # so is the top
                else:
                    self.face([a, b, c, d])

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def finish(self, collection):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for p in me.polygons:
            p.use_smooth = False  # FLAT SHADED: the whole house style
        obj = bpy.data.objects.new(self.name, me)
        collection.objects.link(obj)
        obj.data.materials.append(material(self.mat))
        return obj


_MATS = {}


def material(key):
    if key not in _MATS:
        rgb, emissive = PALETTE[key]
        m = bpy.data.materials.new(key)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        c = tuple(v / 255.0 for v in rgb) + (1.0,)
        if bsdf:
            bsdf.inputs["Base Color"].default_value = c
            bsdf.inputs["Roughness"].default_value = 1.0
        m.diffuse_color = c
        _MATS[key] = m
    return _MATS[key]


def half_width_at(v, t):
    """The tear's half-width at height fraction t (0 tip, 1 top)."""
    return v["width"] / 2 * (4 * t * (1 - t)) ** 0.75


def build(variant):
    v = VARIANTS[variant]
    rng = random.Random(v["seed"])
    parts = []
    H, W, T = v["height"], v["width"], v["thick"]
    z0 = 0.05  # the tip touches the deck

    # --- The tear: three nested shells, so code can breathe each on its own --
    core = Mesh("RiftCore", "Tint")
    core.lens(H / 2 * 0.86, z0 + H * 0.07, W / 2 * 0.62, T / 2 * 0.5, 18, 12, rng, 0.10)
    parts.append(core)
    mid = Mesh("RiftMid", "Tint")
    mid.lens(H / 2 * 0.94, z0 + H * 0.03, W / 2 * 0.86, T / 2 * 0.8, 20, 14, rng, 0.14)
    parts.append(mid)
    halo = Mesh("RiftHalo", "Tint")
    halo.lens(H / 2, z0, W / 2 * 1.15, T / 2 * 1.2, 24, 16, rng, 0.18)
    parts.append(halo)

    # --- Lips: small crystal clusters growing along the edges of the tear ----
    # Sized to the tear (its height is 15 or 21 studs): slender, and in groups
    # of three that fan slightly, so the lip reads as crusted with crystal
    # rather than fenced with spikes.
    k = H / 15.0
    for n in range(v["edges"]):
        side = -1 if n % 2 == 0 else 1
        t = 0.12 + 0.76 * ((n // 2) + rng.random() * 0.4) / (v["edges"] / 2)
        t = min(0.9, t)
        w = half_width_at(v, t) * 1.04
        m = Mesh(f"Edge{n + 1}", "Tint")
        for c in range(3):
            spread = (c - 1) * 0.42
            base = Vector((side * (w + abs(c - 1) * 0.06), (rng.random() - 0.5) * T * 0.3, z0 + H * t + (c - 1) * 0.28 * k))
            out = Vector((side * (0.9 - abs(spread) * 0.3), (rng.random() - 0.5) * 0.25, 0.55 + spread))
            length = (1.4 if c == 1 else 0.95) * (0.8 + 0.5 * rng.random()) * k
            m.crystal(base, out, (0.17 if c == 1 else 0.12) * k, length, 6, lean=0.5 * (rng.random() - 0.5))
        parts.append(m)

    # --- Floating fragments: rock with a crystal set in it -------------------
    mean_r = (v["frag_r"][0] + v["frag_r"][1]) / 2  # bigger stones get an extra chip
    # FRAGMENTS STAY ON THE SIDES. The walk-through path runs along Y (in
    # front of and behind the tear), so rock only sits within 38 degrees of
    # the +/-X axis, and never nearer the tear than its own width. The
    # animation must orbit them in that same band; see the README.
    per_side = {1: [], -1: []}
    for n in range(v["frags"]):
        per_side[1 if n % 2 == 0 else -1].append(n)
    slot = {}
    for sgn, ids in per_side.items():
        for order, n in enumerate(ids):
            slot[n] = (sgn, (order + rng.random() * 0.6) / max(1, len(ids)))
    for n in range(v["frags"]):
        sgn, frac = slot[n]
        ang = (0.0 if sgn > 0 else math.pi) + (rng.random() - 0.5) * 2 * math.radians(38) * (1 if sgn > 0 else -1)
        ring_r = W * (1.05 + 0.8 * rng.random())
        h = z0 + H * (0.2 + 0.72 * frac)  # clear of the ground and the path
        c = Vector((math.cos(ang) * ring_r, math.sin(ang) * ring_r * 0.55, h))
        r = v["frag_r"][0] + (v["frag_r"][1] - v["frag_r"][0]) * rng.random()
        rk = Mesh(f"FragRock{n + 1}", "Rock")
        rk.rock(c, r, rng, subdiv=3,
                squash=(1.0, 0.85 + 0.3 * rng.random(), 0.7 + 0.4 * rng.random()))
        # A couple of chips broken off, floating beside it.
        for _ in range(4 if r > mean_r else 3):
            off = Vector(((rng.random() - 0.5) * r * 2.6, (rng.random() - 0.5) * r * 2.6, r * (0.9 + rng.random())))
            rk.rock(c + off, r * (0.22 + 0.15 * rng.random()), rng, subdiv=1)
        parts.append(rk)
        gm = Mesh(f"FragGem{n + 1}", "Tint")
        gm.crystal(c + Vector((0, 0, r * 0.55)), Vector((rng.random() - 0.5, rng.random() - 0.5, 1.0)), r * 0.28, r * (1.1 + 0.6 * rng.random()), 7)
        parts.append(gm)

    # --- The scar: cracked ground, thin and flat, never in the way -----------
    scar = Mesh("Scar", "Basalt")
    glow = Mesh("ScarGlow", "Tint")
    R = v["scar_r"]
    for i in range(v["cracks"]):
        a = 2 * math.pi * i / v["cracks"] + (rng.random() - 0.5) * 0.35
        length = R * (0.55 + 0.45 * rng.random())
        width = 0.5 + 0.55 * rng.random()
        # A crack is a tapered strip, wide at the tear, pointed at the far end.
        dirv = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-dirv.y, dirv.x, 0))
        p0 = dirv * 0.6
        pm = dirv * length * 0.5 + side * (rng.random() - 0.5) * 0.8
        p1 = dirv * length + side * (rng.random() - 0.5) * 1.2
        for surf, z, wscale in ((scar, GROUND_MAX * 0.5, 1.9), (glow, GROUND_MAX * 0.5 + 0.02, 0.75)):
            wd = width * wscale
            outline = [p0 + side * wd, pm + side * wd * 0.6, p1, pm - side * wd * 0.6, p0 - side * wd]
            pts = [Vector((q.x, q.y, z)) for q in outline]
            for k in range(1, len(pts) - 1):
                surf.face([pts[0], pts[k], pts[k + 1]])
    # A flat worn disc under the tear, so the ground reads as part of the rift.
    sides = 20
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        r0 = R * 0.34 * (0.85 + 0.3 * rng.random())
        r1 = R * 0.34 * (0.85 + 0.3 * rng.random())
        zz = GROUND_MAX * 0.4
        scar.face([(0, 0, zz), (r0 * math.cos(a0), r0 * math.sin(a0), zz), (r1 * math.cos(a1), r1 * math.sin(a1), zz)])
    parts.append(scar)
    parts.append(glow)

    # --- Loose stones on the ground, low enough to walk through --------------
    deb = Mesh("Debris", "Rock")
    for _ in range(v["debris"]):
        a = 2 * math.pi * rng.random()
        d = R * (0.35 + 0.75 * rng.random())
        r = 0.16 + 0.34 * rng.random()
        deb.rock((d * math.cos(a), d * math.sin(a), r * 0.15), r, rng, subdiv=0, squash=(1.0, 1.0, 0.45))
    parts.append(deb)

    la = Mesh("LightAnchor", "Basalt")
    la.crystal((0, 0, z0 + H * 0.5 - 0.2), (0, 0, 1), 0.2, 0.4, 4)
    parts.append(la)

    return parts, H


def make_scene(variant):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    col = bpy.data.collections.new(f"EXPEDITION_{variant}")
    bpy.context.scene.collection.children.link(col)
    parts, H = build(variant)
    report = {}
    for p in parts:
        report[p.name] = p.tris()
        p.finish(col)
    return col, report, H


def validate(variant, report, col=None):
    v = VARIANTS[variant]
    required = ["Scar", "ScarGlow", "RiftCore", "RiftMid", "RiftHalo", "Debris", "LightAnchor"]
    required += [f"Edge{i}" for i in range(1, v["edges"] + 1)]
    required += [f"FragRock{i}" for i in range(1, v["frags"] + 1)] + [f"FragGem{i}" for i in range(1, v["frags"] + 1)]
    errors = [f"missing {n}" for n in required if n not in report]
    total = sum(report.values())
    if not TRI_MIN <= total <= TRI_MAX:
        errors.append(f"{total} tris is outside {TRI_MIN}-{TRI_MAX}")
    worst = max(report.items(), key=lambda kv: kv[1])
    if worst[1] > MESH_MAX:
        errors.append(f"{worst[0]} has {worst[1]} tris; keep every mesh under 10k")
    for name in report:
        if name.endswith((".001", ".002")):
            errors.append(f"bad name {name}")
    # FLUSH: the scar and its glow must lie on the deck. (Debris stones are
    # small rocks with some height, so they get a looser bound.)
    if col is not None:
        for name, limit in (("Scar", GROUND_MAX), ("ScarGlow", GROUND_MAX + 0.05), ("Debris", 0.6)):
            o = col.objects.get(name)
            if o:
                top = max(vt.co.z for vt in o.data.vertices)
                if top > limit:
                    errors.append(f"{name} rises {top:.2f} above the deck (limit {limit})")
    # THE PATH: fragments and their gems must stay off the walk-through lane,
    # the band |x| < half the tear's width that runs the length of Y.
    if col is not None:
        lane = v["width"] / 2 + 0.3
        for o in col.objects:
            if o.name.startswith(("FragRock", "FragGem")):
                nearest = min(abs(vt.co.x) for vt in o.data.vertices)
                if nearest < lane:
                    errors.append(f"{o.name} intrudes on the walk-through lane (|x| {nearest:.2f} < {lane:.2f})")
    return total, errors


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    which = "BOTH"
    if "--variant" in argv:
        which = argv[argv.index("--variant") + 1].upper()
    variants = ["ENTRANCE", "EXIT"] if which == "BOTH" else [which]
    failed = False
    for variant in variants:
        col, report, H = make_scene(variant)
        total, errors = validate(variant, report, col)
        print(f"[{variant}] {len(report)} parts, {total} tris, tear height {H:.1f}")
        for n, t in sorted(report.items(), key=lambda kv: -kv[1])[:6]:
            print(f"    {n}: {t}")
        for e in errors:
            print(f"  ERROR {e}")
            failed = True
        if "--save" in argv:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"expedition_{variant.lower()}.blend"))
        if "--export" in argv:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            bpy.ops.object.select_all(action="DESELECT")
            for o in col.objects:
                o.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(EXPORT_DIR, f"EXPEDITION_{variant}.fbx"),
                use_selection=True, global_scale=1.0, apply_unit_scale=True,
                mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
                axis_forward="-Z", axis_up="Y",
            )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
