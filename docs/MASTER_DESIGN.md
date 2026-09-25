# LUCKBOUND — Master design

**The single design-level source of truth.** What the game is, how its parts
relate, and what is built versus planned.

> **Why this is markdown and not a PDF.** This replaces
> `LUCKBOUND_Master_Spec_v0.2.pdf`, a seven-page binary snapshot generated
> after Phase 1. It could not be diffed, could not be reviewed in a pull
> request, and drifted the moment anything shipped — a second source of truth
> competing with the living docs, which is exactly what AGENTS.md rule 1
> exists to prevent. The v0.1 PDF at the repository root stays: it is the
> owner's original vision and remains **authoritative on intent**. Where this
> document and v0.1 disagree about what the game is *for*, v0.1 wins.

| Layer | Document |
|---|---|
| **Intent** | `design/LUCKBOUND_MGD_Original_v0.1.pdf` — the original vision |
| **Design** | **this file** |
| **Architecture** | `PROTOTYPE_BUILD_SPEC.md` — canonical, schemas and remotes |
| **Order of work** | `DEVELOPMENT_PLAN.md` |
| **Current state** | `STATUS.md`, then `WORKLOG.md`'s top entry |

---

## 1. The game

> **Roll your fate. Enter the unknown. Become legendary.**

You stand at the Crossroads and roll. The roll gives you a world, weighted by
rarity — Common to Mythic. You enter it, explore a map you have never seen in
that exact arrangement, and get out before the timer. Then you roll again.

**The differentiating mechanic is the roll**, not the combat. The owner's own
verdict on the prototype was *"these rolls alone were fun"*, with no combat, no
loot and grey blockout. Everything else exists to give the roll somewhere to
lead.

### The loop

```
CROSSROADS → ROLL → react to what Fate gave you → ENTER
   → a generated map, seeded from the roll
   → find things, survive things, reach the arena
   → return before the timer → rewards → ROLL AGAIN
```

---

## 2. Fate

Fate is the identity of the game and it reaches further than a loot table.

**The roll is true RNG.** `FateInfluencesOdds` is false and the ladder that
would let a player's profile bend world odds is dormant behind it. A roll that
can be bought is not a roll. This is settled — see `STATUS.md` §3.

Where Fate *does* reach:

| | |
|---|---|
| **Which world** | weighted by rarity, true RNG |
| **What a room becomes** | Fate may override ordinary scenario weighting and pick from the rare band — build spec §7.3 |
| **World modifiers** | a world re-tinted and re-ruled (`NIGHT`, and per-world overrides) |
| **Live events** | server-wide, scoped and precedence-ordered — `EVENTS.md` |
| **Scarcity** | some things only ever exist ten times, ledger-backed |

The target feeling, from the *Procedural Biome Design Brief*:

> **"I know this place. I don't know what is going to happen here."**

---

## 3. Worlds

Five rollable worlds in Phase 1. Weights sum to 10000 so they read as
percentages.

| World | Rarity | Phase 1 | Map | State |
|---|---|---|---|---|
| **Verdant Valley** | Common | 60% | chunk kit | 11 pieces delivered and uploaded |
| **Ethereal Scape** | Uncommon | 15% | prebuilt scene | delivered, walkable |
| **Emberfall** | Rare | 15% | — | blueprint exists, no kit |
| **Sky Citadel** | Epic | 7% | — | **no blueprint at all** |
| **Astral Reach** | Mythic | 3% | — | blueprint exists, no kit |

**25% of honest rolls land on a world with no map.** That is the single largest
content debt and `DEVELOPMENT_PLAN.md` §3 owns the plan for it.

Each world's design lives in `biomes/<WORLD>.md`. Each world is *data* — adding
one is a file under `Content/Worlds/` and changes no System.

### Two routes to a map

A world declares exactly one; declaring both is a boot error.

| | Chunk kit | Prebuilt map |
|---|---|---|
| Built by | `ChunkCore` + `ChunkLoader` | `PrebuiltLoader` |
| Every run | different layout from the seed | identical |
| Art must be | modular — matching rims, gaps, heights | anything at all |

Neither is better. A kit buys variety and charges modularity for it.
`MODULAR_MAPS.md` has the full argument.

---

## 4. Procedural generation

The core design bet, and the part the *Procedural Biome Design Brief* sharpened:

> **Author a small library of strong physical chunks, then create run-to-run
> variety by independently changing what happens inside them.**

Model count is not content count. Six layers, each reading only the one before:

```
RUN SEED
  → CHUNK SELECTION        ✅ ChunkCore
  → CONNECTION VALIDATION  ✅ ChunkCore
  → SCENARIO SELECTION     ✅ ScenarioCore      build spec §7.3, wired into
                                              ExpeditionSystem 2026-09-23
  → ENCOUNTER CONFIG       ⬜ needs combat
  → REWARD CONFIG          ⬜ needs items
  → FATE EVENTS            🟡 scenario-level only
```

**The seams are lists of plain numbers and ids**, so every layer above is
generated and asserted in CI without Roblox running.

### Chunks

A world's kit is 12–16 distinct kinds of place. Pieces join only at declared
sockets, and only where socket `Kind` matches — a per-world vocabulary that is
the level-design grammar rather than a technical detail. The Kind the arena
accepts is automatically reserved, so the approach to a boss is always
deliberate.

> **A Kind offered by exactly one piece is a gate AND a sameness.** Verdant
> Valley learned this: one `WIDE` provider meant the same room preceded the
> boss on every seed. Three providers keep the gate and lose the rut.

### Scenarios

A chunk declares `Supports` — what can happen there. Compatibility is
deliberate, not universal. The generator intersects that with
`Content/Scenarios` and assigns one per room, with:

- **structured pacing** — ordinary is the backbone, rare unlocks later in a run
- **anti-repetition** — never the same scenario twice running, and recent
  *(chunk, scenario) pairs* damped, because a place reappearing is fine when
  something different happens in it
- **Fate intervention** — rare, and able to ignore the weighting entirely

Measured today: **50 distinct chunk/scenario rooms from 11 pieces.**

### What is not built

Enemy population, reward configuration and pathfinding validation. `EnemyTags`
are declared per piece and nothing reads them — the design recorded ahead of
the system that will.

---

## 5. Systems

**Prime directive: systems are reusable, content is data.** A System contains
behaviour and no content. Adding a world, enemy, item or scenario means editing
one file under `Content/` and changing no System. If content seems to need a
System change, the schema is wrong.

| Built | State |
|---|---|
| Roll, Fate levels, onboarding arc | solid |
| Saves, migrations, the scarcity ledger | solid |
| The Crossroads hub, authored and walkable | solid |
| Player UI, travel, codes, settings | solid |
| Movement — sprint, double jump | solid |
| Live events, scoped and precedence-ordered | solid |
| Expedition entry, seeded maps, a way home | walkable |
| Scenario selection | wired into the expedition flow; unwalked |
| Parties, expeditions on their own server | built; unwalked (TESTING O/P) |
| Sky Citadel + Verdant Valley chunk kits, ambience, props, chests/vault | uploaded; Sky Citadel walked |
| Enemy art pipeline + all 16 Sky Citadel enemies (models, rigs, first actions) | built in Blender, not spawned in game (`ENEMY_FRAMEWORK.md`) |
| Boss preview in Studio + the Aether Lance's live lightning / charge switch | `/showboss`, `/bossphase` (debug) |

| Not built | Needed for |
|---|---|
| Combat: enemy AI, damage, bosses in play (the art exists) | launch, not the first playtest |
| Items, inventory, loot | launch |
| Discoveries — findable things | **the first playtest** |
| Sound, tutorial | the first playtest |
| Fate Tree, Rebirth, shop, rifts | launch |

---

## 6. Phases

**Phase 1 is complete.** Its deliberate exclusions are build spec §7, and they
hold except where an amendment records otherwise:

- **§7.1** opened expedition entry — arrive, walk a generated map, come back.
- **§7.2** opened parties, and expeditions as their own server.
- **§7.3** opened the scenario layer — decide and record what a room is; spawn
  nothing.

Amendment numbers are claimed in the index at the head of §7, in the same
change. Two branches once claimed §7.2 simultaneously.

Both were owner-directed and written down rather than done quietly. That is the
process: **an exclusion is lifted by an amendment in the spec, in the same
change that lifts it.**

### Next, in order

`DEVELOPMENT_PLAN.md` is authoritative. The short version: close the loop
*without* combat — something to find in a world, maps for every rollable world,
sound, a tutorial — and playtest the roll, because that is the premise that has
never been stress-tested by anyone who did not build it.

---

## 7. The rules that protect this

Full list in `AGENTS.md`. The three that have actually saved the project:

1. **Never create a second version of a module.** CI greps for `_v2`, `_final`,
   `_old` and fails the build.
2. **Assert relationships, not literals.** `Plaza.Diameter == 1150` was true
   the whole time the plaza was a wall. Four chunk tests named `VV_GROVE` and
   broke when the kit improved, while the properties they meant were untouched.
3. **Specify the seam, not the piece.** A brief that specified piece size, edge
   treatment and a 13-item checklist produced a kit built to the document
   rather than to the world. Art briefs state what must be true for the piece
   to work, and leave the rest to the artist.
