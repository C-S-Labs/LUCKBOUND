# =====================================================================================
# WINGED SENTINEL v5 GEOMETRY - sleek, aggressive angel-duelist silhouette (thin waist, long limbs, pointed plate),
# halo-crown blade wings, faceless prow helm with a floating halo. Two layers:
#   UNDER  (always visible, the phase-2 body): graphite frame + violet-black sinew musculature, split ribcage around the
#          aether core, cyan aether channels, glowing joint rings, talon hands/feet.
#   ARMOUR (BREAK=True -> Break_* chunks shed in phase 2): pointed cuirass with a core window, plackart, swept blade
#          pauldrons, bracers, tassets, faulds, greaves, sabatons.
# =====================================================================================
import random
_rnd = random.Random(5)
SINEW = CLOTH                       # material slot 4 = sinew
UNDER = IRON; PLATE = PATINA; TRIM = BRONZE; INLAY = IVORY
from mathutils.bvhtree import BVHTree

# ------------------------------------------------ TORSO (under) ------------------------------------------------------
PIECE = "Torso"
TSEC = [(1.96, .165, .14, 2.2), (2.1, .185, .15, 2.1), (2.28, .26, .18, 2.0, 0, -.01), (2.46, .34, .2, 1.9, 0, -.02),
        (2.62, .38, .2, 2.0, 0, -.02), (2.74, .35, .185, 2.3, 0, -.01), (2.84, .25, .15, 2.5), (2.9, .12, .1, 2.4)]
TSEC = [(z, rx*(0.91 if z > 2.2 else 1.0), ry*0.92, *rest) for (z, rx, ry, *rest) in TSEC]
loft("UpperTorso", UNDER, TSEC, N=32, sub=1)
_tor = BVHTree.FromBMesh(PIECES["Torso"])
def on_body(x, z, front=True):
    o = Vector((x, -2.0 if front else 2.0, z)); d = Vector((0, 1 if front else -1, 0))
    h, n, _, _ = _tor.ray_cast(o, d)
    return (h, n) if h is not None else (None, None)
CORE = Vector((0, 0, 2.52))
hc, nc = on_body(0, 2.52)
# sinew musculature: pectorals, 6-pack abdominal plates, serratus blades, obliques
for s in (1, -1):
    hp_, np_ = on_body(0.14*s, 2.6)
    sph("UpperTorso", SINEW, tuple(hp_ - np_*0.02), 0.13, scale=(1.15, 0.42, 0.72), u=24, v=12,
        rot=tuple((np_.to_track_quat('Y', 'Z')).to_euler()))
    for r_ in range(3):
        hz, nz = on_body(0.055*s, 2.36 - r_*0.1)
        sph("UpperTorso", SINEW, tuple(hz - nz*0.012), 0.05, scale=(0.95, 0.4, 0.85), u=14, v=8)
    for r_ in range(4):
        hs, ns = on_body(0.24*s, 2.5 - r_*0.07)
        if hs is not None:
            blade("UpperTorso", SINEW, tuple(hs + ns*0.005 + Vector((0.03*s, 0, 0))), (0.35*s, -0.3, -0.55), 0.13, 0.03, 0.02, hint=tuple(ns), N=6, sub=0)
    ho, no = on_body(0.15*s, 2.12)
    sph("UpperTorso", SINEW, tuple(ho - no*0.015), 0.08, scale=(0.8, 0.4, 1.4), u=14, v=8, rot=(0, 0.25*s, 0))
# split ribcage framing the core cavity: dark cavity, 4 rib arcs per side, sternum spine
sph("UpperTorso", UNDER, tuple(hc - nc*0.02), 0.11, scale=(1.0, 0.5, 1.25), u=20, v=12)
for s in (1, -1):
    for r_ in range(4):
        z0 = 2.4 + r_*0.075
        pts_ = []
        for u in range(7):
            x = 0.045*s + s*0.25*(u/6)**0.9
            h_, n_ = on_body(x, z0 + 0.06*math.sin(u/6*math.pi) - 0.05*(u/6))
            if h_ is not None: pts_.append(h_ + n_*0.012)
        for a_, b_ in zip(pts_, pts_[1:]):
            tube("UpperTorso", UNDER, tuple(a_), tuple(b_), 0.016 - 0.002*r_, 0.014 - 0.002*r_, N=8)
for z in (2.36, 2.72):
    h_, n_ = on_body(0, z)
    box("UpperTorso", UNDER, None, (0.06, 0.035, 0.08), bev=0.012, segs=1, M=_frame(h_ + n_*0.005, n_, hint=(0, 0, 1)))
