# Burned Plains Batch 2 pre-production plan

**2026-10-06 — recommend eight new terrain sources, bringing Area I to seventeen.**
Six additions should be quiet repeatable connective places; one adds sheltered
tree framing and one adds a restrained rural remnant. This is an authoring brief,
not new production geometry or generator implementation. Performance gate remains
PASSED. Start with route flexibility, then finish environmental variety.

## 1. Authority and audit evidence

- Owner checkout: `C:/Users/jhpel/LUCKBOUND`, `agent/emberfall-burned-plains`,
  `b09a496`, with mixed uncommitted reset/proof documents. Preserved unchanged.
- Planning worktree: `E:/BlenderAIProjects/Worktrees/emberfall-batch2-plan`,
  `agent/emberfall-batch2-plan`, based on `a0f0817`; verified ancestors `73b918b`
  (accepted walkthrough) and `3e15bc4` (scenery scaling).
- Read root AGENTS and parent `E:/BlenderAIProjects/AGENTS.md`, current
  INDEX/handoff/status and relevant Master Design,
  development plan and Git workflow sections. Git's accepted tree has no nested
  AGENTS under the affected paths; parent instruction candidates were checked.
- Current owner-checkout `docs/biomes/EMBERFALL.md`, `MODULARITY_REVIEW.md`,
  `EDGE_PROFILE_REVIEW.md` and contract code supply the accepted grassland/edge
  authority. This branch's older volcanic narrative is superseded, not reopened.
- `../batch1/BATCH1_REVIEW.md`, `OWNER_WALKTHROUGH.md`,
  `SCENERY_SCALING_REVIEW.md`, `FULL_MAP_SCALE_REVIEW.md`; actual `countryside.py`,
  `elevations.py`, `fields.py`, shared helpers and frozen layout report inspected.
- Read the nine actual saved source scenes from external `Emberfall_Batch1/`
  lane blends without saving. All nine terrain coordinate hashes match their
  scene metadata. `source_readback.json` retains actual sockets, road measurements,
  tree counts and refuge metadata. Inspected kit overview/player-view sheets.
  Readback script remains external in `Runtime/Emberfall_Batch2Plan/read_sources.py`.

## 2. Batch 1 library audit

H = HOLLOW; C = CREST. Datum/rise below is source design, before centre-ground
rebasing. Net level does not mean flat interior terrain. Road range is max minus
min sampled road height; this separates endpoint rise from local rolling relief.
All sources rotate to four compass orientations with geometry, guides, anchors
and collision together. Rotation preserves handedness; reversal changes it.

| Chunk | Forward route / road gesture | Socket datums | Road rise / range | Signature and distinctive cue |
|---|---|---|---|---|
| Windward Meadow | S→N; nearly straight, 5-stud one-sided drift | H0→H0 | 0 / 2.0 studs | Medium: long dry-stone wall, entry gate, sheltered meadow and small marker |
| Drainage Crossing | S→N; nearly straight, 3-stud drift | H0→H0 | 0 / 2.3 | Medium: paired lintel culvert mouths, transverse damp ditch and marker |
| Orchard Bend | S→E right 90°; regular 128-radius quarter arc | H0→H0 | 0 / 5.4 | High: sixteen orchard trees, cultivated rows, inner grove and harvest barrow |
| Ridge Ascent | S→N; broad straight, 4-stud drift | H−24→H0 | +24 / 26.0 | Medium: tall west windbreak, rising ridge and open east overlook |
| Switchback Bank | S→E right 90°; same quarter arc, rising | H0→C24 | +24 / 24.0 | Medium: curved cutbank tree line and outer open bend; one bend, not a hairpin |
| Waymark Terrace | S→N; almost straight, 2-stud drift | C0→C0 | 0 / 2.9 | High: single 7.55-stud waymark on a low ridgebench |
| Open Field Clearing | S→N; nearly straight, 4-stud drift | H0→H0 | 0 / 1.9 | Low: empty central lawn between interrupted side walls, four peripheral trees |
| Burn Front Verge | S→W left 90°; same quarter arc, rising | H0→C24 | +24 / 24.0 | High: broken farm wagon, stubble ribbon and inside pasture fence |
| Fenceline Rise | S→N; straight with larger 7-stud drift | C0→C16 | +16 / 16.0 | Low: broken roadside pasture fence, oblique ridge and distant wall |

