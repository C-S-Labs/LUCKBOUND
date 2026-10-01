# Astral Reach enemy roster (STAGING, biome has no map yet)

Mythic world. Contract: `docs/BOSS_ANIMATION_VFX.md`. Full source plan (read by section):
`docs/design/boss_plans/ASTRAL_BOSS_ANIMATION_VFX_PLAN.md`. Only the two bosses below are specified; basics and minibosses are not drafted.

**Authority order (2026-09-30 reconciliation):** `docs/biomes/ASTRAL_REACH.md` (locked design, owner-confirmed 2026-09-29, with `docs/design/ASTRAL_REACH_SCHEME.webp`
and `docs/design/ASTRAL_REACH_BOSS_REFINEMENT.md`) is the design source of truth. The animation/VFX plan (`docs/design/boss_plans/ASTRAL_BOSS_ANIMATION_VFX_PLAN.md`) was written
without seeing it, so **where they differ the locked design wins**. Differences, resolved here:

| Topic | Animation/VFX plan | Locked design (wins) |
|---|---|---|
| Phases | two, "no unapproved third phase" | **3 each** (Phase 1, Phase 2, Final Phase; §5A.5). Final Phase is a full phase, not a low-health escalation. The plan's transitions map to P1->P2; **a P2->Final transition work order is still to be written** from `ASTRAL_REACH.md` §5A.5 |
| Triangles | Seraph 160-200k, Dancer 110-150k | **Seraph 175-200k, Dancer 200-250k** (§4.6); needs a deliberate Mythic validator tier |
| Dancer weapon | second handheld blade revealed in P2 | **RESOLVED 2026-09-30 (owner).** One real long blade through P1 and P2 (future Legendary player weapon stays single-blade). The **second blade materialises at the P2 -> Final transition**, pulled together from particles; it is spectral and boss-only. P2's form change is the cape unfurl plus a fan of floating blades (below) |
| Seraph weapon | wings plus lower feather-blades | design: the six wings are its weapon; lower blade barrage is additive; whether wings become a player weapon is not stated |
| World boss | do not replace `STAR_EATER` | design §4.5: one boss per run, 75% Seraph / 25% Dancer (provisional). `AstralReach.luau` wiring is a separate owner-approved task; no content file changed here |

Also: the plan found no Astral docs on `main` because they lived on an unmerged branch; they are merged with this change.
Plan sizes, timings and thresholds remain **proposals for owner review**.

Planned layout (propose in the first PR, confirm against `manifest.py` conventions): `manifest.py`, `astral_seraph.py`, `astral_seraph_wings.py`, `astral_seraph_halo.py`,
`celestial_dancer.py`, `celestial_dancer_cape.py`, `celestial_dancer_blades.py`, `AS_MOVESET.md`, `CD_MOVESET.md`, `anims/astral_seraph/`, `anims/celestial_dancer/`,
exports to `assets/export/enemies/astral_reach/` with a JSON timing/socket manifest. Mythic tri handling must be added to the validator **deliberately** (existing caps
are 75k epic, ~100k legendary, 10k per mesh); never weaken a check to fit.

## Shared rules for both
Mythic grandeur through composition, not density. **Three phases each (locked design).** Aggregate particles ~180 normal / ~300 brief transition. Server volumes for every wing/blade/beam/shockwave;
a traveling ring is an annulus, not a filled disc. Dancer ~2-2.5 and Seraph body ~3-4 player heights (wingspan ~7-9), for silhouette review only.
Shared FX recipes (ring, crescent ribbon, seal, feather shard, ground sector/lane indicators): contract §5; add feather and narrow-ribbon textures to the shared sheet if missing.

---

## Boss A: Astral Seraph — NOT BUILT (work order)

Upright masked celestial form, silver-white armour, gold filigree, blue chest core, geometric halo, **six independent wing modules** in a two-tier silhouette, feather-blades instead of legs.

**Construction**
| Part | Work |
|---|---|
| Body | Custom `seraph` body profile (hover height, blade clearance, wing bounds; no humanoid knee/grounding rules); reuse torso/arm helpers; ~50-60k tris |
| Wings | Six separate skinned modules `Wing_L_A/B/C`, `Wing_R_A/B/C` (map into two tiers once the concept board exists); bones `Root, Span_01, Span_02, Fan_01..03`; ~80-100k tris total; rigid bases, no per-feather rig |
| Wing seating | Six named body sockets matching module origins, hidden under collars; never fused to the body mesh; no hidden duplicate wing set |
| Halo | Ring plus separate etched/glow shapes, independent pivot |
| Lower feather-blades | Few rigid blades with release sockets (runtime copies as projectiles) |
| Glow | Small separate core and wing glow surfaces |
| Sockets | `VFX_Core`, `VFX_Eye`, `Halo_Center`, `WingSocket_<ID>`, `WingTip_<ID>`, `WingRoot_<ID>`, `LowerBlade_<NN>`; store rest transform and binding in manifest |
| Totals | **owner budget 175-200k** (`ASTRAL_REACH.md` §4.6); halo/blades/detail 30-40k |

