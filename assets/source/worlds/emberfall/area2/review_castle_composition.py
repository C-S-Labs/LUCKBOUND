"""Focused castle architecture/flat-arena evidence assembly."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json
EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/BaselineArchitectureReview')
report=json.loads((EV/'architecture_report.json').read_text());raw=[EV/(n+'.png') for n in report['views']]
assert len(raw)==9 and all(p.exists() for p in raw)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)
for names,label in [(('01_B_irregular_overview','05_A_derived_overview'),'matched_massing'),(('08_B_baseline_section','09_A_derived_section'),'matched_architecture_removed')]:
 canvas=Image.new('RGB',(2560,840),(22,27,31));draw=ImageDraw.Draw(canvas)
 for j,(n,title) in enumerate(zip(names,['B - damaged irregular castle baseline','A - directly derived impact / shallow arena'])):
  with Image.open(EV/(n+'.png')) as im:
   assert im.size==(1280,800);canvas.paste(im,(1280*j,40))
  draw.text((1280*j+12,5),title,font=font,fill='white')
 canvas.save(EV/(label+'.png'))
panels=raw[:7]+[EV/'matched_massing.png',EV/'matched_architecture_removed.png']
sheet=Image.new('RGB',(1800,1215),(22,27,31));draw=ImageDraw.Draw(sheet);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17)
for k,p in enumerate(panels):
 x=(k%3)*600;y=(k//3)*405
 with Image.open(p) as im:
  thumb=ImageOps.contain(im,(600,375));sheet.paste(thumb,(x+(600-thumb.width)//2,y+30+(375-thumb.height)//2))
 draw.text((x+8,y+5),p.stem,font=small,fill='white')
sheet.save(EV/'castle_architecture_review_sheet.png')
(EV/'architecture_evidence_manifest.json').write_text(json.dumps({'raw_views':[str(p) for p in raw],'panels':[str(p) for p in panels],'sheet':str(EV/'castle_architecture_review_sheet.png')},indent=2))
print('9 raw views /9 focused review panels verified')
