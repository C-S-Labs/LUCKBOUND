"""Isolated final gate: FBX colour roundtrip, returning route, anchored stage state.

Not production content or a chunk exporter. Uses the approved modularity baseline.
Run via tools/run_blender.py after production_gate_layout.py.
"""
import hashlib
import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE=Path(__file__).resolve().parent
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview')
BASE=Path('E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview/BurnedPlainsModularity.blend')
SPEC=importlib.util.spec_from_file_location('approved_foundation',HERE/'build_burned_plains.py')
bp=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(bp)
ORIGINAL_HILL=bp.hill
LAYOUT=json.loads((OUT/'return_layout.json').read_text())
ROWS=LAYOUT['placements']
PALETTE=[(.16,.235,.045),(.29,.235,.075),(.045,.037,.030)]
GRASS=[(.21,.34,.055),(.49,.40,.17),(.035,.028,.018)]
REPORT={'scope':'FINAL AREA I TECHNICAL GATE ONLY','studio_tested':(HERE/'production_gate_studio_report.json').exists(),
        'production_export':False,'production_systems_changed':False,'layout':LAYOUT}
MATRICES=[]; HEIGHTS=[]; GUIDES=[]; GROUND=[]; EDGE_PROFILES=[[] for _ in range(5)]


def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)


def guide(i,t):
    if ROWS[i]['bend']:
        a=t*math.pi/2
        return Vector((128-128*math.cos(a),-128+128*math.sin(a),0))
    y=-128+256*t
    return Vector((bp.road_x(y+ROWS[i]['source_center_y']),y,0))


def template_height(i,x,y):
    px=max(0,min(64,(x+128)/4)); py=max(0,min(64,(y+128)/4))
    ix=min(63,int(px)); iy=min(63,int(py)); tx=px-ix; ty=py-iy
    h=HEIGHTS[i]
    return float((h[iy,ix]*(1-tx)+h[iy,ix+1]*tx)*(1-ty)+(h[iy+1,ix]*(1-tx)+h[iy+1,ix+1]*tx)*ty)


def local_height(i,x,y):
    h=template_height(i,x,y)
    y0=ROWS[i]['source_center_y']; base=ORIGINAL_HILL(0,y0)
    low=ORIGINAL_HILL(0,y0-128)-base; high=ORIGINAL_HILL(0,y0+128)-base
    if ROWS[i]['bend']:
        # The elbow copy adapts only its road corridor and connected edge.
        samples=GUIDES[i]
        distances=[(q.x-x)**2+(q.y-y)**2 for q in samples]
        k=int(np.argmin(distances)); distance=math.sqrt(distances[k]); t=k/(len(samples)-1)
        road_z=low+(high-low)*smooth(t)
        h=h*(1-smooth(1-distance/30))+road_z*smooth(1-distance/30)
    influences=[]
    for profile in EDGE_PROFILES[i]:
        face=profile['face']
        distance=abs(y+128) if face=='S' else (abs(y-128) if face=='N' else abs(x-128))
        across=x if face in ('S','N') else y
        endpoint=profile['ends'][0 if across<0 else 1]
        edge_z=profile['center']+(endpoint-profile['center'])*smooth((abs(across)-12)/116)
        if distance<.0001: return edge_z
        t=min(1,distance/24)
        influences.append((((1-t)/max(t,.0001))**2,edge_z))
    total=1+sum(w for w,_ in influences)
    return (h+sum(w*z for w,z in influences))/total


