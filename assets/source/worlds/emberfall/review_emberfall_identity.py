"""Read actual saved identity revision; correct close-up framing, no art edits."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
RENDERS = OUT/'IdentityReview'


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    scene = bpy.data.scenes['Architecture_A']
    bpy.context.window.scene = scene
    bpy.context.view_layer.update()
    for name, prefix, offset in [('identity_flora_half_takeover', 'prop_path_column_pass_takeover_50', (7, -10, 7)),
                                 ('identity_flora_progression', 'prop_chunk_entry_ash_plain_takeover_OLD', (9, -12, 9))]:
        plant = next(o for o in scene.objects if o.name.startswith(prefix))
        target = plant.matrix_world.translation+Vector((0, 0, 1.7))
        camera = next(o for o in scene.objects if o.name == name)
        camera.location = target+Vector(offset)
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.lens = 48
        scene.camera = camera
        scene.render.filepath = str(RENDERS/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        if name == 'identity_flora_half_takeover':
            settings = []
            for mat in bpy.data.materials:
                if mat.name in ('Ember_Molten', 'Ember_DeepHeat', 'Ember_FreshBreakHeat'):
                    node = mat.node_tree.nodes['Principled BSDF']
                    settings.append((node, tuple(node.inputs['Base Color'].default_value), node.inputs['Emission Strength'].default_value))
                    node.inputs['Base Color'].default_value = (.016, .02, .023, 1)
                    node.inputs['Emission Strength'].default_value = 0
            lights = [(o.data, o.data.energy) for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'POINT']
            for light, energy in lights:
                light.energy = 0
            scene.render.filepath = str(RENDERS/(name+'_heat_dark.png'))
            bpy.ops.render.render(write_still=True)
            for node, color, strength in settings:
                node.inputs['Base Color'].default_value = color
                node.inputs['Emission Strength'].default_value = strength
            for light, energy in lights:
                light.energy = energy
    scene.camera = bpy.data.objects['identity_elevated_overview']
    gallery = bpy.data.scenes['FloraSpectrum_REVIEW_ONLY']
    bpy.context.window.scene = gallery
    gallery.camera = bpy.data.objects['flora_spectrum']
    gallery.camera.data.lens = 28
    gallery.render.filepath = str(RENDERS/'flora_spectrum.png')
    bpy.ops.render.render(write_still=True)
    bpy.context.window.scene = scene
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    report = json.loads((HERE/'identity_technical_report.json').read_text(encoding='utf8'))
    report['flora_state_readback'] = [{
        'name': o.name, 'state': o.get('FloraState'), 'fraction': o.get('InfectedSurfaceFraction'),
        'derived_from': o.get('DerivedFrom')}
        for o in bpy.data.collections['Flora_Takeover_States'].objects]
    report['current_materials'] = [m.name for m in bpy.data.materials]
    report['max_source_mesh_triangles'] = max(max(r['mesh_triangles'].values()) for r in report['assets_after'].values())
    assert report['max_source_mesh_triangles'] < 10000
    report['closeups_reframed_from_actual_plant_world_positions'] = True
    (HERE/'identity_technical_report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    (RENDERS/'identity_technical_report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print('IDENTITY_CLOSEUPS_AND_READBACK_READY', report['after_saved_readback'])


if __name__ == '__main__':
    main()
