"""Targeted owner-directed oak, shared chest, cave-floor and Crossroads shelter pass."""
import bpy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).parent))
from scatter_sparse_chunks import MeshBuilder
from refine_flowering_tree import branch

ROOT=Path('E:/BlenderAIProjects/Projects')
SOLID='VV_PROPS_SOLID'
NONSOLID='VV_PROPS_NONSOLID'
OAK='chunk_ancient_oak'
TREASURE='chunk_side_treasure_hollow'
CAVE='chunk_cap_cave_mouth'
CROSS='chunk_path_crossroads_copse'


def object_hash(obj):
    h=hashlib.sha256()
    h.update(str(sorted(c.name for c in obj.users_collection)).encode())
    h.update(struct.pack('16d',*(v for row in obj.matrix_world for v in row)))
    if obj.type=='MESH':
        for v in obj.data.vertices:h.update(struct.pack('3f',*v.co))
        for p in obj.data.polygons:h.update(str((tuple(p.vertices),p.material_index,p.use_smooth)).encode())
        h.update(str([m.name if m else None for m in obj.data.materials]).encode())
    return h.hexdigest()


def bounds(obj,origin=Vector()):
    points=[obj.matrix_world@v.co-origin for v in obj.data.vertices]
    return [min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]


def mesh(builder,name,materials):
    data=bpy.data.meshes.new(name)
    data.from_pydata(builder.vertices,[],builder.faces)
    for m in materials:data.materials.append(bpy.data.materials[m])
    for p,index in zip(data.polygons,builder.material_ids):p.material_index=index
    data.update()
    return data


def create(builder,name,materials,collection,transform):
    obj=bpy.data.objects.new(name,mesh(builder,name+'Mesh',materials))
    bpy.data.collections[collection].objects.link(obj);obj.matrix_world=transform
    return obj


def placement(center,angle=0):
    return Matrix.Translation(Vector(center))@Matrix.Rotation(angle,4,'Z')


def replace_in_place(obj,builder,materials,world_transform):
    # Geometry is converted into the existing object's frame; owner object placement survives.
    transform=obj.matrix_world.inverted()@world_transform
    b=MeshBuilder();b.vertices=[tuple(transform@Vector(v)) for v in builder.vertices]
    b.faces=list(builder.faces);b.material_ids=list(builder.material_ids)
    obj.data=mesh(b,obj.name+'Mesh',materials)


def chest_inner_boards():
    b=MeshBuilder()
    # The same wide planks as the exterior, embedded into the original wall backing.
    for i in range(6):
        for y in (-2.245,2.245):b.box((-3.45+i*1.38,y,2.90),(1.35,.10,3.72),i%2)
    for x in (-3.825,3.825):
        for i in range(4):b.box((x,-1.68+i*1.12,2.90),(.10,1.085,3.72),(i+1)%2)
    return b


