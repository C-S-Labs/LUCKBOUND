# LUCKBOUND — Project Status

**Last updated:** 2026-09-25 · slimmed for token use. The full previous version, with every closed item and walk
report, is `docs/archive/STATUS_HISTORY.md`. Read it only by section, when an item below points to it.

> **New conversation?** Read `INDEX.md` → `AGENTS.md` → the top entry of `docs/WORKLOG.md` → this file.

---

## 1. Where the project stands

- **Phase 1 is complete** (hub, roll, onboarding, saves, UI, sprint and double jump, events). The build spec §7
  amendments that opened later work are §7.1 expedition entry, §7.2 parties as their own server, §7.3 scenarios,
  §7.4 caps and §7.5 loot.
- **Worlds you can enter:** Verdant Valley (30-piece kit), Sky Citadel (36 pieces, walked, with ambience, props,
  chests and the vault) and Ethereal Scape (prebuilt map). Emberfall and Astral Reach have no map yet.
- **Enemies:** the framework is built and all 16 Sky Citadel enemies are modelled, rigged and exported. The Winged
  Sentinel (Boss 3) runs in Studio through `/showboss`, with the Aether Lance's lightning and `/bossphase`.
  **Nothing spawns in gameplay yet.** `EnemyDef` + services wait for the owner's OK.
- **Tooling:**
  - `INDEX.md` + `INDEX_MAP.md` give the repo map, and CI keeps the map current.
  - StyLua is enforced.
  - 808 tests pass in CI.

## 2. Next — pick up here

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
| **World ambience** | **Built 2026-09-23, unwalked** |
| **Ambient props** | **Live 2026-09-23, unwalked** |
| **Loot, fixtures, vault keys** | **Live 2026-09-23, unwalked** |
| **Verdant Valley 30-piece kit exported** | **Open 2026-09-24** |
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
| **First-join intro screen** | **Built, unwalked** |
| **The Engine portal is to become the way into biomes** | **Architecture** |
| **The authored Fate Engine is wired but unwalked** | **Open** |
| **Ethereal Scape's `Scale_Reference` proxy is loose** | Low |
| **The scene has no `EntryAnchor` / `ReturnAnchor`** | Medium |
| **Ethereal Scape: one whole map, not eight chunks** | Decided 2026-09-17 |
| **The Crossroads wants a revamp after testing** | **Design** |
| **Staircase clipping at the walkway junctions** | Medium |
| **The live menu tint is unseen** | **High** |
| **Rifts: event-gated dungeons** | **Design** |
| **The event sky is built and unwalked** | **High** |
| **The event catalogue is a proposal, not a plan** | **Design** |
| **Three panels are designed, not implemented** | Expected |
| **Five settings are stored and honoured by nothing** | Medium |
| **Travel landings are guesses with a safety net** | Medium |
| **Profile schema is now v2** | Note |

## 5. Environment

- Code: `C:\Dev\luckbound` (not OneDrive — must stay outside it)
- Place: `LUCKBOUND_dev.rbxl`, local, unpublished
- Rojo CLI 7.6.0 via Rokit; Studio plugin 7.7.0
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
