---
name: orchestrate-resume
description: Resume an interrupted orchestration from its checkpoint (any previous lead, Claude or Codex). Use only when the user explicitly invokes $orchestrate-resume.
---

# $orchestrate-resume — Codex takes over an interrupted orchestration (this task only)

Use only when the user invoked `$orchestrate-resume`. It continues ONE interrupted task, then ends.

Follow **`docs/ORCHESTRATION.md` §9 (Resume)** together with §8 (failure and handoff rules). Read `INDEX.md` and
`AGENTS.md` first as usual. The checkpoint is under `ORCH_ROOT/.orchestration/` (doc §8). The previous lead may have
been Claude or Codex; you become the orchestrator and recompute the mode from what is available now (native
subagents, else `codex exec`; never the removed `codex mcp-server`).

Key points, none of which replace the doc: the repository is the truth and the checkpoint may be stale; stop and ask
if recovery is unclear; never assume an interrupted worker finished; do not launch a worker whose last outcome was a
usage limit, timeout or interruption without the user's yes; resuming grants no push or PR permission. Your shell is
PowerShell 5.1: no `&&`.
