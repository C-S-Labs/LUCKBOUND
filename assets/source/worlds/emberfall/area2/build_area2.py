"""Emberfall Area II: one editable design study, never a production/export kit.
Run with tools/run_blender.py --factory-startup --python this_file.
Units are studs, Blender X lateral / Y progression / Z up. No accepted source import.
"""
import bpy
import math
import json
import random
import sys
from pathlib import Path
from mathutils import Vector

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII')
OUT.mkdir(parents=True, exist_ok=True)
RNG = random.Random(207)
ROUTE = [(0,0),(0,90),(-85,150),(-85,280),(80,280),(80,430),
         (180,470),(180,600),(-40,600),(-40,720),(80,800),(80,900),(0,950)]
APPROACH = [(0,-240),(0,0)]
COURTS = [(0,72,94,70),(-85,280,92,94),(100,442,138,140),(12,773,130,92),(0,955,122,90)]
COLS = {}
MATS = {}
BUILDINGS = []
VIEWS = [
 ('01_overview',(-900,-720,940),(0,460,25), 'ORTHO',1450),
 ('02_area1_approach',(0,-210,-3),(0,0,23),'PERSP',27),
 ('03_gate_threshold',(0,-30,5),(0,120,12),'PERSP',23),
 ('04_first_reveal',(0,58,7),(-70,185,17),'PERSP',25),
 ('05_workshop_street',(-85,218,13),(75,280,23),'PERSP',25),
 ('06_market',(80,367,19),(95,470,26),'PERSP',25),
 ('07_elevated_progression',(-290,705,160),(15,480,22),'PERSP',25),
 ('08_castle_approach',(80,855,54),(0,1150,110),'PERSP',25),
 ('09_destruction_progression',(-510,615,310),(65,620,31),'ORTHO',730),
 ('10_route_plan',(0,480,1700),(0,480,0),'ORTHO',2600),
]

def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    COLS[name] = c
    return c

def material(name, color, emission=0, alpha=1):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,alpha)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,alpha)
    bs.inputs['Roughness'].default_value=.9
    bs.inputs['Alpha'].default_value=alpha
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1)
        bs.inputs['Emission Strength'].default_value=emission
    if alpha<1:
        m.surface_render_method='DITHERED'
    MATS[name]=m
    return m

def assign(o,name,col,mat):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    COLS[col].objects.link(o)
    o.data.materials.append(MATS[mat])
    return o

