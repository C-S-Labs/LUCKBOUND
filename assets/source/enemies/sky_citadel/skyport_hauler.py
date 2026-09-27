# LUCKBOUND - Sky Citadel BASIC enemy: Skyport Hauler (close range, tank; Skyport + Dockside).
# v4 REVAMP (2026-09-26, owner: v3 read as a blobby snowman - shoulder ram plate clipped straight through the
# head, the furnace core bulged out past the ribs like an egg, and the 3-claw grabbers were lost twigs dangling
# off huge round forearms). Same inverted-V DOCK-LOADER EXO-FRAME concept, rebuilt with real proportions: a
# lowered, narrowed shoulder yoke so the head actually reads above it, a smaller RECESSED furnace core sealed
# behind the ribs instead of poking through them, the shoulder-charge ram rebuilt as a flat plough WEDGE mounted
# forward-and-down off the shoulder (clear of the head entirely) instead of a giant floating disc, and bigger,
# wider-set claws with a brass wrist collar so the GRAB-AND-THROW hands actually read past the forearm. Piston
# legs with wide stomp feet (STOMP) unchanged. Cargo clamp crate on the back unchanged. Glossy iron + brass,
# rust-orange tarp accents. ~2.3 m. Basic tier 10-12.5k.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "SkyportHauler"; OFFSET = (50.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("SH_Tarp", (0.66, 0.3, 0.12), 0.0, 0.35), mat("SH_Iron", (0.2, 0.21, 0.24), 0.85, 0.22),
        mat("SH_Under", (0.08, 0.08, 0.09), 0.4, 0.35), mat("SH_Steel", (0.62, 0.64, 0.68), 0.9, 0.18),
        mat("SH_Brass", (0.78, 0.56, 0.24), 1.0, 0.18), mat("SH_Glow", (1.0, 0.6, 0.12), 0, 0.3, (1.0, 0.55, 0.08), 2.6)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
TARP, IRONM, UNDER, STEEL, BRASS = 0, 1, 2, 3, 4
J, k = make_humanoid(2.3, shoulder=0.3, hip=0.12, build_body=False)
Z = lambda z: z*k
V = Vector
def piston(bone, a, b, r):
    """Hydraulic ram: steel rod sliding into an iron sleeve, brass collar."""
    a, b = V(a), V(b); m = a.lerp(b, 0.55)
    tube(bone, IRONM, tuple(a), tuple(m), r, r, N=10); tube(bone, STEEL, tuple(m), tuple(b), r*0.55, r*0.55, N=8)
    loft(bone, BRASS, [(-0.01*k, r*1.12, r*1.12), (0.01*k, r*1.12, r*1.12)], N=10, M=_frame(m, b - a), cap=False)
def shell(bone, a, b, rs, m=IRONM, N=16, sub=0, flat=3.4):
    a, b = V(a), V(b); d = b - a; n = d.length
    loft(bone, m, [(n*t, r0*k, r1*k, flat) for t, r0, r1 in rs], N=N, M=_frame(a, d), sub=sub)
# ---- hunched torso: open rib cage (steel ribs) round a RECESSED glowing furnace core, iron spine + shoulder yoke ----
loft("UpperTorso", UNDER, [(Z(1.1), .13*k, .1*k), (Z(1.3), .15*k, .11*k), (Z(1.46), .14*k, .1*k), (Z(1.52), .07*k, .06*k)], N=16)
sph("UpperTorso", GLOW, (0, -0.03*k, Z(1.29)), 0.075*k, scale=(1.0, 0.7, 1.1), u=16, v=10)                                    # furnace core (sealed behind the ribs)
box("UpperTorso", UNDER, (0, -0.01*k, Z(1.29)), (0.11*k, 0.02*k, 0.13*k), bev=0.01*k, segs=1)                                 # dark housing rim behind the core so it reads sealed, not floating
for i in range(5):                                                                                                        # steel ribs (tighter spacing, fully caging the core)
    z = Z(1.15) + i*0.065*k; rx = (0.157 + 0.008*math.sin(i*1.3))*k
    arc_band("UpperTorso", STEEL, (0, -0.005*k), z + 0.016*k, z - 0.016*k, (rx, 0.122*k), (rx, 0.122*k), -math.pi*0.92, -math.pi*0.08, 0.02*k, 18)
