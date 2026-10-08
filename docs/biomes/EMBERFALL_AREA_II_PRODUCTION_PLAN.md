# Emberfall Area II — modular-production plan

2026-10-08. **Owner-approved planning baseline at079882b; production remains HOLD.**
No approved scene, source geometry, exports, asset IDs, runtime or Studio place is changed.
All numeric design budgets below are proposed unless explicitly marked measured.

## 1. Authority, accepted state and discrepancies

The owner's current instruction accepts both castle variants at **structural blockout**
quality. Variant B is the architectural baseline; Variant A is that same structure after
catastrophic impact. Materials, selective interior damage and environmental polish are
later work. Acceptance does not authorize production implementation in this session.

Area I remains established 256×256 Burned Plains playable chunks. Area II is currently
one continuous town/terrain scene, not an interchangeable kit. Preserve its outer-wall
arrival, village, market/civic progression, terrace/optional route, inner-wall transition
and castle footprint as the macro reference. Each entire castle is one special logical
finale chunk, including entrance, interiors, final boss encounter and reward space.
There is **no standard 256×256 or former boss-arena footprint cap** on either castle.
Both attach through the same inner-wall interface. Logical unity permits multiple
visual meshes and collision components; it does not authorize splitting the castle into
independently selected rooms or redesigning it to meet a terrain grid.

Sources read, in authority order:

| Source | Relevant evidence / precedence |
|---|---|
| Current owner prompt | Final structural approval, common interface, whole-castle exception, ~20-minute total-session target |
| Owner checkout `C:/Users/jhpel/LUCKBOUND` | INDEX, AGENTS, latest WORKLOG (295), STATUS, MASTER_DESIGN, DEVELOPMENT_PLAN; current grassland biome reset and frozen edge contract |
| Latest Area II worktree `C:/Users/jhpel/branch/emberfall-area2` | Latest WORKLOG (313), STATUS, biome/art addenda, AREA2_REVIEW, STRUCTURAL_ACCEPTANCE, IMPACT_FAILURE_REVIEW, CONSISTENCY_REVIEW and saved reports |
| Same worktree, `assets/source/worlds/emberfall/batch1/` | AUTHORING, BATCH1_REVIEW, FULL_MAP_SCALE_REVIEW; current production findings, not older proof counts |
| Same worktree, `assets/source/worlds/emberfall/batch2/` | BATCH2_PLAN, BATCH2_REVIEW, DELIVERY_STUDIO_REVIEW; delivery recovery supersedes earlier upload HOLD |
| Shared MODULAR_MAPS, CHUNK_AUTHORING and build spec §7.7 | Socket transforms, multipart visuals, collision templates, boundaries, generic asset preparation; no new mechanism implemented here |

The saved scene is `E:/BlenderAIProjects/Runtime/Emberfall_AreaII/EmberfallAreaII.blend`.
Read-only SHA256 matches the latest consistency protection report:
`b2b3e160efb6d30db4831448ebf540f2c13ae79d25b09d5e37c2fbc5a5e9e49d`.
The matched B/A overhead evidence was inspected. No Blender job or resave was performed.
Latest checks cover 139 solid subsets and one open-roof surface subset, 183 exact shared
objects and 79 displaced fragments linked separately to real B sources. B/shared castle
651 signatures and town/transition/grounds 887 signatures remain protected. These are
blockout correspondence checks, not production collision or combat certification.

Discrepancies resolved by this plan and the accompanying owning-document addenda:

- Older owner-checkout handoff says no later-area work and only the Burned Plains proof
  exists. Later isolated worktrees contain Batch 1/2 delivery, scale evidence and Area II/III.
  Record those as isolated work, not integrated main production.
- Latest castle documents still say STOP for visual approval. The current owner prompt
  supplies structural approval; STOP now applies to production pending this plan's review.
- Historical volcanic/Outer Wasteland and variable-middle-zone proposals are superseded
  by the owner's grassland → outer wall → settlement → inner wall → selected castle direction.
  Earlier Area IV/source-region language does not require an extra playable zone after the
  castle finale. No new Area IV unit is proposed.
- CHUNK_AUTHORING's historical uniform footprint sentence is not a castle limit. The
  declared complete bounds still govern placement and overlap.
- Area II handoffs call ~20 minutes **pre-boss** and exclude the finale. The current prompt
  says overall session. Plan against **~1,200 seconds including the finale** pending an
  explicit owner decision about any separate deadline. Do not silently add the boss fight
  beyond that budget or convert unallocated time into road distance.

This branch starts from latest local Area II checkpoint `54668c5`, rather than older
origin/main, to retain the relevant handoffs. Latest consistency documents are already
committed in that inherited checkpoint; this planning change does not modify them.
The source worktree is clean and the owner checkout's mixed edits remain untouched.

## 2. Spatial architecture and conversion boundaries

