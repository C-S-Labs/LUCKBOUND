# CLOTH_CHAINS core (framework): free-hanging cloth -- robes, skirts, capes, scarves, tassels -- for ANY enemy.
#
# Roblox plays bone keys and has no cloth solver, so cloth here is BAKED: each cloth piece gets its own chains of
# bones, a small verlet simulation runs over every action (gravity, damping, a pull back toward the piece's own shape,
# and collision with capsules around the legs / torso), and the result is keyed onto the chain bones. The mesh follows
# the chains by skinning, so a raised knee pushes the robe forward instead of passing through it.
#
# An enemy only DESCRIBES its cloth (content is data), in an extras script run after the body:
#   exec(open(FW + r"\cloth_core.py").read())
#   build_cloth([
#     dict(name="Robe", kind="skirt", meshes=["Waist"], anchor="LowerTorso", top=1.62, sectors=10, segments=4,
#          colliders=["LeftUpperLeg", "LeftLowerLeg", "RightUpperLeg", "RightLowerLeg"]),
#     dict(name="Scarf", kind="strips", meshes=["Ribbons", "RibbonsGlow"], segments=4, colliders=[...]),
#   ])
# The runner then calls cloth_bake() after every action (run.py). kinds:
#   skirt  - a ring of `sectors` chains hanging from `top` (world z at rest) down to the hem, around the anchor's
#            vertical axis. Islands entirely above `keep_above` (default `top`: belts, clasps) keep their weights.
#            Put `top` ABOVE the hip joints (hidden under a belt if there is one): a pinned ring below the hips
#            cannot open for a thigh raised in a deep crouch.
#   strips - one chain per strip. Islands closer than `join` are one strip (a scarf + its glow + its tip). Each strip
#            hangs from the end nearest its anchor bone (the bone most of its verts are weighted to now).
# Small islands (< `rigid_size`, e.g. hem spikes) move rigidly with the cloth point under their centre.
import bpy, bmesh, math
from mathutils import Vector, Matrix

CLOTH_CHAINS = []                                   # built chains: dicts with bones, rest points, anchor, colliders, tuning

def _pfx():
    return globals().get("PREFIX") or NAME + "_"            # extras run before run.py sets PREFIX

def _obj(n):
    return bpy.data.objects.get(_pfx() + n) or bpy.data.objects[n]

def _islands(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); seen = set(); out = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; grp = []
        while st:
            x = st.pop()
            if x.index in seen: continue
            seen.add(x.index); grp.append(x.index); st += [e.other_vert(x) for e in x.link_edges]
        out.append(grp)
    bm.free(); return out

def _wco(o, i):
    return o.matrix_world @ o.data.vertices[i].co

def _seg_closest(p, a, b):
    ab = b - a; t = 0.0 if ab.length_squared < 1e-12 else max(0.0, min(1.0, (p - a).dot(ab)/ab.length_squared))
    return a + ab*t, t

def _seg_seg(p1, q1, p2, q2):
    """Closest points between segments p1q1 and p2q2 (returns c1, c2, s, t)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1.dot(d1), d2.dot(d2), d2.dot(r)
    if a < 1e-12 and e < 1e-12: return p1, p2, 0.0, 0.0
    if a < 1e-12: s = 0.0; t = max(0.0, min(1.0, f/e))
    else:
        c = d1.dot(r)
        if e < 1e-12: t = 0.0; s = max(0.0, min(1.0, -c/a))
        else:
            b = d1.dot(d2); den = a*e - b*b
            s = max(0.0, min(1.0, (b*f - c*e)/den)) if den > 1e-12 else 0.0
            t = (b*s + f)/e
            if t < 0: t = 0.0; s = max(0.0, min(1.0, -c/a))
            elif t > 1: t = 1.0; s = max(0.0, min(1.0, (b - c)/a))
    return p1 + d1*s, p2 + d2*t, s, t

def _bone_radius(bone, pct=0.95):
    """Collider radius of `bone`: a high percentile of the distance to the bone axis of every vertex weighted > 0.5 to it."""
    b = rig.data.bones[bone]; a = rig.matrix_world @ b.head_local; t = rig.matrix_world @ b.tail_local; ds = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(_pfx()): continue
        g = o.vertex_groups.get(bone)
        if g is None: continue
        for v in o.data.vertices:
            for ge in v.groups:
                if ge.group == g.index and ge.weight > 0.5:
                    p = o.matrix_world @ v.co; c, s = _seg_closest(p, a, t)
                    if 0.02 < s < 0.98: ds.append((p - c).length)
    ds.sort()
    return ds[int(len(ds)*pct)] if ds else 0.1

def _set_weights(o, i, wts, clear):
    """Replace vertex i's weights (in groups `clear` plus the new ones) by wts {group: w}, max 4 influences (Roblox)."""
    top = sorted(wts.items(), key=lambda kv: -kv[1])[:4]; s = sum(w for _, w in top) or 1.0
    for g in list(o.vertex_groups):
        if g.name in clear or g.name in wts:
            try: g.remove([i])
            except RuntimeError: pass
    for n, w in top:
        if w/s < 1e-3: continue
        g = o.vertex_groups.get(n) or o.vertex_groups.new(name=n)
        g.add([i], w/s, 'REPLACE')

