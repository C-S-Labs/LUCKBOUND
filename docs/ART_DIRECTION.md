# LUCKBOUND — Art Direction Brief

How to describe the look so it becomes code, and where authored art plugs in.

---

## The approach

**You describe, it gets built procedurally, meshes come later.**

Every visual lives in data:

| File | Holds |
|---|---|
| `src/shared/Content/Hub/Crossroads.luau` | Theme palette, lighting, all five zones, Fate Engine, islands |
| `GameConfig.HubLayout` | Named position anchors and hub dimensions |
| `GameConfig.Portal` | Every PortalRig tunable |
| `src/shared/Core/UITheme.luau` | Fonts, colours, radii for every screen |
| each world's `Environment` | Per-biome ambient, fog, brightness, clock |

`HubBuilder` reads that data and generates geometry. **It contains no art
direction at all.** If changing how something looks requires editing
`HubBuilder`, the schema is missing a field — that is the bug, not the look.

### The mesh seam

Every swappable piece exposes an optional `MeshId`. While `nil`, the builder
generates primitives. Set it and the builder uses the mesh at the same position,
scale and pivot:

```lua
FateEngine = {
	-- ...
	MeshId = "rbxassetid://1234567890",  -- ← one line, nothing else changes
}
```

Authored art replaces blockout **one piece at a time**, no flag day. A test
enforces that the seam exists on every swappable piece.

`HubBuilder` also skips generation entirely if `Workspace` already contains a
`Crossroads` — hand-authored geometry always wins over blockout.

> Mesh uploading is covered in `ADDENDUM_ASSET_PIPELINE.md`, which is
> **explicitly out of scope** until the gameplay loop is proven fun. It is
> proven for the roll; it is not yet proven for the full loop.

---

## What exists now

Built to the Biome Blueprint §2. Current state: functional blockout, **very
dark** — the first thing worth tuning.

| Zone | Position | What's there |
|---|---|---|
| Centre | (0,0,0) | Fate Engine: PortalRig @1.5×, 24-stud marble platform, radial rune inlay, 6 orbiting glass shards, gold spotlight |
| North (−Z) | (0,0,−46) | Hall of Legends: 3-tier semicircular amphitheatre, 5 World-First obelisks, cool museum spotlights |
| East (+X) | (46,0,0) | Discovery Archive: domed rotunda, 3 rings of orbiting shelves, teal + cosmic trim |
| South (+Z) | (0,0,46) | Expedition Gate: PortalRig @2×, 12-stud processional, flanking torch pillars |
| West (−X) | (−46,0,0) | Training Grounds: 30×30 yard, low fence, 3 dummies + boss dummy, warm torches |

Plus 14 deterministic floating islands (seeded, so every server shows one
skyline) and raised radial walkways.

**Rescaled 2026-09-16.** The hub is 10× its original size; see `STATUS.md`. The
old 436-instance count predates that and needs re-measuring on the next Studio
boot — it prints on startup.

Scale is set in two places and they must move together: `GameConfig.HubLayout`
(dimensions) and `GameConfig.Scale.WalkSpeed` (traversal). Changing one without
the other breaks the 20-second budget, and a test will say so.

### The PortalRig

One shared component, instanced per use and reskinned by rarity colour only —
never duplicated per biome. Fate Engine at 1.5×, Expedition Gate at 2×, and
every future world portal from the same rig.

Carries the **2.5-second spin-up**, which Blueprint §1.3 calls the single most
important UX beat. The reveal banner can never appear before it completes;
enforced by test.

---

## What to describe

Plain prose is fine — no numbers or hex codes needed.

### 1. Hub lighting ⭐ (cheapest, highest impact right now)

Currently a deep dusk: `ClockTime 22`, ambient `rgb(40,35,60)`, fog 150→500.
It reads as atmospheric but is genuinely hard to see.

