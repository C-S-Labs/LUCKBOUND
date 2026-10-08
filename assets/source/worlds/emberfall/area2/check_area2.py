"""Bounded saved-scene checks for the two castle blockouts; no traversal/collision certification."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII')
EVIDENCE=OUT/'CastleVariantsReview'
report=json.loads((EVIDENCE/'revision_report.json').read_text())
scene=bpy.context.scene

def find(layer,name):
    def visit(c):
        if c.name==name:return c
        for child in c.children:
            found=visit(child)
            if found:return found
    return visit(layer.layer_collection)


def signature(o):
    sha=hashlib.sha256();sha.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
    if o.type=='MESH':
        sha.update(str([tuple(v.co) for v in o.data.vertices]).encode())
        sha.update(str([tuple(p.vertices) for p in o.data.polygons]).encode())
        sha.update(str([p.material_index for p in o.data.polygons]).encode())
        sha.update(str([m.name for m in o.data.materials]).encode())
    return sha.hexdigest()

checks={'saved_file':bpy.data.filepath,'preserved_original_objects':len(report['preserved_object_hashes']),
 'preserved_original_geometry_exact':all(signature(bpy.data.objects[n])==v for n,v in report['preserved_object_hashes'].items()),
 'both_variants_final_boss':report['both_variants_final_boss'],
 'inner_interface':report['same_inner_interface'],'floor_probes':{},'variant_exclusions':{},'finite_geometry':True}
for variant,key in [('A','VARIANT_A_CATASTROPHE'),('B','VARIANT_B_STRONGHOLD')]:
    layer=scene.view_layers[key];bpy.context.window.view_layer=layer
    other='CASTLE_B_STRONGHOLD' if variant=='A' else 'CASTLE_A_CATASTROPHE'
    checks['variant_exclusions'][variant]=find(layer,other).exclude
    for route_name in ['Route','A_ROUTE','B_ROUTE']:
        find(layer,route_name).exclude=True
    layer.update()
    results=[]
    for a,b in zip(report['variant_'+variant+'_route'],report['variant_'+variant+'_route'][1:]):
        p=(Vector(a)+Vector(b))/2
        hit,pos,norm,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),p+Vector((0,0,5)),Vector((0,0,-1)),distance=100)
        results.append({'xyz':list(p),'hit':hit,'object':obj.name if obj else None,'floor_z':pos.z if hit else None})
    checks['floor_probes'][variant]=results
bpy.context.window.view_layer=scene.view_layers['VARIANT_A_CATASTROPHE']
start=Vector((0,1255,102));target=Vector((0,1545,70));direction=(target-start).normalized()
hit,pos,norm,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),start,direction,distance=(target-start).length-1)
checks['crater_occluded_from_entry_hall']=bool(hit)
checks['entry_occluder']=obj.name if obj else None
hit,pos,norm,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((0,1545,110)),Vector((0,0,-1)),distance=150)
checks['crater_center_floor_z']=pos.z if hit else None
checks['crater_center_hit_object']=obj.name if obj else None
checks['crater_actual_open_cavity']=hit and (obj.name=='A_FINAL_BOSS_SPACE_Floor' or obj.name.startswith('A_MasonryDescent')) and pos.z<60
checks['finite_geometry']=all(math.isfinite(n) for o in scene.objects if o.type=='MESH' for v in o.data.vertices for n in v.co)
checks['missing_floor_samples']=sum(not r['hit'] for results in checks['floor_probes'].values() for r in results)
checks['named_revision_cameras']=all(bpy.data.objects.get(name) and bpy.data.objects[name].type=='CAMERA' for name in report['views'])
checks['initial_proxy_isolated']=bpy.data.collections['INITIAL_PROXY_RETAINED'].hide_viewport and bpy.data.collections['INITIAL_PROXY_RETAINED'].hide_render
(EVIDENCE/'saved_revision_checks.json').write_text(json.dumps(checks,indent=2))
assert checks['preserved_original_geometry_exact'] and checks['finite_geometry']
assert all(checks['variant_exclusions'].values()) and checks['named_revision_cameras'] and checks['initial_proxy_isolated']
assert checks['crater_occluded_from_entry_hall'] and checks['crater_actual_open_cavity'] and checks['missing_floor_samples']==0
print(json.dumps({k:v for k,v in checks.items() if k not in ['floor_probes']}))
