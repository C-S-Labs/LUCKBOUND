"""Batch 1 source-only authoring API. Run exclusively via tools/run_blender.py.

Approved helpers are read-only snapshots; assembly never enters height().
"""
import bpy, bmesh, math, random, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
sys.path.insert(0, str(OUT/'inputs'))
import edge_profile_contract as ec
import build_burned_plains as bp
BASE = Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend')
PALETTE = [(0.16,0.235,0.045),(0.29,0.235,0.075),(0.045,0.037,0.030)]

def init():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(BASE), link=False) as (a,b): b.materials=list(a.materials)
    for key,names in {'LEAF':['canopy_green','canopy_stressed','canopy_singed'], 'GRASS':['grass_green','grass_olive','grass_straw','grass_singed','grass_black_stubble','grass_burned_brown']}.items():
        setattr(bp,key,[bpy.data.materials['BP_'+n] for n in names])
    for key,name in {'WOOD':'field_timber','CHARWOOD':'charred_timber','STONE':'field_stone'}.items(): setattr(bp,key,bpy.data.materials['BP_'+name])
    bp.RNG=random.Random(51026)

def collection(name,scene):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c

def shader():
    m=bpy.data.materials.get('BATCH1_VERTEX_COLOUR')
    if m:return m
    m=bpy.data.materials.new('BATCH1_VERTEX_COLOUR');m.use_nodes=True
    n=m.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Col'
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.93
    m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color']);return m

def colours(obj,state=1):
    d=obj.data
    a=d.color_attributes.get('Col') or d.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
    for p in d.polygons:
        base=PALETTE[state]
        for i in p.loop_indices:
            v=d.vertices[d.loops[i].vertex_index].co
            t=.96+.07*math.sin(v.x/13+v.y/19)
            a.data[i].color=(*(k*t for k in base),1)
    d.color_attributes.active_color=a;d.materials.clear();d.materials.append(shader())

def closed(name,vertices,faces,c,mat=None,depth=5,flat_bottom=False):
    used=sorted({i for f in faces for i in f});mapping={a:i for i,a in enumerate(used)}
    v=[vertices[i] for i in used];fs=[tuple(mapping[i] for i in f) for f in faces];n=len(v)
    edges={}
    for f in fs:
        for a,b in zip(f,f[1:]+f[:1]): edges[tuple(sorted((a,b)))]=edges.get(tuple(sorted((a,b))),0)+1
    if name.startswith('Terrain_'):
        boundary=[(a,b) for (a,b),count in edges.items() if count==1]
        adjacency={}
        for a,b in boundary:adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
        order=[min(adjacency)];previous=None;current=order[0]
        while True:
            nxt=next(a for a in adjacency[current] if a!=previous)
            if nxt==order[0]:break
            order.append(nxt);previous,current=current,nxt
        bottom=min(z for x,y,z in v)-depth;idx={old:n+i for i,old in enumerate(order)}
        allv=v+[(v[i][0],v[i][1],bottom) for i in order]
        allf=fs+[tuple(reversed([idx[i] for i in order]))]+[(a,b,idx[b],idx[a]) for a,b in boundary]
        obj=bp.mesh(name,allv,allf,[mat] if mat else [],c)
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges),name
        bm.to_mesh(obj.data);bm.free();return obj
    allf=fs+[tuple(n+i for i in reversed(f)) for f in fs]+[(a,b,b+n,a+n) for (a,b),count in edges.items() if count==1]
    bottom=min(z for x,y,z in v)-depth
    obj=bp.mesh(name,v+[(x,y,bottom if flat_bottom else z-depth) for x,y,z in v],allf,[mat] if mat else [],c)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),name
    bm.to_mesh(obj.data);bm.free();return obj

