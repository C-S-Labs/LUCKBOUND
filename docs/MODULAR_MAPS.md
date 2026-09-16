# LUCKBOUND — Modular Map System

How a biome map gets built from authored pieces. Addendum §A4.

---

## The idea

**Procedural composition, not procedural terrain.** Variety comes from
arranging a bounded library of hand-authored, pre-validated pieces — not from
generating unbounded landscape.

The addendum rejects noise-generated terrain for good reasons: unreachable or
buried bosses, voxel micro-gaps that let players skip combat, and wildly
variable mobile performance. A chunk library has none of those failure modes,
because every piece was validated once by a human and never changes.

It is the same combinatorial philosophy as Master Spec §14
(`BASE × ELEMENT × RARITY × MUTATION × WORLD`), applied to level layout.

---

## Status

**Built and tested. No art yet — and that is on purpose.**

| Piece | State |
|---|---|
| `Content/AssetManifest.luau` | ✅ logical name → asset id |
| `Content/Chunks/` | ✅ Verdant Valley kit, 8 pieces |
| `Util/ChunkCore.luau` | ✅ seeded assembly, pure and headless |
| `Util/Schema.validateChunks` | ✅ boot-time validation |
| Roblox-side loader | ⏳ Phase 2 — needs expedition entry |
| Actual meshes | ⏳ all 8 are `PLACEHOLDER` |

Every asset key is a placeholder, so `assetId()` returns `nil` and a loader
would fall back to primitives. **Layouts are fully assembled, validated and
tested before a single mesh exists.**

---

## How a piece is defined

```lua
{
    Id       = "VV_GROVE",
    WorldId  = "VERDANT_VALLEY",
    Role     = "COMBAT",
    AssetKey = "VV_CHUNK_GROVE",     -- into AssetManifest
    SizeX = 144, SizeY = 64, SizeZ = 144,
    Sockets = {
        socket("south", "PATH", 0,  72, 180),
        socket("north", "WIDE", 0, -72,   0),
    },
    Weight = 25,
    MaxPerLayout = 1,
    EnemyTags = { "ELDER_TREANT", "FOREST_WOLF" },
}
```

**Roles:** `ENTRY` (exactly one), `PATH`, `COMBAT`, `SIDE` (optional branch),
`BOSS` (exactly one).

**Sockets** are connection points. `Facing` is degrees on a quarter-turn grid:
`0 = -Z (north)`, `90 = +X`, `180 = +Z`, `270 = -X`. Offsets are local to the
piece, before rotation.

---

## Socket `Kind` is the whole design

Two sockets may join **only if their `Kind` matches.** That one rule is what
stops a 4-stud footpath opening onto a cliff face — and it does more work than
it looks like.

Verdant Valley's arena accepts only `WIDE`. The Grove is the only piece that
*offers* a `WIDE` exit. The assembler therefore:

- **never spends the Grove mid-path** (a `WIDE` exit is reserved for the arena)
- **always ends the path on the Grove** before the boss

Which produces exactly Biome Blueprint §3.2's intended progression — *"Elder
Treants gate the approach to the boss clearing"* — **without the generator
hard-coding it.** It falls out of the socket rules. A real assembled layout:

```
VV_ENTRY          (     0,      0)  [ENTRY]
VV_STREAM         (     0,   -512)  [COMBAT]
VV_PATH_STRAIGHT  (     0,  -1024)  [PATH]
VV_MEADOW         (     0,  -1792)  [COMBAT]
VV_PATH_STRAIGHT  (     0,  -2560)  [PATH]
VV_GROVE          (     0,  -3200)  [COMBAT]   ← always the approach
VV_BOSS_CLEARING  (     0,  -4096)  [BOSS]
```

**Design your socket Kinds deliberately.** They are the level-design grammar,
not a technical detail.

---

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
no Roblox types, so a whole layout can be generated and checked in CI. The
Phase 2 loader turns it into CFrames.

### Expedition size

That layout spans **4096 studs** end to end — about **128 seconds** of walking
at WalkSpeed 32, roughly 18% of a 720-second expedition. The rest is combat and
exploration.

`PathLength` is the knob. A test asserts traverse stays under 35% of expedition
duration, so an expedition can never quietly become a corridor simulator.

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

## Authoring a kit — checklist

1. **Pick a grid.** Verdant Valley uses **256 studs**. Sockets must land on it
   or pieces will not meet. Size against the 5-stud character, not against a
   floorplan: the smallest connective piece is 256×512, about 51×102
   character-heights, so a corridor reads as a forest path and not a hallway.
2. **Decide your Kinds first.** At minimum one connective Kind and one the
   arena accepts. The arena Kind is automatically reserved.
3. **Two sockets minimum** on anything `PATH` or `COMBAT`, or the path
   dead-ends. Validation rejects this.
4. **One `ENTRY`, one `BOSS`** per world.
5. **`MaxPerLayout`** on anything that should feel special.
6. **`SizeX/Y/Z` must be honest** — they drive collision rejection. Too small
   and pieces interpenetrate; too large and assembly fails needlessly.
7. **One `SIDE` pocket per world** — Biome Blueprint §6 checklist.
8. Run `./tests/run.sh`. The kit is validated at boot too; a broken kit stops
   the server rather than shipping a broken expedition.

---

## What is deliberately not built yet

- **The Roblox-side loader** — needs Phase 2 expedition entry to exist
- **Enemy population** — `EnemyTags` are declared but unconsumed
- **Pathfinding validation** (addendum §A4 step 4) — a spawn→boss reachability
  pass before letting players in. Collision rejection is not the same thing:
  two pieces can be non-overlapping and still not walkable between.
- **Terrain** — addendum §A3 wants voxel terrain for macro landscape with
  MeshParts for designed objects. Chunks currently assume MeshParts only.

---

## Adding a new world's kit

1. Author pieces in `assets/source/worlds/<world_id>/`
2. Add manifest entries (`PLACEHOLDER` is fine)
3. Add `src/shared/Content/Chunks/<World>.luau` returning a list
4. Run the tests

No System changes at any point. That is the prime directive holding:
**systems are reusable, content is data.**
