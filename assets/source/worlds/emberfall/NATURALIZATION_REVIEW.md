# Emberfall — current-scene naturalization review

Historical input review. The same scene now continues through
[VOCABULARY_REVIEW.md](VOCABULARY_REVIEW.md), dated 2026-10-05.

2026-10-03. Continued **the same**
`E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/EmberfallFoundation.blend`.
No fresh build, new chunks/zones, export, upload, commit or push. The revised
EMBERFALL.md and three references remain authoritative and unchanged.

## Focused review package

Images are in the scene's `NaturalizationReview` folder. One labeled contact
sheet, `naturalization_contact_sheet.png`, accompanies individual full-size views.

| Requested evidence | Image |
|---|---|
| Top-down assembled layout, matched before/after | `before_top_layout.png`, `after_top_layout.png` |
| Three distinct terrain identities | `after_entry_open_basin.png`, `after_path_one_sided_shelf.png`, `after_combat_plateau.png` |
| Corrected baseline seam | `after_baseline_seam_oblique.png` |
| Corrected raised seam | `after_raised_seam_oblique.png` |
| Player-eye seam | `after_baseline_seam_eye.png`, `after_raised_seam_eye.png` |
| Before/after flora density and true-scale proxy | `before_flora_scale_density.png`, `after_flora_scale_density.png` |
| Recent Wasteland structure failure | `before_recent_wasteland_failure.png`, `after_recent_wasteland_failure.png` |
| Embedded basalt grouping | `before_embedded_basalt.png`, `after_embedded_basalt.png` |
| Revised lava close-up | `before_lava_close.png`, `after_lava_close.png` |
| Glow minimized | `glow_minimized_overview.png`, `glow_minimized_top_layout.png` |

Three additional combinations—ENTRY→COMBAT, fault PATH→COMBAT, and causeway→raised
gateworks—each have `combination_<name>_top/eye/oblique.png`. Temporary review
scenes were removed after rendering; the main asset inventory did not expand.
Four no-heat review states also include baseline/raised oblique seams.

## What changed

**All six playable chunks changed macro grammar**, while retaining their existing
terrain mesh topology, origins, footprint, vertical placement and molten geometry:

| Existing chunk | Current identity |
|---|---|
| ENTRY waystone | Broad open ash basin, one peripheral broken ledge |
| PATH fault | One-sided basalt shelf beside the retained narrow molten fault |
| COMBAT broken road | Broad combat plateau, one off-center collapsed shoulder |
| SIDE outskirts | Tilted sheltered ledge, localized retained vent |
| Transition causeway | Broad ascent, one slumped masonry shoulder |
| First Fortress gateworks | Buried ruin terrace with rear vertical failure |

Removed the repeated paired ribbons, double ridge shoulders, long alternating
material bands and ubiquitous narrow sculpted channels. Scenery source families
now include open ashland, a partial plateau, a single ridge/shelf, faultland and
buried ruin terraces. The three visible raised-shelf instances use a split ridge,
open tilted land and broad steps, instead of the same repeated silhouette.
The broad lava basin retains its useful containment and island geometry.

This is not a return to warped-plane hills: the current welded surfaces and
paired lip/foot support remain; strong shelf and failure regions are selected
spatially. Some chunks are deliberately simpler than others.

## Flora scale and distribution

Counts below include **visible placed plants**, excluding hidden source libraries.

| Measurement | Before | After |
|---|---:|---:|
| Plant placements | 192 | 54 |
| Average uniform scale relative to reusable source | 1.9707 | 0.6393 |
| Tallest placed plant | 11.35 studs | 2.50 studs |
| Visible evaluated triangles, whole current layout | 315,730 | 104,322 |
| Visible mesh objects | 732 | 386 |

Placement count fell **71.9%**; average source scale fell **67.6%**. Source flora
geometry remains exact. Playable chunks carry 3–4 small plants in intentional
sheltered/ruin-adjacent pockets; scenery generally carries 1–2. Empty stretches
are intentional. Partial infection states remain, including 50/50 tissue and
restrained ember veins; plants no longer dominate the terrain or foreground.

## Palette, ruins, basalt and lava

