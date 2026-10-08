"""Five-piece Emberfall review only. Run through tools/run_blender.py; no exports.

Blender XY is the footprint, +Y is north; Z is up. Each review translation
belongs to a parent empty, never the authored mesh. No game content is emitted.
"""
import bpy
import json
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_Prototype')
OUT.mkdir(parents=True, exist_ok=True)
RNG = random.Random(42026)
HALF = 128
NAMES = ['chunk_entry_ash_plain', 'path_column_pass', 'chunk_column_forest',
         'side_lava_overlook', 'cap_collapsed_pass']
ROLES = ['ENTRY', 'PATH', 'COMBAT', 'SIDE', 'CAP']
OPENINGS = [['N'], ['N', 'S'], ['N', 'S', 'E'], ['W'], ['S']]
OFFSETS = [(0, -256, 0), (0, 0, 0), (0, 256, 0), (256, 256, 0), (0, 512, 0)]
DESIGNS = [
    'Calm windswept ash shelf; one split blackstone fin catches an ash drift. Almost no nearby heat.',
    'Narrow cool road between monumental jointed basalt walls; one snapped leaning crown and a broad internal rise.',
    'Three combat clearings between asymmetric column groves. Lower cooled basin, main floor, upper flank; radial rather than corridor composition.',
    'One west entrance; a broad rising ash trail ends on a high shelf beside a glassy mineral cairn. View over a vast external lava field.',
    'An old road buried beneath oblique fallen columns well inside the boundary. A cold road remnant beyond and ember bloom nook suggest continuation.'
]


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else bpy.context.scene.collection.children).link(c)
    return c


def material(name, color, emission=0, roughness=.85):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    elif name in ('Ember_Basalt','Ember_CooledLava','Ember_Ash'):
        # Review surface detail; must be baked/verified before any future import.
        nodes=m.node_tree.nodes;links=m.node_tree.links
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.2 if name=='Ember_Basalt' else .6
        noise.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27 if name=='Ember_Basalt' else .16
        bump.inputs['Distance'].default_value=.28
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m