def chest_builders():
    body,lid,metal=MeshBuilder(),MeshBuilder(),MeshBuilder()
    wood=['VV_Bark','VV_WaymarkerWood','VV_ExplorerStraps']
    metals=['VV_CaveMetal','VV_LanternBrass','VV_ExplorerStraps']
    # Open wooden box: floor and four walls, with no volume or cap inside.
    for i in range(6):body.box((-3.45+i*1.38,0,.80),(1.35,4.7,.35),i%2)
    for y in (-2.43,2.43):body.box((0,y,2.7),(8.2,.34,4.5),0)
    for x in (-4.02,4.02):body.box((x,0,2.7),(.34,4.54,4.5),0)
    for i in range(6):
        for y in (-2.62,2.62):body.box((-3.45+i*1.38,y,2.7),(1.35,.14,4.25),i%2)
    for x in (-4.23,4.23):
        for i in range(4):body.box((x,-1.86+i*1.24,2.7),(.12,1.21,4.25),(i+1)%2)
    for x in (-3.72,3.72):
        for y in (-2.08,2.08):body.box((x,y,.42),(.78,.78,.84),0)
    body.box((0,0,.45),(8.65,5.35,.45),0)
    for y in (-2.51,2.51):body.box((0,y,4.80),(8.65,.44,.25),1)
    for x in (-4.10,4.10):body.box((x,0,4.80),(.45,4.7,.25),1)
    inner=chest_inner_boards()
    start=len(body.vertices);body.vertices.extend(inner.vertices)
    body.faces.extend(tuple(start+i for i in f) for f in inner.faces);body.material_ids.extend(inner.material_ids)
    profile=[(-2.78,4.91),(-2.78,5.65),(-1.85,6.65),(0,7.08),(1.85,6.65),(2.78,5.65),(2.78,4.91)]
    # Thin roof planks follow the arch; the underside remains hollow.
    for i in range(6):
        x0=-4.34+i*1.45;x1=x0+(1.45 if i<5 else 1.43)
        for j in range(6):
            y0,z0=profile[j];y1,z1=profile[j+1];dy,dz=y1-y0,z1-z0;length=math.hypot(dy,dz);ny,nz=-dz/length,dy/length
            v=[(x,yy+ny*off,zz+nz*off) for off in (-.19,0) for x,yy,zz in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1))]
            lid.add(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],i%2)
    # Side end panels consist of horizontal planks clipped to the actual arch.
    def clipped(poly,level,above):
        result=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            ina=a[1]>=level if above else a[1]<=level;inb=b[1]>=level if above else b[1]<=level
            if ina:result.append(a)
            if ina!=inb:
                t=(level-a[1])/(b[1]-a[1]);result.append((a[0]+t*(b[0]-a[0]),level))
        return result
    for sign in (-1,1):
        for index,(low,high) in enumerate(((4.91,5.59),(5.62,6.29),(6.32,7.08))):
            p=clipped(clipped(profile,low,True),high,False);n=len(p)
            v=[(sign*x,y,z) for x in (4.23,4.42) for y,z in p]
            faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
            if sign==1:faces=[tuple(reversed(f)) for f in faces]
            lid.add(v,faces,index%2)
        for j in range(6):
            a,b=profile[j],profile[j+1];lid.beam((sign*4.48,*a),(sign*4.48,*b),.16,3)
        lid.box((sign*4.47,0,5.70),(.13,4.9,.20),3)
        for y in (-1.90,1.90):lid.foliage((sign*4.58,y,5.70),(.08,.13,.13),4)
    # All roof hoops, lid braces and the hanging hasp belong to the moving lid.
    for x in (-2.65,2.65):
        for j in range(6):
            y0,z0=profile[j];y1,z1=profile[j+1];dy,dz=y1-y0,z1-z0;length=math.hypot(dy,dz);ny,nz=-dz/length,dy/length
            v=[(xx,yy+ny*off,zz+nz*off) for off in (-.025,.105) for xx,yy,zz in ((x-.25,y0,z0),(x+.25,y0,z0),(x+.25,y1,z1),(x-.25,y1,z1))]
            lid.add(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],3)
        lid.box((x,0,5.06),(.4,5.2,.19),0)
        for y in (-2.75,2.75):metal.box((x,y,2.65),(.50,.18,4.30),0)
        metal.box((x,2.75,4.80),(.80,.30,.28),0)
    lid.box((0,-2.95,4.98),(.44,.15,.76),3)
    for x in (-3.92,3.92):
        for y in (-2.58,2.58):
            metal.box((x,y,.78),(.66,.40,.72),0);metal.box((x,y,4.48),(.66,.40,.46),0)
    for y in (-2.75,2.75):
        metal.box((0,y,.85),(8.4,.13,.24),0)
        for x in (-2.65,2.65):
            for z in (1.25,3.95):metal.foliage((x,y+math.copysign(.13,y),z),(.14,.09,.14),1)
    metal.box((0,-2.83,4.27),(1.28,.23,1.30),0)
    metal.box((0,-2.98,4.23),(.88,.16,.90),1)
    metal.box((0,-3.08,4.38),(.17,.045,.20),2);metal.box((0,-3.08,4.21),(.11,.045,.23),2)
    for sign in (-1,1):
        metal.box((sign*4.36,0,3.12),(.18,1.7,.65),0)
        start=len(metal.vertices);metal.ring((0,0,0),.62,.10,0)
        for i in range(start,len(metal.vertices)):
            x,y,z=metal.vertices[i];metal.vertices[i]=(sign*(4.48+y),x,2.65+z)
    return (body,lid,metal),(wood,wood+metals,metals)


def loot_sack():
    b=MeshBuilder();rings=[(1.00,1.10,.72),(1.36,1.55,1.03),(2.29,1.60,1.11),(3.08,.85,.68),(3.40,.30,.26),(3.80,.46,.34)]
    vertices=[]
    for j,(z,rx,ry) in enumerate(rings):
        for i in range(8):
            t=i*math.tau/8;warping=1+.08*math.sin(i*2.1+j*.8)
            vertices.append((-.55+.07*j+rx*math.cos(t)*warping,.10+ry*math.sin(t)*warping,z+.05*math.sin(t*3+j)))
    faces=[tuple(range(7,-1,-1))]+[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(5) for i in range(8)]+[tuple(range(40,48))]
    b.add(vertices,faces,0)
    start=len(b.vertices);b.ring((0,0,0),.32,.085,1)
    for i in range(start,len(b.vertices)):
        x,y,z=b.vertices[i];b.vertices[i]=(x-.20,z+.10,3.39+y)
    b.beam((-.12,-.21,3.38),(.32,-.43,3.20),.12,1)
    b.beam((-.12,-.21,3.38),(-.43,-.46,3.04),.11,1)
    # A casually tipped sack, shifted off centre and settled against the plank floor.
    rotation=Matrix.Rotation(math.radians(-28),4,'Z')@Matrix.Rotation(math.radians(58),4,'Y')@Matrix.Rotation(math.radians(14),4,'X')
    points=[rotation@Vector(v) for v in b.vertices]
    low=[min(p[k] for p in points) for k in range(3)];high=[max(p[k] for p in points) for k in range(3)]
    offset=Vector((-.85-(low[0]+high[0])/2,.35-(low[1]+high[1])/2,.955-low[2]))
    b.vertices=[tuple(p+offset) for p in points]
    assert all(abs(v[0])<3.75 and abs(v[1])<2.15 for v in b.vertices)
    return b


