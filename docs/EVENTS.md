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

### 4.0 Three tiers of loudness

**Owner-decided (Q5), with the shape left to my judgement.** The answer was
"most events should do something, but simplicity has value" — so events are
tiered, and the tier is a field on the definition rather than a matter of
taste:

| Tier | How often | What it may do | What it may NOT do |
|---|---|---|---|
| **AMBIENT** | Frequently | Sky, light, weather. Nothing mechanical | Open a rift, grant an item, change a number |
| **MODIFIER** | Regularly | The above, plus small mechanical changes — a modifier on mobs, items, drops or pacing | Open a rift, grant a unique |
| **WORLD** | Rarely | Everything: sky, modifiers, rifts, unique items | — |

**Why a field and not a convention.** Once it is declared, the validator can
enforce it: an `AMBIENT` event that tries to declare a rift fails the boot
rather than shipping. Without that, the tiers are an intention that decays.

**The reasoning behind the split.** If every event summons players, none of
them is an occasion — that is the case for keeping AMBIENT. But an event that
*only* changes the colour of the sky teaches players to ignore the sky, which
is the case against having only that. MODIFIER is where most events should
live: something genuinely changes, the change is legible, and nobody has to
drop what they are doing. WORLD events are the ones worth interrupting a
session for, and they should be rare enough that interrupting is correct.

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
- **Open to everyone for the duration** (Q2/Q3). Whoever triggered the event
  does not own it — they own the *item* that caused it. See §5.4.

### 5.3 Difficulty

The owner's framing — *immensely difficult but possible* — is a design
constraint worth writing down, because the default drift is toward "tuned
until nobody complains", which means "tuned until it is not hard".

- **Fixed difficulty, not scaled to the player.** A rift that scales is a
  rift that is the same for everyone, which is the opposite of the intent.
- **The tier ladder is the scaling.** Tier I is a teaching rift in the
  starting biome; Tier IV is the thing people post clips of.
- **Failure costs the attempt, not the event** (owner-decided, Q3). The rift
  stays open to everyone for as long as the event runs; a failed run may be
  retried. Difficulty is therefore a wall to be learned rather than a single
  shot to be lost, which matters more when the door only opens occasionally.
  It also means **no per-player attempt counter on the profile** — the rift's
  state is the event's state and nothing else.

### 5.4 The rewards — DECIDED

**Owner-decided (Q1): the acquisition window is temporary, the item is
permanent.** You keep a relic forever; only that event could ever have granted
it. The alternative — an item that decays, or a permanent look with a
rechargeable power — was considered and rejected.

| | |
|---|---|
| The item | **Permanent.** Kept, displayed, named, with the event and date it came from |
| The window | **Temporary.** Only obtainable while that event ran |
| Power | **Permanent too.** There is no charge, no decay, no expiry attribute |

**What this buys, in build terms:** the item schema needs no expiry mechanic
and the profile needs no per-event counter. Two systems that the split model
would have required do not have to exist. Q1 and Q3 between them removed more
work than they added.

**The FOMO problem, and the owner's answer to it.** A permanent
event-exclusive reward normally means anyone who missed the event is
permanently behind. The answer is §5.6: **events recur.** Seasonally or
periodically, announced ahead of time, so missing one occurrence is missing a
window and not the item class. That is what makes a permanent reward fair, and
it is a commitment rather than a nice-to-have — the reward decision is only
sound if the recurrence decision is kept.

**The power-creep guard that replaces the charge.** With permanent power, the
ceiling has to be held somewhere else: a relic should be **sideways, not
upward** — a distinct way to play rather than a strictly bigger number. A
Tier IV relic that is simply +40% damage devalues every future reward; one
that changes *how* a weapon behaves does not. This is a content rule rather
than a code rule, so it is written here where the content is authored.

### 5.4b Getting to the biome in the first place — a conflict worth naming

**Owner-spotted, and it is a real one.** The planned progression lever is that
**Fate unlocks which pools you draw from** — at a high enough tier, Commons
stop appearing in your rolls (`PLAYER_ABILITIES.md` §3, FORTUNE). That is the
one odds-adjacent mechanic D-8 permits, because it changes the pool rather
than the draw.

Now put a rift in Verdant Valley. A high-tier player **cannot roll Verdant
Valley any more**, so the event they are being invited to is one they have no
way to reach. The better a player does, the fewer events they can attend —
which is exactly backwards.

**The rule that resolves it:**

> **Event access must never depend on the roll pool.**

A biome with a live event is **directly enterable for the duration**, by
anyone, regardless of what their pool contains. The roll decides where you go
when you are rolling; an event decides where you may go while it runs. They
are different doors and they should not share a lock.

Two supporting measures, both cheap and both worth doing anyway:

- **Pool filters should be opt-in and reversible.** "I no longer roll Commons"
  belongs in the Fate Tree as a toggle the player controls, not as a permanent
  consequence of levelling. A player who wants to revisit the valley should be
  able to.
- **The event's entry point is the hub, not the roll.** While a biome event
  runs, the Crossroads offers it as a destination — which the travel panel
  already has the shape for.

