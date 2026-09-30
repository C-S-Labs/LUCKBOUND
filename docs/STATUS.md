# LUCKBOUND — Project Status

**Last updated:** 2026-09-30 · slimmed for token use. The full previous version, with every closed item and walk
report, is `docs/archive/STATUS_HISTORY.md`. Read it only by section, when an item below points to it.

> **New conversation?** Read `INDEX.md` → `AGENTS.md` → the top entry of `docs/WORKLOG.md` → this file.

---

## 1. Where the project stands

- **Rojo saved-asset parse verified (2026-09-30):** reported EOF errors at varying lines are consistent with reads during large Studio saves. Completed VV_COLLISION/VV_STRUCTURE/VV_PROP_LIBRARY all parse and pass a targeted Rojo 7.7 build; no repair needed. Plugin hook cause unconfirmed; reconnect after writes if warnings persist.

- **Prop save verified despite Rojo warning (2026-09-30):** owner Save to File emitted PatchTree:231 precommit nil-index warning; saved XML and live Edit library both contain 823 meshes and all four latest prop IDs. Save complete; underlying Rojo hook cause unconfirmed, visual/collision test pending.

- **Mushroom Glen / Split Meadow imports installed (2026-09-30):** four active prop meshes and exactly four placement rows updated; Split nonsolid bounds/centre corrected to current shorter mesh. Both solids precise; 823 unique active meshes and 746 wind rows preserved. Library selected for owner Save to File, then fresh Play visual/collision check. Replaced sources/imports retained in VV_IMPORT_RECOVERY.MushroomSplitProps. Repo RBXMX save pending.

- **Mushroom Glen / Split Meadow props re-exported (2026-09-30):** four solid/nonsolid FBXs ready in verdant_valley_staging_mushroom_props and verdant_valley_staging_split_props. Exact meshes/hashes/source invariants pass; Studio import/wiring and visual/collision check pending. Saved Blender source used; prior exports/library retained.

- **VV canopy wind (2026-09-30):** 746 canopies use client Sway; 77 other placements stay Static. Attributes on Content.Props.VerdantValley expose SwayEnabled, SwayStrength and SwaySpeed live during Play. Cheap parse/role/format checks pass; owner visual test pending. No obsolete iteration added.

- **VV prop library recovered (2026-09-30):** disappeared from live Edit DataModel; saved 823-mesh copy intact. Restored via existing Rojo sync, reapplied 72 changed IDs and verified all 163 refresh prop IDs. All 39 precise solid sources, 746 canopies and 12 chest components intact. Selected ReplicatedStorage.LuckboundProps.VV_PROP_LIBRARY for owner Save to File; structure/collision already saved and untouched. Cause of disappearance unconfirmed. Prop RBXMX still requires save; no duplicate recovery file left.


- **VV refreshed imports installed (2026-09-30):** all 39 imports/368 meshes matched; 165 visual sources replaced with sizes/frames/pivots preserved, two terrain IDs updated. Active Cliff has 66 meshes and five corrected floor IDs changed; Cutbank has 137 including bridge deck. Other templates retained. All 823 placement refs/sizes pass; 746 canopies/12 chest components independent; all 39 solid sources precise. Re-save grouped VV_STRUCTURE/VV_COLLISION/VV_PROP_LIBRARY, then restart Play for appearance/Cliff/bridge checks. Repo RBXMX unchanged by agent. Replaced sources kept in VV_IMPORT_RECOVERY.RefreshSources; no promotion/deletion.


- **VV refreshed staging ready (2026-09-30):** owner restored five undone Cliff floor edits; current 66-mesh Cliff source now differs from earlier staging. Existing production exporter emitted full 156-FBX kit into verdant_valley_staging_refresh, including saved appearance/geometry repairs and 137-mesh Cutbank deck collision. Cliff FBX matches refreshed source within 0.0000138 stud. Thirty chunk category coverage/name/hash checks pass; source unchanged. Targeted 39-file REFRESH_IMPORT_MANIFEST excludes combined alternatives. Studio import/ID refresh and visual/walk check pending; preserve calibrated prop/chest placement mappings. Existing exports/recovery retained.


- **Cliff collision source discrepancy (2026-09-30):** owner reports old collision still active. All 66 current Blender Cliff collider digests exactly match prior staging; active/recovery Studio templates have identical barrier mesh IDs. Re-exporting current source would repeat it. Owner identification of manually corrected source pending; no regeneration or export performed. Saved visual/Cutbank repairs remain ready for staging.


- **VV Studio art/bridge repair (2026-09-30):** placement confirmed good. Saved current Blender source with missing/zero Col repaired on 60 production meshes, stump inner-wall gap closed, Boss entrance underside skirt closed (walking surfaces/sockets unchanged), and one continuous hidden Cutbank bridge deck in existing collision collection (137 parts). 4,824 unrelated objects unchanged; source previews checked. New visual/Cutbank FBX staging, import/ID refresh and Studio verification pending. Existing runtime/exports untouched; keep fresh Studio_Repair_Input backup and prior assets.


- **VV chest placement correction (2026-09-30):** owner confirms general placement/collision now works. Six Treasure Hollow/Cave Mouth body/lid/hardware components kept Crossroads names; wiring now assigns their intended chunks and converts their centres with manifest structure frames. Each of three chests has all four component roles. Restart Play visual check pending; no re-import/re-save or Blender/texture/collision change. Recovery assets retained.


- **Verdant Valley imported kit wired (2026-09-30):** 30 current terrain IDs/dimensions/GroundOffsetY wired; current chunk-frame imports use MeshYawOffset 0. Existing props schema now has 823 verified rows, including 746 independent canopies and 12 chest components, Static for initial testing. Twenty shortened names are unique under 50 characters. Active Studio VV_STRUCTURE and VV_PROP_LIBRARY grouped; duplicate aggregate imports deleted after matching. Only Cliff collision replaced (66 parts); other 29 templates retained. All 39 colliding prop/chest meshes recooked precise, with sizes/transforms/pivots preserved. Fresh chunk/prop schema, ID/size/reference/position checks pass. Owner must save VV_STRUCTURE, VV_COLLISION and VV_PROP_LIBRARY as RBXMX at IMPORT_STEPS paths, then restart Play and catalogue/walk. Colors remain deferred. Old templates/imported Stone copy retained in VV_IMPORT_RECOVERY; cleanup only after Studio/applicable CI. No repo RBXMX saved by agent.

- **Verdant Valley initial functionality testing (owner direction, 2026-09-30):** missing/black colors/textures, including Cliff Passage structure, are deferred until functionality works; no further color repair/re-import now. Studio has 30 individual terrain models plus the combined 30-mesh verdant_valley_structure; combined 823-mesh verdant_valley_props also imported alongside individual prop files. Combined/per-chunk FBXs are alternatives, not additive content. Recommend excluding the two combined models from Workspace tests while retaining them; no Studio cleanup performed. Appearance validation/promotion remains pending. Current collision update is Cliff Passage only. Name shortening waits until import completion.

- **Verdant Valley Studio color defect (2026-09-30):** owner found black regions on Cliff Passage solid props. Cause confirmed as 6,197 zero Col corners on non-black material faces, rather than an image texture or black Part Color. Same pattern on 19 solid/seven nonsolid joined groups; 34 visible meshes lack Col. Exporter now fills absent/wholly zero colors from existing constant face materials on temporary copies, preserving painted corners and refusing ambiguous cases. Narrow 3-FBX test in verdant_valley_staging_color_check has zero black colors and exactly unchanged FBX vertices/polygons/normals. Owner deferred the Studio color comparison and broader refresh until after functionality testing; retain the color-check files for later. Previous complete staging is not approved for promotion. Collision remains validated and unchanged; no further Cliff collision import needed. Source/Studio objects untouched. Keep all earlier outputs until validation; name shortening deferred until import completes.

