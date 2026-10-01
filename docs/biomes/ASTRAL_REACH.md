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

Tall, strictly symmetrical, humanoid-angelic figure seen front-on, hovering rather than standing.

- **Body:** slim, smooth, armoured white-silver plating with fine gold filigree and thin blue light-lines; a small
  glowing blue **energy core** at the chest. The lower body tapers into long pointed feather-blades in place of
  legs, so the whole figure is a tall spear-like silhouette.
- **Head:** a smooth, masked, helm-like head with no face and only a faint blue celestial glow.
- **Halo:** a thin gold-and-blue ring behind and above the head, etched with sacred-geometry lines (crossing
  arcs and star points); it reads as both crown and shield.
- **Wings:** the dominant shape. Large **blade-feathers** (pale silver-white, gold-edged, blue-lit at the seams)
  fan out from the back in **two tiers**: an upper sweep rising and outward like a crown, and a lower sweep of
  longer feathers spreading out and down, so the whole figure is a radial burst roughly as wide as it is tall.
  The sheet states **6 independent wing segments**; how the painted feather tiers group into those six is not
  shown and is an authoring decision.
- **Colour and effect:** cold white, silver, gold and electric blue against the dark; light streaks along the
  feather edges. The pose is calm, upright and regal.

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
| Weapons | Twin Blades + Floating Blades on the sheet; **now one long blade + Twin Echo afterimages + floating blades** (§5A.1) |

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

A tall, slender, feminine figure caught mid-stride, three-quarter view, leaning forward with the cape streaming
behind her. Asymmetrical and in motion, the opposite of the Seraph.

- **Head:** a pale silver-white hood or helm that covers the face, with a long, smooth veil-like line down the
  back of the head. No visible face.
- **Body:** a dark, fitted, narrow bodice and legs, with gold trim and gold high-heeled boots; a thin, elegant
  frame.
- **Cape and skirts:** the dominant shape. A huge, layered, translucent **lavender-white cape** sweeps behind and
  to one side in long flowing panels, edged in thin gold lines, shading to blue-violet, with sparkling
  **blue-violet energy particles** trailing through it. It is many layers deep and reads as flowing water or
  smoke rather than fabric.
- **Weapons:** a long, slender blade held low in one hand, trailing a streak of light. The moveset panels show
  twin blades plus floating blades circling her.
- **Colour and effect:** pale lavender, violet and cool white with gold accents, on a dark, faintly reflective
  floor. The pose is graceful and unhurried, menacing through elegance.

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
  **Phase assignment is an open design question** (§5A, §6), not something to guess at build time.

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
- **Interior kit: at most 48 unique chunk pieces.** The interior layout is constructed from this set. Pieces must
  be **random-feeling, unique** (varied, not repeats of one look) and **capture the true feeling of the biome
  plans**: grand, otherworldly, uncanny, impossible.
- **Interior size per run: 12–24 chunks per generation**, drawn from the kit. (This replaces an earlier draft
  figure of 20–36, which the owner clarified was not meant per run.)
- **Flow:** the layout goes **up staircases, down stairs**, and flows with the tower exterior in general, so the
  route climbs and descends through the palace rather than sitting on one level.
- Build note: 12–24 is a `GameConfig` range and 48 a kit cap, rolled by the generator's own `Random`. Kit pieces
  need stair/vertical connectors (up and down) in the chunk contract (`CHUNK_AUTHORING.md`); check the blueprint
  supports vertical connections. Whether the two fixed boss platforms count toward the 48 and the 12–24 is
  undecided.
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

## 5A. Boss design refinement (owner, 2026-09-29)

The owner supplied a detailed refinement, preserved verbatim as
[`docs/design/ASTRAL_REACH_BOSS_REFINEMENT.md`](../design/ASTRAL_REACH_BOSS_REFINEMENT.md). This section records
the locked decisions from it and from the owner's message. **The refinement adds to the sheet; it does not delete
it.** Where a refined move differs from a sheet move (both lists are kept, §2 and §3), reconciling them into one
final moveset is a build-time design task, listed in §6.

