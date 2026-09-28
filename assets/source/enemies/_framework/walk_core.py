# WALK CYCLE core (framework, humanoid bodies). A parametric, ANALYTICALLY SOLVED walk loop: every frame's foot
# placement and knee bend is computed from real foot-target geometry via leg_to() (the same law-of-cosines 2-bone
# solve pose_fix.py's arm_to() uses for combat, just applied to the leg's own hinge), not interpolated between a
# couple of hand-posed extremes. That's what makes it correct at ANY stride/height/leg-length the caller passes in,
# so every future humanoid enemy gets a natural walk for free just by calling build_walk_humanoid() -- no per-enemy
# hand animation needed unless its gait is meant to be unusual.
#
# Usage from an action file (<world>/anims/<enemy_id>/Walk.py):
#   exec(open(FW + r"\walk_core.py").read())
#   build_walk_humanoid()                       # defaults suit a normal humanoid stride
#   build_walk_humanoid(role="boss", post=fn)   # post(t) runs after each solved frame: e.g. a boss re-solves its
#                                               # weapon arm so it CARRIES the weapon instead of swinging it
#
# Convention (matches every enemy body script in this repo): character faces -Y, +Z is up, +X is the character's
# left. A walk cycle is built IN PLACE (feet cycle fore/aft under a stationary pelvis) -- Studio's own movement
# code drives the actual translation; baking root motion into the loop would double it up.
import math
from mathutils import Vector, Matrix

def _ik2(ua, la, W, knee_dir=None):
    """Generic analytic 2-bone solve: place bone `ua` (upper segment) so bone `la` (lower segment)'s TAIL lands on
       world W, hinge flexing toward knee_dir (world). `ua` is oriented via a law-of-cosines elbow-plane solve (the
       same one arm_to() uses) without twisting it about its own axis; `la` is then set as a PURE hinge about the
       upper bone's local X, so the tail lands exactly on W whatever body/leg-count it's used for."""
    L1 = rig.data.bones[ua].length; L2 = rig.data.bones[la].length
    _upd(); S = RW @ P[ua].head; W = Vector(W)
    d = W - S; dist = min(max(d.length, abs(L1 - L2) + 1e-3), (L1 + L2)*0.995)   # never locked straight / hyperextended
    u = d.normalized(); W = S + u*dist
    e = Vector(knee_dir if knee_dir is not None else (0.0, -1.0, 0.2)).normalized()
    v = e - u*e.dot(u)
    if v.length < 1e-4: v = Vector((0, 1, 0)) - u*u.y
    v.normalize()
    a = (L1*L1 - L2*L2 + dist*dist)/(2*dist); h = math.sqrt(max(L1*L1 - a*a, 0.0))
    E = S + u*a + v*h
    Ri = RW.to_3x3().inverted()
    def frame(head, tail, back):
        y = (tail - head).normalized(); z = (back - y*back.dot(y)).normalized(); x = y.cross(z)
        M = Matrix((x, y, z)).transposed()
        M4 = (Ri @ M).to_4x4(); M4.translation = RW.inverted() @ head
        return M4
    # Frame the upper bone with its local Z on whichever side of the bend plane its CURRENT Z already is, so the
    # solve never twists the thigh 180 deg about its own axis (anything weighted to it -- robes, tassets -- would
    # flip to the far side). Then place the lower bone explicitly onto W about the SAME local X axis: a pure hinge
    # that always lands on the target, whichever way this body's rest rolls point (same approach as arm_to()).
    zc = RW.to_3x3() @ P[ua].matrix.to_3x3().col[2]
    P[ua].matrix = frame(S, E, v if v.dot(zc) >= 0 else -v); _upd()
    x2 = (RW.to_3x3() @ P[ua].matrix.to_3x3().col[0]).normalized(); y2 = (W - E).normalized()
    z2 = x2.cross(y2).normalized(); x2 = y2.cross(z2)
    M2 = (Ri @ Matrix((x2, y2, z2)).transposed()).to_4x4(); M2.translation = RW.inverted() @ E
    P[la].matrix = M2
    _upd()
    return E

def leg_to(side, W, knee_dir=None):
    """Humanoid convenience wrapper: place {side}UpperLeg/{side}LowerLeg via _ik2()."""
    return _ik2(f"{side}UpperLeg", f"{side}LowerLeg", W, knee_dir)

