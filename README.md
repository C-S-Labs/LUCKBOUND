# LUCKBOUND

> Roll your fate. Enter the unknown. Become legendary.

A Roblox adventure/RNG game. Players roll Fate at the Crossroads to determine
which world they enter, fight and explore it for rare discoveries and powers,
and progressively gain control over their own RNG — occasionally triggering
global events that affect everyone playing.

**Phase 1 is complete and verified in Roblox Studio.** You can walk around the
Crossroads, press ROLL, and watch a destination resolve. 167 tests passing.

Next up: Phase 2 — expedition entry, combat, loot, Discovery Book.

## Read these first

| Document | What it is |
|---|---|
| [`docs/STATUS.md`](docs/STATUS.md) | **Start here.** Current state, decisions locked in, open items, where to pick up |
| [`docs/PROTOTYPE_BUILD_SPEC.md`](docs/PROTOTYPE_BUILD_SPEC.md) | **Canonical.** Architecture, data schemas, RemoteEvent contract, task list |
| [`docs/TESTING.md`](docs/TESTING.md) | Running the 167 tests, and the Studio manual pass |
| [`docs/BLUEPRINT_RECONCILIATION.md`](docs/BLUEPRINT_RECONCILIATION.md) | How the Biome Blueprint merged; 4 items needing sign-off |
| [`docs/WORKLOG.md`](docs/WORKLOG.md) | Session history and handoff points — **read the top entry first** |
| [`docs/MODULAR_MAPS.md`](docs/MODULAR_MAPS.md) | The chunk system: how biome maps assemble from authored pieces |
| [`docs/CHUNK_AUTHORING.md`](docs/CHUNK_AUTHORING.md) | Modelling a chunk in Blender: origin, scale, sockets, export |
| [`assets/README.md`](assets/README.md) | Blender → Roblox asset workflow |
| [`docs/ART_DIRECTION.md`](docs/ART_DIRECTION.md) | How to describe the look so it becomes code |
| [`docs/TOOLCHAIN_ACCESS.md`](docs/TOOLCHAIN_ACCESS.md) | Rojo, Rokit, Studio MCP, Blender, assets |
| [`docs/ADDENDUM_ASSET_PIPELINE.md`](docs/ADDENDUM_ASSET_PIPELINE.md) | Future asset/procgen architecture — **out of scope for now** |
| [`docs/LUCKBOUND_Master_Spec_v0.2.pdf`](docs/LUCKBOUND_Master_Spec_v0.2.pdf) | Master design spec, revised against the working prototype |
| `LUCKBOUND_..._v0.1 (1).pdf` | The original vision. **Authoritative on intent** — kept unchanged |
| [`CLAUDE.md`](CLAUDE.md) | Rules every AI agent on this project must follow |

## Quick start

```bash
./tests/run.sh         # 208 headless tests, no Studio needed

rokit install          # rojo 7.6.0, stylua, selene
rojo plugin install    # Studio plugin
rojo serve             # then hit Connect in the Rojo plugin inside Studio
```

Enable **Game Settings → Security → Studio Access to API Services** before
playtesting, or DataStores fail silently.

## Two rules that shape everything

**Systems are reusable. Content is data.** Adding a world means adding one file
under `src/shared/Content/Worlds/` and changing no System. If that isn't true,
the schema is wrong — see `CLAUDE.md`.

**The roll is true RNG.** No player state — Fate level, points, playtime, spend —
changes the odds of any world. Fate is a score and unlock stat, never a thumb on
the scale. A scripted 3-roll onboarding shows every new player the full rarity
ladder in their first few minutes; after that it is honest chance forever.
See build spec §3.3.

## What's built

- [x] Canonical build spec, toolchain guide, art brief, testing guide
- [x] Rojo project; `Core` (Types, Constants, GameConfig, Net, UITheme, Result)
- [x] Pure cores — `FateCore`, `ProgressionCore`, `ProfileSchema`, `EventCore`
- [x] `Util` — `WeightedRandom`, `Schema`, `PortalRig`
- [x] Systems — `Save` (session-locked), `Progression`, `Fate`, `Event`, `HubBuilder`
- [x] Client — `FateRoll`, `GlobalAnnouncements`, `State`/`Proximity`/`HubEffects` controllers
- [x] The Crossroads: 5 zones, 436 instances, generated from data per the Biome Blueprint
- [x] 15-roll onboarding arc peaking on Epic; true RNG from roll 16
- [x] Modular map system — asset manifest, chunk kit, seeded assembler
- [x] 5 worlds; 208-test headless suite + CI
- [ ] **Sky Citadel biome** — art direction and a 22-piece kit exported: turns both ways, a crossroads, caps so no path leads to nothing (`docs/SKY_CITADEL.md`); needs upload, enemies and a boss
- [ ] Phase 2 — expedition entry, combat, loot, Discovery Book
