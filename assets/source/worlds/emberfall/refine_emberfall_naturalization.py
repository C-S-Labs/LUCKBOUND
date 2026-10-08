"""Edit CURRENT foundation scene: distinct geology, shared seams and sparse life.

No fresh build, runtime work, export or kit expansion. Original scene snapshot
is retained; existing solid terrain topology, molten geometry and origins survive.
"""
import bpy
import bmesh
import hashlib
import importlib.util
import json
import math
import random
import shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
MAIN = OUT/'EmberfallFoundation.blend'
INPUT = OUT/'Input_Naturalization.blend'
IMAGES = OUT/'NaturalizationReview'
RNG = random.Random(3104)
REPORT = {'scene': str(MAIN), 'snapshot': str(INPUT), 'runtime_modified': False,
          'seam_band': 20, 'seam_profiles': ['BASELINE_ROUTE', 'RAISED_ROUTE', 'OPEN_COMBAT', 'LAVA_ADJACENT', 'SCENERY_OUTER']}
GRAMMAR = {'entry_wasteland_waystone': 'Open ash basin, single peripheral broken ledge',
           'path_wasteland_fault': 'One-sided basalt shelf and existing narrow fault',
           'combat_wasteland_broken_road': 'Broad combat plateau, off-center collapsed shoulder',
           'side_wasteland_shrine': 'Tilted sheltered ledge, localized vent',
           'path_fortress_causeway': 'Broad ascending road, one slumped masonry shoulder',
           'combat_fortress_gateworks': 'Buried ruin terrace with rear vertical failure'}


def smooth(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)


def datum(y):
    return 56*max(0, min(1, (y-152)/208))


def digest(ob):
    return hashlib.sha256(repr(([tuple(v.co) for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons])).encode()).hexdigest()


def visible_meshes(scene):
    excluded = set(bpy.data.collections['ReuseLibrary_SOURCE_ONLY'].all_objects) | set(bpy.data.collections['Scenery_8_SOURCE_LIBRARY'].all_objects)
    return [o for o in scene.objects if o.type == 'MESH' and o not in excluded and not o.hide_render]


def stats(scene):
    obs = visible_meshes(scene)
    flora = [o for o in obs if o.get('ReuseSource', '').startswith('prop_')]
    tris = 0
    deps = bpy.context.evaluated_depsgraph_get()
    for o in obs:
        ev = o.evaluated_get(deps)
        d = ev.to_mesh()
        d.calc_loop_triangles()
        tris += len(d.loop_triangles)
        ev.to_mesh_clear()
    return {'mesh_objects': len(obs), 'evaluated_triangles': tris, 'flora_count': len(flora),
            'flora_average_scale': sum(o.scale.x for o in flora)/max(1,len(flora)),
            'flora_max_height': max((o.dimensions.z for o in flora), default=0)}


def family(ob):
    return ob.name.split('.')[0].removeprefix('chunk_')


