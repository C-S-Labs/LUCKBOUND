# Sky Citadel — biome design schema

The Epic world's art direction and its chunk kit. This is the "real section"
`ART_DIRECTION.md` said Sky Citadel needed before Phase 2 makes worlds
enterable — the Biome Blueprint reserved the slot (§7.4) and never drafted it.

> **Consolidated 2026-09-23.** This lived at `docs/SKY_CITADEL.md` while a
> stub at `docs/biomes/SKY_CITADEL.md` simultaneously declared the world had
> no design at all. Two documents for one world, in two places, disagreeing.
> The design below is the surviving one; `biomes/<WORLD>.md` is the location
> `biomes/README.md` defines, and Verdant Valley already uses it.

**Owner-directed 2026-09-22:** *floating spires, future-like castle
architecture — a floating citadel with varying decorations and objects.*

| | |
|---|---|
| Content | `src/shared/Content/Worlds/SkyCitadel.luau`, `Content/Chunks/SkyCitadel.luau` |
| Generator | `assets/source/worlds/sky_citadel/build_sky_citadel_kit.py` |
| Review renders | `assets/source/worlds/sky_citadel/render_review.py` → `renders/*.jpg` |
| Exports | `assets/export/worlds/sky_citadel/chunk_*.fbx` |
| Contract | [`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](../MODULAR_MAPS.md) |

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
| *Crossroads* — Arcane Prism | a great glass prism hung over a compass rose, ringed, held by four gold-tipped pylons that stop short of it | 60 → 160 |
| *Lighthouse* | violet-banded white tower, open lantern with an azure core, antenna | 160 |
| *Sky Tree* | white-barked trunk, branches, a canopy of green and glass orbs | 160 |
| *Banner mast* | alloy mast with three gold crossbars and violet banners | 160 |
| *Shattered span* — stepping plate · span debris · Sundered Spire | 18-stud hex plates a stride apart, each on its own shard; tumbling fragments; a spire whose crown hangs above its stump | 0 · 4–9 · 160 |
| *Aviary* — cage · bird · perch tree · birdbath | five meridian ribs, two hoops and a gold crown; low-poly birds in flight; white trees; glass basins | 50 · 3 · 16 · 4 |
| *Archive* — bookshelf · ribbed vault · tome · map table · clock tower | shelf walls of coloured spines; white arches with azure inner ribs; floating open books; an azure globe; a four-faced clock under a violet roof | 8–10 · 38 · — · 10 · 160 |
| *Aether Springs* — terrace · ramp · light-fall · Cascade Tower | raised walkable decks; 3-over-12 wedges; water sheets falling off the rim; gold-rimmed bowls spilling glass down a white column | 3–6 · — · 58 down · 160 |
| *Lights* — lamp · brazier · light pillar | three light props, assigned per piece so avenues differ | 7–11 |

#### What floats on purpose

The hand pass (`CHUNK_AUTHORING.md`) asks for floating objects to be caught.
In this world some float deliberately, and this is the complete list — anything
else floating is a bug:

spire halos · floating crystals · the pedestal and obelisk-top crystals ·
anti-grav pylons · the fountain's crystal and halos · the corner beacons · the
skiff · the great hoops · the wind altar's shards · the orrery's rings and
planets · the Arcane Prism · the birds · the tomes · the span debris · the
Sundered Spire's crown · the drifting lintel · the keel hoops · the stepping
plates · the keel itself. (Lamp crystals and the gate and turret finials sit
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

### Lighting and ambience — sunrise above the cloud sea

**Chosen 2026-09-23.** The citadel is white and futurist, and the light that
makes white architecture read as both clean and precious is a **low sun**: gold
on every face that turns east, cool blue in every shadow, a sky running from
cobalt overhead to rose at the horizon, and the last few stars still out.

It is also the one hour nobody else holds. Verdant Valley is midday, Ethereal
Scape a white afternoon and deliberately the brightest world, Emberfall an
ash-red dusk, Astral Reach midnight. **Dusk here would have read as a paler
Emberfall; full morning sun, as a second Ethereal Scape.**

| | Value | Why |
|---|---|---|
| `ClockTime` | 6.4 | the sun just clear of the horizon — long raking light |
| `ColorShiftTop` / `Bottom` | gold / cobalt | the warm-lit, cool-shadowed split that sells the hour |
| `Atmosphere` | density 0.3, warm `Color`, cobalt `Decay`, glare 0.7 | the gradient sky; replaces fog |
| `Sky` | sun 16°, 300 stars | a big dawn sun, stars fading |
| `Bloom`, `SunRays`, `Grade` | restrained | glow on the white and gold, faint rays, a slight warm grade |
| `CloudSea` | three layers, 200 / 330 / 520 studs down, under a `CloudCeiling` of 130 (keels reach 96) | near: heaped sunlit cumulus with lavender undersides, tufted, opaque, flat-bottomed. Middle: broad, flatter, cooler banks. Deep: low lumpy banks, almost still. No wisps: the citadel is looked down on, and from above a wisp is a flat oval. Different speeds and headings give parallax |
| `Motes` | sparse, slow, gold | high air catching the light |

**What the walks showed before this was fixed:** a purple dusk. That was never
Sky Citadel's look — the hub's `Atmosphere` stayed in `Lighting`, and while one
exists Roblox ignores fog entirely, so every world wore the hub's haze. The
ambience now sets the hub's scene aside on entry.

**What cannot move yet:** the floating shards, rings and birds are baked into
each piece's single mesh. They are the first kit to be re-exported under
`CHUNK_AUTHORING.md` convention 6 (structure and ambient scenery separate).

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

## The kit — 22 pieces

All twenty-two are exactly **256 × 256 × 256**: footprint ±128, bottom at −96,
crown at +160. Origin at the centre of the footprint on the walk plane.

**Delivered and uploaded 2026-09-23**, as `.rbxmx` models each wrapping one
MeshPart that already carries its `rbxassetid` — so there was no upload step on
our side, exactly as Verdant Valley arrived. The files are kept in
`assets/rbxm/chunks/sky_citadel/` as provenance and a re-import path; the ids in
`Content/AssetManifest.luau` are the load route, and `ChunkLoader` calls
`CreateMeshPartAsync` on them.

**Re-imported the same day with the scenery split out** (`CHUNK_AUTHORING.md`
convention 6). The generator now writes two FBXs, and the owner imported each
once:
- `SC_STRUCTURE.rbxmx`: one Model of 22 structure-only MeshParts, whose ids
  replaced the originals in the manifest.
- `assets/rbxm/props/SC_PROP_LIBRARY.rbxmx`: 22 prop kinds.

168 placements of those props live in `Content/Props/SkyCitadel.luau`. A check
of the generator confirms that the structure geometry is vertex-for-vertex the
same as the saved `.blend`, so the scenery split changed nothing a player walks
on.

**Props and their motion:**

| Prop | Motion |
|---|---|
| crystal, pylon, tome | Hover |
| beacon, lintel | Float |
| hoop | Roll: slow, in its own plane only |
| keel ring | Spin |
| skiff | Moored |
| debris | Tumble |
| bird | Bird |

| chest (5), vault door, forcefield | **fixtures** (convention 7, build spec §7.5): server-placed, collidable; chests open once per party, the vault once per player who uses a key |

**The treasury's vault is a real opening.** `holed_block` builds the keep
with a round tunnel 12 deep behind the door, lined `VaultDark` with a gold ring
at the back, as one closed shell so the lining faces inward. The door (radius
7, down from 8 so the tunnel fits the wall) spins, then slides 6 studs into it.

**Fixed on the same walk:**
- a crystal cluster that stood beside the treasury on thin air;
- Path Straight's two spires, half off the pier;
- the entry towers' bases, overhanging the plaza edge;
- the Ascent Gate's pyramids rising through the roof beams (they now sit on
  capitals the beams run into), and its lintel z-fighting the pylons.

`validate()` now also checks that everything grounded stands wholly on its
deck (`ground_report`).

**Chests** are a hollow body with treasure inside (gold coins, nuggets, a gem)
and a rounded, strapped lid on two real hinges along `CHEST_HINGE`, the same
line the lid pivots on in game. **The vault door** is a full plate out to its
gold rim, seated in a tunnel 0.11 wider: closed, it shows only a hairline
seam.

The aviary's 15 birds circle the cage as one flock, their wings beating
(separate `prop_bird_wing_*` meshes, `Wing` class). Every bird's full circle is
proven clear of trees, bars and the other birds (`clear_bird_orbits`), which
lifted two birds, by 1 and 11 studs.

Two numbers were **read off the delivered meshes rather than trusted**:

- every piece measures exactly 256³, which is what the content declares and
  what `ChunkLoader` forces onto `mesh.Size` — a box that differed would have
  been silently stretched;
- every piece carries `PivotOffset.Y = −32`, the walk plane 32 studs below the
  box centre. That is **`GroundOffsetY = 96` arriving from the art side**,
  independently of the generator that derived it. The two agree.

The pieces are **untextured**: `TextureID` is null on all 22, and the look is
the mesh's own vertex colour with a flat `Color3`. Whether
`CreateMeshPartAsync` preserves vertex colour is a Studio question —
`TESTING.md` Test Q.

### Variety: five axes, mixed differently on every piece

Owner review of the 12-piece kit (2026-09-22): *"each piece is very similar to
the next."* It was: every piece was one white slab on the same cone keel,
ringed by the same parapet, lit by the same lamps, marked by the same needle
spire. Pieces are now built from five independent axes, and the table below
is arranged so neighbours in it differ on most of them:

| Axis | Options |
|---|---|
| **Shape** | one deck · an **archipelago** of islets joined by short railed bridges · a bare span with no deck at all · floating stepping plates |
| **Floor** | white · gold rays · planks · checker · lawn · **night sky** (dark deck, star inlay) · slate yard with a grid · compass rose · hazard stripes · gold grid · glass mosaic · violet carpet |
| **Edge** | castle parapet · railing · low glowing kerb · clipped hedge |
| **Keel** | cone · stepped ziggurat · twin cones · hanging crystal roots · engine drum with nozzles · cone ringed by floating hoops · (+ hanging vines on the garden pieces) |
| **Landmark** | needle spire · spired keep · lighthouse · Sky Tree · Arcane Prism · banner mast · clock tower · Cascade Tower · Sundered Spire · birdcage crown · turbine · observatory mast · signal mast · Crown Spire |

Every landmark reaches exactly +160: it pins the top of the bounding box.

| File | Role | Openings | Shape | Floor | Edge | Keel | Landmark | Tris |
|---|---|---|---|---|---|---|---|---|
| `chunk_entry` | ENTRY | N | octagon | gold rays | parapet | cone | the Beacon (spire) | 5,158 |
| `chunk_path_straight` | PATH | N S | hex pier | planks | railing | twin cones | gatehouse + mast spire | 4,234 |
| `chunk_path_skyport` | PATH | N S | pier + dock islet | planks · hazard pad | railing · kerb | ziggurat · engine | signal mast | 4,234 |
| `chunk_path_hoops` | PATH | N S | bare span + 2 satellites | glass | railing | plumb-bob · roots | satellite spire | 4,890 |
| `chunk_path_shattered` | PATH | N S | **8 floating plates** + 2 satellites | white/pale plates | kerb | a shard under each plate | **Sundered Spire** | 2,562 |
| `chunk_path_aviary` | PATH | N S | octagon under a **cage** | lawn + stepping path | railing | roots + vines | cage crown spire | 6,300 |
| `chunk_crossroads` | PATH | **N S E W** | octagon, 4 mouths | **compass rose** | kerb | ziggurat | **Arcane Prism** | 3,158 |
| `chunk_path_bend` | PATH | S **E** | octagon | checker | railing | crystal roots | spired keep | 3,464 |
| `chunk_path_bend_west` | PATH | S **W** | octagon + lighthouse islet | **night** + compass | kerb | engine | **lighthouse** | 4,060 |
| `chunk_vault_turn` | COMBAT | S **E** | octagon | gold grid | parapet | crystal roots | spire on the keep | 3,726 |
| `chunk_aether_springs` | COMBAT | S **W** | chamfered square, **two raised terraces** | glass mosaic | kerb, open east rim | cone + **falls** | **Cascade Tower** | 3,390 |
| `chunk_garden_terrace` | COMBAT | N S | **three islets** | lawn | hedge | roots + vines | **Sky Tree** | 5,684 |
| `chunk_observatory` | COMBAT | N S | 12-gon + **raised deck** | **night sky** | railing | cone + floating hoops | observatory mast | 5,750 |
| `chunk_armory` | COMBAT | N S | yard + barracks islet | slate yard, grid | parapet | twin cones | **banner mast** | 6,190 |
| `chunk_archive` | COMBAT | N S | chamfered rect, **roofed aisle** | dark checker · violet carpet | kerb | ziggurat | **clock tower** | 8,594 |
| `chunk_spire_court` | COMBAT (gate-court) | S · N `ASCENT` | chamfered square | white | parapet | cone | twin crown spires | 7,594 |
| `chunk_spire_court_b` | COMBAT (gate-court, rare) | S · N `ASCENT` | long octagon + **raised nave** | checker | railing | twin cones | turbine | 5,020 |
| `chunk_side_lookout` | SIDE | S | small 12-gon | pale rays | railing | crystal roots | signal mast | 2,396 |
| `chunk_boss_clearing` | BOSS | S `ASCENT` | round arena | inlaid rings | parapet | engine | Crown Spire | 5,744 |
| `chunk_cap_crumbling` | **CAP** | S | a span that **breaks off** | white | railing, one bent | spine | **Fallen Tower** (leaning) | 1,640 |
| `chunk_cap_overlook` | **CAP** | S | railed round terrace | pale rays | railing | crystal roots | light obelisk | 2,880 |
| `chunk_cap_sealed_gate` | **CAP** | S | walled islet | checker | parapet | ziggurat | spire behind a **shut gate** | 3,406 |

Weights and `MaxPerLayout` are in `Content/Chunks/SkyCitadel.luau`. Every
COMBAT piece, the crossroads and the lookout are once per layout.

### The shape of a run: turns, one intersection, no dead ends

Owner review: *"there is only 1 turning piece, and 0 intersections … the vault
can only be used for loot, and then it dead-ends."* Three changes answer it:

- **Four turns, two each way.** Right: the Spired Keep bend and the vault. Left:
  the lighthouse bend and the Aether Springs. Two of them are COMBAT decks, so
  a turn can be a place and not only a corridor. A test asserts both
  directions exist.
- **One intersection.** The crossroads has a `SKYWAY` mouth on every side.
  That needed a **System change** — `ChunkCore` used to leave every piece by its
  *first* valid exit, so a four-way piece would have gone straight on every
  seed. It now takes a **seeded pick** among the valid exits (only drawn when
  there is a choice, so single-exit kits consume no extra numbers). Asserted:
  across 300 seeds the crossroads leaves by more than one mouth.
- **No dead ends on the path.** The vault is now `chunk_vault_turn`, a COMBAT
  deck you pass through on a right turn, its keep and door beside the route.
  The optional pocket is a new, small **`chunk_side_lookout`** — and
  `IncludeSide` is now **consumed**: after the arena is placed, the assembler
  hangs one SIDE chunk off a spare socket (a crossroads branch, typically),
  tried in seeded order until one fits. `GameConfig.Expedition.IncludeSide`
  switches it; the expedition passes it. It also means **Verdant Valley's
  Hollow is placed for the first time** — asserted.

### No opening onto nothing: the caps

Owner-directed: *"I don't want any paths to lead to 'nothing', unless that
specific chunk is a dead end, crumbling bridge, etc."*

A **CAP** is a new role: a one-socket piece authored as an ending. There are
three, each a different kind of ending — a span that **breaks off** over a
drop, with its far half falling away and the Fallen Tower leaning over the
gap; a railed **overlook** with telescopes and a light obelisk; and a citadel
**gate that stays shut**, sealed doors behind a force field.

After the path, the arena and the side pocket are placed, `ChunkCore` puts a
cap on **every socket still open**. If some socket cannot take any cap
(everything collides), the attempt fails and the next seed is tried. So in a
world that has caps, a map never ships an opening onto nothing — asserted over
200 seeds each with and without the side pocket, by checking that every socket
of every placed piece meets another piece's socket head-on at the same point.
A world without caps keeps the old behaviour; Verdant Valley has none yet, so
its Meadow's west mouth can still face nothing when the Hollow is not there.

**How many of each** (why this is enough): only the crossroads has more
sockets than the path uses, so a map needs at most **two** caps (three spare
mouths minus the pocket); the three caps are unlimited per layout and equally
weighted, so the two ends of one crossroads can differ. Every other piece has
exactly the sockets it uses.

| Role | Pieces | Notes |
|---|---|---|
| ENTRY | 1 | always the first piece |
| PATH | 8 | 4 straights, 1 broken span, 1 aviary, the crossroads, 2 bends (1 each way) |
| COMBAT | 8 | 4 straight decks, 2 turning decks (1 each way), 2 gate-courts |
| SIDE | 1 | the lookout, on a spare mouth |
| CAP | 3 | dead ends authored as dead ends |
| BOSS | 1 | always the last piece on the path |

Review renders, `assets/source/worlds/sky_citadel/renders/`:

- `kit_overview.jpg` — all twenty-two on the review grid, rows of four (the caps are row 6)
- `preview_chain.jpg` — entry → **crossroads** (its west mouth closed by the sealed-gate cap, the lookout on its east
  branch) → shattered span → **west bend** → archive → Hall of Winds → arena
- `preview_corner.jpg`, `preview_corner_top.jpg` — four pieces at four yaws
  meeting at one corner: the beacon check
- a hero and a ground-level shot of each piece

### Axes

Blender +Y is Roblox **north** (−Z) under `-Z Forward, Y Up`; Blender +X is
Roblox +X. **Verified in the written files, not assumed:** deck-edge vertices
were read out of each turning piece's FBX — bend `SE`, west bend `SW`, vault
`SE`, springs `SW`, crossroads `NSEW`, lookout `S` — matching the socket data.

### How to change it

The `.blend` is an **output**. The generator rebuilds the kit from scratch, so
edit the script, not the file:

```
blender -b --factory-startup --python assets/source/worlds/sky_citadel/build_sky_citadel_kit.py -- --export
blender -b --factory-startup --python assets/source/worlds/sky_citadel/render_review.py
```

The first rebuilds, validates, exports every FBX, **re-imports each one and
measures it**, and saves the `.blend`. It refuses to export if any piece fails
validation. The second renders the review set (42 images). Both run headless
in seconds — see *Render headless* below.

`validate()` checks, per piece: footprint exactly 256 × 256; height exactly
−96 → +160; footprint centred on the origin; under 10,000 triangles; flat
shaded; **every float clear of every other float, solid and deck, and ≥ 4 inside
the tile edge**.

To add a piece: write a `build_<name>()` that ends in `finish(p)`, add it to
`BUILDERS`, register anything that floats (`float_crystal`, `scatter_floats`,
`p.float_`) and anything large (`p.solid`, `p.solid_box`), give it one landmark
reaching `CROWN_TOP`, and pick a combination of the five axes no neighbour has.

---

## Hand pass

### 2026-09-22 — the caps

| Check | Result |
|---|---|
| **Floating objects** | The crumbling span's falling half is eight scattered fragments, each placed only where the checker accepts it. |
| **Edges** | `preview_chain.jpg`: the crossroads now has no free mouth — lookout east, sealed gate west. Test: in 400 generated maps, every socket meets another. |
| **Scale** | The gate's doors are 22 tall, the force field 18 — a wall, not a door you could step round. The overlook's railing is waist height all the way round. |
| **Reads as an ending** | Checked on the ground shots: the gate is plainly shut, the span plainly broken, the overlook plainly a place to stop and look. |

### 2026-09-22 — variety, turns, the intersection, and four more

| Check | Result |
|---|---|
| **Floating objects** | `validate()` on all 19, including the new scattered floats (birds, tomes, span debris) — each placed only where the checker accepts it. |
| **Clipping** | The checker caught two real faults while building and both were fixed: the skiff's box was tested as the circle round it (the box test is now an exact separating-axis test), and a lookout crystal had been put through its own signal mast. |
| **Scale** | Shelves 8–10 (a reading room, not a warehouse), the cage 50 high, stepping plates 18 across with ~1.5-stud gaps (a stride, not a jump), terrace ramps 3 over 12–14. |
| **Edges** | `preview_chain.jpg`: straight through the crossroads, the lookout on its east branch, left at the lighthouse, and on to the arena — every join deck to deck. |
| **Origin** | Every footprint centred on (0, 0) within 0.01. |
| **Budget** | The archive first came in at 13,790 triangles — every book spine a box. Wider spines, three shelf rows and one outer shelf row brought it to 8,594. |

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
6. **Triangle budget.** The archive is highest at 8,594 of 10,000.
   `validate()` fails over 10,000.
7. **Gaps you can see through.** The shattered span's plates are ~1.5 studs
   apart. With a single-mesh default-fidelity hull (risk 4) those gaps may be
   filled in; with precise collision a character's foot cannot fall through a
   gap that size either way. Worth confirming on the first walk.

---

## Render headless

Rendering through the Blender MCP bridge inside the interactive session crashed
Blender twice in a row on 2026-09-22, on the same shot (the court's ground
view). The headless run renders the whole review set in seconds and never
touches the open session, so both scripts are documented as headless-first.
Building (no render) through the bridge worked fine.

---

## Next

> **2026-09-25:** the kit has had its refinish and detail passes: off-grey support lines on the shaft corners,
> roof variety, and animated props (orrery rings Spin, turbine rotors Roll). Birds fly at a constant 14 studs/s on
> radius-aware orbits. `validate()` enforces `boss_sightline`, so nothing blocks the view into the boss arena.
> The crossroads piece is on hold for its own pass. The items below are the original list.


1. **Import one piece into Studio and measure it** — 256 × 256 × 256, and note
   whether the vertex colours survive (risk 3).
2. Land `GroundOffsetY` and the collision-fidelity option in `ChunkLoader`
   (risks 1, 4) before uploading the rest.
3. **Walk a generated map.** The first thing worth judging is whether the
   shattered span's stepping plates and the terrace ramps feel right under a
   real character — both are sized by arithmetic, not by a walk.
4. Retune `Environment` once a piece has been seen in Studio.
