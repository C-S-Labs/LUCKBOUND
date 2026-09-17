# Hub prefabs

Authored pieces of the Crossroads. Rojo syncs this folder to
`ServerStorage.LuckboundPrefabs`, naming each instance after its file, and
`Util/PrefabLoader` clones the one a content table names.

**The file stem is the manifest key.** Rename the file and you have renamed the
asset.

## What the loader does for you

So the artist never has to do it in Studio after every delivery:

| | Why |
|---|---|
| **Anchors** every part | an FBX import leaves them loose, and a prefab that falls does it silently |
| **Scales** by `Prefab.Scale` | Studio's importer rarely lands at 1 m = 1 stud |
| **Pivots** onto the hub anchor | the model can sit anywhere in the source file |
| **Rebuilds the hierarchy** | empties do NOT survive FBX → Studio; the model comes back flat |
| **Paints** every part | Roblox imports untextured meshes grey; colour is content |

The contract with the artist is therefore just two things: **the part names**,
and **keeping animated parts separate** (not welded, not unioned).

---

# `HUB_FATE_ENGINE.rbxmx` — the Fate Engine

Delivered 2026-09-18. `FATE_ENGINE_DESIGN.txt` beside it is the artist's own
design note and is the reference for future texturing and animation work.

| | |
|---|---|
| Contents | **78 MeshParts** in one flat `Model` |
| Textures | **none** — flat shaded, untextured, as the house style requires |
| `SurfaceAppearance` | none, which is what keeps rarity reskinning alive |
| Anchored | all 78 on delivery |
| Contract parts | **all 46 present**, no `.001` suffixes |
| Scale as imported | **0.42×** → `Prefab.Scale = 2.3762` |

## Scale

Studio's FBX importer landed it uniformly small. Measured on arrival against
the build spec:

| | Imported | Spec | Factor |
|---|---|---|---|
| `Platform` width | 101.0 | 240 | 2.3762 |
| `Plinth` height | 1.26 | 3 | 2.3762 |
| `OuterRing` width | 48.48 | 115.2 | 2.3762 |
| `SpotAnchor` height | 126.29 | 300 | 2.3755 |

Uniform to four figures, so **one number corrects all of it**. Re-exporting 78
meshes to fix an importer setting is how a pipeline gets abandoned.

## What the artist added beyond the spec

The brief asked for a portal on a dais. The delivery is a **three-stage
machine**, and it is better:

```
CROWN   the portal, floating, ring centre ~102 studs up
AIR     LevitationCore — a faceted cyan-violet crystal, unsupported
GROUND  LevitationGenerator — stepped octagonal machinery, 9 profile levels
```

The visible air gaps are the point: energy holds it together, not struts. The
portal centre moved from the spec's 67 studs to 102 to make room, which is a
deliberate design change and is honoured rather than corrected.

Those extra parts (`LevitationGenerator*`, `GeneratorVents`,
`GeneratorEmitter`, `LevitationCoils`, `LevitationCore`, the platform and
plinth trim) are **static decoration**. The design note says so explicitly, and
nothing in code moves them.

## What is animated

| Part | Behaviour |
|---|---|
| `OuterRing` | spins about its own Z, `SpinSpeed = 1` |
| `InnerRing` | counter-spins, `SpinSpeed = -1.4`, **rarity tinted** |
| `PortalPlane` | transparency pulse, **rarity tinted**, carries light + particles |
| `Glyph1‥8` | **rarity tinted** |
| `Shard1‥6` | spin in place, **rarity tinted**, cycle with the featured rarity |

Rings work because a `MeshPart`'s pivot is its bounding-box centre, and a
symmetric ring's bbox centre is the hub of the wheel. That is why the art spec
insisted on symmetry about the origin — it was load-bearing, not decoration.

## Still to do

- **Lights and particles are created by code** (`PortalRig.attachEffects`),
  because emitters are not mesh data and cannot survive an FBX. Nothing for the
  artist to do; noted so nobody adds them in Studio and gets duplicates.
- **Walk it.** The Engine has never been seen in-game at this scale.
