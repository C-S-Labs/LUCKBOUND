"""Revise the owner-reviewed AreaII scene in place; shared town, two finale studies.
Run through tools/run_blender.py with the saved EmberfallAreaII.blend loaded.
No production geometry, collision, sockets, assets or boss mechanics.
"""
import bpy
import importlib.util
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII')
EVIDENCE=OUT/'CastleVariantsReview'
EVIDENCE.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('area2_helpers',ROOT/'build_area2.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
h.COLS={c.name:c for c in bpy.data.collections}
h.MATS={m.name:m for m in bpy.data.materials}
RNG=random.Random(307)
FLOOR=96
A_ROUTE=[(0,1005,56),(0,1130,83),(0,1214,96),(0,1255,96),(-92,1255,96),(-92,1320,96),(-92,1385,96),(-92,1425,98),(-152,1460,100),(-144,1550,96),(-92,1600,75),(-42,1580,58),(0,1545,52)]
B_ROUTE=[(0,1005,56),(0,1130,83),(0,1230,96),(60,1280,96),(110,1280,96),(110,1360,96),(110,1462,110),(72,1490,110),(0,1518,110),(0,1580,110),(0,1635,110)]
VIEWS=[
 ('01_shared_overall_plan','A',(0,810,2500),(0,810,0),'ORTHO',3700,'plan'),
 ('02_shared_outer_approach','A',(0,-210,-3),(0,0,23),'PERSP',27,''),
 ('03_shared_settlement_progression','A',(-300,705,170),(20,500,26),'PERSP',26,''),
 ('04_shared_inner_wall_approach','A',(80,865,56),(0,1005,96),'PERSP',25,''),
 ('05_shared_inner_gate_threshold','A',(0,981,61),(0,1220,146),'PERSP',24,''),
 ('06_A_settlement_castle','A',(240,700,110),(0,1500,170),'PERSP',29,''),
 ('07_A_exterior_approach','A',(-470,1090,210),(0,1500,160),'PERSP',24,''),
 ('08_A_surviving_room_sequence','A',(12,1240,102),(-86,1255,108),'PERSP',23,''),
 ('09_A_crater_reveal','A',(-92,1420,104),(5,1550,66),'PERSP',22,''),
 ('10_A_crater_boss_overview','A',(-380,1310,370),(0,1550,69),'ORTHO',620,'roofless'),
 ('11_B_settlement_castle','B',(240,700,110),(0,1500,170),'PERSP',29,''),
 ('12_B_exterior_approach','B',(-470,1090,210),(0,1500,160),'PERSP',24,''),
 ('13_B_surviving_interior','B',(110,1330,102),(110,1415,110),'PERSP',23,''),
 ('14_B_architectural_final_arena','B',(0,1571,116),(0,1672,130),'PERSP',22,''),
 ('15A_matched_silhouette','A',(-660,985,300),(0,1480,150),'ORTHO',820,''),
 ('15B_matched_silhouette','B',(-660,985,300),(0,1480,150),'ORTHO',820,''),
 ('16A_footprint_plan','A',(0,1410,1600),(0,1410,96),'ORTHO',1390,'plan'),
 ('16B_footprint_plan','B',(0,1410,1600),(0,1410,96),'ORTHO',1390,'plan'),
]


def new_collection(name,parent=None):
    c=h.collection(name)
    if parent:
        bpy.context.scene.collection.children.unlink(c)
        h.COLS[parent].children.link(c)
    return c


def geometry_hash(o):
    sha=hashlib.sha256()
    sha.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
    if o.type=='MESH':
        sha.update(str([tuple(v.co) for v in o.data.vertices]).encode())
        sha.update(str([tuple(p.vertices) for p in o.data.polygons]).encode())
        sha.update(str([p.material_index for p in o.data.polygons]).encode())
        sha.update(str([m.name for m in o.data.materials]).encode())
    return sha.hexdigest()


def relink(c,parent):
    for p in [bpy.context.scene.collection,*list(bpy.data.collections)]:
        if c.name in p.children:p.children.unlink(c)
    h.COLS[parent].children.link(c)


def castle_tower(name,x,y,z,height,col,r=27):
    h.cylinder(name+'_BatteredPlinth',(x,y,z+4),r+5,8,col,'Fieldstone')
    h.cylinder(name+'_Masonry',(x,y,z+height/2),r,height,col,'Fieldstone')
    for level in [height*.45,height-3]:h.cylinder(name+'_Coping',(x,y,z+level),r+2,3,col,'FreshStone')
    for i in range(8):
        a=i*math.tau/8
        h.box(name+'_Battlement',(x+math.cos(a)*r*.88,y+math.sin(a)*r*.88,z+height+2),(7,7,8),col,'Fieldstone',a)
    for sx in [-1,1]:h.box(name+'_StoutPier',(x+sx*r*.8,y-9,z+18),(10,18,36),col,'Fieldstone')


def wall(name,x,y,z,w,d,height,col,mat='Fieldstone',merlons=True):
    h.box(name,(x,y,z+height/2),(w,d,height),col,mat)
    h.box(name+'_Coping',(x,y,z+height),(w+2,d+3,3),col,'FreshStone')
    if merlons:
        if w>d:
            for xx in range(int(x-w/2+8),int(x+w/2),22):h.box(name+'_Crown',(xx,y,z+height+4),(10,d,7),col,mat)
        else:
            for yy in range(int(y-d/2+8),int(y+d/2),22):h.box(name+'_Crown',(x,yy,z+height+4),(w,10,7),col,mat)


def slab(name,x,y,z,w,d,col,mat='Paving',thickness=3):
    return h.box(name,(x,y,z-thickness/2),(w,d,thickness),col,mat)


def path(name,points,width,col,mat='Paving',supports=False):
    for i,(a,b) in enumerate(zip(points,points[1:])):
        a,b=Vector(a),Vector(b); delta=b-a
        normal=Vector((-delta.y,delta.x,0)).normalized()*width/2
        v=[a+normal,a-normal,b-normal,b+normal]
        h.mesh(name+'_%02d'%i,[tuple(p+Vector((0,0,.25))) for p in v],[(0,1,2,3)],col,mat)
        if supports:
            mid=(a+b)/2
            h.box(name+'_RoughSupport',(mid.x,mid.y,mid.z-7),(width*.72,9,14),col,'FreshStone')


def room(name,x,y,z,w,d,height,col,roofcol,doors,damaged=False):
    slab(name+'_Floor',x,y,z,w,d,col)
    for side in ['N','S','E','W']:
        span=w if side in ['N','S'] else d
        openings=doors.get(side)
        pieces=[(-span/2,span/2)] if not openings else [(-span/2,openings[0]-openings[1]/2),(openings[0]+openings[1]/2,span/2)]
        for a,b in pieces:
            if b-a<=0:continue
            if side in ['N','S']:
                loc=(x+(a+b)/2,y+(d/2 if side=='N' else -d/2),z+height/2)
                size=(b-a,4,height)
            else:
                loc=(x+(w/2 if side=='E' else -w/2),y+(a+b)/2,z+height/2)
                size=(4,b-a,height)
            h.box(name+'_'+side+'Wall',loc,size,col,'SmokePlaster' if damaged else 'Fieldstone')
        if openings:
            offset,width=openings
            if side in ['N','S']:
                if width<=54:
                    h.arch(name+'_'+side+'Opening',x+offset,y+(d/2 if side=='N' else -d/2),z,width,30,5,col)
                else:
                    h.box(name+'_'+side+'BrokenLintel',(x+offset,y+(d/2 if side=='N' else -d/2),z+height-4),(width,5,7),col,'FreshStone')
            else:
                # Side opening uses simple lintel/piers; avoids a rotated duplicate arch study.
                h.box(name+'_'+side+'Lintel',(x+(w/2 if side=='E' else -w/2),y+offset,z+height-4),(5,width,8),col,'FreshStone')
    # Sparse structural bays, not a finished interior.
    for yy in [y-d*.3,y,y+d*.3]:
        for sx in [-1,1]:h.box(name+'_Pier',(x+sx*(w/2-3),yy,z+height/2),(7,7,height),col,'FreshStone')
        h.beam(name+'_RoofTie',(x-w/2,yy,z+height-3),(x+w/2,yy,z+height-3),2,col,'Timber')
    h.roof(name+'_Roof',x,y,z+height,w+8,d+8,w*.23,roofcol,'CastleRoof',half=damaged)


def point_light(name,loc,col,energy=120000):
    d=bpy.data.lights.new(name,'POINT');d.energy=energy;d.shadow_soft_size=14;d.color=(1,.87,.7)
    o=bpy.data.objects.new(name,d);h.COLS[col].objects.link(o);o.location=loc


def small_fire(name,x,y,z,col,scale=7):
    for i in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=scale*.26,radius2=0,depth=scale,location=(x+i*scale*.25,y,z+scale*.42))
        h.assign(bpy.context.object,name,col,'FireAmber')


