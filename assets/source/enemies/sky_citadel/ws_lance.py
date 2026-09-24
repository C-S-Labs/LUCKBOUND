# LUCKBOUND - Winged Sentinel's unique weapon: the Aether Lance.
# Run AFTER winged_sentinel.py (reuses its helpers, materials and rig). Built along the Weapon_R socket:
# grip centred on the right hand, point forward. Separate mesh (< 10k tris), bone-parented to Weapon_R.
# Motif: graphite haft with violet bands, feathered winged guard, long leaf blade with a cyan aether fuller,
# swept feather lugs at the blade base, stone inlay collar, aether counterweight.
import bpy, bmesh, math
from mathutils import Matrix, Vector

PIECES = {}          # the helpers write into PIECES[PIECE]; start clean for the weapon
PARTLOG.clear()
PIECE = "Lance"
BREAK = False
XF = None
BONE = "Weapon_R"

# lance frame: local +Z = along the lance toward the point, origin at the grip
_b = rig.data.bones[BONE]
GRIP = rig.matrix_world @ _b.head_local
AX = (rig.matrix_world.to_3x3() @ (_b.tail_local - _b.head_local)).normalized()
F = _frame(GRIP, AX, hint=(0, 0, 1))          # local X = sideways (blade width), local Y ~ up
def LM(u=0.0, rot=None):
    M = F @ Matrix.Translation((0, 0, u))
    return M @ rot if rot is not None else M

import random as _rnd
_RNG = _rnd.Random(1729)
def bolt(bone, mi, p0, p1, segs=6, jit=0.012, r=0.005, rn=None, N=4):
    """Jagged lightning strand p0->p1 (world), kinks jittered perpendicular to the run, endpoints fixed."""
    rn = rn or _RNG
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0
    a_ = d.orthogonal().normalized(); b_ = d.cross(a_).normalized()
    pts = [p0]
    for i in range(1, segs):
        t = i/segs
        pts.append(p0 + d*t + a_*rn.uniform(-jit, jit) + b_*rn.uniform(-jit, jit)*0.6)
    pts.append(p1)
    for q0, q1 in zip(pts, pts[1:]):
        tube(bone, mi, tuple(q0), tuple(q1), r, r, N=N)
    for q in pts[1:-1]:
        sph(bone, mi, tuple(q), r*1.05, u=6, v=4)          # joint caps so kinks read clean
    return pts

# ---- haft ----
loft(BONE, PATINA, [(-1.02, .03, .03), (-0.3, .036, .036), (1.0, .036, .036), (1.62, .03, .03)], N=16, M=LM())
loft(BONE, IRON, [(-0.28, .042, .042), (0.26, .042, .042)], N=16, M=LM())                      # grip wrap
for k in range(9):                                                                              # wrap ribs
    u = -0.24 + k*0.06
    loft(BONE, IRON, [(u - .008, .047, .047), (u + .008, .047, .047)], N=16, M=LM())
for u in (-0.34, 0.32, 0.9, 1.25):                                                              # violet bands
    loft(BONE, BRONZE, [(u - .018, .044, .044), (u + .018, .044, .044)], N=16, M=LM())
for (u0, u1) in ((0.44, 0.84), (1.0, 1.2)):                                                    # faceted sleeve plates
    loft(BONE, PATINA, [(u0, .04, .04, 1.2), (u0 + 0.03, .05, .05, 1.2), (u1 - 0.03, .05, .05, 1.2), (u1, .04, .04, 1.2)], N=8, M=LM(), sub=0)
    for u in (u0 + 0.03, u1 - 0.03):
        loft(BONE, BRONZE, [(u - .006, .053, .053, 1.2), (u + .006, .053, .053, 1.2)], N=8, M=LM())
for u in (0.39, 0.93, 1.44):                                                                    # cyan ring lines
    loft(BONE, GLOW, [(u - .004, .04, .04), (u + .004, .04, .04)], N=16, M=LM())
