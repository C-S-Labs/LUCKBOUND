# LUCKBOUND - Ethereal Scape BASIC enemy: Aether Wisp (close range, hover; the tutorial enemy).
# A drifting spirit of bound aether: a soft glass teardrop body around a slow-pulsing portal-glow
# core, a thin gold halo ring orbiting loose, and trailing indigo/teal ribbon tendrils. No limbs --
# it hovers at chest height so it comes into sword range on its own (flyer contract: it must
# regularly close to melee, same rule as Sky Citadel's Aviary Harrier / Lantern Wisp).
# Attacks: a slow drifting charge (telegraphed by the core brightening) and a ribbon lash.
# ~1.0 m incl. tendrils. Budget < 10k tris (target ~2-4k, matching Lantern Wisp's scale).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

NAME = "AetherWisp"
OFFSET = (0.0, 0.0, 0.0)
KIT = FW + r"\enemy_kit.py"

BONES = [
    ("Root", (0, 0, 0.85), (0, 0, 1.05), None),
    ("Body", (0, 0, 1.05), (0, 0, 1.35), "Root"),
    ("Core", (0, 0, 1.20), (0, -0.12, 1.20), "Body"),
    ("Halo", (0, 0, 1.20), (0.25, 0, 1.20), "Body"),
    ("Tail1", (0, 0.05, 1.08), (0, 0.10, 0.88), "Body"),
    ("Tail2", (0, 0.10, 0.88), (0.04, 0.16, 0.68), "Tail1"),
    ("Tail3", (0.04, 0.16, 0.68), (0.08, 0.20, 0.50), "Tail2"),
    ("Tail1B", (-0.06, 0.03, 1.05), (-0.09, 0.08, 0.84), "Body"),
    ("Tail2B", (-0.09, 0.08, 0.84), (-0.12, 0.13, 0.62), "Tail1B"),
    ("VFX_Core", (0, -0.12, 1.20), (0, -0.30, 1.20), "Core"),
]
BIDX = {b[0]: i for i, b in enumerate(BONES)}
PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(KIT).read())

MATS = [
    mat("AW_Glass", (0.72, 0.93, 0.86), 0.0, 0.06, (0.45, 0.9, 0.75), 0.4),
    mat("AW_Gold", (0.87, 0.70, 0.38), 1.0, 0.2),
    mat("AW_Teal", (0.22, 0.48, 0.42), 0.0, 0.4),
    mat("AW_Indigo", (0.34, 0.36, 0.62), 0.0, 0.4),
    mat("AW_Spare", (0.5, 0.5, 0.5), 0.0, 0.3),
    mat("AW_Glow", (0.8, 1.0, 0.9), 0.0, 0.2, (0.55, 1.0, 0.8), 2.8),
]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
GLASS, GOLD, TEAL, INDIGO = PATINA, BRONZE, IRON, IVORY

# ---- body: a soft glass teardrop, wider at the top, tapering down ----
loft("Body", GLASS, [(1.34, .03, .03), (1.30, .14, .14), (1.20, .175, .175), (1.10, .15, .15), (1.02, .07, .07), (0.97, .02, .02)],
     N=40, M=TR((0, 0, 0)), sub=2)
# ---- detail: gold waist band, crown gem, small inner halo ----
arc_band("Body", GOLD, (0, 0), 1.105, 1.09, (0.138, 0.138), (0.14, 0.14), 0, 2 * math.pi, 0.018, 28)
gem("Body", GLOW, (0, 0, 1.36), 0.03, 0.06, sides=6)
arc_band("Halo", GOLD, (0, 0), 1.315, 1.305, (0.105, 0.105), (0.11, 0.11), 0, 2 * math.pi, 0.02, 48)
# ---- glowing core, visible through the glass ----
sph("Core", GLOW, (0, -0.02, 1.20), 0.075, u=32, v=20)
sph("VFX_Core", GLOW, (0, -0.12, 1.20), 0.03, u=10, v=8)
# ---- loose gold halo ring, orbiting the body ----
arc_band("Halo", GOLD, (0, 0), 1.235, 1.225, (0.22, 0.22), (0.24, 0.24), 0, 2 * math.pi, 0.012, 64)
for k in range(3):
    a = k * 2 * math.pi / 3
    sph("Halo", GOLD, (0.23 * math.cos(a), 0.23 * math.sin(a), 1.20), 0.018, u=8, v=6)
# ---- twin trailing tendrils: teal + indigo, glowing tips ----
loft("Tail1", TEAL, [(1.08, .045, .04, 2, 0, .02), (0.90, .038, .032, 2, 0, .04)], N=16, sub=1)
loft("Tail2", TEAL, [(0.90, .036, .03, 2, 0, .04), (0.70, .022, .018, 2, 0, .06)], N=14, sub=1)
loft("Tail3", GLOW, [(0.70, .020, .016, 2, 0, .06), (0.52, .004, .004, 2, 0, .09)], N=8)
loft("Tail1B", INDIGO, [(1.06, .036, .032, 2, 0, .015), (0.86, .028, .024, 2, 0, .03)], N=14, sub=1)
loft("Tail2B", GLOW, [(0.86, .026, .022, 2, 0, .03), (0.64, .003, .003, 2, 0, .05)], N=8)
loft("Tail1B", TEAL, [(1.05, .03, .026, 2, 0, -.02), (0.80, .016, .014, 2, 0, -.04)], N=14, sub=1)
loft("Tail1B", GLOW, [(0.83, .015, .013, 2, 0, -.035), (0.66, .002, .002, 2, 0, -.05)], N=8)
# ---- halo spokes: thin gold struts tie the outer halo to the body so nothing floats ----
for k in range(3):
    a = k * 2 * math.pi / 3
    tube("Halo", GOLD, (0.14 * math.cos(a), 0.14 * math.sin(a), 1.21), (0.235 * math.cos(a), 0.235 * math.sin(a), 1.23), 0.008, 0.008, N=6)

# ---- assemble: body + glow meshes on one rig, placed at OFFSET ----
arm_data = bpy.data.armatures.new(NAME + "_Rig")
rig = bpy.data.objects.new(NAME + "_Rig", arm_data)
coll = bpy.context.scene.collection
coll.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for n, h, t, p in BONES:
    b = arm_data.edit_bones.new(n); b.head, b.tail = h, t
    if p: b.parent = eb[p]
    eb[n] = b
bpy.ops.object.mode_set(mode='OBJECT')
arm_data.display_type = 'STICK'
bm = PIECES.pop("Body")
glow = bm.copy()
bmesh.ops.delete(glow, geom=[f for f in glow.faces if f.material_index != GLOW], context='FACES')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == GLOW], context='FACES')
PARTS = []
for nm, b_ in ((f"{NAME}_Body", bm), (f"{NAME}_Glow", glow)):
    me = bpy.data.meshes.new(nm); b_.to_mesh(me); b_.free()
    for m in MATS: me.materials.append(m)
    o = bpy.data.objects.new(nm, me)
    for b in BONES: o.vertex_groups.new(name=b[0])
    coll.objects.link(o); o.parent = rig
    o.modifiers.new("Armature", 'ARMATURE').object = rig
    PARTS.append(o)
    print(f"PIECE {nm}: {sum(len(p.vertices) - 2 for p in me.polygons)} tris")
rig.location = OFFSET
