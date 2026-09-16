# LUCKBOUND — Assets

Blender sources, mesh exports, and baked Roblox models.

---

## The constraint that shapes this folder

**Roblox cannot load `.blend`, `.fbx` or `.obj` at runtime.** Every mesh must be
uploaded to Roblox's servers first and referenced by `rbxassetid://`. There is
no way around it, regardless of tooling — see `docs/ADDENDUM_ASSET_PIPELINE.md`
§A1.

So the split is:

| Lives here | Lives on Roblox's CDN |
|---|---|
| `.blend` sources, `.fbx` exports, `.rbxm` prefabs | the actual mesh geometry |
| The **manifest** mapping names → asset ids | — |

`src/shared/Content/AssetManifest.luau` is the bridge. **Nothing in the game
ever names a raw asset id directly** — code and content name a logical key, so
re-uploading a mesh is a one-line change in one file.

---

## Layout

```
assets/
  source/        .blend files — authoring only, never consumed by the game
    worlds/<world_id>/     chunk pieces for that biome
    props/                 shared set dressing
    characters/            enemies, bosses
    discoveries/           collectible objects
  export/        .fbx ready to upload — mirror source/'s paths
  rbxm/          baked .rbxm / .rbxmx models (see below)
```

---

## Adding a mesh

1. **Author** in Blender → save to `assets/source/worlds/verdant_valley/chunk_meadow.blend`
2. **Export FBX** → `assets/export/worlds/verdant_valley/chunk_meadow.fbx`
   - Apply transforms, Z-up → Y-up, and set the origin where you want the pivot
   - **1 Blender metre = 1 Roblox stud** — decide this once and never drift
3. **Upload** — Studio's 3D Importer (manual) or the Open Cloud Assets API (scriptable)
4. **Record** in `src/shared/Content/AssetManifest.luau`:

```lua
VV_CHUNK_MEADOW = {
    AssetId = "rbxassetid://1234567890",
    Status  = "UPLOADED",        -- was "PLACEHOLDER"
    Source  = "assets/source/worlds/verdant_valley/chunk_meadow.blend",
},
```

Nothing else changes. A `PLACEHOLDER` entry is legal and validates fine — the
loader falls back to primitive geometry, exactly like the `MeshId` seam in the
hub. **That is deliberate: chunk layouts are designed, assembled and tested
before any art exists.**

---

## The `rbxm/` folder

A `.rbxm`/`.rbxmx` is a Roblox model file that can hold MeshParts, attachments,
lights and configuration together. Rojo can sync one straight into the place, so
it suits prefabs that are more than bare geometry.

Not wired into `default.project.json` yet — an empty mapping risks breaking the
sync. When the first prefab exists, add:

```json
"ServerStorage": {
  "$className": "ServerStorage",
  "Prefabs": { "$path": "assets/rbxm" }
}
```

`ServerStorage` is deliberate: prefabs there are invisible to clients, so
exploiters cannot dump the discovery, loot or enemy roster ahead of time
(addendum §A2).

---

## Repository size

`.blend` and `.fbx` files are binary and can be large. `.gitattributes` already
marks them binary so git never tries to diff or merge them.

If the folder passes a few hundred MB, enable **Git LFS** before it becomes
painful — history rewriting later is far worse than setting it up early.

---

## Modular map pieces

The chunk system that consumes these is documented in
[`docs/MODULAR_MAPS.md`](../docs/MODULAR_MAPS.md). Read it before authoring a
kit — socket placement and grid alignment decide whether pieces can connect at
all, and those are cheap to get right up front and expensive to retrofit.
