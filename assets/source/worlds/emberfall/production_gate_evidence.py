"""Prepare the gate contact sheet without changing source evidence."""
import json
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
out=Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview')
here=Path(__file__).parent
report=json.loads((here/'production_gate_report.json').read_text())
sheet=Image.new('RGB',(1500,744),(24,24,24))
draw=ImageDraw.Draw(sheet)
for i,path in enumerate(report['evidence']):
    image=Image.open(path).convert('RGB'); image.thumbnail((500,334))
    x=(i%3)*500; y=(i//3)*372
    sheet.paste(image,(x,y)); draw.text((x+8,y+341),Path(path).stem,fill='white')
sheet.save(out/'production_gate_contact_sheet.jpg',quality=92)
shutil.copyfile(here/'production_gate_studio_report.json',out/'production_gate_studio_report.json')
print('Six views and Studio report prepared')
