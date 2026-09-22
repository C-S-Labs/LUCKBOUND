# LUCKBOUND — Modular Map System

How a biome map gets built from authored pieces. Addendum §A4.

---

## The idea

**Procedural composition, not procedural terrain.** Variety comes from
arranging a bounded library of hand-authored, pre-validated pieces — not from
generating unbounded landscape.

> **This is one of two routes, not the only one.** A world may instead declare
> a `PrebuiltMap` and ship one whole authored scene — see build spec §2.2 and
> `assets/rbxm/maps/README.md`. A kit buys variety and charges modularity for
> it: every piece has to join to every other piece, so gaps, heights and rims
> must all match. Art that was *composed* rather than assembled cannot supply
> that without being re-authored, and Ethereal Scape turned out to be exactly
> that case. Everything below describes the kit route.

The addendum rejects noise-generated terrain for good reasons: unreachable or
buried bosses, voxel micro-gaps that let players skip combat, and wildly
variable mobile performance. A chunk library has none of those failure modes,
because every piece was validated once by a human and never changes.

It is the same combinatorial philosophy as Master Spec §14
(`BASE × ELEMENT × RARITY × MUTATION × WORLD`), applied to level layout.

---

## Status

**Built, tested, and — since 2026-09-16 — actually walkable.**

| Piece | State |
|---|---|
| `Content/AssetManifest.luau` | ✅ logical name → asset id |
| `Content/Chunks/VerdantValley` | ✅ 11 pieces, uploaded |
| `Content/Chunks/SkyCitadel` | ✅ 22 pieces, **delivered and uploaded** — [`biomes/SKY_CITADEL.md`](biomes/SKY_CITADEL.md) |
| `Util/PrebuiltLoader.luau` | ✅ the other route: one authored scene, cloned |
| `Util/ChunkCore.luau` | ✅ seeded assembly, pure and headless |
| `Util/ChunkLoader.luau` | ✅ Layout → Instances, with a mesh/blockout seam |
| `Util/Schema.validateChunks` | ✅ boot-time validation |
| `Systems/ExpeditionSystem` | ✅ builds a map on entry — build spec §7.1 |
| Actual meshes | ✅ both kits uploaded — Verdant Valley's 11 (2026-09-22), Sky Citadel's 22 (2026-09-23) |

Both kits now resolve to real mesh ids. The blockout seam has not gone
anywhere: `assetId()` returns `nil` for anything still `PLACEHOLDER` and the
loader falls back to primitives, which is what let **layouts be assembled,
validated, tested AND walked before a single mesh existed.**

### The blockout is informative, not pretty

When a chunk's mesh is still `PLACEHOLDER`, `ChunkLoader` draws a coloured
floor with a rim, a billboard naming the piece (`ES_WAYSTONE_RING · COMBAT ·
#3`), and a neon post at every socket coloured by its `Kind`.

That is deliberate. **A generated map has to be verifiable by eye.** Two posts
of the same colour meeting is a join the grammar allowed; if the Waystone Ring
is not the piece before the temple, you can see that from the ground rather
than inferring it from a test name.

---

## How a piece is defined

```lua
{
    Id       = "VV_RIDGE_OVERLOOK",
    WorldId  = "VERDANT_VALLEY",
    Role     = "COMBAT",
    AssetKey = "VV_CHUNK_RIDGE_OVERLOOK",  -- into AssetManifest
    SizeX = 256, SizeY = 47.20, SizeZ = 256,
    GroundOffsetY = 4,               -- walk plane, measured up from the box floor
    Sockets = {
        socket("west", "PATH", -128, 0, 270),
        socket("east", "WIDE",  128, 0,  90),   -- an arena approach
    },
    Supports = { Combat = true, Traversal = true, Ambush = true, Shrine = true, MiniBoss = true },
    Weight = 25,
    MaxPerLayout = 1,
    EnemyTags = { "ELDER_TREANT" },
}
```

**Roles:** `ENTRY`, `PATH`, `COMBAT`, `SIDE` (optional branch), `BOSS`, and
`CAP` (seals a socket the layout left open — build spec §7.4). A world needs at
least one `ENTRY`, at least one `BOSS` and at least one connective piece;
everything else is free.

