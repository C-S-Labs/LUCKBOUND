# LUCKBOUND — Project Status

**Last updated:** 2026-09-30 · slimmed for token use. The full previous version, with every closed item and walk
report, is `docs/archive/STATUS_HISTORY.md`. Read it only by section, when an item below points to it.

> **New conversation?** Read `INDEX.md` → `AGENTS.md` → the top entry of `docs/WORKLOG.md` → this file.

---

## 1. Where the project stands

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
  polish pass done (map-wide skyrays, natural mushroom patches, overhang check) — **uploaded IDs retained; integrated Studio walk pending**). Emberfall and Astral
  Reach have no map yet.

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
