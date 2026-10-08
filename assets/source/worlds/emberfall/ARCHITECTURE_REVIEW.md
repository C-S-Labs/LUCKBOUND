# Emberfall — seam, scenery and persistent-elevation prototype

**Architecture baseline:** the same main scene now includes the later saved-source
art pass described in [IDENTITY_REVIEW.md](IDENTITY_REVIEW.md). Counts, dimensions and
images below describe the pre-art baseline; its seam/route architecture remains.
The separately saved thirteen chunk scenes remain baseline snapshots. The newer
identity pass stops for owner review because the heat-dark overview still looks too generic.

Owner-directed 2026-10-02. **Review prototype only.** Exactly five playable assets
and eight scenery assets; no full-kit expansion, runtime changes, exports, uploads,
publication, commit or push. The current `docs/biomes/EMBERFALL.md` remains authoritative
and was not edited. Original chunk names are retained even where geology changed.

## Open and review

- Main: `E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview/EmberfallPrototype.blend`.
- Select scene **Architecture_A**, **Architecture_B**, or **Architecture_C** to compare
  the same five-piece route with different seeded scenery selections/quarter turns.
- **Independent_Assets_LIBRARY_ONLY** contains the centered source assets. Thirteen
  independently openable `.blend` files, named exactly below, are beside the main file.
- `architecture_review_sheet.png`: layouts, top/side, player-height and elevated views.
- `player_eye_seams_sheet.png`: all **16 unique playable boundaries** in arrangement A.
- `scenery_library_sheet.png`: all eight independent scenery assets. Their isolated
  open perimeters are authoring boundaries, not the assembled world's visible edges.
- Actual data: `architecture_technical_report.json`, `architecture_saved_verification.json`,
  and `architecture_visual_coverage.json` beside this document; external reports/images
  accompany the saved scenes. Reports distinguish source assets from fitted review copies.

## What was preserved and rebuilt

Read the existing saved scene rather than rerunning the original generator. Four original
flora meshes have identical before/after geometry/material fingerprints: drained wax
rosette, drained seed shrub, charred ember rose and charred thorn pod. Original materials,
linked flora use, sparse rubble, the glassy overlook cairn, five names/roles and mouth
selection remain. **18 original basalt modules** survive (2/6/4/2/4 by role).

Replaced the old terrain foundations and their closed skirts. Removed the edge rises,
sinks and border-flattening mouth patches. Geology now includes an open ash shelf, a broad
cooled-flow ascent, fractured terraces, a raised combat shelf with a sunken side ravine,
an overlook and an inland collapsed shelf. Supporting topology shapes larger cooled-flow
rock masses; retained columns are accents except in the signature ascent corridor.
Weathering uses smoothly interpolated vertex colors instead of rectangular face-material
patches. Plants are reseated to the new ground and placed near cool shelves/hot recesses.

## Actual Blender readback

Blender **5.2.2 LTS**, metric scale **1.0**. Dimensions are Blender **X × Y × Z**,
where Z is height; Roblox uses X × height × depth. All structural footprints are
**256 × 256**, with structural mesh origins **(0,0,0)** and applied identity transforms.
Playable origins are at the center walk datum. Scenery origins use the centered **seam
datum**; a non-walkable ridge summit is not its origin. Counts include linked prop instances.

| Playable asset / role | Objects / meshes | Structure tris | All mesh tris | Structure height | Mouths |
|---|---:|---:|---:|---:|---|
| `chunk_entry_ash_plain` / ENTRY | 7 / 6 | 2,804 | 4,424 | 34.025 | N |
| `path_column_pass` / PATH | 9 / 6 | 4,076 | 7,288 | 136.174 | S, N |
| `chunk_column_forest` / COMBAT | 8 / 7 | 3,508 | 7,094 | 51.900 | S, N, E |
| `side_lava_overlook` / SIDE | 7 / 6 | 3,016 | 5,592 | 33.522 | W |
| `cap_collapsed_pass` / CAP | 6 / 5 | 3,376 | 6,502 | 70.263 | S |

| Non-playable scenery asset | Objects / meshes | All tris | Terrain height range |
|---|---:|---:|---:|
| `scenery_ashland_a` | 1 / 1 | 854 | 8.937 |
| `scenery_basalt_ridge_a` | 3 / 3 | 1,278 | 63.057 |
| `scenery_basalt_ridge_high` | 3 / 3 | 1,278 | 105.066 |
| `scenery_lava_field_a` | 3 / 3 | 1,074 | 42.999 |
| `scenery_ravine_a` | 2 / 2 | 862 | 71.395 |
| `scenery_drained_flora_a` | 3 / 3 | 1,854 | 16.324 |
| `scenery_charred_flora_a` | 3 / 3 | 2,636 | 43.195 |
| `scenery_foothill_a` | 3 / 3 | 1,278 | 56.037 |

