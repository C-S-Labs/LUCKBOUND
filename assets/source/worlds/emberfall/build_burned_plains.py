"""Area I only: fresh rolling countryside and directional active burn study.

Run through tools/run_blender.py. Historical live input stays intact; no exports.
This is a visual foundation, not a production kit or collision implementation.
"""
import bpy
import bmesh
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from mathutils import Vector

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview')
HERE = Path(__file__).resolve().parent
INPUT = OUT / 'Input_DesignReset.blend'
MAIN = OUT / 'BurnedPlains.blend'
RNG = random.Random(51026)
SPECS = [('opening_edge', -256), ('active_burn_mid_plains', 0), ('interior_edge', 256)]
REPORT = {'scope': 'AREA I ONLY', 'input': str(INPUT), 'production_export': False,
          'runtime_modified': False, 'units': 'one metre = one stud', 'seed': 51026}


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or SCENE.collection).children.link(c)
    return c


def material(name, color, emission=0):
    m = bpy.data.materials.new('BP_' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .94
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def mesh(name, vertices, faces, mats, coll, indices=None):
    d = bpy.data.meshes.new(name)
    d.from_pydata(vertices, [], faces)
    d.update()
    for m in mats:
        d.materials.append(m)
    if indices:
        for p, i in zip(d.polygons, indices):
            p.material_index = i
    o = bpy.data.objects.new(name, d)
    coll.objects.link(o)
    return o


def hill(x, y):
    """Broad temperate landforms, shallow drainage and a 56-stud road ascent."""
    t = max(0, min(1, (y + 384) / 768))
    rise = 56 * t * t * (3 - 2 * t)
    undulation = (8 * math.sin(x / 83 + .4) * math.cos(y / 116)
                  + 4 * math.sin(x / 43 - y / 97))
    drainage = -5 * math.exp(-((x + 78 + 10 * math.sin(y / 65)) / 18) ** 2)
    # Level 24-stud socket mouths and a 24-stud approach band, at three datums.
    edge = min(abs(y - v) for v in (-384, -128, 128, 384))
    socket_weight = min(1, edge / 24) * min(1, max(0, (abs(x) - 12) / 18))
    # Flatten the entire center road; broad hills remain off the route.
    road_weight = min(1, max(0, (abs(x - road_x(y)) - 12) / 24))
    return rise + (undulation + drainage) * min(socket_weight, road_weight)


def road_x(y):
    return 12 * math.sin(math.pi * (y + 384) / 256) ** 3


def front(x):
    return -73 + 52 * math.sin(x / 64 + .6) + 23 * math.sin(x / 27)


def burn_distance(x, y):
    """Advancing front curls around a west windbreak and protected field."""
    v = y - front(x)
    v += 265 * math.exp(-((x + 85) / 42) ** 2 - ((y + 262) / 104) ** 2)
    return v


def burn_state(x, y):
    """Coherent front with an early west tongue and defensible damp pockets."""
    v = burn_distance(x, y)
    damp = ((x + 79 + 10 * math.sin(y / 65)) / 14) ** 2 + ((y + 48) / 90) ** 2
    wall_pocket = ((x - 77) / 32) ** 2 + ((y + 205) / 43) ** 2
    if v < -166 or damp < 1 or wall_pocket < 1:
        # Windward outer fields are already heat-dried ahead of the flame front.
        # Keep entry's road/meadow green; don't make the whole scenery apron lush.
        if y < -384 and abs(x) > 190 + 30 * math.sin(y / 87):
            return 1
        return 0
    dry_refuge = ((x - 60) / 35) ** 2 + ((y - 194) / 39) ** 2
    if v < 53 or dry_refuge < 1:
        return 1
    return 2


def terrain(name, bounds, coll, origin_y=0):
    xmin, xmax, ymin, ymax = bounds
    step = 4
    nx, ny = round((xmax - xmin) / step), round((ymax - ymin) / step)
    vs = [(xmin + i * step, ymin + j * step - origin_y,
           hill(xmin + i * step, ymin + j * step) - hill(0, origin_y))
          for j in range(ny + 1) for i in range(nx + 1)]
    fs, idx, counts = [], [], Counter()
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            x, y = xmin + (i + .5) * step, ymin + (j + .5) * step
            state = burn_state(x, y)
            counts[state] += step * step
            # Little color variation; silhouette and plants do the visual work.
            tone = int((math.sin(x / 23) + math.cos(y / 31) + 2) * .74)
            fs.extend([(a, a + 1, a + nx + 2), (a, a + nx + 2, a + nx + 1)])
            idx.extend([state * 3 + min(2, tone)] * 2)
    o = mesh(name, vs, fs, GROUND, coll, idx)
    o.location = (0, origin_y, hill(0, origin_y))
    o['SurfaceVertexCount'] = len(vs)
    # Closed buried shell; no visible cliff around the modular footprint.
    perimeter = list(range(nx + 1))
    perimeter += [j * (nx + 1) + nx for j in range(1, ny + 1)]
    perimeter += [ny * (nx + 1) + i for i in range(nx - 1, -1, -1)]
    perimeter += [j * (nx + 1) for j in range(ny - 1, 0, -1)]
    n = len(vs)
    vs += [(vs[k][0], vs[k][1], -40 - hill(0, origin_y)) for k in perimeter]
    fs += [(perimeter[k], n + k, n + (k + 1) % len(perimeter),
            perimeter[(k + 1) % len(perimeter)]) for k in range(len(perimeter))]
    fs.append(tuple(reversed(range(n, len(vs)))))
    # Recreate with shell data, then recalculate winding cheaply.
    o.data.clear_geometry()
    o.data.from_pydata(vs, [], fs)
    for p, mi in zip(o.data.polygons, idx):
        p.material_index = mi
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free()
    o['FootprintStuds'] = [xmax - xmin, ymax - ymin]
    return o, counts


def tube(vs, fs, a, b, ra, rb, sides=7):
    a, b = Vector(a), Vector(b)
    direction = (b - a).normalized()
    u = direction.cross(Vector((0, 0, 1)))
    if u.length < .01:
        u = Vector((1, 0, 0))
    u.normalize(); v = direction.cross(u)
    base = len(vs)
    for p, r in ((a, ra), (b, rb)):
        vs.extend(tuple(p + r * (u * math.cos(k * math.tau / sides)
                                  + v * math.sin(k * math.tau / sides))) for k in range(sides))
    fs.append(tuple(base + k for k in reversed(range(sides))))
    fs.append(tuple(base + sides + k for k in range(sides)))
    fs.extend((base + k, base + (k + 1) % sides,
               base + sides + (k + 1) % sides, base + sides + k) for k in range(sides))


def beam(name, a, b, radius, mat, coll, end_radius=None):
    vs, fs = [], []
    tube(vs, fs, a, b, radius, end_radius or radius)
    return mesh(name, vs, fs, [mat], coll)


def blob(name, center, scale, mat, coll, subdivision=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivision, radius=1)
    d = bpy.data.meshes.new(name)
    bm.to_mesh(d); bm.free()
    d.materials.append(mat)
    o = bpy.data.objects.new(name, d); coll.objects.link(o)
    o.location = center; o.scale = scale
    o.rotation_euler.z = RNG.uniform(0, math.tau)
    return o


def grasses(coll, count, bounds, label):
    """Actual blade silhouettes in all states; black stubble never bare geology."""
    vs, fs, mi = [], [], []
    for _ in range(count):
        x = RNG.uniform(bounds[0], bounds[1]); y = RNG.uniform(bounds[2], bounds[3])
        if abs(x - road_x(y)) < 6:
            continue
        state = burn_state(x, y)
        h = RNG.uniform(.6, 1.7) * (1 if state < 2 else .5)
        for k in range(RNG.randint(4, 7)):
            dx, dy = RNG.uniform(-.7, .7), RNG.uniform(-.7, .7)
            a = RNG.uniform(0, math.tau); w = RNG.uniform(.06, .15)
            z = hill(x + dx, y + dy) + .03
            base = len(vs)
            vs.extend([(x + dx - w * math.cos(a), y + dy - w * math.sin(a), z),
                       (x + dx + w * math.cos(a), y + dy + w * math.sin(a), z),
                       (x + dx + .25 * math.sin(a), y + dy + .25 * math.cos(a), z + h)])
            fs.append((base, base + 1, base + 2)); mi.append(state * 2 + RNG.randrange(2))
    o = mesh(label, vs, fs, GRASS, coll, mi)
    o['NoncollidableVisual'] = True
    return o


def tree(x, y, height, coll, forced=None):
    state = burn_state(x, y) if forced is None else forced
    z = hill(x, y)
    vs, fs = [], []
    lean = RNG.uniform(-2, 2)
    tube(vs, fs, (x, y, z), (x + lean, y, z + height * .76),
         height * .035, height * .012, 9)
    crowns = []
    for j in range(7):
        angle = j * 2.4 + RNG.uniform(-.3, .3)
        r = height * RNG.uniform(.19, .33)
        a = (x + lean * .6, y, z + height * (.36 + j * .052))
        b = (x + math.cos(angle) * r, y + math.sin(angle) * r,
             z + height * (.62 + j * .042))
        tube(vs, fs, a, b, height * .012, .10)
        for q in range(2):
            tip = (b[0] + math.cos(angle + q - .5) * r * .35,
                   b[1] + math.sin(angle + q - .5) * r * .35, b[2] + height * .14)
            tube(vs, fs, b, tip, .13, .025, 5)
        # Scorch predominantly source-facing crown; partially defoliated states.
        retain = state == 0 or (state == 1 and j % 3 != 0) or (state == 2 and j == 0 and y < 110)
        if retain:
            crown_state = 0 if state < 2 and b[1] < y - 1 else min(2, state + (j % 3 == 1))
            crowns.append(blob('tree_crown_' + str(state), b, (r * .8, r * .72, height * .16),
                               LEAF[crown_state], coll, 2))
    trunk = mesh('tree_' + ['surviving', 'partially_scorched', 'freshly_blackened'][state],
                 vs, fs, [WOOD if state == 0 else CHARWOOD], coll)
    trunk['BurnState'] = state
    return trunk


def road(coll):
    vs, fs, mi = [], [], []
    for y in range(-560, 617, 4):
        x = road_x(y)
        w = 4.2 + .7 * math.sin(y / 21)
        for xx in (x - w, x + w):
            vs.append((xx, y, hill(xx, y) + .22))
        if len(vs) > 2:
            n = len(vs); fs.append((n - 4, n - 2, n - 1, n - 3))
            mi.append(burn_state(x, y))
    return mesh('old_winding_field_track', vs, fs, ROAD, coll, mi)


def fence(points, coll, damaged=False):
    for i, (x, y) in enumerate(points):
        z = hill(x, y)
        mat = CHARWOOD if burn_state(x, y) == 2 else WOOD
        beam('field_fence_post', (x, y, z), (x + (.5 if damaged else 0), y, z + 3.6), .23, mat, coll)
        if i and not (damaged and i % 3 == 0):
            px, py = points[i - 1]; pz = hill(px, py)
            for h in (1.35, 2.8):
                beam('scorched_field_rail', (px, py, pz + h), (x, y, z + h), .16, mat, coll)
        elif i and damaged:
            beam('fallen_burned_rail', (x - 4, y + 1, z + .2), (x + 2, y + 3, z + .5), .16, mat, coll)


def wall(coll):
    for x in range(35, 119, 4):
        y = -184 + 4 * math.sin(x / 19)
        for course in range(3):
            xx = x + (course % 2) * 1.4
            blob('sheltering_dry_stone_wall', (xx, y, hill(xx, y) + .55 + course * .85),
                 (2.1, 1.1, .65), STONE, coll)


def flame(x, y, h, coll):
    z = hill(x, y)
    vs, fs = [], []
    # Tapered irregular tongues, not glowing ground/crack ribbons.
    for k in range(3):
        dx = RNG.uniform(-.8, .8); dy = RNG.uniform(-.6, .6)
        a = len(vs); w = RNG.uniform(.25, .7)
        vs.extend([(x + dx - w, y + dy, z), (x + dx, y + dy - w, z),
                   (x + dx + w, y + dy, z), (x + dx, y + dy + w, z),
                   (x + dx - .5, y + dy - .25, z + h * RNG.uniform(.6, 1.2))])
        fs.extend([(a + j, a + (j + 1) % 4, a + 4) for j in range(4)])
    o = mesh('active_grass_fire', vs, fs, [FIRE, FIRECORE], coll,
             [0 if i % 3 else 1 for i in range(len(fs))])
    o['ReviewFireOnly'] = True
    return o


def smoke_material():
    m = bpy.data.materials.new('BP_SoftProceduralSmoke_REVIEW')
    m.use_nodes = True; n = m.node_tree.nodes; n.clear(); l = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial'); vol = n.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (.22, .235, .25, 1)
    tex = n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 4
    tex.inputs['Detail'].default_value = 2
    coord = n.new('ShaderNodeTexCoord')
    sub = n.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (.5, .5, .5)
    length = n.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ramp = n.new('ShaderNodeMapRange'); ramp.clamp = True
    ramp.inputs['From Min'].default_value = .1; ramp.inputs['From Max'].default_value = .5
    ramp.inputs['To Min'].default_value = .48; ramp.inputs['To Max'].default_value = 0
    mult = n.new('ShaderNodeMath'); mult.operation = 'MULTIPLY'
    l.new(coord.outputs['Generated'], sub.inputs[0]); l.new(sub.outputs['Vector'], length.inputs[0])
    l.new(length.outputs['Value'], ramp.inputs['Value'])
    l.new(coord.outputs['Generated'], tex.inputs['Vector'])
    l.new(ramp.outputs['Result'], mult.inputs[0]); l.new(tex.outputs['Fac'], mult.inputs[1])
    l.new(mult.outputs[0], vol.inputs['Density']); l.new(vol.outputs['Volume'], out.inputs['Volume'])
    return m


def smoke(x, y, height, coll):
    for k in range(5):
        s = 2.8 + k * 2
        blob('fresh_burn_smoke_REVIEW', (x - k * 2.3, y - k * 1.8, hill(x, y) + 2 + k * height / 5),
             (s, s * .9, height / 4), SMOKE, coll, 2)


def fire_fronts(coll):
    # Sample the actual char/stressed interface, including the opening tongue.
    sites = []
    for x in range(-360, 361, 3):
        if abs(x) < 23:
            continue
        previous = burn_distance(x, -380) >= 53
        for y in range(-377, 181, 3):
            current = burn_distance(x, y) >= 53
            if previous != current and RNG.random() > .08:
                flame(x, y, RNG.uniform(.8, 3.4), coll)
                if RNG.random() < .055:
                    sites.append((x, y))
            previous = current
    for x, y in sites:
        smoke(x, y, RNG.uniform(20, 42), coll)
    # Fresh smoldering trunks and a sparse deeper tree fire.
    for x, y in [(-104, 116), (87, 190), (-180, 278), (130, 326), (300, 395)]:
        smoke(x, y, RNG.uniform(22, 46), coll)
    for x in (86, 88, 91):
        flame(x, 191, 4, coll)


def fissures(coll):
    for x, y, length in [(-42, 260, 16), (72, 332, 11)]:
        pts = [(x + i * .8 + math.sin(i * 1.6), y + i * 2, hill(x + i * .8, y + i * 2) + .08)
               for i in range(round(length / 2))]
        for a, b in zip(pts, pts[1:]):
            o = beam('narrow_interior_supernatural_seam', a, b, .10, EMBER, coll)
            o['ReviewFireOnly'] = True


def camera(name, eye, target, lens=40, ortho=None):
    d = bpy.data.cameras.new(name); o = bpy.data.objects.new(name, d); REVIEW.objects.link(o)
    o.location = eye; o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
    d.lens = lens; d.clip_end = 5000
    if ortho:
        d.type = 'ORTHO'; d.ortho_scale = ortho
    return o


def views():
    cameras = [
        camera('01_broad_overview', (610, -770, 475), (0, 10, 25), 43),
        camera('02_top_progression', (0, 0, 1200), (0, 0, 0), ortho=720),
        camera('03_baseline_player_eye', (road_x(-350), -350, hill(road_x(-350), -350) + 5),
               (8, -80, hill(8, -80) + 9), 25),
        camera('04_opening_edge', (104, -349, hill(104, -349) + 5), (-54, -172, hill(-54, -172) + 8), 28),
        camera('05_mid_plains_active_burn', (28, -78, hill(28, -78) + 5), (-30, 84, hill(-30, 84) + 8), 28),
        camera('06_interior_edge', (5, 163, hill(5, 163) + 5), (0, 382, hill(0, 382) + 8), 28),
        camera('07_raised_gradient', (300, -450, 185), (-12, 18, 24), 35),
    ]
    SCENE.camera = cameras[0]
    for cam in cameras:
        SCENE.render.resolution_x, SCENE.render.resolution_y = (900, 1100) if cam.name.startswith('02') else (1440, 900)
        SCENE.camera = cam; SCENE.render.filepath = str(OUT / (cam.name + '.png'))
        bpy.ops.render.render(write_still=True)
        print('RENDERED', cam.name, flush=True)
    SCENE.camera = cameras[6]
    hidden = [o for o in SCENE.objects if o.get('ReviewFireOnly')]
    for o in hidden:
        o.hide_render = True
    SCENE.render.filepath = str(OUT / '08_glow_removed.png')
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    SCENE.camera = cameras[0]
    REPORT['evidence'] = [str(OUT / (c.name + '.png')) for c in cameras] + [str(OUT / '08_glow_removed.png')]


def main():
    global SCENE, REVIEW, GROUND, GRASS, LEAF, WOOD, CHARWOOD, STONE, ROAD, FIRE, FIRECORE, EMBER, SMOKE
    OUT.mkdir(parents=True, exist_ok=True)
    # Fresh scene; no old terrain or composition is inherited.
    SCENE = bpy.data.scenes.new('Emberfall_Area_I_Burned_Plains')
    bpy.context.window.scene = SCENE
    SCENE.unit_settings.system = 'METRIC'; SCENE.unit_settings.scale_length = 1
    root = collection('AREA_I_FOUNDATION_REVIEW_ONLY')
    play = collection('Playable_3_STUDIES', root)
    scenery = collection('Surrounding_Continuous_Grassland_REVIEW_ONLY', root)
    flora = collection('Flora_NONSOLID', root)
    props = collection('Countryside_SOLID_DECOR', root)
    fx = collection('ActiveBurn_NONSOLID_REVIEW_ONLY', root)
    REVIEW = collection('Cameras_Lights_Scale_REVIEW_ONLY')
    library = collection('Compatible_Flora_SOURCE_ONLY'); library.hide_render = True; library.hide_viewport = True
    with bpy.data.libraries.load(str(INPUT), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ('prop_healthy_ash_rosette_spread',
                       'prop_early_ash_rosette_curled', 'prop_partial_ash_rosette_spread')]
    for o in dst.objects:
        library.objects.link(o)
    REPORT['reused_flora_sources'] = [o.name for o in dst.objects]
    GROUND = []
    for state, base in [('green', (.16, .235, .045)), ('stressed', (.29, .235, .075)),
                        ('fresh_char', (.045, .037, .030))]:
        for i in range(3):
            GROUND.append(material(state + str(i), tuple(v * (.92 + .08 * i) for v in base)))
    GRASS = [material('grass_green', (.21, .34, .055)), material('grass_olive', (.31, .37, .07)),
             material('grass_straw', (.49, .40, .17)), material('grass_singed', (.32, .23, .075)),
             material('grass_black_stubble', (.018, .016, .012)), material('grass_burned_brown', (.084, .060, .029))]
    LEAF = [material('canopy_green', (.13, .27, .042)), material('canopy_stressed', (.36, .32, .072)),
            material('canopy_singed', (.12, .082, .027))]
    WOOD = material('field_timber', (.17, .09, .033)); CHARWOOD = material('charred_timber', (.022, .018, .014))
    STONE = material('field_stone', (.26, .255, .21))
    ROAD = [material('old_soil_track', (.20, .135, .07)),
            material('heat_stressed_soil_track', (.16, .10, .047)),
            material('charred_soil_track', (.06, .041, .025))]
    FIRE = material('flame_orange', (1, .135, .006), 2.5)
    FIRECORE = material('flame_core', (1, .46, .025), 3)
    EMBER = material('restrained_ember', (.8, .065, .005), 1.5); SMOKE = smoke_material()
    chunks, total = [], Counter()
    for name, y in SPECS:
        c = collection(name, play)
        o, counts = terrain('chunk_' + name, (-128, 128, y - 128, y + 128), c, y)
        chunks.append(o); total.update(counts)
        o['Role'] = 'AREA_I_VISUAL_STUDY'; o['SocketWidthStuds'] = 24
        o['SocketNorthLocalZ'] = hill(0, y + 128) - hill(0, y)
        o['SocketSouthLocalZ'] = hill(0, y - 128) - hill(0, y)
        REPORT[name] = {'surface_balance_percent': {['green', 'stressed', 'charred'][k]: round(100 * v / sum(counts.values()), 2) for k, v in counts.items()},
                        'center_datum': hill(0, y)}
    land_total = total.copy()
    for name, bounds in [('west_fields', (-520, -128, -744, 744)), ('east_fields', (128, 520, -744, 744)),
                         ('entry_continuation', (-128, 128, -744, -384)), ('interior_continuation', (-128, 128, 384, 744))]:
        _, counts = terrain(name, bounds, scenery)
        land_total.update(counts)
    grasses(flora, 29000, (-128, 128, -384, 384), 'playable_grass_states')
    grasses(scenery, 41000, (-500, 500, -690, 690), 'surrounding_grass_states')
    road(props); wall(props)
    fence([(x, -265 + .17 * x) for x in range(-115, -20, 10)], props)
    fence([(x, 95 + .14 * x) for x in range(34, 125, 10)], props, True)
    fence([(-116 + .08 * y, y) for y in range(146, 330, 13)], props, True)
    fence([(x, 367) for x in range(38, 118, 10)], props, True)
    # A field gate ahead, milestone and small isolated footing; no settlement.
    for x in (-10, 10):
        beam('interior_field_gate_post', (x, 356, hill(x, 356)), (x, 356, hill(x, 356) + 5), .7, STONE, props)
    blob('old_road_milestone', (17, -278, hill(17, -278) + 1.9), (1.1, .8, 2.1), STONE, props)
    for x, y in [(-56, 282), (-53, 282), (-50, 282), (-56, 285), (-56, 288)]:
        blob('isolated_countryside_footing', (x, y, hill(x, y) + .7), (1.6, 1.1, .8), STONE, props)
    for x, y, h in [(84, -293, 30), (-89, -318, 25), (108, -176, 27), (-47, -152, 26),
                    (-104, 116, 33), (87, 190, 27), (-61, 297, 25), (105, 322, 23),
                    (-91, -264, 24), (-69, -239, 19), (56, -45, 26), (-53, 23, 30),
                    (102, 108, 22), (-86, 223, 19), (56, 299, 23)]:
        tree(x, y, h, flora)
    for _ in range(66):
        x = RNG.choice([-1, 1]) * RNG.uniform(148, 475); y = RNG.uniform(-620, 650)
        tree(x, y, RNG.uniform(17, 36), scenery)
    # A few reused temperate-compatible small flora in protected/drying pockets.
    for i in range(22):
        x = RNG.uniform(52, 104); y = RNG.uniform(-320, -195)
        sources = {o.name: o for o in dst.objects}
        source = sources['prop_healthy_ash_rosette_spread' if burn_state(x, y) == 0 else 'prop_early_ash_rosette_curled']
        o = source.copy(); o.data = source.data.copy(); flora.objects.link(o)
        o.name = 'reused_temperate_understory'; o.parent = None
        o.location = (x, y, hill(x, y)); o.scale = (.55, .55, .55)
        # Preserve source data; review instances use ordinary temperate colors.
        for slot in range(len(o.data.materials)):
            o.data.materials[slot] = GRASS[0 if burn_state(x, y) == 0 else 2]
        o.hide_render = False; o.hide_viewport = False
    flower = material('tiny_meadow_flowers', (.75, .64, .27))
    for _ in range(100):
        x = RNG.uniform(52, 111); y = RNG.uniform(-333, -205)
        if burn_state(x, y) == 0:
            blob('surviving_meadow_flower', (x, y, hill(x, y) + .5), (.15, .15, .10), flower, flora)
    fire_fronts(fx); fissures(fx)
    # Sparse ordinary field stones, never pillars or a repeated geological garden.
    for x, y in [(-96, -210), (61, -145), (-57, 88), (98, 228), (-163, -58), (220, 284)]:
        blob('ordinary_field_rock', (x, y, hill(x, y) + .7), (2.6, 1.8, 1.4), STONE, props)
    world = bpy.data.worlds.new('Burned_Plains_Cool_Ambient'); SCENE.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.32, .38, .45, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .5
    sun_data = bpy.data.lights.new('late_overcast_sun', 'SUN'); sun_data.energy = 2.0; sun_data.angle = .18
    sun = bpy.data.objects.new('late_overcast_sun', sun_data); REVIEW.objects.link(sun)
    sun.rotation_euler = (.55, -.55, -.65)
    SCENE.render.engine = 'BLENDER_EEVEE'
    SCENE.render.resolution_x = 1440; SCENE.render.resolution_y = 900; SCENE.render.resolution_percentage = 100
    SCENE.render.image_settings.file_format = 'PNG'
    SCENE.view_settings.view_transform = 'AgX'
    SCENE['README'] = 'AREA I FOUNDATION ONLY. Player advances +Y; fire spreads -Y. Three 256-stud studies, 24-stud mouths, 56-stud ascent. No production collision/export. Input_DesignReset retains exact old live scene.'
    SCENE['Reference'] = 'docs/design/emberfall/EMBERFALL_REFERENCE_01.png PRIMARY; docs/biomes/EMBERFALL.md'
    bpy.context.view_layer.update()
    REPORT['aggregate_playable_surface_percent'] = {['green', 'stressed', 'charred'][k]: round(100 * v / sum(total.values()), 2) for k, v in total.items()}
    REPORT['whole_land_surface_percent'] = {['green', 'stressed', 'charred'][k]: round(100 * v / sum(land_total.values()), 2) for k, v in land_total.items()}
    REPORT['ascent_studs'] = hill(0, 384) - hill(0, -384)
    # A small exact authored-join check; no exhaustive matrix/traversal tests.
    joins = []
    for a, b in zip(chunks, chunks[1:]):
        va = {round(v.co.x, 3): v.co.z + a.location.z for v in a.data.vertices[:a['SurfaceVertexCount']] if abs(v.co.y - 128) < .001}
        vb = {round(v.co.x, 3): v.co.z + b.location.z for v in b.data.vertices[:b['SurfaceVertexCount']] if abs(v.co.y + 128) < .001}
        gap = max(abs(va[x] - vb[x]) for x in va)
        assert gap < .001
        joins.append({'pair': [a.name, b.name], 'stations': len(va), 'max_gap_stud': gap})
    REPORT['authored_joins'] = joins
    REPORT['objects'] = len(SCENE.objects)
    REPORT['mesh_triangles'] = 0
    for o in SCENE.objects:
        if o.type == 'MESH':
            o.data.calc_loop_triangles(); REPORT['mesh_triangles'] += len(o.data.loop_triangles)
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    views()
    REPORT['objects'] = len(SCENE.objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    for p in (HERE / 'burned_plains_report.json', OUT / 'burned_plains_report.json'):
        p.write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('BURNED_PLAINS_DONE', json.dumps(REPORT['aggregate_playable_surface_percent']), flush=True)


if __name__ == '__main__':
    main()
