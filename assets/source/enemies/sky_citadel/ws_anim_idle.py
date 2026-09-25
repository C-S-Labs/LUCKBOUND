# IDLE loop (120 f @ 30 fps = 4 s, loops): guarding the platform. Run after ws_pose_idle.py.
# Slow breath (torso/head), faint wing sway, tabard/fauld drift; hands stay on the planted lance via IK.
# The glow pulse itself is driven in Studio (tween Neon colour/transparency on the *_Glow parts); keyed here for preview.
sc = bpy.context.scene
sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 120
act = bpy.data.actions.new("Idle_Guard"); rig.animation_data_create(); rig.animation_data.action = act
P = rig.pose.bones
base = {n: tuple(P[n].rotation_euler) for n in ("UpperTorso", "Head", "WingL", "WingR", "FauldFront1", "FauldBack1")}
def pose_at(t):
    import math
    b = math.sin(t*2*math.pi)                      # one breath per loop
    def set_(n, dx=0, dz=0):
        x, y, z = base[n]; P[n].rotation_mode = 'XYZ'; P[n].rotation_euler = (x + dx, y, z + dz)
    set_("UpperTorso", 0.012*b); set_("Head", 0.02*b)
    set_("WingL", 0.015*b, 0.03*b); set_("WingR", 0.015*b, -0.03*b)
    set_("FauldFront1", 0.02*b); set_("FauldBack1", -0.02*b)
for f in (1, 31, 61, 91, 121):
    pose_at((f - 1)/120)
    for pb in P:                                   # key EVERY bone: arms, hands, fingers and the lance socket carry the grip pose
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("scale", frame=f)
        pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
g = bpy.data.materials["GS_Glow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 2.0), (61, 7.0), (121, 2.0)):
    g.default_value = v; g.keyframe_insert("default_value", frame=f)
print("ACTION Idle_Guard 1-121 (loop)")