Recommend **256×256 for ordinary playable settlement district sources**, at authored
scale. This is a useful common overlap/export unit, not a requirement for every architectural
place. Buildings are reusable subassemblies inside a district, not generation chunks.
An assembled district chooses a complete authored street/plot arrangement; it does not
scatter independently randomized houses onto arbitrary terrain.

Use special authored units for the outer wall, market/civic landmark where necessary,
inner wall/forecourt and both whole castles. Their declared rectangular envelopes must
fit the approved composition; compact 128×256 or 256×128 connectors may be approved
only where the boundary survey identifies a real fit problem. Do not pre-author an extra
size family. No castle tessellation, tower chunks or independent boss-room selection.

The accepted town reference is **640×1005 studs**, route about **1610.31 studs**, rising
**56 studs** to the inner gate. A 3×4 array of 256 squares would be 768×1024 and would
enlarge it. **Do not snap the whole scene to that grid.** Standard sources must be fitted
around protected landmarks with measured custom transition envelopes where needed.
If exact composition cannot be preserved with these units, HOLD for boundary review;
do not quietly widen the town, move a landmark or trim a building.

Initial composition bands for the later boundary survey (Blender reference Y):

| Band | Protected composition | Candidate production ownership |
|---|---|---|
| Approach / Y≈0 gate and arrival | Asymmetric towers, main arch, blocked breach, arrival apron | One outer-wall transition plus separate socketless wall/scenery wings |
| Y≈66–335 | Gatekeeper/cottages, garden, storage and workshop yard near (-85,280) | Residential and service district sources; protected first-reveal placements |
| Y≈398–582 | Shops, market court near (100,442), guild/civic marker, service yard | Market landmark unit with authored adjoining street sources |
| Y≈635–773 | Terrace, reconnecting court loop, retaining walls and optional stair | Terrace district; keep local loop inside one source where feasible |
| Y≈790–1005 | Upper civic court, collapsed hall, upper homes/stores, formal gate | Upper district and special inner-wall transition |
| Beyond common inner gate | Shared grounds, accepted castle arrival and complete selected finale | Common forecourt connection feeding one B or A finale unit |

These are **reference bands, not approved cut lines or source rectangles**. The continuous
terrain cannot be converted by slicing equal squares and assigning sockets afterward.
First annotate candidate bounds against current saved surfaces, building/roof bounds,
route guides, plot ownership, sightlines and retaining-wall supports. Put seams in ordinary
street/yard surfaces between complete plots. No seam through a doorway, stairs, market
composition, retaining-wall turn, reveal landmark or castle room. Keep complete building
foundations and damage/debris inside one owner. Retain both the exact macro reference and
the candidate overlay for review before extraction from a disposable scene copy.

Declare whole visual/collision/playable envelopes, including roof overhangs and stairs,
not only nominal floor rectangles. Quarter yaw swaps X/Z bounds; current overlap checks
are XZ-only. Reject overlapping districts and castle/scenery occupancy rather than using
height to excuse an overlap. No bridge-over-street stacking or inter-source structural
dependencies in the first library.

## 3. Streets, sockets and shared wall/castle interfaces

Reuse existing socket `Kind`, `Width`, local offsets, `OffsetY`, outward `Facing` and
quarter-yaw transforms; identical Kinds must have identical physical cross-sections.
The following are **proposed authoring contracts**, not registered IDs or schema fields.
Coordinate mapping remains Blender (x,y,z) → Roblox (x,z,-y); source rebasing transforms
visuals, collision, guides, building roots and socket datums together.

| Proposed Kind / interface | Physical contract | Use |
|---|---|---|
| Existing Burned Plains HOLLOW or CREST | 256-wide canonical sampled edge, 24 clear mouth, ±12 shoulders, 40-stud authored transition; ≤0.01-stud seam tolerance | Countryside side of outer-wall unit; match the selected existing profile, never H directly to C |
| `EF_TOWN_STREET_36` | 36-stud clear carriageway, level transverse at socket datum | Lower residential street; matches accepted early street width |
| `EF_TOWN_STREET_44` | 44-stud clear carriageway, same datum rule | Middle commercial/service street |
| `EF_TOWN_STREET_48` | 48-stud clear carriageway, same datum rule | Upper civic street and inner-wall approach |
| `EF_TOWN_LANE_24` | 24-stud clear shared landing, no curb across opening | Optional inter-source lane only if it cannot remain an internal 22–24-stud lane |
| `EF_CASTLE_THRESHOLD_38` | Shared 38-stud clear threshold at inner gate, reference Blender (0,1005,56), forward into grounds; height/arch profile from saved scene | One reserved finale connection accepting either entire castle package |

