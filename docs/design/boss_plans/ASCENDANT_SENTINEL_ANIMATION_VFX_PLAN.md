# LUCKBOUND — The Ascendant & The Winged Sentinel
## Blender construction, animation, and Roblox VFX production plan

Review draft • 30 September 2026 • Agent handoff companion to `Astral_Boss_Animation_VFX_Plan.md`

## 1. Purpose and authority

Extend the existing bosses with animation-ready parts and coherent effects. Preserve their current silhouettes, weapons, existing action names, and the shared enemy framework. This document is a specification, not a claim that any new asset or runtime behavior has been built or tested.

The owner requested the same planning treatment as Astral Seraph and Celestial Dancer, with spectacle increasing by rarity without visual clutter. These two bosses already have source scripts and exported assets. Begin with an audit and additions; do not rebuild them from scratch.

### Sources inspected

Repository: `C-S-Labs/LUCKBOUND`, remote main source read on 30 September 2026; the preceding inspection identified main at `1001ec2`. Local/unpushed changes are outside this inspection and must be checked before implementation.

| Source | Relevant facts |
|---|---|
| `assets/source/enemies/ethereal_scape/ASCENDANT_MOVESET.md` | Guardian/transfiguration phases, staff and orb, cloth and grip details, hand-edited mesh warning, older and newer attack descriptions |
| `ethereal_scape/anims/the_ascendant/P1_CrescentReap.py` | Current attack is an overhead axe-like staff chop, not the older horizontal sweep |
| `ethereal_scape/anims/the_ascendant/P1_OrbCast.py` and `P1_SkyCast.py` | Existing cast poses, frame timings, `VFX_Cast`, spell origin |
| `ethereal_scape/the_ascendant.py` and `the_ascendant_orb.py` | Gold mask, robe, ribbons, crystal extremities, `StaffOrb`, `VFX_Orb` |
| `assets/source/enemies/sky_citadel/WS_MOVESET.md` | Lance duelist, phase-change choreography, tells/recoveries, lightning and aerial attacks |
| `sky_citadel/winged_sentinel.py`, `ws_lance.py`, `ws_anim_p2.py`, action wrappers | Wing/breakaway parts, lance anchors and split blade, existing transition markers |
| `src/shared/Util/WeaponFX.luau`, `Content/LightningRigs.luau`, `src/client/Controllers/LightningController.luau` | Existing data-driven charge state and cosmetic crackle; reuse these |
| Both biome `manifest.py` files | Existing boss registration and extras order |
| `src/shared/Content/Worlds/EtherealScape.luau` / `SkyCitadel.luau` | World rarities are currently Uncommon and Epic, respectively |
| `docs/ENEMY_FRAMEWORK.md` and the Astral plan | Shared rigs, cloth, marker/export workflow, readable tells and punish windows |

**Separate world rarity from weapon rarity.** Ascendant inhabits the currently Uncommon Ethereal Scape; Sentinel inhabits Epic Sky Citadel. Their staff/lance drops are described as Legendary. A Legendary weapon does not automatically turn the entire encounter into Legendary or Mythic spectacle. Preserve the current classification until deliberately changed.

New effects, exact added events, particle targets, and reconciliation choices below are proposals. Existing source timings are labeled as such. Do not silently rebalance combat under an animation/VFX task.

## 2. Spectacle across the four bosses

| Boss | Signature visual | Normal attack composition | Transition centerpiece |
|---|---|---|---|
| Ascendant | Portal-eye staff orb, crystallizing hands, restrained robe/ribbon follow-through | One orb/weapon effect plus a precise floor warning when needed | Ivory cuirass releases to reveal crystal-veined core |
| Winged Sentinel | Angular wing posture, lance precision, cyan storm web | One active lance trail or narrow lightning pattern; quiet wings | Armor release, storm-web absorption, split-lance plasma ignition |
| Celestial Dancer | Dominant cape and learnable choreography | Thin ribbons and one delayed echo | Second blade assembles into the off-hand |
| Astral Seraph | Monumental silhouette and six moving wing modules | Large deliberate geometric compositions with visible empty space | Wings detach and establish an independent orbital formation |

Keep one dominant shape per attack with at most two supporting decorative layers. Required warnings are additional readability layers. Bigger silhouettes and more purposeful motion carry rarity better than screen-filling particles. Recovery dims energy to approximately 40% of active intensity using a shared consistent cue, not a literal mesh-color multiplier that makes dark materials unreadable.

