# Walk (loop): walk_core's solved humanoid walk at the boss gait (ROLE_GAIT["boss"]: shorter, slower, weightier
# stride), with the Sanctum Staff CARRIED upright in the right hand via the post= hook (left arm keeps the swing).
exec(open(HERE + r"\anims\the_ascendant\_asc_pose.py").read())
ARM_OUT = 0.17   # the free arm hangs wide enough to clear the robe's hip flare
def carry(t):
    sh = world("RightUpperArm")
    C = sh + Vector((-0.2, -0.36 + 0.03*math.cos(2*math.pi*t), -0.58))   # out beside the robe, not over it
    wield(Vector((0.22, -0.14, 1.0)).normalized(), C); roll_edge(Vector((0, -1, 0)))   # butt angled AWAY from the legs
build_walk_humanoid(role="boss", post=carry, arm_out=ARM_OUT)
