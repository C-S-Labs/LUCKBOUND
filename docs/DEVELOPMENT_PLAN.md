# LUCKBOUND — Development Plan

**Written:** 2026-09-21 · **Status:** recommendation, for the owner to accept,
amend or reject.

This exists because development has been reactive — walk the game, find three
things, fix three things — which was right while the shape was still being
found, and is wrong now. The shape is found. This is the map from here to a
real playtest, and then to launch.

**Read §1 and §3 if you read nothing else.** §1 is the decision everything
else hangs off; §3 is the critical path.

---

## 1. The decision that shapes everything

> **The first playtest should not wait for combat.**

Combat is the largest unbuilt system in the project — enemies, damage, hit
detection, animation, balance, death, and an item system underneath it to give
damage a home. It is months of the remaining work, and **none of it is needed
to answer the question a first playtest exists to answer.**

That question is not "is the combat good". It is:

> **Does the roll loop hold someone for an hour, and do they come back
> tomorrow?**

The owner has already answered the first half alone — *"these rolls alone were
fun"*, with no combat, no loot and grey blockout. What is unknown is whether
that survives contact with people who did not build it, and whether anything
brings them back.

**So the first playtest build closes the loop without combat.** An expedition
becomes: arrive in a world, find the things worth finding, get out before the
timer. That is a complete game loop — risk, reward, a reason to look around —
and every part of it is content on systems that already exist.

**What this buys:** a playtest in weeks rather than months, on the mechanic
that is actually differentiating. **What it costs:** testers will ask where the
combat is. That is an acceptable answer to give once; it is not acceptable to
spend three months building combat for a premise nobody has stress-tested.

---

## 2. Where we actually are

Honest inventory. Detail in `STATUS.md`.

| | |
|---|---|
| ✅ **Solid** | The roll and its pacing · Fate and levels · saves and migrations · the hub, rescaled to the player · the whole player UI · travel · codes · settings · live events with scope and precedence · the scarcity ledger · movement (sprint, double jump) |
| 🟡 **Built, never walked** | Almost all of the above. 574 headless tests pass; the Studio walks keep finding things tests structurally cannot see |
| 🔴 **Missing for a playtest** | Something to DO in a world · maps for 3 of 5 rollable worlds · sound · a tutorial · proven persistence · measured performance · a way to hear from testers |
| ⬜ **Missing for launch** | Combat · items and inventory · the Fate Tree · Rebirth · a real shop economy · parties · rifts |

**The single most important number:** **25% of honest rolls land on a world
with no map.** Emberfall (15%), Sky Citadel (7%), Astral Reach (3%). A tester
who rolls Emberfall — a *Rare* — and is told "that world has no map yet" has
been punished for a good roll. Nothing else on this list damages a playtest as
directly.

---

## 3. The critical path to a playtest

Five phases. **Each has an exit gate, and the gate is a thing you can check,
not a feeling.** Sizes are rough: S = a session, M = a few, L = a week or more.

### Phase 0 — Clear the deck · **S**

Everything already known to be broken or unverified, finished before new work
starts. No new features.

| Item | Size |
|---|---|
| Walk everything built but unwalked — tests H2, I–N, C2b | S |
| Staircase junction in Studio + re-export with the collision re-bake | S |
| Travel landings verified on every district (watch for `no floor under landing`) | S |
| Publish the place; verify saves, the ledger, and the two-instance race (test N) | S |

**Gate:** a full session in the published place — join, roll, travel, enter,
return, rejoin — with no errors in the output and no visible faults.

### Phase 1 — Every roll leads somewhere · **M**

The 25% problem. Two routes, and I recommend the second:

1. **Build a chunk kit per world.** Correct, and three kits is real work.
2. **One shared kit, dressed per world.** ✅ The kit supplies the *shapes*; each
   world already supplies its own lighting, palette and flavour. Emberfall's
   ash-lit version of a layout reads as Emberfall, not as a reskin, because the
   player never sees the two side by side.