No constant flashes, opaque shockwave discs, universal neon outlines, or full-screen color pulses. Ground warning shapes communicate actual attack boundaries; decorative outer fringes stay faint. Threat remains readable without bloom and without optional particles. Idle effects should be quiet enough that a tell is visibly different.

## 3. Shared Blender and runtime contract

### Extend the current pipeline

Use `assets/source/enemies/_framework/run.py` headlessly, the current body profile, `enemy_kit`, `anim_core`, pose/grip solvers, cloth bake, validation, render/preview, and exporter. Keep action scripts in the existing biome animation directories. Preserve manifest extras order and avoid creating a second incompatible rig pipeline.

Actions are in place. Server-approved root travel supplies lunges, glides, portal steps, vaults, and landings. Save intended travel as data for the combat controller and Blender preview; do not export travel and apply it again at runtime. Cloth/wing follow-through must be previewed against intended acceleration even when the exported body animation is in place.

Blender delivers geometry, weights, rigs, baked deformation, and clips. Roblox delivers particles, trails, beams, procedural floor warnings, mesh fades/scales, sound, optional local camera response, and authoritative hit volumes. Blender emission renders do not prove runtime appearance.

Preserve current rig names, rest transforms, pivots, material/glow splits, and weapon grip frames. Every vertex gets at most four bone influences; rigid armor stays rigid. Preserve the current project per-piece triangle cap and validator. Do not inflate the boss to a new ceiling for VFX work; record existing counts before adding parts. Geometry budgets in older documents and later owner preferences may differ: reconcile them rather than changing validation to fit.

Socket-helper bones must survive export using the framework's retained/pinned-anchor method. Verify real imported socket transforms while bones animate. Bake constraints/IK to supported keys; do not assume timeline markers, shader nodes, or simulated cloth transfer into Roblox automatically. Use the current exporter and verified Studio import workflow. Bone translation has caused problems in this project: use existing proven runtime charge/movement mechanisms instead of inventing new export assumptions.

### Timing and event data

Retain `Tell`, `HitStart`, `HitEnd`, `RecoverStart`; optional events include `VFX_Cast`, `VFX_Crescent`, `ArmourBreak`, `LanceIgnite`, `P2Start`, `Footstep`, and `WingBeat`. Added events below are proposed and must be supported by the timeline manifest and runtime listener. Recreate/verify Studio animation events rather than assuming automatic FBX marker conversion.

Store per action: clip ID, source fps, start/end, marker frames, committed target/path, sub-hit windows, warning duration, projectile lifetime, impact time, recovery, socket names, FX recipe and cleanup ownership. Source frame numbers below are the actual script's 1-based frames; duration is the difference between markers, not the count of both endpoints. Gameplay converts frames to seconds at 30 fps.

Server controls target choices, phase, movement, damage, counter activation, and confirmed hits. Clients render cosmetics from authoritative attack ID/start time/path and handle late messages by advancing/skipping expired visuals. Cosmetic Beams and Trails never grant hit authority. Skinned bone deformation does not alter physical collision; separate server volumes describe the real strike.

An attack instance owns its temporary objects, event connections, and effects. Cancel, stagger, death, phase change, despawn, and debug reset must clear them. Long-lived phase energy is owned by phase state, not a stale attack callback. Reward logic follows server encounter completion, not client dissolve completion.

### Warning and recovery rules

- At least 8 frames of a recognizable visual tell plus an audio cue before a damaging commitment.
- At least 18 frames of actual punish time after an attack or short string, and at least 0.5 seconds between strings.
- No more than three committed attacks before an opening. Special flurries in the old sheets require explicit reconciliation below.
- Aim/path locks before damaging motion; warning stays visible until release/impact. No invisible steering after commitment.
- Portal destinations and aerial landings are safe placements in sword range, with reachable escape routes. Validate actual collision and navigation; never place behind a wall or outside the arena.
- Decorative remnants cannot continue dealing unmarked damage during a declared opening. Explicitly decide whether a projectile is allowed to remain active during caster recovery; do not assume `HitEnd` at spawn ends its lifetime.

## 4. Ascendant — preserve the edited guardian

### Critical mesh provenance

The moveset explicitly says shipped FBXs come from the owner's hand-edited `assets/export/enemies/ethereal_scape/TheAscendant.blend`. The chest/center crystal were adjusted and `BreakawayGlow` removed. Running a full scripted rebuild/export would restore the old chest and overwrite that work.

