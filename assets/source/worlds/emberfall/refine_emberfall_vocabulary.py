"""Continue the saved/live foundation: geological drama and varied disaster vocabulary.

Protected launcher only. No runtime changes, kit growth, collision or export.
"""
import bpy
import bmesh
import importlib.util
import json
import math
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_FoundationReview')
MAIN = OUT/'EmberfallFoundation.blend'
IMAGES = OUT/'VocabularyReview'
REPORT = {}
HEAT_TYPES = ['tiny_heat_crack','medium_heat_crack','narrow_lava_seam',
              'buried_heat_vent','small_molten_pocket','one_sided_fissure',
              'contained_channel','broad_basin']
RUINS = ['snapped_corner','collapsed_gateway','broken_stair','shattered_barricade',
         'buried_foundation','split_facade','toppled_wall_mass','burned_structure']
BASALTS = ['fractured_wall','broken_cluster','stump_field','buried_column_line',
           'shattered_ridge','leaning_outcrop','shelf_support','collapsed_fan']
GRAMMAR = ['Interrupted open basin','Asymmetrical cut shelf','Broad plateau with slumped rear rise',
           'Shallow collapsed shrine depression','Broken ascent with tilted shoulder',
           'Raised ruin terrace above lower outer field']


def module(filename, name):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)


def datum(y):
    return 56*smooth(152,360,y)


def polygon_distance(x,y,outline):
    inside=False
    distance=1e9
    for a,b in zip(outline,outline[1:]+outline[:1]):
        ax,ay=a; bx,by=b
        dx,dy=bx-ax,by-ay
        t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
        distance=min(distance,math.hypot(x-ax-t*dx,y-ay-t*dy))
        if (ay>y)!=(by>y) and x < ax+(y-ay)*(bx-ax)/(by-ay):
            inside=not inside
    return distance if inside else -distance


def landform(name,x,y,index):
    if 'entry_' in name or name=='open_ashland':
        p=[(-103,-67),(-54,-59),(-47,-23),(-68,-8),(-91,9),(-110,-20)]
        d=polygon_distance(x,y,p)
        return 19*smooth(-12,2,d)+6*smooth(7,13,d)-2.5*smooth(-70,-25,y)*(1-smooth(5,70,y))*(1-smooth(8,42,abs(x)))
    if 'path_wasteland' in name:
        d=polygon_distance(x,y,[(-112,-73),(-66,-61),(-57,-7),(-72,4),(-64,64),(-101,91),(-114,18)])
        return 17*smooth(-10,1,d)+9*smooth(6,11,d)-3*smooth(-65,-20,y)*(1-smooth(27,72,y))*(1-smooth(25,46,x))
    if 'combat_wasteland' in name:
        d=polygon_distance(x,y,[(-108,20),(-58,13),(-27,58),(-48,99),(-103,86)])
        return 22*smooth(-15,1,d)+6*smooth(7,12,d)+3*smooth(-75,30,y)*(1-smooth(50,89,y))*(1-smooth(30,65,abs(x)))
    if 'side_' in name:
        d=polygon_distance(x,y,[(-106,-41),(-71,-62),(-44,-12),(-67,49),(-110,37)])
        basin=polygon_distance(x,y,[(-24,-28),(26,-41),(37,-1),(13,26),(-19,13)])
        return 20*smooth(-13,1,d)-4.5*smooth(-11,5,basin)
    if 'causeway' in name:
        d=polygon_distance(x,y,[(-113,-32),(-73,-41),(-49,14),(-64,66),(-111,81)])
        return 21*smooth(-13,1,d)+7*smooth(5,11,d)-3*smooth(-55,-20,y)*(1-smooth(42,71,y))*(1-smooth(13,35,abs(x)))
    if 'gateworks' in name:
        d=polygon_distance(x,y,[(-113,31),(-44,39),(16,68),(-8,106),(-107,99)])
        return 24*smooth(-14,1,d)+8*smooth(7,12,d)-5*smooth(25,54,x)*(1-smooth(79,107,x))*(1-smooth(50,87,abs(y)))
    # Scenery alternates different footprints, interruption directions and mass.
    if name=='low_lava_terrain':
        return 10*smooth(-15,2,polygon_distance(x,y,[(-113,-73),(-55,-82),(-37,-42),(-67,21),(-108,48)]))
    choices=[([(-108,-57),(-32,-89),(12,-29),(-31,19),(-98,57)],29),
             ([(-91,12),(-19,-7),(78,44),(49,97),(-88,87)],34),
             ([(-87,-84),(-9,-72),(17,-6),(-25,16),(-92,-11)],18),
             ([(13,-94),(84,-71),(104,-7),(67,11),(39,73),(8,49)],27)]
    p,h=choices[index%4]
    d=polygon_distance(x,y,p)
    amplitude={'ruined_outskirts':.2,'ash_faultland':.48,'infected_outskirts':.42,'fortress_silhouette':.68}.get(name,1)
    return amplitude*(h*smooth(-17,2,d)+7*smooth(10,17,d))


