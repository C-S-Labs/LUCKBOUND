# LUCKBOUND — Player Abilities & Upgrades

**Status:** §1–§2.6 are built: our own character controller, one movement
state machine (`Core/LocomotionCore.luau`), stamina, jump, roll and lock-on
(2026-09-28). §6 is the contract weapons
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

## 1. Built: our own character controller

Owner-directed 2026-09-28: **no default Roblox movement.** The Humanoid's state
machine is off (`EvaluateStateMachine = false`) and a `ControllerManager` with a
ground and an air controller moves the character. `LocomotionController` sets its
direction, speed and facing every frame and launches jumps itself. The stock
Animate script is off too: the same stock animation assets are played by the
controller from our speed and mode, until LUCKBOUND has its own animations.

**No turning delay, in any mode** (owner). The facing is written to the root directly every frame
rather than turned by the controller's torque, which lagged fast camera swings and put rolls off-aim.
The per-profile `TurnRate` is gone.

**Only the root collides.** Every other body part has collisions off (re-applied every frame), so a
clip turning the torso through the floor can't push the physics. That push was a camera shake during rolls.

What the Humanoid still owns: health, death (it gets its state machine back on
death), the name plate. `Humanoid.WalkSpeed` survives only as an outside
multiplier, so the loading screen's hold (0) and the `/speed` dev command keep
working without knowing about the controller.

**One state machine.** `LocomotionCore.mode()` derives exactly one mode from the
state, and never stores it, so it cannot disagree with the timers:

| Mode | Meaning |
|---|---|
| `GROUND` | On the floor, walking or sprinting (sprint is a flag, not a mode) |
| `AIR` | Off the floor |
| `ROLL` | A roll or backstep, its recovery included |
| `LOCKED` | A weapon move holds movement (§6) |

## 2. Built: two profiles, one stamina bar

**Profiles.** The hub is for getting around, an expedition is for fighting: same
rules, different weight. The controller picks EXPEDITION while the character
stands inside a loaded expedition stage, HUB otherwise.

| | Hub | Expedition |
|---|---|---|
| Walk / sprint | 32 / ~50 studs/s | ~22 / ~34 studs/s |
| Speed-up / slow-down | 0.08s / 0.05s | 0.12s / 0.08s |
| Air control | 0.8 | 0.45 |
| Stamina | **unlimited**: nothing costs anything | sprint 14/s, jump 10, roll 22 |

Ramps are short in both profiles. The first Studio walk felt like sliding on
ice with longer ones, so weight comes from turning and costs, never from
sliding. Stamina is unlimited in the hub, and only there (owner, 2026-09-28).

The owner asked for a middle ground between the hub's lightness and a Souls
game's weight: that is the expedition column.

**Stamina: a challenge, not a punishment.** One bar (100) for sprint, jump and
roll now, and for attacks and blocks when weapons land.

- Any action can **start** on any stamina above zero; its cost may empty the bar.
- Refill: 30/s after a 0.45s pause from the last spend, so empty to full is ~3.3s.
- Emptying the bar costs a longer 1.1s breather before refill starts.
- A sprint-jump keeps sprint speed without paying for the airtime.
- Holding sprint while standing still costs nothing.

**Upgrades later.** `LocomotionCore.tuning(config, profile, upgrades)` takes a
multiplier per field (for example `{ StaminaMax = 1.2 }`), so the Fate Tree's
stamina and movement nodes will plug in without touching the rules. Health,
damage and attack speed belong to the weapon and combat layers.

**The bars** (`client/UI/Vitals.luau`): health above stamina, **always on screen**
(owner, 2026-09-28). Health reads the Humanoid, in a rose fill (`UITheme.AccentHealth`).
Each bar is house style: a panel-coloured track with
the theme stroke, fully rounded, and a gold fill under the panel gradient that
turns amber when low. A pale lag bar behind the fill holds the old value for a
beat and then drains, so a spend reads as a chunk taken out. **Charge** will be
another row from the same `bar` function, but
only while an Epic or Legendary weapon with a charge is equipped (`WEAPONS.md` §2,
"Charge").

## 2.5 Built: jump, roll and backstep

