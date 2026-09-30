# Shared setup for the staff actions (exec'd first by Reap / casts / flinch / stagger): the pose system, the guard
# (guard() + pose() from Idle_Guard), and K() = a full pose-parameter dict built on the guard, so every key lists
# every parameter and param_keys can re-solve each in-between.
exec(open(HERE + r"\anims\the_ascendant\_asc_pose.py").read())
exec(open(HERE + r"\anims\the_ascendant\Idle_Guard.py").read().split("GUARD = guard(0.0)")[0])   # guard() + pose()
def K(**kw):
    p = dict(guard(0.0), grip=0.0, free=0.0); p.update(kw)
    for k in ("C", "D", "E", "fL", "fR"): p[k] = Vector(p[k])
    return p
GUARD = K()
FEET_WIDE = dict(fL=(0.10, -0.32, 0), fR=(-0.10, 0.22, 0))     # fighting stance for swings
