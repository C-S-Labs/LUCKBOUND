# Ethereal Scape live-scene delivery — 2026-09-30

Use this worktree: `C:\Dev\luckbound\.worktrees\ethereal-scape-polish`.
The primary checkout is on the portal task branch and does not contain this delivery.

**2026-10-01:** both owner-imported models are now verified and synced in this worktree.
Studio shortened50 long prop names, including a duplicate; the worktree XML has been corrected.
Use these corrected models for the walk, rather than recopying the primary prop library over them.
Steps1–4 below are complete for this delivery; proceed to serve and walk.

## Import and save

1. Stop Studio Play. Open **3D Importer** and import:
   `C:\Dev\luckbound\.worktrees\ethereal-scape-polish\assets\export\worlds\ethereal_scape\ethereal_scape_structure.fbx`.
   Keep scale **1**, preserve colors, and keep meshes separate. Expect **227 MeshParts**.
   Their overlap in the imported preview is intentional: runtime content supplies every placement.
2. Rename the imported Model **ES_STRUCTURE**. Keep the individual `chunk_*` mesh names.
   Select its MeshParts and use **SmoothPlastic**. Save the whole Model as XML `.rbxmx`:
   `C:\Dev\luckbound\.worktrees\ethereal-scape-polish\assets\rbxm\chunks\ethereal_scape\ES_STRUCTURE.rbxmx`.
3. Import `assets\export\worlds\ethereal_scape\ethereal_scape_props.fbx` from the same worktree.
   Expect **258 MeshParts**: the existing 13 atmosphere meshes and 245 separated scene props.
   Keep meshes separate and names unchanged. Rename the Model **ES_PROP_LIBRARY** and save as:
   `C:\Dev\luckbound\.worktrees\ethereal-scape-polish\assets\rbxm\props\ES_PROP_LIBRARY.rbxmx`.
   Portals, mounted effects, canopy pivots, chandelier, gate and chest door are separate meshes.
4. Tell Codex both files are saved. The structure's uploaded IDs must then be synced into
   AssetManifest and rechecked before Play. Props are resolved by name from the library.
   No separate boundary FBX is required; the loader creates collision from authored content.
5. Keep imported preview Models out of Workspace when testing. Rojo loads structure provenance into
   ServerStorage and the prop library into ReplicatedStorage. Let the runtime place copies.

## Serve and walk after ID sync

```powershell
cd C:\Dev\luckbound\.worktrees\ethereal-scape-polish
rojo serve
```

Connect the Studio Rojo plugin to this server and accept the changes. Play, then use
`/roll ETHEREAL_SCAPE test` and enter normally. This catalogue includes the dependent room
only alongside its shrine. Normal seeds instantiate the room only when that shrine is selected.
The room is placed 4,096 studs above its parent and is reached through the shrine portal;
the return portal takes players back to that same shrine instance. Destination streaming is requested
before travel ([Roblox Player API](https://create.roblox.com/docs/reference/engine/classes/Player)).

Check bridge/stair seams, flush paths, foliage alignment, windows, border openings and free/locked cameras.
Borders are transparent 64-stud colliders around 35 playable templates, with socket mouths open.
Mounted lights and portal surfaces pulse; canopies sway about their attachment height.

**Vault rule:** only the **biome boss** drops `ETHEREAL_SCAPE_VAULT_KEY` (20% by current content).
That boss's completion slides the shrine vault-room gate upward for everyone, regardless of the drop.
The chest remains locked for each player without a key; unlocking spends that player's key.
Miniboss completion does not open the gate or drop this key. Enemies are still deferred.
For the Studio stand-in, `/boss` simulates the biome boss, `/takekey` clears keys,
and `/givekey ETHEREAL_SCAPE_VAULT_KEY` grants a test key. Existing automatic boss-arena stand-in
remains enabled, so entering the Sanctum can also count as biome-boss completion during the walk.

## Counts and retained files

| Category | Templates |
|---|---:|
| Ordinary PATH / COMBAT / SIDE / CAP | 31 |
| Combat-role subset of ordinary | 11 |
| Registered miniboss arenas | 2 |
| Conditional shrine miniboss chamber | 1 |
| Entry / biome boss / backdrop | 1 / 1 / 6 |
| Loot venues | altar chest + conditional shrine vault |

Enemy tags describe eligibility, not spawned enemies: 24 ordinary templates are tagged,
25 including entry, 28 including the registered miniboss/boss arenas. Gameplay enemies remain absent.

The earlier RBXMX uploads remain in place until you save replacements. Retain old uploads/review assets
until the new IDs, Studio walk and CI pass. No PR/push before owner approval. Atmosphere is next;
enemy integration belongs to a separate conversation. Do not regenerate the old kit to export this scene.