def debris(name,x,y,z,r,col,count=12):
    for i in range(count):
        a=RNG.random()*math.tau;rr=RNG.random()*r
        o=h.box(name,(x+math.cos(a)*rr,y+math.sin(a)*rr,z+RNG.uniform(1,4)),(RNG.uniform(3,9),RNG.uniform(3,8),RNG.uniform(2,6)),col,'FreshStone',a)
        o.rotation_euler[0]=RNG.uniform(-.4,.4)


def shared_changes():
    new_collection('AREA_II_SHARED')
    for name in ['Terrain','OuterWall','EarlySettlement','MidSettlement','LateSettlement','Streets','CivilLife','Destruction','Vegetation','Fire','Smoke','ScaleFigures','Route']:
        relink(h.COLS[name],'AREA_II_SHARED')
    new_collection('INITIAL_PROXY_RETAINED')
    for name in ['CastleProxy','CastleBoundary']:relink(h.COLS[name],'INITIAL_PROXY_RETAINED')
    oldpath=bpy.data.objects.get('AreaIII_ProxyContinuation')
    if oldpath:
        for c in list(oldpath.users_collection):c.objects.unlink(oldpath)
        h.COLS['INITIAL_PROXY_RETAINED'].objects.link(oldpath)
    oldlabel=bpy.data.objects.get('Plan_CASTLE PROXY')
    if oldlabel:
        for c in list(oldlabel.users_collection):c.objects.unlink(oldlabel)
        h.COLS['INITIAL_PROXY_RETAINED'].objects.link(oldlabel)
    h.COLS['INITIAL_PROXY_RETAINED'].hide_render=True
    h.COLS['INITIAL_PROXY_RETAINED'].hide_viewport=True
    new_collection('LateDistrict_Formality','AREA_II_SHARED')
    # Additive late-district evolution; no accepted19 building group transforms changed.
    for sx in [-1,1]:
        wall('CivicCourtLowMasonry',sx*92,955,54,14,82,10,'LateDistrict_Formality',merlons=False)
        for yy in [924,958]:h.box('LateCivicMasonryPier',(sx*93,yy,61),(12,12,14),'LateDistrict_Formality','FreshStone')
    for name,x,y,w,d,hh,state in [('InnerRecordsHouse',-178,856,42,54,30,'damaged'),('GateStores',217,902,42,62,30,'damaged')]:
        h.building(name,x,y,w,d,hh,'LateDistrict_Formality',state,'RoofChar')
    new_collection('INNER_WALL_SHARED')
    h.arch('InnerSeatOfPowerGate',0,1005,56,44,43,34,'INNER_WALL_SHARED')
    for x in [-164,164]:wall('FormalInnerCurtain',x,1005,56,230,18,52,'INNER_WALL_SHARED')
    for sx in [-1,1]:castle_tower('InnerGateTower',sx*58,1005,56,70,'INNER_WALL_SHARED',25)
    h.box('InnerGateGuardHall',(0,1005,108),(82,40,18),'INNER_WALL_SHARED','Fieldstone')
    h.roof('InnerGateFormalRoof',0,1005,117,88,46,16,'INNER_WALL_SHARED','CastleRoof')
    # Shared forecourt/rising causeway deliberately short and broad.
    new_collection('CASTLE_GROUNDS_SHARED')
    path('RisingGrounds',[(0,1005,56),(0,1130,83),(0,1214,96)],48,'CASTLE_GROUNDS_SHARED')
    v=[];f=[]
    for y,z in [(1005,55.6),(1060,67),(1130,82.5),(1205,95.5)]:
        for x in [-300,-95,95,300]:v.append((x,y,z-(7 if abs(x)==300 else 0)))
    for j in range(3):
        for i in range(3):a=j*4+i;f.append((a,a+1,a+5,a+4))
    h.mesh('CastleGrounds_RisingLand',v,f,'CASTLE_GROUNDS_SHARED','CharredGround')
    slab('ArrivalForecourt',0,1160,88,138,72,'CASTLE_GROUNDS_SHARED')
    for sx in [-1,1]:
        h.box('GroundsRetainingBank',(sx*98,1150,69),(14,126,38),'CASTLE_GROUNDS_SHARED','Fieldstone')
        h.box('GroundsPier',(sx*98,1150,90),(18,18,24),'CASTLE_GROUNDS_SHARED','FreshStone')
    new_collection('CASTLE_EXTERIOR_SHARED')
    h.arch('CastleMainEntrance',0,1210,FLOOR,46,49,36,'CASTLE_EXTERIOR_SHARED')
    for sx in [-1,1]:
        wall('CastleFrontCurtain',sx*155,1210,FLOOR,190,16,66,'CASTLE_EXTERIOR_SHARED')
        wall('CastleSideCurtain',sx*250,1490,FLOOR,16,560,64,'CASTLE_EXTERIOR_SHARED')
        castle_tower('CastleGatehouseTower',sx*61,1210,FLOOR,94,'CASTLE_EXTERIOR_SHARED',27)
        for yy,hh in [(1220,105),(1750,126)]:castle_tower('CastleCornerTower',sx*235,yy,FLOOR,hh,'CASTLE_EXTERIOR_SHARED',30)
    wall('CastleRearCurtain',0,1780,FLOOR,500,16,70,'CASTLE_EXTERIOR_SHARED')
    h.box('CastleGatehouseUpperHall',(0,1210,160),(92,55,28),'CASTLE_EXTERIOR_SHARED','Fieldstone')
    h.roof('CastleGatehouseRoof',0,1210,174,102,66,23,'CASTLE_EXTERIOR_SHARED','CastleRoof')
    h.box('CastleKeep_SkylineMass',(0,1732,FLOOR+80),(154,106,160),'CASTLE_EXTERIOR_SHARED','Fieldstone')
    h.roof('CastleKeep_SkylineRoof',0,1732,FLOOR+160,168,122,32,'CASTLE_EXTERIOR_SHARED','CastleRoof')
    for sx in [-1,1]:h.box('KeepBatteredButtress',(sx*70,1687,FLOOR+45),(15,20,90),'CASTLE_EXTERIOR_SHARED','FreshStone')
    # Peripheral land beyond the castle: no center surface across the A cavity.
    for sx in [-1,1]:slab('CastlePeripheralBank',sx*310,1510,83,105,720,'CASTLE_GROUNDS_SHARED','Earth',36)


