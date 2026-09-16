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
      ethereal_scape/        aether_environment_refined.blend — 8 islands,
                             a sky temple, and an R6 rig for scale checking
    props/                 shared set dressing
    characters/            enemies, bosses
    discoveries/           collectible objects
  export/        .fbx ready to upload — mirror source/'s paths
  rbxm/          baked .rbxm / .rbxmx models (see below)
```

---

## Adding a mesh — the short version

1. **Author** in Blender → `assets/source/worlds/<world_id>/<name>.blend`
2. **Export FBX** → `assets/export/worlds/<world_id>/<name>.fbx` (same relative path)
3. **Upload** via Studio's 3D Importer or the Open Cloud Assets API
4. **Record** the returned id in `src/shared/Content/AssetManifest.luau` and flip
   `Status` from `"PLACEHOLDER"` to `"UPLOADED"`

A `PLACEHOLDER` entry is legal and validates fine — `assetId()` returns `nil`
and the loader falls back to primitive geometry, exactly like the `MeshId` seam
in the hub. **That is deliberate: chunk layouts are designed, assembled, tested
and walked before any art exists.**

The long version, including every setting that actually matters and the two
that will waste an evening if you get them wrong, is
[**Uploading a mesh to Roblox**](#uploading-a-mesh-to-roblox) below.

---

## Splitting one authored scene into a kit

`aether_environment_refined.blend` is the first real case, and it is the shape
most authored environments will arrive in: **one scene containing a whole
place**, not eight tidy chunk files. Its collections are

```
Aether_Terrain     Island_00 .. Island_07   (each: _Meadow, _GoldRim, _Underside)
Aether_Flora       Tree_Trunk_*, leaves
Traversal_Path     Path_Bridge, Bridge_Abutment_*, Bridge_Landing_*
Sky_Temple         Temple_Column x10 + bases, Spawn_Column x4, Portal_Left/Right
Sky_Decor          Cloud, Crystal_*, Crystal_Cloudstone, Waystone_00..06 + caps
Scale_Reference    an R6 rig  <- the most important object in the file
Presentation       AI_Preview_Camera / _Sun / _Fill  (do NOT export these)
```

Eight islands, eight chunks. `Content/Chunks/EtherealScape.luau` maps them
1:1 and the manifest `Notes` field records which island is which, so the
correspondence is written down rather than remembered.

### The rule that makes it work

**Export each island with its own origin at the island's centre, on the
256-stud grid.** The chunk system positions pieces by their centre and joins
them at sockets; a mesh whose origin sits at the world origin of the Blender
scene will assemble into a pile at one point. In Blender: select the island's
objects → `Object ▸ Set Origin ▸ Origin to Geometry` (or snap the 3D cursor to
the socket grid and use `Origin to 3D Cursor`) → then export **Selected Objects
only**.

### Scale: check it, do not assume it

The scene carries an **R6 rig in `Scale_Reference` for exactly this reason.**
A Roblox R6 character is **5 studs tall, 2 wide, 1 deep.** After importing,
select that rig in Studio and read its size:

| It measures | Meaning |
|---|---|
| ~5 studs tall | ✅ 1 Blender metre = 1 stud. Everything else is correct. |
| ~0.5 studs | the importer applied a 0.1 scale — re-import with World Units set |
| ~50 studs | a 10× — same fix, other direction |

Do this **once, on the whole-scene import** (`ES_ENVIRONMENT_FULL`) before
splitting anything. Getting it wrong after eight separate uploads means eight
re-uploads.

Then sanity-check against `Content/Chunks/EtherealScape.luau`: the pieces
declare 256–768 studs, so an island that imports at 40 studs across is not a
chunk, it is a prop.

---

## Uploading a mesh to Roblox

### 1. Export from Blender

`File ▸ Export ▸ FBX (.fbx)` into `assets/export/worlds/<world_id>/`, mirroring
the source path. Settings that matter:

| Setting | Value | Why |
|---|---|---|
| **Limit to → Selected Objects** | ✅ | one island per file |
| **Forward / Up** | `-Z Forward`, `Y Up` | Blender is Z-up, Roblox is Y-up |
| **Apply Transform** | ✅ | otherwise rotation and scale arrive baked wrong |
| **Object Types** | Mesh only | leave out the cameras, lights and the R6 rig |
| **Apply Modifiers** | ✅ | the importer does not run your modifier stack |

Before exporting, `Ctrl+A ▸ All Transforms` on everything you are sending.
Unapplied scale is the single most common cause of "it imported at the wrong
size and I cannot see why".

### 2. Import into Studio

**Studio ▸ Avatar tab ▸ 3D Importer** → pick the `.fbx`.

- **Watch the triangle count.** A single MeshPart caps at **10,000 triangles**.
  An island with 60 trees on it will blow through that; the importer will
  offer to split it into multiple MeshParts, which is fine — group them and the
  chunk becomes a Model rather than one MeshPart.
- **Set the Creator correctly** in the importer if this experience is
  group-owned. An asset uploaded to your personal account **will not load in a
  group experience**, and the failure looks like an invisible mesh rather than
  an error.
- Materials: FBX carries material *names*, not Blender's node graphs. The
  scene's twelve materials (Aether Mint Grass, Temple Gold, …) will arrive as
  slots you colour in Studio, or you bake them to a texture in Blender first.
  For a blockout test, colouring in Studio is faster and good enough.

### 3. Read the asset id

Select the imported MeshPart → **Properties ▸ MeshId** → it reads
`rbxassetid://NNNNNNNNNN`. That number is the whole point of the import.

### 4. Record it in the manifest

```lua
ES_CHUNK_SKY_TEMPLE = {
    AssetId = "rbxassetid://1234567890",
    Status  = "UPLOADED",        -- was "PLACEHOLDER"
    Source  = "assets/source/worlds/ethereal_scape/aether_environment_refined.blend",
    Notes   = "Island_07 + the Sky_Temple collection + Portal_Left/Right.",
},
```

**Nothing else changes.** `ChunkLoader` calls
`AssetService:CreateMeshPartAsync` on any key that resolves, and falls back to
blockout for any key that does not — so the kit converts from primitives to art
**one island at a time**, and a half-uploaded kit is a perfectly valid state to
play in. There is no flag day.

### The scriptable alternative

Roblox's **Open Cloud Assets API** uploads meshes with an API key and returns
the id, so steps 2–3 can be a script once you are re-uploading often. Not worth
setting up for a first import — do it by hand, see it work, automate later.

---

## Publishing the PLACE (a different thing entirely)

Uploading a mesh and publishing the experience are unrelated operations, and
the second one is what unblocks persistence:

1. **File ▸ Publish to Roblox As…** → create a new experience (or pick one).
2. **Home ▸ Game Settings ▸ Security** → enable **Studio Access to API
   Services**.

Until both are done, `DataStoreService` raises on every call and the server runs
in volatile mode — which it says on boot, and which is why acceptance criteria
P1-8 and P1-9 are still unverified. See `docs/TOOLCHAIN_ACCESS.md` §5.1.

**Publishing is not required to test map generation.** The expedition system
does not touch DataStores; a local `.rbxl` with Rojo connected is enough to roll
Ethereal Scape, walk through the Gate and stand in a generated map. Publish when
you want saving, cross-server events, or other people in the place.

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