def _chain_weights(bones, s, anchor, blend=0.35):
    """Weights along one chain at chain parameter s (0 = top point, len(bones) = tip): the segment bone, blended
       with its neighbour near the joints so the mesh bends smoothly; above the top it blends into the anchor."""
    K = len(bones)
    if s <= 0.0:
        w = max(0.0, 1.0 + s/blend)                # s in [-blend, 0] fades from the first bone into the anchor
        return {bones[0]: 0.5*w, anchor: 1.0 - 0.5*w}
    k = min(int(s), K - 1); t = s - k                  # bone k spans points k..k+1
    out = {bones[k]: 1.0}
    if t < blend:
        other = bones[k - 1] if k > 0 else anchor; x = 0.5*(1 - t/blend); out[bones[k]] = 1 - x; out[other] = x
    elif t > 1 - blend and k < K - 1:
        x = 0.5*(1 - (1 - t)/blend); out[bones[k]] = 1 - x; out[bones[k + 1]] = x
    return out

def _add_bones(chains):
    """chains: [(bone_names, points (world, top first), anchor)]. Adds the chain bones to the rig in edit mode."""
    Mi = rig.matrix_world.inverted()
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    for names, pts, anchor in chains:
        parent = eb[anchor]
        for k, n in enumerate(names):
            b = eb.get(n) or eb.new(n)
            b.head = Mi @ pts[k]; b.tail = Mi @ pts[k + 1]; b.roll = 0.0
            b.parent = parent; b.use_connect = k > 0; b.use_deform = True
            parent = b
    bpy.ops.object.mode_set(mode='OBJECT')

def _skirt(spec):
    name, anchor, top, M, K = spec["name"], spec["anchor"], spec["top"], spec.get("sectors", 10), spec.get("segments", 4)
    rigid = spec.get("rigid_size", 0.15)
    a0 = rig.matrix_world @ rig.data.bones[anchor].head_local; cx, cy = a0.x, a0.y
    ang = lambda p: math.atan2(p.x - cx, -(p.y - cy)) % (2*math.pi)     # 0 = straight ahead (-Y), + toward its left
    panels, smalls, keep = [], [], []
    for mn in spec["meshes"]:
        o = _obj(mn)
        for isl in _islands(o):
            P = [_wco(o, i) for i in isl]
            size = max(max(p[k] for p in P) - min(p[k] for p in P) for k in range(3))
            if min(p.z for p in P) >= spec.get("keep_above", top) - 1e-4: keep.append((o, isl))
            elif size < rigid: smalls.append((o, isl, sum(P, Vector())/len(P)))
            else: panels.append((o, isl, P))
    allp = [p for _, _, P in panels for p in P if p.z < top]
    hem = min(p.z for p in allp)
    levels = [top - (top - hem)*k/K for k in range(K + 1)]
    band = (top - hem)/K*0.6
    chains = []
    for j in range(M):
        th = 2*math.pi*j/M; pts = []
        for k, z in enumerate(levels):
            sel = [p for p in allp if abs(p.z - z) < band and abs((ang(p) - th + math.pi) % (2*math.pi) - math.pi) < math.pi/M]
            r = sum(math.hypot(p.x - cx, p.y - cy) for p in sel)/len(sel) if sel else None
            pts.append([z, r])
        known = [p[1] for p in pts if p[1] is not None] or [0.3]
        for k, p in enumerate(pts):
            if p[1] is None: p[1] = pts[k - 1][1] if k else known[0]
        world = [Vector((cx + r*math.sin(th), cy - r*math.cos(th), z)) for z, r in pts]
        chains.append(([f"{name}_{j:02d}_{k}" for k in range(1, K + 1)], world, anchor))
    _add_bones(chains)
    clear = set(spec.get("replace", [])) | {anchor}
    def weights_at(p):
        s = (top - p.z)/(top - hem)*K
        a = ang(p)*M/(2*math.pi); j0 = int(a) % M; j1 = (j0 + 1) % M; f = a - int(a)
        w = {}
        for j, wj in ((j0, 1 - f), (j1, f)):
            for n, x in _chain_weights(chains[j][0], s, anchor).items(): w[n] = w.get(n, 0) + wj*x
        return w
    for o, isl, P in panels:
        for i, p in zip(isl, P): _set_weights(o, i, weights_at(p), clear)
    for o, isl, c in smalls:
        w = weights_at(c)
        for i in isl: _set_weights(o, i, w, clear)
    return [dict(spec=spec, kind="skirt", bones=b, rest=pts, anchor=an, ring=True) for b, pts, an in chains]

