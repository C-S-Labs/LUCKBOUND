# LUCKBOUND — Prototype Build Specification
## Phase 1: Foundation · v0.1 · AI-Executable

**Status:** Canonical. **Phase 1 complete and verified in Studio; expedition entry opened by amendment §7.1.** Derived from `LUCKBOUND Master Game Design & Development Specification v0.1`; see `STATUS.md` for current state and `BLUEPRINT_RECONCILIATION.md` for how the Biome Blueprint was merged.
**Supersedes:** nothing. **Superseded by:** nothing.
**Rule of precedence:** where this document and the Master Design PDF disagree on an *implementation* detail, this document wins. Where they disagree on *intent*, the PDF wins and this document is wrong and must be amended.

---

## 0. What Phase 1 Is

> You can walk around a recognizable LUCKBOUND hub and press ROLL.

Nothing more. Phase 1 ships when a player can spawn in The Crossroads, walk to the Fate Engine, press ROLL, watch a reveal animation, and see a destination with its rarity. **No combat. No loot.** Those are Phase 2.

> Expedition entry *was* in that list and was opened by owner-directed amendment on 2026-09-16. **Combat and loot were not.** See §7.1 for exactly what moved and what did not.

The reason Phase 1 stops there: §25 of the Master Spec ("Design North Star") says the roll → anticipation → reveal moment is the thing the whole game rests on. If the roll does not feel good with nothing else attached to it, adding combat will not fix it. Phase 1 is a test of that, not scaffolding to rush through.

### Phase 1 Definition of Done

Ten of twelve are **met and verified in Studio** as of 2026-09-15. The two
persistence criteria require a published place — DataStores do not run on a
local file — and are the only Phase 1 items still unverified.

| # | Criterion | Verified by | |
|---|---|---|---|
| P1-1 | Place opens in Studio with zero errors in Output | Studio playtest | ✅ |
| P1-2 | Player spawns in Crossroads facing the Fate Engine | Studio playtest | ✅ |
| P1-3 | All hub districts are identifiable blockout geometry | Visual | ✅ |
| P1-4 | ROLL prompt appears near the Fate Engine (12 studs, `UI.PromptActivationDistance`) | Studio playtest | ✅ |
| P1-5 | Roll is server-authoritative; client cannot force a result | Exploit test (§7.4) | ✅ |
| P1-6 | Reveal animation runs ≥2.5s before result is shown | Timing | ✅ |
| P1-7 | Result shows world name, rarity name, rarity colour | Visual | ✅ |
| P1-8 | Fate points persist across rejoin | Rejoin test | ⏳ needs a published place |
| P1-9 | Profile save survives a Studio "Stop" mid-session | DataStore test | ⏳ needs a published place |
| P1-10 | Touch controls usable at 1280×720 and phone aspect | Device emulator | ✅ |
| P1-11 | `Fate_RequestRoll` spam (100/s) does not crash or over-roll | Exploit test | ✅ |
| P1-12 | No module named `*_Final`, `*_NEW`, `*_FIXED`, `*_v2` | `grep` in CI | ✅ |

---

## 1. Canonical Architecture

**The rule from §18: Systems are reusable. Content is data.**

Restated operationally, and this is the rule that prevents the `CombatSystem_Final2` outcome:

1. A **System** is a Luau module that contains *behaviour* and *no content*. `WorldSystem` knows how to start an expedition. It does not know that Emberfall is volcanic.
2. **Content** is a plain Luau table with no functions in it (except declared hook fields). Adding Emberfall must require editing exactly one file under `Content/Worlds/` and nothing else.
3. If implementing a content item requires changing a System, **the System's schema is wrong.** Stop and amend this spec instead of special-casing.

### 1.1 Repository → Roblox Explorer mapping

Rojo syncs the repo into the place. The left column is what you edit; the right is what exists at runtime.

```
src/shared/          →  ReplicatedStorage/Luckbound
  Core/                   Core/
    Types.luau              Types          (type definitions only, no runtime values)
    Constants.luau          Constants      (frozen; enums, rarity table, colours)
    GameConfig.luau         GameConfig     (frozen; every tunable number in the game)
    Net.luau                Net            (the ONLY place remotes are created/looked up)
    Result.luau             Result         (ok/err return convention)
  Content/                Content/
    Worlds/                   Worlds/
    Enemies/                  Enemies/
    Bosses/                   Bosses/
    Items/                    Items/
    Discoveries/              Discoveries/
    Events/                   Events/
  Util/                   Util/
    WeightedRandom.luau       WeightedRandom
    Schema.luau               Schema        (validates Content against Types at boot)
    ChunkCore.luau            ChunkCore     (pure: decides what goes where)
    ChunkLoader.luau          ChunkLoader   (Roblox: turns a Layout into Instances)
    PortalRig.luau            PortalRig

src/server/          →  ServerScriptService/LuckboundServer
  init.server.luau        (bootstrap: the ONLY Script; everything else is a ModuleScript)
  Systems/
    SaveSystem.luau
    ProgressionSystem.luau
    FateSystem.luau
    EventSystem.luau
    ExpeditionSystem.luau   (§7.1 -- entry, generation, return. No combat)
    DebugSystem.luau        (developer commands; delete before launch)
    HubBuilder.luau
    -- Phase 2: CombatSystem, LootSystem, InventorySystem, DiscoverySystem

src/client/          →  StarterPlayer/StarterPlayerScripts/LuckboundClient
  init.client.luau        (bootstrap: the ONLY LocalScript)
  Controllers/
    ProximityController.luau
    StateController.luau    (single client-side mirror of server state)
    HubEffects.luau
    ExpeditionController.luau  (§7.1 -- lighting apply/revert, local countdown)
    DebugCommands.luau      (/fly /speed /tp; delete before launch)
  UI/
    FateRoll.luau
    GlobalAnnouncements.luau
    ExpeditionHud.luau      (§7.1 -- destination banner and timer)
    -- Phase 2: Inventory, DiscoveryBook
```

