"""Focused saved-scene B interior revision; matching A edits only. Blockout, no chunks."""
import bpy, importlib.util, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII')
EV=OUT/'InteriorLayoutReview';EV.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('composition',ROOT/'recompose_castle.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
r=c.r;h=c.h;scene=bpy.context.scene
BC=c.BC;BR=c.BR;AC=c.AC;AR=c.AR
ROUTE=c.B_ROUTE[:7]+[(155,1395,96)]+c.B_ROUTE[7:-1]+[(25,1542,120),(25,1630,120)]
REWARD=[(25,1630,120),(-90,1644,120),(-165,1644,120)]
VIEWS=[
 ('01_B_floorplan','B',(0,1490,1000),(0,1490,120),'ORTHO',790,'plan'),
 ('02_B_primary_entrance','B',(20,1310,102),(20,1385,114),'PERSP',24,''),
 ('03_B_progression','B',(160,1535,126),(60,1542,133),'PERSP',23,''),
 ('04_B_boss_room','B',(91,1538,126),(-40,1680,140),'PERSP',20,''),
 ('05_B_sealed_loot_connection','B',(-64,1623,126),(-143,1644,135),'PERSP',25,''),
 ('06_B_foundation_after','B',(10,1480,104),(10,1580,110),'PERSP',24,''),
 ('07_B_matched_section','B',(-470,1270,450),(0,1515,140),'ORTHO',710,'section'),
 ('08_A_matched_section','A',(-470,1270,450),(0,1515,140),'ORTHO',710,'section'),
 ('00_B_foundation_before','B',(10,1480,104),(10,1580,110),'PERSP',24,''),
]

def use(v):
 bpy.context.window.view_layer=scene.view_layers['VARIANT_'+('B_STRONGHOLD' if v=='B' else 'A_CATASTROPHE')]
 bpy.context.view_layer.update()

def signature(o):
 sha=hashlib.sha256();sha.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
 if o.type=='MESH':
  sha.update(str([tuple(v.co) for v in o.data.vertices]).encode());sha.update(str([tuple(p.vertices) for p in o.data.polygons]).encode());sha.update(str([p.material_index for p in o.data.polygons]).encode());sha.update(str([m.name if m else None for m in o.data.materials]).encode())
 return sha.hexdigest()

def hashes(col):return {o.name:signature(o) for o in h.COLS[col].all_objects}

def cameras():
 col=r.new_collection('INTERIOR_REVIEW_CAMERAS')
 for name,v,loc,target,kind,value,mode in VIEWS:
  if 'INTERIOR_'+name in bpy.data.objects:o=bpy.data.objects['INTERIOR_'+name];d=o.data
  else:
   d=bpy.data.cameras.new('INTERIOR_'+name);o=bpy.data.objects.new('INTERIOR_'+name,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_start=.1;d.clip_end=6000
  if mode=='plan':o.rotation_euler=(0,0,math.pi/2)
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value;d.sensor_width=36

def render(selected):
 cameras();scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.cycles.samples=20
 for name,v,loc,target,kind,value,mode in VIEWS:
  if name not in selected:continue
  use(v)
  for col in [BR,AR]:h.COLS[col].hide_render=mode in ['plan','section']
  for route in ['Route','A_ROUTE','B_ROUTE']:h.COLS[route].hide_render=True
  # Reveal the intended ground floor in review sections, not an X-ray of inaccessible upper slabs.
  hidden=[]
  if mode in ['plan','section']:
   for o in h.COLS[BC if v=='B' else AC].objects:
    if 'UpperFloor' in o.name or 'RoofTie' in o.name or o.name=='B_CrossTowerLinkRoof':
     hidden.append((o,o.hide_render));o.hide_render=True
  scene.camera=bpy.data.objects['INTERIOR_'+name];scene.render.filepath=str(EV/(name+'.png'))
  bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)
  for o,val in hidden:o.hide_render=val
  print('INTERIOR VIEW',name,flush=True)
 for col in [BR,AR]:h.COLS[col].hide_render=False

def revise():
 assert 'B_BossChamber_Floor' not in bpy.data.objects,'Interior already revised; use saved scene for rendering'
 use('A');protected={'shared':c.i.preserve_shared(),'basin':hashes(c.AG),'entrance':{o.name:signature(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}}
 use('B');protected['exterior']=hashes('CASTLE_EXTERIOR_SHARED')
 old={o.name:signature(o) for col in [BC,BR] for o in h.COLS[col].objects}
 rec=r.new_collection('PRE_INTERIOR_LAYOUT_RETAINED');rec.hide_render=True;rec.hide_viewport=True
 touched=set()
 def retire(o):
  touched.add(o.name)
  for col in list(o.users_collection):col.objects.unlink(o)
  rec.objects.link(o);o.name='RECOVERED_'+o.name
 def remove_prefix(*prefixes):
  for col in [BC,BR]:
   for o in list(h.COLS[col].objects):
    if o.name.startswith(prefixes):retire(o)
 # One dominant court-facing interior portal; plain sealed fronts replace repeated arches.
 remove_prefix('B_Composed_StewardBlock_SOpening','B_Composed_WestHousehold_SOpening','B_Composed_TransverseHall_SOpening','B_Composed_TransverseHall_SWall','B_Composed_StairTower_NOpening')
 h.box('B_StewardClosedFront',(-74,1410,135),(40,4,78),BC,'Fieldstone')
 h.box('B_HouseholdClosedFront',(-183,1339,126),(34,4,60),BC,'Fieldstone')
 for x,w in [(-31,50),(85,78)]:h.box('B_PrimaryHallFront',(x,1353,118),(w,4,44),BC,'Fieldstone')
 h.box('B_StairUpperExitLintel',(155,1508,169),(38,5,30),BC,'FreshStone')
 h.box('B_StairExitSolidSupport',(155,1508,108),(38,4,24),BC,'Fieldstone')
 h.arch('B_PRIMARY_INTERIOR_PORTAL',20,1353,96,52,39,7,BC)
 for o in list(h.COLS[BC].objects):
  if (o.name.startswith('B_Composed_EastGallery_Pier') and abs(o.location.x-125)<1 and abs(o.location.y-1542)<1) or (o.name.startswith('B_Composed_ResidentialTower_Pier') and abs(o.location.x+121)<1 and abs(o.location.y-1644)<1):retire(o)
 # Boss room amalgamates the audience / archive / lower keep volume, not a detached addition.
 remove_prefix('B_Composed_RearKeep_Floor','B_KeepRaisedFoundation','B_Composed_AudienceHall_Floor','B_Composed_ResidentialTower_Floor','B_Composed_AudienceHall_NWall','B_Composed_AudienceHall_NOpening','B_Composed_AudienceHall_WWall','B_Composed_AudienceHall_WLintel','B_Composed_AudienceHall_Pier','B_AudiencePerimeterSupport','B_AudienceFinalBossDais',
 'B_Composed_ArchiveAnnex_NWall','B_Composed_ArchiveAnnex_SWall','B_Composed_ArchiveAnnex_EWall','B_Composed_ArchiveAnnex_WWall','B_Composed_ArchiveAnnex_SOpening','B_Composed_ArchiveAnnex_WLintel','B_Composed_ArchiveAnnex_Pier','B_Composed_ArchiveAnnex_Floor',
 'B_Composed_RearKeep_EWall','B_Composed_RearKeep_SWall','B_Composed_RearKeep_SOpening','B_Composed_ResidentialTower_EWall','B_Composed_ResidentialTower_ELintel','B_Composed_ResidentialTower_SOpening')
 # Existing rear keep upper floor was spanning the intended boss space; retain its narrow side gallery only.
 for o in list(h.COLS[BC].objects):
  if o.name.startswith('B_Composed_RearKeep_Pier') and o.location.x>-118:retire(o);continue
  if o.name.startswith(('B_Composed_RearKeep_UpperFloor',)):
   c.cut_box(o,(20,1665,175),(276,310,140));touched.add(o.name)
 for o in list(h.COLS[BC].objects):
  if o.name.startswith(('B_Composed_RearKeep_WWall','B_Composed_RearKeep_UpperFloor')):
   c.cut_box(o,(-174,1673,142),(116,30,44));touched.add(o.name)
 r.slab('B_KeepSideGalleryFloor',-146,1732,120,56,88,BC,'Paving',3)
 r.slab('B_BossChamber_Floor',4.5,1640,120,245,248,BC,'Paving',5)
 # At west face, one sealed connection to the existing residential tower (post-boss chamber).
 for y,d in [(1572,112),(1712,104)]:h.box('B_BossWestPartition',(-118,y,156),(4,d,72),BC,'Fieldstone')
 h.box('B_BossWestDoorLintel',(-118,1644,171),(6,32,42),BC,'FreshStone')
 h.box('B_POST_BOSS_SEALED_DOOR',(-118,1644,135),(5,28,30),BC,'CharredTimber')
 for yy in [1628,1660]:h.box('B_RewardDoorFrame',(-118,yy,137),(8,5,34),BC,'FreshStone')
 h.box('B_RewardDoorCoping',(-118,1644,154),(8,37,5),BC,'FreshStone')
 h.box('B_ResidentialClosedSide',(-166,1600,162),(34,4,84),BC,'Fieldstone')
 # Complete west tower partition; original side walls flank this doorway.
 h.box('B_RewardEastUpperWall',(-118,1644,198),(4,88,12),BC,'Fieldstone')
 h.box('B_BossFrontWestWall',(-97.5,1516,156),(41,4,72),BC,'Fieldstone')
 h.box('B_BossRearWall',(.5,1764,156),(237,4,72),BC,'Fieldstone')
 h.box('B_BossRearEastWall',(119,1709,156),(4,110,72),BC,'Fieldstone')
 # Low joining roof volumes fill existing breaks between varied rear masses, retaining the keep/roof hierarchy.
 p={'x':51,'y':1709,'w':136,'d':110,'z':120,'h':62,'rise':12,'roof':'shed'}
 c.roof('B_BossRearConnectingRoof',p,BR)
 r.slab('B_BossWestRoofLink',-98,1574,190,40,116,BR,'CastleRoof',5)
 # Fill unplanned open sub-floor cavities with load-bearing plinths. No new underground route.
 for name,x,y,w,d in [('Boss',.5,1640,237,248),('Gallery',160,1542,76,112),('Residential',-166,1644,96,88),('ServiceCourt',186,1619,94,40),('Keep',-96,1717,156,118)]:
  r.slab('B_SolidRaisedFoundation_'+name,x,y,117,w,d,BC,'Fieldstone',21.25)
 r.slab('B_KeepRearWallFooting',-68,1770,120,100,12,BC,'Fieldstone',3)
 # The old floor is now covered by the continuous same-height floor; no central dais or combat columns.
 r.slab('B_RewardChamber_Floor',-166,1644,120,96,88,BC,'Paving',3)
 for name,loc,energy in [('BossFront',(25,1570,154),360000),('BossRear',(-25,1710,154),360000),('Reward',(-168,1644,151),180000),('Primary',(20,1368,125),160000)]:r.point_light('B_InteriorFill_'+name,loc,BC,energy)
 for o in list(h.COLS['B_ROUTE'].objects):retire(o)
 r.path('B_PrimaryRoute',ROUTE,4,'B_ROUTE','RouteCyan')
 # Record all actual B changes, then replace only corresponding A sources through the existing impact cut.
 bpy.context.view_layer.update()
 current={o.name:o for col in [BC,BR] for o in h.COLS[col].objects}
 touched.update(n for n,o in current.items() if n not in old or signature(o)!=old[n])
 for n in touched:
  if n in current:current[n]['interior_revision']='Focused boss/reward/circulation';current[n]['derive_from_baseline']=True
 use('A')
 for col in [AC,AR]:
  for o in list(h.COLS[col].objects):
   if o.get('baseline_source') in touched:retire(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=1,depth=500,location=(20,1545,240))
 cutter=bpy.context.object;cutter.scale=(175,185,1)
 added=0;removed=0
 for n in sorted(touched):
  src=current.get(n)
  if src is None or src.type!='MESH' or not src.get('derive_from_baseline',True):continue
  target=AR if src.name in h.COLS[BR].objects else AC
  o=src.copy();o.data=src.data.copy();h.COLS[target].objects.link(o);o.name='A_From_'+src.name;o['baseline_source']=src.name
  c.bool_difference(o,cutter)
  if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True);removed+=1
  else:added+=1
 bpy.data.objects.remove(cutter,do_unlink=True)
 bpy.context.view_layer.update()
 assert protected['shared']==c.i.preserve_shared()
 assert protected['basin']==hashes(c.AG)
 assert all(signature(bpy.data.objects[n])==v for n,v in protected['entrance'].items())
 use('B');assert protected['exterior']==hashes('CASTLE_EXTERIOR_SHARED')
 report={'checkpoint_input':'80a893b','protected_hashes':protected,'changed_B_sources':sorted(touched),'A_replaced_survivors':added,'A_changed_sources_fully_removed':removed,'boss_bounds_studs':[-118,119,1516,1764],'boss_floor_z':120,'clear_combat_rectangle_studs':[213,224],'reward_bounds_studs':[-214,-118,1600,1688],'sealed_door':[ -118,1644,120],'primary_portal':[20,1353,96],'primary_route':ROUTE,'reward_route_after_boss_only':REWARD,'route_studs':r.length(ROUTE),'basement_finding':'Unplanned21.25stud open cavity below Z120 raised floors; solid plinth infill, no basement route','chunk_constraint':'Entire castle is one special logical finale chunk; no256x256 or old arena footprint cap; continuous study remains undivided','no_mechanics_or_production':True,'views':[v[0] for v in VIEWS]}
 (EV/'interior_layout_report.json').write_text(json.dumps(report,indent=2))
 scene['CastleFinaleChunk']='Whole castle: entrance, interiors, final encounter, post-boss reward. Logical special unit, no standard footprint cap. Blockout undivided.'
 scene['InteriorLayout']='B primary hall -> stairs/gallery -> broad rear boss chamber -> sealed adjoining residential reward chamber. No basement route.'
 cameras();scene.camera=bpy.data.objects['INTERIOR_07_B_matched_section']
 bpy.data.texts['START_HERE'].write('\nINTERIOR REVISION: B single primary court entrance, rear audience/archive/lower-keep combat chamber, adjoining sealed residential loot chamber. Solid raised foundations eliminate unintended basement. INTERIOR_* cameras and InteriorLayoutReview evidence. Entire castle intended as one special logical finale chunk; no chunk separation yet. A corresponding changes derived only; shallow basin/entrance and shared town/walls unchanged.\n')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 print('INTERIOR SAVED',report['route_studs'],added,removed,flush=True)

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--before' in args:render(['00_B_foundation_before'])
 elif '--refresh-cameras' in args:
  cameras();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 elif '--render-only' in args:
  selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),[v[0] for v in VIEWS if not v[0].startswith('00')]);render(selected)
 else:revise()












