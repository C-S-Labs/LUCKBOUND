# The Crossroads — Blender build brief

**What this is.** A prompt to hand to an AI assistant driving Blender, to build
the Crossroads: LUCKBOUND's hub, and the first thing every player sees.

**How to use it.** Everything between the `COPY FROM HERE` / `COPY TO HERE`
markers is the prompt. Everything outside is reference for us — it names repo
paths the modelling session cannot see.

**Where the numbers come from.** Every dimension below is read out of
`GameConfig.HubLayout` and `Content/Hub/Crossroads.luau`, not invented. The
game already builds a blockout hub at exactly these measurements and cuts its
walkways to meet them, so art built to this drops in without moving anything.

**The Fate Engine is not in this brief.** It exists, it is finished, and it
occupies the centre. The brief reserves its footprint and asks for nothing
inside it.

---

## Note for us, not for the modeller

The four districts the owner named — **shop, discovery archive, leaderboard,
training ground** — do not match the four in `Crossroads.Districts` today:

| Brief | Today | |
|---|---|---|
| Leaderboard | `HALL_OF_LEGENDS` | same thing, renamed |
| Discovery Archive | `DISCOVERY_ARCHIVE` | unchanged |
| Training Ground | `TRAINING_GROUNDS` | unchanged |
| **Shop** | `EXPEDITION_GATE` | **replacement** |

The Gate becomes redundant under the owner's stated direction that the Fate
Engine's portal becomes the way into biomes (`STATUS.md` §4). That swap is a
content change gated on the portal-as-entry spec amendment, and is deliberately
**not** made yet. The brief asks for a Shop because that is what the finished
hub wants; the district table catches up when the amendment lands.

---

# ─── COPY FROM HERE ───

I have Blender connected. Build me the **Crossroads** — the central hub of a
Roblox game called LUCKBOUND. It is the first place every player stands, and it
has to look deliberate: an ancient ceremonial plaza that has been maintained
and built upon, with a monumental arcane portal at its centre and four
districts around it.

Follow the dimensions literally. They are not preferences — game code already
builds walkways that meet these exact numbers, so anything off-measure will not
connect.

## How to work

**Write Python and run it in Blender. Do not place objects by hand.**

**Build in five stages, and verify after each before moving on:**

1. Materials — all six, with the exact palette RGB
2. The plaza floor and its ring
3. The four walkways and the spawn approach
4. The four district platforms
5. District dressing, then flat shading and the final checks

After each stage, query the scene and report what Blender **actually contains**
— names, dimensions and positions read back, not what your script intended. A
script that silently does nothing looks exactly like success until the export
is opened.

**Make each stage idempotent:** delete any object you are about to create if
one with that name already exists, so re-running a stage after a fix does not
leave `Plaza.001` behind. A `.001` suffix means the game cannot find the part.

## Scale law — read this first

**1 Blender metre = 1 Roblox stud. Do not deviate.**

Before building anything, place a reference cube **2 m wide × 5 m tall × 1 m
deep** at the world origin, named `SCALE_REF_R6`. That is the size of a Roblox
character. Every dimension below is already correct against it. Delete it only
at the very end, after the final check.

Check your work against that cube, not against a feeling. An earlier asset on
this project shipped ten times oversized because it was measured against a
reference that was itself wrong.

## Style law — low poly, flat shaded, no textures

**This is a low-poly game**, in the literal sense: every curve resolves into a
small number of flat faces you could count, and every face is **flat shaded** so
it catches light as its own plane.

| Do | Do not |
|---|---|
| Shade Flat on every object | Shade Smooth, or Auto Smooth |
| Cylinders of 8–24 sides | 64, or "enough to look round" |
| One flat colour per material | textures, veining, gradients, roughness maps |
| Let facets be visible | subdivision, bevel modifiers, smoothing groups |

**No image textures of any kind.** No UV unwrapping needed. Colour is flat
material colour and nothing else — the palette carries the look.

