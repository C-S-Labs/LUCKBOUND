# LUCKBOUND - Sky Citadel BASIC enemy: Aviary Harrier (close range, flyer; comes from the Aviary).
# Circles, then dive-swoops; after the dive it LANDS and stalks on foot (pecks/rakes) for a few seconds - sword window -
# then takes off. Parry on the dive grounds it (Grounded-stagger). ~0.9 m tall standing, ~2.3 m wingspan.
# White plumage, slate wingtips, copper beak + talons, amber eyes.
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
exec(open(FW + r"\enemy_kit.py").read())
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
sph("Head", WHITE, (0, -0.3, BZ + 0.24), 0.075, scale=(0.85, 1.15, 0.9), u=16, v=10)
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
    pts = [(f"Wing{side}1", p0, p1, 4), (f"Wing{side}2", p1, p2, 5), (f"Wing{side}3", p2, p3, 6)]
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
# tail fan
for i in range(5):
    a = (i - 2)*0.22
    blade("Tail", WHITE if i % 2 else SLATE, (0, 0.28, BZ - 0.01), (math.sin(a), math.cos(a), -0.12), 0.34, 0.06, 0.012, hint=(0, 0, 1), N=6, sub=0)
# legs: feathered thighs, copper shanks, talons
for side, s in (("L", 1), ("R", -1)):
    h = Vector(BONES[BIDX[f"Leg{side}1"]][1]); kn = Vector(BONES[BIDX[f"Leg{side}1"]][2]); ft = Vector(BONES[BIDX[f"Leg{side}2"]][2])
    tube(f"Leg{side}1", WHITE, tuple(h), tuple(kn), 0.055, 0.035, N=10, sub=1)
    tube(f"Leg{side}2", COPPER, tuple(kn), tuple(ft), 0.018, 0.016, N=8)
    for dx, dy in ((0, -1), (0.6*s, -0.7), (-0.6*s, -0.7), (0, 1)):
        blade(f"Leg{side}2", COPPER, tuple(ft), (dx, dy, -0.35), 0.1, 0.018, 0.012, hint=(0, 0, 1), N=5, sub=0)
rig, PARTS = assemble(NAME, OFFSET)