Route 2 is **content only** — `Content/Chunks/` plus each world's existing
`Environment` — and makes all five worlds enterable in one pass. Bespoke kits
then replace it one world at a time, invisibly, whenever they are ready.

**Gate:** 100 rolls, every one enterable. No "that world has no map yet" path
reachable from the roll pool.

#### Interim, while the first kit is being modelled — owner-directed 2026-09-22

Verdant Valley's chunk art is in authoring. Until it is in and a second world
has a map, **gate the roll pool to Verdant Valley** rather than let a tester
roll into a refusal. Both knobs are data and neither touches a System:

- `GameConfig.Fate.PrototypeWeights` — `VERDANT_VALLEY = 10000`, the rest 0.
  This is the table that governs while `CurrentPhase == 1`; each world's own
  `RollWeight` is only consulted outside Phase 1.
- `GameConfig.Fate.OnboardingSequence` — rolls 1–8 are forced regardless of
  weight, and four of them are not Verdant Valley. Gating the weights without
  also flattening this sequence still drops a fresh profile into Emberfall on
  roll 3.

This is a testing posture, not a design change: it narrows what a tester sees
to the one world that can actually be walked, and it reverses by putting both
tables back. It does **not** close the 25% item — Route 2 above still does
that — and it must not be allowed to become the reason the other kits never
get built. The geometry brief for the kit itself is
[`CHUNK_AUTHORING.md`](CHUNK_AUTHORING.md).

### Phase 2 — Something to do in a world · **M/L**

The loop closes here, and it is the phase that decides whether the playtest is
worth running.

| Item | Why | Size |
|---|---|---|
| **Discoveries** — findable things placed in a generated map, server-validated on pickup | The non-combat objective. `Discovery_Found` and the Discovery Book are already reserved in build spec §4 | M |
| **A reason to hurry** — the timer already exists; make leaving early *cost* something and staying late *risk* something | Without tension, exploration is tourism | S |
| **The Discovery Archive earns its district** — show what you have found | The room exists and displays nothing | S |
| **Return with intent** — the return portal reports what you got | Closes the loop out loud | S |

**Gate:** a stranger can be dropped in with no explanation and, within one
expedition, work out what they are supposed to do.

### Phase 3 — Make it feel like a game · **M**

The difference between "a prototype" and "a thing worth an hour". Cheap,
high-leverage, and almost none of it is systems work.

| Item | Why |
|---|---|
| **Sound** | The single biggest perceived-quality gap. The roll, the reveal, the portal, the rail, PLAY, a discovery. The `SoundGroup`s and volume sliders already exist and route to nothing |
| **First-session tutorial** | The spawn already stands 105 studs clear of every prompt specifically to leave room for this |
| **Placeholder text pass** | Flavour lines, result cards, panel copy |
| **Mobile performance** | Never measured on a real device. `GameConfig.Effects` is reasoned, not measured |
| **Feedback capture** | A `/feedback` command or a panel writing somewhere you can read. Without it, a playtest produces anecdotes |

**Gate:** you can hand the game to someone with no instructions and they are not
confused, not bored in the first two minutes, and not on a phone that stutters.

### Phase 4 — The playtest itself · **S** (process, not code)

**Do not build during the test.** A moving build makes every piece of feedback
unattributable.

| | |
|---|---|
| **Cohort** | 10–20 people, sourced by the owner, ideally strangers rather than friends |
| **Length** | One week. Long enough for "did they come back tomorrow" to mean something |
| **Measure** | Sessions per player · session length · rolls per session · expeditions started vs completed · where they stop playing · rebirth-shaped questions they ask unprompted |
| **Ask** | "What did you think you were supposed to do?" · "What did you want that wasn't there?" · "Would you tell a friend, and what would you say?" |
| **Do not ask** | "Did you like it?" |

**Gate:** you can state, with evidence, whether the loop holds people.

### Phase 5 — Act on what it says · **?**

Deliberately unplanned. If the loop holds, build depth (§4 below). If it does
not, the cheapest fix is to the loop, and having *not* built combat first is
what makes that affordable.

---

