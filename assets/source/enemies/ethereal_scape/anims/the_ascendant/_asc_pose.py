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

def left_on_haft(u, lift=0.0):
    """Off hand on the haft at distance u from the right-hand grip (negative = toward the butt), palm coming from
       the body side and a little below, so the elbow stays down."""
    G0, GA = haft(); C = G0 + GA*u
    away = (Vector((0, 0.1, 1.95)) - C); away.z -= 0.25 + lift
    hand_on("Left", u, away)

def curl_left(amount):
    """Crystal fingers of the free left hand: 0 = open, 1 = loosely curled (idle breathing / casting)."""
    for fn in ("Index", "Middle", "Ring", "Pinky"):
        rot(f"Left{fn}1", x=-0.5*amount); rot(f"Left{fn}2", x=-0.7*amount)
    rot("LeftThumb1", x=-0.3*amount)

def staff(C, D, edge, two_hand=None):
    """Right hand holds the staff at world point C along world direction D (grip -> crescent), edge facing E;
       optional off hand on the haft at distance two_hand."""
    wield(Vector(D).normalized(), Vector(C))
    roll_edge(edge)
    if two_hand is not None: left_on_haft(two_hand)