# twin aether channels inlaid along the fore-haft
for s_ in (1, -1):
    loft(BONE, GLOW, [(0.42, .006, .006, 2, 0.034*s_, 0), (0.44, .006, .006, 2, 0.047*s_, 0), (0.84, .006, .006, 2, 0.047*s_, 0), (0.86, .006, .006, 2, 0.034*s_, 0),
                      (0.98, .006, .006, 2, 0.034*s_, 0), (1.0, .006, .006, 2, 0.047*s_, 0), (1.2, .006, .006, 2, 0.047*s_, 0), (1.22, .006, .006, 2, 0.034*s_, 0), (1.52, .006, .006, 2, 0.034*s_, 0)], N=6, M=LM())

# ---- counterweight (butt): faceted pommel, aether core, crescent fins, spike ----
loft(BONE, BRONZE, [(-1.00, .045, .045), (-1.03, .055, .055)], N=16, M=LM())
loft(BONE, PATINA, [(-1.03, .05, .05, 1.6), (-1.10, .085, .085, 1.6), (-1.18, .06, .06, 1.6)], N=16, M=LM(), sub=1)
loft(BONE, GLOW, [(-1.13, .087, .087, 1.6), (-1.15, .087, .087, 1.6)], N=16, M=LM())
loft(BONE, PATINA, [(-1.18, .04, .04), (-1.34, .012, .012), (-1.40, .002, .002)], N=12, M=LM(), sub=1)
for k in range(6):                                                                              # aether studs round the pommel
    a_ = k*math.pi/3
    n = F.to_3x3() @ Vector((math.cos(a_), math.sin(a_), 0))
    gem(BONE, BRONZE, tuple(F @ Vector((0.083*math.cos(a_), 0.083*math.sin(a_), -1.08))), 0.012, 0.012, rot=tuple(n.to_track_quat('Z', 'X').to_euler()), sides=4)
UP0 = F.to_3x3() @ Vector((0, 1, 0))
for s in (1, -1):
    blade(BONE, BRONZE, tuple(F @ Vector((0.07*s, 0, -1.10))), tuple(F.to_3x3() @ Vector((0.7*s, 0, -1.0))),
          0.22, 0.04, 0.012, hint=tuple(UP0), N=6)
    blade(BONE, PATINA, tuple(F @ Vector((0, 0.07*s, -1.10))), tuple(F.to_3x3() @ Vector((0, 0.5*s, -1.0))),
          0.15, 0.03, 0.01, hint=tuple(F.to_3x3() @ Vector((1, 0, 0))), N=6)

# ---- winged guard (vamplate): larger, two-tier feathers ----
loft(BONE, PATINA, [(0.29, .05, .05), (0.35, .11, .10), (0.40, .065, .06)], N=20, M=LM(), sub=1)
loft(BONE, BRONZE, [(0.345, .113, .103), (0.36, .113, .103)], N=20, M=LM())
UP = F.to_3x3() @ Vector((0, 1, 0))
for s in (1, -1):
    for k in range(4):   # feathers sweeping back over the hand
        root = F @ Vector((0.08*s, 0.0, 0.37 - 0.012*k))
        d = F.to_3x3() @ Vector((0.9*s, 0.25 - 0.22*k, -0.5 - 0.12*k))
        blade(BONE, BRONZE if k % 2 == 0 else PATINA, tuple(root), tuple(d), 0.40 - 0.07*k, 0.055, 0.012, hint=tuple(UP), N=8)
    gem(BONE, GLOW, tuple(F @ Vector((0, 0.105*s, 0.35))), 0.022, 0.018,
        rot=tuple((F.to_3x3() @ Vector((0, s, 0))).to_track_quat('Z', 'X').to_euler()), sides=6)

