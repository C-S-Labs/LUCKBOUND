# Reserved and unconsumed declarations

**The problem this solves.** Several fields, remotes and options are declared,
typed and schema-validated while nothing reads them. Most are deliberate — the
project declares a shape before the system that consumes it, so content authored
today does not need re-authoring later. But a reader could not tell a
*reserved* field from a *forgotten* one without trawling the worklog, and that
ambiguity has already cost real time: `IncludeSide` sat unread for six days,
and `ScenarioCore` was written, tested and left unwired.

**The rule.** Anything declared but unread appears here. A declaration that is
unread *and absent from this table* is a defect, not a decision — that is the
whole point of the register.

Declarations carry a `RESERVED:` comment at the site, pointing here.

Status meanings:

| | |
|---|---|
| **CONSUMED** | Something reads it. Listed only where it was previously reserved. |
| **RESERVED** | Deliberate. The consumer is named and scheduled. |
| **OBSOLETE** | Superseded. Slated for removal, with the replacement named. |
| **ORPHANED** | No consumer, no plan. **A defect.** |

---

## World definition — `Core/Types.WorldDefinition`

| Field | Status | Consumer |
|---|---|---|
| `BossId` | RESERVED | Boss spawning. Blocked by build spec §7 (combat excluded). |
| `LootTableId` | RESERVED | Loot awards for worlds without a `Loot` block. Superseded for any world that adopts §7.5's `Loot` (Sky Citadel): it will become OBSOLETE once every world has one. |
| `DiscoveryTableId` | RESERVED | The Discovery Book. `DEVELOPMENT_PLAN.md` Phase 2 — the first playtest's objective. |
| `MusicId` | RESERVED | Per-world music. `DEVELOPMENT_PLAN.md` lists sound as a playtest blocker. |
| `SkyId` | RESERVED | A per-world **skybox**. Distinct from an event's `Sky` table, which is a temporary overlay `SkyController` already reads — one is the world, the other is weather over it. |
| `Modifiers` | RESERVED | World modifiers. Blocked by §7. Validated today so a malformed list cannot ship. |
| `ModifierOverrides` | RESERVED | Same. Verdant Valley's `NIGHT` entry is the reference shape every other world follows. |

## Chunk definition — `Core/Types.ChunkDefinition`

| Field | Status | Consumer |
|---|---|---|
| `Supports` | **CONSUMED** | `ScenarioCore.compatible` and `Schema.validateChunks`. Reserved from 2026-09-22, live since the scenario layer was wired in. |
| `GroundOffsetY` | **CONSUMED** | `ChunkLoader.build`. |
| `EnemyTags` | RESERVED | Enemy population. Blocked by §7. Declared per piece so a kit authored now does not need revisiting. |
| `Tags` | **AUTHORING ONLY** | Deliberately unread by any System. Free-text notes that make a kit legible to a human — `"gate-to-boss"`, `"roofed"`, `"rare"`. Reading them from code would turn authoring notes into behaviour, which is what `Supports` exists to prevent. |

## Remotes — `Core/Net`, build spec §4

| Remote | Status | Consumer |
|---|---|---|
| `Profile_Updated` | RESERVED | Partial profile pushes. `Profile_Loaded` carries the full snapshot today; this becomes worthwhile when a profile grows past one cheap send. |
| `UI_Acknowledge` | RESERVED | Client→server screen acknowledgement, for tutorial and first-join flows. |

Both sit in §4's **main** table rather than its Reserved list, which reads as
"live". They are reserved; §4 has been annotated to say so.

## Generation options

| Option | Status | Consumer |
|---|---|---|
| `AssembleOptions.IncludeSide` | **CONSUMED** | `ChunkCore.assemble`, and passed from `GameConfig.Expedition.IncludeSide` by `ExpeditionSystem`. Was declared-and-unread from 2026-09-16 to 2026-09-22, then implemented but still not passed from config until 2026-09-23. |

---

## Loot, fixtures and vault keys — build spec §7.5

The machinery is live; these are the slots it leaves for decisions the owner
deferred on 2026-09-23 ("we will put off the loot decisions until the actual
loot pools are constructed").

| Declaration | Status | Consumer |
|---|---|---|
| `LootPool.Entries` (every pool in `Content/LootPools`) | RESERVED | Filled when the loot pools are designed. Rolled today (each member's share is empty); filling one is a content edit only. |
| What an `ItemId` **is**, and where a drop is stored | RESERVED | `LootSystem.grantDrops` is the single seam: today it logs any non-empty drop loudly rather than dropping it silently. Needs the inventory decision (§7 still excludes inventory apart from keys). |
| `KeyCore.dropChance(base, modifiers)`: the `modifiers` list and `KeyChanceDelta` | RESERVED | World modifiers (§7-excluded). `LootSystem` passes an empty list; a modifier with `KeyChanceDelta` moves the key chance, never the vault's `SpawnChance`. |
| `GameConfig.Loot.BossDefeatStandIn` | RESERVED (stand-in) | Replaced by a real boss-defeated event once bosses exist; until then, reaching the arena counts. |

## Nothing is currently ORPHANED

Every unread declaration above has a named consumer and a reason to exist. The
two that were genuinely orphaned — `ScenarioCore` and the
`GameConfig.Expedition.IncludeSide` dial — were wired up rather than listed
here, because a register is for deliberate reservations and not a place to
park work.

## When you add a reserved declaration

1. Add the row here, with the consumer named and the blocker stated.
2. Put `RESERVED: see docs/RESERVED.md` at the declaration.
3. When the consumer lands, move the row to **CONSUMED** or delete it.

If you cannot name the consumer, the declaration is premature. Leave it out.
