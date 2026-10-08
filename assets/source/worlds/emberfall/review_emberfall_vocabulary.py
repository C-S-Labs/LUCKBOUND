"""Saved-scene inventory and one fully heat-muted identity diagnostic; no export."""
import bpy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
IMAGES=OUT/'VocabularyReview'
MAIN=OUT/'EmberfallFoundation.blend'


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    scene=bpy.context.scene
    assert scene.get('VocabularyPassComplete')
    report=json.loads((HERE/'vocabulary_technical_report.json').read_text())
    spec=importlib.util.spec_from_file_location('vocabulary_stats',HERE/'refine_emberfall_naturalization.py')
    study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
    assert study.stats(scene)==report['after']
    vspec=importlib.util.spec_from_file_location('vocabulary_gallery',HERE/'refine_emberfall_vocabulary.py')
    vocabulary=importlib.util.module_from_spec(vspec);vspec.loader.exec_module(vocabulary)
    vocabulary.study=study
    vocabulary.helper=vocabulary.module('build_emberfall_foundation.py','gallery_helpers')
    vocabulary.helper.REVIEW=bpy.data.collections['Cameras_Lights_Scale_REVIEW_ONLY']
    study.helper=vocabulary.helper
    groups=[]
    for kind in vocabulary.RUINS:
        root=bpy.data.objects[next(r['root'] for r in report['ruins'] if r['archetype']==kind)]
        objects=[]
        for o in root.children:
            if o.get('Archetype')==kind or o.name.startswith(('fresh_fallen_wall_mass','localized_collapse_rubble')):
                objects += [o]+list(o.children_recursive)
        groups.append([o for o in objects if o.type=='MESH'])
    vocabulary.gallery(scene,'ruin_variety',groups)
    report['scene_objects']=len(scene.objects)
    report['collections']={c.name:len(c.objects) for c in bpy.data.collections}
    report['chunk_dimensions']=[256,256]
    report['persistent_elevation_delta']=56
    report['playable_center_datums']={}
    for name in study.GRAMMAR:
        t=bpy.data.objects['chunk_'+name]
        from mathutils import Vector
        p,_,_,_=study.tree(t).ray_cast(Vector((0,0,400)),Vector((0,0,-1)))
        assert p is not None and abs(p.z)<.001,(name,p)
        report['playable_center_datums'][name]=p.z
    report['origins']={o.name:list(o.location) for o in scene.objects if o.type=='EMPTY' and any(ch.name.startswith('chunk_') for ch in o.children)}
    report['visible_terrain_counts']=[]
    for o in study.visible_meshes(scene):
        if o.name.startswith('chunk_') and 'distant' not in o.name:
            o.data.calc_loop_triangles()
            report['visible_terrain_counts'].append({'object':o.name,'triangles':len(o.data.loop_triangles)})
    saved_emission=[]; saved_base=[]
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        for node in material.node_tree.nodes:
            if node.type=='BSDF_PRINCIPLED':
                slot=node.inputs['Emission Strength']
                saved_emission.append((slot,slot.default_value));slot.default_value=0
    for name in ('EF_MoltenAuthoredFlow_REVIEW','EF_HeatSeam'):
        material=bpy.data.materials[name]
        base=material.node_tree.nodes.get('Principled BSDF').inputs['Base Color']
        links=[(l.from_socket,l.to_socket) for l in base.links]
        saved_base.append((material,base,tuple(base.default_value),links))
        for l in list(base.links):material.node_tree.links.remove(l)
        base.default_value=(.035,.041,.05,1)
    try:
        scene.camera=bpy.data.objects['VocabularyReview_overview']
        scene.render.filepath=str(IMAGES/'heat_muted_identity.png')
        bpy.ops.render.render(write_still=True)
    finally:
        for slot,value in saved_emission:slot.default_value=value
        for material,base,color,links in saved_base:
            base.default_value=color
            for a,b in links:material.node_tree.links.new(a,b)
    report['assessment']={
        'terrain':'Stronger differentiated local silhouettes and rise/fall, without repeated longitudinal ribbon channels. Some scenery still shares polygonal stepped shelf syntax.',
        'seams':'No open gaps in current assembled border stations; baseline/raised player-eye route joins no longer show a hard handoff. Broad slope shading and scenery shoulder rhythm can still expose modular composition from above.',
        'identity':'Recent ruins, black takeover pockets, integrated basalt and smoke add local identity. Fully heat-muted distant overview still has plain ash areas and coarse polygonal landmarks; not a final art acceptance.',
        'studio_ready':False,
        'next_gate':'Owner Blender review; resolve any identified scenery composition/ash plainness before simple walk-collision and generic vertical socket preparation. No Studio import in this pass.',
        'collision':'Broad hidden route/ramp and combat apron needed; simplify cracks, shelves, stairs and lava banks. No collider authoring or traversal validation.'}
    for path in (HERE/'vocabulary_technical_report.json',IMAGES/'vocabulary_technical_report.json'):
        path.write_text(json.dumps(report,indent=2),encoding='utf8')
    scene.camera=bpy.data.objects['VocabularyReview_overview']
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    print('SAVED_READBACK_OK',json.dumps({'after':report['after'],'joins':len(report['join_checks']),
                                         'heat_features':len(report['heat_features']),'objects':report['scene_objects'],
                                         'max_terrain_triangles':max(r['triangles'] for r in report['visible_terrain_counts'])}))


if __name__=='__main__':main()
