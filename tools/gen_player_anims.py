"""Generates the player's hand-authored animation clips as Roblox KeyframeSequences.

    python tools/gen_player_anims.py

Writes assets/rbxm/animations/<Slot>.rbxmx, one per clip, named for its slot in
src/shared/Content/Animations/Player.luau. Rojo syncs the folder into
ReplicatedStorage.LuckboundAnimations, where:

  * in Studio, CharacterAnimator registers each one for a temporary id and plays
    it straight away (no upload), for any slot whose content id is still "";
  * to ship a clip, right-click it in Explorer -> Save to Roblox (under the group
    that owns the place), and paste the id into its slot.

HOW A CLIP IS DESCRIBED. A clip is a few KEY POSES at fractions of its length.
Each pose gives, per R15 body part, a rotation (degrees about X, Y, Z, applied in
that order in the parent part's space) and optionally a translation (studs). A
part a key leaves out holds the neutral pose. Between keys the angles follow a
Catmull-Rom curve, so motion flows through the keys rather than stopping at each
one, and every frame is baked at FPS so no Roblox easing enum is involved.

AXES (R15, every Motor6D frame is unrotated): X is the body's right, Y up, and Z
BACK (forward is -Z). So, for example:
  * +X on an upper leg or upper arm swings it forward; +X on a lower arm bends
    the elbow; -X on a lower leg bends the knee;
  * -X on UpperTorso or Head bends forward; -X on LowerTorso (the Root joint)
    tips the whole body forward, which is what a forward roll turns through;
  * +Z tips the top to the LEFT; a left arm moves outward with -Z, a right arm
    with +Z.
Mirroring (for a clip's opposite side) swaps Left/Right parts and negates Y and
Z rotations and X translation.

Presentation only; see docs/PLAYER_ANIMATION_BRIEF.md for what each clip must
read as, and PLAYER_ABILITIES.md §2.7 for how clips are played.
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "rbxm", "animations")

FPS = 30

# The R15 pose tree: each part's Pose nests inside its parent's, starting at the
# HumanoidRootPart. Pose names are the moving part's name.
TREE = {
    "HumanoidRootPart": ["LowerTorso"],
    "LowerTorso": ["UpperTorso", "LeftUpperLeg", "RightUpperLeg"],
    "UpperTorso": ["Head", "LeftUpperArm", "RightUpperArm"],
    "LeftUpperArm": ["LeftLowerArm"],
    "LeftLowerArm": ["LeftHand"],
    "RightUpperArm": ["RightLowerArm"],
    "RightLowerArm": ["RightHand"],
    "LeftUpperLeg": ["LeftLowerLeg"],
    "LeftLowerLeg": ["LeftFoot"],
    "RightUpperLeg": ["RightLowerLeg"],
    "RightLowerLeg": ["RightFoot"],
    "Head": [],
    "LeftHand": [],
    "RightHand": [],
    "LeftFoot": [],
    "RightFoot": [],
}
PARTS = [p for p in TREE if p != "HumanoidRootPart"]

# AnimationPriority.Action; CharacterAnimator sets priority itself anyway.
PRIORITY_ACTION = 2


# === maths ===================================================================


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def euler_xyz(rx, ry, rz):
    """Roblox CFrame.fromEulerAnglesXYZ: Rx * Ry * Rz, degrees in."""
    return matmul(matmul(rot_x(math.radians(rx)), rot_y(math.radians(ry))), rot_z(math.radians(rz)))


def catmull_rom(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * (
        (2 * p1)
        + (-p0 + p2) * t
        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
        + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    )


# === the body, for ground contact ============================================
# Approximate R15 joint positions, each relative to its parent's joint, in the
# parent's space, and the far end of each end part. Close enough for the solver
# below to keep a rolling body on the floor; exact avatar sizes vary anyway.

JOINTS = {
    "LowerTorso": (0, 0, 0),
    "UpperTorso": (0, 0.5, 0),
    "Head": (0, 1.5, 0),
    "LeftUpperArm": (-1.0, 1.3, 0),
    "LeftLowerArm": (0, -1.1, 0),
    "LeftHand": (0, -1.0, 0),
    "RightUpperArm": (1.0, 1.3, 0),
    "RightLowerArm": (0, -1.1, 0),
    "RightHand": (0, -1.0, 0),
    "LeftUpperLeg": (-0.5, -0.2, 0),
    "LeftLowerLeg": (0, -1.25, 0),
    "LeftFoot": (0, -1.25, 0),
    "RightUpperLeg": (0.5, -0.2, 0),
    "RightLowerLeg": (0, -1.25, 0),
    "RightFoot": (0, -1.25, 0),
}
TIPS = {
    "Head": (0, 0.9, 0),
    "LeftHand": (0, -0.4, 0),
    "RightHand": (0, -0.4, 0),
    "LeftFoot": (0, -0.1, -0.6),
    "RightFoot": (0, -0.1, -0.6),
}
PARENT = {child: parent for parent, children in TREE.items() for child in children}

# THICKNESS. A body is not a stick figure: each joint point is the centre of a
# part about this many studs thick, so a torso lying flat reaches the floor
# half its depth below its centre line. Without this the first roll clips
# sank ~0.5 studs into the floor (owner's walk, 2026-09-28).
RADIUS = {
    "LowerTorso": 0.55,
    "UpperTorso": 0.55,
    "Head": 0.6,
    "LeftUpperArm": 0.35,
    "RightUpperArm": 0.35,
    "LeftLowerArm": 0.32,
    "RightLowerArm": 0.32,
    "LeftHand": 0.3,
    "RightHand": 0.3,
    "LeftUpperLeg": 0.4,
    "RightUpperLeg": 0.4,
    "LeftLowerLeg": 0.35,
    "RightLowerLeg": 0.35,
    "LeftFoot": 0.3,
    "RightFoot": 0.3,
}
# Extra points inside a part that can touch the floor on their own: the
# shoulders' outer edge and the head's centre.
EXTRA_POINTS = {
    "UpperTorso": [(0, 1.3, 0.45), (0, 1.3, -0.45), (0, 0.4, 0.45), (0, 0.4, -0.45)],
    "LowerTorso": [(0, 0.1, 0.45), (0, 0.1, -0.45)],
    "Head": [(0, 0.55, 0)],
}
# A little air between the body and the floor at the lowest point.
CLEARANCE = 0.1


def matvec(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def lowest_point(values):
    """The lowest Y of the body (joints and end tips) for one frame's values,
    relative to the root joint with the root's own translation ignored."""
    world = {"HumanoidRootPart": ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0])}
    lowest = math.inf
    for part in PARTS:  # parents come before children in TREE order
        rot0, pos0 = world[PARENT[part]]
        rx, ry, rz, tx, ty, tz = values[part]
        offset = list(JOINTS[part])
        if part != "LowerTorso":
            offset = [offset[0] + tx, offset[1] + ty, offset[2] + tz]
        pos = [pos0[i] + d for i, d in enumerate(matvec(rot0, offset))]
        rot = matmul(rot0, euler_xyz(rx, ry, rz))
        world[part] = (rot, pos)
        r = RADIUS[part]
        lowest = min(lowest, pos[1] - r)
        if part in TIPS:
            tip = matvec(rot, TIPS[part])
            lowest = min(lowest, pos[1] + tip[1] - r)
        for point in EXTRA_POINTS.get(part, []):
            lowest = min(lowest, pos[1] + matvec(rot, point)[1] - r)
    return lowest


