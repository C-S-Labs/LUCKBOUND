# The Fate Engine — Blender build prompt

**What this is.** A prompt to paste into Claude Desktop with a Blender MCP
connection attached. It builds the Fate Engine to the exact contract the game
already expects, so the export drops in without a single code change.

**House style.** Low poly, flat shaded, no textures, one hub palette — set out
in `ART_DIRECTION.md` and restated inside the prompt. Every hub asset follows
it, so the hub reads as one place rather than a gallery of unrelated pieces.

**Why it is this specific.** The owner chose the **whole rig** option: the
authored model replaces *everything* the Fate Engine is today, including the
portal rings. `Util/PortalRig` will not build this slot any more — it will
**drive** it. So every part the code looks up by name has to exist in the
export, spelled exactly right, with its origin in the right place. The names
below are not suggestions; they are the API.

---

## How to run this

**Attach or paste the block between the `COPY FROM HERE` / `COPY TO HERE`
markers** into Claude Desktop with a Blender MCP connection attached. Only that
block is instructions — everything outside the markers is reference for us, and
handing it over as well just adds noise about a repo the modelling session
cannot see.

Blender MCP works by executing Python inside Blender, so what Claude Desktop
will actually do is write and run a script. That is the right approach and the
prompt now says so explicitly: build in stages, verify between them, and never
try to do forty objects in one unverified call.

---

## The contract, for reference

`PortalRig` finds these by name and does this to them. Nothing else in the
model is touched, so decoration is free.

| Name | What the code does to it |
|---|---|
| `Plinth` | becomes `PrimaryPart`; the only collidable part of the rig |
| `OuterRing` | spins continuously about the walk-through axis, ~1 rad/s |
| `InnerRing` | spins the other way, ~1.4 rad/s, **and is tinted per rarity** |
| `PortalPlane` | **tinted per rarity**, transparency pulses, holds the light and particles |
| `Rune1`…`Rune8` | static |
| `Glyph1`…`Glyph8` | **tinted per rarity** |
| `Shard1`…`Shard6` | **tinted per rarity**, each spins slowly about its own vertical axis |
| `Platform` | static, collidable — the floor players stand on |
| `Inlay1`…`Inlay16` | static |
| `SpotAnchor` | holds the overhead spotlight |

**Tinted per rarity** is the rule that bites. The portal is recoloured every
roll — Common grey through Mythic — by setting `Color` on those parts. A
Roblox `SurfaceAppearance` (a PBR texture set) **overrides `Color` entirely**,
so any tinted part that ships with a baked texture will be stuck on whatever
colour it was painted and the whole rarity system goes dead on the Engine.
Those parts must be plain, untextured, near-white.

Lights, particles and attachments are **created by code**, not exported. Build
only geometry.

---

# ─── COPY FROM HERE ───

I have Blender connected. Build me a model called the **Fate Engine** for a
Roblox game. It is a monumental arcane portal on a raised marble dais — the
centrepiece of the game's hub, the thing every player walks to first.

This model has to satisfy an exact technical contract, because game code drives
its parts by name. Follow the naming, dimensions and origin rules literally.
Style is yours; the skeleton is not.

## How to work

**Write Python and run it in Blender. Do not place objects by hand.** There are
around fifty objects here with mandated names, exact positions and specific
origins — that is arithmetic, and a script gets it right every time where
hand-placement drifts.

**Build in six stages, and verify after each one before moving on:**

1. Materials — all six, with the exact palette RGB
2. The dais — `Platform` and the 16 inlays
3. The portal rig — `Plinth`, both rings, `PortalPlane`
4. The rune ring — 8 runes and 8 glyphs
5. The shards and `SpotAnchor`
6. Parenting, flat shading, and the final checks

After each stage, query the scene and tell me what you actually created — object
names, dimensions and positions read back from Blender, not what your script
intended to make. A script that silently no-ops is the failure mode here, and it
looks identical to success until the export is opened.

**Make the script idempotent.** Delete any object it is about to create if one
with that name already exists, so re-running a stage after a fix does not leave
`Platform.001` behind. If you do end up with a `.001`, the name is wrong and the
game will not find the part.

## Scale law — read this first

**1 Blender metre = 1 Roblox stud. Do not deviate.**

Before you build anything, place a reference cube **2 m wide × 5 m tall × 1 m
deep** at the world origin and name it `SCALE_REF_R6`. That is the size of a
Roblox character. Every dimension below is in metres and is already correct
against that reference — a 5 m person should look right beside all of it.
Delete `SCALE_REF_R6` only at the very end, after the final check.