# ---- collar: stone ring with aether runes ----
loft(BONE, BRONZE, [(1.54, .045, .045), (1.58, .06, .06), (1.62, .055, .055)], N=16, M=LM())
loft(BONE, IVORY, [(1.62, .056, .056), (1.70, .048, .048)], N=16, M=LM())
loft(BONE, BRONZE, [(1.70, .05, .05), (1.73, .045, .04)], N=16, M=LM())
for k in range(4):
    a_ = k*math.pi/2 + math.pi/4
    n = F.to_3x3() @ Vector((math.cos(a_), math.sin(a_), 0))
    gem(BONE, GLOW, tuple(F @ Vector((0.057*math.cos(a_), 0.057*math.sin(a_), 1.66))), 0.013, 0.01,
        rot=tuple(n.to_track_quat('Z', 'X').to_euler()), sides=4)

# ---- blade head: two halves split down the middle. Each half OWNS its side blade, spine trim and feather lug,
#      so opening moves them together (nothing static left in their path). Bones LanceBladeL / LanceBladeR hinge
#      at the collar edge. Phase 2 opens them (mode picked by LANCE_MODE) and the cyan Beam blade shows between.
for s in (1, -1):
    PIECE = "BladeL" if s > 0 else "BladeR"
    half = (lambda c, s=s: c.x*s > 0)
    def clampx(co, s=s):
        if co.x*s < 0: co.x = 0.0
    XF = Matrix.Translation(F.to_3x3() @ Vector((0.0015*s, 0, 0)))   # 3 mm split line so the closed halves don't touch
    loft(BONE, PATINA, [(1.72, .045, .03, 1.6), (1.86, .13, .032, 1.6), (2.10, .15, .03, 1.6), (2.42, .115, .026, 1.6),
                        (2.68, .055, .018, 1.6), (2.90, .004, .004, 1.6)], N=20, M=LM(), keep=half, fill=True, warp=clampx)
    loft(BONE, BRONZE, [(1.72, .05, .012, 2), (1.86, .138, .012, 2), (2.10, .158, .012, 2), (2.42, .122, .01, 2),
                        (2.68, .06, .008, 2), (2.89, .006, .004, 2)], N=20, M=LM(), keep=half, fill=True, warp=clampx)   # violet edge band
    loft(BONE, BRONZE, [(1.74, .012, .04, 1.5), (2.4, .01, .036, 1.5), (2.8, .004, .02, 1.5)], N=8, M=LM(),
         keep=half, fill=True, warp=clampx)                                                                          # half of the spine
    loft(BONE, GLOW, [(1.80, .004, .033, 2, .045*s), (2.1, .01, .033, 2, .055*s), (2.45, .006, .028, 2, .035*s),
                      (2.62, .002, .022, 2, .015*s)], N=8, M=LM())                                     # fuller
    for k in range(3):   # rune notches down the fuller
        u = 1.92 + k*0.2
        gem(BONE, GLOW, tuple(F @ Vector((.05*s*(1 - k*0.2), 0.034*1, u))), 0.012, 0.008,
            rot=tuple(UP.to_track_quat('Z', 'X').to_euler()), sides=4)
        gem(BONE, GLOW, tuple(F @ Vector((.05*s*(1 - k*0.2), -0.034, u))), 0.012, 0.008,
            rot=tuple((-UP).to_track_quat('Z', 'X').to_euler()), sides=4)
    PS = [(1.86, .13, .032), (2.10, .15, .03), (2.42, .115, .026), (2.68, .055, .018)]
    def prof(u):
        for (a0, a1) in zip(PS, PS[1:]):
            if a0[0] <= u <= a1[0]:
                t = (u - a0[0])/(a1[0] - a0[0]); return a0[1] + (a1[1] - a0[1])*t, a0[2] + (a1[2] - a0[2])*t
        return PS[-1][1], PS[-1][2]
    for fy in (1, -1):
        pts = []
        for k in range(12):
            u = 1.88 + k*0.065
            rx, ry = prof(u); fr = 0.74
            y = ry*(1 - fr**1.6)**(1/1.6)
            pts.append(F @ Vector((0.0015*s + rx*fr*s, fy*(y + 0.001), u)))
        for q0, q1 in zip(pts, pts[1:]):
            tube(BONE, BRONZE, tuple(q0), tuple(q1), 0.0045, 0.0045, N=5)
        for q in pts[1:-1]:
            sph(BONE, BRONZE, tuple(q), 0.0045, u=6, v=4)
    # side blade (winged partisan), now part of this half
    b0 = Vector((0.07*s, 0, 1.73)); d0 = Vector((0.5*s, 0, 1.0)).normalized()
    b1 = b0 + d0*0.42; d1 = Vector((0.12*s, 0, 1.0)).normalized()
    b2 = b1 + d1*0.22; d2 = Vector((-0.2*s, 0, 1.0)).normalized()
    for (q, d, Lb, w) in ((b0, d0, 0.45, 0.05), (b1, d1, 0.25, 0.042), (b2, d2, 0.16, 0.03)):
        blade(BONE, PATINA, tuple(F @ q), tuple(F.to_3x3() @ d), Lb, w, 0.014, hint=tuple(UP), N=8)
    tube(BONE, BRONZE, tuple(F @ (b0 + d0*0.03)), tuple(F @ (b1 + d1*0.02)), 0.009, 0.007, N=5)
    tube(BONE, GLOW, tuple(F @ (b1 + d1*0.02 + Vector((0, 0.012, 0)))), tuple(F @ (b2 + d2*0.05 + Vector((0, 0.012, 0)))), 0.005, 0.004, N=5)
    blade(BONE, BRONZE, tuple(F @ Vector((0.05*s, 0, 1.76))), tuple(F.to_3x3() @ Vector((1.0*s, 0, -0.45))),
          0.24, 0.045, 0.012, hint=tuple(UP), N=8)                                                   # feather lug
    XF = None