Every scenery asset is cheaper than every playable asset. Scenery has **no gameplay
role, sockets, enemy spawns or gameplay-route markings**. Low ash, tall ridges, molten
lowland, deep ravine, both flora families and a broad foothill are represented.
Collision is not finalized; reachable scenery margins must receive safe collision or
believable access restrictions during Studio integration.

Each playable collection retains **Structure**, **Props_Solid**, and **Props_NonSolid**
children. Each scenery asset has **Structure** and **Props_NonSolid** children. `PropLibrary`
retains all four reusable flora originals. Each review scene has a `ReviewLayout_*_ONLY`
root, with `Playable_5`, `Scenery_instances_REVIEW_ONLY`, `Distant_ring_REVIEW_ONLY` and
`Cameras_Lights_REVIEW_ONLY`. Geometry is never baked back into the independent assets.

Actual saved arrangement counts, including cameras, lights, haze and horizon pieces:

| Scene | Objects | Meshes | Triangles |
|---|---:|---:|---:|
| Architecture_A | 238 | 173 | 94,562 |
| Architecture_B | 220 | 168 | 98,180 |
| Architecture_C | 216 | 164 | 92,446 |

Each uses **19 local** and **24 distant** scenery instances, drawn from the eight assets.
Separate cheap perimeter extensions continue the second ring into a broken mountain
silhouette. These and finite cool haze are review-only; no single fixed backdrop plate.

## Seam implementation and findings

The initial band is **24 studs inward** from all four terrain edges. Interior geology
has zero influence within that band; it blends in from 24–52 studs inward. There are
no border skirts, bottom caps, noise at the border, or seam-cover props. The common
`LOW_ROLL_4` profile has a **56-stud flat mouth** and intentional shoulders up to four
studs near the corners. Profiles have controlled tangent slopes and quarter-turn symmetry.

The ascent's north/south borders are the same profile at local +28/-28. Its side borders
use **RAMP_56_LOW_ROLL_4**, continuing the broad route slope along the edge. Review scenery
beside that transition uses a deterministic elevation fit, not random terrain displacement.
The band carries that intentional grade; it does not add a seam-hiding hill.

An initial visual pass caught two problems and corrected them: hard rectangular ash
material patches, and hairline cracks caused by coarse scenery edge interpolation.
Scenery interiors remain coarse (16-stud spacing) but their boundary triangles now use
the exact playable perimeter stations (8-stud spacing, plus ±28 mouth edges). The
readback comparison interpolates both complete edge polylines, not only shared vertices.

Each saved arrangement passes **82 edge comparisons**: four playable→playable, twelve
playable→scenery, and 66 scenery→scenery. Maximum recorded height difference is
**0.000001907 stud**. **Eight mouths / 160 small floor probes** pass across 56-stud widths
and 24-stud approach buffers. Independent readback finds **zero vertical boundary-wall
faces** on all thirteen terrain assets. Top, side, all sixteen unique playable borders
at 4.5-stud eye height, upper joins, the elevated lookback and lower outlook were rendered.

The revised source removes the first pass's square vertical cuts and arbitrary border
humps/sinks. Assembled player views show continuous land, with large formations inland.
The imagery remains a prototype: some silhouettes are still simple, and material baking,
cooked collision and actual movement are not validated by a Blender render.

## Persistent vertical chain

**ENTRY baseline → PATH ascent → COMBAT raised shelf → CAP raised continuation/dead end.**
SIDE branches from COMBAT at the raised level. No descent was added; CAP provides the
allowed alternate raised continuation. **56 studs is provisional**, within the requested
48–64 target, and must remain tunable after playtesting.

| Asset | World placement datum | Entry floor | Outgoing floor | Delta | Continuation |
|---|---:|---:|---:|---:|---|
| ENTRY | 0 | 0 | 0 | 0 | LEVEL_0 |
| PATH | 28 | 0 (local -28) | 56 (local +28) | +56 | LEVEL_1 |
| COMBAT | 56 | 56 | 56 at N/E | 0 | LEVEL_1 |
| SIDE | 56 | 56 at W | none; viewpoint | 0 | raised terminal pocket |
| CAP | 56 | 56 at S | none; collapse | 0 | raised continuation/terminal |

All chunk-local center walk heights remain zero; a review parent supplies placement.
The ascent is broad geological ground, not stairs or precision ledges. Matching-height
high ridges/foothills and lower ravine/lava depressions visually support the raised route.
Arrangement A has a high ridge west of COMBAT and foothill beside CAP; B swaps them;
C uses a different lower ridge/flora composition. The player can look back downhill onto
ENTRY, up the ascent, and outward from the elevated overlook.

