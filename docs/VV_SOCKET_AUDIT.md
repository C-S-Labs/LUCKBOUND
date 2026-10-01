# Verdant Valley socket/opening validation and repair — 2026-09-30

**Historical Session 204 snapshot.** The later authored-path/width follow-up
in `VV_SOCKET_WIDTH_REVIEW.md` independently confirmed and corrected five
PATH/WIDE reversals and Mushroom Glen's wrong lateral exit. Its stronger
criterion and current 30-chunk report supersede these earlier PASS counts.
The original raw before/after evidence below is retained unchanged.

Work remains uncommitted on `integration/vv-main-sync`. No push, merge, rebase,
asset upload, security change, scene save or staging/recovery cleanup occurred.

## Result

The complete pre-repair audit covered **30 chunks and 59 declared sockets**.
Before: **39 PASS, 19 SUSPICIOUS, 1 FAIL, 0 INTENTIONAL/SPECIAL** sockets;
14 PASS, 15 SUSPICIOUS and 1 FAIL chunks. The identical complete post-repair
diagnostic reports **40 PASS, 19 SUSPICIOUS, 0 FAIL, 0 INTENTIONAL/SPECIAL**
sockets; 15 PASS and 15 SUSPICIOUS chunks.

The full catalogue, socket identities/kinds/offsets/widths, layout facing,
production hint, all four runtime calibration scores/centre hits, centre/inset/
lateral collision and terrain probes, cardinal alternative approaches and
solid-prop obstruction samples are in `VV_SOCKET_AUDIT_BEFORE.json` and
`VV_SOCKET_AUDIT_AFTER.json`. Their Markdown companions list all 59 verdicts
and every detected socket anomaly. The complete pre-repair report was produced
before changing production metadata; no SUSPICIOUS case was repaired.

## Conclusive repair: Woodland Refuge

**Root cause: socket metadata in the saved production import frame.** The
declared north opening had no usable authored surface or saved collision
approach. The actual composition approaches the south edge. Its preserved
export input's native +Y opening maps to Roblox south under this chunk's
retained zero art yaw. Native −Y lacks the declared approach. A 180-degree
turn would require coordinated prop translations as well as art/collision
rotation and is unnecessary for this correction.

Changed only its socket contract: identity `north` → `south`, OffsetZ
−128 → +128, Facing 0 → 180. Kind PATH, Width 48, OffsetY 0, art yaw 0,
all 18 prop transforms, all 113 colliders, ground offset, size and asset IDs
are preserved. Existing shared generation/socket mathematics is unchanged.

| Measurement | Before north | After south |
|---|---:|---:|
| Saved collision centre, depths 0/2/6/12/24/40 | 0/6 | 6/6 |
| Saved collision grid, six depths × five lateral samples | 6/30 | 30/30 |
| Exact exported triangles: centre/±8 at depths 2/6/12/24/40 | 0/15 | 15/15 |
| Exact exported triangles: width minus 8-stud margin at depths 2/6/12/24 | 0/8 | 8/8 |
| Runtime precise query centre, six depths | 1/6 | 4/6 |
| Runtime precise query grid | 7/30 | 17/30 |
| Runtime calibration selected offset; centre hits; score | 0; 0/1; 0 | 0; 0/1; 0 |
| Detected solid-prop corridor obstructions | 0 | 0 |

**Verified:** the corrected socket has the authored opening, coherent existing
composition and saved collision approach that north lacked. All measurements
that conclusively established the missing approach now pass. **Not fixed or
claimed verified:** the freshly cooked precise terrain query still misses the
mouth at 0/2 studs and some lateral samples, and calibration still reports
0/1. Exact exported triangles and dedicated collision independently support
the opening; those query misses cannot establish missing visible terrain.
PASS here means the sampled authored opening/collision composition agrees,
not that every Roblox query hull sample or character traversal passes.
Owner Studio visual/movement inspection remains required, including checking
that calibration retains yaw zero and scenery stays aligned in a fresh run.

## Independent geometry and production safety

The read-only Blender audit opened
`E:/BlenderAIProjects/Projects/VerdantValley_Refresh_Export_Input.blend` through
the protected launcher. Its SHA256 matches the refreshed production export
ledger, and all 30 terrain source digests match. The exact triangle BVH report
is `VV_SOCKET_AUTHORED_SURFACES.json`; the scene was never saved or regenerated.
The initial saved-default-hull experiment is preserved separately in
`VV_SOCKET_SAVED_HULL_COMPARISON.json`; it is not used as runtime calibration
evidence. Saved default hulls and newly cooked precise hulls give different
answers, demonstrating why hull-only rotation evidence is insufficient.

All 30 structure IDs match the current manifest and resolve; all 30 collision
templates resolve, with 4,033 active parts; all 823 prop placements resolve.
Roles remain 39 server solid Static/Tier 1 rows, 784 nonsolid rows including
746 Sway canopies. Existing assets, prop data, manifest IDs, current Cliff/
Cutbank data, the 118-part Stone active template and protected 202-part Stone
rollback are unchanged. Sky Citadel and Ethereal Scape files are unchanged.
**No replacement asset IDs or owner upload/import action is required.**

