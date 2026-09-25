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

### 3. UNCOMMON has no blueprint colour — ⚠️ now urgent, was theoretical

§1.1 lists six tiers. The code carries seven.

**This stopped being a hypothetical on 2026-09-16.** When it was written,
`UNCOMMON` was used only by `ANCIENT_RUINS`, a Phase 3 world nobody could roll.
**Ethereal Scape is Uncommon, live at 15%, and guaranteed at onboarding roll 5**
— so the unsanctioned green `#5FD97A` is now on screen for every player within
a minute of joining: on the reveal card, on the Gate's ring, and on the portal
home from the expedition.

**Resolved as:** kept `#5FD97A`. **It is the one colour in `Constants` that is
not blueprint-sanctioned, and it is now shipping.** Either bless it or give a
hex — changing it later means changing it after people have learned it.

There is a second, softer problem worth naming: Ethereal Scape's meadows are
**mint green** and Uncommon is **green**, so this is the weakest test in the
game of the §4.1 rule that portal colour comes from the rarity table rather
than the biome palette. On every other world the two are obviously different
and a mistake would be visible. Here it would not be. A test asserts the
contract directly for that reason.

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
a health bar. **Combat is excluded from Phase 1** (build spec §7), and AGENTS.md
rule 8 forbids widening scope. The dummies are built as static rigs carrying
`IsTrainingDummy` and `Phase = 2` attributes so Phase 2 can find them. No combat
behaviour is attached. The health bar is Phase 2.

### Hub layout lives in GameConfig, visuals in Content

§2.1 asks for `GameConfig.HubLayout`; the project's prime directive says content
is data under `Content/`. Split along the blueprint's own TUNABLE rule: **named
anchors and dimensions** in `GameConfig.HubLayout` (locked once, never
re-derived, per §7.3), **materials, palette and props** in
`Content/Hub/Crossroads.luau`.

### The Global Observatory was cut entirely

**Owner-directed, 2026-09-17.** §2.2 specifies five hub zones. There are now
four: the Global Observatory is gone, along with its orrery, its platform and
its access ramp.

**The reason is that nobody could say what it was for.** Its only content was
the orrery — a translucent globe "representing the server". That is a
decoration, not a feature, and the owner's verdict was *"I don't understand the
purpose in the first place."*

Two things had already made it expensive:

- **Its access blocked the Fate Engine.** §2.2's spiral ramp, built literally
  at the rescaled hub, was a 2.5-turn helix at radius 118 and forty studs wide
  — occupying radius 98–138 against the Engine's 120-stud platform. It wrapped
  the most important object in the game in a wall of steps. Straightening it
  into a processional fixed the symptom and cost a session.
- **It could not simply be lowered.** Sitting above the Engine meant sitting
  above the rig's 111-stud crown, and *that* height is what forced a 145-stud
  climb for a look-out.
- **The architecture moved under it.** Expeditions are to become a separate
  place (`STATUS.md` §5), so the Crossroads becomes a lobby. A monument you
  climb on your way to nowhere is harder to justify in a lobby, not easier.

**Resolved as:** removed. If a global-state display is wanted later, the
recommendation on record is a **ground-level sixth compass point**, not a tower
above the centre — height above the Engine is what created every problem it
had.

A test now asserts the general rule the ramp broke: **no district's platform
may reach into the Fate Engine's footprint.**

### A world may ship one authored map instead of a chunk kit

**Added 2026-09-17**, and it is an addition rather than a retreat: the chunk
system is untouched and still builds Verdant Valley.

Addendum §A4 describes one way a biome gets a map — a kit of interchangeable
pieces that the assembler arranges per seed. The first real delivery of
authored art did not fit it. Ethereal Scape's scene is a **composed traverse**:
its eight islands climb 58 studs a step, each of its six bridges is cut to its
own gap at that gap's height, the landings are authored in matched pairs naming
the two islands they join, and the islands grow from 1030 × 813 at the arrival
shelf to 1932 × 1535 under the temple. Every one of those breaks if the pieces
are shuffled.

Making it modular would have meant re-authoring it — identical gaps, identical
height deltas, identical rims — to buy variety in a world that exists to test
map loading. So a world now declares **either** a chunk kit **or** a
`PrebuiltMap`, and that choice is data (build spec §2.2). `ExpeditionSystem`
has one branch on it, reading `ExpeditionCore.hasPrebuiltMap(world)` and never
a world id, so the prime directive holds: adding an authored world changes no
System.

Declaring both is a boot error. Two routes to one world's map would put a
choice somewhere downstream, and that is the second competing architecture
AGENTS.md rule 1 exists to prevent.

**What this costs:** every run of a prebuilt world is the same map. For a test
biome with no combat that is nothing; for a world players farm it would be a
real loss, and the kit route stays the default for those.

