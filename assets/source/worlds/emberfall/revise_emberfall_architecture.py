"""Saved-source Emberfall seam/scenery/vertical study; protected launcher only.

No exports or runtime registration. Existing flora meshes/materials and selected
disconnected basalt modules are read from the first-pass saved scene, not rebuilt.
"""
import bpy
import hashlib
import importlib.util
import json
import math
import random
import shutil
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/BlenderAIProjects/Runtime/Emberfall_Prototype/EmberfallPrototype.blend')
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
NAMES = ['chunk_entry_ash_plain', 'path_column_pass', 'chunk_column_forest',
         'side_lava_overlook', 'cap_collapsed_pass']
ROLES = ['ENTRY', 'PATH', 'COMBAT', 'SIDE', 'CAP']
OPENINGS = [['N'], ['S', 'N'], ['S', 'N', 'E'], ['W'], ['S']]
POSITIONS = [(0, -256, 0), (0, 0, 28), (0, 256, 56), (256, 256, 56), (0, 512, 56)]
SCENERY = ['scenery_ashland_a', 'scenery_basalt_ridge_a', 'scenery_basalt_ridge_high',
           'scenery_lava_field_a', 'scenery_ravine_a', 'scenery_drained_flora_a',
           'scenery_charred_flora_a', 'scenery_foothill_a']
BAND = 24
STEP = 56  # provisional study value, never a locked production tuning
REPORT = {'units': 'one Blender metre = one Roblox stud', 'seam_band_studs': BAND,
          'provisional_elevation_step': STEP, 'runtime_modified': False}


def smooth(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)


def level(y):
    return STEP*smooth(-104, 104, y)


def shoulder(x, y):
    # A symmetric LOW_ROLL profile, flat over each 56-stud mouth and the
    # outer 24 studs in the inward direction. Compatible at quarter turns.
    return 4*smooth(32, 104, abs(x))*smooth(32, 104, abs(y))


def interior(x, y):
    return smooth(24, 52, min(128-abs(x), 128-abs(y)))


def hill(x, y, cx, cy, sx, sy, z, power=2):
    return z*math.exp(-abs((x-cx)/sx)**power-abs((y-cy)/sy)**power)


def playable_height(i, x, y):
    base = level(y)-28 if i == 1 else 0
    if i == 0:
        relief = hill(x, y, -63, -38, 46, 57, 7)+hill(x, y, 74, 49, 30, 53, 3)
    elif i == 1:
        relief = hill(x, y, -67, 10, 31, 74, 19, 4)
        relief += hill(x, y, 70, -27, 18, 58, -21, 4)
        relief += hill(x, y, 63, 68, 38, 22, 12)
    elif i == 2:
        relief = hill(x, y, -64, 28, 27, 46, -19, 4)
        relief += hill(x, y, 59, 61, 35, 26, 17, 4)
        relief += hill(x, y, -56, -67, 46, 21, 9, 4)
        relief *= smooth(29, 48, math.hypot(x, y))
    elif i == 3:
        relief = 22*smooth(-75, 70, x)*math.exp(-(y/74)**4)
        relief += hill(x, y, 73, -55, 25, 25, -12)
        relief *= smooth(12, 40, math.hypot(x, y))
    else:
        relief = hill(x, y, 0, 48, 76, 32, 23, 4)
        relief += hill(x, y, -65, -28, 30, 47, 8)
        relief *= smooth(20, 43, math.hypot(x, y))
    relief *= smooth(12, 36, math.hypot(x, y))
    return base+shoulder(x, y)+interior(x, y)*relief


def scenery_height(family, x, y):
    if family == 0:
        relief = hill(x, y, -22, 25, 86, 65, 9)
    elif family == 1:
        relief = hill(x, y, 15, 23, 26, 91, 61, 4)+hill(x, y, -27, 62, 30, 31, 23)
    elif family == 2:
        relief = hill(x, y, 17, 5, 28, 86, 103, 4)+hill(x, y, -41, -36, 35, 52, 40)
    elif family == 3:
        relief = hill(x, y, 11, 4, 79, 74, -39, 4)
    elif family == 4:
        relief = hill(x, y, -2, -3, 21, 85, -55, 4)+hill(x, y, 68, 24, 22, 75, 17)
    elif family == 5:
        relief = hill(x, y, -34, 24, 67, 49, 14)+hill(x, y, 62, -30, 19, 43, 16)
    elif family == 6:
        relief = hill(x, y, 28, -20, 31, 64, -17, 4)+hill(x, y, -44, 22, 34, 52, 27)
    else:
        relief = hill(x, y, 26, 7, 69, 91, 56, 4)+hill(x, y, -49, 67, 32, 38, 25)
    return shoulder(x, y)+interior(x, y)*relief


