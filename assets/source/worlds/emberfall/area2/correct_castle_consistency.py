"""A/B consistency: fixed A remnants must be subsets of actual active B architectural volumes."""
import bpy,bmesh,importlib.util,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('failure',ROOT/'refine_impact_structural_failure.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.m;h=q.h;r=q.r;c=q.c;s=q.s;OUT=q.OUT;EV=OUT/'ConsistencyReview';EV.mkdir(exist_ok=True);scene=bpy.context.scene
REC='PRE_CONSISTENCY_RETAINED'
VIEWS=[('overhead',(0,1490,1080),(0,1490,110),'ORTHO',900),('edge',(-10,1490,230),(-165,1644,161),'PERSP',28)]

def cameras():
 col=r.new_collection('CONSISTENCY_REVIEW_CAMERAS')
 for name,loc,target,kind,value in VIEWS:
  ident='CONSISTENCY_'+name
  if ident in bpy.data.objects:o=bpy.data.objects[ident];d=o.data
  else:d=bpy.data.cameras.new(ident);o=bpy.data.objects.new(ident,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_end=6000
  if name=='overhead':o.rotation_euler=(0,0,0)
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value

def render(stage):
 cameras();scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.cycles.samples=20
 for col in ['Route','A_ROUTE','B_ROUTE']:h.COLS[col].hide_render=True
 for variant,name in [('B','overhead'),('A','overhead'),('A','edge')]:
  m.use(variant);scene.camera=bpy.data.objects['CONSISTENCY_'+name];scene.render.filepath=str(EV/(variant+'_'+name+'_'+stage+'.png'));bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name);print('CONSISTENCY VIEW',variant,name,stage,flush=True)

def normal(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

def volume(o):
 bm=bmesh.new();bm.from_mesh(o.data);v=abs(bm.calc_volume(signed=True));bm.free();return v

def cutter(names):
 verts=[];faces=[]
 for name in names:
  o=bpy.data.objects[name];offset=len(verts);verts.extend([tuple(o.matrix_world@v.co) for v in o.data.vertices]);faces.extend([tuple(j+offset for j in p.vertices) for p in o.data.polygons])
 me=bpy.data.meshes.new('ActualBVolume');me.from_pydata(verts,[],faces);me.update();me.materials.append(h.MATS['Fieldstone']);o=bpy.data.objects.new('ActualBVolume',me);scene.collection.objects.link(o);normal(o);return o

def operation(o,names,kind):
 tool=cutter(names);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;normal(o)
 mod=o.modifiers.new('ActualBaselineVolume','BOOLEAN');mod.operation=kind;mod.solver='EXACT';mod.object=tool;mod.use_self=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 normal(o)
 for k,mat in enumerate(o.data.materials):
  if mat is None:o.data.materials[k]=h.MATS['Fieldstone']
 bpy.data.objects.remove(tool,do_unlink=True)

def outside(o,names):
 probe=o.copy();probe.data=o.data.copy();scene.collection.objects.link(probe);operation(probe,names,'DIFFERENCE');v=volume(probe);bpy.data.objects.remove(probe,do_unlink=True);return v

def surface_error(o,source):
 src=bpy.data.objects[source];tree=BVHTree.FromPolygons([src.matrix_world@v.co for v in src.data.vertices],[list(p.vertices) for p in src.data.polygons])
 o.data.calc_loop_triangles();samples=[]
 for tri in o.data.loop_triangles:
  pts=[o.matrix_world@o.data.vertices[k].co for k in tri.vertices]
  samples.extend(pts+[(pts[0]+pts[1]+pts[2])/3]+[(pts[k]+pts[(k+1)%3])/2 for k in range(3)])
 return max(tree.find_nearest(p)[3] for p in samples)

def active_b():return {o.name for o in h.COLS['CASTLE_B_STRONGHOLD'].all_objects if o.type=='MESH' and o.name not in h.COLS['B_ROUTE'].objects.keys()}|{o.name for o in h.COLS['CASTLE_EXTERIOR_SHARED'].all_objects if o.type=='MESH'}

def counterpart(o,B):
 if o.name.startswith(('A_WestGuardHall','A_FailingGallery','A_STRUCT_GuardNorth','A_RevealLedge')):return []
 if o.name.startswith('A_EntryHall_'):
  suffix=o.name[len('A_EntryHall_'):]
  if suffix=='NWall':return ['B_Composed_Entry_NWall','B_Composed_Entry_NWall.001']
  if suffix.startswith(('WWall','WLintel')):return ['B_Composed_Entry_WWall']
  name='B_Composed_Entry_'+suffix;return [name] if name in B else []
 if o.name=='A_BrokenGatehouseRoof':return ['CastleGatehouseRoof']
 if o.name=='A_FracturedFrontCurtain':return ['CastleFrontCurtain.001']
 if o.name.startswith('A_SurvivingCurtainCrown'):return [n for n in B if n.startswith('CastleFrontCurtain') and n.endswith('.001') or n in B and n.startswith('CastleFrontCurtain_Crown')]
 if o.name=='A_ResidentialSouthCornerReturn':return ['B_Composed_ResidentialTower_SWall','B_ResidentialClosedSide']
 source=o.get('baseline_source','');return [source] if source in B else []

def audit_list():
 result=[]
 ground=set(o.name for o in h.COLS[c.AG].all_objects);routes=set(o.name for o in h.COLS['A_ROUTE'].all_objects)
 for o in h.COLS['CASTLE_A_CATASTROPHE'].all_objects:
  if o.type!='MESH' or o.name in ground or o.name in routes:continue
  if 'ActiveBurn' in o.name or 'BurnZone' in o.name:continue
  debris=o.name.startswith(('A_Fallen_','A_ExteriorRecentWallFall','A_BrokenTowerTop')) or 'RecentLocalizedCollapse' in o.name or 'RoofFall' in o.name
  result.append((o,debris))
 return result

def apply():
 assert REC not in bpy.data.collections,'Already applied'
 m.use('B');B=active_b();protected={'B':{n:m.signature(bpy.data.objects[n]) for n in B},'shared':c.i.preserve_shared()}
 m.use('A');protected['arena']=m.hashes(c.AG);protected['route']=m.hashes('A_ROUTE')
 rec=r.new_collection(REC);rec.hide_render=True;rec.hide_viewport=True
 edits=[];maprows=[]
 def retire(o,why):
  edits.append({'name':o.name,'action':'remove','reason':why})
  for col in list(o.users_collection):col.objects.unlink(o)
  rec.objects.link(o);o.name='RECOVERED_CONSISTENCY_'+o.name
 for o,debris in list(audit_list()):
  if o.name=='A_From_B_Composed_ResidentialTower_SWall':
   retire(o,'Duplicate of the actual-source constrained residential south return');continue
  names=counterpart(o,B)
  if debris:
   if not names:
    names=['CastleFrontCurtain.001'] if o.name.startswith('A_ExteriorRecentWallFall') else [n for n in B if n.startswith('CastleCornerTower_Coping')][:1]
   o['baseline_sources']=json.dumps(names);o['consistency_kind']='Displaced destruction fragment; not an added standing structure'
   maprows.append({'A':o.name,'B':names,'kind':'displaced fragment'});continue
  if not names:retire(o,'No architectural counterpart in active B; legacy invented room/feature');continue
  if o.name=='A_BrokenGatehouseRoof':
   assert surface_error(o,'CastleGatehouseRoof')<.001
   o['baseline_sources']=json.dumps(names);o['consistency_kind']='Fixed surface subset of actual open B roof mesh'
   maprows.append({'A':o.name,'B':names,'kind':'fixed surface subset'});continue
  oldvol=volume(o);extra=outside(o,names)
  if extra>max(.02,oldvol*1e-6):
   operation(o,names,'INTERSECT');edits.append({'name':o.name,'action':'constrain_to_actual_B','outside_volume_before':round(extra,5),'B':names})
  if not o.data.polygons or volume(o)<.25:
   retire(o,'No substantial surviving volume in the claimed B counterpart');continue
  o['baseline_sources']=json.dumps(names);o['consistency_kind']='Fixed surviving subset of actual B geometry'
  # Catastrophic retreat of the protruding residential/keep plates, no new construction.
  if o.name in ['A_ResidentialRoofCornerRemnant','A_ResidentialNorthUpperRoom']:
   c.cut_box(o,(-150,1629,180),(180,86,170))
  if o.name=='A_ResidentialWestRoofCrown':c.cut_box(o,(-218,1630,213),(20,84,40))
  if o.name in ['A_ResidentialSouthCornerReturn','A_From_B_Composed_ResidentialTower_SWall']:c.cut_box(o,(-174,1600,204),(90,12,92))
  if o.name=='A_From_B_Composed_ResidentialTower_WWall':c.cut_box(o,(-214,1631,198),(16,82,80))
  if o.name=='A_From_B_Composed_ResidentialTower_Pier':c.cut_box(o,(-211,1618,210),(12,12,104))
  if o.name=='A_From_B_Composed_ResidentialTower_Pier.002':c.cut_box(o,(-211,1644,215),(12,12,94))
  if o.name=='A_KeepNorthernRoofRemnant':
   c.cut_box(o,(12,1750,276),(184,100,80))
  if o.name=='A_KitchenEastSupportedRoof':
   c.cut_box(o,(201,1681,140),(20,48,36))
  # Legacy crater-edge room strips without a credible footprint are gone; valid piers/walls remain.
  if not o.data.polygons or volume(o)<.25:retire(o,'Affected roof/upper-floor bay fully collapses');continue
  normal(o)
  for k,mat in enumerate(o.data.materials):
   if mat is None:o.data.materials[k]=h.MATS['Fieldstone']
  assert outside(o,names)<max(.03,volume(o)*1e-6),o.name
  maprows.append({'A':o.name,'B':names,'kind':'fixed subset','volume':round(volume(o),4)})
 # The made-up stair blocks/landing cannot be retained as a new solid staircase.
 for o in list(h.COLS[q.COL].objects):
  if o.name.startswith(('A_BrokenStairGroundedTread','A_StairInterruptedLanding')):retire(o,'Custom solid stair/landing does not match B stepped geometry')
 maprows=[row for row in maprows if row['A'] in bpy.data.objects]
 # Audit shared shell separately: same object in both layers, no alternative counterpart needed.
 shared_rows=[{'A':n,'B':[n],'kind':'shared exact object'} for n in h.COLS['CASTLE_EXTERIOR_SHARED'].objects.keys() if bpy.data.objects[n].type=='MESH']
 bpy.context.view_layer.update();assert protected['arena']==m.hashes(c.AG) and protected['route']==m.hashes('A_ROUTE');assert protected['shared']==c.i.preserve_shared()
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['B'].items())
 report={'input_checkpoint':'7682ae8','protected':protected,'edits':edits,'A_to_actual_B':maprows+shared_rows,'all_fixed_A_valid_actual_B_subsets':True,'no_new_rooms_buildings_features':True,'legacy_west_halls_removed_route_preserved':True,'approved_arena_exact':True,'B_exact':True,'scope':'A corrections/removals only; no B/shared changes; displaced rubble classified separately'}
 (EV/'consistency_report.json').write_text(json.dumps(report,indent=2));cameras();m.use('A');scene.camera=bpy.data.objects['CONSISTENCY_overhead']
 bpy.data.texts['START_HERE'].write('\nACTUAL A/B CONSISTENCY: A-only west guard/failing gallery and relocated rear bearing removed. All fixed A survivors constrained to actual active B solids; baseline_sources + consistency_report distinguish stationary subsets/shared geometry/displaced debris. Crater/route exact. CONSISTENCY_overhead same camera for B/A; ConsistencyReview / edge closeup. STOP FOR OWNER REVIEW. No production.\n')
 scene['CastleAcceptance']='Approved B and arena; source-consistency correction pending owner review'
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'));print('CONSISTENCY SAVED',len(edits),len(maprows),flush=True)

def repair_cut_faces():
 report=json.loads((EV/'consistency_report.json').read_text());m.use('A')
 # Same baseline south-wall volume was present twice after the earlier fracture pass.
 dup=bpy.data.objects.get('A_From_B_Composed_ResidentialTower_SWall')
 if dup:
  for col in list(dup.users_collection):col.objects.unlink(dup)
  h.COLS[REC].objects.link(dup);old=dup.name;dup.name='RECOVERED_CONSISTENCY_'+old
  report['edits'].append({'name':old,'action':'remove_duplicate','reason':'Same south-wall volume already covered by source-constrained fractured return'})
  report['A_to_actual_B']=[row for row in report['A_to_actual_B'] if row['A']!=old]
  (EV/'consistency_report.json').write_text(json.dumps(report,indent=2))

 for row in report['A_to_actual_B']:
  if not row['kind'].startswith('fixed'):continue
  o=bpy.data.objects[row['A']];normal(o)
  for k,mat in enumerate(o.data.materials):
   if mat is None:o.data.materials[k]=h.MATS['Fieldstone']
  if not o.data.materials:o.data.materials.append(h.MATS['Fieldstone'])
  for poly in o.data.polygons:
   if poly.material_index>=len(o.data.materials):poly.material_index=0
 p=report['protected'];assert p['arena']==m.hashes(c.AG) and p['route']==m.hashes('A_ROUTE')
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in p['B'].items())
 m.use('A');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'));print('Cut-face repair/duplicate isolation; B, arena and route preserved',flush=True)

