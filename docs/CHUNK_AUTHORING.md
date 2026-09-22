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

The ones that cause silent problems if they are wrong:

| Setting | Value |
|---|---|
| Limit to → Selected Objects | on — one piece per file |
| Forward / Up | `-Z Forward`, `Y Up` |
| Apply Transform | on |
| Apply Modifiers | on |
| Object Types | mesh only — no cameras, lights or reference rigs |

A single mesh in Roblox caps at 10,000 triangles. Over that, the importer
offers to split the piece into several meshes, which is fine.

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

## If something here fights the art

Say so rather than working around it. Every number above lives in one content
file on our side and is meant to move; the conventions exist to make pieces
connect, and a convention that is making pieces worse is the wrong convention.