def ray(tree,x,y):
    p,_,_,_=tree.ray_cast(Vector((x,y,400)),Vector((0,0,-1)))
    return p.z if p else 0


def shelf_outline(name,index):
    if 'entry_' in name or name=='open_ashland':return [(-103,-67),(-54,-59),(-47,-23),(-68,-8),(-91,9),(-110,-20)]
    if 'path_wasteland' in name:return [(-112,-73),(-66,-61),(-57,-7),(-72,4),(-64,64),(-101,91),(-114,18)]
    if 'combat_wasteland' in name:return [(-108,20),(-58,13),(-27,58),(-48,99),(-103,86)]
    if 'side_' in name:return [(-106,-41),(-71,-62),(-44,-12),(-67,49),(-110,37)]
    if 'causeway' in name:return [(-113,-32),(-73,-41),(-49,14),(-64,66),(-111,81)]
    if 'gateworks' in name:return [(-113,31),(-44,39),(16,68),(-8,106),(-107,99)]
    if name=='low_lava_terrain':return [(-113,-73),(-55,-82),(-37,-42),(-67,21),(-108,48)]
    return [[(-108,-57),(-32,-89),(12,-29),(-31,19),(-98,57)],
            [(-91,12),(-19,-7),(78,44),(49,97),(-88,87)],
            [(-87,-84),(-9,-72),(17,-6),(-25,16),(-92,-11)],
            [(13,-94),(84,-71),(104,-7),(67,11),(39,73),(8,49)]][index%4]


def terrain_pass(terrains):
    for index,o in enumerate(terrains):
        old=study.tree(o)
        root=o.parent
        name=study.family(o)
        is_source=root.name.endswith('LOCAL_ORIGIN')
        original_z=root.location.z
        m=o.matrix_world.copy()
        has_lava=name in ('path_wasteland_fault','side_wasteland_shrine','low_lava_terrain')
        oldcenterbase=0 if is_source else study.datum(root.location.y)-original_z
        correction=(.38*(ray(old,0,0)-oldcenterbase)+landform(name,0,0,index)) if name in study.GRAMMAR else 0
        def elevation(x,y):
                world=m@Vector((x,y,0))
                base=0 if is_source else datum(world.y)-original_z
                oldbase=0 if is_source else study.datum(world.y)-original_z
                relief=landform(name,x,y,index)
                # Retain useful previous faces, including the actual existing cavities.
                prior=ray(old,x,y)-oldbase
                new=.38*prior+relief-correction
                if has_lava:
                    retain=smooth(38,58,x)
                    if name=='side_wasteland_shrine':
                        retain*=1-smooth(36,68,abs(y))
                    new=new*(1-retain)+prior*retain
                edge=128-max(abs(x),abs(y))
                blend=smooth(24,48,edge)
                # Shared world-field edge stations in this assembled study. Uniform
                # border topology matches after quarter-turns; authored metadata only.
                wx,wy=(x,y) if is_source else (world.x,world.y)
                drift=1.15*math.sin(wx*.014)*math.sin(wy*.008)*smooth(28,85,abs(wx))
                z=base+drift*(1-blend)+new*blend
                return z
        outline=shelf_outline(name,index)
        points=[]; edges=[]
        for j in range(41):
            for i in range(41):
                x,y=-128+i*6.4,-128+j*6.4
                if i in (0,40) or j in (0,40) or abs(polygon_distance(x,y,outline))>19:
                    points.append(Vector((x,y)))
        center=Vector((sum(x for x,y in outline)/len(outline),sum(y for x,y in outline)/len(outline)))
        # Constrained ledge/foot/top outlines break the old raster-stair silhouette.
        # Clamp just inside the seam ease so a landmark never ends on the border.
        factors=(1.24,1,.86) if index%3==0 else (1.22,1.02,.91,.76) if index%3==1 else (1.25,1.06,.9)
        for factor in factors:
            start=len(points)
            ring=[center+(Vector(p)-center)*factor for p in outline]
            for p in ring:
                p.x=max(-102,min(102,p.x));p.y=max(-102,min(102,p.y))
            points.extend(ring)
            edges.extend((start+k,start+(k+1)%len(ring)) for k in range(len(ring)))
        coords,_,faces,_,_,_=delaunay_2d_cdt(points,edges,[],0,1e-5)
        vs=[(p.x,p.y,elevation(p.x,p.y)) for p in coords]
        surface_count=len(vs)
        border=sorted([i for i,p in enumerate(coords) if max(abs(p.x),abs(p.y))>127.99],key=lambda i:math.atan2(coords[i].y,coords[i].x))
        faces=[tuple(f) for f in faces]
        n=len(vs)
        vs += [(vs[a][0],vs[a][1],vs[a][2]-46) for a in border]
        faces += [(a,n+k,n+(k+1)%len(border),border[(k+1)%len(border)]) for k,a in enumerate(border)]
        faces.append(tuple(reversed(range(n,len(vs)))))
        temporary=helper.mesh('terrain_work',vs,faces,list(o.data.materials),root.users_collection[0],root)
        olddata=o.data
        o.data=temporary.data
        bpy.data.objects.remove(temporary,do_unlink=True)
        for p in o.data.polygons:
            p.material_index=0 if p.normal.z>.68 else 1
            p.use_smooth=p.normal.z>.9
            if p.index>=len(faces)-len(border)-1:
                p.material_index=1
            if p.center.x**2+p.center.y**2 < 700:
                p.material_index=0
        o['SeamBandStuds']=24
        o['BorderStations']=41
        o['SurfaceVertexCount']=surface_count
        o['TerrainIdentity']=GRAMMAR[list(study.GRAMMAR).index(name)] if name in study.GRAMMAR else 'Interrupted '+name+' / composition '+str(index%4)
        trees[o.name]=study.tree(o)
        # Preserve existing object ground offsets rather than bury current art.
        for child in root.children:
            if child==o or child.type!='MESH' or child.name.startswith(('molten_','rooted_crust_','buried_broken_road')):
                continue
            x,y=child.location.x,child.location.y
            if max(abs(x),abs(y))<=125:
                child.location.z+=ray(trees[o.name],x,y)-ray(old,x,y)
        # Road foundations are already local, vertex-grounded surfaces.
        for child in root.children:
            if child.name.startswith('buried_broken_road'):
                child.data=child.data.copy()
                for v in child.data.vertices:
                    x,y=v.co.x,v.co.y
                    v.co.z += ray(trees[o.name],x,y)-ray(old,x,y)
        REPORT.setdefault('terrain',[]).append({'object':o.name,'identity':o['TerrainIdentity'],'range':max(v[2] for v in vs[:surface_count])-min(v[2] for v in vs[:surface_count])})