- **Verdant Valley production staging complete (2026-09-30):** owner removed empty canopy leftovers. The existing exporter's --production-scene mode wrote 156 FBXs to assets/export/worlds/verdant_valley_staging_validation, covering 30 structures, 4,032 current collider meshes across 30 chunks, 30 solid and 30 nonsolid groups, 746 independent canopies, and 17 special components including 12 chest pieces. Exact FBX mesh-name/source accounting and every required category pass; no Temp/unrelated content. All 76 working export files unchanged. Cliff Passage's 66 current meshes re-import with matching vertices (max error 0.0000138 stud) and match current live source digests. Linked-mesh material warnings fixed only in temporary export copies; validation set has none. Source/live scene untouched; no collision generator or promotion. JSON/Markdown manifests and VALIDATION_REPORT.json are in staging. Owner Studio validation pending. The first material-warning staging set is retained with DO_NOT_IMPORT.md; keep it, previous production exports and Blender recovery sources until Studio/applicable CI validate replacement. See IMPORT_STEPS production staging section.

- **Verdant Valley prop consolidation (2026-09-30):** saved `VerdantValley_Cleanup.blend` with 30 `chunk_<name>__PropsSolid` and 30 `chunk_<name>__PropsNonSolid` meshes in the existing collections. All 3,923 original production props accounted for exactly once: 1,262 solid sources joined, 1,894 nonsolid sources joined, 749 independent canopies, 12 components across three chests, and six review objects (four Cave Mouth flames, Dawn Meadow fire, High Ledge unclassified piece). Canopy origins and chest hinge pivots preserved. 4,836 untouched object digests match, including structure, collision and Temp; collection hierarchy unchanged. Per-element geometry/material/color/shading checks passed; all 60 outputs below 10,000 triangles. Per-chunk report: `assets/source/worlds/verdant_valley/PROPS_EXPORT_REVIEW.md`; exact source ledger in adjacent JSON. Owner Blender review and eventual Studio import/material/pivot checks remain. Keep `VerdantValley_Props_Export_Input.blend`; no FBX/Roblox asset/manifest replacement. Existing unresolved normals cases remain unresolved by this preparation pass.

- **Verdant Valley normals pass (2026-09-30):** all 30 chunks and 7,987 scene meshes scanned twice. Confirmed winding repaired on 16 visible/Temp objects and 4,005 invisible colliders (34,253 faces across instances; 34,113 unique datablock faces). Crossroads roof: 48 faces; five Cliff Passage vines plus linked Temp source: 28 each; two Wetland water patches: six each. Component-specific closed-shell orientation and selective open-surface corrections only; geometry/transforms/materials/collections preserved. Second scan found no further confirmed flips; exterior roof/vine front/back diagnostic renders reviewed. 178 ambiguous open/boundary cases remain unchanged and require manual review before declaring the kit clean for consolidation. See `assets/source/worlds/verdant_valley/NORMALS_REVIEW.md`. Saved current `VerdantValley_Cleanup.blend`; keep `VerdantValley_Normals_Input.blend` until owner Blender and later Studio verification. No joining, export grouping or production export change.

- **Cliff Passage annotated-zone finish (2026-09-30):** retained nineteen appropriate earlier additions and owner tree deletions. Six linked reference trees, twenty-seven exterior ground props and twenty-six nonsolid props in eight irregular yellow-zone pockets now detail upper/rear slopes and path transitions. One permitted reusable `VV_Vine` has five linked wall instances, three long on one wall and two short on the other. Full new bounds exclude red local-Y ±21; all additions entering yellow (to ±40) have `CanCollide=false` and nonsolid collection membership. Tree/major-prop mesh data comes directly from existing references. All 7,916 existing objects unchanged, including cliffs, terrain, path and collision. Eleven saved-source views reviewed; `VerdantValley_Cleanup.blend` saved. Owner Blender and eventual Studio/export collision checks pending. Keep `VerdantValley_Cliff_Zones_Input.blend`; older environmental review/source artifacts can be removed only after validation.

- **Cliff Passage continuous rock surfaces (2026-09-29):** owner-directed reconstruction supersedes modular structure and selective refinement. Each exposed wall is one welded irregular surface: 41 broad polygons, eight staggered interior vertices and two unequal broad depth changes. No extruded modules, rectangular patches or seam-cover slabs. Exact original seam samples and ridgeline preserved; terrain, path, props, transforms, sockets and collision unchanged, with 7,911 unrelated-object hashes matching. Ten views inspected: both passage directions, player stations, overhead, both overview sides and close range. Source saved; owner Blender and eventual Studio/export/walk checks pending. Keep `VerdantValley_Cliff_Continuous_Input.blend` until validation.

- **Cliff Passage selective refinement (2026-09-29):** softened three of eight secondary formations at unequal strengths, preserving strongest masses and all topology. Only 312 of 3,765 vertices moved inward (maximum 1.670/1.269 studs); materials, terrain, transforms, collision and 7,911 other objects unchanged. Four paired player-height views reviewed. Source saved; owner Blender and later Studio/export review pending. Keep `VerdantValley_Cliff_Selective_Input.blend` until validation.

- **Cliff Passage major rock structure (2026-09-29):** supersedes the shallow face-detail pass below. Four uneven structural formations plus a broad recessed bay per wall; buttresses meet the base, with tilted plates and short shelves. New forward changes capped at three studs; recesses avoid the existing earth bank. Five eye-height stations per wall, entrance/exit and both overview sides inspected; 14 final saved-source renders match the candidate. All 7,911 other objects, materials, transforms, path, corrected upper silhouette and collision unchanged. Nearest formation stays 25.58 studs from route center and outside the path material. Source saved; owner Blender and eventual Studio/export/walk checks pending. Retain `VerdantValley_Cliff_Structure_Input.blend`.

- **Cliff Passage exposed-face detail (2026-09-29):** only cliff_01/02 shaped with four broad asymmetric folds each and a shallow uneven ledge. Maximum projections under two studs; terrain, ridgeline, path, props, collision and 7,911 other objects unchanged. Overview and both passage views inspected. Owner Blender and eventual Studio/export/walk checks pending. Keep `VerdantValley_Cliff_Detail_Input.blend`. Eight pre-existing cliff_02 boundary edges preserved.

- **Cliff Passage remaining grass patch (2026-09-29):** owner-marked upper outer-edge Earth patch corrected to Grass on five triangles only. Saved-source close review complete; geometry and all other assignments/objects unchanged. Owner review pending.

- **Cliff Passage material finish (2026-09-29):** latest owner geometry locked. Rim/underside assignments now follow peer chunks: rock below a thin earth lip, no green lower shell faces. Unified contrasting grass blocks on top, retaining flat facets. All 3,534 vertices, 4,271 faces and 7,912 other objects unchanged. Source saved; three-view review complete, owner Blender and eventual Studio/export checks pending. Retain `VerdantValley_Cliff_Material_Input.blend`.

- **Cliff Passage stray seam edges (2026-09-29):** removed 173 face-less edges left by seam stitching from the live terrain mesh. All 4,272 surface faces unchanged, zero loose/open edges; all 8,013 other objects unchanged. Green colors, complete cliff meshes, latest owner placements and collision preserved. Source saved; owner viewport review pending. Reference: `VerdantValley_Cliff_Edge_Input.blend`.

