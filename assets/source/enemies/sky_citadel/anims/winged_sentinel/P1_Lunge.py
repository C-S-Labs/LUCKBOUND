# P1_Lunge (WS_MOVESET P1 #1 "Dash Lunge"): 12 f tell, 6 f active, 24 f recovery. 44 f @ 30 fps.
# In place: the Studio AI moves the root (dash ~6 m along the lunge line between HitStart and HitEnd, overshoot 2 m).
# Built with param_keys: every 2nd frame is a fully SOLVED pose (natural one-hand hold via wield(), clear arms, grounded),
# so in-betweens never bend a joint the wrong way or pass a limb through the body.
#   f1 ready  f8 coil (sink back, lance drawn beside the hip, wings lift)  f12 tell peak (wings flare)
#   f15 thrust (lean in, arm driven out low, lance level)  f19 hit ends  f26 stumble-through (opening)  f44 ready
BASE = open(HERE + r"\ws_pose.py").read()
LO = globals().get("LANCE_OBJS", [])
FWD, UP = Vector((0, -1, 0)), Vector((0, 0, 1))
exec(BASE, G)                                                     # measure the ready stance once
_SH = world("RightUpperArm")
C0 = seat_point("Right") - _SH                                    # ready grip, relative to the shoulder
D0 = Vector((0.12, -1.0, -0.08)).normalized()                     # ready lance direction (ws_pose "want")
def pose(p):
    exec(BASE, G)
    if p["lean"]: rot_dir("UpperTorso", abs(p["lean"]), "Head", FWD if p["lean"] > 0 else -FWD)
    if p["head"]: rot_dir("Head", p["head"], "Head", FWD)
    if p["wup"]: rot_dir("WingL", abs(p["wup"]), "WingL_Tip", UP if p["wup"] > 0 else -UP); rot_dir("WingR", abs(p["wup"]), "WingR_Tip", UP if p["wup"] > 0 else -UP)
    if p["wback"]: rot_dir("WingL", p["wback"], "WingL_Tip", -FWD); rot_dir("WingR", p["wback"], "WingR_Tip", -FWD)
    if p["wflare"]: rot_dir("WingL", p["wflare"], "WingL_Tip", Vector((1, 0, 0.3))); rot_dir("WingR", p["wflare"], "WingR_Tip", Vector((-1, 0, 0.3)))
    if p["larm"]: rot_dir("LeftUpperArm", p["larm"], "LeftHand", -FWD); clear_arm("Left")
    wield(p["D"], world("RightUpperArm") + Vector(p["C"]))
    ground(LO)
def P_(C, D, lean=0.0, head=0.0, wup=0.0, wback=0.0, wflare=0.0, larm=0.0):
    return dict(C=Vector(C), D=Vector(D).normalized(), lean=lean, head=head, wup=wup, wback=wback, wflare=wflare, larm=larm)
READY  = P_(C0, D0)
COIL   = P_((-0.17, 0.14, -0.88), (0.05, -1, 0.12), lean=-0.12, wup=0.2)
TELL   = P_((-0.18, 0.16, -0.86), (0.05, -1, 0.14), lean=-0.14, wup=0.2, wflare=0.25)
THRUST = P_((0.02, -0.82, -0.62), (0.02, -1, 0.02), lean=0.3, wback=0.3, larm=0.5)
OVER   = P_((0.02, -0.86, -0.66), (0.02, -1, -0.02), lean=0.4, head=0.12, wback=0.3, larm=0.5)
STUMB  = P_((0.0, -0.6, -0.85), (0.0, -1, -0.4), lean=0.32, head=0.3, wup=-0.3, larm=0.2)
begin("P1_Lunge", 44)
param_keys([(1, READY), (8, COIL), (12, TELL), (15, THRUST), (19, OVER), (26, STUMB), (44, READY)], pose,
           step=2, arcs={"C": (-0.06, 0.0, 0.0)})                  # the hand swings slightly OUT around the hip
mark("Tell", 1); mark("VFX_WingFlare", 10); mark("HitStart", 13); mark("HitEnd", 19); mark("RecoverStart", 20)
end()
