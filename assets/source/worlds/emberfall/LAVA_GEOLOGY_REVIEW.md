# Emberfall — contained lava and terrain-language refinement

Focused owner-directed pass, 2026-10-03. Continued the CURRENT saved scene in
place; no restart, new chunks, zones, enemies, bosses or loader changes.
This document supersedes the continuity review as the current visual handoff.

## Result and remaining limits

Lava now occupies six existing terrain features rather than appearing as thin
lines through empty cavities. Three scenery collapse families have exposed
intermediate ledges, asymmetric fault faces and slipping crust. The explicit
route strips are disabled, while rock shoulders, slopes, lava and openings guide
the current route. The existing flora progression gained branching takeover
lesions and restrained inner heat without replacing the four original species.

**This is an improved prototype, not a complete art or collision approval.**
Some collapse walls still look regular/quarry-like; several crust silhouettes
remain panel-like. Wide handoffs, outer ash fields and rounded ridge masses can
still look smooth or plain. Some invasive tendrils look like angular wires.
The heat-minimized overview reveals volcanic failure and layering, but the
outer terrain still does not establish unmistakable Emberfall identity without
orange. Stop for owner review; do not expand the kit or add zones.

## Open the saved result and evidence

- Current main: `E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview/EmberfallPrototype.blend`.
- Exact pre-pass rollback: same folder, `Input_LavaGeology.blend`.
- Renders: same folder, `LavaGeologyReview/`.
- Two comparisons: `lava_before_after_sheet.png` and `lava_geology_review_sheet.png`.
- Actual saved Blender readback: `lava_geology_technical_report.json` in this
  source folder and the render folder. Counts include retained hidden debug art.

| Evidence | Render filename |
|---|---|
| Matched lava-field before / after | before_lava_pool.png / after_lava_pool.png |
| Matched ravine before / after | before_lava_ravine.png / after_lava_ravine.png |
| Large collapse hole and integrated crust | after_lava_pool.png |
| Meso-scale shoulder / partly buried plates | after_meso_shelves.png |
| Broad playable COMBAT footing | after_stable_combat.png |
| Baseline player-eye seam | after_seam_player.png |
| Raised player-eye seam / adjacent scenery | after_raised_seam.png / after_raised_scenery.png |
| Route with explicit guides disabled | after_route_no_rails.png |
| Strong 50/50 conversion closeup | after_flora_midpoint.png |
| Charred tissue with restrained inner heat | after_flora_inner_heat.png |
| Temporarily minimized lava/plant heat and point lights | after_overall_glow_minimized.png |
| Restored normal overall atmosphere | after_overall.png |

## Preserved organization, origins and verticality

Five playable source collections remain: `chunk_entry_ash_plain` ENTRY,
`path_column_pass` PATH, `chunk_column_forest` COMBAT, `side_lava_overlook` SIDE,
`cap_collapsed_pass` CAP. The eight scenery collections remain ashland, basalt
ridge, high ridge, lava field, ravine, drained flora, charred flora and foothill.
No gameplay roles or spawns were added to scenery.

All thirteen source structure meshes retain origin (0,0,0) and XY footprint
[-128,128] × [-128,128], 256×256 studs. Blender XY is the footprint; Z is height.
Exact per-structure Z bounds are in the JSON. Original placement matrices and
all existing structural seam-band vertex coordinates remain exact, including
after local cavity subdivision. The band is 24 studs inward: |X| or |Y| ≥104.
Terrain detail is inland; border profiles were not displaced to hide seams.

| Role | Local entry → exit | Layout elevation / continuation |
|---|---|---|
| ENTRY | 0 → 0 | LEVEL_0, world Z0 |
| PATH | -28 → +28 | Origin Z28; world 0 →56, provisional +56 ascent |
| COMBAT | 0 →0 | LEVEL_1, world Z56 |
| SIDE | 0 →0 | Raised alternate branch, world Z56 |
| CAP | 0 →0 | Raised terminal; no outgoing descent |

Existing Architecture_A/B/C arrangements, source-only library and flora spectrum
review scene remain separate. New `_ContainedLava` children hold fill geometry.
`_REVIEW_DEBUG_SUPERSEDED` children retain obsolete guides/thin lava, with both
render and viewport disabled. **212 existing objects across source and layouts**
were moved there; they are marked non-production, not deleted. Atmosphere,
haze, sun/world mood and original useful basalt modules were preserved.

## Lava, collapse and surface integration

| Existing feature | Visible molten area, stud² | Form |
|---|---:|---|
| ENTRY | 42.99 | Small exposed peripheral pocket |
| PATH | 2,412.62 | Sloping flow channel below the route |
| COMBAT | 2,565.84 | Shallow peripheral pool |
| scenery_lava_field_a | 8,947.54 | Crusted basin, three islands |
| scenery_ravine_a | 5,711.17 | Stepped river, two islands |
| scenery_charred_flora_a | 3,135.91 | Reopened pocket, one island |

