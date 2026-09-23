# World kit framework: how a biome and its scenario variants are built

Sky Citadel is the first world built this way (2026-09-23). Verdant Valley and
Emberfall, and any world after them, follow the same framework. This page is the
contract. `docs/biomes/SKY_CITADEL.md` is the worked example.

## What a world ships

| Layer | What it is | Built by | Game reads |
|---|---|---|---|
| **Base kit** | 30–40 chunk pieces, 256³ each, sockets at edge midpoints | `<world>/build_<world>_kit.py` | `Content/Chunks/<World>.luau` |
| **Scenario kits** | 5–8 variants of the whole base kit: same sockets and walk lines, **their own architecture** | `<world>/build_<world>_scenarios.py` + `<world>_styles.py` + `<world>_structures.py` | `ScenarioKits.luau` (the registry) |
| **Fixed props** | Architecture that moves or is used (lamps, banners, ships, doors). One mesh per construction, placed with a turn and size | the kits, via `as_prop` | `Props_<...>.luau` |
| **Scatter** | Scenery drawn fresh every run from spawn points and pools | `<world>_props.py` (families) + `_framework/scatter_core.py` | `Content/Scatter/<World>/`, `ScatterCore.luau` |
| **Anchors** | Gameplay spots: resources, discoveries, posts, events, route blockers | the scenario hooks | `Anchors_<scenario>.luau` |
| **Atmospheres** | One environment override per scenario (sky, hour, haze, cloud sea, weather) | `<world>_atmospheres.py` | `Environments_Scenarios.luau` |

`ScenarioKits.luau` ties the last five together per scenario: chunk ids, the
model holding its meshes, its scatter pool, its anchors, its blocker, and its
atmosphere key.

## Shared code: `assets/source/worlds/_framework/`

Never copied into a world. Every world's scripts execute these:

| File | Job |
|---|---|
| `geometry_checks.py` | Tags every face with the builder that made it. `validate()` fails a piece with a **detached** part (touching nothing, not a registered float or walkable plate) or a scenario part **clipping** through a rail, wall or keel. `settle()` snaps near-misses, lifts deliberate floaters into animated props, drops scenario parts that can't be attached. `unclip()` drops scenario builds that still clip. |
| `prop_detail.py` | Finishes every prop mesh by material (bevel hard, subdivide organic, facet crystal), budgeted by size: large 2,500–5,000 tris, medium ~900–2,500, small under 900. |
| `scatter_core.py` | The scatter algorithm, the exact twin of `src/shared/Core/ScatterCore.luau` (integer decisions on mulberry32). A seed places the same props in Blender and in the game; `tests/scatter_parity.luau` proves it. |

## The rules every piece keeps

1. **Exactly 256³**: pins at the keel line (-96) and a crown landmark reaching +160.
2. **Sockets** at edge midpoints, widths from the world's vocabulary. The walk line between openings is never built on.
3. **Under 10,000 triangles** per piece.
4. **Nothing floats by accident.** Only islets, walkable stepping plates, and props (which may animate) float.
5. **Nothing clips.** A scenario part may grow out of a mass (a crystal from a tower, a root from a keel, an icicle from the slab it hangs from). It may never pass through a rail, parapet, hedge or bench.
6. **Props are separate from chunks.** Anything that moves, lights, breaks, opens or is interacted with is a prop, flagged with its `Interact`.
7. **One mesh per prop construction.** Copies differ by turn and size on placement (`STRETCH` tolerance), never by a second mesh. Only another colour scheme or truly different proportions make a new mesh.
8. **Names never collide:** `prop_`/`fix_` base kit, `scn_prop_`/`scn_fix_` scenario kits, `sct_` scatter.

## Making scenarios unique, not recoloured

A scenario is not the base piece plus dressing. While a scenario's pieces are
built, `styled(scenario)` swaps the base builders' vocabulary for the
scenario's own: tower, spire, crown landmark, rim, floor pattern, obelisk,
crystal cluster (`sky_citadel_styles.py`). The base builder still decides where
things go, so sockets and footprints hold. Each replacement:

- registers the **same solid** the base part registered (hooks, scatter and validation depend on it);
- renames its code to the base part's name (`@style(scenario, "tower")`), so its faces count as that part;
- draws its own randomness from the piece and the spot, so no two towers match.

The structure hook (`<world>_structures.py`) then adds the scenario's
situation (camps, eruptions, frozen falls, loosened islets), and the looks set
the palette. Budget-guard heavy hook features with `piece_tris(p)`.

## Starting a new world (Verdant Valley, Emberfall)

1. Copy the Sky Citadel scripts as a template; keep `_framework/` shared.
2. Decide the world's socket vocabulary (its own names, disjoint from other worlds'), deck height, crown landmark style and palette.
3. Write the base builders (30–40 pieces), each with a gameplay job.
4. Pick 5–8 scenarios. For each write a **style** (its architecture), a **hook** (its situation), a **look** (its palette), a **scatter pool** and an **atmosphere**.
5. Export (`run.py -- export save` equivalent). Every set must validate. Read the generated `IMPORT_STEPS.md`, `IMPORT_MANIFEST.md` and `ScenarioKits.luau`.
6. Render contact sheets of every set (`work/sheet_set.py`) and compare scenarios side by side before calling it done. **Similar is fine, identical is a failure.**

## The import contract (every world)

The export writes `assets/export/worlds/<world>/IMPORT_STEPS.md`: one FBX per
row, one model name per row. The owner imports each, saves it as `.rbxmx` under
that exact name into `assets/rbxm/incoming/<world>/`, and hands back that folder.
Claude checks every file against `IMPORT_MANIFEST.md`, moves each into place and
wires the kit.