# aether core + channels raycast across the torso (to shoulders, down the abs, around the flanks)
gem("VFX_Core", GLOW, tuple(hc + nc*0.01), 0.075, 0.09, rot=tuple(nc.to_track_quat('Z', 'Y').to_euler()), sides=8)
sph("VFX_Core", GLOW, tuple(hc - nc*0.01), 0.06, u=16, v=10)
def channel(path_xz, r=0.008, off=0.012, front=True, bone="UpperTorso"):
    prev = None
    for x, z in path_xz:
        h_, n_ = on_body(x, z, front)
        if h_ is None: prev = None; continue
        p_ = h_ + n_*off
        if prev is not None: tube(bone, GLOW, tuple(prev), tuple(p_), r, r, N=5)
        prev = p_
for s in (1, -1):
    channel([(0.07*s + 0.03*s*i, 2.56 + 0.04*i) for i in range(8)])                   # to the shoulder
    channel([(0.08*s + 0.02*s*math.sin(i*0.6), 2.44 - 0.05*i) for i in range(9)])      # down the abs
    channel([(0.18*s + 0.02*s*i, 2.32 - 0.03*i) for i in range(6)])                    # flank
    channel([(0.12*s*math.cos(i*0.3), 2.3 + 0.35*i/8) for i in range(9)], front=False)  # back
# back: segmented spine plates + wing sockets
for i in range(9):
    h_, n_ = on_body(0, 2.05 + i*0.09, front=False)
    if h_ is not None:
        box("UpperTorso", UNDER, None, (0.09 - 0.004*i, 0.05, 0.07), bev=0.015, segs=1, M=_frame(h_, n_, hint=(0, 0, 1)))
        box("UpperTorso", TRIM, None, (0.03, 0.06, 0.05), bev=0.008, segs=1, M=_frame(h_ + n_*0.02, n_, hint=(0, 0, 1)))
for s in (1, -1):
    sph("UpperTorso", UNDER, (0.17*s, 0.24, 2.64), 0.09, scale=(1, 0.8, 1), u=16, v=10)
    arc_band("UpperTorso", GLOW, (0.17*s, 0.24), 2.61, 2.605, (.092, .074), (.092, .074), 0, 2*math.pi, 0.008, 24)
# neck: cabled column + glow ring
loft("Neck", UNDER, [(2.86, .075, .075), (3.02, .065, .065)], N=16)
for i in range(6):
    a = i*math.pi/3
    tube("Neck", SINEW, (0.07*math.cos(a), 0.07*math.sin(a), 2.84), (0.06*math.cos(a + 0.4), 0.06*math.sin(a + 0.4), 3.02), 0.018, 0.015, N=6)
arc_band("Neck", GLOW, (0, 0), 2.9, 2.905, (.085, .085), (.085, .085), 0, 2*math.pi, 0.006, 24)

# ------------------------------------------------ ARMOUR: torso (breakaway) ------------------------------------------
BREAK = True
ASEC = [(2.18, .215, .17, 1.7, 0, -.02), (2.3, .29, .21, 1.5, 0, -.05), (2.46, .37, .24, 1.4, 0, -.075),
        (2.62, .405, .235, 1.45, 0, -.065), (2.74, .36, .21, 2.3, 0, -.03), (2.82, .27, .17, 2.5, 0, -.01)]
def core_window(c):   # leave a vertical slit window over the core
    return not (c.y < -0.1 and abs(c.x) < 0.05 and 2.4 < c.z < 2.66)
ASEC = [(z, rx*(0.9 if z > 2.2 else 0.98), ry*0.9, *rest) for (z, rx, ry, *rest) in ASEC]
loft("UpperTorso", PLATE, ASEC, N=40, sub=0, keep=core_window, fill=False)
for z_, r_ in ((2.82, (.23, .153)), (2.19, (.223, .162))):
    arc_band("UpperTorso", TRIM, (0, -0.02), z_ + 0.012, z_ - 0.006, (r_[0] + .006, r_[1] + .006), (r_[0] + .01, r_[1] + .01), 0, 2*math.pi, 0.012, 40)
_arm = BVHTree.FromBMesh(PIECES["Breakaway"])
def on_armour(x, z):
    h, n, _, _ = _arm.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
    return (h, n) if h is not None else (None, None)
