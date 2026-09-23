"""Sky Citadel scenario ARCHITECTURE -- one hook per scenario.

Executed by build_sky_citadel_scenarios.py into its namespace. Each hook
rebuilds a finished piece's architecture for its scenario -- its palette, its
silhouette (towers leaning, snapped, armoured, crowned by a nest; a tree or a
crystal spire through the deck; walls replaced by palisades, blast walls or
hedges; ice pouring off the rims) and its surface paint -- and places the few
props that ARE architecture (warships, forcefields, falling debris). It places
no dressing: the game scatters that at run time from the spawn points.

What each piece gets is drawn from its own random stream, so the same piece
differs between scenarios and two pieces of one scenario differ from each other.

The rules every hook keeps (the kit's validator checks them after):
  * the piece's box stays exactly 256^3: nothing above CROWN_TOP, nothing past
    the tile edge, nothing below -90, and the crown landmark is never touched;
  * the skyway / ascent decks and the walking line between openings are never
    built on;
  * whatever floats is registered and clears everything by the float rules;
    whatever hangs or stands is registered as a solid, so later floats clear it;
  * under 10,000 triangles.
"""


# ==========================================================================
# Tools for building on a finished piece
# ==========================================================================

def palette(p, mapping, fraction=1.0, rng=None, props=True):
    recolour(p, mapping, fraction=fraction, rng=rng, props_too=props)


def thin(ctx, labels, fraction):
    """Take away some of the base kit's own standing props -- lamps gone dark
    and removed, banners torn down, crates carried off -- so a scenario's piece
    is not the base piece with things added."""
    keep = []
    for prop in ctx.p.props:
        if prop["label"] in labels and ctx.rng.random() < fraction:
            continue
        keep.append(prop)
    ctx.p.props = keep


def floors(p, mat, only=None):
    """Recolour the walk surfaces: big upward faces between z -0.2 and 6.5."""
    for fi, f in enumerate(p.faces):
        n = face_normal(p, f)
        if n[2] < 0.9:
            continue
        zc = sum(p.verts[i].z for i in f) / len(f)
        if not (-0.2 < zc < 6.5):
            continue
        xs = [p.verts[i].x for i in f]
        ys = [p.verts[i].y for i in f]
        if (max(xs) - min(xs)) * (max(ys) - min(ys)) < 300:     # decks, not floor tiles
            continue
        if only is None or p.fmat[fi] in only:
            p.fmat[fi] = mat


def site(ctx, r, h=10.0, where=None, tries=80, label="structure", pad=1.0, keep_off=20.0):
    """A flat deck spot of radius r whose whole footprint is off the walking
    line and clear of every solid, float and standing prop. Registers it."""
    p = ctx.p
    if ctx.flat_only:
        return None
    feet = _footprints(p)
    for _ in range(tries):
        c = (where or ctx.uniform)()
        if c is None:
            return None
        x, y = c[0], c[1]
        if abs(x) > HALF - 6 - r or abs(y) > HALF - 6 - r:
            continue
        if in_corridor(p, x, y, half=keep_off + r, o=ctx.open):
            continue
        z0 = ctx.ground.flat(x, y, r, tol=0.25)
        if z0 is None:
            continue
        shape = ("cyl", x, y, r, z0, z0 + h)
        if any(shapes_clash(shape, s, gap=pad) for _, s in feet):
            continue
        p.solid(label, x, y, r, z0, z0 + h)
        return x, y, z0
    return None


def hang_ok(ctx, shape):
    """Something hanging off a deck (a frozen fall, keel crystals) must clear
    every float already there, and stay inside the piece's box."""
    x0, x1, y0, y1, z0, z1 = shape[1:]
    if min(x0, y0) < -HALF + 4 or max(x1, y1) > HALF - 4 or z0 < -90:
        return False
    return not any(shapes_clash(shape, s, gap=1.0) for _, s in ctx.p.floats)


def towers(ctx):
    """Every turret that may be changed: (x, y, r, H, top). Never one that
    carries the crown or a spire."""
    out = []
    sh = shells(ctx.p)
    for lab, s in ctx.p.solids:
        if lab != "tower" or s[0] != "cyl":
            continue
        _, x, y, R_, z0, z1 = s
        r = R_ / 1.25
        H = z1 - 6 - 2.4 * r
        near = [q for q in sh if math.hypot(q["c"].x - x, q["c"].y - y) < r * 1.3]
        if any(q["max"].z >= CROWN_TOP - 0.01 or q["max"].z > z1 + 1.0 for q in near):
            continue
        out.append((x, y, r, H, z1))
    ctx.rng.shuffle(out)
    return out


def tower_shells(ctx, x, y, r, above=-0.5):
    return [q for q in shells(ctx.p) if math.hypot(q["c"].x - x, q["c"].y - y) < r * 1.35 and q["min"].z >= above]


def rim_run(ctx, span):
    """Pick a run of parapet / railing along one deck edge, off the openings,
    and remove it. -> (ax, ay, bx, by, nx, ny) the line it stood on and the
    inward normal, or None."""
    p = ctx.p
    rim = []
    for s in shells(p):
        size = s["max"] - s["min"]
        if s["min"].z < -0.3 or s["max"].z > 6.5 or max(size.x, size.y) > 16:
            continue
        cx, cy = s["c"].x, s["c"].y
        if in_corridor(p, cx, cy, half=26, o=ctx.open) or max(abs(cx), abs(cy)) > HALF - 8:
            continue
        near = [(edge_near(q, cx, cy), q) for q in ctx.polys]
        if not near:
            continue
        (d, nrm), poly = min(near, key=lambda t: t[0][0])
        if d < 3.5:
            rim.append((s, nrm))
    if not rim:
        return None
    seed, nrm = ctx.rng.choice(rim)
    tx, ty = -nrm[1], nrm[0]
    sx, sy = seed["c"].x, seed["c"].y
    run = [(s, (s["c"].x - sx) * tx + (s["c"].y - sy) * ty) for s, n2 in rim
           if abs((s["c"].x - sx) * nrm[0] + (s["c"].y - sy) * nrm[1]) < 2.5 and n2 == nrm]
    run = [(s, t) for s, t in run if abs(t) <= span / 2]
    if len(run) < 2:
        return None
    t0, t1 = min(t for _, t in run), max(t for _, t in run)
    remove_faces(p, [fi for s, _ in run for fi in s["faces"]])
    ctx.refresh()
    ax, ay = sx + tx * t0, sy + ty * t0
    bx, by = sx + tx * t1, sy + ty * t1
    return ax, ay, bx, by, nrm[0], nrm[1]


