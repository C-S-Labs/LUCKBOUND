"""Scenery-only export: frozen Batch1 stays read-only. Run via run_blender.py."""
import bpy, sys, json, math, random, hashlib
from pathlib import Path
from mathutils import Vector

BASE = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_SceneryScaling')
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(BASE))
import batch1_shared as s
import assemble_batch1 as a

bpy.ops.wm.open_mainfile(filepath=str(BASE/'BurnedPlainsBatch1.blend'))
report = json.loads((BASE/'batch1_report.json').read_text())
rows = report['layouts']['Layout1']['rows']
meta = report['kit']
snapshot = json.loads(Path('E:/BlenderAIProjects/Runtime/Emberfall_Walkthrough/walkthrough_data.json').read_text())
sources = []
hashes = {}
for row in rows:
    terrain = next(o for o in bpy.data.scenes[row['id']].objects if o.name.startswith('Terrain_'))
    vs = [tuple(v.co) for v in terrain.data.vertices]
    hashes[row['id']] = hashlib.sha256(json.dumps(vs).encode()).hexdigest()
    assert hashes[row['id']] == meta[row['id']]['geometry_sha256']
    sources.append((row, a.transform(row).inverted(), vs))
f = snapshot['appearance']
class Field:
    def state(self,x,y):
        px=max(0,min(f['nx']-1,(x-f['xmin'])/8));py=max(0,min(f['ny']-1,(y-f['ymin'])/8))
        i=min(f['nx']-2,int(px));j=min(f['ny']-2,int(py));u=px-i;v=py-j
        def g(i,j):return f['grid'][j*f['nx']+i]
        value=((g(i,j)*(1-u)+g(i+1,j)*u)*(1-v)+(g(i,j+1)*(1-u)+g(i+1,j+1)*u)*v)*f['length']+55*math.sin(x/64+.6)+24*math.sin(y/27)
        for r in f['refuges']:
            m=r['inverse'];lx=m[0][0]*x+m[0][1]*y+m[0][3];ly=m[1][0]*x+m[1][1]*y+m[1][3]
            value-=120*r['strength']*math.exp(-2*(((lx-r['x'])/r['rx'])**2+((ly-r['y'])/r['ry'])**2))
        return 0 if value<f['thresholds'][0] else 1 if value<f['thresholds'][1] else 2
field=Field()
def inside(x,y):return any(abs(x-r['x'])<128-1e-6 and abs(y+r['z'])<128-1e-6 for r in rows)
def distance(x,y):return min(math.hypot(max(0,abs(x-r['x'])-128),max(0,abs(y+r['z'])-128)) for r in rows)
def height(x,y):
    heights=[]
    for r,inv,vs in sources:
        p=inv@Vector((x,y,0));xx=max(-128,min(128,p.x));yy=max(-128,min(128,p.y));d=math.hypot(p.x-xx,p.y-yy)
        h=s.ec.surface(vs,4,xx,yy)+r['y']
        if d<1e-5:return h
        heights.append((d,h))
    weights=[(d+1)**-4 for d,h in heights];z=sum(w*h for w,(d,h) in zip(weights,heights))/sum(weights)
    return z+min(1,min(heights)[0]/80)*(10*math.sin(x/170)*math.cos(y/150)+4*math.sin(y/73))

scene=bpy.data.scenes.new('SceneryScalingExport');bpy.context.window.scene=scene
scene.unit_settings.system='NONE';scene.unit_settings.scale_length=1
records=[];objects=[]
def mesh(name,vs,fs,role):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o['AppearanceRole']=role
    a.colour_object(o,field)
    coords=[o.matrix_world@Vector(q) for q in o.bound_box]
    lo=[min(q[k] for q in coords) for k in range(3)];hi=[max(q[k] for q in coords) for k in range(3)]
    c=[(l+h)/2 for l,h in zip(lo,hi)];sz=[h-l for l,h in zip(lo,hi)]
    records.append(dict(key=name,role=role,center=[c[0],c[2],-c[1]],size=[sz[0],sz[2],sz[1]],vertices=len(vs),triangles=len(fs)))
    objects.append(o)
    return o