**Do not go overkill.** This is a large floor plan, and the temptation is to
fill it. Resist. The hub should read as *spacious and ceremonial*, not busy. The
portal at the centre is the hero; everything else frames it and must not compete.

## Orientation and the floor plan

- **Up is Blender +Z.** The plaza is flat and centred on the world origin.
- **+Y is NORTH**, −Y is south, +X is east, −X is west.
- Everything is measured from `(0, 0, 0)`, the dead centre of the hub.

```
                      NORTH  +Y
                   Leaderboard
                    (0, 400)
                         │
                         │  walkway
                         │
   WEST              ┌───┴───┐              EAST  +X
   Training ─────────┤ FATE  ├─────────── Discovery
   Ground            │ENGINE │              Archive
   (-400, 0)         └───┬───┘              (400, 0)
                         │
                         │  processional (wider)
                         │
                       Shop
                    (0, -400)
                      SOUTH  -Y
```

## Build these objects

Give every object **exactly** the name in the left column. No `.001` suffixes,
no prefixes.

### The floor

| Name | Shape | Size (m) | Position (centre) |
|---|---|---|---|
| `Plaza` | cylinder, **24 sides** | 1150 across × 14 tall | `(0, 0, -7)` — top surface flush with Z 0 |
| `PlazaRim` | ring / torus, 24 segments | 1150 outer, 200 wide band | `(0, 0, 0.3)`, lying flat, a shallow raised border |

`Plaza` is the walkable ground. **Keep its top perfectly flat** — no bumps, no
raised centre. Everything else sits on it.

### The Fate Engine's reserved footprint

| Name | Shape | Size (m) | Position |
|---|---|---|---|
| `EngineReserve` | cylinder, 16 sides | **46 across × 2 tall** | `(0, 0, 1)` |

**Build this as a plain marker and nothing else.** It marks where the finished
Fate Engine sits, so the walkways have something to meet. Leave the volume above
it completely empty — the portal is 22 m across and 58 m tall and already
exists. Do not model a portal, a ring, a plinth or an altar.

Keep a **60 m radius clear of all scenery** around the centre. The portal is the
hero of this space.

### The four walkways

Raised paths from the plaza centre out to each district. Each runs from radius
**20** to radius **400**.

| Name | Width (m) | Runs toward |
|---|---|---|
| `Walkway_North` | 44 | Leaderboard, `+Y` |
| `Walkway_East` | 44 | Discovery Archive, `+X` |
| `Walkway_West` | 44 | Training Ground, `−X` |
| `Processional_South` | **72** | the Shop, `−Y` |

All four are **1.5 m thick**, with their **top surface at Z 1.5** — a single
low step up from the plaza, never a wall. The south one is wider on purpose:
it is the approach players walk in along, and it should read as the formal
entrance.

Players spawn at `(0, −250)` facing the centre, so the south processional is
the first thing anyone sees. Give it a little more care than the other three.

### The four district platforms

Each sits at its compass anchor, top surface at **Z 14**, reached by its
walkway.

| Name | Size (m) | Position | Is |
|---|---|---|---|
| `District_Leaderboard` | 320 × 250 × 14 | `(0, 400)` | tiered seating facing a tall standing monument — where players' names are listed |
| `District_Archive` | 210 × 210 × 14 | `(400, 0)` | a domed rotunda, open-sided, shelves and reading plinths around the inside wall |
| `District_Shop` | 290 × 240 × 14 | `(0, −400)` | a covered market colonnade — stalls under a roof, counters facing the walkway |
| `District_Training` | 235 × 235 × 14 | `(−400, 0)` | an open sand-floored yard with a low surrounding wall and dummy posts |

**Each platform is one object at the size above.** Put its dressing in separate
objects named `<DistrictName>_<Thing>`, for example `District_Archive_Dome`,
`District_Training_Dummy1`.

Keep the dressing **sparse and readable**. Four or five objects per district is
plenty. Silhouette matters far more than detail — a player should be able to
tell the market from the archive from 300 m away by shape alone.

