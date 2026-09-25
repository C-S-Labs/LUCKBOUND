# LUCKBOUND - Sky Citadel BASIC enemy: Rootbound Warden (close range, heavy; Sky-Tree Grove + gardens).
# v3 REVAMP (2026-09-24, owner: the v1/v2 barrel body read as a clunky tin can). Now a tall, HUNCHED guardian of
# BRAIDED ROOTS: narrow braided waist, heavy mossy shoulders, very long arms that nearly drag - a root-claw hand for
# the GRAB and a fist sealed in old citadel masonry for the ROOT SLAM. Its face is a carved citadel statue mask
# grown into the wood, amber sap eyes, antler branches in blossom. Slow heavy walk; the slam's recovery is the opening.
# ~2.6 m. Rig: humanoid (R15) + CrownL/C/R branch bones (sway). Basic tier 10-12.5k.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "RootboundWarden"; OFFSET = (40.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("RW_Bark", (0.30, 0.2, 0.13), 0.0, 0.35), mat("RW_Moss", (0.26, 0.45, 0.2), 0.0, 0.45),
        mat("RW_Stone", (0.78, 0.76, 0.7), 0.05, 0.25), mat("RW_Blossom", (0.96, 0.66, 0.76), 0.0, 0.35),
        mat("RW_BarkDark", (0.15, 0.1, 0.07), 0.0, 0.45), mat("RW_Glow", (1.0, 0.62, 0.18), 0, 0.3, (1.0, 0.55, 0.1), 2.4)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BARK, MOSS, STONE, BLOSSOM, DARK = 0, 1, 2, 3, 4
J, k = make_humanoid(2.6, shoulder=0.27, hip=0.11, build_body=False)
Z = lambda z: z*k
V = Vector
def braid(bone, a, c, r, strands=2, turns=0.8, m=BARK, taper=0.75, N=5, steps=7):
    """Root limb: a smooth tapered core with slightly irregular bulges, wrapped by strands spiralling on its surface."""
    a, c = V(a), V(c); d = c - a; F = _frame(a, d); L_ = d.length
    loft(bone, m, [(0, r*0.55, r*0.5), (L_*0.3, r*0.6, r*0.52), (L_*0.6, r*0.5*(0.5 + taper*0.5), r*0.46*(0.5 + taper*0.5)), (L_, r*0.45*taper, r*0.42*taper)], N=12, M=F)
    for sI in range(strands):
        pts_ = []
        for i in range(steps + 1):
            u = i/steps; ang = sI*2*math.pi/strands + turns*2*math.pi*u
            rr = (r*0.55*(1 - u) + r*0.45*taper*u)*0.98
            pts_.append(F @ V((rr*math.cos(ang), rr*0.92*math.sin(ang), L_*u)))
        for p0, p1 in zip(pts_, pts_[1:]):
            tube(bone, DARK, tuple(p0), tuple(p1 + (p1 - p0)*0.08), r*0.16, r*0.15, N=N)
# ---- hunched torso: heavy braided chest over a narrow braided waist ----
braid("LowerTorso", (0, 0, Z(0.93)), (0, 0.01*k, Z(1.14)), 0.1*k, strands=4, turns=0.6, taper=1.05)
loft("UpperTorso", BARK, [(Z(1.12), .12*k, .1*k, 2.2, 0, .02*k), (Z(1.26), .19*k, .15*k, 2.2, 0, .04*k), (Z(1.4), .25*k, .17*k, 2.2, 0, .07*k),
                          (Z(1.5), .23*k, .15*k, 2.2, 0, .09*k), (Z(1.56), .12*k, .1*k, 2.2, 0, .08*k)], N=20, sub=1)
T = body_bvh()
for s in (1, -1):                                                            # root ribs wrapping the chest
    for rI in range(3):
        z0 = Z(1.2) + rI*0.09*k
        flow_line_in("UpperTorso", DARK, [(0.03*s*k, -0.3*k, z0 - 0.02*k), (0.14*s*k, -0.25*k, z0), (0.22*s*k, -0.1*k, z0 + 0.03*k), (0.2*s*k, 0.1*k, z0 + 0.05*k)],
                     r=0.022*k, T=T, centre=(0, 0.04*k, z0))
