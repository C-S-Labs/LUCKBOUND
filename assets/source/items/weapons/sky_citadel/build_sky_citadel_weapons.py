"""Sky Citadel weapons -- generator.

Run inside Blender (tested on 5.2 LTS), e.g. through the Blender MCP:

    ns = {"__name__": "sc_weapons"}
    exec(open(r"<repo>/assets/source/items/weapons/sky_citadel/build_sky_citadel_weapons.py").read(), ns)
    ns["main"]()

or from a shell:

    blender --background --python build_sky_citadel_weapons.py -- --export

It rebuilds every weapon from scratch each run, so the .blend next to this
file is an OUTPUT, not a source. docs/WEAPONS.md is the contract this script
implements; docs/biomes/SKY_CITADEL.md is the look. The geometry helpers are
copied from (not imported from) ../../../worlds/sky_citadel/build_sky_citadel_kit.py,
so the two scripts share one hand without depending on each other.

What it guarantees, and checks before it will export (`validate()`):

* One mesh per weapon (gauntlets: one per hand), parented to one armature
  with an Armature modifier. Names exactly as WEAPONS.md s6, no `.001`.
* Origin at the grip point (Root's head); length along +Z, within the type's
  range; the striking edge or face toward -Y.
* Under 10,000 triangles per mesh (refused), and within the tier target
  (warned).
* Flat shading, one palette colour per face (material + baked vertex colour),
  no textures.
* Rigid weights: every vertex in exactly one vertex group at 1.0, named for a
  bone from the WEAPONS.md s4 vocabulary. Every moving part is its own closed
  shell on its own bone. Fx_ sockets and Root carry no geometry.
* The rarity ladder of WEAPONS.md s2.
* No animation, actions, constraints, drivers or shape keys; rest pose.

Axes: Blender +Y is Roblox NORTH (-Z) under the -Z Forward / Y Up export,
Blender +X is Roblox +X, exactly as the island kit.
"""

import math
import os
import re
import random
from contextlib import contextmanager

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

# --------------------------------------------------------------------------
# Paths and limits
# --------------------------------------------------------------------------

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")) \
    if "__file__" in globals() else os.getcwd()
SOURCE_DIR = os.path.join(REPO, "assets", "source", "items", "weapons", "sky_citadel")
EXPORT_DIR = os.path.join(REPO, "assets", "export", "items", "weapons", "sky_citadel")
BLEND_PATH = os.path.join(SOURCE_DIR, "sky_citadel_weapons.blend")
MANIFEST_PATH = os.path.join(SOURCE_DIR, "WEAPONS_MANIFEST.md")

TRI_LIMIT = 10000
TIER_TRIS = {"common": 1200, "uncommon": 2000, "rare": 3500, "epic": 6000}
RARITIES = ("common", "uncommon", "rare", "epic")

# (singular, plural collection suffix, length range in studs)
TYPES = {
    "sword": ("Swords", (3.6, 4.6)),
    "greatsword": ("Greatswords", (5.2, 6.8)),
    "dagger": ("Daggers", (1.6, 2.4)),
    "hammer": ("Hammers", (3.4, 5.0)),
    "staff": ("Staves", (5.0, 6.8)),
    "bow": ("Bows", (4.0, 5.2)),
    "gauntlets": ("Gauntlets", (1.8, 2.6)),
}
TYPE_ORDER = list(TYPES.keys())

# Review layout: one row per type along +Y (Common -> Epic), rows stepped
# along +X, everything lifted so nothing sits under the floor. Weapons show
# their flats to +X, so the review view looks from +X, where +Y is screen right.
REVIEW_ROW_X0 = 4.0
REVIEW_ROW_STEP = 6.0
REVIEW_Y0 = 2.5
REVIEW_Y_STEP = 2.5
REVIEW_Z = 1.5

# --------------------------------------------------------------------------
# Palette. Copied verbatim from the island kit (docs/biomes/SKY_CITADEL.md).
# sRGB 0-255, (rgb, emissive).
# --------------------------------------------------------------------------

PALETTE = {
    "CitadelWhite": ((232, 236, 244), False),  # decks, walls, spire shafts
    "PaleAlloy": ((176, 188, 210), False),     # trim, railings, plinths, caps
    "DeepAlloy": ((92, 104, 134), False),      # structural dark: bands, fins, poles
    "HullSlate": ((118, 124, 156), False),     # the floating keel under every deck
    "SunGold": ((236, 190, 92), False),        # the one warm accent -- sparingly
    "AzureNeon": ((120, 210, 255), True),      # SMALL emissive accents only
    "AzureDim": ((70, 128, 168), True),        # large emissive strips and inlays
    "CitadelViolet": ((138, 96, 210), False),  # roofs and banners
    "SkyGlass": ((178, 222, 242), False),      # floating crystals, fountain water
    "Verdure": ((96, 156, 124), False),        # clipped topiary in planters
    "VaultDark": ((16, 16, 24), False),        # the inside of the treasury vault
}
MAT_ORDER = list(PALETTE.keys())
EMISSIVE = {k for k, (_, e) in PALETTE.items() if e}
RGB_TO_NAME = {rgb: k for k, (rgb, _) in PALETTE.items()}


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def ensure_materials():
    mats = {}
    for name, (rgb, emissive) in PALETTE.items():
        mname = "SC_" + name
        m = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        lin = [srgb_to_linear(v) for v in rgb] + [1.0]
        bsdf.inputs["Base Color"].default_value = lin
        bsdf.inputs["Roughness"].default_value = 0.75
        emit_in = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if emissive:
            emit_in.default_value = lin
            bsdf.inputs["Emission Strength"].default_value = 2.5
        else:
            bsdf.inputs["Emission Strength"].default_value = 0.0
        m.diffuse_color = lin
        mats[name] = m
    return mats


# --------------------------------------------------------------------------
# Bone vocabulary (WEAPONS.md s4)
# --------------------------------------------------------------------------

FINGERS = ("Thumb", "Index", "Middle", "RingFinger", "Pinky")
VOCAB_ALL = {"Root", "Core"}
VOCAB = {
    "sword": {"Grip", "Blade", "Guard", "Pommel", "Fx_Base", "Fx_Tip"},
    "greatsword": {"Grip", "Blade", "Guard", "Pommel", "Fx_Base", "Fx_Tip"},
    "dagger": {"Grip", "Blade", "Guard", "Pommel", "Fx_Base", "Fx_Tip"},
    "hammer": {"Haft", "Head", "Fx_Strike"},
    "staff": {"Shaft", "Head", "Core", "Fx_Cast"},
    "bow": {"Grip", "Limb_Upper", "Limb_Upper_Tip", "Limb_Lower", "Limb_Lower_Tip",
            "String_Nock", "Fx_Rest", "Fx_Nock"},
    "gauntlets": {"Cuff", "Hand", "Fx_Knuckles"} | {"%s_%d" % (f, i) for f in FINGERS for i in (1, 2)},
}
REQUIRED = {
    "sword": {"Root", "Grip", "Blade", "Fx_Base", "Fx_Tip"},
    "greatsword": {"Root", "Grip", "Blade", "Fx_Base", "Fx_Tip"},
    "dagger": {"Root", "Grip", "Blade", "Fx_Base", "Fx_Tip"},
    "hammer": {"Root", "Haft", "Head", "Fx_Strike"},
    "staff": {"Root", "Shaft", "Head", "Fx_Cast"},
    "bow": set(VOCAB["bow"]) | {"Root"},
    "gauntlets": set(VOCAB["gauntlets"]) | {"Root"},
}
STRUCTURAL = {"Root", "Grip", "Blade", "Haft", "Shaft", "Cuff", "Hand"}
NUMBERED = re.compile(r"^(Float|Ring)_([1-9]\d*)$")


def bone_allowed(wtype, name):
    return name in VOCAB_ALL or name in VOCAB[wtype] or bool(NUMBERED.match(name))


def is_fx(name):
    return name.startswith("Fx_")


def is_animatable(name):
    return not is_fx(name) and name not in STRUCTURAL


# --------------------------------------------------------------------------
# Geometry accumulation. A weapon is built as one vertex/face soup in which
# every face belongs to one bone, then turned into ONE mesh object.
# --------------------------------------------------------------------------


def xf(x=0.0, y=0.0, z=0.0, rz=0.0, rx=0.0, ry=0.0):
    rot = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ").to_matrix().to_4x4()
    return Matrix.Translation((x, y, z)) @ rot


class Weapon:
    """One weapon (or one gauntlet hand) being built.

    `bone()` declares an armature bone; `on(bone)` routes geometry added
    inside it to that bone's vertex group. A face may only ever carry one
    bone -- except the bow string, whose vertices are re-weighted
    individually through `vert_bone`."""

    def __init__(self, wtype, rarity, letter, display, cid, note, hand=None):
        self.wtype, self.rarity, self.letter = wtype, rarity, letter
        self.display, self.cid, self.note = display, cid, note
        self.hand = hand
        suffix = "_" + hand if hand else ""
        self.name = "wpn_sc_%s_%s_%s%s" % (wtype, rarity, letter, suffix)
        self.rig_name = "rig_" + self.name[len("wpn_"):]
        self.verts = []
        self.faces = []
        self.fmat = []
        self.fbone = []
        self.vert_bone = {}      # per-vertex override (bow string only)
        self.bones = {}          # name -> (head, tail, parent, deform)
        self.order = []
        self.cur = None
        self.rng = random.Random(self.name)   # seeded by name: rebuilds are identical

    def bone(self, name, head, tail, parent=None, deform=True):
        if name in self.bones:
            raise ValueError("%s: bone %s declared twice" % (self.name, name))
        self.bones[name] = (Vector(head), Vector(tail), parent, deform)
        self.order.append(name)

    def fx(self, name, head, direction=(0, 0, 1), parent="Root", length=0.15):
        h = Vector(head)
        self.bone(name, h, h + Vector(direction).normalized() * length, parent, deform=False)

    @contextmanager
    def on(self, bone):
        prev, self.cur = self.cur, bone
        try:
            yield
        finally:
            self.cur = prev

    def add(self, verts, faces, mat, M):
        if self.cur is None:
            raise ValueError("%s: geometry added outside a bone" % self.name)
        if mat not in PALETTE:
            raise ValueError("%s: %s is not a palette colour" % (self.name, mat))
        base = len(self.verts)
        self.verts.extend(M @ Vector(v) for v in verts)
        self.faces.extend([base + i for i in f] for f in faces)
        self.fmat.extend([mat] * len(faces))
        self.fbone.extend([self.cur] * len(faces))
        return base

    def mirror_x(self):
        """The left gauntlet: the right one mirrored in X, bone names kept."""
        self.verts = [Vector((-v.x, v.y, v.z)) for v in self.verts]
        self.faces = [list(reversed(f)) for f in self.faces]
        for k, (h, t, par, d) in list(self.bones.items()):
            self.bones[k] = (Vector((-h.x, h.y, h.z)), Vector((-t.x, t.y, t.z)), par, d)


# --------------------------------------------------------------------------
# Primitives. box / frustum / torus / torus_arc / crystal / orb are the
# island kit's, taking a final matrix M so a piece can be placed anywhere.
# loft / tube / blade are new: swept shapes the island never needed.
# Every primitive emits one closed shell.
# --------------------------------------------------------------------------

I4 = Matrix.Identity(4)


def box(w, mat, cx, cy, cz, sx, sy, sz, rz=0.0, rx=0.0, ry=0.0, M=I4):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    w.add(v, f, mat, M @ xf(cx, cy, cz, rz, rx, ry))


def frustum(w, mat, n, r0, r1, z0, z1, cx=0.0, cy=0.0, rot=None, M=I4, sx=1.0, sy=1.0):
    """n-sided prism/cone/pyramid from z0 (radius r0) to z1 (radius r1).
    rot defaults to half a step, so n = 4 and n = 8 have flat faces on the
    axes. A radius of 0 makes an apex. sx/sy squash the section."""
    if rot is None:
        rot = 180.0 / n

    def ring(r, z):
        if r <= 1e-6:
            return [(0.0, 0.0, z)]
        return [(r * sx * math.cos(math.radians(rot + 360.0 * i / n)),
                 r * sy * math.sin(math.radians(rot + 360.0 * i / n)), z) for i in range(n)]

    loft(w, mat, [ring(r0, z0), ring(r1, z1)], M @ xf(cx, cy))


