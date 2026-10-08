"""Assemble one labelled review sheet and summary from actual Blender reports."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Prototype')
HERE=Path(__file__).resolve().parent
report=json.loads((OUT/'technical_report.json').read_text(encoding='utf8'))
saved=json.loads((OUT/'saved_scene_verification.json').read_text(encoding='utf8'))
panels=[('01_entry','ENTRY / calm ash shelf'),('02_column_pass','PATH / jointed column walls'),
        ('03_column_forest','COMBAT / three height bands'),('04_lava_overlook','SIDE / outward land-and-lava view'),
        ('05_collapsed_pass','CAP / rockfall inside the old road'),('06_grounded_region','REVIEW ONLY / continuous surrounding land'),
        ('07_flora_library','FLORA / two drained + two charred variants'),('08_side_shelf','SIDE / single approach, broad upper shelf')]
font_path='C:/Windows/Fonts/segoeui.ttf'
font=ImageFont.truetype(font_path,20)
heading=ImageFont.truetype(font_path,32)
sheet=Image.new('RGB',(1800,1330),(22,28,34));draw=ImageDraw.Draw(sheet)
draw.text((24,16),'EMBERFALL / five-piece prototype review',font=heading,fill=(221,222,213))
for j,(file,label) in enumerate(panels):
    x=j%3*600;y=70+j//3*420
    im=Image.open(OUT/(file+'.png')).convert('RGB');im.thumbnail((592,383))
    sheet.paste(im,(x+4,y));draw.text((x+10,y+386),label,font=font,fill=(208,212,212))
draw.text((1220,950),'5 independent chunks\n256 x 256 studs each\n56-stud level mouths\n4 linked flora species\nReview terrain is separate\nNo runtime export / upload',font=font,fill=(208,212,212),spacing=14)
sheet.save(OUT/'emberfall_review_sheet.png')

lines=['# Emberfall — five-chunk prototype review','',
       'Owner-directed 2026-10-02. Reviewable Blender prototype only; no production registration, export, upload, commit or push.',
       '', '## Open the result','',
       '- Main scene: `E:/BlenderAIProjects/Runtime/Emberfall_Prototype/EmberfallPrototype.blend`.',
       '- Five independent `.blend` scenes are in that same folder, named exactly as the chunks below. Each is centered at (0,0,0) and contains only its own structure and props.',
       '- `emberfall_review_sheet.png` compares all five concepts, surrounding land and flora. Eight individual images are alongside it.',
       '- `technical_report.json` contains actual mesh bounds, origins, socket samples, collection membership, flora and triangle counts. `saved_scene_verification.json` records persisted-file readback.',
       '', '## Actual Blender counts','',
       'Blender 5.2.2 LTS; metric scale 1.0. Dimensions below are Blender X × Y × Z; Roblox equivalents are X × height × depth.',
       'Counts include separated props/flora instances; structural triangle counts alone are subject to the 10,000-per-piece contract. Every individual prop is also below 10,000.',
       '', '| Chunk / inferred role | Mesh / all objects | Structure tris | All mesh tris | Dimensions | Mouths |',
       '|---|---:|---:|---:|---|---|']
for row in report['chunks']:
    dim=' × '.join(f'{d:g}' for d in row['dimensions_xyz'])
    mouths=', '.join(o['side'] for o in row['socket_probes'])
    lines.append(f"| `{row['name']}` / {row['role']} | {row['mesh_objects']} / {row['all_objects']} | {row['structure_triangles']:,} | {row['total_mesh_triangles']:,} | {dim} | {mouths} |")
scene=saved['EmberfallPrototype'];sur=report['review_surround']
lines += ['',f"Main review scene: **{scene['scene_all_objects']} objects / {scene['scene_mesh_objects']} meshes / {scene['scene_mesh_triangles']:,} triangles**, including four hidden library originals, four displayed library references, five scale proxies, and review land.",
          f"Review-only surrounding land: **{sur['objects']} mesh objects / {sur['mesh_triangles']:,} triangles**; continuous fitted ash/cooled-lava collar, continental base, distant jagged ridges, one large lava field and seven cooled-flow forms.",
          '', '## Chunk designs','']
for row in report['chunks']:lines += [f"- **{row['name']}**: {row['design']}"]
lines += ['', '## Collection and prop contract','',
          '`EF_PROTOTYPE_5_CHUNKS` contains exactly five named chunk collections. Each has a review-position parent empty and three explicitly named subcollections: `<chunk>_Structure`, `<chunk>_Props_Solid`, `<chunk>_Props_NonSolid`.',
          'Each structure is one mesh with the exact requested chunk name; each solid group is one `prop_*` mesh. The four `prop_*` library originals live in `PropLibrary` and are hidden; placements share their mesh data. Flora is Static, Tier 2, solid=false. Solid rubble/mineral specimens are Static, Tier 1, solid=true.',
          '`Surround_REVIEW_ONLY` is separate and never included in independent chunks. `Cameras_Lights_REVIEW_ONLY` holds cameras, lighting, scale proxies and the flora display. The two PATH preview lights also carry ReviewOnly=true and are not gameplay content.',
          'No Role override: naming infers ENTRY, PATH, COMBAT, SIDE and CAP. No GateSide or Weight override. Explicit Openings are authoring metadata for all five because high/sunken centers can confuse the auto-probe median; PATH Supports=Traversal,Ambush and COMBAT Supports=Combat,Ambush narrow the generous defaults to the authored intent. Studio transfer is still a future manual step.',
          '', '## Validation and visual review','',
          '- Exactly five requested structural objects; persisted individual files each contain exactly one, with no other chunk or surrounding land.',
          '- All origins are (0,0,0) in the authored frame, with unit scale 1.0. Main-scene translations belong to parent empties. Every footprint measures exactly 256 × 256; no chunk/prop/flora vertex exceeds ±128 horizontally.',
          '- Eight mouths: each tested with 20 actual mesh raycasts across the 56-stud width and first 16 studs of depth. All floor samples equal 0.0, with no overhead geometry detected by those top-down rays. This is targeted Blender sampling, not Roblox cooked-collision verification.',
          '- ENTRY has broad calm open ground, just four low formations and a 7.38-square-stud heat hairline. PATH has about 324.11 square studs of molten ribbon, COMBAT about 133.92; SIDE has only a thin deep-heat accent and CAP no ground lava. Lava concentration differs substantially.',
          f"- COMBAT has a 48 × 64 central floor patch checked at 25 mesh samples, unobstructed by columns and gently sloped; surrounding clearings and connecting lanes add room. The gently sloped terrain area (before cover) is {report['chunks'][2]['gently_sloped_upward_surface_projected_area']:,.0f} square studs. Basalt groups interrupt sightlines around, rather than across, this hub.",
          '- PATH rises broadly to about +12 internally; COMBAT lower basin/main/upper flank are roughly -10/0/+16; SIDE reaches +26 on its broad overlook and +35 on its outer ridge. All return to connection height 0. No tiny mandatory jump ledges.',
          '- CAP collapse sits around local Y=30–75, well before the +128 boundary. Oblique columns and rockfall seal an old road, with a road remnant visible beyond and an ember-flower nook before it. SIDE has only a west mouth and ends at its overlook/mineral landmark, distinguishing it from a through-route.',
          '- Grounded presentation reviewed in the overall, arrival, pass and elevated side cameras: the fitted review terrain hides vertical skirts and continues to ridges and lava fields. No sky beneath the authored route in those views. Exhaustive escape-camera or runtime surround validation is not claimed.',
          '- Both flora families are present, using different species mixes in each chunk. Geometry includes curved layered petals, wax leaves, seed shrubs, beveled hexagonal columns and irregular fracture collars; smooth terrain/flora and restrained procedural bump detail test the less restrictive style. The close basalt remains deliberately stylized and may still need owner-directed weathering.',
          '', '## Technical compromises / pending owner checks','']
lines += ['- '+issue for issue in report['issues']]
lines += ['- Distant ridges and the large lava field are intentionally crude silhouette/context tests. Review terrain is not a runtime surrounding-land solution. Some upper shelves use slopes that still require an owner movement check before production.',
          '- Blender native partial scene-library writing crashed in BKE_view_layer_copy_data. The workaround writes collection libraries, then appends each into a clean scene and saves normally; all five were reopened successfully. No launcher bypass or Blender binary change.',
          '- Normal-token protected launcher was required after the restricted Windows profile lookup refused execution.',
          '', '## Reproduce','',
          'Run `build_emberfall_prototype.py`, then `finalize_emberfall_review.py` through the repository shared `tools/run_blender.py` launcher with factory startup. Run `review_emberfall_prototype.py` with the bundled Python/Pillow runtime to assemble this sheet and report. There is no FBX export path or production write in these scripts.',
          '', '## Leftover cleanup','',
          'No production asset, export, manifest or earlier biome iteration was superseded. Blender-created `.blend1` backups in the prototype folder retain preceding review saves/collection libraries; keep them until owner acceptance and applicable CI/Studio validation, then remove only the unneeded prototype backups. Keep the main scene, five independent scenes, reports, scripts and references. No second batch until owner approval.']
text='\n'.join(lines)+'\n'
(HERE/'PROTOTYPE_REVIEW.md').write_text(text,encoding='utf8')
(OUT/'PROTOTYPE_REVIEW.md').write_text(text,encoding='utf8')
for filename in ('technical_report.json','saved_scene_verification.json'):
    (HERE/filename).write_bytes((OUT/filename).read_bytes())
print('Review sheet and actual-count summary written.')
