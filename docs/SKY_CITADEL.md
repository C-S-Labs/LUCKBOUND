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
hand.

| Prop | Reads as | Scale |
|---|---|---|
| Needle spire | the silhouette; plinth, white shaft, azure band, gold collar, needle, halo | 96–160 tall |
| Turret | castle tower: white octagon, window slits, crenellated walk, violet cone | 30–64 tall |
| Gate | futurist castle gate: two pylons, lintel, peaked chevron, gold keystone | 58 tall, 72 clear |
| Parapet | low crenellated wall with a glowing cap | 3.4 (waist) |
| Railing | posts, top rail, glowing kick-rail | 3.2 (waist) |
| Lamp | slim pole, glowing crystal head | 9 |
| Banner | T-pole, violet cloth, gold bar and emblem | 12 |
| Holo pedestal | kiosk with a floating crystal and ring | 7 |
| Planter | alloy box, two-tier topiary | 7 |
| Bench | alloy seat | 1.4 seat |
| Cargo crates | stacked, rotated alloy boxes | 2.6–3.2 |
| Sky Fountain | drum, glass pool, gold bowl, floating crystal, tilted halos | 21 |
| Obelisk | tapering alloy, gold cap, floating crystal | 34 |
| Anti-grav pylon | glass crystal in two rings, hanging in the air | ~24 |
| Floating crystal | glass bipyramid | 5–24 |
| Corner beacon | alloy post with a glowing band, pointed both ends | 26 |

#### What floats on purpose

The hand pass (`CHUNK_AUTHORING.md`) asks for floating objects to be caught.
In this world some float deliberately, and this is the complete list — anything
else floating is a bug:

spire halos · floating crystals · the pedestal and obelisk-top crystals ·
anti-grav pylons · the fountain's crystal and halos · the corner beacons · the
keel itself. (Lamp crystals and the gate and turret finials sit *on* their
mounts — if one is floating, that is a bug.)

### Lighting

`Content/Worlds/SkyCitadel.luau`'s `Environment` was invented before this
direction existed, and it happens to suit it: `ClockTime 7`, brightness 3, warm
top light, pale fog. **Left unchanged in this pass** — worth retuning only after
a piece has been seen in Studio. The review renders approximate it (warm low
sun, blue sky fill, no fog).

---

## The connection vocabulary

Decided before modelling, per `CHUNK_AUTHORING.md` → *Starting a different
world*. Deliberately disjoint from Verdant Valley's `PATH`/`WIDE`, and a test
asserts it.

| Kind | Role | Width | Ground | What it looks like |
|---|---|---|---|---|
| `SKYWAY` | connective | **40** | z = 0 | a railed bridge deck with glowing edge seams and a keel spine |
| `ASCENT` | arena-only | **72** | z = 0 | a grand approach, no railings, glowing kerbs and chevrons pointing at the arena |

The Spire Court is the **only** piece offering an `ASCENT` exit, and the arena
accepts nothing else — so the court gates the arena on every seed, and is never
spent mid-path. Nobody wrote that rule; it is the reserved-Kind rule doing its
job for the third time (Verdant Valley's Grove, the retired Ethereal kit's
Waystone Ring). Asserted over 200 seeds.

Every opening's deck runs **all the way to the tile edge** at z = 0, so two
pieces meet deck to deck. An opening with nothing attached reads as a bridge
that carries on into the sky — which is the *"ground continues out of sight"*
the brief asks for.

---

## The kit — first delivery, 4 pieces

All four are exactly **256 × 256 × 256**: footprint ±128, keel apex at −96,
crown at +160. Origin at the centre of the footprint on the walk plane.

| File | Id | Role | Openings | Tris | What it is |
|---|---|---|---|---|---|
| `chunk_entry` | `SC_ENTRY` | ENTRY | north `SKYWAY` | 4,714 | Octagonal arrival plaza, landing pad at the centre, the Beacon spire (160), a second spire, two turrets, kiosks, planters, cargo |
| `chunk_path_straight` | `SC_PATH_STRAIGHT` | PATH | north + south `SKYWAY` | 3,742 | Skyway across a hexagonal pier, through a gatehouse between two turrets; a mast spire (160), anti-grav pylons |
| `chunk_spire_court` | `SC_SPIRE_COURT` | COMBAT (grove role) | south `SKYWAY`, north `ASCENT` | 7,286 | Walled court, four corner turrets, twin crown spires (160), the Sky Fountain, lamp avenue, the Ascent Gate |
| `chunk_boss_clearing` | `SC_BOSS_CLEARING` | BOSS | south `ASCENT` | 4,794 | Round arena with an inlaid floor, a ring of obelisks open to the south, the Crown Spire (160) with three halos, sentinel crystals |

Review renders: `assets/source/worlds/sky_citadel/renders/` —
`kit_overview.jpg` (the review row), `preview_chain.jpg` (entry → path → path →
court → arena, joined as the generator joins them), and a hero and a
ground-level shot of each piece.

