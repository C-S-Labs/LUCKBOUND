"""Blender FBX round-trip validation for the owner-edited delivery.
Run with Blender -b --factory-startup --python this_file. Never opens the owner's scene.
"""
import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/export/worlds/ethereal_scape'
delivery = json.loads((OUT / 'live_delivery.json').read_text())
audit = [a for a in delivery['Audit'] if 'Triangles' in a]
for kind, filename, extra in [(False,'ethereal_scape_structure.fbx',13),
                              (True,'ethereal_scape_props.fbx',13)]:
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj,do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT/filename))
    objects = {o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
    expected = [a for a in audit if a['Prop']==kind]
    assert len(objects) == len(expected)+(extra if kind else 0)
    for row in expected:
        obj = objects[row['Export']]
        obj.data.calc_loop_triangles()
        assert len(obj.data.loop_triangles) == row['Triangles'] < 10000, row
        assert obj.data.color_attributes, row['Export']+' lost vertex colours'
        assert all(abs(s-1)<1e-5 for s in obj.scale)
        lo = [min(v.co[a] for v in obj.data.vertices) for a in range(3)]
        hi = [max(v.co[a] for v in obj.data.vertices) for a in range(3)]
        assert all(abs((lo[a]+hi[a])/2)<.01 for a in range(3)), row['Export']+' noncentral pivot'
        if not kind:
            record = next(p for p in delivery['Parts'][row['Chunk']] if p['AssetKey']=='ES_'+row['Export'].upper())
            sizes = [record['SizeX'],record['SizeY'],record['SizeZ']]
        else:
            records = delivery['Placements'].get(row['Chunk'],[])
            record = next((p for p in records if p['Prop']==row['Export']),None)
            if record is None:
                record = next(a['Fixture'] for a in delivery['Audit'] if 'Fixture' in a and a['Fixture']['Prop']==row['Export'])
            sizes = record['S']
        assert all(abs(hi[a]-lo[a]-sizes[a])<.01 for a in range(3)), (row['Export'],lo,hi,sizes)
    print('PASS:', filename,len(objects),'meshes; colours, triangle counts, axes, dimensions, centred pivots')
assert len(delivery['Boundaries']) == 35
assert len(delivery['Parts']) == 42
print('PASS: 41 registered pieces plus one conditional room, 35 boundary groups')