def variant_a():
    col='CASTLE_A_CATASTROPHE';new_collection(col)
    roofs='A_SurvivingRoofs';new_collection(roofs,col)
    new_collection('A_ROUTE',col);h.COLS['A_ROUTE'].hide_render=True
    # Rectangle-to-ellipse annulus preserves exterior shell land around a real empty center.
    cx,cy=0,1545;n=32;outer=[];rim=[]
    for i in range(n):
        a=i*math.tau/n;co,si=math.cos(a),math.sin(a)
        limit_x=250/max(abs(co),1e-6)
        limit_y=(235 if si>0 else 345)/max(abs(si),1e-6)
        rr=min(limit_x,limit_y)
        outer.append((co*rr,cy+si*rr,FLOOR))
        breakup=RNG.uniform(.94,1.06)
        rim.append((co*155*breakup,cy+si*165*breakup,FLOOR+RNG.uniform(-3,4)))
    v=outer+rim;f=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    h.mesh('A_CastleShellGround_EmptyCenter',v,f,col,'CharredGround')
    rings=[rim]
    for rx,ry,z in [(129,137,78),(80,86,54),(58,62,51)]:
        rings.append([(math.cos(i*math.tau/n)*rx,cy+math.sin(i*math.tau/n)*ry,z+RNG.uniform(-2,2)) for i in range(n)])
    for j in range(3):
        faces=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        h.mesh('A_CraterFractureBand',rings[j]+rings[j+1],faces,col,'FreshStone' if j==0 else 'CharredGround')
    h.cylinder('A_FINAL_BOSS_SPACE_Floor',(0,1545,49.5),60,3,col,'Paving',24)
    room('A_EntryHall',0,1255,FLOOR,110,82,38,col,roofs,{'S':(0,38),'W':(0,30)})
    room('A_WestGuardHall',-92,1290,FLOOR,74,132,36,col,roofs,{'E':(-35,30),'N':(0,34)})
    room('A_FailingGallery',-92,1385,FLOOR,74,58,33,col,roofs,{'S':(0,34),'N':(0,64)},True)
    slab('A_RevealLedge',-92,1420,98,76,22,col,'FreshStone')
    path('A_MasonryDescent',A_ROUTE[7:],25,col,'FreshStone',True)
    # Scars are local and material-connected; external castle silhouette survives.
    for x,y,z in [(-210,1219,96),(195,1260,96),(175,1480,100),(-172,1570,100),(105,1678,98)]:
        debris('A_FreshDirectedFall',x,y,z,26,col,16)
        h.beam('A_BlastThrownBeam',(x,y,z+6),(x-16,y-23,z+2),3,col,'CharredTimber')
    for x,y in [(-165,1460),(110,1664),(195,1250)]:small_fire('A_ActiveConnectedBurn',x,y,100,col,8)
    for x,y,zz in [(-120,1410,115),(72,1670,140)]:point_light('A_ReviewFill',(x,y,zz),col)
    point_light('A_EntryReviewFill',(0,1248,119),col,220000)
    point_light('A_GuardReviewFill',(-92,1305,117),col,180000)
    # Evidence of vanished central walls; no complete floor/room behind the facade.
    for x,y in [(-150,1490),(147,1530),(82,1680)]:
        h.box('A_SeveredCentralPier',(x,y,103),(11,14,22),col,'Fieldstone')
    path('A_PlanRoute',A_ROUTE,4,'A_ROUTE','RouteCyan')


