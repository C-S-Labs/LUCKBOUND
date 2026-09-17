# The Fate Engine — Blender build prompt

**What this is.** A prompt to paste into Claude Desktop with a Blender MCP
connection attached. It builds the Fate Engine to the exact contract the game
already expects, so the export drops in without a single code change.

**Why it is this specific.** The owner chose the **whole rig** option: the
authored model replaces *everything* the Fate Engine is today, including the
portal rings. `Util/PortalRig` will not build this slot any more — it will
**drive** it. So every part the code looks up by name has to exist in the
export, spelled exactly right, with its origin in the right place. The names
below are not suggestions; they are the API.

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
| `Platform` | cylinder, 64+ sides | 240 diameter × 10 tall | `(0, 0, 5)` |
| `Inlay1`…`Inlay16` | thin flat spoke | 0.6 wide × 102 long × 0.12 thick | lying flat on the platform top, radiating from the centre, one every 22.5°, each spanning radius 3 → 105, top surface at height 10.02 |

`Platform` is the floor. Keep its top flat and walkable — no lip, no raised rim.
Leave the central **90 × 90 m square clear of obstructions**: there is an
invisible interaction pad there that players stand on to roll.

### The portal rig

| Name | Shape | Size (m) | Position (centre) |
|---|---|---|---|
| `Plinth` | octagonal prism, 8 sides | 84 across flats × **3 tall** | `(0, 0, 11.5)` — sits on the platform, spans height 10 → 13 |
| `OuterRing` | torus, standing vertically | 108 across the centreline, tube 7.2 thick → 115.2 overall | `(0, 0, 67)` |
| `InnerRing` | torus, standing vertically, concentric | 78 across the centreline, tube 3.6 thick → 81.6 overall | `(0, 0, 67)` |
| `PortalPlane` | flattened lens / thin disc | 78 diameter × ~3 thick | `(0, 0, 67)`, thin axis along Y |

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
| `Shard1`…`Shard6` | elongated faceted crystal, tapered at both ends | ~20 × 20 × 48 tall | on a circle of **radius 100** about the Z axis, one every 60°, at heights varying between **50 and 140** |

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

## Materials

Use Blender materials with these exact names. They map to Roblox materials on
import, and the names are how I will find them.

| Material name | Goes on | Look |
|---|---|---|
| `Marble_Pale` | `Platform`, `Plinth` | pale warm marble, soft veining, matte |
| `Basalt_Dark` | `OuterRing` | dark volcanic stone, RGB around (64, 58, 78), rough |
| `Slate_Rune` | `Rune1`…`Rune8` | dark grey-violet slate, RGB around (88, 82, 104) |
| `Inlay_Neon` | `Inlay1`…`Inlay16` | emissive mint, RGB around (124, 245, 224) |
| `Tint_White` | `InnerRing`, `PortalPlane`, `Glyph1`…`Glyph8`, `Shard1`…`Shard6` | **pure white, fully emissive, no texture, no colour variation whatsoever** |

### `Tint_White` is not laziness, it is the contract

Those parts are **recoloured by the game every time a player rolls** — the whole
portal turns Uncommon green, then Legendary gold, and so on. Roblox does that by
multiplying against the part's base colour, and a **PBR texture set overrides it
completely**.

So for every object using `Tint_White`:

- **no image textures**
- **no baked colour**
- **no roughness, normal or metallic maps**
- pure white base, emission on

Colour them in your head if it helps, but export them white. If you paint
`InnerRing` blue, it will be blue forever and the rarity system dies on the
Engine — which is the single most visible feature in the game.

Everything using the other four materials may be textured freely.

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

This is a hub centrepiece rendered on phones, so keep it lean:

- `Platform`: 64-sided cylinder is plenty
- each torus: 48 segments around, 16 around the tube
- shards: under 200 triangles each — they are read as silhouettes
- **whole model under 60,000 triangles**

Detail belongs in the silhouette and the materials, not in the wireframe.

## Export

1. Delete `SCALE_REF_R6` — after the final check below, not before.
2. Select the `FateEngine` empty and all descendants.
3. `File ▸ Export ▸ FBX`, with:
   - **Selected Objects** on
   - **Apply Scalings: FBX All**
   - **Forward: -Z Forward**, **Up: Y Up**
   - **Apply Modifiers** on
4. Save as `fate_engine.fbx`.

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
7. Every object using `Tint_White` has **no image texture of any kind**.
8. Object names are exactly as specified, with **no `.001` suffixes anywhere**.
   List every object name you created so I can check.
9. Triangle count for the whole model.

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
