# PHASE-2 TRANSITION action (60 frames @ 30 fps = 2 s, unskippable).
#   f1  P1 duelist stance          f18 stagger: hunched, wings clamp in, core dims
#   f30 BURST (marker ArmourBreak): chest thrown back, arms flung wide, core flares -> Studio flings Break_* debris
#   f30-44 LANCE: halo shrinks + draws into the collar (fuel); blade halves step out and fan back like wings
#   f44 plasma blade + energy webbing ignite (marker LanceIgnite)   f60 P2 stance, wings fully extended (marker P2Start)
# Markers become AnimationEvents in Studio. Break_* debris motion here is a Blender-only preview.
from mathutils import Matrix, Vector
OUT = HERE
P = rig.pose.bones
sc = bpy.context.scene
sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 60
act = bpy.data.actions.new("P2_Transition"); rig.animation_data_create(); rig.animation_data.action = act
def reset():
    for pb in P:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
        for c in list(pb.constraints): pb.constraints.remove(c)
    bpy.context.view_layer.update()
def to_euler():
    # matrix-set bones may have written into rotation_euler already (mode XYZ); nothing to convert
    pass
def key(frame):
    for pb in P:
        pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=frame); pb.keyframe_insert("location", frame=frame); pb.keyframe_insert("scale", frame=frame)
def r(n, x=0, y=0, z=0):
    P[n].rotation_mode = 'XYZ'; P[n].rotation_euler = (x, y, z)
def add(n, x=0, y=0, z=0):
    e = P[n].rotation_euler; P[n].rotation_euler = (e.x + x, e.y + y, e.z + z)
def wrot(name, axis, ang):
    bpy.context.view_layer.update()
    pb = P[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ pb.matrix
def wings_out(amount=1.0):
    if "wings_open" in globals():
        wings_open(amount); return
    for W, s in (("WingL", 1), ("WingR", -1)):
        wrot(W, 'Y', 0.45*s*amount)
        bpy.context.view_layer.update()
        pb = P[W]; axis = (pb.tail - pb.head).normalized()
        hang = pb.matrix.to_3x3() @ (rig.data.bones[W].matrix_local.to_3x3().inverted() @ Vector((0.2*s, 0.4, -1.0)))
        best = max((1.35, -1.35), key=lambda a: s*(Matrix.Rotation(a, 3, axis) @ hang).x)
        wrot(W, axis, best*amount)
        wrot(W + "_Tip", 'Z', 0.25*s*amount)
    bpy.context.view_layer.update()
P1 = open(OUT + r"\ws_pose.py").read()

# f1: P1 stance
reset(); exec(P1); key(1)
root_z = P["HumanoidRootNode"].location.copy()
# f18: stagger
add("UpperTorso", 0.35, 0, 0); add("Head", 0.35, 0, 0); add("LowerTorso", 0.1, 0, 0)
add("LeftUpperArm", 0.5, 0, -0.2); add("RightUpperArm", 0.3, 0, 0.1)
add("WingL", 0, 0, 0.15); add("WingR", 0, 0, -0.15)
P["HumanoidRootNode"].location = root_z + Vector((0, -0.12, 0))
key(18)
# f30: burst
reset(); exec(P1)
add("UpperTorso", -0.55, 0, 0); add("Head", -0.5, 0, 0)
add("LeftUpperArm", 0.9, 0, 0.9); add("LeftLowerArm", 0.8, 0, 0)
add("RightUpperArm", 0.4, 0, -0.5)
wings_out(0.35)
P["HumanoidRootNode"].location = root_z + Vector((0, 0.05, 0))
key(30)
# f44: wings unfurling, body coming back down
reset(); exec(P1); add("UpperTorso", -0.35, 0, 0); wings_out(0.55)
if "lance_open" in globals(): lance_open(0.5)
key(38)
reset(); exec(P1); add("UpperTorso", -0.2, 0, 0); wings_out(0.85)
if "lance_open" in globals(): lance_open(1.0)
key(44)
# f60: P2 stance
reset(); exec(P1); wings_out(1.0)
if "lance_open" in globals(): lance_open(1.0)
key(60)
for fc in act.fcurves if hasattr(act, "fcurves") else []:
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
m = sc.timeline_markers.new("ArmourBreak", frame=30); m2 = sc.timeline_markers.new("P2Start", frame=60)
act.pose_markers.new("ArmourBreak").frame = 30; act.pose_markers.new("LanceIgnite").frame = 44; act.pose_markers.new("P2Start").frame = 60

# ---- Blender preview of the debris + glow flare (not exported as bone animation) ----
core = rig.matrix_world @ P["VFX_Core"].head
for o in PARTS:
    if "_Break" not in o.name:
        continue
    me = o.data
    c = sum((v.co for v in me.vertices), Vector()) / max(1, len(me.vertices))
    d = (c - Vector((0, 0, 1.9))); d.z = max(d.z, 0) + 0.2; d.normalize()
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    o.keyframe_insert("location", frame=29); o.keyframe_insert("rotation_euler", frame=29); o.keyframe_insert("scale", frame=29)
    L_ = d*1.8 + Vector((0, 0, -0.6)); L_.z = max(L_.z, -c.z + 0.1)   # debris lands ON the floor, never through it
    o.location = L_; o.rotation_euler = (d.y*2.5, d.x*2.5, d.z*1.5)
    o.keyframe_insert("location", frame=48); o.keyframe_insert("rotation_euler", frame=48)
    o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=52)
    o.scale = (0.001, 0.001, 0.001); o.keyframe_insert("scale", frame=56)
g = bpy.data.materials["GS_Glow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 4), (18, 1.5), (28, 6), (30, 18), (40, 8), (60, 6)):
    g.default_value = v; g.keyframe_insert("default_value", frame=f)
for ob in globals().get("LANCE_OBJS", []):
    if ob.name.startswith("WingedSentinel_Beam"):
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=43)
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=44)
    if ob.name.startswith("WingedSentinel_Halo"):
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=43)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=44)
print("ACTION", act.name, "frames 1-60, markers ArmourBreak@30 P2Start@60")
