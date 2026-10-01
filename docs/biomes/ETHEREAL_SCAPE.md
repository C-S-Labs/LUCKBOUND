# Ethereal Scape — biome design schema

The Uncommon world's art direction and its chunk kit.

## Living scenery revision — 2026-10-01

BASE remains universal. Owner requested more visible atmosphere: ES now has lavender pearl
haze (Density0.34/Haze1.8), stronger grade and six lavender motes/sec. Lower sea uses19 (11/8)
Crossroads mesh banks at full quality, layers320/740studs down with180/320stud scatter,
ceiling160. Sparse smaller banks appear on alternating templates and wander18studs/bob3.
Crowns use Foliage with phased strength/pace, 3.6s nominal cycle, gentle pace changes and
tiny gusts. Six BACKDROP templates float3.5studs over24s, structure/props together.
Skyrays breathe8% of map radius over180s and face their true travel tangent; backdrops
no longer inflate map flight bounds. Studio review is the acceptance gate. No new import.

## BASE atmosphere — 2026-10-01

Owner accepted the current imported kit for this Studio pass. BASE is the only available
atmosphere across all maps until further notice; existing variants remain parked via
`GameConfig.Ambience.Atmospheres.Enabled=false`.

ES uses pearl afternoon air (14.3): ivory sunlight, lavender shadow bounce, pale distance haze,
restrained bloom/rays and a subtle cool grade. Two slowly drifting cloud layers remain below
keels (160-stud ceiling clearance), with sparse lavender motes. Authored in the world's
Environment and applied per client by existing ambience code; no imports required. Sync,
leave and re-enter to review. Sanctum/shrine visibility and final exposure need Studio approval.

## Live delivery and runtime — 2026-09-30

**2026-10-01 import verified:** owner saved227 structure/258 prop meshes in primary checkout;
both copied into the ES worktree. All names, uploaded IDs and dimensions verified after restoring
50 Studio-shortened prop names in worktree XML (one duplicate resolved).227 structure IDs synced,
1,029 tests and Rojo build pass. Use corrected worktree models; Studio walk remains pending.

Fresh owner-scene exports: **227 structure meshes**, **258 props** (13 existing atmospheric +245
separated scene props). Main-thread export bakes transforms/modifiers and preserves the live scene;
the inspection-offset Sanctum is aligned in the export only. Generated placement/bounds data comes
from `live_delivery.json` through `tools/prepare_ethereal_delivery.py`. Import and save instructions:
`assets/source/worlds/ethereal_scape/IMPORT_STEPS.md`. Replacement RBXMX/IDs are now synced as noted above.

41 registered templates: ordinary31 (PATH13/COMBAT11/SIDE3/CAP4), ENTRY1, MINIBOSS2, BOSS1,
BACKDROP6. One additional shrine miniboss chamber is a conditional attachment, outside the random pool.
Enemy-tag eligibility: 24 ordinary,25 with entry,28 with registered bosses; these are not live enemy counts.
Loot venues are the altar chest and shrine chamber's keyed chest. The shrine creates its own hidden room
4,096 studs above it and reciprocal walk-through portals; no shrine means no room. Both share expedition lifetime.

35 authored boundary groups create transparent64-stud colliders. Camera exclusion is explicit for custom
camera/visibility rays; Studio must verify free camera, wall jumping and open socket mouths. Tree crowns sway
about root attachments; mounted lights/portal membranes pulse without detaching from their supports.

**Locked owner decision:** only the **biome boss** can drop the vault key. Biome boss completion opens
the shrine vault-room gate for everyone regardless of the drop; the chest still requires/spends each player's
key. Miniboss completion does neither. `/boss` and the existing BOSS-arena stand-in test this until enemy
gameplay is implemented. Prior authoring-only/pending delivery notes below are historical.

Latest room revision (2026-09-30): existing room group enlarged 1.5× horizontally and
1.45× vertically, yielding **114 × 114 studs clear fighting area and a 60.9-stud ceiling**.
Side columns reach roof capitals; six indigo/gold celestial ceiling murals occupy coffer
bays with halo/eye/ray motifs. Detail stays above or outside the combat floor. Alcoves
scale with the room, keeping portal/vault separate. Supersedes earlier 76 × 76 dimensions.