**Jump.** One jump: **the double jump is gone** (owner, 2026-09-28). Height is
unchanged from the old ground jump (50 studs/s launch), so every gap the kits were
built around stays crossable. It has a 0.12s coyote window after walking off an
edge, and a 0.12s buffer so a press just before landing fires on landing.

**Roll** (Q, B on a gamepad, a Roll button on touch):

| | Roll (a direction held) | Backstep (no direction) |
|---|---|---|
| Movement | **18 studs** over 0.65s; speed follows the clip (gentle start, full through the tumble, easing out), the held direction; the clip blends out over 0.22s into standing or running (steering was tried and removed at the owner's call) | 26 studs/s for 0.32s ≈ 8 studs, away from facing |
| Cost | the profile's roll cost | 60% of it |
| Recovery | 0.12s standstill after | same |
| Invulnerable window | 0.05–0.44s in | 0.02–0.16s in |

- A roll is a commitment: no jump, sprint or second roll until it recovers.
- A roll pressed in the last 0.2s is buffered, so chained rolls come out clean without
  mashing.
- Ground only.
- **Four directions, relative to facing** (owner, 2026-09-28). With the shoulder
  camera or a lock-on, the character **keeps facing forward** and rolls the way you
  pressed: front, back, left or right, each with its own animation. Without either,
  it turns to roll the way it is going, so the roll is always "front".
- **The look:** a **discrete burst of wind** where the move starts (owner, replacing
  afterimages): five short streaks of air left behind, stretching out and fading
  within 0.32s. The ground ring was removed after the owner's walk ("too much"). There's also a 3° camera widen and, for a direction with no
  clip yet, a procedural tumble (forward, backward, or over the shoulder to either
  side). Settings: `RollWind*`, `RollTumble*`, `RollFovKickDegrees`.
- **Air dash (the jump dash, owner 2026-09-28):** roll pressed **in the air** gives a
  short horizontal burst (52 studs/s for 0.22s ≈ 11.5 studs):
  - it goes the held way, or forward with no direction held;
  - it holds height, so there is no arc;
  - once per airtime, refilled on landing;
  - free in the hub, 18 stamina in an expedition;
  - it has the same four-direction rule and wind burst as the roll, leans into its
    direction, and has **no** invulnerable window.
  Clips: `AirDashForward/Backward/Left/Right`.
- **The invulnerable window is declared, not applied.** `LocomotionCore.isInvulnerable`
  answers it, and the combat layer will call it when it resolves hits (§7.6).
  Nothing is invulnerable today.

## 2.7 Built: how the body moves (`CharacterAnimator`, `AnimationCore`)

Presentation only: it never changes where or how fast a character goes.

- **Blending, not switching.** Idle, walk and run play at once, weighted by speed,
  so there is no pop between them. Playback rate follows real speed, so the feet
  don't slide.
- **Directional movement.** While facing is held (shoulder camera, lock-on),
  moving sideways or backward reads as a strafe or a backpedal. With a full set of
  four directional clips for a gait, they blend by direction. Until then, the
  procedural fallback runs:
  - the legs turn toward the movement (up to 65°) while the upper body counter-turns;
  - moving backward plays the forward clip in reverse.
- **Lean** into acceleration (and further while sprinting), back when braking, and
  **bank** into turns in proportion to speed.
- **Head look** toward the lock-on target or where the camera looks. It is clamped,
  and never snaps round to something behind.
- **Landings:** a soft or hard dip by fall speed. A hard landing (a real drop, over
  72 studs/s) also slows movement for a beat: 0.3s in an expedition, 0.12s in the
  hub.
- **Turn in place:** standing and turning fast steps the feet.
- **Sounds:** the Roblox client's built-in running loop (its rate follows speed),
  jump and land. The default sound script can't run with the state machine off.
- **One limit:** the procedural layer (legs, lean, head, dip, tumble) bends joints
  locally, so **other players see only the clips**. Filling the slots below is what
  makes the polish visible to everyone.

### Adding real animations: where and how

Everything goes in **one file, `src/shared/Content/Animations/Player.luau`**: one slot
per thing the body does. An empty slot (`""`) uses the fallback; paste an id and
that slot switches to it. No code changes.

1. **Author** each clip on an **R15** rig:
   - **In Studio:** the Animation Editor, or Moon Animator. Get a rig from
     Avatar → Rig Builder → R15, or use your own character.
   - **Or in Blender**, on an R15-matching armature. Export FBX and import it in
     the Animation Editor. The repo's enemy pipeline (`assets/source/enemies/_framework/`)
     can be extended with a player rig if you want these generated like the enemy
     clips.
2. **Follow the slot rules:**
   - **In place:** no root motion. The controller moves the character; the clip
     only moves the body.
   - **Loops** (Idle, Walk*/Run*, Sprint, Rise, Fall): seamless. Author walk
     clips at about 11 studs/s of foot travel, run at about 24 and sprint at about 30
     (`CharacterAnimation.*ClipSpeed`). Playback is scaled to real speed from those.
   - **Directions are relative to facing.** `RunLeft` is running left while facing
     forward. **All four of a gait** (Walk or Run) must be filled before that gait
     switches over; each roll direction switches on its own.
   - **One-shots** (JumpStart, Land*, Roll*, Backstep, Turn*): any length. Rolls and
     the backstep are stretched to the move's real duration (0.5s / 0.32s).
   - Priority is set by code; the editor's setting doesn't matter.
3. **Publish** each clip to Roblox under the **group that owns the place** (ids are
   account/group-scoped; see `PARTNER_SETUP.md`). Copy the id.
4. **Paste** it as `"rbxassetid://<id>"` into its slot. Sync and press Play. The
   boot check rejects a typo'd slot name or a malformed id.

The most valuable first clips are `RollForward/Backward/Left/Right` and
`RunForward/Backward/Left/Right`. They replace the procedural parts other players
can't see.

## 2.55 Built: the shoulder camera (our shift lock)

**Left Ctrl** toggles it. The mouse locks to the centre, the camera shifts 1.75
studs over the right shoulder, and the character faces where the camera looks.
Roblox's own shift lock can't work here: it lives in the PlayerModule (absent in
this place) and turns the character through the Humanoid, which our controller now
does itself. It isn't on Shift, which is sprint. Lock-on takes the camera over while
a lock is held.

## 2.6 Built: lock-on (optional)

The game plays fully without it. Middle mouse, R3, or a Lock button on touch
takes the best target in view; press again to release.

- **Targets:** anything tagged `Constants.NAMES.LOCK_ON_TAG`. The **spawner** adds
  the tag (the `/showboss` preview does), so no enemy asset is edited. The aim point
  is the target's bounding-box centre, measured once at lock time.
- **Choice:** the target nearest the camera's look beats the one merely nearest the
  player (`LockOnCore.pick`). Range 90 studs, within 60° of the camera's look, in sight.
- **Drops:** past 120 studs, out of sight for 1.5s, or the target is gone.
- **Letting go eases back:** the view blends from the lock's framing back to the
  normal (or shoulder) camera over 0.4s instead of snapping (owner, 2026-09-28).
- **Camera:** behind and over the right shoulder (11 studs back, 2.4 right), looking
  past the player toward the target. The aim is capped 9 studs above the player, so
  a tall boss never pulls the camera into the sky. Walls pull the camera in, and
  smoothing is frame-rate independent.
- **Movement while locked:** the character strafes facing the target. Sprinting
  turns back to face the run, as in Souls, and a roll goes the held direction.
- **Marker:** a small gold diamond on the aim point.
- **Switching targets:** while locked, flick the mouse sideways (60px within
  0.25s) or the right stick past 0.7, or tap **Next** on touch. The lock moves to
  the **nearest target on that side** as the camera sees it: one step, never across
  the room. If there's nothing that way, the lock stays put. The stick must return
  to rest before the next flick, and switches are at least 0.3s apart. The locked
  camera ignores the mouse and right stick, so neither gesture is taken from
  anything else (`LockOnCore.switch`).
- **Testing without enemies:** `/dummies [count]` puts plain tagged pillars in an arc
  in front of you, and `/dummies 0` clears them.

All numbers: `GameConfig.Locomotion` and `GameConfig.LockOn`.

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
| **Sprint-jump** (a longer jump out of a sprint) | None. Falls out of what exists | Sprint speed carries through a jump; no separate boost |
| **Dodge** (a short ground burst, i-frames later) | Small now, large once combat exists — a dodge is a combat ability wearing movement's clothes | **Built as the roll** (§2.5); the i-frame window is declared, the combat layer applies it |
| **Ledge grab / mantle** | Medium. Makes authored ledges load-bearing | After the first authored biome is walked |
| **Glide** | Large. Every map's verticality becomes optional | Only as a rare item, never a player baseline |
| **Wall run / climb** | Large. Every wall becomes a surface that must be authored for it | Probably never; it is a different genre |
| **Grapple to a point** | Large, and it is a *content* ability — the map has to declare points | A biome mechanic, not a player one |
| **Mount / vehicle** | Large. Breaks the hub traversal budget on purpose | Hub cosmetic at most |

**The rule for adding any of them:** if the ability changes what a map must
provide, it belongs to the world or to an item, not to the player. Sprint, the
jump and the roll pass that test: every map is walkable without them.

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

1. **It reads the mode.** `LocomotionController.mode()` gives GROUND, AIR,
   ROLL or LOCKED, so a type's base moveset can have a grounded swing, an air
   swing and a roll attack without inventing its own "am I in the air" check.
2. **It locks movement for its own length.** `LocomotionController.lock(spec)`:

   | Field | Default | Use |
   |---|---|---|
   | `DurationSeconds` | 0 | the move's windup + active + recovery; **clamped to `MaxLockSeconds` (2.5s)** so a forgotten unlock still hands control back |
   | `SpeedMultiplier` | 0 | 0 roots (a Greatsword overhead), 0.4 lets a Dagger flurry drift, 1 leaves speed alone |
   | `AllowJump` / `AllowRoll` / `AllowSprint` | false | what the move lets the player cancel into |
   | `Source` | — | the move id, for the dev panel |

   A new lock replaces the old one (a combo is one move after another, never
   two at once). `unlock()` ends it early when the move is cancelled.

**Cancels are the weapon's decision, expressed as data.** A move that lists
`AllowRoll = true` can be roll-cancelled; one that does not is a commitment.
That is where weapon types get their feel: light weapons allow cancels, heavy
ones root and commit. The timing windows themselves come from the animation
markers (`ENEMY_AI.md` §4), not from here.

### 6.1 Weapon stances: how holding a weapon changes the body (design, owner question 2026-09-28)

A sword, a greatsword and bare hands should move differently. The framework handles this as **layers**, so
no weapon needs a second movement system:

- **Legs and locomotion stay shared.** The run, strafe, rolls, jump and landings are the same for everyone.
  They are the Movement layer.
- **A weapon adds a STANCE:** looping **upper-body-only** clips (arms, and a little torso) at the **Action**
  priority: a grip for idle, one for running, one for sprinting. Roblox blends per joint, so the stance takes
  the arms while the legs keep running underneath. A greatsword's two-handed carry and a dagger's low guard
  are just different stance clips.
- **Whole-body moves override the stance.** Rolls, backstep and air dash sit at **Action2** (already set), so
  the body rolls and then settles back into the grip.
- **Attacks sit on top** (Action3/4), from the weapon's moveset (`ENEMY_AI.md` §4.1).
- **A stance may also override whole slots** when a weapon changes the gait (a greatsword's heavier `RunForward`,
  an idle with the blade planted). Same slot names, looked up in the stance first.
- **Weight on movement** goes through the existing weapon hook: a stance can carry a small speed multiplier,
  applied like `lock`'s `SpeedMultiplier`, so the numbers stay on the weapon (`PLAYER_ABILITIES.md` §0).
- **Unarmed is simply no stance:** what exists today.

As data: one file per weapon TYPE, `Content/Animations/Stances/<TYPE>.luau` (Sword, Greatsword, Dagger,
Hammer, Staff, Bow, Gauntlets), holding stance clip slots and optional slot overrides. Legendary or Mythic
weapons with unique movesets may carry their own. The generator can author the stance clips like the rest.

**When:** with items and equipping (`DEVELOPMENT_PLAN.md`: items before combat). The priority ladder is already
in place so nothing built now has to move.

**What stays out of this layer, for good:** damage, hitboxes, applying i-frames, lunges
that deal damage, knockback. A lunge is a weapon move that locks with
`SpeedMultiplier` and applies its own push through the combat layer when it
opens (build spec §7.6).
