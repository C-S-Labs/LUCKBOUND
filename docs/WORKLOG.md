# LUCKBOUND — Work Log

**Append-only session history.** One entry per working session: what was done,
what it changed, where it stopped, and what comes next.

> **Reading this in a new conversation?** Read the **latest entry** for where
> things stopped, then `STATUS.md` for current state. Do not read the whole
> file — only the most recent entry is load-bearing.

**Writing an entry?** Add it at the **top**, under the template. Never edit or
delete an older entry; if something turned out wrong, say so in a newer one.

---

## Template

```
## Session N — YYYY-MM-DD — <short title>
**Merged:** PR #n, #n   **Tests:** N passing   **Head:** <sha>

### Done
- …

### Decisions made
- …

### Stopped at
…

### Next
1. …
```

---

## Session 12 — 2026-09-18 — The authored Fate Engine is in the game

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 305 passing (was 295)

### Done

The Fate Engine was built in Blender against Session 11's contract and
delivered as `.rbxmx`. It is now the centrepiece of the Crossroads.

**The delivery passed the contract clean.** 78 MeshParts, all 46 required
names present, no `.001` suffixes, no `SurfaceAppearance`, everything
anchored, untextured. The naming contract worked exactly as designed — that
is the first delivery on this project that needed no correction to its
structure.

**Two things needed fixing on the way in, neither the artist's fault:**

- **Scale.** Studio's FBX importer landed it at 0.42x, uniformly: `Platform`
  101.0 against a spec 240, `Plinth` 1.26 against 3, `OuterRing` 48.48 against
  115.2, `SpotAnchor` 126.29 against 300 — the same factor to four figures. One
  number in content (`Prefab.Scale = 2.3762`) corrects all of it. Re-exporting
  78 meshes to fix an importer setting is how a pipeline gets abandoned.
- **Hierarchy.** Blender empties do NOT survive an FBX round trip, so the model
  came back flat while `PortalRig` and `HubEffects` walk a tree. The loader
  rebuilds `EngineRig` / `RuneRing` / `CrystalShards` / `RuneInlay` by name
  rather than asking for 78 parts to be hand-grouped in Studio after every
  delivery.

**New `Util/PrefabLoader`** — the hub's counterpart to `PrebuiltLoader`. Clones,
anchors, scales, pivots, regroups and paints. It also reports any contract part
it could not find, rather than going quietly dead.

**`HubBuilder.buildFateEngine` now prefers the prefab** and draws no portal
primitives when it loads. The blockout path underneath is untouched and still
runs on a place with no Rojo — no flag day in either direction.

**Two silent no-ops fixed in `PortalRig`**, both predicted in Session 11 and
both real:

- `setRarity` looped over `InnerRing`'s *children*. An authored ring is a
  single `MeshPart`, so the loop found nothing, coloured nothing, and errored
  nothing. The portal would simply have stopped responding to rarity.
- The spin driver required a `Center` attribute and `continue`d without one, so
  an authored ring would never have turned.

Both now handle a `BasePart` and a `Model` of segments.

**New `PortalRig.attachEffects`** gives an authored rig the point light and
particle emitter a generated one builds for itself. Emitters are not mesh data
and cannot survive an FBX, and without them the 2.5-second spin-up — build spec
§1.3's "single most important UX beat" — would have had nothing to ramp.

### Decisions made

- **Colour is applied in code, from content, not baked into the art.** The
  meshes import grey and that is the pipeline working, not a failure: the house
  style is flat colour with no textures. `Crossroads.FateEngine.PrefabStyles`
  maps part name to `Color`/`Material`/`Transparency`/`CanCollide` plus
  animation attributes, resolved by longest matching prefix so
  `Plinth_SideBand` can be gold while `Plinth` stays marble. Recolouring the
  Engine is now a data edit and a rejoin. Recorded in `ART_DIRECTION.md`.

- **The artist's three-stage machine is honoured, not corrected.** The brief
  asked for a portal on a dais; the delivery is a grounded generator, a
  suspended levitation core, and the portal floating at the crown, with visible
  air gaps that make energy rather than struts the explanation. That moved the
  portal centre from the spec's 67 studs to 102. The spec's number was a
  starting point and the design is better, so the code took the art's number.
  Their design note is saved beside the asset as `FATE_ENGINE_DESIGN.txt`.

- **The generator, core and coils are static.** The design note says explicitly
  that everything beyond the named contract is decorative unless the game adds
  behaviour. A rotating core would also have been caught by the shard rarity
  cycle and tinted away from its cyan-violet.

- **Ring pivots survived because the art spec insisted on symmetry.** A
  `MeshPart`'s rotation centre is its bounding-box centre, not the Blender
  origin — Roblox discards that. For a symmetric ring the two coincide, which
  is why "origin at the hub of the wheel" was written as a hard rule. It was
  load-bearing, not decoration.

### Stopped at

305 passing, syntax and forbidden-name scans clean, everything wired. **The
Engine has never been rendered.** No Studio pass has happened at all.

### Next

1. **Walk the Crossroads.** Watch for the dais landing flush with the walkways,
   the rings counter-rotating, the portal pulsing, and a `/roll` turning the
   inner ring, plane, glyphs and shards to the rolled rarity.
2. **The rest of the Crossroads** — owner-stated as the next day's work. The
   seam is proven now, so each further piece is a `.rbxmx`, a `Prefab` field
   and a paint table, with no new code.
3. Unchanged: walk Ethereal Scape v2, `EntryAnchor` / `ReturnAnchor`,
   Emberfall's kit, `UNCOMMON`'s colour.

---

## Session 11 — 2026-09-17 — The Fate Engine contract

**Branch:** `claude/zen-volta-cuhfyh`, restarted from `main` after #16 merged
**Tests:** 295 passing (unchanged — this session added no code)

### Done

