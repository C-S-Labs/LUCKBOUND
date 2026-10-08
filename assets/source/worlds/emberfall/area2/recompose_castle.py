"""B-first irregular castle composition, then direct impact derivation and shallow arena.
Explicit input BeforeBaselineRework; every Blender operation uses tools/run_blender.py.
"""
import bpy
import importlib.util
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII')
EV=OUT/'BaselineArchitectureReview';EV.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('impact_helpers',ROOT/'correct_castle_impact.py')
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
r=i.r;h=i.h
BC='B_RECOMPOSED_ARCHITECTURE';BR='B_RECOMPOSED_ROOFS'
AC='A_DERIVED_BASELINE';AR='A_DERIVED_ROOFS';AG='A_SHALLOW_ARENA'
B_ROUTE=[(0,1005,56),(0,1130,83),(0,1214,96),(0,1255,96),(20,1330,96),(20,1380,96),(110,1395,96),(155,1420,96),(155,1496,120),(160,1542,120),(100,1542,120),(23,1585,120)]
A_ROUTE=[(0,1005,56),(0,1130,83),(0,1214,96),(0,1255,96),(-92,1255,96),(-92,1320,96),(-92,1385,96),(-92,1420,98),(-92,1460,93),(20,1545,92)]
# Shorter, unequal blocks; there is no pair of350stud wings or long axial nave.
PLAN=[
 {'id':'Entry','x':0,'y':1255,'w':110,'d':82,'z':96,'h':38,'roof':'hip','rise':17,'doors':{'S':(0,38),'N':(0,44)},'derive':False},
 {'id':'EastBarracks','x':155,'y':1325,'w':106,'d':100,'z':96,'h':44,'roof':'shed','rise':12,'doors':{'W':(0,34),'N':(0,34)}},
 {'id':'WestHousehold','x':-183,'y':1395,'w':98,'d':112,'z':96,'h':60,'roof':'hip','rise':22,'upper':124,'doors':{'S':(0,34),'E':(0,36)}},
 {'id':'StewardBlock','x':-100,'y':1480,'w':152,'d':140,'z':96,'h':78,'roof':'hip','rise':32,'upper':132,'doors':{'S':(26,40),'N':(0,34),'E':(0,40)}},
 {'id':'TransverseHall','x':34,'y':1401,'w':180,'d':96,'z':96,'h':44,'roof':'hip_x','rise':24,'doors':{'S':(-14,44),'E':(-6,38),'W':(0,36)}},
 {'id':'StairTower','x':155,'y':1458,'w':64,'d':100,'z':96,'h':88,'roof':'flat','rise':0,'doors':{'S':(0,38),'N':(0,38)}},
 {'id':'EastGallery','x':160,'y':1542,'w':76,'d':112,'z':120,'h':38,'roof':'shed','rise':14,'doors':{'S':(0,38),'W':(0,38),'N':(0,34)}},
 {'id':'AudienceHall','x':23,'y':1585,'w':200,'d':138,'z':120,'h':72,'roof':'hip_x','rise':32,'doors':{'E':(-43,38),'N':(-43,38),'W':(0,38)}},
 {'id':'ResidentialTower','x':-166,'y':1644,'w':96,'d':88,'z':120,'h':84,'roof':'flat','rise':0,'upper':156,'doors':{'S':(0,34),'E':(0,36)}},
 {'id':'ArchiveAnnex','x':-57,'y':1667,'w':120,'d':70,'z':120,'h':48,'roof':'shed','rise':14,'doors':{'S':(37,38),'W':(0,34)}},
 {'id':'KitchenStore','x':175,'y':1694,'w':112,'d':104,'z':96,'h':36,'roof':'shed','rise':12,'doors':{'S':(0,38)}},
 {'id':'RearKeep','x':-96,'y':1717,'w':156,'d':118,'z':120,'h':134,'roof':'hip','rise':34,'upper':164,'doors':{'S':(36,38)}},
]
VIEWS=[
 ('01_B_irregular_overview','B',(-640,1190,510),(0,1500,158),'ORTHO',790,''),
 ('02_B_settlement_player','B',(-85,155,12),(-70,1580,230),'PERSP',26,''),
 ('03_B_interior_progression','B',(20,1370,102),(135,1438,109),'PERSP',23,''),
 ('04_B_recent_destruction','B',(-230,1485,245),(-160,1405,130),'PERSP',26,''),
 ('05_A_derived_overview','A',(-640,1190,510),(0,1500,158),'ORTHO',790,''),
 ('06_A_shallow_basin_player','A',(-92,1420,103),(20,1560,94),'PERSP',22,''),
 ('07_A_combat_basin_plan','A',(20,1545,900),(20,1545,92),'ORTHO',470,''),
 ('08_B_baseline_section','B',(-470,1270,450),(0,1515,140),'ORTHO',710,'roofless'),
 ('09_A_derived_section','A',(-470,1270,450),(0,1515,140),'ORTHO',710,'roofless'),
]