**Explorer objects NOT managed by Rojo** (built in Studio or by `HubBuilder`):

```
Workspace/
  Crossroads/            -- hub blockout
    FateEngine/            -- must contain a Part named "RollAnchor"
    HallOfLegends/
    DiscoveryArchive/
    ExpeditionGate/        -- must contain a Part named "GateAnchor"
    TrainingGrounds/
    SpawnLocation
  ExpeditionStage/       -- generated maps, one Model per live expedition (§7.1)
ServerStorage/
  WorldTemplates/        -- empty in Phase 1
```

### 1.2 Bootstrap order — fixed, not negotiable

`init.server.luau` must initialise in exactly this order. Systems declare dependencies but never require each other at module scope (circular requires are a hard error).

```
1.  Schema.validateAll()      -- fail fast on malformed content, before any player joins
2.  Net.buildRemotes()        -- creates ReplicatedStorage/Luckbound/Net/*
3.  SaveSystem.init()
4.  ProgressionSystem.init(SaveSystem)
5.  EventSystem.init()
6.  FateSystem.init(SaveSystem, ProgressionSystem, EventSystem)
7.  ExpeditionSystem.init(SaveSystem, ProgressionSystem)
8.  DebugSystem.init(FateSystem, ExpeditionSystem)   -- developer commands
9.  HubBuilder.build()        -- lighting always; geometry only if absent
10. ExpeditionSystem.bindGatePrompt()  -- attaches to geometry step 9 creates
11. PlayerService binding     -- PlayerAdded/PlayerRemoving last, so no player can
                                 arrive before systems are ready
```

`DebugSystem` is deliberately **last of the systems**: nothing above it may
depend on it, so deleting the file before launch breaks nothing.

**Step 9 does two separable things, and that separation is load-bearing.**
`HubBuilder.build()` skips *generating geometry* when `Workspace.Crossroads`
already exists — authored art wins, as intended. But it always applies lighting
and always runs `ensureContract`, which guarantees the parts other systems look
up by name exist regardless of who built the hub:

| Part | Needed by |
|---|---|
| `Crossroads/FateEngine/RollAnchor` + `RollPrompt` | `FateSystem` — roll distance |
| `Crossroads/Zones/EXPEDITION_GATE/GateAnchor` + `EnterPrompt` | `ExpeditionSystem` — entry distance |
| `Crossroads/SpawnLocation` | players arriving |

Without that split, an artist modelling a hub and naming it `Crossroads` would
silently switch off rolling and expedition entry. `ensureContract` adds
anything missing and **warns loudly** naming what it had to add. Everything it
adds is invisible and non-colliding, so it changes behaviour and never looks.

`ExpeditionSystem` occupies the slot this spec originally reserved for
`WorldSystem`. It takes **no reference to `FateSystem`**: a player's pending
destination is simply their most recent `RollHistory` entry, read from the
profile. The two systems therefore share *data* rather than *pointers*, the
boot order stays a straight line with no back-reference, and a destination
survives a rejoin for free because `RollHistory` is already persisted.

If `Schema.validateAll()` fails, the server **must** `error()` and refuse to start. A prototype that boots with silently broken content is worse than one that does not boot.

---

## 2. Type & Data Schemas

These are the contracts. Every content file is validated against them at boot.

### 2.1 Rarity (Constants)

Rarity is an ordered enum. Never compare rarity by string.

| Key | Order | Display | Colour | Reveal duration |
|---|---|---|---|---|
| `COMMON` | 1 | Common | `#B8C4CE` | 2.5 s |
| `UNCOMMON` | 2 | Uncommon | `#5FD97A` | 2.8 s |
| `RARE` | 3 | Rare | `#4EA8F0` | 3.2 s |
| `EPIC` | 4 | Epic | `#A96FE8` | 3.8 s |
| `LEGENDARY` | 5 | Legendary | `#F2B23C` | 4.5 s |
| `MYTHIC` | 6 | Mythic | `#F0555B` | 5.5 s |
| `UNKNOWN` | 7 | ??? | `#FFFFFF` | 7.0 s |

Longer reveal for rarer results is the anticipation mechanic. It is a **tunable in `GameConfig`**, and it is the single highest-leverage number in Phase 1. Expect to change it after the first playtest.

### 2.2 WorldDefinition

