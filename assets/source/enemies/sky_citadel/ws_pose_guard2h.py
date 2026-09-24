# TWO-HANDED COMBAT GUARD: low wide stance, lance levelled diagonally across the body toward the player,
# right hand on the grip, left hand forward on the shaft, wings half-raised. Hands placed with IK.
from mathutils import Matrix, Vector
P = rig.pose.bones
def r(n, x=0, y=0, z=0):
    P[n].rotation_mode = 'XYZ'; P[n].rotation_euler = (x, y, z)
r("LowerTorso", -0.1, 0.2, 0); r("UpperTorso", 0.25, -0.3, 0); r("Head", -0.2, 0.1, 0)
r("LeftUpperLeg", -0.65, 0, 0.12); r("LeftLowerLeg", 0.85, 0, 0); r("LeftFoot", -0.15, 0, 0)
r("RightUpperLeg", 0.35, 0, -0.12); r("RightLowerLeg", 0.55, 0, 0); r("RightFoot", -0.5, 0, 0)
r("FauldFront1", 0.45, 0, 0); r("FauldFront2", -0.2, 0, 0)
r("WingL", 0.1, 0, -0.25); r("WingL_Tip", 0, 0, -0.2); r("WingR", 0.1, 0, 0.25); r("WingR_Tip", 0, 0, 0.2)
G = Vector((-0.35, -0.45, 1.85))                       # right-hand grip, by the right hip
D = Vector((0.35, -0.93, -0.12)).normalized()             # lance direction: forward, across, slightly up
def ik(bone, target, pole=None):
    e = bpy.data.objects.new(f"IK_{bone}", None); bpy.context.scene.collection.objects.link(e); e.location = target
    c = P[bone].constraints.new('IK'); c.target = e; c.chain_count = 2
    return e
_c = ik("RightLowerArm", tuple(G + Vector((0, 0.12, 0.10))))
bpy.context.view_layer.update()
def aim_hand(hand, bone_dir_fn, want):
    bpy.context.view_layer.update()
    cur = bone_dir_fn()
    q = cur.rotation_difference(want)
    hb = P[hand]; h = hb.head.copy()
    hb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ hb.matrix
# right hand: Weapon_R straight up
aim_hand("RightHand", lambda: (P["Weapon_R"].tail - P["Weapon_R"].head).normalized(), D)
bpy.context.view_layer.update()
exec(open(FW + r"\pose_fix.py").read())
_bake(["RightUpperArm", "RightLowerArm"])
grip_lance(); wrap("Right")
hand_on("Left", 0.6, (0.4, 0.6, 0.3))
ground(globals().get("LANCE_OBJS", []))
