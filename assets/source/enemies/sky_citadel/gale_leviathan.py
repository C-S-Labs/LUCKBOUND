# LUCKBOUND - Sky Citadel BOSS: The Gale Leviathan (Skyport / Dockside) - v2 high-detail rebuild.
# A humpback-like sky-whale refitted by the citadel: brass turbine engines strapped to its back with riveted harness
# bands, aether gill vents, barnacle pod clusters (breakable), knobbed rostrum, throat pleats, hinged jaw with baleen.
# Fight: P1 skimming passes (belly/fin/tail drag the dock edge; pods shed + are destroyed in melee) -> every 3rd pass it
# LATCHES (P2: bite, fin sweeps; head, fins, turbines exposed) -> tears free, repeats -> P3 crashes onto the platform.
# ~14 m. Every piece < 10k tris. Rig: Spine01-10 > Head > Jaw ; Pec{L,R}1-3 ; Fluke ; Turbine1-3 ; Pod1-6.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "GaleLeviathan"; OFFSET = (112.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Head"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
MATS = [mat("GL_Slate", (0.035, 0.05, 0.09), 0.15, 0.22), mat("GL_Blue", (0.16, 0.27, 0.42), 0.1, 0.25),
        mat("GL_Cream", (0.86, 0.8, 0.68), 0.0, 0.3), mat("GL_Dark", (0.04, 0.05, 0.07), 0.2, 0.3),
        mat("GL_Brass", (0.76, 0.55, 0.22), 1.0, 0.18), mat("GL_Glow", (0.4, 0.95, 1.0), 0, 0.3, (0.3, 0.9, 1.0), 3.0),
        mat("GL_Barnacle", (0.62, 0.6, 0.54), 0.0, 0.45), mat("GL_Eye", (0.95, 0.45, 0.02), 0, 0.2, (1.0, 0.4, 0.0), 1.2),
        mat("GL_Iron", (0.16, 0.16, 0.18), 0.8, 0.3), mat("GL_CreamD", (0.62, 0.56, 0.46), 0.0, 0.35),
        mat("GL_Mouth", (0.28, 0.05, 0.07), 0.0, 0.35), mat("GL_Fang", (0.93, 0.9, 0.8), 0.0, 0.25), mat("GL_Tongue", (0.55, 0.18, 0.22), 0.0, 0.4)]
SLATE, BLUE, CREAM, DARK, BRASS, GLOW, BARN, EYE, IRONM, CREAMD, MOUTHM, FANG, TONGUE = range(13)
PATINA, BRONZE, IRON, IVORY, CLOTH = SLATE, BLUE, DARK, CREAM, BARN
Hz = 3.2; L = 14.0; NS = 10
def sp(t): return Vector((0.3*math.sin(t*math.pi*1.3), -L*0.5 + L*t, Hz + 0.35*math.sin(t*math.pi) - 0.3*t))
RT = [(0.0, 0.42), (0.03, 0.8), (0.1, 1.15), (0.28, 1.5), (0.44, 1.42), (0.6, 1.08), (0.78, 0.6), (0.9, 0.34), (1.0, 0.2)]
def rad(t):
    for (t0, r0), (t1, r1) in zip(RT, RT[1:]):
        if t <= t1:
            u = (t - t0)/(t1 - t0); u = u*u*(3 - 2*u); return r0 + (r1 - r0)*u
    return RT[-1][1]
def frame_at(t):
    c = sp(t); tg = (sp(min(1, t + 0.005)) - sp(max(0, t - 0.005))).normalized()
    x = Vector((0, 0, 1)).cross(tg).normalized(); y = tg.cross(x).normalized()
    return c, x, y, tg
MOUTH = 0.24                                   # mouth line sits at sin(a) = -MOUTH on the head
def surf(t, a, off=0.0):
    c, x, y, tg = frame_at(t); w = rad(t)
    hf = 0.72 + 0.2*min(1, t/0.14)             # flatter rostrum
    sa, ca = math.sin(a), math.cos(a)
    yy = sa*(0.84 if sa < 0 else 1.0)*hf        # flatter belly
    if sa < -0.3 and 0.02 < t < 0.5:            # throat pleats
        yy += 0.018*math.sin(ca*38)*min(1, (0.5 - t)*6)*min(1, (t - 0.02)*20)/max(w, 0.3)
    if sa > 0.9 and 0.45 < t < 0.82:            # dorsal ridge
        yy += 0.05*(sa - 0.9)*10
    return c + x*(w + off)*ca + y*(w + off)*yy
