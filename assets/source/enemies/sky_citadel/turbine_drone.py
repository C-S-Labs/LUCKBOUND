# LUCKBOUND - Sky Citadel BASIC enemy: Turbine Drone (Turbine Hall). Flies between perches, then CLAMPS to the
# floor/wall with three legs to attack (so it is always in sword range while dangerous):
#   clamped: spinning blade-ring sweep around itself; kamikaze spin-up charge (parry slams it down, stunned).
# Breaking the clamp legs stuns it. Bronze hull, teal ducted rotors, cyclops lens. Budget < 10k tris.
# Rig: Root > Hull > RotorA/B/C (spin), LegA/B/C 1+2 (clamp), BladeRing (spin), Lens.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

NAME = "TurbineDrone"
OFFSET = (10.0, 0.0, 0.0)
KIT = FW + r"\enemy_kit.py"
HZ = 1.15   # hover height of the hull centre (clamped pose lowers it)

BONES = [("Root", (0, 0, HZ - 0.3), (0, 0, HZ - 0.1), None),
         ("Hull", (0, 0, HZ - 0.1), (0, 0, HZ + 0.25), "Root"),
         ("Lens", (0, -0.2, HZ + 0.08), (0, -0.38, HZ + 0.08), "Hull"),
         ("BladeRing", (0, 0, HZ - 0.052), (0, 0, HZ + 0.048), "Hull")]
ARMS = []
for i, L in enumerate("ABC"):
    a = math.pi/2 + i*2*math.pi/3   # A points back (+Y), B/C forward-sides; lens faces -Y between them
    d = Vector((math.cos(a), math.sin(a), 0))
    ARMS.append((L, a, d))
    BONES.append((f"Rotor{L}", tuple(d*0.55 + Vector((0, 0, HZ + 0.02))), tuple(d*0.55 + Vector((0, 0, HZ + 0.2))), "Hull"))
    BONES.append((f"Leg{L}1", tuple(d*0.2 + Vector((0, 0, HZ - 0.12))), tuple(d*0.38 + Vector((0, 0, HZ - 0.38))), "Hull"))
    BONES.append((f"Leg{L}2", tuple(d*0.38 + Vector((0, 0, HZ - 0.38))), tuple(d*0.34 + Vector((0, 0, HZ - 0.72))), f"Leg{L}1"))
BIDX = {b[0]: i for i, b in enumerate(BONES)}
PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(KIT).read())

MATS = [
    mat("TD_Bronze", (0.55, 0.35, 0.14), 1.0, 0.24),
    mat("TD_Teal", (0.08, 0.36, 0.36), 0.7, 0.22),
    mat("TD_Iron", (0.05, 0.055, 0.06), 0.6, 0.35),
    mat("TD_Brass", (0.75, 0.6, 0.3), 1.0, 0.18),
    mat("TD_Spare", (0.5, 0.5, 0.5), 0.0, 0.3),
    mat("TD_Glow", (0.2, 0.95, 0.85), 0.0, 0.3, (0.15, 0.9, 0.8), 2.5),
]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BR, TEAL, IR, BRASS = PATINA, BRONZE, IRON, IVORY

# ---- hull: squat bronze turbine body with teal band, vents, top fan hub ----
loft("Hull", BR, [(HZ - 0.20, .12, .12), (HZ - 0.12, .26, .26), (HZ + 0.02, .30, .30), (HZ + 0.12, .27, .27),
                  (HZ + 0.20, .16, .16), (HZ + 0.24, .06, .06)], N=28, sub=1)
loft("Hull", TEAL, [(HZ - 0.02, .305, .305), (HZ + 0.05, .305, .305)], N=28)
for k in range(10):
    a = k*2*math.pi/10
    if abs(math.sin(a) + 1) < 0.4:   # leave the lens clear at the front
        continue
    box("Hull", IR, (0.29*math.cos(a), 0.29*math.sin(a), HZ + 0.10), (0.05, 0.02, 0.03), rot=(0, 0, a + math.pi/2), bev=0.005, segs=1)