A previous asset on this project shipped ~10× oversized because it was measured
against a rig that was itself wrong. Doorways came out 48 person-heights tall.
Check your work against the 5 m cube, not against a feeling.

## Style law — low poly, flat shaded

**This is a low-poly game.** Not "optimised", not "stylised" — low poly, in the
literal sense: every curve resolves into a small number of flat faces you could
count, and every face is **flat shaded** so it catches the light as its own
plane.

| Do | Do not |
|---|---|
| Shade Flat on every object | Shade Smooth, or Auto Smooth |
| Cylinders of 8–16 sides | 32, 64, or "enough to look round" |
| One flat colour per material | textures, veining, gradients, roughness variation |
| Let facets be visible | subdivision, bevel modifiers, smoothing groups |

**Flat shading is the whole style.** A low-poly mesh with smooth shading does
not read as stylised — it reads as a high-poly mesh that went wrong. After
building every object, select all and apply `Object ▸ Shade Flat`.

**No textures at all.** No image maps, no roughness/normal/metallic maps, no UV
unwrapping needed. Colour is flat material colour and nothing else.

The rest of this game's art is already built this way. This piece has to sit in
the same hub as everything else and read as the same hand.

## Orientation

- **Up is Blender +Z.**
- **The player walks through the portal along Blender ±Y.** So the portal rings
  stand vertically like wheels, and their faces point along ±Y.
- The rings' **rotation axis is horizontal, pointing along Y** — the same axis
  the player walks through.
- Everything is symmetrical about the world Z axis. The model's world origin
  `(0, 0, 0)` is the **hub floor at the dead centre of the Engine**. All heights
  below are measured up from there.

## Origins — the rule that makes animation work

Game code spins parts by rotating them about **their own origin**. An origin in
the wrong place turns a spin into a wobble.

- `OuterRing` and `InnerRing`: origin at the **hub of the wheel** — the ring's
  own centre, on the Z axis, at height 67. Not at the geometry's bounding-box
  centre if that differs; not at the world origin.
- `Shard1`…`Shard6`: origin at each shard's **own centre**, so it spins in place.
- Everything else: origin at its own geometric centre is fine.

In Blender: select the object, snap the 3D cursor where the origin belongs, then
`Object ▸ Set Origin ▸ Origin to 3D Cursor`.

## Build these objects

Give every object **exactly** the name in the left column. No suffixes, no
`.001`, no prefixes. If Blender appends `.001` to a duplicate, rename it.

### The dais

| Name | Shape | Size (m) | Position (centre) |
|---|---|---|---|
| `Platform` | cylinder, **16 sides** | 240 across the flats × 10 tall | `(0, 0, 5)` |
| `Inlay1`…`Inlay16` | thin flat spoke | 0.6 wide × 102 long × 0.12 thick | lying flat on the platform top, radiating from the centre, one every 22.5°, each spanning radius 3 → 105, top surface at height 10.02 |

`Platform` is the floor. Keep its top flat and walkable — no lip, no raised rim.
Leave the central **90 × 90 m square clear of obstructions**: there is an
invisible interaction pad there that players stand on to roll.

### The portal rig

| Name | Shape | Size (m) | Position (centre) |
|---|---|---|---|
| `Plinth` | octagonal prism, 8 sides | 84 across flats × **3 tall** | `(0, 0, 11.5)` — sits on the platform, spans height 10 → 13 |
| `OuterRing` | torus, standing vertically, **32 major × 6 minor segments** | 108 across the centreline, tube 7.2 thick → 115.2 overall | `(0, 0, 67)` |
| `InnerRing` | torus, standing vertically, concentric, **32 major × 6 minor** | 78 across the centreline, tube 3.6 thick → 81.6 overall | `(0, 0, 67)` |
| `PortalPlane` | flat **16-sided** disc | 78 across × ~3 thick | `(0, 0, 67)`, thin axis along Y |

`Plinth` is a true **octagon** — 8 sides, and at this style that is the real
shape rather than a cylinder standing in for one. `Platform` at 16 sides is
exactly twice that, so the dais and the plinth share a rhythm instead of
fighting.

**The 3 m plinth height is a hard cap, not a proportion.** A Roblox character
jumps about 7 m. An earlier version of this rig stood 18 m and walled the portal
off completely — players could see it and not reach it. Make it look monumental
by being **wide**, never by being tall.

