# Verdant Valley — normals validation (2026-09-30)

Saved source: `E:/BlenderAIProjects/Projects/VerdantValley_Cleanup.blend`. Rollback: `VerdantValley_Normals_Input.blend`.

## Method and validation

Scanned all 7,987 mesh objects (7,898 unique datablocks), all 30 chunks, Temp sources and 4,032 invisible colliders. Closed edge-manifold shells were oriented individually by consistent winding and positive signed volume. Candidate repairs were screened for within-component nonadjacent face intersections (none found) and enclosing component bounds. No whole-scene Recalculate Outside was performed.

Vine leaves were flipped selectively toward authored local +Y, which faces the passage on both walls. Horizontal water patches face world +Z. Open convex shells were accepted only with supporting-plane evidence against their vertex hull. Other open/nonmanifold surfaces remain unchanged for review.

Second full-scene scan: zero additional confirmed flips. Supplemental 26-direction exterior rays per unique mesh flagged five extra manual cases. Reverse-side hits on single-sided water and vines are expected. This is a conservative repair baseline with unresolved surfaces, not an unconditional all-clear.

All object invariants matched: vertices, edges, face vertex sets/counts, transforms, polygon material/smooth assignments, material slots, collection membership and custom properties. Source polygons were flipped directly to preserve corner data association. No modifiers or negative transforms were present. No composition, joining, grouping, export or production-asset changes.

## Per-chunk results

Exact affected collider names and zero-based face indices are recorded in `E:/BlenderAIProjects/Projects/Normals_Repair_Record.json`. The table reports visual/collider affected counts separately.

| Chunk | Meshes | Affected visual / collider | Faces corrected | Manual objects |
|---|---:|---:|---:|---:|
| chunk_ancient_oak | 242 | 0 / 121 | 1116 | 6 |
| chunk_blossom_terrace | 254 | 0 / 122 | 1115 | 0 |
| chunk_boss_sanctuary | 525 | 0 / 267 | 2167 | 129 |
| chunk_cap_cave_mouth | 223 | 1 / 120 | 1019 | 37 |
| chunk_cliff_overlook_gate | 230 | 0 / 118 | 1090 | 0 |
| chunk_crystal_spring_gate | 256 | 0 / 134 | 1202 | 0 |
| chunk_cutbank_ford | 314 | 0 / 136 | 1127 | 0 |
| chunk_deep_clearing | 277 | 1 / 146 | 1266 | 0 |
| chunk_entry_dawn_meadow | 299 | 0 / 122 | 993 | 1 |
| chunk_entry_woodland_refuge | 252 | 0 / 113 | 1013 | 0 |
| chunk_fern_hollow | 279 | 0 / 119 | 1114 | 0 |
| chunk_forgotten_orchard_gate | 259 | 0 / 124 | 1089 | 0 |
| chunk_high_ledge_gate | 214 | 0 / 132 | 1171 | 0 |
| chunk_longgrass_meadow | 279 | 0 / 134 | 1178 | 1 |
| chunk_mossbound_ruins | 248 | 0 / 118 | 1107 | 0 |
| chunk_mushroom_glen | 289 | 0 / 129 | 1164 | 0 |
| chunk_overgrown_causeway_gate | 245 | 0 / 122 | 1135 | 0 |
| chunk_path_cliff_passage | 243 | 5 / 66 | 664 | 2 |
| chunk_path_crossroads_copse | 283 | 2 / 170 | 1283 | 0 |
| chunk_path_narrow_pass | 258 | 0 / 149 | 1179 | 0 |
| chunk_path_split_meadow | 268 | 0 / 155 | 1220 | 0 |
| chunk_path_sunwash_fork | 275 | 0 / 153 | 1295 | 0 |
| chunk_rock_garden | 223 | 0 / 117 | 1103 | 0 |
| chunk_shaded_grove | 271 | 0 / 124 | 1141 | 1 |
| chunk_side_forgotten_trial | 283 | 0 / 208 | 1113 | 0 |
| chunk_side_treasure_hollow | 216 | 3 / 112 | 1059 | 0 |
| chunk_side_wardens_clearing | 204 | 0 / 90 | 859 | 1 |
| chunk_stone_sentinels | 232 | 0 / 91 | 631 | 0 |
| chunk_wetland_pools | 279 | 2 / 137 | 1219 | 0 |
| chunk_windward_ridge_gate | 260 | 0 / 156 | 1249 | 0 |
| Temp | 7 | 2 / 0 | 172 | 0 |

## Confirmed visible objects and sources

