# The Crossroads, rebuilt (2026-09-23)

The hub was out of date: the biomes' detail had outgrown it. This version was
built from scratch around the **Fate Engine**, and uses the Engine's design as
its guide. The Engine itself (`HUB_FATE_ENGINE`) is **untouched**. It stays
its own prefab, placed at the centre as before.

`build_crossroads_hub.py` builds everything. `renders/` holds the review shots,
taken with the real Engine placed at its in-game scale.

```
blender -b --factory-startup --python build_crossroads_hub.py -- --export --render --save
```

## Design

- **The Engine sets the language.** The hub uses the Engine's palette as
  painted in game: basalt, pale marble, gold trim, cyan inlay, and violet and
  rose shards. It also repeats the Engine's 16-fold radial rhythm, and its
  idea of stone held up by light: every deck floats on a stepped basalt keel
  over a hanging crystal core, the Engine's levitation stack inverted.
- **Layout (studs, north = Roblox −Z).**
  - A 16-sided plaza, radius 118, which covers the spawn ring at 105.
  - Four bridges, 24 wide.
  - Four district decks, radius 80, centred 218 from the Engine.
  - A promenade ring joining the districts, with a beacon overlook on each
    diagonal.
  - Overall about 600 studs across, the same footprint as before.
- **Districts.** Each one opens toward the hub and onto the ring.

| Mesh | Where | What |
|---|---|---|
| `HUB_HALL_OF_CHAMPIONS` | north | a colonnade with banners, a stage with five champion obelisks, two statues, a floating laurel crown |
| `HUB_ARCHIVES` | east | a teal domed rotunda, shelves of books, an orrery on a lectern, drifting open books |
| `HUB_SHOP` | south | six market stalls round a tiered fountain, a floating coin, banner masts, an entrance arch |
| `HUB_TRAINING_GROUNDS` | west | a sand yard, sparring ring, dummy stands, braziers, weapon racks, targets, a watchtower, a gong |

## Pieces

Each is **one mesh under 10k triangles**. Exact counts and bounding boxes are
in `assets/export/hub/crossroads/crossroads_layout.json`.

| File | Meshes |
|---|---|
| `crossroads_hub.fbx` | `HUB_PLATFORM` (7.6k), `HUB_HALL_OF_CHAMPIONS` (4.6k), `HUB_ARCHIVES` (8.0k), `HUB_SHOP` (4.9k), `HUB_TRAINING_GROUNDS` (5.0k). All in **hub coordinates**, so they assemble where they land. |
| `crossroads_hub.fbx` (also) | `HUB_LEVITATOR` (2.9k): under the plaza, a cradle, a great crystal heart and eight thrusters, with conduits out to every district. It is what keeps the whole hub in the sky. |
| `crossroads_animated.fbx` | **79 `anim_*` meshes** (6.2k tris in all), in hub coordinates: every part that moves, split out of its host mesh the way the Sky Citadel props are. Each one's `anim` (Spin / Bob / SpinBob / Flicker) and `host` are in the layout JSON. They include: beacon shards, keel cores and rings, obelisk crystals, the crown, halo and heart, the oculus crystal, the orrery (a sun plus three rings, each carrying its planet), the floating books, the coin and fountain rings, the thruster flames, the three gyroscope rings, and **every ware for sale**. |
| `crossroads_backdrop.fbx` | `HUB_BACKDROP_PEAKS`, `_MESA`, `_SPIRES` (3.4–3.7k each), 390–720 studs tall, to be cloned round the hub |
| `crossroads_orbiters.fbx` | 12 `hubprop_*`: three small isles (shrine, grove, ruin), airship, skiff, two clouds, crystal cluster, rune ring, sky lantern, sky whale, waystone |

The hub pieces are the same in every server. The backdrop and orbiters are
placed at random by the server.

## Shop wares

Each stall sells its own line, four items per counter, and every item is an animated mesh (`anim_ware_<kind>_<n>`):

| Stall | Line |
|---|---|
| 1 | potions |
| 2 | weapons: sword, staff, bow |
| 3 | gems |
| 4 | scrolls and tomes |
| 5 | armour: helms, shields |
| 6 | charms and rings |

## Checks

`build_crossroads_hub.py` runs a clipping scan every build (`CLIP CHECK`). No
moving part may touch a static mesh or another moving part. The count is 0.

## Gameplay anchors

`crossroads_layout.json → anchors` lists named points in Blender coordinates,
where Roblox = (x, z, −y):
- a prompt spot for each district
- the five obelisks
- the three dummy stands and the boss dummy stand
- the six market stalls, the fountain and the orrery
- the four overlooks

The **dummies themselves** are still built by the game; the mesh only has
their stands.

## Import

1. In Studio's 3D Importer, import each FBX (hub, animated, backdrop, orbiters), keeping the object names. Use the
   same settings as the Sky Citadel kit: no parent empties, 1 unit = 1 stud.
2. Save as follows:
   - the hub → `assets/rbxm/prefabs/HUB_CROSSROADS_V2.rbxmx`
   - the animated parts → `assets/rbxm/prefabs/HUB_ANIMATED.rbxmx`
   - the backdrop → `assets/rbxm/prefabs/HUB_BACKDROP_V2.rbxmx`
   - the orbiters → `assets/rbxm/props/HUB_ORBITERS.rbxmx`
3. Then the wiring follows: HubBuilder places the five pieces from the layout,
   clones the backdrop round the hub at random, and drifts the orbiters.
   `GameConfig.HubLayout.ZoneRingRadius` moves from 200 to 218.