# Where the lowest point sits when standing in the neutral pose: the floor.
STANDING_LOWEST = None


def ground(values):
    """GROUND CONTACT: sets the root's height so the body's lowest point is on
    the floor, whatever the rotation. A rolling body then rolls along the
    floor instead of sinking through it or floating over it."""
    global STANDING_LOWEST
    if STANDING_LOWEST is None:
        STANDING_LOWEST = lowest_point({p: NEUTRAL for p in PARTS})
    rx, ry, rz, tx, _, tz = values["LowerTorso"]
    lift = STANDING_LOWEST - lowest_point(values)
    # Standing is exact; anything else keeps a hair of air under it.
    if lift > 1e-6:
        lift += CLEARANCE
    values["LowerTorso"] = (rx, ry, rz, tx, lift, tz)
    return values


# === clips ===================================================================

NEUTRAL = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # rx, ry, rz (deg), tx, ty, tz (studs)


def channel(key, part):
    """A key's six numbers for a part, neutral where the key says nothing."""
    value = key["pose"].get(part)
    if value is None:
        return NEUTRAL
    out = list(value) + [0.0] * (6 - len(value))
    return tuple(float(v) for v in out)


def sample(keys, part, u, loop=False):
    """The part's six numbers at fraction u (0..1) of the clip. A LOOP's
    curve wraps round (its last key must equal its first), so the motion
    flows through the seam instead of easing to a stop there."""
    times = [k["t"] for k in keys]
    if u <= times[0]:
        return channel(keys[0], part)
    if u >= times[-1]:
        return channel(keys[-1], part)
    i = max(j for j in range(len(times) - 1) if times[j] <= u)
    t = (u - times[i]) / (times[i + 1] - times[i])
    n = len(keys)
    if loop:
        # Neighbours across the seam: before key 0 is the second-to-last key
        # (the last one duplicates key 0), after the last is key 1.
        before = keys[i - 1] if i > 0 else keys[n - 2]
        after = keys[i + 2] if i + 2 < n else keys[1]
    else:
        before = keys[max(i - 1, 0)]
        after = keys[min(i + 2, n - 1)]
    p0, p1, p2, p3 = channel(before, part), channel(keys[i], part), channel(keys[i + 1], part), channel(after, part)
    return tuple(catmull_rom(p0[c], p1[c], p2[c], p3[c], t) for c in range(6))