def final_coverage():
 report=json.loads((EV/'consistency_report.json').read_text());p=report['protected'];m.use('B')
 assert all(m.signature(bpy.data.objects[n])==v for n,v in p['B'].items())
 m.use('A');assert p['arena']==m.hashes(c.AG) and p['route']==m.hashes('A_ROUTE') and p['shared']==c.i.preserve_shared()
 live={o.name for o,debris in audit_list()};mapped={row['A'] for row in report['A_to_actual_B']};assert live<=mapped
 checks=json.loads((EV/'consistency_checks.json').read_text())
 checks['fixed_subset_residuals']=[row for row in checks['fixed_subset_residuals'] if bpy.data.objects.get(row['A']) and row['A'] in mapped]
 checks['fixed_survivors_actual_B_subset_verified']=len(checks['fixed_subset_residuals'])
 assert {row['A'] for row in checks['fixed_subset_residuals']}=={row['A'] for row in report['A_to_actual_B'] if row['kind'].startswith('fixed')}
 checks['post_duplicate_removal_live_coverage_and_preservation_pass']=True
 checks['note']='Full geometric audit performed on saved architecture; later removed one duplicate and corrected normals/material slots without moving retained geometry. All retained proofs still covered.'
 (EV/'consistency_checks.json').write_text(json.dumps(checks,indent=2));print('FINAL COVERAGE PASS',len(checks['fixed_subset_residuals']),flush=True)

