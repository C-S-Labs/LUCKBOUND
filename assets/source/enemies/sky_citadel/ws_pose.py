# duelist ready stance: low, leaning in, guard arm up, sword arm drawn back, wings raised for a dash-lunge
P = rig.pose.bones
def r(n, x=0, y=0, z=0):
    P[n].rotation_mode = 'XYZ'; P[n].rotation_euler = (x, y, z)
P["HumanoidRootNode"].location = (0, 0, 0)
r("LowerTorso", -0.1, 0.25, 0)
r("UpperTorso", 0.35, -0.35, 0)
r("Head", -0.3, 0.08, 0)
r("LeftUpperArm", -1.0, 0, 0.35); r("LeftLowerArm", -1.1, 0, 0)
r("RightUpperArm", -0.45, 0, -0.25); r("RightLowerArm", -0.9, 0, 0)
r("LeftUpperLeg", -0.65, 0, 0.12); r("LeftLowerLeg", 0.85, 0, 0); r("LeftFoot", -0.15, 0, 0)
r("RightUpperLeg", 0.35, 0, -0.12); r("RightLowerLeg", 0.55, 0, 0); r("RightFoot", -0.5, 0, 0)
r("FauldFront1", 0.45, 0, 0); r("FauldFront2", -0.2, 0, 0)
r("FauldBack1", -0.1, 0, 0)
r("WingL", 0.1, 0, -0.25); r("WingL_Tip", 0, 0, -0.2)
r("WingR", 0.1, 0, 0.25); r("WingR_Tip", 0, 0, 0.2)
# level the lance: rotate the sword hand so Weapon_R points forward and slightly down, grip beside the hip
from mathutils import Matrix, Vector
bpy.context.view_layer.update()
_wb = P["Weapon_R"]
cur = (_wb.tail - _wb.head).normalized()
want = Vector((0.12, -1.0, -0.08)).normalized()
q = cur.rotation_difference(want)
hb = P["RightHand"]; h = hb.head.copy()
hb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ hb.matrix
exec(open(FW + r"\pose_fix.py").read())
grip_lance(); wrap("Right")
clear_arm("Right"); clear_arm("Left")
ground(globals().get("LANCE_OBJS", []))