loft("UpperTorso", IRONM, [(Z(1.40), .24*k, .15*k, 3.0), (Z(1.48), .27*k, .16*k, 3.0), (Z(1.51), .16*k, .11*k, 2.6)], N=22)   # shoulder yoke, capped BELOW the head so it doesn't swallow it
loft("UpperTorso", IRONM, [(Z(1.1), .1*k, .06*k, 2, 0, .1*k), (Z(1.55), .11*k, .065*k, 2, 0, .11*k)], N=12)                    # spine plate
loft("LowerTorso", IRONM, [(Z(0.9), .15*k, .11*k, 3.2), (Z(1.02), .16*k, .12*k, 3.2), (Z(1.12), .13*k, .1*k, 3.2)], N=18)
arc_band("LowerTorso", TARP, (0, 0), Z(1.06), Z(1.0), (.163*k, .123*k), (.166*k, .126*k), 0, 2*math.pi, 0.012*k, 24)          # tarp waist wrap
# ---- head: low sensor housing pushed forward and clear of the shoulders, twin amber lenses, brass visor band + rim ----
loft("Head", IRONM, [(Z(1.51), .1*k, .11*k, 2.4, 0, -0.045*k), (Z(1.60), .11*k, .12*k, 2.4, 0, -0.055*k), (Z(1.68), .08*k, .09*k, 2.4, 0, -0.045*k)], N=16, sub=1)
loft("Head", BRASS, [(Z(1.565), .102*k, .002*k, 2.4, 0, -0.135*k), (Z(1.605), .102*k, .002*k, 2.4, 0, -0.135*k)], N=16, cap=False)  # brass visor brow band
for s in (1, -1):
    loft("Head", BRASS, [(0, .034*k, .034*k), (0.024*k, .034*k, .034*k)], N=12, M=_frame(V((0.045*s*k, -0.145*k, Z(1.585))), V((0.15*s, -1, 0))), cap=False)
    sph("Head", GLOW, (0.045*s*k, -0.155*k, Z(1.585)), 0.028*k, scale=(1, 0.5, 1), u=12, v=8)
# ---- arms: slim upper arm, big-but-controlled hydraulic forearm, brass wrist collar, WIDE 3-claw grabber ----
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; sh, el, wr, hd = V(j["sh"]), V(j["el"]), V(j["wr"]), V(j["hd"])
    sph(f"{side}UpperArm", UNDER, tuple(sh), 0.075*k, u=12, v=8)
    shell(f"{side}UpperArm", sh, el, [(0.0, .06, .06), (0.5, .07, .065), (1.0, .055, .055)])
    piston(f"{side}UpperArm", sh + V((0.05*s*k, 0.05*k, -0.05*k)), el + V((0.04*s*k, 0.05*k, 0.03*k)), 0.018*k)
    sph(f"{side}LowerArm", UNDER, tuple(el), 0.055*k, u=12, v=8)
    shell(f"{side}LowerArm", el, wr, [(0.0, .075, .075), (0.3, .105, .10), (0.75, .098, .092), (1.0, .07, .07)])       # trimmed down from v3's oversized blob
    piston(f"{side}LowerArm", el + V((0, 0.07*k, 0.02*k)), wr + V((0, 0.08*k, 0.04*k)), 0.02*k)
    fa = (wr - el).normalized(); side_v = fa.cross(V((0, 1, 0))).normalized()
    for t in (0.35, 0.7):
        loft(f"{side}LowerArm", TARP, [(-0.012*k, .108*k, .10*k), (0.012*k, .108*k, .10*k)], N=16, M=_frame(el.lerp(wr, t), wr - el), cap=False)   # hazard bands
    loft(f"{side}LowerArm", BRASS, [(-0.008*k, .076*k, .072*k), (0.01*k, .076*k, .072*k)], N=16, M=_frame(wr, wr - el), cap=False)                  # wrist collar: clean break before the claws
    sph(f"{side}Hand", IRONM, tuple(wr), 0.085*k, u=12, v=8)
    for c in range(3):                                                                                                     # 3-claw grabber, spread wide so it reads clear of the forearm
        a0 = c*2*math.pi/3 + 0.5
        dirv = (fa + side_v*0.75*math.cos(a0) + V((0, 0.75*math.sin(a0), 0))).normalized()
        p0 = wr + dirv*0.07*k; p1 = p0 + dirv*0.16*k; p2 = p1 + (fa - dirv*0.55).normalized()*0.1*k
        tube(f"{side}Hand", STEEL, tuple(p0), tuple(p1), 0.03*k, 0.024*k, N=8); sph(f"{side}Hand", BRASS, tuple(p1), 0.026*k, u=8, v=6)
        tube(f"{side}Hand", STEEL, tuple(p1), tuple(p2), 0.024*k, 0.008*k, N=8)
