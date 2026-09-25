# LUCKBOUND - Sky Citadel BASIC enemy: Rootbound Warden (close range, heavy; Sky-Tree Grove + gardens).
# A treant grown around old citadel masonry. Root slam (ground ring), grab-and-pull, slow heavy walk.
# Bark brown, moss green, pink blossoms (flat leaf/blossom cards to save tris), warm amber sap-glow in the chest hollow.
# ~2.5 m, hunched. Rig: humanoid + 3 branch bones on the crown (sway).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "RootboundWarden"; OFFSET = (40.0, 0.0, 0.025)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("RW_Bark", (0.28, 0.19, 0.12), 0.0, 0.55), mat("RW_Moss", (0.25, 0.42, 0.18), 0.0, 0.6),
        mat("RW_Stone", (0.66, 0.64, 0.6), 0.0, 0.4), mat("RW_Blossom", (0.95, 0.62, 0.72), 0.0, 0.45),
        mat("RW_BarkDark", (0.14, 0.09, 0.06), 0.0, 0.6), mat("RW_Glow", (1.0, 0.6, 0.15), 0, 0.3, (1.0, 0.55, 0.1), 2.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BARK, MOSS, STONE, BLOSSOM, DARK = 0, 1, 2, 3, 4
J, k = make_humanoid(2.5, shoulder=0.26, hip=0.13, bulk=1.45, limb=1.9, m_body=BARK, m_limb=BARK, m_skin=DARK, head=False, hands=False,
                     torso_secs=[(1.08, .15, .12), (1.24, .19, .15), (1.38, .23, .16), (1.48, .2, .14), (1.55, .1, .09)])
Z = lambda z: z*k
# hunched head: stone mask set in bark, glowing eye knots
sph("Head", BARK, (0, -0.04*k, Z(1.6)), 0.12*k, scale=(1.0, 1.0, 0.9), u=12, v=8)
loft("Head", STONE, [(Z(1.54), .08*k, .03*k, 2, 0, -.1*k), (Z(1.64), .09*k, .035*k, 2, 0, -.115*k), (Z(1.7), .07*k, .03*k, 2, 0, -.1*k)], N=10, sub=1)
for s in (1, -1):
    sph("Head", GLOW, (0.04*s*k, -0.155*k, Z(1.63)), 0.016*k, u=8, v=6)
# bark ridges on torso, sap hollow in the chest, moss on shoulders
for i in range(6):
    a = -math.pi/2 + (i - 2.5)*0.35
    tube("UpperTorso", DARK, (0.24*k*math.cos(a), 0.17*k*math.sin(a), Z(1.1)), (0.26*k*math.cos(a), 0.18*k*math.sin(a), Z(1.5)), 0.02*k, 0.012*k, N=6)
sph("UpperTorso", DARK, (0, -0.17*k, Z(1.34)), 0.07*k, scale=(1, 0.5, 1.2), u=12, v=8)
sph("UpperTorso", GLOW, (0, -0.19*k, Z(1.34)), 0.04*k, scale=(1, 0.6, 1.2), u=10, v=8)
for s in (1, -1):
    sph("UpperTorso", MOSS, (0.2*s*k, 0.0, Z(1.5)), 0.1*k, scale=(1.3, 1.1, 0.5), u=12, v=8)
# root hands (club fists of roots) + root feet spreading on the ground
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]
    w = Vector(j["wr"])
    sph(f"{side}Hand", BARK, tuple(w + Vector((0, 0, -0.05*k))), 0.09*k, u=10, v=8)
    for f in range(4):
        a = f*math.pi/2 + 0.4
        tube(f"{side}Hand", DARK, tuple(w + Vector((0, 0, -0.08*k))), tuple(w + Vector((0.08*math.cos(a)*k, 0.08*math.sin(a)*k, -0.24*k))), 0.03*k, 0.008, N=6)
    an = Vector(j["an"])
    for f in range(5):
        a = -math.pi/2 + (f - 2)*0.55
        tube(f"{side}Foot", DARK, tuple(an + Vector((0, 0, 0.02))), tuple(an + Vector((0.2*math.cos(a)*k, 0.2*math.sin(a)*k, -0.07))), 0.035*k, 0.01, N=6)
