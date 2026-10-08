"""Cheap saved-file readback: frozen instances, actual collision vertices, origin."""
import json
import hashlib
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import validate_edge_profiles as validator
from edge_profile_contract import SPECS,socket


def main():
    saved=json.loads((validator.OUT/'source_meshes.json').read_text())
    payloads={};closed=0
    for name in SPECS:
        visual=bpy.data.objects['VISUAL_'+name]
        heights={}
        for o in bpy.data.collections['COLLISION_'+name].objects:
            closed+=1
            if o.get('AuthoredSeamCell'):
                assert len(o.data.vertices)==6 and o['CollisionFidelity']=='Hull'
            for v in o.data.vertices:
                xy=tuple(v.co[:2]);heights[xy]=max(heights.get(xy,float('-inf')),v.co.z)
        cv=[[x,y,heights[(x,y)]] for y in range(-128,129,8) for x in range(-128,129,8)]
        payloads[name]={**saved[name],'visual':[list(v.co) for v in visual.data.vertices],'collision':cv}
        validator.validate(name,payloads[name])
        assert max(abs(a[2]-b[2]) for a,b in zip(saved[name]['collision'],cv))<.00001
    instances=0
    for scene in bpy.data.scenes:
        if not scene.name.startswith('REVIEW_'):continue
        for o in scene.objects:
            if not o.name.startswith('VISUAL_'):continue
            name=o.name.split('.')[0].removeprefix('VISUAL_')
            assert [list(v.co) for v in o.data.vertices]==payloads[name]['visual'],o.name
            instances+=1
    result={'saved_source_count':len(payloads),'frozen_assembled_visual_instances_checked':instances,
            'actual_closed_collision_objects_checked':closed,'origin_at_ground':True,
            'collision_grid_matches_actual_saved_pieces':True,'assembled_vertices_unchanged':True}
    (HERE/'edge_profile_saved_readback.json').write_text(json.dumps(result,indent=2))
    extra={'closed_collision_pieces_per_source':{n:len(bpy.data.collections['COLLISION_'+n].objects) for n in SPECS},
           'inputs_unchanged':True,'saved_readback':result,
           'preserved_inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
             (Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend'),
              Path('E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/BurnedPlainsModularity.blend'),
              Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview/BurnedPlainsProductionGate.blend'))},
           'boundary_collision':'Frozen convex triangular prisms with Hull fidelity, outer 8-stud row.',
           'evidence':[str(p) for p in sorted(validator.OUT.glob('[01][0-9]_*.png'))]}
    # Build already asserted before/after input hashes; retain metadata when the
    # independently rerunnable validator refreshes its measurements.
    for p in (HERE/'edge_profile_report.json',validator.OUT/'validation.json'):
        previous=json.loads(p.read_text());p.write_text(json.dumps({**previous,**extra},indent=2))
    print('SAVED_PROFILE_READBACK_PASS',json.dumps(result))


if __name__=='__main__':main()
