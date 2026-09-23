# Ambient-scenery prop libraries

Synced by Rojo to `ReplicatedStorage.LuckboundProps`. The client's
`PropController` clones props from here by **name** (`prop_crystal_a`, …) and
places them from `src/shared/Content/Props/<World>.luau`.

One `.rbxmx` per world, e.g. `SC_PROP_LIBRARY.rbxmx`: the Model the 3D Importer
makes from the kit's `*_props.fbx`, saved with the export plugin. Each MeshPart
inside keeps its Blender object name — that name is the link to the placements,
so **do not rename them**.

See `docs/CHUNK_AUTHORING.md` convention 6.
