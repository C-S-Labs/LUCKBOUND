# Crossroads V2 refinement: sky ecosystem and hub contract

Orchestrated task `crossroads-v2-refinement` (owner brief, 2026-10-05). This is the shared contract every worker
packet points at. It settles the design so workers make none. It is an enhancement of the CURRENT Crossroads, not a
redesign. Experimental: nothing here reaches `main` without the owner's review.

## 0. Frozen: the Fate Engine

Nobody touches the Fate Engine: not `assets/rbxm/prefabs/HUB_FATE_ENGINE.rbxmx`, not its placement in
`HubV2`/`HubBuilder`, not `FateSystem`, `FateRoll`, `FateEngineMenu`, `FateHud`, `FateCore`, nor the Engine's
dais ring `RESERVE_R`/`EngineCentre` anchor semantics in the platform source. The platform mesh (`HUB_PLATFORM`) may
be edited only at the four bridge junctions and for its own secondary detail; nothing inside `RESERVE_R + 8`.
If something seems to need Engine work, STOP and report to the orchestrator.

## 1. Current system (as inspected)

- Hub art: `assets/source/hub/crossroads/build_crossroads_hub.py` (generator, authoritative with
  `crossroads_hub.blend`) -> FBX in `assets/export/hub/crossroads/` + `crossroads_layout.json` ->
  `make_layout_luau.py` -> `Content/Hub/CrossroadsV2.luau`. Roblox meshes are UPLOADED via Studio's 3D Importer by the
  owner and saved as `assets/rbxm/**.rbxmx` (there is no headless uploader). Any new or changed mesh therefore ends at
  an OWNER GATE: workers deliver Blender source + FBX + sidecar data; they never touch `.rbxmx`.
- Bridges (`build_platform`, ~L293): `Walkway` box from `PLAZA_R-3` (115) to the district; plaza top z=0 and
  bridge top z=0 are coplanar, with the bridge buried 3 studs inside the plaza; the plaza is a 16-gon of
  circumradius 118. Open item in STATUS: "Staircase clipping at the walkway junctions". `check_walkways.py` exists.
- Sky: `HubV2.buildSky` places `HUB_ORBITERS` props with `Wander*` attributes; client `SkyTraffic.luau` flies them
  (waypoints, speed drift, turn-rate limit `speed/radius`, look-ahead spherecast, mutual clearance, docking).
  Ship docking uses `GameConfig.HubLayout.V2.Docking`, `CanDock`, `PropCore.berthOnBox`, tests near
  `tests/cases.luau:9693-9740`.
- Sub-animation paradigm (keep it): a body MeshPart `hubprop_<id>` plus hinged rigid sub-MeshParts named
  `hubprop_<id>__<part>_<n>`, with `Kind` Spin | Flap | Flicker, `Hinge`, `Axis`, `Amp`, `Rate`, `Phase`, emitted into
  `Content/Hub/CrossroadsV2.luau` `OrbiterParts` by the layout pipeline. The sky whale (`hubprop_sky_whale`, 84 studs,
  1.9k tris, flippers/fluke/spout) is the craftsmanship reference and STAYS UNCHANGED.
- Authoring orientation (same as the whale and ships): head/nose along **+X**, up **+Z** in Blender; FBX settings as
  the existing export; `SkyTraffic` applies the importer's quarter-turn. Do not invent another orientation.

## 2. Shared visual contract

