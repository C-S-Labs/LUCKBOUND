# Biome Blueprint v0.1 — Reconciliation Record

**Status: implemented and verified in Studio.** The Biome Blueprint arrived after
the Phase 1 build spec and shipped code, and declares itself canon in several
places. Where it and existing canon disagreed, this is what was done and why.

**Four items still need the owner's sign-off** (§ below). Everything else is
merged, tested and running.

---

## Adopted verbatim

| Blueprint | Where it landed |
|---|---|
| §1.1 rarity palette | `Core/Constants.luau` — replaces the prototype palette |
| §1.2 lighting baseline | `HubBuilder.applyLighting()` |
| §1.3 PortalRig | `Util/PortalRig.luau` — one rig, reskinned by rarity |
| §1.4 UITheme | `Core/UITheme.luau` — new, per "add before any Phase 2 UI" |
| §2.1 layout & anchors | `GameConfig.HubLayout.Anchors` |
| §2.2 all five zones | `Content/Hub/Crossroads.luau` + `HubBuilder` |
| §2.3 hub sky & ambient | `Crossroads.Theme` |
| §3.3 / §4.3 / §5.3 biome lighting | each world's `Environment` |
| §3.5 ModifierOverrides | `VerdantValley.luau` NIGHT entry |

---

## ⚠️ Needs sign-off

### 1. §1.1's Usage column contradicts §4.4 and §5.4

§1.1 assigns **Mythic orange → "Emberfall portal/UI accent"**. But §4.4 says
Emberfall's ring is **blue `#3E8EF7` (Rare)**, and §5.4 says Astral Reach's is
**Mythic orange**. §1.1's note that "Common/Rare/Mythic map to prototype worlds
1:1" agrees with §4.4/§5.4 and not with its own Usage column.

**Resolved as:** Verdant Valley → Common grey, Emberfall → Rare blue, Astral
Reach → Mythic orange. The Usage column is the outlier and I treated it as a
typo. Three tests lock this in.

### 2. Rarity ordering

The blueprint lists rows Common, Rare, Epic, **Mythic, Legendary** — which would
rank Legendary above Mythic. Existing `Constants.RARITY.Order` has Mythic above
Legendary, and master spec §4 agrees (The Void at 0.45% is Mythic; Astral Realm
at 1.5% is Legendary — the rarer world is Mythic).

**Resolved as:** row order is presentation, not ranking. `Order` unchanged.
If you actually want Legendary as the top tier, that's a one-line change but it
inverts which of the five future worlds is rarest.

### 3. UNCOMMON has no blueprint colour

§1.1 lists six tiers. The code carries seven — `UNCOMMON` is used by
`ANCIENT_RUINS` (25%) in build spec §3.1, which is Phase 3 content.

**Resolved as:** kept the prototype green `#5FD97A`. **This is the one colour in
`Constants` that is not blueprint-sanctioned.** Either bless it or give me a hex.

### 4. §4.1's own open flag

The blueprint asks for explicit sign-off that environment colour ≠ rarity colour
(its option (a)). Implemented as (a), and §6's checklist item 1 is enforced by
test. Confirming it closes the flag for every future world's asset prompts too.

---

## Deliberate deviations

### CSG tori → segmented rings

§1.3 specifies rings as CSG (large cylinder minus smaller). Runtime
`SubtractAsync` is slow, can fail, and cylinder-minus-cylinder yields an annulus
rather than a torus anyway. Rings are built from `GameConfig.Portal.RingSegments`
(28) parts arranged radially — visually equivalent, no CSG cost, identical on
mobile. Swap in a mesh via `MeshId` when authored art arrives.

Same reasoning for the **octagonal plinth**: it is a cylinder standing in for an
octagon, and is the first thing an authored mesh should replace.

### Training dummies are geometry only

§2.2 wants 3 dummies that "respond to basic attack input" plus a boss dummy with
a health bar. **Combat is excluded from Phase 1** (build spec §7), and CLAUDE.md
rule 8 forbids widening scope. The dummies are built as static rigs carrying
`IsTrainingDummy` and `Phase = 2` attributes so Phase 2 can find them. No combat
behaviour is attached. The health bar is Phase 2.

### Hub layout lives in GameConfig, visuals in Content

§2.1 asks for `GameConfig.HubLayout`; the project's prime directive says content
is data under `Content/`. Split along the blueprint's own TUNABLE rule: **named
anchors and dimensions** in `GameConfig.HubLayout` (locked once, never
re-derived, per §7.3), **materials, palette and props** in
`Content/Hub/Crossroads.luau`.

### Portal spin-up runs client-side

§1.3's 2.5s spin-up plays on the rolling player's client, so two players rolling
at once don't fight over one animation. Enforced by test: the reveal banner can
never appear before the spin-up completes.

---

## Axis mapping — confirmed and locked (§7.3)

Roblox is Y-up, so "compass" is the X/Z plane. Locked in
`GameConfig.HubLayout.Anchors`, asserted by test:

```
NORTH = -Z   Hall of Legends      (0, 0, -46)
EAST  = +X   Discovery Archive    (46, 0, 0)
SOUTH = +Z   Expedition Gate      (0, 0, 46)
WEST  = -X   Training Grounds     (-46, 0, 0)
UP    = +Y   Global Observatory   (0, 40, 0)
```

Note the blueprint's §2.1 ASCII has a parenthetical "NORTH (+Z... use +Y in
Studio terms per your axis convention, confirm in-engine)". +Y is up in Roblox
and cannot be north; I read that as the uncertainty §7.3 flags, and resolved it
as above. **Verify the sightlines look right in Studio** — if north/south feel
reversed, flip the sign on the Z anchors and nothing else changes.

---

## Later additions, after the blueprint merge

**Sky Citadel (Epic) was added** so the onboarding arc could peak on an Epic
rather than handing every new player a guaranteed Mythic. The blueprint reserves
Epic `#B24BF3` for exactly this slot (§1.1) and lists Sky Citadel among the five
undrafted worlds (§7.4).

It is **data only**: no blueprint section exists for it, so its enemies, boss and
loot tables are empty and its Environment values are invented rather than
blueprint-sanctioned. Phase 1 never enters a world, so this suffices today.

> ⚠️ **This is the largest open debt.** Sky Citadel is live in the roll pool at
> 7%. Rolling it in Phase 2 would send a player to a world that does not exist.
> It needs a blueprint section — palette, layout, enemies, boss, an optional
> side-content pocket per §6 — before expeditions become enterable.

**Rarity colours are verified against §1.1 by test**, and the theme-vs-rarity
rule from §4.1 is enforced: Emberfall's environment is fire-orange while its
portal ring is Rare blue.

## §6 cross-biome checklist status

| Item | Status |
|---|---|
| Portal/UI colour = rarity table, not biome palette | ✅ enforced by test |
| Biome geometry under `Assets/Worlds/<WorldId>/` | ⏳ Phase 2 (no biome geometry yet) |
| World data in `Content/Worlds/`, zero world logic in Systems | ✅ |
| Lighting applied/reverted by ExpeditionSystem, never bleeding | ⏳ Phase 2 (data ready) |
| Boss arena a distinct shape per biome | ⏳ Phase 2 |
| One optional side-content pocket per biome | ⏳ only Emberfall's is specified |
| Mobile part/light budget vs Verdant Valley baseline | ⏳ no biome built yet |

**Hub baseline measured: 436 instances**, printed on boot. That is the number
every biome's part budget should be compared against until a biome exists to set
its own baseline.
