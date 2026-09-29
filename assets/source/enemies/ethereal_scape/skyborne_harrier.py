# LUCKBOUND - Ethereal Scape BASIC enemy: Skyborne Harrier (close range, flyer: diver).
# v2 REFINE (2026-09-27, owner: v1's wings were bare tubes with a few stray blades -- nowhere near Sky Citadel's
# Aviary Harrier in density). DESIGN INTENT: reads as a FLYER first -- the wings are the largest silhouette
# element, layered with real feather ROWS (primaries + coverts, like Aviary Harrier's technique) fanning off both
# wing bones, cloud-white at the roots shading to sky-crystal-tipped primaries (transfiguration). Long crane neck,
# a long slim GOLD MASK beak split by a portal-glow slit, a crystal crest, twin teal ribbon tail streamers over a
# proper feathered tail fan, stilt legs ending in crystal talons. Dives, then LANDS and stalks on foot (sword
# range) before taking off again. No halo. ~1.55 m standing, ~2.4 m wingspan. Basic tier 10-15k. Faces -Y.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "SkyborneHarrier"; OFFSET = (12.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
MATS = [mat("SH_Hide", (0.84, 0.94, 0.88), 0.0, 0.3), mat("SH_Teal", (0.16, 0.52, 0.46), 0.0, 0.3),
        mat("SH_Gold", (0.87, 0.70, 0.38), 1.0, 0.18), mat("SH_Crystal", (0.6, 0.85, 0.97), 0.0, 0.05, (0.4, 0.75, 0.95), 0.4),
        mat("SH_Cream", (0.92, 0.95, 0.9), 0.0, 0.32), mat("SH_Glow", (0.8, 1.0, 0.9), 0, 0.2, (0.55, 1.0, 0.8), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
HIDE, TEAL, GOLD, CRYST, CREAM = 0, 1, 2, 3, 4
V = Vector
def limb(bone, m, a, b, rs, N=14, sub=0):
    a, b = V(a), V(b); d = b - a; n = d.length
    loft(bone, m, [(n*t, r0, r1) for t, r0, r1 in rs], N=N, M=_frame(a, d, hint=(1, 0, 0)), sub=sub)
# ---- skeleton ----
TAILP, CHEST = V((0, 0.32, 1.0)), V((0, -0.24, 1.1))
NECK0, HEAD0 = V((0, -0.2, 1.14)), V((0, -0.33, 1.5))
add_bone("Root", (0, 0, 0.6), (0, 0, 0.9), None)
add_bone("Body", tuple(TAILP), tuple(CHEST), "Root")
add_bone("Neck", tuple(NECK0), tuple(HEAD0), "Body")
add_bone("Head", tuple(HEAD0), (0, -0.62, 1.47), "Neck")
add_bone("Tail", (0, 0.36, 1.02), (0, 0.8, 0.86), "Body")
WING = {}
for side, s in (("Left", 1), ("Right", -1)):
    sh, wr, tip = V((0.12*s, -0.1, 1.16)), V((0.6*s, -0.04, 1.28)), V((1.2*s, 0.06, 1.18))
    add_bone(f"{side}Wing1", tuple(sh), tuple(wr), "Body"); add_bone(f"{side}Wing2", tuple(wr), tuple(tip), f"{side}Wing1")
    hip, kn, an = V((0.08*s, 0.1, 0.96)), V((0.09*s, 0.0, 0.56)), V((0.09*s, 0.1, 0.1))
    add_bone(f"{side}LegUpper", tuple(hip), tuple(kn), "Body"); add_bone(f"{side}LegLower", tuple(kn), tuple(an), f"{side}LegUpper")
    add_bone(f"{side}Foot", tuple(an), tuple(an + V((0, -0.14, -0.06))), f"{side}LegLower")
    WING[side] = (s, sh, wr, tip, hip, kn, an)
# ---- body + neck + head ----
limb("Body", HIDE, TAILP + V((0, 0.1, 0)), CHEST - V((0, 0.1, 0)), [(0.0, .05, .05), (0.2, .13, .14), (0.55, .15, .17), (0.85, .13, .15), (1.0, .06, .07)], N=28, sub=2)
limb("Neck", HIDE, NECK0 + V((0, 0.05, -0.04)), HEAD0 - V((0, 0, 0.02)), [(0.0, .08, .085), (0.5, .055, .06), (1.0, .05, .05)], N=18, sub=1)
arc_band("Neck", GOLD, (0, -0.212), 1.265, 1.245, (.068, .064), (.07, .066), 0, 2*math.pi, 0.012, 24)
sph("Head", HIDE, tuple(HEAD0), 0.07, scale=(0.9, 1.25, 0.9), u=18, v=12)
limb("Head", GOLD, HEAD0 + V((0, -0.03, 0)), V((0, -0.64, 1.46)), [(0.0, .06, .055), (0.25, .045, .04), (1.0, .004, .004)], N=16, sub=1)   # gold mask-beak
box("Head", GLOW, (0, -0.44, 1.528), (0.012, 0.14, 0.012), rot=(0.1, 0, 0), bev=0.004, segs=1)
PIECE = "Gear"
HC = V((0, -0.22, 1.6))
tube("Head", CRYST, tuple(HEAD0 + V((0, 0.0, 0.05))), tuple(HC + V((0, 0, 0.09))), 0.018, 0.01, N=8)   # crystal crest (no halo)
gem("Head", CRYST, tuple(HC + V((0, 0, 0.1))), 0.015, 0.05, sides=5)
# ---- wings: FEATHER ROWS off both wing bones -- primaries (crystal-tipped, outer row) + coverts (cream, inner row) ----
for side, (s, sh, wr, tip, hip, kn, an) in WING.items():
    limb(f"{side}Wing1", HIDE, sh, wr, [(0.0, .058, .05), (1.0, .038, .032)], N=12)
    limb(f"{side}Wing2", HIDE, wr, tip, [(0.0, .038, .032), (1.0, .012, .012)], N=10)
    sph(f"{side}Wing1", HIDE, tuple(wr), 0.04, u=12, v=8)
    n1 = 9   # primaries: long crystal-tipped feathers off the outer wing bone, fanning back and out
    for i in range(n1):
        t = i / (n1 - 1)
        root = wr.lerp(tip, t) + V((0, 0.015, 0))
        d = V((0.35*s*(0.4 + t), 1.0, -0.12 - 0.55*t)).normalized()
        L = 0.32 + 0.42*(1 - abs(t - 0.5)*0.6)
        blade(f"{side}Wing2", HIDE, tuple(root), tuple(d), L*0.62, 0.075, 0.01, hint=(0, 0, 1), N=6, sub=0)
        blade(f"{side}Wing2", CRYST, tuple(root + d*L*0.55), tuple(d), L*0.45, 0.06, 0.009, hint=(0, 0, 1), N=6, sub=0)
    n0 = 7   # coverts: shorter cream feathers layered over the inner wing bone
    for i in range(n0):
        t = i / (n0 - 1)
        root = sh.lerp(wr, t) + V((0, 0.012, 0.01))
        d = V((0.25*s*(0.5 + t*0.5), 1.0, -0.2)).normalized()
        blade(f"{side}Wing1", CREAM, tuple(root), tuple(d), 0.24 + 0.1*t, 0.09, 0.011, hint=(0, 0, 1), N=6, sub=0)
    gold_r = wr + V((0.02*s, -0.01, -0.02))
    sph(f"{side}Wing1", GOLD, tuple(gold_r), 0.02, u=8, v=6)                                            # small gold wrist band-clasp
# ---- tail: a real feather fan (5 layered blades) + twin teal ribbon streamers, glow tips ----
for i in range(5):
    a = (i - 2)*0.22
    d = V((math.sin(a)*0.4, 1.0, -0.05))
    blade("Tail", CREAM if i % 2 else HIDE, (0.02*(i - 2), 0.34, 1.03), tuple(d), 0.3 - 0.02*abs(i - 2), 0.07, 0.011, hint=(0, 0, 1), N=6, sub=0)
for s in (1, -1):
    limb("Tail", TEAL, V((0.02*s, 0.36, 1.02)), V((0.1*s, 0.78, 0.9)), [(0.0, .05, .014), (1.0, .03, .01)], N=10)
    limb("Tail", GLOW, V((0.098*s, 0.77, 0.902)), V((0.12*s, 0.88, 0.86)), [(0.0, .03, .01), (1.0, .003, .003)], N=8)
# ---- stilt legs: hide thigh, crystal shin, gold ankle band, three crystal talons + a rear spur ----
for side, (s, sh, wr, tip, hip, kn, an) in WING.items():
    limb(f"{side}LegUpper", HIDE, hip + V((0, 0, 0.04)), kn, [(0.0, .06, .06), (0.6, .04, .04), (1.0, .028, .028)], N=12)
    sph(f"{side}LegUpper", HIDE, tuple(kn), 0.03, u=10, v=8)
    limb(f"{side}LegLower", CRYST, kn, an, [(0.0, .024, .024), (1.0, .02, .02)], N=8)
    loft(f"{side}LegLower", GOLD, [(-0.012, .026, .026), (0.012, .026, .026)], N=12, M=_frame(an + V((0, -0.005, 0.03)), an - kn, hint=(1, 0, 0)), cap=False)
    sph(f"{side}Foot", CRYST, tuple(an), 0.03, u=10, v=8)
    for a in (-0.45, 0.0, 0.45):
        d = V((math.sin(a), -math.cos(a), 0))
        tube(f"{side}Foot", CRYST, tuple(an), tuple(an + d*0.12 + V((0, 0, -0.09))), 0.018, 0.004, N=6)
    tube(f"{side}Foot", CRYST, tuple(an), tuple(an + V((0, 0.08, -0.09))), 0.015, 0.004, N=6)
rig, PARTS = assemble(NAME, OFFSET)
