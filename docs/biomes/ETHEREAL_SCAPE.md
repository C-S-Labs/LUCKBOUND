# Ethereal Scape — biome design schema

The Uncommon world's art direction and its chunk kit.

> **History.** Ethereal Scape shipped as a `PrebuiltMap` (one hand-authored traverse,
> `aether_environment_refined.blend`). On 2026-09-26 it became a 30-piece chunk kit, was rejected (no platforms,
> too close to Sky Citadel), and was revamped as a grounded cloudscape. On 2026-09-27 the owner still wasn't sold,
> reviewed three direction samples (`renders/samples/`) and chose **the hybrid**. **This document describes the
> hybrid kit.** The original scene stays in the repo as the palette's source of truth.

| | |
|---|---|
| Content | `src/shared/Content/Worlds/EtherealScape.luau`; `Content/Chunks/EtherealScape.luau` and `Content/Props/EtherealScape.luau` (both **generated**) |
| Generator | `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py` + `es_geometry.py`, `es_features.py`, `es_isles.py` (island web), `es_pieces.py` (36 recipes), `es_props.py`, `es_mapgen.py` (preview assembler), `es_samples.py` (the three direction samples, `--samples`) |
| Exports | `assets/export/worlds/ethereal_scape/ethereal_scape_structure.fbx` (30 objects), `ethereal_scape_props.fbx` (8 prop kinds) |
| Review renders | `assets/source/worlds/ethereal_scape/renders/` — a hero and a ground shot per piece, the Sanctum's interior, `preview_chain.jpg`, `kit_overview.jpg`, and **`map_preview.jpg` / `map_preview_top.jpg`** — a whole seeded map assembled by the §7.7 scheme (also in the `.blend` as the `MAP_PREVIEW` collection) |
| Palette reference | `assets/source/worlds/ethereal_scape/aether_environment_refined.blend` |
| Enemies | `assets/source/enemies/ethereal_scape/` (`ROSTER.md`, `manifest.py`) |
| Contract | [`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](../MODULAR_MAPS.md) |

```
blender -b --factory-startup --python assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py -- --export --render
```
The `.blend` is an output. Edit the scripts.

---

## Direction: the hybrid (owner pick, 2026-09-27)

| Sample | Became |
|---|---|
| **A · Floating Isles** | **the base.** Every walkable surface is an isle hung in open sky: meadow top, the original's gold rim band, three jagged tiers of rock underneath, hanging roots, a crystal chandelier out of the tip. Isles are joined by gold plank bridges |
| **C · Temple City** | the architecture of the combat rooms, both miniboss arenas and the Sanctum: ivory flagstone courts, colonnades, shrine halls, statues, bell towers, arches |
| **B · Lush Cloudscape** | the dressing ON the isles: meadow carpets, groves, blossoms, mushrooms, pools, falls |

How it stays unlike its neighbours: Verdant Valley is grounded forest; Sky Citadel is machined deck plate and
needle spires over a void. Ethereal Scape's isles are organic, gold-rimmed and rooted, its waymarks are stout
**aether beacons** (stepped pagodas crowned in crystal — the needle spires of the first hybrid pass read as Sky
Citadel and were replaced), and its architecture is classical.

**Height variation.** Isles inside a piece stand at their own heights (terraces, perches, sunken pool isles) and
a piece's **mouths** may too — a socket's `OffsetY` is its height, so the map climbs and falls: the Skystairs
(±24), the ascent/descent bends (±16), the Twin-Span fork (+10), terraced gardens and twin isles inside pieces.
Bridges between heights climb at most ~37°, span edge to edge, and lie level on each isle top.

## The look — and how it differs from Sky Citadel

Read off the original scene, not invented:

| | Ethereal Scape | Sky Citadel |
|---|---|---|
| Ground | organic **floating isles**: meadow tops, a **gold rim band**, faceted rock undersides with roots and crystal chandeliers, joined by gold plank bridges | white machined deck plate over a void |
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
| `SPAN` | connective | **44** | a golden flagstone landing isle, exactly 44 wide, level at its socket's height, flanked by two squat guide stones |
| `COMMUNION` | arena-only | **64** | the same landing at 64. Only the two Temple Gates offer one, so a gate always precedes the Sanctum |

**Every mouth is identical at the edge**, whatever the piece does inside, so any two pieces meet
flagstone to flagstone, at any height.

## Piece size

- Standard tiles are **256 × 256**. The box is always 256 tall: keel −96, crown +160, walk plane at 0, `GroundOffsetY = 96`.
- **Spawn and boss are bigger**, as the owner allowed, as long as their mouths are standard:
  - the **Entry is 384 × 384**;
  - the **Sanctum is 512 × 512**.
- The assembler collision-checks each piece's own `SizeX`/`SizeZ`.

---

## The kit — 41 pieces

| Role | Count | Pieces |
|---|---|---|
| ENTRY | 1 | **Arrival Isle** (384): a great chamfered isle — gold mosaic landing ringed by crystal-topped spawn columns, the return-portal pad (kept clear, checked), a shrine terrace, the great sky tree, two perches at +14 and −16 |
| PATH — straights | 5 | **Sky Aqueduct** (384 landmark: a stone aqueduct across open sky on three piers and arcades, a water channel spilling mid-span) · **Plank Crossing** (three isles on plank bridges, the middle one raised) · **Grove Isle** (a great tree, a fairy ring, falls off the rim) · **Skystair Up** (+24) · **Skystair Down** (−24) |
| PATH — bends | 4 | **Grove Bend** E (great tree on a raised perch) · **Ascent Bend** E (+16, bell tower over the mouth, hut perch) · **Falls Bend** W (−16, aether falls) · **Shrine Bend** W (shrine hall, waystone arc) |
| PATH — junctions | 4 | **Wayshrine Fork** (S/E/W) · **Three-Trees Fork** (S/N/E) · **Twin-Span Fork** (S/N/W, north mouth +10) · **Convergence** (4-way). §7.7 fills every one of their mouths |
| COMBAT | 11 | **Sky Observatory** (384 landmark: a domed colonnade on a podium, an armillary sphere at the crown, the great telescope) · Meadow of Blooms · Terraced Gardens (+10/+20) · Crystal Hollow · Fallen Colonnade (temple) · Mirror Pool (temple) · Shrine of Winds (temple) · Rooted Hollow · Twin Isles (+12) · **Temple Gate A** · **Temple Gate B** (the only `COMMUNION` exits) |
| **MINIBOSS** | 2 | **Waystone Ring** (the Waystone Sentinel: eight waystones round a gold ring, twin beacons, a gallery perch) · **Reliquary Court** (the Reliquary Keeper: a balustraded temple court before the reliquary hall). One mouth each; only ever at the end of a branch — **never the boss arena** |
| SIDE | 3 | Hermit Grove · Crystal Grotto · Relic Altar |
| CAP | 4 | Broken Bridge · Overlook · Sealed Shrine · Falls Ledge |
| BOSS | 1 | **The Sanctum** (512), on the greatest isle in the sky: see below |
| **BACKDROP** | 6 | **Cloudbank** · **Cloud Shelf** · **Cloud Drift** · **Storm Anvil** — each a seeded arrangement of drifting cloud *props* · Drift Isles · Crystal Spire. No sockets, never walked — the generator rings them round the finished map and turns each one |

## Generation — build spec §7.7

The world declares `Generation = { BranchLength = 2, Minibosses = 1, MaxSides = 2, Backdrop = 18 }`. The
critical path is unchanged (ENTRY → 5 pieces → a Temple Gate → the Sanctum). Then every spare mouth of every
piece grows a branch of up to 2 pieces, and every branch **ends** — in a miniboss arena (one per map), a side
pocket, or a cap; nothing opens onto sky. Last, up to 18 backdrop pieces fill the free cells round the map.
Sky Citadel and Verdant Valley declare no blueprint and assemble exactly as before.

### The Sanctum — a structure that houses the boss

- **Approach:** the `COMMUNION` road crosses from the landing onto the isle and runs between processional lanterns, statues and meadow gardens to a ceremonial stair.
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

- **Interior (detail pass 2026-09-27):** engaged pilasters, crystal sconces, guardian statues, a patterned floor
  border, a coffered gold ceiling with four crystal chandeliers, a crystal ring hung in the lantern, a three-step
  throne dais with a crystal-crested throne and braziers, a gold sun disc on the north wall, open door leaves.
  All outside the validated fight volume.

`renders/es_sanctum_interior.jpg` is the hall from just inside the door.

---

## The atmosphere (props, `CHUNK_AUTHORING.md` convention 6)

Nothing that drifts or flies is baked into a chunk. It is one library mesh per kind, plus
placements in `Content/Props/EtherealScape.luau`.

| Prop | Anim | Where |
|---|---|---|
| `prop_es_cloud_a`, `prop_es_cloud_b` | Float | soft billowed puffs and wisps, high over every clearing |
| `prop_es_cumulus_a/b/c` | Float | towering cumulus, a long shelf, an anvil — arranged by the cloudbank BACKDROP pieces, smooth-shaded |
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
2. **Under 10,000 triangles.** The hybrid is far lighter: the heaviest are the Sanctum and the Entry (~7k).
3. **No degenerate faces.** `mesh.validate()` dropping anything fails the piece.
4. **Walk graph.** This builds a 2-stud heightfield of every walkable surface, with 1.6-stud steps and 5 studs of headroom. It floods from one mouth, and **every other mouth must be reached**.
5. **Mouths:** level ground at the socket's own height across at least 95% of the width.
6. **Nothing detached.** Sky Citadel's real-mesh `geometry_checks.analyse` is reused.
7. **No clipping between builders** (a tree through a pavilion, a crystal through a railing). The ground (isle tops, landings) may be stood in. `declip()` removes any cloud, blossom, grass or mushroom that touches a real object (a mushroom's stem and cap go together). A short list of authored joints is allowed (a porch column in its podium). The final build logs **zero** clip notes.
8. **Grounded:** every column, tower, waystone, statue, beacon, lantern, brazier and orrery stands on ground — rays cast under its base must meet a surface at 4 of 5 points.
9. **Entry:** the column above the landing and the return-portal pad are open to the sky.
10. **Sanctum:** the hall and the great door are unobstructed.

Every feature registers a **keep-out** footprint, so scattered trees, mushrooms and blossoms never
land in a pavilion, a tower or a crag. The first revamp pass logged about 40 clip notes; all are fixed.

Rebuilds are deterministic: seeds come from a crc32 of the piece name, and two runs diff identical.

---

## Enemy roster

Unchanged. See `assets/source/enemies/ethereal_scape/ROSTER.md`. Declared per piece as
`EnemyTags`; nothing consumes them yet (build spec §7.6).

## Next

1. **Upload and walk it in Studio.** Nothing here has been seen in Studio yet. Check the socket heights (`OffsetY`) line up across a rise, and that vertex colour survives.
2. Tune the cloud floor's look under the world's real lighting. Review renders use flat Workbench shading, which greys `CloudWhite`.
3. Fixtures (chests on the Treasury / Relic Altar, a vault) were not in this pass.
