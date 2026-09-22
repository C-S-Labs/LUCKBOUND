# LUCKBOUND — Authoring a chunk in Blender

The geometry brief for the modular map kit. `MODULAR_MAPS.md` describes the
system that consumes these pieces; this file describes the file you hand it.

**Read this before modelling.** Every rule below is a rule because
`Util/ChunkLoader.luau` or `Util/ChunkCore.luau` already behaves that way. None
of it is preference.

---

## Scale

**1 Blender metre = 1 Roblox stud. Do not deviate.** Same rule as the
Crossroads and Fate Engine briefs.

A Roblox R6 character is **5 studs tall, 2 wide, 1 deep.** Keep a 5-metre
reference cube in the scene and measure against it, never against your
viewport's sense of size.

The Verdant Valley kit is already sized in `Content/Chunks/VerdantValley.luau`
and those numbers are the contract:

| Piece | Footprint (studs) |
|---|---|
| `VV_ENTRY` | 512 × 512 |
| `VV_PATH_STRAIGHT` | 256 × 512 |
| `VV_PATH_BEND` | 512 × 512 |
| `VV_STREAM` | 768 × 512 |
| `VV_MEADOW` | 1024 × 1024 |
| `VV_GROVE` | 768 × 768 |
| `VV_HOLLOW` | 512 × 512 |
| `VV_BOSS_CLEARING` | 1024 × 1024 |

**Pieces are not all the same size, and there is no 4-tile grid.** A kit is a
library of differently-shaped pieces that the assembler chains end to end; it
is not a tiled terrain patch. A test build of four equal squares laid in a
2 × 2 block is not a smaller version of this system — it is a different system.

All footprints are multiples of **256 studs**, the kit grid. A piece that is
not a multiple of the grid cannot have its sockets land on the grid, and
pieces will not meet.

---

## The origin — the single most important setting in the file

> **Put the object origin at the exact middle-most point of the chunk's
> bounding box: centre in X, centre in Y, centre in Z.**

Not a corner. Not the middle of one side. Not the Blender world origin. The
dead centre of the box the piece occupies.

### Why: the loader positions by centre and rotates about the origin

`Util/ChunkLoader.luau`:

```lua
local centre = origin + Vector3.new(placed.X, placed.Y, placed.Z)
local cframe = CFrame.new(centre) * CFrame.Angles(0, math.rad(placed.Yaw), 0)
```

`placed.X/Y/Z` is the **centre** the assembler chose for that piece, and
`ChunkCore.overlaps` rejects collisions by comparing centre ± half-size boxes.
So a piece whose origin sits anywhere else lands half a chunk away from where
the generator believes it is — and the generator will happily certify a layout
as collision-free that visibly overlaps on the ground.

The rotation is the worse half. `ChunkCore` derives `Yaw` from the socket pair
— it turns the candidate piece so its socket faces back down the corridor —
so **every piece will be rotated 0°, 90°, 180° or 270° depending on the seed.**
Rotation happens about the origin:

| Origin | What a 90° turn does |
|---|---|
| Centre | the piece spins in place ✅ |
| A corner | the piece swings a whole chunk-width sideways, differently for each yaw ❌ |
| Middle of an edge | the piece swings half a chunk-width sideways ❌ |

Plain version: **the origin is the handle the game picks the chunk up by.**
Grab a floor tile by its middle and turning it leaves it where it was. Grab it
by a corner and turning it throws it across the room.

A corner or edge origin is not a constant offset you can correct for later,
because the error changes with the yaw the seed picked. There is no fix except
the right origin.

### The Y axis, precisely

`ChunkLoader` sets `mesh.Size = Vector3.new(SizeX, SizeY, SizeZ)` and then puts
that box's **centre** at the layout's Y. So the origin is the centre of the
bounding box vertically too, and two things follow:

1. **`SizeY` must be the piece's true full height** — underside and terrain
   body below the walking surface, plus canopy, rock and tree above it. The
   Verdant Valley kit declares `SizeY = 340` for every piece.
2. **The walking surface should sit at the vertical middle of that box.** With
   `SizeY = 340` that is 170 studs of ground body below the walk plane and 170
   studs of headroom above it. Author the ground plane at Blender Z 0 and keep
   the piece symmetric about it.

