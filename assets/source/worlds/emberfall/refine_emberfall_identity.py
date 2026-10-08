"""Edit saved Emberfall architecture in place: crust, active failure and takeover.

Protected Blender launcher only. Keeps route transforms, seam-band geometry,
original flora library, the five/eight asset inventory and the current lighting.
"""
import bpy
import importlib.util
import json
import math
import shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
INPUT = OUT/'Input_ArtDirection.blend'
MAIN = OUT/'EmberfallPrototype.blend'
RENDERS = OUT/'IdentityReview'
REPORT = {}


def module(filename, name):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest_scene(scene):
    meshes = [o for o in scene.objects if o.type == 'MESH']
    triangles = 0
    for ob in meshes:
        ob.data.calc_loop_triangles()
        triangles += len(ob.data.loop_triangles)
    return {'objects': len(scene.objects), 'meshes': len(meshes), 'triangles': triangles,
            'used_materials': len({m.name for ob in meshes for m in ob.data.materials if m})}


def make_material(name, color, roughness=.85, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Emission Color'].default_value = (*color, 1)
    node.inputs['Emission Strength'].default_value = glow
    return mat


def root(group):
    return next((o for o in group.objects if o.type == 'EMPTY'), None)


def surface_tree(ob):
    return BVHTree.FromPolygons([v.co for v in ob.data.vertices],
        [p.vertices for p in ob.data.polygons[:ob['TerrainFaceCount']]])


def floor(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)))[0]
    assert hit is not None, (x, y)
    return hit.z


def triangle_budget(group):
    counts = {}
    for ob in group.all_objects:
        if ob.type == 'MESH':
            ob.data.calc_loop_triangles()
            counts[ob.name] = len(ob.data.loop_triangles)
    return {'objects': len(group.all_objects), 'triangles': sum(counts.values()), 'mesh_triangles': counts}


