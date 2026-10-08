"""Continue saved Emberfall: contained lava, fracture shelves, natural route guidance.

One-pass protected Blender editor. No regeneration, runtime edits or exports.
"""
import bpy
import json
import math
import shutil
import importlib.util
import sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ArchitectureReview')
MAIN = OUT/'EmberfallPrototype.blend'
INPUT = OUT/'Input_LavaGeology.blend'
IMAGES = OUT/'LavaGeologyReview'
REPORT = {}


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clamp(t):
    return max(0, min(1, t))


def floor(tree, x, y):
    return art.floor(tree, max(-127.9999, min(127.9999, x)), max(-127.9999, min(127.9999, y)))


def target_height(name, x, y):
    old = floor(TREES[name], x, y)
    inward = arch.smooth(24, 44, min(128-abs(x), 128-abs(y)))
    if not inward:
        return old
    # Preserve every playable central corridor/hub. Broad shelf damage belongs
    # on shoulders, not under combat footwork or in a socket mouth.
    if name in arch.NAMES:
        i = arch.NAMES.index(name)
        if name == arch.NAMES[0]:
            q = max(abs((x+92)/8), abs((y-52)/7))
            if q < 1:
                return old-1.25*(1-q)*inward
        if abs(x) < 35 or (i == 2 and math.hypot(x, y) < 48):
            return old
        if i == 1:
            # Retain the broad hot channel; fill only the excessively low fringe.
            base = arch.level(y)-28
            if x > 39 and -85 < y < 55 and old-base < -6:
                return max(old, base-6)*inward+old*(1-inward)
        cx, cy, sx, sy = [(-64, -38, 33, 43), (-68, 15, 27, 57),
                          (62, 61, 35, 27), (72, 40, 25, 40), (0, 50, 72, 24)][i]
        q = max(abs((x-cx+.22*(y-cy))/sx), abs((y-cy)/sy))
        if q < 1 and old > (arch.level(y)-28 if i == 1 else 0)+5:
            base = arch.level(y)-28 if i == 1 else 0
            h = old-base
            # Two deliberate historical flow layers, with a slumped side. Broad
            # asymmetric planar ledges replace smooth shoulders, no noise field.
            ledge = 7+.035*(x-cx)+.055*(y-cy) if h < 13 else 15+.025*(x-cx)-.06*(y-cy)
            weight = inward*(1-arch.smooth(.65, 1, q))
            return old+(base+ledge-old)*weight
        return old
    if name not in (arch.SCENERY[3], arch.SCENERY[4], arch.SCENERY[6]):
        return old
    if name == arch.SCENERY[4]:
        width = 24 if y < -24 else 30 if y < 38 else 22
        d = abs((x+3+.12*y)/width)
        if d < .52:
            z = -49+.035*y
        elif d < .74:
            z = -49+clamp((d-.52)/.22)*15
        elif d < 1.15:
            z = -34+.04*y+(3 if x > 0 else -1)
        elif d < 1.43:
            z = -32+clamp((d-1.15)/.28)*20
        elif d < 1.85:
            z = -12+.055*y
        elif d < 2.13:
            z = -12+clamp((d-1.85)/.28)*14
        else:
            return old
        weight = inward*arch.smooth(-95, -72, y)*(1-arch.smooth(68, 95, y))*(1-arch.smooth(1.93, 2.13, d))
    else:
        cx, cy, sx, sy = (11, 3, 75, 65) if name == arch.SCENERY[3] else (28, -20, 28, 59)
        dx, dy = (x-cx)/sx, (y-cy)/sy
        # A tilted polygonal footprint and one torn bank; not a circular bowl.
        d = max(abs(dx+.23*dy), abs(dy), abs(dx-dy)*.66)
        depth = 35 if name == arch.SCENERY[3] else 18
        if d < .48:
            z = -depth+.02*y
        elif d < .64:
            z = -depth+clamp((d-.48)/.16)*depth*.32
        elif d < .82:
            z = -depth*.68+.035*y+(3 if x < cx and y > 8 else 0)
        elif d < .96:
            z = -depth*.68+clamp((d-.82)/.14)*depth*.41
        elif d < 1.08:
            z = -depth*.27+.03*x
        else:
            return old
        weight = inward*(1-arch.smooth(.99, 1.13, d))
    return old+(arch.shoulder(x, y)+z-old)*weight


def source_height_offset(ob, y):
    if ob.parent and ob.parent.get('AssetCollection') in arch.SCENERY:
        return arch.level(ob.parent.location.y+y)-ob.parent.location.z
    return 0


def edit_foundations():
    seen = set()
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.get('TerrainFaceCount') or ob.data.as_pointer() in seen:
            continue
        seen.add(ob.data.as_pointer())
        name = cont.home(ob)
        ground_ids = {k for p in ob.data.polygons[:ob['TerrainFaceCount']] for k in p.vertices}
        for k in ground_ids:
            v = ob.data.vertices[k]
            x, y = cont.canonical(ob, v.co.x, v.co.y)
            v.co.z += target_height(name, x, y)-floor(TREES[name], x, y)
        # Existing disconnected columns/masses move as rigid components, never
        # stretched by the new wall field. Protected-border components stay put.
        moved = 0
        for comp in arch.components(ob.data):
            if any(k in ground_ids for k in comp):
                continue
            pts = [ob.data.vertices[k].co for k in comp]
            if any(max(abs(v.x), abs(v.y)) >= 104 for v in pts):
                continue
            cx, cy = sum(v.x for v in pts)/len(pts), sum(v.y for v in pts)/len(pts)
            x, y = cont.canonical(ob, cx, cy)
            dz = target_height(name, x, y)-floor(TREES[name], x, y)
            if abs(dz) > .01:
                for k in comp:
                    ob.data.vertices[k].co.z += dz
                moved += 1
        ob.data.update()
        REPORT.setdefault('foundation_edits', {})[ob.name] = {'seated_components': moved}
    # Seat existing flora/rubble/surface parts against the same local ground.
    seen = set()
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.get('TerrainFaceCount') or ob.get('ReviewOnlyVolume'):
            continue
        name = cont.home(ob)
        if not name:
            continue
        if ob.get('LibraryAsset'):
            x, y = cont.canonical(ob, ob.location.x, ob.location.y)
            ob.location.z += target_height(name, x, y)-floor(TREES[name], x, y)
        elif ob.data.as_pointer() not in seen:
            seen.add(ob.data.as_pointer())
            for v in ob.data.vertices:
                x, y = cont.canonical(ob, v.co.x+ob.location.x, v.co.y+ob.location.y)
                v.co.z += target_height(name, x, y)-floor(TREES[name], x, y)
            ob.data.update()