- Should it be **readable** (raise ambient) or stay **moody** (add local lights instead)?
- Is the mood *sacred*, *abandoned*, *humming with machinery*?
- Is the Crossroads **old** — ruins someone else built — or **actively running**?

### 2. The reveal moment ⭐⭐ (the whole game, per §25)

Now: screen dims to 60%, world names flash past, scramble into symbols as they
accelerate, then a card fades in with rarity, world name and flavour. Total wait
is `RollBuildupSeconds` + the rarity's own reveal duration — 3.7 s for a Common,
6.7 s for a Mythic.

- Build-up **tense** (slow, quiet, dread) or **exciting** (fast, building)?
- When should the player *suspect* it's rare — early (colour shifts) or only at the last frame?
- On a Mythic: does the world stop? Screen shake? Sound cut out?
- Is the result a **prize** (celebratory) or a **destination** (ominous)?

### 3. The Fate Engine

Currently the PortalRig at 1.5× — segmented gold outer ring, neon inner ring,
ForceField plane, 8 rune plates, floating crystal shards.

- **Machine** (gears, pistons) or **artifact** (stone, runes) or both?
- What does it do **at rest**? What happens **when you roll**?
- How does a Common roll differ visually from a Mythic?

### 4. Placeholder text

Flavour lines, result-card copy, zone labels. All in data — world `Flavor`
fields and `FateRoll.luau` strings.

### 5. Biomes (Phase 2)

Verdant Valley, Emberfall and Astral Reach have blueprint palettes and wired
lighting already. Their *geometry* is Phase 2.

**Sky Citadel has no blueprint at all** — the Biome Blueprint never drafted it
(§7.4 lists it as a reserved slot). Its lighting values are invented. It needs a
real section before Phase 2 makes worlds enterable.

---

## The house style — low poly, one palette

**Owner-directed, 2026-09-17.** Every authored asset in the hub is **low poly
and flat shaded**, and every asset draws from the one palette below. The hub has
to read as a single place built by a single hand, not a gallery of pieces that
happen to stand near each other.

This is a *style*, not a budget. A mesh can be cheap and still be wrong here:

| | Low poly | Merely optimised |
|---|---|---|
| Shading | **flat** — every facet visibly its own plane | smooth, normals interpolated |
| Curves | resolved into a countable number of flat faces | approximated finely enough to look round |
| Surface | one flat colour per material | textures, veining, roughness variation |
| A cylinder | 12–16 sides you can count | 64 sides you cannot |

**Flat shading is not optional.** A low-poly mesh with smooth shading does not
read as stylised — it reads as a high-poly mesh that went wrong. Shade Flat in
Blender, and let the facets catch the light.

**No textures anywhere in the hub.** No image maps, no roughness, normal or
metallic maps, no `SurfaceAppearance`. Colour comes from flat material colour
only. This is partly style and partly mechanics: a `SurfaceAppearance`
**overrides a part's `Color`**, and rarity reskinning works by setting `Color`.
A textured portal ring is a dead portal ring.

Ethereal Scape v2 is already built this way, so the hub matching it is what
makes the game look like one game.

### No built-in Roblox materials

**Owner-directed, 2026-09-18.** Every surface in the hub is `SmoothPlastic`.
Not `Marble`, not `Slate`, not `Basalt`, not `Metal`, not `Glass`.

Roblox's material textures are photographic grain, and grain fights flat-shaded
low-poly geometry — it adds surface noise to a style whose whole premise is that
facets and colour carry the read. The palette is meant to do the work on its
own.

It is also cheaper. `Glass` in particular is expensive on the phones the §6
checklist budgets for, and six floating crystals were using it.

**The exceptions are light, not surface:** `Neon` for emissive parts and
`ForceField` where a shimmer is wanted. Those are shaders, not textures.

Enforced by test for the Fate Engine's paint table.

> **If a future model is authored expecting real materials**, this is the
> decision to revisit — the point is consistency across the hub, not a hatred
> of `Marble`. Revisit it deliberately and change it here, rather than letting
> one asset drift.

