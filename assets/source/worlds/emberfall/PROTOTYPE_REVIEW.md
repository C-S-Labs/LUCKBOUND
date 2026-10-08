# Emberfall — five-chunk prototype review

**Historical first pass.** The owner-directed seam/scenery/vertical revision is recorded
in [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md), with current saved scenes in
`E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview`. Keep this first-pass record
and its original scene/reports until the revision passes owner/Studio review.

Owner-directed 2026-10-02. Reviewable Blender prototype only; no production registration, export, upload, commit or push.

## Open the result

- Main scene: `E:/BlenderAIProjects/Runtime/Emberfall_Prototype/EmberfallPrototype.blend`.
- Five independent `.blend` scenes are in that same folder, named exactly as the chunks below. Each is centered at (0,0,0) and contains only its own structure and props.
- `emberfall_review_sheet.png` compares all five concepts, surrounding land and flora. Eight individual images are alongside it.
- `technical_report.json` contains actual mesh bounds, origins, socket samples, collection membership, flora and triangle counts. `saved_scene_verification.json` records persisted-file readback.

## Actual Blender counts

Blender 5.2.2 LTS; metric scale 1.0. Dimensions below are Blender X × Y × Z; Roblox equivalents are X × height × depth.
Counts include separated props/flora instances; structural triangle counts alone are subject to the 10,000-per-piece contract. Every individual prop is also below 10,000.

| Chunk / inferred role | Mesh / all objects | Structure tris | All mesh tris | Dimensions | Mouths |
|---|---:|---:|---:|---|---|
| `chunk_entry_ash_plain` / ENTRY | 6 / 7 | 3,278 | 4,898 | 256 × 256 × 52.372 | N |
| `path_column_pass` / PATH | 6 / 9 | 9,674 | 12,886 | 256 × 256 × 118.909 | N, S |
| `chunk_column_forest` / COMBAT | 7 / 8 | 6,778 | 10,364 | 256 × 256 × 72.517 | N, S, E |
| `side_lava_overlook` / SIDE | 6 / 7 | 3,278 | 5,854 | 256 × 256 × 68.193 | W |
| `cap_collapsed_pass` / CAP | 5 / 6 | 5,618 | 8,744 | 256 × 256 × 90.636 | S |

Main review scene: **92 objects / 76 meshes / 59,620 triangles**, including four hidden library originals, four displayed library references, five scale proxies, and review land.
Review-only surrounding land: **32 mesh objects / 11,088 triangles**; continuous fitted ash/cooled-lava collar, continental base, distant jagged ridges, one large lava field and seven cooled-flow forms.

## Chunk designs

- **chunk_entry_ash_plain**: Calm windswept ash shelf; one split blackstone fin catches an ash drift. Almost no nearby heat.
- **path_column_pass**: Narrow cool road between monumental jointed basalt walls; one snapped leaning crown and a broad internal rise.
- **chunk_column_forest**: Three combat clearings between asymmetric column groves. Lower cooled basin, main floor, upper flank; radial rather than corridor composition.
- **side_lava_overlook**: One west entrance; a broad rising ash trail ends on a high shelf beside a glassy mineral cairn. View over a vast external lava field.
- **cap_collapsed_pass**: An old road buried beneath oblique fallen columns well inside the boundary. A cold road remnant beyond and ember bloom nook suggest continuation.

## Collection and prop contract

`EF_PROTOTYPE_5_CHUNKS` contains exactly five named chunk collections. Each has a review-position parent empty and three explicitly named subcollections: `<chunk>_Structure`, `<chunk>_Props_Solid`, `<chunk>_Props_NonSolid`.
Each structure is one mesh with the exact requested chunk name; each solid group is one `prop_*` mesh. The four `prop_*` library originals live in `PropLibrary` and are hidden; placements share their mesh data. Flora is Static, Tier 2, solid=false. Solid rubble/mineral specimens are Static, Tier 1, solid=true.
`Surround_REVIEW_ONLY` is separate and never included in independent chunks. `Cameras_Lights_REVIEW_ONLY` holds cameras, lighting, scale proxies and the flora display. The two PATH preview lights also carry ReviewOnly=true and are not gameplay content.
No Role override: naming infers ENTRY, PATH, COMBAT, SIDE and CAP. No GateSide or Weight override. Explicit Openings are authoring metadata for all five because high/sunken centers can confuse the auto-probe median; PATH Supports=Traversal,Ambush and COMBAT Supports=Combat,Ambush narrow the generous defaults to the authored intent. Studio transfer is still a future manual step.

