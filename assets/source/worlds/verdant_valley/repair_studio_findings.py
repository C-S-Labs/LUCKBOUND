"""Targeted current-scene repairs after owner Studio walk; no legacy regeneration."""
import ast,bpy,bmesh,json,hashlib,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/jhpel/LUCKBOUND/assets/source/worlds/verdant_valley')
REPORT=ROOT/'STUDIO_REPAIR_REPORT.json'

def color_helpers():
 tree=ast.parse((ROOT/'export_verdant_valley_kit.py').read_text())
 ns={}
 for n in tree.body:
  if isinstance(n,ast.FunctionDef) and n.name in ('material_rgb','prepare_production_colors'):
   exec(compile(ast.Module(body=[n],type_ignores=[]),str(ROOT),'exec'),ns)
 return ns['prepare_production_colors']

def triangulate(obj, indices):
 mesh=obj.data;bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
 normals={(p.index,mesh.loops[i].vertex_index):mesh.corner_normals[i].vector.copy() for p in mesh.polygons for i in p.loop_indices}
 marker=bm.faces.layers.int.new('vv_repair_face')
 for f in bm.faces:f[marker]=f.index
 selected=[bm.faces[i] for i in indices]
 bmesh.ops.triangulate(bm,faces=selected,quad_method='FIXED',ngon_method='EAR_CLIP')
 bm.faces.index_update();bm.verts.index_update()
 loops=[normals[f[marker],loop.vert.index] for f in bm.faces for loop in f.loops]
 bm.faces.layers.int.remove(marker);bm.to_mesh(mesh);bm.free();mesh.update()
 if mesh.has_custom_normals:mesh.normals_split_custom_set(loops)
 return len(indices)

def main():
 assert bpy.context.mode=='OBJECT'
 assert not bpy.data.collections['VV_CUTBANK_FORD_COLLISION_MERGED'].objects.get('walk_bridge_deck'), 'Repairs already applied; inspect retained input instead'
 prepare=color_helpers();roots=['VV_STRUCTURE','VV_PROPS_SOLID','VV_PROPS_NONSOLID']
 objects=list({o for root in roots for o in bpy.data.collections[root].all_objects})
 color_changes=[];ready=[]
 try:
  for obj in sorted(objects,key=lambda o:o.name):
   copy=obj.copy();copy.data=obj.data.copy()
   result=prepare(copy)
   if result['created_layer'] or result['material_encoded_faces']:
    ready.append((obj,copy.data));color_changes.append(dict(object=obj.name,**result))
   else:
    unused=copy.data
    bpy.data.objects.remove(copy)
    bpy.data.meshes.remove(unused)
    continue
   bpy.data.objects.remove(copy)
 except Exception:
  for obj,mesh in ready:bpy.data.meshes.remove(mesh)
  raise
 if globals().get('MODE','inspect')=='inspect':
  for obj,mesh in ready:bpy.data.meshes.remove(mesh)
  print(json.dumps({'color_objects':len(color_changes),'faces':sum(r['material_encoded_faces'] for r in color_changes)}));return
 # Colors were fully preflighted before changing any source mesh.
 for obj,mesh in ready:obj.data=mesh
 stump=bpy.data.objects['chunk_side_wardens_clearing__PropsSolid']
 indices=[p.index for p in stump.data.polygons if stump.material_slots[p.material_index].material and stump.material_slots[p.material_index].name in ('VV_StumpBark','VV_StumpHeartwood','VV_StumpHollow') and len(p.vertices)>3]
 stump_faces=triangulate(stump,indices)
 boss=bpy.data.objects['chunk_boss_sanctuary']
 indices=[p.index for p in boss.data.polygons if len(p.vertices)>3 and p.center.y>105 and abs(p.center.x)<60 and p.center.z>-4]
 boss_faces=triangulate(boss,indices)
 # Continuous deck derived only from the six existing visible planks.
 obj=bpy.data.objects['chunk_cutbank_ford__PropsSolid'];ns=runpy.run_path(str(ROOT/'validate_scene_normals.py'));bm=bmesh.new();bm.from_mesh(obj.data);bm.normal_update();planks=[]
 for fs in ns['components'](bm):
  if len(fs)!=6:continue
  if not all(obj.material_slots[f.material_index].material and obj.material_slots[f.material_index].name in ('VVBridge_WarmWood','VVBridge_CutWood') for f in fs):continue
  ps=[obj.matrix_world@v.co for v in {v for f in fs for v in f.verts}];lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
  if hi[0]-lo[0]>15 and hi[1]-lo[1]>5 and hi[2]<2:planks.append((lo,hi))
 bm.free();assert len(planks)==6,len(planks)
 lo=[min(p[0][i] for p in planks) for i in range(3)];hi=[max(p[1][i] for p in planks) for i in range(3)]
 top=min(p[1][2] for p in planks)-.02;bottom=top-.5
 name='walk_bridge_deck';collection=bpy.data.collections['VV_CUTBANK_FORD_COLLISION_MERGED'];assert name not in collection.objects
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(x,y,z) for z in (bottom,top) for y in (lo[1],hi[1]) for x in (lo[0],hi[0])],[],[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]);mesh.update();collider=bpy.data.objects.new(name,mesh);collection.objects.link(collider);collider.hide_render=True;collider.display_type='WIRE';collider['solid']=True
 report={'colors':color_changes,'stump_triangulated_polygons':stump_faces,'boss_entry_triangulated_polygons':boss_faces,'bridge':{'object':name,'collection':collection.name,'planks':len(planks),'bounds':[lo,hi],'top':top},'source':bpy.data.filepath,'status':'Blender repaired; targeted render and Studio refresh pending'}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({'color_objects':len(color_changes),'color_faces':sum(r['material_encoded_faces'] for r in color_changes),'stump':stump_faces,'boss':boss_faces,'bridge':report['bridge']}))