def variant_b():
    col='CASTLE_B_STRONGHOLD';new_collection(col)
    roofs='B_SurvivingRoofs';new_collection(roofs,col)
    new_collection('B_ROUTE',col);h.COLS['B_ROUTE'].hide_render=True
    slab('B_CompleteCastleGround',0,1490,FLOOR,500,580,col,'Paving',14)
    slab('B_ArrivalCourtyard',22,1290,FLOOR+.1,136,126,col,'Fieldstone')
    room('B_EastGuardHall',110,1360,FLOOR,94,112,40,col,roofs,{'S':(0,36),'N':(0,36)},True)
    # A short broad stair raises the upper architectural sequence.
    for i in range(28):h.box('B_UpperStair',(110,1418+i*1.6,FLOOR+.5*i),(40,1.7,1),col,'FreshStone')
    slab('B_UpperLanding',110,1478,110,72,32,col)
    slab('B_ArenaVestibule',0,1542,110,48,40,col)
    room('B_UpperGallery',22,1503,110,240,42,38,col,roofs,{'E':(0,32),'N':(-22,38)})
    room('B_FINAL_ARENA_Hypothesis',0,1635,110,124,150,60,col,roofs,{'S':(0,38)})
    # Architectural arena stays open centrally: paired supports belong to perimeter.
    for yy in [1590,1635,1680]:
        for sx in [-1,1]:
            h.box('B_ArenaPerimeterColumn',(sx*54,yy,132),(9,10,44),col,'FreshStone')
            h.box('B_ArenaColumnCap',(sx*54,yy,154),(13,14,4),col,'FreshStone')
        for i in range(8):
            xx=-50+i*12.5; nx=xx+12.5
            h.beam('B_ShallowArenaArch',(xx,yy,155+15*(1-(xx/50)**2)),(nx,yy,155+15*(1-(nx/50)**2)),4,col,'FreshStone')
    slab('B_ArchitecturalBossDais',0,1668,113,64,40,col,'Fieldstone')
    # Less complete flanking storage/roof loss signals severe catastrophe without annihilation.
    room('B_WestServiceWing',-156,1400,FLOOR,102,190,43,col,roofs,{'S':(0,32)},True)
    debris('B_OrdinaryRoofFall',-186,1330,97,18,col,18)
    debris('B_EastDamage',194,1430,97,18,col,12)
    small_fire('B_LocalBurn',-197,1400,128,col,5)
    for name,loc,e in [('B_GuardFill',(110,1360,122),220000),('B_GalleryFill',(16,1503,135),220000),('B_ArenaFill',(0,1610,150),300000),('B_ArenaRearFill',(0,1664,152),280000)]:point_light(name,loc,col,e)
    path('B_PlanRoute',B_ROUTE,4,'B_ROUTE','RouteCyan')


