# Pose clean-up pass for the Winged Sentinel (run at the end of every pose / anim key):
#   grip()      - seats the haft in the palm and wraps every finger + thumb around it (no finger penetrates the haft)
#   hand_on()   - places the off hand on the haft (IK wrist + palm orientation) then wraps it
#   clear_arm() - swings an arm (pole / abduction) until it no longer intersects torso / waist / legs
#   ground()    - drops/lifts the root so the lowest point of the body + lance sits exactly on the floor
import bpy, math
PREFIX = globals().get("PREFIX") or NAME + "_"
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
P = rig.pose.bones
RW = rig.matrix_world
HAFT_R = 0.047                     # grip wrap radius (lance local)
FING_R = 0.017
def _upd(): bpy.context.view_layer.update()
def _rest_rot(bn):
    return P[bn].matrix.to_3x3() @ rig.data.bones[bn].matrix_local.to_3x3().inverted()
def haft():
    _upd(); w = P["Weapon_R"]
    return RW @ w.head, (RW.to_3x3() @ (w.tail - w.head)).normalized()
def _dax(p, G0, GA):
    v = p - G0
    return (v - GA*v.dot(GA)).length
def _palm(side):
    _upd(); s = 1 if side == "Left" else -1
    hb = rig.data.bones[f"{side}Hand"]
    hd = (hb.tail_local - hb.head_local).normalized(); n = Vector((-s, 0, 0))
    R = _rest_rot(f"{side}Hand"); h = RW @ P[f"{side}Hand"].head
    return h, (RW.to_3x3() @ R @ hd).normalized(), (RW.to_3x3() @ R @ n).normalized()
SEAT_D, SEAT_N = 0.165, 0.06 + HAFT_R + 0.004       # haft centre: just past the palm, one palm-half + haft radius medial
def seat_point(side):
    h, hd, n = _palm(side)
    return h + hd*SEAT_D + n*SEAT_N
def grip_lance():
    """Slide the lance (Weapon_R) so its haft sits in the right palm, direction unchanged."""
    C = seat_point("Right"); G0, GA = haft()
    v = C - G0; delta = v - GA*v.dot(GA)
    wb = P["Weapon_R"]
    wb.matrix = Matrix.Translation(RW.to_3x3().inverted() @ delta) @ wb.matrix
    _upd()
def _wrap_bone(bn, G0, GA, target):
    """Rotate bone about the axis that swings its tail toward the haft; pick the angle whose samples never enter the
       haft and whose tail lies closest to 'target' distance from the axis."""
    _upd(); pb = P[bn]
    h = RW @ pb.head; t = RW @ pb.tail
    foot = G0 + GA*(h - G0).dot(GA)
    ax = (t - h).cross(foot - h)
    if ax.length < 1e-6: return
    ax.normalize(); best = None
    for k in range(-30, 49):                         # search both ways: curl in, or back out if already inside
        a = k*0.05
        tt = h + Matrix.Rotation(a, 3, ax) @ (t - h)
        if not all(_dax(h + (tt - h)*f, G0, GA) >= HAFT_R + FING_R*0.9 for f in (0.25, 0.5, 0.75, 1.0)): continue
        sc = abs(_dax(tt, G0, GA) - target) + 0.01*abs(a)
        if best is None or sc < best[0]: best = (sc, a)
    if best is None or best[1] == 0: return
    A = RW.to_3x3().inverted() @ ax; hl = pb.head.copy()
    pb.matrix = Matrix.Translation(hl) @ Matrix.Rotation(best[1], 4, A.normalized()) @ Matrix.Translation(-hl) @ pb.matrix
def wrap(side):
    G0, GA = haft()
    for f in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
        _wrap_bone(f"{side}{f}1", G0, GA, HAFT_R + FING_R)
        _wrap_bone(f"{side}{f}2", G0, GA, HAFT_R + FING_R*0.8)
    _upd()
def _ik(bone, target, pole=None):
    for c in list(P[bone].constraints):
        if c.type == 'IK': P[bone].constraints.remove(c)
    e = bpy.data.objects.new(f"IK_{bone}", None); bpy.context.scene.collection.objects.link(e); e.location = target
    c = P[bone].constraints.new('IK'); c.target = e; c.chain_count = 2
    if pole is not None:
        pe = bpy.data.objects.new(f"POLE_{bone}", None); bpy.context.scene.collection.objects.link(pe); pe.location = pole
        c.pole_target = pe; c.pole_angle = -math.pi/2
    return c
def _bake(bones):
    """Freeze IK results into plain pose transforms (so later edits and FBX export see exactly what we solved)."""
    _upd()
    M = {b: P[b].matrix.copy() for b in bones}
    for b in bones:
        for c in list(P[b].constraints):
            P[b].constraints.remove(c)
    for b in bones:
        P[b].matrix = M[b]; _upd()
