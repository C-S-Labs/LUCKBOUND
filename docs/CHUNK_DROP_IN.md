# Drop-in chunk kits

A new biome's chunks no longer need a hand-written `Content/Chunks/<World>.luau`
or manifest entries. Put the delivered `.rbxmx` in the world's folder and the
server builds the kit when it starts.

Code: `src/server/Systems/ChunkAutoKit.luau` (loads and measures) and
`src/shared/Util/ChunkKitCore.luau` (turns measurements into chunks; tested in
`tests/cases.luau`, "Drop-in chunk kits").

## Steps

1. **Upload in Studio.** Import the kit (3D Importer / Bulk Import) so every
   chunk is a `MeshPart` with a real `rbxassetid` MeshId. One file holding all
   the chunks (like Sky Citadel's `SC_STRUCTURE.rbxmx`) or one file per chunk
   (like Verdant Valley) both work.
2. **Name every chunk** by the rules below, then right-click the model, choose
   *Save to File*, and save it as `.rbxmx`.
3. **Drop it in** `assets/rbxm/chunks/<world_folder>/`. The folder name is the
   world: `emberfall` → `EMBERFALL`, `astral_reach` → `ASTRAL_REACH`. It must
   match an `Id` in `src/shared/Content/Worlds/`.
4. **Sync and play.** With `rojo serve` connected, press Play. The Output shows:
   ```
   [ChunkAutoKit] EMBERFALL: 12 pieces -- 1 entry, 5 path, 4 combat, 1 side, 0 cap, 1 boss
       EMBERFALL_ENTRY  ENTRY  S
       EMBERFALL_LAVA_BRIDGE  COMBAT  N+S(gate)
       ...
   ```
   Any line starting `[ChunkAutoKit] EMBERFALL:` in yellow is a problem to fix.
5. **Commit** the `.rbxmx` on a branch and open a PR.

## Naming rules (the only convention)

The MeshPart's name, with an optional `chunk_` prefix:

| Name contains / starts with | Role |
|---|---|
| contains `entry` | ENTRY: where players arrive (exactly one opening) |
| contains `boss` or `arena` | BOSS: the arena |
| starts `side_` | SIDE: an optional pocket off the path |
| starts `cap_` | CAP: a dead end that closes an unused opening |
| starts `path_` | PATH: connective |
| anything else | COMBAT: a room |

A world needs at least one ENTRY, one BOSS, and one PATH or COMBAT piece. Names
with `__` in them (`chunk_ruins__ashfall`) are recolour variants and are not
pieces. Every piece must follow CHUNK_AUTHORING.md: origin at the centre of the
footprint, level ground at each opening, openings at edge midpoints.

## What is measured, and what you can override

Each piece is loaded once, off-map, and probed. **An edge is an opening** when
there is deck at walk height just inside the middle of that edge *and* nothing
blocks head height there (a rail or wall means "not an opening"). The walk
height, the footprint and the asset id come from the mesh too.

When the probe gets something wrong, set an **attribute on the MeshPart** in
Studio before saving (Properties → Attributes → +):

| Attribute | Type | Example | Effect |
|---|---|---|---|
| `Openings` | string | `N,S` | Use exactly these openings (N/E/S/W; N is -Z) |
| `Role` | string | `SIDE` | Overrides the name rule |
| `GateSide` | string | `N` | This piece leads into the arena, through this opening |
| `Weight` | number | `2` | Picked twice as often |
| `Supports` | string | `Combat,Treasure` | Scenarios this room can host |

**The arena gate.** The arena only connects to a gate opening. Pieces named
`*gate*` (or with a `GateSide` attribute) are the approach. If none are named,
half of the two-opening COMBAT pieces (else PATH pieces) become approaches
automatically.

## Hand-written kits always win

If a world already has a `Content/Chunks/<World>.luau` (today: Sky Citadel,
Verdant Valley), its drop-in folder is **ignored** and the boot log says so.
To move such a world onto a new drop-in file, delete its `Content/Chunks`
module (its `AssetManifest` block can stay, or go).

**Why old chunks kept appearing:** a hand-written kit loads meshes by the ids
typed in `AssetManifest.luau`. Replacing the `.rbxmx` never changed those ids.

## Limits

- All drop-in openings are one Kind (plus the gate), so layouts are less
  shaped than a hand-tuned kit's (Sky Citadel's SKYWAY/SPAN/RITE vocabulary).
  When a biome needs that, write its `Content/Chunks` module.
- Measuring runs on every server start. It takes about one mesh load per piece,
  run in parallel.
- Meshes must already be uploaded. Nothing can upload at runtime.
