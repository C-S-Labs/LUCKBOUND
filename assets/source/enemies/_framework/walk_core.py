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

def walk_pose_humanoid(t, stride=0.32, lift=0.10, hip_twist=0.14, torso_twist=0.11, arm_swing=0.55,
                        elbow_bend=-0.28, lean=0.06):
    """t in [0,1): phase through one full stride cycle. Legs are SOLVED (leg_to); torso/hip/arms are direct FK --
       a walking arm swing and pelvis sway don't need combat-grade IK, just a natural sinusoidal drive."""
    for side in ("Left", "Right"):
        tp = _leg_phase(side, t)
        fwd = (stride/2)*math.cos(2*math.pi*tp)                       # + = foot forward (heel-strike side of the cycle)
        up = lift*max(0.0, math.sin(2*math.pi*(tp - 0.5)))            # lifts only during this foot's swing half
        foot0 = _rest_foot(side)
        target = foot0 + Vector((0, -fwd, up))                        # -Y = forward
        knee_dir = (0.0, -1.0, 0.15 + 0.5*(up/max(lift, 1e-6)))       # knee pushes forward more while the foot is lifted
        leg_to(side, target, knee_dir)
    hip_z = hip_twist*math.sin(2*math.pi*t)                            # pelvis leads with whichever leg is forward
    rot("LowerTorso", z=hip_z, add=False)
    rot("UpperTorso", z=-hip_z*(torso_twist/max(hip_twist, 1e-6)), x=-lean, add=False)   # shoulders counter-rotate
    for side in ("Left", "Right"):
        other_leg = "Right" if side == "Left" else "Left"               # contralateral: arm swings with the OPPOSITE leg
        tp = _leg_phase(other_leg, t)
        ang = arm_swing*math.cos(2*math.pi*tp)
        rot(f"{side}UpperArm", x=ang, add=False)
        if f"{side}LowerArm" in P:
            rot(f"{side}LowerArm", x=elbow_bend, add=False)

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

def strafe_pose_humanoid(t, side_dir=1, stride=0.24, lift=0.10, lean=0.08, arm_out=0.25):
    """One phase of a lateral side-step / shuffle (circling the player, Dark-Souls-style spacing -- not a static
       stand). side_dir: +1 steps toward the character's left, -1 toward its right. Both feet shuffle the same
       way, offset in phase, so the whole body translates-in-place sideways without crossing the legs."""
    for side in ("Left", "Right"):
        tp = _leg_phase(side, t)
        shift = side_dir*(stride/2)*math.cos(2*math.pi*tp)
        up = lift*max(0.0, math.sin(2*math.pi*(tp - 0.5)))
        foot0 = _rest_foot(side)
        leg_to(side, foot0 + Vector((shift, 0, up)), (side_dir*0.3, -1.0, 0.2))
    rot("UpperTorso", y=side_dir*lean, add=False)
    for side in ("Left", "Right"):
        s = 1 if side == "Left" else -1
        rot(f"{side}UpperArm", z=-side_dir*arm_out*s, add=False)

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
    params = dict(stride=g.get("stride_frac", 0.4)*L*0.7, lift=g.get("lift_frac", 0.12)*L)
    begin(name, length=length, loop=True, fps=fps)
    for f in range(1, length + 1):
        t = (f - 1) / length
        key(f, lambda t=t: (strafe_pose_humanoid(t, side_dir=side_dir, **params), post(t) if post else None))
    mark("Footstep", 1); mark("Footstep", length // 2 + 1)
    ok = end()
    print(f"STRAFE {name}: hinge check -> {hinge_errors() if 'hinge_errors' in globals() else 'n/a'}")
    return ok