# phase-2 energy blade (hidden in P1). Starts inside the collar socket, runs 0.45 m past the tip.
PIECE = "Beam"
loft(BONE, GLOW, [(1.74, .02, .008, 1.6), (1.95, .055, .011, 1.6), (2.6, .055, .011, 1.6), (3.05, .03, .008, 1.6),
                  (3.35, .002, .002, 1.6)], N=16, M=LM(), sub=1)
# floating aether halo: own bone (LanceHalo) so phase 2 can slide it out along the energy blade
# energy webbing: glowing membranes stretched between the beam and each fanned-back half (built for the fully open
# pose, so they only exist in phase 2 alongside the Beam). Hinge maths mirrors lance_open("fan").
FAN_ANG = 1.1
FAN_PUSH = 0.035
SLIDE = 0.075      # v6: halves slide straight apart, staying parallel to the plasma blade
def _open_local(p, s):
    h = Vector((0.045*s, 0, 1.73))
    return h + Matrix.Rotation(FAN_ANG*s, 3, 'Y') @ (p - h) + Vector((FAN_PUSH*s, 0, 0))
PIECE = "Beam"
for s in (1, -1):                                   # lightning arcs: beam edge -> each slid-open half (P2 only)
    for k, u in enumerate((1.9, 2.05, 2.2, 2.36, 2.52)):
        p0 = F @ Vector((0.05*s, 0, u)); p1 = F @ Vector(((0.0015 + SLIDE + 0.004)*s, 0, u + 0.05*(1 if k % 2 else -1)))
        bolt(BONE, GLOW, p0, p1, segs=4, jit=0.016, r=0.0045)
