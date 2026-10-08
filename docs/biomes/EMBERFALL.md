# Emberfall — world design direction

## Current production authority — 2026-10-08

17 frozen AreaI sources (Batch1 nine + Batch2 eight), continuous settlement and Castle B/A
structural blockouts are accepted. Consolidation preserves them; normal runtime registration
and AreaII modular-production remain unimplemented. [Production handoff](../../assets/source/worlds/emberfall/PRODUCTION_HANDOFF.md)
owns exact source/mapping/checkpoint paths. [AreaII plan](EMBERFALL_AREA_II_PRODUCTION_PLAN.md)
at079882b is approved planning authority; exact production cuts/contracts/budgets remain proposals.
Progression: Burned Plains → outer wall → settlement → inner-wall transition → one selected
complete castle finale. B is architectural baseline with enclosed boss/reward rooms;
A is its catastrophic-impact derivative with broad shallow arena. Entire castle is one
oversized logical finale unit. No extra AreaIV playable region is implied.
~20 minutes is overall session including finale; exact deadline behavior remains HOLD.
Existing720-second runtime metadata is not changed. Older STOP/area proposals in evidence
are dated history; production implementation requires a separate task.


The **Rare** fire-consumed world for LUCKBOUND.

This document is the design source of truth for the Emberfall rebuild. It supersedes the previous volcanic-wasteland direction while preserving the technical lessons and requirements that remain useful.

> **DESIGN RESET — owner-directed.**
> The existing Blender Emberfall scene is a prototype and learning artifact, not visual authority. Reuse useful assets, scene organization, flora, rock modules, traversal/seam work, and technical lessons where they fit the new direction. Do not preserve terrain or compositions simply because they already exist.

> **DO NOT RESUME THE OLD BUILD FROM ITS CURRENT VISUAL FOUNDATION.**
> Establish the new area design and references first. The next Blender pass should rebuild toward this document rather than trying to progressively “green” or soften the old volcanic scene.

---

## 0. Quick summary

**Tagline:** *A living region being consumed from the inside out.*

Emberfall is a once-vivid temperate region undergoing an **active supernatural invasion and burn event**. The event began deep within the world, around the eventual boss/source region, spread through the castle/stronghold and inhabited land, and is now reaching the outer plains where the player enters.

The player therefore travels **against the direction of spread**:

**newest damage at the opening → older/heavier destruction → overtaken civilization → source of the disaster**

The opening must immediately communicate two truths at the same time:

1. this was recently a healthy, vivid landscape;
2. it is being destroyed **right now**.

Emberfall is **not** a desert, generic volcanic wasteland, lava field, basalt delta, or landscape recovering from an old wildfire.

---

## 1. Design lock

### 1.1 Locked world identity

Treat these points as locked unless the owner explicitly reopens them:

- **Rarity:** Rare world.
- **Grounded world rule:** continuous land; never floating islands over a void.
- **Core premise:** formerly vivid temperate land being actively consumed by a supernatural fire/invasion.
- **Direction of spread:** boss/source → castle/stronghold → inhabited region → outer plains.
- **Player direction:** outer plains → civilization → stronghold → source.
- **Disaster state:** active and advancing, not historical and not ecological recovery.
- **Opening identity:** partially surviving grassland currently being burned through.
- **Progression:** environmental destruction intensifies as the player approaches the source.
- **Verticality:** desirable, but primarily through natural rolling landforms, valleys, ridges, roads, walls, terraces, and later architecture rather than constant jagged volcanic shelves.
- **Scenery:** surrounding land must continue beyond the modular route and reinforce the active area.
- **Orange/emissive rule:** fire, embers, heat seams, and supernatural corruption are accents and escalation signals, not the base color of every surface.
- **Visual storytelling:** surviving landscape and civilization must show what Emberfall was before the invasion.

### 1.2 Intentionally unresolved

Do not prematurely lock these while Area I is being established:

- exact total path length;
- exact chunk count per area;
- final names for later areas;
- whether the middle progression is village → castle, another inhabited district → castle, or a related structure;
- final boss arena form;
- exact world weight / roll tuning;
- final lighting values;
- exact vertical step magnitude;
- exact amount of generated versus manually authored surrounding scenery;
- final alternate boss-route logic;
- specific implementation method for simplified collision beneath detailed terrain.

