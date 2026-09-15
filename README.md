# LUCKBOUND

> Roll your fate. Enter the unknown. Become legendary.

A Roblox adventure/RNG game. Players roll Fate at the Crossroads to determine
which world they enter, fight and explore it for rare discoveries and powers,
and progressively gain control over their own RNG — occasionally triggering
global events that affect everyone playing.

**Current stage: Phase 1 — Foundation.**
The goal is one sentence: *you can walk around a recognizable LUCKBOUND hub and press ROLL.*

## Read these first

| Document | What it is |
|---|---|
| [`docs/PROTOTYPE_BUILD_SPEC.md`](docs/PROTOTYPE_BUILD_SPEC.md) | **Canonical.** Architecture, data schemas, RemoteEvent contract, the Phase 1 task list |
| [`docs/TESTING.md`](docs/TESTING.md) | How to run the tests and what to check in Studio |
| [`docs/TOOLCHAIN_ACCESS.md`](docs/TOOLCHAIN_ACCESS.md) | How to connect an AI agent to Roblox Studio, Rojo and Blender |
| [`CLAUDE.md`](CLAUDE.md) | Rules every AI agent on this project must follow |
| `LUCKBOUND_Master_Game_Design_Development_Specification_v0.1 (1).pdf` | The original design vision. Authoritative on *intent* |

## Quick start

```bash
./tests/run.sh         # 83 headless tests, no Studio needed

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

- [x] Canonical Phase 1 build specification
- [x] Toolchain / AI access guide
- [x] Rojo project scaffold
- [x] `Core/Types`, `Core/Constants`, `Core/GameConfig`, `Core/Net`
- [x] `Util/WeightedRandom`, `Util/Schema`
- [x] `FateCore`, `ProgressionCore`, `ProfileSchema`, `EventCore` (pure, unit-tested)
- [x] `SaveSystem` (session-locked), `ProgressionSystem`, `FateSystem`, `EventSystem`
- [x] Server bootstrap with fail-fast content validation
- [x] World content: Verdant Valley, Emberfall, Astral Reach (+ The Unknown, Phase 3)
- [x] 83-test headless suite + CI
- [ ] `HubBuilder` (T-112) and client UI (T-114–T-117) — best done locally in Studio
