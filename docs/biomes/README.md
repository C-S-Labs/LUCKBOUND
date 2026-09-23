# Biome design schemas

**One file per biome.** Each says what that world *is* — how it looks, what
lives in it, what kinds of place it is made of, and how its pieces connect.

This folder exists because the construction rules and the design of a world
were tangled together and the design lost. A single authoring document tried to
be both the engine contract and the description of Verdant Valley, and every
biome-specific number in it — piece size, how many pieces, which pieces —
arrived at the modeller as a universal law. The result was a kit built to the
document rather than to the world.

So the split is:

| Document | Owns | Changes when |
|---|---|---|
| `../CHUNK_AUTHORING.md` | What makes a chunk work in the engine at all: scale, origin, independence, one file per piece | Almost never — it is an engine contract |
| `<WORLD>.md` here | What this world is made of: its piece size, its connection types, the kinds of place in it, how many pieces | Whenever the world's design does |

**If a rule only applies to one world, it belongs here, not there.**

---

## What a biome schema covers

Six sections. A world is ready to be built when all six are filled in.

1. **Identity** — rarity, roll weight, one paragraph on what the place is.
2. **Palette, light and ambience** — the colours, lighting values and the
   world's mood, all as data in its `Environment` (see *Ambience* below).
3. **The kinds of place** — the list of piece types the world is made of, what
   each is for, and **what each can support** (the scenario compatibility that
   decides what can happen there). Together these are what decide variety: the
   pieces × what they can host, not the piece count alone.
4. **How pieces connect** — the world's connection types, which pieces offer
   which, and what that makes happen. Decided **before** modelling.
5. **Inhabitants** — enemies per piece type, the boss, and where each appears.
6. **Piece size and count** — how big a piece is in this world, and how many
   the kit wants.

**And one delivery rule for every biome:** ambient scenery (floating crystals,
books, birds, lanterns, embers — anything that drifts, flies, glows or exists
only for mood) is **never merged into the pieces**. It ships as a separate prop
library plus per-piece placements, so it can animate and scale with graphics.
[`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md) convention 6 has the how.

A world is *varied* when §3 and §4 multiply well. Build spec §7.3 has the
generation pipeline; the short version is that a chunk declares what it can
support and the generator decides per run what actually happens there, so 11
pieces can be 50 distinct rooms.

None of that is construction detail. It is the design the construction serves.

### Ambience — a world's mood is data

Added 2026-09-23. Every block is optional in a world's `Environment`; the
client's `AmbienceController` draws what is declared, `AmbienceCore.validate`
refuses a half-declared block at boot, and `Types.Environment` is the full
schema.

| Block | What it does |
|---|---|
| `ClockTime`, `Brightness`, `Ambient…`, `ColorShiftTop/Bottom`, `ExposureCompensation` | the light itself — sun height, how warm lit faces go, how cool shadows go |
| `Atmosphere` | the sky's gradient and haze. **Owns the haze:** Roblox ignores `FogStart`/`FogEnd` while one exists |
| `Sky` | sun and moon size, star count |
| `Bloom`, `SunRays`, `Grade` | post-effects: glow, god rays, colour grade |
| `CloudSea` | layers of drifting cloud below the map, wrapped round the camera so they never run out. Each cloud is a cluster — a shaded base with lit billows — of one of three kinds (`Mix`: `Cumulus`, `Stratus`, `Wisp`), each turned its own way |
| `Motes` | faint particles on the air around the camera |

**The world owns the scene.** On entry every sky, atmosphere and post-effect
already in `Lighting` is set aside and the world's replace them — in the
finished game the expedition is its own server (build spec §7.2), so there is
nothing to preserve. The set-aside exists only so a Studio `/leave` hands the
hub back intact.

**Pick an hour nobody else has.** Each world holds its own time of day, and a
test refuses two worlds within an hour of each other: Sky Citadel 6.4 (sunrise),
Verdant Valley 13, Ethereal Scape 15, Emberfall 18, Astral Reach 0.

**Quality scales it.** Cloud and mote counts follow the player's graphics
setting (`GameConfig.Ambience`); level 1 still gets a thin sea, never none.

---

## Status

| World | Schema | Kit |
|---|---|---|
| **Verdant Valley** | ✅ `VERDANT_VALLEY.md` | 12 test pieces delivered 2026-09-22 |
| **Sky Citadel** | ✅ `SKY_CITADEL.md` — art direction and kit | 22 pieces, delivered and uploaded 2026-09-23 |
| **Emberfall** | ⏳ Biome Blueprint §3.3, not yet extracted here | none |
| **Astral Reach** | ⏳ Biome Blueprint §3.5, not yet extracted here | none |
| **Ethereal Scape** | n/a — ships as a `PrebuiltMap`, not a kit | one authored scene |

Emberfall and Astral Reach have Biome Blueprint sections already and need
extracting into this shape — they are now the largest content debt, because
**Sky Citadel gained a real design and a kit on 2026-09-22, and the kit — 22
pieces, three of them caps — was delivered and uploaded on 2026-09-23.**

That design lived at `docs/SKY_CITADEL.md` for a day while a stub in this
folder simultaneously declared the world undesigned: two documents for one
world, in two places, disagreeing. Consolidated here 2026-09-23. A world's
schema lives in this folder and nowhere else.