- **Cliff Passage face/color correction (2026-09-29):** supersedes the incomplete-shell repair below. Both cliff meshes again have 598 faces and zero open edges; local buried cap adjustment avoids surface overlap. Upper shoulders and all four marked end connections are green per owner clarification. Saved current live source, retaining ongoing owner edits; all 941 path faces and 7,928 protected input objects unchanged. Saved-source overview/both ends reviewed; owner approval and later Studio/export checks pending.

- **Cliff Passage owner-adjusted seam repair (2026-09-29):** fresh live reference is `VerdantValley_Cliff_Seam_Input.blend` (7,931 objects). Repaired unwelded ridge cut boundaries and missing end faces; removed duplicate cliff front/top surfaces, retaining owner cliff transforms. Exposed banks now use `VV_Earth`. Main terrain has zero open boundary edges, 7,064 triangles; each cliff 600. All 941 path faces and 7,928 protected objects unchanged. Saved-source overview/both ends reviewed; owner Blender and eventual Studio/export checks pending. Production assets/collision unchanged.

- **Cliff Passage long-ridge rebuild (2026-09-29):** replaced both toothed grass/rock strips in `VerdantValley_Cleanup.blend` with planar broad profiles (two rises and a shallow dip), and rebuilt the two existing cliff caps to share their exact seam. No added props; affected ground-attached props only reseated vertically. Matching-angle saved-source render shows obvious silhouette change and no exposed green wedges. All 941 path faces and 7,910 protected objects unchanged; 6,761 terrain triangles. Blender source saved/loaded; owner visual approval and eventual Studio/export check pending. Keep `VerdantValley_Cliff_Ridge_Input.blend`; production exports/collision unchanged.

- **Windward Ridge center patch (2026-09-29):** smoothed 527 local terrain vertices in the current 7,933-object `VerdantValley_Cleanup.blend`; topology retained, 7,932 other objects unchanged. Saved-source close render reviewed. Owner Blender review and eventual Studio/export/collision alignment checks pending; production assets unchanged. Retain `VerdantValley_Windward_Patch_Input.blend` until validation.

- **Phase 1 is complete** (hub, roll, onboarding, saves, UI, sprint and double jump, events). The build spec §7
  amendments that opened later work are §7.1 expedition entry, §7.2 parties as their own server, §7.3 scenarios,
  §7.4 caps, §7.5 loot and §7.7 universal map generation (2026-09-27).
- **Worlds you can enter:** Verdant Valley (30-piece chunk kit — built, **needs a revamp pass**), Sky Citadel
  (36-piece chunk kit, walked and verified, with ambience, props, chests and the vault) and Ethereal Scape
  (**41-piece hybrid kit** — floating isles + temple + meadow, 2 landmarks, 2 miniboss arenas, 6 backdrop
  pieces with drifting cloud props, height variation — on the §7.7 generation blueprint, 2026-09-27; final
  polish pass done (map-wide skyrays, natural mushroom patches, overhang check) — **not yet uploaded or walked**). Emberfall and Astral
  Reach have no map yet.
- **Verdant Valley baseline:** `codex/vv-stone-walk-collision` starts from the
  pre-separation `ce0f29f` commit. The authoritative art is
  `assets/source/worlds/verdant_valley/verdant_valley_30_cleanup_review.blend`;
  the joined `VV_STRUCTURE.rbxmx` remains the visible kit. The failed full
  separation activation is preserved on `codex/vv-full-separation-reference`.
  The reviewed scene and baseline contain the reviewed 30-mesh Blender scene,
  validated FBX, Studio-imported `VV_STRUCTURE.rbxmx`, and synced mesh IDs. All 30 imported names and dimensions
  match the export report. The saved kit now records PreciseConvexDecomposition on all 30 MeshParts;
  the runtime loader already requests that fidelity. The visual Studio walk and
  in-experience asset-access check remain open before merge. Floating collision
  and visible terrain gaps in the owner's walk remain unresolved.
- **Verdant Valley Blender organization:** The owner's saved scene has top-level
  `VV_STRUCTURE`, `VV_COLLISION`, `VV_PROPS_SOLID`, and `VV_PROPS_NONSOLID`
  collections. Its 30 joined visual chunks are intact; 4,032 collider meshes
  were imported from the current kit, Stone Sentinels, and Cliff Passage FBXs.
  Both prop collections are empty pending classification. Each collision group
  now uses its matching visual chunk's saved Blender transform. Save/reopen
  checks found 30 unique matching origins, no group at the scene origin, and
  unchanged collider vertex/face data; owner visual review remains.
- **Verdant Valley scenery pilot:** Wetland Pools, Cutbank Ford, and Mushroom
  Glen were the first three chunks separated. The owner reviewed them and
  manually corrected three classifications; those edits remain in the current
  scene. The original pilot report records the state before those corrections.
- **Verdant Valley full Blender scenery separation:** After the owner reviewed
  and manually corrected the pilot, the other 27 joined chunks were separated
  in the current scene. Overall collection counts are 72 `VV_STRUCTURE`, 1,145
  `VV_PROPS_SOLID`, and 1,880 `VV_PROPS_NONSOLID`. The pilot corrections and
  all 4,032 collision meshes were preserved. Nineteen genuinely ambiguous
  gold/large-rock pieces remain in structure and are listed in
  `SCENERY_CLASSIFICATION_REMAINING.json`. Owner Blender visual review is next;
  production assets have not changed.
- **Four-chunk scenery review (2026-09-29):** The owner's
  `VerdantValley_Extra_Details_Backup.blend` now has 56 added objects in Treasure
  Hollow, 73 in Longgrass Meadow, 56 in Deep Clearing and 66 in Warden's Clearing,
  spread across wider planting zones. Their distinct features are a detailed
  lantern/traveller's pack, pale flowering tree/wildflowers, trail marker and split stump with
  fungi. `Temp` now contains the five original sources plus reusable `lantern_post`
  (six sources total). On the owner's explicit follow-up, its two flowering-tree
  sources were removed and the placed Longgrass tree became a centerpiece: seven
  canopy lobes, 49 larger muted pink/cream flowers, tapered pale branches and roots.
  Four bark marks now follow the actual tapered trunk faces and are embedded against
  the surface; only their 32 vertices changed in the owner-reported floating-mark fix.
  Its original placement and solid/nonsolid grouping remain; the other 8,021 scene
  objects match their pre-edit geometry/transform/membership digest. Saved-source
  close and overhead renders reviewed; Blender approval and later Studio check pending.
  The hanging lantern is now 15% smaller with
  aligned timber/shoe/crossbeam joins; the owner's later placement edits were preserved.
  only Treasure Hollow has a placed lantern. All 30 original structure chunks
  remain intact. New solid bounds stay at least 38.46 studs from the central
  route line; Deep Clearing's east branch is reserved. Protected scene geometry
  and transforms matched before/after the pass. Owner Blender review is next;
  this scenery pass changed no Studio assets or production exports.