def orient_hand(side, n_w, hd_w):
    """Rotate hand so its palm normal / finger direction match the requested world vectors."""
    _upd(); h, hd, n = _palm(side)
    def basis(a, b):
        b = (b - a*a.dot(b)).normalized(); return Matrix((a, b, a.cross(b))).transposed()
    Rw = basis(hd_w.normalized(), n_w) @ basis(hd, n).inverted()
    R = RW.to_3x3().inverted() @ Rw @ RW.to_3x3()
    pb = P[f"{side}Hand"]; hl = pb.head.copy()
    pb.matrix = Matrix.Translation(hl) @ R.to_4x4() @ Matrix.Translation(-hl) @ pb.matrix
    _upd()
def hand_on(side, u, away):
    """Off hand grips the haft at distance u from the grip centre. 'away' = world direction the palm comes FROM."""
    G0, GA = haft(); C = G0 + GA*u
    a = Vector(away); a = (a - GA*a.dot(GA)).normalized()          # palm normal points from hand to haft = -a
    n_w = -a; hd_w = GA.cross(n_w).normalized()
    if hd_w.z > 0: hd_w = -hd_w                                      # fingers hang downward-ish round the haft
    wr = C - n_w*SEAT_N - hd_w*SEAT_D
    s = 1 if side == "Left" else -1
    ua = f"{side}UpperArm"
    sh = RW @ P[ua].head; axis = (wr - sh).normalized(); ref = axis.orthogonal().normalized()
    rest = {b_: P[b_].matrix.copy() for b_ in (ua, f"{side}LowerArm", f"{side}Hand")}
    best = None
    for k in range(12):                              # swing the elbow round the shoulder->wrist line; keep the cleanest
        pole = sh + (wr - sh)*0.5 + (Matrix.Rotation(k*math.pi/6, 3, axis) @ ref)*0.6
        for b_ in rest: P[b_].matrix = rest[b_]; _upd()
        _ik(f"{side}LowerArm", tuple(RW.inverted() @ wr), tuple(RW.inverted() @ pole)); _bake([ua, f"{side}LowerArm"])
        err = ((RW @ P[f"{side}LowerArm"].tail) - wr).length
        sc = hits("Arm" + side) + 1000*err + (5 if (RW.to_3x3() @ (P[ua].tail - P[ua].head)).dot(Vector((s, 0, 0))) < -0.2 else 0)
        if best is None or sc < best[0]: best = (sc, pole)
    for b_ in rest: P[b_].matrix = rest[b_]; _upd()
    _ik(f"{side}LowerArm", tuple(RW.inverted() @ wr), tuple(RW.inverted() @ best[1])); _bake([ua, f"{side}LowerArm"])
    orient_hand(side, n_w, hd_w)
    # correct residual wrist error by nudging the whole off hand onto the seat
    _upd(); err = C - seat_point(side)
    if err.length > 0.004:
        pb = P[f"{side}Hand"]; pb.matrix = Matrix.Translation(RW.to_3x3().inverted() @ err) @ pb.matrix; _upd()
    wrap(side)
# ---------------- collision helpers ----------------
def _tree(pn):
    o = bpy.data.objects.get(PREFIX + pn)
    if o is None: return None
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons])
    oe.to_mesh_clear(); return t
def hits(a, others=("Torso", "Waist", "LegLeft", "LegRight")):
    _upd(); ta = _tree(a); n = 0
    for b in others:
        tb = _tree(b)
        if ta and tb: n += len(ta.overlap(tb))
    return n
def clear_arm(side, base_hits=0, step=0.06, maxit=14):
    """Abduct the upper arm (and let the forearm follow) until it no longer cuts into the body."""
    s = 1 if side == "Left" else -1; ua = P[f"{side}UpperArm"]
    for _ in range(maxit):
        if hits("Arm" + side) <= base_hits: return True
        hl = ua.head.copy(); ax = RW.to_3x3().inverted() @ Vector((0, 1, 0))
        ua.matrix = Matrix.Translation(hl) @ Matrix.Rotation(-step*s, 4, ax) @ Matrix.Translation(-hl) @ ua.matrix
    return False
def ground(extra=()):
    _upd(); dg = bpy.context.evaluated_depsgraph_get(); minz = 1e9
    for o in list(PARTS) + list(extra):
        if o.hide_render or "_Break" in o.name: continue
        oe = o.evaluated_get(dg); m = oe.to_mesh()
        if len(m.vertices): minz = min(minz, min((o.matrix_world @ v.co).z for v in m.vertices))
        oe.to_mesh_clear()
    r_ = P["HumanoidRootNode"]; r_.location = r_.location + Vector((0, -minz, 0)); _upd()