def normal_at(t, a):
    p = surf(t, a); du = surf(min(1, t + 0.004), a) - surf(max(0, t - 0.004), a); dv = surf(t, a + 0.01) - surf(t, a - 0.01)
    n = du.cross(dv).normalized()
    c = frame_at(t)[0]
    return n if n.dot(p - c) > 0 else -n
pts = [sp(i/NS) for i in range(NS + 1)]
for i in range(NS):
    BONES.append((f"Spine{i+1:02d}", tuple(pts[i]), tuple(pts[i+1]), f"Spine{i:02d}" if i else None))
jh = surf(0.16, -math.pi/2)*0.5 + surf(0.16, 0.0)*0.25 + surf(0.16, math.pi)*0.25
BONES += [("Head", tuple(sp(0.16)), tuple(sp(0.0)), "Spine02"),
          ("Jaw", tuple(jh), tuple(surf(0.0, -math.pi/2)), "Head"),
          ("Fluke", tuple(sp(1.0)), tuple(sp(1.0) + Vector((0, 1.5, 0))), f"Spine{NS:02d}")]
BIDX.update({b[0]: i for i, b in enumerate(BONES)})

# ---------------- body skin: one continuous high-res surface, per-face tone bands, per-vertex blended weights -------------
def weights(t, a):
    sa = math.sin(a)
    if t < 0.2:
        f = max(0.0, min(1.0, (t - 0.12)/0.08))           # head -> spine blend
        w = {"Head": 1 - f}
        if f > 0: w["Spine02"] = f
        if sa < -MOUTH and t < 0.16:                      # lower jaw
            j = max(0.0, min(1.0, (0.16 - t)/0.03))
            w = {k_: v*(1 - j) for k_, v in w.items()}; w["Jaw"] = w.get("Jaw", 0) + j
        return w
    s = t*NS - 0.5; i0 = max(0, min(NS - 1, int(math.floor(s)))); i1 = min(NS - 1, i0 + 1); f = max(0.0, min(1.0, s - i0))
    return {f"Spine{i0+1:02d}": 1 - f, f"Spine{i1+1:02d}": f} if i0 != i1 else {f"Spine{i0+1:02d}": 1.0}
def band(t, a):
    sa = math.sin(a); ca = math.cos(a)
    if sa > 0.45: return SLATE
    if sa > -0.32: return BLUE
    if 0.02 < t < 0.5 and math.sin(ca*38) < -0.55: return CREAMD
    return CREAM
def skin(piece, t0, t1, rows, cols=64):
    global PIECE
    PIECE = piece
    bm = PIECES.setdefault(piece, bmesh.new()); dl = bm.verts.layers.deform.verify()
    grid = []
    for r in range(rows + 1):
        t = t0 + (t1 - t0)*r/rows
        row = []
        for q in range(cols):
            a = -math.pi/2 + 2*math.pi*q/cols
            v = bm.verts.new(surf(t, a))
            for bn, wt in weights(t, a).items():
                v[dl][BIDX[bn]] = wt
            row.append((v, t, a))
        grid.append(row)
    for r in range(rows):
        for q in range(cols):
            v00, ta, aa = grid[r][q]; v01 = grid[r][(q + 1) % cols][0]; v11 = grid[r+1][(q + 1) % cols][0]; v10 = grid[r+1][q][0]
            if piece == "Head":
                jw = [weights(grid[rr][qq][1], grid[rr][qq][2]).get("Jaw", 0.0) for rr, qq in ((r, q), (r, (q + 1) % cols), (r + 1, (q + 1) % cols), (r + 1, q))]
                if max(jw) > 0.5 and min(jw) < 0.5:
                    continue                                     # mouth slit
            f = bm.faces.new((v00, v01, v11, v10)); f.smooth = True
            f.material_index = band((ta + grid[r+1][q][1])/2, aa + math.pi/cols)
    return grid
g = skin("Head", 0.0, 0.2, 44, cols=80)
skin("BodyFront", 0.2, 0.46, 40, cols=80); skin("BodyMid", 0.46, 0.72, 34, cols=80); skin("BodyRear", 0.72, 1.0, 30, cols=64)
PIECE = "Head"
bm = PIECES["Head"]; dl = bm.verts.layers.deform.verify()                      # close the nose
ring = [v for v, t, a in g[0]]; tip = bm.verts.new(sp(0.0) + (sp(0.0) - sp(0.02)).normalized()*0.12)
tip[dl][BIDX["Head"]] = 1.0
jtip = bm.verts.new(sp(0.0) + (sp(0.0) - sp(0.02)).normalized()*0.1 + frame_at(0.0)[2]*(-0.2)); jtip[dl][BIDX["Jaw"]] = 1.0
for q in range(len(ring)):
    a_q = g[0][q][2]; a_n = g[0][(q + 1) % len(ring)][2]
    jq, jn = weights(0.0, a_q).get("Jaw", 0) > 0.5, weights(0.0, a_n).get("Jaw", 0) > 0.5
    if jq != jn: continue
    f = bm.faces.new((ring[(q + 1) % len(ring)], ring[q], jtip if jq else tip)); f.smooth = True; f.material_index = CREAM if jq else SLATE
