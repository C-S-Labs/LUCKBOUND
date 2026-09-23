# Sky Citadel weapons — Blender build prompt

**What this is.** A prompt to paste into **Claude Code in a terminal, opened at
the root of this repo, with the Blender MCP connected**. It builds Sky
Citadel's first weapon batch: **7 types × 6 weapons = 42** (48 meshes, since
gauntlets are pairs), Common to Epic, rigged, and exported the way the island
kit is.

**Why a terminal session rather than this one.** The Blender MCP talks to the
Blender running on the owner's machine, so the session doing the building has
to run there too. It also has the repo, so the prompt can point at the docs
instead of restating them. `WEAPONS.md` is the contract; this prompt is how to
meet it.

**What it deliberately does not do.** No game code, no content files, no
Roblox import, no animations, no commits. It builds, rigs, validates and
exports, then stops for the owner to review in Blender.

---

## How to run this

1. Open Blender with the MCP add-on running, and a terminal at the repo root.
2. Start `claude` there, and check the Blender MCP tools are listed.
3. Paste everything between the `COPY FROM HERE` and `COPY TO HERE` markers.

The session stops after the swords for your review, then does the other six
types.

---

# ─── COPY FROM HERE ───

You are building weapons for **LUCKBOUND**, a Roblox game, in the Blender that
is connected through the Blender MCP. You are in the game's repo. This is a
modelling and rigging task only.

## 0. Read these first. They are the rules, not background

In this order, and properly, before writing any code:

1. **`docs/WEAPONS.md`**: THE contract. Types, sizes, the rarity ladder,
   triangle caps, the rig and bone vocabulary, orientation, names, file paths,
   export settings. If anything below seems to disagree with it, it wins.
   Tell me about the disagreement.
2. **`docs/biomes/SKY_CITADEL.md`**: the world these weapons come from. Read
   *The look*, *The palette* and *The set-dressing vocabulary*. The weapons
   must look like they were forged in that citadel.
3. **`docs/ART_DIRECTION.md`**: *Style*, *No built-in Roblox materials*,
   *Colour is applied in code, not baked in* and *Rarity colours*. Low poly,
   flat shaded; the rarity colour is not a paint colour.
4. **`docs/CHUNK_AUTHORING.md`**: *Unit scale*, *Export settings* and *Lay the
   kit out so it can be seen*.
5. **`assets/source/worlds/sky_citadel/build_sky_citadel_kit.py`**: read it,
   **do not modify it**. It is how this project builds geometry in Blender
   with Python: the `PALETTE` (use those exact RGB values and names), the
   primitive helpers (`box`, `frustum`, `crystal`, `torus`, `half_barrel`),
   `to_object` (how faces become flat-shaded meshes with baked vertex
   colour), `_export_selected` and `verify_exports`. Your script should feel
   like its sibling. You may copy helpers into your own script; do not import
   from or edit the kit's.

## 1. What to build

**Seven types, six weapons each: Sword, Greatsword, Dagger, Hammer, Staff, Bow,
Gauntlets.** Per type: **2 Common, 2 Uncommon, 1 Rare, 1 Epic**. Gauntlets are
a pair: two meshes (`_l`, `_r`) per weapon.

**Do not build Legendary or Mythic.** Those are designed separately, later.
Keep their tricks off the Epics: gold as a main surface, a weapon floating
apart in segments, full-length particle-like ornament (`WEAPONS.md` §2).

### The creative brief

Be creative. The rules exist so your creativity lands in the game unchanged,
not to design the weapons for you.

These are the arms of a **white, machined sky-castle held up by nothing**:
octagonal and chamfered, not round and organic. Seamed with **azure light**.
Gold used **sparingly**, on collars, caps and finials. **Violet** for the proud
pieces. **Things that float on purpose.** Draw from the citadel's own motifs:

- needle spires with a glowing band and a floating halo;
- hex and octagon facets;
- halo rings that orbit nothing;
- turbine fins and gatehouse chevrons;
- crystal bipyramids;
- the keel that tapers to a point and touches nothing.

A Sky Citadel greatsword might have a guard like a gatehouse lintel; a staff
might carry a tiny orrery; a bow's limbs might be two tapering needle spires.
Those are examples, not assignments.

**Every weapon must be distinct.** Six swords are six ideas, not one sword in
six colourways. Vary the silhouette first, then detail, then colour.

**Rarity must be obvious, on purpose** (`WEAPONS.md` §2 has the exact ladder):

