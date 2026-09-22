# LUCKBOUND — Sky Citadel

The Epic world's art direction and its chunk kit. This is the "real section"
`ART_DIRECTION.md` said Sky Citadel needed before Phase 2 makes worlds
enterable — the Biome Blueprint reserved the slot (§7.4) and never drafted it.

**Owner-directed 2026-09-22:** *floating spires, future-like castle
architecture — a floating citadel with varying decorations and objects.*

| | |
|---|---|
| Content | `src/shared/Content/Worlds/SkyCitadel.luau`, `Content/Chunks/SkyCitadel.luau` |
| Generator | `assets/source/worlds/sky_citadel/build_sky_citadel_kit.py` |
| Review renders | `assets/source/worlds/sky_citadel/render_review.py` → `renders/*.jpg` |
| Exports | `assets/export/worlds/sky_citadel/chunk_*.fbx` |
| Contract | [`CHUNK_AUTHORING.md`](CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](MODULAR_MAPS.md) |

---

## The look

**A white castle that has been cut loose from the ground and kept.** Every
piece is an island of the same citadel, hung in open morning sun above the
cloud deck: turrets and walls you would recognise from a storybook castle, but
machined — octagonal, chamfered, seamed with light, and held up by nothing you
can see.

Three things make it read as *future* castle rather than *old* castle:

1. **Needle spires with neon halos.** Tall, tapering octagonal shafts with a
   glowing band at mid-height, a gold collar, and a floating ring of light
   that orbits nothing. They are the world's silhouette — every piece has at
   least one, and one per piece reaches the full 160 studs.
2. **Seams of azure light.** Deck edges, railing kick-rails, window slits,
   parapet caps and floor inlays glow a cool blue. Emissive is structure here,
   not decoration.
3. **Things that float on purpose.** Crystals, halos, pylons and the corner
   beacons hang in the air. The keel under every island tapers to a point and
   touches nothing.

### It must not look like Ethereal Scape

Ethereal Scape is also bright and above the clouds, so the difference has to
be deliberate:

| | Ethereal Scape | Sky Citadel |
|---|---|---|
| What stands there | a temple on meadow islands | a castle on machined decks |
| Ground | mint grass, gold soil | white deck plate, no soil at all |
| Warm accent | temple gold, generously | sun gold, **sparingly** — caps and finials only |
| Glow | portal glow, soft | azure seams, crisp and linear |
| Shape language | round, organic | octagonal, chamfered, vertical |
| Colour contrast | ivory and green | white and **violet** |

### The palette

Named materials in the generator; each face carries its colour both as a
material slot and as a baked vertex colour (see *Colour* under the risks
below). Same house rules as the hub: low poly, flat shaded, no textures,
`SmoothPlastic`, with `Neon` only for the two azure roles.

| Role | RGB | Used for |
|---|---|---|
| `CitadelWhite` | `232, 236, 244` | decks, walls, spire shafts, tower bodies |
| `PaleAlloy` | `176, 188, 210` | trim, railings, plinths, merlons, paving border |
| `DeepAlloy` | `92, 104, 134` | structural dark: bands, lamp poles, keel tip |
| `HullSlate` | `118, 124, 156` | the floating keel under every deck |
| `SunGold` | `236, 190, 92` | collars, finials, the gate keystone — the one warm accent |
| `AzureNeon` | `120, 210, 255` | **small** emissive: halos, lamp crystals, fin tips |
| `AzureDim` | `70, 128, 168` | **large** emissive: deck seams, inlays, window slits |
| `CitadelViolet` | `138, 96, 210` | turret roofs, banners |
| `SkyGlass` | `178, 222, 242` | floating crystals, fountain water |
| `Verdure` | `96, 156, 124` | clipped topiary — the only green in the world |

**Why two azures:** the same reason as the hub's two mints. `Neon` emits at
full `Color` and bloom amplifies it, so anything bigger than a halo gets the
knocked-back `AzureDim`.

**Violet is not the rarity colour.** Epic's portal/UI purple is `#B24BF3`;
`CitadelViolet` is a cooler, darker set-dressing colour that merely rhymes with
it. Rarity colour is a contract; biome palette is set dressing
(`ART_DIRECTION.md`).

### The set-dressing vocabulary

"Varying decorations and objects", as a kit of reusable props. New pieces
should draw from this list before inventing new ones, so the world keeps one
hand. Every prop is a function in the generator.

