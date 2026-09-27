# LUCKBOUND - Sky Citadel BASIC enemy: Citadel Bulwark (close range, tank; Citadel walls + gatehouses).
# NEW (2026-09-26, owner: replaces the Rootbound Warden slot - that grove-root design never fit the citadel and
# was moved to Verdant Valley, where its palette actually belongs). A squat, low-slung STONE-AND-IRON SHIELD
# GUARDIAN: dark graphite plate over a matte black undersuit, violet piping, pale stone inlays, cyan aether glow
# - built WIDE and LOW rather than tall, with a single-slab riveted tower SHIELD strapped along the whole left
# forearm (SHIELD BLOCK: raises it for a long guard window - punishable) and an empty Weapon_R grip for its
# citadel maul (added in Studio; SLAM, long recovery = the opening). Thick greaves, wide sabatons, a low battle
# helm with one narrow glowing visor slit. Distinct from the Skyport Hauler (dock-loader exo-frame, grab-and-
# throw) and the Gilded Sentinel (tall, swept, disciplined duelist guard) - this is the wall that doesn't move.
# ~2.35 m. Basic tier 10-12.5k.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "CitadelBulwark"; OFFSET = (40.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("CB_Graphite", (0.26, 0.27, 0.31), 0.45, 0.2), mat("CB_Violet", (0.40, 0.16, 0.52), 0.2, 0.3),
        mat("CB_Stone", (0.74, 0.72, 0.67), 0.05, 0.28), mat("CB_Under", (0.05, 0.05, 0.06), 0.0, 0.45),
        mat("CB_Iron", (0.24, 0.25, 0.28), 0.85, 0.22), mat("CB_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
GRAPHITE, VIOLET, STONE, UNDER, IRONM = 0, 1, 2, 3, 4
J, k = make_humanoid(2.35, shoulder=0.32, hip=0.15, build_body=False)
Z = lambda z: z*k
V = Vector
# =============================== UNDER-BODY (matte black construct frame - wide, squat) ===============================
loft("UpperTorso", UNDER, [(Z(1.06), .16*k, .12*k, 2.2), (Z(1.20), .19*k, .135*k, 2.2), (Z(1.36), .21*k, .14*k, 2.2),
                           (Z(1.46), .18*k, .12*k, 2.2), (Z(1.51), .07*k, .06*k)], N=18)
loft("LowerTorso", UNDER, [(Z(0.9), .155*k, .115*k, 2.2), (Z(1.0), .145*k, .105*k, 2.2), (Z(1.1), .14*k, .10*k, 2.2)], N=18)
loft("Head", UNDER, [(Z(1.48), .055*k, .055*k), (Z(1.55), .05*k, .05*k)], N=12)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    for bone, a, c, rs in ((f"{side}UpperArm", j["sh"], j["el"], (0.065, 0.075, 0.065, 0.05)),
                           (f"{side}LowerArm", j["el"], j["wr"], (0.055, 0.06, 0.05, 0.04)),
                           (f"{side}UpperLeg", j["hp"], j["kn"], (0.095, 0.105, 0.085, 0.065)),
                           (f"{side}LowerLeg", j["kn"], j["an"], (0.07, 0.078, 0.058, 0.046))):
        a, c = V(a), V(c); d = c - a; n = d.length
        loft(bone, UNDER, [(0, rs[0]*k, rs[0]*k), (n*0.3, rs[1]*k, rs[1]*k*1.05), (n*0.72, rs[2]*k, rs[2]*k), (n, rs[3]*k, rs[3]*k)], N=14, M=_frame(a, d))
    for bone, p_, r in ((f"{side}UpperArm", j["sh"], 0.07), (f"{side}LowerArm", j["el"], 0.058), (f"{side}UpperLeg", j["hp"], 0.09),
                        (f"{side}LowerLeg", j["kn"], 0.07)):
        sph(bone, UNDER, p_, r*k, u=12, v=8)
    wr, hd = V(j["wr"]), V(j["hd"])
    sph(f"{side}Hand", UNDER, tuple(wr), 0.045*k, u=10, v=6)
    box(f"{side}Hand", UNDER, tuple(wr.lerp(hd, 0.5)), (0.045*k, 0.08*k, 0.1*k), bev=0.012*k, segs=1)
    an = V(j["an"])
    sph(f"{side}Foot", UNDER, tuple(an), 0.06*k, u=12, v=8)
# =============================== ARMOUR (graphite plate, violet piping, stone inlay, cyan glow) ===============================
PIECE = "Armour"
# cuirass: thick slab plates, faceted, wide barrel chest - clearly proud of the underbody frame (not just a re-skin)
loft("UpperTorso", GRAPHITE, [(Z(1.08), .195*k, .15*k, 1.8), (Z(1.18), .21*k, .162*k, 1.8),
                              (Z(1.32), .265*k, .18*k, 1.8), (Z(1.42), .27*k, .175*k, 1.8), (Z(1.475), .215*k, .14*k, 2.0)], N=20, cap=False)
for z0, r in ((Z(1.08), (.197*k, .152*k)), (Z(1.475), (.217*k, .142*k))):
    arc_band("UpperTorso", VIOLET, (0, 0), z0 + 0.008*k, z0 - 0.008*k, r, r, 0, 2*math.pi, 0.012*k, 28)
T = body_bvh()
chest_emblem(k, Z(1.30), -.15*k, VIOLET, GLOW, r=0.055)
for s_ in (1, -1):
    flow_line("UpperTorso", VIOLET, [(0.05*s_*k, -.14*k, Z(1.16)), (0.13*s_*k, -.12*k, Z(1.26)), (0.18*s_*k, -.08*k, Z(1.4))], r=0.008*k, T=T, centre=(0, 0, Z(1.25)))
    flow_line("UpperTorso", GLOW, [(0.07*s_*k, -.13*k, Z(1.12)), (0.13*s_*k, -.11*k, Z(1.22)), (0.16*s_*k, -.09*k, Z(1.32))], r=0.005*k, T=T, centre=(0, 0, Z(1.2)))
# waist: heavy belt + stone buckle
for z in (Z(1.06), Z(1.02)):
    arc_band("LowerTorso", GRAPHITE, (0, 0), z + 0.024*k, z - 0.024*k, (.148*k, .108*k), (.146*k, .106*k), -math.pi + 0.3, -0.3, 0.014*k, 16)
arc_band("LowerTorso", IRONM, (0, 0), Z(0.975), Z(0.955), (.152*k, .112*k), (.154*k, .114*k), 0, 2*math.pi, 0.016*k, 28)
box("LowerTorso", STONE, (0, -0.115*k, Z(0.965)), (0.055*k, 0.02*k, 0.045*k), bev=0.007*k, segs=1)
gorget(k, Z(1.49), GRAPHITE, VIOLET, r=0.10, depth=0.09)
faulds(J, k, Z(0.95), GRAPHITE, VIOLET, n=2, width=0.15, drop=0.1, front=True, back=True, sides=True)
# broad single-slab pauldrons (riveted, wider/heavier than the Gilded Sentinel's swept fan)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; sh = V(j["sh"]); bn = f"{side}UpperArm"
    pc = sh + V((0.03*s*k, 0.01*k, 0.05*k))
    box(bn, GRAPHITE, tuple(pc), (0.13*k, 0.16*k, 0.075*k), rot=(0.08, 0, 0.12*s), top=(0.75, 0.85), bev=0.02*k, segs=3)
    box(bn, IRONM, tuple(pc + V((0, -0.03*k, -0.05*k))), (0.135*k, 0.02*k, 0.01*k), rot=(0.08, 0, 0.12*s), bev=0.006*k, segs=1)
# bracers / greaves / knee cops - sized to THIS frame's bulkier limbs (the shared character_kit plates are
# calibrated to the slim default humanoid and read as invisible/sunken over these wider arms and legs)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; el, wr, kn, an = V(j["el"]), V(j["wr"]), V(j["kn"]), V(j["an"])
    Ma = _frame(el, wr - el); na = (wr - el).length
    loft(f"{side}LowerArm", GRAPHITE, [(na*0.06, .066*k, .066*k, 1.8), (na*0.4, .072*k, .072*k, 1.8), (na*0.8, .06*k, .06*k, 1.8)], N=16, M=Ma)
    loft(f"{side}LowerArm", VIOLET, [(na*0.06, .069*k, .069*k, 1.8), (na*0.075, .069*k, .069*k, 1.8)], N=16, M=Ma, cap=False)
    tube(f"{side}LowerArm", GLOW, tuple(Ma @ V((0, -.07*k, na*0.2))), tuple(Ma @ V((0, -.062*k, na*0.7))), 0.006*k, 0.006*k, N=5)
    Ml = _frame(kn, an - kn); nl = (an - kn).length
    loft(f"{side}LowerLeg", GRAPHITE, [(nl*0.05, .085*k, .085*k, 1.8), (nl*0.4, .09*k, .09*k, 1.8), (nl*0.82, .066*k, .066*k, 1.8)], N=16, M=Ml)
    loft(f"{side}LowerLeg", VIOLET, [(nl*0.82, .068*k, .068*k, 1.8), (nl*0.84, .068*k, .068*k, 1.8)], N=16, M=Ml, cap=False)
    sph(f"{side}LowerLeg", GRAPHITE, (kn.x, kn.y - 0.045*k, kn.z), 0.078*k, scale=(1.0, 0.7, 1.05), u=14, v=8)
    loft(f"{side}LowerLeg", VIOLET, [(0, .081*k, .057*k), (0.008*k, .081*k, .057*k)], N=16, M=TR((kn.x, kn.y - 0.045*k, kn.z)), cap=False)
    loft(f"{side}Foot", GRAPHITE, [(0, .052*k, .05*k, 2.2), (0.08*k, .06*k, .05*k, 2.2), (0.17*k, .05*k, .033*k, 2.2), (0.23*k, .022*k, .017*k)], N=14,
         M=TR((an.x, an.y + 0.05*k, 0.05*k), (math.pi/2, 0, 0)), sub=1)
    loft(f"{side}Foot", VIOLET, [(0.08*k, .062*k, .052*k, 2.2), (0.088*k, .062*k, .052*k, 2.2)], N=14, M=TR((an.x, an.y + 0.05*k, 0.05*k), (math.pi/2, 0, 0)), cap=False)
    # gauntlet plate over the underbody fist
    wr, hd = V(j["wr"]), V(j["hd"])
    box(f"{side}Hand", GRAPHITE, tuple(wr.lerp(hd, 0.45)), (0.05*k, 0.085*k, 0.09*k), bev=0.012*k, segs=1)
# ---- tower shield: single riveted slab strapped along the LEFT forearm, violet rim, stone boss, glow core ----
j = J["Left"]; el, wr = V(j["el"]), V(j["wr"])
sh_c = el.lerp(wr, 0.4) + V((0.155*k, -0.01*k, 0.02*k))
box("LeftLowerArm", GRAPHITE, tuple(sh_c), (0.045*k, 0.19*k, 0.34*k), rot=(0.05, 0, 0.06), top=(1.0, 0.72), bev=0.02*k, segs=3)
box("LeftLowerArm", IRONM, tuple(sh_c), (0.05*k, 0.196*k, 0.348*k), rot=(0.05, 0, 0.06), top=(1.0, 0.72), bev=0.006*k, segs=1)
box("LeftLowerArm", STONE, tuple(sh_c + V((0.024*k, 0, 0))), (0.018*k, 0.075*k, 0.09*k), rot=(0.05, 0, 0.06), bev=0.01*k, segs=2)
sph("LeftLowerArm", GLOW, tuple(sh_c + V((0.036*k, 0, 0))), 0.028*k, scale=(0.5, 1, 1), u=12, v=8)
for dy in (-1, 1):
    for dz in (-1, 1):
        sph("LeftLowerArm", IRONM, tuple(sh_c + V((0.026*k, dy*0.15*k, dz*0.24*k))), 0.012*k, u=8, v=6)
for t in (0.3, 0.6):                                                                 # buckle straps bridging forearm to shield (no gap)
    p0 = el.lerp(wr, t); p1 = p0 + V((0.11*k, -0.005*k, 0.01*k))
    tube("LeftLowerArm", IRONM, tuple(p0), tuple(p1), 0.018*k, 0.014*k, N=8)
# ---- helm: low, wide, thick brow, single narrow glowing visor slit, jaw guards ----
loft("Head", GRAPHITE, [(Z(1.51), .075*k, .086*k, 2.0, 0, -0.01*k), (Z(1.575), .088*k, .098*k, 2.0, 0, -0.012*k),
                        (Z(1.63), .086*k, .094*k, 2.1), (Z(1.665), .06*k, .066*k, 2.2), (Z(1.68), .02*k, .022*k)], N=22, sub=1)
loft("Head", VIOLET, [(Z(1.6), .09*k, .10*k, 2.1), (Z(1.61), .09*k, .10*k, 2.1)], N=22, cap=False)
box("Head", IRONM, (0, -0.087*k, Z(1.595)), (0.06*k, 0.005*k, 0.022*k), bev=0.003*k, segs=1)
box("Head", GLOW, (0, -0.09*k, Z(1.595)), (0.05*k, 0.006*k, 0.012*k), bev=0.002*k, segs=1)
for s_ in (1, -1):
    blade("Head", GRAPHITE, (0.05*s_*k, -0.04*k, Z(1.56)), (0.3*s_, -0.3, -1), 0.09*k, 0.05*k, 0.014*k, hint=(0, 0, 1), N=8, sub=0)
PIECE = "Body"
add_bone("Weapon_R", tuple(V(J["Right"]["hd"]) + V((0, -0.02, 0))), tuple(V(J["Right"]["hd"]) + V((0, -0.2, 0))), "RightHand")
add_bone("Shield_L", tuple(sh_c), tuple(sh_c + V((0.1*k, 0, 0))), "LeftLowerArm")
rig, PARTS = assemble(NAME, OFFSET)
