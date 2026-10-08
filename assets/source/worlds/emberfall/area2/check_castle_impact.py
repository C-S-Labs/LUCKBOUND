"""Cheap saved-scene proof of enclosed B / missing A architecture, not traversal certification."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/ImpactCorrectionReview')
report=json.loads((EV/'impact_report.json').read_text())
scene=bpy.context.scene


def signature(o):
 sha=hashlib.sha256();sha.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
 if o.type=='MESH':
  sha.update(str([tuple(v.co) for v in o.data.vertices]).encode())
  sha.update(str([tuple(p.vertices) for p in o.data.polygons]).encode())
  sha.update(str([p.material_index for p in o.data.polygons]).encode())
  sha.update(str([m.name for m in o.data.materials]).encode())
 return sha.hexdigest()


def find(layer,name):
 def visit(c):
  if c.name==name:return c
  for ch in c.children:
   found=visit(ch)
   if found:return found
 return visit(layer.layer_collection)


def layer(variant):
 active=scene.view_layers['VARIANT_A_CATASTROPHE' if variant=='A' else 'VARIANT_B_STRONGHOLD']
 bpy.context.window.view_layer=active
 for name in ['Route','A_ROUTE','B_ROUTE']:find(active,name).exclude=True
 active.update();return active


def ray(xyz,direction=(0,0,-1),distance=400):
 hit,pos,norm,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(xyz),Vector(direction),distance=distance)
 return {'hit':hit,'object':obj.name if obj else None,'z':pos.z if hit else None}


checks={'saved_file':bpy.data.filepath,'shared_preservation_count':len(report['shared_object_hashes']),
 'shared_geometry_exact':all(signature(bpy.data.objects[n])==v for n,v in report['shared_object_hashes'].items()),
 'A_entrance_exact':all(signature(bpy.data.objects[n])==v for n,v in report['preserved_A_entrance_hashes'].items()),
 'finite_mesh_coordinates':all(math.isfinite(n) for o in scene.objects if o.type=='MESH' for v in o.data.vertices for n in v.co),
 'missing_volume_probes':{},'variant_exclusions':{}}
for v in ['A','B']:
 active=layer(v);other='CASTLE_B_STRONGHOLD' if v=='A' else 'CASTLE_A_CATASTROPHE'
 checks['variant_exclusions'][v]=find(active,other).exclude
 checks['missing_volume_probes'][v]=[ray((0,y,350)) for y in [1450,1545,1625]]
layer('B')
checks['B_lower_floor']=ray((0,1440,125));checks['B_upper_floor']=ray((0,1440,155))
checks['B_lower_room_ceiling']=ray((0,1440,115),(0,0,1),50)
probes=[]
for a,b in zip(report['B_route'],report['B_route'][1:]):
 p=(Vector(a)+Vector(b))/2;hit=ray(p+Vector((0,0,5)),distance=100);probes.append({'midpoint':list(p),**hit})
checks['B_route_floor_midpoints']=probes
checks['B_missing_floor_samples']=sum(not p['hit'] for p in probes)
layer('A')
start=Vector((0,1255,102));target=Vector((0,1545,70))
checks['A_entry_crater_occlusion']=ray(start,(target-start).normalized(),(target-start).length-1)
checks['A_center_below_ground']=checks['missing_volume_probes']['A'][1]['z']<60
checks['B_roofed_impact_footprint']=all(p['hit'] and p['z']>190 for p in checks['missing_volume_probes']['B'])
checks['A_corresponding_center_absent']=all(p['hit'] and p['z']<110 for p in checks['missing_volume_probes']['A'])
checks['B_two_real_levels']=abs(checks['B_lower_floor']['z']-96)<1 and abs(checks['B_upper_floor']['z']-132)<1
checks['review_cameras_present']=all(bpy.data.objects.get('IMPACT_'+n) is not None for n in report['views'])
checks['previous_B_study_isolated']=bpy.data.collections['PRE_IMPACT_B_INTERIOR_RETAINED'].hide_render and bpy.data.collections['PRE_IMPACT_B_INTERIOR_RETAINED'].hide_viewport
(EV/'impact_checks.json').write_text(json.dumps(checks,indent=2))
assert checks['shared_geometry_exact'] and checks['A_entrance_exact'] and checks['finite_mesh_coordinates']
assert all(checks['variant_exclusions'].values()) and checks['review_cameras_present'] and checks['previous_B_study_isolated']
assert checks['A_entry_crater_occlusion']['hit'] and checks['A_center_below_ground'] and checks['B_roofed_impact_footprint'] and checks['A_corresponding_center_absent']
assert checks['B_two_real_levels'] and checks['B_missing_floor_samples']==0
print(json.dumps({k:v for k,v in checks.items() if k not in ['B_route_floor_midpoints']}))
