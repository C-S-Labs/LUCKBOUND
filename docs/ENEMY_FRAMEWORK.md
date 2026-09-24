# Enemy Framework: how every enemy, miniboss and boss is built, in every biome

Sky Citadel is the first world with enemies, and it is the worked example. Every later biome (Verdant Valley, Emberfall,
Ethereal Scape, Astral Reach, ...) follows the **same order, the same code and the same rules**. What changes per biome is data:
a roster manifest, a palette, the model scripts and the action files.

It mirrors the world-kit approach: shared code in a `_framework/` folder, and a biome folder that only holds
biome content.

```
assets/source/enemies/
  _framework/                 shared by every biome; never copied
    run.py                    the one headless entry point (validate / render / export / anims / preview / save)
    enemy_kit.py              procedural modelling helpers + assemble() (pieces, glow split, rig, vertex groups)
    humanoid.py               R15-named humanoid body + rig generator (fingers optional)
    pose_fix.py               grip / finger-wrap / off-hand IK / arm-clearance / grounding solvers
    anim_core.py              action builder, combat markers + fairness checks, direction-safe posing helpers
    validate.py               tri budget, rig and tier rules, floor check, overlap report
    render.py / preview.py    standard review renders (auto-framed) / per-key action frames
    export.py                 FBX for Roblox (static rig + one file per action)
  <biome>/                    one folder per biome
    manifest.py               THE roster: id -> script, tier, body, role, extras, moveset
    <enemy>.py                model scripts (one per enemy; bosses may split files)
    anims/<enemy_id>/<Action>.py   one file per action: key poses + timing + markers only
    <BOSS>_MOVESET.md         one per miniboss/boss
    ROSTER.md                 the biome's human-readable roster + build status
assets/export/enemies/<biome>/     <Name>.fbx, <Name>_<Action>.fbx  (what Studio imports)
```

Commands (Blender 4.x/5.x, always headless: the live Blender MCP session crashes on rigs):
```
blender -b --factory-startup --python assets/source/enemies/_framework/run.py -- <biome> <enemy_id> --validate --render
blender -b --factory-startup --python assets/source/enemies/_framework/run.py -- <biome> <enemy_id> --export --anims all --preview
```

---

## 1. The build order (same for every tier)

| Step | What | Gate before moving on |
|---|---|---|
| 1 | **Roster.** Add the enemy to `<biome>/manifest.py` + `ROSTER.md`: role, tier, one-line fantasy, palette | Owner OK on the roster |
| 2 | **Body.** Model script with `enemy_kit` / `humanoid`. Final silhouette, materials, glow split, break chunks (if it sheds) | `--validate` PASS; owner OK on renders |
| 3 | **Rig.** R15 bone names for humanoids; sockets (`Weapon_R`, `Shield_L`, `VFX_*`); fingers for miniboss/boss | validate: R15 + fingers |
| 4 | **Weapon** (unique weapon for bosses; designed **after** the body is final) | tri budget, no clipping |
| 5 | **Poses.** Idle/guard/stance poses via `pose_fix` (true grip, no clipping, grounded) | clip report clean; owner OK |
| 6 | **Moveset.** `<NAME>_MOVESET.md` from the template (§4): tells, active, recovery, combos, phase changes | owner OK |
| 7 | **Actions.** One `anims/<id>/<Action>.py` per move, with combat markers | `anim_core.end()` prints OK (fairness rules) |
| 8 | **Export + Studio.** `--export --anims all`; import, wire the `EnemyDef` (§6), then the VFX (§5) | playtest |

Basics usually skip steps 4 and 6 (their moves come from shared **archetypes**, §3) and need only 3-5 actions.

## 2. Tiers: what "done" means

| | Basic | Miniboss | Boss |
|---|---|---|---|
| Tris | < 10k per mesh (usually one body + one glow) | < 10k per mesh | < 10k **per piece**; split into as many pieces as needed |
| Detail | clean silhouette, 1 readable gimmick | noticeably more than a basic: trims, layered plates | **dramatically** more: layered armour, flow lines, inner body for phase 2 |
| Rig | R15 or simple creature chain | R15 + finger bones | R15 + finger bones + extra chains (wings, capes, jaws) |
| Weapon | socket only (shared weapon meshes) | socket or simple unique | unique weapon, own bones (opening parts, halo, etc.) |
| Phases | 1 | 1-2 (armour shed optional) | 2+, with a transition action (break chunks `Break_*`) |
| Moveset | archetype (3-4 moves) | own sheet, 4-5 moves | own sheet, 5-7 moves per phase + combos |
| Actions | Idle, Move, 1-3 attacks, Hit, Death | + stance/phase actions | full list from the moveset sheet |

Owner rules that apply to every tier:
- **Materials:** smooth, glossy materials (no mottled noise), in the biome's colours.
- **No clipping:** nothing clips, in any pose or action.
- **Looks match speed:** how aggressive an enemy looks matches how fast it attacks.
- **Flyers:** they must come into sword range. The player's weapon is the only damage source (no arena tools).

## 3. Archetypes (shared behaviour; Studio code is written once)
Every enemy's `role` maps to one server behaviour module. A new biome **re-skins archetypes** instead of writing new AI.

