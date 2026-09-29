# Shared posing for every Ascendant action (exec'd at the top of each action file; run.py skips "_" files).
# Built on the framework solvers only: pose_fix.wield / hand_on / arm_to (natural staff hold, hinge elbows),
# walk_core.leg_to (hinge knees). Stance / grips are PARAMETERS, so param_keys re-solves every in-between frame.
import math
from mathutils import Matrix, Vector
exec(open(FW + r"\walk_core.py").read())
CLIP_PIECES = ("ArmLeft", "ArmRight", "Staff")          # limbs + the staff vs Torso/Waist/Legs, every scanned frame
GL = globals().get("STAFF_OBJS", [])
FWD, UP = Vector((0, -1, 0)), Vector((0, 0, 1))
_REST_ANKLE = {"Left": Vector((0.19, 0.02, 0.17)), "Right": Vector((-0.19, 0.02, 0.17))}

def _left_on_staff(tol=0.25):
    _upd(); G0, GA = haft()
    palm = RW @ ((P["LeftHand"].head + P["LeftHand"].tail)*0.5)
    return ((palm - G0) - GA*(palm - G0).dot(GA)).length < tol

def fix_clip(piece):
    """anim_core's one-frame clip correction, made grip-safe. The staff is always in the right hand, and the left
       hand is often on the haft too: swinging either arm clear on ONE frame tears the hand off the staff and back,
       which reads as the arm spazzing. Held arms are fixed in the key poses instead; a free left arm is still
       cleared as the humanoid profile does."""
    if piece != "ArmLeft" or _left_on_staff(): return
    clear_arm("Left", step=0.05, maxit=12)

def flat_foot(side):
    """Keep the crystal foot level on the floor whatever the shin does (rest orientation, current ankle)."""
    _upd(); pb = P[f"{side}Foot"]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ rig.data.bones[f"{side}Foot"].matrix_local.to_3x3().to_4x4(); _upd()

def ground_body():
    """ground() over the body only: the staff may dip low, but the FEET decide where the floor is."""
    _upd(); dg = bpy.context.evaluated_depsgraph_get(); minz = 1e9
    for o in PARTS:
        if o in GL or o.hide_render or "_Break" in o.name: continue
        oe = o.evaluated_get(dg); m = oe.to_mesh()
        if len(m.vertices): minz = min(minz, min((o.matrix_world @ v.co).z for v in m.vertices))
        oe.to_mesh_clear()
    r_ = P["HumanoidRootNode"]; r_.location = r_.location + Vector((0, -minz, 0)); _upd()

def roll_edge(E):
    """Spin the staff about its own haft so the crescent's cutting edge faces world E. Rotation only, about the grip
       on the haft axis, so the hands stay exactly where wield()/hand_on() put them."""
    _upd(); wb = P["Weapon_R"]
    Rn = wb.matrix.to_3x3() @ rig.data.bones["Weapon_R"].matrix_local.to_3x3().inverted()
    G0, GA = haft()
    cur = (RW.to_3x3() @ (Rn @ Vector((0, 0, 1))))          # the edge points world-up at rest
    cur = (cur - GA*cur.dot(GA)); want = Vector(E) - GA*Vector(E).dot(GA)
    if cur.length < 1e-4 or want.length < 1e-4: return
    ang = cur.normalized().angle(want.normalized())
    if GA.dot(cur.cross(want)) < 0: ang = -ang
    Ra = RW.to_3x3().inverted() @ Matrix.Rotation(ang, 3, GA) @ RW.to_3x3()
    h = wb.head.copy(); wb.matrix = Matrix.Translation(h) @ Ra.to_4x4() @ Matrix.Translation(-h) @ wb.matrix; _upd()

