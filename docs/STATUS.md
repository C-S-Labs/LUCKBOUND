# LUCKBOUND — Project Status

**Last updated:** 2026-09-16 · **Phase 1 complete · expedition entry opened (build spec §7.1)**

> **New conversation?** Read `WORKLOG.md`'s top entry first for where the last
> session stopped, then this file. `CLAUDE.md` has the rules.

Start here. This is the handoff document: what exists, what is decided, what is
open, and where to pick up.

---

## 1. Where the project stands

Phase 1's goal was one sentence: *you can walk around a recognizable LUCKBOUND
hub and press ROLL.* That is done, running in Roblox Studio, and playtested.

**As of 2026-09-16 the roll has somewhere to go.** Owner-directed amendment
§7.1 lifted expedition entry out of the Phase 1 exclusion list: you can roll
Ethereal Scape, walk through the Expedition Gate, and stand in a map generated
from its chunk kit. **Combat, enemies, bosses and loot were NOT lifted and
remain excluded.** An expedition today is: arrive, walk a generated map, come
home.

⏳ **Not yet seen in Studio.** Everything below is green in CI and nobody has
walked it. That is the top of the next session's list.

**The Design North Star (Master Spec §25) has been answered.** After playing the
roll loop with no combat, no loot, no art and grey blockout geometry, the
owner's verdict was: *"these rolls alone were fun."* Nothing was propping it up,
which makes that the strongest possible signal the core premise works.

### Verified working in Studio

| | Evidence |
|---|---|
| Server boots clean | `[LUCKBOUND] boot 9/9` → `server ready` (now 10 steps) |
| Hub generates procedurally | `[HubBuilder] built Crossroads: 5 zones, 436 instances` |
| 15-roll onboarding, exact order | Full arc logged, Epic at roll 8 |
| True RNG hands over at roll 16 | Roll 16 logged with no `(onboarding)` tag |
| ProximityPrompt roll interaction | `[E] ROLL` at the Fate Engine |
| Reveal pacing scales with rarity | Measured 9.4 s (Rare) vs 12.2 s (Mythic) |
| Runs without DataStores | Volatile-mode fallback, no crash |

**436 instances** is the current mobile-budget baseline for the hub.

### Expedition entry — new 2026-09-16

| | |
|---|---|
| Enterable worlds | **Verdant Valley, Ethereal Scape** |
| Rollable but NOT enterable | Emberfall (15%), Sky Citadel (7%), Astral Reach (3%) |
| Entry point | Expedition Gate `ProximityPrompt`, server-side `Triggered` |
| Destination | the player's **last roll** — no new state, survives rejoin |
| Map | `ChunkCore` assembles, `ChunkLoader` builds, seeded per expedition |
| Seed | `(userId, TotalRolls, worldId)` — logged, so any map can be rebuilt |
| Lighting | applied **per client**, restored on exit. Never bleeds |
| Return | a small rarity-coloured portal on the arrival chunk, or the timer |
| Reward | +25 Fate on completion or return; **nothing for dying** |
| Switch | `GameConfig.Expedition.Enabled` — one boolean back to Phase 1 |

**25% of honest rolls currently land on a world with no map.** Those players are
told *"That world has no map yet."* and stay in the hub. It is handled, not
solved — see §4.

### World scale — rescaled 2026-09-16

The hub was 120 studs across: 24 character-heights, with a 5×5 Discovery
Archive. It read as a room.

| | Before | After |
|---|---|---|
| Hub playable Ø | 120 | **1200** |
| Zone ring radius | 46 | **420** |
| Zone platforms | 26–56 | **230–360** |
| WalkSpeed | 16 (default) | **32** |
| Visual extent | ~420 | **4000** |
| Chunk grid | 48 | **256** |

**Playable footprint and perceived size are separate numbers.** 4000 studs is
not walkable — 43.8s to a zone even at double speed. 1200 at WalkSpeed 32 gives
13.1s centre-to-centre, ~4.4s edge-to-edge, and scenery reaching 4000 makes the
world read as vast anyway.

Both halves are **enforced by test**: no zone may exceed
`Scale.MaxTraversalSeconds` (20s), every zone must be ≥40 characters across, and
expedition walking must stay under 35% of expedition duration.

⏳ **Not yet seen in Studio.** Verified by test; nobody has walked it.

### Modular map system

Added 2026-09-16. `assets/` holds Blender sources; `AssetManifest` maps logical
names to Roblox asset ids; `Content/Chunks/` holds authored pieces; `ChunkCore`
assembles them into a seeded, collision-free, deterministic layout; and
`ChunkLoader` turns that layout into walkable geometry.