def mesh(name, verts, faces, mat, coll, parent=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.materials.append(mat)
    data.update()
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.parent = parent
    return obj


def smoothstep(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)


def socket_zone(i, x, y, width=28, depth=16):
    for s in OPENINGS[i]:
        across, along = (x, y) if s in ('N', 'S') else (y, x)
        signed = along if s in ('N', 'E') else -along
        if abs(across) <= width and signed >= HALF-depth:
            return True
    return False


def height(i, x, y):
    # Low-frequency authored shelves; the terrain grid supports broad ramps.
    if i == 0:
        z = 2.8*math.exp(-((x+60)/48)**2-((y+30)/67)**2)
        z += 8*smoothstep(90, 128, max(abs(x), -y))
    elif i == 1:
        z = 12*math.exp(-((y-14)/52)**4)*max(0, 1-(x/42)**4)
        z += 18*smoothstep(28, 66, abs(x))
        # One low fissure on east side, not twin orange guardrails.
        z -= 26*math.exp(-((x-32)/9)**4-((y+23)/57)**4)
    elif i == 2:
        z = 16*smoothstep(25, 75, x)*math.exp(-((y-40)/68)**4)
        z -= 10*math.exp(-((x+63)/28)**4-((y-22)/45)**4)
        z += 14*smoothstep(96, 128, max(abs(x), abs(y)))
        # Flat main hub at local origin and generous open corridors to mouths.
        z *= smoothstep(25, 45, math.hypot(x, y))
    elif i == 3:
        z = 26*smoothstep(-100, 65, x)
        z += 8*smoothstep(80, 128, abs(y))
        z += 9*smoothstep(100, 128, x)
        # Local footprint center is ground datum; overlook on eastern half.
        z -= 26*smoothstep(-100, 65, 0)*math.exp(-(x/24)**4-(y/40)**4)
    else:
        z = 3*smoothstep(-90, 0, y)
        z += 18*smoothstep(35, 100, abs(x))
        z += 16*smoothstep(75, 128, y)
    # Taper the approach to exactly level 56-wide connections.
    for s in OPENINGS[i]:
        across, along = (x, y) if s in ('N', 'S') else (y, x)
        signed = along if s in ('N', 'E') else -along
        fade = smoothstep(92, 112, signed)*(1-smoothstep(28, 44, abs(across)))
        z *= 1-fade
    z *= smoothstep(16, 40, math.hypot(x,y))
    return z


def terrain(i, c, root):
    axes=sorted(set(range(-128,129,8)) | {-28,28})
    n = len(axes)
    vs = [(x, y, height(i, x, y)) for y in axes for x in axes]
    fs = []
    for j in range(n-1):
        for k in range(n-1):
            a = j*n+k
            fs.extend([(a, a+1, a+n+1), (a, a+n+1, a+n)])
    ring = list(range(n)) + [j*n+n-1 for j in range(1,n)]
    ring += list(range(n*n-2, (n-1)*n-1, -1)) + [j*n for j in range(n-2,0,-1)]
    start = len(vs)
    vs += [(vs[a][0], vs[a][1], -24) for a in ring]
    for j, a in enumerate(ring):
        k = (j+1)%len(ring)
        fs.append((a, start+j, start+k, ring[k]))
    fs.append(tuple(reversed(range(start, len(vs)))))
    obj = mesh('ground', vs, fs, ASH if i == 0 else COOLED, c, root)
    walk = obj.data.attributes.new('authored_walk_surface', 'BOOLEAN', 'FACE')
    for j in range(2*(n-1)**2): walk.data[j].value = True
    obj.data.materials.append(ASH)
    obj.data.materials.append(BASALT)
    for p in obj.data.polygons[:2*(n-1)**2]:
        x,y,z = p.center
        # Recomputed centers after update; ash makes walking routes readable.
        p.material_index = 1 if abs(x) < 28 or (i == 3 and abs(y) < 32) else 0
        p.use_smooth = True
    return obj


def column(name, x, y, base, radius, tall, c, root, tilt=(0,0), mat=None, rings=6):
    # A hexagonal prism with narrow bevel faces and irregular geological joints.
    outline = []
    for j in range(6):
        a = 2*math.pi*j/6
        b = 2*math.pi*(j+1)/6
        va = Vector((math.cos(a),math.sin(a)))
        vb = Vector((math.cos(b),math.sin(b)))
        outline += [va.lerp(vb,.075), va.lerp(vb,.925)]
    vs=[]
    top_noise=[RNG.uniform(-.07,.065)*tall for _ in range(6)]
    side_noise=[RNG.uniform(-.065,.065) for _ in range(6)]
    joint_heights = [0,.19,.204,.47,.487,.75,.766,1] if rings==8 else [k/(rings-1) for k in range(rings)]
    for k in range(rings):
        t=joint_heights[k]
        scale=1+(.012 if k%2 else -.027)
        for j,v in enumerate(outline):
            z=base+t*tall+top_noise[j//2]*(t if k==rings-1 else .22*math.sin(t*math.pi))
            r=radius*(scale+side_noise[j//2]+.018*math.sin(t*13+j//2))
            vs.append((x+v.x*r+t*tilt[0],y+v.y*r+t*tilt[1],z))
    fs=[]
    for k in range(rings-1):
        for j in range(12):
            a=k*12+j;b=k*12+(j+1)%12
            fs.append((a,b,b+12,a+12))
    fs += [tuple(reversed(range(12))),tuple(range((rings-1)*12,rings*12))]
    obj=mesh(name,vs,fs,mat or BASALT,c,root)
    # Supporting bevels are actual geometry, no subdivision at export time.
    return obj


def rock(name,x,y,z,sx,sy,sz,c,root,mat=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
    obj=bpy.context.object
    for old in list(obj.users_collection): old.objects.unlink(obj)
    c.objects.link(obj)
    obj.name=name;obj.parent=root
    for v in obj.data.vertices:
        q=v.co
        q.x=x+q.x*sx*(1+.08*math.sin(q.y*7))
        q.y=y+q.y*sy
        q.z=z+q.z*sz
    obj.data.materials.append(mat or BASALT)
    return obj


def ribbon(name, points, width, c, root, mat):
    vs=[]
    for j,p in enumerate(points):
        prev=Vector(points[max(0,j-1)]);nxt=Vector(points[min(len(points)-1,j+1)])
        d=nxt-prev; perpendicular=Vector((-d.y,d.x,0)).normalized()
        v=Vector(p)
        vs += [tuple(v-perpendicular*width/2),tuple(v+perpendicular*width/2)]
    return mesh(name,vs,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(points)-1)],mat,c,root)


def join_objects(c, name, root):
    obs=[o for o in c.objects if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.join()
    obj=obs[0];obj.name=name
    # Every vertex was authored in local chunk frame; keep datum at (0,0,0).
    obj.location=(0,0,0);obj.parent=root
    return obj


def plant_asset(name, kind):
    c=collection(name+'_parts', LIBRARY)
    if kind < 2:
        if kind == 0:
            # Waxy lance-leaf rosette; pointed curved leaves, no flat fan cards.
            for j in range(9):
                a=j*math.tau/9;length=RNG.uniform(2.4,3.7)
                verts=[]
                for k in range(7):
                    t=k/6;r=length*t;w=.55*math.sin(math.pi*t)
                    for side in (-1,0,1):
                        verts.append((math.cos(a)*r-math.sin(a)*w*side,
                                      math.sin(a)*r+math.cos(a)*w*side,
                                      .25+2.1*math.sin(t*1.9)+(.12 if side==0 else 0)))
                ob=mesh('waxy_leaf',verts,[(k*3+j,k*3+j+1,k*3+j+4,k*3+j+3) for k in range(6) for j in range(2)],DRAINED,c)
                for p in ob.data.polygons:p.use_smooth=True
        else:
            # Brittle branching seed shrub: dim pale seed heads and curved stems.
            for j in range(7):
                a=j*2.399;end=(math.cos(a)*1.6,math.sin(a)*1.6,3+j%3*.55)
                stem_curve('seed_stem',[(0,0,0),(.3*end[0],.3*end[1],1.7),end],.075,c,None,DRAINED_STEM)
                rock('seed_head',*end,.28,.28,.5,c,None,DRAINED)
    else:
        for j in range(3 if kind == 2 else 5):
            a=j*2.399;cx=math.cos(a)*(.6+j*.18);cy=math.sin(a)*(.6+j*.18);cz=1.9+j*.3
            stem_curve('charred_stem',[(cx*.3,cy*.3,0),(cx*.75,cy*.75,cz*.65),(cx,cy,cz)],.09,c,None,CHARRED)
            if kind == 2:
                # Rose-like nested curled black petals around a recessed ember.
                for layer in range(2):
                    for k in range(6):
                        angle=k*math.tau/6+layer*.4;verts=[]
                        for t in range(5):
                            u=t/4;r=.15+(1-layer*.35)*math.sin(u*2.3)
                            for s in (-1,0,1):
                                aa=angle+s*.45*math.sin(u*math.pi)
                                verts.append((cx+math.cos(aa)*r,cy+math.sin(aa)*r,cz+u*.8+.12*(s==0)))
                        ob=mesh('curled_petal',verts,[(q*3+s,q*3+s+1,q*3+s+4,q*3+s+3) for q in range(4) for s in range(2)],CHARRED,c)
                        for p in ob.data.polygons:p.use_smooth=True
                rock('dim_heart',cx,cy,cz+.2,.2,.2,.16,c,None,EMBER)
            else:
                for k in range(3):
                    stem_curve('thorn',[(cx,cy,cz*.7),(cx+math.cos(a+k)*.75,cy+math.sin(a+k)*.75,cz*.9)],.06,c,None,CHARRED)
                rock('split_seedpod',cx,cy,cz,.27,.27,.65,c,None,CHARRED)
                ribbon('ember_split',[(cx-.06,cy-.28,cz-.2),(cx+.08,cy-.28,cz+.32)],.07,c,None,EMBER)
    obj=join_objects(c,name,None)
    for old in list(obj.users_collection):old.objects.unlink(obj)
    LIBRARY.objects.link(obj)
    bpy.data.collections.remove(c)
    obj['solid']=False;obj['Animation']='Static';obj['Tier']=2
    obj.hide_render=True;obj.hide_set(True)
    return obj


def stem_curve(name,points,radius,c,root,mat):
    # Mesh tube, not curve, to keep reusable assets portable.
    vs=[]
    for p in points:
        for j in range(6):vs.append((p[0]+radius*math.cos(j*math.tau/6),p[1]+radius*math.sin(j*math.tau/6),p[2]))
    fs=[(k*6+j,k*6+(j+1)%6,(k+1)*6+(j+1)%6,(k+1)*6+j) for k in range(len(points)-1) for j in range(6)]
    fs.extend([tuple(reversed(range(6))),tuple(range(len(vs)-6,len(vs)))])
    return mesh(name,vs,fs,mat,c,root)


def place_flora(i,c,root,kind,x,y,scale=1):
    src=PLANTS[kind];obj=bpy.data.objects.new(src.name+'_placement',src.data)
    c.objects.link(obj);obj.parent=root
    obj.location=(x,y,height(i,x,y)+.03);obj.scale=(scale,scale,scale)
    obj.rotation_euler.z=RNG.uniform(0,math.tau)
    obj['LibraryAsset']=src.name;obj['solid']=False;obj['Animation']='Static';obj['Tier']=2
    return obj


def build_chunk(i):
    group=collection(NAMES[i],PLAYABLE)
    root=bpy.data.objects.new(NAMES[i]+'_review_position',None);group.objects.link(root)
    root['Footprint']='256 x 256';root['AuthoredOrigin']='0,0,0';root['InferredRole']=ROLES[i]
    st=collection(NAMES[i]+'_Structure',group)
    solid=collection(NAMES[i]+'_Props_Solid',group)
    ambient=collection(NAMES[i]+'_Props_NonSolid',group)
    terrain(i,st,root)
    if i == 0:
        for x,y,r,h in [(-77,-38,14,18),(-65,-30,8,25),(-97,52,10,8),(87,83,12,12)]:
            column('wind_split_fin',x,y,height(i,x,y)-1,r,h,st,root,tilt=(3,-2))
    elif i == 1:
        for sign in (-1,1):
            for row in range(2):
                for j in range(9):
                    y=-94+j*23+RNG.uniform(-2,2);x=sign*(43+row*24+4*math.sin(j*.8))
                    column('jointed_wall',x,y,height(i,x,y)-2,RNG.uniform(10,13),RNG.uniform(35,68)+(10 if row else 0),st,root,tilt=(sign*RNG.uniform(1,5),RNG.uniform(-2,3)),rings=8)
        column('snapped_leaning_crown',-65,24,45,7,27,st,root,tilt=(12,2),rings=8)
    elif i == 2:
        centers=[(-62,-58),(63,-64),(-74,56),(56,65)]
        for cx,cy in centers:
            for j in range(6):
                a=j*2.399;x=cx+math.cos(a)*RNG.uniform(6,21);y=cy+math.sin(a)*RNG.uniform(6,20)
                column('combat_grove',x,y,height(i,x,y)-2,RNG.uniform(6,10),RNG.uniform(14,47),st,root,tilt=(RNG.uniform(-2,2),RNG.uniform(-2,2)))
        # Hero crown near lower basin, away from central fighting space.
        for j in range(5):column('broken_crown',-82+8*math.cos(j*1.1),25+8*math.sin(j*1.1),-8,4,9+j%3*3,st,root)
    elif i == 3:
        for x,y in [(80,82),(92,-85),(-57,83),(-80,-90)]:
            column('overlook_spur',x,y,height(i,x,y)-1,13,18,st,root,tilt=(2,1))
        # Mineral specimen is a landmark nook, no loot implementation.
        for j in range(5):column('glassy_mineral_cairn',57+j%2*5,25+j*3,height(i,57,25),2.5,5+j%3*2,solid,root,tilt=(1,1),mat=GLASS,rings=3)
    else:
        for sign in (-1,1):
            for j in range(8):
                x=sign*(43+j%2*13);y=-85+j*25
                column('old_pass_wall',x,y,height(i,x,y)-2,11,28+j%4*9,st,root,tilt=(sign*2,0),rings=5)
        # Thick angled broken columns tumble across the former road internally.
        for j in range(7):
            x=-29+j*9;y=30+j%3*11
            column('collapsed_oblique_basalt',x,y,2,7,18+j%3*4,st,root,tilt=((18 if j%2 else -20),20),rings=4)
        for j in range(5):rock('rockfall_mass',-30+j*15,48+j%2*9,10,15,13,12,st,root)
    structure=join_objects(st,NAMES[i],root)
    # Openings override is needed for elevated/sunken centers, where the median
    # auto-probe can mistake a shelf for the universal walk plane. No Role override.
    structure['Openings']=','.join(OPENINGS[i]);structure['solid']=True
    if i == 1:structure['Supports']='Traversal,Ambush'
    if i == 2:structure['Supports']='Combat,Ambush'
    # Lava geometry is separate non-solid ambience; no gameplay damage implied.
    if i == 0:
        ribbon('prop_lava_hairline',[(-104,48,height(i,-104,48)+.04),(-95,53,height(i,-95,53)+.04),(-87,60,height(i,-87,60)+.04)],.35,ambient,root,MOLTEN)
    elif i == 1:
        ribbon('prop_low_fissure',[(32,-65,-8),(33,-41,-8),(31,-14,-8),(32,16,-8)],4,ambient,root,MOLTEN)
        for y in (-48,-15):point_light('fissure_uplight',(32,y,-3),15000,(1,.17,.035),ambient,root,7)
    elif i == 2:
        ribbon('prop_basin_heat',[(-71,-10,-9.3),(-69,15,-9.3),(-64,34,-9.3)],3,ambient,root,MOLTEN)
    elif i == 3:
        ribbon('prop_shelf_wound',[(97,-34,height(i,97,-34)+.04),(104,-22,height(i,104,-22)+.04),(103,-9,height(i,103,-9)+.04)],.55,ambient,root,EMBER)
    plants=[[(0,-49,30,1),(1,-67,-27,1.3),(0,86,60,.9)],
            [(2,55,-49,1.3),(3,64,22,1),(1,-35,61,1.2)],
            [(3,-70,4,1.4),(2,-74,30,1),(0,52,44,1.3),(1,69,31,1)],
            [(0,60,41,1.4),(1,51,47,1.1),(2,89,-39,.85)],
            [(2,-28,1,1.4),(3,-36,12,1),(1,29,-61,.9)]][i]
    for kind,x,y,s in plants:place_flora(i,ambient,root,kind,x,y,s)
    # Sparse solid rubble; none inside socket buffers or central combat hub.
    for j in range([5,8,10,4,7][i]):
        x,y=RNG.choice([(-1,1),(1,-1)])
        x*=RNG.uniform(75,100);y*=RNG.uniform(65,93)
        rock('prop_basalt_rubble',x,y,height(i,x,y)+.7,2+j%3,2.5,1.5,solid,root)
    if list(solid.objects):
        p=join_objects(solid,'prop_'+NAMES[i]+'_solid',root);p['solid']=True;p['Animation']='Static';p['Tier']=1
    for obj in ambient.objects:
        if obj.type=='MESH':obj['solid']=False
    root.location=OFFSETS[i]
    return group,root,structure


def point_light(name,loc,power,color,c,root=None,radius=5):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    ob=bpy.data.objects.new(name,data);c.objects.link(ob);ob.parent=root;ob.location=loc
    ob['ReviewOnly']=True


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def validate(chunks):
    report={'units':'one metre = one stud','BlenderVersion':bpy.app.version_string,'chunks':[], 'issues':[
        'No Studio export/upload or runtime registration. Missing BOSS is intentional: this is not a boot-valid kit.',
        'Blender Openings/Supports properties are authoring intent; Studio attribute transfer is not automatic.',
        'Automatic center-median walk-height probe can misread vertical chunks; explicit Openings recommended on import.',
        'Multiple structural materials, procedural bump detail and smooth shading are Blender review appearance. Studio color/normal baking and collision decomposition remain unverified.',
        'No lava damage, loot, boundary system or permanent surrounding-land system implemented.',
        'Minor ENTRY/SIDE surface seams are visual cooled-crust accents; major PATH/COMBAT molten surfaces sit in recessed ground.',
        'SIDE origin is the common connection datum, with center carved to that datum; climb reaches eastern upper shelf.'
    ]}
    for i,(c,root,structure) in enumerate(chunks):
        objects=[o for o in c.all_objects if o.type=='MESH']
        bounds=[];cross=[]
        for o in objects:
            local=root.matrix_world.inverted()@o.matrix_world
            pts=[local@v.co for v in o.data.vertices]
            if any(abs(v.x)>128.001 or abs(v.y)>128.001 for v in pts):cross.append(o.name)
            bounds+=pts
        lo=[min(v[k] for v in bounds) for k in range(3)];hi=[max(v[k] for v in bounds) for k in range(3)]
        # Actual mesh ray probes, not analytic height promises.
        tree=BVHTree.FromPolygons([v.co for v in structure.data.vertices],[tuple(p.vertices) for p in structure.data.polygons])
        sockets=[]
        for s in OPENINGS[i]:
            heights=[];block=0
            for across in (-28,-20,0,20,28):
                for inside in (0,.2,8,16):
                    along=128-max(.01,inside)
                    x,y=(across,along) if s=='N' else (across,-along) if s=='S' else (along,across) if s=='E' else (-along,across)
                    hit,_,_,_=tree.ray_cast(Vector((x,y,140)),Vector((0,0,-1)),200)
                    assert hit is not None,(NAMES[i],s,x,y)
                    heights.append(hit.z)
                    if abs(hit.z)>.001:block+=1
            sockets.append({'side':s,'sample_count':len(heights),'width_studs':56,'buffer_studs':16,'actual_floor_min':min(heights),'actual_floor_max':max(heights),'not_level_samples':block})
            assert not block,(NAMES[i],s,heights)
        assert not cross,cross
        assert triangles(structure)<=10000,(NAMES[i],triangles(structure))
        assert tuple(structure.location)==(0,0,0)
        assert abs(height(i,0,0))<.001
        hub=[]
        if i==2:
            for x in (-24,-12,0,12,24):
                for y in (-32,-16,0,16,32):
                    hit,normal,_,_=tree.ray_cast(Vector((x,y,140)),Vector((0,0,-1)),200)
                    assert hit is not None and abs(hit.z-height(i,x,y))<.05
                    assert normal.z>.9
                    hub.append(hit.z)
        # Cheap floor area measurement from actual upward terrain triangles,
        # excluding top columns by height and steep faces; not a traversal suite.
        structure.data.calc_loop_triangles();usable=0
        walk=structure.data.attributes['authored_walk_surface']
        for t in structure.data.loop_triangles:
            if not walk.data[t.polygon_index].value:continue
            a,b,d=[structure.data.vertices[j].co for j in t.vertices]
            normal=(b-a).cross(d-a)
            if normal.z>0 and normal.normalized().z>.9 and max(a.z,b.z,d.z)<28:
                usable+=normal.z/2
        report['chunks'].append({'name':NAMES[i],'role':ROLES[i],'design':DESIGNS[i],
            'mesh_objects':len(objects),'all_objects':len(list(c.all_objects)),
            'structure_triangles':triangles(structure),'total_mesh_triangles':sum(triangles(o) for o in objects),
            'dimensions_xyz':[round(hi[k]-lo[k],3) for k in range(3)],
            'bounds_local':[lo,hi],'authored_origin':list(structure.location),
            'review_translation':list(root.location),'socket_probes':sockets,'boundary_crossings':cross,
            'gently_sloped_upward_surface_projected_area':round(usable,1),
            'combat_clear_hub':{'width':48,'length':64,'actual_samples':25,'floor_range':[min(hub),max(hub)]} if hub else None,
            'collections':{sub.name:[o.name for o in sub.objects] for sub in c.children},
            'flora_assets':sorted(set(o.get('LibraryAsset') for o in objects if o.get('LibraryAsset'))),
            'ambient_lava_surface_area':round(sum(p.area for o in objects if o.name.startswith('prop_') and 'LibraryAsset' not in o and any(m and m.name=='Ember_Molten' for m in o.data.materials) for p in o.data.polygons),2)})
    report['flora_library']=[{'name':p.name,'triangles':triangles(p),'solid':False} for p in PLANTS]
    report['review_surround']={'objects':len(list(SURROUND.objects)),'mesh_triangles':sum(triangles(o) for o in SURROUND.objects if o.type=='MESH')}
    (OUT/'technical_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


def review_land():
    # Cheap continuous ground plate, visually below the inset authored chunks.
    mesh('review_only_continental_ground',[(-2300,-2300,-20),(2500,-2300,-20),(2500,2600,-20),(-2300,2600,-20)],[(0,1,2,3)],COOLED,SURROUND)
    for j in range(22):
        a=math.tau*j/22;r=RNG.uniform(1200,1900)
        x=math.cos(a)*r;y=math.sin(a)*r+200
        sx=RNG.uniform(180,350);sy=RNG.uniform(180,330);h=RNG.uniform(150,360)
        vs=[]
        for ring in (0,1):
            for k in range(12):
                ang=k*math.tau/12;rad=RNG.uniform(.8,1.15)*(1 if ring==0 else .42)
                vs.append((x+math.cos(ang)*sx*rad,y+math.sin(ang)*sy*rad,-20 if ring==0 else h*RNG.uniform(.3,.65)))
        vs.append((x+sx*.18,y-sy*.12,h))
        fs=[]
        for k in range(12):
            q=(k+1)%12;fs += [(k,q,q+12),(k,q+12,k+12),(k+12,q+12,24)]
        mesh('review_only_jagged_ridge',vs,fs,DISTANT,SURROUND)
    # Continuous inset collar meets actual perimeter elevations; no separate
    # boulder necklace and no exposed square sides. Only review geometry overlaps.
    def surround_height(x,y):
        near=[]
        for i,(ox,oy,_) in enumerate(OFFSETS):
            lx=max(-128,min(128,x-ox));ly=max(-128,min(128,y-oy))
            d=math.hypot(x-ox-lx,y-oy-ly)
            near.append((d,height(i,lx,ly)))
        d,z=min(near,key=lambda q:q[0])
        return z*(1-smoothstep(0,160,d))-18*smoothstep(0,160,d)
    xs=list(range(-384,641,16));ys=list(range(-640,897,16))
    vs=[(x,y,surround_height(x,y)) for y in ys for x in xs];fs=[];n=len(xs)
    for j in range(len(ys)-1):
        for k in range(n-1):
            x=xs[k]+8;y=ys[j]+8
            if any(abs(x-ox)<128 and abs(y-oy)<128 for ox,oy,_ in OFFSETS):continue
            a=j*n+k;fs.extend([(a,a+1,a+n+1),(a,a+n+1,a+n)])
    collar=mesh('review_only_fitted_ash_continuation',vs,fs,COOLED,SURROUND)
    collar.data.materials.append(ASH)
    for p in collar.data.polygons:
        p.use_smooth=True
        x,y,_=p.center
        if -280<y<-128 and abs(x)<260:p.material_index=1
    # Vast lava field outward of overlook; sparse cooled crust divides hot flows.
    ribbon('review_only_distant_lava_field',[(540,-150,-18),(730,110,-18),(670,400,-18),(920,710,-18)],150,SURROUND,None,MOLTEN)
    for j in range(7):rock('review_only_cooled_flow',590+j*54,90+j*76,-16,75,110,7,SURROUND,None,COOLED)
    for o in SURROUND.objects:o['ReviewOnly']=True


def camera(name,loc,target,lens=38):
    data=bpy.data.cameras.new(name);data.lens=lens;data.clip_end=12000
    ob=bpy.data.objects.new(name,data);REVIEW.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob


def save_and_render(chunks,report):
    scene=bpy.context.scene
    # Write independent collection libraries, not scene IDs: Blender 5.2's
    # partial scene writer crashes in BKE_view_layer_copy_data on this machine.
    for i,(c,root,obj) in enumerate(chunks):
        root.location=(0,0,0);bpy.context.view_layer.update()
        bpy.data.libraries.write(str(OUT/(NAMES[i]+'.blend')),{c},fake_user=True)
        root.location=OFFSETS[i]
    bpy.context.view_layer.update()
    shots=[('01_entry',(92,-373,42),(-10,-244,9),32),
           ('02_column_pass',(6,-104,7),(0,35,25),25),
           ('03_column_forest',(119,135,66),(-10,285,4),33),
           ('04_lava_overlook',(346,263,43),(800,390,-2),27),
           ('05_collapsed_pass',(5,412,9),(0,558,22),28),
           ('06_grounded_region',(1040,-1050,800),(40,170,0),43),
           ('07_flora_library',(17,-535,16),(17,-500,2),28),
           ('08_side_shelf',(467,125,135),(272,280,17),35)]
    cams=[camera(*s) for s in shots]
    scene.camera=cams[-1]
    scene['README']='Five-piece prototype only. Surround_REVIEW_ONLY never exports. Individual files are chunk-local.'
    scene['ReferenceImages']='docs/design/emberfall/EMBERFALL_REFERENCE_01.png; EMBERFALL_REFERENCE_02.png'
    # Comfortable whole-set solid viewport when opened interactively.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_distance=1150
                area.spaces.active.region_3d.view_location=(60,170,20)
                area.spaces.active.clip_end=12000
                area.spaces.active.shading.color_type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallPrototype.blend'))
    for cam in cams:
        scene.camera=cam;scene.render.filepath=str(OUT/(cam.name+'.png'))
        bpy.ops.render.render(write_still=True)


def main():
    global PLAYABLE,LIBRARY,SURROUND,REVIEW,PLANTS
    global BASALT,ASH,COOLED,MOLTEN,GLASS,CHARRED,DRAINED,DRAINED_STEM,EMBER,DISTANT
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):bpy.data.collections.remove(c)
    BASALT=material('Ember_Basalt',(.045,.058,.074))
    ASH=material('Ember_Ash',(.19,.215,.24))
    COOLED=material('Ember_CooledLava',(.075,.09,.11))
    MOLTEN=material('Ember_Molten',(1,.09,.004),2.2)
    GLASS=material('Ember_Glass',(.025,.041,.05),roughness=.28)
    CHARRED=material('Ember_CharredFlora',(.025,.022,.023))
    # sRGB #bdbc42 converted to linear values for Blender node colors.
    def linear(v):return ((v/255+.055)/1.055)**2.4
    DRAINED=material('Ember_DrainedFlora',tuple(linear(v) for v in (189,188,66)))
    DRAINED_STEM=material('Ember_DrainedStem',(.20,.20,.07))
    EMBER=material('Ember_DeepHeat',(.5,.023,.004),1.4)
    DISTANT=material('Ember_DistantAsh',(.125,.16,.19))
    PLAYABLE=collection('EF_PROTOTYPE_5_CHUNKS');LIBRARY=collection('PropLibrary')
    SURROUND=collection('Surround_REVIEW_ONLY');REVIEW=collection('Cameras_Lights_REVIEW_ONLY')
    PLANTS=[plant_asset(n,k) for k,n in enumerate(['prop_drained_wax_rosette','prop_drained_seed_shrub','prop_charred_ember_rose','prop_charred_thorn_pod'])]
    chunks=[build_chunk(i) for i in range(5)]
    review_land()
    for j,p in enumerate(PLANTS):
        obj=bpy.data.objects.new('review_only_'+p.name,p.data);REVIEW.objects.link(obj)
        obj.location=(j*11,-500,.03);obj.scale=(1.5,1.5,1.5);obj['ReviewOnly']=True
    mesh('review_only_flora_display',[(-8,-508,0),(42,-508,0),(42,-492,0),(-8,-492,0)],[(0,1,2,3)],ASH,REVIEW)['ReviewOnly']=True
    # Human scale proxies are review-only and excluded from chunk counts.
    for i,x,y in [(0,15,-300),(1,7,-82),(2,3,251),(3,310,284),(4,5,458)]:
        localx=x-OFFSETS[i][0];localy=y-OFFSETS[i][1]
        column('review_only_5_stud_person',x,y,height(i,localx,localy),.65,5,REVIEW,None,mat=ASH,rings=2)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.20,.27,.34,1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.7
    light=bpy.data.lights.new('review_overcast_sun','SUN');light.energy=2.2;light.angle=.5
    ob=bpy.data.objects.new('review_overcast_sun',light);REVIEW.objects.link(ob);ob.rotation_euler=(.5,-.6,-.4)
    scene.view_settings.view_transform='AgX'
    bpy.context.view_layer.update()
    report=validate(chunks)
    save_and_render(chunks,report)
    print('EMBERFALL_PROTOTYPE_COMPLETE',json.dumps([{'name':r['name'],'tris':r['structure_triangles']} for r in report['chunks']]))


if __name__=='__main__':main()
