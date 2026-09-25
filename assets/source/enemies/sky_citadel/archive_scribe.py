# LUCKBOUND - Sky Citadel BASIC enemy: Archive Scribe (long range / support; Archive + Reliquary).
# Stays ROOTED while channelling (punish window): homing glyph pages, wards an ally, blinks away.
# Ivory robes with ink-black trim, a tall scholar's hood hiding a void face with two cyan eyes, open floating tome,
# pages fan from a paper halo on the back (PageA-D bones). ~1.95 m, hovers a hand's width off the floor.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "ArchiveScribe"; OFFSET = (35.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
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
# v2 character pass (2026-09-24). Nothing floats: the tome is HELD open in the left hand and chained to the belt;
# the pages form a PAPER HALO - a fan of pages on a brass back-ring (PageA-D bones still let them riffle / fan out
# as the channel tell). Gold glyph lines on the robe, scroll cases + ink pots on the belt, quill tucked in the hood.
jl = J["Left"]; hl = Vector(jl["hd"]); wl = Vector(jl["wr"])
add_bone("Tome", tuple(hl + Vector((0, -0.06*k, 0.02*k))), tuple(hl + Vector((0, -0.06*k, 0.14*k))), "LeftHand")
tc = hl + Vector((-0.02*k, -0.08*k, 0.02*k))
for s_ in (1, -1):
    box("Tome", LEATHER, tuple(tc + Vector((0.07*s_*k, 0, 0))), (0.14*k, 0.11*k, 0.018*k), rot=(0.9, 0.22*s_, 0), bev=0.005, segs=1)
    box("Tome", PAPER, tuple(tc + Vector((0.066*s_*k, -0.004*k, 0.012*k))), (0.125*k, 0.095*k, 0.014*k), rot=(0.9, 0.22*s_, 0), bev=0.003, segs=1)
    tube("Tome", GLOW, tuple(tc + Vector((0.03*s_*k, -0.03*k, 0.03*k))), tuple(tc + Vector((0.1*s_*k, -0.03*k, 0.03*k))), 0.004*k, 0.004*k, N=4)
ch = [tc + (Vector((0.08*k, 0.02*k, Z(1.02))) - tc)*t + Vector((0, 0, -0.08*k*math.sin(math.pi*t))) for t in [i/8 for i in range(9)]]
for i, (a_, b_) in enumerate(zip(ch, ch[1:])):                              # chain from tome to belt
    loft("Tome" if i < 4 else "LowerTorso", GOLD, [(-0.008*k, .012*k, .007*k), (0.008*k, .012*k, .007*k)], N=8, M=_frame(a_.lerp(b_, 0.5), b_ - a_), cap=False)
ring_c = Vector((0, 0.17*k, Z(1.42)))                                    # paper halo on a brass back-ring
loft("UpperTorso", GOLD, [(-0.01*k, .2*k, .2*k), (0.01*k, .2*k, .2*k)], N=28, M=TR(tuple(ring_c), (math.pi/2, 0, 0)), cap=False)
box("UpperTorso", GOLD, tuple(Vector((0, 0.13*k, Z(1.42)))), (0.04*k, 0.08*k, 0.04*k), bev=0.006*k, segs=1)   # mount to the back
for i, pn in enumerate("ABCD"):
    a = math.pi*(0.15 + 0.7*i/3)
    c = ring_c + Vector((0.2*math.cos(a)*k, 0, 0.2*math.sin(a)*k))
    add_bone("Page" + pn, tuple(c), tuple(c + Vector((0.12*math.cos(a)*k, 0, 0.12*math.sin(a)*k))), "UpperTorso")
    for j_ in range(2):
        aa = a + (j_ - 0.5)*0.22
        cc = ring_c + Vector((0.27*math.cos(aa)*k, 0.01*j_, 0.27*math.sin(aa)*k))
        box("Page" + pn, PAPER, tuple(cc), (0.07*k, 0.006, 0.14*k), rot=(0, -aa + math.pi/2, 0), bev=0.002, segs=1)
        box("Page" + pn, GLOW, tuple(cc + Vector((0, -0.005, 0))), (0.03*k, 0.006, 0.07*k), rot=(0, -aa + math.pi/2, 0), bev=0.001, segs=1)
T = body_bvh()
for s_ in (1, -1):                                                        # ink stole, flush on the robe
    flow_line_in("LowerTorso", INK, [(0.07*s_*k, -.13*k, Z(1.35)), (0.075*s_*k, -.16*k, Z(1.1)), (0.08*s_*k, -.19*k, Z(0.85)), (0.085*s_*k, -.23*k, Z(0.6))], r=0.016*k, T=T, centre=(0, 0, Z(0.95)))
for s_ in (1, -1):                                                        # gold glyph lines down the robe front
    flow_line_in("LowerTorso", GOLD, [(0.05*s_*k, -.16*k, Z(1.0)), (0.09*s_*k, -.2*k, Z(0.7)), (0.07*s_*k, -.25*k, Z(0.45)), (0.12*s_*k, -.28*k, Z(0.26))], r=0.006*k, T=T, centre=(0, 0, Z(0.7)))
    for z in (0.85, 0.6, 0.38):
        q = on_surface_in(T, (0.0, -.3*k, Z(z)), (0, 0, Z(z)), 0.0)
        gem("LowerTorso", GLOW, tuple(q), 0.016*k, 0.008*k, rot=(math.pi/2, 0, 0), sides=4)
arc_band("LowerTorso", LEATHER, (0, 0), Z(1.05), Z(1.0), (.162*k, .122*k), (.17*k, .128*k), 0, 2*math.pi, 0.014*k, 24)   # belt
for s_, kind in ((1, "scroll"), (-1, "ink")):
    c = Vector((0.15*s_*k, -0.04*k, Z(0.93)))
    if kind == "scroll":
        tube("LowerTorso", LEATHER, tuple(c + Vector((0, 0, 0.07*k))), tuple(c - Vector((0, 0, 0.12*k))), 0.028*k, 0.028*k, N=10)
        loft("LowerTorso", GOLD, [(-0.01*k, .031*k, .031*k), (0.01*k, .031*k, .031*k)], N=10, M=TR(tuple(c - Vector((0, 0, 0.1*k)))), cap=False)
    else:
        sph("LowerTorso", INK, tuple(c), 0.035*k, scale=(1, 1, 1.1), u=12, v=8)
        tube("LowerTorso", GOLD, tuple(c + Vector((0, 0, 0.03*k))), tuple(c + Vector((0, 0, 0.06*k))), 0.014*k, 0.012*k, N=8)
blade("Head", PAPER, (0.07*k, 0.07*k, Z(1.72)), (0.35, 0.6, 1), 0.2*k, 0.035*k, 0.006*k, hint=(1, 0, 0), N=6, sub=0)   # quill in the hood
for side in ("Left", "Right"):                                              # gold sleeve cuffs + ink gloves
    j = J[side]
    loft(f"{side}LowerArm", GOLD, [(0.29*k, .122*k, .112*k), (0.31*k, .122*k, .112*k)], N=16, M=_frame(Vector(j["el"]), Vector(j["wr"]) - Vector(j["el"])), cap=False)
PIECES_OFFSET_Z = 0.08    # hovers above the floor
rig, PARTS = assemble(NAME, (OFFSET[0], OFFSET[1], OFFSET[2] + PIECES_OFFSET_Z))