loft("Hull", BRASS, [(HZ + 0.24, .07, .07), (HZ + 0.28, .05, .05), (HZ + 0.30, .015, .015)], N=16)
# ---- cyclops lens (front, -Y) ----
loft("Lens", BRASS, [(0, .11, .11), (0.03, .12, .12), (0.05, .10, .10)], N=20, M=TR((0, -0.27, HZ + 0.1), (math.pi/2, 0, 0)))
loft("Lens", IR, [(0.03, .085, .085), (0.06, .08, .08)], N=20, M=TR((0, -0.27, HZ + 0.1), (math.pi/2, 0, 0)))
sph("Lens", GLOW, (0, -0.325, HZ + 0.1), 0.06, scale=(1, 0.5, 1), u=16, v=10)
# ---- three arms with ducted rotors ----
for L, a, d in ARMS:
    side = Vector((-d.y, d.x, 0))
    tube("Hull", BR, tuple(d*0.24 + Vector((0, 0, HZ + 0.04))), tuple(d*0.46 + Vector((0, 0, HZ + 0.06))), 0.045, 0.035, N=10)
    c = d*0.55 + Vector((0, 0, HZ + 0.06))
    loft("Hull", TEAL, [(c.z - 0.06, .17, .17), (c.z - 0.04, .19, .19), (c.z + 0.05, .19, .19), (c.z + 0.07, .17, .17)],
         N=28, M=TR((c.x, c.y, 0)), cap=False)                                                 # duct (open)
    loft("Hull", IR, [(c.z - 0.045, .165, .165), (c.z + 0.055, .165, .165)], N=28, M=TR((c.x, c.y, 0)), cap=False)
    loft("Hull", BRASS, [(c.z + 0.065, .195, .195), (c.z + 0.08, .195, .195)], N=28, M=TR((c.x, c.y, 0)), cap=False)
    sph(f"Rotor{L}", BRASS, tuple(c), 0.04, u=10, v=6)
    for k in range(5):                                                                          # fan blades
        b_ = k*2*math.pi/5
        blade(f"Rotor{L}", TEAL, tuple(c), (math.cos(b_), math.sin(b_), 0.12), 0.15, 0.05, 0.008,
              hint=(0, 0, 1), N=6, sub=0)
    # clamp leg: two segments ending in a three-claw foot
    h1 = Vector(BONES[BIDX[f"Leg{L}1"]][1]); k1 = Vector(BONES[BIDX[f"Leg{L}1"]][2]); f1 = Vector(BONES[BIDX[f"Leg{L}2"]][2])
    sph(f"Leg{L}1", IR, tuple(h1), 0.045, u=10, v=6)
    tube(f"Leg{L}1", BR, tuple(h1), tuple(k1), 0.035, 0.03, N=10)
    sph(f"Leg{L}2", BRASS, tuple(k1), 0.038, u=10, v=6)
    tube(f"Leg{L}2", IR, tuple(k1), tuple(f1), 0.028, 0.02, N=10)
    for cl in (-0.6, 0, 0.6):
        dd = (d*math.cos(cl) + side*math.sin(cl)).normalized()
        blade(f"Leg{L}2", BRASS, tuple(f1), tuple(dd*0.8 + Vector((0, 0, -0.5))), 0.09, 0.025, 0.012, hint=(0, 0, 1), N=6, sub=0)
# ---- blade ring: a spinning COLLAR round the hull waist, in the clear band between the rotor arms (above) and the
#      leg hips (below) - nothing crosses that band, so the ring spins 360 deg without touching arms or legs ----
RZ = HZ - 0.052
loft("BladeRing", IR, [(RZ - 0.018, .292, .292), (RZ + 0.018, .292, .292)], N=28)
loft("BladeRing", GLOW, [(RZ - 0.004, .297, .297), (RZ + 0.004, .297, .297)], N=28, cap=False)
# ---- v2 character pass (2026-09-24), shaped by the moveset ----
#  * CLAMP legs are the weak point (breaking them stuns it): heavy armoured legs, 3-prong grip claws, and a glowing
#    cyan joint core on every knee = "hit here".
#  * BLADE-RING sweep: the belly ring becomes 8 curved scythe blades with glowing edges (reads dangerous from afar).
#  * SPIN-UP charge tell: top turbine intake with a visible fan + heat vents that glow when it spins up.
#  * Cyclops lens gets an armoured hood with shutter blades (aggressive "brow").
for i in range(8):                                                     # scythe blades, flat in the collar plane
    a = i*math.pi/4
    d_ = Vector((math.cos(a), math.sin(a), 0)); t_ = Vector((-math.sin(a), math.cos(a), 0))
    root = d_*0.29 + Vector((0, 0, RZ))
    blade("BladeRing", BRASS, tuple(root), tuple(d_*0.7 + t_*0.7), 0.24, 0.045, 0.01, hint=(0, 0, 1), N=5, sub=0)
    tube("BladeRing", GLOW, tuple(root + (d_*0.7 + t_*0.7).normalized()*0.03 + t_*0.012), tuple(root + (d_*0.7 + t_*0.7).normalized()*0.2 + t_*0.008), 0.004, 0.003, N=5)