- **Remaining Verdant Valley composition pass (2026-09-29):** the live
  `VerdantValley_Extra_Details_Backup.blend` has restrained additions on 24 of the
  remaining 26 chunks (746 dressing objects, 19–37 per modified chunk). Cliff Passage
  and Cave Mouth needed none. At completion, the four references and all original
  7,279 objects matched the pre-pass geometry/transform/membership digest (the later
  owner-authorized flowering-tree exception is recorded above); collision,
  sockets, terrain and primary landmarks are unchanged. Whole-kit overhead and
  individual route/low feature renders were reviewed; crowded planting was thinned
  and repeated flower/stone details differentiated. New bounds remain 22.73 studs
  inside rectangular footprints and 35.56 studs from socket route centerlines.
  Owner found initial islands too clustered: 319 props redistributed across wider
  shoulders and 386 linking props added. Unique details stayed fixed.
  `COMPOSITION_REVIEW.md` in the world source folder records each chunk. Owner
  Blender visual review is next; no production export or Studio rollout occurred.
- **Pre-cleanup Verdant Valley geometry review (2026-09-29):**
  The live scene was captured as `VerdantValley_Geometry_Review_Reference.blend`
  after owner edits in Longgrass Meadow and Wetland Pools. Reviewed all 30 chunks;
  no scene edits. Four floating details: Woodland Refuge top stacked log (0.179 stud),
  Cliff Passage and Crossroads Copse canopy contact gaps (0.223/0.191 stud), and
  Crystal Spring foam over dry grass (0.43–0.61 stud above terrain). Recurring solid
  rock/trunk intersections and log/boulder or rock/masonry intrusions are recorded
  by exact object name in `GEOMETRY_REVIEW.md`; 52 solid pairs reviewed closely,
  with normal joins/rock clusters retained as lower-priority overlap candidates.
  All 8,023 live object hashes match the refreshed reference after the read-only pass.
  Follow-up fixes must preserve owner edits; prior generator outputs are not the
  current reference. Production exports and Roblox collision hulls were not changed.
- **Current Verdant Valley landmark refinement (2026-09-29):** owner manual edits
  supersede that review. Current authoring file is `E:/BlenderAIProjects/Projects/VerdantValley_Cleanup.blend`;
  the 7,946-object input is retained as `VerdantValley_Landmark_Refinement_Input.blend`.
  Ancient Oak now has a tapered branching trunk, ten canopy lobes, seated bark scars and root moss.
  Treasure Hollow's chest now has broad wooden planks, a domed lid, metal hoops, hinges,
  carry rings and brass lock; the same model is installed in Cave Mouth and the new Crossroads
  shelter. Covered Cave Mouth terrain uses bare-earth material (167 faces, no geometry edits).
  Cleared Crossroads' center obstacle and the marked northeast planting; added a small open
  timber shelter on stone footings with a chest inside. Final scene has 7,937 objects.
  All 7,920 unrelated input objects, including collision and the other finished references,
  match their geometry/transform/collection hashes. Existing chest feet seated against terrain;
  feature and overhead renders reviewed. Owner Blender approval and eventual Studio/export
  checks remain; no production assets changed. Keep rollback sources until those checks pass.
- **Loot-chest and Crossroads follow-up (2026-09-29):** current source remains
  `VerdantValley_Cleanup.blend` (7,959 objects). All three chests are about 21% smaller
  than the first detailed model (14%, then another 8% following owner size feedback),
  with planked/metal-trimmed lid ends, a hollow wooden box and simple tied loot sack.
  Each lid is a single separate mesh with its complete moving trim/hasp and a rear
  local-X hinge pivot; a -105-degree open pose was reviewed without saving animations.
  Rigging/gameplay hookup remain for later. Crossroads shelter moved to local (56,56),
  rotated to -45 degrees so its open front faces the junction; two existing tree
  assemblies and 13 Temp-derived rocks/bushes/tufts frame its sides/back.
  All 7,925 unrelated input objects match hashes; terrain, collision, sockets and
  Ancient Oak are unchanged. Closed/open and overhead/source renders reviewed.
  Keep `VerdantValley_Loot_Chest_Input.blend` and older rollback sources until owner
  approval and later Studio checks; production exports remain unchanged.
- **Chest interior follow-up (2026-09-29):** all three shared chests now have 20
  broad inner wall planks matching the outside and an off-center sack tipped onto
  its side, seated on the plank floor. Six meshes changed; all 7,953 other objects
  match their hashes. Original body vertices/faces, outer bounds, lids, hinges and
  hardware are unchanged; the closed exterior render is pixel-identical to the
  approved model. Saved-source open/close views reviewed; source remains 7,959 objects.
  Keep `VerdantValley_Chest_Interior_Input.blend` until owner review and later Studio
  checks; no production exports changed.
- **Chest lid seam correction (2026-09-29):** five roof-panel slits closed per
  chest (120 vertices per lid); outer dimensions, other geometry and hinge transforms
  unchanged. All 7,956 other objects match hashes. Saved close render reviewed;
  keep `VerdantValley_Lid_Seam_Input.blend` until approval and later Studio checks.
- **Crossroads shelter support/stone follow-up (2026-09-29):** four post extensions
  connect the header frame to the rafters, with two center king posts supporting
  the ridge. Stonework now has seated masonry courses, beveled worn corners,
  flagstone paving, and segmented step/footings. Only frame/stone meshes changed;
  7,949 other objects in the owner's current 7,951-object scene match hashes.
  Roof, chest, terrain/collision and surrounding planting are unchanged. Front/side
  renders reviewed; keep `VerdantValley_Shelter_Support_Input.blend` until owner
  approval and later Studio checks. No production export changed.
- **Stone Sentinels collision prototype:** A new generator derives 202 thin,
  16-stud walk-surface tiles from the current connected terrain body. It
  excludes 80 detached art components and leaves steep/open spans unbridged.
  Blender checks: 203 FBX meshes reimported including the origin marker; 2,893
  of 2,965 4-stud samples hit the custom surface, including 353/356 in the
  north approach; maximum sampled height deviation is 0.245 stud before the
  intentional 0.35-stud lowering. The loader is isolated to Stone Sentinels
  and disables joined visual collision only when the imported model is present.
  Studio imported and prepared all 202 parts. On a temporary assembled chunk,
  the joined visual's collision was off and all 253 reference rays hit at each
  of four yaws with maximum 0.351-stud error. A character walked about 95
  studs along the central route while grounded and at full health. The
  saved model is `assets/rbxm/chunks/verdant_valley/VV_STONE_SENTINELS_COLLISION.rbxmx`.
  XML inspection found 202 unique MeshIds and names, explicit precise fidelity
  on all parts, and a zero pivot. Rojo reloaded it: 94 north-approach rays all
  hit within 0.351 stud; a character walked to the north mouth grounded and
  at full health. Three deliberately omitted steep north-edge samples produced
  no Roblox collision hit, so the pilot did not bridge those openings. An
  owner visual walk at the exact prior failure spot and a
  two-client check remain before any kit-wide rollout.
  The owner requested that this prototype remain local until newer repository
  versions are reconciled; no push or PR has been made.
- **Stone Sentinels collider optimization:** On local branch
  `codex/vv-stone-collision-merge`, compatible adjacent 16-stud tiles from the
  same reviewed Blender scene collapse from 202 to 118 MeshParts (41.6% fewer).
  The original RBXMX remains as the known-good reference. The merged asset has
  118 unique uploaded meshes, a zero pivot, and explicit precise collision;
  Stone Sentinels alone now selects it through `CollisionTemplate`. Studio
  raycasts against the saved asset at four yaws hit 253/253 visible-surface
  samples with mean/p95/max height errors of 0.315/0.350/0.351 stud (original:
  0.333/0.350/0.351); all three cliff probes remained open. A 4-stud grid
  had 2,933 shared hits, 1,036 shared misses, zero one-sided hits, and at most
  0.220 stud height difference between colliders. A temporary loader build
  confirmed 118 pieces active with the visual mesh collision and queries off.
  An in-game character walk and owner visual check at the former invisible
  floor remain pending. Do not extend this optimization across the kit yet.