def time_reversed(keys):
    """The same keys played backward (a backpedal from a run)."""
    return [{"t": round(1 - k["t"], 6), "pose": k["pose"]} for k in reversed(keys)]


def shift_phase(keys_half, mirror_fn):
    """A full cycle from its first half: the second half is the first half
    mirrored (left and right swap), so a run's two steps match exactly."""
    first = keys_half
    second = [{"t": 0.5 + k["t"], "pose": mirror_fn([k])[0]["pose"]} for k in keys_half]
    return first + second + [{"t": 1.0, "pose": keys_half[0]["pose"]}]


def mirror(keys):
    """The same clip for the other side of the body."""
    out = []
    for key in keys:
        pose = {}
        for part, value in key["pose"].items():
            v = list(value) + [0.0] * (6 - len(value))
            swapped = (
                part.replace("Left", "\0").replace("Right", "Left").replace("\0", "Right")
            )
            pose[swapped] = (v[0], -v[1], -v[2], -v[3], v[4], v[5])
        out.append({"t": key["t"], "pose": pose})
    return out


# Shared shapes, so the four rolls read as one family.
def tuck(hips=110, knees=-130, arms=95, elbows=90, torso=-35, head=-35):
    return {
        "UpperTorso": (torso,),
        "Head": (head,),
        "LeftUpperArm": (arms, 0, -10),
        "RightUpperArm": (arms, 0, 10),
        "LeftLowerArm": (elbows,),
        "RightLowerArm": (elbows,),
        "LeftUpperLeg": (hips, 0, -6),
        "RightUpperLeg": (hips, 0, 6),
        "LeftLowerLeg": (knees,),
        "RightLowerLeg": (knees,),
        "LeftFoot": (25,),
        "RightFoot": (25,),
    }


def ready(lean=-10):
    """The pose a roll ends in: upright, knees soft, ready to run."""
    return {
        "UpperTorso": (lean,),
        "LeftUpperArm": (18, 0, -6),
        "RightUpperArm": (-8, 0, 6),
        "LeftLowerArm": (30,),
        "RightLowerArm": (35,),
        "LeftUpperLeg": (18,),
        "RightUpperLeg": (-4,),
        "LeftLowerLeg": (-28,),
        "RightLowerLeg": (-18,),
    }


def with_root(pose, rx=0.0, rz=0.0, ty=0.0, tz=0.0, ry=0.0):
    p = dict(pose)
    p["LowerTorso"] = (rx, ry, rz, 0.0, ty, tz)
    return p


# ROLL FORWARD: gather low, dive and tuck over one shoulder through a full turn,
# come up already leaning into the run. Slight yaw so it reads as a shoulder
# roll rather than a gymnast's forward roll.
ROLL_FORWARD = [
    {"t": 0.00, "pose": with_root(ready(-8))},
    {"t": 0.12, "pose": with_root(tuck(60, -80, 55, 40, -28, -15), rx=-28, ty=-0.9, ry=6)},
    {"t": 0.30, "pose": with_root(tuck(), rx=-125, ty=-1.45, tz=-0.3, ry=12)},
    {"t": 0.50, "pose": with_root(tuck(115, -135), rx=-225, ty=-1.6, ry=12)},
    {"t": 0.70, "pose": with_root(tuck(100, -120, 80, 70), rx=-318, ty=-1.25, ry=6)},
    {"t": 0.86, "pose": with_root(tuck(65, -90, 45, 45, -24, -8), rx=-352, ty=-0.65)},
    {"t": 1.00, "pose": with_root(ready(-12), rx=-360)},
]

