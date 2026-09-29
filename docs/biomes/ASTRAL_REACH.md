# Astral Reach — locked design scheme

The Mythic world, and the hardest sky and door in the game. This document **locks in the owner's drafted scheme**
for Astral Reach and its two legendary bosses, **The Astral Seraph** and **The Celestial Dancer**.

> **DESIGN ONLY — NOTHING HERE IS BUILT.** Owner-directed 2026-09-29: record the design, do not construct it.
> No kit, content file, generator, rig or boss exists yet. Building comes in a later, separate task, and must start
> from this document rather than re-deriving the look.

**Source of truth:** the owner's concept sheet, committed as
[`docs/design/ASTRAL_REACH_SCHEME.webp`](../design/ASTRAL_REACH_SCHEME.webp) (one image: the world, both bosses,
their movesets, close-ups and environmental interaction). Where this text and the sheet ever disagree, **the sheet
wins**, except that the owner's later written plan (§4, added 2026-09-29) **overrides the sheet's triangle targets and
the boss-tier wording**; fix the text. The sheet's own wording is reproduced faithfully below; the "Build notes" sections are
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
| Tier | Legendary (a few levels under the Dancer in difficulty) |
| Triangle count | ~120k on the sheet; **owner budget 175–200k** (§4.6) |
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
- The triangle budget is now 175–200k (§4.6): far above anything shipped so far, so raise the enemy budget in
  `ENEMY_FRAMEWORK.md` for these two bosses before modelling.
- Six attacks, all authored as data (Content), none as System code (prime directive).

---

## 3. Boss: The Celestial Dancer

**Grace in motion.** *Mythic.*

> The Celestial Dancer is a master of balance — between motion and stillness, life and death. She dances across the
> void, her blades painting patterns of fate. Those who witness her are said to be chosen… or cursed.

| | |
|---|---|
| Tier | Mythic: the game's first Mythic and its hardest boss at release |
| Triangle count | ~140k on the sheet; **owner budget 200–250k** (§4.6) |
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
- Budget is now 200–250k (§4.6); same `ENEMY_FRAMEWORK.md` caveat as the Seraph.
- Eight attacks in "Multi-phase fight"; the sheet lists the moves in order and does not assign them to phases.
  **Phase assignment is an open design question** (see below), not something to guess at build time.

---

## 4. Structure of a run (owner plan, 2026-09-29)

*Owner-directed intent, written after the sheet. Design, not built. The owner marked some parts "subject to
change / needs brainstorming"; those are flagged.*

**Intent:** the first Legendary-and-up biome, so **it must be grand**. The **palace defines Astral Reach**: the
outside is the approach, the inside is the showcase.

### 4.1 Exterior: small kit, random path to the palace

- A **small exterior chunk kit, about 4–6 pieces**.
- **One spawn platform, static every run.**
- Every other exterior chunk is used to **randomly generate the path to the main Palace** shown in the sheet.
- Outer platforms can carry a **small miniboss encounter, a loot area, or simply be pathway**.
- **The shortest path from spawn to the palace is only about 3–4 chunks long**, so the player never travels endlessly
  in a line to reach the main build. (Longer routes via side platforms are fine; the *shortest* one is capped.)
- Build note: fits the universal generation blueprint (`MODULAR_MAPS.md`, build spec §7.7). The 3–4 cap is a
  tunable in `GameConfig`; confirm the blueprint can express a fixed spawn, a fixed palace target and a
  shortest-path cap.

### 4.2 Palace exterior: one giant set piece

- **Exempt from chunk size rules.** A single giant landmark, **looking almost identical to the reference picture**
  (black Gothic cathedral, lancet windows, spires, vertical beam of light): **otherworldly and grand**.
- **Budget up to ~200k triangles for the exterior alone.**
- **Performance plan:** entering the palace **teleports the player far away** to where the interior is generated.
  The exterior is then **unrendered, or simply despawned**, while the player is inside (choice deferred; either
  meets the intent).
- Build note: a scenario-layer / expedition-entry concern (build spec §7.1, §7.3). Teleport-in and despawn are new
  behaviour and need a written amendment; no special-casing in a System.

### 4.3 Palace interior: all-interior, generated on entry, massive

- **All interior chunk generation happens once the player enters**, at the far-away location.
- **Massive and impossible: both too big and too small for the exterior.** Impossible size ratios are a headline
  feature.
- Showcase qualities: **randomness, uncanniness, otherworldliness, impossible size ratios**, all leading to the
  **grand palace boss room where the main spectacle begins**.
- **Interior size: 20–36 chunks per run.** They must be **random, unique** (varied, not repeats of one look) and
  **capture the true feeling of the biome plans**: grand, otherworldly, uncanny, impossible.
- Build note: 20–36 is a `GameConfig` range, rolled by the generator's own `Random`. "Unique" implies an interior
  kit large enough to fill 36 chunks without visible repetition, so kit size is a sizing decision for authoring
  time; whether the two fixed boss platforms count toward the 20–36 is undecided.
