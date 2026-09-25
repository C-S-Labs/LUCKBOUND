# LUCKBOUND - Sky Citadel BASIC enemy: Spring Eel (medium range; Aether Springs).
# Lunges from a spring (bite), spits aether, dives and resurfaces elsewhere. Only hittable while SURFACED - the
# lunge recovery (lying across the rim) is the punish window. Turquoise body, glowing cyan belly seam, pearl fins,
# frilled head with a hinged jaw. Rig: Seg01-Seg12 spine chain (root at the water line) > Head > Jaw, FrillL/R.
import bpy, bmesh, math
from mathutils import Matrix, Euler, Vector
NAME = "SpringEel"; OFFSET = (45.0, 0.0, 0.0)
E = HERE
BONES = []; BIDX = {}; PIECES = {}; PIECE = "Body"; PARTLOG = []; BREAK = False; XF = None
exec(open(FW + r"\enemy_kit.py").read())
MATS = [mat("SE_Teal", (0.1, 0.5, 0.5), 0.3, 0.2), mat("SE_Deep", (0.04, 0.2, 0.26), 0.3, 0.25),
        mat("SE_Pearl", (0.88, 0.9, 0.92), 0.4, 0.15), mat("SE_Mouth", (0.35, 0.08, 0.12), 0.0, 0.4),
        mat("SE_Fang", (0.95, 0.93, 0.85), 0.0, 0.3), mat("SE_Glow", (0.4, 1.0, 0.95), 0, 0.2, (0.3, 1.0, 0.9), 2.5)]
PATINA, BRONZE, IRON, IVORY, CLOTH, GLOW = range(6)
TEAL, DEEP, PEARL, MOUTH, FANG = 0, 1, 2, 3, 4
# spine: an S rising from the spring at the origin, head arched forward at ~2.1 m
N = 12
def spine(t):
    return Vector((0.28*math.sin(t*math.pi*1.4), 0.35*math.sin(t*math.pi) - 0.1 - 0.35*t, 0.05 + 2.0*math.sin(t*math.pi*0.55)))
pts = [spine(i/N) for i in range(N + 1)]
for i in range(N):
    BONES.append((f"Seg{i+1:02d}", tuple(pts[i]), tuple(pts[i+1]), f"Seg{i:02d}" if i else None))
hd0 = pts[-1]; hdir = (pts[-1] - pts[-2]).normalized(); hdir = (hdir + Vector((0, -1.2, -0.3))).normalized()
BONES += [("Head", tuple(hd0), tuple(hd0 + hdir*0.32), f"Seg{N:02d}"),
          ("Jaw", tuple(hd0 + hdir*0.04 + Vector((0, 0, -0.05))), tuple(hd0 + hdir*0.3 + Vector((0, 0, -0.09))), "Head")]
BIDX.update({b[0]: i for i, b in enumerate(BONES)})
R = lambda t: 0.17*(1 - 0.55*t) + 0.03    # body radius taper (thick at the base)
for i in range(N):
    a, b = pts[i], pts[i+1]; t0, t1 = i/N, (i + 1)/N
    Mf = _frame(a, b - a, hint=(1, 0, 0))
    L = (b - a).length
    loft(f"Seg{i+1:02d}", TEAL, [(-0.02, R(t0), R(t0)*0.92), (L*0.5, R((t0 + t1)/2)*1.03, R((t0 + t1)/2)*0.95), (L + 0.02, R(t1), R(t1)*0.92)], N=14, M=Mf)
    # belly seam (glowing) + dorsal pearl fin
    loft(f"Seg{i+1:02d}", GLOW, [(0, .025, .02, 2, 0, -R(t0)*0.9), (L, .022, .02, 2, 0, -R(t1)*0.9)], N=6, M=Mf)
    if 1 <= i <= N - 2:
        blade(f"Seg{i+1:02d}", PEARL, tuple(a.lerp(b, 0.5) + (Mf.to_3x3() @ Vector((0, R(t0)*0.85, 0)))), tuple(Mf.to_3x3() @ Vector((0, 1, -0.9))),
              0.16*(1 - 0.4*t0), 0.05, 0.008, hint=tuple(Mf.to_3x3() @ Vector((1, 0, 0))), N=6, sub=0)
    if i % 3 == 1:   # side fins
        for s in (1, -1):
            blade(f"Seg{i+1:02d}", PEARL, tuple(a + (Mf.to_3x3() @ Vector((R(t0)*0.9*s, 0, 0)))), tuple(Mf.to_3x3() @ Vector((s, -0.2, -0.6))),
                  0.18, 0.06, 0.008, hint=tuple(Mf.to_3x3() @ Vector((0, 1, 0))), N=6, sub=0)
