# LUCKBOUND — Weapons

**The canonical list of weapon types and the rules every weapon mesh follows.**
Owner-directed 2026-09-23. Before this file the types lived nowhere in the
repo. Anything here that disagrees with a build prompt wins; fix the prompt.

The first batch is **Sky Citadel's**: 7 types × 6 weapons, Common to Epic. The
build prompt is `SKY_CITADEL_WEAPONS_BLENDER_PROMPT.md`.

---

## 1. Types

| Type | Held | Length (studs) | Notes |
|---|---|---|---|
| **Sword** | one hand | 3.6–4.6 | the baseline blade |
| **Greatsword** | two hands | 5.2–6.8 | long grip, heavy guard |
| **Dagger** | one hand | 1.6–2.4 | short, fast, often reverse-grip-friendly |
| **Hammer** | one or two hands | 3.4–5.0 | head ≈ 25–35% of the length |
| **Staff** | two hands | 5.0–6.8 | a focus at the head; the caster weapon |
| **Bow** | one hand (grip) | 4.0–5.2 tall | the string is rigged; arrows are NOT part of the bow |
| **Gauntlets** | worn, a PAIR | 1.8–2.6 cuff to fingertip | two meshes (`_l`, `_r`), one weapon |

A 5-stud character is the reference. 1 Blender metre = 1 stud.

## 2. Rarity — what each tier must SHOW

Common to Epic are generated in batches. **Legendary and Mythic are designed
one at a time, later**, and may be exported in several meshes for their
higher triangle counts. A batch never contains them.

> **Movesets (owner, 2026-09-25):** every weapon carries its own moves as data (`PLAYER_ABILITIES.md` §0). Weapons
> of one type share a base moveset; **Legendary and Mythic weapons get unique movesets**, designed one at a time
> with a moveset sheet like a boss. The move format and fairness rules are `ENEMY_AI.md` §4.

Per type, **2 Common, 2 Uncommon, 1 Rare, 1 Epic**.

Detail and "coolness" rise **deliberately** with rarity. A Common is not ugly:
it is honest, well-made standard issue. An Epic is unmistakable **from its
silhouette alone**, at thumbnail size, in black.

| Tier | Triangle target | Must have | Must not have |
|---|---|---|---|
| **Common** | ≤ 1,200 | a clean, readable silhouette; 2–3 palette colours; alloy and white | glow, gold, anything floating |
| **Uncommon** | ≤ 2,000 | + `SunGold` fittings; one `AzureDim` seam or inlay; a shaped detail (fuller, flared guard, turned pommel) | floating parts |
| **Rare** | ≤ 3,500 | + `AzureNeon` glowing channels; a `SkyGlass` crystal element; a secondary silhouette shape (wings, fins, a halo); **at least one animatable accent** (a spinning core, a ring) | more than 2 floating parts |
| **Epic** | ≤ 6,000 | + `CitadelViolet`; **2 or more floating or orbiting elements** on their own bones; a signature silhouette drawn from citadel motifs (needle spires, halo rings, hex facets, turbine fins) | anything that would read Legendary (see below) |

**Hard cap: 10,000 triangles per mesh.** A weapon over it is not exported; the
build script refuses. For gauntlets, the cap is per hand.

Reserved for Legendary and above, so Epic never cheapens them: **gold used as a
main surface** (not a trim), a weapon that visibly **breaks apart** (a blade
floating in segments), and **full-length particle-style ornament**.

## 3. Style

The house style (`ART_DIRECTION.md`) and the island kit's palette
(`biomes/SKY_CITADEL.md` › *The palette*) are the rules:

- **Low poly, flat shaded.** 6–12 sided cylinders; facets visible; no
  subdivision, no bevel modifiers, no smooth shading.
- **Colour is baked vertex colour** from the kit's palette, the same way
  `build_sky_citadel_kit.py` does it. **No image textures and no
  `SurfaceAppearance`**: they override `Color` in Roblox and fight the style.
- **Violet is not the rarity colour.** `CitadelViolet` rhymes with Epic's
  `#B24BF3`; it does not replace it. Rarity colour belongs to UI and portals.

## 4. Rig — every weapon is rigged, and every moving part is modular

**Each weapon is ONE skinned mesh** (gauntlets: one per hand) **with an
armature**. Anything that could plausibly move, now or later, is built so it
can be animated without remodelling:

1. **Its own closed shell.** A moving piece is never merged, boolean'd or
   welded into its neighbour. It is a separate island of geometry inside the
   mesh.
2. **Its own bone**, from the vocabulary below, with the **same-named vertex
   group**, weighted **100%** (rigid: one bone per vertex, weight 1.0).