def exterior_damage():
    ac='CASTLE_A_CATASTROPHE';bc='CASTLE_B_STRONGHOLD'
    shared=h.COLS['CASTLE_EXTERIOR_SHARED']
    # Intact detail alternatives belong to B; core defensive masses remain shared.
    moved=[]
    for o in list(shared.objects):
        x,y,z=o.location
        choose=o.name=='CastleGatehouseRoof'
        choose|=o.name.startswith('CastleFrontCurtain') and x>58
        choose|=o.name.startswith('CastleCornerTower') and ('Battlement' in o.name or 'Coping' in o.name) and x<-190 and y<1300 and z>180
        if choose:
            shared.objects.unlink(o);h.COLS[bc].objects.link(o);moved.append(o.name)
    h.roof('A_BrokenGatehouseRoof',0,1210,174,102,66,23,ac,'CastleRoof',True)
    for yy in [1182,1210,1238]:h.beam('A_GatehouseExposedRafter',(51,yy,174),(0,yy,197),3,ac,'CharredTimber')
    outline=[(60,55),(90,66),(132,65),(158,47),(185,56),(215,63),(250,66)]
    front=[(60,1202,96),(250,1202,96)]+[(x,1202,96+hh) for x,hh in reversed(outline)]
    back=[(x,1218,z) for x,y,z in front];n=len(front)
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    h.mesh('A_FracturedFrontCurtain',front+back,faces,ac,'Fieldstone')
    for x,z in [(90,162),(120,162),(213,160),(242,162)]:h.box('A_SurvivingCurtainCrown',(x,1210,z),(10,16,7),ac,'Fieldstone')
    debris('A_ExteriorRecentWallFall',174,1192,96,19,ac,20)
    debris('A_BrokenTowerTop',-235,1220,204,24,ac,8)