def along(run, step):
    ax, ay, bx, by, nx, ny = run
    L = math.hypot(bx - ax, by - ay)
    k = max(1, int(L / step))
    for i in range(k + 1):
        t = i / k
        yield ax + (bx - ax) * t, ay + (by - ay) * t


def lean_group(ctx, group, cx, cy, deg, axis_deg, drop=0.0):
    """Tilt a set of shells about the horizontal axis through (cx, cy, 0)."""
    M = xf(cx, cy, -drop) @ xf(rz=axis_deg) @ xf(rx=deg) @ xf(rz=-axis_deg) @ xf(-cx, -cy, 0)
    moved = set()
    for s in group:
        for v in s["verts"]:
            if v not in moved:
                ctx.p.verts[v] = M @ ctx.p.verts[v]
                moved.add(v)
    return M


def crystal_spire(p, x, y, z, rng, tall, spread, n, mats=("AetherBloom", "Pearl", "SkyGlass"), down=False):
    """A formation of crystals erupting from one point (or hanging, if down)."""
    for k in range(n):
        a = rng.uniform(0, 2 * math.pi)
        d = 0 if k == 0 else rng.uniform(0.3, 1.0) * spread
        tilt = (d / max(spread, 0.1)) * rng.uniform(14, 34)
        h = tall * (1.0 if k == 0 else rng.uniform(0.3, 0.7))
        w = max(1.2, h * rng.uniform(0.14, 0.22))
        with frame(p, xf(x + math.cos(a) * d, y + math.sin(a) * d, z, math.degrees(a), 0, tilt * (-1 if down else 1))):
            if down:
                crystal(p, mats[k % len(mats)], 0, 0, 0, w, 0.01, h, n=5)
            else:
                crystal(p, mats[k % len(mats)], 0, 0, 0, w, h, 0.01, n=5)


# ==========================================================================
# UNMOORING -- the citadel is coming apart
# ==========================================================================

def s_unmooring(ctx):
    p, rng = ctx.p, ctx.rng
    loosen_islet(ctx)
    # a turret or two leaning as the deck under it gives
    for (x, y, r, H, z1) in towers(ctx)[: rng.randint(1, 2)]:
        group = tower_shells(ctx, x, y, r)
        if group and max(q["max"].z for q in group) < 120:
            lean_group(ctx, group, x, y, rng.uniform(6, 11), rng.uniform(0, 360))
    ctx.refresh()
    breach_walls(ctx, rng.randint(1, 3))
    # the deck has buckled: plates heaved up along fault lines, azure light in the gaps
    for _ in range(rng.randint(2, 4)):
        big = rng.random() < 0.5
        at = site(ctx, 11.0 if big else 7.5, 6.0, label="buckled plate")
        if at:
            x, y, z0 = at
            a = rng.uniform(0, 180)
            L, Wd = (18, 10) if big else (12, 7)
            tilt = rng.uniform(9, 16)
            with frame(p, xf(x, y, z0, a)):
                box(p, "CitadelWhite", 0, 0, math.sin(math.radians(tilt)) * Wd / 2 + 0.2, L, Wd, 1.4, rx=tilt)
                box(p, "PaleAlloy", 0, Wd / 2 - 0.4, math.sin(math.radians(tilt)) * Wd + 0.4, L, 0.8, 0.8, rx=tilt)
                box(p, "AzureNeon", 0, -Wd / 2 - 0.2, 0.1, L - 1, 0.6, 0.12)
                box(p, "AzureDim", 0, -Wd / 2 - 0.3, -0.4, L - 0.5, 0.4, 0.8)
                for k in range(3):
                    crystal(p, "AzureNeon", rng.uniform(-L / 2 + 1, L / 2 - 1), -Wd / 2 - 0.3, 0, 0.35,
                            rng.uniform(0.8, 1.8), 0.01, n=4)
    # a core breach: the anti-grav core showing through a broken ring of deck
    if role(p) in ("COMBAT", "BOSS", "SIDE") or rng.random() < 0.3:
        at = site(ctx, 7.5, 8.0, label="core breach")
        if at:
            x, y, z0 = at
            blot(p, "Soot", x, y, 6.5, "breach %s" % p.name, z=z0 + 0.03, h=0.08, n=11)
            blot(p, "AzureNeon", x, y, 3.2, "breach glow %s" % p.name, z=z0 + 0.1, h=0.06, n=9)
            for k in range(9):
                a = 40 * k + rng.uniform(-8, 8)
                with frame(p, xf(x + math.cos(math.radians(a)) * 5.2, y + math.sin(math.radians(a)) * 5.2, z0, a, 0,
                                 rng.uniform(15, 35))):
                    box(p, "CitadelWhite", 0, 0, 0.8, 2.6, 3.4, 1.2)
            crystal_spire(p, x, y, z0, rng, rng.uniform(5, 8), 2.2, 5, mats=("AzureNeon", "SkyGlass"))
    # dead seams, cracks, and the light leaking up through them
    for _ in range(rng.randint(3, 6)):
        surface_crack(ctx, rng.uniform(20, 38), w=1.3)
    for _ in range(rng.randint(2, 4)):
        surface_crack(ctx, rng.uniform(14, 26), w=0.7, mat="AzureNeon")
    # pieces of the keel falling away below the deck -- afloat on purpose
    for _ in range(rng.randint(2, 5)):
        for _t in range(40):
            x, y = rng.uniform(-100, 100), rng.uniform(-100, 100)
            z = rng.uniform(-60, -15)
            shape = ("cyl", x, y, 4.0, z - 3, z + 3)
            if not free_for_float(p, shape):
                continue
            if not ctx.polys or min(edge_dist(q, x, y) for q in ctx.polys) > 24:
                continue
            p.float_("span debris", x, y, 4.0, z - 3, z + 3)
            with frame(p, xf(x, y, z, rng.uniform(0, 90), rng.uniform(-30, 30), rng.uniform(-30, 30))):
                with as_prop(p, "span debris", I4):
                    lump(p, "HullSlate", [(0, -3), (2.6, -1.2), (3.2, 0.6), (1.6, 2.2), (0, 2.6)], n=6,
                         seed="falling %d" % rng.randrange(7), jitter=0.3)
            break
    for prop in p.props:
        if prop["label"] in ("floating crystal", "anti-grav pylon"):
            prop["matrix"] = prop["matrix"] @ xf(rx=rng.uniform(12, 28), ry=rng.uniform(-15, 15))
    topple(ctx, ("lamp", "light pillar", "crate"), 0.3)


