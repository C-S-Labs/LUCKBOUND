"""Small revised Emberfall foundation study; protected launcher, no exports.

Authored cross-section networks form continuous rock/ash/shelf meshes, including
cliff risers, slumped ledges and molten trenches. The old terrain is never loaded
as a foundation. Only explicitly selected flora and basalt components are reused.
"""
import bpy
import bmesh
import hashlib
import json
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview/EmberfallPrototype.blend')
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
MAIN = OUT / 'EmberfallFoundation.blend'
RNG = random.Random(3103)
REPORT = {'source': str(SOURCE), 'units': 'metres = studs', 'runtime_modified': False,
          'method': 'Welded authored cross-section networks with paired shelf lips/feet, planar strata and continuous buried volume; no warped-plane source or crust inserts.',
          'prototype_only': True}
YS = [-128, -116, -96, -71, -43, -12, 24, 59, 88, 112, 128]
FLORA = ['prop_drained_wax_rosette', 'prop_drained_seed_shrub',
         'prop_charred_ember_rose', 'prop_charred_thorn_pod',
         'prop_surviving_ash_rosette', 'prop_partial_rosette_30',
         'prop_partial_rosette_50', 'prop_partial_rosette_70',
         'prop_partial_seed_shrub_50', 'prop_invasive_root_bloom']
SPECS = [
    ('entry_wasteland_waystone', (0, -512, 0), 'ENTRY', 'WASTELAND', 'none'),
    ('path_wasteland_fault', (0, -256, 0), 'PATH', 'WASTELAND', 'channel'),
    ('combat_wasteland_broken_road', (0, 0, 0), 'COMBAT', 'WASTELAND', 'none'),
    ('side_wasteland_shrine', (256, 0, 0), 'SIDE', 'WASTELAND', 'vent'),
    ('path_fortress_causeway', (0, 256, 28), 'PATH', 'WASTELAND_TO_FORTRESS', 'seam'),
    ('combat_fortress_gateworks', (0, 512, 56), 'COMBAT', 'FORTRESS', 'none'),
]


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def material(name, color, roughness=.9, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def mesh(name, vertices, faces, mats, collection, parent=None, indices=None):
    d = bpy.data.meshes.new(name)
    d.from_pydata(vertices, [], faces)
    d.update()
    for m in mats:
        d.materials.append(m)
    o = bpy.data.objects.new(name, d)
    collection.objects.link(o)
    o.parent = parent
    if indices:
        for p, i in zip(d.polygons, indices):
            p.material_index = i
    bm = bmesh.new()
    bm.from_mesh(d)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(d)
    bm.free()
    return o


def box(name, center, size, mat, collection, parent=None, tilt=0):
    x, y, z = size
    vs = [(a*x/2, b*y/2, c*z/2) for c in (-1, 1) for b in (-1, 1) for a in (-1, 1)]
    fs = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    o = mesh(name, vs, fs, [mat], collection, parent)
    o.location = center
    o.rotation_euler = (tilt, tilt*.37, RNG.uniform(-.055, .055))
    bevel = o.modifiers.new('Worn broken masonry edges', 'BEVEL')
    bevel.width = min(size)*.08
    bevel.segments = 1
    return o


def fingerprint(d):
    h = hashlib.sha256()
    h.update(repr(([tuple(v.co) for v in d.vertices], [tuple(p.vertices) for p in d.polygons],
                   [p.material_index for p in d.polygons], [m.name for m in d.materials])).encode())
    return h.hexdigest()


def reuse_assets():
    with bpy.data.libraries.load(str(SOURCE), link=False) as (src, dst):
        dst.objects = FLORA + ['path_column_pass']
    lib = coll('ReuseLibrary_SOURCE_ONLY')
    originals = {}
    solid = None
    for o in dst.objects:
        assert o is not None, 'Missing reuse source'
        o.parent = None
        o.location = (0, 0, 0)
        if o.name in FLORA:
            lib.objects.link(o)
            originals[o.name] = fingerprint(o.data)
            o.hide_render = True
        else:
            solid = o
    # Extract actual connected basalt modules from the old joined solid asset.
    neighbors = {v.index: set() for v in solid.data.vertices}
    for e in solid.data.edges:
        a, b = e.vertices
        neighbors[a].add(b)
        neighbors[b].add(a)
    unseen = set(neighbors)
    modules = []
    while unseen:
        comp = {unseen.pop()}
        pending = list(comp)
        while pending:
            for k in neighbors[pending.pop()] & unseen:
                comp.add(k)
                unseen.remove(k)
                pending.append(k)
        pts = [solid.data.vertices[k].co for k in comp]
        lo = Vector(tuple(min(p[a] for p in pts) for a in range(3)))
        hi = Vector(tuple(max(p[a] for p in pts) for a in range(3)))
        if hi.z-lo.z < 9 or len(comp) != 96:
            continue
        center = Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z))
        remap = {k: i for i, k in enumerate(sorted(comp))}
        vs = [tuple(solid.data.vertices[k].co-center) for k in sorted(comp)]
        ps = [p for p in solid.data.polygons if all(k in comp for k in p.vertices)]
        o = mesh('reuse_basalt_column_'+str(len(modules)), vs,
                 [tuple(remap[k] for k in p.vertices) for p in ps],
                 list(solid.data.materials), lib, indices=[p.material_index for p in ps])
        o.hide_render = True
        modules.append(o)
    bpy.data.objects.remove(solid, do_unlink=True)
    assert len(modules) >= 2
    lib.hide_render = True
    lib.hide_viewport = True
    REPORT['reused_flora_fingerprints'] = originals
    REPORT['reused_basalt_modules'] = len(modules)
    return lib, modules