`PortalPlane` is the fabric players walk through. It sits inside `InnerRing`,
filling it.

The top of `OuterRing` lands at about height 125. That is the Engine's crown and
it should read as the tallest thing in the hub.

### The rune ring

Eight stone plates around the top rim of the plinth, each with a glowing glyph
resting on it.

| Name | Shape | Size (m) | Position |
|---|---|---|---|
| `Rune1`…`Rune8` | flat slab | 13.2 tangential × 20.4 radial × 1.8 tall | on the plinth top, centred at radius 33.6, one every 45°, top at height 14.2 |
| `Glyph1`…`Glyph8` | flat plate | 6.6 × 6.6 × 0.72 | resting on its matching rune, centred at height 15.5, **rotated 45° about Z** relative to the rune |

`GlyphN` must sit on `RuneN` — matching indices, same angle around the circle.

**Glyphs carry no lettering.** Geometric shapes only: chevrons, radial slashes,
concentric arcs, a pierced diamond. Generated lettering reads as gibberish to
players and this project has a standing rule against it.

### The crystal shards

Six shards floating free above the dais, at different heights, each tilted
differently so the group never reads as mechanical.

| Name | Shape | Size (m) | Position |
|---|---|---|---|
| `Shard1`…`Shard6` | **hexagonal** crystal, tapered to a point at both ends — 6 sides, no more | ~20 × 20 × 48 tall | on a circle of **radius 100** about the Z axis, one every 60°, at heights varying between **50 and 140** |

Vary the heights properly — 55, 92, 138, 71, 120, 84 rather than an even ladder.
Tilt each one a little off vertical, up to about 20°, with a different spin
around its own axis. They must look scattered, not installed.

They are inside the platform's 120 m radius, so they float over the dais rather
than beyond it.

### The spotlight anchor

| Name | Shape | Size (m) | Position |
|---|---|---|---|
| `SpotAnchor` | small cube | 2 × 2 × 2 | `(0, 0, 300)` |

Invisible in game — code attaches a spotlight to it. Build it anyway; without it
the Engine has no key light.

## Materials — flat colour, no textures

Use Blender materials with these exact names. **Every one is a flat base colour
with no texture of any kind** — no image maps, no roughness, normal or metallic
maps, no UV unwrapping. Colour is the material's base colour and that is all.

These RGB values are the game's hub palette. They are not suggestions and not a
starting point — the whole hub is built from this one set, and a piece that
invents its own colours will read as imported from a different game.

| Material name | Goes on | RGB | Reads as |
|---|---|---|---|
| `Marble_Pale` | `Platform`, `Plinth` | `226, 221, 234` | pale lilac-white stone |
| `Basalt_Dark` | `OuterRing` | `64, 58, 78` | heavy dusk-purple stone |
| `Slate_Rune` | `Rune1`…`Rune8` | `88, 82, 104` | grey-violet carved slate |
| `Inlay_Neon` | `Inlay1`…`Inlay16` | `124, 245, 224` | emissive mint, glowing |
| `Trim_Gold` | optional accent banding on `Plinth` and `Platform` | `230, 178, 74` | warm gold — **use sparingly**, it is the only warm note and it stops being an accent if it is everywhere |
| `Tint_White` | `InnerRing`, `PortalPlane`, `Glyph1`…`Glyph8`, `Shard1`…`Shard6` | `255, 255, 255` | pure white, fully emissive |

### `Tint_White` is not laziness, it is the contract

Those parts are **recoloured by the game every time a player rolls** — the whole
portal turns Uncommon green, then Legendary gold, and so on. Roblox does that by
setting the part's `Color`, which multiplies against what you exported.

So for every object using `Tint_White`:

- **pure white base colour**, emission on
- **no texture of any kind**
- **no vertex colour painting** — that multiplies too

Colour them in your head if it helps, but export them white. If you paint
`InnerRing` blue it will be blue forever, and the rarity system dies on the most
visible object in the game.

### Light the scene like the hub, not like a studio

The hub sits under a low, raking pre-dawn key light — warm gold from above,
cool purple ambient fill, `ClockTime 4.5`. Set your viewport up that way before
you judge anything. A piece that looks right under Blender's default lighting
will read washed-out and shapeless in the game, because flat-shaded facets live
or die on where the key light is.

## Hierarchy

Parent the objects to empties so the export carries the structure:

```
FateEngine                 (empty, at world origin)
├── Platform
├── RuneInlay              (empty)
│   └── Inlay1 … Inlay16
├── EngineRig              (empty)
│   ├── Plinth
│   ├── OuterRing
│   ├── InnerRing
│   ├── PortalPlane
│   └── RuneRing           (empty)
│       ├── Rune1 … Rune8
│       └── Glyph1 … Glyph8
├── CrystalShards          (empty)
│   └── Shard1 … Shard6
└── SpotAnchor
```

The empties must carry those exact names too — code walks this tree.

Every empty sits at the **world origin** `(0, 0, 0)`, not at the centre of its
children. Only `OuterRing`, `InnerRing` and the shards have special origins.

## Polygon budget

The segment counts above already set this. Built as specified, the whole model
lands around **1,800 triangles**:

| | Triangles |
|---|---|
| `Platform`, 16-sided | ~90 |
| `Plinth`, octagonal | ~40 |
| 16 inlays | ~190 |
| `OuterRing` + `InnerRing`, 32 × 6 each | ~770 |
| `PortalPlane`, 16-sided disc | ~30 |
| 8 runes | ~100 |
| 8 glyphs | ~320 |
| 6 shards, hexagonal | ~240 |
| `SpotAnchor` | 12 |

**Hard ceiling: 5,000 triangles for the entire model.** If you are anywhere
near it, something has been subdivided that should not have been.

That is not a mobile-performance number — at this scale the game could afford
far more. It is the **style**. Detail lives in the silhouette, in the facet
angles and in where the gold accent lands, never in the polygon count. If a
shape needs more geometry to read, change the shape.

## Export

1. Delete `SCALE_REF_R6` — after the final check below, not before.
2. Select the `FateEngine` empty and all descendants.
3. Select everything and apply `Object ▸ Shade Flat` one final time. Confirm
   no object has an Auto Smooth or Smooth By Angle modifier left on it.
4. `File ▸ Export ▸ FBX`, with:
   - **Selected Objects** on
   - **Apply Scalings: FBX All**
   - **Forward: -Z Forward**, **Up: Y Up**
   - **Apply Modifiers** on
5. Save as `fate_engine.fbx`.

## Before you say you are done, verify

Report each of these back to me with the actual measured number:

1. `SCALE_REF_R6` is 5 m tall, and standing next to `Plinth` it reaches
   **well above** it — the plinth is a low step, not a wall.
2. `Plinth` is exactly **3 m tall**. Not 3.5. Not 6.
3. `OuterRing` measures **115.2 m** across at its widest.
4. The top of `OuterRing` is at height **~125 m**.
5. `OuterRing` and `InnerRing` both have their **origin at `(0, 0, 67)`** —
   confirm by selecting each and reading the origin, not the bounding box.
6. Both rings stand **vertically**, faces pointing along ±Y, so a character
   walking along Y passes through them.
7. **Every object is flat shaded.** Name any object still set to Shade Smooth,
   or carrying an Auto Smooth / Smooth By Angle modifier — there should be none.
8. **No object anywhere in the file has a texture, an image map, or a UV-mapped
   material.** Every material is a flat base colour.
9. The material colours match the palette RGB values exactly. List each
   material and its RGB so I can check.
10. Every object using `Tint_White` is pure white `255, 255, 255` with **no
    vertex colour painting**.
11. `Platform` has **16 sides**, `Plinth` has **8**, each torus is **32 × 6**,
    each shard is **hexagonal**. Report the actual counts.
12. Object names are exactly as specified, with **no `.001` suffixes anywhere**.
    List every object name you created so I can check.
13. **Triangle count for the whole model — it should be near 1,800 and must be
    under 5,000.** If it is in the tens of thousands, something got subdivided
    and the style is broken; find it and fix it before reporting.

If any number is off, fix it and re-report rather than telling me it is close.

# ─── COPY TO HERE ───

---

## After the FBX exists

1. Import it into Studio (`Model ▸ Import 3D`), which uploads the meshes and
   returns a `Model` of `MeshPart`s.
2. Check the `Scale_Reference` against a real character **before** anything else.
   Measure a doorway and a tree too, never the reference alone — that mistake is
   what put the first Ethereal Scape delivery 10× out.
3. Right-click the model → **Save to File…** → **Roblox XML model files
   (*.rbxmx)** → save as `assets/rbxm/prefabs/FATE_ENGINE.rbxmx`.
4. Send it over and the loader gets wired in the same pass.

The `assets/rbxm/prefabs/` folder and its loader do not exist yet — they are
the follow-up to this document, and the names above are what that loader will
look for.
