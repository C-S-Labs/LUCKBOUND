"""Player-height coverage of every prototype boundary plus scenery asset portraits."""
import bpy
import importlib.util
import json
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
spec = importlib.util.spec_from_file_location('emberfall_architecture', HERE/'revise_emberfall_architecture.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    scene = bpy.data.scenes['Architecture_A']
    bpy.context.window.scene = scene
    root = scene.collection.children[0]
    cameras = next(c for c in root.children if c.name.startswith('Cameras_Lights'))
    coverage = []
    positions = {(int(p[0]/256), int(p[1]/256)): i for i, p in enumerate(study.POSITIONS)}
    for cell, i in positions.items():
        pos = study.POSITIONS[i]
        for side, (nx, ny) in [('N', (0, 1)), ('E', (1, 0)), ('S', (0, -1)), ('W', (-1, 0))]:
            neighbor = (cell[0]+nx, cell[1]+ny)
            if neighbor in positions and positions[neighbor] < i:
                continue
            tx, ty = -ny, nx
            x, y = nx*116-tx*20, ny*116-ty*20
            eye = (pos[0]+x, pos[1]+y, pos[2]+study.playable_height(i, x, y)+4.5)
            target = (pos[0]+nx*158+tx*53, pos[1]+ny*158+ty*53,
                      study.level(pos[1]+ny*158+ty*53)+4.5)
            name = f'seam_eye_{i+1}_{side}'
            camera = study.camera(name, eye, target, cameras, 26)
            scene.camera = camera
            scene.render.filepath = str(OUT/(name+'.png'))
            scene.render.resolution_x = 800
            scene.render.resolution_y = 520
            scene.cycles.samples = 12
            bpy.ops.render.render(write_still=True)
            coverage.append({'image': name+'.png', 'chunk': study.NAMES[i], 'side': side,
                             'neighbor': study.NAMES[positions[neighbor]] if neighbor in positions else 'local scenery',
                             'eye_height_above_authored_floor': 4.5})
    # Separate gallery scene, containing independent art with no arrangement fit.
    gallery = bpy.data.scenes.new('SceneryLibrary_Review')
    bpy.context.window.scene = gallery
    objects = study.coll('Scenery_8_Review_ONLY')
    lighting = study.coll('Gallery_Lights_REVIEW_ONLY')
    source_scene = bpy.data.scenes['Architecture_A']
    gallery.world = source_scene.world
    source_sun = next(o for o in source_scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN')
    sun = source_sun.copy()
    lighting.objects.link(sun)
    gallery.render.engine = 'CYCLES'
    gallery.cycles.samples = 16
    gallery.cycles.use_denoising = True
    gallery.render.resolution_x = 800
    gallery.render.resolution_y = 520
    gallery.view_settings.view_transform = 'AgX'
    for i, name in enumerate(study.SCENERY):
        x, y = i % 4*320, i//4*320
        study.clone_group(bpy.data.collections[name], objects, (x, y, 0), name+'_gallery')
        cam = study.camera('asset_'+name, (x+235, y-240, 225), (x, y, 15), lighting, 38)
        gallery.camera = cam
        gallery.render.filepath = str(OUT/('asset_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
    # All new cameras/gallery objects remain disposable; do not alter saved art.
    (OUT/'visual_coverage.json').write_text(json.dumps(coverage, indent=2), encoding='utf8')
    (HERE/'architecture_visual_coverage.json').write_text(json.dumps(coverage, indent=2), encoding='utf8')
    print('PLAYER_EYE_BOUNDARIES_RENDERED', len(coverage))


if __name__ == '__main__':
    main()