def torus(w, mat, R, r, cx, cy, cz, n=16, m=4, rx=0.0, ry=0.0, rz=0.0, M=I4):
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        for j in range(m):
            b = 2 * math.pi * j / m + math.pi / m
            d = R + r * math.cos(b)
            verts.append((d * math.cos(a), d * math.sin(a), r * math.sin(b)))
    for i in range(n):
        for j in range(m):
            i2, j2 = (i + 1) % n, (j + 1) % m
            faces.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    w.add(verts, faces, mat, M @ xf(cx, cy, cz, rz, rx, ry))


def torus_arc(w, mat, R, r, cx, cy, cz, a0, a1, n=16, m=4, rx=0.0, ry=0.0, rz=0.0, M=I4):
    """Part of a ring, a0..a1 degrees in its own plane, ends capped."""
    verts, faces = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        for j in range(m):
            b = 2 * math.pi * j / m + math.pi / m
            d = R + r * math.cos(b)
            verts.append((d * math.cos(a), d * math.sin(a), r * math.sin(b)))
    for i in range(n):
        for j in range(m):
            j2 = (j + 1) % m
            faces.append((i * m + j, (i + 1) * m + j, (i + 1) * m + j2, i * m + j2))
    faces.append(tuple(range(m)))
    faces.append(tuple(reversed(range(n * m, n * m + m))))
    w.add(verts, faces, mat, M @ xf(cx, cy, cz, rz, rx, ry))


def crystal(w, mat, cx, cy, cz, r, up, down, n=4, rz=0.0, M=I4):
    verts = [(0, 0, up), (0, 0, -down)]
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((r * math.cos(a), r * math.sin(a), 0))
    faces = []
    for i in range(n):
        a, b = 2 + i, 2 + (i + 1) % n
        faces.append((0, a, b))
        faces.append((1, b, a))
    w.add(verts, faces, mat, M @ xf(cx, cy, cz, rz))


def orb(w, mat, x, y, z, r, n=8, M=I4):
    """A low-poly ball as ONE closed shell (the kit's is three frustums)."""
    k = 0.35
    loft(w, mat, [
        [(x, y, z - r)],
        [(x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a), z - r * 0.8) for a in _angles(n)],
        [(x + r * math.cos(a), y + r * math.sin(a), z - r * k) for a in _angles(n)],
        [(x + r * math.cos(a), y + r * math.sin(a), z + r * k) for a in _angles(n)],
        [(x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a), z + r * 0.8) for a in _angles(n)],
        [(x, y, z + r)],
    ], M)


def _angles(n, rot=None):
    if rot is None:
        rot = 180.0 / n
    return [math.radians(rot + 360.0 * i / n) for i in range(n)]


def loft(w, mat, rings, M=I4):
    """Skin a list of rings (each a list of 3D points with the same count, or
    a single point for an apex) into one closed shell."""
    verts, idx = [], []
    for r in rings:
        s = len(verts)
        verts.extend(tuple(v) for v in r)
        idx.append(list(range(s, s + len(r))))
    faces = []
    for A, B in zip(idx, idx[1:]):
        if len(A) > 1 and len(B) > 1:
            n = len(A)
            faces += [(A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]) for i in range(n)]
        elif len(A) == 1:
            n = len(B)
            faces += [(A[0], B[(i + 1) % n], B[i]) for i in range(n)]
        else:
            n = len(A)
            faces += [(A[i], A[(i + 1) % n], B[0]) for i in range(n)]
    if len(idx[0]) > 1:
        faces.append(tuple(reversed(idx[0])))
    if len(idx[-1]) > 1:
        faces.append(tuple(idx[-1]))
    w.add(verts, faces, mat, M)


def tube(w, mat, pts, radii, n=8, sx=1.0, ref=(1, 0, 0), rot=None, M=I4):
    """An n-gon swept along a polyline (parallel-transported frame). The
    frame's first axis starts along `ref` and is scaled by sx (a flattened
    limb or quillon). A radius of 0 at an end makes a point."""
    pts = [Vector(p) for p in pts]
    ref = Vector(ref)
    t0 = (pts[1] - pts[0]).normalized()
    u = (ref - t0 * ref.dot(t0)).normalized()
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = t0
        elif i == len(pts) - 1:
            t = (pts[i] - pts[i - 1]).normalized()
        else:
            t = ((pts[i] - pts[i - 1]).normalized() + (pts[i + 1] - pts[i]).normalized()).normalized()
        u = (u - t * u.dot(t)).normalized()
        v = t.cross(u)
        r = radii[i]
        if r <= 1e-6:
            rings.append([tuple(p)])
        else:
            rings.append([tuple(p + (u * math.cos(a) * sx + v * math.sin(a)) * r) for a in _angles(n, rot)])
    loft(w, mat, rings, M)


def hex_section(hw, ht, k=0.55):
    """Double-edged blade section: edges at +/-Y (width hw), flats facing
    +/-X (half-thickness ht)."""
    return [(0.0, -hw), (ht, -hw * k), (ht, hw * k), (0.0, hw), (-ht, hw * k), (-ht, -hw * k)]


def single_section(y_edge, y_back, ht, bevel=0.35):
    """Single-edged section: the edge at -Y (y_edge < y_back), a flat back."""
    ye = y_edge + (y_back - y_edge) * bevel
    return [(0.0, y_edge), (ht, ye), (ht, y_back), (-ht, y_back), (-ht, ye)]


def blade(w, mat, sections, M=I4):
    """sections: [(z, [(x, y), ...]) ...]; a section of one point is the tip."""
    loft(w, mat, [[(x, y, z) for x, y in pts] for z, pts in sections], M)


def lathe(w, mat, n, profile, rot=None, sx=1.0, sy=1.0, M=I4):
    """An n-gon turned along Z through (z, r) stations: grips, pommels."""
    rings = []
    for z, r in profile:
        if r <= 1e-6:
            rings.append([(0.0, 0.0, z)])
        else:
            rings.append([(r * sx * math.cos(a), r * sy * math.sin(a), z) for a in _angles(n, rot)])
    loft(w, mat, rings, M)


def inlay(w, mat, ht, y0, y1, z0, z1, width, proud=0.006, t=0.01):
    """A strip set into both flats of a blade, standing `proud` above the
    flat at x = +/-ht: a straight line from (y0, z0) to (y1, z1)."""
    L = math.hypot(y1 - y0, z1 - z0)
    ang = math.degrees(math.atan2(y1 - y0, z1 - z0))
    for s in (1, -1):
        box(w, mat, s * (ht + proud - t / 2), (y0 + y1) / 2, (z0 + z1) / 2, t, width, L, rx=-ang)


# --------------------------------------------------------------------------
# Weapon registry
# --------------------------------------------------------------------------

WEAPONS = []   # (wtype, rarity, letter, display, cid, note, builder)


def weapon(wtype, rarity, letter, display, cid, note):
    def deco(fn):
        WEAPONS.append((wtype, rarity, letter, display, cid, note, fn))
        return fn
    return deco


def sword_bones(w, grip0, grip1, guard_z, blade0, tip, pommel=True, guard=True):
    """The blade-family skeleton. Root at the grip point (origin); Grip from
    the origin up; Guard pivots at its centre and spins about +Z; Pommel
    pivots at the grip's butt and points down; Blade from its base to the tip."""
    w.bone("Root", (0, 0, 0), (0, 0, 0.3), None, deform=False)
    w.bone("Grip", (0, 0, 0), (0, 0, grip1), "Root")
    if guard:
        w.bone("Guard", (0, 0, guard_z), (0, 0, guard_z + 0.25), "Grip")
    if pommel:
        w.bone("Pommel", (0, 0, grip0), (0, 0, grip0 - 0.2), "Grip")
    w.bone("Blade", (0, 0, blade0), (0, 0, tip), "Grip")
    w.fx("Fx_Base", (0, 0, blade0), parent="Blade")
    w.fx("Fx_Tip", (0, 0, tip), parent="Blade")


def ring_bone(w, name, centre, rx=0.0, ry=0.0, parent="Root", length=0.2, rz=0.0):
    """A halo's bone: head at its spin centre, pointing along its normal
    (the same rotation torus() is given)."""
    nrm = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ").to_matrix() @ Vector((0, 0, 1))
    c = Vector(centre)
    w.bone(name, c, c + nrm * length, parent)


# ==========================================================================
# SWORDS -- 3.6-4.6 studs. Edge toward -Y, flats toward +/-X.
# ==========================================================================


@weapon("sword", "common", "a", "Wardline Blade", "SC_SWORD_WARDLINE_BLADE",
        "Standard issue of the citadel guard: a blade that narrows in two spire tiers to its point, a chamfered bar guard and a wheel pommel.")
def sword_wardline(w):
    sword_bones(w, grip0=-0.45, grip1=0.45, guard_z=0.525, blade0=0.6, tip=3.55)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.07, 0.065, -0.45, 0.45)
        frustum(w, "PaleAlloy", 8, 0.082, 0.082, 0.36, 0.45)
        frustum(w, "PaleAlloy", 8, 0.08, 0.08, -0.45, -0.37)
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.525, 0.14, 0.86, 0.1)
        for s in (1, -1):   # chamfered octagonal end blocks
            frustum(w, "PaleAlloy", 8, 0.075, 0.075, -0.05, 0.05, M=xf(0, s * 0.47, 0.525, rx=90))
    ht = 0.055
    with w.on("Blade"):
        blade(w, "CitadelWhite", [          # two tiers, like a spire stepping in
            (0.6, hex_section(0.19, ht)),
            (2.7, hex_section(0.18, ht)),
            (2.72, hex_section(0.15, ht)),
            (3.1, hex_section(0.14, ht)),
            (3.12, hex_section(0.1, ht * 0.85)),
            (3.55, [(0.0, 0.0)]),
        ])
        box(w, "PaleAlloy", 0, 0, 0.66, 0.13, 0.3, 0.1)     # ricasso collar
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 8, 0.055, 0.055, -0.5, -0.45)
        frustum(w, "PaleAlloy", 8, 0.14, 0.14, -0.04, 0.04, M=xf(0, 0, -0.63, ry=90))   # the wheel, face to the flats


@weapon("sword", "common", "b", "Parapet Cleaver", "SC_SWORD_PARAPET_CLEAVER",
        "A broad single-edged cleaver; its back is crenellated like a parapet walk, a square alloy grip, block guard and pyramid pommel.")
def sword_parapet(w):
    sword_bones(w, grip0=-0.42, grip1=0.4, guard_z=0.48, blade0=0.58, tip=3.42)
    with w.on("Grip"):
        frustum(w, "PaleAlloy", 4, 0.075, 0.07, -0.42, 0.4, rot=45)
        for z in (-0.25, 0.0, 0.25):
            frustum(w, "DeepAlloy", 4, 0.085, 0.085, z - 0.03, z + 0.03, rot=45)
    with w.on("Guard"):
        box(w, "DeepAlloy", 0, 0.0, 0.48, 0.22, 0.62, 0.16)
        box(w, "PaleAlloy", 0, 0.0, 0.48, 0.26, 0.3, 0.12)
    ht = 0.05
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.58, single_section(-0.2, 0.17, ht)),
            (1.5, single_section(-0.27, 0.17, ht)),
            (2.6, single_section(-0.33, 0.17, ht)),
            (3.05, single_section(-0.3, 0.12, ht)),
            (3.3, single_section(-0.2, -0.02, ht * 0.8)),
            (3.42, [(0.0, -0.16)]),
        ])
        for z in (0.95, 1.35, 1.75, 2.15, 2.5):   # merlons on the back
            box(w, "PaleAlloy", 0, 0.19, z, 0.085, 0.07, 0.2)
        box(w, "PaleAlloy", 0, 0.0, 0.66, 0.12, 0.4, 0.12)   # a squared ricasso plate
    with w.on("Pommel"):
        frustum(w, "DeepAlloy", 4, 0.1, 0.16, -0.43, -0.49, rot=45)
        frustum(w, "DeepAlloy", 4, 0.16, 0.1, -0.49, -0.58, rot=45)


@weapon("sword", "uncommon", "a", "Gilded Sentinel", "SC_SWORD_GILDED_SENTINEL",
        "A leaf blade that swells toward the point with an azure fuller; a long white swell grip between gold ferrules, swept gold quillons, a faceted gold stopper.")