def ground(t,x,y):
    return ray(trees[t.name],x,y)


def prism(name,root,outline,height,material,tag=None):
    t=study.terrain_for(root); c=root.users_collection[0]
    z=ground(t,sum(x for x,y in outline)/len(outline),sum(y for x,y in outline)/len(outline))
    vs=[(x,y,z-.65) for x,y in outline]+[(x,y,z+height*(.9+.1*math.sin(i*2.1))) for i,(x,y) in enumerate(outline)]
    n=len(outline)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=helper.mesh(name,vs,faces,[material,fresh],c,root,[0,0]+[1 if i%3==1 else 0 for i in range(n)])
    center=Vector((sum(x for x,y in outline)/n,sum(y for x,y in outline)/n,z))
    for v in o.data.vertices:v.co-=center
    o.location=center
    if tag:o['Archetype']=tag
    return o


def heat(root,kind,points,width):
    t=study.terrain_for(root); c=root.users_collection[0]
    vs=[]; fs=[]; bank=[]
    for j,(x,y) in enumerate(points):
        tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])
        tangent.normalize(); normal=Vector((-tangent.y,tangent.x))
        w=width*(.25 if j in (0,len(points)-1) else .82+.2*math.sin(j*1.7))
        for side in (-1,1):
            xx,yy=x+normal.x*w*side,y+normal.y*w*side
            vs.append((xx,yy,ground(t,xx,yy)+.045))
        for side in (-1,1):
            for multiplier,dz in ((1.0,.06),(1.5,.45),(2.1,-.25)):
                if kind=='one_sided_fissure' and side==1 and multiplier==1.5:dz=2.2
                xx,yy=x+normal.x*w*side*multiplier,y+normal.y*w*side*multiplier
                bank.append((xx,yy,ground(t,xx,yy)+dz))
    for j in range(len(points)-1):
        a=j*2; fs.append((a,a+1,a+3,a+2))
    o=helper.mesh('heat_'+kind,vs,fs,[heatmat if width<1 else lava],c,root)
    colors=o.data.color_attributes.new(name='MoltenEdge',type='FLOAT_COLOR',domain='POINT')
    for j,item in enumerate(colors.data):
        item.color=(.72,.72,.72,1) if j not in (0,1,len(vs)-2,len(vs)-1) else (.12,.12,.12,1)
    o['Archetype']=kind; o['HeatFeature']=True
    bf=[]
    for j in range(len(points)-1):
        for side in (0,3):
            for k in (0,1):
                a=j*6+side+k;bf.append((a,a+1,a+7,a+6))
    lips=helper.mesh('buried_split_lips_'+kind,bank,bf,[rock],c,root)
    lips['HeatFeature']=True
    REPORT.setdefault('heat_features',[]).append({'root':root.name,'type':kind,'half_width':width,'length':sum(math.dist(a,b) for a,b in zip(points,points[1:]))})
    return o