def geology(name, x, y):
    # Six different spatial compositions, not rotations of the longitudinal bands.
    if name == 'entry_wasteland_waystone' or name == 'open_ashland':
        ash = -.65*smooth(-95, -40, y)*(1-smooth(18, 75, y))*(1-smooth(20, 80, abs(x)))
        ledge = 12*smooth(-111,-93,x)*(1-smooth(-73,-55,x))*smooth(-55,-22,y)*(1-smooth(66,101,y))
        return ash+ledge
    if name == 'path_wasteland_fault':
        return 24*(1-smooth(-72,-59,x))*smooth(-86,-42,y)*(1-smooth(62,100,y))
    if name == 'combat_wasteland_broken_road':
        # Wide planar apron with a single slumped rear-left plateau.
        return 19*(1-smooth(-47,-36,x))*smooth(29,39,y)*(1-smooth(84,105,y)) + .7*smooth(-82,80,y)
    if name == 'side_wasteland_shrine':
        return 13*(1-smooth(-75,-62,x))*smooth(-54,-38,y)*(1-smooth(57,86,y)) + 1.5*smooth(-87,88,y)
    if name == 'path_fortress_causeway':
        return 17*(1-smooth(-79,-65,x))*smooth(8,24,y)*(1-smooth(67,96,y)) + 2*smooth(48,94,x)*(1-smooth(22,51,abs(y)))
    if name == 'combat_fortress_gateworks':
        return 15*smooth(43,54,y)*(1-smooth(19,45,x))*(1-smooth(97,109,y)) + .6*smooth(-90,25,y)
    if name == 'ruined_outskirts':
        return 5*smooth(-30,-18,y)*(1-smooth(51,80,y))*(1-smooth(35,68,x))
    if name == 'broken_ridge_shelf':
        return 30*smooth(-69,-55,x)*(1-smooth(-18,2,x))*smooth(-69,-49,y)*(1-smooth(71,100,y))
    if name == 'ash_faultland':
        return 12*(1-smooth(-19,-2,x))*(1-smooth(24,42,y))*smooth(-91,-65,y)
    if name == 'infected_outskirts':
        return 9*smooth(10,27,y)*(1-smooth(59,93,y))*(1-smooth(-38,-19,x))
    if name == 'fortress_silhouette':
        return 21*smooth(24,36,y)*(1-smooth(71,104,y))*(1-smooth(24,44,x))
    if name == 'SCENERY_OPEN_TILT':
        return max(0,9+.07*x+.045*y)*(1-smooth(78,107,abs(x)))*(1-smooth(87,112,abs(y)))
    if name == 'SCENERY_SPLIT_RIDGE':
        return 17*(1-smooth(-54,-36,x))*smooth(-79,-62,y)*(1-smooth(14,35,y)) + 25*smooth(6,21,x)*smooth(-19,-3,y)*(1-smooth(71,91,y))
    if name == 'SCENERY_BROAD_STEPS':
        return (4*smooth(-65,-54,y)+9*smooth(-2,8,y)+5*smooth(53,63,y))*(1-smooth(79,107,abs(x)))
    if name == 'elevated_shelf':
        return 28*smooth(-97,-76,x)*(1-smooth(20,42,x))*smooth(-55,-43,y)*(1-smooth(71,97,y))
    return 0


def tree(ob):
    return BVHTree.FromPolygons([v.co for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons])


def ground(ob, x, y):
    p, _, _, _ = TREES[ob.name].ray_cast(Vector((x,y,300)), Vector((0,0,-1)))
    assert p is not None
    return p.z


def terrain_edit(ob):
    name = family(ob)
    old = ob.data
    # The live study has 231 surface vertices; the following 60 vertices are
    # buried skirt/bottom support. Keep indices/topology and broad cavity shapes.
    ob.data = old.copy()
    root = ob.parent
    wy = root.location.y if root else 0
    base_z = root.location.z if root else 0
    rotation = root.rotation_euler.z if root else 0
    lava = 'path_wasteland_fault' in name or 'side_wasteland' in name or name == 'low_lava_terrain'
    for v in ob.data.vertices:
        x,y,z = v.co
        world = ob.matrix_world @ v.co
        old_datum = datum(world.y)-base_z if root and 'ring_origin' in root.name else datum(y+wy)-datum(wy) if name == 'path_fortress_causeway' else 0
        if v.index >= 231:
            # Shared buried depth means adjoining walls do not have mismatched
            # foundations on the elevated side. No visible border wall added.
            v.co.z = old_datum-46
            continue
        relief = geology(ob.get('GrammarOverride',name),x,y)
        if name == 'low_lava_terrain':
            relief = z-old_datum
            if x < 35:
                relief *= .1
        elif lava:
            # Retain the actual molten containment and rim on its active side.
            keep = smooth(44,58,x)
            if name == 'side_wasteland_shrine':
                keep *= 1-smooth(40,78,abs(y))
            relief = relief*(1-keep)+(z-old_datum)*keep
        edge = 128-max(abs(x),abs(y))
        # 20-stud controlled profile, an additional short ease into the interior.
        blend = smooth(20,40,edge)
        lateral = x if abs(y) >= abs(x) else y
        shared = .16*(math.cos(lateral*.047)-1)
        v.co.z = old_datum+shared*(1-blend)+relief*blend
        j,k = divmod(v.index,21)
        active_rows = range(4,7) if name=='side_wasteland_shrine' else range(2,9)
        if lava and k in (15,16) and j in active_rows:
            v.co.z = z
    ob.data.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        if p.index < 200:
            p.material_index = 1 if p.normal.z < .82 else 0
            # Local exposed broken tops, not continuous brown stripe assignments.
            if p.normal.z > .82 and p.center.z-(datum(p.center.y+wy)-datum(wy) if name == 'path_fortress_causeway' else 0) > 8:
                p.material_index = 1
    ob['TerrainIdentity'] = ob.get('GrammarOverride',GRAMMAR.get(name, name.replace('_',' ')))
    ob['SeamBandStuds'] = 20
    ob['SeamProfile'] = 'RAISED_ROUTE' if name == 'combat_fortress_gateworks' else 'OPEN_COMBAT' if 'combat_' in name else 'LAVA_ADJACENT' if lava else 'SCENERY_OUTER' if name not in GRAMMAR else 'BASELINE_ROUTE'
    TREES[ob.name] = tree(ob)
    REPORT.setdefault('terrain_objects', []).append({'object': ob.name, 'identity': ob['TerrainIdentity'], 'profile': ob['SeamProfile']})


