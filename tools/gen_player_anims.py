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
        lowest = min(lowest, pos[1])
        if part in TIPS:
            tip = matvec(rot, TIPS[part])
            lowest = min(lowest, pos[1] + tip[1])
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


def sample(keys, part, u):
    """The part's six numbers at fraction u (0..1) of the clip."""
    times = [k["t"] for k in keys]
    if u <= times[0]:
        return channel(keys[0], part)
    if u >= times[-1]:
        return channel(keys[-1], part)
    i = max(j for j in range(len(times) - 1) if times[j] <= u)
    t = (u - times[i]) / (times[i + 1] - times[i])
    p0 = channel(keys[max(i - 1, 0)], part)
    p1 = channel(keys[i], part)
    p2 = channel(keys[i + 1], part)
    p3 = channel(keys[min(i + 2, len(keys) - 1)], part)
    return tuple(catmull_rom(p0[c], p1[c], p2[c], p3[c], t) for c in range(6))


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

CLIPS = {
    # "grounded": the ground-contact solver sets the root height every frame,
    # so the keys' own root heights are only hints.
    "RollForward": {"keys": ROLL_FORWARD, "length": 0.5, "loop": False, "grounded": True},
    "RollBackward": {"keys": ROLL_BACKWARD, "length": 0.5, "loop": False, "grounded": True},
    "RollLeft": {"keys": ROLL_LEFT, "length": 0.5, "loop": False, "grounded": True},
    "RollRight": {"keys": mirror(ROLL_LEFT), "length": 0.5, "loop": False, "grounded": True},
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
        values = {p: sample(clip["keys"], p, u) for p in PARTS}
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
    start, end = sample(keys, "LowerTorso", 0), sample(keys, "LowerTorso", 1)
    for c in range(3):
        if abs(((end[c] - start[c]) + 180) % 360 - 180) > 1e-6:
            errors.append("the root must end upright (a whole number of turns)")
            break
    for c in range(3, 6):
        if abs(end[c] - start[c]) > 1e-6:
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
