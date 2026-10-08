# Emberfall — continuity, footing and active-takeover refinement

**Historical snapshot:** the current saved scene now includes the 2026-10-03
contained-lava and terrain-language pass. See `LAVA_GEOLOGY_REVIEW.md` and its
actual saved-data report for the current result and remaining review items.

Owner-directed focused pass, 2026-10-02. **Same current saved scene**, edited from
the identity revision, not regenerated from an earlier input. Five playable and
eight scenery assets, A/B/C layouts, mood, haze, 56-stud ascent and flora spectrum
retained. No new chunks, systems, export, upload, publishing, commit or push.

## Result for owner review

**Improved, but not a complete visual pass.** The old contrasting empty perimeter
gutters are reduced by continuous surface tint and restrained edge detail. Some
broad handoffs still feel too plain at player height; sparse low-relief details
do not fully carry the larger terrain composition across every join. Do not label
the dead-band goal completely solved.

The mixed plants now show a brown, irregular singe front, sagging/curling tissue,
invasive black tendrils and dim ember hairlines emerging through the old plant.
The 50/50 closeup communicates active takeover more clearly than the previous
two-color split. Some tendrils remain angular/wire-like, particularly close up.

Collapse rims have asymmetric fault steps and broken/slipping shelf remnants.
**Deep walls still look too smooth in places**, and several crust inserts still
read as broad polygon panels. Those are remaining review items, not a claimed
natural-geology pass. Stop here for the owner; no content expansion.

## Open the result

- Current scene: `E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview/EmberfallPrototype.blend`.
- Current evidence: `Emberfall_ArchitectureReview/ContinuityReview/`.
- `continuity_review_sheet.png`: overview, baseline and raised player joins,
  scenery join, oblique seam, top seam, elevated lookback, playable lows,
  collapse, crust and flora progression.
- `flora_50_close.png`: actual placed PATH midpoint plant, clearly framed.
- `flora_50_gallery.png`: isolated midpoint in the existing spectrum scene.
- `continuity_technical_report.json`: actual saved Blender readback, per-asset
  mesh/collection counts, origins/bounds/elevation metadata and targeted low-area
  samples. Matching repo/external copies.

## Terrain continuity

- Removed the old surface-color fade-to-dark perimeter gutter. Independent assets
  use rotation-compatible opposing border colors. Existing A/B/C terrain copies
  use continuous world-space ash/crust weathering; their geometry remains exact.
  This color fitting is an offline review operation, not runtime scenery code.
- Paired shallow ash/crust surface strips reach each edge and continue inward
  over 64 studs. Matching edge stations, controlled curvature, no random noise.
  Initial bright strips were rejected in review as repetitive strokes; final
  strips blend closely with ground color. Small off-mouth fragments and four
  sparse handoff plants per asset carry light detail toward the boundary.
- Original structural 24-stud seam-band vertices remain **exactly unchanged**.
  No edge humps, sinks, skirts or added tile walls. Border surface detail is marked
  nonsolid; strips have 0.055-stud edge lift, inset fragments 0.08–0.17 stud.
  Their geometry is cut at the border, not baked across two asset collections.
- The shared pattern repeats and some open areas still feel bland. The review
  is strongest for surface continuity, weaker for broad cross-border geology.

## Playable low areas — revised and retained

| Asset | Revision / reason |
|---|---|
| ENTRY `chunk_entry_ash_plain` | Retained broad open ash apron; no negative authored pocket needing fill. |
| PATH `path_column_pass` | Replaced eastern narrow ~21-stud cut with broad ~7-stud sloped channel. Preserves readable hot-cut identity and ascent without a deep peripheral foot trap. |
| COMBAT `chunk_column_forest` | Replaced western ~19-stud bowl with broad ~5-stud peripheral basin; central fighting surface retained. |
| SIDE `side_lava_overlook` | Reduced small southeast ~12-stud pocket to broad ~3-stud scoop, while retaining raised overlook flow. |
| CAP `cap_collapsed_pass` | Retained broad raised terminal shelf; no negative authored pocket requiring fill. |

Numbers describe the negative relief component relative to the local route field,
not every structure vertex or the total blended elevation. Nearby positive shelf
relief remains. Existing props/modules were reseated with the local terrain change.

Cheap **9-point surface samples per revised low area**, not traversal simulation:
PATH minimum relative route height -6.94 studs, steepest sampled face 28.17°;
COMBAT -4.94 studs, 13.30°; SIDE samples remain on its positive shelf (minimum
+7.66 studs), 35.85°. SIDE's samples do not establish every pocket's safety.
The retained ascent's broad route is unchanged; this checks three local repairs.

