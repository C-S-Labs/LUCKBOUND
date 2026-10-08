# Burned Plains production-readiness gate — 2026-10-05

**Subsequent geometry gate:** [EDGE_PROFILE_REVIEW.md](EDGE_PROFILE_REVIEW.md)
resolves this report's sole blocker with frozen authored profiles, alternate
neighbours, quarter rotations and matching cooked collision. The original NO-GO
and layout-specific corrections below remain historical evidence. Stop for owner
review before production authoring; accepted appearance/route decisions are unchanged.

**Result: NO-GO for expanding the production kit.** Appearance, returning-route
progression and transformed state alignment pass this bounded gate. The remaining
blocker is the **authored edge-profile/collision contract at rising turns**.
The new study closes its edges by changing geometry for this particular layout;
it does not prove those same exported pieces join different neighbours unchanged.
This is concrete geometry evidence, not a reopening of the approved art direction.

Owner-approved foundation and modularity evidence remain the visual baseline.
Diagnostic overhead bands are non-blocking polish unless reachable cameras expose
a chunk boundary. No production systems, content entries, manifests or IDs changed.

## Appearance backend

The selected candidate is **one-time, assembly-derived vertex recolouring on
client-owned fixed-size EditableMesh visuals**, with authoritative authored geometry
and collision retained separately. No per-frame field updates, runtime landscape
generation, or distinct uploaded mesh for every burn-state/layout combination.

Actual pipeline evidence:

| Stage | Result |
|---|---|
| Blender disposable export copy | Prototype FLOAT/POINT attribute converted to active `Col`, BYTE_COLOR/CORNER; existing legacy FBX settings, SRGB, -Z/Y, Apply Transform |
| FBX reimport | All 25,856 corners matched; zero packed-colour channel error; 8,958 triangles; 226,524-byte file |
| Studio import | Colours visibly present in preview; 256 × 56.40654 × 256 MeshPart; 23,812 imported vertices and 23,812 colour attributes |
| Edit API | Fixed-size attribute recolouring works; byte-calibrated error <0.000001; CreateMeshPartAsync from EditableMesh works |
| Actual server AssetPreparation → ChunkLoader | Scratch manifest/definition supplied through existing arguments; real modules unchanged; uploaded colours retained; 90° layout gives -90° Roblox orientation |
| Play client | Five independent fixed-size copies allocated, recoloured and made renderable; 0/90/180/270/0 orientations; ~0.582 seconds total on this desktop, cached copies ~0.066 seconds each |

Studio initially refused Play-client EditableMesh access. Owner enabled the Mesh /
Image API setting; the subsequent test passed. Edit/plugin success alone would
have been misleading. The imported MeshPart and current loader both retain a grey
default `Color` (~0.64): appearance visuals must explicitly use white to avoid
multiplying/darkening vertex colours. Do not change collision templates to solve tint.

Imported colours are sRGB/byte values, not arbitrary Blender node graphs. Export
bakes the initial colour data; runtime can replace those attributes once after
assembly. This is not a custom world-space shader on an ordinary MeshPart.
The probe already has a distinct colour attribute per imported vertex, so fixed-size
editing is sufficient here. Check this invariant on final exports; shared colour
IDs must not recolour unrelated regions. Different topology/import consolidation
may require a disposable non-fixed initialization followed by a fixed-size copy.

One uploaded mesh per authored terrain piece remains reusable. Each simultaneously
visible placement with a different field needs its own editable visual data;
mutating a canonical cached template or sharing one editable object between those
placements would couple their colours. Five visuals add five MeshParts and five
EditableMesh objects, not one Part per vertex. The probe's flat-normal import expands
vertices significantly; the five-copy test has 119,060 vertices/colour attributes
and 44,790 triangles. Colour bytes alone are ~0.45 MiB; this is **not** total engine
memory (positions, normals, UVs, indices, upload buffers and object overhead also cost).
No trustworthy per-allocation memory measurement or mobile benchmark was obtained.
The Python reference field uses 162,440 bytes of float64 grid storage; a runtime
implementation need not transmit that grid if clients reconstruct deterministic
parameters. Total Studio process memory is not a valid editable-mesh cost estimate.