def debug_geometry():
    count = 0
    for scene in bpy.data.scenes:
        for ob in list(scene.objects):
            if ob.type != 'MESH':
                continue
            mats = [m.name for m in ob.data.materials if m]
            guide = '_continuous_ash_crust' in ob.name
            obsolete_lava = not ob.get('LibraryAsset') and len(mats) == 1 and mats[0] in ('Ember_Molten', 'Ember_DeepHeat')
            if not (guide or obsolete_lava) or ob.get('SupersededSurfaceDebug'):
                continue
            parent = ob.users_collection[0]
            dbg = next((c for c in parent.children if c.name.startswith(parent.name+'_REVIEW_DEBUG')), None)
            if not dbg:
                dbg = arch.coll(parent.name+'_REVIEW_DEBUG_SUPERSEDED', parent)
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            dbg.objects.link(ob)
            dbg.hide_render = True
            dbg.hide_viewport = True
            ob.hide_render = True
            ob['SupersededSurfaceDebug'] = True
            ob['ProductionArt'] = False
            count += 1
    REPORT['debug_objects_hidden'] = count


def integrate_crust(group):
    ob = next(o for o in group.all_objects if '_fractured_crust' in o.name)
    tree = art.surface_tree(bpy.data.objects[group.name])
    vs, fs, indices = [], [], []
    for j, comp in enumerate(arch.components(ob.data)):
        pts = [ob.data.vertices[k].co for k in comp]
        if len(comp) < 18:
            offset = len(vs); mapping = {k: offset+i for i, k in enumerate(comp)}
            vs.extend(tuple(ob.data.vertices[k].co) for k in comp)
            for p in ob.data.polygons:
                if all(k in mapping for k in p.vertices):
                    fs.append(tuple(mapping[k] for k in p.vertices)); indices.append(p.material_index)
            continue
        cx, cy = sum(p.x for p in pts)/len(pts), sum(p.y for p in pts)/len(pts)
        rx = (max(p.x for p in pts)-min(p.x for p in pts))*.53
        ry = (max(p.y for p in pts)-min(p.y for p in pts))*.53
        # Torn lobe, missing corner and narrow capture neck replace hexagonal panels.
        outline = [(-1,-.15),(-.85,-.7),(-.35,-.82),(-.18,-.43),(.18,-.8),(.8,-.65),
                   (1,.18),(.58,.42),(.65,.8),(.04,1),(-.45,.6),(-.8,.48)]
        start = len(vs)
        for ring in range(2):
            for a, b in outline:
                x, y = cx+a*rx, cy+b*ry
                x, y = max(-102, min(102, x)), max(-102, min(102, y))
                z = floor(tree, x, y)
                gain = arch.smooth(-.4, .8, a*.3+b)
                lifted = .15 if abs(cx) < 35 and group.name in arch.NAMES else .65+(j%3)*.4
                z += -.6 if ring == 0 else -.22+gain*lifted
                vs.append((x,y,z))
        # Unequal triangulated sectors imply a surface splitting/slumping.
        center_id = len(vs)
        vs.append((cx+rx*.08, cy-ry*.12, floor(tree,cx+rx*.08,cy-ry*.12)+.08))
        for k in range(12):
            fs.append((start+12+k,start+12+(k+1)%12,center_id)); indices.append(0)
            fs.append((start+k,start+(k+1)%12,start+12+(k+1)%12,start+12+k))
            indices.append(1 if k in (3,4) else 0)
    data = bpy.data.meshes.new(ob.name+'_embedded_torn_skin')
    data.from_pydata(vs, [], fs)
    for m in ob.data.materials:
        data.materials.append(m)
    for p, i in zip(data.polygons,indices): p.material_index=i
    ob.data = data
    for scene in [bpy.data.scenes['Architecture_'+s] for s in 'ABC']:
        for placed in scene.objects:
            if placed.type != 'MESH' or not placed.parent or placed.parent.get('AssetCollection') != group.name or '_fractured_crust' not in placed.name:
                continue
            if group.name in arch.NAMES:
                placed.data = data
            else:
                placed.data = data.copy()
                angle = math.radians(placed.parent.get('AuthoredQuarterTurn',0))
                cs,sn=math.cos(angle),math.sin(angle)
                for v in placed.data.vertices:
                    x,y=v.co.x,v.co.y
                    v.co.x,v.co.y=cs*x-sn*y,sn*x+cs*y
                    v.co.z += source_height_offset(placed,v.co.y)
    ob['SurfaceIntegration'] = 'torn crust lobes; most rims embedded; selective thermal peel; no path border'


