# Astral Reach — locked design scheme

The Mythic world, and the hardest sky and door in the game. This document **locks in the owner's drafted scheme**
for Astral Reach and its two legendary bosses, **The Astral Seraph** and **The Celestial Dancer**.

> **DESIGN ONLY — NOTHING HERE IS BUILT.** Owner-directed 2026-09-29: record the design, do not construct it.
> No kit, content file, generator, rig or boss exists yet. Building comes in a later, separate task, and must start
> from this document rather than re-deriving the look.

**Source of truth:** the owner's concept sheet, committed as
[`docs/design/ASTRAL_REACH_SCHEME.webp`](../design/ASTRAL_REACH_SCHEME.webp) (one image: the world, both bosses,
their movesets, close-ups and environmental interaction). Where this text and the sheet ever disagree, **the sheet
wins**; fix the text. The sheet's own wording is reproduced faithfully below; the "Build notes" sections are
interpretation added to make it buildable and are labelled as such.

| | |
|---|---|
| World id | `ASTRAL_REACH` (rarity Mythic, weight 300 = 3%: build spec §7, `MASTER_DESIGN.md`) |
| Status | design locked 2026-09-29, **not built** |
| Ambient hour | midnight (`0`), already reserved in the world-hour uniqueness test (`biomes/README.md`) |
| Event tie-in | *Astral Alignment* (`EVENTS.md`), Tier IV |
| Bosses | The Astral Seraph (Legendary), The Celestial Dancer (Mythic) |
| Contract when built | [`CHUNK_AUTHORING.md`](../CHUNK_AUTHORING.md), [`MODULAR_MAPS.md`](../MODULAR_MAPS.md), [`ENEMY_FRAMEWORK.md`](../ENEMY_FRAMEWORK.md), [`ENEMY_AI.md`](../ENEMY_AI.md) |

---

## 1. The world

**Tagline:** *A realm between worlds.*

> A shattered cathedral adrift in the void, where the stars themselves are the only sky. The Astral Reach exists
> outside time, its floating islands and broken spires a relic of a forgotten celestial age.

### World overview (from the sheet)

Astral Reach is a **floating cathedral realm, suspended in the void**. Fragments of ancient architecture drift
between islands, connected by **shattered bridges and luminous pathways**. The sky is a sea of stars, with distant
galaxies visible on the horizon.

### Key features

- Floating islands and cathedral spires
- Shattered bridges and pathways
- **Star-filled skybox (no clouds)**
- Deep, moody lighting
- Minimal, deliberate environment
- Celestial energy effects

### Mood and atmosphere

Serene · Mysterious · Isolated · Grand

### Locations on the sheet

| Location | Role (as captioned) |
|---|---|
| **Main Cathedral** | Central hub of the realm. The grandest structure. |
| **Sky Islands** | Floating landmasses and ruins. |
| **Bridges & Pathways** | Connect islands and lead to the cathedral. |

### Environmental details (from the sheet)

| Detail | Caption |
|---|---|
| **Starry Skybox** | Distant galaxies and nebulae. |
| **Celestial Architecture** | Ancient, otherworldly, and massive. |
| **Edge Platforms** | Often used for traversal and event spawns. |

### Environmental interaction (from the sheet)

| Effect | Caption |
|---|---|
| **Reactive Floor** | Subtle star-trail patterns from movement. |
| **Floating Platforms** | Used for traversal and phase transitions. |
| **Celestial Particles** | Ambient energy and atmospheric effects. |

### Look, as painted

- **Palette:** near-black midnight navy to deep indigo and violet; light comes only from **electric blue-white
  glow** (rune circles, window tracery, seams, a vertical beam of light rising from the cathedral). Accents on the
  bosses are pale silver-lavender with thin gold filigree. No warm daylight and no clouds anywhere.
- **Silhouette:** a huge dark Gothic cathedral (tall lancet windows, buttresses, needle spires) on a central mass,
  ringed by smaller floating islands with their own spires, all against a starfield with galactic bands.
- **Ground:** dark stone platforms with glowing blue rune rings and inlaid light-lines; edges fall away into void.
- **Scale:** grand and empty. "Minimal, deliberate environment": few large pieces, lots of open dark, not clutter.