for z0 in (Z(1.24), Z(1.34)):                                                # amber sap glowing between the ribs
    flow_line_in("UpperTorso", GLOW, [(-0.1*k, -0.3*k, z0 + 0.04*k), (0, -0.3*k, z0 + 0.045*k), (0.1*k, -0.3*k, z0 + 0.04*k)], r=0.008*k, T=T, centre=(0, 0.04*k, z0 + 0.04*k))
# ---- legs: braided thighs + shins, root-toed feet ----
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    braid(f"{side}UpperLeg", j["hp"], j["kn"], 0.13*k, strands=3, turns=0.5)
    braid(f"{side}LowerLeg", j["kn"], j["an"], 0.1*k, strands=3, turns=0.5, taper=0.8)
    sph(f"{side}LowerLeg", BARK, j["kn"], 0.06*k, u=10, v=6)
    an = V(j["an"])
    sph(f"{side}Foot", BARK, tuple(an), 0.055*k, u=10, v=6)
    for t in range(4):                                                       # splayed root toes gripping the ground
        a0 = -math.pi/2 + (t - 1.5)*0.45
        p0 = an + V((0, 0, -0.01*k)); p1 = an + V((0.16*k*math.cos(a0)*0.7*s + 0.02*s*k, 0.16*k*math.sin(a0), -an.z + 0.012))
        tube(f"{side}Foot", DARK if t % 2 else BARK, tuple(p0), tuple(p1), 0.028*k, 0.01*k, N=7)
PIECE = "Limbs"
# ---- arms: long braided arms; right = root-claw GRAB hand, left = masonry SLAM fist ----
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    sh, el, wr, hd = V(j["sh"]), V(j["el"]), V(j["wr"]), V(j["hd"])
    sph(f"{side}UpperArm", BARK, tuple(sh), 0.08*k, u=12, v=8)
    braid(f"{side}UpperArm", sh, el, 0.11*k, strands=3, turns=0.7)
    sph(f"{side}LowerArm", BARK, tuple(el), 0.055*k, u=10, v=6)
    braid(f"{side}LowerArm", el, wr, 0.1*k, strands=3, turns=0.7, taper=0.9)
    if side == "Right":                                                      # root-claw hand: 4 long curled root fingers
        sph("RightHand", BARK, tuple(wr), 0.05*k, u=10, v=6)
        for f in range(4):
            a0 = (f - 1.5)*0.55
            pts_ = [wr + V((0.03*math.sin(a0)*k, -0.02*k, 0)) + V((0.05*math.sin(a0)*k*u, (-0.06*u - 0.05*u*u)*k, -0.2*k*u + 0.06*k*u*u)) for u in [i/4 for i in range(5)]]
            for i, (p0, p1) in enumerate(zip(pts_, pts_[1:])):
                tube("RightHand", DARK if f % 2 else BARK, tuple(p0), tuple(p1), (0.024 - 0.004*i)*k, (0.02 - 0.004*i)*k, N=7)
    else:                                                                    # masonry slam fist: carved citadel stone, roots gripping it, sap crack
        fc = wr + (hd - wr)*0.45
        box("LeftHand", STONE, tuple(fc), (0.2*k, 0.18*k, 0.22*k), rot=(0.05, 0.1, 0.1), bev=0.025*k, segs=2)
        for t in range(3):
            a0 = t*2.1
            pts_ = [wr + (fc - wr)*0.1 + V(((0.11*math.cos(a0 + u*3))*k, (0.1*math.sin(a0 + u*3))*k, -u*0.2*k)) for u in [i/4 for i in range(5)]]
            for p0, p1 in zip(pts_, pts_[1:]): tube("LeftHand", DARK, tuple(p0), tuple(p1), 0.016*k, 0.014*k, N=6)
        box("LeftHand", GLOW, tuple(fc + V((0, -0.091*k, 0.02*k))), (0.012*k, 0.006*k, 0.14*k), rot=(0.05, 0.1, 0.35), bev=0.002*k, segs=1)
    for m in range(6):                                                       # heavy moss mantle over the shoulder
        a0 = (m - 2.5)*0.3
        blade(f"{side}UpperArm", MOSS, tuple(sh + V((0.01*s*k, 0.06*k*math.sin(a0), 0.05*k))), (0.45*s, 0.35*math.sin(a0), -1), 0.17*k, 0.05*k, 0.01*k, hint=(0, 1, 0), N=5, sub=0)
    for m in range(5):
        sph(f"{side}UpperArm", BLOSSOM, tuple(sh + V((0.03*s*k + 0.035*math.cos(m*1.3)*k, 0.035*math.sin(m*1.3)*k, 0.1*k))), 0.028*k, u=8, v=6)
