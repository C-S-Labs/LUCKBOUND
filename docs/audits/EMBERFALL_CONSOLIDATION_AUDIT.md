# Emberfall production consolidation — Stage 1 audit and execution plan

2026-10-08. **Documentation only. Stage 2 has not started. Owner review required.**

## 1. Conclusion and authority

The accepted work can be consolidated without rebuilding geometry or uploading assets.
Recommend a new isolated `integration/emberfall-production` worktree based on a refreshed,
pinned `origin/main`, with **file-level Emberfall integration from `079882b`**, plus deliberate
reconciliation of the owner checkout's uncommitted grassland design and frozen-contract
documents. Do not merge every candidate branch or start directly from the complete Area II
tree: it inherits unrelated Verdant Valley enemy work missing from main.

All listed committed Emberfall candidates are ancestors of the Area II planning checkpoint.
Their contributions already coexist there. This does **not** mean that checkpoint contains
the owner checkout's uncommitted foundation work or that its old design prose is current.
The four approved proof .blend hashes and four authority-document hashes still match Batch 1's
recorded baselines. The current Area II source matches its approved planning hash exactly.

**Conditional GO for preservation/consolidation after Stage 2 authorization**, subject to
the entry gates in §8. No missing accepted .blend, broken linked library, or unresolved Git
ancestry fork was found. Remaining ownership/document conflicts can be resolved without
changing design. This is not approval for Area II production, normal runtime registration,
an arbitrary-seed appearance system, or publication. Those remain separate work.

Current owner authority, overriding historical reports:

- Area I is Burned Plains; Area II is the settlement inside the outer wall.
- Inner-wall transition selects one castle. B is the damaged/burning architectural baseline
  with enclosed final encounter and reward chamber; A is its catastrophic-impact counterpart
  with a broad shallow arena. Each entire castle is one oversized logical finale chunk.
- Approximately 20 minutes means the overall session including traversal, combat, exploration,
  loot and finale. Timer behavior is unresolved; do not alter runtime timers here.
- Area II plan `079882b` is approved as a planning baseline, not implementation authorization.
- No chunk extraction from the continuous town; no castle redesign, source movement,
  re-export/re-upload, asset replacement, Studio/place modification, main merge, push or PR.

The provisional [production handoff](../../assets/source/worlds/emberfall/PRODUCTION_HANDOFF.md)
is a navigation/authority registry for the existing fragmented state. Its title does not
claim that a consolidated branch or master Blender assembly already exists.

## 2. Evidence and audit limits

Read INDEX/AGENTS, latest WORKLOG entries, STATUS and relevant indexed design/toolchain/
authoring/production sections. One bounded read-only worker audited mappings and document
precedence; the lead reviewed the underlying files, ancestry, worktree snapshots and source
hashes. No worker wrote files or performed Git lifecycle operations.

Machine evidence beside this report:

| Evidence | Contents |
|---|---|
| [Git snapshot](EMBERFALL_GIT_SNAPSHOT.json) | Full HEADs/parents, ancestor tests, branch deltas, exact commit history, every existing worktree's dirty paths and SHA256s, stashes, main-to-plan diff |
| [Integration file groups](EMBERFALL_INTEGRATION_FILE_GROUPS.json) | Exact candidate path allowlist from pinned `079882b`, shared docs requiring reconciliation, explicitly excluded unrelated paths |
| [Dirty comparison](EMBERFALL_DIRTY_COMPARISON.json) | Byte comparison of relevant uncommitted files with the planning tree |
| [Blend inventory](EMBERFALL_BLEND_INVENTORY.json) | 55 .blend and 40 .blend1 files, absolute paths, sizes, SHA256s and modification times |
| [Blend readback](EMBERFALL_BLEND_READBACK.json) | Ten current source/review files: scenes, collections, layers, counts, mesh/transform signatures, libraries and image dependencies |
| [External ledger](EMBERFALL_EXTERNAL_LEDGER.json) | 177 external JSON/Python/FBX/place files: exact paths, bytes and SHA256; includes 25 FBX and 12 saved place files |
| [Approved hash checks](EMBERFALL_APPROVED_HASH_CHECKS.json) | Four historical approved proof hashes and four Batch 1 authority-document hashes: all match |

Git refs are local observations; no fetch, push, merge or remote-CI claim was made.
Only `origin/main` was present among relevant remote-tracking refs. Refresh and re-audit if
Stage 2 observes newer remote/local work. Snapshot includes unrelated guardian dirty paths
solely to protect them; they are excluded from Emberfall integration.