if '--trees-only' in sys.argv:
    # Source object transforms must be evaluated in their owning scene. Without
    # this, cached canopy matrices can be stale after a headless .blend load.
    bpy.context.window.scene=bpy.data.scenes['Layout1'];bpy.context.view_layer.update()
    vs=[];faces=[];colors=[];batch=0
    def flush():
        global vs,faces,colors,batch
        o=mesh('EF_SCENERY_TREES_'+str(batch),vs,faces,'sceneryProps')
        attr=o.data.color_attributes['Col']
        for k,color in enumerate(colors):attr.data[k].color=color
        vs=[];faces=[];colors=[];batch+=1
    for o in bpy.data.scenes['Layout1'].objects:
        if o.type!='MESH' or not o.get('NonPlayable') or o.name.startswith('Continuation_'):continue
        o.data.calc_loop_triangles();attr=o.data.color_attributes.get('Col')
        for tri in o.data.loop_triangles:
            if len(faces)>=8000:flush()
            start=len(vs)
            for vi,li in zip(tri.vertices,tri.loops):
                vs.append(tuple(o.matrix_world@o.data.vertices[vi].co))
                if attr:color=tuple(attr.data[li].color)
                else:
                    mat=o.data.materials[o.data.polygons[tri.polygon_index].material_index]
                    node=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
                    color=tuple(node.inputs['Base Color'].default_value) if node else tuple(mat.diffuse_color)
                colors.append(color)
            faces.append((start,start+1,start+2))
    if faces:flush()
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/'EF_SCENERY_TREES.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',colors_type='SRGB',add_leaf_bones=False,bake_anim=False)
    (OUT/'trees_manifest.json').write_text(json.dumps(records,indent=2))
    print('SCENERY_TREES',len(records),sum(r['triangles'] for r in records))
    sys.exit(0)

