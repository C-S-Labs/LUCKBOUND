# LUCKBOUND - Sky Citadel BASIC enemy: Cloud Skirmisher (long range). Throws cloud-javelins, then must RELOAD
# (grabs a new javelin from the back quiver, 1.5 s) - that is the opening. Lean scout build, light armour. ~1.9 m.
# v2 character pass (2026-09-24): wind-cut hood, face wrap with a cyan slit, asymmetric brass pauldron, wrapped limbs,
# trailing scarf streamers, quiver of glow-tipped javelins. Basic tier 10-12.5k.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "CloudSkirmisher"; OFFSET = (30.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("CS_Cloth", (0.2, 0.3, 0.44), 0.0, 0.45), mat("CS_Brass", (0.75, 0.56, 0.24), 1.0, 0.2),
        mat("CS_Under", (0.08, 0.09, 0.12), 0.3, 0.4), mat("CS_White", (0.9, 0.9, 0.88), 0.0, 0.4),
        mat("CS_Leather", (0.3, 0.2, 0.13), 0.0, 0.45), mat("CS_Glow", (0.35, 0.9, 1.0), 0, 0.3, (0.3, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BLUE, BRASS, UNDER, WHITE, LEATHER = 0, 1, 2, 3, 4
J, k = make_humanoid(1.9, shoulder=0.2, hip=0.1, build_body=False)
Z = lambda z: z*k
V = Vector
# ---- shaped under-body (dark undersuit, slim) ----
loft("UpperTorso", UNDER, [(Z(1.10), .11*k, .08*k, 2.3), (Z(1.24), .125*k, .085*k, 2.3), (Z(1.37), .16*k, .092*k, 2.3), (Z(1.46), .14*k, .085*k, 2.3), (Z(1.52), .05*k, .05*k)], N=18)
loft("LowerTorso", UNDER, [(Z(0.92), .115*k, .085*k, 2.3), (Z(1.02), .105*k, .08*k, 2.3), (Z(1.12), .108*k, .078*k, 2.3)], N=18)
loft("Head", UNDER, [(Z(1.48), .04*k, .04*k), (Z(1.58), .038*k, .04*k)], N=12)
for side, s_ in (("Left", 1), ("Right", -1)):
    j = J[side]
    for bone, a_, c_, rs in ((f"{side}UpperArm", j["sh"], j["el"], (0.045, 0.055, 0.048, 0.038)), (f"{side}LowerArm", j["el"], j["wr"], (0.04, 0.045, 0.036, 0.029)),
                             (f"{side}UpperLeg", j["hp"], j["kn"], (0.066, 0.072, 0.06, 0.046)), (f"{side}LowerLeg", j["kn"], j["an"], (0.048, 0.055, 0.038, 0.031))):
        a_, c_ = V(a_), V(c_); d = c_ - a_; n = d.length
        loft(bone, UNDER, [(0, rs[0]*k, rs[0]*k), (n*0.3, rs[1]*k, rs[1]*k*1.08), (n*0.72, rs[2]*k, rs[2]*k), (n, rs[3]*k, rs[3]*k)], N=12, M=_frame(a_, d))
        for t in (0.3, 0.72):                                           # cloth wraps, sized to the limb at that point
            rr_ = rs[1] if t < 0.5 else rs[2]
            loft(bone, WHITE if "Arm" in bone else LEATHER, [(n*t - 0.012*k, rr_*k*1.03, rr_*k*1.08*1.03), (n*t + 0.012*k, rr_*k*1.03, rr_*k*1.08*1.03)], N=12, M=_frame(a_, d), cap=False)
    for bone, p_, r in ((f"{side}UpperArm", j["sh"], 0.05), (f"{side}LowerArm", j["el"], 0.04), (f"{side}UpperLeg", j["hp"], 0.064), (f"{side}LowerLeg", j["kn"], 0.048)):
        sph(bone, UNDER, p_, r*k, u=12, v=8)
    wr, hd = V(j["wr"]), V(j["hd"])
    loft(f"{side}Hand", LEATHER, [(0.0, .03*k, .022*k, 2.4), (0.06*k, .036*k, .024*k, 2.4), (0.13*k, .016*k, .015*k)], N=12, M=_frame(wr, hd - wr, hint=(0, 1, 0)), sub=1)
    an = V(j["an"]); sph(f"{side}Foot", LEATHER, tuple(an), 0.036*k, u=12, v=8)
    loft(f"{side}Foot", LEATHER, [(0, .042*k, .04*k, 2.4), (0.09*k, .048*k, .038*k, 2.4), (0.19*k, .03*k, .02*k, 2.4), (0.22*k, .01*k, .01*k)], N=12, M=TR((an.x, an.y + 0.045*k, 0.04*k), (math.pi/2, 0, 0)), sub=1)
    for bone, a_, c_, t0, t1, rr, m_ in ((f"{side}LowerArm", j["el"], j["wr"], 0.45, 0.95, (0.046, 0.043, 0.036), BRASS), (f"{side}LowerLeg", j["kn"], j["an"], 0.15, 0.8, (0.058, 0.054, 0.042), LEATHER)):
        a_, c_ = V(a_), V(c_); d = c_ - a_; M_ = _frame(a_ + d*t0, d); L_ = d.length*(t1 - t0)
        loft(bone, m_, [(0, rr[0]*k, rr[0]*k*1.05, 2.6), (L_*0.5, rr[1]*k, rr[1]*k*1.05, 2.6), (L_, rr[2]*k, rr[2]*k, 2.6)], N=14, M=M_)
        if "Arm" in bone:
            tube(bone, GLOW, tuple(M_ @ V((0, -rr[1]*k*1.05, L_*0.15))), tuple(M_ @ V((0, -rr[2]*k*1.05, L_*0.85))), 0.004*k, 0.004*k, N=5)
PIECE = "Gear"
# jerkin: fitted blue vest, brass-edged collar, crossing leather straps, brass studs, belt + buckle, front tabard
loft("UpperTorso", BLUE, [(Z(1.12), .118*k, .088*k, 2.1), (Z(1.25), .132*k, .094*k, 2.1), (Z(1.37), .168*k, .1*k, 2.1), (Z(1.46), .15*k, .092*k, 2.2)], N=20, sub=1, cap=False)
arc_band("UpperTorso", BRASS, (0, 0), Z(1.468), Z(1.458), (.152*k, .094*k), (.152*k, .094*k), 0, 2*math.pi, 0.008*k, 24)
T = body_bvh()
band = []                                                             # bandolier: one CLOSED band, left shoulder -> right hip, all the way round
for i in range(25):
    a = i*2*math.pi/24
    z = Z(1.28) + 0.16*k*math.cos(a - math.pi/2*0 )*0 + 0.15*k*math.sin(a + math.pi/4)
    band.append(on_surface_in(T, (0.3*k*math.cos(a), 0.3*k*math.sin(a), z), (0, 0, z), lift=0.004*k))
for a_, b_ in zip(band, band[1:]):
    loft("UpperTorso", LEATHER, [(0, .014*k, .005*k), ((b_ - a_).length, .014*k, .005*k)], N=6, M=_frame(a_, b_ - a_))
for i in range(3):
    sph("UpperTorso", BRASS, tuple(on_surface(T, (0.09*k - 0.05*i*k, -.1*k, Z(1.36) - 0.06*i*k), (0, 0, Z(1.28)), 0.006*k)), 0.01*k, u=8, v=6)
arc_band("LowerTorso", LEATHER, (0, 0), Z(1.1), Z(1.06), (.12*k, .088*k), (.122*k, .09*k), 0, 2*math.pi, 0.012*k, 24)
box("LowerTorso", BRASS, (0, -0.092*k, Z(1.08)), (0.04*k, 0.012*k, 0.032*k), bev=0.004*k, segs=1)
cloth("LowerTorso", "LowerTorso", Z(0.8), BLUE, -.084*k, Z(1.075), Z(0.72), .16*k, .19*k, bow=0.02, teeth=3, depth=0.05*k, rows=5, cols=6)
# asymmetric brass pauldron on the lead (left) shoulder
sh = V(J["Left"]["sh"])
for i, (dz, r, sc) in enumerate(((0.03, 0.09, (1.25, 1.1, 0.6)), (-0.025, 0.08, (1.15, 1.0, 0.48)))):
    sph("LeftUpperArm", BRASS, (sh.x + (0.02 + 0.015*i)*k, 0, sh.z + dz*k), r*k, scale=sc, cut_below=0.0, u=18, v=8, rot=(0, -0.4 - 0.1*i, 0))
# head: undersuit skull, face wrap, cyan visor slit, wind-cut hood swept back to a point, brass band
loft("Head", UNDER, [(Z(1.53), .062*k, .07*k), (Z(1.62), .078*k, .088*k), (Z(1.7), .074*k, .084*k), (Z(1.75), .045*k, .05*k), (Z(1.77), .01*k, .01*k)], N=18, sub=1)
loft("Head", WHITE, [(Z(1.54), .07*k, .078*k), (Z(1.63), .082*k, .09*k)], N=18, keep=lambda c: c.y < 0.02*k)
for s_ in (1, -1):                                                    # twin visor lenses, angled (focused, alert)
    loft("Head", GLOW, [(0, .016*k, .007*k, 1.8), (0.03*k, .014*k, .006*k, 1.8), (0.04*k, .004*k, .003*k, 1.8)], N=8,
         M=_frame(Vector((0.012*s_*k, -0.083*k, Z(1.662))), Vector((s_, 0.25, 0.18)), hint=(0, -1, 0)))
loft("Head", BLUE, [(Z(1.56), .08*k, .086*k, 2, 0, .006*k), (Z(1.66), .084*k, .094*k, 2, 0, .008*k), (Z(1.74), .077*k, .088*k, 2, 0, .012*k),
                    (Z(1.785), .04*k, .052*k, 2, 0, .02*k), (Z(1.8), .01*k, .014*k, 2, 0, .03*k)], N=20, keep=lambda c: c.y > -0.045*k, fill=False, sub=1)
arc_band("Head", BRASS, (0, 0), Z(1.705), Z(1.695), (.078*k, .088*k), (.078*k, .088*k), 0.4, math.pi - 0.4, 0.006*k, 12)
# scarf at the neck + two streamers trailing back
loft("UpperTorso", WHITE, [(Z(1.49), .07*k, .068*k), (Z(1.53), .066*k, .064*k)], N=16)
for s_, L_ in ((1, 0.5), (-1, 0.38)):
    st = [V((0.03*s_*k, 0.06*k, Z(1.5))) + V((0.05*s_*t*k, (0.1 + 0.9*t)*L_*k, -0.25*t*L_*k + 0.03*math.sin(math.pi*t*1.5)*k)) for t in [i/6 for i in range(7)]]
    for i, (a_, b_) in enumerate(zip(st, st[1:])):
        blade("UpperTorso", WHITE, tuple(a_), tuple(b_ - a_), (b_ - a_).length*1.15, 0.05*k*(1 - 0.08*i), 0.006*k, hint=(0, 0, 1), N=5, sub=0)
# quiver of glow-tipped javelins across the back
q0 = V((0.1*k, 0.1*k, Z(1.02))); qd = V((-0.35, 0.12, 1)).normalized()
loft("UpperTorso", LEATHER, [(0, .045*k, .04*k), (0.5*k, .04*k, .036*k)], N=12, M=_frame(q0, qd))
loft("UpperTorso", BRASS, [(0.48*k, .047*k, .042*k), (0.5*k, .047*k, .042*k)], N=12, M=_frame(q0, qd), cap=False)
for i in range(3):
    o = V(((i - 1)*0.022*k, 0, 0)); a_ = q0 + qd*0.3*k + o; b_ = q0 + qd*(0.78 + 0.03*i)*k + o
    tube("UpperTorso", LEATHER, tuple(a_), tuple(b_), 0.007*k, 0.007*k, N=5)
    loft("UpperTorso", GLOW, [(0, .014*k, .006*k, 1.4), (0.07*k, .002*k, .002*k)], N=6, M=_frame(b_, qd))
PIECE = "Body"
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.02, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.2, 0)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