def heat_pass():
    roots=[bpy.data.objects[n+'_ORIGIN'] for n in study.GRAMMAR]
    plans=[(roots[0],'tiny_heat_crack',[(-53,-12),(-49,-9),(-45,-11),(-41,-7)],.16),
           (roots[1],'medium_heat_crack',[(-37,39),(-29,44),(-23,40),(-13,49),(-4,47)],.6),
           (roots[2],'narrow_lava_seam',[(48,-67),(54,-59),(50,-47),(62,-38),(66,-28)],1.25),
           (roots[4],'buried_heat_vent',[(-55,46),(-49,49),(-40,47),(-34,53)],.85),
           (roots[3],'small_molten_pocket',[(-2,-20),(1,-17),(7,-16),(11,-10)],2.6),
           (roots[5],'one_sided_fissure',[(61,48),(70,39),(68,25),(79,14),(82,4)],2.2)]
    for root,kind,pts,w in plans:
        heat(root,kind,pts,w)
        if kind=='buried_heat_vent':
            prism('partially_buried_vent_roof',root,[(-48,47),(-43,46),(-39,50),(-45,51)],.3,rock)
        if kind=='small_molten_pocket':
            prism('pocket_cooled_crust_remnant',root,[(3,-18),(5,-17),(5,-15),(2,-16)],.18,rock)
    for o in list(study.visible_meshes(bpy.context.scene)):
        if o.name.startswith('molten_'):
            kind='broad_basin' if 'basin' in o.name else 'contained_channel' if 'channel' in o.name else 'small_molten_pocket'
            o['Archetype']=kind
            REPORT.setdefault('heat_features',[]).append({'root':o.parent.name,'type':kind,'retained_geometry':True})
    # One small ring event in the approach; do not scatter heat over every tile.
    root=bpy.data.objects['ring_origin_-1_0']
    heat(root,'buried_heat_vent',[(-33,10),(-27,15),(-20,12),(-14,19)],.8)
    for o in list(bpy.data.objects):
        if o.name.startswith('heat_inside_fault_face'):
            o.hide_render=True; o.hide_set(True)
    smoke_source=next(o for o in bpy.context.scene.objects if o.name.startswith('smoke_from_active'))
    for root,point in [(roots[1],(-24,44)),(roots[4],(-44,49)),(roots[5],(76,25))]:
        t=study.terrain_for(root)
        o=bpy.data.objects.new('localized_heat_failure_smoke_REVIEW',smoke_source.data)
        root.users_collection[0].objects.link(o);o.parent=root
        o.location=(*point,ground(t,*point)+7)
        o.scale=(2.3,2.8,8)
        o['ReviewOnly']='Static vent smoke proxy; future ambience data, no runtime changes.'


def ruins_pass(terrains):
    targets=[]
    for t in terrains:
        root=t.parent
        panels=[o for o in root.children if o.name.startswith('recent_split_wall')]
        if not panels:continue
        targets.append((t,root,panels))
    for index,(t,root,panels) in enumerate(targets):
        name=study.family(t)
        kind='collapsed_gateway' if 'gateworks' in name else 'broken_stair' if 'causeway' in name else RUINS[index%8]
        anchor=panels[0].location.copy()
        # Keep selected previous wall corners, replace repeated panels elsewhere.
        if kind!='snapped_corner':
            for o in panels:
                for child in list(o.children):bpy.data.objects.remove(child,do_unlink=True)
                bpy.data.objects.remove(o,do_unlink=True)
        x,y=anchor.x,anchor.y
        def block(label,dx,dy,w,d,h,mat=masonry):
            return prism(label,root,[(x+dx-w/2,y+dy-d/2),(x+dx+w/2,y+dy-d/2+.3),(x+dx+w/2-.8,y+dy+d/2),(x+dx-w/2,y+dy+d/2-.5)],h,mat,kind)
        if kind=='collapsed_gateway':
            block('gateway_left_failure',-12,0,8,7,23)
            block('gateway_right_stump',12,2,7,8,12)
            o=block('gateway_fallen_lintel',2,-8,21,5,4,fresh);o.rotation_euler.z=.22
        elif kind=='broken_stair':
            for j in range(5):block('snapped_approach_stair',1+(.7 if j>2 else 0),-13+j*4,12-j*.5,4,1.2+j*1.45)
            block('stair_split_cheek',-9,-3,3,17,7)
        elif kind=='shattered_barricade':
            block('barricade_low_failed_mass',-4,0,18,3,3.5)
            o=block('barricade_snapped_post',10,2,1.4,1.8,7,wood);o.rotation_euler.y=.3
        elif kind=='buried_foundation':
            block('foundation_remaining_footing',0,0,23,4,1.4)
            block('foundation_return',-10,6,4,13,2)
        elif kind=='split_facade':
            block('facade_pier_left',-8,0,6,4,16)
            block('facade_pier_right',7,0,5,4,9)
            block('facade_broken_sill',0,0,13,4,3)
        elif kind=='toppled_wall_mass':
            o=block('recent_toppled_intact_mass',0,0,21,8,5,fresh);o.rotation_euler=(.14,.12,.4)
            block('wall_source_fresh_stub',-12,6,5,4,6)
        elif kind=='burned_structure':
            for j in (-1,1):
                o=block('burned_frame_snapped_post',j*7,0,1.8,1.8,9+j*2,wood);o.rotation_euler.y=j*.16
            block('burned_roof_ground_section',2,-5,17,6,1.5,bpy.data.materials['EF_SnappedSlateRoof'])
        else:
            for o in panels:o['Archetype']=kind
        # All fragments share materials and course dimensions with the later gate.
        for o in root.children:
            if o.name.startswith(('fresh_fallen','localized_collapse')):o['RelatedStructure']='Roadside defensive precinct'
        REPORT.setdefault('ruins',[]).append({'root':root.name,'archetype':kind})


