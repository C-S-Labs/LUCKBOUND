# Sky Citadel: the 36-piece upload

The live game has the original 22 meshes, plus the 14 new pieces as grey
blockout (every map still generates). To make all 36 real:

1. Studio: **File > Import 3D** → `assets/export/worlds/sky_citadel/sky_citadel_structure.fbx`
   (Anchored ON, Merge Meshes OFF, Rig none). Save the Model as
   `assets/rbxm/incoming/sky_citadel/SC_STRUCTURE_36.rbxmx`.
2. Same for `sky_citadel_props.fbx` → `assets/rbxm/incoming/sky_citadel/SC_PROPS_36.rbxmx`.
3. Tell Claude: *"The 36-piece import is in assets/rbxm/incoming/sky_citadel."*

Claude then puts every new mesh id in `AssetManifest.luau`, swaps in
`staged_luau/Props_SkyCitadel.luau` + `Fixtures_SkyCitadel.luau`, and replaces
the prop library. The 22 old meshes must be replaced together with the props
(their halos and hovering crystals became props), so it is one switch.