This is tweakable later, as the owner notes, and the Fate Tree is where the
tweaking will happen. What must not drift is the principle: **progression may
change what you roll; it may never lock you out of an event.**

### 5.5 Who gets what — the Star and the event are separate things

**Owner-decided (Q2).** This is the cleanest idea in the whole design and it
is worth stating precisely, because it resolves a tension the earlier draft
left open:

> **The finder gets the item. Everyone gets the event.**

A Catalyst Star is one of ten that will ever exist, and it belongs to whoever
found it — that is what the ledger enforces. The *event* it triggers is
`GLOBAL` and open to every player online for its duration: the sky, the rift,
and whatever the rift yields. Ten Stars therefore produce ten game-wide
occasions rather than ten private ones.

Two consequences worth holding on to:

- **Scarcity and participation stop fighting each other.** The item can be
  absurdly rare precisely because the *experience* is not. Nobody is excluded
  from the best moments in the game by a 1-in-a-trillion draw.
- **The trigger is a gift, not a prize gate.** The player who found the Star
  is the reason everyone else is having a good night, which is a far better
  social position than being the only one allowed through a door.

### 5.6 Recurrence — seasonal and periodic events

**Owner-directed.** Events recur: seasonally, or periodically on a schedule,
and **announced ahead of time** so people can be there.

This is load-bearing, not decoration. §5.4's permanent reward is only fair
because a comparable window comes round again; the moment recurrence is
dropped, every missed event becomes a permanent gap.

| | |
|---|---|
| Mechanism | §2's **scheduled** trigger: a pure function of UTC time, so every server agrees with no messaging and no DataStore |
| Cost | Small. The cheapest event class in the catalogue |
| Announcing ahead | A scheduled event can be computed *before* it starts, so "next Convergence in 2h 14m" is just the same function asked about the future |

**A countdown is worth building with it.** If events are scheduled and
knowable, the hub can say when the next one is — which turns an event from
something you miss into something you plan around. A line in the menu, or on
the Hall of Legends, costs almost nothing once `scheduledAt` exists.

### 5.7 Announcing outside the game (Discord)

**Owner-directed:** rare events should be posted publicly so people who were
not online can come. Worth doing, with one technical caveat that decides the
shape of it.

**Roblox servers cannot post to a Discord webhook directly.** Discord blocks
requests originating from Roblox's address space, so `HttpService` calls to
`discord.com` fail regardless of how the request is formed. The standard and
supported answer is a **relay you own** — a tiny Cloudflare Worker or
equivalent — that accepts a request from the game, verifies a shared secret,
and forwards it to the webhook.

Rules for it, since it is the game's only outbound call:

- **Fire and forget, off the hot path.** The announcement is a side effect of
  an event that has already started. A slow or dead relay must never delay the
  event or a player's roll.
- **One server posts, not forty.** A `GLOBAL` event fires on every server at
  once; without a guard, every one of them posts. The ledger's claim already
  names exactly one origin server for a unique item — reuse that, or claim a
  short-lived "who announces" key the same way.
- **The secret lives in the relay, never in the place file.** The game sends
  an event id and a name; the relay decides the message format and holds the
  webhook URL.
- **`HttpService` must be enabled**, which is a place-level setting and a
  deliberate one.

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

## 6. Decisions — answered 2026-09-20

All five were put to the owner and answered. Recorded here rather than in a
chat log, because this file is the memory.

| # | Question | Decision | Consequence |
|---|---|---|---|
| **Q1** | Rift reward permanence | **The item is permanent; the window is temporary.** No decay, no charge | The item schema needs no expiry attribute. Fairness now depends on §5.6 recurrence — that is a commitment, not a preference |
| **Q2** | Who gets a Catalyst Star's rift | **Everyone, for the duration. The finder gets the item** | Scarcity and participation stop competing. Ten Stars produce ten game-wide occasions |
| **Q3** | Does a failed run close the door | **No.** The rift stays open to all until the event ends | No per-player attempt counter. Rift state *is* event state |
| **Q4** | Is Convergence D-8-safe | **Yes — pool access, not odds** | And it surfaced a real conflict: pool progression can lock players out of biome events. Resolved in §5.4b: event access never depends on the roll pool |
| **Q5** | How loud should a common event be | **Most events do something; simplicity still has value** | Three tiers — AMBIENT / MODIFIER / WORLD (§4.0), enforced by the validator rather than by convention |

**Q1 and Q3 between them removed more work than they added** — the expiry
mechanic and the attempt counter both stopped being necessary.

**The one debt these decisions create** is §5.6: permanent event-exclusive
rewards are only fair while events recur. If recurrence is ever dropped, Q1
has to be reopened with it.

### Still open

1. **What a relic actually does.** §5.4's guard says sideways, not upward — a
   distinct way to play rather than a bigger number — but no relic has been
   designed. Blocked on items existing at all.
2. **Which events recur on what cadence.** §5.6 says they do; the calendar is
   unwritten.
3. **Rift tier ↔ biome mapping.** §4.3 proposes one. It should be revisited
   once combat exists and "difficult" can be measured rather than asserted.

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