def box(name,loc,size,col,mat,rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=assign(bpy.context.object,name,col,mat)
    o.scale=size
    o.rotation_euler[2]=rotation
    return o

def mesh(name,verts,faces,col,mat):
    d=bpy.data.meshes.new(name)
    d.from_pydata(verts,[],faces); d.update()
    o=bpy.data.objects.new(name,d); COLS[col].objects.link(o)
    d.materials.append(MATS[mat]); return o

def beam(name,a,b,width,col='Destruction',mat='CharredTimber'):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,width,(b-a).length),col,mat)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def cylinder(name,loc,radius,depth,col,mat,vertices=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    return assign(bpy.context.object,name,col,mat)

def elevation(y):
    stations=[(-300,-10),(0,0),(120,4),(280,12),(430,18),(600,30),(760,42),(950,54),(1005,56),(1080,78),(1400,87)]
    for (a,z),(b,w) in zip(stations,stations[1:]):
        if a<=y<=b: return z+(w-z)*(y-a)/(b-a)
    return -10 if y<0 else 87

def distance_segment(x,y,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)

def street_height(x,y):
    z=elevation(y)
    for cx,cy,w,d in COURTS:
        outside=max(abs(x-cx)-w/2,abs(y-cy)-d/2,0)
        blend=max(0,1-outside/60)
        z=z*(1-blend)+elevation(cy)*blend
    return z

def terrain_height(x,y):
    d=min(distance_segment(x,y,a,b) for a,b in zip(APPROACH+ROUTE, (APPROACH+ROUTE)[1:]) if a!=b)
    relief=min(1,max(0,(d-38)/45))
    for cx,cy,w,depth in COURTS:
        outside=max(abs(x-cx)-w/2,abs(y-cy)-depth/2,0)
        relief*=min(1,outside/30)
    return street_height(x,y)+relief*(3*math.sin(x/82)*math.cos(y/92)+max(0,abs(x)-180)*.017)

def terrain():
    verts=[];faces=[]
    nx,ny=40,82
    for j in range(ny+1):
        y=-300+j*20
        for i in range(nx+1):
            x=-400+i*20
            verts.append((x,y,terrain_height(x,y)))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i
            faces.extend([(a,a+1,a+nx+2),(a,a+nx+2,a+nx+1)])
    o=mesh('ContinuousLand_ReviewOnly',verts,faces,'Terrain','StressedGround')
    for mat in ['SurvivingGround','CharredGround','Earth']: o.data.materials.append(MATS[mat])
    for p in o.data.polygons:
        c=sum((Vector(verts[v]) for v in p.vertices),Vector())/3
        noise=math.sin(c.x/60)+math.cos(c.y/54)+.4*math.sin((c.x+c.y)/19)
        garden=(c.x+205)**2/70**2+(c.y-160)**2/68**2<1
        p.material_index=1 if garden or (c.y<60 and noise>1.1) else 2 if c.y>690 or noise<-.3 or (c.x>95 and c.y>350) else 0
    # Review land has an intentionally simple finite skirt, never a playable boundary.
    edges=[verts[i] for i in range(nx+1)]+[verts[j*(nx+1)+nx] for j in range(1,ny+1)]+[verts[ny*(nx+1)+i] for i in range(nx-1,-1,-1)]+[verts[j*(nx+1)] for j in range(ny-1,0,-1)]
    v=[];f=[]
    for a,b in zip(edges,edges[1:]+edges[:1]):
        n=len(v);v.extend([a,b,(b[0],b[1],-28),(a[0],a[1],-28)]);f.append((n,n+1,n+2,n+3))
    mesh('LandSkirt_Scenery',v,f,'Terrain','Earth')

def road_segment(a,b,width,mat='Road',name='Street',col='Streets'):
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy)
    ox,oy=-dy/l*width/2,dx/l*width/2
    n=max(1,math.ceil(l/16));v=[];f=[]
    for i in range(n+1):
        t=i/n;x=a[0]+t*dx;y=a[1]+t*dy
        v.extend([(x+ox,y+oy,street_height(x+ox,y+oy)+.16),(x-ox,y-oy,street_height(x-ox,y-oy)+.16)])
    for i in range(n): f.append((2*i,2*i+1,2*i+3,2*i+2))
    return mesh(name,v,f,col,mat)

def plaza(name,x,y,w,d):
    z=elevation(y)+.18
    return mesh(name,[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)],[(0,1,2,3)],'Streets','Paving')


def roof(name,x,y,z,w,d,h,col,mat,half=False):
    v=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x,y-d/2,z+h),
       (x-w/2,y+d/2,z),(x+w/2,y+d/2,z),(x,y+d/2,z+h)]
    f=[(0,3,5,2),(1,2,5,4),(0,2,1),(3,4,5)] if not half else [(0,3,5,2),(0,2,1)]
    return mesh(name,v,f,col,mat)

