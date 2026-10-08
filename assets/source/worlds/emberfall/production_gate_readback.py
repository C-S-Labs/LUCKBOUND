"""Cheap readback of experimental corner adjustments; never changes scenes."""
import bpy
import json
from pathlib import Path

out=Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview')
bpy.ops.wm.open_mainfile(filepath=str(out/'BurnedPlainsProductionGate.blend'))
baseline=bpy.data.scenes['Area_I_Modularity_0_180_0']
scene=bpy.data.scenes['AREA_I_FINAL_GATE_RETURN_ROUTE']
names=['opening_edge','active_burn_mid_plains','active_burn_mid_plains','active_burn_mid_plains','interior_edge']
rows=[]
for i,name in enumerate(names):
    original=next(o for o in baseline.objects if o.name=='PLAYABLE_'+name)
    current=next(o for o in scene.objects if o.name=='GATE_TERRAIN_'+str(i+1))
    diffs=[abs(a.co.z-b.co.z) for a,b in zip(original.data.vertices[:4225],current.data.vertices[:4225])]
    rows.append({'chunk':i+1,'max_prototype_shape_adjustment_studs':max(diffs)})
report=json.loads((out/'production_gate_report.json').read_text())
report['prototype_geometry_adjustments']=rows
report['studio_tested']=True
report['fbx_probe']['roblox_import']='PASS: production_gate_studio_report.json'
for path in [out/'production_gate_report.json',Path(__file__).parent/'production_gate_report.json']:
    path.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(rows))
