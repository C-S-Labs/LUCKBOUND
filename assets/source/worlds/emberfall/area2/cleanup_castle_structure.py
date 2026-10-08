"""Final bounded structural cleanup of the provisionally accepted castle blockout."""
import bpy,importlib.util,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_AreaII');EV=OUT/'StructuralCleanupReview';EV.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('interior_helpers',ROOT/'revise_castle_interiors.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
h=m.h;r=m.r;c=m.c;scene=bpy.context.scene
BS='B_STRUCTURAL_SUPPORTS';AS='A_DERIVED_STRUCTURAL_SUPPORTS'
VIEWS=[('roof_supports',(-365,1545,255),(-65,1692,211),'ORTHO',390),('entrance_gaps',(-45,1310,133),(20,1353,129),'PERSP',25),('burned_beams',(-160,1465,230),(-182,1404,147),'ORTHO',180),('perimeter_damage',(470,1700,310),(220,1692,170),'ORTHO',470)]

def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]

def cameras():
 col=r.new_collection('STRUCTURAL_REVIEW_CAMERAS')
 for name,loc,target,kind,value in VIEWS:
  if 'STRUCT_'+name in bpy.data.objects:o=bpy.data.objects['STRUCT_'+name];d=o.data
  else:d=bpy.data.cameras.new('STRUCT_'+name);o=bpy.data.objects.new('STRUCT_'+name,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_start=.1;d.clip_end=6000
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value

def render(stage,selected=None):
 cameras();scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.cycles.samples=20
 for name,loc,target,kind,value in VIEWS:
  if selected and name not in selected:continue
  m.use('B');scene.camera=bpy.data.objects['STRUCT_'+name];scene.render.filepath=str(EV/(name+'_'+stage+'.png'));bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name);print('STRUCT VIEW',name,stage,flush=True)
 if stage=='after' and (not selected or 'roof_supports' in selected):
  m.use('A');scene.camera=bpy.data.objects['STRUCT_roof_supports'];scene.render.filepath=str(EV/'A_derived_supports_after.png');bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)

def arch_infill(name,x,y,z,width,arch_height,wall_height,col,depth=4):
 # Clip the spandrel to the original doorway span, avoiding coplanar side-wall faces.
 rr=width/2+5;spring=arch_height-width/2;n=12;bottom=[]
 for k in range(n+1):
  xx=-width/2+width*k/n;bottom.append((x+xx,z+spring+math.sqrt(max(0,rr*rr-xx*xx))))
 top=z+max(wall_height,arch_height+5);v=[]
 for yy in [y-depth/2,y+depth/2]:
  v.extend([(a,yy,b) for a,b in bottom]);v.extend([(a,yy,top) for a,b in bottom])
 q=n+1;f=[]
 for k in range(n):f.extend([(k,k+1,k+1+q,k+q),(k+2*q,k+3*q,k+1+3*q,k+1+2*q),(k,k+2*q,k+1+2*q,k+1),(k+q,k+1+q,k+1+3*q,k+3*q)])
 f.extend([(0,q,3*q,2*q),(n,n+2*q,n+3*q,n+q)])
 return h.mesh(name,v,f,col,'Fieldstone')