def terrain_for(root):
    return next(o for o in root.children if o.type == 'MESH' and o.name.startswith('chunk_'))


def recent_panel(name, collection, root, terrain, x, y, width, height, tilt=0, turn=0):
    outline = [(0,0),(width,0),(width,height*.4),(width*.83,height*.52),
               (width*.78,height*.88),(width*.54,height*.76),(width*.4,height),
               (width*.22,height*.92),(0,height*.97)]
    vs = [(a,b,z) for b in (-1.6,1.6) for a,z in outline]
    n = len(outline)
    fs = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o = helper.mesh(name,vs,fs,[MASON,FRESH],collection,root,[0,0]+[1 if i>1 else 0 for i in range(n)])
    o.location = (x,y,ground(terrain,x,y)-.45)
    o.rotation_euler = (tilt,.04,turn)
    o['RecentCollapse'] = True
    # Shallow course seams remain on the larger wall mass; no stacks of loose
    # equally sized blocks. Longitudinal grain gives the masonry scale.
    for j in range(1,int(height/3.8)):
        length = width*(.94 if j<height/7 else .68)
        line = helper.box('wall_course_recess', (length/2,-1.63,j*3.8), (length,.09,.075), JOINT,collection,o)
        line.rotation_euler = (0,0,0)
    return o


def rebuild_ruins(scene):
    targets = [o for o in list(bpy.data.objects) if o.type == 'MESH' and o.name.startswith('fused_ruin_masonry')]
    roots = {o.parent for o in targets if o.parent}
    REPORT['ruin_blocks_removed'] = len(targets)
    for o in targets:
        bpy.data.objects.remove(o,do_unlink=True)
    rebuilt = []
    for root in sorted(roots,key=lambda o:o.name):
        terrain = terrain_for(root)
        name = family(terrain)
        collection = next(c for c in root.users_collection)
        if name == 'path_wasteland_fault':
            plans = [(-31,17,13,8,-.13,0)]
        elif name == 'combat_wasteland_broken_road':
            plans = [(-36,37,24,12,.12,math.pi/2),(-37,37,16,9,-.16,0)]
        elif name == 'side_wasteland_shrine':
            plans = [(-26,39,16,11,.08,0)]
        elif name == 'path_fortress_causeway':
            plans = [(-38,27,27,19,.17,math.pi/2),(34,42,18,13,-.12,math.pi/2)]
        elif name == 'combat_fortress_gateworks':
            plans = [(-43,24,27,38,.11,math.pi/2),(-43,24,20,28,-.08,0),(36,34,22,26,-.16,math.pi/2)]
        elif name == 'fortress_silhouette':
            plans = [(-25,31,25,29,.15,math.pi/2),(-25,31,19,24,-.09,0)]
        else:
            plans = [(-25,32,16,9,.12,0)]
        for i,(x,y,w,h,tilt,turn) in enumerate(plans):
            recent_panel('recent_split_wall',collection,root,terrain,x,y,w,h,tilt,turn)
            # Failure debris is immediately beside its parent wall, not evenly
            # dispersed ancient ruins; larger intact fallen mass, few fragments.
            if i == 0:
                p = helper.box('fresh_fallen_wall_mass',(x+11,y-8,ground(terrain,x+11,y-8)+1.2),(w*.65,6,3.6),FRESH,collection,root,.23)
                for dx,dy in [(3,-5),(7,-11)]:
                    helper.box('localized_collapse_rubble',(x+dx,y+dy,ground(terrain,x+dx,y+dy)+.7),(3.3,2.1,1.8),MASON,collection,root,.3)
                if name in ('combat_fortress_gateworks','path_fortress_causeway'):
                    helper.box('snapped_roof_beam',(x+6,y-12,ground(terrain,x+6,y-12)+1.4),(16,1.2,1.4),WOOD,collection,root,.22)
                    helper.box('recently_fallen_roof_section',(x+10,y-16,ground(terrain,x+10,y-16)+2.3),(12,13,1.1),ROOF,collection,root,.27)
        rebuilt.append({'root':root.name,'family':name,'panels':len(plans)})
    REPORT['rebuilt_ruins'] = rebuilt