| Prop | Reads as | Scale |
|---|---|---|
| Needle spire | the silhouette; plinth, white shaft, azure band, gold collar, needle, halo. Can stand on a roof (`z0`) | 96–160 tall |
| Turret | castle tower: white octagon, window slits, crenellated walk, violet cone — or a flat roof carrying a spire | 24–64 tall |
| Gate | futurist castle gate: two pylons, lintel, peaked chevron, gold keystone | 58 tall, 72 clear |
| Moon Gate | a white ring standing in the deck, azure inner arc, gold keystone | 55 tall, 72 clear |
| Parapet | low crenellated wall with a glowing cap | 3.4 (waist) |
| Railing | posts, top rail, glowing kick-rail | 3.2 (waist) |
| Lamp | slim pole, glowing crystal head | 9 |
| Banner | T-pole, violet cloth, gold bar and emblem | 12 |
| Holo pedestal | kiosk with a floating crystal and ring | 7 |
| Planter · topiary orb | alloy box with a two-tier cone, or a clipped ball on a stem | 7 |
| Bench | alloy seat | 1.4 seat |
| Cargo crates · containers | stacked, rotated alloy boxes; ribbed 7-stud containers | 2.6–3.2 |
| Sky Fountain | drum, glass pool, gold bowl, floating crystal, tilted halos | 21 |
| Obelisk | tapering alloy, gold cap, floating crystal | 34 |
| Anti-grav pylon | glass crystal in two rings, hanging in the air | ~24 |
| Floating crystal | glass bipyramid | 5–24 |
| Corner beacon | **three styles** — alloy post, glass shard in rings, glowing lantern — see below | 15–34 |
| *Skyport* — skiff | white hull, violet sails, azure drive; moored, floating | 27 long |
| *Skyport* — crane · landing pad | alloy mast and boom with a hanging crate; ringed pad with azure marks | 25 · 40 across |
| *Hoops* — great ring | alloy ring with an azure inner ring and gold studs, spanning the skyway | 72 across |
| *Satellite island* | a small hex deck on its own keel, not reachable — scenery | 34–44 across |
| *Garden* — hedge · pool · pergola · gazebo · flower bed | clipped green walls, glass reflecting pool, slatted colonnade, violet-roofed pavilion, beds of gold/violet/glass buds | 2.4 · flush · 9 · 18 · 1.6 |
| *Observatory* — dome · telescope · dish · orrery | white dome with azure slits; gold-rimmed tube; tilted dishes on masts; nested azure rings with orb planets | 26 · 20 · 12–16 · 17 |
| *Armory* — weapon rack · shield rack · target · forge · barracks | glass blades and gold hilts; violet hex shields; azure bullseye; glowing mouth and chimney; long hall under a violet pitched roof | 3.4–20 |
| *Vault* — keep · round door · chests · crystal cluster | white strongbox with corner turrets; gold-ringed vault door; gold chests; glass and violet crystals growing from the deck | 25 · 16 · 2 · 9 |
| *Hall of Winds* — colonnade · turbine · wind altar | two rows of pillars under an architrave; 3-blade turbines; a ring with three orbiting shards | 31 · 76–160 · 18 |

#### What floats on purpose

The hand pass (`CHUNK_AUTHORING.md`) asks for floating objects to be caught.
In this world some float deliberately, and this is the complete list — anything
else floating is a bug:

spire halos · floating crystals · the pedestal and obelisk-top crystals ·
anti-grav pylons · the fountain's crystal and halos · the corner beacons · the
skiff · the great hoops · the wind altar's shards · the orrery's rings and
planets · the keel itself. (Lamp crystals and the gate and turret finials sit
*on* their mounts — if one is floating, that is a bug.)

#### Floating things never clip — checked, not eyeballed

Owner-directed 2026-09-22, after the first pass put an identical beacon flush
in every corner — so wherever four tiles met, four beacons fused into one
block. Two rules now hold for every piece, and `validate()` refuses to export
a piece that breaks either:

1. **Nothing that floats clips anything.** Every floating object is registered
   as a cylinder or box as it is built; so is every large solid (spires,
   turrets, gates, buildings, decks). A float may not intersect another float,
   a solid, or a deck, with a 1-stud gap.
2. **Nothing that floats comes within 4 studs of the tile edge.** This is the
   rule that makes neighbours safe: whatever piece is placed next door, at
   whatever rotation, its floats are ≥ 4 inside its own edge and ours are ≥ 4
   inside ours, so they are always ≥ 8 apart.

