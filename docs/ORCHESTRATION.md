# LUCKBOUND — Orchestration protocol (provider-neutral)

How one **lead agent** (the *orchestrator*) drives worker agents to finish a larger task. It is opt-in, and it works the
same whether the lead is Claude or Codex. Entry points: `/orchestrate` and `/orchestrate-resume` (Claude Code,
`.claude/skills/`), `$orchestrate` and `$orchestrate-resume` (Codex, `.agents/skills/`). Both are **explicit-only**:
nothing starts orchestration because a task is large or a tool is installed.

`AGENTS.md`, `INDEX.md` and `docs/GIT_WORKFLOW.md` stay authoritative and are unchanged by this file. Orchestration
changes **who types the code**, not the project's rules. It applies to ONE task; when that task is reported, it is
over. Standalone Claude and standalone Codex sessions never read this file unless asked.

## 1. Roles

The **orchestrator** owns: reading `INDEX.md` and `AGENTS.md` first, understanding the objective, settling design,
the plan and dependency graph, worker scopes, branches and worktrees, task packets, monitoring, review, overlap
detection, integration order, final validation, the checkpoint, and the handoff to the user. It owns the whole Git
lifecycle (branch, commit, push, PR) under `GIT_WORKFLOW.md`'s implementation-agent rules.

**Workers** implement, research or test inside a task packet. They do not redefine architecture, make game-design
decisions, or touch Git beyond §6.

Never hand a worker an unresolved LUCKBOUND design decision. If the task seems to need a Phase 1 exclusion or a spec
amendment, raise it with the user (AGENTS.md hard rule 8) instead of delegating it.

## 2. Modes (pick by what is actually available)

| Mode | Lead | Workers | How workers run |
|---|---|---|---|
| A | Claude | Codex | `codex exec` child processes (§9) |
| B | Codex | Codex | Codex native subagents; else `codex exec` children. **Never** the removed `codex mcp-server` |
| C | Claude | Claude | Claude Code subagents (Agent tool), pointed at a worktree path |
| D | either | none | single agent, sequential, same task boundaries and gates |

The user may name a mode. Otherwise: lead Claude with `codex --version` working → A; lead Codex → B; Claude only →
C; nothing spawnable → D. A provider failure or usage limit **degrades** the mode (§8); it does not void the plan.

**Do not delegate wastefully.** Trivial edits, tiny fixes, questions, and work whose task packet would cost more
context than the change itself stay with the orchestrator. `/orchestrate` means delegation is available and expected
where it pays off, not that every subtask goes to a worker. If nothing is worth delegating, say so and do it
(Mode D).

## 3. Plan before spawning

1. Read in the normal order (AGENTS.md Step 0 and 1): `INDEX.md`, top `docs/WORKLOG.md` entry, `docs/STATUS.md`, then
   only the spec/design sections the task touches (`INDEX_MAP.md` gives the lines).
2. Settle design with the user first if anything material is open (`docs/MASTER_DESIGN.md`, locked decisions in
   `STATUS.md`).
3. Write a short plan and classify every task:
   **FOUNDATION** (others depend on its contract), **PARALLEL** (independent, contract stable), **DEPENDENT**,
   **INTEGRATION**, **VALIDATION**.
4. Do not spawn a worker whose contract does not exist yet. Foundation work finishes, is reviewed and is integrated
   first; only then do parallel workers start, branching from the integrated result.
5. Concurrency: default to a few independent workers. Add more only when scopes do not overlap, contracts are
   stable, worktrees are isolated and integration stays cheap. Never parallelise tightly coupled work to raise the
   worker count. Three good workers beat ten overlapping ones.
6. Large single tasks: split into bounded phases derived from the task (data declarations, system, content,
   tests). Do not split small tasks. Phases limit lost work; they are **not commits** (commit only under
   GIT_WORKFLOW.md). After a substantial phase, review enough to know it is safe to build on, update the checkpoint,
   then start the next.

