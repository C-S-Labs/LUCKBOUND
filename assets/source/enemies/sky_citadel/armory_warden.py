# LUCKBOUND - Sky Citadel MINIBOSS: Armory Warden (Armory). An empty suit of ceremonial plate animated by aether.
# P1 heavy + slow: sweeping cleave, charge. P2 (<50%): sheds plates (Break_* debris like the Winged Sentinel), becomes a
# fast skeletal frame: leap slam, thrown armour plates. Polished steel, crimson plume + tabard, gold edging, hollow
# helm with a violet-white aether flame inside. ~2.8 m. Full rig incl. fingers; Weapon_R socket.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "ArmoryWarden"; OFFSET = (58.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Frame"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("AW_Steel", (0.62, 0.64, 0.68), 1.0, 0.15), mat("AW_Gold", (0.82, 0.6, 0.22), 1.0, 0.2),
        mat("AW_Frame", (0.08, 0.08, 0.1), 0.6, 0.3), mat("AW_Crimson", (0.5, 0.05, 0.07), 0.0, 0.4),
        mat("AW_Leather", (0.25, 0.13, 0.08), 0.0, 0.45), mat("AW_Glow", (0.85, 0.75, 1.0), 0, 0.3, (0.8, 0.7, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
STEEL, GOLD, FRAME, CRIMSON, LEATHER = 0, 1, 2, 3, 4
# the inner frame (what remains in P2): dark skeletal aether-rig
J, k = make_humanoid(2.8, shoulder=0.22, hip=0.11, bulk=0.7, limb=0.8, m_body=FRAME, m_limb=FRAME, m_skin=FRAME, head=False, fingers=True)
Z = lambda z: z*k
sph("UpperTorso", GLOW, (0, 0, Z(1.33)), 0.05*k, u=12, v=8)                              # aether heart (exposed in P2)
# ---------------- P1 plate (Break_* chunks) ----------------
PIECE = "Plate"
loft("UpperTorso", STEEL, [(Z(1.12), .17*k, .12*k, 2.4), (Z(1.3), .22*k, .145*k, 2.8, 0, -.01*k), (Z(1.45), .23*k, .14*k, 3.0),
                           (Z(1.52), .12*k, .09*k)], N=24, sub=1)
loft("UpperTorso", STEEL, [(Z(1.2), .02*k, .01, 2, 0, -.14*k), (Z(1.32), .16*k, .03*k, 2, 0, -.16*k), (Z(1.44), .15*k, .02*k, 2, 0, -.145*k)], N=12, sub=1)
arc_band("UpperTorso", GOLD, (0, 0), Z(1.43), Z(1.445), (.228*k, .14*k), (.226*k, .138*k), -math.pi + 0.2, -0.2, 0.012, 20)
tube("UpperTorso", GOLD, (0, -.17*k, Z(1.2)), (0, -.17*k, Z(1.44)), 0.008*k, 0.008*k, N=6)
loft("LowerTorso", STEEL, [(Z(0.93), .15*k, .11*k, 2.4), (Z(1.02), .17*k, .12*k, 2.4), (Z(1.13), .16*k, .11*k, 2.4)], N=20, sub=1)
cloth("LowerTorso", "LowerTorso", Z(0.8), CRIMSON, -.13*k, Z(1.05), Z(0.6), .2*k, .24*k, bow=0.03, teeth=4, depth=0.06*k, rows=6, cols=6)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    sph(f"{side}UpperArm", STEEL, (j["sh"][0]*1.1, 0, j["sh"][2] + .02*k), 0.12*k, scale=(1.15, 1.1, 0.8), cut_below=-0.3, u=18, v=10)
    for bn, a, b, r in ((f"{side}UpperArm", "sh", "el", .06), (f"{side}LowerArm", "el", "wr", .058), (f"{side}UpperLeg", "hp", "kn", .085), (f"{side}LowerLeg", "kn", "an", .07)):
        A, B_ = Vector(j[a]), Vector(j[b]); L = (B_ - A).length
        loft(bn, STEEL, [(L*0.1, r*k*0.9, r*k*0.95, 3), (L*0.16, r*k, r*k*1.05, 3), (L*0.84, r*k*0.92, r*k*0.97, 3), (L*0.9, r*k*0.82, r*k*0.86, 3)], N=16, M=_frame(A, B_ - A))
        loft(bn, GOLD, [(L*0.16 - 0.006, r*k*1.01, r*k*1.06, 3), (L*0.16 + 0.006, r*k*1.01, r*k*1.06, 3)], N=16, M=_frame(A, B_ - A))
    sph(f"{side}LowerLeg", GOLD, (j["kn"][0], -0.05*k, j["kn"][2]), 0.05*k, scale=(1, 0.7, 1.1), u=12, v=8)
    sph(f"{side}LowerArm", GOLD, (j["el"][0], 0.05*k, j["el"][2]), 0.045*k, scale=(1, 0.7, 1), u=12, v=8)
    loft(f"{side}Foot", STEEL, [(0, .05*k, .035*k), (0.2*k, .055*k, .04*k), (0.28*k, .02*k, .02*k)], N=12,
         M=TR((j["an"][0], j["an"][1] + 0.05*k, 0.045*k), (math.pi/2, 0, 0)), sub=1)
    sph(f"{side}Hand", STEEL, (Vector(j["wr"]) + Vector((0, 0, -0.03*k))).to_tuple(), 0.05*k, scale=(0.8, 1.1, 1.1), u=12, v=8)
# helm: bascinet with visor slits, gold crest ridge, crimson plume; the aether flame burns inside (glow, PIECE Frame)
loft("Head", STEEL, [(Z(1.52), .095*k, .1*k, 2.6), (Z(1.62), .1*k, .11*k, 2.6), (Z(1.74), .095*k, .105*k, 2.4),
                     (Z(1.83), .06*k, .07*k, 2.2), (Z(1.88), .015*k, .02*k)], N=24, sub=1)
loft("Head", STEEL, [(0, .085*k, .07*k, 1.5), (0.06*k, .06*k, .05*k, 1.5), (0.1*k, .01*k, .01*k, 1.5)], N=12,
     M=_frame(Vector((0, -0.09*k, Z(1.62))), Vector((0, -1, -0.15)), hint=(0, 0, 1)))                        # pointed visor
for i in range(3):
    box("Head", FRAME, (0, -.13*k, Z(1.65 + i*0.025)), (0.12*k, 0.03, 0.008*k), bev=0.002, segs=1)
tube("Head", GOLD, (0, -.11*k, Z(1.8)), (0, .06*k, Z(1.86)), 0.012*k, 0.01*k, N=6)
for i in range(6):
    blade("Head", CRIMSON, (0, 0.02*k + i*0.02*k, Z(1.86)), (0, 0.6 + i*0.12, 0.7 - i*0.15), 0.28*k, 0.035*k, 0.01, hint=(1, 0, 0), N=6, sub=0)
# --- miniboss detail pass ---
PIECE = "PlateTrim"
# heraldic chest emblem: crimson shield with a gold spire, filigree scrolls, central ridge
c0 = Vector((0, -.172*k, Z(1.33)))
loft("UpperTorso", CRIMSON, [(0, .07*k, .08*k, 2), (0.012*k, .07*k, .08*k, 2)], N=6, M=TR(tuple(c0), (math.pi/2, 0, 0)))
loft("UpperTorso", GOLD, [(0, .075*k, .085*k, 2), (0.008*k, .075*k, .085*k, 2), (0.008*k, .068*k, .078*k, 2), (0, .068*k, .078*k, 2)], N=6, M=TR(tuple(c0), (math.pi/2, 0, 0)))
loft("UpperTorso", GOLD, [(Z(1.27), .02*k, .004*k, 2, 0, -.186*k), (Z(1.38), .005*k, .004*k, 2, 0, -.186*k)], N=6)
for s_ in (1, -1):
    for c_ in range(3):
        cc = Vector((0.13*s_*k, -0.15*k, Z(1.42 - c_*0.08)))
        sp_ = [cc + Vector((0.02*k*(1 - u)*math.cos(u*9)*s_, -0.004*k, 0.02*k*(1 - u)*math.sin(u*9))) for u in [i/10 for i in range(11)]]
        for a_, b_ in zip(sp_, sp_[1:]):
            tube("UpperTorso", GOLD, tuple(a_), tuple(b_), 0.004*k, 0.004*k, N=4)
loft("UpperTorso", GOLD, [(Z(1.18), .012*k, .01*k, 2, 0, .15*k), (Z(1.47), .012*k, .01*k, 2, 0, .145*k)], N=6)
cloth("UpperTorso", "UpperTorso", Z(0.9), CRIMSON, .16*k, Z(1.5), Z(0.55), .38*k, .5*k, bow=0.05, teeth=6, depth=0.05*k, rows=10, cols=10, face=1)
loft("LowerTorso", FRAME, [(Z(1.05), .165*k, .12*k), (Z(0.78), .19*k, .15*k)], N=28, cap=False)
for r_ in range(5):
    arc_band("LowerTorso", STEEL, (0, 0), Z(1.02 - r_*0.05), Z(1.0 - r_*0.05), (.168*k + r_*0.005*k, .123*k + r_*0.005*k), (.17*k + r_*0.005*k, .125*k + r_*0.005*k), 0, 2*math.pi, 0.004*k, 28)
arc_band("LowerTorso", GOLD, (0, 0), Z(1.1), Z(1.06), (.172*k, .125*k), (.176*k, .128*k), 0, 2*math.pi, 0.01*k, 32)
box("LowerTorso", GOLD, (0, -.13*k, Z(1.08)), (0.06*k, 0.015*k, 0.05*k), bev=0.004*k, segs=1)
for side, s_ in (("Left", 1), ("Right", -1)):
    j = J[side]; out = 0.0 if s_ > 0 else math.pi
    arc_band(f"{side}UpperArm", STEEL, (j["sh"][0], 0), j["sh"][2] - 0.02*k, j["sh"][2] - 0.1*k, (.1*k, .095*k), (.125*k, .12*k), out - 1.6, out + 1.6, 0.01*k, 24)
    arc_band(f"{side}UpperArm", GOLD, (j["sh"][0], 0), j["sh"][2] - 0.095*k, j["sh"][2] - 0.103*k, (.124*k, .119*k), (.127*k, .122*k), out - 1.6, out + 1.6, 0.006*k, 24)
    blade(f"{side}UpperArm", STEEL, (j["sh"][0]*1.12, 0, j["sh"][2] + 0.1*k), (0.5*s_, 0, 1), 0.12*k, 0.03*k, 0.02*k, hint=(0, 1, 0), N=6)
    A_, B_ = Vector(j["el"]), Vector(j["wr"])
    loft(f"{side}LowerArm", STEEL, [(0.7*(B_ - A_).length, .06*k, .062*k), ((B_ - A_).length*1.02, .075*k, .078*k)], N=18, M=_frame(A_, B_ - A_), cap=False)
    arc_band(f"{side}LowerLeg", GOLD, (j["kn"][0], 0), j["an"][2] + 0.1*k, j["an"][2] + 0.09*k, (.076*k, .08*k), (.078*k, .082*k), 0, 2*math.pi, 0.006*k, 24)
arc_band("Head", GOLD, (0, 0), Z(1.715), Z(1.73), (.1*k, .112*k), (.099*k, .11*k), -math.pi + 0.3, -0.3, 0.008*k, 20)
for i in range(8):
    sph("Head", FRAME, ((i % 4 - 1.5)*0.018*k, -.132*k, Z(1.585 - (i // 4)*0.02)), 0.006*k, u=6, v=4)
PIECE = "Frame"
sph("Head", GLOW, (0, -.02*k, Z(1.66)), 0.05*k, scale=(1, 1, 1.4), u=12, v=8)
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.02, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.25, 0)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
