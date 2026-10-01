# LUCKBOUND — Astral Seraph & Celestial Dancer
## Blender construction, animation, and Roblox VFX production plan

Review draft • 30 September 2026 • Prepared for Codex / Claude Code

## 1. Scope and source status

This is an agent handoff specification for constructing the bosses, their moving accessories, animation clips, reusable effect meshes, and Roblox effect timing. It is a plan, not a report that these assets or runtime systems have been built.

Established design foundation: `Astral_Reach_Boss_Design_Refinement.md` (saved 29 September), plus the earlier decision that Dancer reveals a second handheld blade in phase two. Seraph has six wing modules, a two-tier overall silhouette, masked head, silver-white armor, gold filigree, blue chest core, geometric halo, and feather-blades instead of conventional legs. Dancer has an obscured face, dark bodice, gold boots, and a dominant layered lavender-white/violet cape.

Repository inspection: `C-S-Labs/LUCKBOUND`, main at `1001ec2`; all seven visible remote branches were enumerated, and the six distinct branch-tip trees inspected. No Seraph/Dancer-named assets or Astral boss plan documents were present in those trees. `docs/biomes/ASTRAL_REACH.md` was absent from main. Unpushed local work is outside this inspection. Agents must reconcile this draft with local files before implementation.

Actual existing integration references:

- `docs/ENEMY_FRAMEWORK.md`: shared Blender framework, cloth, rigs, markers, import lessons, VFX rules.
- `assets/source/enemies/sky_citadel/WS_MOVESET.md`: existing moveset format and 30 fps timing convention.
- `docs/ART_DIRECTION.md`: rarity color belongs to UI/portals; biome art can have its own palette.
- `src/shared/Content/Worlds/AstralReach.luau`: world is Mythic, currently points to `STAR_EATER`. Do not silently replace its boss selection with either new boss.

The saved refinement is expressive rather than fully balanced: its silent attacks, long uninterrupted strings, and increasing overlap need adaptation to the framework's readable tells and punish windows. All exact timings, dimensions, budgets, phase thresholds, and attack allocations below are **proposals for review**, not previously approved facts. Preserve current local approved designs if they differ and record the conflict explicitly. Obtain the actual concept board before claiming a visual match; prose alone does not establish exact geometry.

Ascendant and Winged Sentinel are the next application of this format after the owner reviews these two. Their existing meshes, animations, and movesets should be extended, not replaced by this draft.

## 2. Art direction: spectacle with restraint

| Boss | What carries the spectacle | Movement | Effect language | Avoid |
|---|---|---|---|---|
| Astral Seraph | Scale, silhouette changes, independently moving wings | Upright gliding; stillness before commitment | Gold geometric outlines, ice-blue energy, narrow white highlights, feather shapes | Constant flapping, generic fire, fog walls, all wings attacking continuously |
| Celestial Dancer | Cape follow-through, precise choreography, second blade | Step, glide, pivot, pause, sudden acceleration | Lavender ribbons, violet echoes, thin gold accents, restrained star motes | Continuous spinning, giant opaque slash discs, particle-filled cape, unreadable teleport hits |

Each attack gets one dominant shape and at most two decorative supporting layers. A ground warning is a required readability layer, not optional decoration. White is a brief accent; colored energy and dark negative space remain visible. Idle is quiet. Recovery is quieter. Phase transitions get the largest single silhouette change, followed by a return to readable combat.

Higher rarity increases choreography, spatial composition, distinctive moving parts, and the importance of signature moments. It does not automatically increase particle density, flash frequency, or the number of hazards occurring at once. Both Astral bosses belong to the Mythic world; they achieve grandeur differently.

### Visual hierarchy

1. Player and immediate threat boundary.
2. Boss posture and attacking weapon/wing.
3. Active hazard and visible safe space.
4. Decorative particles and lingering light.

An attack must still be understandable with decorative particles and bloom disabled. Color is supplemented by shape, posture, and audio. Any persistent damaging residue stays visibly distinct from a fading harmless afterimage.

## 3. Shared construction and export contract