def _rest_foot(side):
    _upd(); return RW @ P[f"{side}LowerLeg"].tail

def _leg_phase(side, t):
    return t if side == "Right" else (t + 0.5) % 1.0

# WHOLE-BODY RULE (owner): a locomotion cycle animates the entire body, never legs or arms alone. Every frame keys,
# in this order (the legs hang off the pelvis, so the pelvis moves BEFORE the feet are solved onto the floor):
#   1. root: vertical bob (low at each double-support) + lateral sway over the stance foot
#   2. pelvis: yaw toward the forward leg + roll (swing-side hip drops)
#   3. legs: solved onto world foot targets computed from the REST feet, so the planted foot never slides
#   4. chest: counter-yaw and counter-roll against the pelvis, plus lean in the direction of travel
#   5. neck/head: cancel what the spine did, so the head stays level and facing forward
#   6. arms: swing from the shoulder about WORLD axes (never raw Euler: a bone's roll decides where a raw Euler
#      rotation goes), held clear of the torso, elbow flexing with the swing
FWD_W, LEFT_W, UP_W = Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

def _wrot(bone, axis, ang):
    """Rotate `bone` (and everything parented to it) by `ang` about a WORLD axis through its head.
       +ang about UP_W turns the face toward the character's left; about -FWD_W... see the callers."""
    if abs(ang) < 1e-7: return
    _upd(); pb = P[bone]; h = pb.head.copy()
    a = (RW.to_3x3().inverted() @ Vector(axis)).normalized()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, a) @ Matrix.Translation(-h) @ pb.matrix; _upd()

def _tilt(bone, ang_side, ang_fwd=0.0):
    """Tilt a spine bone: ang_side > 0 moves its top toward the character's LEFT, ang_fwd > 0 leans it forward."""
    _wrot(bone, Vector((0, 1, 0)), ang_side)        # about +Y: +Z swings toward +X (left)
    _wrot(bone, Vector((1, 0, 0)), ang_fwd)         # about +X: +Z swings toward -Y (forward)

def _swing_arm(side, fwd=0.0, out=0.0, elbow=0.0):
    """Upper arm swung from the shoulder: fwd > 0 carries the hand forward, out > 0 carries it away from the body
       (both radians, about world axes, so the result does not depend on the bone's roll). elbow > 0 flexes the
       forearm forward, as a pure hinge in the arm's swing plane."""
    s = 1 if side == "Left" else -1
    ua, la = f"{side}UpperArm", f"{side}LowerArm"
    _wrot(ua, Vector((1, 0, 0)), fwd)                # about +X: a hanging arm's hand goes toward -Y (forward)
    _wrot(ua, Vector((0, 1, 0)), -s*out)             # about +Y: hand goes toward +X for the left arm
    if la in P and abs(elbow) > 1e-7:
        _upd(); d = (P[la].tail - P[la].head).normalized()
        ax = d.cross(RW.to_3x3().inverted() @ FWD_W)
        if ax.length > 1e-4:
            _wrot(la, RW.to_3x3() @ ax.normalized(), elbow)

def _level_head(chest_yaw, chest_side, chest_fwd, keep=0.75):
    """Neck/head counter the chest so the gaze stays level and forward (keep = fraction of the chest motion cancelled)."""
    if "Neck" not in P: return
    _wrot("Neck", UP_W, -chest_yaw*keep)
    _tilt("Neck", -chest_side*keep, -chest_fwd*keep*0.5)

