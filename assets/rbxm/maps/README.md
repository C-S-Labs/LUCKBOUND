# Prebuilt maps

Models in this folder are **whole, hand-authored expedition maps**. Rojo syncs
the folder to `ServerStorage.LuckboundMaps`, naming each instance after its
file, and `Util/PrebuiltLoader` clones the one whose name matches a world's
`PrebuiltMap.AssetKey`.

One file per map. The file stem **is** the manifest key — rename the file and
you have renamed the asset.

## The two ways a world gets a map

A world declares exactly one of them, and `Schema.validateMaps` refuses a world
that declares both:

| | Chunk kit | Prebuilt map |
|---|---|---|
| Declared by | chunks naming the world in `Content/Chunks/` | `PrebuiltMap` on the world |
| Built by | `ChunkCore` + `ChunkLoader` | `PrebuiltLoader` |
| Every run | different layout from the seed | identical |
| Art must be | modular: matching rims, gaps, heights | anything at all |
| Today | Verdant Valley | Ethereal Scape |

Neither is the better one. A kit buys variety and charges modularity for it.

## The contract with the modeller

Two named parts, anywhere in the model:

| Name | What it is |
|---|---|
| `EntryAnchor` | the player arrives standing on top of it |
| `ReturnAnchor` | the way home is built on top of it |

Both optional. Without `EntryAnchor` the loader stands the player on top of the
model's bounding box and warns; without `ReturnAnchor` the way home goes at the
arrival point. So an unprepared scene still loads and can be walked — art
arrives before its anchors do, and a hard failure there would mean a map could
not be looked at until it was finished.

Everything else is free. The loader anchors every part on clone (an FBX import
leaves them all loose, and a scene that falls on its first frame does it
silently), scales the model by the world's `PrebuiltMap.Scale`, and pivots it
onto the stage origin.

---

# `ES_ENVIRONMENT_FULL.rbxmx` — Ethereal Scape

The Blender scene imported into Studio and saved back out as a Roblox XML
model. Delivered 2026-09-16.

| | |
|---|---|
| Format | `.rbxmx` (XML) — readable from the repo, which is the point |
| Size | 4.3 MB |
| Contents | **699 MeshParts** in one flat `Model` |
| Mesh data | **every part carries a real `rbxassetid://` MeshId** — the geometry is uploaded and lives on Roblox's CDN |
| Names | preserved from Blender: `Island_00_Meadow`, `Temple_Column`, `Waystone_03`, `Path_Bridge`, `Spawn_Column`, `R6_Torso` … |

**The upload half of the pipeline worked.** 699 meshes on the CDN, referenced
by id, names intact. That is the expensive part and it is done.

## Why this world is prebuilt

It was going to be eight chunks. Measuring the delivered file settled it the
other way: **the scene is a composed traverse, not a set of interchangeable
pieces.** Four independent things say so.

**1. It climbs.** The eight island meadows rise monotonically, ~58 studs a
step:

```
Island_00  y 354      Island_04  y 571
Island_01  y 408      Island_05  y 625
Island_02  y 467      Island_06  y 693
Island_03  y 512      Island_07  y 761
```

**2. Each bridge is cut to its own gap.** Six `Path_Bridge` parts, 714–833
studs long, each sitting in one specific gap at that gap's specific height.

**3. The landings are authored in matched pairs.** Thirteen `Bridge_Landing`
parts named `_NN_0` and `_NN_1` — the two ends of bridge NN, one on each island
it joins.

**4. It builds toward the temple.** Islands grow 1030 × 813 at the arrival
shelf to 1932 × 1535 under the Sky Temple.

Shuffle the islands and all four break at once. The socket grammar is not
wrong — this art is simply not modular, and making it modular would mean
re-authoring it: identical gaps, identical height deltas, identical rims.

Fourteen more landmasses (`Satellite_00`–`15`) hang off the route as backdrop.

## Scale — resolved, provisionally

The scene carries its own R6 proxy in `Scale_Reference`, and this is exactly
what it was for:

```
R6_Leg   22.6 studs tall
R6_Torso 22.6
R6_Head  14.4
         -----
         59.6 studs total     A real Roblox R6 character is 5.
```

Earlier sessions read that as ~12× and guessed the **proxy** was wrong, because
the islands measured 1030–1932 studs and that felt right. Measuring the rest of
the scene reverses the verdict: **everything agrees with the proxy, not with
Roblox.**

| Object | As delivered | Against a 5-stud character | At scale 0.1 |
|---|---|---|---|
| Temple doorway jamb | 239 studs | 48× a person | 24 studs |
| Tree (trunk + crown) | 126 | 25× | 13 |
| Waystone + cap | 117 | 23× | 12 |
| Spawn colonnade column | 108 | 22× | 11 |
| Bridge deck | 789 long | — | 79 |
| Island 00 meadow | 1030 × 813 | — | 103 × 81 |
| Arrival → temple | 10,278 | 642 s walk | 1,028 studs, 32 s |

A 48-person-high doorway is not a stylistic choice, it is a unit error. The
scene is internally consistent and uniformly ~10× oversized, so **one number
fixes all of it** — `PrebuiltMap.Scale`, currently `0.1`.

That number is **provisional until someone walks it.** It is data on the world,
not a re-upload: change it, rejoin, walk it again. Nothing has to be re-exported
and no mesh has to be re-uploaded whatever the answer turns out to be.

## Still to do on this file

1. **Add `EntryAnchor` and `ReturnAnchor`.** Today the loader derives both and
   warns. `Spawn_Platform` on Island_00 is the obvious home for the first.
2. **Anchor it in Studio and re-save.** All 699 parts are `Anchored = false`.
   The loader fixes this on every clone, which is correct as a safety net and
   wasteful as a habit.
3. **Walk it at `Scale = 0.1`** and tune from there.