Use `assets/source/enemies/_framework/` and its headless `run.py` entry point. Reuse `enemy_kit`, `anim_core`, body profiles, `cloth_core`, `hands_core`, pose helpers, validation, preview, and export. Do not create a parallel enemy pipeline or assume a new VFX service is required: inspect the actual client/server implementation and extend the shared system where it exists.

Suggested content locations, subject to current local index and manifest conventions:

| Deliverable | Proposed location |
|---|---|
| Roster and build registration | `assets/source/enemies/astral_reach/manifest.py` and `ROSTER.md` |
| Seraph body and extras | `astral_seraph.py`, `astral_seraph_wings.py`, `astral_seraph_halo.py` |
| Dancer body and extras | `celestial_dancer.py`, `celestial_dancer_cape.py`, `celestial_dancer_blades.py` |
| Approved moveset sheets | `AS_MOVESET.md`, `CD_MOVESET.md` |
| Action scripts | `anims/astral_seraph/<Action>.py`, `anims/celestial_dancer/<Action>.py` |
| Shared visual mesh recipes | A reusable FX location selected from the current repo conventions |
| FBX exports | `assets/export/enemies/astral_reach/` |
| Timing/socket/export manifest | JSON alongside exports; runtime content uses existing `EnemyDef` conventions |

### Authoring rules

- Use a player scale reference in Blender and verify its imported Studio size. Initial review targets: Dancer about 2–2.5 player heights; Seraph body about 3–4, wingspan about 7–9. These are proportions for silhouette review, not final studs.
- Author at 30 fps; gameplay uses seconds. Timing tables below use elapsed frame counts from `Tell = 0`; adapt to the framework's actual frame-index origin during generation.
- Combat travel is runtime root motion. Blender attacks are in place; save an intended motion curve separately for the controller and previews. Do not apply both exported root translation and runtime travel.
- Cape motion must account for intended world acceleration in the bake preview, then export relative bone keys. A stationary in-place simulation alone will not produce correct dash lag.
- Bake IK, constraints, and secondary motion to supported bone transforms. Blender simulations, particle systems, shader graphs, lights, and viewport glow are not the Roblox effect implementation.
- Hard armor is rigidly weighted. Cloth and feathers use deliberate deform weights, with at most four influences per vertex. Split solid body, trim, and glow geometry where runtime tint/transparency requires it.
- Preserve the framework's strict per-piece triangle cap unless current importer documentation and project rules explicitly permit changing it. Do not weaken validators to pass an oversized mesh.
- The framework currently documents animation problems with bone translation; use rotation-based deformations and runtime model movement for module travel. Prove any required translation in a small Studio round-trip first.
- FX socket helper bones can be dropped when they deform nothing: use the existing export pinning method, then verify all sockets in Studio. A helper empty is not automatically a working runtime Attachment.
- Export static rigs and separate FBX files per action through the existing exporter. Verify scale, rest pose, axis conversion, material split, skinning, and action identity before publishing animations.

### Proposed geometry allocation

These are art targets, not platform limits. Existing project caps remain authoritative; Mythic handling must be added to the manifest/validator deliberately if unsupported.

| Asset | Target total triangles | Included in that total |
|---|---:|---|
| Seraph | 160–200k, maximum 250k only if current owner rule permits | Body 50–60k; all six wings 80–100k; halo, lower blades and details 30–40k |
| Dancer | 110–150k, maximum 200k | Body/outfit 55–70k; cape 35–50k; both weapons and detail 20–30k |
| Temporary effect meshes | 200–1,500 each as a starting target | Ring, crescent, geometric disc, shard; profile transparent screen coverage as well as triangles |

Do not increase either model to its ceiling merely because the budget exists. Thin surfaces need verified visibility from relevant camera angles; use carefully chosen thickness or two-sided rendering instead of indiscriminately doubling geometry.

## 4. Combat, marker, and VFX contract

Retain `Tell`, `HitStart`, `HitEnd`, `RecoverStart`; optional markers include `Impact`, `Footstep`, `WingBeat`, and named `VFX_*`. Additional named sub-hit markers and their exact windows go in the move manifest. Do not assume Blender timeline markers become Roblox animation events automatically: recreate or import them through a verified tool, and compare every exported event to the manifest.

