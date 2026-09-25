# Generic LUCKBOUND humanoid body (R15 bone names) for enemy scripts. exec() after enemy_kit.py.
# make_humanoid(H, ...) scales a 1.8 m base skeleton to height H, adds the bones, and builds a plain body
# (limbs, torso, pelvis, head, hands, feet) from the given material indices. Costume parts go on top.
def make_humanoid(H=1.8, shoulder=0.21, hip=0.105, bulk=1.0, limb=1.0, m_body=None, m_limb=None, m_skin=None,
                  head=True, hands=True, fingers=False, torso_secs=None, build_body=True):
    """build_body=False: bones + joints only (for fully custom, shaped bodies)."""
    k = H/1.8
    def P(x, y, z): return (x*k, y*k, z*k)
    BONES.extend([("HumanoidRootNode", P(0, 0, 0.88), P(0, 0, 0.98), None),
                  ("LowerTorso", P(0, 0, 0.95), P(0, 0, 1.12), "HumanoidRootNode"),
                  ("UpperTorso", P(0, 0, 1.12), P(0, 0, 1.50), "LowerTorso"),
                  ("Head", P(0, 0, 1.52), P(0, 0, 1.80), "UpperTorso")])
    J = {}
    for side, s in (("Left", 1), ("Right", -1)):
        sx = shoulder*s; hx = hip*s
        J[side] = dict(sh=P(sx, 0, 1.46), el=P(sx*1.08, 0.01, 1.19), wr=P(sx*1.12, 0, 0.93), hd=P(sx*1.12, -0.01, 0.80),
                       hp=P(hx, 0, 0.95), kn=P(hx, 0, 0.52), an=P(hx, 0.01, 0.09), toe=P(hx, -0.14, 0.03))
        j = J[side]
        BONES.extend([(f"{side}UpperArm", j["sh"], j["el"], "UpperTorso"), (f"{side}LowerArm", j["el"], j["wr"], f"{side}UpperArm"),
                      (f"{side}Hand", j["wr"], j["hd"], f"{side}LowerArm"),
                      (f"{side}UpperLeg", j["hp"], j["kn"], "LowerTorso"), (f"{side}LowerLeg", j["kn"], j["an"], f"{side}UpperLeg"),
                      (f"{side}Foot", j["an"], j["toe"], f"{side}LowerLeg")])
    BIDX.clear(); BIDX.update({b[0]: i for i, b in enumerate(BONES)})
    if not build_body:
        return J, k
    mb = m_body if m_body is not None else PATINA
    ml = m_limb if m_limb is not None else IRON
    ms = m_skin if m_skin is not None else ml
    b = bulk*k
    ts = torso_secs or [(1.10, .14, .10), (1.25, .16, .11), (1.38, .19, .115), (1.47, .17, .10), (1.52, .08, .07)]
    loft("UpperTorso", mb, [(z*k, rx*b, ry*b, 2.4) for z, rx, ry in ts], N=20, sub=1)
    loft("LowerTorso", mb, [(0.93*k, .13*b, .10*b, 2.4), (1.02*k, .15*b, .11*b, 2.4), (1.13*k, .135*b, .095*b, 2.4)], N=18, sub=1)
    if head:
        loft("Head", ms, [(1.50*k, .05*k, .05*k), (1.56*k, .05*k, .05*k)], N=10)
        sph("Head", ms, P(0, -0.005, 1.66), 0.1*k, scale=(0.9, 1.0, 1.15), u=16, v=10)
    L = limb*k
    for side, s in (("Left", 1), ("Right", -1)):
        j = J[side]
        def seg(bone, a, c, r0, r1, m=ml):
            loft(bone, m, [(0, r0*L, r0*L), ((Vector(c) - Vector(a)).length, r1*L, r1*L)], N=12, M=_frame(a, Vector(c) - Vector(a)), cap=False)
        sph(f"{side}UpperArm", ml, j["sh"], 0.062*L, u=12, v=8)
        seg(f"{side}UpperArm", j["sh"], j["el"], 0.05, 0.04)
        sph(f"{side}LowerArm", ml, j["el"], 0.05*L, u=12, v=8)
        seg(f"{side}LowerArm", j["el"], j["wr"], 0.04, 0.032)
        if hands:
            sph(f"{side}Hand", ms, j["wr"], 0.035*L, u=8, v=6)
            box(f"{side}Hand", ms, tuple(Vector(j["wr"]).lerp(Vector(j["hd"]), 0.5)), (0.04*L, 0.08*L, 0.1*L), bev=0.012, segs=1)
        sph(f"{side}UpperLeg", ml, j["hp"], 0.08*L, u=12, v=8)
        seg(f"{side}UpperLeg", j["hp"], j["kn"], 0.068, 0.05)
        sph(f"{side}LowerLeg", ml, j["kn"], 0.062*L, u=12, v=8)
        seg(f"{side}LowerLeg", j["kn"], j["an"], 0.048, 0.036)
        loft(f"{side}Foot", ml, [(0, .045*L, .03*L), (0.16*k, .05*L, .035*L), (0.24*k, .03*L, .02*L)], N=10,
             M=TR((j["an"][0], j["an"][1] + 0.05*k, 0.04*k), (math.pi/2, 0, 0)), sub=1)
        if fingers:
            for fn, yy in (("Index", -0.03), ("Middle", -0.01), ("Ring", 0.01), ("Pinky", 0.03)):
                p0 = Vector(j["hd"]) + Vector((0, yy*k, 0.02*k)); p1 = p0 + Vector((0, 0, -0.045*k)); p2 = p1 + Vector((-0.005*s*k, 0, -0.035*k))
                add_bone(f"{side}{fn}1", p0, p1, f"{side}Hand"); add_bone(f"{side}{fn}2", p1, p2, f"{side}{fn}1")
                tube(f"{side}{fn}1", ms, p0, p1, 0.011*L, 0.01*L, N=6); tube(f"{side}{fn}2", ms, p1, p2, 0.01*L, 0.008*L, N=6)
            t0 = Vector(j["wr"]) + Vector((0, -0.04*k, -0.05*k)); t1 = t0 + Vector((0, -0.03*k, -0.03*k)); t2 = t1 + Vector((0, -0.02*k, -0.03*k))
            add_bone(f"{side}Thumb1", t0, t1, f"{side}Hand"); add_bone(f"{side}Thumb2", t1, t2, f"{side}Thumb1")
            tube(f"{side}Thumb1", ms, t0, t1, 0.012*L, 0.011*L, N=6); tube(f"{side}Thumb2", ms, t1, t2, 0.011*L, 0.009*L, N=6)
    return J, k