# ---- legs: piston-sprung, reverse-braced, wide stomp feet ----
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; hp, kn, an = V(j["hp"]), V(j["kn"]), V(j["an"])
    sph(f"{side}UpperLeg", UNDER, tuple(hp), 0.07*k, u=12, v=8)
    shell(f"{side}UpperLeg", hp, kn, [(0.0, .09, .09), (0.4, .115, .11), (1.0, .075, .075)])
    sph(f"{side}LowerLeg", UNDER, tuple(kn), 0.055*k, u=12, v=8)
    shell(f"{side}LowerLeg", kn, an, [(0.0, .075, .075), (0.3, .1, .095), (1.0, .065, .065)])
    piston(f"{side}LowerLeg", kn + V((0, 0.07*k, -0.02*k)), an + V((0, 0.06*k, 0.06*k)), 0.018*k)
    sph(f"{side}Foot", IRONM, tuple(an), 0.05*k, u=10, v=6)
    box(f"{side}Foot", IRONM, (an.x, an.y - 0.04*k, 0.035*k), (0.15*k, 0.3*k, 0.07*k), bev=0.02*k, segs=2)
    box(f"{side}Foot", BRASS, (an.x, an.y - 0.19*k, 0.03*k), (0.14*k, 0.02*k, 0.05*k), bev=0.006*k, segs=1)
# ---- shoulder charge ram: a flat plough WEDGE mounted flush on the lead (left) shoulder, hazard edge -
#      close enough to the shoulder sphere to fuse into it (v3's giant disc floated off the shoulder and clipped
#      the head; the first v4 pass then floated the whole ram off the arm entirely) ----
PIECE = "Gear"
sh = V(J["Left"]["sh"])
ram_c = sh + V((0.09*k, -0.05*k, -0.015*k))
box("LeftUpperArm", IRONM, tuple(ram_c), (0.115*k, 0.145*k, 0.085*k), rot=(0.15, 0, -0.3), top=(0.3, 0.85), bev=0.014*k, segs=2)
box("LeftUpperArm", BRASS, tuple(ram_c + V((0, -0.083*k, -0.025*k))), (0.115*k, 0.011*k, 0.058*k), rot=(0.15, 0, -0.3), bev=0.004*k, segs=1)  # hazard leading edge
# ---- back: cargo clamp arms holding a crate ----
PIECE = "Body"
cz = Z(1.28); cy = 0.26*k
box("UpperTorso", TARP, (0, cy, cz), (0.34*k, 0.2*k, 0.28*k), bev=0.014*k, segs=2)
for dz in (-0.1, 0.1):
    box("UpperTorso", IRONM, (0, cy, cz + dz*k), (0.35*k, 0.21*k, 0.03*k), bev=0.005*k, segs=1)
for s in (1, -1):
    piston("UpperTorso", V((0.1*s*k, 0.1*k, Z(1.48))), V((0.12*s*k, cy - 0.05*k, cz + 0.14*k)), 0.016*k)
add_bone("Weapon_R", tuple(V(J["Right"]["hd"]) + V((0, -0.02, 0))), tuple(V(J["Right"]["hd"]) + V((0, -0.2, 0))), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