**Two kits now exist, and the second one is the interesting result.** Ethereal
Scape's was authored against the checklist rather than against Verdant Valley,
with its own socket vocabulary (`SPAN`/`RITE` vs `PATH`/`WIDE`) — and the same
emergent gate-to-the-boss property fell out of it. Nobody wrote that rule; it is
the reserved-Kind rule generalising. See `MODULAR_MAPS.md`.

All 16 pieces are `PLACEHOLDER`, so the loader draws **labelled blockout** —
each platform carries its ChunkId and Role, with a neon post at every socket
coloured by Kind. **A generated map is verifiable by eye before any mesh
exists.**

### Test suite

**276 tests, all passing.** Headless — no Roblox required.

```bash
./tests/run.sh
```

CI runs them on every push, plus a syntax check and the forbidden-module-name
scan (build spec P1-12).

---

## 2. What is built

```
src/shared/Core/     Types, Constants, GameConfig, Net, UITheme, Result,
                     FateCore, ProgressionCore, ProfileSchema, EventCore,
                     ExpeditionCore
src/shared/Util/     WeightedRandom, Schema, PortalRig, ChunkCore, ChunkLoader
src/shared/Content/  Worlds/ (6), Hub/Crossroads, Chunks/ (2 kits), AssetManifest
src/server/          init.server + Systems/ (Save, Progression, Fate, Event,
                                             Expedition, HubBuilder)
src/client/          init.client + Controllers/ (State, Proximity, HubEffects,
                                                 Expedition)
                                 + UI/ (FateRoll, GlobalAnnouncements, ExpeditionHud)
```

**Pure cores are the reason the test suite exists.** `FateCore`,
`ProgressionCore`, `ProfileSchema`, `EventCore` and `ExpeditionCore` hold every
decision with no Roblox globals, so they run headlessly. Systems hold only
plumbing.

`ChunkCore` / `ChunkLoader` is the same split applied to geometry: the first
decides what goes where and is pure, the second turns plain numbers into
Instances and knows no rules. **The seam between them is a list of numbers, and
that seam is why map generation is testable at all.**

### Worlds

| Id | Rarity | Weight | Phase | Biome? | Enterable? |
|---|---|---|---|---|---|
| `VERDANT_VALLEY` | Common | 6000 (60%) | 1 | blueprint written | ✅ kit |
| `ETHEREAL_SCAPE` | Uncommon | 1500 (15%) | 1 | **authored art** | ✅ kit |
| `EMBERFALL` | Rare | 1500 (15%) | 1 | blueprint written | ❌ no kit |
| `SKY_CITADEL` | Epic | 700 (7%) | 1 | ⚠️ **none — data only** | ❌ no kit |
| `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written | ❌ no kit |
| `THE_UNKNOWN` | Unknown | 5 | 3 | none | ❌ no kit |

Weights sum to 10000 so they read directly as percentages. Verified at 400,000
draws, worst drift 0.062pp.

**Ethereal Scape** is the first world with authored art behind it —
`assets/source/worlds/ethereal_scape/aether_environment_refined.blend`, a sky
temple above the cloud deck: eight gold-rimmed meadow islands, bridges between
them, seven waystones, and an R6 rig in a `Scale_Reference` collection so the
metre-to-stud conversion can be checked rather than assumed. Its eight chunks
map 1:1 onto those eight islands. It declares **no enemies, boss or loot on
purpose** — it is the map-generation test biome, and giving it combat content
would make it a worse test.

---

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
| — | **Expedition entry is open; combat/loot are not** | spec §7.1 |
| — | Destination = the player's last roll. No new state, no schema bump | `ExpeditionCore` |
| — | Biome lighting is applied **per client**, never by the server | Blueprint §6 |
| — | Rarity colour is a UI/portal contract; biome palette is set dressing | Blueprint §4.1 |
| — | Compass mapping N=-Z, E=+X, S=+Z, W=-X, up=+Y | GameConfig.HubLayout |

### Why true RNG matters downstream

With no odds tilting, **a player at roll 200 faces identical odds to one at roll
16.** "Stuck in Commons" is a permanent condition, not an early-game phase.
Fate cannot weight its way out of it.

The lever that stays consistent: **Fate unlocks which pools you draw from,
never how the draw resolves.** Higher Fate grants access to a pool that has no
Common in it. That is the Phase 3 design, and it is the answer to the
progression-feel problem.

---

## 4. Open items

### Needs the owner's sign-off

Four items in `BLUEPRINT_RECONCILIATION.md`. The significant one:

**Blueprint §1.1's Usage column contradicts §4.4 and §5.4** over which world
carries Mythic orange. Resolved in favour of §4.4/§5.4 (Emberfall = Rare blue,
Astral Reach = Mythic orange) and locked by test. Confirming closes it for every
future world's asset prompts.

Also open: rarity ordering (Mythic above Legendary) and formal confirmation of
the theme-vs-rarity rule.

⚠️ **The `UNCOMMON` colour just became urgent.** It was theoretical while
Uncommon belonged to a Phase 3 world nobody could roll. Ethereal Scape is
Uncommon, live at 15%, and guaranteed at onboarding roll 5 — so the
unsanctioned green `#5FD97A` is now on screen for every player within a minute
of joining. Bless it or replace it **before** people learn it.

