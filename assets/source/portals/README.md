# Expedition portals (build spec §7.8)

Two authored portals, generated headless from `build_expedition_portals.py`:

| Model | Triangles | Parts | Role |
|---|---|---|---|
| `EXPEDITION_ENTRANCE` | ~11k | 30 | always open, on the ENTRY chunk |
| `EXPEDITION_EXIT` | ~18k | 38 | sealed by `Blade1..8` until the boss falls, on the BOSS chunk |

Budget is 10k–25k triangles per model and under 10k per mesh; the script fails if either is broken.

```
blender -b --factory-startup --python build_expedition_portals.py -- --variant BOTH --export --save
```

(or `python build_expedition_portals.py --variant BOTH` with the `bpy` wheel). It writes `expedition_<variant>.blend`
here and `assets/export/portals/EXPEDITION_<VARIANT>.fbx`.

## Contract (names are exact)

`Foundation` (buried, not collidable) · `Plinth` (PrimaryPart, the only collidable part) · `OuterRing` (spins) ·
`InnerRing` (counter-spins, tinted) · `PortalPlane` (tinted, pulses) · `Rune1..8` · `Glyph1..8` (tinted) ·
`Shard1..6` (tinted, spin) · `RingFoot1..2` · `SpotAnchor` · EXIT only: `Blade1..8`.

Tinted parts are untextured and near-white so the rarity colour shows. Lights and particles are made by code.

**Flush:** `Foundation` sits below z = 0 and is sunk into the chunk deck; `Plinth` rises 1.8 studs as a stepped rim.
Nothing else sits on the walk plane.

## Studio import (owner step, not done yet)

1. Import each FBX with the 3D Importer (Imported Rig, Custom, Meter, 1.0).
2. Save as `assets/rbxm/prefabs/EXPEDITION_ENTRANCE.rbxmx` / `EXPEDITION_EXIT.rbxmx`.
3. Measure the imported scale against the spec and record it as `Prefab.Scale` (as `HUB_FATE_ENGINE` did).

Until those files exist the game keeps drawing the `PortalRig` blockout portals.