# ==========================================================================
# SIEGE -- raiders dug into a burning citadel
# ==========================================================================

def palisade(p, run, rng):
    ax, ay, bx, by, nx, ny = run
    a = math.degrees(math.atan2(by - ay, bx - ax))
    for x, y in along(run, 1.7):
        h = rng.uniform(5.0, 7.0)
        with frame(p, xf(x + nx * 0.8, y + ny * 0.8, 0, a, rng.uniform(-10, -4), rng.uniform(-4, 4))):
            frustum(p, "Twig", 4, 0.5, 0.0, 0, h, rot=45)
    L = math.hypot(bx - ax, by - ay)
    for z in (1.4, 3.4):
        box(p, "Bark", (ax + bx) / 2 + nx * 1.4, (ay + by) / 2 + ny * 1.4, z, L + 1.2, 0.5, 0.5, rz=a)


def watchtower(p, x, y, z0, rng):
    H = rng.uniform(13, 19)
    a = rng.uniform(0, 90)
    with frame(p, xf(x, y, z0, a)):
        for sx in (-2.6, 2.6):
            for sy in (-2.6, 2.6):
                box(p, "Bark", sx, sy, H / 2, 0.7, 0.7, H)
        for z in (H * 0.35, H * 0.7):
            for s in (-1, 1):
                box(p, "Twig", 0, s * 2.6, z, 5.6, 0.3, 0.3, ry=s * 30)
                box(p, "Twig", s * 2.6, 0, z, 0.3, 5.6, 0.3, rx=s * 30)
        box(p, "Twig", 0, 0, H + 0.25, 7.2, 7.2, 0.5)
        for s in (-1, 1):
            box(p, "Twig", 0, s * 3.5, H + 1.2, 7.2, 0.3, 1.6)
            box(p, "Twig", s * 3.5, 0, H + 1.2, 0.3, 7.2, 1.6)
        for sx in (-3.4, 3.4):
            for sy in (-3.4, 3.4):
                box(p, "Bark", sx, sy, H + 2.8, 0.4, 0.4, 5.2)
        frustum(p, "RaiderRust", 4, 5.6, 0.0, H + 5.2, H + 8.6, 0, 0)
        box(p, "RaiderRust", 0, 0, H + 9.2, 0.2, 0.2, 2.2)
        box(p, "RaiderRust", 0, 1.0, H + 9.8, 0.1, 2.0, 1.2)
        for s in (-0.7, 0.7):                           # the ladder
            box(p, "Bark", s, -3.1, H / 2, 0.25, 0.25, H)
        for k in range(int(H / 1.4)):
            box(p, "Bark", 0, -3.1, 0.8 + k * 1.4, 1.6, 0.2, 0.2)


def s_siege(ctx):
    p, rng = ctx.p, ctx.rng
    breach_walls(ctx, rng.randint(1, 2))
    for _ in range(rng.randint(1, 2)):
        run = rim_run(ctx, rng.uniform(22, 46))
        if run:
            palisade(p, run, rng)
    if rng.random() < 0.6:
        crumble_tower(ctx)
    for (x, y, r, H, z1) in towers(ctx)[: rng.randint(1, 3)]:
        # rust plates bolted over the white, raider banners down the walls
        for k in range(rng.randint(3, 6)):
            a = rng.uniform(0, 2 * math.pi)
            z = rng.uniform(4, H * 0.85)
            box(p, "RaiderRust", x + math.cos(a) * (r * 0.97 + 0.15), y + math.sin(a) * (r * 0.97 + 0.15), z,
                0.35, rng.uniform(3, 5), rng.uniform(3, 6), rz=math.degrees(a), ry=rng.uniform(-6, 6))
        a = rng.uniform(0, 2 * math.pi)
        L = min(H - 4, rng.uniform(9, 16))
        box(p, "RaiderRust", x + math.cos(a) * (r * 1.2 + 0.25), y + math.sin(a) * (r * 1.2 + 0.25), H + 1 - L / 2,
            0.2, 3.2, L, rz=math.degrees(a))
    for _ in range(rng.randint(0, 2) if role(p) in ("COMBAT", "BOSS") else rng.randint(0, 1)):
        at = site(ctx, 6.0, 30.0, label="watchtower")
        if at:
            watchtower(p, at[0], at[1], at[2], rng)
    for _ in range(rng.randint(3, 6)):
        surface_blot(ctx, "Char", rng.uniform(1.8, 3.6), sx=rng.uniform(1.0, 1.5), n=11, jitter=0.5)
    if role(p) in ("COMBAT", "PATH", "BOSS", "ENTRY"):
        warship(ctx, n=2 if role(p) == "COMBAT" and rng.random() < 0.35 else 1)
    topple(ctx, ("banner", "lamp", "crate"), 0.35)