def building(name,x,y,w,d,h,col,state='intact',roofmat='RoofDusty'):
    z=terrain_height(x,y)+.2
    BUILDINGS.append(dict(name=name,xy=[x,y],footprint=[w,d],eave=h,state=state))
    box(name+'_StonePlinth',(x,y,z+2),(w+3,d+3,4),col,'Fieldstone')
    mat='Plaster' if state=='intact' else 'SmokePlaster'
    if state=='collapsed':
        box(name+'_RearWall',(x,y+d/2-1,z+h*.33),(w,2,h*.66),col,mat)
        box(name+'_SideRemnant',(x-w/2+1,y,z+h*.19),(2,d,h*.38),col,mat)
        rubble(name+'_FreshRubble',x,y,18,18)
        for k in range(3):
            beam(name+'_ExposedRafter', (x-w/2,y-d/2+k*d/2,z+4),(x+2,y-d/2+k*d/2,z+h+8),2,col='Destruction')
    else:
        # Separate wall masses leave one broad entry opening; no ornamental facade work.
        for sx in [-1,1]: box(name+'_SideWall',(x+sx*(w/2-1),y,z+h/2+2),(2,d,h),col,mat)
        box(name+'_RearWall',(x,y+d/2-1,z+h/2+2),(w,2,h),col,mat)
        for sx in [-1,1]: box(name+'_FrontPier',(x+sx*(w/4+3),y-d/2+1,z+h/2+2),(w/2-6,2,h),col,mat)
        box(name+'_FrontLintel',(x,y-d/2+1,z+h-1),(12,2,6),col,mat)
        for sx in [-1,1]:
            for sy in [-1,1]: box(name+'_TimberPost',(x+sx*(w/2-1),y+sy*(d/2-1),z+h/2+2),(1.6,1.6,h+1),col,'Timber' if state=='intact' else 'CharredTimber')
        box(name+'_EaveBeam',(x,y-d/2,z+h+2),(w+2,2,2),col,'Timber')
        roof(name+'_Roof',x,y,z+h+3,w+5,d+5,w*.29,col,roofmat,half=state=='damaged')
        if state=='damaged':
            for k in range(3):
                yy=y-d/2+k*d/2
                beam(name+'_RoofSkeleton',(x+w/2,yy,z+h+3),(x,yy,z+h+3+w*.29),1.8,'Destruction')
            rubble(name+'_EavesFall',x+w/2+8,y,7,7)
    if state=='burning': fire(name+'_Fire',x+w/2-3,y,z+h+2,7)
    return z

def rubble(name,x,y,r,count):
    for i in range(count):
        a=RNG.random()*math.tau; rr=RNG.random()*r
        xx=x+math.cos(a)*rr; yy=y+math.sin(a)*rr
        o=box(name,(xx,yy,terrain_height(xx,yy)+RNG.uniform(1,3)),(RNG.uniform(2,7),RNG.uniform(2,5),RNG.uniform(2,5)),'Destruction','FreshStone',RNG.random()*3)
        o.rotation_euler[0]=RNG.uniform(-.5,.5)

def fire(name,x,y,z,scale):
    for i in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=scale*.3,radius2=0,depth=scale,location=(x+i*scale*.28,y,z+scale*.4))
        assign(bpy.context.object,name,'Fire','FireAmber' if i%2 else 'FireHot')
    for i in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x+i*2,y,z+scale+10+i*13))
        o=assign(bpy.context.object,name+'_StaticSmokeProxy','Smoke','Smoke')
        o.scale=(scale*.65+i*2,scale*.55+i*2,9+i*3)

def tree(name,x,y,state):
    z=terrain_height(x,y);h=RNG.uniform(20,31)
    cylinder(name+'_Trunk',(x,y,z+h/2),1.2,h,'Vegetation','CharredTimber' if state=='char' else 'Timber',6)
    for a in [0,2.1,4.2]: beam(name+'_Branch',(x,y,z+h*.6),(x+math.cos(a)*7,y+math.sin(a)*7,z+h),.8,'Vegetation','CharredTimber' if state=='char' else 'Timber')
    if state!='char':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=9,location=(x,y,z+h))
        o=assign(bpy.context.object,name+'_Canopy','Vegetation','Leaf' if state=='green' else 'DryLeaf');o.scale=(1,.8,.85)

def arch(name,x,y,z,width,height,depth,col):
    r=width/2;spring=height-r
    for s in [-1,1]: box(name+'_Jamb',(x+s*(r+3),y,z+spring/2),(6,depth,spring),col,'Fieldstone')
    for i in range(9):
        a=math.pi*i/9;b=math.pi*(i+1)/9
        v=[]
        for yy in [y-depth/2,y+depth/2]:
            for rr,t in [(r,a),(r,b),(r+5,b),(r+5,a)]: v.append((x+rr*math.cos(t),yy,z+spring+rr*math.sin(t)))
        mesh(name+'_ArchSector',v,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],col,'Fieldstone')

