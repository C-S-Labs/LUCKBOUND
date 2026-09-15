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
| [`docs/TOOLCHAIN_ACCESS.md`](docs/TOOLCHAIN_ACCESS.md) | How to connect an AI agent to Roblox Studio, Rojo and Blender |
| [`CLAUDE.md`](CLAUDE.md) | Rules every AI agent on this project must follow |
| `LUCKBOUND_Master_Game_Design_Development_Specification_v0.1 (1).pdf` | The original design vision. Authoritative on *intent* |

## Quick start

```bash
rokit install          # rojo 7.6.0, stylua, selene
rojo plugin install    # Studio plugin
rojo serve             # then hit Connect in the Rojo plugin inside Studio
```

## Architecture in one line

**Systems are reusable. Content is data.** Adding a world means adding one file
under `src/shared/Content/Worlds/` and changing no System. If that isn't true,
the schema is wrong — see `CLAUDE.md`.

## What's built

- [x] Canonical Phase 1 build specification
- [x] Toolchain / AI access guide
- [x] Rojo project scaffold
- [x] `Core/Types`, `Core/Constants`, `Core/GameConfig`, `Core/Net`
- [x] `Util/WeightedRandom`
- [x] World content: Verdant Valley, Emberfall, Astral Reach (+ The Unknown, Phase 3)
- [ ] `Util/Schema`, SaveSystem, ProgressionSystem, FateSystem, HubBuilder, UI — tasks T-107 onward
