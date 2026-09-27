# Ethereal Scape — biome design schema

The Uncommon world's art direction and its chunk kit.

> **History.** Ethereal Scape shipped as a `PrebuiltMap`: one composed, hand-authored,
> no-combat traverse (`aether_environment_refined.blend`). On 2026-09-26 it became a 30-piece
> chunk kit (PR #131). The owner then rejected that first kit on sight: every piece was missing
> its platform (a geometry bug), it was bland, and it reused Sky Citadel's shape and design
> language (needle "waystones", obelisks, floating octagon-ish decks). **This document describes
> the revamp that replaced it, the same day.** The original scene stays in the repo as the
> palette's source of truth and as art reference.

| | |
|---|---|
| Content | `src/shared/Content/Worlds/EtherealScape.luau`; `Content/Chunks/EtherealScape.luau` and `Content/Props/EtherealScape.luau` (both **generated**) |
| Generator | `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py` + `es_geometry.py`, `es_features.py`, `es_pieces.py`, `es_props.py` |
| Exports | `assets/export/worlds/ethereal_scape/ethereal_scape_structure.fbx` (30 objects), `ethereal_scape_props.fbx` (8 prop kinds) |
| Review renders | `assets/source/worlds/ethereal_scape/renders/` — a hero and a ground shot per piece, the Sanctum's interior, `preview_chain.jpg`, `kit_overview.jpg` |
| Palette reference | `assets/source/worlds/ethereal_scape/aether_environment_refined.blend` |
| Enemies | `assets/source/enemies/ethereal_scape/` (`ROSTER.md`, `manifest.py`) |
| Contract | [`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](../MODULAR_MAPS.md) |

```
blender -b --factory-startup --python assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- --export --render
```
The `.blend` is an output. Edit the scripts.

---

## Floating or grounded? Grounded, on walkable cloud

The owner asked for this to be decided on purpose, so every biome feels different.

| World | The ground |
|---|---|
| Verdant Valley | a grounded forest valley |
| Sky Citadel | machined castle islands hanging over a cloud sea, with a void between them |
| **Ethereal Scape** | **walkable cloud.** The cloud *is* the ground. The original scene's meadow islands become **mesas** rising out of it, clearings are walled by billowing cloud banks, and the only voids are deliberate ones (a rift, a bridge that snaps) |

Making it float again would have been a second Sky Citadel however different its props. Walking
*on* the clouds keeps the original art's DNA: meadow islands, gold rims, the temple. It also
gives the world its own feel: soft, rolling and dreamlike, where Sky Citadel is crisp and
precipitous. The flavour line still fits: *"The ground is a courtesy, and it ends."*

## The look — and how it differs from Sky Citadel

Read off the original scene, not invented:

| | Ethereal Scape | Sky Citadel |
|---|---|---|
| Ground | walkable cloud, meadow carpets, meadow **mesas** with a **gold rim band** and faceted rock flanks | white machined deck plate over a void |
| Verticality | gem-cut **trees**, ancient **great sky trees**, **crystal colossi**, broad rock **crags**, square **bell towers**, the columned **temple** | needle spires with neon halos |
| Architecture | classical: ivory columns with gold bases and capitals, pavilions with gold hip roofs, arches of voussoirs, squat rune **waystones**, broken colonnades | futurist: octagonal, chamfered turrets and gates |
| Glow | portal **purple**, small and round (rune bands, lantern cores, blossoms, seals) | azure seams, linear |
| Air | cloud puffs, sky lanterns, crystal shards, satellite isles, **skyrays** | birds, halos, hoops, beacons |

### The palette — the original's real values

The first kit guessed pale tones. These are read off the scene's materials (sRGB):

| Material | RGB | Used for |
|---|---|---|
| `AetherMintGrass` | 79, 148, 115 | meadow carpets, mesa tops, grass |
| `CloudWhite` | 212, 224, 235 | the cloud floor, banks, billows |
| `Cloudstone` | 107, 122, 140 | mesa flanks, crags, stone bases |
| `DeepTealLeaves` | 20, 59, 51 | tree crowns |
| `GoldenPath` | 209, 184, 87 | roads, landings, plaza mosaics, plank decks |
| `IndigoLeaves` | 31, 41, 92 | the cooler crowns, the skyray's back |
| `PaleGoldSoil` | 189, 171, 82 | soil, flagstone seams, strata |
| `PortalGlow` | 94, 46, 178 | the one Neon role: rune bands, lantern cores, seals, blossoms |
| `SkyCrystal` | 46, 168, 235 | crystals, windows, pools, aether falls |
| `SoftWood` | 77, 56, 31 | trunks, planks, posts, roof ribs |
| `TempleGold` | 184, 133, 38 | rims, capitals, roofs, trim |
| `TempleIvory` | 194, 191, 158 | columns, walls, waystones, balustrades |

---

## The connection vocabulary

Disjoint from Sky Citadel's `SKYWAY`/`ASCENT` and Verdant Valley's `PATH`/`WIDE`. A test
asserts it.

| Kind | Role | Width | What arrives at the edge |
|---|---|---|---|
| `SPAN` | connective | **44** | a golden flagstone landing, exactly 44 wide, level at z = 0, flanked by two squat guide stones |
| `COMMUNION` | arena-only | **64** | the same landing at 64. Only the two Temple Gates offer one, so a gate always precedes the Sanctum |

**Every mouth is identical at the edge**, whatever the piece does inside, so any two pieces meet
flagstone to flagstone. Cloud banks always leave the mouth and 17 studs either side open.

## Piece size

- Standard tiles are **256 × 256**. The box is always 256 tall: keel −96, crown +160, walk plane at 0, `GroundOffsetY = 96`.
- **Spawn and boss are bigger**, as the owner allowed, as long as their mouths are standard:
  - the **Entry is 384 × 384**;
  - the **Sanctum is 512 × 512**.
- The assembler collision-checks each piece's own `SizeX`/`SizeZ`.

---

## The kit — 30 pieces

| Role | Count | Pieces |
|---|---|---|
| ENTRY | 1 | **Arrival Meadow** (384): gold mosaic landing ringed by crystal-topped spawn columns; the original's shrine pavilion on a mesa; a great sky tree; the sky above the landing and the south return-portal pad kept clear (both checked) |
| PATH — straights | 5 | **Meadow Walk** (lantern-lined road, tree mesa) · **Ruin Stair** (up onto a temple terrace, under a colossal ruined gate, down again) · **Rift Bridge** (a gold plank bridge over a torn rift in the cloud, a crag rising out of it) · **Crystal Field** (clusters under a crystal colossus) · **Lily Terraces** (low mesas stepping away, a crag on the highest) |
| PATH — bends | 4 | **Grove Bend** E (ancient grove, fairy ring) · **Terrace Bend** E (bell-tower mesa up a lantern ramp) · **Shrine Bend** W (waystone-ringed pavilion, bell tower) · **Falls Bend** W (**Aether Falls**: a mesa rim spills glowing water into a pool) |
| PATH — **intersections** | 3 | **Wayshrine Fork** (3-way: waystone circle, signpost, great tree) · **Three-Trees Fork** (3-way: three ancient trees, a mushroom ring) · **Convergence** (4-way: compass court, fountain, eight lanterns) |
| COMBAT | 10 | Meadow of Blooms · Terraced Gardens (two garden mesas, soil rows, crag) · Crystal Hollow (pool in a ring of crystals) · Fallen Colonnade (temple floor, half-fallen colonnade, bell tower) · Mirror Pool (balustraded pool on stepping stones) · Shrine of Winds (three pavilions round an orb altar) · Rooted Hollow (a great tree's roots arch over the path) · Twin Mesas (a high plank bridge over the path) · **Temple Gate A** (bell towers flank the arch over the `COMMUNION` road) · **Temple Gate B** (rare: a columned, roofed gate hall the road passes through) |
| SIDE | 3 | Hermit Grove (a hut under a great tree) · Crystal Grotto · Relic Altar |
| CAP | 3 | **Broken Bridge** (the plank bridge snaps over a rift; a lone crag in the void) · **Overlook** (balustraded mesa lookout, a sky seat) · **Sealed Shrine** (a door sealed in a crag's face, its seal glowing) |
| BOSS | 1 | **The Sanctum** (512): see below |

### The Sanctum — a structure that houses the boss

- **Approach:** the `COMMUNION` road leads between processional lanterns and meadow gardens to a ceremonial stair.
- **The temple:**
  - it stands on a podium, 276 × 264;
  - a **portico** of six columns carries an entablature and a pediment with a purple glow medallion;
  - walls of pilasters alternate with **crystal windows** set right through the wall, lit inside and out;
  - a **great door** 64 wide and 44 tall leads in.
- **Inside:**
  - an **open hall**, about 240 × 230 by 58 tall, with nothing standing in it (checked);
  - a ring mosaic floor and a low dais at the north end;
  - a ribbed roof around a central **lantern**: a crystal-windowed clerestory under a gold hip roof.
- **Corners:** four **towers** with gold cones, whose crystal tips pin the +160 crown.

`renders/es_sanctum_interior.jpg` is the hall from just inside the door.

---

## The atmosphere (props, `CHUNK_AUTHORING.md` convention 6)

Nothing that drifts or flies is baked into a chunk. It is one library mesh per kind, plus
placements in `Content/Props/EtherealScape.luau`.

| Prop | Anim | Where |
|---|---|---|
| `prop_es_cloud_a`, `prop_es_cloud_b` | Float | high over every clearing (70–125 studs; low clouds hung over the paths like rocks) |
| `prop_es_lantern` | Float | sky lanterns rising over shrines, gates, forks, the arrival and the arena |
| `prop_es_shard` | Hover | crystal pieces and the falls |
| `prop_es_isle_grove`, `_crystal`, `_ruin` | Float | satellite islets in the tile's outer sky, 100–150 up |
| `prop_es_skyray` | Bird | manta-like gliders circling each clearing — this world's flyer, not Sky Citadel's birds |

Every placement is proven clear of the piece's **real mesh** (BVH), at least 4 studs inside the
tile and clear of every other prop. **A skyray's whole orbit** is proven clear, not just its
resting point (48 samples round the circle).

---

## Validation — what `build_ethereal_scape_kit.py` refuses to export

The first kit "passed" with no floors because it only checked the box. These are checked now,
on the real mesh, for every piece:

1. **Box** exactly (2H × 2H) × 256, centred, keel −96, crown +160.
2. **Under 10,000 triangles.** The heaviest pieces are the Sanctum (~9.9k), the Entry (~9.8k) and the Rift Bridge (~9.7k).
3. **No degenerate faces.** `mesh.validate()` dropping anything fails the piece.
4. **Walk graph.** This builds a 2-stud heightfield of every walkable surface, with 1.6-stud steps and 5 studs of headroom. It floods from one mouth, and **every other mouth must be reached**.
5. **Mouths:** level ground at z = 0 across at least 95% of the width.
6. **Nothing detached.** Sky Citadel's real-mesh `geometry_checks.analyse` is reused.
7. **No clipping between builders** (a tree through a pavilion, a crystal through a railing). Soft things (cloud, grass, blossom) may lap over anything. A short list of authored joints is allowed (a stair set against its podium).
8. **Entry:** the column above the landing and the return-portal pad are open to the sky.
9. **Sanctum:** the hall and the great door are unobstructed.

Every feature registers a **keep-out** footprint, so scattered trees, mushrooms and blossoms never
land in a pavilion, a tower or a crag. The first revamp pass logged about 40 clip notes; all are fixed.

Rebuilds are deterministic: seeds come from a crc32 of the piece name, and two runs diff identical.

---

## Enemy roster

Unchanged. See `assets/source/enemies/ethereal_scape/ROSTER.md`. Declared per piece as
`EnemyTags`; nothing consumes them yet (build spec §7.6).

## Next

1. **Upload and walk it in Studio.** Nothing here has been seen in Studio yet. Measure one piece and confirm vertex colour survives.
2. Tune the cloud floor's look under the world's real lighting. Review renders use flat Workbench shading, which greys `CloudWhite`.
3. Fixtures (chests on the Treasury / Relic Altar, a vault) were not in this pass.