PIECE = "Body"
# ---- head: carved citadel statue MASK grown into the wood, amber eyes, antlers in blossom ----
hc = V((0, -0.05*k, Z(1.58)))
sph("Head", BARK, tuple(hc + V((0, 0.03*k, 0))), 0.1*k, scale=(1.0, 1.1, 1.0), u=14, v=10)
loft("Head", STONE, [(Z(1.5), .07*k, .04*k, 2.2, 0, -0.1*k), (Z(1.58), .085*k, .05*k, 2.2, 0, -0.12*k), (Z(1.66), .08*k, .045*k, 2.2, 0, -0.115*k),
                     (Z(1.7), .055*k, .03*k, 2.2, 0, -0.1*k)], N=16, sub=1, keep=lambda c: c.y < -0.1*k)
for s in (1, -1):
    tube("Head", GLOW, (0.018*s*k, -0.163*k, Z(1.6)), (0.052*s*k, -0.156*k, Z(1.615)), 0.009*k, 0.007*k, N=6)
    tube("Head", DARK, (0.06*s*k, -0.1*k, Z(1.55)), (0.075*s*k, -0.04*k, Z(1.64)), 0.018*k, 0.012*k, N=6)
for side, bx, dz in (("L", 1, 0), ("C", 0, 0.05), ("R", -1, 0)):          # antler branches
    b0 = hc + V((0.06*bx*k, 0.04*k, 0.08*k)); d_ = V((0.5*bx, 0.25, 1)).normalized()
    b1 = b0 + d_*(0.32 + dz)*k
    add_bone(f"Crown{side}", tuple(b0), tuple(b1), "Head")
    tube(f"Crown{side}", BARK, tuple(b0), tuple(b1), 0.03*k, 0.014*k, N=7)
    for t in range(2):
        f0 = b0.lerp(b1, 0.45 + 0.3*t); fd = V((0.8*bx + (0.6 if bx == 0 else 0)*(1 - 2*t), 0.2, 0.6)).normalized()
        tube(f"Crown{side}", BARK, tuple(f0), tuple(f0 + fd*0.12*k), 0.014*k, 0.006*k, N=6)
        for q in range(3):
            sph(f"Crown{side}", BLOSSOM if q % 2 else MOSS, tuple(f0 + fd*0.12*k + V((0.02*math.cos(q*2)*k, 0.02*math.sin(q*2)*k, 0.01*k))), 0.022*k, u=8, v=6)
    for q in range(4):
        sph(f"Crown{side}", BLOSSOM if q % 2 else MOSS, tuple(b1 + V((0.025*math.cos(q*1.6)*k, 0.025*math.sin(q*1.6)*k, 0.01*k*q))), 0.026*k, u=8, v=6)
add_bone("Weapon_R", tuple(V(J["Right"]["hd"]) + V((0, -0.02, 0))), tuple(V(J["Right"]["hd"]) + V((0, -0.2, 0))), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