Blender inventory covers the index/document-named `E:/BlenderAIProjects/Runtime/Emberfall_*`
families and Emberfall-named Projects candidates (none found there). It is not an assertion
that unnamed files anywhere on the machine cannot exist. Every file in those families is
listed, including independent old prototype scenes and all recovery copies. Ten authoritative
or immediately derived files were opened read-only using the shared launcher; remaining
historical/recovery files were hashed, not reopened. No scene save, render or export occurred.
Restricted launch was refused by the profile guard; the same launcher succeeded with a
normal token. Readback signatures cover mesh vertices/topology/material indices and world
transforms, not a complete semantic/physics certification. Whole-file hashes protect the
remaining colors, materials, metadata, modifiers and scene settings.

## 3. Branch and worktree integration matrix

`P = 079882bbbcc389c82099f54dd6ef5fd6de2d5aeb`, the **content reference**; proposed integration
base is refreshed main, not P. Full HEADs and exact changed paths are in the Git snapshot.
“Already in P” means committed ancestry, not merged into main. Shared overlaps for every
production lane include INDEX/INDEX_MAP, STATUS/WORKLOG and biome/authoring guidance.

| Branch / HEAD | Relationship and authoritative contribution | Overlaps / conflicts | Treatment / risk / dependency |
|---|---|---|---|
| `Emberfall` / `b09a496` | Historical design checkpoint; ancestor of P | Old volcanic vocabulary; inherited non-Emberfall work | Reference/recovery; no separate merge. Medium documentation risk |
| `agent/emberfall-terrain-foundation` / `b09a496` | Same committed HEAD; dirty continuation of old Foundation scene | 11 dirty files; vocabulary/biome/modular/status changes disagree with later grassland reset | Archive/reference dirty evidence; do not promote old visuals. Medium; preserve external input |
| `agent/emberfall-burned-plains` / `b09a496` | Same HEAD; **48 dirty entries hold accepted reset, modularity/gate and frozen edge proof** | Primary reference replaced; three references and target list deleted locally; AGENTS and shared docs modified | Selective owner-file/proof integration after snapshot; no branch merge can capture it. High authority-loss risk |
| `agent/emberfall-batch1-countryside` / `2eb3e2f` | Ancestor; owned three authoring sources copied into final batch | Dirty shared API equals P; countryside differs only trailing blank lines | Reference/no content action; preserve dirty tree. Low; final Batch1 preferred |
| `agent/emberfall-batch1-elevations` / `2eb3e2f` | Ancestor; three elevation sources incorporated | Dirty API equals P; elevations equal after newline normalization | Reference/no action. Low |
| `agent/emberfall-batch1-fields` / `2eb3e2f` | Ancestor; three field sources incorporated | Dirty API equals P; fields differ only trailing blank line | Reference/no action. Low |
| `agent/emberfall-batch1` / `36b719c` | Nine final sources, authoring API, corrected cook contract and evidence; already in P | Source scripts/report, centre-ground rebasing; older review STOP | Take final file group from P; not worker originals. Medium; owner proof inputs required |
| `agent/emberfall-batch1-walkthrough` / `73b918b` | Uploaded/mapped Layout1, accepted walkthrough, outer-only boundaries; already in P | Review adapter/mapping; original versus baked appearance IDs | Preserve exact files from P. Medium; Batch1 geometry and importYaw=180 |
| `agent/emberfall-scenery-scaling` / `3e15bc4` | 61 baked clump/tree/ground parts, canopy recovery and scenery seam correction; already in P | Shared walkthrough adapter/mappings; older EditableMesh paths | Preserve P representation/evidence. Medium; layout-specific, not arbitrary-route implementation |
| `agent/emberfall-scale-profiler` / `3e15bc4` | Alias of scenery checkpoint; profiler dirty output | One untracked BenchmarkClient predecessor differs from final `a0f0817` profiler | Reference only; final profiler has server-only-property fixes and added measurements. Low |
| `agent/emberfall-scale-test` / `a0f0817` | Desktop scale fixture and effective diagnostic IDs; already in P | Separate overlay/fixtures; quarantined IDs and non-equivalent collision package | Preserve explicitly NON-PRODUCTION. Medium interpretation risk; no normal registration |
| `agent/emberfall-batch2-plan` / `eacdb24` | Accepted eight-source gap/repeat plan; already in P | Historical sufficiency estimates and before-boss timing | Copy plan as historical role authority; reconcile active timing. Low |
| `agent/emberfall-batch2-production` / `313e259` | Eight sources/four dressings, recovered uploads, final bounds/cell packing, imported 24-placement proof; already in P | Source/review mappings, outdated HOLD paragraphs, fixed-layout adapter | Preserve complete final group from P including recovery. High mapping/packaging risk; Batch1/scenery dependencies |
| `agent/emberfall-area2-blockout` / `54668c5` | Continuous town, B/A blockouts, final actual-B correspondence; parent of P | Reports from successive castle iterations; legacy approval/timing statements | Preserve final source/reference/scripts plus dated evidence. Medium; no replay of historical builders |
| `agent/emberfall-area2-plan` / `079882b` | Approved modular-production planning checkpoint; inherits all committed lanes | Shared docs addenda atop old design; no implementation authorization | Primary donor for file-level integration. High scope risk if whole-branch merged |
| `main`, `origin/main` / `aa22e3d` | Stable shared runtime/CI base; ancestor of P via `5f01c09` merge | Missing current Emberfall files and non-main VV art inherited by P | New integration worktree starts here after refresh. No main modification |
| `agent/emberfall-consolidation-audit` / base `aa22e3d` | This Stage1 documentation branch | Audit/index/handoff documents only | Select audit docs into Stage2; never merge it indiscriminately over reconciled handoffs |