def sword_gilded(w):
    sword_bones(w, grip0=-0.5, grip1=0.5, guard_z=0.58, blade0=0.7, tip=3.78)
    with w.on("Grip"):
        lathe(w, "CitadelWhite", 8, [(-0.5, 0.06), (-0.3, 0.072), (0.05, 0.078), (0.35, 0.068), (0.5, 0.062)])
        frustum(w, "SunGold", 8, 0.074, 0.074, 0.43, 0.5)
        frustum(w, "SunGold", 8, 0.072, 0.072, -0.5, -0.43)
    with w.on("Guard"):
        box(w, "SunGold", 0, 0, 0.58, 0.17, 0.32, 0.13)
        for s in (1, -1):
            tube(w, "SunGold", [(0, s * 0.14, 0.58), (0, s * 0.36, 0.61), (0, s * 0.5, 0.69), (0, s * 0.56, 0.83)],
                 [0.05, 0.045, 0.035, 0.0], n=6)
    ht = 0.055
    with w.on("Blade"):
        frustum(w, "SunGold", 6, 0.17, 0.17, 0.7, 0.78, sx=0.4)   # the blade's gold collar
        blade(w, "CitadelWhite", [
            (0.7, hex_section(0.15, ht)),
            (1.6, hex_section(0.18, ht)),
            (2.8, hex_section(0.25, ht)),
            (3.3, hex_section(0.2, ht * 0.9)),
            (3.78, [(0.0, 0.0)]),
        ])
        inlay(w, "AzureDim", ht, 0.0, 0.0, 0.82, 2.95, 0.05)
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.05, 0.05, -0.56, -0.5)
        crystal(w, "SunGold", 0, 0, -0.63, 0.1, 0.08, 0.15, n=8)   # scent-stopper


@weapon("sword", "uncommon", "b", "Chevron Edge", "SC_SWORD_CHEVRON_EDGE",
        "A long diamond-section needle from a hex ricasso; the guard is the gatehouse chevron with its gold keystone, a wrapped hex grip, a hex-nut pommel.")
def sword_chevron(w):
    sword_bones(w, grip0=-0.42, grip1=0.45, guard_z=0.52, blade0=0.66, tip=3.86)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 6, 0.072, 0.068, -0.42, 0.45)
        for z in (-0.27, -0.09, 0.09, 0.27):   # slanted wraps
            frustum(w, "PaleAlloy", 6, 0.082, 0.082, -0.016, 0.016, M=xf(0, 0, z, rx=18))
    with w.on("Guard"):
        ang = math.degrees(math.atan2(0.2, 0.46))
        for s in (1, -1):
            box(w, "PaleAlloy", 0, s * 0.25, 0.575, 0.13, 0.5, 0.09, rx=s * ang)
            crystal(w, "PaleAlloy", 0, s * 0.49, 0.69, 0.06, 0.1, 0.02, n=4)
        box(w, "SunGold", 0, 0, 0.5, 0.15, 0.13, 0.13, rx=45)       # the keystone
    ht = 0.05
    with w.on("Blade"):
        frustum(w, "PaleAlloy", 6, 0.16, 0.16, 0.66, 0.92, rot=90, sx=0.45)   # hex ricasso
        blade(w, "CitadelWhite", [
            (0.9, hex_section(0.17, ht, k=0.3)),
            (1.3, hex_section(0.165, ht, k=0.3)),
            (3.35, hex_section(0.09, ht * 0.8, k=0.3)),
            (3.86, [(0.0, 0.0)]),
        ])
        inlay(w, "AzureDim", ht, 0.0, 0.0, 0.96, 3.2, 0.022)
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 6, 0.11, 0.11, -0.43, -0.52)            # hex nut
        frustum(w, "SunGold", 6, 0.08, 0.0, -0.52, -0.64)               # gold point


@weapon("sword", "rare", "a", "Turbine Warden", "SC_SWORD_TURBINE_WARDEN",
        "Four swept turbine fins brace a cradle where a glass hex core spins; a raised neon-channelled spine, a clipped point, a grip of stacked hub discs, a rotor pommel.")
def sword_turbine(w):
    sword_bones(w, grip0=-0.45, grip1=0.45, guard_z=0.47, blade0=0.8, tip=3.6)
    w.bone("Core", (0, 0, 0.615), (0, 0, 0.8), "Guard")
    with w.on("Grip"):
        for i in range(9):   # stacked hub discs
            z0 = -0.45 + 0.1 * i
            frustum(w, "DeepAlloy", 8, 0.07, 0.07, z0, z0 + 0.08)
            frustum(w, "PaleAlloy", 8, 0.082, 0.082, z0 + 0.08, z0 + 0.1)
    with w.on("Guard"):
        frustum(w, "PaleAlloy", 8, 0.1, 0.13, 0.46, 0.51)     # base plate
        frustum(w, "PaleAlloy", 8, 0.13, 0.11, 0.72, 0.77)    # top collar
        frustum(w, "SunGold", 8, 0.135, 0.135, 0.5, 0.52)     # gold band
        for k in range(4):
            M = xf(0, 0, 0, rz=90 + 90 * k)    # +Y, -X, -Y, +X
            big = k % 2 == 0          # the pair along +/-Y is the crossguard; the pair along X is shorter
            reach = 0.62 if big else 0.36
            # fin: tapered, swept up toward the blade, pitched 18 degrees about its span like a turbine blade
            pitch = xf(0, 0, 0.615) @ xf(rx=18) @ xf(0, 0, -0.615)
            tube(w, "PaleAlloy", [(0.12, 0, 0.615), (reach * 0.55, 0, 0.66), (reach, 0, 0.8 if big else 0.72)],
                 [0.1, 0.075, 0.03], n=4, sx=0.25, ref=(0, 1, 0), rot=45, M=M @ pitch)
            crystal(w, "AzureNeon", reach + 0.03, 0, 0.83 if big else 0.75, 0.035, 0.08, 0.04, n=4, M=M @ pitch)
    with w.on("Core"):
        crystal(w, "SkyGlass", 0, 0, 0.615, 0.085, 0.085, 0.085, n=6)
    ht = 0.055
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.8, hex_section(0.2, ht)),
            (2.95, hex_section(0.2, ht)),
            (3.22, hex_section(0.13, ht * 0.85)),
            (3.6, [(0.0, 0.0)]),
        ])
        inlay(w, "DeepAlloy", ht, 0.0, 0.0, 0.88, 3.0, 0.08, proud=0.014, t=0.03)       # raised spine
        for y in (-0.022, 0.022):
            inlay(w, "AzureNeon", ht, y, y, 0.95, 2.95, 0.012, proud=0.02, t=0.01)      # channels on it
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.075, 0.075, -0.46, -0.55)                             # rotor hub
        for k in range(3):
            tube(w, "PaleAlloy", [(0.06, 0, -0.505), (0.2, 0, -0.52)], [0.035, 0.012], n=4, sx=0.3,
                 ref=(0, 1, 0), M=xf(rz=120 * k + 30) @ xf(0, 0, -0.505) @ xf(rx=25) @ xf(0, 0, 0.505))
        crystal(w, "SkyGlass", 0, 0, -0.55, 0.05, 0.0, 0.12, n=6)


@weapon("sword", "epic", "a", "Spireward", "SC_SWORD_SPIREWARD",
        "A slim shouldered spire blade with a violet fuller and neon seams; a turret guard whose violet spires sweep up like wings; a halo and a smaller one orbit the blade, twin violet shards hover beside it.")
def sword_spireward(w):
    sword_bones(w, grip0=-0.5, grip1=0.45, guard_z=0.47, blade0=0.92, tip=3.72)
    ring_bone(w, "Ring_1", (0, 0, 1.45), rx=8, ry=18, parent="Blade")
    ring_bone(w, "Ring_2", (0, 0, 2.55), rx=-10, ry=-20, parent="Blade")
    w.bone("Float_1", (0, 0.52, 1.35), (0, 0.52, 1.55), "Blade")
    w.bone("Float_2", (0, -0.52, 1.35), (0, -0.52, 1.55), "Blade")
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.066, 0.066, -0.5, 0.45)
        for z in (-0.35, -0.15, 0.05, 0.25):    # violet wraps, slanted
            frustum(w, "CitadelViolet", 8, 0.074, 0.074, -0.016, 0.016, M=xf(0, 0, z, rx=20))
        frustum(w, "SunGold", 8, 0.075, 0.075, 0.39, 0.45)
    with w.on("Guard"):
        frustum(w, "CitadelWhite", 8, 0.11, 0.13, 0.47, 0.76)          # the turret drum
        frustum(w, "AzureNeon", 8, 0.135, 0.135, 0.58, 0.62)           # its window band
        frustum(w, "CitadelViolet", 8, 0.16, 0.09, 0.76, 0.86)         # its roof
        for s in (1, -1):   # two slim violet spires sweeping up and out, 50 degrees above level
            M = xf(0, s * 0.09, 0.62, rx=-s * 40)
            frustum(w, "CitadelViolet", 8, 0.062, 0.0, 0.0, 0.48, M=M)
            frustum(w, "SunGold", 8, 0.07, 0.07, 0.0, 0.04, M=M)
    ht = 0.05
    with w.on("Blade"):
        frustum(w, "SunGold", 6, 0.13, 0.13, 0.92, 0.98, sx=0.5)      # gold collar
        blade(w, "CitadelWhite", [
            (0.92, hex_section(0.1, ht)),
            (1.04, hex_section(0.21, ht)),          # the shoulders
            (1.4, hex_section(0.185, ht)),
            (2.6, hex_section(0.14, ht)),
            (3.3, hex_section(0.07, ht * 0.75)),
            (3.72, [(0.0, 0.0)]),
        ])
        inlay(w, "CitadelViolet", ht, 0.0, 0.0, 1.1, 2.9, 0.04)
        for s in (1, -1):
            inlay(w, "AzureNeon", ht, s * 0.09, s * 0.065, 1.1, 2.6, 0.013)
    with w.on("Ring_1"):
        torus(w, "AzureNeon", 0.36, 0.024, 0, 0, 1.45, n=18, m=4, rx=8, ry=18)
    with w.on("Ring_2"):
        torus(w, "AzureNeon", 0.24, 0.02, 0, 0, 2.55, n=16, m=4, rx=-10, ry=-20)
    for name, s in (("Float_1", 1), ("Float_2", -1)):
        with w.on(name):
            crystal(w, "CitadelViolet", 0, 0, 0, 0.055, 0.22, 0.15, n=4, rz=45, M=xf(0, s * 0.52, 1.35, rx=-s * 10))
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.075, 0.075, -0.5, -0.54)
        frustum(w, "CitadelViolet", 8, 0.11, 0.045, -0.54, -0.64)
        crystal(w, "SkyGlass", 0, 0, -0.64, 0.045, 0.0, 0.14, n=6)


# ==========================================================================
# GREATSWORDS -- 5.2-6.8 studs, two hands. Long grips, heavy guards.
# ==========================================================================


@weapon("greatsword", "common", "a", "Bastion Greatblade", "SC_GREATSWORD_BASTION_GREATBLADE",
        "A broad parallel-edged blade with a squared ricasso, a wide bar guard with block ends, a ringed octagonal grip and an octagonal pommel.")
def greatsword_bastion(w):
    sword_bones(w, grip0=-0.7, grip1=0.7, guard_z=0.78, blade0=0.88, tip=5.35)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.075, 0.075, -0.7, 0.7)
        for z in (-0.5, -0.2, 0.1, 0.4):
            frustum(w, "PaleAlloy", 8, 0.085, 0.085, z - 0.02, z + 0.02)
        frustum(w, "PaleAlloy", 8, 0.088, 0.088, 0.62, 0.7)
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.78, 0.18, 1.3, 0.14)
        for s in (1, -1):
            box(w, "DeepAlloy", 0, s * 0.62, 0.78, 0.22, 0.14, 0.22)
    ht = 0.06
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.88, hex_section(0.25, ht, k=0.6)),
            (4.6, hex_section(0.24, ht, k=0.6)),
            (4.95, hex_section(0.2, ht, k=0.6)),
            (5.12, hex_section(0.12, ht * 0.75, k=0.6)),
            (5.35, [(0.0, 0.0)]),
        ])
        box(w, "PaleAlloy", 0, 0, 0.97, 0.15, 0.42, 0.16)     # squared ricasso block
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 8, 0.07, 0.13, -0.7, -0.78)
        frustum(w, "PaleAlloy", 8, 0.13, 0.13, -0.78, -0.9)
        frustum(w, "PaleAlloy", 8, 0.13, 0.07, -0.9, -0.98)


@weapon("greatsword", "common", "b", "Merlon Warblade", "SC_GREATSWORD_MERLON_WARBLADE",
        "A slim diamond-section blade on a narrow ricasso with parrying lugs, a thick cross with hex ends, a square wrapped grip and an edge-on hex wheel pommel.")