The server owns move choice, targets, committed movement, damaging volumes, phase state, and hit results. Clients render cosmetic assets from an authoritative attack ID, start time, target snapshot/path, phase, and seed if needed. Animation markers coordinate presentation with the same timing specification; a client event never grants damage authority. Late events fast-forward or skip expired visuals rather than replaying an entire stale attack.

Skinned bone deformation does not make a matching physical collision shape. Use explicit gameplay volumes for wings, blades, beams, and shockwaves, driven by server-approved geometry/path data. VFX must match their real width, height, reach, duration, and direction. Decorative outer fringes stay faint and harmless. Rings sweep an annulus if described as a traveling ring, not an invisible damaging filled disc.

### Required fairness rules

- Every damaging commitment has at least 8 frames of recognizable warning and an audio cue; proposed tells here are generally longer.
- Every attack or short string ends with at least 18 frames of genuine punish time. Use at least 0.5 seconds between strings and no more than three attacks before an opening.
- Tracking stops at a visible `Commit` point. Do not continue steering a rapid slash/beam invisibly after the player has reacted.
- Ground warnings stay visible throughout their tell. Safe zones must be reachable with the actual player's movement and dodge system, without relying on unverified jumping or invulnerability assumptions.
- Flying bosses descend or hover within verified sword range for openings. Detached hazards stop threatening the punish zone during recovery.
- Transition/defeat debris does no damage. Transition invulnerability, if used, is a clearly defined server state; transition ends in a free punish window.

### Shared effects and performance

Use the existing shared spark/glow/streak/ring/rune/shard textures, plus a feather silhouette and narrow ribbon texture if missing. Blender supplies simple FX meshes; Studio supplies ParticleEmitters, Trails, Beams, runtime mesh scaling/fading, and sound. Use only one boss light, on the core, consistent with the current framework. Do not add whole-screen bloom or exposure pulses per strike.

Keep the framework's approximate ceiling of 150 live particles per individual effect. Proposed initial aggregate boss caps: 180 live particles during normal combat and 300 briefly during a transition, including every wing/cape emitter. These are profiling targets rather than proven safe device limits. Low quality reduces particles and removes echoes/shards, while preserving every tell and hazard boundary. Bound FX lifetime, beam count, trail lifetime, and temporary mesh count; screen-filling transparent layers can be costly even at low particle counts.

Each effect instance belongs to one attack ID. Cancel/death/despawn/reset disables trails, disconnects events, and clears owned hazards and visuals. Repeated previews cannot accumulate attachments, lights, or pooled objects. Camera motion is local, distance-scaled, optional, and briefly used on major impacts only.

## 5. Astral Seraph: build specification

### Parts and rig

| Part | Blender construction | Animation/runtime purpose |
|---|---|---|
| Central body | Upright masked celestial form; separate rigid armor and blue core shell | Very little torso motion; readable core and posture |
| Six wings | Six separately exportable skinned modules; rigid bases, hinged spans, controlled feather fans | Attached P1; independent model motion P2 |
| Wing seating | Six named body sockets and matching module origins; sockets hidden under decorative shoulder/root collars | Seamless phase transition without popping |
| Geometric halo | Ring plus separate readable etched/glow shapes; independent pivot | Aligns before beam; tilts and rotates independently |
| Lower feather-blades | A small set of distinct rigid blade objects with release sockets; preserve lower silhouette | Barrage projectiles launch as runtime copies; original blade visibility changes deliberately |
| Core and wing glow | Small separate surfaces following the proper bones | Controlled tell, active, and dim recovery state |

Name wings `Wing_L_A/B/C`, `Wing_R_A/B/C`. These IDs do not mean three vertical tiers: map them into the painting's two-tier silhouette once the concept board is available. Each wing starts with `Root`, `Span_01`, `Span_02`, `Fan_01..03` (six deform bones); add complexity only when a pose requires it. Do not rig every feather individually.

Choose a custom `seraph` body profile using the framework's body-agnostic checks. It must understand hovering, blade lower-body clearance, wing/module bounds, and declared safe hover height rather than applying humanoid knee/grounding rules to nonexistent legs. Reuse compatible torso/arm helpers where appropriate.

