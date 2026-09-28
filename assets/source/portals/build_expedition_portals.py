"""THE EXPEDITION PORTALS (build spec §7.8): the ENTRANCE and the EXIT.

Two authored portals, each ONE model of separate named meshes in the same
contract as the Fate Engine (docs/FATE_ENGINE_BLENDER_PROMPT.md), so PortalRig
and HubEffects-style code can spin, tint and open them by name:

    ENTRANCE  always open, the way home. Target 10-14k triangles.
    EXIT      opens where the boss fell. Target 18-25k triangles. Adds the
              iris Blade1..8 that seal the aperture until the boss is dead.

Authored in STUDS (1 Blender unit = 1 stud; the export lands 1:1). The walk
plane is z = 0 at the portal's centre. Blender +Y is the walk-through axis
(the rings' axis); the ring plane is XZ, centred at z = RING_HEIGHT.

FLUSH (owner, 2026-09-28: "should NOT float above the chunk; it should be part
of the chunk, flush"). `Foundation` is a slab BELOW z = 0 that the code sinks
into the chunk's deck; `Plinth` rises only a couple of studs, as a shallow
stepped rim a character walks onto. Nothing in the model sits above z = 0
without standing on those two.

CONTRACT (all one flat model; names are exact, no .001 suffixes)
    Foundation   static, buried under the deck. Not collidable.
    Plinth       PrimaryPart, the only collidable part.
    OuterRing    spins about its own Y axis
    InnerRing    counter-spins, TINTED per rarity
    PortalPlane  TINTED, transparency pulses, carries light and particles
    Rune1..8     static (plinth rim)
    Glyph1..8    TINTED (float over the runes)
    Shard1..6    TINTED, spin slowly about their own vertical axis
    RingFoot1..2 static struts the ring stands in
    Blade1..8    EXIT only: iris shutters. Sealed = closed over the aperture;
                 open = slid radially outward into the OuterRing. Pure
                 translation, so no hinge pivot survives (or fails) FBX.

TINTED parts are near-white and untextured on purpose: a SurfaceAppearance
overrides Color and would kill the per-rarity reskin.

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
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EXPORT_DIR = os.path.join(REPO, "assets", "export", "portals")

TRI_MIN, TRI_MAX = 10_000, 25_000

# (rgb 0-255, emissive). House palette: the Fate Engine as painted in game.
PALETTE = {
    "Basalt": ((64, 58, 78), False),
    "BasaltLight": ((88, 82, 104), False),
    "Marble": ((226, 221, 234), False),
    "MarbleDim": ((196, 190, 208), False),
    "Gold": ((230, 178, 74), False),
    "Inlay": ((68, 135, 123), True),
    # Near-white so a rarity Color on the part is the colour you see.
    "Tint": ((240, 240, 246), True),
}

# Per-variant dimensions, in studs.
VARIANTS = {
    "ENTRANCE": {
        "ring_out": 9.0, "ring_in": 6.8, "ring_depth": 1.6,
        "inner_out": 6.4, "inner_in": 5.6, "plane": 5.6,
        "plinth_r": 12.0, "found_r": 14.0,
        "ring_segs": 48, "inner_segs": 96, "teeth": 24, "pylon_tiers": 5,
        "blades": False, "shards": 6, "detail": 1.0,
    },
    "EXIT": {
        "ring_out": 13.0, "ring_in": 9.8, "ring_depth": 2.4,
        "inner_out": 9.2, "inner_in": 8.0, "plane": 8.0,
        "plinth_r": 17.0, "found_r": 19.5,
        "ring_segs": 72, "inner_segs": 144, "teeth": 36, "pylon_tiers": 8,
        "blades": True, "shards": 6, "detail": 1.6,
    },
}

PLINTH_HEIGHT = 1.8    # total rim height; the game caps the step at 3
FOUNDATION_DEPTH = 4.0
SINK = 0.15            # ring stands this far into the plinth


class Mesh:
    """One named object's geometry, built from primitives into one bmesh."""

    def __init__(self, name, mat):
        self.name, self.mat = name, mat
        self.bm = bmesh.new()

    def _face(self, pts):
        vs = [self.bm.verts.new(p) for p in pts]
        try:
            self.bm.faces.new(vs)
        except ValueError:
            pass

    def box(self, centre, size, yaw=0.0, pitch=0.0):
        """Axis box, optionally turned about Z (yaw) then X (pitch)."""
        sx, sy, sz = (s / 2 for s in size)
        corners = [Vector((x * sx, y * sy, z * sz)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        rot = Matrix.Rotation(yaw, 3, "Z") @ Matrix.Rotation(pitch, 3, "X")
        pts = [rot @ c + Vector(centre) for c in corners]
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for q in idx:
            self._face([pts[i] for i in q])

    def sweep_panel(self, centre, ang, tangent, radial, thick):
        """A flat slab lying in a ring face: radial along the ring's spoke,
        tangential along the rim, thin along Y."""
        rot = Matrix.Rotation(-ang, 3, "Y")
        # ring plane is XZ; spoke direction is (cos a, 0, sin a)
        sx, sy, sz = radial / 2, thick / 2, tangent / 2
        corners = [Vector((x * sx, y * sy, z * sz)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        pts = [rot @ c + Vector(centre) for c in corners]
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for q in idx:
            self._face([pts[i] for i in q])

    def frustum(self, centre, r0, r1, z0, z1, sides, rot=0.0):
        """A vertical tapered prism about a vertical axis, capped."""
        cx, cy = centre[0], centre[1]
        lo = [(cx + r0 * math.cos(rot + 2 * math.pi * i / sides), cy + r0 * math.sin(rot + 2 * math.pi * i / sides), z0) for i in range(sides)]
        hi = [(cx + r1 * math.cos(rot + 2 * math.pi * i / sides), cy + r1 * math.sin(rot + 2 * math.pi * i / sides), z1) for i in range(sides)]
        for i in range(sides):
            j = (i + 1) % sides
            self._face([lo[i], lo[j], hi[j], hi[i]])
        if r0 > 0:
            self._face(list(reversed(lo)))
        if r1 > 0:
            self._face(hi)

    def bipyramid(self, centre, radius, half_height, sides):
        """A faceted crystal: point, ring, ring, point. 4 * sides triangles."""
        c = Vector(centre)
        top, bot = c + Vector((0, 0, half_height)), c - Vector((0, 0, half_height))
        up = [c + Vector((radius * math.cos(2 * math.pi * i / sides), radius * math.sin(2 * math.pi * i / sides), half_height * 0.25)) for i in range(sides)]
        dn = [c + Vector((radius * math.cos(2 * math.pi * i / sides), radius * math.sin(2 * math.pi * i / sides), -half_height * 0.25)) for i in range(sides)]
        for i in range(sides):
            j = (i + 1) % sides
            self._face([top, up[i], up[j]])
            self._face([up[i], dn[i], dn[j], up[j]])
            self._face([bot, dn[j], dn[i]])

    def sweep(self, profile, segs, radius_z, arc=(0.0, 2 * math.pi), closed=True):
        """Sweeps a closed (d, a) profile round the Y axis at height radius_z.

        d is distance from the ring centre in the ring plane (XZ), a is
        displacement along Y (the walk-through axis)."""
        a0, a1 = arc
        n = len(profile)
        rings = []
        steps = segs if (a1 - a0) >= 2 * math.pi - 1e-6 else segs + 1
        for s in range(steps):
            phi = a0 + (a1 - a0) * s / segs
            rings.append([Vector((d * math.cos(phi), a, radius_z + d * math.sin(phi))) for d, a in profile])
        cnt = segs if steps == segs else segs
        for s in range(cnt):
            t = (s + 1) % steps
            for k in range(n):
                m = (k + 1) % n
                self._face([rings[s][k], rings[t][k], rings[t][m], rings[s][m]])
        if steps != segs:
            self._face(list(reversed(rings[0])))
            self._face(rings[-1])

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


def ring_profile(r_in, r_out, depth, bevel):
    """A chamfered rectangular cross-section, (d, a) pairs."""
    h = depth / 2
    b = min(bevel, (r_out - r_in) / 2 - 1e-3, h - 1e-3)
    return [
        (r_in + b, -h), (r_out - b, -h), (r_out, -h + b), (r_out, h - b),
        (r_out - b, h), (r_in + b, h), (r_in, h - b), (r_in, -h + b),
    ]


def build(variant):
    v = VARIANTS[variant]
    detail = v["detail"]
    rng = random.Random(7 if variant == "ENTRANCE" else 11)
    H = PLINTH_HEIGHT - SINK + v["ring_out"]  # ring centre height
    parts = []

    # --- Foundation: buried, hides the seam with the deck --------------------
    m = Mesh("Foundation", "Basalt")
    tiers = [(v["found_r"], v["found_r"] - 0.6, -FOUNDATION_DEPTH, -1.5), (v["found_r"] - 0.6, v["found_r"] - 1.4, -1.5, 0.0)]
    for r0, r1, z0, z1 in tiers:
        m.frustum((0, 0, 0), r0, r1, z0, z1, 32, rot=math.pi / 32)
    # Buried ribs: give the slab something to be, and the mesh its detail.
    for i in range(int(32 * detail)):
        a = 2 * math.pi * i / int(32 * detail)
        m.box((math.cos(a) * (v["found_r"] - 0.9), math.sin(a) * (v["found_r"] - 0.9), -1.2), (1.4, 0.7, 1.0), yaw=a)
    parts.append(m)

    # --- Plinth: shallow stepped rim, the collidable floor -------------------
    m = Mesh("Plinth", "Marble")
    steps = 4
    for s in range(steps):
        r0 = v["plinth_r"] - s * 1.1
        r1 = r0 - 0.5
        z0 = PLINTH_HEIGHT * s / steps
        z1 = PLINTH_HEIGHT * (s + 1) / steps
        m.frustum((0, 0, 0), r0, r1, z0, z1, 16, rot=math.pi / 16)
    # Radial inlay grooves worked into the top step.
    for i in range(int(16 * detail)):
        a = 2 * math.pi * i / int(16 * detail)
        m.box((math.cos(a) * v["plinth_r"] * 0.55, math.sin(a) * v["plinth_r"] * 0.55, PLINTH_HEIGHT + 0.04), (v["plinth_r"] * 0.55, 0.32, 0.1), yaw=a)
    tiles = int(32 * detail)
    for i in range(tiles):
        a = 2 * math.pi * (i + 0.5) / tiles
        d = v["plinth_r"] * 0.78
        m.box((d * math.cos(a), d * math.sin(a), PLINTH_HEIGHT + 0.06), (2.2, 1.5, 0.14), yaw=a)
    bollards = int(24 * detail)
    for i in range(bollards):
        a = 2 * math.pi * (i + 0.5) / bollards
        d = v["plinth_r"] - 0.55
        m.frustum((d * math.cos(a), d * math.sin(a), 0), 0.34, 0.2, PLINTH_HEIGHT * 0.25, PLINTH_HEIGHT * 0.25 + 0.9, 6, rot=a)
        m.bipyramid(Vector((d * math.cos(a), d * math.sin(a), PLINTH_HEIGHT * 0.25 + 1.25)), 0.2, 0.32, 4)
    parts.append(m)

    # --- Rings ---------------------------------------------------------------
    m = Mesh("OuterRing", "BasaltLight")
    m.sweep(ring_profile(v["ring_in"], v["ring_out"], v["ring_depth"], 0.35), v["ring_segs"], H)
    # Teeth on the rim and keystones every eighth of the ring.
    for i in range(v["teeth"]):
        a = 2 * math.pi * i / v["teeth"]
        d = v["ring_out"] + 0.25
        big = i % 3 == 0
        s = (0.9 if big else 0.55) * (1.0 + 0.3 * (detail - 1))
        # A tooth is a small bipyramid pointing away from the hub.
        c = Vector((d * math.cos(a), 0, H + d * math.sin(a)))
        m.bipyramid(c, s * 0.5, s * 1.1, 6 if big else 4)
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        d = (v["ring_in"] + v["ring_out"]) / 2
        m.box((d * math.cos(a), -v["ring_depth"] / 2 - 0.12, H + d * math.sin(a)), (1.4, 0.24, 1.4), yaw=0.0)
        m.box((d * math.cos(a), v["ring_depth"] / 2 + 0.12, H + d * math.sin(a)), (1.4, 0.24, 1.4), yaw=0.0)
    # Carved panels round both faces, and studs along the inner lip.
    span = (v["ring_out"] - v["ring_in"]) * 0.62
    chord = 2 * math.pi * (v["ring_in"] + v["ring_out"]) / 2 / v["ring_segs"] * 0.72
    for i in range(v["ring_segs"]):
        a = 2 * math.pi * (i + 0.5) / v["ring_segs"]
        d = (v["ring_in"] + v["ring_out"]) / 2
        for y in (-1, 1):
            c = Vector((d * math.cos(a), y * (v["ring_depth"] / 2 + 0.06), H + d * math.sin(a)))
            m.sweep_panel(c, a, chord, span, 0.12)
        e = v["ring_in"] + 0.05
        m.bipyramid(Vector((e * math.cos(a), 0, H + e * math.sin(a))), 0.26, 0.5, 5)
    parts.append(m)

    m = Mesh("InnerRing", "Tint")
    m.sweep(ring_profile(v["inner_in"], v["inner_out"], 0.5, 0.1), v["inner_segs"], H)
    for i in range(v["inner_segs"] // 2):
        a = 2 * math.pi * i / (v["inner_segs"] // 2)
        d = v["inner_in"] - 0.15
        m.bipyramid(Vector((d * math.cos(a), 0, H + d * math.sin(a))), 0.16, 0.36, 4)
    parts.append(m)

    m = Mesh("PortalPlane", "Tint")
    rings_r = [0.0, v["plane"] * 0.34, v["plane"] * 0.68, v["plane"]]
    segs = 48
    for k in range(len(rings_r) - 1):
        for i in range(segs):
            a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
            p = lambda r, a: (r * math.cos(a), 0.0, H + r * math.sin(a))
            if k == 0:
                m._face([p(0, 0), p(rings_r[1], a0), p(rings_r[1], a1)])
            else:
                m._face([p(rings_r[k], a0), p(rings_r[k + 1], a0), p(rings_r[k + 1], a1), p(rings_r[k], a1)])
    parts.append(m)

    # Feet: struts the ring stands in, so it reads as seated, not hovering.
    for n, sx in enumerate((-1, 1), start=1):
        m = Mesh(f"RingFoot{n}", "Basalt")
        for t in range(v["pylon_tiers"]):
            f = t / max(1, v["pylon_tiers"] - 1)
            r0 = 2.2 - 1.2 * f
            step = v["ring_out"] * 0.42 / v["pylon_tiers"]
            z0 = PLINTH_HEIGHT * 0.3 + t * step
            cx = sx * (v["ring_out"] * 0.62)
            m.frustum((cx, 0, 0), r0, r0 - 0.15, z0, z0 + step * 0.86, 8, rot=t * 0.2)
            m.frustum((cx, 0, 0), r0 + 0.22, r0 + 0.22, z0 + step * 0.86, z0 + step, 8, rot=t * 0.2)
            for k in range(int(8 * detail)):
                b = 2 * math.pi * k / int(8 * detail) + t * 0.2
                m.box((cx + (r0 + 0.1) * math.cos(b), (r0 + 0.1) * math.sin(b), z0 + step * 0.45), (0.28, 0.28, step * 0.5), yaw=b)
        top = PLINTH_HEIGHT * 0.3 + v["ring_out"] * 0.42
        m.bipyramid(Vector((sx * (v["ring_out"] * 0.62), 0, top + 1.4)), 0.7 * detail, 1.5 * detail, 8)
        parts.append(m)

    # --- Runes and glyphs on the plinth rim ---------------------------------
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        d = v["plinth_r"] - 2.3
        m = Mesh(f"Rune{i + 1}", "Gold")
        cx, cy = d * math.cos(a), d * math.sin(a)
        m.box((cx, cy, PLINTH_HEIGHT + 0.35), (1.6, 1.6, 0.7), yaw=a)
        m.box((cx, cy, PLINTH_HEIGHT + 0.85), (1.0, 1.0, 0.3), yaw=a + math.pi / 4)
        m.frustum((cx, cy, 0), 0.5, 0.05, PLINTH_HEIGHT + 1.0, PLINTH_HEIGHT + 1.9 * detail, 6, rot=a)
        parts.append(m)
        g = Mesh(f"Glyph{i + 1}", "Tint")
        g.bipyramid(Vector((cx, cy, PLINTH_HEIGHT + 3.2 * detail)), 0.42 * detail, 0.9 * detail, 6)
        parts.append(g)

    # --- Shards: free-floating crystals around the ring ---------------------
    for i in range(v["shards"]):
        a = 2 * math.pi * i / v["shards"] + 0.3
        d = v["ring_out"] * 1.35
        h = H + math.sin(i * 1.7) * v["ring_out"] * 0.3
        m = Mesh(f"Shard{i + 1}", "Tint")
        sides = 6 if variant == "ENTRANCE" else 8
        rr = 0.7 * detail * (0.9 + 0.2 * rng.random())
        m.bipyramid(Vector((d * math.cos(a), d * math.sin(a) * 0.6, h)), rr, rr * 2.4, sides)
        for k in range(int(4 * detail)):
            b = 2 * math.pi * k / int(4 * detail)
            m.bipyramid(Vector((d * math.cos(a) + math.cos(b) * rr * 1.3, d * math.sin(a) * 0.6 + math.sin(b) * rr * 1.3, h - rr * 0.6)), rr * 0.32, rr * 0.9, 4)
        parts.append(m)

    # --- SpotAnchor: a tiny hidden marker the code hangs the light from ------
    m = Mesh("SpotAnchor", "Basalt")
    m.box((0, 0, H + v["ring_out"] * 1.6), (0.4, 0.4, 0.4))
    parts.append(m)

    # --- EXIT only: the iris that seals the aperture -------------------------
    if v["blades"]:
        blades = 8
        for i in range(blades):
            a = 2 * math.pi * i / blades
            m = Mesh(f"Blade{i + 1}", "BasaltLight")
            r0, r1 = 0.0, v["ring_in"] + 0.1
            half = math.pi / blades
            # A wedge lying in the XZ plane, thin along Y.
            steps = 6
            for s in range(steps):
                ra, rb = r0 + (r1 - r0) * s / steps, r0 + (r1 - r0) * (s + 1) / steps
                pts = lambda r, ang, y: (r * math.cos(ang), y, H + r * math.sin(ang))
                for y0, y1, sgn in ((-0.35, 0.35, 1),):
                    m._face([pts(ra, a - half, y1), pts(rb, a - half, y1), pts(rb, a + half, y1), pts(ra, a + half, y1)])
                    m._face([pts(ra, a + half, y0), pts(rb, a + half, y0), pts(rb, a - half, y0), pts(ra, a - half, y0)])
                    m._face([pts(rb, a - half, y0), pts(rb, a + half, y0), pts(rb, a + half, y1), pts(rb, a - half, y1)])
                    m._face([pts(ra, a - half, y1), pts(ra, a + half, y1), pts(ra, a + half, y0), pts(ra, a - half, y0)])
                    m._face([pts(ra, a - half, y0), pts(rb, a - half, y0), pts(rb, a - half, y1), pts(ra, a - half, y1)])
                    m._face([pts(ra, a + half, y1), pts(rb, a + half, y1), pts(rb, a + half, y0), pts(ra, a + half, y0)])
            # Ridge lines on the face: gold studs along the wedge's spine.
            for s in range(1, 9):
                r = r1 * s / 9
                m.bipyramid(Vector((r * math.cos(a), -0.55, H + r * math.sin(a))), 0.22, 0.4, 4)
            parts.append(m)

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


def validate(variant, report):
    v = VARIANTS[variant]
    required = ["Foundation", "Plinth", "OuterRing", "InnerRing", "PortalPlane", "RingFoot1", "RingFoot2", "SpotAnchor"]
    required += [f"Rune{i}" for i in range(1, 9)] + [f"Glyph{i}" for i in range(1, 9)] + [f"Shard{i}" for i in range(1, v["shards"] + 1)]
    if v["blades"]:
        required += [f"Blade{i}" for i in range(1, 9)]
    errors = [f"missing {n}" for n in required if n not in report]
    total = sum(report.values())
    if not TRI_MIN <= total <= TRI_MAX:
        errors.append(f"{total} tris is outside {TRI_MIN}-{TRI_MAX}")
    worst = max(report.items(), key=lambda kv: kv[1])
    if worst[1] > 10_000:
        errors.append(f"{worst[0]} has {worst[1]} tris; keep every mesh under 10k")
    for name in report:
        if name.endswith((".001", ".002")):
            errors.append(f"bad name {name}")
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
        total, errors = validate(variant, report)
        print(f"[{variant}] {len(report)} parts, {total} tris, ring centre z={H:.2f}")
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