def sparsify_flora(scene):
    excluded = set(bpy.data.collections['ReuseLibrary_SOURCE_ONLY'].all_objects)
    roots = {o.parent for o in bpy.data.objects if o.type == 'MESH' and o not in excluded and o.get('ReuseSource','').startswith('prop_') and o.parent}
    pockets = {'entry_wasteland_waystone':(-38,-27,3),'path_wasteland_fault':(-47,18,3),
               'combat_wasteland_broken_road':(-28,48,4),'side_wasteland_shrine':(-18,46,3),
               'path_fortress_causeway':(-27,35,3),'combat_fortress_gateworks':(-28,23,4)}
    for root in sorted(roots,key=lambda o:o.name):
        terrain = terrain_for(root)
        name = family(terrain)
        obs = sorted([o for o in root.children if o.get('ReuseSource','').startswith('prop_')],key=lambda o:('partial_rosette_50' not in o.get('ReuseSource',''),o.name))
        x,y,count = pockets.get(name,(-23,33,1 if name=='open_ashland' else 2))
        for j,o in enumerate(obs):
            if j>=count:
                bpy.data.objects.remove(o,do_unlink=True)
                continue
            dx,dy = [(-2.6,-1.3),(1.7,2.8),(3.6,-2.1),(-4.6,4.1)][j]
            o.location = (x+dx,y+dy,ground(terrain,x+dx,y+dy)+.03)
            scale = [.59,.73,.5,.65][j]
            o.scale = (scale,)*3
            o['PlacementIntent'] = 'Sheltered ruin-adjacent cluster; empty stretches intentional'


def regroup_basalt(scene):
    roots = {o.parent for o in bpy.data.objects if o.type=='MESH' and o.get('ReuseSource','').startswith('reuse_basalt') and o.parent}
    for root in sorted(roots,key=lambda o:o.name):
        terrain = terrain_for(root)
        name = family(terrain)
        old = [o for o in root.children if o.get('ReuseSource','').startswith('reuse_basalt')]
        for o in old:
            bpy.data.objects.remove(o,do_unlink=True)
        if name in ('open_ashland','ruined_outskirts','ash_faultland','infected_outskirts'):
            continue
        x,y = (-86,14) if name=='path_wasteland_fault' else (-83,22) if name=='entry_wasteland_waystone' else (-67,52) if name=='combat_wasteland_broken_road' else (-81,37) if name=='path_fortress_causeway' else (-70,41)
        count = 5 if name in GRAMMAR else 4
        collection = root.users_collection[0]
        for j in range(count):
            source = bpy.data.objects['reuse_basalt_column_'+str(j%6)]
            xx,yy = x+[0,5,9,3,12][j],y+[0,3,-1,8,6][j]
            scale = [.32,.37,.26,.41,.3][j]
            o = helper.copy_asset(source,'embedded_basalt_group',collection,root,(xx,yy,ground(terrain,xx,yy)-4.5),scale)
            o.rotation_euler.z = .13*j
            o['solid'] = True
            o['EmbeddedFormation'] = True
        REPORT.setdefault('basalt_groups',[]).append({'root':root.name,'count':count,'replaces':len(old)})


def cool_materials():
    colors = {'EF_AshGround':(.064,.073,.086),'EF_BasaltFreshBreak':(.025,.037,.049),
              'EF_ExposedVolcanicStrata':(.043,.048,.052),'EF_WeatheredCivilization':(.095,.105,.115)}
    before = {}
    for name,col in colors.items():
        m = bpy.data.materials[name]
        before[name] = list(m.diffuse_color)
        m.diffuse_color = (*col,1)
        m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*col,1)
    REPORT['palette_before'] = before
    REPORT['palette_after'] = colors
    m = bpy.data.materials['EF_MoltenAuthoredFlow_REVIEW']
    p = m.node_tree.nodes.get('Principled BSDF')
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB':
            n.color_ramp.interpolation = 'EASE'
            while len(n.color_ramp.elements)>2:
                n.color_ramp.elements.remove(n.color_ramp.elements[-1])
            for e,pos,col in zip(n.color_ramp.elements,(.22,.83),[(.68,.085,.012,1),(.92,.21,.022,1)]):
                e.position = pos
                e.color = col
            e = n.color_ramp.elements.new(.96)
            e.color = (1,.39,.055,1)
        elif n.type == 'TEX_NOISE':
            n.inputs['Detail'].default_value = 1.2
            n.inputs['Roughness'].default_value = .3
    p.inputs['Emission Strength'].default_value = .8
    REPORT['lava_material'] = 'Primary molten orange, dark cooled rim, sparse hotter core; eased low-contrast irregular patches instead of discrete contour bands.'