Discovered unrelated `agent/guardian-surface-review` / `1cf2c7f` is dirty (9 entries), as
are its related historical references in the shared clone. No authority for Emberfall;
protect and leave alone. Other non-Emberfall branches are not a proposed integration input.
No stashes existed at audit time.

Actual committed production spine, earliest first:

`b09a496 → 2eb3e2f → 4ef2a3e → 1208226 → 36b719c → 206e8b3 → d462dcd → 73b918b →
3e15bc4 → a0f0817 → eacdb24 → 2af9994 → 4bdc59d → 67c806d → 2e39396 → 313e259 →
b1a85cc → caa7ca3 → ec0840a → 80a893b → 004a567 → d210b23 → ed0f230 → 7682ae8 →
54668c5 → 079882b`.

No cross-lane Git merges are needed: worker content was copied into Batch1, then ordinary
descendants accumulated production work. A conventional merge of P would also bring the
non-main `c95c3bf/1cf2c7f` ancestry through `5f01c09`. The main-to-P diff has **312 paths**:
138 Emberfall source/evidence, 29 opt-in fixtures/project files, 16 shared/design documents,
and **129 excluded unrelated paths**, mostly VV enemy source/export art and owning docs.
These exact classifications are in the integration file groups. Whole shared document
replacement is unsafe: ART_DIRECTION adds 1,261 lines, MODULAR_MAPS changes 747/582 lines,
and ENEMY_FRAMEWORK includes unrelated changes. Use reviewed Emberfall hunks only.

## 4. Blender source ownership inventory

All paths below use `E:/BlenderAIProjects/Runtime/` as root. Full SHA256s for every source
and recovery file are in the inventory; prefixes here are identification aids.

| File / hash prefix | Role and recommended authority |
|---|---|
| `Emberfall_Batch1/BurnedPlainsBatch1.blend` / `3e17a4ff40d7` | **Frozen integrated Batch1 authority**: nine named source scenes plus Layout1/2/3 and empty Scene. Source scenes/EF collections and COLLISION_EF collections are the accepted export/readback basis. Layout copies are derived presentation, not independently editable production sources |
| `Emberfall_Batch1/countryside/BurnedPlains_countryside.blend` / `d0f2d0ada986` | Three original authoring scene inputs: Windward Meadow, Drainage Crossing, Orchard Bend. Retain for generator provenance; do not give them a competing live-edit role against the integrated frozen file |
| `Emberfall_Batch1/elevations/BurnedPlains_elevations.blend` / `ec2b6a8aa028` | Ridge Ascent, Switchback Bank, Waymark Terrace authoring inputs; integrated sources include rebasing/name differences |
| `Emberfall_Batch1/fields/BurnedPlains_fields.blend` / `eec8f8f34a67` | Open Field Clearing, Burn Front Verge, Fenceline Rise inputs; final accepted cooking and aggregate metadata take precedence |
| `Emberfall_Batch2/BurnedPlainsBatch2.blend` / `03d0ce447931` | **Eight new source authority** plus four explicitly named DRESSING_B scene alternatives and empty Scene. Twelve scenes do not mean twelve new terrain identities |
| `Emberfall_Batch2/BurnedPlainsBatch2_GateA.blend` / `afe1f8278ee1` | First-three approved technical gate; intermediate/recovery, not final full library |
| `Emberfall_Batch2/BurnedPlainsBatch2_Review.blend` / `8d79772b5990` | Derived early Batch2 review, not authoring source |
| `Emberfall_Batch2/BurnedPlainsCombinedReview.blend` / `6e808961b611` | Derived combined 17-source review and repeated layouts; source/layout duplicates must not become editable authority |
| `Emberfall_Batch2/BurnedPlainsProductionReview.blend` / `9ea4f7fc3847` | Final imported-review/export packaging reference (11,830 objects), preserved bounds/cell recovery and appearance evidence; not a future world layout specification |
| `Emberfall_SceneryScaling/SceneryScaling.blend` / `906f220fdb69` | **Accepted scenery representation reference**: copied Batch1 sources and layouts plus generated scenery. Use only scenery collections as scenery authority; frozen Batch1 source geometry remains owned by Batch1 |
| `Emberfall_AreaII/EmberfallAreaII.blend` / `b2b3e160efb6` | **Sole continuous settlement + shared-wall/grounds + Castle B/A editable blockout authority**; one scene, two variant view layers; 3,427 objects including retained alternatives |
| `Emberfall_BurnedPlainsReview/BurnedPlains.blend` / `2138cbed63a7` | Approved grassland visual/material foundation; shared BP_* material/helper inputs. Three compatible flora sources are library reference, not a separate final chunk kit |
| `Emberfall_EdgeProfileReview/BurnedPlainsEdgeProfiles.blend` / `4833aeee7bdc` | Accepted frozen geometry/collision contract proof; not a substitute for nine+eight authored sources |
| `Emberfall_ModularityReview/BurnedPlainsModularity.blend` / `474626aa3e34` | Approved earlier composition proof; historical collar approach is superseded by frozen authored profiles |
| `Emberfall_ProductionGateReview/BurnedPlainsProductionGate.blend` / `3d028de6b676` | Historical failed rising-turn/decomposition gate and backend evidence; blocker closed by edge-profile/Batched cook corrections |
| `Emberfall_FoundationReview/EmberfallFoundation.blend` / `9a1eb3899486` | Superseded volcanic/foundation experiment, including dirty terrain-foundation work. Recovery/reference only |
| `Emberfall_ArchitectureReview/*`, `Emberfall_Prototype/*` | 32 and 12 blend/blend1 files respectively: early independent sources/layouts and identity/geology/continuity studies; historical evidence, not AreaI visual authority |
| `*/Input_*.blend`, AreaII `Before*/` and `OwnerReview_Input/`, every `.blend1` | Recovery only. File recency is not approval; AreaII blend1 is an old hash repeated through recovery archives |

