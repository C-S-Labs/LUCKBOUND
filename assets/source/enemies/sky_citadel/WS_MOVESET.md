# The Winged Sentinel: moveset (v5 duelist)

Fast, precise lance duelist. Every attack is readable (a clear wind-up tell plus a glow cue) and every attack leaves an opening.
The design rule is **fast attacks, short but guaranteed punish windows**. Nothing is unavoidable. Its aerial moves always end
inside sword range, and the player deals all damage (no arena tools).

Timings are at 30 fps. The windows are what the player gets:
- **Tell**: how long before the hit lands.
- **Active**: how long the hitbox is live.
- **Recover**: the punish window. The boss can't act, and hits during it land.

## Phase 1 (armoured, lance closed): about 60% of HP

| # | Move | Tell | Active | Recover | Dodge / counterplay | Notes |
|---|------|------|--------|---------|---------------------|-------|
| 1 | **Dash Lunge** | 12 f (wings flare, visor flash) | 6 f | **24 f** | Side-step; the thrust is a straight line | Bread-and-butter. It overshoots 2 m past the player and ends facing away. |
| 2 | **Twin Thrust** | 9 f, then 7 f | 4 f + 4 f | **20 f** | Back-step twice, or roll through the second thrust | The second thrust has a longer tell (the grip slides back). |
| 3 | **Crescent Sweep** | 14 f (lance drawn back low, blade glows) | 8 f, 200° arc | **28 f** | Jump it, or roll behind | Covers his flank. It's the answer to players hugging his back. |
| 4 | **Wing Vault → Plunge** | 16 f (crouch, wings fold up) | lands on a marked spot, 10 f | **36 f** (lance stuck in the floor) | Leave the ground circle (it shows 16 f before impact) | Airborne under 1 s and lands in sword range. **The biggest P1 opening.** |
| 5 | **Parry Stance** | 8 f (lance vertical, halo spins) | 30 f counter window | **20 f** if nothing hits it | Don't attack. Wait it out, then punish | If the player hits the stance, he ripostes (a lunge with the 12 f tell). Used at most once per 15 s. |
| 6 | **Guard Break Bash** | 10 f (pommel raised) | 5 f | **22 f** | Dodge; blocking does not stop it | Only used when the player blocks 3+ times in a row. |

**P1 combos** (each ends on the listed recovery, never chained into another combo):
- **A: Lunge → Sweep.** He only follows up if the player dodged sideways *toward* him. There's a 6 f gap between the moves.
- **B: Twin Thrust → Vault Plunge.** The vault tell starts immediately, so a player who backed off gets the plunge.
- **C: Lunge ×2.** He re-aims between the lunges (10 f), and the second lunge has the full 24 f recovery.

He's vulnerable to stagger after every 3rd committed attack (a 1.2 s breather: wings droop, glow dims). It's also a free damage window.

## Transition (P2_Transition, 60 f): invulnerable, no damage
- He does a short hover. His armour bursts off at frame 30, and the debris only lands where it's harmless.
- The storm web slides up the blade and is absorbed (f30–44). The halves slide open and the plasma blade ignites (f44).
- After it ends, he stands still for **2 s** (the P2Start marker onward) before attacking: a free damage window to reward the phase push.

## Phase 2 (unarmoured, plasma lance, wings spread): last 40% of HP
He's faster, but his recoveries stay generous. Without armour he takes **+25% damage**.

| # | Move | Tell | Active | Recover | Dodge / counterplay | Notes |
|---|------|------|--------|---------|---------------------|-------|
| 1 | **Blink Lunge** | 9 f | 5 f | **20 f** | Side-step | P1 lunge, faster; a short afterimage trail marks the path. |
| 2 | **Plasma Arc** | 12 f (blade flares) | 8 f, 240° arc, +1.5 m reach | **26 f** | Jump or roll through | The plasma extends his reach, and the recovery grows to match. |
| 3 | **Storm Dive** | 18 f (rises 4 m, wings spread wide) | 3 dives, 8 f each, 14 f apart | **40 f** after the 3rd (grounded, blade in floor) | Each dive is marked on the ground; roll each one | Every dive lands in sword range. **Main P2 opening.** |
| 4 | **Aether Fork** | 15 f (lance raised, cyan arcs crawl up the blade into the plasma) | 3 bolts strike the marked spots, 6 f | **30 f** (he stays still while channelling) | Leave the marks, then run in and hit him | **His own** lightning: cyan with violet cores, fired from the lance tip and curving down, like the storm-web pattern. It's not the Stormhawk scenario's sky strikes, so it works on any map (base chunk kit / original Sky Citadel). The marks are cyan rune circles that show for the whole tell. |
| 5 | **Riposte Stance** | 6 f | 24 f | **18 f** | As P1 Parry | Shorter, but used at most once per 12 s. |
| 6 | **Desperation Flurry** (below 15% HP, once) | 20 f (wings wrap, core glows white) | 5-hit lance flurry, 4 f each | **60 f** kneel, glow out | Back off during the flurry | A long final punish window: the "finish him" moment. |

