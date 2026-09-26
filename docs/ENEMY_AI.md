# Enemy AI: how every enemy, miniboss and boss thinks, adapts and is tuned

> **Status: design only, 2026-09-25. Number reserved 2026-09-26.** Nothing here is built, and nothing here may be
> built yet: combat, enemies and bosses are excluded by build spec §7. §7.6 is now claimed and this doc's module
> names are locked (spec §7.6), but step 0 is not fully closed — remotes and `GameConfig` blocks are still
> undecided, deferred to step 1. Until step 0 closes, this document is a design to agree on, not a task list.
>
> **Scope, owner-directed 2026-09-25.** This document is **authoritative for enemy behaviour** and supersedes any
> earlier behaviour scheme: the behaviour column of `ENEMY_FRAMEWORK.md` §3 and the service description in its §6.
> `ENEMY_FRAMEWORK.md` still owns how an enemy is **built**: roster, body, rig, animations, combat markers, tell
> and recovery frames, VFX cues, and the `EnemyDef` data shape. Where the two touch, this doc reads the framework's
> build data and never redefines it.
>
> **Agents:** follow §12 in order. Never start a step until the previous step's exit criteria pass, and never
> author enemy behaviour before its contracts exist.

---

## 1. Goals

1. **Smart:** enemies make contextual decisions, not scripted loops.
2. **Fair:** every loss feels earned and readable.
3. **Adaptive:** bosses evolve across the whole player base, and fight tempo adapts to each player.
4. **Universal:** one system serves every world. Nothing is built around one biome, including Sky Citadel, which
   only happens to be the first world with a roster.
5. **Fun first:** intentionally challenging, but winnable by anyone.

## 2. Governing rules

These are the `AGENTS.md` rules applied to AI. They are not new rules.

- **Systems are reusable. Content is data.** A new enemy, boss or world is one file under `src/shared/Content/`.
  If AI behaviour for it needs a System change, the schema is wrong: stop and propose an amendment.
- **A player has movement. An item has combat** (`PLAYER_ABILITIES.md` §0). Player damage lives on items, so the
  combat language (§4) is shared by items and enemies, never by the player.
- **The roll is true RNG (D-8).** Difficulty never changes any odds. It changes only the *number* of loot rolls
  (§9).
- **No world-specific code paths.** A world contributes data: its effect palette, its chunk markers, its roster.
- **Every tunable lives in `GameConfig`.** Tick rates, caps, jitter, adjustment ranges: none are literals in a
  System.
- **No `math.random`.** Score jitter and variant rolls use the owning System's `Random`, so fights are seedable and
  the headless sims are reproducible.
- **Server authority.** The server perceives, decides, and resolves hits. Clients play animations, telegraphs and
  VFX.
- **Schemas before content.** The contracts in §4–§6 are locked and tested before any behaviour is authored.

## 3. Architecture

The names are proposals; the step 0 amendment fixes them, together with the naming rules in `AGENTS.md`.
`ENEMY_FRAMEWORK.md` §6 already proposes `EnemyService` and `BossService`, and this design keeps them as the only
two Systems.

| Module | Kind | Responsibility |
|---|---|---|
| `CombatCore` | pure core | damage, hit resolution, status effects, the ability/move format |
| `PerceptionCore` | pure core | sight cone, hearing radius, last-known position, alert state |
| `EnemyAICore` | pure core | utility scoring: considerations → action scores → chosen action |
| `DifficultyCore` | pure core | universal profile + personal adjustment → multipliers |
| `BossCore` | pure core | phases, scripted sequences, party scaling, evolution-profile selection |
| `TelemetryCore` | pure core | shapes the fight summaries sent to sims and to evolution |
| `EnemyService` | System | spawning, ticking brains, movement drivers, archetype dispatch |
| `BossService` | System | phase changes, sequence playback, punish windows |

Every pure core runs in the headless suite (`tests/cases.luau`). The two Systems are thin: they wire the cores to
Roblox instances and hold no rules of their own.

## 4. The combat language (shared by items and enemies)

