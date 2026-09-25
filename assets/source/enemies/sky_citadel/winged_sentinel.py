# LUCKBOUND - Sky Citadel BOSS 3: The Winged Sentinel (FAST duelist; wing-assisted dash-lunges). 2 phases:
#   P1 armoured.  P2: the "Breakaway" piece (breastplate, plackart, spaulders, kite guard, tassets, faulds) is shed,
#   exposing a glowing inner aether core + veins, and the wings extend fully.
# ~3.55 m / ~2.5x a Roblox player. Smooth gloss materials; palette via GS_PALETTE=gilded|stone (citadel colours).
# Split into export pieces (each < 10k tris) that share one R15-named rig. Rigid per-part skinning;
# front/back faulds on 2-bone chains. Weapons NOT modelled - Weapon_R / Shield_L are sockets.
# Build prints a CLIP report (BVH surface intersections between parts; Under/joint sockets excluded).
# Earlier versions: gilded_sentinel_v1.py (boxy), _v2.py (verdigris/samurai), _v3.py (raptor helm, tabards).
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector

NAME = "WingedSentinel"

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

def patina_mat():
    m = mat("GS_Patina", (0.08, 0.17, 0.15), 0.2, 0.6)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 14.0; nz.inputs["Detail"].default_value = 8.0
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.055, 0.12, 0.105, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (0.11, 0.21, 0.18, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    return m

import os
PALETTE = os.environ.get("GS_PALETTE", "gilded")
# Palettes tie the Sentinel to the citadel: its gold trim, pale stone, violet spire caps and cyan aether.
#   gilded : gold plate, citadel-stone inlays, violet-slate trim, cyan aether   (default)
#   stone  : citadel-stone plate, gold trim, slate undersuit, cyan aether
PAL = {
    "gilded": dict(plate=((0.10, 0.105, 0.115), 0.7, 0.26), trim=((0.26, 0.17, 0.42), 0.5, 0.22),
                   under=((0.014, 0.014, 0.018), 0.3, 0.55), inlay=((0.80, 0.78, 0.73), 0.0, 0.22)),
    "stone":  dict(plate=((0.70, 0.68, 0.64), 0.0, 0.2), trim=((0.78, 0.55, 0.20), 1.0, 0.22),
                   under=((0.06, 0.07, 0.10), 0.6, 0.25), inlay=((0.16, 0.11, 0.26), 0.3, 0.25)),
}[PALETTE]
MATS = [
    mat("GS_Plate", *PAL["plate"]),     # main armour plate
    mat("GS_Trim",  *PAL["trim"]),      # edge trim / horns / feather accents
    mat("GS_Under", *PAL["under"]),     # undersuit / joints
    mat("GS_Inlay", *PAL["inlay"]),     # inlays / covert feathers
    mat("GS_Sinew", (0.055, 0.045, 0.085), 0.35, 0.3),   # v5: violet-black sinew of the under-body (phase 2)
    mat("GS_Glow",  (0.35, 0.9, 1.0), 0.0, 0.3, (0.3, 0.85, 1.0), 4.0),   # cyan aether (matches the citadel)
]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)

BONES = [
    ("HumanoidRootNode", (0, 0, 1.62), (0, 0, 1.80), None),
    ("LowerTorso", (0, 0, 1.72), (0, 0, 2.02), "HumanoidRootNode"),
    ("UpperTorso", (0, 0, 2.02), (0, 0, 2.92), "LowerTorso"),
    ("Neck", (0, 0, 2.88), (0, 0, 2.99), "UpperTorso"),        # extra joint: head turns/tilts pivot lower, reads smoother
    ("Head", (0, 0, 2.99), (0, 0, 3.60), "Neck"),
    ("FauldFront1", (0, -0.2, 1.84), (0, -0.2, 1.5), "LowerTorso"),
    ("FauldFront2", (0, -0.2, 1.5), (0, -0.22, 1.04), "FauldFront1"),
    ("FauldBack1", (0, 0.19, 1.84), (0, 0.19, 1.5), "LowerTorso"),
    ("FauldBack2", (0, 0.19, 1.5), (0, 0.21, 1.04), "FauldBack1"),
    ("VFX_Core", (0, -0.22, 2.52), (0, -0.4, 2.52), "UpperTorso"),
    ("VFX_Eye", (0, -0.2, 3.25), (0, -0.36, 3.25), "Head"),
]
for side, s in (("Left", 1), ("Right", -1)):
    BONES += [
        (f"{side}UpperArm", (0.5*s, 0.02, 2.76), (0.54*s, 0.02, 2.14), "UpperTorso"),
        (f"{side}LowerArm", (0.54*s, 0.02, 2.14), (0.57*s, 0.0, 1.58), f"{side}UpperArm"),
        (f"{side}Hand", (0.57*s, 0.0, 1.58), (0.57*s, -0.02, 1.36), f"{side}LowerArm"),
        (f"{side}UpperLeg", (0.18*s, 0, 1.76), (0.19*s, 0, 1.02), "LowerTorso"),
        (f"{side}LowerLeg", (0.19*s, 0, 1.02), (0.2*s, 0.04, 0.2), f"{side}UpperLeg"),
        (f"{side}Foot", (0.2*s, 0.04, 0.2), (0.2*s, -0.36, 0.04), f"{side}LowerLeg"),
        (f"Wing{side[0]}", (0.17*s, 0.3, 2.64), (0.3*s, 0.42, 2.9), "UpperTorso"),
        (f"Wing{side[0]}_Tip", (0.3*s, 0.42, 2.9), (0.36*s, 0.47, 3.02), f"Wing{side[0]}"),
    ]
