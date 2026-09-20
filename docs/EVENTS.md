# LUCKBOUND — Live Events & Rifts

**Status:** design. §1–§3 describe what is **built** (scope, precedence, the
ledger, the menu tint). Everything from §4 on is a **proposal** — a catalogue
to argue with, not a commitment. Nothing in §5–§7 is implemented.

**Owns:** what an event is, what events could exist, and the event-gated
dungeons ("Rifts") that some of them open.
**See also:** `PLAYER_UI.md` §3.5 (the menu's live tint), build spec §4.2
(scope and precedence on the wire), `MODULAR_MAPS.md` (how a map is built).

---

## 1. What an event is

> **An event is the game happening *to* the player rather than because of
> them.** Everyone sees the same thing at the same time, nobody opted in, and
> it ends whether or not anyone was paying attention.

That framing decides a lot of what follows. An event is not a quest, not a
daily, and not a button in a menu. It is weather — with the important
difference that some of this weather opens a door.

### The three scopes

| Scope | Reach | Example |
|---|---|---|
| `GLOBAL` | Every server in the game | A Catalyst Star is found |
| `SERVER` | This server only | A hot streak of rare rolls |
| `BIOME` | Everyone inside one world | Emberfall's ember surge |

Scope is a **field**, not a flavour of the event's kind, because reach and
subject are independent: the same aurora can be a one-server curiosity or
game-wide news. An event with no stated scope is a `SERVER` event — the
narrowest honest default, so a missing field cannot announce itself to the
whole game.

**One event owns the sky.** Overlaps resolve by scope, then priority, then the
event running longest, then Id. Everything else contributes additive effects
only. Build spec §4.2 has the exact rule and the reasoning.

---

## 2. How an event is triggered

Four mechanisms, and which one an event uses says more about it than its
effects do.

| Trigger | How it fires | Cost to build | Example |
|---|---|---|---|
| **Roll-triggered** | A roll result starts it | Built (Fatebreak does this) | Starfall on any Mythic |
| **Threshold** | The Nth of something, counted per server | Small | 25 rare rolls in one server |
| **Ledger-capped** | A global counter says how many may ever exist | **Built** (`LedgerCore`) | Catalyst Star, 10 ever |
| **Scheduled** | The wall clock says it is time | Small, and see below | Fate Tide, hourly |

### Scheduled events need no coordination at all

Worth stating because the obvious implementation is the wrong one. Roblox
servers are ephemeral and cannot be told "start at 8pm" by any central
authority — but they do not need to be. If a scheduled event is a **pure
function of UTC time**, every server computes the same answer independently,
with no messaging, no DataStore, and no drift:

```
EventCore.scheduledAt(now) -> { active event ids }
```

A server that starts mid-event computes that it is mid-event and joins in. A
player who rejoins sees the same thing. There is nothing to lose, because
there is nothing being sent. This is the cheapest event class to build and
should probably be the first one after the two that already exist.

### Ledger-capped is the expensive one, and it is already done

"Only ten will ever exist" is a promise about every server at once.
MessagingService cannot keep it — it is lossy, rate-limited, and reaches only
running servers. `LedgerCore` + `LedgerSystem` claim a number from a single
DataStore key with `UpdateAsync` **before** anything is announced, and refuse
when the ledger is unreachable. See §3.

---

## 3. What is built today

| | |
|---|---|
| `Scope`, `Priority`, precedence | ✅ `EventCore.dominant`, tested |
| Client-side self-expiry | ✅ A lost message cannot strand an altered sky |
| The menu tints to the dominant event | ✅ `ThemeCore`, contrast-floored |
| Global scarcity ledger | ✅ `LedgerCore` (pure) + `LedgerSystem` (claims, fails closed) |
| Events as content | 🔨 In progress — `Content/Events/` |
| The sky actually changing | 🔨 In progress — per-client lighting + a sky layer |
| Rifts (§5) | ❌ Not started. Needs combat, which is Phase 2 |

---

## 4. The event catalogue — a proposal

Rarity here means *how often a player should expect to see one*, which is a
design target, not an implementation. Durations are opening bids.

### 4.1 Global — the game-wide ones

| Event | Trigger | Rarity | Duration | What it does | Rift? |
|---|---|---|---|---|---|
| **Catalyst Star** | Ledger-capped, 10 ever | Ten times, ever | 7 min | Cold starlight sky, aurora, the hub rumbles. Every server is told who found it and how many remain | **Yes — all biomes** |
| **Starfall** | Any Mythic roll | ~3% of rolls, so hourly on a busy game | 5 min | The existing Fatebreak: Mythic-orange sky, reality "altered" | Yes — roller's biome |
| **The Unknown Hour** | Rolling `THE_UNKNOWN` (weight 5 ⇒ 0.05%) | Twice a week, game-wide | 10 min | The sky goes *out*. Stars, no sun, fog to nothing. The rarest sky in the game | **Yes — the Void Gate** |
| **Convergence** | Scheduled, weekly | Weekly, announced | 20 min | Everyone's roll pool loses its Common tier for the duration. **Pool access, never odds** — D-8 holds | No |
| **Fate Tide** | Scheduled, a few times daily | Common | 15 min | Fate rewards doubled. The safe, cheerful one — no sky drama, no odds change | No |

### 4.2 Server — the ones a room shares

| Event | Trigger | Rarity | Duration | What it does | Rift? |
|---|---|---|---|---|---|
| **Rolling Thunder** | 5 rare-or-better rolls inside 60s on one server | Busy servers, a few times an hour | 3 min | Every roll on the server is announced to it. A hot streak becomes a communal moment | No |
| **Echo of the Engine** | Threshold: 100 rolls on the server | A few times a session | 5 min | The Engine spins without stopping and the roll cooldown drops. **Pacing, not odds** | No |
| **Hall Resonance** | Scheduled or threshold | Occasional | 5 min, *extendable* | The obelisks light. Every rare+ roll on the server adds 30s, to a cap. A community goal with a visible bar | No |
| **The Gilded Hour** | Scheduled | Daily | 10 min | Shop stock refreshes and prices drop. Gives the Shop panel a reason to be checked | No |
| **Aurora Veil** | Threshold or scheduled | Common | 4 min | Purely cosmetic sky. Exists so that not every event is a summons — weather should sometimes just be weather | No |

### 4.3 Biome — the ones that open doors

These are the interesting ones, because a biome event can change the map that
is generated inside it.

| Event | Biome | Trigger | Rarity | What it does | Rift |
|---|---|---|---|---|---|
| **Verdant Overgrowth** | Verdant Valley | Threshold | Common | The valley floods with growth; light goes green-gold | **Tier I** — the teaching rift |
| **Ethereal Bloom** | Ethereal Scape | Roll-triggered on an Uncommon+ entry | Uncommon | The sky cracks over the sky temple; the cloud deck turns to light | **Tier II** |
| **Ember Surge** | Emberfall | Threshold | Uncommon | Ash falls upward. Fog reddens, brightness climbs | **Tier II** |
| **Citadel Ascension** | Sky Citadel | Scheduled | Rare | The citadel's rings align; gravity feels wrong | **Tier III** |
| **Astral Alignment** | Astral Reach | Scheduled, rare | Rare | The hardest sky and the hardest door in the game | **Tier IV** |

---

## 5. Rifts — event-gated dungeons

> **Owner-directed.** While a biome event is live, a portal opens in one of
> the generated zones. Through it is a far harder dungeon, and it yields
> rewards obtainable nowhere else.

This is the strongest idea in the whole event design, because it turns an
event from *a thing you watch* into *a thing you drop everything for*.

### 5.1 Where the portal appears

Two map routes already exist, and the rift needs an answer for each:

| Map kind | How the rift attaches |
|---|---|
| **Kit-assembled** (`ChunkCore`) | A new chunk `Role = "RIFT"`, placed like any other. The assembler already guarantees a non-overlapping, reachable layout, so the rift lands somewhere walkable for free |
| **Prebuilt scene** (`PrebuiltLoader`) | A named part — `RiftAnchor` — exactly the trick `EntryAnchor` and `ReturnAnchor` already use. Two named parts is the entire contract with the modeller |

**Whichever route, the portal is spawned by the same `PortalRig` the Fate
Engine and the return portal use**, tinted to the event rather than to a
rarity. Nothing new has to be authored to prototype it.

### 5.2 The rules that keep it honest

- **Open only while the event is live**, and the server checks that on entry.
  A client that asks to enter a closed rift is refused like any other
  fabricated request (rule 5).
- **A run in progress is not cut off.** When the event ends, anyone inside
  keeps a grace period to finish or leave. Yanking a player out of a boss
  fight because a timer elsewhere expired is the worst possible ending.
- **The run has its own timer**, capped by the event's remaining time plus
  that grace. Both numbers are shown.
- **Rewards are decided server-side on clear**, never on entry, never by the
  client, and never partially — a disconnect mid-run yields nothing, which
  must be *said* up front rather than discovered.
- **One clear per player per event**, ledger-style if the reward is capped
  globally, profile-flagged if it is not.

### 5.3 Difficulty

The owner's framing — *immensely difficult but possible* — is a design
constraint worth writing down, because the default drift is toward "tuned
until nobody complains", which means "tuned until it is not hard".

- **Fixed difficulty, not scaled to the player.** A rift that scales is a
  rift that is the same for everyone, which is the opposite of the intent.
- **The tier ladder is the scaling.** Tier I is a teaching rift in the
  starting biome; Tier IV is the thing people post clips of.
- **Failure must cost something** or difficulty is just time. The cheapest
  honest cost: the rift closes for *you* on a failed run, for that event.

### 5.4 The rewards — and the one design trap

Owner's words: *"temporarily obtainable"*, *"extremely nice looking and
powerful"*, *"ONLY permitted through that event"*.

There is a genuine ambiguity in "temporary" and it is worth resolving
deliberately, because the two readings produce very different games:

| Reading | What it means | Consequence |
|---|---|---|
| **The item is temporary** | It decays when the event ends | No permanent power creep. But the player has nothing to show for a hard clear a week later |
| **The acquisition window is temporary** | You keep it forever, but only that event could ever grant it | A trophy with a story. **But** anyone who missed the event is permanently behind |

**Recommendation: split the reward.** The item is permanent, its *power* is
not.

- **The look is forever.** The item, its appearance, its name and the line
  "obtained during Ethereal Bloom, 3 of 47 clears" stay in the profile
  permanently. This is the reward that makes people care, and it costs the
  game's balance nothing.
- **The power is charged.** The item carries an event-charge that is spent or
  expires with the event. It is genuinely, obviously stronger while charged.
- **It can be recharged by the next occurrence of the same event.** This is
  the part that defuses the trap: missing an event costs you *this* window,
  not the game. Nobody is permanently behind, and the item still means
  something.

This also lands cleanly on the architecture already agreed: **power belongs to
the item, never to the player** (`PLAYER_ABILITIES.md` §0). A charged relic is
an item with a temporary attribute, which is exactly a thing the item schema
will already need.

### 5.5 What a rift needs that does not exist yet

Honest list, in dependency order:

1. **Combat.** Build spec §7 excludes it. A rift without it is a walk.
2. **Items and an inventory.** Also Phase 2. `Loot_Awarded` and
   `Inventory_Changed` are already reserved in §4.
3. **An item attribute that expires** — for the charge. Small, once items
   exist, but it decides the profile schema, so it wants deciding *with* the
   item schema rather than after.
4. **A rift map per tier.** Either a chunk kit or an authored scene; both
   routes already work.
5. **A clear/fail record on the profile**, for one-clear-per-event and for the
   trophy line.

**None of it blocks the event system itself**, which is the argument for
building events now and rifts when combat lands: every event in §4 that is
marked "Rift? No" is fully buildable today.

---

## 6. Open questions for the owner

1. **Rift rewards: the split above, or one of the pure readings?** This is the
   biggest call in the document and everything else in §5 hangs off it.
2. **Should a Catalyst Star's rift be one-per-server or one-per-player?** Ten
   exist ever; if each opens a rift the whole game can run, that is ten
   game-wide raids in the product's lifetime — which may be exactly right, or
   may be too thin to build for.
3. **Does a failed rift run close the door for that player?** §5.3's
   recommendation, but it is harsh and worth saying out loud.
4. **Is `Convergence` (a pool with no Commons, game-wide) acceptable under
   D-8?** The reading here is yes — it changes which pool you draw from, never
   how the draw resolves — but it is close enough to the line that it should
   be an explicit decision rather than an inference.
5. **How loud should a common event be?** `Aurora Veil` exists to argue that
   some events should be nothing but sky. If every event summons players, none
   of them feel like an occasion.

---

## 7. What to build in what order

1. **Finish the event content schema and the sky** — in progress. Unblocks
   every "Rift? No" row in §4.
2. **Scheduled events** (`EventCore.scheduledAt`) — cheapest class, no
   coordination, immediately gives Fate Tide and The Gilded Hour.
3. **Threshold events** — a per-server counter; gives Rolling Thunder, Echo of
   the Engine, Hall Resonance.
4. **Biome events without rifts** — the skies, so the biome half is proven
   before the door is added.
5. **The rift portal, with no dungeon behind it** — a portal that opens in a
   generated map during an event and teleports you to an empty room. Proves
   placement, gating, the timer and the grace period without waiting for
   combat.
6. **Rifts proper** — when combat and items exist.
