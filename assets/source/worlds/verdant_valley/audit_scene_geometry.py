"""Read-only contact and solid-intersection review of the owner's current chunk meshes."""
import bpy
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector

spec = importlib.util.spec_from_file_location('vv_contact_checks',Path(__file__).parents[1]/'_framework'/'geometry_checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
checks.TOUCH = .15


def main():
    out = Path(sys.argv[sys.argv.index('--')+1])
    out.mkdir(parents=True,exist_ok=True)
    solid = set(bpy.data.collections['VV_PROPS_SOLID'].objects)
    nonsolid = set(bpy.data.collections['VV_PROPS_NONSOLID'].objects)
    chunks = sorted(bpy.data.collections['VV_STRUCTURE'].objects,key=lambda o:o.name)
    report = {'reference':bpy.data.filepath,'contact_tolerance':.15,'chunks':[]}
    for chunk in chunks:
        props = [o for o in solid|nonsolid if o.name.startswith(chunk.name+'__')]
        shells = []
        origin = chunk.location
        for obj in [chunk]+sorted(props,key=lambda o:o.name):
            mesh=obj.data
            p=SimpleNamespace(verts=[obj.matrix_world@v.co-origin for v in mesh.vertices],
                              faces=[tuple(f.vertices) for f in mesh.polygons],
                              ftag=[obj.name]*len(mesh.polygons))
            for s in checks._shells(p):
                s['solid']=obj in solid
                s['ground']=obj==chunk
                shells.append(s)
        parent=list(range(len(shells)))
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        clips=[]
        order=sorted(range(len(shells)),key=lambda i:shells[i]['min'][0])
        for ii,i in enumerate(order):
            a=shells[i]
            for j in order[ii+1:]:
                b=shells[j]
                if b['min'][0]>a['max'][0]+checks.TOUCH:break
                if not checks._near(a,b,checks.TOUCH):continue
                touch,cross=checks._touching(a,b)
                if not touch:continue
                parent[root(i)]=root(j)
                if not cross or a['tag']==b['tag']:continue
                if not(a['solid'] and b['solid']):continue
                steep=sum(abs(checks._face_normal(a['pts'],a['tri'][fa]).z)<.9
                          and abs(checks._face_normal(b['pts'],b['tri'][fb]).z)<.9 for fa,fb in cross)
                if not steep:continue
                lo=[max(a['min'][k],b['min'][k]) for k in range(3)]
                hi=[min(a['max'][k],b['max'][k]) for k in range(3)]
                clips.append({'objects':[a['tag'],b['tag']],'crossing_faces':steep,
                              'center':[round((x+y)/2,3) for x,y in zip(lo,hi)],
                              'bounds_overlap':[round(y-x,3) for x,y in zip(lo,hi)]})
        ground_roots={root(i) for i,s in enumerate(shells) if s['ground']}
        groups=defaultdict(list)
        for i,s in enumerate(shells):
            if root(i) not in ground_roots:groups[root(i)].append(i)
        floats=[]
        for members in groups.values():
            low=[min(shells[i]['min'][k] for i in members) for k in range(3)]
            high=[max(shells[i]['max'][k] for i in members) for k in range(3)]
            tags=sorted(set(shells[i]['tag'] for i in members))
            nearest=1e9;rest=None
            for i in members:
                a=shells[i]
                for j,b in enumerate(shells):
                    if root(j)==root(i) or not checks._near(a,b,3):continue
                    for first,second in ((a,b),(b,a)):
                        for point in checks._samples(first):
                            hit=checks._bvh(second).find_nearest(point,nearest)
                            if hit[0] is not None and hit[3]<nearest:nearest=hit[3];rest=b['tag']
            floats.append({'objects':tags,'shells':len(members),'solid':any(shells[i]['solid'] for i in members),
                           'center':[round((x+y)/2,3) for x,y in zip(low,high)],
                           'size':[round(y-x,3) for x,y in zip(low,high)],
                           'nearest_surface_gap':round(nearest,3) if nearest<1e9 else None,'nearest_object':rest})
        row={'name':chunk.name,'origin':list(origin),'solid_objects':sum(o in solid for o in props),
             'nonsolid_objects':sum(o in nonsolid for o in props),'shells':len(shells),
             'floating_candidates':floats,'solid_clipping_candidates':clips}
        report['chunks'].append(row)
        (out/'geometry_candidates.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(chunk.name,'shells',len(shells),'floating groups',len(floats),'solid crossings',len(clips),flush=True)
    print('AUDIT_COMPLETE',flush=True)


if __name__=='__main__':main()
