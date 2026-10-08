"""Cheap saved readback and contact sheet for the foundation study, no exports."""
import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
HERE = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallFoundation.blend'))
scene = bpy.context.scene
report = json.loads((OUT/'foundation_technical_report.json').read_text())
# Frame the actual narrow molten surface rather than its occluding foreground.
molten = bpy.data.objects['molten_channel_path_wasteland_fault']
target = molten.matrix_world @ molten.data.vertices[20].co
cam = bpy.data.objects['path_narrow_channel']
cam.location = target+Vector((-16, -18, 18))
cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects['terrain_meso']
cam.location = (-37, -457, 33)
cam.rotation_euler = (Vector((-76, -507, 12))-cam.location).to_track_quat('-Z', 'Y').to_euler()
active = scene.camera
for name in ('path_narrow_channel', 'terrain_meso'):
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
scene.camera = active
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallFoundation.blend'))
deps = bpy.context.evaluated_depsgraph_get()
excluded = set(bpy.data.collections['ReuseLibrary_SOURCE_ONLY'].all_objects) | set(bpy.data.collections['Scenery_8_SOURCE_LIBRARY'].all_objects)
visible = [o for o in scene.objects if o not in excluded and not o.hide_render]
evaluated_tris = 0
for o in visible:
    if o.type != 'MESH':
        continue
    ev = o.evaluated_get(deps)
    d = ev.to_mesh()
    d.calc_loop_triangles()
    evaluated_tris += len(d.loop_triangles)
    ev.to_mesh_clear()
report['saved_readback'] = {'scene': scene.name, 'scene_objects_including_libraries': len(scene.objects),
                            'visible_objects': len(visible), 'visible_mesh_objects': sum(o.type == 'MESH' for o in visible),
                            'evaluated_visible_triangles': evaluated_tris, 'terrain_checks': [], 'socket_checks': []}
report['visible_objects'] = len(visible)
for row in report['chunks']:
    ob = bpy.data.objects['chunk_'+row['name']]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    edges = sum(not e.is_manifold for e in bm.edges)
    bm.free()
    bounds = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
    row['world_bounds'] = [[round(min(p[a] for p in bounds), 4) for a in range(3)], [round(max(p[a] for p in bounds), 4) for a in range(3)]]
    row['terrain_local_origin'] = list(ob.location)
    row['nonmanifold_edges'] = edges
    assert edges == 0
    assert abs(row['world_bounds'][1][0]-row['world_bounds'][0][0]-256) < .001
    assert abs(row['world_bounds'][1][1]-row['world_bounds'][0][1]-256) < .001
    report['saved_readback']['terrain_checks'].append({'name': row['name'], 'closed': True, 'footprint_exact': True})


def sample(ob, x, y):
    t = BVHTree.FromPolygons([v.co for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons])
    p, n, _, _ = t.ray_cast(Vector((x, y, 250)), Vector((0, 0, -1)))
    assert p is not None and n.z > .9
    return (ob.matrix_world @ p).z


route = [report['chunks'][k] for k in (0, 1, 2, 4, 5)]
for left, right in zip(route, route[1:]):
    a = bpy.data.objects['chunk_'+left['name']]
    b = bpy.data.objects['chunk_'+right['name']]
    gaps = [abs(sample(a, x, 127.999)-sample(b, x, -127.999)) for x in (-20, 0, 20)]
    assert max(gaps) < .01
    report['saved_readback']['socket_checks'].append({'pair': [left['name'], right['name']], 'max_gap': max(gaps)})
a = bpy.data.objects['chunk_'+report['chunks'][2]['name']]
b = bpy.data.objects['chunk_'+report['chunks'][3]['name']]
gaps = [abs(sample(a, 127.999, y)-sample(b, y, 127.999)) for y in (-20, 0, 20)]
assert max(gaps) < .01
report['saved_readback']['socket_checks'].append({'pair': ['combat', 'side'], 'max_gap': max(gaps)})
report['review_images'] = sorted(p.name for p in OUT.glob('*.png') if p.name != 'foundation_contact_sheet.png')
assert len(report['review_images']) == 17
report['visual_assessment'] = {'glow_minimized': 'Localized ruined outskirts, broken volcanic shelves and infected plants remain readable without lava emission or orange lava color. Wide overview still has repeated longitudinal shelf rhythms and broad plain aprons. Identity gate is partial, not production accepted.',
                             'remaining': ['Authored profiles remain too ribbon-like in parts of the overview.', 'Some bank faces are overly planar; coarse masonry needs stronger stress/failure.', 'Far apron is contextual review ground, not a finished scenery kit.', 'Procedural materials, smoke and color attributes are Blender-only.', 'Collision and vertical socket measurement require later generic work and owner acceptance.']}
for path in [OUT/'foundation_technical_report.json', HERE/'foundation_technical_report.json']:
    path.write_text(json.dumps(report, indent=2), encoding='utf8')
print('SAVED_READBACK', json.dumps({k: report['saved_readback'][k] for k in ('visible_objects', 'visible_mesh_objects', 'evaluated_visible_triangles')}))
