"""Three approved terrains, actual socket placements, assembly-space colour proof.

Blender-only isolated experiment. No upload, production export or loader changes.
Run with tools/run_blender.py after modularity_probe.py.
"""
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview')
spec = importlib.util.spec_from_file_location('foundation', HERE / 'build_burned_plains.py')
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)
ORIGINAL_HILL = bp.hill
LAYOUT = json.loads((OUT / 'socket_layout.json').read_text())
PLACED = LAYOUT['placements']
CENTRES = [-256, 0, 256]
NAMES = ['opening_edge', 'active_burn_mid_plains', 'interior_edge']
REPORT = {'scope': 'AREA I isolated modularity proof', 'production_changes': False,
          'input': str(OUT / 'Input_ApprovedBurnedPlains.blend'), 'layout': LAYOUT}


def placement_matrix(i):
    p = PLACED[i]
    # Roblox Z = -Blender Y. ChunkCore yaw uses the opposite CFrame sign.
    return Matrix.Translation((p['x'], -p['z'], p['y'])) @ Matrix.Rotation(-math.radians(p['yaw']), 4, 'Z') @ Matrix.Translation((0, -CENTRES[i], -ORIGINAL_HILL(0, CENTRES[i])))


def raw_height(x, y):
    i = max(0, min(2, int((y + 384) // 256)))
    p = PLACED[i]
    local = Matrix.Rotation(math.radians(p['yaw']), 4, 'Z') @ Vector((x - p['x'], y + p['z'], 0))
    return ORIGINAL_HILL(local.x, local.y + CENTRES[i]) - ORIGINAL_HILL(0, CENTRES[i]) + p['y']


def height(x, y):
    # Authored compatibility collar in this experimental copy only. Both sides
    # have identical edge elevation and zero edge slope; retain every interior.
    edge = min([-128, 128], key=lambda v: abs(y-v))
    t = min(1, abs(y-edge)/24)
    weight = t*t*(3-2*t)
    return raw_height(x, edge) + (raw_height(x,y)-raw_height(x,edge))*weight


def colour_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value = .94
    c = m.node_tree.nodes.new('ShaderNodeVertexColor'); c.layer_name = 'AssemblyColour'
    m.node_tree.links.new(c.outputs['Color'], p.inputs['Base Color'])
    return m


def tint(o, palette, mat):
    d = o.data
    d.materials.clear(); d.materials.append(mat)
    a = d.color_attributes.new(name='AssemblyColour', type='FLOAT_COLOR', domain='POINT')
    for v in d.vertices:
        w = o.matrix_world @ v.co
        state = bp.burn_state(w.x, w.y)
        tone = .96 + .04 * math.sin(w.x / 23) * math.cos(w.y / 31)
        a.data[v.index].color = (*[c * tone for c in palette[state]], 1)
    for p in d.polygons:
        p.material_index = 0
    o['AppearanceOwner'] = 'ASSEMBLY_FIELD; geometry and anchors remain chunk-owned'


def copy_local(source, i, coll):
    o = source.copy(); o.data = source.data.copy(); coll.objects.link(o)
    o.parent = None
    o.matrix_world = placement_matrix(i) @ source.matrix_world
    o['PrototypeChunkIndex'] = i + 1
    return o


def split_grass(source, i, coll):
    # Keep the approved authored blade anchors and silhouettes; split the review
    # batch for ownership, then transform it like any other chunk-local detail.
    vs, fs = [], []
    lo, hi = CENTRES[i] - 128, CENTRES[i] + 128
    for p in source.data.polygons:
        coords = [source.matrix_world @ source.data.vertices[k].co for k in p.vertices]
        cy = sum(v.y for v in coords) / len(coords)
        if lo <= cy < hi:
            original_state = bp.burn_state(sum(v.x for v in coords)/len(coords), cy)
            mapped = [placement_matrix(i) @ v for v in coords]
            new_state = bp.burn_state(sum(v.x for v in mapped)/len(mapped), sum(v.y for v in mapped)/len(mapped))
            # The approved blade shape has a discrete half-height char variant.
            # Select that variant at an authored anchor using the shared field.
            if (original_state==2) != (new_state==2):
                baseline = (coords[0].z + coords[1].z)/2
                coords[-1].z = baseline + (coords[-1].z-baseline)*(2 if original_state==2 else .5)
            for k,v in enumerate(coords):
                w=placement_matrix(i)@v
                v.z += height(w.x,w.y)-raw_height(w.x,w.y)
            start = len(vs); vs.extend(tuple(v) for v in coords)
            fs.append(tuple(range(start, len(vs))))
    o = bp.mesh('authored_grass_chunk_' + str(i + 1), vs, fs, [], coll)
    o.matrix_world = placement_matrix(i)
    o['PrototypeChunkIndex'] = i + 1
    return o


def main():
    bpy.ops.wm.open_mainfile(filepath=REPORT['input'])
    approved = bpy.data.scenes['Emberfall_Area_I_Burned_Plains']
    sources = list(approved.objects)
    scene = bpy.data.scenes.new('Area_I_Modularity_0_180_0')
    bpy.context.window.scene = scene; bp.SCENE = scene
    root = bp.collection('ISOLATED_AREA_I_MODULARITY_REVIEW')
    chunks = [bp.collection('PLAYABLE_256_' + n, root) for n in NAMES]
    scenery = bp.collection('SCENERY_NONPLAYABLE_NO_SOCKETS', root)
    connective = bp.collection('ASSEMBLY_ROAD_FIELD_FIRE_REVIEW', root)
    bp.REVIEW = bp.collection('EVIDENCE_CAMERAS_LIGHTS')
    scene.world = approved.world
    for o in sources:
        if o.type == 'LIGHT':
            light = o.copy(); light.data = o.data.copy(); bp.REVIEW.objects.link(light)
    ground = colour_material('PROBE_Ground_AssemblyVertexColour')
    grass = colour_material('PROBE_Grass_AssemblyVertexColour')
    road = colour_material('PROBE_Road_AssemblyVertexColour')
    ground_palette = [(.16, .235, .045), (.29, .235, .075), (.045, .037, .030)]
    grass_palette = [(.21, .34, .055), (.49, .40, .17), (.035, .028, .018)]
    road_palette = [(.20, .135, .07), (.16, .10, .047), (.06, .041, .025)]
    terrains = []
    for i, n in enumerate(NAMES):
        source = bpy.data.objects['chunk_' + n]
        o = copy_local(source, i, chunks[i]); o.name = 'PLAYABLE_' + n
        maximum_adjustment = 0
        inverse = o.matrix_world.inverted()
        for v in o.data.vertices[:o['SurfaceVertexCount']]:
            w=o.matrix_world@v.co
            delta=height(w.x,w.y)-raw_height(w.x,w.y)
            maximum_adjustment=max(maximum_adjustment,abs(delta))
            w.z+=delta; v.co=inverse@w
        o['ExperimentalEdgeCollarStuds']=24
        o['MaxCollarAdjustmentStuds']=maximum_adjustment
        o['FootprintClass'] = 'STANDARD_PLAYABLE_256_REVIEW'
        tint(o, ground_palette, ground); terrains.append(o)
    batch = bpy.data.objects['playable_grass_states']
    for i in range(3):
        tint(split_grass(batch, i, chunks[i]), grass_palette, grass)
    preserved = Counter()
    for s in sources:
        if s.type != 'MESH' or s == batch or s.name.startswith('chunk_'):
            continue
        colls = {c.name for c in s.users_collection}
        if not colls.intersection({'Flora_NONSOLID', 'Countryside_SOLID_DECOR'}):
            continue
        if s.name == 'old_winding_field_track':
            continue
        bounds = [s.matrix_world @ Vector(v) for v in s.bound_box]
        anchor = sum(bounds, Vector()) / 8
        if not (-128 <= anchor.x <= 128 and -384 <= anchor.y < 384):
            continue
        i = max(0, min(2, int((anchor.y + 384) // 256)))
        o = copy_local(s, i, chunks[i]); preserved[s.name.split('.')[0]] += 1
        transformed_anchor=placement_matrix(i)@anchor
        o.location.z += height(transformed_anchor.x,transformed_anchor.y)-raw_height(transformed_anchor.x,transformed_anchor.y)
        if s.name.startswith('tree_crown'):
            w = o.matrix_world.translation
            state = bp.burn_state(w.x, w.y)
            o.data.materials.clear(); o.data.materials.append(bpy.data.materials['BP_canopy_' + ['green', 'stressed', 'singed'][state]])
            # Stage silhouettes remain authored, not generated by the mask.
        elif s.name.startswith(('tree_', 'field_fence', 'scorched_field', 'fallen_burned')):
            centre = placement_matrix(i) @ anchor
            o.data.materials.clear(); o.data.materials.append(bpy.data.materials['BP_' + ('charred_timber' if bp.burn_state(centre.x, centre.y) == 2 else 'field_timber')])
    # Continuous road assembled from the exact local approved guide samples.
    guides = []
    for i in range(3):
        samples = [placement_matrix(i) @ Vector((bp.road_x(y), y, ORIGINAL_HILL(bp.road_x(y), y)))
                   for y in range(CENTRES[i] - 128, CENTRES[i] + 129, 4)]
        for v in samples:
            v.z=height(v.x,v.y)
        samples.sort(key=lambda v: v.y)
        guides.extend(samples if i == 0 else samples[1:])
    guides = ([Vector((bp.road_x(y),y,height(bp.road_x(y),y))) for y in range(-560,-384,4)]
              + guides + [Vector((bp.road_x(y),y,height(bp.road_x(y),y))) for y in range(388,617,4)])
    vs, fs = [], []
    for p in guides:
        width = 4.2 + .7 * math.sin(p.y / 21)
        vs.extend([(p.x - width, p.y, p.z + .22), (p.x + width, p.y, p.z + .22)])
        if len(vs) > 2:
            n = len(vs); fs.append((n - 4, n - 2, n - 1, n - 3))
    track = bp.mesh('ASSEMBLY_track_from_authored_guides', vs, fs, [], connective)
    tint(track, road_palette, road)
    track['CollisionPolicy'] = 'VISUAL_ONLY; existing terrain is walking surface'
    # Continuation uses the actual exposed edge heights; large dimensions do not
    # make it a playable chunk. This is not the current random BACKDROP pass.
    bp.GROUND = [ground] * 9
    bp.hill = height
    counts = Counter()
    for name, bounds in [('west_scenery', (-440, -128, -640, 640)), ('east_scenery', (128, 440, -640, 640)),
                         ('entry_scenery', (-128, 128, -640, -384)), ('interior_scenery', (-128, 128, 384, 640))]:
        o, _ = bp.terrain(name, bounds, scenery)
        o['FootprintClass'] = 'SCENERY_ONLY'; o['NoSockets'] = True
        o['NoncollidableVisual'] = True
        tint(o, ground_palette, ground)
    # Use the approved distribution/palette for exterior context, at lower count.
    bp.GRASS = [bpy.data.materials[n] for n in ['BP_grass_green', 'BP_grass_olive', 'BP_grass_straw', 'BP_grass_singed', 'BP_grass_black_stubble', 'BP_grass_burned_brown']]
    tint(bp.grasses(scenery, 80000, (-430, 430, -620, 620), 'scenery_blades'), grass_palette, grass)
    bp.LEAF = [bpy.data.materials['BP_canopy_' + n] for n in ['green', 'stressed', 'singed']]
    bp.WOOD = bpy.data.materials['BP_field_timber']; bp.CHARWOOD = bpy.data.materials['BP_charred_timber']
    for x, y, h in [(-210,-290,29),(220,-240,27),(-205,-100,26),(190,110,28),(-230,340,27),(230,360,28)]:
        bp.tree(x, y, h, scenery)
    bp.FIRE = bpy.data.materials['BP_flame_orange']; bp.FIRECORE = bpy.data.materials['BP_flame_core']
    bp.SMOKE = bpy.data.materials['BP_SoftProceduralSmoke_REVIEW']
    bp.EMBER = bpy.data.materials['BP_restrained_ember']
    bp.fire_fronts(connective); bp.fissures(connective)
    bpy.context.view_layer.update()
    joins = []
    for i, y in enumerate([-128, 128]):
        edge = []
        for o in terrains[i:i+2]:
            stations = {}
            colours = o.data.color_attributes['AssemblyColour']
            for v in o.data.vertices[:o['SurfaceVertexCount']]:
                w = o.matrix_world @ v.co
                if abs(w.y-y)<.001:
                    stations[round(w.x,3)] = (w.z, tuple(colours.data[v.index].color))
            edge.append(stations)
        gap = max(abs(edge[0][x][0]-edge[1][x][0]) for x in edge[0])
        colour_gap = max(max(abs(a-b) for a,b in zip(edge[0][x][1],edge[1][x][1])) for x in edge[0])
        assert len(edge[0])==65 and gap<.001 and colour_gap<.00001
        joins.append({'y':y,'stations':65,'max_height_gap':gap,'max_colour_gap':colour_gap})
    for x in range(-126,128,4):
        for y in range(-382,384,4):
            counts[bp.burn_state(x,y)] += 1
    REPORT.update({'joins':joins,'playable_balance_percent':{['green','stressed','charred'][k]:round(v/sum(counts.values())*100,2) for k,v in counts.items()},
                   'preserved_local_objects':sum(preserved.values()),'road_samples':len(guides),
                   'terrain_geometry_changed':'24-stud experimental join collars only; approved input unchanged',
                   'max_collar_adjustment_studs':max(o['MaxCollarAdjustmentStuds'] for o in terrains),
                   'primary_yaw':[0,180,0],'alternate_yaw':[90,270,90],
                   'backend':'offline Blender vertex-colour bake, not Roblox runtime proof'})
    scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
    scene['README']='Approved macro geometry retained; experimental 24-stud join collars. Actual ChunkCore 0/180/0 layout; assembly field and guide-road proof. No runtime/export. Approved input preserved.'
    cameras = [bp.camera('01_assembled_overview',(540,-640,380),(0,0,16),40),
               bp.camera('02_top_burn_crossing',(0,0,1100),(0,0,0),ortho=950),
               bp.camera('03_player_eye_boundary',(10,-155,height(10,-155)+5),(-40,-75,height(-40,-75)+7),28),
               bp.camera('04_raised_join_front',(-225,-255,112),(-35,-110,12),36),
               bp.camera('05_interior_road',(4,145,height(4,145)+5),(0,350,height(0,350)+7),28)]
    evidence=[]
    for cam in cameras:
        scene.camera=cam
        scene.render.resolution_x,scene.render.resolution_y=(900,1100) if cam.name.startswith('02') else (1200,800)
        scene.render.filepath=str(OUT/(cam.name+'.png')); bpy.ops.render.render(write_still=True)
        evidence.append(scene.render.filepath); print('RENDERED',cam.name,flush=True)
    scene.camera=cameras[0]
    # Same placements/field/road rotated together, proving area axis is not north.
    alternate=bpy.data.scenes.new('Area_I_Modularity_90_270_90')
    alternate.world=scene.world
    alternate_root=bp.collection('ALTERNATE_LAYOUT_SOURCE_LINK', alternate.collection)
    for s in scene.objects:
        if s.type not in ('MESH','LIGHT'):
            continue
        o=s.copy(); alternate_root.objects.link(o)
        o.matrix_world=Matrix.Rotation(-math.pi/2,4,'Z')@s.matrix_world
    bpy.context.window.scene=alternate; bp.SCENE=alternate; bp.REVIEW=bp.collection('ALTERNATE_EVIDENCE')
    cam=bp.camera('06_quarter_turn_top',(0,0,1100),(0,0,0),ortho=1200)
    alternate.camera=cam; alternate.render.engine='BLENDER_EEVEE'
    alternate.render.resolution_x=1200; alternate.render.resolution_y=800
    alternate.view_settings.view_transform='AgX'; alternate.render.filepath=str(OUT/'06_quarter_turn_top.png')
    bpy.ops.render.render(write_still=True); evidence.append(alternate.render.filepath)
    bpy.context.window.scene=scene
    REPORT['evidence']=evidence
    REPORT['terrain_triangles']=[]
    for o in terrains:
        o.data.calc_loop_triangles(); REPORT['terrain_triangles'].append(len(o.data.loop_triangles))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsModularity.blend'))
    for p in [HERE/'modularity_report.json',OUT/'modularity_report.json']:
        p.write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('MODULARITY_DONE',json.dumps(REPORT['joins']),flush=True)


if __name__ == '__main__':
    main()