Batch2 canonical new identities: QUIET_HOLLOW_BEND, RAISED_PASTURE_BEND,
LOW_SHOULDER_CLIMB, SWALE_DRIFT, PASTURE_SADDLE, LONG_DITCH_VERGE, LEEWARD_GROVE,
ABANDONED_FIELDSTEAD (all `EF_`). Combined authority is nine Batch1 + eight Batch2 =17.

The ten opened files have **zero Blender library links**. Images are generated viewer
buffers or absent; no external texture dependency was observed in them. Sources depend
instead on external Python snapshots, materials loaded from the approved foundation,
and scene append/copy workflows. Existing collection signatures differ between some
lane originals and aggregate sources (names/rebasing are included in the audit signature);
do not infer a geometry failure or choose lane files by timestamp. Use accepted aggregate
sources, original manifests, and source geometry hashes for the future normalized check.

AreaII active ownership is explicit:

- `AREA_II_SHARED`: 810 objects (terrain, outer wall, settlement/street/civic/fire/vegetation
  children); `INNER_WALL_SHARED`:67; `CASTLE_GROUNDS_SHARED`:10.
- `CASTLE_EXTERIOR_SHARED`:183; `CASTLE_B_STRONGHOLD`:490;
  `CASTLE_A_CATASTROPHE`:235, including `A_SHALLOW_ARENA`:3.
- Layers `VARIANT_A_CATASTROPHE` and `VARIANT_B_STRONGHOLD` exclude the opposite castle.
- INITIAL_PROXY_RETAINED, PRE_*_RETAINED and FINAL_CORRECTIONS_RETAINED are hidden recovery.
  Route guides and review cameras/lights are reference metadata, not export geometry.

Approved actual-B correspondence evidence at `54668c5`: 139 solid subsets, one roof surface
subset, 183 exact shared objects and 79 displaced fragments associated with actual B sources;
651 B/shared and 887 town/transition/grounds signatures protected. A source-name tag alone
is insufficient. Never re-derive A from an older B generator or promote hidden alternatives.

## 5. Proposed master Blender workspace

Keep accepted source/FBX/runtime paths stable for this consolidation. Create only the
**new master assembly and its source registry** in an explicitly documented external workspace,
provisionally `E:/BlenderAIProjects/Projects/Emberfall/`. This path does not exist as a result
of Stage1. Git holds the registry/handoff/assembly recipe; large .blend/FBX/place binaries
stay external with SHA256 and backup inventory. Do not introduce an LFS migration here.

Proposed master `EmberfallMaster.blend` is a **read-only linked review assembly**. Link
named collections from the two frozen source files, selected scenery reference and AreaII
blockout. Use collection instances for review placements, no local geometry overrides or
append-and-edit copies. Record each link's absolute path, source hash, collection/scene,
role, local-to-master transform and exclusion policy. Reject missing/mismatched inputs.
Relative paths may be used only once stable source/master relationships are documented.

Suggested scenes (labels are proposed, not new game content):

1. Library catalogue: 17 source identities plus dressings, sources at authored scale;
   collision/socket/guide display toggles; no reauthoring from this scene.
