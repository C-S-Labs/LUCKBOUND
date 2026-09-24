# Animation core shared by every enemy action. An action file (<world>/anims/<enemy_id>/<Action>.py) only describes
# KEY POSES + TIMING; this module handles actions, interpolation, contact clean-up and the combat markers Studio reads.
#
#   begin("P1_Lunge", length=48, loop=False)
#   key(1,  lambda: pose_base())                         # any callable that poses the rig
#   key(12, lambda: (pose_base(), rot("UpperTorso", x=0.4)))
#   mark("Tell", 1); mark("HitStart", 13); mark("HitEnd", 19); mark("RecoverStart", 19)
#   end()
#
# Combat markers (required on every attack action; the Studio combat script listens with GetMarkerReachedSignal):
#   Tell          wind-up starts: VFX tell + audio cue on. Must be >= 8 f before HitStart.
#   HitStart      hitbox live          HitEnd   hitbox off
#   RecoverStart  punish window opens (glow dims)        Recovery = action end - RecoverStart, must be >= 18 f.
# Optional: Footstep, WingBeat, Impact, VFX_<name> - free-form VFX/SFX triggers.
import bpy, math
from mathutils import Matrix, Vector, Euler
P = rig.pose.bones
CLIP_PIECES = ("ArmLeft", "ArmRight", "Lance", "BladeL", "BladeR")   # checked vs Torso/Waist/Legs each key
REQUIRED_ATTACK_MARKERS = ("Tell", "HitStart", "HitEnd", "RecoverStart")
_ACT = {}
def reset_pose():
    """Clear the pose + any leftover IK helpers so every action starts from the rest pose."""
    for pb in P:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.rotation_mode = 'XYZ'; pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    for o in [o for o in bpy.data.objects if o.name.startswith(("IK_", "POLE_"))]:
        bpy.data.objects.remove(o)
    rig.animation_data_create(); rig.animation_data.action = None
    bpy.context.view_layer.update()
def rot(bone, x=0.0, y=0.0, z=0.0, add=True):
    pb = P[bone]; pb.rotation_mode = 'XYZ'
    e = pb.rotation_euler if add else Euler((0, 0, 0))
    pb.rotation_euler = (e.x + x, e.y + y, e.z + z)
def move_root(x=0.0, y_up=0.0, z=0.0):
    """Root motion in WORLD terms (x sideways, y_up vertical, z = forward along -Y). HumanoidRootNode's local Y is up."""
    r = P["HumanoidRootNode"]; r.location = (r.location[0] + x, r.location[1] + y_up, r.location[2] + z)
def begin(name, length, loop=False, fps=30):
    sc = bpy.context.scene; sc.render.fps = fps; sc.frame_start, sc.frame_end = 1, length
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    _ACT.update(name=name, act=act, length=length, loop=loop, keys=[])
    return act
def key(frame, pose_fn):
    """Reset to rest, run pose_fn, then key EVERY pose bone (full keys keep Studio playback exact)."""
    reset_keep_action()
    pose_fn()
    bpy.context.view_layer.update()
    for pb in P:
        pb.keyframe_insert("location", frame=frame); pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=frame)
        pb.keyframe_insert("scale", frame=frame)
    _ACT["keys"].append(frame)
    if "hits" in G:                                   # pose_fix loaded: report limb/weapon clipping per key
        clips = {pc: hits(pc) for pc in CLIP_PIECES if bpy.data.objects.get(PREFIX + pc)}
        bad = {k: v for k, v in clips.items() if v}
        if bad: print(f"ANIM clip f{frame}: {bad}")
def reset_keep_action():
    act = rig.animation_data.action
    for pb in P:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.rotation_mode = 'XYZ'; pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.animation_data.action = act
def mark(name, frame):
    _ACT["act"].pose_markers.new(name).frame = frame
def end(ease="BEZIER"):
    act = _ACT["act"]
    fcs = act.fcurves if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = ease
    names = {m.name: m.frame for m in act.pose_markers}
    problems = []
    if any(m in names for m in ("HitStart", "Tell")):                      # it's an attack: enforce fairness rules
        for m in REQUIRED_ATTACK_MARKERS:
            if m not in names: problems.append(f"missing marker {m}")
        if not problems:
            if names["HitStart"] - names["Tell"] < 8: problems.append("tell < 8 f")
            if _ACT["length"] - names["RecoverStart"] < 18: problems.append("recovery < 18 f")
    print(f"ANIM {_ACT['name']} {_ACT['length']} f keys={_ACT['keys']} markers={names} " + ("OK" if not problems else "RULES: " + ", ".join(problems)))
    return not problems
# ---------------- direction-safe posing helpers (no guessing Euler signs per rig) ----------------
def _upd(): bpy.context.view_layer.update()
def rot_dir(bone, amt, probe, want, axis="x"):
    """Rotate `bone` by |amt| about its local axis in whichever sign moves `probe` (a bone name, measured at its tail)
       along world vector `want`. e.g. rot_dir("UpperTorso", 0.3, "Head", (0, -1, 0)) = lean forward 0.3 rad."""
    _upd(); t0 = rig.matrix_world @ P[probe].tail
    i = "xyz".index(axis); e = list(P[bone].rotation_euler); e[i] += amt; P[bone].rotation_euler = e; _upd()
    if ((rig.matrix_world @ P[probe].tail) - t0).dot(Vector(want)) < 0:
        e[i] -= 2*amt; P[bone].rotation_euler = e; _upd()
def reach(side, target, pole_side=1.0):
    """IK the arm so the wrist lands on world `target` (elbow pushed outward/down), then bake to FK."""
    ua = f"{side}UpperArm"; s = 1 if side == "Left" else -1
    sh = rig.matrix_world @ P[ua].head
    pole = sh + Vector((0.6*s*pole_side, 0.3, -0.5))
    _ik(f"{side}LowerArm", tuple(rig.matrix_world.inverted() @ Vector(target)), tuple(rig.matrix_world.inverted() @ pole))
    _bake([ua, f"{side}LowerArm"])
def aim_weapon(direction, hand="RightHand", socket="Weapon_R"):
    """Turn the hand so the weapon socket points along world `direction` (grip stays in the palm)."""
    _upd(); pb = P[socket]; cur = (rig.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    hb = P[hand]; h = hb.head.copy(); R = rig.matrix_world.to_3x3().inverted() @ q.to_matrix() @ rig.matrix_world.to_3x3()
    hb.matrix = Matrix.Translation(h) @ R.to_4x4() @ Matrix.Translation(-h) @ hb.matrix; _upd()
def world(bone, end="head"):
    _upd(); return rig.matrix_world @ getattr(P[bone], end)
