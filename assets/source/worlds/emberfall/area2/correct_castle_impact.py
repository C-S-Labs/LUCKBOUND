"""Castle-only impact correction: B enclosed baseline; A its destroyed interior.
Load the pre-correction review blend using tools/run_blender.py. Blockout only.
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
EV=OUT/'ImpactCorrectionReview';EV.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('castle_helpers',ROOT/'revise_castle_variants.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
h=r.h
B_ROUTE=[(0,1005,56),(0,1130,83),(0,1214,96),(0,1255,96),(0,1310,96),(110,1310,96),(160,1310,96),(160,1386,96),(105,1395,96),(72,1420,96),(72,1480,132),(72,1525,132),(0,1550,132),(0,1625,132)]
VIEWS=[
 ('01_A_exterior','A',(-660,985,300),(0,1480,150),'ORTHO',820,''),
 ('02_B_exterior','B',(-660,985,300),(0,1480,150),'ORTHO',820,''),
 ('03_A_missing_palace','A',(-420,1230,465),(0,1505,137),'ORTHO',700,''),
 ('04_B_roofed_palace','B',(-420,1230,465),(0,1505,137),'ORTHO',700,''),
 ('05_A_surviving_entrance','A',(12,1240,102),(-86,1255,108),'PERSP',23,''),
 ('06_A_impact_reveal','A',(-92,1420,104),(5,1550,100),'PERSP',22,''),
 ('07_A_sheared_floors','A',(-310,1510,245),(0,1530,118),'PERSP',24,''),
 ('08_A_impact_to_earth','A',(-380,1310,370),(0,1550,69),'ORTHO',620,'roofless'),
 ('09_B_enclosed_lower_hall','B',(0,1374,103),(30,1470,117),'PERSP',23,''),
 ('10_B_gallery_final_arena','B',(0,1542,138),(0,1630,153),'PERSP',23,''),
 ('11A_palace_section','A',(-420,1230,465),(0,1505,137),'ORTHO',700,'roofless'),
 ('11B_palace_section','B',(-420,1230,465),(0,1505,137),'ORTHO',700,'roofless'),
]


def floor_fragment(name,polygon,z,col,thick=5):
 n=len(polygon);v=[(x,y,z) for x,y in polygon]+[(x,y,z-thick) for x,y in polygon]
 f=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return h.mesh(name,v,f,col,'FreshStone')


def preserve_shared():
 names=['AREA_II_SHARED','INNER_WALL_SHARED','CASTLE_GROUNDS_SHARED']
 objects={o.name:r.geometry_hash(o) for name in names for o in h.COLS[name].all_objects}
 return objects


def baseline_b():
 # Archive only the old B interior, preserving B-specific exterior alternatives.
 archive=r.new_collection('PRE_IMPACT_B_INTERIOR_RETAINED')
 archive.hide_render=True;archive.hide_viewport=True
 for colname in ['CASTLE_B_STRONGHOLD','B_SurvivingRoofs','B_ROUTE']:
  for o in list(h.COLS[colname].objects):
   if o.name.startswith(('CastleFrontCurtain','CastleCornerTower','CastleGatehouseRoof')):continue
   h.COLS[colname].objects.unlink(o);archive.objects.link(o)
 c='B_BASELINE_ENCLOSED_PALACE';r.new_collection(c,'CASTLE_B_STRONGHOLD')
 roof='B_BASELINE_ROOFS';r.new_collection(roof,'CASTLE_B_STRONGHOLD')
 r.slab('B_BaselineGround',0,1490,95.75,500,580,c,'Paving',14)
 r.room('B_BaselineEntry',0,1255,96,110,82,38,c,roof,{'S':(0,38),'N':(0,44)})
 r.slab('B_SmallArrivalCourt',25,1320,96.1,145,46,c)
 r.room('B_BaselineEastGuard',160,1330,96,100,112,44,c,roof,{'W':(-20,38),'N':(0,38)},True)
 r.slab('B_GuardLinkFloor',132,1394,96,62,28,c)
 h.box('B_GuardLinkLintel',(132,1394,131),(62,28,5),c,'Fieldstone')
 for yy in [1380,1408]:h.box('B_GuardLinkSide',(132,yy,111),(62,5,30),c,'Fieldstone')
 # Central enclosed structure covers the future impact footprint with two levels.
 r.room('B_CentralPalaceHall',0,1435,96,210,190,70,c,roof,{'S':(0,48),'E':(-40,38),'N':(0,44),'W':(40,36)})
 r.slab('B_CentralUpperFloor_West',-35,1435,132,140,190,c,'Paving',6)
 r.slab('B_CentralUpperFloor_EastEdge',100,1435,132,10,190,c,'Paving',6)
 r.slab('B_CentralUpperFloor_South',65,1377,132,60,74,c,'Paving',6)
 r.slab('B_CentralUpperFloor_North',65,1512,132,60,36,c,'Paving',6)
 for i in range(30):h.box('B_CentralStair',(72,1421+i*2,96+(i+1)*1.2-.6),(40,2.1,1.2),c,'FreshStone')
 r.slab('B_StairHeadLanding',72,1489,132,45,22,c,'Paving',6)
 for xx in [-84,84]:
  for yy in [1370,1430,1490]:
   h.box('B_CentralLoadBearingColumn',(xx,yy,130),(10,12,68),c,'FreshStone')
   h.box('B_CentralColumnCap',(xx,yy,164),(16,18,5),c,'Fieldstone')
 for sx in [-1,1]:
  x=sx*176
  r.room('B_PalaceSideWing',x,1515,96,96,350,74,c,roof,{'S':(0,34),'E' if sx<0 else 'W':(-40,36)})
  r.slab('B_SideWingUpperFloor',x,1515,132,96,350,c,'Paving',6)
  for yy in [1430,1530,1630]:
   h.arch('B_SideRoomPartition',x,yy,96,30,28,5,c)
   h.box('B_UpperSideRoomPartition',(x,yy,149),(96,5,34),c,'Fieldstone')
  for yy in [1400,1470,1540,1610,1680]:
   h.beam('B_SideWingRoofTie',(x-43,yy,168),(x+43,yy,168),3,roof,'Timber')
 r.room('B_BaselineUpperGallery',0,1550,132,250,40,42,c,roof,{'S':(0,44),'N':(0,44),'E':(0,32),'W':(0,32)})
 r.room('B_BaselineFinalArena',0,1625,132,180,110,64,c,roof,{'S':(0,44)})
 for yy in [1590,1625,1660]:
  for sx in [-1,1]:h.box('B_FinalArenaSupport',(sx*78,yy,160),(10,10,56),c,'FreshStone')
  for i in range(8):
   a=-74+i*18.5;b=a+18.5
   h.beam('B_FinalArenaShallowArch',(a,yy,182+14*(1-(a/74)**2)),(b,yy,182+14*(1-(b/74)**2)),4,c,'FreshStone')
 r.slab('B_FinalArenaDais',0,1645,135,68,36,c,'Fieldstone')
 # Roof structure is coarse and structural, not roof tiles or final ornament.
 for yy in [1370,1420,1470,1510]:
  h.beam('B_CentralRoofTie',(-100,yy,164),(100,yy,164),3,roof,'Timber')
  for sx in [-1,1]:h.beam('B_CentralRoofRafter',(sx*105,yy,166),(0,yy,216),3,roof,'Timber')
 for name,loc,e in [('B_LowerHallFill',(0,1410,115),300000),('B_UpperHallFill',(0,1460,150),280000),('B_GuardFillNew',(160,1330,120),180000),('B_GalleryFillNew',(0,1550,155),220000),('B_ArenaFillNew',(0,1600,167),300000),('B_ArenaRearFillNew',(0,1650,170),260000)]:r.point_light(name,loc,c,e)
 r.debris('B_RecentGuardRoofFall',202,1310,97,15,c,12)
 r.small_fire('B_ActiveGuardFire',198,1340,140,c,7)
 r.small_fire('B_ActiveWingFire',-210,1620,173,c,8)
 r.path('B_CorrectedPlanRoute',B_ROUTE,4,'B_ROUTE','RouteCyan')


def remnants_a():
 c='A_IMPACT_ARCHITECTURE_REMNANTS';r.new_collection(c,'CASTLE_A_CATASTROPHE')
 roof='A_IMPACT_ROOF_REMNANTS';r.new_collection(roof,'CASTLE_A_CATASTROPHE')
 # Surviving southern upper hall cross-section corresponds to B central hall.
 floor_fragment('A_CentralUpperFloor_ShearedSouth',[(-105,1340),(105,1340),(105,1372),(48,1381),(20,1370),(-27,1380),(-105,1368)],132,c,6)
 for x in [-105,105]:
  h.box('A_CentralHallSouthWallStub',(x,1355,129),(6,30,66),c,'Fieldstone')
 h.box('A_CentralHallUpperSouthWall',(0,1340,149),(210,6,34),c,'Fieldstone')
 h.roof('A_CentralRoofSouthRemnant',0,1351,166,218,30,50,roof,'CastleRoof')
 for sx in [-1,1]:
  # Wall-attached lower rooms and sheared upper floors, rather than bare crater rim.
  for j,(yy,depth,inner) in enumerate([(1408,72,150),(1515,84,159),(1642,80,144)]):
   xouter=sx*224;xinner=sx*inner
   poly=[(xouter,yy-depth/2),(xinner,yy-depth/2+4),(sx*(inner-9),yy-10),(xinner,yy+depth/2-8),(xouter,yy+depth/2)]
   floor_fragment('A_SideRoomLowerFloor',poly,96,c,6)
   poly2=[(xouter,yy-depth/2),(sx*(inner+9),yy-depth/2),(xinner,yy-8),(sx*(inner+15),yy+depth/2),(xouter,yy+depth/2)]
   floor_fragment('A_SideRoomUpperFloor_CrossSection',poly2,132,c,6)
   h.box('A_SideWingOuterWall',(sx*222,yy,133),(6,depth,74),c,'Fieldstone')
   for end in [-1,1]:
    # Jagged inner end heights make walls visibly sheared, not completed rooms.
    verts=[(sx*222,yy+end*depth/2,96),(sx*inner,yy+end*depth/2,96),(sx*(inner-7),yy+end*depth/2,128),(sx*(inner+18),yy+end*depth/2,143),(sx*222,yy+end*depth/2,170)]
    verts+= [(x,y+5,z) for x,y,z in verts]
    faces=[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
    h.mesh('A_ShearedSideRoomPartition',verts,faces,c,'FreshStone')
   h.box('A_SurvivingSideSupport',(sx*(inner+10),yy,125),(11,12,58),c,'Fieldstone')
   h.box('A_BrokenUpperSupport',(sx*213,yy,161),(10,12,58),c,'FreshStone')
   # Roof strips remain along walls while central roof is gone.
   h.roof('A_AttachedWingRoofStrip',sx*211,yy,170,32,depth,14,roof,'CastleRoof',True)
   h.beam('A_SnappedWingRafter',(sx*224,yy,170),(sx*(inner+8),yy,184),3,roof,'CharredTimber')
  # Gallery cantilevers ending over space, with floor cores and diagonal support.
  poly=[(sx*220,1542),(sx*134,1542),(sx*121,1552),(sx*146,1571),(sx*220,1571)]
  floor_fragment('A_UpperGallery_EndsInVoid',poly,132,c,7)
  h.beam('A_SeveredGalleryBrace',(sx*216,1558,98),(sx*148,1558,128),4,c,'CharredTimber')
  # B stair circulation has a counterpart ending at a vanished upper level.
  for i in range(18):h.box('A_WingStair_RemainingSteps',(sx*202,1450+i*2,97+i*2),(28,2.1,2),c,'FreshStone')
  for i in range(11):h.box('A_UpperStair_EndsInVoid',(sx*(201-i*4),1604,133+i*2),(4.1,27,2),c,'FreshStone')
  h.beam('A_BrokenStairStringer',(sx*205,1604,128),(sx*153,1604,155),5,c,'Fieldstone')
 # Surviving high supports mark the scale of the former central roof/arena.
 for x,y,top in [(-134,1630,181),(134,1630,192),(-150,1468,163),(151,1480,174)]:
  h.box('A_ShearedCentralLoadBearingSupport',(x,y,(80+top)/2),(12,14,top-80),c,'FreshStone')
  h.box('A_RecognizableSupportCapital',(x,y,top),(18,20,5),c,'Fieldstone')
 # Inward-fallen roof structure plunges from surviving perimeter toward cavity.
 for sx,yy in [(-1,1510),(1,1590),(-1,1660)]:
  h.beam('A_InwardFallenMainRafter',(sx*182,yy,169),(sx*88,1545+(yy-1545)*.42,74),5,c,'CharredTimber')
  h.beam('A_RafterBrokenCrossTie',(sx*143,yy-10,122),(sx*98,yy+15,78),4,c,'Timber')
  r.debris('A_InwardMasonryAndRoofFall',sx*107,1545+(yy-1545)*.7,68,18,c,13)
 # A solid roof/floor must never cover the crater center. Small angular fragments only.
 for x,y,z in [(-54,1490,55),(68,1575,53),(-78,1600,57)]:
  o=h.box('A_FallenUpperFloorFragment',(x,y,z),(28,17,5),c,'FreshStone',.3);o.rotation_euler[0]=.3
 r.point_light('A_RemnantSectionFill',(-140,1520,165),c,150000)
 r.point_light('A_RevealArchitectureFill',(75,1590,150),c,180000)


def cameras():
 col=r.new_collection('IMPACT_REVIEW_CAMERAS')
 for name,variant,loc,target,kind,value,mode in VIEWS:
  name='IMPACT_'+name;d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
  d.type=kind;d.clip_end=6000;d.clip_start=.1
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value;d.sensor_width=36


def build():
 assert 'A_IMPACT_ARCHITECTURE_REMNANTS' not in bpy.data.collections,'Already corrected; use protected pre-correction input for explicit rebuild'
 before=preserve_shared()
 entrance={o.name:r.geometry_hash(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}
 baseline_b();remnants_a();cameras()
 assert before==preserve_shared(),'Shared town or boundaries changed'
 scene=bpy.context.scene
 scene['CastleConcept']='B enclosed two-level palace baseline; A roof/interior annihilated by downward impact into earth'
 scene['Timing']='20min TOTAL gameplay; no walking quotas; combat timing unproven'
 t=bpy.data.texts['START_HERE'];t.write('\nIMPACT CORRECTION: B is enclosed multi-level palace baseline. A retains its exterior and short entry sequence; most corresponding floors/roof/rooms are gone. Attached room/floor/stair remnants + inward roof fall show the impact. No crater in B. IMPACT_* review cameras. Previous revision preserved in BeforeImpactCorrection.\n')
 bpy.context.window.view_layer=scene.view_layers['VARIANT_A_CATASTROPHE']
 scene.camera=bpy.data.objects['IMPACT_03_A_missing_palace']
 report={'base_checkpoint':'caa7ca3','blend':str(OUT/'EmberfallAreaII.blend'),'shared_geometry_exact':True,'shared_object_hashes':before,'shared_object_count':len(before),'preserved_A_entrance_hashes':entrance,'castle_exterior_footprint_studs':[500,580],'castle_silhouette_peak_z':288,'A_route_studs':r.length(r.A_ROUTE),'B_route_studs':r.length(B_ROUTE),'B_route':B_ROUTE,'B_enclosed_levels_z':[96,132],'B_main_roof_peak_z':216,'B_final_arena_clear_studs':[156,86],'both_selected_bosses_final':True,'B_no_crater':True,'A_downward_impact_into_preexisting_palace':True,'views':[v[0] for v in VIEWS],'scope':'castle-only blockout; no production/collision/sockets/upload/Studio','preserved_previous':str(OUT/'BeforeImpactCorrection')}
 (EV/'impact_report.json').write_text(json.dumps(report,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 print('IMPACT CORRECTION SAVED',json.dumps({k:report[k] for k in ['shared_object_count','shared_geometry_exact','A_route_studs','B_route_studs']}),flush=True)


def render():
 scene=bpy.context.scene;scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.cycles.samples=24
 roofnames=['A_SurvivingRoofs','B_SurvivingRoofs','A_IMPACT_ROOF_REMNANTS','B_BASELINE_ROOFS']
 for name,variant,loc,target,kind,value,mode in VIEWS:
  layer='VARIANT_A_CATASTROPHE' if variant=='A' else 'VARIANT_B_STRONGHOLD'
  bpy.context.window.view_layer=scene.view_layers[layer]
  for n in roofnames:bpy.data.collections[n].hide_render=mode=='roofless'
  for n in ['Route','A_ROUTE','B_ROUTE']:bpy.data.collections[n].hide_render=True
  scene.camera=bpy.data.objects['IMPACT_'+name];scene.render.filepath=str(EV/(name+'.png'))
  bpy.ops.render.render(write_still=True,layer=layer);print('IMPACT VIEW',name,flush=True)
 # Never save render-only visibility changes.


if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--lower-subfloor' in args:
  bpy.data.objects['B_BaselineGround'].location.z=88.75
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'))
 selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),None)
 if selected:VIEWS=[v for v in VIEWS if v[0] in selected]
 if '--render-only' not in args:build()
 if '--build-only' not in args:render()
