"""Annotated owner evidence from the focused castle interior review renders."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/InteriorLayoutReview')
FONT='C:/Windows/Fonts/arial.ttf'
def font(n):return ImageFont.truetype(FONT,n)

def label(d,xy,text,color=(245,245,245),size=21):
 f=font(size);box=d.textbbox(xy,text,font=f);d.rectangle((box[0]-6,box[1]-4,box[2]+6,box[3]+4),fill=(22,28,32));d.text(xy,text,font=f,fill=color)

def pair(names,titles,out):
 sheet=Image.new('RGB',(1600,650),(22,28,32));d=ImageDraw.Draw(sheet)
 for k,(name,title) in enumerate(zip(names,titles)):
  im=Image.open(EV/(name+'.png')).convert('RGB');im.thumbnail((790,555));sheet.paste(im,(k*800+(800-im.width)//2,55));label(d,(k*800+15,16),title,size=22)
 sheet.save(EV/out)

def main():
 report=json.loads((EV/'interior_layout_report.json').read_text());im=Image.open(EV/'01_B_floorplan.png').convert('RGB');d=ImageDraw.Draw(im,'RGBA');s=1280/790
 def p(x,y):return (640+(y-1490)*s,450+x*s)
 def rect(bounds,color):
  x0,x1,y0,y1=bounds;a=p(x0,y0);b=p(x1,y1);d.rectangle((*a,*b),fill=(*color,30),outline=(*color,255),width=5)
 rect(report['boss_bounds_studs'],(245,75,64));rect(report['reward_bounds_studs'],(66,210,104))
 points=[p(x,y) for x,y,z in report['primary_route'] if y>=1210];d.line(points,fill=(70,220,250,255),width=7)
 for a,b in zip(points,points[1:]):
  angle=math.atan2(b[1]-a[1],b[0]-a[0]);cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2
  d.polygon([(cx+10*math.cos(angle),cy+10*math.sin(angle)),(cx+10*math.cos(angle+2.5),cy+10*math.sin(angle+2.5)),(cx+10*math.cos(angle-2.5),cy+10*math.sin(angle-2.5))],fill=(70,220,250,255))
 d.line([p(x,y) for x,y,z in report['reward_route_after_boss_only']],fill=(66,210,104,255),width=5)
 for x,y,z in [report['primary_portal'],report['sealed_door']]:
  u,v=p(x,y);d.ellipse((u-8,v-8,u+8,v+8),fill=(255,197,70,255))
 label(d,(25,18),'VARIANT B - GROUND-FLOOR ROUTE / REAR FINALE ROOMS',size=25)
 label(d,(690,660),'FINAL BOSS: ~213 x 224 stud clear center',(255,115,100),19)
 label(d,(785,72),'POST-BOSS LOOT',(95,240,135),20)
 label(d,(845,237),'SEALED LINK',(255,197,70),18)
 label(d,(260,445),'PRIMARY INTERIOR PORTAL',(70,220,250),18)
 label(d,(28,821),'Cyan: primary approach | Green: access only after boss | Gold: portal / sealed door',size=19)
 label(d,(28,855),'Roofs / upper slabs hidden for this plan. No boss, rewards, collision or gate mechanics implemented.',size=17)
 im.save(EV/'B_annotated_floorplan.png')
 pair(['00_B_foundation_before','06_B_foundation_after'],['BEFORE - unplanned open sub-floor void','AFTER - solid plinth; no basement route'],'basement_before_after.png')
 pair(['07_B_matched_section','08_A_matched_section'],['B - enclosed rear boss + adjoining reward room','A - corresponding source architecture removed'],'matched_variant_interiors.png')
 items=[('B_annotated_floorplan','Primary route / final rooms'),('02_B_primary_entrance','One dominant interior portal'),('03_B_progression','Stairs / gallery / boss entry'),('04_B_boss_room','Broad unobstructed combat floor'),('05_B_sealed_loot_connection','Sealed adjoining reward room'),('basement_before_after','Void simplified to solid foundation'),('matched_variant_interiors','A remains derived from B')]
 sheet=Image.new('RGB',(1800,1320),(22,28,32));ds=ImageDraw.Draw(sheet)
 for k,(name,title) in enumerate(items):
  x=(k%3)*600;y=(k//3)*440;pic=Image.open(EV/(name+'.png')).convert('RGB');pic.thumbnail((588,378));sheet.paste(pic,(x+(600-pic.width)//2,y+45));label(ds,(x+10,y+13),title,size=18)
 sheet.save(EV/'interior_review_sheet.png')
 print('7 review panels, annotated plan, paired foundation / variant evidence')
if __name__=='__main__':main()
