# LUCKBOUND - Sky Citadel BASIC enemy: Prism Crawler (Prism Arena). Six-legged crystal crawler.
# Long range but punishable: slowly charges a refracting beam from the prism on its back (long windup, the prism
# brightens), fires, then OVERHEATS (vents open, prism dims) -> big punish window. Can burrow into a crystal shell.
# Clear/aqua crystal with rainbow-edged facets, dark slate carapace joints. Budget < 10k tris.
# Rig: Root > Body > Prism (aim/tilt), Head, Mandibles L/R, 6 legs x 3 bones.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

NAME = "PrismCrawler"
OFFSET = (15.0, 0.0, 0.0)
KIT = FW + r"\enemy_kit.py"
BZ = 0.55     # body height

BONES = [("Root", (0, 0.1, BZ - 0.2), (0, 0.1, BZ), None),
         ("Body", (0, 0.25, BZ), (0, -0.25, BZ), "Root"),
         ("Head", (0, -0.28, BZ), (0, -0.55, BZ - 0.02), "Body"),
         ("MandibleL", (0.07, -0.5, BZ - 0.05), (0.09, -0.66, BZ - 0.08), "Head"),
         ("MandibleR", (-0.07, -0.5, BZ - 0.05), (-0.09, -0.66, BZ - 0.08), "Head"),
         ("Prism", (0, 0.05, BZ + 0.15), (0, 0.05, BZ + 0.75), "Body"),
         ("VFX_Beam", (0, -0.05, BZ + 0.62), (0, -0.4, BZ + 0.62), "Prism")]
