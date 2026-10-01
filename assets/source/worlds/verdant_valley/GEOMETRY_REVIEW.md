# Verdant Valley — geometry review (2026-09-29)

Current reference: `E:/BlenderAIProjects/Projects/VerdantValley_Geometry_Review_Reference.blend`, captured from the owner-edited live scene. All 8,023 object hashes are recorded in `Geometry_Review/reference_manifest.json`. Live scene still matches this reference after review: zero changed objects. **Report only: no meshes, transforms, collections or collision were edited.**

All 30 chunks were checked using current mesh contact/intersection tests and individual overhead/route previews; 56 selected findings received close views from two directions. Scope: floating geometry in either prop collection, and intersections involving collision-classified solid props. Canopy/vegetation overlap was ignored. Ground embedding, connected tree roots/branches, bridge joinery, cave/arch masonry, clustered natural rocks and fire sparks were separated from likely unwanted intrusions.

The scene contains 1,307 solid props, 2,648 nonsolid props, 30 terrain objects, 4,032 existing collision meshes and six Temp sources. Temp display props and the invisible collision templates were excluded from floating-art checks. This checks Blender art and intended solid classification, not the final Roblox collision hulls.

Owner edits are now authoritative. Compared with the prior bark-fix input, changed meshes/transforms occur in Longgrass Meadow and Wetland Pools (the comparison also includes our intervening bark correction). **Do not rerun the dressing/tree generators over the owner-edited scene to fix this list.** Use the current object geometry and placement.

## Floating details

| Chunk | Objects | Finding | Blender XY offset from chunk origin |
|---|---|---|---|
| Woodland Refuge | `composition_003_log` | Top log has a measured 0.179-stud gap to the two lower logs. Minor but genuinely unsupported. | (68, -60.5) |
| Cliff Passage | `tree_canopy_27`, `tree_canopy_30` over `tree_trunk_13` | Crown group misses its trunk by about 0.223 stud at the closest surface. Canopy overlap is fine; this is a contact gap. | (56.6, -75.2) |
| Crossroads Copse | `tree_canopy_05`, `tree_canopy_06` over `tree_trunk_03` | Crown group misses its trunk by about 0.191 stud. | (-72.7, -61.3) |
| Crystal Spring Gate | `water_foam_03` | Foam lies over dry grass, about 0.43–0.61 stud above terrain at its corners. This is the clearest stray floating item. | (-35.9, 43.6) |

Object names in these tables use the suffix after `chunk_name__`. The following table retains full names for precise selection. Floating gaps are mesh measurements, not guessed from thumbnails. The closest-surface estimates in the raw candidate file are sampling results; the dedicated measurements above use both surfaces.

## Solid intersections to review

52 selected solid intersection pairs were visually inspected. Thirty-seven involve tree trunks; recurring trunks passing into nearby boulders are the main cleanup pattern. The fallen log in Split Meadow crosses through its boulder, and added rocks intrude into masonry in Overgrown Causeway, Crossroads Copse and Forgotten Orchard. Some shallow rock-to-rock overlap and stacked wood contact may be acceptable by intention; those remain recorded as lower-priority overlap rather than automatic fixes. All are static solid-classified objects.

