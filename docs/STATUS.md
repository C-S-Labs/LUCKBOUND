# LUCKBOUND — Project Status

**Last updated:** 2026-09-16 · **Phase 1: COMPLETE and verified in Studio**

> **New conversation?** Read `WORKLOG.md`'s top entry first for where the last
> session stopped, then this file. `CLAUDE.md` has the rules.

Start here. This is the handoff document: what exists, what is decided, what is
open, and where to pick up.

---

## 1. Where the project stands

Phase 1's goal was one sentence: *you can walk around a recognizable LUCKBOUND
hub and press ROLL.* That is done, running in Roblox Studio, and playtested.

**The Design North Star (Master Spec §25) has been answered.** After playing the
roll loop with no combat, no loot, no art and grey blockout geometry, the
owner's verdict was: *"these rolls alone were fun."* Nothing was propping it up,
which makes that the strongest possible signal the core premise works.

### Verified working in Studio

| | Evidence |
|---|---|
| Server boots clean, 9/9 steps | `[LUCKBOUND] boot 9/9` → `server ready` |
| Hub generates procedurally | `[HubBuilder] built Crossroads: 5 zones, 436 instances` |
| 15-roll onboarding, exact order | Full arc logged, Epic at roll 8 |
| True RNG hands over at roll 16 | Roll 16 logged with no `(onboarding)` tag |
| ProximityPrompt roll interaction | `[E] ROLL` at the Fate Engine |
| Reveal pacing scales with rarity | Measured 9.4 s (Rare) vs 12.2 s (Mythic) |
| Runs without DataStores | Volatile-mode fallback, no crash |

**436 instances** is the current mobile-budget baseline for the hub.

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
assembles them into a seeded, collision-free, deterministic layout.

All 8 Verdant Valley pieces are `PLACEHOLDER` — **layouts assemble and validate
before any mesh exists.** The Roblox-side loader is Phase 2.

### Test suite

**208 tests, all passing.** Headless — no Roblox required.

```bash
./tests/run.sh
```

CI runs them on every push, plus a syntax check and the forbidden-module-name
scan (build spec P1-12).

---

## 2. What is built

```
src/shared/Core/     Types, Constants, GameConfig, Net, UITheme, Result,
                     FateCore, ProgressionCore, ProfileSchema, EventCore
src/shared/Util/     WeightedRandom, Schema, PortalRig, ChunkCore
src/shared/Content/  Worlds/ (5), Hub/Crossroads, Chunks/, AssetManifest
src/server/          init.server + Systems/ (Save, Progression, Fate, Event, HubBuilder)
src/client/          init.client + Controllers/ (State, Proximity, HubEffects)
                                 + UI/ (FateRoll, GlobalAnnouncements)
```

**Pure cores are the reason the test suite exists.** `FateCore`,
`ProgressionCore`, `ProfileSchema` and `EventCore` hold every decision with no
Roblox globals, so they run headlessly. Systems hold only plumbing.

### Worlds

| Id | Rarity | Weight | Phase | Biome? |
|---|---|---|---|---|
| `VERDANT_VALLEY` | Common | 7000 (70%) | 1 | blueprint written |
| `EMBERFALL` | Rare | 2000 (20%) | 1 | blueprint written |
| `SKY_CITADEL` | Epic | 700 (7%) | 1 | ⚠️ **none — data only** |
| `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written |
| `THE_UNKNOWN` | Unknown | 5 | 3 | none |

Weights sum to 10000 so they read directly as percentages. Verified at 400,000
draws, worst drift 0.113pp.

---

## 3. Decisions locked in

These are settled. Do not relitigate without a deliberate reversal.

| # | Decision | Where |
|---|---|---|
| **D-8** | **Fate is TRUE RNG.** No player state ever changes the odds of any world. | spec §3.3 |
| **D-9** | **15-roll scripted onboarding**, peaking on Epic at roll 8, never Mythic. | spec §3.3.1 |
| D-3 | Roll cooldown 3.0 s, enforced server-side, silent on rejection | spec §3.4 |
| D-4 | Reveal duration scales with rarity (2.5 s → 7.0 s) | Constants |
| D-6 | Roll history capped at 50 entries | GameConfig |
| D-7 | Expedition 720 s — **flagged as likely too long**, revisit in Phase 2 | spec §6 |
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

Also open: rarity ordering (Mythic above Legendary), a blueprint-sanctioned
colour for `UNCOMMON`, and formal confirmation of the theme-vs-rarity rule.

### Known debt

| Item | Severity | Notes |
|---|---|---|
| **Sky Citadel has no biome** | **Blocks Phase 2** | Rolling it would send players nowhere. Needs a blueprint section, enemies, boss, loot. |
| Hub is very dark | Cosmetic | `Crossroads.Theme` — one value |
| New scale unplayed | Unknown | Verified by test only; needs a Studio walk |
| UI needs resize/layout pass | Cosmetic | Owner-flagged |
| Placeholder text | Cosmetic | Flavour lines, labels, result card |
| Octagonal plinth is a cylinder | Cosmetic | First thing an authored mesh replaces |
| Training dummies inert | By design | Combat is Phase 2; tagged `Phase = 2` |

---

## 5. Next session — pick up here

The owner's stated list, in their words: **UI overhaul with resizing,
placeholder text, and other tuning.**

Cheapest-to-most-expensive:

1. **Playtest the new scale.** Does 1200 studs feel right, or still small? Is
   WalkSpeed 32 comfortable? Both are one-line changes in `GameConfig`.
2. **Hub brightness** — one value in `Crossroads.Theme`. Minutes.
3. **Placeholder text** — flavour lines, result card copy, zone labels.
4. **UI overhaul** — `FateRoll` and `GlobalAnnouncements` resize/layout, mobile
   scaling. `UITheme` already centralises fonts and colours.
5. **Sky Citadel biome** — required before Phase 2.
6. **Phase 2** — expedition entry, combat, loot, Discovery Book. Build spec §7
   lists what Phase 1 deliberately excludes.

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