| Chunk | Environment / burn usefulness | Gameplay possibilities | Repeat guidance |
|---|---|---|---|
| Windward | Open maintained field; five trees in flank groups; strongest wall-sheltered refuge | Entry, orientation, pacing reset, modest open skirmish | Once as entry; do not repurpose as ordinary filler |
| Drainage | Open-to-framed crossing; five bank trees; damp transverse refuge makes a surviving interruption plausible | Traversal beat, bounded roadside skirmish, reset | At most twice, widely spaced; culvert geometry remains recognizable |
| Orchard | Most tree-dense piece; 16 of the library's 56 trees; cultivated outside rows and shorter inside grove | Framed traversal, constrained orchard skirmish, bend reveal | Once per Area I route; recolouring does not disguise rows/barrow |
| Ridge | Semi-open, six uneven windbreak trees; sheltered leeward grass, open east slope | Traversal, overlook, open off-road encounter | Up to twice with intervening low pieces; avoid repeated ridge silhouettes |
| Switchback | Semi-enclosed inside bank, eight tree-line anchors; broad outside lawn and lower-bank refuge | Climbing traversal and outside-bend encounter | Up to twice with spacing; avoid consecutive cutbank/arc grammar |
| Waymark | Open ridgebench, five peripheral trees; tiny wall-protected remnant | Open west encounter, orientation, pacing reset | Once; the stone silhouette is a landmark even though modest |
| Clearing | Most open central combat lawn, four edge trees; small damp western refuge | Main open encounter and recovery space | Repeat often within low-signature limits; change neighbors/dressing context |
| Verge | Open outside swale, four trees; fence/stubble/wood show advancing damage | Traversal, open flank encounter, abandonment beat | Once; wagon and regular left arc remain memorable |
| Fenceline | Open pasture, three sparse trees; narrow drainage refuge below fence | Traversal, smaller pasture encounter, breath between landmarks | Repeat within low limits; don't chain identical fence-side views |

Every source supports surviving/stressed/charred appearance through assembly
state and authored root/refuge semantics. Neither the chunk name nor elevation
fixes a burn stage. Combat uses here are spatial opportunities, not certified
enemy/pathfinding layouts. Props currently have deferred physical classification.

**Orientation caveat:** current `placeAgainst` takes the first matching socket.
For H/H or C/C pieces, the normal match enters the first (S) socket. Four rotations
do not supply the opposite handed bend or reverse a rise automatically. Mixed H/C
pieces can enter either end according to the arriving Kind: existing rising turns
become falling opposite-handed turns when approached from C. Reversed same-Kind
traversal requires explicit planning of the consumed socket; do not count it as
an automatically available choice or alter the loader for this batch.

## 3. Ranked gaps

1. **Quiet bends on both profile networks.** H level bending currently requires
   Orchard; there is no C/C bend. Existing H→C bends simultaneously turn, climb
   24 studs and introduce recognizable dressing. Provide independent quiet turns.
2. **CREST continuity and a shallow profile conversion.** C level travel relies
   on Waymark; its other straight rises 16. Returning C→H currently requires a
   reverse rising turn. A shallow opposite-edge H/C connector lets profile changes
   occur independently of a landmark or compass change.
3. **Road gestures beyond one arc and small one-sided straight drift.** All three
   turns use the identical 201.057-stud quarter-circle guide; straights share the
   same sine-cubed drift with amplitudes 2–7. Add different turn timing, an actual
   shallow S gesture and a long roadside ditch instead of another crossing.
4. **Gentler elevation rhythm and ordinary downhill travel.** Non-level endpoints
   are +16 or +24; rises dominate forward same-Kind traversal. Add +12 H/C straight
   conversion and −8 C/C pasture descent. Level pieces may roll internally.
5. **Enclosure without orchard rows or a linear cutbank windbreak.** Most places
   are open lawns with edge groups, walls/fences. An irregular offset grove can
   create compression/release and a sheltered encounter without dense forest.
6. **More ordinary countryside between memorable locations.** Clearing and
   Fenceline are the two low-signature sources. Accepted full-kit showcase layouts
   intentionally include every landmark: Layout1 has Waymark/Wagon adjacent;
   Layout2/3 also cluster landmarks. These are demonstrations, not long-run pacing.
