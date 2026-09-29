# JOINTS core (framework): extra deformation joints for humanoid bodies, so limbs and the torso bend smoothly.
# Solvers and animations keep using the R15 bones; the helper bones below are DRIVEN from them every key, so they
# need no animation of their own:
#   Spine                - child of LowerTorso, turns half of UpperTorso's rotation: the chest bends through its middle
#                          instead of hinging at one line.
#   {side}LowerArmTwist  - child of LowerArm (from ~45% of its length), turns half of the hand's roll: the forearm
#                          twists smoothly into the wrist instead of pinching.
#   shoulder pads        - a share of the pad mesh's arm weight moves to UpperTorso, so a raised arm does not drag the
#                          pad with it.
# Usage from an extras script (after the body):  exec(open(FW + r"\joints_core.py").read());  add_joints()
import bpy
from mathutils import Vector, Quaternion

def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a)/(b - a))); return t*t*(3 - 2*t)

def _rewt(o, i, delta):
    """Add delta {group: change} to vertex i's weights, keep the strongest 4 (Roblox limit), normalise."""
    v = o.data.vertices[i]; idx = [g.group for g in v.groups]
    w = {o.vertex_groups[gi].name: g.weight for gi, g in zip(idx, v.groups)}
    for n, d in delta.items(): w[n] = max(0.0, w.get(n, 0.0) + d)
    top = sorted(((n, x) for n, x in w.items() if x > 1e-4), key=lambda kv: -kv[1])[:4]
    s = sum(x for _, x in top) or 1.0
    for gi in idx: o.vertex_groups[gi].remove([i])
    for n, x in top: (o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add([i], x/s, 'REPLACE')

def add_joints(sides=("Left", "Right"), fore_at=0.45, fore_blend=(0.15, 0.95), spine_z=(2.0, 2.5), pad_share=0.45,
               pad_mesh="Mantle"):
    pfx = globals().get("PREFIX") or NAME + "_"
    if "Spine" in rig.data.bones: return
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    ut, lt = eb["UpperTorso"], eb["LowerTorso"]
    s = eb.new("Spine"); s.head = ut.head.copy(); s.tail = ut.head.lerp(ut.tail, 0.5); s.roll = ut.roll; s.parent = lt
    for side in sides:
        la = eb[f"{side}LowerArm"]; t = eb.new(f"{side}LowerArmTwist")
        t.head = la.head.lerp(la.tail, fore_at); t.tail = la.tail.copy(); t.roll = la.roll; t.parent = la
    bpy.ops.object.mode_set(mode='OBJECT')
    Mi = rig.matrix_world.inverted(); B = rig.data.bones
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(pfx)]
    z0, z1 = spine_z; nsp = nfa = npad = 0
    for o in meshes:
        gname = {g.index: g.name for g in o.vertex_groups}
        has = set(gname.values())
        for v in o.data.vertices:
            w = {gname[g.group]: g.weight for g in v.groups}
            p = Mi @ (o.matrix_world @ v.co); delta = {}
            wu = w.get("UpperTorso", 0.0)
            if wu > 0.02 and p.z < z1:                                   # torso middle: LowerTorso -> Spine -> UpperTorso
                u = max(0.0, (p.z - z0)/(z1 - z0))
                if u < 0.5: to_lt, to_sp = wu*(1 - 2*u), wu*2*u
                else: to_lt, to_sp = 0.0, wu*(2 - 2*u)
                delta["UpperTorso"] = -(to_lt + to_sp); delta["LowerTorso"] = to_lt; delta["Spine"] = to_sp; nsp += 1
            for side in sides:
                wl = w.get(f"{side}LowerArm", 0.0)
                if wl > 0.02:                                            # forearm: LowerArm -> LowerArmTwist toward the wrist
                    b = B[f"{side}LowerArm"]; ax = b.tail_local - b.head_local
                    t = (p - b.head_local).dot(ax)/ax.length_squared
                    sh_ = _smooth(*fore_blend, t)
                    if sh_ > 0.01:
                        delta[f"{side}LowerArm"] = delta.get(f"{side}LowerArm", 0.0) - wl*sh_
                        delta[f"{side}LowerArmTwist"] = wl*sh_; nfa += 1
                if o.name == pfx + pad_mesh:
                    wa = w.get(f"{side}UpperArm", 0.0)
                    if wa > 0.02:
                        delta[f"{side}UpperArm"] = delta.get(f"{side}UpperArm", 0.0) - wa*pad_share
                        delta["UpperTorso"] = delta.get("UpperTorso", 0.0) + wa*pad_share; npad += 1
            if delta: _rewt(o, v.index, delta)
    print(f"JOINTS added Spine + {len(sides)} forearm twist bones; reskinned {nsp} torso / {nfa} forearm / {npad} pad verts")

def distribute_joints():
    """Runs after every pose (anim_core.key -> POST_POSE): drive the helper bones from the solved bones."""
    P = rig.pose.bones
    if "Spine" in P:
        q = P["UpperTorso"].matrix_basis.to_quaternion()
        P["Spine"].rotation_mode = 'QUATERNION'; P["Spine"].rotation_quaternion = Quaternion().slerp(q, 0.5)
    for side in ("Left", "Right"):
        n = f"{side}LowerArmTwist"
        if n in P:
            q = P[f"{side}Hand"].matrix_basis.to_quaternion(); tw = Quaternion((q.w, 0.0, q.y, 0.0))    # roll about the bone's Y
            tw = tw.normalized() if tw.magnitude > 1e-6 else Quaternion()
            P[n].rotation_mode = 'QUATERNION'; P[n].rotation_quaternion = Quaternion().slerp(tw, 0.5)

_hooks = globals().setdefault("POST_POSE", [])
if "distribute_joints" not in [f.__name__ for f in _hooks]: _hooks.append(distribute_joints)