def install_chest(objects,builders,materials,transform):
    body,lid,hardware=objects
    replace_in_place(body,builders[0],materials[0],transform)
    replace_in_place(hardware,builders[2],materials[2],transform)
    hinge=Matrix.Translation(Vector((0,2.78,4.91)))
    lid.matrix_world=transform@hinge
    replace_in_place(lid,builders[1],materials[1],transform)
    lid['chest_role']='Lid';lid['hinge_axis']='LOCAL_X';lid['open_angle_degrees']=-105.0
    body['chest_role']='Body';hardware['chest_role']='BodyHardware'
    prefix=body.name.split('__')[0];name=prefix+'__landmark_chest_loot'
    sack=bpy.data.objects.get(name)
    if sack:replace_in_place(sack,loot_sack(),['VV_WaymarkerWood','VV_ExplorerStraps'],transform)
    else:sack=create(loot_sack(),name,['VV_WaymarkerWood','VV_ExplorerStraps'],NONSOLID,transform)
    sack['chest_role']='LootSack'
    return sack


def grounded_chest(chunk,transform):
    surface=BVHTree.FromPolygons([chunk.matrix_world@v.co for v in chunk.data.vertices],[tuple(p.vertices) for p in chunk.data.polygons])
    heights=[]
    for x in (-3.72,3.72):
        for y in (-2.08,2.08):
            for dx,dy in ((-.39,-.39),(-.39,.39),(.39,-.39),(.39,.39)):
                p=transform@Vector((x+dx,y+dy,0))
                hit,_,_,_=surface.ray_cast(Vector((p.x,p.y,200)),Vector((0,0,-1)),500)
                assert hit is not None
                heights.append(hit.z)
    transform.translation.z=min(heights)-.015
    return transform


def refine_oak():
    c=bpy.data.objects[OAK];trunk=bpy.data.objects[OAK+'__tree_trunk_07']
    lo,hi=bounds(trunk,c.location);base=c.location+Vector((48,-49,lo[2]));frame=placement(base)
    wood=MeshBuilder()
    rings=[((0,0,0),5.15),((.5,-.3,7),4.60),((-.6,.4,17),3.75),((.4,.7,26),3.05),((2,.3,34),2.05)]
    vertices=[tuple(Vector(center)+Vector((r*math.cos(i*math.tau/9),r*math.sin(i*math.tau/9),0))) for center,r in rings for i in range(9)]
    faces=[tuple(range(8,-1,-1))];indices=[0]
    for ring in range(4):
        for i in range(9):
            faces.append((ring*9+i,ring*9+(i+1)%9,(ring+1)*9+(i+1)%9,(ring+1)*9+i))
            indices.append(1 if i in (2,6) else 0)
    faces.append(tuple(range(36,45)));indices.append(0)
    wood.add(vertices,faces,0);wood.material_ids[:]=indices
    limbs=[((-.4,.4,22),(-7,2,29),2.2,1.6),((-7,2,29),(-11,4,36),1.6,.65),
           ((.4,.7,25),(8,-3,33),2.0,1.1),((8,-3,33),(13,-5,38),1.1,.45),
           ((1,0,28),(3,9,39),1.6,.6),((1,.2,31),(-5,-8,38),1.45,.5),
           ((2,.3,33),(6,4,45),1.8,.5),((-.2,0,16),(-5,-1,19),1.15,.85)]
    for a,b,r,t in limbs:branch(wood,a,b,r,t)
    replace_in_place(trunk,wood,['VV_Bark','VV_WaymarkerWood'],frame)
    foliage=MeshBuilder()
    lobes=[((-2,-1,37),(19,17,12)),((-13,1,35),(12,10,10)),((11,2,38),(13,11,11)),
           ((1,10,39),(13,11,11)),((0,-10,34),(14,10,10)),((-5,2,45),(13,11,10)),
           ((9,4,46),(10,9,9)),((-13,-4,42),(7,6,6)),((12,-6,42),(7,6,6))]
    for i,(center,scale) in enumerate(lobes):foliage.foliage(center,scale,1 if i in (3,5,7) else 0)
    canopy=bpy.data.objects[OAK+'__tree_canopy_13']
    replace_in_place(canopy,foliage,['VV_Leaf','VV_LeafLight'],frame)
    # Preserve the second object's identity/placement while giving it a crown-side lobe.
    top=MeshBuilder();top.foliage((1,3,47),(9,8,8),1)
    replace_in_place(bpy.data.objects[OAK+'__tree_canopy_14'],top,['VV_Leaf','VV_LeafLight'],frame)
    details=MeshBuilder();surface=BVHTree.FromPolygons(wood.vertices,wood.faces)
    # Scar seams and a dark knot are projected onto the actual tapered trunk surface.
    for x,z,w,h in ((-.5,7,.35,3.4),(1.2,12,.30,4.0),(-1,20,.26,3.3),(0,11,1.6,2.2)):
        hit,normal,_,_=surface.ray_cast(Vector((x,-20,z)),Vector((0,1,0)),40)
        assert hit is not None
        side=normal.cross(Vector((0,0,1))).normalized();up=side.cross(normal).normalized()
        n=8 if w>1 else 4
        coords=[]
        for i in range(n):
            sample=hit+side*math.cos(i*math.tau/n)*w/2+up*math.sin(i*math.tau/n)*h/2
            seated,face_normal,_,_=surface.ray_cast(Vector((sample.x,-20,sample.z)),Vector((0,1,0)),40)
            assert seated is not None
            coords.append(tuple(seated+face_normal*.005))
        details.add(coords,[tuple(range(n))],0)
    # Moss is seated on upper root faces, avoiding floating details at the base.
    for index in (1,3,5):
        root=bpy.data.objects[OAK+'__woody_piece_'+str(index).zfill(2)]
        b=BVHTree.FromPolygons([frame.inverted()@root.matrix_world@v.co for v in root.data.vertices],[tuple(p.vertices) for p in root.data.polygons])
        rlo,rhi=bounds(root,base);x=(rlo[0]+rhi[0])/2;y=(rlo[1]+rhi[1])/2
        for dx,dy,size in ((0,0,1.5),(1.9,.4,.9)):
            hit,normal,_,_=b.ray_cast(Vector((x+dx,y+dy,30)),Vector((0,0,-1)),60)
            if hit:details.foliage(tuple(hit-normal*.20),(size,size*.72,.4),1)
    create(details,OAK+'__landmark_bark_moss',['VV_ScatterTreeBark','VV_WaymarkerMoss'],NONSOLID,frame)


