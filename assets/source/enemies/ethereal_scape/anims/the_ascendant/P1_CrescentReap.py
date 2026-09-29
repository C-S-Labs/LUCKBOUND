# P1_CrescentReap (ASCENDANT_MOVESET P1 #1): 14 f tell, 5 f active, 37 f recovery. 60 f @ 30 fps. In place.
# A two-handed horizontal crescent sweep from its RIGHT across the front to its LEFT (~200 deg; the start side stays
# safe). Built with param_keys: every 2nd frame is a fully SOLVED pose (wield + hand_on on the staff, hinge knees,
# crystal feet flat), so in-betweens never bend a joint the wrong way or pass a limb through the body.
#   f1 guard   f9 coil (staff swung down and back to its right, torso wound right)   f16 tell peak (deeper, crescent
#   flares: VFX_Crescent)   f17 HitStart   f19 sweep through the front   f22 HitEnd, crescent past its left
#   f23 RecoverStart: over-rotated, crescent dragging low on its left (the punish window)   f44 still low
#   f52 staff brought up in front   f60 guard
exec(open(HERE + r"\anims\the_ascendant\_asc_pose.py").read())
# Two-handed like a batter/axe swing (owner): left hand the bottom hand, palm opposite the right, thumb toward the
# crescent. Windup up over the right shoulder, sweep through the front, follow-through low to its left. Key poses
# were chosen by a search for straight wrists and no arm/staff clipping.
exec(open(HERE + r"\anims\the_ascendant\Idle_Guard.py").read().split("GUARD = guard(0.0)")[0])   # guard() + pose()
def K(base=None, **kw):
    p = dict(guard(0.0), grip=0.0, free=0.0); p.update(kw)
    for k in ("C", "D", "E", "fL", "fR"): p[k] = Vector(p[k])
    return p
GUARD = K()
COIL  = K(sink=0.13, twist=-0.55, lean=0.02, head_turn=0.25, fL=(0.08, -0.26, 0), fR=(-0.1, 0.24, 0),
          C=(-0.50, -0.15, 2.25), D=(-0.35, 0.55, 0.75), E=(0, 0, 1), u=-0.30)
TELL  = K(sink=0.15, twist=-0.7, lean=0.0, head_turn=0.35, fL=(0.08, -0.28, 0), fR=(-0.1, 0.24, 0),
          C=(-0.55, 0.00, 2.30), D=(-0.25, 0.71, 0.66), E=(0, 0.2, 1), u=-0.30)
SWEEP = K(sink=0.16, twist=-0.05, lean=0.12, head_turn=0.0, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(-0.19, -1.10, 1.97), D=(-0.40, -0.85, 0.33), E=(1, 0, 0), u=-0.39)
PAST  = K(sink=0.16, twist=0.55, lean=0.16, head_turn=-0.2, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(0.40, -0.75, 1.89), D=(0.74, -0.64, 0.22), E=(0.4, 0.8, 0), u=-0.36)
DRAG  = K(sink=0.2, twist=0.7, lean=0.26, head=0.15, head_turn=-0.25, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(0.62, -0.45, 1.61), D=(0.76, -0.05, -0.65), E=(0.3, 0.9, -0.2), u=-0.19)
RECOVER = K(sink=0.14, twist=0.3, lean=0.1, head_turn=-0.1, fL=(0.09, -0.27, 0), fR=(-0.09, 0.22, 0),
          C=(0.40, -0.78, 2.23), D=(-0.37, -0.51, 0.78), E=(0.1, -0.9, 0.2), u=-0.36)   # staff brought up in front, back to guard
begin("P1_CrescentReap", 60)
param_keys([(1, GUARD), (9, COIL), (16, TELL), (19, SWEEP), (22, PAST), (26, DRAG), (44, DRAG), (52, RECOVER), (60, GUARD)], pose, step=2)
mark("Tell", 3); mark("VFX_Crescent", 14); mark("HitStart", 17); mark("HitEnd", 22); mark("RecoverStart", 23)
end()