def flow(path, mi=TRIM, r=0.011, off=0.008):
    pts = []
    for x, z in path:
        h_, n_ = on_armour(x, z)
        if h_ is not None: pts.append(h_ + n_*off)
    if len(pts) < 2: return
    tb = bmesh.new(); rings = []; N = 8
    for i, p_ in enumerate(pts):
        tg = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        x = Vector((0, -1, 0)).cross(tg); x = x.normalized() if x.length > 1e-4 else Vector((1, 0, 0)); y = tg.cross(x)
        rr = r*(1 - 0.35*i/(len(pts) - 1))
        rings.append([tb.verts.new(p_ + x*rr*math.cos(2*math.pi*q/N) + y*rr*math.sin(2*math.pi*q/N)) for q in range(N)])
    for r0, r1 in zip(rings, rings[1:]):
        for q in range(N):
            tb.faces.new((r0[q], r0[(q + 1) % N], r1[(q + 1) % N], r1[q]))
    tb.faces.new(rings[0]); tb.faces.new(list(reversed(rings[-1])))
    _add(tb, "UpperTorso", mi, Matrix(), True, 0)
for s in (1, -1):
    # raised angular pectoral plates (faceted), trim edged
    hp_, np_ = on_armour(0.145*s, 2.6)
    Mp = _frame(hp_ - np_*0.01, np_, hint=(0, 0, 1))
    loft("UpperTorso", PLATE, [(0, .11, .08, 1.3), (0.03, .105, .075, 1.3), (0.045, .085, .058, 1.3)], N=6, M=Mp @ Matrix.Rotation(0.35*s, 4, 'Z'))
    loft("UpperTorso", TRIM, [(0.028, .113, .083, 1.3), (0.036, .113, .083, 1.3)], N=6, M=Mp @ Matrix.Rotation(0.35*s, 4, 'Z'))
    # flow lines: collar -> over the pecs -> converging at the waist
    flow([(0.1*s + 0.17*s*math.sin(u*math.pi*0.5)*(1 - u), 2.8 - 0.62*u) for u in [k/30 for k in range(31)]])
    flow([(0.26*s*(1 - u) + 0.06*s*u, 2.7 - 0.5*u) for u in [k/26 for k in range(27)]], r=0.008)
    flow([(0.058*s, 2.38 + 0.3*u) for u in [k/16 for k in range(17)]], r=0.011)          # core window frame
for i in range(7):   # high swept gorget: blades rising round the neck and curving back
    a = -math.pi/2 + (i - 3)*0.42
    base = Vector((0.13*math.cos(a), 0.11*math.sin(a) + 0.01, 2.82))
    blade("UpperTorso", TRIM if i % 3 == 0 else PLATE, tuple(base), (0.45*math.cos(a), 0.45*math.sin(a) + 0.55, 1.0), 0.26 - 0.03*abs(i - 3), 0.05, 0.018, hint=(0, 0, 1), N=8)
for i in range(3):   # chevron plackart plates pointing down to the belt
    z0 = 2.15 - i*0.07
    for s in (1, -1):
        blade("UpperTorso", PLATE, (0.2*s - 0.02*s*i, -0.2 + 0.01*i, z0 + 0.03), (-1.0*s, -0.12, -0.55), 0.24 - 0.03*i, 0.05, 0.02, hint=(0, 1, 0), N=6)
        tube("UpperTorso", TRIM, (0.2*s - 0.02*s*i, -0.215 + 0.01*i, z0 + 0.045), (0.01*s, -0.24, z0 - 0.06), 0.006, 0.005, N=5)
BREAK = False

# ------------------------------------------------ HEAD: faceless prow helm + floating halo -------------------------------
PIECE = "Head"
XF = scale_about((0, 0, 2.95), (1.24, 1.08, 0.88))     # wider from the front, shorter (esp. from the top)
def vwarp5(co):
    if co.y < 0:
        co.z += 0.5*abs(co.x)*min(1.0, -co.y/0.1)
def hs(z, rx, ry, oy=-.02): return (z, rx, ry, 1.45, 0, oy)
loft("Head", UNDER, [(2.98, .1, .13), (3.42, .08, .11)], N=16)
def beakwarp(co):
    vwarp5(co)
    if co.y < -0.05:      # the lower faceplate itself draws down/forward into a subtle beak at the centre line
        u = max(0.0, 1 - abs(co.x)/0.17); f = u*u*(3 - 2*u) * max(0.0, min(1.0, (3.23 - co.z)/0.22))
        co.y -= 0.03*f; co.z -= 0.012*f