- **Common** is honest, well-made standard issue of the citadel guard. Clean
  and good-looking, never ugly, never cheap.
- **Uncommon** adds gold fittings, one azure seam, and a shaped detail.
- **Rare** adds glowing channels, a glass crystal, a secondary silhouette
  shape, and at least one animatable accent.
- **Epic** adds violet, two or more floating or orbiting elements, and a
  signature silhouette you would recognise in black at thumbnail size.

Line the six up and the step from each tier to the next should be felt, not
squinted at.

Give each weapon a **display name** (Title Case, 2–3 words, evocative, of
the citadel: *Azure Warden*, *Keelbreaker*) and a **future content Id**
(`SC_<TYPE>_<SLUG>`, UPPER_SNAKE). Both go in the manifest (§6).

## 2. Hard rules

- **Scale: 1 Blender metre = 1 Roblox stud.** Before anything else, place a
  reference box **2 × 1 × 5 m** (x × y × z) at the origin named
  `SCALE_REF_CHARACTER`, a 5-stud character. Keep it in the review scene; it is
  never exported. Sizes per type are in `WEAPONS.md` §1.
- **Low poly, flat shaded, triangle budgets** per `WEAPONS.md` §2. **Hard cap
  10,000 triangles per mesh.** Your script must refuse to export a weapon over
  it.
- **Colour:** only the kit's `PALETTE` colours, baked as vertex colour the way
  `to_object` does it, and a material slot per palette colour. **No image
  textures, no UV work, no procedural shaders.** You may add palette entries
  only if a weapon truly needs one; name them in the kit's style and list
  them in your report.
- **Orientation and origin** exactly as `WEAPONS.md` §5: the origin at the grip
  point, the length along +Z, the business side toward −Y. Transforms applied.
- **Names** exactly as `WEAPONS.md` §6. A `.001` suffix anywhere is a bug:
  your script is not idempotent.
- **Files** exactly where `WEAPONS.md` §6 says. Create the folders.

## 3. The rig — modular, named, ready to animate later

Read `WEAPONS.md` §4 again; it is the part that is easiest to get subtly
wrong. In short:

- Each weapon is **one mesh** (gauntlets: one per hand) parented to **one
  armature** with an Armature modifier. Bone names come **only** from the
  vocabulary in `WEAPONS.md` §4; vertex group names equal bone names.
- **Anything that could plausibly move gets its own bone and its own closed
  shell of geometry**, never merged into its neighbour:
  - a guard, a pommel;
  - a hammer head;
  - a staff's crown and its core;
  - bow limbs and their tips, and the string's nock;
  - every gauntlet finger segment;
  - every floating shard, halo or ring.

  The bone head sits at the piece's **natural pivot**: its hinge, its spin
  centre, its knuckle. It points along the piece's natural axis of motion.
  Build the geometry so it could rotate about that pivot without clipping
  through its neighbours.
- **Rigid weights:** every vertex belongs to exactly one vertex group, weight
  1.0. Static geometry goes to its structural bone; nothing is unweighted.
- **Effect sockets** (`Fx_Tip`, `Fx_Base`, `Fx_Strike`, `Fx_Cast`, `Fx_Rest`,
  `Fx_Nock`, `Fx_Knuckles`) are non-deforming bones with no vertex group,
  placed exactly where a trail, impact or projectile should start.
- The bow string runs in two straight segments. Its ends are weighted to the
  limb tips and its middle to `String_Nock` (`WEAPONS.md` §4).
- The **left gauntlet mirrors the right** in X, with the same bone names.
- **Rig only.** No animations, no actions, no poses left applied, no
  constraints, no IK, no drivers, no shape keys. Leave every armature in rest
  pose.

## 4. How to work

- **Write one generator script** at
  `assets/source/items/weapons/sky_citadel/build_sky_citadel_weapons.py`, and
  run it inside Blender through the MCP. Do not model by hand: the numbers,
  names and pivots have to be exact and re-runnable.
- One builder function per weapon, grouped by type. A `main()` builds, rigs,
  validates, lays out, exports and saves, in that order.
- **Idempotent:** re-running replaces what it made, and never leaves `.001`s.
- **Deterministic:** a seeded `random.Random(name)` if you use randomness at
  all, so a rebuild is identical.
- **Build type by type.** After each weapon, read the scene back through the
  MCP and report real numbers: its triangle count, its dimensions, its bone
  list, and the vertex count per bone. Report what Blender actually contains,
  not what the script intended. A silent no-op looks like success until
  someone opens the file.
