"""Assemble focused castle-only impact correction evidence; preserve preceding town views."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json

EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/ImpactCorrectionReview')
report=json.loads((EV/'impact_report.json').read_text())
raw=[EV/(n+'.png') for n in report['views']]
assert len(raw)==12 and all(p.exists() for p in raw)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)
pairs=[('01_A_exterior','02_B_exterior','comparison_exterior'),('03_A_missing_palace','04_B_roofed_palace','comparison_missing_vs_present'),('11A_palace_section','11B_palace_section','comparison_floor_sections')]
for a,b,name in pairs:
 canvas=Image.new('RGB',(2560,840),(22,27,31));draw=ImageDraw.Draw(canvas)
 for i,(n,title) in enumerate([(a,'A - same castle after downward impact'),(b,'B - enclosed palace baseline; no crater')]):
  with Image.open(EV/(n+'.png')) as im:
   assert im.size==(1280,800);canvas.paste(im,(1280*i,40))
  draw.text((i*1280+12,5),title,font=font,fill='white')
 canvas.save(EV/(name+'.png'))
panels=[EV/'comparison_missing_vs_present.png',EV/'comparison_exterior.png']+raw[4:10]+[EV/'comparison_floor_sections.png']
sheet=Image.new('RGB',(1800,1215),(22,27,31));draw=ImageDraw.Draw(sheet);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17)
for i,p in enumerate(panels):
 x=(i%3)*600;y=(i//3)*405
 with Image.open(p) as im:
  thumb=ImageOps.contain(im,(600,375));sheet.paste(thumb,(x+(600-thumb.width)//2,y+30+(375-thumb.height)//2))
 draw.text((x+8,y+6),p.stem,font=small,fill='white')
sheet.save(EV/'impact_review_sheet.png')
(EV/'impact_evidence_manifest.json').write_text(json.dumps({'raw_views':[str(p) for p in raw],'panels':[str(p) for p in panels],'sheet':str(EV/'impact_review_sheet.png')},indent=2))
print('12 castle views verified;9 focused panels/contact sheet saved')
