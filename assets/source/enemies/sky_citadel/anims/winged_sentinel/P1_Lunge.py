# P1_Lunge (WS_MOVESET P1 #1 "Dash Lunge"): 12 f tell, 6 f active, 24 f recovery. 44 f @ 30 fps.
# In place: the Studio AI moves the root (dash ~6 m along the lunge line between HitStart and HitEnd, overshoot 2 m).
#   f1  ready stance            f8  coil (sinks, lance drawn back high, wings lift)   f12 tell peak (wings flared)
#   f15 full thrust (arm + torso extended forward, lance level, wings swept back)     f19 hit ends, overextended
#   f26 stumble-through (head down, wings droop = visible opening)                     f44 back to ready stance
BASE = open(HERE + r"\ws_pose.py").read()
LO = globals().get("LANCE_OBJS", [])
FWD, UP = Vector((0, -1, 0)), Vector((0, 0, 1))
def stance():
    exec(BASE, G)
def coil():
    stance()
    rot_dir("UpperTorso", 0.12, "Head", -FWD)                     # rock back
    sh = world("RightUpperArm")
    reach("Right", sh + Vector((-0.32, 0.28, -0.3)))             # draw the lance back beside the hip
    aim_weapon((0.05, -1, 0.08))
    rot_dir("WingL", 0.2, "WingL_Tip", UP); rot_dir("WingR", 0.2, "WingR_Tip", UP)
    ground(LO)
def tell():
    coil()
    rot_dir("WingL", 0.25, "WingL_Tip", Vector((1, 0, 0.3))); rot_dir("WingR", 0.25, "WingR_Tip", Vector((-1, 0, 0.3)))
    ground(LO)
def thrust():
    stance()
    rot_dir("UpperTorso", 0.3, "Head", FWD)                        # lean into it
    sh = world("RightUpperArm")
    reach("Right", sh + Vector((0.05, -0.62, -0.18)))             # arm driven straight out in front
    aim_weapon((0.02, -1, 0.0))
    rot_dir("LeftUpperArm", 0.5, "LeftHand", -FWD)                # off arm swings back for balance
    clear_arm("Left")
    rot_dir("WingL", 0.3, "WingL_Tip", -FWD); rot_dir("WingR", 0.3, "WingR_Tip", -FWD)
    ground(LO)
def overextend():
    thrust()
    rot_dir("UpperTorso", 0.1, "Head", FWD); rot_dir("Head", 0.12, "Head", FWD)
    ground(LO)
def stumble():
    stance()
    rot_dir("UpperTorso", 0.32, "Head", FWD); rot_dir("Head", 0.3, "Head", FWD)
    sh = world("RightUpperArm")
    reach("Right", sh + Vector((0.0, -0.4, -0.5)))                # lance tip sagging toward the floor
    aim_weapon((0.0, -1, -0.35))
    rot_dir("WingL", 0.3, "WingL_Tip", -UP); rot_dir("WingR", 0.3, "WingR_Tip", -UP)
    ground(LO)
begin("P1_Lunge", 44)
key(1, stance); key(8, coil); key(12, tell); key(15, thrust); key(19, overextend); key(26, stumble); key(44, stance)
mark("Tell", 1); mark("VFX_WingFlare", 10); mark("HitStart", 13); mark("HitEnd", 19); mark("RecoverStart", 20)
end()