Use a bounded active/streamed working set and teardown on expedition removal.
Allocation failure must be handled explicitly and measured on target devices.
Mesh API enablement, asset ownership/permission and account eligibility are deployment
requirements. This local desktop probe is not published-server or mobile certification.
Roblox documents restricted client memory and permissions:
[EditableMesh](https://create.roblox.com/docs/reference/engine/classes/EditableMesh),
[importer vertex colours](https://create.roblox.com/docs/studio/importer).

Fallback ranking for this approved appearance (1 = best fit; ratings are qualitative):

| Rank / backend | Fidelity / seams / rotation | Authoring / runtime / memory | Reliability / maintenance |
|---|---|---|---|
| 1. Fixed-size per-placement vertex colours | High / high / high | Low ongoing authoring / one-time cost / editable memory budget | Verified bounded pipeline; permissions and mobile limits need deployment checks |
| 2. Prebaked finite assembled layouts or matched state variants | High within supported layouts / conditional / explicit variants | More authoring and uploads / cheap runtime / more cached asset data | Very reliable ordinary meshes; variant and seam coverage grow quickly |
| 3. Continuous assembly surface overlay with ordinary meshes | Potentially high / high / high | Additional surface authoring / draw cost and z-fighting / duplicated surface | Needs export/runtime proof; retain collision and preserve hills |
| 4. Texture masks / EditableImage | High potential / conditional on UV continuity / transformable | UV work / texture generation / strict image budget | Not tested here; more moving parts than the proven colour path |
| 5. Whole-MeshPart tint plus dressing | Low / poor broad-state transitions / easy rotation | Easy / cheap / low | Reliable API, but inadequate replacement for the approved field |

Prebaked variants are the fallback if editable budgets/permissions fail, **not** an
automatic degradation to obvious squares. Their connected layout coverage must be
proved before acceptance. No fallback was implemented or substituted for approved art.

## Returning route and burn field

Five 256-square pieces in a U/return layout: straight opening, elbow, straight,
elbow, straight interior. Layout yaws **0/0/90/90/180**. Existing ChunkCore helpers
place four matching socket pairs with elevation; all ten footprint pairs are
non-overlapping. The elbows are isolated test guide adaptations, not new kit content.
This repeated study climbs ~110 studs; it does not revise the approved area's
56-stud ascent design. Standard content must be authored to the intended run budget.

The reference field derives depth from cumulative distance along **ordered,
transformed authored road guides through consumed sockets**. A deterministic pinned
grid/harmonic extension provides a single continuous field between those guides;
irregular front modulation and transformed authored refuges modify surface severity.
Final queries use one bilinear field, not nearest-route-segment selection that can
jump between adjacent legs. The route is ~1,174.77 studs long. Midpoint depths:
0.117, 0.305, 0.500, 0.695, 0.883; entry ~0.0017, exit ~0.9983; no local backstep.
The exit returns to the entry's world Z without returning to healthy countryside.

Playable surface balance: **18.88% green / 31.05% stressed / 50.07% charred**.
This is an aggregate composition measure, never a per-chunk quota. The active
front crosses a join rather than resetting on each square. Refuge masks may lower
local severity intentionally; they do not change route depth.

Current production Layout has no consumed-connection graph or guide/depth metadata.
Layout Index alone is not a universal route-distance substitute (branches, attached
rooms and backdrops differ). Future main routes need explicit ordered connections;
branches need a deliberate graph-depth rule rooted at their parent connection.
Branch semantics are not tested by this five-piece main-path proof. World-axis or
Euclidean distance from entry must never determine depth.

## Vegetation and local composition

Previously, some meshes encode positions in their vertices while object origins
remain at zero; sampling origins misclassified them. Baked tree populations and
world-fixed refuges also did not move together after rotation. This gate uses
explicit local root/prop anchors and local refuge frames transformed by the same
placement matrix. Terrain, grass, timber state and tree variants sample one final
field. Every tree's trunk and canopy share its root decision; individual canopy
parts do not independently sample unrelated ground positions.

Twenty-three authored tree anchors retain their locations. Healthy/stressed/singed/
fresh-char/skeletal variants alter existing branch/crown composition. No healthy
tree is selected on charred ground. The rotated drainage refuge and its underlying
terrain share the same transform. Root-protection for a hero tree is an explicit
local refuge affecting both ground and tree, not a forced green tree on black soil.
Optional overrides must specify their reason and whether they affect the shared
local refuge, or intentionally represent a recently damaged prop. They do not
permit arbitrary inconsistent populations. The experiment also flushes/bakes
source-library TRS before copying crowns; hidden library evaluation cannot be
assumed. Existing landmarks and 755 local remnant objects are retained copies,
not a production instance budget or procedural scattering prescription.

## Road and scenery

Hybrid recommendation confirmed for bending routes: chunks author socket mouths,
guide curves, clearance and local roadside compositions; assembly joins guides
into continuous presentation and longitudinal texture distance. The review strip
uses 321 samples, 7.4–9.4 stud width, and maximum sampled slope ~0.207. Both elbows
use authored curves; sockets meet without texture/mesh resets. This continuous
Blender object is evidence, not a ready runtime spline implementation. Production
may use bounded joined strips or segments with common end frames and shared UV
distance. Do not warp trees/walls arbitrarily to fit an automatically chosen road;
real turn chunks must author appropriate roadside composition and usable geometry.

Standard playable pieces remain **256 × 256**. `interior_continuation` remains
**256 × 360 non-playable scenery**, no sockets; it must not masquerade as a route
piece. Other non-playable continuation may be larger, explicitly visual-only and
non-collidable. Existing BACKDROP supports zero sockets/larger bounds but is a
budgeted placement mechanism, not an automatic terrain-edge fitter. Special arena/
transition footprints require explicit future generation/loader support and owner
approval. Invisible safety boundaries and verified collision remain mandatory.

## Seams, collars and the remaining blocker

Four joins, 65 stations each: maximum height gap **0.000001772 stud** after the
experimental correction. One shared field prevents per-chunk material resets.
Normal-eye, 12-stud raised and reachable-ridge renders show usable continuous
countryside/road; no exposed crack or square material reset was identified in these
sampled views. The ridge view is partly occluded by its crest, so it does not
certify every elevated camera. Diagnostic overhead slope/density bands remain
non-blocking polish under the owner's rule; full kit authoring must apply the same
reachable-camera acceptance check, rather than chase perfect orthographic views.

**24 studs is an experimental blending region, not a visible standardized collar.**
Socket mouths retain their level 24-stud opening. Full-edge flat strips fail at a
turn where adjacent entry/exit edges have different socket elevations: their shared
corner cannot equal two heights. The test instead computes shared corner/edge
profiles from the assembled neighbours and bakes them into its disposable meshes.
Saved readback measures maximum source-shape adjustments of ~8.99, 9.17, **17.98**,
9.17 and **17.98** studs across the five pieces (includes the elbow corridor changes).
This is considerably larger than the prior straight proof's ~2.4-stud collar fix.

Therefore do **not** propagate that layout-dependent height operation as a silent
visual-only runtime effect. It would violate authored geometry ownership and can
put the visible ground well away from collision. Full non-socket edges are not
guaranteed interchangeable merely because socket Kind/position matches.

Smallest next resolution: author an explicit fixed edge-profile family for a
representative rising turn and compatible straights; freeze their terrain and
matching collision, then assemble the same meshes against at least two valid
neighbour/rotation combinations **without reshaping their vertices**. Socket
mouths remain level. If full-edge compatibility constrains selection, encode the
exact compatibility in content/socket kinds or a reviewed generic schema; do not
invent an Emberfall-only loader exception. Alternatively propose a bounded
connective surface with matching collision and prove it separately. Neither option
is approved production behavior by this report. No kit expansion before this test.

## Proposed repository changes — review-gated, not implemented

- `ChunkCore`/`ChunkKitCore`, Types/Schema, expedition layout manifest: preserve
  consumed connections, authored guides and deterministic depth/refuge metadata;
  optional generic continuity contract with content data, not a world-ID branch.
- `AssetPreparation`/`ChunkLoader`/client visual lifecycle: keep canonical assets
  immutable; prepare placement-specific non-collidable editable visuals, white tint,
  allocation/error handling and cancellation/teardown. Reuse existing networking.
- `PropCore`/`PropController`, solid prop presentation: explicit authored anchors,
  state variants and compatible override/refuge data sampled from the same field.
- World/chunk/prop content and manifest/export tooling: declared edge compatibility,
  guide/anchor metadata, Col export invariant and explicit scenery classification.
  Add reserved declarations to RESERVED only when actually introduced.
- `GameConfig`: eventual appearance working-set, initialization and dressing budgets.

These are proposals, not evidence that production already supports the field.
The ordinary imported-colour/cache/loader route was tested; production assembly
recolour integration has not been implemented. No new remotes or reserved fields.

## Evidence, validation and repository state

External review folder:
`E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview/`

- `BurnedPlainsProductionGate.blend`: isolated five-piece return scene plus preserved
  original scenes; not production assets.
- `Input_ApprovedLive.blend`: exact copy of the dirty approved live session, original
  filepath/scene retained. Approved BurnedPlains and modularity files also hash-identical.
- `01_return_route_overview.png`, `02_route_depth_top.png`, `03_player_eye_bend.png`,
  `04_raised_gameplay.png`, `05_reachable_ridge.png`, `06_return_interior_eye.png`.
- `production_gate_contact_sheet.jpg`, `return_layout.json`, probe-only
  `probe_export/colour_probe.fbx`; reports mirrored with repository JSON.

`production_gate_layout.py` exercises actual ChunkCore; `production_gate_study.py`
builds/export-probes/renders only this experiment; `production_gate_readback.py`
measures saved changes; `production_gate_evidence.py` prepares the sheet.
`production_gate_studio_probe.luau` preserves the bounded API check.
Studio's import preview was visually inspected with Computer Use. The dedicated
screen_capture tool did not complete; Studio results are in
`production_gate_studio_report.json`, rather than claiming a saved Studio screenshot.
Studio is left in Edit mode with `Workspace.EmberfallProductionGateAppearance` for
review; Play-only/cache/loader test objects vanish on stop. No place publish/save.

Cheap checks: Python syntax, JSON parse, actual socket/yaw/overlap, aggregate balance,
four height joins, returning-depth monotonicity, transformed tree/root classification,
saved shape deltas, FBX roundtrip, actual Studio importer/cache/loader and five-copy
Play-client API probe, evidence existence and index freshness. No broad traversal,
collision sweep, full export or regression campaign. New production collision is
not validated, and that is part of the stated blocker.

Changes comprise isolated gate sources/reports, owning design, modularity review
addendum, export/modularity/build-spec addenda, STATUS/WORKLOG and INDEX/INDEX_MAP.
All existing owner changes are preserved. Branch `agent/emberfall-burned-plains`;
left uncommitted because the checkout includes mixed owner/prior-session design,
reference changes. No push/PR/merge/main work.

Keep approved inputs, prior proof, exact live checkpoints and current experiment.
No production assets, exports or manifest entries replaced. Retire experimental
gate outputs only after the static-profile solution passes owner visual/Studio and
applicable CI checks; older approved studies remain recovery/authority inputs.

**NO-GO — reusable authored rising-turn edge profiles and matching collision remain
unproved without layout-specific terrain reshaping.**
