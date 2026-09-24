# LUCKBOUND - Sky Citadel BASIC enemy: Cloud Skirmisher (long range, javelin thrower). Light infantry of the citadel:
# throws a javelin (Weapon_R socket) then has a clear re-draw pause (punish window); backsteps when approached.
# Slate-blue cloth, brass pauldron + bracers, white sash, hooded half-helm with a cyan eye slit. ~1.9 m.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "CloudSkirmisher"; OFFSET = (30.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("CS_Cloth", (0.2, 0.3, 0.44), 0.0, 0.45), mat("CS_Brass", (0.75, 0.56, 0.24), 1.0, 0.2),
        mat("CS_Under", (0.08, 0.09, 0.12), 0.3, 0.4), mat("CS_White", (0.9, 0.9, 0.88), 0.0, 0.4),
        mat("CS_Leather", (0.3, 0.2, 0.13), 0.0, 0.45), mat("CS_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BLUE, BRASS, UNDER, WHITE, LEATHER = 0, 1, 2, 3, 4
J, k = make_humanoid(1.9, shoulder=0.2, hip=0.1, bulk=0.95, limb=1.0, m_body=BLUE, m_limb=UNDER, m_skin=UNDER, head=False)
Z = lambda z: z*k
# hooded half-helm: brass skullcap, slate hood, cyan slit, cloth face wrap
sph("Head", BRASS, (0, 0, Z(1.67)), 0.1*k, scale=(0.95, 1.05, 1.0), cut_below=0.0, u=18, v=10)
loft("Head", UNDER, [(Z(1.52), .06*k, .06*k), (Z(1.66), .092*k, .1*k), (Z(1.70), .09*k, .1*k)], N=16)
box("Head", GLOW, (0, -.098*k, Z(1.685)), (0.12*k, 0.02, 0.016*k), bev=0.004, segs=1)
loft("Head", WHITE, [(Z(1.55), .095*k, .105*k), (Z(1.65), .1*k, .108*k)], N=16, M=TR((0, -0.004, 0)))           # face wrap
loft("Head", BLUE, [(Z(1.56), .13*k, .12*k, 2, 0, .02), (Z(1.70), .125*k, .125*k, 2, 0, .03), (Z(1.80), .06*k, .08*k, 2, 0, .05)],
     N=18, M=TR((0, 0.015, 0)), keep=lambda c: c.y > -0.05, fill=True)                                        # hood (open front)
blade("Head", BRASS, (0, 0.0, Z(1.77)), (0, 1, 0.5), 0.2*k, 0.03*k, 0.01, hint=(1, 0, 0), N=6, sub=0)
# brass left pauldron (asymmetric light armour), bracers, white sash, leather belt + javelin quiver on back
j = J["Left"]
sph("LeftUpperArm", BRASS, (j["sh"][0]*1.05, 0, j["sh"][2] + .02*k), 0.09*k, scale=(1.15, 1.1, 0.8), cut_below=-0.2, u=16, v=10)
for side in ("Left", "Right"):
    j = J[side]
    loft(f"{side}LowerArm", BRASS, [(0, .052*k, .054*k, 2.4), (0.2*k, .046*k, .048*k, 2.4)], N=12,
         M=_frame(Vector(j["el"]).lerp(Vector(j["wr"]), 0.3), Vector(j["wr"]) - Vector(j["el"])))
    loft(f"{side}LowerLeg", LEATHER, [(0, .06*k, .064*k, 2.4), (0.3*k, .05*k, .054*k, 2.4)], N=12,
         M=_frame(Vector(j["kn"]).lerp(Vector(j["an"]), 0.15), Vector(j["an"]) - Vector(j["kn"])))
tube("UpperTorso", WHITE, (0.16*k, -0.09*k, Z(1.45)), (-0.15*k, -0.11*k, Z(1.08)), 0.03*k, 0.03*k, N=8)           # sash
arc_band("LowerTorso", LEATHER, (0, 0), Z(1.12), Z(1.06), (.15*k, .11*k), (.155*k, .115*k), 0, 2*math.pi, 0.015, 24)
cloth("LowerTorso", "LowerTorso", Z(0.8), BLUE, -.11*k, Z(1.07), Z(0.66), .22*k, .26*k, bow=0.03, teeth=3, depth=0.05*k, rows=6, cols=6)
cloth("LowerTorso", "LowerTorso", Z(0.8), BLUE, .1*k, Z(1.07), Z(0.62), .24*k, .28*k, bow=0.03, teeth=3, depth=0.05*k, rows=6, cols=6, face=1)
loft("UpperTorso", LEATHER, [(0, .05*k, .05*k), (0.55*k, .045*k, .045*k)], N=10, M=_frame(Vector((0.08*k, 0.15*k, Z(1.05))), Vector((-0.35, 0.1, 1))))  # quiver
for i in range(3):
    tube("UpperTorso", BRASS, tuple(Vector((0.08*k, 0.15*k, Z(1.05))) + Vector((-0.35, 0.1, 1)).normalized()*0.55*k + Vector(((i - 1)*0.025, 0, 0))),
         tuple(Vector((0.08*k, 0.15*k, Z(1.05))) + Vector((-0.35, 0.1, 1)).normalized()*0.72*k + Vector(((i - 1)*0.03, 0, 0))), 0.008, 0.008, N=5)
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.02, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.2, 0)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