2. Accepted AreaI review: existing Layout1 composition and accepted scenery snapshot,
   separately from the 24-placement Batch2 review. Do not label the repeated stress layout
   as the approved final world.
3. AreaII+B and AreaII+A: same shared settlement/wall/exterior collections, one selected
   variant; preserve source exclusion flags so no recovery geometry leaks in.
4. Whole-world B/A review: common master coordinates and linked area instances. Any new
   AreaI-to-town placement is a **provisional review transform**, measured from guides and
   reviewed by owner; it is not an approved final seam, route recipe or production layout.

Owner-approved geometry stays editable only in its designated source; edit source, save,
refresh source registry hash and reload master links deliberately. A hash change must be
reviewed; do not have sessions silently accept whatever newest file exists. Keep prior
hashes/checkpoints as recovery history. Scenery source tables/recipe are owned by
`batch1_shared.py`, accepted scenery generator and Batch2 scenery application; foundation
materials and input helpers remain named dependencies. Do not extract a second independently
editable shared-asset library during consolidation. Future library extraction requires
its own hash-preservation/synchronization gate and owner-approved scope.

One continuous AreaII file retains settlement, wall architecture and both castles. Logical
finale unity does not imply one physical mesh. No blockout cutting, city grid snapping,
castle room randomization, destroyed-variant redesign or new full-world route decision.

## 6. Assets, exports, mappings and relocation risks

| Ledger / evidence at P | Meaning / preservation target |
|---|---|
| `tools/studio/emberfall_walkthrough/asset_mapping.json` | 673 entries:627 collision,9 terrain,18 grass,8 props,2 road,7 original scenery,fire+smoke; retain active/neutral IDs, roles, center/size/fidelity/export provenance |
| `tools/studio/emberfall_walkthrough/scenery_asset_mapping.json` | 61 Layout1BakedScenery records:27 grass,28 ground/underlap,6 tree batches; zero EditableMesh allocation; fixed-layout appearance |
| `batch2/source_export_manifest.json` | Three source FBXs,602 assets=44 visual+558 collision; eight canonical sources and four dressings |
| `batch2/asset_mapping.json` | 602 source IDs,323 review provenance IDs,17 delivered Models; reviewOnly=true; no pending review files. Active fixed review selects299 parts/1,634,590 visual triangles |
| `batch2/review_export_manifest.json`, `review_bounds_manifest.json`, `review_cell_manifest.json` | Keep original oversized/failed entries and final replacements together;23 oversized objects became104, one failed cell became two; triangles retained |
| `batch2/DELIVERY_STUDIO_REVIEW.md`, delivery/studio validation JSON | Final recovered PASS supersedes earlier upload HOLD; automated24-placement imported walk and fresh preload. Historical report status READY FOR OWNER REVIEW is preserved separately from current owner acceptance context |
| `tools/studio/emberfall_scale_test/unique_asset_mapping.json` | Diagnostic59 effective new IDs+2 accepted-tree fallbacks; unavailable tree IDs125951556096146/94233156691610 are quarantined; never promote raw mapping |

Batch2 source Model IDs: visual0 `88065938858510`, visual1 `88157428738073`, collision0
`108592230513646`. Example Batch1 terrain `EF_ENTRY_WINDWARD_MEADOW_TERRAIN`: active
Layout1 ID `71262629707248`, neutral provenance `136407962119094`. Preserve both.
Recovery review8–10 Models `77627139767340`, `84606504499635`, `101975381652352`;
bounds repair `75950126993814`, `117153955200676`; cell partition `72653471665682`.
Failed original cell `129911637407003` stays inactive provenance; replacements
`118200763683119` / `70949029507308` stay selected. The complete mapping is authoritative,
not this abbreviated ID list.

Exact Hull/Precise source collision/templates and mesh-local **importYaw=180** must survive.
Do not compensate by changing chunk sockets/yaw or center offsets. Parked Batch1
`EF_BATCH1_COLLISION` has Default fidelity despite matching627 IDs; it is not equivalent
to reviewed cooking. Preserve its file/IDs as diagnostic recovery, do not activate it.

Current normal `AssetManifest.luau` has no Emberfall EF mapping; normal project excludes all
three opt-in fixtures. `Content/Worlds/Emberfall.luau` is legacy metadata, including720s;
there is no normally registered production Chunks/Emberfall kit. Successful fixtures use
production AssetPreparation/ChunkLoader, proving the bounded loader path, not normal
expedition generation. Consolidation must not invent that missing implementation.

Relocation would break or misdirect:

- Batch1 API OUT and approved BASE .blend paths; `inputs/edge_profile_contract.py` and
  `inputs/build_burned_plains.py`; external helper copies used by walkthrough/scenery.
- `batch1/assemble_batch1.py` ROOT points to historical `C:/Users/jhpel/branch/emberfall-batch1`
  for actual ChunkCore probes. Merely copying it would still read that old worktree.
