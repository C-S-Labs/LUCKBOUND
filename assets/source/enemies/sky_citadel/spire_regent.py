# LUCKBOUND - Sky Citadel BOSS: The Spire Regent (Boss Clearing) - v2 high-detail rebuild.
# A towering marble guardian bound to the central spire; hovers on layered marble drapery (no legs).
# 3 phases: P1 hand slams + shard volley; P2 (<60%) crown ignites, shards form a rotating wall, arena aether lines;
# P3 (<25%) marble cracks (violet core + crack network glow), halo slam shockwave, floor-chunk throw.
# White marble + gold filigree; violet aether only in gems, eyes, core, cracks. ~6.5 m. Shards stuck in the floor stay
# hittable. Pieces < 10k tris each; full rig incl. fingers.
import bpy, bmesh, math, random
from mathutils import Matrix, Euler, Vector
NAME = "SpireRegent"; OFFSET = (88.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Torso"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read()); exec(open(FW + r"\humanoid.py").read())
MATS = [mat("SR_Marble", (0.92, 0.9, 0.87), 0.0, 0.14), mat("SR_Gold", (0.84, 0.62, 0.22), 1.0, 0.16),
        mat("SR_Slate", (0.14, 0.14, 0.18), 0.4, 0.3), mat("SR_Veil", (0.8, 0.82, 0.88), 0.0, 0.22),
        mat("SR_Crack", (0.22, 0.08, 0.32), 0.0, 0.3), mat("SR_Glow", (0.55, 0.25, 1.0), 0, 0.3, (0.55, 0.22, 1.0), 1.6),
        mat("SR_MarbleWarm", (0.86, 0.82, 0.76), 0.0, 0.18), mat("SR_Void", (0.02, 0.015, 0.04), 0.0, 0.6),
        mat("SR_Light", (0.95, 0.9, 1.0), 0, 0.3, (0.95, 0.88, 1.0), 6.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
MARBLE, GOLD, SLATE, VEIL, CRACK, WARM, VOID, LIGHT = 0, 1, 2, 3, 4, 6, 7, 8
rnd = random.Random(11)
J, k = make_humanoid(6.5, shoulder=0.24, hip=0.12, bulk=1.2, limb=1.15, m_body=MARBLE, m_limb=MARBLE, m_skin=MARBLE, head=False, fingers=True)
Z = lambda z: z*k
PIECES.clear(); PARTLOG.clear()      # rebuild every surface below with boss-level detail (the bones stay)

# ======================= TORSO: sculpted cuirass, abdominal relief, gold filigree, core, P3 crack network =================
PIECE = "Torso"
loft("UpperTorso", MARBLE, [(Z(1.1), .15*k, .11*k, 2.4), (Z(1.2), .17*k, .12*k, 2.4, 0, -.005*k), (Z(1.3), .2*k, .13*k, 2.5, 0, -.01*k),
                            (Z(1.4), .235*k, .14*k, 2.6), (Z(1.47), .215*k, .125*k, 2.8), (Z(1.53), .1*k, .085*k)], N=36, sub=1)
loft("UpperTorso", MARBLE, [(Z(1.3), .04*k, .01*k, 2, 0, -.118*k), (Z(1.36), .15*k, .02*k, 2, 0, -.128*k), (Z(1.43), .17*k, .02*k, 2, 0, -.126*k),
                            (Z(1.47), .12*k, .012*k, 2, 0, -.118*k)], N=20, sub=1)                                         # pectorals
for r_ in range(3):                                                                                                         # abdominal plates
    for s in (1, -1):
        box("UpperTorso", MARBLE, (0.04*s*k, -.122*k, Z(1.14 + r_*0.05)), (0.07*k, 0.03*k, 0.04*k), bev=0.012*k, segs=2)
# gold filigree: collar, breastplate edge, scrolls, sunburst around the core
arc_band("UpperTorso", GOLD, (0, 0), Z(1.49), Z(1.535), (.2*k, .125*k), (.12*k, .1*k), 0, 2*math.pi, 0.03, 40)
for i in range(16):
    a = i*2*math.pi/16
    blade("UpperTorso", GOLD, (0.16*k*math.cos(a), 0.11*k*math.sin(a), Z(1.51)), (math.cos(a), math.sin(a)*0.7, -0.35), 0.05*k, 0.012*k, 0.004*k, hint=(0, 0, 1), N=4, sub=0)
for s in (1, -1):
    for c_ in range(4):                                                                                                     # spiral scrolls
        cc = Vector((0.09*s*k, -0.152*k, Z(1.4 - c_*0.055)))
        sp_ = [cc + Vector((0.018*k*(1 - u)*math.cos(u*9)*s, -0.002*k, 0.018*k*(1 - u)*math.sin(u*9))) for u in [i/10 for i in range(11)]]
        for a_, b_ in zip(sp_, sp_[1:]):
            tube("UpperTorso", GOLD, tuple(a_), tuple(b_), 0.003*k, 0.003*k, N=4)
core_c = Vector((0, -.152*k, Z(1.34)))
loft("UpperTorso", GOLD, [(0, .05*k, .05*k), (0.012*k, .052*k, .052*k), (0.018*k, .038*k, .038*k)], N=24, M=TR(tuple(core_c), (math.pi/2, 0, 0)))
for i in range(12):
    a = i*math.pi/6
    blade("UpperTorso", GOLD, tuple(core_c + Vector((0.05*k*math.cos(a), -0.004*k, 0.05*k*math.sin(a)))), (math.cos(a), -0.1, math.sin(a)),
          (0.04 if i % 2 else 0.065)*k, 0.012*k, 0.004*k, hint=(0, 1, 0), N=4, sub=0)
gem("UpperTorso", GLOW, tuple(core_c + Vector((0, -0.012*k, 0))), 0.034*k, 0.03*k, rot=(math.pi/2, 0, 0), sides=8)
# P3 crack network: seams raycast onto the cuirass so they lie in the surface (brighten in Studio when P3 triggers)
from mathutils.bvhtree import BVHTree
_tor = BVHTree.FromBMesh(PIECES["Torso"])
def on_torso(x, z):
    hit, nrm, _, _ = _tor.ray_cast(Vector((x, -2.0*k, z)), Vector((0, 1, 0)))
    return (hit, nrm) if hit is not None else (None, None)
for i in range(10):
    a = i*2*math.pi/10 + rnd.random()*0.3
    x, z = core_c.x + 0.055*k*math.cos(a), core_c.z + 0.055*k*math.sin(a)
    prev, _ = on_torso(x, z)
    for sgi in range(5):
        a += (rnd.random() - 0.5)*0.9
        x += 0.03*k*math.cos(a); z += 0.03*k*math.sin(a)
        hp_, np_ = on_torso(x, z)
        if prev is None or hp_ is None: break
        tube("UpperTorso", CRACK, tuple(prev + np_*0.002*k), tuple(hp_ + np_*0.002*k), 0.0045*k*(1 - sgi*0.15), 0.0035*k*(1 - sgi*0.15), N=4)
        prev = hp_
# ======================= HEAD: no face - a deep marble cowl holding a void of violet light, two white star-points ======
PIECE = "Head"
cowl = [(Z(1.47), .17*k, .15*k, 2.2, 0, .01*k), (Z(1.55), .135*k, .135*k, 2.2, 0, -.005*k), (Z(1.66), .128*k, .14*k, 2.2, 0, -.012*k),
        (Z(1.75), .115*k, .13*k, 2.2, 0, -.005*k), (Z(1.82), .07*k, .09*k, 2.2, 0, .01*k), (Z(1.85), .015*k, .03*k, 2, 0, .02*k)]
loft("Head", VEIL, cowl, N=36, sub=1, cap=False, keep=lambda c: not (c.y < -0.05*k and (c.x/(0.1*k))**2 + ((c.z - Z(1.66))/(0.108*k))**2 < 1.0), fill=False)
loft("Head", VOID, [(z, rx*0.9, ry*0.9, n, ox, oy) for z, rx, ry, n, ox, oy in cowl[:-1]], N=28, keep=lambda c: c.y > -0.02*k, fill=False)   # dark back wall
sph("Head", VOID, (0, 0.02*k, Z(1.64)), 0.105*k, scale=(1.05, 0.95, 1.6), u=20, v=12)                                        # void core (hides the neck)
arc_band("Head", GOLD, (0, -0.005*k), Z(1.765), Z(1.555), (.1*k, .133*k), (.1*k, .133*k), -math.pi/2 - 0.62, -math.pi/2 + 0.62, 0.008*k, 18) if False else None
loft("Head", GLOW, [(Z(1.57), .004*k, .004*k), (Z(1.61), .03*k, .026*k), (Z(1.66), .038*k, .032*k), (Z(1.72), .022*k, .02*k), (Z(1.77), .003*k, .003*k)],
     N=16, M=TR((0, -0.07*k, 0)), sub=1)                                                                                   # violet wisp-flame, no features
for i in range(9):                                                                                                       # motes drifting in the void
    a = i*2.4
    gem("Head", GLOW, (0.06*k*math.cos(a), -0.06*k + 0.02*k*math.sin(a), Z(1.6 + 0.02*i)), 0.005*k, 0.007*k, sides=4)
rnd2 = random.Random(3)
for i in range(7):                                                                                                        # drifting motes
    a = rnd2.random()*math.pi*2
    gem("Head", LIGHT if i % 3 == 0 else GLOW, (0.16*k*math.cos(a), 0.16*k*math.sin(a) - 0.02*k, Z(1.6 + rnd2.random()*0.25)), 0.007*k, 0.01*k, sides=4)
# marble veil falling from the cowl to the shoulders, gold edge
veil = [(Z(1.62), .14*k, .15*k), (Z(1.54), .16*k, .15*k), (Z(1.47), .19*k, .15*k)]
loft("Head", VEIL, [(z, rx, ry, 2, 0, .015*k) for z, rx, ry in veil], N=28, keep=lambda c: c.y > 0.0, fill=False, sub=1, cap=False)
arc_band("Head", GOLD, (0, 0.015*k), Z(1.47), Z(1.462), (.192*k, .152*k), (.194*k, .154*k), -0.1, math.pi + 0.1, 0.01, 20)
arc_band("Head", GOLD, (0, -0.005*k), Z(1.742), Z(1.762), (.121*k, .136*k), (.119*k, .134*k), 0, 2*math.pi, 0.012*k, 36)       # circlet on the cowl

# ======================= CROWN: two tiers, jewelled; ignites in P2 =======================================================
PIECE = "Crown"
add_bone("Crown", (0, 0, Z(1.75)), (0, 0, Z(1.95)), "Head")
for tier, (rz, L, n_, rr) in enumerate(((1.765, 0.22, 11, 0.118), (1.8, 0.14, 11, 0.09))):
    for i in range(n_):
        a = i*2*math.pi/n_ + tier*math.pi/n_
        Lx = (L if i % 2 == 0 else L*0.6)*k
        blade("Crown", GOLD, (rr*k*math.cos(a), rr*k*1.1*math.sin(a), Z(rz)), (0.3*math.cos(a), 0.3*math.sin(a), 1), Lx, 0.03*k, 0.01*k, hint=(0, 0, 1), N=6)
        if i % 2 == 0:
            gem("Crown", GLOW, (rr*k*1.02*math.cos(a), rr*k*1.12*math.sin(a), Z(rz + 0.04)), 0.011*k, 0.012*k, rot=(math.pi/2, 0, a + math.pi/2), sides=4)
    arc_band("Crown", GOLD, (0, 0), Z(rz - 0.005), Z(rz + 0.015), (rr*k*1.01, rr*k*1.12), (rr*k*1.0, rr*k*1.1), 0, 2*math.pi, 0.01*k, 36)
gem("Crown", GLOW, (0, -0.138*k, Z(1.79)), 0.022*k, 0.03*k, rot=(math.pi/2, 0, 0), sides=6)

# ======================= HALO: double ring, spokes, rune plates ============================================================
PIECE = "Halo"
add_bone("Halo", (0, 0.2*k, Z(1.7)), (0, 0.28*k, Z(1.7)), "Head")
def torus(bone, mi, R_, r_, M, seg=64, rs=8):
    tb = bmesh.new()
    rg = [[tb.verts.new(((R_ + r_*math.cos(b))*math.cos(a), (R_ + r_*math.cos(b))*math.sin(a), r_*math.sin(b))) for b in [2*math.pi*j/rs for j in range(rs)]]
          for a in [2*math.pi*i/seg for i in range(seg)]]
    for i in range(seg):
        for j in range(rs):
            tb.faces.new((rg[i][j], rg[(i+1) % seg][j], rg[(i+1) % seg][(j+1) % rs], rg[i][(j+1) % rs]))
    _add(tb, bone, mi, M)
MH = TR((0, 0.2*k, Z(1.7)), (math.pi/2, 0, 0))
torus("Halo", GOLD, 0.27*k, 0.012*k, MH); torus("Halo", GOLD, 0.21*k, 0.007*k, MH)
torus("Halo", GLOW, 0.24*k, 0.004*k, MH, seg=64, rs=6)
for i in range(24):
    a = i*math.pi/12
    c_ = MH @ Vector((0.27*k*math.cos(a), 0.27*k*math.sin(a), 0))
    blade("Halo", GOLD, tuple(c_), tuple(MH.to_3x3() @ Vector((math.cos(a), math.sin(a), 0))), (0.09 if i % 2 == 0 else 0.05)*k, 0.018*k, 0.006*k,
          hint=tuple(MH.to_3x3() @ Vector((0, 0, 1))), N=4, sub=0)
    if i % 3 == 0:
        tube("Halo", GOLD, tuple(MH @ Vector((0.21*k*math.cos(a), 0.21*k*math.sin(a), 0))), tuple(c_), 0.004*k, 0.004*k, N=4)
        box("Halo", MARBLE, None, (0.03*k, 0.02*k, 0.008*k), bev=0.002*k, segs=1, M=MH @ Matrix.Translation((0.24*k*math.cos(a + 0.13), 0.24*k*math.sin(a + 0.13), 0)) @ Matrix.Rotation(a, 4, 'Z'))

# ======================= ARMS: layered pauldrons, engraved bracers, rings, bigger hands, fingers =========================
PIECE = "Arms"
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side]; PIECE = "Arm" + side
    cx = j["sh"][0]*1.08; out = 0.0 if s > 0 else math.pi
    sph(f"{side}UpperArm", MARBLE, (cx, 0, j["sh"][2] + 0.03*k), 0.11*k, scale=(1.1, 1.05, 0.75), cut_below=-0.2, u=28, v=14)
    arc_band(f"{side}UpperArm", GOLD, (cx, 0), j["sh"][2] + 0.013*k, j["sh"][2] + 0.005*k, (.119*k, .114*k), (.121*k, .116*k), 0, 2*math.pi, 0.01*k, 32)
    for lam, (z0, z1, r0, r1) in enumerate(((0.01, -0.07, .1, .13), (-0.05, -0.13, .11, .14))):
        arc_band(f"{side}UpperArm", MARBLE, (j["sh"][0], 0), j["sh"][2] + z0*k, j["sh"][2] + z1*k, (r0*k, r0*k*0.95), (r1*k, r1*k*0.95), out - 1.7, out + 1.7, 0.012*k, 24)
        arc_band(f"{side}UpperArm", GOLD, (j["sh"][0], 0), j["sh"][2] + z1*k + 0.006*k, j["sh"][2] + z1*k - 0.002*k, (r1*k, r1*k*0.95), (r1*k + 0.004*k, r1*k*0.95 + 0.004*k), out - 1.7, out + 1.7, 0.008*k, 24)
    gem(f"{side}UpperArm", GLOW, (j["sh"][0]*1.08 + 0.02*s*k, -0.09*k, j["sh"][2] + 0.04*k), 0.02*k, 0.02*k, rot=(math.pi/2, 0, 0), sides=6)
    for bn, a, b, r0, r1 in ((f"{side}UpperArm", "sh", "el", .06, .05), (f"{side}LowerArm", "el", "wr", .052, .042)):
        A, B_ = Vector(j[a]), Vector(j[b])
        loft(bn, MARBLE, [(0, r0*k, r0*k), ((B_ - A).length*0.5, r0*k*1.04, r0*k*1.04), ((B_ - A).length, r1*k, r1*k)], N=20, M=_frame(A, B_ - A), cap=False, sub=1)
        sph(bn, MARBLE, tuple(A), r0*k*1.05, u=16, v=10)
    A, B_ = Vector(j["el"]), Vector(j["wr"]); Mb = _frame(A, B_ - A)
    loft(f"{side}LowerArm", GOLD, [(0.2*k, .058*k, .058*k, 2.4), (0.24*k, .061*k, .061*k, 2.4), (0.36*k, .052*k, .052*k, 2.4), (0.38*k, .049*k, .049*k, 2.4)], N=20, M=Mb)
    for e in range(8):
        a_ = e*math.pi/4
        tube(f"{side}LowerArm", GOLD, tuple(Mb @ Vector((0.062*k*math.cos(a_), 0.062*k*math.sin(a_), 0.24*k))), tuple(Mb @ Vector((0.055*k*math.cos(a_ + 0.3), 0.055*k*math.sin(a_ + 0.3), 0.35*k))), 0.003*k, 0.003*k, N=4)
    sph(f"{side}Hand", MARBLE, j["wr"], 0.05*k, u=14, v=10)
    box(f"{side}Hand", MARBLE, tuple(Vector(j["wr"]).lerp(Vector(j["hd"]), 0.5)), (0.055*k, 0.11*k, 0.12*k), bev=0.02*k, segs=2)
    for fn, yy in (("Index", -0.036), ("Middle", -0.012), ("Ring", 0.012), ("Pinky", 0.036)):
        p0 = Vector(j["hd"]) + Vector((0, yy*k, 0.02*k)); p1 = p0 + Vector((0, 0, -0.055*k)); p2 = p1 + Vector((-0.006*s*k, 0, -0.045*k))
        for bb, a_, b_, r0, r1 in ((f"{side}{fn}1", p0, p1, 0.015, 0.014), (f"{side}{fn}2", p1, p2, 0.014, 0.011)):
            loft(bb, MARBLE, [(0, r0*k, r0*k), ((b_ - a_).length, r1*k, r1*k)], N=10, M=_frame(a_, b_ - a_), sub=1)
        sph(f"{side}{fn}1", MARBLE, tuple(p1), 0.0145*k, u=10, v=6)
        if fn == "Ring":
            loft(f"{side}{fn}1", GOLD, [(0.012*k, .017*k, .017*k), (0.02*k, .017*k, .017*k)], N=12, M=_frame(p0, p1 - p0))
    t0 = Vector(j["wr"]) + Vector((0, -0.05*k, -0.05*k)); t1 = t0 + Vector((0, -0.035*k, -0.035*k)); t2 = t1 + Vector((0, -0.025*k, -0.035*k))
    for bb, a_, b_, r0, r1 in ((f"{side}Thumb1", t0, t1, 0.017, 0.015), (f"{side}Thumb2", t1, t2, 0.015, 0.012)):
        loft(bb, MARBLE, [(0, r0*k, r0*k), ((b_ - a_).length, r1*k, r1*k)], N=10, M=_frame(a_, b_ - a_), sub=1)

# ======================= ROBE: layered drapery, gold hem pattern, aether wisps beneath ======================================
PIECE = "Robe"
loft("LowerTorso", VEIL, [(Z(1.13), .16*k, .12*k), (Z(0.95), .21*k, .17*k), (Z(0.6), .27*k, .23*k), (Z(0.3), .31*k, .27*k), (Z(0.14), .3*k, .26*k),
                          (Z(0.1), .26*k, .22*k)], N=48, sub=1)
for i in range(16):                                                         # folds
    a = i*2*math.pi/16 + 0.1
    loft("LowerTorso", MARBLE, [(0, .014*k, .02*k), (Z(0.8), .024*k, .03*k)], N=8,
         M=_frame(Vector((0.21*k*math.cos(a), 0.17*k*math.sin(a), Z(0.95))), Vector((0.1*k*math.cos(a), 0.1*k*math.sin(a), -Z(0.8)))))
# overskirt panels (front + back) lying flush on the robe, gold-edged, embroidered spire chevrons
def robe_r(z):   # robe radii (rx, ry) at height z (matches the robe loft profile)
    prof = [(1.13, .16, .12), (0.95, .21, .17), (0.6, .27, .23), (0.3, .31, .27), (0.14, .3, .26)]
    zz = z/k
    for (z0, a0, b0), (z1, a1, b1) in zip(prof, prof[1:]):
        if z1 <= zz <= z0:
            u = (z0 - zz)/(z0 - z1); return (a0 + (a1 - a0)*u)*k, (b0 + (b1 - b0)*u)*k
    return prof[-1][1]*k, prof[-1][2]*k
for face in (-1, 1):
    tb = bmesh.new(); rows_ = []
    for r in range(13):
        z = Z(1.08 - 0.9*r/12); rx, ry = robe_r(z); half = 0.42 + 0.25*r/12
        row = []
        for q in range(9):
            a = (math.pi/2 if face > 0 else -math.pi/2) + (q/8 - 0.5)*2*half
            row.append(tb.verts.new((rx*1.02*math.cos(a), ry*1.02*math.sin(a), z)))
        rows_.append(row)
    for r in range(12):
        for q in range(8):
            tb.faces.new((rows_[r][q], rows_[r][q+1], rows_[r+1][q+1], rows_[r+1][q]))
    edge = [[rows_[r][q].co.copy() for q in (0, 8)] for r in range(13)]
    _add(tb, "LowerTorso", WARM, Matrix(), True, 0, mods=[("SOLIDIFY", {"thickness": 0.012*k, "offset": 1})])
    for r in range(12):                                                      # gold edges
        for e in (0, 1):
            tube("LowerTorso", GOLD, tuple(edge[r][e]*1.012), tuple(edge[r+1][e]*1.012), 0.005*k, 0.005*k, N=4)
    for cv in range(4):                                                      # spire chevrons
        z = Z(0.95 - cv*0.2); rx, ry = robe_r(z)
        a0 = math.pi/2 if face > 0 else -math.pi/2
        pA = Vector((rx*1.04*math.cos(a0 - 0.25), ry*1.04*math.sin(a0 - 0.25), z - Z(0.06)))
        pB = Vector((rx*1.04*math.cos(a0), ry*1.04*math.sin(a0), z))
        pC = Vector((rx*1.04*math.cos(a0 + 0.25), ry*1.04*math.sin(a0 + 0.25), z - Z(0.06)))
        tube("LowerTorso", GOLD, tuple(pA), tuple(pB), 0.005*k, 0.005*k, N=4); tube("LowerTorso", GOLD, tuple(pB), tuple(pC), 0.005*k, 0.005*k, N=4)
    gem("LowerTorso", GLOW, tuple(Vector((0, robe_r(Z(1.02))[1]*1.05*face, Z(1.02)))), 0.02*k, 0.012*k, rot=(math.pi/2, 0, 0), sides=4)
arc_band("LowerTorso", GOLD, (0, 0), Z(1.14), Z(1.08), (.16*k, .12*k), (.175*k, .135*k), 0, 2*math.pi, 0.04, 40)
arc_band("LowerTorso", GOLD, (0, 0), Z(0.2), Z(0.13), (.308*k, .268*k), (.302*k, .262*k), 0, 2*math.pi, 0.04, 56)
for i in range(28):                                                         # hem medallions
    a = i*2*math.pi/28
    gem("LowerTorso", GOLD, (0.312*k*math.cos(a), 0.272*k*math.sin(a), Z(0.165)), 0.012*k, 0.006*k, rot=(math.pi/2, 0, a + math.pi/2), sides=4)
# aether beneath the hovering hem: a floating glow ring and curling ribbons (no fangs)
tb = bmesh.new(); Rr = 0.24*k; seg = 64
ring_v = [[tb.verts.new(((Rr + 0.01*k*math.cos(bb))*math.cos(a), (Rr*0.86 + 0.01*k*math.cos(bb))*math.sin(a), Z(0.06) + 0.01*k*math.sin(bb)))
           for bb in [2*math.pi*j/6 for j in range(6)]] for a in [2*math.pi*i/seg for i in range(seg)]]
for i in range(seg):
    for j in range(6):
        tb.faces.new((ring_v[i][j], ring_v[(i+1) % seg][j], ring_v[(i+1) % seg][(j+1) % 6], ring_v[i][(j+1) % 6]))
_add(tb, "LowerTorso", GLOW, Matrix())
for i in range(6):
    a0 = i*2*math.pi/6
    pts_ = [Vector(((0.22*k + 0.03*k*math.sin(u*9))*math.cos(a0 + u*1.6), (0.19*k + 0.03*k*math.sin(u*9))*math.sin(a0 + u*1.6), Z(0.12) - u*Z(0.1)))
            for u in [q/14 for q in range(15)]]
    for q, (pa, pb) in enumerate(zip(pts_, pts_[1:])):
        tube("LowerTorso", GLOW, tuple(pa), tuple(pb), 0.008*k*(1 - q/15), 0.008*k*(1 - (q + 1)/15), N=5)
# ======================= SHARDS: faceted marble spire fragments with gold bands and violet cores ==========================
PIECE = "Shards"
for i in range(6):
    a = i*math.pi/3
    c = Vector((0.55*k*math.cos(a), 0.55*k*math.sin(a), Z(1.1 + 0.15*math.sin(i*1.3))))
    add_bone(f"Shard{i+1}", c - Vector((0, 0, 0.3)), c + Vector((0, 0, 0.3)), "HumanoidRootNode")
    M = TR(tuple(c), (0.15*math.sin(i), 0.2*math.cos(i), a))
    loft(f"Shard{i+1}", MARBLE, [(-0.3*k, .002, .002, 1.2), (-0.16*k, .045*k, .035*k, 1.2), (0.0, .055*k, .042*k, 1.25), (0.14*k, .045*k, .035*k, 1.2), (0.32*k, .002, .002, 1.2)], N=6, M=M)
    for zb in (-0.1, 0.08):
        loft(f"Shard{i+1}", GOLD, [(zb*k - 0.008*k, .05*k, .039*k, 1.25), (zb*k + 0.008*k, .05*k, .039*k, 1.25)], N=6, M=M)
    loft(f"Shard{i+1}", GLOW, [(-0.05*k, .014*k, .014*k, 1.3), (0.05*k, .012*k, .012*k, 1.3)], N=6, M=M @ Matrix.Translation((0, -0.036*k, 0)))
add_bone("Weapon_R", Vector(J["Right"]["hd"]) + Vector((0, -0.05, 0)), Vector(J["Right"]["hd"]) + Vector((0, -0.6, 0)), "RightHand")
rig, PARTS = assemble(NAME, OFFSET)