**A role is a routing concept, not a design one.** It tells the assembler where
a piece may be placed and nothing else. A ruin and a mushroom glen can both be
`COMBAT` and be nothing alike — the variety of a world lives in how many
different *kinds of place* it has, not in how many roles. What those are, per
world, is in [`biomes/`](biomes/).

**Sockets** are connection points. `Facing` is degrees on a quarter-turn grid:
`0 = -Z (north)`, `90 = +X`, `180 = +Z`, `270 = -X`. Offsets are local to the
piece, before rotation.

---

## Socket `Kind` is the whole design — and it is PER-WORLD

Two sockets may join **only if their `Kind` matches.** That one rule is what
stops a 4-stud footpath opening onto a cliff face — and it does more work than
it looks like.

Verdant Valley's arena accepts only `WIDE`. The Grove is the only piece that
*offers* a `WIDE` exit. The assembler therefore:

- **never spends the Grove mid-path** (a `WIDE` exit is reserved for the arena)
- **always ends the path on the Grove** before the boss

Which produces Biome Blueprint §3.2's intended gating — the arena is never
reached down a footpath — **without the generator hard-coding it.** It falls
out of the socket rules. A real assembled layout (the path runs SOUTH here
because the delivered entry piece opens south):

```
VV_ENTRY            (   0,     0)  [ENTRY]
VV_PATH_STRAIGHT    (   0,   256)  [PATH]
VV_MEADOW_A         (   0,   512)  [COMBAT]
VV_STREAM_CROSSING  (   0,   768)  [COMBAT]
VV_MUSHROOM_GLEN    (   0,  1024)  [COMBAT]
VV_RIDGE_OVERLOOK   (-256,  1024)  [COMBAT]   ← an arena approach, one of three
VV_BOSS_CLEARING    (-512,  1024)  [BOSS]
```

**Design your socket Kinds deliberately.** They are the level-design grammar,
not a technical detail.

> **This cuts both ways, and the Verdant Valley kit has now hit the other
> edge.** A Kind offered by exactly one piece produces a gate; a Kind offered by
> exactly one piece *also* produces the same map every seed. With 8 pieces the
> Grove gating the boss was the intent. With 12 it is the single largest limit
> on variety, because the arena approach can never be anything else. The fix is
> content — give the arena Kind to two or three pieces that each deserve to be
> the last thing before a boss. The gate survives; the sameness does not.

### Two worlds, two vocabularies, one rule

Kinds are **not a global enum.** Each world invents its own, and a test asserts
the two existing sets do not overlap:

| World | Connective | Arena-only |
|---|---|---|
| Verdant Valley | `PATH` | `WIDE` |
| Sky Citadel | `SKYWAY` (40 studs) | `ASCENT` (72 studs) |

**Sky Citadel is the second kit (2026-09-22)**, and the third time the
reserved-Kind rule has produced gating on its own: only its two gate-courts
offer `ASCENT`, so one of them precedes the Crown Spire arena on every seed
(asserted over 200). It is also the first kit with turns both ways and an
intersection — see *Exits and side pockets* below. Its pieces are the first in the project generated by a script and
exported as real FBXs — see `SKY_CITADEL.md` for what that surfaced about the
loader (the mesh is stretched to `SizeX/Y/Z`, so every piece is pinned to an
exact 256³ box).

Before that, only one kit existed. A second was written for Ethereal Scape, against
this checklist rather than against Verdant Valley, and **the same emergent
property fell out of it**: the Waystone Ring was the only piece offering a
`RITE` exit, the Sky Temple accepted nothing else, so the waystones gated the
temple on every seed. Nobody wrote that rule — it was the reserved-Kind rule
doing its job for a second time.

That kit was retired on 2026-09-17 when the art it was written for turned out
to be a composed traverse rather than eight interchangeable pieces, and the
world became prebuilt instead. **The evidence for the grammar still stands:**
it was written blind against a second world's design and produced correct
gating, which is what was being tested. What it did not survive was contact
with art that was never modular — and that is a fact about the art, not about
the grammar. The next kit (Emberfall) is the real second data point.

