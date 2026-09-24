# Body profile TEMPLATE: copy to <biome>/bodies/<name>.py (biome-specific) or _framework/bodies/<name>.py (shared),
# then set  "body": "<name>"  in the biome manifest. run.py loads <biome>/bodies/<name>.py first, else the framework one.
# Example: a fish boss with fins that holds a trident -> "body": "finned". It must NOT reuse humanoid elbows:
# fins bend as a flexible chain, the grip is a fin-wrap, etc. Implement ONLY what this body needs:
exec(open(FW + r"\pose_common.py").read(), G)     # generic: hits(), ground(), _tree(), _upd()
BODY_PIECES = ("Body",)                  # pieces a limb/weapon must not pass through
CLIP_PIECES = ("FinL", "FinR", "Weapon")  # pieces scanned for clipping every other frame by anim_core
JOINTS = {                               # your joint rules (bone -> allowed local rotation ranges, radians)
    # "FinL_01": {"x": (-0.6, 0.6), "y": (0, 0), "z": (-0.3, 0.3)},
}
def joint_report(tag=""):
    """Return a list of problems (strings); anim_core prints them per key and flags them."""
    bad = []
    for bn, lim in JOINTS.items():
        e = P[bn].matrix_basis.to_euler('XYZ')
        for i, ax in enumerate("xyz"):
            lo, hi = lim.get(ax, (-9, 9))
            if not (lo - 0.02 <= e[i] <= hi + 0.02): bad.append(f"{bn} {ax}={e[i]:.2f}")
    if bad: print(f"JOINTS {tag}: BAD: " + ", ".join(bad))
    return bad
def fix_clip(piece):
    """Called for an in-between frame where `piece` clips: nudge this body's own joints clear (optional)."""
    pass
# Optional, body-specific solvers used by your action files, e.g.:
# def wield(direction, point): ...   (how THIS body holds a weapon - fin wrap, tail curl, telekinesis, ...)
