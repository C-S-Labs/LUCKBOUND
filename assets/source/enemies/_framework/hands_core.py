# HANDS core (framework): three-joint fingers, so a hand can close all the way round a weapon's haft.
#
# pose_fix.wrap() curls every finger joint around the haft axis until it touches (never through it). Two bones per
# finger can only hook onto a haft; three can wrap it. A body built with two-bone fingers (and a mesh that has no
# vertices part-way along the last segment, like faceted crystal fingers) opts in from an extras script:
#   exec(open(FW + r"\hands_core.py").read())
#   add_phalanges()          # every finger + thumb, both hands
# It splits each {side}{finger}2 bone at `split` into {finger}2 + {finger}3, cuts a ring of vertices into that
# segment's mesh at the new joint (a few tris per finger), and re-weights the mesh either side of it.
# humanoid.make_humanoid(fingers=True) already builds three-joint fingers; this is for custom hands.
import bpy, bmesh
from mathutils import Vector

FINGERS = ("Index", "Middle", "Ring", "Pinky", "Thumb")

def add_phalanges(sides=("Left", "Right"), fingers=FINGERS, split=0.5, blend=0.12):
    pfx = globals().get("PREFIX") or NAME + "_"
    todo = []
    for side in sides:
        for fn in fingers:
            b2, b3 = f"{side}{fn}2", f"{side}{fn}3"
            if b2 in rig.data.bones and b3 not in rig.data.bones:
                b = rig.data.bones[b2]; todo.append((b2, b3, b.head_local.copy(), b.tail_local.copy()))
    if not todo: return
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    for b2, b3, H, T in todo:
        M = H.lerp(T, split); e2 = eb[b2]; roll = e2.roll
        kids = [c for c in e2.children]
        e2.tail = M
        e3 = eb.new(b3); e3.head = M; e3.tail = T; e3.roll = roll; e3.parent = e2; e3.use_connect = True
        e3.use_deform = True
        for c in kids: c.parent = e3                       # fingertip sockets (if any) ride the new tip bone
    bpy.ops.object.mode_set(mode='OBJECT')
    Mw = rig.matrix_world; cuts = 0
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(pfx)]:
        groups = {g.name: g.index for g in o.vertex_groups}
        mine = [t for t in todo if t[0] in groups]
        if not mine: continue
        bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.verify()
        Mo = o.matrix_world.inverted() @ Mw                    # rig space -> this mesh's local space
        for b2, b3, H, T in mine:
            gi = groups[b2]
            g3 = o.vertex_groups.get(b3) or o.vertex_groups.new(name=b3); groups[b3] = g3.index
            Hl, Tl = Mo @ H, Mo @ T; d = (Tl - Hl); L = d.length; d.normalize(); Ml = Hl.lerp(Tl, split)
            owned = lambda v: v[dl].get(gi, 0.0) > 0.5
            faces = [f for f in bm.faces if all(owned(v) for v in f.verts)]
            if faces:
                geom = list({x for f in faces for x in (list(f.verts) + list(f.edges))}) + faces
                bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Ml, plane_no=d, dist=1e-5)
                cuts += 1
            for v in bm.verts:
                w = v[dl].get(gi, 0.0)
                if w <= 0.0: continue
                t = (v.co - Hl).dot(d)/L
                x = min(1.0, max(0.0, (t - (split - blend))/(2*blend)))     # 0 below the joint, 1 above it
                if x > 0.0:
                    v[dl][gi] = w*(1 - x)
                    v[dl][g3.index] = w*x
                    if v[dl][gi] <= 1e-6: del v[dl][gi]
        bm.to_mesh(o.data); bm.free(); o.data.update()
    print(f"HANDS {len(todo)} fingers now have 3 joints ({cuts} mesh cuts)")