Roblox **stretches** a mesh to fill `mesh.Size`. If the declared `SizeY` does
not match the real bounding box, the art arrives distorted rather than
clipped — which is why point 1 is a hard requirement and not bookkeeping.

> **Known seam, being tracked:** the blockout floor puts the *walking surface*
> at the layout Y, while the mesh path puts the *bounding-box centre* there.
> Those agree only if the walk plane is centred in the box, which is why the
> rule above says to centre it. A `GroundOffsetY` field on the chunk schema
> would remove the constraint; it is recorded as an open item in `STATUS.md`
> rather than hacked into the loader.

### Doing it in Blender

1. Select every object in the piece.
2. `Ctrl+A ▸ All Transforms` — unapplied scale and rotation is the most common
   cause of "it imported at the wrong size and I cannot see why".
3. `Object ▸ Join` if the piece is to be one mesh, or parent everything to one
   empty if it is to stay a Model.
4. `Object ▸ Set Origin ▸ Origin to Geometry` (bounds centre), or snap the 3D
   cursor to the computed centre and use `Origin to 3D Cursor` when the
   geometry's mass centre is not the footprint centre — which it usually is
   not, because scatter is uneven.
5. Move the piece so its origin sits at the Blender world origin before
   exporting. The exporter writes positions relative to the scene origin, and
   a piece parked out at (4000, 0, 0) arrives 4000 studs off.

---

## Every chunk is an independent object

A chunk is a **self-contained piece that must read correctly standing alone,
next to any other piece the grammar allows, at any of four rotations.**

This is not a stylistic preference. `ChunkCore` chains pieces one at a time and
the order is seed-dependent, so:

- **Nothing may cross a chunk boundary.** No tree overhanging the edge, no
  rock straddling two pieces, no path that only makes sense because of what you
  happened to place next to it in the Blender scene. The neighbour will be a
  different piece next seed.
- **Nothing may depend on a neighbour's geometry.** A bridge cut to one
  specific gap, a stair built for one specific height difference, a cliff that
  only reads because the piece behind it is taller — each of those is a map,
  not a kit. `assets/README.md` has the four questions that settle which one
  you have; any "no" means the art should ship as a `PrebuiltMap` instead.
- **Every piece is flat at the same height.** Collision rejection is XZ-only
  and the loader joins chunks flat, with no ramp drawn between them. Both
  existing kits set `OffsetY = 0` on every socket. **Do not author a climbing
  kit** until that is fixed — it is a named limit in `MODULAR_MAPS.md`.
- **The edges must match across the whole kit.** Ground height at the rim,
  path width at a socket, material at the seam. Two pieces meeting is a butt
  join between two flat edges; anything that does not line up shows as a
  visible step or a gap the player can fall through.
- **Scatter stays inside its own piece.** Trees, rocks and bushes are merged
  into the chunk they belong to. They are part of the piece's identity, not
  independently placed by the generator.

---

## Where chunks join: sockets

**No. Chunks cannot attach on any side.** They attach only where you declared
a socket, and only to a socket of a matching `Kind`.

A socket is a declared connection point in `Content/Chunks/<World>.luau`:

```lua
socket("south", "PATH", 0, 256, 180)
--      id      kind   offsetX offsetZ facing
```

- `OffsetX` / `OffsetZ` are **local to the piece, measured from the origin,
  before rotation.** For a 512-deep piece, the south socket is at `+256` and
  the north at `-256` — which only works if the origin is the centre, the same
  constraint as above, arriving from a second direction.
- `Facing` is degrees on a quarter-turn grid: `0 = -Z (north)`, `90 = +X`,
  `180 = +Z (south)`, `270 = -X`. It is the direction the opening points
  outward.
- Sockets must land on the **256-stud grid**, or pieces will not meet.

### The four rules the assembler enforces

1. **Only where a socket exists.** An edge with no socket is a wall as far as
   the generator is concerned — nothing will ever be placed against it. A
   1024-wide meadow with sockets only on north and south will never be entered
   from the east, whatever the art suggests.
