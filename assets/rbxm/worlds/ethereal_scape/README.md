# Ethereal Scape — authored environment

`EtherealScape_Environment.rbxmx` — the Blender scene imported into Studio and
saved back out as a Roblox XML model. Delivered 2026-09-16.

## What is in it

| | |
|---|---|
| Format | `.rbxmx` (XML) — readable from the repo, which is the point |
| Size | 4.3 MB |
| Contents | **699 MeshParts** in one `Model`, flat (no sub-grouping) |
| Mesh data | **every part carries a real `rbxassetid://` MeshId** — the geometry is uploaded and lives on Roblox's CDN |
| Names | preserved from Blender: `Island_00_Meadow`, `Temple_Column`, `Waystone_03`, `Path_Bridge`, `Spawn_Column`, `R6_Torso` … |

**The upload half of the pipeline worked.** 699 meshes on the CDN, referenced
by id, names intact. That is the expensive part and it is done.

## What has to change before it can be used

Recorded here rather than fixed in place: editing 699 parts by hand in XML is
how you corrupt a 4 MB file. These are Studio-side fixes on the next pass.

### 1. Everything is `Anchored = false` — all 699 parts

The whole environment falls the instant the game runs. This is the one that
must be fixed before it is dropped into a live Workspace.

In Studio: select the Model → **Model tab → Anchor**. One click, all children.

### 2. It is one flat Model, not eight islands

`Content/Chunks/EtherealScape.luau` expects **8 separate pieces** that the
generator arranges — `ES_ARRIVAL_SHELF`, `ES_SPAN_STRAIGHT`, … `ES_SKY_TEMPLE`.
This file is a single pre-arranged scene.

Both are legitimate; they are different products:

- **As one scene** it is a hand-authored map. It would need
  `ES_ENVIRONMENT_FULL` in the manifest and a loader that places it whole —
  and Ethereal Scape's chunk kit stops being used.
- **As eight pieces** it feeds the existing generator. Group the parts by
  island in Studio, save eight `.rbxmx` files, and each becomes a chunk.

**This is a design decision, not a bug.** See `docs/STATUS.md`.

### 3. No `PrimaryPart`

The Model has none, so there is no defined point to position it from.
Set one (an island base, or a deliberate origin marker) before delivery.

### 4. Scale is ~12x off the reference — needs the modeller to confirm

The scene carries its own R6 proxy in `Scale_Reference`, and this is exactly
what it was for:

```
R6_Leg   22.6 studs tall
R6_Torso 22.6
R6_Head  14.4
         -----
         59.6 studs total

A real Roblox R6 character is 5 studs tall.
```

So the rig imported **~11.9x** larger than a character. Either the scene is 12x
oversized, or the R6 proxy was built 12x too large in Blender and the scene is
fine. **The file alone cannot say which**, and the answer changes everything
downstream:

| If… | Then an island is | Against the kit's 512–1024 studs |
|---|---|---|
| the scene is 12x oversized | ~90 × 70 studs | far too small |
| the proxy is wrong, scene is right | ~1090 × 860 studs | about right |

Measured island footprints as imported: `Island_00` is 1092 × 861, `Island_01`
is 1229 × 909 — which sit comfortably in the kit's range and suggest **the
scene is right and the R6 proxy is the thing that is 12x too big.**

Confirm with the modeller before rescaling anything. Rescaling the wrong one
means re-uploading 699 meshes.

### 5. Layout spread

Parts span **11,500 studs in X** but only 4,350 in Z, and the X distribution is
continuous rather than clustered — so it is a long strip, not a stray object.
Expected if the islands were laid out in a line; worth a look in Studio.