def camera(name, loc, target, lens=32, ortho=None):
    if name in bpy.data.objects:
        o = bpy.data.objects[name]
        o.location = loc
        o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
        o.data.type = 'PERSP'
        o.data.lens = lens
    else:
        o = helper.camera(name,loc,target,lens,ortho)
    if ortho:
        o.data.type='ORTHO'
        o.data.ortho_scale=ortho
    return o


def render(scene, shots, prefix):
    for name,loc,target,lens,ortho in shots:
        scene.camera = camera('NaturalReview_'+name,loc,target,lens,ortho)
        scene.render.filepath = str(IMAGES/(prefix+'_'+name+'.png'))
        bpy.ops.render.render(write_still=True)


def seams(scene):
    result = []
    rows = [('entry_wasteland_waystone','path_wasteland_fault'),('path_wasteland_fault','combat_wasteland_broken_road'),
            ('combat_wasteland_broken_road','path_fortress_causeway'),('path_fortress_causeway','combat_fortress_gateworks')]
    for a,b in rows:
        oa,ob = bpy.data.objects['chunk_'+a],bpy.data.objects['chunk_'+b]
        gaps=[]
        slopes=[]
        for x in (-35,0,35):
            ta,tb = tree(oa),tree(ob)
            pa,na,_,_=ta.ray_cast(Vector((x,127.999,300)),Vector((0,0,-1)))
            pb,nb,_,_=tb.ray_cast(Vector((x,-127.999,300)),Vector((0,0,-1)))
            assert pa is not None and pb is not None
            gaps.append(abs((oa.matrix_world@pa).z-(ob.matrix_world@pb).z))
            slopes.append(math.degrees(na.angle(nb)))
        result.append({'pair':[a,b],'max_gap':max(gaps),'max_normal_angle':max(slopes)})
    REPORT['join_probes'] = result