- **Wrote `docs/FATE_ENGINE_BLENDER_PROMPT.md`** — a prompt for Claude Desktop
  driving Blender over MCP, which builds the Fate Engine to the exact contract
  the game already enforces. It is not a style brief: the part names in it are
  the API `PortalRig` looks up.

- **Corrected the prompt to low poly** after the owner flagged it. The first
  version was **lean but not low poly** — a 64-sided platform, 48x16 tori,
  "soft veining" marble, textures allowed on four of five materials, and a
  60,000-triangle ceiling. That is an optimisation budget, not a style. There
  was also no `Shade Flat` instruction anywhere, and a low-poly mesh with
  smooth shading reads as a high-poly mesh that went wrong.

  Now: 16-sided platform, octagonal plinth, 32x6 tori, hexagonal shards, flat
  shading mandatory, **no textures at all**, and a ceiling of 5,000 triangles
  against an expected ~1,800.

### Decisions made

- **Low poly and one palette are the hub-wide house style**, not a note on one
  asset. Recorded in `ART_DIRECTION.md` rather than only in the prompt, with
  the palette lifted from `Content/Hub/Crossroads.luau` so there is one source
  of truth. Ethereal Scape v2 is already built this way, so the hub matching it
  is what makes the game look like one game.

  The no-textures rule is style *and* mechanics: a `SurfaceAppearance`
  overrides a part's `Color`, and rarity reskinning works by setting `Color`.

- **Fixed a stale `ART_DIRECTION` defaults table** while establishing the
  palette beside it — it still read Brightness 2 / ClockTime 22, hub 1200,
  zone ring 420, five zone platforms. All superseded by the brightness pass,
  the de-scale and the Observatory's removal. Stale numbers next to a new
  palette would have been read as current by the next modeller.

- **The Fate Engine prefab replaces the WHOLE RIG, rings included.**
  Owner-directed. The alternative was a static shell with `PortalRig` still
  building the rings on top, which would have kept rarity reskinning for free.
  The owner wants exact art control instead.

  **What that costs, written down so it is not rediscovered:** `PortalRig` no
  longer *builds* this slot, it *drives* it. Every part `setRarity`,
  `playSpinUp`, `setActive`, `setIdle` and the spin loop look up by name must
  exist in the export, spelled exactly:

  `Plinth` · `OuterRing` · `InnerRing` · `PortalPlane` · `Rune1..8` ·
  `Glyph1..8` · `Shard1..6` · `Platform` · `Inlay1..16` · `SpotAnchor`

- **The rarity-tinted parts must ship untextured.** `InnerRing`, `PortalPlane`,
  the glyphs and the shards are recoloured on every roll by setting `Color`. A
  Roblox `SurfaceAppearance` overrides `Color` outright, so a PBR texture on
  any of them silently kills rarity reskinning **on the most visible object in
  the game**. The prompt spends a section on this because it is the failure
  that would ship looking fine and be found weeks later.

- **The plinth cap is restated as a rule, not a proportion.** 3 studs, hard.
  A character jumps ~7; the Gate shipped an 18-stud plinth once and walled its
  own portal off. The prompt says "monumental by being wide, never by being
  tall" for that reason.

### Stopped at

The prompt is written and committed. No code changed — the loader it implies
does not exist yet, deliberately: the contract is agreed first, the loader is
written against the first real file.

### Next

1. **Owner builds the Engine in Blender**, exports FBX, imports to Studio,
   saves `assets/rbxm/prefabs/FATE_ENGINE.rbxmx`.
2. **Then the hub prefab loader** — `assets/rbxm/prefabs/` → `ServerStorage` →
   `HubBuilder` clones into a slot, and `PortalRig` gains a "drive an existing
   rig" path beside its "build one" path. A mirror of `PrebuiltLoader`.
3. **Check the scale on arrival** against a real character *and* a doorway and
   a tree — never the reference rig alone. That is what put Ethereal Scape v1
   10x out.
4. Unchanged: walk Ethereal Scape v2, walk the hub, `EntryAnchor` /
   `ReturnAnchor`, Emberfall's kit, `UNCOMMON`'s colour.

---

## Session 10 — 2026-09-17 — Cutting the Observatory, and one map instead of eight chunks

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 295 passing (was 301)
**Note:** PR #13 and #14 are both merged. This work is unmerged and needs a new PR.

### Done

Two owner decisions, both structural, and the second one reversed a decision
made earlier the same session.

**1. The Global Observatory is gone.** Removed from `Content/Hub/Crossroads`
(the district), `Core/GameConfig` (its anchor), `Systems/HubBuilder`
(`buildObservatory` and `buildObservatoryApproach`, 108 lines, plus its
`ZONE_BUILDERS` entry), `Controllers/HubEffects` (the `IsOrrery` branch),
`Controllers/DebugCommands` (the teleport alias) and a stale comment in
`Util/Schema`. Nothing else referenced it — the district table really was the
only seam. The hub is four districts.

Seven tests named it by Id; they became one rule that holds for any district,
present or future: *no district reaches into the Fate Engine's platform.* That
is the property the staircase violated.

**2. Ethereal Scape ships as one authored map, not eight chunks.**

The session started by writing a script to split the delivered `.rbxmx` into
eight chunks, on the owner's instruction. Then the owner asked whether shipping
it whole would be easier, and measuring the file to answer that showed the
split was wrong. The script was deleted rather than left beside a working
alternative (CLAUDE.md rule 1).

**What the measurements said.** Four independent properties of the scene, all
from `assets/rbxm/maps/ES_ENVIRONMENT_FULL.rbxmx` itself:

- The eight island meadows **climb monotonically**, y 354 → 761, ~58 studs a
  step.
- The six `Path_Bridge` parts are **each cut to their own gap** — 714–833 studs
  long, each at its gap's specific height.
- The thirteen `Bridge_Landing` parts are **authored in matched pairs**,
  `_NN_0` and `_NN_1`, naming the two islands each bridge joins.