def lava_height(name, x, y):
    if name == arch.NAMES[0]: return floor(TREES[name],-92,52)-.25
    if name == arch.NAMES[1]: return arch.level(y)-28-4.4
    return {arch.NAMES[2]:-3.15,arch.SCENERY[3]:-24,arch.SCENERY[4]:-38,arch.SCENERY[6]:-12.5}[name]


def lava_fill(group):
    name=group.name
    terrain=bpy.data.objects[name]
    collection=arch.coll(name+'_ContainedLava',group)
    vs,fs=[],[]
    area=0
    for p in terrain.data.polygons[:terrain['TerrainFaceCount']]:
        pts=[terrain.data.vertices[k].co.copy() for k in p.vertices]
        # Terrain-plane clipping fills the actual cavity, rather than a guessed
        # narrow ribbon. Full banks and islands mask the buried molten body.
        if any(max(abs(v.x),abs(v.y))>=104 for v in pts): continue
        if name==arch.NAMES[0] and any(abs(v.x+92)>11 or abs(v.y-52)>11 for v in pts): continue
        if name==arch.NAMES[1] and any(v.x<38 for v in pts): continue
        clipped=[]
        for a,b in zip(pts,pts[1:]+pts[:1]):
            da=a.z-lava_height(name,a.x,a.y); db=b.z-lava_height(name,b.x,b.y)
            if da<=0: clipped.append(a)
            if (da<0)!=(db<0): clipped.append(a+(b-a)*(da/(da-db)))
        if len(clipped)<3:continue
        start=len(vs)
        vs.extend((p.x,p.y,lava_height(name,p.x,p.y)+.025) for p in clipped)
        fs.append(tuple(start+k for k in range(len(clipped))))
        area+=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(clipped,clipped[1:]+clipped[:1])))*.5
    if not fs:
        bpy.data.collections.remove(collection)
        REPORT.setdefault('lava',{})[name]={'surface_area':0,'note':'No clipped area; investigate before accepting'}
        return
    ob=arch.mesh('prop_'+name+'_contained_molten_body',vs,fs,collection,[MOLTEN])
    ob.parent=art.root(group);ob['solid']=False
    ob['MoltenSurfaceAreaStuds2']=area
    # Buried depth skirt describes a contained body; walls are authored terrain.
    ob['VisualVolumeDepth']=8
    # Dark crust islands: irregular floating cooled skin over molten pockets,
    # distinctly different from the nearly flush travel surface above the basin.
    if name in arch.SCENERY:
        tree=art.surface_tree(terrain)
        islands=[]
        coords=[(7,-25,10,8),(-24,15,15,7),(30,26,9,13)] if name==arch.SCENERY[3] else [(0,-42,7,13),(6,24,8,10)] if name==arch.SCENERY[4] else [(23,-29,7,6)]
        iv,iff=[],[]
        for j,(cx,cy,rx,ry) in enumerate(coords):
            if floor(tree,cx,cy)>lava_height(name,cx,cy):continue
            s=len(iv)
            shape=[(-1,-.1),(-.7,-.8),(.1,-1),(.8,-.4),(1,.1),(.36,.9),(-.5,.7)]
            for ring in range(2):
                for x,y in shape:
                    px,py=cx+x*rx,cy+y*ry
                    iv.append((px,py,lava_height(name,px,py)+(-.4 if ring==0 else .65+.2*x)))
            iff.append(tuple(s+7+k for k in range(7)))
            iff.extend((s+k,s+(k+1)%7,s+7+(k+1)%7,s+7+k) for k in range(7))
            islands.append((cx,cy))
        island=arch.mesh('prop_'+name+'_crusted_molten_islands',iv,iff,collection,[CRUST])
        island.parent=art.root(group);island['solid']=False
        REPORT.setdefault('lava',{})[name]={'surface_area':round(area,2),'crust_islands':len(islands),'type':'crusted pool' if name==arch.SCENERY[3] else 'stepped ravine river' if name==arch.SCENERY[4] else 'reopened pocket'}
    else:
        REPORT.setdefault('lava',{})[name]={'surface_area':round(area,2),'type':'sloping cooled-flow channel' if name==arch.NAMES[1] else 'shallow peripheral pool'}
    art.propagate(group,collection)


def flora_edge_heat():
    # Keep the approved spectrum/geometry. Touch only the existing derived front,
    # replacing a uniform plane-like split with small branching incursions.
    for ratio in (30,50,70):
        ob=bpy.data.objects['prop_partial_rosette_'+str(ratio)]
        attr=ob.data.color_attributes.get('TakeoverTissue')
        vs=[tuple(v.co) for v in ob.data.vertices]
        fs=[tuple(p.vertices) for p in ob.data.polygons]
        indices=[p.material_index for p in ob.data.polygons]
        mats=list(ob.data.materials)
        oldcolors=[tuple(c.color) for c in attr.data]
        heatindex=next(k for k,m in enumerate(mats) if m.name=='Ember_TissueHeat')
        charindex=next(k for k,m in enumerate(mats) if m.name=='Ember_InvasiveGrowth')
        # Small warm branching lesions where invasion meets pale tissue. Six short
        # intervals, not an all-over luminous leaf or a point light per plant.
        for j,a in enumerate((.78,1.22,4.82)):
            pts=[]
            for t in (.40,.50,.60,.70):
                r=3*t
                ang=a+.08*math.sin(t*11+j)
                pts.append((r*math.cos(ang),r*math.sin(ang),.25+2.1*math.sin(t*1.9)+.18))
            cont.tube(vs,fs,indices,pts,.040,charindex)
            cont.tube(vs,fs,indices,[(x+.023,y-.012,z+.027) for x,y,z in pts[1:]],.012,heatindex)
        new=bpy.data.meshes.new(ob.name+'_advancing_boundary')
        new.from_pydata(vs,[],fs)
        for m in mats:new.materials.append(m)
        for p,k in zip(new.polygons,indices):p.material_index=k;p.use_smooth=True
        color=new.color_attributes.new(name='TakeoverTissue',type='FLOAT_COLOR',domain='CORNER')
        for k,c in enumerate(color.data):c.color=oldcolors[k] if k<len(oldcolors) else (.01,.01,.008,1)
        cont.remap(ob.data,new)


