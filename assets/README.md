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

## One authored scene: split it, or ship it whole?

Authored environments arrive in the shape `aether_environment_refined.blend`
arrived in: **one scene containing a whole place**, not eight tidy chunk files.
That leaves a decision, and it is the art that makes it, not the code.

```
Aether_Terrain     Island_00 .. Island_07   (each: _Meadow, _GoldRim, _Underside)
Aether_Flora       Tree_Trunk_*, leaves
Traversal_Path     Path_Bridge, Bridge_Abutment_*, Bridge_Landing_*
Sky_Temple         Temple_Column x10 + bases, Spawn_Column x4, Portal_Left/Right
Sky_Decor          Cloud, Crystal_*, Crystal_Cloudstone, Waystone_00..06 + caps
Scale_Reference    an R6 rig  <- the most important object in the file
Presentation       AI_Preview_Camera / _Sun / _Fill  (do NOT export these)
```

### The question to ask first

**Are the pieces interchangeable, or were they composed?**

A chunk kit buys variety and charges modularity for it: every piece must join
to every other piece, so gaps, heights and rims all have to be the same. Art
that was composed cannot supply that without being re-authored.

Ethereal Scape looked like eight chunks and measured like one map — its islands
climb, its six bridges are each cut to their own gap, and the islands grow
toward the temple. `assets/rbxm/maps/README.md` shows the measurements. It
ships whole.

Four questions that settle it, all answerable by measuring the file:

1. Do the pieces sit at the **same height**, or does the route climb?
2. Are the **gaps between them identical**, or is each connector bespoke?
3. Are the pieces **the same size**, or do they build toward something?
4. Would **shuffling them** still read as the same place?

Four yeses is a kit. Any no is a map.

### If it is a kit: export island by island

**Export each piece with its own origin at the piece's centre, on the 256-stud
grid.** The chunk system positions pieces by their centre and joins them at
sockets; a mesh whose origin sits at the world origin of the Blender scene will
assemble into a pile at one point. In Blender: select the piece's objects →
`Object ▸ Set Origin ▸ Origin to Geometry` (or snap the 3D cursor to the socket
grid and use `Origin to 3D Cursor`) → then export **Selected Objects only**.

Each piece becomes a manifest entry and a chunk in `Content/Chunks/`.

### If it is a map: one file, one entry

Save the whole scene as a `.rbxmx` into `assets/rbxm/maps/`, named for its
manifest key, and give the world a `PrebuiltMap`. Two named parts inside it —
`EntryAnchor` and `ReturnAnchor` — are the entire contract. See
`assets/rbxm/maps/README.md`.

No socket grammar, no grid alignment, no per-piece origins. Every run of that
world is the same map, which is the price.

### Scale: check it, do not assume it

The scene carries an **R6 rig in `Scale_Reference` for exactly this reason.**
A Roblox R6 character is **5 studs tall, 2 wide, 1 deep.** After importing,
select that rig in Studio and read its size:

| It measures | Meaning |
|---|---|
| ~5 studs tall | ✅ 1 Blender metre = 1 stud. Everything else is correct. |
| ~0.5 studs | the importer applied a 0.1 scale — re-import with World Units set |
| ~50 studs | a 10× — same fix, other direction |

Do this **once, on the whole-scene import**, before splitting anything. Getting
it wrong after eight separate uploads means eight re-uploads.

**Do not check the rig alone.** Ethereal Scape's proxy measured 59.6 studs and
two sessions concluded the proxy was wrong, because the islands looked the
right size for a chunk kit. They were not: the doorways were 48 person-heights
tall, the trees 25. Measure a doorway, a tree and a walkway against a 5-stud
character too — if they all agree with the rig, the rig is right and the scene
is oversized.

A prebuilt map can fix that with one number (`PrebuiltMap.Scale`) and no
re-upload. A chunk kit cannot: its `SizeX/Y/Z` drive collision rejection and
must match the uploaded geometry.

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

`rbxm/maps/` is wired into `default.project.json` and syncs to
`ServerStorage.LuckboundMaps`, where `Util/PrebuiltLoader` finds whole authored
maps by name. See `rbxm/maps/README.md`.

`ServerStorage` is deliberate: models there are invisible to clients, so
exploiters cannot dump the discovery, loot or enemy roster ahead of time
(addendum §A2). It also means a 4 MB map is not replicated to every player at
join — only the clone on the stage is.

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