### Known debt

| Item | Severity | Notes |
|---|---|---|
| **25% of rolls land on a world with no map** | **High** | Emberfall 15%, Sky Citadel 7%, Astral Reach 3%. Refused politely at the Gate; printed as a boot warning and asserted by test. Emberfall and Astral Reach need only a chunk kit; Sky Citadel needs a blueprint section first. |
| **Nothing since the rescale has been in Studio** | **Unknown** | The 10× world *and* the whole expedition path are test-verified only. `TESTING.md` Test C2 is the pass. |
| `UNCOMMON` colour unsanctioned | Medium | Now shipping — see above |
| Chunk collision is XZ-only | Medium | Blocks any kit that climbs. `MODULAR_MAPS.md` |
| No pathfinding validation | Medium | Non-overlapping ≠ walkable between. Addendum §A4 step 4 |
| All 16 chunks are `PLACEHOLDER` | Expected | Blockout is deliberate; upload is a per-piece change |
| Hub is very dark | Cosmetic | `Crossroads.Theme` — one value |
| UI needs resize/layout pass | Cosmetic | Owner-flagged |
| Placeholder text | Cosmetic | Flavour lines, labels, result card |
| Octagonal plinth is a cylinder | Cosmetic | First thing an authored mesh replaces |
| Training dummies inert | By design | Combat is Phase 2; tagged `Phase = 2` |

---

## 5. Next session — pick up here

**Everything below the line is unplayed.** The 10× rescale and the entire
expedition path are green in CI and have never been in Studio. Nothing else on
this list is worth doing before that.

1. **Run `TESTING.md` Test C2.** Roll to 5, take the Gate, walk Ethereal Scape,
   come home. It answers four questions at once: does the new scale feel right,
   does map generation produce a *place*, does per-client lighting restore, and
   is walking through the Gate a payoff or an anticlimax.
2. **Hub brightness** — one value in `Crossroads.Theme`. Minutes.
3. **Upload the Ethereal Scape islands.** `assets/README.md` has the full
   walkthrough. Check scale against the R6 rig on the whole-scene import
   *before* splitting into eight, or it is eight re-uploads.
4. **A chunk kit for Emberfall** — biggest single reduction in the "no map"
   number, 15pp, and its blueprint section already exists.
5. **Placeholder text** — flavour lines, result card copy, zone labels.
6. **UI overhaul** — `FateRoll` and `GlobalAnnouncements` resize/layout, mobile
   scaling. `UITheme` already centralises fonts and colours.
7. **Sky Citadel biome** — still the largest content debt.
8. **Phase 2 proper** — combat, loot, the Discovery Book. Build spec §7 still
   excludes all of it.

### Working agreement that emerged this session

- Small steps with a checkpoint, not ten instructions at once.
- Verify CI is green **before** merging. This was violated once (PR #7) and
  shipped an unbootable `main`.
- `git add` new files explicitly. `git commit -am` silently skips untracked
  files — that is exactly how PR #7 broke.

---

## 6. Environment

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

## 7. Document map

| Document | Purpose |
|---|---|
| `PROTOTYPE_BUILD_SPEC.md` | **Canonical.** Architecture, schemas, remotes, tasks |
| `STATUS.md` | This file — current state and handoff |
| `TESTING.md` | Running tests, and the Studio manual pass |
| `BLUEPRINT_RECONCILIATION.md` | How the Biome Blueprint merged; open sign-offs |
| `ART_DIRECTION.md` | How to describe the look so it becomes code |
| `TOOLCHAIN_ACCESS.md` | Studio MCP, Rojo, Blender, assets, setup |
| `WORKLOG.md` | **Session history and handoff points — read the top entry** |
| `MODULAR_MAPS.md` | The chunk system: how biome maps assemble from pieces |
| `../assets/README.md` | Blender → Roblox asset workflow |
| `ADDENDUM_ASSET_PIPELINE.md` | Future asset/procgen architecture — target design |
| `LUCKBOUND_Master_Spec_v0.2.pdf` | Master design spec, updated with build reality |
| `../LUCKBOUND_...v0.1 (1).pdf` | Original vision. **Authoritative on intent.** |

`CLAUDE.md` in the repo root holds the rules every AI agent must follow.