def cleanup():
 assert BS not in bpy.data.collections,'Cleanup already applied; render/check saved file instead'
 m.use('A');protected={'shared':c.i.preserve_shared(),'basin':m.hashes(c.AG),'A_entrance':{o.name:m.signature(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}}
 m.use('B');floating=[o.name for o in h.COLS[m.BR].objects if o.name.startswith('B_ExposedBurnedRoofRib')];changed=set(floating+['B_KitchenRafter'])
 protected['B_accepted']={o.name:m.signature(o) for col in [m.BC,m.BR,'B_ROUTE'] for o in h.COLS[col].objects if o.name not in changed}
 protected['entrance_interface']={o.name:m.signature(o) for o in h.COLS['CASTLE_EXTERIOR_SHARED'].objects if o.name.startswith(('CastleMainEntrance','CastleFrontCurtain','CastleGatehouse'))}
 protected['A_route']=m.hashes('A_ROUTE')
 rec=r.new_collection('PRE_STRUCTURAL_CLEANUP_RETAINED');rec.hide_render=True;rec.hide_viewport=True
 def retire(o):
  for col in list(o.users_collection):col.objects.unlink(o)
  rec.objects.link(o);o.name='RECOVERED_STRUCT_'+o.name
 r.new_collection(BS,'CASTLE_B_STRONGHOLD');r.new_collection(AS,'CASTLE_A_CATASTROPHE')
 endpoints={};chains=[]
 def beam(name,a,b,width=6,mat='Timber',col=BS):
  o=h.beam(name,a,b,width,col,mat);endpoints[o.name]=[a,b];o['structural_role']='Connected bearing/framing, not a new traversal feature';return o
 # Suspended framing bridges opened interior volumes; no supports added to combat floors.
 beam('B_STRUCT_KeepSouthBearing',(-174,1658,188),(123,1658,188),8)
 beam('B_STRUCT_KeepEastBearing',(-18,1658,188),(-18,1776,188),8)
 beam('B_STRUCT_KeepSouthTrussWest',(-174,1658,188),(-96,1658,254),6)
 beam('B_STRUCT_KeepSouthTrussEast',(-96,1658,254),(123,1658,188),6)
 h.box('B_STRUCT_KeepSouthUpperInfill',(-96,1658,223),(156,4,62),BS,'Fieldstone')
 h.box('B_STRUCT_KeepEastUpperInfill',(-18,1717,223),(4,118,62),BS,'Fieldstone')
 beam('B_STRUCT_ArchiveFrontBearing',(-118,1632,166),(123,1632,166),8)
 beam('B_STRUCT_ArchiveRearBearing',(-118,1702,166),(119,1702,166),8)
 beam('B_STRUCT_ArchiveEdgeBearing',(3,1632,166),(3,1702,166),6)
 beam('B_STRUCT_AudienceWestBearing',(-77,1516,190),(-77,1658,190),6)
 # Visible mortise-like framing at intentionally broken cut edges, rather than free hovering ribs.
 for ident,x0,edge,y0,y1,zz,ys in [('Household',-232,-200,1382.5,1451,156,[1386,1414]),('CrossHall',-56,41,1373,1439,140,[1386,1414]),('Steward',-176,-94.5,1452.5,1547.5,174,[1486,1514])]:
  beam('B_STRUCT_'+ident+'_CutEdge',(edge,y0,zz-1),(edge,y1,zz-1),4,'CharredTimber')
  for yy in ys:beam('B_STRUCT_'+ident+'_BurnedRib',(x0,yy,zz),(edge,yy,zz),3,'CharredTimber')
 for yy in [1386,1414]:beam('B_STRUCT_Household_BreachRib',(-200,yy,156),(-134,yy,156),3,'CharredTimber')
 beam('B_STRUCT_HouseholdKneeBrace',(-232,1414,146),(-200,1414,155),4,'CharredTimber')
 for n in floating:retire(bpy.data.objects[n])
 retire(bpy.data.objects['B_KitchenRafter']);beam('B_KitchenRafter',(144,1697,135),(214,1715,98),4,'CharredTimber',m.BC)
 # Fill the architectural arch haunches; the arch opening and route remain untouched.
 arch_infill('B_STRUCT_PrimaryHallHaunch',20,1353,96,52,39,44,BS)
 arch_infill('B_STRUCT_EntrySouthHaunch',0,1214,96,38,30,38,BS)
 arch_infill('B_STRUCT_EntryNorthHaunch',0,1296,96,44,30,38,BS)
 arch_infill('B_STRUCT_BarracksNorthHaunch',155,1375,96,34,30,44,BS)
 arch_infill('B_STRUCT_GallerySouthHaunch',160,1486,120,38,30,38,BS)
 arch_infill('B_STRUCT_GalleryNorthHaunch',160,1598,120,34,30,38,BS)
 # Shared gate roof framing seats on the surviving upper-hall wall and roof ridge.
 ext='CASTLE_EXTERIOR_SHARED'
 arch_infill('CastleMainEntranceUpperInfill',0,1210,96,46,49,54,ext,34)
 beam('CastleGateRoof_EaveBearing',(46,1182,174),(46,1238,174),4,'CharredTimber',ext)
 beam('CastleGateRoof_RidgeBearing',(0,1182,197),(0,1238,197),4,'CharredTimber',ext)
 for yy in [1182,1210,1238]:beam('CastleGateRoof_ConnectedRafter',(46,yy,174),(0,yy,197),3,'CharredTimber',ext)
 # Two different peripheral failures, away from front gate and all AreaII walls.
 cuts=[((250,1660,164),(28,42,18)),((255,1758,225),(24,24,26))];exterior_changed=[]
 for loc,size in cuts:
  for o in list(h.COLS[ext].objects):
   if o.type!='MESH' or not o.name.startswith(('CastleSideCurtain','CastleCornerTower')):continue
   lo,hi=bounds(o)
   if all(hi[k]>loc[k]-size[k]/2 and lo[k]<loc[k]+size[k]/2 for k in range(3)):
    n=o.name;c.cut_box(o,loc,size);exterior_changed.append(n)
    if not o.data.polygons:retire(o)
 h.box('CastleRecentCopingFall',(236,1654,97.75),(7,11,4),ext,'FreshStone')
 h.box('CastleRecentCrownFall',(236,1676,98.75),(6,7,6),ext,'FreshStone')
 # Replace affected derived sources only; all original roof mass meshes remain exact.
 m.use('A')
 for col in [m.AC,m.AR]:
  for o in list(h.COLS[col].objects):
   if o.get('baseline_source') in changed:retire(o)
 for o in list(h.COLS['CASTLE_A_CATASTROPHE'].objects):
  if o.name.startswith('A_GatehouseExposedRafter'):retire(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=1,depth=500,location=(20,1545,240));cutter=bpy.context.object;cutter.scale=(175,185,1)
 copied=0;removed=0
 for src in [*h.COLS[BS].objects,bpy.data.objects['B_KitchenRafter']]:
  if src.type!='MESH':continue
  # B north entry differs from A's turn west; its infill has no matching A doorway.
  if src.name=='B_STRUCT_EntryNorthHaunch':continue
  o=src.copy();o.data=src.data.copy();h.COLS[AS].objects.link(o);o.name='A_From_'+src.name;o['baseline_source']=src.name
  c.bool_difference(o,cutter)
  if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True);removed+=1
  else:copied+=1
 bpy.data.objects.remove(cutter,do_unlink=True)
 # Short A entrance retains its own accepted orientation; apply the same haunch policy.
 arch_infill('A_STRUCT_GuardNorthHaunch',-92,1356,96,34,30,36,AS)['structural_source']='Shared arch-infill construction policy'

 bpy.context.view_layer.update()
 assert protected['shared']==c.i.preserve_shared() and protected['basin']==m.hashes(c.AG)
 assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['A_entrance'].items())
 assert protected['A_route']==m.hashes('A_ROUTE')
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['B_accepted'].items())
 assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['entrance_interface'].items())
 report={'input_checkpoint':'004a567','date':'2026-10-08','protected':protected,'changed_B_sources':sorted(changed),'support_beam_endpoints':endpoints,'exterior_changed':exterior_changed,'A_surviving_derived_supports':copied,'A_fully_removed_supports':removed,'original_roof_masses_exact':True,'accepted_layout_exact':True,'B_supports_collection':BS,'A_supports_collection':AS,'localized_wall_damage_regions':cuts,'no_production_or_chunk_separation':True,'observations_deferred':['Village footprints/pitched roof construction too repetitive','Vary types/silhouettes/heights/damage/functions','Compose market with evidence of former use','Share village/castle architectural asset language']}
 (EV/'structural_report.json').write_text(json.dumps(report,indent=2))
 cameras();m.use('B');scene.camera=bpy.data.objects['STRUCT_roof_supports']
 bpy.data.texts['START_HERE'].write('\nFINAL STRUCTURAL CLEANUP: B_STRUCTURAL_SUPPORTS / A_DERIVED_STRUCTURAL_SUPPORTS. Bearing/truss framing, upper keep infill, arch haunches, connected burned ribs and modest shared curtain/tower damage. Accepted layout, roofs, routes, B final rooms, A arena and town unchanged. StructuralCleanupReview has paired before/after evidence. Ready for owner acceptance; modular-production PLANNING follows, no chunk separation or production work yet. Village variety/market composition/shared asset language recorded for later.\n')
 scene['CastleAcceptance']='Provisionally accepted architecture/layout; final bounded structure cleanup ready for owner acceptance and subsequent modular-production planning'
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'));print('STRUCTURAL SAVED',copied,removed,len(exterior_changed),flush=True)

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 selected=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--views=')),None)
 if '--before' in args:render('before',selected)
 elif '--render-only' in args:render('after',selected)
 else:cleanup()
