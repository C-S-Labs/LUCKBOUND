# Ethereal Scape -- a Python mirror of ChunkCore.assemble's §7.7 universal generation, used ONLY to lay out a
# whole example map in the review .blend (the game's assembler is the Luau one; tests/cases.luau checks it).
# Game frame throughout: X east, Y up, Z south; yaw in degrees, clockwise from above (north -> east at 90).
import random

GAME_SOCKET = {"N": (0, -1, 0), "S": (0, 1, 180), "E": (1, 0, 90), "W": (-1, 0, 270)}


def norm(d):
    return d % 360


def rotate(x, z, yaw):
    return {0: (x, z), 90: (-z, x), 180: (-x, -z), 270: (z, -x)}[yaw]


def sockets_of(spec):
    H = spec["half"]
    out = []
    for card, kind in spec["sockets"]:
        gx, gz, facing = GAME_SOCKET[card]
        out.append(dict(id=card, kind=kind, x=gx * H, y=spec.get("lift", {}).get(card, 0), z=gz * H, facing=facing))
    return out


def world_socket(pl, spec, s):
    ox, oz = rotate(s["x"], s["z"], pl["yaw"])
    return dict(kind=s["kind"], x=pl["x"] + ox, y=pl["y"] + s["y"], z=pl["z"] + oz, facing=norm(s["facing"] + pl["yaw"]))


def place_against(spec, open_s):
    want = norm(open_s["facing"] + 180)
    for s in sockets_of(spec):
        if s["kind"] == open_s["kind"]:
            yaw = norm(want - s["facing"])
            ox, oz = rotate(s["x"], s["z"], yaw)
            return dict(id=spec["id"], role=spec["role"], x=open_s["x"] - ox, y=open_s["y"] - s["y"],
                        z=open_s["z"] - oz, yaw=yaw), s
    return None, None


def extent(pl, spec):
    return spec["half"], spec["half"]


def overlaps(a, sa, b, sb):
    ax, az = extent(a, sa)
    bx, bz = extent(b, sb)
    return abs(a["x"] - b["x"]) < ax + bx - 1 and abs(a["z"] - b["z"]) < az + bz - 1


def assemble(specs, path_length, gen, seed):
    rng = random.Random(seed)
    by = {}
    for s in specs:
        by.setdefault(s["role"], []).append(s)
    lib = {s["id"]: s for s in specs}
    middle = by["PATH"] + by["COMBAT"]
    placed, used, spent = [], {}, []
    boss_kinds = {k for b in by["BOSS"] for _c, k in b["sockets"]}

    def allowed(s):
        n = used.get(s["id"], 0)
        return (s.get("max") is None or n < s["max"]) and (s["role"] == "CAP" or n < 2)

    def collides(p, s):
        return any(overlaps(p, s, o, lib[o["id"]]) for o in placed)

    def record(p, s, arrived=None):
        placed.append(p)
        spent.append({arrived} if arrived else set())
        used[s["id"]] = used.get(s["id"], 0) + 1

    def pick(pool):
        tot = sum(s["weight"] for s in pool)
        r = rng.random() * tot
        for s in pool:
            r -= s["weight"]
            if r <= 0:
                return s
        return pool[-1]

    entry = by["ENTRY"][0]
    record(dict(id=entry["id"], role="ENTRY", x=0, y=0, z=0, yaw=0), entry)
    exit_s = sockets_of(entry)[0]
    spent[0].add(exit_s["id"])
    open_s = world_socket(placed[0], entry, exit_s)
    prev = entry
    for i in range(1, path_length + 1):
        final = i == path_length
        ok = False
        for _ in range(40):
            c = pick([m for m in middle if m["id"] != prev["id"] and allowed(m)])
            p, arr = place_against(c, open_s)
            if not p or collides(p, c):
                continue
            exits = [s for s in sockets_of(c) if s["id"] != arr["id"] and (s["kind"] in boss_kinds) == final]
            if not exits:
                continue
            ex = rng.choice(exits)
            record(p, c, arr["id"])
            spent[-1].add(ex["id"])
            open_s, prev, ok = world_socket(p, c, ex), c, True
            break
        if not ok:
            return None
    boss = by["BOSS"][0]
    p, arr = place_against(boss, open_s)
    if not p or collides(p, boss):
        return None
    record(p, boss, arr["id"])

    def has_boss_kind(s):
        return any(k in boss_kinds for _c, k in s["sockets"])

    queue = []

    def enqueue(idx, depth):
        pl = placed[idx]
        spec = lib[pl["id"]]
        for s in sockets_of(spec):
            if s["id"] not in spent[idx] and s["kind"] not in boss_kinds:
                queue.append((idx, s, depth))

    for idx, pl in enumerate(list(placed)):
        if pl["role"] != "BOSS":
            enqueue(idx, 0)

    def attach(pool, idx, s):
        if not pool:
            return None
        at = world_socket(placed[idx], lib[placed[idx]["id"]], s)
        cand = list(pool)
        rng.shuffle(cand)
        for c in cand:
            if not allowed(c) or c["id"] == placed[idx]["id"] or has_boss_kind(c):
                continue
            p, arr = place_against(c, at)
            if p and not collides(p, c):
                record(p, c, arr["id"])
                spent[idx].add(s["id"])
                return len(placed) - 1
        return None

    minis = sides = 0
    head = 0
    while head < len(queue):
        idx, s, depth = queue[head]
        head += 1
        if s["id"] in spent[idx]:
            continue
        grown = attach(middle, idx, s) if depth < gen["BranchLength"] else None
        if grown is not None:
            enqueue(grown, depth + 1)
            continue
        if minis < gen["Minibosses"] and attach(by.get("MINIBOSS"), idx, s) is not None:
            minis += 1
        elif sides < gen["MaxSides"] and rng.random() < 0.5 and attach(by.get("SIDE"), idx, s) is not None:
            sides += 1
    if minis < gen["Minibosses"]:
        return None
    for idx in range(len(placed)):
        for s in sockets_of(lib[placed[idx]["id"]]):
            if s["id"] not in spent[idx] and s["kind"] not in boss_kinds:
                if attach(by["CAP"], idx, s) is None:
                    return None
    budget = gen["Backdrop"]
    for host in list(placed):
        hs = lib[host["id"]]
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            if budget <= 0:
                break
            b = pick(by["BACKDROP"])
            p = dict(id=b["id"], role="BACKDROP", x=host["x"] + dx * (hs["half"] + b["half"]), y=host["y"],
                     z=host["z"] + dz * (hs["half"] + b["half"]), yaw=rng.choice((0, 90, 180, 270)))
            if not collides(p, b):
                record(p, b)
                budget -= 1
    return placed
