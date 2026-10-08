"""Read-only diagnosis of the previous gate's terrain corrections."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview')
out=Path('E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview')
bpy.ops.wm.open_mainfile(filepath=str(root/'BurnedPlainsProductionGate.blend'))
base=bpy.data.scenes['Area_I_Modularity_0_180_0']
study=bpy.data.scenes['AREA_I_FINAL_GATE_RETURN_ROUTE']
names=['opening_edge','active_burn_mid_plains','active_burn_mid_plains','active_burn_mid_plains','interior_edge']
sources=[next(o for o in base.objects if o.name=='PLAYABLE_'+n) for n in names]
meshes=[next(o for o in study.objects if o.name=='GATE_TERRAIN_'+str(i+1)) for i in range(5)]
rows=[]
for i,(a,b) in enumerate(zip(sources,meshes)):
    deltas=[abs(v.co.z-w.co.z) for v,w in zip(a.data.vertices[:4225],b.data.vertices[:4225])]
    j=max(range(len(deltas)),key=deltas.__getitem__)
    rows.append({'chunk':i+1,'max_delta':deltas[j],'local_position':list(a.data.vertices[j].co),
                 'before_world_height':a.data.vertices[j].co.z+b.matrix_world.translation.z,
                 'after_world_height':b.data.vertices[j].co.z+b.matrix_world.translation.z})
report={'corrections':rows,'socket_transforms':'previous actual ChunkCore probe passed; centers oppose/coincide',
        'cause':'source straight rising template reused at rotated and turned exits; off-mouth edge/corner heights not contracted; shared-corner averaging then adjusted up to 17.98 studs',
        'not_tested_previously':'matching simplified collision'}
out.mkdir(parents=True,exist_ok=True)
(out/'root_cause.json').write_text(json.dumps(report,indent=2))
(Path(__file__).parent/'edge_profile_root_cause.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
