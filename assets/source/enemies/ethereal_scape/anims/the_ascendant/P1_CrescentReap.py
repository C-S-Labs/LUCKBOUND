# P1_CrescentReap (ASCENDANT_MOVESET P1 #1): the close-range attack, a fluid two-handed OVERHEAD AXE CHOP. 60 f @ 30 fps,
# in place. The staff goes straight UP and BACK over the shoulder (the windup), chops down and forward THROUGH the
# player, follows through low to its left, holds (the punish window), then lifts back to guard.
#   f1 guard  f8 rising  f16 tell peak (staff up and back, VFX_Crescent)  f17 HitStart  f19 the blade is on the player
#   f22 HitEnd, past the player  f23 RecoverStart  f30-44 low follow-through  f52 staff up in front  f60 guard
# HIT_POINT is where the player's torso is in front of the boss (the scale blockout's centre): the crescent's middle
# is placed exactly there on the strike frame, so the blade visibly crosses the player. Tune it here.
exec(open(HERE + r"\anims\the_ascendant\_asc_moves.py").read())
HIT_POINT = Vector((0.0, -2.1, 1.15))        # player torso centre, ~2.1 m in front of the boss's axis
U_MID = 2.15                                 # the crescent's middle, along the haft from the right-hand grip
_D_STRIKE = Vector((0.10, -0.93, -0.35)).normalized()
_C_STRIKE = HIT_POINT - _D_STRIKE*U_MID      # so grip + haft*U_MID lands on HIT_POINT
RAISE = K(sink=0.08, twist=-0.25, lean=-0.06, head_turn=0.1, **FEET_WIDE,
          C=(-0.26, 0.05, 2.30), D=(-0.10, 0.20, 0.97), E=(0, -1, 0), u=-0.5)
TELL  = K(sink=0.12, twist=-0.45, lean=-0.14, head_turn=0.2, **FEET_WIDE,
          C=(-0.28, 0.20, 2.50), D=(0.0, 0.42, 0.91), E=(0, -1, 0), u=-0.35)          # straight up and back
STRIKE = K(sink=0.20, twist=0.25, lean=0.30, head_turn=0.0, **FEET_WIDE,
          C=_C_STRIKE, D=_D_STRIKE, E=(0, -0.3, -0.95), u=-0.45)                    # the blade is ON the player
FOLLOW = K(sink=0.22, twist=0.50, lean=0.32, head_turn=-0.2, **FEET_WIDE,
          C=(0.06, -0.55, 1.55), D=(0.42, -0.62, -0.66), E=(0.3, -0.2, -0.9), u=-0.45)
LOW   = K(sink=0.22, twist=0.60, lean=0.30, head=0.12, head_turn=-0.25, **FEET_WIDE,
          C=(0.50, -0.50, 1.60), D=(0.74, -0.10, -0.66), E=(0.3, 0.6, -0.5), u=-0.5)
UPFRONT = K(sink=0.14, twist=0.25, lean=0.10, head_turn=-0.1, **FEET_WIDE,
          C=(0.15, -0.70, 1.95), D=(0.20, -0.55, 0.81), E=(-0.2, -1, 0.1), u=-0.65)
begin("P1_CrescentReap", 60)
param_keys([(1, GUARD), (8, RAISE), (16, TELL), (19, STRIKE), (22, FOLLOW), (30, LOW), (44, LOW), (52, UPFRONT), (60, GUARD)],
           pose, step=2)
mark("Tell", 3); mark("VFX_Crescent", 14); mark("HitStart", 17); mark("HitEnd", 22); mark("RecoverStart", 23)
end()