The checker was tested against planted faults (two overlapping crystals, one
past the edge margin, one inside a spire) and flagged all three.

**The corner beacons are now placed, not stamped.** Each of the four picks its
own style (post, shard or lantern), size (0.75–1.3×), height (−18 to +26),
turn, and inset from the corner (12–36 studs on each axis), then is kept only if
it passes both rules — up to 60 tries per corner. The choices are seeded from
the piece's name, so a rebuild is identical. `preview_corner.jpg` shows four
pieces meeting at one corner.

**What pins the bounding box now.** The beacons used to touch the tile edge,
and that is what held every mesh's box to exactly 256 × 256 — which matters
because the loader stretches a mesh to `SizeX/Z`, and a Roblox MeshPart pivots
on its box centre. That job moved to **four 0.3-stud pins** at the midpoint of
each edge, at the keel line (z = −96). Each lies wholly on its own side of the
edge, so two neighbours' pins meet face to face and never interpenetrate; 96
studs under the deck and a third of a stud across, they are invisible in play.
The +160 crown is still pinned by one landmark per piece.

### Lighting

`Content/Worlds/SkyCitadel.luau`'s `Environment` was invented before this
direction existed, and it happens to suit it: `ClockTime 7`, brightness 3, warm
top light, pale fog. **Left unchanged** — worth retuning only after a piece has
been seen in Studio. The review renders approximate it (warm low sun, blue sky
fill, no fog).

---

## The connection vocabulary

Decided before modelling, per `CHUNK_AUTHORING.md` → *Starting a different
world*. Deliberately disjoint from Verdant Valley's `PATH`/`WIDE`, and a test
asserts it.

| Kind | Role | Width | Ground | What it looks like |
|---|---|---|---|---|
| `SKYWAY` | connective | **40** | z = 0 | a railed bridge deck with glowing edge seams and a keel spine |
| `ASCENT` | arena-only | **72** | z = 0 | a grand approach, no railings, glowing kerbs and chevrons pointing at the arena |

Only the two **gate-courts** — the Spire Court and the rarer Hall of Winds —
offer an `ASCENT` exit, and the arena accepts nothing else. So a gate-court
precedes the arena on every seed and is never spent mid-path. Nobody wrote that
rule; it is the reserved-Kind rule doing its job for the third time (Verdant
Valley's Grove, the retired Ethereal kit's Waystone Ring). Asserted over 200
seeds.

Every opening's deck runs **all the way to the tile edge** at z = 0, so two
pieces meet deck to deck. An opening with nothing attached reads as a bridge
that carries on into the sky — which is the *"ground continues out of sight"*
the brief asks for.

---

## The kit — 12 pieces

All twelve are exactly **256 × 256 × 256**: footprint ±128, bottom at −96,
crown at +160. Origin at the centre of the footprint on the walk plane.

| File | Id | Role | Openings | Weight | Tris | What it is |
|---|---|---|---|---|---|---|
| `chunk_entry` | `SC_ENTRY` | ENTRY | N `SKYWAY` | — | 5,054 | Octagonal arrival plaza, landing pad, the Beacon spire, two turrets, kiosks, cargo |
| `chunk_path_straight` | `SC_PATH_STRAIGHT` | PATH | N + S `SKYWAY` | 40 | 4,282 | Skyway across a hex pier, through a gatehouse between two turrets |
| `chunk_path_bend` | `SC_PATH_BEND` | PATH | S + **E** `SKYWAY` | 25 | 4,036 | **The quarter turn.** Skyway round the Spired Keep — a turret carrying a 100-stud spire |
| `chunk_path_skyport` | `SC_PATH_SKYPORT` | PATH | N + S `SKYWAY` | 20 | 3,910 | A skiff dock off the skyway: landing pad, crane, containers, control tower with antenna spire, a moored skiff |
| `chunk_path_hoops` | `SC_PATH_HOOPS` | PATH | N + S `SKYWAY` | 20 | 4,964 | A bare span, no pier, through three great floating rings, between two unreachable satellite islands |
| `chunk_garden_terrace` | `SC_GARDEN_TERRACE` | COMBAT | N + S `SKYWAY` | 20 | 5,810 | Hedged avenue, reflecting pool under a pergola, gazebo in flower beds, topiary, the Sun Spire |
| `chunk_observatory` | `SC_OBSERVATORY` | COMBAT | N + S `SKYWAY` | 15 | 5,138 | Dome with telescope and mast, a dish array, an orrery over a star-map floor |
| `chunk_armory` | `SC_ARMORY` | COMBAT | N + S `SKYWAY` | 15 | 6,070 | Sparring ring, target line, weapon and shield racks, barracks, forge, watch turret |
| `chunk_spire_court` | `SC_SPIRE_COURT` | COMBAT (gate-court) | S `SKYWAY`, N `ASCENT` | 25 | 7,690 | Walled court, four turrets, twin crown spires, the Sky Fountain, the Ascent Gate |
| `chunk_spire_court_b` | `SC_SPIRE_COURT_B` | COMBAT (gate-court, **rare**) | S `SKYWAY`, N `ASCENT` | 8 | 5,620 | The Hall of Winds: two colonnades, the Great Turbine, the Wind Altar, the Moon Gate |
| `chunk_side_vault` | `SC_SIDE_VAULT` | SIDE | S `SKYWAY` | 100 | 3,646 | A sealed treasury: vault keep with a round gold door, chests, crystal clusters |
| `chunk_boss_clearing` | `SC_BOSS_CLEARING` | BOSS | S `ASCENT` | — | 5,398 | Round arena, inlaid floor, obelisk ring, the Crown Spire with three halos |