The next design effort should solve **Area I first** rather than designing the entire world at equal detail.

---

## 2. Reference hierarchy

### 2.1 Primary visual target — Area I

The refreshed Emberfall reference folder should contain the newly approved **Burned Plains** image as the primary visual authority for the opening.

That image owns:

- broad temperate grassland scale;
- an active advancing burn front;
- predominantly dry, burned, and freshly charred terrain;
- limited but unmistakable surviving green;
- burned and partially surviving trees;
- smoke distributed through the landscape;
- fences / countryside remnants;
- long sightlines;
- a distant stronger source of destruction;
- the feeling that the player has arrived while the catastrophe is still spreading.

**Adjustment from the generated reference:** its remaining healthy greenery should be reduced further. The target is approximately **half to two-thirds less healthy green than the initial generated version**, replacing that area primarily with dry grass, freshly scorched vegetation, blackened ground, and transitional burn states.

### 2.2 Reference priority rule

For Area I, the new Burned Plains reference **overrides the previous Emberfall volcanic references** wherever they conflict.

Old references may only be retained for narrowly useful details that still fit this document, such as:

- specific rock forms;
- smoke behavior;
- firelight;
- ruined architecture;
- later-area destruction;
- individual material ideas.

They must not re-establish the old ash-desert / volcanic-wasteland composition.

### 2.3 Later references

Do not lock detailed references for later areas yet. Gather them when that area is being designed.

The broad world sequence is enough for now:

1. Area I — Burned Plains / opening countryside
2. Area II — inhabited/civilized region
3. Area III — castle/stronghold
4. Area IV — source / boss region

---

## 3. World narrative expressed through environment

The environmental progression should explain the disaster without requiring exposition.

The invasion originates at the deepest point of the run and spreads outward. Distance from the source therefore roughly corresponds to **how long an area has been exposed**.

At the outer edge, the player sees fire arriving.

Closer in, the player sees what sustained exposure does.

Near the source, the original environment may be almost completely overwhelmed.

This produces a natural visual gradient:

**healthy remnants → stressed/drying land → active burn → fresh char → long-exposed destruction → supernatural source**

This gradient is not a rigid shader blend. It should appear through terrain, vegetation, structures, smoke, fire, props, silhouettes, and landmark density.

---

## 4. World progression — current high-level plan

### 4.1 Area I — Burned Plains

**17 frozen playable sources are authored; see the production handoff for accepted source/export evidence and runtime limits.**

The player enters through formerly vivid open countryside just as the invasion reaches it.

The area should feel broad, exposed, windswept, and recently alive. It contains the strongest contrast between surviving Emberfall and the advancing disaster.

See §5 for the full Area I specification.

### 4.2 Area II — settlement inside the outer wall

The approved continuous macro blockout includes outer-wall arrival, village, market,
streets/terraces, inner wall and castle approach. Preserve its640×1005-stud composition.
It is a blockout reference, not a modular kit; do not slice or resize it during consolidation.
Heavier fire damage, civic/cultivated remnants and increasing architectural importance
retain the approved grounded-disaster identity. Exact district boundaries and interfaces
are subject to the approved AreaII planning/proof gates.

### 4.3 Selected complete castle finale

Shared inner-wall transition leads into one castle. Variant B is the damaged/burning
architectural baseline with enclosed final-boss and reward chambers. Variant A is the
same structure after catastrophic impact, preserving actual-B correspondence and its
broad shallow arena. Entire selected castle is one special logical finale chunk,
unrestricted by ordinary256-square or former boss-arena limits. Internal visual/collision
packages do not become independently selected rooms. No castle geometry changes here.

### 4.4 Catastrophe and session pacing

The catastrophe/source story belongs within the selected finale; an additional AreaIV
playable region is not an active requirement. Overall session target is approximately20
minutes including traversal, combat, exploration, looting and finale. Exact timer and
A reward provision remain owner decisions; do not infer walking quotas or rescale content.

---

## 5. Area I — Burned Plains

### 5.1 Area fantasy

A beautiful open countryside is losing a race against an advancing supernatural fire.

The player should not interpret the area as:

> “This place burned down.”

The intended read is:

> “This place is burning down.”

The landscape must preserve enough of its previous identity that its destruction is visible.

### 5.2 Visual balance

