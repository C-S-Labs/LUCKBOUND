# LUCKBOUND - The Ascendant's unique weapon: the Sanctum Staff. Run AFTER the_ascendant.py (manifest "extras"):
# reuses its materials, helpers and rig. Built along the Weapon_R socket (grip in the right palm), skinned 100% to
# Weapon_R as its own piece "Staff" (< 10k tris), so it follows every action.
# Motif: the Sanctum's key turned weapon. A long gold-and-ivory haft with teal grip wraps; at the head a gold socket
# holding a CRESCENT of raw sky crystal (cutting edge on the outside curve, a portal-glow fuller along it) and a
# smaller back-horn, so the silhouette reads as a waxing moon, never a lance. The butt is a crystal counterweight.
# VFX sockets: VFX_StaffBase / VFX_StaffTip (weapon trail during HitStart..HitEnd).
# WEAPON TYPE: **Staff** (docs/WEAPONS.md §1: two hands, a focus at the head), so it can drop for players as the
# Ascendant's Legendary staff. Its parts already follow the Staff bone vocabulary (§4): Shaft = haft + butt,
# Head = gold socket + crescent + back-horn, Core = the portal eye. On the boss everything is skinned to Weapon_R;
# the player-drop export (Root/Shaft/Head/Core/Fx_Cast, wpn_es_staff_legendary_a) is a follow-up, see ROSTER.md.
import bpy, bmesh, math
from mathutils import Matrix, Vector
V = Vector
PIECES = {}; PARTLOG.clear(); PIECE = "Staff"; BREAK = False; XF = None
BONE = "Weapon_R"
_b = rig.data.bones[BONE]
GRIP = rig.matrix_world @ _b.head_local
AX = (rig.matrix_world.to_3x3() @ (_b.tail_local - _b.head_local)).normalized()
F = _frame(GRIP, AX, hint=(0, 0, 1))             # local +Z along the haft toward the blade, local +Y = edge side
def W(y, z, x=0.0): return F @ V((x, y, z))       # staff-local -> world
def seg(mi, u0, u1, r0, r1, N=12, sub=0, smooth=True):
    loft(BONE, mi, [(u0, r0, r0), (u1, r1, r1)], N=N, M=F, sub=sub, smooth=smooth)
HR = 0.045                                        # haft radius (pose_fix HAFT_R is 0.047: the palm seat fits it)
BUTT, HEAD = -0.82, 1.55
# ---- haft: ivory shaft, gold collars, teal grip wraps where the hands sit ----
seg(IVO, BUTT + 0.1, HEAD, HR, HR, N=14)
for u in (-0.72, -0.62, -0.08, 0.3, 0.9, 1.45):
    seg(GOLD, u - 0.022, u + 0.022, HR + 0.012, HR + 0.012, N=14)
    seg(GOLD, u - 0.03, u + 0.03, HR + 0.006, HR + 0.006, N=14)
for u0, u1 in ((-0.06, 0.28), (-0.6, -0.12)):      # right-hand and left-hand wraps
    for i in range(7):
        u = u0 + (u1 - u0)*(i + 0.5)/7
        loft(BONE, TEAL, [(-0.018, HR + .006, HR + .006), (0.018, HR + .006, HR + .006)], N=12,
             M=F @ Matrix.Translation((0, 0, u)) @ Matrix.Rotation(0.3, 4, 'X'), cap=False)
# ---- butt: gold cap and a crystal counterweight ----
seg(GOLD, BUTT - 0.02, BUTT + 0.12, HR + 0.02, HR + 0.008, N=14, sub=1)
crystal(BONE, W(0, BUTT - 0.0), -AX, 0.05, 0.2, sides=6)
for a in range(4):
    d = F.to_3x3() @ V((math.cos(a*math.pi/2 + 0.4), math.sin(a*math.pi/2 + 0.4), -0.9))
    crystal(BONE, W(0, BUTT + 0.02), d, 0.022, 0.1, sides=4)
# ---- head socket: gold, flared, holding the crystal ----
loft(BONE, GOLD, [(HEAD - 0.06, HR + .01, HR + .01), (HEAD + 0.04, HR + .03, HR + .03), (HEAD + 0.12, .085, .06), (HEAD + 0.17, .07, .05)],
     N=16, M=F, sub=1)