- Batch2 sibling batch1 imports, repository `parents[...]` depth, fixed Runtime paths,
  hardcoded `.rokit/bin/luau.exe`, exporters and scenery/review recipes.
- JSON sourceExport/export paths and model/mesh-local offsets; absolute paths are also
  provenance and must not be globally search-replaced.
- Rojo overlay paths/serve commands and saved review place evidence.

Therefore preserve accepted paths, import original manifests byte-for-byte, and write new
execution-root instructions. Stage2 may reconcile an identified hardcoded repository-root
resolver in the existing script, only if required for the consolidated workflow; separate
that change, preserve outputs and run a cheap read-only root/path probe. It must not run a
builder or exporter merely to test root discovery. External helper copies need explicit
hash/sync records; do not overwrite snapshots or silently designate a stale copy current.

## 7. Documentation reconciliation

Historical reports stay dated evidence. Active requirements come from the reconciled owning
documents plus one production handoff. Reconcile text, not geometry. Do not rename/delete
old reports merely because they contain superseded requirements.

| Conflict | Stage2 resolution |
|---|---|
| Owner INDEX/STATUS/WORKLOG stop at proof/no later areas | Add consolidated17-source + settlement/castle state, preserving outside-normal-runtime distinction; do not wholesale copy old STATUS |
| P EMBERFALL older Outer Wasteland/volcanic/variable-middle body versus dirty approved grassland reset | Use owner approved design as base; integrate current AreaII/castle plan addenda. Explicitly mark older studies historical rather than reviving them |
| P/AreaII reports say20min pre-boss; plan addendum says total | Overall session including finale is current authority; actual timer remains open. Record720s runtime discrepancy without changing it |
| BATCH1_REVIEW/authoring says owner checkout always latest / pending review | Dated authority manifest still valid; active handoff points to consolidated owning docs and `73b918b` accepted review |
| BATCH2_REVIEW early HOLD / absent final adapter | DELIVERY_STUDIO_REVIEW + final mapping/delivery checks supersede these sections operationally; retain failure history |
| Castle STRUCTURAL_ACCEPTANCE/CONSISTENCY STOP for approval | Owner now approves structural blockouts; production detailing/collision/combat certification remains pending |
| Earlier AreaIV/source-region language, separate small boss arena | No extra playable zone inferred after selected whole-castle finale; current finale exception governs |
| MODULAR_MAPS early128×128/128×192 city proposals and global footprint assumptions | Approved AreaII plan governs candidate boundaries; ordinary256 is proposed, exact cuts unresolved; castle oversized exception explicit |
| MODULAR_MAPS/CHUNK_AUTHORING old40–46 collision attempts or repair collars | Accepted source-authored40-stud edge transition;69–70 cooked terrain colliders; no curved-interval merges or runtime repairs |
| AreaII plan heading “for review” versus owner approval of079882b | Add approved-planning status; proposed budgets/cuts/contracts are still unimplemented; don't rewrite measurements into guarantees |
| MASTER_DESIGN/DEVELOPMENT_PLAN legacy inventory | Add narrow Emberfall status pointer only; do not rewrite unrelated combat roadmap or global historical counts |
| AGENTS local changes | Compare owner edits against current main rules; preserve current Blender launcher/upload/security/testing policy. No automatic global AGENTS replacement |
| INDEX_MAP stale/incomplete authority in old trees | Regenerate in consolidated tree after explicit staging; never hand-merge generated map |
| WORKLOG duplicated numbers across divergent histories | Keep every applicable entry once, branch-qualified during reconciliation; integration agent renumbers per GIT_WORKFLOW; do not import all unrelated VV history |
| Archived reference02/03 and prototype target vs current sole grassland reference01 | Keep historical bytes/checkpoints until cleanup gates; clearly deactivate obsolete references. Owner deletion request is not inferred from dirty D flags |

The new handoff should name source roles/hashes, commit pins, active ownership, known
runtime boundary, source/export/mapping paths, proof evidence, retention, open decisions,
execution-root instructions and next task. It replaces navigation fragmentation, not the
specialist authoring/production plan contracts.

## 8. Exact Stage2 sequence — proposed, not executed

1. **Authorization and entry snapshot.** Owner reviews this plan and authorizes Stage2
   consolidation only. Refresh origin/main, pin full SHA and recheck all donor HEADs/dirty
   statuses/hashes. If changed, revise the allowlist and authority matrix before writing.
   Make a new isolated worktree at the existing external Worktrees root for
   `integration/emberfall-production`; never switch/stash/reset the owner checkout.
   Record donor refs and external backup locations. No branch deletion.
2. **Preservation checkpoint.** Keep a read-only backup of all48 owner dirty entries,
   11 terrain-foundation entries, six worker-file entries, profiler predecessor and all
   external accepted/recovery sources/exports/evidence. Preserve deletions as status
   records, not deletion commands. Verify backup hashes. Existing worktrees remain intact.
