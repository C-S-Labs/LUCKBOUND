# Emberfall - Variant A/B architectural consistency review

2026-10-08. Local branch agent/emberfall-area2-blockout; input 7682ae8.
Variant B is the architectural source of truth. Stop for owner visual review.

## Correction

The previous audit checked source names, which did not prove architectural correspondence.
This pass checks actual active B mesh geometry. No new A rooms or structural features.

- Removed unmatched legacy WestGuardHall/FailingGallery buildings, reveal ledge and
  associated fragments, plus a relocated rear bearing wall and invented solid stair
  treads/landing. The marked entry route is unchanged; it crosses original B open ground
  where the unmatched halls formerly stood. Remaining entrance-room geometry is constrained
  to B's entrance room, retaining intentional damaged openings.
- Constrained surviving wall, floor, roof and support remnants to their corresponding
  original B volumes. 71 unmatched/empty pieces removed, 45 pieces constrained; one further
  duplicate residential wall removed to eliminate overlapping faces.
- Crater-edge residential room: front roof and upper-floor bays retreat, front/west upper
  walls and unsupported parapet sections collapse. Substantial rear corner and supported
  roof strips remain within the actual residential building. Debris stays peripheral.
- Broken front gate roof remains a surface subset of B's existing open roof mesh.
  Cut-face normals/material slots repaired; no material-polish pass.

## Verification and limits

All active A architectural objects covered: 139 fixed solid-volume subsets and one open
roof surface subset; 183 exact shared B objects; 79 previously displaced fragments tagged
separately to real B sources. Displaced rubble is not claimed to occupy original B positions.
Boolean difference against actual B source volumes verifies the fixed solid remnants;
nearest-surface probes verify the open gate roof. Saved checks cover every retained fixed
survivor. After the full geometric audit, one duplicate was removed and normals/material
slots repaired without moving retained geometry; final saved coverage/preservation rechecked.

651 B/shared castle mesh signatures, 887 settlement/transition/grounds signatures, all three
approved arena meshes and A_ROUTE signatures match input exactly. B boss/reward rooms,
castle footprint and shared exterior silhouette unchanged. No crater resize or floor change.
These are bounded blockout correspondence checks, not engineering or combat validation.
Owner visual assessment of structural survival remains necessary.

## Owner-editable scene and evidence

Scene: E:/BlenderAIProjects/Runtime/Emberfall_AreaII/EmberfallAreaII.blend
View layers: VARIANT_A_CATASTROPHE / VARIANT_B_STRONGHOLD. Default CONSISTENCY_overhead.
Removed alternatives isolated in PRE_CONSISTENCY_RETAINED, excluded from selected variants.

Evidence folder: E:/BlenderAIProjects/Runtime/Emberfall_AreaII/ConsistencyReview/
- consistency_review_sheet.png: matched overhead plus crater-edge before/after.
- matched_overhead.png: B/A at identical camera position, orientation and ortho scale.
- crater_edge_comparison.png: corrected residential-room collapse close view.
- B_overhead_before/after.png, A_overhead_before/after.png, A_edge_before/after.png.

Repository consistency_report.json records actual B counterparts and edits;
consistency_checks.json records geometric residuals and final saved coverage.
consistency_protection.json records protected inputs and external deliverable hashes.
Generator: correct_castle_consistency.py, always through tools/run_blender.py.

## Review / next

Evaluate whether all remaining A rooms read as destroyed B spaces, whether the marked route
through cleared ground remains legible, and whether the residential rear remnant reads as
catastrophic failure without intruding on the broad flat arena. No unresolved correspondence
failure in checks. Stop here; do not begin production or further castle detailing.

20-minute target remains TOTAL pre-boss gameplay, with unproven combat timing. No scale change.
Whole castle is one logical special finale unit, not a 256x256 restriction; no chunk separation.
Village variety, market composition, shared village/castle language and selective interior
charring/beam damage remain deferred production/design observations only.

Cleanup: retain all prior scenes, .blend1, archived inputs, recovery collections and evidence.
This review supersedes source-name-only assertions in IMPACT_FAILURE_REVIEW.md, not its
historical record. Recommend removing obsolete recovery/iterations only after owner acceptance
and applicable replacement checks; no files were deleted from prior archives.
