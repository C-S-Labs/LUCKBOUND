# Idle_Guard (120 f loop @ 30 fps): the Ascendant's HIGH GUARD, which every P1 attack starts from and returns to.
# Staff held diagonally across the body: crescent raised high over its right shoulder, right hand at chest height,
# left hand low on the haft before the belt, butt angled down across the front. A slow breath (torso, head, grip rise and fall) keeps it alive;
# the glow pulse itself is Studio-side (tween the *_Glow parts). Every 2nd frame is a fully SOLVED pose.
exec(open(HERE + r"\anims\the_ascendant\_asc_pose.py").read())
def guard(breath=0.0):
    # crescent raised over its RIGHT shoulder, butt low across the front; right hand at chest height, left hand low
    # on the haft in front of the belt (arms hang naturally, nothing crosses the body)
    return dict(sink=0.07 - 0.008*breath, fL=Vector((0.05, -0.2, 0)), fR=Vector((-0.05, 0.2, 0)), twist=0.12, lean=0.05 - 0.02*breath,
                head=0.08 - 0.03*breath, head_turn=-0.1, C=Vector((-0.40, -0.52, 2.10 + 0.015*breath)), D=Vector((-0.42, -0.1, 0.9)),
                E=Vector((-0.2, -1, 0.1)), u=-0.55)
def pose(p):
    stance(p)
    staff(p["C"], p["D"], p["E"], two_hand=p["u"])
    ground_body()
GUARD = guard(0.0)
begin("Idle_Guard", 120, loop=True)
param_keys([(1, guard(0.0)), (61, guard(1.0)), (121, guard(0.0))], pose, step=4)
end()
