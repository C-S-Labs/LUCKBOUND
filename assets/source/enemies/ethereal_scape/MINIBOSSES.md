# Ethereal Scape minibosses: DRAFT work orders (2026-09-30, nothing built)

Step 1 of `docs/ENEMY_FRAMEWORK.md` §1 (roster/design draft). **Every move, timing and number here is a proposal for owner review.** Nothing is modelled. Contract: `docs/BOSS_ANIMATION_VFX.md`; stagger/parry: `docs/ENEMY_AI.md` §10.1.

**Tier rules (framework §2):** up to 35k tris total, every mesh under 10k, R15 plus finger bones, socket or simple unique weapon, 1-2 phases, own moveset sheet with 4-5 moves, actions = Idle/Move/attacks/Hit/Stagger/Death plus stance actions. Fairness minimums: 8 f tell plus audio, 18 f recovery, 3-attack limit, 0.5 s between strings, no 360° without a gap, reachable safe zone. Design language (`ROSTER.md`): temple-ivory and gold breaking into sky crystal at the extremities, gold slit masks, mint/teal ribbons, hovering over stomping, no hood, halo only as a rare accent.

**Arena facts (`docs/biomes/ETHEREAL_SCAPE.md`):** one miniboss per map, at the end of a branch, never the boss arena. Waystone and Reliquary have their own arena pieces; the Gatewarden stands at either Temple Gate (the only `COMMUNION` exits).

Build order for each: roster OK -> body (`--validate`) -> rig -> poses -> moveset sheet -> actions -> export. Create `<id>.py` plus `manifest.py` entry, `<NAME>_MOVESET.md`, `anims/<id>/`.

---

## 1. Waystone Sentinel (Waystone Ring arena) · id `waystone_sentinel`
**Fantasy:** a squat rune waystone given a body: slow, heavy, a brute that draws power from the eight waystones of its ring. Archetype `brute` plus miniboss sheet.
**Body:** broad ivory-and-gold torso, crystal-fractured shoulders and fists, a gold ring (halo-like accent, allowed here) floating behind the head, a slit mask. Slow lumbering stance, hovering a hand above the floor. ~28-34k tris. No cape.
**Moves (draft, T/A/R at 30 fps):**
| Move | T/A/R | Idea |
|---|---|---|
| Waystone Slam | 24 / 8 / 36 | overhead two-fist slam; marked impact footprint, one spark ring |
| Ring Sweep | 20 / 10 / 30 | gold ring swings out in one arc; safe flank visible |
| Beacon Pulse | 30 / 12 / 40 | channels; two waystones light with a ground line; narrow beam along each marked line, one safe lane |
| Stone Step | 18 / 6 / 28 | short committed shoulder charge, stops in melee range |
**Phase 2 (below ~50%, optional):** ivory plate sheds (`Break_*`), crystal core exposed, pulse gains a third line (never covering the whole arena); damage-taken modifier per the owner's usual sheet value. **Stagger:** meter-based (large/brute model, `ENEMY_AI.md` §10.1); slow drain.
**Prototype:** Waystone Slam end to end.

## 2. Reliquary Keeper (Reliquary Court arena) · id `reliquary_keeper`
**Fantasy:** guards the relics; punishing if approached carelessly (a counter-puncher). Humanoid, robed, carries a reliquary lantern on a staff (staff-class weapon, simple unique).
**Body:** slender ivory robe with a front slit, gold mask, crystal hands and hem, mint ribbons, lantern with a portal core. Small cloth (robe only, via `cloth_core`). ~26-33k tris.
**Moves (draft):**
| Move | T/A/R | Idea |
|---|---|---|
| Lantern Bolt | 20 / 6 / 30 | one slow mint bolt from the lantern, own lifetime contract |
| Relic Ward | 14 / 24 counter window / 24 | a visible guard stance; hits during it are punished by a **boss counter** (distinct from the player parry), cue differs from recovery, answer with a gap |
| Reliquary Rain | 30 / two 8 f waves / 36 | marked crystal columns in two labelled groups, safe lane survives both |
| Staff Rebuke | 12 / 5 / 26 | short close-range jab when approached |
**Phase 2 (optional):** relics float around her and fire one extra bolt per Lantern Bolt, never overlapping with the rain. **Stagger:** agile model (parry opens a short window) plus hidden meter.
**Prototype:** Lantern Bolt plus Relic Ward (proves the counter cue).

## 3. Gatewarden (either Temple Gate) · id `gatewarden`
**Fantasy:** the common obstacle before the Sanctum; **two skins, one archetype** (Gate A / Gate B palettes). A tall armoured temple guard with a polearm: the baseline melee duelist of the world. Humanoid, ivory-and-gold plate, crystal gauntlets, slit mask.
**Body:** more layered plates than a basic, narrow tabard (no cape), polearm (Spear-class, socket or simple unique). ~24-32k tris plus a second recolour (vertex colours / material set, no second mesh).
**Moves (draft):**
| Move | T/A/R | Idea |
|---|---|---|
| Gate Thrust | 14 / 6 / 24 | straight spear thrust, short committed advance |
| Sweeping Guard | 18 / 8 / 28 | low-to-high sweep, safe flank |
| Portcullis Drop | 24 / 8 / 36 | leap-and-plant, marked footprint, ends in sword range |
| Two-Step Combo | 12, 10 / 5+5 / 30 | thrust then sweep, second tell at least 8 f |
**Phase 2:** none (one phase). **Stagger:** agile model.
**Prototype:** Gate Thrust plus the Two-Step Combo.

---

## Open questions for the owner
1. Approve the three concepts, move lists and the phase choice (1 or 2 phases each) before any body is modelled.
2. Weapon: Waystone Sentinel fists only; Keeper's staff and Gatewarden's polearm as sockets (shared) or simple unique meshes?
3. Does the Gatewarden's second skin need a distinct silhouette detail, or palette only?
4. These minibosses' damage-taken and stagger numbers come from simulation (`ENEMY_AI.md` §10.1), not this draft.
