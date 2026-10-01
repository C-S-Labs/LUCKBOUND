# Verdant Valley complete socket audit — width_after

30 chunks; 59 sockets. Socket counts: {'PASS': 42, 'SUSPICIOUS': 17}. Chunk counts: {'PASS': 16, 'SUSPICIOUS': 14}. INTENTIONAL/SPECIAL: 0.

All 30 production chunks were sampled before production corrections. Sky Citadel and Ethereal Scape were untouched.

Samples: edge centre plus 2, 6, 12, 24 and 40 studs inward; lateral 0, ±8 and ±(Width/2−8). Runtime freshly cooked precise terrain queries; saved dedicated collision and solid props. All four cardinal approaches and all four runtime calibration scores retained in JSON. Layout yaw is zero, so layout-facing direction equals declared facing. Width/edge margin constrain the tested corridor, not the entire perimeter.

Independent visible-surface evidence: Blender triangle BVH from the preserved refreshed export input; source SHA256 and all 30 terrain digests match the production ledger. Export-local Blender axes map to imported Roblox (−X, Z, +Y), followed by selected art yaw. Boundary triangle misses at exactly depth zero are inconclusive; inset central corridor and representative width are assessed. All raw heights/normals/obstructions remain available.

PASS means sampled source/composition agreement, not a completed character traversal. SUSPICIOUS is retained for owner inspection; no automatic repair. No unusual socket has enough documented evidence to assign INTENTIONAL/SPECIAL merely to dismiss a miss.

| Chunk | Socket | Kind / direction / offset / width | Hint → selected; score / centres | Collision centre /30 grid | Terrain centre /30 grid | Authored core / width | Class |
|---|---|---|---|---|---|---|---|
| VV_PATH_SUNWASH_FORK | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_PATH_SUNWASH_FORK | 2:east | PATH / 90° / [128, 0, 0] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_PATH_SUNWASH_FORK | 3:south | PATH / 180° / [0, 0, 128] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_CUTBANK_FORD | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_CUTBANK_FORD | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_WINDWARD_RIDGE_GATE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_WINDWARD_RIDGE_GATE | 2:west | WIDE / 270° / [-128, 0, 0] / 52 | 0→0; 22 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_FORGOTTEN_ORCHARD_GATE | 1:south | WIDE / 180° / [0, 0, 128] / 52 | 180→180; 22 / 2 | 5/6; 28/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_FORGOTTEN_ORCHARD_GATE | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 180→180; 22 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_LONGGRASS_MEADOW | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 12 / 2 | 6/6; 28/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_LONGGRASS_MEADOW | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 12 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_SHADED_GROVE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_SHADED_GROVE | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_FERN_HOLLOW | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 12 / 2 | 5/6; 28/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_FERN_HOLLOW | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_PATH_CLIFF_PASSAGE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 17 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_PATH_CLIFF_PASSAGE | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 17 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_STONE_SENTINELS | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_STONE_SENTINELS | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_MOSSBOUND_RUINS | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_MOSSBOUND_RUINS | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 12 / 2 | 6/6; 29/30 | 5/6; 29/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_ANCIENT_OAK | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_ANCIENT_OAK | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_WETLAND_POOLS | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_WETLAND_POOLS | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_PATH_NARROW_PASS | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 22 / 2 | 6/6; 28/30 | 5/6; 28/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_PATH_NARROW_PASS | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_BLOSSOM_TERRACE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 12 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_BLOSSOM_TERRACE | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_ROCK_GARDEN | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 17 / 2 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_ROCK_GARDEN | 2:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 17 / 2 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_CRYSTAL_SPRING_GATE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_CRYSTAL_SPRING_GATE | 2:west | WIDE / 270° / [-128, 0, 0] / 52 | 0→0; 12 / 2 | 5/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_OVERGROWN_CAUSEWAY_GATE | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 12 / 2 | 6/6; 29/30 | 5/6; 29/30 | 15/15; 8/8 | PASS |
| VV_OVERGROWN_CAUSEWAY_GATE | 2:south | WIDE / 180° / [0, 0, 128] / 52 | 0→0; 12 / 2 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_HIGH_LEDGE_GATE | 1:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 22 / 2 | 6/6; 30/30 | 3/6; 19/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_HIGH_LEDGE_GATE | 2:west | WIDE / 270° / [-128, 0, 0] / 52 | 0→0; 22 / 2 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_CLIFF_OVERLOOK_GATE | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 1 / 1 | 6/6; 30/30 | 5/6; 28/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_CLIFF_OVERLOOK_GATE | 2:south | WIDE / 180° / [0, 0, 128] / 52 | 0→0; 1 / 1 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_DEEP_CLEARING | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_DEEP_CLEARING | 2:east | PATH / 90° / [128, 0, 0] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_DEEP_CLEARING | 3:south | PATH / 180° / [0, 0, 128] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_PATH_SPLIT_MEADOW | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_PATH_SPLIT_MEADOW | 2:east | PATH / 90° / [128, 0, 0] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_PATH_SPLIT_MEADOW | 3:west | PATH / 270° / [-128, 0, 0] / 48 | 180→180; 33 / 3 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_MUSHROOM_GLEN | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 28 / 3 | 6/6; 28/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_MUSHROOM_GLEN | 2:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 28 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_MUSHROOM_GLEN | 3:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 28 / 3 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_PATH_CROSSROADS_COPSE | 1:north | PATH / 0° / [0, 0, -128] / 48 | 0→0; 44 / 4 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_PATH_CROSSROADS_COPSE | 2:east | PATH / 90° / [128, 0, 0] / 48 | 0→0; 44 / 4 | 6/6; 29/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_PATH_CROSSROADS_COPSE | 3:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 44 / 4 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_PATH_CROSSROADS_COPSE | 4:west | PATH / 270° / [-128, 0, 0] / 48 | 0→0; 44 / 4 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_CAP_CAVE_MOUTH | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 11 / 1 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_ENTRY_DAWN_MEADOW | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 11 / 1 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_ENTRY_WOODLAND_REFUGE | 1:south | PATH / 180° / [0, 0, 128] / 48 | 0→0; 0 / 0 | 6/6; 30/30 | 4/6; 17/30 | 15/15; 8/8 | PASS |
| VV_BOSS_SANCTUARY | 1:north | WIDE / 0° / [0, 0, -128] / 52 | 180→180; 11 / 1 | 6/6; 30/30 | 6/6; 30/30 | 15/15; 8/8 | PASS |
| VV_CAP_TREASURE_HOLLOW | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 11 / 1 | 5/6; 27/30 | 6/6; 30/30 | 15/15; 8/8 | SUSPICIOUS |
| VV_CAP_WARDENS_CLEARING | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 6 / 1 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |
| VV_SIDE_FORGOTTEN_TRIAL | 1:north | PATH / 0° / [0, 0, -128] / 48 | 180→180; 6 / 1 | 6/6; 30/30 | 6/6; 29/30 | 15/15; 8/8 | PASS |