for pn in ("Head", "BodyFront", "BodyMid", "BodyRear"):
    bmesh.ops.recalc_face_normals(PIECES[pn], faces=PIECES[pn].faces)

# ---------------- head detail (own piece) ----------------
PIECE = "HeadDetail"
# ---------------- mouth interior: roof, floor, gums, tongue, fang rows (visible when the jaw opens) ----------------
def mouth_strip(piece, bone_w, rows_pts, mi):
    """rows_pts: list of rows of world points; bone_w: weights dict for every vertex."""
    bm_ = PIECES.setdefault(piece, bmesh.new()); dl_ = bm_.verts.layers.deform.verify()
    grid_ = []
    for row in rows_pts:
        rv = []
        for p_ in row:
            v = bm_.verts.new(p_)
            for bn, wt in bone_w.items(): v[dl_][BIDX[bn]] = wt
            rv.append(v)
        grid_.append(rv)
    fs = []
    for r in range(len(grid_) - 1):
        for q in range(len(grid_[r]) - 1):
            f = bm_.faces.new((grid_[r][q], grid_[r][q+1], grid_[r+1][q+1], grid_[r+1][q])); f.smooth = True; f.material_index = mi; fs.append(f)
    bmesh.ops.recalc_face_normals(bm_, faces=fs)
AM = math.asin(MOUTH)
def mrow(t, roof):
    c, x, y, tg = frame_at(t); w = rad(t)
    yc = -0.2*w
    edgeR = surf(t, -AM + (0.03 if roof else -0.03), -0.015); edgeL = surf(t, math.pi + AM - (0.03 if roof else -0.03), -0.015)
    pts_ = [edgeR]
    for q in range(17):
        a = (q/16)*math.pi if roof else -(q/16)*math.pi
        pts_.append(c + x*(0.8*w*math.cos(a)) + y*(yc + (0.42 if roof else 0.25)*w*math.sin(a)))
    pts_.append(edgeL)
    return pts_
TS = [0.012 + 0.135*i/14 for i in range(15)]
mouth_strip("Head", {"Head": 1.0}, [mrow(t, True) for t in TS], MOUTHM)
mouth_strip("Head", {"Jaw": 1.0}, [mrow(t, False) for t in TS], MOUTHM)
# throat (back wall) + front palate wall
for t_, wts in ((TS[-1], {"Head": 1.0}),):
    rr = mrow(t_, True); rf = mrow(t_, False)
    mouth_strip("Head", wts, [rr, [frame_at(t_)[0] + frame_at(t_)[2]*(-0.2*rad(t_))]*len(rr)], DARK)
    mouth_strip("Head", {"Jaw": 1.0}, [rf, [frame_at(t_)[0] + frame_at(t_)[2]*(-0.2*rad(t_))]*len(rf)], DARK)
# tongue on the floor (Jaw)
c0, x0, y0, tg0 = frame_at(0.1); w0_ = rad(0.1)
loft("Jaw", TONGUE, [(0, .32*w0_, .1*w0_, 2), (0.35, .4*w0_, .12*w0_, 2), (1.1, .3*w0_, .1*w0_, 2), (1.35, .05, .04, 2)], N=16,
     M=_frame(frame_at(0.14)[0] + frame_at(0.14)[2]*(-0.38*rad(0.14)), sp(0.02) - sp(0.14), hint=(0, 0, 1)), sub=1)