Wing clips are module-local (`Fold, Open, Sweep, OrbitIdle, Settle`) and **bone-rotation only**; orbit/travel of detached modules is Roblox runtime motion. P1: a module controller follows body sockets.
P2: it releases roots onto prescribed world paths. Prove detachment with no transform jump in a short technical proof before expanding P2.

**Animations:** `Spawn_Reveal, Idle_Hover, Glide_Forward/Left/Right, Turn, P1_WingSweep_L/R, P1_HaloBeam, P1_Descent, P1_FeatherBarrage, P1_WingCloak, P1_CelestialRotation, P2_Transition, P2_Idle, P2_DetachedSweep, P2_OrbitalGate, P2_HaloBeam, P2_FeatherBarrage, Stagger, StaggerRecover, Hit_React, Death_Dissolve`.

**Moves (30 fps, T/A/R, proposals)**
- P1: Wing Sweep 30/10/30; Halo Beam 42/18/36 (aim commits f30, warning to f42); Descent 36/12/48 (damage = marked footprint, radial accent cosmetic); Feather-Blade Barrage 36/18/36 (three marked batches, travel must not outlive active); Wing Cloak 36/10/42 (one safe wedge); Celestial Rotation 36/24/42 (tested gap, not a solid 360°).
- P2 (Wing Cloak withheld while wings are released): Detached Sweep 36/12/36 (one module attacks, five hold); Orbital Gate 42/30/48 (visible corridor, one composed hazard); Halo Beam 42/18/42; Feather Barrage 42/24/42.
- **Transition:** 90 f no damage then 45 f vulnerable low hover. f0-24 stop, halo tilts, core gathers; f25-42 roots separate in mirrored pairs; f43-72 modules into orbital composition, one thin geometry ring; f73-90 body descends, wings park outside the melee lane; f90-135 punish window, recovery glow ~40%.
- Low-health escalation is visual only; the locked design's third (Final) phase supersedes the plan's "no third phase" and its work order is TODO.
- **P2 -> Final ("Ascension") transition** (proposal, ~90 f no damage, then 45 f punish): the detached wings reform into independent floating blades and rings (the locked Final Phase), halo and body settle on separate timings, one expanding geometry ring, wings park outside the melee lane. Final-phase overlap of halo beam and wing attacks must still keep a reachable safe space and 18 f punish (contract §2); confirm with owner.
- **Defeat (~4 s):** damage stops, wings freeze then drift out harmlessly, halo loses alignment, core dims, blades loosen, feather particles rise, staggered fade, one final silhouette. No collidable debris.

**Prototype (first end to end):** Wing Sweep, plus detachment as a short technical proof.
**Acceptance (extra):** modules detach with no visible jump, keep the two-tier P1 silhouette and are never welded to the body in P2; no wing strikes during beam recovery; barrage defeat mid-volley leaves no hazards.

---

## Boss B: Celestial Dancer — NOT BUILT (work order)

Obscured face, dark bodice, gold boots, dominant layered lavender-white/violet cape, **one real blade through P1 and P2, and a spectral second blade materialised in the Final Phase**.

**Silhouette rule (owner, from `docs/design/ASTRAL_REACH_SCHEME.webp`): slim and elegant.** The scheme art shows a tall, slender figure; the cape is a long, layered, translucent, gold-edged train that streams behind like a gown, never a bulky cloak or a wide rigid mass. P1 body plus cape must read slim from front, side and back at player scale. Review the silhouette against the sheet before any animation; reject a cape that widens the figure at rest. Width belongs to motion (flare on turns) and to the P2 unfurl, not to the rest pose.

**Construction**
| Part | Work |
|---|---|
| Body/outfit | Existing humanoid profile, fingers, forearm twist, spine extras, grip solver; ~55-70k tris |
| Main cape | Layered lavender top / violet underside, separate gold trim; five vertical chains x 4 bones + two side panels x 3 (26 bones, adjust to geometry); pin shoulders, protect neck/boot silhouette; 35-50k tris |
| Secondary panels | Separate overlapping cloth islands, no tassel simulation |
| Cape variants | P1 cape: slim layered train. P2 cape: lavender-white outer layer peels away, violet underside becomes the outer face, panels split into longer ribbon streamers. Same rig and bone chains, swapped skin/weights and a state toggle; no extra bones |
| Blades | Primary long blade (player-weapon quality). Second spectral blade as a separate export (matching family, off-hand grip), split along its length so it assembles by sections, **used in the Final Phase only**; 20-30k tris with detail |
| Floating blades | P2: 3-5 registered spectral blades that assemble into a fan/crown behind her; no sword swarm; each is a counted, bounded runtime object |
| FX | Crescent and ribbon shapes independent of the body mesh |
| Sockets | `Weapon_R/L`, `BladeBase_R/L`, `BladeTip_R/L`, `VFX_Eye`, `VFX_Core`, `CapeEdge_L/R`, `CapeHem_Center`, `Foot_L/R`, `Offhand_Reveal` |
| Totals | **owner budget 200-250k** (`ASTRAL_REACH.md` §4.6) |

