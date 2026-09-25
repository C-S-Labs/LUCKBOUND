# Shared LUCKBOUND enemy-building kit (lofts, plates, blades, gems, cloth, skinning into PIECES).
# The calling script defines: MATS, BONES, BIDX, PIECES, PIECE, PARTLOG, BREAK, XF and material indices
# (PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW) before exec-ing this file. Extracted from winged_sentinel.py.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

def mat(name, col, metal=0.0, rough=0.6, emit=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def scale_about(c, f):
    f = f if isinstance(f, (tuple, list)) else (f, f, f)
    S = Matrix.Diagonal((*f, 1.0))
    return Matrix.Translation(c) @ S @ Matrix.Translation(-Vector(c))

def add_bone(name, head, tail, parent):
    BONES.append((name, tuple(head), tuple(tail), parent))
    BIDX[name] = len(BONES) - 1

def _mesh_of(tb, mods=()):
    me = bpy.data.meshes.new("tmp")
    tb.to_mesh(me); tb.free()
    if mods:
        o = bpy.data.objects.new("tmp", me)
        bpy.context.scene.collection.objects.link(o)
        for kind, kw in mods:
            m = o.modifiers.new(kind, kind)
            for k, v in kw.items():
                setattr(m, k, v)
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
        me = me2
    return me

def _add(tb, bone, mi, M=Matrix(), smooth=True, sub=0, mods=(), wfn=None):
    bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
    for f in tb.faces:
        if mi is not None:
            f.material_index = mi
        f.smooth = smooth
    mods = list(mods)
    if sub:
        mods.append(("SUBSURF", {"levels": sub, "render_levels": sub}))
    me = _mesh_of(tb, mods)
    me.transform(M)
    if XF is not None:
        me.transform(XF)
    import sys as _sys
    f = _sys._getframe(1)
    while f and f.f_code.co_name in ("loft", "arc_band", "tube", "blade", "box", "sph", "gem", "cloth", "fauld", "_add"):
        f = f.f_back
    me.calc_loop_triangles()
    PARTLOG.append((PIECE, f"L{f.f_lineno if f else 0}:{MATS[mi].name if mi is not None else 'mixed'}", mi,
                    [v.co.copy() for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles]))
    bm = PIECES.setdefault("Breakaway" if BREAK else PIECE, bmesh.new())
    dl = bm.verts.layers.deform.verify()
    n0 = len(bm.verts)
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bm.verts.ensure_lookup_table()
    for v in bm.verts[n0:]:
        if wfn:
            for bn, w in wfn(v.co).items():
                v[dl][BIDX[bn]] = w
        else:
            v[dl][BIDX[bone]] = 1.0

def TR(loc=(0, 0, 0), rot=(0, 0, 0)):
    return Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()

def _ring(tb, z, rx, ry, n=2.0, ox=0.0, oy=0.0, N=16):
    out = []
    for i in range(N):
        a = 2*math.pi*i/N
        c, s = math.cos(a), math.sin(a)
        x = rx*math.copysign(abs(c)**(2/n), c)
        y = ry*math.copysign(abs(s)**(2/n), s)
        out.append(tb.verts.new((x + ox, y + oy, z)))
    return out

def loft(bone, mi, secs, N=16, M=Matrix(), sub=0, cap=True, smooth=True, wfn=None, warp=None, keep=None, fill=False):
    """secs: (z, rx, ry[, n, ox, oy]) along local Z."""
    tb = bmesh.new()
    rings = []
    for sct in secs:
        z, rx, ry = sct[:3]
        n = sct[3] if len(sct) > 3 else 2.0
        ox = sct[4] if len(sct) > 4 else 0.0
        oy = sct[5] if len(sct) > 5 else 0.0
        rings.append(_ring(tb, z, max(rx, 1e-3), max(ry, 1e-3), n, ox, oy, N))
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(N):
            tb.faces.new((r0[i], r0[(i+1) % N], r1[(i+1) % N], r1[i]))
    if cap:
        tb.faces.new(rings[0]); tb.faces.new(rings[-1])
    if keep:
        bmesh.ops.delete(tb, geom=[f for f in tb.faces if not keep(f.calc_center_median())], context='FACES')
        bmesh.ops.delete(tb, geom=[v for v in tb.verts if not v.link_faces], context='VERTS')
        if fill:
            _e = [e for e in tb.edges if e.is_boundary]
            if _e:
                bmesh.ops.holes_fill(tb, edges=_e)
    if warp:
        for v in tb.verts:
            warp(v.co)
    _add(tb, bone, mi, M, smooth, sub, wfn=wfn)

def arc_band(bone, mi, c, z0, z1, r0, r1, a0, a1, thick=0.02, segs=12, sub=0):
    """Curved plate: elliptical arc a0..a1 (0=+X, -pi/2=front) sweeping z0->z1, radii r0->r1 (rx,ry)."""
    tb = bmesh.new()
    def pt(a, z, r, off):
        return tb.verts.new((c[0] + (r[0] + off)*math.cos(a), c[1] + (r[1] + off)*math.sin(a), z))
    grid = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0)*i/segs
        grid.append([pt(a, z0, r0, 0), pt(a, z1, r1, 0), pt(a, z1, r1, -thick), pt(a, z0, r0, -thick)])
    for g0, g1 in zip(grid, grid[1:]):
        for k in range(4):
            tb.faces.new((g0[k], g1[k], g1[(k+1) % 4], g0[(k+1) % 4]))
    tb.faces.new(grid[0]); tb.faces.new(list(reversed(grid[-1])))
    _add(tb, bone, mi, Matrix(), smooth=True, sub=sub)