def plates(group, stage, family, terrain):
    tree = surface_tree(terrain)
    details = study.coll(group.name+'_SurfaceIdentity', group)
    vertices, faces, materials = [], [], []
    centers = [(-65, -52), (-65, -15), (-57, 30), (-66, 66),
               (61, -61), (57, -23), (62, 23), (53, 63)]
    if family == 'ENTRY':
        centers = centers[:3]+centers[5:7]
    if family in ('CAP', 'COMBAT'):
        centers += [(-27, 54), (10, 67), (31, 48), (3, -66)]
    if family in ('ENTRY', 'PATH', 'COMBAT', 'CAP'):
        centers += [(-5, -70), (6, 62), (-11, 30)]
    if family == 'LAVA_FIELD':
        centers = [(-62, -56), (-44, 47), (52, -49), (66, 25), (-67, 6)]
    scale = .76 if family == 'ENTRY' else 1
    for j, (cx, cy) in enumerate(centers):
        sx, sy = (16+j % 3*3)*scale, (13+j % 2*5)*scale
        angle = (j*.73+stage*.29)
        # Six unequal polygon corners, tilted independently along a fresh tear.
        outline = [(-1, -.6), (-.42, -1), (.8, -.88), (1, .3), (.31, 1), (-.89, .77)]
        start = len(vertices)
        xy = [(cx+sx*(x*math.cos(angle)-y*math.sin(angle)),
               cy+sy*(x*math.sin(angle)+y*math.cos(angle))) for x, y in outline]
        assert all(max(abs(x), abs(y)) < 102 for x, y in xy)
        lift = (.25+stage*.15) if abs(cx) < 23 else (.38 if stage == 0 else 1.1+stage*.35)
        for ring in range(3):
            for k, (x, y) in enumerate(xy):
                factor = 1 if ring < 2 else .95
                px, py = cx+(x-cx)*factor, cy+(y-cy)*factor
                z = floor(tree, px, py)-.6 if ring == 0 else floor(tree, px, py)+lift*(.5+.5*(k/5))
                if ring == 2:
                    z += .15
                vertices.append((px, py, z))
        for ring in range(2):
            for k in range(6):
                faces.append(tuple(start+q for q in (ring*6+k, ring*6+(k+1) % 6, (ring+1)*6+(k+1) % 6, (ring+1)*6+k)))
                materials.append(3 if stage > 0 and ring == 0 and k in (1, 2) else 1)
        faces.append(tuple(start+12+k for k in range(6)))
        materials.append(2 if family == 'SIDE' and j in (3, 5) else 0)
        # A second displaced wedge gives a legible fracture, not a painted line.
        if stage > 0 and j % 2 == 0:
            start = len(vertices)
            a, b = xy[1], xy[2]
            x1, y1 = a[0]*.88+cx*.12, a[1]*.88+cy*.12
            x2, y2 = b[0]*.88+cx*.12, b[1]*.88+cy*.12
            vertices += [(x1, y1, floor(tree, x1, y1)+.5), (x2, y2, floor(tree, x2, y2)+.5),
                         (cx+3, cy-4, floor(tree, cx+3, cy-4)+lift+2), (cx-3, cy-2, floor(tree, cx-3, cy-2)+lift+2)]
            faces.append((start, start+1, start+2, start+3))
            materials.append(1)
    ob = study.mesh('prop_'+group.name+'_fractured_crust', vertices, faces, details, [CRUST, SCORCH, GLASS, FRESH])
    ob.parent = root(group)
    ob['solid'] = True
    ob['IdentityLayer'] = 'fractured crust with ash/strata; no seam cover'
    for p, index in zip(ob.data.polygons, materials):
        p.material_index = index
    # Ash accumulated on the windward side of old crust, displaced by fresher breaks.
    if stage == 0:
        ashverts, ashfaces = [], []
        for j, (cx, cy) in enumerate([(-54, -37), (68, 39), (-42, 52)]):
            start = len(ashverts)
            for x, y in [(cx-15, cy-4), (cx+17, cy-6), (cx+10, cy+11), (cx-12, cy+9), (cx-2, cy+2)]:
                ashverts.append((x, y, floor(tree, x, y)+(.95 if x == cx-2 else .12)))
            ashfaces += [(start+k, start+(k+1) % 4, start+4) for k in range(4)]
        ash = study.mesh('prop_'+group.name+'_windward_ash', ashverts, ashfaces, details, [DUST])
        ash.parent = root(group)
        for p in ash.data.polygons:
            p.use_smooth = True
    REPORT.setdefault('surfaces', {})[group.name] = {'stage': stage, 'dominant': family, 'plates': len(centers)}
    return details


def vent_smoke(group, terrain, stage):
    collection = study.coll(group.name+'_VentSmoke', group)
    mat = bpy.data.materials.get('Ember_VentingAsh_REVIEW_ONLY')
    if not mat:
        mat = bpy.data.materials.new('Ember_VentingAsh_REVIEW_ONLY')
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial')
        volume = nodes.new('ShaderNodeVolumePrincipled')
        volume.inputs['Color'].default_value = (.18, .15, .125, 1)
        volume.inputs['Density'].default_value = .022
        mat.node_tree.links.new(volume.outputs['Volume'], output.inputs['Volume'])
    tree = surface_tree(terrain)
    x, y = (72, -25) if stage == 1 else (24, 58)
    z = floor(tree, x, y)
    old.rock('prop_recent_fracture_vent_smoke', x, y, z+14, 5, 7, 19 if stage == 1 else 27, collection, root(group), mat)
    for ob in collection.objects:
        ob['ReviewOnlyVolume'] = True
        ob['solid'] = False
    return collection