### §2.3's hub lighting was brightened — key light, not exposure

"Hub is very dark" was open from the first Studio session to the sixth.
§2.3's values were authored against Roblox's default lighting; under `Future`
lighting across a 1150-stud footprint they left the plaza close to unreadable.

**The cause was `ClockTime = 22`, not `Brightness`.** With the sun below the
horizon there is no key light for `Brightness` to raise — turning it up only
blows out the neon and the portal glow while the stone stays flat.

**Resolved as:** `ClockTime` 22 → **4.5**, which puts the sun just above the
horizon: a low raking pre-dawn light that still reads as night and keeps the
purple sky §2.3 specifies. `Brightness` 2 → 2.6 and `ExposureCompensation`
0 → 0.15 alongside it. **The palette is untouched** — ambient and outdoor fill
were lifted in luminance only, the hues are §2.3's.

Asserted by test as a relationship rather than a number: the key light must be
above the horizon, and the hub must be brighter than the darkest biome.

### Portal spin-up runs client-side

§1.3's 2.5s spin-up plays on the rolling player's client, so two players rolling
at once don't fight over one animation. Enforced by test: the reveal banner can
never appear before the spin-up completes.

---

## Axis mapping — confirmed and locked (§7.3)

Roblox is Y-up, so "compass" is the X/Z plane. Locked in
`GameConfig.HubLayout.Anchors`, asserted by test:

```
NORTH = -Z   Hall of Legends      (0, 0, -420)
EAST  = +X   Discovery Archive    (420, 0, 0)
SOUTH = +Z   Expedition Gate      (0, 0, 420)
WEST  = -X   Training Grounds     (-420, 0, 0)
UP    = +Y   Global Observatory   (0, 140, 0)   <- cut 2026-09-17, see above
```

*(The radii were 46 and 40 when this was written; the 10× world rescale on
2026-09-16 moved them to 420 and 140. The axis mapping itself is unchanged —
that is the part that was locked.)*

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
blueprint-sanctioned.

> ⚠️ **This is the largest open debt, and it is no longer hypothetical.**
> Expeditions became enterable on 2026-09-16 (build spec §7.1). Sky Citadel is
> live in the roll pool at 7% with no chunk kit, so a player who rolls it and
> walks to the Gate is told *"That world has no map yet."* — refused politely
> rather than crashed, but refused. **Emberfall (15%) and Astral Reach (3%) are
> in the same position**: 25% of honest rolls now land on a world that cannot
> be entered.
>
> Emberfall and Astral Reach at least have blueprint sections and need only a
> chunk kit. Sky Citadel needs the section first — palette, layout, enemies,
> boss, and a §6 side pocket.
>
> The list is printed as a warning on every boot and asserted by a test, so the
> number cannot drift without someone noticing.

**Rarity colours are verified against §1.1 by test**, and the theme-vs-rarity
rule from §4.1 is enforced: Emberfall's environment is fire-orange while its
portal ring is Rare blue.

## §6 cross-biome checklist status

| Item | Status |
|---|---|
| Portal/UI colour = rarity table, not biome palette | ✅ enforced by test |
| Biome geometry under `assets/source/worlds/<world_id>/` | ✅ Ethereal Scape; others still empty |
| World data in `Content/Worlds/`, zero world logic in Systems | ✅ |
| Lighting applied/reverted by ExpeditionSystem, never bleeding | ✅ **closed** — see below |
| Boss arena a distinct shape per biome | ✅ Ethereal Scape's Sky Temple is authored and uploaded; Verdant Valley's is blockout |
| One optional side-content pocket per biome | ✅ Verdant Valley's is a kit piece; Ethereal Scape's are its 14 satellite islands. Emberfall's is specified but unbuilt |
| Mobile part/light budget vs Verdant Valley baseline | ⏳ blockout only, no mesh budget yet |

**Hub baseline measured: 436 instances**, printed on boot. That is the number
every biome's part budget should be compared against until a biome exists to set
its own baseline.

### Lighting bleed — closed, and the reason matters

This item was listed as "Phase 2, data ready", and the obvious implementation
would have failed it. `Lighting` is a **shared service**: a server that applied
a world's `Environment` on entry would paint that biome onto every connected
player's screen, including people standing in the hub.

So the server never touches `Lighting` at all. It sends the `Environment` table
in `Expedition_Started`, and `ExpeditionController` applies it **on the entering
client only**, restoring a snapshot of the hub's lighting on exit. That is what
makes "never bleeding" true with more than one player on the server rather than
true only in a single-player test.

The failure mode to watch for is the restore, not the apply: if
`ExpeditionController.TRACKED` ever misses a property that
`ChunkLoader.applyEnvironment` writes, that property leaks into the hub and
stays there. The two lists have to be kept in step.