def main():
    global helper,TREES,MASON,FRESH,JOINT,WOOD,ROOF
    IMAGES.mkdir(parents=True,exist_ok=True)
    if not INPUT.exists():
        shutil.copy2(MAIN,INPUT)
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    scene = bpy.context.scene
    assert not scene.get('NaturalizationPassComplete'), 'Refinement already applied; review saved scene rather than reapply.'
    spec = importlib.util.spec_from_file_location('emberfall_foundation_helpers',HERE/'build_emberfall_foundation.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.REVIEW = bpy.data.collections['Cameras_Lights_Scale_REVIEW_ONLY']
    helper.RNG = RNG
    REPORT['before'] = stats(scene)
    REPORT['origins_before'] = {o.name:[list(o.location),list(o.rotation_euler)] for o in bpy.data.objects if o.type=='EMPTY'}
    lava_hashes = {o.name:digest(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('molten_')}
    flora_hashes = {o.name:digest(o) for o in bpy.data.collections['ReuseLibrary_SOURCE_ONLY'].objects if o.type=='MESH'}
    shots = [
        ('top_layout',(100,0,2000),(100,0,0),36,1900),
        ('overview',(1030,-1150,760),(100,40,22),42,None),
        ('entry_open_basin',(118,-648,72),(-12,-485,4),32,None),
        ('path_one_sided_shelf',(116,-363,69),(-28,-248,7),34,None),
        ('combat_plateau',(106,-112,68),(-28,28,7),34,None),
        ('baseline_seam_oblique',(100,-435,27),(-20,-377,1),34,None),
        ('baseline_seam_eye',(0,-401,4.5),(-10,-345,2),27,None),
        ('second_baseline_join',(82,-178,24),(-12,-111,2),32,None),
        ('raised_seam_oblique',(86,354,83),(-8,410,61),31,None),
        ('raised_seam_eye',(0,363,60.5),(-5,428,61),27,None),
        ('elevated_lookback',(8,403,65),(0,171,12),26,None),
        ('flora_scale_density',(52,-558,14),(-26,-521,4),31,None),
        ('recent_wasteland_failure',(12,-13,12),(-30,41,7),33,None),
        ('embedded_basalt',(-33,-283,22),(-77,-234,17),34,None),
        ('lava_close',(568,-16,5),(585,12,-10),37,None),
    ]
    render(scene,[shots[0],shots[11],shots[12],shots[13],shots[14]],'before')
    TREES = {}
    terrain = [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('chunk_') and 'distant_stressed' not in o.name]
    old_trees = {o.name:tree(o) for o in terrain}
    for ob in terrain:
        if len(ob.data.vertices)!=291:
            # Every current foundation object shares the original topology;
            # distant ground from the same helper has the same surface support.
            assert len(ob.data.vertices)>=231
        terrain_edit(ob)
    # Ground-attached saved art only moves vertically until the targeted rebuilds.
    for ob in list(bpy.data.objects):
        if ob.type!='MESH' or not ob.parent or ob.name.startswith(('chunk_','molten_','rooted_crust_')):
            continue
        if ob.parent.type != 'EMPTY':
            continue
        terrains = [o for o in ob.parent.children if o.name in TREES]
        if not terrains:
            continue
        t = terrains[0]
        # Retain the authored object's former burying/height offset.
        x,y = ob.location.x,ob.location.y
        if max(abs(x),abs(y))>127:
            continue
        # Original anchors sit within two studs of the ground except markers.
        if ob.get('ReuseSource') or ob.name.startswith(('road_remnant','charred_fence','broken_stairs','fallen_marker','broken_waystone','tilting_waystone','slumped_gate','recent_gatework','heat_inside')):
            old_hit,_,_,_=old_trees[t.name].ray_cast(Vector((x,y,300)),Vector((0,0,-1)))
            offset = ob.location.z-old_hit.z
            ob.location.z = ground(t,x,y)+offset
    MASON=bpy.data.materials['EF_WeatheredCivilization']
    FRESH=helper.material('EF_RecentFractureFaces',(.14,.16,.18))
    JOINT=helper.material('EF_RecessedMasonryCourses',(.032,.039,.047))
    WOOD=bpy.data.materials['EF_CharredTimber']
    ROOF=helper.material('EF_SnappedSlateRoof',(.047,.057,.066))
    cool_materials()
    rebuild_ruins(scene)
    sparsify_flora(scene)
    regroup_basalt(scene)
    bpy.context.view_layer.update()
    REPORT['lava_geometry_exact'] = all(digest(bpy.data.objects[n])==h for n,h in lava_hashes.items())
    REPORT['source_assets_exact'] = all(digest(bpy.data.objects[n])==h for n,h in flora_hashes.items())
    assert REPORT['lava_geometry_exact'] and REPORT['source_assets_exact']
    REPORT['playable_macro_grammars_changed'] = 6
    seams(scene)
    REPORT['after'] = stats(scene)
    render(scene,shots,'after')
    changes=[]
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED':
                changes.append((n,n.inputs['Emission Strength'].default_value))
                n.inputs['Emission Strength'].default_value=0
    lava=bpy.data.materials['EF_MoltenAuthoredFlow_REVIEW']
    base=lava.node_tree.nodes.get('Principled BSDF').inputs['Base Color']
    links=[(k.from_socket,k.to_socket) for k in base.links]
    oldcolor=tuple(base.default_value)
    for link in list(base.links):
        lava.node_tree.links.remove(link)
    base.default_value=(.045,.05,.055,1)
    render(scene,[shots[0],shots[1],shots[5],shots[8]],'glow_minimized')
    for n,value in changes:
        n.inputs['Emission Strength'].default_value=value
    base.default_value=oldcolor
    for a,b in links:
        lava.node_tree.links.new(a,b)
    scene.camera=bpy.data.objects['NaturalReview_overview']
    scene['NaturalizationPassComplete']=True
    scene['README']='Current foundation, edited in place: six terrain identities, shared 20-stud seams, sparse small flora, recent split masonry and embedded basalt. No expansion/export/Studio.'
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    for path in (HERE/'naturalization_technical_report.json',IMAGES/'naturalization_technical_report.json'):
        path.write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('NATURALIZATION_SAVED',json.dumps({'before':REPORT['before'],'after':REPORT['after'],'joins':REPORT['join_probes']}))


if __name__=='__main__':
    main()
