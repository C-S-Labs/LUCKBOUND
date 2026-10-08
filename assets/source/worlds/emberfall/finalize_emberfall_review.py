"""Convert five authored collection libraries to directly openable local scenes.

Run only through tools/run_blender.py after build_emberfall_prototype.py.
Reads the saved files back to verify actual persisted geometry, not intent.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Euler

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Prototype')
NAMES=['chunk_entry_ash_plain','path_column_pass','chunk_column_forest','side_lava_overlook','cap_collapsed_pass']


def inspect(scene):
    meshes=[o for o in scene.objects if o.type=='MESH']
    counts={}
    for o in meshes:
        o.data.calc_loop_triangles()
        counts[o.name]=len(o.data.loop_triangles)
    return {'scene_all_objects':len(scene.objects),'scene_mesh_objects':len(meshes),'scene_mesh_triangles':sum(counts.values()),
            'mesh_counts':counts,'collections':[c.name for c in scene.collection.children]}


def name_categories(coll,name):
    for c,category in zip(coll.children,('Structure','Props_Solid','Props_NonSolid')):
        c.name=name+'_'+category


def main():
    results={}
    for name in NAMES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path=OUT/(name+'.blend')
        with bpy.data.libraries.load(str(path),link=False) as (source,target):
            assert name in source.collections
            target.collections=[name]
        coll=target.collections[0]
        name_categories(coll,name)
        assert all(o.library is None for o in coll.all_objects)
        for library in list(bpy.data.libraries):
            bpy.data.libraries.remove(library)
        scene=bpy.context.scene;scene.name=name;scene.collection.children.link(coll)
        root=next(o for o in coll.objects if o.type=='EMPTY')
        root.location=(0,0,0)
        structure=bpy.data.objects[name]
        assert tuple(structure.location)==(0,0,0)
        assert len([o for o in scene.objects if o.name in NAMES])==1
        scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    view=area.spaces.active
                    view.region_3d.view_distance=370;view.region_3d.view_location=(0,0,18)
                    view.region_3d.view_rotation=Euler((math.radians(58),0,math.radians(32)),'XYZ').to_quaternion()
                    view.shading.color_type='MATERIAL';view.clip_end=10000
        scene['README']='Independent prototype chunk. Local origin is (0,0,0), no surrounding review land. Not exported.'
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        bpy.ops.wm.open_mainfile(filepath=str(path))
        results[name]=inspect(bpy.context.scene)
        assert tuple(bpy.data.objects[name].location)==(0,0,0)
        assert not any(c.name.startswith('Surround') for c in bpy.data.collections)
        assert not any(n!=name and n in bpy.data.objects for n in NAMES)
        assert results[name]['mesh_counts'][name]<=10000
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    for name in NAMES:name_categories(bpy.data.collections[name],name)
    results['EmberfallPrototype']=inspect(bpy.context.scene)
    assert all(n in bpy.data.objects for n in NAMES)
    assert len([o for o in bpy.context.scene.objects if o.name in NAMES])==5
    scene=bpy.context.scene
    scene.camera=bpy.data.objects['07_flora_library'];scene.camera.data.lens=28
    scene.render.filepath=str(OUT/'07_flora_library.png')
    bpy.ops.render.render(write_still=True)
    scene.camera=bpy.data.objects['06_grounded_region']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    report=json.loads((OUT/'technical_report.json').read_text(encoding='utf8'))
    for row in report['chunks']:
        row['collections']={c.name:[o.name for o in c.objects] for c in bpy.data.collections[row['name']].children}
    (OUT/'technical_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (OUT/'saved_scene_verification.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('PERSISTED_SCENES_VERIFIED',json.dumps({k:(v['scene_mesh_objects'],v['scene_mesh_triangles']) for k,v in results.items()}))


if __name__=='__main__':main()