# ==========================================================================
# LOCKDOWN -- the citadel has armoured itself against everyone
# ==========================================================================

def blast_wall(p, run):
    ax, ay, bx, by, nx, ny = run
    a = math.degrees(math.atan2(by - ay, bx - ax))
    L = math.hypot(bx - ax, by - ay) + 2.0
    cx, cy = (ax + bx) / 2 + nx * 0.6, (ay + by) / 2 + ny * 0.6
    box(p, "Steel", cx, cy, 2.9, L, 1.4, 5.8, rz=a)
    box(p, "Hazard", cx + nx * 0.72, cy + ny * 0.72, 1.2, L, 0.06, 0.6, rz=a)
    box(p, "AlarmRed", cx, cy, 5.9, L - 0.6, 0.4, 0.2, rz=a)
    k = max(1, int(L / 8))
    for i in range(k + 1):
        t = i / k - 0.5
        box(p, "Gunmetal", cx + math.cos(math.radians(a)) * L * t, cy + math.sin(math.radians(a)) * L * t, 3.1,
            1.2, 2.0, 6.2, rz=a)


def s_lockdown(ctx):
    p, rng = ctx.p, ctx.rng
    forcefields(ctx)
    for _ in range(rng.randint(1, 3)):
        run = rim_run(ctx, rng.uniform(20, 44))
        if run:
            blast_wall(p, run)
    for (x, y, r, H, z1) in towers(ctx)[: rng.randint(1, 4)]:
        # an armoured sleeve over the lower shaft, red band at its top
        top = H * rng.uniform(0.45, 0.7)
        frustum(p, "Gunmetal", 8, r * 1.12, r * 1.06, 0.2, top, x, y)
        frustum(p, "AlarmRed", 8, r * 1.1, r * 1.1, top - 0.8, top - 0.3, x, y)
        for k in range(4):
            a = math.radians(45 + 90 * k)
            box(p, "Hazard", x + math.cos(a) * r * 1.1, y + math.sin(a) * r * 1.1, top * 0.5, 0.2, 1.2, top * 0.9,
                rz=math.degrees(a))
    for _ in range(rng.randint(0, 2)):
        at = site(ctx, 2.6, 30.0, label="sensor mast")
        if at:
            x, y, z0 = at
            h = rng.uniform(16, 26)
            frustum(p, "Gunmetal", 6, 1.8, 1.4, z0, z0 + 1.2, x, y)
            frustum(p, "Steel", 6, 0.45, 0.3, z0 + 1.2, z0 + h, x, y)
            with frame(p, xf(x, y, z0 + h - 2, rng.uniform(0, 360), 0, 35)):
                frustum(p, "Steel", 8, 2.6, 0.6, 0, 1.2)
            crystal(p, "AlarmRed", x, y, z0 + h + 0.8, 0.5, 0.9, 0.5, n=4)
    # warning chevrons painted toward every opening
    for d in ctx.open:
        for k in range(3):
            mx, my, turn = mouth(d, inset=40 + 9 * k)
            if ctx.ground.flat(mx, my, 6.0, tol=0.2) is None:
                continue
            for sd in (-1, 1):
                box(p, "Hazard", mx + (sd * 3.5 if turn == 0 else 0), my + (sd * 3.5 if turn else 0), 0.07,
                    8, 1.0, 0.06, rz=turn + sd * 30)


# ==========================================================================
# STORMHAWK -- storm-battered heights where a great raptor hunts
# ==========================================================================

def snap_spire(ctx):
    """Break a (non-crown) spire off partway up: its halos gone with it."""
    p, rng = ctx.p, ctx.rng
    spires = [s for lab, s in p.solids if lab == "spire" and s[0] == "cyl" and s[5] < CROWN_TOP - 0.01]
    rng.shuffle(spires)
    for (_, x, y, R_, z0, z1) in spires:
        cut = z0 + (z1 - z0) * rng.uniform(0.35, 0.6)
        group = [q for q in shells(p) if math.hypot(q["c"].x - x, q["c"].y - y) < R_ and q["max"].z > cut]
        if not group:
            continue
        drop = []
        for q in group:
            if q["min"].z > cut:
                drop += q["faces"]
            else:
                for v in q["verts"]:
                    if p.verts[v].z > cut:
                        p.verts[v] = Vector((p.verts[v].x, p.verts[v].y, cut))
        remove_faces(p, drop)
        p.props = [q for q in p.props if not (math.hypot(q["matrix"].translation.x - x, q["matrix"].translation.y - y) < R_
                                                  and q["matrix"].translation.z > cut)]
        for k in range(7):
            a = math.radians(360 / 7 * k + rng.uniform(-10, 10))
            crystal(p, "StormStone", x + math.cos(a) * R_ * 0.25, y + math.sin(a) * R_ * 0.25, cut, R_ * 0.18,
                    rng.uniform(1.0, 4.0), 0.01, n=4)
        ctx.refresh()
        return True
    return False