class Context:
    def __init__(self,spec,scene):
        self.spec=spec;self.id=spec['id'];self.scene=scene
        self.c=collection(self.id,scene);self.collision=collection('COLLISION_'+self.id,scene)
        self.anchors=[];self.refuges=[];self.rng=random.Random(spec['seed'])
        self.zero=self.raw(0,0)
        bp.hill=self.height;bp.RNG=self.rng
    def raw(self,x,y):
        sp=self.spec['edges'];c=ec.corner_heights(sp);u=ec.smooth((x+128)/256);v=ec.smooth((y+128)/256)
        base=(1-u)*ec.edge(sp,'W',y)+u*ec.edge(sp,'E',y)+(1-v)*ec.edge(sp,'S',x)+v*ec.edge(sp,'N',x)-((1-u)*(1-v)*c['SW']+u*(1-v)*c['SE']+(1-u)*v*c['NW']+u*v*c['NE'])
        base+=self.spec['land'](x,y)*ec.smooth((128-abs(x))/40)*ec.smooth((128-abs(y))/40)
        # An eight-stud curved extrusion makes edge prisms convex and cookable;
        # the rest of the forty-stud authored band remains a natural transition.
        values=[]
        for side in sp:
            d={'S':y+128,'N':128-y,'W':x+128,'E':128-x}[side];s=x if side in ('N','S') else y
            e=ec.edge(sp,side,s)
            if d<=8+1e-9:return e
            if d<40:values.append((((40-d)/(d-8))**2,e))
        return (base+sum(w*z for w,z in values))/(1+sum(w for w,z in values))
    def height(self,x,y):return self.raw(x,y)-self.zero
    def ground(self,x,y):return ec.surface(self.vertices,4,x,y)
    def tree(self,x,y,h=27,style='field',yaw=0):
        bp.hill=self.ground;before=set(self.c.objects);bp.tree(x,y,h,self.c,forced=0)
        anchor={'type':'tree','x':x,'y':y,'height':h,'style':style,'override':None}
        self.anchors.append(anchor)
        for o in set(self.c.objects)-before:o['StateAnchor']=json.dumps(anchor);o['StateRole']='crown' if 'crown' in o.name else 'trunk'
    def wall(self,points):
        for x,y in points:bp.blob('field_wall',(x,y,self.ground(x,y)+1.25),(2.8,1.15,1.25),bp.STONE,self.c,2)
    def fence(self,points,damaged=False):bp.hill=self.ground;bp.fence(points,self.c,damaged)
    def rock(self,x,y,s=2):bp.blob('field_stone',(x,y,self.ground(x,y)+s*.4),(s,s*.8,s*.65),bp.STONE,self.c,2)
    def beam(self,name,a,b,r=.22):return bp.beam(name,a,b,r,bp.WOOD,self.c)
    def refuge(self,x,y,rx,ry,strength,reason):self.refuges.append(dict(x=x,y=y,rx=rx,ry=ry,strength=strength,reason=reason))
    def box(self,name,x,y,z,sx,sy,sz,mat=None):
        v=[(x+a*sx,y+b*sy,z+c*sz) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        return bp.mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],[mat or bp.WOOD],self.c)

def grid(ctx,step):
    n=256//step+1;v=[(x,y,ctx.height(x,y)) for y in range(-128,129,step) for x in range(-128,129,step)];fs=[]
    for j in range(n-1):
        for i in range(n-1):a=j*n+i;fs.extend(((a,a+1,a+n+1),(a,a+n+1,a+n)))
    return v,fs

def collision(ctx):
    sp=ctx.spec['edges']
    # Merge only exactly collinear canonical intervals. Studio's Hull cooker
    # simplifies long curved convex prisms, so source convexity alone is insufficient.
    for side,(kind,datum) in sp.items():
        vals=ec.samples(kind);groups=[];start=0;last=None
        for i in range(32):
            slope=vals[i+1]-vals[i]
            if last is not None and abs(slope-last)>1e-8:groups.append((start,i));start=i
            last=slope
        groups.append((start,32))
        for g,(a,b) in enumerate(groups):
            ss=list(range(-128+8*a,-128+8*b+1,8))
            # At shared corners both extrusion strips describe identical solids;
            # trim this strip if the horizontal side already owns that corner.
            if side in ('E','W'):
                if 'S' in sp:ss=[s for s in ss if s>=-120]
                if 'N' in sp:ss=[s for s in ss if s<=120]
            if len(ss)<2:continue
            vs=[]
            for d in (0,8):
                for s in ss:
                    x,y={'S':(s,-128+d),'N':(s,128-d),'W':(-128+d,s),'E':(128-d,s)}[side]
                    vs.append((x,y,ctx.height(x,y)))
            n=len(ss);fs=[(i,i+1,n+i+1,n+i) for i in range(n-1)]
            o=closed('EDGE_'+side+'_'+str(g),vs,fs,ctx.collision,flat_bottom=True)
            o['CollisionFidelity']='Hull';o['EdgeProfile']=kind
    # Sixteen closed interior tiles, clipped away from exact edge prisms.
    for ty in range(-128,128,64):
        for tx in range(-128,128,64):
            xs=list(range(tx,tx+65,8));ys=list(range(ty,ty+65,8))
            xs=[x for x in xs if not ('W'in sp and x==-128 or 'E'in sp and x==128)]
            ys=[y for y in ys if not ('S'in sp and y==-128 or 'N'in sp and y==128)]
            vs=[(x,y,ctx.height(x,y)) for y in ys for x in xs];n=len(xs);fs=[]
            for j in range(len(ys)-1):
                for i in range(n-1):a=j*n+i;fs.extend(((a,a+1,a+n+1),(a,a+n+1,a+n)))
            o=closed('WALK_'+str(tx)+'_'+str(ty),vs,fs,ctx.collision);o['CollisionFidelity']='PreciseConvexDecomposition'
    ctx.collision.hide_render=True;ctx.collision.hide_viewport=True