**Collision remains unproven.** These are visual terrain edits, not cooked Roblox
colliders. Studio walk/roll/combat-camera tests must check channel shoulders,
SIDE's steeper shelf, lifted inland crust lips, rubble/module undersides, and
access to deep scenery voids. Border detail and new collapse remnants are
explicitly nonsolid. No exhaustive raycast sweeps or automated character tests.

## Collapse and crust

- Edited the existing lava-field, ravine and charred-flora depressions with
  deliberate asymmetric fault sectors; retained their broad negative-space shape
  and inland depth. All changes fade out before the protected seam band.
- Added partial rim shelves and slumped fragments on alternating sides, with
  uneven ledge angles and restrained strata faces. Corrected overly tall remnants
  after the first review; new ledge top height is capped at 2.2 studs above its
  supporting terrain. Deep geometry remains non-playable scenery.
- Existing crust objects retained: partially buried rims, lower lift, unequal
  corner notches, less uniform colored bevel outlining and irregular upper
  fracture facets. Inland tearing lips remain higher than flush border detail.
- Remaining weaknesses: several six-sided parent outlines and wide smooth pit
  walls still expose the procedural construction. Large ridge/mound forms also
  remain smooth. No attempt to hide these with another density pass.

## Flora process

- Original four source species and material fingerprints **exact**. Surviving
  and drained states preserved. Existing derived 30/50/70% and shrub midpoint
  meshes refined, updating their already placed linked instances.
- Support topology inside existing leaves allows an irregular creeping boundary
  within a leaf rather than a clean per-leaf material split. Pale tissue blends
  through singed brown into carbonized tissue; affected tips sag/curl unequally.
- Thick black tendrils overlay old tissue, branch into thorns and expose dim warm
  hairlines underneath. Small heated core seams emerge from inside the plant.
  No point-light or global atmosphere increase, particles or animated flames.
- Charred rose and thorn-pod **placements** use active-tissue derivatives;
  original source species remain untouched. Redundant planar support subdivisions
  on those derivatives were dissolved after review.
- Spectrum gallery and actual planted closeups updated. The state percentages
  remain art targets, not a measured biological area after curling/tendrils.

## Actual saved data

All thirteen source terrain footprints remain **256×256** at **(0,0,0)**.
Original placement-empty matrices and seam-band coordinates match the input
exactly. Sockets/roles remain unchanged; PATH local entry -28, exit +28, delta
+56; world entry 0, exit 56. COMBAT/SIDE/CAP remain at world LEVEL_1 = 56.
CAP is a terminal raised continuation; no outgoing/descent socket was added.

Global materials: **21 → 23** after saved readback (creeping tissue, restrained tissue heat, blended
border surface). Saved scene counts include repeated flora and review haze,
horizon, lights/cameras; source library includes original and derivative props.

| Scene | Objects | Meshes | Triangles |
|---|---:|---:|---:|
| Architecture_A | 777 | 694 | 677,632 |
| Architecture_B | 744 | 692 | 715,704 |
| Architecture_C | 739 | 687 | 673,448 |
| Independent_Assets_LIBRARY_ONLY | 213 | 206 | 239,412 |
| FloraSpectrum_REVIEW_ONLY | 22 | 17 | 9,772 |

Largest individual source mesh: **4,076 triangles**. Total density is substantially
higher than the previous 195–202k-triangle review layouts; these repeated linked
plants are **not accepted production performance**. No optimization rollout or
new collision/schema work was included in this focused visual pass.

Existing source collections remain intact. Additions live under each asset's
`_BorderFlow`; three collapse families also have `_CollapseRemnants`. Existing
`_SurfaceIdentity`, `_FloraProgression`, structure/prop collections and review
layout groups remain. `Flora_Takeover_States` contains active derivatives;
review layouts remain separate from independent assets. Full collection/mesh
lists are recorded in the actual report.

Protected Blender launch, saved readback, source bounds/origins, original flora,
edge/transforms invariants, targeted floor/normal samples, Python parse, expected
render outputs and index/diff sanity checked. No game/runtime changes or Studio
physics tests. Existing generic loader limitations from ARCHITECTURE_REVIEW.md
remain unchanged; this art pass does not resolve vertical socket probing,
flat blockout, XZ-only overlap or scenery profile placement.

## Retained inputs and cleanup

`Input_Continuity.blend` is the exact pre-pass current scene. Keep it, earlier
Input_ArtDirection/Input_FirstPass, `.blend1`, identity/architecture images and
reports, and the thirteen architecture-baseline isolated scenes. None are current
art exports; no production files/manifests were superseded. Remove redundant
review iterations only after owner visual acceptance and applicable Studio/CI
checks prove replacement safe. Those gates are pending, so keep them now.

The new script is a **one-pass saved-scene editor**, not a rebuild recipe. Its
`--review-only` / `--extra-review` modes only render; mutation stages must not be
repeated on already refined art. Do not run earlier architecture generators over
the current scene. Stop after this refinement.