Use `cloth_core`; **one driver per cape chain per clip** (no runtime sim over baked keys; authored flare targets feed the bake). Lag starts 3-5 f on a turn, settles in 12-18. Check cape clearance against hands, both blades and heels each frame. Do not mirror L/R variants blindly. Trails span blade base to tip, never the cape.

**Animations:** `Spawn_Reveal, Idle_Guard, Step_Forward, Glide_Forward/Back/Left/Right, Pivot_L/R, Stop_Settle, P1_OpeningWaltz, P1_VeiledStep_L/R, P1_CrescentWaltz, P1_FallingStar, P1_SilentStep, P2_Transition, P2_Idle_Dual, P2_TwinEcho, P2_DualBladePhrase, P2_GrandDance_A/B/C, Stagger, StaggerRecover, Hit_React, Death_FinalStep`.

**Moves (proposals)**
- P1: Opening Waltz 36/8/30; Veiled Step 24/8/24; Crescent Waltz 30/24/36; Falling Star 36/12/42 (post-`HitEnd` residue harmless; a dangerous residual path only as an explicitly timed, visibly persistent hazard with revised schedule); Silent Step 18/6/30.
- **Opening Waltz cue sheet:** f0 `Tell` step + chime; f8 blade near floor, drag line; f16 pivot ends; f24 `Commit` (server freezes path); f36 `HitStart`, runtime dash and Trail on; f40 max extension, one crescent; f44 `HitEnd`, Trail off, crescent fades in 8 f; f44-74 `RecoverStart`, no re-aim or chain.
- P2 (keep P1 attacks with dual poses; never change reach behind an unchanged warning): Twin Echo (tell 30, hit f30-38, echo tell f38-56, echo hit f56-64, recovery 36; echo is a hollow outline on the same fixed path); Dual Blade Phrase (tell 30, hit 8, second tell 18, hit 8, recovery 36; two hits max); Grand Dance in three phrases A (30 f held recovery), B (30), C (48), each with at least 30 warning frames and a real opening; no ten-hit string, no random teleport.
- **P1 -> P2 transition: "The cape unfurls"** (proposal, ~72 f no damage, then 36 f punish). f0-18 she stops in a stable asymmetric pose, cape settles, motes drift in; f19-42 the lavender-white outer layer lifts and peels away in sections (cosmetic fragments fade, no damage), revealing the violet underside; f43-60 the cape splits into ribbon streamers and flares once; f49-72 the floating blades assemble into a fan behind her, one thin ankle ring; trails stay off until a real attack; f72-108 calm held stance, reachable, recovery-dimmed. Still one blade in her hand.
- **P2 -> Final transition: "The echo becomes real"** (proposal, ~72 f no damage, then 36 f punish). f0-18 stops, off-hand opens, motes drift inward; f19-36 one narrow line sketches the blade length (the Twin Echo outline made solid); f37-48 hand closes correctly around the grip as the spectral second blade condenses by sections from the surrounding particles, one 3-frame white-lavender accent; f49-72 dual stance, floating blades re-arrange, cape flares once; trails stay off until a real attack; f72-108 held calm stance. Final-phase echo hits stay **hollow outlines**, visibly different from the solid second blade.
- The locked Final Phase says "minimal recovery" and "chained"; **owner confirmed 2026-09-30: the three-attack limit and 18 f punish stay.** The Final Phase stays hard through pressure and tight parry windows, not missing openings. Stagger (`ENEMY_AI.md` §10.1): Dancer is parry-staggerable, increasingly hard in P2 and Final but always possible; the Seraph is staggered only by its hidden meter, never by parrying ranged attacks.
- **Defeat (~3.5-4 s):** damage cancels, blades lower, cape settles, one final step, blades dissolve in sequence, body fades after the cape is still. No ragdoll or explosion.

**Prototype (first end to end):** Opening Waltz (slim-silhouette cape, grip, travel, markers, readability), plus the cape unfurl and second-blade materialisation as short technical proofs.
**Acceptance (extra):** slim silhouette matches the scheme art at rest; the unfurl never pops (same rig, swapped skin); the spectral blade is never confused with an echo; both grips stay attached in the Final Phase; pivot feet behave; cape cannot hide every warning cue (a boot, shoulder or cape-edge cue always announces the slash); no ghost trail damage.

---

## Build status
| Enemy | Tier | Status |
|---|---|---|
| Astral Seraph | Boss | work order written 2026-09-30, nothing built |
| Celestial Dancer | Boss | work order written 2026-09-30, nothing built |

First action when picking this up: read the plan §8 acceptance gates, reconcile local plans, then silhouette renders for owner review before any animation.
