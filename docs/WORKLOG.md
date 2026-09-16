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
