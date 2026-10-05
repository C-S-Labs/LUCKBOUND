---
name: orchestrate-resume
description: Resume an interrupted orchestration from its checkpoint (any previous lead, Claude or Codex). User-invoked only.
disable-model-invocation: true
argument-hint: [task name or note]
---

# /orchestrate-resume — Claude takes over an interrupted orchestration (this task only)

Note from the user (if any): $ARGUMENTS

Use only when the user typed `/orchestrate-resume`. It continues ONE interrupted task, then ends.

Follow **`docs/ORCHESTRATION.md` §9 (Resume)** together with §8 (failure and handoff rules). Read `INDEX.md` first
(AGENTS.md Step 0). The checkpoint is under `ORCH_ROOT/.orchestration/` (doc §8). The previous lead may have been
Claude or Codex; you become the orchestrator, and you recompute the mode from what is available now.

Key points, none of which replace the doc: the repository is the truth and the checkpoint may be stale; stop and ask
if recovery is unclear; never assume an interrupted worker finished; do not launch a worker whose last outcome was a
usage limit, timeout or interruption without the user's yes; resuming grants no push or PR permission.