Town socket certificate: symmetric cross-section through carriageway, flush traversable
shoulder/pavement and matched curb/drain endpoints; no curb crossing the clear mouth.
Propose a **64-stud-wide seam envelope** around main streets, with paved/yard surface
continuing outside the named clear width. Freeze samples at carriageway edges, curb
corners and envelope endpoints, plus each actual profile breakpoint. Keep at least
**16 studs inward** free of buildings, fixed rubble, stalls and threshold grade changes.
Match street centreline position/tangent and material direction; grade eases to a level
landing at the socket, without creating a visible repeated pad. Source elevation may
change between sockets through authored streets/terraces. Opposing transverse samples
reverse order; symmetric profiles avoid hidden mirroring requirements.

Do not apply HOLLOW/CREST's full-side curved grass shoulders or 40-stud terrain band to
urban frontages. They solve a rolling-terrain problem. For urban seams, continue only
the exposed ground that actually abuts a neighbor, match its corner datums where multiple
units meet, and close remaining edges with authored plots/walls or non-playable town
continuation. A 64-stud certificate is insufficient if the rest of two exposed ground
edges touches: that full shared surface also needs matching geometry. No cover-strip
repair, post-assembly ground deformation or buildings shared across a seam.

Special transition ownership:

1. **Outer wall:** countryside approach landing/profile → approved wall/gate → arrival
   apron → lower 36-stud street. Preserve the 36-stud outer arch and the deliberate
   blocked breach. Gate/towers/near foundations belong to the transition. Long curtain
   wings may be socketless backdrop assets; never consume a playable neighbor cell.
   The first proof may support one BP profile; add the other only if the selected route
   needs it. Do not make every 36-street source expose countryside terrain.
2. **Street-width changes:** keep 36→44 and 44→48 changes inside authored districts
   or landmark/transition sources. They have separate arrival/departure Kinds, with
   a deliberate internal widening. Do not match unlike widths by Kind aliasing.
3. **Inner wall:** upper 48-stud street → existing 38-stud gate → common landing.
   Preserve gate elevation +56 in the macro scene, wall silhouette and sightline.
   Gate, threshold floor and wall-foot collision belong to this transition; grounds
   beyond a selected handover plane belong to the selected complete finale. No
   duplicated coplanar collision or a missing floor between ownership domains.
4. **Castle attachment:** B and A use exactly the same local socket frame, outward
   facing, entry landing mesh/profile, pivot convention and reserved Kind. Both include
   their respective complete entrance-to-final-encounter progression and reward provision.
   Derive local offsets from the measured whole-package pivot; reference (0,1005,56)
   is a macro-scene anchor, **not** an unmeasured export-local offset. Survey the common
   grounds and actual arch height before freezing the certificate. The nominal castle
   shell is 500×580; grounds may enlarge the declared complete finale envelope. Retain
   actual approved size; never scale it to a standard tile or claim 500×580 already
   describes the complete loading bounds.

The 38-stud gate is a bottleneck, not a new arena restriction. B retains its primary
hall → tower stair → gallery → integrated rear boss room, about 213×224 clear floor,
and sealed 96×88 reward chamber. A retains its entry/marked route and exact flat
300×320 impact basin. No basement route, new A hall, shifted keep or resized crater.
A reward layout remains an owner decision; future production must resolve it within
the accepted structure. Reward mechanics stay behind their existing implementation gates.

## 4. Building-family inventory and placement

Shared fieldstone, muted plaster, burned timber, pitched roofs, battered plinths,
coping and faceted arches connect town and castle. Reuse construction components
where helpful, while assembling recognizable complete buildings. No building randomizer
or new runtime architectural System is proposed.

Bounded initial library: **eight base types, six silhouette alternatives and four
structural ruin derivatives** (18 complete geometry compositions maximum). Not every
type needs every roof or damage combination. Proposed footprints/heights below are
authoring ranges in studs; reconcile each with its approved plot before authoring.
Height is eave/ridge above local floor, not absolute scene elevation.

| Family / base type | Footprint; eave / ridge | Meaningful silhouette/roof options | Initial structural states |
|---|---|---|---|
| Residential: small cottage | 30×38 to 32×42; 16–18 / 24–28 | Long gable with porch; alternate cross-gable with offset hearth annex | Surviving shell; one roof-bay loss |
| Residential: terrace house | 34×42 to 42×58; 22–30 / 32–42 | Narrow two-storey gable; alternate stepped L plan with lower rear shed | Partial floor/upper-wall failure, intact supported corner |
| Commercial: shop house | 36×48 to 38×50; 24–27 / 34–39 | Street-facing broad gable with recessed shop; alternate hipped corner shop with side loading bay | Closed shell; broken frontage/awning |
| Commercial: store hall | 46×66 to 50×68; 24–31 / 35–44 | Long ridge, loading doors and low attached bay; alternate paired unequal gables | Burned roof frame or substantial roof collapse |
| Workshop/service: workshop | 44×58; 25–27 / 34–39 | Low broad gable, chimney and open work bay; alternate courtyard L with lean-to | One broken bay; local active burn, grounded debris |
| Workshop/service: stable/service shed | 28×48 to 38×60; 14–19 / 23–29 | Low hipped shed, yard-facing bays; no second silhouette initially | Surviving posts/roof versus fallen roof section |
| Ruined residential: terrace remnant | Same original residential plot; surviving 8–22 high | Collapsed from terrace-house baseline; retain stair/hearth and grounded corner | One approved collapse composition, original foundation trace |
| Ruined service: failed hall | 60×74 accepted landmark plot; surviving 10–32 high | Collapsed original hall bays, unequal roof plates and supported wall returns | One high-signature failure composition |