def collection(name,parent=None):return r.new_collection(name,parent)


def recovery():
 if 'PRE_BASELINE_CASTLE_RETAINED' not in h.COLS:
  c=collection('PRE_BASELINE_CASTLE_RETAINED');c.hide_render=True;c.hide_viewport=True
 return h.COLS['PRE_BASELINE_CASTLE_RETAINED']


def archive_objects(col):
 target=recovery()
 for o in list(col.objects):col.objects.unlink(o);target.objects.link(o)


def bool_difference(obj,cutter):
 if obj.type!='MESH':return
 bpy.context.view_layer.update()
 bpy.context.view_layer.objects.active=obj
 mod=obj.modifiers.new('BlockoutVolumeRemoval','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name)


def cut_box(obj,loc,size):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);c=bpy.context.object;c.scale=size
 bool_difference(obj,c);bpy.data.objects.remove(c,do_unlink=True)


def roof(name,p,col):
 x,y,w,d,z,hh=p['x'],p['y'],p['w']+8,p['d']+8,p['z']+p['h'],p['rise']
 typ=p['roof']
 if typ=='flat':
  r.slab(name,x,y,z+4,w,d,col,'Fieldstone',5)
  for yy in [y-d/2,y+d/2]:h.box(name+'_Parapet',(x,yy,z+9),(w,5,14),col,'FreshStone')
  for xx in [x-w/2,x+w/2]:h.box(name+'_Parapet',(xx,y,z+9),(5,d,14),col,'FreshStone')
  return
 v=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)]
 if typ=='shed':
  v.extend([(a,b,z+3+(hh if j in [2,3] else 0)) for j,(a,b,c) in enumerate(v)])
  f=[(0,3,2,1),(4,5,6,7)]+[(j,(j+1)%4,(j+1)%4+4,j+4) for j in range(4)]
 elif typ=='hip_x':
  v.extend([(x-w*.27,y,z+hh),(x+w*.27,y,z+hh)])
  f=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(0,3,2,1)]
 else:
  v.extend([(x,y-d*.27,z+hh),(x,y+d*.27,z+hh)])
  f=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(0,3,2,1)]
 h.mesh(name,v,f,col,'CastleRoof')


def block(p):
 name='B_Composed_'+p['id'];before=set(bpy.data.objects)
 r.room(name,p['x'],p['y'],p['z'],p['w'],p['d'],p['h'],BC,BR,p['doors'])
 bpy.data.objects.remove(bpy.data.objects[name+'_Roof'],do_unlink=True)
 roof(name+'_Roof',p,BR)
 if 'upper' in p:r.slab(name+'_UpperFloor',p['x'],p['y'],p['upper'],p['w']-6,p['d']-6,BC,'Paving',6)
 for o in set(bpy.data.objects)-before:o['castle_block']=p['id'];o['derive_from_baseline']=p.get('derive',True)
 return name