The six wing modules remain separate throughout both phases. In P1 a module controller follows body sockets while wing clips provide local folding. In P2 it releases the module roots onto prescribed world paths. Bake module-local feather motion; drive orbit/translation in Roblox. Blender preview assembles all modules in one scene, but they are not fused into one deforming body mesh. No hidden duplicate wing set switches in during combat.

Sockets: `VFX_Core`, `VFX_Eye`, `Halo_Center`, `WingSocket_<ID>`, `WingTip_<ID>`, `WingRoot_<ID>`, `LowerBlade_<NN>`. Store their rest transform and binding target in the manifest, then verify moving socket transforms against imported bones.

### Animation set

`Spawn_Reveal`, `Idle_Hover`, `Glide_Forward`, `Glide_Left`, `Glide_Right`, `Turn`, `P1_WingSweep_L/R`, `P1_HaloBeam`, `P1_Descent`, `P1_FeatherBarrage`, `P1_WingCloak`, `P1_CelestialRotation`, `P2_Transition`, `P2_Idle`, `P2_DetachedSweep`, `P2_OrbitalGate`, `P2_HaloBeam`, `P2_FeatherBarrage`, `Stagger`, `StaggerRecover`, `Hit_React`, `Death_Dissolve`.

Wing-module local clips: `Fold`, `Open`, `Sweep`, `OrbitIdle`, `Settle`. P2 body clips and module path/clip tracks share the same attack timeline. Whole-body motion remains coherent; idle is restrained rather than totally frozen. Shared torso clips may be reused for P2 if a meaningful silhouette change comes from the module tracks.

### Phase 1 attacks — attached, ceremonial

T/A/R = tell / active / guaranteed recovery, at 30 fps. Listed recovery begins after all sub-hazards end. Between attack strings retain the shared 0.5-second minimum pause.

| Move | T/A/R | Blender motion | Roblox effect layers | Counterplay |
|---|---|---|---|---|
| Wing Sweep | 30 / 10 / 30 | One side opens slowly, holds, sweeps once; opposite side balances | Wing edge charges; thin crescent during sweep; a few feather motes | Read attacking side, evade through the tested safe flank; no full-arena reach |
| Halo Beam | 42 / 18 / 36 | Complete stillness; halo locks on chest axis; slight recoil | Narrow aiming line, geometric halo illumination; one solid beam core with soft edge | Aim commits at f30; warning remains to f42; leave corridor; boss stays low |
| Descent | 36 / 12 / 48 | Rise, fold, snap down, compress wing fans and settle at low hover | Ground impact boundary; one ring/column accent; sparse shards | Leave marked impact footprint; boss is reachable throughout recovery |
| Feather-Blade Barrage | 36 / 18 / 36 | Lower blades spread, hold, release in three ordered batches | Three visibly marked landing groups; blade streaks and small hit sparks | Each batch has a full warning; later targets fixed before release; safe corridor maintained |
| Wing Cloak | 36 / 10 / 42 | Wings enclose body, pause, open in one decisive motion | Visible ground sectors with one deliberate safe wedge; short gold radial streaks | Reach safe wedge; opening is explicit, not concealed by flash |
| Celestial Rotation | 36 / 24 / 42 | Wings extend, body turns through a controlled arc | Outline attacking tips, faint swept-sector warning | Retreat beyond sweep or use tested gap; not a solid 360-degree unavoidable hit |

For barrage, projectile travel/arrival timings are authored in the manifest; a projectile must not arrive after the declared active phase ends. Extend active time and move recovery if travel requires it. Descent's radial accent is cosmetic in the first prototype: damage is the marked impact footprint. A traveling damaging wave is a separate reviewed addition with a verified escape route.

### Phase 2 transition — release of anatomy

Proposed transition: 90 frames, no damage, then 45 frames of vulnerable low hover.

| Time | Animation/parts | Effects |
|---|---|---|
| f0–24 | Body stops; halo tilts; wings tense outward | Blue core gathers light; wing collars develop thin gold outlines |
| f25–42 | Wing roots separate in mirrored pairs with continuous world transforms | 3-frame root flashes, six restrained feather bursts; optional fine tether beams only during separation |
| f43–72 | All six modules move into an open orbital composition | One expanding thin geometry ring; motes fade rather than filling the arena |
| f73–90 | Body descends; wings park outside melee approach lane | Core settles to P2 baseline; transient beams disappear |
| f90–135 | Genuine punish window, no wing attack | Recovery glow at roughly 40% of active intensity |