def terrain_height(chunk,x,y):
    b=BVHTree.FromPolygons([chunk.matrix_world@v.co for v in chunk.data.vertices],[tuple(p.vertices) for p in chunk.data.polygons])
    origin=chunk.location+Vector((x,y,200));hit,_,_,_=b.ray_cast(origin,Vector((0,0,-1)),500)
    assert hit is not None
    return hit.z


def shelter(builders,materials,xy=(65,68),angle=-math.pi/2,in_place=False):
    c=bpy.data.objects[CROSS];rot=Matrix.Rotation(angle,4,'Z');center=c.location+Vector((*xy,0))
    samples=[]
    for x in (-12,0,12):
        for y in (-10,0,10):
            p=rot@Vector((x,y,0))+Vector((*xy,0));samples.append(terrain_height(c,p.x,p.y))
    floor=max(samples)+.08;center.z=floor;frame=placement(center,angle)
    stone,timber,roof=MeshBuilder(),MeshBuilder(),MeshBuilder()
    stone.box((0,0,-.35),(26,22,.7),0)
    for x in (-10.5,10.5):
        for y in (-8,8):
            p=rot@Vector((x,y,0))+Vector((*xy,0));height=terrain_height(c,p.x,p.y)-floor-.12
            stone.box((x,y,(height+1.6)/2),(3.5,3.5,1.6-height),0)
            timber.beam((x,y,1.4),(x,y,17.5),1.65,0)
    # Low broken stone back/side walls leave a wide opening facing the route.
    for x,height in ((-8.8,5.6),(-4.5,7.0),(0,8.2),(4.5,7.2),(8.8,5.3)):
        stone.box((x,8.3,height/2),(4.35,1.9,height),0 if height<7 else 1)
    for sign in (-1,1):
        stone.box((sign*10.7,4.1,2.6),(2.4,6.6,5.2),0)
        timber.beam((sign*10.5,-8,16.8),(sign*10.5,8,16.8),1.3,0)
    for y in (-8,8):
        timber.beam((-11.5,y,17),(11.5,y,17),1.4,1)
        for sign in (-1,1):timber.beam((sign*10.5,y,13.5),(sign*7.5,y,17),.75,0)
        timber.beam((-14,y,18),(0,y,23),1.15,0);timber.beam((0,y,23),(14,y,18),1.15,0)
    timber.beam((0,-12.7,23),(0,12.7,23),1.0,0)
    for sign in (-1,1):
        for i in range(8):
            y0=-13.4+i*3.35;y1=y0+3.31
            pts=[(0,y0,23.1),(sign*15.3,y0,17.65),(sign*15.3,y1,17.65),(0,y1,23.1)]
            vertices=pts+[(x,y,z+.36) for x,y,z in pts]
            roof.add(vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],i%2)
    # Shallow stone step, supported down to the actual grass surface.
    p=rot@Vector((0,-12.8,0))+Vector((*xy,0));stepbottom=terrain_height(c,p.x,p.y)-floor-.08
    if stepbottom<-.18:stone.box((0,-12.8,(stepbottom-.18)/2),(11,3.6,-.18-stepbottom),1)
    support=shelter_roof_supports();offset=len(timber.vertices);timber.vertices.extend(support.vertices)
    timber.faces.extend(tuple(i+offset for i in f) for f in support.faces);timber.material_ids.extend(support.material_ids)
    stone=detail_shelter_stone(stone)
    made=[]
    for part,b,mats in (('stone',stone,['VV_Ruin','VV_RockLight']),('frame',timber,['VV_Bark','VV_WaymarkerWood']),('roof',roof,['VV_ExplorerStraps','VV_Bark'])):
        name=CROSS+'__landmark_cache_'+part
        if in_place:
            obj=bpy.data.objects[name];obj.matrix_world=frame;replace_in_place(obj,b,mats,frame)
        else:obj=create(b,name,mats,SOLID,frame)
        if part=='frame':obj['roof_supports']=True
        made.append(obj)
    chestframe=frame@Matrix.Translation(Vector((0,2.5,0)))
    if in_place:return made,chestframe
    chest=[]
    for part,b,mat in zip(('body','lid','hardware'),builders,materials):
        chest.append(create(b,CROSS+'__landmark_chest_'+part,mat,SOLID,chestframe))
    install_chest(chest,builders,materials,chestframe)
    return made,chest



