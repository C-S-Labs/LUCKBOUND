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
| **Rotates** by `Prefab.YawDegrees` | an FBX carries the exporter's compass, not the game's |
| **Places** by `Prefab.AnchorPart` | a named part registers the model; a pivot is invisible metadata an FBX chain can mangle |
| **Pivots** onto the hub anchor | when no `AnchorPart` is named — the model can sit anywhere in the source file |
| **Rebuilds the hierarchy** | empties do NOT survive FBX → Studio; the model comes back flat |
| **Paints** every part | Roblox imports untextured meshes grey; colour is content |
| **Sets collision** from the paint table | an imported mesh ships no `PhysicsData`, so every hull is generated — see the Crossroads section |

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

---

# `HUB_CROSSROADS.rbxmx` — the hub itself

Delivered 2026-09-18, built from `docs/CROSSROADS_BLENDER_PROMPT.md`. This is
the plaza the Fate Engine stands on, and it replaces the generated blockout
wholesale.

| | |
|---|---|
| Contents | **225 MeshParts** in one flat `Model` |
| Textures | **none** — flat shaded, untextured, as the house style requires |
| `SurfaceAppearance` | none |
| Anchored | all 225 on delivery |
| Contract parts | **all 10 present** |
| Scale as imported | **0.5×** → `Prefab.Scale = 2.0` |
| Compass | north arrived at **+Z** → `Prefab.YawDegrees = 180` |

## Scale — 2.0, and it is exact

Studio's FBX importer halved it. Measured on arrival against the brief, on six
independent dimensions:

| | Imported | Brief | Factor |
|---|---|---|---|
| `EngineReserve` width | 23.000 | 46 | 2.000 |
| `Walkway_North` width | 22.000 | 44 | 2.000 |
| `Walkway_North` thickness | 0.750 | 1.5 | 2.000 |
| `Walkway_North` length | 190.000 | 380 | 2.000 |
| District deck thickness | 7.000 | 14 | 2.000 |
| District ring radius | 200.000 | 400 | 2.000 |

**Six agreeing measurements is what makes one number the right correction.**
Re-exporting 225 meshes to fix an importer setting is how a pipeline gets
abandoned.

## The compass was 180° out, and that is the exporter, not the modeller

The brief put north at Blender `+Y`. The FBX round trip landed it at Roblox
`+Z`. `GameConfig.HubLayout.Anchors` has always put north at `-Z`.

Confirmed as a **pure rotation, not a mirror**: all four districts are exactly
negated in both X and Z, and every one of the 225 parts arrived with an
identity rotation. A mirrored delivery would have needed a re-export. This one
needed a number.

## Registration — by part name, not by pivot

The artist set the model pivot correctly: it landed on the hub centre at floor
level, `(60.4658, 34.2238, -96.3400)`, to four decimals. It is still not what
the loader uses.

A pivot is invisible metadata, and invisible metadata is exactly what a
Blender → FBX → Studio → `.rbxm` chain mangles quietly. `EngineReserve` is a
**named part in the contract** — visible in the file, already the artist's
obligation, and the one object in the scene whose entire purpose is to mark
this point. Its centre sits half its own height above the deck, so:

```
AnchorPart   = "EngineReserve"
AnchorOffset = (0, -0.5, 0)      -- source units
```

## Where the delivery differs from the brief

None of these are faults, and none needed fixing. Recorded so the next reader
does not go looking for a bug.

| | Brief | Delivered (at Scale) |
|---|---|---|
| Plaza diameter | 1150 | **1305** |
| `Processional_South` width | 72 | **44** (same as the other three) |
| District footprints | 210–320 | **300–400** (≈1.25–1.4× larger) |
| Pillar ring radius | 520 | **640** |

The plaza grew but still reaches under the furthest district edge (600 studs
against a 652-stud radius), and still covers `HubLayout.HubDiameter`. Both are
asserted by test. The processional is no longer wider than the walkways it
sits beside — a loss of emphasis on the spawn approach, not a defect.

## Collision — why so little of it is on

**MEASURED: all 225 parts ship with an empty `PhysicsData` and no
`CollisionFidelity`.** Roblox therefore generates a hull for each at `Default`
fidelity when it loads, and `Default` is coarse enough to **fill small
openings**.

A great many of these meshes are several separate objects merged into one:
eight columns in a ring, four archways, a pair of flanking guardians, a
parapet that circles the whole plaza. A filled hull on any of those is an
invisible wall exactly where players walk:

| Mesh | What a filled hull does |
|---|---|
| `Walkways_Gateways` | seals all four walkway mouths |
| `Processional_South_Guardians` | seals the spawn approach |
| `Plaza_RimParapet` | lays a 5.8-stud slab across the entire floor |
| `District_Archive_Columns` | fills the rotunda |
| `District_Shop_EntrancePylons` | seals the market entrance |
| `District_Training_Wall` | fills the yard |

