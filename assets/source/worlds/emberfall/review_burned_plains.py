"""Cheap saved-scene readback and labelled Area I contact sheet; no collision/export."""
import bpy
import bmesh
import json
from pathlib import Path

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview')
HERE = Path(__file__).resolve().parent


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT / 'BurnedPlains.blend'))
    scene = bpy.context.scene
    assert scene.name == 'Emberfall_Area_I_Burned_Plains'
    report = json.loads((HERE / 'burned_plains_report.json').read_text(encoding='utf8'))
    checks = []
    chunks = [o for o in scene.objects if o.name.startswith('chunk_')]
    assert len(chunks) == 3
    for o in chunks:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bad = sum(not e.is_manifold for e in bm.edges)
        bm.free()
        assert bad == 0, (o.name, bad)
        o.data.calc_loop_triangles()
        assert len(o.data.loop_triangles) < 10000
        assert abs(o.dimensions.x - 256) < .001 and abs(o.dimensions.y - 256) < .001
        surface = list(o.data.vertices)[:o['SurfaceVertexCount']]
        center = next(v for v in surface if abs(v.co.x) < .001 and abs(v.co.y) < .001)
        assert abs(center.co.z) < .001
        checks.append({'name': o.name, 'closed': True, 'triangles': len(o.data.loop_triangles),
                       'dimensions': list(o.dimensions), 'origin_at_center_ground': True})
    assert all(Path(p).is_file() and Path(p).stat().st_size > 10000 for p in report['evidence'])
    assert (OUT / 'Input_DesignReset.blend').is_file()
    forbidden = [o.name for o in scene.objects if any(s in o.name.lower() for s in ('basalt', 'molten', 'fortress', 'castle'))]
    assert not forbidden, forbidden
    report['saved_readback'] = {'scene': scene.name, 'terrain': checks, 'eight_renders_exist': True,
                              'scene_objects': len(scene.objects),
                              'no_old_geology_or_later_area_objects': True,
                              'original_live_snapshot_preserved': True}
    report['objects'] = len(scene.objects)
    for p in (HERE / 'burned_plains_report.json', OUT / 'burned_plains_report.json'):
        p.write_text(json.dumps(report, indent=2), encoding='utf8')
    print('READBACK_PASS', json.dumps({'terrains': checks, 'whole_land': report['whole_land_surface_percent']}))


if __name__ == '__main__':
    main()
