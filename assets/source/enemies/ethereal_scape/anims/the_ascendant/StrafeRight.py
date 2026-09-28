# StrafeRight (loop): circle to its RIGHT around the player, staff carried. Mirror of StrafeLeft.
exec(open(HERE + r"\anims\the_ascendant\Walk.py").read().split("build_walk_humanoid")[0])
build_strafe_humanoid(name="StrafeRight", role="boss", side_dir=-1, length=30, post=carry, arm_out=ARM_OUT)