loft("Head", PLATE, [hs(2.97, .1, .14), hs(3.02, .11, .16), hs(3.06, .118, .175), hs(3.11, .121, .184), hs(3.16, .122, .19), hs(3.225, .12, .19)], N=64, warp=beakwarp, sub=1)
loft("Head", UNDER, [hs(3.22, .11, .18), hs(3.28, .11, .18)], N=48, warp=vwarp5)
loft("Head", GLOW, [hs(3.24, .1125, .1825), hs(3.255, .1125, .1825)], N=48, warp=vwarp5, keep=lambda c: c.y < -0.05)
loft("Head", PLATE, [hs(3.275, .128, .2, -.025), hs(3.3, .128, .2, -.025), hs(3.38, .112, .18), hs(3.47, .08, .15, -.005),
                     hs(3.53, .04, .1, .02), (3.56, .01, .04, 2, 0, .05)], N=48, warp=vwarp5)
loft("Head", TRIM, [hs(3.27, .131, .204, -.025), hs(3.285, .131, .204, -.025)], N=48, warp=vwarp5)
def curved_blade(bone, mi, pts, widths, thick, side_hint=(1, 0, 0), N=10):
    """Blade swept along a curve: lens sections at each point, width/thickness tapering to a point."""
    tb = bmesh.new(); rings = []
    for i, p_ in enumerate(pts):
        tg = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        x = Vector(side_hint).cross(tg).normalized(); y = tg.cross(x)
        w = widths[i]; th = thick*(w/max(widths))
        ring_ = []
        for q in range(N):
            a = 2*math.pi*q/N
            ca, sa = math.cos(a), math.sin(a)
            ring_.append(tb.verts.new(p_ + y*(w*math.copysign(abs(ca)**(2/1.6), ca)) + x*(max(th, 0.002)*math.copysign(abs(sa)**(2/1.6), sa))))
        rings.append(ring_)
    for r0, r1 in zip(rings, rings[1:]):
        for q in range(N):
            tb.faces.new((r0[q], r0[(q + 1) % N], r1[(q + 1) % N], r1[q]))
    tb.faces.new(rings[0]); tb.faces.new(list(reversed(rings[-1])))
    _add(tb, bone, mi, Matrix(), True, 1)
# swept crest: three curved horn-blades per side rising off the crown and hooking back/down, plus a centre fin
for s in (1, -1):
    for i, (st, L, rise, out, w0) in enumerate((((0.03, -0.07, 3.5), 0.46, 0.1, 0.08, 0.05), ((0.08, -0.02, 3.43), 0.38, 0.07, 0.12, 0.042), ((0.105, 0.0, 3.34), 0.3, 0.04, 0.15, 0.034))):
        st = Vector((st[0]*s, st[1], st[2]))
        pts = [st + Vector((out*s*u, L*u, rise*math.sin(math.pi*u*0.85) - 0.16*L*u*u)) for u in [k/9 for k in range(10)]]
        ws = [w0*(1 - 0.92*(k/9)**1.2) for k in range(10)]
        curved_blade("Head", TRIM if i == 0 else PLATE, pts, ws, 0.014, side_hint=(0, 0, 1))
    blade("Head", PLATE, (0.11*s, -0.08, 3.05), (0.35*s, 1.0, -0.45), 0.24, 0.05, 0.014, hint=(0, 0, 1), N=6)    # jaw blades
PIECE = "HeadPlates"
# layered helm plates: three overlapping shells stepping down the crown/back, each with a violet rim
for i, (z0, z1, g) in enumerate(((3.38, 3.54, 0.018), (3.26, 3.4, 0.03), (3.14, 3.28, 0.042))):
    secs = [hs(z0, .128 + g, .2 + g, -.02), hs((z0 + z1)/2, .122 + g, .19 + g, -.015), hs(z1, .09 + g*0.6, .16 + g*0.6, 0)]
    loft("Head", PLATE, secs, N=48, keep=lambda c, i=i: c.y > 0.02 + 0.03*i, fill=False, cap=False, sub=1)
    loft("Head", TRIM, [hs(z0 - 0.004, .13 + g, .203 + g, -.02), hs(z0 + 0.008, .13 + g, .203 + g, -.02)], N=48, keep=lambda c, i=i: c.y > 0.02 + 0.03*i, fill=False)
# cheek guards (layered side plates sweeping back to the jaw) - front edges taper flush into the faceplate/prow
def cheekwarp(co):
    t = max(0.0, min(1.0, (abs(co.x) - 0.06)/0.08)); t = t*t*(3 - 2*t)
    if co.y < 0:
        k_ = 0.955 + 0.045*t; co.x *= k_; co.y *= k_
    beakwarp(co)
for s in (1, -1):
    loft("Head", PLATE, [hs(3.0, .122, .18), hs(3.1, .135, .195), hs(3.2, .128, .19)], N=48,
         keep=lambda c, s=s: c.x*s > 0.06 and c.y < 0.06, fill=False, cap=False, sub=1, warp=cheekwarp)
    loft("Head", TRIM, [hs(3.0, .124, .182), hs(3.012, .124, .182)], N=48, keep=lambda c, s=s: c.x*s > 0.06 and c.y < 0.06, fill=False, warp=cheekwarp)
