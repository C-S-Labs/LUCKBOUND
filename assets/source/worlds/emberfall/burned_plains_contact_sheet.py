"""Label eight actual Blender review renders for the Area I handoff."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview')
PANELS = [
    ('01_broad_overview', 'Broad overview / rolling countryside'),
    ('02_top_progression', 'Top / entry bottom; interior top'),
    ('03_baseline_player_eye', 'Baseline eye / 5 studs above road'),
    ('04_opening_edge', 'Opening / surviving field and arriving burn'),
    ('05_mid_plains_active_burn', 'Mid-plains / crossing the advancing front'),
    ('06_interior_edge', 'Interior / char, field gate, two narrow seams'),
    ('07_raised_gradient', 'Raised / surviving -> stressed -> charred'),
    ('08_glow_removed', 'Same raised view / fire and seams hidden'),
]


def main():
    canvas = Image.new('RGB', (1920, 1530), '#171c20')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
    title = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 31)
    draw.text((24, 18), 'EMBERFALL / AREA I - BURNED PLAINS FOUNDATION', font=title, fill='#eeeeea')
    draw.text((24, 59), 'Whole land: 18% green / 31% stressed / 51% charred. Player travels inward; fire spreads toward entry.', font=font, fill='#c9c4b4')
    for i, (file, label) in enumerate(PANELS):
        x = (i % 3) * 640; y = 106 + (i // 3) * 467
        image = Image.open(OUT / (file + '.png')).convert('RGB')
        image = ImageOps.contain(image, (624, 410))
        canvas.paste(image, (x + 8 + (624 - image.width) // 2, y + (410 - image.height) // 2))
        draw.text((x + 12, y + 419), label, font=font, fill='#eeeeea')
    draw.text((1294, 1100), 'AREA I ONLY', font=title, fill='#e5b981')
    draw.text((1294, 1150), 'Three connected 256-stud studies', font=font, fill='#ccccca')
    draw.text((1294, 1190), '56-stud ascent / 24-stud mouths', font=font, fill='#ccccca')
    draw.text((1294, 1230), 'Owner visual acceptance pending', font=font, fill='#ccccca')
    draw.text((1294, 1270), 'No production export or runtime changes', font=font, fill='#ccccca')
    canvas.save(OUT / 'burned_plains_contact_sheet.png')
    print(OUT / 'burned_plains_contact_sheet.png')


if __name__ == '__main__':
    main()
