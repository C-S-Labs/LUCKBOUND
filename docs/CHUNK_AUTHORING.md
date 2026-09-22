# LUCKBOUND — Chunk authoring conventions

**What this is:** the things that have to be true for a piece to work in the
game at all. It is an engine contract and it applies to every world.

**What it is not:** a description of any particular world. Piece size, how many
pieces, what kinds of place they are, and which openings connect to which all
belong to the world being built, and live in its schema in
[`docs/biomes/`](biomes/). **Ask for that document before modelling.**

**Everything not in one of those two places is yours.** Density, scatter,
silhouette, materials, how the ground rolls, what a piece is *of* — none of it
is constrained and none of it should be inferred from here. If something below
reads like a target to hit, it is not: these are the only universal
constraints, and a piece that satisfies them is correct however it looks.

---

## The five conventions

### 1. One metre is one stud

A Roblox character is about 5 studs tall, so a 5-metre reference object in the
scene is a person. Build against that.

The piece's footprint is set by the world, not here. It will be one number, the
same for every piece in that world.

### 2. The origin goes at the centre of the tile, on the ground

Middle of the footprint in both horizontal axes, at ground level vertically —
the point a person would stand on at the centre of the piece.

This is the one that matters most, because the game positions and **rotates**
each piece about its origin. Pieces are turned in quarter-steps depending on how
the map came out, so an origin anywhere but the centre swings the piece out of
place by a different amount each time it is rotated. A corner origin cannot be
corrected for after the fact.

Have the whole piece sitting at the world origin when you export, with
transforms applied.

### 3. Connections need level ground at the opening

Pieces join edge to edge, so wherever a piece is meant to connect, **the ground
should arrive at that opening level, and at the same height on every piece in
the kit** — otherwise the two sides meet at a step or leave a gap.

That applies *only at the openings*. The rest of the perimeter is free: cliff it
off, wall it, run it into dense trees, let it roll. A piece does not have to be
connectable on all four sides, and the sides that are not connectable are
unconstrained.

Two rules of thumb that make a kit hold together:

- Openings of the same type should be **similar in width and identical in
  ground height**, because any two of them may end up joined.
- An opening may end up with **nothing attached to it** — the map does not use
  every one. So an opening reads better as somewhere the ground continues out of
  sight than as a clean doorway onto an edge.

Which openings are which *type* is a per-world decision. It is in the world's
schema, and it is decided before modelling because it is what puts the openings
where they go.

### 4. A piece stands alone

The piece next to any given piece changes from run to run, so nothing should
cross a piece's boundary or depend on what is beside it. No tree overhanging the
edge, no bridge cut to one specific gap, nothing that only reads because of what
happened to be next to it in the authoring scene.

### 5. One file per piece

Export each piece on its own, as its own FBX — not the collection, not the whole
scene. Each one is uploaded separately and the game recombines them, so they
have to arrive as separate meshes.

Name the file for the piece it is rather than a number — `chunk_meadow`,
`chunk_ruins`, `chunk_waterfall`. Names *inside* the file do not matter to us at
all; nothing reads them.

---

## Export settings

| Setting | Value |
|---|---|
| Limit to → Selected Objects | on — one piece per file |
| Forward / Up | `-Z Forward`, `Y Up` |
| **Apply Transform** | **on** |
| Apply Modifiers | on |
| Object Types | mesh only — no cameras, lights or reference rigs |

**Apply Transform matters more than it looks.** With it off, the axis conversion
rides along as a rotation on the object instead of being baked into the mesh
data, and whether that survives the import depends on the importer. This project
has already lost time to an FBX chain mangling transforms quietly.

**Triangle budget: 10,000 per piece.** Over that, Roblox splits the piece into
several meshes and it stops being one object we can place. Decimate rather than
let it split.

**Materials: a piece arrives as one mesh with one colour.** Several material
slots on a joined mesh do not survive as several colours. Either keep a piece to
one material, or expect to colour it on our side.

### Unit scale — this one has already bitten us

A batch once imported at **256,000 studs** instead of 256 — exactly 1000×, which
means the FBX was written in **millimetres** while everything downstream reads
metres.

Two places to set, and both have to agree:

1. **Blender → Scene Properties → Units.** Unit System `Metric`, Unit Scale
   `1.0`, Length `Metres`.
2. **FBX export → Transform.** Scale `1.00`, **Apply Scalings: `FBX All`**.

Then **verify rather than trust it:**

> Import one piece into Studio and read its size. **A piece must measure the
> footprint the world's schema says.** If it reads 1000× the export is in
> millimetres; if it reads 1/100 something applied a 0.01.

Roblox's 3D Importer has its own scale option. Leave it alone and get the file
right; two rescales fighting each other is worse than one.

---

## Lay the kit out so it can be seen

When several pieces are generated in one pass, **space them out on a grid so
every piece is visible at a glance** — a comfortable gap between them, laid out
in rows.

An earlier batch generated every piece stacked at the same spot. Nothing was
broken by it and the exports were fine, but it was impossible to tell what had
been built without hiding things one at a time — and a piece nobody can see is a
piece nobody checks.

**The catch:** the game reads each piece's position from the file, so **each
piece must sit at the world origin when it is exported.** The review layout and
the export position are different things. Either move a piece to the origin,
export it, and put it back, or keep the review offset on a parent that is not
part of the export.

---

## Before you send it — one hand pass

Automated generation is good at making a hundred things and bad at noticing that
four of them are wrong. **Look at each piece yourself**, for:

- **Floating objects.** Scatter sitting slightly above the ground, or hovering
  where the ground dips away under it.
- **Clipping.** Objects buried in each other. A rock partly in the ground is
  fine and often good; a tree through another tree is not.
- **Scale.** Put the 5-metre reference next to a tree, a rock and a bush in
  turn. This catches the case where the piece is right and the scatter inside it
  is 10× off.
- **The edges.** Place a copy of the piece beside itself, rotated a quarter
  turn, and look at where they meet. That is exactly what the game will do.
- **The origin.** Rotate the piece 90° in the viewport. It should spin in place.
  If it swings sideways, the origin is wrong.

The last two take about a minute per piece and catch the two failures that are
most expensive to find later.

---

## What happens on our side

The game builds each expedition by drawing pieces and chaining them together — a
different arrangement every run, from a seed. It places each piece by its
origin, rotates it in quarter-turns to face the piece before it, and joins them
at their openings. It never looks inside the file.

So the parts that have to be predictable are exactly the five above. Everything
else it places as-is.

---

## If something here fights the art

Say so rather than working around it. The conventions exist to make pieces
connect, and a convention that is making pieces worse is the wrong convention.
