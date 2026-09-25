# LUCKBOUND - Sky Citadel BASIC: Gilded Sentinel (v2 redesign, 2026-09-24). The citadel's line guard: a disciplined
# stone-and-gold construct knight, ~2.1 m. Role melee_guard: measured 1-2 hit sword combos behind a forearm plate.
# Detail scheme (shared with the bosses, basic tier): smooth glossy plates that FOLLOW the body, gold trim rims and
# flow lines, cyan aether glow channels. Nothing clips.
# Silhouette: broad swept pauldrons, narrow waist, tall crested helm with a single V visor slit, split tabard (no cape: capes are saved for meaningful mobs).
# Budget: basic tier 10-12.5k tris, every mesh < 10k (Body / Armour pieces).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "GildedSentinel"; OFFSET = (20.0, 0.0, 0.01)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("GSB_Stone", (0.80, 0.78, 0.72), 0.05, 0.22), mat("GSB_Gold", (0.85, 0.62, 0.24), 1.0, 0.18),
        mat("GSB_Slate", (0.09, 0.10, 0.14), 0.35, 0.28), mat("GSB_Cloth", (0.16, 0.28, 0.48), 0.0, 0.4),
        mat("GSB_Spare", (0.5, 0.5, 0.5), 0, 0.3), mat("GSB_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
STONE, GOLD, SLATE, BLUE = 0, 1, 2, 3
J, k = make_humanoid(2.1, shoulder=0.23, hip=0.11, build_body=False)
Z = lambda z: z*k
V = Vector
# =============================== UNDER-BODY (slate construct musculature) ===============================
loft("UpperTorso", SLATE, [(Z(1.10), .12*k, .085*k, 2.3), (Z(1.22), .135*k, .09*k, 2.3), (Z(1.36), .175*k, .1*k, 2.3),
                           (Z(1.46), .16*k, .09*k, 2.3), (Z(1.52), .06*k, .055*k)], N=18, sub=0)
loft("LowerTorso", SLATE, [(Z(0.92), .125*k, .09*k, 2.3), (Z(1.02), .115*k, .085*k, 2.3), (Z(1.12), .115*k, .082*k, 2.3)], N=18, sub=1)
loft("Head", SLATE, [(Z(1.48), .045*k, .045*k), (Z(1.58), .04*k, .042*k)], N=12)
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    for bone, a, c, rs in ((f"{side}UpperArm", j["sh"], j["el"], (0.05, 0.062, 0.055, 0.042)),
                           (f"{side}LowerArm", j["el"], j["wr"], (0.045, 0.05, 0.04, 0.032)),
                           (f"{side}UpperLeg", j["hp"], j["kn"], (0.072, 0.08, 0.066, 0.05)),
                           (f"{side}LowerLeg", j["kn"], j["an"], (0.052, 0.06, 0.042, 0.034))):
        a, c = V(a), V(c); d = c - a; n = d.length
        loft(bone, SLATE, [(0, rs[0]*k, rs[0]*k), (n*0.3, rs[1]*k, rs[1]*k*1.08), (n*0.72, rs[2]*k, rs[2]*k), (n, rs[3]*k, rs[3]*k)], N=14, M=_frame(a, d), sub=0)
    for bone, p_, r in ((f"{side}UpperArm", j["sh"], 0.058), (f"{side}LowerArm", j["el"], 0.045), (f"{side}UpperLeg", j["hp"], 0.07),
                        (f"{side}LowerLeg", j["kn"], 0.052)):
        sph(bone, SLATE, p_, r*k, u=12, v=8)
    for bone, p_, r in ((f"{side}LowerArm", j["el"], 0.048), (f"{side}LowerLeg", j["kn"], 0.056)):   # glow joint rings
        loft(bone, GLOW, [(-0.004*k, r*k, r*k), (0.004*k, r*k, r*k)], N=18, M=_frame(V(p_), V(j["wr"] if "Arm" in bone else j["an"]) - V(p_)), cap=False)
    # gauntlet hand (closed-ish, sword grip) + sabaton
    wr, hd = V(j["wr"]), V(j["hd"]); Mh = _frame(wr, hd - wr, hint=(0, 1, 0))
    loft(f"{side}Hand", STONE, [(0.0, .03*k, .024*k, 2.4), (0.05*k, .038*k, .026*k, 2.4), (0.11*k, .034*k, .024*k, 2.4), (0.14*k, .016*k, .016*k)], N=12, M=Mh, sub=1)
    an = V(j["an"])
    sph(f"{side}Foot", SLATE, tuple(an), 0.045*k, u=12, v=8)
    loft(f"{side}Foot", STONE, [(0, .048*k, .045*k, 2.4), (0.07*k, .055*k, .045*k, 2.4), (0.16*k, .045*k, .03*k, 2.4), (0.21*k, .02*k, .015*k)], N=14,
         M=TR((an.x, an.y + 0.045*k, 0.045*k), (math.pi/2, 0, 0)), sub=1)
    loft(f"{side}Foot", GOLD, [(0.07*k, .057*k, .047*k, 2.4), (0.078*k, .057*k, .047*k, 2.4)], N=14, M=TR((an.x, an.y + 0.045*k, 0.045*k), (math.pi/2, 0, 0)), cap=False)
# =============================== ARMOUR (ivory plate, gold trim, cyan glow) ===============================
PIECE = "Armour"
# cuirass: tapered, faceted keel down the centre (n<2 = crisp ridge), open at the arms
loft("UpperTorso", STONE, [(Z(1.13), .135*k, .098*k, 1.7, 0, -0.004*k), (Z(1.22), .145*k, .108*k, 1.7, 0, -0.008*k),
                           (Z(1.33), .19*k, .126*k, 1.75, 0, -0.012*k), (Z(1.42), .2*k, .122*k, 1.85, 0, -0.008*k), (Z(1.465), .18*k, .11*k, 2.0)], N=24, sub=1, cap=False)
for z0, r in ((Z(1.13), (.137*k, .1*k)), (Z(1.465), (.182*k, .112*k))):
    arc_band("UpperTorso", GOLD, (0, 0), z0 + 0.006*k, z0 - 0.006*k, r, r, 0, 2*math.pi, 0.01*k, 28)
T = body_bvh()
flow_line("UpperTorso", GOLD, [(0, -.14*k, Z(1.16)), (0, -.14*k, Z(1.25)), (0, -.13*k, Z(1.3))], r=0.007*k, T=T, centre=(0, 0, Z(1.25)))
chest_emblem(k, Z(1.36), -.137*k, GOLD, GLOW, r=0.048)
for s_ in (1, -1):
    flow_line("UpperTorso", GOLD, [(0.05*s_*k, -.13*k, Z(1.4)), (0.12*s_*k, -.115*k, Z(1.44)), (0.17*s_*k, -.07*k, Z(1.455))], r=0.006*k, T=T, centre=(0, 0, Z(1.35)))
    flow_line("UpperTorso", GLOW, [(0.07*s_*k, -.11*k, Z(1.17)), (0.12*s_*k, -.1*k, Z(1.24)), (0.15*s_*k, -.085*k, Z(1.33))], r=0.0045*k, T=T, centre=(0, 0, Z(1.25)))
# segmented abdomen bands + belt with a gold buckle
for i, z in enumerate((Z(1.075), Z(1.035))):
    arc_band("LowerTorso", STONE, (0, 0), z + 0.02*k, z - 0.02*k, (.125*k, .093*k), (.123*k, .09*k), -math.pi + 0.35, -0.35, 0.012*k, 16)
arc_band("LowerTorso", GOLD, (0, 0), Z(0.995), Z(0.975), (.13*k, .096*k), (.132*k, .098*k), 0, 2*math.pi, 0.014*k, 28)
box("LowerTorso", GOLD, (0, -0.1*k, Z(0.985)), (0.05*k, 0.018*k, 0.04*k), bev=0.006*k, segs=1)
gorget(k, Z(1.49), STONE, GOLD, r=0.085, depth=0.075)
# swept pauldrons: three overlapping lens plates fanning down/out, gold-edged, and a small crown plate
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; sh = V(j["sh"]); bn = f"{side}UpperArm"
    for i, (dz, r, sc) in enumerate(((0.03, 0.105, (1.25, 1.12, 0.62)), (-0.03, 0.095, (1.2, 1.05, 0.5)), (-0.08, 0.085, (1.12, 1.0, 0.42)))):
        c_ = V((sh.x + (0.02 + 0.015*i)*s*k, 0, sh.z + dz*k))
        R_ = (0, -0.35*s - 0.1*s*i, 0)                                  # tilt outward/down: a sloped shoulder shell
        sph(bn, STONE, tuple(c_), r*k, scale=sc, cut_below=0.0, u=18, v=8, rot=R_)
        loft(bn, GOLD, [(0, r*sc[0]*k*1.005, r*sc[1]*k*1.005), (0.007*k, r*sc[0]*k*1.005, r*sc[1]*k*1.005)], N=22, M=TR(tuple(c_), R_), cap=False)
    # bracer + greave: slim plates that hug the limb (flatter section, no puffing), glow channel on the forearm
    for bone, a_, c_, t0, t1, rr, glow in ((f"{side}LowerArm", j["el"], j["wr"], 0.25, 0.92, (0.053, 0.05, 0.042), True),
                                           (f"{side}LowerLeg", j["kn"], j["an"], 0.14, 0.86, (0.064, 0.058, 0.046), False)):
        a_, c_ = V(a_), V(c_); d_ = c_ - a_; n_ = d_.length; M_ = _frame(a_ + d_*t0, d_)
        L_ = n_*(t1 - t0)
        loft(bone, STONE, [(0, rr[0]*k, rr[0]*k*1.05, 2.6), (L_*0.45, rr[1]*k, rr[1]*k*1.05, 2.6), (L_, rr[2]*k, rr[2]*k, 2.6)], N=16, M=M_)
        if glow: tube(bone, GLOW, tuple(M_ @ V((0, -rr[1]*k*1.04, L_*0.15))), tuple(M_ @ V((0, -rr[2]*k*1.04, L_*0.85))), 0.005*k, 0.005*k, N=5)
    kn = V(j["kn"])                                                     # knee cop, flush on the knee
    sph(f"{side}LowerLeg", STONE, (kn.x, kn.y - 0.035*k, kn.z), 0.06*k, scale=(1.0, 0.7, 1.05), u=16, v=8)
    sph(f"{side}LowerLeg", GOLD, (kn.x, kn.y - 0.078*k, kn.z), 0.017*k, scale=(1, 0.6, 1), u=10, v=6)
# shield arm: the forearm guard (the actual shield is weaponry on Shield_L)
j = J["Left"]; c = V(j["el"]).lerp(V(j["wr"]), 0.5) + V((0.065*k, 0, 0))
blade("LeftLowerArm", STONE, tuple(c + V((0.012*k, 0, 0.12*k))), (0.05, 0, -1), 0.28*k, 0.09*k, 0.016*k, hint=(1, 0, 0), N=8, sub=0)
gem("LeftLowerArm", GLOW, tuple(c + V((0.02*k, 0, 0))), 0.022*k, 0.016*k, rot=(0, math.pi/2, 0), sides=6)
# faulds: front/back lens plates + side tassets
for (x, y) in ((0, -1), (0, 1), (1, 0), (-1, 0)):
    p0 = V((0.12*x*k, 0.1*y*k, Z(0.98)))
    if y > 0 or x:                                                     # back plate + side tassets (tabard covers the front)
        blade("LowerTorso", STONE, tuple(p0 + V((0.02*x*k, 0.02*y*k, 0))), (0.08*x, 0.08*y, -1), 0.22*k, (0.12 if y else 0.1)*k, 0.014*k, hint=(y, -x, 0), N=8, sub=0)
# split tabard (front) in cloth
cloth("LowerTorso", "LowerTorso", Z(0.8), BLUE, -.115*k, Z(0.97), Z(0.5), .13*k, .15*k, bow=0.02, teeth=2, depth=0.04*k, rows=6, cols=6)
# helm: tall smooth helm, single V visor slit, swept gold crest fin, cheek guards
loft("Head", STONE, [(Z(1.53), .062*k, .074*k, 1.8, 0, -0.008*k), (Z(1.6), .078*k, .092*k, 1.8, 0, -0.01*k), (Z(1.67), .08*k, .092*k, 1.9),
                     (Z(1.72), .074*k, .084*k, 2.0), (Z(1.755), .05*k, .058*k, 2.1), (Z(1.77), .012*k, .014*k)], N=24, sub=1)
loft("Head", STONE, [(Z(1.68), .083*k, .095*k, 1.9), (Z(1.695), .082*k, .094*k, 1.9)], N=24, keep=lambda c: c.y < -0.02*k)   # visor brow
loft("Head", GOLD, [(Z(1.598), .082*k, .096*k, 2.2), (Z(1.607), .082*k, .096*k, 2.2)], N=22, cap=False)
for s_ in (1, -1):
    tube("Head", GLOW, (0.0, -0.093*k, Z(1.645)), (0.05*s_*k, -0.083*k, Z(1.672)), 0.0065*k, 0.0065*k, N=6)
    blade("Head", STONE, (0.068*s_*k, -0.05*k, Z(1.625)), (0.08*s_, -0.18, -1), 0.1*k, 0.04*k, 0.01*k, hint=(1, 0.3*s_, 0), N=8, sub=0)
for i, (dy, dz, L_) in enumerate(((-0.03, 0.0, 0.2), (0.0, -0.025, 0.17), (0.03, -0.05, 0.13))):   # swept gold crest
    blade("Head", GOLD, (0, dy*k, Z(1.765) + dz*k), (0, 1, 0.45 - 0.12*i), L_*k, 0.04*k, 0.008*k, hint=(1, 0, 0), N=8, sub=0)
PIECE = "Body"
add_bone("Weapon_R", V(J["Right"]["hd"]) + V((0, -0.02, 0)), V(J["Right"]["hd"]) + V((0, -0.2, 0)), "RightHand")
add_bone("Shield_L", V(J["Left"]["el"]).lerp(V(J["Left"]["wr"]), 0.5) + V((0.08, 0, 0)), V(J["Left"]["el"]).lerp(V(J["Left"]["wr"]), 0.5) + V((0.2, 0, 0)), "LeftLowerArm")
rig, PARTS = assemble(NAME, OFFSET)
