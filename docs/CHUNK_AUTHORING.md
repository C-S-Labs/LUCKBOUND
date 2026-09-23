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

## The six conventions

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

**If a kit has a piece with more openings than a route can spend** — an
intersection, typically — most maps will leave one of them over, and the engine
closes it for you. A **cap** is a piece whose whole job is to be the end of
something: one opening, and a reason for the path to stop (a viewpoint, a
collapse, a locked gate). It is somewhere a player walks into and looks around,
not a wall, so give it something to find. Author two or three so a map with
several loose ends does not end the same way twice. They are placed
automatically wherever a route runs out; see build spec §7.4.

Which openings are which *type* is a per-world decision. It is in the world's
schema, and it is decided before modelling because it is what puts the openings
where they go.

### 4. A piece stands alone

The piece next to any given piece changes from run to run, so nothing should
cross a piece's boundary or depend on what is beside it. No tree overhanging the
edge, no bridge cut to one specific gap, nothing that only reads because of what
happened to be next to it in the authoring scene.

### 5. Every piece is its own object, named for what it is

Each piece must reach Roblox as **its own mesh**. The game uploads and places
them separately and recombines them per run.

You may export them **one FBX per piece, or all of them in one FBX** as
separate objects. Roblox's 3D Importer turns a multi-object FBX into one Model
with a MeshPart per object, and centres each mesh on its own bounds, which is
the convention the loader uses. One file is less work; either is correct.
**Do not join the pieces into one object.**

**Names matter.** The object name becomes the part name and is how a piece is
matched to its content entry. Name for what the piece is — `chunk_meadow`,
`chunk_ruins`, `chunk_waterfall` — never a number.

### 6. Structure and ambient scenery are separate — every kit, every biome

**Adopted 2026-09-23, owner-directed. Applies to every kit from now on**, so no
biome has to be re-exported to get animated or scalable scenery later.

A piece is two different kinds of thing, and they are delivered differently:

| | Structure | Ambient scenery |
|---|---|---|
| **What** | everything walked on, collided with, or that makes the place what it is: decks, floors, walls, bridges, stairs, keels, cliffs, landmarks, trees, rocks, buildings | everything that floats, drifts, flies, spins, glows or is there only for mood, never blocking the player: floating crystals and shards, floating books, rings, birds and drones, lanterns, falling leaves, embers |
| **Delivered as** | part of the piece's mesh (convention 5) | **not** merged into the piece; one copy of each *kind*, plus a list of where it goes |
| **Drawn by** | the server, with collision | each player's device only, no collision, animated, and thinned out on low graphics |

**How to deliver ambient scenery:**

1. **Author each kind once**, as its own object named `prop_<what>` —
   `prop_crystal_a`, `prop_crystal_b`, `prop_book`, `prop_bird`. A variant is a
   new name. A crystal used 200 times across the kit is still **one** object.
2. **Collect one copy of each** into a collection named `PropLibrary` and
   export that collection as **one FBX**, objects kept separate. Import it with
   the 3D Importer (one Model, one MeshPart per prop), then save it as one
   `.rbxmx` with the export plugin in the place.
3. **Where they go is data, not geometry.** For each piece, a list of props:
   name, position, rotation and scale **relative to the piece's origin**, an
   animation class and a detail tier. A generated kit's script writes this list
   for you. For a hand-placed kit, place props as linked duplicates, and a
   Blender script reads them out of the scene.
4. **Animation class** per placement, one of `PropCore.ANIMS`. Pick the one
   that is true to the object (owner, 2026-09-23: "the animations have to make
   sense for what they are"):

   | Class | Motion | Use for |
   |---|---|---|
   | `Static` | none | anything that should just hang there |
   | `Float` | slow bob only | beacons, a drifting stone |
   | `Hover` | gentle bob plus a slow turn about vertical | crystals, pylons, books |
   | `Spin` | slow turn about vertical, nothing else | rings round a keel or a tower |
   | `Roll` | very slow turn **in its own plane**, no bob or sway | rings a path passes through |
   | `Moored` | small bob, slight rock along the keel | boats at a dock |
   | `Tumble` | bob, mild rock, slow turn | debris, rubble |
   | `Bird` | the piece's flock circles its centre, nose first, banked | birds |

   Rules every class keeps (tested): **nothing ever changes size**; bob and
   spin are about true vertical whatever the prop's tilt; rock and roll are
   about the prop's own axes. A `Bird` circles the vertical axis through its
   piece's centre at its own radius and height, and the whole flock turns as
   one. So **the generator must prove each bird's full circle clear**, as Sky
   Citadel's `clear_bird_orbits` does. A spot that is merely clear at rest is
   not enough. **Detail tier** 1–3: 1 shows on every device, 3 is dense extra
   shown only on high graphics (`GameConfig.Ambience.Props.TierMinQuality`).
5. **Where it lands in the repo.** Placements are
   `src/shared/Content/Props/<World>.luau` (`Id` = the world, `Library`,
   `Placements`), validated at boot by `Schema.validateProps`. The library
   `.rbxmx` goes in `assets/rbxm/props/` and Rojo mounts it as
   `ReplicatedStorage.LuckboundProps`; `PropController` clones by name, so a
   renamed MeshPart is a missing prop (it warns, naming it).

**A generated kit does all of this from its script.** Sky Citadel's
`build_sky_citadel_kit.py` builds each prop inside `as_prop(...)`, dedupes
shapes into a library (22 kinds from 168 placements), and writes exactly two
FBXs, `sky_citadel_structure.fbx` (22 pieces) and `sky_citadel_props.fbx` (one
of each prop), plus `Content/Props/SkyCitadel.luau`. Its `main()` refuses to
finish unless both files re-import with the right object counts and sizes.

**Placement maths (for the next kit).** Placements are written in the layout
frame (Blender x, y, z → game x, z, −y). The importer turns every mesh by the
piece's measured `MeshYawOffset`, so `PropController` applies that same turn
last, on the prop's own rotation. Keep `MeshYawOffset` accurate and props land
where they were authored.

**Why:**
- it's the only way scenery can move
- detail can scale with each player's graphics
- each kind of prop is uploaded once instead of baked into 22 meshes
- floating clutter stops inflating each piece's collision

**Keep the size pins.** With the scenery removed, the structure mesh must still
fill the piece's declared box exactly (for Sky Citadel, 256³: tiny pins at the
bottom corners, the landmark reaching the top). `ChunkLoader` sets every mesh to
its declared size, so a piece that shrank would be stretched.

**Rigid props only for now.** A bird that flies a path is fine. Flapping wings
need the wings as separate parts or a rigged mesh, which is a later polish.

---

## What a piece can support

Beyond the five conventions, tell us **what kinds of thing could happen in this
piece** — is there arena space for a mini-boss, real verticality for a
traversal challenge, an enclosed corner for a puzzle, somewhere a secret could
hide, a point of no return for an ambush?

You are not designing those encounters. You are saying what the geometry can
carry, and we record it as the piece's compatibility list. The generator picks
what actually happens in a room per run, so **the same piece is a different
room on different runs** — which is where most of the game's variety comes
from, and why a piece that can carry several things is worth more than a piece
that can carry one.

A sentence per piece is enough: *"open, with high ground at one end — good for
a fight or an ambush, no cover for a puzzle."*

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
