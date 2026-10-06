# LUCKBOUND — Project Status

**Last updated:** 2026-09-30 · slimmed for token use. The full previous version, with every closed item and walk
report, is `docs/archive/STATUS_HISTORY.md`. Read it only by section, when an item below points to it.

> **New conversation?** Read `INDEX.md` → `AGENTS.md` → the top entry of `docs/WORKLOG.md` → this file.

---

## 1. Where the project stands

- **Movement refinement (2026-10-05, `agent/player-movement-refinement`, local only):** free input travel is independent of visual facing; free-ground speed ramps are zero while lock-on, weapon locks and hard-landing response retain their profile settings. Roll remains 18 studs with 0.52s execution; air dash is 70 studs/s for 0.32s with one-shot ordinary-air handoff. Generated Run poses reduce modeled bob and a separate forward Sprint uses measured stride speed. First owner walk: movement feels improved; immediate jump-dash incorrectly rolled and expedition legs felt fast. Follow-up fixes intentional-jump airborne classification and low-dash floor sensing, lowers expedition walk/sprint to 15/23.85 studs/s, and adds 15% forward Run/Sprint arm swing with unchanged stride matching. Targeted suite: **1,138 passing**. Owner Studio acceptance is pending at TESTING.md Test K2; this is not merged/pushed/published.

- **Production generation migration (2026-10-01, agent/procgen-production):** server-owned single-flight templates, safe local visuals/fidelity fallback, seed working sets with six bounded workers and cached/deferred presentation. 1,063 units, 300 layout comparisons, 4,280 loader comparisons; Studio cache/fidelity/worker/anchor/client invariants and all30 VV rotations/collision samples pass. Cold seed1 grounding VV0.366s/SC7.199s/ES7.317s; reuse0.366/1.315/1.317s with zero API calls. Six-map creation/Precise310 -> 64, visual-only Precise140 -> 0, no duplicate preparations. Owner accepts retaining the pipeline (2026-10-02): VV fresh/reuse/random seed appeared instantaneous; SC first/new seed about 3-4s with instant replay, tested railings and both boss arenas correct; ES first about 4-5s, reuse/new seed nearly instant, tested stairs/railings/chunks correct; quick re-entry carries no old attributes. These are manual estimates, not a benchmark rerun. Explicit atmosphere/streaming/catalogue coverage and published-server/native memory validation remain open. No push/merge/save/publish; original benchmark branch preserved. See GENERATION_MIGRATION.md.

- **ES enemies handed to Codex (2026-09-30):** read `assets/source/enemies/ethereal_scape/CODEX_HANDOFF.md`; Ascendant work waits on the owner's updated spec/mesh.
- **Boss animation/VFX (2026-09-30, docs only):** `docs/BOSS_ANIMATION_VFX.md` is the universal contract for every boss; per-boss work orders are in `ASCENDANT_MOVESET.md`, `WS_MOVESET.md` and `astral_reach/ROSTER.md` (Seraph, Dancer: not built). Ascendant work waits on the owner's updated spec and mesh.

- **UI overhaul (branch `agents/UI-overhaul`, 2026-09-29):** the whole player UI moved to the SIGIL visual language
  (`client/UI/Sigil/`): HUD, chat, leaderboard (Fate level column), universal menu, the Fate Engine main menu with
  sub-sigils, the loading/title screen and the C&S Labs ident. Owner walked it in Studio; present in frozen main PR #149 and retained in this integration. Shop,
  Archive, Fate Tree and Rebirth are still preview panels inside their sub-sigils. See the WORKLOG entry for leftovers.