def _strips(spec):
    name, K, join = spec["name"], spec.get("segments", 4), spec.get("join", 0.12)
    isl = []
    for mn in spec["meshes"]:
        o = _obj(mn)
        for g in _islands(o): isl.append((o, g, [_wco(o, i) for i in g]))
    def gap(A, B):
        lo = lambda P, k: min(p[k] for p in P); hi = lambda P, k: max(p[k] for p in P)
        return math.sqrt(sum(max(0.0, lo(A, k) - hi(B, k), lo(B, k) - hi(A, k))**2 for k in range(3)))
    groups = []                                          # union islands into strips
    for it in isl:
        hit = [g for g in groups if any(gap(it[2], x[2]) < join for x in g)]
        merged = [it] + [x for g in hit for x in g]
        groups = [g for g in groups if g not in hit] + [merged]
    groups.sort(key=lambda g: (round(sum(p.z for x in g for p in x[2])/sum(len(x[2]) for x in g), 2),
                               sum(p.x for x in g for p in x[2])))
    out = []; chains = []
    for gi, g in enumerate(groups):
        votes = {}
        for o, idx, _ in g:
            for i in idx:
                for ge in o.data.vertices[i].groups:
                    n = o.vertex_groups[ge.group].name
                    if n in rig.data.bones and not n.startswith(name): votes[n] = votes.get(n, 0) + ge.weight
        anchor = spec.get("anchor") or max(votes, key=votes.get)
        b = rig.data.bones[anchor]; A0, A1 = rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local
        P = [p for _, _, pts in g for p in pts]
        root = min(P, key=lambda p: (_seg_closest(p, A0, A1)[0] - p).length)
        near = [p for p in P if (p - root).length < 0.05]; root = sum(near, Vector())/len(near)
        d = sorted(P, key=lambda p: (p - root).length); n = len(d)
        pts = [root] + [sum(d[int(n*k/K):max(int(n*(k + 1)/K), int(n*k/K) + 1)], Vector())/max(1, len(d[int(n*k/K):max(int(n*(k + 1)/K), int(n*k/K) + 1)])) for k in range(K)]
        pts[-1] = sum(d[-max(1, n//20):], Vector())/max(1, n//20)       # the tip: the farthest verts
        chains.append(([f"{name}_{gi:02d}_{k}" for k in range(1, K + 1)], pts, anchor))
    _add_bones(chains)
    for (bones, pts, anchor), g in zip(chains, groups):
        clear = set(spec.get("replace", [])) | {anchor}
        def s_of(p):
            best = None
            for k in range(K):
                c, t = _seg_closest(p, pts[k], pts[k + 1]); d = (p - c).length
                if best is None or d < best[0]: best = (d, k + t)
            return best[1]
        for o, idx, P in g:
            size = max(max(p[k] for p in P) - min(p[k] for p in P) for k in range(3))
            if size < spec.get("rigid_size", 0.15):
                w = _chain_weights(bones, s_of(sum(P, Vector())/len(P)), anchor, blend=0.2)
                for i in idx: _set_weights(o, i, w, clear)
            else:
                for i, p in zip(idx, P): _set_weights(o, i, _chain_weights(bones, s_of(p), anchor, blend=0.2), clear)
        out.append(dict(spec=spec, kind="strips", bones=bones, rest=pts, anchor=anchor, ring=False))
    return out

def build_cloth(specs):
    """Add the chain bones for every cloth spec and re-skin its meshes onto them. Call once, after the body."""
    for spec in specs:
        chains = _skirt(spec) if spec["kind"] == "skirt" else _strips(spec)
        cols = [(c, spec.get("radius", {}).get(c) or _bone_radius(c)) for c in spec.get("colliders", [])]
        for ch in chains:
            A = rig.data.bones[ch["anchor"]].matrix_local
            ch["local"] = [A.inverted() @ (rig.matrix_world.inverted() @ p) for p in ch["rest"]]   # anchor-bone space
            ch["len"] = [(ch["rest"][k + 1] - ch["rest"][k]).length for k in range(len(ch["bones"]))]
            ch["colliders"] = cols
            CLOTH_CHAINS.append(ch)
        print(f"CLOTH_CHAINS {spec['name']}: {len(chains)} chains x {len(chains[0]['bones'])} bones, colliders "
              + ", ".join(f"{c} r={r:.3f}" for c, r in cols))
    bpy.context.view_layer.update()

def _anchor_target(ch, M):
    return [M @ p for p in ch["local"]]

def cloth_bake(substeps=6, iters=4, loops=3, preroll=30, gravity=9.81, damping=0.12, margin=0.08):
    """Simulate every CLOTH_CHAINS chain over the rig's current action and key the chain bones (quaternion keys on every
       frame). Looping actions (anim_core _ACT['loop']) run `loops` cycles and keep the last, so the loop is seamless;
       one-shots pre-roll on frame 1 first so the cloth starts settled."""
    if not CLOTH_CHAINS: return
    sc = bpy.context.scene; f0, f1 = sc.frame_start, sc.frame_end; L = f1 - f0 + 1
    loop = bool(globals().get("_ACT", {}).get("loop", False))
    seq = ([f0 + (i % L) for i in range(L*loops)] if loop else [f0]*preroll + list(range(f0, f1 + 1)))
    keep_from = len(seq) - L
    RWm = rig.matrix_world; dt = 1.0/(sc.render.fps*substeps); g = Vector((0, 0, -gravity))*dt*dt
    def frame_state(f):
        sc.frame_set(f)
        A = {ch["anchor"]: RWm @ rig.pose.bones[ch["anchor"]].matrix for ch in CLOTH_CHAINS}
        C = {}
        for ch in CLOTH_CHAINS:
            for c, _ in ch["colliders"]:
                if c not in C:
                    pb = rig.pose.bones[c]; C[c] = (RWm @ pb.head, RWm @ pb.tail)
        return A, C
    X = [None]*len(CLOTH_CHAINS); Xp = [None]*len(CLOTH_CHAINS); rec = []
    A_prev, C_prev = frame_state(seq[0])
    for ci, ch in enumerate(CLOTH_CHAINS):
        X[ci] = [p.copy() for p in _anchor_target(ch, A_prev[ch["anchor"]])]; Xp[ci] = [p.copy() for p in X[ci]]
    for si, f in enumerate(seq):
        A_now, C_now = frame_state(f)
        for sub in range(1, substeps + 1):
            u = sub/substeps
            for ci, ch in enumerate(CLOTH_CHAINS):
                Ma = A_now[ch["anchor"]] if u >= 1 else _lerp_mat(A_prev[ch["anchor"]], A_now[ch["anchor"]], u)
                T = _anchor_target(ch, Ma); sp = ch["spec"]; K = len(ch["bones"])
                x, xp = X[ci], Xp[ci]
                for k in range(1, K + 1):                              # verlet + gravity
                    v = (x[k] - xp[k])*(1.0 - damping); xp[k] = x[k].copy(); x[k] = x[k] + v + g
                x[0] = T[0].copy(); xp[0] = T[0].copy()
                st0, st1 = sp.get("stiff_top", 0.35), sp.get("stiff_tip", 0.06)
                for k in range(1, K + 1):                              # pull toward the piece's own (animated) shape
                    s = st0 + (st1 - st0)*(k - 1)/max(1, K - 1)
                    x[k] = x[k].lerp(T[k], s/substeps*2)
            cols = [((C_prev[c][0].lerp(C_now[c][0], u), C_prev[c][1].lerp(C_now[c][1], u)), r) for c, r in
                    {c: r for ch in CLOTH_CHAINS for c, r in ch["colliders"]}.items()]
            for _ in range(iters):
                for ci, ch in enumerate(CLOTH_CHAINS):
                    x = X[ci]; K = len(ch["bones"]); Lk = ch["len"]
                    for k in range(K):                                 # segment lengths (root pinned)
                        d = x[k + 1] - x[k]; l = d.length or 1e-9; e = (l - Lk[k])/l
                        if k == 0: x[1] = x[1] - d*e
                        else: x[k] = x[k] + d*e*0.5; x[k + 1] = x[k + 1] - d*e*0.5
                    for (a, b), r in cols:                             # capsule collision, segments included
                        R = r + margin
                        for k in range(K):
                            c1, c2, s, t = _seg_seg(x[k], x[k + 1], a, b)
                            dv = c1 - c2; dl = dv.length
                            if dl < R:
                                n = dv/dl if dl > 1e-6 else Vector((0, -1, 0)); push = n*(R - dl)
                                if k == 0: x[1] = x[1] + push*(1.0 if s > 0 else 0.0)
                                else: x[k] = x[k] + push*(1 - s); x[k + 1] = x[k + 1] + push*s
                if any(ch["ring"] for ch in CLOTH_CHAINS):                    # skirt ring: neighbours keep their spacing
                    for spec_name in {ch["spec"]["name"] for ch in CLOTH_CHAINS if ch["ring"]}:
                        ring = [(ci, ch) for ci, ch in enumerate(CLOTH_CHAINS) if ch["ring"] and ch["spec"]["name"] == spec_name]
                        for (ia, ca), (ib, cb) in zip(ring, ring[1:] + ring[:1]):
                            for k in range(1, len(ca["bones"]) + 1):
                                r0 = (ca["rest"][k] - cb["rest"][k]).length; d = X[ib][k] - X[ia][k]; l = d.length or 1e-9
                                lo, hi = r0*0.8, r0*ca["spec"].get("ring_stretch", 1.15)
                                if l < lo or l > hi:
                                    e = (l - (lo if l < lo else hi))/l*0.5; X[ia][k] = X[ia][k] + d*e; X[ib][k] = X[ib][k] - d*e
        A_prev, C_prev = A_now, C_now
        if si >= keep_from: rec.append((f, [[p.copy() for p in x] for x in X]))
    _key_chains(rec)

def _lerp_mat(M0, M1, u):
    l0, r0, s0 = M0.decompose(); l1, r1, s1 = M1.decompose()
    return Matrix.LocRotScale(l0.lerp(l1, u), r0.slerp(r1, u), s0.lerp(s1, u))

def _key_chains(rec):
    """Key each chain bone so it points from its particle to the next (FK: head = parent's tail, length kept)."""
    sc = bpy.context.scene; Ri = rig.matrix_world.inverted(); P = rig.pose.bones; prevq = {}
    for f, X in rec:
        sc.frame_set(f)
        for ci, ch in enumerate(CLOTH_CHAINS):
            parent_pose = P[ch["anchor"]].matrix.copy(); parent_rest = rig.data.bones[ch["anchor"]].matrix_local
            head = Ri @ X[ci][0]
            for k, bn in enumerate(ch["bones"]):
                rest = rig.data.bones[bn].matrix_local
                free = parent_pose @ parent_rest.inverted() @ rest            # this bone with an identity basis
                want = (Ri @ X[ci][k + 1] - head).normalized()
                R = free.to_3x3().col[1].normalized().rotation_difference(want).to_matrix()
                M = Matrix.Translation(head) @ (R @ free.to_3x3()).to_4x4()
                basis = free.inverted() @ M
                q = basis.to_quaternion()
                if bn in prevq and prevq[bn].dot(q) < 0: q.negate()
                prevq[bn] = q
                pb = P[bn]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = (0, 0, 0)
                pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
                parent_pose, parent_rest = M, rest
                head = head + want*ch["len"][k]
    print(f"CLOTH_CHAINS baked {len(CLOTH_CHAINS)} chains over {len(rec)} frames")