PIECE = "Head"
fin = [Vector((0, -0.17 + 0.36*u, 3.47 + 0.075*math.sin(math.pi*u) + 0.02*u)) for u in [k/11 for k in range(12)]]
curved_blade("Head", TRIM, fin, [0.05*(1 - 0.85*(k/11)**1.5) + 0.004 for k in range(12)], 0.012, side_hint=(1, 0, 0))
# floating halo (own bone): violet crown ring with inward blade spikes + cyan inner ring
XF = None
PIECE = "HeadHalo"
add_bone("Halo", (0, 0.5, 3.42), (0, 0.62, 3.42), "Head")
def ring(bone, mi, R_, r_, M, seg=64, rs=8):
    tb = bmesh.new()
    rg = [[tb.verts.new(((R_ + r_*math.cos(b))*math.cos(a), (R_ + r_*math.cos(b))*math.sin(a), r_*math.sin(b))) for b in [2*math.pi*j/rs for j in range(rs)]]
          for a in [2*math.pi*i/seg for i in range(seg)]]
    for i in range(seg):
        for j in range(rs):
            tb.faces.new((rg[i][j], rg[(i+1) % seg][j], rg[(i+1) % seg][(j+1) % rs], rg[i][(j+1) % rs]))
    _add(tb, bone, mi, M)
MHa = TR((0, 0.52, 3.42), (math.pi/2 - 0.12, 0, 0))
ring("Halo", TRIM, 0.36, 0.016, MHa); ring("Halo", GLOW, 0.31, 0.006, MHa)
for i in range(16):
    a = i*math.pi/8
    L_ = 0.14 if i % 2 == 0 else 0.08
    blade("Halo", TRIM if i % 2 == 0 else PLATE, tuple(MHa @ Vector((0.36*math.cos(a), 0.36*math.sin(a), 0))), tuple(MHa.to_3x3() @ Vector((math.cos(a), math.sin(a), 0))),
          L_, 0.025, 0.01, hint=tuple(MHa.to_3x3() @ Vector((0, 0, 1))), N=6, sub=0)