def check():
 report=json.loads((EV/'consistency_report.json').read_text());p=report['protected'];m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in p['B'].items())
 m.use('A');assert p['arena']==m.hashes(c.AG) and p['route']==m.hashes('A_ROUTE') and p['shared']==c.i.preserve_shared()
 rows=[]
 for row in report['A_to_actual_B']:
  o=bpy.data.objects[row['A']];assert all(bpy.data.objects.get(n) for n in row['B'])
  if row['kind']=='fixed surface subset':
   err=surface_error(o,row['B'][0]);assert err<.001
   rows.append({'A':o.name,'surface_distance_to_B':round(err,6)})
  elif row['kind']=='fixed subset':
   extra=outside(o,row['B']);assert extra<max(.03,volume(o)*1e-6),(o.name,extra)
   rows.append({'A':o.name,'outside_actual_B_volume':round(extra,6)})
 live={o.name for o,debris in audit_list()};mapped={row['A'] for row in report['A_to_actual_B']};assert live<=mapped,live-mapped
 checks={'all_surviving_A_architecture_audited':True,'fixed_survivors_actual_B_subset_verified':len(rows),'fixed_subset_residuals':rows,'shared_B_geometry_exact':True,'approved_arena_route_exact':True,'no_unmapped_A_architecture':True,'displaced_rubble_identified_separately':True}
 (EV/'consistency_checks.json').write_text(json.dumps(checks,indent=2));print('CONSISTENCY CHECK PASS',len(rows),flush=True)

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--final-review' in args:
  final_coverage();render('after')
 elif '--repair-cut-faces' in args:repair_cut_faces()
 elif '--review' in args:
  render('after');check()
 elif '--before' in args:render('before')
 elif '--after' in args:render('after')
 elif '--check' in args:check()
 else:apply()


