"""Isolated frozen-source terrain/collision proof. Launch with tools/run_blender.py.

No mesh authoring function accepts an assembled pose or neighbour. No exports.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Matrix,Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import edge_profile_contract as contract
import validate_edge_profiles as validator
import build_burned_plains as bp
import production_gate_study as gate

OUT=validator.OUT
BASE=Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend')
INPUTS=[BASE,gate.BASE,Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview/BurnedPlainsProductionGate.blend')]


def coll(name,scene):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c


def closed(name,vertices,faces,collection):
    used=sorted({i for f in faces for i in f});mapping={old:new for new,old in enumerate(used)}
    vertices=[vertices[i] for i in used];faces=[tuple(mapping[i] for i in f) for f in faces]
    n=len(vertices); edges={}
    polygons=list(faces)+[tuple(n+i for i in reversed(f)) for f in faces]
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            k=tuple(sorted((a,b))); edges[k]=edges.get(k,0)+1
    polygons.extend((a,b,b+n,a+n) for (a,b),count in edges.items() if count==1)
    obj=bp.mesh(name,vertices+[(x,y,z-4) for x,y,z in vertices],polygons,[],collection)
    bm=bmesh.new(); bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges),name
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data)
    bm.free(); return obj


def source(name,scene):
    collection=coll('SOURCE_'+name,scene); collision=coll('COLLISION_'+name,scene)
    v,f=contract.grid(name,4); terrain=bp.mesh('VISUAL_'+name,v,f,[],collection)
    cv,cf=contract.grid(name,8)
    connected=set(contract.SPECS[name]).intersection({'S','N','E','W'})
    def at_boundary(x,y):
        return ('S' in connected and y==-128 or 'N' in connected and y==120
                or 'W' in connected and x==-128 or 'E' in connected and x==120)
    for y in range(-128,128,8):
        for x in range(-128,128,8):
            if not at_boundary(x,y):continue
            quad=[(x,y,contract.height(name,x,y)),(x+8,y,contract.height(name,x+8,y)),
                  (x+8,y+8,contract.height(name,x+8,y+8)),(x,y+8,contract.height(name,x,y+8))]
            for k,indices in enumerate(((0,1,2),(0,2,3))):
                o=closed('EDGE_CONVEX_'+name+'_'+str(x)+'_'+str(y)+'_'+str(k),[quad[i] for i in indices],[(0,1,2)],collision)
                o['CollisionFidelity']='Hull';o['AuthoredSeamCell']=True
    for ty in range(-128,128,64):
        for tx in range(-128,128,64):
            vs=[(tx+i*8,ty+j*8,contract.height(name,tx+i*8,ty+j*8)) for j in range(9) for i in range(9)]
            fs=[]
            for j in range(8):
                for i in range(8):
                    if at_boundary(tx+i*8,ty+j*8):continue
                    a=j*9+i; fs.extend(((a,a+1,a+10),(a,a+10,a+9)))
            o=closed('WALK_'+name+'_'+str(tx)+'_'+str(ty),vs,fs,collision)
            o['CollisionFidelity']='PreciseConvexDecomposition'
    rng=random.Random(970+contract.SPECS[name]['shape']); vertices=[]; faces=[]
    road=contract.guide(name)
    for _ in range(1700):
        x,y=rng.uniform(-127,127),rng.uniform(-127,127)
        if min((x-a)**2+(y-b)**2 for a,b in road)<36: continue
        z=contract.surface(v,4,x,y)+.03
        for q in range(3):
            start=len(vertices); dx,dy=rng.uniform(-.5,.5),rng.uniform(-.5,.5)
            vertices.extend(((x+dx-.1,y+dy,z),(x+dx+.1,y+dy,z),(x+dx+.12,y+dy+.18,z+rng.uniform(.5,1.4))))
            faces.append((start,start+1,start+2))
    bp.mesh('AUTHORED_GRASS_'+name,vertices,faces,[],collection)
    bp.hill=lambda x,y:contract.surface(v,4,x,y)
    bp.RNG=random.Random(210+contract.SPECS[name]['shape'])
    for x,y,h in [(-62,-94,27),(84,104,29),(-94,92,23),(65,-50,20)]:
        before=set(collection.objects); bp.tree(x,y,h,collection,forced=0)
        for obj in set(collection.objects)-before: obj['TreeAnchor']=[x,y]
    # Distinct restrained compositions, preserving the shared authoring vocabulary.
    if name in ('A','A2'):
        for x in range(31,113,7):
            y=-58+5*math.sin(x/37)
            bp.blob('old_field_wall',(x,y,bp.hill(x,y)+1.4),(3,1.2,1.4),bpy.data.materials['BP_field_stone'],collection)
    else:
        pts=[(-70+i*10,-47+6*math.sin(i/3)) for i in range(8)]
        bp.fence(pts,collection,damaged=name in ('B2','C'))
    metadata=[contract.socket(name,s) for s in ('S','W','N','E') if s in contract.SPECS[name]]
    terrain['SocketProfiles']=json.dumps(metadata); terrain['FootprintStuds']=[256,256]
    terrain['FrozenSource']=True; terrain['AuthoringTransitionDepth']=contract.DEPTH
    payload={'footprint':[256,256],'sockets':metadata,
             'visual':[list(v.co) for v in terrain.data.vertices],
             'collision':[list(Vector(q)) for q in cv]}
    return collection,collision,payload


def pose(row):
    return Matrix.Translation((row['x'],-row['z'],row['y']))@Matrix.Rotation(-math.radians(row['yaw']),4,'Z')


def assembly(label,rows,sources,collision_only=False):
    scene=bpy.data.scenes.new('REVIEW_'+label); bpy.context.window.scene=scene
    review=coll('Cameras_Lighting',scene); bp.REVIEW=review
    mats=coll('Assembled_authored_chunks',scene)
    matrices=[pose(r) for r in rows]; points=[]; length=0; previous=None
    for row,matrix in zip(rows,matrices):
        for x,y in contract.guide(row['name']):
            w=matrix@Vector((x,y,contract.height(row['name'],x,y)))
            if previous is not None and math.hypot(w.x-previous.x,w.y-previous.y)<1e-7: continue
            if previous is not None: length+=math.hypot(w.x-previous.x,w.y-previous.y)
            points.append((w.x,w.y,length)); previous=w
    field=gate.RouteField(points)
    values=[]
    for row,matrix in zip(rows,matrices):
        for y in range(-126,128,4):
            for x in range(-126,128,4):
                w=matrix@Vector((x,y,0)); values.append(field.raw(w.x,w.y))
    field.thresholds=[float(np.quantile(values,.1888)),float(np.quantile(values,.4993))]
    mat=gate.shader('Edge_ground_'+label); gm=gate.shader('Edge_grass_'+label)
    cyan=bp.material('collision_cyan_'+label,(.02,.48,.58))
    for row,matrix in zip(rows,matrices):
        sc,cc,_=sources[row['name']]
        for original in (cc.objects if collision_only else sc.objects):
            o=original.copy(); o.data=original.data.copy(); o.parent=None; mats.objects.link(o)
            o.matrix_world=matrix@original.matrix_world
            if collision_only:
                o.data.materials.clear(); o.data.materials.append(cyan)
                o.show_wire=True; o.show_all_edges=True
                o.data.materials.append(bp.material('collision_wire_'+o.name,(.012,.035,.04)))
                wire=o.modifiers.new('Diagnostic_edges_only','WIREFRAME')
                wire.thickness=.055;wire.use_replace=False;wire.material_offset=1
            elif original.name.startswith(('VISUAL_','AUTHORED_GRASS')):
                gate.tint(o,field,gate.GRASS if 'GRASS' in original.name else gate.PALETTE,gm if 'GRASS' in original.name else mat)
            elif 'TreeAnchor' in original:
                x,y=original['TreeAnchor']; root=matrix@Vector((x,y,0)); state=field.state(root.x,root.y)
                o.data.materials.clear(); o.data.materials.append(bp.CHARWOOD if original.name.startswith('tree_') and not original.name.startswith('tree_crown') and state else (bp.WOOD if not original.name.startswith('tree_crown') else bp.LEAF[state]))
                if original.name.startswith('tree_crown') and state==2: o.hide_render=True
    def world_height(x,y):
        for row,m in zip(rows,matrices):
            q=m.inverted()@Vector((x,y,0))
            if abs(q.x)<=128.001 and abs(q.y)<=128.001:
                return contract.surface(sources[row['name']][2]['visual'],4,q.x,q.y)+row['y']
        raise ValueError((x,y))
    if not collision_only:
        # Explicit non-playable continuity, separate from all frozen sources.
        scenery=coll('NONPLAYABLE_CONTINUATION',scene);sv=[];sf=[]
        axis=list(range(-384,641,8));n=len(axis)
        def outside_height(x,y):
            candidates=[]
            for row,m in zip(rows,matrices):
                q=m.inverted()@Vector((x,y,0));cx=max(-128,min(128,q.x));cy=max(-128,min(128,q.y))
                d=math.hypot(q.x-cx,q.y-cy)
                h=contract.surface(sources[row['name']][2]['visual'],4,cx,cy)+row['y']
                if d<1e-7:return h
                candidates.append((d,h))
            weights=[1/(d**4) for d,h in candidates]
            h=sum(w*c[1] for w,c in zip(weights,candidates))/sum(weights)
            d=min(c[0] for c in candidates)
            return h+contract.smooth(d/80)*8*math.sin(x/115)*math.cos(y/140)
        for y in axis:
            for x in axis:sv.append((x,y,outside_height(x,y)))
        for j in range(n-1):
            for i in range(n-1):
                x,y=axis[i]+4,axis[j]+4
                if any(abs((m.inverted()@Vector((x,y,0))).x)<128 and abs((m.inverted()@Vector((x,y,0))).y)<128 for m in matrices):continue
                a=j*n+i;sf.extend(((a,a+1,a+n+1),(a,a+n+1,a+n)))
        o=bp.mesh('SCENERY_NOT_PLAYABLE_NOT_EXPORTED',sv,sf,[],scenery)
        o['Playable']=False;o['ParticipatesInSockets']=False
        gate.tint(o,field,gate.PALETTE,mat)
    # One strip through existing source-local intent; no terrain modification.
    rv=[];rf=[]
    for k,(x,y,_) in enumerate(points):
        a=points[max(0,k-1)];b=points[min(len(points)-1,k+1)]
        dx,dy=b[0]-a[0],b[1]-a[1]; dist=max(.001,math.hypot(dx,dy))
        for sign in (-1,1):
            xx,yy=x-sign*dy/dist*4.2,y+sign*dx/dist*4.2
            try: z=world_height(xx,yy)+.08
            except ValueError: z=world_height(x,y)+.08
            rv.append((xx,yy,z))
        if k: rf.append((2*k-2,2*k,2*k+1,2*k-1))
    road=bp.mesh('ASSEMBLY_ROAD_INTENT',rv,rf,[],mats)
    road.hide_render=collision_only
    gate.tint(road,field,[(.20,.135,.07),(.16,.10,.047),(.06,.041,.025)],gate.shader('Road_'+label))
    sun=bpy.data.lights.new('Overcast','SUN');sun.energy=2;sun.angle=.18
    so=bpy.data.objects.new('Overcast',sun);review.objects.link(so);so.rotation_euler=(.55,-.55,-.65)
    scene.world=bpy.data.worlds.new('Grey_sky_'+label);scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.32,.36,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1100;scene.render.resolution_y=760
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.render.film_transparent=False
    scene['PrototypeOnly']=True;scene['FrozenSourceNoLayoutReshaping']=True
    return scene,world_height


def render(scene,name,eye,target,lens=40,ortho=None):
    bpy.context.window.scene=scene;bp.REVIEW=next(c for c in scene.collection.children if c.name.startswith('Cameras_Lighting'))
    cam=bp.camera(name,eye,target,lens,ortho);scene.camera=cam
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)


def main():
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    OUT.mkdir(parents=True,exist_ok=True)
    with bpy.data.libraries.load(str(BASE),link=False) as (a,b):
        b.materials=[n for n in a.materials if n.startswith('BP_')]
        b.collections=[n for n in a.collections if n=='Scale_Reference']
    bp.WOOD=bpy.data.materials['BP_field_timber'];bp.CHARWOOD=bpy.data.materials['BP_charred_timber']
    bp.LEAF=[bpy.data.materials['BP_canopy_'+n] for n in ('green','stressed','singed')]
    library=bpy.data.scenes.new('FROZEN_INDEPENDENT_SOURCES');bpy.context.window.scene=library
    # A 5-stud Roblox standing reference, isolated from geometry and exports.
    scale=coll('Scale_Reference',library)
    bp.beam('5_stud_standing_reference',(0,0,0),(0,0,5),.8,bp.WOOD,scale)
    sources={name:source(name,library) for name in contract.SPECS}
    bpy.context.view_layer.update()  # Resolve source canopy/prop TRS before copying.
    payloads={name:s[2] for name,s in sources.items()}
    (OUT/'source_meshes.json').write_text(json.dumps(payloads))
    layouts=json.loads((OUT/'layouts.json').read_text())
    report=validator.run(payloads,layouts)
    scenes={}
    labels=['A_0_B1','A_0_B2','A_0_B3','A_90_B2','rising_corner']
    for label in labels: scenes[label]=assembly(label,layouts[label],sources)
    scenes['source_A']=assembly('source_A',[{'name':'A','x':0,'y':0,'z':0,'yaw':0}],sources)
    scenes['collision']=assembly('collision',layouts['rising_corner'],sources,True)
    render(scenes['source_A'][0],'02_source_A',(310,-340,240),(0,0,0),42)
    for label,num in zip(labels[:4],['03','04','05','06']):
        sc,_=scenes[label]; center=(130,0,0) if label=='A_90_B2' else (0,128,6)
        render(sc,num+'_'+label,(center[0]+450,center[1]-480,320),center,42)
    sc,wh=scenes['rising_corner']
    render(sc,'01_profile_contract_overview',(730,-610,470),(128,128,12),42)
    render(sc,'07_visual_seam',(25,102,wh(25,102)+5),(25,153,wh(25,153)+4),27)
    render(scenes['collision'][0],'08_collision_seam',(310,-140,210),(125,130,12),42)
    render(sc,'09_player_eye',(0,103,wh(0,103)+5),(18,178,wh(18,178)+5),27)
    render(sc,'10_elevated_gameplay',(-61,73,wh(-61,73)+12),(95,216,wh(95,216)+6),30)
    render(sc,'11_reachable_ridge',(95,101,wh(95,101)+5),(190,230,wh(190,230)+6),28)
    assert all(validator.fingerprint(sources[n][2])==report['source_mesh_sha256'][n] for n in sources)
    report['preserved_inputs_sha256']=hashes
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    report['closed_collision_pieces_per_source']={n:len(s[1].objects) for n,s in sources.items()}
    report['boundary_collision']='Frozen 8-stud outer row; convex triangular prisms, Hull. Interior closed tiles, PreciseConvexDecomposition.'
    report['inputs_unchanged']=True
    report['evidence']=[str(p) for p in sorted(OUT.glob('0[1-9]_*.png'))]+[str(p) for p in sorted(OUT.glob('1[01]_*.png'))]
    bpy.context.window.scene=sc;sc.camera=bpy.data.objects['01_profile_contract_overview']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsEdgeProfiles.blend'))
    for path in (HERE/'edge_profile_report.json',OUT/'validation.json'):path.write_text(json.dumps(report,indent=2))
    print('FROZEN_TERRAIN_COLLISION_PROOF_PASS',len(report['joins']),flush=True)


if __name__=='__main__': main()