# ---- the crescent: swept lens sections along a moon-arc in the local (Y, Z) plane ----
def sweep(mi, mid, width, thick, edge_mi=None):
    """mid: list of (y, z) centre points; width/thick: per point. Section = lens across the arc's normal (in-plane) x
       thickness (local X). Outer edge faces the arc's convex side."""
    tb = bmesh.new(); rings = []; n = len(mid); NS = 8
    for i, (y, z) in enumerate(mid):
        a = V(mid[max(i - 1, 0)]); b = V(mid[min(i + 1, n - 1)]); t2 = (b - a).normalized(); nrm = V((t2.y, -t2.x))   # in-plane normal
        w, th = width[i], thick[i]; ring = []
        for k in range(NS):
            ang = 2*math.pi*k/NS; cw, st = math.cos(ang), math.sin(ang)
            off = nrm*(w*cw); ring.append(tb.verts.new((th*st*(1 - 0.5*abs(cw)), y + off.x, z + off.y)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(NS):
            f = tb.faces.new((r0[k], r0[(k + 1) % NS], r1[(k + 1) % NS], r1[k]))
            f.material_index = edge_mi if (edge_mi is not None and k in (0, 1, NS - 1)) else mi
    tb.faces.new(rings[0]); tb.faces.new(list(reversed(rings[-1])))
    _add(tb, BONE, None, F, smooth=False, sub=0)
N_ = 18
# crescent: rises from the socket, swells toward the edge side, then hooks back to a point over the haft line
main = []
for i in range(N_):
    t = i/(N_ - 1)
    main.append((0.34*math.sin(t*math.pi*0.92) - 0.02*t, HEAD + 0.12 + 0.98*t - 0.12*t*t))
wid = [0.05 + 0.1*math.sin(min(1, t*1.15)*math.pi)**0.8 for t in [i/(N_ - 1) for i in range(N_)]]
wid[-1] = 0.006; wid[-2] *= 0.55
thk = [0.028*(1 - 0.6*i/(N_ - 1)) for i in range(N_)]
sweep(CRYST, main, wid, thk)
# portal-glow fuller along the crescent's spine (just proud of both faces)
for sx in (1, -1):
    pts = [W(y, z, sx*(thk[i]*0.72)) for i, (y, z) in enumerate(main[1:-3], start=1)]
    for a, b in zip(pts, pts[1:]): tube(BONE, GLOW, tuple(a), tuple(b), 0.009, 0.009, N=5)
# gold spine along the inner (concave) curve
spine = []
for i, (y, z) in enumerate(main[:-2]):
    a = V(main[max(i - 1, 0)]); b = V(main[min(i + 1, N_ - 1)]); t2 = (b - a).normalized(); nrm = V((t2.y, -t2.x))
    p = V((y, z)) - nrm*(wid[i]*0.92); spine.append(W(p.x, p.y))
for a, b in zip(spine, spine[1:]): tube(BONE, GOLD, tuple(a), tuple(b), 0.017, 0.017, N=6)
for q in spine[1:-1]: sph(BONE, GOLD, tuple(q), 0.0172, u=6, v=4)
# back-horn: a smaller crescent hooking the other way, so the head reads as a moon
horn = []
for i in range(9):
    t = i/8
    horn.append((-0.2*math.sin(t*math.pi*0.8) - 0.03, HEAD + 0.13 + 0.36*t))
hw = [0.035 + 0.035*math.sin(t*math.pi) for t in [i/8 for i in range(9)]]; hw[-1] = 0.005
sweep(CRYST, horn, hw, [0.022*(1 - 0.5*i/8) for i in range(9)])
# portal eye: a glow ring set in gold where crescent and horn meet the socket (the Sanctum key's bow)
EYE = W(0.0, HEAD + 0.22)
loft(BONE, GOLD, [(-0.03, .07, .07), (0.03, .07, .07), (0.03, .05, .05), (-0.03, .05, .05)], N=20,
     M=Matrix.Translation(EYE) @ (F.to_3x3() @ Matrix.Rotation(math.pi/2, 3, 'Y')).to_4x4())
loft(BONE, GLOW, [(-0.012, .05, .05), (0.012, .05, .05)], N=20, M=Matrix.Translation(EYE) @ (F.to_3x3() @ Matrix.Rotation(math.pi/2, 3, 'Y')).to_4x4())
# VFX sockets for the weapon trail (Studio Trail between the two attachments)
add_bone("VFX_StaffBase", W(0.05, HEAD + 0.2), W(0.05, HEAD + 0.3), BONE)
add_bone("VFX_StaffTip", W(main[-1][0], main[-1][1] - 0.02), W(main[-1][0], main[-1][1] + 0.08), BONE)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n in ("VFX_StaffBase", "VFX_StaffTip"):
    h, t = BONES[BIDX[n]][1], BONES[BIDX[n]][2]
    eb = rig.data.edit_bones.new(n); eb.head = rig.matrix_world.inverted() @ V(h); eb.tail = rig.matrix_world.inverted() @ V(t)
    eb.parent = rig.data.edit_bones[BONE]
bpy.ops.object.mode_set(mode='OBJECT')
# ---- assemble the staff (skinned to Weapon_R, same rig); glow split into its own mesh like assemble() does ----
STAFF_OBJS = []
_all = PIECES["Staff"]; _g = _all.copy()
bmesh.ops.delete(_g, geom=[f for f in _g.faces if f.material_index != GLOW], context='FACES')
bmesh.ops.delete(_all, geom=[f for f in _all.faces if f.material_index == GLOW], context='FACES')
for pn, bm in (("Staff", _all), ("StaffGlow", _g)):
    nm = f"{NAME}_{pn}"
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
    for m in MATS: me.materials.append(m)
    o = bpy.data.objects.new(nm, me)
    for b in BONES: o.vertex_groups.new(name=b[0])
    bpy.context.scene.collection.objects.link(o); o.parent = rig
    o.matrix_parent_inverse = rig.matrix_world.inverted()
    o.modifiers.new("Armature", 'ARMATURE').object = rig
    PARTS.append(o); STAFF_OBJS.append(o)
    print(f"PIECE {nm}: {sum(len(p.vertices) - 2 for p in me.polygons)} tris")
