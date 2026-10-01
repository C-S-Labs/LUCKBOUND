# Verdant Valley authored path exits and asymmetric widths — 2026-09-30

This follow-up refines Session 204's terrain/collision audit with **authored path
identity and independently measured opening width**. Flat grass and successful
query hull raycasts do not establish a path exit. Earlier PASS counts must not
be read as validation of this previously unmeasured condition.

## Before corrections: independent measurements

Exact triangles and material assignments were measured in the preserved
production export input; source SHA256 and all 30 terrain digests match the
refreshed production ledger. Four edges per chunk were sampled laterally every
0.5 stud, at depths 2/6/12/24/40. Each chunk's retained production yaw maps the
export-local coordinates into the runtime compass. No scene save or export.

All six gates with asymmetric PATH/WIDE sockets were checked, as was the Boss
entrance. The numbers below come from **each individual mesh**, not a shared
assumption. Widths describe the 2-stud inset mouth: contiguous central VV_Path
surface / level pad within ±0.35 stud / total visible ground apron. Socket
contract widths are 48 PATH and 52 WIDE, including the intended edge buffer;
the colored path itself need not fill the whole socket width.

| Chunk | Runtime edge | Declared | Measured path / pad / apron | Verdict |
|---|---|---|---|---|
| Overgrown Causeway | north | WIDE 52 | 43 / 46.5 / 72 | reversed |
| Overgrown Causeway | south | PATH 48 | 50 / 52.5 / 80 | reversed |
| Windward Ridge | east | WIDE 52 | 43 / 46.5 / 72 | reversed |
| Windward Ridge | west | PATH 48 | 50 / 52.5 / 80 | reversed |
| Crystal Spring | east | WIDE 52 | 43 / 46.5 / 72 | reversed |
| Crystal Spring | west | PATH 48 | 50 / 52.5 / 80 | reversed |
| High Ledge | east | WIDE 52 | 43 / 46.5 / 72 | reversed |
| High Ledge | west | PATH 48 | 50 / 52.5 / 80 | reversed |
| Cliff Overlook | north | WIDE 52 | 43 / 46.5 / 72 | reversed |
| Cliff Overlook | south | PATH 48 | 50 / 52.5 / 80 | reversed |
| Forgotten Orchard | south | WIDE 52 | 50 / 52.5 / 80 | agrees; unchanged |
| Forgotten Orchard | west | PATH 48 | 43 / 46.5 / 72 | agrees; unchanged |
| Boss Sanctuary | north | WIDE 52 | 50 / 52.5 / 80 | agrees; unchanged |

Path material continues inward independently on both exits of every gate;
the deeper level band may narrow as terrain rises, without changing mouth
identity. Raw material intervals, heights, normals and pad widths at every
slice are in `VV_SOCKET_WIDTH_EVIDENCE.json`.

**Mushroom Glen:** north, south and west each have a 43-stud central VV_Path
mouth, a 46.5-stud level pad and a 72-stud visible apron. Its declared east
socket has **no VV_Path mouth** at 2, 6, 12, 24 or 40 studs inward: grass can
support a ray but is not the authored route. West is the omitted path exit;
existing saved west collision passes 30/30 approach samples, with no sampled
solid obstruction. North/south retain their declarations.

**Forgotten Trial:** the retained 180-degree art frame places its only
43-stud path/46.5-stud pad at the declared north edge. Its other edges have
grass patches but no centered authored path mouth. Its own contract agrees;
its appearance in a poor connection does not establish a defect in Trial.

**Woodland Refuge:** the previous south correction is retained. The exact
authored exit remains south; no art/collision/prop rotation is needed.

The complete 30-chunk material/width comparison finds **six new failing
chunks: five reversed gates plus Mushroom Glen**. Other source exit/kind sets
agree with metadata, including Refuge's prior correction. This does not close
the previously recorded suspicious collision/query cases.

## Shared cause and limits of the prior heuristic