def geology_in_place(ob, stage):
    data = ob.data
    # Existing disconnected columns and round mass components remain, but selected
    # vertical components become buried, leaning remnants inside the existing land.
    reduced = 0
    for comp in study.components(data):
        if len(comp) > 180:
            continue
        pts = [data.vertices[k].co for k in comp]
        low, high = min(p.z for p in pts), max(p.z for p in pts)
        if high-low < 18:
            continue
        x = sum(p.x for p in pts)/len(pts)
        y = sum(p.y for p in pts)/len(pts)
        if max(abs(x), abs(y)) > 96:
            continue
        # Retain two stronger column silhouettes in the ascent; bury the others.
        if ob.name == study.NAMES[1] and x < -45 and y > 25:
            continue
        for k in comp:
            p = data.vertices[k].co
            t = (p.z-low)/(high-low)
            p.z = low-2+(p.z-low)*.57
            p.x += t*4.5*math.sin(y*.04)
        reduced += 1
    data.update()
    return reduced


def tint_ground(ob, stage, turn=0):
    data = ob.data
    attr = data.color_attributes.get('EmberGroundTint')
    if not attr:
        return
    for p in data.polygons[:ob['TerrainFaceCount']]:
        for li in p.loop_indices:
            x, y, z = data.vertices[data.loops[li].vertex_index].co
            inside = study.interior(x, y)
            edge = (.027, .034, .039)
            if stage == 0:
                ash = math.exp(-((x+18)/73)**2-((y-12)/82)**2)
                center = tuple(a+(b-a)*ash for a, b in zip((.047, .031, .019), (.19, .155, .095)))
            elif stage == 1:
                scorched = .5+.5*math.sin((x+y*.35)*.027)
                center = tuple(a+(b-a)*scorched for a, b in zip((.018, .025, .028), (.071, .038, .018)))
            else:
                ash = math.exp(-((x+60)/35)**2-((y-63)/42)**2)
                center = tuple(a+(b-a)*ash for a, b in zip((.012, .016, .023), (.085, .058, .024)))
            attr.data[li].color = (*(edge[k]+(center[k]-edge[k])*inside for k in range(3)), 1)


def variant(source, name, fraction, collection, old_state=False):
    ob = bpy.data.objects.new(name, source.data.copy())
    collection.objects.link(ob)
    ob.hide_render = True
    ob.hide_set(True)
    original = len(ob.data.materials)
    ob.data.materials.append(OLD if old_state else bpy.data.materials['Ember_DrainedFlora'])
    ob.data.materials.append(INFECTED)
    ob.data.materials.append(SCORCH)
    # One-sided conversion is deliberately readable as a half-taken-over plant.
    order = sorted(ob.data.polygons, key=lambda p: p.center.x)
    infected = set(p.index for p in order[:round(len(order)*fraction)])
    for p in ob.data.polygons:
        p.material_index = original+1 if p.index in infected else original
    ob['DerivedFrom'] = source.name
    ob['InfectedSurfaceFraction'] = fraction
    ob['FloraState'] = 'OLD_STRESSED' if old_state else f'PARTIAL_{int(fraction*100)}' if fraction else 'DRAINED'
    return ob


def invasive(collection):
    temporary = study.coll('Invasive_growth_parts', collection)
    for j in range(5):
        a = j*2.399
        end = (math.cos(a)*2.8, math.sin(a)*2.8, .5+j % 2)
        old.stem_curve('invasive_root', [(0, 0, .05), (end[0]*.35, end[1]*.35, .8), end], .14, temporary, None, INFECTED)
        old.stem_curve('invasive_thorn', [(end[0]*.55, end[1]*.55, .7), (end[0]*.4, end[1]*.4, 2+j*.25)], .10, temporary, None, INFECTED)
    source = bpy.data.objects['prop_charred_thorn_pod']
    pod = source.copy()
    pod.data = source.data.copy()
    pod.hide_render = False
    temporary.objects.link(pod)
    pod.hide_set(False)
    pod.location.z = .4
    ob = old.join_objects(temporary, 'prop_invasive_root_bloom', None)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    collection.objects.link(ob)
    bpy.data.collections.remove(temporary)
    ob['DerivedFrom'] = source.name
    ob['FloraState'] = 'INVASIVE'
    ob.hide_render = True
    ob.hide_set(True)
    return ob


