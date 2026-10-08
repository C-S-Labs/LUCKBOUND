"""Five compact owner comparison panels for the structural cleanup."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/StructuralCleanupReview')
FONT='C:/Windows/Fonts/arial.ttf'
ROWS=[('roof_supports','Roof bearings / upper keep infill'),('entrance_gaps','Entrance haunch gaps closed'),('burned_beams','Burned ribs connected / fallen beam seated'),('perimeter_damage','Localized curtain / tower-crown damage')]
for name,title in ROWS:
 im=Image.new('RGB',(1600,620),(23,29,33));d=ImageDraw.Draw(im)
 for k,stage in enumerate(['before','after']):
  pic=Image.open(EV/(name+'_'+stage+'.png')).convert('RGB');pic.thumbnail((790,545));im.paste(pic,(k*800+(800-pic.width)//2,58));d.text((k*800+15,17),stage.upper()+' - '+title,font=ImageFont.truetype(FONT,20),fill=(243,243,243))
 im.save(EV/(name+'_comparison.png'))
im=Image.new('RGB',(1600,620),(23,29,33));d=ImageDraw.Draw(im)
for k,(name,title) in enumerate([('roof_supports_after','B baseline - restored support'),('A_derived_supports_after','A - same support sources cut by impact')]):
 pic=Image.open(EV/(name+'.png')).convert('RGB');pic.thumbnail((790,545));im.paste(pic,(k*800+(800-pic.width)//2,58));d.text((k*800+15,17),title,font=ImageFont.truetype(FONT,22),fill=(243,243,243))
im.save(EV/'matched_support_derivation.png')
sheet=Image.new('RGB',(1600,960),(23,29,33))
for k,name in enumerate([a+'_comparison' for a,b in ROWS]+['matched_support_derivation']):
 pic=Image.open(EV/(name+'.png'));pic=pic.resize((800,310));sheet.paste(pic,((k%2)*800,(k//2)*320))
sheet.save(EV/'structural_review_sheet.png')
print('Five comparison panels; four before/after pairs and matched B/A support derivation')