Before modifying anything, locate the actual current `.blend` and any newer `_fixed` variants locally; compare dates, meshes, rig names and exported appearance. Keep the chosen authoritative scene intact. Generate actions separately and export them onto its compatible rig/meshes using the existing proven transfer workflow. Alternatively reconcile the generator with the edited geometry first, then prove identical before/after silhouette. File name alone does not establish which copy is newest.

Do not reintroduce `BreakawayGlow` merely because the generator still knows about it. Confirm the inner core and armor-break mesh still exist in the edited scene before designing the transition around them.

### Art identity

Ivory and unlit gold, crystal hands/feet/crown/hem, faceless gold mask with a narrow vertical glow slit, indigo robe lining, mint/teal back ribbons. **No hood and no halo** in the current body description. The staff head has a crescent around a portal-eye orb; that orb is the main casting focus. Use mint-white `#8CFFD0` and crystal blue `#7FC8FF`; gold remains unlit. Check against Ethereal Scape's bright cloud lighting so the spell silhouette does not wash out.

The latest action additions make the staff predominantly ranged, with the overhead chop as its close-range answer. Preserve this current identity. Ascendant's cloth is supporting motion; Dancer retains the largest, most theatrical cape.

### Parts and bones

| Existing component | Preserve | Addition or verification |
|---|---|---|
| Edited body and inner torso | Chest shape, central crystal placement, proportions | Verify P2 core is not occluded; keep a separate glow surface only where already compatible |
| Ivory `Breakaway` cuirass | Actual edited armor surfaces | Split/identify harmless debris chunks if not already available; no duplicate full armor underneath |
| Robe and four back scarves | Existing baked chains and trim weights | Tune follow-through for new casts and portal steps, not a new giant cape |
| Sanctum Staff | Crescent, haft grip frame, current shape | Verify base/tip anchors and keep hands clear of the head |
| `StaffOrb` | Existing separate mesh skinned to `Weapon_R` | Control orb glow as phase/tell data, not whole-staff overexposure |
| Crystal crown/extremities | Existing silhouette | Optional reusable small shard visual for transition/death; avoid rigging every crystal |

The source sheet records 154 bones after joint/orb additions: existing body, cloth, fingers and extras. Cloth includes 16 robe chains × 5 bones plus four scarves × 4. Inspect the actual authoritative scene before assuming those counts. **Do not add dozens of new bones just to hang VFX**; use existing sockets or a small verified addition.

Bindings to preserve/verify: `Weapon_R`, `VFX_Core`, `VFX_Eye`, `VFX_PalmL`, `VFX_PalmR`, `VFX_Orb`, and the documented `VFX_StaffBase`/`VFX_StaffTip` if actually present. The last two are documented socket expectations, not verified imported assets. Add and register missing ones deliberately. The orb socket belongs at the orb center and follows the staff, not the torso.

Maintain three-joint fingers, opposing thumb, forearm twist and solved grips. Any off-hand reversal uses release → rotate while free → re-grip; never spin the palm while gripping. Inspect inherited clipping/wrist reports rather than carrying them into new clips: the sheet records older chest/waist grazes and a severe wrist angle, but they may have changed in the re-authored action.

### Existing-action production recipes

| Action | Source timing | Body/secondary motion | Runtime VFX recipe |
|---|---|---|---|
| `P1_CrescentReap` | 60 f; Tell 3, Crescent 14, hit 17–22, recover 23–60 | Two-handed overhead lift/chop; low left follow-through; cloth settles; stable grip | Small orb/crescent charge, narrow downward blade ribbon during active frames, contact spark only on confirmed hit |
| `P1_OrbCast` | 54 f; Tell 3, Cast 12, hit/spawn window 18–22, recover 24–54 | Staff pulls back then points/thrusts; robe response subdued | Orb gathering pulse; one readable mint-blue bolt from `VFX_Orb`; tiny release ring, no giant beam |
| `P1_SkyCast` | 66 f; Tell 3, Cast 20, release 34–40, recover 42–66 | Staff rises overhead then makes a short downward jab; ribbons catch up | Orb pulse plus ground marks; a selected spell recipe supplies actual impact timing/volumes |
| Idle/Walk/Strafes | Existing built actions | Whole-body weight shifts, staff held correctly, free arm clears robe | Sparse slow hand/core motes, no attack trail |
| Hit/Stagger/Recover | Existing built additions | Distinct flinch vs held broken-poise stance | Cancel active attack cosmetics; lower charge glow; no fake blast on every hit |

**Spawn window is not projectile damage lifetime.** OrbCast's `HitEnd` at f22 ends the release window. The gameplay projectile needs an independent authoritative lifetime/range/collision contract. For the first readability prototype, show bolt travel and caster recovery in an isolated test; choose and document whether the bolt expires before recovery or remains as a readable single threat. It must not leave an unmarked lingering hazard.