# fang rows: upper (Head) point down, lower (Jaw) point up; biggest at the front
for s in (1, -1):
    for i in range(16):
        t = 0.018 + 0.125*i/15
        L_ = 0.34 - 0.2*(i/15)
        aU = (-AM + 0.05) if s > 0 else (math.pi + AM - 0.05)
        aD = (-AM - 0.05) if s > 0 else (math.pi + AM + 0.05)
        c_, x_, y_, tg_ = frame_at(t)
        pu = surf(t, aU, -0.05); pd = surf(t, aD, -0.05)
        inw = (c_ - pu); inw.z = 0; inw = inw.normalized()
        loft("Head", FANG, [(0, .045*(L_/0.34), .04*(L_/0.34), 2), (L_*0.6, .03*(L_/0.34), .028*(L_/0.34), 2), (L_, .003, .003, 2)], N=8,
             M=_frame(pu, -y_ + inw*0.25, hint=tuple(tg_)), sub=0)
        if i % 2 == 0:
            loft("Jaw", FANG, [(0, .04*(L_/0.34), .035*(L_/0.34), 2), (L_*0.5, .026*(L_/0.34), .024*(L_/0.34), 2), (L_*0.8, .003, .003, 2)], N=8,
                 M=_frame(pd, y_ + inw*0.25, hint=tuple(tg_)), sub=0)
    # eye: socket, lid ring, gold iris, dark pupil slit, heavy brow
    t, a = 0.125, (0.12 if s > 0 else math.pi - 0.12)
    p = surf(t, a); n = normal_at(t, a)
    Mf = _frame(p - n*0.05, n, hint=(0, 1, 0))
    loft("Head", DARK, [(0, .26, .2), (0.07, .25, .19), (0.09, .2, .15)], N=24, M=Mf, sub=1)
    loft("Head", SLATE, [(0.04, .3, .24), (0.1, .28, .22), (0.13, .23, .17)], N=24, M=Mf, sub=1, cap=False)   # lid
    sph("Head", EYE, tuple(p + n*0.0), 0.17, scale=(1, 1, 0.55), u=20, v=12, rot=tuple(n.to_track_quat('Z', 'Y').to_euler()))
    box("Head", DARK, None, (0.05, 0.22, 0.03), bev=0.012, segs=1, M=_frame(p + n*0.09, n, hint=(0, 0, 1)))      # slit pupil
    blade("Head", SLATE, tuple(p + n*0.1 + Vector((0, 0.12, 0.2))), tuple(Vector((0.2*s, -1, -0.12))), 0.7, 0.14, 0.07, hint=tuple(n), N=8)
# rostrum knobs (tubercles)
import random
rnd = random.Random(7)
for i in range(22):
    t = 0.015 + rnd.random()*0.12; a = math.pi/2 + (rnd.random() - 0.5)*1.6
    p = surf(t, a); n = normal_at(t, a); r = 0.06 + rnd.random()*0.05
    sph("Head", SLATE, tuple(p - n*(r*0.25)), r, u=10, v=6, scale=(1, 1, 0.55), rot=tuple(n.to_track_quat('Z', 'Y').to_euler()))
# blowhole: brass ring + twin glowing slits
t, a = 0.2, math.pi/2
p = surf(t, a); n = normal_at(t, a); Mb = _frame(p - n*0.03, n, hint=(0, 1, 0))
loft("Head", BRASS, [(0, .24, .17), (0.06, .25, .18), (0.08, .2, .13)], N=24, M=Mb, cap=False)
loft("Head", IRONM, [(0.0, .2, .13), (0.05, .2, .13)], N=24, M=Mb)
for s in (1, -1):
    loft("Head", GLOW, [(0.05, .03, .09), (0.07, .025, .08)], N=10, M=Mb @ Matrix.Translation((0.08*s, 0, 0)))
for i in range(10):
    a_ = i*2*math.pi/10
    sph("Head", BRASS, tuple(Mb @ Vector((0.245*math.cos(a_), 0.175*math.sin(a_), 0.07))), 0.02, u=6, v=4)
# aether gill vents: 4 recessed slits per flank behind the eye (dark lip + glowing core)
for s_ in (1, -1):
    for i in range(4):
        t = 0.205 + i*0.02; a0 = (0.08 if s_ > 0 else math.pi - 0.08)
        p = surf(t, a0); n = normal_at(t, a0); up = frame_at(t)[2]
        Mv = _frame(p - n*0.04, n, hint=tuple(frame_at(t)[3]))
        loft("Head", DARK, [(0, .28, .035), (0.06, .32, .05), (0.07, .26, .035)], N=12, M=Mv)
        loft("Head", GLOW, [(0.05, .24, .016), (0.075, .2, .012)], N=10, M=Mv)
# citadel head armour: riveted iron plate with brass rim across the rostrum, cyan crest gem
PIECE = "HeadArmour"
tb = bmesh.new(); rows_ = []
for r in range(9):
    t = 0.035 + 0.1*r/8
    row = []
    for q in range(13):
        a = math.pi/2 + (q/12 - 0.5)*1.25
        row.append(tb.verts.new(surf(t, a, 0.05)))
    rows_.append(row)
