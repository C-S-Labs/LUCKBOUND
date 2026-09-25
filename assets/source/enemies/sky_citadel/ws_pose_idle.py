# IDLE / GUARD-THE-PLATFORM pose: lance planted upright (butt on the ground) in front, both hands stacked on the
# shaft, head bowed, wings folded. Hands placed with IK so they sit exactly on the haft.
from mathutils import Matrix, Vector
P = rig.pose.bones
def r(n, x=0, y=0, z=0):
    P[n].rotation_mode = 'XYZ'; P[n].rotation_euler = (x, y, z)
r("Head", 0.35, 0, -0.25)
r("UpperTorso", 0.08, 0, 0)
LANCE_X, LANCE_Y = -0.40, -0.72            # where the lance stands, in front-right of the body
GRIP_U = 1.40                              # grip sits 1.40 m above the butt tip -> butt on the floor
def ik(bone, target, pole=None):
    e = bpy.data.objects.new(f"IK_{bone}", None); bpy.context.scene.collection.objects.link(e); e.location = target
    c = P[bone].constraints.new('IK'); c.target = e; c.chain_count = 2
    return e
ik("RightLowerArm", (LANCE_X - 0.06, LANCE_Y + 0.02, GRIP_U + 0.06))
bpy.context.view_layer.update()
def aim_hand(hand, bone_dir_fn, want):
    bpy.context.view_layer.update()
    cur = bone_dir_fn()
    q = cur.rotation_difference(want)
    hb = P[hand]; h = hb.head.copy()
    hb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ hb.matrix
# right hand: Weapon_R straight up
aim_hand("RightHand", lambda: (P["Weapon_R"].tail - P["Weapon_R"].head).normalized(), Vector((0, 0, 1)))
bpy.context.view_layer.update()
exec(open(FW + r"\pose_fix.py").read())
_bake(["RightUpperArm", "RightLowerArm"])
grip_lance(); wrap("Right")
ground()                                              # feet on the floor first
def _lance_minz():
    _upd(); dg = bpy.context.evaluated_depsgraph_get(); bz = 1e9
    for o in LANCE_OBJS:
        if o.hide_render: continue
        oe = o.evaluated_get(dg); m = oe.to_mesh()
        if len(m.vertices): bz = min(bz, min((o.matrix_world @ v.co).z for v in m.vertices))
        oe.to_mesh_clear()
    return bz
for _it in range(3):                                  # plant the butt on the floor: re-solve the arm with the grip lowered
    bz = _lance_minz()
    if abs(bz) < 0.004: break
    wr = RW @ P["RightLowerArm"].tail - Vector((0, 0, bz))
    _ik("RightLowerArm", tuple(RW.inverted() @ wr)); _bake(["RightUpperArm", "RightLowerArm"])
    aim_hand("RightHand", lambda: (P["Weapon_R"].tail - P["Weapon_R"].head).normalized(), Vector((0, 0, 1)))
    grip_lance(); wrap("Right")
hand_on("Left", 0.5, (0.7, 0.3, 0.0))
