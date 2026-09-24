# Verdant Valley — biome design schema

**Rarity:** Common · **Roll weight:** 5000 (60% of the Phase 1 pool)
**Map route:** chunk kit · **Blueprint:** §3.2

The starting world and the one every player sees first. A sunlit temperate
forest valley — open meadows, a stream, dense groves — that reads as safe and
becomes less so toward the north. It is the world the onboarding arc returns to
between lifts, so it has to be pleasant to be in repeatedly rather than
striking once.

---

## 1. Palette and light

Lives in `Content/Worlds/VerdantValley.luau` → `Environment`. Blueprint §3.3:
soft midday, dappled canopy light.

| | |
|---|---|
| Ambient | `90, 100, 70` |
| Outdoor ambient | `120, 130, 100` |
| Sky shift | `150, 170, 120` |
| Fog | `180, 200, 160`, 100 → 400 |
| Brightness / clock | 2.5 · 13:00 |

Mesh materials in the delivered kit: `Verdant_Grass`, `Path_Stone`,
`Tree_Trunk`, `Canopy_Light`, `Canopy_Leaf`, `Wildflower`. Flat colour, no
textures — the house low-poly style in `ART_DIRECTION.md`.

**Modifiers:** `NORMAL` and `NIGHT`. Night re-tints; it does not build separate
geometry. This world's `ModifierOverrides` is the reference example.

---

## 2. The kinds of place

**This is the section that decides how varied a run feels**, and it is
deliberately open-ended. Twelve to sixteen distinct kinds of place is the
target. A new kind of place is welcome at any time and needs no permission —
it is a piece of content, and adding one changes no System.

Delivered in the 2026-09-22 test kit:

| Piece | What it is |
|---|---|
| `chunk_entry` | Arrival. Gentle, open, low threat |
| `chunk_path_straight` | Connective forest path |
| `chunk_meadow_a` · `chunk_meadow_b` | Open ground, long sightlines, pack fights |
| `chunk_grove` | Dense old trees, short sightlines |
| `chunk_stream_crossing` | Water, a crossing, banks to fight across |
| `chunk_fern_hollow` | Sunken, overgrown, enclosed |
| `chunk_mushroom_glen` | Strange and bright — the odd one in a normal forest |
| `chunk_ruins` | Something was here before you |
| `chunk_waterfall` | Landmark. Somewhere you remember passing |
| `chunk_ridge_overlook` | High ground, a view out over the rest |
| `chunk_boss_clearing` | The arena |

**Roles are a routing concept, not a design one.** Every piece carries one of
`ENTRY` / `PATH` / `COMBAT` / `SIDE` / `BOSS` so the assembler knows where it is
allowed to put it. That is all a role means. A ruin and a mushroom glen can both
be `COMBAT` and be nothing alike, and the world is more varied for it.

The only counts the engine insists on: **at least one `ENTRY`, at least one
`BOSS`**, and at least one connective piece. Everything else is free.

---

## 3. How pieces connect

Verdant Valley's connection types:

| Type | Meaning |
|---|---|
| `PATH` | An ordinary forest opening. The connective type — most pieces offer it |
| `WIDE` | A broad approach. **The arena accepts only this** |

Openings are centred on an edge midpoint and are 42–50 studs across in the
delivered kit. A piece may have an opening on any side it leaves open, and no
opening on a side the art closes.

### The consequence worth understanding

Because the arena accepts only `WIDE`, any piece that offers a `WIDE` exit
becomes a possible approach to the boss — and a piece offering `WIDE` is never
spent mid-path, because the assembler reserves arena types. Today the Grove is
the only `WIDE` provider, so **the Grove precedes the boss on every single
seed.** That was the intent when the kit was eight pieces and the Blueprint
called for Elder Treants gating the approach.

**With twelve pieces it is now the single largest limit on variety**, and the
fix is content: give `WIDE` to two or three pieces that deserve to be the last
thing before a boss — the Grove, the Ridge Overlook, the Ruins — and the
approach varies per run while still always being a deliberate one.

---

## 4. Inhabitants

`Content/Worlds/VerdantValley.luau` → `Enemies`, `BossId`.

| Enemy | Where it belongs |
|---|---|
| `MOSS_SLIME` | Entry, early path — the tutorial enemy |
| `THORN_GOBLIN` | Stream, hollow — camps and ambushes |
| `FOREST_WOLF` | Meadows — packs, open ground |
| `ELDER_TREANT` | Grove — slow, heavy, gates the approach |
| `ROOTBOUND_GUARDIAN` | Boss clearing |

Declared per piece as `EnemyTags`. **Nothing consumes them yet** — enemy
population is not built. The tags are the design being recorded ahead of the
system that will read them.

Loot `LOOT_VERDANT` · discoveries `DISC_VERDANT`.

---

## 5. Piece size and count

| | |
|---|---|
| Piece footprint | **256 × 256 studs**, uniform |
| Height | Free. Delivered kit runs 42–77 studs |
| Kit size | 12 delivered; 12–16 is the target |
| Path length | 5 (`GameConfig.Expedition.PathLength`) |

256 was arrived at by bracketing: an earlier iteration at ~100 studs read too
tight to be a place, and one at ~1024 was so open the scatter disappeared into
it. **It is a number in a content file and it is meant to move** if a real
piece reads wrong on the ground.