# ROLL BACKWARD: sit back, roll over the back with hands by the ears to push,
# land on the feet facing forward. Low and quick, not a backflip.
_BACK_TUCK = tuck(120, -130, 150, 110, -22, -30)
ROLL_BACKWARD = [
    {"t": 0.00, "pose": with_root(ready(-6))},
    {"t": 0.16, "pose": with_root(tuck(90, -115, 45, 60, -22, -28), rx=22, ty=-1.35, tz=0.4)},
    {"t": 0.36, "pose": with_root(_BACK_TUCK, rx=120, ty=-1.6, tz=0.2)},
    {"t": 0.56, "pose": with_root(_BACK_TUCK, rx=228, ty=-1.5)},
    {"t": 0.76, "pose": with_root(tuck(72, -95, 120, 60, -20, -12), rx=318, ty=-1.1)},
    {"t": 0.90, "pose": with_root(tuck(40, -60, 35, 35, -14, -4), rx=352, ty=-0.55)},
    {"t": 1.00, "pose": with_root(ready(-8), rx=360)},
]

# ROLL LEFT: facing forward, the body drops and rolls sideways over the left
# shoulder through a full turn, tucked, and comes up facing forward again.
_SIDE_TUCK = tuck(95, -125, 85, 85, -20, -20)
ROLL_LEFT = [
    {"t": 0.00, "pose": with_root(ready(-6))},
    {"t": 0.12, "pose": with_root(tuck(55, -75, 50, 45, -18, -10), rz=26, ty=-0.95)},
    {"t": 0.30, "pose": with_root(_SIDE_TUCK, rz=120, ty=-1.45, rx=-10)},
    {"t": 0.50, "pose": with_root(_SIDE_TUCK, rz=222, ty=-1.55, rx=-12)},
    {"t": 0.70, "pose": with_root(tuck(90, -115, 75, 70, -18, -14), rz=316, ty=-1.2, rx=-8)},
    {"t": 0.86, "pose": with_root(tuck(55, -80, 40, 40, -14, -6), rz=352, ty=-0.6)},
    {"t": 1.00, "pose": with_root(ready(-8), rz=360)},
]


# === running =================================================================
# One step is half the cycle; the other step is the same step mirrored, so the
# two sides always match. Phase 0: left foot planted ahead, right leg driving
# back, right arm forward. Phase 0.25: passing, the right knee coming through
# high. The ground-contact solver plants the lowest foot, which gives the body
# its bob for free.


def run_step(lean=-12, stride=1.0, arms=1.0, knee_lift=1.0, twist=6):
    s, a, k = stride, arms, knee_lift
    contact = {
        "UpperTorso": (lean, -twist * a, 0),
        "Head": (-lean * 0.6, twist * a * 0.8, 0),
        "LeftUpperLeg": (38 * s, 0, 0),
        "LeftLowerLeg": (-12,),
        "LeftFoot": (-10,),
        "RightUpperLeg": (-28 * s, 0, 0),
        "RightLowerLeg": (-45 * s,),
        "RightFoot": (20,),
        "RightUpperArm": (40 * a, 0, 8),
        "RightLowerArm": (75,),
        "LeftUpperArm": (-35 * a, 0, -8),
        "LeftLowerArm": (55,),
    }
    passing = {
        "UpperTorso": (lean - 2, 0, 0),
        "Head": (-(lean - 2) * 0.6,),
        "LeftUpperLeg": (4 * s, 0, 0),
        "LeftLowerLeg": (-22,),
        "RightUpperLeg": (58 * s * k, 0, 0),
        "RightLowerLeg": (-105 * k,),
        "RightFoot": (15,),
        "RightUpperArm": (5 * a, 0, 8),
        "RightLowerArm": (80,),
        "LeftUpperArm": (0, 0, -8),
        "LeftLowerArm": (70,),
    }
    return [{"t": 0.0, "pose": contact}, {"t": 0.25, "pose": passing}]


RUN_FORWARD = shift_phase(run_step(), mirror)
# The backpedal: a shorter, upright cycle played backward, weight kept over the
# heels, arms low.
RUN_BACKWARD = time_reversed(shift_phase(run_step(lean=6, stride=0.7, arms=0.5, knee_lift=0.7, twist=3), mirror))


