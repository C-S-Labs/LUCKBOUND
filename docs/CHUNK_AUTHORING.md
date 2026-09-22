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

## How many sockets, and on which sides

**Author a socket on every side that is genuinely open, and none on a side the
art closes.** A cliff face, a canyon wall, a dense thicket, the back of a ruin
— those get no socket, and the generator will never place anything against
them. That instinct is right and it is what the system wants.

`BOSS` gets exactly one. `ENTRY` gets one exit. Everything else should offer as
many as its art honestly allows.

But three things have to be true before extra sockets actually buy variety, and
today only one of them is.

### 1. The exit is not currently random — this needs a fix

`ChunkCore.exitFor` returns the **first** socket in declaration order that is
valid for the step:

```lua
local function exitFor(chunk: any, consumedId: string, isFinal: boolean): any?
	for _, sock in chunk.Sockets do
		if sock.Id ~= consumedId and isBossKind(sock.Kind) == isFinal then
			return sock
		end
	end
	return nil
end
```

So a piece with four sockets leaves through the same one every time. The entry
chunk is worse — it is hard-coded to `entry.Sockets[1]`. **Adding sockets to a
piece today adds nothing to the variety of a run.** What varies is which piece
is drawn and which yaw the join implies.

Making the exit a weighted random pick among the valid sockets is a small,
contained change to `ChunkCore`, and it is what turns "sockets on every open
side" into the thing you are asking for. It is **recorded as an open item in
`STATUS.md`, not done in this pass** — it changes a System, and a System change
gets its own piece of work with its own tests rather than riding along with a
documentation update.

**Author the sockets anyway.** The data is right either way, and the run
becomes more varied the day that change lands, with no re-export.

### 2. An unused socket is a hole in the art

The generator consumes one socket to arrive and one to leave. On a four-socket
piece that leaves **two openings facing nothing**, and nothing in the loader
caps them. If a socket is modelled as a real gap in the tree line, the player
walks up to it and sees the void under the map.

Until there is a capping mechanism, the art has to solve it:

> **Every socket opening must read as plausible when nothing is attached to
> it.** A path that continues into dense trees and bends out of sight. A gap
> between boulders that narrows. A creek that runs off the edge. What it must
> not be is a clean architectural doorway onto nothing.

This is the real cost of a high socket count, and it is worth paying on the
big `COMBAT` pieces — a meadow with four exits is the piece that makes two
seeds feel different — while a narrow `PATH` piece is fine with two.

### 3. Every socket of a Kind must still be interchangeable

Covered below in the edge contract, but it scales with socket count: four
`PATH` openings on a meadow means four openings that each have to match every
other `PATH` opening in the kit, because the seed decides which meets which.

### What bounds "truly random" anyway

Even with a random exit, a run is not unconstrained, by design:

- **Collision rejection is XZ-only.** A path that folds back over itself is
  rejected even where it would clear in 3D, so some shapes never occur.
- **The arena Kind is reserved.** A Kind the boss accepts is not spendable
  mid-path — that is the rule that makes the Grove always gate the boss, and
  it is a feature, not a limit to remove.
- **`MaxPerLayout`** caps anything that should feel special.
- **The path is a chain, not a graph.** One open socket is carried forward at
  a time; layouts branch only through the SIDE pocket.

### The SIDE pocket does not exist yet

`AssembleOptions.IncludeSide` is declared and `ChunkCore.assemble`'s docstring
promises "optionally hanging one SIDE pocket off a spare socket" — but
**nothing reads that field.** `VV_HOLLOW` is authored, validated, and never
placed. Logged in `STATUS.md`. Worth knowing before anyone spends a day
modelling the hollow.

---

## The edge contract — the seam problem

The terrain in the current pieces varies right up to the boundary, and it slopes
off at the edge. **Two of those edges meeting will not line up**, and the join
shows as a step, a gap you can see through, or a lip that stops the player.

The fix is in the art, and it is a single kit-wide rule.

### The weld band

> **Reserve a flat band, `32` studs wide, along every edge of every chunk. It
> is perfectly flat, at ground height exactly, straight along the footprint
> boundary, on every piece in the kit. Terrain variation lives inward of it
> and eases to zero before it reaches it.**

Two flat, coplanar, straight edges butt together perfectly at any rotation,
forever, with no per-pair work and no runtime cost. It does not matter how
different the two pieces are, how many vertices each edge has, or which yaw the
seed picked — the seam is watertight because both sides are the same flat
plane.

32 studs is about six character-heights: wide enough that the eye reads a
continuous ground plane across the join, narrow enough that it is a small
fraction of a 512-stud piece. **The exact number matters less than it being
identical on every piece.** Pick it once, put it in this doc, never vary it.

Inside the band:

- **Ground height is exactly the walk plane.** No undulation, no slope, no
  displacement modifier reaching into it.
- **Nothing sits on it** except art that is duplicated identically on both
  sides of the join — which in practice means nothing. No rocks, no trees, no
  scatter, no creek stones. The `EdgeDetail_E_01` objects in the current file
  are exactly what has to move inward.
- **Materials match across the kit.** Two pieces of different vintage meeting
  must not show a colour step at the seam.

Outside the band, vary as much as you like. A meadow can roll, a creek can cut,
the ground can rise — as long as it has returned to flat ground height by the
time it reaches the band.

### The skirt

Add a **downward apron** below the band — 8 studs is plenty — so that a
hairline gap from floating-point drift shows dark ground rather than sky. It is
never seen when the join is correct, and it is cheap insurance for when it is
not.

### On generating a connector piece in Studio

You proposed a middle connector piece, generated in Studio, that bridges two
edges and matches their material and colour. Reasonable instinct, and it is the
right question to ask — but it is the more expensive of the two fixes and it
does not actually solve the problem:

- **It cannot match the material.** A chunk's colour and finish live inside the
  uploaded mesh, as `SurfaceAppearance` and textures. Code can read neither. A
  procedurally generated connector would be a flat-coloured strip between two
  textured pieces — trading an invisible seam for a visible band.
- **It is a System change.** `ChunkLoader` currently knows how to place a piece
  and nothing else. Teaching it to synthesise geometry at every join, at four
  rotations, for every `Kind`, is a large amount of new behaviour to maintain
  forever, in service of working around an art rule that costs one flat band.
- **It halves the useful footprint.** Every join gains a piece that is not part
  of the level.
- **The problem comes back anyway.** A connector bridges a height difference by
  ramping, and a ramp at every join changes how the map plays.

**Fix it in the art with the weld band.** The one form of the connector idea
worth keeping is the skirt above: a thin, non-colliding piece *under* the join
that stops you seeing through it. That version does not need to match anything,
because it is never meant to be seen.

---

## Naming

**Does it matter? For a chunk kit — no, and that is worth stating explicitly,
because it is not true elsewhere in this project.**

`ChunkLoader` builds a MeshPart from an asset id and positions it. It never
looks inside the model for a named part. Contrast:

| Loader | Reads names? |
|---|---|
| `ChunkLoader` (a chunk kit) | ❌ nothing inside the piece is read by name |
| `PrefabLoader` (the hub) | ✅ registers from a **named part** — a pivot is invisible metadata an FBX chain mangles quietly |
| `PrebuiltLoader` (a whole map) | ✅ `EntryAnchor` and `ReturnAnchor` |

So inside a chunk you may name objects whatever helps you work. The convention
in the current file — `VerdantValley_Chunk_02_Terrain`,
`VerdantValley_Chunk_02_RouteRock_01_Slab`,
`VerdantValley_Chunk_03_CreekStone_S_01_Pebble` — is clear and consistent, and
nothing here asks you to change it.

### The one name that does matter: the root

The chunk's origin is **not an object with a name.** It is the transform of the
piece's root object, so what carries it is the root's name — and that is the
name the export, the manifest and the content file all have to agree on.

`VerdantValley_Chunk_03` does not say which of the eight pieces this is. The
kit is role-named, and the manifest already has all eight keys reserved with
their source paths:

| Root object / file stem | Manifest key | Chunk `Id` |
|---|---|---|
| `chunk_entry` | `VV_CHUNK_ENTRY` | `VV_ENTRY` |
| `chunk_path_straight` | `VV_CHUNK_PATH_STRAIGHT` | `VV_PATH_STRAIGHT` |
| `chunk_path_bend` | `VV_CHUNK_PATH_BEND` | `VV_PATH_BEND` |
| `chunk_stream` | `VV_CHUNK_STREAM` | `VV_STREAM` |
| `chunk_meadow` | `VV_CHUNK_MEADOW` | `VV_MEADOW` |
| `chunk_grove` | `VV_CHUNK_GROVE` | `VV_GROVE` |
| `chunk_hollow` | `VV_CHUNK_HOLLOW` | `VV_HOLLOW` |
| `chunk_boss_clearing` | `VV_CHUNK_BOSS_CLEARING` | `VV_BOSS_CLEARING` |

A number tells nobody whether `Chunk_03` is the meadow or the stream, and the
role is what decides its size, its socket count and where the generator is
allowed to put it. **Name the root for the piece it is.**

### Socket markers — a convention worth adopting

Nothing reads them today, but the socket offsets in `Content/Chunks/` are
currently typed by hand and there is no way to check them against the file.
An empty at each socket makes the file self-describing and the data reviewable:

```
Socket_north_PATH        empty, at the socket's centre, +Y pointing outward
Socket_south_PATH
Socket_east_WIDE
```

`Socket_<id>_<KIND>`, matching the `Id` and `Kind` in the content file exactly.
Put them in their own collection and **exclude that collection from the FBX
export** — they are authoring metadata, not geometry.

The payoff is that the offsets in `Content/Chunks/VerdantValley.luau` can be
read straight off the file instead of derived from a screenshot, and a
mismatch between art and data becomes something a person can see. If that turns
out to be worth automating later, a script reading these empties and emitting
the Lua table is the obvious next step — but that is a proposal, not a promise,
and the content file stays the source of truth until it happens.

### Do not leave the root off the world origin

The root of `VerdantValley_Chunk_03` currently sits at **Location Y = 100 m**.
Export writes positions relative to the scene origin, so a root parked away
from it arrives offset by exactly that much. Zero the root's location before
exporting — and note this is separate from the origin rule: the *origin* must
be at the piece's centre, and that centre must then sit at `(0, 0, 0)`.

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
5. All transforms applied; **root location zeroed**, piece sitting at the
   Blender world origin.
6. Root object named for the piece's role, matching its manifest key.
7. **A 32-stud weld band on all four edges: flat, at ground height, empty of
   scatter, identical on every piece in the kit.** Variation eases to zero
   before it reaches the band. Skirt below it.
8. A socket on every genuinely open side, none on a side the art closes — and
   **every opening reads as plausible with nothing attached to it.**
9. Each opening is on the 256 grid, at its declared offset, identical in width
   and ground height to every other socket of that `Kind` in the kit.
10. Nothing crosses the boundary; nothing depends on a neighbour.
11. Socket marker empties in their own collection, excluded from the export.
12. Exported alone, to the manifest's `Source`-mirroring export path.
13. `./tests/run.sh` still green — the kit is validated at boot too, and a
    broken kit stops the server rather than shipping a broken expedition.
