# LUCKBOUND - Sky Citadel MINIBOSS: Orrery Engine (Observatory). A floating astronomical machine.
# P1: rings orbit slowly; fires orbs; ring sweep (ducks/jumps). Core is hittable between sweeps.
# P2: rings spin up and separate; three orbs orbit the player and converge (dodge -> core exposed & stunned).
# Brass rings, deep navy core sphere with star inlays, star-white orbs, cyan aether. ~3 m tall, hovers.
# Rig: Root > Core > RingA/B/C (each spins on its own axis) > OrbA/B/C riding the rings; Tripod legs fold.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "OrreryEngine"; OFFSET = (66.0, 0.0, 0.0)
E = HERE
CZ = 1.9
BONES = [("Root", (0, 0, 0.4), (0, 0, 0.7), None), ("Core", (0, 0, CZ - 0.3), (0, 0, CZ + 0.3), "Root")]
RINGS = [("A", 1.05, (0.35, 0.0, 0.0)), ("B", 0.85, (1.2, 0.5, 0.0)), ("C", 0.65, (-0.6, 1.1, 0.4))]
for n, r, rot in RINGS:
    BONES.append((f"Ring{n}", (0, 0, CZ), (0, 0, CZ + 0.2), "Core"))
    ax = Euler(rot).to_matrix() @ Vector((1, 0, 0))
    BONES.append((f"Orb{n}", tuple(Vector((0, 0, CZ)) + ax*r), tuple(Vector((0, 0, CZ)) + ax*(r + 0.2)), f"Ring{n}"))
for i in range(3):
    a = i*2*math.pi/3 + math.pi/2
    BONES.append((f"Leg{i+1}", (0.15*math.cos(a), 0.15*math.sin(a), CZ - 0.4), (0.55*math.cos(a), 0.55*math.sin(a), 0.35), "Core"))
BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
BIDX.update({b[0]: i for i, b in enumerate(BONES)})
MATS = [mat("OE_Brass", (0.78, 0.58, 0.25), 1.0, 0.18), mat("OE_Navy", (0.05, 0.08, 0.22), 0.5, 0.2),
        mat("OE_Dark", (0.08, 0.07, 0.06), 0.8, 0.3), mat("OE_Star", (0.95, 0.95, 1.0), 0.0, 0.2),
        mat("OE_Copper", (0.6, 0.32, 0.18), 1.0, 0.25), mat("OE_Glow", (0.4, 0.9, 1.0), 0, 0.3, (0.35, 0.85, 1.0), 3.0)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
BRASS, NAVY, DARK, STAR, COPPER = 0, 1, 2, 3, 4
# core sphere with a brass equator, star inlays, glowing aperture
sph("Core", NAVY, (0, 0, CZ), 0.38, u=32, v=18)
arc_band("Core", BRASS, (0, 0), CZ + 0.03, CZ - 0.03, (.385, .385), (.385, .385), 0, 2*math.pi, 0.025, 40)
for i in range(18):
    a = i*2.4; e = math.asin(-0.9 + 1.8*((i*0.618) % 1))
    p = Vector((math.cos(a)*math.cos(e), math.sin(a)*math.cos(e), math.sin(e)))*0.382 + Vector((0, 0, CZ))
    gem("Core", STAR, tuple(p), 0.014, 0.008, rot=tuple(p.to_track_quat('Z', 'Y').to_euler()) if False else (0, 0, 0), sides=4)
loft("Core", BRASS, [(0, .16, .16), (0.03, .17, .17), (0.05, .13, .13)], N=24, M=TR((0, -0.37, CZ), (math.pi/2, 0, 0)))
sph("Core", GLOW, (0, -0.4, CZ), 0.11, scale=(1, 0.5, 1), u=16, v=10)
# top finial + armillary pins
loft("Core", BRASS, [(CZ + 0.36, .08, .08), (CZ + 0.45, .05, .05), (CZ + 0.62, .01, .01)], N=12)
sph("Core", STAR, (0, 0, CZ + 0.66), 0.05, u=12, v=8)
# three rings (flat bands, each tilted) + their orbs
for n, r, rot in RINGS:
    M = TR((0, 0, CZ), rot)
    tb = bmesh.new(); seg = 64; w = 0.06; th = 0.025
    grid = []
    for i in range(seg):
        a = 2*math.pi*i/seg
        c, s_ = math.cos(a), math.sin(a)
        grid.append([tb.verts.new((c*(r - w), s_*(r - w), -th)), tb.verts.new((c*r, s_*r, -th)), tb.verts.new((c*r, s_*r, th)), tb.verts.new((c*(r - w), s_*(r - w), th))])
    for i in range(seg):
        g0, g1 = grid[i], grid[(i + 1) % seg]
        for q in range(4):
            tb.faces.new((g0[q], g1[q], g1[(q + 1) % 4], g0[(q + 1) % 4]))
    _add(tb, f"Ring{n}", BRASS if n != "B" else COPPER, M)
    for m in range(12):   # engraved hour marks
        a = m*math.pi/6
        box(f"Ring{n}", DARK, None, (0.015, 0.05, 0.055), bev=0.003, segs=1,
            M=M @ Matrix.Translation((math.cos(a)*(r - 0.03), math.sin(a)*(r - 0.03), 0)) @ Matrix.Rotation(a, 4, 'Z'))
    ax = Euler(rot).to_matrix() @ Vector((1, 0, 0))
    op = Vector((0, 0, CZ)) + ax*r
    sph(f"Orb{n}", STAR, tuple(op), 0.13 if n == "A" else 0.1, u=18, v=10)
    sph(f"Orb{n}", GLOW, tuple(op), 0.145 if n == "A" else 0.115, scale=(1, 1, 0.12), u=18, v=4)
# tripod legs (fold up in flight), claw feet
for i in range(3):
    b = BONES[BIDX[f"Leg{i+1}"]]
    tube(f"Leg{i+1}", DARK, b[1], b[2], 0.05, 0.03, N=10)
    sph(f"Leg{i+1}", BRASS, b[1], 0.07, u=12, v=8)
    blade(f"Leg{i+1}", BRASS, b[2], tuple(Vector(b[2]) - Vector(b[1]) + Vector((0, 0, -0.3))), 0.18, 0.05, 0.02, hint=(0, 0, 1), N=6, sub=0)
# --- miniboss detail pass ---
PIECE = "Mechanism"
for t_ in range(40):                                                   # gear ring on the core
    a = t_*2*math.pi/40
    box("Core", BRASS, None, (0.04, 0.05, 0.05), bev=0.006, segs=1, M=TR((0.405*math.cos(a), 0.405*math.sin(a), CZ), (0, 0, a)))
arc_band("Core", DARK, (0, 0), CZ + 0.05, CZ - 0.05, (.39, .39), (.39, .39), 0, 2*math.pi, 0.01, 48)
for n, r, rot in RINGS:                                                # zodiac glyph plates + moons
    M = TR((0, 0, CZ), rot)
    for g_ in range(6):
        a = g_*math.pi/3 + 0.26
        box(f"Ring{n}", STAR, None, (0.05, 0.07, 0.07), bev=0.008, segs=1,
            M=M @ Matrix.Translation((math.cos(a)*(r - 0.03), math.sin(a)*(r - 0.03), 0.03)) @ Matrix.Rotation(a, 4, 'Z'))
        gem(f"Ring{n}", GLOW, tuple(M @ Vector((math.cos(a)*(r - 0.03), math.sin(a)*(r - 0.03), 0.068))), 0.015, 0.012, sides=4)
    if n == "B":
        for m_ in range(2):
            a = 2.2 + m_*1.9
            sph(f"Ring{n}", COPPER, tuple(M @ Vector((math.cos(a)*r, math.sin(a)*r, 0))), 0.06, u=12, v=8)
add_bone("Telescope", (0, 0.1, CZ + 0.3), (0, -0.5, CZ + 0.75), "Core")  # telescope arm
tube("Telescope", BRASS, (0, 0.1, CZ + 0.3), (0, -0.15, CZ + 0.55), 0.05, 0.04, N=12)
sph("Telescope", DARK, (0, -0.15, CZ + 0.55), 0.06, u=12, v=8)
Mt_ = _frame(Vector((0, -0.15, CZ + 0.55)), Vector((0, -1, 0.7)))
loft("Telescope", BRASS, [(0, .07, .07), (0.3, .06, .06), (0.32, .08, .08), (0.4, .08, .08)], N=16, M=Mt_, cap=False)
loft("Telescope", GLOW, [(0.38, .07, .07), (0.39, .07, .07)], N=16, M=Mt_)
for i in range(3):                                                     # counterweight chains
    a = i*2*math.pi/3 + math.pi/6
    top = Vector((0.25*math.cos(a), 0.25*math.sin(a), CZ - 0.3))
    for li in range(6):
        c = top + Vector((0, 0, -0.07*li))
        loft("Core", DARK, [(-0.03, .015, .03), (0.03, .015, .03)], N=8, M=_frame(c, Vector((0, 0, 1))) @ Matrix.Rotation((li % 2)*math.pi/2, 4, 'Z'), cap=False)
    gem("Core", STAR, tuple(top + Vector((0, 0, -0.5))), 0.05, 0.08, sides=6)
rig, PARTS = assemble(NAME, OFFSET)