| ID | Chunk | Full object names | Approximate intersection offset XYZ | Assessment |
|---|---|---|---|---|
| C1 | Ancient Oak | `chunk_ancient_oak__rock_07` / `chunk_ancient_oak__tree_trunk_09` | (64.814, 38.893, 3.908) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C2 | Ancient Oak | `chunk_ancient_oak__rock_09` / `chunk_ancient_oak__tree_trunk_12` | (91.519, 24.849, 2.889) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C3 | Blossom Terrace | `chunk_blossom_terrace__rock_02` / `chunk_blossom_terrace__tree_trunk_07` | (-67.914, 55.427, 3.597) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C4 | Blossom Terrace | `chunk_blossom_terrace__composition_027_rock` / `chunk_blossom_terrace__tree_trunk_09` | (-61.962, -64.185, 3.818) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C5 | Blossom Terrace | `chunk_blossom_terrace__rock_06` / `chunk_blossom_terrace__tree_trunk_12` | (60.677, -39.607, 4.463) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C6 | Cave Mouth | `chunk_cap_cave_mouth__cave_structure_01` / `chunk_cap_cave_mouth__tree_trunk_03` | (-62.437, -59.37, 7.741) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C7 | Cave Mouth | `chunk_cap_cave_mouth__cave_rock_10` / `chunk_cap_cave_mouth__tree_trunk_03` | (-62.437, -59.755, 4.439) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C8 | Cave Mouth | `chunk_cap_cave_mouth__cave_structure_07` / `chunk_cap_cave_mouth__tree_trunk_04` | (68.096, -50.009, 6.583) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C9 | Cliff Overlook Gate | `chunk_cliff_overlook_gate__composition_030_rock` / `chunk_cliff_overlook_gate__tree_trunk_07` | (53.96, -72.92, 3.968) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C10 | Crystal Spring Gate | `chunk_crystal_spring_gate__rock_07` / `chunk_crystal_spring_gate__tree_trunk_07` | (-21.358, 91.528, 7.92) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C11 | Cutbank Ford | `chunk_cutbank_ford__rock_13` / `chunk_cutbank_ford__tree_trunk_13` | (86.686, 65.719, 1.816) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C12 | Dawn Meadow | `chunk_entry_dawn_meadow__tree_trunk_06` / `chunk_entry_dawn_meadow__composition_025_rock` | (83.064, 27.809, 4.244) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C14 | Woodland Refuge | `chunk_entry_woodland_refuge__composition_023_rock` / `chunk_entry_woodland_refuge__composition_028_rock` | (60.588, 51.599, 5.341) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C15 | Fern Hollow | `chunk_fern_hollow__rock_01` / `chunk_fern_hollow__tree_trunk_03` | (-90.621, -18.261, 2.713) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C16 | Fern Hollow | `chunk_fern_hollow__rock_04` / `chunk_fern_hollow__tree_trunk_07` | (-80.758, 39.774, 2.064) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C17 | Fern Hollow | `chunk_fern_hollow__rock_07` / `chunk_fern_hollow__tree_trunk_18` | (58.83, 64.766, 3.437) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C18 | Fern Hollow | `chunk_fern_hollow__composition_029_rock` / `chunk_fern_hollow__tree_trunk_22` | (72.186, -68.9, 3.96) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C19 | Fern Hollow | `chunk_fern_hollow__tree_trunk_21` / `chunk_fern_hollow__rock_08` | (73.706, 49.908, 3.265) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C20 | Forgotten Orchard Gate | `chunk_forgotten_orchard_gate__ruin_piece_05` / `chunk_forgotten_orchard_gate__composition_020_rock` | (53.129, 46.821, 2.014) | Rock intersects masonry; review intrusion versus intentional rubble. |
| C21 | Forgotten Orchard Gate | `chunk_forgotten_orchard_gate__composition_020_rock` / `chunk_forgotten_orchard_gate__ruin_piece_07` | (60.951, 47.004, 3.357) | Rock intersects masonry; review intrusion versus intentional rubble. |
| C22 | High Ledge Gate | `chunk_high_ledge_gate__composition_027_rock` / `chunk_high_ledge_gate__rock_09` | (53.4, -51.414, 3.024) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C23 | High Ledge Gate | `chunk_high_ledge_gate__rock_10` / `chunk_high_ledge_gate__tree_trunk_08` | (69.315, 73.921, 14.272) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C24 | Mossbound Ruins | `chunk_mossbound_ruins__rock_05` / `chunk_mossbound_ruins__composition_032_rock` | (41.039, -50.017, 2.606) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C25 | Overgrown Causeway Gate | `chunk_overgrown_causeway_gate__composition_029_rock` / `chunk_overgrown_causeway_gate__ruin_piece_07` | (54.985, -63.979, 2.645) | Rock intersects masonry; review intrusion versus intentional rubble. |
| C26 | Overgrown Causeway Gate | `chunk_overgrown_causeway_gate__tree_trunk_13` / `chunk_overgrown_causeway_gate__rock_07` | (86.751, -55.506, 2.625) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C28 | Cliff Passage | `chunk_path_cliff_passage__cliff_01` / `chunk_path_cliff_passage__tree_trunk_19` | (85.884, -40.105, 9.248) | Trunk embeds in sloping cliff surface; likely intentional ground contact, lower priority. |
| C29 | Cliff Passage | `chunk_path_cliff_passage__cliff_02` / `chunk_path_cliff_passage__tree_trunk_03` | (-71.861, 51.187, 19.033) | Trunk embeds in sloping cliff surface; likely intentional ground contact, lower priority. |
| C30 | Cliff Passage | `chunk_path_cliff_passage__rock_52` / `chunk_path_cliff_passage__tree_trunk_15` | (56.66, 57.0, 34.586) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C32 | Crossroads Copse | `chunk_path_crossroads_copse__composition_024_rock` / `chunk_path_crossroads_copse__ruin_piece_01` | (-74.056, -75.454, 3.545) | Rock intersects masonry; review intrusion versus intentional rubble. |
| C33 | Split Meadow | `chunk_path_split_meadow__rock_01` / `chunk_path_split_meadow__tree_trunk_01` | (-79.962, 62.436, 3.895) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C34 | Split Meadow | `chunk_path_split_meadow__rock_02` / `chunk_path_split_meadow__tree_trunk_01` | (-79.962, 63.937, 3.213) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C35 | Split Meadow | `chunk_path_split_meadow__composition_001_log` / `chunk_path_split_meadow__rock_07` | (71.087, 72.728, 0.743) | Fallen log passes through boulder; obvious intrusion. |
| C36 | Split Meadow | `chunk_path_split_meadow__tree_trunk_08` / `chunk_path_split_meadow__rock_08` | (78.501, -65.834, 2.384) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C37 | Rock Garden | `chunk_rock_garden__composition_031_rock` / `chunk_rock_garden__rock_21` | (64.892, -69.495, 3.96) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C38 | Rock Garden | `chunk_rock_garden__rock_19` / `chunk_rock_garden__tree_trunk_08` | (75.766, -78.58, 2.518) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C39 | Shaded Grove | `chunk_shaded_grove__tree_trunk_03` / `chunk_shaded_grove__rock_01` | (-83.283, -50.105, 4.272) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C40 | Shaded Grove | `chunk_shaded_grove__rock_02` / `chunk_shaded_grove__tree_trunk_04` | (-76.971, 72.002, 3.138) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C41 | Shaded Grove | `chunk_shaded_grove__rock_03` / `chunk_shaded_grove__tree_trunk_04` | (-76.971, 68.283, 3.54) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C42 | Shaded Grove | `chunk_shaded_grove__composition_019_rock` / `chunk_shaded_grove__tree_trunk_09` | (-66.115, -60.78, 3.049) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C43 | Shaded Grove | `chunk_shaded_grove__tree_trunk_16` / `chunk_shaded_grove__composition_030_rock` | (43.43, -53.911, 3.719) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C44 | Shaded Grove | `chunk_shaded_grove__tree_trunk_18` / `chunk_shaded_grove__rock_07` | (54.589, -66.02, 2.905) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C45 | Wardens Clearing | `chunk_side_wardens_clearing__rock_04` / `chunk_side_wardens_clearing__detail_scatter_tree_02_trunk` | (-47.938, -68.0, 5.202) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C46 | Stone Sentinels | `chunk_stone_sentinels__rock_19` / `chunk_stone_sentinels__composition_032_rock` | (81.434, -64.713, 2.284) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C47 | Wetland Pools | `chunk_wetland_pools__composition_021_rock` / `chunk_wetland_pools__rock_08` | (-46.513, -97.943, 3.353) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C48 | Windward Ridge Gate | `chunk_windward_ridge_gate__rock_01` / `chunk_windward_ridge_gate__tree_trunk_04` | (-71.042, 71.327, 30.517) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C49 | Windward Ridge Gate | `chunk_windward_ridge_gate__rock_09` / `chunk_windward_ridge_gate__tree_trunk_08` | (58.566, 66.474, 23.857) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C50 | Windward Ridge Gate | `chunk_windward_ridge_gate__rock_10` / `chunk_windward_ridge_gate__tree_trunk_12` | (76.105, 82.524, 25.12) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C52 | Deep Clearing | `chunk_deep_clearing__tree_trunk_04` / `chunk_deep_clearing__detail_scatter_03_rock_006` | (-71.113, -66.743, 2.316) | Trunk intersects rock/cave wall; separate solid silhouettes. |
| C53 | Boss Sanctuary | `chunk_boss_sanctuary__rock_04` / `chunk_boss_sanctuary__composition_001_offering` | (-118.287, -52.0, 1.479) | Offering bowl edge clips adjacent boulder; minor. |
| C54 | Longgrass Meadow | `chunk_longgrass_meadow__detail_scatter_02_rock_041` / `chunk_longgrass_meadow__rock_05` | (62.524, 48.571, 1.828) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C55 | Treasure Hollow | `chunk_side_treasure_hollow__detail_scatter_02_rock_022` / `chunk_side_treasure_hollow__rock_15` | (45.617, 20.066, 2.729) | Solid rock-to-rock overlap; lower priority, potentially intentional cluster. |
| C56 | Treasure Hollow | `chunk_side_treasure_hollow__detail_scatter_92_log_052` / `chunk_side_treasure_hollow__woody_piece_01` | (74.408, -40.232, 1.749) | Overlapping fallen timber; lower priority, potentially intentional. |