# ---------------- joint sanity (natural hinges, wrists, shoulders) ----------------
HINGES = {"LeftLowerArm": "arm", "RightLowerArm": "arm", "LeftLowerLeg": "leg", "RightLowerLeg": "leg"}
def _dir(bn): _upd(); pb = P[bn]; return (RW.to_3x3() @ (pb.tail - pb.head)).normalized()
def joint_report(tag=""):
    """Angles in degrees. Elbow/knee: signed flex (negative = hyperextended / bent the wrong way).
       Wrist: angle between forearm and hand. Returns list of problems."""
    out, bad = [], []
    for side in ("Left", "Right"):
        ua, la, hd = _dir(f"{side}UpperArm"), _dir(f"{side}LowerArm"), _dir(f"{side}Hand")
        body_fwd = (RW.to_3x3() @ (_rest_rot("UpperTorso") @ Vector((0, -1, 0)))).normalized()
        el = math.degrees(ua.angle(la)); n = ua.cross(la)
        # a natural elbow folds the forearm toward the front/inside of the upper arm
        side_ax = (RW.to_3x3() @ (_rest_rot(f"{side}UpperArm") @ Vector((1, 0, 0)))).normalized()
        wr = math.degrees(la.angle(hd))
        out.append(f"{side[0]}elbow {el:.0f} {side[0]}wrist {wr:.0f}")
        if wr > 50: bad.append(f"{side} wrist {wr:.0f}°")
        ul, ll = _dir(f"{side}UpperLeg"), _dir(f"{side}LowerLeg")
        kn = math.degrees(ul.angle(ll)); kdir = ul.cross(ll).dot((RW.to_3x3() @ (_rest_rot(f"{side}UpperLeg") @ Vector((1, 0, 0)))).normalized())
        out.append(f"{side[0]}knee {kn:.0f}{'!' if kn > 5 and kdir < 0 else ''}")
    print(f"JOINTS {tag}: " + " ".join(out) + ("  BAD: " + ", ".join(bad) if bad else ""))
    return bad

def wield(D, C, side="Right", pole_off=(0.5, 0.35, -0.6)):
    """Natural one-hand weapon hold: the haft runs along world direction D through world point C (in the palm).
       The hand stays in line with the forearm (the haft sits across the palm, so the forearm is solved to be well
       off the haft axis) and the elbow points out/down/back via the pole, so nothing bends unnaturally.
       Solves: forearm -> hand frame -> IK wrist target, iterated; then seats and wraps the lance."""
    D = Vector(D).normalized(); C = Vector(C); s = 1 if side == "Left" else -1
    ua, la = f"{side}UpperArm", f"{side}LowerArm"
    sh = RW @ P[ua].head
    chain = [ua] + [c.name for c in P[ua].children_recursive]      # arm + hand + fingers + weapon sockets
    keep = {b_: P[b_].matrix.copy() for b_ in chain}
    def _restore():
        for b_ in chain: P[b_].matrix = keep[b_]; _upd()
    best = None
    for po in (pole_off, (0.8, 0.1, -0.3), (0.6, 0.6, -0.2), (0.9, -0.2, -0.5), (0.3, 0.7, -0.7)):
        _restore()
        _wield_once(D, C, side, s, ua, la, sh + Vector((po[0]*s, po[1], po[2])))
        sc = hits("Arm" + side) + 3*joint_penalty(side)
        if best is None or sc < best[0]: best = (sc, po)
        if sc == 0: break
    _restore()
    _wield_once(D, C, side, s, ua, la, sh + Vector((best[1][0]*s, best[1][1], best[1][2])))
def joint_penalty(side):
    fa, hd = _dir(f"{side}LowerArm"), _dir(f"{side}Hand")
    return max(0.0, math.degrees(fa.angle(hd)) - 35)
def _wield_once(D, C, side, s, ua, la, pole):
    for sgn in (1, -1):
        for _ in range(4):
            fa = _dir(la)
            hd = (fa - D*fa.dot(D))
            if hd.length < 1e-3: hd = Vector((0, 0, -1)) - D*D.z
            hd.normalize(); n = D.cross(hd)*sgn
            wr = C - n*SEAT_N - hd*SEAT_D
            _ik(la, tuple(RW.inverted() @ wr), tuple(RW.inverted() @ pole)); _bake([ua, la])
        orient_hand(side, n, hd)
        if _dir("Weapon_R").dot(D) > 0.5 or side != "Right": break
    if side == "Right":
        G0, GA = haft(); q = GA.rotation_difference(D)
        wb = P["Weapon_R"]; h = wb.head.copy(); Rl = RW.to_3x3().inverted() @ q.to_matrix() @ RW.to_3x3()
        wb.matrix = Matrix.Translation(h) @ Rl.to_4x4() @ Matrix.Translation(-h) @ wb.matrix; _upd()
        grip_lance()
    wrap(side)