### Axes

Blender +Y is Roblox **north** (−Z) under `-Z Forward, Y Up`; Blender +X is
Roblox +X. **Verified in the written file, not assumed:** the entry's deck-edge
vertices sit at FBX z = −128 and none at +128.

### How to change it

The `.blend` is an **output**. The generator rebuilds the kit from scratch, so
edit the script, not the file:

```
blender -b --factory-startup --python assets/source/worlds/sky_citadel/build_sky_citadel_kit.py -- --export
blender -b --factory-startup --python assets/source/worlds/sky_citadel/render_review.py
```

The first rebuilds, validates, exports all four FBXs, **re-imports each one and
measures it**, and saves the `.blend`. It refuses to export if any piece fails
validation. The second renders the review set. Both run headless in a few
seconds — see *Render headless* below.

`validate()` checks, per piece: footprint exactly 256 × 256; height exactly
−96 → +160; footprint centred on the origin; under 10,000 triangles; flat
shaded.

---

## Hand pass — 2026-09-22

The five checks from `CHUNK_AUTHORING.md`, done by eye on the renders:

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

None of these is fixed here: they sit on the loader side, and this pass was
content. They are recorded in `STATUS.md`.

1. **`GroundOffsetY` (already High in `STATUS.md`).** `ChunkLoader` puts the
   mesh's bounding-box **centre** at the layout Y. These pieces' walk plane is
   **32 studs below** that centre (box −96 → +160). Until the loader consumes a
   ground offset, an uploaded piece sits 32 studs low. The number is the same
   for every piece in the kit, by construction.
2. **The mesh is stretched to `SizeX/Y/Z`.** `tryMesh` sets `mesh.Size` from
   the chunk data. That is why the generator pins every box to exactly 256³ —
   corner beacons for the footprint, keel apex and a 160-stud spire for the
   height. A piece that does not fill its box would be silently distorted.
   Worth knowing for every future kit, not just this one.
3. **One MeshPart means one `Color`.** `CreateMeshPartAsync` returns a single
   part, and the hub's paint-by-part-name approach does not exist for chunks.
   Each piece therefore carries its colours as **baked vertex colours** (plus
   material slots). Whether Studio's importer keeps them on a MeshPart has
   **not been verified** — the first import will say. If it does not, the
   options are a multi-part delivery (a `.rbxmx` like the hub prefabs, which is
   a loader change) or accepting one colour per piece.
4. **Collision on one mesh.** The loader sets `CanCollide = true` at default
   fidelity. `ART_DIRECTION.md` already says what that does to a mesh with
   openings: railings, parapets and the gate arches will seal into coarse
   hulls. `CreateMeshPartAsync` accepts a `CollisionFidelity` option; the
   loader should pass `PreciseConvexDecomposition` for chunks.
5. **The spawn uses the mesh's top.** `entryPosition` is the surface's top
   face — with a mesh, that is the bounding-box top at +160 (+32 once the
   ground offset lands). The entry keeps the column above (0, 0) clear so a
   player drops onto the landing pad rather than a spire, but it is a 128-stud
   drop until the loader spawns from the ground offset instead.
6. **Triangle budget.** The court is at 7,286 of 10,000. Variants that add
   dressing need watching; `validate()` fails over 10,000.

---

## Render headless

Rendering through the Blender MCP bridge inside the interactive session crashed
Blender twice in a row on 2026-09-22, on the same shot (the court's ground
view). The headless run renders all ten images in about three seconds and never
touches the open session, so both scripts are documented as headless-first.
Building (no render) through the bridge worked fine.

---

## Next

1. **Import one piece into Studio and measure it** — 256 × 256 × 256, and note
   whether the vertex colours survive (risk 3).
2. Land `GroundOffsetY` and the collision-fidelity option in `ChunkLoader`
   (risks 1, 4) before uploading the other three.
3. **The remaining 8–12 pieces**, as variants of the existing roles. Ideas that
   stay inside the vocabulary above:
   - `chunk_path_bend` — a skyway turning a quarter round a turret (**needed**:
     every current socket faces north/south, so no layout ever turns)
   - `chunk_path_straight_b` — a skyway with a hangar of cargo and a landing pad
   - `chunk_path_straight_c` — a narrow skyway flanked by two hovering pylons, no pier
   - `chunk_garden_terrace` — a COMBAT court of clipped topiary and benches
   - `chunk_observatory` — a COMBAT platform with a dish array and an orrery of halos
   - `chunk_armory` — a COMBAT yard of racks and crates under a turret
   - `chunk_side_vault` — the world's SIDE pocket, off a spare `SKYWAY`
   - `chunk_spire_court_b` — a second ASCENT gate-court, weighted rare
4. Retune `Environment` once a piece has been seen in Studio.
