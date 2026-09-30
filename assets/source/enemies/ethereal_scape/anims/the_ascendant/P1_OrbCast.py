# P1_OrbCast (ranged): the staff is drawn back, then thrust at the player; the ORB at its head fires a bolt.
# 54 f. Tell 3, VFX_Cast 12 (orb charging), HitStart 18 (the bolt spawns at VFX_Orb), HitEnd 22, RecoverStart 24 (30 f).
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
AIM = dict(**FEET_WIDE)
PULL = K(sink=0.12, twist=-0.25, lean=-0.10, **AIM, C=(-0.30, -0.15, 2.05), D=(-0.10, -0.55, 0.83), E=(0, 0, 1), u=-0.5)
THRUST = K(sink=0.18, twist=0.10, lean=0.22, **AIM, C=(-0.30, -0.65, 2.00), D=(0.0, -0.98, 0.20), E=(0, 0, 1), u=-0.5)
HOLD = K(sink=0.17, twist=0.10, lean=0.20, **AIM, C=(-0.30, -0.62, 2.02), D=(0.0, -0.97, 0.24), E=(0, 0, 1), u=-0.5)
begin("P1_OrbCast", 54)
param_keys([(1, GUARD), (12, PULL), (18, THRUST), (24, HOLD), (34, HOLD), (54, GUARD)], pose, step=2)
mark("Tell", 3); mark("VFX_Cast", 12); mark("HitStart", 18); mark("HitEnd", 22); mark("RecoverStart", 24)
end()