## Coverage of all chunks

"Other overlap" is the raw intersection count remaining after the selected close review; it is mainly joined/clustered architecture and rocks, not a count of confirmed defects. No float listed means no ungrounded contact group detected above the 0.15-stud contact tolerance; it is not a guarantee about sub-tolerance gaps.

| Chunk | Floating details | Selected solid pairs | Other solid overlap candidates |
|---|---|---|---|
| Ancient Oak | None detected | C1, C2 | 13 |
| Blossom Terrace | None detected | C3, C4, C5 | 2 |
| Boss Sanctuary | None detected | C53 | 65 |
| Cave Mouth | None detected | C6, C7, C8 | 63 |
| Cliff Overlook Gate | None detected | C9 | 4 |
| Crystal Spring Gate | F51 | C10 | 14 |
| Cutbank Ford | None detected | C11 | 32 |
| Deep Clearing | None detected | C52 | 0 |
| Dawn Meadow | None detected | C12 | 6 |
| Woodland Refuge | F13 | C14 | 11 |
| Fern Hollow | None detected | C15, C16, C17, C18, C19 | 0 |
| Forgotten Orchard Gate | None detected | C20, C21 | 7 |
| High Ledge Gate | None detected | C22, C23 | 6 |
| Longgrass Meadow | None detected | C54 | 0 |
| Mossbound Ruins | None detected | C24 | 31 |
| Mushroom Glen | None detected | None selected | 34 |
| Overgrown Causeway Gate | None detected | C25, C26 | 8 |
| Cliff Passage | F27 | C28, C29, C30 | 56 |
| Crossroads Copse | F31 | C32 | 1 |
| Narrow Pass | None detected | None selected | 3 |
| Split Meadow | None detected | C33, C34, C35, C36 | 4 |
| Sunwash Fork | None detected | None selected | 1 |
| Rock Garden | None detected | C37, C38 | 17 |
| Shaded Grove | None detected | C39, C40, C41, C42, C43, C44 | 0 |
| Forgotten Trial | None detected | None selected | 11 |
| Treasure Hollow | None detected | C55, C56 | 10 |
| Wardens Clearing | None detected | C45 | 5 |
| Stone Sentinels | None detected | C46 | 12 |
| Wetland Pools | None detected | C47 | 11 |
| Windward Ridge Gate | None detected | C48, C49, C50 | 1 |