3. **Foundation contract reconciliation.** Copy the34 untracked owner proof/report/script
   files enumerated in Git snapshot at their exact current hashes; retain active grassland
   reference01. Reconcile approved owner biome and edge/socket/collision documentation
   with current main rules and P's later addenda. Do not copy dirty AGENTS, STATUS, WORKLOG,
   INDEX_MAP or delete references wholesale. Preserve superseded Foundation work as
   recorded historical paths/hashes without promoting its visuals. Gate: four proof and
   four authority hashes match snapshot; approved design intact.
4. **AreaI source integration.** Apply P's `assets/source/worlds/emberfall/batch1/` and
   `batch2/` files from the exact file group allowlist. Include authoring/report/manifests,
   delivery/cell/bounds recovery, not just new Python sources. Root-level historical
   Emberfall scripts/reports in the138-path group are retained evidence; do not run them.
   No lane merge/cherry-pick. Gate: nine+eight canonical sources, four dressings, source
   JSON/socket/collider counts and external source hashes preserved.
5. **Review fixture/mapping integration.** Apply P's29 fixture/project paths: walkthrough,
   scale_test, batch2 adapters/mappings and three opt-in Rojo projects. Mark diagnostic
   fixture/IDs clearly; preserve final mapping selection. No default.project/src change.
   Gate: all ID-role/offset/fidelity rows and FBX hashes unchanged, normal Rojo excludes
   fixtures, zero quarantined IDs selected, no recovery cell reactivated.
6. **AreaII source-reference and plan integration.** Apply P's `area2/` group and exact
   `docs/biomes/EMBERFALL_AREA_II_PRODUCTION_PLAN.md`; retain accepted external .blend path.
   Reconcile only its approval-status wording and current owning-doc addenda. Gate:
   AreaII SHA `b2b3e160efb6d30db4831448ebf540f2c13ae79d25b09d5e37c2fbc5a5e9e49d`,
   protected signatures/layers/hidden alternatives unchanged. No scene separation.
7. **Master registry/linked review workspace.** Establish §5 using source collections and
   read-only links; no extraction into competing editable source files. Any global assembly
   transform is recorded provisional and reviewed. Gate: source hashes unchanged after
   master creation/reopen, links resolve, variants exclusive, hidden recovery absent;
   master's library instances retain source-local transforms/units and metadata.
8. **Single handoff and owning-doc reconciliation.** Promote the provisional handoff with
   actual new integration root/HEAD, current source registry and validation results.
   Apply §7 to shared docs through reviewed hunks. Carry forward relevant WORKLOG entries
   with branch attribution, add consolidation entry, update STATUS/INDEX and regenerate
   INDEX_MAP. Gate: no competing active design statements or missing source links.
9. **Final validation and owner handoff.** Run §9 required checks. Checkpoint each stage
   locally with explicit paths and external registry hashes. Give owner report, source
  /master views and remaining HOLDs. Stop before main merge, push, PR, upload/publication
   or AreaII modular-production proof unless separately authorized.

File-level restoration from a pinned commit is preferred to cherry-picking mixed commits
because it includes later bounds/recovery fixes and avoids hauling unrelated ancestry.
An ordinary merge is appropriate only if owner expressly approves the collateral ancestry
after reviewing the129 excluded paths, or a verified future main already contains it.
Selective commits are suitable only for a self-contained later change whose whole diff
matches scope. Neither condition holds automatically for this audit. Do not use an “ours”
merge or fabricated merge parent to imply excluded work was integrated.

## 9. Validation and rollback gates

| Gate | Automatic check after consolidation | Owner/manual check / escalation |
|---|---|---|
| Source preservation | SHA256 every accepted/recovery .blend and FBX against inventory; source-local counts, vertex/topology/transform/color/metadata signatures. Compare source objects, not aggregate presentation counts or datablock names alone | Stop on unexplained mismatch; don't “fix” accepted geometry to fit expected hash |
| AreaI contracts |17 canonical IDs,9+8 provenance,4 dressing aliases;256 footprints,24 mouths,HOLLOW/CREST corners,40 authored transition, frozen sockets/offsets;627+558 terrain colliders,69–70/source; existing closed/fidelity/readback results | Reuse accepted cook/ray/walk evidence if assets/transforms/template behavior unchanged; no exhaustive sweep |
| Delivery/mapping |602 source/323 review provenance mappings,299 active parts; all IDs/center/size/importYaw/fidelity and source-hash associations; final bounds≤2048, failed cell inactive; no fallback-floor selection | New imported/cooked mapping difference requires targeted cook/seam check, not mass upload |
| B/A and continuous town |AreaII whole-file hash, layer exclusion, collections and existing651/887 signature sets,183 shared objects,139+1 fixed survivors,79 displaced counterpart links; full castle bounds retained | Owner inspects master B/A visibility/placement only; structural acceptance retained, no new combat certification claimed |
| Paths/export recipes |Parse Python/JSON; resolve exact read-only input paths and external helper hashes; no missing source/library/material input. Compare existing export hashes; do not execute generators/exporters | Path-only resolver change must pass cheap probe; unexpected source selection is HOLD |
| Rojo/runtime boundary |Build normal and three opt-in projects to disposable external outputs; verify default doesn't include adapters, AssetManifest/Worlds/ChunkCore/ChunkLoader unchanged unless separately authorized | No existing Studio place opened/changed during consolidation checks |
| Repository/docs |Required syntax/unit checks (`tests/run.sh`, Luau CLI or CI limitation documented), StyLua check/Selene on integrated Luau; git diff --check; JSON parse; documentation paths, INDEX generator and --check; no forbidden names | Later main integration requires green CI on exact head; Stage2 local-only cannot claim remote CI |
| Protection/recovery |Recheck all historical worktree HEADs/status/protected hashes; audit main unchanged; backups/registry readable | Existing owner edit causes pause/re-snapshot, never destructive restore |