### Scenery

| Name | |
|---|---|
| `FloatingIsland1`…`FloatingIsland8` | rock slabs drifting well outside the plaza, between radius 700 and 1800, at heights 100–400. Backdrop only, never walkable. |
| `Pillar_NE`, `Pillar_NW`, `Pillar_SE`, `Pillar_SW` | four tall broken columns on the diagonals at radius 520, 90 m tall, marking the corners without blocking sightlines |

Scenery may reach out to radius **2000**. Nothing beyond the plaza is walked on.

## Materials — flat colour, no textures

Exact names, exact RGB. This is the game's hub palette and the Fate Engine is
already painted from it — a piece that invents its own colours will read as
imported from a different game.

| Material name | Goes on | RGB |
|---|---|---|
| `Marble_Pale` | `Plaza`, walkways, district platforms | `226, 221, 234` |
| `Plaza_Stone` | `PlazaRim`, ground detail | `58, 52, 76` |
| `Walkway_Stone` | walkway edging, steps | `78, 70, 98` |
| `Basalt_Dark` | pillars, heavy structure, roofs | `64, 58, 78` |
| `Slate_Rune` | carved detail, dummy posts, shelving | `88, 82, 104` |
| `Trim_Gold` | banding, rails, monument capitals | `230, 178, 74` |
| `Inlay_Neon` | glowing inlays and lamps — **use sparingly** | `68, 135, 123` |

**Every one is a flat base colour with no texture, no image map, no roughness,
normal or metallic map.** Gold is the only warm note in a cool palette; if it is
everywhere it stops being an accent.

### Light the scene like the hub

The Crossroads sits under a low, raking pre-dawn light — warm gold from above,
cool purple ambient fill, a deep violet sky. Set your viewport up that way
before judging anything. A piece that looks right under Blender's default
lighting will read washed out and shapeless in the game, because flat-shaded
facets live or die on where the key light is.

## Hierarchy

Parent everything to empties so the export carries the structure. The empties
need these exact names too.

```
Crossroads                    (empty, at world origin)
├── Plaza
├── PlazaRim
├── EngineReserve
├── Walkways                  (empty)
│   ├── Walkway_North / _East / _West
│   └── Processional_South
├── Districts                 (empty)
│   ├── District_Leaderboard  + its dressing
│   ├── District_Archive      + its dressing
│   ├── District_Shop         + its dressing
│   └── District_Training     + its dressing
└── Scenery                   (empty)
    ├── FloatingIsland1 … 8
    └── Pillar_NE / _NW / _SE / _SW
```

Every empty sits at the **world origin**, not at the centre of its children.

## Polygon budget

**Hard ceiling: 40,000 triangles for the entire hub.** Expect to land nearer
25,000.

That is not a performance number — it is the style. Detail lives in silhouette,
in facet angles and in where the gold lands, never in polygon count. If a shape
needs more geometry to read, change the shape.

Rough guide: the plaza and rim under 1,000 between them; each walkway under 200;
each district platform under 500; district dressing under 3,000 each; scenery
under 4,000 in total.

## Export

1. Select everything and apply `Object ▸ Shade Flat` one final time. Confirm no
   object has an Auto Smooth or Smooth By Angle modifier left on it.
2. Delete `SCALE_REF_R6`.
3. Select the `Crossroads` empty and all descendants.
4. `File ▸ Export ▸ FBX`, with **Selected Objects** on, **Apply Scalings: FBX
   All**, **Forward: −Z Forward**, **Up: Y Up**, **Apply Modifiers** on.
5. Save as `crossroads.fbx`.

## Before you say you are done, verify

Report each of these back with the **actual measured number**:

1. `SCALE_REF_R6` is 5 m tall, and next to a walkway it towers over it — the
   walkways are a single low step, not walls.
2. `Plaza` is **1150 m** across and its top is flat at Z 0.
3. Every walkway's top surface is at **Z 1.5**, and every district platform's
   top is at **Z 14**.