Molten tops are clipped to actual terrain intersections and close with contour
sides and an eight-stud buried bottom. Rock creates the cavity depth; lava
occupies the exposed bottom. The three scenery basins were reshaped into broad
rims, broken intermediate ledges and lower floors; lava levels expose those
ledges rather than covering the collapse structure. Selected fracture faces
are sharper; strata bands replace isolated face-color swatches.

Playable inland shoulders gained deliberate displaced/slumped planes, while
macro slopes and central routes remained intact. Existing crust components use
unequal torn sectors, buried rims, selective lifted lips and tilted overlap.
Most remain partly embedded; main-corridor lifts are restrained. No blanket
random ground displacement or increased micro-scatter was used. The largest
old ridge masses remain rounded and need visual direction before another pass.

The new contained-molten shader and localized bank lights are **Blender review
art**. Procedural material appearance and review-only light power have not been
converted into Roblox assets. No bake/export/upload or runtime lighting work.

## Footing, flora and cheap checks

PATH's outer eastern low channel was limited to approximately six studs below
its ramp, down from the previous seven. The previously broadened COMBAT basin
(~5 studs) and SIDE scoop (~3) were retained; ENTRY and CAP broad traversal
surfaces were retained. Existing central route vertices |X|≤28 compare exactly
against the pre-pass scene for all five assets; the COMBAT hub was protected.
Scenery basins are non-playable visual geometry, not optional route openings.

Forty-five targeted floor/normal samples (nine per playable asset) found max
sampled slopes ENTRY6.98°, PATH22.01°, COMBAT29.61°, SIDE23.23°, CAP31.20°.
These include approach/terminal slopes, not a cooked collision guarantee.
The COMBAT center samples are flat. Existing SIDE shelves, CAP slope, plate lips,
module undersides and access to scenery cavities still need owner Studio
walk/roll/combat/camera testing. Broad simplified hidden walk collision would
be appropriate under the central ash/ramp/combat surfaces and SIDE shelves;
visual cracks, lifted plate edges and scenery should not dictate foot collision.
No hidden collision or loader behavior was implemented in this art pass.

All four original flora mesh/material fingerprints compare exactly. Existing
derived 30/50/70% states gained short branching black lesions and fine heated
seams across surviving tissue. Curling, singed intermediate tissue and creeping
tendrils remain. 145 anchors were reseated to actual ground; 62 scenery placements
were shifted onto dry banks after the new fill, without adding plants/species.
The midpoint now reads more actively consumed, although some wire-like tendrils
and a broad side-to-side conversion silhouette remain visible up close.

The heat-minimized test temporarily disabled relevant emissions, darkened molten
surface color and disabled point lights. Material values, node links and light
energies were restored before the final saved scene; restoration asserted true.
Baseline, raised and raised-scenery player-eye renders show structural alignment
retained, without new hard cuts. Broad handoff composition remains a review item.

## Actual object and triangle changes

| Saved scene | Objects before →after | Meshes before →after | Triangles before →after |
|---|---:|---:|---:|
| Architecture_A | 777 →851 | 694 →731 | 677,632 →772,162 |
| Architecture_B | 744 →813 | 692 →737 | 715,704 →816,347 |
| Architecture_C | 739 →800 | 687 →724 | 673,448 →765,679 |
| Independent_Assets_LIBRARY_ONLY | 213 →226 | 206 →215 | 239,412 →263,760 |
| FloraSpectrum_REVIEW_ONLY | 22 →22 | 17 →17 | 9,772 →10,456 |

These are scene-instance totals including retained hidden/debug geometry, not
export budgets. Largest source mesh remains 4,076 triangles. Visible mesh counts
are A666/B673/C660/source184/gallery17. Saved global material datablocks: 28;
architecture uses22, source21. The total includes retained reference/unused
datablocks, not 28 production materials. Repeated flora/detail cost is not yet
approved for production. No src/loader files changed; existing runtime vertical
and scenery-fitting limitations described in ARCHITECTURE_REVIEW remain.

## Retained iterations and next review

Keep Input_LavaGeology, Input_Continuity, Input_ArtDirection, earlier architecture
inputs, independent baseline scenes, .blend1 recovery files and historical
reports/renders. Current main replaces their visual state, but exports/manifests
were not replaced. Debug guide geometry is retained solely for authoring history.
Recommend cleanup only after owner visual acceptance and applicable Studio/CI
replacement checks. Nothing was deleted. Next step is owner review of these
renders and movement concerns; no additional production work is authorized.