def _frame(p0, d, hint=(0, 1, 0)):
    z = Vector(d).normalized()
    x = Vector(hint).cross(z)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(p0)
    return M

def tube(bone, mi, p0, p1, r0, r1, N=10, sub=0):
    d = Vector(p1) - Vector(p0)
    loft(bone, mi, [(0, r0, r0), (d.length, r1, r1)], N=N, M=_frame(p0, d), sub=sub)

def blade(bone, mi, p0, d, length, width, thick=0.02, hint=(0, 1, 0), N=8, sub=1):
    """Feather / fin blade: lens section, flat across local X."""
    loft(bone, mi, [(0, width*0.45, thick), (length*0.25, width, thick), (length*0.7, width*0.8, thick*0.8),
                    (length*0.93, width*0.35, thick*0.6), (length, 0.004, 0.003)],
         N=N, M=_frame(p0, d, hint), sub=sub)

def box(bone, mi, loc, size, rot=(0, 0, 0), top=(1, 1), bev=0.02, segs=2, M=None):
    tb = bmesh.new()
    bmesh.ops.create_cube(tb, size=1.0)
    for v in tb.verts:
        t = v.co.z + 0.5
        v.co.x *= size[0]*(1 + (top[0]-1)*t)
        v.co.y *= size[1]*(1 + (top[1]-1)*t)
        v.co.z *= size[2]
    if bev > 0:
        bmesh.ops.bevel(tb, geom=list(tb.edges), offset=bev, offset_type='OFFSET', segments=segs,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    _add(tb, bone, mi, M if M is not None else TR(loc, rot), smooth=False)

def sph(bone, mi, loc, r, scale=(1, 1, 1), u=16, v=10, rot=(0, 0, 0), cut_below=None):
    tb = bmesh.new()
    bmesh.ops.create_uvsphere(tb, u_segments=u, v_segments=v, radius=r)
    if cut_below is not None:
        bmesh.ops.delete(tb, geom=[x for x in tb.verts if x.co.z < cut_below*r - 1e-4], context='VERTS')
        e = [e for e in tb.edges if e.is_boundary]
        if e:
            bmesh.ops.holes_fill(tb, edges=e)
    bmesh.ops.scale(tb, vec=scale, verts=tb.verts)
    _add(tb, bone, mi, TR(loc, rot))

def gem(bone, mi, loc, r, h, rot=(0, 0, 0), sides=8):
    tb = bmesh.new()
    top = tb.verts.new((0, 0, h)); bot = tb.verts.new((0, 0, -h*0.4))
    ring = [tb.verts.new((r*math.cos(a), r*math.sin(a), 0)) for a in [i*2*math.pi/sides for i in range(sides)]]
    for i in range(sides):
        a, b = ring[i], ring[(i+1) % sides]
        tb.faces.new((a, b, top)); tb.faces.new((b, a, bot))
    _add(tb, bone, mi, TR(loc, rot), smooth=False)

def cloth(b1, b2, zsplit, mi, y, z0, z1, w0, w1, bow=0.05, teeth=5, depth=0.12, face=-1, cols=10, rows=10):
    """Tattered hanging panel with zig-zag hem, 2-bone blended weights."""
    tb = bmesh.new()
    grid = []
    for r in range(rows + 1):
        t = r/rows
        z = z0 + (z1 - z0)*t
        w = w0 + (w1 - w0)*t
        row = []
        for c in range(cols + 1):
            u = c/cols - 0.5
            zz = z
            if r == rows:
                ph = (c/cols)*teeth
                zz = z - depth*(1 - abs((ph % 1)*2 - 1)) - 0.03*math.sin(c*1.7)
            yy = y + face*bow*(1 - (2*u)**2) + face*0.05*t
            row.append(tb.verts.new((u*w, yy, zz)))
        grid.append(row)
    for r in range(rows):
        for c in range(cols):
            tb.faces.new((grid[r][c], grid[r][c+1], grid[r+1][c+1], grid[r+1][c]))
    def wfn(co):
        t = min(1, max(0, (zsplit + 0.15 - co.z)/0.3))
        return {b1: 1 - t, b2: t} if t > 0 else {b1: 1.0}
    _add(tb, b1, mi, Matrix(), True, 0, mods=[("SOLIDIFY", {"thickness": 0.025, "offset": 0})], wfn=wfn)


# ---------------------------------------------------------------------------------------------
# assemble(): build the rig from BONES, split PIECES into body + glow meshes (glow = material GLOW), skin all to the
# rig, place at OFFSET. Returns (rig, PARTS). Any mesh over 10k tris is flagged so it can be split.
# ---------------------------------------------------------------------------------------------
def assemble(NAME, OFFSET=(0, 0, 0), glow_ids=None, glow_split=True):
    glow_ids = set(glow_ids if glow_ids is not None else [GLOW])
    arm_data = bpy.data.armatures.new(NAME + "_Rig")
    rig = bpy.data.objects.new(NAME + "_Rig", arm_data)
    coll = bpy.context.scene.collection
    coll.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for n, h, t, p in BONES:
        b = arm_data.edit_bones.new(n); b.head, b.tail = h, t
        if p: b.parent = eb[p]
        eb[n] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    arm_data.display_type = 'STICK'
    parts = []
    out = {}
    for pn, bm in list(PIECES.items()):
        if glow_split:
            g = bm.copy()
            bmesh.ops.delete(g, geom=[f for f in g.faces if f.material_index not in glow_ids], context='FACES')
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in glow_ids], context='FACES')
            out[pn] = bm
            if len(g.faces):
                out[pn + "Glow"] = g
            else:
                g.free()
        else:
            out[pn] = bm
    for pn, bm in out.items():
        if not len(bm.faces):
            bm.free(); continue
        nm = f"{NAME}_{pn}"
        me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
        for m in MATS: me.materials.append(m)
        o = bpy.data.objects.new(nm, me)
        for b in BONES: o.vertex_groups.new(name=b[0])
        coll.objects.link(o); o.parent = rig
        o.modifiers.new("Armature", 'ARMATURE').object = rig
        parts.append(o)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        print(f"PIECE {nm}: {tris} tris" + ("   <-- OVER 10k, SPLIT" if tris > 10000 else ""))
    rig.location = OFFSET
    return rig, parts
