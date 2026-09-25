# Sky Citadel refinish (2026-09-24): re-import steps

The 36 chunk meshes and the prop library were re-exported with the semi-mid-poly finish:
- violet trim bevels on long sharp edges
- cyan seams on big wall panels
- trim-edged deck plates

Shapes, sizes, sockets and names are unchanged, so only the **mesh ids** change.

## 1. Chunks (structure)
1. Studio: **3D Importer**, then `assets/export/worlds/sky_citadel/sky_citadel_structure.fbx`. Leave the scale alone.
   It comes in as one Model with 36 MeshParts named `chunk_*`.
2. Check one piece: it must read **256 × 256 × 256**.
3. Select all 36 MeshParts and set **Material = SmoothPlastic** (the glossy finish; the FBX can't carry it).
   Keep vertex colours on, the same as before.
4. Right-click the Model, then *Save to File*, overwriting `assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx`.
5. Copy each MeshPart's new **MeshId** into `src/shared/Content/AssetManifest.luau`. Only the `AssetId` line changes on
   each `SC_CHUNK_*` entry: `chunk_entry` → `SC_CHUNK_ENTRY`, `chunk_path_straight` → `SC_CHUNK_PATH_STRAIGHT`, and so on.

## 2. Props
6. 3D Importer, then `assets/export/worlds/sky_citadel/sky_citadel_props.fbx`. Save it over
   `assets/rbxm/props/SC_PROP_LIBRARY.rbxmx`, and update the `SC_PROP_*` AssetIds the same way.
   The placements files (`src/shared/Content/Props/SkyCitadel.luau`, `Fixtures/SkyCitadel.luau`) were regenerated.
   Their content is unchanged apart from line endings.

## 3. Recolours (scenario variants)
7. The `SC_CHUNK_*__<SCENARIO>` recolours are built from the kit. Rebuild them so they get the finish too:
   `blender -b --factory-startup --python assets/source/worlds/sky_citadel/build_sky_citadel_recolors.py -- --export`.
   Then import and save them over `SC_RECOLORS.rbxmx` and update their ids, as in step 5.
   (If you'd rather keep the old recolours for now, skip this step. They still load; they just won't have the trim.)

## 4. Walk it
8. Press Play. The chunks should join flush: the finish never touches the outermost 1 stud of a tile.
   Check a few joins close up, and one boss clearing for the trim and seams.
