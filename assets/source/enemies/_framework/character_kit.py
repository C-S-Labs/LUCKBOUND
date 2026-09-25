# Character kit: reusable HUMANOID dressing for basic enemies (and anything built with humanoid.py).
# exec() after enemy_kit.py + humanoid.py. Gives basics real character in the enemies' shared design language:
# layered smooth plates with trim rims, surface-following trim/glow flow lines, capes, faulds, bracers, knee cops.
# Everything is sized from the humanoid joints J and scale k, so one call fits any height/build.
# Budget: a full dress is ~3-6k tris; put dressing in its own PIECE (e.g. PIECE = "Armour") so meshes stay < 10k.
import math, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

def body_bvh():
    """BVH of everything built so far (all pieces) - for placing trim ON the surface."""
    vs, fs = [], []
    for bm in PIECES.values(): bm.verts.ensure_lookup_table(); bm.verts.index_update()
    for bm in PIECES.values():
        o = len(vs)
        vs += [v.co.copy() for v in bm.verts]
        fs += [tuple(o + v.index for v in f.verts) for f in bm.faces]
    for bm in PIECES.values(): bm.verts.index_update()
    return BVHTree.FromPolygons(vs, fs)

def on_surface_in(T, p, centre, lift=0.0, settle=1.0):
    """Cast from INSIDE (centre) out through p: the first hit is the body's own skin, never an outer part.
       settle < 1 pulls the point toward the centre: smoothed (sub=1) surfaces shrink a little after this is placed."""
    c = Vector(centre); d = (Vector(p) - c)
    hit = T.ray_cast(c, d.normalized(), 10.0)
    return (c + (hit[0] - c)*settle + hit[1]*lift) if hit[0] is not None else Vector(p)

def flow_line_in(bone, mi, pts, r=0.006, T=None, centre=None, N=6):
    P_ = [on_surface_in(T, p, centre, lift=r*0.3) for p in pts]
    for a, b in zip(P_, P_[1:]): tube(bone, mi, tuple(a), tuple(b), r, r, N=N)
    for q in P_[1:-1]: sph(bone, mi, tuple(q), r*1.02, u=N, v=4)
    return P_

def on_surface(T, p, centre, lift=0.004):
    """Project p onto the body surface along the ray from `centre` through p (outside-in), lifted slightly."""
    p = Vector(p); c = Vector(centre); d = (p - c)
    if d.length < 1e-6: return p
    origin = c + d.normalized()*(d.length + 0.5)
    hit = T.ray_cast(origin, -d.normalized())
    return (hit[0] + hit[1]*lift) if hit[0] is not None else p

def flow_line(bone, mi, pts, r=0.006, T=None, centre=None, N=6):
    """Smooth trim / glow line through pts (optionally hugged onto the body surface)."""
    P_ = [on_surface(T, p, centre) if T is not None else Vector(p) for p in pts]
    for a, b in zip(P_, P_[1:]):
        tube(bone, mi, tuple(a), tuple(b), r, r, N=N)
    for q in P_[1:-1]:
        sph(bone, mi, tuple(q), r*1.02, u=N, v=4)
    return P_

def shaped_limbs(J, k, m_limb, bulk=1.0, limb=1.0):
    """Muscle-shaped sleeves over humanoid.py's stick limbs (bicep, forearm, thigh, calf) - reads as a body, not a doll."""
    L = limb*k*bulk
    for side in ("Left", "Right"):
        j = J[side]
        for bone, a, c, rs in ((f"{side}UpperArm", j["sh"], j["el"], (0.055, 0.068, 0.06, 0.045)),
                               (f"{side}LowerArm", j["el"], j["wr"], (0.05, 0.056, 0.042, 0.034)),
                               (f"{side}UpperLeg", j["hp"], j["kn"], (0.08, 0.088, 0.072, 0.056)),
                               (f"{side}LowerLeg", j["kn"], j["an"], (0.058, 0.066, 0.046, 0.038))):
            a, c = Vector(a), Vector(c); d = c - a; n = d.length
            loft(bone, m_limb, [(0.0, rs[0]*L, rs[0]*L*1.05), (n*0.3, rs[1]*L, rs[1]*L*1.1), (n*0.7, rs[2]*L, rs[2]*L*1.05), (n, rs[3]*L, rs[3]*L)],
                 N=16, M=_frame(a, d), sub=1)

def layered_pauldron(side, J, k, m_plate, m_trim, layers=3, spike=None, size=1.0):
    s = 1 if side == "Left" else -1; j = J[side]; sh = Vector(j["sh"]); bn = f"{side}UpperArm"
    for i in range(layers):
        z = sh.z + (0.05 - 0.045*i)*k; r = (0.12 - 0.012*i)*k*size
        c = Vector((sh.x + (0.02 + 0.018*i)*s*k, 0, z))
        sph(bn, m_plate, tuple(c), r, scale=(1.05, 1.0, 0.55 - 0.05*i), cut_below=0.0, u=20, v=10)
        loft(bn, m_trim, [(0, r*1.03, r*1.0*1.03), (0.008*k, r*1.03, r*1.03)], N=24, M=Matrix.Translation(c), cap=False)
    if spike:
        blade(bn, m_trim, (sh.x + 0.1*s*k, 0, sh.z + 0.08*k), (0.6*s, 0.1, 1.0), spike*k, 0.035*k, 0.012*k, hint=(0, 1, 0), N=6)