## Validation

- Full integrated Luau suite: **1,015/1,015 pass** (one added Refuge socket/
  neighbour placement regression across four layout yaws; existing VV/socket/
  collision/prop-role tests included).
- Blender launcher regression suite: **7/7 pass**. Protected read-only Blender
  source audit: 30/30 source terrain digests and source hash match.
- Collision verifier failure probes: **7/7 pass**. Production verifier:
  29 combined models/3,915 parts plus Stone 118 = 4,033 unique collider IDs.
  **3,915 parts still serialize physics without explicit fidelity tokens;
  physical fidelity/traversal remains owner Studio evidence.**
- Temporary Refuge→Shaded Grove saved-collision pairs: 217/220 broad samples
  pass across layout yaws 0/90/180/270. All four joins, all centre samples and
  every Refuge-side sample pass. Three outer neighbour samples, 40 studs into
  Shaded Grove at lateral +16, hit a steep side of `walk_-096_-032`
  (normal Y ≈0.369, height −0.256); yaw 90 passes all 55 samples. These are
  unresolved orientation/precision-sensitive query evidence on unchanged
  neighbour collision, not a verified repaired neighbour. See
  `VV_SOCKET_PAIR_PROBES.json`; temporary probe instances were destroyed.
- Luau syntax compilation: **129 files pass**, including both diagnostic
  scripts; Python diagnostic scripts compile. StyLua 2.0.2 check, index,
  forbidden-name, diff/handoff and production-preservation checks pass.
- Full **Rojo 7.7.0 build passes**:
  `E:/BlenderAIProjects/Runtime/vv_socket_review.rbxlx`.
  No remote CI was run because commit/push is prohibited.

## Remaining owner inspection

**Follow-up Studio result (2026-09-30):** the owner manually tested about
eight procedural seeds after the final exit/width corrections: Refuge remains
fixed, Mushroom connects correctly and corrected PATH/WIDE gates connect
cleanly, with no additional socket-placement or visible connection failures.
See `VV_SOCKET_WIDTH_REVIEW.md` for the current 42 PASS/17 SUSPICIOUS/0 FAIL
classification. The historical 19-suspicious discussion below is retained as
earlier evidence; serialized fidelity and ambiguous Studio queries remain
limitations, not confirmed metadata failures.

The 19 suspicious sockets are on Windward Ridge Gate, Forgotten Orchard Gate,
Longgrass Meadow, Fern Hollow, Cliff Passage, Mossbound Ruins, Narrow Pass,
Blossom Terrace, Rock Garden, Crystal Spring Gate, High Ledge Gate, Cliff
Overlook Gate, Mushroom Glen, Crossroads Copse and Treasure Hollow. Exact
socket/sample coordinates and reasons are in the after report. Most are
isolated collision seam/lateral misses; Crystal Spring has a centre miss at
40 studs and Treasure Hollow at 12. High Ledge's east precise hull returns
high geometry farther inward; Cliff Overlook's north calibration misses its
2-stud centre. Their exported visible triangles and saved central collision
are present; none conclusively demonstrates this metadata defect class.

Also inspect Refuge's visible south mouth and fresh runtime scenery, and the
three Shaded Grove pairwise outer samples. These are retained hypotheses/query
limitations; no character traversal or EditableMesh reconstruction was claimed.

## Files changed and reproducibility

- `src/shared/Content/Chunks/VerdantValley.luau`: Refuge socket and current
  production provenance comments; `tests/cases.luau`: four-yaw join regression.
- `tools/audit_vv_sockets.luau`: reusable Studio Server diagnostic. Execute
  in one-chunk batches because tool results truncate around 100 KB; inject
  freshly read chunk content as `VV_AUDIT_CHUNKS` to avoid require caching.
  `VV_AUDIT_FIRST`/`VV_AUDIT_LAST` select catalogue indices.
- `assets/source/worlds/verdant_valley/audit_socket_surfaces.py`: protected,
  read-only Blender source triangle audit.
- `tools/report_vv_socket_audit.py`: reproduce complete classified reports
  from captured evidence; `tools/probe_vv_socket_pair.luau`: disposable pair
  probes; `tools/test_vv_collision_verifier.py`: seven verifier failure probes.
- This report; before/after JSON and Markdown; authored-surfaces, saved-hull
  comparison and pair-probe JSON; `docs/biomes/VERDANT_VALLEY.md`,
  `docs/STATUS.md`, `docs/WORKLOG.md`, `INDEX.md`, `INDEX_MAP.md`.

## Cleanup recommendation

No replacement asset iteration was introduced. Keep every historical export,
staging/recovery source and protected rollback. Fresh diagnostic evidence is
the audit record, not obsolete asset material; no cleanup is recommended until
owner Studio and applicable later CI validation establish replacement safety.