def tower(name,x,y,height,damaged=False,col='OuterWall',radius=22):
    z=terrain_height(x,y)
    cylinder(name+'_BatteredPlinth',(x,y,z+4),radius+4,8,col,'Fieldstone')
    cylinder(name+'_Tower',(x,y,z+height/2),radius,height,col,'Fieldstone')
    cylinder(name+'_Coping',(x,y,z+height-2),radius+1.5,3,col,'FreshStone')
    for i in range(8):
        if damaged and i in [0,1,2]:continue
        a=i*math.tau/8
        box(name+'_Crown',(x+math.cos(a)*radius*.86,y+math.sin(a)*radius*.86,z+height+1.5),(5,5,6),col,'Fieldstone',a)
    for sx in [-1,1]: box(name+'_Buttress',(x+sx*radius*.9,y-8,z+12),(7,14,24),col,'Fieldstone')

def defense():
    for s in [-1,1]:
        if s<0:
            box('OuterCurtain',(s*238,0,20),(344,14,40),'OuterWall','Fieldstone')
        else:
            box('OuterCurtain_GateSide',(78,0,20),(24,14,40),'OuterWall','Fieldstone')
            box('OuterCurtain_BeyondBreach',(264,0,20),(292,14,40),'OuterWall','Fieldstone')
            mesh('BrokenWall_Breach',[(90,-7,0),(118,-7,0),(118,-7,26),(110,-7,16),(102,-7,12),(90,-7,24),(90,7,0),(118,7,0),(118,7,26),(110,7,16),(102,7,12),(90,7,24)],[(0,1,2,3,4,5),(11,10,9,8,7,6),(0,6,7,1),(1,7,8,2),(2,8,9,3),(3,9,10,4),(4,10,11,5),(5,11,6,0)],'OuterWall','Fieldstone')
        if s<0:box('CurtainCoping',(s*238,0,40),(344,18,3),'OuterWall','FreshStone')
        else:box('CurtainCoping_BeyondBreach',(264,0,40),(292,18,3),'OuterWall','FreshStone')
        for x in range(82,393,24):
            if not (s>0 and 90<x<124):box('CurtainMerlon',(s*x,0,43),(11,14,6),'OuterWall','Fieldstone')
        for x in ([215,315] if s>0 else [115,215,315]): box('CurtainBatteredPier',(s*x,-9,14),(10,14,28),'OuterWall','Fieldstone')
    tower('WestGate_Intact',-42,0,58)
    tower('EastGate_Broken',42,0,40,True)
    arch('OuterGate',0,0,0,36,31,32,'OuterWall')
    box('GuardChamber',(0,0,37),(46,26,9),'OuterWall','SmokePlaster')
    roof('GuardRoof_Partial',0,0,42,51,30,10,'OuterWall','RoofChar',True)
    # Deliberate low breach on right; set behind a substantial debris/scenery bank.
    rubble('BreachBank_NotAlternateRoute',104,10,19,20)
    rubble('GateTowerFall',67,32,27,22)
    beam('GateSnappedBeam',(35,17,34),(65,40,7),3)
    fire('GateRoofEmbers',24,8,42,4)
    # Drained roadside ditch leads to recognizable town infrastructure.
    for x in [-32,32]: road_segment((x,-220),(x,-30),5,'Earth','ApproachDrain')