## 4. Branches and worktrees

- The orchestrator works on its task branch `agent/<task>` (from `origin/main`, per GIT_WORKFLOW.md). **Never on
  `main`.** If the current checkout is not that branch (for example the owner is on another branch), do NOT switch
  it: create an integration worktree for the task branch instead.
- Parallel **writing** workers each get their own branch `agent/<task>-<part>` and their own worktree, created by the
  orchestrator: `git worktree add <ORCH_ROOT>/<slug> -b agent/<task>-<part> <start>`. `<start>` is the integrated
  task branch (or `origin/main` for the first foundation worker). Two writers never share a working tree.
- `ORCH_ROOT` = the `branch/` directory beside the main checkout (for example `C:/Dev/branch/`), outside the
  repository, so nothing there can be committed. If another location is already in use for this clone, use that.
- Read-only research/review workers need no worktree: `--sandbox read-only` on the main checkout.
- Single worker, single tree, nothing else running: a worktree is optional; use the protected-paths rule instead (§5).
- Worker branches are sub-branches of one logical task: they are merged into `agent/<task>` and ship as one PR.
- Never switch the owner's checkout. If `assets/rbxm/prefabs/HUB_SKY.rbxmx` has an owner edit, leave it alone.

## 5. Task packet (every worker gets one)

Self-contained and short. **Reference repository paths; never paste `AGENTS.md`, `INDEX.md`, spec sections or diffs**
the worker can read itself. The packet holds only what is not recoverable from the repo.

```
Objective:      what you must produce
Scope:          files/systems you may modify (and the worktree path you work in)
Forbidden:      files/systems you must not touch (incl. pre-existing changes: <paths>)
Contracts:      repo paths to read (INDEX.md first, AGENTS.md, then specific docs/sections)
Settled:        decisions the user made that are not written in the repo
Dependencies:   what already exists and where
Deliverables:   exact expected outputs
Validation:     checks to run before you finish
Git:            §6 verbatim (workers never commit)
Handoff:        report files changed, what and why, checks run with results, anything skipped or uncertain
```

Always include: "You are a worker for another agent's task. Do not make design decisions; if the spec is ambiguous or
seems to need one, stop and report the question. Touch only the files in scope. Do not edit `AGENTS.md`, `CLAUDE.md`
or unrelated files. Shared project rules stay authoritative." On a follow-up or resumed run add: "The worktree
already contains earlier work. Inspect it (`git status`, `git diff`) and continue; do not restart."

## 6. Git policy for workers

Workers may **inspect** Git (`status`, `diff`, `log`). Workers must **never**: switch or create branches, create or
manage worktrees, stash, reset, checkout/restore files, rebase, merge, push, force-push, open or edit PRs, publish a
Roblox place, or overwrite an owner-edited Blender scene. They modify the working tree and run validation only.

**Commits:** workers never commit. The orchestrator commits each worker's output itself after review
(`git -C <worktree> add <explicit paths>`, then `commit`). A probe confirmed a `workspace-write` Codex worker cannot
stage or commit in its own linked worktree anyway (`index.lock: Permission denied`), so this is also the only
arrangement that works.

Integration, pushing and PRs belong to the orchestrator and follow the existing gates: `/orchestrate` is **not**
permission to push or open a PR. For work the user should look at (meshes, weapons, enemies, UI, animation, world
generation, or anything uncertain), stop after local commit and validation and let the user review first. Never
merge into `main` (integration-agent job). No force-push, no bypassing repo validation, no destroying uncommitted
owner work.

**Do not rely on the sandbox as a Git boundary.** On this Windows setup a probe showed Codex's `workspace-write`
sandbox blocks staging and committing in a linked worktree, yet allowed `git worktree add` and writes outside its
working directory. The sandbox is inconsistent, so these rules are enforced by the packet and by review (§7), and
that review is mandatory.

## 7. Review, integration, validation