Use the following as a **composition target, not a per-chunk quota**:

- **15–25% healthy/surviving green**
- **25–35% dry, yellowed, stressed, or partially singed vegetation**
- **50–60% freshly burned / charred / actively burning terrain**

These states should form irregular fronts and pockets rather than evenly mixed noise.

Healthy green should be **localized and meaningful**:

- terrain the fire has not reached yet;
- a protected side of a ridge;
- damp or low ground;
- vegetation behind a stone wall;
- a small surviving field;
- isolated trees or shrubs just outside the burn front.

Avoid broad uninterrupted green carpets. The area is already being lost.

### 5.3 Burn-state language

Area I should contain several readable stages:

1. **Untouched / nearly untouched**
   - vivid but restrained green grass;
   - small flowers;
   - healthy leaves;
   - intact countryside details.

2. **Heat-stressed**
   - faded green;
   - pale yellow-green;
   - dry tan grass;
   - curling leaves;
   - sparse smoke or heat discoloration.

3. **Actively burning**
   - localized flame fronts;
   - orange embers;
   - burning shrubs / fallen branches / fence sections;
   - smoke;
   - fresh blackening.

4. **Freshly charred**
   - black grass stubble;
   - dark exposed soil;
   - ash;
   - skeletal shrubs;
   - smoking trunks;
   - glowing embers used selectively.

5. **Early supernatural takeover**
   - restrained fissures or ember veins;
   - unnatural heat where ordinary wildfire alone would not explain it;
   - limited corruption pointing toward the deeper source.

The opening should emphasize states 2–4. State 5 increases toward the exit into the next area.

### 5.4 Fire-front rule

Fire should have **direction**.

Do not scatter identical burning patches randomly across every chunk.

The player should be able to read that destruction is moving outward from deeper Emberfall. Across a sequence of chunks:

- the entry side may retain more surviving countryside;
- the route crosses increasingly recent burn lines;
- smoke and char become denser;
- fire fronts become more frequent;
- supernatural evidence becomes stronger toward the interior.

Individual chunks can contain local exceptions, but the run-level trend must remain clear.

### 5.5 Terrain language

The Burned Plains are **grassland first, damaged terrain second**.

Preferred macro forms:

- rolling hills;
- shallow valleys;
- broad slopes;
- low ridgelines;
- natural drainage cuts;
- raised meadows;
- occasional exposed rock faces;
- old roads or field tracks;
- modest escarpments;
- overlooks with long sightlines.

The terrain should not default to:

- repeated basalt shelves;
- angular volcanic islands;
- caldera-like bowls;
- huge fractured plates;
- dune-like ash mounds;
- constant black rock fields.

Fire changes the **surface condition** before it changes the entire geology.

### 5.6 Meso-scale terrain detail

The previous prototype correctly identified the need for meso-scale structure, but Area I needs a different vocabulary.

Useful meso features include:

- shallow erosion cuts;
- worn roadside banks;
- exposed soil where vegetation burned away;
- collapsed field edges;
- small rocky shoulders;
- creek/drainage channels;
- root-exposed slopes;
- broken retaining walls;
- low ledges;
- localized ground subsidence near supernatural heat;
- irregular burn boundaries following terrain.

Do not solve empty space by filling it with random rock clusters.

### 5.7 Countryside remnants

Area I should communicate that this was a lived-in landscape before major architecture appears.

Useful elements:

- wooden fences and stone field walls;
- gates;
- dirt roads / worn paths;
- milestones or markers;
- drainage ditches;
- small bridges;
- abandoned carts or farm equipment where stylistically appropriate;
- isolated foundations;
- small shrines / way markers;
- ruined sheds or watch structures;
- field boundaries;
- occasional cultivated-looking plant remnants.

These should support the landscape rather than turn the opening into the settlement area.

### 5.8 Tree language

Trees are a major storytelling tool.

Mix:

- surviving healthy trees;
- trees with one side scorched;
- partially defoliated trees;
- actively burning trees used sparingly;
- freshly blackened trunks;
- skeletal dead trees deeper into the burn.

Avoid making every tree a uniformly black spike.

Tree condition should help show the direction and recency of the burn.

### 5.9 Flora language

The old five-stage flora concept remains useful, but the emphasis changes.

Area I flora progression:

