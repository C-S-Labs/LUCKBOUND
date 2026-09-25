# LUCKBOUND - Sky Citadel BASIC enemy: Lantern Wisp (close range, low hover at chest height).
# An ember spirit bound inside a brass lantern cage from the Lantern Row. Attacks: cage swing (the cage swings
# on its bail like a flail), ember burst (windup: flame swells + brightens). Pops in a flare on death.
# ~1.2 m tall incl. tail, hovers so the cage sits at sword height. Budget < 10k tris (target ~2-3k).
# Glow is split into its own mesh (for the flicker / windup brighten in Studio).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

NAME = "LanternWisp"
OFFSET = (5.0, 0.0, -0.45)          # where it stands in the shared Sky Citadel enemy scene
KIT = FW + r"\enemy_kit.py"

BONES = [
    ("Root", (0, 0, 1.00), (0, 0, 1.20), None),
    ("Body", (0, 0, 1.20), (0, 0, 1.55), "Root"),
    ("Cage", (0, 0, 2.02), (0, 0, 1.50), "Body"),          # pivots at the bail: swing attack
    ("Flame", (0, 0, 1.35), (0, 0, 1.75), "Cage"),
    ("Tail1", (0, 0, 1.22), (0, 0.03, 1.00), "Cage"),
    ("Tail2", (0, 0.03, 1.00), (0, 0.08, 0.80), "Tail1"),
    ("Tail3", (0, 0.08, 0.80), (0, 0.15, 0.62), "Tail2"),
    ("VFX_Core", (0, 0, 1.50), (0, -0.15, 1.50), "Flame"),
]
BIDX = {b[0]: i for i, b in enumerate(BONES)}
PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(KIT).read())

MATS = [
    mat("LW_Brass", (0.62, 0.44, 0.18), 1.0, 0.22),
    mat("LW_BrassDark", (0.30, 0.20, 0.08), 1.0, 0.3),
    mat("LW_Soot", (0.03, 0.028, 0.03), 0.3, 0.35),
    mat("LW_Core", (1.0, 0.7, 0.3), 0.0, 0.3, (1.0, 0.55, 0.1), 1.6),
    mat("LW_Spare", (0.5, 0.5, 0.5), 0.0, 0.3),
    mat("LW_Flame", (0.95, 0.22, 0.0), 0.0, 0.3, (1.0, 0.22, 0.0), 0.9),
]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BRASS, DARK, SOOT, CORE = PATINA, BRONZE, IRON, IVORY

# ---- lantern crown + bail ----
loft("Cage", BRASS, [(1.88, .17, .17), (1.92, .18, .18), (1.97, .13, .13), (2.02, .06, .06), (2.05, .02, .02)], N=20, sub=1)
loft("Cage", DARK, [(1.905, .185, .185), (1.925, .185, .185)], N=20)
for k in range(8):   # crown vents
    a = k*math.pi/4
    box("Cage", SOOT, (0.12*math.cos(a), 0.12*math.sin(a), 1.965), (0.035, 0.012, 0.02), rot=(0.6, 0, a + math.pi/2), bev=0.004, segs=1)
pts = [Vector((0.09*math.cos(t), 0, 2.02 + 0.10*math.sin(t))) for t in [math.pi*i/8 for i in range(9)]]
for a_, b_ in zip(pts, pts[1:]):
    tube("Cage", DARK, tuple(a_), tuple(b_), 0.012, 0.012, N=6)                       # bail loop
sph("Cage", BRASS, (0, 0, 2.12), 0.022, u=10, v=6)
# ---- cage: 6 curved bars between top and bottom rings ----
loft("Cage", BRASS, [(1.86, .165, .165), (1.89, .17, .17)], N=24)
loft("Cage", BRASS, [(1.22, .11, .11), (1.26, .12, .12)], N=24)
for k in range(6):
    a = k*math.pi/3 + math.pi/6
    prof = [(1.88, .16), (1.72, .21), (1.52, .215), (1.36, .17), (1.25, .115)]
    ps = [Vector((r*math.cos(a), r*math.sin(a), z)) for z, r in prof]
    for p0, p1 in zip(ps, ps[1:]):
        tube("Cage", DARK, tuple(p0), tuple(p1), 0.014, 0.014, N=6)
    for p in ps[1:-1]:
        sph("Cage", BRASS, tuple(p), 0.02, u=8, v=6)                                   # rivets
# ---- base: soot bowl + drip spike ----
loft("Cage", SOOT, [(1.26, .11, .11), (1.20, .09, .09), (1.14, .04, .04)], N=16, sub=1)
loft("Cage", BRASS, [(1.14, .035, .035), (1.06, .004, .004)], N=10)
# ---- the ember spirit: teardrop flame, bright core, dark slit eyes ----
loft("Flame", GLOW, [(1.30, .03, .03), (1.36, .10, .10), (1.48, .13, .12), (1.60, .10, .09), (1.72, .05, .04),
                     (1.80, .008, .008)], N=16, sub=1)