# head: long skull, frill, glowing eyes, jaw with fangs, whisker barbels
Mh = _frame(hd0, hdir, hint=(0, 0, 1))
loft("Head", TEAL, [(-0.05, .085, .085), (0.08, .11, .09), (0.22, .08, .06), (0.33, .03, .03)], N=16, M=Mh, sub=1)
loft("Head", DEEP, [(0.05, .06, .03, 2, 0, .07), (0.28, .03, .02, 2, 0, .04)], N=8, M=Mh)
for s in (1, -1):
    sph("Head", GLOW, tuple(Mh @ Vector((0.075*s, 0.045, 0.12))), 0.022, u=8, v=6)
    add_bone(f"Frill{'L' if s > 0 else 'R'}", Mh @ Vector((0.08*s, 0.03, 0.02)), Mh @ Vector((0.25*s, 0.1, -0.1)), "Head")
    for f in range(3):
        blade(f"Frill{'L' if s > 0 else 'R'}", PEARL, tuple(Mh @ Vector((0.08*s, 0.03 + f*0.02, 0.02 - f*0.03))),
              tuple(Mh.to_3x3() @ Vector((s, 0.3 + f*0.3, -0.5))), 0.2 - 0.03*f, 0.05, 0.008, hint=tuple(Mh.to_3x3() @ Vector((0, 0, 1))), N=6, sub=0)
    tube("Head", PEARL, tuple(Mh @ Vector((0.05*s, -0.02, 0.28))), tuple(Mh @ Vector((0.18*s, -0.1, 0.42))), 0.008, 0.002, N=5)   # barbel
Mj = _frame(Vector(BONES[BIDX["Jaw"]][1]), Vector(BONES[BIDX["Jaw"]][2]) - Vector(BONES[BIDX["Jaw"]][1]), hint=(0, 0, 1))
loft("Jaw", TEAL, [(0, .07, .035), (0.2, .05, .025), (0.27, .02, .015)], N=12, M=Mj, sub=1)
loft("Jaw", MOUTH, [(0.02, .055, .01, 2, 0, .03), (0.24, .02, .008, 2, 0, .02)], N=8, M=Mj)
for f in range(4):
    for s in (1, -1):
        blade("Jaw", FANG, tuple(Mj @ Vector((0.04*s, 0.035, 0.06 + f*0.05))), tuple(Mj.to_3x3() @ Vector((0, 1, 0.1))), 0.05, 0.012, 0.008,
              hint=tuple(Mj.to_3x3() @ Vector((1, 0, 0))), N=4, sub=0)
        blade("Head", FANG, tuple(Mh @ Vector((0.05*s, -0.04, 0.08 + f*0.05))), tuple(Mh.to_3x3() @ Vector((0, -1, 0.1))), 0.05, 0.012, 0.008,
              hint=tuple(Mh.to_3x3() @ Vector((1, 0, 0))), N=4, sub=0)
# spring ripple ring at the base (glow; separate so Studio can animate/hide it)
PIECE = "Ripple"
arc_band("Seg01", GLOW, (0, -0.1), 0.02, 0.0, (.42, .42), (.46, .46), 0, 2*math.pi, 0.02, 40)
arc_band("Seg01", GLOW, (0, -0.1), 0.015, 0.0, (.6, .6), (.63, .63), 0, 2*math.pi, 0.015, 48)
PIECE = "Body"
exec(open(FW + r"\character_kit.py").read())
# ---- v2 character pass (2026-09-24), moveset-driven: LUNGE BITE, SPIT, DIVE ----
# a pearl dorsal fin ridge running the whole spine (reads the lunge arc), glowing lateral spots (visible while it
# is surfaced = when you can hit it), gill frills + whisker barbels on the head.
for i in range(2, N):
    a, b = pts[i], pts[i + 1]; t0 = i/N
    d = (b - a).normalized(); side = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0))
    up = side.cross(d).normalized()
    blade(f"Seg{i + 1:02d}", PEARL, tuple(a.lerp(b, 0.5) + up*R(t0)*0.85), tuple(up*1.0 - d*0.5), 0.12*(1 - 0.4*t0) + 0.04, 0.05, 0.008, hint=tuple(d), N=5, sub=0)
    for sd in (1, -1):
        sph(f"Seg{i + 1:02d}", GLOW, tuple(a.lerp(b, 0.5) + side*sd*R(t0)*0.93), 0.016, scale=(1, 1, 1), u=8, v=6)
hd = pts[-1]
for sd in (1, -1):
    for g in range(3):                                                       # gill frills
        blade("Head", PEARL, tuple(hd + Vector((0.07*sd, 0.03*g, -0.02))), (sd, 0.5, 0.1 - 0.1*g), 0.1, 0.035, 0.006, hint=(0, 0, 1), N=5, sub=0)
    wp = [hd + hdir*0.26 + Vector((0.035*sd, 0, -0.03)) + Vector((0.09*sd*u, -0.05*u, -0.12*u*u)) for u in [i/4 for i in range(5)]]
    for a_, b_ in zip(wp, wp[1:]): tube("Head", PEARL, tuple(a_), tuple(b_), 0.006, 0.003, N=5)   # barbels
PIECE = "Body"
rig, PARTS = assemble(NAME, OFFSET)