def strafe_step(lean_side=-9):
    """Moving RIGHT while facing forward: a quick side-step. The right leg
    reaches out, the left follows in; the body leans into the direction and
    the hips turn a touch toward it. (+Z moves a right limb outward.)"""
    apart = {
        "LowerTorso": (0, -8, lean_side),
        "UpperTorso": (-8, 6, -lean_side * 0.6),
        "Head": (4, 2, -lean_side * 0.4),
        "RightUpperLeg": (10, 0, 28),
        "RightLowerLeg": (-18,),
        "RightFoot": (0, 0, -12),
        "LeftUpperLeg": (-6, 0, -16),
        "LeftLowerLeg": (-30,),
        "LeftFoot": (0, 0, 10),
        "RightUpperArm": (20, 0, 22),
        "RightLowerArm": (60,),
        "LeftUpperArm": (15, 0, -14),
        "LeftLowerArm": (65,),
    }
    together = {
        "LowerTorso": (0, -8, lean_side),
        "UpperTorso": (-8, 6, -lean_side * 0.6),
        "Head": (4, 2, -lean_side * 0.4),
        "RightUpperLeg": (30, 0, 4),
        "RightLowerLeg": (-70,),
        "LeftUpperLeg": (4, 0, 6),
        "LeftLowerLeg": (-18,),
        "RightUpperArm": (10, 0, 14),
        "RightLowerArm": (65,),
        "LeftUpperArm": (22, 0, -10),
        "LeftLowerArm": (60,),
    }
    return [
        {"t": 0.0, "pose": apart},
        {"t": 0.5, "pose": together},
        {"t": 1.0, "pose": apart},
    ]


RUN_RIGHT = strafe_step()
RUN_LEFT = mirror(RUN_RIGHT)

# === standing ================================================================

IDLE = [
    {
        "t": 0.0,
        "pose": {
            "LowerTorso": (0, 0, 1.5),
            "UpperTorso": (-3, 2, -1.5),
            "Head": (2, -3, 0),
            "LeftUpperArm": (4, 0, -6),
            "RightUpperArm": (6, 0, 6),
            "LeftLowerArm": (14,),
            "RightLowerArm": (12,),
            "LeftUpperLeg": (4, 0, -3),
            "RightUpperLeg": (-2, 0, 5),
            "LeftLowerLeg": (-8,),
        },
    },
    {
        "t": 0.5,
        "pose": {
            "LowerTorso": (0, 0, -1),
            "UpperTorso": (-1, -2, 1),
            "Head": (-1, 6, 0),
            "LeftUpperArm": (6, 0, -5),
            "RightUpperArm": (4, 0, 7),
            "LeftLowerArm": (10,),
            "RightLowerArm": (16,),
            "LeftUpperLeg": (1, 0, -3),
            "RightUpperLeg": (2, 0, 4),
            "RightLowerLeg": (-6,),
        },
    },
]
IDLE.append({"t": 1.0, "pose": IDLE[0]["pose"]})

# The backstep: dip, push off, land a step back with the guard up, facing
# forward throughout.
_GUARD = {"LeftUpperArm": (45, 0, -12), "RightUpperArm": (55, 0, 12), "LeftLowerArm": (95,), "RightLowerArm": (100,)}
BACKSTEP = [
    {"t": 0.0, "pose": ready(-4)},
    {"t": 0.25, "pose": {**_GUARD, "UpperTorso": (-12,), "LeftUpperLeg": (35,), "RightUpperLeg": (25,), "LeftLowerLeg": (-60,), "RightLowerLeg": (-55,)}},
    {"t": 0.55, "pose": {**_GUARD, "UpperTorso": (8,), "Head": (-6,), "LeftUpperLeg": (25,), "RightUpperLeg": (-20,), "LeftLowerLeg": (-20,), "RightLowerLeg": (-35,)}},
    {"t": 0.8, "pose": {**_GUARD, "UpperTorso": (-6,), "LeftUpperLeg": (30,), "RightUpperLeg": (15,), "LeftLowerLeg": (-50,), "RightLowerLeg": (-45,)}},
    {"t": 1.0, "pose": ready(-6)},
]

# === in the air ==============================================================

JUMP_START = [
    {"t": 0.0, "pose": ready(-4)},
    {"t": 0.35, "pose": {"UpperTorso": (-18,), "LeftUpperLeg": (38,), "RightUpperLeg": (32,), "LeftLowerLeg": (-65,), "RightLowerLeg": (-60,), "LeftUpperArm": (-35, 0, -8), "RightUpperArm": (-35, 0, 8), "LeftLowerArm": (20,), "RightLowerArm": (20,)}},
    {"t": 1.0, "pose": {"UpperTorso": (-4,), "LeftUpperLeg": (-4,), "RightUpperLeg": (12,), "LeftLowerLeg": (-8,), "RightLowerLeg": (-30,), "LeftUpperArm": (70, 0, -14), "RightUpperArm": (60, 0, 14), "LeftLowerArm": (30,), "RightLowerArm": (35,)}},
]

