# Hit_React (24 f): a flinch when hit (not a stagger): chest and head snap back, the stance dips, the staff shakes and
# settles. Plays over any state. No combat markers.
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
SNAP = K(sink=0.12, twist=0.18, lean=-0.30, head=-0.25, head_turn=0.15, C=(-0.06, -0.42, 2.30), D=(-0.55, -0.15, 0.82), E=(-0.2, -1, 0.1), u=-0.85)
SETTLE = K(sink=0.08, twist=0.06, lean=-0.10, head=-0.05, C=(-0.09, -0.44, 2.33), D=(-0.60, -0.15, 0.79), E=(-0.2, -1, 0.1), u=-0.85)
begin("Hit_React", 24)
param_keys([(1, GUARD), (4, SNAP), (10, SNAP), (16, SETTLE), (24, GUARD)], pose, step=2)
end()