def labels():
    for col,items in [('A_ROUTE',[('SURVIVING HALLS',-230,1285,145),('CRATER REVEAL',-230,1415,145),('MAIN FINAL BOSS SPACE',-155,1550,65)]),('B_ROUTE',[('COURTYARD',-45,1280,104),('GUARD / STAIR',146,1370,146),('ARCHITECTURAL FINAL BOSS',-125,1635,176)])]:
        for text,x,y,z in items:
            d=bpy.data.curves.new('FinalePlanLabel','FONT');d.body=text;d.size=13
            o=bpy.data.objects.new(text,d);h.COLS[col].objects.link(o);o.location=(x,y,z);d.materials.append(h.MATS['RouteCyan'])


def layer_collection(layer,name):
    def find(c):
        if c.name==name:return c
        for child in c.children:
            r=find(child)
            if r:return r
    return find(layer.layer_collection)


def make_views():
    scene=bpy.context.scene
    scene.view_layers[0].name='VARIANT_A_CATASTROPHE'
    if 'VARIANT_B_STRONGHOLD' not in scene.view_layers:scene.view_layers.new('VARIANT_B_STRONGHOLD')
    layer_collection(scene.view_layers['VARIANT_A_CATASTROPHE'],'CASTLE_B_STRONGHOLD').exclude=True
    layer_collection(scene.view_layers['VARIANT_B_STRONGHOLD'],'CASTLE_A_CATASTROPHE').exclude=True
    bpy.context.window.view_layer=scene.view_layers['VARIANT_A_CATASTROPHE']
    new_collection('CASTLE_REVIEW_CAMERAS')
    for name,variant,loc,target,kind,value,mode in VIEWS:
        d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);h.COLS['CASTLE_REVIEW_CAMERAS'].objects.link(o)
        o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
        d.type=kind;d.clip_end=6000;d.clip_start=.1
        if kind=='ORTHO':d.ortho_scale=value
        else:d.lens=value;d.sensor_width=36
    scene.camera=bpy.data.objects['15A_matched_silhouette']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;sp.clip_end=6000
                sp.region_3d.view_distance=1750;sp.region_3d.view_location=(0,930,90)
                sp.region_3d.view_rotation=bpy.data.objects['15A_matched_silhouette'].rotation_euler.to_quaternion()
                sp.shading.type='MATERIAL'


