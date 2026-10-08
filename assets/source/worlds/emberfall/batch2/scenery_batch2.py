"""Apply the accepted baked-clump scenery recipe to the bounded Batch2 review."""
import bpy
import json
import math
import random
import sys
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parent/'batch1'))
import batch1_shared as s
import assemble_batch1 as a
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsCombinedReview.blend'))
    report=json.loads((OUT/'batch2_report.json').read_text());meta=report['kit']
    label='Combined2';layout_report=report['layouts'][label];rows=layout_report['rows']
    scene=bpy.data.scenes[label];bpy.context.window.scene=scene;bpy.context.view_layer.update()
    points=[];refuges=[];sources=[]
    for index,row in enumerate(rows):
        m=a.transform(row);guide=meta[row['id']]['guide']
        reverse=row['exit']==meta[row['id']]['sockets'][0]['Id'] if index<len(rows)-1 else (Vector(guide[0][:2])-(m.inverted()@Vector(points[-1][:3])).to_2d()).length>100
        if reverse:guide=guide[::-1]
        for x,y,z in guide:
            w=m@Vector((x,y,z));dist=points[-1][3]+math.hypot(w.x-points[-1][0],w.y-points[-1][1]) if points else 0
            if points and math.hypot(w.x-points[-1][0],w.y-points[-1][1])<1e-5:continue
            points.append((w.x,w.y,w.z,dist))
        for refuge in meta[row['id']]['refuges']:refuges.append((m.inverted(),refuge))
        terrain=next(o for o in bpy.data.scenes[row['id']].objects if o.name.startswith('Terrain_'))
        sources.append((row,m.inverted(),[tuple(v.co) for v in terrain.data.vertices]))
    bounds=(min(r['x'] for r in rows)-128,min(-r['z'] for r in rows)-128,max(r['x'] for r in rows)+128,max(-r['z'] for r in rows)+128)
    field=a.Field([(x,y,d) for x,y,z,d in points],bounds,refuges);field.thresholds=layout_report['thresholds']
    def inside(x,y):return any(abs(x-r['x'])<128-1e-6 and abs(y+r['z'])<128-1e-6 for r in rows)
    def distance(x,y):return min(math.hypot(max(0,abs(x-r['x'])-128),max(0,abs(y+r['z'])-128)) for r in rows)
    cache={}
    def height(x,y):
        key=(x,y)
        if key in cache:return cache[key]
        values=[]
        for r,inv,vs in sources:
            p=inv@Vector((x,y,0));xx=max(-128,min(128,p.x));yy=max(-128,min(128,p.y));d=math.hypot(p.x-xx,p.y-yy)
            h=s.ec.surface(vs,4,xx,yy)+r['y']
            if d<1e-5:cache[key]=h;return h
            values.append((d,h))
        weights=[(d+1)**-4 for d,h in values]
        value=sum(w*h for w,(d,h) in zip(weights,values))/sum(weights)
        value+=min(1,min(values)[0]/80)*(10*math.sin(x/170)*math.cos(y/150)+4*math.sin(y/73))
        cache[key]=value;return value
    objects=[]
    def mesh(name,vs,fs,role):
        obj=s.bp.mesh(name,vs,fs,[],scene.collection);obj['AppearanceRole']=role
        obj['NonPlayable']=True;obj['CanCollide']=False
        a.colour_object(obj,field);objects.append(obj);return obj
    # Execute the frozen accepted strategy, not a new scenery architecture.
    recipe=(ROOT/'tools/studio/emberfall_walkthrough/build_scenery_scaling.py').read_text()
    recipe=recipe[recipe.index('# Existing coarse surfaces'):recipe.index("bpy.ops.object.select_all(action='DESELECT')",recipe.index('# Existing coarse surfaces'))]
    recipe=recipe.replace("layout=bpy.data.scenes['Layout1']",'layout=scene')
    namespace=dict(bpy=bpy,math=math,random=random,Vector=Vector,scene=scene,rows=rows,sources=sources,inside=inside,distance=distance,height=height,field=field,mesh=mesh)
    exec(compile(recipe,'accepted_scenery_recipe','exec'),namespace)
    for old in namespace['original']:old.hide_render=True;old.hide_viewport=True
    counts=dict(meshes=len(objects),triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),grass_triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.get('AppearanceRole')=='grass'),source_terrain_edits=0,editable_meshes=0,edge_step=4,underlap_drop=.04)
    layout_report['scenery']=counts
    report['route']=[[x,z,-y,d] for x,y,z,d in points]
    (OUT/'batch2_report.json').write_text(json.dumps(report,indent=2))
    for name,index,lift in [('scenery_eye',len(points)//2,5),('scenery_elevated',len(points)*2//3,14)]:
        p=points[index];target=points[min(len(points)-1,index+18)]
        s.render(scene,OUT/label/(name+'.png'),(p[0],p[1],p[2]+lift),target[:3])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsProductionReview.blend'))
    print('ACCEPTED_SCENERY_APPLIED',json.dumps(counts))


if __name__=='__main__':main()
