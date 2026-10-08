"""Integrate frozen Batch 1 sources; no terrain/collision edits after authoring."""
import sys,json,math,hashlib,random,subprocess,itertools
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import batch1_shared as s
OUT=s.OUT
ROOT=Path('C:/Users/jhpel/branch/emberfall-batch1')
LANES=('countryside','elevations','fields')
REPORT={'production_ids_replaced':False,'runtime_modified':False,'terrain_edits_after_freeze':0,'collision_edits_after_freeze':0,'layouts':{}}

def load_sources():
    sources={};manifest={}
    for lane in LANES:
        rows=json.loads((OUT/lane/'manifest.json').read_text())
        with bpy.data.libraries.load(str(OUT/lane/('BurnedPlains_'+lane+'.blend')),link=False) as (a,b):b.scenes=[r['id'] for r in rows]
        for row,scene in zip(rows,b.scenes):
            sources[row['id']]=scene;manifest[row['id']]=row
    return sources,manifest

def layouts(meta):
    defs={k:dict(Id=k,Role='PATH',SizeX=256,SizeZ=256,Sockets=v['sockets']) for k,v in meta.items()}
    def luau(v):
        if isinstance(v,dict):return '{'+','.join(k+'='+luau(x) for k,x in v.items())+'}'
        if isinstance(v,list):return '{'+','.join(luau(x) for x in v)+'}'
        return json.dumps(v)
    source=(ROOT/'src/shared/Util/ChunkCore.luau').read_text().replace('local WeightedRandom = require(script.Parent.WeightedRandom)','local WeightedRandom = {}')
    code='local Core=(function()\n'+source+'\nend)()\nlocal defs='+luau(defs)+'''
local names={}
for k in defs do if k~="EF_ENTRY_WINDWARD_MEADOW" then table.insert(names,k) end end
table.sort(names)
local found={}
local function attempt(order,yaw)
 local placed={{ChunkId=order[1],X=0,Y=0,Z=0,Yaw=yaw,Index=1}}
 local exits={};local arrived=nil
 for i=2,#order do
  local before=defs[order[i-1]]
  local departure=before.Sockets[2]
  if arrived and departure.Id==arrived.Id then departure=before.Sockets[1] end
  local open=Core.worldSocket(placed[i-1],before,departure)
  local p,a=Core.placeAgainst(defs[order[i]],open,i)
  if not p then return end
  for j,q in placed do if Core.overlaps(q,defs[order[j]],p,defs[order[i]]) then return end end
  table.insert(exits,departure.Id);table.insert(placed,p);arrived=a
 end
 local rows={}
 for i,p in placed do table.insert(rows,string.format('{"id":"%s","x":%.12f,"y":%.12f,"z":%.12f,"yaw":%d,"exit":"%s"}',order[i],p.X,p.Y,p.Z,p.Yaw,exits[i] or "END")) end
 table.insert(found,'['..table.concat(rows,",")..']')
end
local desired={
 {"EF_ENTRY_WINDWARD_MEADOW","EF_DRAINAGE_CROSSING","EF_RIDGE_ASCENT","EF_ORCHARD_BEND","EF_SWITCHBACK_BANK","EF_WAYMARK_TERRACE","EF_FENCELINE_RISE","EF_BURN_FRONT_VERGE","EF_OPEN_FIELD_CLEARING"},
 {"EF_ENTRY_WINDWARD_MEADOW","EF_ORCHARD_BEND","EF_OPEN_FIELD_CLEARING","EF_DRAINAGE_CROSSING","EF_SWITCHBACK_BANK","EF_FENCELINE_RISE","EF_WAYMARK_TERRACE","EF_BURN_FRONT_VERGE","EF_RIDGE_ASCENT"},
 {"EF_ENTRY_WINDWARD_MEADOW","EF_RIDGE_ASCENT","EF_BURN_FRONT_VERGE","EF_FENCELINE_RISE","EF_WAYMARK_TERRACE","EF_SWITCHBACK_BANK","EF_ORCHARD_BEND","EF_DRAINAGE_CROSSING","EF_OPEN_FIELD_CLEARING"}
}
for i,order in desired do attempt(order,({0,90,270})[i]) end
if #found<3 then
 local function permute(a,n)
  if #found>=3 then return end
  if n>#a then local order={"EF_ENTRY_WINDWARD_MEADOW"};for _,k in a do table.insert(order,k) end;attempt(order,90*#found);return end
  for i=n,#a do a[n],a[i]=a[i],a[n];permute(a,n+1);a[n],a[i]=a[i],a[n] end
 end
 permute(names,1)
end
assert(#found>=3,"Three valid full-kit routes required")
print('['..table.concat(found,",")..']')
'''
    f=OUT/'actual_chunkcore_layouts.luau';f.write_text(code)
    p=subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe',str(f)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    data=json.loads(p.stdout);(OUT/'layouts.json').write_text(json.dumps(data,indent=2));return data[:3]