def length(points):return sum((Vector(b)-Vector(a)).length for a,b in zip(points,points[1:]))


def revise():
    assert bpy.data.filepath and Path(bpy.data.filepath).name=='EmberfallAreaII.blend'
    assert 'CASTLE_A_CATASTROPHE' not in bpy.data.collections,'Already revised: preserve owner edits; do not rebuild automatically'
    originals={o.name:geometry_hash(o) for name in ['Terrain','OuterWall','EarlySettlement','MidSettlement','LateSettlement','CivilLife','Vegetation'] for o in h.COLS[name].objects}
    shared_changes();variant_a();variant_b();exterior_damage();labels();make_views()
    after={name:geometry_hash(bpy.data.objects[name]) for name in originals}
    assert originals==after,'Original settlement geometry changed unexpectedly'
    scene=bpy.context.scene;scene['Scope']='Revised AreaII and two alternate final-boss castle blockouts; no production'
    scene['VariantSelection']='View Layer dropdown: VARIANT_A_CATASTROPHE or VARIANT_B_STRONGHOLD. Shared AreaII/inner gate/exterior once.'
    scene.render.resolution_x=1280;scene.render.resolution_y=800
    scene.render.use_single_layer=True;scene.cycles.samples=24
    scene['Timing']='20min TOTAL gameplay incl combat/loot/POIs/transitions; no per-area walking quotas'
    text=bpy.data.texts.get('START_HERE');text.clear()
    text.write('EMBERFALL — REVISED AREA II / CASTLE VARIANTS\n1 unit = 1 stud.\nUse top-right VIEW LAYER dropdown: VARIANT_A_CATASTROPHE or VARIANT_B_STRONGHOLD.\nOne shared town, inner wall and castle exterior; variant-specific interior/damage.\nA: intact exterior -> three surviving spaces -> crater reveal -> descent/final-boss space.\nB: courtyard -> guard hall -> stairs/gallery -> architectural final arena hypothesis.\nBoth bosses are FINAL bosses of the selected run; B is not a miniboss.\nRoute/A_ROUTE/B_ROUTE hidden in normal rendering; toggle for plan study.\nINITIAL_PROXY_RETAINED is hidden recovery geometry. Initial scene/images/.blend1 preserved in OwnerReview_Input.\n18 named revision cameras create14 single panels+two comparison panels.\nNo production kit/collision/sockets/Roblox upload/mechanics.\n20min total gameplay; do not derive distances from unproven encounter times.\n')
    report={'revision_base':'b1a85cc','blend':str(OUT/'EmberfallAreaII.blend'),'initial_preserved':str(OUT/'OwnerReview_Input'),
      'area2_route_studs':1610.3084187152397,'area2_pure_walk_minutes':1610.3084187152397/16.8/60,
      'area2_footprint_studs':[640,1005],'area2_original_building_groups':19,'new_late_building_groups':2,
      'castle_exterior_footprint_studs':[500,580],'old_proxy_footprint_studs':[220,195],
      'castle_floor_z':96,'castle_keep_peak_z':288,'inner_gate_z':56,
      'variant_A_route_studs':length(A_ROUTE),'variant_B_route_studs':length(B_ROUTE),
      'variant_A_route':A_ROUTE,'variant_B_route':B_ROUTE,
      'crater_diameter_studs':[310,330],'crater_depth_studs':45,'A_boss_space_diameter_studs':120,
      'B_arena_clear_studs':[100,126],'same_inner_interface':[0,1005,56],
      'preserved_original_object_count':len(originals),'preserved_geometry_exact':originals==after,
      'preserved_object_hashes':originals,'timing':'20min total gameplay; combat substantial/largest expected, actual encounter/loot/castle timings unproven',
      'objects':len(scene.objects),'visible_variant_counts':{},'views':[v[0] for v in VIEWS],
      'no_production':True,'no_upload':True,'both_variants_final_boss':True}
    for name in ['VARIANT_A_CATASTROPHE','VARIANT_B_STRONGHOLD']:
        bpy.context.window.view_layer=scene.view_layers[name]
        report['visible_variant_counts'][name]={'objects':len(bpy.context.view_layer.objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.view_layer.objects if o.type=='MESH')}
    bpy.context.window.view_layer=scene.view_layers['VARIANT_A_CATASTROPHE']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
    (EVIDENCE/'revision_report.json').write_text(json.dumps(report,indent=2))
    print('REVISED SAVED',json.dumps({k:report[k] for k in ['objects','preserved_original_object_count','preserved_geometry_exact','variant_A_route_studs','variant_B_route_studs']}),flush=True)


