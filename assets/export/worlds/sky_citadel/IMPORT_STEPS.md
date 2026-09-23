# Sky Citadel: import steps

GENERATED on every export. Follow top to bottom. Nothing else is needed.

## 1. Import into Roblox Studio (one file at a time)

For **each row** below:

1. Studio: **File > Import 3D**. Pick the FBX from `C:\Dev\luckbound\assets\export\worlds\sky_citadel\`.
2. Import settings: **Anchored ON**, **Merge Meshes OFF** (every object must stay its own MeshPart),
   **Rig: none**. Leave names alone.
3. It lands as one Model in Workspace. **Rename that Model** to the name in the right column.
4. Right-click the Model > **Save to File...** > type **.rbxmx** > save it into
   `C:\Dev\luckbound\assets\rbxm\incoming\sky_citadel\` with that same name.
5. Delete the Model from Workspace before the next row.

| # | Import this FBX | Save the Model as |
|---|---|---|
| 1 | `sky_citadel_structure.fbx` | `SC_STRUCTURE_BASE.rbxmx` |
| 2 | `scenarios\unmooring\sky_citadel_unmooring_structure.fbx` | `SC_STRUCTURE_UNMOORING.rbxmx` |
| 3 | `scenarios\siege\sky_citadel_siege_structure.fbx` | `SC_STRUCTURE_SIEGE.rbxmx` |
| 4 | `scenarios\lockdown\sky_citadel_lockdown_structure.fbx` | `SC_STRUCTURE_LOCKDOWN.rbxmx` |
| 5 | `scenarios\stormhawk\sky_citadel_stormhawk_structure.fbx` | `SC_STRUCTURE_STORMHAWK.rbxmx` |
| 6 | `scenarios\rime\sky_citadel_rime_structure.fbx` | `SC_STRUCTURE_RIME.rbxmx` |
| 7 | `scenarios\reclaimed\sky_citadel_reclaimed_structure.fbx` | `SC_STRUCTURE_RECLAIMED.rbxmx` |
| 8 | `scenarios\aether_surge\sky_citadel_aether_surge_structure.fbx` | `SC_STRUCTURE_AETHER_SURGE.rbxmx` |
| 9 | `sky_citadel_props.fbx` | `SC_PROPS_BASE.rbxmx` |
| 10 | `scenarios\sky_citadel_scenario_props.fbx` | `SC_PROPS_SCENARIOS.rbxmx` |
| 11 | `scenarios\sky_citadel_scatter_props.fbx` | `SC_PROPS_SCATTER.rbxmx` |

**Never rename a MeshPart inside a Model.** Their names are how the game finds them
(every one is listed in `IMPORT_MANIFEST.md`).

## 2. Hand back

When all 11 files are in `assets\rbxm\incoming\sky_citadel\`, tell Claude:

> The Sky Citadel import is in `assets/rbxm/incoming/sky_citadel`.

Claude then checks every file against `IMPORT_MANIFEST.md` (nothing missing, nothing
renamed, every MeshPart has a real mesh id), moves each into place, and wires the kit.
Do not put these files anywhere else, and do not edit the ones already in
`assets/rbxm/props` or `assets/rbxm/maps` -- the live game uses those until the switch.

