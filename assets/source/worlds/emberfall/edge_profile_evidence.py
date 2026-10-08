"""Label untouched diagnostic/gameplay renders in one interchangeability sheet."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview')


def main():
    files=sorted(OUT.glob('[01][0-9]_*.png'))
    sheet=Image.new('RGB',(1560,4*395),(23,26,29)); draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    for i,p in enumerate(files):
        im=Image.open(p).convert('RGB');im.thumbnail((514,355))
        x,y=(i%3)*520,(i//3)*395
        sheet.paste(im,(x,y+31));draw.text((x+6,y+5),p.stem.replace('_',' '),font=font,fill=(231,228,212))
    draw.text((1046,1191),'Frozen sources / alternate neighbours',font=font,fill=(231,228,212))
    draw.text((1046,1225),'Visual + collision, quarter rotations',font=font,fill=(231,228,212))
    sheet.save(OUT/'contact_sheet.jpg',quality=92)
    print(str(OUT/'contact_sheet.jpg'))


if __name__=='__main__': main()
