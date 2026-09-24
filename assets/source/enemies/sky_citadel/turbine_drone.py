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
         ("Lens", (0, -0.2, HZ), (0, -0.38, HZ), "Hull"),
         ("BladeRing", (0, 0, HZ - 0.22), (0, 0, HZ - 0.12), "Hull")]
ARMS = []
for i, L in enumerate("ABC"):
    a = math.pi/2 + i*2*math.pi/3 + math.pi   # A points back, B/C forward-sides
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
loft("Lens", BRASS, [(0, .11, .11), (0.03, .12, .12), (0.05, .10, .10)], N=20, M=TR((0, -0.27, HZ + 0.02), (math.pi/2, 0, 0)))
loft("Lens", IR, [(0.03, .085, .085), (0.06, .08, .08)], N=20, M=TR((0, -0.27, HZ + 0.02), (math.pi/2, 0, 0)))
sph("Lens", GLOW, (0, -0.325, HZ + 0.02), 0.06, scale=(1, 0.5, 1), u=16, v=10)
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
# ---- belly blade ring (spins in the clamped sweep attack) ----
loft("BladeRing", IR, [(HZ - 0.23, .10, .10), (HZ - 0.19, .10, .10)], N=20)
for k in range(8):
    b_ = k*2*math.pi/8
    blade("BladeRing", BRASS, (0.09*math.cos(b_), 0.09*math.sin(b_), HZ - 0.21), (math.cos(b_ + 0.5), math.sin(b_ + 0.5), 0),
          0.22, 0.045, 0.01, hint=(0, 0, 1), N=6, sub=0)
loft("BladeRing", GLOW, [(HZ - 0.215, .105, .105), (HZ - 0.205, .105, .105)], N=20)

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