1. **healthy temperate flora**
2. **heat-stressed / drying flora**
3. **singed / partially burned flora**
4. **freshly charred flora**
5. **early supernatural corruption**

“Invasive volcanic growth” should not dominate the opening. Save stronger alien/corrupted growth for deeper areas unless a small amount is needed to foreshadow the source.

Palette anchors can include:

- healthy natural greens;
- dirty olive;
- the pale yellow-green region around `#bdbc42`;
- straw / dry tan;
- scorched brown;
- charcoal black;
- ash gray;
- restrained ember orange/red.

### 5.10 Fire, embers, and molten material

Area I is **not a lava biome**.

Most orange should come from:

- active grass/brush fire;
- burning wood;
- embers;
- fresh supernatural seams;
- distant fire fronts.

Open molten material should be rare this far from the source.

A chunk does **not** need orange emissive geometry to read as Emberfall. Char patterns, smoke, damaged vegetation, fire direction, and environmental storytelling should carry much of the identity.

Where supernatural fissures appear:

- keep them relatively narrow;
- integrate them into damaged ground;
- avoid giant empty cavities with orange lines;
- use them as evidence that this is more than an ordinary wildfire.

Their scale and frequency can increase in later areas.

### 5.11 Smoke and atmosphere

Smoke should reinforce both depth and active spread.

Use:

- thin local smoke from fresh burn patches;
- heavier columns from larger fires;
- distant haze obscuring deeper Emberfall;
- warm light locally near fire;
- cooler/desaturated ambient light elsewhere.

Do not blanket the entire opening in opaque gray fog. The broad plains and distant landmarks need readable sightlines.

### 5.12 Landmark strategy

Area I needs memorable silhouettes without turning into a rock garden.

Possible landmark families:

- a lone partially burned large tree;
- a broken field wall crossing a slope;
- a farmhouse/shed ruin;
- a scorched windbreak or tree line;
- a shallow stream or bridge that interrupted the fire;
- a burned hill crest;
- an old road marker;
- a distant tower/castle silhouette;
- a localized supernatural rupture;
- a large dead tree visible across multiple chunks.

Landmarks should help orient the player and hint at the route toward civilization/source.

### 5.13 Verticality

Retain Emberfall's verticality target, but express it naturally.

The opening can climb through:

- rolling hills;
- valley crossings;
- sloped roads;
- terraces created by old fields;
- shallow ravines;
- broad ridges;
- occasional rock cuts.

Avoid making every elevation change a jagged cliff or volcanic shelf.

The existing approximate **48–64 stud overall ascent range** remains a useful target where compatible with the modular layout, but visual quality and traversal should determine the final value.

### 5.14 Route guidance

Do not use visible guard rails or obvious artificial edge strips.

Guide the player through:

- road remnants;
- fence/field-wall alignment;
- slope direction;
- burn fronts;
- safe openings between active fires;
- tree lines;
- terrain framing;
- landmarks;
- sightlines toward deeper destruction;
- future enemy placement;
- lighting contrast.

The intended feeling remains:

> “I could physically go elsewhere, but the world clearly suggests the route.”

### 5.15 Area I escalation

Area I itself should have a beginning, middle, and end.

**Opening edge**
- clearest surviving grassland identity;
- some healthy pockets;
- mostly dry/freshly burned damage;
- relatively little supernatural geology;
- distant smoke/fire establishes the threat.

**Mid-plains**
- healthy pockets shrink;
- charred fields dominate;
- more damaged fences/trees;
- active fire fronts cross the landscape;
- more evidence of abandonment;
- occasional supernatural seams appear.

**Interior edge / transition**
- little healthy land remains;
- smoke is heavier;
- burning/charred material dominates;
- first stronger signs of supernatural takeover;
- civilization becomes more visible ahead;
- the next area should feel like a continuation of the same disaster, not a biome swap.

---

## 6. Grounded-world and scenery rules

### 6.1 Continuous land

**Hard rule:** Emberfall is not a floating-island map.

All playable layouts must read as part of a much larger landmass. Outward-facing boundaries must never reveal “the map ends here.”

For Area I, surrounding scenery can include:

- continuation of rolling fields;
- distant burned hills;
- tree lines;
- smoke columns;
- field walls / roads;
- distant structures;
- deeper blackened regions;
- castle/stronghold silhouettes where composition allows.