2. **`Kind` must match exactly.** Two sockets join only if their `Kind`
   strings are equal. This is the level-design grammar: Verdant Valley uses
   `PATH` for connective joins and `WIDE` for the boss arena, and because the
   Grove is the only piece offering a `WIDE` exit, the Grove is always the
   piece before the boss. Nobody coded that — it falls out of the rule.
3. **Kinds are per-world.** Each world invents its own vocabulary, and a test
   asserts the sets do not overlap between worlds.
4. **One socket is consumed per join.** A `PATH` or `COMBAT` piece needs **at
   least two sockets** or the corridor dead-ends there; validation rejects one.
   `ENTRY` needs one exit, `BOSS` needs one entrance, `SIDE` needs one.

### What this means for the geometry

A socket is a promise about the art. **Every socket of the same `Kind` must be
physically interchangeable across the whole kit:** the same opening width, the
same ground height, the same approach. A `PATH` opening that is 40 studs wide
on one piece and 12 on another produces a visible pinch when the seed puts them
together, and a `PATH` opening at a different ground height produces a step the
player may not be able to climb.

Model the opening as a real gap in the piece's edge treatment — a break in the
tree line, a cut in the rim — centred on the declared offset. The blockout
already draws a **neon post at every socket, coloured by `Kind`**, so you can
stand in a generated map and see whether your art's opening is where the data
says it is. Two posts of the same colour meeting is a legal join; a post with
no opening behind it is art that has drifted from its data.

---

## Export

**One FBX per chunk. One chunk per file. Never the whole folder.**

`AssetManifest.luau` maps one logical key to one uploaded asset id, and
`ChunkLoader` asks for one key and positions and rotates the single MeshPart it
gets back. A grouped export arrives as one fused object with one id, and the
generator has nothing to shuffle — the whole point is that eight pieces
recombine per seed, so they must be eight separate assets.

Path and naming, mirroring `assets/README.md`:

| | |
|---|---|
| Source | `assets/source/worlds/verdant_valley/chunk_grove.blend` |
| Export | `assets/export/worlds/verdant_valley/chunk_grove.fbx` |
| Manifest key | `VV_CHUNK_GROVE` |
| Chunk `AssetKey` | `VV_CHUNK_GROVE` |

The manifest already has a `Source` path reserved for all eight Verdant Valley
pieces. Use those paths.

### FBX settings that matter

| Setting | Value | Why |
|---|---|---|
| **Limit to → Selected Objects** | ✅ | one chunk per file |
| **Forward / Up** | `-Z Forward`, `Y Up` | Blender is Z-up, Roblox is Y-up |
| **Apply Transform** | ✅ | otherwise rotation and scale arrive baked wrong |
| **Object Types** | Mesh only | leave out cameras, lights and the scale rig |
| **Apply Modifiers** | ✅ | the importer does not run your modifier stack |

Watch the **10,000 triangle cap** on a single MeshPart. A meadow with sixty
trees will exceed it; the importer offers to split into several MeshParts,
which is fine — group them and the chunk becomes a Model rather than one
MeshPart.

### After upload

Record the returned id in `AssetManifest.luau` and flip `Status` from
`"PLACEHOLDER"` to `"UPLOADED"`. Nothing else changes anywhere. `ChunkLoader`
uses the mesh for any key that resolves and blockout for any key that does not,
so **the kit converts from primitives to art one piece at a time.** A
half-uploaded kit is a valid state to play in. There is no flag day.

---

## Checklist before you export

1. 1 metre = 1 stud, checked against a 5-metre reference, not by eye.
2. Footprint matches the `SizeX` / `SizeZ` in `Content/Chunks/`, and both are
   multiples of 256.
3. `SizeY` matches the true full height, walk plane centred in it.
4. Origin at the middle-most point of the bounding box — all three axes.
5. All transforms applied; piece sitting at the Blender world origin.
6. An opening in the edge at every declared socket, on the 256 grid, at the
   declared offset, identical in width and height to every other socket of
   that `Kind` anywhere in the kit.
7. Nothing crosses the boundary; nothing depends on a neighbour.
8. Exported alone, to the manifest's `Source`-mirroring export path.
9. `./tests/run.sh` still green — the kit is validated at boot too, and a
   broken kit stops the server rather than shipping a broken expedition.