# ------------------------------------------------ ARMS: sinew under-limbs + sleek armour + talon hands ------------------
for side, s in (("Left", 1), ("Right", -1)):
    PIECE = "Arm" + side
    ua, la, hd = f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"
    SH = Vector(BONES[BIDX[ua]][1]); EL = Vector(BONES[BIDX[la]][1]); WR = Vector(BONES[BIDX[hd]][1]); HE = Vector(BONES[BIDX[hd]][2])
    out = 0.0 if s > 0 else math.pi
    # under: shoulder ball, bicep/forearm sinew bulges, glow joint rings, channel lines
    sph(ua, UNDER, tuple(SH), 0.1, u=20, v=12)
    Mu = _frame(SH, EL - SH); Lu = (EL - SH).length
    loft(ua, SINEW, [(0.04, .075, .08), (Lu*0.35, .095, .1), (Lu*0.7, .08, .085), (Lu, .065, .07)], N=20, M=Mu, sub=1)
    sph(la, UNDER, tuple(EL), 0.072, u=16, v=10)
    Ml = _frame(EL, WR - EL); Ll = (WR - EL).length
    loft(la, SINEW, [(0.03, .07, .075), (Ll*0.3, .082, .085), (Ll*0.8, .06, .062), (Ll, .05, .052)], N=20, M=Ml, sub=1)
    for bn, c_, M_, r_ in ((ua, SH + (EL - SH)*0.02, Mu, 0.1), (la, EL, Ml, 0.08), (hd, WR, Ml, 0.058)):
        loft(bn, GLOW, [(-0.004, r_, r_), (0.004, r_, r_)], N=24, M=_frame(c_, (EL - SH) if bn == ua else (WR - EL)), cap=False)
    for M_, L_, bn, r0 in ((Mu, Lu, ua, 0.098), (Ml, Ll, la, 0.084)):
        tube(bn, GLOW, tuple(M_ @ Vector((0, -r0, 0.1))), tuple(M_ @ Vector((0, -r0*0.85, L_*0.85))), 0.007, 0.006, N=5)
    # talon hand: palm, 4 two-bone fingers + thumb with violet talons
    sph(hd, UNDER, tuple(WR), 0.055, u=14, v=8)
    Mh = _frame(WR, HE - WR, hint=(0, 1, 0))
    loft(hd, SINEW, [(0.01, .055, .07, 2.4), (0.09, .06, .075, 2.6), (0.15, .052, .068, 2.6)], N=16, M=Mh, sub=1)
    for fn, yy in (("Index", -0.05), ("Middle", -0.017), ("Ring", 0.017), ("Pinky", 0.05)):
        p0 = WR + (HE - WR).normalized()*0.15 + Vector((0, yy, 0)); p1 = p0 + Vector((-0.01*s, 0, -0.08)); p2 = p1 + Vector((-0.03*s, 0, -0.07))
        add_bone(f"{side}{fn}1", p0, p1, hd); add_bone(f"{side}{fn}2", p1, p2, f"{side}{fn}1")
        tube(f"{side}{fn}1", UNDER, tuple(p0), tuple(p1), 0.018, 0.016, N=8); sph(f"{side}{fn}1", UNDER, tuple(p1), 0.017, u=8, v=6)
        tube(f"{side}{fn}2", UNDER, tuple(p1), tuple(p2), 0.016, 0.012, N=8)
        blade(f"{side}{fn}2", TRIM, tuple(p2 - (p2 - p1).normalized()*0.01), tuple(p2 - p1 + Vector((-0.01*s, 0, -0.02))), 0.055, 0.016, 0.012, hint=(0, 1, 0), N=6, sub=0)
    t0 = WR + Vector((-0.02*s, -0.07, -0.05)); t1 = t0 + Vector((-0.02*s, -0.04, -0.05)); t2 = t1 + Vector((-0.02*s, -0.02, -0.05))
    add_bone(f"{side}Thumb1", t0, t1, hd); add_bone(f"{side}Thumb2", t1, t2, f"{side}Thumb1")
    tube(f"{side}Thumb1", UNDER, tuple(t0), tuple(t1), 0.02, 0.018, N=8); tube(f"{side}Thumb2", UNDER, tuple(t1), tuple(t2), 0.018, 0.013, N=8)
    blade(f"{side}Thumb2", TRIM, tuple(t2), tuple(t2 - t1), 0.05, 0.016, 0.012, hint=(0, 1, 0), N=6, sub=0)
    # armour (breakaway): swept blade pauldron (3 layered blades + spike), bracer with elbow fin
    BREAK = True
    for i in range(3):
        blade(ua, PLATE if i < 2 else TRIM, tuple(SH + Vector((0.03*s, -0.07 + 0.06*i, 0.12 - 0.04*i))), (0.6*s, 0.8, 0.3 - 0.18*i), 0.6 - 0.1*i, 0.14 - 0.02*i, 0.03, hint=(0, 0, 1), N=10)
    loft(ua, PLATE, [(0, .12, .13, 2.2), (0.05, .13, .14, 2.2), (0.1, .1, .11, 2.2)], N=24, M=TR(tuple(SH + Vector((0.01*s, 0.01, 0.02)))), sub=1)
    loft(ua, TRIM, [(0.048, .133, .143, 2.2), (0.058, .133, .143, 2.2)], N=24, M=TR(tuple(SH + Vector((0.01*s, 0.01, 0.02)))))
    loft(la, PLATE, [(Ll*0.15, .08, .085, 2.6), (Ll*0.3, .095, .1, 2.6), (Ll*0.85, .07, .075, 2.6), (Ll*0.92, .06, .064, 2.6)], N=24, M=Ml,
         keep=lambda c: c.y > -0.035, fill=False, sub=1)
    tube(la, TRIM, tuple(Ml @ Vector((0, 0.098, Ll*0.3))), tuple(Ml @ Vector((0, 0.07, Ll*0.85))), 0.01, 0.008, N=6)
    blade(la, PLATE, tuple(EL + Vector((0, 0.06, 0.01))), (0.2*s, 1.0, 0.6), 0.28, 0.06, 0.018, hint=(1, 0, 0), N=8)
    BREAK = False