---

## Exits, side pockets and caps — changed 2026-09-22, extended 2026-09-23

Two behaviours that were documented as debt are now built, because the Sky
Citadel kit needed them to make an intersection mean anything:

- **A seeded pick among valid exits.** `exitFor` used to return the *first*
  valid socket, so a piece with four openings left the same way on every seed.
  It now draws among them — only when there is a real choice, so a kit of
  two-socket pieces consumes exactly the random numbers it did before.
- **`IncludeSide` is consumed.** After the arena, one SIDE chunk is hung off a
  spare socket (one the path neither arrived nor left through), tried in
  seeded order until one fits without colliding. No fit is not a failure.
  `GameConfig.Expedition.IncludeSide` is the switch; the expedition passes it.
  Verdant Valley's Hollow — authored, validated and never placed until now —
  is placed off the Meadow's west socket.
- **Leftover openings are sealed** (build spec §7.4). Last of all, every socket
  still unjoined takes a `CAP` piece, so a map ends in authored art instead of
  at an opening onto nothing. It runs after everything else and draws from the
  stream after every other decision, so **the same seed produces the same map
  with sealing on and off** — asserted seed by seed, piece by piece. A cap that
  will not fit is skipped: where the path folds back, the cell beyond an
  opening can already be occupied. `GameConfig.Expedition.SealOpenSockets` is
  the switch; a world with no `CAP` pieces is unaffected by it.

## Assembly

```lua
local ok, layout, attempts = ChunkCore.assembleWithRetry(
    Chunks,
    { WorldId = "VERDANT_VALLEY", PathLength = 5 },
    function(attempt) return seedStream(expeditionSeed, attempt) end,
    5
)
```

The result is plain numbers — `{ ChunkId, X, Y, Z, Yaw, Role, Index }` — with
no Roblox types, so a whole layout can be generated and checked in CI.
`Util/ChunkLoader.luau` is the other half: it turns those numbers into CFrames
and Instances and knows nothing about layout rules. **The seam between the two
is a list of numbers, and that seam is why the rules are testable at all.**

### Expedition size

That layout spans **1536 studs** end to end — about **48 seconds** of walking
at WalkSpeed 32, roughly 7% of a 720-second expedition. The rest is combat and
exploration.

It was 4096 studs until the kit went to a uniform 256 on 2026-09-22. **That is
a lot of slack, and `PathLength` is the knob that takes it up** — the traverse
test asserts a relationship, not a number, so a longer path is a content change
and nothing re-derives. Worth retuning once a real piece has been walked, not
before: how long 256 studs of authored forest takes to cross is not the same
question as how long it takes to walk across an empty blockout.

`PathLength` is the knob, and since 2026-09-16 it is **content**: a world sets
`MapPathLength` and falls back to `GameConfig.Expedition.PathLength` when it
does not.

A test asserts traverse stays under 35% of expedition duration **per world**,
so an expedition can never quietly become a corridor simulator. Note the shape
of that rule: it is a *relationship*, not a number, which is what lets a world
pick its own duration without anyone re-deriving a map size to match.

**The same relationship guards a prebuilt world**, where there is no
`PathLength` to turn — the knob is `PrebuiltMap.Scale`, and the tests assert
the scaled traverse fits inside the duration, that an island stays at least as
roomy as a hub district platform, and that a doorway is grand rather than
absurd. Ethereal Scape's first delivery was ~10× oversized: 10,278 studs and
642 seconds against a 300-second expedition. `Scale = 0.1` fixed the arithmetic
and read too small on the ground, so the modeller rebuilt the scene at play
scale — 2,277 studs, 71 seconds one way, `Scale = 1.0`.

That round trip is the argument for the second and third assertions. The first
one alone is satisfied by *any* sufficiently small scale, and "the walk fits"
is not the same claim as "this is a place".

**Retries are expected, not a smell.** A path can fold back and collide with
itself; that is seed-dependent. Measured with 5 attempts:

| Path length | Success |
|---|---|
| 3 | 300/300 |
| 4 | 299/300 |
| 5 | 293/300 |
| 8 | 295/300 |
| 10 | 283/300 |

Assembly is **deterministic**: the same seed always produces the same map, so an
expedition can be replayed for debugging or exploit investigation — which is
what addendum §A4 asks for with per-expedition seeding.

---

## The layer above: what happens in a room

**This document is about where pieces go. It is deliberately not about what
happens in them** — that is the scenario layer, `PROTOTYPE_BUILD_SPEC.md` §7.3,
and the separation is the point:

```
RUN SEED → CHUNK SELECTION → CONNECTION VALIDATION → SCENARIO SELECTION → …
              ChunkCore            ChunkCore              ScenarioCore
```

`ChunkCore` knows nothing about scenarios and `ScenarioCore` knows nothing
about geometry. A chunk declares `Supports` — what it *can* host — and the
generator intersects that with `Content/Scenarios`. So the same Ridge Overlook
is an ambush on one seed and a shrine on the next, and **11 pieces produced 50
distinct chunk/scenario rooms** in the measurement below.

That is why the piece count in a kit matters less than it looks: model count is
not content count.

---

## The geometry contract

The layout rules above are about *data*. The rules below are about the *art*,
and they are the ones that are expensive to discover late.

**The full brief is [`CHUNK_AUTHORING.md`](CHUNK_AUTHORING.md)** — read it
before modelling. The three rules that everything else hangs off:

### 1. The origin is the middle-most point of the chunk

Centre in X, centre in Y, centre in Z. Not a corner, not the middle of a side,
not the Blender world origin.

`ChunkLoader` places a piece by putting its origin at the centre the assembler
chose, and `ChunkCore.overlaps` rejects collisions against centre ± half-size
boxes — so any other origin lands the art half a chunk from where the generator
believes it is. Worse, `Yaw` is derived from the socket pair, so **every piece
gets rotated 0/90/180/270 depending on the seed**, and rotation happens about
the origin. A centre origin spins the piece in place; a corner origin swings it
a whole chunk-width sideways, by a different amount for each yaw. It is not a
constant offset anything can correct for.

### 2. Every chunk is independent

Nothing crosses a boundary, nothing depends on a neighbour, every piece reads
alone and at four rotations. The piece next to it is a different piece next
seed. Art that cannot meet that is a map, not a kit — ship it as a
`PrebuiltMap` instead (`assets/rbxm/maps/README.md`).

### 3. Chunks do not join on any side — only at sockets, only by Kind

An edge with no socket is a wall to the generator; nothing is ever placed
against it. Two sockets join only when their `Kind` strings match exactly, and
each join consumes one socket from each side. Which means **every socket of the
same `Kind` must be physically interchangeable across the whole kit** — same
opening width, same ground height, same approach — because the seed decides
which two meet.

Author a socket on every side the art leaves genuinely open, and none on a side
it closes. Two caveats, both tracked in `STATUS.md`: `exitFor` currently returns
the **first** valid socket rather than a random one, so extra sockets do not yet
vary a run; and the generator consumes only two sockets per piece, so every
other opening faces nothing and must read as plausible unattached.

### 4. Openings need level ground; the rest of the perimeter does not

Pieces butt together edge to edge, so **where a piece connects, the ground must
arrive at that opening level and at the same height on every piece in the kit**
— otherwise the join is a step or a gap.

That constraint applies at the openings and nowhere else. The rest of the
perimeter can cliff off, be walled, run into dense trees or roll however the
art wants, and a piece does not have to be connectable on all four sides.

**This was originally written as a kit-wide flat band along every edge, and
that was wrong.** Handed to a modeller it flattened the terrain to the
boundary on all four sides and produced a putting green — the rule was doing
far more work than the join needed. The join needs level ground at the
openings. Everything else was over-specification, and
`CHUNK_AUTHORING.md` is now scoped to what actually breaks.

---

## Authoring a kit — checklist

