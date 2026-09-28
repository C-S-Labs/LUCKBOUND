# LUCKBOUND — Project Status

**Last updated:** 2026-09-28 · slimmed for token use. The full previous version, with every closed item and walk
report, is `docs/archive/STATUS_HISTORY.md`. Read it only by section, when an item below points to it.

> **New conversation?** Read `INDEX.md` → `AGENTS.md` → the top entry of `docs/WORKLOG.md` → this file.

---

## 1. Where the project stands

- **Phase 1 is complete** (hub, roll, onboarding, saves, UI, sprint and double jump, events). The build spec §7
  amendments that opened later work are §7.1 expedition entry, §7.2 parties as their own server, §7.3 scenarios,
  §7.4 caps, §7.5 loot and §7.7 universal map generation (2026-09-27).
- **Worlds you can enter:** Verdant Valley (30-piece chunk kit — built, **needs a revamp pass**), Sky Citadel
  (36-piece chunk kit, walked and verified, with ambience, props, chests and the vault) and Ethereal Scape
  (**41-piece hybrid kit** — floating isles + temple + meadow, 2 landmarks, 2 miniboss arenas, 6 backdrop
  pieces with drifting cloud props, height variation — on the §7.7 generation blueprint, 2026-09-27; final
  polish pass done (map-wide skyrays, natural mushroom patches, overhang check) — **not yet uploaded or walked**). Emberfall and Astral
  Reach have no map yet.
- **Verdant Valley baseline:** `codex/vv-stone-walk-collision` starts from the
  pre-separation `ce0f29f` commit. The authoritative art is
  `assets/source/worlds/verdant_valley/verdant_valley_30_cleanup_review.blend`;
  the joined `VV_STRUCTURE.rbxmx` remains the visible kit. The failed full
  separation activation is preserved on `codex/vv-full-separation-reference`.
  The reviewed scene and baseline contain the reviewed 30-mesh Blender scene,
  validated FBX, Studio-imported `VV_STRUCTURE.rbxmx`, and synced mesh IDs. All 30 imported names and dimensions
  match the export report. The saved kit now records PreciseConvexDecomposition on all 30 MeshParts;
  the runtime loader already requests that fidelity. The visual Studio walk and
  in-experience asset-access check remain open before merge. Floating collision
  and visible terrain gaps in the owner's walk remain unresolved.
- **Stone Sentinels collision prototype:** A new generator derives 202 thin,
  16-stud walk-surface tiles from the current connected terrain body. It
  excludes 80 detached art components and leaves steep/open spans unbridged.
  Blender checks: 203 FBX meshes reimported including the origin marker; 2,893
  of 2,965 4-stud samples hit the custom surface, including 353/356 in the
  north approach; maximum sampled height deviation is 0.245 stud before the
  intentional 0.35-stud lowering. The loader is isolated to Stone Sentinels
  and disables joined visual collision only when the imported model is present.
  Studio imported and prepared all 202 parts. On a temporary assembled chunk,
  the joined visual's collision was off and all 253 reference rays hit at each
  of four yaws with maximum 0.351-stud error. A character walked about 95
  studs along the central route while grounded and at full health. The
  saved model is `assets/rbxm/chunks/verdant_valley/VV_STONE_SENTINELS_COLLISION.rbxmx`.
  XML inspection found 202 unique MeshIds and names, explicit precise fidelity
  on all parts, and a zero pivot. Rojo reloaded it: 94 north-approach rays all
  hit within 0.351 stud; a character walked to the north mouth grounded and
  at full health. Three deliberately omitted steep north-edge samples produced
  no Roblox collision hit, so the pilot did not bridge those openings. An
  owner visual walk at the exact prior failure spot and a
  two-client check remain before any kit-wide rollout.
  The owner requested that this prototype remain local until newer repository
  versions are reconciled; no push or PR has been made.
- **Stone Sentinels collider optimization:** On local branch
  `codex/vv-stone-collision-merge`, compatible adjacent 16-stud tiles from the
  same reviewed Blender scene collapse from 202 to 118 MeshParts (41.6% fewer).
  The original RBXMX remains as the known-good reference. The merged asset has
  118 unique uploaded meshes, a zero pivot, and explicit precise collision;
  Stone Sentinels alone now selects it through `CollisionTemplate`. Studio
  raycasts against the saved asset at four yaws hit 253/253 visible-surface
  samples with mean/p95/max height errors of 0.315/0.350/0.351 stud (original:
  0.333/0.350/0.351); all three cliff probes remained open. A 4-stud grid
  had 2,933 shared hits, 1,036 shared misses, zero one-sided hits, and at most
  0.220 stud height difference between colliders. A temporary loader build
  confirmed 118 pieces active with the visual mesh collision and queries off.
  An in-game character walk and owner visual check at the former invisible
  floor remain pending. Do not extend this optimization across the kit yet.
