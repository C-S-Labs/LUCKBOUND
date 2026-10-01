# The Ascendant: moveset (v1)

Ethereal Scape's boss, fought in the Sanctum. A temple guardian mid-transfiguration: its ivory-and-gold body is giving
way to sky crystal at the hands, feet, crown and hem. It fights with the **Sanctum Staff** (weapon type **Staff**, `docs/WEAPONS.md`), a long
haft whose head is a crescent of sky crystal around a portal-eye core. It is the boss's Legendary drop.

**Fantasy: a sweeping, gliding duelist.** It's the Winged Sentinel's opposite number, so the two bosses never play
alike:
- The Sentinel **thrusts and dashes in straight lines**.
- The Ascendant **sweeps arcs and steps through portals**. Its reach is long and its danger is lateral: wide crescents
  you jump or roll through, not lines you side-step.
- It never stomps. It glides, circles (StrafeLeft/StrafeRight) and repositions through short portal steps, in keeping
  with the biome's weightless design language (`ROSTER.md`).

**Design rule (boss-moveset-rules): fast but fair.**
- Every attack is clearly telegraphed: a pose change, a glow cue on the crescent and palms, and an audio cue.
- Every attack leaves a real punish window.
- Nothing hits the whole arena, aerial and portal moves land in sword range, and the player deals all the damage
  (no arena hazards to exploit).

Timings are at 30 fps.
- **Tell**: `Tell` marker to `HitStart`, how long you have to react. At least 8 f.
- **Active**: `HitStart` to `HitEnd`, the hitbox is live.
- **Recover**: `RecoverStart` to the end of the action, the punish window. At least 18 f, and 30-60 f for big moves.
  `anim_core.end()` enforces the Tell and Recover minimums on every built action and prints the result.

## Phase 1: The Guardian (ivory cuirass intact), 100-55% HP