7. **One additional abandonment story, without more hero clutter.** Rural life is
   largely field boundaries, culvert, orchard and wagon. A small farm outbuilding
   footprint can foreshadow civilization while keeping the wall/settlement later.

## 4. Practical signature and repeat rules

These are authoring/curation rules, not installed generator fields or new systems.
Signature describes recognizable composition, independent of burn colour.

| Class | Meaning | Initial per-Area-I use rule |
|---|---|---|
| Low | Connective landform, no unique prop/silhouette | Up to 3 uses/source; at least 4 intervening chunks; varied neighbors and dressing |
| Medium | Recognizable framing or terrain composition | Up to 2 uses/source; at least 6 intervening chunks; changed reveal/context |
| High | Obvious landmark or unique authored arrangement | Once/source; at least 4 ordinary chunks between high-signature places |

Batch1: **Low** Clearing/Fenceline; **Medium** Windward/Drainage/Ridge/Switchback;
**High** Orchard/Waymark/Verge. Windward stays entry-only regardless of class.
In longer recipes target roughly 60–75% low-signature placements; a short segment
can reasonably depart from that. Do not force every high source into every route.
Avoid repeating a three-source sequence. Do not chain more than two regular
quarter-circle bends without a different connective gesture. Insert a quiet
opening after a major reveal/encounter; never treat every chunk as a mandatory fight.
For repeated low sources, prefer a different quarter yaw, but require another
authored dressing choice when the same yaw/reveal repeats. Colour/state alone
does not satisfy this rule. Reject a cramped or repetitive recipe instead of
adding props until the repetition is hidden. No mirrored geometry is implied.

## 5. Proposed Batch 2 — eight source chunks

All working names below are planning labels, not registered content IDs. Socket
datums are pre-rebase. Guides must keep exact endpoints/outward tangents, clear
24-stud mouths and the 40-stud source transition; vary the interior beyond it.

| Order / working name | Exact library role and route | Sockets / elevation | Signature / repeat |
|---|---|---|---|
| 1. **Quiet Hollow Bend** | Ordinary left turn; S→W, net 90°, long approach then a late broad sweep, not a circular elbow | H0→H0; level endpoints, 2–4-stud interior roll | Low; up to 3; two dressings |
| 2. **Raised Pasture Bend** | Landmark-free C-network right turn; S→E, net 90°, early broad turn followed by a longer exit | C0→C0; level endpoints, low rounded shoulder with 2–4-stud relief | Low; up to 3; two dressings |
| 3. **Low Shoulder Climb** | Shallow reversible profile conversion, independent of a turn; S→N opposite edges, broad oblique track | H0→C12; +12 forward / −12 from C, broad modest grade | Low; up to 3; no extra dressing needed initially |
| 4. **Swale Drift** | Alternative H straight, shallow S road with two opposing sweeps, approx. 18–24-stud lateral excursion in the interior | H0→H0; shallow dip/recovery, target 3–5-stud road range | Low; up to 3; two restrained dressings |
| 5. **Pasture Saddle** | Ordinary C downhill connector and reset; S→N with low off-axis road over a broad saddle | C0→C−8; gentle −8 exit fall with one small local roll | Low; up to 3; no extra dressing needed initially |
| 6. **Long Ditch Verge** | Alternate H straight; road follows a longitudinal drainage swale rather than crossing it | H0→H0; level endpoints, local 2–4-stud low ground | Low; up to 3; two dressings |
| 7. **Leeward Grove** | Sheltered C connector; S→N, track slips beside an irregular grove then opens, no orchard grid | C0→C0; level endpoints, shallow lee pocket | Medium; up to 2; one composition initially |
| 8. **Abandoned Fieldstead** | Rare rural threshold/encounter place on C; S→N, road skirts a compact outbuilding footprint | C0→C0; broad near-level side yard | High; once; one composition initially |

**1 — Quiet Hollow Bend:** open grassland with a low outside bank, almost no
roadside stone, one sparse off-road tree group. Broad outside space supports a
small encounter or pacing reset; no obstruction at the bend. A shallow lee/damp
pocket gives justified surviving grass while the open bank burns. Orchard cannot
substitute without cultivated rows/barrow; existing rising turns change profile
and height. Variant A has a few distant pasture trees; B has a short transverse
field-boundary remnant well away from the road. No gate, wagon or marker.

