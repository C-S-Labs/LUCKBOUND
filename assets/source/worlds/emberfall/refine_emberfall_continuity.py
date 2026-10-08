"""Focused edits of CURRENT saved Emberfall: continuity, footing and burning flora.

Protected launcher only; never regenerate architecture or export production assets.
"""
import bpy
import bmesh
import json
import math
import shutil
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
MAIN = OUT/'EmberfallPrototype.blend'
INPUT = OUT/'Input_Continuity.blend'
IMAGES = OUT/'ContinuityReview'
REPORT = {}


def load_helpers():
    import importlib.util
    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, HERE/filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return load('continuity_arch', 'revise_emberfall_architecture.py'), load('continuity_identity', 'refine_emberfall_identity.py')


def delta(name, x, y):
    fade = arch.interior(x, y)
    if name == arch.NAMES[1]:
        return fade*(arch.hill(x, y, 70, -27, 18, 58, 21, 4)-arch.hill(x, y, 65, -24, 29, 67, 7)) * arch.smooth(12, 36, math.hypot(x, y))
    if name == arch.NAMES[2]:
        return fade*(arch.hill(x, y, -64, 28, 27, 46, 19, 4)-arch.hill(x, y, -61, 27, 38, 57, 5)) * arch.smooth(29, 48, math.hypot(x, y))
    if name == arch.NAMES[3]:
        return fade*(arch.hill(x, y, 73, -55, 25, 25, 12)-arch.hill(x, y, 69, -53, 34, 37, 3)) * arch.smooth(12, 40, math.hypot(x, y))
    if name in (arch.SCENERY[3], arch.SCENERY[4], arch.SCENERY[6]):
        # Deliberate fault blocks, not random border sculpting. Asymmetrical broad
        # sectors with short steep rim steps and a retained readable deep void.
        cx = 0 if name == arch.SCENERY[4] else 12 if name == arch.SCENERY[3] else 28
        span = 24 if name == arch.SCENERY[4] else 65 if name == arch.SCENERY[3] else 28
        rim = max(0, 1-abs(abs(x-cx)-span)/23)
        block = 4 if y < -40 else -7 if y < -8 else 6 if y < 32 else -3
        return fade*rim*block*arch.smooth(-95, -70, y)*(1-arch.smooth(68, 100, y))
    return 0


def canonical(ob, x, y):
    parent = ob.parent
    if parent and parent.get('AssetCollection') in arch.SCENERY:
        a = math.radians(parent.get('AuthoredQuarterTurn', 0))
        return math.cos(a)*x+math.sin(a)*y, -math.sin(a)*x+math.cos(a)*y
    return x, y


def home(ob):
    if ob.parent and ob.parent.get('AssetCollection'):
        return ob.parent['AssetCollection']
    for name in arch.NAMES+arch.SCENERY:
        if ob in list(bpy.data.collections[name].all_objects):
            return name
    return None


def adjust_ground():
    seen = set()
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH':
            continue
        name = home(ob)
        if not name:
            continue
        if ob.get('LibraryAsset'):
            x, y = canonical(ob, ob.location.x, ob.location.y)
            ob.location.z += delta(name, x, y)
            continue
        if ob.data.as_pointer() in seen or ob.get('ReviewOnlyVolume'):
            continue
        seen.add(ob.data.as_pointer())
        terrain_ids = {k for p in ob.data.polygons[:ob['TerrainFaceCount']] for k in p.vertices} if ob.get('TerrainFaceCount') else None
        for v in ob.data.vertices:
            x, y = canonical(ob, v.co.x+ob.location.x, v.co.y+ob.location.y)
            dz = delta(name, x, y)
            # Seat the retained modules/details too, preserving their local shape.
            v.co.z += dz if terrain_ids is None or v.index in terrain_ids else delta(name, x, y)
        ob.data.update()
    REPORT['playable_low_area_revisions'] = {
        arch.NAMES[0]: 'Keep open ash apron; no authored negative pocket.',
        arch.NAMES[1]: 'Eastern 21-stud narrow hot cut replaced with broad ~7-stud channel (58-wide characteristic span). Retain 56-stud ascent.',
        arch.NAMES[2]: 'Western 19-stud bowl replaced with ~5-stud broad peripheral basin (76-wide characteristic span); central combat hub untouched.',
        arch.NAMES[3]: 'Small 12-stud southeast pocket reduced to broad ~3-stud scoop (68-wide characteristic span).',
        arch.NAMES[4]: 'Retain broad raised end shelf; no authored negative pocket.'}