def close_reported_openings():
    """Close the stump's actual inner-wall gap and the floating entrance skirt."""
    stump=bpy.data.objects['chunk_side_wardens_clearing__PropsSolid']
    mesh=stump.data
    original_normals={(p.index,mesh.loops[i].vertex_index):mesh.corner_normals[i].vector.copy() for p in mesh.polygons for i in p.loop_indices}
    bm=bmesh.new();bm.from_mesh(mesh);bm.normal_update();bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
    marker=bm.faces.layers.int.new('vv_repair_face')
    for f in bm.faces:f[marker]=f.index+1
    hollow=next(i for i,m in enumerate(mesh.materials) if m and m.name=='VV_StumpHollow')
    heart=next(i for i,m in enumerate(mesh.materials) if m and m.name=='VV_StumpHeartwood')
    rim={v for f in bm.faces if f.material_index==heart for v in f.verts}
    centre=Vector((-47,-20,0))
    inner=sorted([v for v in rim if abs((Vector((v.co.x,v.co.y,0))-centre).length-2.7)<.002],key=lambda v:__import__('math').atan2(v.co.y+20,v.co.x+47))
    assert len(inner)==9,len(inner)
    cap={v for f in bm.faces if f.material_index==hollow for v in f.verts}
    cap_top=max(v.co.z for v in cap)
    floor=[v for v in cap if abs(v.co.z-cap_top)<.001]
    assert len(floor)==9
    floor_height=min(v.co.z for v in inner)-.20
    for v in floor:v.co.z=floor_height
    pairs=[min(floor,key=lambda b:(Vector((b.co.x,b.co.y,0))-Vector((v.co.x,v.co.y,0))).length) for v in inner]
    added=[]
    for i in range(9):
        j=(i+1)%9
        f=bm.faces.new((inner[i],inner[j],pairs[j],pairs[i]));f.material_index=hollow;f[marker]=0;added.append(f)
    bm.normal_update()
    for f in added:
        c=f.calc_center_median();toward=Vector((-47-c.x,-20-c.y,0))
        if f.normal.dot(toward)<0:f.normal_flip()
    bmesh.ops.triangulate(bm,faces=added,quad_method='FIXED',ngon_method='EAR_CLIP')
    # Preserve all unaffected custom corner normals through the topology update.
    bm.normal_update();bm.verts.index_update()
    normals=[original_normals[f[marker]-1,loop.vert.index] if f[marker] and f.material_index!=hollow else f.normal.copy() for f in bm.faces for loop in f.loops]
    wall_flags=[not f[marker] for f in bm.faces]
    bm.faces.layers.int.remove(marker);bm.to_mesh(mesh);bm.free();mesh.update();mesh.normals_split_custom_set(normals)
    prepare=color_helpers();prepare(stump)
    material=mesh.materials[hollow]
    rgb=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value if material.use_nodes else material.diffuse_color
    for face,is_wall in zip(mesh.polygons,wall_flags):
        if is_wall:
            for index in face.loop_indices:mesh.color_attributes['Col'].data[index].color=rgb
    boss=bpy.data.objects['chunk_boss_sanctuary'];grass={v for p in boss.data.polygons if p.normal.z>.1 for v in p.vertices}
    lowered=[]
    for v in boss.data.vertices:
        if v.index not in grass and abs(v.co.y-128)<.001 and abs(v.co.x)<=40.001 and v.co.z>-2.8:
            lowered.append([v.index,float(v.co.z)]);v.co.z=-2.8
    assert lowered
    boss.data.update()
    r=json.loads(REPORT.read_text());r['stump_inner_wall']={'rim_vertices':9,'wall_triangles':18,'floor_height':floor_height};r['boss_skirt_lowered']=lowered;r['status']='Blender repaired; source save and Studio visual validation pending';REPORT.write_text(json.dumps(r,indent=2))
    print(json.dumps({'inner_wall_triangles':18,'boss_skirt_vertices':len(lowered),'boss_walk_surface_unchanged':True}))

if __name__=='__main__':
    main()
    if globals().get('MODE','inspect')=='repair':
        close_reported_openings()
