# LUCKBOUND - Sky Citadel BASIC enemy: Aviary Harrier (close range, flyer; comes from the Aviary).
# Circles, then dive-swoops; after the dive it LANDS and stalks on foot (pecks/rakes) for a few seconds - sword window -
# then takes off. Parry on the dive grounds it (Grounded-stagger). ~0.9 m tall standing, ~2.3 m wingspan.
# White plumage, slate wingtips, copper beak + talons, amber eyes.
# v2 character pass (2026-09-24): an ARMOURED war-raptor of the citadel aviary - copper helm-mask with swept crest,
# breast plate, plated wing leading edges, layered primaries with glowing veins, long streamer tail. Basic tier 10-12.5k.
# Rig: Root > Body > Neck > Head > Beak ; WingL/R 1-3 ; Tail ; LegL/R 1-2 + Talons.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "AviaryHarrier"; OFFSET = (25.0, 0.0, 0.0)
E = HERE
BZ = 0.52
BONES = [("Root", (0, 0.1, BZ - 0.15), (0, 0.1, BZ), None),
         ("Body", (0, 0.22, BZ), (0, -0.18, BZ + 0.06), "Root"),
         ("Neck", (0, -0.18, BZ + 0.06), (0, -0.26, BZ + 0.22), "Body"),
         ("Head", (0, -0.26, BZ + 0.22), (0, -0.40, BZ + 0.26), "Neck"),
         ("Beak", (0, -0.36, BZ + 0.25), (0, -0.48, BZ + 0.2), "Head"),
         ("Tail", (0, 0.22, BZ), (0, 0.55, BZ - 0.05), "Body")]
BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\character_kit.py").read())
WING = {}
for side, s in (("L", 1), ("R", -1)):
    p0 = Vector((0.1*s, -0.08, BZ + 0.08)); p1 = Vector((0.42*s, -0.02, BZ + 0.2)); p2 = Vector((0.78*s, 0.04, BZ + 0.18)); p3 = Vector((1.15*s, 0.12, BZ + 0.1))
    WING[side] = (p0, p1, p2, p3)
    BONES += [(f"Wing{side}1", tuple(p0), tuple(p1), "Body"), (f"Wing{side}2", tuple(p1), tuple(p2), f"Wing{side}1"),
              (f"Wing{side}3", tuple(p2), tuple(p3), f"Wing{side}2")]
    h = Vector((0.08*s, 0.02, BZ - 0.08)); kn = Vector((0.11*s, -0.05, 0.25)); ft = Vector((0.11*s, -0.02, 0.04))
    BONES += [(f"Leg{side}1", tuple(h), tuple(kn), "Body"), (f"Leg{side}2", tuple(kn), tuple(ft), f"Leg{side}1")]
