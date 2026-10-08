"""Create a review-only linked master; never save or change source libraries.
Run via repository tools/run_blender.py, from any checkout. Existing output is refused.
"""
import bpy, json, pathlib, hashlib, math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parent
registry=json.loads((ROOT/'source_registry.json').read_text())
out=pathlib.Path(registry['master']);out.parent.mkdir(parents=True,exist_ok=True)
if out.exists(): raise RuntimeError('Existing master: review it before explicitly choosing a new output.')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for s in registry['sources'].values():assert sha(s['path'])==s['sha256'],s['path']
bpy.ops.wm.read_factory_settings(use_empty=True)
linked={};scenes=[]
def collection(key,name):
 k=(key,name)
 if k not in linked:
  with bpy.data.libraries.load(registry['sources'][key]['path'],link=True) as (src,dst):
   assert name in src.collections,name;dst.collections=[name]
  linked[k]=dst.collections[0]
 return linked[k]
def scene(name):
 s=bpy.data.scenes.new(name);s['Purpose']='Linked review only; editable authority remains external source.';scenes.append(s);return s
bounds={}
def inst(s,key,name,offset=(0,0,0)):
 c=collection(key,name);o=bpy.data.objects.new(key+':'+name,None);o.instance_type='COLLECTION';o.instance_collection=c;o.location=offset;s.collection.objects.link(o);o['SourceFile']=registry['sources'][key]['path'];o['SourceCollection']=name
 pts=bounds.setdefault(s.name,[])
 for ob in c.all_objects:
  if ob.type=='MESH' and not ob.hide_render:
   pts.extend([ob.matrix_world @ Vector(v)+Vector(offset) for v in ob.bound_box])
 return o
catalogue=scene('01_SourceCatalogue_17_plus4')
for key in ('batch1','batch2'):
 for src in registry['sources'][key]['scenes']:
  if src['name'].startswith('EF_'):
   i=sum(1 for o in catalogue.objects if o.type=='EMPTY');offset=((i//2%7)*330,(i//2//7)*330,0)
   inst(catalogue,key,src['name'],offset);inst(catalogue,key,'COLLISION_'+src['name'],offset)
area1=scene('02_AreaI_AcceptedLayout1_Scenery')
layout=next(s for s in registry['sources']['scenery']['scenes'] if s['name']=='Layout1')
layout_names=[n for n in layout['root_collections'] if not n.startswith(('Scale_','COLLISION_'))]
for n in layout_names:inst(area1,'scenery',n)
shared=['AREA_II_SHARED','INNER_WALL_SHARED','CASTLE_GROUNDS_SHARED','CASTLE_EXTERIOR_SHARED']
for variant in ('B','A'):
 s=scene('03_AreaII_Castle'+variant);names=shared+['CASTLE_B_STRONGHOLD' if variant=='B' else 'CASTLE_A_CATASTROPHE']
 for n in names:inst(s,'area2',n)
 w=scene('04_WholeWorld_'+variant+'_PROVISIONAL');w['PlacementApproved']=False;w['PlacementNote']=registry['whole_world_placement']['note']
 for n in layout_names:inst(w,'scenery',n,registry['whole_world_placement']['area1_translation'])
 for n in names:inst(w,'area2',n)
for s in scenes:
 points=bounds[s.name];lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)));center=(lo+hi)/2;span=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
 cam=bpy.data.cameras.new(s.name+'_Camera');cam.type='ORTHO';cam.ortho_scale=span*1.3;o=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(o);o.location=center+Vector((.75,-1.05,1.2))*span;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();s.camera=o;cam.clip_end=30000
 sun=bpy.data.lights.new(s.name+'_Sun','SUN');sun.energy=3;sunobj=bpy.data.objects.new(sun.name,sun);s.collection.objects.link(sunobj);sunobj.rotation_euler=(.4,-.3,-.5)
 world=bpy.data.worlds.new(s.name+'_World');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.22,.28,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;s.world=world
 s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG'
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':area.spaces.active.clip_end=30000
bpy.context.window.scene=bpy.data.scenes['04_WholeWorld_B_PROVISIONAL']
for unused in list(bpy.data.scenes):
 if unused not in scenes:bpy.data.scenes.remove(unused)
notes=bpy.data.texts.new('READ_ME_AUTHORITY');notes.write('Linked review workspace. Do not make library overrides or editable mesh copies.\n'+registry['whole_world_placement']['note']+'\nAuthoritative paths/hashes are in source_registry.json and PRODUCTION_HANDOFF.md.\nSourceCatalogue has17 sources plus4 dressing variants, collision collections linked hidden as authored.\nAreaII scenes show the approved source collections with both castles reviewed separately.\n')
assert not [m for m in bpy.data.meshes if m.library is None]
bpy.ops.wm.save_as_mainfile(filepath=str(out))
for variant in ('B','A'):
 s=bpy.data.scenes['03_AreaII_Castle'+variant];s.render.filepath=str(out.parent/('AreaII_Castle'+variant+'.png'));bpy.context.window.scene=s;bpy.ops.render.render(write_still=True)
for s in registry['sources'].values():assert sha(s['path'])==s['sha256'],s['path']
report={'master':str(out),'sha256':sha(out),'scenes':[s.name for s in scenes],'linked_libraries':[bpy.path.abspath(l.filepath) for l in bpy.data.libraries],'local_meshes':0,'linked_collections':len(linked),'source_hashes_unchanged':True,'placement_approved':False}
(ROOT/'master_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