4. Each district platform's centre is exactly **400 m** from the origin, on its
   compass axis.
5. `EngineReserve` is **46 m** across, and there is **nothing else** within 60 m
   of the origin. List anything that is.
6. **Every object is flat shaded.** Name any object still Shade Smooth or
   carrying a smoothing modifier — there should be none.
7. **No object has a texture, image map or UV-mapped material.** Every material
   is a flat base colour.
8. Each material's RGB matches the palette exactly. List them so I can check.
9. Object names are exactly as specified, with **no `.001` suffixes anywhere**.
   List every object name you created.
10. **Total triangle count.** It must be under 40,000. If it is in the hundreds
    of thousands, something got subdivided and the style is broken — find it and
    fix it before reporting.

If any number is off, fix it and re-report rather than telling me it is close.

# ─── COPY TO HERE ───

---

## After the FBX exists

1. Import into Studio (`Model ▸ Import 3D`).
2. **Check the scale against a real character before anything else** — and
   measure a walkway and a district platform too, never the reference rig
   alone. That mistake is what put the first authored asset on this project ten
   times oversized.
3. Right-click → **Save to File…** → **Roblox XML model files (*.rbxmx)** →
   `assets/rbxm/prefabs/HUB_CROSSROADS.rbxmx`.
4. Send it over. The prefab seam already exists and is proven on the Fate
   Engine, so wiring is a `Prefab` field and a paint table — no new code.

Expect the import to arrive at the wrong scale and with a flat hierarchy. Both
are normal, both are handled by `PrefabLoader`, and neither is the modeller's
problem.

---

## What actually arrived — 2026-09-18

The delivery is in: `assets/rbxm/prefabs/HUB_CROSSROADS.rbxmx`, 225 MeshParts,
plus an unbriefed second file, `HUB_BACKDROP.rbxm`, holding a mountain horizon.
Both are wired and the generated blockout hub no longer runs. Full measurements
live in `assets/rbxm/prefabs/README.md`.

**Two things the brief predicted, both handled in content:**

- It imported at **0.5×** → `Prefab.Scale = 2.0`, confirmed on six independent
  dimensions that agreed to four figures.
- The hierarchy came back **flat**, as expected.

**One the brief did not predict, and should next time:**

- **North arrived at Roblox `+Z`, and the game's north is `-Z`.** The FBX
  export settings in step 4 carry the exporter's axis convention, not the
  game's, so a 180° compass error is the *normal* outcome rather than a
  mistake. It is now corrected by `Prefab.YawDegrees` — a number in content,
  never a re-export. **A future brief should say so up front**, next to the
  scale warning, and should ask the modeller to confirm which way north points
  in the exported file.

**Where the delivery differs from what was asked**, recorded rather than
corrected — none of it is a fault:

| | Asked | Delivered (at Scale) |
|---|---|---|
| Plaza diameter | 1150 | 1305 |
| `Processional_South` width | 72 | 44 |
| District footprints | 210–320 | 300–400 |
| Pillar ring radius | 520 | 640 |

The dimensions the brief called load-bearing — walkway width, deck heights,
the 400-stud ring, and `EngineReserve` — all landed exactly. The ones that
drifted are the ones nothing connects to, which is the brief working as
intended.

The one worth noting for next time: **the south processional is no longer
wider than the other three walkways.** The brief asked for 72 against 44 and
explicitly said why — it is the approach every player walks in along. It came
back at walkway width, so the spawn approach lost the emphasis it was meant to
have. Not worth a re-export; worth restating if the hub is ever re-authored.

**What the brief got right and should be reused:** the reserved
`EngineReserve` footprint. Asking for a plain named marker at the centre and
nothing inside it gave the integration an exact registration point, and it is
now what the whole 225-part model is positioned from — in preference to the
model pivot, which is invisible metadata. **Every future hub-scale brief should
ask for a marker like it.**