```
WorldDefinition = {
  Id                 : string      -- UPPER_SNAKE, globally unique, never reused
  Name               : string      -- display
  Rarity             : RarityKey
  RollWeight         : number      -- basis points (see §3.1)
  EnabledInPhase     : number      -- 1 | 2 | 3 ; gates without deleting content
  Environment        : { SkyId, AmbientColor, FogColor, FogEnd, ClockTime }
  MusicId            : string?
  Enemies            : { string }  -- EnemyDefinition Ids
  BossId             : string?
  LootTableId        : string?
  DiscoveryTableId   : string?
  Modifiers          : { string }  -- allowed ModifierDefinition Ids
  DurationSeconds    : number
  MapPathLength      : number?     -- chunks between arrival and the arena; nil = config default
  PrebuiltMap        : { AssetKey : string, Scale : number }?   -- see below
  RecommendedPower   : number
  Flavor             : string      -- shown on the reveal card
}
```

**A world gets its map one of two ways, and declares which by data.**

| | Chunk kit | Prebuilt map |
|---|---|---|
| Declared by | chunks in `Content/Chunks/` naming the world | `PrebuiltMap` |
| Built by | `ChunkCore` + `Util/ChunkLoader` | `Util/PrebuiltLoader` |
| Every run | a different layout, from the expedition seed | identical |
| The art must be | modular: matching rims, gaps, heights | anything |

Declaring **both is a boot error** (`Schema.validateMaps`). Two routes to one
world's map is an ambiguity something downstream would have to resolve, and
resolving it is the second competing architecture CLAUDE.md rule 1 exists to
prevent. Declaring **neither** is legal and means the world is rollable but not
enterable — printed as a boot warning, refused politely at the Gate.

`ExpeditionSystem` contains exactly one branch on this, and it reads
`ExpeditionCore.hasPrebuiltMap(world)` — never a world id. Adding an authored
world changes no System.

`PrebuiltMap.AssetKey` names an `AssetManifest` entry, which names a `.rbxmx`
in `assets/rbxm/maps/` that Rojo syncs to `ServerStorage.LuckboundMaps`. Inside
it, two optional named parts are the whole contract with the modeller:
`EntryAnchor` (where the player arrives) and `ReturnAnchor` (where the way home
goes). Missing either, the loader derives it from the bounding box and warns —
so art can be walked before it is finished.

`PrebuiltMap.Scale` exists because authored scenes arrive at the scale their
author worked in. It is one number on the world, so correcting an oversized
scene costs a data edit rather than a re-export and re-upload of every mesh.

`MapPathLength` is **content, not config**, and the reason is a relationship
rather than a preference: a world with a short expedition needs a short map or
the whole expedition is the walk. A world running 300 seconds wants about 3
connective chunks; one that inherited the default 5 at that duration would be
40% traverse. The test suite asserts the relationship rather than either
number. It is meaningless on a prebuilt world, so setting both is also a boot
error.

`Flavor` is the "No records found." line for THE_UNKNOWN. It is part of the hook, not decoration.

### 2.3 ItemDefinition / DiscoveryDefinition / EnemyDefinition / BossDefinition

Full field lists are in `src/shared/Core/Types.luau` — that file is the machine-readable copy of this section, and it is authoritative over this table if they drift. Summary:

- **ItemDefinition:** `Id, Name, Rarity, Type (Weapon|Ability|Companion|Relic|Aura), Damage, AbilityId, PassiveId, Element, VisualId, WorldAffinity, DiscoveryText`
- **DiscoveryDefinition:** `Id, Name, Rarity, WorldAffinity, FlavorText, IsSoulbound, IsHidden, FatebreakEventId?, OddsDenominator`
- **EnemyDefinition:** `Id, Name, Health, Damage, WalkSpeed, AttackRange, TelegraphSeconds, AttackCooldown, ModelId, LootTableId`
- **BossDefinition:** `Id, Name, Health, Phases ({ HealthThreshold, AttackIds }), AttackIds, ModelId, LootTableId, FateReward`

`IsHidden = true` means the Discovery Book shows `???` until first discovery — the §10 community-research mechanic. It is a data flag, not a code path.

### 2.4 PlayerProfile — save schema v1

```
PlayerProfile = {
  SchemaVersion    : number   -- 1
  FatePoints       : number
  FateLevel        : number
  TotalRolls       : number
  RollHistory      : { { WorldId, Rarity, Timestamp } }  -- capped at 50
  Discoveries      : { [string]: { FirstFoundAt: number, Count: number } }
  Inventory        : { ItemInstance }        -- Phase 2
  EquippedSlots    : { [SlotName]: string }  -- Phase 2
  Stats            : { ExpeditionsCompleted, BossesDefeated, DeepestRarity }
  LastSeenAt       : number
  CreatedAt        : number
}
```

**Migration rule:** never rename or repurpose a field. To change meaning, add a new field, bump `SchemaVersion`, and add an entry to `SaveSystem.MIGRATIONS[n]`. A migration must be pure and idempotent.

---

## 3. The Fate Roll — full specification

This is the centre of Phase 1. Specified to the level where two different implementers produce the same behaviour.

### 3.1 Weights

`RollWeight` is in **basis points of the full game**, taken directly from Master Spec §4:

| World | Rarity | Weight (bp) | Full-game % |
|---|---|---|---|
| `VERDANT_VALLEY` | Common | 5000 | 50% |
| `ANCIENT_RUINS` | Uncommon | 2500 | 25% |
| `SUNKEN_KINGDOM` | Rare | 1200 | 12% |
| `INFERNO` | Rare | 700 | 7% |
| `SKY_CITADEL` | Epic | 400 | 4% |
| `ASTRAL_REALM` | Legendary | 150 | 1.5% |
| `THE_VOID` | Mythic | 45 | 0.45% |
| `THE_UNKNOWN` | Unknown | 5 | 0.05% |