- **Look at your work.** After each type, take viewport screenshots through the
  MCP: the six in a row beside `SCALE_REF_CHARACTER`, and the Epic close up.
  Judge them against the brief before moving on. Also pose-test each
  animatable bone once: rotate it ~30° about its natural axis in pose mode,
  screenshot, and **reset it to rest**. Moving pieces must not tear the mesh or
  clip their neighbours.

## 5. Layout for review, and export

- One collection per type (`Weapons_Swords`, `Weapons_Greatswords`, …, and
  `Weapons_Gauntlets`), laid out in a row per type, Common → Epic, left to right,
  with clear gaps (`CHUNK_AUTHORING.md` › *Lay the kit out so it can be seen*).
  Put the review offset on something that is not exported, or move each
  weapon to the origin for export and back.
- **Export one FBX per type** to
  `assets/export/items/weapons/sky_citadel/sky_citadel_<type>.fbx`, containing
  that type's meshes and armatures, **each at the world origin**. Use the kit's
  export settings plus the rig ones in `WEAPONS.md` §6: **Add Leaf Bones off,
  Only Deform Bones off, Bake Animation off.**
- **Verify every export by re-importing it** into a throwaway collection, as
  the kit's `verify_exports` does, and check:
  - the mesh and armature counts;
  - every mesh within its type's size range and at or under 10k triangles;
  - every expected bone name present;
  - no `.001`s.

  Delete the throwaway collection afterwards.
- Save the Blender file to
  `assets/source/items/weapons/sky_citadel/sky_citadel_weapons.blend`, with the
  review layout and `SCALE_REF_CHARACTER` in it.

## 6. Validation — the script refuses to export on any failure

Before export, for every weapon mesh (gauntlets: each hand):

- the name matches `WEAPONS.md` §6, with no `.001`;
- triangles ≤ 10,000 (refuse), and within the tier's target (warn, and
  justify in the report if over);
- all faces flat shaded; no modifiers except Armature; no shape keys; no
  animation data;
- the vertex colour attribute is present, and every colour is a palette
  colour;
- the origin is at the grip; the length is along +Z and within the type's range;
- the armature is present and in rest pose; every bone name is in the
  vocabulary; the required bones for its type are present;
- every vertex is in exactly one vertex group at weight 1.0; every group name
  is a bone; every deforming bone has vertices; no `Fx_` bone has vertices;
- **modularity:** each animatable bone's vertices form one or more closed
  shells that share no vertex with another bone's shells;
- the tier rules hold:
  - Common: no emissive palette colours, no `SunGold`, no `Float_`, `Ring_`
    or `Core` bones;
  - Rare: at least one of `Core`, `Ring_n` or `Float_n`;
  - Epic: at least two `Float_n` or `Ring_n` bones, and uses
    `CitadelViolet`.

Then write **`assets/source/items/weapons/sky_citadel/WEAPONS_MANIFEST.md`**: one
row per weapon with the object name(s), future Id, display name, type,
rarity, triangles, dimensions, bones, the palette colours used, and a
one-line design note.

## 7. What you must NOT do

- Do not create or edit **any file** other than the generator script, the
  `.blend`, the seven FBXs and the manifest. That means nothing in `src/`,
  `docs/`, `tests/`, the kit script, or any content file.
- Do not import anything into Roblox, write any Luau, or wire weapons into
  the game.
- Do not author animations of any kind.
- Do not build Legendary or Mythic weapons.
- **Do not commit or push.** The owner reviews in Blender first.

## 8. Checkpoints

1. After reading §0, reply with a short plan:
   - your reading of the brief;
   - a one-line concept for each of the six **swords** (name, rarity, the idea);
   - your bone list for a sword and for a bow.

   Wait for my OK.
2. Build, rig, validate, export and screenshot the **six swords**. Report
   them with the real numbers and screenshots, then **stop and wait** for my
   review. I may send changes; apply them before continuing.
3. Then build the other six types in this order: Greatsword, Dagger, Hammer,
   Staff, Bow, Gauntlets. Report after each (numbers plus screenshots) and
   carry on unless I stop you.
4. Final report:
   - every file written, with its path;
   - the manifest table;
   - every warning and any palette additions;
   - anything in `WEAPONS.md` you found unclear or had to interpret.

# ─── COPY TO HERE ───
