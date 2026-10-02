# Ethereal Scape enemies: handoff to Codex (2026-09-30)

> **OWNERSHIP UPDATE (owner, 2026-10-02): Claude Code keeps THE ASCENDANT** (it created it). **Codex takes the other Ethereal Scape enemies** (basics' animations, the three minibosses). Codex: do not export, rebuild or edit the Ascendant mesh, rig, actions or `TheAscendant_fixed.blend`; where this file says "Codex" about the Ascendant, it now means Claude Code. Ascendant construction was not started tonight; the next Ascendant step is the read-only audit of `_fixed` (work order §1). To avoid binary-merge conflicts, only one agent touches `.blend` files for a given enemy.


Owner-directed: **the Ascendant and the rest of the Ethereal Scape (ES) enemy work moves from Claude Code to Codex.** Everything below is what a fresh agent needs. Read `INDEX.md`, `AGENTS.md`, then this file. Rules in `AGENTS.md` apply unchanged (branch `agent/<task>`, PR, do not merge unless integration agent, token discipline, update WORKLOG/STATUS/INDEX).

## Read in this order
1. `docs/BOSS_ANIMATION_VFX.md`: the universal boss animation/VFX contract (fairness, markers, recipes, budgets, acceptance).
2. `assets/source/enemies/ethereal_scape/ASCENDANT_MOVESET.md`: moveset plus the **"Work order 2026-09-30"** at the end (the Ascendant's construction list).
3. `docs/ENEMY_FRAMEWORK.md` (build/rig/export) and `docs/ENEMY_AI.md` §10.1 (parry and hidden stagger meter, owner rule 2026-09-30).
4. `assets/source/enemies/ethereal_scape/ROSTER.md` (note: its status table is stale, see below).
Long source plan, by section only: `docs/design/boss_plans/ASCENDANT_SENTINEL_ANIMATION_VFX_PLAN.md` §4.

## State of the ES enemies (verified against `origin/main`)
| Enemy | Tier | Source script | Export in `assets/export/enemies/ethereal_scape/` |
|---|---|---|---|
| Aether Wisp | basic | `aether_wisp.py` | `.blend` only |
| Temple Acolyte | basic | `temple_acolyte.py`, `anims/temple_acolyte/` Walk, Strafe | `.blend`, Walk, Strafe FBX |
| Meadow Stag | basic | `meadow_stag.py`, `anims/meadow_stag/Walk.py` | `.blend`, Walk FBX |
| Crystal Warden | basic | `crystal_warden.py` | `.blend` only |
| Skyborne Harrier | basic | `skyborne_harrier.py` | `.blend` only |
| 3 minibosses (Waystone Sentinel, Reliquary Keeper, Gatewarden) | miniboss | **drafted only**: `MINIBOSSES.md` (needs owner OK before modelling) | none |
| The Ascendant | boss | `the_ascendant*.py`, `anims/the_ascendant/` | body FBX plus Idle_Guard, Walk, StrafeL/R, P1_CrescentReap, P1_OrbCast, P1_SkyCast, Hit_React, P1_Stagger, P1_StaggerRecover |

`ROSTER.md`'s status table was corrected 2026-09-30 (basics scripted; verify each in Blender before claiming "built"). None of this is imported in Studio yet, and nothing spawns in gameplay (`EnemyDef` + services wait for the owner's OK).

## The Ascendant: hard guard rails
- **`assets/export/enemies/ethereal_scape/TheAscendant_fixed.blend` (4.8 MB, saved 2026-09-28) is the owner's newer hand-edited scene, added to the repo 2026-09-30.** It differs greatly in size from the older `TheAscendant.blend` (525 KB). **Owner confirmed 2026-09-30: the larger `TheAscendant_fixed.blend` is the authoritative Ascendant mesh.** Its contents were not inspected when it was committed, so still open it and audit it (work order §1) before exporting; the older `TheAscendant.blend` is superseded.
- **The owner's updated Ascendant spec (extra rigging and joint properties) may still be coming.** Do not export or rebuild the Ascendant mesh or rig until the owner confirms which file is authoritative; then reconcile it against the work order and update the work order first.
- The shipped FBXs come from the owner's **hand-edited** `TheAscendant.blend` (chest/centre crystal adjusted, `BreakawayGlow` removed). **Never run a full scripted rebuild/export over it** and never re-add `BreakawayGlow`. Locate the authoritative `.blend` (and any `_fixed`), compare, and add non-destructively.
- ES world/chunk edits (`ES_STRUCTURE.rbxmx`, `ES_PROP_LIBRARY.rbxmx`) are being implemented in a separate PR; do not touch them here.
- Do not commit `assets/rbxm/prefabs/HUB_SKY.rbxmx` changes (owner's local edit).

## Next steps, in order
1. **Audit** (work order §1): authoritative file, tri and bone counts (docs say ~150-154 bones), which sockets really exist.
2. Reconcile the owner's pushed spec/mesh; update the work order.
3. **Prototypes first:** `P1_OrbCast` plus overhead `P1_CrescentReap`, end to end (sockets, grips, cast origin, markers). Parry/stagger actions are already present (`Hit_React`, `P1_Stagger`, `P1_StaggerRecover`).
4. Remaining ES basics: animations (Idle, Walk, Strafe, attacks) per `ENEMY_FRAMEWORK.md` §1, one at a time.
5. Three minibosses: get owner OK on `MINIBOSSES.md`, then build (budget <=35k tris, finger bones), after basics.
6. Ascendant extras: `P2_Transfiguration`, death, approved move variants (work order §5), armour debris.
7. Studio import of ES enemies is the owner's step ("once, when the boss is finished"); do not mark any Studio check passed unless run.

## Decisions already made (do not relitigate)
- No halo and no hood on the Ascendant; caster-first roster (OrbCast/SkyCast); overhead chop is the close answer; phase boundary 55% HP, +25% damage without cuirass.
- Three-attack limit and 18 f punish stay everywhere (owner, 2026-09-30). Stagger is hit-triggered with a hidden meter (`ENEMY_AI.md` §10.1).
- Plan timings, budgets and move variants are proposals for owner review; no combat rebalance in an animation task.
- Open stale prose to fix when convenient: ASCENDANT_MOVESET "only ranged move" line.
- The owner's updated Ascendant spec (extra rigging/joint properties) may still arrive separately; reconcile it against `_fixed` when it does.

## Leftovers (do not delete yet)
Old moveset sections describing the horizontal Reap and melee-first roster stay until the roster is reconciled with the owner.