def basalt_pass(terrains):
    targets=[t for t in terrains if any(o.name.startswith('embedded_basalt_group') for o in t.parent.children)]
    for index,t in enumerate(targets):
        root=t.parent; olds=[o for o in root.children if o.name.startswith('embedded_basalt_group')]
        x,y=olds[0].location.x,olds[0].location.y
        for o in olds:bpy.data.objects.remove(o,do_unlink=True)
        kind=BASALTS[index%len(BASALTS)]
        count=6 if kind in ('fractured_wall','buried_column_line','stump_field') else 4
        for j in range(count):
            if kind=='stump_field': dx,dy,h=(j%3)*7,(j//3)*8,2.5+(j%3)*1.5
            elif kind=='fractured_wall': dx,dy,h=j*4,0,16+(j%3)*3
            elif kind=='buried_column_line':dx,dy,h=j*5,j*1.8,3+(j%3)*2
            elif kind=='shattered_ridge':dx,dy,h=j*7,j*3,5+j*2
            elif kind=='shelf_support':dx,dy,h=j*4,4*(j%2),13-j*1.4
            else:dx,dy,h=j*5,4*(j%2),9+j*2
            xx,yy=x+dx,y+dy
            outline=[(xx+3.2*math.cos(k*math.tau/6),yy+3.2*math.sin(k*math.tau/6)) for k in range(6)]
            o=prism('basalt_'+kind,root,outline,h,rock,kind)
            o['EmbeddedFormation']=True
            if kind in ('collapsed_fan','leaning_outcrop'):
                # Tilt geometry about its rooted base, not around the scene origin.
                for v in o.data.vertices:
                    rise=v.co.z
                    v.co.x+=rise*(.85 if kind=='collapsed_fan' else .4)
                    v.co.y+=rise*(j-1.5)*.15
                    if kind=='collapsed_fan':v.co.z=rise*.3
            elif kind=='shattered_ridge':
                for v in o.data.vertices:
                    if v.index>=6:v.co.x+=3;v.co.y+=1.5
        REPORT.setdefault('basalt',[]).append({'root':root.name,'archetype':kind})


def flora_pass(scene):
    source=bpy.data.objects['prop_surviving_ash_rosette']
    library=helper.coll('FloraInfection_SOURCE_ONLY',bpy.data.collections['ReuseLibrary_SOURCE_ONLY'])
    library.hide_render=True
    pale=bpy.data.materials['Ember_OldFlora']; black=bpy.data.materials['Ember_InvasiveGrowth']
    scorch=bpy.data.materials['Ember_ScorchedStrata']; ember=bpy.data.materials['Ember_TissueHeat']
    variants=[]
    for state,amount in [('healthy',0),('early',.18),('partial',.5),('corrupted',1)]:
        for variant in range(2):
            d=source.data.copy();d.materials.clear()
            for m in (pale,black,scorch,ember):d.materials.append(m)
            for v in d.vertices:
                x,y,z=v.co
                angle=(math.atan2(y,x)+math.tau)%math.tau
                threshold=math.tau*amount+.23*math.sin(math.hypot(x,y)*2.3)
                infected=amount==1 or amount>0 and angle<threshold
                if infected:
                    v.co.z=z*(1.15+amount*.6)+.22*math.hypot(x,y)*amount
                    v.co.x*=1-.2*amount
                    v.co.y*=1-.1*amount
                if variant:
                    v.co.x*=.82
                    v.co.y*=1.08
                    v.co.z*=1.2
            for p in d.polygons:
                center=sum((d.vertices[k].co for k in p.vertices),Vector())/len(p.vertices)
                angle=(math.atan2(center.y,center.x)+math.tau)%math.tau
                infected=amount==1 or amount>0 and angle<math.tau*amount+.23*math.sin(center.length*2.3)
                p.material_index=1 if infected else 0
                if infected and p.index%11==2:p.material_index=2
                if infected and p.index%31==4:p.material_index=3
            o=bpy.data.objects.new('prop_'+state+'_ash_rosette_'+('curled' if variant else 'spread'),d)
            library.objects.link(o)
            o['InfectionState']=state;o['Variant']='curled' if variant else 'spread'
            o['TakeoverFraction']=amount
            if state=='corrupted':
                # Root-tissue forks and dark curled petal tips, genuine added geometry.
                bm=bmesh.new();bm.from_mesh(d)
                for j in range(4):
                    angle=j*1.8+.3
                    x,y=.12*math.cos(angle),.12*math.sin(angle)
                    rings=[]
                    for k in range(4):
                        z=.25+k*.55
                        radius=.14*(1-k*.23)
                        rings.append([bm.verts.new((x+k*.17*math.cos(angle),y+k*.17*math.sin(angle),z+radius*math.sin(a*math.tau/5))) for a in range(5)])
                        for a,v in enumerate(rings[-1]):v.co.x+=radius*math.cos(a*math.tau/5)
                    for k in range(3):
                        for a in range(5):
                            face=bm.faces.new((rings[k][a],rings[k][(a+1)%5],rings[k+1][(a+1)%5],rings[k+1][a]));face.material_index=1 if a!=2 else 3
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
            variants.append(o)
    flora=[o for o in study.visible_meshes(scene) if o.get('ReuseSource','').startswith('prop_')]
    pockets={}
    for o in flora:pockets.setdefault(o.parent,[]).append(o)
    for root,obs in pockets.items():
        t=study.terrain_for(root);name=study.family(t)
        states=[0,0,1,0] if 'entry_' in name or name=='open_ashland' else [0,2,3,2] if 'path_wasteland' in name else [4,6,7,5] if 'gateworks' in name or 'infected' in name else [2,4,6,5]
        for j,o in enumerate(sorted(obs,key=lambda o:o.name)):
            src=variants[states[j%4]]
            o.data=src.data
            o['ReuseSource']=src.name;o['InfectionState']=src['InfectionState']
            # Keep previous small scale; cap taller curled/corrupted variant bounds.
            zmax=max(v.co.z for v in o.data.vertices)
            scale=min(o.scale.x,2.5/max(.01,zmax))
            o.scale=(scale,)*3
            o.location.z=ground(t,o.location.x,o.location.y)+.025
    REPORT['flora']={'states':4,'variants':8,'count_before':len(flora),'count_after':len(flora),
                     'placements_by_state':{s:sum(o.get('InfectionState')==s for o in flora) for s in ['healthy','early','partial','corrupted']}}
    return variants


def background_apron(terrains):
    visible=[t for t in terrains if not t.parent.name.endswith('LOCAL_ORIGIN')]
    centers={(round(t.parent.location.x),round(t.parent.location.y)) for t in visible}
    def occupied(x,y):
        return any(abs(x-cx)<127.999 and abs(y-cy)<127.999 for cx,cy in centers)
    # Tile-sized exterior patches cannot bridge across the concave kit outline.
    # Shared indices and 41 edge stations meet the current ring exactly.
    vs=[]; faces=[]; lookup={}
    def vertex(x,y):
        key=(round(x,4),round(y,4))
        if key not in lookup:
            lookup[key]=len(vs)
            z=datum(y)+1.15*math.sin(x*.014)*math.sin(y*.008)*smooth(28,85,abs(x))
            vs.append((x,y,z))
        return lookup[key]
    for cx in range(-2048,2049,256):
        for cy in range(-2048,2049,256):
            if (cx,cy) in centers:continue
            ring=[]
            for side in range(4):
                for j in range(40):
                    a=-128+j*6.4
                    x,y=[(cx+a,cy-128),(cx+128,cy+a),(cx-a,cy+128),(cx-128,cy-a)][side]
                    ring.append(vertex(x,y))
            middle=vertex(cx,cy)
            faces.extend((middle,ring[j],ring[(j+1)%len(ring)]) for j in range(len(ring)))
    apron=bpy.data.objects['continuous_land_apron_REVIEW']
    temp=helper.mesh('apron_work',vs,faces,[bpy.data.materials['EF_AshGround']],apron.users_collection[0])
    apron.data=temp.data;bpy.data.objects.remove(temp,do_unlink=True)
    for p in apron.data.polygons:p.use_smooth=True
    apron['BackdropMethod']='External land only; follows assembled perimeter, no intersecting underlay or visible tile skirt.'
    REPORT['backdrop']='Conforming external land, excludes all occupied kit footprints; not runtime scenery logic.'


def render(scene,name,loc,target,ortho=None):
    c=study.camera('VocabularyReview_'+name,loc,target,36,ortho)
    scene.camera=c;scene.render.filepath=str(IMAGES/(name+'.png'))
    bpy.ops.render.render(write_still=True)


def gallery(scene,name,groups,span=62):
    # Exact copies of current placed art, temporary isolated gallery only.
    saved={o:o.hide_render for o in scene.objects if o.type in ('MESH','CURVE')}
    for o in saved:o.hide_render=True
    c=helper.coll('Temporary_'+name)
    clones=[]
    for i,objects in enumerate(groups):
        if not objects:continue
        coords=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
        minimum=Vector(tuple(min(p[k] for p in coords) for k in range(3)))
        maximum=Vector(tuple(max(p[k] for p in coords) for k in range(3)))
        center=(minimum+maximum)/2
        scale=min(1,span*.75/max(maximum.x-minimum.x,maximum.y-minimum.y,maximum.z-minimum.z,.01))
        offset=Vector(((i%4)*span,(i//4)*span,0))
        for old in objects:
            o=old.copy();o.data=old.data
            c.objects.link(o);o.parent=None;o.matrix_world=old.matrix_world.copy()
            o.matrix_world.translation-=center
            o.matrix_world.translation*=scale
            o.scale*=scale
            o.matrix_world.translation+=offset+Vector((0,0,(maximum.z-minimum.z)*scale/2))
            o.hide_render=False;clones.append(o)
    bpy.context.view_layer.update()
    center=Vector((span*1.5,span*.5,0))
    render(scene,name,center+Vector((85,-180,170)),center+Vector((0,0,3)),span*4.1)
    for o in clones:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(c)
    for o,hidden in saved.items():o.hide_render=hidden


def reviews(scene,variants,terrains):
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    shots=[('assembled_top',(100,0,2300),(100,0,0),1900),
           ('overview',(1040,-1100,650),(90,15,15),None),
           ('route_drama',(108,-615,90),(-22,-435,10),None),
           ('raised_lookback',(17,447,85),(-28,151,24),None),
           ('baseline_player_eye',(0,-404,4.6),(-9,-340,2),None),
           ('baseline_shallow_oblique',(92,-420,22),(-20,-365,1),None),
           ('raised_player_eye',(0,365,60.6),(-7,430,59),None),
           ('raised_shallow_oblique',(83,358,76),(-15,406,58),None)]
    for name,loc,target,ortho in shots:render(scene,name,loc,target,ortho)
    for label,rootname,point in [('tiny_crack','entry_wasteland_waystone',(-47,-9)),
                                ('medium_crack','path_wasteland_fault',(-20,44)),
                                ('narrow_seam','combat_wasteland_broken_road',(55,-47)),
                                ('vent_slit','path_fortress_causeway',(-44,49)),
                                ('molten_pocket','side_wasteland_shrine',(5,-15)),
                                ('one_sided_fissure','combat_fortress_gateworks',(72,25))]:
        t=bpy.data.objects['chunk_'+rootname]
        target=t.matrix_world@Vector((*point,ground(t,*point)))
        render(scene,'heat_'+label,target+Vector((20,-27,20)),target,None)
    render(scene,'heat_contained_channel',(104,-311,20),(76,-245,-4),None)
    render(scene,'heat_broad_basin',(620,-58,35),(588,14,-8),None)
    groups=[]
    for name in RUINS:
        roots=[bpy.data.objects[r['root']] for r in REPORT['ruins'] if r['archetype']==name]
        root=roots[0] if roots else None
        groups.append([o for o in root.children_recursive if o.type=='MESH' and not o.name.startswith(('chunk_','basalt','heat_','buried_split','molten','rooted_crust')) and not o.get('ReuseSource')] if root else [])
    gallery(scene,'ruin_variety',groups)
    gallery(scene,'basalt_variety',[[o for o in bpy.data.objects[next(r['root'] for r in REPORT['basalt'] if r['archetype']==name)].children if o.get('Archetype')==name] for name in BASALTS])
    gallery(scene,'flora_infection_ladder',[[v] for v in variants],span=8)
    gallery(scene,'chunk_lineup',[[o for o in t.parent.children_recursive if o.type=='MESH' and not o.hide_render] for t in terrains if study.family(t) in study.GRAMMAR],span=280)
    saved=[]
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        for n in m.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED':
                slot=n.inputs['Emission Strength'];saved.append((slot,slot.default_value));slot.default_value=0
    for label,loc,target,ortho in [shots[0],shots[1]]:render(scene,'glow_minimized_'+label,loc,target,ortho)
    for slot,value in saved:slot.default_value=value
    scene.camera=bpy.data.objects['VocabularyReview_overview']


def main(render_images=True):
    global study,helper,trees,rock,fresh,masonry,wood,lava,heatmat
    scene=bpy.context.scene
    assert scene.name=='Emberfall_Foundation_Review'
    assert not scene.get('VocabularyPassComplete'),'Already applied; use saved review.'
    IMAGES.mkdir(parents=True,exist_ok=True)
    study=module('refine_emberfall_naturalization.py','vocabulary_study')
    helper=module('build_emberfall_foundation.py','vocabulary_helpers')
    helper.REVIEW=bpy.data.collections['Cameras_Lights_Scale_REVIEW_ONLY'];study.helper=helper
    rock=bpy.data.materials['EF_BasaltFreshBreak'];fresh=bpy.data.materials['EF_RecentFractureFaces']
    masonry=bpy.data.materials['EF_WeatheredCivilization'];wood=bpy.data.materials['EF_CharredTimber']
    lava=bpy.data.materials['EF_MoltenAuthoredFlow_REVIEW'];heatmat=bpy.data.materials['EF_HeatSeam']
    REPORT['before']=study.stats(scene)
    origins={o.name:(list(o.location),list(o.rotation_euler)) for o in scene.objects if o.type=='EMPTY'}
    terrains=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('chunk_') and 'distant' not in o.name]
    terrains.sort(key=lambda o:(study.family(o) not in study.GRAMMAR,o.name))
    trees={}
    terrain_pass(terrains)
    background_apron(terrains)
    ruins_pass(terrains)
    basalt_pass(terrains)
    heat_pass()
    variants=flora_pass(scene)
    bpy.context.view_layer.update()
    # Uniform border sampling now makes all visible ring joins compatible. Cheap
    # station checks cover the assembled layout, not a rotation/traversal matrix.
    join_checks=[]
    visible=[o for o in study.visible_meshes(scene) if o.name.startswith('chunk_') and 'distant' not in o.name]
    for i,a in enumerate(visible):
        for b in visible[i+1:]:
            delta=b.parent.location-a.parent.location
            if min(abs(delta.x),abs(delta.y))>.01 or abs(max(abs(delta.x),abs(delta.y))-256)>.01:continue
            alongx=abs(delta.x)>abs(delta.y)
            ca=a.parent.location;cb=b.parent.location
            center=(ca+cb)/2
            gaps=[]
            samples=[]
            for t in (a,b):
                row={}
                for v in list(t.data.vertices)[:t['SurfaceVertexCount']]:
                    p=t.matrix_world@v.co
                    if abs((p.x if alongx else p.y)-(center.x if alongx else center.y))<.001:
                        row[round(p.y if alongx else p.x,3)]=p.z
                samples.append(row)
            common=set(samples[0])&set(samples[1])
            assert len(common)==41,(a.name,b.name,len(common))
            gaps=[abs(samples[0][key]-samples[1][key]) for key in common]
            join_checks.append({'pair':[a.name,b.name],'max_gap':max(gaps)})
    REPORT['join_checks']=join_checks
    assert max(r['max_gap'] for r in join_checks)<.001
    REPORT['origins_exact']=all((list(bpy.data.objects[n].location),list(bpy.data.objects[n].rotation_euler))==v for n,v in origins.items())
    assert REPORT['origins_exact']
    REPORT['after']=study.stats(scene)
    REPORT['heat_types']=HEAT_TYPES;REPORT['ruin_types']=sorted(set(r['archetype'] for r in REPORT['ruins']))
    REPORT['basalt_types']=sorted(set(r['archetype'] for r in REPORT['basalt']))
    checks=[]
    for t in terrains:
        bm=bmesh.new();bm.from_mesh(t.data)
        errors=sum(not e.is_manifold for e in bm.edges);bm.free()
        assert errors==0,(t.name,errors)
        checks.append({'object':t.name,'nonmanifold_edges':errors})
    REPORT['closed_mesh_checks']=checks
    scene['VocabularyPassComplete']=True
    scene['README']='Current foundation refinement: varied heat, stronger isolated geological forms, unified border stations, recent ruin/basalt archetypes, four-state sparse flora. Stop for Blender review; no production/export.'
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    if render_images:reviews(scene,variants,terrains)
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    for path in (HERE/'vocabulary_technical_report.json',IMAGES/'vocabulary_technical_report.json'):
        path.write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('VOCABULARY_SAVED',json.dumps({'before':REPORT['before'],'after':REPORT['after'],'max_join_gap':max(r['max_gap'] for r in join_checks),'ruins':REPORT['ruin_types'],'basalt':REPORT['basalt_types']}))


if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    main()
