"""Cliff Passage zoned dressing using linked established assets and one shared vine.

Run once in the current owner scene. Terrain/cliffs/collision are immutable.
Review mode runs in a background copy and never saves camera/visibility changes.
"""
import bpy
import sys
import json
import math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fit_cliff_passage_top import object_hash

ROOT = Path('E:/BlenderAIProjects/Projects')
CHUNK = 'chunk_path_cliff_passage'
# Revised image: central corridor about 40 studs, yellow strips about 19 each.
PROTECTED_HALF_WIDTH = 21


def bounds(obj):
    inv = bpy.data.objects[CHUNK].matrix_world.inverted()
    points = [inv @ obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return ([min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)])


def vine_template():
    """The sole permitted new prop: one shared, faceted hanging vine asset."""
    if 'VV_Vine' in bpy.data.objects:
        return bpy.data.objects['VV_Vine']
    from scatter_sparse_chunks import MeshBuilder
    m = MeshBuilder()
    nodes = [(0, 0, 0), (.45, 0, -1.8), (-.30, 0, -3.9), (.60, 0, -6.2),
             (.20, 0, -8.0), (-.50, 0, -10.7), (.30, 0, -13.4), (0, 0, -16)]
    for a, b in zip(nodes, nodes[1:]):
        m.beam(a, b, .075, 0)
    # Alternating unequal leaves with intentional breaks; no ivy blanket.
    for i, z in enumerate([-.5, -1.3, -2.2, -3.0, -4.4, -5.0, -6.1, -6.8,
                           -8.2, -8.9, -10.1, -11.7, -12.3, -13.4, -14.9]):
        sign = -1 if i % 2 else 1
        width = [.80, 1.05, .65, .88][i % 4]
        a, b = next((a, b) for a, b in zip(nodes, nodes[1:]) if a[2] >= z >= b[2])
        stem_x = a[0] + (b[0]-a[0])*(z-a[2])/(b[2]-a[2])
        m.add([(stem_x, 0, z), (stem_x+sign*width*.48, .035, z+.22),
               (stem_x+sign*width, .08, z-.22), (stem_x+sign*width*.46, .13, z-.66),
               (stem_x+sign*width*.46, -.025, z-.17)],
              [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], 1 + i % 2)
    obj = m.finish('VV_Vine', bpy.data.collections['Temp'],
                   [bpy.data.materials[n] for n in ('VV_DetailMoss', 'VV_Leaf', 'VV_LeafLight')])
    obj.location = bpy.data.collections['Temp'].objects['Star_bush'].location + Vector((8, 0, 16))
    obj['CanCollide'] = False
    obj['approved_exception'] = 'Owner permits one reusable vine when no suitable existing asset exists.'
    return obj