BIDX.update({b[0]: i for i, b in enumerate(BONES)})
MATS = [mat("AH_White", (0.9, 0.9, 0.87), 0.0, 0.35), mat("AH_Slate", (0.12, 0.14, 0.19), 0.0, 0.3),
        mat("AH_Copper", (0.72, 0.38, 0.18), 1.0, 0.22), mat("AH_Cream", (0.85, 0.78, 0.62), 0.0, 0.35),
        mat("AH_Dark", (0.05, 0.05, 0.06), 0.3, 0.3), mat("AH_Glow", (1.0, 0.6, 0.1), 0, 0.3, (1.0, 0.55, 0.05), 2.5)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
WHITE, SLATE, COPPER, CREAM, DARK = 0, 1, 2, 3, 4
# body: teardrop along Y, cream breast
loft("Body", WHITE, [(-0.22, .04, .05), (-0.14, .13, .14), (0.02, .15, .15), (0.2, .11, .1), (0.32, .04, .04)], N=16,
     M=TR((0, 0, BZ), (-math.pi/2, 0, 0)), sub=1)
loft("Body", CREAM, [(-0.18, .08, .06, 2, 0, -.08), (0.0, .11, .07, 2, 0, -.1), (0.14, .07, .05, 2, 0, -.07)], N=12,
     M=TR((0, 0, BZ), (-math.pi/2, 0, 0)), sub=1)
# neck + head + hooked copper beak + amber eyes + slate crest
tube("Neck", WHITE, (0, -0.16, BZ + 0.06), (0, -0.25, BZ + 0.2), 0.07, 0.055, N=12, sub=1)
loft("Head", WHITE, [(0.0, .045, .05), (0.05, .062, .066), (0.11, .058, .06), (0.16, .036, .04), (0.19, .012, .014)], N=16,
     M=_frame(Vector((0, -0.2, BZ + 0.225)), Vector((0, -1, 0.12)), hint=(0, 0, 1)), sub=1)
loft("Beak", COPPER, [(0, .035, .045), (0.06, .026, .036), (0.1, .016, .024)], N=10,
     M=_frame(Vector((0, -0.365, BZ + 0.26)), Vector((0, -1, -0.15)), hint=(0, 0, 1)), sub=1)
loft("Beak", COPPER, [(0, .016, .024), (0.05, .008, .012), (0.075, .002, .003)], N=8,
     M=_frame(Vector((0, -0.46, BZ + 0.245)), Vector((0, -0.4, -1)), hint=(0, 0, 1)), sub=1)          # hooked tip
for s in (1, -1):
    sph("Head", DARK, (0.045*s, -0.34, BZ + 0.26), 0.018, u=10, v=6)
    sph("Head", GLOW, (0.05*s, -0.345, BZ + 0.262), 0.011, u=8, v=6)
    blade("Head", SLATE, (0.03*s, -0.26, BZ + 0.29), (0.25*s, 1.0, 0.35), 0.13, 0.02, 0.008, hint=(0, 0, 1), N=6, sub=0)
    blade("Head", SLATE, (0.012*s, -0.37, BZ + 0.285), (0.9*s, 0.5, -0.25), 0.075, 0.018, 0.01, hint=(0, 0, 1), N=6, sub=0)   # angry brow
# wings: arm bones + rows of feather blades (primaries slate-tipped)
for side, s in (("L", 1), ("R", -1)):
    p0, p1, p2, p3 = WING[side]
    tube(f"Wing{side}1", WHITE, tuple(p0), tuple(p1), 0.05, 0.04, N=10, sub=1)
    tube(f"Wing{side}2", WHITE, tuple(p1), tuple(p2), 0.04, 0.03, N=10, sub=1)
    tube(f"Wing{side}3", WHITE, tuple(p2), tuple(p3), 0.03, 0.015, N=8, sub=1)
    pts = [(f"Wing{side}1", p0, p1, 5), (f"Wing{side}2", p1, p2, 6), (f"Wing{side}3", p2, p3, 8)]
    for bn, a, b, n in pts:
        for i in range(n):
            t = (i + 0.5)/n
            root = a.lerp(b, t)
            outer = bn.endswith("3")
            L = (0.30 + 0.1*t) if not outer else (0.42 - 0.08*t)
            d = Vector((0.15*s if outer else 0.05*s, 1.0, -0.12))
            blade(bn, SLATE if outer else WHITE, tuple(root + Vector((0, 0.02, 0))), tuple(d), L, 0.06, 0.012, hint=(0, 0, 1), N=6, sub=0)
            if not outer:
                blade(bn, CREAM, tuple(root + Vector((0, 0.01, 0.015))), tuple(d), L*0.55, 0.05, 0.01, hint=(0, 0, 1), N=6, sub=0)   # coverts
# tail fan: 7 layered feathers + two long streamers with glowing tips
for i in range(7):
    a = (i - 3)*0.17
    blade("Tail", WHITE if i % 2 else SLATE, (0, 0.28, BZ - 0.01 + 0.004*(i % 2)), (math.sin(a), math.cos(a), -0.12), 0.36 + 0.04*(i % 2 == 0), 0.06, 0.012, hint=(0, 0, 1), N=6, sub=0)
for s in (1, -1):
    st = [Vector((0.03*s, 0.3, BZ - 0.02)) + Vector((0.07*s*t, 0.6*t, -0.1*t - 0.06*math.sin(math.pi*t))) for t in [i/6 for i in range(7)]]
    for a_, b_ in zip(st, st[1:]):
        blade("Tail", SLATE, tuple(a_), tuple(b_ - a_), (b_ - a_).length*1.1, 0.03, 0.008, hint=(0, 0, 1), N=5, sub=0)
    sph("Tail", GLOW, tuple(st[-1]), 0.018, scale=(1, 1.6, 0.6), u=10, v=6)
# legs: feathered thighs, copper shanks, talons
for side, s in (("L", 1), ("R", -1)):
    h = Vector(BONES[BIDX[f"Leg{side}1"]][1]); kn = Vector(BONES[BIDX[f"Leg{side}1"]][2]); ft = Vector(BONES[BIDX[f"Leg{side}2"]][2])
    tube(f"Leg{side}1", WHITE, tuple(h), tuple(kn), 0.055, 0.035, N=10, sub=1)
    tube(f"Leg{side}2", COPPER, tuple(kn), tuple(ft), 0.018, 0.016, N=8)
    for dx, dy in ((0, -1), (0.6*s, -0.7), (-0.6*s, -0.7), (0, 1)):
        blade(f"Leg{side}2", COPPER, tuple(ft), (dx, dy, -0.35), 0.1, 0.018, 0.012, hint=(0, 0, 1), N=5, sub=0)

# =============================== ARMOUR / CHARACTER ===============================
PIECE = "Armour"
# copper brow-mask: a swept visor plate over the eyes (angled down at the front = predatory), cheek plates, crest
for sd in (1, -1):
    blade("Head", COPPER, (0.028*sd, -0.35, BZ + 0.285), (0.35*sd, 1.0, 0.18), 0.16, 0.045, 0.01, hint=(-0.25*sd, 0.1, 1), N=8, sub=0)   # brow plate
for i, (dx, L_) in enumerate(((0.0, 0.2), (0.022, 0.16), (-0.022, 0.16))):                                        # crest swept back
    blade("Head", COPPER if i == 0 else SLATE, (dx, -0.3, BZ + 0.3), (dx*4, 1.0, 0.28), L_, 0.03, 0.007, hint=(0, -0.3, 1), N=8, sub=0)
# neck ruff: soft back-and-side collar only
for i in range(7):
    a = math.pi*(0.1 + 0.8*i/6)
    blade("Neck", WHITE if i % 2 else CREAM, (0.06*math.cos(a), -0.17 + 0.05*math.sin(a), BZ + 0.1), (math.cos(a)*0.4, 0.6*math.sin(a) + 0.3, -0.5),
          0.08, 0.04, 0.008, hint=(0, 0, 1), N=5, sub=0)
# breast shell: conforms to the body (same loft, 4% larger, front-lower region only) + copper studs + amber gem
loft("Body", WHITE, [(-0.22, .04*1.05, .05*1.05), (-0.14, .13*1.05, .14*1.05), (0.02, .15*1.05, .15*1.05), (0.2, .11*1.05, .1*1.05), (0.32, .04, .04)], N=16,
     M=TR((0, 0, BZ), (-math.pi/2, 0, 0)), sub=1, keep=lambda c: c.y < -0.06 and c.z < BZ + 0.06 and abs(c.x) < 0.12, fill=False, cap=False)
T = body_bvh()                                                     # copper rim lines hugging the breast shell
for sd in (1, -1):
    flow_line("Body", COPPER, [(0.02*sd, -0.2, BZ + 0.05), (0.08*sd, -0.16, BZ + 0.0), (0.11*sd, -0.08, BZ - 0.06), (0.1*sd, 0.0, BZ - 0.1)], r=0.006, T=T, centre=(0, -0.02, BZ))
gem("Body", GLOW, (0, -0.205, BZ - 0.02), 0.022, 0.016, rot=(math.pi/2 + 0.5, 0, 0), sides=6)
# wing leading-edge armour (copper-edged white plates) + glowing veins on the big primaries
for side, s in (("L", 1), ("R", -1)):
    p0, p1, p2, p3 = WING[side]
    for bn, a_, b_ in ((f"Wing{side}1", p0, p1), (f"Wing{side}2", p1, p2)):
        d_ = b_ - a_
        loft(bn, WHITE, [(0, .055, .03, 2.2), (d_.length*0.5, .05, .028, 2.2), (d_.length, .04, .022, 2.2)], N=12, M=_frame(a_ + Vector((0, -0.01, 0.012)), d_, hint=(0, 0, 1)), sub=1)
        tube(bn, COPPER, tuple(a_ + Vector((0, -0.045, 0.02))), tuple(b_ + Vector((0, -0.035, 0.018))), 0.008, 0.007, N=6)
    for i in (2, 4, 6):
        t = (i + 0.5)/8; root = p2.lerp(p3, t); d = Vector((0.15*s, 1.0, -0.12)).normalized(); L = 0.42 - 0.08*t
        tube(f"Wing{side}3", GLOW, tuple(root + Vector((0, 0.03, 0.012))), tuple(root + d*L*0.8 + Vector((0, 0, 0.012))), 0.0045, 0.003, N=5)
# talon gauntlets: copper bands + feathered thigh skirts
for side, s in (("L", 1), ("R", -1)):
    kn = Vector(BONES[BIDX[f"Leg{side}1"]][2]); ft = Vector(BONES[BIDX[f"Leg{side}2"]][2]); h = Vector(BONES[BIDX[f"Leg{side}1"]][1])
    for t in (0.2, 0.55):
        c_ = kn.lerp(ft, t)
        loft(f"Leg{side}2", COPPER, [(-0.012, .026, .026), (0.012, .026, .026)], N=10, M=_frame(c_, ft - kn))
    for i in range(4):
        a = (i - 1.5)*0.5
        blade(f"Leg{side}1", WHITE, tuple(h.lerp(kn, 0.35) + Vector((0.03*s*math.cos(a), -0.03*math.sin(a) - 0.02, 0))), (0.2*s*math.cos(a), -0.2*math.sin(a), -1), 0.14, 0.045, 0.008, hint=(0, 1, 0), N=5, sub=0)
PIECE = "Body"
rig, PARTS = assemble(NAME, OFFSET)