for r in range(8):
    for q in range(12):
        tb.faces.new((rows_[r][q], rows_[r][q+1], rows_[r+1][q+1], rows_[r+1][q]))
_add(tb, "Head", IRONM, Matrix(), True, 0, mods=[("SOLIDIFY", {"thickness": 0.05, "offset": 1})])
for r in (0, 8):
    for q in range(12):
        a0_ = math.pi/2 + (q/12 - 0.5)*1.25; a1_ = math.pi/2 + ((q + 1)/12 - 0.5)*1.25; t = 0.035 + 0.1*r/8
        tube("Head", BRASS, tuple(surf(t, a0_, 0.1)), tuple(surf(t, a1_, 0.1)), 0.03, 0.03, N=6)
for q in (0, 12):
    for r in range(8):
        a_ = math.pi/2 + (q/12 - 0.5)*1.25
        tube("Head", BRASS, tuple(surf(0.035 + 0.1*r/8, a_, 0.1)), tuple(surf(0.035 + 0.1*(r + 1)/8, a_, 0.1)), 0.03, 0.03, N=6)
for r in (1, 4, 7):
    for q in (1, 4, 8, 11):
        sph("Head", BRASS, tuple(surf(0.035 + 0.1*r/8, math.pi/2 + (q/12 - 0.5)*1.25, 0.105)), 0.03, u=8, v=4)
pc = surf(0.085, math.pi/2, 0.1); nc = normal_at(0.085, math.pi/2)
loft("Head", BRASS, [(0, .16, .16), (0.04, .17, .17), (0.06, .12, .12)], N=6, M=_frame(pc, nc, hint=(0, 1, 0)))
gem("Head", GLOW, tuple(pc + nc*0.07), 0.1, 0.09, rot=tuple(nc.to_track_quat('Z', 'Y').to_euler()), sides=6)
# harness chains: sagging loops hanging under the belly from each strap
PIECE = "Harness"
for t_ in (0.358, 0.498, 0.638):
    bnh = f"Spine{int(t_*NS) + 1:02d}"
    for s_ in (1, -1):
        a0_ = -math.pi/2 + 0.55*s_
        A = surf(t_, a0_, 0.06); B = surf(t_ + 0.05, -math.pi/2 + 0.2*s_, 0.06)
        for li in range(10):
            u = li/9; p_ = A.lerp(B, u) + Vector((0, 0, -0.55*math.sin(u*math.pi)))
            Mc = _frame(p_, B - A, hint=(0, 0, 1)) @ Matrix.Rotation((li % 2)*math.pi/2, 4, 'Z')
            loft(bnh, IRONM, [(-0.07, .035, .06), (0.07, .035, .06)], N=10, M=Mc, cap=False)
# ---------------- jaw lip + chin barnacle beard ----------------
PIECE = "Head"
for i in range(16):
    t = 0.02 + rnd.random()*0.12; a = -math.pi/2 + (rnd.random() - 0.5)*1.2
    p = surf(t, a); n = normal_at(t, a)
    loft("Jaw", BARN, [(0, .05, .05), (0.07, .035, .035), (0.08, .02, .02)], N=8, M=_frame(p - n*0.02, n))
# ---------------- dorsal ridge plates + dorsal hump fin ----------------
PIECE = "BodyMid"
for i in range(9):
    t = 0.5 + i*0.035; a = math.pi/2
    p = surf(t, a); n = normal_at(t, a)
    blade(f"Spine{int(t*NS) + 1:02d}", SLATE, tuple(p - n*0.02), tuple(n + Vector((0, 0.8, 0))), 0.22 - 0.01*i, 0.12, 0.05, hint=(1, 0, 0), N=6)
t = 0.68; p = surf(t, math.pi/2); n = normal_at(t, math.pi/2)
blade("Spine07", SLATE, tuple(p - n*0.05), tuple(n*1.0 + Vector((0, 0.9, 0))), 0.9, 0.35, 0.12, hint=(1, 0, 0), N=10)

