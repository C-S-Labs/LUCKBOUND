# LUCKBOUND - Sky Citadel BASIC enemy: Prism Crawler (Prism Arena). Six-legged crystal crawler.
# Long range but punishable: raises its crystal tail and charges a refracting beam from the prism stinger (long windup, the prism
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
         ]
TAILP = [Vector((0, 0.34, BZ + 0.02)), Vector((0, 0.5, BZ + 0.2)), Vector((0, 0.52, BZ + 0.45)), Vector((0, 0.38, BZ + 0.64)),
         Vector((0, 0.16, BZ + 0.72))]
for i in range(4):
    BONES.append((f"Tail{i + 1}", tuple(TAILP[i]), tuple(TAILP[i + 1]), "Body" if i == 0 else f"Tail{i}"))
BONES += [("Prism", tuple(TAILP[4]), tuple(TAILP[4] + Vector((0, -0.18, -0.06))), "Tail4"),
          ("VFX_Beam", tuple(TAILP[4] + Vector((0, -0.2, -0.06))), tuple(TAILP[4] + Vector((0, -0.5, -0.15))), "Prism")]
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

# ---- six legs: slate joints, crystal segments, sharp crystal feet ----
for L, s, hip, knee, ankle, foot in LEGS:
    sph(L + "1", SLATE, tuple(hip), 0.05, u=8, v=6)
    loft(L + "1", CRY, [(0, .042, .042, 1.4), ((knee - hip).length*0.5, .05, .05, 1.4), ((knee - hip).length, .036, .036, 1.4)], N=8, M=_frame(hip, knee - hip), sub=1)
    sph(L + "2", SLATE, tuple(knee), 0.04, u=8, v=6)
    loft(L + "2", CRY, [(0, .034, .034, 1.4), ((ankle - knee).length*0.4, .04, .04, 1.4), ((ankle - knee).length, .026, .026, 1.4)], N=8, M=_frame(knee, ankle - knee), sub=1)
    sph(L + "3", SLATE, tuple(ankle), 0.03, u=8, v=6)
    loft(L + "3", RAIN, [(0, .025, .025, 1.5), ((foot - ankle).length, .004, .004, 1.5)], N=5, M=_frame(ankle, foot - ankle))

# ---- v3 (2026-09-24): CRYSTAL SCORPION. Everything attached, nothing floats.
#  * BEAM: the segmented crystal tail curls over the back and ends in a prism stinger that fires the beam
#    (tail rises + the stinger's glowing facets brighten = the charge tell).
#  * OVERHEAT: heat vents along the underside of every tail segment glow, then vent -> the punish window.
#  * BURROW: overlapping carapace plates down the back close into a shell.
for i in range(4):                                                               # tail segments (faceted crystal) + slate collars + vents
    a_, b_ = TAILP[i], TAILP[i + 1]; d_ = b_ - a_; n_ = d_.length; r0 = 0.085 - 0.012*i
    M_ = _frame(a_, d_, hint=(1, 0, 0))
    loft(f"Tail{i + 1}", CRY, [(0.0, r0*0.8, r0*0.7, 1.5), (n_*0.35, r0, r0*0.85, 1.5), (n_*0.85, r0*0.85, r0*0.72, 1.5), (n_*1.05, r0*0.7, r0*0.6, 1.5)], N=10, M=M_, sub=1)
    loft(f"Tail{i + 1}", SLATE, [(n_*0.9, r0*0.9, r0*0.78, 1.5), (n_*1.02, r0*0.88, r0*0.76, 1.5)], N=10, M=M_)
    loft(f"Tail{i + 1}", GLOW, [(n_*0.84, r0*0.88, r0*0.76, 1.5), (n_*0.9, r0*0.88, r0*0.76, 1.5)], N=10, M=M_, cap=False)   # heat seam (vents)
    blade(f"Tail{i + 1}", RAIN, tuple(M_ @ Vector((0, r0*0.55, n_*0.5))), tuple(M_.to_3x3() @ Vector((0, 1, 0.4))), 0.09 - 0.012*i, 0.035, 0.02, hint=tuple(M_.to_3x3() @ Vector((1, 0, 0))), N=4, sub=0)
st = TAILP[4]; sd_ = Vector((0, -0.18, -0.06))                                   # the prism stinger: hex crystal, glowing lens face
Ms = _frame(st, sd_, hint=(1, 0, 0))
loft("Prism", SLATE, [(-0.02, .07, .07, 2), (0.02, .065, .065, 2)], N=6, M=Ms)
loft("Prism", CRY, [(0.0, .055, .055, 2), (0.08, .065, .065, 2), (0.16, .05, .05, 2), (0.2, .03, .03, 2)], N=6, M=Ms)
loft("Prism", GLOW, [(0.2, .03, .03, 2), (0.205, .03, .03, 2)], N=6, M=Ms)
for k in range(6):                                                               # glowing facet lines on the stinger
    a = k*math.pi/3
    tube("Prism", GLOW, tuple(Ms @ Vector((0.064*math.cos(a), 0.064*math.sin(a), 0.07))), tuple(Ms @ Vector((0.034*math.cos(a), 0.034*math.sin(a), 0.195))), 0.004, 0.003, N=4)
for k in range(5):                                                               # overlapping carapace plates (burrow shell)
    y = -0.2 + k*0.11
    loft("Body", SLATE if k % 2 == 0 else CRY, [(-0.045, .19 - 0.012*abs(k - 2), .125, 1.6), (0.045, .2 - 0.012*abs(k - 2), .13, 1.6)], N=12,
         M=TR((0, y, BZ + 0.0), (math.pi/2, 0, 0)), keep=lambda c: c.z > BZ + 0.04, fill=False, cap=False)
loft("Head", CRY, [(0, .035, .03, 1.4), (0.14, .02, .018, 1.4), (0.2, .003, .003, 1.4)], N=5, M=_frame(Vector((0, -0.42, BZ + 0.06)), Vector((0, -0.6, 1))))   # horn
for sd in (1, -1):
    blade("Head", SLATE, (0.05*sd, -0.44, BZ + 0.07), (0.7*sd, 0.5, 0.3), 0.12, 0.04, 0.012, hint=(0, 0, 1), N=5, sub=0)      # brow crest
    md = Vector((0.25*sd, -1.0, -0.2)).normalized(); mp = Vector((0.07*sd, -0.5, BZ - 0.05)) + md*0.11      # barb ON the mandible
    blade(("MandibleL" if sd > 0 else "MandibleR"), CRY, tuple(mp), (-0.7*sd, -0.5, 0), 0.06, 0.018, 0.012, hint=(0, 0, 1), N=4, sub=0)
for L, s_, hip, knee, ankle, foot in LEGS:
    blade(L + "2", RAIN, tuple(knee + Vector((0, 0, 0.02))), (0.4*s_, 0, 1), 0.1, 0.03, 0.02, hint=(0, 1, 0), N=4, sub=0)
    loft(L + "1", SLATE, [((knee - hip).length*0.2, .055, .055, 1.4), ((knee - hip).length*0.55, .058, .058, 1.4)], N=8, M=_frame(hip, knee - hip), cap=False)
exec(open(FW + r"\character_kit.py").read())                                    # eye cluster seated ON the head surface
T = body_bvh()
for sd in (1, -1):
    for k in range(3):
        q = on_surface(T, (0.05*sd + 0.02*k*sd, -0.52 + 0.03*k, BZ + 0.04 + 0.015*k), (0, -0.42, BZ - 0.01), lift=-0.004)
        sph("Head", GLOW, tuple(q), 0.014, u=8, v=6)
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
