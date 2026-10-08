# Emberfall — active-collapse and flora-takeover art study

**Historical input to the focused continuity refinement.** Current saved art and
review findings are in CONTINUITY_REVIEW.md; this document's counts/images describe
the retained pre-continuity iteration. Do not regenerate over the current scene.

Owner-directed 2026-10-02, continuing the **existing** architecture scene. Current
authoritative biome §1.3.1/§1.8/§2.7/§3.3/§16 and both existing references were reread.
No chunk expansion, route/loader change, enemies, boss, export, upload, commit or push.

## Result and stopping condition

**The close-range infection concept is clearer, but the landscape has not yet passed
the identity test.** With all heat materials darkened and fissure lights off, the
overview still reads as a gray volcanic landscape with added plates and plants.
It does not yet unmistakably communicate the intended active Emberfall catastrophe.
Stopped here under the owner's explicit instruction; no further content accumulation.

Remaining weaknesses: dominant smooth ridge/mound silhouettes, the central travel
surface's smoothness, repeated broad gray rock masses, and crust wedges that sometimes
read as thin regular panels or perched overlays rather than torn geological skin.
Outer/mid/inner progression is clearer in planted clusters and fresh-break details
than at landscape scale. Review these weaknesses directly, not just the better closeups.

## Open the current result

- **Same main file:** `E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview/EmberfallPrototype.blend`.
- Existing **Architecture_A/B/C** scenes and placements retained; current opening scene A.
- **Independent_Assets_LIBRARY_ONLY** contains the revised five/eight source collections.
- Added **FloraSpectrum_REVIEW_ONLY** scene compares seven flora states without changing the route.
- All new images: `Emberfall_ArchitectureReview/IdentityReview/`.
- `identity_review_sheet.png` combines outer/mid/inner player views, overview, close
  terrain, raised collapse, 30/50/70% closeups, full flora spectrum and no-heat overview.
- `identity_technical_report.json` beside this document records actual before/after
  Blender counts, source mesh triangles, unchanged seam vertices/transforms and original
  flora fingerprints. External copy accompanies the images.

The thirteen separately saved chunk files and earlier architecture sheets/reports
remain **architecture-baseline snapshots**. This art pass edits the main scene in
place; do not mistake those old isolated files for the revised art or overwrite the
current scene by running the architecture rebuild/finalizer.

## What changed

1. **Terrain surfaces:** changed continuous vertex-color weathering to charcoal/blue-black,
   scorched brown and dusty olive/ash tones. Added bevel-supported cooled-crust plates,
   offset fracture wedges, exposed scorched strata and localized deep-red fresh faces.
   Outer ENTRY/ashland has quieter old crust and three windward ash pockets; PATH/COMBAT
   adds more breakup; CAP/inner ravine/lava-field families use darker, hotter scars.
   Detail stays inland of the protected 24-stud seam band; no border noise/deformation.
2. **Geology:** 23 tall disconnected components across the five playable structures
   were lowered/buried/leaned in place, including columns and existing mass components.
   A few stronger ascent columns remain. Added broad crust fragments and broken wedges,
   with sparse glass-material accents on SIDE. This reduces pillar dominance locally,
   but did not sufficiently replace the overall mound-and-rock silhouette language.
3. **Flora:** all four original source meshes/material assignments are preserved exactly.
   Derived surviving dusty-green rosette; partial rosettes with approximately 30/50/70%
   infected surface; 50% infected seed shrub; and root/thorn invasive bloom derived from
   the original thorn pod. Original drained and charred plants remain represented.
   Partial plants retain pale tissue on one side, black tissue on the other; separate
   black climbing veins wrap the planting. Veins are consolidated per source chunk.
4. **Disaster progression:** outer pockets mix surviving/drained with early infection;
   mid pockets mix 30/50/70% and half-infected shrubs; inner pockets use heavily infected,
   charred and invasive growth. Placed sparse smoke vents in PATH and CAP, increasing
   locally toward CAP. Existing haze, overcast world/sun and fissure-light direction
   retained. No explosions, animation or particle system.
5. **Elevation:** existing 56-stud ascent and raised continuation stay intact. Cooler
   pale/mixed flora marks upper shelves; charred/root-like forms and fresh faces mark
   the failing inland shelf/ravine. The raised-collapse view looks over lower land.
   No staircase, new platform chain or change to the route/socket representation.

