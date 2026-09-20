# LUCKBOUND — Player Abilities & Upgrades

**Status:** §1 and §2 are built. §3 onward is **planning** — owner-requested
ideas, not commitments, and nothing here is implemented.

---

## 0. The line this document exists to hold

> **A player has movement. An item has combat.**

Owner-directed, and it is the most important rule in this file. Damage, reach,
swing arcs, cooldowns, hit effects, elemental procs and animations belong to
**the model that grants them** — a sword carries its own attributes and its own
script. The player carries how they get around.

Why it matters beyond tidiness: if abilities live on the player, then every new
weapon is a change to the player, and the player becomes the place every
system meets. Put them on the item and a new sword is a new model with a new
attribute table — content, not code. It is the prime directive applied to
combat before combat exists.

**The test that pins it:** `no player ability config carries a combat number`
fails the build if `GameConfig.Locomotion` ever grows a field whose name
contains damage, attack, crit or dps.

---

## 1. Built: sprint

| | |
|---|---|
| Input | Left Shift, or L3 on a gamepad. Touch: hold-to-move |
| Speed | `Scale.WalkSpeed × SprintMultiplier` — 32 × 1.55 ≈ 50 |
| Ramp | 0.25s up, 0.4s down, so it reads as effort rather than a speed setting |
| Stamina | 100, draining 12.5/s → **8 seconds of sprint** |
| Refill | 16.6/s after a 0.8s delay → **6 seconds to full** |
| Exhaustion | At zero, sprint cuts out and cannot restart until the delay passes |
| Indicator | A 120px pip above the roll prompt. Fades in when spent, out when full — a player who never sprints never learns there is a bar |

**Why stamina at all.** Without it, sprint is not an ability, it is the walk
speed — everyone holds Shift forever and the number in `Scale.WalkSpeed`
becomes a lie. Eight seconds is roughly the walk from the Engine's dais to a
district, so a sprint is exactly "skip one leg", which is a decision.

**Standing still costs nothing.** Holding sprint while stationary does not
drain, because draining for it would teach players to let go of a key that
costs them nothing.

## 2. Built: double jump

| | |
|---|---|
| Budget | One ground jump plus **one** air jump. A third is not a tuning change, it is a different game |
| Height | `JumpPower × 0.85` — noticeably a recovery, not a second full jump |
| Coyote time | 0.12s. Walking off a walkway and jumping spends the **ground** jump |
| Re-press guard | 0.2s, so one input frame cannot spend both |
| Effect | A gold spark ring at the feet. An ability nobody can see reads as a physics glitch |

**The air jump replaces vertical velocity rather than adding to it**, so a jump
pressed while falling fast is worth the same as one pressed at the top of an
arc. Adding would make the ability worthless exactly when it is needed.

---

## 3. Planned: the Fate Tree

Owner-requested: *"the stat tree… should be extensive, need more ideas for what
to let the player upgrade in general."* This is the idea list. Four branches,
because four is enough to force a choice and few enough to read on a phone.

**The constraint that shapes all of it:** Decision **D-8** — Fate never tilts
the odds. Nothing in this tree may change the chance of rolling a world. What
it may change is **which pool you draw from**, what a world is worth once you
are in it, and how long you last there. Any node that reads "+2% Mythic
chance" is out by construction; write "unlocks the Deep pool at Fate 40"
instead.

Spent in **Fate levels**, not points: levelling stays the thing that unlocks,
points stay the score.

### FORTUNE — what the roll can reach
- **Pool access.** The headline node type: at a threshold, Commons stop
  appearing in your draw. This is the answer to "stuck in Commons" that does
  not touch a single weight.
- **Reroll charges.** One banked reroll, recharging over N rolls. Consumable,
  capped, and visible — the anticipation beat survives because you still do not
  know what the reroll lands on.
- **Roll cooldown** reduction, floored well above zero. The cooldown is pacing,
  not friction.
- **Second sight.** Reveals the *rarity band* a fraction of a second earlier.
  Costs nothing mechanically and feels enormous.