### 6.2 Scenery should tell the same burn story

The scenery ring must not be generic filler.

It should contain the same gradient of:

- surviving land;
- dry land;
- active burn;
- char;
- deeper destruction.

This is especially important for long sightlines across the plains.

---

## 7. Terrain and collision production rules

### 7.1 Visual terrain versus traversal surface

Detailed visual terrain does **not** need to define the exact walk surface.

Recommended production rule:

- visual terrain may contain richer surface breakup;
- playable walking collision may be simplified beneath it;
- combat spaces remain broad and reliable;
- small burned debris, roots, charred stumps, fissure lips, and visual cuts should not make traversal noisy unless intentionally designed as obstacles.

### 7.2 Invisible safety boundaries — inherited owner requirement (2026-09-30)

Every playable chunk needs invisible player-collision boundaries along exposed platform and walkway sides, following local floor height and accompanying its parent chunk at every yaw and elevation. Initial height is **64 studs above the supporting walking surface**.

Leave all actual socket mouths, bridges, doorways, and traversable approaches clear. Backdrops need no boundaries; enclosed rooms use their solid walls. Camera queries explicitly exclude the boundary geometry. Any future animated visual identification is a separate noncollidable prop; the collision wall remains fixed.

This safety contract does not justify floating islands, visible edge strips, or arbitrary walls across walkable routes. Terrain, landmarks, and sightlines still provide visual guidance.

Main provides generic `Boundary` schema/runtime support under build spec §7.7. Emberfall's production boundary data, full kit/connection schema, and Studio validation remain pending. See the shared map requirement in `../MODULAR_MAPS.md`.

### 7.3 Socket and modular-layout preservation

The rebuild must preserve the established modular-world requirements:

- authored socket compatibility;
- clean traversable joins;
- chunk rotation/yaw support;
- elevation-aware boundaries;
- no scenery or props blocking socket mouths;
- surrounding land that disguises the modular footprint.

Do not sacrifice reliable joins for visual continuity. Solve both deliberately.

---

## 8. Later-area fire / fissure escalation

The old lava rules are retained only as **later-area guidance**, not as the identity of Area I.

As the player approaches the source, Emberfall may progressively introduce:

1. ember / heat seams;
2. supernatural fissures;
3. small exposed molten pockets;
4. narrow channels;
5. contained basins;
6. deeper ravines with molten material;
7. major source-region molten features.

Frequency and scale should correlate with proximity to the source.

Avoid:

- a lava pool in every chunk;
- thin orange strips painted into oversized holes;
- glow as the only source of biome identity;
- turning every area into a volcanic cave/field.

If a cavity contains molten material, the material should convincingly occupy the feature and interact with surrounding crust/rock.

---

## 9. Civilization progression

Civilization should become more prominent as the player moves inward.

### Area I

Use sparse countryside evidence:

- fences;
- field walls;
- roads;
- markers;
- small structures;
- foundations;
- carts / tools where appropriate;
- distant architecture.

### Area II

Built space becomes a major part of navigation and storytelling.

### Area III

Architecture becomes dominant enough to define silhouettes and traversal, while the invasion visibly overwhelms it.

### Catastrophe within the selected finale

Remaining architecture expresses the source/catastrophe within the selected castle, not an additional playable area.

The transition must be gradual enough that the world feels like one region.

---

## 10. Boss direction

The existing **Cinder Colossus** remains a viable flagship boss concept, but its final role should be reevaluated when the source/boss area is designed.

Desired existing read worth preserving:

- large;
- iconic;
- connected to Emberfall's destructive force;
- visually appropriate for the deepest, most consumed part of the world.

Do **not** let the current boss concept force the opening back into a volcanic biome.

Alternate boss-route logic remains optional/future-facing until the area progression is better defined.

---

## 11. Anti-drift rules

Emberfall should **not** become:

- a desert with occasional plants;
- a gray ash plain with orange cracks;
- a pure volcanic wasteland;
- a basalt-deltas biome;
- a red-everywhere hellscape;
- a lava pool in every chunk;
- a field of repeated angular rock shelves;
- a landscape recovering from an old wildfire;
- a lush green biome with a few burned decals;
- a clean medieval town with fire added afterward;
- an industrial forge/factory unless later lore explicitly requires it;
- a world whose identity disappears when emissive orange is disabled.