### Build notes (interpretation, not on the sheet)

- Sits beside Sky Citadel as its opposite: Sky Citadel is a white castle in morning sun above clouds; Astral Reach
  is a black cathedral at midnight above nothing. Keep them apart in palette and light (`ART_DIRECTION.md`).
- Likely piece families when the kit is authored: cathedral core/nave, island slabs, spires, bridge spans (whole
  and shattered), edge platforms (traversal and event spawn), rune-ring floors, backdrop islands. Final list is a
  kit-authoring decision, not locked here.
- "No clouds" is a hard rule: the ambience layer (`GameConfig.Ambience`) must run stars/galaxy/particles only.
- The reactive floor (star trails from movement) and the phase-transition floating platforms are gameplay-facing:
  when built they need a client effect and, for platforms, a server-authoritative rule (rule 5, AGENTS.md).

---

## 2. Boss: The Astral Seraph

**Being beyond the heavens.** *Legendary.*

> The Astral Seraph is a celestial guardian forged from the remnants of a fallen realm. Its wings are not just for
> flight — they are weapons, shields, and extensions of its will.

| | |
|---|---|
| Tier | Legendary |
| Triangle count | ~120k (target) |
| Primary focus | AoE / Mid-Range |
| Weapon | Celestial Wings + Halo Blades |

### Key features

- **6 wing segments**, each with independent motion
- **Floating halo ring** (attack + shield)
- **Phased movement** (ground / aerial)
- **Light-based attacks + AoE control**

### Moveset and attacks

| # | Attack | Description (from the sheet) |
|---|---|---|
| 1 | **Wing Slash** | Sweeps with wing blades in a wide arc. |
| 2 | **Halo Blast** | Fires a ring of energy outward. |
| 3 | **Divine Lance** | Charges and thrusts a focused beam. |
| 4 | **Aerial Dive** | Soars into the air, then dives at the player with massive force. |
| 5 | **Wing Barrage** | Spawns multiple wing blades that circulate and strike. |
| 6 | **Phase Shift** | Briefly becomes untargetable, reappearing with a burst of light. |

### Additional detail close-ups

| Close-up | Caption |
|---|---|
| Wing Segment | Each segment moves independently and reacts to combat. |
| Halo Ring | Rotates and charges during special attacks. |
| Head / Face | Masked, with subtle celestial glow. |
| Back View | Shows wing structure and energy core. |

### Look, as painted

Tall, symmetrical, humanoid-angelic figure: a slender armoured white-silver body with gold filigree, a masked
faceless head, a glowing blue energy core in the chest, a thin floating halo ring behind the head, and **six large
feathered blade-wings** fanning from the back (three per side, long tapering feather-blades edged in blue light).

### Build notes (interpretation, not on the sheet)

- Six independently animated wing segments means six wing joints on the rig (or more for feather clusters), so it
  needs the extra-joint route in `ENEMY_FRAMEWORK.md`; the halo is its own joint/part.
- Phased ground/aerial movement and an untargetable Phase Shift are boss-evolution phases in `ENEMY_AI.md`
  territory. Untargetable must be a server flag, never client-decided.
- ~120k triangles is a **target** and is far above anything shipped so far; check it against the enemy triangle
  budget in `ENEMY_FRAMEWORK.md` before modelling, and raise the budget or LOD plan first if it does not fit.
- Six attacks, all authored as data (Content), none as System code (prime directive).

---

## 3. Boss: The Celestial Dancer

**Grace in motion.** *Mythic.*

> The Celestial Dancer is a master of balance — between motion and stillness, life and death. She dances across the
> void, her blades painting patterns of fate. Those who witness her are said to be chosen… or cursed.

| | |
|---|---|
| Tier | Mythic |
| Triangle count | ~140k (target) |
| Primary focus | Mobility / Melee |
| Weapons | Twin Blades + Floating Blades |

### Key features

- **Flowing cape** (skinned mesh)
- **Dynamic hair and cloth simulation**
- **Multi-phase fight**
- **Telegraphed and aerial combat**
- **Precision and grace-based attacks**