loft("Hull", TEAL, [(HZ + 0.2, .16, .16), (HZ + 0.26, .15, .15), (HZ + 0.27, .12, .12)], N=24, sub=1)      # top intake cowl
loft("Hull", IR, [(HZ + 0.262, .118, .118), (HZ + 0.266, .118, .118)], N=24)
for i in range(7):                                                     # intake fan blades
    a = i*2*math.pi/7
    blade("Hull", BRASS, (0, 0, HZ + 0.262), (math.cos(a), math.sin(a), 0.05), 0.11, 0.035, 0.006, hint=(-math.sin(a)*0.5, math.cos(a)*0.5, 1), N=5, sub=0)
sph("Hull", BRASS, (0, 0, HZ + 0.27), 0.03, u=10, v=6)
for k in range(10):                                                    # heat vents glow (spin-up tell), under the hull vents
    a = k*2*math.pi/10
    if abs(math.sin(a) + 1) < 0.4: continue
    box("Hull", GLOW, (0.296*math.cos(a), 0.296*math.sin(a), HZ + 0.075), (0.04, 0.012, 0.012), rot=(0, 0, a + math.pi/2), bev=0.003, segs=1)
# lens hood + shutter blades (angled down at the front = mean)
loft("Lens", BR, [(0.0, .13, .13), (0.07, .135, .135)], N=20, M=_frame(Vector((0, -0.27, HZ + 0.1)), Vector((0, -1, 0)), hint=(0, 0, 1)), keep=lambda c: c.z > HZ + 0.11, fill=False, cap=False)
for sd in (1, -1):
    blade("Lens", BRASS, (0.02*sd, -0.34, HZ + 0.18), (0.9*sd, -0.1, -0.35), 0.12, 0.03, 0.008, hint=(0, 0, 1), N=6, sub=0)
# armoured clamp legs: plates on both segments, glowing knee core (weak point), 3-prong grip claw
for L, a, d in ARMS:
    k0 = Vector(BONES[BIDX[f"Leg{L}1"]][1]); kn = Vector(BONES[BIDX[f"Leg{L}1"]][2]); ft = Vector(BONES[BIDX[f"Leg{L}2"]][2])
    for bn, p0, p1, w in ((f"Leg{L}1", k0, kn, 0.05), (f"Leg{L}2", kn, ft, 0.042)):
        dd = p1 - p0
        loft(bn, BR, [(0.02, w, w*0.7, 2.6), (dd.length*0.5, w*1.1, w*0.75, 2.6), (dd.length*0.9, w*0.7, w*0.55, 2.6)], N=12, M=_frame(p0, dd, hint=(0, 0, 1)), sub=0)
    sph(f"Leg{L}2", IR, tuple(kn), 0.045, u=12, v=8)
    loft(f"Leg{L}2", GLOW, [(-0.012, .048, .048), (0.012, .048, .048)], N=16, M=_frame(kn, ft - kn), cap=False)
    sph(f"Leg{L}2", GLOW, tuple(kn + d*0.035), 0.022, u=10, v=6)
    for j_ in range(3):
        b_ = j_*2*math.pi/3 + a
        pd = Vector((math.cos(b_)*0.6, math.sin(b_)*0.6, -1))
        blade(f"Leg{L}2", BRASS, tuple(ft + Vector((0, 0, 0.03))), tuple(pd), 0.09, 0.025, 0.012, hint=(0, 0, 1), N=5, sub=0)

# ---- assemble ----
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