def damage_b():
 # Remove actual roof/wall volume; rubble never fills the main route or arena center.
 cuts=[('WestHousehold_Roof',(-165,1420,185),(70,75,90)),('TransverseHall_Roof',(82,1406,166),(82,66,70)),('StewardBlock_Roof',(-47,1500,211),(95,95,120)),('KitchenStore_Roof',(195,1690,152),(88,96,80))]
 for suffix,loc,size in cuts:cut_box(bpy.data.objects['B_Composed_'+suffix],loc,size)
 for o in list(h.COLS[BC].objects):
  if o.name.startswith('B_Composed_WestHousehold_NWall'):cut_box(o,(-180,1451,155),(54,14,70))
  if o.name.startswith('B_Composed_EastGallery_EWall'):cut_box(o,(198,1558,165),(15,40,46))
 for o in list(h.COLS[BR].objects):
  if o.name.startswith('B_Composed_StairTower_Roof_Parapet'):cut_box(o,(181,1501,196),(30,30,58))
 # B-specific gatehouse/crown geometry, not accepted town walls.
 for o in list(h.COLS['CASTLE_B_STRONGHOLD'].objects):
  if o.name.startswith('CastleGatehouseRoof'):cut_box(o,(31,1228,193),(48,48,48))
 for x,y,z,rad in [(-180,1415,97,22),(-30,1494,133,16),(212,1565,121,17),(197,1700,97,25)]:r.debris('B_RecentLocalizedCollapse',x,y,z,rad,BC,14)
 for name,a,b in [('HouseholdRoofFall',(-218,1420,166),(-157,1435,98)),('StewardFloorBeam',(-25,1490,167),(-57,1505,134)),('KitchenRafter',(186,1690,143),(220,1707,99))]:h.beam('B_'+name,a,b,4,BC,'CharredTimber')
 for x,y,z in [(-200,1404,157),(-45,1495,177),(200,1565,144),(187,1682,131)]:r.small_fire('B_ActiveBurnZone',x,y,z,BC,10)
 for x,y,z in [(-165,1400,160),(78,1400,140),(-45,1500,174)]:
  for yy in [y-14,y+14]:h.beam('B_ExposedBurnedRoofRib',(x-24,yy,z),(x+19,yy,z+12),3,BR,'CharredTimber')