- **Overgrown Causeway split pilot (2026-09-28):** the reviewed joined mesh was
  separated into one connected terrain mesh (256 × 43.5 × 256) and one static
  scenery mesh containing 88 detached trees, rocks, ruins and moss components.
  Both mesh IDs load in the LUCKBOUND Studio place with precise collision. The
  `Collide` opt-in now builds static Tier 1 scenery on the server under the
  replicated chunk; the client skips those rows. A temporary four-yaw stage
  confirmed server-to-client replication with no duplicate client prop, sampled
  path raycasts, character traversal at all four rotations, and an obstacle
  stopping the character. This is a pilot check, not complete geometry coverage.
  A saved prop library, live `SizeY`/MeshId update, and two-client Studio test
  remain pending. Other 29 chunks and the old live Causeway asset are unchanged.
- **Wetland Pools joins (2026-09-28):** the temporary per-mouth socket-height
  change was reverted after the owner's next walk showed the route beyond
  Wetland Pools dropping by about two studs. The reviewed Blender mesh has
  both visible mouths at the same height; the higher Studio raycast hits were
  on its collision hull. Both socket offsets are zero again. Restart the live
  run to verify the restored route level, then inspect the collision hull
  separately. No mesh asset was replaced.
- **Full Verdant Valley separation candidate (2026-09-28):** Blender now has
  `verdant_valley_separated.blend` with 30 connected terrain objects and 66
  `prop_*` objects (37 solid, 29 ambient). Both FBXs were imported in Studio;
  staged `VV_STRUCTURE.rbxmx` and `VV_PROP_LIBRARY.rbxmx` contain all 96 named
  MeshParts and uploaded MeshIds, with anchored parts and precise collision on
  terrain and solid props. `ids.json`, a split report, and candidate chunk/prop content are staged under
  `assets/export/worlds/verdant_valley/`. The two former side-named cap meshes
  now use `chunk_cap_*` in the candidate. Exporter checks geometry conservation,
  colors, socket openings and FBX reimport; the candidate Luau suite passes.
  **Failed historical candidate, not the desired baseline.** The owner walk
  found invisible collision floors over lower terrain across the kit because
  each remaining terrain mesh was still large and concave. Do not activate or
  roll this candidate out; retain it only for diagnostics and tooling.

  | Id | Rarity | Weight | Phase | Map | Enterable? |
  |---|---|---|---|---|---|
  | `VERDANT_VALLEY` | Common | 6000 (60%) | 1 | chunk kit, 30 pieces — needs a revamp pass | ✅ |
  | `ETHEREAL_SCAPE` | Uncommon | 1500 (15%) | 1 | chunk kit, 41 pieces — hybrid isles/temple, §7.7 blueprint, not uploaded | ✅ |
  | `EMBERFALL` | Rare | 1500 (15%) | 1 | blueprint written | ❌ no kit |
  | `SKY_CITADEL` | Epic | 700 (7%) | 1 | chunk kit, 36 pieces — walked and verified | ✅ |
  | `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written | ❌ no kit |
  | `THE_UNKNOWN` | Unknown | 5 | 3 | none | ❌ no kit |

  (Supersedes the Worlds table in `docs/archive/STATUS_HISTORY.md`, written before Sky Citadel had a kit.)
- **Enemies:** the framework is built and all 16 Sky Citadel enemies are modelled, rigged and exported. The Winged
  Sentinel (Boss 3) runs in Studio through `/showboss`, with the Aether Lance's lightning and `/bossphase`. Ethereal
  Scape has a drafted 9-enemy roster (1 basic built: Aether Wisp) under `assets/source/enemies/ethereal_scape/`.
  **Nothing spawns in gameplay yet.** `EnemyDef` + services wait for the owner's OK.
- **Tooling:**
  - **Luau CLI (2026-09-28):** official `luau-lang/luau@0.740.0` is pinned in `rokit.toml` and installed locally. The assembled headless suite passes: 905/905. The CLI has no `--version` option; `rokit list` confirms the pin.
  - **Codex Studio MCP (2026-09-28):** connected to the LUCKBOUND place; a temporary Play stage supported the Causeway pilot check. Stopping Play discarded the test stage and temporary prop source.
  - **Developer panel + command registry** (2026-09-27): F4 in Studio; 39 commands, all clickable, autocomplete; see `docs/DEV_TOOLS.md`.
  - `INDEX.md` + `INDEX_MAP.md` give the repo map, and CI keeps the map current.
  - StyLua is enforced.
  - 908 headless tests passing locally as of 2026-09-28.

## 2. Next — pick up here

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
| **Verdant Valley 30-piece kit exported** | **Open 2026-09-25 — kit built and walked; needs a revamp pass** |
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
| **The Engine portal is to become the way into biomes** | **Architecture** |
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