The detachment is intentional celestial release, not necessarily torn flesh or an explosive damage event. Preserve symmetry at first; independent timing becomes the P2 signature.

### Phase 2 attacks — controlled independence

Keep P1 attacks where anatomically sensible, replacing attached sweeps/rotation with module equivalents. Wing Cloak is withheld while wings are released; do not pretend detached wings still originate from body joints.

| Move | T/A/R | Motion and VFX | Threat limit |
|---|---|---|---|
| Detached Sweep | 36 / 12 / 36 | One wing aligns as a floating blade, edge lights, then crosses one marked sector | One attacking module; remaining five hold a calm composition |
| Orbital Gate | 42 / 30 / 48 | Two wings form a rotating gate with a clearly visible open corridor; gold edge ribbons describe movement | One composed hazard pattern, not six independent simultaneous attacks |
| Halo Beam P2 | 42 / 18 / 42 | Halo rotates independently, locks aim, fires; parked wings frame the beam | Body stays reachable afterward; no wing strikes during beam recovery |
| Feather Barrage P2 | 42 / 24 / 42 | Wider formation of the same three batches; richer core/halo pose, restrained blade trails | Marks remain readable; preserve a reachable safe corridor |

At low health use a visual escalation inside P2, not an unapproved third combat phase: halo tilts more, core pulses stronger, idle modules vary their orientation. One intentional two-threat sequence can be proposed later after playtesting. Do not grant an AI agent permission to add arbitrary overlapping damage or delete recovery windows.

### Defeat

About 4 seconds: all damage stops; wings freeze then drift down/out harmlessly; halo loses alignment; core dims; lower blades loosen; feather-shaped particles rise while the body fades in staggered sections. Keep one final readable silhouette. Do not flood the screen or simulate collidable wing debris. Reward timing follows the game's server encounter/reward rules, not a client dissolve callback.

## 6. Celestial Dancer: build specification

### Parts and rig

| Part | Blender construction | Animation/runtime purpose |
|---|---|---|
| Body/outfit | Humanoid rig; masked/veiled face, dark fitted torso, gold boots | Precise weight shifts, planted pivots, controlled shoulders |
| Main cape | Broad layered shape with lavender-white top and violet underside; separate gold trim | Dominant moving silhouette; weighted soft folds |
| Secondary cape panels | Separate overlapping cloth islands, not many tiny simulated tassels | Lag, concealment, flare and settling without noisy flutter |
| Primary blade | Separate unique boss weapon; clear base/tip sockets | P1 weapon, grip held throughout strikes |
| Second blade | Separate export with matching visual family and distinct off-hand grip | P2 materialization, dual-wield choreography |
| FX crescent and ribbon | Simple reusable shapes independent of body mesh | Brief slash accent, echo visual, blade-reveal line |

Use the existing humanoid profile, fingers, forearm twist/spine extras, and grip solving. Initial cape rig: five main vertical chains of four deform bones plus two side-panel chains of three (26 cape bones). Adjust to actual geometry and bone budget; share gold trim weights with its cloth panel. Pin cape shoulders and protect the neck/boot silhouettes.

Use `cloth_core` for natural follow-through, with explicit authored cape poses where attack readability needs a controlled flare. One driver owns each cape chain per clip: do not layer a second runtime simulation over baked keys. Hand-authored flare targets must feed the bake or be blended deliberately rather than overwritten by its post-pass. Test cape clearance against hands, both blades, heels, and body in every exported frame.

Cape lag starts around 3–5 frames on a turn; settle over 12–18 after a sudden stop. Do not hide the attacking hand for the entire tell. A visible boot, shoulder, or cape-edge cue must announce even a concealed slash.