**Only worlds with `EnabledInPhase <= GameConfig.CurrentPhase` enter the pool, and weights are renormalised over that pool.** This is why weights are absolute rather than percentages: Phase 3 can enable the full eight without retuning anything.

Phase 1 enables five — `VERDANT_VALLEY`, `ETHEREAL_SCAPE`, `EMBERFALL`, `SKY_CITADEL`, `ASTRAL_REACH` — with prototype weights summing to 10000 so they read directly as percentages:

| World | Rarity | Weight | % |
|---|---|---|---|
| `VERDANT_VALLEY` | Common | 6000 | 60% |
| `ETHEREAL_SCAPE` | Uncommon | 1500 | 15% |
| `EMBERFALL` | Rare | 1500 | 15% |
| `SKY_CITADEL` | Epic | 700 | 7% |
| `ASTRAL_REACH` | Mythic | 300 | 3% |

Adding the fifth world forced a renormalisation — the set must keep summing to
10000 or the numbers stop reading as percentages. The five points came off
Verdant Valley (70 → 60) and Emberfall (20 → 15), **not** off Epic or Mythic:
those are the two rates a player forms an opinion about, and they are
unchanged.

Sky Citadel is **data only**: the Biome Blueprint drafts no Sky Citadel (its §7.4 lists it as a reserved slot), so its enemies, boss and loot tables are empty and its Environment values are invented rather than blueprint-sanctioned. Phase 1 never enters a world, so this suffices today. **It needs a real biome before Phase 2 makes worlds enterable.**

> **Design decision requiring your sign-off (D-1):** at 5%, a tester doing 4 rolls has a 19% chance of ever seeing Astral Reach. If the point of the test is "does the rare roll make them react", 5% may be too rare to observe in a 10-minute session. Alternative: 65/25/10. I have gone with **75/20/5** as the default because a rare that is not rare does not produce the reaction either. Change `GameConfig.PrototypeWeights` to override.

### 3.2 First-roll rule

`TotalRolls == 0` always returns `VERDANT_VALLEY`, regardless of weights, and is flagged `IsTutorialRoll = true`. A new player's first experience must be the tutorial world. This does not increment any pity counter.

### 3.3 TRUE RNG — the roll is never weighted by the player

**Design decision, owner-directed, overrides Master Spec §4.**

The roll is an honest draw. No player state — Fate level, Fate points, total rolls, playtime, spend — changes the probability of any world. `FateCore.effectiveWeight` does not read the profile when `GameConfig.Fate.FateInfluencesOdds` is `false`, which is the default and the intent.

Fate remains the primary meta-progression stat. It is a **score and unlock currency**, not an odds modifier: it gates features, titles, Hall of Fate standing and Fatebreak eligibility. What it explicitly does not do is sell better luck.

> **Tension with the source document, recorded deliberately.** Master Spec §4 describes a ladder — "I can influence my world rolls" → "I can manipulate world modifiers" → "I can bend reality" — where Fate buys agency over RNG. True RNG removes the first two rungs. The endgame rungs (modifier control, Fatebreak Expeditions) can still be built as *content access* rather than *odds tilting*, and that is the recommended reading: Fate unlocks **which pools you may draw from**, never **how the draw resolves**. The weighting code is retained and disabled rather than deleted, so the decision is reversible with one boolean.

Two things this buys you, worth stating because they are the real argument for it:

1. **The roll is defensible.** Every roll is logged with its seed (§3.4.6), the draw is reproducible, and "the game is rigged against me" has a verifiable answer. An odds-tilting system has no such answer, and players will build spreadsheets.
2. **The rare result keeps meaning.** If Fate raises Mythic odds, a Mythic at high Fate is worth less than a Mythic at low Fate, and the Fatebreak announcement (§12) stops being a statement about luck.

### 3.3.1 Scripted onboarding — the first 15 rolls

True RNG creates one problem: a new player may never see what the game is capable of. The onboarding sequence solves that without touching the odds. `GameConfig.Fate.OnboardingSequence` forces rolls 1–15, in order; roll 16 onward is pure chance, forever.

| Roll | World | Rarity | | Roll | World | Rarity |
|---|---|---|---|---|---|---|
| 1 | Verdant Valley | Common | | 9 | Verdant Valley | Common |
| 2 | Verdant Valley | Common | | 10 | Verdant Valley | Common |
| 3 | Emberfall | **Rare** | | 11 | Emberfall | **Rare** |
| 4 | Verdant Valley | Common | | 12 | Verdant Valley | Common |
| 5 | **Ethereal Scape** | **Uncommon** | | 13 | Verdant Valley | Common |
| 6 | Emberfall | **Rare** | | 14 | Emberfall | **Rare** |
| 7 | Verdant Valley | Common | | 15 | Verdant Valley | Common |
| 8 | **Sky Citadel** | **EPIC** | | 16+ | *true RNG* | — |

Two rules shape it:

**1. It never hands out a Mythic.** A guaranteed top tier devalues the top tier permanently, and the Fatebreak announcement (§12) depends on Mythic meaning something. The arc peaks on Epic at roll 8. Astral Reach must be earned from honest odds. Enforced by test.