### Critical visual test

With flames and emissive materials temporarily hidden, Area I should still read as:

> **a recently vivid countryside being actively destroyed**

through:

- burn boundaries;
- dry-to-charred vegetation;
- damaged trees;
- blackened fields;
- smoke residue;
- broken countryside features;
- surviving green pockets;
- directional environmental damage.

If it instead reads as a desert, volcanic plain, generic wasteland, or healthy meadow, the foundation is wrong.

---

## 12. Implementation order

The next production effort should proceed in this order:

1. **Reference reset**
   - remove obsolete opening-area references that reinforce the volcanic-wasteland direction;
   - install the approved Burned Plains image as the primary Area I reference;
   - retain old images only if they have a clearly documented later-area/detail role.

2. **Area I design acceptance**
   - confirm Burned Plains terrain language;
   - confirm green/dry/char balance;
   - confirm fire-front direction;
   - confirm countryside prop language;
   - confirm opening → interior escalation.

3. **Fresh Blender foundation**
   - preserve useful technical organization/assets;
   - rebuild terrain/composition toward the new Area I brief;
   - do not attempt to cosmetically convert the old volcanic scene.

4. **Area I prototype review**
   - evaluate from assembled overview, top view, baseline player eye, raised player eye, and representative close-ups;
   - explicitly test whether the scene reads as grassland being actively consumed rather than desert/volcanic terrain.

5. **Only after visual acceptance**
   - finalize collision approach;
   - perform Studio walk/collision testing;
   - validate boundaries, joins, traversal, and runtime behavior.

6. **Then design Area II**
   - repeat the area-by-area design process rather than extrapolating the entire remaining world automatically.

### Explicit warning

Do **not** spend a large orchestration pass designing or rebuilding Areas II–IV before Area I is accepted.

The current goal is to establish the correct Emberfall foundation once, then carry that visual logic inward.

---

## 13. Working one-sentence brief

> **Emberfall is a Rare grounded world where the player enters a once-vivid temperate countryside at the moment a supernatural fire invasion reaches it, then travels inward through progressively older and more severe destruction—toward overtaken civilization, a fallen stronghold, and ultimately the source of the catastrophe.**

---

## 14. Area I foundation review — 2026-10-05

The fresh Blender study is `E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend`.
Three connected 256-stud compositions demonstrate opening, active-burn mid-plains
and interior edge. All visible terrain is rebuilt as rolling grassland; the old
live scene is preserved in `Input_DesignReset.blend` and remains historical.

Whole-land surface classification is approximately **18% surviving, 31% stressed,
51% charred**; individual compositions intentionally differ. Player travels +Y,
fire advances toward -Y. Roads, field walls/fences, staged trees, drainage pockets,
active fronts and smoke establish the countryside being lost. Two narrow interior
seams provide limited supernatural foreshadowing. No later area is built.

See [BURNED_PLAINS_REVIEW.md](../../assets/source/worlds/emberfall/BURNED_PLAINS_REVIEW.md)
for exact proportions, preserved assets, eight actual views, the ten-question
anti-drift assessment and remaining limits. **Visual foundation owner-approved.**
The existing production socket, yaw, simplified collision and invisible safety
requirements remain in force; this is a visual study, with no export/runtime work.

## 15. Area I modular continuity investigation — 2026-10-05

The approved visual direction remains locked. The isolated three-piece test is
`E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/BurnedPlainsModularity.blend`;
`Input_ApprovedBurnedPlains.blend` preserves the exact live approved input.
See [MODULARITY_REVIEW.md](../../assets/source/worlds/emberfall/MODULARITY_REVIEW.md)
for actual contracts, alternatives, evidence and proposed production implications.

Recommended responsibility split: authored 256-square playable terrain, collision,
landmarks, flora anchors and road guides; assembly-aware burn appearance, joined
road presentation and explicitly non-playable edge scenery. `interior_continuation`
is 256 × 360 scenery with no sockets; it does not change the playable footprint.
The repository supports declared special rectangular pieces, not a reason to
resize normal Burned Plains content.

The bounded 0/180/0 segment and its 90/270/90 whole-assembly rotation retain the
approved planar palette balance and cross two joins without colour resets.
Experimental 24-stud edge collars address slope reversal in the copy; local
authored details remain. No production loader/schema/content/export changes.

