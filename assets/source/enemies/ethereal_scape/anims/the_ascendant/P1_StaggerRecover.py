# P1_StaggerRecover (45 f): the stagger ends. He plants the staff, straightens up, re-grips with the left hand and
# returns to guard. Plays after P1_Stagger; ends exactly on Idle_Guard's first pose.
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
_W = dict(fL=(0.14, -0.20, 0), fR=(-0.14, 0.14, 0))
STAG_A = K(sink=0.30, twist=0.20, lean=0.42, head=0.30, head_turn=0.15, **_W, grip=1.0, free=1.0,
           C=(-0.15, -0.55, 1.55), D=(0.40, -0.30, -0.86), E=(0, -1, 0), u=-0.5)
PLANT = K(sink=0.20, twist=0.10, lean=0.22, head=0.10, **_W, grip=1.0, free=1.0,
          C=(-0.20, -0.60, 1.80), D=(0.12, -0.35, 0.93), E=(0, -1, 0), u=-0.5)
STAND = K(sink=0.10, twist=0.10, lean=0.08, C=(-0.22, -0.55, 2.10), D=(-0.35, -0.20, 0.91), E=(-0.2, -1, 0.1), u=-0.7)
begin("P1_StaggerRecover", 45)
param_keys([(1, STAG_A), (14, PLANT), (30, STAND), (45, GUARD)], pose, step=2)
end()