def stance(p):
    """Legs + torso. p: sink (m), fL / fR = (dx, dy, 0) foot offsets from the rest ankles, twist (+ = chest to its LEFT),
       lean (+ = forward), side_lean, head (+ = chin down), head_turn."""
    move_root(y_up=-p.get("sink", 0.0))
    tw = p.get("twist", 0.0)                                   # pelvis first: the legs hang off LowerTorso
    if tw: rot("LowerTorso", y=tw*0.35); rot("UpperTorso", y=tw*0.65)
    for side in ("Left", "Right"):
        off = Vector(p.get("f" + side[0], (0, 0, 0)))
        s = 1 if side == "Left" else -1
        leg_to(side, _REST_ANKLE[side] + Vector((off.x, off.y, 0)), (0.12*s, -1.0, 0.1))
        flat_foot(side)
    if p.get("lean"): rot_dir("UpperTorso", abs(p["lean"]), "Head", FWD if p["lean"] > 0 else -FWD)
    if p.get("side_lean"): rot_dir("UpperTorso", abs(p["side_lean"]), "Head", Vector((1, 0, 0)) if p["side_lean"] > 0 else Vector((-1, 0, 0)))
    if p.get("head"): rot_dir("Neck", abs(p["head"]), "Head", FWD if p["head"] > 0 else -FWD)
    if p.get("head_turn"): rot("Head", y=p["head_turn"])
    _upd()

AXE_GRIP = 1   # the off hand's wrap: overhand from the front, thumb on top (the approved guard render)
def left_on_haft(u, lift=0.0, grip=None):
    """Off hand on the haft at distance u from the right-hand grip (negative = toward the butt), held like the lower
       hand on an axe carried across the body (owner's reference): the hand comes onto the haft from OUTSIDE, so the
       back of the hand faces out, the palm faces the body and the fingers wrap round the haft toward the torso."""
    G0, GA = haft(); C = G0 + GA*u
    body = RW @ ((P["UpperTorso"].head + P["UpperTorso"].tail)*0.5)
    away = C - body; away = away - GA*away.dot(GA)             # from the body out through the grip point
    if lift: away = away + Vector((0, 0, -lift))
    hand_on("Left", u, away, grip=AXE_GRIP)

def curl_left(amount):
    """Crystal fingers of the free left hand: 0 = open, 1 = loosely curled (idle breathing / casting)."""
    for fn in ("Index", "Middle", "Ring", "Pinky"):
        rot(f"Left{fn}1", x=-0.5*amount); rot(f"Left{fn}2", x=-0.7*amount)
    rot("LeftThumb1", x=-0.3*amount)

def staff(C, D, edge, two_hand=None, grip=0.0, free=0.0):
    """Right hand holds the staff at world point C along world direction D (grip -> crescent), edge facing E;
       optional off hand on the haft at distance two_hand.
       grip: 0 = the per-pose wrap rule; > 0 / < 0 fixes the off hand's wrap (pose_fix.hand_on). A wrap change must
       never happen on the haft (it spins the hand ~160 deg in a frame): release the hand (free -> 1), change the
       wrap while it is off, then re-grip (free -> 0). free blends, per bone, from the grip to a relaxed free arm."""
    wield(Vector(D).normalized(), Vector(C))
    roll_edge(edge)
    if two_hand is None: return
    g = None if abs(grip) < 1e-6 else (1 if grip > 0 else -1)
    if free < 1e-3: left_on_haft(two_hand, grip=g); return
    chain = ["LeftUpperArm"] + [c.name for c in P["LeftUpperArm"].children_recursive]
    _swing_arm("Left", fwd=0.35, out=0.15, elbow=0.9)      # free hand hovers in front of the belt, near the haft
    off = {n: P[n].matrix_basis.copy() for n in chain}
    if free > 0.999: return
    for n in chain: P[n].matrix_basis = Matrix.Identity(4)
    _upd(); left_on_haft(two_hand, grip=g)
    on = {n: P[n].matrix_basis.copy() for n in chain}
    for n in chain:
        q = on[n].to_quaternion().slerp(off[n].to_quaternion(), free)
        P[n].matrix_basis = Matrix.Translation(on[n].to_translation().lerp(off[n].to_translation(), free)) @ q.to_matrix().to_4x4()
    _upd()