### 5A.1 Weapon palettes and phases (locked)

| | Astral Seraph | Celestial Dancer |
|---|---|---|
| Phases | **3** (Phase 1, Phase 2, Final Phase; §5A.5) | **3** (Phase 1, Phase 2, Final Phase; §5A.5) |
| Weapon palette | **The 6 feather wings** are its weapon: it attacks with them at range, and by diving, swooping and slashing, and more. | **The single long blade** as painted, throughout. The "twin" look comes from **Twin Echo afterimages**, not a second held sword. Floating blades join in phase 2. |
| Character | A grand boss | Moveset **choreographed to look like dancing** |

> **Revised 2026-09-29:** an earlier draft had the Dancer's phase 2 turn her weapon into a real two-sword weapon.
> **The owner dropped that** because the afterimage (Twin Echo) can carry the twin idea.

> **FUTURE LEGENDARY WEAPON (marked):** the Dancer's **long blade** is to become an **obtainable Legendary weapon**
> in the future, so it is designed as a real, player-usable weapon (a normal weapon model and moveset should be
> possible), with the Twin Echo afterimage as a possible signature effect. The earlier "twin swords" weapon is
> **no longer planned**. Not built and not yet in `WEAPONS.md` or any content file; when designed, add it there
> (`WEAPONS.md` owns weapon design and rarity rules) and to `RESERVED.md` if declared before use. Whether the
> Seraph's wings also become a weapon is **not stated**, so it is not assumed.

Reconciliation notes:
- The sheet's "Twin Blades + Floating Blades" becomes: one blade, Twin Echo afterimages, and floating blades.
- Floating blades stay on the sheet; the final movesets (§5A.5) place them in phase 2.

### 5A.2 The Astral Seraph, refined

**Identity:** less a creature than a sacred figure given form. It communicates **scale, divinity, symmetry and
unnatural stillness**; the body is the centre of one larger celestial structure (wings, halo, armour and chest
core as one impossible design). It stays upright and symmetrical for much of the fight and **hovers**; the player
should feel it is far too large and composed to be fighting them personally.

**Visual points added by the refinement:**
- Wings must read as a **deliberate, organised structure**, not six identical feather stacks, and must be able to
  **change the silhouette completely** while the body barely moves. Exact grouping stays an authoring decision.
- The **blue chest core** is the strongest contrast point and matters in attacks and phase changes.
- The **halo** is celestial instrument or seal, not decoration: sacred geometry that lights during attacks.
- Feather-blades replace legs: it is never truly standing.

**Movement: it glides, almost never runs.** Smooth, precise, and it appears to simply *decide* where it will be.
Examples: drifting backward while facing the player; sliding sideways without turning the torso; rising vertically
before an attack; stopping dead in midair; advancing with almost no preparation; rotating the body while wings stay
fixed; folding the wings like a cloak, then unfolding. **Posture is itself the telegraph.**

**Idle:** it spends a surprising amount of time doing almost nothing: gentle hover, faint wing motion, slowly turning
halo, pulsing core, upward particles, occasional feather adjustments. Total stillness should read as *something is
about to happen*.

**Combat philosophy:** large, readable movements with **deceptive reach**; ceremonial, not frantic. Attacks look
slow, but its size makes the true range much larger than expected.

