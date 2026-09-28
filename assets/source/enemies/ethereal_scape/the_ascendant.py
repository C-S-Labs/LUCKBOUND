# LUCKBOUND - Ethereal Scape BOSS: The Ascendant (the Sanctum). ~3.5 m (crown tip), ~1.9x a Roblox player.
# A temple guardian MID-TRANSFIGURATION: a tall, slender ivory-and-gold form whose extremities have already turned to
# raw sky crystal lit from inside by portal glow -- crystal forearms and hands, crystal shins and feet, a crystal crown
# breaking out of the back of the skull, crystal shards shedding off the robe hem and pauldrons. It is the end point
# of the biome's transfiguration motif (ROSTER.md "Design language"): the Acolyte's hands and hem have started to
# turn; the Ascendant is nearly through.
#   Face : smooth faceless GOLD MASK split by a vertical portal-glow slit (no hood, no halo).
#   Cloak: a front-slit robe built as TWO overlapping panels (the Temple Acolyte's technique), each rigged from the
#          waist to its own thigh, so the legs stride through the slit without dragging a closed tube. Ivory outside,
#          indigo lining (shows through the slit), gold trim, crystal shards at the hem.
#   Ribbons: mint/teal ribbons trailing off the back of the mantle, ending in portal glow.
# Phase 2: the ivory cuirass (piece "Breakaway") bursts off, exposing the crystal-veined inner torso and its
# portal core (VFX_Core). See ASCENDANT_MOVESET.md.
# Pieces follow the humanoid profile's clip names (Torso/Waist/LegLeft/LegRight vs ArmLeft/ArmRight + Staff) so
# pose_fix / anim_core can scan every action. Weapon: the_ascendant_staff.py (a Staff, WEAPONS.md) (manifest "extras").
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "TheAscendant"; OFFSET = (0.0, 0.0, 0.0)
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Torso"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
V = Vector
MATS = [mat("AS_Ivory", (0.93, 0.90, 0.82), 0.0, 0.25), mat("AS_Gold", (0.87, 0.70, 0.38), 1.0, 0.18),
        mat("AS_Crystal", (0.50, 0.80, 1.0), 0.0, 0.04, (0.42, 0.78, 1.0), 1.1), mat("AS_Teal", (0.16, 0.52, 0.46), 0.0, 0.3),
        mat("AS_Indigo", (0.30, 0.32, 0.58), 0.0, 0.35), mat("AS_Portal", (0.8, 1.0, 0.9), 0.0, 0.2, (0.55, 1.0, 0.8), 3.0),
        mat("AS_Mint", (0.55, 0.88, 0.74), 0.0, 0.3)]
IVO, GOLD, CRYST, TEAL, INDIGO, GLOW, MINT = range(7)
PATINA, BRONZE, IRON, IVORY, CLOTH = IVO, GOLD, CRYST, IVO, INDIGO     # enemy_kit's default names
ANCHOR_PREFIXES = ("VFX_",)                                            # export.py pins these so Studio keeps them

