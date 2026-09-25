# Sky Citadel enemy roster (base chunk set only)

Rules: basic enemies and minibosses stay under 10k tris each. Bosses can go over, split into pieces of under 10k each.
Weapons are designed separately (bosses get unique weapons after their body is final).
Flyers must regularly come into sword range; the player's weapon is the damage source (no arena tools).

## Basic (10)
1. Gilded Sentinel (close range, a man-sized construct guard). NOT BUILT YET. The 3.5 m model below became Boss 3.
2. Aviary Harrier (close range, flyer: dive, then lands and stalks)
3. Lantern Wisp (close range, low hover: cage swing / ember burst). BUILT: `lantern_wisp.py`, 5.3k tris (body + glow),
   rig Root>Body>Cage(swing)>Flame + 3-bone ember tail; scene x=5
4. Cloud Skirmisher (long range: javelin, then a reload pause)
5. Turbine Drone (clamps to the floor/wall to attack). BUILT: `turbine_drone.py`, 6.3k tris (body + glow),
   rig Hull + 3 spinning rotors + 3 two-bone clamp legs + BladeRing + Lens; scene x=10. TODO: check lens faces front
6. Prism Crawler (long range: slow charged beam, overheats). BUILT: `prism_crawler.py`, 2.8k tris (body + glow),
   rig Body > Prism (aim) + Head + 2 mandibles + 6 legs x 3 bones; scene x=15
7. Archive Scribe (long range / support: stays rooted while channelling)
8. Rootbound Warden (close range, heavy)
9. Spring Eel (medium range, hittable while surfaced)
10. Skyport Hauler (close range, tank)

## Minibosses (3)
- Armory Warden, Orrery Engine, Beacon Keeper

## Bosses (3)
1. The Spire Regent (boss clearing)
2. The Gale Leviathan (skyport / dockside; skim passes -> latched -> crash)
3. **The Winged Sentinel**: BUILT. `winged_sentinel.py` + `ws_lance.py`; scene `scenes/boss_winged_sentinel.blend`; FBX `exports/WingedSentinel.fbx`
   - FAST duelist: wing-assisted dash-lunges; each lunge leaves a punish window. Size ~3.55 m (kept small because it's fast)
   - Palette: dark graphite plate, matte black undersuit, violet trim, pale stone inlays, cyan aether glow
   - Fully rigged: R15-named body + tabard/fauld chains + 4 wing bones + 20 finger bones + Weapon_R / Shield_L / VFX sockets
   - Glow split into its own meshes (`_Glow`, `_BreakawayGlow`, `_LanceGlow`) -> set Neon in Studio and tween colour for the idle pulse
   - Phase 2: `Break_*` debris chunks (Breastplate, SpaulderL/R, ForearmGuardL, TassetL/R, FauldFront/Back) are flung off;
     inner aether core + veins revealed; wings extend. Action `P2_Transition` (60 f @ 30 fps; markers ArmourBreak@30, P2Start@60)
   - Poses: `ws_pose.py` (one-handed lunge-ready, lance couched), `ws_pose_guard2h.py` (two-handed combat guard),
     `ws_pose_idle.py` (guarding the platform, lance planted, both hands on the shaft), `ws_pose_p2.py` (P2 wings extended)
   - Animations exported: `exports/WingedSentinel_Idle_Guard.fbx` (120 f loop), `exports/WingedSentinel_P2_Transition.fbx` (60 f)
   - Phase-2 lance ("fan"): the halo shrinks and draws into the collar as fuel (f30-44); the blade halves, each carrying its
     side blade + feather lug, step out and fan back ~63 deg like wings; the plasma Beam + two energy-web membranes ignite
     (f44, marker LanceIgnite). Clip check: 0 closed, 0 open (incl. vs body). Tried and rejected: hinge / wide jaws
     (halves collide at the base: 358-430 overlaps), slide-apart (0 clips, but reads as broken floating pieces).
     Extra Neck bone added for smoother head turns.
   - Aether Lance: 4.4 m winged partisan (side blades, floating halo, rune fullers); 8.9k + 0.9k glow tris
   - Body 38.2k tris across 16 meshes, each under 10k
   - Poses are Studio-grade: `ws_pose_fix.py` seats the haft in the palm, wraps every finger/thumb (no penetration), places the off hand
     on the shaft by IK (elbow chosen to avoid the body), and grounds the body; P2 debris lands on the floor. Diag: 0 limb/body clips.
   - Moveset: `WS_MOVESET.md` (P1 6 moves, P2 6 moves, combos, punish windows, fairness rules, action list)
   - TODO: attack animations per WS_MOVESET.md; intro cutscene

## Shared scene
`scenes/sky_citadel_enemies.blend`: every Sky Citadel enemy side by side along +X (boss at 0, then +5 per enemy),
each in its own collection. Meshes only (loading rigs into the live session crashes Blender); the rigged
per-enemy files are `scenes/boss_winged_sentinel.blend`, `enemy_lantern_wisp.blend`, `enemy_turbine_drone.blend`.
Shared build helpers: `work/enemies/enemy_kit.py`.

## Build status (2026-09-24): ALL 16 BUILT, first pass
Palette sheet: `work/enemies/SKY_CITADEL_ENEMY_PALETTE.png`. Shared scene: `scenes/sky_citadel_enemies.blend` (line along +X).
| x | Enemy | Tier | Script | Tris (body + glow) |
|---|---|---|---|---|
| 0 | The Winged Sentinel | Boss | winged_sentinel.py + ws_lance.py | 38.2k body + lance, 24 meshes |
| 5 | Lantern Wisp | Basic | lantern_wisp.py | 3.9k + 1.3k |
| 10 | Turbine Drone | Basic | turbine_drone.py | 5.9k + 0.4k |
| 15 | Prism Crawler | Basic | prism_crawler.py | 2.7k + 0.1k |
| 20 | Gilded Sentinel | Basic | gilded_sentinel_basic.py | 7.3k + 0.1k |
| 25 | Aviary Harrier | Basic | aviary_harrier.py | 6.3k + 0.2k |
| 30 | Cloud Skirmisher | Basic | cloud_skirmisher.py | 4.8k |
| 35 | Archive Scribe | Basic | archive_scribe.py | 7.1k + 0.3k |
| 40 | Rootbound Warden | Basic | rootbound_warden.py | ~5.2k + 0.3k |
| 45 | Spring Eel | Basic | spring_eel.py | 3.7k + 1.1k |
| 50 | Skyport Hauler | Basic | skyport_hauler.py | ~5.6k + 0.2k |
| 58 | Armory Warden | Miniboss | armory_warden.py | frame 3.7k + plate 6.4k (P2 shed) |
| 66 | Orrery Engine | Miniboss | orrery_engine.py | 6.8k + 0.6k |
| 74 | Beacon Keeper | Miniboss | beacon_keeper.py | 6.7k |
| 88 | The Spire Regent | Boss | spire_regent.py | 8 pieces, ~10.6k total |
| 112 | The Gale Leviathan | Boss | gale_leviathan.py | 9 pieces, ~14.6k total |
Shared code: `enemy_kit.py` (shapes + assemble), `humanoid.py` (R15 body generator), `render_enemy.py` (headless render).
Minibosses/bosses have finger bones. Weapons are sockets only (Weapon_R etc.) except the Winged Sentinel's lance.
Next passes: detail/refinement per enemy, weapons, animations (only the Winged Sentinel is animated so far).
