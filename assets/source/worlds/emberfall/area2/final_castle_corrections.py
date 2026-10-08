"""Owner-final keep/gate corrections and restrained architecture-linked impact rim."""
import bpy,importlib.util,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('structural',ROOT/'cleanup_castle_structure.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m;h=s.h;r=s.r;c=s.c;scene=bpy.context.scene
OUT=s.OUT;EV=OUT/'FinalCorrectionsReview';EV.mkdir(exist_ok=True)
VIEWS=[('keep_support','B',(-365,1545,255),(-65,1692,211),'ORTHO',390),('gate','A',(180,1005,220),(0,1210,161),'PERSP',48),('crater','A',(340,1190,630),(20,1545,96),'ORTHO',540)]
# Radius variation follows unequal architectural sectors rather than circular noise.
OFFSETS=[4,8,13,10,4,-3,-7,-2,5,11,14,8,1,-5,-8,-3,4,9,3,-4,-10,-5,2,8,12,7,0,-6,-3,4,10,7]
def cameras():
 col=r.new_collection('FINAL_CORRECTION_CAMERAS')
 for name,variant,loc,target,kind,value in VIEWS:
  ident='FINAL_'+name
  if ident in bpy.data.objects:o=bpy.data.objects[ident];d=o.data
  else:d=bpy.data.cameras.new(ident);o=bpy.data.objects.new(ident,d);col.objects.link(o)
  o.location=loc;o.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();d.type=kind;d.clip_end=6000
  if kind=='ORTHO':d.ortho_scale=value
  else:d.lens=value

def render(stage):
 cameras();scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.cycles.samples=20
 for name,v,loc,target,kind,value in VIEWS:
  m.use(v)
  for route in ['Route','A_ROUTE','B_ROUTE']:h.COLS[route].hide_render=True
  scene.camera=bpy.data.objects['FINAL_'+name];scene.render.filepath=str(EV/(name+'_'+stage+'.png'))
  bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name);print('FINAL VIEW',name,stage,flush=True)

def radial_offset(x,y):
 a=math.atan2((y-1545)/185,(x-20)/175)%math.tau;t=a/math.tau*32;k=int(t);return OFFSETS[k]*(1-(t-k))+OFFSETS[(k+1)%32]*(t-k)

def alter_rim(o,ring_only=False):
 count=0;inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  w=o.matrix_world@v.co;rr=math.hypot((w.x-20)/175,(w.y-1545)/185)
  if abs(rr-1)>.022:continue
  delta=radial_offset(w.x,w.y);factor=1+delta/180
  w.x=20+(w.x-20)*factor;w.y=1545+(w.y-1545)*factor
  if ring_only:w.z+=.35*math.sin(math.atan2(w.y-1545,w.x-20)*3+.7)
  v.co=inv@w;count+=1
 if count:o.data.update();o['impact_rim_revision']='Same baseline impact boundary, locally displaced by architectural sectors; central floor unchanged'
 return count