def recolor(ob, stage):
    attr = ob.data.color_attributes.get('EmberGroundTint')
    if not attr:
        return
    for p in ob.data.polygons[:ob['TerrainFaceCount']]:
        for li in p.loop_indices:
            v = ob.data.vertices[ob.data.loops[li].vertex_index].co
            # World-space flow for review layouts; symmetric boundary stations in
            # independent assets. Color reaches the edge, unlike the old fadeout.
            w = ob.matrix_world @ v
            flow = flow_field(ob, v, w)
            inward = arch.smooth(0, 65, min(128-abs(v.x), 128-abs(v.y)))
            low = (.023, .03, .034)
            ash = (.13, .112, .075)
            amount = (.12+.38*flow)*(1-stage*.12*inward)
            attr.data[li].color = (*(a+(b-a)*amount for a, b in zip(low, ash)), 1)


def flow_field(ob, local, world):
    if ob.parent and ob.parent.get('AssetCollection'):
        return .5+.5*math.sin((world.x+world.y*.38)*.039+1.1*math.sin(world.y*.015))
    # Independent assets match opposing borders and quarter-turn rotations.
    return .5+.25*(math.cos(local.x*math.tau/256)+math.cos(local.y*math.tau/256))


def tube(vs, fs, mids, pts, radius, mat):
    start = len(vs)
    pts = [Vector(p) for p in pts]
    for k, p in enumerate(pts):
        tangent = (pts[min(k+1, len(pts)-1)]-pts[max(0, k-1)]).normalized()
        side = tangent.cross(Vector((0, 0, 1)))
        if side.length < .01:
            side = tangent.cross(Vector((0, 1, 0)))
        side.normalize()
        up = tangent.cross(side).normalized()
        r = radius*(1-.8*k/(len(pts)-1))
        for j in range(6):
            vs.append(tuple(p+r*(side*math.cos(j*math.tau/6)+up*math.sin(j*math.tau/6))))
    for k in range(len(pts)-1):
        for j in range(6):
            fs.append((start+k*6+j, start+k*6+(j+1)%6, start+(k+1)*6+(j+1)%6, start+(k+1)*6+j))
            mids.append(mat)
    fs += [tuple(start+j for j in reversed(range(6))), tuple(start+(len(pts)-1)*6+j for j in range(6))]
    mids += [mat, mat]


def continuity(group, stage):
    ground = bpy.data.objects[group.name]
    tree = art.surface_tree(ground)
    collection = arch.coll(group.name+'_BorderFlow', group)
    vs, fs, mids = [], [], []
    # A common edge vocabulary continues ash/crust through all rotations.
    # Cut surfaces at the exact edge; no bridging object depends on a neighbor.
    for side in range(4):
        def xy(t, u):
            return [(t, 128-u), (128-u, t), (t, -128+u), (-128+u, t)][side]
        for j, center in enumerate((-77, 46)):
            start = len(vs)
            for u in (0, 8, 16, 24, 36, 48, 64):
                drift = 4*math.sin(u*.065)*(1 if j == 0 else -1)
                width = (5 if j == 0 else 3.2)*(1+.35*math.sin(u*.09))*(1-arch.smooth(44, 64, u))
                for sign in (-1, 1):
                    x, y = xy(center+drift+sign*width, u)
                    vs.append((x, y, art.floor(tree, max(-127.9999, min(127.9999, x)), max(-127.9999, min(127.9999, y)))+.055))
            for row in range(6):
                a = start+row*2
                fs.extend([(a, a+1, a+3), (a, a+3, a+2)])
                mids.extend([0 if j == 0 else 1]*2)
        # Three offset inset fragments carry the broken skin toward the seam.
        # Tiny relief, kept outside the 56-wide connection mouth.
        for j, (t, u) in enumerate(((-58, 12), (61, 30), (-69, 46))):
            start = len(vs)
            outline = [(-4, -3), (1, -4), (5, -1), (2, 3), (-2, 2)]
            for a, b in outline:
                x, y = xy(t+a, u+b)
                vs.append((x, y, art.floor(tree, x, y)+.08+(j%2)*.09))
            fs.append(tuple(start+k for k in range(5)))
            mids.append(1)
    ob = arch.mesh('prop_'+group.name+'_continuous_ash_crust', vs, fs, collection, [DUST, CRUST])
    ob.parent = art.root(group)
    ob['solid'] = False
    ob['SeamDetail'] = 'paired flush ash/crust ribbons; 0.055 stud edge lift; original terrain unchanged'
    plants = ['prop_surviving_ash_rosette', 'prop_partial_rosette_30', 'prop_partial_rosette_50', 'prop_partial_rosette_70']
    for j, (x, y) in enumerate([(-70, 115), (113, 69), (64, -114), (-113, -61)]):
        src = bpy.data.objects[plants[min(stage+int(j == 1), 3)]]
        ob = bpy.data.objects.new('prop_'+group.name+'_handoff_growth', src.data)
        collection.objects.link(ob)
        ob.parent = art.root(group)
        ob.location = (x, y, art.floor(tree, x, y)+.02)
        ob.scale = (.75,)*3
        ob.rotation_euler.z = j*1.7
        ob['LibraryAsset'] = src.name
        ob['solid'] = False
    art.study = arch
    art.propagate(group, collection)


