# LUCKBOUND - Sky Citadel MINIBOSS: Beacon Keeper (Lighthouse Point). A tall keeper whose head IS a lighthouse lamp.
# P1: sweeping searchlight that marks players for a delayed strike, lantern-staff slam.
# P2: the lamp overheats (glow -> red), beam spin + flare bursts. Whitewashed stone body, black iron lantern cage
# head with a warm lamp core, long dark-blue keeper's coat, brass fittings. ~3.1 m, gaunt. Full rig incl. fingers.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "BeaconKeeper"; OFFSET = (74.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("BK_White", (0.88, 0.87, 0.83), 0.0, 0.35), mat("BK_Iron", (0.06, 0.06, 0.07), 0.7, 0.3),
        mat("BK_Coat", (0.08, 0.13, 0.26), 0.0, 0.45), mat("BK_Brass", (0.78, 0.58, 0.25), 1.0, 0.2),
        mat("BK_Red", (0.6, 0.1, 0.08), 0.0, 0.4), mat("BK_Glow", (1.0, 0.85, 0.45), 0, 0.3, (1.0, 0.8, 0.35), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
WHITE, IRONM, COAT, BRASS, RED = 0, 1, 2, 3, 4
J, k = make_humanoid(3.1, shoulder=0.2, hip=0.1, bulk=0.85, limb=0.85, m_body=WHITE, m_limb=WHITE, m_skin=IRONM, head=False, fingers=True,
                     torso_secs=[(1.1, .13, .1), (1.26, .15, .105), (1.38, .17, .11), (1.47, .15, .1), (1.52, .07, .07)])
Z = lambda z: z*k
# long keeper's coat (split tails), red-and-white lighthouse bands on the collar
loft("UpperTorso", COAT, [(Z(1.1), .15*k, .115*k, 2.4), (Z(1.3), .17*k, .12*k, 2.4), (Z(1.46), .19*k, .12*k, 2.4), (Z(1.52), .1*k, .09*k)], N=20, sub=1)
for side, s in (("Left", 1), ("Right", -1)):
    cloth("LowerTorso", "LowerTorso", Z(0.6), COAT, 0.0, Z(1.1), Z(0.35), .16*k, .22*k, bow=0.0, teeth=3, depth=0.04*k, rows=8, cols=5, face=1) if False else None
loft("LowerTorso", COAT, [(Z(1.12), .15*k, .11*k), (Z(0.85), .19*k, .15*k), (Z(0.45), .22*k, .18*k)], N=20, keep=lambda c: c.y > -0.02*k or abs(c.x) > 0.05*k, fill=False)
for i in range(3):
    arc_band("UpperTorso", RED if i % 2 == 0 else WHITE, (0, 0), Z(1.49 + i*0.02), Z(1.51 + i*0.02), (.105*k - i*0.005*k, .095*k), (.1*k - i*0.005*k, .09*k), 0, 2*math.pi, 0.02, 24)
for i in range(4):
    sph("UpperTorso", BRASS, (0, -.125*k, Z(1.18 + i*0.08)), 0.012*k, u=8, v=6)                   # coat buttons
# the lamp head: iron gallery, glass lantern of glow, domed cap with vent + finial
loft("Head", IRONM, [(Z(1.52), .06*k, .06*k), (Z(1.57), .06*k, .06*k)], N=12)
loft("Head", IRONM, [(Z(1.57), .13*k, .13*k), (Z(1.6), .14*k, .14*k)], N=24)                   # gallery floor
for i in range(12):
    a = i*math.pi/6
    tube("Head", IRONM, (0.14*k*math.cos(a), 0.14*k*math.sin(a), Z(1.6)), (0.14*k*math.cos(a), 0.14*k*math.sin(a), Z(1.64)), 0.004*k, 0.004*k, N=4)
arc_band("Head", IRONM, (0, 0), Z(1.64), Z(1.645), (.14*k, .14*k), (.14*k, .14*k), 0, 2*math.pi, 0.008, 24)   # railing
loft("Head", GLOW, [(Z(1.6), .09*k, .09*k, 1.2), (Z(1.76), .09*k, .09*k, 1.2)], N=8)                       # lamp glass
for i in range(8):
    a = i*math.pi/4 + math.pi/8
    tube("Head", IRONM, (0.093*k*math.cos(a), 0.093*k*math.sin(a), Z(1.6)), (0.093*k*math.cos(a), 0.093*k*math.sin(a), Z(1.76)), 0.006*k, 0.006*k, N=4)
loft("Head", RED, [(Z(1.76), .115*k, .115*k), (Z(1.8), .1*k, .1*k), (Z(1.86), .05*k, .05*k), (Z(1.9), .015*k, .015*k)], N=16, sub=1)
sph("Head", BRASS, (0, 0, Z(1.92)), 0.018*k, u=10, v=6)
add_bone("LampSweep", (0, 0, Z(1.68)), (0, -0.2*k, Z(1.68)), "Head")                          # searchlight direction
# brass shoulder lanterns hooks, iron gloves, boots
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    sph(f"{side}UpperArm", COAT, (j["sh"][0]*1.05, 0, j["sh"][2] + 0.01*k), 0.075*k, scale=(1.2, 1.1, 0.8), cut_below=-0.3, u=14, v=8)
    loft(f"{side}LowerLeg", IRONM, [(0, .055*k, .06*k, 2.4), (0.36*k, .05*k, .055*k, 2.4)], N=12, M=_frame(Vector(j["kn"]).lerp(Vector(j["an"]), 0.1), Vector(j["an"]) - Vector(j["kn"])))
# --- miniboss detail pass ---
for side, s_ in (("Left", 1), ("Right", -1)):                          # epaulettes + fringe, glove cuffs
    j = J[side]
    loft(f"{side}UpperArm", BRASS, [(0, .07*k, .05*k, 2.2), (0.012*k, .075*k, .055*k, 2.2)], N=18, M=TR((j["sh"][0]*1.05, 0, j["sh"][2] + 0.04*k)))
    for f_ in range(10):
        a = (f_/9 - 0.5)*2.6 + (0 if s_ > 0 else math.pi)
        p0 = Vector((j["sh"][0]*1.05 + 0.072*k*math.cos(a), 0.052*k*math.sin(a), j["sh"][2] + 0.04*k))
        tube(f"{side}UpperArm", BRASS, tuple(p0), tuple(p0 + Vector((0.01*math.cos(a), 0.01*math.sin(a), -0.05*k))), 0.004*k, 0.003*k, N=4)
    arc_band(f"{side}LowerArm", BRASS, (j["wr"][0], j["wr"][1]), j["wr"][2] + 0.05*k, j["wr"][2] + 0.02*k, (.045*k, .045*k), (.05*k, .05*k), 0, 2*math.pi, 0.006*k, 20)
for i in range(3):                                                     # lighthouse stripes on the coat hem
    z0 = Z(0.47 + i*0.06)
    arc_band("LowerTorso", RED if i % 2 == 0 else WHITE, (0, 0), z0 + Z(0.03), z0, (.21*k, .17*k), (.222*k, .18*k), -math.pi/2 + 0.35, 3*math.pi/2 - 0.35, 0.008*k, 28)
for s_ in (1, -1):                                                     # lapels
    blade("UpperTorso", COAT, (0.04*s_*k, -.125*k, Z(1.47)), (0.35*s_, -0.15, -1), 0.2*k, 0.035*k, 0.008*k, hint=(0, 1, 0), N=6, sub=0)
arc_band("LowerTorso", IRONM, (0, 0), Z(1.12), Z(1.08), (.155*k, .118*k), (.158*k, .12*k), 0, 2*math.pi, 0.01*k, 28)
box("LowerTorso", BRASS, (0, -.122*k, Z(1.1)), (0.04*k, 0.012*k, 0.035*k), bev=0.004*k, segs=1)
kr = Vector((0.11*k, -0.09*k, Z(1.04)))                                  # key ring
loft("LowerTorso", BRASS, [(-0.004*k, .025*k, .025*k), (0.004*k, .025*k, .025*k)], N=14, M=TR(tuple(kr), (0, math.pi/2, 0)), cap=False)
for kk in range(4):
    a = kk*0.5 - 0.7
    blade("LowerTorso", BRASS, tuple(kr + Vector((0, 0.02*k*math.cos(a), -0.02*k))), (0, math.sin(a)*0.3, -1), 0.06*k, 0.01*k, 0.004*k, hint=(1, 0, 0), N=4, sub=0)
tube("LowerTorso", BRASS, (-0.13*k, -0.08*k, Z(1.1)), (-0.14*k, -0.09*k, Z(0.93)), 0.014*k, 0.018*k, N=10)   # spyglass
loft("LowerTorso", IRONM, [(0, .02*k, .02*k), (0.012*k, .02*k, .02*k)], N=10, M=_frame(Vector((-0.14*k, -0.09*k, Z(0.93))), Vector((-0.01, -0.01, -0.17))))
for i in range(4):                                                     # fresnel lens rings
    arc_band("Head", BRASS, (0, 0), Z(1.62 + i*0.035), Z(1.625 + i*0.035), (.082*k, .082*k), (.082*k, .082*k), 0, 2*math.pi, 0.006*k, 16)
tube("Head", IRONM, (0, 0, Z(1.93)), (0, 0, Z(2.02)), 0.004*k, 0.004*k, N=4)            # weather vane
blade("Head", IRONM, (0, 0.0, Z(2.0)), (0, 1, 0), 0.06*k, 0.02*k, 0.004*k, hint=(1, 0, 0), N=4, sub=0)
blade("Head", IRONM, (0, 0.0, Z(2.0)), (0, -1, 0.1), 0.05*k, 0.008*k, 0.004*k, hint=(1, 0, 0), N=4, sub=0)
for s_ in (1, -1):
    tube("Head", IRONM, (0, 0, Z(1.985)), (0.03*s_*k, 0, Z(1.985)), 0.002*k, 0.002*k, N=4)
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.02, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.25, 0)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