### Moveset and attacks

| # | Attack | Description (from the sheet) |
|---|---|---|
| 1 | **Opening Dance** | Calm, non-aggro state. Builds energy and movement. |
| 2 | **Twin Slash** | Quick, precise strikes. |
| 3 | **Spinning Blossom** | Wide arc with floating blades. |
| 4 | **Lunar Dash** | Blinks between positions. |
| 5 | **Phase Step** | Short-range teleport with afterimage. |
| 6 | **Celestial Rain** | Summons a field of blades from above. |
| 7 | **Aerial Rotation** | Spins mid-air with blade storm. |
| 8 | **Ending Blade** | Final strike with all remaining blades. |

### Additional detail close-ups

| Close-up | Caption |
|---|---|
| Cape | Layered, reactive cloth with anime-like flow. |
| Hair | Dynamic strands with physics. |
| Blade | Floral / celestial design with energy core. |
| Back View | Shows floating blades and cape structure. |

### Look, as painted

A tall, slender female-presenting figure with a pale silver-white face-covering helm, long trailing translucent
lavender-white cape and skirts with gold trim and blue-violet energy wisps, a dark fitted bodice, and long
flowing hair or veil. Twin slender blades in hand; additional blades float around her. She reads as **elegant and
fluid**, the opposite silhouette to the Seraph's rigid symmetrical wings.

### Build notes (interpretation, not on the sheet)

- **Opening Dance is a non-aggro state**, so this fight begins peaceful: an encounter-state machine
  (idle/dance, then aggro), not an attack that damages.
- **Ending Blade uses "all remaining blades"**: the floating blades are a counted resource that other attacks
  spend and the finisher consumes. The count is server state and belongs in boss content/config, not hard-coded.
- Cape, hair and cloth are the hard technical asks (skinned cape, physics strands). Roblox has no native cloth
  sim, so expect bone-chain secondary motion in the rig and a fallback; decide at build time, note in
  `ENEMY_FRAMEWORK.md`.
- ~140k triangles is a **target**, same budget caveat as the Seraph.
- Eight attacks in "Multi-phase fight"; the sheet lists the moves in order and does not assign them to phases.
  **Phase assignment is an open design question** (see below), not something to guess at build time.

---

## 4. The pair

- Both are **legendary bosses of one world**: Astral Reach is the only place either appears. The sheet labels the
  Seraph *Legendary* and the Dancer *Mythic*.
- They are deliberately opposed. Seraph: symmetrical, rigid, radiant, **AoE and mid-range**, wings as weapons and
  shields. Dancer: asymmetrical, fluid, **mobile and melee**, blades as choreography.
- The sheet closes on a quote for the Dancer: *"The stars are not above you. They are within the realm."*
  (The Celestial Dancer). Treat it as world/boss flavour text.

## 5. Open questions (to settle before building, not decided here)

1. **How do the two bosses relate in the encounter?** Separate expedition endings, a random one per run, two
   stages of one run, or a co-fight? The sheet does not say.
2. **Which attacks belong to which phase** for each boss, and how many phases each has.
3. **Triangle budgets:** ~120k and ~140k versus the current enemy budget.
4. **Drops and Fate integration:** loot tables, first-clear rewards and anything tied to Mythic rarity are not on
   the sheet.
5. **Tier of the encounter** relative to the *Astral Alignment* event (Tier IV) is only implied.
6. **Cloth/hair approach** on Roblox (bone chains vs baked animation).

None of these is a reason to change the sheet; they are gaps to fill in a follow-up design pass.

---

## 6. When it is built

Follow the normal order, not a shortcut: this schema, then the world kit (`CHUNK_AUTHORING.md`), then boss rigs and
data per `ENEMY_FRAMEWORK.md`, then behaviour per `ENEMY_AI.md`'s mandatory build order. Add the world's content as
one file under `src/shared/Content/` (prime directive); if that seems to need a System change, the schema is wrong;
raise an amendment. Update `biomes/README.md`, `STATUS.md` and `docs/RESERVED.md` in that change.
