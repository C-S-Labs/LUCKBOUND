# Enemies (source)

Read `docs/ENEMY_FRAMEWORK.md` first. There are two kinds of folder here:
- `_framework/`: shared code for every biome (runner, modelling kit, pose solvers, animation core, validation, export).
- `<biome>/`: that biome's content. `manifest.py` is the roster; model scripts, `anims/<enemy>/<Action>.py`, moveset sheets.

```
blender -b --factory-startup --python assets/source/enemies/_framework/run.py -- sky_citadel winged_sentinel --validate --render
blender -b --factory-startup --python assets/source/enemies/_framework/run.py -- sky_citadel winged_sentinel --export --anims all --preview
```
Outputs: FBX in `assets/export/enemies/<biome>/`; review renders in `<biome>/renders/` (git-ignored).

Sky Citadel (the first biome): 10 basics, 3 minibosses, 3 bosses, all built. The Winged Sentinel is fully posed. It has the
Idle_Guard, P2_Transition and P1_Lunge actions, and the rest of its moveset is in `sky_citadel/WS_MOVESET.md`.
Some Winged Sentinel files (`ws_*.py`, `render_ws.py`) predate the runner and are kept as its boss-specific extension.
`render_ws.py` expects `HERE`/`FW`/`OUT_DIR`/`RENDER_DIR` to be set, which run.py does.
