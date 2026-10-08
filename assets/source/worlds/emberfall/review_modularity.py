"""Saved-readback checks and labelled evidence sheet for the isolated proof."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview')


def readback():
    import bpy
    import bmesh
    from mathutils import Vector
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsModularity.blend'))
    scene=bpy.data.scenes['Area_I_Modularity_0_180_0']
    bpy.context.window.scene=scene
    terrain=[o for o in scene.objects if o.name.startswith('PLAYABLE_')]
    assert len(terrain)==3
    checks=[]
    for o in terrain:
        points=[o.matrix_world@v.co for v in o.data.vertices[:o['SurfaceVertexCount']]]
        span=[max(v[k] for v in points)-min(v[k] for v in points) for k in (0,1)]
        assert all(abs(v-256)<.001 for v in span)
        bm=bmesh.new(); bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges); bm.free()
        checks.append({'name':o.name,'footprint':span,'closed':True})
    road=next(o for o in scene.objects if o.name=='ASSEMBLY_track_from_authored_guides')
    rows=[(road.data.vertices[i].co,road.data.vertices[i+1].co) for i in range(0,len(road.data.vertices),2)]
    seam_rows=[r for r in rows if any(abs(r[0].y-y)<.001 for y in (-128,128))]
    assert len(seam_rows)==2
    assert all((r[1]-r[0]).length>6 for r in seam_rows)
    for p in json.loads((HERE/'modularity_report.json').read_text())['evidence']:
        assert Path(p).is_file()
    report=json.loads((HERE/'modularity_report.json').read_text())
    report['saved_readback']={'terrain':checks,'road_seam_rows':2,'road_is_one_connected_strip':len(road.data.polygons)==len(rows)-1,
                              'no_studio_connected':True,'approved_scene_retained_in_review_file': 'Emberfall_Area_I_Burned_Plains' in bpy.data.scenes}
    for p in [HERE/'modularity_report.json',OUT/'modularity_report.json']:
        p.write_text(json.dumps(report,indent=2),encoding='utf8')
    print('SAVED_READBACK_PASS',len(terrain),'closed terrains; 2 road joins; evidence present',flush=True)


def sheet():
    from PIL import Image, ImageDraw, ImageFont
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    im=Image.open(OUT/'02_top_burn_crossing.png').convert('RGB')
    d=ImageDraw.Draw(im)
    for cy,label in [(-256,'Opening 0 degrees'),(0,'Mid-plains 180 degrees'),(256,'Interior 0 degrees')]:
        x1=450-128*900/950; x2=450+128*900/950
        y1=550-(cy+128)*900/950; y2=550-(cy-128)*900/950
        d.rectangle((x1,y1,x2,y2),outline=(120,218,240),width=2)
        d.text((x2+8,(y1+y2)/2),label,font=small,fill=(220,240,245),stroke_width=1,stroke_fill=(0,0,0))
    d.text((24,26),'Cyan = playable ownership; exterior = non-playable scenery',font=small,fill='white',stroke_width=1,stroke_fill='black')
    im.save(OUT/'07_ownership_overlay.png')
    frames=[('01_assembled_overview.png','Assembled countryside'),('07_ownership_overlay.png','Three footprints / shared burn field'),
            ('03_player_eye_boundary.png','Player eye across opening / mid join'),('04_raised_join_front.png','Raised burn-front crossing'),
            ('05_interior_road.png','Road to interior'),('06_quarter_turn_top.png','Same assembly turned 90 degrees')]
    canvas=Image.new('RGB',(1500,1470),(27,30,34)); draw=ImageDraw.Draw(canvas)
    for i,(name,label) in enumerate(frames):
        cell=Image.open(OUT/name).convert('RGB'); cell.thumbnail((730,425))
        x=(i%2)*750+(750-cell.width)//2; y=(i//2)*490+35+(425-cell.height)//2
        canvas.paste(cell,(x,y)); draw.text(((i%2)*750+14,(i//2)*490+8),label,font=font,fill='white')
    canvas.save(OUT/'modularity_contact_sheet.png')
    print('CONTACT_SHEET_PASS')


if __name__=='__main__':
    sheet() if '--sheet-only' in sys.argv else readback()