**P2 combos:**
- Blink Lunge → Plasma Arc (8 f gap)
- Blink Lunge ×3 (each 20 f recovery, only the last gets 26 f)
- Storm Dive → Lightning Fork (only above 50% of P2 HP)

## Fairness rules (apply to every boss)
1. Every attack has a visual tell of at least 8 f **and** an audio cue. No hitbox is live during the tell.
2. Every attack or combo ends in a recovery of at least 18 f. Aerial moves end grounded and in sword range.
3. No attack covers 360° with no gap, and nothing hits the whole arena.
4. There's a pause of 0.5 s or more between strings; he never goes more than 3 attacks without a punish window.
5. Area-of-effect marks show for the whole tell, and the player always has a reachable safe zone.
6. The player does all the damage. There are no arena hazards the player must use.

## Animations to build (Studio actions, all on the existing rig)
- Done: `Idle_Guard` (120 f loop), `P2_Transition` (60 f).
- To build:
  - Phase 1: `P1_Lunge`, `P1_TwinThrust`, `P1_Sweep`, `P1_VaultPlunge`, `P1_Parry` / `P1_Riposte`, `P1_GuardBreak`, `P1_Stagger`
  - Phase 2: `P2_Idle`, `P2_BlinkLunge`, `P2_PlasmaArc`, `P2_StormDive`, `P2_AetherFork`, `P2_Riposte`, `P2_Flurry`, `P2_Kneel`
  - Shared: `Hit_React`, `Death`
- Markers in every action: `HitStart`, `HitEnd`, `RecoverStart`. The Studio combat script reads these for hitboxes and punish windows.

## VFX plan (Roblox Studio)
Everything is self-contained on the boss: no map or scenario dependencies.
Colours are cyan `#7FF6FF` with violet `#9C7BD8` accents; the neon parts (the `*_Glow` meshes) drive the glow.

**How it's built**
- **Attachments:** the rig's socket bones become attachments: `Weapon_R`, the lance tip (`LanceBladeL`/`R` tails), `VFX_Core`, `VFX_Eye`, the wing tips and the feet.
- **Particles and trails:** `ParticleEmitter` and `Trail` / `Beam` objects are parented to those attachments. Trails use two attachments (for example, blade base to tip).
- **Driven by animation markers:** the combat script listens for `GetMarkerReachedSignal("HitStart"/"HitEnd"/"RecoverStart"/"Tell")` and toggles the effects. The effects therefore always line up with the animation, and the tell VFX doubles as the player's warning.
- **Textures:** a small shared texture set (spark, soft glow, streak, ring, rune circle, shard) is used by every Sky Citadel boss and recoloured per boss.
- **Budget:** at most about 150 live particles per effect. Everything is Neon plus particles; no PointLights except the core glow.

**Per category**
| Category | Effect |
|---|---|
| **Tells** | Visor flash (`VFX_Eye`, 3 f), a cyan pulse through the glow parts, and a ground rune for AoE moves. It shows for the whole tell. |
| **Attacks** | Lance `Trail` (cyan to transparent) during the Active frames only. Thrusts get a short streak burst at the tip; sweeps get a curved arc mesh that fades over 8 f. |
| **Impacts** | Plunge/Dive: a radial spark ring plus floor shards plus a quick camera shake (only near the player). Hits on the player: a small spark and a hit-stop of 2 frames. |
| **Movement** | Wing-dash: a feather-shard burst from the wing tips plus a short afterimage (a translucent clone of the body parts fading over 10 f) in P2. Hover: a soft downdraft dust ring. |
| **Openings** | During recovery the glow dims to about 40% and 2�3 slow motes drift off the core, a consistent "he's open" signal on every boss. |
| **Phase 2** | Armour-break burst (the debris parts fly off per the P2_Transition keys), a core flare, the storm web collapsing into the lance, and the plasma ignite. The glow stays brighter from then on. |
| **Defeat** | The glow flickers, then goes out. He kneels, using the lance as a prop, and the wings droop. The glow parts crack into shards. Then a slow cyan upward dissolve (parts fade, particles rise) plus a halo ring expanding and fading. Loot and chest reveal at the end. Total about 4 s; the player can't be damaged during it. |