## Every detected anomaly

- **VV_FORGOTTEN_ORCHARD_GATE / south (SUSPICIOUS):** Isolated centre collision miss: 0; Inset collision sample misses: d24/l-8.
- **VV_FORGOTTEN_ORCHARD_GATE / west (SUSPICIOUS):** Inset collision sample misses: d40/l16.
- **VV_LONGGRASS_MEADOW / north (SUSPICIOUS):** Inset collision sample misses: d40/l-8.
- **VV_LONGGRASS_MEADOW / south (SUSPICIOUS):** Inset collision sample misses: d40/l16.
- **VV_FERN_HOLLOW / north (SUSPICIOUS):** Isolated centre collision miss: 0; Inset collision sample misses: d12/l-16.
- **VV_PATH_CLIFF_PASSAGE / east (SUSPICIOUS):** Inset collision sample misses: d24/l16.
- **VV_MOSSBOUND_RUINS / west (SUSPICIOUS):** Inset collision sample misses: d12/l-16.
- **VV_PATH_NARROW_PASS / north (SUSPICIOUS):** Inset collision sample misses: d12/l-16.
- **VV_BLOSSOM_TERRACE / east (SUSPICIOUS):** Inset collision sample misses: d40/l16.
- **VV_ROCK_GARDEN / south (SUSPICIOUS):** Inset collision sample misses: d40/l8.
- **VV_CRYSTAL_SPRING_GATE / west (SUSPICIOUS):** Isolated centre collision miss: 40; Inset collision sample misses: d40/l0.
- **VV_HIGH_LEDGE_GATE / east (SUSPICIOUS):** Runtime precise terrain queries disagree with a usable centre approach.
- **VV_CLIFF_OVERLOOK_GATE / north (SUSPICIOUS):** Runtime precise terrain queries disagree with a usable centre approach.
- **VV_MUSHROOM_GLEN / north (SUSPICIOUS):** Inset collision sample misses: d12/l8.
- **VV_PATH_CROSSROADS_COPSE / north (SUSPICIOUS):** Inset collision sample misses: d12/l-16.
- **VV_PATH_CROSSROADS_COPSE / east (SUSPICIOUS):** Inset collision sample misses: d40/l-16.
- **VV_ENTRY_WOODLAND_REFUGE / south (PASS):** Precise query mouth no-hit; exact export triangles and saved walk corridor agree.
- **VV_CAP_TREASURE_HOLLOW / north (SUSPICIOUS):** Isolated centre collision miss: 12; Inset collision sample misses: d12/l0, d24/l-8, d24/l8.

## Added path identity and width criterion

These follow-up verdicts include exact VV_Path mouth identity and independently measured 2-stud level pad/material widths. A 50-stud colored path with a pad at least 50 studs is the WIDE signature; a 43-stud path is PATH. No centered path mouth is FAIL even when grass/query hulls are walkable. Existing authored buffer remains included in the declared 48/52 widths. Full slices and root cause are in VV_SOCKET_WIDTH_EVIDENCE.json and VV_SOCKET_WIDTH_REVIEW.md. Original Session 204 snapshots remain unchanged.


## Evidence limitations and preservation

The saved default terrain hull differs from runtime precise hulls (comparison JSON retained). Neither hull is the visible triangle mesh. Isolated sample misses may be collider seams or query cooking artifacts and are not proof of an unusable player corridor. EditableMesh/security settings were not changed. No existing asset, ID, staging export, recovery material or protected Stone rollback was replaced.

The entire authored source was read without saving. Prop placements resolved against the saved library; solid/nonsolid/Sway counts and runtime calibration are in raw JSON. Source solid obstruction probes cover nearby authored meshes; large joined prop bounds alone are not treated as obstacles.
