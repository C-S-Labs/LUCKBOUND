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

So collision is granted to **57 of 225 parts**: the floor, the four decks, the
four walkways and their kerbs, every stair flight, the training yard floor,
and freestanding single-volume props — pillars, rocks, tree trunks, shrines,
the monument, the fountain. Everything else is scenery you walk through.

**None of this is verified in Studio.** It is the safe half of a choice that
cannot be checked headlessly. If a walk shows a railing that ought to stop
you, the fix is one `CollisionFidelity` line on that entry in
`Content/Hub/Crossroads`, never `CanCollide` on its own.

## Paint coverage

**225 of 225 parts resolve to a paint rule**, verified against the delivered
file rather than assumed. 184 style keys, resolved by longest prefix.

The export left `.001`-style suffixes on duplicated objects
(`District_Archive_Dome.001`, `District_Shop_DisplayGoods.023`,
`Walkways_Banners.010`). Prefix matching absorbs them, so they cost nothing —
but note there is **no plain `District_Archive_Dome`**, so nothing may require
one by exact name.

## The Expedition Gate has no gate

The authored south district is a **market**, because the brief asked for the
hub that the portal-as-entry direction wants. That amendment has not landed,
so expedition entry still runs through `EXPEDITION_GATE` and still has to work
today.

The Gate therefore keeps its anchor and its `ENTER` prompt and **loses its
art** — no portal rig is drawn on top of the stalls. The prompt sits at the
head of the market stairs, at `(0, 14, 250)`, measured:

```
stairs           218.5
deck near edge   235.0
prompt           250.0
entrance pylons  248.0
stalls begin     256.0
```

When the amendment lands, that whole arrangement goes away with the district.

## Still to do

- **Walk it.** Never seen in Studio. In priority order: does the floor hold,
  do the stairs climb, can you reach the market prompt, and does anything
  invisible stop you.
- **Profile it.** 225 MeshParts replace ~436 primitives, but mesh data is
  heavier to replicate than a `Part`, and 57 generated collision hulls are new
  work at load.

---

# `HUB_BACKDROP.rbxm` — the mountain horizon

Delivered 2026-09-18, alongside the hub and **authored in the same Blender
scene** — which is why it takes the same scale and the same yaw, and why
registering both from the same point in that scene puts them concentric rather
than merely near each other.

| | |
|---|---|
| Contents | **4 MeshParts** in one flat `Model` |
| Scale | **2.0**, same as the hub |
| Span | 2048 → **4096 studs**, against `HubLayout.VisualExtent` 4000 |
| Height | 452 → **904 studs**, base 68 studs below the plaza deck |
| Collision | **none** — nothing out there is walked on |
| Contract | none; nothing in the game looks it up |

Binary `.rbxm` rather than `.rbxmx`. Rojo syncs both, and the file stem is
still the manifest key.

## How it registers

There is no `EngineReserve` out here, so it registers from the largest mesh:

```
AnchorPart   = "Backdrop_Mountain"
AnchorOffset = (-15.3538, -157.2021, -34.9448)   -- source units
```

That offset is the vector from that mesh's centre to **the hub centre in the
shared source scene**. The check that it is right: both models' ground planes
(source `Y = 0`) then land on the same world height, `-68.45`. They agree to
four decimals, which is the evidence for the same-scene claim and is asserted
by test.

| Part | Source size | Source centre |
|---|---|---|
| `Backdrop_Foothills` | 1171.40 × 277.73 × 1107.97 | (75.37, 138.87, -124.31) |
| `Backdrop_Mountain` | 2048.00 × 382.85 × 1924.12 | (75.82, 191.43, -61.40) |
| `Backdrop_MountainCap` | 1795.94 × 219.13 × 1656.22 | (87.69, 342.31, -25.62) |
| `Backdrop_Spires` | 996.57 × 296.03 × 969.98 | (102.18, 148.01, -88.06) |

All four arrived with identity rotation and their base at source `Y = 0`.

**Note the name collision.** `HUB_CROSSROADS` also contains five
`Backdrop_*` meshes — `GroundIslets`, `Rocks`, `TreeCanopies`, `TreeTrunks`,
`Crystals` — which are the *ground skirt under the plaza*, not the horizon.
They are painted from the shell's table; these four from the backdrop's. Two
tables, two models, no overlap in practice, but the prefix is shared and worth
knowing about before adding a `Backdrop_` rule to either.