SkyCast has no single implied spell: map the action to one named ground-spell recipe in encounter data. Do not spawn lattice, starfall and Crown Flare simultaneously because the script comment mentions all three. Cast animation release and floor impact can have separate event times.

### OrbCast prototype cue sheet

| Source frame | Animation / event | Effect |
|---|---|---|
| f1–2 | Guard | Quiet orb baseline |
| f3 | `Tell` | Small mask slit flash, crystal pulse, clear tonal cast cue |
| f12 | `VFX_Cast` | Particles gather narrowly into orb; avoid making the staff head a white blob |
| f16 | Proposed `Commit` | Lock aim/path in attack data, keep warning visible |
| f18 | `HitStart` | Spawn one bolt from the current socket transform; small release accent |
| f22 | `HitEnd` | Stop spawning; projectile owns its own remaining lifetime |
| f24 | `RecoverStart` | Dim palms/orb, hold readable follow-through; no second cast |
| f54 | Action end | Return to guard; optional motes finish on a bounded lifetime |

First build this and the existing overhead chop end to end. These prove staff sockets, skinning, grips, cast origins and runtime timing without committing to the entire older moveset.

### Additional attacks — compatibility plan

These are existing design-sheet moves, not confirmed finished actions. Resolve the older melee-first sheet versus the newer caster-first implementation before enabling them. Reuse cast clips only where pose and recovery fit; clone/re-time a clip with a new ID when behavior needs different timing.

| Move | Older sheet T/A/R | Proposed animation and effects | Required reconciliation |
|---|---|---|---|
| Rising Crescent | 12 / 5 / 26 | Low staff draw → upward diagonal; thin rising ribbon | Dedicated strike pose; no instant follow-up after overhead chop recovery |
| Portal Step → Thrust | 16 / 6 / 28 | Sink at departure → appear at marked arrival → butt-first staff thrust | Early arrival warning, validated placement, committed facing; root travel is server-owned |
| Sanctum Lattice | 18 / 8 / 34 | Staff plant/palm pose or approved cast variant; three small crystal pillar columns | Generic SkyCast has different timings and only 24 f recovery; cannot substitute unchanged |
| Crown Flare | 8 / 26 counter window / 20 | Staff vertical, crown cue; mask signal remains distinct | Counter only activates on qualifying server hit; answer uses full Rising Crescent tell |
| Twin Reap P2 | 12 then 8 / 5+5 / 30 | Two deliberate staff strokes, blade ribbon per stroke | Decide whether these remain horizontal arcs or become a new overhead pattern; do not label a chop as a sweep |
| Portal Chain P2 | 14 per arrival / three 6-f thrusts / 40 | Three marked short portal steps; one staff strike each | Every destination has full warning and reachable escape; no accumulated opaque portals |
| Starfall Lattice P2 | 20 / two 8-f waves / 36 | Upward cast, five crystal columns in two labeled floor groups | Full warnings for both groups, gap/impact times explicitly recorded; safe lane survives both |
| Crescent Wave P2 | 16 / 10 travel / 30 | One low staff launch, narrow traveling crescent | Confirm whether it remains appropriate to caster-first design; actual collision height must permit intended escape |
| Ascension finisher | 24 / four 5-f Reaps / 60 | Crown/hands brighten; deliberate final sequence → kneel | Four attacks conflicts with three-attack limit; propose two strokes → opening → two strokes → final 60 f kneel |

Retain phase boundary at 55% HP, no damage during transfiguration, and +25% damage taken without cuirass as current sheet settings unless an explicit balance task changes them. No new third phase. Jump/roll counterplay in the old sheet must be verified against actual player capabilities and collision heights.

### Transfiguration cue sheet

Existing design duration: 70 frames, followed by 60 frames (2 seconds) of vulnerable stillness. Transition action is listed as unbuilt in the sheet.

| Source time | Blender / parts | Roblox effects |
|---|---|---|
| f1–20 | Sinks to one knee, staff supports weight | Fine portal-light veins rise from hands/feet; soft rising tone |
| f21–29 | Torso braces; robe follows | Core charges under armor, no damaging floor mark |
| f30 `ArmourBreak` | Edited cuirass is removed; identified chunks move harmlessly | Small mint-white accent and a few crystal shards; avoid fire/smoke explosion |
| f30–50 | Crystal inner torso revealed; crown opens visually through light | One short core pulse, narrow upward motes |
| f50–70 | Rises into slight hover within sword range | Glow settles to P2 baseline, transition particles fade |
| f70 `P2Start` onward | Holds vulnerable pose for 2 seconds | Shared recovery dimming; no portal escape or cast |