# ------------------------------------------------ WAIST + FAULDS ---------------------------------------------------------
PIECE = "Waist"
loft("LowerTorso", SINEW, [(1.7, .2, .15, 2.4), (1.82, .215, .16, 2.4), (1.98, .19, .15, 2.4)], N=28, sub=1)
arc_band("LowerTorso", GLOW, (0, 0), 1.9, 1.895, (.2, .153), (.2, .153), 0, 2*math.pi, 0.006, 28)
BREAK = True
loft("LowerTorso", PLATE, [(1.66, .23, .17, 2.4), (1.78, .25, .185, 2.4), (1.9, .225, .17, 2.4)], N=28, sub=1)
arc_band("LowerTorso", TRIM, (0, 0), 1.93, 1.875, (.232, .175), (.245, .185), 0, 2*math.pi, 0.018, 36)
gem("LowerTorso", GLOW, (0, -0.2, 1.9), 0.035, 0.03, rot=(math.pi/2, 0, 0), sides=4)
def fauld5(b1, b2, y, face):
    def wfn(co):
        t = min(1, max(0, (1.5 - co.z)/0.3))
        return {b1: 1 - t, b2: t} if t > 0 else {b1: 1.0}
    M = Matrix.Translation((0, y, 1.84)) @ Matrix.Rotation(0.06*face, 4, 'X')
    loft(b1, PLATE, [(0, .11, .018), (-0.3, .1, .018), (-0.62, .07, .016), (-0.8, .005, .008)], N=16, M=M, sub=1, wfn=wfn)
    for xx in (-0.07, 0.07):
        loft(b1, TRIM, [(-0.02, .006, .022, 2, xx), (-0.6, .005, .02, 2, xx*0.6), (-0.76, .004, .018, 2, 0)], N=6, M=M, wfn=wfn)
    loft(b1, GLOW, [(-0.1, .004, .021), (-0.55, .003, .02)], N=6, M=M, wfn=wfn)
fauld5("FauldFront1", "FauldFront2", -0.2, 1)
fauld5("FauldBack1", "FauldBack2", 0.19, -1)
BREAK = False

# ------------------------------------------------ LEGS: sinew under + sleek greaves + talon sabatons ---------------------
for side, s in (("Left", 1), ("Right", -1)):
    PIECE = "Leg" + side
    ul, ll, ft = f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot"
    HP = Vector(BONES[BIDX[ul]][1]); KN = Vector(BONES[BIDX[ll]][1]); AN = Vector(BONES[BIDX[ft]][1]); TO = Vector(BONES[BIDX[ft]][2])
    Mt = _frame(HP, KN - HP); Lt = (KN - HP).length
    Ms = _frame(KN, AN - KN); Ls = (AN - KN).length
    sph(ul, UNDER, tuple(HP), 0.11, u=18, v=10)
    loft(ul, SINEW, [(0.04, .11, .12), (Lt*0.3, .13, .14, 2, 0, -.01), (Lt*0.7, .11, .115), (Lt, .08, .085)], N=22, M=Mt, sub=1)
    sph(ll, UNDER, tuple(KN), 0.085, u=16, v=10)
    loft(ll, SINEW, [(0.03, .08, .085), (Ls*0.25, .09, .11, 2, 0, .025), (Ls*0.6, .07, .08), (Ls, .05, .055)], N=22, M=Ms, sub=1)
    for c_, M_, r_ in ((HP + (KN - HP)*0.03, Mt, 0.115), (KN, Ms, 0.088), (AN, Ms, 0.058)):
        loft(ul if c_ is not KN and c_ is not AN else ll, GLOW, [(-0.004, r_, r_), (0.004, r_, r_)], N=24, M=_frame(c_, (KN - HP) if M_ is Mt else (AN - KN)), cap=False)
    tube(ul, GLOW, tuple(Mt @ Vector((0, -0.132, 0.1))), tuple(Mt @ Vector((0, -0.1, Lt*0.85))), 0.008, 0.007, N=5)
    tube(ll, GLOW, tuple(Ms @ Vector((0, -0.09, 0.08))), tuple(Ms @ Vector((0, -0.06, Ls*0.85))), 0.007, 0.006, N=5)
    # talon foot (under)
    Mf = _frame(AN, TO - AN, hint=(0, 0, 1)); Lf = (TO - AN).length
    loft(ft, SINEW, [(-0.05, .06, .05), (Lf*0.3, .07, .05), (Lf*0.8, .045, .035), (Lf, .01, .01)], N=16, M=Mf, sub=1)
    for dx in (-0.04, 0.0, 0.04):
        blade(ft, TRIM, tuple(TO + Vector((dx, 0.03, -0.01))), (dx*4, -1, -0.3), 0.09, 0.02, 0.014, hint=(0, 0, 1), N=6, sub=0)
    # armour (breakaway): tasset, thigh plate, knee spike, greave, sabaton shell
    BREAK = True
    M_tas = Matrix.Translation((HP.x*1.45, 0, 1.86)) @ Matrix.Rotation(-0.16*s, 4, 'Y') @ Matrix.Rotation(math.pi/2, 4, 'Z')
    loft(ul, PLATE, [(0, .13, .016), (-0.25, .14, .016), (-0.45, .08, .014), (-0.55, .005, .008)], N=14, M=M_tas, sub=1)
    loft(ul, TRIM, [(-0.02, .006, .02), (-0.5, .004, .018)], N=6, M=M_tas)
    loft(ul, PLATE, [(Lt*0.15, .12, .135, 2.6), (Lt*0.5, .135, .15, 2.6, 0, -.01), (Lt*0.85, .1, .11, 2.6)], N=22, M=Mt, keep=lambda c: c.y < 0.03, fill=False, sub=1)
    sph(ll, PLATE, tuple(KN + Vector((0, -0.07, 0.02))), 0.085, scale=(1.0, 0.7, 1.2), u=16, v=10)
    blade(ll, TRIM, tuple(KN + Vector((0, -0.11, 0.06))), (0, -0.5, 1), 0.2, 0.045, 0.02, hint=(1, 0, 0), N=8)
    loft(ll, PLATE, [(Ls*0.1, .095, .11, 2.6, 0, -.01), (Ls*0.3, .1, .125, 2.4, 0, .015), (Ls*0.9, .07, .08, 2.6), (Ls*0.97, .065, .075, 2.6)], N=24, M=Ms, sub=1)
    tube(ll, TRIM, tuple(Ms @ Vector((0, -0.118, Ls*0.12))), tuple(Ms @ Vector((0, -0.08, Ls*0.9))), 0.012, 0.009, N=6)
    loft(ft, PLATE, [(-0.06, .075, .065, 2.4, 0, .01), (Lf*0.3, .085, .065, 2.4, 0, .01), (Lf*0.8, .055, .045, 2.2, 0, .005), (Lf + 0.06, .006, .006)], N=18, M=Mf, sub=1)
    tube(ft, TRIM, tuple(Mf @ Vector((0, 0.068, 0))), tuple(Mf @ Vector((0, 0.03, Lf + 0.03))), 0.009, 0.006, N=6)
    BREAK = False

