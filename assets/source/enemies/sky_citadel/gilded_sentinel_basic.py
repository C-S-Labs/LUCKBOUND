# LUCKBOUND - Sky Citadel BASIC enemy: Gilded Sentinel (close range). The citadel's rank-and-file construct guard,
# carved from the same pale stone as the architecture, gold-trimmed, cyan aether visor. ~2.1 m (1.5x a player).
# Attacks: 2-hit combo, shield bash, guard stance (block, then riposte window). Weapon_R / Shield_L are sockets.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "GildedSentinel"; OFFSET = (20.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("GSB_Stone", (0.74, 0.72, 0.67), 0.0, 0.25), mat("GSB_Gold", (0.82, 0.6, 0.22), 1.0, 0.2),
        mat("GSB_Slate", (0.10, 0.11, 0.15), 0.4, 0.3), mat("GSB_Cloth", (0.16, 0.27, 0.45), 0.0, 0.45),
        mat("GSB_Spare", (0.5, 0.5, 0.5), 0, 0.3), mat("GSB_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
STONE, GOLD, SLATE, BLUE = 0, 1, 2, 3
J, k = make_humanoid(2.1, shoulder=0.23, hip=0.11, bulk=1.15, limb=1.25, m_body=STONE, m_limb=SLATE, m_skin=SLATE, head=False)
Z = lambda z: z*k
# breastplate + gold rims, aether gem
loft("UpperTorso", STONE, [(Z(1.18), .17*k, .06*k, 2, 0, -.10*k), (Z(1.32), .21*k, .07*k, 2, 0, -.115*k), (Z(1.44), .20*k, .06*k, 2, 0, -.11*k)], N=16, sub=1)
arc_band("UpperTorso", GOLD, (0, 0), Z(1.445), Z(1.46), (.215*k, .135*k), (.21*k, .13*k), 0, 2*math.pi, 0.012, 24)
gem("UpperTorso", GLOW, (0, -.19*k, Z(1.33)), 0.035*k, 0.03*k, rot=(math.pi/2, 0, 0), sides=6)
loft("UpperTorso", GOLD, [(0, .05*k, .05*k), (0.012, .05*k, .05*k), (0.012, .04*k, .04*k), (0, .04*k, .04*k)], N=16, M=TR((0, -.182*k, Z(1.33)), (math.pi/2, 0, 0)))
# helm: tall crested stone helm, cyan T-visor
loft("Head", STONE, [(Z(1.50), .085*k, .095*k, 2.4), (Z(1.60), .10*k, .11*k, 2.4), (Z(1.74), .095*k, .105*k, 2.4), (Z(1.82), .06*k, .07*k, 2.2), (Z(1.86), .02*k, .03*k)], N=20, sub=1)
loft("Head", STONE, [(Z(1.56), .07*k, .02*k, 2, 0, -.085*k), (Z(1.66), .085*k, .025*k, 2, 0, -.095*k), (Z(1.72), .08*k, .02*k, 2, 0, -.09*k)], N=12, sub=1)
arc_band("Head", GOLD, (0, 0), Z(1.715), Z(1.73), (.1*k, .112*k), (.099*k, .11*k), -math.pi + 0.5, -0.5, 0.012, 14)
box("Head", GLOW, (0, -.118*k, Z(1.68)), (0.11*k, 0.02, 0.018*k), bev=0.004, segs=1)
box("Head", GLOW, (0, -.118*k, Z(1.63)), (0.018*k, 0.02, 0.08*k), bev=0.004, segs=1)
blade("Head", GOLD, (0, 0.02*k, Z(1.83)), (0, 1, 0.4), 0.28*k, 0.04*k, 0.012, hint=(1, 0, 0), N=8)
for s in (1, -1):
    blade("Head", GOLD, (0.1*s*k, 0.0, Z(1.70)), (0.4*s, 0.9, 0.5), 0.14*k, 0.03*k, 0.01, hint=(0, 0, 1), N=6)
# pauldrons, bracers, greaves, tassets, tabard
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    sph(f"{side}UpperArm", STONE, (j["sh"][0]*1.08, 0, j["sh"][2] + .03*k), 0.11*k, scale=(1.1, 1.05, 0.75), cut_below=-0.25, u=18, v=10)
    loft(f"{side}LowerArm", STONE, [(0, .07*k, .072*k, 2.4), (0.04*k, .08*k, .082*k, 2.4), (0.28*k, .068*k, .07*k, 2.4), (0.30*k, .06*k, .062*k, 2.4)], N=14, M=_frame(Vector(j["el"]).lerp(Vector(j["wr"]), 0.12), Vector(j["wr"]) - Vector(j["el"])))
    loft(f"{side}LowerLeg", STONE, [(0, .08*k, .085*k, 2.4), (0.04*k, .092*k, .1*k, 2.4), (0.38*k, .07*k, .075*k, 2.4), (0.40*k, .06*k, .065*k, 2.4)], N=14, M=_frame(Vector(j["kn"]).lerp(Vector(j["an"]), 0.08), Vector(j["an"]) - Vector(j["kn"])))
    sph(f"{side}LowerLeg", GOLD, (j["kn"][0], -0.045*k, j["kn"][2]), 0.05*k, scale=(1, 0.6, 1.1), u=12, v=8)
    arc_band(f"{side}UpperLeg", STONE, (j["hp"][0]*1.2, 0), Z(1.00), Z(0.78), (.1*k, .09*k), (.12*k, .1*k), (0 if s > 0 else math.pi) - 0.9, (0 if s > 0 else math.pi) + 0.9, 0.012, 10)
if True:   # left forearm guard (shield arm) - plate is body armour; the real shield is weaponry (Shield_L socket)
    j = J["Left"]; c = Vector(j["el"]).lerp(Vector(j["wr"]), 0.5) + Vector((0.07*k, 0, 0))
    loft("LeftLowerArm", STONE, [(-0.13*k, .008, .03*k), (-0.06*k, .015, .08*k), (0.08*k, .015, .09*k), (0.15*k, .008, .03*k)], N=8, M=TR(c), sub=1)
    gem("LeftLowerArm", GLOW, tuple(c + Vector((0.018, 0, 0))), 0.02*k, 0.015, rot=(0, math.pi/2, 0), sides=6)
cloth("LowerTorso", "LowerTorso", Z(0.8), BLUE, -.12*k, Z(1.08), Z(0.62), .20*k, .24*k, bow=0.03, teeth=4, depth=0.06*k, rows=6, cols=6)
arc_band("LowerTorso", GOLD, (0, 0), Z(1.10), Z(1.06), (.16*k, .12*k), (.17*k, .125*k), 0, 2*math.pi, 0.015, 24)
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.02, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.2, 0)), "RightHand")
add_bone("Shield_L", Vector(J["Left"]["el"]).lerp(Vector(J["Left"]["wr"]), 0.5) + Vector((0.08, 0, 0)), Vector(J["Left"]["el"]).lerp(Vector(J["Left"]["wr"]), 0.5) + Vector((0.2, 0, 0)), "LeftLowerArm")
rig, PARTS = assemble(NAME, OFFSET)
