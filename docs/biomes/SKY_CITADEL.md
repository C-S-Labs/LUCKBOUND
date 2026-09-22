# Sky Citadel — biome design schema

> **🔴 STUB. This world has no design behind it.** Everything below marked
> *invented* was chosen to make the data valid, not because anyone designed it.
> **Fill this in before modelling anything**, because §2 and §3 decide what the
> pieces are and how they connect, and discovering them after the geometry
> exists means re-cutting every piece.

**Rarity:** Epic · **Roll weight:** 400 canonical / 700 in the Phase 1 pool (7%)
**Map route:** chunk kit (none built) · **Blueprint:** none — §7.4 reserves the
slot and drafts nothing

Sky Citadel was added *after* the Biome Blueprint merge, so the onboarding arc
could peak on an Epic at roll 8 rather than handing every new player a
guaranteed Mythic. It has been live in the roll pool since, at 7%, with no map —
a player who rolls it is told the world has no map yet. **It is the largest
content debt in the project.**

---

## 1. Palette and light — *invented, and the only part with any substance*

In `Content/Worlds/SkyCitadel.luau`. Deliberately the brightest world in the
prototype: you are above the weather, in open sun. Reads as relief against
Emberfall's ash and Astral Reach's void.

| | |
|---|---|
| Ambient | `140, 160, 200` |
| Outdoor ambient | `170, 185, 215` |
| Sky shift | `255, 235, 190` — warm early light |
| Fog | `225, 235, 250`, 150 → 700 |
| Brightness / clock | 3 · 07:00 |

Long fog and a 7 a.m. clock is the one real design decision here: it is a place
you look *out* from.

---

## 2. The kinds of place — **empty**

What is a Sky Citadel piece? Nothing has decided. Questions worth answering
before anything is built:

- **Is it one structure or an archipelago?** A citadel implies built stone,
  halls and courtyards. Ethereal Scape already owns "islands joined by bridges",
  and it ships as a prebuilt map precisely because that shape resisted being
  modular. Repeating it here would repeat that problem.
- **Does it have ground?** If pieces are platforms in open sky, falling off is a
  mechanic, and nothing in the game handles that today.
- **What does a connective piece look like** when the world is architecture
  rather than landscape? A corridor, a colonnade, a rampart, a stair?
- **What is the equivalent of a meadow** — the piece that exists to be fought
  in?

Target 12–16 kinds of place, as everywhere.

---

## 3. How pieces connect — **empty**

Needs its own connection types. **Do not reuse Verdant Valley's `PATH`/`WIDE`** —
the vocabularies are deliberately per-world and a test asserts they do not
overlap. Architecture suggests different ones: a `GATE` between courtyards, a
`SPAN` for something crossed, a `HALL` the arena accepts.

Whichever type the boss arena accepts becomes reserved, so the pieces offering
it become the approach to the boss. **That is the lever for pacing** — pick it
deliberately.

---

## 4. Inhabitants — **empty**

`Enemies = {}`, `BossId = nil`, `LootTableId = nil`, `DiscoveryTableId = nil`.
An Epic world needs an Epic boss, and it has none.

---

## 5. Piece size and count — **undecided**

Verdant Valley uses 256 × 256. A world of halls and courtyards may want a
different number, and is allowed one — piece size is per-world. Interiors read
larger than open ground at the same footprint, so 256 may be generous here.

---

## 6. What has to happen, in order

1. **Fill in §2 and §3.** Design, not modelling. Cheapest step and it gates
   everything else.
2. **§4** — enemies and a boss, so the world has stakes.
3. **Decide §5** against a 5-stud character.
4. Then build, to `../CHUNK_AUTHORING.md`.