def greatsword_merlon(w):
    sword_bones(w, grip0=-0.72, grip1=0.72, guard_z=0.8, blade0=0.9, tip=5.6)
    with w.on("Grip"):
        frustum(w, "PaleAlloy", 4, 0.075, 0.075, -0.72, 0.72, rot=45)
        for z in (-0.55, -0.3, -0.05, 0.2, 0.45):   # slanted wraps
            frustum(w, "DeepAlloy", 4, 0.086, 0.086, -0.015, 0.015, rot=45, M=xf(0, 0, z, rx=16))
    with w.on("Guard"):
        box(w, "DeepAlloy", 0, 0, 0.8, 0.16, 1.0, 0.12)
        for s in (1, -1):
            frustum(w, "PaleAlloy", 6, 0.09, 0.09, -0.09, 0.09, M=xf(0, s * 0.52, 0.8, rx=90))
    ht = 0.055
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.9, hex_section(0.1, ht, k=0.3)),
            (1.55, hex_section(0.1, ht, k=0.3)),       # the narrow ricasso
            (1.64, hex_section(0.2, ht, k=0.3)),
            (4.85, hex_section(0.15, ht, k=0.3)),
            (5.6, [(0.0, 0.0)]),
        ])
        for s in (1, -1):   # parrying lugs
            frustum(w, "PaleAlloy", 4, 0.05, 0.0, 0.0, 0.17, M=xf(0, s * 0.09, 1.52, rx=-s * 90))
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 6, 0.06, 0.06, -0.79, -0.72)
        frustum(w, "PaleAlloy", 6, 0.15, 0.15, -0.045, 0.045, M=xf(0, 0, -0.92, ry=90))   # hex wheel


@weapon("greatsword", "uncommon", "a", "Gatehouse Lintel", "SC_GREATSWORD_GATEHOUSE_LINTEL",
        "The guard is a citadel gate: a lintel with two hanging pylons, finials and a gold keystone; a broad blade with an azure fuller; gold-ferruled grip, pyramid-capped cube pommel.")
def greatsword_lintel(w):
    sword_bones(w, grip0=-0.7, grip1=0.7, guard_z=0.88, blade0=1.0, tip=5.5)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.075, 0.075, -0.7, 0.7)
        frustum(w, "PaleAlloy", 8, 0.084, 0.084, -0.08, 0.08)
        frustum(w, "SunGold", 8, 0.085, 0.085, 0.63, 0.7)
        frustum(w, "SunGold", 8, 0.085, 0.085, -0.7, -0.63)
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.88, 0.2, 1.1, 0.16)                 # the lintel
        box(w, "SunGold", 0, 0, 0.88, 0.24, 0.12, 0.13)                 # keystone, proud on both faces
        for s in (1, -1):
            box(w, "DeepAlloy", 0, s * 0.48, 0.7, 0.13, 0.13, 0.22)     # hanging pylons
            crystal(w, "PaleAlloy", 0, s * 0.5, 0.96, 0.07, 0.12, 0.0, n=4, rz=45)   # finials
    ht = 0.06
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (1.0, hex_section(0.22, ht)),
            (2.2, hex_section(0.26, ht)),
            (4.6, hex_section(0.22, ht)),
            (5.1, hex_section(0.14, ht * 0.85)),
            (5.5, [(0.0, 0.0)]),
        ])
        inlay(w, "AzureDim", ht, 0.0, 0.0, 1.15, 4.4, 0.06)
    with w.on("Pommel"):
        box(w, "PaleAlloy", 0, 0, -0.8, 0.17, 0.17, 0.2, rz=45)
        frustum(w, "PaleAlloy", 4, 0.12, 0.0, -0.9, -1.0, rot=0)


@weapon("greatsword", "uncommon", "b", "Keelbreaker", "SC_GREATSWORD_KEELBREAKER",
        "The blade is the island keel: a long triangle from wide shoulders to a point, a slate ridge carrying an azure seam; ribs sweep down to gold finials; a keel-point pommel.")
def greatsword_keel(w):
    sword_bones(w, grip0=-0.68, grip1=0.68, guard_z=0.76, blade0=0.86, tip=5.7)
    with w.on("Grip"):
        frustum(w, "CitadelWhite", 8, 0.072, 0.072, -0.68, 0.68)
        for z in (-0.48, -0.24, 0.0, 0.24, 0.48):
            frustum(w, "DeepAlloy", 8, 0.08, 0.08, -0.016, 0.016, M=xf(0, 0, z, rx=-18))
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.76, 0.18, 0.36, 0.12)
        for s in (1, -1):   # ribs sweeping down like the keel's hoops
            tube(w, "PaleAlloy", [(0, s * 0.16, 0.78), (0, s * 0.38, 0.72), (0, s * 0.52, 0.58)],
                 [0.05, 0.04, 0.03], n=6)
            crystal(w, "SunGold", 0, s * 0.53, 0.56, 0.045, 0.03, 0.08, n=6)
    ht = 0.06
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.86, hex_section(0.18, ht, k=0.5)),
            (1.05, hex_section(0.32, ht, k=0.5)),
            (1.6, hex_section(0.3, ht, k=0.5)),
            (5.7, [(0.0, 0.0)]),
        ])
        inlay(w, "HullSlate", ht, 0.0, 0.0, 1.0, 4.1, 0.09, proud=0.012, t=0.03)     # the keel ridge
        inlay(w, "AzureDim", ht, 0.0, 0.0, 1.1, 3.9, 0.018, proud=0.018, t=0.01)     # its seam
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.08, 0.08, -0.68, -0.73)
        frustum(w, "HullSlate", 8, 0.12, 0.0, -0.73, -1.0)


@weapon("greatsword", "rare", "a", "Aethervane", "SC_GREATSWORD_AETHERVANE",
        "The ricasso is an open frame where a glass core spins; neon channels run from it up the blade; swept vane fins make the guard; a caged-crystal pommel.")
def greatsword_aethervane(w):
    sword_bones(w, grip0=-0.7, grip1=0.7, guard_z=0.8, blade0=0.95, tip=5.72)
    w.bone("Core", (0, 0, 1.25), (0, 0, 1.45), "Blade")
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.075, 0.075, -0.7, 0.7)
        for z in (-0.35, 0.35):
            frustum(w, "AzureNeon", 8, 0.08, 0.08, z - 0.01, z + 0.01)
        frustum(w, "PaleAlloy", 8, 0.085, 0.085, 0.63, 0.7)
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.8, 0.2, 0.34, 0.14)
        for s in (1, -1):   # vane fins, thin in X, sweeping up and out
            tube(w, "PaleAlloy", [(0, s * 0.15, 0.76), (0, s * 0.45, 0.86), (0, s * 0.7, 1.2)],
                 [0.1, 0.07, 0.02], n=4, sx=0.25, rot=45)
            crystal(w, "AzureNeon", 0, s * 0.72, 1.24, 0.035, 0.09, 0.04, n=4)
    with w.on("Core"):
        crystal(w, "SkyGlass", 0, 0, 1.25, 0.12, 0.2, 0.2, n=6)
    ht = 0.06
    with w.on("Blade"):
        box(w, "PaleAlloy", 0, 0, 0.98, 0.12, 0.48, 0.06)           # frame: bottom plate
        box(w, "PaleAlloy", 0, 0, 1.52, 0.12, 0.48, 0.06)           # top plate
        for s in (1, -1):
            box(w, "PaleAlloy", 0, s * 0.2, 1.25, 0.1, 0.08, 0.6)   # side rails
        blade(w, "CitadelWhite", [
            (1.55, hex_section(0.24, ht)),
            (4.55, hex_section(0.23, ht)),
            (5.12, hex_section(0.15, ht * 0.85)),
            (5.72, [(0.0, 0.0)]),
        ])
        for s in (1, -1):
            inlay(w, "AzureNeon", ht, s * 0.06, s * 0.06, 1.62, 4.75, 0.014)
            inlay(w, "AzureNeon", ht * 0.9, s * 0.06, s * 0.012, 4.75, 5.2, 0.014)
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 8, 0.09, 0.09, -0.76, -0.7)
        for k in range(4):   # cage prongs
            a = math.radians(45 + 90 * k)
            box(w, "PaleAlloy", 0.075 * math.cos(a), 0.075 * math.sin(a), -0.86, 0.03, 0.03, 0.2)
        crystal(w, "SkyGlass", 0, 0, -0.86, 0.06, 0.08, 0.1, n=6)
        frustum(w, "PaleAlloy", 8, 0.09, 0.03, -0.96, -1.02)


@weapon("greatsword", "epic", "a", "Zenith Orrery", "SC_GREATSWORD_ZENITH_ORRERY",
        "A slim violet-fullered blade that steps in to a needle at a neon band and gold collar, like a spire; on its ricasso a glass collar spins inside two crossed halos, each carrying a planet, like the observatory's orrery.")
def greatsword_orrery(w):
    sword_bones(w, grip0=-0.72, grip1=0.72, guard_z=0.82, blade0=0.92, tip=5.65)
    c = 1.45   # the orrery's centre on the ricasso
    w.bone("Core", (0, 0, c), (0, 0, c + 0.2), "Blade")
    ring_bone(w, "Ring_1", (0, 0, c), rx=35, parent="Blade")
    ring_bone(w, "Ring_2", (0, 0, c), ry=35, parent="Blade")
    with w.on("Grip"):
        frustum(w, "CitadelViolet", 8, 0.07, 0.07, -0.72, 0.72)
        for z in (-0.45, -0.15, 0.15, 0.45):
            frustum(w, "PaleAlloy", 8, 0.078, 0.078, -0.016, 0.016, M=xf(0, 0, z, rx=18))
        frustum(w, "SunGold", 8, 0.079, 0.079, 0.64, 0.72)
    with w.on("Guard"):
        frustum(w, "CitadelViolet", 8, 0.1, 0.12, 0.74, 0.9)
        frustum(w, "SunGold", 8, 0.125, 0.125, 0.8, 0.83)
        for s in (1, -1):
            tube(w, "CitadelViolet", [(0, s * 0.1, 0.82), (0, s * 0.34, 0.85), (0, s * 0.5, 0.92)],
                 [0.045, 0.035, 0.015], n=6)
            crystal(w, "AzureNeon", 0, s * 0.52, 0.93, 0.03, 0.07, 0.03, n=4)
    ht = 0.05
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.92, hex_section(0.09, ht)),
            (1.62, hex_section(0.09, ht)),          # the ricasso the orrery rides on
            (1.74, hex_section(0.2, ht)),
            (2.5, hex_section(0.19, ht)),
            (3.95, hex_section(0.16, ht)),
            (4.0, hex_section(0.1, ht * 0.8)),      # steps in to the needle, like a spire
            (5.2, hex_section(0.06, ht * 0.7)),
            (5.65, [(0.0, 0.0)]),
        ])
        inlay(w, "AzureNeon", ht, 0.0, 0.0, 0.98, 1.58, 0.02)       # the ricasso's glowing core line
        frustum(w, "SunGold", 6, 0.22, 0.22, 1.62, 1.7, sx=0.35)     # gold collar where the blade widens
        inlay(w, "CitadelViolet", ht, 0.0, 0.0, 1.85, 3.85, 0.045)
        frustum(w, "AzureNeon", 6, 0.185, 0.185, 3.88, 3.96, sx=0.36)   # the spire's glowing band
        frustum(w, "SunGold", 6, 0.13, 0.13, 4.0, 4.07, sx=0.4)         # and its gold collar
    with w.on("Core"):
        torus(w, "SkyGlass", 0.15, 0.045, 0, 0, c, n=6, m=4)        # glass collar threaded on the ricasso
    with w.on("Ring_1"):
        torus(w, "AzureNeon", 0.56, 0.022, 0, 0, c, n=22, m=4, rx=35)
        orb(w, "SkyGlass", 0.56, 0, c, 0.045, n=6)                  # its planet
    with w.on("Ring_2"):
        torus(w, "AzureNeon", 0.44, 0.02, 0, 0, c, n=20, m=4, ry=35)
        orb(w, "CitadelViolet", 0, -0.44, c, 0.04, n=6)             # its planet
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.08, 0.08, -0.77, -0.72)
        orb(w, "SkyGlass", 0, 0, -0.87, 0.1, n=8)
        crystal(w, "CitadelViolet", 0, 0, -0.96, 0.04, 0.0, 0.12, n=4)


# ==========================================================================
# DAGGERS -- 1.6-2.4 studs, one hand, often reverse-grip. Short grips,
# compact guards (a reverse grip wants nothing long below the hand).
# ==========================================================================