LUCKBOUND hub language: basalt, pale marble, gold trim, cyan inlay, violet/rose/cyan crystal shards; low-poly, flat
shaded, vertex-coloured by the existing material table in the build script (reuse its palette names; add a new
palette entry only if a species needs it, in that species' own script). Every creature = a LUCKBOUND body plan
(crystal growth on spine/back, gold or marble accents, glowing inlay/eyes) plus a SUBTLE biome accent:
Verdant Valley (moss, leaf, bark, flower), Emberfall (ash, ember-orange glow, charred plates), Sky Citadel (marble
armour, gold trim, banners), Ethereal Scape (pearl, translucent fins, violet twilight), Astral Reach (star-glass,
prismatic facets). Not one mascot per biome; accents vary, cohesion stays.

## 3. Roster (decided; 10 designs, plus the retained whale)

Scale = longest body dimension (studs) after build. Tri budget: every mesh < 10k (hard rule); creature totals below.

| id | class | biome accent | size | total tris | notes |
|---|---|---|---|---|---|
| `skyfinch` | TINY | Verdant | 3-4 | <=900 | songbird; wings, tail; flits, perches |
| `lumen_moth` | TINY | Ethereal Scape | 4-6 | <=1000 | broad pearly wings, glow inlay; soft erratic drift |
| `cinderkite` | SMALL | Emberfall | 9-12 | <=1800 | slim raptor, ember tail streamers; glider |
| `prism_darter` | SMALL | Astral Reach | 10-14 | <=1800 | star-glass dragonfly, 4 wings; hover and dart |
| `citadel_falcon` | MEDIUM | Sky Citadel | 24-30 | <=3500 | marble-armoured raptor, gold trim; stoop and glide |
| `canopy_drake` | MEDIUM | Verdant | 28-36 | <=4000 | leaf-finned drake: wings, neck, tail chain; can land |
| `aether_manta` | LARGE | Ethereal Scape | 80-100 | <=5000 | translucent-finned manta; slow wing-beat undulation |
| `ashen_roc` | LARGE | Emberfall | 90-110 | <=6000 | great ember-lit bird: wings (2-segment), tail, head |
| `starweaver` | COLOSSAL | Astral Reach | 520-700 | <=30000 | jelly-like celestial: pulsing bell, halo ring, chained tendrils |
| `elder_greatturtle` | COLOSSAL | Verdant | 560-760 | <=32000 | island-backed sky turtle: grove on shell, 4 paddles, head, breath |

Existing `hubprop_sky_whale` (LARGE, 84-134 studs) is kept as a living member of the sky.
Colossals are multi-part (<=12 meshes per creature, each < 10k tris), more detailed than the whale per unit size,
move deliberately, fly far out and rarely.

## 4. Technical contract

### 4.1 Authoring and sidecar (creature workers)

Each creature worker owns a NEW folder `assets/source/hub/crossroads/creatures/<group>/` and writes ONLY there plus
its own export files. They reuse (read-only) the helpers of `build_crossroads_hub.py` by `runpy` (see
`check_walkways.py`), and MUST NOT edit that file, `crossroads_layout.json`, `crossroads_orbiters.fbx` or the
existing `.blend`. Deliverables per group:

- `creatures/<group>/build_<group>.py` (headless via `python tools/run_blender.py -b --factory-startup --python ...`),
  producing review renders (scratch, not committed except one contact sheet per group under `creatures/<group>/renders/`)
- `assets/export/hub/crossroads/creatures_<group>.fbx` (one body + sub-parts per creature, each at its own origin,
  pivot = body centre, head +X)
- `assets/export/hub/crossroads/creatures_<group>.json`, exactly:

```
{ "group": "<group>", "creatures": { "<id>": {
    "model": "hubprop_<id>", "class": "TINY|SMALL|MEDIUM|LARGE|COLOSSAL",
    "size": [x, y, z],              // studs, body bounding box, Blender axes already mapped like the whale layout
    "tris": N, "biome": ["VERDANT", ...],
    "parts": { "hubprop_<id>__<part>_<n>": {
        "kind": "Flap|Spin|Flicker|Pulse", "offset": [x,y,z], "hinge": [x,y,z], "axis": [x,y,z],
        "amp": rad, "rate": hz_or_radps, "phase": rad,
        "chain": "<other part name or null>",   // hinge parent: this part's motion composes on it (tail/neck/wing-tip)
        "lag": rad,                              // phase lag behind its chain parent
        "gait": "Always|Flight|Idle|Turn"        // when it animates (see 4.3)
    } } } } }
```

Offsets/hinges are in body-local space exactly as the existing `OrbiterParts` (same maths as `part_of`).
Animation coverage expected per anatomy: wing beat (2-segment wings where the species has big wings), tail chain,
head/neck motion, body undulation by chained segments, breathing (`Pulse`), glow `Flicker`.

### 4.2 Runtime data (traffic worker)

- New content file `src/shared/Content/Hub/SkyCreatures.luau`: species table (model, class, size, parts, biome,
  `CanLand`, weight) plus a generator `tools/gen_sky_creatures.py` that merges the `creatures_*.json` sidecars (and the
  whale's existing `OrbiterParts` entry) into it. Validated by `Util/Schema` at boot (server refuses to start on bad data).
- New tunables in `GameConfig.HubLayout.V2.SkyLife`: per-CLASS behaviour profile (data, no per-species code):
  population (`Min`/`Max`, `Detail`), orbit band (`RadiusMin/Max`, `HeightMin/Max`), `Speed`, `Accel`, `TurnRadiusScale`,
  `MaxBank`, `HubClearance` (horizontal keep-out radius about the hub axis) and `OverheadMinY` (minimum height above the
  deck when inside that radius), `CloseApproach` frequency, `SeparationScale`, `UpdateHz` (distance-based throttle),
  `ActivationRadius`. Guidance (tunable): TINY/SMALL may cross the hub at >= 40 studs over the deck and come within a
  few dozen studs of the player; MEDIUM keep-out ~ hub radius + 80; LARGE ~ +260 and slow turns; COLOSSAL orbit radius
  2200-3200, never inside 1800 of the hub, 1-2 present at a time, rare (long respawn/absence cycles).
- New pure module `Core/FlightCore.luau` (`--!strict`, testable headless): heading-rate-limited kinematics where
  velocity ALWAYS equals heading * speed (no sideways translation, no instant yaw), speed reduction before tight turns,
  bank from lateral acceleration, class profiles, keep-out tests, perch state machine
  (`fly -> approach -> land -> perch -> takeoff -> fly`). Random via owned `Random`, never `math.random`.
- `SkyTraffic.luau` becomes the thin client driver over `FlightCore`: waypoint choice per class band, look-ahead
  against the real hub meshes (kept), separation scaled by both radii, sub-part animation drivers for the four `Kind`s,
  `chain`/`lag`, `gait` modulation (flap rate rises with speed and climb, glide intervals, idle breathing while perched,
  banking), distance-based update throttling and early-out for far colossals. Landing: species with `CanLand` pick perch
  points on backdrop islands (raycast top surface, `PropCore.berthOnBox` may be reused for rim geometry), never
  colossals, never near the hub. Keep future riding open: each flyer keeps a stable root `BasePart` + `Mount` attribute
  placeholders are NOT added (no saddle work); just do not weld or destroy the body/part structure.
- Boat removal: delete the five small-ship, galleon/carrier entries from `Orbiters`, the `Docking` block,
  `CanDock`/berth/dock code and dock tests, once replaced. Keep clouds, isles, crystals, rune ring, lantern, waystone
  entries and all reusable traffic code. Keep the boat meshes in `HUB_ORBITERS.rbxmx` and the generator functions
  (AGENTS cleanup rule: recommend deletion only after Studio proves the replacement). Record any now-unread
  declaration in `docs/RESERVED.md` or delete it.
- `HubV2.buildSky` spawns creatures from `SkyCreatures` + `SkyLife` instead of boat groups; missing models (not yet
  imported) are skipped with a single warning so the hub still boots before the owner's import.

### 4.3 Animation gaits

`Always` continuous; `Flight` wing/tail cycle whose rate scales with speed and climb and which pauses into glides on
a per-class schedule; `Idle` breathing/tail flick while perched or hovering; `Turn` additional lean/tail swing with
bank; `Thrust` (round 2) a Pulse part's burst train tied to acceleration and speed. Mass cue: tiny = fast shallow beats, colossal = very slow deep beats, turning radii and accelerations by class.

### 4.4 Hub geometry worker

Owns `build_crossroads_hub.py` hub pieces (not the `prop_*` generators, which stay), `check_walkways.py`,
`make_layout_luau.py`, `crossroads_hub.blend`, `assets/export/hub/crossroads/crossroads_hub.fbx`,
`crossroads_animated.fbx`, `crossroads_layout.json`, `Content/Hub/CrossroadsV2.luau` (regenerated, only the hub
pieces and anchors may change). Tasks, in order: (1) diagnose the four bridge/plaza junction overlaps with evidence
(headless; renders at each junction + numeric overlap/coplanarity report); (2) repair so each junction looks
constructed (seated landing, collar/threshold trim, no coplanar overlap, rails/gateposts/spine meeting the plaza curb
deliberately), without moving Engine, plaza radius or walkable heights by more than 0.05; (3) walkable-surface and
clipping audit with `check_walkways.py` and `check_buried_parts.py`, fix confirmed defects only; (4) restrained
secondary detail refinement (trim, supports, rail caps, lamps, banners, underside detail, vegetation) per the owner
brief: nothing that clutters the plaza, no change of silhouette/layout/navigation. Budget: each mesh < 10k tris.
Deliver before/after renders (contact sheet) and a written findings report. Studio re-import is an owner gate.

## 5. Acceptance (orchestrator checks)

- Fate Engine untouched (`git diff` shows no path from section 0).
- Boats no longer spawn; no dock code remains; whale and non-boat orbiters unchanged in behaviour.
- Every flyer's body heading equals its velocity heading (unit test over FlightCore for each class and tight turns).
- Keep-out per class holds in a headless sweep of many seeds; colossals never inside their radius.
- All Luau tests pass (`tests/run.sh` if `luau` exists), StyLua clean, `tools/gen_index.py` current, Rojo build ok if rojo present.
- Creature sidecars validate: tris budgets, mesh < 10k, naming, orientation (head +X), sizes in class range.
- Studio-dependent checks (import, visual, collision, performance) are listed as MANUAL and are the owner's gate.

## 6. Round 2 amendment (owner Studio test, 2026-10-05) - SUPERSEDES earlier colossal/animation rules where it conflicts

Owner findings from a Studio run: starweaver and turtle spawn super far away and clip into islands; tendrils barely
move and the bell does not respond to acceleration; medium/large birds and the drake raise their wings and do not beat
them incrementally, their other limbs never move, and they slide through the air; the manta's fins are detached from
its body; overall the creatures feel robotic. Owner decisions:

1. COLOSSALS: pool grows to 4 species (existing starweaver, elder_greatturtle + 2 new, below). A server ALWAYS has at least
   1 colossal present and never more than 3 (replaces the old rare/absent presence cycle; a colossal may still leave and be
   replaced, but the floor of 1 is never broken). They are meant to be SEEN: orbit band much closer than 2200-3200 (target
   closest approach 600-1400 studs, visible and imposing from the hub) and they MAY fly over the central hub (at an altitude
   that clears the deck by their own extent) and around it.
2. PATHFINDING: colossals (and all classes) plan around existing islands: backdrop islands AND the far range, and every
   other body, as obstacles (bounding spheres/boxes inflated by the creature's own radius). The route is chosen around
   them with smooth, wide turns; if a leg is blocked a new waypoint is chosen before it arrives. No clipping into any
   island, far-range mountain, the hub or another creature (check starweaver at ~700 studs wide).
3. ANIMATION FEEL (all creatures): layered, non-metronomic, mass-appropriate motion:
   - wing beats asymmetric (fast downstroke, slower upstroke), per-wing tiny phase/amplitude noise, glide intervals with
     wings partly folded or held, flare on landing and takeoff; body heave/pitch locked to the beat (lift on downstroke);
   - body roll into turns, tail follows through the turn with delay (follow-the-leader), neck and head counter-move and look
     toward the turn; legs/feet tuck in flight and extend when landing; breathing always on;
   - jelly-like creatures pulse their bell in thrust bursts tied to acceleration/speed and trail tendrils with real lag;
   - slow, deep, long-period motion for colossals; fast shallow for tiny.
   Anything the animation needs that the meshes do not have (separate legs/feet/jaw/ears/crest parts, extra chain
   segments) is a MODEL change by the art workers, within the 10k-per-mesh and class tri budgets.
4. NEW COLOSSALS (decided): `cinder_wyrm` (Emberfall: a vast sinuous ash-and-ember sky serpent, 700-900 studs long, 14+ chained
   body segments undulating with lag, two pairs of small ember fins, jaw, crown of spines, glowing seams) and `aether_nautilus`
   (Ethereal Scape: a colossal pearl nautilus with a chambered translucent-look shell, trailing tentacle chains, a jet funnel
   that thrusts in pulses, drifting fin halo; 520-700 studs). Same quality bar as the whale/starweaver; each <=12 meshes,
   each < 10k tris. Their own group `colossal2`, sidecar `creatures_colossal2.json`, FBX `creatures_colossal2.fbx`,
   library file `HUB_CREATURES_COLOSSAL2` (add to `SkyLife.CreatureLibraries`).
5. MODEL FIXES: the manta's fins attach to the body (no gap; hinge at the body edge, overlapping root). Every creature's
   wing/limb hinge, axis, amp, rate, chain, gait is audited with a pose preview (Blender frames of the rig at several phases
   using the SAME hinge maths as `SkyTraffic.hingeAbout` and the chain rule `acc = parent.acc * hinge`) so the data is proven
   before the owner re-imports.
6. Existing sidecar rules stand (frame key, Pulse = scale fraction, names `hubprop_<id>__<part>_<n>`). Re-exports keep part
   names stable where possible so the owner's re-import overwrites the same file.

## 7. Round 3 amendment (owner Studio test 2, 2026-10-05) - SUPERSEDES §6 where it conflicts

1. COLOSSALS: exactly ONE per server (floor 1, ceiling 1; it may be replaced by another species over time, never zero or two).
2. COLOSSAL SPAWN/ROUTE: colossals must NOT spawn or linger over the hub. They spawn at the outer part of their band at a random bearing and
   travel the open lanes BETWEEN islands, UNDER the hub and OVER it at the planned overpass altitude. Small/medium may still cross the hub.
3. ISLANDS: the surrounding backdrop islands grow with distance from the hub (scale factor rises with radius, so the far ones are huge)
   and are SPREAD OUT with real gaps: wider radial band, minimum spacing, and vertical staggering so lanes exist below, beside and above the hub.
   The look from the hub must stay good. All parameters in `GameConfig.HubLayout.V2.Backdrop`; the planner's obstacle inflation follows the new sizes.
4. SERPENT / EEL LOCOMOTION (new data-driven mode, any creature may use it): sidecar creature field `spine = {"parts": [ordered part names, root
   segment first], "wavelength": studs, "amp": studs, "rate": Hz, "plane": "lateral"|"vertical"}`. The body root (head) is the leader. Segments are NOT
   hinge-chained sines: each segment is placed on the trail the head has actually travelled (follow-the-leader, spacing from the part Offsets), with a
   travelling lateral wave added perpendicular to the path (amplitude growing toward the tail). The HEAD itself sways and yaws/pitches with the
   wave, so the whole body flows like a snake or an eel and the head moves with the body. Fins attached to segments inherit that segment's pose.
   Turning makes the body follow the arc. Used by `cinder_wyrm` (spine over its `body_a_*` segments).
5. SELF-CLIP LIMITS (new system): every moving part may carry `limit = [min, max]` radians (hinge-angle range, same sign convention as the driver).
   The driver clamps (soft) to it. The art-side tool `tools/gen_part_limits.py` (Blender BVH sweep) computes, per Flap part, the largest swing that keeps
   the part from intersecting the body mesh or any non-chained part, over the chain's combined swing, and writes `limit` into the sidecars. Starweaver
   tendrils must never whip up through the bell; tendril motion is also calmer: lower amp/rate and heavily damped inertia (no sporadic whip).
6. TURTLE: the shell does NOT pulse or change size (remove its Pulse; keep limbs, head, tail, isle/grove sway, crystals flicker). Same rule for any
   creature mass that is a landmass or shell: no breathing scale on rigid shells.
7. WING POWER: lifting costs energy. Wing stroke amplitude, depth of the downstroke and body heave scale with the class's lift effort: MEDIUM and LARGE
   birds/dragons beat visibly harder and more dramatically than TINY/SMALL (bigger amplitude, stronger downstroke, bigger body heave and pitch, larger
   rise per beat; tiny stay quick and fluttery with small amplitude). Class profile data, no per-species code. Realism over rate: bigger = slower beat but much
   deeper/stronger; gliding between bursts for LARGE.