def add_flora(group, terrain, sources, states, coords):
    tree = surface_tree(terrain)
    ambient = next(c for c in group.children if c.name.endswith('Props_NonSolid'))
    added = []
    for j, (state, (x, y, scale)) in enumerate(zip(states, coords)):
        source = sources[state]
        ob = bpy.data.objects.new('prop_'+group.name+'_takeover_'+state, source.data)
        ambient.objects.link(ob)
        ob.parent = root(group)
        ob.location = (x, y, floor(tree, x, y)+.03)
        ob.rotation_euler.z = j*.47
        ob.scale = (scale, scale, scale)
        ob['LibraryAsset'] = source.name
        ob['FloraState'] = state
        ob['solid'] = False
        added.append(ob)
        if state in ('30', '50', '70', 'SHRUB50'):
            # Three visible dark veins climb and wrap the pale side of the plant.
            for k in range(3):
                a = 1.8+k*.45
                vein = old.stem_curve('prop_infection_climbing_vein', [(x+.4*math.cos(a), y+.4*math.sin(a), ob.location.z-.1),
                    (x+scale*1.1*math.cos(a), y+scale*1.1*math.sin(a), ob.location.z+scale*.75),
                    (x+scale*2*math.cos(a+.3), y+scale*2*math.sin(a+.3), ob.location.z+scale*1.7)], .08*scale, ambient, root(group), INFECTED)
                vein['solid'] = False
                added.append(vein)
    return added


def propagate(source, addition):
    # Extend the EXISTING placed collections; preserve their parents/transforms.
    for scene in [bpy.data.scenes['Architecture_'+letter] for letter in 'ABC']:
        for parent in scene.collection.children[0].children:
            for group in parent.children:
                placement = root(group)
                if not placement or placement.get('AssetCollection') != source.name:
                    continue
                target = study.coll(addition.name+'_placed', group)
                turn = placement.get('AuthoredQuarterTurn', 0)
                angle = math.radians(turn)
                cs, sn = math.cos(angle), math.sin(angle)
                fitted = source.name in study.SCENERY
                for ob in addition.all_objects:
                    copy = ob.copy()
                    target.objects.link(copy)
                    copy.parent = placement
                    copy.matrix_parent_inverse.identity()
                    if fitted:
                        x, y = copy.location.x, copy.location.y
                        copy.location.x, copy.location.y = cs*x-sn*y, sn*x+cs*y
                        if not copy.get('LibraryAsset'):
                            copy.data = ob.data.copy()
                            for v in copy.data.vertices:
                                x, y = v.co.x, v.co.y
                                v.co.x, v.co.y = cs*x-sn*y, sn*x+cs*y
                                v.co.z += study.level(placement.location.y+v.co.y)-placement.location.z
                        else:
                            copy.rotation_euler.z += angle
                            copy.location.z += study.level(placement.location.y+copy.location.y)-placement.location.z