@weapon("dagger", "common", "a", "Sentry Dirk", "SC_DAGGER_SENTRY_DIRK",
        "The guard's sidearm: a straight hex-section dirk, a short bar guard, an octagonal grip and a flat disc pommel.")
def dagger_sentry(w):
    sword_bones(w, grip0=-0.3, grip1=0.3, guard_z=0.35, blade0=0.42, tip=1.75)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.06, 0.055, -0.3, 0.3)
        frustum(w, "PaleAlloy", 8, 0.068, 0.068, 0.24, 0.3)
    with w.on("Guard"):
        box(w, "PaleAlloy", 0, 0, 0.35, 0.12, 0.46, 0.08)
    ht = 0.04
    with w.on("Blade"):
        blade(w, "CitadelWhite", [
            (0.42, hex_section(0.12, ht)),
            (1.35, hex_section(0.11, ht)),
            (1.58, hex_section(0.07, ht * 0.8)),
            (1.75, [(0.0, 0.0)]),
        ])
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 8, 0.1, 0.1, -0.37, -0.31)


@weapon("dagger", "common", "b", "Hull Spike", "SC_DAGGER_HULL_SPIKE",
        "A square-section spike like a keel rivet: no edge, all point; a square block guard, a square grip with alloy bands, a pyramid pommel.")
def dagger_spike(w):
    sword_bones(w, grip0=-0.28, grip1=0.28, guard_z=0.33, blade0=0.4, tip=1.85)
    with w.on("Grip"):
        frustum(w, "PaleAlloy", 4, 0.06, 0.06, -0.28, 0.28, rot=45)
        for z in (-0.15, 0.0, 0.15):
            frustum(w, "DeepAlloy", 4, 0.068, 0.068, z - 0.02, z + 0.02, rot=45)
    with w.on("Guard"):
        box(w, "DeepAlloy", 0, 0, 0.33, 0.2, 0.2, 0.1)
    with w.on("Blade"):
        frustum(w, "CitadelWhite", 4, 0.07, 0.05, 0.4, 1.35, rot=0)      # diamond-on square spike
        frustum(w, "CitadelWhite", 4, 0.05, 0.0, 1.35, 1.85, rot=0)
        box(w, "PaleAlloy", 0, 0, 0.44, 0.13, 0.13, 0.08, rz=45)         # a collar where it leaves the guard
    with w.on("Pommel"):
        frustum(w, "DeepAlloy", 4, 0.09, 0.0, -0.29, -0.42, rot=45)


@weapon("dagger", "uncommon", "a", "Gilt Talon", "SC_DAGGER_GILT_TALON",
        "A curved single-edged talon with an azure seam along its spine; forward-swept gold quillons, a white grip and a gold ring pommel for the reverse grip.")
def dagger_talon(w):
    sword_bones(w, grip0=-0.32, grip1=0.3, guard_z=0.36, blade0=0.44, tip=1.85)
    with w.on("Grip"):
        lathe(w, "CitadelWhite", 8, [(-0.32, 0.055), (-0.1, 0.064), (0.15, 0.062), (0.3, 0.056)])
        frustum(w, "SunGold", 8, 0.066, 0.066, 0.25, 0.3)
    with w.on("Guard"):
        box(w, "SunGold", 0, 0, 0.36, 0.12, 0.22, 0.09)
        for s in (1, -1):
            tube(w, "SunGold", [(0, s * 0.1, 0.36), (0, s * 0.2, 0.4), (0, s * 0.24, 0.5)], [0.035, 0.028, 0.0], n=6)
    ht = 0.04
    with w.on("Blade"):
        # the talon: its edge on -Y curving back, the spine on +Y
        blade(w, "CitadelWhite", [
            (0.44, single_section(-0.11, 0.07, ht)),
            (0.9, single_section(-0.14, 0.06, ht)),
            (1.3, [(x, y + 0.04) for x, y in single_section(-0.15, 0.03, ht * 0.9)]),
            (1.62, [(x, y + 0.12) for x, y in single_section(-0.12, -0.01, ht * 0.75)]),
            (1.85, [(0.0, 0.14)]),
        ])
        inlay(w, "AzureDim", ht, 0.03, 0.05, 0.5, 1.3, 0.022)
    with w.on("Pommel"):
        torus(w, "SunGold", 0.075, 0.02, 0, 0, -0.4, n=8, m=4, ry=90)     # a ring for the little finger


@weapon("dagger", "uncommon", "b", "Chevron Kris", "SC_DAGGER_CHEVRON_KRIS",
        "A stepped blade that narrows in three chevron tiers; an azure inlay down its centre, a gold keystone guard, a hex grip with slanted wraps and a hex-nut pommel.")
def dagger_kris(w):
    sword_bones(w, grip0=-0.3, grip1=0.3, guard_z=0.36, blade0=0.44, tip=1.9)
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 6, 0.06, 0.058, -0.3, 0.3)
        for z in (-0.16, 0.0, 0.16):
            frustum(w, "PaleAlloy", 6, 0.068, 0.068, -0.013, 0.013, M=xf(0, 0, z, rx=18))
    with w.on("Guard"):
        ang = math.degrees(math.atan2(0.1, 0.22))
        for s in (1, -1):
            box(w, "PaleAlloy", 0, s * 0.12, 0.38, 0.1, 0.24, 0.06, rx=s * ang)
        box(w, "SunGold", 0, 0, 0.35, 0.11, 0.09, 0.09, rx=45)            # keystone
    ht = 0.04
    with w.on("Blade"):
        blade(w, "CitadelWhite", [            # three chevron tiers
            (0.44, hex_section(0.13, ht)),
            (0.85, hex_section(0.12, ht)),
            (0.88, hex_section(0.1, ht)),
            (1.25, hex_section(0.095, ht)),
            (1.28, hex_section(0.075, ht * 0.9)),
            (1.6, hex_section(0.07, ht * 0.85)),
            (1.9, [(0.0, 0.0)]),
        ])
        inlay(w, "AzureDim", ht, 0.0, 0.0, 0.5, 1.55, 0.02)
    with w.on("Pommel"):
        frustum(w, "PaleAlloy", 6, 0.085, 0.085, -0.31, -0.38)
        frustum(w, "SunGold", 6, 0.06, 0.0, -0.38, -0.46)


@weapon("dagger", "rare", "a", "Prism Fang", "SC_DAGGER_PRISM_FANG",
        "The whole blade is a faceted SkyGlass fang rising from a white socket with neon channels; a neon ring spins around the socket above two short fins; a disc grip.")
def dagger_prism(w):
    sword_bones(w, grip0=-0.3, grip1=0.3, guard_z=0.36, blade0=0.44, tip=1.9)
    ring_bone(w, "Ring_1", (0, 0, 0.62), parent="Blade")
    with w.on("Grip"):
        for i in range(6):   # stacked hub discs
            z0 = -0.3 + 0.1 * i
            frustum(w, "DeepAlloy", 8, 0.058, 0.058, z0, z0 + 0.08)
            frustum(w, "PaleAlloy", 8, 0.068, 0.068, z0 + 0.08, z0 + 0.1)
    with w.on("Guard"):
        frustum(w, "PaleAlloy", 8, 0.08, 0.1, 0.31, 0.4)        # a squat hub the ring orbits
        for s in (1, -1):   # two short fins
            tube(w, "PaleAlloy", [(0, s * 0.09, 0.36), (0, s * 0.22, 0.4), (0, s * 0.3, 0.5)],
                 [0.06, 0.04, 0.012], n=4, sx=0.3, rot=45)
    with w.on("Ring_1"):
        torus(w, "AzureNeon", 0.17, 0.018, 0, 0, 0.62, n=14, m=4)
    ht = 0.04
    with w.on("Blade"):
        # the white socket the glass is set into
        blade(w, "CitadelWhite", [
            (0.44, hex_section(0.11, ht)),
            (0.72, hex_section(0.115, ht)),
        ])
        for s in (1, -1):
            inlay(w, "AzureNeon", ht, s * 0.03, s * 0.03, 0.48, 0.7, 0.012)
        # the SkyGlass fang: diamond section, facets on every side
        blade(w, "SkyGlass", [
            (0.72, hex_section(0.11, ht * 0.9, k=0.3)),
            (1.2, hex_section(0.13, ht, k=0.3)),
            (1.55, hex_section(0.09, ht * 0.85, k=0.3)),
            (1.9, [(0.0, 0.0)]),
        ])
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.07, 0.07, -0.31, -0.35)
        crystal(w, "PaleAlloy", 0, 0, -0.35, 0.07, 0.0, 0.12, n=4)


@weapon("dagger", "epic", "a", "Eclipse Needle", "SC_DAGGER_ECLIPSE_NEEDLE",
        "A slim needle spire of a blade with a violet fuller, rising from a violet crescent guard; a halo and two glass shards orbit the hand, a crystal hangs below the pommel.")
def dagger_eclipse(w):
    sword_bones(w, grip0=-0.3, grip1=0.3, guard_z=0.36, blade0=0.46, tip=1.85)
    ring_bone(w, "Ring_1", (0, 0, 0.72), rx=10, ry=20, parent="Blade")
    w.bone("Float_1", (0, 0.3, 0.62), (0, 0.3, 0.8), "Blade")
    w.bone("Float_2", (0, -0.3, 0.62), (0, -0.3, 0.8), "Blade")
    with w.on("Grip"):
        frustum(w, "DeepAlloy", 8, 0.058, 0.058, -0.3, 0.3)
        for z in (-0.18, 0.0, 0.18):
            frustum(w, "CitadelViolet", 8, 0.066, 0.066, -0.014, 0.014, M=xf(0, 0, z, rx=20))
        frustum(w, "SunGold", 8, 0.066, 0.066, 0.25, 0.3)
    with w.on("Guard"):
        frustum(w, "CitadelWhite", 8, 0.075, 0.085, 0.31, 0.42)
        frustum(w, "AzureNeon", 8, 0.088, 0.088, 0.35, 0.37)
        for s in (1, -1):   # the violet crescent, horns up
            tube(w, "CitadelViolet", [(0, s * 0.07, 0.38), (0, s * 0.18, 0.4), (0, s * 0.24, 0.5), (0, s * 0.24, 0.6)],
                 [0.04, 0.035, 0.025, 0.0], n=6)
    ht = 0.035
    with w.on("Blade"):
        frustum(w, "SunGold", 6, 0.1, 0.1, 0.46, 0.51, sx=0.5)
        blade(w, "CitadelWhite", [
            (0.46, hex_section(0.085, ht)),
            (0.56, hex_section(0.12, ht)),
            (1.25, hex_section(0.09, ht)),
            (1.29, hex_section(0.06, ht * 0.85)),   # steps in to the needle
            (1.85, [(0.0, 0.0)]),
        ])
        inlay(w, "CitadelViolet", ht, 0.0, 0.0, 0.6, 1.2, 0.028)
        frustum(w, "AzureNeon", 6, 0.1, 0.1, 1.21, 1.26, sx=0.38)     # the spire's band
    with w.on("Ring_1"):
        torus(w, "AzureNeon", 0.2, 0.016, 0, 0, 0.72, n=16, m=4, rx=10, ry=20)
    for name, s in (("Float_1", 1), ("Float_2", -1)):
        with w.on(name):
            crystal(w, "SkyGlass", 0, 0, 0, 0.035, 0.12, 0.08, n=4, rz=45, M=xf(0, s * 0.3, 0.7, rx=-s * 10))
    with w.on("Pommel"):
        frustum(w, "SunGold", 8, 0.06, 0.06, -0.3, -0.33)
        frustum(w, "CitadelViolet", 8, 0.08, 0.03, -0.33, -0.4)
        crystal(w, "SkyGlass", 0, 0, -0.4, 0.03, 0.0, 0.1, n=6)


# ==========================================================================
# HAMMERS -- 3.4-5.0 studs. The head spans ~25-35% of the length (face to
# back), is its own shell on `Head`, pivots at the top of the haft, and its
# striking face looks down -Y with Fx_Strike at the face's centre.
# ==========================================================================


def hammer_bones(w, haft_top, head_c, face_y):
    w.bone("Root", (0, 0, 0), (0, 0, 0.3), None, deform=False)
    w.bone("Haft", (0, 0, 0), (0, 0, haft_top), "Root")
    w.bone("Head", (0, 0, haft_top), (0, 0, haft_top + 0.3), "Haft")
    w.fx("Fx_Strike", (0, face_y, head_c), direction=(0, -1, 0), parent="Head")