Latest correction (2026-09-30): boundary height is now **64 studs**, superseding 32 below.
Two mouth-crossing walls removed using actual connector profiles, including the Sanctum
approach whose edited local mouth plane differs from nominal tile bounds. All 60 connector
keels now use a 2-stud chamfer on lower corners; matching faces share the same silhouette
and level bottom. Includes two previously missed pieces with shifted origins. Owner inspect
then Studio clearance/join test pending; older prose describes superseded iterations.

### Animation separation and safety walls — 2026-09-30

Live collection `ES_ANIMATION_PROPS` contains 244 separate prop objects. Newly extracted:
66 light/effect groups and 161 tree-crown meshes, preserving positions and local pivots.
Attached lights use material/light pulsing; tree crowns can use existing Sway. Chandelier
is one suspended assembly with ceiling pivot. Source meshes no longer contain extracted
geometry; exporting structure alone would omit these props. Complete export/prop placement
generation must precede the next Studio walk. Current FBXs remain older delivery.

`ES_SAFETY_BOUNDARIES` holds a separate, source-parented collision group for all 35 playable
chunks (no backdrops). Walls follow the union of walking surfaces including bridge edges,
with socket mouths open. Thickness 0.36 studs, height 32; hidden render/wire display for
author review. Wall collision stays fixed; future animated identification is separate.
Sidecars `live_animation_props.json` and `live_safety_boundaries.json` are authoring metadata,
not automatically consumed runtime data.

Runtime proposal: add reusable optional per-chunk boundary definitions under §7.7, server
placement in the chunk frame, and explicit camera-query exclusion. No content-specific
system behavior. Existing maps default to no boundaries. This proposal is not implemented:
the current loader recreates MeshParts from IDs, and CanQuery=false cannot exclude collidable
parts from Roblox queries. Importer/custom Blender properties alone are insufficient.

Correct tagged breakdown: COMBAT 11, PATH 12, SIDE 1, ENTRY 1, MINIBOSS 2, BOSS 1.
That is **24 of 31 ordinary pieces**, **25 including entry**, **28 including bosses**.
Earlier '25 ordinary' wording included entry incorrectly. Tags do not spawn gameplay enemies.

Connector underside revision (2026-09-30): standard mouth pyramids replaced with
socket-flush keels; matching faces retain full width down to the common keel depth.
Only inward edges are lightly beveled; top decks remain unchanged. Generator preserves
the new shape; live helper applies the faceted edge finish. Studio seam test pending.

### Live shrine / loot review — 2026-09-30

`ES_CAP_SEALED_SHRINE` has a walk-through portal arch. Separate group
`ES_SHRINE_MINIBOSS_ROOM` contains an enclosed arena with a clear 76 × 76 stud
combat floor, matching return portal in a vestibule and opaque dark backing hiding
the sky. A locked container sits in a rear-side alcove beyond the combat floor.
Portal surfaces, light crystals and vault door are separate props with animation
pivots. Portal emission has a gentle Blender preview pulse; Blender material
keyframes do not automatically become Roblox animation.

The room is standalone art, not a registered generated chunk. Owner controls its
hidden placement. Teleport triggers, RiftController hookup and runtime vault
registration need a detached-room placement contract; do not alter shared loaders
or fabricate far-away fixture coordinates. Generic loot content defines ES
chest/vault/boss pools and a 20% party boss-completion key chance, matching SC.
Drop entries remain deliberately empty. `ES_SIDE_RELIC_ALTAR` has one registered
chest using installed SC fixture meshes. Two planned loot locations: altar chest
and room vault; the room vault's runtime placement is pending.

Removed ES_ENTRY's stray added trim; original perimeter retained. Separate
`ES_ENTRY_PORTAL_PREVIEW` collection uses the completed portal branch asset on
the rear circle, chunk offset **0, 0, 110**. Exclude this preview from chunk export:
runtime supplies the prefab. Carry the offset into portal content at branch integration.