# ---------------- skeleton (R15 names + neck + fingers + sockets). Faces -Y, +X is its left. ----------------
def B(n, h, t, p): add_bone(n, h, t, p)
B("HumanoidRootNode", (0, 0, 1.62), (0, 0, 1.76), None)
B("LowerTorso", (0, 0, 1.70), (0, 0, 2.02), "HumanoidRootNode")
B("UpperTorso", (0, 0, 2.02), (0, 0, 2.76), "LowerTorso")
B("Neck", (0, 0, 2.72), (0, 0, 2.86), "UpperTorso")
B("Head", (0, 0, 2.86), (0, 0, 3.28), "Neck")
B("VFX_Core", (0, -0.2, 2.38), (0, -0.36, 2.38), "UpperTorso")
B("VFX_Eye", (0, -0.15, 3.05), (0, -0.3, 3.05), "Head")
J = {}
for side, s in (("Left", 1), ("Right", -1)):
    j = J[side] = dict(sh=V((0.43*s, 0.02, 2.62)), el=V((0.47*s, 0.04, 2.06)), wr=V((0.50*s, 0.0, 1.54)), hd=V((0.50*s, -0.02, 1.30)),
                       hp=V((0.16*s, 0.0, 1.72)), kn=V((0.18*s, -0.02, 0.96)), an=V((0.19*s, 0.02, 0.17)), toe=V((0.19*s, -0.30, 0.05)))
    B(f"{side}UpperArm", j["sh"], j["el"], "UpperTorso"); B(f"{side}LowerArm", j["el"], j["wr"], f"{side}UpperArm")
    B(f"{side}Hand", j["wr"], j["hd"], f"{side}LowerArm")
    B(f"{side}UpperLeg", j["hp"], j["kn"], "LowerTorso"); B(f"{side}LowerLeg", j["kn"], j["an"], f"{side}UpperLeg")
    B(f"{side}Foot", j["an"], j["toe"], f"{side}LowerLeg")
    hdir = (j["hd"] - j["wr"]).normalized(); med = V((-s, 0, 0))
    B(f"VFX_Palm{side[0]}", j["wr"] + hdir*0.12 + med*0.04, j["wr"] + hdir*0.12 + med*0.12, f"{side}Hand")
    for fn, yy in (("Index", -0.045), ("Middle", -0.015), ("Ring", 0.015), ("Pinky", 0.043)):
        p0 = j["hd"] + V((0, yy, 0.03)); p1 = p0 + V((0, 0, -0.085)); p2 = p1 + V((-0.006*s, 0, -0.07))
        B(f"{side}{fn}1", p0, p1, f"{side}Hand"); B(f"{side}{fn}2", p1, p2, f"{side}{fn}1")
    t0 = j["wr"] + V((-0.02*s, -0.05, -0.07)); t1 = t0 + V((0, -0.04, -0.05)); t2 = t1 + V((0, -0.02, -0.05))
    B(f"{side}Thumb1", t0, t1, f"{side}Hand"); B(f"{side}Thumb2", t1, t2, f"{side}Thumb1")
# Weapon_R rests IN the right palm (pose_fix seat: 0.165 m down the hand, one palm-half + haft radius medial), pointing
# forward. Grips then only ever rotate it (Roblox mishandles animated bone translation).
_wr, _hd = J["Right"]["wr"], J["Right"]["hd"]
_wh = _wr + (_hd - _wr).normalized()*0.165 + V((1, 0, 0))*(0.06 + 0.047 + 0.004)
B("Weapon_R", _wh, _wh + V((0, -0.26, 0)), "RightHand")

# ---------------- helpers (this boss only) ----------------
def seg_loft(bone, mi, a, c, radii, N=16, sub=1, smooth=True, n=2.0, hint=(0, 1, 0)):
    """Loft along a->c; radii = [(fraction, rx, ry)]."""
    a, c = V(a), V(c); d = c - a; L = d.length
    loft(bone, mi, [(f*L, rx, ry, n) for f, rx, ry in radii], N=N, M=_frame(a, d, hint), sub=sub, smooth=smooth)
def crystal(bone, loc, d, r, h, sides=5, mi=CRYST, wfn=None):
    """Faceted crystal shard at loc pointing along world d (base sunk 40% of h below loc)."""
    d = V(d).normalized(); q = V((0, 0, 1)).rotation_difference(d)
    tb = bmesh.new()
    top = tb.verts.new((0, 0, h)); bot = tb.verts.new((0, 0, -h*0.4))
    ring = [tb.verts.new((r*math.cos(a), r*math.sin(a), 0)) for a in [i*2*math.pi/sides for i in range(sides)]]
    for i in range(sides):
        a_, b_ = ring[i], ring[(i + 1) % sides]; tb.faces.new((a_, b_, top)); tb.faces.new((b_, a_, bot))
    _add(tb, bone, mi, Matrix.Translation(V(loc)) @ q.to_matrix().to_4x4(), smooth=False, wfn=wfn)
def facet_ball(bone, mi, loc, r, scale=(1, 1, 1)):
    tb = bmesh.new(); bmesh.ops.create_icosphere(tb, subdivisions=1, radius=r)
    bmesh.ops.scale(tb, vec=scale, verts=tb.verts)
    _add(tb, bone, mi, Matrix.Translation(V(loc)), smooth=False)