That is the same class of bug as the `CylinderMesh` that once left the hub
with no floor, and it is invisible in exactly the same way.

### What the first walk changed — 2026-09-18

The first pass granted collision to only **57 of 225** parts and left every
merged or hollow mesh pass-through. That was the safe half of a choice that
could not be checked headlessly, and the walk found its cost: **players sank
into the flanks of district platforms and walked through railings.**

Collision now covers **91 of 225**, and **30 of those carry an explicit
`CollisionFidelity = PreciseConvexDecomposition`** — precisely the meshes
listed above, where a `Default` hull would seal the opening that makes the
piece the shape it is.

| | Fidelity | Why |
|---|---|---|
| Floors, decks, walkways, kerbs, stairs, yard | `Default` | flat slabs; a coarse hull is exactly right, and cheap |
| Platform skirts | `Default` | solid frustums under each deck — the piece players were sinking into |
| Freestanding props (pillars, rocks, trunks, shrines, monument, fountain) | `Default` | filling their own volume is correct |
| Arches, colonnades, balustrades, walls, pylons, stalls, seating, dummies, racks | **`PreciseConvexDecomposition`** | the openings are the point |
| Everything else (banners, flames, runes, glows, roofs, signs, canopies, islands, horizon) | — | no collision at all |

`PreciseConvexDecomposition` is a real runtime cost, computed at load and
cached per mesh asset. It is spent on 30 parts deliberately rather than
granted by default, and it is the **only** correct way to make one of these
solid — `CanCollide` alone would wall off a route.

### `CollisionFidelity` is baked into the file, not set at runtime

**It cannot be assigned from a script.** It is plugin security, exactly like
`MeshId`, and writing it throws *"The current thread cannot write
'CollisionFidelity' (lacking capability Plugin)"*. That exception took down
`PrefabLoader.build`, which took down `HubBuilder.build`, which meant boot
stopped at 9/11 and **the entire hub failed to appear**. One property.

It is a *serialized* property, so the value lives in the `.rbxmx`:

```xml
<token name="CollisionFidelity">3</token>   <!-- PreciseConvexDecomposition -->
```

Baked into the 30 parts listed above, and verified by reparsing the file. The
`CollisionFidelity` field in `Content/Hub/Crossroads` is still the place to
read what a piece is *supposed* to be — the loader now **checks** the asset
agrees and warns by name when it does not, rather than trying to set it.

**If a re-delivery arrives, the bake has to be redone.** A fresh export from
Studio carries no `CollisionFidelity`, so every one of those 30 parts would
silently drop to `Default` — the loader's warning is what catches that.

## Paint coverage

**225 of 225 parts resolve to a paint rule**, verified against the delivered
file rather than assumed. 184 style keys, resolved by longest prefix.

The export left `.001`-style suffixes on duplicated objects
(`District_Archive_Dome.001`, `District_Shop_DisplayGoods.023`,
`Walkways_Banners.010`). Prefix matching absorbs them, so they cost nothing —
but note there is **no plain `District_Archive_Dome`**, so nothing may require
one by exact name.

## The Expedition Gate is gone entirely

The authored south district is a **market**. The first pass kept an invisible
`ENTER` prompt on it so expedition entry still worked; the walk rejected that
— *"Verdant Valley teleport remains in shop area, this should not be here"*
— and the Fate Engine's portal takes the job instead.

So the authored hub now builds **no gate anchor and no gate prompt at all**,
and `ensureContract` no longer puts one back either (it would have resurrected
the prompt the moment anyone saved the built hub into the place).

**What this costs, stated plainly:** until the Engine carries entry, there is
no in-world way into an expedition. `ExpeditionSystem` already tolerates a
missing anchor — it warns that entry is remote-only and carries on — so
`/enter` still works for testing and nothing else breaks. A test pins the
absence so it cannot be closed by accident.

## The Fate Engine sits flush on it

Measured: the Engine's `Platform` top face is **1.934 studs above its model
pivot** at Scale 0.464, while the authored walkways' top face is
`WalkwayRaise` (1.5). The dais was therefore proud of every path meeting it,
and the walk asked for one continuous surface. `FateEngine.Prefab.Offset`
lowers the model by the difference, derived rather than typed:

```lua
Offset = Vector3.new(0, GameConfig.HubLayout.WalkwayRaise - 1.934, 0)
```

Note this makes the dais flush with the **walkways**, which stand 1.5 studs
above the plaza by design. Crossing the open plaza to the Engine still has
that one low step — it is the walkway's step, not the dais's.

## Where players arrive