The six alternatives belong to cottages, terrace houses, shops, stores, workshops and
the ruined residential remnant (different original bay failure). The four further ruin
derivatives belong to cottage, shop, store and workshop. Ruins must identify their source
building and lost load path, as A identifies B. A roof removed from an intact box is not
an adequate ruin. Scale/color changes do not count toward the 18 compositions.

Separate landmark compositions: guild/civic hall with modest bell mass, market court,
upper civic court/failed terrace and gatekeeper arrival. Preserve approved placement,
height hierarchy and former use. They are not ordinary reusable house variants. The
initial village arrangement is approved as a foundation, while building variety and
market elaboration were explicitly deferred; production variants must fit its plots
and sightline hierarchy rather than redesign its town layout.

Placement rules:

- Each authored plot contains full roof/eaves, footing, stoop, chimney, collapse debris,
  solid scenery and camera clearance. Proposed 8-stud margin inside ordinary district
  bounds; measured complete envelopes govern exceptions. Socket's 16-stud approach
  clearance takes precedence. No object clipping into a neighbor after rotation.
- Doors face a street/court and connect by a deliberate stoop/path. Eaves, shop fronts,
  roof ridge orientation and yards establish blocks and a frontage rhythm. Break rows
  with a lower service bay, setback court, garden trace or damaged gap.
- Proposed clear side lane 22–24 studs, narrow plot passage at least 12, enterable door
  at least 8 wide/10 high, main encounter area at least 48×48. These are proof targets,
  not certification for a combat roster or camera. Do not shrink approved broad arches.
- Require a declared accessible/sealed status per building. First proof has one simple
  enterable shop/workshop bay, remaining houses exterior-only. Avoid paying for every
  house interior before gameplay requires it. Decorative doors cannot lead to voids.
- Building collision travels with its authored district, independent of burn color.
  Alternate structural geometry must ship its own matching collision certificate.

## 5. Street and encounter composition

Proposed library is **eight district sources plus three special transition/landmark
units**, then the two accepted castle alternatives. Start smaller under §9.

| Working composition | Sockets / circulation | Signature and function |
|---|---|---|
| Residential frontage straight | 36→36; staggered fronts, yard opening | Low; ordinary inhabited connective place |
| Residential dogleg | 36→36, quarter turn with unequal approach lengths | Low; view shift, quiet court; not the same elbow repeated |
| Workshop street | 36→44 widening; yard beside road | Medium; service use, optional encounter/loot bay |
| Shop-front street | 44→44; setback bays/opposed doors | Low; varied commerce without market landmark |
| Market approach bend | 44→44; modest reveal through unequal fronts | Low; prepares distinct market composition |
| Terrace/court loop | 44→48; local split/rejoin around retaining wall | Medium; optional exploration, main route remains legible |
| Upper residential street | 48→48; surviving tall corner and low ruin frontage | Low; heavier destruction, clear castle view |
| Quiet service court cap | One 24 or matching main-street socket | Low; plausible terminus with former work/storage use |
| Special market/civic composition | 44→44; approved court/marker, subordinate stalls/yard | High; market reveal and generous encounter surface |
| Special outer-wall arrival | BP profile→36 | Once; approved countryside/town change |
| Special inner-wall/forecourt | 48→reserved 38 threshold | Once; approved town/finale handover |
| Complete castle B / complete castle A | One identical reserved 38 threshold each | Exactly one selected per run; entire logical finale |

Names are planning labels, not content registrations. The survey may consolidate a
district/landmark or introduce one compact connector to preserve composition; do not
expand the library until that need is demonstrated. Preserve the existing garden,
service yard and optional terrace route as authored former-use spaces.

The town needs a legible main road, adjoining local streets and blocks, not a series of
combat boxes. Provide cross-street views and closed courtyard compositions, believable
loading yards, wells/garden remnants and alternative local paths that reconnect. Market
stalls share one commercial circulation area; leave shop fronts and clear court centre
visible. No random houses in leftover spaces, mandatory fights in every chunk, or
identical chest at every street endpoint.