def town():
    for i,(a,b) in enumerate(zip(ROUTE,ROUTE[1:])):
        road_segment(a,b,36 if i<3 else 44 if i<8 else 48,name='PrimaryStreet_%02d'%i)
        # Two curb/drain ribbons communicate construction, no spline gesture.
        dx,dy=b[0]-a[0],b[1]-a[1]; l=math.hypot(dx,dy); nx,ny=-dy/l,dx/l
        for s in [-1,1]: road_segment((a[0]+s*nx*24,a[1]+s*ny*24),(b[0]+s*nx*24,b[1]+s*ny*24),2,'Fieldstone','DrainCoping')
    road_segment(*APPROACH,32,'Road','AreaI_Approach')
    plaza('ArrivalApron',0,72,94,70)
    plaza('WorkshopYard',-85,280,92,94)
    plaza('MarketCourt',100,442,138,140)
    plaza('UpperCivicCourt',12,773,130,92)
    plaza('InnerBoundaryCourt',0,955,122,90)
    # Early houses retain identity, garden and empty working yard.
    entries=[('GateKeeperHouse',-98,66,30,38,18,'intact'),
      ('EdgeCottage',84,94,30,38,16,'damaged'),('GardenHome',-175,152,32,42,18,'intact'),
      ('LowerHome',-142,223,34,42,22,'damaged'),('Workshop',-161,291,44,58,25,'damaged'),
      ('StoreYardHall',-8,213,46,66,24,'intact'),('StreetHome',-12,335,34,45,24,'damaged')]
    for name,x,y,w,d,h,state in entries: building(name,x,y,w,d,h,'EarlySettlement',state)
    entries=[('MarketShopWest',18,405,36,48,26,'intact'),('MarketShopEast',197,398,38,50,27,'burning'),
      ('MarketStore',245,507,48,65,29,'damaged'),('GuildHall',-14,480,62,76,34,'damaged'),
      ('ServiceWorkshop',250,582,44,58,27,'collapsed'),('UpperStores',84,655,46,68,28,'burning'),
      ('ServiceHome',-106,553,38,48,28,'damaged')]
    for name,x,y,w,d,h,state in entries:building(name,x,y,w,d,h,'MidSettlement',state)
    entries=[('CivicHall',-126,790,64,82,34,'damaged'),('FailedTerraceHall',180,791,60,74,32,'collapsed'),
      ('UpperHome',141,881,42,58,30,'burning'),('InnerStore',-103,898,50,66,31,'collapsed'),
      ('LastStandingHouse',-184,938,42,58,30,'damaged')]
    for name,x,y,w,d,h,state in entries:building(name,x,y,w,d,h,'LateSettlement',state,'RoofChar')
    # Secondary street stubs and one reconnecting courtyard loop.
    road_segment((-85,170),(-224,170),22,'Road','GardenLane')
    road_segment((180,565),(290,565),24,'Road','WorkshopSideCourt')
    for a,b in [((-40,635),(-150,655)),((-150,655),(-150,708)),((-150,708),(-40,720))]:road_segment(a,b,22,'Paving','OptionalCourtLoop')
    for x,y,w in [(-185,182,86),(240,550,88),(-192,715,75)]:
        box('RetainingWall',(x,y,elevation(y)+3),(w,7,9),'Terrain','Fieldstone')
        box('RetainingCoping',(x,y,elevation(y)+8),(w+2,9,2),'Terrain','FreshStone')
    # Terrace wall beneath late failure; breach deformation implied by missing segment.
    for x,w in [(130,50),(224,48)]:box('FailedTerraceRemnant',(x,748,elevation(748)+6),(w,10,14),'LateSettlement','Fieldstone')
    rubble('TerraceFreshFailure',178,745,25,25)
    beam('FailedHallRoofFall',(183,780,elevation(780)+28),(164,738,elevation(738)+4),3)
    road_segment((198,776),(177,735),3,'Heat','LateHeatFracture','Fire')
    fire('InnerFailureActive',187,790,elevation(790)+9,10)
    # Well is a hollow broad ring, not a detailed prop.
    for name,x,y in [('ShelteredWell',-205,150),('MarketWell',47,465)]:
        z=terrain_height(x,y)
        for i in range(8):
            a=i*math.tau/8;box(name,(x+math.cos(a)*6,y+math.sin(a)*6,z+2.5),(5,2,5),'CivilLife','Fieldstone',a+math.pi/2)
        for s in [-1,1]:box(name+'_Post',(x+s*7,y,z+6),(1.4,1.4,12),'CivilLife','Timber')
        roof(name+'_Cover',x,y,z+12,20,15,5,'CivilLife','RoofDusty')
    for x in [-245,-165]:box('GardenBoundary',(x,152,elevation(152)+2),(3,78,5),'CivilLife','Fieldstone')
    box('GardenTrough',(-222,186,elevation(186)+2),(15,5,4),'CivilLife','Fieldstone')
    for i in range(4):box('CultivatedBed',(-230+i*14,147,elevation(147)+.5),(7,36,1),'Vegetation','Leaf')
    # Market canopy row, recognizable commerce interrupted by a connected fire front.
    for i in range(4):
        x=61+i*26;y=520;z=elevation(y)
        for sx in [-1,1]:box('MarketCanopyPost',(x+sx*10,y,z+8),(1.4,1.4,16),'CivilLife','CharredTimber' if i>1 else 'Timber')
        if i<3:roof('MarketCanopy',x,y,z+16,24,19,5,'CivilLife','RoofDusty' if i<2 else 'RoofChar')
        else:beam('CollapsedCanopy',(x-10,y,z+2),(x+10,y+8,z+3),2)
        box('AbandonedMarketCounter',(x,y+1,z+3),(18,8,6),'CivilLife','Timber')
        if i>=2:fire('MarketConnectedFire',x,y,z+(15 if i==2 else 3),7)
    # Small blockout cart masses, no wheels/prop craftsmanship.
    for name,x,y in [('EvacuationCart',28,83),('MarketBrokenCart',170,498)]:
        z=elevation(y);o=box(name,(x,y,z+3),(11,18,5),'CivilLife','Timber');o.rotation_euler[1]=.2
        for s in [-1,1]:cylinder(name+'_Wheel',(x+s*7,y,z+2),3,1,'CivilLife','CharredTimber',8).rotation_euler[1]=math.pi/2
        beam(name+'_Shaft',(x,y-9,z+3),(x,y-20,z+1),1,'CivilLife','Timber')
    for x,y,state in [(-270,-145,'dry'),(172,-166,'char'),(-290,100,'char'),(-244,134,'green'),(-174,168,'dry'),(263,221,'char'),(-265,345,'dry'),(291,480,'char'),(-270,620,'char'),(268,865,'char')]:tree('VegetationRemnant',x,y,state)
    # Intentionally modest civic landmark, distinguished by a broad gable and square bell mass.
    z=elevation(480);box('GuildCivicMarker',(-35,504,z+42),(16,18,18),'MidSettlement','Fieldstone')
    roof('GuildMarkerRoof',-35,504,z+51,20,22,8,'MidSettlement','RoofDusty')
    # Short optional stairs support terrace access, never required jumping.
    for i in range(10):box('OptionalTerraceStair',(-162,664+i*3,elevation(664)+i*.6),(22,3,1.2),'Streets','Fieldstone')