**2. It approximates the real odds.** Counted out: 9 Common, 1 Uncommon, 4 Rare, 1 Epic — 60/7/27/7 against true RNG's 60/15/15/7/3. A front-loaded parade of rares followed by a wall of Commons would make roll 16 feel like a punishment. Ending on a Common means the player has already felt what normal is, so the handover is continuous rather than a cliff. Enforced by test (drift < 12pp, and no run of more than 3 Commons).

**Slot 5 was changed from Common to Ethereal Scape (Uncommon)** when that world was added. It does three things at once: it teaches the second rung of the ladder, which the arc previously skipped; it guarantees every player sees the map-generation test biome inside the first minute rather than waiting on a 15% draw; and it drops the scripted Common share from 66.7% to **60.0%**, which is exactly the true rate — so the handover at roll 16 is now seamless rather than merely close. The arc still peaks on Epic at roll 8 and still never hands out a Mythic. **D-9 is extended, not reversed.**

The valleys are the point. Rares land at 3, 6, 11 and 14 with Commons between them, so each reads as a lift rather than an entitlement.

Other properties:

- **Indexed by `profile.TotalRolls`**, so it survives a rejoin mid-arc and cannot be farmed by disconnecting.
- Scripted rolls are flagged `IsScripted = true` and are **never announced server-wide** (§4.1) — otherwise every new player would fire banners.
- Only the first `ShortExpeditionRolls` (default 3) run short expeditions. Shortening all 15 would change what the game is, not just ease someone in.

**This resolves open question D-1.** The earlier worry was that at a 5% Astral Reach rate a tester in a short session would probably never see a rare roll. Guaranteeing an Epic during onboarding means every player learns the ladder exists — and learns there are tiers above what they have been shown.

> **Open design consequence, flagged.** With true RNG, a player at roll 200 faces exactly the same odds as at roll 16, so "stuck in Commons" is a permanent condition, not an early-game one. Fate cannot fix it by weighting — that is D-8. The lever consistent with true RNG is **Fate unlocking which pools you draw from**, never how the draw resolves (§3.3). Phase 3 work.

### 3.4 Server authority and anti-exploit

Non-negotiable, and the most common way a Roblox prototype gets ruined:

1. The client **sends no data** with `Fate_RequestRoll`. It is an empty signal. A roll request carrying a payload is discarded and logged.
2. The result is computed with a server-side `Random.new()` instance owned by `FateSystem`. Never `math.random`.
3. Rate limit: **1 roll per `GameConfig.Fate.RollCooldownSeconds`** (default 3.0) per player, enforced server-side with a timestamp in memory. Requests inside the window are dropped silently — no error to the client, which would just tell an exploiter where the boundary is.
4. The server validates the player is within `GameConfig.Fate.MaxRollDistance` (default 30 studs) of `Workspace.Crossroads.FateEngine.RollAnchor`. Distance checks are cheap and stop remote-spam from spawn.
5. The reveal animation is **client-side presentation of an already-decided result**. The client learns the answer at the start of the animation. This is correct and must not be "fixed": a client that learns the answer late can be made to reveal early, and a client that decides the answer is an exploit.
6. Every roll is logged server-side: `{userId, worldId, rarity, timestamp, seed}`. Without this you cannot answer "the RNG is rigged" accusations, which will arrive.

### 3.5 Roll sequence (canonical)

```
client: player enters RollAnchor radius
client: show "Press E / Tap to ROLL" prompt          (ProximityController)
client: input → Net.Fate_RequestRoll:FireServer()    (no arguments)
server: FateSystem.requestRoll(player)
          ├─ cooldown check          → drop
          ├─ distance check          → drop
          ├─ build enabled pool
          ├─ apply Fate weighting
          ├─ WeightedRandom.pick(pool, rng)
          ├─ ProgressionSystem.recordRoll(player, result)
          ├─ SaveSystem.markDirty(player)
          └─ Net.Fate_RollResult:FireClient(player, payload)
client: FateRoll UI plays reveal for Rarity.RevealDuration
client: reveal card → world name, rarity, flavor, colour
server: if result.Rarity >= MYTHIC → EventSystem.announce(...)  (all clients)
```

`payload = { WorldId, Name, Rarity, Flavor, IsTutorialRoll, RollNumber }`.

---

## 4. Network Contract

**One file creates remotes: `Core/Net.luau`. A remote created anywhere else is a spec violation.**

Naming: `Domain_Action`. Domain is the owning system. Past tense = server→client fact. Imperative = client→server request.

### Live remotes — this is the complete list

Created by `Core/Net.luau` and nowhere else.

