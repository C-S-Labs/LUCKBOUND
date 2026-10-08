"""A-only impact aftermath: deliberate structural bay failures, not a circular architecture cut."""
import bpy,importlib.util,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('final_helpers',ROOT/'final_castle_corrections.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
s=f.s;m=f.m;h=f.h;r=f.r;c=f.c;OUT=f.OUT;EV=OUT/'ImpactStructuralReview';EV.mkdir(exist_ok=True);scene=bpy.context.scene
COL='A_STRUCTURAL_IMPACT_FAILURE'
VIEWS=[('01_overhead',(20,1545,980),(20,1545,96),'ORTHO',900),('02_oblique',(350,1190,610),(20,1545,115),'ORTHO',570),('03_broken_walls',(-20,1510,190),(-142,1650,161),'PERSP',28),('04_stairs',(80,1490,160),(176,1434,110),'PERSP',35),('05_surviving_supports',(60,1630,185),(-104,1745,192),'PERSP',27)]

def cameras():
 col=r.new_collection('IMPACT_STRUCTURE_REVIEW_CAMERAS')
 for name,loc,target,kind,val in VIEWS:
  ident='IMPACT_'+name
  if ident in bpy.data.objects:o=bpy.data.objects[ident];d=o.data
  else:d=bpy.data.cameras.new(ident);o=bpy.data.objects.new(ident,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_end=6000
  if name=='01_overhead':o.rotation_euler=(0,0,0)
  if kind=='ORTHO':d.ortho_scale=val
  else:d.lens=val

def render(stage,selected=None):
 m.use('A');cameras();scene.render.resolution_x=1200;scene.render.resolution_y=850;scene.cycles.samples=20
 for col in ['Route','A_ROUTE','B_ROUTE']:h.COLS[col].hide_render=True
 for name,*rest in VIEWS:
  if selected and name not in selected:continue
  scene.camera=bpy.data.objects['IMPACT_'+name];scene.render.filepath=str(EV/(name+'_'+stage+'.png'));bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name);print('IMPACT VIEW',name,stage,flush=True)

def tag(o,source,why):
 o['baseline_source']=source;o['failure_reason']=why;return o

def slab(name,poly,z,depth,source,mat='Fieldstone',heights=None):
 n=len(poly);tops=heights or [z]*n;v=[(x,y,t-depth) for (x,y),t in zip(poly,tops)]+[(x,y,t) for (x,y),t in zip(poly,tops)]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
 return tag(h.mesh(name,v,faces,COL,mat),source,'Floor/roof bay fractures retreat to surviving perimeter walls; independent of basin outline')

def wall(name,axis,fixed,profile,bottom,width,source):
 poly=[(profile[0][0],bottom)]+profile+[(profile[-1][0],bottom)];n=len(poly);verts=[]
 for dd in [-width/2,width/2]:
  verts.extend([(a,fixed+dd,z) if axis=='X' else (fixed+dd,a,z) for a,z in poly])
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
 o=tag(h.mesh(name,verts,faces,COL,'Fieldstone'),source,'Stepped masonry failure; substantial grounded corner remains, missing upper bays collapse farther back')
 o.data.materials.append(h.MATS['FreshStone'])
 for p in o.data.polygons:
  if p.index>1:p.material_index=1
 return o

def apply():
 assert COL not in bpy.data.collections,'Already applied'
 m.use('B');protected={'B':{o.name:m.signature(o) for col in [m.BC,m.BR,s.BS,'B_ROUTE'] for o in h.COLS[col].all_objects},'exterior':m.hashes('CASTLE_EXTERIOR_SHARED'),'shared':c.i.preserve_shared()}
 m.use('A');protected.update({'flat_floor':m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN']),'route':m.hashes('A_ROUTE'),'entry':{o.name:m.signature(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}})
 rec=r.new_collection('PRE_IMPACT_FAILURE_RETAINED');rec.hide_render=True;rec.hide_viewport=True;r.new_collection(COL,'CASTLE_A_CATASTROPHE');retired=[]
 def retire(o):
  if o in rec.objects.values():return
  retired.append({'name':o.name,'source':o.get('baseline_source')})
  for col in list(o.users_collection):col.objects.unlink(o)
  rec.objects.link(o);o.name='RECOVERED_IMPACT_'+o.name
 def drop_source(prefix):
  for col in [m.AC,m.AR,s.AS]:
   for o in list(h.COLS[col].objects):
    if str(o.get('baseline_source','')).startswith(prefix):retire(o)
 def drop(names):
  for name in names:
   for col in [m.AC,m.AR,s.AS]:
    for o in list(h.COLS[col].objects):
     if o.get('baseline_source')==name:retire(o)
 # Restore a near-circular basin rim; architecture no longer shares its contour.
 for name in ['A_PeripheralShellLand','A_ShallowImpactTransition']:
  o=bpy.data.objects[name];inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   w=o.matrix_world@v.co;rr=math.hypot((w.x-20)/175,(w.y-1545)/185)
   if .90<rr<1.10:
    a=math.atan2((w.y-1545)/185,(w.x-20)/175);factor=1+.008*math.sin(3*a+.4)
    w.x=20+175*math.cos(a)*factor;w.y=1545+185*math.sin(a)*factor;w.z=96;v.co=inv@w
  o.data.update()
 # Gallery has no viable floor or opposite bearing wall. Remove the entire failed bay.
 for prefix in ['B_Composed_EastGallery','B_SolidRaisedFoundation_Gallery','B_STRUCT_Gallery','B_Composed_ArchiveAnnex','B_STRUCT_Archive','B_TowerStair','B_Composed_StairTower','B_CrossTowerLink']:
  drop_source(prefix)
 drop(['B_ActiveBurnZone','B_ActiveBurnZone.001','B_ActiveBurnZone.002','B_ActiveBurnZone.006','B_ActiveBurnZone.007','B_ActiveBurnZone.008','B_ActiveBurnZone.009','B_ActiveBurnZone.010','B_ActiveBurnZone.011'])
 drop_source('B_STRUCT_Household')
 # Surviving eastern stair-tower corner: low connected cheek/flight, no tapering suspended treads.
 slab('A_StairCornerFooting',[(174,1408),(190,1408),(190,1460),(181,1460),(177,1449),(174,1449)],96,3,'B_Composed_StairTower_Floor')
 wall('A_StairTowerGroundedEastCorner','Y',187,[(1408,146),(1424,144),(1429,129),(1435,135),(1441,119),(1453,114),(1460,100)],96,6,'B_Composed_StairTower_EWall')
 wall('A_StairBrokenSouthReturn','X',1408,[(174,134),(180,138),(190,146)],96,5,'B_Composed_StairTower_SWall.001')
 for k in range(8):tag(h.box('A_BrokenStairGroundedTread',(181,1418+3*k,96+(k+1)*1.1/2),(14,3,1.1*(k+1)),COL,'Paving'),'B_TowerStair','Grounded lower flight only; upper stair/landing failed')
 slab('A_StairInterruptedLanding',[(174,1441),(189,1441),(189,1448),(183,1448),(178,1446),(174,1446)],104.8,8.8,'B_TowerStair')
 # Steward bay fails substantially; keep a lower L-shaped outer-wall remnant, not a high thin slice.
 drop_source('B_Composed_StewardBlock');drop_source('B_STRUCT_Steward')
 wall('A_StewardWestFracture','Y',-176,[(1410,146),(1441,150),(1446,135),(1465,139),(1473,124),(1512,128),(1517,109),(1550,103)],96,6,'B_Composed_StewardBlock_WWall')
 wall('A_StewardSouthReturn','X',1410,[(-176,146),(-162,137),(-160,119),(-142,108),(-138,99)],96,6,'B_Composed_StewardBlock_SWall')
 slab('A_StewardGroundFloorRemnant',[(-176,1410),(-138,1410),(-147,1432),(-159,1439),(-158,1472),(-167,1480),(-166,1520),(-176,1550)],96,3,'B_Composed_StewardBlock_Floor')
 # Transverse hall collapses through a roof bay; primary front remains connected to intact entry.
 drop_source('B_Composed_TransverseHall_RoofTie');drop_source('B_Composed_TransverseHall_Pier');drop_source('B_Composed_TransverseHall_ELintel');drop_source('B_Composed_TransverseHall_Roof')
 drop_source('B_STRUCT_PrimaryHallHaunch');drop_source('B_PRIMARY_INTERIOR_PORTAL_ArchSector')
 wall('A_HallFrontBrokenCrownLeft','X',1353,[(-56,140),(-23,140),(-20,125),(-6,116)],96,5,'B_PrimaryHallFront')
 wall('A_HallFrontBrokenCrownRight','X',1353,[(46,118),(62,128),(68,125),(84,140),(124,140)],96,5,'B_PrimaryHallFront.001')
 drop(['B_PrimaryHallFront','B_PrimaryHallFront.001'])
 slab('A_HallRoofWallSeatedRemnant',[(-60,1349),(-12,1349),(-17,1360),(-30,1363),(-33,1359),(-60,1364)],142,3,'B_Composed_TransverseHall_Roof','CastleRoof')
 # Household north/east corner loses the upper room; remaining south roof stays identifiable.
 drop(['B_Composed_WestHousehold_NWall','B_Composed_WestHousehold_EWall.001','B_Composed_WestHousehold_ELintel','B_Composed_WestHousehold_Roof','B_Composed_WestHousehold_UpperFloor','B_Composed_WestHousehold_RoofTie.001','B_Composed_WestHousehold_RoofTie.002','B_STRUCT_Household_BreachRib.001'])
 wall('A_HouseholdNorthBrokenReturn','X',1451,[(-232,156),(-207,153),(-202,137),(-190,142),(-183,122),(-160,107)],96,5,'B_Composed_WestHousehold_NWall')
 wall('A_HouseholdEastBrokenEnd','Y',-134,[(1413,121),(1420,115),(1426,98)],96,5,'B_Composed_WestHousehold_EWall.001')
 slab('A_HouseholdUpperRoomFragment',[(-229,1342),(-137,1342),(-137,1370),(-174,1370),(-182,1382),(-229,1382)],124,6,'B_Composed_WestHousehold_UpperFloor')
 slab('A_HouseholdSurvivingSouthRoof',[(-236,1335),(-130,1335),(-130,1374),(-148,1374),(-157,1383),(-195,1378),(-207,1386),(-236,1380)],156,3,'B_Composed_WestHousehold_Roof','CastleRoof',[156,156,156,162,168,174,168,156])
 # Raised residential room: grounded western corner and north bays, fractured floor plates.
 respoly=[(-214,1598),(-182,1598),(-190,1630),(-174,1640),(-174,1664),(-118,1664),(-118,1688),(-214,1688)]
 drop(['B_RewardChamber_Floor','B_SolidRaisedFoundation_Residential','B_Composed_ResidentialTower_UpperFloor','B_ResidentialClosedSide','B_Composed_ResidentialTower_SWall.001','B_BossWestDoorLintel','B_POST_BOSS_SEALED_DOOR','B_RewardDoorCoping','B_RewardDoorFrame.001','B_RewardEastUpperWall'])
 drop_source('B_Composed_ResidentialTower_RoofTie');drop_source('B_Composed_ResidentialTower_Roof')
 slab('A_ResidentialFracturedFoundation',respoly,117,21.25,'B_SolidRaisedFoundation_Residential');slab('A_ResidentialBrokenFloor',respoly,120,3,'B_RewardChamber_Floor','Paving')
 wall('A_ResidentialSouthCornerReturn','X',1600,[(-214,204),(-193,204),(-188,183),(-180,186),(-174,143)],120,6,'B_ResidentialClosedSide')
 slab('A_ResidentialNorthUpperRoom',[(-214,1664),(-180,1664),(-177,1668),(-143,1668),(-143,1688),(-214,1688)],156,6,'B_Composed_ResidentialTower_UpperFloor')
 roofpoly=[(-218,1596),(-192,1596),(-188,1617),(-199,1622),(-199,1658),(-176,1658),(-176,1668),(-114,1668),(-114,1692),(-218,1692)]
 slab('A_ResidentialRoofCornerRemnant',roofpoly,208,5,'B_Composed_ResidentialTower_Roof')
 wall('A_ResidentialNorthSurvivingCrown','X',1692,[(-218,220),(-169,220),(-164,211),(-143,215),(-114,209)],208,5,'B_Composed_ResidentialTower_Roof_Parapet.001')
 wall('A_ResidentialWestRoofCrown','Y',-218,[(1596,213),(1617,218),(1626,210),(1658,216),(1692,220)],208,5,'B_Composed_ResidentialTower_Roof_Parapet.002')
 # Rear keep retains high exterior walls/roof ridge; central-facing roof/floors fail to supported back bays.
 keeppoly=[(-174,1658),(-153,1658),(-153,1672),(-130,1676),(-130,1710),(-103,1710),(-103,1738),(-18,1738),(-18,1776),(-174,1776)]
 bosspoly=[(-118,1698),(-96,1704),(-94,1727),(-54,1727),(-50,1740),(18,1738),(35,1748),(67,1744),(87,1732),(119,1735),(119,1764),(-118,1764)]
 drop(['B_SolidRaisedFoundation_Keep','B_SolidRaisedFoundation_Boss','B_BossChamber_Floor','B_BossWestPartition.001','B_BossRearEastWall','B_Composed_RearKeep_Roof','B_BossRearConnectingRoof','B_STRUCT_KeepSouthUpperInfill','B_STRUCT_KeepSouthBearing','B_Composed_RearKeep_UpperFloor','B_Composed_RearKeep_WWall','B_KeepSideGalleryFloor','B_KeepRearWallFooting'])
 drop_source('B_Composed_RearKeep_RoofTie')
 slab('A_KeepFracturedFoundation',keeppoly,117,21.25,'B_SolidRaisedFoundation_Keep');slab('A_BossRearFracturedFoundation',bosspoly,117,21.25,'B_SolidRaisedFoundation_Boss');slab('A_BossRearBrokenFloor',bosspoly,120,3,'B_BossChamber_Floor','Paving')
 wall('A_RearBossWestBrokenWall','Y',-118,[(1698,137),(1707,145),(1718,141),(1729,168),(1740,174),(1744,192),(1764,192)],120,6,'B_BossWestPartition.001')
 wall('A_RearBossEastBrokenWall','Y',119,[(1735,143),(1742,152),(1748,147),(1755,183),(1764,192)],120,6,'B_BossRearEastWall')
 wall('A_KeepWestBrokenOuterWall','Y',-174,[(1658,221),(1680,226),(1689,211),(1706,221),(1715,205),(1738,254),(1776,254)],120,6,'B_Composed_RearKeep_WWall')
 slab('A_KeepBrokenGroundFloor',keeppoly,120,3,'B_KeepSideGalleryFloor','Paving')
 wall('A_KeepSouthBrokenUpperReturn','X',1658,[(-174,221),(-164,222),(-159,203),(-151,210),(-145,165)],120,6,'B_STRUCT_KeepSouthUpperInfill')
 slab('A_KeepUpperFloorNorthRemnant',[(-174,1740),(-138,1740),(-128,1747),(-118,1747),(-118,1776),(-174,1776)],164,6,'B_Composed_RearKeep_UpperFloor')
 slab('A_KeepNorthernRoofRemnant',[(-178,1738),(-134,1738),(-130,1745),(-90,1740),(-70,1746),(-14,1742),(-14,1780),(-178,1780)],254,4,'B_Composed_RearKeep_Roof','CastleRoof',[254,277,280,288,277,254,254,254])
 wall('A_KeepNorthBayBearing','X',1740,[(-174,254),(-148,254),(-141,263),(-96,284),(-64,268),(-18,254)],117,6,'B_Composed_RearKeep_NWall')
 slab('A_RearBossRoofWallSeatedRemnant',[(-25,1753),(20,1753),(28,1758),(72,1754),(123,1752),(123,1768),(-25,1768)],191,4,'B_BossRearConnectingRoof','CastleRoof',[197,197,194,191,185,185,197])
 # Kitchen is a more substantial surviving corner. Its torn arch/unsupported roof portion collapses.
 drop_source('B_Composed_KitchenStore_SOpening');drop_source('B_Composed_KitchenStore_RoofTie');drop_source('B_Composed_KitchenStore_Roof')
 drop(['B_Composed_KitchenStore_Floor','B_Composed_KitchenStore_WWall','B_KitchenRafter'])
 kitchen=[(119,1720),(143,1720),(145,1702),(180,1708),(180,1660),(201,1660),(201,1642),(231,1642),(231,1746),(119,1746)]
 slab('A_KitchenBrokenFloor',kitchen,96,3,'B_Composed_KitchenStore_Floor','Paving')
 wall('A_KitchenWestCornerBroken','Y',119,[(1720,105),(1724,116),(1734,122),(1746,132)],96,6,'B_Composed_KitchenStore_WWall')
 slab('A_KitchenEastSupportedRoof',[(209,1640),(235,1640),(235,1750),(211,1750),(211,1726),(216,1718),(208,1691),(214,1684)],134,3,'B_Composed_KitchenStore_Roof','CastleRoof',[133,133,133,133,133,133,133,133])
 # Grounded large fragments sit on outer peripheral land, never in the flat combat floor.
 falls=[('GalleryFloorFall',(217,1520,6),(16,24,5),'B_Composed_EastGallery_Floor','FreshStone'),('GalleryWallFall',(222,1554,5),(13,20,4),'B_Composed_EastGallery_EWall','Fieldstone'),('StairFlightFall',(218,1448,5),(13,23,4),'B_TowerStair','Paving'),('StewardRoofFall',(-202,1509,7),(17,23,6),'B_Composed_StewardBlock_Roof','CastleRoof'),('ResidentialFloorFall',(-184,1571,8),(24,15,7),'B_Composed_ResidentialTower_UpperFloor','FreshStone'),('KeepBeamFall',(-86,1747,5),(34,6,4),'B_Composed_RearKeep_RoofTie','CharredTimber'),('ArchiveStoneFall',(-74,1746,8),(15,17,7),'B_Composed_ArchiveAnnex_Roof','Fieldstone'),('KitchenArchFall',(211,1645,6),(12,15,5),'B_Composed_KitchenStore_SOpening_ArchSector','FreshStone')]
 debris=[]
 for name,(x,y,hh),size,src,mat in falls:
  o=tag(h.box('A_Fallen_'+name,(x,y,(120 if name in ['KeepBeamFall','ArchiveStoneFall'] else 95.75)+size[2]/2),size,COL,mat),src,'Collapsed identifiable architectural bay, resting on peripheral land outside combat floor');debris.append(o.name)
 # Existing isolated ties/upper supports that lost their bearing are removed, not decorated.
 drop(['B_STRUCT_KeepEastBearing','B_STRUCT_KeepEastUpperInfill'])
 bpy.context.view_layer.update()
 assert protected['flat_floor']==m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN']) and protected['route']==m.hashes('A_ROUTE')
 assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['entry'].items())
 assert protected['shared']==c.i.preserve_shared() and protected['exterior']==m.hashes('CASTLE_EXTERIOR_SHARED')
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['B'].items())
 report={'input_checkpoint':'ed0f230','protected':protected,'retired':retired,'new_structural_remnants':[o.name for o in h.COLS[COL].objects],'peripheral_falls':debris,'failure_zones':['East gallery bay entirely collapses','Stair tower upper flight/roof fails; grounded lower corner','Steward wall reduced to stable L-remnant','Household upper north room collapses','Residential west/north corner remains','Keep rear bay retains ridge, front bays collapse','Kitchen eastern corner survives'],'no_B_shared_changes':True,'flat_combat_floor_exact':True,'review':'Structural plausibility assessed by surviving wall corners, bearing connections and grounded debris; not only crater outline'}
 (EV/'impact_failure_report.json').write_text(json.dumps(report,indent=2));cameras();m.use('A');scene.camera=bpy.data.objects['IMPACT_02_oblique']
 bpy.data.texts['START_HERE'].write('\nA STRUCTURAL IMPACT PASS: near-circular shallow basin; gallery/sliver stairs/unsupported ties collapse. Unequal grounded wall corners and surviving northern roof bays, fractured raised floors, eight perimeter falls. B/shared castle and A entry/route/combat floor exact. IMPACT_* views / ImpactStructuralReview. PRE_IMPACT_FAILURE_RETAINED is hidden input recovery. STOP FOR OWNER REVIEW; no production.\n')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'));print('A STRUCTURAL SAVED',len(retired),len(h.COLS[COL].objects),flush=True)

def check():
 report=json.loads((EV/'impact_failure_report.json').read_text());p=report['protected']
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in p['B'].items())
 assert p['exterior']==m.hashes('CASTLE_EXTERIOR_SHARED')
 m.use('A');assert p['shared']==c.i.preserve_shared()
 assert p['flat_floor']==m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN'])
 assert p['route']==m.hashes('A_ROUTE') and all(m.signature(bpy.data.objects[n])==v for n,v in p['entry'].items())
 col=h.COLS[COL];assert all(bpy.data.objects.get(o.get('baseline_source','')) for o in col.objects)
 def distance_segment(a,b):
  d=b-a;den=d.length_squared;t=max(0,min(1,-a.dot(d)/den)) if den else 0
  return (a+d*t).length
 def closest_triangle(pts):
  a,b,c=pts;cross=lambda u,v:u.x*v.y-u.y*v.x
  if abs(cross(b-a,c-a))>1e-8:
   signs=[cross(b-a,-a),cross(c-b,-b),cross(a-c,-c)]
   if min(signs)>=0 or max(signs)<=0:return 0
  return min(distance_segment(a,b),distance_segment(b,c),distance_segment(c,a))
 clearance={}
 for o in col.objects:
  assert all(all(math.isfinite(x) for x in v.co) for v in o.data.vertices) and o.data.polygons
  o.data.calc_loop_triangles();nearest=10000
  for tri in o.data.loop_triangles:
   pts=[]
   for j in tri.vertices:
    w=o.matrix_world@o.data.vertices[j].co;pts.append(Vector(((w.x-20)/150,(w.y-1545)/160)))
   nearest=min(nearest,closest_triangle(pts))
  clearance[o.name]=round(nearest,4)
 assert min(clearance.values())>=.999,'New architecture/rubble intrudes into central combat-floor footprint: '+str({k:v for k,v in clearance.items() if v<.999})
 def contact(a,b):
  aa=s.bounds(bpy.data.objects[a]);bb=s.bounds(bpy.data.objects[b]);return all(aa[0][j]<=bb[1][j]+.05 and bb[0][j]<=aa[1][j]+.05 for j in range(3))
 pairs=[('A_ResidentialNorthUpperRoom','A_From_B_Composed_ResidentialTower_NWall'),('A_ResidentialRoofCornerRemnant','A_From_B_Composed_ResidentialTower_WWall'),('A_KeepNorthernRoofRemnant','A_KeepNorthBayBearing'),('A_KeepUpperFloorNorthRemnant','A_From_B_Composed_RearKeep_NWall'),('A_KeepWestBrokenOuterWall','A_KeepBrokenGroundFloor'),('A_KeepBrokenGroundFloor','A_KeepFracturedFoundation'),('A_KitchenEastSupportedRoof','A_From_B_Composed_KitchenStore_EWall'),('A_StairInterruptedLanding','A_StairCornerFooting')]
 contacts={a+' / '+b:contact(a,b) for a,b in pairs};assert all(contacts.values()),contacts
 checks={'B_all_protected_exact':True,'shared_exterior_exact':True,'shared887_exact':True,'A_entry_route_exact':True,'flat_combat_floor_exact':True,'all52_remnants_have_B_sources':True,'finite_nonempty_new_geometry':True,'new_remnants_and_falls_outside_flat_combat_floor':True,'normalized_floor_clearance':clearance,'targeted_bearing_contacts':contacts,'visual_assessment_required':'Corners/roof seating/local bay collapse reviewed in five matched views; no physics or engineering simulation'}
 (EV/'impact_failure_checks.json').write_text(json.dumps(checks,indent=2));print('IMPACT CHECK PASS',len(col.objects),'minimum floor clearance',min(clearance.values()),flush=True)

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),None)
 if '--check' in args:check()
 elif '--before' in args:render('before',selected)
 elif '--after' in args:render('after',selected)
 else:apply()
