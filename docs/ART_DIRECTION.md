# LUCKBOUND — Art Direction Brief

How to describe the look so it becomes code, and where authored art plugs in later.

---

## The approach

**You describe, I build procedurally, meshes come later.**

Every visual is data in `src/shared/Content/Hub/Crossroads.luau`. `HubBuilder`
reads that data and generates geometry; it contains no art direction at all.
So describing the look is a data edit, not a rewrite.

**The mesh seam.** Every swappable piece exposes an optional `MeshId`. While it
is `nil` the builder generates primitives. Set it to a Roblox asset id and the
builder uses the mesh instead, keeping the same position, scale and pivot:

```lua
FateEngine = {
	-- ...
	MeshId = "rbxassetid://1234567890",  -- ← one line, no other change
}
```

That means your second option — AI-generated or Blender-authored models — stays
open and costs one line *per piece*, whenever you want it. You can replace the
Fate Engine alone and leave everything else as blockout. There is no flag day.

### Why not meshes now

Not a capability limit — a sequencing one. Mesh imports need export, upload,
moderation approval, and asset-id wiring, and AI-generated meshes routinely
arrive with broken scale, pivots or topology. That's a multi-day pipeline whose
output is *prettier blockout*. Phase 1 exists to answer one question: does
pressing ROLL make you want to press it again? Procedural geometry answers it
this week. Your own spec says it: *"It doesn't need to be beautiful yet."*

The one exception worth buying early is the **Fate Engine**. It is on screen for
the entire game and it is the thing the game is named after. If you commission or
generate a single hero asset, make it that one.

---

## What to describe

Answer in plain prose — no need for numbers or colour codes, I'll translate.

### 1. The Crossroads (highest value)

Currently built from Master Spec §3: deep blue/purple sky at dusk, warm gold
lighting, slate platforms, neon runes, floating islands in the distance, five
compass districts around a central plinth.

- What's the **feeling** standing there? Sacred? Abandoned? Busy? Humming with machinery?
- Is it **old** — ruins something else built — or **active** — running right now?
- **Scale**: is the player a visitor in something enormous, or an operator at a workstation?
- Is the sky **empty** or full of something — stars, storms, other islands, distant worlds?
- Time of day, and does it change?

### 2. The Fate Engine ⭐ (most important object in the game)

Currently three counter-rotating gold rings around a glowing purple core on a
stone plinth.

- Is it **machine** (gears, pistons, metal) or **artifact** (stone, runes, magic) or both?
- What does it do **at rest**? Idle spin, pulse, hum, dormant until approached?
- **What happens when you roll?** This is the single most valuable thing you can describe. Does it wind up? Charge? Tear open? Go silent first?
- What does a **Common** roll look like versus a **Mythic**? Different colour, more rings, a different sound, screen shake?
- Does the player **enter** it, or watch it?

### 3. The reveal moment ⭐⭐ (the whole game, per §25)

Right now: screen dims, world names flash past, then scramble into symbols as it
accelerates, then a card fades in with rarity, world name and flavour text. Total
wait is `RollBuildupSeconds` + the rarity's own reveal duration — 3.7s for a
Common, 6.7s for a Mythic.

- Should the build-up be **tense** (slow, quiet, dread) or **exciting** (fast, loud, building)?
- When does the player **suspect** it's rare — early (colour shifts as it builds) or only at the end (identical until the last frame)?
- On a Mythic: does the world **stop**? Screen shake? Everything go white? Sound cut out?
- Does the result feel like a **prize** (celebratory) or a **destination** (ominous, you're going somewhere)?
- After the card: should they be **dropped straight in**, or choose when to enter?

### 4. The three biomes (Phase 2 — describe later)

Verdant Valley, Emberfall and Astral Reach are worlds you *enter*, and entering
isn't built yet. Their environment data (`Environment = { AmbientColor, FogColor,
FogEnd, ClockTime }`) is already wired, so lighting and atmosphere land as soon
as you describe them — but geometry, props and enemies are Phase 2 work.

Worth describing **after** you've played the roll loop, not before.

---

## What I'll do with it

Your description becomes edits to `Theme` and the district/engine tables, plus
tween curves and timing in `src/client/UI/FateRoll.luau`. Then you `rojo serve`,
look at it, and tell me what's wrong. That loop is fast — most changes are
numbers.

If you connect the **Studio MCP locally** (see `docs/TOOLCHAIN_ACCESS.md`), a
local agent can also screenshot the result and iterate on the look without you
describing every adjustment in words.

---

## Current defaults, for reference

| Thing | Current value |
|---|---|
| Sky / atmosphere | `#1B1740` top, `#3D2E6B` horizon, dusk at ClockTime 20.5 |
| Key light | Warm gold `#F5C97B` |
| Stone | `#5B5470`, Slate material |
| Runes | Cyan `#8FD4FF`, Neon |
| Crystal / core | Purple `#A97BE8`, Neon |
| Gold accents | `#D9A441` |
| Fog | `#2A2350`, 180 → 1100 studs |
| Central platform | 62-stud radius cylinder |
| Districts | 120 studs from centre; Observatory at +58 height |
| Fate Engine | 54 studs tall, 3 rings spinning 0.25 / −0.40 / 0.62 rad/s |
| Floating islands | 14, deterministic from seed 20260915 |
| Reveal timing | Common 3.7s → Mythic 6.7s total |
