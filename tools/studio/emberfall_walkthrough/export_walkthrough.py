"""Read frozen sources only; export exact visual/collision assets for Layout1 walkthrough."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
BASE=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Walkthrough');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(BASE))
import batch1_shared as s
import assemble_batch1 as a
bpy.ops.wm.open_mainfile(filepath=str(BASE/'BurnedPlainsBatch1.blend'))
report=json.loads((BASE/'batch1_report.json').read_text());rows=report['layouts']['Layout1']['rows'];meta=report['kit']
points=[];refuges=[]
for index,row in enumerate(rows):
    m=a.transform(row);guide=meta[row['id']]['guide']
    reverse=row['exit']==meta[row['id']]['sockets'][0]['Id'] if index<len(rows)-1 else (Vector(guide[0][:2])-(m.inverted()@Vector(points[-1][:3])).to_2d()).length>100
    if reverse:guide=guide[::-1]
    for x,y,z in guide:
        w=m@Vector((x,y,z));dist=points[-1][3]+math.hypot(w.x-points[-1][0],w.y-points[-1][1]) if points else 0
        if points and math.hypot(w.x-points[-1][0],w.y-points[-1][1])<1e-5:continue
        points.append((w.x,w.y,w.z,dist))
    for r in meta[row['id']]['refuges']:refuges.append((m.inverted(),r))
bounds=(min(r['x'] for r in rows)-128,min(-r['z'] for r in rows)-128,max(r['x'] for r in rows)+128,max(-r['z'] for r in rows)+128)
field=a.Field([(x,y,d) for x,y,z,d in points],bounds,refuges);field.thresholds=report['layouts']['Layout1']['thresholds']
data={'layout':'Layout1','rows':rows,'kit':{},'assets':[],'appearance':{'xmin':field.xmin,'ymin':field.ymin,'step':8,'nx':field.nx,'ny':field.ny,'length':field.length,'thresholds':list(field.thresholds),'grid':field.grid.flatten().tolist(),'refuges':[]},'route':[[x,z,-y,d] for x,y,z,d in points]}
for inv,r in refuges:data['appearance']['refuges'].append({'inverse':[[float(inv[i][j]) for j in range(4)] for i in range(4)],**r})
exports=bpy.data.scenes.new('OwnerWalkthroughExport');bpy.context.window.scene=exports;exports.unit_settings.system='NONE';exports.unit_settings.scale_length=1
visual=[];collision=[]
def make_record(obj,key,role,chunk=None,fidelity=None):
    coords=[obj.matrix_world@Vector(c) for c in obj.bound_box];lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
    center=[(lo[i]+hi[i])/2 for i in range(3)];size=[hi[i]-lo[i] for i in range(3)]
    record={'key':key,'name':key,'role':role,'chunk':chunk,'center':[center[0],center[2],-center[1]],'size':[size[0],size[2],size[1]],'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'fidelity':fidelity}
    obj.name=key;obj['ExportKey']=key;obj.hide_render=False;obj.hide_viewport=False;data['assets'].append(record)
    return record
def copy_obj(o):
    copy=o.copy();copy.data=o.data.copy();copy.matrix_world=o.matrix_basis;exports.collection.objects.link(copy);return copy
for ident,m in meta.items():
    scene=bpy.data.scenes[ident];terrain=next(o for o in scene.objects if o.name.startswith('Terrain_'))
    assert hashlib.sha256(json.dumps([tuple(v.co) for v in terrain.data.vertices]).encode()).hexdigest()==m['geometry_sha256']
    definition={'Id':ident,'WorldId':'EMBERFALL','Role':'ENTRY' if ident.startswith('EF_ENTRY') else 'PATH','Sockets':m['sockets'],'Boundary':m['Boundary'],'MeshYawOffset':0,'CollisionTemplate':'EF_BATCH1_COLLISION_'+ident,'Supports':['Traversal'],'SizeX':256,'SizeZ':256,'Weight':1}
    for o in scene.objects:
        if o.type!='MESH' or o.get('ReviewOnly') or o.name=='Five_Stud_Human':continue
        if o.get('AppearanceRole') in ('terrain','grass'):
            copy=copy_obj(o);key=ident+'_TERRAIN' if o is terrain else ident+'_GRASS_'+str(sum(r['chunk']==ident and r['role']=='grass' for r in data['assets']))
            rec=make_record(copy,key,o['AppearanceRole'],ident);visual.append(copy)
            if o is terrain:definition.update(AssetKey=key,SizeY=rec['size'][1],GroundOffsetY=rec['size'][1]/2-rec['center'][1])
        elif o.get('CollisionFidelity'):
            copy=copy_obj(o);key=ident+'_COLLISION_'+str(sum(r['chunk']==ident and r['role']=='collision' for r in data['assets']))
            make_record(copy,key,'collision',ident,o['CollisionFidelity']);collision.append(copy)
    data['kit'][ident]=definition
# Package visible assembly-owned props/road/scenery from the approved scene.
# Exact transformed vertices/faces/colour data retained; batching is export-only.
review=bpy.data.scenes['Layout1'];bpy.context.window.scene=review;bpy.context.view_layer.update();groups={}
for o in review.objects:
    if o.type!='MESH' or o.hide_render or o.name=='Five_Stud_Human' or o.get('CollisionFidelity'):continue
    if any(c.name.startswith('PLACED_') for c in o.users_collection) and o.get('AppearanceRole') in ('terrain','grass'):continue
    group='SCENERY' if o.get('NonPlayable') else 'ROAD' if o.name.startswith('CONTINUOUS_ROAD') else 'SMOKE' if 'Smoke' in o.name or 'smoke' in o.name else 'FIRE' if any('flame' in mat.name.lower() or 'core' in mat.name.lower() for mat in o.data.materials) else 'PROPS'
    groups.setdefault(group,[]).append(o)
def flush(group,vs,fs,colours,num):
    mesh=bpy.data.meshes.new(group);mesh.from_pydata(vs,[],fs);mesh.update();obj=bpy.data.objects.new(group,mesh);exports.collection.objects.link(obj)
    attr=mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER');idx=0
    for p in mesh.polygons:
        for loop in p.loop_indices:attr.data[loop].color=colours[idx];idx+=1
    mesh.color_attributes.active_color=attr;mesh.materials.append(s.shader())
    make_record(obj,'EF_BATCH1_'+group+'_'+str(num),group.lower());visual.append(obj)
for group,objects in groups.items():
    vs=[];fs=[];cols=[];num=0
    for o in objects:
        mesh=o.data;mesh.calc_loop_triangles();attr=mesh.color_attributes.get('Col')
        for tri in mesh.loop_triangles:
            if len(fs)>=8500:flush(group,vs,fs,cols,num);vs=[];fs=[];cols=[];num+=1
            indices=[]
            for vertex,loop in zip(tri.vertices,tri.loops):
                w=o.matrix_world@mesh.vertices[vertex].co;indices.append(len(vs));vs.append(tuple(w))
                if attr:col=tuple(attr.data[loop].color)
                else:
                    mat=mesh.materials[mesh.polygons[tri.polygon_index].material_index] if mesh.materials else None
                    node=mat.node_tree.nodes.get('Principled BSDF') if mat and mat.use_nodes else None
                    col=tuple(node.inputs['Base Color'].default_value) if node else tuple(mat.diffuse_color) if mat else (.25,.2,.1,1)
                cols.append(col)
            fs.append(tuple(indices))
    if fs:flush(group,vs,fs,cols,num)
def export(name,objs):
    bpy.context.window.scene=exports;bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/name),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',use_mesh_modifiers=True,colors_type='SRGB',use_custom_props=True,add_leaf_bones=False,bake_anim=False)
export('EF_BATCH1_VISUAL.fbx',visual);export('EF_BATCH1_COLLISION.fbx',collision)
for rec in data['assets']:rec['export']='EF_BATCH1_COLLISION.fbx' if rec['role']=='collision' else 'EF_BATCH1_VISUAL.fbx'
data['spawn']=data['route'][12][:3]
(OUT/'walkthrough_data.json').write_text(json.dumps(data,separators=(',',':')))
(OUT/'asset_mapping.json').write_text(json.dumps([{**r,'required_roblox_asset':'Mesh','id_destination':'walkthrough manifest Assets["'+r['key']+'"]'} for r in data['assets']],indent=2))
print('FROZEN_EXPORT_COMPLETE',json.dumps({'visual':len(visual),'collision':len(collision),'groups':{k:len(v) for k,v in groups.items()},'route_points':len(points),'field':field.stats,'source_terrain_modified':False}))