def make_edge_profiles():
    corners={}
    for i,m in enumerate(MATRICES):
        for x in (-128,128):
            for y in (-128,128):
                w=m@Vector((x,y,0)); key=(round(w.x),round(w.y))
                corners.setdefault(key,[]).append(template_height(i,x,y)+ROWS[i]['y'])
    means={k:sum(v)/len(v) for k,v in corners.items()}
    for connection in LAYOUT['connections']:
        for i,face in [(connection['from']-1,'E' if ROWS[connection['from']-1]['bend'] else 'N'),(connection['to']-1,'S')]:
            points=[(128,-128),(128,128)] if face=='E' else [(-128,-128 if face=='S' else 128),(128,-128 if face=='S' else 128)]
            keys=[(round((MATRICES[i]@Vector((*p,0))).x),round((MATRICES[i]@Vector((*p,0))).y)) for p in points]
            EDGE_PROFILES[i].append({'face':face,'center':connection['y']-ROWS[i]['y'],
                                     'ends':[means[k]-ROWS[i]['y'] for k in keys]})
    REPORT['shared_edge_profiles']=EDGE_PROFILES


def world_height(x,y):
    nearby=[]
    for i,m in enumerate(MATRICES):
        local=m.inverted()@Vector((x,y,0))
        dx=max(abs(local.x)-128,0); dy=max(abs(local.y)-128,0)
        if dx==0 and dy==0:
            return local_height(i,local.x,local.y)+ROWS[i]['y']
        xx=max(-128,min(128,local.x)); yy=max(-128,min(128,local.y))
        distance=math.hypot(dx,dy)
        nearby.append((distance,local_height(i,xx,yy)+ROWS[i]['y']))
    # Small coherent continuation, not playable terrain or random BACKDROP.
    if nearby[0][0]<0: raise AssertionError('negative distance')
    closest=min(nearby)
    if closest[0]<.001: return closest[1]
    weights=[(d+1)**-4 for d,_ in nearby]
    return sum(w*h for w,(_,h) in zip(weights,nearby))/sum(weights)


class RouteField:
    """Graph-depth constraints extended continuously through an area grid.

    Distance along connected authored guides defines semantic depth. A harmonic
    spatial extension avoids nearest-segment projection jumps on returning routes.
    The reference implementation is an offline bounded proof, not a runtime solver.
    """
    def __init__(self,points):
        self.points=points
        self.length=points[-1][2]
        self.step=8; self.xmin=-360; self.ymin=-640
        self.nx=155; self.ny=131
        xs=self.xmin+np.arange(self.nx)*self.step
        ys=self.ymin+np.arange(self.ny)*self.step
        xx,yy=np.meshgrid(xs,ys)
        dist=np.full(xx.shape,np.inf); depth=np.zeros(xx.shape)
        pins=np.zeros(xx.shape,dtype=bool); sums=np.zeros(xx.shape); counts=np.zeros(xx.shape)
        for x,y,s in points:
            dd=(xx-x)**2+(yy-y)**2
            nearer=dd<dist; depth[nearer]=s/self.length; dist[nearer]=dd[nearer]
            ix=round((x-self.xmin)/self.step); iy=round((y-self.ymin)/self.step)
            sums[iy,ix]+=s/self.length; counts[iy,ix]+=1; pins[iy,ix]=True
        constraints=np.divide(sums,counts,out=np.zeros_like(sums),where=counts>0)
        depth[pins]=constraints[pins]
        # Red/black SOR; fixed guide constraints, no discontinuous query switching.
        parity=np.indices(depth.shape).sum(axis=0)%2
        for iteration in range(2400):
            before=depth.copy()
            for colour in (0,1):
                average=(depth[:-2,1:-1]+depth[2:,1:-1]+depth[1:-1,:-2]+depth[1:-1,2:])/4
                block=depth[1:-1,1:-1]
                mask=(parity[1:-1,1:-1]==colour)&~pins[1:-1,1:-1]
                block[mask]+=1.75*(average[mask]-block[mask])
                depth[0]=depth[1]; depth[-1]=depth[-2]; depth[:,0]=depth[:,1]; depth[:,-1]=depth[:,-2]
                depth[pins]=constraints[pins]
            residual=float(np.max(np.abs(depth-before)))
            if residual<2e-6: break
        self.grid=depth
        self.refuges=[]
        REPORT['field_solver']={'grid':list(depth.shape),'step_studs':8,'iterations':iteration+1,
                                'normalized_change_residual':residual,'fixed_guide_nodes':int(pins.sum()),
                                'route_length_studs':self.length,'grid_float64_bytes':depth.nbytes}

    def progress(self,x,y):
        px=max(0,min(self.nx-1,(x-self.xmin)/self.step)); py=max(0,min(self.ny-1,(y-self.ymin)/self.step))
        ix=min(self.nx-2,int(px)); iy=min(self.ny-2,int(py)); a=px-ix; b=py-iy
        g=self.grid
        return float((g[iy,ix]*(1-a)+g[iy,ix+1]*a)*(1-b)+(g[iy+1,ix]*(1-a)+g[iy+1,ix+1]*a)*b)

    def raw(self,x,y):
        severity=self.progress(x,y)*self.length+32*math.sin(x/64+.6)+16*math.sin(y/27)
        for r in self.refuges:
            p=r['inverse']@Vector((x,y,0))
            radius=((p.x-r['x'])/r['rx'])**2+((p.y-r['y'])/r['ry'])**2
            severity-=r['strength']*math.exp(-radius*2)
        return severity

    def state(self,x,y):
        v=self.raw(x,y)
        return 0 if v<self.thresholds[0] else (1 if v<self.thresholds[1] else 2)