def datum(y):
    # Long broad ascent, short level opening approaches; height remains 56 above.
    return 56*max(0, min(1, (y-152)/208))


def local_datum(y, world_y):
    return datum(y+world_y)-datum(world_y)


def lava_material():
    m = material('EF_MoltenAuthoredFlow_REVIEW', (.7, .065, .008), .46, .9)
    n = m.node_tree.nodes
    l = m.node_tree.links
    p = n.get('Principled BSDF')
    coord = n.new('ShaderNodeTexCoord')
    mapping = n.new('ShaderNodeVectorMath')
    mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (.032, .012, .1)
    l.new(coord.outputs['Object'], mapping.inputs[0])
    noise = n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1.15
    noise.inputs['Detail'].default_value = .4
    noise.inputs['Roughness'].default_value = .32
    l.new(mapping.outputs[0], noise.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    stops = [(0, (.035, .009, .006, 1)), (.36, (.2, .027, .01, 1)),
             (.44, (.68, .075, .01, 1)), (.55, (.9, .19, .015, 1)), (.66, (1, .43, .055, 1)), (.8, (1, .65, .14, 1))]
    for j, (pos, color) in enumerate(stops):
        e = ramp.color_ramp.elements[0] if j == 0 else ramp.color_ramp.elements.new(pos)
        e.position = pos
        e.color = color
    ramp.color_ramp.interpolation = 'CONSTANT'
    l.new(noise.outputs['Fac'], ramp.inputs[0])
    attr = n.new('ShaderNodeAttribute')
    attr.attribute_name = 'MoltenEdge'
    mix = n.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1
    l.new(ramp.outputs[0], mix.inputs[1])
    l.new(attr.outputs['Color'], mix.inputs[2])
    l.new(mix.outputs[0], p.inputs['Base Color'])
    l.new(mix.outputs[0], p.inputs['Emission Color'])
    m['ReviewOnly'] = 'Object-space anisotropic low-frequency color flow and painted edge cooling; Roblox realization pending.'
    return m


def foundation(name, collection, root, variant, world_y, lava='none', scenery=False):
    # Sections are unequal and explicit: interruption/slump is shaped at metres,
    # not random vertex noise. Paired lip/foot lines make ledges actual topology.
    profiles = [
        [0, 1, 6, 19, 25, 18, 8, 3, 1, 0, 0],
        [0, 2, 11, 24, 17, 7, 16, 28, 18, 3, 0],
        [0, 1, 3, 12, 27, 24, 8, 0, 0, 0, 0],
        [0, 0, 0, 9, 16, 28, 32, 12, 4, 2, 0],
        [0, 2, 13, 23, 17, 4, 0, 4, 20, 5, 0],
        [0, 0, 6, 24, 35, 29, 17, 2, 8, 3, 0],
        [0, 4, 15, 28, 34, 32, 12, 5, 0, 0, 0],
        [0, 2, 5, 18, 27, 23, 11, 16, 22, 4, 0]]
    shelves = profiles[variant % len(profiles)]
    outer = profiles[(variant+3) % len(profiles)]
    amp = 1.45 if scenery and variant in (2, 6, 7) else .28 if scenery and variant == 0 else .7 if variant == 0 else 1
    # x, relative geological height: ash apron, high shelf, eroded face, partial
    # low shelf, central route, broken bank, trench, outer crust and continuation.
    base_x = [-128, -116, -101, -91, -88, -73, -68, -49, -43, -30,
              0, 31, 45, 51, 59, 67, 82, 86, 103, 116, 128]
    vs, fs, ids = [], [], []
    for j, y in enumerate(YS):
        end = j in (0, len(YS)-1)
        fade = min(1, max(0, (128-abs(y))/24))
        sh, ou = shelves[j]*amp, outer[j]*amp*.63
        ridge = [0, .4, ou*.8, ou+sh*.28, ou+sh*.28-3*fade,
                 ou+sh*.17, ou*.28, ou*.28, 1.1*fade, .25*fade,
                 0, .3*fade, 1.5*fade, 2.8*fade, 2*fade,
                 -9*fade if lava in ('channel', 'basin', 'vent') else sh*.4,
                 -11*fade if lava in ('channel', 'basin', 'vent') else sh*.4,
                 sh*.42, sh*.42+2*fade, ou*.3, 0]
        if lava == 'basin':
            ridge[15:17] = [-14*fade, -16*fade]
        for k, x in enumerate(base_x):
            edge = k in (0, len(base_x)-1)
            jitter = 0 if end or edge or k == 10 else (math.sin(j*.81+k*.16+variant)*9.8 + math.cos(j*.53+k*.34)*4.2)*fade
            xx = x+jitter
            if 2 <= k <= 8:
                xx += (0, 0, 6, 12, 23, 17, 3, -8, -13, -3, 0)[j]*fade*(1 if k <= 6 else .5 if k == 7 else .15)
            if variant in (2, 5) and 8 <= k <= 13:
                xx += (-10 if k <= 9 else 10)*fade
            if lava == 'basin' and k == 16:
                xx += (0, 0, 8, 16, 18, 14, 18, 14, 6, 0, 0)[j]*fade
            if lava == 'basin' and 12 <= k <= 15:
                xx -= (0, 0, 2, 12, 20, 14, 22, 11, 0, 0, 0)[j]*fade*(k-10)/5
            if k > 0 and not edge:
                xx = max(vs[-1][0]+.6, xx)
                xx = min(xx, 128-(len(base_x)-1-k)*.6)
            if lava == 'vent' and k in (15, 16):
                ridge[k] *= 1 if j in (4, 5, 6) else .15
            yy = y if end or edge or 9 <= k <= 11 else y+math.sin(k*.85+j*1.31+variant)*6*fade
            dz = ridge[k] if not end and not edge else 0
            if name == 'combat_wasteland_broken_road' and k >= 11:
                dz *= max(0, min(1, (abs(yy)-32)/24))
            vs.append((xx, yy, local_datum(yy, world_y)+dz))
    width = len(base_x)
    for j in range(len(YS)-1):
        for k in range(width-1):
            a = j*width+k
            fs.append((a, a+1, a+1+width, a+width))
            # Exposed rock changes by surface role; no checkerboard noise.
            ids.append(2 if k in (3, 5, 16) else 1 if k in (2, 4, 6, 7, 14, 17, 18) else 0)
    perimeter = list(range(width)) + [j*width+width-1 for j in range(1, len(YS))] + list(range((len(YS)-1)*width+width-2, (len(YS)-1)*width-1, -1)) + [j*width for j in range(len(YS)-2, 0, -1)]
    start = len(vs)
    bottom = -46
    for a in perimeter:
        vs.append((vs[a][0], vs[a][1], bottom))
    for j, a in enumerate(perimeter):
        nxt = (j+1) % len(perimeter)
        fs.append((a, start+j, start+nxt, perimeter[nxt]))
        ids.append(1)
    fs.append(tuple(reversed(range(start, len(vs)))))
    ids.append(1)
    o = mesh('chunk_'+name, vs, fs, [ASH, ROCK, STRATA], collection, root, ids)
    o['FoundationMethod'] = REPORT['method']
    o['Footprint'] = '256 x 256'
    o['VisualCollision'] = 'Simplify central corridor and combat apron; do not collide every shelf fracture.'
    if lava in ('channel', 'basin', 'vent'):
        # Trace the actual embedded trench, occupying its width; irregular end
        # closure lives inside the terrain rather than a rectangular basin stamp.
        lv, lf = [], []
        stations = range(2, 9) if lava != 'vent' else range(4, 7)
        for j in stations:
            left, right = Vector(vs[j*width+15]), Vector(vs[j*width+16])
            for t in (0, .12, .42, .76, .94, 1):
                p = left.lerp(right, t)
                p.z = local_datum(p.y, world_y) + (-7.1 if lava != 'basin' else -10)
                lv.append(tuple(p))
        for j in range(len(list(stations))-1):
            for k in range(5):
                a = j*6+k
                lf.append((a, a+1, a+7, a+6))
        molten = mesh('molten_'+lava+'_'+name, lv, lf, [LAVA], collection, root)
        colors = molten.data.color_attributes.new(name='MoltenEdge', type='FLOAT_COLOR', domain='POINT')
        for k, item in enumerate(colors.data):
            edge = k % 6 in (0, 5) or k//6 in (0, len(list(stations))-1)
            item.color = (.085, .06, .045, 1) if edge else (.8, .75, .65, 1)
        molten['Archetype'] = lava
        if lava == 'basin':
            # Crust islands are attached geology with buried roots, not surface
            # decals: taper unequal solid polygon forms from the trench floor.
            for j, (x, y, rx, ry, top) in enumerate([(69, -48, 8, 14, -5), (86, 35, 11, 18, -6), (54, 68, 7, 9, -4)]):
                vv = []
                for z, scale in [(-20, 1.15), (top-1.2, 1), (top, .76)]:
                    vv += [(x+rx*scale*a, y+ry*scale*b, z) for a, b in [(-1,-.5),(-.35,-1),(.6,-.8),(1,.25),(.25,1),(-.9,.65)]]
                ff = [tuple(range(12,18)), tuple(reversed(range(6)))]
                ff += [(q*6+k,q*6+(k+1)%6,(q+1)*6+(k+1)%6,(q+1)*6+k) for q in range(2) for k in range(6)]
                mesh('rooted_crust_remnant_'+str(j), vv, ff, [ROCK], collection, root)
    return o


def tree(o):
    return BVHTree.FromPolygons([v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])


def floor(t, x, y):
    p, _, _, _ = t.ray_cast(Vector((x, y, 250)), Vector((0, 0, -1)))
    assert p is not None
    return p.z


def copy_asset(source, name, collection, parent, loc, scale=1):
    o = bpy.data.objects.new(name, source.data)
    collection.objects.link(o)
    o.parent = parent
    o.location = loc
    o.scale = (scale,)*3
    o.rotation_euler.z = RNG.uniform(0, math.tau)
    o['ReuseSource'] = source.name
    o['solid'] = False
    return o


def road(collection, root, t, intensity, ascent=False):
    for j, y in enumerate((-100, -63, -23, 20, 57, 95)):
        # Sparse broad, broken paving: land remains visible between fragments.
        if intensity < 2 and j % 2:
            continue
        for x in (-11, 7):
            z = floor(t, x, y)
            box('road_remnant', (x+RNG.uniform(-3, 3), y+RNG.uniform(-3, 3), z-.55), (15+RNG.uniform(-4, 2), RNG.uniform(9, 16), 1.1), MASON, collection, root, -.025 if ascent else .015)


def broken_wall(collection, root, t, x, y, length, height, axis='Y'):
    # Unequal torn silhouette, staggered surviving courses and slumped fragments.
    for i in range(round(length/9)):
        px, py = (x+i*8.6, y) if axis == 'X' else (x, y+i*8.6)
        h = height * RNG.uniform(.3, 1)
        for course in range(max(1, round(h/4))):
            xx = px+(1.3 if course % 2 and axis == 'X' else 0)
            yy = py+(1.3 if course % 2 and axis == 'Y' else 0)
            box('fused_ruin_masonry', (xx, yy, floor(t, xx, yy)+course*3.6+1.6),
                (8.2, 4.5, 3.6) if axis == 'X' else (4.5, 8.2, 3.6), MASON, collection, root, .02 if course else -.09)


def architecture(name, collection, root, t, stage):
    road(collection, root, t, stage, stage == 3)
    if stage == 0:
        box('broken_waystone_base', (-24, -42, floor(t, -24, -42)+1.1), (9, 7, 2.7), MASON, collection, root)
        box('tilting_waystone', (-24, -42, floor(t, -24, -42)+6.4), (3, 3, 10), MASON, collection, root, .24)
    elif stage == 1:
        broken_wall(collection, root, t, -29, -6, 24, 6, 'X')
        box('fallen_marker', (-26, 56, floor(t, -26, 56)+1.1), (4, 12, 3), MASON, collection, root, .13)
    elif stage == 2:
        broken_wall(collection, root, t, -35, 35, 38, 9)
        broken_wall(collection, root, t, -33, 39, 22, 5, 'X')
        for i in range(4):
            box('charred_fence_remnant', (25+i*4, -45+i*6, floor(t, 25+i*4, -45+i*6)+2), (1, 1, 5), WOOD, collection, root, .4)
    elif stage == 3:
        broken_wall(collection, root, t, -39, -57, 60, 14)
        broken_wall(collection, root, t, 35, 25, 44, 19)
        box('slumped_gate_lintel', (-29, 55, floor(t, -29, 55)+3), (23, 7, 7), MASON, collection, root, -.23)
        for i in range(3):
            box('broken_stairs_into_ash', (-30, -93+i*7, floor(t, -30, -93+i*7)+i*.8), (10, 7, 2), MASON, collection, root)
    else:
        # First gateworks, not a whole castle or a boss arena.
        for x, y, h in [(-42, 25, 47), (37, 40, 31)]:
            broken_wall(collection, root, t, x, y-12, 27, h)
            broken_wall(collection, root, t, x, y-12, 24, h*.88, 'X')
            broken_wall(collection, root, t, x+17, y-6, 18, h*.7)
        broken_wall(collection, root, t, -40, 75, 56, 16, 'X')
        for x, y, sz in [(-12, 39, 11), (23, 67, 8), (-32, -39, 12)]:
            box('recent_gatework_collapse', (x, y, floor(t, x, y)+2), (sz, 8, 5), MASON, collection, root, .32)


def enrich(name, collection, root, terrain, stage, modules, scenery=False):
    t = tree(terrain)
    solid = coll(name+'_SOLID_DECOR', collection)
    plants = coll(name+'_FLORA_NONSOLID', collection)
    if not scenery:
        architecture(name, solid, root, t, stage)
    elif stage:
        broken_wall(solid, root, t, -19, 8, 34, 7 if stage < 4 else 35)
        if stage == 4:
            broken_wall(solid, root, t, -19, 8, 24, 32, 'X')
    states = [4, 0, 5] if stage < 2 else [5, 6, 8, 7] if stage < 4 else [7, 2, 9]
    for j in range(7 if scenery else 11):
        x = RNG.choice([-1, 1])*RNG.uniform(20, 44)
        y = RNG.uniform(-113, 111)
        source = bpy.data.objects[FLORA[states[j % len(states)]]]
        copy_asset(source, name+'_flora', plants, root, (x, y, floor(t, x, y)+.05), RNG.uniform(1.5, 2.5))
    for j, (x, y) in enumerate([(-67, -23), (-94, 63)] if not scenery else [(-78, 33)]):
        o = copy_asset(modules[(stage+j) % len(modules)], name+'_basalt_reuse', solid, root,
                       (x, y, floor(t, x, y)-3), .75 if scenery else .6)
        o['solid'] = True
    return t


def camera(name, location, target, lens=34, ortho=None):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.clip_end = 10000
    if ortho:
        d.type = 'ORTHO'
        d.ortho_scale = ortho
    o = bpy.data.objects.new(name, d)
    REVIEW.objects.link(o)
    o.location = location
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


def triangles(o):
    if o.type != 'MESH':
        return 0
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def main():
    global ASH, ROCK, STRATA, MASON, WOOD, LAVA, REVIEW
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'Emberfall_Foundation_Review'
    lib, modules = reuse_assets()
    ASH = material('EF_AshGround', (.086, .079, .065))
    ROCK = material('EF_BasaltFreshBreak', (.037, .044, .05), .82)
    STRATA = material('EF_ExposedVolcanicStrata', (.055, .046, .033))
    MASON = material('EF_WeatheredCivilization', (.16, .137, .103))
    WOOD = material('EF_CharredTimber', (.025, .018, .012))
    LAVA = lava_material()
    play = coll('Playable_6_FOUNDATION_STUDY')
    scenerylib = coll('Scenery_8_SOURCE_LIBRARY')
    scenerylib.hide_render = True
    scenerylib.hide_viewport = True
    ring = coll('SceneryRing_REVIEW_ONLY')
    REVIEW = coll('Cameras_Lights_Scale_REVIEW_ONLY')
    REPORT['chunks'] = []
    for i, (name, pos, role, zone, lava) in enumerate(SPECS):
        c = coll(name, play)
        root = bpy.data.objects.new(name+'_ORIGIN', None)
        c.objects.link(root)
        root.location = pos
        if role == 'SIDE':
            root.rotation_euler.z = math.pi/2
        root['Role'] = role
        root['Zone'] = zone
        root['SocketHeightsLocal'] = '-28,+28' if i == 4 else '0'
        terrain = foundation(name, c, root, i, pos[1], lava)
        t = enrich(name, c, root, terrain, i if i < 3 else 2 if i == 3 else i-1, modules)
        if lava == 'seam':
            # Heated face below an uplifted lip, not open molten ground.
            box('heat_inside_fault_face', (-71, 24, floor(t, -71, 24)-1), (.35, 17, .7),
                material('EF_HeatSeam', (.55, .065, .01), .65, .6), c, root)
        row = {'name': name, 'role': role, 'zone': zone, 'origin_world': pos,
               'footprint': [256, 256], 'lava': lava, 'elevation_delta': 56 if i == 4 else 0,
               'objects': len(c.all_objects), 'triangles': sum(triangles(o) for o in c.all_objects),
               'terrain_triangles': triangles(terrain), 'floor_samples': []}
        for x, y in [(0, -116), (0, 0), (0, 116), (-24, 0), (24, 0)]:
            p, n, _, _ = t.ray_cast(Vector((x, y, 250)), Vector((0, 0, -1)))
            row['floor_samples'].append({'xy': [x, y], 'height': round(p.z, 4), 'slope': round(math.degrees(math.acos(min(1, n.z))), 2)})
        assert all(v['slope'] < 25 for v in row['floor_samples'])
        REPORT['chunks'].append(row)
    families = [('open_ashland', 0, 'none', 0), ('ruined_outskirts', 1, 'none', 1),
                ('broken_ridge_shelf', 2, 'none', 0), ('low_lava_terrain', 3, 'basin', 0),
                ('ash_faultland', 4, 'none', 0), ('infected_outskirts', 5, 'none', 2),
                ('fortress_silhouette', 6, 'none', 4), ('elevated_shelf', 7, 'none', 3)]
    cells = {(round(pos[0]/256), round(pos[1]/256)) for _, pos, *_ in SPECS}
    # One connected local ring with reused scenery assets; fitted elevation follows
    # the same datum as the playable ascent, without editing any runtime loader.
    perimeter = {(x, y) for x, y in cells for x, y in [(x+dx, y+dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]} - cells
    REPORT['scenery'] = []
    groups = {}
    for k, (name, variant, lava, stage) in enumerate(families):
        c = coll('scenery_'+name, scenerylib)
        root = bpy.data.objects.new(name+'_LOCAL_ORIGIN', None)
        c.objects.link(root)
        terrain = foundation(name, c, root, variant, 0, lava, True)
        enrich(name, c, root, terrain, stage, modules, True)
        groups[k] = c
        REPORT['scenery'].append({'name': name, 'objects': len(c.all_objects), 'triangles': sum(triangles(o) for o in c.all_objects), 'footprint': [256, 256]})
    REPORT['ring_instances'] = []
    for x, y in sorted(perimeter):
        # Only ONE broad molten feature in the entire visible arrangement.
        k = 3 if (x, y) == (2, 0) else (6 if y >= 2 else 7 if y == 1 else [0, 1, 2, 4, 5][(x+y*3) % 5])
        source = groups[k]
        c = coll(f'ring_{x}_{y}_{families[k][0]}', ring)
        origin = bpy.data.objects.new(f'ring_origin_{x}_{y}', None)
        c.objects.link(origin)
        origin.location = (x*256, y*256, datum(y*256))
        if y != 1 and k != 3:
            origin.rotation_euler.z = math.radians([0, 90, 180, 270][(x*3+y*7) % 4])
        for old in source.all_objects:
            if old.type != 'MESH':
                continue
            o = old.copy()
            c.objects.link(o)
            o.parent = origin
            if old.name.startswith('chunk_') and y == 1:
                o.data = old.data.copy()
                for v in o.data.vertices:
                    if v.co.z > -40:
                        v.co.z += local_datum(v.co.y, 256)
            elif y == 1:
                o.location.z += local_datum(o.location.y, 256)
        REPORT['ring_instances'].append({'cell': [x, y], 'family': families[k][0], 'datum': datum(y*256)})
    # Grounded distant apron and stressed ridge silhouettes, not void edges.
    far = coll('DistantGround_REVIEW_ONLY')
    apron_vs, apron_fs, shared = [], [], {}
    for x in range(-8, 9):
        for y in range(-9, 10):
            if (x, y) in cells | perimeter:
                continue
            face = []
            for xx, yy in [(x*256-128,y*256-128),(x*256+128,y*256-128),
                           (x*256+128,y*256+128),(x*256-128,y*256+128)]:
                key = (xx, yy)
                if key not in shared:
                    shared[key] = len(apron_vs)
                    apron_vs.append((xx, yy, datum(yy)-.35))
                face.append(shared[key])
            apron_fs.append(tuple(face))
    mesh('continuous_land_apron_REVIEW', apron_vs, apron_fs, [ASH], far)
    for j in range(9):
        x, y = -1200+j*320, 1290+RNG.uniform(-90, 90)
        root = bpy.data.objects.new('horizon_shelf_origin', None)
        far.objects.link(root)
        root.location = (x, y, -18)
        root.scale = (3, 2.5, 4.5)
        root.rotation_euler.z = math.radians(70+j*23)
        foundation('distant_stressed_shelf_'+str(j), far, root, (j+2)%8, 0, 'none', True)
    smoke = bpy.data.materials.new('EF_ActiveFailureSmoke_REVIEW')
    smoke.use_nodes = True
    ns = smoke.node_tree.nodes
    ns.remove(ns.get('Principled BSDF'))
    vol = ns.new('ShaderNodeVolumePrincipled')
    vol.inputs['Density'].default_value = .035
    vol.inputs['Color'].default_value = (.19, .17, .145, 1)
    smoke.node_tree.links.new(vol.outputs['Volume'], ns.get('Material Output').inputs['Volume'])
    for x, y, z in [(33, 540, 78), (332, 511, 62), (322, 31, 0), (-212, -197, 0)]:
        for j in range(3):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(x+j*4, y+j*2, z+9+j*14))
            o = bpy.context.object
            o.name = 'smoke_from_active_fracture_REVIEW'
            for c in list(o.users_collection):
                c.objects.unlink(o)
            REVIEW.objects.link(o)
            o.scale = (6+j*3, 7+j*3, 12+j*3)
            o.data.materials.append(smoke)
    for pos in [(0, -560, 2.5), (0, 247, 29), (0, 493, 58.5)]:
        box('5_stud_scale_reference', pos, (1.7, 1, 5), material('ScaleReference'+str(pos), (.24, .3, .32)), REVIEW)
    sun_d = bpy.data.lights.new('Cool_ash_daylight', 'SUN')
    sun_d.energy = 3
    sun_d.angle = .15
    sun = bpy.data.objects.new('Cool_ash_daylight', sun_d)
    REVIEW.objects.link(sun)
    sun.rotation_euler = (.55, -.6, -.45)
    scene.world = bpy.data.worlds.new('Ash_Haze')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.16, .21, .25, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    shots = [
        ('overview', (1060, -1300, 1090), (90, 0, 10), 40),
        ('entry_no_open_lava', (27, -606, 7), (-5, -444, 14), 24),
        ('path_narrow_channel', (42, -267, 12), (78, -238, -7), 30),
        ('combat_broken_shelves', (23, -87, 8), (-31, 63, 16), 26),
        ('ascent_to_gateworks', (9, 151, 8), (-2, 392, 67), 25),
        ('raised_gateworks', (10, 417, 63), (-5, 552, 77), 24),
        ('broad_lava_player', (556, -54, 14), (604, -18, -9), 32),
        ('broad_lava_close', (568, -16, 5), (585, 12, -10), 37),
        ('terrain_meso', (-18, -463, 18), (-75, -502, 12), 34),
        ('flora_partial', (32, -238, 8), (38, -215, 4), 40),
        ('seam_baseline', (0, -394, 5), (-15, -357, 7), 28),
        ('seam_raised', (0, 371, 61), (-4, 426, 65), 28),
    ]
    cams = [camera(n, loc, target, lens) for n, loc, target, lens in shots]
    scene.camera = cams[0]
    scene['README'] = 'Six playable + eight scenery foundation study. Fresh terrain, retained flora/basalt only. No exports/runtime. Review before collision/Studio.'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_location = (0, 0, 28)
                area.spaces.active.region_3d.view_distance = 1700
                area.spaces.active.clip_end = 10000
                area.spaces.active.shading.color_type = 'MATERIAL'
    REPORT['visible_objects'] = sum(1 for o in scene.objects if not o.hide_render and not any(c.hide_render for c in o.users_collection))
    visible = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render and not any(c.hide_render for c in o.users_collection)]
    # Source library children are excluded explicitly (ancestor visibility).
    visible = [o for o in visible if o not in list(scenerylib.all_objects) and o not in list(lib.all_objects)]
    REPORT['visible_mesh_objects'] = len(visible)
    REPORT['visible_triangles_base'] = sum(triangles(o) for o in visible)
    REPORT['max_visible_mesh_triangles'] = max(triangles(o) for o in visible)
    REPORT['collections'] = [play.name, scenerylib.name, ring.name, far.name, lib.name, REVIEW.name]
    REPORT['source_flora_unchanged'] = all(fingerprint(bpy.data.objects[n].data) == h for n, h in REPORT['reused_flora_fingerprints'].items())
    assert REPORT['source_flora_unchanged']
    REPORT['studio_ready'] = False
    REPORT['collision_needs'] = 'Broad route, ascent and combat walk skins; simplify shelf risers and masonry, keep plant tissue and decorative cracks nonsolid. No collision generated.'
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    for cam in cams:
        scene.camera = cam
        scene.render.filepath = str(OUT/(cam.name+'.png'))
        bpy.ops.render.render(write_still=True)
    # Actual placed plant close-up; point framing at its evaluated geometry.
    planted = next(o for o in scene.objects if o.get('ReuseSource') == 'prop_partial_rosette_50' and o.parent and o.parent.name.startswith('combat_wasteland'))
    center = planted.matrix_world @ Vector((0, 0, 2))
    cam = camera('flora_actual_50', center+Vector((9, -13, 8)), center, 42)
    scene.camera = cam
    scene.render.filepath = str(OUT/'flora_actual_50.png')
    bpy.ops.render.render(write_still=True)
    changes = []
    color_changes = []
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                changes.append((n, n.inputs['Emission Strength'].default_value))
                n.inputs['Emission Strength'].default_value = 0
                if m == LAVA or m.name == 'EF_HeatSeam':
                    base = n.inputs['Base Color']
                    links = [(link.from_socket, link.to_socket) for link in list(base.links)]
                    color_changes.append((base, tuple(base.default_value), links, m))
                    for link in list(base.links):
                        m.node_tree.links.remove(link)
                    base.default_value = (.055, .05, .044, 1)
    for index in (0, 3, 4, 5):
        scene.camera = cams[index]
        scene.render.filepath = str(OUT/('glow_minimized_'+cams[index].name+'.png'))
        bpy.ops.render.render(write_still=True)
    for n, value in changes:
        n.inputs['Emission Strength'].default_value = value
    for base, value, links, m in color_changes:
        base.default_value = value
        for a, b in links:
            m.node_tree.links.new(a, b)
    scene.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    (OUT/'foundation_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    (HERE/'foundation_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('FOUNDATION_COMPLETE', json.dumps({k: REPORT[k] for k in ('visible_mesh_objects', 'visible_triangles_base', 'max_visible_mesh_triangles', 'source_flora_unchanged')}))


if __name__ == '__main__':
    main()