Current generic generation grows a critical path and capped branches; it does not prove
arbitrary graph reconnection or a locked three-area sequence. Keep the first optional
loop **inside one authored district**, and cap any external branches with meaningful
service courts. Later implementation must demonstrate an ordered Area I→outer wall→
Area II→inner wall→one BOSS unit using the existing blueprint/Kind rules. If these rules
cannot express area sequencing, source-repeat spacing or valid caps, propose the smallest
generic spec/schema amendment before runtime work. Do not disguise a preassembled town
as arbitrary procedural success, use attached-room portals for ordinary streets, or put
Emberfall selection special-cases in Systems.

## 6. Collision, safety and packaging ownership

Use a chunk-owned, server-authoritative `CollisionTemplate` for ground, terrace/stairs,
retaining walls, whole-building blockers and significant debris. Packaged collision
preserves reviewed fidelity and avoids reacquiring every mesh shape each Play. Simple
boxes/wedges and deliberately convex Hull pieces suit architectural walls/floors better
than dense terrain grids. Use precise decomposition only where actual concavity needs
it and cooked results are accepted. Stairs may use a tested traversal ramp with visual
treads; it must fit landings and not create a camera/character trap.

Every physical surface has one owner: district ground, building shell or landmark/
transition. Disable corresponding visual collision only with the matching complete
template present. Do not silently double floors/curbs or accept a missing-template
visual fallback as collision certification. Structural walls, doors and floors remain
authoritative even when their art is batched. Small ash, signs, roof detail and embers
are noncollidable/nonquery/non-touch scenery; doorway gates/rewards use existing fixtures
when that work is separately authorized. Solid prop instances remain server-owned.

Batch immobile nonsolid masonry/roof detail by source, material and visibility region;
retain reusable complete building shells or a small number of submeshes when they improve
asset reuse. Do not export one MeshPart per brick, beam or grass clump. Do not merge the
whole town/finale into a single oversized part: under-10,000 triangles per exported
mesh and measured bounds still apply. Logical castle unity is preserved across internal
visual/collision packages; those packages are not separate selectable chunks.

Safety boundaries protect exposed playable edges and blocked departures; keep all
valid mouths open. Reuse source-local boundary/camera-exclusion semantics. Interior
tile edges are not safety walls: Batch1 removed 128, Batch2 removed 368 internal segments.
Do not reinstall invisible barriers across a town's streets or local exploration loops.
Validate boundary endpoints against the assembled playable outline; structural town
walls and boundary-only camera exclusions are different concerns.

## 7. Burn progression, variety and repetition

Separate **burn exposure** from **structural destruction**. Surviving, damaged,
actively burning and collapsed buildings are not four interchangeable color skins.
Structural states have authored missing bays, roof types, floor/support survival and
matched collision. Active fire can occupy a partly surviving or ruined source, with
deterministic restrained pockets; it need not always coincide with maximum collapse.

Reuse ordered guide arclength/semantic depth and transformed local roots/refuges as the
composition model. Do not use world Y/X/Z or chunk index alone to create abrupt burn
steps. At intersections/optional loops use distance from the main progression anchors,
not a fresh zero-based side-route gradient. Castle/source→inner town→outer town→countryside
front remains legible; retained gardens/courtyards provide justified refuges. B's intensity
may differ from A, while both share the same geography and building ancestry.

The Area I 18.88/31.05/50.07 grass balance is **not a town building quota**. Use heavier
inner exposure with scattered surviving plaster, roof tiles and structural corners to
show former habitation. Correlated fire fronts should cross streets/neighboring plots;
vary damage by wall orientation, roof exposure, refuge and authored structural cause.
Avoid identical roof loss, burning window and rubble fan at each boundary.

Prefer ordinary baked appearance modules and a small reviewed state library. Full-run
EditableMesh terrain/grass allocation previously failed after nine terrains, at the
first grass allocation; that is a measured test failure, not a universal count ceiling.
Arbitrary-layout coherent baked state selection is still OPEN. Do not assume review-
layout baked snapshots solve production selection. Require two assembled layouts with
cross-seam state continuity and matching structural collision before selecting a final
appearance strategy. No scene-wide black tint or runtime collider deformation.

Adapt Batch2 signature rules, with a smaller-town proof first:

| Class | Proposed settlement restriction | Controlled variation |
|---|---|---|
| Low ordinary street/court | At most twice/source in initial Area II; ≥2 intervening districts | Different neighbor pair and frontage/dressing preset; no repeated three-source sequence |
| Medium workshop/terrace | Once initially; permit twice only after repetition review | Different approach/reveal plus genuinely different supported plot arrangement |
| High market/civic/failure landmark | Once; preferably ≥2 ordinary districts between major reveals | Preserve approved identity, vary restrained nonsolid dressing only |
| Outer/inner wall | Exactly once in correct order | Same accepted interface; no interchangeable random wall collapse |
| Castles | Exactly one B or A | A derived from B; internal packing cannot change structural ancestry |