def crown_nest(ctx):
    """Replace a turret's roof with the stormhawk's nest."""
    p, rng = ctx.p, ctx.rng
    for (x, y, r, H, z1) in towers(ctx):
        roof = [q for q in tower_shells(ctx, x, y, r, above=H + 2.5)]
        if not roof:
            continue
        remove_faces(p, [fi for q in roof for fi in q["faces"]])
        R_ = r * 1.5
        z = H + 3.0
        for k in range(26):
            a = 360 / 26 * k + rng.uniform(-5, 5)
            box(p, "Twig", x + math.cos(math.radians(a)) * R_, y + math.sin(math.radians(a)) * R_, z + (k % 3) * 0.5,
                R_ * 0.9, 0.7, 0.7, rz=a + 90 + rng.uniform(-18, 18), rx=rng.uniform(-14, 14))
        for k in range(16):
            a = 360 / 16 * k + 11
            box(p, "Bark", x + math.cos(math.radians(a)) * (R_ + 1.2), y + math.sin(math.radians(a)) * (R_ + 1.2),
                z - 0.8, R_ * 0.8, 0.6, 0.6, rz=a + 70, rx=18)
        frustum(p, "Twig", 10, R_ - 1.5, R_ + 0.4, z - 0.6, z + 0.8, x, y)
        for k in range(3):
            a = math.radians(120 * k + 30)
            lump(p, "Bone", [(1.0, z + 0.8), (1.25, z + 1.8), (0.8, z + 2.9), (0, z + 3.3)], n=7,
                 seed="crown egg %d" % k, jitter=0.05, cx=x + math.cos(a) * 2.0, cy=y + math.sin(a) * 2.0)
        add_anchor(p, "EVENT", x, y, z, "the stormhawk's nest crowns this turret: it dives from here")
        ctx.refresh()
        return True
    return False


def s_stormhawk(ctx):
    p, rng = ctx.p, ctx.rng
    snap_spire(ctx)
    if rng.random() < 0.3:
        snap_spire(ctx)
    if role(p) in ("COMBAT", "BOSS", "SIDE") or rng.random() < 0.35:
        crown_nest(ctx)
    for (x, y, r, H, z1) in towers(ctx)[: rng.randint(1, 3)]:
        # claw rakes down the shaft
        a = rng.uniform(0, 2 * math.pi)
        z = rng.uniform(8, max(9, H * 0.7))
        for k in (-1, 0, 1):
            b = a + k * 0.16
            box(p, "Soot", x + math.cos(b) * (r * 0.97 + 0.1), y + math.sin(b) * (r * 0.97 + 0.1), z - k * 0.8,
                0.25, 0.7, rng.uniform(6, 10), rz=math.degrees(b), rx=rng.uniform(18, 26))
        if rng.random() < 0.5 and H + 16 < CROWN_TOP - 10:
            frustum(p, "SunGold", 5, 0.35, 0.1, H + 3, H + rng.uniform(10, 15), x + r * 0.6, y)
            torus(p, "AzureNeon", 0.8, 0.12, x + r * 0.6, y, H + 8, n=8)
    for _ in range(rng.randint(2, 4)):
        surface_crack(ctx, rng.uniform(16, 30), w=0.8, mat="AzureNeon")
    for _ in range(rng.randint(2, 4)):          # claw gouges across the deck
        for _t in range(40):
            c = ctx.uniform()
            if c is None or ctx.clear(c[0], c[1], 7.0, corridor=False) is None:
                continue
            a = rng.uniform(0, 180)
            for k in (-1, 0, 1):
                ox, oy = -math.sin(math.radians(a)) * k * 1.6, math.cos(math.radians(a)) * k * 1.6
                box(p, "Soot", c[0] + ox, c[1] + oy, 0.07, 11 - abs(k) * 2, 0.7, 0.06, rz=a)
            break
    topple(ctx, ("lamp", "light pillar", "banner"), 0.4)


# ==========================================================================
# RIME -- frozen solid at altitude
# ==========================================================================

def frozen_fall(ctx):
    """Ice pouring off a deck edge and frozen mid-fall, far down the keel."""
    p, rng = ctx.p, ctx.rng
    for _ in range(40):
        c = ctx.uniform()
        if c is None:
            return False
        poly = min(ctx.polys, key=lambda q: edge_dist(q, c[0], c[1]))
        d, (nx, ny) = edge_near(poly, c[0], c[1])
        ex, ey = c[0] - nx * d, c[1] - ny * d       # on the edge
        if in_corridor(p, ex, ey, half=28, o=ctx.open):
            continue
        L = rng.uniform(18, 40)
        w = rng.uniform(6, 11)
        shape = ("box", ex - w, ex + w, ey - w, ey + w, -L - 4, 1)
        if not hang_ok(ctx, shape):
            continue
        tx, ty = -ny, nx
        # an ice sheet down the rim, and a curtain of long icicles in front of it
        a = math.degrees(math.atan2(ny, nx))
        with frame(p, xf(ex - nx * 0.8, ey - ny * 0.8, -DECK_T - L * 0.22, a)):
            lump(p, "Ice", [(0.01, -L * 0.25), (1.0, -L * 0.05), (1.0, L * 0.15), (0.01, L * 0.22)], n=6,
                 seed="sheet %s" % p.name, jitter=0.15, sx=1.3, sy=w * 0.9)
        k = int(w * 1.4)
        for i in range(k):
            t = (i + 0.5) / k * 2 - 1
            reach = L * (1.0 - 0.6 * abs(t)) * rng.uniform(0.6, 1.0)
            cx = ex - nx * (1.5 + rng.uniform(0, 1.5)) + tx * t * w
            cy = ey - ny * (1.5 + rng.uniform(0, 1.5)) + ty * t * w
            crystal(p, "Ice" if i % 3 else "SkyGlass", cx, cy, -DECK_T + 0.5, rng.uniform(0.8, 1.6), 0.5, reach, n=5,
                    rz=rng.uniform(0, 72))
        p.solid("frozen fall", ex, ey, w, -L - 4, 1)
        return True
    return False


def icicle_ring(p, x, y, R_, z, rng, n=16):
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.1, 0.1)
        crystal(p, "Ice", x + math.cos(a) * R_, y + math.sin(a) * R_, z, rng.uniform(0.25, 0.5), 0.01,
                rng.uniform(1.5, 6.5), n=4)