def fingerprint(data):
    return hashlib.sha256(repr(([(tuple(v.co)) for v in data.vertices],
        [tuple(p.vertices) for p in data.polygons],
        [p.material_index for p in data.polygons],
        [m.name if m else None for m in data.materials])).encode()).hexdigest()


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else bpy.context.scene.collection.children).link(c)
    return c


def mesh(name, vertices, faces, collection, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    for material in materials:
        data.materials.append(material)
    data.update()
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    return ob


def terrain_data(fn, spacing):
    axis = sorted(set(range(-128, 129, spacing)) | {-104, -32, -28, 0, 28, 32, 104})
    n = len(axis)
    vertices = [(x, y, fn(x, y)) for y in axis for x in axis]
    faces = []
    for j in range(n-1):
        for k in range(n-1):
            a = j*n+k
            faces += [(a, a+1, a+n+1), (a, a+n+1, a+n)]
    if spacing > 8:
        # Cheap interior, exact playable perimeter stations. Matching only
        # the coarser shared vertices leaves interpolation cracks.
        stations = sorted(set(range(-128, 129, 8)) | {-28, 28})
        refined = []
        cache = {(x, y): k for k, (x, y, z) in enumerate(vertices)}
        for face in faces:
            split = False
            for k in range(3):
                a, b, c = face[k], face[(k+1) % 3], face[(k+2) % 3]
                pa, pb = vertices[a], vertices[b]
                for axis in (0, 1):
                    across = 1-axis
                    if pa[axis] == pb[axis] and abs(pa[axis]) == 128:
                        values = [s for s in stations if min(pa[across], pb[across]) < s < max(pa[across], pb[across])]
                        values.sort(reverse=pa[across] > pb[across])
                        ids = [a]
                        for value in values:
                            xy = (pa[axis], value) if axis == 0 else (value, pa[axis])
                            if xy not in cache:
                                cache[xy] = len(vertices)
                                vertices.append((*xy, fn(*xy)))
                            ids.append(cache[xy])
                        ids.append(b)
                        refined.extend((p, q, c) for p, q in zip(ids, ids[1:]))
                        split = True
                        break
                if split:
                    break
            if not split:
                refined.append(face)
        faces = refined
    # Deliberately no skirts, bottom caps, or seam-cover geometry.
    return vertices, faces, axis


def components(data):
    neighbors = [[] for _ in data.vertices]
    for e in data.edges:
        a, b = e.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)
    unseen = set(range(len(data.vertices)))
    result = []
    while unseen:
        pending = [unseen.pop()]
        component = set(pending)
        while pending:
            for other in neighbors[pending.pop()]:
                if other in unseen:
                    unseen.remove(other)
                    component.add(other)
                    pending.append(other)
        result.append(component)
    return result