These are curation constraints, not currently enforced new fields. Small Area II cannot
blindly inherit Area I's four/six intervening-piece rule. Initially aim for about 60%
low-signature district placements, without forcing a count to hit the fraction. Start
with two authored frontage presets for one low street, preserving ground, sockets and
main circulation. If a building/solid arrangement changes, validate its collision too;
nonsolid dressing-only variants preserve collision identity. Rotation/color alone is
insufficient. Avoid mirroring sockets, stairs or castle damage.

## 8. Evidence, initial budgets and risks

Measured evidence (these are fixture observations, **not platform limits**):

| Test | Observed cost/result | What it establishes / does not establish |
|---|---|---|
| Batch1 final frozen nine | 230,445 source visual triangles, 902 source visual objects; 627 terrain colliders, 69–70/source | Source authoring cost; source objects are not deployed-instance counts |
| Batch2 eight new sources | 169,800 source visual triangles, 250 source objects, 558 terrain colliders | Quiet library additions; 44 exported source/variant visual meshes, 212,850 triangles including alternatives |
| Batch2 imported repeated 24 | 1,634,590 visual triangles, 299 presentation parts, 907 unique cooked collision assets, 1,675 placed colliders; 400 outer boundary parts | Real loader, 162 rays with zero misses, max seam 0.0001221 stud; 372-second normal traversal visits all 24; not combat pacing |
| Batch2 fresh client | 1,974 parts, 1,074 unique IDs preloaded with no failure | Successful bounded fresh Play after stale-state failure; not cold-cache or mobile guarantee |
| Full-map cost fixture, 36 equivalents | 2,338,548 visual triangles; 760 visual / 2,868 collision MeshParts; 3,628 total MeshParts; 4,340 BaseParts; 4,457 descendants | High-end PC scale PASS with repeated geometry/proxies; not a finished town/castle map |
| Same fixture, two fresh Plays | Server 19.63–22.45s; client assets 20.29–23.56s; player 20.64–25.19s; ~60 FPS, p95 17.72–18.13ms | Foreground 1993×978, Level21, i9/RTX4080; cache warmth uncontrolled, no NPC combat |
| Acquisition breakdown | 627 unique collision shapes 15.26–17.79s; six-worker visuals ~1.10–1.72s; scenery ~1.25–1.31s | Collision API acquisition dominates diagnostic path; existing preparation batching works |
| Same fixture memory/IDs | Graphics mesh delta ~61.5MB; physics ~19.2MB; 786 unique IDs, mostly repeated/byte-identical content | No reliable genuinely unique-geometry or low-end memory ceiling |
| Batch2 imported bounds recovery | 23 oversized scenery objects→104, one failed cell→two; total triangles unchanged | Actual review part size clamped beyond 2048 studs; packaging bounds must be checked |

Proposed authoring/packing budgets, subject to the proof and owner approval:

| Unit | Visual triangles / MeshParts | Collision and total instances | Unique assets |
|---|---|---|---|
| Ordinary 256 district | 60k target, 90k HOLD threshold; ≤24 visual MeshParts | ≤80 solid collision BaseParts; ≤140 total BaseParts including boundaries; ≤160 descendants | Prefer ≤8 new visual MeshIds/source after shared building reuse; count state alternatives explicitly |
| Market or wall transition | ≤120k visual triangles / ≤32 visual parts | ≤100 solid collision BaseParts; ≤180 total BaseParts / ≤210 descendants | Review every unique landmark mesh; reuse wall/roof families |
| Selected complete castle | 350k target, 450k HOLD threshold / ≤64 visual parts | ≤300 solid collision BaseParts; ≤400 total BaseParts / ≤450 descendants | ≤40 new visual MeshIds for selected variant initially; budget both cached variants separately |
| Building shell | 4–8k visual triangles; usually 1–3 meshes | Typically 4–12 simple collider parts; no per-brick collision | Share identical immutable modules; distinct silhouette/structural states count as distinct assets |
| First proof: three district sources + one inner-wall interface | ≤390k total source visual triangles / ≤104 visual parts | ≤340 solid colliders; ≤600 BaseParts / ≤690 descendants | ≤60 new visual IDs, ≤32 new mesh-collider IDs; prefer native Parts for simple collision |

Collision targets count native Parts and mesh colliders; safety parts are in the total
BasePart column, not hidden in visual or solid-collider counts. Collider triangles,
unique meshes and cached templates must also be recorded. These proposed town costs are
higher than grassland source triangles to allow real architecture, while controlling
instances through reuse/batching. They require measurement; they are not proven ceilings.
One active castle per run; loading/caching both is extra memory, not free variation.

Initial **whole-run review guardrail**, including Area I, town, transitions, castle and
scenery: stay within about **2.34m visual triangles, 760 visual MeshParts, 2,900 mesh
colliders, 4,340 total BaseParts and 4,460 descendants** until representative profiling
justifies changes. Native-collider counts cannot evade the BasePart budget. Use an early
whole-run ledger; do not grant each area the entire measured map envelope. At most
**150 incremental unique rendered/collision MeshIds** beyond the selected Area I library
is an initial review trigger, not a measured safe unique-memory limit; texture IDs are
additional and require their own preload/memory report. Above a target means HOLD and
review, not automatic visual simplification or geometry redesign.

