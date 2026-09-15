# LUCKBOUND — Instructions for AI Agents

You are working on a Roblox game. **Read `docs/PROTOTYPE_BUILD_SPEC.md` before writing any code.** It is the canonical architecture. This file is the short version of the rules that protect it.

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

## When you are unsure

Ask. A question costs a minute. A second competing architecture costs the project.