_RISE = {"UpperTorso": (-4,), "LeftUpperLeg": (30,), "LeftLowerLeg": (-60,), "RightUpperLeg": (8,), "RightLowerLeg": (-25,), "LeftUpperArm": (55, 0, -20), "RightUpperArm": (45, 0, 22), "LeftLowerArm": (35,), "RightLowerArm": (40,)}
RISE = [
    {"t": 0.0, "pose": _RISE},
    {"t": 0.5, "pose": {**_RISE, "LeftUpperLeg": (34,), "RightUpperLeg": (12,), "LeftUpperArm": (60, 0, -24), "RightUpperArm": (50, 0, 26)}},
    {"t": 1.0, "pose": _RISE},
]

_FALL = {"UpperTorso": (-6,), "Head": (-8,), "LeftUpperLeg": (14, 0, -8), "LeftLowerLeg": (-22,), "RightUpperLeg": (-6, 0, 10), "RightLowerLeg": (-35,), "LeftUpperArm": (25, 0, -62), "RightUpperArm": (15, 0, 68), "LeftLowerArm": (25,), "RightLowerArm": (20,)}
FALL = [
    {"t": 0.0, "pose": _FALL},
    {"t": 0.5, "pose": {**_FALL, "LeftUpperArm": (15, 0, -70), "RightUpperArm": (25, 0, 60), "LeftUpperLeg": (6, 0, -8), "RightUpperLeg": (2, 0, 10)}},
    {"t": 1.0, "pose": _FALL},
]

# Landings plant the feet (grounded) and let the knees take the weight. The
# controller's own landing dip stands down while a landing clip plays.
LAND_SOFT = [
    {"t": 0.0, "pose": {"UpperTorso": (-6,), "LeftUpperLeg": (10,), "RightUpperLeg": (6,), "LeftLowerLeg": (-12,), "RightLowerLeg": (-10,), "LeftUpperArm": (25, 0, -20), "RightUpperArm": (20, 0, 22)}},
    {"t": 0.35, "pose": {"UpperTorso": (-20,), "Head": (8,), "LeftUpperLeg": (42,), "RightUpperLeg": (36,), "LeftLowerLeg": (-72,), "RightLowerLeg": (-66,), "LeftUpperArm": (30, 0, -18), "RightUpperArm": (28, 0, 18), "LeftLowerArm": (35,), "RightLowerArm": (35,)}},
    {"t": 1.0, "pose": ready(-6)},
]
LAND_HARD = [
    {"t": 0.0, "pose": {"UpperTorso": (-8,), "LeftUpperLeg": (14,), "RightUpperLeg": (8,), "LeftLowerLeg": (-16,), "RightLowerLeg": (-12,), "LeftUpperArm": (30, 0, -30), "RightUpperArm": (30, 0, 30)}},
    {"t": 0.3, "pose": {"UpperTorso": (-42,), "Head": (22,), "LeftUpperLeg": (95,), "RightUpperLeg": (70, 0, 10), "LeftLowerLeg": (-125,), "RightLowerLeg": (-110,), "RightUpperArm": (70, 0, 18), "RightLowerArm": (15,), "LeftUpperArm": (20, 0, -35), "LeftLowerArm": (40,)}},
    {"t": 0.6, "pose": {"UpperTorso": (-30,), "Head": (14,), "LeftUpperLeg": (70,), "RightUpperLeg": (50, 0, 6), "LeftLowerLeg": (-100,), "RightLowerLeg": (-85,), "RightUpperArm": (40, 0, 16), "RightLowerArm": (35,), "LeftUpperArm": (15, 0, -25), "LeftLowerArm": (40,)}},
    {"t": 1.0, "pose": ready(-8)},
]