Sockets: `Weapon_R`, `Weapon_L`, `BladeBase_R/L`, `BladeTip_R/L`, `VFX_Eye`, `VFX_Core`, `CapeEdge_L/R`, `CapeHem_Center`, `Foot_L/R`, `Offhand_Reveal`. Trails span blade base to tip, not the entire cape width. World travel is supplied by the move controller; bake the resulting cape response.

### Animation set

`Spawn_Reveal`, `Idle_Guard`, `Step_Forward`, `Glide_Forward`, `Glide_Back`, `Glide_Left/Right`, `Pivot_L/R`, `Stop_Settle`, `P1_OpeningWaltz`, `P1_VeiledStep_L/R`, `P1_CrescentWaltz`, `P1_FallingStar`, `P1_SilentStep`, `P2_Transition`, `P2_Idle_Dual`, `P2_TwinEcho`, `P2_DualBladePhrase`, `P2_GrandDance_A/B/C`, `Stagger`, `StaggerRecover`, `Hit_React`, `Death_FinalStep`.

Right/left variations are not blindly mirrored: asymmetrical cape, grips, and blade visibility require dedicated inspection. `Glide` has deliberate magical sliding; `Step` and `Pivot` keep meaningful foot contact. Stable head/hood framing supports the elegant identity.

### Phase 1 attacks — learn the rhythm

| Move | T/A/R | Blender motion | Roblox effect layers | Counterplay |
|---|---|---|---|---|
| Opening Waltz | 36 / 8 / 30 | Deliberate step, blade drags low, pivot, pause, single accelerating slash | Thin floor line during tell, active blade Trail, one fading crescent | Direction locks f24; dodge clear of final corridor; she stops within approach range |
| Veiled Step | 24 / 8 / 24 | Body turns away, cape flares, boot/shoulder commits, blade emerges | Brief lit cape edge during warning; narrow Trail on strike | Tell identifies slash side; cape cannot hide all warning cues |
| Crescent Waltz | 30 / 24 / 36 | Slow rotation then one accelerating committed sweep | Short blade ribbon; one curved crescent at contact | Outer range/safe flank is visible; initial decorative turn is harmless |
| Falling Star | 36 / 12 / 42 | Small lift, airborne pause, diagonal descent, controlled low landing | Marked travel lane; thin luminous path with explicit expiration | Leave lane; landing gives melee opening |
| Silent Step | 18 / 6 / 30 | Nearly still, heel lifts, weight shifts, fast short cross-step slash | Modest blade-tip pulse and quiet chime; short cape-edge streak | Read weight shift; no music swell required, but retain audible warning |

Falling Star's first prototype uses harmless fading residue after `HitEnd`. The saved concept mentions a briefly dangerous residual path; enable that only as an explicitly timed, visibly persistent hazard with a full warning and a revised active/recovery schedule. No invisible damage from a pretty fading trail.

### Opening Waltz — exact prototype cue sheet

| Frame | Body/cape | Runtime/VFX | Damage |
|---|---|---|---|
| f0 | `Tell`: leading foot steps | Soft chime, small tip pulse | Off |
| f8 | Blade lowers near floor | Fine drag-line spark texture, low density | Off |
| f16 | Pivot ends; cape catches up | Drag effect stops; anticipated lane remains visible | Off |
| f24 | `Commit`: body holds, cape still settles | Server freezes path/aim | Off |
| f36 | `HitStart`: shoulders and blade release | Runtime dash starts; blade Trail enables | On |
| f40 | Maximum extension | One thin crescent; contact sparks only on confirmed hits | On |
| f44 | `HitEnd`: feet/braking pose | Trail disables; crescent fades within 8 frames | Off |
| f44–74 | `RecoverStart`: stop, lower blade, cape settles | Glow dims; no re-aim or chained hit | Off; boss punishable |

This is the first end-to-end Dancer prototype. Prove its cape, grip, travel, markers, and readability before producing the full moveset.

### Phase 2 transition — the second blade

Proposed 72-frame reveal, then 36-frame free punish window. No damage throughout the reveal.