A ring of **8 invisible `SpawnLocation` pads at radius 34**, just clear of the
dais (23.4), each facing the Engine. `GameConfig.HubLayout.SpawnRing`.

The single pad 250 studs down the processional is gone: it meant every player
began with a long walk to the only interactive thing in the game. Eight pads
cover the four walkway mouths and the four diagonals, so several players can
arrive at once without stacking.

`HubBuilder` also removes the place's default `Baseplate` and `SpawnLocation`
at boot. The Baseplate sits at Y 0 — exactly where the authored plaza's top
surface is — so it z-fights the floor and extends past it.

## Still to do

- **Walk it again.** The collision restoration, the flush dais, the spawn ring
  and the colour lift are all unverified.
- **Profile it.** 225 MeshParts replace ~436 primitives, mesh data is heavier
  to replicate than a `Part`, and there are now 91 generated collision hulls —
  30 of them precise decompositions — as new work at load.
- **Minor, accepted:** the walkways clip slightly into the district stair
  flights. Authored geometry overlapping authored geometry; fixing it means a
  re-export, and the walk called it minimal.

---

# `HUB_BACKDROP.rbxm` — the mountain horizon

Delivered 2026-09-18, alongside the hub and **authored in the same Blender
scene** — which is why it takes the same scale and the same yaw, and why
registering both from the same point in that scene puts them concentric rather
than merely near each other.

| | |
|---|---|
| Contents | **4 MeshParts** in one flat `Model` |
| Used as | a **source of one mesh**, never placed whole — see below |
| Collision | **none** — nothing out there is walked on |
| Contract | none; nothing in the game looks it up |

Binary `.rbxm` rather than `.rbxmx`. Rojo syncs both, and the file stem is
still the manifest key.

| Part | Source size | Source centre |
|---|---|---|
| `Backdrop_Foothills` | 1171.40 × 277.73 × 1107.97 | (75.37, 138.87, -124.31) |
| `Backdrop_Mountain` | 2048.00 × 382.85 × 1924.12 | (75.82, 191.43, -61.40) |
| `Backdrop_MountainCap` | 1795.94 × 219.13 × 1656.22 | (87.69, 342.31, -25.62) |
| `Backdrop_Spires` | 996.57 × 296.03 × 969.98 | (102.18, 148.01, -88.06) |

All four arrived with identity rotation and their base at source `Y = 0`.

## It is built as a ring of clones, not placed whole

**Placing the delivered model at the origin failed three times**, and the
reason is worth recording because it is not obvious:

| Scale | Ring across | Result |
|---|---|---|
| 2.0 (as authored) | 4096 | *"far too large"* |
| 1.0 | 2048 | clipped through the plaza |
| 3.0 | 6144 | **still clipping** |

The distance from the hub to the nearest peak is a property of the **mesh
geometry**, which lives in a Roblox asset id — nothing in this repo can
measure it. So every scale was a guess. And scaling cannot separate the two
things that matter anyway:

> A uniform scale moves the ring closer as it shrinks, so height and radius
> fall together and the mountains subtend **the same angle from the hub's
> centre at any scale.** Scaling cannot make them look smaller from where
> players stand. All it changes is how far away they are.

So the horizon is now **built**: one chunk mesh, cloned around a circle at a
radius we choose. Distance stops being emergent and becomes a number — and a
number is testable.

```
Part    Backdrop_Mountain     Count   14        Radius  2400
Scale   1.0                   BaseY   -68.4475  Seed    20260918
```

Every one of those is chosen against measured hub geometry:

| | Studs |
|---|---|
| Plaza edge | 653 |
| Hub ground skirt | 1097 |
| Chunk half-width | 1024 |
| **Band near face** | **1376** |
| Band far face | 3424 |
| `FogEnd` | 4400 |

which leaves **723 studs of clear sky** between the crossroads edge and the
mountains — inside the 500–1000 the owner asked for — and **279 studs** of
clearance past the hub's own ground skirt. The far face stays inside the fog,
so the range fades rather than ending in a hard line.

**The chunks are meant to overlap.** 14 chunks of 2048 across a 15080-stud
circumference is 1.9× coverage. A single chunk is a ragged mass, and
overlapping rotated copies is what turns a repeated mesh into a continuous
range instead of a ring of identical lumps. Yaw and scale are jittered from a
seeded `Random`, so every server shows one skyline rather than a new one each
boot — the same rule the floating islands follow.

Every number above is asserted by test, including the gap, the ground
clearance, the fog, the coverage ratio, and that the chunks stand on the same
ground plane as the plaza.

**To retune it, change `Radius`** — not `Scale`. `Scale` changes how big each
massif is; `Radius` is the distance, which is what every complaint about this
horizon has actually been about.