For each returned worker, the orchestrator itself (never on the worker's say-so):

1. Reads `git status` and the real diff in the worker's worktree, including untracked files, and checks it against
   the packet and the AGENTS.md hard rules.
2. Confirms no Git lifecycle change: worker's branch unchanged, no commits unless granted, `git worktree list` and
   `git stash list` as expected, the main checkout and protected paths byte-identical to the recorded state.
3. Checks for overlap with other workers: intersect the changed-file lists. **Unexpected overlap stops automatic
   integration**: reconcile deliberately; never settle an architectural conflict by picking one side.
4. Fixes small problems itself; sends larger ones back with a narrower prompt. **At most two failed
   implementation-correction rounds** per problem, then ask the user. Availability failures (§8) do not count.
5. Integrates in dependency order: merge each accepted worker branch into `agent/<task>`, then re-check.

**Validation** follows AGENTS.md ("Verify before you merge", "Before you finish", and "Rapid iteration and
testing"): cheap sanity checks to get the result ready for the owner's own test, the index and doc updates the change
requires, and no exhaustive extra suites unless the owner asked or a failure needs diagnosing. If a deeper check
would help, say what it would establish and wait. Update `WORKLOG`, `STATUS` and the index under the normal rules.
End with the leftover-cleanup recommendation.

## 8. Checkpoint and interruption recovery

The checkpoint lets any replacement orchestrator (even another provider) recover without the old conversation. It is a
small pointer, **not** a transcript, spec, diff or Codex output.

- **Location:** `<ORCH_ROOT>/.orchestration/<task>.md`: outside the repo, so it can never be committed and needs no
  exclude entry. If that cannot be written, say so; do not fall back to a path inside the repo.
- **When:** only after the user invoked orchestration and the task and branch are set. Update only at boundaries:
  **A** plan/branches/worktrees set; **B** before dispatching a worker; **C** after a worker returns or fails;
  **D** after review; **E** after validation or integration; **F** before reporting. Not while reasoning.
- **Format** (plain text; write `none` when empty; one line per worker):
  ```
  objective:    <1-3 lines or a pointer>
  orchestrator: claude | codex      mode: A | B | C | D
  repo:         <absolute path of the main checkout>
  task_branch:  agent/<task>        task_worktree: <path, or "main checkout">
  base:         <short sha of origin/main at start>
  stage:        planning | dispatching | reviewing | integrating | validating | completed
  graph:        FOUNDATION a > b; PARALLEL c, d; INTEGRATION e; VALIDATION f
  protected:    <pre-existing changed/untracked paths + git hash-object for modified ones>
  blockers:     <or none>
  next_action:  <one line>
  workers:
  - id: <slug> | branch | worktree | status | depends | commit | validation | integration | outcome | corrections | note
  updated:      <ISO time>
  ```
  `status`: PLANNED BLOCKED RUNNING REVIEW PASSED FAILED INTEGRATED CANCELLED.
  `outcome`: none success interrupted usage-limit timeout failed uncertain.
- **Completion:** at F set `stage: completed`. Keep the file while uncommitted work exists or the branch has not
  finished its normal Git lifecycle; delete it only when the work is committed and pushed/PR'd (or the user says so).
  Never delete the only record of uncommitted work. Do not store prompts, diffs or Codex responses in it.

**A worker run is unsuccessful or uncertain** if it exits non-zero, times out (including the orchestrator's own tool
timeout), mentions a usage/rate/quota limit, crashes, or leaves no clear completion report. Then:

1. Do **not** retry and do **not** probe the provider again, least of all after a usage limit.
2. Do not assume it changed nothing. Inspect `git status` and the real diff in that worker's worktree, compare
   protected paths, and sort what you see into complete, partial, untouched, uncertain.
3. Preserve valid partial work; do not revert it because the run failed.
4. If it touched a protected path or did any Git lifecycle operation, stop and say so.
5. Record `outcome`, update the checkpoint, and tell the user what is actually in the working tree.
6. Offer, and wait: try again later (resume), let the orchestrator finish the remainder itself (say how large it is;
   **never switch quietly**, that defeats saving usage), or let the user continue by hand in Codex or Claude (the
   checkpoint says what remains). A dead lead is never replaced by auto-launching another agent.

**Provider handoff** (lead out of usage, or the user switches lead): the replacement starts with the resume
procedure below. Preserved by the checkpoint: objective, plan and graph, active workers, branches, worktrees,
completed commits, validation evidence, unresolved failures, next action. Never assume an interrupted worker
completed; verify its Git state and output.

## 9. Resume (`/orchestrate-resume`, `$orchestrate-resume`)

Explicit only. Continues ONE interrupted task, then ends like a normal run.

1. Read `INDEX.md` and the normal docs (AGENTS.md Step 0 and 1), then this file.
2. Find the checkpoint: `<ORCH_ROOT>/.orchestration/`. If the user gave a task name use it; if exactly one file
   matches the current branch or only one exists, use it; otherwise list them and ask. Never guess.
3. Check the repository: `git worktree list`, then for the task branch and each worker `git status --short`,
   `git log <base>..<branch>`, `git diff`, plus `git stash list`. Verify protected paths. The checkpoint's `repo`
   must match this clone.
4. **Reconcile. The repository is the truth; the checkpoint may be stale.** Rewrite it to match. If the branch,
   worktrees, protected paths or history are inconsistent enough that safe recovery is unclear, **stop and ask**.
5. Say briefly what you are resuming, then continue from the recorded stage, not from the start. Mark yourself as the
   new `orchestrator` and recompute `mode` from what is available now.
6. A worker with `outcome` of `usage-limit`, `timeout` or `interrupted`: do not launch it to test. Ask the user
   whether the provider is available again. Launch only on their yes, with a prompt that points at the worktree and
   the remaining work, not at earlier prompts or diffs.
7. Resuming does not reset `corrections`, does not grant push or PR permission, and never lets a worker do Git.

## 10. Running workers (per mode)

Write the packet to a temp file **outside the repo** (never into it) and delete it afterwards. Update the checkpoint
before and after each run. Never pass a flag that bypasses the sandbox or approvals.

- **Mode A / B fallback, `codex exec`.** Read-only research: `codex exec --sandbox read-only --ephemeral -C <dir>
  -o <tmp>/<id>.txt - < <tmp>/<id>.prompt`. Implementation: the same with `--sandbox workspace-write` and `-C <the
  worker's worktree>`. Read the `-o` file afterwards, not the stream. Several independent workers may run at once
  (background jobs, one worktree each). Codex's Windows shell is PowerShell 5.1: no `&&`.
- **Mode B native.** Check `codex features list` shows `multi_agent` enabled. The root agent spawns one subagent per
  worker, each told its absolute worktree path and given the packet. Subagents are workers: they do not spawn
  further workers or redefine the plan.
- **Mode C.** One Claude Code subagent (Agent tool, `general-purpose`) per worker, prompt = the packet, working in
  the worktree the orchestrator created (do not use the tool's own worktree isolation: branch naming and location
  here are the orchestrator's).
- **Mode D.** The orchestrator does each task itself in order, with the same scopes, review step and gates.

## 11. Future: one worker per biome

This protocol is deliberately content-neutral. A later enemy-production task needs no change here: it is a plan
whose FOUNDATION is movement, the combat contract, enemy AI core and two gold-standard enemies, and whose PARALLEL
workers (one per biome) start only after that contract is accepted. Their packets would carry the global enemy
contract, the biome contract, enemy definitions, movement archetypes, moveset graphs, animation and VFX needs,
group-owned animation publishing requirements, performance budgets and acceptance tests, as repo paths. INTEGRATION
(manifests, animation registry, spawn, encounters) and VALIDATION follow. That workflow is not built here.
