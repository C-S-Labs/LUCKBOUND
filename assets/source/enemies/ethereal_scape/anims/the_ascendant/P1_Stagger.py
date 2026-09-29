# P1_Stagger (loop, 60 f): knocked off balance (armour break / poise broken). Knees buckled, torso hunched forward, the
# staff planted low as a prop with only the right hand on it; the left arm hangs. Loops while staggered; the punish window.
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
_W = dict(fL=(0.14, -0.20, 0), fR=(-0.14, 0.14, 0))
STAG_A = K(sink=0.30, twist=0.20, lean=0.42, head=0.30, head_turn=0.15, **_W, grip=1.0, free=1.0,
           C=(-0.15, -0.55, 1.55), D=(0.40, -0.30, -0.86), E=(0, -1, 0), u=-0.5)
STAG_B = K(sink=0.33, twist=0.10, lean=0.46, head=0.34, head_turn=0.05, **_W, grip=1.0, free=1.0,
           C=(-0.18, -0.55, 1.52), D=(0.34, -0.34, -0.88), E=(0, -1, 0), u=-0.5)
begin("P1_Stagger", 60, loop=True)
param_keys([(1, STAG_A), (31, STAG_B), (61, STAG_A)], pose, step=4)
end()
