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

## 6. Open questions for this world

- **Which pieces offer `WIDE`?** See §3. Recommended: Grove, Ridge Overlook,
  Ruins.
- **`chunk_entry`'s opening faces south in the delivered art**, while content
  declares it north. One of the two has to move; the art is easier to keep and
  the data is easier to change.
- **`SIDE` pockets are never placed.** `IncludeSide` is declared and never read,
  so an optional branch cannot occur at all. Fern Hollow and Mushroom Glen are
  the natural side pockets for this world once it works.