def castle():
    arch('InnerBoundaryGate',0,1005,elevation(1005),38,34,20,'CastleBoundary')
    for x in [-139,139]:box('InnerBoundaryWall',(x,1005,elevation(1005)+19),(226,12,38),'CastleBoundary','Fieldstone')
    for x in [-47,47]:tower('InnerBoundaryPier',x,1005,46,False,'CastleBoundary',16)
    # Beyond AreaII: silhouette relationship only, no interior or architectural lock.
    z=elevation(1165)
    box('CastleProxy_Podium',(0,1170,z+8),(220,195,16),'CastleProxy','CastleStone')
    box('CastleProxy_Keep',(0,1195,z+61),(105,80,105),'CastleProxy','CastleStone')
    roof('CastleProxy_KeepRoof',0,1195,z+114,114,90,21,'CastleProxy','CastleRoof')
    for x,y,h in [(-84,1120,76),(84,1120,68),(-84,1222,86),(84,1222,92)]:tower('CastleProxy_Tower',x,y,h,True,'CastleProxy',20)
    for x in [-80,80]:box('CastleProxyCurtain',(x,1170,z+30),(14,165,55),'CastleProxy','CastleStone')
    box('CastleProxyFront',(0,1107,z+27),(135,12,48),'CastleProxy','CastleStone')
    road_segment((0,950),(0,1100),40,'Paving','AreaIII_ProxyContinuation')


