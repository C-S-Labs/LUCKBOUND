---
name: orchestrate
description: Opt-in orchestration for ONE task. Claude leads and drives Codex or Claude workers under docs/ORCHESTRATION.md. User-invoked only.
disable-model-invocation: true
argument-hint: <task>
---

# /orchestrate — Claude leads (this task only)

Task: $ARGUMENTS

You are the **orchestrator** for the task above, and only that task. Never carry this into later tasks unless the user
types `/orchestrate` again. Do not start it on your own because work looks large or Codex is installed.

**The protocol lives in `docs/ORCHESTRATION.md`. Read it now and follow it; it is the single source of truth and is
shared with Codex-led runs.** Read `INDEX.md` first (AGENTS.md Step 0). Do not restate or change the protocol here.

## Claude-specific mechanics

- **Modes you can lead:** A (Claude to Codex via `codex exec`, doc §10), C (Claude to Claude via the Agent tool), D
  (do it yourself, sequentially). Check `codex --version` before choosing A; if it fails, fall back to C or D and tell
  the user. Honour a mode the user names.
- **Task packets** go to a temp file outside the repo (the session scratchpad if one exists). Never write them into the
  repo, and never paste repository documents into them: give paths (doc §5).
- **Codex runs:** long ones go in the background (`run_in_background`) with a generous timeout. Several independent
  workers may run concurrently, one worktree each. If your own tool timeout kills a run, that is a `timeout`
  outcome (doc §8), not a failure of the implementation.
- **Worktrees and checkpoint:** create them yourself (doc §4, §8), under `ORCH_ROOT` (the `branch/` directory beside
  this clone). Never switch the owner's current checkout.
- **Git is yours alone.** Workers get the Git policy of doc §6. Review every diff yourself, check that no worker did
  Git it should not have, and never rely on the sandbox to prevent it.
- **Stop points:** two failed correction rounds; any protected-path touch; any unresolved design decision; any
  usage-limit failure (do not retry or probe). `/orchestrate` is not permission to push or open a PR.
- If the session dies, the user continues with `/orchestrate-resume` (or `$orchestrate-resume` in Codex).

When the task is reported back, orchestration is over.