def gorget(k, z, m_plate, m_trim, r=0.1, depth=0.085):
    loft("UpperTorso", m_plate, [(z - 0.05*k, r*k, depth*k, 2.2), (z, (r + 0.02)*k, (depth + 0.015)*k, 2.2), (z + 0.035*k, (r - 0.015)*k, (depth - 0.01)*k, 2.2)],
         N=24, sub=1, cap=False)
    loft("UpperTorso", m_trim, [(z, (r + 0.023)*k, (depth + 0.018)*k, 2.2), (z + 0.008*k, (r + 0.023)*k, (depth + 0.018)*k, 2.2)], N=24, cap=False)

def faulds(J, k, z_top, m_plate, m_trim, n=3, width=0.13, drop=0.09, front=True, back=True, sides=True):
    """Hanging plate skirt: layered tassets front/back/sides with trim rims."""
    spots = []
    if front: spots.append((0.0, -1))
    if back: spots.append((0.0, 1))
    if sides: spots += [(1, 0), (-1, 0)]
    for sx, sy in spots:
        for i in range(n):
            zc = z_top - drop*i*k
            w = (width - 0.012*i)*k
            ang = math.atan2(sx, -sy) if (sx or sy) else 0
            off = Vector((0.15*sx*k, 0.12*sy*k if sy else 0, zc))
            M = Matrix.Translation(off) @ Matrix.Rotation(-ang, 4, 'Z') @ Matrix.Rotation(0.12*(1 if sy <= 0 else -1) if sy else 0, 4, 'X')
            box("LowerTorso", m_plate, tuple(off), (w, 0.022*k, drop*1.25*k), rot=(0.1*(-sy), 0, -ang), bev=0.008*k, segs=2)
            box("LowerTorso", m_trim, tuple(off + Vector((0, 0, -drop*0.62*k))), (w*1.02, 0.026*k, 0.012*k), rot=(0.1*(-sy), 0, -ang), bev=0.004*k, segs=1)

def cape(k, z_top, z_bot, m_cloth, m_trim, width=0.34, y=0.13, bow=0.05):
    cloth("UpperTorso", "LowerTorso", z_top - 0.35*k, m_cloth, y*k, z_top, z_bot, width*0.8*k, width*1.15*k, bow=bow, teeth=5, depth=0.1*k,
          face=1, cols=10, rows=10)
    arc_band("UpperTorso", m_trim, (0, y*0.2*k), z_top + 0.01*k, z_top - 0.01*k, (width*0.55*k, y*1.05*k), (width*0.57*k, y*1.08*k),
             -0.2, math.pi + 0.2, 0.012*k, 16)

def bracer(side, J, k, m_plate, m_trim, m_glow=None):
    j = J[side]; a, c = Vector(j["el"]), Vector(j["wr"]); d = c - a; n = d.length; bn = f"{side}LowerArm"
    M = _frame(a + d*0.3, d)
    loft(bn, m_plate, [(0, .058*k, .06*k, 2.3), (n*0.5, .054*k, .056*k, 2.3), (n*0.62, .046*k, .048*k, 2.3)], N=16, M=M, sub=1)
    for t in (0.0, n*0.6):
        loft(bn, m_trim, [(t, .061*k, .063*k, 2.3), (t + 0.01*k, .061*k, .063*k, 2.3)], N=16, M=M, cap=False)
    if m_glow is not None:
        tube(bn, m_glow, tuple(M @ Vector((0, -.06*k, n*0.08))), tuple(M @ Vector((0, -.052*k, n*0.5))), 0.006*k, 0.005*k, N=5)

def knee_cop(side, J, k, m_plate, m_trim, spike=0.0):
    j = J[side]; kn = Vector(j["kn"]); bn = f"{side}LowerLeg"
    sph(bn, m_plate, (kn.x, kn.y - 0.05*k, kn.z), 0.065*k, scale=(1.0, 0.65, 1.1), u=16, v=10)
    loft(bn, m_trim, [(0, .066*k, .043*k), (0.008*k, .066*k, .043*k)], N=18, M=TR((kn.x, kn.y - 0.05*k, kn.z)), cap=False)
    if spike:
        blade(bn, m_trim, (kn.x, kn.y - 0.09*k, kn.z + 0.02*k), (0, -0.7, 0.7), spike*k, 0.03*k, 0.01*k, hint=(1, 0, 0), N=6)

def greave(side, J, k, m_plate, m_trim):
    j = J[side]; a, c = Vector(j["kn"]), Vector(j["an"]); d = c - a; n = d.length; bn = f"{side}LowerLeg"
    M = _frame(a + d*0.18, d)
    loft(bn, m_plate, [(0, .07*k, .072*k, 2.3), (n*0.35, .07*k, .078*k, 2.3), (n*0.72, .052*k, .056*k, 2.3)], N=16, M=M, sub=1,
         keep=lambda co: co.y < 0.03*k or True)
    loft(bn, m_trim, [(n*0.72, .054*k, .058*k, 2.3), (n*0.72 + 0.01*k, .054*k, .058*k, 2.3)], N=16, M=M, cap=False)

def chest_emblem(k, z, y, m_trim, m_glow, r=0.05):
    gem("UpperTorso", m_glow, (0, y, z), r*0.7*k, r*0.55*k, rot=(math.pi/2, 0, 0), sides=6)
    loft("UpperTorso", m_trim, [(0, r*k, r*k), (0.012*k, r*k, r*k), (0.012*k, r*0.8*k, r*0.8*k), (0, r*0.8*k, r*0.8*k)], N=18,
         M=TR((0, y + 0.004*k, z), (math.pi/2, 0, 0)))
    for s in (1, -1):                                       # rays of trim out from the emblem
        blade("UpperTorso", m_trim, (0.05*s*k, y + 0.01*k, z + 0.02*k), (s, 0.15, 0.5), 0.1*k, 0.018*k, 0.006*k, hint=(0, 1, 0), N=5, sub=0)