def scene_feature(scene,name):
    return next(o for o in scene.objects if o.get('TerrainFaceCount') and o.parent and o.parent.get('AssetCollection')==name)


def feature_camera(scene,name,label,offset,target):
    ob=scene_feature(scene,name)
    root=ob.parent
    a=math.radians(root.get('AuthoredQuarterTurn',0));cs,sn=math.cos(a),math.sin(a)
    x,y=target[0],target[1]
    pos=root.location+Vector((cs*x-sn*y,sn*x+cs*y,target[2]))
    if name in arch.SCENERY:pos.z+=arch.level(pos.y)-root.location.z
    eye=pos+Vector((cs*offset[0]-sn*offset[1],sn*offset[0]+cs*offset[1],offset[2]))
    group=next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
    return arch.camera('lava_review_'+label,eye,pos,group,40)


def render(stage):
    scene=bpy.data.scenes['Architecture_A'];bpy.context.window.scene=scene
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.cycles.samples=32
    views=[('lava_pool',arch.SCENERY[3],(138,-146,116),(11,3,-10)),
           ('lava_ravine',arch.SCENERY[4],(104,-117,105),(0,-3,-21))]
    cams=[]
    for label,name,offset,target in views:
        cam=feature_camera(scene,name,label,offset,target);cams.append((label,cam))
    if stage=='after':
        for ob in list(bpy.data.objects):
            if ob.type=='CAMERA' and ob.name.startswith('lava_review_'):
                bpy.data.objects.remove(ob,do_unlink=True)
        cams=[]
        for label,name,offset,target in views:
            cams.append((label,feature_camera(scene,name,label,offset,target)))
        group=next(c for c in scene.collection.children[0].children if c.name.startswith('Cameras_Lights'))
        for label,eye,target,lens in [
            ('overall',(650,-760,560),(40,125,34),40),
            ('route_no_rails',(-6,-159,4.5),(0,-88,10),28),
            ('seam_player',(-65,-146,5.7),(-47,-88,12),28),
            ('raised_seam',(3,357,60.5),(-12,427,65),28),
            ('raised_scenery',(-111,223,60.5),(-172,270,67),28),
            ('meso_shelves',(26,274,63),(68,318,73),36),
            ('stable_combat',(0,203,60.5),(0,280,59),30)]:
            cams.append((label,arch.camera('lava_review_'+label,eye,target,group,lens)))
        bpy.context.view_layer.update()
        plant=next(o for o in scene.objects if o.name.startswith('prop_path_column_pass_takeover_50'))
        aim=plant.matrix_world.translation+Vector((0,0,1.7))
        cams.append(('flora_midpoint',arch.camera('lava_review_flora_midpoint',aim+Vector((6,-9,6)),aim,group,50)))
        plant=next(o for o in scene.objects if o.name.startswith('prop_cap_collapsed_pass_takeover_CHARRED'))
        aim=plant.matrix_world.translation+Vector((0,0,2))
        cams.append(('flora_inner_heat',arch.camera('lava_review_flora_inner_heat',aim+Vector((6,-9,6)),aim,group,50)))
    for label,cam in cams:
        scene.camera=cam;scene.render.filepath=str(IMAGES/(stage+'_'+label+'.png'))
        bpy.ops.render.render(write_still=True)
    if stage=='after':
        stored=[]
        for mat in bpy.data.materials:
            if not mat.use_nodes:continue
            if mat.name not in ('Ember_Molten','Ember_DeepHeat','Ember_FreshBreakHeat','Ember_TissueHeat','Ember_ContainedMolten'):continue
            bs=mat.node_tree.nodes.get('Principled BSDF')
            if bs:
                stored.append((bs,bs.inputs['Emission Strength'].default_value))
                bs.inputs['Emission Strength'].default_value=0
        lights=[(o.data,o.data.energy) for o in scene.objects if o.type=='LIGHT' and o.data.type=='POINT']
        for light,energy in lights:light.energy=0
        scene.camera=dict(cams)['overall'];scene.render.filepath=str(IMAGES/'after_overall_glow_minimized.png')
        bpy.ops.render.render(write_still=True)
        for bs,value in stored:bs.inputs['Emission Strength'].default_value=value
        for light,energy in lights:light.energy=energy
        scene.camera=dict(cams)['overall']


