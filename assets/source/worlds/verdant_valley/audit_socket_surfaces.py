"""Read-only authored terrain/solid-prop opening samples in export-local coordinates.

Run through tools/run_blender.py against the preserved refreshed export input.
No scene saves, exports, regeneration, or security changes.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    root = Path(__file__).resolve().parents[4]
    ledger = json.loads((root / 'assets/export/worlds/verdant_valley_staging_refresh/export_manifest.json').read_text())
    source = Path(bpy.data.filepath)
    report = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'matches_export_source': hashlib.sha256(source.read_bytes()).hexdigest() == ledger['source_sha256'],
              'coordinates': 'Export-local Blender: X right, Y horizontal, Z up. Cardinal labels are native, not inferred Roblox import orientation.',
              'chunks': []}
    structures = bpy.data.collections['VV_STRUCTURE'].all_objects
    solids = bpy.data.collections['VV_PROPS_SOLID'].all_objects
    records = {f['chunk']: f['sources'][0] for f in ledger['files'] if f['category'] == 'structure' and f['chunk']}
    for obj in sorted(structures, key=lambda x: x.name):
        inverse = obj.matrix_world.inverted()
        def bvh(mesh_obj):
            matrix = inverse @ mesh_obj.matrix_world
            vertices = [matrix @ v.co for v in mesh_obj.data.vertices]
            return BVHTree.FromPolygons(vertices, [list(f.vertices) for f in mesh_obj.data.polygons])
        terrain = bvh(obj)
        props = [(p.name, bvh(p)) for p in solids if p.name.startswith(obj.name + '__')]
        h = hashlib.sha256()
        h.update(str([list(r) for r in obj.matrix_world]).encode())
        for v in obj.data.vertices: h.update(str(tuple(v.co)).encode())
        for f in obj.data.polygons: h.update(str((tuple(f.vertices), f.material_index, f.use_smooth)).encode())
        row = {'name': obj.name, 'digest': h.hexdigest(), 'matches_export_geometry': h.hexdigest() == records[obj.name]['source_digest'], 'directions': []}
        for dx,dy,label in [(0,1,'+Y'),(1,0,'+X'),(0,-1,'-Y'),(-1,0,'-X')]:
            edge = 192 if 'boss_sanctuary' in obj.name and dx else 128
            samples = []
            for depth in [0,2,6,12,24,40]:
                for lateral in [-18,-16,-8,0,8,16,18]:
                    p = Vector((dx*(edge-depth)-dy*lateral,dy*(edge-depth)+dx*lateral,80))
                    hit, normal, _, _ = terrain.ray_cast(p,Vector((0,0,-1)),160)
                    obstructions=[]
                    for name, tree in props:
                        ph, pn, _, _ = tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,1)),5)
                        side, _, _, _ = tree.ray_cast(Vector((p.x-2,p.y,3)),Vector((1,0,0)),4)
                        if ph is not None or side is not None: obstructions.append(name)
                    samples.append({'depth':depth,'lateral':lateral,'hit':hit is not None,
                                    'z':round(hit.z,5) if hit is not None else None,
                                    'normal':round(normal.z,5) if normal is not None else None,
                                    'solid_obstruction':obstructions})
            row['directions'].append({'native_direction':label,'samples':samples})
        report['chunks'].append(row)
    destination = root / 'docs/VV_SOCKET_AUTHORED_SURFACES.json'
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chunks':len(report['chunks']),'source_matches':report['matches_export_source'],
                      'geometry_matches':sum(c['matches_export_geometry'] for c in report['chunks']), 'report':str(destination)}))


if __name__ == '__main__':
    main()
