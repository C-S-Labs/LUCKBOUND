# Sky Citadel: import steps

GENERATED on every export. Follow top to bottom. Nothing else is needed.

Two files: every chunk in one, every prop in the other. Each imports as one Model
with a folder per set inside (chunks: Base + the seven scenarios; props: Base,
Scenarios, Scatter).

## 1. Import into Roblox Studio (twice)

For **each of the two rows** below:

1. Studio: **File > Import 3D**. Pick the FBX from `C:\Dev\luckbound\assets\export\worlds\sky_citadel\import\`.
2. Import settings: **Anchored ON**, **Merge Meshes OFF** (every object must stay its own MeshPart),
   **Rig: none**. Leave names alone.
3. It lands as one Model in Workspace. Check its name matches the right column (rename if not).
4. Right-click the Model > **Save to File...** > type **.rbxmx** > save it into
   `C:\Dev\luckbound\assets\rbxm\incoming\sky_citadel\` with that same name.
5. Delete the Model from Workspace before the next row.

| # | Import this FBX | Save the Model as |
|---|---|---|
| 1 | `SkyCitadel_Chunks.fbx` | `SkyCitadel_Chunks.rbxmx` |
| 2 | `SkyCitadel_Props.fbx` | `SkyCitadel_Props.rbxmx` |

**Never rename a MeshPart inside a Model.** Their names are how the game finds them
(every one is listed in `IMPORT_MANIFEST.md`).

## 2. Hand back

When all 2 files are in `assets\rbxm\incoming\sky_citadel\`, tell Claude:

> The Sky Citadel import is in `assets/rbxm/incoming/sky_citadel`.

Claude then checks every file against `IMPORT_MANIFEST.md` (nothing missing, nothing
renamed, every MeshPart has a real mesh id), moves each into place, and wires the kit.
Do not put these files anywhere else, and do not edit the ones already in
`assets/rbxm/props` or `assets/rbxm/maps` -- the live game uses those until the switch.