| # | Move | Tell | Active | Recover | Counterplay | Notes |
|---|------|------|--------|---------|-------------|-------|
| 1 | **Crescent Reap** | 14 f: staff drawn back to its right at waist height, torso coiled, crescent flares | 5 f, ~200° horizontal arc, 4.5 m reach | **37 f**: blade drags low on its left, torso over-rotated | Roll through it toward its **right** side (the swing's start), or jump it | Bread and butter. **Built:** `P1_CrescentReap`. |
| 2 | **Rising Crescent** | 12 f: staff dipped low behind the right foot | 5 f, rising diagonal | **26 f** | Side-step to its left | Its answer to players who roll in low after a Reap. Never chains from a Reap: there is always the Reap's full 37 f first. |
| 3 | **Portal Step → Thrust** | 16 f: it sinks into a floor portal; a glowing arrival ring shows where it will surface (always within 5 m of the player, never behind a wall) | 6 f butt-first thrust from the ring | **28 f** | Move off the ring. It surfaces facing where you **were** | Its gap-closer. The ring shows for the whole tell. |
| 4 | **Sanctum Lattice** | 18 f: staff planted, both crystal palms raised; three rune rings appear on the floor | 3 crystal pillars erupt at the rings, 8 f | **34 f**: staff stuck in the floor, palms dim | Leave the rings, then punish. It stays still for the whole channel | The biggest P1 opening. The pillars are its own crystal, not a map feature, so it works on any Sanctum chunk. |
| 5 | **Crown Flare** (counter) | 8 f: staff vertical, crown blazes | 26 f counter window | **20 f** if nothing hits it | Don't attack; wait for it to end, then punish | If struck, it answers with a Rising Crescent (its normal 12 f tell). At most once per 15 s. |

**P1 strings.** A string ends on its last move's recovery and never chains into another string.
- **A: Reap → Reap.** A 10 f re-aim between the two; only the second gets the full 37 f recovery. Used only if the
  first missed.
- **B: Portal Step → Reap.** It surfaces, then Reaps with the full 14 f tell.
- It never makes more than 3 committed attacks without a window. After the 3rd it pauses for 1 s: the palms and crown
  dim, a free damage window.

## Transition: P2_Transfiguration (70 f, invulnerable, no damage)
- f1–20: it staggers and sinks to one knee, the staff planted. Cracks of portal light run up from its crystal hands
  and feet.
- f30 (`ArmourBreak`): the ivory cuirass (the `Breakaway` piece) bursts off. It lands only where it's harmless.
- f30–50: the crystal-veined inner torso and its portal core (`VFX_Core`) are revealed, and the crown flares.
- f50–70: it rises and lifts a hand's breadth off the floor. The feet stay in sword range; it isn't flying.
- After it ends (the `P2Start` marker), it stands still for **2 s** before attacking: a free window that rewards
  pushing the phase.

## Phase 2: Ascended (inner body exposed, crystal ascendant), 55-0% HP
It's faster, and every recovery stays at or above the P1 floor. With the cuirass gone it takes **+25% damage**.

| # | Move | Tell | Active | Recover | Counterplay | Notes |
|---|------|------|--------|---------|-------------|-------|
| 1 | **Twin Reap** | 12 f, then 8 f | 5 f + 5 f (R→L, then L→R) | **30 f** after the second | Roll through each arc | The second arc's tell is the staff flipping overhead: readable. |
| 2 | **Portal Chain** | 14 f per step (arrival ring each time) | 3 thrusts, 6 f each | **40 f** after the 3rd (it kneels, core flickers) | Leave each ring | **Main P2 opening.** Every surface is within sword range of the player. |
| 3 | **Starfall Lattice** | 20 f (staff raised skyward, rune rings mark the floor) | 5 pillars in two waves, 8 f each | **36 f** | Leave the rings; there is always a clear lane | Like P1 #4, larger, with a guaranteed safe lane. |
| 4 | **Crescent Wave** | 16 f (crescent charges white) | a 6 m ground-level crescent wave, 10 f travel | **30 f** | Jump it | Its only ranged move, to punish players who stand off. |
| 5 | **Ascension** (below 15% HP, once) | 24 f (lifts, crown and palms go white) | 4 alternating Reaps, 5 f each | **60 f**: collapses to one knee, glow out | Back off during the flurry, then finish it | The "finish it" moment. |

## Fairness rules (every boss, restated)
1. Every attack has a visual tell of at least 8 f **and** an audio cue. No hitbox is live during the tell.
2. Every attack or string ends in at least 18 f of recovery. Portal and aerial moves end grounded, in sword range.
3. No attack covers 360° without a gap (the Reap is ~200°; its start side is always safe), and nothing hits the
   whole arena.
4. At most 3 attacks without a punish window, and at least 0.5 s between strings.
5. Floor marks (arrival rings, rune rings) show for the whole tell, and there is always a reachable safe spot.
6. The player does all the damage. No map dependencies: every effect is the boss's own, so all of it works on the
   base Sanctum chunks.

## Animations
All on the one rig (`TheAscendant.fbx`), in place (the AI moves the root between markers), staff held in
`Weapon_R` with rotation-only keys.

- **Built** (`anims/the_ascendant/`):
  - `Idle_Guard`: 120 f loop, high guard, two breaths and a slow weight shift foot to foot (hips, chest, staff, head).
  - `P1_CrescentReap`: 60 f, full combat markers. In the recovery the off hand lets go of the haft (48-52), changes its
    grip while it is off (52-54) and re-grips for the guard (54-60), so the hand never spins on the haft.
  - `Walk`: `walk_core.build_walk_humanoid(role="boss")`, the staff carried upright via the `post=` hook. It is
    whole-body: bob, sway, hip roll, a counter-rotating chest, a level head and a free left arm swing.
  - `StrafeLeft` / `StrafeRight`: `build_strafe_humanoid`, both directions, staff carried, in a staggered stance. The
    feet never cross, and the free arm moves smoothly and stays clear of the robe.
- **Cloth** (`the_ascendant_cloth.py`): the robe is a skirt of 16 chains × 5 bones, pinned under the belt and
  colliding with both legs and arms; the four back scarves are one 4-bone chain each, colliding with the back, the
  hips, the legs and the arms. The free arm hangs at `arm_out` 0.17 so it clears the robe's hip flare. Robe-vs-leg overlap below the hips (worst frame) went from 176-298 tris on every frame to 0 in Strafe and
  Idle, ≤ 4 in Walk and ≤ 14 in the Reap's deepest lunge.
- **Hands** (`the_ascendant_hands.py`): every finger and thumb has 3 joints, so both hands close round the haft. The
  haft (94 mm across) is thick for the crystal fingers (~155 mm), so a finger wraps about 105°. To wrap further,
  lengthen the fingers or thin the grip.
- The rig is 150 bones: 44 body, 96 cloth, 10 extra finger joints.
- **The shipped FBXs come from the owner's hand-edited `TheAscendant.blend`**, not from `the_ascendant.py`. The owner
  cleaned up the chest and moved the centre crystal by hand, and removed `BreakawayGlow`. Re-running
  `run.py --export` / `--anims` rebuilds the scripted chest and would overwrite that edit. Build the actions with the
  runner, then export them onto the `.blend`'s mesh (as Session 96 did) until the script matches the edit.
- **Known leftovers:** the left upper arm grazes the chest while two-handing the staff low in the recovery (up to 48
  tris, frames 20-58, steady, no jerk). The staff grazes the waist on sweep frame 18 (20 tris). The wrist reaches 82°
  in the lift at frames 46-49.
- **Session 101 additions** (`anims/the_ascendant/`):
  - `P1_CrescentReap` re-authored as a fluid **overhead axe chop**: the staff goes straight up and back, then chops down
    and forward. On the strike frame (f19) the crescent's middle is placed exactly on `HIT_POINT` (the player's torso,
    2.1 m in front of the boss's axis, 1.15 m up; the top of `P1_CrescentReap.py`), so the blade crosses the player.
  - `P1_OrbCast` (ranged bolt) and `P1_SkyCast` (overhead area spell): both fire from the **spell orb** on the staff
    (`VFX_Orb` socket, mesh piece `StaffOrb`). Markers: Tell, VFX_Cast, HitStart (the spell spawns), HitEnd, RecoverStart.
  - `Hit_React` (flinch), `P1_Stagger` (loop, poise broken), `P1_StaggerRecover` (stagger ends, back to guard).
  - The Staff is mostly a **ranged** weapon (orb casts), with the Reap as its close-range option.
- **Rig joints added** (`joints_core.py`, driven procedurally): `Spine` (mid-chest), `{side}LowerArmTwist` (forearm
  roll); the shoulder pads follow the torso more than the arm. 44 body + 96 cloth + 10 finger + 4 orb/joint = 154 bones.
- **To build:**
  - Phase 1: `P1_RisingCrescent`, `P1_PortalStep`, `P1_Lattice`, `P1_CrownFlare`
  - Transition: `P2_Transfiguration`
  - Phase 2: `P2_Idle`, `P2_TwinReap`, `P2_PortalChain`, `P2_StarfallLattice`, `P2_CrescentWave`, `P2_Ascension`,
    `P2_Kneel`
  - Shared: `Death`

**Markers** (Studio reads them with `GetMarkerReachedSignal`):
- `Tell`, `HitStart`, `HitEnd`, `RecoverStart` on every attack.
- Optional: `VFX_Crescent` (crescent flare at the tell's peak), `Footstep`, `ArmourBreak`, `P2Start`.

## VFX plan (Studio)
Palette: portal glow `#8CFFD0` (mint-white) with sky-crystal blue `#7FC8FF`. Gold stays unlit. The `*_Glow` meshes are
the Neon parts. Every cue is the shared framework cue (`ENEMY_FRAMEWORK.md` §5), so players read it the same way on
every boss.

| Cue | Effect | Attachment |
|---|---|---|
| Tell | Mask-slit flash; the crescent's fuller and the palms brighten; AoE moves add floor rune rings | `VFX_Eye`, `VFX_PalmL/R`, staff glow |
| Active | Crescent trail during `HitStart`..`HitEnd` only | `VFX_StaffBase` → `VFX_StaffTip` |
| Recover | Glow dims to 40%; slow crystal motes drift off the hands ("it's open") | glow meshes, `VFX_PalmL/R` |
| Portal step | Floor portal ring at departure and arrival; mint afterimage | root |
| Phase change | Cuirass debris flies off, core flares, crown blazes | `VFX_Core`, `Breakaway` |
| Defeat | Crown shards crack off, then an upward crystal dissolve and a fading portal ring; loot after (~4 s, harmless) | `VFX_Core` |


## Work order 2026-09-30: animation and VFX construction (owner-directed; contract in `docs/BOSS_ANIMATION_VFX.md`)

Source: `docs/design/boss_plans/ASCENDANT_SENTINEL_ANIMATION_VFX_PLAN.md` §4. **Pending input: the owner is pushing an updated Ascendant spec and mesh
with extra rigging and joint properties. Do not start any step that touches the mesh or rig until it lands; reconcile that spec first and update this
order.** Timings below are existing source timings or *proposals*; no combat rebalance.

**0. Guard rails**
- The shipped FBXs come from the hand-edited `TheAscendant.blend` (chest/centre crystal adjusted, `BreakawayGlow` removed). Never run a full
  scripted rebuild/export over it, and never re-add `BreakawayGlow`. Locate the newest authoritative `.blend` (and any `_fixed`), compare dates,
  meshes, rig names and exports, then generate actions separately and transfer them onto the compatible rig.
- Confirm the inner core and `Breakaway` mesh still exist before designing the transition around them. No hood, no halo.
- Do not add dozens of bones for VFX. Plan counts (154 bones: 16 robe chains x 5, 4 scarves x 4) are unverified; audit the real scene.

**1. Audit (deliverable)**: authoritative file, tri/bone counts, which of `Weapon_R`, `VFX_Core`, `VFX_Eye`, `VFX_PalmL/R`, `VFX_Orb`,
`VFX_StaffBase`, `VFX_StaffTip` really exist (the last two are only documented), clipping/wrist reports against the re-authored actions.

**2. Construction to add**
| Item | Work |
|---|---|
| Sockets | Register missing `VFX_StaffBase`/`VFX_StaffTip`; orb socket at orb centre following the staff; verify imported transforms while animating |
| Armour debris | Split/identify harmless chunks of the real `Breakaway` cuirass (no duplicate armour underneath); deterministic cosmetic motion, TTL, restore on reset |
| Crystal shard | One reusable low-poly shard for transition/death; do not rig every crystal |
| FX meshes | Thin ring, tapered crescent, optional bolt shell, crystal pillar (see contract §5) |
| Cloth | Tune follow-through for casts and portal steps; no new giant cape |
| Orb | `StaffOrb` glow driven as phase/tell data, not whole-staff overexposure |
| Actions to build | `P2_Transfiguration` (70 f), `Hit_React`, `Stagger/Recover`, death, plus approved move variants below |

**3. Existing actions: production recipes** (source frames, 1-based)
- `P1_CrescentReap` 60 f: Tell 3, Crescent 14, hit 17-22, recover 23-60. Overhead chop; narrow downward blade ribbon on active frames only.
- `P1_OrbCast` 54 f: Tell 3, Cast 12, hit/spawn 18-22, recover 24-54. One mint-blue bolt from `VFX_Orb`, tiny release ring.
- `P1_SkyCast` 66 f: Tell 3, Cast 20, release 34-40, recover 42-66. Maps to **one** named ground-spell recipe in encounter data; never lattice, starfall and Crown Flare together.
- **Spawn window is not projectile lifetime.** `HitEnd` f22 ends the release window; the bolt needs its own authoritative lifetime/range/collision and must not become an unmarked lingering hazard.
- OrbCast cue sheet: f3 `Tell`, f12 `VFX_Cast`, f16 proposed `Commit`, f18 `HitStart` (spawn bolt from live socket), f22 `HitEnd`, f24 `RecoverStart` (dim, no second cast), f54 end.

**4. Prototypes (do these first, end to end):** `P1_OrbCast` + overhead `P1_CrescentReap`. They prove staff sockets, skinning, grips, cast origin and timing.

**5. Move variants (older melee-first sheet; reconcile before enabling, none confirmed built)**
Rising Crescent 12/5/26; Portal Step -> Thrust 16/6/28; Sanctum Lattice 18/8/34 (generic SkyCast cannot substitute); Crown Flare 8/26 counter/20;
Twin Reap P2 12 then 8 / 5+5 / 30 (decide arcs vs overhead); Portal Chain P2 14 per arrival / 3x6 f / 40; Starfall Lattice P2 20 / 2x8 f / 36;
Crescent Wave P2 16/10/30; Ascension finisher: replace four Reaps with **two strokes, opening, two strokes, 60 f kneel** (three-attack rule).
Portal destinations validated against real collision/navigation, each with a full warning and reachable escape. Counterplay (jump/roll) verified against actual player capability.

**6. Transfiguration cue sheet** (70 f, then 60 f vulnerable; no damage; keeps 55% boundary and +25% damage without cuirass): f1-20 knee, veins rise; f21-29 core
charges; f30 `ArmourBreak` shards, no fire/smoke; f30-50 crystal torso revealed; f50-70 rise into slight hover in sword range; f70 `P2Start`, no portal escape or cast.

**7. Defeat (~4 s):** cancel casts/projectiles per encounter cleanup, staff lowers, crown sheds a few harmless shards, robe settles, one thin portal ring, motes rise. Preserve the edited silhouette. No implosion, no floor-wide hazard.

**8. Conflicts to resolve (record decisions here):** older horizontal Reap vs current overhead chop (keep the chop; any horizontal move gets a new approved id);
melee duelist vs caster-first roster (define one roster, enable nothing automatically); "only ranged move" prose is stale (OrbCast/SkyCast exist); table timing vs cast clips; edited `.blend` vs generator.

**9. VFX recipes:** `ASCENDANT_MOVESET.md` VFX plan above stays; additionally palette `#8CFFD0` / `#7FC8FF` checked against Ethereal Scape's bright cloud lighting; aggregate ~50 live particles normal, ~110 transition.

**10. Acceptance (boss-specific, on top of contract §8):** edited chest/crystal intact and `BreakawayGlow` absent; cast effects start at the moving `VFX_Orb`; armour breaks remove the correct parts once and restore on reset.