**2 — Raised Pasture Bend:** raised open meadow, low ridge on one flank and broad
cross-field views; sparse vegetation and at most a short distant fence fragment.
Outside lawn is usable encounter space, inner shoulder a modest overlook. The
lee stays partly stressed as windward grass chars. Waymark/Fenceline cannot turn,
and Switchback/Verge do not give a level C/C elbow. Two compositions: sparse far
trees versus broken distant pasture boundary. Keep the track visually distinct
from Quiet Hollow Bend in turn timing and bank placement, not just decoration.

**3 — Low Shoulder Climb:** broad grass slope with a shallow side drainage and
small asymmetric shrub/tree pocket; no summit monument. Traversal/reset with
off-road skirmish room; shelter softens local burn while the exposed shoulder
shows advancing damage. Batch1 straight rises preserve their Kind; mixed-profile
turns force a +24 change and direction change. Repeat as up/down conversion when
Kind permits, without inventing a new profile. Geometry earns the source slot.

**4 — Swale Drift:** open shallow valley, track alternately hugs and leaves low
grass banks; few trees on one bank, no paired roadside walls. Provides recovery,
open encounter space and two sightline shifts without changing compass exit.
Damp swale gives a thin coherent refuge through stressed/charred pasture. Clearing
has a near-straight central lawn; Drainage is a transverse culvert event. Variant A
uses a sparse bank grove; B uses distant agricultural strips and almost no trees.
Author the different blade/tree distributions; do not scatter at assembly time.

**5 — Pasture Saddle:** broad descending meadow, one low shoulder and an open
view out; occasional exposed stone, no continuous fence. Supports traversal,
overlook-to-lawn pacing and an ordinary open fight. Burn runs across exposed grass
with a small sheltered lower fold. Fenceline is +16 with a fence-led identity;
repeated reverse mixed-profile turns are not a quiet downhill alternative. Keep
the saddle subtle so it remains connective rather than a named scenic summit.

**6 — Long Ditch Verge:** off-road shallow drainage runs alongside part of the
track, interrupted by ordinary field openings; sparse bank grass and small tree
clumps. Mildly constrained roadside skirmish releases into a wider patch; ditch
is traversable shallow ground, not a new bridge/crossing mechanic. The damp strip
interrupts advancing fire longitudinally. Drainage Crossing's paired culverts and
crosswise dip cannot supply this framing; Fenceline uses raised C pasture. Variant
A is nearly treeless damp margin, B a loose bank group; neither adds culvert props.

**7 — Leeward Grove:** approximately 6–8 ordinary staged trees in unequal
overlapping groups off one side, with a clear opposing flank and open exit.
Compression/release supports a constrained encounter and sheltered reset pocket;
retain current tree family/scale, no dense forest or new vegetation technology.
One protected lee cluster contrasts stressed crowns and charred outer stems.
Orchard's rows and Switchback's line are different spatial grammars. No unique
giant tree, marker or ruin; spacing preserves recognizable composition.

**8 — Abandoned Fieldstead:** compact stone footing and a few broken timber
remnants of a farm shed on one side, adjoining open yard and traces of worked
ground. No complete house, settlement street or outer-wall geometry. Encounter
yard/pause and a rare abandonment story: stressed timber versus actively charred
remnants follows root state, stone persists, lee weeds can survive locally.
Batch1 has no rural building footprint. Once per route, preferably mid/late Area I;
skip it on some routes. Do not combine wagon, waymark and orchard into this place.

**Contract check:** adjacent H0/H0 turns share corner +12; adjacent C0/C0 turns
share −12. A H0/C0 level turn would conflict and is deliberately excluded.
Opposite-edge H0/C12 conversion and C0/C−8 descent share no connected corner;
their other edges/corners are independently source-authored. All pieces remain
256×256 with shared transverse samples, ±12 shoulders, corner agreement,
geometry/socket/collision rotation, hybrid road and no neighbor repair. Preserve
exact Hull seam sampling/cooked fidelity conventions; inexpensive authoring
checks first, then owner walkthrough. Safety barriers remain exposed-edge-only.

## 6. Controlled variant strategy