## Exact runtime limitations and smallest generic follow-ups

No runtime changes were made. These findings come from the current implementation:

1. **Placement already supports offsets.** `ChunkCore.worldSocket` adds `OffsetY`;
   `placeAgainst` subtracts the arriving socket's `OffsetY`. `ChunkLoader.build` carries
   `placed.Y` into mesh/collider/prop placement. This monotonic, non-overlapping chain
   does not itself require an overlap rewrite.
2. **Drop-in measurement cannot reliably express the transition.** `ChunkAutoKit.probe`
   first rejects edge heights outside tolerance of its inferred center walk height.
   Both ±28 mouths can therefore be omitted. `ChunkKitCore.build` preserves offsets for
   successfully measured openings, but an `Openings` override defaults an **unmeasured**
   opening to zero. Smallest generic fix: measure authored declared mouths regardless
   of center-height difference and retain their measured per-mouth offsets against an
   explicit/common local datum. Verify ±28 transfer and `GroundOffsetY` after import.
3. **Direction is not guaranteed by the drop-in grammar.** `ChunkKitCore` sorts openings
   by facing, and `ChunkCore.placeAgainst` accepts the first matching Kind. A reversed
   transition is a valid descent mathematically. The review deliberately uses PATH's
   south low mouth as arrival. A disposable Studio fixture should specify that chain;
   normal generation needs data-defined compatible arrivals/edge profiles or, if needed,
   existing content socket Kinds. Do not special-case Emberfall in a System.
4. **Overlap remains XZ-only.** `ChunkCore.overlaps` rejects a folded route that occupies
   the same footprint at a different height. Before testing stacked/folded layouts,
   add an optional generic Y-interval check, using authored bounds relative to the ground
   datum (`bottom=-GroundOffsetY`, `top=SizeY-GroundOffsetY`), preserving flat-kit behavior.
   A naïve center ± SizeY/2 check would mishandle asymmetric terrain origins.
5. **Fallback blockout remains flat.** `ChunkLoader.buildBlockout` draws a single floor
   at the placement datum. A missing ascent mesh would leave disconnected floors.
   Smallest generic prototype fix is a socket-height-aware ramp/terrace fallback or a
   clear fail/diagnostic for an unavailable vertical asset; no major loader rewrite.
6. **Scenery compatibility is offline only.** Flat/raised scenery uses the same source
   meshes translated to datum 0/56. Transition-side fitting happens only on disposable
   review copies. Production needs generic elevation/profile-aware scenery selection
   and compatible transition-edge asset variants or a supported fitting mechanism.
   Current gameplay sockets alone do not ensure full-edge compatibility after rotation.
7. **Runtime physics/reachability remains untested.** Open terrain surfaces need local
   importer/material/normal checks and suitable cooked or dedicated walk collision.
   Five roles intentionally omit BOSS, so this is not a boot-valid production kit.
   Do not drop scenery into the normal auto-kit folder: it is not gameplay content.

Before Studio testing, transfer the nonzero mouths reliably and use an explicit temporary
chain with the correct imported yaw, sizes and datum. Walk the ascent/joins, test the upper
camera/roll/jump behavior and prevent unintended access into scenery. Y-aware overlap is
required for later stacked layouts, not a prerequisite to this straight Blender proof.

## Review gate and retained cleanup

Owner review: distinctness of all five places; smooth-versus-faceted balance; lava depth
and plant visibility; whether high scenery embeds the route convincingly; whether three
surround selections meaningfully change the setting. Final elevation, band width, profile
schema, collision/access rules and production scenery variants remain unlocked.

Retain the entire first-pass `Emberfall_Prototype` directory, its original generators,
`PROTOTYPE_REVIEW.md`, original technical reports and contact sheet as historical input.
`Input_FirstPass.blend` is the immutable saved-source copy for this pass; `.blend1` files
are iteration rollbacks. These are the older iterations superseded for visual review.
No export, manifest entry, production asset or code reference was superseded. Remove
redundant review/backups only after owner acceptance plus applicable CI and Studio checks;
until then keep them. No further chunks or production work without owner review.

## Reproduce this study

Use the protected `tools/run_blender.py` launcher for each script, in order:
`revise_emberfall_architecture.py`, `verify_emberfall_architecture.py`, then
`review_emberfall_architecture.py`. Revision reads retained saved input and edits original
assets; verification converts the thirteen collection libraries into independent scenes
and reopens them; review renders every playable boundary and eight scenery portraits.
`-- --no-render` on revision saves/checks without repeating overview renders.