- **Damage types:** one fixed, universal list.
- **Hitboxes:** resolved on the server, with standard size classes (§7).
- **A move** is data. An enemy move and an item attack use the same shape:
  - an id, a damage value and damage type, a hitbox shape and size class, and a cooldown;
  - an optional status effect, which must be in the world palette (§6);
  - a telegraph cue id (the framework's standard cues, `ENEMY_FRAMEWORK.md` §5);
  - the animation action it plays.
- **Timing comes from the animation, not from a number the AI owns.** The framework's combat markers (`Tell`,
  `HitStart`, `HitEnd`, `RecoverStart`) define the windup, active and recovery windows, and `anim_core.end()`
  already enforces the tell and recovery minimums (framework §4). The AI reads those windows. It never shortens
  them.
- **Status effects** are defined once (behaviour, icon, colour, sound). Worlds whitelist which ones may appear.
- **Readability:** one cue means one thing in every world, and no cue relies on colour or sound alone.

### 4.1 Weapons carry their own moves

Owner-directed 2026-09-25, consistent with `PLAYER_ABILITIES.md` §0 and `WEAPONS.md`.

- **Every weapon has built-in functionality:** its moves are data in the same move format as an enemy's, bound to
  the weapon, never to the player.
- **Weapon types share a base moveset** (Sword, Greatsword, Dagger, Hammer, Staff, Bow, Gauntlets), so Common to Epic
  weapons of one type fight alike and differ by stats, effects and look.
- **Legendary and Mythic weapons have unique movesets**, designed one at a time like a boss: a moveset sheet, one
  action per move, the same marker and fairness rules.
- **Enemies read weapon moves the way players read enemy moves:** a charged or signature attack has a tell the AI
  perceives, and the AI never reacts faster than the human window (§8).
- **A weapon's effect must fit its world's palette** (§6) when the weapon comes from a world's drop pool.

## 5. The map contract

Every chunk gives the AI the same kinds of information, so any world gets smart enemies without new code.

- **Markers are named empties authored in Blender** and exported with the chunk kit:
  `AI_Cover_##`, `AI_Perch_##`, `AI_Patrol_<Route>##`, `AI_Spawn_##`, `AI_Choke_##`, plus arena bounds for boss
  rooms. The exact names are fixed in step 0 and then added to `CHUNK_AUTHORING.md`.
- **Derived in code where possible:** walkable area, ledge edges, open sky. Hand-placed markers carry design intent
  only ("a good sniper perch"), which keeps authoring light.
- **Retrofit once:** the existing Sky Citadel and Verdant Valley kits get one marker pass. Ethereal Scape is an
  authored map with no chunk kit, so it gets its markers placed on the map itself.
- **Validator:** a test fails any kit piece missing a required marker, the same way the kit's `validate()` checks
  already work.
- **Base kit only:** markers and the moves that use them must work on the base kit, never on scenario-only features
  (framework §4, "No map dependencies").

## 6. World effect palettes

- Each world file declares its allowed status effects and damage flavours, for example Sky Citadel: shock,
  knockback, wind.
- An enemy may only use its home world's palette. **The schema check rejects any other effect.**
- Difficulty changes an effect's intensity or frequency within the palette. It never introduces an effect from
  outside it.
- The Fate Engine is still a placeholder. The AI reaches it through one interface, "apply world effect X at
  intensity Y", fixed in step 0 so AI work is not blocked while the Fate Engine's logic and animation are
  finished. The interface is registered in `RESERVED.md` until something reads it.

## 7. Archetypes

The framework's `role` picks the behaviour (framework §3: `melee_guard`, `brute`, `diver`, `hover_melee`,
`hover_ranged`, `ranged_thrower`, `caster`, `swarm`, `ambusher`, `miniboss`, `boss`). This document adds what each
role **thinks**, grouped by how it moves.

| Movement family | Roles | Actions it scores | Key heuristic |
|---|---|---|---|
| **Ground melee** | `melee_guard`, `brute`, `swarm`, `ambusher` | Approach, Strike, Lunge, Circle, Block, Retreat | a close range band; **attack tokens** cap how many attack one player at once, and the rest circle |
| **Ranged** | `ranged_thrower`, `hover_ranged`, `caster` | Kite, Fire, Channel, Reposition, Flee-to-ally | a preferred distance band; backs off when crowded; repositions to a line-of-sight marker |
| **Flying** | `diver`, `hover_melee`, `hover_ranged` | Orbit, Dive, Strafe, Perch | steering, not pathfinding; dives when the target is busy; must come into sword range (framework §2) |