| Name | Class | Dir | Payload | Guard |
|---|---|---|---|---|
| `Fate_RequestRoll` | RemoteEvent | C→S | *(none)* | cooldown + distance |
| `Fate_RollResult` | RemoteEvent | S→C | `RollPayload` | — |
| `Profile_Loaded` | RemoteEvent | S→C | `ProfileSnapshot` | fires once on join |
| `Profile_Updated` | RemoteEvent | S→C | `PartialSnapshot` | — |
| `Progression_FateChanged` | RemoteEvent | S→C | `{FatePoints, FateLevel, Delta, Reason}` | — |
| `Announce_Global` | RemoteEvent | S→C | `{Kind, Text, Rarity, PlayerName}` | server-only |
| `Event_StateSync` | RemoteEvent | S→C | live-event snapshot | fires on join (§4.1) |
| `UI_Acknowledge` | RemoteEvent | C→S | `{ScreenId}` | rate-limited 10/s |
| `Expedition_RequestEnter` | RemoteEvent | C→S | *(none)* | cooldown + distance + one-at-a-time |
| `Expedition_Started` | RemoteEvent | S→C | `ExpeditionPayload` | — |
| `Expedition_Ended` | RemoteEvent | S→C | `ExpeditionEndPayload` | — |
| `Expedition_TimerSync` | RemoteEvent | S→C | `{RemainingSeconds, ServerNow}` | — |
| `Debug_Command` | RemoteEvent | C→S | `{Name, Args}` | **Studio or place creator, + `Debug.AllowCommands`** |
| `Debug_Reply` | RemoteEvent | S→C | `{Ok, Text}` | — |

The two `Debug_*` remotes always **exist** but are **inert**: `DebugSystem`
connects no handler unless `GameConfig.Debug.AllowCommands` is true, and every
command additionally checks that the caller is in Studio or is the place's
creator. See `TESTING.md` §2.5 for the command list and the reasoning behind
which commands are server-side at all.

The four `Expedition_*` rows were **Reserved** in this table from the start,
which is exactly what reserving them was for: implementing expedition entry
promoted names the spec already owned instead of inventing new ones.

### Reserved — declared now, implemented in Phase 2/3

Declaring these now stops an agent from inventing `CombatHit2` when it needs one.

`Combat_RequestAttack`, `Combat_RequestAbility`, `Combat_RequestDodge`, `Combat_HitConfirmed`, `Combat_EnemyStateChanged`, `Loot_Awarded`, `Discovery_Found`, `Discovery_BookSync`, `Inventory_RequestEquip`, `Inventory_Changed`, `Event_FatebreakStarted`, `Event_FatebreakEnded`.

### 4.1 Late joiners — the rule that is easy to get wrong

**Requirement: anything globally visible must be visible to a player who joins a server that is already running.**

`FireAllClients` only reaches people who are already connected. A Fatebreak broadcast at minute 2 does not exist for someone who joins at minute 3, even though the event is still running. So:

1. **Server state is the source of truth, not the broadcast.** `EventCore.State` holds active events and a recent-announcement buffer. Every broadcast is a *side effect* of mutating that state — never the other way round.
2. **Mutate state before broadcasting.** A player joining in the gap between the two still gets the event via their snapshot.
3. **Every join gets `Event_StateSync`** with the full picture: active events with `RemainingSeconds` and `ElapsedSeconds`, plus the last `AnnouncementBufferSize` announcements with `AgeSeconds`.
4. **Send remaining time, not absolute end time.** A client with a skewed clock still counts down correctly. `ServerNow` is included for anything that needs to reconcile.
5. **Announcements age out** (`AnnouncementBufferMaxAgeSeconds`, default 300 s) so a joiner sees what just happened, not a week of history.
6. **Cross-server** (Master Spec §12 — reality altered *everywhere*) runs over `MessagingService`. The payload carries the original `StartedAt`, so every server counts down to the same wall-clock end and a late joiner on *any* server sees the same clock.
7. **Sweep expired events on a timer** and re-sync, so nobody is left rendering a Starfall that ended.

If you fire a remote to "everyone" without touching `EventCore` state, you have just made something invisible to the next person through the door.

### Universal remote rules

1. Every `OnServerEvent` handler validates argument **count and type** before use. `FireServer` can be called with anything.
2. No `RemoteFunction` from client to server anywhere in this project. A yielding server call is a hang waiting to happen; use event pairs.
3. No remote carries an `Instance` from client to server except a `Player` — and the server ignores it and uses the implicit sender.
4. Server never trusts a client-sent number. Not position, not damage, not index.

---

## 5. Phase 1 Task List — AI-executable

Each task is independently assignable. `DoD` = Definition of Done. Dependencies are hard.

**All 18 tasks are complete.** Kept for reference and for the dependency graph.