- **Stone Sentinels Studio render-surface feasibility:** In Studio Edit mode,
  `CreateEditableMeshAsync` opened the uploaded visual MeshPart (7,084 render
  faces, 14,993 vertices). Six `EditableMesh:RaycastLocal` surface heights were
  within 0.35 stud of the existing custom collider; at one lower-area sample,
  the visual physics hull hit 1.31 studs above the rendered surface. This is
  sufficient evidence for a render-geometry input prototype, but a generator
  would still need to distinguish walkable ground from joined scenery. The
  same API was blocked in Play mode by the experience Mesh & Image API setting;
  no setting was changed and no generator was built.
- **Verdant Valley reported-panel repair batch (2026-09-29):** Boss Sanctuary's latest
  repair passed the owner walk. Seven more chunks have targeted replacement FBXs
  generated from the active Blender scene: Blossom Terrace 195→122, Treasure Hollow
  169→112, High Ledge Gate 192→132, Crossroads Copse 224→170, Split Meadow 210→155,
  Shaded Grove 194→124, and Forgotten Trial 248→208 (initial cells→colliders).
  Their reported panels are unmerged; 4-stud cells address reproduced low or missing
  hits. The refreshed 28-chunk report is 5,629→3,848, with 3,967 intended kit
  colliders including Stone Sentinels and Cliff Passage. The seven models are staged
  in Studio with 3,848 unique MeshIds, zero pivots and correct settings. The owner
  saved the wrapper; precise-fidelity XML repair, file verification and Rojo build
  pass. Owner walking is pending. Stone's existing 118-part merged model was lifted 0.30 stud
  to match the other chunks' 0.05-stud surface offset; MeshIds and geometry are
  unchanged, and its 202-piece rollback remains untouched. Cliff Passage is excluded.
- **Cliff Passage corridor candidate (2026-09-29):** Only this chunk's saved Blender
  geometry was edited: 343 grass crest vertices softened within 1.5 studs sideways
  and 0.8 studs vertically; a one-chunk visual FBX is exported. A separate collision
  FBX has 64 terrain sampled floor tiles across the central corridor and two
  overlapping, 60-stud-tall side walls. Both socket ends stay open; the hills have
  no walk collision. Cliff Passage now names its own optional collision template,
  which replaces the joined visual's old physical deck when imported. The other
  28 collision models and Stone Sentinels were untouched. Both FBXs are now
  staged in the local testing Studio place: Cliff visual MeshId
  `rbxassetid://108374847811684` is in `VV_STRUCTURE` and in `AssetManifest`,
  while all 66 uploaded colliders are under `VV_COLLISION` with a zero pivot.
  Basic generation/count and Studio part-setting checks pass; owner RBXMX save,
  crest review and corridor walking are pending. The latest current-scene
  revision extends 235 upper grass-shoulder vertices inward up to 4.2 studs
  along both rock-face seams. Its one-chunk visual FBX was refreshed; owner
  Blender review and Studio reimport are pending. A side-view follow-up smoothed
  the sharp crest tips, tucked low grass behind the gray face, and converted
  exposed steep skirts to the existing rock material. The current Blender scene
  and visual FBX include that revision; collision remains unchanged.
  After the owner's finalized Cliff Passage collision passed a Studio test but
  was absent from the saved RBXMX, the re-imported 66-part model was added back
  under the live Studio `VV_COLLISION` wrapper as
  `VV_PATH_CLIFF_PASSAGE_COLLISION_MERGED`. All 28 prior templates remain
  present with their prior part counts; the Cliff model has 64 floor tiles,
  two barriers, 66 unique uploaded MeshIds, a zero pivot and correct settings.
  Owner save of the wrapper as `VV_COLLISION.rbxmx` and a follow-up Studio test
  are pending; the repository file still lacks this model.
- **Verdant Valley adaptive collision kit batch (2026-09-28):** The owner's
  active scene at `E:\BlenderAIProjects\Projects\VerdantValley_CliffPassage_SeparateCollisionDeck.blend`
  is the input (SHA-256 `4b4568595bb6b24f4c7ca0bb0a78aa2699f30cdb020448cb4d39e45b49ebe6bf`).
  The currently saved 28-chunk RBXMX other than Stone Sentinels and Cliff Passage has 5,494
  initial generated cells and, after targeted repairs, 3,631 merged collider meshes. Including the preserved
  118-part Stone model and Cliff Passage's current one-piece visual collision,
  the intended kit total is 3,750. Boss Sanctuary is now the unusually high
  chunk at 267; next are Windward Ridge Gate 156, Sunwash Fork 153 and Deep Clearing 146. FBXs, a per-chunk count report and
  guarded `CollisionTemplate` entries are local. In the owner's separate
  Studio place, all 28 models were imported, named, pivoted and staged in
  `ServerStorage.LuckboundChunkKits.verdant_valley`; a post-recovery check
  confirmed the original 3,425 MeshParts with unique valid MeshIds, precise fidelity and
  expected per-model counts. The owner exported `VV_COLLISION.rbxmx`; its
  initial selection included Stone and visible kit copies and 31 top-level
  models, which Rojo rejected. The file now has one `VV_COLLISION` wrapper
  containing exactly the 28 new models. After the owner's first walk found
  fall-through spots in Fern Hollow's `walk_patch_-032_-016_4x2`, that one
  64 × 32-stud patch was replaced by eight 16-stud cells (Fern 112 → 119).
  A focused Studio probe found no misses around the former hole and heights
  within 0.003 stud of the Blender surface. The 28 new models were raised
  0.15 stud, leaving an effective 0.20-stud surface offset; Stone and Cliff
  were unchanged. Fern Hollow and Cutbank Ford socket-edge collision heights
  match within 0.001 stud, so the second named Fern patch was not altered.
  The owner's next walk confirmed Fern Hollow's gap is fixed, but found
  another physics gap/depression on Narrow Pass's `walk_patch_-016_+064_2x4`
  near Sunwash Fork. A small sample across the 2×4 patch class found no other
  misses. Narrow Pass's eight cells were left unmerged (127 → 134 parts), and
  its repaired socket edge matches Sunwash Fork within about 0.002 stud at
  nine sampled positions. The owner estimated that roughly 90% of chunks
  still had visible foot sinking, so the 28 new models were raised another
  0.10 stud, leaving an effective 0.10-stud offset. Studio verifies 28 models,
  3,439 parts, 3,439 unique MeshIds, precise fidelity and expected flags.
  The owner saved the updated wrapper RBXMX; on-disk XML fidelity repair and
  count/MeshId verification and Rojo build passed. The generator and full FBX set now use the
  same 0.10-stud offset. Cutbank Ford's bridge currently relies on the structure
  for collision, and Wetland Pools appears visually slightly high despite
  working collision; both are noted for later, with no changes this pass.
  The next walk found a remaining Narrow Pass dip on `walk_+000_+112`.
  That cell was split into sixteen 4-stud cells (Narrow 134 → 149), and a
  focused 25-point Studio probe now has no misses or low corner hit. The owner
  also reported visible collider geometry and slight general foot sinking;
  all 28 rollout templates are now invisible and lifted another 0.05 stud,
  leaving a 0.05-stud surface offset. The loader also hides collider geometry
  during Studio play. Studio sanity checks found 3,454 parts, unique MeshIds
  and correct flags. The owner saved the updated wrapper; fidelity repair,
  on-disk verification and Rojo build pass. The owner walk is pending.
  Severe sinking at the Boss Sanctuary entrance's sloped flank is under
  targeted review. The owner is open to an invisible boundary but wants to
  avoid blocking the entry; the exact spot is needed before placing one.
  The owner subsequently confirmed Narrow Pass is good and reported a
  socket-adjacent dip on Entry Dawn Meadow's 2×4 panel plus fall-through spots
  on Boss Sanctuary's separate 6×5 panel. A seeded Studio spot check sampled
  15/57 panels of at least 2×4 size at 25 points each: no random-panel misses
  or >0.20-stud interior depressions. Targeted checks reproduced one Boss
  panel miss and a 0.35-stud low hit near Entry's socket. Candidate FBXs split
  both panels and their failing corner cells. The owner imported both
  replacements; Entry's 45 focused socket samples and Boss's 25 focused panel
  samples now hit without the reported defects. The combined RBXMX was saved
  and verifies 3,520 unique MeshIds, hidden parts and restored precise fidelity.
  The full generated report reads 5,403 initial cells → 3,520 colliders;
  Rojo build passes and owner walk testing is pending. The separate Boss
  entrance-edge issue remains.
  The owner confirmed Entry and the prior Boss panel repair, then found a
  second Boss issue on `walk_patch_-080_-048_10x4` and showed visible terrain
  outside the collision grid. Boss Sanctuary's authored footprint is 384×256,
  but the generator had sampled only 256×256. A new Boss-only candidate samples
  the full ±192-stud width and splits the reported 10×4 panel into forty
  16-stud cells. Its generated bounds reach x ±192 and y ±128; Boss becomes
  349 initial cells → 267 colliders. The full candidate report is 5,494 cells
  → 3,631 colliders, or 3,750 across the kit with unchanged Stone and Cliff.
  The owner imported the 267-part Boss model; all 45 focused panel probes hit
  and sampled outer-strip points beyond the former ±128-stud boundary now hit
  terrain. Studio verifies 28 models and 3,631 valid collider parts. The
  combined RBXMX was saved and its omitted precise-fidelity XML restored;
  file verification and Rojo build confirm counts, MeshIds and flags. Owner walking of
  the Boss perimeter and entrance is pending.
  No high-count optimization
  or broad automated raycast test was run.
