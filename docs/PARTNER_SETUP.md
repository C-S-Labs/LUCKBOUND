# Testing a world on your own Studio place

For a collaborator who wants to run LUCKBOUND in their **own** Studio place,
with their own uploads. It uses Verdant Valley as the example, but the same
steps work for any chunk-kit world.

## Why you need your own uploads

The game loads each chunk by its **mesh asset id** (`AssetManifest.luau`). A
mesh uploaded by one account often **won't load** in a place owned by another
account or group. It fails silently: the chunk turns into a grey block. So each
person who tests in their own place imports the chunk FBX files themselves and
points the manifest at their own ids. The tool below does that for you.

## One-time setup

```bash
git clone https://github.com/C-S-Labs/LUCKBOUND.git
cd LUCKBOUND
rokit install              # rojo, stylua, selene (versions pinned in rokit.toml)
rojo serve                 # then, in Studio: Rojo plugin -> Connect
```

Open a blank Baseplate in Studio and connect. Rojo fills in ReplicatedStorage,
ServerScriptService, StarterPlayerScripts and ServerStorage from the repo.

## Adding your Verdant Valley pieces

1. **Import** each chunk FBX with Studio's 3D Importer (Avatar tab). Use the
   settings in `assets/README.md` → *Uploading a mesh to Roblox*.
   Keep every MeshPart's name as `chunk_<piece>`, e.g. `chunk_entry` or
   `chunk_meadow_a`. **The name decides which manifest entry the id goes
   to.**
2. **Save** each imported Model (right-click → *Save to File…*, `.rbxmx`) into
   `assets/rbxm/chunks/verdant_valley/`. Overwrite the existing files; they
   hold the old ids. One file per piece or one file for the whole kit both
   work.
3. **Record the ids:**
   ```bash
   python tools/sync_asset_ids.py verdant_valley          # shows what will change
   python tools/sync_asset_ids.py verdant_valley --write  # writes AssetManifest.luau
   ```
   A line starting `NO MANIFEST ENTRY` means a MeshPart name that doesn't
   match a piece in `src/shared/Content/Chunks/VerdantValley.luau`. Rename the
   part and save again, or talk to us before adding a new piece.
4. **Test headless:** `./tests/run.sh`, which must end `0 failed`.
5. **Test in Studio:** press Play, then type these in chat:
   ```
   /roll verdant_valley
   /enter
   ```
   The server log prints `N chunks (N mesh, 0 blockout)`. A **blockout** count
   above 0 means a piece loaded as a grey block: its id is wrong or can't be
   used from your place (see *Why you need your own uploads*).
   `/enter <seed>` rebuilds a map exactly, using the seed printed on entry.

## What goes where

See `assets/README.md` → *Layout*. In short:

| You have | Put it in |
|---|---|
| chunk `.fbx` exports | `assets/export/worlds/verdant_valley/` |
| imported chunk `.rbxmx` | `assets/rbxm/chunks/verdant_valley/` |
| a prop library `.rbxmx` | `assets/rbxm/props/VV_PROP_LIBRARY.rbxmx` |
| `.blend` sources | `assets/source/worlds/verdant_valley/` |

Don't put chunks in `assets/rbxm/maps/`. That folder is for whole,
hand-built maps only.

## Animation and other account-scoped ids

The same restriction applies to **any** `rbxassetid://` in this repo, not just
chunk meshes: `Content/BossPreviews.luau`'s `Idle`/`Pose` animation ids,
`Content/LightningRigs.luau`'s texture id, and so on. An asset uploaded to one
account or group won't load for a client or server running under a different
account/group — Roblox denies the fetch silently. There's no crash; you just
get a warning in the output (`Animation failed to load`, or the mesh render
as a grey block) and the feature quietly does nothing.

If `/showboss` shows the arena but the boss won't play its idle, or logs
`Animation failed to load` for an id that matches `BossPreviews.luau`, this is
almost always why — not a code bug. Fix it the same way as a mesh: re-upload
(or re-publish) the animation under whichever account/group owns the place
you're testing in, and update the id in `BossPreviews.luau`.

**One important difference from Studio testing:** this per-account
restriction only bites while assets and the place are owned by *different*
accounts/groups — which is the normal case in Studio, since each
collaborator's local `.rbxl` is their own. Once LUCKBOUND is actually
**published** as a group-owned experience, with every asset also uploaded to
that same group, any player who joins the live game can load them — group
*membership* isn't required to play, only to upload/manage assets or open the
place in Team Create. So this restriction is a Studio/local-testing problem
you route around per-collaborator now, not something that will affect real
players later, as long as the place and its assets share one owner.

## Sending changes back

Work on a branch and open a pull request. Your manifest ids only work in your
place, so leave `AssetManifest.luau` out of the PR unless we agree to share a
group upload.
