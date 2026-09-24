# LUCKBOUND - Sky Citadel BASIC enemy: Skyport Hauler (close range, tank; Skyport + Dockside).
# A dock-loader brute: grab-and-throw, shoulder charge (long recovery = punish), ground stomp.
# Rust-orange tarp cloak, riveted iron plates, rope wraps, a cargo-hook on its back, brass goggles glowing amber.
# ~2.3 m, broad. Weapon_R socket (hammer/anchor TBD).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "SkyportHauler"; OFFSET = (50.0, 0.0, 0.015)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("SH_Tarp", (0.62, 0.28, 0.12), 0.0, 0.5), mat("SH_Iron", (0.22, 0.23, 0.25), 0.8, 0.3),
        mat("SH_Under", (0.1, 0.09, 0.08), 0.2, 0.45), mat("SH_Rope", (0.7, 0.6, 0.42), 0.0, 0.6),
        mat("SH_Brass", (0.72, 0.52, 0.22), 1.0, 0.22), mat("SH_Glow", (1.0, 0.6, 0.12), 0, 0.3, (1.0, 0.55, 0.08), 2.5)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
TARP, IRONM, UNDER, ROPE, BRASS = 0, 1, 2, 3, 4
J, k = make_humanoid(2.3, shoulder=0.27, hip=0.13, bulk=1.55, limb=1.7, m_body=IRONM, m_limb=UNDER, m_skin=UNDER, head=False,
                     torso_secs=[(1.08, .16, .12), (1.25, .2, .15), (1.4, .25, .16), (1.5, .22, .14), (1.55, .1, .09)])
Z = lambda z: z*k
# head sunk low: iron mask helm + brass goggles
sph("Head", IRONM, (0, -0.02*k, Z(1.6)), 0.1*k, scale=(1.05, 1.0, 0.95), u=16, v=10)
for s in (1, -1):
    loft("Head", BRASS, [(0, .03*k, .03*k), (0.025*k, .032*k, .032*k)], N=12, M=TR((0.04*s*k, -0.09*k, Z(1.62)), (math.pi/2, 0, 0)))
    sph("Head", GLOW, (0.04*s*k, -0.117*k, Z(1.62)), 0.022*k, scale=(1, 0.4, 1), u=10, v=6)
for i in range(4):   # breathing grille
    box("Head", UNDER, ((i - 1.5)*0.018*k, -0.095*k, Z(1.54)), (0.008*k, 0.02, 0.04*k), bev=0.002, segs=1)
# riveted chest plate + huge shoulder plates + rope wraps
loft("UpperTorso", IRONM, [(Z(1.2), .2*k, .05*k, 2.5, 0, -.13*k), (Z(1.38), .25*k, .06*k, 2.5, 0, -.15*k), (Z(1.48), .22*k, .05*k, 2.5, 0, -.13*k)], N=14)
for i in range(6):
    sph("UpperTorso", BRASS, (((i % 3) - 1)*0.12*k, -0.215*k, Z(1.25 + 0.1*(i // 3))), 0.012*k, u=6, v=4)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    sph(f"{side}UpperArm", IRONM, (j["sh"][0]*1.1, 0, j["sh"][2] + .02*k), 0.14*k, scale=(1.15, 1.2, 0.75), cut_below=-0.3, u=16, v=10)
    for r in range(3):
        a = Vector(j["el"]).lerp(Vector(j["wr"]), 0.25 + r*0.2)
        loft(f"{side}LowerArm", ROPE, [(-0.012*k, .08*k, .08*k), (0.012*k, .08*k, .08*k)], N=12, M=_frame(a, Vector(j["wr"]) - Vector(j["el"])))
    loft(f"{side}LowerLeg", IRONM, [(0, .1*k, .105*k, 2.4), (0.3*k, .085*k, .09*k, 2.4)], N=12, M=_frame(Vector(j["kn"]).lerp(Vector(j["an"]), 0.1), Vector(j["an"]) - Vector(j["kn"])))
    sph(f"{side}Hand", IRONM, j["wr"], 0.085*k, u=12, v=8)        # big gauntlet fist
# tarp cloak over the back + hood rolled at the neck
cloth("UpperTorso", "UpperTorso", Z(1.0), TARP, 0.17*k, Z(1.52), Z(0.72), .46*k, .55*k, bow=0.06, teeth=5, depth=0.07*k, rows=8, cols=8, face=1)
loft("UpperTorso", TARP, [(0, .16*k, .13*k), (0.07*k, .15*k, .12*k)], N=16, M=TR((0, 0.02*k, Z(1.5))))
# cargo hook + coiled chain on the back
add_bone("CargoHook", (0.12*k, 0.28*k, Z(1.2)), (0.12*k, 0.3*k, Z(1.5)), "UpperTorso")
tube("CargoHook", IRONM, (0.12*k, 0.26*k, Z(1.05)), (0.12*k, 0.26*k, Z(1.6)), 0.02*k, 0.02*k, N=8)
pts = [Vector((0.12*k + 0.08*math.sin(t)*k, 0.26*k, Z(1.05) - 0.08*k + 0.08*math.cos(t)*k)) for t in [math.pi*i/6 for i in range(7)]]
for a_, b_ in zip(pts, pts[1:]):
    tube("CargoHook", IRONM, tuple(a_), tuple(b_), 0.018*k, 0.018*k, N=6)
arc_band("LowerTorso", ROPE, (0, 0), Z(1.1), Z(1.04), (.2*k, .15*k), (.21*k, .155*k), 0, 2*math.pi, 0.02, 24)
add_bone("Weapon_R", Vector(J["Right"]["wr"]) + Vector((0, -0.05, -0.05)), Vector(J["Right"]["wr"]) + Vector((0, -0.25, -0.05)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