class Field:
    def __init__(self,points,bounds,refuges):
        self.length=points[-1][2];self.step=8;self.xmin=bounds[0]-128;self.ymin=bounds[1]-128
        self.nx=int((bounds[2]-self.xmin+128)/8)+1;self.ny=int((bounds[3]-self.ymin+128)/8)+1
        xx,yy=np.meshgrid(self.xmin+np.arange(self.nx)*8,self.ymin+np.arange(self.ny)*8)
        dist=np.full(xx.shape,np.inf);depth=np.zeros(xx.shape);sums=np.zeros(xx.shape);counts=np.zeros(xx.shape)
        for x,y,d in points:
            dd=(xx-x)**2+(yy-y)**2;n=dd<dist;depth[n]=d/self.length;dist[n]=dd[n]
            ix=round((x-self.xmin)/8);iy=round((y-self.ymin)/8);sums[iy,ix]+=d/self.length;counts[iy,ix]+=1
        pins=counts>0;fixed=np.divide(sums,counts,out=np.zeros_like(sums),where=pins);depth[pins]=fixed[pins]
        parity=np.indices(depth.shape).sum(axis=0)%2
        for iteration in range(2400):
            before=depth.copy()
            for colour in (0,1):
                avg=(depth[:-2,1:-1]+depth[2:,1:-1]+depth[1:-1,:-2]+depth[1:-1,2:])/4
                block=depth[1:-1,1:-1];mask=(parity[1:-1,1:-1]==colour)&~pins[1:-1,1:-1];block[mask]+=1.75*(avg[mask]-block[mask])
                depth[0]=depth[1];depth[-1]=depth[-2];depth[:,0]=depth[:,1];depth[:,-1]=depth[:,-2];depth[pins]=fixed[pins]
            if np.max(np.abs(depth-before))<2e-6:break
        self.grid=depth;self.refuges=refuges;self.stats={'iterations':iteration+1,'bytes':depth.nbytes,'length':self.length}
    def progress(self,x,y):
        px=max(0,min(self.nx-1,(x-self.xmin)/8));py=max(0,min(self.ny-1,(y-self.ymin)/8));i=min(self.nx-2,int(px));j=min(self.ny-2,int(py));a=px-i;b=py-j;g=self.grid
        return float((g[j,i]*(1-a)+g[j,i+1]*a)*(1-b)+(g[j+1,i]*(1-a)+g[j+1,i+1]*a)*b)
    def raw(self,x,y):
        value=self.progress(x,y)*self.length+55*math.sin(x/64+.6)+24*math.sin(y/27)
        for inverse,r in self.refuges:
            p=inverse@Vector((x,y,0));d=((p.x-r['x'])/r['rx'])**2+((p.y-r['y'])/r['ry'])**2;value-=120*r['strength']*math.exp(-2*d)
        return value
    def state(self,x,y):v=self.raw(x,y);return 0 if v<self.thresholds[0] else 1 if v<self.thresholds[1] else 2

def transform(row):return Matrix.Translation((row['x'],-row['z'],row['y']))@Matrix.Rotation(-math.radians(row['yaw']),4,'Z')

def colour_object(obj,field):
    d=obj.data;a=d.color_attributes.get('Col') or d.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
    for v in d.vertices:
        w=obj.matrix_world@v.co
    cache={}
    for p in d.polygons:
        for i in p.loop_indices:
            vi=d.loops[i].vertex_index
            if vi not in cache:
                w=obj.matrix_world@d.vertices[vi].co;state=field.state(w.x,w.y);base=s.PALETTE[state]
                if obj.get('AppearanceRole')=='grass':base=[(.21,.34,.055),(.39,.32,.11),(.018,.016,.012)][state]
                t=.95+.08*math.sin(w.x/13+w.y/19);cache[vi]=(*(k*t for k in base),1)
            a.data[i].color=cache[vi]
    d.materials.clear();d.materials.append(s.shader());d.color_attributes.active_color=a