def render_views():
    scene = bpy.data.scenes['Architecture_A']
    bpy.context.window.scene = scene
    cameras = next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
    scene.cycles.samples = 32
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    views = [('outer_player', (4, -327, 4.5), (-30, -242, 4), 27),
             ('mid_player', (7, -77, study.level(-77)+4.5), (-5, 51, study.level(51)+5), 28),
             ('inner_player', (5, 426, 61), (-21, 550, 74), 28),
             ('elevated_overview', (720, -830, 690), (50, 148, 33), 42),
             ('close_terrain', (-33, 258, 69), (-54, 293, 57), 42),
             ('raised_collapse', (99, 174, 81), (-54, 298, 51), 31),
             ('flora_half_takeover', (-23, 52, study.level(52)+8), (-34, 66, study.level(66)+2), 50),
             ('flora_progression', (12, -349, 9), (-22, -273, 3), 46)]
    bpy.context.view_layer.update()
    for name, prefix, offset in [('flora_half_takeover', 'prop_path_column_pass_takeover_50', (7, -10, 7)),
                                 ('flora_progression', 'prop_chunk_entry_ash_plain_takeover_OLD', (9, -12, 9))]:
        plant = next(o for o in scene.objects if o.name.startswith(prefix))
        target = plant.matrix_world.translation+Vector((0, 0, 1.7))
        views = [(n, tuple(target+Vector(offset)), tuple(target), 48) if n == name else (n, loc, aim, lens)
                 for n, loc, aim, lens in views]
    cams = [study.camera('identity_'+name, loc, target, cameras, lens) for name, loc, target, lens in views]
    for cam in cams:
        scene.camera = cam
        scene.render.filepath = str(RENDERS/(cam.name+'.png'))
        bpy.ops.render.render(write_still=True)
    # Matched no-heat diagnostic, not a claim that orange makes the identity.
    stored = []
    for mat in bpy.data.materials:
        if mat.name in ('Ember_Molten', 'Ember_DeepHeat', 'Ember_FreshBreakHeat'):
            node = mat.node_tree.nodes.get('Principled BSDF')
            stored.append((node, tuple(node.inputs['Base Color'].default_value), node.inputs['Emission Strength'].default_value))
            node.inputs['Base Color'].default_value = (.016, .02, .023, 1)
            node.inputs['Emission Strength'].default_value = 0
    light_values = [(o.data, o.data.energy) for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'POINT']
    for data, value in light_values:
        data.energy = 0
    for cam in (cams[3], cams[1], cams[6]):
        scene.camera = cam
        scene.render.filepath = str(RENDERS/(cam.name+'_heat_dark.png'))
        bpy.ops.render.render(write_still=True)
    for node, color, strength in stored:
        node.inputs['Base Color'].default_value = color
        node.inputs['Emission Strength'].default_value = strength
    for data, value in light_values:
        data.energy = value
    scene.camera = cams[3]


def flora_gallery(sources):
    gallery = bpy.data.scenes.new('FloraSpectrum_REVIEW_ONLY')
    bpy.context.window.scene = gallery
    group = study.coll('FloraSpectrum_REVIEW_ONLY')
    gallery.world = bpy.data.scenes['Architecture_A'].world
    light = next(o for o in bpy.data.scenes['Architecture_A'].objects if o.type == 'LIGHT' and o.data.type == 'SUN')
    group.objects.link(light.copy())
    gallery.render.engine = 'CYCLES'
    gallery.cycles.samples = 32
    gallery.cycles.use_denoising = True
    gallery.render.resolution_x = 1200
    gallery.render.resolution_y = 700
    gallery.view_settings.view_transform = 'AgX'
    states = ['OLD', 'DRAINED', '30', '50', '70', 'CHARRED', 'INVASIVE']
    study.mesh('review_flora_floor', [(-8, -9, 0), (57, -9, 0), (57, 9, 0), (-8, 9, 0)], [(0, 1, 2, 3)], group, [CRUST])
    for j, state in enumerate(states):
        ob = bpy.data.objects.new('review_'+state, sources[state].data)
        group.objects.link(ob)
        ob.location = (j*8, 0, .03)
        if state in ('30', '50', '70'):
            for k in range(3):
                old.stem_curve('review_takeover_vein', [(j*8+.15, -.2, 0), (j*8-.6, .4+k*.3, .8), (j*8-1.8, .5+k*.3, 1.6)], .08, group, None, INFECTED)
        ob['ReviewOnly'] = True
    cameras = [('flora_spectrum', (24, -38, 22), (24, 0, 1), 28)]
    for state, j in [('30', 2), ('50', 3), ('70', 4)]:
        cameras.append(('flora_'+state+'_percent', (j*8+3, -7, 5.5), (j*8, 0, 1), 48))
    for name, location, target, lens in cameras:
        gallery.camera = study.camera(name, location, target, group, lens)
        gallery.render.filepath = str(RENDERS/(name+'.png'))
        bpy.ops.render.render(write_still=True)