| ID | Task | Depends | DoD | |
|---|---|---|---|---|
| **T-101** | Repo scaffold: `rokit.toml`, `default.project.json`, `.gitignore`, folder tree | — | `rojo build` produces an `.rbxlx` that opens in Studio | ✅ |
| **T-102** | `Core/Types.luau` — all schemas from §2 as Luau types | T-101 | `luau-lsp` reports 0 errors | ✅ |
| **T-103** | `Core/Constants.luau` — rarity table, enums, frozen | T-102 | Table is deep-frozen; mutation throws | ✅ |
| **T-104** | `Core/GameConfig.luau` — every tunable in §3, §6 | T-102 | No magic number appears in any System | ✅ |
| **T-105** | `Core/Net.luau` — builds the 7 Phase-1 remotes | T-103 | All 7 exist under `ReplicatedStorage/Luckbound/Net` at runtime | ✅ |
| **T-106** | `Util/WeightedRandom.luau` + unit test | T-102 | 1e6-sample test: observed % within 0.5pp of expected | ✅ |
| **T-107** | `Util/Schema.luau` — validate Content against Types | T-102 | Malformed world fixture fails boot with a named field | ✅ |
| **T-108** | `Content/Worlds` — 3 prototype + 5 Phase-3 stubs | T-107 | All 8 validate; 3 enabled | ✅ |
| **T-109** | `SaveSystem` — ProfileStore-style session locking | T-104 | Rejoin test P1-8; Stop-mid-session test P1-9 | ✅ |
| **T-110** | `ProgressionSystem` — Fate points, level curve, roll history | T-109 | Fate increments persist | ✅ |
| **T-111** | `FateSystem` — §3 in full, incl. all §3.4 guards | T-106, T-110 | Exploit tests P1-5, P1-11 pass | ✅ |
| **T-112** | `HubBuilder` — Crossroads blockout, 5 districts + Fate Engine | T-101 | P1-2, P1-3, P1-4 | ✅ |
| **T-113** | `init.server.luau` — bootstrap in §1.2 order | T-105…T-111 | Boots clean, 0 Output errors | ✅ |
| **T-114** | `ProximityController` + `StateController` (client) | T-105 | Prompt shows/hides at radius | ✅ |
| **T-115** | `UI/FateRoll` — build-up, reveal, result card | T-114 | P1-6, P1-7, P1-10 | ✅ |
| **T-116** | `UI/GlobalAnnouncements` — banner for Mythic+ | T-114 | Fires on a forced Mythic roll | ✅ |
| **T-117** | `init.client.luau` — client bootstrap | T-114…T-116 | Boots clean | ✅ |
| **T-118** | CI: StyLua, Selene, forbidden-name grep (P1-12) | T-101 | Green on push | ✅ |

Two tasks grew beyond their original description: **T-112** was rebuilt against the Biome Blueprint (five zone builders dispatched by `Kind`, shared PortalRig, `GameConfig.HubLayout` anchors), and **T-115** gained the 2.5 s portal spin-up that must precede the result banner.

**Suggested parallelisation if you run multiple agents:** T-102→104 must be one agent, sequentially, first — everything downstream depends on those three files being coherent. After that, `{T-106,T-107,T-108}`, `{T-109,T-110}`, and `{T-112}` are independent. T-111 joins the first two. UI (T-114→117) needs only T-105.

---

## 6. Tunables Requiring Your Sign-Off

These are design decisions I made to keep the spec executable. Each is a one-line change. Flagged rather than buried:

| # | Decision | Default | Why |
|---|---|---|---|
| ~~D-1~~ | ~~Phase 1 roll weights~~ | 75 / 20 / 5 | **Resolved** by scripted onboarding (§3.3.1) |
| ~~D-2~~ | ~~First roll forced to tutorial~~ | — | **Superseded** by the 3-roll onboarding sequence |
| D-8 | Fate never affects odds | `FateInfluencesOdds = false` | Owner-directed. §3.3 records the tension with Master Spec §4 |
| D-9 | Onboarding length | 3 rolls / 100 s each | Fits ~5 min; shows the full rarity ladder once |
| D-3 | Roll cooldown | 3.0 s | Long enough to prevent spam, short enough not to annoy |
| D-4 | Reveal duration scales with rarity | 2.5 s → 7.0 s | The anticipation mechanic; highest-leverage number |
| ~~D-5~~ | ~~Fate weight bonus per level~~ | inert | **Disabled** by D-8; code retained, flag off |
| D-6 | Roll history cap | 50 entries | DataStore size safety |
| D-7 | Expedition duration | 720 s (12 min) | From PDF §6; likely too long for a PoC — revisit in Phase 2 |

D-7 is worth arguing about now. Twelve minutes is a long first expedition for a tester who does not yet know if they like the game. Phase 2 may want 4–5 minutes.

---

## 6.1 Bugs Found Building Phase 1

Recorded because each cost a debugging cycle and each is a class of mistake that will recur.

| Bug | Why the tests missed it |
|---|---|
| `Workspace.FilteringEnabled` is read-only; Rojo errored applying it | Never exercised — it is project-file config, not code |
| `type()` used to validate a `Vector3`; Luau reports `"vector"` | Harness shimmed `Vector3` as a table, so `type()` returned `"table"`. **152 tests passed against a build that could not boot.** |
| `DataStoreService:GetDataStore` raises on an unpublished place | Roblox-only path; the bootstrap died at step 3 of 9 |
| `MessagingService:SubscribeAsync` yields forever on an unpublished place | `pcall` catches errors but not hangs. Silent stall at step 5 of 9 — no error text at all |
| `PortalRig` rings rotated about the world origin, not the ring centre | Geometry, not asserted by any test |
| `deepFreeze` raised on a table reachable by two paths | Only triggered once `UITheme` reused `Constants` tables |
| **`CylinderMesh` gives a part *block* collision** — invisible corners stopped the player in open space | No test rendered geometry; only data was asserted |
| **`CylinderMesh`'s axis is Y, `PartType.Cylinder`'s is X** — every caller passed the X convention, so the 1150-stud plaza was built as a 1150-stud **wall** and the hub had no floor | A dimension triple is valid data whichever way round it means |
| Walkways used the platform's **X** half-extent regardless of approach axis, leaving 30–40 stud holes | The number was right for two zones out of four |
| The Observatory ramp used a literal 5-stud step depth; at the new radius steps were 26 studs apart | The literal was correct at the old 120-stud scale |
| The Gate's prompt sat on a plinth wider than its own activation distance | The reach test carried a `* 2` fudge and covered only the Engine |
| The Observatory's spiral ramp encircled the Fate Engine (radius 98–138 against a 120-stud platform) and blocked the approach to it | A gradient test existed; nothing asserted *where* the ramp was. The district was later cut — see `BLUEPRINT_RECONCILIATION.md` |
| A district got two platforms — a box from `buildPlatform` and a cylinder from its own builder, one buried in the other | Platform shape was implied by which builder ran, not declared in data |
| **`MeshPart.MeshId` is not assignable at runtime** — `HubBuilder.meshOrNil` set it inside a `pcall`, so every `MeshId` seam silently drew a primitive instead | No authored mesh had ever been supplied, so the fallback path was the only one ever exercised |
| **An authored `Crossroads` disabled the roll anchor, gate anchor, spawn and lighting** along with the generated geometry | `build()` returned early as one branch; nothing separated *geometry* from *contract* |