def road(scene,points,field,height,terrain_arrays):
    c=s.collection('ASSEMBLY_ROAD_AUTHORED_GUIDES',scene);vs=[];fs=[];uvdist=[]
    for i,(x,y,z,dist) in enumerate(points):
        a=points[max(0,i-1)];b=points[min(len(points)-1,i+1)];dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
        width=4.2+(0 if i in (0,len(points)-1) else .35*math.sin(dist/19))
        for fraction in (-1,-.5,0,.5,1):
            px=x+nx*width*fraction;py=y+ny*width*fraction;vs.append((px,py,height(px,py)+.07));uvdist.append(((fraction+1)/2,dist/16))
        if i:
            for q in range(4):
                a=5*i-5+q;b=5*i+q;fs.extend(((a,b,b+1),(a,b+1,a+1)))
    # Clip authored road strips against the frozen visual triangles. The road
    # follows exactly the same planes, avoiding hill/overlay intersections.
    strips=[]
    for i in range(1,len(points)):
        poly=[vs[(i-1)*5],vs[i*5],vs[i*5+4],vs[(i-1)*5+4]]
        if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))<0:poly.reverse()
        strips.append((poly,points[i-1],points[i]))
    clippedv=[];clippedf=[];clippeduv=[]
    for r,m,inv,terrain in terrain_arrays:
        for quad,a,b in strips:
            local=[inv@Vector(q) for q in quad];xmin=min(p.x for p in local);xmax=max(p.x for p in local);ymin=min(p.y for p in local);ymax=max(p.y for p in local)
            if xmax<-128 or xmin>128 or ymax<-128 or ymin>128:continue
            i0=max(0,int((xmin+128)//4));i1=min(63,int((xmax+128)//4));j0=max(0,int((ymin+128)//4));j1=min(63,int((ymax+128)//4))
            for j in range(j0,j1+1):
                for i in range(i0,i1+1):
                    n=j*65+i
                    for indices in ((n,n+1,n+66),(n,n+66,n+65)):
                        poly=[tuple(m@Vector(terrain[k])) for k in indices]
                        for ca,cb in zip(quad,quad[1:]+quad[:1]):
                            if not poly:break
                            result=[]
                            def cross(p):return (cb[0]-ca[0])*(p[1]-ca[1])-(cb[1]-ca[1])*(p[0]-ca[0])
                            for p,q in zip(poly,poly[1:]+poly[:1]):
                                d,e=cross(p),cross(q)
                                if d>=-1e-8:result.append(p)
                                if (d>=0)!=(e>=0):
                                    t=d/(d-e);result.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(3)))
                            poly=result
                        if len(poly)<3:continue
                        start=len(clippedv)
                        dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
                        for x,y,z in poly:
                            t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den));dist=a[3]+t*(b[3]-a[3]);across=((x-a[0])*(-dy)+(y-a[1])*dx)/math.sqrt(den)
                            clippedv.append((x,y,z+.015));clippeduv.append((.5+across/8.4,dist/16))
                        for k in range(1,len(poly)-1):clippedf.append((start,start+k,start+k+1))
    vs,fs,uvdist=clippedv,clippedf,clippeduv
    obj=s.bp.mesh('CONTINUOUS_ROAD_REVIEW',vs,fs,[],c);obj['ReviewOnly']=True
    mat=s.bp.material('Batch1_track',(.18,.12,.06));obj.data.materials.append(mat)
    layer=obj.data.uv_layers.new(name='DistanceAlongRoute')
    for p in obj.data.polygons:
        for l in p.loop_indices:layer.data[l].uv=uvdist[obj.data.loops[l].vertex_index]
    return obj

