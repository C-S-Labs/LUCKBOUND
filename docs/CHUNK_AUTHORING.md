# LUCKBOUND — Chunk authoring conventions

**What this is:** the short list of things that have to be true for a piece to
work in the game. Not a specification, and not an art brief.

**Everything not on this list is yours.** Density, scatter, silhouette,
materials, how the ground rolls, what the piece is *of* — none of that is
constrained here and none of it should be inferred from here. If something
below reads like a target to hit, it is not: these are the only constraints,
and a piece that satisfies them is correct however it looks.

---

## The six conventions

### 1. One metre is one stud

A Roblox character is about 5 studs tall, so a 5-metre reference object in the
scene is a person. Build against that.

### 2. Every piece is 256 × 256 on the ground

One size for the whole kit. Height is free — build up and down as much as the
piece wants.

256 studs is a little over 50 character-heights across. Previous iterations
were ~100 (too tight) and ~1024 (far too open); this is the middle we settled
on. **If it turns out to read wrong on the ground, say so and we change the
number** — it lives in one content file on our side, and it is cheaper to
change than to work around.

### 2b. A full kit is 12–16 pieces, all different

These pieces are the raw material the game shuffles — it draws from the kit and
chains a different arrangement together every run. **So the variety of a run is
the variety of the kit.** Twelve to sixteen distinct pieces is the target for a
world. Fewer and runs start repeating themselves; more is welcome but not
required.

**Different means genuinely different** — a different shape of clearing, a
different reason to be there — not the same piece with the trees moved.

**For this pass, build 4.** Enough to generate a real map and walk it, cheap to
throw away if something in the pipeline is still wrong. The four that make a
complete walkable map are:

| Piece | Role |
|---|---|
| `chunk_entry` | where the player arrives — one opening |
| `chunk_path_straight` | connective — two openings, opposite sides |
| `chunk_grove` | the piece before the arena — two openings |
| `chunk_boss_clearing` | the arena — one opening |

Once those four are through the pipeline, the remaining 8–12 can be built in
one go. Where several pieces serve the same purpose, suffix them —
`chunk_meadow_a`, `chunk_meadow_b` — and we weight them on our side so one can
be common and another rare.

### 3. The origin goes at the centre of the tile, on the ground

Middle of the footprint in both horizontal axes, at ground level vertically —
so the origin is the point a person would stand on at the centre of the piece.

This is the one that matters most, because the game positions and **rotates**
each piece about its origin. Pieces are turned in quarter-steps depending on
how the map came out, so an origin anywhere but the centre swings the piece
out of place by a different amount each time it is rotated. A corner origin
cannot be corrected for after the fact.

Have the whole piece sitting at the Blender world origin when you export, with
transforms applied.

### 4. Connections need level ground at the opening

Pieces join edge to edge, so wherever a piece is meant to connect, **the ground
should arrive at that opening level, and at the same height on every piece in
the kit** — otherwise the two sides meet at a step or leave a gap.

That applies *only at the openings*. The rest of the perimeter is free: cliff
it off, wall it, run it into dense trees, let it roll. A piece does not have to
be connectable on all four sides, and the sides that are not connectable are
unconstrained.

Tell us which sides are openings and roughly how wide, and we put that in the
data. Two rules of thumb that make a kit hold together:

- Openings of the same type should be **similar in width and identical in
  ground height**, because any two of them may end up joined.
- An opening may end up with **nothing attached to it** — the map does not use
  every one. So an opening reads better as somewhere the ground continues out
  of sight than as a clean doorway onto an edge.

### 5. A piece stands alone

The piece next to any given piece changes from run to run, so nothing should
cross a piece's boundary or depend on what is beside it. No tree overhanging
the edge, no bridge cut to one specific gap, nothing that only reads because of
what happened to be next to it in the authoring scene.

### 6. One file per piece

Export each piece on its own, as its own FBX — not the collection, not the
whole scene. Each one is uploaded separately and the game recombines them, so
they have to arrive as separate meshes.

Name the file for the piece it is rather than a number: `chunk_meadow`,
`chunk_grove`, `chunk_stream`, `chunk_entry`, `chunk_boss_clearing`, and so on.
Which piece it is determines where the game is allowed to place it, and a
number does not carry that.

Names *inside* the file do not matter to us at all — nothing reads them. Use
whatever helps you work.

---

## Export settings

