"""Finalize and read back the thirteen saved Emberfall study assets, no exports."""
import bpy
import importlib.util
import json
from pathlib import Path
from mathutils import Euler

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
spec = importlib.util.spec_from_file_location('emberfall_architecture', HERE/'revise_emberfall_architecture.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def inspect(scene):
    meshes = [o for o in scene.objects if o.type == 'MESH']
    counts = {}
    for ob in meshes:
        ob.data.calc_loop_triangles()
        counts[ob.name] = len(ob.data.loop_triangles)
    return {'objects': len(scene.objects), 'meshes': len(meshes), 'triangles': sum(counts.values()),
            'mesh_triangles': counts, 'collections': [c.name for c in scene.collection.children]}


def main():
    report = json.loads((OUT/'technical_report.json').read_text(encoding='utf8'))
    results = {'independent_assets': {}, 'review_scenes': {}}
    for name in study.NAMES+study.SCENERY:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = OUT/(name+'.blend')
        with bpy.data.libraries.load(str(path), link=False) as (source, target):
            assert name in source.collections
            target.collections = [name]
        group = target.collections[0]
        for library in list(bpy.data.libraries):
            bpy.data.libraries.remove(library)
        scene = bpy.context.scene
        scene.name = name
        scene.collection.children.link(group)
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.scale_length = 1
        scene['README'] = 'Independent 256x256 study asset at local seam datum; no review scenery/layouts or runtime registration. Open surfaces require Studio collision validation.'
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    view = area.spaces.active
                    view.region_3d.view_distance = 390
                    view.region_3d.view_location = (0, 0, 20)
                    view.region_3d.view_rotation = Euler((.95, 0, .55)).to_quaternion()
                    view.shading.color_type = 'MATERIAL'
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        bpy.ops.wm.open_mainfile(filepath=str(path))
        ob = bpy.data.objects[name]
        assert tuple(ob.location) == (0, 0, 0)
        lo, hi = study.bounds(ob)
        assert lo[:2] == [-128, -128] and hi[:2] == [128, 128]
        assert len(bpy.data.scenes) == 1
        assert not any('REVIEW_ONLY' in c.name or 'ReviewLayout' in c.name for c in bpy.data.collections)
        row = inspect(bpy.context.scene)
        row['origin'] = list(ob.location)
        row['structure_dimensions'] = [hi[k]-lo[k] for k in range(3)]
        row['ground_datum_is_center_walk_height'] = name in study.NAMES
        # No face made from three or more vertices on a vertical boundary plane.
        boundary_walls = []
        for p in ob.data.polygons:
            coords = [ob.data.vertices[k].co for k in p.vertices]
            for axis in (0, 1):
                if all(abs(abs(v[axis])-128) < .0001 for v in coords) and max(v.z for v in coords)-min(v.z for v in coords) > .001:
                    boundary_walls.append(p.index)
        assert not boundary_walls
        row['boundary_wall_faces'] = len(boundary_walls)
        results['independent_assets'][name] = row
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    results['saved_blender_scenes'] = [s.name for s in bpy.data.scenes]
    results['flora_hashes'] = {name: study.fingerprint(bpy.data.objects[name].data) for name in report['flora_hashes_before']}
    assert results['flora_hashes'] == report['flora_hashes_before']
    for letter in 'ABC':
        scene = bpy.data.scenes['Architecture_'+letter]
        results['review_scenes'][letter] = inspect(scene)
        root = scene.collection.children[0]
        # Resolve by collection hierarchy rather than Blender's auto-suffixes.
        played = next(c for c in root.children if c.name.startswith('Playable_5'))
        cells = {}
        for group in played.children:
            placement = next(o for o in group.objects if o.type == 'EMPTY')
            pos = tuple(placement.location)
            cells[(round(pos[0]/256), round(pos[1]/256))] = (group, pos, 'PLAYABLE')
        for parent in root.children:
            if parent.name.startswith(('Scenery_instances', 'Distant_ring')):
                for group in parent.children:
                    placement = next(o for o in group.objects if o.type == 'EMPTY')
                    pos = tuple(placement.location)
                    cells[(round(pos[0]/256), round(pos[1]/256))] = (group, pos, placement['AssetCollection'])
        results['review_scenes'][letter]['saved_seams'] = study.check_arrangement(cells)
    (OUT/'saved_scene_verification.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    (HERE/'architecture_technical_report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    (HERE/'architecture_saved_verification.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    print('SAVED_ARCHITECTURE_VERIFIED', {name: (row['objects'], row['triangles']) for name, row in results['independent_assets'].items()})


if __name__ == '__main__':
    main()