At 256 and path length 5 a map spans ~1536 studs — about 48 s of walking in a
720 s expedition, which is a lot of slack. `PathLength` is the knob and is worth
retuning once a real piece has been walked, not before.

---

## 6. What each piece can support

The scenario-compatibility gate (build spec §7.3). Deliberately not universal —
a traversal challenge in a flat meadow is not a challenge, and a mini-boss in a
corridor is not an arena.

| Piece | Supports |
|---|---|
| `VV_PATH_STRAIGHT` | Combat, Traversal, Ambush |
| `VV_MEADOW_A` | Combat, MiniBoss, Treasure, Ambush |
| `VV_MEADOW_B` | Combat, MiniBoss, Ambush, Shrine |
| `VV_STREAM_CROSSING` | Combat, Traversal, Ambush, Event |
| `VV_MUSHROOM_GLEN` | Combat, Shrine, Event, Secret, Puzzle |
| `VV_FERN_HOLLOW` | Combat, Puzzle, Treasure, Secret, Ambush |
| `VV_RUINS` | Combat, Puzzle, Treasure, MiniBoss, Secret, Event |
| `VV_WATERFALL` | Combat, Traversal, Secret, Shrine, Event |
| `VV_RIDGE_OVERLOOK` | Combat, Traversal, Ambush, Shrine, MiniBoss |

`VV_ENTRY` and `VV_BOSS_CLEARING` declare none and are never assigned a
scenario — arrival should be calm and the arena is already the biggest thing in
the run.

**Measured: 50 distinct chunk/scenario rooms from 11 pieces**, across 174
distinct layouts in 200 seeds.

---

## 7. Settled, and what is still open

### Settled 2026-09-22, when the kit was delivered

- **`WIDE` now sits on Ruins, Waterfall and Ridge Overlook.** The Grove was the
  only provider and did not survive the upload (14,448 triangles against a
  10,000 cap). Three providers keep the gate — the arena is still only
  approached deliberately — and the approach now varies ~35/35/30 per seed
  instead of being the same room every time.
- **The entry opens south.** The art decided; the data moved to match.
- **There is no side pocket, and there cannot be one yet.** Every delivered
  piece has exactly two openings, the critical path spends both, so no seed
  leaves a spare socket for a branch. Fern Hollow became a `COMBAT` piece.
  `Schema.validateChunks` now refuses a kit that declares `SIDE` without a
  3-socket piece, rather than letting a pocket validate and never appear.

### Still open

- **The Grove.** It needs decimating under 10,000 triangles and re-uploading.
  Its absence costs a kind of place, not a working kit.
- **A three-opening piece**, if this world is to have the optional branch
  Blueprint §6 asks for. A T-junction or a crossroads clearing. This is a
  request for the modeller, not a code change.
- **Encounter and reward configuration.** A plan says a room is an Ambush;
  nothing spawns it. Build spec §7 still excludes that.

---

## 8. The 30-piece base kit (2026-09-24)

The kit was redelivered as 30 pieces in one `.blend`, laid out 5 × 6. It is exported and wired by
`assets/source/worlds/verdant_valley/export_verdant_valley_kit.py`. That folder's
[`IMPORT_STEPS.md`](../../assets/source/worlds/verdant_valley/IMPORT_STEPS.md) has the piece table and upload steps.

- **The sockets were redone from the geometry.** The .blend's own socket labels put N on Blender −Y but E on +X.
  That is a mirror, not a rotation, so on the bends (Orchard, the six gates) no turn of the mesh could match them.
  The script ray-casts each edge for the flat mouth pad instead (48 studs wide = `PATH`, 52 = `WIDE`).
  It refuses to export if a measurement disagrees with its table.
  After the N/S flip, every piece's openings matched what the art intended.
- **Roles.** 2 ENTRY (Dawn Meadow, Woodland Refuge), 1 BOSS (Sanctuary, 384 × 256),
  1 CAP (Cave Mouth), 3 SIDE (Treasure Hollow, Warden's Clearing, Forgotten Trial),
  6 PATH, 17 COMBAT.
  **Six pieces offer `WIDE`**, so a run's arena approach is spread evenly between them.
  Five pieces are 3- or 4-way junctions, so side pockets now actually attach.
  That closes §7's "Verdant Valley cannot host a SIDE pocket".
- **Names follow `CHUNK_DROP_IN.md`** (`chunk_entry_*`, `chunk_side_*`, `chunk_cap_*`, `chunk_path_*`, `*_gate`),
  so the same FBX would also load as a drop-in kit.
  The hand-written module is kept because drop-in collapses every opening to one Kind,
  and that would lose the `WIDE` gate.
- **Engine contract, checked by the script:**
  - every footprint is exactly 256 (the boss 384 × 256), centred on the origin
  - every mouth sits at ground height 0 ± 0.35
  - 7,288–9,970 triangles per piece, under the 10k cap
  - material colours are baked to vertex colour (one mesh per piece)
  - `MeshYawOffset = 180`, the half turn Sky Citadel's identical export landed at;
    `calibrateYaw` measures the real turn per piece
- **Supports, EnemyTags and Weights are proposals.** They are read from each piece's theme and live in the script's `EXPECTED` table.
- 200/200 seeds assemble into 200 distinct layouts, and every one of the 30 pieces appears.
  **Not yet uploaded or walked in Studio.**