- **Fatebreak affinity.** Longer eligibility window for the §12 event.

### ENDURANCE — how long you last out there
- **Expedition duration** +N seconds per rank. The most honest upgrade in the
  tree, and the one the D-7 debate is really about.
- **Stamina pool** and **regeneration**, separately. Two nodes, because a
  player who wants long sprints and one who wants frequent ones are different
  players.
- **Air jumps +1**, gated *high*. It changes how every map reads, so it is an
  endgame node or it is nothing.
- **Fall damage** softening (once falling exists).
- **Return grace.** More seconds between the timer ending and the ejection.

### DISCOVERY — what a world yields
- **Discovery radius / sense.** A pulse that points at the nearest unfound
  thing on the map.
- **Second look.** A chance a discovery yields twice. Loot, not odds — it does
  not touch D-8.
- **Cartography.** The map's layout is revealed on arrival rather than walked
  into. Real value in a kit-assembled map, which is exactly what `ChunkCore`
  makes.
- **Archive slots.** More of what the Discovery Archive can display, which is
  the district's whole reason to exist.
- **First-visit bonus** multiplier (`Rewards.FirstTimeWorld`).

### CRAFT — what your gear becomes
This is the branch that talks to items **without breaking §0**: every node here
changes what the *player* may do with an item, never what the item does.
- **Slots.** A second weapon slot, then a trinket.
- **Reforge attempts.** Rerolling an item's own attribute table — the item
  still owns the table.
- **Salvage yield.** What breaking something down returns.
- **Affinity.** Faster swap between slots; shorter time-to-ready after a sprint.
- **Upkeep.** Durability decay slowed, if durability ever exists.

### Node shapes worth having
Not every node should be "+5%". A tree of percentages is a tree nobody reads.
- **Threshold unlocks** — a pool, a slot, a mechanic. The memorable ones.
- **Ranks** — the +5%s, for the spine between thresholds.
- **Keystones** — one per branch, mutually exclusive, with a real cost. *"Your
  rolls never return Common; your expeditions are 25% shorter."*
- **Respec** — cheap and early. A tree you cannot leave is a tree nobody
  experiments with.

---

## 4. Planned: movement abilities beyond the two

In rough order of how much they change level design, which is the order they
should be considered in:

| Ability | Cost to the rest of the game | Verdict |
|---|---|---|
| **Sprint-jump** (a longer jump out of a sprint) | None. Falls out of what exists | **Do it next.** Free feel, no new input |
| **Dash** (a short ground burst, i-frames later) | Small now, large once combat exists — a dodge is a combat ability wearing movement's clothes | Build the movement half; leave i-frames to the item/combat layer |
| **Ledge grab / mantle** | Medium. Makes authored ledges load-bearing | After the first authored biome is walked |
| **Glide** | Large. Every map's verticality becomes optional | Only as a rare item, never a player baseline |
| **Wall run / climb** | Large. Every wall becomes a surface that must be authored for it | Probably never; it is a different genre |
| **Grapple to a point** | Large, and it is a *content* ability — the map has to declare points | A biome mechanic, not a player one |
| **Mount / vehicle** | Large. Breaks the hub traversal budget on purpose | Hub cosmetic at most |

**The rule for adding any of them:** if the ability changes what a map must
provide, it belongs to the world or to an item, not to the player. Sprint and
double jump pass that test — every map is walkable without them.

---

## 5. Where these would live

Nothing about the split changes as this list is worked through:

- **Rules** → `Core/LocomotionCore.luau` (pure, tested headlessly).
- **Numbers** → `GameConfig.Locomotion` (and never a literal in the controller).
- **Input and instances** → `Controllers/LocomotionController.luau`.
- **Anything with a damage number** → the item's own model and script. Not here.

The tree, when it is built, wants the same shape: `Core/FateTreeCore.luau` for
what a node costs and whether it may be taken, `Content/FateTree/` for the
nodes themselves, and a panel that draws whatever it finds.