BONES += [("Weapon_R", (-0.459, -0.015, 1.415), (-0.459, -0.275, 1.415), "RightHand"),
          ("Shield_L", (0.66, 0.0, 1.86), (0.8, 0.0, 1.86), "LeftLowerArm")]
BIDX = {b[0]: i for i, b in enumerate(BONES)}

def add_bone(name, head, tail, parent):
    BONES.append((name, tuple(head), tuple(tail), parent))
    BIDX[name] = len(BONES) - 1

PIECES = {}
PARTLOG = []   # (piece, label, material index, verts, tris) - for the clipping check
PIECE = "Torso"
BREAK = False   # True -> part goes to the phase-2 "Breakaway" piece
XF = None   # optional regional scale (head / hands / feet)

def scale_about(c, f):
    f = f if isinstance(f, (tuple, list)) else (f, f, f)
    S = Matrix.Diagonal((*f, 1.0))
    return Matrix.Translation(c) @ S @ Matrix.Translation(-Vector(c))


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
    PARTLOG.append((PIECE, f"L{f.f_lineno if f else 0}:{MATS[mi].name}", mi,
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

exec(open(HERE + r"\ws5_geometry.py").read())

# =====================================================================================
# clipping check: surface intersections between separately-built parts.
# Joints/undersuit (Under) are sockets meant to sit inside plates, so pairs involving them are skipped.
# =====================================================================================
from mathutils.bvhtree import BVHTree as _BVH
import os as _os
_trees = [(_BVH.FromPolygons(v, t), lab, mi) for (_, lab, mi, v, t) in PARTLOG] if _os.environ.get("CLIPCHECK") else []
CLIPS = []
for i in range(len(_trees)):
    ti, li, mi_ = _trees[i]
    if mi_ == IRON:
        continue
    for j in range(i + 1, len(_trees)):
        tj, lj, mj = _trees[j]
        if mj == IRON or li.split(":")[0] == lj.split(":")[0]:
            continue
        n = len(ti.overlap(tj))
        if n:
            CLIPS.append((n, li, lj))
CLIPS.sort(reverse=True)
print("CLIP pairs:", len(CLIPS))
for c in CLIPS[:60]:
    print("CLIP", c)

# =====================================================================================
# assemble: one object per piece, all on one rig
# =====================================================================================
arm_data = bpy.data.armatures.new(NAME + "_Rig")
rig = bpy.data.objects.new(NAME + "_Rig", arm_data)
coll = bpy.context.scene.collection
coll.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for n, h, t, p in BONES:
    b = arm_data.edit_bones.new(n)
    b.head, b.tail = h, t
    if p:
        b.parent = eb[p]
    eb[n] = b
bpy.ops.object.mode_set(mode='OBJECT')
arm_data.display_type = 'STICK'
PARTS = []
total = 0
# split every cyan glow face into its own mesh so Studio can pulse it (Neon + tweened colour).
# Breakaway glow stays separate so it disappears with the armour in phase 2.
def _split_glow(bm):
    g = bm.copy()
    bmesh.ops.delete(g, geom=[f for f in g.faces if f.material_index != GLOW], context='FACES')
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == GLOW], context='FACES')
    return g
_glow = {}
for pname in list(PIECES):
    gname = "BreakawayGlow" if pname == "Breakaway" else "Glow"
    g = _split_glow(PIECES[pname])
    if gname in _glow:
        me_ = bpy.data.meshes.new("tmpglow"); g.to_mesh(me_); g.free(); _glow[gname].from_mesh(me_); bpy.data.meshes.remove(me_)
    else:
        _glow[gname] = g
PIECES.update(_glow)
# phase-2 debris: split the Breakaway armour into named chunks (by the bone each face is weighted to)
# so Studio can fling each one as physics debris when the armour bursts off.
CHUNK_OF = {"UpperTorso": "Breastplate", "VFX_Core": "Breastplate", "LowerTorso": "Belt",
            "LeftUpperArm": "PauldronL", "RightUpperArm": "PauldronR", "LeftLowerArm": "BracerL", "RightLowerArm": "BracerR",
            "LeftUpperLeg": "TassetL", "RightUpperLeg": "TassetR", "LeftLowerLeg": "GreaveL", "RightLowerLeg": "GreaveR",
            "LeftFoot": "SabatonL", "RightFoot": "SabatonR",
            "FauldFront1": "FauldFront", "FauldFront2": "FauldFront", "FauldBack1": "FauldBack", "FauldBack2": "FauldBack"}