| Time | Blender motion | Roblox effect |
|---|---|---|
| f0–18 | Stops in a stable asymmetric pose, off-hand opens; cape settles | Several motes drift inward toward off-hand |
| f19–36 | Off-hand follows the future blade axis | One narrow beam/line sketches blade length |
| f37–48 | Hand closes correctly around weapon; blade becomes visible | 3-frame white-lavender accent; materialize second mesh by sections |
| f49–72 | Opens into dual stance; cape flares once then falls | Thin ankle ring; both Trails stay disabled until an actual attack |
| f72–108 | Held calm dual stance, reachable | Recovery dimming; optional sparse edge motes |

Second handheld blade is the core P2 change. Floating blade choreography in the refinement is a separate optional addition; do not automatically add an army of swords alongside dual wielding. In the initial version, one spectral echo can express the floating-blade idea without another physical weapon rig.

### Phase 2 attacks — fuller dance, preserved openings

Keep P1 attacks with dual-weapon poses; never hide changed reach behind an unchanged warning. Slightly richer ribbons and cape accents replace blanket brightness increases.

| Move | Timing at 30 fps | Animation/VFX | Fairness |
|---|---|---|---|
| Twin Echo | Tell 30; physical hit f30–38; echo tell f38–56; echo hit f56–64; recovery 36 | One physical slash, then one spectral crescent repeats the committed path; use clearly different hollow outline for the echo warning | Full delayed-hit warning; same fixed path; echo stops before recovery |
| Dual Blade Phrase | Tell 30; first hit 8; second tell 18; second hit 8; recovery 36 | Leading blade sweeps, off-hand answers in complementary diagonal; cape follows rather than covering both | Two hits maximum; distinct cues; no surprise third slash |
| Grand Dance | Three separate phrases below | Repeatable choreography; each phrase has a recognizable ending pose | Genuine openings between phrases; no ten-hit uninterrupted string |

Grand Dance A: step → forward glide → horizontal slash → held recovery (30 frames).

Grand Dance B: slow pivot → one sweep → backward glide → held recovery (30 frames).

Grand Dance C: cape turn → visible committed acceleration cue → crossing slash → delayed echo with its full tell → deep settling recovery (48 frames).

Each phrase starts with at least 30 warning frames for its first hit and meets the standard pause between strings. The visual performance can continue with gentle cape settling during recovery, but she cannot attack, evade the punish zone, or become invulnerable then. Preserve the repeatable order. Avoid random teleport destinations or changing it each attempt.

Low-health escalation remains inside P2: greater aerial grace, more deliberate cape extension, one brighter active blade accent, and varied harmless repositioning. Preserve all warning/recovery timings. Do not interpret the refinement's “minimal recovery” wording as authorization to violate the current combat contract.

### Defeat

About 3.5–4 seconds: damage cancels; blades lower; cape settles; sparse particles drift away; she takes one final deliberate step; the two blades dissolve in sequence; the body fades after the cape falls still. No ragdoll or explosion. Let the final pose carry the emotion.

## 7. Accompanying effect assets

| Asset | Build/export details | Use |
|---|---|---|
| Thin annular ring | Center origin, flat plane, small thickness, radial UVs, scale reference | Phase reveal and impact accents |
| Crescent ribbon | Curved narrow strip; pivot at arc center; tapered ends, gradient UV along length | Wing sweep and sword accent |
| Seraph geometric seal | Simplified sacred linework with open negative space; separate glow split | Halo alignment and transition |
| Feather shard | Small silhouette-readable feather blade; pivot at base; low-poly | Harmless debris or explicitly registered projectile |
| Dancer echo crescent | Reuse crescent geometry with distinct outline/texture, not a full translucent boss clone | Delayed attack warning/active shape |
| Second blade reveal segments | Use the actual second blade split logically along its length | Controlled assembly/dissolve without Blender-only shader tricks |
| Ground sector/lane indicators | Procedural Studio geometry or shared textures with precisely recorded dimensions | Every damaging area warning; matched to server volumes |

Static FX meshes export separately from body actions. Blender preview objects must be tagged so they cannot accidentally enter the character FBX. Runtime cosmetic geometry is noncollidable; gameplay uses separate explicit volumes. UVs and material behavior are tested in Studio, not assumed from Blender emission renders.

## 8. Production sequence and acceptance gates