The historical exporter measures native Blender +Y=N/+X=E and writes that
native socket table together with a blanket 180-degree art hint. Current
production imports map export-local (x,y,z) to Roblox (−x,z,+y), followed by the
chunk's calibrated art yaw. `tools/wire_vv_imports.py` installs per-chunk yaw
hints and converts prop translations/rotations, while retaining socket rows.

For these five opposite-edge gates the current art yaw is zero: physical
exits remain on the declared axis, **but their unequal widths exchange sides**.
The independently correct Orchard and Boss use yaw 180. Mushroom's zero-yaw
three-way swaps the authored lateral exit from east to west. This is a
native-authoring versus current production metadata convention mismatch, not
evidence that shared generation mathematics is wrong.

The runtime heuristic samples Width/2−8: 16 studs for PATH and 18 for WIDE.
Both fit inside the 43-stud normal path. Opposite-edge gates therefore tie
without detecting reversed identities. Mushroom's grass query hulls also let
several orientations tie despite the missing east path. No change to shared
calibration/generation is warranted by this evidence; fix the proven content
contracts while preserving the complete authored composition.

## Corrections and verification

Corrected the **five independently confirmed gate reversals** in the existing
chunk content: Causeway and Cliff Overlook now offer north PATH / south WIDE;
Windward, Crystal Spring and High Ledge now offer east PATH / west WIDE.
Names still identify their actual compass edges; Kind controls Width through
the existing 48/52 helper. Mushroom Glen's east declaration becomes west
(OffsetX −128, Facing 270, PATH 48); north/south remain. No other socket table
was changed in this follow-up, including Trial, Orchard, Boss and Refuge.

| Correction | Before contract | After contract | Exact physical evidence |
|---|---|---|---|
| Causeway | north WIDE / south PATH | north PATH / south WIDE | 43/50-stud path mouths; 46.5/52.5-stud pads |
| Windward | east WIDE / west PATH | east PATH / west WIDE | 43/50-stud path mouths; 46.5/52.5-stud pads |
| Crystal Spring | east WIDE / west PATH | east PATH / west WIDE | 43/50-stud path mouths; 46.5/52.5-stud pads |
| High Ledge | east WIDE / west PATH | east PATH / west WIDE | 43/50-stud path mouths; 46.5/52.5-stud pads |
| Cliff Overlook | north WIDE / south PATH | north PATH / south WIDE | 43/50-stud path mouths; 46.5/52.5-stud pads |
| Mushroom Glen | east PATH, no path mouth | west PATH, measured mouth | 0→43-stud path mouth; corrected west collision 30/30 |

**All 30 chunks / 59 sockets were rechecked with fresh disk metadata.** With
the added authored-path identity/width criterion, before corrections:
34 PASS / 14 SUSPICIOUS / **11 FAIL sockets across six chunks**. After:
**42 PASS / 17 SUSPICIOUS / 0 FAIL / 0 INTENTIONAL** sockets; 16 PASS and
14 SUSPICIOUS chunks. Every previously failing path/Kind condition now passes.
The gate contract fixes do not claim to repair separate ambiguous collision
samples or cooked query hulls. Crystal's west centre miss at 40 studs, High
Ledge's east terrain queries, Cliff Overlook's north query/calibration and
Mushroom's north collision sample at depth 12/lateral +8 remain flagged.
All 17 suspicious socket coordinates/reasons are in the complete follow-up
after report. Original Session 204 evidence remains unchanged as history.

Runtime calibration retains **all 30 existing hint selections**; all six
corrected chunks remain yaw zero. Exact geometry and all prop translations
stay spatially coherent. All 30 structure/template references and 823 props
resolve; role counts remain 39 solid, 784 nonsolid including 746 Sway rows.
All 4,033 current collider IDs, saved production assets, source scenes,
manifest IDs and protected Stone rollback are unchanged. **No replacement
asset IDs or owner import/upload action is required.**

