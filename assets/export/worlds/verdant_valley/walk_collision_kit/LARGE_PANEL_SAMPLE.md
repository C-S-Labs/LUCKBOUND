# Large merged-panel spot check

Run against the 3,454-collider Studio kit on 2026-09-28, before the Entry Dawn
Meadow and Boss Sanctuary panel replacements. "Large" means a merged panel of
at least eight original 16-stud cells. There were 57 such panels. After sorting
by model and part name, a `Random.new(20260928)` shuffle selected 15 panels
(26.3%). Each selected panel was cloned alone into Workspace and hit with 25
downward rays at five positions along each horizontal axis, including points
near its edges. A local low-hit check compared each interior sample with its
horizontal neighbors. This is a spot check, not a full physics validation.

All 15 randomly selected panels had 25/25 ray hits and no interior point more
than 0.20 stud below both horizontal neighbors:

| Model | Panel |
|---|---|
| Entry Dawn Meadow | `walk_patch_+032_-096_2x4` |
| Overgrown Causeway Gate | `walk_patch_+000_-048_3x3` |
| Blossom Terrace | `walk_patch_+000_-032_3x4` |
| Crossroads Copse | `walk_patch_-112_-016_4x2` |
| Cliff Overlook Gate | `walk_patch_+032_+000_3x3` |
| Cutbank Ford | `walk_patch_-032_-048_3x3` |
| Shaded Grove | `walk_patch_-032_-016_4x2` |
| Fern Hollow | `walk_patch_-016_-128_2x4` |
| Boss Sanctuary | `walk_patch_-096_+048_4x3` |
| Ancient Oak | `walk_patch_-016_-032_2x4` |
| Treasure Hollow | `walk_patch_+000_-080_4x4` |
| Fern Hollow | `walk_patch_-016_+064_2x4` |
| Cave Mouth | `walk_patch_+000_-048_3x3` |
| Treasure Hollow | `walk_patch_-032_+016_5x2` |
| Wardens Clearing | `walk_patch_-016_+048_2x5` |

The two owner-reported panels were checked separately. Boss Sanctuary's
`walk_patch_-032_+016_6x5` missed one of 25 rays at approximately local Roblox
`(-63.4, 56)`. Entry Dawn Meadow's `walk_patch_-016_+064_2x4` hit all 25
initial samples, but a closer socket-edge probe found a hit at local Roblox
`(12, 127.8)` about 0.35 stud below adjacent hits. Both panels were therefore
split locally. The random sample does not establish that every other large
panel is safe, but it does not justify changing the kit-wide merge limit yet.