## 4. After the playtest — the long game

In dependency order. Not scheduled here on purpose: the playtest reorders it.

1. **Items and inventory** — the foundation. Damage, effects and animations
   belong to the item that grants them (`PLAYER_ABILITIES.md` §0), so the item
   schema has to exist before combat can.
2. **Combat** — enemies, damage, death, the Training Grounds dummies that are
   already tagged `Phase = 2`.
3. **The Fate Tree** — designed in `PLAYER_ABILITIES.md` §3. Gate it on
   understanding what players actually want more of.
4. **Rebirth and prestige** — the retention layer. Worth nothing until there is
   enough game to reset.
5. **A real shop economy** — needs items first.
6. **Rifts** — `EVENTS.md` §5. Needs combat and items. **The portal and the
   gating can be prototyped with an empty room before either exists**, which is
   worth doing early because it de-risks the whole design cheaply.
7. **Expeditions in their own place** — `TeleportService`, for performance and
   party isolation. `ExpeditionCore` is already pure and unaffected; only
   `ExpeditionSystem` and `ChunkLoader` move.
8. **Parties** — designed, unbuilt.
9. **The Crossroads revamp** — agreed for after testing. The drop-in contract is
   in `ART_DIRECTION.md`.
10. **Live ops** — seasonal event recurrence (§5.6 of `EVENTS.md`), the Discord
    relay, the Catalyst Stars actually going out into the world.

---

## 5. What we are deliberately NOT doing yet

Writing this down is the point of the document. Each of these is a thing that
would feel productive and would delay the playtest.

| Not yet | Why |
|---|---|
| Combat | §1. The playtest does not need it, and it is the biggest thing in the project |
| The Crossroads revamp | Agreed. The current hub tests the systems fine, and every art swap costs a re-walk |
| Rifts | Need combat and items |
| ~~Parties~~ | **Built 2026-09-22 at the owner's direction** — build spec §7.2 |
| Rebirth / prestige | Nothing to reset yet |
| ~~Expeditions in their own place~~ | **Built 2026-09-22 at the owner's direction** — a reserved server of the same place, build spec §7.2 |
| More events | Three are enough to prove the system. More is content, and content is cheap *later* |

---

## 6. How to work, so we stop jumping around

The rules that would have prevented most of the back-and-forth so far.

1. **One phase at a time, and finish it.** A phase is done when its gate is
   met, not when the interesting part is done.
2. **Walk it before building on it.** Every Studio walk so far has found things
   574 tests could not — a camera the engine also owns, an Enum name, a guessed
   constant. Unwalked work is unfinished work, however green the suite is.
3. **Batch the art.** Art changes force re-walks. Collect them and land them
   together rather than one at a time.
4. **Never build during a playtest.** A moving build makes feedback useless.
5. **A number in a config beats a number in a head.** If we tune something
   twice, it becomes a config value with a comment saying what it is for.
6. **Tests assert relationships, not literals.** The rescale broke twelve tests
   and every one named the number left behind — because they were written that
   way. The ones that asserted literals just had to be rewritten.

---

## 7. The risks worth naming

| Risk | Why it matters | What reduces it |
|---|---|---|
| **The loop does not hold strangers** | The premise is unvalidated outside the people who built it | §1 — find out early and cheaply |
| **Mobile performance** | A large share of Roblox's audience, and never measured | Phase 3, before testers |
| **Persistence in the wild** | Saves have never run against real DataStores under load | Phase 0, on a published place |
| **The 25% dead rolls** | Punishes good luck, which is the one thing the game is about | Phase 1 |
| **Scope creep through good ideas** | The event system, the ledger and the rift design were all excellent ideas that arrived before the loop was closed | §5, and this document |

---

## 8. If you only do four things

1. **Phase 0.** Walk what exists, publish, prove saves.
2. **One shared chunk kit** so every roll leads somewhere.
3. **Discoveries**, so an expedition has a point.
4. **Sound and a tutorial**, so it feels like a game rather than a build.

That is the playtest build. Everything else can wait for what the testers say.