41 registered pieces: ENTRY 1, PATH 13, COMBAT 11, SIDE 3, CAP 4, MINIBOSS 2,
BOSS 1, BACKDROP 6. Ordinary PATH/COMBAT/SIDE/CAP total **31**. EnemyTags on
**25 ordinary pieces**, **28** including boss/miniboss pieces; these are metadata,
not live enemy spawning. The new standalone room is additional to those counts.
No automatic save/export or PR; owner scene review and Studio test remain required.

Vault revision: black backing now follows only the portal aperture, with ivory masking
outside it. Alcove gains wall columns/coffers/inlays; container gains ribs/diamond
inlays and lock detail. Separate sealed gate `ES_SHRINE_VAULT_GATE_PROP_01` is authored
to slide 18 studs into the ceiling after miniboss defeat. Defeat-triggered opening is
pending runtime implementation alongside the detached-room contract.

> **Boss-aligned finish, 2026-09-30:** owner requests smoother chunks matching the Ascendant.
> Live scene gains curved gold filigree and a small portal core on the throne back, rounded
> architectural block edges and smooth curved ivory/gold/wood shading. Owner rejected softer
> island sides: terrain undersides and skirts are faceted again. Shared platform rims remain fixed; crystals and foliage
> retain their facets. Use evaluated modifiers/normals on export and recheck Studio.

> **Detail revision, 2026-09-30:** curved throne back, oval mask/faceted symmetrical eye,
> rounded seated cushion and supported armrests replace the block slabs. Floor edge accents
> raycast to their supporting cap and avoid explicit path strips; columns (including backdrops)
> gain fitted collars/ribs, missing window trim and restrained wall friezes. Gardens' upper
> filler was rejected and removed: actual deck ends now share a miter seam and existing
> stringers/cross members fit beneath it. Lower foot landing remains unchanged. No loader edits.
> Latest clearance revision replaces the Gardens stair/foot landing entirely with a continuous
> full-width route and following rails. Column trim is cut around framed panes, and flat path
> decals stop at nearby bridge decks (70 faces across nine chunks). Floor trim crossing these
> transitions is removed. Live changes are not saved/exported automatically; owner review and Studio gate remain.

> **Presence pass, 2026-09-30:** existing throne enlarged 1.65x across, 1.35x vertically
> and 1.25x in depth, preserving its footing and rear-wall clearance. Added rear canopy,
> armrest gems and seat trim; thin compass/aisle floor inlays; pediment wings, entrance
> frieze and octagonal tower relief panels. Chair bounds remain behind the fight area.
> Five chair blocks now have single-segment chamfers, three back panels taper upward,
> and the inner entrance wall has four shallow arched reliefs and a lintel crest. Entry
> detail is 900 triangles and remains outside the fighting region. Live review/save/export pending.

> **Sanctum follow-up, 2026-09-30:** separate 3,196-triangle suspended crystal chandelier,
> interior/exterior lattice trim on 39 thick wall/lantern panes, and faceted ivory slit masks,
> gold crown rays and robe folds on both existing doors. Original meshes remain intact.
> These additions are live and unsaved/unexported; review renders are `live_sanctum_interior.png`
> and `live_sanctum_door.png`. The Studio mushroom displacement was traced to reversed X/Z
> multipart offsets: generator, JSON and generated content now use native Roblox import axes.
> All 28 foliage offsets match the saved Studio import; Studio retest remains required.

> **Live polish, 2026-09-30:** owner-edited scene gains ivory relief panels and slim gold ribs
> on 10 tall square columns, gold frames and mullions on 60 crystal windows, and closed landing
> patches at both ends of the Terraced Gardens diagonal stair. Additions are separate detail
> meshes; existing owner geometry is preserved. One mushroom was moved inward 0.25 studs.
> Blender review completed; owner inspection, save, re-export and Studio check remain pending.
> Use `live_scene_polish.py` on Blender's main thread only; never regenerate the edited scene.

> **History.** Ethereal Scape shipped as a `PrebuiltMap` (one hand-authored traverse,
> `aether_environment_refined.blend`). On 2026-09-26 it became a 30-piece chunk kit, was rejected (no platforms,
> too close to Sky Citadel), and was revamped as a grounded cloudscape. On 2026-09-27 the owner still wasn't sold,
> reviewed three direction samples (`renders/samples/`) and chose **the hybrid**. **This document describes the
> hybrid kit.** The original scene stays in the repo as the palette's source of truth.