Every COMBAT piece and the side vault are `MaxPerLayout = 1`.

**The side vault is declared but never placed yet** — the same as Verdant
Valley's Hollow: `ChunkCore` does not consume `IncludeSide` (`STATUS.md`,
Medium). It is validated and exported, ready for when it does.

**Only one piece turns, and only one way.** The bend exits east; a mirrored
west bend was left out on purpose, because `ChunkCore.exitFor` takes the first
valid socket (`STATUS.md`, High) and the extra variety would not show until
that is fixed.

Review renders, `assets/source/worlds/sky_citadel/renders/`:

- `kit_overview.jpg` — all twelve on the review grid, rows of four
- `preview_chain.jpg` — entry → skyport → **bend** → garden → Hall of Winds →
  arena, the last three turned a quarter so the join follows the bend
- `preview_corner.jpg`, `preview_corner_top.jpg` — four pieces at four yaws
  meeting at one corner: the beacon check
- a hero and a ground-level shot of each piece

### Axes

Blender +Y is Roblox **north** (−Z) under `-Z Forward, Y Up`; Blender +X is
Roblox +X. **Verified in the written files, not assumed:** the entry's
deck-edge vertices sit at FBX z = −128 and none at +128; the bend's sit at FBX
z = +128 (south) and x = +128 (east), and nowhere else.

### How to change it

The `.blend` is an **output**. The generator rebuilds the kit from scratch, so
edit the script, not the file:

```
blender -b --factory-startup --python assets/source/worlds/sky_citadel/build_sky_citadel_kit.py -- --export
blender -b --factory-startup --python assets/source/worlds/sky_citadel/render_review.py
```

The first rebuilds, validates, exports all twelve FBXs, **re-imports each one
and measures it**, and saves the `.blend`. It refuses to export if any piece
fails validation. The second renders the review set (28 images). Both run
headless in seconds — see *Render headless* below.

`validate()` checks, per piece: footprint exactly 256 × 256; height exactly
−96 → +160; footprint centred on the origin; under 10,000 triangles; flat
shaded; **every float clear of every other float, solid and deck, and ≥ 4 inside
the tile edge**.

To add a piece: write a `build_<name>()` that ends in `finish(p)`, add it to
`BUILDERS`, register anything that floats (`float_crystal`, `p.float_`) and
anything large (`p.solid`, `p.solid_box`), and give it one landmark reaching
`CROWN_TOP`.

---

## Hand pass

### 2026-09-22 — the kit expansion

| Check | Result |
|---|---|
| **Floating objects** | Checked by `validate()` for all 12 (above), and by eye on the renders: the beacons, crystals, pylons, hoops and skiff all hang clear. |
| **Clipping** | None found by the checker. By eye: the armory's front beacon *looks* as if it cuts the deck corner in the hero shot — it is in front of it, nearer the camera; the checker puts it clear. |
| **Scale** | The 5-stud figure against the new props: weapon racks and targets at chest-to-head height, the gazebo and pergola walk-under, the skiff a boat not a ship, the turbines monumental. |
| **Edges** | `preview_chain.jpg`: the bend's east skyway meets the quarter-turned garden deck to deck, and the Hall of Winds' ASCENT meets the arena's. `preview_corner.jpg`: four beacons, four styles, four places. |
| **Origin** | Every footprint centred on (0, 0) within 0.01. |