- **Animation slots are the framework's actions** (Idle, Move, attacks, Hit, Death), so a new enemy of a role reuses
  the whole brain and only needs its own art.
- **Size classes** standardise reach and hitboxes across worlds, tied to the framework's tier budgets.
- **Modifiers are data:** personality (Cowardly, Berserker, Tactician, Greedy) shifts weights, and Fate-touched
  variants (Elite, Mirror, Splitter) add a trait. A variant roll is its own roll, owned by `EnemyService`, and has
  nothing to do with the world roll.

## 8. The decision model (utility AI)

- **Tick:** a few times a second, staggered across enemies; the rate is in `GameConfig`. Distant enemies sleep.
- **Considerations** are small pure functions returning 0–1: distance, own health, target health, line of sight,
  cooldown ready, allies nearby, "the target is attacking me", and so on.
- **Score** = the action's weight × the product of its considerations, plus a small seeded jitter.
- **Targeting:** a threat table (damage dealt, distance, last attacker). It is multi-target from day one: solo is a
  party of one.
- **Squads:** a shared blackboard assigns flank, bait and support roles.

### Fairness guardrails (hard rules, tested)

- The framework's tell and recovery minimums always hold (framework §4), and difficulty only ever **lengthens**
  them.
- No perfect aim, and no reaction faster than a human window (a `GameConfig` value, about 200 ms).
- An enemy knows only what `PerceptionCore` grants it.
- At most three attacks without a window, with a gap between strings (framework §4).
- In-fight adaptation is capped and resets when the fight ends. Only universal boss evolution (§10) persists.

## 9. Difficulty and rewards

**There is no difficulty setting.** Two automatic layers stack:

1. **The universal profile:** the shared, versioned tuning every player fights. This is what evolves (§10).
2. **The personal adjustment:** an invisible, capped change to fight **tempo**, per player, on top of the profile.

### The personal adjustment

- It reads performance signals (damage dealt, dodge rate, progress through the fight), **never deaths alone**. A
  player who dies on purpose produces weak signals, which count as low confidence.
- Easing is gradual, capped (around 15–20%, in `GameConfig`), and does not reset on death.
- Easing means longer tells, slower pacing and fewer simultaneous attackers, **not** less HP or damage. The fight
  still looks and feels like the real one.
- Hardening uses the same levers in the other direction.
- In a party, the adjustment is blended, weighted toward the stronger players, so a carried player cannot soften
  the fight for everyone.

### Rewards

- **Every clear pays the full base reward and full progression.** The bonus sits on top; nothing is taken away.
- A harder tempo earns **more loot rolls, never better odds.** Every roll uses the same honest table (D-8).
- The bonus is modest (around +10–30%) and never gates anything essential: progression, worlds and story stay
  reachable for everyone.
- A clear rating is shown after the fight, never during it.
- **Dying on purpose to farm easy clears must always pay less than playing properly.** A test pins this.

### Win-rate targets

These are tuning targets for the simulations, not runtime rules.

| Tier | Target rate at which the player loses |
|---|---|
| Basic enemy | about 10–15% |
| Boss | about 40–60% |

CI flags any configuration whose simulated rate lands far outside its band.

## 10. Bosses

The same brain as every enemy, with more layers, all driven by the moveset sheet (framework §1 step 6):

- **Phases:** HP thresholds swap the move set and the weights, with the sheet's transition action.
- **Scripted sequences:** authored combos, chosen as a single action.
- **Party scaling (data):** an HP multiplier, more attack tokens and more multi-target moves, not HP alone.

### Universal evolution

- Each boss fight sends a small summary (which moves landed or were dodged, the players' range, fight length,
  outcome) to a global rolling store.
