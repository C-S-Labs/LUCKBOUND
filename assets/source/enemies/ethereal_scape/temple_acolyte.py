# LUCKBOUND - Ethereal Scape BASIC enemy: Temple Acolyte (long range / support; caster).
# ES design language (see ROSTER.md): a slim temple-ivory votary mid-transfiguration. A smooth faceless GOLD MASK
# split by a portal-glow slit, a gold HALO ring behind the head, forearms and hands already turned to sky
# crystal, a robe hem breaking into crystal shards, and teal RIBBONS trailing off the shoulders.
# Chants a slow ranged bolt from a crystal orb (Chant bone, orbited by gold motes) before its chest; the chant
# BREAKS when the player closes in (punish window). ~1.9 m.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "TempleAcolyte"; OFFSET = (3.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read()); exec(open(FW + r"\character_kit.py").read())
MATS = [mat("TA_Cloud", (0.86, 0.95, 0.92), 0.0, 0.28), mat("TA_Teal", (0.16, 0.52, 0.46), 0.0, 0.3),
        mat("TA_Gold", (0.87, 0.70, 0.38), 1.0, 0.18), mat("TA_Crystal", (0.6, 0.85, 0.97), 0.0, 0.05, (0.4, 0.75, 0.95), 0.4),
        mat("TA_Indigo", (0.3, 0.32, 0.58), 0.0, 0.35), mat("TA_Glow", (0.8, 1.0, 0.9), 0, 0.2, (0.55, 1.0, 0.8), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
ROBE, TEAL, GOLD, CRYST, INDIGO = 0, 1, 2, 3, 4
J, k = make_humanoid(1.9, shoulder=0.17, hip=0.09, bulk=0.8, limb=0.9, m_body=ROBE, m_limb=ROBE, m_skin=GOLD, head=False)
Z = lambda z: z*k
V = Vector
# ---- slim column robe: narrow waist, straight fall, indigo under-layer showing at the hem ----
# v2 (2026-09-27, owner: build the split into the DESIGN, not as a rigging patch on a closed tube). TWO
# overlapping half-panels (front + back overlap so no gap shows at rest), each one rigged almost entirely to
# its own leg below the waist. No shared centreline vertices, so each panel is free to swing with its leg
# without fighting the other side -- and it's a real modelling seam, ready for cloth physics on each panel
# later, not a patched weight blend.
_ROBE_SECS = [(Z(1.12), .14*k, .1*k), (Z(0.95), .15*k, .12*k), (Z(0.55), .2*k, .17*k), (Z(0.22), .23*k, .2*k)]
_UNDER_SECS = [(Z(0.3), .175*k, .15*k), (Z(0.12), .165*k, .14*k)]
_OVERLAP = 0.22   # each panel reaches this far past the centreline (in x/rx units) so the slit doesn't gap at rest
def _panel_wfn(leg_bone):
    def wfn(co):
        t = min(1.0, max(0.0, (Z(1.05) - co.z) / (Z(1.05) - Z(0.14))))   # 0 at the waist, 1 at the hem
        torso_w = 1.0 - 0.9*t
        return {"LowerTorso": torso_w, leg_bone: 1.0 - torso_w}
    return wfn
for _side, _leg in (("Left", "LeftUpperLeg"), ("Right", "RightUpperLeg")):
    _sgn = 1 if _side == "Left" else -1
    _keep = (lambda s: (lambda c: s*c.x > -_OVERLAP*0.16*k))(_sgn)   # keep this side + a bit past centre (overlap)
    loft("LowerTorso", ROBE, _ROBE_SECS, N=24, sub=1, wfn=_panel_wfn(_leg), keep=_keep, fill=True)
    loft("LowerTorso", INDIGO, _UNDER_SECS, N=24, wfn=_panel_wfn(_leg), keep=_keep, fill=True)
loft("UpperTorso", ROBE, [(Z(1.12), .15*k, .11*k), (Z(1.36), .19*k, .12*k), (Z(1.5), .12*k, .1*k)], N=20, sub=1)
arc_band("LowerTorso", GOLD, (0, 0), Z(1.05), Z(1.0), (.15*k, .112*k), (.157*k, .118*k), 0, 2*math.pi, 0.012*k, 24)   # waist cord
# ---- transfiguration: the hem sheds sky-crystal shards, pointing down and out ----
for i in range(12):
    a = i*2*math.pi/12
    r = (0.165 + 0.02*(i % 2))*k
    gem("LowerTorso", CRYST, (r*math.cos(a), r*math.sin(a)*0.87, Z(0.16) - 0.03*(i % 3)*k), 0.028*k, (0.09 + 0.04*(i % 3))*k,
        rot=(0.35*math.sin(a), -0.35*math.cos(a), 0), sides=5)
# ---- head: smooth gold mask (no hood), vertical portal slit, gold halo ring behind ----
sph("Head", GOLD, (0, -0.005*k, Z(1.66)), 0.1*k, scale=(0.82, 0.9, 1.22), u=24, v=16)
box("Head", GLOW, (0, -0.093*k, Z(1.67)), (0.012*k, 0.012*k, 0.13*k), bev=0.004*k, segs=1)
tube("Head", ROBE, (0, 0, Z(1.5)), (0, 0, Z(1.56)), 0.05*k, 0.045*k, N=12)                                              # neck
hc = V((0, 0.13*k, Z(1.72)))
loft("Head", GOLD, [(-0.007*k, .16*k, .16*k), (0.007*k, .16*k, .16*k)], N=32, M=TR(tuple(hc), (math.pi/2, 0, 0)), cap=False)
tube("Head", GOLD, (0, 0.06*k, Z(1.66)), tuple(hc + V((0, 0, -0.16*k))), 0.012*k, 0.01*k, N=8)                        # stem: halo is mounted to the back of the head
for i in range(4):                                                                                                   # crystal points on the halo
    a = math.pi*(0.25 + 0.5*i/3)
    gem("Head", CRYST, (0.16*math.cos(a)*k, 0.13*k, Z(1.72) + 0.16*math.sin(a)*k), 0.012*k, 0.04*k, rot=(0, math.pi/2 - a, 0), sides=4)
# ---- shoulders: gold pauldron caps; teal ribbons trailing down the back, portal-glow tips ----
for side, s in (("Left", 1), ("Right", -1)):
    sph("UpperTorso", GOLD, (0.17*s*k, 0.0, Z(1.44)), 0.055*k, scale=(1.1, 1.0, 0.7), u=12, v=8)
    loft("UpperTorso", TEAL, [(Z(1.42), .035*k, .012*k, 2, 0.08*s*k, .1*k), (Z(1.0), .045*k, .012*k, 2, 0.09*s*k, .105*k),
                              (Z(0.55), .035*k, .012*k, 2, 0.1*s*k, .155*k)], N=10, sub=1)
    loft("UpperTorso", GLOW, [(Z(0.58), .033*k, .012*k, 2, 0.1*s*k, .155*k), (Z(0.4), .004*k, .004*k, 2, 0.1*s*k, .17*k)], N=8)
# ---- arms: ivory sleeves to the elbow, then crystal forearms + crystal-shard hands ----
    j = J[side]; el, wr, hd = V(j["el"]), V(j["wr"]), V(j["hd"])
    M = _frame(el, wr - el)
    loft(f"{side}LowerArm", ROBE, [(0, .055*k, .055*k), (0.08*k, .075*k, .075*k), (0.11*k, .08*k, .08*k)], N=16, M=M, cap=False)
    loft(f"{side}LowerArm", GOLD, [(0.1*k, .082*k, .082*k), (0.12*k, .082*k, .082*k)], N=16, M=M, cap=False)
    for t, rr in ((0.45, 0.05), (0.75, 0.042)):
        gem(f"{side}LowerArm", CRYST, tuple(el.lerp(wr, t)), rr*k, 0.14*k, rot=(0, 0, 0), sides=6)
    for f in range(3):
        d = (hd - wr).normalized()
        gem(f"{side}Hand", CRYST, tuple(hd + V((0.02*(f - 1)*k, -0.01*k, -0.03*k))), 0.014*k, 0.07*k, sides=4)
PIECE = "Gear"
for side in ("Left", "Right"):                                                                                     # gold ankle guards join shin to foot
    an = V(J[side]["an"])
    tube(f"{side}Foot", GOLD, tuple(an + V((0, 0, 0.03*k))), (an.x, an.y - 0.03*k, 0.035*k), 0.045*k, 0.04*k, N=12)
# ---- chant focus: a crystal orb before the chest, orbited by three gold motes (the chant tell) ----
cc = V((0, -0.19*k, Z(1.2)))   # set into a gold cradle on the sternum (nothing floats)
add_bone("Chant", tuple(cc), tuple(cc + V((0, -0.15*k, 0))), "UpperTorso")
sph("Chant", CRYST, tuple(cc), 0.06*k, u=16, v=10)
sph("Chant", GLOW, tuple(cc), 0.035*k, u=10, v=8)
loft("Chant", GOLD, [(-0.004*k, .1*k, .1*k), (0.004*k, .1*k, .1*k)], N=24, M=TR(tuple(cc), (0.4, 0, 0)), cap=False)
for i in range(3):
    a = i*2*math.pi/3
    sph("Chant", GOLD, tuple(cc + V((0.1*math.cos(a)*k, 0.1*math.sin(a)*math.cos(0.4)*k, 0.1*math.sin(a)*math.sin(0.4)*k))), 0.014*k, u=8, v=6)
rig, PARTS = assemble(NAME, (OFFSET[0], OFFSET[1], OFFSET[2] + 0.06))