def along_y(y0, y1, z, x=0.0):
    """A frame whose local Z runs along world +Y from y0, centred at (x, z):
    frustum(... z0=0, z1=y1-y0, M=along_y(...)) lays a prism along the head."""
    return xf(x, y0, z, rx=-90)


@weapon("hammer", "common", "a", "Wardhall Maul", "SC_HAMMER_WARDHALL_MAUL",
        "The guard's maul: an octagonal white drum head with alloy bands at both faces on a long dark haft with ringed wraps.")
def hammer_wardhall(w):
    hammer_bones(w, haft_top=3.0, head_c=3.28, face_y=-0.6)
    with w.on("Haft"):
        frustum(w, "DeepAlloy", 8, 0.07, 0.07, -0.45, 3.0)
        frustum(w, "PaleAlloy", 8, 0.09, 0.06, -0.55, -0.45)
        for z in (-0.25, 0.05, 0.35):
            frustum(w, "PaleAlloy", 8, 0.08, 0.08, z - 0.03, z + 0.03)
    with w.on("Head"):
        frustum(w, "CitadelWhite", 8, 0.28, 0.28, 0.0, 1.2, M=along_y(-0.6, 0.6, 3.28))
        for y0 in (-0.52, 0.42):
            frustum(w, "PaleAlloy", 8, 0.295, 0.295, 0.0, 0.1, M=along_y(y0, y0 + 0.1, 3.28))
        frustum(w, "PaleAlloy", 8, 0.09, 0.09, 3.005, 3.08)          # socket collar


@weapon("hammer", "common", "b", "Merlon Mallet", "SC_HAMMER_MERLON_MALLET",
        "A white block head crenellated along its top like a wall walk, alloy face plates, a square alloy haft and a pyramid butt.")
def hammer_merlon(w):
    hammer_bones(w, haft_top=2.6, head_c=2.83, face_y=-0.57)
    with w.on("Haft"):
        frustum(w, "PaleAlloy", 4, 0.075, 0.075, -0.45, 2.6, rot=45)
        for z in (-0.2, 0.2, 1.2):
            frustum(w, "DeepAlloy", 4, 0.085, 0.085, z - 0.04, z + 0.04, rot=45)
        frustum(w, "DeepAlloy", 4, 0.09, 0.0, -0.45, -0.6, rot=45)
    with w.on("Head"):
        box(w, "CitadelWhite", 0, 0, 2.83, 0.42, 1.05, 0.42)
        for y in (-0.35, 0.0, 0.35):
            box(w, "PaleAlloy", 0, y, 3.11, 0.3, 0.2, 0.14)            # merlons
        for s in (1, -1):
            box(w, "PaleAlloy", 0, s * 0.54, 2.83, 0.46, 0.06, 0.46)   # face plates


@weapon("hammer", "uncommon", "a", "Sunforge Hammer", "SC_HAMMER_SUNFORGE_HAMMER",
        "A forge hammer: a white drum face with a gold rim and an azure band, a squared alloy hub, a tapering beak behind; a white haft with a gold ferrule and dark wraps.")
def hammer_sunforge(w):
    hammer_bones(w, haft_top=3.2, head_c=3.45, face_y=-0.56)
    with w.on("Haft"):
        frustum(w, "CitadelWhite", 8, 0.07, 0.068, -0.5, 3.2)
        frustum(w, "SunGold", 8, 0.08, 0.08, 3.1, 3.2)
        for z in (-0.3, -0.1, 0.1, 0.3):
            frustum(w, "DeepAlloy", 8, 0.078, 0.078, -0.016, 0.016, M=xf(0, 0, z, rx=18))
        frustum(w, "DeepAlloy", 8, 0.085, 0.06, -0.6, -0.5)
    with w.on("Head"):
        frustum(w, "CitadelWhite", 8, 0.26, 0.26, 0.0, 0.45, M=along_y(-0.55, -0.1, 3.45))
        frustum(w, "SunGold", 8, 0.275, 0.275, 0.0, 0.05, M=along_y(-0.56, -0.51, 3.45))    # gold face rim
        frustum(w, "AzureDim", 8, 0.268, 0.268, 0.0, 0.04, M=along_y(-0.3, -0.26, 3.45))    # azure band
        box(w, "PaleAlloy", 0, 0.0, 3.45, 0.3, 0.3, 0.4)                                    # hub
        tube(w, "PaleAlloy", [(0, 0.1, 3.45), (0, 0.42, 3.43), (0, 0.72, 3.32)], [0.15, 0.1, 0.0], n=6)   # beak
        frustum(w, "PaleAlloy", 8, 0.09, 0.09, 3.205, 3.27)                                 # socket collar


@weapon("hammer", "uncommon", "b", "Chevron Sledge", "SC_HAMMER_CHEVRON_SLEDGE",
        "A long two-handed sledge: a white hex head ringed in gold at both faces with an azure gatehouse chevron inlaid on each side; a hex haft with slanted wraps and a hex-nut butt.")
def hammer_chevron(w):
    hammer_bones(w, haft_top=3.74, head_c=4.05, face_y=-0.62)
    with w.on("Haft"):
        frustum(w, "DeepAlloy", 6, 0.075, 0.072, -0.5, 3.74)
        for z in (-0.3, -0.05, 0.2, 0.45, 0.7):
            frustum(w, "PaleAlloy", 6, 0.084, 0.084, -0.016, 0.016, M=xf(0, 0, z, rx=18))
        frustum(w, "PaleAlloy", 6, 0.1, 0.1, -0.6, -0.5)
    with w.on("Head"):
        frustum(w, "CitadelWhite", 6, 0.3, 0.3, 0.0, 1.24, rot=30, M=along_y(-0.62, 0.62, 4.05))   # flats on the sides
        for y0 in (-0.62, 0.56):
            frustum(w, "SunGold", 6, 0.31, 0.31, 0.0, 0.06, rot=30, M=along_y(y0, y0 + 0.06, 4.05))
        ang = 35.0
        for sx_ in (1, -1):   # the chevron, one on each side face, its point at the top
            for s in (1, -1):
                box(w, "AzureDim", sx_ * 0.262, s * 0.1, 4.03, 0.012, 0.32, 0.03, rx=-s * ang)
        frustum(w, "PaleAlloy", 6, 0.1, 0.1, 3.755, 3.82)          # socket collar


@weapon("hammer", "rare", "a", "Galecage", "SC_HAMMER_GALECAGE",
        "An open cage head: two white faces rimmed with neon halos, joined by alloy bars, with a glass core spinning inside; two vane fins sweep from its back.")
def hammer_galecage(w):
    hc = 3.4
    hammer_bones(w, haft_top=3.1, head_c=hc, face_y=-0.6)
    w.bone("Core", (0, 0, hc), (0, 0.2, hc), "Head")
    with w.on("Haft"):
        frustum(w, "DeepAlloy", 8, 0.072, 0.072, -0.45, 3.1)
        for z in (-0.2, 0.5):
            frustum(w, "AzureNeon", 8, 0.078, 0.078, z - 0.012, z + 0.012)
        frustum(w, "PaleAlloy", 8, 0.08, 0.08, -0.12, 0.42)
        frustum(w, "PaleAlloy", 8, 0.09, 0.06, -0.55, -0.45)
    with w.on("Head"):
        for s in (1, -1):
            y0 = 0.42 if s > 0 else -0.58
            frustum(w, "CitadelWhite", 8, 0.28, 0.28, 0.0, 0.16, M=along_y(y0, y0 + 0.16, hc))
            torus(w, "AzureNeon", 0.27, 0.02, 0, s * 0.59, hc, n=16, m=4, rx=90)   # neon rim halo
        for k in range(4):   # cage bars
            a = math.radians(45 + 90 * k)
            box(w, "PaleAlloy", 0.22 * math.cos(a), 0, hc + 0.22 * math.sin(a), 0.06, 0.84, 0.06)
        box(w, "PaleAlloy", 0, 0, hc - 0.2, 0.44, 0.1, 0.1)             # socket beam under the bars
        box(w, "PaleAlloy", 0, 0, 3.15, 0.12, 0.12, 0.1)                # and its post
        for s in (1, -1):   # vane fins from the back, one up, one down; thin in X
            tube(w, "PaleAlloy", [(0, 0.5, hc + s * 0.26), (0, 0.62, hc + s * 0.5), (0, 0.8, hc + s * 0.62)],
                 [0.1, 0.06, 0.015], n=4, sx=0.25, rot=45)
            crystal(w, "AzureNeon", 0, 0.82, hc + s * 0.64, 0.03, 0.06, 0.06, n=4)
    with w.on("Core"):
        crystal(w, "SkyGlass", 0, 0, 0, 0.13, 0.15, 0.15, n=6, M=xf(0, 0, hc, rx=90))


@weapon("hammer", "epic", "a", "Obelisk Maul", "SC_HAMMER_OBELISK_MAUL",
        "The head is a citadel obelisk laid on its side: a white octagonal face with a neon halo, tapering to a violet spire behind; two halos orbit the spire and a crystal floats above, as it does over the obelisks.")
def hammer_obelisk(w):
    hc = 3.5
    hammer_bones(w, haft_top=3.24, head_c=hc, face_y=-0.61)
    ring_bone(w, "Ring_1", (0, 0.5, hc), rx=90, rz=25, parent="Head")
    ring_bone(w, "Ring_2", (0, 0.78, hc), rx=90, rz=-25, parent="Head")
    w.bone("Float_1", (0, -0.1, 3.95), (0, -0.1, 4.15), "Head")
    with w.on("Haft"):
        frustum(w, "DeepAlloy", 8, 0.07, 0.07, -0.5, 3.24)
        for z in (-0.3, -0.05, 0.2, 0.45):
            frustum(w, "CitadelViolet", 8, 0.078, 0.078, -0.016, 0.016, M=xf(0, 0, z, rx=20))
        frustum(w, "SunGold", 8, 0.08, 0.08, 3.14, 3.24)
        frustum(w, "PaleAlloy", 8, 0.085, 0.085, -0.5, -0.45)
        frustum(w, "CitadelViolet", 8, 0.085, 0.0, -0.5, -0.62)
    with w.on("Head"):
        frustum(w, "PaleAlloy", 8, 0.29, 0.27, 0.0, 0.05, M=along_y(-0.61, -0.56, hc))      # face plate
        frustum(w, "CitadelWhite", 8, 0.27, 0.2, 0.0, 0.91, M=along_y(-0.56, 0.35, hc))     # obelisk body
        frustum(w, "AzureNeon", 8, 0.25, 0.25, 0.0, 0.05, M=along_y(-0.14, -0.09, hc))      # its glowing band
        frustum(w, "SunGold", 8, 0.212, 0.212, 0.0, 0.06, M=along_y(0.33, 0.39, hc))        # gold collar
        frustum(w, "CitadelViolet", 8, 0.2, 0.0, 0.0, 0.6, M=along_y(0.35, 0.95, hc))       # violet spire
        torus(w, "AzureNeon", 0.18, 0.018, 0, -0.618, hc, n=8, m=4, rx=90)                   # neon halo on the face
        frustum(w, "PaleAlloy", 8, 0.1, 0.1, 3.245, 3.3)                                     # socket collar
    with w.on("Ring_1"):
        torus(w, "AzureNeon", 0.3, 0.02, 0, 0.5, hc, n=16, m=4, rx=90, rz=25)
    with w.on("Ring_2"):
        torus(w, "AzureNeon", 0.17, 0.016, 0, 0.78, hc, n=12, m=4, rx=90, rz=-25)
    with w.on("Float_1"):
        crystal(w, "SkyGlass", 0, -0.1, 3.95, 0.08, 0.16, 0.12, n=6)


# ==========================================================================
# Scene building
# ==========================================================================


def _ui_override(**extra):
    """Operators like the FBX exporter and mode_set read context, which a
    script run from a timer (the Blender MCP bridge) does not have. Borrow the
    first window/area so the same code works from the UI, a timer, or
    --background (where there is no window and the plain context suffices)."""
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                return bpy.context.temp_override(window=window, area=area, **extra)
    return bpy.context.temp_override(**extra)