def s_rime(ctx):
    p, rng = ctx.p, ctx.rng
    for (x, y, r, H, z1) in towers(ctx):
        icicle_ring(p, x, y, r * 1.2, H + 2.0, rng, n=int(10 + r * 1.5))
    for _ in range(rng.randint(1, 3) if role(p) != "SIDE" else rng.randint(0, 1)):
        frozen_fall(ctx)
    for _ in range(rng.randint(1, 3)):
        at = site(ctx, 4.0, 45.0, label="ice pillar")
        if at:
            crystal_spire(p, at[0], at[1], at[2], rng, rng.uniform(14, 36), 3.2, rng.randint(3, 6),
                          mats=("Ice", "SkyGlass", "Snow"))
    for _ in range(rng.randint(1, 3)):          # snow banked up against the walls
        c = None
        for _t in range(40):
            c = ctx.uniform()
            if c is None:
                break
            poly = min(ctx.polys, key=lambda q: edge_dist(q, c[0], c[1]))
            d, (nx, ny) = edge_near(poly, c[0], c[1])
            ex, ey = c[0] - nx * (d - 3.2), c[1] - ny * (d - 3.2)
            if ctx.clear(ex, ey, 3.0, corridor=True) is None:
                continue
            a = math.degrees(math.atan2(ny, nx)) + 90
            L = rng.uniform(10, 20)
            if any(shapes_clash(("cyl", ex, ey, L / 2, -1, 4), s, gap=1.0) for _, s in p.floats + p.solids):
                continue
            with frame(p, xf(ex, ey, 0, a)):
                lump(p, "Snow", [(3.0, 0), (2.6, 1.4), (1.4, 2.6), (0, 3.0)], n=8, seed="bank %s %.0f" % (p.name, ex),
                     jitter=0.2, sx=L / 6)
            p.solid("snow bank", ex, ey, L / 2, 0, 3)
            break
    for poly in ctx.polys:                      # icicles along the deck rims
        n = len(poly)
        cx, cy = sum(q[0] for q in poly) / n, sum(q[1] for q in poly) / n
        for _ in range(max(6, 2 * n)):
            i = rng.randrange(n)
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            t = rng.uniform(0.1, 0.9)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            x, y = x + (cx - x) * 0.02, y + (cy - y) * 0.02
            crystal(p, "Ice", x, y, -DECK_T + 0.05, rng.uniform(0.4, 0.8), 0.01, rng.uniform(2.5, 8), n=4)


# ==========================================================================
# RECLAIMED -- the green took the citadel back
# ==========================================================================

def great_tree(ctx):
    p, rng = ctx.p, ctx.rng
    H = rng.uniform(26, 42)
    R_ = rng.uniform(13, 18)
    canopy_clear = lambda x, y, z0: not any(
        shapes_clash(("cyl", x, y, R_ + 10, z0 + H * 0.7, z0 + H + 14), s, gap=1.0) for _, s in p.floats + p.solids)
    at = None
    for _ in range(6):      # the whole crown must clear everything afloat and standing
        c = site(ctx, 6.0, 12.0, label="great tree", tries=60)
        if c and canopy_clear(*c) and abs(c[0]) + R_ + 10 < HALF - 4 and abs(c[1]) + R_ + 10 < HALF - 4:
            at = c
            break
    if not at:
        return False
    x, y, z0 = at
    frustum(p, "Bark", 7, 5.2, 3.4, z0, z0 + 2.5, x, y)        # the flare at its foot
    frustum(p, "Bark", 7, 3.4, 2.4, z0 + 2.5, z0 + H * 0.7, x, y)
    frustum(p, "Bark", 7, 2.4, 1.1, z0 + H * 0.7, z0 + H, x, y)
    for k in range(rng.randint(3, 5)):          # boughs
        a = rng.uniform(0, 360)
        with frame(p, xf(x, y, z0 + H * rng.uniform(0.5, 0.8), a, 0, rng.uniform(40, 65))):
            frustum(p, "Bark", 5, 1.0, 0.4, 0, rng.uniform(7, 11))
    for k in range(rng.randint(9, 13)):         # the canopy: layered lobes, broad and low
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.2, 1.0) * R_ * 0.7
        rr = rng.uniform(6.0, 9.5)
        lump(p, ("Verdure", "Moss", "MossLight")[k % 3], [(rr * 0.6, 0), (rr, rr * 0.5), (rr * 0.85, rr * 1.0),
                                                          (0, rr * 1.3)],
             n=8, seed="canopy %s %d" % (p.name, k), jitter=0.25, cx=x + math.cos(a) * d, cy=y + math.sin(a) * d,
             cz=z0 + H * 0.72 + rng.uniform(0, H * 0.25))
    for k in range(rng.randint(5, 8)):          # roots across the deck, over the edge if it is near
        a = rng.uniform(0, 2 * math.pi)
        px, py = x, y
        for j in range(4):
            L = rng.uniform(3, 5)
            nx, ny = px + math.cos(a) * L, py + math.sin(a) * L
            if in_corridor(p, nx, ny, half=19, o=ctx.open) or ctx.ground.flat(nx, ny, 0.8, tol=0.5) is None:
                break
            box(p, "Bark", (px + nx) / 2, (py + ny) / 2, z0 + 0.35, L + 0.5, 1.4 - 0.25 * j, 0.8,
                rz=math.degrees(a))
            px, py = nx, ny
            a += rng.uniform(-0.5, 0.5)
    p.solid("tree canopy", x, y, R_ + 10, z0 + H * 0.7, z0 + H + 14)
    return True


