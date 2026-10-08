# Emberfall — Area I Burned Plains foundation

Owner-directed design reset, 2026-10-05. **Visual foundation owner-approved.**
The subsequent isolated technical pass is documented in `MODULARITY_REVIEW.md`;
it does not supersede this approved visual direction.
Only Area I is authored. No later settlement, castle, source, boss, production
exports, Roblox content/runtime changes or Studio work.

## Source and authority

Read the current `docs/biomes/EMBERFALL.md` completely before authoring. Inspected
the refreshed folder: only `EMBERFALL_REFERENCE_01.png` remains, the approved
Burned Plains image. It governs composition; the low-poly game style governs
geometry. Its castle is not built in this pass.

Inspected and rendered the live `Emberfall_Foundation_Review` scene before work.
It had 534 objects, six playable shelf studies, eight scenery sources, basalt
archetypes, molten channels/vents and fortress compositions. Its macro terrain
and compositions conflict with the reset. It is technical/history input only.

Preserved that exact live state, including unsaved objects, as
`E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/Input_DesignReset.blend`.
The original `EmberfallFoundation.blend` is unchanged. No historical asset deleted.

## Rebuilt and reused

**Rebuilt:** all visible terrain, burn composition, surrounding fields, field
track, broadleaf trees, grass/stubble, fences, dry-stone wall, milestone, isolated
footing, fire fronts, smoke and two narrow interior heat seams.

**Reused:** source-only healthy/early/partial rosettes, with 22 separate review
instances recolored without modifying the source meshes/materials; technical
collection separation, metre/stud scale, centered origins, clean join sampling,
24-stud clear road mouths and the 56-stud ascent lesson. No basalt, lava, old
terrain or fortress asset enters the new visible scene.

**Preserved:** every old scene object/material, rocks, flora library, architecture,
smoke/heat studies and technical work in Input_DesignReset and original source.

## Completed representative compositions

Three independent 256×256 terrain objects assembled along +Y, with surrounding
continuous grassland extending past every outward edge:

| Study | Green | Stressed | Charred | Story |
|---|---:|---:|---:|---|
| Opening edge | 50.66% | 42.04% | 7.30% | Surviving field, flowers, wall, intact fence; arriving west burn tongue |
| Active-burn mid-plains | 5.98% | 44.51% | 49.51% | Road crosses irregular burn front; damp drainage remnant; damaged fences/trees |
| Interior edge | 0% | 6.59% | 93.41% | Black stubble, smoking trunks, field gate and isolated footing; two uncommon seams |
| Combined three studies | 18.88% | 31.05% | 50.07% | Composition target across the sequence, not per-piece quotas |
| Entire land, including scenery | 18.42% | 30.57% | 51.01% | Heat-dried windward outer fields prevent a lush scenery apron |

These are **planar terrain surface classifications**, not a pixel-coverage
measurement or exact accounting for tree crowns, roads and occlusion. Judge the
actual views as well. The opening intentionally contains more green than the run.

## Burn direction and terrain

Player travels +Y into the destruction; invasion/fire spreads toward -Y/entry.
A coherent curved front and west advance tongue create recognizable transitions.
Flames are sampled on the actual dry/char interface, with a broad gap at the road.
Surviving pockets have reasons: sheltered stone-wall field, drainage low, and land
ahead of the burn. Offshore/random lava-like patches are absent.

Broad hills, shallow drainage and road slopes supply verticality. Fire changes
grass condition on the same landforms; it does not create rock shelves. Destroyed
land has visible black grass stubble and burned soil. The track itself darkens
through stressed/charred ground. Trees include green, one-sided scorch, partially
defoliated and blackened skeletons; one deeper tree site burns sparingly.

No molten pools, calderas, plate crust, basalt pillars or volcanic cliff chain.
Only two 0.2-stud-wide short supernatural seams occur toward the interior.
Field gate/footing suggest maintained land ahead without building Area II.

## Visual anti-drift evaluation