def retain_columns(i, data, fn):
    candidates = []
    for comp in components(data):
        pts = [data.vertices[k].co for k in comp]
        lo = [min(p[a] for p in pts) for a in range(3)]
        hi = [max(p[a] for p in pts) for a in range(3)]
        cx, cy = (lo[0]+hi[0])/2, (lo[1]+hi[1])/2
        if len(comp) < 200 and max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])) < 100:
            candidates.append((cx, cy, comp))
    # Keep signature modules selectively; geological terrain does the main work.
    candidates.sort(key=lambda q: (q[0], q[1]))
    limits = [2, 6, 4, 2, 4]
    if i == 1:
        candidates = [q for q in candidates if abs(q[0]) > 44]
    chosen = candidates[::max(1, len(candidates)//limits[i])][:limits[i]]
    vertices, faces, indices = [], [], []
    for x, y, comp in chosen:
        delta = fn(x, y)-old.height(i, x, y)
        remap = {}
        for k in sorted(comp):
            remap[k] = len(vertices)
            p = data.vertices[k].co
            vertices.append((p.x, p.y, p.z+delta))
        for p in data.polygons:
            if all(k in comp for k in p.vertices):
                faces.append(tuple(remap[k] for k in p.vertices))
                indices.append(p.material_index)
    REPORT.setdefault('preserved_basalt_modules', {})[NAMES[i]] = len(chosen)
    return vertices, faces, indices


def formation(name, x, y, sx, sy, height, fn, collection, material):
    # Broad tilted, stratified cooled-flow masses; actual bevel/support rings.
    vertices = []
    segments = 18
    base = min(fn(x+sx*math.cos(k*math.tau/8), y+sy*math.sin(k*math.tau/8)) for k in range(8))-4
    height = fn(x, y)+height*.55-base
    for ring, (scale, z) in enumerate([(1, 0), (1.02, .13), (.91, .49), (.84, .54), (.75, .87), (.64, 1)]):
        for k in range(segments):
            a = k*math.tau/segments
            shape = 1+.08*math.sin(a*3+.8)+.04*math.cos(a*5)
            vertices.append((x+sx*scale*shape*math.cos(a)+ring*.5,
                             y+sy*scale*shape*math.sin(a),
                             base+height*z+math.cos(a+.4)*height*.065))
    faces = [tuple(reversed(range(segments)))]
    for ring in range(5):
        for k in range(segments):
            a = ring*segments+k
            b = ring*segments+(k+1)%segments
            faces.append((a, b, b+segments, a+segments))
    faces.append(tuple(range(5*segments, 6*segments)))
    ob = mesh(name, vertices, faces, collection, [material, ASH, BASALT])
    for p in ob.data.polygons:
        p.material_index = 1 if p.index == len(faces)-1 else (2 if 37 <= p.index <= 54 else 0)
    return ob


def append_formation(target, ob):
    offset = len(target[0])
    target[0].extend(tuple(v.co) for v in ob.data.vertices)
    target[1].extend(tuple(offset+k for k in p.vertices) for p in ob.data.polygons)
    target[2].extend(p.material_index for p in ob.data.polygons)
    bpy.data.objects.remove(ob, do_unlink=True)


def ground_materials(data, terrain_faces):
    data.update()
    data.materials.append(GROUND)
    colors = data.color_attributes.new(name='EmberGroundTint', type='FLOAT_COLOR', domain='CORNER')
    for p in data.polygons[:terrain_faces]:
        # No face-level ash rectangles. Smooth weathering islands stay inland;
        # a continuous charcoal surface crosses the shared seam unchanged.
        p.material_index = len(data.materials)-1
        p.use_smooth = True
        for loop_index in p.loop_indices:
            x, y, z = data.vertices[data.loops[loop_index].vertex_index].co
            ash = interior(x, y)*(.42*math.exp(-((x+41)/68)**2-((y-12)/83)**2))
            color = tuple(a+(b-a)*ash for a, b in zip((.073, .088, .103), (.145, .16, .175)))
            colors.data[loop_index].color = (*color, 1)
    for p in data.polygons[terrain_faces:]:
        p.use_smooth = False


def reseat_saved_props(i, group, fn):
    for ob in group.all_objects:
        if ob.type == 'LIGHT':
            ob.location.z = fn(ob.location.x, ob.location.y)+5
        elif ob.type == 'MESH' and ob.name != NAMES[i]:
            if ob.get('LibraryAsset'):
                ob.location.z = fn(ob.location.x, ob.location.y)+.03
            else:
                # Saved joined rubble: preserve each original disconnected shape.
                ob.data = ob.data.copy()
                for comp in components(ob.data):
                    pts = [ob.data.vertices[k].co for k in comp]
                    x = sum(p.x for p in pts)/len(pts)
                    y = sum(p.y for p in pts)/len(pts)
                    delta = fn(x, y)-old.height(i, x, y)
                    for k in comp:
                        ob.data.vertices[k].co.z += delta
                ob.data.update()


def rebuild_playable():
    descriptions = ['Windswept open ashland, retained split fins and drained shelter pockets',
                    'Broad cooled-flow ascent, fractured western terraces and eastern hot cut',
                    'Raised combat shelf, western sunken ravine and asymmetric broken lava plates',
                    'Raised lava overlook, glassy cairn and pale shelf growth',
                    'Raised continuation ending in geological collapse and one buried road fragment']
    assets = []
    for i, name in enumerate(NAMES):
        group = bpy.data.collections[name]
        root = next(o for o in group.objects if o.type == 'EMPTY')
        root.location = (0, 0, 0)
        ob = bpy.data.objects[name]
        fn = lambda x, y, i=i: playable_height(i, x, y)
        old_data = ob.data
        vertices, faces, axis = terrain_data(fn, 8)
        terrain_faces = len(faces)
        # Stable material mapping for new shapes and retained column components.
        mats = [COOLED, ASH, BASALT]
        kept_v, kept_f, kept_m = retain_columns(i, old_data, fn)
        offset = len(vertices)
        vertices.extend(kept_v)
        faces.extend(tuple(offset+k for k in p) for p in kept_f)
        indices = [0]*terrain_faces+[mats.index(old_data.materials[k]) if old_data.materials[k] in mats else 2 for k in kept_m]
        target = [vertices, faces, indices]
        forms = [
            [(-67, -46, 21, 34, 14)],
            [(-70, -55, 25, 27, 25), (-72, 34, 26, 42, 39), (65, 67, 26, 22, 24)],
            [(64, 63, 30, 25, 24), (-57, -66, 39, 19, 19), (76, -54, 21, 29, 11)],
            [(72, 69, 27, 22, 31), (81, -66, 20, 22, 18)],
            [(-52, 47, 29, 25, 29), (18, 62, 39, 23, 25), (69, 38, 20, 29, 34)]
        ][i]
        for j, (x, y, sx, sy, z) in enumerate(forms):
            append_formation(target, formation('cooled_shelf', x, y, sx, sy, z, fn, group.children[0], COOLED))
        data = bpy.data.meshes.new(name+'_authored_surface')
        data.from_pydata(target[0], [], target[1])
        for m in mats:
            data.materials.append(m)
        data.update()
        for p, k in zip(data.polygons, target[2]):
            p.material_index = k
        ground_materials(data, terrain_faces)
        ob.data = data
        ob.location = (0, 0, 0)
        ob['Openings'] = ','.join(OPENINGS[i])
        ob['SeamBand'] = BAND
        ob['SeamProfile'] = 'LOW_ROLL_4; mouth FLAT_ASH_56'
        ob['EntryElevationLocal'] = -28 if i == 1 else 0
        ob['ExitElevationLocal'] = 28 if i == 1 else 0
        ob['ElevationDelta'] = STEP if i == 1 else 0
        ob['HasOutgoingSocket'] = i < 3
        ob['ContinuationLevel'] = 'LEVEL_0' if i == 0 else 'LEVEL_1'
        ob['EdgeProfiles'] = json.dumps({s: {'profile': 'RAMP_56_LOW_ROLL_4' if i == 1 and s in ('E', 'W') else 'LOW_ROLL_4', 'mouth': fn(0, 128 if s == 'N' else -128) if s in ('N', 'S') else fn(128 if s == 'E' else -128, 0)} for s in ('N', 'E', 'S', 'W')})
        ob['Design'] = descriptions[i]
        ob['TerrainFaceCount'] = terrain_faces
        root['ReviewOnlyTransform'] = True
        reseat_saved_props(i, group, fn)
        # Refit retained heat ribbons into the new geological recesses.
        for heat in [o for o in group.all_objects if o.type == 'MESH' and ('prop_low_fissure' in o.name or 'prop_basin_heat' in o.name)]:
            for v in heat.data.vertices:
                if i == 1:
                    v.co.x += 38
                v.co.z = fn(v.co.x, v.co.y)+.12
            heat.data.update()
        # Reposition saved flora intentionally to cooler crests and hot recesses.
        plants = [o for o in group.all_objects if o.get('LibraryAsset')]
        if i == 1:
            for plant, (x, y) in zip(plants, [(69, -46), (76, 0), (-35, 66)]):
                plant.location = (x, y, fn(x, y)+.03)
        if i == 2:
            for plant, (x, y) in zip(plants, [(-66, 10), (-70, 34), (48, 46), (63, 39)]):
                plant.location = (x, y, fn(x, y)+.03)
        assets.append(group)
    return assets


def flora(name, x, y, fn, collection, species, scale=1):
    source = PLANTS[species]
    ob = bpy.data.objects.new(name, source.data)
    collection.objects.link(ob)
    ob.location = (x, y, fn(x, y)+.03)
    ob.scale = (scale, scale, scale)
    ob.rotation_euler.z = x*.13+y*.07
    ob['LibraryAsset'] = source.name
    ob['solid'] = False
    return ob


def make_scenery():
    parent = coll('EF_LOCAL_SCENERY_8_ASSETS')
    assets = []
    for family, name in enumerate(SCENERY):
        group = coll(name, parent)
        st = coll(name+'_Structure', group)
        non = coll(name+'_Props_NonSolid', group)
        fn = lambda x, y, f=family: scenery_height(f, x, y)
        vertices, faces, _ = terrain_data(fn, 16)
        ob = mesh(name, vertices, faces, st, [COOLED, ASH, BASALT])
        ground_materials(ob.data, len(faces))
        ob['Playable'] = False
        ob['SceneryFamily'] = name.removeprefix('scenery_').removesuffix('_a')
        ob['SeamBand'] = BAND
        ob['SeamProfile'] = 'LOW_ROLL_4; mouth FLAT_ASH_56'
        ob['SceneryCollision'] = 'unreachable interior only; reachable margin needs collision in Studio'
        ob['ElevationSupport'] = 'datum 0 or 56; reviewed fitting for transition borders'
        ob['TerrainFaceCount'] = len(faces)
        if family in (1, 2, 7):
            for j, (x, y, sx, sy, h) in enumerate([(24, 16, 27, 62, 38), (-45, 64, 24, 28, 26)]):
                formation('scenery_fractured_ridge', x, y, sx, sy, h*(1.6 if family == 2 else 1), fn, st, BASALT)
        if family == 3:
            # Winding broad molten lowland: not a passable glowing alternate route.
            old.ribbon('scenery_molten_lowland', [(x, y, fn(x, y)+.18) for x, y in [(-48, -53), (-29, -25), (8, 1), (38, 27), (51, 56)]], 19, non, None, MOLTEN)
            formation('cooled_lava_islet', -39, 38, 19, 24, 13, fn, st, COOLED)
        if family == 4:
            old.ribbon('scenery_ravine_deep_heat', [(0, y, fn(0, y)+.16) for y in [-72, -36, 0, 34, 70]], 5, non, None, EMBER)
        if family in (5, 6):
            for j, (x, y) in enumerate([(-42, 32), (27, -44)]):
                flora('scenery_flora_pocket', x, y, fn, non, (j % 2)+(0 if family == 5 else 2), 1+(j % 3)*.2)
        # All scenery components stay well inside its own tile, except shared terrain.
        assets.append(group)
    return parent, assets


def count_collection(group):
    objects = list(group.all_objects)
    triangles = {}
    for ob in objects:
        if ob.type == 'MESH':
            ob.data.calc_loop_triangles()
            triangles[ob.name] = len(ob.data.loop_triangles)
    return {'objects': len(objects), 'mesh_objects': len(triangles),
            'triangles': sum(triangles.values()), 'mesh_triangles': triangles,
            'collections': {c.name: [o.name for o in c.objects] for c in group.children}}


def bounds(ob):
    pts = [v.co for v in ob.data.vertices]
    low = [min(p[a] for p in pts) for a in range(3)]
    high = [max(p[a] for p in pts) for a in range(3)]
    return low, high


def inspect_assets(playable, scenery):
    REPORT['playable'] = []
    REPORT['scenery'] = []
    for i, group in enumerate(playable):
        ob = bpy.data.objects[NAMES[i]]
        low, high = bounds(ob)
        assert low[0:2] == [-128, -128] and high[0:2] == [128, 128]
        assert tuple(ob.location) == (0, 0, 0)
        assert abs(playable_height(i, 0, 0)) < 1e-6
        tree = BVHTree.FromPolygons([v.co for v in ob.data.vertices], [p.vertices for p in ob.data.polygons])
        probes = []
        for side in OPENINGS[i]:
            heights = []
            for across in (-28, -14, 0, 14, 28):
                for inset in (.01, 8, 16, 24):
                    along = 128-inset
                    x, y = (across, along if side == 'N' else -along) if side in ('N', 'S') else (along if side == 'E' else -along, across)
                    hit = tree.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)))[0]
                    assert hit is not None, (i, side, x, y)
                    expected = playable_height(i, x, y)
                    assert abs(hit.z-expected) < .001, (i, side, hit.z, expected)
                    heights.append(hit.z)
            assert max(heights)-min(heights) < .001
            probes.append({'side': side, 'samples': len(heights), 'width': 56, 'buffer': 24, 'local_height': round(heights[0], 5)})
        row = count_collection(group)
        row.update({'name': NAMES[i], 'role': ROLES[i], 'dimensions_xyz': [high[a]-low[a] for a in range(3)],
                    'bounds_local': [low, high], 'origin': list(ob.location), 'entry_local': ob['EntryElevationLocal'],
                    'exit_local': ob['ExitElevationLocal'] if ob['HasOutgoingSocket'] else None, 'world_datum': POSITIONS[i][2],
                    'entry_world': POSITIONS[i][2]+ob['EntryElevationLocal'], 'exit_world': POSITIONS[i][2]+ob['ExitElevationLocal'] if ob['HasOutgoingSocket'] else None,
                    'delta': ob['ElevationDelta'], 'continuation': ob['ContinuationLevel'], 'mouth_probes': probes,
                    'edge_profiles': json.loads(ob['EdgeProfiles']), 'design': ob['Design']})
        REPORT['playable'].append(row)
    for i, group in enumerate(scenery):
        ob = next(o for o in group.all_objects if o.name == SCENERY[i])
        row = count_collection(group)
        low, high = bounds(ob)
        row.update({'name': SCENERY[i], 'origin': list(ob.location), 'terrain_dimensions': [high[a]-low[a] for a in range(3)],
                    'role': None, 'sockets': [], 'enemy_spawns': [], 'bounds_local': [low, high]})
        REPORT['scenery'].append(row)


