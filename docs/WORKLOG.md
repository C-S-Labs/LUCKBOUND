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

## Session 47 — 2026-09-22 — Sky Citadel: caps, so no path leads to nothing

**Branch:** `claude/sky-citadel-kit-expansion` (PR #37, stacked on #35) · **Tests:** 600 passing (594 + 6)

### Done
- Owner-directed: *"I don't want any paths to lead to 'nothing', unless that
  specific chunk is a dead end, crumbling bridge, etc."* The only leak was the
  crossroads: four mouths, the path uses two, the pocket sometimes a third.
- **New `CAP` role** (Types, Schema -- exactly one socket -- and a blockout
  colour) and **three caps**: a span that breaks off with the Fallen Tower
  leaning over it, a railed overlook, a gate that stays shut.
- **`ChunkCore` caps every open socket** after the path, arena and pocket, or
  fails the attempt so the next seed is tried. Worlds without caps unchanged.
- Test: in 400 Sky Citadel maps (with and without the pocket) every socket of
  every placed piece meets another head-on; assembly still >= 190/200.
- The review chain shows the crossroads fully closed: lookout east, sealed
  gate west. 22 FBXs exported and re-imported at 256^3.

### Decisions made
- **Three caps, unlimited per layout** -- a map needs at most two, and the two
  ends of one crossroads can differ.
- **An unfillable socket rejects the seed** rather than shipping an open mouth.
  Retries absorb it (same >= 190/200 bar as before).
- **Verdant Valley gets no caps here** -- it has no art; its caps come with it.

### Next
1. Merge #35, then #37.
2. Studio: import one FBX -- 256^3? vertex colours?
3. Loader: `GroundOffsetY` (32), `CollisionFidelity`.

---

## Session 46 — 2026-09-22 — Sky Citadel: variety, turns, an intersection, and four more

**Branch:** `claude/sky-citadel-kit-expansion` (PR #37, stacked on #35) · **Tests:** 594 passing (586 + 8)

### Done
- **Variety pass on every piece.** Owner review: "each piece is very similar
  to the next." Pieces are now built from five axes — shape (single deck,
  archipelago, bare span, stepping plates), floor (eleven treatments), edge
  (parapet, railing, kerb, hedge), keel (six styles) and landmark (fourteen) —
  mixed so neighbours differ. New landmarks: lighthouse, Sky Tree, Arcane
  Prism, banner mast, clock tower, Cascade Tower, Sundered Spire, birdcage.
- **Turns both ways, one intersection, no dead ends.** Owner review: "only 1
  turning piece, and 0 intersections … the vault … dead-ends." Added a west
  bend and a four-way crossroads; the vault became `chunk_vault_turn`, a deck
  you pass through on a right turn; the side pocket is a new small lookout.
- **Four more pieces**, owner-requested: `chunk_path_shattered` (stepping
  plates, the Sundered Spire), `chunk_path_aviary` (a birdcage dome with
  birds), `chunk_archive` (the first roofed hall), `chunk_aether_springs`
  (terraced pools, a left turn). **19 pieces.**
- **System change, generic and tested:** `ChunkCore` picks a seeded exit among
  valid ones, and consumes `IncludeSide` (one SIDE pocket off a spare socket).
  `GameConfig.Expedition.IncludeSide = true`, passed by `ExpeditionSystem`.
  Verdant Valley's Hollow is placed for the first time. Two STATUS debts closed.
- Validator: an exact separating-axis test for box-shaped floats against decks;
  floor decals are single up-facing faces (2 tris, not 12); registrations honour
  lifted frames. `scatter_floats` places birds, tomes and debris only where the
  checker accepts them.
- All 19 exported and re-imported at 256³; every turning piece's and the
  crossroads' openings read back out of the FBX and match the socket data.

### Decisions made
- **19 pieces, above the 12–16 target** — owner asked for four more; the brief
  says more is welcome. The count test is now a minimum.
- **The side pocket stays a dead end, by definition** — but it now hangs off a
  crossroads branch, so taking it is a choice, and nothing on the critical path
  dead-ends (asserted).
- **Local StyLua was not applied** to System files: its output disagreed with
  the committed style (and once changed a statement's parse). CI's StyLua check
  is non-blocking; edits follow the surrounding hand style.

### Stopped at
Nineteen FBXs exported, nothing uploaded. PR #37 updated; #35 still unmerged.

### Next
1. Merge #35, then #37.
2. Import `chunk_entry.fbx` into Studio: 256³? vertex colours?
3. Loader: `GroundOffsetY` (32), `CollisionFidelity`.
4. Walk a generated map: stepping-plate gaps, terrace ramps, the crossroads.

---

## Session 45 — 2026-09-22 — Sky Citadel: eight more pieces, and floats that cannot clip

**Branch:** `claude/sky-citadel-kit-expansion` (stacked on PR #35) · **Tests:** 586 passing (582 + 4)

### Done
- **Eight new pieces**, owner-directed, each a different reason to be there
  and each bringing new props: `chunk_path_bend` (the first quarter turn),
  `chunk_path_skyport` (skiff dock, crane, landing pad), `chunk_path_hoops`
  (a bare span through three floating rings, between satellite islands),
  `chunk_garden_terrace`, `chunk_observatory` (dome, dishes, orrery),
  `chunk_armory` (racks, targets, forge, barracks), `chunk_side_vault` (the
  world's SIDE pocket) and `chunk_spire_court_b` (the Hall of Winds — a rare
  second gate-court with a Moon Gate). **12 pieces**, inside the 12–16 target.
- **Floating objects cannot clip** — owner-directed: identical flush corner
  beacons fused into one block where four tiles met. Every float and every
  large solid is now registered as it is built, and `validate()` refuses to
  export a piece where a float touches another float, a solid or a deck, or
  comes within 4 studs of the tile edge (so neighbours' floats are always ≥ 8
  apart, at any rotation). Tested against planted faults.
- **Corner beacons vary**: three styles, and per-corner size, height, turn and
  inset, seeded by piece name, each placed only where the checker accepts it.
- **Edge pins** took over the beacons' other job — holding each mesh's box to
  exactly 256 × 256 — as four 0.3-stud pins at the keel line.
- All 12 exported and re-imported at 256³; the bend's openings verified at FBX
  +Z (south) and +X (east). Review renders now include a chain through the
  bend and four pieces meeting at a corner.
- Content: 8 chunk entries, 8 manifest placeholders. Tests: two gate-courts,
  the SIDE pocket, the 12–16 count, layouts that turn.

### Decisions made
- **Two ASCENT providers, not one.** The rare Hall of Winds shares the Spire
  Court's role; the reserved-Kind rule still guarantees a gate-court before the
  arena.
- **No west bend yet.** `exitFor` takes the first socket, so it would add no
  variety until that is fixed.
- **Sky Citadel's assembly bar is ≥ 190/200 seeds**, like Verdant Valley's:
  a path that turns can fold back on itself.

### Stopped at
Twelve FBXs exported, nothing uploaded; PR stacked on #35.

### Next
1. Merge #35, then this.
2. Import `chunk_entry.fbx` into Studio: 256³? vertex colours?
3. Loader: `GroundOffsetY` (32), `CollisionFidelity`, a random exit pick,
   `IncludeSide`.

---

## Session 44 — 2026-09-22 — Sky Citadel: art direction and the first generated kit

**Branch:** `claude/sky-citadel-chunk-kit` · **Tests:** 582 passing (574 + 8)

### Done
- **`docs/SKY_CITADEL.md`** — the section the Biome Blueprint never wrote.
  Owner direction: *floating spires, future-like castle architecture, a
  floating citadel with varying decorations and objects.* A white futurist
  castle on floating islands: needle spires with neon halos, violet-roofed
  turrets, azure seams of light, a ten-role palette, a prop vocabulary, and an
  explicit "what floats on purpose" list for the hand pass. Written against
  Ethereal Scape so the two sky worlds do not blur.
- **Connection vocabulary first**, as the brief asks: `SKYWAY` (40 studs,
  connective) and `ASCENT` (72, arena-only). The Spire Court is the only
  `ASCENT` provider, so it gates the arena on every seed — the reserved-Kind
  rule producing gating for the third time.
- **Four pieces, generated in Blender 5.2 by a script in the repo**
  (`assets/source/worlds/sky_citadel/build_sky_citadel_kit.py`): entry, path
  straight, spire court (grove role), boss clearing. Exported as four FBXs,
  each re-imported and measured: 256 × 256 × 256, one mesh, Y up, metres,
  opening confirmed at FBX −Z (north). 3.7k–7.3k triangles.
- **Content:** `Content/Chunks/SkyCitadel.luau`, four `SC_CHUNK_*` manifest
  placeholders, world header rewritten. Sky Citadel is now **enterable**
  (blockout, no enemies); "no map" drops from 25% to 18%.
- **Tests:** 4 that asserted Sky Citadel had no map moved to Emberfall; 8 new
  — per-world Kinds disjoint, ASCENT reservation, 256³ declared, 200/200
  seeds assemble, the court always precedes the arena.

### Decisions made
- **Every piece fills an exact 256³ box.** `ChunkLoader.tryMesh` stretches the
  mesh to `SizeX/Y/Z`, which the brief never says. Corner beacons pin the
  footprint, the keel apex (−96) and one 160-stud spire pin the height. The
  walk plane is therefore 32 below the box centre, kit-wide — the number
  `GroundOffsetY` will need.
- **Colour baked as vertex colours** as well as material slots: a chunk is one
  MeshPart, so paint-by-part-name is not available. Unverified in Studio.
- **The `.blend` is an output.** The script is the source; re-run it.
- **Render headless.** Rendering through the Blender MCP bridge crashed the
  interactive session twice on the same shot; `blender -b` does all ten in
  ~3 s. Both scripts are documented headless-first.

### Stopped at
Four FBXs exported and committed, nothing uploaded. Found four loader-side
issues on the way and recorded them in `STATUS.md` rather than fixing them
(this pass was content): mesh stretched to declared size, single-MeshPart
colour, default collision fidelity, spawn from the mesh top.

### Next
1. Import `chunk_entry.fbx` into Studio: does it read 256³, and do the vertex
   colours survive?
2. `GroundOffsetY` (32 for this kit) and `CollisionFidelity` in `ChunkLoader`.
3. Owner review of the look (`renders/`), then iterate the generator.
4. `chunk_path_bend` — no current socket turns — then the other 7–11 pieces.

---

## Session 43 — 2026-09-22 — Unit scale, kit size, and a hand pass

**Branch:** `claude/nifty-babbage-elpxrv` · **Tests:** 574 passing (unchanged)

Third pass on the same brief, from a real export batch. All four changes came
from things that actually went wrong, which is the right way for this document
to grow.

### The export was in millimetres

The eight Verdant Valley FBXs imported at **256,000 studs** against a declared
256. Exactly 1000×, so the file was written in millimetres while everything
downstream reads metres. Studio cannot do anything useful with a part that
size.

The brief now names both settings that have to agree — Blender units
Metric/Metres/Unit Scale 1.0, and FBX Transform → Scale 1.00 with Apply
Scalings `FBX All` — but the part that will actually catch it is the check
rather than the settings: **import one piece and measure it; a 256 piece must
read 256.** Settings drift between Blender versions and exporter presets; a
measurement does not. The FBX-scale-0.001 workaround is named and discouraged,
because a compensating factor is a thing someone later removes for looking
wrong.

### The kit wants 12–16 pieces, not 8

Owner-directed. The variety of a run is the variety of the kit — the generator
shuffles what it is given — and 8 starts to repeat itself.

Recorded as **variants of existing roles, not new roles**: several meadows,
several groves, weighted so one is common and another rare. That keeps the
socket grammar and the Blueprint progression intact while multiplying what a
seed can produce, and it costs no System change. `Content/Chunks/` stays at 8
declared until art exists for more — a declared chunk with no art is a piece
the blockout draws and nobody meant.

**First delivery is 4:** ENTRY, PATH_STRAIGHT, GROVE, BOSS_CLEARING. Smallest
set that assembles a complete walkable map, and the Grove has to be in it — the
WIDE reservation makes it the only piece offering the exit the arena accepts.
Worth noting that fell out of the socket rules rather than being chosen.

### The pieces were generated stacked

Every piece occupied the same spot in the scene. Nothing was broken — the
exports were fine — but the kit could not be reviewed without hiding objects
one at a time, and **a piece nobody can see is a piece nobody checks.**

The brief asks for a spaced review layout, with the catch stated plainly: the
review position and the export position are different things, and a piece
exported while parked on the review grid arrives that far off in game. That is
the same origin/transform trap as everything else in this document, wearing a
different hat.

### A hand pass before delivery

Owner-requested, and yes it is reasonable to ask for: automated generation is
good at making a hundred things and bad at noticing that four of them are
wrong. Five specific checks — floating scatter, clipping, scale against the
5-metre reference, and two that are worth the minute they cost:

- **Place a copy of the piece beside itself, rotated a quarter turn.** That is
  exactly what the game does, so it is the fastest way to see a bad join before
  it is eight pieces and an upload.
- **Rotate the piece 90° in the viewport.** It should spin in place. If it
  swings sideways, the origin is wrong — the one error no test here can catch.

### Also added

A short **"starting a different world"** section, since Sky Citadel is next:
the conventions port, the connection vocabulary does not. Each world's socket
Kinds are decided before modelling, because they decide where the openings go
and re-cutting openings on a finished kit is the expensive version of that
conversation.

### Done

- `docs/CHUNK_AUTHORING.md` — unit scale, kit size and first delivery, review
  layout, the hand pass, starting a new world. ~940 words to ~1,800; still
  conventions, still no compliance checklist.
- `docs/MODULAR_MAPS.md` — the authoring checklist gained the 12–16 target and
  "decide your Kinds before modelling".
- `Content/Chunks/VerdantValley.luau` — header records the 12–16 target, the
  variants-not-roles rule, and the 4-piece first delivery.
- `docs/STATUS.md` — four rows, including the process one that should have been
  written last session and was not: **specify the seam, not the piece.**

### Stopped at

Docs and one content header. No System changed, 574 green. PDF re-exported.

### Next

Unchanged from Session 42, and now blocking real art:

1. **`GroundOffsetY`** — must land before any mesh is uploaded.
2. **Four pieces through the whole pipeline** before the remaining 8–12 are
   built.
3. **Sky Citadel's socket Kinds** — the owner is starting that world next, and
   `STATUS.md` still says it needs a Blueprint section first. Worth settling
   before geometry exists, not after.
4. `PathLength` retune after a real piece is walked; `exitFor` random exit;
   decide `IncludeSide`.

---

## Session 42 — 2026-09-22 — The brief was a spec; the kit came back wrong

**Branch:** `claude/nifty-babbage-elpxrv` · **Tests:** 574 passing (unchanged)

### What happened

The Session 40/41 brief was handed to the modeller's AI engine. What came back
was roughly 10× the area of the previous iteration, terrain flattened to the
boundary on all four sides, scatter lost in an empty green plane. The earlier
iteration — which was good — had to be restored from backup.

**The brief caused it, and it is worth being precise about how**, because the
same mistake is available on every future art brief here:

1. **A table of eight footprints (512–1024 studs).** Stated as "the contract".
   The engine built to the largest numbers, and the same scatter budget spread
   over ~10× the area reads as empty.
2. **"A 32-stud flat band along every edge, empty of scatter, variation eases
   to zero before it reaches it."** Read literally, that flattens the terrain
   to the perimeter and pushes all detail into the middle.
3. **A 13-item checklist.** It reads as a compliance list, so satisfying it
   became the goal rather than building something that looks like a forest.

Every one of those was written in good faith and every one was over-reach. The
join needed level ground *at the openings*. I specified the whole piece.

> **A number stated in a brief is a number that gets built.** Specify the seam,
> not the piece.

### Done — the brief is now conventions, not a spec

`docs/CHUNK_AUTHORING.md` rewritten from ~3,800 words to ~940: six conventions,
export settings, a short "what happens on our side", and an explicit line at
the top that **everything not listed is the modeller's** and nothing in it
should be read as a target. Owner-scoped, four decisions:

- **One size for the whole kit: 256 × 256.** Not a table. The two iterations
  bracketed it — ~100 studs read too tight, ~1024 too open — so the number is
  the middle they named, and the doc says out loud that it lives in one content
  file and is meant to move if it reads wrong on the ground.
- **Level ground at the openings only.** The rest of the perimeter is free to
  cliff, wall or roll. The weld band is gone.
- **Invariants only.** No reasoning, no essays, no compliance checklist. The
  long-form argument stays in `MODULAR_MAPS.md` for us.
- **Nothing about look.** Density, scatter and style are not mentioned, by the
  owner's call — `ART_DIRECTION` and the modeller own that.

### The content followed the art, not the other way round

`Content/Chunks/VerdantValley.luau`: **all 8 pieces are now 256 × 256**, sockets
at the edge midpoints (±128). Header rewritten to say why, and to say plainly
that the sizes follow the art — they are numbers in a content file and the
piece that reads correctly on the ground wins.

No System changed. 574 tests still pass, including the 300-trial assembly run
and "the smallest map piece is at least 40 characters across" (256 / 5 = 51).

**Traverse dropped from 4096 studs to 1536** — about 48 s of a 720 s
expedition, ~7%. The test asserts a relationship rather than a number so it is
green, but that is a lot of slack. `PathLength` takes it up, and that is worth
retuning **after** a real piece has been walked: how long 256 studs of authored
forest takes to cross is a different question from how long an empty blockout
takes.

### The origin convention changed too

The brief now asks for the origin at the **centre of the footprint, at ground
level** — what an artist would author anyway, and what the blockout already
assumes. The previous version asked for the bounding-box centre, which meant
170 studs of ground body under the player's feet at `SizeY = 340`. That was
bending the wrong side.

`ChunkLoader` does not yet consume a ground-level origin. **`GroundOffsetY` is
now a prerequisite for the first mesh upload**, not deferrable debt — raised to
High in `STATUS.md`, with the loader carrying a comment at the two lines
involved. Nothing is uploaded yet, so there is time; a piece imported before it
lands sits half-sunk.

### Decisions made

- **Specify the seam, not the piece.** Recorded as a process row in `STATUS.md`
  so the next art brief on this project inherits it rather than rediscovering
  it.
- **Sizes are content and follow the art.** Stated in the brief, the content
  file header and `MODULAR_MAPS.md`. If 256 reads wrong, the number moves.
- **Uniform size over varied.** Differently-sized pieces remain legal and the
  assembler handles them; one number is simply easier to author against, which
  is the constraint that matters right now.

### Stopped at

Docs, the content sizes, and two code comments. 574 green. PDF re-exported for
the modeller.

### Next

1. **`GroundOffsetY`** — the one thing that must land before a mesh is
   uploaded.
2. **One piece through the whole pipeline** before the other seven are
   modelled: author, export, upload, flip the manifest to `UPLOADED`, walk it
   among seven blockouts. Every remaining assumption in this area gets settled
   by that one piece, and getting it wrong costs one re-export instead of
   eight.
3. **Retune `PathLength`** once that piece has been walked.
4. `exitFor` random exit, and decide `IncludeSide` — both still open from
   Session 41.

---

## Session 41 — 2026-09-22 — Sockets on every open side, and the seam

**Branch:** `claude/nifty-babbage-elpxrv` · **Tests:** 574 passing (unchanged)

Follow-up to Session 40, same branch. Three owner questions from Blender
screenshots of the Verdant Valley kit in progress.

### "Can sockets go on every side that isn't blocked?"

Yes, and it is the right instinct — but **it buys nothing today**, and finding
out why turned up two pieces of code/doc drift:

1. **`ChunkCore.exitFor` returns the FIRST valid socket**, not a random one. A
   four-socket piece leaves through the same one every seed. The entry chunk is
   worse: hard-coded to `entry.Sockets[1]`. So the variety the owner is asking
   for is one weighted-random pick away, and is not there now.
2. **`AssembleOptions.IncludeSide` is declared and never read.**
   `ChunkCore.assemble`'s own docstring promises it hangs a SIDE pocket off a
   spare socket. Nothing consumes the field. **`VV_HOLLOW` has never been
   placed in any layout** — the Blueprint §6 side-pocket item is satisfied on
   paper only.

Neither was fixed here. Both change a System and belong in their own piece of
work with their own tests; this pass was documentation. Both are now debt rows
in `STATUS.md`, and the brief tells the modeller to author the sockets anyway —
the data is right either way and the run gets more varied the day the pick
lands, with no re-export.

A third thing falls out of high socket counts and is worth naming: **the
generator consumes exactly two sockets per piece, so every other opening faces
nothing, and nothing caps them.** Today that is the art's problem — an opening
must read as plausible unattached — and the systematic fix is a cap piece the
loader places, which needs a schema field.

### "The edges vary, so pieces won't meet — do we generate a connector in Studio?"

The edges do vary, and they slope off; two of them meeting would step, gap or
lip. The answer is a **weld band**: a 32-stud flat strip at ground height along
every edge of every piece, empty of scatter, with terrain variation easing to
zero before it reaches it. Two flat coplanar straight edges butt together
perfectly at any rotation, with no per-pair work and no runtime cost.

The proposed Studio-generated connector was considered properly and rejected,
for reasons worth keeping:

- **It cannot match the material.** Colour and finish live inside the uploaded
  mesh as `SurfaceAppearance` and textures, which code cannot read. The
  connector would be a flat-coloured strip between two textured pieces —
  trading an invisible seam for a visible band.
- **It is a permanent System change** in `ChunkLoader`, at four rotations, for
  every Kind, to work around an art rule that costs one flat band.
- It halves the useful footprint, and bridging a height difference means a ramp
  at every join, which changes how the map plays.

One part of the idea was kept: a **skirt** under the join — thin,
non-colliding, never meant to be seen — so float drift shows dark ground
rather than sky.

### "What should the anchor points be named?"

For a chunk kit, **names inside the piece do not matter at all**, and that is
worth stating because it is not true elsewhere here: `PrefabLoader` registers
the hub from a NAMED PART and `PrebuiltLoader` reads `EntryAnchor` /
`ReturnAnchor`, but `ChunkLoader` builds a MeshPart from an asset id and never
looks inside. The existing `VerdantValley_Chunk_02_RouteRock_01_Slab` scheme is
fine as it stands.

Two things about naming do matter, and both are now in the brief:

- **The root.** The origin is not an object — it is the root's transform, so
  the root's name is what export, manifest and content must agree on.
  `Chunk_03` says nothing about which of eight role-named pieces it is, and the
  role decides size, socket count and where the generator may put it. The brief
  carries the full root ↔ manifest key ↔ chunk Id table.
- **Socket marker empties**, `Socket_<id>_<KIND>`, in their own collection,
  excluded from export. Nothing reads them; the point is that the offsets in
  `Content/Chunks/` are hand-typed today with no way to check them against the
  file. Proposed as a convention, explicitly not as a promise to automate.

Also flagged from the screenshot: the root of `VerdantValley_Chunk_03` sits at
**Location Y = 100 m**. Export writes positions relative to the scene origin,
so that arrives 100 studs out.

### Done

- `docs/CHUNK_AUTHORING.md` — three new sections: how many sockets and on which
  sides, the edge contract, naming. Checklist grew from 9 items to 13.
- `docs/MODULAR_MAPS.md` — the weld band added as a fourth geometry-contract
  rule; the socket section now carries the two caveats.
- `docs/STATUS.md` — three debt rows: `exitFor` first-match, `IncludeSide`
  never read, unused sockets never capped.
- The brief was exported to PDF for the owner's modeller.

### Stopped at

Docs only, again. No System changed. 574 tests still green.

### Next

1. **`exitFor` picks its exit at random** — the one change that makes "sockets
   on every open side" do what the owner wants. Small, needs tests, should not
   ride along with anything else.
2. **Decide `IncludeSide`**: implement it, or delete the field and the
   docstring's promise. A declared option nothing reads is worse than neither.
3. Re-author the kit's edges to the weld band before any piece is uploaded —
   it is a cheap rule now and an eight-piece re-export later.

---

## Session 40 — 2026-09-22 — The chunk origin contract, written down

**Branch:** `claude/nifty-babbage-elpxrv` · **Tests:** 574 passing (unchanged)

### What prompted this

The owner is modelling the Verdant Valley chunk kit in Blender and sent a
screenshot of four 100 × 100 pieces with their **origins at the corners**,
asking why the earlier guidance had said corners.

It had — in conversation, not in the repo, which is the actual failure here.
**There was no chunk-authoring brief in `docs/` at all.** The Crossroads and
the Fate Engine each got a full Blender prompt; the chunk kit, which is the
piece with the strictest geometry contract of the three, got none. So the
guidance lived in a chat, was wrong, and nothing in the repo contradicted it.

### The origin belongs at the chunk's centre, and this is why

`ChunkLoader` places a piece by putting its origin at `placed.X/Y/Z` — which is
the **centre** the assembler chose — and `ChunkCore.overlaps` rejects
collisions against centre ± half-size. And `Yaw` is derived from the socket
pair, so **every piece is rotated 0/90/180/270 depending on the seed**, about
its origin.

That last part is what makes a corner origin unrecoverable rather than merely
offset: the error is a different vector for each of the four yaws. Meanwhile
the generator still certifies the layout as collision-free, because it only
ever saw centre ± half-size. **A wrong origin produces a map that is correct in
data and broken on the ground** — the worst shape a bug can have here.

### Done

- **New `docs/CHUNK_AUTHORING.md`** — the brief that should have existed.
  Scale, the origin rule and its derivation, what "independent chunk" forbids,
  how sockets actually gate joins, FBX settings, and a pre-export checklist.
- **`MODULAR_MAPS.md`** gained a *geometry contract* section: origin, chunk
  independence, and "chunks do not join on any side — only at sockets, only by
  Kind". Its authoring checklist now points at the new brief.
- **`assets/README.md`** — the kit-export section said "origin at the piece's
  centre" already, which was right but under-argued and easy to skim past. It
  now says middle-most point in all three axes, says why, and says one FBX per
  chunk explicitly.
- **`ChunkLoader.luau`** carries the contract as a comment at the exact two
  lines that depend on it. No behaviour change.
- **`STATUS.md`** — two new debt rows and the Verdant Valley testing posture.
- **`DEVELOPMENT_PLAN.md`** — the interim roll-gating step under Phase 1.
- **`README.md`, `CLAUDE.md`** — doc lists updated.

### Decisions made

- **Origin at the geometric centre of the bounding box, all three axes.**
  Recorded in code and in three docs, because it is invisible metadata that no
  test can see — the same class of failure as the hub's "register from a named
  part, not a pivot" rule.
- **The kit is not a tiled grid.** The screenshot's four equal 100 × 100
  squares in a 2 × 2 block is a different system from the one that exists: the
  kit is eight differently-sized pieces (256 × 512 up to 1024 × 1024) chained
  end to end. Said plainly in the new brief, with the size table, because it is
  the kind of misunderstanding that costs an art pass.
- **Gating the roll pool to Verdant Valley for testing is a data change, and
  it is `GameConfig.Fate.PrototypeWeights`, not each world's `RollWeight`.**
  `FateCore.effectiveWeight` prefers the override table while
  `CurrentPhase == 1`. `OnboardingSequence` has to be flattened too or rolls
  1–8 still force four other worlds. Written down, not implemented — it is the
  owner's call when to flip it.

### Not done, deliberately

- **Nothing was renamed.** The owner called the world "Verdant Plains"; the
  repo calls it `VERDANT_VALLEY` throughout — content ids, `VV_` asset keys,
  chunk ids, tests, the Biome Blueprint. If the name is changing that is a
  rename pass of its own, and it should happen before the art is uploaded
  rather than after.
- **The `GroundOffsetY` field is not built.** The mesh path puts the bounding
  box *centre* at the layout Y while the blockout puts the *walking surface*
  there. The brief works around it by requiring the walk plane be centred in
  `SizeY`; the real fix is a schema field, which is a spec amendment. Logged
  in `STATUS.md` debt.

### Stopped at

Docs only. No System changed, no content changed, 574 tests still green.

### Next

1. **Owner decides the name** — Verdant Valley or Verdant Plains — before art
   is uploaded.
2. **Re-author the test chunks to the real sizes** in
   `Content/Chunks/VerdantValley.luau`, with centre origins and an opening at
   every declared socket.
3. **Upload one piece** — `VV_CHUNK_ENTRY` is the smallest useful test — flip
   its manifest entry to `UPLOADED`, and walk a generated map with one mesh
   among seven blockouts. That is the cheapest possible proof of the origin
   contract, and it also settles the `GroundOffsetY` question with evidence.
4. **Then gate the roll pool** and test the loop end to end.

---

## Session 39 — 2026-09-21 — Weather that covers the plaza, and a plan

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 574 passing (was 572)

### The event bar moved to the top

It sat at y=280 — the middle of the screen, across the player's view of the one
event they were trying to look at. A status bar belongs at an edge.

Three things want the top of the screen now: the event bar, a roll
announcement and the expedition banner. The event bar takes the very top (it is
world state and persists), announcements slide in below it, and the expedition
banner steps down 60px while an event is running rather than landing on top of
it — driven off `EventController`, which both already had access to.

### The weather covers the plaza now

The mote emitter was a **one-stud part** over the Fate Engine. A
ParticleEmitter emits across its part, so a one-stud part makes a column and a
plaza-sized one makes weather — which is why the effect only ever appeared over
the dais.

The emitter is now `HubDiameter × SkySpanFactor` across. Two supporting
changes: particle lifetime went 6–11s to 10–18s, because they now have to fall
the whole way from `SkyHeight` rather than a short hop, and the content rate is
multiplied by `SkyRateScale` — content states a rate as a *feel* ("a Starfall
is heavier than a Veil") and spreading the same rate over a whole plaza would
have made every event a drizzle.

### `docs/DEVELOPMENT_PLAN.md`

Owner-requested, and overdue: development has been reactive — walk, find three
things, fix three things — which was right while the shape was being found and
is wrong now.

**The recommendation it turns on: the first playtest should not wait for
combat.** Combat is the largest unbuilt system in the project and none of it is
needed to answer what a first playtest is for — *does the roll loop hold a
stranger for an hour, and do they come back*. The owner has already answered
half of that alone ("these rolls alone were fun"); what is unknown is whether
it survives people who did not build it.

So the playtest build closes the loop **without** combat: an expedition becomes
find the things worth finding and get out before the timer. Every part of that
is content on systems that already exist.

Five phases, each with a checkable exit gate: clear the deck → every roll
leads somewhere → something to do in a world → make it feel like a game → run
the test. Plus a list of what is deliberately NOT being built yet and why, and
six working rules aimed squarely at the back-and-forth.

**The number that matters most in it:** 25% of honest rolls still land on a
world with no map. A tester who rolls a *Rare* and is told the world does not
exist has been punished for a good roll.

### Stopped at

Pushed. `CLAUDE.md` now points at the plan, and STATUS §5 defers to it.

### Next

Phase 0 of the plan: walk everything unwalked, fix the staircase in Studio,
publish the place and prove saves, the ledger and the two-instance race.

---

## Session 38 — 2026-09-21 — A command that was never a command

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 572 passing (was 569)

### Why `/event` did nothing

Reported as "events don't trigger". They trigger fine — **the command was
never registered on the client.**

`DebugSystem.COMMANDS.event` has existed on the server for two sessions, but
the client registers each command as a `TextChatCommand` and forwards it, and
`/event`, `/endevents` and `/ledger` were never added to that list. So typing
them sent an ordinary chat message and nothing else, which is exactly what the
screenshot showed: the text in the chat log, no reply, no sky.

**A server command with no client alias is not a command.** All three are
registered now.

### The reason nobody noticed for two sessions

Replies went to the **Output window only**. In Studio that is reasonable — it
is where the rest of the diagnostics live. In a running client nobody can see
it, so "this command failed", "this command does not exist" and "this command
worked silently" were the same experience: nothing happened.

Replies now also go to chat as a system message. `DisplaySystemMessage` rather
than `SendAsync`, because this is the game answering the player rather than the
player saying something.

### Entry on the Fate Engine

The portal is enterable from the dais. The staircase is still unmodelled and no
longer blocks testing the teleport or the biome scripts.

Two details worth keeping:

- **The anchor carries the `GATE_ANCHOR` name wherever it sits**, and
  `ExpeditionSystem.gatePart` now searches the hub by name rather than walking
  a fixed path to `Zones/EXPEDITION_GATE`. Moving entry again -- to the top of
  the staircase, when it exists -- is a placement decision in `HubBuilder`
  rather than an edit to a system.
- **`F`, not `E`.** Every ProximityPrompt defaults to E and ROLL already owns
  it on that dais. The key is content, checked against
  `Constants.HOTKEY_NAMES` like every other key, and a test asserts it is both
  real and not E.

### The menu behind the loading screen

Three independent things can hide the hub menu -- leaving the Crossroads, a
roll resolving, and the loading screen being up -- and each of them used to set
`gui.Enabled` itself. That is how the rail ended up sitting over the title
card: one of them said "show" without knowing another had said "hide".

One function decides now, and the three inputs are three booleans it reads.

### Stopped at

All four items from the fourth walk are done. Pushed, 572 green, none of it
walked.

### Next

1. Walk it: entry from the Engine (test C2b), the events now that they run,
   and the loading screen with the menu hidden.
2. The staircase junction in Studio, with the collision re-bake.
3. Travel landings, district tint, event sky.

---

## Session 37 — 2026-09-21 — The Engine, dimmer again

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 569 passing (was 568)

A partial session — two of four changes from the fourth walk, committed on
their own because the other two are not started.

### The Engine's light, cut a second time

Session 36 took the spotlight from 8 to 3 and it was still a white pool over
the plaza. Now **1.1**, and the cone from 80° to **50°** — a wide cone washes
the whole plaza, a narrow one pools on the dais, which is what the light is
for. The portal's own point light came down with it (idle 1 → 0.5, active
3 → 1.5).

**There is no ratio to derive any of this from.** Range and height are
distances and scale with the world; brightness moves the *other* way, because
a light that did not move away from a surface that came closer is a brighter
light. Past that it is a look, and the only instrument is a walk. The numbers
are commented as such so the next person tunes rather than derives.

The light test stopped asserting `brightness == 3` and now asserts the
relationship — active brighter than idle, but not by more than 4× — so tuning
the look does not mean editing a test each time.

### Spawn ring 110 → 105

Five studs in, as asked. Still outside prompt reach and roll range, which is
what the three tests pin.

### Not done, and why

- **The GUI is still visible behind the loading screen.** Not started.
- **Entry on the Fate Engine portal** — started, and stopped: the edit that
  wired the ENTER prompt onto the Engine was declined mid-session. The config
  flags I had added for it (`EntryAtEngine`, `EntryPromptKey`) were **removed
  rather than left dangling**, because config that nothing reads is the same
  lie as a button that does nothing. Two lines to put back when it goes ahead.

The design for it, so it is not re-derived: the entry anchor carries the
`GATE_ANCHOR` name wherever it sits, and `ExpeditionSystem.gatePart` finds it
by name rather than by path — so moving entry from the market to the Engine is
a placement change in `HubBuilder`, not a system change. The prompt needs a key
other than `E`, since every ProximityPrompt defaults to it and ROLL is already
on the same dais.

### Next

1. Hide the hub menu while the loading screen is up.
2. Entry on the Engine portal, if it is still wanted.
3. Then the walk: travel landings, district tint, event sky.

---

## Session 36 — 2026-09-21 — Three things the rescale left behind

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 568 passing (was 566)

The half-size world was walked. Everything that broke was the same mistake in
three places: **a distance that did not scale with the world.**

### 1. The loading screen had no Crossroads in it

Two causes, and they compounded.

`Content/Hub/Cinematics` is nothing but distances — six camera radii, six
heights, six look-offsets — and none of them scaled. The cameras stayed where
they were while the hub halved underneath them, so every shot framed empty sky
with something small in the middle of it.

The second is subtler and follows from Session 35's spawn gating: **with
StreamingEnabled, Roblox streams the world around the player's CHARACTER, and a
player who has none is a player nothing streams to.** The screen flew its
camera around a hub that was never going to arrive, which is also why it timed
out with "taking longer than usual". Fixed with `ReplicationFocus`, the
documented answer: the server points each joining player at a part in the hub
until their character exists and can take the job back.

**And the timeout now says what it was waiting for** — instance count, settle
time, preload state. The first version of that message told nobody anything,
and finding the cause took a walk and a code read.

### 2. The Fate Engine was a white blowout

Its spotlight was `Brightness 8, Range 400, Height 300` — tuned for a world
twice this size. Range and Height are distances and now scale, but **brightness
does not work that way**: the same light hung half as high over a half-size
dais is four times the illuminance by inverse square. Cut to 3, by eye rather
than by ratio, because the right number there is a look.

The crystal shards had the same problem in a more obvious form: `OrbitRadius`,
heights and `Size` unscaled meant shards the size of the machine they orbit.

### 3. The rings still were not connected — same speed, different axle

Session 35 gave `PortalPlane` exactly `InnerRing`'s speed, and it still read as
disconnected. The reason: **`SpinAxis` defaults to `"Y"`**, and the rings
declare `"Z"`. The aperture was turning about the vertical at precisely the
right rate — the one combination that looks like a bug rather than a
mechanism.

A test now asserts every part in the portal assembly shares an axle, not just a
speed.

### The pattern, worth naming

A world rescale does not fail on the numbers you think about. It fails on the
ones nobody filed under "distance": a camera radius, a light's range, an orbit,
a shard's size. The suite caught twelve of those in Session 35 because the hub
geometry was pinned by relationships; these three were missed because nothing
related them to the hub. Two new tests close that — every camera shot must
frame something the size of the hub, and everything in one assembly must share
an axle.

### Stopped at

Pushed. The revamp question was answered: **agreed, after testing** — the
contract that makes a new `.rbxmx` a drop-in is recorded in `ART_DIRECTION.md`.

### Next

1. Walk it again: the loading tour, the Engine's light, the rings.
2. The staircase junction in Studio, with the collision re-bake.
3. Travel landings, district tint, event sky — still unwalked.

---

## Session 35 — 2026-09-21 — The world halves, the rings become two, and nobody spawns early

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 566 passing (was 563)

### 1. The whole world is half the size it was

Owner-directed after the measurement in Session 34: *"shrink the ENTIRE map
scale down to 1.0 instead of 2.0."*

Done through **one number** — `GameConfig.HubLayout.WorldScale = 0.5` — which
every distance that positions something on or around the authored shell now
derives from, including both prefab scales in content. Setting it back to 1.0
restores the world exactly.

**The test suite did the hard part**, and this is the clearest return the
project has had on writing tests as relationships rather than literals. The
couplings were already pinned from the mesh's own measurements
(`RAW_RING × Prefab.Scale == ZoneRingRadius`, and three more), so halving the
shell alone produced **twelve failures, each naming the number left behind**:
the blockout districts, the bridge overlap, the deck height, the kerb
extensions, the backdrop's own scale and base height, the island field. Not one
of them needed a judgement about geometry.

**WalkSpeed 32 → 24, and not to 16.** The doubling existed to make an oversized
hub walkable — but the *biomes* were always authored at play scale, so they
were sized against 32 rather than against the oversized hub. Dropping to
Roblox's 16 would turn Ethereal Scape's 95-second traverse into 142 and make an
authored map read as a hike. 24 keeps the plaza brisk (8.3s centre to district,
inside the 20s budget) and leaves the biomes as designed.

**Four thresholds were re-derived rather than relaxed**, and the distinction
matters: each had been written as an absolute in a world that was twice the
size it should have been. "≥200 characters across" was really asking for 100
characters of honest space; "≥40 characters" for 20; the mountains' "500–1000
studs of clear sky" was a proportion of the world all along. The fourth stopped
asserting the literal 1150 entirely and now asserts that the plaza equals
whatever `HubDiameter` says — which is the assertion it should always have
been.

### 2. Two rings, not three

The inner ring so nearly encases the portal that they read as one object, so
they are now one: ring 1 is the outer frame, ring 2 is the inner ring **and**
the aperture, turning together against it.

`PortalPlane` takes `InnerRing`'s speed **exactly** (−0.31), not a similar one.
A near-match is worse than either extreme: two nested discs at −0.31 and −0.14
slide against each other, which reads as one of them slipping rather than as a
mechanism. A test pins the equality.

### 3. Nobody spawns until they press PLAY

A player was being offered the Fate Engine's ROLL prompt *before pressing
anything* — which spoils the loading screen and skips the moment a tutorial
would use.

`Players.CharacterAutoLoads` is now **false**. The client fires `Player_Ready`
when PLAY is pressed (declared in build spec §4 in the same change) and the
server spawns them then; a second is ignored, so it cannot be used as a free
respawn.

And the spawn ring moved from 34 to **110** — outside `PromptActivationDistance`
(35) and outside `MaxRollDistance` (70), but well inside the districts at 200,
so the Engine is still what you are looking at. **The gap between the spawn and
the prompt is where a first-join tutorial lives**, and three tests now stop the
two drifting back together.

### 4. The staircase clipping is not ours to fix in code

Reported from the walk. Worth recording precisely, because the instinct is to
reach for `Bridges.Overlap`:

> **With an authored shell present, `HubBuilder` generates no walkways at
> all.** `if shell then ... else buildWalkway() end`. The stairs, the walkways
> and the districts are all mesh.

So `Overlap`, `WalkwayWidth` and `ExtendInwardTo` only apply to the blockout
path, which does not run. The junction is a Studio edit plus a re-export — and
the re-export must re-bake `CollisionFidelity`, or the 30 precise parts drop to
`Default` and seal their own openings.

### Stopped at

Pushed, all green, **none of it rendered**. The half-size hub is the biggest
unverified change the project has made in one pass.

### Next

1. **Walk the half-size hub**: the plaza, the district walk at WalkSpeed 24,
   and whether the counters now read correctly against the player.
2. The staircase junction in Studio, then a re-export with the collision bake.
3. The rest of the walk — travel landings, district tint, event sky.

---

## Session 34 — 2026-09-21 — The third walk: a camera saved too early, and lamps that drift

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 563 passing (was 559)

### 1. The camera, finally — it was restoring a value captured too early

Reported precisely enough to solve it: *"persists ONLY when the player is first
put into the loading screen. After resetting the character, my camera locked
back on."*

`releaseCamera` wrote back the `CameraType` captured at init. On a **first
join** that capture happens before Roblox's camera system has started, when
`CurrentCamera.CameraType` is still **`Fixed`** — so the screen faithfully
restored `Fixed`, and a Fixed camera follows nobody. After a respawn the camera
script had already set `Custom`, so the saved value was right *by accident*,
which is exactly why resetting appeared to fix it.

Gameplay wants `Custom`. That is not a value worth preserving from a moment
before the game had started, so it is now simply asserted, `savedCameraType` is
deleted rather than left to tempt someone, and the subject is named with a
bounded retry for a character that has not finished loading.

**Three sessions, three different causes, same symptom.** The camera being
taken by the engine, then a race with the tour thread, now a saved value from
too early. Worth remembering that "the camera is stuck" is a symptom with a
family of causes, not a bug.

### 2. Light sources are fixtures, not floating objects

Owner-directed: *anything labelled a light source should be static with colour
animations*. The glow was right; the drifting was not.

Five styles lost every attribute that changed their position and kept their
`PulseAlpha`: `Plaza_RimLampCrystals`, `Walkways_GatewayCrystals`,
`District_Leaderboard_CrystalFinials`, `District_Archive_LampCrystals`,
`District_Shop_LanternCrystals`.

The Fate Engine's `CrystalShards` deliberately still orbit — they are part of a
machine, not a light fitting. A test pins the rule and a second pins that the
lamps still pulse, so "make them static" cannot quietly become "make them
dead".

### 3. The aperture turns against the frame

The outer ring runs +0.22 and the inner −0.31, but the veil between them had no
spin at all — the middle of the machine was the one part standing still. Now
−0.14: opposed to the **outer** ring, which is the one the eye reads first, and
slower than the inner ring so the three layers stay distinguishable instead of
blurring into one direction.

### 4. The hub is about twice player scale — measured, not changed

Owner's test: *if the head clears the shop counters, the map is sized right.*
Measured from the prefab at the shipped `Prefab.Scale = 2.0`:

| Prop | At Scale 2.0 | Should be |
|---|---|---|
| Shop counters | **6.00 studs** | ~3.0 (chest) |
| Railings | **6.70 studs** | ~3.2 (waist) |
| Crates | **28.80 studs** | a crate |

A character is ~5 studs. Three independent human-scale props agree: the set
dressing is about twice the size it should be, and `Prefab.Scale = 1.0` makes
the owner's test pass on both references.

**Deliberately not applied.** `Prefab.Scale` alone breaks the hub: the authored
districts scale with the shell, but the walkways, spawn ring, travel landings,
prompt reach and portal scales are separate `GameConfig.HubLayout` numbers that
would not move with it. It is a coordinated change to every distance in the
game, several pinned by tests, and it should be made with somebody watching it
rather than shipped blind. Full evidence and knock-on list in
`ART_DIRECTION.md`.

### Stopped at

Pushed. The scale change is the first thing to do together.

### Next

1. **The rescale**, with eyes on it: `Prefab.Scale` and every `HubLayout`
   distance, in one pass.
2. The rest of the walk — travel landings, district tint, event sky.
3. Sound; then `scheduledAt` and the rift portal.

---

## Session 33 — 2026-09-21 — The second walk: a button that ate its label, and settings that saved nothing

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 559 passing · **PR:** #27

Three more from Studio. All three are the same class as the last three: things
that only exist once a person is holding the mouse.

### 1. The TRAVEL buttons swallowed their own rows

A screenshot of the Travel panel showed four rows that were nothing but a
full-width yellow TRAVEL button — no destination name, no subtitle. The fifth
row, the one never clicked, was fine.

`UIKit.button`'s press animation shrank the button by 3px on mouse-down and
then tweened it back to **`UDim2.new(1, 0, 0, 44)`** — the size the
*constructor* happens to use. Every caller that resizes its button afterwards
(the travel rows are 104×38) therefore had it snap to full width on the first
click and stay there, covering the label beside it.

Now the resting size is captured **at press time**, so a button returns to
wherever it currently belongs rather than to where it started life. Mouse-leave
releases it too, so dragging off a pressed button no longer leaves it shrunk.

### 2. The camera release lost a race it did not know it was in

Reported as "camera is still stuck" — the tour's last frame, frozen, not
following the player.

Session 32 fixed the camera being *taken* by Roblox's camera script mid-load by
re-asserting `Scriptable` every frame. That fix then caused this one:
`RenderStepped:Wait()` returns mid-frame, so `finish()` could run **while the
tour loop was suspended**, hand the camera back — and then the loop's next two
lines would take it straight back and pin it forever.

Fixed on both sides, because one would have been another race:
- The tour returns immediately if `finished`, **before** touching the camera.
- `releaseCamera` runs again a frame later, by which point the tour has
  certainly stopped.

And a second cause underneath it: restoring `CameraType` is not enough.
While the tour held the camera, Roblox's camera script never got to point it at
anything, so a camera set back to `Custom` with **no `CameraSubject`** simply
stays where it was left — which looks exactly like a camera that is still
stuck. Naming the humanoid is what actually gives control back.

### 3. The Settings panel saved everything and applied nothing

Correctly reported, and it was true: `SettingsCore` declared, `StateController`
held and synced, and nothing anywhere *applied*. Three of the seven now do
something real:

| | |
|---|---|
| Music / Effects | Two `SoundGroup`s, created **before any sound exists** — a sound added to a game with no routing is a sound that ships ignoring the volume slider |
| Interface size | A `UIScale` on every Luckbound ScreenGui, including ones built later |
| Others' rolls | Suppresses other players' roll banners. Your own result and anything world-scale still arrive — those are not chatter |

Reduce motion and Start-with-menu-hidden already worked. **Screen shake is
still inert and now says so**, with a `SettingsController.screenShake()` for
whoever builds a shake to honour from its first frame. `PLAYER_UI.md` §3.6 is
the honest table of what drives what.

### The pattern in six bugs across two walks

Not one of them was a logic error a test could have caught. They were: an Enum
name, a guessed constant, a camera the engine also owns, a tween restoring the
wrong value, a race between two threads, and a layer that was never written.
**Every one needed a person holding the mouse.** The suite is doing its job —
it is just not the job of finding these.

### Stopped at

Pushed to PR #27. Tests J and L–N are still unwalked.

### Next

1. The rest of the walk: travel landings, the district tint, the event sky.
2. Sound. The groups exist and the sliders drive them; nothing plays.
3. Then `EventCore.scheduledAt` and the rift portal.

---

## Session 32 — 2026-09-21 — The first walk of the UI, and three bugs 551 tests could not see

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 559 passing (was 551)

The hub UI was rendered for the first time. It works: the rail draws in the
owner's order, the Fate card reads, the Crossroads looks like a place. Three
things were wrong, and the interesting part is *why none of them were caught*.

### 1. Every keystroke threw

```
Backslash is not a valid member of "Enum.KeyCode"  -- HubMenu:607
```

Content named the collapse key `"Backslash"`. Roblox calls it **`BackSlash`**,
with a capital S. And indexing an Enum with a name it does not have **raises**
— it does not return nil — so the handler threw on *every key pressed*, twice a
second in the output, and died before it reached the panel shortcuts. None of
the seven hotkeys worked.

**Why the tests missed it:** the harness shims `Enum` permissively, returning
an item for any name asked of it. A test could not have told the difference.
That is the CLAUDE.md shim rule again, in its subtlest form yet — the shim was
not *wrong*, it was more forgiving than the engine.

**Fixed three ways**, because one was not enough:
- `Constants.HOTKEY_NAMES` — an explicit list of names content may use, which
  the suite *can* see. `BackSlash` is in it with a comment saying the capital
  S is not a typo.
- `Schema.validateHubMenu` refuses an unknown name at boot, with the name in
  the message.
- The client resolves hotkeys **once at init** through a guarded lookup, not
  per keystroke inside the handler — the slowest possible place to put an Enum
  index and the worst place for it to throw.

### 2. The loading screen could never finish

The bar stopped at ~94% and every player waited out the 25-second timeout to
be told loading had *"taken longer than usual"*.

`RequiredHubInstances = 380`. The hub builds **357**. The number was a guess,
it was wrong the day it was written, and it would have gone wrong again every
time the art changed.

**The fix is to stop counting.** Replication is now judged by its *shape*:
instances arrive, and then they stop arriving. When the descendant count has
not moved for `HubSettleSeconds`, the hub is here — however many parts it
turns out to have. There is no number left to get wrong.

**Why the tests missed it:** there *was* a test, and it asserted
`RequiredHubInstances <= 436`. 380 passes that. The test checked the number was
not absurd; it could not check the number was *right*, because the right answer
only exists at runtime. A test that asserts a literal is under another literal
proves nothing about the world — the same lesson STATUS §4 already records
about the hub having no floor while 276 tests passed.

### 3. The camera stopped moving, and two glyphs were boxes

"Camera locks in place." It had not locked — it had been **handed back**. When
the character spawns, Roblox's own camera script sets `CameraType` to `Custom`
and starts following the humanoid, so the loading tour was writing CFrames to a
camera that was no longer listening. It now re-asserts `Scriptable` every frame
and re-acquires `CurrentCamera`, because the engine can also replace the camera
object outright on spawn.

The tour was also genuinely too slow to read as motion — 26° over 9 seconds is
under 3°/s. Now 52° with a gentle dolly in, and a test asserts the arc rate
stays above 4°/s.

`✦` and `⟲` rendered as empty boxes: Roblox's font does not carry every symbol
a text editor will happily show you. Now `★` and `↺`. **A glyph must be seen in
Studio before it is trusted** — there is no headless test for font coverage.

### Stopped at

All three fixed, 559 tests green, pushed. The rest of test I–N is unwalked:
the hub menu's panels, travel, the district tint and the event sky have not
been exercised yet.

### Next

1. **Walk the rest.** Tests J (menu), L (tint), M (event sky) in particular —
   M step 5, an event running across an expedition boundary, is the likeliest
   remaining bug.
2. The DataStore warning in the log is expected in Studio — but note it means
   **no unique can be granted there**, by design. Test N needs a published
   place.
3. Then `EventCore.scheduledAt` and the rift portal, as before.

---

## Session 31 — 2026-09-20 — Events become content, and scarcity becomes true

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 551 passing (was 514)

The owner answered the five open event questions, and two of the answers
**removed** work rather than adding it. `docs/EVENTS.md` now carries the
catalogue, the Rift design and every decision with its reasoning.

### The decisions (EVENTS.md §6, STATUS D-10..D-14)

| | |
|---|---|
| **Rift rewards** | The item is **permanent**; only the window is temporary. No decay, no charge — so **no expiry attribute on the item schema** |
| **Who gets in** | The finder gets the *item*, everyone gets the *event*. Ten Stars = ten game-wide occasions |
| **Failure** | Costs the attempt, not the event — so **no per-player attempt counter** |
| **Convergence** | D-8-safe: it changes which pool you draw from, never how the draw resolves |
| **Loudness** | Three tiers, AMBIENT / MODIFIER / WORLD, enforced by the validator rather than by convention |

**Q1 and Q3 between them deleted two systems** that the alternative readings
would have required. The debt they create is §5.6: a permanent
event-exclusive reward is only fair while events recur. If recurrence is
dropped, D-10 has to be reopened with it.

### The conflict the owner caught

Worth recording in full, because it is the kind of thing that only shows up
when two features meet. The planned progression lever is that **Fate unlocks
which pools you draw from** — at a high enough tier, Commons stop appearing.
Now put a rift in Verdant Valley: a high-tier player **cannot roll that world
any more**, so the event they are invited to is one they cannot reach. The
better you do, the fewer events you can attend.

Resolved as **D-13: event access never depends on the roll pool.** A biome
with a live event is directly enterable for the duration. The roll decides
where you go when rolling; an event decides where you may go while it runs.
Two doors, two locks.

### What was built

- **`Content/Events/`** — three authored events. Aurora Veil is the AMBIENT
  worked example and exists to argue that some weather should just be weather.
- **`Schema.validateEvents`** — the tier rules, scope rules, placeholder
  checking, and the one that matters most: **an event may only write lighting
  properties that something restores.** That list now lives once in
  `EventCore` and `ExpeditionController` derives its restore list from it.
- **`EventSystem.trigger(id, player)`** — claim first, announce second. A
  refused claim means nothing happened: no event, no sky, no announcement.
- **`SkyController`** — per-client lighting, a mote layer and a colour grade,
  reverting exactly. It releases the sky when an expedition starts and takes
  it back on return, because otherwise `ExpeditionController` would snapshot
  an event-altered hub as "the hub" and restore that forever.
- **`/event <ID>` and `/ledger <ID>`** — a unique started this way **still
  claims from the ledger**, deliberately: testing the sky must not be a way to
  mint an eleventh Star.

### Stopped at

All green, nothing rendered. Two Studio tests are new and one of them is
unusual: **test N needs two instances on a published place**, because a
concurrency bug cannot be seen headlessly or by eye. Claims made while testing
are permanent — ten is ten.

### Next

1. Walk tests I–N. Test M step 5 (an event running when you enter and leave an
   expedition) is the likeliest thing to be wrong.
2. `EventCore.scheduledAt` — scheduled events need no cross-server
   coordination at all if they are a pure function of UTC time. Cheapest class
   in the catalogue and it unlocks the seasonal recurrence D-10 depends on.
3. The rift portal with an empty room behind it, which proves placement,
   gating and the timer without waiting for combat.

---

## Session 30 — 2026-09-20 — The menu learns where it is standing

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 514 passing (was 473)

Owner direction: the menu should change colour with the area and with live
events. There is no day/night cycle and there will not be one — instead,
**events** at three scopes (global, server, biome) will shape the sky. This
session built the half that can be built now.

### What was built

| | |
|---|---|
| `EventCore.Scope` + `dominant()` | Three scopes and one deterministic answer to "which event owns the sky" |
| `ThemeCore` | The live palette, the contrast floor, and which district a point is in. Pure |
| `Content/Hub/Palettes` | How far the menu leans, per district and per event kind |
| `EventController` | The client's event mirror, which **expires events itself** |
| `ThemeController` | Resolves and paints, on a timer, never per frame |
| `/event` and `/endevents` | Start any event on demand — the only way to walk a 1-in-a-trillion sky |

### The measurement that changed the design

A plain mix toward a district colour **lightens** the surface, and the menu's
faintest text sits only ~5:1 above that surface to begin with. Measured: 20%
toward starlight took a raised row from 5.06:1 to **2.96:1** — unreadable. So
every interesting tint would have been clawed back by the contrast clamp, and
what content asked for would not have been what rendered.

`ThemeCore` therefore mixes in **linear light and rescales back to the
surface's original luminance**: the surface takes the district's hue and keeps
its own brightness. Contrast survives a tint essentially unchanged, the clamp
becomes a backstop that rarely fires, and the strengths in content can be
interesting rather than timid. It is also the better look — the menu stays
dark and shifts colour rather than fading toward whatever it is standing next
to.

The stroke is the deliberate exception and mixes straight: nothing is read
against a 1px edge, and it is the part that reads best. **Surfaces lean; the
edge speaks.**

### What the contrast test found on its first run

`TextMuted` shipped last session at **3.40:1** against a raised row — below
WCAG's 4.5:1 floor for body text, which a 13px row subtitle is by any honest
reading. Nothing to do with the tint; it was wrong the day it was written.
Contrast failure is invisible to whoever picks the colour and obvious to
whoever cannot read it, which is exactly the kind of bug a test should find
and an eye should not be asked to. Raised to (145, 139, 170), now 5.06:1 at
worst. It is closer to `TextSecondary` now, so the two roles lean more on size
and letter-spacing — worth a look in Studio.

### Decisions made

**Scope outranks priority.** A game-wide event is by definition the biggest
news on screen; a local event with a big number must not shout over it.

**A tie goes to the event running longest, not the newest.** A tie broken by
recency would flip the sky whenever an equal event started somewhere, and a
sky that changes for no reason the player can see reads as a bug.

**The client expires events itself.** The server says "N seconds left" and
never promises to say when it ends. Cross-server messages are lossy and
servers die; local expiry means the world heals itself.

**An event with no scope is a SERVER event.** The narrowest honest default —
a missing field must not be able to announce itself to the whole game.

**Only surfaces tint, never semantics.** Gold means "press this", teal means
"designed, not built", rarity colours are a contract — and two of those
collide with authored district colours (the Archive's accent *is* that teal,
the Hall's *is* that gold). A test asserts no semantic token ever appears in a
resolved palette.

### The harness learned a second lesson

The `Color3` shim carried only the arguments it was constructed with — no
`R`/`G`/`B` floats, no `Lerp`. Any code doing colour *maths* was therefore
untestable, which is the same trap the `Vector3` shim fell into and the same
one CLAUDE.md already records. It now carries linear-ready floats, lerps and
compares by value.

### Stopped at

Pushed, all green, **nothing rendered**. The tint is subtle by construction on
dark surfaces and may want to be stronger; `Content/Hub/Palettes` is the only
dial. `TESTING.md` test L walks it.

### Next

1. **Walk test L** along with I, J and K.
2. **The owner is choosing between options** for the rest: the global ledger
   that makes "only 10 will ever exist" true, what the sky actually does, and
   how events are authored. None of it is started.
3. `EventSystem` still publishes cross-server as fire-and-forget. That is fine
   for spectacle and **not** fine for scarcity — see STATUS §4.

---

## Session 29 — 2026-09-20 — Three owner corrections to the hub UI

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 473 passing (was 472)

Owner review of Session 28's UI. Three changes, all small, all directed.

### EXIT is gone

The loading screen has **one button**. Roblox gives no way to close the app
from inside a place, so EXIT could only ever kick the player back to the app's
home screen — a button whose best outcome is leaving. A title screen offering
one thing is stronger than one offering a choice nobody wants to make. The
`controls` frame lost 32px with it.

### Travel has no cooldown

`TeleportCooldownSeconds` is **deleted**, not set to zero, along with
`HubMenuCore.travelCooldownRemaining` and the per-frame loop that drove the
buttons' countdown. Owner-directed: travel should be quick and effectively
instantaneous.

The fades came down with it — 0.45/0.25/0.55 to **0.22/0.06/0.28**, about half
a second end to end, which reads as a cut rather than a wait. That fade is now
the *only* thing between pressing TRAVEL and arriving, so it is asserted to
stay under 0.75s as well as above zero.

The server's rate limit stays and went **up**, 20/min to 60. It is not a
cooldown wearing another name: a player pressing the button as fast as they
can will never meet it, and a script firing the remote in a loop will. A test
pins both halves — that the cooldown field does not exist, and that the limit
is far above human speed. Removing only the *check* would have left the number
sitting there for the next session to wire back up.

### The rail is in the owner's order

Travel, Party, Fate Tree, Rebirth, Shop, Codes, Settings. The blocks were
sorted in the content file too, so the file reads in the same order as the
rail. It groups by what a player is doing — get somewhere, get someone, the
two progression screens that talk to each other, the two transactional ones,
then Settings — and a test pins the sequence, because add-order drift would
undo it silently.

### Stopped at

Pushed. Still nothing rendered in Studio; `TESTING.md` tests I, J and K are
updated for all three changes (the rail order is now step 1 of test J).

### Next

Unchanged from Session 28: walk the UI, then the Crossroads.

---

## Session 28 — 2026-09-20 — The hub gets a face

**Branch:** `claude/player-ui-crossroads-gui-2accal` · **Tests:** 472 passing (was 378)

The game had no way to talk to the player except a prompt and a result card.
It now has a loading screen, a side rail with seven panels, travel to all five
Crossroads locations, redeemable codes, saved settings, and two player
abilities. **None of it has been rendered** — see below.

### What was built

| | |
|---|---|
| **Loading screen** | Blurred camera tour over six hub subjects, title, progress, PLAY and EXIT. `UI/LoadingScreen` + `Content/Hub/Cinematics` |
| **Hub menu** | A collapsible left rail, seven panels, one open at a time. `UI/HubMenu` + `Content/Hub/Menu` |
| **Travel** | Five destinations, server-authorised, 6s cooldown, screen fade. `HubMenuCore` + `HubUISystem` |
| **Codes** | Three shipped codes, redeem-once, rate-limited. `CodeCore` + `Content/Codes` |
| **Settings** | Seven, validated and persisted. `SettingsCore`, profile schema v2 |
| **Abilities** | Sprint with stamina, and a double jump with a coyote window. `LocomotionCore` + `LocomotionController` |
| **Widget kit** | `UI/UIKit` — the only place a tween is created in the hub UI |

### Decisions made

**The menu exists in the Crossroads and nowhere else**, and that rule is one
pure function (`HubMenuCore.isVisible`) that the client and the server both
call. An expedition is meant to be the game rather than a screen with the game
behind it. It also hides itself during a roll: the reveal is the four seconds
the whole thing rests on and must not be framed by a rail.

**Collapsing hides the rail entirely** rather than shrinking it to a strip of
glyphs. The ask was for the screen back, and a rail of icons is still a rail on
the screen. Collapsing closes any open panel for the same reason.

**Four panels ship designed but labelled.** Shop, Fate Tree, Party and Rebirth
draw their real layout over placeholder copy with an IN DESIGN badge, because
the direction was "designed now, implemented after testing" and a button that
silently does nothing is worse than no button. **They own no remotes** — a
panel gets a remote when it gets an implementation.

**A player has movement; an item has combat.** Sprint and double jump are the
whole of Phase 1's player abilities, and damage, effects and animations belong
to the model that grants them. This is now pinned by a test that fails the
build if `GameConfig.Locomotion` grows a field whose name contains damage,
attack, crit or dps. `docs/PLAYER_ABILITIES.md` holds the planned ladder and
the Fate Tree's four branches — the "more ideas for what to upgrade" request.

**Travel sends a destination Id and nothing else.** The server looks the Id up
in Content, takes the anchor from `GameConfig`, and finds the Y by raycasting
down onto the deck — because the authored districts' heights are a property of
a mesh nothing in code can measure. An unknown Id is refused by name.

**Five remotes were added to build spec §4 in the same change** as the code
that uses them, which is the rule that table exists to enforce.

### One thing the harness learned

The shimmed `Vector3` was a plain table with no operators, so `anchor +
landing` — the expression the whole travel system rests on — would have raised
in the test harness while working perfectly in Studio, and the likely outcome
is that the *test* gets deleted. It now adds, subtracts, scales and compares by
value, like the real one. Same lesson as the `Vector3`-as-table bug already
recorded in CLAUDE.md.

### Stopped at

Everything is written, tested headlessly and pushed. **Nothing has been seen in
Studio.** The loading screen's blur, the rail's feel on a phone, and whether
the five travel landings actually put a player on the deck are all reasoned
rather than observed.

### Next

1. **Walk the UI.** `TESTING.md` tests I, J and K — they were written for this.
   Watch the server output for `no floor under landing for '<Id>'`.
2. **Then the Crossroads walk** that was next before this session (STATUS §5).
3. **Sound.** Every beat here wants one — the rail opening, PLAY, a code
   accepted — and there is no audio system at all.
4. **Decide whether the Fate Tree's four branches are the right four** before
   any of it is built. `PLAYER_ABILITIES.md` §3 is the proposal, not a
   decision.

---

## Session 27 — 2026-09-18 — The portal turns, and the hub breathes

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 378 passing (was 369)

The hub was accepted as good enough to build on. Two things were added to it:
the Fate Engine's portal now turns and stops somewhere meaningful, and about
fifty pieces of the Crossroads that were inert now move.

### The portal turns, and stops square to the hub

The rings already spun about their own axle like a wheel. The portal
**assembly** — both rings, the veil, the gold clamps and the levitation core —
now also turns about the hub's vertical axis, so the aperture sweeps the plaza
instead of facing one direction forever.

| | |
|---|---|
| `YawIdleSpeed` 0.22 rad/s | matched to `OuterRing`'s own spin, so the two read as one mechanism rather than two machines bolted together |
| `YawSlots` 4 | it may only stop square to the hub — facing a walkway, which is where a staircase up to it has to land |

It rides the same `SpinBoost` ramp the rings do, so a roll winds it up for
free. What is new is the **stop**: on settle it eases onto the next quarter-turn
slot and holds there until the next roll.

**Why the next slot and not the nearest.** The target is the first slot the
portal has not already passed by the time it could plausibly stop. Choosing the
nearest would make it stop dead or reverse, and reversing a machine that has
been turning one way for a minute reads as broken rather than deliberate.

**Why the yaw is one module-level number** rather than a per-part attribute
like every other motion in `HubEffects`: every piece must turn by exactly the
same amount, and accumulating an angle per part would let them drift apart over
minutes of float error. That is precisely the failure the two rings already had
once, when they were given independent wobble periods and the inner assembly
swung out through the outer aperture.

It is also a state machine, which an attribute is not — free-running, then
riding the ramp, then eased to a dead stop, then locked.

**One assumption, pinned by test.** The yaw is applied about the *world*
vertical through the origin, which is only the Engine's own axis because the
Engine sits there. A test asserts `Anchors.FATE_ENGINE` is the origin, because
that line is silently wrong anywhere else.

### `YawFollow` is a style field, not an attribute

It would have been natural to put it in a style's `Attributes` table. That
turned out to be a trap worth recording: those tables carry multi-line
commentary, and a script that merges into one flattens the comment onto a
single line and **comments out everything after it**. A flag that has to be
merged into commented Lua is a flag that will one day be merged into a comment.

It is a first-class field alongside `SizeScale` and `CollisionFidelity`, and
`PrefabLoader` sets the attribute from it.

### The animation pass

About fifty parts of the Crossroads read as painted-on. Now:

| | Count | Cost |
|---|---|---|
| Spin, bob or wobble | **26** | a CFrame write every frame |
| Transparency pulse | **24** | 20 Hz, effectively free |

The rule applied: **anything that glows should breathe, anything crystalline
should drift, and anything made of cloth or leaves should move in the wind.**
The long tail of floor inlays and rune rings gets pulses only; per-frame motion
is spent on the pieces a player walks right past — shrine crystals, lamp
crystals, gateway crystals, banners and tree canopies.

Periods are deliberately unequal across districts so the four do not breathe in
unison, and canopies get 1.4° on a nine-second period — anything more and
low-poly foliage reads as rubber rather than as leaves.

**A budget test now caps it.** Per-frame styles are capped at 30, and the suite
also asserts the hub animates *enough* to feel alive, and that culling happens
before the far side of a 1300-stud plaza.

### Stopped at

378 passing, all gates green. **None of it has been seen in Studio.**

### Next

1. Walk it: the portal's turn and its stop, and whether fifty animated parts
   cost anything noticeable.
2. **The staircase.** Deliberately not built — the owner asked whether to author
   it in Blender or generate it in Studio, and that decision shapes the work.
   The recommendation given: **author ONE step in Blender**, and have code clone
   and stack it. That is the same pattern the mountain ring just proved —
   authored look, procedural placement — and it means the staircase can be
   built to whatever height and slot the portal actually stops at, rather than
   being a fixed model that only fits one configuration.
3. Then the Fate Engine's entry logic, which is still the only planned way into
   a biome and still does not exist.

---

## Session 26 — 2026-09-18 — The horizon is built, not placed

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 369 passing

Third walk, one fault: the mountains still clipped the hub and were still too
close, at Scale 3.0. This entry is about why scaling was never going to fix it.

### Three scales, three failures

| Scale | Ring across | Result |
|---|---|---|
| 2.0 (as authored) | 4096 | "far too large" |
| 1.0 | 2048 | clipped through the plaza |
| 3.0 | 6144 | **still clipping** |

**The distance from the hub to the nearest peak is a property of the mesh
geometry**, which lives in a Roblox asset id — nothing in this repo can
measure it. Every scale was therefore a guess dressed up as a calculation. The
bounding box says where the ring *ends* and says nothing about where it
*begins*, which is the only number that mattered.

And scaling could not separate the two things anyway:

> A uniform scale moves the ring closer as it shrinks, so height and radius
> fall together and the mountains subtend the same angle from the hub's centre
> at any scale. Scaling cannot make them look smaller from where players
> stand. All it changes is how far away they are.

### The fix was the owner's suggestion, and it is better than what it replaced

Take one chunk of mountain, stand it a set distance beyond the crossroads, and
clone it around a circle. **Distance stops being emergent and becomes a number
we choose** — and a number is testable.

```
Part    Backdrop_Mountain     Count   14        Radius  2400
Scale   1.0                   BaseY   -68.4475  Seed    20260918
```

Every one chosen against measured hub geometry: plaza edge 653, ground skirt
1097, chunk half-width 1024 — giving a band from 1376 to 3424, so **723 studs
of clear sky** past the crossroads edge and **279** past the ground skirt,
with the far face inside `FogEnd` so the range fades rather than ending.

Chunks are *meant* to overlap: 1.9x coverage, with yaw and scale jittered from
a seeded `Random`. A single chunk is a ragged mass; overlapping rotated copies
turn a repeated mesh into a continuous range rather than a ring of identical
lumps. One skyline per server, the same rule the floating islands follow.

`buildBackdrop` is now shaped exactly like `buildFloatingIslands`, which is the
right precedent — content declares count, radius and seed; the System holds no
numbers.

### The assertion that was missing all along

None of the three failed attempts had a test that could fail, because with a
whole placed model there was no number to assert against — only `Scale`, which
is not the thing anyone cares about. The gap is now asserted directly:

```
the mountains stand 500-1000 studs clear of the crossroads edge
```

plus ground clearance, fog, coverage ratio, and that the chunks stand on the
same ground plane as the plaza.

**To retune it, change `Radius`, never `Scale`.** `Scale` sets how big each
massif is; `Radius` is the distance, which is what every complaint about this
horizon has actually been about.

### Stopped at

369 passing, all gates green. Verified: band 1376..3424, 723 studs of clear
sky, 279 past the ground, 1.90x coverage, ground plane -68.4475 matching the
shell exactly.

**Not re-walked.**

### Next

1. Walk it.
2. Then the Fate Engine's entry logic — still the only planned way into a
   biome, and still not built.

---

## Session 25 — 2026-09-18 — The second walk: distance, height, kerbs, flags

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 369 passing (was 367)

Four faults from the second walk of the authored hub. Two of them are
corrections to Session 23's own fixes, which is the useful part of this entry.

### The horizon: 2.0 → 1.0 → 3.0, and the round trip is the lesson

Session 23 shrank the ring from 4096 studs to 2048 because it read as "far too
large". That made it smaller **and brought it inside the hub's own ground
skirt (1097 studs)**, where the peaks clipped through the plaza edge — which is
what the second walk actually objected to.

**The trap, written down so nobody walks into it a third time:** a uniform
scale moves the ring closer as it shrinks, so height and radius fall together
and the mountains subtend **the same angle from the hub's centre at any
scale**. Scaling cannot make them look smaller from where players stand. All
it changes is how far away they are.

So the only question worth asking is distance. At **3.0** the ring is 6144
across, outer radius 3072 — **1975 studs clear of the hub's ground skirt** —
and still inside `FogEnd` 4400 so it is visible rather than swallowed.

The test that would have caught the clipping now exists: it asserts the ring
clears the **ground skirt**, not merely the plaza. Clearing the plaza was true
at Scale 1.0 and meant nothing.

### The Engine: flush with the plaza, not with the walkways

Session 23 lowered the dais to `WalkwayRaise` (1.5), flush with the four paths.
That still left a 1.5-stud step for anyone crossing the **open plaza**, which
is most of the approach angles.

It now sits at **Y 0**, on the plaza. Arriving along a walkway is a step
*down* onto it, which is free in Roblox; stepping *up* is the thing that
catches. Confirmed the 1.934 figure is the walkable deck and not a rim by
measuring the concentric inlays, which sit on it at 1.933.

### The kerbs stopped 40 studs short

Measured: every walkway runs radius 20 → 400, but its kerbs were authored
60 → 400. So each path had 40 studs of bare deck and the black edging ended in
mid-air before the dais.

`PrefabLoader` gained `ExtendInwardTo`: it grows a bar toward the hub centre
until its inner end reaches a given radius, keeping the outer end fixed.
Stretching a MeshPart's `Size` along its own length is safe **here** precisely
because these are straight extruded bars with no detail along that axis — so
it is opt-in per style, never applied to everything that stops short. It also
refuses to shrink a part, because silently cropping one that already reaches
would be a far harder bug to see.

### The flags, on their third colour

`Basalt` read as black. Gold read as wrong. Owner-directed: match the
crystal-and-pedestal objects the rest of the hub is dressed with — so the
cloth is now the same dimmed teal (`Theme.Inlay`, Neon, 0.3 transparent) as
the shrine and lamp crystals, and the poles are pale stone like the pedestals
under them.

### Stopped at

369 passing, all gates green. Verified against the delivered files: dais top
`0.000`, ring radius 3072 with 1975 studs of clearance, ground planes agreeing
at −68.448, kerbs extending to 20 against a 23-stud dais.

**Not re-walked.**

### Next

1. Walk it.
2. Then the Fate Engine's entry logic — still the only planned way into a
   biome, and still not built.

---

## Session 24 — 2026-09-18 — One property took down the whole hub

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 367 passing

Session 23's collision fix did not boot. The Crossroads did not render at all,
and the log said why in one line:

```
The current thread cannot write 'CollisionFidelity' (lacking capability Plugin)
  PrefabLoader, Line 257 - function build
```

**`MeshPart.CollisionFidelity` cannot be assigned at runtime.** It is plugin
security, exactly like `MeshId` — which this project already has a comment
about, in this same file, from the last time it happened. The throw killed
`PrefabLoader.build`, which killed `HubBuilder.build`, so boot stopped at 9/11
and there was no hub at all. One property, whole world.

### The fix, and why it is in the asset rather than the code

`CollisionFidelity` is a *serialized* property, so the value belongs in the
`.rbxmx`. Baked into the 30 parts that need it as
`<token name="CollisionFidelity">3</token>`, and verified by reparsing the
file — 225 MeshParts, 30 carrying fidelity 3, exactly the intended set.

**Content still declares it.** `Crossroads.Shell.Styles` remains the one place
to read what a piece is supposed to be; `PrefabLoader` now **checks the asset
agrees** and warns by name when it does not, instead of trying to set it. That
warning is the only thing standing between a re-delivery and a hub full of
invisible walls, because a fresh export from Studio carries no fidelity at all
and every precise part would silently drop back to `Default`.

### The lesson worth carrying

Two properties on `MeshPart` are now known to be script-unwritable: `MeshId`
and `CollisionFidelity`. Both were discovered the same way — by a seam that
looked correct, passed every headless test, and did nothing (or worse) in
engine. **A content field that maps to a Roblox property is not proven until
it has been set in a running place.** The headless suite can assert that
content declares the right value; it cannot assert Roblox will accept it.

The difference this time: it threw rather than failing quietly, and the thing
it took down was load-bearing. That is the better failure of the two.

### Stopped at

367 passing, all gates green. The hub builds again in principle — **not yet
re-walked.**

### Next

1. Walk it. Same list as Session 23, which no longer applies to anything that
   has actually been seen.
2. Then the Fate Engine's entry logic.

---

## Session 23 — 2026-09-18 — The first walk of the authored hub

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 367 passing (was 361)

The Crossroads was walked in Studio for the first time. The verdict was *"looks
very nice in general"* with seven specific faults, all fixed the same day. This
entry is mostly about what a walk found that 361 green tests could not.

### It did not load at first, and that was not a code fault

The first run showed the old blockout hub. The log gave it away by what was
**missing**: no `Shell: authored HUB_CROSSROADS` line, but also no
`prefab not found ... using the blockout instead` warning. Getting neither
means execution never reached that check — `Layout.Shell` was nil.

`C:\Dev\luckbound`, the checkout Rojo serves, was on `claude/zen-volta-cuhfyh`
at `07b3ea3`: two merges behind, with no `Shell` in its content file at all.
**Merging to GitHub does not move the working checkout**, and a worktree is a
separate directory. Worth remembering — the symptom looks exactly like a
broken asset path.

### What the walk found

**Collision, and the first pass had it backwards.** Session 22 granted
collision to 57 of 225 parts and left every merged or hollow mesh
pass-through — the safe half of a choice that could not be checked headlessly,
chosen because a `Default` hull on an archway seals the walkway behind it. The
walk found the cost immediately: **players sank into the flanks of district
platforms and walked through railings.**

It is now **91 of 225, with 30 at `PreciseConvexDecomposition`** — the arches,
colonnades, balustrades, walls, pylons, stalls, seating, dummies and racks
whose openings are the point. Skirts collide at `Default`, because a skirt is
a solid frustum and is exactly the piece players were sinking into.

> The rule this settles, now in `ART_DIRECTION.md`: **collision and fidelity
> are decided together, never separately.** Both halves cost a playtest.

**The horizon was three times the hub.** At the authored Scale 2.0 the ring
was 4096 studs across against a 1305-stud plaza. Retuned to **1.0**: 2048
across, 1.57× the plaza, outer radius 1024 falling just inside the hub's own
ground skirt at 1097 — so the mountains rise *from* the island rather than
floating past its edge. That nesting is why 1.0 and not another number.

Two things fell out of that which are worth writing down:

- **`AnchorOffset.Y` is scale-dependent.** It is multiplied by `Scale`, so
  rescaling silently moves the model's ground plane. The formula
  (`registrationSourceY = 68.4475 / Scale`) is now in the prefab README, and
  the test that guards it was rewritten to compare ground planes **in world
  studs** rather than source units — which only meant the same thing while the
  two models shared a scale.
- **A uniform scale cannot change apparent size from the centre.** Height and
  radius fall together, so the mountains subtend the same angle wherever the
  scale lands. What changes is how they read from the plaza's *edge* and how
  big they look beside the hub in a wide shot. Recorded so the next person
  retuning it does not expect the other thing.

**The Engine was not flush with its paths.** Measured: `Platform`'s top face
sits 1.934 studs above the model pivot at Scale, against a walkway deck at
`WalkwayRaise` 1.5 — so the dais stood 0.43 proud of every path meeting it.
`FateEngine.Prefab.Offset` now lowers it by the difference, derived from
`WalkwayRaise` rather than typed, and a test pins the result rather than the
input.

**Things that were painted read as unpainted.** Gateway arches, banners,
training dummies, braziers and weapon racks were all reported as
"uncolored". They were painted — in `Basalt` (64,58,78) and `Slate`
(88,82,104) — and at `ClockTime 4.5` those simply read as black against a
night sky. The palette did not change; those pieces moved one step up it.
**When something reads as unpainted here, suspect the value before the paint
table.**

### Two things removed, one added

**The Expedition Gate is gone entirely.** Session 22 kept an invisible `ENTER`
prompt on the market so entry still worked. The walk rejected that outright —
*"Verdant Valley teleport remains in shop area, this should not be here"* —
and the Fate Engine's portal takes the job. `ensureContract` no longer puts
one back either, because it would have resurrected the prompt the moment
anyone saved the built hub into the place.

**This leaves no in-world way into an expedition**, and that is deliberate
rather than an oversight. `ExpeditionSystem` already tolerated a missing
anchor — it warns that entry is remote-only and carries on — so `/enter` still
works for testing. A test pins the absence so it cannot be closed by accident.

**The spawn is a ring now.** Eight invisible pads at radius 34, just clear of
the 23.4-stud dais, each facing the Engine. The single pad 250 studs down the
processional meant every player began with a long walk to the only interactive
thing in the game; the ring honours "the first frame must contain the thing
the game is about" without charging for it. `HubBuilder` also removes the
place's default `Baseplate` and `SpawnLocation` at boot — the Baseplate sits
at Y 0, exactly where the authored plaza's top surface is.

### Accepted, not fixed

The walkways clip slightly into the district stair flights. That is authored
geometry overlapping authored geometry, so fixing it means a re-export, and
the walk called it minimal.

### Stopped at

367 passing. Re-verified against the delivered file: 225 of 225 parts painted,
91 collidable, 30 precise; the dais lands at exactly 1.500 against a 1.5
walkway; the horizon's ground plane at −68.447 matching the hub's.

**None of the fixes have been walked.** Everything in this entry is reasoned
and asserted, not seen.

### Next, when work resumes

1. **Walk it again** — the collision restoration above all. The risk has moved
   from "invisible walls where there should be none" to "the precise hulls
   cost more at load than the budget allows".
2. **Then the Fate Engine's entry logic**, which is now the only way into a
   biome and does not exist yet. Note the design point already recorded: "keep
   this biome?" is **new game state** between rolling and entering.
3. **Profile on a real low-end device.** Still never measured, and there are
   now 91 generated collision hulls on top of everything else.
4. Then texturing and animation, which is what the hub was cleared for.

---

## Session 22 — 2026-09-18 — The Crossroads arrives, and is measured first

**Branch:** `claude/crossroads-prefab-integration-08761b` · **Tests:** 361 passing (was 328)

The authored hub landed: `Crossroads.rbxmx`, 225 MeshParts, built from the
brief written last session. Plus a second, unbriefed delivery — a mountain
horizon, 4 MeshParts. Both are now wired in, and the generated blockout hub no
longer runs when they are present.

### Everything below was measured before any code was written

That is the whole method, and it paid twice this session. Both deliveries were
parsed straight out of the files — the `.rbxmx` as XML, the binary `.rbxm`
with a small LZ4 reader — and every number in content came from that, not from
the brief and not from an assumption.

**Scale is exactly 2.0.** Studio's importer halved it. Six independent
dimensions agreed to four figures: the Engine's reserved footprint, walkway
width, walkway thickness, walkway length, district deck thickness, and the
district ring radius. Six agreeing measurements is what makes one number the
right correction rather than a guess that happens to look close.

**The compass was 180° out**, and it is the exporter rather than the modeller:
the brief put north at Blender `+Y`, the FBX landed it at Roblox `+Z`, and
`HubLayout.Anchors` has always had north at `-Z`. Confirmed as a pure rotation
and not a mirror — all four districts negated in both X and Z, and all 225
parts with identity rotation. A mirror would have needed a re-export; this
needed a number.

### Two new fields on the prefab seam, and why they are not special-casing

`PrefabLoader` gained `YawDegrees` and `AnchorPart`/`AnchorOffset`. Both are
"how the import landed", which is the file's stated job, and both are general
rather than Crossroads-shaped — the Fate Engine simply declares neither.

The second one is the interesting one. **The model is registered from a named
part, not from its pivot.** The artist's pivot was in fact perfect: the hub
centre at floor level, to four decimals. It is still not what the loader uses,
because a pivot is invisible metadata and invisible metadata is what a
Blender → FBX → Studio → rbxm chain mangles quietly. `EngineReserve` is a part
name — already the contract with the artist, visible in the file, and the one
object in the scene whose whole purpose is to mark that point.

### The collision decision, which is the risky part of this session

**All 225 parts ship with empty `PhysicsData` and no `CollisionFidelity`**, so
Roblox generates every hull at `Default` fidelity on load — and `Default`
fills small openings.

Many of these meshes are several objects merged into one: eight columns in a
ring, four archways, two flanking guardians, a parapet circling the plaza. A
filled hull on `Walkways_Gateways` seals all four walkway mouths. On
`Processional_South_Guardians` it seals the spawn approach. On
`Plaza_RimParapet` it lays a 5.8-stud slab across the whole floor.

That is the `CylinderMesh`-with-a-block-hull bug again, in a new costume, and
it is invisible in the same way.

So collision went to **57 of 225 parts** — the floor, four decks, four
walkways and kerbs, every stair flight, the yard floor, and freestanding
single-volume props. Everything else is walk-through scenery. A player passing
through a balustrade is a small oddity; a player unable to reach the market is
not.

**This is the safe half of a choice that cannot be checked headlessly**, and it
is the first thing to look at on a walk. The escape hatch is a
`CollisionFidelity` line on the one entry that needs it — never `CanCollide`
alone. `PrefabLoader` now honours that field for exactly this reason.

### The Expedition Gate keeps its prompt and loses its portal

The authored south district is a **market**, because the brief asked for the
hub the portal-as-entry direction wants. That amendment has not landed, so
entry still runs through `EXPEDITION_GATE` and still has to work today.

Drawing a monumental portal rig on top of the stalls would be the wrong answer
to that. An invisible anchor at the head of the market stairs is the right one:
`(0, 14, 250)`, measured between the entrance pylons at 248 and the stalls at
256, and 31.5 studs from the stair head — inside the 70-stud prompt reach.
Asserted by test, because a prompt out of reach of the place players stand is
the exact bug the Gate shipped with once already.

### What the delivery does differently from the brief

Recorded rather than corrected — none of it is a fault:

| | Brief | Delivered |
|---|---|---|
| Plaza diameter | 1150 | 1305 |
| `Processional_South` width | 72 | 44 |
| District footprints | 210–320 | 300–400 |
| Pillar ring radius | 520 | 640 |

The plaza still reaches under the furthest district (600 against a 652 radius)
and still covers `HubDiameter`; both are asserted. The processional is no
longer wider than the other three, which costs the spawn approach some
emphasis but breaks nothing.

### 33 new tests

The ones worth naming, because they assert relationships rather than numbers:

- the authored Engine footprint equals the dais radius the hub cuts walkways to
- walkway width, deck step and ring radius all fall out of the same scale
- the plaza reaches under the furthest district, and covers `HubDiameter`
- the compass correction is a quarter turn, not a tilt
- **every surface on the walk from spawn to a district is solid**
- **no merged or hollow mesh collides at `Default` fidelity** — with the six
  worst offenders named in the test, so the reason survives the code
- the horizon shares the hub's scale, yaw and ground plane
- no dressing inherits its platform's collision, including the `.001` suffixes

Paint coverage was verified separately against the delivered file: **225 of
225 parts resolve to a rule**, 184 keys, longest prefix. That check is offline
rather than in CI, because embedding 225 part names in the suite would be
worse than the bug it catches.

### Stopped at

361 passing, CI gates green locally (syntax, forbidden names, tests; selene
`src` unchanged at 3 pre-existing warnings). Nothing opened in Studio.

### Next, when work resumes

1. **Walk the Crossroads.** Nothing here has been seen. In order: does the
   floor hold, do the stairs climb, can you reach the market prompt, and does
   anything invisible stop you. The collision set is the reason to look.
2. **Then colour and animation**, which is the owner's stated next step —
   matching the hub to the Fate Engine's palette now that both are on screen
   together. The paint table is the whole dial; no code needed.
3. **Profile on a real low-end device.** Still never measured, and 225
   MeshParts plus 57 generated collision hulls have just been added to a
   budget that was already carrying four sessions of animation.
4. Then the portal-as-entry spec amendment, and the `EXPEDITION_GATE` → `SHOP`
   swap that follows from it.

---

## Session 21 — 2026-09-18 — The roll ramp, and a brief for the Crossroads

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 328 passing (was 325)

### The Engine had no reaction to a roll at all

Not a tuning problem — a wiring gap. `PortalRig.playSpinUp` set a `State`
attribute and `PortalRig.animate` read it to pick a faster spin. But the
**authored** rings are driven by `HubEffects`, off attributes, and it never read
`State`. So the 2.5-second spin-up — build spec §1.3's "single most important UX
beat" — missed the Engine entirely. The blockout Gate behind it was the only
thing reacting.

**The ramp now lives on one attribute.** `PortalRig` eases `SpinBoost` on the
rig, and every ring inside multiplies its rate by it:

| | |
|---|---|
| `SpinBoostPeak` 5.5× | how hard it winds up |
| `SpinRampUpSeconds` 1.1 | idle → peak, as the roll begins |
| `SpinWindDownSeconds` 2.6 | peak → idle, as the result lands |

Smoothstepped, so there is no kick at the start or jolt at the end, and guarded
by a generation counter — a second roll landing mid-ramp abandons the first
cleanly rather than leaving two loops fighting over one number. Attributes
cannot be tweened, so this is a spawned ease rather than a `TweenService` call.

**The colour is now the answer, and arrives last.** It used to be painted the
instant the player pressed the button, which spent the entire wind-up showing
something already decided. `playSpinUp` stores a `PendingRarity` and paints
nothing; `setIdle` releases the ramp **and** tweens the colour over 1.6s. So the
portal slows down *into* the world you rolled.

A test asserts the three relationships that make that read as one gesture:
the roll winds it up at all, it snaps up faster than it coasts down, and the
colour lands **before** the rings finish slowing — finishing after them would
leave the portal at rest on the wrong colour, which is worse than snapping.

### The Crossroads brief

`docs/CROSSROADS_BLENDER_PROMPT.md`, with a PDF sent to the owner.

Every dimension is read out of `GameConfig.HubLayout` and
`Content/Hub/Crossroads.luau` rather than invented — 1150-stud plaza, districts
at radius 400, walkways 44 wide at Z 1.5, platforms 14 thick at Z 14 — so
authored art meets the walkways the game already cuts to those numbers.

It carries the same three guards the Fate Engine brief earned: the 5-metre scale
reference, staged work with the scene read back after each stage, and a
verification checklist demanding measured numbers rather than assurances. Plus
a new one for a floor plan this large: **do not go overkill.** The temptation on
1150 studs is to fill it, and the portal at the centre is the hero.

**It also reserves the Engine's footprint and asks for nothing inside it** — a
plain `EngineReserve` marker, 60 studs of clear radius, and an explicit
instruction not to model a portal.

**One mismatch, recorded rather than silently resolved.** The four districts the
owner named do not match the four in content: Leaderboard is `HALL_OF_LEGENDS`
renamed, and **Shop replaces `EXPEDITION_GATE`** — which goes redundant under
the portal-as-entry direction. The brief asks for what the finished hub wants;
the district table catches up when that spec amendment lands. Flagged in
`STATUS.md` so it is a decision rather than a discrepancy.

### Stopped at

328 passing. This is the last pass before a break until the Crossroads map is
built.

### Next, when work resumes

1. Walk the roll ramp — it is unverified in-engine.
2. **Profile on a real low-end device.** Four sessions of animation have been
   added on top of a budget that has never been measured.
3. The Crossroads map, from the brief.
4. Then: the portal-as-entry spec amendment, the placeholder staircase, and the
   `EXPEDITION_GATE` → `SHOP` district swap that follows from it.

---

## Session 20 — 2026-09-18 — Nesting, materials, and the barrier that timed out

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 325 passing (was 322)

### The barrier worked, by giving up

The log confirmed the fix — `driving 2 ring(s) OuterRing(MeshPart, spin 0.22)
InnerRing(MeshPart, spin -0.31), plane yes` and `animating 35 part(s), 6
shard(s), 40 orbiter(s)` — but the timestamps told a second story:

```
12:54:06.447  client ready
12:54:26.493  [PortalRig] EngineRig: driving 2 ring(s) ...
```

**Exactly 20 seconds: the timeout, not the condition.** `seen >= PartCount`
never became true, because a client's view of the hub need never match the
server's exactly — a part can be culled, streamed out, or not be a `BasePart`
by the time it arrives. Requiring equality looked rigorous and was simply
wrong.

It now waits for replication to **settle**: three consecutive polls with no new
parts. That asks the question that matters — *has anything arrived recently* —
rather than a stricter one that can never be satisfied.

### Why the rings kept clipping

The owner's close-up showed the pale inner assembly riding outside the dark
scaffold. Three separate causes, all mine, all from the last two sessions:

1. A 6% size pulse on the veil, which grew it through its own frame.
2. **Different wobble periods on the two rings**, so they tilted independently
   — and with ~1 stud of clearance the inner assembly swung straight out
   through the outer aperture.
3. A swell I had *just* added to the outer ring, which shrinks the hole the
   inner ring sits in. The one part I thought was safe to breathe was the one
   part that could not.

Fixed by making the rig nest properly and lean as one object:

| | Studs |
|---|---|
| Outer aperture | 18.00 |
| Inner ring (`SizeScale` 0.88) | 14.02 — **1.99 clear a side** |
| Veil (`SizeScale` 0.82) | 12.49 — inside the ring it fills |

Both rings now share identical wobble degrees and period, so the assembly leans
as one and only the **spin** differs. New `SizeScale` on a style entry sets a
piece into its frame without re-exporting the mesh.

The outer ring's emphasis comes from its spin, its jitter, and four gold clamps
that pulse **against** the ring's rhythm rather than with it — warmth to land on
in a cool palette, and no geometry risk.

### No built-in Roblox materials

Owner-directed, and it matches the house style better than what was there.
Every surface is now `SmoothPlastic`: 21 material references across the Engine
paint table and the blockout hub. `Neon` and `ForceField` stay, because those
are light rather than surface.

Photographic grain fights flat-shaded low-poly geometry — it adds surface noise
to a style whose premise is that facets and colour carry the read. It is also
cheaper: `Glass` is expensive on the phones the §6 checklist budgets for, and
six floating crystals were using it.

Recorded in `ART_DIRECTION.md` with the counter-argument the owner asked for:
if a future model is authored expecting real materials, revisit it **there**
rather than letting one asset drift.

### Logged, not built

**First-join intro screen.** Title over slow cinematic shots of the map until
the player presses Play. The stated purpose is as much technical as aesthetic —
it buys the client time to render and replicate. Directly relevant: the hub
animator already waits for ~450 instances, and that wait is currently invisible
and unexplained to the player.

### Stopped at

325 passing. Three new assertions cover the nesting, the shared sway, and the
no-textures rule — each one a bug that actually shipped.

### Next

1. Walk it. The barrier should now report in well under a second.
2. Profile on a real low-end device — still unmeasured.
3. Placeholder staircase, then the spec amendment for portal-as-entry.

---

## Session 19 — 2026-09-18 — The replication barrier that was not one

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 322 passing

### Done

The owner sent the server log, and it named the bug in two lines that had been
invisible from screenshots for four playtests:

```
[PortalRig]  EngineRig: driving 0 ring(s) -- NONE FOUND, plane MISSING
[HubEffects] animating 0 part(s), 0 shard(s), 0 orbiter(s); engineRig found
```

**`engineRig` found, `OuterRing` not found inside it.** That is a
half-replicated model, and it means every animation this client ever ran was
running against a hub that had not arrived.

**The Session 13 barrier was never a barrier.** I had the server set
`Crossroads:SetAttribute("Ready", true)` last and the client wait for it. But
**an attribute replicates with the model it sits on, while that model's 447
descendants stream in afterwards.** The client saw `Ready` instantly, scanned
instantly, and found a Crossroads containing almost nothing.

Worse, it explains the whole sequence of wrong diagnoses: the shards happened to
win the race often enough to look like they worked, which made every subsequent
symptom look like a property of the rings rather than a property of timing.

**A count is a barrier an attribute cannot be.** The server now publishes
`PartCount` alongside `Ready`, and the client waits until it can actually *see*
that many BaseParts (capped at 20 seconds, then proceeds regardless rather than
hanging). It is checking the thing it needs, not a proxy for it.

**Also fixed: the shard rarity cycle could never start.** It was gated on
`#shards > 0` **at scan time** and spawned only then — so with zero shards
found, the rotation never began at all, even once the crystals arrived. It now
runs unconditionally and asks "are there shards yet" each pass.

### Decisions made

- **Wait for the thing, not for a signal about the thing.** `Ready` was a flag
  that meant "the server finished", and I read it as "the client has it". Those
  are different statements and the gap between them is exactly one replication
  window.

- **A lazily-gated loop beats a conditionally-spawned one.** Anything that asks
  "is there work?" once, at the worst possible moment, answers no forever.

### Benign log lines, noted so they are not chased later

- `[SaveSystem] DataStores unavailable` — expected in Studio until the place is
  published with Studio API access enabled. Profiles run in memory.
- `[DebugSystem] DEVELOPER COMMANDS ARE ON` — intentional, and already on the
  pre-launch checklist to turn off.
- `[Rojo-Warn] Disconnected` — the dev session dropping, not the game.

### Stopped at

322 passing. The barrier is unverified in-engine; the log will say
`animating N part(s)` with a real N if it worked.

### Next

1. Walk it and read that one line.
2. Profile on a real low-end device — still unmeasured across three sessions of
   added animation.
3. Placeholder staircase, then the spec amendment for portal-as-entry.

---

## Session 18 — 2026-09-18 — Clipping, layering, and a polish pass

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 322 passing (was 320)

### Done

Sixth playtest. Two reported faults, both measurable, plus an unprompted polish
pass the owner asked for.

**THE VEIL PULSED THROUGH ITS OWN FRAME, and the numbers say so exactly.**
Measured from the delivered mesh at `Prefab.Scale`:

| | Studs |
|---|---|
| `PortalPlane` | 15.22 |
| `InnerRing` | 15.92 |
| Clearance | **0.35 a side** |
| Veil at `PulseScale = 0.06` | **16.13** |

I added that size pulse last session without checking it against the ring it
sits inside. The breath is now carried entirely by transparency, which cannot
clip, and a test asserts the veil's pulsed width stays inside the ring.

**Ring and veil had merged.** Both emissive in the same hue, so they read as one
bright disc and the ring's teeth stopped existing. `InnerRing` is now `Metal`:
it takes the rarity colour but catches light instead of emitting it, so the
frame is machined and the aperture inside it glows. That is the way round it
should have been — the thing you walk through should be the light source.

**The base is two-tone at last, by being both colours in turn.** The "blue
cylindrical base" is `LevitationCore`, a **single mesh** — it cannot be painted
two tones, which is why two attempts at recolouring it failed. It now drifts
cyan → violet over six seconds while breathing on a different period, so the two
never line up and it never looks like a loop. New `ColorA`/`ColorB`/
`ColorSeconds` in the animator.

### The polish pass

Asked what would make a player stop and say the game is well made, the answer
was **ordered motion** — things that happen *in sequence* read as a mechanism
thinking, where the same things at random phases read as flicker.

New `WaveCount` on a style entry: `PrefabLoader` reads the trailing number in
each part's name and sets an ordered phase, so a set ripples instead of
twinkling.

- **Eight glyphs** light one after another around the plinth.
- **Sixteen inlays** ripple outward on a slower period, so the dais breathes
  under the plinth rather than with it.

### Owner notes taken mid-session

- **Rings slower and looser.** 0.32 / −0.45 → **0.22 / −0.31**, a 28- and
  20-second revolution, with the rate breathing ±32% over a longer wobble. The
  note was "fluid and flowing, not forced", and the fix for *forced* is less
  regularity rather than less speed alone.

- **Polished over rustic** — a judgement call, and reversible in one line.
  `Basalt`'s heavy grain read as corroded bronze against pale marble and cool
  energy, which is a third material language in a palette that only has two.
  `Slate` keeps the mass and the dark value without the rust.

### Decisions made

- **Geometry that moves needs its clearance checked.** A size pulse is not a
  free effect: it has a budget set by whatever surrounds it, and that budget is
  now asserted rather than assumed.

- **Layer by material, not by colour.** Dark matte frame → matte machined ring →
  emissive aperture gives three readable layers from one rarity hue. Colour
  alone had all three fighting.

- **Sequence beats randomness for sets.** Hash phasing is right for six shards
  adrift; ordered phasing is right for eight glyphs in a ring.

### Stopped at

322 passing. Unverified in-engine. The performance budget from Session 16 is
still unmeasured, and this round added ~24 animated parts (glyphs and inlays),
all on the throttled transparency path and distance-culled.

### Next

1. Walk it.
2. **Profile on a real low-end device.** Two sessions have now added animation
   on top of an unmeasured budget.
3. Placeholder staircase, then the spec amendment for portal-as-entry.
4. The Crossroads proper — the owner expects the Engine to read much better
   once it is not standing in a test harness.

---

## Session 17 — 2026-09-18 — Making the Engine stop reading as a machine

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 320 passing (was 317)

### Done

Fifth playtest. Speed confirmed good. Every remaining note was a variation of
the same thing — *it moves, but it moves like machinery* — so this round is
about breaking uniformity.

**THE VARIATION CODE WAS RIGHT; THE HASH WAS USELESS.** Two sessions of
"crystals still in unison" traced to one line. Both the bob phase and the
`Vary` spread keyed off a plain rolling hash of the part name, and
`Shard1`..`Shard6` differ only in the last character:

```
Shard1 -> 147   Shard4 -> 150
Shard2 -> 148   Shard5 -> 151
Shard3 -> 149   Shard6 -> 152     out of 1000
```

Half a percent apart, so every crystal got the same phase and effectively the
same speed. A trailing multiply by a large constant scrambles it — the same six
now land at .50 .92 .35 .78 .21 .64. `Vary` is also keyed on the attribute name
as well as the part, so a shard's speed and its drift are not varied by the
same amount.

**Adjacent names hashing to adjacent values is the kind of bug that produces no
error and no wrong number — just an effect that quietly does nothing.**

**Rings turn like a motor → wobble and jitter.** New `WobbleDegrees` /
`WobbleSeconds` (a small tilt across the spin axis, on two uneven periods so
the sway never lands on a beat) and `SpinJitter` (the rate breathes ±25%
instead of holding exact). Shards wobble too, varied per crystal.

**The colour snap → a tween.** `setRarity` took an optional duration and every
paint goes through it. `GameConfig.Portal.RarityTweenSeconds = 0.9`, applied
both when the spin-up starts and when the roll settles, so the colour travels
across the rig while the rings wind up rather than swapping on one frame.

**The veil → Neon.** `ForceField`'s shimmer was too subtle to read against a
dark hub, so the aperture looked like a hole rather than the thing you step
into. Neon actually glows; the transparency pulse (0.38–0.62) keeps the bloom
in check and lets the ring's teeth stay readable through it.

### The harness bug this uncovered

Asserting `veil.Material == Enum.Material.Neon` failed against a correct
value. The `Enum` shim built **a fresh table on every access**, so
`Enum.Material.Neon ~= Enum.Material.Neon` and no test asserting a material
could ever have passed.

Same class as the Vector3-as-table shim recorded in CLAUDE.md, and the same
lesson: an unfaithful shim is worse than no test. Fixed in `build_suite.py` by
caching each item, so identity behaves as the engine does.

### Decisions made

- **Test the property, not a proxy for it.** The veil test asserted
  `Transparency < 0.35`, which stopped meaning anything the moment the material
  changed — an emissive surface at 0.45 reads far brighter than a shimmer at
  0.2. It now asserts the two things that actually make it visible: that it is
  emissive, and that its pulse never fades far enough to vanish.

- **Uniformity is the bug, not the lack of features.** Every note this round
  was fixed by making something less regular rather than by adding motion.

### Stopped at

320 passing. Unverified in-engine.

### Next

1. Walk it. Six visibly different crystals, a swaying ring, a glowing aperture,
   and a colour that travels rather than snaps.
2. Profile on a real low-end device — the Session 16 budget is still unmeasured.
3. Placeholder staircase, then the spec amendment for portal-as-entry.

---

## Session 16 — 2026-09-18 — Tuning the Engine, and a performance budget

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 317 passing (was 311)

### Done

Fourth playtest. **Rings turn now.** Five fixes from the notes, plus the first
real performance work on the hub animator.

- **Rings were too fast.** 1.0 / -1.4 rad/s is a 6- and 4.5-second revolution,
  which on fine teeth reads as a fan. Down to 0.32 / -0.45 — 20 and 14 seconds.
  Shards 0.9 → 0.5.

- **The Engine reverted to UNKNOWN after a roll.** `HubEffects.settle()` reset
  it deliberately, which was right when the Engine was a decorative monument
  and wrong now that it is the portal to the world you just rolled. It made the
  Engine disagree with the Gate standing behind it, holding the destination
  colour — visible in the same screenshot, blue against purple. `settle` now
  takes the rolled rarity and keeps it.

- **The crystals moved in lockstep.** Two causes, both fixed. The rarity cycle
  tweened all six to the same colour at the same instant; it is now a **wave**
  — each shard takes the next rarity along, starting 0.18s after the one
  before, so the group always shows a spread. And all six shared one style
  entry, so they shared one speed: new `Vary` support in `PrefabLoader` scales
  a numeric attribute per part from a hash of its **name**, so the spread is
  different per crystal, identical every run, and still one line of content.

- **The veil was nearly invisible**, which is backwards — it is the surface
  players walk through and the point of the whole machine. Deep blue at 0.45
  transparent against a dark hub. Now brighter, 0.2 transparent, explicitly
  **non-colliding**, and the only part of the Engine that changes size: it
  breathes on a 2.8s loop, faster than the core, so it reads as the live thing.
  Its rarity tint deliberately skips `NeonTint` — it is `ForceField`, not Neon,
  so it does not bloom and should stay the brightest surface in the rig.

### The performance budget

The owner reported Studio "slightly choppy" and flagged low-end devices for
launch. The animator runs every frame on every client, so it is now built
around doing as little as possible. New `GameConfig.Effects`:

| | |
|---|---|
| `AnimationDistance` 700 | past this a part stops animating entirely — the hub is 1150 across and scenery reaches 4000, so most of what is tagged is off screen or a speck |
| `CullIntervalSeconds` 0.5 | the distance check is throttled; per part per frame it would cost more than the animation it protects |
| `SlowUpdateSeconds` 0.05 | `Size` and `Transparency` write at 20 Hz, not 60 |

**Only `CFrame` runs at full rate**, because motion is what the eye catches
stuttering. A `Size` change on a MeshPart re-scales the mesh and is far more
expensive than a CFrame write; at 20 Hz a slow breath is indistinguishable
from 60 and costs a third as much.

### Decisions made

- **Spin speed is a band, and both edges are bugs that shipped.** Too slow
  (0.15 rad/s) read as "not animated" for two playtests; too fast (1.4) read as
  "very very fast" on the third. The test now asserts a revolution between 8
  and 30 seconds rather than a minimum.

- **The Engine holds the destination.** Consistent with the owner's stated
  direction that this portal becomes the way into biomes.

- **Variation is content, not code.** `Vary` on a style entry, keyed off the
  part name, rather than six near-identical entries or a random jitter that
  differs every join.

### Stopped at

317 passing. Unverified in-engine. Performance work is by construction rather
than measurement — no profiling has been done, and the cull distance is a
guess that wants a real device behind it.

### Next

1. Walk it. Speeds, the held rarity, varied crystals, a visible veil.
2. **Profile on a real low-end device** before trusting the numbers above.
3. Placeholder staircase, then the spec amendment for portal-as-entry.

---

## Session 15 — 2026-09-18 — The rings were never in the list

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 311 passing (was 305)

### Done

Third playtest. Neon dimming confirmed good. **Shards rotate; rings still did
not** — and that pairing is what finally identified the bug, because both are
client-side CFrame writes on anchored server parts. Anchoring was never the
problem, and the owner's guess that it might be was the right question to ask.

**ROOT CAUSE: there were two animation paths, and the rings were only in the
broken one.**

`HubEffects` ran a Heartbeat loop that collected parts tagged
`IsFeaturedShard` — shards, and nothing else. The rings depended entirely on a
separate route: `findRigs()` → `PortalRig.animate(engineRig)` → find rings by
name. Two independent lookups, failing differently, which is why the symptom
kept pointing at replication, then at spin speed, then at anchoring.

I raised the spin speed last session on the theory it was too slow to see.
That was a real problem and worth fixing, but it was not *this* problem, and I
should have gone looking for why one set of parts moved and another did not
rather than reaching for the most available explanation.

**The fix collapses the two paths into one.** `HubEffects` now animates
anything carrying a motion attribute, wherever it sits and whoever put it
there:

| Attribute | Does |
|---|---|
| `SpinSpeed` + `SpinAxis` | turns about its own X, Y or Z |
| `BobStuds` + `BobSeconds` | drifts up and down |
| `PulseScale` + `PulseSeconds` | breathes larger and smaller |
| `PulseAlphaMin` / `PulseAlphaMax` | pulses transparency |

Each part gets a phase derived from its **name**, so six shards never bob in
lockstep, and it is the same every join rather than random.

Rotation accumulates as an angle and the CFrame is rebuilt from a captured base
each frame. Multiplying into the live CFrame instead would let the bob offset
compound and walk the part away from where the artist put it.

`PortalRig.animate` now skips `BasePart` rings and a plane carrying
`PulseAlphaMin`, so nothing is driven twice. It still drives the blockout rig's
segment Models, which the data path cannot.

**Also done, from the same playtest:**

- **Shards float.** `BobStuds = 1.6` over 5.5s, phase-offset per shard.
- **The levitation core breathes** (`PulseScale = 0.12`) and now reads in two
  tones: cyan core over **violet coils**, both from the hub palette rather than
  invented.
- **The portal veil breathes too**, slower than the rings so the two do not
  beat against each other.
- **Walkways stopped burying the dais.** `WalkwayRaise` 6 → 1.5 and
  `Bridges.Overlap` 10 → 3. The authored dais is only ~2 studs proud of the hub
  floor, so decks raised 6 ran straight over the top of it. `PlatformRaise`
  10 → 2 as well, so the blockout dais is the same step as the authored one.

### Decisions made

- **One animator, driven by data.** Motion is now a line in the content paint
  table, not a code change — consistent with the prime directive, and it means
  a part cannot be animated by one system and invisible to another.

- **Tests for the failure modes that shipped, not just for the fix.** Three new
  relationship assertions, each of which would have caught a real bug from this
  round:
  - both rings name `Z` as their spin axis (a ring is thin along Z, so Z is the
    axle; spinning about Y would tumble it end over end)
  - every spinner completes a revolution in **under 30 seconds** — a speed that
    cannot be seen is the same as no animation, and that is exactly how it
    shipped twice
  - walkway decks sit **below** the dais top, and the overlap leaves most of
    the dais visible

### Stopped at

311 passing. Unverified in-engine. The `[HubEffects] animating N part(s)` line
now reports the count directly, so if anything is still still, that number says
whether it was collected.

### Next

1. Walk it. Rings, bobbing shards, breathing core, visible dais.
2. Placeholder staircase.
3. Spec amendment for portal-as-entry.

---

## Session 14 — 2026-09-18 — Spin speed, neon glare, and a diagnostic

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 305 passing

### Done

Second playtest. **Sizing confirmed good** at `Scale = 0.464`. Rarity recolour
on the portal confirmed working. Animation still reported dead.

**The rarity recolour working is the diagnostic that matters.** It proves
`engineRig` is found and `PortalRig.playSpinUp` runs — so the Session 13
replication-race fix worked, and the rig is not missing. The fault is
downstream of that.

**Most likely cause, and fixed: the spin was too slow to see.**
`Portal.IdleSpinSpeed` was `0.15` rad/s — **one revolution every 42 seconds.**
On the blockout's 28 visible segments that reads as a slow hum. On an authored
ring, which is near rotationally symmetric, a slow rotation about its own
symmetry axis is **invisible by construction**. Raised to `0.6` (a revolution
every 10s). Shards went `0.35` → `0.9` for the same reason: 18 seconds a
revolution reads as still.

**Added a diagnostic rather than guessing again.** Two prints, because "nothing
is animated" has now cost two rounds and a screenshot cannot distinguish "no
rings found" from "rings turning too slowly to see":

```
[PortalRig] EngineRig: driving 2 ring(s) OuterRing(MeshPart, spin 1) InnerRing(MeshPart, spin -1.4), plane yes
[HubEffects] scan: 6 shard(s), 0 orbiter(s); engineRig found, gateRig found
```

If those numbers come back as expected, the speed was the whole story. If they
come back `0 ring(s)` or `MISSING`, the fault is lookup, not speed, and the
line says which.

**Neon glare.** The portal was bright enough to bloom a halo over its own mesh
detail. Roblox's `Neon` emits at the part's **full `Color`** and bloom
amplifies it — and `Transparency` does not help, because Neon ignores it. The
only lever is the colour itself.

Added `Portal.NeonTint = 0.55`, applied in `PortalRig.setRarity` to everything
Neon before it lands, and dimmed the statically-painted Neon parts in the paint
table by the same factor (mint `124,245,224` → `68,135,123`). Hue preserved,
geometry readable.

### Decisions made

- **An animation speed that is invisible is a bug, not a taste.** The old value
  was chosen against blockout geometry with 28 visible segments. Authored art
  changed what "slow" means, and nothing flagged it because both look identical
  in a still.

- **Neon is tinted at the source, in config, not per part.** `NeonTint` is one
  tunable that every Neon path goes through, so the Gate and the return portals
  get the same treatment without a second decision.

- **Not addressed: walkways cover the base of the portal.** Owner-noted and
  explicitly deprioritised — the current Crossroads is a test harness, not the
  real map, which is the next piece of work. Recorded so it is not rediscovered
  as a bug.

### Stopped at

305 passing. Both fixes are unverified in-engine; the diagnostic exists to make
the next round conclusive either way.

### Next

1. **Walk it and read the two `[PortalRig]` / `[HubEffects]` lines.** They
   settle whether the remaining fault is lookup or speed.
2. Placeholder staircase, once animation is confirmed.
3. Then the spec amendment for portal-as-entry.

---

## Session 13 — 2026-09-18 — First playtest of the authored Engine

**Branch:** `claude/zen-volta-cuhfyh` · **Tests:** 305 passing

### Done

The Engine was walked in Studio. It rendered, and the paint table worked —
the owner confirmed colour came through. Two real bugs and one re-tune.

**THE ANIMATION BUG WAS A REPLICATION RACE, and it was never about the
prefab.** Nothing in the hub animated: no rings, no shards, nothing on a roll.

`HubEffects.init` does `Workspace:WaitForChild("Crossroads")` and then scans
once. But a Model does **not** replicate atomically — the client sees the
Crossroads before its descendants arrive. It then finds no `EngineRig` and no
shards, animates nothing, and never retries. It looks exactly like broken
animation code.

This was latent all along; the blockout hub is small enough to usually win the
race. An authored Engine is ~80 MeshParts of mesh data, which loses it every
time. So the prefab did not cause the bug, it made it deterministic.

Fixed with an explicit done signal rather than a delay: the server sets
`Crossroads:SetAttribute("Ready", true)` as its last act, and the client waits
for that before scanning. Plus a `DescendantAdded` hook so anything tagged that
lands late still animates.

**Re-tuned the scale.** The owner's verdict was "way too big" — the ring stood
115 studs, 23x a player. The ask was ~4.5x player height:

| | Was | Now |
|---|---|---|
| `Prefab.Scale` | 2.3762 | **0.464** |
| Portal ring height | 115.2 | **22.5** (4.5x a 5-stud player) |
| Portal opening | 81.6 | 15.9 — still walkable |
| Dais width | 240 | 46.9 |
| Crown height | 300 | 58.6 |

**That cascaded, and the tests caught it.** `PlatformRadius` is the number
walkways are cut to meet, so leaving it at 120 would have left four walkways
stopping 97 studs short in mid-air. It is now **derived** from the authored
platform (101.0 x 0.464 / 2 = 23) rather than chosen beside it. `AnchorSize`
came down from 90 to 30 — at 90 the roll pad was wider than the entire
re-tuned Engine.

Then the suite failed on the BLOCKOUT rig: `Portal.FateEngineScale` still put
its ring at radius 54 against a 23-radius dais. Dropped 6.0 -> 1.25 so the
stand-in matches the authored rig at 11.25 either way. A place with no Rojo now
looks proportionally like the real thing.

### Decisions made

- **`PlatformRadius` is derived from the prefab, not set alongside it.** The
  dais *is* that radius. Two numbers describing one edge is how walkways end up
  in mid-air, and the test asserting they agree is what caught it within a
  minute of the change.

- **The blockout tracks the authored art's size.** A stand-in that is 5x the
  thing it stands in for is not a stand-in.

- **Recorded, not built: the Engine portal becomes the way into biomes.**
  Owner-stated direction — roll, react, a prompt to keep the biome, then a
  staircase generates from the portal's centre down to the base and animates as
  if building itself. Logged in `STATUS.md` §4 as **architecture**, because the
  "keep this biome?" step is **new game state** between rolling and entering
  (today the destination is implicitly the last roll), and it makes the
  Expedition Gate district redundant the way the Observatory became. That needs
  a spec amendment before any of it is written.

### Stopped at

305 passing. The re-tuned Engine has not been walked — the scale is arithmetic
against the owner's stated target, not an observation.

### Next

1. **Walk it again.** Judge the new size, and whether the rings now turn and a
   `/roll` recolours the portal. The animation fix is unverified in-engine.
2. **Placeholder staircase** from the portal centre to the base, so walkability
   can be tested before the real one is modelled. Held until the size is
   confirmed — building it against a scale that may move again would be wasted.
3. Then the spec amendment for portal-as-entry.

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
