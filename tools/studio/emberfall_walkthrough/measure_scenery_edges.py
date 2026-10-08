"""Read-only scenery edge comparison; invoke through tools/run_blender.py."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
base=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
out=Path('E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling')
sys.path.insert(0,str(base))
import assemble_batch1 as assembly
import batch1_shared as shared
bpy.ops.wm.open_mainfile(filepath=str(out/'SceneryScaling.blend'))
rows=json.loads((base/'batch1_report.json').read_text())['layouts']['Layout1']['rows']
def inside(x,y):return any(abs(x-r['x'])<128-1e-5 and abs(y+r['z'])<128-1e-5 for r in rows)
def bvh(objects):
    vs=[];fs=[]
    for o in objects:
        o.data.calc_loop_triangles();start=len(vs)
        vs.extend(o.matrix_world@v.co for v in o.data.vertices)
        fs.extend(tuple(start+i for i in t.vertices) for t in o.data.loop_triangles)
    return BVHTree.FromPolygons(vs,fs,all_triangles=True)
old=bvh([o for o in bpy.data.scenes['Layout1'].objects if o.name.startswith('Continuation_')])
new=bvh([o for o in bpy.data.scenes['SceneryScalingExport'].objects if o.name.startswith('EF_SCENERY_SURFACE_')])
samples=[]
for row in rows:
    source=next(o for o in bpy.data.scenes[row['id']].objects if o.name.startswith('Terrain_'))
    vs=[tuple(v.co) for v in source.data.vertices];matrix=assembly.transform(row)
    for side in range(4):
        for t in range(-124,128,4):
            x,y=[(t,-128),(128,t),(-t,128),(-128,-t)][side]
            p=matrix@Vector((x,y,shared.ec.surface(vs,4,x,y)))
            check=matrix@Vector((x+(1 if side==1 else -1 if side==3 else 0),y+(-1 if side==0 else 1 if side==2 else 0),0))
            if inside(check.x,check.y):continue
            hits=[tree.ray_cast(Vector((p.x,p.y,1000)),Vector((0,0,-1)))[0] for tree in (old,new)]
            if all(h is not None for h in hits):samples.append(dict(chunk=row['id'],side=side,t=t,old_error=abs(hits[0].z-p.z),new_error=abs(hits[1].z-p.z)))
result=dict(samples=len(samples),old_max=max(s['old_error'] for s in samples),new_max=max(s['new_error'] for s in samples),detail=samples)
(out/'scenery_edge_measurement.json').write_text(json.dumps(result,indent=2))
print('EDGE_MEASUREMENT',result['samples'],result['old_max'],result['new_max'])