LEGS = []
for i, (s, y) in enumerate([(s, y) for y in (-0.15, 0.08, 0.3) for s in (1, -1)]):
    L = f"Leg{'L' if s > 0 else 'R'}{i//2 + 1}"
    hip = Vector((0.18*s, y, BZ)); knee = Vector((0.45*s, y + 0.02*(i//2 - 1)*3, BZ + 0.22)); foot = Vector((0.68*s, y + 0.05*(i//2 - 1)*3, 0.0))
    ankle = knee.lerp(foot, 0.55) + Vector((0.05*s, 0, 0))
    LEGS.append((L, s, hip, knee, ankle, foot))
    BONES += [(L + "1", tuple(hip), tuple(knee), "Body"), (L + "2", tuple(knee), tuple(ankle), L + "1"), (L + "3", tuple(ankle), tuple(foot), L + "2")]
BIDX = {b[0]: i for i, b in enumerate(BONES)}
PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(KIT).read())

MATS = [
    mat("PC_Crystal", (0.55, 0.85, 0.9), 0.0, 0.05),
    mat("PC_Rainbow", (0.75, 0.55, 0.95), 0.2, 0.08),
    mat("PC_Slate", (0.10, 0.12, 0.16), 0.5, 0.25),
    mat("PC_Frost", (0.85, 0.95, 1.0), 0.0, 0.1),
    mat("PC_Spare", (0.5, 0.5, 0.5), 0.0, 0.3),
    mat("PC_Glow", (0.5, 1.0, 1.0), 0.0, 0.2, (0.45, 1.0, 0.95), 2.5),
]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
CRY, RAIN, SLATE, FROST = PATINA, BRONZE, IRON, IVORY

# ---- faceted body: low-exponent lofts give crystal ridges; slate underplate ----
loft("Body", CRY, [(-0.28, .06, .05, 1.3), (-0.2, .2, .13, 1.3), (0.05, .26, .16, 1.3), (0.25, .2, .12, 1.3),
                   (0.38, .05, .04, 1.3)], N=14, M=TR((0, 0, BZ), (math.pi/2, 0, 0)), sub=1)
loft("Body", SLATE, [(-0.24, .15, .06), (0.3, .16, .06)], N=12, M=TR((0, 0, BZ - 0.1), (math.pi/2, 0, 0)))
for k in range(4):   # back crystal spines, rainbow edged
    y = -0.12 + k*0.12
    for s in (1, -1):
        blade("Body", RAIN if k % 2 else CRY, (0.1*s, y, BZ + 0.1), (0.5*s, 0.3, 1.0), 0.18 - 0.02*k, 0.05, 0.03, hint=(0, 1, 0), N=4, sub=0)
# ---- head + mandibles + eye cluster ----
loft("Head", CRY, [(0.26, .05, .04, 1.3), (0.32, .13, .09, 1.3), (0.48, .11, .08, 1.3), (0.56, .03, .03, 1.3)], N=12, sub=1,
     M=TR((0, 0, BZ), (math.pi/2, 0, 0)))
for s, bn in ((1, "MandibleL"), (-1, "MandibleR")):
    blade(bn, RAIN, (0.07*s, -0.5, BZ - 0.05), (0.25*s, -1.0, -0.2), 0.2, 0.035, 0.02, hint=(0, 0, 1), N=4, sub=0)
    for k in range(3):
        gem("Head", GLOW, (0.05*s + 0.02*k*s, -0.52 + 0.03*k, BZ + 0.04 + 0.015*k), 0.014, 0.012, rot=(math.pi/2, 0, 0), sides=5)
# ---- the prism: tall hexagonal crystal on the back, glowing core, slate mount with vents ----
loft("Body", SLATE, [(BZ + 0.08, .14, .14), (BZ + 0.16, .12, .12)], N=6, M=TR((0, 0.05, 0)))
for k in range(6):
    a = k*math.pi/3
    box("Body", SLATE, (0.13*math.cos(a), 0.05 + 0.13*math.sin(a), BZ + 0.12), (0.05, 0.02, 0.04), rot=(0, 0, a + math.pi/2), bev=0.005, segs=1)
loft("Prism", CRY, [(BZ + 0.15, .10, .10, 2), (BZ + 0.25, .13, .13, 2), (BZ + 0.6, .11, .11, 2), (BZ + 0.78, .01, .01, 2)],
     N=6, M=TR((0, 0.05, 0)))
loft("Prism", GLOW, [(BZ + 0.3, .045, .045, 2), (BZ + 0.62, .03, .03, 2)], N=6, M=TR((0, 0.05, 0)))
for k in range(3):   # small satellite prisms
    a = k*2*math.pi/3 + 0.3
    loft("Prism", RAIN, [(BZ + 0.18, .04, .04, 2), (BZ + 0.36, .035, .035, 2), (BZ + 0.44, .005, .005, 2)], N=6,
         M=TR((0.15*math.cos(a), 0.05 + 0.15*math.sin(a), 0)))
# ---- six legs: slate joints, crystal segments, sharp crystal feet ----
for L, s, hip, knee, ankle, foot in LEGS:
    sph(L + "1", SLATE, tuple(hip), 0.05, u=8, v=6)
    loft(L + "1", CRY, [(0, .042, .042, 1.4), ((knee - hip).length*0.5, .05, .05, 1.4), ((knee - hip).length, .036, .036, 1.4)], N=8, M=_frame(hip, knee - hip), sub=1)
    sph(L + "2", SLATE, tuple(knee), 0.04, u=8, v=6)
    loft(L + "2", CRY, [(0, .034, .034, 1.4), ((ankle - knee).length*0.4, .04, .04, 1.4), ((ankle - knee).length, .026, .026, 1.4)], N=8, M=_frame(knee, ankle - knee), sub=1)
    sph(L + "3", SLATE, tuple(ankle), 0.03, u=8, v=6)
    loft(L + "3", RAIN, [(0, .025, .025, 1.5), ((foot - ankle).length, .004, .004, 1.5)], N=5, M=_frame(ankle, foot - ankle))

# ---- v2 character pass (2026-09-24), shaped by the moveset ----
#  * BEAM CHARGE: three refraction rings float round the prism + lens shards feeding light up it (brighten = tell).
#  * OVERHEAT: six slate vent flaps round the prism mount with glowing heat slots under them (they open = opening).
#  * BURROW: overlapping carapace plates down the back that close into a shell; crystal cluster on the tail.
#  * Predatory head: brow crest, crystal horn, forward-swept mandible barbs.
for i, (z, r) in enumerate(((BZ + 0.3, 0.2), (BZ + 0.45, 0.17), (BZ + 0.58, 0.14))):     # refraction rings (on Prism)
    loft("Prism", RAIN, [(-0.008, r, r, 2), (0.008, r, r, 2)], N=6, M=TR((0, 0.05, z), (0, 0, 0.26*i)), cap=False)
    for k in range(3):
        a = k*2*math.pi/3 + 0.5*i
        gem("Prism", GLOW, (r*math.cos(a), 0.05 + r*math.sin(a), z), 0.018, 0.028, rot=(0, 0, a), sides=4)
for k in range(6):                                                               # vent flaps + heat slots
    a = k*math.pi/3 + math.pi/6
    c_ = Vector((0.16*math.cos(a), 0.05 + 0.16*math.sin(a), BZ + 0.1))
    blade("Body", SLATE, tuple(c_ + Vector((0, 0, 0.03))), (math.cos(a)*0.7, math.sin(a)*0.7, -0.6), 0.1, 0.07, 0.012, hint=(-math.sin(a), math.cos(a), 0), N=5, sub=0)
    box("Body", GLOW, tuple(c_ + Vector((-0.02*math.cos(a), -0.02*math.sin(a), 0.0))), (0.045, 0.012, 0.012), rot=(0, 0, a + math.pi/2), bev=0.003, segs=1)
for k in range(5):                                                               # overlapping carapace plates (burrow shell)
    y = -0.22 + k*0.11
    loft("Body", SLATE if k % 2 == 0 else CRY, [(-0.04, .2 - 0.012*abs(k - 2), .12, 1.6), (0.04, .21 - 0.012*abs(k - 2), .125, 1.6)], N=10,
         M=TR((0, y, BZ + 0.02), (math.pi/2, 0, 0)), keep=lambda c: c.z > BZ + 0.05, fill=False, cap=False)
for k in range(5):                                                               # tail crystal cluster
    a = k*2*math.pi/5
    loft("Body", RAIN if k % 2 else CRY, [(0, .03, .03, 1.5), (0.1 + 0.03*(k % 2), .025, .025, 1.5), (0.14 + 0.03*(k % 2), .003, .003, 1.5)], N=5,
         M=_frame(Vector((0.03*math.cos(a), 0.36 + 0.03*math.sin(a), BZ + 0.02)), Vector((0.5*math.cos(a), 1.0, 0.4 + 0.3*math.sin(a))) ))
loft("Head", CRY, [(0, .035, .03, 1.4), (0.14, .02, .018, 1.4), (0.2, .003, .003, 1.4)], N=5, M=_frame(Vector((0, -0.42, BZ + 0.07)), Vector((0, -0.6, 1))))   # horn
for sd in (1, -1):
    blade("Head", SLATE, (0.05*sd, -0.44, BZ + 0.08), (0.7*sd, 0.5, 0.35), 0.12, 0.04, 0.012, hint=(0, 0, 1), N=5, sub=0)     # brow crest
    blade(("MandibleL" if sd > 0 else "MandibleR"), CRY, (0.1*sd, -0.6, BZ - 0.06), (-0.6*sd, -0.6, 0), 0.07, 0.02, 0.012, hint=(0, 0, 1), N=4, sub=0)   # barb
for L, s_, hip, knee, ankle, foot in LEGS:                                       # leg spikes on every knee
    blade(L + "2", RAIN, tuple(knee + Vector((0, 0, 0.02))), (0.4*s_, 0, 1), 0.1, 0.03, 0.02, hint=(0, 1, 0), N=4, sub=0)

for k in range(6):                                                               # glowing prism edges (charge tell reads outside)
    a = k*math.pi/3
    c0 = Vector((0.132*math.cos(a), 0.05 + 0.132*math.sin(a), BZ + 0.25)); c1 = Vector((0.112*math.cos(a), 0.05 + 0.112*math.sin(a), BZ + 0.6))
    tube("Prism", GLOW, tuple(c0), tuple(c1), 0.007, 0.006, N=5)
    tube("Prism", GLOW, tuple(c1), (0, 0.05, BZ + 0.78), 0.005, 0.002, N=5)
for L, s_, hip, knee, ankle, foot in LEGS:                                       # slate armour sleeve on each thigh
    loft(L + "1", SLATE, [((knee - hip).length*0.2, .055, .055, 1.4), ((knee - hip).length*0.55, .058, .058, 1.4)], N=8, M=_frame(hip, knee - hip), cap=False)

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