- **Overgrown Causeway split pilot (2026-09-28):** the reviewed joined mesh was
  separated into one connected terrain mesh (256 × 43.5 × 256) and one static
  scenery mesh containing 88 detached trees, rocks, ruins and moss components.
  Both mesh IDs load in the LUCKBOUND Studio place with precise collision. The
  `Collide` opt-in now builds static Tier 1 scenery on the server under the
  replicated chunk; the client skips those rows. A temporary four-yaw stage
  confirmed server-to-client replication with no duplicate client prop, sampled
  path raycasts, character traversal at all four rotations, and an obstacle
  stopping the character. This is a pilot check, not complete geometry coverage.
  A saved prop library, live `SizeY`/MeshId update, and two-client Studio test
  remain pending. Other 29 chunks and the old live Causeway asset are unchanged.
  **New warning to fix later:** `[ChunkLoader] solid prop
  'prop_overgrown_causeway_scenery' missing from LuckboundProps for
  VV_OVERGROWN_CAUSEWAY_GATE`. No Causeway behavior was changed in this check.
- **Wetland Pools joins (2026-09-28):** the temporary per-mouth socket-height
  change was reverted after the owner's next walk showed the route beyond
  Wetland Pools dropping by about two studs. The reviewed Blender mesh has
  both visible mouths at the same height; the higher Studio raycast hits were
  on its collision hull. Both socket offsets are zero again. Restart the live
  run to verify the restored route level, then inspect the collision hull
  separately. No mesh asset was replaced.
- **Full Verdant Valley separation candidate (2026-09-28):** Blender now has
  `verdant_valley_separated.blend` with 30 connected terrain objects and 66
  `prop_*` objects (37 solid, 29 ambient). Both FBXs were imported in Studio;
  staged `VV_STRUCTURE.rbxmx` and `VV_PROP_LIBRARY.rbxmx` contain all 96 named
  MeshParts and uploaded MeshIds, with anchored parts and precise collision on
  terrain and solid props. `ids.json`, a split report, and candidate chunk/prop content are staged under
  `assets/export/worlds/verdant_valley/`. The two former side-named cap meshes
  now use `chunk_cap_*` in the candidate. Exporter checks geometry conservation,
  colors, socket openings and FBX reimport; the candidate Luau suite passes.
  **Failed historical candidate, not the desired baseline.** The owner walk
  found invisible collision floors over lower terrain across the kit because
  each remaining terrain mesh was still large and concave. Do not activate or
  roll this candidate out; retain it only for diagnostics and tooling.

  | Id | Rarity | Weight | Phase | Map | Enterable? |
  |---|---|---|---|---|---|
  | `VERDANT_VALLEY` | Common | 6000 (60%) | 1 | chunk kit, 30 pieces — needs a revamp pass | ✅ |
  | `ETHEREAL_SCAPE` | Uncommon | 1500 (15%) | 1 | chunk kit, 41 pieces — hybrid isles/temple, §7.7 blueprint, not uploaded | ✅ |
  | `EMBERFALL` | Rare | 1500 (15%) | 1 | blueprint written | ❌ no kit |
  | `SKY_CITADEL` | Epic | 700 (7%) | 1 | chunk kit, 36 pieces — walked and verified | ✅ |
  | `ASTRAL_REACH` | Mythic | 300 (3%) | 1 | blueprint written | ❌ no kit |
  | `THE_UNKNOWN` | Unknown | 5 | 3 | none | ❌ no kit |

  (Supersedes the Worlds table in `docs/archive/STATUS_HISTORY.md`, written before Sky Citadel had a kit.)
- **Enemies:** the framework is built and all 16 Sky Citadel enemies are modelled, rigged and exported. The Winged
  Sentinel (Boss 3) runs in Studio through `/showboss`, with the Aether Lance's lightning and `/bossphase`. Ethereal
  Scape has a drafted 9-enemy roster (1 basic built: Aether Wisp) under `assets/source/enemies/ethereal_scape/`.
  **Nothing spawns in gameplay yet.** `EnemyDef` + services wait for the owner's OK.
- **Tooling:**
  - **Luau CLI (2026-09-28):** official `luau-lang/luau@0.740.0` is pinned in `rokit.toml` and installed locally. The assembled headless suite passes: 905/905. The CLI has no `--version` option; `rokit list` confirms the pin.
  - **Codex Studio MCP (2026-09-28):** connected to the LUCKBOUND place; a temporary Play stage supported the Causeway pilot check. Stopping Play discarded the test stage and temporary prop source.
  - **Developer panel + command registry** (2026-09-27): F4 in Studio; 39 commands, all clickable, autocomplete; see `docs/DEV_TOOLS.md`.
  - `INDEX.md` + `INDEX_MAP.md` give the repo map, and CI keeps the map current.
  - StyLua is enforced.
  - 908 headless tests passing locally as of 2026-09-28.

## 2. Next — pick up here

> **2026-09-27: close ship berths fixed after precommit review.** Berths now use
> the island's oriented face and half the ship's beam, with a 20-stud hull gap;
> overlap/approach checks use the ship box instead of its enclosing sphere.
> This supersedes the earlier radius-based berth calculation. 866 tests pass,
> including angled mesa/carrier and all-side clearance regressions; changed docking
> files lint clean. Studio docking observation remains pending. Owner authorized
> a final review, commit and push of all related test-command/docking changes.