def ring_at(bone, mi, c, d, r, w=0.02, t=0.012, N=24):
    """Flat band (collar / cuff) of radius r around axis d through c."""
    loft(bone, mi, [(-w/2, r + t, r + t), (w/2, r + t, r + t)], N=N, M=_frame(V(c), V(d)), cap=False)
def vein(bone, pts, r=0.006):
    """Portal-glow crack line through world points."""
    for a, b in zip(pts, pts[1:]): tube(bone, GLOW, tuple(a), tuple(b), r, r, N=5)
    for q in pts[1:-1]: sph(bone, GLOW, tuple(q), r*1.05, u=5, v=4)

# ================= TORSO (inner body: shown whole in phase 2) =================
PIECE = "Torso"
TORSO = [(2.00, .17, .13), (2.15, .20, .145), (2.35, .26, .17), (2.52, .30, .18), (2.64, .29, .16), (2.72, .20, .12), (2.80, .10, .09)]
loft("UpperTorso", IVO, [(z, rx, ry, 2.3) for z, rx, ry in TORSO], N=24, sub=1)
# portal core in the sternum, set in a gold ring, crystal veins radiating out (P2 read; P1 sees it through the cuirass slit)
core = V((0, -0.172, 2.38))
sph("UpperTorso", GLOW, core, 0.055, scale=(1, 0.7, 1.25), u=16, v=10)
loft("UpperTorso", GOLD, [(-0.012, .075, .09), (0.012, .075, .09), (0.012, .058, .072), (-0.012, .058, .072)], N=20, M=TR(core + V((0, -0.005, 0)), (math.pi/2, 0, 0)))
for a in (0.5, 1.3, 1.85, 2.65, 3.6, 4.4, 5.3):
    d = V((math.cos(a)*0.95, 0, math.sin(a)*1.1))
    vein("UpperTorso", [core + V((d.x*0.07, -0.005, d.z*0.07)), core + V((d.x*0.15, 0.025, d.z*0.16)),
                        core + V((d.x*0.23 + 0.02*math.sin(3*a), 0.07, d.z*0.25))], r=0.007)
for s in (1, -1):                                                     # crystal breaking out of the flanks
    for z, rr, hh in ((2.18, .03, .10), (2.28, .035, .13), (2.40, .03, .09)):
        rx = 0.2 + (z - 2.15)*0.3
        crystal("UpperTorso", (rx*s*0.98, 0.03, z), (s, 0.25, 0.35), rr, hh)

# ================= CUIRASS (phase-1 armour, sheds in P2_Transition) =================
BREAK = True
CUI = [(2.08, .205, .165), (2.22, .235, .18), (2.40, .29, .205), (2.55, .325, .21), (2.66, .31, .19), (2.72, .24, .15)]
loft("UpperTorso", IVO, [(z, rx, ry, 2.4) for z, rx, ry in CUI], N=28, sub=1, cap=False)
for z, rx, ry in (CUI[0], CUI[-1]):
    loft("UpperTorso", GOLD, [(z - 0.012, rx + .012, ry + .012, 2.4), (z + 0.012, rx + .012, ry + .012, 2.4)], N=28, cap=False)
# gold sternum ridge split by the portal slit (the mask's motif carried into the armour)
for s in (1, -1):
    loft("UpperTorso", GOLD, [(2.12, .018, .02), (2.40, .022, .025), (2.66, .016, .02)], N=8,
         M=TR((0.035*s, -0.198, 0), (0.06, 0, 0)))
