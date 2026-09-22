# LUCKBOUND — Instructions for AI Agents

You are working on a Roblox game.

## START HERE — read these three, in this order, before doing anything

This project runs across many separate conversations. Nothing carries over
between them except what is written in the repo, so these three files ARE the
handoff:

1. **`docs/WORKLOG.md` — the latest entry only.** Where the last session
   stopped and what comes next. Do not read the whole file; only the top entry
   is load-bearing.
2. **`docs/STATUS.md`** — current state, decisions already locked in, open
   items with severity. If you are about to relitigate a decision, it is
   probably recorded here as settled.
3. **`docs/PROTOTYPE_BUILD_SPEC.md`** — the canonical architecture.

**`docs/DEVELOPMENT_PLAN.md` says what to work on next**, and why in that
order. Read it before picking up anything that is not already in flight.

Then `docs/` has the rest: `MODULAR_MAPS.md`, `CHUNK_AUTHORING.md`,
`TESTING.md`, `ART_DIRECTION.md`,
`BLUEPRINT_RECONCILIATION.md`, `TOOLCHAIN_ACCESS.md`, `PLAYER_UI.md`,
`PLAYER_ABILITIES.md`, `EVENTS.md`.

## BEFORE YOU FINISH — update the handoff

A session that leaves no trace has to be re-derived from scratch next time.
Before ending any session where you changed something:

- **Append a `docs/WORKLOG.md` entry at the top** using the template there:
  what you did, what you decided, where you stopped, what comes next.
- **Update `docs/STATUS.md`** if state changed — test count, what is built,
  open items, next-session priorities.
- **Update the doc that owns the thing you changed** (scale → `ART_DIRECTION`
  and `MODULAR_MAPS`; architecture → the build spec; and so on).

Documentation is not an afterthought on this project — it is the only memory
it has.

This file is the short version of the rules that protect the architecture.

## The prime directive

> **Systems are reusable. Content is data.**

A System contains behaviour and no content. Content is a plain table. Adding a new world, enemy, item or discovery must require editing exactly one file under `src/shared/Content/` and changing no System.

If implementing a piece of content seems to require changing a System, **the schema is wrong.** Stop, say so, and propose a spec amendment. Do not special-case it.

## Hard rules

1. **Never create a second version of a module.** No `CombatSystem_Final`, `_NEW`, `_FIXED`, `_v2`, `_old`, `_backup`. Fix the original or delete it. CI greps for these and fails the build.
2. **Never invent a RemoteEvent.** The complete list lives in §4 of the build spec and is created only by `src/shared/Core/Net.luau`. Need a new one? Add it to the spec table first, in the same PR.
3. **Never invent a naming convention.** Modules `PascalCase`. Content Ids `UPPER_SNAKE`. Remotes `Domain_Action`. Locals `camelCase`. Constants `UPPER_SNAKE`.
4. **Never put a magic number in a System.** Every tunable lives in `Core/GameConfig.luau`. If you typed a number that a designer might want to change, it belongs there.
5. **Never trust the client.** No client-supplied number, position, index or instance is used without server validation. Rolls, damage and loot are decided server-side, always.
6. **Never use `math.random`.** Use the `Random` instance owned by the relevant System, so results are seedable and auditable.
7. **Never require a System from another System at module scope.** Dependencies are passed into `init()`. Circular requires are a hard error.
8. **Never widen scope.** §7 of the build spec lists what Phase 1 deliberately excludes. If a task seems to need one of those, the task is wrong — raise it.

## Boot order

Fixed, in `src/server/init.server.luau`. See build spec §1.2. `Schema.validateAll()` runs first and the server must refuse to start if it fails.

## Style

- Luau with `--!strict` at the top of every module.
- StyLua and Selene are configured; run them before committing.
- Return a single table from every ModuleScript.
- Errors use the `Result` convention in `Core/Result.luau` — `{ok = true, value = …}` or `{ok = false, err = …}`. Reserve `error()` for programmer mistakes, not expected failures.

## Verify before you merge

CI runs the tests, a syntax check, and the forbidden-name scan. **Check that it
is green before merging a PR.** This was skipped once and shipped a `main` that
could not boot, because `git commit -am` silently skipped a new untracked file.

- `git add` new files explicitly — `-am` stages only tracked ones.
- Run `./tests/run.sh` before pushing.
- A shim in the test harness must behave like the real Roblox type. An
  unfaithful one is worse than no test: `Vector3` faked as a table once let a
  boot-blocking bug pass 152 tests.

## When you are unsure

Ask. A question costs a minute. A second competing architecture costs the project.