Debris flight in Blender is a preview, not proof that object keys will import. Use a registered rigid debris recipe/parts with deterministic cosmetic movement and clear TTL. Restore correct armor state on debug reset. Replacing the edited chest is outside this task.

### Defeat

About 4 seconds: cancel casts/projectiles according to encounter cleanup; staff lowers; crystal crown loses glow and sheds a few harmless shards; robe settles; hands/core dim; a thin portal ring expands and fades as crystal motes rise. Preserve the edited body silhouette. Reward timing follows server rules. No huge implosion, no halo added to this boss, no floor-wide portal hazard.

## 5. Winged Sentinel — precision and plasma

### Art and parts

Fast lance duelist with wing-assisted straight-line attacks. Preserve the approximately 3.55 m source proportions and armored/inner-aether silhouettes; verify imported size against a player instead of treating meters as studs. Palette: cyan `#7FF6FF` with violet `#9C7BD8` accent. Generated lightning rig currently uses its own narrower cyan value; preserve it unless the palette is deliberately reconciled. Graphite/stone armor remains solid and mostly unlit.

| Existing component | Keep | Animation / FX requirement |
|---|---|---|
| Body and armor chunks | Current R15-named rig and `Break_*` pieces | Small stance compression, precise thrust; chunks leave harmlessly in P2 |
| Wings | `WingL`, `WingR`, tip children | Fold/flare/brace for thrusts; open during P2; no Seraph-like detached wings |
| Faulds | Existing two-bone front/back chains | Follow-through on vault/landing without intersecting thighs/lance |
| Aether Lance | `Weapon_R` grip, separate haft/blade/glow pieces | Stable one-hand/two-hand holds, clear point direction |
| Blade halves | `LanceBladeL`, `LanceBladeR` | Existing charge controller owns opening; animation must not fight it |
| Lance halo | `LanceHalo` | Existing contraction/absorption reveal; independent from a body halo |
| Storm web | Real mesh plus `Web*`/`Arc*` anchor Beams | Reuse generated lightning data and client controller; avoid duplicate beam networks |

Sockets: preserve `VFX_Core`, `VFX_Eye`, `Weapon_R`, wing tips, existing `Web*`/`Arc*` anchors and lance-half tips. Register explicit blade trail base/tip and plunge origin if missing. Give the trail a stable span representing the actual active blade, with appropriate P2 reach. Do not span both outer wings and call it a weapon trail.

### Charge ownership

`WeaponFX.setCharged(model, on)` already shows the plasma blade, opens the halves and enables P2 arcs; `LightningController` reshapes cosmetic crackle. `LightningRigs.luau` is generated by `ws_lance.py` and must not be edited by hand.

Use one charge-state owner. Bake hand/body poses for the charged silhouette, but avoid competing blade-half animation and per-frame charge transforms. Transition ramps should use the existing charge mechanism or a small compatible extension; preserve final state and off/reset behavior. Charge must work for boss, player-held weapon and display without attaching encounter-only effects to every weapon instance.

The weapon's Phase1 crackle can persist as an idle identity cue. This is separate from the **damaging attack Trail**, enabled only for active strikes. Low graphics can remove secondary crackle but must preserve actual plasma reach and readable attack tells.

### Existing Dash Lunge prototype

`P1_Lunge.py`: 44 frames, Tell 1, wing flare 10, HitStart 13, HitEnd 19, RecoverStart 20. Source intends runtime travel roughly 6 m on the lunge line with 2 m overshoot; measure actual game scale before using those distances.

| Source frame | Body/wing | Runtime / VFX |
|---|---|---|
| f1 `Tell` | Ready → compress stance, lance draws back | Visor flash plus restrained cyan pulse and clear wing/metal cue |
| f8 | Deepest preparation | Wings lift, point remains readable |
| f10 `VFX_WingFlare` | Wing flare | Small tip feather accents, no full wing particle veil |
| f12 | Proposed `Commit` | Freeze path/aim; warning still visible |
| f13 `HitStart` | Shoulder/arm thrust | Server lunge begins; narrow lance Trail enables |
| f15 | Full extension | One short tip streak; contact sparks only for confirmed impact |
| f19 `HitEnd` | Attack passes target | Trail disables; no lingering damaging lane |
| f20 `RecoverStart` | Overshoot/braking posture | Glow dims; boss remains punishable and does not instantly turn back |
| f44 | Guard | Cleanup complete; no new string until shared pause condition holds |