| | |
|---|---|
| Content | `src/shared/Content/Worlds/EtherealScape.luau`; `Content/Chunks/EtherealScape.luau` and `Content/Props/EtherealScape.luau` (both **generated**) |
| Generator | `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py` + `es_geometry.py`, `es_features.py`, `es_isles.py` (island web), `es_pieces.py` (41 recipes), `es_props.py`, `es_mapgen.py` (preview assembler), `es_samples.py` (the three direction samples, `--samples`) |
| Exports | `assets/export/worlds/ethereal_scape/ethereal_scape_structure.fbx` (41 chunk assemblies / 42 mesh objects), `ethereal_scape_props.fbx` (14 prop kinds); `ethereal_scape_structure.json` records multipart mesh bounds and offsets |
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
| `prop_es_isle_grove`, `_crystal`, `_ruin` | Float | satellite islets in the tile's outer sky, 100–150 up — thinned 2026-09-27 (55% / 30% per kind) |
| `prop_es_petals` | Float | a loose swirl of blossom petals drifting 8–22 up over the meadows |
| `prop_es_lotus` | Hover | a floating aether lotus (glowing heart, dark pad), 12–30 up; more over shrines, crystal and arenas. Deliberately **not** a wisp — `AETHER_WISP` is an enemy |
| `prop_es_kite` | Sway | a pilgrim's prayer kite trailing two ribbons, 50–80 up, on ~60% of pieces |
| `prop_es_skyray` | **Glide** | manta-like gliders that roam the **whole map** — this world's flyer, not Sky Citadel's birds |

Every placement is proven clear of the piece's **real mesh** (BVH), at least 4 studs inside the
tile and clear of every other prop.

**Skyrays fly the whole map (owner 2026-09-27).** They were `Bird`s circling their own chunk; now the
`Glide` class (`PropCore`, `PropController`) re-anchors every skyray on the generated map once all chunks
are placed: it circles the **map's centre** (the mean of the chunk floors) starting where it was authored,
its radius breathing in and out by 45% of the map's radius (70 s cycle) so one ray crosses inner and outer
chunks alike, at `Glide.Altitude` (172) above the **highest** chunk floor plus a 0–40 spread — above every
crown (160), so no beacon or crag anywhere is in its way. Gliders always animate (they have no fixed spot
to be near). Tuning is `GameConfig.Ambience.Props.Glide`.

**The skyray is read from below**, so the belly carries the detail: a lofted manta body (domed indigo back
with a crystal ridge, flatter pale belly), five pairs of gill slits, a wide dark mouth lipped in gold
between two curled cephalic horns, eyes on the head's flanks, a glowing spot pattern and glowing wingtips,
pelvic fins and a long whip tail with a small dorsal fin.

---

## Validation — what `build_ethereal_scape_kit.py` refuses to export

The first kit "passed" with no floors because it only checked the box. These are checked now,
on the real mesh, for every piece:

1. **Box** exactly (2H × 2H) × 256, centred, keel −96, crown +160.
2. **Under 10,000 triangles per exported mesh, not per chunk** (owner-directed 2026-09-30).
   Larger assemblies split into aligned semantic groups and further pieces as necessary. All spatial
   checks below apply to the complete chunk. The Sanctum exports separate grounds and temple meshes.
