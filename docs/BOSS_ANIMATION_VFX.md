# Boss animation and VFX contract (universal, every boss in every biome)

**Status: owner-directed 2026-09-30, adopted as the standard for all bosses, existing and future.** Every figure
marked *proposal* is a starting target to profile and review, not a platform guarantee. Behaviour/AI stays in
`ENEMY_AI.md`; how a body is built stays in `ENEMY_FRAMEWORK.md`. This doc owns the **cinematic layer**: animation
production, effect recipes, markers, cleanup and acceptance gates.

Full source plans (long, read by section only): `docs/design/boss_plans/ASTRAL_BOSS_ANIMATION_VFX_PLAN.md` and
`docs/design/boss_plans/ASCENDANT_SENTINEL_ANIMATION_VFX_PLAN.md`. Per-boss construction work orders live beside each
boss (see §9). Where a plan and an existing moveset disagree, **record the conflict and keep the owner's later edit**;
never silently rebalance combat inside an animation/VFX task.

## 1. Principles

1. **Spectacle comes from silhouette, choreography and empty space, not particle density.** Higher rarity buys more
   composition, more distinctive moving parts and signature moments. It does not buy more flashes or simultaneous hazards.
2. **One dominant shape per attack, at most two decorative layers.** A ground warning is a required readability layer,
   never decoration. Idle is quiet, recovery is quieter. A phase change gets the biggest single silhouette change, then returns to readable combat.
3. **Hierarchy:** player and threat boundary, then boss posture and attacking part, then active hazard and safe space,
   then decoration. Every attack must stay readable with bloom and optional particles off.
4. **World rarity is not weapon rarity.** A Legendary drop does not make the encounter Legendary or Mythic spectacle.
5. **Server owns damage, targets, movement, phase and hit results. Clients only render** cosmetics from an
   authoritative attack id, start time, committed path/target and phase. A client event never grants damage.
   Late events fast-forward or skip expired visuals.

## 2. Fairness (extends the Sky Citadel rules; these are the shared minimums)

- At least **8 f** of recognisable visual tell **and** an audio cue before any damaging commitment. No hitbox during the tell.
- At least **18 f** genuine punish time after an attack or short string; at least **0.5 s** between strings; **never more than 3
  committed attacks before an opening.** Combo metadata counts damaging commitments, not action-file names.
- Aim/path locks at a visible `Commit` point; nothing steers invisibly after it. Warnings stay visible until release/impact.
- No 360° hit without a gap, nothing hits the whole arena, a reachable safe zone always exists (verify against the real
  movement/roll system, not assumed jumps or invulnerability).
- Fliers and aerial landings end inside sword range, on validated ground (never behind a wall or outside the arena).
- Detached or lingering hazards stop threatening during recovery. A pretty fading afterimage must be visibly distinct
  from a persistent damaging residue; **no unmarked damage from a decorative trail.** A projectile's lifetime is its own
  contract and is not ended by the caster's `HitEnd`; decide and document whether it may outlive the cast.
- Transition and defeat debris does no damage; transition invulnerability is an explicit server state ending in a free punish window.

## 3. Blender contract (all in the existing `_framework/`, headless `run.py`)

- Extend, never fork: reuse `enemy_kit`, `anim_core`, body profiles, `cloth_core`, `hands_core`, pose/grip solvers,
  validation, preview and `export.py`. No second rig pipeline. Preserve manifest extras order.
- **Audit before touching an existing boss:** locate the authoritative `.blend` (compare dates, meshes, rig names, exports;
  file name alone proves nothing), record current tri and bone counts, then add non-destructively. Never rebuild over a hand-edited mesh.
- Author at 30 fps. Attacks are **in place**; travel (lunges, glides, portal steps, vaults) is server runtime root motion.
  Save the intended travel curve as data for the controller and previews; never export root travel **and** apply it again.
- Preview cloth/wings against the intended world acceleration, then export relative bone keys (an in-place sim alone gets dash lag wrong).
- Bake IK, constraints and secondary motion to supported bone transforms. Sims, particles, shader graphs, lights and viewport
  glow are not the Roblox effect. Blender timeline markers do not become Studio events automatically: recreate/verify and compare to the manifest.
- Skinning: max **4 influences** per vertex; hard armour rigid; split solid/trim/glow geometry where runtime tint or transparency needs it.
  Skinned deformation does not move collision, so gameplay uses explicit server volumes.
- Keep the per-piece triangle cap and its validator. Never weaken a validator to pass an oversized mesh; a new tier needs a deliberate manifest/validator change.
- **Bone translation is unreliable on import.** Use rotation-driven deformation and runtime model movement; prove any needed
  translation in a small Studio round-trip first.
- Socket helper bones are dropped by Studio if they deform nothing: use the existing export pinning, then verify every
  socket's imported transform **while the bone animates**. A helper empty is not a working Attachment.
- Do not add dozens of bones to hang VFX; use existing sockets or a small verified addition. Preview-only objects are tagged so they never enter a character FBX.
- Verify imported size against a player-height reference (Blender metres are not studs).

## 4. Timing, markers and manifest (per action)

Required markers: `Tell`, `HitStart`, `HitEnd`, `RecoverStart`. Proposed optional: `Commit`, `Impact`, `Footstep`,
`WingBeat`, `ArmourBreak`, `LanceIgnite`, `P2Start`, and named `VFX_*`. An added marker needs the manifest entry **and** a runtime listener.

Store per action: clip id, source fps, start/end, marker frames, committed target/path, sub-hit windows, warning duration,
projectile lifetime, impact time, recovery, socket names, FX recipe id, cleanup owner. Frame counts are differences between
markers (note whether the source script is 1-based). Gameplay converts at 30 fps. Compare every imported event to the manifest.