def main():
    assert not any(o.name.startswith((OAK+'__landmark_',CROSS+'__landmark_')) for o in bpy.data.objects), 'Run on the retained input reference, not an already-refined scene.'
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    (ROOT/'Landmark_Refinement_Input_Manifest.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
    edited={OAK+'__tree_trunk_07',OAK+'__tree_canopy_13',OAK+'__tree_canopy_14',
            TREASURE+'__wood_piece_01',TREASURE+'__ruin_piece_02',TREASURE+'__unclassified_03',
            CAVE+'__wood_piece_02',CAVE+'__wood_piece_03',CAVE+'__unclassified_04',CAVE}
    deleted=[]
    cross=bpy.data.objects[CROSS]
    for o in list(bpy.data.objects):
        if o.type!='MESH' or not o.name.startswith(CROSS+'__'):continue
        low,high=bounds(o,cross.location);mid=[(a+b)/2 for a,b in zip(low,high)]
        if (abs(mid[0])<12 and abs(mid[1])<12) or (mid[0]>35 and mid[1]>35):
            deleted.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    refine_oak()
    builders,materials=chest_builders()
    oldbody=bpy.data.objects[TREASURE+'__wood_piece_01'];lo,hi=bounds(oldbody)
    v=oldbody.matrix_world@oldbody.data.vertices[4].co-oldbody.matrix_world@oldbody.data.vertices[0].co
    angle=math.atan2(v.y,v.x)+math.pi;center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
    install_chest([bpy.data.objects[TREASURE+s] for s in ('__wood_piece_01','__ruin_piece_02','__unclassified_03')],builders,materials,grounded_chest(bpy.data.objects[TREASURE],placement(center,angle)))
    cavebody=bpy.data.objects[CAVE+'__wood_piece_02'];lo,hi=bounds(cavebody);center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
    caveparts=[bpy.data.objects[CAVE+s] for s in ('__wood_piece_02','__wood_piece_03','__unclassified_04')]
    install_chest(caveparts,builders,materials,grounded_chest(bpy.data.objects[CAVE],placement(center,math.pi)))
    # All three use the same model, converted to retain existing owner object matrices.
    made,newchest=shelter(builders,materials)
    # Cave floor colour correction only; the terrain vertex/face topology is fixed.
    cave=bpy.data.objects[CAVE];roof=bpy.data.objects[CAVE+'__cave_structure_04']
    terrain_geometry=([tuple(v.co) for v in cave.data.vertices],[tuple(p.vertices) for p in cave.data.polygons])
    ceiling=BVHTree.FromPolygons([roof.matrix_world@v.co for v in roof.data.vertices],[tuple(p.vertices) for p in roof.data.polygons])
    floor_index=next(i for i,m in enumerate(cave.data.materials) if m.name=='VV_CaveFloor')
    repainted=[]
    for p in cave.data.polygons:
        mat=cave.data.materials[p.material_index].name
        if mat not in ('VV_Grass','VV_GrassLight','VV_Path','VV_DetailMoss') or p.normal.z<.1:continue
        center=cave.matrix_world@p.center
        hit,_,_,_=ceiling.ray_cast(center+Vector((0,0,.03)),Vector((0,0,1)),100)
        if hit is not None:p.material_index=floor_index;repainted.append(p.index)
    cave.data.update();bpy.context.view_layer.update()
    assert terrain_geometry==([tuple(v.co) for v in cave.data.vertices],[tuple(p.vertices) for p in cave.data.polygons])
    for name,h in baseline.items():
        if name in edited or name in deleted:continue
        assert object_hash(bpy.data.objects[name])==h,'Unrelated owner object changed: '+name
    # Verify every old collision mesh, all unaffected art, and cave terrain geometry independently.
    assert len(repainted)>0
    for o in made+newchest:
        lo,hi=bounds(o,cross.location)
        assert lo[0]>35 and lo[1]>35 and hi[0]<112 and hi[1]<112
    newnames=sorted(set(bpy.data.objects.keys())-set(baseline))
    for name in edited|set(newnames):
        o=bpy.data.objects[name]
        assert all(math.isfinite(value) for v in o.data.vertices for value in v.co)
        o.data.calc_loop_triangles();assert len(o.data.loop_triangles)<10000
    result={'input_objects':len(baseline),'output_objects':len(bpy.data.objects),
            'edited_objects':sorted(edited),'deleted_objects':deleted,'new_objects':newnames,
            'cave_repainted_faces':repainted,'protected_objects':len(baseline)-len(edited)-len(deleted),
            'scene':bpy.data.filepath}
    (ROOT/'Landmark_Refinement_Record.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps({k:v for k,v in result.items() if k!='cave_repainted_faces'}))
    print('Cave floor repainted',len(repainted),'faces')


def shelter_dressing():
    c=bpy.data.objects[CROSS];made=[]
    # Two existing tree assemblies, copied with distinct size and rotation.
    for number,(suffixes,x,y,size,theta) in enumerate([
        (('tree_trunk_02','tree_canopy_03','tree_canopy_04'),77,72,.86,.42),
        (('tree_trunk_07','tree_canopy_13','tree_canopy_14'),46,89,.62,-.76)],1):
        source=bpy.data.objects[CROSS+'__'+suffixes[0]];lo,hi=bounds(source)
        anchor=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
        ground=terrain_height(c,x,y)-.08
        group=placement(c.location+Vector((x,y,ground-c.location.z)),theta)@Matrix.Scale(size,4)@Matrix.Translation(-anchor)
        for suffix in suffixes:
            old=bpy.data.objects[CROSS+'__'+suffix];obj=old.copy();obj.data=old.data
            obj.name=CROSS+'__landmark_surround_tree_'+str(number)+'_'+suffix
            collection=SOLID if 'trunk' in suffix else NONSOLID
            bpy.data.collections[collection].objects.link(obj);obj.matrix_world=group@old.matrix_world;made.append(obj)
    specs=[('rock',80,43,.78,.71),('rock',86,48,.38,-.35),('rock',77,39,.30,1.4),
           ('rock',83,55,.49,-.6),('flowering_bush',84,41,1.16,.19),
           ('Star_bush',82,58,1.4,-.82),('flowering_bush',81,70,.90,1.37),
           ('Star_bush',44,80,1.18,.55),('flowering_bush',39,84,.90,-.65),
           ('grass_tuft',47,85,1.35,.8),('grass_tuft',73,82,1.52,-1.1),
           ('grass_tuft',86,54,1.17,.39),('grass_tuft',83,48,1.21,1.5)]
    for i,(kind,x,y,size,theta) in enumerate(specs,1):
        old=bpy.data.objects[kind];lo,hi=bounds(old);anchor=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
        obj=old.copy();obj.data=old.data;obj.name=CROSS+'__landmark_surround_'+str(i).zfill(2)+'_'+kind
        bpy.data.collections[SOLID if kind=='rock' else NONSOLID].objects.link(obj)
        ground=terrain_height(c,x,y)-(.14 if kind=='rock' else .035)
        obj.matrix_world=placement(c.location+Vector((x,y,ground-c.location.z)),theta)@Matrix.Scale(size,4)@Matrix.Translation(-anchor)@old.matrix_world
        made.append(obj)
    return made


def refine_loot_chests():
    assert not bpy.data.objects.get(CROSS+'__landmark_surround_01_rock'), 'Loot refinement already applied; use its retained input reference.'
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    edited=set();builders,materials=chest_builders();new=[];scale=.7912
    for prefix,suffixes in [(TREASURE,('__wood_piece_01','__ruin_piece_02','__unclassified_03')),
                            (CAVE,('__wood_piece_02','__wood_piece_03','__unclassified_04'))]:
        objects=[bpy.data.objects[prefix+s] for s in suffixes];body=objects[0];lo,hi=bounds(body)
        v=body.matrix_world@body.data.vertices[1].co-body.matrix_world@body.data.vertices[0].co
        angle=math.atan2(v.y,v.x);center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
        frame=grounded_chest(bpy.data.objects[prefix],placement(center,angle)@Matrix.Scale(scale,4))
        new.append(install_chest(objects,builders,materials,frame));edited.update(o.name for o in objects)
    made,chestframe=shelter(builders,materials,xy=(56,56),angle=-math.pi/4,in_place=True)
    edited.update(o.name for o in made)
    parts=[bpy.data.objects[CROSS+'__landmark_chest_'+p] for p in ('body','lid','hardware')]
    new.append(install_chest(parts,builders,materials,chestframe@Matrix.Scale(scale,4)));edited.update(o.name for o in parts)
    new.extend(shelter_dressing())
    finish_loot_refinement(baseline,edited,made,parts,new)


def finish_loot_refinement(baseline,edited,made,parts,new):
    scale=.7912
    bpy.context.view_layer.update()
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    for obj in made+parts+new:
        assert all(math.isfinite(a) for v in obj.data.vertices for a in v.co)
        obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)<10000
        if obj.name.startswith(CROSS+'__'):
            lo,hi=bounds(obj,bpy.data.objects[CROSS].location)
            assert min(lo[:2])>35 and max(hi[:2])<112,(obj.name,lo,hi)
    for prefix,suffix in ((TREASURE,'__ruin_piece_02'),(CAVE,'__wood_piece_03'),(CROSS,'__landmark_chest_lid')):
        lid=bpy.data.objects[prefix+suffix];assert lid['hinge_axis']=='LOCAL_X'
    result={'scene':bpy.data.filepath,'input_objects':len(baseline),'output_objects':len(bpy.data.objects),
            'edited_objects':sorted(edited),'new_objects':sorted(o.name for o in new),'protected_objects':len(baseline)-len(edited),
            'chest_scale':scale,'opening_axis':'lid local X','open_angle_degrees':-105,'shelter_center':[56,56],'shelter_angle_degrees':-45}
    (ROOT/'Loot_Chest_Refinement_Input_Manifest.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
    (ROOT/'Loot_Chest_Refinement_Record.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def refine_chest_interiors():
    baseline={o.name:object_hash(o) for o in bpy.data.objects};edited=set();rows=[]
    sack_builder=loot_sack();inner=chest_inner_boards()
    for prefix,body_suffix,lid_suffix in ((TREASURE,'__wood_piece_01','__ruin_piece_02'),(CAVE,'__wood_piece_02','__wood_piece_03'),(CROSS,'__landmark_chest_body','__landmark_chest_lid')):
        body=bpy.data.objects[prefix+body_suffix];lid=bpy.data.objects[prefix+lid_suffix]
        assert not body.get('interior_planks'), 'Interior pass already applied.'
        frame=lid.matrix_world@Matrix.Translation(Vector((0,-2.78,-4.91)))
        old_vertices=[tuple(v.co) for v in body.data.vertices];old_faces=[tuple(p.vertices) for p in body.data.polygons]
        old_bounds=bounds(body);b=MeshBuilder();b.vertices=list(old_vertices);b.faces=list(old_faces);b.material_ids=[p.material_index for p in body.data.polygons]
        transform=body.matrix_world.inverted()@frame;start=len(b.vertices)
        b.vertices.extend(tuple(transform@Vector(v)) for v in inner.vertices);b.faces.extend(tuple(start+i for i in f) for f in inner.faces);b.material_ids.extend(inner.material_ids)
        body.data=mesh(b,body.name+'Mesh',[m.name for m in body.data.materials]);body['interior_planks']=20
        assert [tuple(v.co) for v in body.data.vertices[:start]]==old_vertices
        assert [tuple(p.vertices) for p in body.data.polygons[:len(old_faces)]]==old_faces
        assert bounds(body)==old_bounds
        sack=bpy.data.objects[prefix+'__landmark_chest_loot'];replace_in_place(sack,sack_builder,['VV_WaymarkerWood','VV_ExplorerStraps'],frame)
        edited.update((body.name,sack.name));rows.append({'chunk':prefix,'inner_planks':20,'sack_floor_embedding':.02,'exterior_preserved':True})
    bpy.context.view_layer.update()
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    result={'scene':bpy.data.filepath,'objects':len(bpy.data.objects),'edited_objects':sorted(edited),'protected_objects':len(baseline)-len(edited),'changes':rows}
    (ROOT/'Chest_Interior_Refinement_Record.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print(json.dumps(result))


def shelter_roof_supports():
    b=MeshBuilder()
    for y in (-8,8):
        for x in (-10.5,10.5):b.beam((x,y,17.35),(x,y,19.55),1.65,0)
        b.beam((0,y,17.4),(0,y,23.0),.95,0)
    return b


def masonry_block(builder,low,high,mat,index):
    x0,y0,z0=low;x1,y1,z1=high;c=min(.12+(index%3)*.035,(x1-x0)/5,(y1-y0)/5)
    outline=[(x0+c,y0),(x1-c,y0),(x1,y0+c),(x1,y1-c),(x1-c,y1),(x0+c,y1),(x0,y1-c),(x0,y0+c)]
    bevel=min(.10,(z1-z0)*.25);cx=(x0+x1)/2;cy=(y0+y1)/2
    top=[(x+(bevel if x<cx else -bevel),y+(bevel if y<cy else -bevel)) for x,y in outline]
    v=[(x,y,z) for z in (z0,z1-bevel) for x,y in outline]+[(x,y,z1) for x,y in top]
    faces=[tuple(range(7,-1,-1)),tuple(range(16,24))]+[(r*8+i,r*8+(i+1)%8,(r+1)*8+(i+1)%8,(r+1)*8+i) for r in range(2) for i in range(8)]
    builder.add(v,faces,mat)


def detail_shelter_stone(source):
    b=MeshBuilder();b.box((0,0,-.41),(26,22,.58),0);counter=0
    # Mortar bed beneath large, irregularly spaced flagstones; top remains at z=0.
    for row,(ya,yb) in enumerate(zip((-11,-5.4,.3,5.7),(-5.4,.3,5.7,11))):
        cuts=(-13,-7.3,-1.8,3.8,8.6,13) if row%2==0 else (-13,-8.4,-3.0,2.5,8,13)
        for xa,xb in zip(cuts,cuts[1:]):
            masonry_block(b,(xa+.025,ya+.025,-.15),(xb-.025,yb-.025,0),1 if counter%5==2 else 0,counter);counter+=1
    # Retain each old footing/wall/step envelope; divide it into seated courses.
    for start in range(8,len(source.vertices),8):
        vv=source.vertices[start:start+8];lo=[min(v[k] for v in vv) for k in range(3)];hi=[max(v[k] for v in vv) for k in range(3)]
        footing=start<40;step=lo[1]<-10
        courses=2 if footing else 1 if step else math.ceil((hi[2]-lo[2])/2.15)
        along=1 if hi[1]-lo[1]>hi[0]-lo[0] else 0
        for course in range(courses):
            za=lo[2]+course*(hi[2]-lo[2])/courses;zb=lo[2]+(course+1)*(hi[2]-lo[2])/courses
            cuts=[lo[along],hi[along]] if footing else [lo[along],lo[along]+(hi[along]-lo[along])*(.43 if course%2 else .57),hi[along]]
            for aa,ab in zip(cuts,cuts[1:]):
                low=list(lo);high=list(hi);low[2]=za;high[2]=zb;low[along]=aa+.018;high[along]=ab-.018
                masonry_block(b,low,high,1 if counter%6==1 else 0,counter);counter+=1
    return b


def refine_shelter_supports():
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    frame=bpy.data.objects[CROSS+'__landmark_cache_frame'];stone=bpy.data.objects[CROSS+'__landmark_cache_stone']
    assert not frame.get('roof_supports'), 'Shelter support pass already applied.'
    b=MeshBuilder();b.vertices=[tuple(v.co) for v in frame.data.vertices];b.faces=[tuple(p.vertices) for p in frame.data.polygons];b.material_ids=[p.material_index for p in frame.data.polygons]
    support=shelter_roof_supports();offset=len(b.vertices);b.vertices.extend(support.vertices);b.faces.extend(tuple(i+offset for i in f) for f in support.faces);b.material_ids.extend(support.material_ids)
    frame.data=mesh(b,frame.name+'Mesh',[m.name for m in frame.data.materials]);frame['roof_supports']=True
    sb=MeshBuilder();sb.vertices=[tuple(v.co) for v in stone.data.vertices]
    stone.data=mesh(detail_shelter_stone(sb),stone.name+'Mesh',[m.name for m in stone.data.materials])
    bpy.context.view_layer.update();edited={frame.name,stone.name}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    for o in (frame,stone):o.data.calc_loop_triangles();assert len(o.data.loop_triangles)<10000
    result={'scene':bpy.data.filepath,'edited':sorted(edited),'protected_objects':len(baseline)-2,'roof_bearings':4,'king_posts':2,'stone_triangles':len(stone.data.loop_triangles)}
    (ROOT/'Shelter_Support_Refinement_Record.json').write_text(json.dumps(result,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print(json.dumps(result))


def refine_windward_patch():
    """Flatten the center pinch into the ridge slope, feathering the transition."""
    import numpy as np
    obj=bpy.data.objects['chunk_windward_ridge_gate'];m=obj.data
    assert not obj.get('patch_refined'), 'Patch repair already applied.'
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    fan=[p for p in m.polygons if p.material_index==2 and 0 in p.vertices]
    assert len(fan)==190
    ids=sorted({i for p in fan for i in p.vertices}-{0})
    boundary=np.array([tuple(m.vertices[i].co) for i in ids])
    slope=np.linalg.lstsq(np.column_stack((boundary[:,:2],np.ones(len(boundary)))),boundary[:,2],rcond=None)[0]
    terrain_ids={i for p in m.polygons if p.material_index in (0,1,2) for i in p.vertices}
    changed=[]
    for i in terrain_ids:
        v=m.vertices[i].co;r=math.hypot(v.x,v.y)
        if r>=32:continue
        t=max(0,min(1,(r-16)/16));weight=1-t*t*(3-2*t)
        v.z+=(slope[0]*v.x+slope[1]*v.y+slope[2]-v.z)*weight;changed.append(i)
    m.update();obj['patch_refined']=True
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n!=obj.name)
    assert all(math.isfinite(x) for vertex in m.vertices for x in vertex.co)
    m.calc_loop_triangles();assert len(m.loop_triangles)<10000
    result={'scene':bpy.data.filepath,'edited':obj.name,'changed_vertices':len(changed),'protected_objects':len(baseline)-1,'triangles':len(m.loop_triangles),'plane':slope.tolist(),'flat_radius':16,'blend_radius':32}
    (ROOT/'Windward_Patch_Refinement_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print(json.dumps(result))


def refine_windward_transitions():
    """Broaden the consistent ridge slope and feather the outer transition."""
    import numpy as np
    obj=bpy.data.objects['chunk_windward_ridge_gate'];m=obj.data
    assert obj.get('patch_refined') and not obj.get('transitions_refined')
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    original=[tuple(v.co) for v in m.vertices]
    terrain_ids={i for p in m.polygons if p.material_index in (0,1,2) for i in p.vertices}
    plane=json.loads((ROOT/'Windward_Patch_Refinement_Record.json').read_text())['plane']
    active=[]
    for i in terrain_ids:
        v=m.vertices[i].co;r=math.hypot(v.x,v.y)
        if r<=16 or r>=96:continue
        t=max(0,min(1,(r-48)/48));weight=1-t*t*t*(10-15*t+6*t*t)
        v.z+=(plane[0]*v.x+plane[1]*v.y+plane[2]-v.z)*weight;active.append(i)
    m.update();obj['transitions_refined']=True
    assert all(tuple(m.vertices[i].co)==original[i] for i in range(len(original)) if i not in active)
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n!=obj.name)
    assert all(math.isfinite(x) for v in m.vertices for x in v.co)
    result={'scene':bpy.data.filepath,'edited_vertices':len(active),'protected_objects':len(baseline)-1,'approved_center_preserved':True,'max_adjustment':max(abs(m.vertices[i].co.z-original[i][2]) for i in active)}
    (ROOT/'Windward_Transition_Refinement_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print(json.dumps(result))


if __name__=='__main__':
    if '--windward-transitions' in sys.argv:refine_windward_transitions()
    elif '--windward-patch' in sys.argv:refine_windward_patch()
    elif '--shelter-support' in sys.argv:refine_shelter_supports()
    elif '--interior-refinement' in sys.argv:refine_chest_interiors()
    elif '--loot-refinement' in sys.argv:refine_loot_chests()
    else:main()
