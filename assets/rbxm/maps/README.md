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

**v2, delivered 2026-09-17.** The Blender scene imported into Studio and saved
back out as a Roblox XML model.

| | |
|---|---|
| Format | `.rbxmx` (XML) — readable from the repo, which is the point |
| Size | 6.6 MB |
| Contents | **925 MeshParts** in one flat `Model` |
| Materials | **429 `SurfaceAppearance`** objects — PBR, not flat colour |
| Mesh data | every part carries a real `rbxassetid://` MeshId |
| Anchoring | ✅ **all 925 anchored on delivery** |
| Scale | ✅ **play scale — `PrebuiltMap.Scale = 1.0`** |
| Layout | 8 islands, 16 satellites, 6 railed bridges, 1 sky temple |

## Measured on arrival

Against a 5-stud R6 character, and at `WalkSpeed = 32`:

| | Studs | Reads as |
|---|---|---|
| Tree (trunk + crown) | 28 | 5.6 person-heights |
| Waystone + cap | 24 | 4.8 |
| Temple doorway | 53 | 10.6 — a cathedral door |
| Temple columns | 62 | 12.4 |
| Temple floor | 267 × 164 | about a hub district platform |
| Smallest island (`Island_00`) | 228 × 180 | ~7 s to cross |
| Largest island (`Island_07`) | 428 × 340 | the temple's plateau |
| Arrival → temple | 2,277 | **71 s one way**, 142 there and back of 300 |

`tests/cases.luau` asserts the *relationships* these imply — the round trip
fits the expedition, an island is at least as roomy as a hub district, a
doorway is grand and not absurd. It does not assert the numbers themselves,
because a re-delivery changes them.

> **Note for a re-delivery:** the `Scale_Reference` R6 proxy in this version
> measures 13.2 studs tall (legs 5 + torso 5 + head 3.2) against a real 5. The
> rest of the scene reads correctly at 1.0, so the proxy is a loose stand-in
> rather than a live reference. Worth tightening if it is meant to be the
> yardstick — measure a doorway and a tree too, never the proxy alone.

## Why this world is prebuilt

It was going to be eight chunks. Measuring the delivery settled it the other
way: **the scene is a composed traverse, not a set of interchangeable pieces.**

- **It climbs.** The eight island meadows rise monotonically, y 61 → 151.
- **Each bridge is built for its own gap.** Six `BridgeGolden_NN` assemblies —
  planks, posts, upper and lower rails, underframe, caps — each spanning one
  specific pair at that pair's height.
- **The islands are individually themed.** `AI_Island01_Centerpiece`,
  `AI_Island03_ArchPier`, `AI_Island04_Gnomon`, `AI_Island05_GroundCrystal` —
  v2 leaned *further* into composition, not less.
- **It builds toward the temple.** Islands grow 228 × 180 at the arrival shelf
  to 428 × 340 under the Sky Temple.
- **Paths are laid across it.** `IslandPath_01`–`06` gravel runs join each
  island's bridgeheads.

Shuffle the islands and every one of those breaks. The socket grammar is not
wrong — this art is simply not modular, and making it modular would mean
re-authoring it with identical gaps, heights and rims.

## Still to do on this file

1. **Add `EntryAnchor` and `ReturnAnchor`.** Today the loader derives both and
   warns on every entry. `Spawn_Platform` on Island_00 (44 × 44, at the
   colonnade) is the obvious home for the first; somewhere on the temple
   plateau for the second.

That is the whole list. v2 arrived anchored and at scale.
