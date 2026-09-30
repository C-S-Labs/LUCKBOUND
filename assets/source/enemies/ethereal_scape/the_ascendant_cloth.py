# LUCKBOUND - The Ascendant's cloth (manifest "extras", after the body and the staff). Data only: the framework's
# cloth_core builds the chains, re-skins the pieces and bakes the motion into every action.
#   Robe  - the front-slit two-panel robe hangs free from the hips as a skirt of 10 chains and collides with both
#           legs and arms, so a raised knee pushes the robe instead of passing through it. Belt pieces above `top` stay rigid;
#           the hem spikes ride the robe rigidly.
#   Scarf - the four ribbons down its back (two from the shoulders, two from the waist, each with its glow + tip)
#           trail as chains and collide with the back, hips, legs and arms.
exec(open(FW + r"\cloth_core.py").read())
LEGS = ["LeftUpperLeg", "LeftLowerLeg", "RightUpperLeg", "RightLowerLeg"]
ARMS = ["LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand"]
build_cloth([
    dict(name="Robe", kind="skirt", meshes=["Waist"], anchor="LowerTorso", top=1.8, keep_above=1.6, sectors=16, segments=5,
         replace=["LeftUpperLeg", "RightUpperLeg"], colliders=LEGS, stiff_top=0.45, stiff_tip=0.12,
         ring_stretch=1.4),                              # the front slit lets the panels part round a raised knee
    dict(name="Scarf", kind="strips", meshes=["Ribbons", "RibbonsGlow"], segments=4, join=0.05,
         colliders=["UpperTorso", "LowerTorso"] + LEGS + ARMS, radius={"LowerTorso": 0.26}, stiff_top=0.25, stiff_tip=0.03),
])