3. **Its bone head at its natural pivot**: a hinge, a spin axis's centre, a
   finger knuckle. The bone points along the piece's natural axis of motion.
4. Static pieces are weighted to the nearest structural bone (`Blade`,
   `Shaft`, `Haft`…), never left unweighted.

### Bone vocabulary

PascalCase. Numbered bones start at 1. `Root` is always the first bone, its head
at the **grip point**, which is also the object origin.

| Type | Structural | Animatable | Effect sockets (no geometry) |
|---|---|---|---|
| all | `Root` | `Float_1…n` (detached hovering pieces), `Ring_1…n` (halos, orbiting rings), `Core` (a spinning/pulsing crystal) | |
| Sword · Greatsword · Dagger | `Grip`, `Blade` | `Guard` (crossguard that can flare or spin), `Pommel` | `Fx_Base`, `Fx_Tip` (trail line) |
| Hammer | `Haft` | `Head` | `Fx_Strike` (the striking face) |
| Staff | `Shaft` | `Head` (the crown or cage), `Core` | `Fx_Cast` (where spells leave) |
| Bow | `Grip` | `Limb_Upper`, `Limb_Upper_Tip`, `Limb_Lower`, `Limb_Lower_Tip`, `String_Nock` | `Fx_Rest` (arrow rest), `Fx_Nock` |
| Gauntlets | `Cuff`, `Hand` | two bones per finger, listed below | `Fx_Knuckles` (impact point) |

**Gauntlet fingers** are `Thumb_1/2`, `Index_1/2`, `Middle_1/2`, `RingFinger_1/2`,
`Pinky_1/2`. It is `RingFinger`, not `Ring`, so it never collides with the halo
`Ring_n` bones. Each segment is its own shell; segment 1 pivots at the
knuckle, segment 2 at the middle joint.

**Bow string:** a string in two straight runs, upper tip → nock → lower tip. The
end vertices are weighted to `Limb_Upper_Tip` / `Limb_Lower_Tip`, and the nock
vertices to `String_Nock`, so drawing the bow is moving one bone.

**Effect sockets** (`Fx_*`) are non-deforming bones with no weights. They mark
where code will attach trails, particles and projectiles. Export them: FBX
"Only Deform Bones" must be **off**.

Rigging is the whole brief: **no animations, actions, constraints, IK or drivers**
are authored.

## 5. Orientation, in Blender

- **Origin = grip point** (`Root`'s head). Transforms applied; scale 1.
- The weapon's length runs along **+Z** (tip, head or crown up).
- The striking edge or face points **−Y** (Blender front).
- **Bow:** upright along Z, grip at the origin, string on the **+Y** side, the
  arrow flying toward −Y.
- **Gauntlets:** wrist at the origin, fingers along +Z, knuckles facing −Y. The
  **right** gauntlet is authored; the left is its mirror in X, with bone names
  unchanged (the `_l` / `_r` is on the object, not the bones).

## 6. Names and files

| What | Pattern | Example |
|---|---|---|
| Mesh object | `wpn_<world>_<type>_<rarity>_<letter>` | `wpn_sc_sword_common_a` |
| Gauntlet meshes | `…_<letter>_l`, `…_<letter>_r` | `wpn_sc_gauntlets_epic_a_r` |
| Armature object | `rig_` in place of `wpn_` | `rig_sc_sword_common_a` |
| Future content Id | `<WORLD>_<TYPE>_<SLUG>`, UPPER_SNAKE | `SC_SWORD_AZURE_WARDEN` |
| Display name | Title Case, 2–3 words | *Azure Warden* |

`<world>` is `sc` for Sky Citadel; `<type>` is the singular lower-case type
(`sword`, `greatsword`, `dagger`, `hammer`, `staff`, `bow`, `gauntlets`);
`<rarity>` is `common`, `uncommon`, `rare` or `epic`; `<letter>` is `a`, `b`… per
type and rarity.

| File | Path |
|---|---|
| Generator script | `assets/source/items/weapons/sky_citadel/build_sky_citadel_weapons.py` |
| Blender file | `assets/source/items/weapons/sky_citadel/sky_citadel_weapons.blend` |
| Manifest | `assets/source/items/weapons/sky_citadel/WEAPONS_MANIFEST.md` |
| Exports, one FBX per type | `assets/export/items/weapons/sky_citadel/sky_citadel_<type>.fbx` |

**Export settings:** the island kit's (`CHUNK_AUTHORING.md` › *Export settings*
and *Unit scale*): Forward `-Z`, Up `Y`, Apply Scalings `FBX All`, scale 1.00,
Apply Transform on, mesh + armature only. Plus, for rigs: **Add Leaf Bones off,
Only Deform Bones off, Bake Animation off.** Each weapon at the world origin
when written, whatever the review layout.