Illustrative accounting only: 16 Area I placements at 24-route average ≈1.09m triangles,
six 90k town districts =540k, two 90k transitions =180k, one 450k castle =450k: about
2.26m. This leaves little space for extras and shows why a ledger matters. Batch2 average
includes route-specific scenery, so it is not a precise marginal cost. **24 Area I
placements plus that same later content ≈2.80m exceeds the guardrail.** No 16-piece Area I
decision is made here; select composition/pacing first and profile the resulting recipe.

Loading recommendation: reuse unique role-aware preparation, six-worker bounded batching,
immutable shared visuals and exact packaged collision templates. The parked Batch1
collision package has Default fidelity and must not replace reviewed Hull/Precise shapes.
Count preparation, cloning, replication, preload and character readiness separately.
Zero EditableMesh allocation is the initial proof target. Do not promise progressive
loading, new cache eviction, custom streaming or deferred authoritative collision;
those require separate generic design if actual later profiling demands them.

Risks: truly distinct architectural memory/IDs; A/B double caching; overlarge combined
scenery bounds; initial stale client fetches; cooked stairs/door collisions; courtyard
camera occlusion; overdraw/fire lights/particles; whole-castle residency and readiness;
missing generic area sequencing/loop closure/repetition enforcement; unproven target
device/published entry and combat cost. Pack visuals into bounded spatial batches for
normal culling without turning castle internals into generation chunks. Do not carry
catalogue Persistent mode into production as an unexamined requirement. Published
streaming/entry tests must prove complete collision before admitting players.

## 9. Bounded first-production-proof sequence and GO/HOLD gates

**This is a proposed next task, not authorization to execute now.** No parallel
production batches until the shared contracts and proof pass. Cheap source checks →
owner visual/manual test → targeted fixes → required integration checks, following
the repository's rapid-iteration rule. Do not pre-run exhaustive traversal matrices.

1. **Boundary/contract gate:** owner approves this plan; later annotate candidate cuts
   in a disposable copy/overlay while keeping the current blend exact. Freeze one
   residential 36-street district, one workshop 36→44 district, one terrace/shop 44→48
   district and one inner-wall 48→38 interface. Preserve the market landmark as a
   reference rather than producing the full market in this proof. Confirm complete
   package pivots/bounds and common castle socket against both variants without
   subdividing either castle.
2. **Small architecture library:** cottage, shop, workshop and terrace house; add two
   meaningful silhouette alternatives and two source-derived collapse states (eight
   complete compositions maximum). At least one simple enterable bay. No full interiors,
   castle detailing, broad prop library or Area I polish. One two-preset ordinary street
   proves controlled frontage variation; other sources use one authored arrangement.
3. **Frozen geometry proof:** the three sources plus inner-wall unit in one approved
   composition, then a second arrangement reusing the low residential source with a
   different frontage preset. Keep a local optional loop in the terrace source. Test
   each used Kind at the relevant quarter yaws using actual socket/overlap math; include
   one repeated same-yaw source and one rotated counterpart. B and A attachment is a
   transform/certificate comparison to retained whole units, not a new castle export.
4. **Owner art review:** street-level composition/roof hierarchy, coherent former use,
   damage/front continuity, market sightline and inner-wall/castle reveal. Stop for
   feedback before upload/import work. Preserve approved macro geometry throughout.
5. **Separately authorized imported proof:** representative district/wall assets through
   actual AssetPreparation/ChunkLoader and exact packaged collision. One normal owner
   walk across widths, terrace/local loop, enterable bay and inner threshold. Targeted
   rays only at new mechanisms and reported failures. Later import the complete selected
   castle if needed for full encounter/camera/loading validation, still one logical unit.
6. **After owner pass:** repeated-source review, required CI and published/device profiling
   against the chosen complete-map recipe. Only then approve a bounded second production
   batch or parallel authoring lanes using frozen API/contracts and disjoint ownership.

Measurable acceptance:

| Gate | GO | HOLD |
|---|---|---|
| Preservation / ownership | Approved scene SHA unchanged; no macro relocation/rescale; every plot/roof/collider has one owner | Any edit to approved input, split castle, mismatched B ancestry or boundary through a protected composition |
| Socket certificate | Used pairs opposed, centers/heights/profile gaps ≤0.01 stud; all used rotations non-overlapping; B/A common threshold identical | Kind-only compatibility without geometry evidence, width mismatch, missing floor or runtime repair |
| Town circulation | Main route reaches inner wall in both proof layouts; one usable local loop; zero uncapped external openings; zero door/plot obstructions | Dead streets onto scenery/void, branch blocks route, loop requires unbuilt graph reconnection |
| Structure / collision | Clear declared doors/landings; zero missed bounded seam/floor rays; owner walk does not catch/fall; matching template coverage | Visual-only collision assumption, curved Hull merge errors, duplicate ground or invisible internal wall |
| Variety / burn | Four functions, six silhouette compositions plus two ruins; two frontage presets; no repeated three-source sequence; no owner-visible seam/front discontinuity in agreed views | Scaled/recolored copies presented as silhouettes, repeated rubble/front stamp, incoherent neighbor exposure |
| Packing / budget | Proof stays within §8 ledger; each mesh <10k triangles and each delivered dimension ≤2048; zero missing required assets/fallbacks; zero EditableMeshes | Unexplained extra parts/unique IDs, clamping, full-run EditableMesh dependence, incomplete template fidelity |
| Loading (later imported proof) | Two stop/start Play sessions, zero failed preload IDs; stage timings recorded; whole recipe aims ≤25s effective ready on same test PC and viewport | Repeated fetch failures, readiness before collision, regression beyond comparison envelope without explained cause |
| Runtime (later full recipe) | Same-PC no-combat p95 ≤20ms, no sustained >33ms stalls in agreed views; counts within initial guardrail | Target missed or new AI/VFX cost omitted from rollout assessment |
| Rollout | Owner approves proof; CI passes; published entry and representative device checks meet agreed targets | PC-only evidence described as mobile certification; missing generic sequencing/appearance contract or unresolved A reward requirement |

Timing is a planning gate, not yet a playable proof: keep roughly **6–8 minutes of
traversal** in the complete route envelope suggested by the handoffs, leaving roughly
**12–14 minutes for encounters, finale, exploration and loot**. A provisional 20-minute
activity ledger might be traversal 6, settlement/countryside combat 6, exploration/loot
3, boss/reward 4, transitions/pauses 1 minute. These allocations are unmeasured and
need gameplay tuning. B's reference II+III walk ~2.48min and A ~2.28min are geometric
estimates at 16.8 studs/s, not a reason to extend streets. Log actual traversal and
activity separately when those systems exist; HOLD a route that meets the session
target only by padding empty walking. Do not set production timers in this task.

## 10. Owner decisions still needed

1. Approve 256-square ordinary districts with measured special transition/landmark
   envelopes; exact cut overlay must preserve the 640×1005 town. Approve a compact
   connector only if the boundary survey proves it necessary.
2. Approve the proposed 36/44/48 street vocabulary, optional 24 lane and shared 38
   castle threshold. Decide whether the first outer-wall proof must accept HOLLOW,
   CREST or both; use actual chosen Area I terminal, not guesswork.
3. Approve the small proof/library scope and the proposed silhouette/destruction roster,
   including one enterable bay and exterior-only houses initially.
4. Choose A's post-boss reward provision inside its accepted structure. B's existing
   reward chamber remains accepted. Do not redesign A while this decision is pending.
5. Confirm whether ~20 minutes includes the boss/reward in the actual expedition
   deadline. This plan follows the current overall-session wording; older pre-boss
   wording is historical. Choose pacing with gameplay, not another blockout rescale.
6. Specify initial target devices/player count and published readiness/frame targets;
   accept or revise provisional §8 budgets before wider production.
7. At the later contract gate, approve the smallest generic amendment if existing
   sequencing/state-selection/repetition data cannot express the curated district recipe.
   No new live fields, remotes, Systems or amendment number are allocated now.

Structural approval of both castles, B→A ancestry, whole-castle logical unity, identical
inner interface and preservation of macro composition are settled, not questions to reopen.

## 11. Checkpoint, evidence retention and stop

Plan and owning-document addenda are checkpointed locally on `agent/emberfall-area2-plan`
under `E:/BlenderAIProjects/Worktrees/emberfall-area2-plan`. No push/PR/merge is requested.
Source worktree and owner checkout stay unchanged. This is planning readiness, not
production GO or implementation completion.

No assets, exports or manifest rows are replaced. Historical proposals superseded as
active requirements: separate/new A architecture, former standard castle/arena cap,
equal-grid town slicing, walking quotas and the old pre-boss-only timer interpretation.
Keep initial/BeforeImpactCorrection/BeforeBaselineRework/BeforeInteriorLayout/
BeforeStructuralCleanup/BeforeFinalCorrections/BeforeImpactStructuralFailure/
BeforeConsistencyCorrection inputs, `.blend1`, recovery collections and evidence.
Keep Batch1/2 source assets, failed-upload/bounds-cell ledgers and scale fixtures. Only
recommend retiring task-owned obsolete review copies after owner acceptance and relevant
CI/Studio replacement checks; owner-kept or referenced assets remain kept.

**STOP for owner planning review. No production assets were generated or changed.**