P2 Blink Lunge reuses this language with its own timings and a single sparse afterimage. Prefer a simplified silhouette/wing-lance snapshot over repeatedly cloning the whole complex animated rig.

### Phase 1 recipes

Timings here reproduce the sheet; inconsistencies are flagged below rather than silently applied.

| Move | Sheet T/A/R | Animation and VFX | Readability / cleanup |
|---|---|---|---|
| Dash Lunge | 12 / 6 / 24 | Stance compression, wing flare, straight lance streak | Committed line, overshoot, stopped Trail during recovery |
| Twin Thrust | 9 then 7 / 4+4 / 20 | First thrust → grip retracts → second thrust; two short trails | Second tell must reconcile to at least 8 f; sheet prose also disagrees about which tell is longer |
| Crescent Sweep | 14 / 8 / 28 | Draw lance low, turn torso through a 200° arc | One narrow crescent fades in 8 f; safe flank remains visible |
| Wing Vault → Plunge | 16 / 10 / 36 | Crouch/fold → brief vault → lance plants, wings brace | Ground circle through tell; one impact spark ring, sparse shards; no damaging residue |
| Parry Stance | 8 / 30 counter / 20 if unused | Lance upright, controlled halo turn, taut wings | Counter cue differs from recovery; successful response uses full 12-f lunge tell |
| Guard Break Bash | 10 / 5 / 22 | Pommel rise and short committed bash | Focused pommel pulse; distinct sound/shape for unblockable cue; server condition unchanged |

Preserve the 1.2-second stagger/breather after the sheet's third committed attack. Combo definitions must count damaging commitments, not just names of action files. Twin Thrust plus Plunge is three hits/commitments at most; do not accidentally add another lunge before recovery.

### Phase change — existing 60-frame choreography

| Source frame | Parts / animation | Effect |
|---|---|---|
| f1–18 | P1 stance → brief hunch, wings clamp | Core dims; quiet electrical tension |
| f19–29 | Torso braces | Crackle focuses into lance web; avoid extra lightning everywhere |
| f30 `ArmourBreak` | Armor chunks leave; inner aether body revealed | Small core flare and harmless fragments |
| f30–44 | Lance halo contracts; web draws into blade; halves open | Reuse storm-web/charge data; one directed absorption accent |
| f44 `LanceIgnite` | Plasma blade visible; hands/weapon pose stable | Short cyan-violet ignition line, restrained white accent |
| f45–60 | P2 stance; wings extend | Particles clear; plasma settles into clean blade silhouette |
| f60 `P2Start` | Vulnerable stationary stance for 2 seconds | Recovery dimming while preserving the plasma's actual shape |

The current script says debris object motion is Blender-only preview. Implement real Studio debris visibility/spawning/removal; a successful imported body clip is not a successful armor-break system. Verify charge state is consistent for all viewers, late joiners, debug previews and resets. No damage during transition.

### Phase 2 recipes

| Move | Sheet T/A/R | Animation and VFX | Readability / cleanup |
|---|---|---|---|
| Blink Lunge | 9 / 5 / 20 | Sharper wing-assisted thrust, one 10-f fading silhouette echo | Echo harmless; visible tell survives its speed |
| Plasma Arc | 12 / 8 / 26 | Larger 240° lance arc with increased reach | Narrow ribbon matches the real +1.5 m reach after scale conversion; no opaque full disc |
| Storm Dive | 18 / three 8-f dives with 14-f intervals / 40 | Rise/spread → three marked dives → grounded blade plant | Each landing gets its own full warning; explicitly resolve whether 14 f means gap or start spacing |
| Aether Fork | 15 / 6 / 30 | Lance lifts and channels; three curved bolts descend from its tip | Three rune marks, cyan lightning with violet core; no map-dependent sky strike |
| Riposte Stance | 6 / 24 counter / 18 | Compact guard pose, controlled halo cue | Six-frame tell conflicts with shared minimum; propose 8 f before activation |
| Desperation Flurry | 20 / five 4-f thrusts / 60 | Wings wrap then reveal precise final sequence → kneel | Five commitments conflict with three-attack maximum; propose 3 hits → opening → 2 hits → 60-f final kneel |

For Storm Dive, each arrival is inside sword range and the final landing stays grounded throughout recovery. Bolts/pillars belong to the boss recipe and work on the base chunk kit; no reliance on Stormhawk/scenario effects. Preserve P2 boundary at 40% total HP and +25% incoming damage without armor unless an explicit balance change is approved.