- **Layout rule: almost all pathways lead to the boss room**, not one branch among many. Exceptions: **a few small
  treasure rooms, minibosses and the like**.
- Build note: an inverted dungeon graph (few dead ends, many routes to one goal). Confirm the interior blueprint
  supports many-to-one convergence with a small number of flagged side rooms.

### 4.4 Two fixed boss platforms

The interior has **2 set (non-random) chunks**: **two large boss platforms**, one per boss.

| Platform | Boss | Tier / difficulty |
|---|---|---|
| **Dancer platform** | The Celestial Dancer | Mythic. First Mythic in the game and **the hardest boss at release**. |
| **Seraph platform** | The Astral Seraph | Legendary. **A few levels under the Dancer's difficulty.** |

### 4.5 Which boss spawns

- A run spawns **one** boss: **75% Astral Seraph, 25% Celestial Dancer.**
- **Provisional, subject to change.** Rates belong in `GameConfig`, rolled by a `Random` the system owns
  (AGENTS.md rules 4 and 6).
- This settles how they interact: **weighted alternatives**, not a co-fight and not two stages. Whether the unused
  boss's platform is still generated is a build decision.

### 4.6 Budgets

| Item | Budget |
|---|---|
| Palace exterior | up to ~200k triangles |
| **The Astral Seraph** | **175–200k triangles** |
| **The Celestial Dancer** | **200–250k triangles** |
| Boss rooms | deliberately **shaved down**: **vast, open, yet detailed** to convey the bosses' grandness |

- Owner's reasoning: open rooms mean **performance is not a concern** despite the heavy boss meshes.
- Supersedes the sheet's ~120k / ~140k.
- Build note: far above current enemy mesh limits. The exterior is despawned while inside, so budgets are per-scene,
  not summed. Confirm Roblox mesh/import limits and streaming for meshes this heavy (split into MeshParts) before
  modelling.

### 4.7 Boss room moving parts (brainstorm, not locked)

- The boss room has **multiple parts that move in stages**, for **phase transitions and other purposes**.
- **How it works is undecided and needs brainstorming.** Directions to explore, none chosen:
  - platforms that rise, drift apart or re-assemble between phases (echoing the sheet's "Floating Platforms: used
    for traversal and phase transitions");
  - architecture (spires, arches, rings) that reconfigures around each boss;
  - Seraph: parts tied to its ground/aerial phasing and wing/halo attacks; Dancer: parts that follow her
    choreography, the calm Opening Dance and the blade-field attacks.
- **Fixed constraint:** it must **keep the otherworldly, random feel**. Movement that affects footing or damage is
  server-authoritative (AGENTS.md rule 5).

### 4.8 Enemies

- **Minibosses and normal enemies for this biome are not yet drafted.** Slots exist for them (§4.1, §4.3); design
  later under `ENEMY_FRAMEWORK.md`.

---

## 5. The pair

- Both are **legendary bosses of one world**: Astral Reach is the only place either appears. The sheet labels the
  Seraph *Legendary* and the Dancer *Mythic*.
- They are deliberately opposed. Seraph: symmetrical, rigid, radiant, **AoE and mid-range**, wings as weapons and
  shields. Dancer: asymmetrical, fluid, **mobile and melee**, blades as choreography.
- The sheet closes on a quote for the Dancer: *"The stars are not above you. They are within the realm."*
  (The Celestial Dancer). Treat it as world/boss flavour text.

## 6. Open questions (to settle before building, not decided here)

1. ~~How do the two bosses relate?~~ **Settled 2026-09-29:** one per run, 75% Seraph / 25% Dancer (provisional, §4.5).
2. **Which attacks belong to which phase** for each boss, and how many phases each has.
3. **How the boss room's staged moving parts work** (§4.7), for both bosses.
4. **Mesh and import limits** for 175–250k-triangle bosses and a ~200k exterior (§4.6).
5. **Minibosses and normal enemies** for the biome (§4.8), and what the exterior and interior side rooms hold.
6. **Drops and Fate integration:** loot tables, first-clear rewards and anything tied to Mythic rarity are not on
   the sheet.
7. **Tier of the encounter** relative to the *Astral Alignment* event (Tier IV) is only implied.
8. **Cloth/hair approach** on Roblox (bone chains vs baked animation).

None of these is a reason to change the sheet; they are gaps to fill in a follow-up design pass.

---

## 7. When it is built

Follow the normal order, not a shortcut: this schema, then the exterior kit (4–6 pieces) and interior kit (`CHUNK_AUTHORING.md`), then boss rigs and
data per `ENEMY_FRAMEWORK.md`, then behaviour per `ENEMY_AI.md`'s mandatory build order. Add the world's content as
one file under `src/shared/Content/` (prime directive); if that seems to need a System change, the schema is wrong;
raise an amendment. Update `biomes/README.md`, `STATUS.md` and `docs/RESERVED.md` in that change.