def clear_previous():
    """Idempotence: remove everything this script made last time (and only
    that), so a re-run never leaves a `.001`."""
    active = bpy.context.view_layer.objects.active
    if active and active.mode != "OBJECT":
        with _ui_override(active_object=active, object=active):
            bpy.ops.object.mode_set(mode="OBJECT")
    for obj in list(bpy.data.objects):
        if obj.name.startswith(("wpn_sc_", "rig_sc_")) or obj.name.startswith("SCALE_REF_CHARACTER"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        if coll.name.startswith(("Weapons_", "_fbx_verify")):
            bpy.data.collections.remove(coll)
    for m in list(bpy.data.meshes):
        if m.users == 0 and m.name.startswith(("wpn_sc_", "SCALE_REF_CHARACTER")):
            bpy.data.meshes.remove(m)
    for a in list(bpy.data.armatures):
        if a.users == 0 and a.name.startswith("rig_sc_"):
            bpy.data.armatures.remove(a)
    us = bpy.context.scene.unit_settings
    us.system = "METRIC"
    us.scale_length = 1.0
    us.length_unit = "METERS"


def scale_ref(mats):
    """The 5-stud character, 2 x 1 x 5, standing at the origin. Never exported."""
    mesh = bpy.data.meshes.new("SCALE_REF_CHARACTER")
    hx, hy = 1.0, 0.5
    v = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
         (-hx, -hy, 5), (hx, -hy, 5), (hx, hy, 5), (-hx, hy, 5)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(v, [], f)
    mesh.materials.append(mats["HullSlate"])
    obj = bpy.data.objects.new("SCALE_REF_CHARACTER", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "SOLID"
    return obj


def collection_for(wtype):
    name = "Weapons_" + TYPES[wtype][0]
    coll = bpy.data.collections.get(name)
    if not coll:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def to_objects(w, mats, coll):
    """The weapon soup -> one flat-shaded mesh with baked vertex colour and
    rigid vertex groups, parented to its armature."""
    used = [m for m in MAT_ORDER if m in set(w.fmat)]
    mesh = bpy.data.meshes.new(w.name)
    mesh.from_pydata([tuple(v) for v in w.verts], [], w.faces)
    for name in used:
        mesh.materials.append(mats[name])
    for poly, mname in zip(mesh.polygons, w.fmat):
        poly.material_index = used.index(mname)
        poly.use_smooth = False

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in mesh.polygons:
        rgb = PALETTE[used[poly.material_index]][0]
        c = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
        for li in poly.loop_indices:
            col.data[li].color_srgb = c
    mesh.color_attributes.active_color = col
    mesh.update()

    # armature
    arm_data = bpy.data.armatures.new(w.rig_name)
    arm = bpy.data.objects.new(w.rig_name, arm_data)
    coll.objects.link(arm)
    arm.show_in_front = False
    bpy.context.view_layer.objects.active = arm
    with _ui_override(active_object=arm, object=arm, selected_objects=[arm]):
        bpy.ops.object.mode_set(mode="EDIT")
        for name in w.order:
            head, tail, parent, deform = w.bones[name]
            eb = arm_data.edit_bones.new(name)
            eb.head, eb.tail = head, tail
            eb.roll = 0.0
            eb.use_deform = deform
            if parent:
                eb.parent = arm_data.edit_bones[parent]
                eb.use_connect = False
        bpy.ops.object.mode_set(mode="OBJECT")
    # Bones live in one hidden bone collection so the viewport shows the
    # weapon, not its rig. Toggle "Bones" in Armature > Bone Collections.
    bcoll = arm_data.collections.new("Bones")
    for b in arm_data.bones:
        bcoll.assign(b)
    bcoll.is_visible = False

    obj = bpy.data.objects.new(w.name, mesh)
    coll.objects.link(obj)
    obj.parent = arm
    obj.matrix_parent_inverse = Matrix.Identity(4)
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm

    # rigid weights: a vertex takes the bone of its face (or its override)
    vbone = {}
    for f, b in zip(w.faces, w.fbone):
        for i in f:
            vbone[i] = b
    vbone.update(w.vert_bone)
    groups = {}
    for i, b in vbone.items():
        groups.setdefault(b, []).append(i)
    for name in w.order:
        if name in groups:
            obj.vertex_groups.new(name=name).add(groups[name], 1.0, "REPLACE")

    for o in (obj, arm):
        o["weapon_type"] = w.wtype
        o["rarity"] = w.rarity
        o["content_id"] = w.cid
        o["display_name"] = w.display
    return obj, arm


def build_all(types=None):
    mats = ensure_materials()
    clear_previous()
    ref = scale_ref(mats)
    built = []   # (Weapon, mesh obj, armature obj)
    for wtype, rarity, letter, display, cid, note, fn in WEAPONS:
        if types and wtype not in types:
            continue
        coll = collection_for(wtype)
        hands = ("r", "l") if wtype == "gauntlets" else (None,)
        for hand in hands:
            w = Weapon(wtype, rarity, letter, display, cid, note, hand)
            fn(w)
            if hand == "l":
                w.mirror_x()
            obj, arm = to_objects(w, mats, coll)
            built.append((w, obj, arm))
    return ref, built


# ==========================================================================
# Validation
# ==========================================================================

NAME_RE = re.compile(r"^wpn_sc_(%s)_(common|uncommon|rare|epic)_[a-z](_[lr])?$" % "|".join(TYPE_ORDER))


def local_bbox(obj):
    vs = [v.co for v in obj.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)])
    mx = Vector([max(v[i] for v in vs) for i in range(3)])
    return mn, mx