| Object | Faces corrected |
|---|---:|
| `chunk_cap_cave_mouth__unclassified_04` | 48 |
| `chunk_side_treasure_hollow__unclassified_03` | 48 |
| `chunk_side_treasure_hollow__detail_scatter_lantern_post` | 144 |
| `chunk_deep_clearing__detail_scatter_trail_waymarker` | 5 |
| `chunk_side_treasure_hollow__detail_scatter_traveller_pack` | 30 |
| `chunk_path_crossroads_copse__landmark_cache_roof` | 48 |
| `chunk_path_crossroads_copse__landmark_chest_hardware` | 48 |
| `chunk_wetland_pools__water_06` | 6 |
| `chunk_wetland_pools__water_07` | 6 |
| `chunk_path_cliff_passage__finish_wall_vine_01` | 28 |
| `chunk_path_cliff_passage__finish_wall_vine_02` | 28 |
| `chunk_path_cliff_passage__finish_wall_vine_03` | 28 |
| `chunk_path_cliff_passage__finish_wall_vine_04` | 28 |
| `chunk_path_cliff_passage__finish_wall_vine_05` | 28 |
| `VV_Vine` | 28 |
| `lantern_post` | 144 |

## Ambiguous objects intentionally unchanged

### chunk_ancient_oak

- `chunk_ancient_oak__woody_piece_01` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_ancient_oak__woody_piece_02` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_ancient_oak__woody_piece_03` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_ancient_oak__woody_piece_04` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_ancient_oak__woody_piece_05` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_ancient_oak__landmark_bark_moss` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_boss_sanctuary

- `chunk_boss_sanctuary__rock_10` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__rock_11` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__rock_34` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__rock_35` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__composition_001_offering` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_01` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_02` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_03` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_04` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_05` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_06` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_07` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__bush_08` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_05` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_06` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_07` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_08` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_09` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_10` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_11` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_12` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_13` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_14` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_15` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_16` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_17` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_18` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_19` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_20` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_21` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__moss_detail_22` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_07` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_08` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_09` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_10` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_11` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_12` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_13` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_14` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_15` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_16` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_17` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_18` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_19` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_20` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_21` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_22` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_23` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_24` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_25` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_26` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_27` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_28` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_29` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_30` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_31` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_32` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_33` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_34` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_35` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_36` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_37` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_38` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_39` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_40` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_41` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_42` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_43` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_44` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_45` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_46` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_47` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_48` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_49` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_50` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_51` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_52` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_53` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_54` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_55` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_56` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_57` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_58` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_59` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_60` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_61` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_62` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_63` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_64` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_65` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_66` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_67` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_68` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_69` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_70` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_71` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_72` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_73` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_74` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_75` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_76` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_77` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_78` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_79` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_80` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_81` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_82` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_83` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_84` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_85` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_86` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_87` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_88` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_89` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_90` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_91` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_92` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_93` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_94` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_95` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_96` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_97` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_98` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_99` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_100` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_101` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_102` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_103` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_boss_sanctuary__tree_canopy_104` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_cap_cave_mouth

- `chunk_cap_cave_mouth__cave_rock_02` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_06` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_07` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_08` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_09` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_10` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_12` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_13` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_14` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_15` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_16` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_17` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_18` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_19` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_20` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_22` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_24` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_25` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_26` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_29` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_30` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_31` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_32` — Exterior ray back hit: inspect open boundary/nonplanar triangulation.
- `chunk_cap_cave_mouth__cave_rock_33` — Exterior ray back hit: inspect open boundary/nonplanar triangulation.
- `chunk_cap_cave_mouth__cave_rock_34` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_35` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_36` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_37` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_39` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_41` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_rock_42` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_structure_01` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_structure_02` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_structure_03` — Exterior ray back hit: inspect open boundary/nonplanar triangulation.
- `chunk_cap_cave_mouth__cave_structure_05` — Exterior ray back hit: inspect open boundary/nonplanar triangulation.
- `chunk_cap_cave_mouth__cave_structure_06` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_cap_cave_mouth__cave_structure_07` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_entry_dawn_meadow

- `chunk_entry_dawn_meadow__fire` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_longgrass_meadow

- `chunk_longgrass_meadow__detail_scatter_flowering_tree_trunk` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_path_cliff_passage

- `chunk_path_cliff_passage` — Open/nonmanifold surface: intended side cannot be proved by topology.
- `chunk_path_cliff_passage__cliff_02` — Open/nonmanifold surface: intended side cannot be proved by topology.

### chunk_shaded_grove

- `walk_-032_+080.018` — Exterior ray back hit: inspect open boundary/nonplanar triangulation.

### chunk_side_wardens_clearing

- `chunk_side_wardens_clearing__detail_scatter_split_stump` — Open/nonmanifold surface: intended side cannot be proved by topology.

## Totals

Chunks inspected: 30  
Objects with confirmed orientation problems: 4021  
Faces corrected: 34253 across object instances (34113 unique datablock faces)  
Ambiguous objects requiring manual review: 178

Affected visual/Temp objects: 16. Affected invisible collider objects: 4005.

## Cleanup recommendation

Keep `VerdantValley_Normals_Input.blend`, audit JSON and diagnostic views until owner Blender review and later Studio verification pass. No production export or manifest entry was replaced; existing exports remain unchanged. No older asset was removed.