The checker existed before the eight new pieces were written, so it shaped
their layout rather than auditing it afterwards; nothing needed fixing after
it ran.

### 2026-09-22 — the first four

| Check | Result |
|---|---|
| **Floating objects** | Everything on the list above floats on purpose; every other prop is placed on z = 0 by construction (no scatter-by-rule). None found. |
| **Clipping** | Found and fixed: the gate chevrons were built with the wrong rotation sign and crossed into a V. Spire buttress fins read as dark sleeves round the shaft — slimmed and moved to `PaleAlloy`. |
| **Scale** | The 5-stud reference figure (gold, `REF_Person_5m_*`, never exported) stands by each piece. Railings and parapets meet it at the waist; lamps are ~2 figures; turrets 6–13; the crown spires 32. The ground shots read as a place, not a model. |
| **Edges** | `preview_chain.jpg`: every join is deck to deck at the same height and width; nothing crosses the boundary. |
| **Origin** | Checked numerically rather than by rotating: every footprint's centre is (0, 0) within 0.01, so a quarter turn spins in place. |

Also found and fixed: the chevrons on the `ASCENT` approach pointed back at
the player instead of at the arena.

---

## Risks before upload — read before importing to Studio

None of these is fixed here: they sit on the loader side, and these passes were
content. They are recorded in `STATUS.md`.

1. **`GroundOffsetY` (already High in `STATUS.md`).** `ChunkLoader` puts the
   mesh's bounding-box **centre** at the layout Y. These pieces' walk plane is
   **32 studs below** that centre (box −96 → +160). Until the loader consumes a
   ground offset, an uploaded piece sits 32 studs low. The number is the same
   for every piece in the kit, by construction.
2. **The mesh is stretched to `SizeX/Y/Z`.** `tryMesh` sets `mesh.Size` from
   the chunk data. That is why the generator pins every box to exactly 256³ —
   edge pins for the footprint and the bottom, a 160-stud landmark for the top.
   A piece that does not fill its box would be silently distorted. Worth
   knowing for every future kit, not just this one.
3. **One MeshPart means one `Color`.** `CreateMeshPartAsync` returns a single
   part, and the hub's paint-by-part-name approach does not exist for chunks.
   Each piece therefore carries its colours as **baked vertex colours** (plus
   material slots). Whether Studio's importer keeps them on a MeshPart has
   **not been verified** — the first import will say. If it does not, the
   options are a multi-part delivery (a `.rbxmx` like the hub prefabs, which is
   a loader change) or accepting one colour per piece.
4. **Collision on one mesh.** The loader sets `CanCollide = true` at default
   fidelity. `ART_DIRECTION.md` already says what that does to a mesh with
   openings: railings, parapets, gate arches, the hoops, the pergola and the
   Moon Gate will seal into coarse hulls. `CreateMeshPartAsync` accepts a
   `CollisionFidelity` option; the loader should pass
   `PreciseConvexDecomposition` for chunks.
5. **The spawn uses the mesh's top.** `entryPosition` is the surface's top
   face — with a mesh, that is the bounding-box top at +160 (+32 once the
   ground offset lands). The entry keeps the column above (0, 0) clear so a
   player drops onto the landing pad rather than a spire, but it is a 128-stud
   drop until the loader spawns from the ground offset instead.
6. **Triangle budget.** The Spire Court is highest at 7,690 of 10,000.
   `validate()` fails over 10,000.

---

## Render headless

Rendering through the Blender MCP bridge inside the interactive session crashed
Blender twice in a row on 2026-09-22, on the same shot (the court's ground
view). The headless run renders the whole review set in seconds and never
touches the open session, so both scripts are documented as headless-first.
Building (no render) through the bridge worked fine.

---

## Next

1. **Import one piece into Studio and measure it** — 256 × 256 × 256, and note
   whether the vertex colours survive (risk 3).
2. Land `GroundOffsetY` and the collision-fidelity option in `ChunkLoader`
   (risks 1, 4) before uploading the rest.
3. `ChunkCore`: a random pick among valid exits, and `IncludeSide` — then a
   west-turning bend is worth adding, and the vault gets placed.
4. Up to four more pieces to reach 16, if runs still repeat once walked:
   a second straight variant, a second arena approach, a crossroads pier.
5. Retune `Environment` once a piece has been seen in Studio.