> **2026-09-27: hub docking corrected locally.** Large galleons/carriers explicitly
> opt into docking; whales and other orbiters do not, regardless of size. Berths
> account for full ship radius and clearance. Ships brake to a full stop, retain
> steering while approaching and have a turn-scaled timeout; docking and visual
> headings are separate. Docking tunables are in HubLayout.V2.Docking. 862 tests
> pass; medium/higher graphics Studio docking observation remains pending.
> Owner confirms the catalogue test environment now works after the loader fix.

> **2026-09-27: catalogue load crash fixed locally.** Owner's Output traced the
> failure to ChunkLoader's test return-offset rotation: CFrame.Angles was missing
> its third argument, aborting loading on the first entry. Added the zero Z angle;
> all five calls in the loader now supply three arguments. Restart Play after sync
> and rerun the catalogue to verify complete loading in Studio.

> **2026-09-27: catalogue orientation and streaming correction.** Separated chunks
> now turn their sockets along the observation row, with rotated footprint spacing
> and return-portal offset. Test stages use Persistent streaming to keep the whole
> kit in client Explorer; normal streaming stays unchanged. 858 tests pass. Studio
> verification of all 30 VV folders, orientation and the 60-minute timer remains
> pending. These address visible weaknesses in the test implementation; the earlier
> screenshot of normal assembly still needs command/expedition Output evidence.

> **2026-09-27: test timer extended to 60 minutes.** Test instances use 3600 seconds
> in place and through the reserved-server manifest; normal durations are unchanged.
> 854 tests pass. Owner's screenshot shows normal assembly (index 0 and 108–110,
> repeated chunks), rather than catalogue assembly. Awaiting the command/expedition
> Output replies and model TestMode attribute to distinguish stale Studio code from
> a lost selection; the reported missing-chunk issue is not yet resolved.

> **2026-09-27: catalogue test roll implemented locally.** `/roll <WORLD_ID> test`
> selects the next instance's all-chunk observation line; ordinary `/roll` keeps
> seeded generation. Every current kit definition appears once, including rare
> pieces and multiple entry/boss variants, with matching joins where possible,
> configured gaps otherwise, and open sockets allowed. The flag follows the
> server manifest and is bound to one roll/instance. 851 headless tests pass;
> Studio catalogue/normal-roll and published teleport checks remain pending.

> **2026-09-27: Verdant Valley cap variety, local change.** Cave Mouth remains a cap;
> Treasure Hollow and Warden's Clearing are now caps; all three caps are unlimited
> and equally weighted following the owner's corrected direction. Forgotten Trial is
> the sole SIDE chunk. Kit names, generated
> content, exporter and manifest agree; mesh IDs and geometry are unchanged.
> 817 tests pass; 400 additional VV layouts close every socket and exercise repeat
> placements of both converted caps. Studio/Rojo loading and walks remain pending.

> **2026-09-26: local socket recovery** on `codex/recover-socket-fixes`, based on main `5090ace`: canonical VV mesh mappings, per-chunk calibration tolerance, centre-hit diagnostics, and Rojo 7.7 restored. Latest main and recovery both pass 817 tests; full Rojo build and Luau syntax pass. Studio four-yaw asset/collision checks remain pending; existing 43 seam-height failures are a separate baseline. New Ethereal Scape and enemy work preserved. No push or main merge.

> **2026-09-26: Ethereal Scape converted from a `PrebuiltMap` to a 30-piece chunk kit, owner-directed.** It shipped
> as one composed, hand-authored, no-combat traverse (a map-generation test rig). That is superseded:
> `Content/Worlds/EtherealScape.luau` now declares a chunk kit + `MapPathLength` like Sky Citadel and Verdant
> Valley; `Content/Chunks/EtherealScape.luau` has the 30 pieces (generated by
> `assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py`, geometrically validated, not yet uploaded or
> walked); `docs/biomes/ETHEREAL_SCAPE.md` is the schema. A 9-enemy roster was drafted alongside it
> (`assets/source/enemies/ethereal_scape/ROSTER.md`), one basic built (Aether Wisp) to prove the palette
> translates to a character; `Enemies`/`BossId`/`LootTableId` stay empty, same as every other world, since no
> world's combat content is built yet (§7.6, reserved). `tests/cases.luau`'s "Ethereal Scape" group and the "two
> ways a world gets a map" checks were rewritten for the new reality — **run the suite before merging**, this
> session could not (no local Luau interpreter). The original scene stays in the repo as the palette's source of
> truth. See `docs/biomes/ETHEREAL_SCAPE.md`'s header for the full reasoning.

> **2026-09-26: §7.6 reserved for enemy AI/combat, module names locked.** Build spec §7.6 now claims the number
> `ENEMY_AI.md` §12 step 0 asked for, so no other branch can take it. `CombatCore`, `PerceptionCore`, `EnemyAICore`,
> `DifficultyCore`, `BossCore`, `TelemetryCore`, `EnemyService` and `BossService` are locked as the final module
> names. **Nothing opens yet** — combat/enemies/bosses stay excluded by §7's list. Remotes and `GameConfig` blocks,
> the rest of step 0, are deferred to step 1, when the actual schemas exist to design them against.

> **2026-09-25: enemy AI designed, not built.** `docs/ENEMY_AI.md` is now authoritative for enemy behaviour:
> utility AI over the framework's roles, no difficulty setting (a shared versioned profile plus an invisible,
> capped personal tempo adjustment), harder play pays extra loot rolls never better odds, universal versioned
> boss evolution with rollback, and weapons carrying their own moves with unique Legendary movesets. It sets a
> mandatory build order. Nothing is opened: step 0 is a §7.x amendment for the owner to approve, and items and
> inventory still come first.

> **2026-09-25: animation ids are account/group-scoped, documented.** A partner playtesting `/showboss
> winged_sentinel` in their own place got a silent `Animation failed to load` warning for the Idle id — same class
> of bug as a mesh uploaded to the wrong account (`assets/README.md` already covered that for meshes). Documented
> in `docs/PARTNER_SETUP.md` ("Animation and other account-scoped ids") and `BossPreviews.luau`'s header. No code
> changed — `DebugSystem.luau`'s `/showboss` animation loading is correct; Roblox just denies cross-account asset
> fetches without raising an error. Once LUCKBOUND is published under one group with all assets uploaded to that
> same group, this stops affecting real players — it only bites Studio testing across separate accounts/places.

> **2026-09-25: audit + index.** `INDEX.md` is the mandatory first read for every AI agent: a hand-written guide,
> plus `INDEX_MAP.md`, generated with the exact line of every symbol. `AGENTS.md` holds the agent rules, and
> `CLAUDE.md`/`GEMINI.md` point to it.
>
> Legacy Verdant Valley pieces are gone. The kit is `VV_STRUCTURE.rbxmx` (the same shape as `SC_STRUCTURE`).
> The duplicate Fern Hollow and Mushroom Glen manifest rows were removed on `socket-fixing`; both canonical keys point to the current 30-piece assets in `VV_STRUCTURE.rbxmx`. The owner confirmed both pieces load their intended meshes in Studio on 2026-09-25. Earlier socket warnings were downstream of the wrong assets loading. Boss Sanctuary rotation is verified.