| role | Behaviour | Punish window |
|---|---|---|
| `melee_guard` | walk up, 1-2 hit combo | 20 f after the combo |
| `brute` | slow, heavy overhead / charge | long recovery (30 f+), stuck weapon |
| `diver` | fly, telegraphed dive, lands and stalks | grounded 36 f after the dive |
| `hover_melee` | hovers at chest height, swing / burst | 24 f after the burst |
| `hover_ranged` / `ranged_thrower` | keeps distance, shoots, then **reloads** | the reload |
| `caster` | channels AoE with ground marks | channelling = rooted |
| `swarm` | several weak units, leap bites | 16 f after landing |
| `ambusher` | hidden, springs out, retreats | 28 f after the strike |
| `miniboss` / `boss` | driven by its moveset sheet | per sheet |

## 4. Moveset rules (every miniboss and boss; basics inherit these through archetypes)
The template and worked example is `assets/source/enemies/sky_citadel/WS_MOVESET.md`.
- **Tell:** every attack has a tell of at least 8 f **and** an audio cue. Its VFX *is* the warning.
- **Recovery:** every attack or combo ends in at least 18 f of recovery (the punish window). Big moves get 30-60 f.
- **Rhythm:** at most 3 attacks without a window, and at least 0.5 s between strings.
- **Nothing unavoidable:** there's always a reachable safe spot. Aerial moves land in sword range, and AoE marks show for the whole tell.
- **No map dependencies:** attacks must work on the **base chunk kit**, so they never rely on scenario-only features.
  - Example: the Sentinel's lightning is its own *Aether Fork*, not the Stormhawk scenario's strikes.
- **Enforcement:** `anim_core.end()` checks the markers against these rules. An attack action without `Tell`, `HitStart`, `HitEnd` and `RecoverStart` fails.

Combat markers (Studio reads these through `AnimationTrack:GetMarkerReachedSignal`):
- `Tell`: wind-up starts (VFX and audio on)
- `HitStart` / `HitEnd`: the hitbox is live between them
- `RecoverStart`: the punish window opens (glow dims)
- Optional triggers: `Impact`, `Footstep`, `WingBeat`, `VFX_<name>`

### Animation quality (enforced by anim_core; the actions ARE the Studio animations)
- **Solved in-betweens:** build attacks with `param_keys`. Each key is a set of pose *parameters* (grip point, weapon
  direction, lean, wing angles), and every 2nd frame is re-solved from the eased parameters. In-betweens are real solved poses, not
  rotation interpolation, so no elbow or wrist flips.
- **Natural weapon hold:** use `pose_fix.wield(dir, point)`. The haft lies across the palm with the hand in line with the forearm,
  and the elbow is pole-driven outward. It tries several elbow poles and keeps the one with no clipping and the straightest wrist.
- **Quaternion keys:** keys are stored as quaternions (shortest path).
- **Scan and correct:** every action is scanned on every other frame for limb or weapon clipping (and corrective keys are added).
  Every key logs its joint angles, and a wrist bent over 50° is flagged.
- **In place:** attacks are animated in place, and the AI moves the root between markers.

## 5. VFX (one shared system)
- **Attachments:** the socket bones become Attachments: `Weapon_R`, weapon tip, `VFX_Core`, `VFX_Eye`, wing tips and feet.
- **Emitters:** `ParticleEmitter`, `Trail` and `Beam` objects hang off those attachments and are switched on and off by the combat markers.
- **Texture sheet:** one shared sheet (spark, soft glow, streak, ring, rune circle, shard) for every biome, recoloured per biome palette.
- **Standard cues, identical on every enemy so players learn them once:**
  - **Tell:** eye flash plus a glow pulse; AoE moves add a ground rune.
  - **Active:** a weapon trail, only during HitStart to HitEnd.
  - **Recover:** the glow dims to 40% and slow motes drift off, meaning "open".
  - **Impact:** a spark ring and shards, plus camera shake near the player only.
  - **Phase change:** the break chunks fly off and the core flares.
  - **Defeat:** the glow flickers out, then a kneel or collapse, then an upward dissolve, then loot. The player can't be damaged during it.
- **Budget:** at most about 150 live particles per effect; Neon parts plus particles; one light maximum (the core).

## 6. Studio side (data-driven)
**Staged, not wired:** the owner approves `src/` changes, so this is proposed only.

Each biome gets `src/shared/Content/Enemies/<Biome>.luau` listing `EnemyDef`s. Each def has:
- id, tier and role
- the model asset, and the animation ids keyed by action name
- stats (HP, damage, speed)
- `phases` (HP thresholds and transition action), `moves` (from the moveset sheet) and `vfx` (palette + attachment names)

One `EnemyService` (spawning, aggro, archetype dispatch) and one `BossService` (phases, move selection, punish windows) serve
**every** biome. The world content's `Enemies = {}` / `BossId` fields (for example `Worlds/SkyCitadel.luau`) point at these defs.
The template is `assets/source/enemies/_framework/EnemyDef.template.luau`.

## 7. Starting a new biome (checklist)
1. `mkdir assets/source/enemies/<biome>`. Copy `sky_citadel/manifest.py` and empty the `ENEMIES` dict.
2. Write the roster: 10 basics, 3 minibosses and 3 bosses (the Sky Citadel pattern), with each basic mapped to an archetype.
3. Build the models with `enemy_kit` / `humanoid` (top of each script: `exec(open(FW + r"\enemy_kit.py").read())`).
   Every path goes through the `FW`, `HERE`, `OUT_DIR` and `RENDER_DIR` globals that `run.py` sets; never hard-code them.
4. Validate, render, owner review, then iterate.
5. Write the boss movesets, then the actions, then export.
6. Add `Content/Enemies/<Biome>.luau` defs (after owner approval of the Studio wiring).
Don't copy or edit `_framework/` per biome. If a helper is missing, add it to the framework so every biome gets it.
