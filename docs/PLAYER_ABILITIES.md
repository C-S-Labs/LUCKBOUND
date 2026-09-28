# LUCKBOUND — Player Abilities & Upgrades

**Status:** §1, §2 and §2.5 are built, on one movement state machine
(`Core/LocomotionCore.luau`, rebuilt 2026-09-28). §6 is the contract weapons
will build against; its hooks exist and nothing calls them yet. §3 and §4 are
**planning**: owner-requested ideas, not commitments.

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

How weapon moves are shaped, including unique Legendary movesets, is `ENEMY_AI.md` §4.1.

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

## 2.5 Built: the state machine, sprint-jump and dash

**One state machine.** `LocomotionCore.mode()` derives exactly one mode from the
state, and never stores it, so it cannot disagree with the timers:

| Mode | Meaning |
|---|---|
| `GROUND` | On the floor, walking or sprinting (sprint is a flag, not a mode) |
| `AIR` | Off the floor: jumping, falling, sprint-jump carry |
| `DASH` | A dash is in flight |
| `LOCKED` | A weapon move holds movement (§6) |

**Sprint-jump.** A ground jump taken while sprinting launches at `JumpPower ×
1.08` and keeps `sprint speed × 1.12` until landing: a longer jump, no new input.
Capped small by a test, because every gap in every kit must stay crossable
without it.

**Dash**, the movement half only (§4's verdict):

| | |
|---|---|
| Input | Q, B on a gamepad, an on-screen Dash button on touch |
| Burst | 95 studs/s for 0.18s ≈ 17 studs, horizontal only, the move direction (facing if still) |
| Cost | 20 stamina from the sprint bar (five from full); refill pauses 0.5s after |
| Cooldown | 0.7s start to start |
| In the air | Not allowed (`AirDashes = 0`). Raising it extends every gap, so it is a feel test, not a free change |
| Cancel | Jumping ends a dash early, so a dash off a ledge can be saved |
| I-frames | **None here.** The combat layer reads `mode() == "DASH"` and decides |

All numbers are in `GameConfig.Locomotion`.

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
| **Sprint-jump** (a longer jump out of a sprint) | None. Falls out of what exists | **Built** (§2.5) |
| **Dash** (a short ground burst, i-frames later) | Small now, large once combat exists — a dodge is a combat ability wearing movement's clothes | **Movement half built** (§2.5); i-frames stay with the combat layer |
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

---

## 6. How fighting drives movement (the weapon contract)

Weapons fight; the player moves (§0). A weapon move never writes a WalkSpeed or
a velocity itself. It talks to movement through two things only:

1. **It reads the mode.** `LocomotionController.mode()` gives GROUND, AIR, DASH
   or LOCKED, so a type's base moveset can have a grounded swing, an air swing
   and a dash attack without inventing its own "am I in the air" check.
2. **It locks movement for its own length.** `LocomotionController.lock(spec)`:

   | Field | Default | Use |
   |---|---|---|
   | `DurationSeconds` | 0 | the move's windup + active + recovery; **clamped to `MaxLockSeconds` (2.5s)** so a forgotten unlock still hands control back |
   | `SpeedMultiplier` | 0 | 0 roots (a Greatsword overhead), 0.4 lets a Dagger flurry drift, 1 leaves speed alone |
   | `AllowJump` / `AllowDash` / `AllowSprint` | false | what the move lets the player cancel into |
   | `Source` | — | the move id, for the dev panel |

   A new lock replaces the old one (a combo is one move after another, never
   two at once). `unlock()` ends it early when the move is cancelled.

**Cancels are the weapon's decision, expressed as data.** A move that lists
`AllowDash = true` can be dodge-cancelled; one that does not is a commitment.
That is where weapon types get their feel: light weapons allow cancels, heavy
ones root and commit. The timing windows themselves come from the animation
markers (`ENEMY_AI.md` §4), not from here.

**What stays out of this layer, for good:** damage, hitboxes, i-frames, lunges
that deal damage, knockback. A lunge is a weapon move that locks with
`SpeedMultiplier` and applies its own push through the combat layer when it
opens (build spec §7.6).