def main():
    global study, old, CRUST, SCORCH, GLASS, FRESH, DUST, OLD, INFECTED
    RENDERS.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        shutil.copy2(MAIN, INPUT)
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    bpy.context.window.scene = bpy.data.scenes['Independent_Assets_LIBRARY_ONLY']
    study = module('revise_emberfall_architecture.py', 'emberfall_architecture')
    old = module('build_emberfall_prototype.py', 'emberfall_mesh_helpers')
    REPORT['before'] = {s.name: digest_scene(s) for s in bpy.data.scenes}
    REPORT['materials_before'] = len(bpy.data.materials)
    REPORT['flora_original_hashes_before'] = {n: study.fingerprint(bpy.data.objects[n].data) for n in ['prop_drained_wax_rosette', 'prop_drained_seed_shrub', 'prop_charred_ember_rose', 'prop_charred_thorn_pod']}
    transforms = {o.name: [list(row) for row in o.matrix_world] for o in bpy.data.objects if o.type == 'EMPTY'}
    protected = {ob.name: {k: tuple(v.co) for k, v in enumerate(ob.data.vertices) if max(abs(v.co.x), abs(v.co.y)) >= 104}
                 for ob in bpy.data.objects if ob.type == 'MESH' and ob.get('TerrainFaceCount')}
    CRUST = make_material('Ember_BrokenCrust', (.018, .022, .026), .64)
    SCORCH = make_material('Ember_ScorchedStrata', (.082, .035, .014), .94)
    GLASS = bpy.data.materials['Ember_Glass']
    FRESH = make_material('Ember_FreshBreakHeat', (.38, .025, .006), .68, .65)
    DUST = make_material('Ember_WindblownAsh', (.23, .19, .105), .98)
    OLD = make_material('Ember_OldFlora', (.075, .095, .025), .88)
    INFECTED = make_material('Ember_InvasiveGrowth', (.012, .009, .008), .72)
    library = bpy.data.collections['PropLibrary']
    variants = study.coll('Flora_Takeover_States', library)
    rosette = bpy.data.objects['prop_drained_wax_rosette']
    sources = {'OLD': variant(rosette, 'prop_surviving_ash_rosette', 0, variants, True),
               'DRAINED': rosette, 'CHARRED': bpy.data.objects['prop_charred_ember_rose']}
    for ratio in (30, 50, 70):
        sources[str(ratio)] = variant(rosette, f'prop_partial_rosette_{ratio}', ratio/100, variants)
    sources['SHRUB50'] = variant(bpy.data.objects['prop_drained_seed_shrub'], 'prop_partial_seed_shrub_50', .5, variants)
    sources['INVASIVE'] = invasive(variants)
    source_scene = bpy.data.scenes['Independent_Assets_LIBRARY_ONLY']
    bpy.context.window.scene = source_scene
    groups = [bpy.data.collections[n] for n in study.NAMES+study.SCENERY]
    stages = [0, 1, 1, 1, 2]+[0, 1, 2, 2, 2, 0, 2, 1]
    families = ['ENTRY', 'PATH', 'COMBAT', 'SIDE', 'CAP', 'ASHLAND', 'RIDGE', 'RIDGE_HIGH', 'LAVA_FIELD', 'RAVINE', 'DRAINED', 'CHARRED', 'FOOTHILL']
    for i, (group, stage, family) in enumerate(zip(groups, stages, families)):
        terrain = bpy.data.objects[group.name]
        REPORT.setdefault('buried_column_components', {})[group.name] = geology_in_place(terrain, stage)
        details = plates(group, stage, family, terrain)
        propagate(group, details)
        if group.name in (study.NAMES[1], study.NAMES[4]):
            propagate(group, vent_smoke(group, terrain, stage))
        ambient = next(c for c in group.children if c.name.endswith('Props_NonSolid'))
        # Preserve and state-map existing placements in every saved scene.
        for scene in bpy.data.scenes:
            for ob in scene.objects:
                if ob.type != 'MESH' or not ob.get('LibraryAsset') or ob.get('IdentityStateMapped'):
                    continue
                home = ob.parent.get('AssetCollection') if ob.parent else None
                if home != group.name and ob not in list(group.all_objects):
                    continue
                if stage == 0 and 'drained' in ob['LibraryAsset']:
                    ob.data = sources['OLD'].data if 'rosette' in ob['LibraryAsset'] else ob.data
                    ob['FloraState'] = 'OLD_STRESSED' if 'rosette' in ob['LibraryAsset'] else 'DRAINED'
                elif stage == 1 and 'drained' in ob['LibraryAsset']:
                    ob.data = sources['50' if 'rosette' in ob['LibraryAsset'] else 'SHRUB50'].data
                    ob['FloraState'] = 'PARTIAL_50'
                ob['IdentityStateMapped'] = True
        # Small deliberate clusters; stage diversity rather than a plant carpet.
        states = ['OLD', 'DRAINED', '30'] if stage == 0 else ['30', '50', '70', 'SHRUB50'] if stage == 1 else ['70', 'CHARRED', 'INVASIVE']
        coords = [(-34, 66, 1.7), (-23, 72, 1.4), (42, -55, 1.5), (35, -67, 1.3)]
        before = set(ambient.objects)
        add_flora(group, terrain, sources, states, coords)
        added_collection = study.coll(group.name+'_FloraProgression', group)
        for ob in set(ambient.objects)-before:
            ambient.objects.unlink(ob)
            added_collection.objects.link(ob)
        veins = [o for o in added_collection.objects if 'infection_climbing_vein' in o.name]
        if veins:
            temporary = study.coll(group.name+'_vein_parts', added_collection)
            for ob in veins:
                added_collection.objects.unlink(ob)
                temporary.objects.link(ob)
            merged = old.join_objects(temporary, 'prop_'+group.name+'_takeover_veins', root(group))
            temporary.objects.unlink(merged)
            added_collection.objects.link(merged)
            merged['solid'] = False
            bpy.data.collections.remove(temporary)
        propagate(group, added_collection)
    seen = set()
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.get('TerrainFaceCount') or ob.data.as_pointer() in seen:
            continue
        seen.add(ob.data.as_pointer())
        index = next((i for i, name in enumerate(study.NAMES+study.SCENERY) if ob.name.startswith(name)), None)
        if index is not None:
            if ob.name not in study.NAMES+study.SCENERY:
                geology_in_place(ob, stages[index])
            tint_ground(ob, stages[index])
    REPORT['original_empty_transforms_unchanged'] = all([list(row) for row in bpy.data.objects[name].matrix_world] == value for name, value in transforms.items())
    assert REPORT['original_empty_transforms_unchanged']
    REPORT['seam_vertices_unchanged'] = all(tuple(bpy.data.objects[name].data.vertices[k].co) == value for name, points in protected.items() for k, value in points.items())
    assert REPORT['seam_vertices_unchanged']
    REPORT['flora_original_hashes_after'] = {n: study.fingerprint(bpy.data.objects[n].data) for n in REPORT['flora_original_hashes_before']}
    assert REPORT['flora_original_hashes_after'] == REPORT['flora_original_hashes_before']
    REPORT['assets_after'] = {g.name: triangle_budget(g) for g in groups}
    REPORT['materials_after'] = len(bpy.data.materials)
    bpy.context.window.scene = bpy.data.scenes['Architecture_A']
    render_views()
    flora_gallery(sources)
    bpy.context.window.scene = bpy.data.scenes['Architecture_A']
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after_saved_readback'] = {s.name: digest_scene(s) for s in bpy.data.scenes}
    REPORT['blender_version'] = bpy.app.version_string
    (HERE/'identity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    (RENDERS/'identity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('IDENTITY_REVISION_SAVED', REPORT['after_saved_readback'])


if __name__ == '__main__':
    main()
