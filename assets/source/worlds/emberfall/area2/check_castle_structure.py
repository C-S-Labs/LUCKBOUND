"""Cheap protection/contact checks for the final castle structural cleanup."""
import bpy,importlib.util,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('structural',ROOT/'cleanup_castle_structure.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m;h=s.h;scene=bpy.context.scene;report=json.loads((s.EV/'structural_report.json').read_text());p=report['protected']
def same(entries):return all(n in bpy.data.objects and m.signature(bpy.data.objects[n])==v for n,v in entries.items())
def overlap(a,b):
 alo,ahi=s.bounds(bpy.data.objects[a]);blo,bhi=s.bounds(bpy.data.objects[b]);return all(ahi[k]+.02>=blo[k] and bhi[k]+.02>=alo[k] for k in range(3))
def ray(x,y,z):
 hit,pos,n,j,o,mat=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((x,y,z)),Vector((0,0,-1)),distance=12);return hit and abs(pos.z-120)<.001
m.use('A');checks={'shared887_exact':s.c.i.preserve_shared()==p['shared'],'A_arena_exact':m.hashes(s.c.AG)==p['basin'],'A_entrance_exact':same(p['A_entrance']),'A_route_exact':m.hashes('A_ROUTE')==p['A_route']}
checks['A_support_sources_valid']=all(o.get('baseline_source','') in bpy.data.objects or o.get('structural_source') for o in h.COLS[s.AS].objects if o.type=='MESH')
m.use('B');checks['B_accepted_geometry_routes_exact']=same(p['B_accepted']);checks['common_entrance_interface_exact']=same(p['entrance_interface'])
contacts=[('B_STRUCT_Household_BreachRib','B_STRUCT_Household_CutEdge'),('B_STRUCT_Household_BreachRib','B_Composed_WestHousehold_ELintel'),('B_STRUCT_KeepSouthBearing','B_BossRearEastWall'),('B_STRUCT_KeepSouthUpperInfill','B_STRUCT_KeepSouthBearing'),('B_STRUCT_KeepEastUpperInfill','B_STRUCT_KeepEastBearing'),('B_STRUCT_KeepEastBearing','B_STRUCT_KeepSouthBearing'),('B_STRUCT_AudienceWestBearing','B_Composed_AudienceHall_Roof'),('B_STRUCT_ArchiveEdgeBearing','B_Composed_ArchiveAnnex_Roof'),('B_STRUCT_ArchiveEdgeBearing','B_STRUCT_ArchiveFrontBearing'),('B_STRUCT_ArchiveEdgeBearing','B_STRUCT_ArchiveRearBearing'),('B_STRUCT_Household_BurnedRib','B_STRUCT_Household_CutEdge'),('B_STRUCT_CrossHall_BurnedRib','B_Composed_TransverseHall_WLintel'),('B_STRUCT_Steward_BurnedRib','B_STRUCT_Steward_CutEdge'),('CastleGateRoof_ConnectedRafter','CastleGateRoof_EaveBearing'),('CastleGateRoof_ConnectedRafter','CastleGateRoof_RidgeBearing')]
checks['bearing_contact_bounds']={a+' / '+b:overlap(a,b) for a,b in contacts}
for col in ['Route','A_ROUTE','B_ROUTE']:s.r.layer_collection(bpy.context.view_layer,col).exclude=True
bpy.context.view_layer.update()
checks['boss_floor_clear']=all(ray(x,y,127) for x,y in [(-90,1560),(0,1560),(90,1560),(-90,1640),(0,1640),(90,1640),(-90,1730),(0,1730),(90,1730)])
checks['reward_floor_clear']=all(ray(x,y,127) for x,y in [(-190,1620),(-150,1620),(-190,1672),(-150,1672)])
checks['finite_geometry']=all(math.isfinite(q) for col in [s.BS,s.AS,'CASTLE_EXTERIOR_SHARED'] for o in h.COLS[col].objects if o.type=='MESH' for v in o.data.vertices for q in v.co)
checks['new_support_meshes_nonempty']=all(o.data.polygons for col in [s.BS,s.AS] for o in h.COLS[col].objects if o.type=='MESH')
checks['damage_regions']=len(report['localized_wall_damage_regions']);checks['existing_roof_masses_exact']=report['original_roof_masses_exact']
(s.EV/'structural_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2),flush=True)
assert all(v for k,v in checks.items() if k!='bearing_contact_bounds') and all(checks['bearing_contact_bounds'].values())
