"""Label current Blender render evidence without changing the original renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IMAGES=Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview/VocabularyReview')
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)


def sheet(filename,panels):
    cellw,cellh,caption=600,400,34
    canvas=Image.new('RGB',(cellw*2,((len(panels)+1)//2)*(cellh+caption)),(18,23,29))
    draw=ImageDraw.Draw(canvas)
    for i,(image,label) in enumerate(panels):
        picture=Image.open(IMAGES/(image+'.png')).convert('RGB')
        picture.thumbnail((cellw,cellh))
        x=(i%2)*cellw;y=(i//2)*(cellh+caption)
        canvas.paste(picture,(x+(cellw-picture.width)//2,y))
        draw.text((x+10,y+cellh+5),label,font=FONT,fill=(225,232,238))
    canvas.save(IMAGES/filename)


if __name__=='__main__':
    sheet('vocabulary_contact_sheet.png',[
        ('overview','Current assembled overview'),('assembled_top','Assembled top: route and scenery seams'),
        ('chunk_lineup','Six existing chunks: isolated terrain identities'),('heat_muted_identity','Identity with glow and molten color muted'),
        ('baseline_player_eye','Baseline seam: player eye'),('raised_player_eye','Raised seam: player eye'),
        ('heat_tiny_crack','Tiny heat crack'),('heat_vent_slit','Buried vent slit / cooled roof'),
        ('heat_molten_pocket','Small molten pocket / crust remnant'),('heat_one_sided_fissure','One-sided fissure / asymmetric bank'),
        ('ruin_variety','Eight recent-collapse ruin archetypes'),('basalt_variety','Eight basalt formation archetypes'),
        ('flora_infection_ladder','Four infection states, two shapes each'),('heat_broad_basin','Retained rare broad basin')])
    sheet('heat_vocabulary_sheet.png',[
        ('heat_tiny_crack','Tiny crack'),('heat_medium_crack','Medium crack'),
        ('heat_narrow_seam','Narrow lava seam'),('heat_vent_slit','Buried glow vent'),
        ('heat_molten_pocket','Small molten pocket'),('heat_one_sided_fissure','One-sided fissure'),
        ('heat_contained_channel','Retained contained channel'),('heat_broad_basin','Retained broad basin: rare')])
    print('Two review contact sheets saved; original renders unchanged.')