def finish_zones():
    chunk = bpy.data.objects[CHUNK]
    assert not chunk.get('zone_finish'), 'Already applied; preserve manual placement edits.'
    # Owner has already removed the previous-pass oak-derived trees.
    prior = [o for o in bpy.data.objects if o.name.startswith(CHUNK+'__environment_tree_')]
    removable = {o.name for o in prior}
    protected = {o.name: object_hash(o) for o in bpy.data.objects if o.name not in removable}
    terrain = BVHTree.FromObject(chunk, bpy.context.evaluated_depsgraph_get())
    made, sources, contacts = [], {}, []

    def ground(x, y):
        hit, normal, index, _ = terrain.ray_cast(Vector((x, y, 180)), Vector((0, 0, -1)), 360)
        assert hit is not None and normal.z > .5, (x, y, 'no usable support')
        assert 'Grass' in chunk.data.materials[chunk.data.polygons[index].material_index].name, (x, y)
        return hit, normal

    def linked(source, label, matrix, solid=False):
        obj = source.copy()
        obj.data = source.data  # Genuine linked instance; no new tree/rock/vegetation mesh.
        obj.name = CHUNK+'__finish_'+label
        bpy.data.collections['VV_PROPS_SOLID' if solid else 'VV_PROPS_NONSOLID'].objects.link(obj)
        obj.matrix_world = matrix
        obj.hide_render = obj.hide_viewport = False
        obj.hide_set(False)
        obj['zone_finish'] = CHUNK
        obj['reference_source'] = source.name
        obj['CanCollide'] = solid
        sources[obj.name] = source.name
        made.append(obj)
        return obj

    for o in prior:
        bpy.data.objects.remove(o, do_unlink=True)

    # Six established reference-tree assemblies, all full canopy bounds outside yellow.
    trees = [(-36, -94, 'chunk_deep_clearing__detail_scatter_tree_01', .95, 1.4),
             (30, 97, 'chunk_side_wardens_clearing__detail_scatter_tree_02', .85, -1.2),
             (-23, -58, 'chunk_deep_clearing__detail_scatter_tree_02', 1.08, .2),
             (30, -59, 'chunk_side_wardens_clearing__detail_scatter_tree_01', .90, 2.3),
             (-18, 60, 'chunk_side_wardens_clearing__detail_scatter_tree_02', 1.04, -.6),
             (35, 58, 'chunk_deep_clearing__detail_scatter_tree_01', .80, 1.7)]
    for i, (x, y, prefix, scale, angle) in enumerate(trees, 1):
        trunk, crown = [bpy.data.objects[prefix+'_'+s] for s in ('trunk', 'canopy')]
        anchor = Vector((trunk.location.x, trunk.location.y,
                         min((trunk.matrix_world @ v.co).z for v in trunk.data.vertices)))
        hit, normal = ground(x, y)
        burial = .35 if normal.z > .9 else .65
        transform = (Matrix.Translation(chunk.matrix_world @ (hit-Vector((0, 0, burial))))
                     @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Scale(scale, 4)
                     @ Matrix.Translation(-anchor))
        for source, role in ((trunk, 'trunk'), (crown, 'canopy')):
            linked(source, f'tree_{i:02d}_{role}', transform @ source.matrix_world, role == 'trunk')

    def prop(kind, x, y, scale, angle, label, solid=False):
        source = bpy.data.collections['Temp'].objects[kind]
        hit, normal = ground(x, y)
        linear = source.matrix_world.copy()
        linear.translation = Vector((0, 0, 0))
        # Low ground cover follows slope; rocks retain their faceted model silhouette.
        tilt = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4() if kind != 'rock' else Matrix.Identity(4)
        matrix = tilt @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Scale(scale, 4) @ linear
        points = [matrix @ v.co for v in source.data.vertices]
        anchor = Vector(((min(p.x for p in points)+max(p.x for p in points))/2,
                         (min(p.y for p in points)+max(p.y for p in points))/2,
                         min(p.z for p in points)))
        matrix.translation = chunk.matrix_world @ hit - anchor
        obj = linked(source, label, matrix, solid)
        bpy.context.view_layer.update()
        bottom = min((obj.matrix_world @ v.co).z for v in source.data.vertices)
        gaps = []
        for v in source.data.vertices:
            p = chunk.matrix_world.inverted() @ obj.matrix_world @ v.co
            if p.z < bottom + obj.dimensions.z*.48:
                h, _ = ground(p.x, p.y)
                gaps.append(p.z-h.z)
        obj.location.z -= max(gaps, default=0) + (.12 if kind == 'rock' else .05)
        return obj

    # Eight unequal path-side pockets, each short and broken by long quiet stretches.
    pockets = [(-105, -25.7, [('grass_tuft', 0, 0, .9), ('Star_bush', 3.1, -.2, .65), ('rock', -2.5, -.8, .22)]),
               (-57, -24.9, [('Star_bush', 0, 0, .75), ('grass_tuft', 3.5, -.4, 1.0), ('grass_tuft', -2.1, .5, .65)]),
               (-8, -25.3, [('grass_tuft', 0, 0, 1.05), ('rock', 3.2, -.5, .28), ('Star_bush', 6.1, -.3, .60), ('grass_tuft', 8.1, .4, .75)]),
               (66, -25.2, [('Star_bush', 0, 0, .70), ('grass_tuft', -3.1, -.5, .9), ('rock', 3.5, -.4, .24)]),
               (-85, 25.6, [('Star_bush', 0, 0, .70), ('grass_tuft', 3.5, -.4, .85), ('rock', -3.0, .1, .23)]),
               (-23, 25.2, [('grass_tuft', 0, 0, .9), ('Star_bush', 4.2, .5, .75), ('grass_tuft', 6.7, -.1, .70)]),
               (38, 25.6, [('Star_bush', 0, 0, .78), ('rock', -3.0, .5, .26), ('grass_tuft', 3.4, -.6, 1.0), ('grass_tuft', 5.9, .3, .7)]),
               (108, 25.8, [('grass_tuft', 0, 0, 1.1), ('Star_bush', -3.5, .2, .70), ('rock', 2.8, .6, .24)])]
    for i, (x, y, rows) in enumerate(pockets, 1):
        for j, (kind, dx, dy, scale) in enumerate(rows, 1):
            prop(kind, x+dx, y+dy, scale, i*.83+j*.71, f'yellow_{i:02d}_{j:02d}_{kind}')

    # Upper shelves and rear shoulders: readable boulder/tree combinations, not a ring.
    exterior = [
        ('rock', -34, -58, 1.45, .2), ('rock', -39, -62, .8, 1.5),
        ('Star_bush', -29, -64, 1.1, -.4), ('grass_tuft', -20, -67, 1.5, .9),
        ('rock', 19, -63, 1.2, -1.1), ('rock', 14, -67, .65, .4),
        ('Star_bush', 31, -66, 1.1, 2.2), ('grass_tuft', 24, -69, 1.3, .5),
        ('rock', -7, 63, 1.7, 1.0), ('rock', -1, 65, .9, -.6),
        ('Star_bush', -18, 69, 1.2, .6), ('grass_tuft', -25, 65, 1.45, -1.0),
        ('Star_bush', 28, 63, 1.05, 1.4), ('grass_tuft', 39, 64, 1.2, .8),
        ('rock', 12, -87, 1.75, .4), ('rock', 5, -93, 1.05, -1.3),
        ('rock', 16, -96, .55, 2.0), ('Star_bush', 4, -98, 1.15, .3),
        ('grass_tuft', 16, -102, 1.2, 1.7),
        ('rock', -18, 88, 1.55, -1.3), ('rock', -24, 91, .85, .2),
        ('Star_bush', -9, 91, 1.2, .6), ('grass_tuft', -15, 96, 1.4, -1.0),
        ('Star_bush', -44, -89, 1.1, .5), ('grass_tuft', -40, -100, 1.3, .4),
        ('Star_bush', 24, 92, 1.0, -.2), ('grass_tuft', 35, 104, 1.2, 2.0)]
    for i, (kind, x, y, scale, angle) in enumerate(exterior, 1):
        prop(kind, x, y, scale, angle, f'exterior_{i:02d}_{kind}', kind == 'rock')

    vine = vine_template()
    for i, (side, number, x, top, length, width) in enumerate([
            (-1, 1, -38, 26.0, 16.0, 1.70), (-1, 1, -34, 26.8, 11.5, 1.20),
            (-1, 1, -24, 26.4, 18.2, 1.45), (1, 2, 43, 32.0, 9.0, 1.10),
            (1, 2, 51, 31.0, 5.8, .90)], 1):
        wall = bpy.data.objects[f'{CHUNK}__cliff_{number:02d}']
        wall_bvh = BVHTree.FromObject(wall, bpy.context.evaluated_depsgraph_get())
        def face_at(xx, zz):
            origin = wall.matrix_world.inverted() @ (chunk.matrix_world @ Vector((xx, 0, zz)))
            direction = wall.matrix_world.to_3x3().inverted() @ Vector((0, side, 0))
            hit, _, _, _ = wall_bvh.ray_cast(origin, direction, 150)
            assert hit is not None, (xx, zz, 'missing cliff face')
            return wall.matrix_world @ hit
        a, b = face_at(x, top), face_at(x, top-length)
        z_axis = (a-b).normalized()
        x_axis = Vector((-side, 0, 0))
        y_axis = z_axis.cross(x_axis).normalized()
        # A rigid instance hugs the broad wall plane; no per-placement mesh generation.
        matrix = Matrix.Identity(4)
        for r in range(3):
            matrix[r][0] = x_axis[r]*width
            matrix[r][1] = y_axis[r]
            matrix[r][2] = z_axis[r]*(a-b).length/16
        matrix.translation = a+y_axis*.16
        obj = linked(vine, f'wall_vine_{i:02d}', matrix)
        bpy.context.view_layer.update()
        # Keep even the thin stems visible where adjacent broad faces change slope.
        mesh_gaps = []
        for v in vine.data.vertices:
            p = matrix @ v.co
            local = chunk.matrix_world.inverted() @ p
            origin = wall.matrix_world.inverted() @ (chunk.matrix_world @ Vector((local.x, 0, local.z)))
            hit, _, _, _ = wall_bvh.ray_cast(origin, Vector((0, side, 0)), 150)
            if hit is not None:
                mesh_gaps.append(-side*(p.y-(wall.matrix_world @ hit).y))
        shift = max(0, .04-min(mesh_gaps))
        matrix.translation.y -= side*shift
        obj.matrix_world = matrix
        deviations = []
        for t in (0, .2, .4, .6, .8, 1):
            p = matrix @ Vector((0, 0, -16*t))
            local = chunk.matrix_world.inverted() @ p
            deviations.append((p-face_at(local.x, local.z)).dot(y_axis))
        contacts.append({'name': obj.name, 'axis_contact_range': [min(deviations), max(deviations)],
                         'mesh_face_gap_range': [min(mesh_gaps)+shift, max(mesh_gaps)+shift]})
        assert max(mesh_gaps)+shift < .55, contacts[-1]
        assert max(abs(d) for d in deviations) < .65, contacts[-1]

    bpy.context.view_layer.update()
    for obj in made:
        lo, hi = bounds(obj)
        assert lo[1] >= 21 or hi[1] <= -21, ('red encroachment', obj.name)
        in_yellow = min(abs(lo[1]), abs(hi[1])) < 40
        if in_yellow:
            assert not obj['CanCollide'] and any(c.name == 'VV_PROPS_NONSOLID' for c in obj.users_collection), obj.name
            assert any(s in obj.name for s in ('yellow_', 'wall_vine_')), obj.name
        assert max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])) < 127, obj.name
        assert obj.data is bpy.data.objects[sources[obj.name]].data, obj.name
    assert all(object_hash(bpy.data.objects[n]) == h for n, h in protected.items())
    chunk['zone_finish'] = '2026-09-30: annotated red/yellow zones, linked references, shared vine'
    record = {'red_half_width': 21, 'yellow_outer_width': 40, 'unchanged_existing_objects': len(protected),
              'previous_generated_trees_removed_by_owner': not prior, 'reference_trees': len(trees),
              'yellow_ground_props': sum('yellow_' in o.name for o in made),
              'exterior_ground_props': len(exterior), 'vine_instances': len(contacts),
              'sources': sources, 'vine_contacts': contacts, 'removed': sorted(removable)}
    (ROOT/'Cliff_Zones_Record.json').write_text(json.dumps(record, indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VerdantValley_Cleanup.blend'))
    print(json.dumps({k: v for k, v in record.items() if k not in ('sources', 'vine_contacts')}))


def review():
    out = ROOT/'Cliff_Zones_Review'/('Before' if '--before' in sys.argv else 'After')
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    shade = scene.display.shading
    shade.light = 'STUDIO'
    shade.color_type = 'MATERIAL'
    shade.show_shadows = shade.show_cavity = True
    shade.cavity_type = 'WORLD'
    shade.background_type = 'WORLD'
    scene.world.color = (.19, .20, .19)
    scene.view_settings.view_transform = 'Standard'
    camera = bpy.data.objects.new('EnvironmentReviewCamera', bpy.data.cameras.new('EnvironmentReviewCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.clip_end = 5000
    chunk = bpy.data.objects[CHUNK]
    for o in bpy.data.objects:
        o.hide_render = not (o.name == CHUNK or o.name.startswith(CHUNK+'__'))
    # Rotated top matches annotation: corridor vertical, north end at top.
    views = [('Overhead', (0, 0, 500), (0, 0, 0), True),
             ('Passage_West', (-113, 0, 7), (60, 0, 9), False),
             ('Passage_East', (113, 0, 7), (-60, 0, 9), False),
             ('Wall_Strong', (-38, 4, 6), (-29, -31, 18), False),
             ('Wall_Sparse', (46, -3, 8), (46, 32, 23), False),
             ('Yellow_South', (-56, -8, 6), (-46, -25, 1.5), False),
             ('Yellow_North', (22, 6, 9), (37, 26, 5), False),
             ('Exterior_South', (-80, -160, 43), (-5, -76, 12), False),
             ('Exterior_North', (80, 160, 52), (0, 75, 22), False),
             ('Exterior_West', (-166, -54, 39), (-48, -45, 22), False),
             ('Exterior_East', (166, 53, 47), (45, 47, 25), False)]
    for label, position, target, ortho in views:
        camera.location = chunk.location + Vector(position)
        camera.rotation_euler = (chunk.location+Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
        if ortho:
            camera.rotation_euler.z = math.pi/2
        camera.data.type = 'ORTHO' if ortho else 'PERSP'
        camera.data.ortho_scale = 370
        camera.data.lens = 29
        scene.render.filepath = str(out/(label+'.png'))
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    review() if '--review' in sys.argv else finish_zones()