Temporary pair probes covered four layout yaws and the appropriate shared
buffered width (±18 for WIDE, ±16 for PATH). Mushroom→Trial passes **220/220**;
Causeway→Boss, Crystal→Boss and Cliff Overlook→Boss each pass **220/220**.
Windward→Boss passes **217/220**, High Ledge→Boss **216/220**, and the unchanged
Orchard→Boss control **216/220**. All pair centres and approach heights pass.
The 11 ambiguous samples hit collider side normals at panel seams: Windward
distance 0/lateral +8 in three yaws (normal Y≈0.010); High Ledge distance
0/lateral −8 in four yaws (≈0.570); Orchard mostly distance −24/lateral +8
(≈0.337), with distance 0/lateral −8 at yaw 270 (≈0.569). These are manual
collision/query follow-ups, not proof of wrong path/Kind or a reason to alter
the correct control. Total: **1,529/1,540** broad pair samples pass, every
centre passes; see `VV_SOCKET_WIDTH_PAIR_PROBES.json`. All clones were destroyed.

Validation: **1,017/1,017 full integrated Luau tests** (two additional
gate/Trial connection regressions), **7/7 Blender launcher regressions**,
**7/7 collision-verifier probes**, production collision verifier, Python/Luau
syntax, StyLua 2.0.2, index/diff/handoff checks, and **full Rojo 7.7 build pass**.
The build is `E:/BlenderAIProjects/Runtime/vv_socket_width_review.rbxlx`.
The same 3,915 serialized-fidelity collider parts still require owner Studio
evidence. Remote CI remains pending; the final wrap-up authorizes a local
completion commit only, with no push or merge into main.

### Owner Studio validation — 2026-09-30

The owner manually tested approximately **eight procedural Verdant Valley
seeds** after the latest corrections. Woodland Refuge remains fixed,
Mushroom Glen connects correctly, and the corrected PATH/WIDE gate chunks
produce clean connections. No additional socket-placement or visible
connection failures were observed. This completes the requested manual
validation of the corrected socket metadata; no speculative socket or
geometry changes are warranted by this result.

The sample does not reclassify the **17 SUSPICIOUS, zero FAIL** audit results
or establish the cooked collision fidelity of every serialized part. The
3,915 serialized-fidelity parts, precise Studio-query/calibration ambiguity,
and isolated lateral/panel-seam samples remain known limitations, rather
than newly confirmed socket defects. Remote CI awaits an authorized push.
No security/API setting, source geometry, asset ID or prop transform changed.

## Exact files and preserved history

- `src/shared/Content/Chunks/VerdantValley.luau`: six socket tables only;
  `tests/cases.luau`: two contract/connection regressions.
- `assets/source/worlds/verdant_valley/audit_socket_widths.py`: reusable
  exact triangle/material width diagnostic for all 30 chunks.
- `tools/report_vv_socket_audit.py`: explicit `--width-followup` mode,
  enforcing path presence and physical Kind without rewriting old snapshots.
- `tools/probe_vv_socket_pair.luau`: general pair/Kind/socket selection and
  contract-width samples; prior Refuge/ Grove defaults retained.
- This report, `VV_SOCKET_WIDTH_EVIDENCE.json`,
  `VV_SOCKET_WIDTH_RUNTIME_AFTER.json`, `VV_SOCKET_WIDTH_PAIR_PROBES.json`,
  `VV_SOCKET_AUDIT_WIDTH_BEFORE.json/.md`,
  `VV_SOCKET_AUDIT_WIDTH_AFTER.json/.md`, and index/biome/status/worklog handoff.
- `docs/VV_SOCKET_AUDIT.md`: notice linking to this stronger follow-up.

Final wrap-up remains on `integration/vv-main-sync`. The owner authorized a
local integration completion commit after final automated checks, with no
push or merge into main. The existing two-parent integration merge at
`191ea0b` is retained; the completion commit records the remaining socket
corrections, audit evidence, formatting and handoff. All historical/staging/
recovery material and current solid/nonsolid/Sway architecture remain protected.

Cleanup: no replacement asset iteration is needed. Keep all existing
historical/staging/recovery files; no cleanup or deletion is part of this task.