def assemble(label,rows,sources,meta):
    scene=bpy.data.scenes.new(label);bpy.context.window.scene=scene;s.light_scene(scene)
    mats=[transform(r) for r in rows];points=[];refuges=[];placed=[]
    for i,(r,m) in enumerate(zip(rows,mats)):
        guide=meta[r['id']]['guide'];rev=(r['exit']==meta[r['id']]['sockets'][0]['Id']) if i<len(rows)-1 else (np.linalg.norm(np.array(guide[0][:2])-np.array((m.inverted()@Vector(points[-1][:3]))[:2]))>100)
        if rev:guide=guide[::-1]
        for x,y,z in guide:
            w=m@Vector((x,y,z));dist=points[-1][3]+math.hypot(w.x-points[-1][0],w.y-points[-1][1]) if points else 0
            if points and math.hypot(w.x-points[-1][0],w.y-points[-1][1])<1e-5:continue
            points.append((w.x,w.y,w.z,dist))
        for refuge in meta[r['id']]['refuges']:refuges.append((m.inverted(),refuge))
        terrain=next(o for o in sources[r['id']].objects if o.name.startswith('Terrain_'))
        placed.append((r,m,terrain))
    bounds=(min(r['x'] for r in rows)-128,min(-r['z'] for r in rows)-128,max(r['x'] for r in rows)+128,max(-r['z'] for r in rows)+128)
    field=Field([(x,y,d) for x,y,z,d in points],bounds,refuges)
    values=[]
    for r,m,t in placed:
        for v in list(t.data.vertices)[:4225:4]:w=m@v.co;values.append(field.raw(w.x,w.y))
    field.thresholds=np.quantile(values,[.1888,.4993]);states=[0 if v<field.thresholds[0] else 1 if v<field.thresholds[1] else 2 for v in values]
    balance=[states.count(i)/len(states)*100 for i in range(3)]
    state_counts=[0,0,0];sourcehashes={};roadmax=0
    for r,m,t in placed:
        sourcehashes[r['id']]=hashlib.sha256(json.dumps([tuple(v.co) for v in t.data.vertices]).encode()).hexdigest()
        assert sourcehashes[r['id']]==meta[r['id']]['geometry_sha256']
        c=s.collection('PLACED_'+r['id'],scene);cc=s.collection('COLLISION_PLACED_'+r['id'],scene);cc.hide_render=True;cc.hide_viewport=True
        for original in sources[r['id']].objects:
            if original.type!='MESH' or original.get('ReviewOnly') or original.name=='Five_Stud_Human':continue
            assert original.parent is None,'Source parent requires explicit transform evaluation'
            o=original.copy();o.data=original.data.copy();o.matrix_world=m@original.matrix_basis
            iscollision=any(co.name.startswith('COLLISION_') for co in original.users_collection)
            (cc if iscollision else c).objects.link(o)
            if iscollision:continue
            if original.get('AppearanceRole') in ('terrain','grass'):colour_object(o,field)
            if original.get('StateAnchor'):
                anchor=json.loads(original['StateAnchor']);w=m@Vector((anchor['x'],anchor['y'],0));state=field.state(w.x,w.y);state_counts[state]+=1;o['AssembledState']=state
                if original.get('StateRole')=='crown':
                    o.data.materials.clear();o.data.materials.append(s.bp.LEAF[state]);h=int(hashlib.sha256(original.name.encode()).hexdigest()[:6],16)
                    if state==2 or state==1 and h%4==0:o.hide_render=True;o.hide_viewport=True
                elif anchor.get('type')!='tree' or original.get('StateRole')=='trunk':
                    o.data.materials.clear();o.data.materials.append(s.bp.CHARWOOD if state==2 else s.bp.WOOD)
    # Non-playable surrounding countryside; interpolation uses frozen boundaries
    # and never writes the playable vertex arrays.
    def world_height(x,y):
        candidates=[]
        for r,m,t in placed:
            p=m.inverted()@Vector((x,y,0));xx=max(-128,min(128,p.x));yy=max(-128,min(128,p.y));d=math.hypot(p.x-xx,p.y-yy)
            h=s.ec.surface([tuple(v.co) for v in list(t.data.vertices)[:4225]],4,xx,yy)+r['y']
            if d<1e-5:return h
            candidates.append((d,h))
        d,h=min(candidates);return h+min(1,d/80)*(10*math.sin(x/170)*math.cos(y/150)+4*math.sin(y/73))
    # Cache heights; regular scenery tile sampling avoids expensive repeated lookup.
    terrain_arrays=[(r,m,m.inverted(),[tuple(v.co) for v in list(t.data.vertices)[:4225]]) for r,m,t in placed]
    def wh(x,y):
        a=[]
        for r,m,inv,vs in terrain_arrays:
            p=inv@Vector((x,y,0));xx=max(-128,min(128,p.x));yy=max(-128,min(128,p.y));d=math.hypot(p.x-xx,p.y-yy);h=s.ec.surface(vs,4,xx,yy)+r['y']
            if d<1e-5:return h
            a.append((d,h))
        weights=[(d+1)**-4 for d,h in a];total=sum(weights);h=sum(w*z for w,(d,z) in zip(weights,a))/total;d=min(a)[0]
        return h+min(1,d/80)*(10*math.sin(x/170)*math.cos(y/150)+4*math.sin(y/73))
    road(scene,points,field,wh,terrain_arrays)
    scenery=s.collection('SCENERY_NONPLAYABLE_CONTINUATION',scene);scenery_count=0
    loX=int(bounds[0])-256;loY=int(bounds[1])-256;hiX=int(bounds[2])+256;hiY=int(bounds[3])+256
    for y0 in range(loY,hiY,256):
        for x0 in range(loX,hiX,256):
            vs=[];fs=[]
            for y in range(y0,y0+257,16):
                for x in range(x0,x0+257,16):vs.append((x,y,wh(x,y)))
            for j in range(16):
                for i in range(16):
                    x=x0+i*16+8;y=y0+j*16+8
                    if any(abs(x-r['x'])<128 and abs(y+r['z'])<128 for r in rows):continue
                    a=j*17+i;fs.extend(((a,a+1,a+18),(a,a+18,a+17)))
            if not fs:continue
            o=s.bp.mesh('Continuation_'+str(scenery_count),vs,fs,[],scenery);o['NonPlayable']=True;o['CanCollide']=False;o['AppearanceRole']='terrain';colour_object(o,field);scenery_count+=1
    # Authored front placement follows assembled field, not chunk stamping.
    fx=s.collection('ASSEMBLY_ACTIVE_FIRE_NONSOLID',scene);rng=random.Random(601+int(label[-1]));flames=0
    s.bp.FIRE=s.bp.material('Batch1_flame',(.8,.25,.02),1.5);s.bp.FIRECORE=s.bp.material('Batch1_core',(1,.5,.06),2)
    for r,m,t in placed:
        vs=next(q[3] for q in terrain_arrays if q[0] is r)
        for y in range(-120,121,12):
            for x in range(-120,121,12):
                w=m@Vector((x,y,s.ec.surface(vs,4,x,y)));v=field.raw(w.x,w.y)
                if abs(v-field.thresholds[1])<18 and flames<100:
                    s.bp.hill=lambda a,b,h=w.z:h;s.bp.flame(w.x,w.y,rng.uniform(1.2,3.2),fx);flames+=1
    # Peripheral field/tree lines continue countryside into non-playable hills.
    s.bp.RNG=rng;s.bp.hill=wh
    for k in range(65):
        edge=k%4;t=k//4/16
        x,y=[(bounds[0]-155,bounds[1]+t*(bounds[3]-bounds[1])),(bounds[2]+155,bounds[1]+t*(bounds[3]-bounds[1])),(bounds[0]+t*(bounds[2]-bounds[0]),bounds[1]-170),(bounds[0]+t*(bounds[2]-bounds[0]),bounds[3]+170)][edge]
        x+=18*math.sin(k*2.1);y+=16*math.cos(k*1.6);before=set(scenery.objects);state=field.state(x,y);s.bp.tree(x,y,rng.uniform(18,33),scenery,forced=state)
        for o in set(scenery.objects)-before:o['NonPlayable']=True;o['CanCollide']=False
    s.bp.SMOKE=s.bp.smoke_material();s.bp.hill=wh
    for index in range(0,len(points),max(1,len(points)//12)):
        x,y,z,d=points[index]
        if field.state(x,y)==2:s.bp.smoke(x+23,y+17,rng.uniform(18,34),fx)
    # Numerical join measurement uses frozen actual mesh arrays at 129 stations.
    seam=0;joins=[]
    for i in range(len(rows)-1):
        a=rows[i];b=rows[i+1];side=a['exit'];sock=next(q for q in meta[a['id']]['sockets'] if q['Id']==side)
        va=terrain_arrays[i][3];vb=terrain_arrays[i+1][3];ma=mats[i];mb=mats[i+1];inv=mb.inverted()
        boundary_states=[]
        for transverse in range(-128,129,2):
            x,y={'S':(transverse,-128),'N':(transverse,128),'W':(-128,transverse),'E':(128,transverse)}[side]
            w=ma@Vector((x,y,s.ec.surface(va,4,x,y)));p=inv@w;delta=abs(s.ec.surface(vb,4,p.x,p.y)-p.z);seam=max(seam,delta);boundary_states.append(field.state(w.x,w.y))
        joins.append({'from':a['id'],'to':b['id'],'kind':sock['Kind'],'states_across_edge':sorted(set(boundary_states)),'burn_front_crosses':1 in boundary_states and 2 in boundary_states})
    assert seam<.01,seam
    REPORT['layouts'][label]=dict(rows=rows,balance_percent=balance,thresholds=list(field.thresholds),field=field.stats,joins=joins,max_seam=seam,scenery_tiles=scenery_count,active_flames=flames,vegetation_object_states=state_counts,source_geometry_hashes=sourcehashes)
    scene['ReviewReport']=json.dumps(REPORT['layouts'][label]);dest=OUT/label;dest.mkdir(exist_ok=True)
    cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2;size=max(bounds[2]-bounds[0],bounds[3]-bounds[1])
    s.render(scene,dest/'overview.png',(cx+size*.58,cy-size*.82,size*.72+120),(cx,cy,20))
    s.render(scene,dest/'route_top.png',(cx,cy,size+400),(cx,cy,0),size+400)
    for index,name,height in [(12,'player_eye',5),(len(points)//2,'raised_gameplay',18),(len(points)*2//3,'ridge_gameplay',8)]:
        x,y,z,d=points[index];target=points[min(len(points)-1,index+18)];s.render(scene,dest/(name+'.png'),(x,y,z+height),target[:3])
    # A genuine reachable off-road high point, at five-stud eye height.
    r,m,t=placed[5];candidates=[v.co for v in list(t.data.vertices)[:4225] if abs(v.co.x)<95 and abs(v.co.y)<95];high=max(candidates,key=lambda v:v.z);eye=m@high;eye.z+=5;target=points[len(points)*2//3]
    s.render(scene,dest/'reachable_high_point.png',tuple(eye),target[:3])
    # Representative seam with collision rendered for diagnostic evidence.
    seampt=points[64];idx=next(i for i,p in enumerate(points) if p[3]>=field.thresholds[1]);frontpt=points[idx]
    s.render(scene,dest/'seam_road.png',(seampt[0]+15,seampt[1]-20,seampt[2]+6),(seampt[0],seampt[1]+18,seampt[2]))
    s.render(scene,dest/'active_front.png',(frontpt[0]+18,frontpt[1]-24,frontpt[2]+7),(frontpt[0],frontpt[1]+24,frontpt[2]))
    if label=='Layout1':
        diagnostic=s.bp.material('collision_diagnostic',(.03,.45,.6))
        changed=[]
        for c in scene.collection.children:
            if c.name.startswith('COLLISION_PLACED_'):
                c.hide_render=False;c.hide_viewport=False
                for o in c.objects:
                    o.data.materials.append(diagnostic)
                    for p in o.data.polygons:p.material_index=len(o.data.materials)-1
                    changed.append(o)
            elif c.name.startswith('PLACED_') or c.name.startswith('ASSEMBLY_'):c.hide_render=True
        s.render(scene,dest/'collision_seam.png',(seampt[0]+26,seampt[1]-38,seampt[2]+22),(seampt[0],seampt[1]+10,seampt[2]))
        for c in scene.collection.children:
            if c.name.startswith('COLLISION_PLACED_'):c.hide_render=True;c.hide_viewport=True
            elif c.name.startswith('PLACED_') or c.name.startswith('ASSEMBLY_'):c.hide_render=False
    return scene

def main():
    s.init();sources,meta=load_sources();REPORT['kit']=meta
    order=layouts(meta)
    for i,rows in enumerate(order):assemble('Layout'+str(i+1),rows,sources,meta)
    (OUT/'batch1_report.json').write_text(json.dumps(REPORT,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsBatch1.blend'))
    print('BATCH1_ASSEMBLY_COMPLETE',len(meta),len(REPORT['layouts']))
if __name__=='__main__':main()