# ---------------- pectoral fins: long humpback fins with tubercle scallops, cream undersides ----------------
PIECE = "Fins"
for side, s in (("L", 1), ("R", -1)):
    PIECE = "Fin" + side
    t0 = 0.24; a0 = (-0.45 if s > 0 else math.pi + 0.45)
    root = surf(t0, a0, -0.1)
    axis = Vector((0.85*s, 0.45, -0.3)).normalized(); Lf = 7.0
    j1 = root + axis*Lf*0.35; j2 = j1 + (axis + Vector((0.05*s, 0.15, -0.05))).normalized()*Lf*0.35
    tip = j2 + (axis + Vector((0.1*s, 0.35, -0.02))).normalized()*Lf*0.3
    add_bone(f"Pec{side}1", root, j1, "Spine03"); add_bone(f"Pec{side}2", j1, j2, f"Pec{side}1"); add_bone(f"Pec{side}3", j2, tip, f"Pec{side}2")
    for k_, (a_, b_, w0, w1, bn) in enumerate(((root, j1, 0.72, 0.74, f"Pec{side}1"), (j1, j2, 0.74, 0.56, f"Pec{side}2"), (j2, tip, 0.56, 0.05, f"Pec{side}3"))):
        Mf = _frame(a_, b_ - a_, hint=(0, 0, 1)); Ls = (b_ - a_).length
        secs = [(-0.06 if k_ else 0, w0, .13 - k_*0.03, 2.4), (Ls*0.5, (w0 + w1)/2*1.02, .11 - k_*0.03, 2.4), (Ls + (0.06 if k_ < 2 else 0), w1, .09 - k_*0.03, 2.4)]
        loft(bn, BLUE, secs, N=24, M=Mf, keep=lambda c: c.y >= -0.005, fill=False, sub=1)
        loft(bn, CREAM, [(z, w*0.995, h*0.995, n_) for z, w, h, n_ in secs], N=24, M=Mf, keep=lambda c: c.y < 0.005, fill=False, sub=1)
        for q in range(7):                                  # tubercles on the leading edge
            u = (q + 0.5)/7
            lead = Mf @ Vector((-(w0 + (w1 - w0)*u)*0.97*s*(-1 if s > 0 else 1)*(-1), 0, Ls*u))
            lead = Mf @ Vector((-(w0 + (w1 - w0)*u)*0.97, 0, Ls*u))
            sph(bn, SLATE, tuple(lead), 0.065*(1 - 0.3*k_), scale=(1, 0.8, 1), u=10, v=6)
# fin detail: brass cuff + rivets at the root, barnacle clusters, pale scar patches, scalloped trailing edge
for side, s_ in (("L", 1), ("R", -1)):
    PIECE = "Fin" + side
    b1 = BONES[BIDX[f"Pec{side}1"]]; b2 = BONES[BIDX[f"Pec{side}2"]]; b3 = BONES[BIDX[f"Pec{side}3"]]
    r_, j1_, j2_, tp_ = Vector(b1[1]), Vector(b1[2]), Vector(b2[2]), Vector(b3[2])
    Mr = _frame(r_ + (j1_ - r_)*0.3, j1_ - r_, hint=(0, 0, 1))
    loft(f"Pec{side}1", BRASS, [(0, .78, .2, 2.4), (0.18, .78, .2, 2.4)], N=28, M=Mr, cap=False)
    for q in range(14):
        a_ = q*2*math.pi/14
        sph(f"Pec{side}1", BRASS, tuple(Mr @ Vector((0.79*math.cos(a_), 0.21*math.sin(a_), 0.09))), 0.025, u=6, v=4)
    for bn, A_, B_, wA, wB in ((f"Pec{side}1", r_, j1_, 0.72, 0.74), (f"Pec{side}2", j1_, j2_, 0.74, 0.56), (f"Pec{side}3", j2_, tp_, 0.56, 0.05)):
        Mf = _frame(A_, B_ - A_, hint=(0, 0, 1)); Ls = (B_ - A_).length
        for q in range(6):                                                      # scalloped trailing edge
            u = (q + 0.5)/6; w_ = wA + (wB - wA)*u
            blade(bn, SLATE, tuple(Mf @ Vector((w_*0.92, 0, Ls*u))), tuple(Mf.to_3x3() @ Vector((1, 0, 0.35))), 0.16*(1 - 0.5*u), 0.1, 0.03,
                  hint=tuple(Mf.to_3x3() @ Vector((0, 1, 0))), N=6, sub=0)
        for q in range(3):                                                      # pale scar patches on the top
            u = 0.2 + 0.3*q; w_ = (wA + (wB - wA)*u)*0.3*((q % 2)*2 - 1)
            sph(bn, CREAMD, tuple(Mf @ Vector((w_, 0.075 - 0.02*(bn[-1] == "3"), Ls*u))), 0.11*(1 - 0.3*(bn[-1] == "3")), scale=(1.6, 0.25, 1), u=12, v=6)
    M2 = _frame(j1_, j2_ - j1_, hint=(0, 0, 1)); up2 = (M2.to_3x3() @ Vector((0, 1, 0))).normalized()
    for jp, bn, (Aj, Bj), w_ in ((j1_, f"Pec{side}2", (r_, j2_), 0.72), (j2_, f"Pec{side}3", (j1_, tp_), 0.55)):
        Mj_ = _frame(jp, Bj - Aj, hint=(0, 0, 1))
        sph(bn, BLUE, tuple(jp), 1.0, scale=(w_*1.02, 0.1, 0.3), u=20, v=8, rot=tuple(Mj_.to_3x3().to_euler()))       # joint blend
    for c_ in range(6):                                                         # barnacle cluster on top of the fin
        p_ = M2 @ Vector((0.18*math.cos(c_*1.1), 0.08, 0.25 + 0.12*math.sin(c_*1.1)))
        loft(f"Pec{side}2", BARN, [(0, .07, .07), (0.1, .045, .045), (0.12, .03, .03)], N=8, M=_frame(p_, up2), cap=False)
        loft(f"Pec{side}2", DARK, [(0.09, .03, .03), (0.11, .025, .025)], N=8, M=_frame(p_, up2))