PIECE = "Halo"
HU = 1.58          # v7: the storm web rides just behind the blade, round the collar
HM = LM(HU); _hr = _rnd.Random(404)
def hp(r, a_, z=0.0): return HM @ Vector((r*math.cos(a_), r*math.sin(a_), z))
NS = 12
ang = [i*2*math.pi/NS + _hr.uniform(-0.08, 0.08) for i in range(NS)]
rad = {"in": 0.105, "mid": 0.185, "out": 0.26}
nodes = {k: [hp(r*(1 + _hr.uniform(-0.03, 0.03)), a_) for a_ in ang] for k, r in rad.items()}
for k in ("out", "mid"):                                        # jagged rings (storm-front loops)
    for i in range(NS):
        bolt(BONE, GLOW, nodes[k][i], nodes[k][(i + 1) % NS], segs=3 if k == "mid" else 4, jit=0.014, r=0.006 if k == "out" else 0.004, rn=_hr)
for i in range(NS):                                             # spokes: inner anchor -> mid -> out (every strike reaches the rim)
    bolt(BONE, GLOW, nodes["mid"][i], nodes["out"][i], segs=3, jit=0.012, r=0.004, rn=_hr)
    if i % 2 == 0:
        bolt(BONE, GLOW, nodes["in"][i], nodes["mid"][i], segs=3, jit=0.01, r=0.004, rn=_hr)
    else:                                                       # forks: split strands between neighbouring cells
        bolt(BONE, GLOW, nodes["mid"][i], hp(0.225, ang[i] + math.pi/NS), segs=2, jit=0.01, r=0.003, rn=_hr)
for i in range(0, NS, 2):                                       # inner anchor arcs cradle the blade (clear of the edges)
    bolt(BONE, GLOW, nodes["in"][i], nodes["in"][(i + 2) % NS], segs=4, jit=0.01, r=0.004, rn=_hr)
for k, r_ in (("out", 0.013), ("mid", 0.01)):                     # violet junction nodes
    for q in nodes[k]:
        sph(BONE, BRONZE, tuple(q), r_, u=10, v=6)
for i in range(0, NS, 2):
    gem(BONE, GLOW, tuple(nodes["in"][i]), 0.01, 0.008, rot=tuple((HM.to_3x3() @ Vector((0, 0, 1))).to_track_quat('Z', 'X').to_euler()), sides=4)
# v5 pairing: the lance halo carries the same spiked crown as the Sentinel's helm halo
for i in range(12):
    a_ = i*math.pi/6
    c_ = LM(HU) @ Vector((0.26*math.cos(a_), 0.26*math.sin(a_), 0))
    blade(BONE, BRONZE if i % 2 == 0 else PATINA, tuple(c_), tuple(LM(HU).to_3x3() @ Vector((math.cos(a_), math.sin(a_), 0))),
          0.09 if i % 2 == 0 else 0.05, 0.02, 0.008, hint=tuple(LM(HU).to_3x3() @ Vector((0, 0, 1))), N=6, sub=0)
PIECE = "Lance"

# ---- assemble the lance object, bone-parented to Weapon_R ----
# add the two blade bones (children of Weapon_R) - edit mode is safe here (headless build only)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for bn, hx in (("LanceBladeL", 0.045), ("LanceBladeR", -0.045)):
    eb = rig.data.edit_bones.new(bn)
    eb.head = rig.matrix_world.inverted() @ (F @ Vector((hx, 0, 1.73)))
    eb.tail = rig.matrix_world.inverted() @ (F @ Vector((hx, 0, 2.30)))
    eb.parent = rig.data.edit_bones[BONE]