Only run a targeted Studio integration check if changed root/adapter serialization, selected
asset IDs, import transforms, collision fidelity/template packaging, or source geometry
invalidates prior evidence. Use a new isolated test place/session and explicit owner
authorization for that step. Existing unchanged accepted walkthrough and162-ray/24-visit
Batch2 evidence need not be repeated. No expensive whole-map walks, upload batches or
multi-rotation collision matrices as a consolidation default. A new master whole-world
placement requires owner visual review, not proof that the unimplemented full expedition works.

Rollback: each Stage2 commit is a scope checkpoint; registry records external hashes before
any new master save. If a gate fails, leave the isolated integration worktree at its last
passing checkpoint, diagnose there, and discard/recreate only a disposable new master if
needed. Use forward corrective/revert commits instead of resetting shared donor branches.
Existing donor worktrees/files/assets/IDs remain the recovery baseline. Never restore an
owner source from a dated generator. Keep backup copies and donor refs until owner accepts
the integrated baseline and applicable CI/targeted Studio checks are complete.

## 10. Remaining decisions, risks and effort

Consolidation entry requirements: explicit Stage2 authorization; refreshed donor/main
snapshot; preservation backup; agreement with the scoped-from-main strategy and source
ownership above. These are review gates, not a request to redesign any accepted content.

Choices that remain open but need not block file/document preservation:

- Exact final AreaI recipe and master whole-world placement; master review transforms are
  provisional until reviewed. Repeat stress fixtures do not decide gameplay layout.
- AreaII candidate bounds/socket profiles/common wall interface, small proof scope and
  owner decisions in plan §10. Plan approval does not freeze every proposed cut/budget.
- A reward provision, timer/deadline behavior, target devices/published-place readiness.
- Arbitrary-route assembled appearance, exact collision asset/template packaging and
  generic sequencing/loop/repetition mechanisms. No system work is authorized here.
- External source backup location/ownership over time; preserve paths now, migration later.

Highest risks: overwriting dirty grassland design with committed volcanic prose; importing
unrelated VV ancestry; selecting wrong active/recovery IDs; replaying generators over
manual blockouts; duplicate editable sources; stale hardcoded worktree/helper paths;
mistaking desktop proxy profiling or review-loader success for production certification.

Estimated **moderate-to-high reconciliation complexity**, low geometry implementation
complexity because geometry stays unchanged. Allow roughly2–4 focused work sessions:
one for snapshots/contracts and scoped files; one for mappings/path/doc reconciliation;
one for master links and preservation checks; optional fourth for conflict resolution and
owner review corrections. This is an effort estimate, not a promised elapsed time; no
expensive renders/re-exports/uploads are included. Scope can grow only by owner direction.

## 11. Stage1 result and retention

Stage1 changed only audit evidence/report, provisional handoff, INDEX/INDEX_MAP and branch
STATUS/WORKLOG. Its isolated branch starts at main `aa22e3d`; none of the proposed content
integration was executed. No source moves, geometry saves, mapping edits, merges, uploads,
Studio calls, branch deletion, push or PR occurred. Local checkpoint/worktree status is
reported with the owner handoff rather than embedded as a self-referential commit hash.

No production iteration was replaced by this change. Keep all old prototype/foundation,
failed collision/collar/decomposition reports, Batch1 lane files/blend1, scale fixtures,
quarantined mappings, Batch2 upload/bounds/cell provenance, AreaII Before*/hidden recovery
and owner-deleted reference history. After owner accepts the consolidated baseline and
required CI/targeted Studio gates pass, consider archiving obsolete review/workspace
iterations from active navigation. Never delete referenced files or kept recovery copies.
**Stop here for owner review.**