**Worthwhile for four low sources:** Quiet Hollow Bend, Raised Pasture Bend,
Swale Drift and Long Ditch Verge. Start with one composition each; author a second
restrained, reviewed tree/grass/field-remnant arrangement once terrain is accepted.
Both retain identical terrain, sockets, route/collision and mouth clearances.
Different anchors/refuges may accompany actual changed dressing, sampled through
the same assembly field. Preserve vegetation root/state semantics and accepted
baked scenery approach. Classify any physical dressing at normal packaging time.

These are eight terrain sources plus four optional dressing alternatives, **not
twelve new chunks** and not permanent green/yellow/black mesh classes. QuietBend
and Swale repeat at the same yaw in the long recipe, so their second compositions
have concrete value. Shoulder/Saddle have useful up/down or grade/context changes;
Grove/Fieldstead should gain no variant merely to increase the inventory. Avoid
new variants of Batch1 hero landmarks in this production batch.

## 7. Logical route stress test and limits

`layout_audit.py` runs actual unchanged `ChunkCore.worldSocket/placeAgainst/overlaps`
through the installed Luau CLI. Real Batch1 sockets come from saved-source
readback; proposed sockets are hypothetical metadata. Four explicit recipes,
76 placements total; each checks matching Kind, quarter yaw, no footprint overlap
and source/landmark spacing. Adjacent proposed-corner datums are checked too.
This tests logical capability, not new terrain seams, visual acceptance or combat.
Reproduce: bundled Python `assets/source/worlds/emberfall/batch2/layout_audit.py`;
normal-token Luau may be needed. Full orders/poses/repeats: `layout_audit.json`.

| Recipe | Low / medium / high | Bends / old regular arcs | Net socket rise | Repetition result |
|---|---|---|---|---|
| Batch1 repeated control, 16 | 6 / 8 / 2 | 2 / 2 | +72 | Fits, but repeated Orchard, overused Clearing/Drainage/Ridge, short spacing and repeated three-source motif |
| Hollow countryside, 16 | 11 / 4 / 1 | 4 / 1 | +28 | QuietBend/Clearing/Ditch/Swale repeat; spacing/caps/motif checks pass |
| Mixed elevation, 20 | 13 / 5 / 2 | 5 / 2 | +44 | Saddle three uses, Grove/Fenceline/two quiet sources twice; checks pass |
| Long repeated route, 24 | 18 / 4 / 2 | 5 / 1 | +28 | Eight sources repeat, Swale/Shoulder/Saddle three times; checks pass |

All nine Batch1 sources occur across the exercise. The mixed recipe puts Waymark
at 9 and Wagon at 16; the long recipe puts Fieldstead at 11 and Orchard at 18.
Thus landmark separation need not force blank straight filler or all landmarks.
Initial long recipe repeated QuietBend→Ditch→Clearing; swapping the later ordinary
neighbors broke that motif without new geometry. Baseline is an adversarial
example, not proof that every Batch1-only layout must fail.

- **Turn gestures:** all turns still change socket heading by 90°, as required.
  New bends change interior timing; Swale changes road gesture without topology.
  Ordinary recipes reduce old quarter-circle reliance to 1–2 events. No claim of
  a new 45° socket, hairpin or mirror transform.
- **Elevation:** mixed route includes +24 turns, −8 descents, +16 pasture rises
  and a −12 reverse Shoulder. Long route uses both ±12 conversions and −8 resets
  around a +24 ridge. +28/+44 examples show alternate rhythms; the older roughly
  48–64 overall ascent guidance remains provisional, not forced into each recipe.
- **Open/enclosed pacing:** Grove at 6/17 in mixed and 8/22 in long punctuates
  open pasture; Ditch adds mild bank framing, while Clearing/Swale restore open
  space. Enclosure is still less numerous than open land, appropriate to plains.
  Future fights must leave those reset intervals usable.
- **Burn coherence:** every proposed role permits semantic-depth state at both
  appearances/repeated uses; none hardcodes a front or a green/char class.
  Start remains recently damaged, mid-route advancing front, late-route heavier
  char; damp/lee refuges are local exceptions, not resets. A doubled-back route
  still requires the accepted connected field and coherent surrounding scenery.
  No new field/baked-sector implementation or colour-balance render was tested.
- **Same-source reuse:** logical limits pass even when QuietBend and Swale repeat
  with the same yaw; apply the proposed dressing alternatives. Rotating alone did
  not hide overused Orchard in the control. Actual perception remains unproven
  until new geometry and repeated-source owner walkthrough exist.