## Evidence and retained reference

External evidence directory: `E:/BlenderAIProjects/Projects/Geometry_Review/`. `sheet_0.png` through `sheet_4.png` cover all 30 chunks overhead/route. `candidates_0.png` through `candidates_11.png` show selected issues from two directions; individual `C<number>_0/1.png` and `F<number>_0/1.png` files are larger. `geometry_candidates.json` retains all 480 distinct solid intersection pairs for inspection, including normal joins; `detail_measurements.json` measures the log/canopy gaps. `reference_manifest.json` and `owner_reference_changes.json` capture current ownership of the scene.

No geometry fixes were made. Keep this new review reference for the follow-up correction pass. Earlier `Composition_After/`, `Composition_Spread/`, flowering-tree previews and their rollback blends are older visual references; they no longer describe every owner-edited placement. Retain rollback blends until approved replacements and eventual Studio checks pass, then remove superseded previews/backups if unneeded. No production export or manifest entry was replaced.

## Owner Studio follow-up repairs — 2026-09-30

Current source VerdantValley_Cleanup.blend is saved. Exact accounting is in
STUDIO_REPAIR_REPORT.json. The stump lacked an inner wall between its jagged
rim and shallow floor; eighteen inward-facing triangles now close it, while
outer geometry and unaffected custom normals remain. Boss entrance had a
floating underside skirt: ten underside vertices lowered to local Z -2.8;
all walking surface vertices and sockets preserved. Explicit targeted
triangulation removes reliance on importer polygon tessellation.

One hidden walk_bridge_deck spans the six existing Cutbank planks, with its
top 0.02 stud below their tops. Existing 136 colliders unchanged; total 137.
All other collision, especially manually corrected Cliff Passage, unchanged.
Existing material colors fill missing/wholly zero Col on sixty production
meshes (20,774 original faces); painted corners preserved. New stump walls
use existing VV_StumpHollow color. 4,824 unrelated objects retain exact hashes.

Backface-culling source previews: E:/BlenderAIProjects/Projects/VV_Studio_Repair_Review.
Updated FBX staging and Studio testing remain pending. Keep fresh
VerdantValley_Studio_Repair_Input.blend and previous exports until validation;
intermediate review snapshot and old diagnostic preview can be removed then.
