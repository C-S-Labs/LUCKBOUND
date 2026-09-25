# Body profile: humanoid (R15 names; two arms with hinge elbows, two legs with hinge knees, five-finger hands).
# Rules live in _framework/pose_fix.py: hinge elbows/knees, shoulder limits, natural elbow direction, diagonal palm grip.
BODY_PIECES = ("Torso", "Waist", "LegLeft", "LegRight")
exec(open(FW + r"\pose_fix.py").read(), G)
CLIP_PIECES = ("ArmLeft", "ArmRight", "Lance", "BladeL", "BladeR")
def fix_clip(piece):                       # anim_core calls this for an in-between frame that clips
    clear_arm("Left" if ("Left" in piece or piece == "BladeL") else "Right", step=0.05, maxit=12)
