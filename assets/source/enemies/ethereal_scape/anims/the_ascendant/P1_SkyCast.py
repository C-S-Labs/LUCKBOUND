# P1_SkyCast (ranged, area): the staff is raised overhead, the orb blazes, then a small downward jab releases the spell
# (lattice / starfall / crown flare). 66 f. Tell 3, VFX_Cast 20 (orb overhead), HitStart 34 (spell released),
# HitEnd 40, RecoverStart 42 (24 f).
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
UP = K(sink=0.06, twist=-0.10, lean=-0.14, C=(-0.25, -0.30, 2.50), D=(0.0, 0.06, 1.0), E=(0, -1, 0), u=-0.45)
UP2 = K(sink=0.04, twist=-0.10, lean=-0.18, C=(-0.25, -0.30, 2.60), D=(0.0, 0.10, 1.0), E=(0, -1, 0), u=-0.45)
JAB = K(sink=0.16, twist=0.10, lean=0.12, C=(-0.28, -0.40, 2.40), D=(0.0, -0.30, 0.95), E=(0, -1, 0), u=-0.45)
begin("P1_SkyCast", 66)
param_keys([(1, GUARD), (16, UP), (28, UP2), (34, JAB), (42, JAB), (66, GUARD)], pose, step=2)
mark("Tell", 3); mark("VFX_Cast", 20); mark("HitStart", 34); mark("HitEnd", 40); mark("RecoverStart", 42)
end()
