# Player Animation Brief

**What this is:** the spec for every hand-made player animation, one row per slot in
`src/shared/Content/Animations/Player.luau`. Author against it, try each clip live
with `/animslot`, then paste the id into the content file. The system that plays
these is `PLAYER_ABILITIES.md` §2.7; this file is only what to make.

**Rig:** R15. **Style:** the movement's own brief. The hub is light and quick, an
expedition is weightier but never sluggish (a middle ground between the hub and a
Souls game). Readable at a distance: big, clear silhouettes over subtle detail.

---

## 1. Rules for every clip

- **In place.** No root motion. The code moves the character; the clip only moves
  the body. A clip that drifts will fight the controller.
- **Directions are relative to facing.** `RunLeft` = running to the left while the
  chest faces forward (the shoulder-camera and lock-on case).
- **Loops loop seamlessly:** first frame = last frame.
- **One-shots start and end near the idle pose**, so they blend in and out cleanly.
- **Speeds.** Loops are scaled to the real speed from the speed they were authored at.
  Author the feet to cover the ground at these rates, and nothing will slide:

  | Gait | Authored speed (studs/s) | Config |
  |---|---|---|
  | Walk | ~11 | `CharacterAnimation.WalkClipSpeed` |
  | Run | ~24 | `RunClipSpeed` |
  | Sprint | ~30 | `SprintClipSpeed` |

  If a finished clip covers ground at a different rate, change the config number
  instead of re-animating.
- **Priority is set by code.** The Animation Editor's priority setting is ignored.
- **Publish under the group that owns the place** (`PARTNER_SETUP.md`), or the id
  won't load for anyone else.

## 2. Make them in this order

Each clip in this order replaces a procedural stand-in that **other players can't
see**, so each one makes the game look better for everyone, not just you.

| # | Slot(s) | Type | Length | What it must read as |
|---|---|---|---|---|
| 1 | `RollForward` | one-shot | any (stretched to 0.5s) | A committed shoulder roll: gather low, tuck, roll over one shoulder, come up already moving. Ends upright and balanced, ready to run |
| 2 | `RollLeft`, `RollRight` | one-shot | any (stretched to 0.5s) | A sideways evasive roll or dive-roll. Keep the chest facing forward (the lock-on case); the body goes sideways. Mirror images of each other |
| 3 | `RollBackward` | one-shot | any (stretched to 0.5s) | A backward roll that ends facing forward, not a backflip. Low and quick |
| 4 | `RunForward` | loop | ~0.7–0.8s cycle | The main on-foot gait in both profiles. Athletic, forward-driven, arms countering the legs. This is what players see most |
| 5 | `RunLeft`, `RunRight`, `RunBackward` | loop | match `RunForward` | Side-step or crossover runs, and a backpedal. Chest forward, head level. **All four Run slots must be filled** before directional running switches on |
| 6 | `Idle` | loop | 3–5s | Breathing, weight on one leg, a small look around. Alive, not restless |
| 7 | `Backstep` | one-shot | any (stretched to 0.32s) | A quick hop back, facing forward, guard up. Short and crisp |
| 8 | `JumpStart` | one-shot | ~0.15–0.25s | The push-off: a crouch into extension. Short, because the jump launches at once |
| 9 | `Rise`, `Fall` | loop | ~0.5–1s | Rising: legs tucked, arms up. Falling: legs reaching down, arms out for balance |
| 10 | `LandSoft`, `LandHard` | one-shot | 0.2s / 0.4s | Soft: a knee-bend absorb. Hard: a deep crouch, one hand near the floor, then rise. The code also dips the body, so keep the clip's own drop modest |
| 11 | `Sprint` | loop | ~0.6s cycle | Longer stride, stronger lean and arm drive than Run. Forward only |
| 12 | `Walk*` (all four) | loop | ~1s cycle | Slow movement: a half-pushed stick or a weapon's crawl. Least visible, so last |
| 13 | `TurnLeft`, `TurnRight` | one-shot | ~0.3s | A step-and-pivot when turning on the spot |
| 14 | `AirDashForward/Backward/Left/Right` | one-shot | any (stretched to 0.2s) | A mid-air burst the given way, relative to facing: the body snaps into a streamlined lean, legs trailing, then opens back up to fall. Chest stays forward on the side and back dashes |

**Diagonals come free.** Four roll clips cover all eight directions: a roll pressed
north-east plays `RollForward` with the body turned 45° toward the true direction
(`AnimationCore.rollYaw`). The same applies to the air dash. Don't author diagonal
clips.

## 3. What the code already adds on top (don't animate these in)

These layers bend the joints after the clip plays, so building them into the clip
doubles them up:

- **Lean** into acceleration and turns (up to 9° pitch, 11° bank), plus 5° extra when sprinting.
- **Head look** toward the lock-on target or camera (up to 55° yaw, 30° pitch). Keep the head fairly neutral.
- **Landing dip** (0.35 studs soft, 1.0 hard).
- **Strafe leg-turn** (only while a gait's four directional clips are missing).

The roll tumble, the backstep hop and the air-dash lean only run for a slot with no clip. As soon as a
roll direction has a clip, its tumble stops.

## 4. The loop: author, try, keep

1. Author the clip and **publish** it to the group. Copy the numeric id.
2. In Play: **`/animslot RollForward 1234567890`**. It swaps in live with no restart.
   `/animslot` with no arguments lists every slot and where it comes from (a clip,
   a live override, or the fallback). `/animslot RollForward ""` undoes the override.
3. Happy with it? Paste `"rbxassetid://1234567890"` into that slot in
   `Content/Animations/Player.luau`. Live overrides are lost on rejoin; the file is
   what ships.
4. The boot check rejects a misspelled slot or a malformed id.