def build(spec,dress):
    scene=bpy.data.scenes.new(spec['id']);bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    ctx=Context(spec,scene);ctx.vertices,faces=grid(ctx,4)
    terrain=closed('Terrain_'+spec['id'],ctx.vertices,faces,ctx.c);colours(terrain)
    ctx.terrain=terrain;collision(ctx);dress(ctx)
    # Anchored meadow blades, split below the per-mesh triangle ceiling.
    guide=spec['guide'];vs=[];fs=[];batch=0
    for k in range(spec.get('grass_count',3500)):
        x,y=ctx.rng.uniform(-127,127),ctx.rng.uniform(-127,127)
        if min((x-a)**2+(y-b)**2 for a,b in guide)<40:continue
        if spec.get('grass_filter') and not spec['grass_filter'](x,y):continue
        z=ctx.ground(x,y)+.04
        for q in range(3):
            i=len(vs);a=ctx.rng.random()*math.tau;h=ctx.rng.uniform(.55,1.45)
            dx,dy=.17*math.cos(a),.17*math.sin(a)
            vs.extend(((x-dx,y-dy,z),(x+dx,y+dy,z),(x+.22,y+.12,z+h)));fs.append((i,i+1,i+2))
        if len(fs)>=6000:
            o=bp.mesh('Grass_'+str(batch),vs,fs,[],ctx.c);o['AppearanceRole']='grass';colours(o);vs=[];fs=[];batch+=1
    if fs:o=bp.mesh('Grass_'+str(batch),vs,fs,[],ctx.c);o['AppearanceRole']='grass';colours(o)
    # Every source is rebased once, sockets and anchors use identical origin.
    sockets=[]
    for side,(kind,datum) in spec['edges'].items():
        x,z,facing={'S':(0,128,180),'N':(0,-128,0),'W':(-128,0,270),'E':(128,0,90)}[side]
        sockets.append(dict(Id=side,Kind='BP_EDGE_'+kind,OffsetX=x,OffsetY=datum-ctx.zero,OffsetZ=z,Facing=facing,Width=24))
    terrain['SocketProfiles']=json.dumps(sockets);terrain['FootprintStuds']=[256,256];terrain['AuthoringTransitionDepth']=40
    terrain['AppearanceRole']='terrain';terrain['FrozenSource']=True
    guide3=[(x,y,ctx.ground(x,y)+.055) for x,y in guide]
    meta=dict(id=spec['id'],title=spec['title'],purpose=spec['purpose'],sockets=sockets,guide=guide3,refuges=ctx.refuges,anchors=ctx.anchors,landmark=spec.get('landmark'),collision_parts=len(ctx.collision.objects),objects=len(ctx.c.objects),triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in ctx.c.objects if o.type=='MESH'))
    error=max(abs(ctx.height(*( {'S':(s,-128),'N':(s,128),'W':(-128,s),'E':(128,s)}[side]))-(datum+ec.profile(kind,s)-ctx.zero)) for side,(kind,datum) in spec['edges'].items() for s in range(-128,129,2))
    assert error<.01;meta['edge_error']=error
    meta['geometry_sha256']=hashlib.sha256(json.dumps([tuple(v.co) for v in terrain.data.vertices]).encode()).hexdigest()
    scene['Metadata']=json.dumps(meta);return ctx,meta

def straight(amplitude=6):return [(amplitude*math.sin(math.pi*t/64)**3,-128+4*t) for t in range(65)]
def turn(side='E'):
    return [((1 if side=='E' else -1)*(128-128*math.cos(t*math.pi/128)),-128+128*math.sin(t*math.pi/128)) for t in range(65)]

def light_scene(scene):
    scene.world=bpy.data.worlds.new(scene.name+'_World');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.31,.37,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    d=bpy.data.lights.new('Daylight','SUN');d.energy=2.2;d.angle=.22;o=bpy.data.objects.new('Daylight',d);scene.collection.objects.link(o);o.rotation_euler=(.5,-.35,-.4)
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1200;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    # Required five-stud human scale marker, kept outside beauty frames.
    c=collection('Scale_Reference',scene);obj=bp.mesh('Five_Stud_Human',[(400,0,0),(400,0,5),(401,0,0)],[(0,1,2)],[],c);c.hide_render=True

def render(scene,path,eye=(285,-355,270),target=(0,0,4),ortho=None):
    bpy.context.window.scene=scene
    d=bpy.data.cameras.new('ReviewCamera');d.clip_end=10000;o=bpy.data.objects.new('ReviewCamera',d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=40
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    scene.camera=o;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def finish_lane(lane,rows,contexts):
    dest=OUT/lane;dest.mkdir(parents=True,exist_ok=True)
    for ctx in contexts:
        light_scene(ctx.scene);render(ctx.scene,dest/(ctx.id+'_overview.png'))
        x,y,z=ctx.spec['guide'][10][0],ctx.spec['guide'][10][1],0
        t=ctx.spec['guide'][27];render(ctx.scene,dest/(ctx.id+'_eye.png'),(x,y,ctx.ground(x,y)+5),(t[0],t[1],ctx.ground(*t)+4))
    (dest/'manifest.json').write_text(json.dumps(rows,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/('BurnedPlains_'+lane+'.blend')))