def retopo_cavity(ob):
    """Refine only inland cavity edges, keeping every existing vertex indexed."""
    old=ob.data; count=ob['TerrainFaceCount'];name=cont.home(ob)
    vs=[tuple(v.co) for v in old.vertices]
    mids={}; slot=len(old.materials)
    for p in old.polygons[:count]:
        for a,b in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):
            va,vb=old.vertices[a].co,old.vertices[b].co
            xa,ya=cont.canonical(ob,va.x,va.y);xb,yb=cont.canonical(ob,vb.x,vb.y)
            if max(abs(xa),abs(ya),abs(xb),abs(yb))>=104:continue
            if min(va.z-source_height_offset(ob,va.y),vb.z-source_height_offset(ob,vb.y))>1:continue
            key=tuple(sorted((a,b)))
            if key in mids:continue
            p=(va+vb)*.5;x,y=cont.canonical(ob,p.x,p.y)
            p.z=target_height(name,x,y)+source_height_offset(ob,p.y)
            mids[key]=len(vs);vs.append(tuple(p))
    faces=[];materials=[]
    for p in old.polygons[:count]:
        ids=list(p.vertices);edges=[mids.get(tuple(sorted((a,b)))) for a,b in zip(ids,ids[1:]+ids[:1])]
        if all(k is not None for k in edges):
            a,b,c=ids;ab,bc,ca=edges
            new=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
        elif any(k is not None for k in edges):
            perimeter=[]
            for a,k in zip(ids,edges):
                perimeter.append(a)
                if k is not None:perimeter.append(k)
            center=sum((Vector(vs[k]) for k in ids),Vector())/len(ids)
            x,y=cont.canonical(ob,center.x,center.y)
            center.z=target_height(name,x,y)+source_height_offset(ob,center.y)
            ci=len(vs);vs.append(tuple(center))
            new=[(a,b,ci) for a,b in zip(perimeter,perimeter[1:]+perimeter[:1])]
        else:new=[tuple(ids)]
        faces.extend(new);materials.extend([p.material_index]*len(new))
    newcount=len(faces)
    faces.extend(tuple(p.vertices) for p in old.polygons[count:])
    materials.extend(p.material_index for p in old.polygons[count:])
    data=bpy.data.meshes.new(old.name+'_local_fracture_support')
    data.from_pydata(vs,[],faces)
    for mat in old.materials:data.materials.append(mat)
    data.materials.append(bpy.data.materials['Ember_ScorchedStrata'])
    data.update()
    for p,m in zip(data.polygons,materials):
        p.material_index=m;p.use_smooth=True
        if p.index<newcount:
            center=p.center;x,y=cont.canonical(ob,center.x,center.y)
            if center.z-source_height_offset(ob,center.y)<-7 and abs(p.normal.z)<.88:
                p.use_smooth=False
                if p.index%4==0:p.material_index=slot
    color=data.color_attributes.new(name='EmberGroundTint',type='FLOAT_COLOR',domain='CORNER')
    oldcolor=old.color_attributes.get('EmberGroundTint')
    for newp,oldp in zip(data.polygons[newcount:],old.polygons[count:]):
        for ni,oi in zip(newp.loop_indices,oldp.loop_indices):
            color.data[ni].color=oldcolor.data[oi].color if oldcolor else (1,1,1,1)
    ob.data=data;ob['TerrainFaceCount']=newcount
    cont.recolor(ob,2)


def rebuild_molten_body(ob,terrain):
    name=cont.home(ob);vs=[];faces=[];area=0
    def height(p):
        x,y=cont.canonical(terrain,p.x,p.y)
        return lava_height(name,x,y)+source_height_offset(terrain,p.y)
    cache={}
    def vertex(p):
        key=(round(p.x,5),round(p.y,5))
        if key not in cache:
            cache[key]=len(vs);vs.append((p.x,p.y,height(p)+.025))
        return cache[key]
    for poly in terrain.data.polygons[:terrain['TerrainFaceCount']]:
        pts=[terrain.data.vertices[k].co.copy() for k in poly.vertices]
        canonical=[cont.canonical(terrain,p.x,p.y) for p in pts]
        if any(max(abs(x),abs(y))>=104 for x,y in canonical):continue
        if name==arch.NAMES[0] and any(abs(x+92)>11 or abs(y-52)>11 for x,y in canonical):continue
        if name==arch.NAMES[1] and any(x<38 for x,y in canonical):continue
        clipped=[]
        for a,b in zip(pts,pts[1:]+pts[:1]):
            da,db=a.z-height(a),b.z-height(b)
            if da<=0:clipped.append(a)
            if (da<0)!=(db<0):clipped.append(a+(b-a)*(da/(da-db)))
        if len(clipped)<3:continue
        ids=[vertex(p) for p in clipped]
        if len(set(ids))<3:continue
        faces.append(tuple(ids))
        area+=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(clipped,clipped[1:]+clipped[:1])))*.5
    n=len(vs);tops=list(faces)
    edges={}
    for face in tops:
        for a,b in zip(face,face[1:]+face[:1]):
            key=tuple(sorted((a,b)));edges.setdefault(key,[]).append((a,b))
    vs.extend((x,y,z-8) for x,y,z in list(vs))
    faces.extend(tuple(k+n for k in reversed(face)) for face in tops)
    for pairs in edges.values():
        if len(pairs)==1:
            a,b=pairs[0];faces.append((a,b,b+n,a+n))
    data=bpy.data.meshes.new(ob.name+'_contained_depth')
    data.from_pydata(vs,[],faces);data.materials.append(bpy.data.materials['Ember_ContainedMolten'])
    ob.data=data;ob['MoltenSurfaceAreaStuds2']=round(area,2);ob['VisualVolumeDepth']=8
    if ob.name=='prop_'+name+'_contained_molten_body':REPORT['lava'][name]['surface_area']=round(area,2)