| Setting | Value |
|---|---|
| Limit to → Selected Objects | on — one piece per file |
| Forward / Up | `-Z Forward`, `Y Up` |
| Apply Transform | on |
| Apply Modifiers | on |
| Object Types | mesh only — no cameras, lights or reference rigs |

A single mesh in Roblox caps at 10,000 triangles. Over that, the importer
offers to split the piece into several meshes, which is fine.

### Unit scale — this one has already bitten us

The last batch imported at **256,000 studs** instead of 256. That is exactly
1000×, which means the FBX was written in **millimetres** while everything
downstream reads it as metres. Studio cannot do anything useful with a part
that size.

Two places to set, and both have to agree:

1. **Blender → Scene Properties → Units.** Unit System `Metric`, Unit Scale
   `1.0`, Length `Metres`.
2. **FBX export → Transform.** Scale `1.00`, and **Apply Scalings: `FBX All`.**

Then **verify rather than trust it.** The check takes ten seconds and catches
every version of this problem at once:

> Import one piece into Studio and read its size. **A 256 × 256 piece must
> measure 256 × 256 studs.** If it reads 256,000 the export is in millimetres;
> if it reads 2.56 something applied a 0.01.

If the exporter cannot be made to behave, setting the FBX export scale to
`0.001` compensates — but fix the units properly first, because a compensating
factor is a thing someone will later remove for looking wrong.

Roblox's 3D Importer also has its own scale option. Leave it alone and get the
file right; two rescales fighting each other is worse than one.

---

## Lay the kit out so it can be seen

When several pieces are generated in one pass, **space them out on a grid so
every piece is visible at a glance** — a comfortable gap between them, say half
a piece-width of clear air, laid out in rows.

The last batch generated every piece stacked on top of the others at the same
spot. Nothing was broken by it and the exports were fine, but it was impossible
to tell what had been built without hiding things one at a time — and a piece
nobody can see is a piece nobody checks.

**The one catch:** the game reads each piece's position from the file, so
**each piece must sit at the world origin when it is exported.** The review
layout and the export position are different things. Either move a piece to the
origin, export it, and put it back, or keep the review offset on a parent that
is not part of the export. What must not happen is a piece exported while
parked out on the review grid — it arrives that far off in game.

---

## Before you send it — one hand pass

Automated generation is good at making a hundred things and bad at noticing
that four of them are wrong. **Look at each piece yourself before it ships**,
and specifically for these:

- **Floating objects.** Trees, rocks and bushes sitting slightly above the
  ground, or hovering where the ground dips away under them. Common when
  scatter is placed by rule rather than by eye.
- **Clipping and intersection.** Objects buried in each other or half-sunk in
  the terrain. A rock partly in the ground is fine and often good; a tree
  through another tree is not.
- **Scale.** Put the 5-metre reference next to a tree, a rock and a bush in
  turn. A tree should read as a tree next to a person. This catches the case
  where the piece is right and the scatter inside it is 10× off.
- **The edges.** Place a copy of the piece beside itself, rotated a quarter
  turn, and look at where they meet. That is exactly what the game will do, and
  it is the fastest way to see a bad join before it is eight pieces and an
  upload.
- **The origin.** Rotate the piece 90° in the viewport. It should spin in
  place. If it swings sideways, the origin is not where it needs to be.

That last pair takes about a minute per piece and catches the two failures that
are most expensive to find later.

---

## What happens on our side

Briefly, so the constraints make sense rather than looking arbitrary.

The game builds each expedition by drawing pieces and chaining them together —
a different arrangement every run, from a seed. It places each piece by its
origin, rotates it in quarter-turns to face the piece before it, and joins them
at their openings. It never looks inside the file.

So the parts that have to be predictable are exactly the six above: the size,
the origin, the openings, and the fact that each piece is independent and
arrives as its own mesh. Everything else it simply places as-is.

---

## Starting a different world

The conventions above are the same for every world — size, origin, openings,
independence, one file per piece. What is *not* portable is which pieces
connect to which: each world gets its own set of connection types, decided
before anything is modelled, because it is what makes the pieces chain in the
intended order.

So for a new world, ask us for the connection vocabulary first. It is a short
conversation and it costs nothing; discovering afterwards that every piece
connects to every other piece means re-cutting the openings on all of them.

---

## If something here fights the art

Say so rather than working around it. Every number above lives in one content
file on our side and is meant to move; the conventions exist to make pieces
connect, and a convention that is making pieces worse is the wrong convention.
