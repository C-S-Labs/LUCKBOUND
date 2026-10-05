---
name: orchestrate
description: Opt-in orchestration for ONE task. Codex leads and drives Codex workers under docs/ORCHESTRATION.md. Use only when the user explicitly invokes $orchestrate.
---

# $orchestrate — Codex leads (this task only)

The task is the user's request that invoked this skill, and only that task. Do not carry this into later tasks unless
the user invokes `$orchestrate` again. Never start it on your own because work looks large.

You are the **orchestrator**. **The protocol lives in `docs/ORCHESTRATION.md`. Read it now and follow it; it is the
single source of truth and is shared with Claude-led runs.** Read `INDEX.md` and `AGENTS.md` first as usual. This
skill adds nothing to `AGENTS.md` and changes no standalone Codex behaviour.

## Codex-specific mechanics

- **Mode B (Codex to Codex).** Prefer Codex's native subagents (`codex features list` should show `multi_agent`
  enabled). If they are unavailable, run workers as `codex exec` children (doc §10). **Do not use the removed
  `codex mcp-server`.** If neither works, use Mode D and tell the user.
- **Subagents are workers.** They get a task packet (doc §5), work only in the worktree path you give them, and never
  spawn further workers or change the plan.
- **Worktrees and checkpoint:** create them yourself (doc §4, §8), under `ORCH_ROOT` (the `branch/` directory beside
  this clone). Never switch the owner's current checkout. Creating worktrees and writing the checkpoint need
  access outside the working directory; request approval rather than working around it.
- **Git is yours alone.** Workers get the Git policy of doc §6. Review every diff yourself and never rely on the
  sandbox to prevent worker Git.
- **Stop points:** two failed correction rounds; any protected-path touch; any unresolved design decision; any
  usage-limit failure (do not retry or probe). `$orchestrate` is not permission to push or open a PR.
- Your shell is PowerShell 5.1 on Windows: no `&&`.
- If the session dies, the user continues with `$orchestrate-resume` (or `/orchestrate-resume` in Claude Code).

When the task is reported back, orchestration is over.