# crown: three branches with blossom + leaf cards
for i, (a, L) in enumerate(((0.5, 0.55), (-0.3, 0.6), (1.4, 0.45))):
    bn = f"Branch{i+1}"
    base = Vector((0.1*math.cos(a)*k, 0.08*k, Z(1.52)))
    tip = base + Vector((0.35*math.cos(a), 0.25, 1.0)).normalized()*L*k
    add_bone(bn, base, tip, "UpperTorso")
    tube(bn, BARK, tuple(base), tuple(tip), 0.045*k, 0.012*k, N=8)
    for c in range(7):
        t = 0.45 + c*0.08
        p = base.lerp(tip, t) + Vector((math.sin(c*2.3)*0.08, math.cos(c*1.7)*0.08, math.sin(c)*0.05))*k
        blade(bn, BLOSSOM if c % 3 == 0 else MOSS, tuple(p), (math.sin(c*1.3), math.cos(c*2.1), 0.6), 0.14*k, 0.07*k, 0.006, hint=(0, 0, 1), N=4, sub=0)
exec(open(FW + r"\character_kit.py").read())
# ---- v2 character pass (2026-09-24), moveset-driven: ROOT SLAM + GRAB ----
# masonry fists (the slam weapon: old citadel stone the tree grew around), root tendrils coiling down the forearms and
# off the heels into the ground, moss drapes, blossom clusters, amber sap cracks glowing through the chest.
PIECE = "Growth"
T = body_bvh()
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; wr = Vector(j["wr"]); hd = Vector(j["hd"]); el = Vector(j["el"])
    fc = wr + (hd - wr)*0.25 + Vector((0, 0, -0.03*k))
    box(f"{side}Hand", STONE, tuple(fc), (0.17*k, 0.15*k, 0.17*k), rot=(0.1, 0.15*s, 0.2*s), bev=0.02*k, segs=2)      # masonry fist
    box(f"{side}Hand", DARK, tuple(fc + Vector((0, -0.075*k, 0))), (0.13*k, 0.01*k, 0.02*k), rot=(0.1, 0.15*s, 0.2*s), bev=0.004*k, segs=1)
    for t in range(3):                                                       # roots coiling down the forearm onto the fist
        a0 = t*2.1
        pts_ = [el.lerp(fc, u) + Vector((0.06*k*math.cos(a0 + u*4), 0.06*k*math.sin(a0 + u*4), 0)) for u in [i/6 for i in range(7)]]
        flow_line_in(f"{side}LowerArm", BARK, pts_, r=0.016*k, T=T, centre=None) if False else None
        for a_, b_ in zip(pts_, pts_[1:]): tube(f"{side}LowerArm", DARK, tuple(a_), tuple(b_), 0.014*k, 0.012*k, N=6)
    an = Vector(j["an"])
    for t in range(3):                                                       # heel roots into the ground
        a0 = math.pi/2 + (t - 1)*0.7
        p0 = an + Vector((0, 0.03*k, 0.05*k)); p1 = an + Vector((0.12*k*math.cos(a0)*s, 0.14*k*math.sin(a0), -0.01*k))
        tube(f"{side}Foot", DARK, tuple(p0), tuple(p1), 0.025*k, 0.008*k, N=6)
    sh = Vector(j["sh"])
    for m in range(5):                                                       # moss drape over the shoulder
        a0 = (m - 2)*0.35
        blade(f"{side}UpperArm", MOSS, tuple(sh + Vector((0.02*s*k, 0.06*k*math.sin(a0), 0.08*k))), (0.5*s, 0.3*math.sin(a0), -1), 0.2*k, 0.06*k, 0.01*k, hint=(0, 1, 0), N=5, sub=0)
    for m in range(4):                                                       # blossom cluster
        sph(f"{side}UpperArm", BLOSSOM, tuple(sh + Vector((0.05*s*k + 0.03*math.cos(m*1.6)*k, 0.03*math.sin(m*1.6)*k, 0.12*k))), 0.03*k, u=8, v=6)
for s in (1, -1):                                                            # amber sap cracks on the chest
    flow_line_in("UpperTorso", GLOW, [(0.02*s*k, -0.2*k, Z(1.36)), (0.08*s*k, -0.2*k, Z(1.3)), (0.1*s*k, -0.19*k, Z(1.2)), (0.15*s*k, -0.16*k, Z(1.14))], r=0.008*k, T=T, centre=(0, 0, Z(1.28)))
PIECE = "Body"
rig, PARTS = assemble(NAME, OFFSET)