- **Phase 1 is complete** (hub, roll, onboarding, saves, UI, events; movement now uses main's own controller, single jump, roll/backstep and air dash). The build spec §7
  amendments that opened later work are §7.1 expedition entry, §7.2 parties as their own server, §7.3 scenarios,
  §7.4 caps, §7.5 loot and §7.7 universal map generation (2026-09-27).
- **Worlds you can enter:** Verdant Valley (30-piece separated kit — corrected sockets validated across approximately eight owner-tested seeds; broader fidelity review pending), Sky Citadel
  (36-piece chunk kit, walked and verified, with ambience, props, chests and the vault) and Ethereal Scape
  (**41-piece hybrid kit** — floating isles + temple + meadow, 2 landmarks, 2 miniboss arenas, 6 backdrop
  pieces with drifting cloud props, height variation — on the §7.7 generation blueprint, 2026-09-27; final
  reviewed multipart kit, shrine room and BASE scenery — **owner authorized integration**). Emberfall and Astral
  Reach have no map yet (Astral Reach's design scheme and both bosses are locked in `docs/biomes/ASTRAL_REACH.md`; animation/VFX work orders in `assets/source/enemies/astral_reach/ROSTER.md`, 2026-09-30; unbuilt).

  | Id | Rarity | Weight | Phase | Map | Enterable? |
  |---|---|---|---|---|---|
  | `VERDANT_VALLEY` | Common | 6000 (60%) | 1 | chunk kit, 30 pieces — separated terrain/props/collision; socket Studio pass complete | ✅ |
  | `ETHEREAL_SCAPE` | Uncommon | 1500 (15%) | 1 | chunk kit, 41 pieces — hybrid isles/temple, §7.7 blueprint, uploaded IDs retained | ✅ |
  | `EMBERFALL` | Rare | 1500 (15%) | 1 | blueprint written | ❌ no kit |
  | `SKY_CITADEL` | Epic | 700 (7%) | 1 | chunk kit, 36 pieces — walked and verified | ✅ |
  | `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written | ❌ no kit |
  | `THE_UNKNOWN` | Unknown | 5 | 3 | none | ❌ no kit |

  (Supersedes the Worlds table in `docs/archive/STATUS_HISTORY.md`, written before Sky Citadel had a kit.)
- **Enemies:** the framework is built and all 16 Sky Citadel enemies are modelled, rigged and exported. The Winged
  Sentinel (Boss 3) runs in Studio through `/showboss`, with the Aether Lance's lightning and `/bossphase`. Ethereal
  Scape has a drafted 9-enemy roster under `assets/source/enemies/ethereal_scape/`.
  - Built so far: its basics, and its boss **The Ascendant** (2026-09-28).
  - The Ascendant has a body, a Staff-class weapon, `ASCENDANT_MOVESET.md`, and Idle, Crescent Reap, Walk and
    Strafe ×2 exported.
  - 2026-09-28 (Session 97): all five actions were rebuilt as whole-body motion and exported onto the owner's
    hand-edited `.blend` mesh. The strafe arm spasm, legs crossing and the Reap's hand spin are fixed. The FBXs come
    from the `.blend`, not the script (see `ASCENDANT_MOVESET.md`).
  - Session 98: baked cloth (`_framework/cloth_core.py`) makes the robe and back scarves hang free and collide
    with the legs and body. Three-joint fingers (`hands_core.py`) close both hands round the staff. The rig is now
    150 bones, so confirm Studio's importer accepts it. Session 99: the free arm clears the robe. The owner will import
    once, when the boss is finished.
  - Not yet imported in Studio.
  **Nothing spawns in gameplay yet.** `EnemyDef` + services wait for the owner's OK.
- **Tooling:**
  - **Developer panel + command registry** (2026-09-27): F4 in Studio; 43 commands, all clickable, autocomplete; see `docs/DEV_TOOLS.md`.
  - `INDEX.md` + `INDEX_MAP.md` give the repo map, and CI keeps the map current.
  - StyLua is enforced.
  - Integrated validation: **1,017/1,017 Luau tests**, **7/7 Blender regressions**, **7/7 collision-verifier probes**, StyLua and syntax compilation (129 files including diagnostics) pass; full Rojo 7.7 project build succeeds. Index/forbidden-name/handoff checks pass. Collision verifier validates all 4,033 active colliders; 3,915 serialized-fidelity parts still require Studio inspection.

- **Leaderboard + chat:** SIGIL LVL/name columns use server-replicated FateLevel; filtered TextChatService messages only. Opening chat collapses the retained hidden rail. Integrated UI smoke test remains pending.

- **Verdant Valley production:** all 30 structures and calibrated per-chunk yaw/size/GroundOffsetY values retained with matching VV manifest IDs. The saved prop library has 823 meshes/placements: 30 solid groups, 30 nonsolid groups, 746 Sway canopies and 17 special parts, including 12 chest components. Thirty-nine solid rows are server-owned Static/Tier 1; nonsolid/canopy rows are client-owned. Chest props have no new loot/fixture interaction.
- **VV walk collision:** 29 child templates/3,915 parts in VV_COLLISION (including 66 Cliff parts and the 137-part Cutbank bridge set), plus the separate 118-part merged Stone template, cover all 30 chunks. Missing/empty templates retain visual collision. The original 202-part Stone rollback is protected. Collision verifier now uses the refreshed production ledger, not the obsolete 28-model report; serialized fidelity still needs Studio reload inspection.
- **VV appearance and placement:** refreshed terrain/prop IDs, repaired colors/stump/Boss underside, chest ownership/centres, and Mushroom Glen/Split Meadow refreshes are saved. Source/runtime/reference checks precede owner fresh Play checks; prior warnings and save-pending statements are historical in WORKLOG. Normal/winding review retains 178 ambiguous manual-review cases. No old staging set is approved for promotion.
- **VV testing:** `VV_SOCKET_WIDTH_REVIEW.md` supersedes the earlier audit's flat-ground PASS criterion with exact authored path/width measurements across all 30 chunks/59 sockets. Independently confirmed and corrected Mushroom's east→west exit plus PATH/WIDE reversals on Causeway, Windward, Crystal Spring, High Ledge and Cliff Overlook. Trial, Orchard, Boss and prior Refuge south correction unchanged. Before stronger audit: 34 PASS/14 SUSPICIOUS/11 FAIL sockets (six failing chunks); after: **42 PASS/17 SUSPICIOUS/0 FAIL**. Runtime yaw selections and all assets/prop transforms retained. Mushroom→Trial pair passes 220/220; all pair centres pass; Owner manually tested approximately eight procedural seeds after the latest corrections: Refuge remains fixed, Mushroom connects correctly and corrected PATH/WIDE gates connect cleanly; no additional socket-placement or visible connection failures observed. The 17 suspicious sockets, Windward/High Ledge/Orchard panel seams, earlier Refuge terrain-query and Shaded Grove pair limitations remain audit/query ambiguities, not confirmed metadata failures. Luau **1,017/1,017**, Blender/verifier probes 7/7 each; Rojo 7.7 passes. Historical generators cannot reconstruct current production safely.
- **Blender protection:** shared launcher validates Windows profile lookup before parent/child work; failed restricted-token lookup requires normal-token retry. Installed MCP/startup protection and seven regressions are retained. Fifteen thumbnail trees and original add-on recovery remain; owner normal-use/restart check and upstream native fix remain pending. Launcher is Windows-specific; cloud bpy 4.2 tooling is retained separately, not claimed as an equivalent protected workflow.
- **Integration:** fd60833 and frozen main 1001ec2 are reconciled by existing local two-parent merge 191ea0b. Final local completion commit is authorized after checks; push and merge into main are prohibited. Production assets, newer movement/animation/lock-on/UI/progression, ES assets, enemy work, HUB_SKY and the animation Rojo mount are retained. Socket-specific owner Studio validation is complete; remote CI and broader integrated movement/UI/asset-fidelity checks remain pending.

## 2. Next — pick up here

> **2026-09-30: expedition portals wired locally on `agent/expedition-portal`.** Owner verified the corrected
> Blender meshes and Studio proportions, then delivered both `.rbxmx` prefabs. They now load through Rojo at
> scale 1 with measured Scar offsets; complete rifts stream atomically. Entrance defaults to ENTRY centre,
> exit to BOSS centre, raycast flush; optional validated `Content/Portals/<World>.luau` offsets are supported.
> Return/exit triggers enforce server distance, living membership, exact stage and open state. Arena and
> `/boss` share one reward claim. Prototype gate behavior/tunables removed; shop and legacy travel Id kept.
> **967 tests pass**, full source syntax and Rojo build pass, StyLua clean. Selene has no errors (two existing
> Schema shadowing warnings). **Next:** owner performs `TESTING.md` Test C2c; gameplay/streaming remain
> unverified. Flow texture upload is pending (plain ribbons work); Fate Engine rework and XP remain separate.

> **2026-09-30: rift import correction, local on `agent/expedition-portal`.** Both Blender sources and FBXs
> regenerated with welded, outward-facing triangulated shells, gap-free scar disc and baked Y-up unit-scale
> export. Both FBX re-import checks pass (names, dimensions, scale and topology). Import with **Stud / 1.0**;
> `RiftHalo` height = 15 / 21 studs. Owner subsequently verified corrected Blender geometry and Studio
> proportions and delivered both prefabs. Earlier Studio imports may be removed after Test C2c passes.

> **2026-09-29: expedition rifts, branch `agent/expedition-portal` (build spec §7.8), not merged.** Entrance and exit
> are now rifts (authored meshes in `assets/source/portals/`, ~5.9k and ~7.8k tris; motion and light in code). New:
> `Core/RiftCore` (pure curves), `Util/RiftRig` (build, effects, seal/open), `Controllers/RiftController` (per-frame
> pose), `ExpeditionCore.outcomeFor/payoutFor` (a cleared run pays in full, an early one `EarlyExitFraction`, a death
> nothing). `ExpeditionSystem` builds the entrance on the arrival chunk and a SEALED exit on the boss chunk; the boss
> stand-in opens it. Initial 944 tests passed; now 967. Imports, measured scale/axes and hub gate behavior
> removal are complete locally (2026-09-30). **Pending:** flow-texture upload, Studio Test C2c, and the
> Fate engine rework (ready toggle, host starts, roll-then-lower entry) which plugs into `payoutFor`.

> **2026-10-05: rifts re-based on main (temp branch `temp/expedition-portal-on-main`).** Group-owned textures set
> (`Rift.FlowTexture`, lightning strip); fragments livelier; `/riftexit` added; RiftController logs what it tracks and warns
> if the flow texture fails to load. Not merged to `main`.

> **Generation migration accepted by owner (2026-10-02):** retain the new pipeline.
> VV/SC/ES tested traversal and quick re-entry passed; remaining published, memory,
> explicit atmosphere/streaming and unreported catalogue checks are recorded in
> GENERATION_MIGRATION.md. Future small proxy/enemy contracts remain proposals.
> Sessions 235-237. Production PR #156 opened; local checks pass, no merge conflict.
> Await final-head CI; owner explicitly requires stopping before merge.
> Separate ES collision pilot rejected and excluded; keep current collision. No Studio save/publish.

> **2026-10-01 ES integration:** owner authorizes PR/merge of the Studio-walked kit
> and current BASE scenery. Temporary loading diagnostics removed; generation
> behavior restored. Loading redesign is next. Ribbon visibility remains open.
> Session234 supersedes earlier no-push gates.

> **2026-10-01 ES readability:** twilight kept; ambient/exposure lifted, density0.31/haze1.6,
> gentle purple grade. Ribbons lowered420–620, broader/longer and opacity0.30 for visibility,
> same rendering budget. Studio retest pending. Session233.

> **2026-10-01 ES ribbons:** client-only upper-air beams fade/drift/relocate across full
> map bounds +600studs,2–8 beams/10Hz depending on quality. No import, physics or particles.
> 1,038 tests/syntax/Rojo pass; Studio appearance/performance review pending. Session232.

> **2026-10-01 ES twilight:** owner replaces bright afternoon with18.35 orange-purple
> dusk, apricot horizon/violet shadows and readable ambient fill. Overhead accent choice
> pending; SC/Crossroads unchanged. Session231.

> **2026-10-01 density tuning:** ES19 lower banks (11/8), SC31 (12/12/7), about35%
> more than the first sparse pass. Crossroads unchanged; Studio retest pending. Session230.

> **2026-10-01 ES living scenery:** stronger BASE look;161 crowns get varied wind, six
> decorative backdrops bob with props, glider lateral sweep/heading corrected. ES/SC use
> sparse Crossroads bank meshes with broad depth scatter and smooth drift.1,034 units,
> loader regressions/Rojo pass; Studio motion/cloud walk pending. Session229.

> **2026-10-01 BASE-only ambience:** owner confirms kit works in Studio. All worlds now
> use BASE only (Ambience.Atmospheres.Enabled=false); variants retained. ES pearl afternoon
> lighting/haze, restrained bloom, lower cloud banks and motes implemented as Environment data.
> 1,029 tests/Rojo pass; visual atmosphere walk pending. Session228.

> **2026-10-01 ES imports verified:** owner replacement models copied from primary checkout into
> the ES worktree;227 structure/258 props, all expected names/uploaded IDs/dimensions verified.
> Restored50 ellipsis-shortened prop names (including one duplicate) in worktree XML. All227
> structure IDs synced;1,029 units and Rojo build pass. Ready for Studio walk from the worktree;
> primary prop XML still has shortened names. No PR/push until acceptance. Session227.

> **2026-09-30 ES live delivery/runtime:** fresh exports227 structure/258 prop meshes, matching
> placements, 35 generic64-stud boundary groups, conditional shrine room and two-way walk-through
> transit with membership/cooldown/streaming checks. Only biome-boss completion opens the vault-room
> gate and can drop its key; keyed chest stays per-player. Minibosses do neither. Import instructions
> in `assets/source/worlds/ethereal_scape/IMPORT_STEPS.md`. Owner must replace both RBXMX files,
> then sync IDs and Studio-walk before PR/push. Existing uploaded IDs/RBXMX still predate this delivery.
> Unit/loader/FBX checks pass; actual Studio physics/cameras remain pending. Atmosphere follows,
> enemies separate conversation. Session226; prior pending notes below are superseded where noted.

> **2026-09-30 shrine arena enlargement:** 114 × 114 clear floor, ceiling 60.9 studs;
> side supports reach roof and six celestial ceiling murals added between beams. Geometry
> audit and interior render checked. Owner review/save and fresh Studio delivery pending.
> No loader change, save/export or PR. Session 116.

> **2026-09-30 boundary/profile correction:** two mouth-blocking walls removed, including
> Sanctum; 35 boundary groups raised to 64 studs. All 60 connector keels get matching lower
> chamfers/level bottoms, including two shifted-origin pieces. Future map and SC boundary
> requirements recorded. Owner/Studio review and runtime delivery remain pending. Session 115.

> **2026-09-30 props/boundaries:** 244 live animation props (66 newly separated light groups,
> 161 tree crowns plus prior shrine/chandelier props), transforms preserved; 35 authored safety
> boundary groups. Geometry audit passed. Runtime boundary schema/camera exclusions and fresh
> complete exports/placement data pending; existing FBXs predate separation. No loader change.
> Correct ordinary tagged count is 24 plus entry = 25 (28 including bosses). Session 114.

> **2026-09-30 connector underside:** standard mouth pyramids replaced live with faceted
> socket-flush keels and small edge bevels away from seam planes. Original landing generator
> updated, owner edits preserved; scene/Studio inspection pending. No loader edits. Session 113.

> **2026-09-30 shrine/loot:** live detached shrine room, clear 76 × 76 fight floor,
> matching portal with dark vestibule backing, recessed vault and separate effect props.
> ES pools/key chance and altar chest content added; room teleport/vault registration
> pending placement contract. ENTRY trim removed, completed portal preview on rear circle.
> Python/StyLua/Rojo passed; Studio gate pending, no new loader edits or PR. Session 112.

> **2026-09-30 ES correction:** throne curves now retain flat shading. Bridge cutting now
> uses the complete triangulated cap boundary, removing Observatory path slivers and 57
> further overlap faces. Removed 465 floor-trim pieces crossing paths/decks/structures and
> four architectural pieces penetrating glass. All 65 detail meshes pass geometry audit.
> Owner inspect/save/export and Studio gate pending; no loader edits or PR. Session 111.
>
> **2026-09-30 ES clearance revision:** Gardens stair and full-width foot landing rebuilt;
> added column trim stops around window footprints, and 70 path decal faces clipped at
> bridge transitions across nine chunks. Owner inspect/save/export and Studio gate pending.
> No loader edits or PR. See Session 110.
>
> **2026-09-30 ES detail revision:** curved throne/eye with fitted cushion and arms,
> restrained floor and column/window trim (including backdrops) added in live scene.
> Terrain undersides restored to facets after owner rejection of smooth belly shading.
> Gardens upper wedge replaced by fitted original deck/stringer ends; lower landing unchanged.
> All 57 new detail meshes pass closed/nondegenerate/finite audit. Owner review/save/export
> and Studio gate pending; no loader changes or PR. See Session 109.
>
> **2026-09-30 boss-aligned ES finish:** owner now requests smoother worlds matching bosses.
> Ascendant-style throne filigree/core added; all 59 ES structure/detail meshes processed,
> 258 architectural blocks rounded and curved/island-side shading softened. Base vertices
> unchanged; 59 evaluated mesh checks pass. Unsaved/unexported; export modifiers/normals,
> recalculate bounds/offsets and retest Studio. SC/Winged Sentinel follow-up remains pending.
> No loader changes or PR in this pass. See Session 108 and ART_DIRECTION.

> **2026-09-30 Sanctum presence:** chair enlarged; rear canopy, floor inlays and exterior
> reliefs added in live scene. Five chair blocks now chamfered, three back panels tapered;
> four arched inner entrance-wall reliefs and lintel crest added. Owner review/save/export
> pending. See Sessions 106–107. No loader changes or PR in these passes.

> **2026-09-30 Sanctum follow-up:** live chandelier (3,196 tris), 39 thick window panes
> detailed on both sides, and enhanced door mask/crown/robe reliefs. Unsaved/unexported;
> owner review remains required. Studio floating mushrooms traced to inverted X/Z multipart
> offsets, fixed in ES generator/JSON/content; 28 foliage placements match actual RBXMX
> import centres. Shared loader unchanged in this follow-up. Retest Studio, then re-export
> the owner-edited scene with all added meshes and updated metadata. See Session 105.

> **2026-09-30 live owner-edited ES polish:** 60 windows framed/mullioned, 10 tall square
> columns detailed, Terraced Gardens stair landings patched. Changes are in the open Blender
> scene; agent did not save/re-export. Use main-thread timers for Blender Open MCP writes (its
> worker-thread handler crashed on direct mesh writes). Preserve the owner's scene.
> One mushroom edge overhang corrected; Studio-only floating decorations need an affected
> chunk/seed/screenshot from the owner. Re-export must include ARCH_DETAIL/STAIR_DETAIL
> meshes and recompute bounds/offsets. See Session 104. No new loader changes or PR.

> **2026-09-30: ES Studio repair ready for reimport**, branch `agent/ethereal-scape-polish` in
> `.worktrees/ethereal-scape-polish`; primary checkout remains on the portal branch. First owner walk
> failed for missing faces/seams, clipping and blocked routes. Closed/shared terrain shells, roofs and
> props now pass topology checks; bridges clear entire rims, eight island webs provide slope run,
> thresholds and bridge approaches pass player-clearance checks. Removed kites; small foliage exports
> separately with collision disabled, all structures remain solid. Outward Sanctum doors, a richer
> throne and fluted columns are rebuilt. 71 structure meshes and 13 props, maximum 9,994 tris per mesh;
> Sanctum 11,990 total across three parts. 1,016 units, 4,280 loader comparisons, full geometry/export
> checks and Rojo build pass. VV/SC legacy loading matches; actual Studio physics still needs testing.
> Owner exported replacement RBXMX files; copied into this worktree and all 71 chunk IDs synced.
> All 13 props have uploaded IDs; 1,016 units and Rojo build pass. Ready for owner reinspection.
> **No PR or push before owner testing.** Owner may hand-edit the output blend; preserve those edits.
> Enemy polish follows chunk acceptance; Ascendant's owner-edited blend/animations are untouched.

> **Superseded by repair above — first ES import staging.** Owner's 42-mesh structure and 14-prop RBXMX exports
> copied from the primary checkout into the polish worktree; all 42 chunk IDs synced. Unit tests,
> loader compatibility checks and full Rojo build pass. Serve from the polish worktree. Studio walk
> remains pending; owner explicitly requires that test before a PR is created.

> **2026-09-30: Ethereal Scape chunk polish and multipart delivery**, `agent/ethereal-scape-polish`.
> Owner clarified: under 10k triangles per mesh, not per chunk; low-poly style retained. Existing trees
> and columns polished; Sanctum doors echo the existing Ascendant, confirmed as its main boss.
> Sanctum: 11,074 tris across 3,518-tri grounds and 7,556-tri temple meshes. Optional MeshParts content
> loads/calibrates the entire assembly together, with whole-chunk fallback if one mesh is missing.
> 1,014 Luau tests, 41/41 geometry checks, splitter stress cases and real FBX round-trips pass;
> 42 structure meshes and 14 props stay under 10k. Existing blend/FBXs/renders regenerated.
> CI loader compatibility checks pass 4,240 cases: all VV/SC single-mesh chunks match the old loader
> at four yaws, including fallback/recolour/catalogue paths. Multipart alignment/fallback also passes.
> Studio import, four-yaw alignment/collision and colour checks remain pending. Basics already exist;
> review and polish those next, then minibosses. Ascendant's current model/animations are preserved.

> **2026-09-28: polished body movement.** `CharacterAnimator` + `AnimationCore`: blended gaits, directional
> strafe (clips when filled, procedural until then), lean, head look, landings, sounds; rolls in four
> directions relative to facing. Clip slots in `Content/Animations/Player.luau` (§2.7 has the how-to).
> 997 tests pass. Studio walk pending.

> **2026-09-28: our own character controller.** Default Roblox movement is off: a `ControllerManager` drives the
> character from `LocomotionCore`, with HUB (fast) and EXPEDITION (weightier) profiles, one stamina bar, a single
> jump (the double jump is gone), roll/backstep, and optional lock-on with an over-the-shoulder camera
> (`LockOnCore`, `LockOnController`). There is a new stamina bar (`UI/Vitals`). 940 tests pass. **Studio walk
> pending:** `TESTING.md` Test K, all 17 steps. Lock-on switching (mouse/stick flick, touch Next) and `/dummies`
> were added the same day; charge is scoped to Epic/Legendary weapons only (`WEAPONS.md` §2).

> **2026-09-27: close ship berths fixed after precommit review.** Berths now use
> the island's oriented face and half the ship's beam, with a 20-stud hull gap;
> overlap/approach checks use the ship box instead of its enclosing sphere.
> This supersedes the earlier radius-based berth calculation. 866 tests pass,
> including angled mesa/carrier and all-side clearance regressions; changed docking
> files lint clean. Studio docking observation remains pending. Owner authorized
> a final review, commit and push of all related test-command/docking changes.

> **2026-09-27: hub docking corrected locally.** Large galleons/carriers explicitly
> opt into docking; whales and other orbiters do not, regardless of size. Berths
> account for full ship radius and clearance. Ships brake to a full stop, retain
> steering while approaching and have a turn-scaled timeout; docking and visual
> headings are separate. Docking tunables are in HubLayout.V2.Docking. 862 tests
> pass; medium/higher graphics Studio docking observation remains pending.
> Owner confirms the catalogue test environment now works after the loader fix.

> **2026-09-27: catalogue load crash fixed locally.** Owner's Output traced the
> failure to ChunkLoader's test return-offset rotation: CFrame.Angles was missing
> its third argument, aborting loading on the first entry. Added the zero Z angle;
> all five calls in the loader now supply three arguments. Restart Play after sync
> and rerun the catalogue to verify complete loading in Studio.

> **2026-09-27: catalogue orientation and streaming correction.** Separated chunks
> now turn their sockets along the observation row, with rotated footprint spacing
> and return-portal offset. Test stages use Persistent streaming to keep the whole
> kit in client Explorer; normal streaming stays unchanged. 858 tests pass. Studio
> verification of all 30 VV folders, orientation and the 60-minute timer remains
> pending. These address visible weaknesses in the test implementation; the earlier
> screenshot of normal assembly still needs command/expedition Output evidence.

> **2026-09-27: test timer extended to 60 minutes.** Test instances use 3600 seconds
> in place and through the reserved-server manifest; normal durations are unchanged.
> 854 tests pass. Owner's screenshot shows normal assembly (index 0 and 108–110,
> repeated chunks), rather than catalogue assembly. Awaiting the command/expedition
> Output replies and model TestMode attribute to distinguish stale Studio code from
> a lost selection; the reported missing-chunk issue is not yet resolved.

> **2026-09-27: catalogue test roll implemented locally.** `/roll <WORLD_ID> test`
> selects the next instance's all-chunk observation line; ordinary `/roll` keeps
> seeded generation. Every current kit definition appears once, including rare
> pieces and multiple entry/boss variants, with matching joins where possible,
> configured gaps otherwise, and open sockets allowed. The flag follows the
> server manifest and is bound to one roll/instance. 851 headless tests pass;
> Studio catalogue/normal-roll and published teleport checks remain pending.

> **2026-09-27: Verdant Valley cap variety, local change.** Cave Mouth remains a cap;
> Treasure Hollow and Warden's Clearing are now caps; all three caps are unlimited
> and equally weighted following the owner's corrected direction. Forgotten Trial is
> the sole SIDE chunk. Kit names, generated
> content, exporter and manifest agree; mesh IDs and geometry are unchanged.
> 817 tests pass; 400 additional VV layouts close every socket and exercise repeat
> placements of both converted caps. Studio/Rojo loading and walks remain pending.

> **2026-09-26: local socket recovery** on `codex/recover-socket-fixes`, based on main `5090ace`: canonical VV mesh mappings, per-chunk calibration tolerance, centre-hit diagnostics, and Rojo 7.7 restored. Latest main and recovery both pass 817 tests; full Rojo build and Luau syntax pass. Studio four-yaw asset/collision checks remain pending; existing 43 seam-height failures are a separate baseline. New Ethereal Scape and enemy work preserved. No push or main merge.

> **2026-09-26: Ethereal Scape converted from a `PrebuiltMap` to a 30-piece chunk kit, owner-directed.** It shipped
> as one composed, hand-authored, no-combat traverse (a map-generation test rig). That is superseded:
> `Content/Worlds/EtherealScape.luau` now declares a chunk kit + `MapPathLength` like Sky Citadel and Verdant
> Valley; `Content/Chunks/EtherealScape.luau` has the 30 pieces (generated by
> `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py`, geometrically validated, not yet uploaded or
> walked); `docs/biomes/ETHEREAL_SCAPE.md` is the schema. A 9-enemy roster was drafted alongside it
> (`assets/source/enemies/ethereal_scape/ROSTER.md`), one basic built (Aether Wisp) to prove the palette
> translates to a character; `Enemies`/`BossId`/`LootTableId` stay empty, same as every other world, since no
> world's combat content is built yet (§7.6, reserved). `tests/cases.luau`'s "Ethereal Scape" group and the "two
> ways a world gets a map" checks were rewritten for the new reality — **run the suite before merging**, this
> session could not (no local Luau interpreter). The original scene stays in the repo as the palette's source of
> truth. See `docs/biomes/ETHEREAL_SCAPE.md`'s header for the full reasoning.

> **2026-09-26: §7.6 reserved for enemy AI/combat, module names locked.** Build spec §7.6 now claims the number
> `ENEMY_AI.md` §12 step 0 asked for, so no other branch can take it. `CombatCore`, `PerceptionCore`, `EnemyAICore`,
> `DifficultyCore`, `BossCore`, `TelemetryCore`, `EnemyService` and `BossService` are locked as the final module
> names. **Nothing opens yet** — combat/enemies/bosses stay excluded by §7's list. Remotes and `GameConfig` blocks,
> the rest of step 0, are deferred to step 1, when the actual schemas exist to design them against.

> **2026-09-25: enemy AI designed, not built.** `docs/ENEMY_AI.md` is now authoritative for enemy behaviour:
> utility AI over the framework's roles, no difficulty setting (a shared versioned profile plus an invisible,
> capped personal tempo adjustment), harder play pays extra loot rolls never better odds, universal versioned
> boss evolution with rollback, and weapons carrying their own moves with unique Legendary movesets. It sets a
> mandatory build order. Nothing is opened: step 0 is a §7.x amendment for the owner to approve, and items and
> inventory still come first.

> **2026-09-25: animation ids are account/group-scoped, documented.** A partner playtesting `/showboss
> winged_sentinel` in their own place got a silent `Animation failed to load` warning for the Idle id — same class
> of bug as a mesh uploaded to the wrong account (`assets/README.md` already covered that for meshes). Documented
> in `docs/PARTNER_SETUP.md` ("Animation and other account-scoped ids") and `BossPreviews.luau`'s header. No code
> changed — `DebugSystem.luau`'s `/showboss` animation loading is correct; Roblox just denies cross-account asset
> fetches without raising an error. Once LUCKBOUND is published under one group with all assets uploaded to that
> same group, this stops affecting real players — it only bites Studio testing across separate accounts/places.

> **2026-09-25: audit + index.** `INDEX.md` is the mandatory first read for every AI agent: a hand-written guide,
> plus `INDEX_MAP.md`, generated with the exact line of every symbol. `AGENTS.md` holds the agent rules, and
> `CLAUDE.md`/`GEMINI.md` point to it.
>
> Legacy Verdant Valley pieces are gone. The kit is `VV_STRUCTURE.rbxmx` (the same shape as `SC_STRUCTURE`).
> The duplicate Fern Hollow and Mushroom Glen manifest rows were removed on `socket-fixing`; both canonical keys point to the current 30-piece assets in `VV_STRUCTURE.rbxmx`. The owner confirmed both pieces load their intended meshes in Studio on 2026-09-25. Earlier socket warnings were downstream of the wrong assets loading. Boss Sanctuary rotation is verified.

> **2026-09-25: the Winged Sentinel stands in Studio.** Run `/showboss winged_sentinel` in the boss arena: 16 studs,
> facing the entrance, playing the Idle_Guard animation (`rbxassetid://132590990835909`). The Aether Lance's web is
> geometry plus live Beams; `/bossphase 2` charges the plasma blade.
>
> **Owner to verify:** re-import the latest `WingedSentinel.fbx` (with pinned anchors), then check that the strands
> show (`/showboss` reports the count) and that `/bossphase 2` opens the blade halves.
>
> Next for enemies:
> - The rest of the Sentinel moveset animations (Epic tier and above get weapon animations).
> - The `EnemyDef` + services wiring, which awaits the owner's OK.
>
> Queued:
> - The crossroads chunk pass.
> - The hub refinish.
> - Recolours and scenarios stay parked until after release (files kept).

> **2026-09-24: enemies have a framework.** `docs/ENEMY_FRAMEWORK.md` +
> `assets/source/enemies/_framework/` build, validate, pose, animate and export every enemy in every biome.
> Sky Citadel's 16 enemies are built and exported (`assets/export/enemies/sky_citadel/`); the Winged Sentinel has
> Idle, the P2 transition and the first moveset attack. Studio wiring (`EnemyDef` + services) awaits the owner's OK.

1. Fresh Rojo sync/Play: verify saved collision fidelity, catalogue and seeded VV generation, remaining prop alignment and query ambiguities, Cliff/Cutbank/Stone/Wetland traversal and main's movement/profile/camera/lock-on behavior. Check low/high quality props and Sway attributes; smoke-test ES and newer hub/SIGIL UI.
2. Owner Blender normal-use/restart check; use the shared launcher and reinstall startup/MCP integration after add-on replacement.
3. Run remote CI on a later authorized commit before main integration. Local wrap-up commit is authorized; do not push or merge into main.
4. Existing follow-ups remain: hub ship docking observation; player animation slots/upload checks; Winged Sentinel re-import/lightning and remaining moveset; Ascendant Studio import and importer bone acceptance. Gameplay enemy services/items still await their design/amendment gates.
5. Shop, Archive, Fate Tree and Rebirth remain preview panels. Roll-anywhere and sacrificing an old roll need a spec amendment. Retire hidden UI rail/showcase only after owner/live-server checks. Recolours and other owner-kept assets remain parked.
6. Keep old VV exports, failed separation candidates, staging/recovery sources and protected rollbacks until integrated Studio/CI validation establishes safe replacement. Do not run an older generator to recreate current assets.

## 3. Decisions locked in

These are settled. Do not relitigate without a deliberate reversal.

| # | Decision | Where |
|---|---|---|
| **D-8** | **Fate is TRUE RNG.** No player state ever changes the odds of any world. | spec §3.3 |
| **D-9** | **15-roll scripted onboarding**, peaking on Epic at roll 8, never Mythic. Slot 5 extended to Uncommon 2026-09-16 — arc unchanged in shape. | spec §3.3.1 |
| D-3 | Roll cooldown 3.0 s, enforced server-side, silent on rejection | spec §3.4 |
| D-4 | Reveal duration scales with rarity (2.5 s → 7.0 s) | Constants |
| D-6 | Roll history capped at 50 entries | GameConfig |
| D-7 | Expedition 720 s default — **still flagged as too long**; a world may override it and Ethereal Scape runs 300 s | spec §6 |
| **D-10** | **A rift reward is permanent; only the WINDOW is temporary.** No decay, no charge, no expiry attribute. Fair only while events recur — that is a commitment, not a preference | `EVENTS.md` §5.4, §6 |
| **D-11** | **The finder gets the unique item; everyone gets the event.** Ten Catalyst Stars produce ten game-wide occasions, not ten private ones | `EVENTS.md` §5.5 |
| **D-12** | **A failed rift run costs the attempt, not the event.** The rift stays open to all until the event ends; no per-player attempt counter | `EVENTS.md` §5.3 |
| **D-13** | **Event access never depends on the roll pool.** A biome with a live event is directly enterable by anyone, regardless of what their pool contains — otherwise pool progression locks high-tier players out of the events they have earned | `EVENTS.md` §5.4b |
| **D-14** | **Events are tiered AMBIENT / MODIFIER / WORLD**, enforced by the validator. Only WORLD may open a rift or grant a unique | `EVENTS.md` §4.0 |
| — | **Expedition entry is open; combat/loot are not** | spec §7.1 |
| — | Destination = the player's last roll. No new state, no schema bump | `ExpeditionCore` |
| — | Biome lighting is applied **per client**, never by the server | Blueprint §6 |
| — | Rarity colour is a UI/portal contract; biome palette is set dressing | Blueprint §4.1 |
| — | Compass mapping N=-Z, E=+X, S=+Z, W=-X, up=+Y | GameConfig.HubLayout |
| — | **A prefab is registered from a NAMED PART, not from its model pivot.** A pivot is invisible metadata an FBX chain mangles quietly; a part name is already the contract with the artist | `Util/PrefabLoader` |
| — | **Scale and compass corrections are content, never re-exports.** An importer setting is fixed by a number in `Prefab` | `Content/Hub/Crossroads` |
| — | **Agents implement on `agent/<task>` branches and open PRs; only an integration agent merges, one PR at a time against the current `main`** | `docs/GIT_WORKFLOW.md` |

### Why true RNG matters downstream

With no odds tilting, **a player at roll 200 faces identical odds to one at roll
16.** "Stuck in Commons" is a permanent condition, not an early-game phase.
Fate cannot weight its way out of it.

The lever that stays consistent: **Fate unlocks which pools you draw from,
never how the draw resolves.** Higher Fate grants access to a pool that has no
Common in it. That is the Phase 3 design, and it is the answer to the
progression-feel problem.

---

## 4. Open items (one line each; details are in the archive under the same bold name)

| Item | Severity / state |
|---|---|
| **Reserved declarations are now registered** | **New 2026-09-23** |
| **Unused sockets are never capped** | Medium |
| **A chunk's mesh origin must be its footprint centre, and nothing enforces it** | **High** |
| **Runs were a single straight shot** | **Fix pushed 2026-09-23, unproven** |
| **World ambience** | **Built 2026-09-23, walked and verified 2026-09-25** |
| **Ambient props** | **Live 2026-09-23, walked and verified 2026-09-25** |
| **Loot, fixtures, vault keys** | **Live 2026-09-23, walked and verified 2026-09-25** |
| **Verdant Valley 30-piece kit exported** | **Separated production kit saved; socket Studio pass complete (~8 seeds); broader fidelity/movement review pending** |
| **The Grove did not survive the upload** | Medium |
| **The scenario layer** | **New 2026-09-22, headless only** |
| **A brief that specifies the piece gets the piece it specified** | **Process** |
| **Kit target raised to 12–16 pieces** | **Content** |
| **The kit was generated stacked at one point** | Low |
| **Portal plane is still above head height** | Medium |
| **18% of rolls land on a world with no map** | **High** |
| **A chunk mesh is stretched to its declared size** | **High — narrowed 2026-09-23** |
| **Chunk colour on a single MeshPart is unverified** | **High — testable now** |
| **The authored hub's collision set, take two** | Medium |
| **A re-delivered prefab loses its baked `CollisionFidelity`** | Medium |
| **Scaling the horizon cannot change its apparent size** | Note |
| **The horizon wants a purpose-built chunk** | Low |
| **Trees on the bordering floating islands are malformed** | Low |
| **The portal's stop has nothing to lead to yet** | **Open** |
| **The mountain horizon is built, not placed** | Low |
| **First-join intro screen** | **Built, walked and verified 2026-09-25** |
| **The Engine portal is to become the way into biomes** | **SIGIL Fate Engine menu built; entry/roll server rules retained** |
| **The authored Fate Engine is wired** | **Walked and verified 2026-09-25** |
| **Ethereal Scape's `Scale_Reference` proxy is loose** | Low |
| **The scene has no `EntryAnchor` / `ReturnAnchor`** | Medium |
| **Ethereal Scape: one whole map, not eight chunks** | Decided 2026-09-17 |
| **The Crossroads wants a revamp after testing** | **Design** |
| **Staircase clipping at the walkway junctions** | Medium |
| **The live menu tint is unseen** | **High** |
| **Rifts: event-gated dungeons** | **Design** |
| **The event sky is built** | **Walked and verified 2026-09-25** |
| **The event catalogue is a proposal, not a plan** | **Design** |
| **Three panels are designed, not implemented** | Expected |
| **Five settings are stored and honoured by nothing** | Medium |
| **Travel landings are guesses with a safety net** | Medium |
| **Profile schema is now v2** | Note |

## 5. Environment

- Code: `C:\Dev\luckbound` (not OneDrive — must stay outside it)
- Place: `LUCKBOUND_dev.rbxl`, local, unpublished
- Rojo CLI 7.7.0 via Rokit; Studio plugin 7.7.0
- **Unpublished means no DataStores.** Expected; the server runs in volatile
  mode and says so. Publishing is what enables saving.

### Startup

```powershell
cd C:\Dev\luckbound
git pull
rojo serve
```

Studio → open `LUCKBOUND_dev` → Rojo panel **Connect** → **Accept** → **▶ Play**

---