Assessment of final actual renders, **not owner acceptance**:

| Question | Result / evidence |
|---|---|
| 1. Formerly vivid grassland? | Yes: rolling meadows, broadleaf trees, grass blades, flowers and maintained fields |
| 2. Fire happening now? | Yes: active fronts, smoke, partial scorch and fresh stubble; static review effects |
| 3. Green visible and subordinate? | Yes across composition: 18% whole land; opening intentionally richer |
| 4. Advancing destruction understandable? | Yes: entry → stressed/front → char; raised/top views show direction |
| 5. Rolling forms over volcanic shelves? | Yes: fresh hill/drainage foundation, no inherited shelf geometry |
| 6. Read survives removing orange? | Yes: matched raised no-fire/no-seam diagnostic retains damage, smoke and fields |
| 7. Previous landscape understandable? | Yes: living/scorched tree contrast, flowers, fences, wall, track and milestone |
| 8. Avoids desert? | **Yes:** grass and stubble across land, temperate trees and field organization; no dunes/sand |
| 9. Avoids generic volcanic wasteland? | **Yes:** no volcanic geology/lava; countryside forms and remnants carry identity |
| 10. Room for later escalation? | Yes: no major architecture, large fissures, molten features or extreme source geology |

## Evidence

Scene: [BurnedPlains.blend](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend).
Opened in live Blender for owner review.

Contact sheet: [eight views](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/burned_plains_contact_sheet.png).

- [Broad overview](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/01_broad_overview.png)
- [Top progression](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/02_top_progression.png)
- [Baseline eye, 5 studs above road](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/03_baseline_player_eye.png)
- [Opening edge](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/04_opening_edge.png)
- [Mid-plains active burn](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/05_mid_plains_active_burn.png)
- [Interior edge](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/06_interior_edge.png)
- [Raised gradient](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/07_raised_gradient.png)
- [Same raised view, fire/seams hidden](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/08_glow_removed.png)
- [Old live scene before reset](E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/before.png)

## Validation and technical limits

Shared protected Blender launcher passed with a normal user token after restricted
profile refusal. Cheap saved readback: three closed terrain meshes, each 8,958
triangles and 256×256 footprint, exact ground-center origins. Two joins checked
at 65 stations each: maximum gap 0.000000954 stud. Overall road ascent 56 studs.
All eight render files exist; no old geology/later-area object in the new scene.
Python/JSON syntax and generated index checked. Report: `burned_plains_report.json`.

Scene has 940 objects / 650,196 mesh triangles including extensive surrounding
fields, grass batches and hidden source flora. This is review geometry. Large
grass/scenery meshes need future production decomposition; only the three
representative terrain meshes meet the per-exported-mesh ceiling currently.

Authored joins in this layout are preserved. This does **not** claim arbitrary
yaw/pair compatibility, production socket schema, collision, runtime boundaries
or traversal validation. The inherited invisible-boundary contract remains
required later. No technical requirement was removed to obtain the art result.

## Remaining Area I issues and stopping point

- Owner has accepted proportions, landforms and progression. Production modularity
  remains separate; see `MODULARITY_REVIEW.md` for the bounded continuity proof.
- Tree crowns/grass blades and flame tongues are deliberately simple; smoke is a
  static procedural volume study, not runtime VFX or animation.
- Surface-state boundaries remain visibly faceted in overhead views; the interior
  can use more localized damage/story detail after the foundation is accepted.
- Field gate is only a hint; no later-area architecture is authored.
- Lighting is provisional; production separation, collision and Studio work wait.

Keep Emberfall_Prototype, Emberfall_ArchitectureReview, Emberfall_FoundationReview,
their Input_* rollbacks, historical generators/review documents and the new exact
Input_DesignReset. They are superseded as **Area I visual authority**, not deleted
or technically replaced. Consider retirement only after owner acceptance, later
Studio/CI replacement checks and reference checks; no exports/manifest rows were
replaced in this pass. Stop here for Area I owner review.