# Existing coarse surfaces are replaced only on the scenery side. At playable
# borders sample the frozen 4-stud edge, and continue one stud beneath it.
layout=bpy.data.scenes['Layout1']
original=[o for o in layout.objects if o.name.startswith('Continuation_')]
area=0;edge_delta=0;states=[0,0,0];tiers=[0,0]
rng=random.Random(6100626)
for tile,old in enumerate(original):
    ov=[old.matrix_world@v.co for v in old.data.vertices]
    terrainvs=[];terrainfs=[];grassvs=[];grassfs=[]
    def add_grass(x,y,z,d):
        state=field.state(x,y);states[state]+=1
        # Match authored near-boundary blade frequency, fade smoothly to half
        # density beyond 128 studs. Keep real silhouette geometry throughout.
        angle=rng.random()*math.tau;w=.17;h=rng.uniform(.55,1.45)
        b=len(grassvs);dx=w*math.cos(angle);dy=w*math.sin(angle)
        grassvs.extend(((x-dx,y-dy,z+.04),(x+dx,y+dy,z+.04),(x+.22,y+.12,z+h+.04)))
        grassfs.append((b,b+1,b+2));tiers[0 if d<128 else 1]+=1
    for j in range(16):
        for i in range(16):
            n=j*17+i;x=ov[n].x;y=ov[n].y
            if inside(x+8,y+8):continue
            area+=256
            # Four-stud boundary tessellation; coarse interior gets a fan with
            # the same perimeter samples so no T junction can open a crack.
            near=distance(x+8,y+8)<24
            if near:
                base=len(terrainvs)
                for yy in range(5):
                    for xx in range(5):terrainvs.append((x+xx*4,y+yy*4,height(x+xx*4,y+yy*4)))
                for yy in range(4):
                    for xx in range(4):
                        b=base+yy*5+xx;terrainfs.extend(((b,b+1,b+6),(b,b+6,b+5)))
            else:
                perimeter=[]
                for side,(nx,ny) in enumerate(((x+8,y-8),(x+24,y+8),(x+8,y+24),(x-8,y+8))):
                    step=4 if distance(nx,ny)<24 else 16
                    for k in range(0,16,step):
                        perimeter.append([(x+k,y),(x+16,y+k),(x+16-k,y+16),(x,y+16-k)][side])
                count=len(perimeter);base=len(terrainvs)
                terrainvs.extend((px,py,height(px,py)) for px,py in perimeter);terrainvs.append((x+8,y+8,height(x+8,y+8)))
                terrainfs.extend((base+k,base+(k+1)%count,base+count) for k in range(count))
            # Match the accepted three-blade clumps, not evenly scattered blades:
            # equal triangle density alone made the backdrop read too dense.
            for sy in range(6):
                for sx in range(6):
                    gx=x+(sx+rng.random())*16/6;gy=y+(sy+rng.random())*16/6;d=distance(gx,gy)
                    probability=.91/3*(1-.5*max(0,min(1,(d-96)/160)))
                    if rng.random()<probability:
                        # Terrain's actual triangles, rather than analytic height,
                        # seat the vegetation. Find through a tile-local BVH below.
                        for blade in range(3):add_grass(gx,gy,0,d)
    terrain=mesh('EF_SCENERY_SURFACE_'+str(tile),terrainvs,terrainfs,'terrain')
    from mathutils.bvhtree import BVHTree
    bvh=BVHTree.FromPolygons([Vector(v) for v in terrainvs],terrainfs,all_triangles=True)
    for start in range(0,len(grassvs),3):
        center=(Vector(grassvs[start])+Vector(grassvs[start+1]))/2
        hit=bvh.ray_cast(Vector((center.x,center.y,1000)),Vector((0,0,-1)))
        assert hit[0] is not None
        for k in range(3):
            q=grassvs[start+k];grassvs[start+k]=(q[0],q[1],q[2]+hit[0].z)
    # Conservative per-import batching keeps each upload below 8500 triangles.
    for batch,start in enumerate(range(0,len(grassfs),8000)):
        faces=grassfs[start:start+8000];vv=grassvs[start*3:(start+len(faces))*3]
        mesh('EF_SCENERY_COVER_'+str(tile)+'_'+str(batch),vv,[tuple(v-start*3 for v in face) for face in faces],'grass')

# Underside lip only at exposed playable edges. A lowered inward overlap closes
# independent import rounding without changing a single playable vertex.
lipvs=[];lipfs=[]
for r,inv,vs in sources:
    m=inv.inverted()
    for side in range(4):
        for transverse in range(-128,128,4):
            def local(t,out):return [(t,-128-out),(128+out,t),(-t,128+out),(-128-out,-t)][side]
            mid=m@Vector((*local(transverse+2,.5),0))
            if inside(mid.x,mid.y):continue
            b=len(lipvs)
            for t,out in ((transverse,-1),(transverse+4,-1),(transverse+4,1),(transverse,1)):
                p=m@Vector((*local(t,out),0));lipvs.append((p.x,p.y,height(p.x,p.y)-.04))
            lipfs.extend(((b,b+1,b+2),(b,b+2,b+3)))
mesh('EF_SCENERY_EDGE_UNDERLAP',lipvs,lipfs,'terrain')

bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'EF_SCENERY_CONTINUATION.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,mesh_smooth_type='FACE',colors_type='SRGB',use_custom_props=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SceneryScaling.blend'))
result=dict(records=records,area_studs2=area,grass_states=states,grass_tiers=tiers,source_hashes=hashes,source_unchanged=True,underlap_width=2,underlap_drop=.04,terrain_edge_step=4)
(OUT/'scenery_manifest.json').write_text(json.dumps(result,indent=2))
print('SCENERY_EXPORT',json.dumps({k:v for k,v in result.items() if k!='records' and k!='source_hashes'}))