def save_independent(group, name):
    # Save a collection library, then append it into a clean ordinary scene.
    path = OUT/(name+'.blend')
    bpy.data.libraries.write(str(path), {group}, fake_user=True)
    return path


def clone_group(source, parent, position, name, fitted=False, turn=0):
    group = coll(name, parent)
    root = bpy.data.objects.new(name+'_placement', None)
    group.objects.link(root)
    root.location = position
    root['ReviewOnly'] = True
    root['AssetCollection'] = source.name
    root['AuthoredQuarterTurn'] = turn
    for ob in source.all_objects:
        if ob.type == 'EMPTY':
            continue
        copy = ob.copy()
        group.objects.link(copy)
        copy.parent = root
        copy.matrix_parent_inverse.identity()
        if fitted:
            angle = math.radians(turn)
            cs, sn = math.cos(angle), math.sin(angle)
            lx, ly = copy.location.x, copy.location.y
            copy.location.x, copy.location.y = cs*lx-sn*ly, sn*lx+cs*ly
            # Offline compatibility study: no random deformation. Apply the same
            # controlled route-level field to all surfaces/props at this cell.
            if copy.type == 'MESH' and not copy.get('LibraryAsset'):
                copy.data = ob.data.copy()
                for v in copy.data.vertices:
                    vx, vy = v.co.x, v.co.y
                    v.co.x, v.co.y = cs*vx-sn*vy, sn*vx+cs*vy
                    world_y = position[1]+copy.location.y+v.co.y
                    v.co.z += level(world_y)-position[2]
                copy.data.update()
            else:
                copy.rotation_euler.z += angle
                copy.location.z += level(position[1]+copy.location.y)-position[2]
        copy['ReviewOnly'] = fitted
    return group