> **2026-09-25: the Winged Sentinel stands in Studio.** Run `/showboss winged_sentinel` in the boss arena: 16 studs,
> facing the entrance, playing the Idle_Guard animation (`rbxassetid://132590990835909`). The Aether Lance's web is
> geometry plus live Beams; `/bossphase 2` charges the plasma blade.
>
> **Owner to verify:** re-import the latest `WingedSentinel.fbx` (with pinned anchors), then check that the strands
> show (`/showboss` reports the count) and that `/bossphase 2` opens the blade halves.
>
> Next for enemies:
> - The rest of the Sentinel moveset animations (Epic tier and above get weapon animations).
> - The `EnemyDef` + services wiring, which awaits the owner's OK.
>
> Queued:
> - The crossroads chunk pass.
> - The hub refinish.
> - Recolours and scenarios stay parked until after release (files kept).

> **2026-09-24: enemies have a framework.** `docs/ENEMY_FRAMEWORK.md` +
> `assets/source/enemies/_framework/` build, validate, pose, animate and export every enemy in every biome.
> Sky Citadel's 16 enemies are built and exported (`assets/export/enemies/sky_citadel/`); the Winged Sentinel has
> Idle, the P2 transition and the first moveset attack. Studio wiring (`EnemyDef` + services) awaits the owner's OK.

## 3. Decisions locked in

These are settled. Do not relitigate without a deliberate reversal.

| # | Decision | Where |
|---|---|---|
| **D-8** | **Fate is TRUE RNG.** No player state ever changes the odds of any world. | spec §3.3 |
| **D-9** | **15-roll scripted onboarding**, peaking on Epic at roll 8, never Mythic. Slot 5 extended to Uncommon 2026-09-16 — arc unchanged in shape. | spec §3.3.1 |
| D-3 | Roll cooldown 3.0 s, enforced server-side, silent on rejection | spec §3.4 |
| D-4 | Reveal duration scales with rarity (2.5 s → 7.0 s) | Constants |
| D-6 | Roll history capped at 50 entries | GameConfig |
| D-7 | Expedition 720 s default — **still flagged as too long**; a world may override it and Ethereal Scape runs 300 s | spec §6 |
| **D-10** | **A rift reward is permanent; only the WINDOW is temporary.** No decay, no charge, no expiry attribute. Fair only while events recur — that is a commitment, not a preference | `EVENTS.md` §5.4, §6 |
| **D-11** | **The finder gets the unique item; everyone gets the event.** Ten Catalyst Stars produce ten game-wide occasions, not ten private ones | `EVENTS.md` §5.5 |
| **D-12** | **A failed rift run costs the attempt, not the event.** The rift stays open to all until the event ends; no per-player attempt counter | `EVENTS.md` §5.3 |
| **D-13** | **Event access never depends on the roll pool.** A biome with a live event is directly enterable by anyone, regardless of what their pool contains — otherwise pool progression locks high-tier players out of the events they have earned | `EVENTS.md` §5.4b |
| **D-14** | **Events are tiered AMBIENT / MODIFIER / WORLD**, enforced by the validator. Only WORLD may open a rift or grant a unique | `EVENTS.md` §4.0 |
| — | **Expedition entry is open; combat/loot are not** | spec §7.1 |
| — | Destination = the player's last roll. No new state, no schema bump | `ExpeditionCore` |
| — | Biome lighting is applied **per client**, never by the server | Blueprint §6 |
| — | Rarity colour is a UI/portal contract; biome palette is set dressing | Blueprint §4.1 |
| — | Compass mapping N=-Z, E=+X, S=+Z, W=-X, up=+Y | GameConfig.HubLayout |
| — | **A prefab is registered from a NAMED PART, not from its model pivot.** A pivot is invisible metadata an FBX chain mangles quietly; a part name is already the contract with the artist | `Util/PrefabLoader` |
| — | **Scale and compass corrections are content, never re-exports.** An importer setting is fixed by a number in `Prefab` | `Content/Hub/Crossroads` |

### Why true RNG matters downstream

With no odds tilting, **a player at roll 200 faces identical odds to one at roll
16.** "Stuck in Commons" is a permanent condition, not an early-game phase.
Fate cannot weight its way out of it.

The lever that stays consistent: **Fate unlocks which pools you draw from,
never how the draw resolves.** Higher Fate grants access to a pool that has no
Common in it. That is the Phase 3 design, and it is the answer to the
progression-feel problem.

---

## 4. Open items (one line each; details are in the archive under the same bold name)

| Item | Severity / state |
|---|---|
| **Reserved declarations are now registered** | **New 2026-09-23** |
| **Unused sockets are never capped** | Medium |
| **A chunk's mesh origin must be its footprint centre, and nothing enforces it** | **High** |
| **Runs were a single straight shot** | **Fix pushed 2026-09-23, unproven** |
| **World ambience** | **Built 2026-09-23, walked and verified 2026-09-25** |
| **Ambient props** | **Live 2026-09-23, walked and verified 2026-09-25** |
| **Loot, fixtures, vault keys** | **Live 2026-09-23, walked and verified 2026-09-25** |
| **Verdant Valley 30-piece kit exported** | **Open 2026-09-25 — kit built and walked; needs a revamp pass** |
| **The Grove did not survive the upload** | Medium |
| **The scenario layer** | **New 2026-09-22, headless only** |
| **A brief that specifies the piece gets the piece it specified** | **Process** |
| **Kit target raised to 12–16 pieces** | **Content** |
| **The kit was generated stacked at one point** | Low |
| **Portal plane is still above head height** | Medium |
| **18% of rolls land on a world with no map** | **High** |
| **A chunk mesh is stretched to its declared size** | **High — narrowed 2026-09-23** |
| **Chunk colour on a single MeshPart is unverified** | **High — testable now** |
| **The authored hub's collision set, take two** | Medium |
| **A re-delivered prefab loses its baked `CollisionFidelity`** | Medium |
| **Scaling the horizon cannot change its apparent size** | Note |
| **The horizon wants a purpose-built chunk** | Low |
| **Trees on the bordering floating islands are malformed** | Low |
| **The portal's stop has nothing to lead to yet** | **Open** |
| **The mountain horizon is built, not placed** | Low |
| **First-join intro screen** | **Built, walked and verified 2026-09-25** |
| **The Engine portal is to become the way into biomes** | **Architecture** |
| **The authored Fate Engine is wired** | **Walked and verified 2026-09-25** |
| **Ethereal Scape's `Scale_Reference` proxy is loose** | Low |
| **The scene has no `EntryAnchor` / `ReturnAnchor`** | Medium |
| **Ethereal Scape: one whole map, not eight chunks** | Decided 2026-09-17 |
| **The Crossroads wants a revamp after testing** | **Design** |
| **Staircase clipping at the walkway junctions** | Medium |
| **The live menu tint is unseen** | **High** |
| **Rifts: event-gated dungeons** | **Design** |
| **The event sky is built** | **Walked and verified 2026-09-25** |
| **The event catalogue is a proposal, not a plan** | **Design** |
| **Three panels are designed, not implemented** | Expected |
| **Five settings are stored and honoured by nothing** | Medium |
| **Travel landings are guesses with a safety net** | Medium |
| **Profile schema is now v2** | Note |

## 5. Environment

- Code: `C:\Dev\luckbound` (not OneDrive — must stay outside it)
- Place: `LUCKBOUND_dev.rbxl`, local, unpublished
- Rojo CLI 7.7.0 via Rokit; Studio plugin 7.7.0
- **Unpublished means no DataStores.** Expected; the server runs in volatile
  mode and says so. Publishing is what enables saving.

### Startup

```powershell
cd C:\Dev\luckbound
git pull
rojo serve
```

Studio → open `LUCKBOUND_dev` → Rojo panel **Connect** → **Accept** → **▶ Play**

---
