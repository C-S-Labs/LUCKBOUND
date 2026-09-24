# LUCKBOUND - Sky Citadel BASIC enemy: Archive Scribe (long range / support; Archive + Reliquary).
# Stays ROOTED while channelling (punish window): homing glyph pages, wards an ally, blinks away.
# Ivory robes with ink-black trim, a tall scholar's hood hiding a void face with two cyan eyes, open floating tome,
# four orbiting pages on their own bones (PageA-D) so they can circle. ~1.95 m, hovers a hand's width off the floor.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "ArchiveScribe"; OFFSET = (35.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("AS_Ivory", (0.86, 0.82, 0.72), 0.0, 0.4), mat("AS_Ink", (0.04, 0.04, 0.06), 0.2, 0.3),
        mat("AS_Gold", (0.8, 0.6, 0.25), 1.0, 0.2), mat("AS_Paper", (0.93, 0.9, 0.8), 0.0, 0.5),
        mat("AS_Leather", (0.35, 0.16, 0.12), 0.0, 0.4), mat("AS_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
ROBE, INK, GOLD, PAPER, LEATHER = 0, 1, 2, 3, 4
J, k = make_humanoid(1.95, shoulder=0.19, hip=0.1, bulk=0.9, limb=0.95, m_body=ROBE, m_limb=INK, m_skin=INK, head=False)
Z = lambda z: z*k
# long robe (floor length bell) over the legs, ink hem + trim
loft("LowerTorso", ROBE, [(Z(1.12), .15*k, .11*k), (Z(0.9), .2*k, .16*k), (Z(0.5), .26*k, .22*k), (Z(0.14), .31*k, .27*k)], N=24, sub=1)
arc_band("LowerTorso", INK, (0, 0), Z(0.24), Z(0.14), (.292*k, .252*k), (.312*k, .272*k), 0, 2*math.pi, 0.02, 32)
loft("UpperTorso", ROBE, [(Z(1.12), .16*k, .12*k), (Z(1.36), .2*k, .13*k), (Z(1.5), .16*k, .11*k)], N=20, sub=1)
# wide sleeves
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    loft(f"{side}LowerArm", ROBE, [(0, .06*k, .06*k), (0.2*k, .09*k, .09*k), (0.3*k, .12*k, .11*k)], N=16,
         M=_frame(Vector(j["el"]), Vector(j["wr"]) - Vector(j["el"])), cap=False)
    arc_band(f"{side}LowerArm", INK, (0, 0), 0, 0, (0, 0), (0, 0), 0, 0.01, 0.0, 1) if False else None
# rounded draped scholar's hood (deep cowl) + void face + cyan eyes + gold circlet; dark mantle over the shoulders
loft("Head", ROBE, [(Z(1.49), .15*k, .15*k, 2, 0, .015), (Z(1.62), .13*k, .14*k, 2, 0, .01), (Z(1.74), .115*k, .13*k, 2, 0, .02),
                    (Z(1.81), .08*k, .1*k, 2, 0, .03), (Z(1.84), .03*k, .05*k, 2, 0, .03)], N=24, sub=1,
     keep=lambda c: not (c.y < -0.05 and Z(1.55) < c.z < Z(1.76)), fill=True)
sph("Head", INK, (0, -0.01, Z(1.65)), 0.1*k, scale=(0.9, 0.9, 1.05), u=14, v=10)
for s in (1, -1):
    sph("Head", GLOW, (0.035*s*k, -0.09*k, Z(1.67)), 0.013*k, u=8, v=6)
arc_band("Head", GOLD, (0, 0.012), Z(1.755), Z(1.768), (.118*k, .133*k), (.116*k, .131*k), -math.pi + 0.35, -0.35, 0.01, 14)
loft("UpperTorso", INK, [(Z(1.36), .25*k, .16*k, 2.4), (Z(1.46), .22*k, .15*k, 2.4), (Z(1.52), .14*k, .12*k, 2.4)], N=24, sub=1)   # mantle
arc_band("UpperTorso", GOLD, (0, 0), Z(1.37), Z(1.355), (.25*k, .16*k), (.252*k, .162*k), 0, 2*math.pi, 0.01, 28)
# floating open tome in front of the chest + quill, orbiting pages
add_bone("Tome", (0, -0.28*k, Z(1.2)), (0, -0.28*k, Z(1.32)), "UpperTorso")
for s in (1, -1):
    box("Tome", LEATHER, (0.1*s*k, -0.3*k, Z(1.24)), (0.19*k, 0.14*k, 0.02*k), rot=(0.5, 0.25*s, 0), bev=0.006, segs=1)
    box("Tome", PAPER, (0.095*s*k, -0.3*k, Z(1.255)), (0.17*k, 0.12*k, 0.015*k), rot=(0.5, 0.25*s, 0), bev=0.003, segs=1)
gem("Tome", GLOW, (0, -0.31*k, Z(1.3)), 0.03*k, 0.04*k, sides=4)
for i, pn in enumerate("ABCD"):
    a = i*math.pi/2 + 0.4
    c = Vector((0.42*math.cos(a)*k, 0.42*math.sin(a)*k, Z(1.35 + 0.08*math.sin(i*1.7))))
    add_bone("Page" + pn, tuple(c - Vector((0, 0, 0.06))), tuple(c + Vector((0, 0, 0.06))), "UpperTorso")
    box("Page" + pn, PAPER, tuple(c), (0.12*k, 0.008, 0.16*k), rot=(0.15, 0.2, a + math.pi/2), bev=0.002, segs=1)
    box("Page" + pn, GLOW, tuple(c + Vector((0, 0, 0.02))), (0.07*k, 0.012, 0.012), rot=(0.15, 0.2, a + math.pi/2), bev=0.002, segs=1)
# ink-black stole with gold ends
for s in (1, -1):
    box("UpperTorso", INK, (0.075*s*k, -0.2*k, Z(0.98)), (0.07*k, 0.012, 0.62*k), rot=(0.12, 0, 0), bev=0.004, segs=1)
    box("UpperTorso", GOLD, (0.075*s*k, -0.235*k, Z(0.67)), (0.075*k, 0.016, 0.04*k), rot=(0.12, 0, 0), bev=0.004, segs=1)
PIECES_OFFSET_Z = 0.08    # hovers above the floor
rig, PARTS = assemble(NAME, (OFFSET[0], OFFSET[1], OFFSET[2] + PIECES_OFFSET_Z))