def route_overlay():
    for i,(a,b) in enumerate(zip(ROUTE,ROUTE[1:])):
        o=road_segment(a,b,4,'RouteCyan','IntendedRoute','Route');o.location.z=2
        if i%2==0:
            dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);x=(a[0]+b[0])/2;y=(a[1]+b[1])/2
            v=[(x+dx/l*9,y+dy/l*9,street_height(x,y)+3),(x-dx/l*5-dy/l*6,y-dy/l*5+dx/l*6,street_height(x,y)+3),(x-dx/l*5+dy/l*6,y-dy/l*5-dx/l*6,street_height(x,y)+3)]
            mesh('RouteDirection',v,[(0,1,2)],'Route','RouteCyan')
    for text,x,y in [('1  OUTER GATE',-325,20),('2  HOMES / YARDS',-325,208),('3  MARKET / CIVIC',-325,460),('4  TERRACE STREET',-325,640),('5  UPPER COURT',-325,812),('6  INNER BOUNDARY',-325,998),('CASTLE PROXY',-195,1300)]:
        d=bpy.data.curves.new('PlanLabel','FONT');d.body=text;d.size=19;d.extrude=0
        o=bpy.data.objects.new('Plan_'+text,d);COLS['Route'].objects.link(o);o.location=(x,y,elevation(y)+5);d.materials.append(MATS['RouteCyan'])
    COLS['Route'].hide_render=True
    COLS['Route'].hide_viewport=True


def cameras():
    for name,loc,target,kind,value in VIEWS:
        d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);COLS['ReviewCameras'].objects.link(o)
        o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
        d.type=kind;d.clip_end=5000;d.clip_start=.1
        if kind=='ORTHO':d.ortho_scale=value
        else:d.lens=value;d.sensor_width=36
        o['ReviewPurpose']=name
    scene=bpy.context.scene;scene.camera=bpy.data.objects['01_overview']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.clip_end=5000
                area.spaces.active.region_3d.view_distance=1250
                area.spaces.active.region_3d.view_location=(0,460,30)
                area.spaces.active.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
                area.spaces.active.shading.type='MATERIAL'