**Refined attacks** (in addition to the sheet's six, §2; reconcile at build time):

| Attack | Description |
|---|---|
| **Wing Sweep** | Slowly opens one side of its wings, pauses, then the whole wing structure sweeps across a huge part of the arena. The anticipation is the point. |
| **Halo Beam** | Goes completely stationary; halo rotates and its geometry lights; core intensifies; a focused celestial beam fires from the halo or along the chest axis. Reads as activating machinery, not casting a spell. |
| **Descent** | Rises very high, wings fold inward, drops almost vertically and very fast; large radial shockwave on impact. |
| **Feather-Blade Barrage** | Lower-body feather-blades separate, float briefly around it, then launch at predetermined areas. |
| **Wing Cloak** | Folds all wings around itself into an enclosed silhouette, then explodes outward as a radial attack or many directional projectiles. |
| **Celestial Rotation** | Spins on its vertical axis in place; extended wings become a massive rotating hazard, like a celestial mechanism. |

**Phase 2: control was only temporary.**
- Chest core much brighter; halo geometry more active.
- Wings begin to move **independently of the body**: orbiting, sweeping, repositioning.
- **Detached Wings (the key phase-2 mechanic):** wings can **detach** from the body and become enormous floating
  blades, rings or sweeping structures around the arena, while the Seraph itself stays relatively still. The
  player must track both the body and the structures.
- **Low health:** the body can rotate independently from the lower silhouette, the halo can re-orient on its own,
  wings run on separate timing, and the core becomes the brightest thing in the arena. The aim is not faster
  attacks but that **the rules governing the Seraph are coming apart**.

Build notes (interpretation): detached wings mean each wing needs its own server-driven position and hitbox
(rule 5); the six wing segments are the natural detach units, which fits the sheet's "6 wing segments, independent
motion". The 3-phase fight and the sheet's "phased movement (ground/aerial)" should be reconciled (aerial may be
movement style rather than a phase).

### 5A.3 The Celestial Dancer, refined

**Identity:** the opposite of the Seraph: **asymmetrical, elegant, fast, intensely deliberate**, combat turned into
choreography. **Rule: she never appears to move like a normal fighter.** She steps, pivots, glides, turns,
pauses, then suddenly crosses an enormous distance.

**Visual points added:** hood or veil hides the face (no reliance on expression); dark bodice and gold high-heeled
boots contrast the enormous cape; the cape is the dominant shape: long, layered, gold-edged, pale lavender-white
into deeper violet, with embedded energy particles that grow during attacks.

**The cape is a major animated component (not a rigid accessory):** lags in normal movement; swings out on turns;
trails on dashes; keeps moving after a stop, then settles; sections flare during attacks; can hide her silhouette
so the player sees only a field of fabric before the blade emerges; edge particles linger after movement.

**Movement language: Step → glide → turn → slash → pause → accelerate.**
- **Step:** a deliberate, possibly harmless-looking step that can begin a larger sequence.
- **Glide:** slides with very little vertical motion, feet barely pushing, cape following.
- **Pivot:** rotates on one foot, upper body first, cape after; the blade trails and completes the strike at the end.
- **Pause:** she stops, the cape and particles keep moving, the blade is still. It creates tension, then the next
  move comes almost instantly.
- **Sudden acceleration (signature):** from near-still to crossing a large part of the arena in one elegant move
  (not a conventional dash); the player sees the start but the distance is surprising.