# ------------------------------------------------ WINGS: halo-crown of detached blades ---------------------------------
# Each wing = a hub (WingL/R -> WingL/R_Tip) and 9 separated blades on their own bones (WingL_B01..).
# P1 (rest): folded upward-back fan. Phase 2: wings_open() fans them wide (see bottom of file).
WBL = {}
for side, s in (("L", 1), ("R", -1)):
    PIECE = "Wing" + side
    W = "Wing" + side
    hub = Vector(BONES[BIDX[W + "_Tip"]][1])
    sph(W, UNDER, tuple(Vector(BONES[BIDX[W]][1])), 0.06, u=14, v=8)
    tube(W, UNDER, BONES[BIDX[W]][1], tuple(hub), 0.05, 0.04, N=12)
    sph(W + "_Tip", TRIM, tuple(hub), 0.075, u=18, v=10)
    arc_band(W + "_Tip", GLOW, (hub.x, hub.y), hub.z + 0.003, hub.z - 0.003, (.08, .08), (.08, .08), 0, 2*math.pi, 0.006, 24)
    WBL[side] = []
    NB = 7
    for i in range(NB):
        t = i/(NB - 1)
        ang = math.radians(4 + 76*t)                              # angle from vertical, fanning outward
        d = Vector((math.sin(ang)*s, 0.38 + 0.25*t, math.cos(ang))).normalized()
        L_ = 1.75 - 0.9*t**1.3
        root = hub + d*0.3 + Vector((0, 0.03*i, 0))
        bn = f"{W}_B{i+1:02d}"
        add_bone(bn, root, root + d*L_, W + "_Tip")
        WBL[side].append((bn, root))
        hint = Vector((0, 1, 0)) - d*d.y
        Mb = _frame(root, d, hint=tuple(hint))
        w_ = 0.12 - 0.03*t
        secs = [(0, w_*0.25, 0.022), (L_*0.12, w_, 0.03), (L_*0.55, w_*0.85, 0.026), (L_*0.88, w_*0.4, 0.018), (L_, 0.004, 0.004)]
        loft(bn, PLATE, [(z, w, th, 1.8) for z, w, th in secs], N=14, M=Mb, sub=1)
        loft(bn, TRIM, [(z, w*1.08, th*0.45, 1.8) for z, w, th in secs], N=14, M=Mb)                     # violet edge band
        loft(bn, GLOW, [(L_*0.12, 0.012, 0.034), (L_*0.6, 0.009, 0.03), (L_*0.86, 0.004, 0.02)], N=8, M=Mb)   # cyan core line
        tube(W + "_Tip", UNDER, tuple(hub + d*0.07), tuple(root + d*0.02), 0.018, 0.012, N=6)                    # thin strut from hub to blade
BREAK = False
PIECE = "Torso"
