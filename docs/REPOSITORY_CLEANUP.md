# Local repository/filesystem cleanup - 2026-10-02

Owner authorized auditing C:/Dev, cleaning redundant checkouts/files, and separating
pending work into C:/Dev/branch. No implementation, asset, enemy, portal or Blender
content changes were made by this cleanup.

## Findings and size

The initial inventory covered 25,269 files, 14 registered worktrees and 6,409,652,896
logical file bytes across C:/Dev (not allocated NTFS size). C:/Dev/luckbound contained
5,229MB, primarily nested duplicate worktrees. Main's tracked binary assets had zero
byte-identical duplicate groups. Git's approximately842MB of retained history is
not disposable; no history, branch refs, reflogs or parked assets were deleted.

After cleanup and while the audit checkout/build still exist: C:/Dev is
4,254,813,782bytes, saving2,154,839,114bytes. Removing this audit checkout after the
local documentation commit reclaims approximately670MB more. Final measured totals
are recorded locally in C:/Dev/branch/recovery/audit-final.json.

## Folder layout

| Location | Purpose / action |
|---|---|
| C:/Dev/luckbound | Primary checkout now on main7c0513f; merged fast generation present |
| C:/Dev/branch/expedition-portal-followup | Original portal branch db51d12 and verified local ES edits preserved |
| C:/Dev/branch/procgen-performance | Original bb47f91 benchmark branch/evidence preserved |
| C:/Dev/branch/ui-overhaul | Unmerged UI commit retained; only phantom file/EOL modifications cleared |
| C:/Dev/branch/recovery | Inventories, preservation hashes, original snapshots and verified scratch ZIP |
| C:/Dev/luckbound/.claude/worktrees/boss-anim-vfx-plans | Exception: live Claude process47952 and open PR154; moving deferred until owner pauses it |
| C:/Dev/CCBlender | Blender MCP project/environment retained |
| C:/Dev/tools | Shared Luau and legacy scripts retained; current script use unconfirmed |

Primary checkout retains the untracked authoritative TheAscendant_fixed.blend,
owner Blender rollback files, local MCP settings and owner place file. These were
not judged disposable. Local settings are excluded from Git on the cleanup branch.

## Worktrees removed

Only clean, already-integrated trees were removed: luckbound-movement; dev-console;
enter-lock; es-final-polish; es-walk-fixes; detached leaderboard-chat; astral-reach
scheme documentation; procgen-production; ethereal-scape-polish. The owner-rejected
es-collision-pilot checkout was also removed, retaining its local Git history and
original source snapshot. Branch names/commits were not deleted.

Empty luckbound-worktrees, luckbound/.worktrees and backups containers were removed.
There were no missing registered worktrees requiring prune. Portal and benchmark
were never rebased or merged into one another; main was only fast-forwarded.

## Preservation and cleanup

- Both genuine owner ES_STRUCTURE/ES_PROP_LIBRARY edits copied to the portal tree
  with SHA256 checks; source restored only after preservation verification.
- New portal destination had no edits; its text differences from HEAD were Git
  newline conversion. Existing destination settings were required to be absent.
- 96 UI files and115 benchmark files were byte-identical phantom Git edits. One UI
  file differed only in newline encoding; restored HEAD bytes before index refresh.
- Archived69 unique retired session script/log/tool files in completed-session-scratch.zip;
  every archived file hash checked before removing loose scratch copies.
- Preserved es-collision-original-scene.blend and es-polish-owner-rollback.blend1.
- Deleted five known reproducible retired Rojo builds and10 generated Python
  bytecode files. No owner Studio place was deleted or saved.
- No broad deletion of C:/Dev/tools: automatic review rejected that part because
  current use was unproven. Scripts remain intact; no bypass attempted.

## Verification

Git connectivity check passes; registered retained worktree paths exist. Portal
and benchmark commit identities unchanged; preserved asset hashes match. Current
main Rojo7.7 build passes. No src/, default.project.json, manifest or runtime asset
changes on the cleanup branch. No Studio publication, source save, push or merge
performed by this filesystem task. Existing generation PR156 was already merged
before this task began.

## Remaining cleanup

Pause/close the active Claude session before moving its locked worktree to
C:/Dev/branch/es-ascendant-and-minibosses. Do not force-unlock or relocate it while
working. Its HEAD changed during the audit, confirming ongoing work.

Keep all production collision, parked recolours, rollback sources, benchmark raw
results and unique pending branch history. Future retirement requires reference
checks and owner/CI acceptance. Check external tool consumers before archiving old
C:/Dev/tools scripts. No broad source/export cull is justified by this audit.