**Technical owner review pending, not ready for kit propagation.** A Roblox
appearance/memory/permission test, bending-route field proof, edge shading/LOD and
transformed refuge/tree-stage semantics remain. Current ordinary materials cannot
simply receive Blender world-space shader nodes; EditableMesh colours are a
candidate requiring validation. Do not mass-produce, redesign or begin Area II.

## 16. Area I production-readiness gate — 2026-10-05

The owner approved the visual foundation and modularity proof. Section 15's
pending-review status is historical. Diagnostic overhead bands are non-blocking
polish unless visible from plausible gameplay/elevated reachable positions.
See [PRODUCTION_READINESS_REVIEW.md](../../assets/source/worlds/emberfall/PRODUCTION_READINESS_REVIEW.md).

Standard playable footprint remains 256-square; larger continuation is explicitly
non-playable scenery. Special transition/arena footprints require future explicit
support and owner approval. Area-by-area authoring remains mandatory.

Burn depth follows ordered connected authored guides/route semantics, never a world
axis or Euclidean distance from entry. One continuous field drives terrain and
transformed local refuge/root anchors. Tree/prop variants retain authored composition;
hero overrides must explain a consistent refuge or intentional exception. Hybrid
authored guides plus assembly road continuity remains accepted. Returning-route
balance remains 18.88/31.05/50.07 aggregate green/stressed/charred.

FBX Col BYTE_COLOR/CORNER survives Studio import and actual AssetPreparation /
ChunkLoader. Five client fixed-size EditableMesh visuals can be recoloured once
after assembly. Use white tint, immutable canonical templates, bounded independent
visuals, deterministic shared parameters and teardown. Owner enabled Mesh/Image
APIs in the test place. Mobile/published-place limits remain deployment checks.

**NO-GO for kit expansion:** rising-turn full-edge closure currently depends on
layout-specific prototype geometry adjustments up to ~18 studs. The 24-stud collar
is a technical blend region, never a recognizable socket strip; arbitrary runtime
reshaping is not approved. Freeze reusable authored edge profiles and matching
collision, then prove alternate neighbours without changing vertices. Production
schema/loader proposals remain review-gated. Do not expand Area I or later areas.

## 17. Area I authored edge / collision gate — 2026-10-05

Section 16's geometry NO-GO is historical. The isolated
[EDGE_PROFILE_REVIEW.md](../../assets/source/worlds/emberfall/EDGE_PROFILE_REVIEW.md)
proves six frozen sources: two predecessors join three alternate neighbours under
all quarter yaws, plus a rising-turn three-way corner. Maximum visual/collision
edge gap is 0.000001046 stud, without neighbour-specific edits. Two bounded R15
Studio crossings pass, including the rotated rising-turn exit. Owner review is
next; this task does not authorize production kit expansion.

Standard playable footprint remains 256-square. Minimal symmetric HOLLOW/CREST
connected-side profiles use a clear 24-stud mouth and 33 canonical transverse
height samples. Relative shoulders are +12/-12; adjacent connected corners must
agree in absolute source height. Existing Kind/OffsetY/Facing/yaw handles placement;
sampled geometry validation makes that compatibility real. Centre-ground origin,
local anchors, geometry and collision travel together. No fixed world-axis rule.

Use a 40-stud source-authored transition budget, not the old 24-stud repair collar.
Keep its curved shoulder/rolling approach invisible as a technical region from
gameplay cameras. No layout-specific sculpting or large runtime deformation.
Only numerical/dressing corrections within 0.01 stud are permissible. Outside
connected sides, unique local terrain composition remains authored.

Simplified traversal shares visual edge samples. Closed convex triangular seam
cells in the outer 8-stud row use baked Hull fidelity; coarse interior tiles may
use precise decomposition. The latter alone introduced shoulder steps in Studio
despite matching source vertices. Existing authored CollisionTemplate loading can
preserve mixed baked fidelity. Production import/walk and instance-budget checks
still apply to real assets; no production export/runtime/IDs changed in this proof.

The approved appearance backend, route-depth field, transformed root/refuge
alignment, hybrid road, non-playable scenery and gameplay-camera seam rule remain
locked. New scene: `E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview/BurnedPlainsEdgeProfiles.blend`.
Approved foundation/modularity/production-gate files remain hash-unchanged.
