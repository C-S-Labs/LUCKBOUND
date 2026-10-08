"""Cheap current castle composition checks, not gameplay/collision validation."""
import bpy
import hashlib,json,math
from pathlib import Path
from mathutils import Vector
EV=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII/BaselineArchitectureReview')
report=json.loads((EV/'architecture_report.json').read_text());scene=bpy.context.scene


def signature(o):
 sha=hashlib.sha256();sha.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
 if o.type=='MESH':
  sha.update(str([tuple(v.co) for v in o.data.vertices]).encode());sha.update(str([tuple(p.vertices) for p in o.data.polygons]).encode())
  sha.update(str([p.material_index for p in o.data.polygons]).encode());sha.update(str([m.name for m in o.data.materials]).encode())
 return sha.hexdigest()


def find(layer,name):
 def visit(c):
  if c.name==name:return c
  for child in c.children:
   found=visit(child)
   if found:return found
 return visit(layer.layer_collection)


def use(variant):
 layer=scene.view_layers['VARIANT_A_CATASTROPHE' if variant=='A' else 'VARIANT_B_STRONGHOLD'];bpy.context.window.view_layer=layer
 for name in ['Route','A_ROUTE','B_ROUTE']:find(layer,name).exclude=True
 layer.update();return layer


def ray(point,direction=(0,0,-1),distance=400):
 hit,pos,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(point),Vector(direction),distance=distance)
 return {'hit':hit,'object':obj.name if obj else None,'z':pos.z if hit else None}


use('A')
checks={'shared_objects':len(report['shared_hashes']),'shared_geometry_exact':all(signature(bpy.data.objects[n])==v for n,v in report['shared_hashes'].items()),
 'A_entrance_exact':all(signature(bpy.data.objects[n])==v for n,v in report['A_entrance_hashes'].items()),
 'B_first_reviewed':report['B_first_reviewed'],'A_direct_source_links':all(bpy.data.objects[n].get('baseline_source')==v and v in bpy.data.objects for n,v in report['A_source_map'].items()),
 'A_derived_survivor_meshes':len(report['A_source_map']),'finite_geometry':all(math.isfinite(n) for o in scene.objects if o.type=='MESH' for v in o.data.vertices for n in v.co),
 'route_floor_samples':{},'variant_exclusions':{},'matched_volume_samples':{}}
for variant in ['A','B']:
 layer=use(variant);other='CASTLE_B_STRONGHOLD' if variant=='A' else 'CASTLE_A_CATASTROPHE';checks['variant_exclusions'][variant]=find(layer,other).exclude
 points=report[variant+'_route'];samples=[]
 for a,b in zip(points,points[1:]):
  p=(Vector(a)+Vector(b))/2;samples.append({'midpoint':list(p),**ray(p+Vector((0,0,5)),distance=100)})
 checks['route_floor_samples'][variant]=samples
 checks['matched_volume_samples'][variant]=[ray((x,y,360)) for x,y in [(34,1401),(-100,1480),(23,1585)]]
use('A')
floor=bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN'];checks['arena_floor_vertex_z_range']=[min(v.co.z for v in floor.data.vertices),max(v.co.z for v in floor.data.vertices)]
checks['arena_clear_samples']=[ray((20+dx,1545+dy,125)) for dx,dy in [(0,0),(-100,0),(100,0),(0,-110),(0,110),(-80,-80),(80,80),(-80,80),(80,-80)]]
checks['arena_flat_clear']=all(s['hit'] and s['object']=='A_FLAT_FINAL_BOSS_BASIN' and abs(s['z']-92)<.001 for s in checks['arena_clear_samples'])
checks['arena_depression_studs']=report['depression_studs'];checks['max_transition_grade']=report['max_transition_grade']
checks['no_route_floor_misses']=all(p['hit'] for samples in checks['route_floor_samples'].values() for p in samples)
start=Vector((0,1255,102));target=Vector((20,1545,98));checks['A_entry_conceals_basin']=ray(start,(target-start).normalized(),(target-start).length-1)['hit']
checks['B_has_roofed_impact_architecture']=all(p['hit'] and p['z']>150 for p in checks['matched_volume_samples']['B'])
checks['A_corresponding_volume_removed']=all(p['hit'] and abs(p['z']-92)<.001 for p in checks['matched_volume_samples']['A'])
checks['roof_damage_present']={name:len(bpy.data.objects['B_Composed_'+name+'_Roof'].data.vertices)>8 for name in ['WestHousehold','StewardBlock','TransverseHall','KitchenStore']}
checks['plan_height_variety']=len(set(p['h'] for p in report['plan']));checks['longest_non_keep_block_studs']=max(max(p['w'],p['d']) for p in report['plan'] if p['id']!='RearKeep')
checks['all_current_cameras']=all('BASELINE_'+n in bpy.data.objects for n in report['views'])
(EV/'architecture_checks.json').write_text(json.dumps(checks,indent=2))
assert checks['shared_geometry_exact'] and checks['A_entrance_exact'] and checks['finite_geometry'] and checks['A_direct_source_links']
assert all(checks['variant_exclusions'].values()) and checks['arena_flat_clear'] and checks['no_route_floor_misses']
assert checks['A_entry_conceals_basin'] and checks['B_has_roofed_impact_architecture'] and checks['A_corresponding_volume_removed']
assert all(checks['roof_damage_present'].values()) and checks['all_current_cameras']
print(json.dumps({k:v for k,v in checks.items() if k not in ['route_floor_samples','arena_clear_samples']}))