# The air dash: the body snaps into a streamlined lean toward the dash, limbs
# trailing, then opens back up to fall. Forward and backward here; the sides
# from the forward dash turned onto the side and its mirror.
AIRDASH_FORWARD = [
    {"t": 0.0, "pose": _FALL},
    {"t": 0.3, "pose": {"LowerTorso": (-38,), "UpperTorso": (-10,), "Head": (30,), "LeftUpperLeg": (-15,), "RightUpperLeg": (-25,), "LeftLowerLeg": (-35,), "RightLowerLeg": (-50,), "LeftUpperArm": (-45, 0, -20), "RightUpperArm": (-45, 0, 20), "LeftLowerArm": (10,), "RightLowerArm": (10,)}},
    {"t": 0.7, "pose": {"LowerTorso": (-30,), "UpperTorso": (-8,), "Head": (26,), "LeftUpperLeg": (-10,), "RightUpperLeg": (-22,), "LeftLowerLeg": (-40,), "RightLowerLeg": (-55,), "LeftUpperArm": (-40, 0, -24), "RightUpperArm": (-40, 0, 24), "LeftLowerArm": (15,), "RightLowerArm": (15,)}},
    {"t": 1.0, "pose": _FALL},
]
AIRDASH_BACKWARD = [
    {"t": 0.0, "pose": _FALL},
    {"t": 0.3, "pose": {"LowerTorso": (24,), "UpperTorso": (-12,), "Head": (-10,), "LeftUpperLeg": (45,), "RightUpperLeg": (35,), "LeftLowerLeg": (-40,), "RightLowerLeg": (-30,), "LeftUpperArm": (55, 0, -15), "RightUpperArm": (55, 0, 15), "LeftLowerArm": (50,), "RightLowerArm": (50,)}},
    {"t": 0.7, "pose": {"LowerTorso": (20,), "UpperTorso": (-10,), "Head": (-8,), "LeftUpperLeg": (40,), "RightUpperLeg": (30,), "LeftLowerLeg": (-45,), "RightLowerLeg": (-35,), "LeftUpperArm": (50, 0, -20), "RightUpperArm": (50, 0, 20), "LeftLowerArm": (55,), "RightLowerArm": (55,)}},
    {"t": 1.0, "pose": _FALL},
]
AIRDASH_LEFT = [
    {"t": 0.0, "pose": _FALL},
    {"t": 0.3, "pose": {"LowerTorso": (0, 0, 34), "UpperTorso": (-6, 0, 6), "Head": (0, 0, -18), "LeftUpperLeg": (0, 0, 8), "RightUpperLeg": (0, 0, 22), "LeftLowerLeg": (-25,), "RightLowerLeg": (-45,), "LeftUpperArm": (10, 0, -35), "RightUpperArm": (10, 0, 75), "LeftLowerArm": (30,), "RightLowerArm": (10,)}},
    {"t": 0.7, "pose": {"LowerTorso": (0, 0, 28), "UpperTorso": (-6, 0, 5), "Head": (0, 0, -15), "LeftUpperLeg": (0, 0, 6), "RightUpperLeg": (0, 0, 20), "LeftLowerLeg": (-28,), "RightLowerLeg": (-48,), "LeftUpperArm": (10, 0, -40), "RightUpperArm": (10, 0, 70), "LeftLowerArm": (30,), "RightLowerArm": (15,)}},
    {"t": 1.0, "pose": _FALL},
]

CLIPS = {
    # "grounded": the ground-contact solver sets the root height every frame,
    # so the keys' own root heights are only hints.
    "RollForward": {"keys": ROLL_FORWARD, "length": 0.65, "loop": False, "grounded": True},
    "RollBackward": {"keys": ROLL_BACKWARD, "length": 0.65, "loop": False, "grounded": True},
    "RollLeft": {"keys": ROLL_LEFT, "length": 0.65, "loop": False, "grounded": True},
    "RollRight": {"keys": mirror(ROLL_LEFT), "length": 0.65, "loop": False, "grounded": True},
    # Run cycles: authored at GameConfig.CharacterAnimation.RunClipSpeed.
    "RunForward": {"keys": RUN_FORWARD, "length": 0.6, "loop": True, "grounded": True},
    "RunBackward": {"keys": RUN_BACKWARD, "length": 0.62, "loop": True, "grounded": True},
    "RunRight": {"keys": RUN_RIGHT, "length": 0.42, "loop": True, "grounded": True},
    "RunLeft": {"keys": RUN_LEFT, "length": 0.42, "loop": True, "grounded": True},
    "Idle": {"keys": IDLE, "length": 4.0, "loop": True, "grounded": True},
    "Backstep": {"keys": BACKSTEP, "length": 0.32, "loop": False, "grounded": True},
    "JumpStart": {"keys": JUMP_START, "length": 0.2, "loop": False},
    "Rise": {"keys": RISE, "length": 0.8, "loop": True},
    "Fall": {"keys": FALL, "length": 0.9, "loop": True},
    "LandSoft": {"keys": LAND_SOFT, "length": 0.24, "loop": False, "grounded": True},
    "LandHard": {"keys": LAND_HARD, "length": 0.5, "loop": False, "grounded": True},
    "AirDashForward": {"keys": AIRDASH_FORWARD, "length": 0.2, "loop": False},
    "AirDashBackward": {"keys": AIRDASH_BACKWARD, "length": 0.2, "loop": False},
    "AirDashLeft": {"keys": AIRDASH_LEFT, "length": 0.2, "loop": False},
    "AirDashRight": {"keys": mirror(AIRDASH_LEFT), "length": 0.2, "loop": False},
}