def walk_pose_humanoid(t, stride=0.32, lift=0.10, hip_twist=0.14, torso_twist=0.11, arm_swing=0.55,
                        elbow_bend=0.28, lean=0.06, bob=0.03, sway=0.03, hip_roll=0.05, arm_out=0.10):
    """t in [0,1): phase through one full stride cycle. Whole body, in the WHOLE-BODY RULE order above. Legs are
       SOLVED (leg_to); spine and arms are driven about world axes."""
    foot0 = {s: _rest_foot(s) for s in ("Left", "Right")}             # before the root moves: feet stay put in world
    c2 = math.cos(4*math.pi*t)                                          # two contacts per cycle (t = 0 and 0.5)
    stance = math.sin(2*math.pi*t)                                      # > 0: right foot is the stance foot
    move_root(x=-sway*stance, y_up=-bob*0.5*(1 + c2))                   # low at contact, weight over the stance foot
    hip_z = hip_twist*math.sin(2*math.pi*t)                             # pelvis leads with whichever leg is forward
    _wrot("LowerTorso", UP_W, hip_z)
    _tilt("LowerTorso", hip_roll*stance)                                # swing-side hip drops
    for side in ("Left", "Right"):
        tp = _leg_phase(side, t)
        fwd = (stride/2)*math.cos(2*math.pi*tp)                        # + = foot forward (heel-strike side of the cycle)
        up = lift*max(0.0, math.sin(2*math.pi*(tp - 0.5)))             # lifts only during this foot's swing half
        target = foot0[side] + Vector((0, -fwd, up))                   # -Y = forward
        knee_dir = (0.0, -1.0, 0.15 + 0.5*(up/max(lift, 1e-6)))        # knee pushes forward more while the foot is lifted
        leg_to(side, target, knee_dir)
    chest_yaw = -hip_z*(torso_twist/max(hip_twist, 1e-6)) - hip_z       # net shoulders counter-rotate against the hips
    chest_side = -hip_roll*stance*1.4                                   # chest rights itself over the dropped hip
    _wrot("UpperTorso", UP_W, chest_yaw)
    _tilt("UpperTorso", chest_side, lean + 0.25*lean*c2)                # a touch more lean on each push-off
    _level_head(chest_yaw + hip_z, chest_side + hip_roll*stance, lean)
    for side in ("Left", "Right"):
        other_leg = "Right" if side == "Left" else "Left"                # contralateral: arm swings with the OPPOSITE leg
        sw = math.cos(2*math.pi*_leg_phase(other_leg, t))              # +1 = arm fully forward
        _swing_arm(side, fwd=arm_swing*sw, out=arm_out,
                   elbow=elbow_bend*(1.0 + 0.6*max(0.0, sw)))           # forearm flexes more on the forward swing

def _leg_len(side="Right"):
    return rig.data.bones[f"{side}UpperLeg"].length + rig.data.bones[f"{side}LowerLeg"].length

# Role presets (fractions of leg length, so a giant boss and a small basic both get a PROPORTIONAL, natural gait
# with zero per-enemy tuning). "role" matches the manifest's combat archetype id where one applies; anything not
# listed falls back to "default". Add more roles here as new archetypes show up -- this table is the one place
# a size/weight-class difference in gait belongs, not scattered per-enemy overrides.
ROLE_GAIT = {
    "default":  dict(stride_frac=0.55, lift_frac=0.14, hip_twist=0.14, torso_twist=0.11, arm_swing=0.55, cadence=1.0),
    "brute":    dict(stride_frac=0.40, lift_frac=0.11, hip_twist=0.08, torso_twist=0.06, arm_swing=0.30, cadence=0.75),
    "miniboss": dict(stride_frac=0.42, lift_frac=0.12, hip_twist=0.09, torso_twist=0.07, arm_swing=0.35, cadence=0.80),
    "boss":     dict(stride_frac=0.42, lift_frac=0.12, hip_twist=0.09, torso_twist=0.07, arm_swing=0.35, cadence=0.80),
    "caster":   dict(stride_frac=0.45, lift_frac=0.12, hip_twist=0.10, torso_twist=0.10, arm_swing=0.20, cadence=0.90),
    "scout":    dict(stride_frac=0.62, lift_frac=0.16, hip_twist=0.16, torso_twist=0.13, arm_swing=0.65, cadence=1.15),
}

def _resolve_gait(role, overrides):
    g = dict(ROLE_GAIT.get(role or "default", ROLE_GAIT["default"]))
    g.update(overrides)
    L = _leg_len()
    return dict(stride=g.pop("stride_frac")*L, lift=g.pop("lift_frac")*L,
                bob=g.get("bob_frac", 0.02)*L, sway=g.get("sway_frac", 0.02)*L,
                hip_twist=g["hip_twist"], torso_twist=g["torso_twist"], arm_swing=g["arm_swing"]), g.get("cadence", 1.0)