def remap(old_data, new_data):
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.data == old_data:
            ob.data = new_data


def refine_plant(ob, ratio, rosette=True):
    data = ob.data.copy()
    bm = bmesh.new()
    bm.from_mesh(data)
    # Additional support topology only on existing tissue; lets the creeping
    # front vary inside a leaf rather than recoloring entire leaf cards.
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    tissue_slot = len(data.materials)
    data.materials.append(TISSUE)
    def score(p):
        return p.x+.48*math.sin(p.y*3.1+p.z*2.7)+.24*math.sin(p.y*6.5-p.z*4.1)-.3*(2-p.z)
    vals = sorted(score(v.co) for v in data.vertices)
    threshold = vals[min(len(vals)-1, round(len(vals)*ratio))]
    color = data.color_attributes.new(name='TakeoverTissue', type='FLOAT_COLOR', domain='CORNER')
    for v in data.vertices:
        active = 1-arch.smooth(threshold-.36, threshold+.36, score(v.co))
        radial = math.hypot(v.co.x, v.co.y)
        # Singed tips sag/curl asymmetrically, surviving tissue remains recognizable.
        if rosette:
            v.co.z += active*(.18*math.sin(radial*2.4+v.co.y)-.18)*arch.smooth(1.4, 2.8, radial)
            v.co.x += active*.12*math.sin(radial*2.6)
    for p in data.polygons:
        p.material_index = tissue_slot
        p.use_smooth = True
        for li in p.loop_indices:
            v = data.vertices[data.loops[li].vertex_index]
            active = 1-arch.smooth(threshold-.36, threshold+.36, score(v.co))
            pale, brown, black = (.50, .49, .052), (.12, .065, .019), (.008, .009, .009)
            a, b, t = (pale, brown, active*2) if active < .5 else (brown, black, (active-.5)*2)
            color.data[li].color = (*(x+(y-x)*t for x, y in zip(a, b)), 1)
    vs = [tuple(v.co) for v in data.vertices]
    fs = [tuple(p.vertices) for p in data.polygons]
    mids = [p.material_index for p in data.polygons]
    original_colors = [tuple(c.color) for c in color.data]
    black_slot = len(data.materials)
    data.materials.append(INFECTED)
    heat_slot = len(data.materials)
    data.materials.append(HEAT)
    # Unequal invasive tendrils break through the core and creep along retained
    # tissue. Three warm hairlines under thicker black growth, not a flame carpet.
    for j, angle in enumerate((1.8, 2.65, 3.65, 4.35)):
        length = 2.5 if rosette else 1.6
        pts = []
        for t in (0, .2, .4, .6, .8, 1):
            r = length*t
            a = angle+.14*math.sin(t*7+j)
            pts.append((math.cos(a)*r, math.sin(a)*r, .30+2.1*math.sin(t*1.9)+.18))
        tube(vs, fs, mids, pts, .075, black_slot)
        tube(vs, fs, mids, [(x+.035, y-.045, z+.035) for x, y, z in pts[1:5]], .023, heat_slot)
        p = Vector(pts[3])
        tube(vs, fs, mids, [p, p+Vector((.21, -.16, .28)), p+Vector((.15, -.32, .58))], .08, black_slot)
    # Small recessed heated core surrounded by black emerging roots.
    for j in range(3):
        a = j*2.399
        tube(vs, fs, mids, [(.16*math.cos(a), .16*math.sin(a), .1), (.22*math.cos(a+.3), .22*math.sin(a+.3), .55), (.11*math.cos(a), .11*math.sin(a), .95)], .035, heat_slot)
    mats = list(data.materials)
    rebuilt = bpy.data.meshes.new(ob.name+'_creeping_tissue')
    rebuilt.from_pydata(vs, [], fs)
    for mat in mats:
        rebuilt.materials.append(mat)
    for p, mi in zip(rebuilt.polygons, mids):
        p.material_index = mi
        p.use_smooth = True
    attr = rebuilt.color_attributes.new(name='TakeoverTissue', type='FLOAT_COLOR', domain='CORNER')
    for k, c in enumerate(attr.data):
        c.color = original_colors[k] if k < len(original_colors) else (.008, .009, .009, 1)
    remap(ob.data, rebuilt)
    ob['TakeoverProcess'] = 'irregular brown singe front, curled tissue, black emerging roots, dim ember veins'
    REPORT.setdefault('flora', {})[ob.name] = {'target_state': ratio, 'vertices': len(rebuilt.vertices), 'triangles': sum(len(p.vertices)-2 for p in rebuilt.polygons)}