def tri_count(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def palette_used(mesh):
    col = mesh.color_attributes.get("Col")
    names, bad = set(), set()
    if col is None:
        return names, {"<no Col attribute>"}
    for d in col.data:
        c = d.color_srgb
        rgb = tuple(int(round(c[i] * 255)) for i in range(3))
        if rgb in RGB_TO_NAME:
            names.add(RGB_TO_NAME[rgb])
        else:
            bad.add(rgb)
    return names, bad


def islands(mesh):
    """Connected vertex islands (by edges) as lists of vertex indices."""
    parent = list(range(len(mesh.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in mesh.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    out = {}
    for i in range(len(mesh.vertices)):
        out.setdefault(find(i), []).append(i)
    return list(out.values())


def validate_one(w, obj, arm):
    errs, warns = [], []
    me = obj.data
    wtype, rarity = w.wtype, w.rarity

    # names
    if not NAME_RE.match(obj.name) or obj.name != w.name:
        errs.append("bad mesh name %r" % obj.name)
    if arm.name != "rig_" + obj.name[len("wpn_"):]:
        errs.append("bad armature name %r" % arm.name)
    for n in (obj.name, arm.name, me.name, arm.data.name):
        if re.search(r"\.\d{3}$", n):
            errs.append("duplicate-suffixed name %r" % n)

    # triangles
    tris = tri_count(me)
    if tris > TRI_LIMIT:
        errs.append("%d triangles > hard cap %d" % (tris, TRI_LIMIT))
    elif tris > TIER_TRIS[rarity]:
        warns.append("%d triangles over the %s target %d" % (tris, rarity, TIER_TRIS[rarity]))

    # shading, modifiers, shape keys, animation
    if any(p.use_smooth for p in me.polygons):
        errs.append("smooth-shaded faces")
    if [m.type for m in obj.modifiers] != ["ARMATURE"] or obj.modifiers[0].object != arm:
        errs.append("modifiers must be exactly one Armature -> its rig: %r" % [m.type for m in obj.modifiers])
    if me.shape_keys:
        errs.append("has shape keys")
    for idb in (obj, me, arm, arm.data):
        if idb.animation_data:
            errs.append("%s has animation data" % idb.name)

    # colour
    names, bad = palette_used(me)
    if bad:
        errs.append("non-palette vertex colours %r" % sorted(bad)[:4])
    if len(me.materials) and any(m is None or not m.name.startswith("SC_") for m in me.materials):
        errs.append("non-palette material slot")

    # origin, orientation, length
    if obj.parent != arm or obj.matrix_parent_inverse != Matrix.Identity(4) \
\
            or obj.location.length > 1e-6 or obj.rotation_euler[:] != (0, 0, 0) or tuple(obj.scale) != (1, 1, 1):
        errs.append("mesh transform not identity under its rig")
    if arm.rotation_euler[:] != (0, 0, 0) or tuple(arm.scale) != (1, 1, 1):
        errs.append("rig rotated or scaled")
    mn, mx = local_bbox(obj)
    dims = mx - mn
    lo, hi = TYPES[wtype][1]
    if not (lo - 1e-4 <= dims.z <= hi + 1e-4):
        errs.append("length %.3f outside %s range %.1f-%.1f" % (dims.z, wtype, lo, hi))
    if dims.z < max(dims.x, dims.y):
        errs.append("length is not along +Z (dims %s)" % tuple(round(d, 3) for d in dims))
    if not (mn.z < 0 < mx.z) and wtype != "gauntlets":
        errs.append("origin is not inside the weapon's length")

    # armature
    bones = arm.data.bones
    if "Root" not in bones or bones["Root"].head_local.length > 1e-6:
        errs.append("Root missing or not at the origin")
    elif bones[0].name != "Root" or bones["Root"].parent is not None:
        errs.append("Root is not the first, parentless bone")
    for b in bones:
        if not bone_allowed(wtype, b.name):
            errs.append("bone %r not in the %s vocabulary" % (b.name, wtype))
    missing = REQUIRED[wtype] - set(bones.keys())
    if missing:
        errs.append("missing required bones %s" % sorted(missing))
    for prefix in ("Float", "Ring"):
        nums = sorted(int(NUMBERED.match(b.name).group(2)) for b in bones
                      if NUMBERED.match(b.name) and b.name.startswith(prefix + "_"))
        if nums != list(range(1, len(nums) + 1)):
            errs.append("%s_n bones not numbered from 1: %s" % (prefix, nums))
    for pb in arm.pose.bones:
        if pb.matrix_basis != Matrix.Identity(4):
            errs.append("bone %s not in rest pose" % pb.name)
        if pb.constraints:
            errs.append("bone %s has constraints" % pb.name)
    if arm.data.pose_position != "POSE" and arm.data.pose_position != "REST":
        errs.append("odd pose_position")

    # weights
    gname = {g.index: g.name for g in obj.vertex_groups}
    for g in obj.vertex_groups:
        if g.name not in bones:
            errs.append("vertex group %r is not a bone" % g.name)
    vb = []
    for v in me.vertices:
        gs = [(gname[g.group], g.weight) for g in v.groups]
        if len(gs) != 1 or abs(gs[0][1] - 1.0) > 1e-6:
            errs.append("vertex %d weights %r (need exactly one group at 1.0)" % (v.index, gs))
            vb.append(None)
            if len(errs) > 30:
                break
        else:
            vb.append(gs[0][0])
    counts = {}
    for b in vb:
        counts[b] = counts.get(b, 0) + 1
    for b in bones:
        n = counts.get(b.name, 0)
        if is_fx(b.name) or b.name == "Root":
            if b.use_deform or n:
                errs.append("%s must be non-deforming with no vertices" % b.name)
        elif not b.use_deform or n == 0:
            errs.append("deforming bone %s has no vertices" % b.name)

    # modularity: every island is one bone and closed (the bow string, and
    # only it, may span its tips and nock); no face mixes bones otherwise.
    edge_faces = {}
    for p in me.polygons:
        for k in p.edge_keys:
            edge_faces[k] = edge_faces.get(k, 0) + 1
    open_edges = {k for k, c in edge_faces.items() if c != 2}
    string_bones = {"Limb_Upper_Tip", "Limb_Lower_Tip", "String_Nock"}
    for isl in islands(me):
        bs = {vb[i] for i in isl}
        if len(bs) > 1 and not (wtype == "bow" and bs <= string_bones):
            errs.append("an island mixes bones %s" % sorted(map(str, bs)))
        if any(is_animatable(b or "") for b in bs):
            s = set(isl)
            if any(a in s for a, b in open_edges):
                errs.append("an island of %s is not closed" % sorted(map(str, bs)))

    # tier rules
    bn = set(bones.keys())
    floats = [b for b in bn if NUMBERED.match(b)]
    if rarity == "common":
        if names & (EMISSIVE | {"SunGold"}):
            errs.append("Common uses %s" % sorted(names & (EMISSIVE | {"SunGold"})))
        if floats or "Core" in bn:
            errs.append("Common has floating/core bones")
        if not (2 <= len(names) <= 3):
            warns.append("Common uses %d colours (target 2-3)" % len(names))
        if not ({"CitadelWhite"} & names and {"PaleAlloy", "DeepAlloy"} & names):
            warns.append("Common should be alloy and white")
    if rarity == "uncommon":
        if floats:
            errs.append("Uncommon has floating parts")
        if "SunGold" not in names or "AzureDim" not in names:
            errs.append("Uncommon needs SunGold fittings and an AzureDim seam")
    if rarity == "rare":
        if not (floats or "Core" in bn):
            errs.append("Rare needs Core, Ring_n or Float_n")
        if len(floats) > 2:
            errs.append("Rare has more than 2 floating parts")
        if "AzureNeon" not in names or "SkyGlass" not in names:
            errs.append("Rare needs AzureNeon channels and a SkyGlass crystal")
    if rarity == "epic":
        if len(floats) < 2:
            errs.append("Epic needs 2+ Float_n/Ring_n bones")
        if "CitadelViolet" not in names:
            errs.append("Epic must use CitadelViolet")

    info = {
        "tris": tris,
        "dims": tuple(round(d, 3) for d in dims),
        "zrange": (round(mn.z, 3), round(mx.z, 3)),
        "bones": [b.name for b in bones],
        "verts_per_bone": {b.name: counts.get(b.name, 0) for b in bones},
        "colours": [m for m in MAT_ORDER if m in names],
    }
    return errs, warns, info


def validate(built):
    report, ok = {}, True
    for w, obj, arm in built:
        errs, warns, info = validate_one(w, obj, arm)
        report[obj.name] = {"errors": errs, "warnings": warns, **info}
        ok = ok and not errs
    return ok, report


# ==========================================================================
# Layout, export, verify
# ==========================================================================


def layout(built):
    slot = {}
    for w, obj, arm in built:
        row = TYPE_ORDER.index(w.wtype)
        key = (w.wtype, w.rarity, w.letter)
        if key not in slot:
            slot[key] = len([k for k in slot if k[0] == w.wtype])
        i = slot[key]
        x = REVIEW_ROW_X0 + row * REVIEW_ROW_STEP
        y = REVIEW_Y0 + i * REVIEW_Y_STEP
        if w.hand:
            x += 0.9 if w.hand == "r" else -0.9
        arm.location = (x, y, REVIEW_Z)
    bpy.context.view_layer.update()


def _export_fbx(path):
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"MESH", "ARMATURE"},
        axis_forward="-Z",
        axis_up="Y",
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        colors_type="SRGB",
        add_leaf_bones=False,
        use_armature_deform_only=False,
        bake_anim=False,
        path_mode="AUTO",
    )


def export_type(wtype, items):
    """One FBX per type; every rig moved to the world origin while written."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, "sky_citadel_%s.fbx" % wtype)
    arms = [a for _, _, a in items]
    objs = [o for _, o, _ in items] + arms
    saved = [a.location.copy() for a in arms]
    for a in arms:
        a.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    try:
        with _ui_override(selected_objects=list(objs), active_object=objs[0], object=objs[0]):
            _export_fbx(path)
    finally:
        for a, loc in zip(arms, saved):
            a.location = loc
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.update()
    return path


def verify_export(path, wtype, items):
    """Re-import into a throwaway collection and measure what came back. The
    originals are renamed aside first, so an imported name is the FBX's own
    and a `.001` means the file really carries one."""
    errs = []
    lo, hi = TYPES[wtype][1]
    originals = {o.name: o for _, o, a in items} | {a.name: a for _, o, a in items}
    expect = {o.name: (local_bbox(o), {b.name: b.head_local.copy() for b in a.data.bones})
              for _, o, a in items}
    for n, o in originals.items():
        o.name = n + "~orig"
    before = {k: set(getattr(bpy.data, k)) for k in ("objects", "meshes", "armatures", "materials", "actions")}
    coll = bpy.data.collections.new("_fbx_verify")
    bpy.context.scene.collection.children.link(coll)
    lc = bpy.context.view_layer.layer_collection.children[coll.name]
    prev_active = bpy.context.view_layer.active_layer_collection
    bpy.context.view_layer.active_layer_collection = lc
    result = {"file": os.path.relpath(path, REPO).replace("\\", "/")}
    try:
        with _ui_override():
            bpy.ops.import_scene.fbx(filepath=path)
        new = [o for o in bpy.data.objects if o not in before["objects"]]
        meshes = [o for o in new if o.type == "MESH"]
        arms = [o for o in new if o.type == "ARMATURE"]
        result["meshes"], result["armatures"] = len(meshes), len(arms)
        if len(meshes) != len(items) or len(arms) != len(items):
            errs.append("came back %d meshes / %d armatures, expected %d each" % (len(meshes), len(arms), len(items)))
        for o in new:
            if re.search(r"\.\d{3}$", o.name):
                errs.append("imported name %r" % o.name)
        for o in meshes:
            if o.name not in expect:
                errs.append("unexpected mesh %r" % o.name)
                continue
            (emn, emx), ebones = expect[o.name]
            pts = [o.matrix_world @ v.co for v in o.data.vertices]
            mn = Vector([min(p[i] for p in pts) for i in range(3)])
            mx = Vector([max(p[i] for p in pts) for i in range(3)])
            L = mx.z - mn.z
            if not (lo - 1e-3 <= L <= hi + 1e-3):
                errs.append("%s came back %.3f long" % (o.name, L))
            if (mn - emn).length > 1e-3 or (mx - emx).length > 1e-3:
                errs.append("%s came back moved/rotated: %s..%s vs %s..%s" % (
                    o.name, tuple(round(c, 3) for c in mn), tuple(round(c, 3) for c in mx),
                    tuple(round(c, 3) for c in emn), tuple(round(c, 3) for c in emx)))
            t = tri_count(o.data)
            if t > TRI_LIMIT:
                errs.append("%s came back %d triangles" % (o.name, t))
            rig = o.parent if o.parent and o.parent.type == "ARMATURE" else None
            if rig is None:
                mod = next((m for m in o.modifiers if m.type == "ARMATURE"), None)
                rig = mod.object if mod else None
            if rig is None:
                errs.append("%s came back without its armature" % o.name)
                continue
            got = {b.name: rig.matrix_world @ b.head_local for b in rig.data.bones}
            if set(got) != set(ebones):
                errs.append("%s bones differ: missing %s extra %s" % (
                    o.name, sorted(set(ebones) - set(got)), sorted(set(got) - set(ebones))))
            for bname, h in ebones.items():
                if bname in got and (got[bname] - h).length > 1e-3:
                    errs.append("%s bone %s came back at %s, expected %s" % (
                        o.name, bname, tuple(round(c, 3) for c in got[bname]), tuple(round(c, 3) for c in h)))
            if not o.data.color_attributes:
                errs.append("%s came back without vertex colours" % o.name)
    finally:
        bpy.context.view_layer.active_layer_collection = prev_active
        for o in [o for o in bpy.data.objects if o not in before["objects"]]:
            bpy.data.objects.remove(o, do_unlink=True)
        for k in ("meshes", "armatures", "materials", "actions"):
            for d in [d for d in getattr(bpy.data, k) if d not in before[k]]:
                getattr(bpy.data, k).remove(d)
        bpy.data.collections.remove(coll)
        for n, o in originals.items():
            o.name = n
    result["errors"] = errs
    return result


# ==========================================================================
# Manifest
# ==========================================================================


def write_manifest(built, report, verified):
    lines = [
        "# Sky Citadel weapons — manifest",
        "",
        "Generated by `build_sky_citadel_weapons.py`; do not edit by hand, re-run the",
        "script. The contract is `docs/WEAPONS.md`. Dimensions are X × Y × Z in studs",
        "(Z is the length; −Y is the edge/face). Triangles are per mesh (gauntlets: per",
        "hand). Bones in armature order; `Fx_` sockets and `Root` carry no geometry.",
        "",
        "| Object(s) | Future Id | Display name | Type | Rarity | Triangles | Dimensions | Bones | Palette colours | Design note |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    seen = {}
    for w, obj, arm in built:
        seen.setdefault((w.wtype, w.rarity, w.letter), []).append((w, obj))
    for key, entries in seen.items():
        w = entries[0][0]
        objs = " / ".join("`%s`" % o.name for _, o in entries)
        tris = " / ".join(str(report[o.name]["tris"]) for _, o in entries)
        d = report[entries[0][1].name]["dims"]
        dims = "%.2f × %.2f × %.2f" % d
        bones = ", ".join(report[entries[0][1].name]["bones"])
        cols = sorted(set().union(*[report[o.name]["colours"] for _, o in entries]), key=MAT_ORDER.index)
        lines.append("| %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            objs, w.cid, w.display, w.wtype.capitalize(), w.rarity.capitalize(), tris, dims, bones,
            ", ".join(cols), w.note))
    warns = [(n, x) for n, r in report.items() for x in r["warnings"]]
    lines += ["", "## Exports", ""]
    for v in verified:
        lines.append("- `%s` — %d meshes, %d armatures, re-import verified" % (v["file"], v["meshes"], v["armatures"]))
    lines += ["", "## Warnings", ""]
    lines += ["- `%s`: %s" % (n, x) for n, x in warns] or ["None."]
    lines.append("")
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


# ==========================================================================
# Review helpers (UI only -- not called by main)
# ==========================================================================

VIEWS = {
    "RIGHT": (90.0, 0.0, 90.0),    # from +X: the flats; +Y is screen right
    "FRONT": (90.0, 0.0, 0.0),     # from -Y: the edge
    "THREE_Q": (72.0, 0.0, 58.0),
}


def screenshot(path, centre, distance, view="RIGHT", only=None, perspective=False, overlays=False):
    """Viewport capture of the first 3D view. `only` names the collections to
    leave visible (the scale reference always stays)."""
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            r3d = space.region_3d
            region = next(r for r in area.regions if r.type == "WINDOW")
            space.shading.type = "SOLID"
            space.shading.color_type = "MATERIAL"
            space.shading.light = "STUDIO"
            space.overlay.show_overlays = overlays
            r3d.view_perspective = "PERSP" if perspective else "ORTHO"
            r3d.view_rotation = Euler([math.radians(a) for a in VIEWS[view]], "XYZ").to_quaternion()
            r3d.view_location = centre
            r3d.view_distance = distance
            hidden = []
            if only is not None:
                for lc in bpy.context.view_layer.layer_collection.children:
                    if lc.name.startswith("Weapons_") and lc.name not in only and not lc.hide_viewport:
                        lc.hide_viewport = True
                        hidden.append(lc)
            try:
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
                    bpy.ops.screen.screenshot_area(filepath=path)
            finally:
                for lc in hidden:
                    lc.hide_viewport = False
            return path
    raise RuntimeError("no 3D view to capture")


def scene_report(prefix="wpn_sc_"):
    """Read the scene back: what Blender actually contains."""
    out = {}
    for obj in sorted((o for o in bpy.data.objects if o.name.startswith(prefix) and o.type == "MESH"),
                      key=lambda o: o.name):
        arm = obj.parent
        mn, mx = local_bbox(obj)
        gname = {g.index: g.name for g in obj.vertex_groups}
        counts = {}
        for v in obj.data.vertices:
            for g in v.groups:
                counts[gname[g.group]] = counts.get(gname[g.group], 0) + 1
        out[obj.name] = {
            "rig": arm.name if arm else None,
            "tris": tri_count(obj.data),
            "dims": tuple(round(c, 3) for c in (mx - mn)),
            "z": (round(mn.z, 3), round(mx.z, 3)),
            "bones": ["%s%s" % (b.name, "" if b.use_deform else "*") for b in arm.data.bones] if arm else [],
            "verts_per_bone": counts,
        }
    return out


# ==========================================================================
# main
# ==========================================================================


def main(export=True, save=True, types=None):
    ref, built = build_all(types)
    ok, report = validate(built)
    layout(built)
    out = {"valid": ok, "report": report}
    if export:
        if not ok:
            bad = {k: v["errors"] for k, v in report.items() if v["errors"]}
            raise RuntimeError("validation failed; not exporting: %r" % bad)
        verified = []
        for wtype in TYPE_ORDER:
            items = [b for b in built if b[0].wtype == wtype]
            if not items:
                continue
            path = export_type(wtype, items)
            v = verify_export(path, wtype, items)
            if v["errors"]:
                raise RuntimeError("export verification failed for %s: %r" % (wtype, v["errors"]))
            verified.append(v)
        out["exported"] = verified
        write_manifest(built, report, verified)
    if save:
        os.makedirs(SOURCE_DIR, exist_ok=True)
        prefs = bpy.context.preferences.filepaths
        keep = prefs.save_version
        prefs.save_version = 0          # no .blend1 beside the output
        try:
            bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
        finally:
            prefs.save_version = keep
    return out


if __name__ == "__main__":
    import sys
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    print(main(export="--export" in argv))