**Combat philosophy:** difficulty from **rhythm recognition and movement deception**, not visual chaos. Attacks are
beautiful enough that players may watch instead of reacting; through repetition they learn the choreography ("I
know what that step means").

**Refined signature attacks** (in addition to the sheet's eight, §3; reconcile at build time):

| Attack | Description |
|---|---|
| **The Opening Waltz** | Slow approach, a step, a rotation, the blade drags along the ground leaving a light trail; a pause; then a sudden long horizontal slash covering far more distance than the setup suggests. |
| **Veiled Step** | Turns away; the cape expands and hides her and the weapon; she emerges from the opposite side with a rapid slash. A recurring defence/attack transition. |
| **Crescent Waltz** | A wide spin sequence: slow first turn, faster second, final turn a huge sweeping blade arc, the cape a few frames behind for a layered circular silhouette. |
| **Falling Star** | Rises slightly, cape lifting; pauses midair; descends diagonally dragging the blade; bright line and a brief lingering danger zone along the path. |
| **Silent Step** | Stands completely still, shifts her weight, then vanishes forward in a very short, very fast move; visible only through cape and blade trail. Teaches players to read her body language. |
| **Twin Echo** | Sword sequence creating delayed afterimages: the real sword strikes once, and a luminous echo repeats the slash a moment later. |
| **Floating Blade Sequence** | Later phase: extra blades hover and follow the choreography (she spins, a blade follows the arc, she stops, the blade continues, she changes direction as it completes the earlier motion): the choreography generates weapons. |

**Phase 2: a more complete dance, not rage.**
- More complex choreography, more deceptive pauses, a more active cape, and chaining with little recovery, e.g.
  step → slash → stop → spin → disappear → reappear → glide → second slash, **while she still looks calm**.
- Weapon stays the single long blade; **Twin Echo** afterimages and floating blades carry the "twin" idea (§5A.1).
- **Signature: The Grand Dance.** She moves to the arena centre, the cape expands, the music can briefly quiet, and
  she performs a long **repeatable** sequence the player can learn: (1) slow step, (2) forward glide,
  (3) horizontal slash, (4) long pause, (5) spin, (6) backward glide, (7) sudden forward acceleration,
  (8) floating blade sweep, (9) cape concealment, (10) final crossing slash. It should read as a performance.
- **Final stretch (low health):** cape saturated with energy, more particles, longer brighter blade trails, more
  aerial movement (skimming above the ground in long transitions). **Movement and attack blur together**: a glide
  can be a slash, a spin a teleport-like reposition, a cape turn can hide a strike, a landing can be an area
  attack, and the player is never sure whether she is positioning or attacking.

**Defeat:** no ragdoll. She stays standing a moment, the blade lowers, the cape settles, particles drift away, she
takes one last step, the cape falls still, and the weapon dissolves into light as she fades, keeping the fight's
elegance.

Build notes (interpretation): the cape needs bone-chain or baked secondary motion driven by movement (see §3 cloth
caveat); "The Grand Dance" is a fixed scripted sequence, i.e. boss data (Content), not System code; the pauses and
telegraphs mean movement must be server-authoritative but readable, and hit windows must follow the visible motion.

### 5A.4 The contrast (from the refinement)

| | Astral Seraph | Celestial Dancer |
|---|---|---|
| Silhouette | Symmetrical | Asymmetrical |
| Movement | Floating / monumental | Gliding / choreographed |
| Scale | Enormous | Tall and elegant |
| Combat | Large-area celestial attacks | Precise chained movement |
| Main visual feature | Wings + halo | Cape + blade |
| Threat | Reach and scale | Rhythm and acceleration |
| Body language | Stillness | Constant choreography |
| Phase progression | Anatomy becomes impossible | Dance becomes increasingly complex |
| Player skill | Reading large telegraphs | Learning movement patterns |

The Seraph is **something celestial the player cannot comprehend**; the Dancer is **something beautiful the player
can eventually learn to understand**. Neither should feel like a conventional fantasy boss with celestial
decorations added.

### 5A.5 Final movesets by phase (owner, 2026-09-29: locked)

This is the owner's **final attack assignment**. It **resolves the earlier attack-list reconciliation**: the sheet's
lists (§2, §3) and the refinement's (§5A.2, §5A.3) are now merged into the lists below. Where they differ, **these
lists win.** The sheet's Wing Slash, Halo Blast, Divine Lance, Aerial Dive, Wing Barrage and Phase Shift, and the
Dancer's Twin Slash, Lunar Dash, Phase Step, Celestial Rain, Aerial Rotation and Ending Blade, are **not in the
final lists**; they may inform animation or variations but are not planned attacks unless the owner re-adds them.

**Core distinction:** Seraph = increasingly complex **overlapping celestial structures**. Dancer = increasingly
complex **choreography and movement chains**.

#### Astral Seraph

**Phase 1: The Celestial Guardian**

| Attack | Description |
|---|---|
| Wing Sweep | Massive horizontal wing attack covering a wide area. |
| Halo Beam | Sacred geometry activates on the halo before firing a focused beam. |
| Descent | Rises high, folds its wings, then rapidly descends with a radial shockwave. |
| Feather-Blade Barrage | Feather-blades separate and launch toward targeted areas. |
| Wing Cloak | Wings fold around the body before explosively opening outward. |
| Celestial Rotation | Rotates with extended wings, creating a large circular hazard. |

**Phase 2: The Unbound Seraph**

| Attack | Description |
|---|---|
| Detached Wings | Wing structures detach and independently attack around the arena. |
| Independent Wing Sweeps | Detached wings perform separate sweeping attacks while the Seraph remains airborne. |
| Halo/Body Rotation | Halo and body rotate independently, creating overlapping attack patterns. |
| Expanded Feather-Blade Barrage | More feather-blades detach and attack from multiple directions. |
| Celestial Rotation (expanded) | Detached wings participate in the rotation. |

**Final Phase: Ascension**
- All previous attacks, in significantly less predictable combinations.
- Detached Wings become independent floating blades/rings.
- Halo Beam and wing attacks can overlap.
- Body, halo and wings move on separate timing, so the Seraph feels increasingly impossible to interpret.

#### Celestial Dancer

**Phase 1: The First Dance**

| Attack | Description |
|---|---|
| Opening Waltz | Slow approach, rotation, ground-trailing blade, sudden forward slash. |
| Veiled Step | Cape conceals her movement before she emerges with a strike. |
| Crescent Waltz | Progressive spinning sequence ending in a large sweeping slash. |
| Falling Star | Brief aerial rise followed by a diagonal descending attack. |
| Silent Step | Momentary stillness followed by an extremely rapid movement/strike. |

**Phase 2: The Grand Dance**

| Attack | Description |
|---|---|
| Twin Echo | A blade strike leaves a delayed luminous echo that repeats the movement. |
| Floating Blade Sequence | Additional blades orbit/follow the choreography and attack independently. |
| Grand Dance | Extended multi-stage choreography combining movement, pauses, spins, glides and sudden acceleration. |
| Veiled Step (more frequent) | Used as the transition between attacks. |
| Crescent Waltz (expanded) | Longer chained sequences. |
| Falling Star (chaining) | Can transition directly into another movement instead of recovering. |

**Final Phase: The Unending Dance**
- All previous attacks, chained together with minimal recovery.
- Movement itself becomes part of the attack: glides become slashes, spins become area attacks, cape turns become
  concealed attacks, landings become impact attacks.
- Floating blades can continue previous attack arcs while the Dancer changes direction.
- The Grand Dance becomes the centerpiece sequence, combining nearly every movement pattern.

**Phase count (owner-confirmed 2026-09-29): each boss has 3 phases**: Phase 1, Phase 2 and the Final Phase. This
supersedes the earlier "2 phases" wording; the Final Phase is a full phase, not a low-health escalation.

---

## 6. Open questions (to settle before building, not decided here)

1. ~~How do the two bosses relate?~~ **Settled 2026-09-29:** one per run, 75% Seraph / 25% Dancer (provisional, §4.5).
2. ~~Phases and attack assignment~~ **Settled** in §5A.5: 3 phases each.
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

## Universal safety boundaries

This records the owner's 2026-09-30 safety requirement; it does not replace the existing
world blueprint or define a new kit/connection vocabulary. Full map schema remains pending.

Every playable chunk needs invisible player-collision boundaries along exposed platform
and walkway sides, following local floor height and accompanying its parent chunk.
Initial height is 64 studs. Leave all socket mouths, bridges and doorways clear.
Backdrops need no boundaries; enclosed rooms use their solid walls.
Camera queries explicitly exclude the boundaries. Future animated visual identification
is a separate noncollidable prop, independent of the fixed collision wall.
Verify drop edges, traversal clearance and jump escape attempts in Studio.
See [shared map requirement](../MODULAR_MAPS.md). Generic runtime support is pending.