def build():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):bpy.data.collections.remove(c)
    for name in ['Terrain','OuterWall','EarlySettlement','MidSettlement','LateSettlement','CastleBoundary','CastleProxy','Streets','CivilLife','Destruction','Vegetation','Fire','Smoke','Route','ReviewCameras','ReviewLighting','ScaleFigures']:collection(name)
    colors={'Fieldstone':(.26,.255,.21),'FreshStone':(.39,.37,.31),'Plaster':(.58,.52,.41),
      'SmokePlaster':(.37,.34,.28),'Timber':(.16,.095,.05),'CharredTimber':(.022,.018,.014),
      'RoofDusty':(.30,.16,.095),'RoofChar':(.095,.072,.052),'Road':(.30,.235,.15),
      'Paving':(.35,.32,.26),'StressedGround':(.25,.23,.12),'SurvivingGround':(.19,.25,.105),
      'CharredGround':(.065,.071,.058),'Earth':(.12,.105,.072),'Leaf':(.22,.31,.11),
      'DryLeaf':(.33,.29,.09),'CastleStone':(.21,.225,.215),'CastleRoof':(.12,.13,.12),
      'RouteCyan':(.06,.8,.92),'Figure':(.53,.69,.76)}
    for name,color in colors.items():material(name,color)
    material('FireAmber',(1,.22,.015),2);material('FireHot',(1,.57,.055),2)
    material('Heat',(.84,.16,.015),1.5);material('Smoke',(.12,.135,.13),alpha=.28)
    terrain();defense();town();castle();route_overlay();cameras()
    for x,y in [(0,74),(-85,252),(80,433),(-40,699),(80,920)]:
        z=street_height(x,y)
        box('PlayerScale_5stud',(x,y,z+2.3),(2,1,3.6),'ScaleFigures','Figure')
        cylinder('PlayerScale_Head',(x,y,z+4.5),.7,1,'ScaleFigures','Figure',8)
    scene=bpy.context.scene;scene.name='Emberfall_AreaII_SelectedBlockout'
    scene.unit_settings.system='NONE';scene['Units']='1 Blender unit = 1 Roblox stud'
    scene['Scope']='Visual development only. No production kit, collision, sockets or upload.'
    scene['RouteOverlay']='Toggle Route collection for cyan plan overlay; ten named review cameras.'
    scene.world.color=(.17,.20,.22);scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.29,.33,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    d=bpy.data.lights.new('WarmOvercastSun','SUN');d.energy=2.3;d.angle=.15
    o=bpy.data.objects.new('WarmOvercastSun',d);COLS['ReviewLighting'].objects.link(o);o.rotation_euler=(.38,-.5,-.55)
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=750;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    readme=bpy.data.texts.new('START_HERE')
    readme.write('EMBERFALL AREA II — SELECTED DESIGN BLOCKOUT\n1 unit = 1 stud.\nGate at Y0; AreaII ends at Y1005. Castle beyond is proxy only.\nRoute collection hidden by default; toggle for cyan route and plan labels.\nNamed cameras 01–10. Scene intentionally uses simple revisable masses.\nFire/Smoke separate: toggle to judge identity without glow.\nNo runtime assets, exports, sockets, collision or detailed castle.\nOwner review: scale, gate, district rhythm, architecture, destruction and castle reveal.\n')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
    report={
      'scope':'visual blockout; no production', 'blend':str(OUT/'EmberfallAreaII.blend'),
      'route_studs':sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(ROUTE,ROUTE[1:]))+55,
      'route_points':ROUTE+[(0,1005)],'ascent_studs':elevation(1005)-elevation(0),
      'inhabited_footprint_studs':[640,1005], 'total_preboss_gameplay_minutes':20,
      'pure_walk_minutes_estimate':(sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(ROUTE,ROUTE[1:]))+55)/16.8/60,
      'timing_uncertainty':'Combat, looting, exploration, POIs and transitions included in20min; no per-area walking quota',
      'buildings':BUILDINGS,'building_count':len(BUILDINGS),
      'objects':len(bpy.context.scene.objects),
      'mesh_objects':sum(o.type=='MESH' for o in bpy.context.scene.objects),
      'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'),
      'collections':{c.name:len(c.objects) for c in bpy.context.scene.collection.children},
      'cameras':[v[0] for v in VIEWS],
      'finite_geometry':all(math.isfinite(a) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices for a in v.co),
      'accepted_source_edits':False,'collision_or_sockets':False}
    (OUT/'blockout_report.json').write_text(json.dumps(report,indent=2))
    print('AREAII SAVED',json.dumps({k:report[k] for k in ['objects','building_count','triangles','route_studs','ascent_studs','finite_geometry']}),flush=True)


def render():
    scene=bpy.context.scene
    # CPU path tracing avoids GPU device dependence for this restrained study.
    for name,loc,target,kind,value in VIEWS:
        scene.camera=bpy.data.objects[name]
        COL=bpy.data.collections['Route'];COL.hide_render=True
        COL.hide_viewport=False
        if name=='10_route_plan':COL.hide_render=False
        scene.render.filepath=str(OUT/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        print('AREAII VIEW',name,flush=True)
    # Rendering overlay/camera changes are never saved over owner's review file.

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if '--render-only' not in args:build()
    if '--build-only' not in args:render()