def surface_edge(group, position, side):
    # Read actual persisted vertices, not the height function.
    ob = next(o for o in group.all_objects if o.type == 'MESH' and o.get('TerrainFaceCount'))
    limit = 128 if side in ('N', 'E') else -128
    axis = 1 if side in ('N', 'S') else 0
    across = 1-axis
    return {round(v.co[across]+position[across], 4): v.co.z+position[2]
            for v in ob.data.vertices if abs(v.co[axis]-limit) < 1e-5}


def check_arrangement(cells):
    rows = []
    for cell, (group, pos, family) in cells.items():
        for direction, step, opposite in [('N', (0, 1), 'S'), ('E', (1, 0), 'W')]:
            other_cell = (cell[0]+step[0], cell[1]+step[1])
            if other_cell not in cells:
                continue
            other, other_pos, other_family = cells[other_cell]
            a = surface_edge(group, pos, direction)
            b = surface_edge(other, other_pos, opposite)
            keys = sorted(set(a) | set(b))
            def at(profile, key):
                if key in profile:
                    return profile[key]
                stations = sorted(profile)
                low = max(k for k in stations if k < key)
                high = min(k for k in stations if k > key)
                return profile[low]+(profile[high]-profile[low])*(key-low)/(high-low)
            error = max(abs(at(a, k)-at(b, k)) for k in keys)
            assert len(keys) >= 19 and error < .0001, (cell, other_cell, error)
            rows.append({'a': group.name, 'b': other.name, 'samples': len(keys), 'max_gap': error,
                         'type': 'playable-playable' if family == other_family == 'PLAYABLE' else 'playable-scenery' if 'PLAYABLE' in (family, other_family) else 'scenery-scenery'})
    return rows