eb = rig.data.edit_bones.new("LanceHalo")
eb.head = rig.matrix_world.inverted() @ (F @ Vector((0, 0, HU)))
eb.tail = rig.matrix_world.inverted() @ (F @ Vector((0, 0, HU + 0.28)))
eb.parent = rig.data.edit_bones[BONE]
bpy.ops.object.mode_set(mode='OBJECT')
LANCE_BONE = {"Lance": BONE, "Beam": BONE, "BladeL": "LanceBladeL", "BladeR": "LanceBladeR", "Halo": "LanceHalo"}
LANCE_OBJS = []
for pn in ("Lance", "BladeL", "BladeR", "Beam", "Halo"):
    body = PIECES[pn]
    glow = body.copy()
    bmesh.ops.delete(glow, geom=[f for f in glow.faces if f.material_index != GLOW], context='FACES')
    bmesh.ops.delete(body, geom=[f for f in body.faces if f.material_index == GLOW], context='FACES')
    for nm, bm in ((f"WingedSentinel_{pn}", body), (f"WingedSentinel_{pn}Glow", glow)):
        if not len(bm.faces):
            bm.free(); continue
        me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
        for m in MATS:
            me.materials.append(m)
        ob = bpy.data.objects.new(nm, me)
        bpy.context.scene.collection.objects.link(ob)
        bb = rig.data.bones[LANCE_BONE[pn]]
        ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bb.name
        ob.matrix_parent_inverse = (rig.matrix_world @ bb.matrix_local @ Matrix.Translation((0, bb.length, 0))).inverted()
        if pn == "Beam":
            ob.hide_render = True            # phase 2 only
        LANCE_OBJS.append(ob)
        print("PIECE", nm, sum(len(p.vertices) - 2 for p in me.polygons), "tris")
FX = F.to_3x3() @ Vector((1, 0, 0))
import os
LANCE_MODE = os.environ.get("LANCE_MODE", "slide")
def _bone_axes(bn):
    pb = rig.pose.bones[bn]; ml = rig.data.bones[bn].matrix_local.to_3x3().inverted()
    R = pb.matrix.to_3x3() @ ml          # rest->pose rotation of this bone (world, rig at identity rotation)
    return pb, (R @ FX).normalized(), (R @ UP).normalized(), (R @ AX).normalized()
def lance_open(amount=1.0, mode=None):
    """Phase-2 lance transform. Modes:
       hinge : halves hinge outward at the collar like opening jaws (0.32 rad); halo slides out onto the beam
       wide  : bigger jaw (0.55 rad) - side blades flare like wings; halo slides out
       slide : halves slide straight apart + forward (parallel), halo slides out
       fan   : halves hinge back toward the haft (blades swept back like folded wings), beam alone forms the point"""
    mode = mode or LANCE_MODE
    P_ = rig.pose.bones
    for bn, s in (("LanceBladeL", 1), ("LanceBladeR", -1)):
        bpy.context.view_layer.update()
        pb, fx, up, ax = _bone_axes(bn); h = pb.head.copy()
        if mode in ("hinge", "wide", "fan"):
            ang = {"hinge": 0.32, "wide": 0.55, "fan": FAN_ANG}[mode]*amount
            tipv = pb.tail - h
            SGN = max((1, -1), key=lambda g: (Matrix.Rotation(ang*s*g, 3, up) @ tipv).dot(fx*s))
            M = Matrix.Translation(h) @ Matrix.Rotation(ang*s*SGN, 4, up) @ Matrix.Translation(-h)
            if mode == "fan":
                M = Matrix.Translation(fx*s*FAN_PUSH*amount) @ M
        else:
            M = Matrix.Translation(fx*s*SLIDE*amount)
        pb.matrix = M @ pb.matrix
    bpy.context.view_layer.update()
    # the storm web is absorbed INTO the blade: it slides forward up the blade and collapses inward, igniting the plasma.
    # (Studio: tween the web part's size/transparency along this path; the bone carries the motion.)
    pb, fx, up, ax = _bone_axes("LanceHalo")
    pb.matrix = Matrix.Translation(ax*0.5*amount) @ pb.matrix
    pb.scale = (max(0.02, 1 - amount),)*3
    bpy.context.view_layer.update()
    for ob in LANCE_OBJS:
        if ob.name.startswith("WingedSentinel_Halo"):
            ob.hide_render = amount >= 0.99
    bpy.context.view_layer.update()
    for ob in LANCE_OBJS:
        if ob.name.startswith("WingedSentinel_Beam"):
            ob.hide_render = amount < 0.5
