# LUCKBOUND - Ethereal Scape BASIC enemy: Meadow Stag (close range: charger, packs of two/three).
# v2 REFINE (2026-09-27, owner: v1 read as unrefined -- unreadable gold head blob, a halo it didn't need, and the
# silhouette didn't read "charger"). DESIGN INTENT: reads as a lean, low, forward-leaning charger -- long low
# body, head carried level with the shoulders (not lifted), antlers swept forward like a lowered lance, not a
# crown. Cloud-mint hide, a woven gold-and-teal chest harness (surface-projected like a real tack strap, not a
# floating collar), a crystal ANTLER SET swept forward -- the star piece, no metal on the head at all, a slate
# brow crest, notched ears, glow eyes, teal-wrapped fetlocks over crystal shins/hooves, a ridge of small crystal
# spines down the spine, teal ribbon tail. No halo. ~1.7 m at the shoulder, low-slung. Basic tier 10-15k. Faces -Y.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "MeadowStag"; OFFSET = (6.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
exec(open(FW + r"\character_kit.py").read())
MATS = [mat("MS_Hide", (0.82, 0.93, 0.87), 0.0, 0.3), mat("MS_Teal", (0.16, 0.52, 0.46), 0.0, 0.3),
        mat("MS_Gold", (0.87, 0.70, 0.38), 1.0, 0.18), mat("MS_Crystal", (0.6, 0.85, 0.97), 0.0, 0.05, (0.4, 0.75, 0.95), 0.4),
        mat("MS_Slate", (0.22, 0.24, 0.3), 0.3, 0.35), mat("MS_Glow", (0.8, 1.0, 0.9), 0, 0.2, (0.55, 1.0, 0.8), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
HIDE, TEAL, GOLD, CRYST, SLATE = 0, 1, 2, 3, 4
V = Vector
def limb(bone, m, a, b, rs, N=14, sub=0):
    a, b = V(a), V(b); d = b - a; n = d.length
    loft(bone, m, [(n*t, r0, r1) for t, r0, r1 in rs], N=N, M=_frame(a, d, hint=(1, 0, 0)), sub=sub)
# ---- skeleton: long low barrel, head carried LEVEL with the shoulders (charger stance, not a grazer) ----
RUMP, CHEST = V((0, 0.46, 0.92)), V((0, -0.4, 0.94))
add_bone("Root", (0, 0, 0.55), (0, 0, 0.85), None)
add_bone("Body", tuple(RUMP), tuple(CHEST), "Root")
NECK0, HEAD0 = V((0, -0.4, 1.02)), V((0, -0.68, 1.22))
add_bone("Neck", tuple(NECK0), tuple(HEAD0), "Body")
add_bone("Head", tuple(HEAD0), (0, -0.94, 1.28), "Neck")
add_bone("Tail", (0, 0.54, 0.98), (0, 0.7, 0.76), "Body")
LEGS = {}
for nm, x, y in (("FrontLeft", 0.12, -0.33), ("FrontRight", -0.12, -0.33), ("BackLeft", 0.12, 0.37), ("BackRight", -0.12, 0.37)):
    hip, knee, hoof = V((x, y, 0.88)), V((x, y + (0.04 if "Back" in nm else -0.02), 0.48)), V((x, y, 0.05))
    add_bone(nm + "Upper", tuple(hip), tuple(knee), "Body")
    add_bone(nm + "Lower", tuple(knee), tuple(hoof), nm + "Upper")
    LEGS[nm] = (hip, knee, hoof)
# ---- body: long low barrel, tapering to a lean chest -- forward-leaning mass ----
limb("Body", HIDE, RUMP + V((0, 0.12, 0)), CHEST - V((0, 0.16, 0)),
     [(0.0, .075, .075), (0.12, .16, .18), (0.4, .19, .21), (0.7, .185, .21), (0.9, .15, .18), (1.0, .07, .09)], N=32, sub=2)
# ---- neck: short and thick, level -- not a raised swan neck ----
limb("Neck", HIDE, NECK0 + V((0, 0.07, -0.04)), HEAD0, [(0.0, .12, .12), (0.5, .1, .1), (1.0, .085, .085)], N=24, sub=2)
# ---- chest + shoulder harness: a real strap surface-projected round the chest, gold buckle, teal underlay ----
T = body_bvh()
band = []
for i in range(21):
    a = i*2*math.pi/20
    p0 = (0.02*math.cos(a), CHEST.y + 0.02 + 0.15*math.sin(a), 1.0 + 0.09*math.cos(a))
    band.append(on_surface_in(T, p0, (0, CHEST.y + 0.02, 1.0), lift=0.006))
for a_, b_ in zip(band, band[1:]):
    loft("Body", TEAL, [(0, .022, .01), ((b_ - a_).length, .022, .01)], N=6, M=_frame(a_, b_ - a_))
for a_, b_ in zip(band, band[1:]):
    loft("Body", GOLD, [(0, .009, .004), ((b_ - a_).length, .009, .004)], N=6, M=_frame(a_ + V((0, 0, 0.006)), b_ - a_), cap=False)
box("Body", GOLD, tuple(V(band[10]) + V((0, 0, 0.01))), (0.03, 0.014, 0.022), bev=0.004, segs=1)   # buckle
# ---- head: hide skull only -- no metal mask; slate brow crest, notched ears, glow eyes ----
sph("Head", HIDE, tuple(HEAD0 + V((0, -0.09, -0.01))), 0.085, scale=(0.85, 1.4, 0.8), u=18, v=14)
sph("Head", HIDE, tuple(HEAD0 + V((0, -0.2, -0.04))), 0.048, scale=(0.85, 1.3, 0.65), u=14, v=10)   # muzzle, low and forward
for s in (1, -1):
    sph("Head", GLOW, tuple(HEAD0 + V((0.05*s, -0.12, 0.01))), 0.013, scale=(1.0, 0.5, 0.65), u=10, v=8)
    blade("Head", HIDE, tuple(HEAD0 + V((0.045*s, 0.02, 0.03))), (0.8*s, 0.2, 0.5), 0.095, 0.036, 0.011, hint=(0, 1, 0), N=6, sub=0)   # ear, swept back
    blade("Head", SLATE, tuple(HEAD0 + V((0.012*s, -0.1, 0.02))), (0.3*s, 1.0, 0.15), 0.045, 0.017, 0.006, hint=(0, 0, 1), N=5, sub=0)  # brow crest
PIECE = "Gear"   # crystal antlers: the star piece, own mesh
# ---- antlers SWEEP FORWARD like a lowered lance (charger read), not a tall crown: low base, long low tines ----
for s in (1, -1):
    a0 = HEAD0 + V((0.055*s, 0.0, 0.07)); a1 = V((0.18*s, -0.1, 1.55)); a2 = V((0.34*s, -0.42, 1.78))
    tube("Head", CRYST, tuple(a0), tuple(a1), 0.036, 0.025, N=12, sub=1)
    tube("Head", CRYST, tuple(a1), tuple(a2), 0.025, 0.014, N=12, sub=1)
    for ti, tt in enumerate((0.25, 0.52, 0.78)):                                     # tines fanning up and forward off the main beam
        base = a1.lerp(a2, tt); tip = base + V((0.1*s*(1 + tt*0.3), -0.18 - 0.04*ti, 0.18 - 0.03*ti))
        tube("Head", CRYST, tuple(base - (tip - base).normalized()*0.015), tuple(tip), 0.02 - 0.002*ti, 0.005, N=8)
    bt = a0.lerp(a1, 0.15); bttip = bt + V((0.1*s, -0.16, -0.02))
    tube("Head", CRYST, tuple(bt - (bttip - bt).normalized()*0.02), tuple(bttip), 0.024, 0.005, N=8)   # low brow tine, guarding the eye, forward-pointing
# ---- legs: hide thighs, gold-trimmed teal fetlock wraps, crystal shins + crystal hooves ----
for nm, (hip, knee, hoof) in LEGS.items():
    sph(nm + "Upper", HIDE, tuple(hip + V((0, 0, 0.02))), 0.095, scale=(0.8, 1.1, 1.1), u=14, v=10)
    limb(nm + "Upper", HIDE, hip, knee, [(0.0, .066, .075), (0.6, .047, .052), (1.0, .036, .038)], N=14, sub=1)
    limb(nm + "Lower", CRYST, knee, hoof + V((0, 0, 0.065)), [(0.0, .034, .034), (0.5, .026, .026), (1.0, .021, .021)], N=10)
    loft(nm + "Lower", TEAL, [(0.0, .037, .037), (0.045, .039, .039), (0.09, .037, .037)], N=10, M=_frame(knee, hoof - knee, hint=(1, 0, 0)))
    loft(nm + "Lower", GOLD, [(0.04, .0395, .0395), (0.05, .0395, .0395)], N=10, M=_frame(knee, hoof - knee, hint=(1, 0, 0)), cap=False)
    gem(nm + "Lower", CRYST, tuple(hoof + V((0, 0, 0.042))), 0.042, 0.048, rot=(math.pi, 0, 0), sides=6)
PIECE = "Body"
# ---- teal ribbon tail, glow tip ----
limb("Tail", TEAL, V((0, 0.54, 0.99)), V((0, 0.68, 0.78)), [(0.0, .048, .019), (1.0, .028, .011)], N=10)
limb("Tail", GLOW, V((0, 0.67, 0.8)), V((0, 0.72, 0.69)), [(0.0, .028, .011), (1.0, .003, .003)], N=8)
rig, PARTS = assemble(NAME, OFFSET)