def horizon_extensions(cells, collection):
    # Cheap independent distant pieces extend the second ring into a broken
    # mountain skyline. Never a fixed backdrop plate or playable geometry.
    for (cx, cy), (group, pos, _) in cells.items():
        sides = []
        if cx == -2:
            sides.append('W')
        if cx == 3:
            sides.append('E')
        if cy == -3:
            sides.append('S')
        if cy == 4:
            sides.append('N')
        for side in sides:
            edge = surface_edge(group, pos, side)
            keys = sorted(edge)
            vertices = []
            for ring, t in enumerate((0, .25, .62, 1)):
                for along in keys:
                    start = pos[1]+(128 if side == 'N' else -128) if side in ('N', 'S') else pos[0]+(128 if side == 'E' else -128)
                    outward = 650*t
                    across = along*(1+t*.42)
                    z = edge[along]+t*(38+90*(.5+.5*math.sin(along*.009+len(side))))
                    if side in ('N', 'S'):
                        vertices.append((across, start+(outward if side == 'N' else -outward), z))
                    else:
                        vertices.append((start+(outward if side == 'E' else -outward), across, z))
            n = len(keys)
            faces = [(j*n+k, j*n+k+1, (j+1)*n+k+1, (j+1)*n+k) for j in range(3) for k in range(n-1)]
            ob = mesh(f'horizon_{cx}_{cy}_{side}_REVIEW_ONLY', vertices, faces, collection, [COOLED])
            for p in ob.data.polygons:
                p.use_smooth = True
            ob['ReviewOnly'] = True


