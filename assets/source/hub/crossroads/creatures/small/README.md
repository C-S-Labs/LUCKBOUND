# Crossroads V2 sky creatures: group SMALL

`build_small.py` builds `skyfinch`, `lumen_moth` (TINY) and `cinderkite`, `prism_darter` (SMALL) per
`docs/design/SKY_ECOSYSTEM_CONTRACT.md` 2, 3, 4.1. Helpers and palette come read-only from
`build_crossroads_hub.py` via runpy; six new palette entries (Moss, Leaf, Ash, EmberDeep, StarGlass,
PearlViolet) are appended locally.

    python tools/run_blender.py -b --factory-startup --python build_small.py -- --export --render

Outputs: `assets/export/hub/crossroads/creatures_small.fbx` and `.json`; `renders/contact_sheet.jpg`
(columns: finch, moth, kite, darter; rows: 3/4, top, front).

Conventions: head +X, up +Z; origin = body bounding-box centre; all meshes share that origin. Wings sit flat
at rest; a positive turn about a wing's axis lifts the tip (left wing axis mirrored). JSON `size` is the whole
creature at rest (body + parts), `biome` uses world ids, offsets/hinges/axes are in Blender axes (as
`crossroads_layout.json`); `Pulse` amp is a scale fraction. Meshes are uploaded by the owner later.