- **Remaining weakness:** one quiet H-left and one quiet C-right source still
  bind profile to forward handedness under first-match placement. Mixed-profile
  reverse turns help, but extreme turn-heavy recipes may need one more quiet
  opposing-hand source later. Tree family/stone modularity remains shared;
  vary composition, not the accepted vegetation/scenery strategy.

## 8. Area I sufficiency estimate

**Seventeen sources appear sufficient to begin Area I production and route
authoring; do not pre-author Batch3.** Eight low, five medium (including entry)
and four high sources permit ordinary repeats without nine-piece full-kit cycles.
Sixteen to twenty placements are a useful initial Area I authoring range, with
24 here an intentionally long stress recipe, not a required area length.

Scale review measured 2,140.458 studs for nine sources: about 238 studs/placement.
At current 16.8 studs/s, a rough 12–18 Area I placements means 2.8–4.2 minutes
walking before encounters/exploration; 16–20 means roughly 3.8–4.7. New guide
lengths are unbuilt, so these are planning estimates. A provisional 5–8-minute
Area I leaves time in the overall ~20 minutes for outer-wall transition,
destroyed settlement/shops/houses, castle approach/interior and boss lead-in.
No runtime allocation between areas is locked by this document. The performance
fixture's 36 equivalents is a cost example, not 36 Burned Plains pieces.

A **small later Batch3 of 2–3 sources is conditional**, chiefly if actual Area I
needs more than about 20–24 placements, repeated-source walkthrough still feels
obvious, or missing opposite-handed quiet turns constrain desired recipes.
Likely candidates then: quiet H-right, quiet C-left, or one different constrained
encounter landform selected from real playtest gaps. Outer wall/end transitions,
caps and later-area kits are separate authored roles; they are not silently
counted among these seventeen two-socket countryside sources.

## 9. Implementation order after reset

1. Quiet Hollow Bend and Raised Pasture Bend: solve both level-turn bottlenecks;
   judge their different guide timing together, without new landmarks.
2. Low Shoulder Climb: free profile conversion from a +24 landmark turn and give
   a quiet fall from C. Validate opposite-edge profile geometry cheaply.
3. Swale Drift and Pasture Saddle: break straight-road rhythm and constant climb.
4. Long Ditch Verge: second low H straight, longitudinal framing and damp story.
5. Leeward Grove: add C level shelter and compression/release.
6. Abandoned Fieldstead last: one rare rural story after connective coverage works.
7. Add the four warranted dressing alternatives; assemble one repeated-source
   owner route using the logical recipes. Retain accepted sources until reviewed.

Use the existing source authoring helpers and shared Blender launcher, with fresh
Batch2 output paths. Do not execute Batch1 generators over frozen accepted files.
For each iteration: source/mouth/profile/guide/hash sanity checks → owner visual
test → targeted corrections. Normal export/cooked-collision/CI gates still apply
when production is delivered. No new performance campaign is needed to begin.
Arbitrary-route baked appearance packaging remains the existing rollout item;
it does not block authoring these source-local compositions or justify reopening
EditableMesh, loading, streaming or scenery strategy in this task.

## 10. Repository checkpoint and cleanup

Changed: this plan, `layout_audit.py`, `layout_audit.json`, `source_readback.json`,
root INDEX/INDEX_MAP and narrow WORKLOG/STATUS/Emberfall handoff addenda. Local
checkpoint only on `agent/emberfall-batch2-plan`; final hash/status reported in
chat. No production chunk geometry, Roblox upload, push, merge, PR or main edit.
Owner checkout and all three accepted checkpoints remain untouched.

Python/JSON parsing, accepted nine-source hash comparison, logical recipe assertions,
whitespace and generated-index checks pass. Whole-source StyLua check reproduces
the previously documented unchanged `PropController.luau` finding; no source/test
code changed and no unrelated formatting fix was made. Broad gameplay tests and
CI were not run for this local planning-only checkpoint.

No older production iteration, export or manifest is superseded. Keep all prior
proofs and accepted assets. New external readback/temporary Luau are planning
evidence; retire them only after the plan is preserved and applicable checks pass.
No cleanup deletion is proposed or performed during this audit.

BATCH 2 PLAN READY — implementation can begin.
