# Ethereal Scape — biome design schema

The Uncommon world's art direction and its chunk kit.

> **Amendment 2026-09-26, owner-directed.** Ethereal Scape shipped as a
> `PrebuiltMap` — a single composed, hand-authored traverse
> (`assets/source/worlds/ethereal_scape/aether_environment_refined.blend`),
> explicitly a no-combat map-generation test rig (see that file's header and
> `Content/Worlds/EtherealScape.luau`'s prior header, both dated before this
> change). **That decision is superseded here.** The world now declares a
> **30-piece chunk kit**, the same shape of deliverable as Sky Citadel and
> Verdant Valley, and is opened to a drafted enemy roster. The original
> composed scene stays in the repo as the palette's source of truth (its
> materials are exactly what this kit is built to match) and as art reference,
> but is no longer what the world loads. `Schema.validateMaps` enforces that a
> world may declare a chunk kit or a `PrebuiltMap`, never both — see
> `Content/Worlds/EtherealScape.luau` for the data-side half of this change.

| | |
|---|---|
| Content | `src/shared/Content/Worlds/EtherealScape.luau`, `Content/Chunks/EtherealScape.luau` |
| Generator | `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py` |
| Exports | `assets/export/worlds/ethereal_scape/chunk_*.fbx` |
| Palette reference | `assets/source/worlds/ethereal_scape/aether_environment_refined.blend` |
| Enemies | `assets/source/enemies/ethereal_scape/` (`ROSTER.md`, `manifest.py`) |
| Contract | [`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](../MODULAR_MAPS.md), [`ENEMY_FRAMEWORK.md`](../ENEMY_FRAMEWORK.md) |

---

## The look

**A sky temple standing above the cloud deck, on meadow islands rather than
machined decks.** Where Sky Citadel is octagonal, chamfered and vertical,
Ethereal Scape is **round and organic** — islands read as ground that happened
to come loose, not architecture that was built to float. Nothing here is a
castle; the temple at the world's heart is the one exception, and even it is
ivory and gold rather than white and violet.

It must not read as a paler Sky Citadel (that world's own doc states the same
rule in reverse):

| | Ethereal Scape | Sky Citadel |
|---|---|---|
| What stands there | shrines and a temple on meadow islands | a castle on machined decks |
| Ground | mint grass, gold soil, cloudstone flagstone | white deck plate, no soil at all |
| Warm accent | temple gold, generously | sun gold, sparingly |
| Glow | portal glow, soft, round | azure seams, crisp and linear |
| Shape language | round, organic, grown | octagonal, chamfered, machined |
| Colour contrast | ivory and mint green | white and violet |

### The palette

Source of truth: the materials already named in
`Content/Worlds/EtherealScape.luau`'s header, read off
`aether_environment_refined.blend`. The generator uses exactly these — nothing
invented that the original scene didn't already establish.

| Role | Used for |
|---|---|
| `AetherMintGrass` | meadow floors, the world's green |
| `PaleGoldSoil` | bare soil, path shoulders |
| `GoldenPath` | ceremonial paved road floor |
| `CloudWhite` | temple stone, balustrades, cloudstone |
| `Cloudstone` | flagstone yards, cliff faces |
| `DeepTealLeaves` | tree canopies, hedges |
| `IndigoLeaves` | the cooler half of every canopy, moss |
| `TempleIvory` | temple walls, shrines, waystones |
| `TempleGold` | temple trim, rails, finials — the one warm accent |
| `SkyCrystal` | floating crystals, the one glass material |
| `PortalGlow` | emissive: portal arches, waystone runes, aether motes |

Flat shaded, `SmoothPlastic`, no textures — same house rule as every other
world. `PortalGlow` is the only `Neon` role, kept small (arches, rune lines,
motes) so bloom reads as a glow, not a wash.

### The set-dressing vocabulary

| Prop | Reads as | Scale |
|---|---|---|
| Waystone | a squat ivory pillar with a glowing rune band | 24 tall (measured off the original scene) |
| Portal arch | two curved ivory piers meeting at a keystone, `PortalGlow` filling the gap | 30 tall, 18 clear |
| Temple finial | a slim gold spike on a stepped ivory base | reaches the +160 crown |
| Shrine bell | a small gold bell under a four-post ivory canopy | 12 |
| Sky crystal cluster | 3–5 glass shards at varied angles, one always tallest | 6–24 |
| Aether mote ring | a slow ring of small glowing points orbiting a centre | 4–10 radius |
| Root-tangle keel | a braided under-hang (the same braid language as Verdant Valley's Rootbound Warden — this world's islands are grown, not built) | hangs to z = −96 |
| Sky tree | a teal/indigo canopy on an ivory-pale trunk | 20–34 |
| Reflecting pool | a shallow `CloudWhite` basin, flush with the floor | flush |
| Hedge | clipped `DeepTealLeaves` wall | 2.4 |
| Balustrade | ivory posts, a gold rail | 3.4 waist |
| Vine trellis | thin gold lattice with hanging `IndigoLeaves` | 3.2 waist |
| Cloud-wisp base | the island's edge simply fades — no visible keel, mist geometry instead | — |

---

## The connection vocabulary

Decided before modelling, per `CHUNK_AUTHORING.md` → *Starting a different
world*. Deliberately disjoint from Sky Citadel's `SKYWAY`/`ASCENT` and Verdant
Valley's `PATH`/`WIDE` — a test asserts every world's kind set is disjoint
from every other's.

| Kind | Role | Width | Ground | What it looks like |
|---|---|---|---|---|
| `SPAN` | connective | **44** | z = 0 | a plank-and-stone causeway, low ivory curb, portal-glow edge line |
| `COMMUNION` | arena-only | **64** | z = 0 | a ceremonial gold-paved approach, waystones either side, no rail |

Only the two **Temple Gate** pieces offer a `COMMUNION` exit, and the Sanctum
arena accepts nothing else — the same reserved-Kind pattern Sky Citadel's gate
courts and Verdant Valley's Grove use, so a gate always precedes the arena on
every seed without any code hard-coding it.

Every opening's floor runs to the tile edge at z = 0, so two pieces meet floor
to floor; an opening with nothing attached reads as a causeway continuing into
the mist.

---

## Piece size and count

| | |
|---|---|
| Piece footprint | **256 × 256 studs**, uniform (the Sanctum arena: 320 × 256) |
| Height | **256**: floor at 0, keel to −96, crown pin to +160 — same box convention as Sky Citadel and Verdant Valley, so `ChunkLoader`'s size/pivot handling needs no per-world branch |
| Kit size | **30 pieces** |
| Path length | 5 (matches Verdant Valley; retune once walked) |

---

## The kit — 30 pieces

Built from the same five-axis pattern Sky Citadel's kit uses, so no two pieces
read alike even though every piece draws from one small vocabulary:

| Axis | Options |
|---|---|
| **Shape** | one meadow island · an archipelago of islets on short plank bridges · a bare crystal-arch span, no deck · floating aether stepping-stones |
| **Floor** | mint grass · gold soil · golden ceremonial path · cloudstone flagstone · indigo moss · temple ivory tile · starfield inlay · portal-glow ring inlay |
| **Edge** | ivory curb with crystal studs · gold vine trellis · temple balustrade · clipped hedge · nothing (sheer, a glow line only) |
| **Keel** | root-tangle hang · crystal stalactite cluster · cloud-wisp fade (no visible keel) · temple foundation blocks · hovering aether-mote ring |
| **Landmark** | waystone · temple finial · portal arch · sky tree · crystal obelisk · shrine bell tower · aether beacon (slow pulsing orb) |

Every landmark reaches exactly +160.

| Id | Role | Openings | Shape | Floor | Edge | Keel | Landmark |
|---|---|---|---|---|---|---|---|
| `ES_ENTRY` | ENTRY | N `SPAN` | one island | gold soil | ivory curb | temple blocks | waystone |
| `ES_PATH_STRAIGHT` | PATH | N S `SPAN` | archipelago, 2 islets | mint grass | balustrade | root-tangle | sky tree |
| `ES_PATH_ARCWAY` | PATH | N S `SPAN` | bare span | — | nothing | crystal stalactite | portal arch |
| `ES_PATH_STEPPING` | PATH | N S `SPAN` | stepping-stones | cloudstone | nothing | mote ring | crystal obelisk |
| `ES_PATH_BEND_EAST` | PATH | S E `SPAN` | one island | golden path | hedge | root-tangle | waystone |
| `ES_PATH_BEND_WEST` | PATH | S W `SPAN` | one island | indigo moss | trellis | cloud-wisp | shrine bell |
| `ES_PATH_LANTERN_ROW` | PATH | N S `SPAN` | archipelago, 3 islets | gold soil | curb | temple blocks | portal arch |
| `ES_CONVERGENCE` | PATH | N S E W `SPAN` | one island, 4 mouths | starfield inlay | balustrade | mote ring | aether beacon |
| `ES_PATH_ORCHARD` | PATH | N S `SPAN` | one island | indigo moss | hedge | root-tangle | sky tree |
| `ES_MEADOW_BLOOM` | COMBAT | N S `SPAN` | one island | mint grass | nothing | cloud-wisp | waystone |
| `ES_MEADOW_TERRACE` | COMBAT | N S `SPAN` | two raised terraces | mint grass, gold soil | curb | temple blocks | sky tree |
| `ES_CRYSTAL_GROVE` | COMBAT | N S `SPAN` | one island | cloudstone | nothing | crystal stalactite | crystal obelisk |
| `ES_WAYSTONE_RING` | COMBAT | N S `SPAN` | one island, ring layout | golden path | ivory curb | temple blocks | waystone (×3, one central) |
| `ES_CLOUDSTONE_YARD` | COMBAT | N S `SPAN` | one island | cloudstone | balustrade | temple blocks | shrine bell |
| `ES_HANGING_GARDEN` | COMBAT | N S `SPAN` | terraced archipelago | indigo moss | trellis | root-tangle | sky tree |
| `ES_SHRINE_COURT` | COMBAT | N S `SPAN` | one island | temple ivory tile | balustrade | temple blocks | shrine bell |
| `ES_AETHER_FALLS` | COMBAT | N S `SPAN` | two raised terraces | portal-glow inlay | curb, open one rim | crystal stalactite | portal arch |
| `ES_SKY_ORCHARD` | COMBAT | N S `SPAN` | one island, larger | indigo moss | hedge | root-tangle | sky tree (×2) |
| `ES_MIRROR_POOL` | COMBAT | N S `SPAN` | one island, flush pool | temple ivory tile | nothing | cloud-wisp | aether beacon |
| `ES_RELIQUARY_COURT` | COMBAT | N S `SPAN` | one island | temple ivory tile | temple balustrade | temple blocks | portal arch |
| `ES_STARFIELD_TERRACE` | COMBAT | N S `SPAN` | raised terrace | starfield inlay | curb | mote ring | crystal obelisk |
| `ES_TEMPLE_GATE_A` | COMBAT (gate-court) | S `SPAN` · N `COMMUNION` | one island | golden path | temple balustrade | temple blocks | twin waystones |
| `ES_TEMPLE_GATE_B` | COMBAT (gate-court, rare) | S `SPAN` · N `COMMUNION` | one island, larger | golden path | temple balustrade | temple blocks | portal arch |
| `ES_SIDE_OVERLOOK` | SIDE | S `SPAN` | small island | cloudstone | balustrade | cloud-wisp | waystone |
| `ES_SIDE_HERMITAGE` | SIDE | S `SPAN` | small island | indigo moss | hedge | root-tangle | shrine bell |
| `ES_SIDE_TREASURY` | SIDE | S `SPAN` | small island | temple ivory tile | ivory curb | temple blocks | crystal obelisk |
| `ES_CAP_UNFINISHED_SPAN` | CAP | S `SPAN` | bare span, breaks off | — | nothing | crystal stalactite (broken) | — |
| `ES_CAP_OVERLOOK` | CAP | S `SPAN` | small island | cloudstone | balustrade | temple blocks | aether beacon |
| `ES_CAP_SEALED_SHRINE` | CAP | S `SPAN` | one island | temple ivory tile | temple balustrade | temple blocks | shrine, doors shut |
| `ES_SANCTUM` | BOSS | S `COMMUNION` | round arena, 320×256 | golden path, ring inlay | temple balustrade | temple blocks | temple finial |

| Role | Pieces | Notes |
|---|---|---|
| ENTRY | 1 | always the first piece |
| PATH | 8 | includes the Convergence (4-way, so a SIDE pocket has somewhere to attach) |
| COMBAT | 14 | 2 are gate-courts offering `COMMUNION` |
| SIDE | 3 | optional branch, `IncludeSide` |
| CAP | 3 | authored endings — a span that stops mid-construction, a viewpoint, a shrine that stays sealed |
| BOSS | 1 | the Sanctum, always last, `COMMUNION`-only |

---

## Enemy roster (drafted here; not yet wired to `Content/Enemies`)

**Same universal rules as every other world's roster** — `ENEMY_FRAMEWORK.md`'s
tier budgets (basic 10,000–12,500 tris, miniboss ≤35,000, boss ≤75,000),
rig rules (R15 core bones; minibosses and bosses get finger bones), and the
flyer rule (a flyer must regularly come into sword range — the player's
weapon is the damage source, no arena tools). Full roster and build status:
`assets/source/enemies/ethereal_scape/ROSTER.md`.

Declared per piece as `EnemyTags` in `Content/Chunks/EtherealScape.luau`, the
same "recorded ahead of the system that reads it" pattern Verdant Valley
uses — **nothing consumes them yet**; enemy population and `Content/Enemies`
entries are Phase 2/3 work (build spec §7.6, reserved).

| Enemy (concept) | Tier | Where it belongs |
|---|---|---|
| `AETHER_WISP` | Basic | Entry, early path — drifts, light hit-and-run, the tutorial enemy |
| `TEMPLE_ACOLYTE` | Basic | Shrine Court, Reliquary — chants a slow ranged bolt, breaks on approach |
| `MEADOW_STAG` | Basic | Meadow Bloom, Sky Orchard — charges, packs of two or three |
| `CRYSTAL_WARDEN` | Basic | Crystal Grove — tanky, slow, shatters into shards on death |
| `SKYBORNE_HARRIER` | Basic | archipelago/bend pieces — flyer, dives then lands to stalk (same flyer contract as Sky Citadel's Aviary Harrier) |
| `WAYSTONE_SENTINEL` | Miniboss | Waystone Ring |
| `RELIQUARY_KEEPER` | Miniboss | Reliquary Court |
| `GATEWARDEN` | Miniboss | either Temple Gate |
| `THE_ASCENDANT` | Boss | the Sanctum |

`AETHER_WISP` and `SKYBORNE_HARRIER` deliberately echo Sky Citadel's Lantern
Wisp and Aviary Harrier roles (hover-melee, diver) — same archetype, this
world's palette — so `docs/ENEMY_FRAMEWORK.md`'s shared-Studio-behaviour
`role` ids need no new cases.

---

## Next

1. Build the kit (`build_ethereal_scape_kit.py`), validate bbox/tri/flat-shade per piece, render a review grid.
2. Hand pass (`CHUNK_AUTHORING.md`): floating objects, clipping, scale, edges, origin — the same five checks every kit gets before it is considered a first pass.
3. Build 1–2 roster enemies to prove the palette translates from environment to character.
4. Walk it once uploaded — nothing here has been seen in Studio yet, same caveat every kit starts with.