def refine_fractures():
    global TREES,REPORT
    REPORT=json.loads((HERE/'lava_geology_technical_report.json').read_text(encoding='utf8'))
    assert not bpy.context.scene.get('LavaFracturesFinished'),'Already finished.'
    # Read only original source surfaces for the intentional field. Never replace
    # the current scene or its existing corrections with this input.
    with bpy.data.libraries.load(str(INPUT),link=False) as (src,dst):dst.objects=arch.NAMES+arch.SCENERY
    TREES={n:art.surface_tree(o) for n,o in zip(arch.NAMES+arch.SCENERY,dst.objects)}
    for ob in dst.objects:bpy.data.objects.remove(ob,do_unlink=True)
    protected={o.name:{v.index:tuple(v.co) for v in o.data.vertices if max(abs(v.co.x),abs(v.co.y))>=104} for o in bpy.data.objects if o.type=='MESH' and o.get('TerrainFaceCount')}
    for ob in list(bpy.data.objects):
        if ob.type=='MESH' and ob.get('TerrainFaceCount') and cont.home(ob) in (arch.SCENERY[3],arch.SCENERY[4],arch.SCENERY[6]):retopo_cavity(ob)
    for ob in list(bpy.data.objects):
        if ob.type!='MESH':continue
        if '_contained_molten_body' in ob.name:
            terrain=next(o for o in ob.parent.users_collection[0].all_objects if o.get('TerrainFaceCount')) if ob.parent else bpy.data.objects[cont.home(ob)]
            rebuild_molten_body(ob,terrain)
        elif '_crusted_molten_islands' in ob.name:
            name=cont.home(ob)
            # Lower the retained crust with its molten surface.
            dz={arch.SCENERY[3]:-8,arch.SCENERY[4]:-10,arch.SCENERY[6]:-4}[name]
            if ob.data.users>1:ob.data=ob.data.copy()
            for v in ob.data.vertices:v.co.z+=dz
    # Local review uplight reflects the contained heat onto the banks. No global
    # light/haze change, no plant torches. Copies follow the existing ring fit.
    for name,positions in [(arch.SCENERY[3],[(-39,2,-20),(51,15,-20)]),(arch.SCENERY[4],[(0,-39,-34),(4,36,-34)])]:
        for scene in [bpy.data.scenes['Independent_Assets_LIBRARY_ONLY']]+[bpy.data.scenes['Architecture_'+s] for s in 'ABC']:
            homes=[]
            if scene.name=='Independent_Assets_LIBRARY_ONLY':homes=[(bpy.data.collections[name],None)]
            else:
                for parent in scene.collection.children[0].children:
                    for group in parent.children:
                        root=art.root(group)
                        if root and root.get('AssetCollection')==name:homes.append((group,root))
            for group,root in homes:
                for x,y,z in positions:
                    if root:
                        a=math.radians(root.get('AuthoredQuarterTurn',0));cs,sn=math.cos(a),math.sin(a)
                        x,y=cs*x-sn*y,sn*x+cs*y;z+=arch.level(root.location.y+y)-root.location.z
                    light=bpy.data.lights.new('review_contained_lava_uplight','POINT');light.energy=9000;light.color=(1,.19,.035);light.shadow_soft_size=12
                    ob=bpy.data.objects.new('review_contained_lava_uplight',light);group.objects.link(ob);ob.parent=root;ob.location=(x,y,z);ob['ReviewOnly']=True
    REPORT['seam_band_exact_after_fractures']=all(tuple(bpy.data.objects[n].data.vertices[k].co)==v for n,rows in protected.items() for k,v in rows.items())
    assert REPORT['seam_band_exact_after_fractures']
    for s in bpy.data.scenes:s['LavaFracturesFinished']=True
    render('after')
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN));bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after']={s.name:art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['assets']={n:arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    REPORT['materials_saved']=len(bpy.data.materials)
    REPORT['source_max_mesh_triangles']=max(t for a in REPORT['assets'].values() for t in a['mesh_triangles'].values())
    REPORT['fracture_topology_note']='Locally split inland cavity edges; old vertices retained; sharp selected strata faces. Lower visible lava exposes intermediate ledges; molten bodies have actual eight-stud buried depth.'
    (HERE/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    (IMAGES/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('FRACTURES_FINISHED',REPORT['after']);print('LAVA_FILLS',REPORT['lava'])


def finalize_review():
    global REPORT
    REPORT=json.loads((HERE/'lava_geology_technical_report.json').read_text(encoding='utf8'))
    assert not bpy.context.scene.get('LavaGeologyFinalReview'),'Final review already saved.'
    # Coherent geological bands, not the initial alternating face swatches.
    for ob in bpy.data.objects:
        if ob.type!='MESH' or not ob.get('TerrainFaceCount'):continue
        name=cont.home(ob)
        if name in (arch.SCENERY[3],arch.SCENERY[4],arch.SCENERY[6]):
            scorch=next(k for k,m in enumerate(ob.data.materials) if m.name=='Ember_ScorchedStrata')
            low,high={arch.SCENERY[3]:(-22,-19),arch.SCENERY[4]:(-33,-29),arch.SCENERY[6]:(-12,-10)}[name]
            for p in ob.data.polygons[:ob['TerrainFaceCount']]:
                h=p.center.z-source_height_offset(ob,p.center.y)
                p.material_index=scorch if low<h<high and abs(p.normal.z)<.88 else 0
        if name in arch.NAMES:
            # Selective sharper shoulder fractures, while retaining smooth broad
            # ash surfaces and every central walking vertex.
            for p in ob.data.polygons[:ob['TerrainFaceCount']]:
                if all(abs(ob.data.vertices[k].co.x)>36 and max(abs(ob.data.vertices[k].co.x),abs(ob.data.vertices[k].co.y))<100 for k in p.vertices) and abs(p.normal.z)<.94:
                    p.use_smooth=False
    seated=0;trees={}
    for ob in bpy.data.objects:
        if ob.type!='MESH' or not ob.get('LibraryAsset'):continue
        name=cont.home(ob)
        if not name:continue
        ground=next(o for o in ob.parent.users_collection[0].all_objects if o.get('TerrainFaceCount')) if ob.parent else bpy.data.objects[name]
        if ground.name not in trees:trees[ground.name]=art.surface_tree(ground)
        z=floor(trees[ground.name],ob.location.x,ob.location.y)+.03
        if abs(z-ob.location.z)>.4:
            ob.location.z=z;seated+=1
    # Cheap measured floor samples in all five central route areas. No collision
    # matrix or automated traversal; cooked Studio collision remains untested.
    REPORT['central_floor_samples']={}
    for name in arch.NAMES:
        tree=art.surface_tree(bpy.data.objects[name]);rows=[]
        for x in (-20,0,20):
            for y in (-64,0,64):
                hit,normal,_,_=tree.ray_cast(Vector((x,y,300)),Vector((0,0,-1)))
                rows.append({'xy':[x,y],'height':hit.z,'slope_degrees':math.degrees(math.acos(min(1,abs(normal.z))))})
        REPORT['central_floor_samples'][name]=rows
    # Compare original central vertices against the actual saved input.
    with bpy.data.libraries.load(str(INPUT),link=False) as (src,dst):dst.objects=list(arch.NAMES)
    REPORT['central_route_vertices_exact']={}
    for name,old in zip(arch.NAMES,dst.objects):
        current=bpy.data.objects[name]
        ids={k for p in old.data.polygons[:old['TerrainFaceCount']] for k in p.vertices if abs(old.data.vertices[k].co.x)<=28}
        REPORT['central_route_vertices_exact'][name]=all(tuple(old.data.vertices[k].co)==tuple(current.data.vertices[k].co) for k in ids)
        bpy.data.objects.remove(old,do_unlink=True)
    assert all(REPORT['central_route_vertices_exact'].values())
    REPORT['flora_anchors_reseated']=seated
    REPORT['material_review_note']='Alternating fracture swatches replaced by continuous exposed strata bands; selected wall/shoulder fractures sharpened without random displacement.'
    for s in bpy.data.scenes:s['LavaGeologyFinalReview']=True
    render('after')
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN));bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after']={s.name:art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['visible_meshes']={s.name:sum(o.type=='MESH' and not o.hide_render for o in s.objects) for s in bpy.data.scenes}
    REPORT['assets']={n:arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    REPORT['materials_saved']=len(bpy.data.materials)
    REPORT['source_max_mesh_triangles']=max(t for a in REPORT['assets'].values() for t in a['mesh_triangles'].values())
    (HERE/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    (IMAGES/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('FINAL_REVIEW_SAVED',REPORT['after'])


def bank_heat_review():
    global REPORT
    REPORT=json.loads((HERE/'lava_geology_technical_report.json').read_text(encoding='utf8'))
    assert bpy.context.scene.get('LavaGeologyFinalReview'),'Finish saved art review first.'
    assert not bpy.context.scene.get('LavaBankHeatReviewed'),'Bank/heat review already saved.'
    trees={};moved=0
    for ob in bpy.data.objects:
        if ob.type!='MESH' or not ob.get('LibraryAsset'):continue
        name=cont.home(ob)
        if name not in (arch.SCENERY[3],arch.SCENERY[4],arch.SCENERY[6]):continue
        ground=next(o for o in ob.parent.users_collection[0].all_objects if o.get('TerrainFaceCount')) if ob.parent else bpy.data.objects[name]
        if ground.name not in trees:trees[ground.name]=art.surface_tree(ground)
        tree=trees[ground.name]
        x,y=cont.canonical(ob,ob.location.x,ob.location.y)
        water=lava_height(name,x,y)+source_height_offset(ground,ob.location.y)
        if ob.location.z>water+.75:continue
        center=11 if name==arch.SCENERY[3] else 28 if name==arch.SCENERY[6] else 0
        sign=1 if x>=center else -1
        angle=math.radians(ob.parent.get('AuthoredQuarterTurn',0)) if ob.parent and name in arch.SCENERY else 0
        cs,sn=math.cos(angle),math.sin(angle)
        for step in range(1,10):
            nx=max(-100,min(100,x+sign*step*8));ny=y
            lx,ly=cs*nx-sn*ny,sn*nx+cs*ny
            z=floor(tree,lx,ly)
            if z>lava_height(name,nx,ny)+source_height_offset(ground,ly)+.75:
                ob.location=(lx,ly,z+.03);moved+=1;break
    REPORT['flora_moved_to_dry_banks']=moved
    scene=bpy.data.scenes['Architecture_A'];bpy.context.window.scene=scene
    scene.cycles.samples=32;scene.render.resolution_x=1200;scene.render.resolution_y=800
    for label in ('lava_pool','lava_ravine','overall'):
        scene.camera=bpy.data.objects['lava_review_'+label]
        scene.render.filepath=str(IMAGES/('after_'+label+'.png'));bpy.ops.render.render(write_still=True)
    # Stronger no-heat diagnostic: temporarily darken molten/heat base color too,
    # so the answer cannot rely on bright orange diffuse color without emission.
    saved=[];links=[]
    for mat in bpy.data.materials:
        if mat.name not in ('Ember_Molten','Ember_DeepHeat','Ember_FreshBreakHeat','Ember_TissueHeat','Ember_ContainedMolten'):continue
        node=mat.node_tree.nodes.get('Principled BSDF')
        saved.append((node,tuple(node.inputs['Base Color'].default_value),node.inputs['Emission Strength'].default_value))
        for link in list(node.inputs['Base Color'].links):
            links.append((mat.node_tree,link.from_socket,link.to_socket));mat.node_tree.links.remove(link)
        node.inputs['Base Color'].default_value=(.017,.022,.025,1);node.inputs['Emission Strength'].default_value=0
    lights=[(o.data,o.data.energy) for o in scene.objects if o.type=='LIGHT' and o.data.type=='POINT']
    for light,power in lights:light.energy=0
    scene.camera=bpy.data.objects['lava_review_overall'];scene.render.filepath=str(IMAGES/'after_overall_glow_minimized.png');bpy.ops.render.render(write_still=True)
    for node,color,strength in saved:
        node.inputs['Base Color'].default_value=color;node.inputs['Emission Strength'].default_value=strength
    for tree,start,end in links:tree.links.new(start,end)
    for light,power in lights:light.energy=power
    REPORT['heat_diagnostic_restored']=all(tuple(node.inputs['Base Color'].default_value)==color and node.inputs['Emission Strength'].default_value==strength for node,color,strength in saved) and all(light.energy==power for light,power in lights)
    assert REPORT['heat_diagnostic_restored']
    for s in bpy.data.scenes:s['LavaBankHeatReviewed']=True
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN));bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after']={s.name:art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['assets']={n:arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    (HERE/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    (IMAGES/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('BANK_HEAT_REVIEW_SAVED',moved,REPORT['after'])


def main():
    global arch,art,cont,TREES,CRUST,MOLTEN
    IMAGES.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    arch=load('revise_emberfall_architecture.py','lava_arch')
    art=load('refine_emberfall_identity.py','lava_art');art.study=arch
    cont=load('refine_emberfall_continuity.py','lava_cont');cont.arch=arch;cont.art=art
    if '--bank-heat-review' in sys.argv:
        bank_heat_review();return
    if '--finalize-review' in sys.argv:
        finalize_review();return
    if '--finish-fractures' in sys.argv:
        refine_fractures();return
    if '--review-only' in sys.argv:
        render('after');return
    assert not bpy.context.scene.get('LavaGeologyRefined'),'Already refined; use review-only.'
    if not INPUT.exists():shutil.copy2(MAIN,INPUT)
    REPORT['before']={s.name:art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['input']=str(INPUT)
    render('before')
    bpy.context.window.scene=bpy.data.scenes['Independent_Assets_LIBRARY_ONLY']
    TREES={n:art.surface_tree(bpy.data.objects[n]) for n in arch.NAMES+arch.SCENERY}
    protected={o.name:{v.index:tuple(v.co) for v in o.data.vertices if max(abs(v.co.x),abs(v.co.y))>=104} for o in bpy.data.objects if o.type=='MESH' and o.get('TerrainFaceCount')}
    roots={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type=='EMPTY'}
    originals=['prop_drained_wax_rosette','prop_drained_seed_shrub','prop_charred_ember_rose','prop_charred_thorn_pod']
    flora={n:arch.fingerprint(bpy.data.objects[n].data) for n in originals}
    CRUST=bpy.data.materials['Ember_BrokenCrust']
    MOLTEN=art.make_material('Ember_ContainedMolten',(.62,.06,.006),.72,1.6)
    nodes=MOLTEN.node_tree.nodes;links=MOLTEN.node_tree.links
    tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.18;tex.inputs['Detail'].default_value=2
    coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Object'],tex.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(.13,.008,.003,1)
    ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.9,.28,.018,1)
    mid=ramp.color_ramp.elements.new(.54);mid.color=(.57,.065,.005,1)
    links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
    bs=nodes.get('Principled BSDF');links.new(ramp.outputs['Color'],bs.inputs['Base Color']);links.new(ramp.outputs['Color'],bs.inputs['Emission Color'])
    debug_geometry()
    edit_foundations()
    for name in arch.NAMES+arch.SCENERY:integrate_crust(bpy.data.collections[name])
    for name in [arch.NAMES[0],arch.NAMES[1],arch.NAMES[2],arch.SCENERY[3],arch.SCENERY[4],arch.SCENERY[6]]:
        lava_fill(bpy.data.collections[name])
    flora_edge_heat()
    REPORT['seam_band_exact']=all(tuple(bpy.data.objects[n].data.vertices[k].co)==v for n,rows in protected.items() for k,v in rows.items())
    REPORT['placement_matrices_exact']=all([list(r) for r in bpy.data.objects[n].matrix_world]==rows for n,rows in roots.items())
    REPORT['original_flora_exact']=flora=={n:arch.fingerprint(bpy.data.objects[n].data) for n in originals}
    assert REPORT['seam_band_exact'] and REPORT['placement_matrices_exact'] and REPORT['original_flora_exact']
    for scene in bpy.data.scenes:scene['LavaGeologyRefined']=True
    render('after')
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN))
    bpy.ops.wm.open_mainfile(filepath=str(MAIN))
    REPORT['after']={s.name:art.digest_scene(s) for s in bpy.data.scenes}
    REPORT['visible_meshes']={s.name:sum(o.type=='MESH' and not o.hide_render for o in s.objects) for s in bpy.data.scenes}
    REPORT['assets']={n:arch.count_collection(bpy.data.collections[n]) for n in arch.NAMES+arch.SCENERY}
    REPORT['origins_bounds_elevations']={n:{'origin':list(bpy.data.objects[n].location),'bounds':arch.bounds(bpy.data.objects[n]),'entry':bpy.data.objects[n].get('EntryElevationLocal'),'exit':bpy.data.objects[n].get('ExitElevationLocal')} for n in arch.NAMES+arch.SCENERY}
    REPORT['collision_note']='Retained broad central corridors/hub, PATH fringe minimum -6. Visual shoulder shelves and lava banks need simplified nonsolid art over later walk colliders; Studio untested.'
    REPORT['materials_saved']=len(bpy.data.materials)
    (HERE/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    (IMAGES/'lava_geology_technical_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf8')
    print('LAVA_GEOLOGY_SAVED',REPORT['after'])
    print('LAVA_FILLS',REPORT['lava'])


if __name__=='__main__':main()