_bk = PIECES.pop("Breakaway")
_dl = _bk.verts.layers.deform.verify()
_bname = {i: b[0] for i, b in enumerate(BONES)}
def _chunk(f, dl):
    w = f.verts[0][dl]
    gi = max(w.items(), key=lambda kv: kv[1])[0] if len(w) else None
    return CHUNK_OF.get(_bname.get(gi), "Breastplate")
for cname in sorted(set(CHUNK_OF.values())):
    c = _bk.copy()
    cdl = c.verts.layers.deform.verify()
    bmesh.ops.delete(c, geom=[f for f in c.faces if _chunk(f, cdl) != cname], context='FACES')
    bmesh.ops.delete(c, geom=[v for v in c.verts if not v.link_faces], context='VERTS')
    if len(c.faces):
        PIECES["Break_" + cname] = c
    else:
        c.free()
_bk.free()
for pname, bm in PIECES.items():
    me = bpy.data.meshes.new(f"{NAME}_{pname}")
    bm.to_mesh(me); bm.free()
    for m in MATS:
        me.materials.append(m)
    o = bpy.data.objects.new(f"{NAME}_{pname}", me)
    for b in BONES:
        o.vertex_groups.new(name=b[0])
    coll.objects.link(o)
    o.parent = rig
    md = o.modifiers.new("Armature", 'ARMATURE'); md.object = rig
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    total += tris
    PARTS.append(o)
    print(f"PIECE {pname}: {tris} tris")
print("TRIS total", total)
obj = PARTS[0]
def wings_open(amount=1.0):
    """Phase 2: throw each wing out to the side (hub swings outward + back) and fan its blades wide, from near-vertical
    down past horizontal, so the wing spreads dramatically beside him."""
    P_ = rig.pose.bones
    for side, s_ in (("L", 1), ("R", -1)):
        bpy.context.view_layer.update()
        hub = P_["Wing" + side]; h = hub.head.copy()
        hub.matrix = Matrix.Translation(h) @ Matrix.Rotation(0.55*amount*s_, 4, Vector((0, 1, 0))) @ Matrix.Rotation(-0.2*amount, 4, Vector((1, 0, 0))) @ Matrix.Translation(-h) @ hub.matrix
        for i, (bn, root) in enumerate(WBL[side]):
            bpy.context.view_layer.update()
            pb = P_[bn]; h = pb.head.copy()
            t = i/6
            ang = (0.05 + 1.25*t)*amount*s_
            pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector((0, 1, 0.15)).normalized()) @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()

# ---------- presentation scene ----------
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1200, 1500
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.50, 0.56, 0.66, 1); bg.inputs[1].default_value = 0.35
def _look(o, tgt=(0, 0, 1.8)):
    o.rotation_euler = (Vector(tgt) - o.location).to_track_quat('-Z', 'Y').to_euler()
for n, loc, e, size, col in (("Key", (-4, -5, 5.5), 900, 4, (1, .93, .85)), ("Rim", (4, 4, 5), 900, 3, (.65, .8, 1)),
                             ("Fill", (5, -4, 2), 200, 4, (1, 1, 1))):
    d = bpy.data.lights.new(n, 'AREA'); d.energy = e; d.size = size; d.color = col
    o = bpy.data.objects.new(n, d); coll.objects.link(o); o.location = loc; _look(o)
pm = bpy.data.meshes.new("Pedestal"); pb = bmesh.new()
bmesh.ops.create_cone(pb, cap_ends=True, segments=64, radius1=2.2, radius2=2.2, depth=0.1); pb.to_mesh(pm); pb.free()
pm.materials.append(mat("Ped", (0.45, 0.46, 0.5), 0, 0.8))
p = bpy.data.objects.new("Pedestal", pm); coll.objects.link(p); p.location = (0, 0, -0.05)
# Roblox player scale reference block (~5 studs at 1 stud = 0.28 m)
ref = bpy.data.meshes.new("PlayerRef"); rb = bmesh.new()
bmesh.ops.create_cube(rb, size=1.0); bmesh.ops.scale(rb, vec=(0.5, 0.28, 1.4), verts=rb.verts)
bmesh.ops.translate(rb, vec=(0, 0, 0.7), verts=rb.verts); rb.to_mesh(ref); rb.free()
ref.materials.append(mat("Ref", (0.9, 0.35, 0.3), 0, 0.7))
r = bpy.data.objects.new("PlayerRef", ref); coll.objects.link(r); r.location = (1.45, -0.7, 0)
cd = bpy.data.cameras.new("Cam"); cd.lens = 55
cam = bpy.data.objects.new("Cam", cd); coll.objects.link(cam); sc.camera = cam
cam.location = (-4.4, -7.6, 2.9); _look(cam)