sph("VFX_Core", CORE, (0, -0.02, 1.47), 0.06, u=12, v=8)
for s in (1, -1):
    tube("Flame", SOOT, (0.018*s, -0.123, 1.52), (0.065*s, -0.112, 1.545), 0.009, 0.006, N=6)       # angled slit eyes
# ---- ember tail trailing below the cage ----
loft("Tail1", GLOW, [(1.14, .05, .05), (1.02, .045, .04, 2, 0, .02)], N=12, sub=1)
loft("Tail2", GLOW, [(1.05, .04, .035, 2, 0, .02), (0.82, .03, .025, 2, 0, .07)], N=12, sub=1)
loft("Tail3", GLOW, [(0.85, .025, .02, 2, 0, .07), (0.62, .003, .003, 2, 0, .15)], N=10, sub=1)
# ---- orbiting ember motes ----
for k in range(3):
    a = k*2*math.pi/3
    gem("Body", GLOW, (0.34*math.cos(a), 0.34*math.sin(a), 1.45 + 0.08*k), 0.02, 0.03, sides=5)

# ---- v2 character pass (2026-09-24): an ornate citadel lantern with a mischievous flame spirit inside ----
# spired crown + finial, filigree scrolls on every bar, chain stub on the bail, hanging tassel charms,
# flame tongues licking out between the bars, flame "arms" gesturing, a grinning mouth, more ember motes.
loft("Cage", BRASS, [(2.05, .03, .03), (2.09, .045, .045), (2.13, .02, .02), (2.24, .004, .004)], N=12, sub=1)   # spire finial
for k in range(8):                                                     # crown fins (ornamental)
    a = k*math.pi/4 + math.pi/8
    blade("Cage", BRASS, (0.15*math.cos(a), 0.15*math.sin(a), 1.95), (math.cos(a)*0.5, math.sin(a)*0.5, 1.0), 0.09, 0.03, 0.008, hint=(-math.sin(a), math.cos(a), 0), N=6, sub=0)
for i in range(3):                                                     # chain stub above the bail
    loft("Cage", DARK, [(-0.004, .02, .012), (0.004, .02, .012)], N=10, M=TR((0, 0, 2.17 + 0.035*i), (0, 0, math.pi/2*i)), cap=False)
for k in range(6):                                                     # leaf filigree plates on the bars (flat, on the bar)
    a = k*math.pi/3 + math.pi/6
    for z, r in ((1.62, .214), (1.44, .205)):
        c_ = Vector((r*math.cos(a), r*math.sin(a), z))
        blade("Cage", BRASS, tuple(c_ + Vector((0, 0, 0.04))), (0, 0, -1), 0.08, 0.035, 0.008, hint=(math.cos(a), math.sin(a), 0), N=6, sub=0)
for k in range(3):                                                     # hanging tassel charms off the base ring
    a = k*2*math.pi/3
    c_ = Vector((0.11*math.cos(a), 0.11*math.sin(a), 1.2))
    tube("Cage", DARK, tuple(c_), tuple(c_ + Vector((0, 0, -0.1))), 0.005, 0.005, N=5)
    gem("Cage", CORE, tuple(c_ + Vector((0, 0, -0.12))), 0.018, 0.03, rot=(math.pi, 0, 0), sides=5)
for k in range(6):                                                     # flame tongues licking out between the bars
    a = k*math.pi/3
    blade("Flame", GLOW, (0.1*math.cos(a), 0.1*math.sin(a), 1.5 + 0.05*(k % 2)), (math.cos(a), math.sin(a), 0.9), 0.12, 0.04, 0.016, hint=(0, 0, 1), N=6)
for sd in (1, -1):                                                     # flame arms, one raised (cheeky), one low
    arm = [Vector((0.09*sd, -0.03, 1.46)), Vector((0.15*sd, -0.02, 1.47 + (0.05 if sd > 0 else -0.04))), Vector((0.185*sd, -0.02, 1.54 + (0.09 if sd > 0 else -0.08)))]
    for a_, b_ in zip(arm, arm[1:]):
        tube("Flame", GLOW, tuple(a_), tuple(b_), 0.028, 0.02, N=8)
    gem("Flame", GLOW, tuple(arm[-1]), 0.035, 0.05, rot=(0, 0.6*sd, 0), sides=5)
m_ = [Vector((0.05*t, -0.124 + 0.012*t*t, 1.462 - 0.022*(1 - t*t))) for t in [i/4 - 1 for i in range(9)]]   # crooked grin
for a_, b_ in zip(m_, m_[1:]):
    tube("Flame", SOOT, tuple(a_), tuple(b_), 0.006, 0.006, N=5)
for k in range(5):                                                     # more ember motes, spiralling
    a = k*2*math.pi/5 + 0.4
    gem("Body", GLOW, (0.3*math.cos(a), 0.3*math.sin(a), 1.3 + 0.1*k), 0.015, 0.025, sides=5)

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
bmesh.ops.delete(glow, geom=[f for f in glow.faces if f.material_index not in (GLOW, CORE)], context='FACES')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in (GLOW, CORE)], context='FACES')
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