1. **Reconcile local plans.** Read current `AGENTS.md`, `CLAUDE.md`, `INDEX.md` and targeted architecture/art documents. Locate local branches/files. Produce a short conflict list, preserve approved choices, and choose a task branch using the current repo rules. Do not merge unrelated branches as part of this task.
2. **Prepare parts and silhouette.** Generate bodies, extras, rigs, and manifests through the existing framework. Render front/side/back and player-scale views, wing cloak/orbit poses, cape flare, and dual stance. Owner reviews silhouette before expensive animation production.
3. **Round-trip one small rig.** Import one Dancer body/cape/blade pose and one Seraph body plus wing module. Verify export size, weights, retained sockets, root/pivot placement, and material splits.
4. **Build two complete prototypes.** Dancer Opening Waltz and Seraph Wing Sweep, including real active/recovery states and Roblox effects. Make detachment and second-blade reveals as short technical proofs before expanding P2.
5. **Review readability in game.** Third-person and lock-on cameras; front/side/rear; near/far; actual Astral lighting; low quality and mobile-sized viewport. Owner reviews motion and effect density.
6. **Expand approved actions.** Fill moveset/animation manifests, build transitions and remaining attacks, then encounter behavior using existing runtime conventions. Separately review any world boss selection change.
7. **Validate and document.** Run framework checks, appropriate Luau checks/tests for changed runtime behavior, export/event checks, and Studio encounter tests. Update the moveset, roster, index and work log according to repo rules. Do not mark Studio tests passed without actually running them.

Acceptance criteria:

- All body/weapon/cape parts have clean rest poses and no unintended clipping across exported frames; both blade grips stay attached, and pivot feet behave as intended.
- Wing modules detach without a visible transform jump, preserve the two-tier P1 silhouette, and never remain accidentally welded to the body in P2.
- All rigs/parts/socket names and clip identifiers match the manifest; every required marker has the intended timing after import.
- Bone-skinned appearances and server hit volumes agree; warning footprints describe real attacks rather than approximate decorative arcs.
- Each move has a reachable safe response and a reachable sword punish window; no damaging visual persists into declared recovery.
- Required tells remain visible without bloom, decoration, or full-quality particles. Cape/wing geometry cannot hide all cues.
- Test interruption, phase threshold during a move, defeat during a barrage, two viewers, late network events, streaming, despawn, and repeated debug previews. No duplicate hits, continuing hazards, missing phase modules, or leftover trails.
- Profile one whole boss encounter on representative low/mid hardware, including transition transparency costs. Reduce decorative layers before reducing readable tells.

## 9. Agent handoff text

> Implement the attached Astral boss production plan through LUCKBOUND's existing enemy framework. First read the current agent/index instructions and locate any local Seraph/Dancer plans; report material conflicts rather than silently overwriting them. Treat this document's timing, size, budgets, and phase allocation as proposed design data until owner review. Preserve six independently movable Seraph wing modules, the concept's two-tier silhouette, Dancer's animated cape, and her second handheld blade in P2. Use headless Blender and the shared modeling/cloth/pose/export helpers. First deliver player-scale silhouette renders, a body/wing/cape Studio round-trip, and the two prototype attacks specified here. Build accompanying meshes and socket/timing manifests, then wire Roblox effects through the existing shared system. Server controls damage and movement; clients render bounded effects. Keep real tells, safe zones, and punish windows. Avoid unapproved extra phases, floating sword swarms, unavoidable overlapping attacks, and arbitrary particle density. Report generated files, validation results, and any Studio checks that remain pending. Ascendant and Winged Sentinel are outside this implementation pass.

## 10. Technical references

- Roblox rigging/skinning: https://create.roblox.com/docs/art/modeling/rigging — imported bone influences; skinned deformation does not change collision shape.
- Roblox FBX export settings: https://create.roblox.com/docs/art/modeling/export-requirements — rig/influence export, scale handling, leaf-bone setting.
- Roblox animation events: https://create.roblox.com/docs/animation/events — event markers and `GetMarkerReachedSignal()`.
- Roblox effects: https://create.roblox.com/docs/effects — Attachment-based lights, ParticleEmitters, Beams, and Trails.

These references support the engine workflow. The boss choreography and proposed production budgets are authored design choices.