def crust_integration():
    seen = set()
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or '_fractured_crust' not in ob.name or ob.data.as_pointer() in seen:
            continue
        seen.add(ob.data.as_pointer())
        group_name = home(ob)
        terrain = next(o for o in ob.parent.users_collection[0].all_objects if o.get('TerrainFaceCount')) if ob.parent else None
        if not terrain:
            terrain = bpy.data.objects[group_name]
        tree = art.surface_tree(terrain)
        for comp in arch.components(ob.data):
            pts = [ob.data.vertices[k].co for k in comp]
            cx = sum(p.x for p in pts)/len(pts)
            cy = sum(p.y for p in pts)/len(pts)
            for k in comp:
                p = ob.data.vertices[k].co
                floor_z = art.floor(tree, p.x, p.y)
                relative = p.z-floor_z
                # Bury half the plate rim, retain a restrained lifted tearing lip.
                gain = arch.smooth(-8, 8, (p.x-cx)*.55+(p.y-cy)*.8)
                lift = -.12+gain*(.55 if abs(cx) < 28 else 1.35)
                p.z = floor_z+min(max(relative*.45, -.7), lift)
                # Offset/notch only upper support vertices; avoids uniform bevel rims.
                if relative > 0:
                    p.x += .65*math.sin((p.y-cy)*.31)
        ob.data.update()


def collapse_remnants(group):
    terrain = bpy.data.objects[group.name]
    tree = art.surface_tree(terrain)
    collection = arch.coll(group.name+'_CollapseRemnants', group)
    vs, fs, mids = [], [], []
    span = 25 if group.name == arch.SCENERY[4] else 63 if group.name == arch.SCENERY[3] else 27
    center = 0 if group.name == arch.SCENERY[4] else 12 if group.name == arch.SCENERY[3] else 28
    for j, y in enumerate((-55, -15, 30, 58)):
        sign = -1 if j%2 else 1
        cx = center+sign*span
        cy = y
        start = len(vs)
        outline = [(-8, -9), (8, -6), (10, 0), (4, 3), (7, 9), (-7, 11), (-11, 1)]
        center_z = art.floor(tree, cx, cy)
        for ring in range(2):
            for x, yy in outline:
                px, py = cx+x, cy+yy
                base = art.floor(tree, px, py)
                z = base-.7 if ring == 0 else center_z+1.2+(px-cx)*sign*.27+(py-cy)*.08
                vs.append((px, py, z))
        fs.append(tuple(start+7+k for k in range(7)))
        mids.append(0)
        for k in range(7):
            fs.append((start+k, start+(k+1)%7, start+7+(k+1)%7, start+7+k))
            mids.append(1 if k%3 else 2)
        # Smaller fallen remnant slopes into the failing floor.
        x = cx-sign*12
        zz = art.floor(tree, x, cy+14)
        s = len(vs)
        vs += [(x-6, cy+11, zz), (x+6, cy+9, zz+1), (x+3, cy+18, zz+2.5), (x-4, cy+21, zz-1)]
        fs.append((s, s+1, s+2, s+3)); mids.append(0)
    ob = arch.mesh('prop_'+group.name+'_undermined_shelves', vs, fs, collection, [CRUST, SCORCH, HEAT])
    ob.parent = art.root(group)
    ob['solid'] = False
    for p, m in zip(ob.data.polygons, mids):
        p.material_index = m
    art.propagate(group, collection)


