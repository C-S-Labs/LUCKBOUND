"""Bounded assembled semantic appearance export, not arbitrary-seed production state."""
import bpy
import json
import sys
import math
from pathlib import Path
from mathutils import Matrix

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/'batch1'))
import export_batch2 as exporter
import assemble_batch1 as assembly
OUT=exporter.OUT


def repair_bounds(scene, pairs):
    """Split only oversized disposable scenery; keep every triangle/color exact."""
    original=json.loads((OUT/'review_export_manifest.json').read_text())
    replaced={r['key']:r for r in original['records'] if max(r['size'])>2048}
    repaired=[]
    for obj,rec in pairs:
        if rec['key'] not in replaced:continue
        prior=replaced[rec['key']]
        assert rec['role']=='scenery' and rec['triangles']==prior['triangles']
        assert max(abs(a-b) for a,b in zip(rec['size'],prior['size']))<.002
        attr=obj.data.color_attributes['Col'];groups={}
        for poly in obj.data.polygons:
            coords=[obj.matrix_world@obj.data.vertices[i].co for i in poly.vertices]
            centre=sum(coords,coords[0]*0)/len(coords)
            groups.setdefault((math.floor(centre.x/768),math.floor(centre.y/768)),[]).append(poly)
        total=0
        for number,polys in enumerate(groups.values()):
            vertices=[];faces=[];colors=[]
            for poly in polys:
                face=[]
                for vertex,loop in zip(poly.vertices,poly.loop_indices):
                    face.append(len(vertices));vertices.append(tuple(obj.matrix_world@obj.data.vertices[vertex].co));colors.append(tuple(attr.data[loop].color))
                faces.append(face)
            mesh=bpy.data.meshes.new('BoundedScenery');mesh.from_pydata(vertices,[],faces);mesh.update()
            piece=bpy.data.objects.new('BoundedScenery',mesh);scene.collection.objects.link(piece)
            col=mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
            for i,value in enumerate(colors):col.data[i].color=value
            mesh.color_attributes.active_color=col;mesh.materials.append(exporter.sh.shader())
            record=exporter.record(piece,rec['key']+'_CELL_'+str(number),'scenery')
            record['replaces']=rec['key'];assert max(record['size'])<2048
            repaired.append((piece,record));total+=record['triangles']
        assert total==rec['triangles']
    assert {r['replaces'] for o,r in repaired}==set(replaced)
    if '--repair-cell' in sys.argv:
        key='EF_BATCH2_REVIEW_SCENERY_15_CELL_0'
        selected=[(o,r) for o,r in repaired if r['key']==key];assert len(selected)==1
        obj,prior=selected[0];pieces=[]
        polygons=list(obj.data.polygons)
        for number,polys in enumerate((polygons[:len(polygons)//2],polygons[len(polygons)//2:])):
            vertices=[];faces=[];colors=[];attr=obj.data.color_attributes['Col']
            for poly in polys:
                face=[]
                for vertex,loop in zip(poly.vertices,poly.loop_indices):
                    face.append(len(vertices));vertices.append(tuple(obj.data.vertices[vertex].co));colors.append(tuple(attr.data[loop].color))
                faces.append(face)
            mesh=bpy.data.meshes.new('DeliveryCell');mesh.from_pydata(vertices,[],faces);mesh.update()
            piece=bpy.data.objects.new('DeliveryCell',mesh);scene.collection.objects.link(piece)
            col=mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
            for i,value in enumerate(colors):col.data[i].color=value
            mesh.color_attributes.active_color=col;mesh.materials.append(exporter.sh.shader())
            record=exporter.record(piece,key+'_PART_'+str(number),'scenery');record['replaces']=key
            assert max(record['size'])<2048 and all(math.isfinite(v) for co in vertices for v in co)
            pieces.append((piece,record))
        assert sum(r['triangles'] for o,r in pieces)==prior['triangles']
        files=exporter.export_files(scene,pieces,'EF_BATCH2_REVIEW_CELL')
        result=dict(replaced=[key],records=[r for o,r in pieces],files=files,triangles=prior['triangles'],reason='Isolated delivered cell repeatedly rejected by Studio; exact faces/colors partitioned into two import artifacts')
        (OUT/'review_cell_manifest.json').write_text(json.dumps(result,indent=2))
        (HERE/'review_cell_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
        print('REVIEW_CELL_PASS',result['triangles']);return
    files=exporter.export_files(scene,repaired,'EF_BATCH2_REVIEW_BOUNDS')
    result=dict(replaced=list(replaced),records=[r for o,r in repaired],files=files,triangles=sum(r['triangles'] for o,r in repaired),reason='Roblox MeshPart Size clamp; spatial partition only, source geometry and colors unchanged')
    (OUT/'review_bounds_manifest.json').write_text(json.dumps(result,indent=2))
    (HERE/'review_bounds_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('REVIEW_BOUNDS_PASS',len(replaced),len(repaired),len(files),result['triangles'])


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsProductionReview.blend'))
    report=json.loads((OUT/'batch2_report.json').read_text());meta=report['kit'];original_rows=report['layouts']['Combined2']['rows']
    baseline=json.loads((ROOT/'assets/source/worlds/emberfall/batch1/batch1_report.json').read_text())['kit']
    scene=bpy.data.scenes['Combined2'];bpy.context.window.scene=scene;bpy.context.view_layer.update()
    placed=[c for c in scene.collection.children if c.name.startswith('PLACED_')]
    assert len(placed)==len(original_rows)
    target=bpy.data.scenes.new('Batch2ReviewExport');target.unit_settings.system='NONE';target.unit_settings.scale_length=1
    pairs=[];rows=[];definitions={};canonical=set();placement_objects=set()
    for index,(source_row,collection) in enumerate(zip(original_rows,placed),1):
        ident='EF_REVIEW_'+str(index).zfill(2);row=dict(source_row);source=source_row.get('source_id',source_row['id'])
        if meta[source_row['id']].get('variant_of'):source=meta[source_row['id']]['variant_of']
        canonical.add(source);row.update(id=ident,source_id=source,dressing_source=source_row['id']);rows.append(row)
        local=assembly.transform(source_row).inverted();terrain_record=None;gnum=0
        for original in collection.objects:
            placement_objects.add(original)
            if original.get('AppearanceRole') not in ('terrain','grass'):continue
            copy=original.copy();copy.data=original.data.copy();target.collection.objects.link(copy);copy.matrix_world=local@original.matrix_world
            key=ident+'_TERRAIN' if original.get('AppearanceRole')=='terrain' else ident+'_GRASS_'+str(gnum)
            if original.get('AppearanceRole')=='grass':gnum+=1
            rec=exporter.record(copy,key,original['AppearanceRole'],ident);pairs.append((copy,rec))
            if rec['role']=='terrain':terrain_record=rec
        m=meta[source_row['id']];terrain=terrain_record
        definitions[ident]=dict(Id=ident,WorldId='EMBERFALL',Role='ENTRY' if index==1 else 'PATH',Sockets=m['sockets'],Boundary=m.get('Boundary',baseline.get(source,{}).get('Boundary')),MeshYawOffset=0,CollisionTemplate='EF_BATCH2_COLLISION_'+source,Supports=['Traversal'],SizeX=256,SizeZ=256,SizeY=terrain['size'][1],GroundOffsetY=terrain['size'][1]/2-terrain['center'][1],AssetKey=terrain['key'],Weight=1,CanonicalSource=source)
        assert definitions[ident]['Boundary']
    groups={}
    for o in scene.objects:
        if o.type!='MESH' or o.hide_render or o.get('CollisionFidelity') or o.name=='Five_Stud_Human':continue
        if o in placement_objects and o.get('AppearanceRole') in ('terrain','grass'):continue
        group='scenery' if o.get('NonPlayable') else 'road' if o.name.startswith('CONTINUOUS_ROAD') else 'smoke' if 'Smoke' in o.name or 'smoke' in o.name else 'fire' if any('flame' in mat.name.lower() or 'core' in mat.name.lower() for mat in o.data.materials) else 'props'
        groups.setdefault(group,[]).append(o)
    for group,objects in groups.items():pairs.extend(exporter.batches(objects,target,'EF_BATCH2_REVIEW_'+group.upper(),group))
    if '--repair-bounds' in sys.argv or '--repair-cell' in sys.argv:
        repair_bounds(target,pairs)
        return
    files=exporter.export_files(target,pairs,'EF_BATCH2_REVIEW_VISUAL')
    source_manifest=json.loads((OUT/'source_export_manifest.json').read_text())
    old_mapping=json.loads((ROOT/'tools/studio/emberfall_walkthrough/asset_mapping.json').read_text())
    collision=[dict(r) for r in source_manifest['assets']+old_mapping if r['role']=='collision' and r['chunk'] in canonical]
    data=dict(layout='Combined2 — long repeated route /24',rows=rows,kit=definitions,assets=[r for o,r in pairs]+collision,route=report['route'],spawn=report['route'][12][:3],importYaw=180,appearanceMode='BoundedCombined2SemanticSnapshot',collisionTemplates={source:'EF_BATCH2_COLLISION_'+source for source in canonical},canonicalLibrarySources=17,reviewSourceUses=len(canonical),snapshotOnly=True)
    (OUT/'review_data.json').write_text(json.dumps(data,separators=(',',':')))
    result=dict(files=files,visual_meshes=len(pairs),visual_triangles=sum(r['triangles'] for o,r in pairs),unique_collision=len(collision),placed_collision=sum(meta[r['dressing_source']]['collision_parts'] for r in rows),snapshotOnly=True,records=[r for o,r in pairs])
    (OUT/'review_export_manifest.json').write_text(json.dumps(result,indent=2))
    (HERE/'review_export_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('REVIEW_EXPORT_PASS',json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