Four lessons worth keeping:

1. **A shim that is merely enough to pass is worse than no test.** Make shims behave like the real type.
2. **A yielding `init()` is invisible.** Hence the `[LUCKBOUND] boot N/11` progress logging — a stall now names its own step.
3. **A test that asserts a number proves nothing about the shape that number produces.** `Plaza.Diameter == 1150` was true the whole time the plaza was a wall. Assert *relationships* — thinner than it is wide, can be jumped onto, reaches past its own plinth — because those survive a rescale and a literal does not.
4. **A fudge factor in an assertion is a disabled assertion.** The prompt-reach check passed with `* 2` in it while the Gate was genuinely unusable. If a test needs slack to pass, find out why before adding the slack.

## 7. What Phase 1 Deliberately Excludes

Listed so no agent "helpfully" adds them:

Combat of any kind · enemies · bosses · loot · inventory · equipment · the Discovery Book · ~~expedition entry or exit~~ *(see §7.1)* · world modifiers · AFK/idle · trading · leaderboards · monetisation · Fatebreaks beyond the announcement banner · audio beyond a single roll SFX.

If a task seems to require one of these, the task is wrong. Raise it; do not implement it.

---

## 7.1 Amendment: expedition entry, opened 2026-09-16

**Owner-directed.** This is the one item lifted out of §7, and the amendment is
recorded here rather than made quietly, per CLAUDE.md rule 8.

### What was opened, and what was not

| | |
|---|---|
| ✅ Entering a rolled world through the Expedition Gate | the whole point |
| ✅ Seeded map generation from the chunk library | the thing being tested |
| ✅ A per-player expedition timer and a way home | you cannot test a door you cannot come back through |
| ✅ Per-client biome lighting | §6 checklist item, and free once entry exists |
| ❌ Combat, enemies, bosses, loot, inventory, the Discovery Book | **still excluded** |

**The exclusions above are not softened.** An expedition today is: arrive, walk
a generated map, come back. Nothing fights you and nothing drops. If a task
seems to need combat, the task is still wrong.

### Why it was opened now

The modular map system (`docs/MODULAR_MAPS.md`) has been assembling layouts in
CI since 2026-09-16 and **not one of them had ever been stood in.** A layout
that validates as a list of numbers and a layout that reads as a place when you
walk it are different claims, and only the first was being tested. Ethereal
Scape — the first world with authored art behind it — made the second claim
worth checking before more kits were authored against untested assumptions.

### The switch

`GameConfig.Expedition.Enabled`. Set it to `false` and the game is Phase 1
exactly: the Gate's prompt disappears, `Expedition_RequestEnter` is dropped at
the door, and nothing else changes. The amendment is one boolean wide.

### What it added

| | |
|---|---|
| `Core/ExpeditionCore.luau` | pure: destination, seed, eligibility, timer. Testable |
| `Util/ChunkLoader.luau` | Layout → Instances. The Roblox half of the chunk system |
| `Systems/ExpeditionSystem.luau` | remotes, geometry, teleports, timer sweep |
| `Controllers/ExpeditionController` | lighting apply/revert, local countdown |
| `UI/ExpeditionHud` | destination banner, countdown, toasts |
| 4 remotes | promoted from Reserved, §4 |

### Anti-exploit, same standard as §3.4

1. `Expedition_RequestEnter` carries **no payload**. One carrying arguments is
   discarded and logged.
2. The Gate's `ProximityPrompt.Triggered` fires **on the server** with the
   triggering player, so the primary entry path carries no client data at all.
3. Rate limited to one entry per `EntryCooldownSeconds`, server-side.
4. Distance validated against the Gate's portal, `MaxEntryDistance`.
5. One expedition per player; stage slots are bounded by `MaxConcurrent`.
6. Every refusal is **silent** except the two a legitimate player can actually
   hit (no destination; the world has no map kit). Same reasoning as §3.4.3.
7. Every expedition is seeded from `(userId, rollNumber, worldId)` and the seed
   is logged, so any map can be rebuilt exactly. The §3.4.6 argument about
   rigged rolls applies equally to rigged maps.

### The gap this exposes

Three rollable worlds have no chunk kit — **Emberfall, Sky Citadel, Astral
Reach.** Rolling one and walking to the Gate now produces *"That world has no
map yet."* rather than a crash, and the list is printed as a warning on every
boot and asserted by test. That is the honest state, not a solved problem:
`ETHEREAL_SCAPE` and `VERDANT_VALLEY` are the only enterable worlds.