def render():
    scene = bpy.data.scenes['Architecture_A']
    bpy.context.window.scene = scene
    for ob in list(bpy.data.objects):
        if ob.type == 'CAMERA' and ob.name.startswith('continuity_'):
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.view_layer.update()
    cameras = next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 730
    scene.cycles.samples = 24
    views = [('overview', (650, -760, 560), (40, 125, 34), 40),
             ('join_player', (-5, -150, 4.5), (25, -89, 10), 28),
             ('join_oblique', (-92, -151, 8), (6, -128, 3), 36),
             ('join_top', (0, -128, 230), (0, -128, 0), 42),
             ('raised_lookback', (39, 176, 70), (-25, -145, 6), 30),
             ('combat_basin', (-21, 236, 66), (-63, 284, 51), 36),
             ('ascent_channel', (30, -67, arch.level(-67)+9), (68, -15, arch.level(-15)-3), 36),
             ('crust_close', (-31, 258, 65), (-58, 294, 57), 40)]
    # Resolve actual scenery instance rather than guessing which seed chose it.
    hole = next(o for o in scene.objects if o.get('TerrainFaceCount') and o.parent and o.parent.get('AssetCollection') == arch.SCENERY[4])
    center = hole.matrix_world @ Vector((0, 0, -10))
    views.append(('collapse_close', tuple(center+Vector((125, -100, 100))), tuple(center), 40))
    plant = next(o for o in scene.objects if o.name.startswith('prop_path_column_pass_takeover_50'))
    center = plant.matrix_world.translation+Vector((0, 0, 1.8))
    views.append(('flora_50_close', tuple(center+Vector((6, -9, 6))), tuple(center), 50))
    for name, eye, target, lens in views:
        cam = arch.camera('continuity_'+name, eye, target, cameras, lens)
        scene.camera = cam
        scene.render.filepath = str(IMAGES/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    gallery = bpy.data.scenes['FloraSpectrum_REVIEW_ONLY']
    bpy.context.window.scene = gallery
    gallery.cycles.samples = 24
    for name, camname in [('flora_progression', 'flora_spectrum'), ('flora_50_gallery', 'flora_50_percent')]:
        gallery.camera = bpy.data.objects[camname]
        gallery.render.filepath = str(IMAGES/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    bpy.context.window.scene = scene
    scene.camera = bpy.data.objects['continuity_overview']


def finish_flow():
    """Local review corrections of the saved pass, without restarting any art."""
    global REPORT
    assert not bpy.context.scene.get('ContinuityTintFinal'), 'Final pass already saved; use review mode.'
    REPORT = json.loads((HERE/'continuity_technical_report.json').read_text(encoding='utf8'))
    blend = art.make_material('Ember_BorderSurfaceBlend', (.04, .045, .04), .91)
    color = blend.node_tree.nodes.new('ShaderNodeVertexColor')
    color.layer_name = 'BorderFlowTint'
    blend.node_tree.links.new(color.outputs['Color'], blend.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    seen = set()
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or ob.data.as_pointer() in seen:
            continue
        seen.add(ob.data.as_pointer())
        if '_continuous_ash_crust' in ob.name:
            ob.data.materials[0] = blend
            attr = ob.data.color_attributes.new(name='BorderFlowTint', type='FLOAT_COLOR', domain='CORNER')
            for p in ob.data.polygons:
                for li in p.loop_indices:
                    v = ob.data.vertices[ob.data.loops[li].vertex_index].co
                    w = ob.matrix_world @ v
                    flow = .5+.5*math.sin((w.x+w.y*.38)*.039+1.1*math.sin(w.y*.015))
                    amount = .12+.38*flow
                    attr.data[li].color = (*(a+(b-a)*amount+.009 for a, b in zip((.023, .03, .034), (.13, .112, .075))), 1)
            ob['SeamDetail'] = 'ground-colored flush ash/crust continuation; light relief; nonsolid'
        if '_undermined_shelves' in ob.name:
            terrain = next(o for o in ob.parent.users_collection[0].all_objects if o.get('TerrainFaceCount')) if ob.parent else bpy.data.objects[home(ob)]
            tree = art.surface_tree(terrain)
            for v in ob.data.vertices:
                floor_z = art.floor(tree, v.co.x, v.co.y)
                v.co.z = min(v.co.z, floor_z+2.2)
            for p in ob.data.polygons:
                if p.material_index == 2:
                    p.material_index = 1
        if '_fractured_crust' in ob.name:
            # Break the regular bevel picture-frame, notch selected corners, and
            # divide the broad upper skin into unequal triangular fracture facets.
            for comp in arch.components(ob.data):
                if len(comp) < 18:
                    continue
                pts = [ob.data.vertices[k].co for k in comp]
                cx, cy = sum(p.x for p in pts)/len(pts), sum(p.y for p in pts)/len(pts)
                low = min(comp)
                for k in comp:
                    if (k-low)%6 in (1, 4):
                        p = ob.data.vertices[k].co
                        factor = .18 if (k-low)%6 == 1 else .08
                        p.x += (cx-p.x)*factor
                        p.y += (cy-p.y)*factor
            for p in ob.data.polygons:
                if len(p.vertices) == 4 and p.index%6 not in (1, 2):
                    p.material_index = 0
            bm = bmesh.new(); bm.from_mesh(ob.data)
            tops = [f for f in bm.faces if len(f.verts) == 6]
            result = bmesh.ops.poke(bm, faces=tops, offset=0, use_relative_offset=False)
            for j, v in enumerate(result['verts']):
                v.co.x += 1.2*math.sin(j*2.3)
                v.co.y += 1.8*math.cos(j*1.7)
                v.co.z += .11
            bm.to_mesh(ob.data); bm.free()
    # The charred derivatives do not need support subdivision on flat dark
    # regions. Dissolve only those redundant coplanar edges; original species exact.
    for n in ('prop_charred_ember_rose_active_tissue', 'prop_charred_thorn_pod_active_tissue'):
        data = bpy.data.objects[n].data
        bm = bmesh.new(); bm.from_mesh(data)
        bmesh.ops.dissolve_limit(bm, angle_limit=.002, verts=list(bm.verts), edges=list(bm.edges), delimit={'MATERIAL'})
        bm.to_mesh(data); bm.free()
    REPORT['review_corrections'] = 'Ash ribbon contrast blended to ground; regular plate rim broken/notched; collapse remnant side heights capped at 2.2 studs; redundant planar charred subdivision dissolved.'
    REPORT['low_area_spot_checks'] = {}
    for n, cx, cy in [(arch.NAMES[1], 65, -24), (arch.NAMES[2], -61, 27), (arch.NAMES[3], 69, -53)]:
        ground = bpy.data.objects[n]
        tree = art.surface_tree(ground)
        readings = []
        for x in (cx-16, cx, cx+16):
            for y in (cy-16, cy, cy+16):
                hit, normal, _, _ = tree.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)))
                base = arch.level(y)-28 if n == arch.NAMES[1] else 0
                readings.append({'xy': [x, y], 'height': hit.z, 'relative_to_route_datum': hit.z-base, 'slope_degrees': math.degrees(math.acos(min(1, abs(normal.z))))})
        REPORT['low_area_spot_checks'][n] = readings
    REPORT['assets'] = {n: arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    render()
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after_saved_readback'] = {s.name: art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['materials'] = len(bpy.data.materials)
    (HERE/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    (IMAGES/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('CONTINUITY_FINISHED', REPORT['after_saved_readback'])


def final_tint():
    global REPORT
    REPORT = json.loads((HERE/'continuity_technical_report.json').read_text(encoding='utf8'))
    assert not bpy.context.scene.get('ContinuityTintFinal'), 'Final tint already saved.'
    stages = [0, 1, 1, 1, 2, 0, 1, 2, 2, 2, 0, 2, 1]
    # Geometry stays identical. Review layouts need independent color layers so
    # a shared source mesh cannot accidentally bake its local coordinates over
    # every placement. This is offline art fitting, not runtime scenery code.
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.parent and ob.parent.get('AssetCollection') and (ob.get('TerrainFaceCount') or '_continuous_ash_crust' in ob.name):
            ob.data = ob.data.copy()
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if ob.get('TerrainFaceCount'):
            recolor(ob, stages[(arch.NAMES+arch.SCENERY).index(home(ob))])
        if '_continuous_ash_crust' in ob.name:
            attr = ob.data.color_attributes.get('BorderFlowTint')
            for p in ob.data.polygons:
                for li in p.loop_indices:
                    v = ob.data.vertices[ob.data.loops[li].vertex_index].co
                    flow = flow_field(ob, v, ob.matrix_world @ v)
                    amount = .12+.38*flow
                    attr.data[li].color = (*(a+(b-a)*amount+.009 for a, b in zip((.023, .03, .034), (.13, .112, .075))), 1)
    for s in bpy.data.scenes:
        s['ContinuityTintFinal'] = True
    render()
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after_saved_readback'] = {s.name: art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['assets'] = {n: arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    REPORT['source_max_mesh_triangles'] = max(t for g in REPORT['assets'].values() for t in g['mesh_triangles'].values())
    REPORT['surface_continuity'] = 'Rotation-compatible independent boundary tint; world-space color flow on existing A/B/C review copies. No border height deformation.'
    REPORT['materials'] = len(bpy.data.materials)
    (HERE/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    (IMAGES/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('CONTINUITY_FINAL_TINT_SAVED', REPORT['after_saved_readback'])


def main():
    global arch, art, DUST, CRUST, SCORCH, INFECTED, HEAT, TISSUE
    IMAGES.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        shutil.copy2(MAIN, INPUT)
    # Always CURRENT input; the backup is rollback evidence, never a regeneration recipe.
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    arch, art = load_helpers()
    art.study = arch
    if '--low-review' in __import__('sys').argv:
        scene = bpy.data.scenes['Architecture_A']
        bpy.context.window.scene = scene
        cameras = next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
        scene.camera = arch.camera('review_clear_ascent_channel', (116, -54, arch.level(-54)+55), (83, -24, arch.level(-24)-2), cameras, 40)
        scene.render.resolution_x, scene.render.resolution_y = 1100, 730
        scene.cycles.samples = 24
        scene.render.filepath = str(IMAGES/'ascent_channel.png')
        bpy.ops.render.render(write_still=True)
        return
    if '--extra-review' in __import__('sys').argv:
        scene = bpy.data.scenes['Architecture_A']
        bpy.context.window.scene = scene
        cameras = next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
        scene.render.resolution_x, scene.render.resolution_y = 1100, 730
        scene.cycles.samples = 24
        for name, eye, aim in [('raised_join_player', (5, 358, 60.5), (-28, 423, 64)), ('scenery_join_player', (-111, 223, 60.5), (-173, 277, 65))]:
            scene.camera = arch.camera('review_'+name, eye, aim, cameras, 30)
            scene.render.filepath = str(IMAGES/(name+'.png'))
            bpy.ops.render.render(write_still=True)
        # Disposable review cameras; current saved art/counts unchanged.
        return
    if '--final-tint' in __import__('sys').argv:
        final_tint()
        return
    if '--finish-flow' in __import__('sys').argv:
        finish_flow()
        return
    if '--review-only' in __import__('sys').argv:
        render()
        return
    assert not bpy.context.scene.get('ContinuityRefined'), 'Refinement already applied; use --review-only.'
    bpy.context.window.scene = bpy.data.scenes['Independent_Assets_LIBRARY_ONLY']
    REPORT['before'] = {s.name: art.digest_scene(s) for s in bpy.data.scenes}
    transforms = {o.name: [list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type == 'EMPTY'}
    protected = {o.name: {v.index: tuple(v.co) for v in o.data.vertices if max(abs(v.co.x), abs(v.co.y)) >= 104} for o in bpy.data.objects if o.type == 'MESH' and o.get('TerrainFaceCount')}
    originals = ['prop_drained_wax_rosette', 'prop_drained_seed_shrub', 'prop_charred_ember_rose', 'prop_charred_thorn_pod']
    hashes = {n: arch.fingerprint(bpy.data.objects[n].data) for n in originals}
    DUST, CRUST, SCORCH, INFECTED = [bpy.data.materials[n] for n in ['Ember_WindblownAsh', 'Ember_BrokenCrust', 'Ember_ScorchedStrata', 'Ember_InvasiveGrowth']]
    HEAT = art.make_material('Ember_TissueHeat', (.38, .045, .008), .72, 1.15)
    TISSUE = art.make_material('Ember_CreepingTissue', (.22, .2, .03), .83)
    node = TISSUE.node_tree.nodes.new('ShaderNodeVertexColor')
    node.layer_name = 'TakeoverTissue'
    TISSUE.node_tree.links.new(node.outputs['Color'], TISSUE.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    adjust_ground()
    for ratio in (30, 50, 70):
        refine_plant(bpy.data.objects['prop_partial_rosette_'+str(ratio)], ratio/100)
    refine_plant(bpy.data.objects['prop_partial_seed_shrub_50'], .5, False)
    # Original charred library remains exact. Existing placed copies get active
    # derivatives with recessed veins; no new species or flora carpet.
    variants = bpy.data.collections['Flora_Takeover_States']
    for name in ('prop_charred_ember_rose', 'prop_charred_thorn_pod'):
        src = bpy.data.objects[name]
        derivative = src.copy(); derivative.data = src.data.copy()
        derivative.name = name+'_active_tissue'
        variants.objects.link(derivative)
        refine_plant(derivative, .93, False)
        for ob in list(bpy.data.objects):
            if ob != src and ob != derivative and ob.type == 'MESH' and ob.data == src.data:
                ob.data = derivative.data
        derivative.hide_render = True
    crust_integration()
    stages = [0, 1, 1, 1, 2, 0, 1, 2, 2, 2, 0, 2, 1]
    for name, stage in zip(arch.NAMES+arch.SCENERY, stages):
        group = bpy.data.collections[name]
        continuity(group, stage)
        if name in (arch.SCENERY[3], arch.SCENERY[4], arch.SCENERY[6]):
            collapse_remnants(group)
    seen = set()
    bpy.context.view_layer.update()
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.get('TerrainFaceCount') and ob.data.as_pointer() not in seen:
            seen.add(ob.data.as_pointer())
            recolor(ob, stages[(arch.NAMES+arch.SCENERY).index(home(ob))])
    REPORT['original_flora_exact'] = hashes == {n: arch.fingerprint(bpy.data.objects[n].data) for n in originals}
    REPORT['seam_band_vertices_exact'] = all(tuple(bpy.data.objects[n].data.vertices[k].co) == p for n, rows in protected.items() for k, p in rows.items())
    REPORT['original_empty_matrices_exact'] = all([list(r) for r in bpy.data.objects[n].matrix_world] == rows for n, rows in transforms.items())
    assert REPORT['original_flora_exact'] and REPORT['seam_band_vertices_exact'] and REPORT['original_empty_matrices_exact']
    REPORT['assets'] = {n: arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    REPORT['origins_dimensions_elevations'] = {n: {'origin': list(bpy.data.objects[n].location), 'bounds': arch.bounds(bpy.data.objects[n]), 'entry': bpy.data.objects[n].get('EntryElevationLocal'), 'exit': bpy.data.objects[n].get('ExitElevationLocal'), 'delta': bpy.data.objects[n].get('ElevationDelta')} for n in arch.NAMES+arch.SCENERY}
    for s in bpy.data.scenes:
        s['ContinuityRefined'] = True
    render()
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after_saved_readback'] = {s.name: art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['materials'] = len(bpy.data.materials)
    REPORT['collision_status'] = 'Visual surface edits only. Cooked collision, character/camera tests pending Studio; border-flow details explicitly nonsolid.'
    (HERE/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    (IMAGES/'continuity_technical_report.json').write_text(json.dumps(REPORT, indent=2), encoding='utf8')
    print('CONTINUITY_SAVED', REPORT['after_saved_readback'])


if __name__ == '__main__':
    main()