# === XML =====================================================================


def fmt(x):
    return f"{x:.6g}"


def cframe_xml(values):
    rx, ry, rz, tx, ty, tz = values
    m = euler_xyz(rx, ry, rz)
    fields = [("X", tx), ("Y", ty), ("Z", tz)]
    for i in range(3):
        for j in range(3):
            fields.append((f"R{i}{j}", m[i][j]))
    inner = "".join(f"<{k}>{fmt(v)}</{k}>" for k, v in fields)
    return f'<CoordinateFrame name="CFrame">{inner}</CoordinateFrame>'


class Refs:
    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return f"RBX{self.n:08X}"


def pose_xml(part, frame_values, refs, indent):
    values = NEUTRAL if part == "HumanoidRootPart" else frame_values[part]
    pad = "\t" * indent
    children = "".join(pose_xml(c, frame_values, refs, indent + 1) for c in TREE[part])
    return (
        f'{pad}<Item class="Pose" referent="{refs.next()}"><Properties>'
        f'<string name="Name">{part}</string>{cframe_xml(values)}'
        f'<token name="EasingDirection">0</token><token name="EasingStyle">0</token>'
        f'<float name="Weight">1</float></Properties>\n{children}{pad}</Item>\n'
    )


def build(name, clip):
    refs = Refs()
    frames = max(2, round(clip["length"] * FPS) + 1)
    body = []
    for f in range(frames):
        u = f / (frames - 1)
        values = {p: sample(clip["keys"], p, u, clip["loop"]) for p in PARTS}
        if clip.get("grounded"):
            values = ground(values)
        time = u * clip["length"]
        body.append(
            f'\t<Item class="Keyframe" referent="{refs.next()}"><Properties>'
            f'<string name="Name">Keyframe</string><float name="Time">{fmt(time)}</float>'
            f"</Properties>\n{pose_xml('HumanoidRootPart', values, refs, 2)}\t</Item>\n"
        )
    return (
        '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
        f'<Item class="KeyframeSequence" referent="{refs.next()}"><Properties>'
        f'<string name="Name">{name}</string>'
        f'<bool name="Loop">{"true" if clip["loop"] else "false"}</bool>'
        f'<token name="Priority">{PRIORITY_ACTION}</token></Properties>\n'
        + "".join(body)
        + "</Item>\n</roblox>\n"
    )


# === checks ==================================================================


def check(name, clip):
    """Cheap sanity: keys ordered 0..1, known parts, and a one-shot that ends
    where it began (a full turn counts as where it began)."""
    keys = clip["keys"]
    errors = []
    if keys[0]["t"] != 0 or keys[-1]["t"] != 1:
        errors.append("keys must start at t=0 and end at t=1")
    if any(keys[i]["t"] >= keys[i + 1]["t"] for i in range(len(keys) - 1)):
        errors.append("key times must increase")
    for key in keys:
        for part in key["pose"]:
            if part not in PARTS:
                errors.append(f"unknown part {part}")
    if clip["loop"] and keys[0]["pose"] != keys[-1]["pose"]:
        errors.append("a loop's last key must equal its first")
    start, end = sample(keys, "LowerTorso", 0), sample(keys, "LowerTorso", 1)
    for c in range(3):
        if abs(((end[c] - start[c]) + 180) % 360 - 180) > 1e-6:
            errors.append("the root must end upright (a whole number of turns)")
            break
    for c in range(3, 6):
        if not clip.get("grounded") and abs(end[c] - start[c]) > 1e-6:
            errors.append("the root must end where it began (no drift)")
            break
    return [f"{name}: {e}" for e in errors]


def main():
    errors = [e for name, clip in CLIPS.items() for e in check(name, clip)]
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, clip in CLIPS.items():
        path = os.path.join(OUT_DIR, f"{name}.rbxmx")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(build(name, clip))
        print(f"wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
