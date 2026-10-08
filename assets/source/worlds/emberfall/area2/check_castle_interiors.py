"""Cheap saved-scene interior checks, not physics or boss-mechanics certification."""
import bpy,importlib.util,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('interiors',ROOT/'revise_castle_interiors.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=json.loads((m.EV/'interior_layout_report.json').read_text());scene=bpy.context.scene

def ray(start,direction=(0,0,-1),distance=300):
 hit,p,n,index,o,mat=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(start),Vector(direction),distance=distance)
 return {'hit':hit,'object':o.name if o else None,'point':list(p) if hit else None}

def use(v):
 m.use(v)
 for col in ['Route','A_ROUTE','B_ROUTE']:m.r.layer_collection(bpy.context.view_layer,col).exclude=True
 bpy.context.view_layer.update()

use('A');p=r['protected_hashes']
checks={'shared_exact':p['shared']==m.c.i.preserve_shared(),'A_basin_exact':p['basin']==m.hashes(m.c.AG),'A_entrance_exact':all(m.signature(bpy.data.objects[n])==s for n,s in p['entrance'].items())}
use('B');checks['exterior_exact']=p['exterior']==m.hashes('CASTLE_EXTERIOR_SHARED')
checks['boss_clear_floor']=[ray((x,y,127),distance=12) for x,y in [(-90,1560),(0,1560),(90,1560),(-90,1640),(0,1640),(90,1640),(-90,1730),(0,1730),(90,1730)]]
checks['reward_clear_floor']=[ray((x,y,127),distance=12) for x,y in [(-190,1620),(-150,1620),(-190,1672),(-150,1672)]]
checks['reward_behind_seal_clear']=not ray((-122,1644,128),(-1,0,0),60)['hit']
checks['reward_internal_clear']=not ray((-190,1672,126),(1,0,0),45)['hit']
checks['reward_floor_level']=all(a['hit'] and abs(a['point'][2]-120)<.001 for a in checks['reward_clear_floor'])
checks['combat_floor_level']=all(a['hit'] and abs(a['point'][2]-120)<.001 for a in checks['boss_clear_floor'])
# Human-width center probes at primary portal, room doorway and sealed reward link.
checks['primary_portal_open']=not ray((20,1340,102),(0,1,0),25)['hit']
checks['hall_to_stair_turn_clear']=not ray((110,1395,102),(1,0,0),45)['hit'] and not ray((155,1395,102),(0,1,0),25)['hit']
checks['stair_upper_exit_open']=not ray((155,1495,126),(0,1,0),30)['hit']
checks['boss_entry_open']=not ray((140,1542,126),(-1,0,0),45)['hit']
checks['reward_sealed']=ray((-100,1644,128),(-1,0,0),45)
checks['foundation_solid']=ray((0,1485,105),(0,1,0),100)
checks['route_floor_midpoints']=[ray(( (a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2+5),distance=100) for a,b in zip(r['primary_route'],r['primary_route'][1:])]
checks['route_no_floor_misses']=all(a['hit'] for a in checks['route_floor_midpoints'])
checks['finite_vertices']=all(math.isfinite(x) for col in [m.BC,m.BR,m.AC,m.AR] for o in m.h.COLS[col].objects if o.type=='MESH' for v in o.data.vertices for x in v.co)
checks['A_sources_current']=all(o.get('baseline_source') in bpy.data.objects for col in [m.AC,m.AR] for o in m.h.COLS[col].objects if o.type=='MESH')
(m.EV/'interior_layout_checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps({k:v for k,v in checks.items() if k not in ['boss_clear_floor','reward_clear_floor','route_floor_midpoints']},indent=2),flush=True)
assert all(checks[k] for k in ['shared_exact','A_basin_exact','A_entrance_exact','exterior_exact','combat_floor_level','reward_floor_level','reward_internal_clear','reward_behind_seal_clear','primary_portal_open','boss_entry_open','stair_upper_exit_open','hall_to_stair_turn_clear','route_no_floor_misses','finite_vertices','A_sources_current'])
assert checks['reward_sealed']['object']=='B_POST_BOSS_SEALED_DOOR'
assert checks['foundation_solid']['object'].startswith('B_SolidRaisedFoundation')