- Base ash changed from warm `(0.086,0.079,0.065)` to cool graphite/blue-gray
  `(0.064,0.073,0.086)` in Blender linear color. Basalt is blue-black
  `(0.025,0.037,0.049)`; exposed strata are desaturated gray
  `(0.043,0.048,0.052)`. Large sandy/brown terrain bands were removed.
  Masonry is cool gray; pale yellow-green plants provide restrained contrast.
- **430 old stacked-block objects** across source and placed groups were replaced.
  Twenty-one ruin-bearing groups now use partially standing wall masses, split
  corners, fresh fracture sides, leaned sections and rubble concentrated directly
  below the failed mass. Causeway/gateworks include snapped beams and fallen roof
  sections. Wasteland examples stay small and peripheral. Road paver pairs became
  fewer, broader buried foundation remnants conforming to the actual slope.
- Isolated column placements were removed. **Twenty source/placed formation
  groups** now contain 4–5 connected-looking saved basalt columns with buried
  roots, staggered height and placement beside the geological shelf. Open ashland
  and several subdued scenery families have no columns. Six reusable column
  mesh sources remain exact; no new basalt asset family was introduced.
- Lava feature count did not increase: one playable channel, one vent, one heat
  seam, one visible broad scenery basin. All molten mesh fingerprints match the
  input. Material now has a primary orange body, dark cooled edges, low-contrast
  eased irregular heat patches and restrained hotter color. Discrete nested
  contour bands were removed. Shader/material realization remains Blender-only.

## Seam construction and actual checks

Controlled seam zones are **20 studs inward**, with a short interior ease. Shared
edge logic supplies a low-relief ash profile, matching approach slopes, route
height, shoulder datum and 46-stud buried sidewall support. Meso forms begin
inside the controlled band. Sparse buried road remains and low ash folds keep
the joins from being conspicuous empty gutters.

Archetypes recorded in the scene/report: `BASELINE_ROUTE`, `RAISED_ROUTE`,
`OPEN_COMBAT`, `LAVA_ADJACENT`, `SCENERY_OUTER`. These are Blender authoring
metadata, not invented runtime socket Kinds or loader behavior.

Four main-chain joins, three targeted samples each: maximum gap **0.0000611
stud**, maximum normal disagreement **0.5275 degrees**. Six playable terrain
meshes remain closed with zero nonmanifold edges; original parent origins and
rotations are exact. Footprints stay 256×256 and the 56-stud ascent persists.
Source asset geometry and molten geometry are unchanged. Targeted Python/JSON
sanity and saved-scene review only; no collision/traversal campaign or Studio
import. Alternate pairings are visual evidence, not exhaustive connectivity
validation at every rotation.

## Honest visual assessment and Studio gate

Local volcanic identity is stronger without orange: cool ash, grouped basalt,
broken shelves, small infected plants and recently failed structures remain.
Open ash spaces now contrast with shelves and terraces instead of every tile
having the same sculpting density.

**Remaining similarity:** some scenery siblings still share coarse low-poly
facet construction. Large exterior ash aprons remain relatively plain and can
read as generic gray land in the heat-disabled overview.

**Remaining seams:** the sampled route joins and alternate pairings are
structurally continuous, and player-eye baseline/raised joins improved. Some
scenery terrace silhouettes and local faceted material changes still expose
the modular handoff in top-down/oblique views. Do not claim all seams vanished.

**Not yet stable enough for a Studio walk test.** Owner Blender acceptance of
this naturalization pass, especially remaining scenery handoffs/terrace facets,
comes first. Then simplified hidden walk collision and the already-documented
generic vertical socket measurement work can precede Studio traversal/camera
checks. No final collision tuning was done against this changing terrain.

## Current source and cleanup

`refine_emberfall_naturalization.py` edits the saved current scene once;
`review_emberfall_naturalization.py` finishes targeted composition and provides
alternate-pair evidence. `naturalization_technical_report.json` records actual
before/after measurements and the pending visual gate.

Exact input is retained as `Input_Naturalization.blend`; the original Foundation
review images/report and earlier architecture/recovery scenes remain historical.
Keep these and `.blend1` recovery files until owner acceptance and applicable
Studio/CI checks prove the new art can replace them. Recommend removing obsolete
stacked masonry/large even-scatter/isolated-column snapshots only after those
checks. No source files, exports or manifest entries were deleted or replaced.
Stop here; no production expansion.
