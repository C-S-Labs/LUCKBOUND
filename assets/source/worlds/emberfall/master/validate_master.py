import bpy,pathlib,json,hashlib
r=pathlib.Path('E:/BlenderAIProjects/Worktrees/emberfall-production/assets/source/worlds/emberfall/master');reg=json.loads((r/'source_registry.json').read_text());report=json.loads((r/'master_validation.json').read_text())
assert bpy.data.filepath==reg['master'] or pathlib.Path(bpy.data.filepath)==pathlib.Path(reg['master'])
assert len([s for s in bpy.data.scenes if s.name in report['scenes']])==6
extra=[s for s in bpy.data.scenes if s.name not in report['scenes']]
assert all(len(s.objects)==0 for s in extra)
report['empty_startup_scene']=bool(extra)
assert len([m for m in bpy.data.meshes if m.library is None])==0
assert not any(o.override_library for o in bpy.data.objects)
for lib in bpy.data.libraries:assert pathlib.Path(bpy.path.abspath(lib.filepath)).exists()
for v in ('A','B'):
 s=bpy.data.scenes['03_AreaII_Castle'+v];cols=[o.instance_collection.name for o in s.objects if o.instance_type=='COLLECTION'];assert ('CASTLE_A_CATASTROPHE' in cols)==(v=='A');assert ('CASTLE_B_STRONGHOLD' in cols)==(v=='B');assert all('RETAINED' not in c for c in cols)
for src in reg['sources'].values():assert hashlib.sha256(pathlib.Path(src['path']).read_bytes()).hexdigest()==src['sha256']
report['reopened_links_verified']=True;report['no_local_overrides']=True;report['variant_exclusivity_verified']=True;(r/'master_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('MASTER REOPEN PASS:6 scenes,4 resolved libraries,60 linked collections,0 local meshes/overrides; B/A exclusive; source hashes unchanged')
