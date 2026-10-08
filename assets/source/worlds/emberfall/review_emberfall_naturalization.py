"""Focused current-scene finishing, alternate joins and cheap saved readback."""
import bpy
import bmesh
import importlib.util
import json
import math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
IMAGES=OUT/'NaturalizationReview'
MAIN=OUT/'EmberfallFoundation.blend'


def module(file,name):
    s=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def road_fragments(root,terrain,helper,study):
    old=[o for o in root.children if o.name.startswith('road_remnant')]
    if not old:
        return
    for o in old:
        bpy.data.objects.remove(o,do_unlink=True)
    name=study.family(terrain)
    ys=[-68,49] if 'entry_' in name or 'path_wasteland_' in name else [42] if 'side_' in name else [-69,7,78]
    collection=root.users_collection[0]
    for j,y in enumerate(ys):
        # Broad interrupted buried road foundation, not a repeated pair of pavers.
        outline=[(-13,y-15),(-4,y-18),(11,y-12),(15,y+3),(8,y+17),(-9,y+13),(-16,y+4)]
        top=[(x,yy,study.ground(terrain,x,yy)+.025) for x,yy in outline]
        n=len(top)
        vs=top+[(x,yy,z-.8) for x,yy,z in top]
        fs=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
        helper.mesh('buried_broken_road_foundation',vs,fs,[bpy.data.materials['EF_WeatheredCivilization']],collection,root)


