"""Create the16 requested revision panels from18 renders; no additional evidence swarm."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageFont
import json

ROOT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/CastleVariantsReview')
report=json.loads((ROOT/'revision_report.json').read_text())
files=[ROOT/(name+'.png') for name in report['views']]
assert len(files)==18 and all(p.exists() for p in files)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
for number,label in [('15','matched_silhouette'),('16','footprint_plan')]:
    canvas=Image.new('RGB',(2560,838),(22,27,31));draw=ImageDraw.Draw(canvas)
    for i,variant in enumerate(['A','B']):
        path=ROOT/(number+variant+'_'+label+'.png')
        with Image.open(path) as im:
            assert im.size==(1280,800);canvas.paste(im,(i*1280,38))
        draw.text((i*1280+12,6),'A — Catastrophe Castle' if variant=='A' else 'B — Fallen Stronghold',font=font,fill='white')
    canvas.save(ROOT/(number+'_'+label+'_comparison.png'))
panels=files[:14]+[ROOT/'15_matched_silhouette_comparison.png',ROOT/'16_footprint_plan_comparison.png']
sheet=Image.new('RGB',(1600,1120),(22,27,31));draw=ImageDraw.Draw(sheet)
small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13)
for i,path in enumerate(panels):
    x=(i%4)*400;y=(i//4)*280
    with Image.open(path) as im:
        thumb=ImageOps.contain(im,(400,250))
        sheet.paste(thumb,(x+(400-thumb.width)//2,y+26+(250-thumb.height)//2))
    draw.text((x+7,y+5),path.stem,font=small,fill='white')
sheet.save(ROOT/'revision_review_sheet.png')
(ROOT/'evidence_manifest.json').write_text(json.dumps({'panels':[str(p) for p in panels],'raw_renders':[str(p) for p in files],'contact_sheet':str(ROOT/'revision_review_sheet.png')},indent=2))
print('18 renders verified;16 final review panels and one sheet saved')
