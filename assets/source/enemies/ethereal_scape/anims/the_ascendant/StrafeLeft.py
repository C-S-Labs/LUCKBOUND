# StrafeLeft (loop): circle to its LEFT around the player (walk_core side-step at the boss gait), staff carried.
exec(open(HERE + r"\anims\the_ascendant\Walk.py").read().split("build_walk_humanoid")[0])
build_strafe_humanoid(name="StrafeLeft", role="boss", side_dir=1, length=30, post=carry, arm_out=ARM_OUT)