- The islands **grow toward the temple**: 1030 × 813 at the arrival shelf,
  1932 × 1535 under the Sky Temple.

Shuffle the islands and all four break at once. The bridges are the hardest
of the four: a bridge is one part spanning a gap, so nearest-centre assignment
tears each one onto a single side and leaves the far island with nothing to
land on.

**The seam that makes it data, not a special case.** A world declares EITHER a
chunk kit OR a `PrebuiltMap { AssetKey, Scale }`. Declaring both is a boot
error (`Schema.validateMaps`). New `Util/PrebuiltLoader` clones the scene,
anchors it, scales it and pivots it onto the stage. `ExpeditionSystem` gained
exactly **one branch**, and it reads `ExpeditionCore.hasPrebuiltMap(world)` —
never a world id. Adding another authored world changes no System.

Wired end to end: `assets/rbxm/maps/` → `ServerStorage.LuckboundMaps` (Rojo) →
`PrebuiltLoader`. The Ethereal Scape chunk kit and its eight `ES_CHUNK_*`
manifest entries were deleted; `ES_ENVIRONMENT_FULL` is now the world's only
asset entry.

**3. The scale question is answered, provisionally, and it reverses the
previous two sessions' guess.** Sessions 8 and 9 read the `Scale_Reference` R6
proxy at 59.6 studs (≈12× a real 5-stud character) and concluded the *proxy*
was wrong, because the islands measured 1030–1932 studs and that suited the
kit. Measuring the rest of the scene says otherwise — everything agrees with
the proxy rather than with Roblox:

| Object | Delivered | Against a 5-stud character |
|---|---|---|
| Temple doorway jamb | 239 studs | 48× a person |
| Tree | 126 | 25× |
| Waystone + cap | 117 | 23× |
| Colonnade column | 108 | 22× |
| Arrival → temple | 10,278 | 642 s of walking |

A 48-person-high doorway is a unit error, not a style. The scene is internally
consistent and uniformly ~10× oversized, so **one number fixes all of it**:
`PrebuiltMap.Scale = 0.1`. At that scale the traverse is 1,028 studs and 32
seconds one way, which sits comfortably inside the 300-second expedition.

**4. Same session, after a playtest: v2 of the scene, and `Scale = 1.0`.**

The owner walked the map at `Scale = 0.1` and reported it too small. The
modeller re-delivered the scene rebuilt at Roblox scale, and it arrived
better in three other ways too:

| | v1 | v2 |
|---|---|---|
| MeshParts | 699 | 925 |
| Materials | flat colour | 429 PBR `SurfaceAppearance` |
| Anchored on delivery | none | all 925 |
| Bridges | bare decks | `BridgeGolden_NN` — planks, posts, rails, underframe |
| Island paths | none | `IslandPath_01`–`06` gravel runs |
| Per-island theming | none | `AI_Island01_Centerpiece`, `AI_Island03_ArchPier`, … |
| Traverse | 10,278 studs (642 s) | 2,277 studs (**71 s** one way) |

`PrebuiltMap.Scale` is now `1.0`. The field stays at 1.0 deliberately: it is
the seam that made correcting v1 a one-line edit instead of a re-export, and
the next authored world will not arrive at play scale either.

**The v2 delivery also broke a test I wrote earlier the same session**, and
that is the lesson worth keeping. I had asserted that `Scale` matched the
ratio of the scene's R6 proxy to a real character — a number derived from
measurements of one specific file. The file was replaced four hours later and
the assertion became a liability. v2's proxy measures 13.2 studs against a
real 5, while the rest of the scene reads correctly at 1.0, so the proxy is a
loose stand-in and the assertion would have demanded `Scale = 0.379`.

Replaced with three relationships that survive a re-delivery:

- the round trip fits inside `DurationSeconds` with room to spare
- an island is at least as roomy as a hub district platform (**this is the
  one that catches "too small"** — "the walk fits" is satisfied by any
  sufficiently tiny scale)