def keel_roots(ctx, n):
    """Roots gripping the island from below: down the keel, into the air."""
    p, rng = ctx.p, ctx.rng
    for _ in range(n):
        for _t in range(30):
            c = ctx.uniform()
            if c is None:
                return
            poly = min(ctx.polys, key=lambda q: edge_dist(q, c[0], c[1]))
            d, (nx, ny) = edge_near(poly, c[0], c[1])
            ex, ey = c[0] - nx * d, c[1] - ny * d
            if in_corridor(p, ex, ey, half=26, o=ctx.open):
                continue
            L = rng.uniform(14, 34)
            shape = ("box", ex - 5, ex + 5, ey - 5, ey + 5, -L - 3, 0)
            if not hang_ok(ctx, shape):
                continue
            z = -DECK_T
            x, y = ex + nx * 1.2, ey + ny * 1.2
            for j in range(5):
                seg = L / 5
                nxp = x + nx * rng.uniform(0.5, 2.5) + rng.uniform(-1.5, 1.5)
                nyp = y + ny * rng.uniform(0.5, 2.5) + rng.uniform(-1.5, 1.5)
                with frame(p, xf((x + nxp) / 2, (y + nyp) / 2, z - seg / 2)):
                    frustum(p, "Bark", 5, 1.2 - 0.18 * j, 1.0 - 0.18 * j, -seg / 2 - 0.3, seg / 2 + 0.3)
                x, y, z = nxp, nyp, z - seg
            p.solid("keel root", ex, ey, 5, -L - 3, 0)
            break


def s_reclaimed(ctx):
    p, rng = ctx.p, ctx.rng
    if rng.random() < 0.7:
        crumble_tower(ctx, cut=rng.uniform(0.35, 0.7))
    if rng.random() < 0.3:
        crumble_tower(ctx, cut=rng.uniform(0.35, 0.7))
    for _ in range(rng.randint(0, 2)):
        run = rim_run(ctx, rng.uniform(16, 36))
        if run:
            ax, ay, bx, by, nx, ny = run
            a = math.degrees(math.atan2(by - ay, bx - ax))
            for x, y in along(run, 3.0):
                lump(p, rng.choice(("Moss", "Verdure")), [(1.8, 0), (2.0, 1.4), (1.4, 2.6), (0, 3.0)], n=6,
                     seed="hedge %.1f %.1f" % (x, y), jitter=0.3, cx=x + nx * 1.2, cy=y + ny * 1.2)
    if role(p) in ("COMBAT", "BOSS", "SIDE") or rng.random() < 0.4:
        great_tree(ctx)
    keel_roots(ctx, rng.randint(1, 3))
    for poly in ctx.polys:
        K["vines"](p, poly, "reclaimed %s %d" % (p.name, len(poly)), count=max(8, 2 * len(poly)))
    for _ in range(rng.randint(6, 12)):         # moss carpets at the foot of the walls
        c = None
        for _t in range(30):
            c = ctx.uniform()
            if c is None:
                break
            poly = min(ctx.polys, key=lambda q: edge_dist(q, c[0], c[1]))
            d, (nx, ny) = edge_near(poly, c[0], c[1])
            if d > 9:
                continue
            ex, ey = c[0] - nx * (d - 3.5), c[1] - ny * (d - 3.5)
            if ctx.clear(ex, ey, 3.0, corridor=False) is None:
                continue
            blot(p, rng.choice(("Moss", "MossLight")), ex, ey, rng.uniform(2.5, 4.5), "carpet %.1f %.1f" % (ex, ey),
                 sx=rng.uniform(1.6, 2.6), rz=math.degrees(math.atan2(ny, nx)) + 90)
            break
    for _ in range(rng.randint(2, 4)):
        surface_crack(ctx, rng.uniform(14, 26))
    topple(ctx, ("lamp", "banner", "light pillar"), 0.35)


# ==========================================================================
# AETHER SURGE -- crystal erupting through the citadel
# ==========================================================================

def s_aether_surge(ctx):
    p, rng = ctx.p, ctx.rng
    # the eruption: one to three formations through the deck, veins glowing out from each
    for _ in range(rng.randint(1, 3) if role(p) not in ("PATH",) else rng.randint(0, 2)):
        tall = rng.uniform(20, 58)
        at = site(ctx, 7.0, tall + 4, label="crystal eruption", tries=100)
        if not at:
            continue
        x, y, z0 = at
        crystal_spire(p, x, y, z0, rng, tall, 5.5, rng.randint(7, 11))
        for k in range(rng.randint(4, 7)):
            a = math.radians(rng.uniform(0, 360))
            L = rng.uniform(12, 30)
            mx, my = x + math.cos(a) * (6 + L / 2), y + math.sin(a) * (6 + L / 2)
            if ctx.clear(mx, my, L * 0.5, corridor=False) is not None:
                box(p, "AetherDim", mx, my, 0.07, L, 0.9, 0.06, rz=math.degrees(a))
    # crystal growing out of the turrets
    for (x, y, r, H, z1) in towers(ctx)[: rng.randint(1, 3)]:
        for k in range(rng.randint(3, 6)):
            a = rng.uniform(0, 360)
            z = rng.uniform(6, H * 0.9)
            with frame(p, xf(x + math.cos(math.radians(a)) * r * 0.8, y + math.sin(math.radians(a)) * r * 0.8, z,
                             a, 0, rng.uniform(40, 70))):
                crystal(p, rng.choice(("AetherBloom", "Pearl", "SkyGlass")), 0, 0, 0, rng.uniform(0.8, 1.6),
                        rng.uniform(4, 9), 0.5, n=5)
    # and hanging under the islands
    for _ in range(rng.randint(1, 3)):
        c = ctx.uniform()
        if c is None:
            break
        g = ctx.ground.z_at(c[0], c[1])
        if g is None:
            continue
        hit = ctx.ground.bvh.ray_cast(Vector((c[0], c[1], -DECK_T - 0.2)), Vector((0, 0, -1)), 90.0)
        zb = hit[0].z if hit[0] is not None else -DECK_T
        tall = rng.uniform(10, 26)
        shape = ("box", c[0] - 6, c[0] + 6, c[1] - 6, c[1] + 6, zb - tall - 2, zb + 1)
        if not hang_ok(ctx, shape):
            continue
        crystal_spire(p, c[0], c[1], zb + 0.5, rng, tall, 3.0, rng.randint(3, 6), down=True)
        p.solid("keel crystal", c[0], c[1], 6, zb - tall - 2, zb + 1)
    # crystal rocks adrift round the piece, on purpose
    for _ in range(rng.randint(1, 3)):
        for _t in range(40):
            x, y = rng.uniform(-110, 110), rng.uniform(-110, 110)
            z = rng.uniform(8, 40)
            if not free_for_float(p, ("cyl", x, y, 4.0, z - 5, z + 5)):
                continue
            if not ctx.polys or min(edge_dist(q, x, y) for q in ctx.polys) > 30:
                continue
            K["float_crystal"](p, "AetherBloom", x, y, z, 2.6, 4.5, 4.0)
            break