## Validation and visual review

- Exactly five requested structural objects; persisted individual files each contain exactly one, with no other chunk or surrounding land.
- All origins are (0,0,0) in the authored frame, with unit scale 1.0. Main-scene translations belong to parent empties. Every footprint measures exactly 256 × 256; no chunk/prop/flora vertex exceeds ±128 horizontally.
- Eight mouths: each tested with 20 actual mesh raycasts across the 56-stud width and first 16 studs of depth. All floor samples equal 0.0, with no overhead geometry detected by those top-down rays. This is targeted Blender sampling, not Roblox cooked-collision verification.
- ENTRY has broad calm open ground, just four low formations and a 7.38-square-stud heat hairline. PATH has about 324.11 square studs of molten ribbon, COMBAT about 133.92; SIDE has only a thin deep-heat accent and CAP no ground lava. Lava concentration differs substantially.
- COMBAT has a 48 × 64 central floor patch checked at 25 mesh samples, unobstructed by columns and gently sloped; surrounding clearings and connecting lanes add room. The gently sloped terrain area (before cover) is 53,248 square studs. Basalt groups interrupt sightlines around, rather than across, this hub.
- PATH rises broadly to about +12 internally; COMBAT lower basin/main/upper flank are roughly -10/0/+16; SIDE reaches +26 on its broad overlook and +35 on its outer ridge. All return to connection height 0. No tiny mandatory jump ledges.
- CAP collapse sits around local Y=30–75, well before the +128 boundary. Oblique columns and rockfall seal an old road, with a road remnant visible beyond and an ember-flower nook before it. SIDE has only a west mouth and ends at its overlook/mineral landmark, distinguishing it from a through-route.
- Grounded presentation reviewed in the overall, arrival, pass and elevated side cameras: the fitted review terrain hides vertical skirts and continues to ridges and lava fields. No sky beneath the authored route in those views. Exhaustive escape-camera or runtime surround validation is not claimed.
- Both flora families are present, using different species mixes in each chunk. Geometry includes curved layered petals, wax leaves, seed shrubs, beveled hexagonal columns and irregular fracture collars; smooth terrain/flora and restrained procedural bump detail test the less restrictive style. The close basalt remains deliberately stylized and may still need owner-directed weathering.

## Technical compromises / pending owner checks

- No Studio export/upload or runtime registration. Missing BOSS is intentional: this is not a boot-valid kit.
- Blender Openings/Supports properties are authoring intent; Studio attribute transfer is not automatic.
- Automatic center-median walk-height probe can misread vertical chunks; explicit Openings recommended on import.
- Multiple structural materials, procedural bump detail and smooth shading are Blender review appearance. Studio color/normal baking and collision decomposition remain unverified.
- No lava damage, loot, boundary system or permanent surrounding-land system implemented.
- Minor ENTRY/SIDE surface seams are visual cooled-crust accents; major PATH/COMBAT molten surfaces sit in recessed ground.
- SIDE origin is the common connection datum, with center carved to that datum; climb reaches eastern upper shelf.
- Distant ridges and the large lava field are intentionally crude silhouette/context tests. Review terrain is not a runtime surrounding-land solution. Some upper shelves use slopes that still require an owner movement check before production.
- Blender native partial scene-library writing crashed in BKE_view_layer_copy_data. The workaround writes collection libraries, then appends each into a clean scene and saves normally; all five were reopened successfully. No launcher bypass or Blender binary change.
- Normal-token protected launcher was required after the restricted Windows profile lookup refused execution.

## Reproduce

Run `build_emberfall_prototype.py`, then `finalize_emberfall_review.py` through the repository shared `tools/run_blender.py` launcher with factory startup. Run `review_emberfall_prototype.py` with the bundled Python/Pillow runtime to assemble this sheet and report. There is no FBX export path or production write in these scripts.

## Leftover cleanup

No production asset, export, manifest or earlier biome iteration was superseded. Blender-created `.blend1` backups in the prototype folder retain preceding review saves/collection libraries; keep them until owner acceptance and applicable CI/Studio validation, then remove only the unneeded prototype backups. Keep the main scene, five independent scenes, reports, scripts and references. No second batch until owner approval.