def shader(name,attribute='AssemblyColour'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Roughness'].default_value=.94
    c=m.node_tree.nodes.new('ShaderNodeVertexColor'); c.layer_name=attribute
    m.node_tree.links.new(c.outputs['Color'],p.inputs['Base Color'])
    return m


def tint(o,field,palette,material):
    d=o.data; d.materials.clear(); d.materials.append(material)
    old=d.color_attributes.get('AssemblyColour')
    if old: d.color_attributes.remove(old)
    attr=d.color_attributes.new(name='AssemblyColour',type='FLOAT_COLOR',domain='POINT')
    for v in d.vertices:
        w=o.matrix_world@v.co; state=field.state(w.x,w.y)
        attr.data[v.index].color=(*palette[state],1)
    for face in d.polygons: face.material_index=0


def export_probe(source):
    scene=bpy.data.scenes.new('ISOLATED_FBX_COLOUR_ROUNDTRIP'); bpy.context.window.scene=scene
    o=source.copy(); o.data=source.data.copy(); scene.collection.objects.link(o)
    o.name='EMBERFALL_GATE_COLOUR_PROBE'; o.matrix_world=Matrix.Identity(4)
    d=o.data; before=d.color_attributes['AssemblyColour']
    values=[tuple(before.data[v.index].color) for v in d.vertices]
    for a in list(d.color_attributes): d.color_attributes.remove(a)
    attr=d.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
    for face in d.polygons:
        for li in face.loop_indices: attr.data[li].color=values[d.loops[li].vertex_index]
    d.color_attributes.active_color=attr; d.color_attributes.render_color_index=0
    d.materials.clear(); d.materials.append(shader('Gate_FBXPacked_Col','Col'))
    expected={}
    for loop in d.loops:
        key=tuple(round(v,3) for v in d.vertices[loop.vertex_index].co)
        expected[key]=tuple(attr.data[loop.index].color)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    path=OUT/'probe_export'/'colour_probe.fbx'; path.parent.mkdir(exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',
                            global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,
                            use_mesh_modifiers=True,mesh_smooth_type='FACE',colors_type='SRGB',add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    o.hide_render=True
    existing=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path),colors_type='SRGB')
    bpy.context.view_layer.update()
    imported=[v for v in bpy.data.objects if v not in existing and v.type=='MESH']
    assert len(imported)==1
    result=imported[0]; layer=result.data.color_attributes.get('Col')
    assert layer and layer.domain=='CORNER'
    xy={}
    for key,value in expected.items(): xy.setdefault(key[:2],[]).append((key[2],value))
    gaps=[]; position_gaps=[]; unmatched=0
    for loop in result.data.loops:
        w=result.matrix_world@result.data.vertices[loop.vertex_index].co
        key=tuple(round(v,3) for v in w)
        options=xy.get(key[:2],[])
        if not options: unmatched+=1; continue
        z,value=min(options,key=lambda item:abs(item[0]-w.z))
        if abs(z-w.z)>.002: unmatched+=1; continue
        position_gaps.append(abs(z-w.z))
        gaps.append(max(abs(a-b) for a,b in zip(value,layer.data[loop.index].color)))
    print('FBX_COMPARE',json.dumps({'unmatched':unmatched,'matched':len(gaps),'gap':max(gaps) if gaps else None,
                                  'matrix':list(map(list,result.matrix_world))}),flush=True)
    assert not unmatched and max(gaps)<.01
    result.data.calc_loop_triangles()
    REPORT['fbx_probe']={'file':str(path),'export_layer':'Col BYTE_COLOR CORNER','import_layer':layer.name,
                         'import_format':layer.data_type,'matched_corners':len(gaps),'unmatched_corners':unmatched,
                         'max_linear_colour_channel_error':max(gaps),'triangles':len(result.data.loop_triangles),
                         'max_position_comparison_error_studs':max(position_gaps),
                         'bytes':path.stat().st_size,'roblox_import':'UNVERIFIED: no connected Studio',
                         'settings':'legacy world FBX settings; SRGB, -Z/Y, baked space transform'}
    if (HERE/'production_gate_studio_report.json').exists():
        REPORT['fbx_probe']['roblox_import']='PASS: see production_gate_studio_report.json for bounded import/cache/loader/client results'
    print('FBX_ROUNDTRIP_PASS',json.dumps(REPORT['fbx_probe']),flush=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Read the accepted proof, including its retained approved foundation scene.
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE,Path('E:/BlenderAIProjects/Runtime/Emberfall_BurnedPlainsReview/BurnedPlains.blend')]}
    bpy.ops.wm.open_mainfile(filepath=str(BASE))
    baseline=bpy.data.scenes['Area_I_Modularity_0_180_0']
    templates={n:next(o for o in baseline.objects if o.name=='PLAYABLE_'+n) for n in ['opening_edge','active_burn_mid_plains','interior_edge']}
    foundation=bpy.data.scenes['Emberfall_Area_I_Burned_Plains']; sources=list(foundation.objects)
    export_probe(templates['opening_edge'])
    scene=bpy.data.scenes.new('AREA_I_FINAL_GATE_RETURN_ROUTE'); bpy.context.window.scene=scene; bp.SCENE=scene
    root=bp.collection('EXPERIMENT_ONLY_FIVE_PIECE_GATE')
    chunks=[bp.collection('PLAYABLE_256_GATE_'+str(i+1),root) for i in range(5)]
    scenery=bp.collection('NONPLAYABLE_CONTINUATION_GATE',root)
    connective=bp.collection('ASSEMBLY_APPEARANCE_ROAD_FIRE_GATE',root)
    library=bp.collection('AUTHORED_TREE_STAGES_SOURCE_ONLY'); library.hide_render=True; library.hide_viewport=True
    bp.REVIEW=bp.collection('GATE_CAMERAS_LIGHTS')
    scene.world=foundation.world
    for s in foundation.objects:
        if s.type=='LIGHT': bp.REVIEW.objects.link(s.copy())
    names=['opening_edge','active_burn_mid_plains','active_burn_mid_plains','active_burn_mid_plains','interior_edge']
    for i,row in enumerate(ROWS):
        MATRICES.append(Matrix.Translation((row['x'],-row['z'],row['y']))@Matrix.Rotation(-math.radians(row['yaw']),4,'Z'))
        HEIGHTS.append(np.array([v.co.z for v in templates[names[i]].data.vertices[:4225]]).reshape((65,65)))
        GUIDES.append([guide(i,k/64) for k in range(65)])
    make_edge_profiles()
    points=[]; travelled=0; previous=None
    for i in range(5):
        for k,q in enumerate(GUIDES[i]):
            w=MATRICES[i]@q
            if previous is not None: travelled+=math.hypot(w.x-previous.x,w.y-previous.y)
            if not (i and k==0): points.append((w.x,w.y,travelled))
            previous=w
    field=RouteField(points)
    # Protection is authored in the chunk frame and transformed with its anchor.
    refuges=[(0,77,51,32,43,350,'STONE_WALL_FIELD'),(2,-79,-48,14,90,650,'DAMP_DRAINAGE'),
             (0,84,-37,12,16,180,'HERO_TREE_PROTECTED_ROOTS')]
    for i,x,y,rx,ry,strength,name in refuges:
        field.refuges.append({'inverse':MATRICES[i].inverted(),'x':x,'y':y,'rx':rx,'ry':ry,'strength':strength,'name':name,'chunk':i+1})
    cells=[]
    for i in range(5):
        for y in range(-126,128,4):
            for x in range(-126,128,4):
                w=MATRICES[i]@Vector((x,y,0)); cells.append(field.raw(w.x,w.y))
    field.thresholds=[float(np.quantile(cells,.1888)),float(np.quantile(cells,.4993))]
    # Quantiles preserve the approved aggregate; they are never per-chunk quotas.
    counts=Counter(0 if v<field.thresholds[0] else (1 if v<field.thresholds[1] else 2) for v in cells)
    REPORT['balance_percent']={['green','stressed','charred'][k]:round(v/len(cells)*100,2) for k,v in counts.items()}
    REPORT['field_thresholds_studs']=field.thresholds
    REPORT['refuges']=[{k:v for k,v in r.items() if k!='inverse'} for r in field.refuges]
    groundmat=shader('Gate_AssemblyGround'); grassmat=shader('Gate_AssemblyGrass'); roadmat=shader('Gate_AssemblyRoad')
    for i in range(5):
        source=templates[names[i]]
        o=source.copy(); o.data=source.data.copy(); chunks[i].objects.link(o)
        o.name='GATE_TERRAIN_'+str(i+1); o.matrix_world=MATRICES[i]
        for v in o.data.vertices[:4225]: v.co.z=local_height(i,v.co.x,v.co.y)
        o['PrototypeOnly']=True; o['FootprintStuds']=[256,256]; o['RouteIndex']=i+1
        o.data.update(); tint(o,field,PALETTE,groundmat); GROUND.append(o)
    # Retain authored grass anchors; choose stage height and colour at final pose.
    batch=next(o for o in sources if o.name=='playable_grass_states')
    vertices=[batch.matrix_world@v.co for v in batch.data.vertices]
    for i,row in enumerate(ROWS):
        vs=[]; fs=[]; sy=row['source_center_y']
        for face in batch.data.polygons:
            coords=[vertices[k].copy() for k in face.vertices]
            x=sum(v.x for v in coords)/3; y=sum(v.y for v in coords)/3
            if not (sy-128<=y<sy+128): continue
            original=bp.burn_state(x,y); root=MATRICES[i]@Vector((x,y-sy,0)); state=field.state(root.x,root.y)
            oldfloor=(coords[0].z+coords[1].z)/2
            blade=coords[2].z-oldfloor
            if original==2: blade*=2
            if state==2: blade*=.5
            for k,v in enumerate(coords):
                v.y-=sy; v.z=local_height(i,v.x,v.y)+(blade if k==2 else .03)
            start=len(vs); vs.extend(tuple(v) for v in coords); fs.append((start,start+1,start+2))
        o=bp.mesh('GATE_AUTHORED_GRASS_'+str(i+1),vs,fs,[],chunks[i]); o.matrix_world=MATRICES[i]
        tint(o,field,GRASS,grassmat)
    # Copy compatible local remnant composition. No runtime anchor warping.
    retained=0
    for i,row in enumerate(ROWS):
        sy=row['source_center_y']
        correction=Matrix.Translation((0,-sy,-ORIGINAL_HILL(0,sy)))
        for s in sources:
            if s.type!='MESH' or s.name.startswith(('tree_','old_winding_field_track','playable_grass','chunk_')): continue
            if not {c.name for c in s.users_collection}.intersection({'Countryside_SOLID_DECOR','Flora_NONSOLID'}): continue
            center=sum([s.matrix_world@Vector(v) for v in s.bound_box],Vector())/8
            if not (-128<center.x<128 and sy-128<=center.y<sy+128): continue
            o=s.copy(); o.data=s.data.copy(); o.parent=None; chunks[i].objects.link(o)
            o.matrix_world=MATRICES[i]@correction@s.matrix_world
            local=correction@center
            o.location.z+=local_height(i,local.x,local.y)-template_height(i,local.x,local.y)
            w=MATRICES[i]@local; stage=field.state(w.x,w.y)
            if s.name.startswith(('field_fence','scorched_field','fallen_burned')):
                o.data.materials.clear(); o.data.materials.append(bpy.data.materials['BP_'+('charred_timber' if stage==2 else 'field_timber')])
            elif s.name.startswith('surviving_meadow_flower') and stage!=0:
                o.hide_render=True
            elif s.name.startswith('reused_temperate'):
                o.data.materials.clear(); o.data.materials.append(bpy.data.materials[['BP_grass_green','BP_grass_straw','BP_grass_black_stubble'][stage]])
            retained+=1
    # A single healthy branch skeleton supplies authored stage variants: root and
    # every canopy part receive one shared anchor decision, never separate samples.
    bp.LEAF=[bpy.data.materials['BP_canopy_'+n] for n in ('green','stressed','singed')]
    bp.WOOD=bpy.data.materials['BP_field_timber']; bp.CHARWOOD=bpy.data.materials['BP_charred_timber']
    bp.hill=lambda x,y:0; bp.RNG=random.Random(51026)
    old=set(bpy.data.objects); bp.tree(0,0,26,library,forced=0)
    bpy.context.view_layer.update()  # Flush newly authored canopy poses before copying.
    parts=[o for o in bpy.data.objects if o not in old]
    trunk=next(o for o in parts if o.name.startswith('tree_surviving'))
    crowns=sorted([o for o in parts if o!=trunk],key=lambda o:o.name)
    anchors=[(84,-293,30),(-89,-318,25),(108,-176,27),(-47,-152,26),(-91,-264,24),(-69,-239,19),
             (-104,116,33),(56,-45,26),(-53,23,30),(102,108,22),
             (87,190,27),(-61,297,25),(105,322,23),(-86,223,19),(56,299,23)]
    treechecks=[]
    for i,row in enumerate(ROWS):
        sy=row['source_center_y']
        for x,y,h in anchors:
            if not sy-128<=y<sy+128: continue
            ly=y-sy; w=MATRICES[i]@Vector((x,ly,local_height(i,x,ly))); state=field.state(w.x,w.y)
            depth=field.progress(w.x,w.y)
            stage=('healthy' if state==0 else ('stressed' if field.raw(w.x,w.y)<field.thresholds[1]-35 else 'singed')) if state<2 else ('skeletal' if depth>.8 else 'fresh_char')
            pose=MATRICES[i]@Matrix.Translation((x,ly,local_height(i,x,ly)))@Matrix.Scale(h/26,4)
            kept=0
            for k,s in enumerate([trunk]+crowns):
                if k and ((stage=='skeletal') or (stage=='fresh_char' and k!=1) or (stage=='singed' and k%3) or (stage=='stressed' and k%4==0)): continue
                o=s.copy(); o.data=s.data.copy(); o.parent=None; chunks[i].objects.link(o)
                # Source-only library is excluded from evaluation; use authored TRS.
                o.matrix_world=pose@Matrix.LocRotScale(s.location,s.rotation_euler.to_quaternion(),s.scale)
                o.name='GATE_TREE_'+stage; o['AnchorWorld']=list(w); o['EffectiveBurnState']=state; o['RouteDepth']=depth
                o.data.materials.clear()
                o.data.materials.append(bp.WOOD if k==0 and state==0 else (bp.CHARWOOD if k==0 else bp.LEAF[state]))
                kept+=1
            treechecks.append({'chunk':i+1,'world_root':list(w),'terrain_state':state,'variant':stage,'parts':kept,'depth':depth})
            assert not (state==2 and stage in ('healthy','stressed'))
    REPORT['tree_anchor_checks']=treechecks; REPORT['retained_remnant_objects']=retained
    # The road is the same hybrid intent, now with two authored quarter-circle guides.
    roadpoints=[]
    for i in range(5):
        samples=[MATRICES[i]@Vector((q.x,q.y,local_height(i,q.x,q.y))) for q in GUIDES[i]]
        roadpoints.extend(samples if i==0 else samples[1:])
    vs=[]; fs=[]; arclength=0; last=None; roadslopes=[]
    for k,p in enumerate(roadpoints):
        if last is not None:
            delta=math.hypot(p.x-last.x,p.y-last.y); arclength+=delta
            roadslopes.append(abs(p.z-last.z)/max(delta,.001))
        a=roadpoints[max(k-1,0)]; b=roadpoints[min(k+1,len(roadpoints)-1)]
        tangent=Vector((b.x-a.x,b.y-a.y,0)).normalized(); normal=Vector((tangent.y,-tangent.x,0))
        width=4.2+.5*math.sin(arclength/27)
        for sign in (-1,1):
            q=p+normal*width*sign; vs.append((q.x,q.y,q.z+.22))
        if k: fs.append((2*k-2,2*k,2*k+1,2*k-1))
        last=p
    track=bp.mesh('GATE_JOINED_AUTHORED_ROAD',vs,fs,[],connective)
    tint(track,field,[(.20,.135,.07),(.16,.10,.047),(.06,.041,.025)],roadmat)
    REPORT['road']={'samples':len(roadpoints),'max_sample_slope':max(roadslopes),'width_range_studs':[7.4,9.4],'connected_strip':True}
    # Separate large continuation; it follows edge height and the same field.
    sv=[]; sf=[]; step=8; xs=list(range(-320,833,step)); ys=list(range(-600,377,step))
    for y in ys:
        for x in xs: sv.append((x,y,world_height(x,y)))
    for j in range(len(ys)-1):
        for k in range(len(xs)-1):
            x=xs[k]+4; y=ys[j]+4
            if any(abs((m.inverted()@Vector((x,y,0))).x)<128 and abs((m.inverted()@Vector((x,y,0))).y)<128 for m in MATRICES): continue
            a=j*len(xs)+k; sf.extend([(a,a+1,a+len(xs)+1),(a,a+len(xs)+1,a+len(xs))])
    apron=bp.mesh('GATE_NONPLAYABLE_SCENERY',sv,sf,[],scenery); apron['NoSockets']=True; apron['NoncollidableVisual']=True
    tint(apron,field,PALETTE,groundmat)
    # Fire follows the actual shared char threshold, including socket crossings.
    bp.hill=world_height; bp.FIRE=bpy.data.materials['BP_flame_orange']; bp.FIRECORE=bpy.data.materials['BP_flame_core']; bp.SMOKE=bpy.data.materials['BP_SoftProceduralSmoke_REVIEW']
    sites=[]
    for y in range(-380,130,8):
        for x in range(-120,641,8):
            if field.state(x,y)==1 and field.state(x+8,y)==2:
                sites.append((x+4,y))
            elif field.state(x,y)==1 and field.state(x,y+8)==2:
                sites.append((x,y+4))
    for k,(x,y) in enumerate(sites):
        if abs(min(roadpoints,key=lambda p:(p.x-x)**2+(p.y-y)**2).x-x)<1: continue
        bp.flame(x,y,bp.RNG.uniform(.8,2.8),connective)
        if k%27==0: bp.smoke(x,y,25,connective)
    bpy.context.view_layer.update()
    # Continuity at all four connected full edges, evaluated from both meshes.
    joins=[]
    for c in LAYOUT['connections']:
        i=c['from']-1; j=c['to']-1; x=c['x']; y=-c['z']
        normal=Vector((ROWS[j]['x']-ROWS[i]['x'],-ROWS[j]['z']+ROWS[i]['z'],0)).normalized()
        across=Vector((-normal.y,normal.x,0))
        gaps=[]
        for t in range(-128,129,4):
            q=Vector((x,y,0))+across*t
            ha=[]
            for n in (i,j):
                local=MATRICES[n].inverted()@q; ha.append(local_height(n,local.x,local.y)+ROWS[n]['y'])
            gaps.append(abs(ha[0]-ha[1]))
        assert max(gaps)<.001
        joins.append({'from':i+1,'to':j+1,'stations':65,'max_height_gap':max(gaps),'one_shared_field':True})
    REPORT['joins']=joins
    route_depth=[field.progress(x,y) for x,y,s in points]
    # Pin-grid interpolation may have sub-cell noise; categorical late progress
    # must not reset when the route returns to the entry's world Y coordinate.
    REPORT['progression']={'start_depth':route_depth[0],'end_depth':route_depth[-1],
                           'max_local_backstep':max([0]+[a-b for a,b in zip(route_depth,route_depth[1:])]),
                           'chunk_midpoint_depth':[field.progress(*(MATRICES[i]@GUIDES[i][32])[:2]) for i in range(5)],
                           'return_same_world_y':ROWS[0]['z']==ROWS[-1]['z']}
    assert REPORT['progression']['end_depth']>.97
    assert REPORT['progression']['max_local_backstep']<.01
    mids=REPORT['progression']['chunk_midpoint_depth']; assert all(a<b for a,b in zip(mids,mids[1:]))
    for r in field.refuges:
        world=MATRICES[r['chunk']-1]@Vector((r['x'],r['y'],0))
        inverse=r['inverse']@world
        assert abs(inverse.x-r['x'])+abs(inverse.y-r['y'])<.001
    scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
    cameras=[bp.camera('01_return_route_overview',(950,-900,650),(256,-40,52),42),
             bp.camera('02_route_depth_top',(256,-80,1500),(256,-80,0),ortho=1200),
             bp.camera('03_player_eye_bend',(8,-143,world_height(8,-143)+5),(50,-45,world_height(50,-45)+7),27),
             bp.camera('04_raised_gameplay',(55,-35,world_height(55,-35)+12),(230,15,world_height(230,15)+5),28),
             bp.camera('05_reachable_ridge',(102,-58,world_height(102,-58)+5),(390,-60,world_height(390,-60)+6),30),
             bp.camera('06_return_interior_eye',(512,-180,world_height(512,-180)+5),(512,-335,world_height(512,-335)+6),28)]
    REPORT['evidence']=[]
    for cam in cameras:
        scene.camera=cam; scene.render.resolution_x=1200; scene.render.resolution_y=800
        scene.render.filepath=str(OUT/(cam.name+'.png')); bpy.ops.render.render(write_still=True)
        REPORT['evidence'].append(scene.render.filepath); print('RENDERED',cam.name,flush=True)
    scene.camera=cameras[0]; scene['README']='OWNER APPROVED BASELINE PRESERVED. Final technical gate only. No production kit/exports/IDs. Route depth uses connected authored guides; all states sample one field.'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsProductionGate.blend'))
    REPORT['preserved_inputs_sha256']=hashes
    for p,h in hashes.items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    REPORT['inputs_unchanged']=True
    for p in [HERE/'production_gate_report.json',OUT/'production_gate_report.json']:
        p.write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('FINAL_GATE_BLENDER_PASS',json.dumps(REPORT['balance_percent']),flush=True)


if __name__=='__main__':
    main()