### Colour is applied in code, not baked in

Authored meshes arrive **grey** — Roblox imports untextured geometry with no
colour, and untextured is exactly what this style asks for. That is not a
failure to fix in Blender; it is the pipeline working.

Colour is two per-part Roblox properties, `Color` and `Material`, neither of
which needs UVs. They are set from a **paint table in content**, keyed by part
name with longest-prefix matching (see `Crossroads.FateEngine.PrefabStyles`
for the Engine and `Crossroads.Shell.Styles` for the hub itself, 184 keys
across 225 parts). So recolouring an authored piece is a data edit and a
rejoin — never a re-export.

**Longest prefix wins, and the trailing underscore is the tool for it.**
`Plinth_SideBand` can be gold while `Plinth` stays marble, because the longer
key matches first. The same trick is what keeps a district's dressing separate
from its platform: `District_Shop` is the deck, and `District_Shop_` is the
catch-all for everything mounted on it. Without that second key a part the
table forgot would silently inherit the deck's entry — including its
collision.

### Collision is part of the paint table, and it is the dangerous part

An imported `MeshPart` arrives with **no baked `PhysicsData`**, so Roblox
generates its collision hull on load at `Default` fidelity. `Default` is
coarse, and coarse means **it fills small openings**.

That matters because a Blender export routinely merges many separate objects
into one mesh — a colonnade of eight columns, four archways, a pair of
flanking statues, a parapet that rings a plaza. Each of those is one
`MeshPart`, and a filled hull across it is an invisible wall exactly where
players walk.

So the rule is:

> **Collision and fidelity are decided together, never separately.** A single
> solid volume — a floor, a deck, a stair flight, a pillar, a rock — collides
> at `Default`, which is cheap and exactly right. A mesh with openings that
> matter — an arch, a colonnade, a balustrade, a ring wall — collides at
> `PreciseConvexDecomposition` or not at all. **`CanCollide` on its own, on a
> mesh with a hole in it, walls off a route.**

`PreciseConvexDecomposition` is a real runtime cost, computed at load and
cached per mesh asset, so it is spent deliberately rather than granted by
default. In the Crossroads it is on 30 parts of 225.

This is also why `CanCollide` defaults to **off** in `PrefabLoader` and
content turns it on: the failure mode of forgetting is a part you can walk
through, not a world you cannot walk in.

**Both halves of that rule cost a playtest to learn.** The first authored hub
shipped with collision on only the unambiguous solids and everything else
pass-through — safe against invisible walls, and it produced the opposite
complaint: players sank into the flanks of district platforms and walked
through railings. Neither half is optional.

Roblox's built-in materials give stone grain, glass and neon bloom for free.
Use them instead of authoring a surface.

### The hub palette — the thematic cycle

Straight from `Content/Hub/Crossroads.luau`, which is the source of truth. An
authored piece uses these and nothing else.

| Role | RGB | Reads as |
|---|---|---|
| Marble | `226, 221, 234` | pale lilac-white — the dais, the plinth, every floor |
| Marble trim / gold | `230, 178, 74` | the one warm accent; use sparingly or it stops being an accent |
| Plaza stone | `58, 52, 76` | deep dusk purple — the ground plane |
| Walkway stone | `78, 70, 98` | one step lighter than the plaza |
| Dark stone | `64, 58, 78` | the outer portal ring, heavy structural pieces |
| Rune slate | `88, 82, 104` | grey-violet, for carved detail |
| Mint neon | `124, 245, 224` | the rune inlays and `UNKNOWN` glow |
| Dimmed inlay | `68, 135, 123` | mint neon, knocked back for emissive surfaces — see below |
| Deep teal | `27, 75, 74` | the Discovery Archive's own hue, the only district with one |
| Sand | `107, 104, 98` | the Training yard floor |
| Marble in shadow | `196, 190, 208` | balustrades and railings against a pale deck |
| Torch light | `255, 176, 92` | warm flame |
| Engine spot | `255, 200, 120` | the key light over the Fate Engine |