### Defeat

About 4 seconds: cancel hazards; plasma/crackle dims; Sentinel kneels supported by lance; wings droop; only a few glow shards release; small cyan upward dissolve and one fading halo accent. Keep the lance silhouette visible long enough to establish its drop identity. No damaging feather rain or huge lightning storm after health reaches zero.

## 6. Moveset conflicts to resolve before full encounter wiring

These are material source conflicts, not reasons to stop preparing parts/prototypes.

| Conflict | Safe preparation now | Proposed resolution for review |
|---|---|---|
| Ascendant older horizontal Reap vs current overhead chop | Preserve existing action/mesh and author overhead VFX | Update moveset description/counterplay to match chop; keep any horizontal move under a distinct approved action ID |
| Ascendant older melee duelist vs current orb-caster additions | Build OrbCast/SkyCast socket recipes | Define one caster-first phase roster; do not automatically enable every older move |
| Ascendant table timing vs current cast clips | Manifest actual source marker frames | Use separate cast variants where lattice recovery/timing requires them |
| Ascendant edited `.blend` differs from generator | Inspect/keep authoritative mesh, transfer compatible actions | Reconcile generator only as a deliberate geometry-preservation task |
| Ascendant “only ranged move” statement vs OrbCast/SkyCast | Preserve newer built casts | Correct stale prose during documentation reconciliation |
| Sentinel 7-f Twin Thrust follow-up and 6-f Riposte tell | Prepare poses/effect recipes without enabling unsafe variant | Raise to at least 8 f; choose whether second thrust should be longer than first |
| Sentinel Storm Dive 14-f interval ambiguity | Model/preview dives with separate timeline entries | Specify start-to-start vs gap, ensuring every landing's warning meets the minimum |
| Four-hit Ascension / five-hit Flurry vs three-attack rule | Build key poses and separate phrase clips | Divide into phrases with real openings, or obtain an explicit intentional exception |
| Combo overrides skip recovery of standalone action | Keep standalone actions and recovery markers | Combo metadata defines actual recovery; cannot show “open” dimming while secretly chaining |

Never silently treat a stale sheet as more authoritative than a later owner edit. Record decisions and consolidate one moveset per boss after review. Do not broaden this task into rewriting both encounters' combat balance.

## 7. Shared accompanying FX assets and recipes

| Asset / recipe | Blender work | Roblox work |
|---|---|---|
| Thin ring | Center pivot, radial UV, small thickness, open center | Departure/arrival portal boundary, phase accent, impact spark ring |
| Tapered crescent | Narrow arc strip with tapered ends and gradient UV | Sword/staff/lance accents with per-boss palette and correct strike plane |
| Ascendant bolt shell | Optional simple crystal/ribbon shape, low polygon count | One projectile body and streak from `VFX_Orb`; authoritative path separate |
| Crystal pillar | Small reusable column/shard assembly, clear vertical silhouette | Spawn at marked point, rise/dissolve with explicit active lifetime |
| Crystal shard | Reuse current crystal visual language, simple pivot | Harmless transition/death fragments; bounded count/lifetime |
| Armor debris | Derive from actual existing removable armor, record part names/origins | Hide source armor once; move cosmetic fragments, fade and remove |
| Sentinel lightning | Preserve existing storm-web meshes and anchor definitions | Reuse `WeaponFX`/`LightningController`; Aether Fork is a separate bounded attack recipe |
| Sentinel afterimage | Simplified silhouette assembled from existing shapes if needed | One snapshot per dash, no animated rig clone swarm |
| Ground marks | Usually use shared textures/procedural Studio geometry | Exact footprint, full warning duration, safe lane and committed destination |

Static FX meshes export separately. Tag preview-only objects so they never accidentally enter boss FBXs. Cosmetic objects are noncollidable and excluded from gameplay raycasts/hit queries where appropriate. Validate thin surfaces from front/back and at ground-level cameras; do not assume a Blender plane is visible from both sides in game.

### Runtime recipe schema

Each named recipe records: owning boss/action ID; event/phase; origin binding; local offset and orientation; target/path source; warning shape; active volume reference; components; color/texture; scale; duration; live-count target; low-quality replacement; cancellation behavior. Recipes should be data where the existing system allows it, with reusable code for rings, bursts, trails and debris. Avoid copy-pasted emitter construction in each attack script.

Proposed initial aggregate decorative particle targets, to profile rather than treat as platform guarantees:

| Boss | Normal combat | Brief transition | Light |
|---|---:|---:|---|
| Ascendant | About 50 live | About 110 live | At most the existing core light |
| Sentinel | About 90 live | About 180 live | At most the existing core light |

Keep the framework's approximate per-effect ceiling of 150 live particles as well. Count all emitters together; existing lightning Beams and large transparent meshes require separate profiling. On low quality reduce motes, debris, echoes and secondary crackle first. Preserve plasma geometry, orb origin, every warning, and real hazard boundaries. No added global lighting effects per attack.

## 8. Deliverables and verification

### Agent delivery checklist

1. Short audit: authoritative local branch/mesh, existing vs missing parts/sockets/actions, move conflicts, current triangle/bone counts and runtime effect integration points.
2. Updated per-boss production manifest with exact socket bindings, part provenance, source action timings, separate travel/hazard timing and event ownership.
3. Non-destructive source scene changes and action/FX generation scripts, plus FBX exports made from the correct mesh.
4. Review renders: existing body front/side/back/player-scale; cast/chop/lunge extremes; phase reveal; armor removal; cloth/wing settling.
5. Two end-to-end prototypes: Ascendant OrbCast plus overhead chop, and Sentinel Dash Lunge with existing charge/transition proof. Visualize warnings and server hit volumes during development.
6. After review, remaining compatible move variants, transitions and death effects; consolidated movesets and asset registration.
7. Verification report distinguishing source validation, visual Blender review, imported Studio checks and actual runtime playtests. Update current index/work log conventions. Do not mark a Studio check passed from a rendered video alone.

### Acceptance gates

- The owner's edited Ascendant chest/crystal remains intact; removed glow parts do not reappear. Rig/action transfer does not quietly replace the mesh.
- Grip never slips or flips while held; wrists/shoulders stay within the profile's constraints; cloth/armor/weapon clearance is checked across every exported frame.
- Both cast effects start at the actual moving `VFX_Orb`; lance trail spans match closed/charged reach; anchors follow deformation properly after import.
- Armor breaks remove the correct source parts once, reveal the intended inner body and restore on reset. Debris is harmless and self-cleans.
- Sentinel charge has one owner; no double-opening, transform jitter, duplicate crackle, or missing charged state on another viewer.
- Every imported event matches its source manifest. Sub-hits, projectile impact and recovery are explicitly timed rather than inferred from a generic animation event.
- Every attack warning is clear at low graphics and mobile-sized views in actual biome lighting; targets can reach safety and then punish in sword range.
- Test interruption, poise break, phase threshold during attack, death with an active spell, streaming/late events, two viewers, despawn and repeated debug previews. No leftover trails, duplicate hazards or unbounded spawned objects.
- Profile full transitions and multi-hit sequences on representative devices, including transparent overdraw and existing beam count. Reduce decoration while retaining combat information.

## 9. Copyable agent handoff

> Extend The Ascendant and Winged Sentinel using this plan and LUCKBOUND's current enemy framework. Read current agent/index instructions and audit local/unpushed boss changes first. Preserve the authoritative hand-edited Ascendant `.blend`; do not overwrite its chest/crystal or restore removed `BreakawayGlow` by blindly running the generator. Keep the newer overhead `P1_CrescentReap` and orb-caster animations; flag the older melee-first moveset conflicts. Reuse Sentinel's existing `WeaponFX`, generated lightning data, lance charge controller and wing rig. Deliver missing part/socket/timing manifests and Blender/Studio prototypes before expanding every attack. Use server-owned damage/movement and bounded client effects. Preserve clear tells, real recovery windows, valid portal/landing placements, and single-owner charge transforms. Treat proposed timing corrections, phrase splits and effect budgets as review proposals; do not silently change combat balance. Provide generated files, before/after renders, exact checks run and pending Studio tests. Keep spectacle focused: crystal transfiguration for Ascendant, precision/plasma ignition for Sentinel, with Seraph/Dancer retaining Mythic-scale composition.

## 10. References

- Existing repo paths listed in §1 are the content and pipeline references.
- Roblox rigging/skinning: https://create.roblox.com/docs/art/modeling/rigging
- Roblox export settings: https://create.roblox.com/docs/art/modeling/export-requirements
- Roblox animation events: https://create.roblox.com/docs/animation/events
- Roblox effects: https://create.roblox.com/docs/effects

Engine references support the workflow; new choreography/effect targets in this document are proposed art decisions. No boss assets, branch merges, or encounter balance were modified by preparing this plan.