def apply():
 assert 'FINAL_CORRECTIONS_RETAINED' not in bpy.data.collections,'Already applied'
 m.use('B');protected={'shared':c.i.preserve_shared(),'B':{o.name:m.signature(o) for col in [m.BC,m.BR,'B_ROUTE'] for o in h.COLS[col].objects},'B_interior_frame':{o.name:m.signature(o) for o in h.COLS[s.BS].objects if 'KeepSouthTruss' not in o.name}}
 m.use('A');protected['A_floor']=m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN']);protected['A_route']=m.hashes('A_ROUTE');protected['A_entry']={o.name:m.signature(o) for o in bpy.data.objects if o.name.startswith(('A_EntryHall','A_WestGuardHall','A_FailingGallery'))}
 rec=r.new_collection('FINAL_CORRECTIONS_RETAINED');rec.hide_render=True;rec.hide_viewport=True;retired=[]
 def retire(o):
  retired.append(o.name)
  for col in list(o.users_collection):col.objects.unlink(o)
  rec.objects.link(o);o.name='RECOVERED_FINAL_'+o.name
 for col in [s.BS,s.AS]:
  for o in list(h.COLS[col].objects):
   if 'KeepSouthTruss' in o.name:retire(o)
 for o in list(h.COLS['CASTLE_EXTERIOR_SHARED'].objects):
  if o.name.startswith('CastleGateRoof_'):retire(o)
 ext='CASTLE_EXTERIOR_SHARED'
 # Stone remains attached to the existing upper hall; no exposed reinforcement.
 h.box('CastleGateDamagedStoneEaveBase',(46,1210,175),(6,55,2),ext,'Fieldstone')
 h.box('CastleGateBrokenParapetFront',(46,1192,179),(6,18,8),ext,'Fieldstone')
 h.box('CastleGateBrokenParapetRear',(46,1226,178),(6,22,6),ext,'Fieldstone')
 c.cut_box(bpy.data.objects['CastleGateBrokenParapetFront'],(45,1200,182),(9,7,5))
 c.cut_box(bpy.data.objects['CastleGatehouseUpperHall'],(38,1184,173),(14,10,8))
 c.cut_box(bpy.data.objects['CastleMainEntranceUpperInfill'],(18,1196,150),(9,8,4))
 altered={};m.use('A')
 for col in [m.AC,m.AR,s.AS]:
  for o in h.COLS[col].objects:
   if o.type=='MESH' and o.get('baseline_source'):
    n=alter_rim(o)
    if n:altered[o.name]={'baseline_source':o['baseline_source'],'perimeter_vertices':n}
 for name in ['A_PeripheralShellLand','A_ShallowImpactTransition']:
  o=bpy.data.objects[name];altered[name]={'rim_vertices':alter_rim(o,True)}
 bpy.context.view_layer.update()
 assert protected['shared']==c.i.preserve_shared()
 assert protected['A_floor']==m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN'])
 assert protected['A_route']==m.hashes('A_ROUTE')
 assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['A_entry'].items())
 m.use('B');assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['B'].items())
 assert all(m.signature(bpy.data.objects[n])==v for n,v in protected['B_interior_frame'].items())
 assert all(all(math.isfinite(a) for a in v.co) for name in altered for v in bpy.data.objects[name].data.vertices)
 report={'input_checkpoint':'d210b23','protected':protected,'retired':retired,'A_boundary_edits':altered,'radius_offsets_studs':OFFSETS,'rim_height_variation_studs':.35,'B_geometry_routes_unchanged':True,'interior_framing_preserved':True,'flat_basin_exact':True,'A_entry_route_exact':True,'shared887_exact':True,'gate_changes_shared_both_variants':True,'production_notes':['Selective charring and breakage of interior framing','Localized ceiling collapse and damaged beams; do not damage every support uniformly'],'no_production_separation_upload':True}
 (EV/'final_corrections_report.json').write_text(json.dumps(report,indent=2))
 cameras();m.use('B');scene.camera=bpy.data.objects['FINAL_keep_support']
 bpy.data.texts['START_HERE'].write('\nOWNER-FINAL CORRECTIONS: exposed keep truss removed; shared gate timber replaced by attached broken masonry/parapet. Interior framing retained. A rim/adjacent cut edges locally displaced together; flat arena remains exact. FinalCorrectionsReview has three matched before/after pairs. Selective interior charring/breakage/ceiling collapse belongs to production detailing. Macro accepted; final correction acceptance -> modular-production PLANNING.\n')
 scene['CastleAcceptance']='Owner accepts macro architecture, B layout/final rooms and derived A; final corrections ready for owner acceptance and modular-production planning'
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EmberfallAreaII.blend'));print('FINAL CORRECTIONS SAVED',len(retired),len(altered),flush=True)

def check():
 report=json.loads((EV/'final_corrections_report.json').read_text());p=report['protected']
 m.use('B')
 assert all(m.signature(bpy.data.objects[n])==v for key in ['B','B_interior_frame'] for n,v in p[key].items())
 m.use('A');assert p['shared']==c.i.preserve_shared()
 assert p['A_floor']==m.signature(bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN'])
 assert p['A_route']==m.hashes('A_ROUTE')
 assert all(m.signature(bpy.data.objects[n])==v for n,v in p['A_entry'].items())
 assert all(bpy.data.objects.get(row['baseline_source']) for row in report['A_boundary_edits'].values() if 'baseline_source' in row)
 floor=bpy.data.objects['A_FLAT_FINAL_BOSS_BASIN'];assert all(abs((floor.matrix_world@v.co).z-92)<.001 for v in floor.data.vertices)
 assert all(n not in bpy.data.objects for n in report['retired'])
 checks={'saved_B_architecture_rooms_routes_exact':True,'interior_framing_except_rejected_exposed_truss_exact':True,'shared887_exact':True,'A_flat_combat_floor_exact_z92':True,'A_route_entrance_exact':True,'A_altered_edges_have_B_sources':True,'eight_rejected_supports_isolated':len(report['retired'])==8,'no_layout_massing_production_changes':True}
 (EV/'final_corrections_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks),flush=True)

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if '--check' in args:check()
 elif '--before' in args:render('before')
 elif '--after' in args:render('after')
 else:apply()
