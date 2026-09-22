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
2. **Palette and light** — the colours and lighting values, and where they live
   in content.
3. **The kinds of place** — the list of piece types the world is made of, and
   what each is for. This is the part that decides variety.
4. **How pieces connect** — the world's connection types, which pieces offer
   which, and what that makes happen. Decided **before** modelling.
5. **Inhabitants** — enemies per piece type, the boss, and where each appears.
6. **Piece size and count** — how big a piece is in this world, and how many
   the kit wants.

None of that is construction detail. It is the design the construction serves.

---

## Status

| World | Schema | Kit |
|---|---|---|
| **Verdant Valley** | ✅ `VERDANT_VALLEY.md` | 12 test pieces delivered 2026-09-22 |
| **Sky Citadel** | 🔴 `SKY_CITADEL.md` — stub, needs filling | none |
| **Emberfall** | ⏳ Biome Blueprint §3.3, not yet extracted here | none |
| **Astral Reach** | ⏳ Biome Blueprint §3.5, not yet extracted here | none |
| **Ethereal Scape** | n/a — ships as a `PrebuiltMap`, not a kit | one authored scene |

Emberfall and Astral Reach have Biome Blueprint sections already and need
extracting into this shape. **Sky Citadel has no blueprint section at all** —
it was added after the blueprint merge so the onboarding arc could peak on an
Epic, and its lighting values are invented rather than designed. It is the
largest content debt in the project.
