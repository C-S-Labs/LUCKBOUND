# Crossroads V2 sky creatures, group `mid`

`build_mid.py` builds four flyers (contract: `docs/design/SKY_ECOSYSTEM_CONTRACT.md` s2, s3, s4.1) and writes
`assets/export/hub/crossroads/creatures_mid.fbx` + `creatures_mid.json`.

    python tools/run_blender.py -b --factory-startup --python <abs path>/build_mid.py -- --export --render [--only id,id]

| id | class | biome | extent (studs, rest pose) | tris | parts |
|---|---|---|---|---|---|
| `citadel_falcon` | MEDIUM | Sky Citadel | 28.6 x 29.5 x 9.6 | 1904 | 9 |
| `canopy_drake` | MEDIUM | Verdant | 34.9 x 32.8 x 10.0 | 1784 | 14 |
| `aether_manta` | LARGE | Ethereal Scape | 90.6 x 96.0 x 15.8 | 1208 | 14 |
| `ashen_roc` | LARGE | Emberfall | 99.5 x 105.8 x 33.0 | 2496 | 11 |

Conventions
- Head +X, up +Z, pivot at the body mesh's bounding-box centre; every mesh < 10k tris (max 588).
- Sidecar `size` is the WHOLE creature at rest (body + parts), mapped like `Content` `Size` (`[x, z, y]` of Blender),
  because the contract's class ranges describe the creature, not the torso. Body-only sizes are in the build log.
- `offset`, `hinge`, `axis` use the exact `OrbiterParts` maths of `make_layout_luau.py` (importer half turn,
  relative to the body bbox centre), so a generator can copy them straight in.
- Mirrored wings use phase 0 / pi so both rise together. `Flap` rate = Hz, amp = rad. `Pulse` (breathing): amp is a
  fractional scale about `hinge`. `Flicker`: glow shards, rate Hz.
- `chain` = hinge parent (wing -> wingtip -> ...; neck -> head; tail segments; manta fin -> fin -> fin), `lag` = phase
  lag behind it. Large creatures: slow deep beats (manta 0.18 Hz, roc 0.22 Hz, falcon 0.9 Hz).
- Palette: existing hub names, plus species-local entries defined in `build_mid.py` (VerdMoss/VerdLeaf/VerdDeep,
  AshPlate/AshChar/AshLight, PearlFin/PearlDeep/Dusk). The kit's REFINISH pass is switched off for these meshes.
- The drake's back between the shoulders is a flat, clear moss patch (room for a future saddle).
- `renders/contact_sheet.png`: rows from the TOP are roc, manta, drake, falcon (image is stacked bottom-up);
  columns: 3/4 view, side, top, underside.
