"""Owner-authorized Layout1-only appearance snapshot; no frozen source writes."""
from pathlib import Path
source=Path(__file__).with_name('export_walkthrough.py').read_text(encoding='utf-8-sig')
# Reuse exact validated source extraction and the approved semantic field.
exec(source.split('# Package visible assembly-owned')[0])
snapshot=[]
for obj,record in zip(visual,[r for r in data['assets'] if r['role']!='collision']):
    row=next(r for r in rows if r['id']==record['chunk'])
    local=obj.matrix_basis.copy()
    obj.matrix_world=a.transform(row)@local
    bpy.context.view_layer.update()
    a.colour_object(obj,field)
    obj.matrix_world=local
    obj.name='EF_LAYOUT1_SNAPSHOT_'+record['key']
    snapshot.append(obj)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for obj in snapshot:obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'EF_BATCH1_LAYOUT1_APPEARANCE.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',use_mesh_modifiers=True,colors_type='SRGB',use_custom_props=True,add_leaf_bones=False,bake_anim=False)
print('LAYOUT1_SNAPSHOT',len(snapshot),'same vertices, faces, normals, pivots; assembly-derived colours only')