**Dark values do not survive this lighting at scale.** The first authored walk
reported gateway arches, banners, training dummies, braziers and weapon racks
as *"uncolored"* — they were painted, in `Basalt` and `Slate`, and at
`ClockTime 4.5` those simply read as black against a night sky. The palette
did not change; those pieces moved one step up it, to `Slate` and
`MarbleDim`. **When something reads as unpainted here, suspect the value
before the paint table.**

All of these are named fields on `Crossroads.Theme` — `Marble`, `MarbleTrim`,
`Plaza`, `Walkway`, `Basalt`, `Slate`, `Inlay`, `Cosmic`, `DeepTeal`, `Sand`,
`MarbleDim`. They were literals scattered through the Engine's paint table
until the hub needed them a hundred more times; **use the name, never the
triple**, so a palette change is one edit.

**Why there are two mint greens.** `Neon` emits at full `Color` and bloom
amplifies it, so the palette's `124, 245, 224` bleeds a halo across everything
near it at any real size. Emissive surfaces get the knocked-back
`68, 135, 123`; the bright value is kept for small accents — a shrine crystal,
an oculus — where the bloom is the point.

Ambient is `72, 66, 96` under a `90, 70, 140` sky at `ClockTime 4.5` — a low,
raking pre-dawn light. **Author for that.** A piece that looks right under
Blender's default studio lighting will read washed-out and flat in the hub;
check it under a single low warm key with cool purple fill.

Anything that gets **recoloured by rarity** — portal rings, portal planes,
glyphs, the Engine's crystal shards — is exported **pure white and emissive**,
with no colour of its own. The game tints those at runtime, and a colour baked
in fights it.

---

## Current defaults

| Thing | Value |
|---|---|
| Ambient / Outdoor | `rgb(72,66,96)` / `rgb(96,88,128)` |
| ColorShift_Top | `rgb(90,70,140)` |
| Fog | `rgb(30,25,50)`, 700 → 4400 |
| Brightness / ClockTime | 2.6 / 4.5 (brightness pass, 2026-09-16) |
| Marble / Gold accent | `rgb(226,221,234)` / `rgb(230,178,74)` |
| Hub diameter (playable) | 1150 studs |
| Visual extent (scenery) | 4000 studs |
| Zone ring radius | 400 studs |
| Zone platforms | 210–320 studs (four districts; the Observatory was cut) |
| WalkSpeed | 32 (Roblox default is 16) |
| Walkways | 44 studs wide, raised 6 (gate processional 72) |
| Portal spin-up | 2.5 s |
| Reveal total | Common 3.7 s → Mythic 6.7 s |

### Rarity colours — do not deviate

Biome Blueprint §1.1, single source of truth. **Rarity colour is a UI and portal
contract; biome palette is set dressing.** Emberfall's environment is fire-orange
but its portal ring is Rare blue. Enforced by test.

| Rarity | Hex | |
|---|---|---|
| Common | `#9E9E9E` | Verdant Valley |
| Uncommon | `#5FD97A` | ⚠️ not in the blueprint — needs sign-off |
| Rare | `#3E8EF7` | Emberfall |
| Epic | `#B24BF3` | Sky Citadel |
| Legendary | `#FFD447` | Hall of Legends |
| Mythic | `#FF7A1A` | Astral Reach |
| Unknown | `#7CF5E0` | Fatebreaks |

---

## How a description becomes code

Your prose becomes edits to `Crossroads.Theme`, the zone tables, `UITheme`, or
tween curves in `FateRoll.luau`. Then `rojo serve`, look at it, say what's wrong.
Most changes are numbers, so the loop is fast.

With the **Studio MCP** connected locally (see `TOOLCHAIN_ACCESS.md`), an agent
can also screenshot the result and iterate without you describing every tweak.