3. **No degenerate faces.** `mesh.validate()` dropping anything fails the piece.
4. **Walk graph.** This builds a 2-stud heightfield of every walkable surface, with 1.6-stud steps and 5 studs of headroom. It floods from one mouth, and **every other mouth must be reached**.
5. **Mouths:** level ground at the socket's own height across at least 95% of the width.
6. **Nothing detached.** Sky Citadel's real-mesh `geometry_checks.analyse` is reused.
7. **No clipping between builders** (a tree through a pavilion, a crystal through a railing). The ground (isle tops, landings) may be stood in. `declip()` removes any cloud, blossom, grass or mushroom that touches a real object (a mushroom's stem and cap go together). A short list of authored joints is allowed (a porch column in its podium). The final build logs **zero** clip notes.
8. **Grounded, no overhang:** every column, tower, waystone, statue, beacon, lantern, brazier, orrery and crag stands on ground — rays cast under its base, at the centre and at **8 points round its full radius** (+3 studs for bases ≥ 4 studs, since the isle's gold rim band juts past its floor), must **all** meet a surface. The old rule (4 of 5 points at 0.7 r) let the Waystone Ring's and Mirror Pool's beacons and the Sealed Shrine's crag hang over their isle's edge (owner 2026-09-27). A beacon's footing is its whole base plate (2.3 r); a crag's is its real base (1.35 r).
9. **Entry:** the column above the landing and the return-portal pad are open to the sky.
10. **Sanctum:** the hall and the great door are unobstructed.

**Mushrooms grow in patches** (`mushroom_patch()`, the universal rule in `ART_DIRECTION.md`): uneven clumps
of parents and offspring, three shapes (classic, tall-slender, squat-broad) and five cap colours. Only the
Grove Isle's fairy ring is a deliberate ring, and it is ragged.

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

---

## Generation tuning (2026-09-27 walk)

- **`Generation.CombatShare = 0.4`** — about 40% of the ordinary (PATH + COMBAT) pieces are fights, so the count
  grows with the map. `ChunkCore` weights COMBAT pieces 6× while the map is under the share.
- **Elevation:** socket `OffsetY` accumulates, so a climb (Skystair Up +24, East Ascent +16, Twin-Span +10) lifts
  every piece after it, and a descent lowers them.

## First polish pass — 2026-09-30

Small trees now have three root flares and two supporting crown branches. Detail uses the existing wood colour,
flat facets and scatter positions, without consuming extra random values. The complete rebuild passes
41/41 geometry checks. Temple columns have bevelled base and neck moldings. The existing Ascendant is
the main Sanctum boss (owner-confirmed); gold slit-mask and crystal-crown reliefs on the open doors echo
his design without changing his model, animations or the hall's combat space.

The assembled Sanctum is 11,074 triangles: grounds 3,518 and temple 7,556. The limit is per exported
mesh. Additional larger groups split automatically, preserving every oriented triangle and its colour.
`MeshParts` lists the complete assembly with component sizes and offsets in imported mesh axes. The
loader rotates/calibrates the assembly together and falls back to a complete blockout if any part is
missing. Import all named objects; retain their names, save `ES_STRUCTURE.rbxmx`, then run
`tools/sync_asset_ids.py ethereal_scape --write` to record the newly uploaded mesh IDs.

Cloud billows use eight-sided tiers so all 14 atmosphere library meshes also meet the per-mesh limit.
`tests/validate_ethereal_exports.py` checks 30k and oversized-primitive splits, then imports the real FBXs
and checks mesh names, triangle limits, unit scales, vertex colours, dimensions and assembly offsets.

Review renders isolate individual chunks and their props, and separate the chain, catalogue and assembled
map. `--only` preserves unrelated renders. The generator refuses to overwrite delivery outputs on a failed
validation, including render-only runs. The existing blend and exports are regenerated in place.

This starts the owner-requested chunk polish; further terrain, flora and architecture review remains.
Basic enemies and minibosses follow it. Keep current Studio imports until CI and a Studio walk prove replacement.

## Studio delivery staged — 2026-09-30

Owner saved the new 42-mesh structure and 14-prop library. Both RBXMX files are now in the polish
worktree and all chunk IDs, including the separate temple, are synced to AssetManifest. Rojo build,
unit tests and legacy/multipart loader contract checks pass. Run rojo serve from that worktree,
reconnect Studio, then /roll ETHEREAL_SCAPE test and enter to inspect every chunk. A normal roll
checks assembly afterward. Studio collision, alignment and colour checks remain pending; owner
requires those before PR creation. Keep prior Studio imports until that replacement gate passes.

## Studio repair pass — 2026-09-30

The owner's first Studio test failed: missing faces/seams, clipped details and blocked routes.
The previously uploaded RBXMX models are retained for comparison and are **not** the repaired art.
No PR or push is authorized until the owner tests the replacement.

- Island tops, gold rims and rock tiers now form one closed shell with shared edge vertices.
  Landing undersides, cloud floors, mesa/ramp shells, roofs and skyray surfaces are closed too.
  Validation rejects open/nonmanifold solids, inward shells and collapsed triangles; review renders
  use backface culling. Only marked floor inlays are intentionally single-sided.
- Bridge decks compensate for slope thickness and remain level across the entire gold rim before
  descending. Eight island-web recipes gained more slope run by modestly moving/resizing their
  isles. Entry's perch beacon and Plank Crossing's waystone moved clear of the bridge approaches.
  Every bridge and shrine/hut approach now has a sampled player-clearance check.
- Shrine steps fit between their columns; small porches have two columns to prevent overlapping
  bases. Hut doors are wider/taller. Reliquary guardians moved to the perimeter. Roads sit above
  court inlays; waterfalls clear the real island rim and connect to an exposed spill surface.
- Columns have lightly fluted shafts and end-to-end moldings. Sanctum doors sit outside the wall
  with their reliefs facing the approach. The throne has feet, a framed seat/back, arm supports,
  slit-mask relief and seven crystal-tipped crown rays, all behind the combat floor.
- Prayer kites were removed. Mushrooms, blossoms and grass export as foliage components with
  `CanCollide = false`; buildings, bridges and terrain remain solid. This is a generic optional
  mesh-record flag under the existing §7.7 assembly contract, defaulting to true for other maps.

Delivery is the existing `ethereal_scape_structure.fbx` (71 meshes) and
`ethereal_scape_props.fbx` (13 meshes), regenerated under
`C:/Dev/luckbound/.worktrees/ethereal-scape-polish/assets/export/worlds/ethereal_scape/`.
Sanctum is 11,990 triangles: 3,292 terrain, 8,530 temple, 168 non-collidable foliage.
The largest export is 9,994 triangles. Import all meshes with names intact, then save:

- `assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx`
- `assets/rbxm/props/ES_PROP_LIBRARY.rbxmx`

Both paths are relative to the **polish worktree**, not the portal checkout. Export only the new
imported Models, then run `tools/sync_asset_ids.py ethereal_scape --write`. New component IDs
remain placeholders until that import; do not expect the existing Studio uploads to show this pass.
Reinspect the entire catalogue, then normal assembly and VV/SC. Keep the old imported Models
separate until the owner approves replacement. Enemy polish follows the chunk acceptance gate;
Ascendant's owner-edited model and animations are untouched.

Replacement import staged: owner exported 71 structure meshes and 13 uploaded props into the
primary checkout; copied into the polish worktree and all structure IDs synced. Unit tests and
Rojo build pass. Ready for Studio reinspection. Owner intends to hand-edit the output blend:
preserve those changes before any subsequent generator run.

### ES twilight revision — 2026-10-01

Owner supersedes the bright afternoon: BASE now uses18.35 orange-purple twilight,
brightness2 and exposure-0.18. Apricot horizon, violet decay/shadows and muted lavender
cloud undersides; ambient fill preserves readable combat/interiors. Prior afternoon notes
are historical. SC sunrise and Crossroads remain unchanged. Overhead accents are proposals
only: high violet wisps, a distant celestial halo or sparse constellation points.

### ES upper-air ribbons — 2026-10-01

Studio prototype implemented as client Beams through optional Environment.Ribbons.
Soft violet-to-rose smoke-textured veils at650–950studs,700–1500studs long,45–95wide;
map-wide sectors extend600studs beyond layout bounds. Each fades through its55–90s cycle,
then relocates invisibly; ends taper in transparency. Gentle lateral drift32studs/ripple14.
Count2–8 by graphics quality, capped8,12segments,10Hz update. No imported asset, collision
or particles. Current opacity0.16 remains a Studio tuning value. Review with twilight;
SC/Crossroads unchanged.

### ES readability tuning — 2026-10-01

Twilight18.35 retained. Lifted shadow fill/exposure(-0.06), density0.31/haze1.6, gentle
purple grade(246,232,255) and contrast0.075. Ribbons lowered420–620studs, width80–135,
length1000–2000, opacity0.30 to improve visibility; same2–8beam/10Hz budget. Studio retest
pending; supersedes previous visibility values, with no new assets or imports.