PIECE = "Fluke"
# ---------------- fluke: wide notched tail with scalloped trailing edge ----------------
PIECE = "Fluke"
c1, x1, y1, tg1 = frame_at(1.0)
outline = []
for s in (-1, 1):
    pts2 = [(0.0, -0.15), (0.9, 0.05), (1.8, 0.5), (2.6, 1.15), (2.9, 1.55), (2.65, 1.7)]
    trail = []
    for q in range(9):                                       # scalloped trailing edge back to the notch
        u = q/8; x_ = 2.65*(1 - u) + 0.12*u; y_ = 1.7*(1 - u) + 1.0*u + 0.1*math.sin(u*math.pi*6)
        trail.append((x_, y_))
    half = pts2 + trail
    if s < 0: outline += [(-x_, y_) for x_, y_ in reversed(half)]
    else: outline += half
tb = bmesh.new()
vs = [tb.verts.new(c1 + x1*x_ + tg1*y_*1.0 - tg1*0.1) for x_, y_ in outline]
tb.faces.new(vs)
bmesh.ops.triangulate(tb, faces=tb.faces)
_add(tb, "Fluke", SLATE, Matrix(), True, 0, mods=[("SOLIDIFY", {"thickness": 0.18, "offset": 0}), ("SUBSURF", {"levels": 1, "render_levels": 1})])
tube("Fluke", CREAM, tuple(c1 - tg1*0.1), tuple(c1 + tg1*0.7), 0.16, 0.08, N=12)