The 30/50/70 figures describe the approximate assigned **surface fraction**, not a
precise biological ratio. The 50% rosette visibly splits intact yellow-green and black
leaf groups; `flora_50_percent.png` and `identity_flora_half_takeover.png` show it closely.
No-heat views darken Ember_Molten/DeepHeat/FreshBreakHeat and disable local point lights;
all original heat settings are restored before saving.

## Preserved work and checks

- Five playable and eight scenery source collections, original roles, sockets,
  parent placement matrices, origins and 256×256 footprints preserved.
- **Every pre-existing terrain vertex within the 24-stud seam band is exactly unchanged**
  across the source library and all three arrangements; all original parent-empty world
  matrices match exactly. New geometry remains inward of that band. Thus the prior
  architecture seam agreement is retained without rerunning broad traversal tests.
- Original four flora geometry/material fingerprints match before/after exactly.
- Source structures remain present; no old objects deleted to restart the scene.
- Normal and heat-dark renders, saved-source readback, Python parse and index/diff
  checks performed. No Studio collision/physics or broad game tests; new raised detail
  surfaces require later collision checks before production.

## Actual object, material and triangle changes

Counts include repeated linked flora meshes, review lights/cameras, fog/horizon geometry.
Material total in the .blend: **14 → 21**; each architecture scene uses **11 → 18**
distinct materials. New root/vein and crust material families are reusable.

| Scene | Objects before → after | Meshes before → after | Triangles before → after |
|---|---:|---:|---:|
| Architecture_A | 238 → 510 | 173 → 437 | 94,562 → 195,246 |
| Architecture_B | 220 → 483 | 168 → 431 | 98,180 → 201,710 |
| Architecture_C | 216 → 482 | 164 → 430 | 92,446 → 191,158 |
| Source library | 62 → 143 | 55 → 136 | 44,796 → 74,254 |
| New review-only flora gallery | 0 → 22 | 0 → 17 | 0 → 3,412 |

| Existing source asset | Current objects | Current all-mesh tris |
|---|---:|---:|
| chunk_entry_ash_plain | 13 | 5,404 |
| path_column_pass | 16 | 9,504 |
| chunk_column_forest | 14 | 9,346 |
| side_lava_overlook | 13 | 7,640 |
| cap_collapsed_pass | 12 | 9,372 |
| scenery_ashland_a | 7 | 1,834 |
| scenery_basalt_ridge_a | 9 | 3,326 |
| scenery_basalt_ridge_high | 8 | 3,864 |
| scenery_lava_field_a | 8 | 3,574 |
| scenery_ravine_a | 7 | 3,448 |
| scenery_drained_flora_a | 9 | 2,834 |
| scenery_charred_flora_a | 8 | 5,222 |
| scenery_foothill_a | 9 | 3,326 |

All individual source meshes remain under 10,000 triangles. The art additions roughly
double layout triangle counts and substantially increase object counts because state
plantings repeat throughout the existing ring. This is a review study, not an approved
production budget. Do not add more density to compensate for unresolved macro identity.

## Organization and retained cleanup

Original collection hierarchy remains. New **SurfaceIdentity**, **FloraProgression**
and sparse **VentSmoke** children group additions under each existing asset and placed
collection. **PropLibrary/Flora_Takeover_States** contains the six derived reusable flora
assets; the original four library entries remain. No new playable/scenery chunk asset.

Keep `Input_ArtDirection.blend` (exact pre-pass architecture source), earlier architecture
images/reports, thirteen isolated baseline files and `.blend1` rollbacks. They are the
older iterations this art pass supersedes visually in the main scene. No production
export, manifest entry or runtime code was replaced. Recommend retiring redundant
review-only iterations only after owner acceptance and applicable Studio/CI checks;
the current identity failure means keep the known-good architecture input now.

Authoring script: `refine_emberfall_identity.py` reads the preserved pre-pass input and
edits its existing objects/collections; `review_emberfall_identity.py` corrects close-up
framing from actual saved plant positions. Both must use `tools/run_blender.py`.
Further art direction is an owner review decision, not an automatic continuation.
