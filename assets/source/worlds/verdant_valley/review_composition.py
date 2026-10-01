"""Render isolated chunk overhead and route-height views without saving scene changes."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector
import importlib.util


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    spec = importlib.util.spec_from_file_location('vv_detail', Path(__file__).with_name('detail_composition.py'))
    detail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(detail)
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    shade = scene.display.shading
    shade.light = 'STUDIO'
    shade.color_type = 'MATERIAL'
    shade.show_shadows = True
    shade.show_cavity = True
    shade.cavity_type = 'WORLD'
    shade.background_type = 'WORLD'
    scene.world.color = (0.24, 0.26, 0.25)
    scene.view_settings.view_transform = 'Standard'
    camera = bpy.data.objects.new('CompositionReviewCamera', bpy.data.cameras.new('CompositionReviewCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.clip_end = 10000
    objects = list(bpy.data.objects)
    chunks = sorted(bpy.data.collections['VV_STRUCTURE'].objects, key=lambda o:o.name)
    if '--kit' in args:
        prefixes=tuple(o.name+'__' for o in chunks)
        for o in objects:
            o.hide_render=not (o in chunks or o.name.startswith(prefixes)) or any('COLLISION' in c.name for c in o.users_collection)
        camera.location=(0,0,3000)
        camera.rotation_euler=(0,0,0)
        camera.data.ortho_scale=2500
        scene.render.resolution_x=2000
        scene.render.resolution_y=1700
        scene.render.filepath=str(out/'whole_kit.png')
        bpy.ops.render.render(write_still=True)
        return
    for chunk in chunks:
        if len(args) > 1 and chunk.name not in args[1:]:
            continue
        for o in objects:
            o.hide_render = not (o == chunk or o.name.startswith(chunk.name + '__')) or any('COLLISION' in c.name for c in o.users_collection)
        for view in ('top', 'route', 'detail'):
            center = chunk.location + Vector((0, 0, 8))
            sockets = next((row[2] for row in detail.EXPECTED.values() if row[0]==chunk.name), {'N':'PATH'})
            horizontal = all(s in ('E','W') for s in sockets)
            camera.location = center + (Vector((0, 0, 500)) if view == 'top' else Vector((-180,0,24)) if horizontal else Vector((0,-180,24)))
            target = center if view == 'top' else chunk.location + Vector((0, 12, 8))
            if view=='detail':
                feature = next((o for o in objects if o.name.startswith(chunk.name+'__composition_001')),None)
                target = feature.location + Vector((0,0,2)) if feature else center
                camera.location = target + Vector((19,-30,7))
            camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
            camera.data.type = 'ORTHO' if view == 'top' else 'PERSP'
            camera.data.ortho_scale = 420 if 'boss_' in chunk.name else 295
            camera.data.lens = 28
            scene.render.filepath = str(out / (chunk.name + '_' + view + '.png'))
            bpy.ops.render.render(write_still=True)
    print('COMPOSITION_REVIEW_COMPLETE', out)


if __name__ == '__main__':
    main()
