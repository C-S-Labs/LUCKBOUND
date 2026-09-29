# P1_CrescentReap (ASCENDANT_MOVESET P1 #1): 14 f tell, 5 f active, 37 f recovery. 60 f @ 30 fps. In place.
# A two-handed horizontal crescent sweep from its RIGHT across the front to its LEFT (~200 deg; the start side stays
# safe). Built with param_keys: every 2nd frame is a fully SOLVED pose (wield + hand_on on the staff, hinge knees,
# crystal feet flat), so in-betweens never bend a joint the wrong way or pass a limb through the body.
#   f1 guard   f9 coil (staff swung down and back to its right, torso wound right)   f16 tell peak (deeper, crescent
#   flares: VFX_Crescent)   f17 HitStart   f19 sweep through the front   f22 HitEnd, crescent past its left
#   f23 RecoverStart: over-rotated, crescent dragging low on its left (the punish window)   f44 still low
#   f52 staff lifted up and out in front   f60 guard
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
          C=(-0.50, -0.15, 2.25), D=(-0.35, 0.55, 0.75), E=(0, 0, 1), u=-0.3)
TELL  = K(sink=0.15, twist=-0.7, lean=0.0, head_turn=0.35, fL=(0.08, -0.28, 0), fR=(-0.1, 0.24, 0),
          C=(-0.55, 0.00, 2.30), D=(-0.25, 0.71, 0.66), E=(0, 0.2, 1), u=-0.3)
SWEEP = K(sink=0.16, twist=-0.05, lean=0.12, head_turn=0.0, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(-0.41, -0.88, 2.01), D=(-0.10, -0.99, 0.01), E=(1, 0, 0), u=-0.41)
PAST  = K(sink=0.16, twist=0.55, lean=0.16, head_turn=-0.2, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(0.51, -0.94, 1.83), D=(0.79, -0.61, 0.02), E=(0.4, 0.8, 0), u=-0.19)
DRAG  = K(sink=0.2, twist=0.7, lean=0.26, head=0.15, head_turn=-0.25, fL=(0.1, -0.32, 0), fR=(-0.1, 0.22, 0),
          C=(0.40, -0.69, 1.89), D=(0.81, 0.07, -0.58), E=(0.3, 0.9, -0.2), u=-0.3)
LIFT  = K(sink=0.15, twist=0.45, lean=0.16, head_turn=-0.15, fL=(0.09, -0.29, 0), fR=(-0.09, 0.22, 0),
          C=(0.03, -0.93, 2.09), D=(0.51, -0.80, 0.30), E=(0.2, 0.9, 0.1), u=-0.45)   # staff comes up OUT front, butt clear of the belt
RISE  = K(sink=0.12, twist=0.25, lean=0.12, head_turn=-0.1, fL=(0.08, -0.26, 0), fR=(-0.08, 0.22, 0),
          C=(-0.30, -0.70, 2.05), D=(-0.35, -0.20, 0.92), E=(-0.2, -1, 0.1), u=-0.45)   # staff lifted up and OUT, never across
begin("P1_CrescentReap", 60)
param_keys([(1, GUARD), (9, COIL), (16, TELL), (19, SWEEP), (22, PAST), (26, DRAG), (44, DRAG), (48, LIFT), (52, RISE), (60, GUARD)], pose, step=2,
           arcs={"C": (0.0, -0.22, 0.06), "D": (0.0, -0.25, 0.2)})   # hands AND crescent swing out in front, over the waist
mark("Tell", 3); mark("VFX_Crescent", 14); mark("HitStart", 17); mark("HitEnd", 22); mark("RecoverStart", 23)
end()