- A periodic server job nudges the weights toward countering what is currently working ("the meta"), inside caps.
- **Every step is a new, versioned profile** (for example `WINGED_SENTINEL` v2.4), logged with before and after
  numbers.
- Learning is split by **skill cohort**, so veterans never drag the boss out of reach for new players.
- Only a profile that passed the simulations can go live, and **every step can be rolled back.**
- There is no per-player boss memory.

### Raid-ready, not raids

- Multi-entity bosses share one blackboard.
- Nothing in code assumes four players. Raids (4–10+ players) are future scope, with their own design document.

## 11. Tuning and telemetry

- **Simulation:** headless bot players (aggressive melee, kiter, turtle, button-masher) run thousands of fights per
  configuration, plus sweeps over individual weights.
- **Playtest telemetry:** deaths, the killing move, dodge success, fight length, and quits mid-fight.
- **Versioning:** roles, moves and weight profiles all carry versions.
- **A tuning log** (`docs/AI_TUNING_LOG.md`, created at step 8) records every change: what, why, before and after.
- **Regression tests** lock in behaviour that is known to be good.
- **No live machine learning in production.** "Learning" means versioned, tested weight changes.

## 12. Order of operations (mandatory)

Each step ends with exit criteria. **Do not start a step until the previous one passes.** Every step updates
`STATUS.md`, `WORKLOG.md` and the index as `AGENTS.md` requires, and every `src/` change needs the owner's OK
(framework §6).

This order sits inside `DEVELOPMENT_PLAN.md` §4: **items and inventory come before combat.** Steps 1 and 3 depend on
the item schema.

| # | Step | Exit criteria |
|---|---|---|
| 0 | **The amendment.** ~~Claim the next §7.x number~~ **done: §7.6, 2026-09-26.** ~~Fix module names~~ **done, spec §7.6.** Still open: remotes (spec §4 first) and `GameConfig` blocks | owner approves the amendment as a whole |
| 1 | **Contracts:** damage types, status effects, the move format, size classes, marker names, the palette schema, the Fate Engine interface | schemas in `Types` / `Schema`; schema tests pass; `RESERVED.md` rows for anything unread |
| 2 | **`CombatCore`** (pure) | headless tests: damage, hit resolution, effects, palette enforcement |
| 3 | **Item combat:** attacks, dodge and timing windows on items, server-resolved | Studio pass; the dodge and reaction timings are written down, because the guardrails depend on them |
| 4 | **The map contract:** marker names in `CHUNK_AUTHORING.md`, the validator, the retrofit | the validator passes on every kit piece of every world |
| 5 | **`PerceptionCore` + `EnemyAICore`** (pure) | headless decision tests, e.g. "a ranged enemy at low HP retreats to an ally" |
| 6 | **Vertical slice:** one ground-melee basic, one world, end to end through `EnemyService` | a Studio fight works; the guardrails verified; the enemy defined as data only |
| 7 | **Ranged and flying families** | each passes its decision tests on the kits of **every** world |
| 8 | **Simulation harness:** bot players, sweeps, win-rate reports, the CI gate; start the tuning log | basic enemies meet their target band |
| 9 | **`DifficultyCore` + rewards** | the farming-by-dying test passes |
| 10 | **`TelemetryCore`** | fight summaries are logged and shaped correctly |
| 11 | **`BossCore` + `BossService`:** phases, sequences, party scaling | the first boss meets its band in sims and in a playtest |
| 12 | **Universal evolution:** cohorts, caps, versions, rollback | a dry run produces a valid, logged, reversible profile |
| 13 | **Content across worlds** | every new enemy or boss is data only |
| — | *Future:* raids | a separate design document |

### Rules for agents

- Never skip or reorder a step.
- Never add a world-specific branch to a System.
- Never give an enemy an effect outside its world's palette.
- Never let difficulty change any odds.
- If a step needs a contract change, change §4–§6 and their tests first, then note it in `WORKLOG.md`.

## 13. Open questions

- Perception details: stealth, sound events, alert states.
- Loot-greed behaviour, and how the Greedy personality interacts with drops.
- The exact status-effect list and each world's palette.
- The Fate Engine's logic and the final form of its interface.
- How item combat feels, settled at step 3.