1. **Pick one size for the kit.** Verdant Valley uses **256 × 256 for every
   piece**, with sockets at the edge midpoints — one number for the modeller to
   build against rather than a table of eight. Size it against the 5-stud
   character, not against a floorplan: 256 is about 51 character-heights, which
   reads as a clearing. Two earlier iterations came back at ~100 studs (too
   tight to read as a place) and ~1024 (so open that the scatter vanished into
   it), which is how 256 was arrived at. Differently-sized pieces are legal and
   the assembler handles them; one size is simply easier to author to.
2. **Decide your Kinds first.** At minimum one connective Kind and one the
   arena accepts. The arena Kind is automatically reserved. **Do this before
   any modelling** — it is what decides where each piece's openings go, and
   re-cutting openings on a finished kit is the expensive version of this
   conversation.
2b. **Aim for 12–16 pieces.** The variety of a run is the variety of the kit;
   8 starts to repeat itself. Extra pieces are variants of the existing roles —
   several meadows, several groves — weighted so one is common and another
   rare, not new roles.
3. **Two sockets minimum** on anything `PATH` or `COMBAT`, or the path
   dead-ends. Validation rejects this.
4. **At least one `ENTRY` and one `BOSS`** per world — that is all the schema
   requires. More of either is legal and gives a run two different arrivals or
   two different arenas. (A test currently asserts Verdant Valley has exactly
   one of each; that is a statement about that kit, not a rule.)
5. **`MaxPerLayout`** on anything that should feel special.
6. **`SizeX/Y/Z` must be honest** — they drive collision rejection. Too small
   and pieces interpenetrate; too large and assembly fails needlessly.
7. **At least one `SIDE` pocket** — Biome Blueprint §6 checklist asks for one;
   it is a floor, not a ceiling. It needs a piece with 3+ sockets to hang off,
   and the schema refuses a kit that declares a pocket without one.
8. **`CAP` pieces if any piece has more openings than a path can spend** — an
   intersection strands a mouth on most seeds, and without a cap that mouth
   opens onto nothing. A cap has exactly one socket, no `Supports` and no
   `MaxPerLayout`; the schema enforces all three.
9. **Author the geometry against [`CHUNK_AUTHORING.md`](CHUNK_AUTHORING.md)** —
   origin at the chunk's centre, one FBX per chunk, an opening at every socket.
10. Run `./tests/run.sh`. The kit is validated at boot too; a broken kit stops
   the server rather than shipping a broken expedition.

---

## Known limits, named rather than discovered later

- **Collision rejection is XZ-only.** `ChunkCore.overlaps` ignores Y entirely,
  so a path that climbs and folds back over itself is rejected as colliding
  even though it would clear in three dimensions. Sockets *do* carry `OffsetY`
  and the placement maths honours it — but both existing kits set it to 0, so
  that code path is real and untested. **Do not author a climbing kit without
  fixing collision first**, and note the blockout loader joins chunks flat: a
  vertical join would need a ramp the loader does not yet draw.
- **Pathfinding validation is still missing** (below). Two pieces can be
  non-overlapping and still not walkable between.

## What is deliberately not built yet

- **Enemy population** — `EnemyTags` are declared but unconsumed
- **Encounter and reward configuration** — a scenario plan says a room is an
  Ambush; nothing spawns it. Build spec §7.3 draws that line deliberately
- **Pathfinding validation** (addendum §A4 step 4) — a spawn→boss reachability
  pass before letting players in. Collision rejection is not the same thing:
  two pieces can be non-overlapping and still not walkable between.
- **Terrain** — addendum §A3 wants voxel terrain for macro landscape with
  MeshParts for designed objects. Chunks currently assume MeshParts only.

---

## Adding a new world's kit

1. Author pieces in `assets/source/worlds/<world_id>/`, one `.blend` per
   piece, to `CHUNK_AUTHORING.md`
2. Add manifest entries (`PLACEHOLDER` is fine)
3. Add `src/shared/Content/Chunks/<World>.luau` returning a list
4. Run the tests

No System changes at any point. That is the prime directive holding:
**systems are reusable, content is data.**
