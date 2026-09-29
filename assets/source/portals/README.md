# Expedition rifts (build spec §7.8)

Two authored rifts, tears in the air, generated headless from `build_expedition_portals.py`. (The first cut was a
mechanical ring portal; the owner replaced it on 2026-09-28 as out of place in a floating biome.)

| Model | Triangles | Parts | Role |
|---|---|---|---|
| `EXPEDITION_ENTRANCE` | ~7.4k | 41 | always open, on the ENTRY chunk; coloured by the biome's rarity |
| `EXPEDITION_EXIT` | ~10.3k | 59 | materialises where the boss fell; always crimson |

The mesh is the shape; **code is the motion and the light** (Beams with a flow texture, particles, tweening, the point
light). Every mesh is under 10k triangles and the script fails if a name is missing or the ground parts rise.

```
blender -b --factory-startup --python build_expedition_portals.py -- --variant BOTH --export --save
```

(or `python build_expedition_portals.py --variant BOTH` with the `bpy` wheel). It writes `expedition_<variant>.blend`
here and `assets/export/portals/EXPEDITION_<VARIANT>.fbx`.

## Contract (names are exact)

`Scar` (PrimaryPart, carries the prompt, thin, not collidable) · `ScarGlow` (tinted) · `RiftCore` / `RiftMid` /
`RiftHalo` (tinted shells the code breathes independently) · `Edge1..N` (tinted crystal lips) · `FragRock1..N` +
`FragGem1..N` (floating rock; gems tinted) · `Debris` · `LightAnchor`.

Tinted parts are untextured and near-white so the rarity colour shows. Lights, beams and particles are made by code.

**Flush and walkable:** nothing is collidable and the ground parts sit under 0.12 studs. The tear's tip touches the
deck, so the way through is level ground with nothing to climb. Fragments float at least 20% up the tear, clear of the
path.

## Studio import (owner step, not done yet)

1. Import each FBX with the 3D Importer (Imported Rig, Custom, Meter, 1.0).
2. Save as `assets/rbxm/prefabs/EXPEDITION_ENTRANCE.rbxmx` / `EXPEDITION_EXIT.rbxmx`.
3. Measure the imported scale against the spec and record it as `Prefab.Scale` (as `HUB_FATE_ENGINE` did).
4. Upload the flow texture (see the spec) and put its id in `AssetManifest`.

Until those files exist the game keeps drawing the `PortalRig` blockout portals.