def build_b():
 assert BC not in bpy.data.collections,'Baseline already composed; explicit rebuild input required'
 bpy.context.window.view_layer=bpy.context.scene.view_layers['VARIANT_B_STRONGHOLD']
 before=i.preserve_shared()
 entrance={o.name:r.geometry_hash(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}
 # Remove the paired wings/central pitched hall; preserve source objects in hidden recovery.
 for name in ['B_BASELINE_ENCLOSED_PALACE','B_BASELINE_ROOFS','B_SurvivingRoofs','B_ROUTE']:archive_objects(h.COLS[name])
 for o in list(h.COLS['CASTLE_EXTERIOR_SHARED'].objects):
  if o.name.startswith(('CastleKeep_','KeepBatteredButtress')):
   h.COLS['CASTLE_EXTERIOR_SHARED'].objects.unlink(o);recovery().objects.link(o)
 collection(BC,'CASTLE_B_STRONGHOLD');collection(BR,'CASTLE_B_STRONGHOLD')
 r.slab('B_RecomposedSubfloor',0,1490,95.75,500,580,BC,'Paving',14)
 bpy.data.objects['B_RecomposedSubfloor']['derive_from_baseline']=False
 for p in PLAN:block(p)
 r.slab('B_ArrivalCourt',20,1327,96.1,140,58,BC)
 r.slab('B_WestPocketCourt',-207,1564,96.1,60,44,BC)
 r.slab('B_EastServiceCourt',186,1619,120.1,94,40,BC)
 r.slab('B_CrossTowerLink',139,1419,96.05,34,96,BC)
 h.box('B_CrossTowerLinkRoof',(139,1419,139),(34,96,5),BR,'Fieldstone')
 for k in range(28):h.box('B_TowerStair',(155,1428+k*2,96+(k+1)*24/28-24/56),(40,2.1,24/28),BC,'FreshStone')
 r.slab('B_TowerUpperLanding',155,1496,120,56,26,BC,'Paving',6)
 r.slab('B_KeepRaisedFoundation',-96,1717,120,156,118,BC,'Fieldstone',24)
 for yy in [1544,1585,1626]:
  for sx in [-1,1]:h.box('B_AudiencePerimeterSupport',(23+sx*86,yy,153),(10,12,66),BC,'FreshStone')
 r.slab('B_AudienceFinalBossDais',23,1607,123,64,36,BC,'Fieldstone')
 damage_b()
 for name,loc,e in [('CrossHall',(25,1380,117),240000),('Stair',(155,1470,117),220000),('Gallery',(160,1542,140),220000),('Audience',(23,1550,159),300000),('AudienceRear',(23,1610,164),280000)]:r.point_light('B_ComposedReviewFill_'+name,loc,BC,e)
 r.path('B_ComposedRoute',B_ROUTE,4,'B_ROUTE','RouteCyan')
 assert before==i.preserve_shared()
 report={'base_checkpoint':'ec0840a','shared_geometry_exact':True,'shared_hashes':before,'A_entrance_hashes':entrance,'plan':PLAN,'B_route':B_ROUTE,'B_route_studs':r.length(B_ROUTE),'B_first_reviewed':False,'A_derived':False,'castle_footprint_studs':[500,580],'views':[v[0] for v in VIEWS],'blend':str(OUT/'EmberfallAreaII.blend')}
 (EV/'architecture_report.json').write_text(json.dumps(report,indent=2))
 make_cameras()
 bpy.context.window.view_layer=bpy.context.scene.view_layers['VARIANT_B_STRONGHOLD'];bpy.context.scene.camera=bpy.data.objects['BASELINE_01_B_irregular_overview']
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 print('B BASELINE SAVED FIRST',r.length(B_ROUTE),flush=True)


def make_cameras():
 col=collection('BASELINE_REVIEW_CAMERAS')
 for name,variant,loc,target,kind,value,mode in VIEWS:
  d=bpy.data.cameras.new('BASELINE_'+name);o=bpy.data.objects.new('BASELINE_'+name,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_end=6000;d.clip_start=.1
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value;d.sensor_width=36


def derive_a():
 assert BC in bpy.data.collections and AC not in bpy.data.collections
 report=json.loads((EV/'architecture_report.json').read_text())
 # Preserve the short entrance and exterior A wounds; retire the obsolete deep crater/long-wing fragments.
 for name in ['A_IMPACT_ARCHITECTURE_REMNANTS','A_IMPACT_ROOF_REMNANTS','A_ROUTE']:archive_objects(h.COLS[name])
 keep=('A_EntryHall','A_WestGuardHall','A_FailingGallery','A_BrokenGatehouseRoof','A_GatehouseExposedRafter','A_FracturedFrontCurtain','A_SurvivingCurtainCrown','A_ExteriorRecentWallFall','A_BrokenTowerTop','A_RevealLedge','A_EntryReviewFill','A_GuardReviewFill')
 for o in list(h.COLS['CASTLE_A_CATASTROPHE'].objects):
  if o.name.startswith(keep):continue
  h.COLS['CASTLE_A_CATASTROPHE'].objects.unlink(o);recovery().objects.link(o)
 collection(AC,'CASTLE_A_CATASTROPHE');collection(AR,'CASTLE_A_CATASTROPHE');collection(AG,'CASTLE_A_CATASTROPHE')
 bpy.context.window.view_layer=bpy.context.scene.view_layers['VARIANT_A_CATASTROPHE']
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=1,depth=500,location=(20,1545,240))
 cutter=bpy.context.object;cutter.scale=(175,185,1);cutter.name='ImpactRemovalStudy'
 counts={'copied_meshes':0,'fully_removed_meshes':0,'cut_meshes':0};sources={}
 for sourcecol,targetcol in [(BC,AC),(BR,AR)]:
  for src in list(h.COLS[sourcecol].objects):
   if src.type!='MESH' or not src.get('derive_from_baseline',True):continue
   o=src.copy();o.data=src.data.copy();h.COLS[targetcol].objects.link(o);o.name='A_From_'+src.name;o['baseline_source']=src.name
   counts['copied_meshes']+=1
   bbox=[o.matrix_world@Vector(v) for v in o.bound_box]
   overlap=max(v.x for v in bbox)>-155 and min(v.x for v in bbox)<195 and max(v.y for v in bbox)>1360 and min(v.y for v in bbox)<1730
   if overlap:bool_difference(o,cutter);counts['cut_meshes']+=1
   if not o.data.polygons:
    bpy.data.objects.remove(o,do_unlink=True);counts['fully_removed_meshes']+=1
   else:sources[o.name]=src.name
 bpy.data.objects.remove(cutter,do_unlink=True)
 shallow_basin()
 r.path('A_ShallowRoute',A_ROUTE,4,'A_ROUTE','RouteCyan')
 r.point_light('A_BaselineRemnantFill',(-120,1490,155),AC,160000)
 r.point_light('A_BasinReviewFill',(100,1600,140),AC,140000)
 assert report['shared_hashes']==i.preserve_shared()
 assert all(r.geometry_hash(bpy.data.objects[n])==v for n,v in report['A_entrance_hashes'].items())
 report.update({'B_first_reviewed':True,'A_derived':True,'A_source_map':sources,'derivation_counts':counts,'A_route':A_ROUTE,'A_route_studs':r.length(A_ROUTE),'arena_center':[20,1545,92],'flat_arena_diameters_studs':[300,320],'rim_z':96,'depression_studs':4,'transition_run_studs':25,'max_transition_grade':4/25,'main_arena_fully_flat':True,'no_production':True})
 (EV/'architecture_report.json').write_text(json.dumps(report,indent=2))
 scene=bpy.context.scene;scene['CastleConcept']='B irregular damaged castle first; A directly copied/cut from B around a flat shallow boss basin'
 scene['Timing']='20min TOTAL gameplay; no walking quotas; combat timing unproven'
 t=bpy.data.texts['START_HERE'];t.clear();t.write('EMBERFALL - CURRENT BASELINE ARCHITECTURE REVIEW\nSwitch view layer VARIANT_B_STRONGHOLD / VARIANT_A_CATASTROPHE.\nB: unequal short castle blocks, offset keep, pocket courts, varied rooflines, substantial recent damage.\nA: same B mesh sources cut by impact; preserved short entrance;300x320stud flat basin,4stud depression.\nB_RECOMPOSED_ARCHITECTURE / ROOFS are source of truth. A_DERIVED_BASELINE / ROOFS retain baseline_source metadata.\nSettlement, outer wall, inner wall and grounds unchanged.\nBASELINE_* cameras / BaselineArchitectureReview evidence. Hidden PRE_BASELINE_CASTLE_RETAINED contains obsolete recovery studies.\nNo production/collision/sockets/uploads/boss mechanics. Total20min gameplay; encounter timings unproven.\n')
 bpy.context.window.view_layer=scene.view_layers['VARIANT_B_STRONGHOLD'];scene.camera=bpy.data.objects['BASELINE_01_B_irregular_overview']
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 print('A DIRECTLY DERIVED',json.dumps(counts),flush=True)


def shallow_basin():
 n=32;outer=[];rim=[];inner=[]
 for k in range(n):
  a=k*math.tau/n;co,si=math.cos(a),math.sin(a)
  lx=(250-20)/co if co>0 else (-250-20)/co if co<0 else 1e9
  ly=(1780-1545)/si if si>0 else (1210-1545)/si if si<0 else 1e9
  rr=min(lx,ly);outer.append((20+co*rr,1545+si*rr,95.75));rim.append((20+175*co,1545+185*si,96));inner.append((20+150*co,1545+160*si,92))
 faces=[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
 h.mesh('A_PeripheralShellLand',outer+rim,faces,AG,'CharredGround')
 h.mesh('A_ShallowImpactTransition',rim+inner,faces,AG,'FreshStone')
 h.mesh('A_FLAT_FINAL_BOSS_BASIN',[(20,1545,92)]+inner,[(0,k+1,(k+1)%n+1) for k in range(n)],AG,'Paving')
 # Impact debris belongs outside the flat combat floor; no central rubble obstacle pass.


def render(selected=None):
 scene=bpy.context.scene;scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.cycles.samples=24
 for name,variant,loc,target,kind,value,mode in VIEWS:
  if selected and name not in selected:continue
  layer='VARIANT_A_CATASTROPHE' if variant=='A' else 'VARIANT_B_STRONGHOLD';bpy.context.window.view_layer=scene.view_layers[layer]
  for roofs in [BR,AR]:
   if roofs in bpy.data.collections:bpy.data.collections[roofs].hide_render=mode=='roofless'
  for route in ['Route','A_ROUTE','B_ROUTE']:bpy.data.collections[route].hide_render=True
  scene.camera=bpy.data.objects['BASELINE_'+name];scene.render.filepath=str(EV/(name+'.png'))
  bpy.ops.render.render(write_still=True,layer=layer);print('BASELINE VIEW',name,flush=True)
 # Render-only visibility changes never saved.


if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--adjust-baseline-review' in args:
  steps=sorted([o for o in h.COLS[BC].objects if o.name.startswith('B_TowerStair')],key=lambda o:int(o.name.rsplit('.',1)[1]) if '.' in o.name else 0)
  for k,o in enumerate(steps):o.location.y=1428+k*2
  o=bpy.data.objects['B_TowerUpperLanding'];o.location.y=1496;o.scale.y=26
  bpy.data.objects['B_CrossTowerLink'].location.z=94.55
  for name,variant,loc,target,kind,value,mode in VIEWS:
   o=bpy.data.objects['BASELINE_'+name];o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
  print('DAMAGED ROOF COUNTS',[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in h.COLS[BR].objects if o.type=='MESH' and o.name.endswith('_Roof')],flush=True)
 if '--derive-a' in args:derive_a()
 elif '--render-only' not in args:build_b()
 selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),None)
 if '--baseline-only' in args or ('--derive-a' not in args and '--render-only' not in args):selected=[v[0] for v in VIEWS if v[1]=='B' and v[0].startswith(('01','02','03','04'))]
 if '--build-only' not in args:render(selected)