# ==========================================================================
# LOOKS -- each scenario's palette and surfaces, applied AFTER all structure,
# so what a hook added (rubble, a fallen roof, rim shards) takes the scenario's
# colours too.
# ==========================================================================

def l_unmooring(ctx):
    thin(ctx, ("lamp", "light pillar", "crate", "banner"), 0.3)
    ctx.p.beacon_drop = 0.35                             # beacons drifted off their moorings
    thin(ctx, ("floating crystal",), 0.2)
    palette(ctx.p, {"AzureDim": "DeepAlloy", "AzureNeon": "DeepAlloy"}, 0.55, ctx.rng, props=False)
    palette(ctx.p, {"CitadelViolet": "StormSlate"}, props=True)


def l_siege(ctx):
    p = ctx.p
    thin(ctx, ("lamp", "light pillar", "banner", "holo pedestal", "telescope"), 0.4)
    ctx.p.beacon_drop = 0.55                             # beacons shot down by the raiders
    thin(ctx, ("floating crystal",), 0.55)
    palette(p, {"CitadelViolet": "RaiderRust", "AzureDim": "Char", "AzureNeon": "EmberGlow"}, props=True)
    floors(p, "Scorched", only=("CitadelWhite", "PaleAlloy"))


def l_lockdown(ctx):
    p = ctx.p
    thin(ctx, ("banner", "crate", "brazier"), 0.5)
    thin(ctx, ("floating crystal", "floating tome"), 0.5)    # cleared for the turrets' sightlines
    palette(p, {"CitadelWhite": "Gunmetal", "PaleAlloy": "Steel", "CitadelViolet": "Gunmetal", "SunGold": "Hazard",
                "AzureNeon": "AlarmRed", "AzureDim": "AlarmDim", "Verdure": "Gunmetal"}, props=True)
    floors(p, "Plating", only=("Gunmetal",))


def l_stormhawk(ctx):
    p = ctx.p
    thin(ctx, ("lamp", "banner", "crate", "telescope"), 0.3)
    ctx.p.beacon_drop = 0.5                              # the hawk strikes anything that glows
    thin(ctx, ("floating crystal",), 0.3)
    palette(p, {"CitadelWhite": "StormStone", "PaleAlloy": "StormSlate", "CitadelViolet": "DeepAlloy"}, props=True)
    floors(p, "StormSlate", only=("StormStone",))


def l_rime(ctx):
    p, rng = ctx.p, ctx.rng
    ctx.p.beacon_drop = 0.3                              # iced over and fallen
    thin(ctx, ("floating tome",), 0.3)
    palette(p, {"CitadelWhite": "Frost", "PaleAlloy": "FrostDeep", "Verdure": "Snow", "AzureDim": "Ice",
                "SkyGlass": "Ice"}, props=False)
    palette(p, {"CitadelViolet": "Snow"}, 0.5, rng, props=False)
    for fi, _si in tops(p):
        if p.fmat[fi] not in ("Ice",):
            p.fmat[fi] = "Snow"
    floors(p, "Snow", only=("Frost",))


def l_reclaimed(ctx):
    p, rng = ctx.p, ctx.rng
    thin(ctx, ("lamp", "light pillar", "banner", "crate", "container", "holo pedestal", "brazier"), 0.45)
    ctx.p.beacon_drop = 0.65                             # long since fallen
    thin(ctx, ("floating crystal", "floating tome", "drifting lintel"), 0.6)
    palette(p, {"CitadelWhite": "Weathered", "PaleAlloy": "Lichen", "CitadelViolet": "HullSlate",
                "AzureNeon": "DeepAlloy", "AzureDim": "HullSlate", "SunGold": "Lichen"}, props=True)
    floors(p, "Weathered")
    by_shell = {}
    for fi, si in tops(p):
        by_shell.setdefault(si, []).append(fi)
    for fl in by_shell.values():
        if rng.random() < 0.55 and not any(p.fmat[fi] in ("Verdure", "Moss", "MossLight", "Bark") for fi in fl):
            m = rng.choice(("Moss", "MossLight"))
            for fi in fl:
                p.fmat[fi] = m


def l_aether_surge(ctx):
    p = ctx.p
    p.beacon_drop = 0.3                                  # burnt out by the surge
    palette(p, {"CitadelWhite": "Pearl", "PaleAlloy": "Lavender", "AzureNeon": "AetherBloom",
                "AzureDim": "AetherDim", "DeepAlloy": "HullSlate"}, props=True)
    floors(p, "Pearl")


LOOKS = {
    "unmooring": l_unmooring, "siege": l_siege, "lockdown": l_lockdown, "stormhawk": l_stormhawk,
    "rime": l_rime, "reclaimed": l_reclaimed, "aether_surge": l_aether_surge,
}

STRUCTURES.update({
    "unmooring": s_unmooring, "siege": s_siege, "lockdown": s_lockdown, "stormhawk": s_stormhawk,
    "rime": s_rime, "reclaimed": s_reclaimed, "aether_surge": s_aether_surge,
})