def build_walk_humanoid(name="Walk", length=32, fps=30, role=None, post=None, **overrides):
    """Builds and keys a full looping walk cycle, scaled to THIS rig's own leg length and the enemy's role (see
       ROLE_GAIT) -- a boss and a basic both walk naturally with zero per-enemy tuning unless you want to override.
       post(t), optional: called after each frame's walk pose (same phase t) to override the upper body, e.g. hold a
       weapon; the legs stay solved by the walk."""
    params, cadence = _resolve_gait(role, overrides)
    length = max(8, round(length / cadence))
    begin(name, length=length, loop=True, fps=fps)
    for f in range(1, length + 1):
        t = (f - 1) / length
        key(f, lambda t=t: (walk_pose_humanoid(t, **params), post(t) if post else None))
    mark("Footstep", 1); mark("Footstep", length // 2 + 1)
    ok = end()
    print(f"WALK {name}: hinge check -> {hinge_errors() if 'hinge_errors' in globals() else 'n/a'}")
    return ok

def strafe_pose_humanoid(t, side_dir=1, stride=0.24, lift=0.10, lean=0.08, arm_out=0.10, arm_swing=0.12,
                         elbow_bend=0.22, bob=0.025, sway=0.03, hip_roll=0.05, hip_twist=0.04, min_gap=0.70,
                         stagger=0.35):
    """One phase of a lateral side-step (circling the player, Dark-Souls-style spacing). side_dir: +1 steps toward
       the character's left, -1 toward its right. Whole body, in the WHOLE-BODY RULE order above.
       The feet swing in antiphase, so their gap is rest - 2*amplitude at its closest; the amplitude is capped so the
       gap never drops below min_gap x the rest stance width (the feet never meet or cross), and the knees point
       forward and slightly OUT, away from each other. stagger (x the rest stance width) keeps a fighter's staggered
       stance, left foot forward: at the closest gap the shins pass BESIDE each other instead of meeting."""
    foot0 = {s: _rest_foot(s) for s in ("Left", "Right")}
    rest_gap = abs(foot0["Left"].x - foot0["Right"].x)
    amp = min(stride/2, rest_gap*(1.0 - min_gap)/2)
    c2 = math.cos(4*math.pi*t)
    stance = math.sin(2*math.pi*t)                                      # > 0: right foot is the stance foot
    move_root(x=-sway*stance, y_up=-bob*0.5*(1 + c2))
    _wrot("LowerTorso", UP_W, hip_twist*side_dir*stance)                # hips open slightly toward the lead step
    _tilt("LowerTorso", hip_roll*stance)
    for side in ("Left", "Right"):
        s = 1 if side == "Left" else -1
        tp = _leg_phase(side, t)
        shift = side_dir*amp*math.cos(2*math.pi*tp)
        up = lift*max(0.0, math.sin(2*math.pi*(tp - 0.5)))
        stag = -s*stagger*rest_gap/2                                    # -Y = forward: left foot ahead, right behind
        leg_to(side, foot0[side] + Vector((shift, stag, up)), (0.25*s, -1.0, 0.2 + 0.4*(up/max(lift, 1e-6))))
    chest_side = side_dir*lean - hip_roll*stance*1.4                    # lean into the travel, right over the dropped hip
    chest_yaw = -hip_twist*side_dir*stance*1.5
    _wrot("UpperTorso", UP_W, chest_yaw)
    _tilt("UpperTorso", chest_side, 0.03 + 0.02*c2)
    _level_head(chest_yaw + hip_twist*side_dir*stance, chest_side + hip_roll*stance, 0.03)
    for side in ("Left", "Right"):
        s = 1 if side == "Left" else -1
        lead = 1.0 if s == side_dir else 0.0                            # the arm on the travel side opens a little more
        _swing_arm(side, fwd=arm_swing*math.cos(2*math.pi*t + (0 if s > 0 else math.pi)),
                   out=arm_out*(1.0 + 0.5*lead) + 0.04*max(0.0, s*stance),
                   elbow=elbow_bend*(1.0 + 0.3*c2))

# ---------------- quadruped gait (creature bodies, e.g. Meadow Stag) ----------------
# No fixed bone-naming convention needed: pass whatever leg names the enemy script already uses (they must each
# be f"{name}Upper"/f"{name}Lower", parented the same way humanoid legs are -- exactly the pattern every quadruped
# built so far already follows). Nothing about the mesh/rig needs to change to use this.
def _quad_leg_len(legs):
    n0 = next(iter(legs))
    return rig.data.bones[n0 + "Upper"].length + rig.data.bones[n0 + "Lower"].length

def walk_pose_quadruped(t, legs, pairs, stride=0.3, lift=0.12, spine_pitch=0.05, bob=0.02):
    """legs: iterable of leg-name prefixes (e.g. "FrontLeft"). pairs: {name: 0 or 1} -- which half of the cycle
       that leg is in. Diagonal pairs sharing a group (TROT, the default a charger like the Stag wants) move
       together; give every leg its own group (0,0.25,0.5,0.75) for a slower, more stable 4-beat walk instead."""
    for name in legs:
        ua, la = name + "Upper", name + "Lower"
        group = pairs[name]
        tp = (t + group) % 1.0
        fwd = (stride/2)*math.cos(2*math.pi*tp)
        up = lift*max(0.0, math.sin(2*math.pi*(tp - 0.5)))
        _upd(); foot0 = RW @ P[la].tail
        fold = -1.0 if "Back" in name else 1.0   # real quadrupeds: front knee folds back, hind hock folds forward
        knee_dir = (0.0, fold, 0.2 + 0.5*(up/max(lift, 1e-6)))
        _ik2(ua, la, foot0 + Vector((0, -fwd, up)), knee_dir)
    if "Body" in P:
        rot("Body", x=spine_pitch*math.sin(4*math.pi*t), add=False)   # slight spine flex, twice per cycle (both support phases)
    root = "HumanoidRootNode" if "HumanoidRootNode" in P else ("Root" if "Root" in P else None)
    if root: P[root].location = (0, bob*math.cos(4*math.pi*t), 0)   # local Y = the bone's own length axis = world up at rest

def build_walk_quadruped(name="Walk", length=24, fps=30, gait="trot", role=None,
                          legs=("FrontLeft", "FrontRight", "BackLeft", "BackRight"), **overrides):
    """gait: "trot" (diagonal pairs together -- fast, aggressive; default, suits a charger) or "walk" (4-beat,
       one foot at a time -- slower, more stable/cautious). role tunes stride/lift the same way ROLE_GAIT does."""
    if gait == "trot":
        pairs = {legs[0]: 0.0, legs[3]: 0.0, legs[1]: 0.5, legs[2]: 0.5}   # FL+BR vs FR+BL
    else:
        pairs = {legs[0]: 0.0, legs[2]: 0.25, legs[1]: 0.5, legs[3]: 0.75}  # FL, BL, FR, BR -- one at a time
    g = dict(ROLE_GAIT.get(role or "default", ROLE_GAIT["default"])); g.update(overrides)
    L = _quad_leg_len(legs)
    params = dict(stride=g.get("stride_frac", 0.5)*L, lift=g.get("lift_frac", 0.14)*L)
    cadence = g.get("cadence", 1.0); length = max(8, round(length / cadence))
    begin(name, length=length, loop=True, fps=fps)
    for f in range(1, length + 1):
        t = (f - 1) / length
        key(f, lambda t=t: walk_pose_quadruped(t, legs, pairs, **params))
    mark("Footstep", 1); mark("Footstep", length // 2 + 1)
    ok = end()
    print(f"WALK {name} (quadruped/{gait}): hinge check -> {hinge_errors() if 'hinge_errors' in globals() else 'n/a'}")
    return ok

def build_strafe_humanoid(name="Strafe", length=24, fps=30, side_dir=1, role=None, post=None, **overrides):
    """Looping side-step cycle for circling/spacing behaviour. side_dir=+1 (circle left) or -1 (circle right) --
       export both as separate Studio animations (StrafeLeft/StrafeRight) and blend by input direction.
       post(t): as build_walk_humanoid (e.g. keep the weapon held while circling)."""
    g = dict(ROLE_GAIT.get(role or "default", ROLE_GAIT["default"]))
    g.update(overrides)
    L = _leg_len()
    params = dict(stride=g.get("stride_frac", 0.4)*L*0.7, lift=g.get("lift_frac", 0.12)*L,
                  bob=g.get("bob_frac", 0.02)*L*0.8, sway=g.get("sway_frac", 0.02)*L)
    begin(name, length=length, loop=True, fps=fps)
    for f in range(1, length + 1):
        t = (f - 1) / length
        key(f, lambda t=t: (strafe_pose_humanoid(t, side_dir=side_dir, **params), post(t) if post else None))
    mark("Footstep", 1); mark("Footstep", length // 2 + 1)
    ok = end()
    print(f"STRAFE {name}: hinge check -> {hinge_errors() if 'hinge_errors' in globals() else 'n/a'}")
    return ok
