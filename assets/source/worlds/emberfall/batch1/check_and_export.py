"""Bounded saved-source validation and one disposable FBX; no upload IDs."""
import bpy,bmesh,sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,'E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
import batch1_shared as s
OUT=s.OUT
bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsBatch1.blend'))
report=json.loads((OUT/'batch1_report.json').read_text());checks={};probed=[]
for ident,meta in report['kit'].items():
    scene=bpy.data.scenes[ident];terrain=next(o for o in scene.objects if o.name.startswith('Terrain_'))
    assert hashlib.sha256(json.dumps([tuple(v.co) for v in terrain.data.vertices]).encode()).hexdigest()==meta['geometry_sha256']
    cv=next(c for c in scene.collection.children if c.name.startswith('COLLISION_'))
    max_error=0;hull_error=0
    for sock in meta['sockets']:
        side=sock['Id'];kind=sock['Kind'].split('_')[-1];datum=sock['OffsetY']
        for across in range(-128,129,2):
            x,y={'S':(across,-128),'N':(across,128),'W':(-128,across),'E':(128,across)}[side]
            h=s.ec.surface([tuple(v.co) for v in list(terrain.data.vertices)[:4225]],4,x,y)
            max_error=max(max_error,abs(h-datum-s.ec.profile(kind,across)))
    for obj in cv.objects:
        bm=bmesh.new();bm.from_mesh(obj.data);assert all(e.is_manifold for e in bm.edges);bm.free()
        if obj.get('CollisionFidelity')=='Hull':
            for f in obj.data.polygons:hull_error=max(hull_error,max(f.normal.dot(v.co-obj.data.vertices[f.vertices[0]].co) for v in obj.data.vertices))
    assert max_error<.01 and hull_error<.0001
    boundary=[]
    vs=[tuple(v.co) for v in list(terrain.data.vertices)[:4225]]
    for side in ('S','N','W','E'):
        connected=any(k['Id']==side for k in meta['sockets'])
        stations=sorted(set(list(range(-128,129,32))+([-12,12] if connected else [])))
        for a,b in zip(stations,stations[1:]):
            if connected and a>=-12 and b<=12:continue
            xy=lambda t:{'S':(t,-128),'N':(t,128),'W':(-128,t),'E':(128,t)}[side]
            x,y=xy(a);xx,yy=xy(b)
            boundary.append(dict(A=[x,s.ec.surface(vs,4,x,y),-y],B=[xx,s.ec.surface(vs,4,xx,yy),-yy]))
    meta['Boundary']=dict(Height=64,Thickness=2,Segments=boundary)
    terrain['Boundary']=json.dumps(meta['Boundary']);scene['Metadata']=json.dumps(meta)
    checks[ident]=dict(profile_error=max_error,hull_halfspace_error=hull_error,collision_parts=len(cv.objects),boundary_parts=len(boundary),terrain_triangles=sum(len(p.vertices)-2 for p in terrain.data.polygons),appearance_copy_meshes=sum(o.get('AppearanceRole') in ('terrain','grass') for o in scene.objects))
    if ident in ('EF_SWITCHBACK_BANK','EF_WAYMARK_TERRACE'):
        for o in cv.objects:
            v=[tuple(q.co) for q in o.data.vertices];f=[]
            o.data.calc_loop_triangles()
            for p in o.data.loop_triangles:f.append(list(p.vertices))
            probed.append(dict(chunk=ident,name=o.name,fidelity=o['CollisionFidelity'],vertices=[[x,z,-y] for x,y,z in v],faces=f))
    scene['GeometryFrozen']=True
report['source_checks']=checks
report['runtime_boundary_schema']='Existing Boundary.Height/Thickness/Segments; tagged by existing ChunkLoader, exclude from camera queries.'
(OUT/'batch1_report.json').write_text(json.dumps(report,indent=2))
(OUT/'collision_payload.json').write_text(json.dumps(probed,separators=(',',':')))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsBatch1.blend'))
scene=bpy.data.scenes['EF_SWITCHBACK_BANK'];bpy.context.window.scene=scene
terrain=next(o for o in scene.objects if o.name.startswith('Terrain_'))
bpy.ops.object.select_all(action='DESELECT');terrain.select_set(True);bpy.context.view_layer.objects.active=terrain
path=OUT/'RepresentativeSwitchback.fbx'
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',use_mesh_modifiers=True,colors_type='SRGB',use_custom_props=True,add_leaf_bones=False,bake_anim=False)
source_tri=sum(len(p.vertices)-2 for p in terrain.data.polygons)
re=bpy.data.scenes.new('Disposable_FBX_Readback');bpy.context.window.scene=re
bpy.ops.import_scene.fbx(filepath=str(path));imported=next(o for o in re.objects if o.type=='MESH');imported.data.calc_loop_triangles()
attr=imported.data.color_attributes.get('Col');assert attr and len(imported.data.loop_triangles)==source_tri
exp=dict(file=str(path),bytes=path.stat().st_size,triangles=len(imported.data.loop_triangles),colour_domain=attr.domain,colour_type=attr.data_type,dimensions=list(imported.dimensions),source_origin=list(terrain.location),import_origin=list(imported.location))
payload=dict(vertices=[[v.co.x,v.co.z,-v.co.y] for v in imported.data.vertices],faces=[list(t.vertices) for t in imported.data.loop_triangles],colours=[list(attr.data[i].color_srgb) for i in range(len(attr.data))])
(OUT/'fbx_result.json').write_text(json.dumps(exp,indent=2));(OUT/'appearance_payload.json').write_text(json.dumps(payload,separators=(',',':')))
print('SOURCE_AND_FBX_PASS',json.dumps(exp))