# ---------------- turbine engines strapped on with riveted harness bands ----------------
PIECE = "Turbines"
for i, (t, a) in enumerate(((0.33, math.pi/2 + 0.42), (0.47, math.pi/2 - 0.42), (0.61, math.pi/2 + 0.3))):
    p = surf(t, a); n = normal_at(t, a); tg = frame_at(t)[3]
    bn = f"Turbine{i+1}"; PIECE = bn
    ctr = p + n*0.62
    add_bone(bn, ctr - tg*0.4, ctr + tg*0.4, f"Spine{int(t*NS) + 1:02d}")
    Mt = _frame(ctr - tg*0.75, tg, hint=tuple(n))                      # engine axis runs along the body (intake forward)
    loft(bn, BRASS, [(0, .5, .5), (0.12, .56, .56), (1.1, .54, .54), (1.35, .42, .42), (1.5, .34, .34)], N=32, M=Mt, cap=False, sub=1)   # cowl
    loft(bn, IRONM, [(0.02, .47, .47), (1.45, .31, .31)], N=32, M=Mt, cap=False)                                                         # liner
    for r_ in range(16):                                                                                                               # cowl ribs
        a_ = r_*2*math.pi/16
        tube(bn, BRASS, tuple(Mt @ Vector((0.565*math.cos(a_), 0.565*math.sin(a_), 0.15))), tuple(Mt @ Vector((0.55*math.cos(a_), 0.55*math.sin(a_), 1.08))), 0.018, 0.018, N=5)
    for rr, z_ in ((0.57, 0.1), (0.555, 1.1)):
        for r_ in range(20):
            a_ = r_*2*math.pi/20
            sph(bn, BRASS, tuple(Mt @ Vector((rr*math.cos(a_), rr*math.sin(a_), z_))), 0.018, u=6, v=4)
    loft(bn, BRASS, [(0.1, .12, .12), (0.25, .1, .1), (0.35, .02, .02)], N=16, M=Mt, sub=1)                                            # spinner
    for b_ in range(10):                                                                                                               # fan blades
        a_ = b_*2*math.pi/10
        blade(bn, IRONM, tuple(Mt @ Vector((0.08*math.cos(a_), 0.08*math.sin(a_), 0.22))), tuple(Mt.to_3x3() @ Vector((math.cos(a_ + 0.3), math.sin(a_ + 0.3), 0.15))),
              0.38, 0.1, 0.015, hint=tuple(Mt.to_3x3() @ Vector((0, 0, 1))), N=6, sub=0)
    loft(bn, GLOW, [(1.3, .3, .3), (1.42, .28, .28)], N=24, M=Mt, cap=False)                                                         # exhaust glow ring
    loft(bn, GLOW, [(1.2, .16, .16), (1.4, .05, .05)], N=16, M=Mt)                                                                   # exhaust core
    for s in (1, -1):                                                                                                                  # pylons
        tube(bn, IRONM, tuple(surf(t + 0.012*s, a) + n*0.02), tuple(Mt @ Vector((0, -0.5, 0.55 + 0.3*s))), 0.07, 0.05, N=8)
    # harness: wide riveted iron strap wrapped around the body at this station, brass buckle plate under the engine
    PIECE = "Harness"
    tt = t + 0.028; bnh = f"Spine{int(tt*NS) + 1:02d}"
    tb = bmesh.new(); rows_ = []
    for q in range(49):
        a_ = -math.pi/2 + 2*math.pi*q/48
        nq = normal_at(tt, a_); tgq = frame_at(tt)[3]
        base = surf(tt, a_, 0.02)
        rows_.append([tb.verts.new(base - tgq*0.13), tb.verts.new(base + tgq*0.13), tb.verts.new(base + tgq*0.13 + nq*0.045), tb.verts.new(base - tgq*0.13 + nq*0.045)])
    for q in range(48):
        for e in range(4):
            tb.faces.new((rows_[q][e], rows_[q+1][e], rows_[q+1][(e + 1) % 4], rows_[q][(e + 1) % 4]))
    _add(tb, bnh, IRONM, Matrix(), True, 0)
    for q in range(0, 48, 3):
        a_ = -math.pi/2 + 2*math.pi*q/48; nq = normal_at(tt, a_); tgq = frame_at(tt)[3]
        for e in (-1, 1):
            sph(bnh, BRASS, tuple(surf(tt, a_, 0.065) + tgq*0.085*e), 0.022, u=6, v=4)
    box(bnh, BRASS, None, (0.34, 0.34, 0.05), bev=0.02, segs=1, M=_frame(surf(tt, a, 0.07), normal_at(tt, a), hint=tuple(frame_at(tt)[3])))
# ---------------- barnacle pod clusters (P1 breakables, dropped onto the dock) ----------------
PIECE = "Pods"
for i in range(6):
    t = 0.28 + i*0.075; a = (0.35 if i % 2 else math.pi - 0.35) + (0.25 if i > 2 else 0)
    p = surf(t, a); n = normal_at(t, a)
    bn = f"Pod{i+1}"; add_bone(bn, p, p + n*0.5, f"Spine{int(t*NS) + 1:02d}")
    sph(bn, BARN, tuple(p), 0.3, scale=(1, 1, 0.55), u=16, v=8)
    for c_ in range(7):
        ang = c_*2*math.pi/7
        off = Vector((math.cos(ang), math.sin(ang), 0))*0.2
        Mp = _frame(p + (_frame(p, n).to_3x3() @ off), n)
        loft(bn, BARN, [(0, .09, .09), (0.14, .065, .065), (0.17, .045, .045)], N=10, M=Mp, sub=0, cap=False)
        loft(bn, DARK, [(0.13, .045, .045), (0.16, .035, .035)], N=10, M=Mp)
    loft(bn, BARN, [(0, .12, .12), (0.24, .08, .08), (0.28, .055, .055)], N=12, M=_frame(p, n), cap=False)
    sph(bn, GLOW, tuple(p + n*0.26), 0.05, u=10, v=6)
rig, PARTS = assemble(NAME, OFFSET, glow_ids=[GLOW, EYE])
import os as _os
if _os.environ.get("POSE") == "bite":
    pb = rig.pose.bones["Jaw"]; pb.rotation_mode = 'XYZ'; best = None
    for sg in (1, -1):
        pb.rotation_euler = (0.55*sg, 0, 0); bpy.context.view_layer.update()
        z = (rig.matrix_world @ pb.tail).z
        if best is None or z < best[0]: best = (z, sg)
    pb.rotation_euler = (0.55*best[1], 0, 0); bpy.context.view_layer.update()
