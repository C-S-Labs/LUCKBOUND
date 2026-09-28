# LUCKBOUND - Ethereal Scape BASIC enemy: Crystal Warden (close range, heavy: brute).
# v3 REFINE (2026-09-27, owner: v1 was a floating gem cloud; v2's bulk multiplier made it a round snowman blob
# with the chest plates visibly detached in front). DESIGN INTENT: reads as a TANK -- broad square shoulders,
# a hard wedge down to a narrow waist (NOT a round ball), heavy slab forearms. Every crystal piece is FLUSH-
# MOUNTED on the body surface (projected with on_surface_in), not floating in front of it. Cloud-white temple
# armour has grown crystal plates (transfiguration): a single flush ridged breastplate, flush shoulder crystal
# caps, crystal vambraces built as part of the forearm taper (not a separate blob), crystal greaves. A tall
# gold-banded mask helm with a jaw plate and portal-glow slit. Slow heavy slams (long wind-up = punish window);
# shatters into shards on death. No halo. ~2.25 m, wide stance. Basic tier 10-15k. Faces -Y.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "CrystalWarden"; OFFSET = (9.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("CW_Cloud", (0.84, 0.94, 0.9), 0.0, 0.28), mat("CW_Teal", (0.16, 0.52, 0.46), 0.0, 0.3),
        mat("CW_Gold", (0.87, 0.70, 0.38), 1.0, 0.18), mat("CW_Crystal", (0.6, 0.85, 0.97), 0.0, 0.05, (0.4, 0.75, 0.95), 0.4),
        mat("CW_Indigo", (0.3, 0.32, 0.58), 0.0, 0.3), mat("CW_Glow", (0.8, 1.0, 0.9), 0, 0.2, (0.55, 1.0, 0.8), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
FRAME, TEAL, GOLD, CRYST, INDIGO = 0, 1, 2, 3, 4
J, k = make_humanoid(2.25, shoulder=0.27, hip=0.11, bulk=1.05, limb=1.15, m_body=FRAME, m_limb=FRAME, m_skin=INDIGO, head=False)
Z = lambda z: z*k
V = Vector
# ---- torso: SQUARE broad shoulders, straight hard wedge down to a narrow waist (tank silhouette, not a ball) ----
loft("UpperTorso", FRAME, [(Z(1.08), .15*k, .11*k, 2.6), (Z(1.22), .21*k, .13*k, 2.6), (Z(1.4), .24*k, .135*k, 2.8), (Z(1.51), .155*k, .1*k, 2.6)], N=28, sub=2)
loft("LowerTorso", INDIGO, [(Z(0.88), .128*k, .095*k), (Z(1.0), .112*k, .085*k), (Z(1.1), .148*k, .105*k)], N=24, sub=1)   # cinched waist
arc_band("LowerTorso", GOLD, (0, 0), Z(1.03), Z(0.96), (.117*k, .088*k), (.122*k, .092*k), 0, 2*math.pi, 0.02*k, 32)
for yy in (-1, 1):
    box("LowerTorso", TEAL, (0, yy*0.06*k, Z(0.72)), (0.135*k, 0.07*k, 0.3*k), rot=(-0.06*yy, 0, 0), bev=0.005*k, segs=2)
# ---- head: tall gold mask helm, gold-banded, squared jaw plate, portal slit ----
tube("Head", INDIGO, (0, 0, Z(1.49)), (0, 0, Z(1.56)), 0.072*k, 0.064*k, N=14)
loft("Head", GOLD, [(Z(1.56), .08*k, .085*k, 2.4), (Z(1.66), .085*k, .09*k, 2.4), (Z(1.73), .07*k, .076*k, 2.4)], N=24, sub=1)   # helm dome
loft("Head", GOLD, [(Z(1.555), .078*k, .04*k, 2.4, 0, -.04*k), (Z(1.6), .078*k, .04*k, 2.4, 0, -.04*k)], N=16, cap=False)         # jaw plate, fused to the dome front
box("Head", GLOW, (0, -0.075*k, Z(1.58)), (0.011*k, 0.011*k, 0.075*k), bev=0.003*k, segs=1)
for zz in (1.6, 1.68):
    arc_band("Head", GOLD, (0, 0), Z(zz + 0.006), Z(zz - 0.006), (.076*k, .086*k), (.079*k, .089*k), -math.pi + 0.3, -0.3, 0.006*k, 16)
gem("Head", CRYST, (0, 0.008*k, Z(1.755)), 0.02*k, 0.11*k, sides=6)                                                              # single small crest, fused to the dome crown
PIECE = "Gear"   # crystal armour: own mesh (keeps each mesh < 10k)
# ---- flush breastplate: ONE ridged crystal slab projected directly onto the chest surface, gold rivets ----
T = body_bvh()
bp_c = on_surface_in(T, (0, -0.4*k, Z(1.32)), (0, 0, Z(1.32)), lift=0.002*k)
box("UpperTorso", CRYST, tuple(bp_c), (0.19*k, 0.05*k, 0.22*k), top=(0.82, 0.94), bev=0.018*k, segs=1)
for zz, ridge_w in ((1.24, 0.16), (1.4, 0.13)):
    rc = on_surface_in(T, (0, -0.4*k, Z(zz)), (0, 0, Z(zz)), lift=0.01*k)
    box("UpperTorso", CRYST, tuple(rc), (ridge_w*k, 0.022*k, 0.028*k), bev=0.008*k, segs=1)
for s_ in (1, -1):
    rp = on_surface_in(T, (0.12*s_*k, -0.4*k, Z(1.32)), (0, 0, Z(1.32)), lift=0.014*k)
    sph("UpperTorso", GOLD, tuple(rp), 0.011*k, u=8, v=6)
box("UpperTorso", GLOW, tuple(bp_c + V((0, -0.002*k, 0))), (0.01*k, 0.012*k, 0.13*k), bev=0.003*k, segs=1)
# ---- shoulders: flush crystal cap fused directly onto the shoulder ball (single overlapping piece, square-edged) ----
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; sh, el, wr, hd = V(j["sh"]), V(j["el"]), V(j["wr"]), V(j["hd"])
    sph(f"{side}UpperArm", CRYST, tuple(sh + V((0, 0, 0.015*k))), 0.105*k, scale=(1.15, 1.1, 0.62), rot=(0.12, 0, 0), u=6, v=6)      # faceted cap, low poly = crystalline read
    sph(f"{side}UpperArm", GOLD, tuple(sh + V((-0.02*s*k, -0.075*k, 0.05*k))), 0.013*k, u=8, v=6)                                    # rivet
    fa = wr - el
    loft(f"{side}LowerArm", FRAME, [(fa.length*t, r*k, r*k, 2.6) for t, r in ((0.1, .06), (0.4, .072), (0.8, .066))], N=14, sub=1, M=_frame(el, fa))
    loft(f"{side}LowerArm", CRYST, [(fa.length*0.35, .076*k, .076*k, 2.6), (fa.length*0.55, .08*k, .08*k, 2.6), (fa.length*0.9, .07*k, .07*k, 2.6)], N=8, M=_frame(el, fa), sub=1)  # vambrace, part of the same taper
    loft(f"{side}LowerArm", GOLD, [(fa.length*0.16, .062*k, .062*k), (fa.length*0.22, .062*k, .062*k)], N=14, M=_frame(el, fa), cap=False)
    sph(f"{side}Hand", CRYST, tuple(hd), 0.1*k, scale=(1, 1, 1.05), u=10, v=8)
    for f in range(3):
        gem(f"{side}Hand", CRYST, tuple(hd + V((0.028*(f - 1)*k, -0.075*k, -0.015*k))), 0.022*k, 0.075*k, rot=(math.pi/2 + 0.3, 0, 0), sides=5)
    sph(f"{side}Hand", GOLD, tuple(hd + V((0, -0.095*k, 0.017*k))), 0.015*k, u=8, v=6)
# ---- legs: crystal greaves grown from the shin taper, gold ankle collar ----
    kn, an = V(j["kn"]), V(j["an"])
    lg = an - kn
    loft(f"{side}LowerLeg", FRAME, [(lg.length*t, r*k, r*k, 2.6) for t, r in ((0.08, .062), (0.4, .075), (0.85, .058))], N=14, sub=1, M=_frame(kn, lg))
    loft(f"{side}LowerLeg", CRYST, [(lg.length*0.3, .078*k, .078*k, 2.6), (lg.length*0.5, .082*k, .082*k, 2.6), (lg.length*0.85, .065*k, .065*k, 2.6)], N=8, M=_frame(kn, lg), sub=1)
    sph(f"{side}LowerLeg", GOLD, tuple(kn + V((0, -0.045*k, 0))), 0.06*k, scale=(1, 0.7, 1), u=14, v=10)
    tube(f"{side}Foot", GOLD, tuple(an + V((0, 0, 0.035*k))), (an.x, an.y - 0.035*k, 0.035*k), 0.055*k, 0.05*k, N=14, sub=1)
    sph(f"{side}Foot", CRYST, (an.x, an.y - 0.1*k, 0.04*k), 0.055*k, scale=(1, 1.5, 0.7), u=8, v=6)
add_bone("Weapon_R", tuple(V(J["Right"]["hd"]) + V((0, -0.02, 0))), tuple(V(J["Right"]["hd"]) + V((0, -0.2, 0))), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