## 5. Runtime effect recipe (data, not copy-pasted emitter code)

Each recipe records: owning boss/action id; event or phase; origin binding; local offset/orientation; target/path source;
warning shape; active volume reference; components; colour/texture; scale; duration; live-count target; low-quality
replacement; cancellation behaviour. Reuse code for rings, bursts, trails and debris. Reuse existing systems
(`WeaponFX`, `LightningRigs`, `LightningController`); do not invent a parallel VFX service. Never hand-edit generated `LightningRigs.luau`.

- **Ownership/cleanup:** an attack instance owns its objects, connections and effects. Cancel, stagger, death, phase change,
  despawn and debug reset clear them. Phase energy is owned by phase state, not a stale attack callback. Repeated `/showboss`
  previews must not accumulate attachments, lights or pooled objects. Reward timing follows server encounter completion, never a client dissolve.
- **Budget (proposals, profile before trusting):** ≤150 live particles per effect (existing rule); aggregate decorative
  targets per boss: Ascendant ~50 normal / ~110 transition, Sentinel ~90 / ~180, Astral bosses ~180 / ~300. One light only
  (the core). No whole-screen bloom or exposure pulse per strike. Bound lifetimes, beam counts, trail lifetimes and temporary
  mesh counts; profile transparent overdraw, not just particles. Camera shake: local, distance-scaled, optional, major impacts only.
- **Low quality** removes motes, debris, echoes and secondary crackle first; **never** a tell, warning, orb origin or hazard boundary.
- **Cues stay consistent across bosses** (`ENEMY_FRAMEWORK.md` §5): recovery dims to ~40% of active intensity as a shared
  cue, not a literal colour multiply that blacks out dark materials.
- **FX meshes** (ring, crescent, shard, pillar, seal, ribbon): small (200–1,500 tris starting target), pivot and UV rules
  per recipe, exported separately from body FBXs, non-collidable, checked from back and ground-level cameras, tested in Studio not just Blender emission renders.
- Ground warning shapes use shared textures or procedural geometry with recorded dimensions that match the server volume.

## 6. Phases, transitions and defeat (the shape every boss follows)

- Phase boundaries and damage modifiers stay as the boss's moveset sheet states; this doc adds no third phase.
- **Transition:** no damage, one largest silhouette change, harmless cosmetic debris with deterministic movement and a TTL,
  then a free vulnerable window (recovery-dimmed). Break pieces hide the source armour once and restore on reset.
- **Defeat:** about 3.5–4 s, all damage cancelled, no ragdoll or explosion, one readable final silhouette, a bounded
  dissolve; loot/reward follows the server.
- Low-health escalation, if any, is visual inside the phase; it never removes warnings or recovery.

## 7. Mandatory delivery order for any boss (extends `ENEMY_AI.md` §12 / framework §1)

1. Audit (authoritative mesh, existing vs missing parts/sockets/actions, counts, conflicts).
2. Per-boss production manifest (sockets, provenance, source timings, travel/hazard timing, event ownership).
3. Silhouette renders at player scale; **owner reviews before expensive animation.**
4. One-rig Studio round-trip (size, weights, retained sockets, pivots, material splits).
5. **Two end-to-end prototypes** (listed in each work order), including real active/recovery states and runtime effects, with
   warnings and server volumes visualised.
6. In-game readability review (third person and lock-on, near/far, real biome lighting, low quality, mobile-size viewport).
7. Expand approved actions, transitions, death; consolidate one moveset per boss; register assets.
8. Validate and report, separating source validation, Blender visual review, imported Studio checks and real playtests.
   **Never mark a Studio check passed that was not run.**

## 8. Acceptance gates (all bosses)

- Clean rest poses, no clipping across any exported frame, grips never slip or flip while held, joints inside the profile's limits.
- Names of rigs, parts, sockets and clips match the manifest; every marker has the intended timing after import.
- Server volumes agree with what the skin shows; every move has a reachable safe response and sword punish window; nothing
  damaging survives into declared recovery.
- Tells read without bloom/decoration, in real biome lighting, at low quality and mobile-size views.
- Stress: interruption, poise break, phase threshold mid-move, death with an active spell/barrage, streaming and late events,
  two viewers, late joiners, despawn, repeated debug previews. No duplicate hits, stray trails, duplicate hazards, missing phase
  parts or unbounded spawned objects.
- Profile a whole encounter on low/mid hardware including transition transparency and existing beam count.

## 9. Per-boss work orders (where the construction lists live)

| Boss | Status | Work order |
|---|---|---|
| The Ascendant (Ethereal Scape) | built, awaiting owner's updated spec and mesh with extra rigging/joint properties | `assets/source/enemies/ethereal_scape/ASCENDANT_MOVESET.md`, "Work order 2026-09-30" |
| Winged Sentinel (Sky Citadel) | built, extend only | `assets/source/enemies/sky_citadel/WS_MOVESET.md`, "Work order 2026-09-30" |
| Astral Seraph (Astral Reach) | not built | `assets/source/enemies/astral_reach/ROSTER.md` |
| Celestial Dancer (Astral Reach) | not built | `assets/source/enemies/astral_reach/ROSTER.md` |

`src/shared/Content/Worlds/AstralReach.luau` still names `STAR_EATER` as its boss. **Do not swap it for Seraph or Dancer without a
separate owner-approved task.** Future bosses copy a work-order block (audit, manifest, prototypes, parts, FX recipes, conflicts, acceptance).