box("UpperTorso", GLOW, (0, -0.205, 2.38), (0.02, 0.02, 0.44), bev=0.006, segs=1)
def _cui(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(CUI, CUI[1:]):
        if z0 <= z <= z1:
            t = (z - z0)/(z1 - z0); return a0 + (a1 - a0)*t, b0 + (b1 - b0)*t
    return CUI[-1][1:]
def _on_cui(x_frac, z, lift=0.006):      # point on the cuirass front at x = x_frac * half-width
    rx, ry = _cui(z); x = x_frac*rx; y = -ry*math.sqrt(max(0.0, 1 - x_frac**2)) - lift
    return V((x, y*1.02, z))
for s in (1, -1):                        # gold filigree: two sweeping lines from the shoulders down into the slit
    for off in (0.0, 0.12):
        pts = [_on_cui(s*(0.86 - off - 0.8*t), 2.66 - off*0.4 - 0.5*t**1.3) for t in [i/9 for i in range(10)]]
        for q0, q1 in zip(pts, pts[1:]): tube("UpperTorso", GOLD, tuple(q0), tuple(q1), 0.011, 0.011, N=6)
        for q in pts[1:-1]: sph("UpperTorso", GOLD, tuple(q), 0.0112, u=6, v=4)
    crystal("UpperTorso", _on_cui(s*0.93, 2.3, -0.01), (s*0.9, -0.3, 0.25), 0.03, 0.12)       # crystal breaking the plate edge
    crystal("UpperTorso", _on_cui(s*0.95, 2.2, -0.01), (s*0.9, -0.1, -0.1), 0.025, 0.09)
BREAK = False

# ================= MANTLE: stand-up gold collar (open at the front) + layered pauldrons =================
PIECE = "Mantle"
arc_band("UpperTorso", GOLD, (0, 0.01), 2.70, 2.88, (.22, .17), (.28, .23), -math.pi/2 + 0.6, 3*math.pi/2 - 0.6, 0.018, 22)
arc_band("UpperTorso", IVO, (0, 0.01), 2.70, 2.83, (.205, .155), (.25, .2), -math.pi/2 + 0.66, 3*math.pi/2 - 0.66, 0.02, 22)
for side, s in (("Left", 1), ("Right", -1)):
    sh = J[side]["sh"]; bn = f"{side}UpperArm"
    for i in range(2):
        c = V((sh.x + (0.02 + 0.05*i)*s, 0.015, sh.z + 0.06 - 0.09*i)); r = 0.2 - 0.025*i; tilt = (0.35 + 0.2*i)*s
        sph(bn, IVO, c, r, scale=(1.2, 0.95, 0.42), cut_below=0.0, u=28, v=10, rot=(0, tilt, 0))
        loft(bn, GOLD, [(0, r*1.2 + .004, r*0.95 + .004), (0.016, r*1.2 + .004, r*0.95 + .004)], N=28,
             M=Matrix.Translation(c) @ Matrix.Rotation(tilt, 4, 'Y'), cap=False)
        edge = c + V((math.cos(tilt)*r*1.15*s, 0, -math.sin(tilt)*r*1.15*s))
        for dy, h in ((-0.09, 0.12), (0.0, 0.17), (0.09, 0.11)):
            crystal(bn, edge + V((0, dy, 0.0)), (s, 0.2*dy/0.09, -0.35 - 0.2*i), 0.03, h*(1 - 0.25*i))
    crystal(bn, sh + V((0.08*s, 0.06, 0.16)), (0.25*s, 0.3, 1.0), 0.04, 0.24)
    crystal(bn, sh + V((0.16*s, 0.0, 0.12)), (0.6*s, 0.1, 1.0), 0.032, 0.16)

# ================= HEAD: neck, gold mask, portal slit, crystal crown breaking out of the skull =================
PIECE = "Head"
tube("Neck", IVO, (0, 0.0, 2.70), (0, -0.005, 2.93), 0.085, 0.075, N=14)
for z in (2.80, 2.86):
    ring_at("Neck", GOLD, (0, -0.003, z), (0, 0, 1), 0.074, w=0.018, t=0.008, N=16)
HC = V((0, -0.01, 3.06))
sph("Head", GOLD, HC, 0.16, scale=(0.78, 0.92, 1.32), u=28, v=18)
box("Head", GLOW, (0, -0.151, 3.05), (0.016, 0.02, 0.25), bev=0.006, segs=1)                    # the portal slit
for s in (1, -1):                                                                                     # raised slit lips
    loft("Head", GOLD, [(2.91, .007, .008), (3.05, .01, .012), (3.19, .006, .008)], N=6, M=TR((0.017*s, -0.146, 0)))
loft("Head", GOLD, [(-0.012, .122, .145), (0.012, .122, .145)], N=28, M=TR(HC + V((0, 0.0, 0.1)), (-0.35, 0, 0)), cap=False)   # circlet
for sx in (1, -1):                            # swept-back crystal horns growing out of the temples, hugging the skull
    for i, (h, r, dz, dy) in enumerate(((0.34, .038, 0.02, 0.0), (0.24, .03, -0.05, 0.03), (0.16, .024, -0.11, 0.05))):
        base = HC + V((0.1*sx, 0.02 + dy, 0.08 + dz))
        crystal("Head", base, (0.35*sx, 1.0, 0.28 - 0.12*i), r, h, sides=5)
for i in range(6):                            # a cascade of shards down the back of the head to the collar
    z = 0.12 - 0.06*i; x = 0.035*((-1)**i)*(1 + 0.3*i)
    crystal("Head", HC + V((x, 0.115 - 0.004*i, z)), (x*3, 1.0, -0.35 - 0.12*i), 0.028 - 0.002*i, 0.2 - 0.015*i, sides=5)
# two mint ribbons tied off the back of the circlet
PIECE = "Ribbons"
def ribbon(bone, pts, w0, w1, t=0.012, tip=0.18, mi=TEAL):
    """Flat ribbon along world pts (width across the path's horizontal normal); last `tip` of it is portal glow."""
    tb = bmesh.new(); n = len(pts); rows = []
    L = sum((b - a).length for a, b in zip(pts, pts[1:])); acc = 0.0; mats = []
    for i, p in enumerate(pts):
        if i: acc += (p - pts[i - 1]).length
        d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross(V((0, 0, 1))); side = side.normalized() if side.length > 1e-3 else V((1, 0, 0))
        nrm = side.cross(d).normalized(); w = w0 + (w1 - w0)*acc/L
        rows.append([tb.verts.new(p + side*w*sx + nrm*t*sy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        mats.append(GLOW if acc/L > 1 - tip else None)
    for i, (r0, r1) in enumerate(zip(rows, rows[1:])):
        for k in range(4):
            f = tb.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k])); f.material_index = mi if mats[i + 1] is None else GLOW
    tb.faces.new(rows[0]); tb.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
    for f in tb.faces: f.smooth = True
    _add(tb, bone, None)
for s in (1, -1):                                                     # longer teal ribbons off the back of the mantle
    c0 = V((0.13*s, 0.155, 2.68))
    ribbon("UpperTorso", [c0 + V((0.035*s*i + 0.004*s*i*i, 0.05*i + 0.007*i*i, -0.13*i)) for i in range(8)], 0.055, 0.025)
    c1 = V((0.09*s, 0.172, 1.95))
    ribbon("LowerTorso", [c1 + V((0.012*s*i, 0.035*i + 0.006*i*i + 0.012, -0.12*i)) for i in range(7)], 0.04, 0.02, mi=MINT)

# ================= ARMS: ivory sleeves turning to crystal forearms and hands =================
for side, s in (("Left", 1), ("Right", -1)):
    PIECE = "Arm" + side
    j = J[side]; sh, el, wr, hd = j["sh"], j["el"], j["wr"], j["hd"]
    ua, la, hb = f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"
    seg_loft(ua, IVO, sh + (el - sh)*0.12, el, [(0, .09, .09), (0.25, .1, .098), (0.65, .086, .085), (1.0, .072, .072)], N=16)
    ring_at(ua, GOLD, sh.lerp(el, 0.93), el - sh, 0.072, w=0.03, t=0.012, N=16)
    u = (el - sh).normalized(); o = V((s, 0.0, 0.0)); o = (o - u*o.dot(u)).normalized(); f_ = u.cross(o)
    for k_, ang in enumerate((-0.6, 0.4, 1.4)):                     # glow cracks creeping UP the sleeve from the elbow
        rad = lambda t: 0.086 + (0.072 - 0.086)*(t - 0.65)/0.35 + 0.003
        pts = []
        for i, t in enumerate((0.9, 0.8, 0.7, 0.6 - 0.04*k_)):
            a = ang + 0.25*math.sin(3*i + k_)
            pts.append(sh.lerp(el, t) + (o*math.cos(a) + f_*math.sin(a))*rad(t))
        vein(ua, pts, 0.0055)
    facet_ball(la, CRYST, el, 0.074)                                  # crystal elbow
    seg_loft(la, CRYST, el, wr, [(0, .088, .088), (0.5, .092, .088), (1.0, .062, .06)], N=6, sub=0, smooth=False)
    # ivory shell fragment still clinging to the outer forearm, gold broken edge
    fa = (wr - el).normalized(); M = _frame(el, wr - el)
    loft(la, IVO, [(0.05, .095, .095), (0.2, .096, .094), (0.26, .092, .09)], N=14, M=M, sub=0, cap=False)
    ring_at(la, GOLD, el + fa*0.26, fa, 0.09, w=0.014, t=0.008, N=14)
    for (t, a, h, rr) in ((0.42, 0.3, 0.2, .035), (0.5, 2.0, 0.15, .03), (0.6, -0.9, 0.22, .036), (0.72, 1.1, 0.14, .028),
                          (0.58, 3.5, 0.16, .03), (0.8, -0.2, 0.12, .026), (0.46, -2.2, 0.13, .028), (0.86, 2.6, 0.1, .022)):
        p = el.lerp(wr, t); out = (V((s, 0, 0))*math.cos(a) + V((0, 1, 0))*math.sin(a))
        crystal(la, p + out*0.06, out*1.0 + fa*0.7, rr, h, sides=5)
    vein(la, [el.lerp(wr, t) + V((s*0.058*(1 - 0.3*t), -0.035, 0)) for t in (0.3, 0.55, 0.8, 0.97)], 0.005)
    # crystal hand: faceted palm, portal glow in the palm, crystal fingers
    hdir = (hd - wr).normalized()
    seg_loft(hb, CRYST, wr - hdir*0.02, hd + hdir*0.035, [(0, .042, .058), (0.3, .05, .076), (0.85, .042, .07), (1.0, .034, .06)],
             N=6, sub=0, smooth=False, n=2.0)
    sph(hb, GLOW, wr + hdir*0.12 + V((-s*0.04, 0, 0)), 0.032, scale=(0.35, 1, 1.2), u=10, v=8)
    crystal(hb, wr + hdir*0.06 + V((s*0.035, 0, 0)), (s, 0, 0.3), 0.022, 0.08, sides=4)
    crystal(hb, wr + hdir*0.1 + V((s*0.035, 0.03, 0)), (s, 0.3, -0.2), 0.02, 0.07, sides=4)
    for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
        for n_, r0, r1 in ((1, .019, .017), (2, .016, .011)):
            bn = f"{side}{fn}{n_}"; b = BONES[BIDX[bn]]
            seg_loft(bn, CRYST, V(b[1]), V(b[2]), [(0, r0, r0), (1, r1, r1)], N=5, sub=0, smooth=False)
            facet_ball(bn, CRYST, V(b[1]), r0*1.1)
        b = BONES[BIDX[f"{side}{fn}2"]]
        crystal(f"{side}{fn}2", V(b[2]), V(b[2]) - V(b[1]), 0.011, 0.03, sides=4)

# ================= LEGS: ivory thighs (under the robe), gold knee cops, crystal shins and feet =================
for side, s in (("Left", 1), ("Right", -1)):
    PIECE = "Leg" + side
    j = J[side]; hp, kn, an = j["hp"], j["kn"], j["an"]
    ul, ll, ft = f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot"
    seg_loft(ul, IVO, hp + V((0, 0, 0.05)), kn, [(0, .13, .13), (0.3, .125, .12), (0.75, .1, .095), (1.0, .085, .085)], N=16)
    sph(ll, GOLD, kn + V((0, -0.065, 0.01)), 0.09, scale=(1.0, 0.6, 1.15), u=16, v=10)
    ring_at(ll, GOLD, kn + V((0, -0.065, 0.01)), (0, 1, 0), 0.09*0.98, w=0.012, t=0.004, N=16)
    facet_ball(ll, CRYST, kn, 0.085)
    seg_loft(ll, CRYST, kn, an, [(0, .09, .09), (0.35, .085, .092), (1.0, .058, .06)], N=6, sub=0, smooth=False)
    ld = (an - kn).normalized()
    loft(ll, IVO, [(0.06, .098, .1), (0.24, .094, .097), (0.3, .088, .092)], N=14, M=_frame(kn, an - kn), cap=False)   # greave fragment
    ring_at(ll, GOLD, kn + ld*0.3, ld, 0.088, w=0.014, t=0.008, N=14)
    for (t, a, h) in ((0.5, 0.2, 0.15), (0.62, 2.6, 0.13), (0.72, -0.8, 0.12), (0.85, 1.6, 0.1)):
        p = kn.lerp(an, t); out = V((s*math.cos(a), math.sin(a), 0))
        crystal(ll, p + out*0.06, out + ld*0.6, 0.026, h, sides=4)
    vein(ll, [kn.lerp(an, t) + V((0.0, -0.075*(1 - 0.35*t), 0)) for t in (0.35, 0.6, 0.85)], 0.006)
    ring_at(ft, GOLD, an + V((0, 0, 0.0)), (0, 0, 1), 0.062, w=0.03, t=0.012, N=14)
    # faceted crystal foot, sole flat on the floor
    FS = [(0, .07, .085), (0.12, .088, .085), (0.3, .08, .06), (0.44, .035, .028), (0.5, .012, .012)]
    loft(ft, CRYST, [(z, rx, ry, 1.8, 0, ry - 0.085) for z, rx, ry in FS], N=6, M=TR((an.x, an.y + 0.1, 0.085), (math.pi/2, 0, 0)), smooth=False)
    vein(ft, [V((an.x, an.y + 0.02 - 0.13*i, 0.165 - 0.03*i - 0.004*i*i)) for i in range(3)], 0.006)
    crystal(ft, (an.x + 0.05*s, an.y + 0.1, 0.09), (s, 0.6, 0.4), 0.022, 0.09, sides=4)             # heel spurs
    crystal(ft, (an.x - 0.02*s, an.y + 0.12, 0.1), (-0.2*s, 1, 0.5), 0.022, 0.08, sides=4)

# ================= WAIST: pelvis, gold belt + medallion, the TWO-PANEL front-slit robe =================
PIECE = "Waist"
loft("LowerTorso", IVO, [(1.64, .19, .14), (1.76, .215, .155), (1.90, .2, .145), (2.06, .17, .13)], N=20, sub=1)
loft("LowerTorso", GOLD, [(1.92, .232, .175, 2.3), (2.02, .215, .165, 2.3)], N=28, cap=False)
loft("LowerTorso", GOLD, [(1.915, .236, .179, 2.3), (1.93, .236, .179, 2.3)], N=28, cap=False)
MED = V((0, -0.178, 1.965))
loft("LowerTorso", GOLD, [(0, .05, .065), (0.015, .05, .065), (0.015, .036, .05), (0, .036, .05)], N=16, M=TR(MED, (math.pi/2, 0, 0)))
crystal("LowerTorso", MED + V((0, -0.012, 0)), (0, -1, 0), 0.028, 0.03, sides=4, mi=GLOW)
# Robe: each panel is its own shell (outer ivory, inner indigo lining, gold edges) on an elliptical cylinder. Panel
# weights blend LowerTorso -> its thigh from the belt to the hem (the Acolyte's split, here with an open FRONT slit
# that widens toward the hem, so a striding leg comes through it instead of pushing a closed tube).
ROBE = [(1.95, .232, .172), (1.75, .285, .215), (1.35, .35, .27), (0.95, .43, .34), (0.62, .5, .4), (0.56, .51, .41)]
def _robe_r(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(ROBE, ROBE[1:]):
        if z1 <= z <= z0:
            t = (z0 - z)/(z0 - z1); return a0 + (a1 - a0)*t, b0 + (b1 - b0)*t
    return ROBE[-1][1:] if z < ROBE[-1][0] else ROBE[0][1:]
def _slit(z):             # half-width of the front opening at height z (negative = the panels overlap there)
    t = min(1.0, max(0.0, (1.62 - z)/(1.62 - 0.56)))
    return -0.05 + (0.2 + 0.05)*t**0.85
def robe_panel(side, s, rows=16, cols=16, th=0.022):
    leg = f"{side}UpperLeg"
    tb = bmesh.new(); grid = []
    zs = [ROBE[0][0] + (ROBE[-1][0] - ROBE[0][0])*i/rows for i in range(rows + 1)]
    for z in zs:
        rx, ry = _robe_r(z)
        a_front = -math.pi/2 + math.asin(max(-0.5, min(0.9, _slit(z)/rx)))      # front edge (slit side)
        a_back = math.pi/2 + 0.2                                                  # overlaps past the back centre
        row = []
        for c in range(cols + 1):
            a = a_front + (a_back - a_front)*c/cols
            hem = 0.018*math.sin(7*a) if z == zs[-1] else 0.0                     # gently scalloped hem
            for off in (0.0, -th):
                row.append(tb.verts.new((s*(rx + off)*math.cos(a), (ry + off)*math.sin(a), z + hem)))
        grid.append(row)
    def F(vs, mi):
        f = tb.faces.new(vs); f.material_index = mi
    for r in range(rows):
        for c in range(cols):
            o0, i0, o1, i1 = grid[r][2*c], grid[r][2*c + 1], grid[r][2*c + 2], grid[r][2*c + 3]
            O0, I0, O1, I1 = grid[r + 1][2*c], grid[r + 1][2*c + 1], grid[r + 1][2*c + 2], grid[r + 1][2*c + 3]
            F((o0, o1, O1, O0), GOLD if r >= rows - 1 else IVO)
            F((i0, I0, I1, i1), INDIGO)
    for r in range(rows):                                               # slit edge (gold) + back edge
        F((grid[r][0], grid[r + 1][0], grid[r + 1][1], grid[r][1]), GOLD)
        F((grid[r][-2], grid[r][-1], grid[r + 1][-1], grid[r + 1][-2]), IVO)
    for c in range(cols):                                               # top + hem edges
        F((grid[0][2*c], grid[0][2*c + 1], grid[0][2*c + 3], grid[0][2*c + 2]), IVO)
        F((grid[-1][2*c], grid[-1][2*c + 2], grid[-1][2*c + 3], grid[-1][2*c + 1]), GOLD)
    bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
    for f in tb.faces: f.smooth = True
    def wfn(co):
        t = min(1.0, max(0.0, (1.9 - co.z)/(1.9 - 0.6)))
        tw = 1.0 - 0.92*t**0.8
        return {"LowerTorso": tw, leg: 1.0 - tw}
    _add(tb, "LowerTorso", None, wfn=wfn)
    # crystal shedding off the hem, following the leg
    for i in range(9):
        a = -math.pi/2 + 0.45 + i*(math.pi + 0.1)/9
        rx, ry = _robe_r(0.59)
        crystal(leg, (s*(rx - 0.012)*math.cos(a), (ry - 0.012)*math.sin(a), 0.57 - 0.012*(i % 2)), (s*0.3*math.cos(a), 0.3*math.sin(a), -1),
                0.026 + 0.006*(i % 3), 0.09 + 0.05*((i*2) % 3), sides=5)
    rng = [(0.1, 0.72, .03, .11), (0.35, 0.95, .026, .09), (0.62, 0.78, .034, .13), (0.9, 1.05, .024, .08), (1.18, 0.7, .03, .12),
           (1.45, 0.88, .026, .1), (1.75, 0.74, .03, .1), (2.05, 0.98, .022, .08), (2.4, 0.8, .028, .1), (2.75, 0.7, .03, .12),
           (0.5, 1.22, .02, .07), (1.6, 1.18, .02, .07), (2.55, 1.15, .02, .06)]
    for u_, z, rr, hh in rng:
        a = -math.pi/2 + 0.42 + u_*0.95
        if a > math.pi/2 + 0.15: continue
        rx, ry = _robe_r(z); p_ = V((s*rx*math.cos(a), ry*math.sin(a), z)); out = V((s*math.cos(a), math.sin(a), 0))
        crystal("LowerTorso", p_ - out*0.004, out + V((0, 0, -0.55)), rr, hh, sides=5, wfn=wfn)
for side, s in (("Left", 1), ("Right", -1)):
    robe_panel(side, s)

rig, PARTS = assemble(NAME, OFFSET)