- a doorway is between 1.5 and 20 person-heights (catches v1's 48×)

Same mistake as the `Plaza.Diameter == 1150` test recorded in build spec
§6.1, in a new outfit: *a test that asserts a measurement proves nothing once
the thing measured is replaced.*

### Decisions made

- **The Observatory was cut, not relocated.** Session 9 recommended moving it
  to a sixth compass point. The owner's answer was that its purpose was never
  clear, and with expeditions moving to separate places the hub becomes a
  lobby — a monument you climb on the way to nowhere is harder to justify in a
  lobby, not easier. Recorded in `BLUEPRINT_RECONCILIATION` as a deliberate
  deviation from §2.2's five zones, so nobody "restores" it.
- **Composed art ships whole; modular art ships as a kit.** Written up in
  `assets/README.md` as four questions answerable by measuring a file: do the
  pieces sit at the same height, are the gaps identical, are the pieces the
  same size, would shuffling them still read as the same place. Four yeses is
  a kit; any no is a map.
- **The chunk system was not weakened.** Verdant Valley still assembles, and
  every assembly test still runs against it. The Ethereal Scape kit's one real
  result — that the reserved-Kind rule produced boss gating on a second,
  independently authored vocabulary — is recorded in `MODULAR_MAPS.md` rather
  than lost with the kit.
- **`Scale` is data on the world, not a re-export.** Getting it wrong costs a
  one-line edit and a rejoin. Getting a chunk kit's `SizeX/Y/Z` wrong costs
  re-uploading meshes, which is the other half of why prebuilt won here.

### Stopped at

295 tests passing, syntax and forbidden-name scans clean, everything wired.
Nothing has been walked in Studio: the Observatory's removal, the hub
brightness pass and the entire prebuilt path are all untested on the ground.

### Next

1. **Walk Ethereal Scape v2.** Entry, lighting, timer and return are already
   proven on v1. What is new is 925 anchored PBR parts at play scale. Judge
   the traverse — 71 s one way, 142 there and back of 300. If it drags,
   `DurationSeconds` is the knob, not `Scale`.
2. **Walk the hub** — brightness, the non-colliding SpawnLocation, and the gap
   where the Observatory was. `TESTING.md` Test C3.
3. **Add `EntryAnchor` and `ReturnAnchor`** to the scene in Studio and anchor
   all 699 parts. Until then the loader guesses arrival from the bounding box
   and warns on every entry — it works, it is just not the modeller's choice of
   where you land. `Spawn_Platform` on Island_00 is the obvious home for the
   first.
4. **A chunk kit for Emberfall** — 15pp off the "rollable but not enterable"
   number, and the real second data point for the socket grammar now that
   Ethereal Scape's kit is retired.
5. **`UNCOMMON`'s colour still needs blessing**, and placeholder text and the
   UI pass are unchanged.

---

## Session 9 — 2026-09-16 — Unblocking the art pipeline

**Branch:** `claude/zen-volta-cuhfyh` (PR #13) · **Tests:** 301 passing (was 293)

### Done

The two bugs found by reading in Session 7, both of which would have bitten the
moment authored art was wired in, plus the brightness complaint that had been
open since Session 1.

- **`HubBuilder.meshOrNil` was silently broken.** It set `MeshPart.MeshId`
  directly, which Roblox permits only from the importer, inside a `pcall` — so
  it failed, warned, and fell back to a primitive. **Every `MeshId` seam in
  `Content/Hub/Crossroads` did nothing.** The symptom would have been "we
  uploaded the mesh and the game ignored it", with no error to chase. Now uses
  `AssetService:CreateMeshPartAsync`, which is what `Util/ChunkLoader` already
  used — the two seams had drifted apart.
- **An authored `Crossroads` disabled the contract, not just the geometry.**
  `build()` returned early as a single branch, taking the `RollAnchor`, the
  `GateAnchor` and its prompt, the `SpawnLocation` and `applyLighting()` with
  it. An artist naming a model `Crossroads` would have switched off rolling and
  expedition entry with no error. Geometry and contract are now separate:
  lighting always applies, `ensureContract` always runs, and it adds anything
  missing while warning loudly about what it had to add.
- **Hub brightness.** `ClockTime` 22 → 4.5, `Brightness` 2 → 2.6,
  `ExposureCompensation` 0 → 0.15, ambient lifted in luminance only.

### Decisions made

- **The contract is three named parts, and they live in one place.**
  `buildRollAnchor`, `buildGateAnchor` and `buildSpawn` were extracted from the
  three builders that used to own them inline, because *both* paths through
  HubBuilder now need them. Duplicating any one would let an authored hub drift
  from a generated one — which is exactly the class of bug being fixed.
- **`ensureContract` only adds invisible, non-colliding parts.** It changes
  behaviour and never appearance, so it can run against authored art without an
  artist ever seeing it interfere.
- **The darkness was `ClockTime`, not `Brightness`.** With the sun below the
  horizon there is no key light for `Brightness` to raise; turning it up blows
  out the neon and the portal glow while the stone stays flat. 4.5 puts the sun
  just above the horizon — a low raking pre-dawn light that still reads as
  night and keeps §2.3's purple sky. **The palette is untouched.**
- **The `SpawnLocation` is now non-colliding**, so it cannot be a 1-stud lip on
  the walkway it sits over.

### Stopped at

All three fixed, 301 green, nothing walked. Three changes are untested in
Studio: the Observatory approach from Session 6, the brightness pass, and the
non-colliding spawn.

**The art pipeline is now unblocked** — an uploaded mesh id in a `MeshId` seam
will actually be used, and authored geometry can no longer silently break the
game.

### Next

1. Walk the hub once (`TESTING.md` Test C3) — three untested changes.
2. Answer the two open design questions: the Observatory's purpose, and
   one-scene-vs-eight-chunks for Ethereal Scape.
3. Confirm the Ethereal Scape scale with the modeller.
4. Wire the authored asset in, which now has nothing blocking it.

---

## Session 8 — 2026-09-16 — First authored asset lands

**Branch:** `claude/zen-volta-cuhfyh` (PR #13) · **Tests:** 293 passing · no code change

### Done

- **`assets/rbxm/worlds/ethereal_scape/EtherealScape_Environment.rbxmx`** — the
  Ethereal Scape Blender scene, imported to Studio and saved back as XML. The
  first authored art in the repo.
- A README beside it recording exactly what is in the file and what has to
  change before it can be used.

### What the file actually is

**699 MeshParts in one flat Model, every one carrying a real
`rbxassetid://` MeshId.** The geometry is uploaded and on Roblox's CDN; Blender
names survived (`Island_00_Meadow`, `Temple_Column`, `Waystone_03`,
`Path_Bridge`, `R6_Torso`). The expensive half of the pipeline worked on the
first attempt, and `.rbxmx` meant all of this could be read and verified from
the repo rather than taken on trust — which is the whole argument for asking
for XML.

### Four things to fix, none of them a repo problem

1. **All 699 parts are `Anchored = false`.** The environment falls the moment
   the game runs. One click in Studio on the Model.
2. **Flat Model, not eight islands.** The chunk kit expects 8 separate pieces.
   This is one pre-arranged scene. Both are legitimate products — see the
   decision below.
3. **No `PrimaryPart`**, so there is no defined point to position it from.
4. **The R6 proxy reads 59.6 studs tall where a character is 5.** Roughly 12x.
   Either the scene is oversized or the proxy is — the file cannot say which.

### The scale question, and why the reference earned its place

The R6 rig in `Scale_Reference` did exactly the job it was put there for: it
caught a 12x discrepancy on the first delivery, before anyone built a kit
around the wrong numbers.

The evidence points at **the proxy being wrong, not the scene**: measured
island footprints are 1092 x 861 and 1229 x 909 studs, which sit comfortably
inside the chunk kit's 512-1024 range. A 12x reduction would make them ~90
studs — smaller than a hub walkway. **Confirm with the modeller before
rescaling anything**; getting it backwards means re-uploading 699 meshes.

### Decision needed: one scene, or eight chunks?

Not a bug — a fork in the road, and it decides whether Ethereal Scape's chunk
kit survives:

- **One scene** — a hand-authored map. Needs `ES_ENVIRONMENT_FULL` in the
  manifest and a whole-scene loader. The generator stops being used for this
  world, and the socket grammar it proved goes unused here.
- **Eight chunks** — group by island in Studio, save eight `.rbxmx` files, feed
  the existing generator. Keeps seeded variety and the Waystone-gate property.

The kit was built for the second. The file as delivered is the first.

### Stopped at

File placed and documented. No code touched, and deliberately so: the two
loader bugs from Session 7 (`meshOrNil`, the `Crossroads` guard) are still
open, and both must land before any of this can be wired in.

### Next

1. Confirm the scale question with the modeller.
2. Decide: one scene or eight chunks.
3. Fix `meshOrNil` and the `Crossroads` guard (Session 7's list).
4. Wire `assets/rbxm` into `default.project.json` once the shape is settled.

---

## Session 7 — 2026-09-16 — Modeller handoff, and the art seam

**Branch:** `claude/zen-volta-cuhfyh` (PR #13) · **Tests:** 293 passing · no code change

### Done

- Observatory staircase confirmed fixed in Studio by the owner.
- **`docs/MODELLER_HANDOFF.pdf`** — a 7-page brief to hand to an artist:
  deliverable formats, the six export settings that matter, the R6 scale check,
  how to build a prefab whose parts can be animated, the reserved `Crossroads`
  name, and a spec sheet of exact part names and stud dimensions for the Fate
  Engine and the Expedition Gate.

### Decisions made

- **Ask for `.rbxmx` (XML), not `.rbxm` (binary).** Both work in the game; only
  the XML one can be *read* from this side. With XML the wiring code is written
  against the part names actually in the file; with binary it is written blind
  against a list, and a typo surfaces at runtime instead of at review.
- **The spec sheet's numbers are derived from `GameConfig.Portal`, not typed by
  hand**, so they cannot drift from what the code expects. If a scale changes,
  regenerate the PDF rather than editing it.
- **The plinth's 3-stud cap is in the brief as a hard constraint**, with the
  reason: an earlier build scaled it to 18 and walled the portal off entirely.
  An artist told only "make it monumental" would rebuild that bug in mesh form.

### Open — two things that will break when art lands

Both are mine to fix, both were found by reading rather than by a test:

1. **`HubBuilder.meshOrNil` is broken.** It sets `MeshPart.MeshId` at runtime,
   which Roblox does not permit. It is wrapped in a `pcall`, so all nine
   `MeshId` seams in `Crossroads.luau` **silently fall back to primitives** —
   an authored mesh would appear not to work, with no error. `ChunkLoader`
   already does it correctly via `AssetService:CreateMeshPartAsync`; the fix is
   to bring `meshOrNil` in line, plus a prefab-clone path for `.rbxmx`.
2. **A hand-built `Crossroads` disables more than the hub.** `HubBuilder.build`
   returns early if `Workspace.Crossroads` exists, which also skips the
   `RollAnchor`, the `GateAnchor` and its prompt, the `SpawnLocation` and
   `applyLighting()` — so rolling and expedition entry break silently. The
   per-piece `MeshId` seam is the intended path; wholesale replacement needs a
   guard that still builds the contract parts.

### Stopped at

Docs only, no code touched. The two items above are the first work of the next
session, and both should land **before** the first authored asset arrives.

### Next

1. Fix `meshOrNil`, add the prefab path, wire `assets/rbxm` into
   `default.project.json` when the first `.rbxmx` lands.
2. Guard `HubBuilder.build` so authored geometry cannot silently remove the
   anchors, spawn and lighting.
3. Teach `PortalRig` to **adopt** an authored rig rather than only generate one,
   keeping the same attribute contract (`SpinSpeed`, `Center`, `State`).
4. Everything from Session 6: Observatory purpose, island upload, hub
   brightness, `UNCOMMON` colour, Emberfall kit.

---

## Session 6 — 2026-09-16 — The loop closes, and the staircase moves

**Branch:** `claude/zen-volta-cuhfyh` (PR #13) · **Tests:** 293 passing (was 291)

### Done

**The core loop was walked end to end in Studio and it works.** Roll → Gate →
generated map → return → Fate. From the owner's log:

```
[Expedition] Setsuru -> ETHEREAL_SCAPE  seed 107807269  5 chunks (0 mesh, 5 blockout)  attempt 1  300s
[Expedition] Setsuru left ETHEREAL_SCAPE after 55s (RETURNED)
```

Confirmed working by the owner: the geometry fix, all four walkways, the
spiral staircase climbing, every developer command, portal recolouring by
rarity, `/tp` to every region with correct spacing, and Fate on completion.

One new problem, and it was the same class as the others — geometry nobody had
looked at:

- **The Observatory's spiral ramp encircled the Fate Engine.** A 2.5-turn helix
  at radius 118, forty studs wide, so it occupied radius **98–138** while the
  Engine's own platform is radius **120**. Fixing the *step gaps* last session
  turned it from a broken ladder into a continuous **wall** around the most
  important object in the game. Replaced with one straight processional on the
  Observatory's own 45° bearing — the empty diagonal between the Hall and the
  Archive. Crosses no walkway, clears the rig's 111-stud crown where it passes
  overhead, leaves the Engine plaza completely open.
- **The Observatory had two platforms** — a box from `buildPlatform` and a
  cylinder from its own builder, one buried inside the other. Platform shape is
  now declared in data (`PlatformShape = "ROUND"`) rather than implied by which
  builder happened to run.

### Decisions made

- **Shape belongs in the data, not in the builder that runs.** The duplicate
  platform existed because "the Observatory is round" was knowledge held in
  `buildObservatory` rather than in the Observatory's own record. One field
  removed the duplication and made it checkable at boot.
- **The approach is a ramp, not a stair.** Discrete steps at a 2-stud rise sit
  exactly on Roblox's auto-step limit and snag; a single sloped deck at 28° is
  smooth, is four parts instead of sixty-five, and cannot develop gaps.
- **Balustrades and piers are non-colliding.** A decorative rail must never
  become the reason a player cannot get onto their own staircase — which is
  the same mistake, in miniature, as the plinth that walled off the Gate.

### Recommendation, as requested: the Observatory

The staircase is fixed, but **the real question is what the Observatory is
for.** Its only content is the orrery — a global-state display.

The geometry forces the problem: sitting *above the Engine* means sitting above
the rig's 111-stud crown, and that height is what forces the climb. It cannot
simply be lowered.

**Recommendation: if it survives, move it off-centre to a sixth compass point**
rather than lowering it. A 145-stud climb for a look-out is a poor trade, and a
ground-level sixth district costs nothing that "above the centre" was buying.

Worth answering *before* the art pass, because it changes the hub's footprint.

### Recorded, not acted on

Two owner-stated directions that change the shape of later work:

- **Expeditions will move to a separate place/instance** via `TeleportService`,
  for performance and to isolate parties and solo queues. The current in-place
  `ExpeditionStage` is therefore a prototype of the **loop**, not of the
  **deployment**. `ExpeditionCore` is unaffected — destination, seed,
  eligibility and timer decide the same things wherever the map is built, which
  is the payoff of having kept it pure. `STATUS.md` §5 has the migration notes.
- **Fate-on-completion may become currency or a loot pool.**
  `ProgressionSystem.award` is the single seam.

### On the `.blend` question

**It must be uploaded to Roblox first — there is no way around it.** Roblox
cannot load `.blend` or `.fbx` at runtime; every mesh has to become an
`rbxassetid://`. But **the PLACE does not need publishing for that**: Studio's
3D Importer uploads to the account from a local `.rbxl`. Publishing the place
is only needed for DataStores. Walkthrough in `assets/README.md`.

### Stopped at

Everything from the playtest is fixed and green. **The Observatory approach is
the only untested change** — it should be re-walked first.

### Next

1. Re-walk the Observatory approach (`TESTING.md` Test C3).
2. Decide what the Observatory is for, or cut it.
3. Upload the eight Ethereal Scape islands — the biggest visible change left.
4. Hub brightness; bless the `UNCOMMON` colour; an Emberfall chunk kit.
5. **Turn `Debug.AllowCommands` and `AllowForcedRolls` off before launch.**

---

## Session 5 — 2026-09-16 — The first walk, and what it found

**Branch:** `claude/zen-volta-cuhfyh` (PR #13) · **Tests:** 291 passing (was 276)

### Done

The rescaled hub was walked in Studio for the first time. It found four bugs
that 276 green tests could not see, three of them sharing one cause.

- **The hub had no floor.** `HubBuilder.cylinder()` built a `Part` wearing a
  `CylinderMesh`, and two separate things were wrong with that:
  1. a `CylinderMesh` is **visual only** — the part keeps its *block* collision
     hull, so invisible square corners stop the player in open space;
  2. `CylinderMesh`'s axis is **Y**, `PartType.Cylinder`'s is **X**, and every
     caller passed the X convention `(thickness, diameter, diameter)`. So a
     thin disc was built as a diameter-**tall column**. The 1150-stud plaza was
     a 1150-stud wall. The player spawned on top of it.

  Now a real `Shape = Cylinder` primitive, rolled a quarter turn. Real
  collision, right orientation. Same fix applied to the portal plinths.
- **Two walkways stopped short.** They used the platform's X half-extent
  regardless of which axis they approached along — right for the two square
  zones, 30–40 stud holes for Hall of Legends and the Gate. Now projected onto
  the approach direction, sloped to meet both surfaces, and overlapped at both
  ends.
- **The Observatory ramp was 70 floating tiles.** A literal 5-stud step depth,
  correct at the old 120-stud scale, left 21-stud gaps at the new radius. Depth
  is now derived from the arc each step must span.
- **The Expedition Gate could not be used.** Its prompt sat on a plinth 84
  studs in radius against a 70-stud activation distance, and the plinth was 18
  studs tall — higher than a character can jump. Now a `GateAnchor` part
  (exactly the Fate Engine's `RollAnchor` pattern) and a capped plinth height.
- **Rescaled on the owner's read of it:** hub 1200 → 1150, zone ring 420 → 400,
  platforms down ~10%, portal scales 9/12 → 6/8.
- **Developer commands**, requested: `/fly /speed /tp /where /worlds` on the
  client, `/roll /enter /leave` on the server. `TESTING.md` §2.5.

### Decisions made

- **Commands live on whichever side already has authority.** Your character's
  velocity, speed and CFrame are already yours — Roblox gives the client
  network ownership of its own rig — so routing those through the server buys
  nothing. Roll results, expedition entry and Fate awards are the opposite and
  are server-side, debug build or not.
- **Three gates on the server commands**, and the middle one is the real one:
  `Debug.AllowCommands`, **Studio-or-place-creator**, then the command's own
  flag. A config flag left true by accident must not by itself hand a stranger
  a free Mythic.
- **A forced roll is never announced.** Same line, same reason, as a scripted
  onboarding roll: a developer typing `/roll ASTRAL_REACH` must not fire a
  Fatebreak banner at the whole server.
- **`MaxPlinthHeight` caps the step, not the width.** The rig still scales and
  still reads as monumental; only the height you have to climb is capped, so a
  portal can never again become a walled-off monument.
- **No `PlatformStand` in `/fly`.** It is the obvious way to stop the humanoid
  fighting the velocity constraint, and it makes the rig go limp and fly
  face-down. A `LinearVelocity` with infinite `MaxForce` already beats gravity,
  so the humanoid is left alone and stays upright.

### The lesson worth keeping

**A test that asserts a number proves nothing about the shape that number
produces.** `Plaza.Diameter == 1150` was true the entire time the plaza was a
wall. And **a fudge factor in an assertion is a disabled assertion** — the
prompt-reach check passed with a `* 2` in it while the Gate was genuinely
unusable.

The 15 new tests assert *relationships* instead: is it thinner than it is wide,
can it be jumped onto, does the prompt reach past its own plinth, does the
walkway have a positive span, is the spawn above the deck. Those survive a
rescale. Literals do not. Recorded in build spec §6.1 and `STATUS.md` §4.

### Stopped at

**The hub is fixed but unwalked; the expedition is still unproven.** The Gate
was unreachable last session, so nobody has yet entered a generated map — the
thing §7.1 was built for. Everything here is green in CI and none of it has
been seen.

### Next

1. **Check the floor first.** Plaza, Engine platform and Observatory platform
   should now be surfaces you can stand anywhere on, with four continuous
   walkways and a continuous ramp. If not, stop there and report it.
2. **Then `TESTING.md` Test C2** — `/roll ETHEREAL_SCAPE`, take the Gate, walk
   the map, come home.
3. Hub brightness; upload the eight islands; bless the `UNCOMMON` colour; an
   Emberfall chunk kit.
4. **Turn `Debug.AllowCommands` and `AllowForcedRolls` off before launch.**

---

## Session 4 — 2026-09-16 — Ethereal Scape, and the door at the end of the roll

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 276 passing (was 208)

### Done

- **Ethereal Scape**, the Uncommon world, built from the first piece of
  authored art the project has had. The `.blend` is a sky temple above the
  cloud deck — eight gold-rimmed meadow islands, bridges, seven waystones, and
  an **R6 rig in a `Scale_Reference` collection**, which is the single most
  useful object in the file: it makes the metre-to-stud conversion checkable
  instead of assumed.
- **A chunk kit mapped 1:1 onto those eight islands**, with its own socket
  vocabulary — `SPAN` for the bridges, `RITE` for the temple approach.
- **Expedition entry.** Roll a world, walk to the Gate, hold E, and stand in a
  map generated from that world's kit. Timer, per-client biome lighting, a
  return portal, +25 Fate on completion. Build spec **§7.1** records the
  amendment.
- **`ChunkLoader`** — the Roblox half of the chunk system, which did not exist
  before. Mesh when the manifest has one, labelled blockout when it does not.
- **`ExpeditionCore`** — pure: destination, seed, eligibility, timer. 40 tests.
- Four `Expedition_*` remotes **promoted from Reserved**, not invented.
- Docs: build spec §1.1/§1.2/§2.2/§3.1/§3.3.1/§4/§7.1, `MODULAR_MAPS`,
  `BLUEPRINT_RECONCILIATION`, `TESTING` (new Test C2), `STATUS`, and a full
  Blender→Roblox upload walkthrough in `assets/README.md`.

### Decisions made

- **§7 was amended, not ignored.** Expedition entry was on the Phase 1
  exclusion list and CLAUDE.md rule 8 forbids widening scope, so the owner's
  direction was recorded as a spec amendment with its own section rather than
  done quietly. **Combat, enemies, bosses and loot stayed excluded.** The whole
  thing is one boolean wide: `GameConfig.Expedition.Enabled`.
- **A player's destination is their last roll.** No pending-destination field,
  no schema bump, no `FateSystem`→`ExpeditionSystem` reference. It survives a
  rejoin for free because `RollHistory` is already persisted, and re-rolling
  changes where you are going — which is what a player would expect anyway.
- **Biome lighting is applied by the client, never the server.** `Lighting` is
  a shared service: the obvious server-side implementation would have painted
  the biome onto everyone's screen including people still in the hub. This is
  what actually closes the Blueprint §6 checklist item rather than appearing to.
- **`MapPathLength` is content, not config.** A world with a short expedition
  needs a short map or the expedition *is* the walk. Ethereal Scape runs 300s
  and sets 3; at the default 5 it would have been 40% traverse.
- **Onboarding slot 5 became Ethereal Scape.** Three reasons: it teaches the
  Uncommon rung the arc skipped, it guarantees the test biome is reachable in
  the first minute instead of behind a 15% draw, and it drops the scripted
  Common share from 66.7% to exactly 60.0% — the true rate. D-9 extended, not
  reversed: still 15 rolls, still peaks on Epic at 8, still never Mythic.
- **Weights renormalised to 60/15/15/7/3.** The five points came off Verdant
  Valley and Emberfall, not off Epic or Mythic — those are the rates players
  form opinions about.
- **Ethereal Scape declares no enemies, boss or loot.** It is the
  map-generation test rig. Giving it combat content would make it a worse test
  and would have meant inventing Phase 2 content nobody asked for.
- **The blockout is informative rather than pretty.** Every placeholder chunk
  carries its ChunkId and Role on a billboard and a neon post at each socket,
  coloured by Kind. A generated map has to be verifiable *by eye* — otherwise
  "generation works" is just a test name.

### The result worth keeping

Ethereal Scape's kit was authored against the `MODULAR_MAPS` checklist, not
against Verdant Valley, and **the same emergent property fell out of it**: the
Waystone Ring is the only piece offering a `RITE` exit, the Sky Temple accepts
nothing else, so seven waystones gate the temple on every seed. Nobody wrote
that rule. That is the reserved-Kind rule generalising to a kit it was not
fitted to, which is the best evidence available that the grammar is real.

### Stopped at

**Green in CI, and nobody has walked any of it.** That is now true of two
sessions' work stacked on each other — the 10× rescale from Session 3 *and* the
whole expedition path. 276 tests and a syntax check say the numbers are right;
no test can say whether a generated map reads as a place.

### Next

1. **`TESTING.md` Test C2** — roll to 5, take the Gate, walk Ethereal Scape,
   come home. Four questions answered at once. Nothing else matters until this
   has happened.
2. **Upload the eight islands** — `assets/README.md`. Check scale against the
   R6 rig on the whole-scene import *before* splitting, or it is eight
   re-uploads.
3. **`UNCOMMON`'s colour needs blessing.** It was theoretical; it is now on
   screen inside the first minute of every session.
4. **A chunk kit for Emberfall** — 15pp off the "no map" number, and its
   blueprint section already exists.
5. Hub brightness, placeholder text, UI pass — unchanged from Session 3.

---

## Session 3 — 2026-09-16 — World scale

**Merged:** PR #12 · **Tests:** 208 passing · **Head:** see `git log`

### Done
- **Rescaled the hub 10×.** 120 → **1200 studs** playable, zones at 420 radius,
  platforms from 26–56 studs to 230–360. The old Discovery Archive was 5×5
  character-heights; every zone is now at least 40 characters across.
- **WalkSpeed 16 → 32**, applied on `CharacterAdded`. This is the other half of
  the traversal budget — changing hub size without it breaks the budget.
- **Visual extent to 4000 studs** via 40 floating islands at 900–4000 radius,
  fog pushed to 4400. Playable footprint and perceived size are now separate
  numbers, deliberately.
- **Fate Engine rig 1.5× → 9×** so it reads as monumental on a 140-radius
  platform rather than as a speck. Gate 2× → 12×; the blueprint's ratio holds.
- **Chunk grid 48 → 256 studs.** Pieces now 256–1024 studs; a path-length-5
  expedition spans ~4100 studs.
- **Interaction distances scaled** — roll distance 30 → 140, prompt 12 → 70.

### Decisions made
- **4000 studs is not a walkable footprint.** At WalkSpeed 32 it is 43.8s to a
  zone; even at 64 it is 21.9s. 1200 at WalkSpeed 32 gives **13.1s**
  centre-to-centre and ~4.4s edge-to-edge. The world reads as 4000 because
  scenery goes that far — you just never walk there.
- Blueprint §2.2's absolute dimensions were relative to a 120-stud hub. What it
  was actually specifying is **proportions**, and those are preserved. Tests
  now assert relationships (gate wider than walkway, engine monumental against
  its platform) rather than the old literals.
- Traversal is now **enforced by test**, not vibes: no zone may exceed
  `Scale.MaxTraversalSeconds`, and expedition walking must stay under 35% of
  expedition duration.

### Stopped at
Scale merged and green. **Not yet seen in Studio** — the numbers are verified
by test but nobody has walked it.

### Next
1. **Pull and playtest.** Does 1200 studs feel right, or still small? Is
   WalkSpeed 32 comfortable? Both are one-line changes.
2. Hub brightness — still dark, `Crossroads.Theme`.
3. UI overhaul: resize/layout pass, mobile scaling.
4. Placeholder text: flavour lines, result card, zone labels.
5. Sky Citadel biome — blocks Phase 2.

---

## Session 2 — 2026-09-16 — Asset pipeline and modular maps

**Merged:** PR #11 · **Tests:** 196 passing

### Done
- `assets/` tree — `source/` (.blend), `export/` (.fbx), `rbxm/`, per world.
  `.gitattributes` marks binaries and blocks auto-merge on `.rbxmx`.
- `Content/AssetManifest` — logical name → `rbxassetid://`. `PLACEHOLDER`
  entries are legal and resolve to `nil`, so loaders fall back to primitives.
- `Content/Chunks` — Verdant Valley kit, 8 pieces from Biome Blueprint §3.2.
- `Util/ChunkCore` — seeded, deterministic, collision-checked assembly. Pure,
  so layouts generate and validate in CI with no meshes.
- `Schema.validateChunks` at boot.
- Docs: `MODULAR_MAPS.md`, `assets/README.md`.

### Decisions made
- **Socket `Kind` is the level-design grammar.** Sockets join only on matching
  Kind, and a Kind the arena accepts is reserved for the arena. In Verdant
  Valley the Grove is the only `WIDE` provider, so it always becomes the boss
  approach — reproducing the blueprint's intent without hard-coding it.
- Retries are expected: a path can fold back and collide. 5 attempts gives
  ~99% success.

### Stopped at
Chunk system built and tested; no Roblox-side loader (needs Phase 2 expedition
entry) and no actual meshes.

---

## Session 1 — 2026-09-15 — Phase 1 foundation

**Merged:** PRs #1–#10 · **Tests:** 167 passing

### Done
- Build spec, architecture, and the whole Phase 1 server + client.
- The Crossroads hub, generated from data per the Biome Blueprint.
- 15-roll onboarding arc; true RNG from roll 16.
- Headless test suite + CI.
- **Verified in Studio.** Playtested, and the owner's verdict on the roll loop
  with no combat, loot or art: *"these rolls alone were fun."* That answers
  Master Spec §25, which is the question the whole project rests on.

### Decisions made
- **D-8: Fate is true RNG.** No player state ever changes any world's odds.
- **D-9: 15-roll onboarding**, peaking on Epic, never Mythic.
- Rarity colour is a UI/portal contract; biome palette is set dressing.

### Bugs found (all recorded in build spec §6.1)
`Workspace.FilteringEnabled` read-only broke Rojo sync · `type()` vs `typeof()`
on Vector3 blocked boot and **passed 152 tests** · `GetDataStore` raises on an
unpublished place · `MessagingService:SubscribeAsync` yields forever and stalled
the bootstrap silently.

### Stopped at
Phase 1 complete. Two acceptance criteria (P1-8, P1-9, persistence) blocked on
publishing the place.