def atmosphere(collection):
    # Finite review-only haze softens the outer terrain limit in player views.
    material = bpy.data.materials.new('review_cool_haze')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    volume = nodes.new('ShaderNodeVolumePrincipled')
    volume.inputs['Color'].default_value = (.48, .57, .65, 1)
    volume.inputs['Density'].default_value = .00022
    material.node_tree.links.new(volume.outputs['Volume'], output.inputs['Volume'])
    vertices = [(x, y, z) for z in (-700, 1600) for y in (-2400, 2800) for x in (-2400, 2800)]
    ob = mesh('Atmosphere_REVIEW_ONLY', vertices,
              [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], collection, [material])
    ob.display_type = 'WIRE'
    ob['ReviewOnly'] = True


def camera(name, location, target, collection, lens=30, ortho=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_end = 12000
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob


def build_arrangement(letter, seed, playable, scenery):
    scene = bpy.data.scenes.new('Architecture_'+letter)
    bpy.context.window.scene = scene
    root = coll('ReviewLayout_'+letter+'_ONLY')
    scene['README'] = 'Review-only fitted arrangement; no exports. Eight independently saved scenery assets reused with controlled elevation compatibility. Not runtime generation.'
    playable_parent = coll('Playable_5', root)
    ring = coll('Scenery_instances_REVIEW_ONLY', root)
    far = coll('Distant_ring_REVIEW_ONLY', root)
    lights = coll('Cameras_Lights_REVIEW_ONLY', root)
    cells = {}
    for i, position in enumerate(POSITIONS):
        cell = (position[0]//256, position[1]//256)
        group = clone_group(playable[i], playable_parent, position, NAMES[i]+'_placed')
        cells[cell] = (group, position, 'PLAYABLE')
    rng = random.Random(seed)
    selections = []
    for y in range(-3, 5):
        for x in range(-2, 4):
            if (x, y) in cells:
                continue
            local = -1 <= x <= 2 and -2 <= y <= 3
            # Lava/ravine outlook remains contextual while still changing every run.
            family = rng.choice([3, 4, 0]) if (x, y) == (2, 1) else rng.randrange(8)
            if (x, y) == (-1, 1):
                family = [2, 7, 1][ord(letter)-65]
            if (x, y) == (1, 2):
                family = [7, 2, 5][ord(letter)-65]
            pos = (x*256, y*256, level(y*256))
            group = clone_group(scenery[family], ring if local else far, pos,
                                f'{SCENERY[family]}_cell_{x}_{y}', fitted=True, turn=rng.choice([0, 90, 180, 270]))
            cells[x, y] = (group, pos, SCENERY[family])
            selections.append({'cell': [x, y], 'asset': SCENERY[family], 'datum': pos[2], 'ring': 'local' if local else 'distant',
                               'controlled_transition_fit': y == 0})
    bpy.context.view_layer.update()
    seams = check_arrangement(cells)
    horizon_extensions(cells, far)
    atmosphere(lights)
    REPORT.setdefault('arrangements', {})[letter] = {'seed': seed, 'cells': selections, 'seams': seams,
        'counts': count_collection(root), 'local_instances': sum(s['ring'] == 'local' for s in selections),
        'distant_instances': sum(s['ring'] == 'distant' for s in selections)}
    sun_data = bpy.data.lights.new('overcast_sun', 'SUN')
    sun_data.energy = 2.4
    sun_data.angle = .5
    sun = bpy.data.objects.new('overcast_sun', sun_data)
    lights.objects.link(sun)
    sun.rotation_euler = (.45, -.5, -.35)
    scene.world = bpy.data.worlds.new('Emberfall_CoolAtmosphere_'+letter)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .29, .36, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    shots = [('overview_'+letter, (1060, -1160, 850), (70, 170, 20), 40, None)]
    if letter == 'A':
        shots += [
            ('top_seams', (100, 150, 1800), (100, 150, 0), 40, 1320),
            ('side_vertical', (840, 150, 82), (0, 150, 32), 42, None),
            ('eye_baseline_ascent', (0, -142, 4.5), (0, 90, 62), 26, None),
            ('eye_ascent_upper_join', (0, 104, 60.5), (0, 260, 60), 27, None),
            ('eye_raised_cap_join', (0, 360, 60.5), (0, 500, 63), 27, None),
            ('eye_side_join', (103, 256, 60.5), (290, 256, 72), 28, None),
            ('eye_low_scenery_join', (-110, -240, 7), (-270, -240, 8), 29, None),
            ('eye_high_scenery_join', (-126, 220, 60.5), (-132, 340, 60), 29, None),
            ('elevated_lookback', (5, 232, 64), (-5, -280, 5), 23, None),
            ('overlook_lava_lowlands', (346, 275, 93), (518, 264, 23), 25, None),
            ('entry_identity', (100, -361, 44), (-10, -246, 6), 28, None),
            ('combat_identity', (113, 143, 106), (-12, 289, 63), 28, None),
            ('cap_identity', (10, 414, 70), (0, 552, 75), 26, None)]
    cams = [camera(n, loc, target, lights, lens, ortho) for n, loc, target, lens, ortho in shots]
    scene.camera = cams[0]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_distance = 1450
                space.region_3d.view_location = (70, 160, 45)
                space.clip_end = 12000
                space.shading.color_type = 'MATERIAL'
    return scene, cams


def main():
    global old, COOLED, ASH, BASALT, MOLTEN, EMBER, PLANTS, GROUND
    OUT.mkdir(parents=True, exist_ok=True)
    input_path = OUT/'Input_FirstPass.blend'
    if not input_path.exists():
        shutil.copy2(SOURCE, input_path)
    bpy.ops.wm.open_mainfile(filepath=str(input_path))
    spec = importlib.util.spec_from_file_location('emberfall_first_pass_helpers', HERE/'build_emberfall_prototype.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    COOLED, ASH, BASALT, MOLTEN, EMBER = [bpy.data.materials[n] for n in ['Ember_CooledLava', 'Ember_Ash', 'Ember_Basalt', 'Ember_Molten', 'Ember_DeepHeat']]
    GROUND = COOLED.copy()
    GROUND.name = 'Ember_WeatheredGround'
    tint = GROUND.node_tree.nodes.new('ShaderNodeVertexColor')
    tint.layer_name = 'EmberGroundTint'
    GROUND.node_tree.links.new(tint.outputs['Color'], GROUND.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    PLANTS = [bpy.data.objects[n] for n in ['prop_drained_wax_rosette', 'prop_drained_seed_shrub', 'prop_charred_ember_rose', 'prop_charred_thorn_pod']]
    plant_hashes = {p.name: fingerprint(p.data) for p in PLANTS}
    for name in ['Surround_REVIEW_ONLY', 'Cameras_Lights_REVIEW_ONLY']:
        c = bpy.data.collections.get(name)
        if c:
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    playable = rebuild_playable()
    scenery_parent, scenery = make_scenery()
    inspect_assets(playable, scenery)
    REPORT['flora_hashes_before'] = plant_hashes
    REPORT['flora_hashes_after'] = {p.name: fingerprint(p.data) for p in PLANTS}
    assert REPORT['flora_hashes_before'] == REPORT['flora_hashes_after']
    REPORT['blender_version'] = bpy.app.version_string
    libraries = [(g, n) for g, n in zip(playable+scenery, NAMES+SCENERY)]
    for group, name in libraries:
        save_independent(group, name)
    scenes = [build_arrangement(letter, seed, playable, scenery) for letter, seed in [('A', 421), ('B', 824), ('C', 1207)]]
    # The initial source scene is an asset-library scene, distinct from layouts.
    initial = bpy.data.scenes.get('Scene') or next(s for s in bpy.data.scenes if s not in [x[0] for x in scenes])
    initial.name = 'Independent_Assets_LIBRARY_ONLY'
    initial['README'] = 'Five original playable objects edited in place plus eight local scenery assets, all at local origin. ReviewLayout collections in other scenes are disposable.'
    bpy.context.window.scene = scenes[0][0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    (OUT/'technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    for scene, cams in scenes:
        bpy.context.window.scene = scene
        if '--no-render' not in sys.argv:
            for cam in cams:
                scene.camera = cam
                scene.render.filepath = str(OUT/(cam.name+'.png'))
                bpy.ops.render.render(write_still=True)
        scene.camera = cams[0]
    bpy.context.window.scene = scenes[0][0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    print('ARCHITECTURE_STUDY_COMPLETE', [(r['name'], r['triangles']) for r in REPORT['playable']+REPORT['scenery']])


if __name__ == '__main__':
    main()