def render():
    scene=bpy.context.scene
    for name,variant,loc,target,kind,value,mode in VIEWS:
        layername='VARIANT_A_CATASTROPHE' if variant=='A' else 'VARIANT_B_STRONGHOLD'
        bpy.context.window.view_layer=scene.view_layers[layername]
        for route in ['Route','A_ROUTE','B_ROUTE']:bpy.data.collections[route].hide_render=mode=='plan' and False or True
        if mode=='plan':
            for route in ['Route','A_ROUTE','B_ROUTE']:bpy.data.collections[route].hide_render=False
        for roofs in ['A_SurvivingRoofs','B_SurvivingRoofs']:bpy.data.collections[roofs].hide_render=mode in ['plan','roofless']
        scene.camera=bpy.data.objects[name];scene.render.filepath=str(EVIDENCE/(name+'.png'))
        bpy.ops.render.render(write_still=True,layer=layername)
        print('CASTLE VIEW',name,flush=True)
    # Do not save render-only camera/roof/route visibility changes.

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if '--update-cameras' in args:
        for name,variant,loc,target,kind,value,mode in VIEWS:
            o=bpy.data.objects[name];o.location=loc
            if kind=='PERSP':o.data.lens=value
            else:o.data.ortho_scale=value
            o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
    selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),None)
    if selected:VIEWS=[v for v in VIEWS if v[0] in selected]
    if '--render-only' not in args:revise()
    if '--build-only' not in args:render()
