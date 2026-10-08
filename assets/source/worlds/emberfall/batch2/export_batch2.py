"""Exact new-source exports; export-copy batching only, existing Roblox assets untouched."""
import bpy
import json
import sys
import hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'batch1'))
import batch1_shared as sh
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')
DEST=OUT/'exports';DEST.mkdir(exist_ok=True)


def record(obj,key,role,chunk=None,fidelity=None):
    coords=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
    center=[(lo[i]+hi[i])/2 for i in range(3)];size=[hi[i]-lo[i] for i in range(3)]
    obj.name=key;obj['ExportKey']=key;obj.hide_render=False;obj.hide_viewport=False
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles)<10000
    if not obj.data.uv_layers:obj.data.uv_layers.new(name='UVMap')
    return dict(key=key,name=key,role=role,chunk=chunk,center=[center[0],center[2],-center[1]],size=[size[0],size[2],size[1]],triangles=len(obj.data.loop_triangles),fidelity=fidelity)


def batches(objects,scene,prefix,role,chunk=None):
    """Evaluate transforms/material colors into disposable <8500-tri meshes."""
    result=[];vs=[];fs=[];colors=[];num=0
    def flush():
        nonlocal vs,fs,colors,num
        mesh=bpy.data.meshes.new(prefix);mesh.from_pydata(vs,[],fs);mesh.update()
        obj=bpy.data.objects.new(prefix,mesh);scene.collection.objects.link(obj)
        attr=mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
        for index,col in enumerate(colors):attr.data[index].color=col
        mesh.color_attributes.active_color=attr;mesh.materials.append(sh.shader())
        result.append((obj,record(obj,prefix+'_'+str(num),role,chunk)))
        vs=[];fs=[];colors=[];num+=1
    for original in objects:
        original.data.calc_loop_triangles();attr=original.data.color_attributes.get('Col')
        for tri in original.data.loop_triangles:
            if len(fs)>=8500:flush()
            face=[]
            for vertex,loop in zip(tri.vertices,tri.loops):
                face.append(len(vs));vs.append(tuple(original.matrix_world@original.data.vertices[vertex].co))
                if attr:col=tuple(attr.data[loop].color)
                else:
                    mat=original.data.materials[original.data.polygons[tri.polygon_index].material_index] if original.data.materials else None
                    node=mat.node_tree.nodes.get('Principled BSDF') if mat and mat.use_nodes else None
                    col=tuple(node.inputs['Base Color'].default_value) if node else tuple(mat.diffuse_color) if mat else (.25,.2,.1,1)
                colors.append(col)
            fs.append(tuple(face))
    if fs:flush()
    return result


def export_files(scene,pairs,stem):
    """Bound uploads: roughly160k triangles/file, each actual FBX below20MiB."""
    files=[];group=[];tris=0
    def flush():
        nonlocal group,tris
        path=DEST/(stem+'_'+str(len(files))+'.fbx')
        bpy.context.window.scene=scene;bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
        for obj,rec in group:obj.select_set(True)
        bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',use_mesh_modifiers=True,colors_type='SRGB',use_custom_props=True,add_leaf_bones=False,bake_anim=False)
        assert path.stat().st_size<20*1024*1024
        for obj,rec in group:rec['export']=str(path)
        # Actual import round-trip: unique keys, geometry counts and dimensions.
        imported=bpy.data.scenes.new(stem+'_Readback_'+str(len(files)));bpy.context.window.scene=imported
        bpy.ops.import_scene.fbx(filepath=str(path))
        byname={o.name.split('.')[0]:o for o in imported.objects if o.type=='MESH'}
        for obj,rec in group:
            got=byname[rec['key']];got.data.calc_loop_triangles()
            assert len(got.data.loop_triangles)==rec['triangles'],rec['key']
            expected=rec['size']  # bake_space_transform round-trip keeps FBX Y-up.
            assert max(abs(got.dimensions[i]-expected[i]) for i in range(3))<.002,(rec['key'],list(got.dimensions),expected)
            if rec['role']!='collision':assert got.data.color_attributes.get('Col'),rec['key']
            assert got.data.uv_layers
        files.append(dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),meshes=len(group),triangles=tris,roundtrip=True))
        group=[];tris=0
    for pair in pairs:
        if group and tris+pair[1]['triangles']>160000:flush()
        group.append(pair);tris+=pair[1]['triangles']
    if group:flush()
    return files


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsBatch2.blend'))
    rows=json.loads((OUT/'batch2_sources.json').read_text());variants=json.loads((OUT/'batch2_variants.json').read_text())
    export_scene=bpy.data.scenes.new('Batch2SourceExport');export_scene.unit_settings.system='NONE';export_scene.unit_settings.scale_length=1
    visual=[];collision=[]
    for row in rows+variants:
        scene=bpy.data.scenes[row['id']];bpy.context.window.scene=scene;bpy.context.view_layer.update()
        terrain=next(o for o in scene.objects if o.name.startswith('Terrain_'))
        assert hashlib.sha256(json.dumps([tuple(v.co) for v in terrain.data.vertices]).encode()).hexdigest()==row['geometry_sha256']
        props=[];cnum=0;gnum=0
        for o in scene.objects:
            if o.type!='MESH' or o.get('ReviewOnly') or o.name=='Five_Stud_Human':continue
            if o.get('CollisionFidelity') and not row.get('variant_of'):
                copy=o.copy();copy.data=o.data.copy();export_scene.collection.objects.link(copy);copy.matrix_world=o.matrix_basis
                collision.append((copy,record(copy,row['id']+'_COLLISION_'+str(cnum),'collision',row['id'],o['CollisionFidelity'])));cnum+=1
            elif o.get('AppearanceRole') in ('terrain','grass'):
                if o is terrain and row.get('variant_of'):continue
                copy=o.copy();copy.data=o.data.copy();export_scene.collection.objects.link(copy);copy.matrix_world=o.matrix_basis
                key=row['id']+'_TERRAIN' if o is terrain else row['id']+'_GRASS_'+str(gnum)
                if o is not terrain:gnum+=1
                visual.append((copy,record(copy,key,o['AppearanceRole'],row['id'])))
            elif not o.get('CollisionFidelity'):props.append(o)
        visual.extend(batches(props,export_scene,row['id']+'_PROPS','props',row['id']))
    files=export_files(export_scene,visual,'EF_BATCH2_SOURCE_VISUAL')+export_files(export_scene,collision,'EF_BATCH2_SOURCE_COLLISION')
    result=dict(scope='New reusable source exports; no assembled burn direction encoded in terrain sources',sources=rows,variants=variants,assets=[r for o,r in visual+collision],files=files,collision_meshes=len(collision),visual_meshes=len(visual),existing_assets_modified=False)
    (OUT/'source_export_manifest.json').write_text(json.dumps(result,indent=2))
    (HERE/'source_export_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('SOURCE_EXPORT_PASS',json.dumps(dict(files=files,visual=len(visual),collision=len(collision))))


if __name__=='__main__':main()