def alternate_pair(scene,helper,study,left,right,name,raised=False):
    test=bpy.data.scenes.new('SeamCombination_'+name+'_REVIEW_ONLY')
    test.world=scene.world
    test.render.engine='CYCLES'
    test.cycles.samples=16
    test.cycles.use_denoising=True
    test.render.resolution_x=1000
    test.render.resolution_y=680
    test.view_settings.view_transform='AgX'
    test.unit_settings.system='METRIC'
    test.unit_settings.scale_length=1
    c=bpy.data.collections.new('Join_'+name+'_REVIEW_ONLY')
    test.collection.children.link(c)
    roots=[]
    for index,chunk in enumerate((left,right)):
        old=bpy.data.objects[chunk+'_ORIGIN']
        root=old.copy()
        c.objects.link(root)
        root.location.y=(-128,128)[index]
        if chunk.startswith('path_fortress'):
            root.location.z=28
        elif raised:
            root.location.z=56
        else:
            root.location.z=0
        clones={old:root}
        # Include nested wall-course details without changing the current layout.
        descendants=list(old.children_recursive)
        for ob in descendants:
            clone=ob.copy()
            c.objects.link(clone)
            clones[ob]=clone
        for ob in descendants:
            clones[ob].parent=clones.get(ob.parent,root)
        roots.append(root)
    sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN').copy()
    c.objects.link(sun)
    oldreview=helper.REVIEW
    helper.REVIEW=c
    height=56 if raised else 0
    shots=[('top',(0,0,750),(0,0,height),32,650),
           ('eye',(0,-26,height+4.5),(-8,56,height+2),28,None),
           ('oblique',(100,-72,height+31),(-6,15,height+1),32,None)]
    bpy.context.window.scene=test
    for view,loc,target,lens,ortho in shots:
        test.camera=helper.camera(name+'_'+view,loc,target,lens,ortho)
        test.render.filepath=str(IMAGES/('combination_'+name+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=scene
    helper.REVIEW=oldreview
    # Contact scenes are temporary: render evidence survives, study inventory
    # remains the same six playable/eight source assets.
    for o in list(c.objects):
        bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.scenes.remove(test)
    bpy.data.collections.remove(c)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    scene=bpy.context.scene
    report=json.loads((IMAGES/'naturalization_technical_report.json').read_text())
    study=module('refine_emberfall_naturalization.py','natural_study')
    helper=module('build_emberfall_foundation.py','natural_helpers')
    helper.REVIEW=bpy.data.collections['Cameras_Lights_Scale_REVIEW_ONLY']
    study.helper=helper
    study.TREES={o.name:study.tree(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('chunk_')}
    if not scene.get('NaturalizationSceneryFinishComplete'):
        targets=[o for o in study.visible_meshes(scene) if o.name.startswith('chunk_elevated_shelf')]
        for ob,grammar in zip(sorted(targets,key=lambda o:o.parent.name),['SCENERY_SPLIT_RIDGE','SCENERY_OPEN_TILT','SCENERY_BROAD_STEPS']):
            oldtree=study.tree(ob)
            ob['GrammarOverride']=grammar
            study.terrain_edit(ob)
            for child in ob.parent.children:
                if child==ob or child.type!='MESH' or max(abs(child.location.x),abs(child.location.y))>127:
                    continue
                x,y=child.location.x,child.location.y
                p,_,_,_=oldtree.ray_cast(Vector((x,y,300)),Vector((0,0,-1)))
                child.location.z+=study.ground(ob,x,y)-p.z
        scene['NaturalizationSceneryFinishComplete']=True
    if not scene.get('NaturalizationFinishComplete'):
        roots={o.parent for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('road_remnant') and o.parent}
        for root in roots:
            road_fragments(root,study.terrain_for(root),helper,study)
        scene['NaturalizationFinishComplete']=True
    bpy.context.view_layer.update()
    # Render existing saved cameras again after the small targeted corrections.
    for ob in sorted([o for o in scene.objects if o.type=='CAMERA' and o.name.startswith('NaturalReview_')],key=lambda o:o.name):
        label=ob.name.removeprefix('NaturalReview_')
        scene.camera=ob
        scene.render.filepath=str(IMAGES/('after_'+label+'.png'))
        bpy.ops.render.render(write_still=True)
    changes=[]
    for m in bpy.data.materials:
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type=='BSDF_PRINCIPLED':
                    changes.append((n,n.inputs['Emission Strength'].default_value))
                    n.inputs['Emission Strength'].default_value=0
    lava=bpy.data.materials['EF_MoltenAuthoredFlow_REVIEW']
    base=lava.node_tree.nodes.get('Principled BSDF').inputs['Base Color']
    oldcolor=tuple(base.default_value)
    links=[(k.from_socket,k.to_socket) for k in base.links]
    for link in list(base.links):
        lava.node_tree.links.remove(link)
    base.default_value=(.045,.05,.055,1)
    for label in ('top_layout','overview','baseline_seam_oblique','raised_seam_oblique'):
        scene.camera=bpy.data.objects['NaturalReview_'+label]
        scene.render.filepath=str(IMAGES/('glow_minimized_'+label+'.png'))
        bpy.ops.render.render(write_still=True)
    for n,value in changes:
        n.inputs['Emission Strength'].default_value=value
    for a,b in links:
        lava.node_tree.links.new(a,b)
    base.default_value=oldcolor
    for args in [('entry_wasteland_waystone','combat_wasteland_broken_road','entry_combat',False),
                 ('path_wasteland_fault','combat_wasteland_broken_road','fault_combat',False),
                 ('path_fortress_causeway','combat_fortress_gateworks','causeway_raised',True)]:
        alternate_pair(scene,helper,study,*args)
    terrain=[o for o in bpy.data.collections['Playable_6_FOUNDATION_STUDY'].all_objects if o.type=='MESH' and o.name.startswith('chunk_')]
    checks=[]
    for ob in terrain:
        bm=bmesh.new()
        bm.from_mesh(ob.data)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        bm.free()
        assert nonmanifold==0
        checks.append({'object':ob.name,'nonmanifold_edges':nonmanifold,'identity':ob['TerrainIdentity'],
                       'local_origin':list(ob.location),'parent_origin':list(ob.parent.location)})
    report['after']=study.stats(scene)
    report['closed_terrain_readback']=checks
    report['origins_exact']=all(name in bpy.data.objects and [list(bpy.data.objects[name].location),list(bpy.data.objects[name].rotation_euler)]==value for name,value in report['origins_before'].items())
    assert report['origins_exact']
    report['extra_combinations']=['entry_combat','fault_combat','causeway_raised']
    report['raised_scenery_variants']=[(o.parent.name,o.get('GrammarOverride')) for o in study.visible_meshes(scene) if o.get('GrammarOverride')]
    report['visual_assessment']={'identity':'Stronger local and macro separation without heat. Open ash spaces intentionally contrast with one-sided shelf, plateau and raised failure. Still a prototype, not a production identity acceptance.',
                                 'similarity':'Scenery source siblings still share low-poly facet construction; repeated longitudinal bands removed. Large ash aprons remain relatively plain.',
                                 'seams':'Current route seams and three alternate pairings structurally continuous. Scenery silhouette handoffs and local faceted color changes remain visible in parts of top/oblique views; do not claim invisible seams universally.',
                                 'studio_ready':False,'next_gate':'Owner Blender acceptance of naturalization, especially scenery joins/terrace facets; then generic vertical socket handling and simplified walk collision.'}
    scene.camera=bpy.data.objects['NaturalReview_overview']
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    for path in (HERE/'naturalization_technical_report.json',IMAGES/'naturalization_technical_report.json'):
        path.write_text(json.dumps(report,indent=2),encoding='utf8')
    print('FINAL_READBACK',json.dumps(report['after']))


if __name__=='__main__':
    main()
