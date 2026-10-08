from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
def sheet(items,path,cols,w=480,h=365):
    canvas=Image.new('RGB',(cols*w,((len(items)+cols-1)//cols)*h),(23,28,30));d=ImageDraw.Draw(canvas)
    for i,(image,label) in enumerate(items):
        im=Image.open(image).convert('RGB');im.thumbnail((w,h-34));x=i%cols*w;y=i//cols*h;canvas.paste(im,(x+(w-im.width)//2,y));d.text((x+10,y+h-30),label,font=font,fill='white')
    canvas.save(path)
items=[];eye=[]
for lane in ('countryside','elevations','fields'):
    for r in json.loads((OUT/lane/'manifest.json').read_text()):
        label=r['title']+' | '+str(r['collision_parts'])+' collision'
        items.append((OUT/'individual'/(r['id']+'_overview.png'),label));eye.append((OUT/'individual'/(r['id']+'_eye.png'),r['title']))
sheet(items,OUT/'kit_contact_sheet.jpg',3)
sheet(eye,OUT/'kit_player_views.jpg',3)
items=[(OUT/('Layout'+str(i))/(name+'.png'),'Layout '+str(i)+' — '+name.replace('_',' ')) for i in (1,2,3) for name in ('overview','route_top','player_eye','raised_gameplay','reachable_high_point')]
sheet(items,OUT/'layouts_contact_sheet.jpg',5,w=400,h=315)
sheet([(OUT/'Layout1'/(name+'.png'),name.replace('_',' ')) for name in ('seam_road','collision_seam','active_front')],OUT/'technical_contact_sheet.jpg',3)
print('Four evidence sheets ready')
