"""Read-only VV authored exit/width audit, including every asymmetric gate.

Measures exact triangles/materials, not flat terrain or query hulls alone.
Use the protected Blender launcher with the preserved production export input.
"""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    root = Path(__file__).resolve().parents[4]
    ledger = json.loads((root / 'assets/export/worlds/verdant_valley_staging_refresh/export_manifest.json').read_text())
    baseline = json.loads((root / 'docs/VV_SOCKET_AUDIT_AFTER.json').read_text())
    definitions = {c['id']: c for c in baseline['chunks']}
    records = {f['chunk']: f['sources'][0] for f in ledger['files'] if f['category'] == 'structure' and f['chunk']}
    source = Path(bpy.data.filepath)
    report = {'source': str(source), 'source_matches':hashlib.sha256(source.read_bytes()).hexdigest()==ledger['source_sha256'],
              'coordinate_map':'Native export (x,y,z) -> imported Roblox (-x,z,y), then clockwise art yaw',
              'method':'Exact triangle rays at 0.5-stud lateral spacing ±100, depths 2/6/12/24/40; report contiguous flat pad and material runs separately.',
              'chunks': []}
    for obj in sorted(bpy.data.collections['VV_STRUCTURE'].all_objects,key=lambda o:o.name):
        ident = 'VV_' + obj.name.removeprefix('chunk_').upper()
        ident = {'VV_SIDE_TREASURE_HOLLOW':'VV_CAP_TREASURE_HOLLOW','VV_SIDE_WARDENS_CLEARING':'VV_CAP_WARDENS_CLEARING'}.get(ident,ident)
        c=definitions[ident]
        inverse=obj.matrix_world.inverted()
        terrain=BVHTree.FromPolygons([v.co.copy() for v in obj.data.vertices],[list(p.vertices) for p in obj.data.polygons])
        materials=[m.name if m else '' for m in obj.data.materials]
        h=hashlib.sha256()
        h.update(str([list(r) for r in obj.matrix_world]).encode())
        for v in obj.data.vertices:h.update(str(tuple(v.co)).encode())
        for p in obj.data.polygons:h.update(str((tuple(p.vertices),p.material_index,p.use_smooth)).encode())
        row={'id':ident,'name':obj.name,'hint':c['hint'],'sockets':[{k:s[k] for k in ('name','facing','width','kind')} for s in c['sockets']],
             'matches_export_geometry':h.hexdigest()==records[obj.name]['source_digest'], 'materials':materials,'edges':[]}
        for native,(dx,dy),facing in [('+Y',(0,1),180),('+X',(1,0),270),('-Y',(0,-1),0),('-X',(-1,0),90)]:
            runtime=(facing+c['hint'])%360
            edge=192 if ident=='VV_BOSS_SANCTUARY' and dx else 128
            edge_row={'native':native,'runtime_facing':runtime,'slices':[]}
            for depth in (2,6,12,24,40):
                samples=[]
                for t in range(-200,201):
                    lateral=t*.5
                    hit,normal,face,_=terrain.ray_cast(Vector((dx*(edge-depth)-dy*lateral,dy*(edge-depth)+dx*lateral,80)),Vector((0,0,-1)),160)
                    mat=materials[obj.data.polygons[face].material_index] if face is not None else None
                    samples.append({'lateral':lateral,'z':round(hit.z,5) if hit is not None else None,'normal':round(normal.z,5) if normal is not None else None,'material':mat})
                def run_width(predicate):
                    middle=len(samples)//2
                    if not predicate(samples[middle]):return {'width':0,'bounds':None}
                    a=b=middle
                    while a>0 and predicate(samples[a-1]):a-=1
                    while b+1<len(samples) and predicate(samples[b+1]):b+=1
                    return {'width':samples[b]['lateral']-samples[a]['lateral'],'bounds':[samples[a]['lateral'],samples[b]['lateral']]}
                flat=run_width(lambda p:p['z'] is not None and abs(p['z'])<.35)
                walk=run_width(lambda p:p['z'] is not None and abs(p['z'])<6 and p['normal']>.65)
                material_runs=[]
                for p in samples:
                    if material_runs and material_runs[-1]['material']==p['material']:material_runs[-1]['end']=p['lateral']
                    else:material_runs.append({'start':p['lateral'],'end':p['lateral'],'material':p['material']})
                edge_row['slices'].append({'depth':depth,'flat_pad':flat,'walkable':walk,'material_runs':material_runs,'samples':samples})
            row['edges'].append(edge_row)
        report['chunks'].append(row)
    report['sample_columns']=['lateral','height','normal_z','material_index (-1 means no hit)']
    for c in report['chunks']:
        for edge in c['edges']:
            for sl in edge['slices']:
                sl['samples']=[[p['lateral'],p['z'],p['normal'],c['materials'].index(p['material']) if p['material'] else -1] for p in sl['samples']]
    path=root/'docs/VV_SOCKET_WIDTH_EVIDENCE.json'
    path.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8')
    for c in report['chunks']:
        if any(s['kind']=='WIDE' for s in c['sockets']) or c['id'] in ('VV_MUSHROOM_GLEN','VV_SIDE_FORGOTTEN_TRIAL'):
            print(json.dumps({'id':c['id'],'yaw':c['hint'],'materials':c['materials'],'edges':[{'runtime':e['runtime_facing'],'flat':[(s['depth'],s['flat_pad']['width']) for s in e['slices']],'material':e['slices'][0]['material_runs']} for e in c['edges']]}))
    print('SOURCE_MATCH',report['source_matches'],'GEOMETRY_MATCH',sum(c['matches_export_geometry'] for c in report['chunks']))


if __name__=='__main__':main()
