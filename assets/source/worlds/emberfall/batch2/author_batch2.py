"""Approved Batch2 source authoring. Run through tools/run_blender.py only.

First-three gate is separate from remaining authoring; accepted Batch1 is read-only.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'batch1'))
import batch1_shared as sh
from countryside import road, fence, timber

OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')


def bump(x, y, cx, cy, rx, ry):
    return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)


def bend(sign, late):
    # Exact straight forty-stud mouth approaches, distinct interior turn timing.
    p0, p3 = (0, -88), (sign*88, 0)
    p1 = (0, -8 if late else -66)
    p2 = (sign*(25 if late else 76), 0)
    guide = [(0, -128+4*i) for i in range(10)]
    for i in range(49):
        t=i/48; u=1-t
        guide.append(tuple(u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1)))
    guide.extend((sign*(88+4*i), 0) for i in range(1,11))
    return guide


def quiet_land(x,y):
    return (6*bump(x,y,64,26,68,83)-2.3*bump(x,y,-38,-8,50,56)
            +1.2*bump(x,y,-58,78,73,47)+.45*math.sin(x/48)*math.sin(y/57))


def pasture_land(x,y):
    return (4*bump(x,y,-59,51,67,70)-1.6*bump(x,y,44,-30,62,61)
            +.7*math.sin((x+y)/68))


def shoulder_land(x,y):
    return (3.2*bump(x,y,-59,26,82,69)-2.1*bump(x,y,57,-22,27,76)
            +.65*math.sin(y/54)*math.sin(x/78))


def quiet(ctx):
    road(ctx)
    for x,y,h in [(69,64,26),(86,73,20),(77,92,23)]:ctx.tree(x,y,h,style='pasture')
    ctx.refuge(-38,18,39,52,.55,'Shallow damp lee beneath ordinary outside grass bank')
    ctx.rock(83,-64,1.25)


def pasture(ctx):
    road(ctx)
    for x,y,h in [(-76,68,24),(-93,58,20)]:ctx.tree(x,y,h,style='pasture')
    ctx.refuge(-42,42,42,38,.48,'Raised meadow lee behind low rounded shoulder')
    ctx.rock(-64,-42,1.5)


def shoulder(ctx):
    road(ctx)
    for x,y,h in [(63,37,24),(79,45,20),(71,63,18)]:ctx.tree(x,y,h,style='lee')
    ctx.refuge(57,0,23,65,.55,'Shallow side drainage softens burn below exposed shoulder')
    ctx.rock(-86,61,1.35)


def swale_land(x,y):
    return (6*bump(x,y,-74,16,43,100)+4*bump(x,y,72,-31,51,72)
            -4.2*bump(x,y,0,5,45,61)+.45*math.sin(y/61))


def saddle_land(x,y):
    return (3.5*bump(x,y,-72,-14,72,66)-1.4*bump(x,y,35,22,64,58)
            +.55*math.sin(y/48)*math.cos(x/71))


def ditch_land(x,y):
    channel=44+7*math.sin(y/65)
    return (4.5*bump(x,y,-79,41,65,72)+2*bump(x,y,83,-51,54,72)
            -3.7*math.exp(-((x-channel)/14)**2)*math.exp(-(y/98)**4))


def grove_land(x,y):
    return (4.7*bump(x,y,-61,8,55,87)-2.0*bump(x,y,-21,16,42,70)
            +1.0*bump(x,y,68,-43,77,53))


def fieldstead_land(x,y):
    return (2.4*bump(x,y,-73,58,73,58)+1.4*bump(x,y,74,-60,77,61)
            -.6*bump(x,y,54,13,40,40))


def swale_guide():
    result=[]
    for i in range(65):
        y=-128+i*4;u=(y+88)/176
        x=0 if u<=0 or u>=1 else 22*math.sin(2*math.pi*u)*sh.ec.smooth(min(u,1-u)/.12)
        result.append((x,y))
    return result


def swale(ctx):
    road(ctx)
    for x,y,h in [(-77,31,25),(-88,44,19),(-69,58,21)]:ctx.tree(x,y,h,style='swale')
    ctx.refuge(0,9,37,69,.65,'Damp valley fold retains a coherent thin refuge')


def saddle(ctx):
    road(ctx)
    for x,y,h in [(-84,-53,23),(-95,-34,18)]:ctx.tree(x,y,h,style='pasture')
    for x,y,r in [(78,66,1.8),(83,61,1.1),(-73,44,1.3)]:ctx.rock(x,y,r)
    ctx.refuge(39,36,35,46,.45,'Sheltered lower fold beneath descending pasture')


def ditch(ctx):
    road(ctx)
    ctx.tree(92,74,21,style='drainage')
    ctx.refuge(44,0,16,79,.78,'Longitudinal damp ditch follows field circulation')
    for x,y,r in [(62,-61,1.1),(57,56,1.2)]:ctx.rock(x,y,r)


def grove(ctx):
    road(ctx)
    for x,y,h in [(-39,-39,25),(-61,-25,29),(-47,-10,22),(-69,4,24),(-43,21,27),(-62,38,20),(-37,49,23)]:ctx.tree(x,y,h,style='leeward')
    ctx.refuge(-42,10,36,63,.65,'Irregular overlapping ordinary grove shelters its lee')
    ctx.rock(91,-60,1.35)


def fieldstead(ctx):
    road(ctx)
    # A modest 18x14 shed footprint beside an open yard. No standing house.
    cx,cy=52,18
    for x in range(43,62,4):
        for y in (11,25):ctx.box('Shed_footing',x,y,ctx.ground(x,y)+.55,1.9,.9,.55,sh.bp.STONE)
    for y in (15,19,23):ctx.box('Shed_footing',43,y,ctx.ground(43,y)+.55,.9,1.9,.55,sh.bp.STONE)
    for x,y,h in [(43,11,4.2),(61,25,2.9),(43,25,3.4)]:
        timber(ctx,ctx.box('Shed_broken_upright',x,y,ctx.ground(x,y)+h/2,.27,.3,h/2),(x,y),'post')
    for a,b in [((44,12),(59,21)),((48,23),(62,17)),((51,10),(64,8))]:
        timber(ctx,ctx.beam('Shed_fallen_timber',(*a,ctx.ground(*a)+.4),(*b,ctx.ground(*b)+.4),.24),a,'fallen')
    for x,y,h in [(-82,68,25),(-93,49,19),(83,-61,23)]:ctx.tree(x,y,h,style='field')
    ctx.refuge(53,26,21,25,.6,'Stone footing lee retains weeds beside recently charred timber')
    # Restrained cultivation traces, not a second orchard or settlement street.
    for x in (74,82):
        for y in (-25,-17,-9):ctx.rock(x,y,.65)


def alternative(ctx):
    road(ctx)
    name=ctx.spec['variant_of']
    if name=='EF_QUIET_HOLLOW_BEND':
        ctx.wall([(x,82) for x in range(-53,-22,5)])
        ctx.tree(92,-72,21,style='pasture')
        ctx.refuge(-36,60,35,28,.55,'Short transverse field boundary shelters ordinary grass')
    elif name=='EF_RAISED_PASTURE_BEND':
        fence(ctx,[(-88,52),(-77,61),(-65,68)],True)
        ctx.tree(-84,-76,19,style='pasture')
        ctx.refuge(-44,43,42,38,.48,'Raised meadow lee remains sheltered')
    elif name=='EF_SWALE_DRIFT':
        for x in (69,78):
            for y in range(-74,-34,9):ctx.rock(x,y,.65)
        ctx.refuge(0,9,37,69,.65,'Damp swale continues beside restrained worked-ground remnants')
    elif name=='EF_LONG_DITCH_VERGE':
        for x,y,h in [(77,-37,23),(87,-20,18),(72,-8,21)]:ctx.tree(x,y,h,style='drainage')
        ctx.refuge(44,0,16,79,.78,'Loose bank group frames the same longitudinal damp ditch')


def specifications():
    return [
        (dict(id='EF_QUIET_HOLLOW_BEND',title='Quiet Hollow Bend',purpose='Low-signature late-sweep HOLLOW left connector',seed=2001,edges={'S':('HOLLOW',0),'W':('HOLLOW',0)},land=quiet_land,guide=bend(-1,True),grass_count=3200,signature='LOW'),quiet),
        (dict(id='EF_RAISED_PASTURE_BEND',title='Raised Pasture Bend',purpose='Low-signature early-turn CREST right connector',seed=2002,edges={'S':('CREST',0),'E':('CREST',0)},land=pasture_land,guide=bend(1,False),grass_count=3200,signature='LOW'),pasture),
        (dict(id='EF_LOW_SHOULDER_CLIMB',title='Low Shoulder Climb',purpose='Quiet reversible shallow HOLLOW/CREST conversion',seed=2003,edges={'S':('HOLLOW',0),'N':('CREST',12)},land=shoulder_land,guide=sh.straight(11),grass_count=3200,signature='LOW'),shoulder),
        (dict(id='EF_SWALE_DRIFT',title='Swale Drift',purpose='Quiet shallow S in an open recovery valley',seed=2004,edges={'S':('HOLLOW',0),'N':('HOLLOW',0)},land=swale_land,guide=swale_guide(),grass_count=3200,signature='LOW'),swale),
        (dict(id='EF_PASTURE_SADDLE',title='Pasture Saddle',purpose='Quiet ordinary CREST downhill connector',seed=2005,edges={'S':('CREST',0),'N':('CREST',-8)},land=saddle_land,guide=sh.straight(-10),grass_count=3200,signature='LOW'),saddle),
        (dict(id='EF_LONG_DITCH_VERGE',title='Long Ditch Verge',purpose='Quiet longitudinal drainage-road framing',seed=2006,edges={'S':('HOLLOW',0),'N':('HOLLOW',0)},land=ditch_land,guide=sh.straight(-6),grass_count=3200,signature='LOW'),ditch),
        (dict(id='EF_LEEWARD_GROVE',title='Leeward Grove',purpose='Moderate irregular off-road grove compression/release',seed=2007,edges={'S':('CREST',0),'N':('CREST',0)},land=grove_land,guide=sh.straight(9),grass_count=3200,signature='MEDIUM'),grove),
        (dict(id='EF_ABANDONED_FIELDSTEAD',title='Abandoned Fieldstead',purpose='Rare modest shed footing with open encounter yard',seed=2008,edges={'S':('CREST',0),'N':('CREST',0)},land=fieldstead_land,guide=sh.straight(-8),grass_count=3200,signature='HIGH'),fieldstead),
    ]


def validate(ctx, meta):
    terrain=ctx.terrain
    assert tuple(terrain.location)==(0,0,0)
    assert abs(ctx.ground(0,0))<.0001
    assert abs(terrain.dimensions.x-256)<.001 and abs(terrain.dimensions.y-256)<.001
    error=0; hull_error=0
    vertices=[tuple(v.co) for v in terrain.data.vertices[:4225]]
    for socket in meta['sockets']:
        side=socket['Id'];kind=socket['Kind'].split('_')[-1]
        for across in range(-128,129,2):
            x,y={'S':(across,-128),'N':(across,128),'W':(-128,across),'E':(128,across)}[side]
            error=max(error,abs(sh.ec.surface(vertices,4,x,y)-socket['OffsetY']-sh.ec.profile(kind,across)))
    for obj in [terrain,*ctx.collision.objects]:
        bm=bmesh.new();bm.from_mesh(obj.data)
        assert all(edge.is_manifold for edge in bm.edges),obj.name
        bm.free()
        if obj.get('CollisionFidelity')=='Hull':
            for face in obj.data.polygons:
                hull_error=max(hull_error,max(face.normal.dot(v.co-obj.data.vertices[face.vertices[0]].co) for v in obj.data.vertices))
    assert error<.01 and hull_error<.0001
    boundary=[]
    for side in ('S','N','W','E'):
        connected=side in ctx.spec['edges']
        stations=sorted(set(list(range(-128,129,32))+([-12,12] if connected else [])))
        for a,b in zip(stations,stations[1:]):
            if connected and a>=-12 and b<=12:continue
            xy=lambda t:{'S':(t,-128),'N':(t,128),'W':(-128,t),'E':(128,t)}[side]
            x,y=xy(a);xx,yy=xy(b)
            boundary.append(dict(A=[x,ctx.ground(x,y),-y],B=[xx,ctx.ground(xx,yy),-yy]))
    meta['Boundary']=dict(Height=64,Thickness=2,Segments=boundary)
    meta['signature']=ctx.spec['signature']
    meta['source_checks']=dict(profile_error=error,hull_halfspace_error=hull_error,closed=True,origin=[0,0,0],footprint=[256,256])
    heights=[p[2] for p in meta['guide']]
    meta['road_range']=max(heights)-min(heights)
    meta['road_rise']=heights[-1]-heights[0]
    meta['road_length']=sum(math.dist(a[:2],b[:2]) for a,b in zip(meta['guide'],meta['guide'][1:]))
    meta['max_mesh_triangles']=max(sum(len(p.vertices)-2 for p in o.data.polygons) for o in ctx.c.objects if o.type=='MESH')
    assert meta['max_mesh_triangles']<10000
    meta['objects']-=1;meta['triangles']-=512 if len(ctx.spec['guide'])==65 else 8*(len(ctx.spec['guide'])-1)
    meta['review_road_excluded']=True
    terrain['Boundary']=json.dumps(meta['Boundary']);ctx.scene['Metadata']=json.dumps(meta)
    return meta


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--gate',choices=['A','B'],default='A')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(parents=True,exist_ok=True);sh.init();rows=[]
    selected=specifications()[:3] if args.gate=='A' else specifications()[3:]
    if args.gate=='B':
        rows=json.loads((OUT/'gate_a_sources.json').read_text())
        with bpy.data.libraries.load(str(OUT/'BurnedPlainsBatch2_GateA.blend'),link=False) as (a,b):b.scenes=[r['id'] for r in rows]
        # Preserve GateA exactly; append only five sources and four dressings.
        for spec,dress in specifications():
            if spec['id'] in ('EF_QUIET_HOLLOW_BEND','EF_RAISED_PASTURE_BEND','EF_SWALE_DRIFT','EF_LONG_DITCH_VERGE'):
                variant=dict(spec);variant.update(id=spec['id']+'_DRESSING_B',variant_of=spec['id'],seed=spec['seed']+100,title=spec['title']+' — dressing B')
                selected.append((variant,alternative))
    variants=[]
    for spec,dress in selected:
        ctx,meta=sh.build(spec,dress);bpy.context.view_layer.update();rows.append(validate(ctx,meta))
        if spec.get('variant_of'):
            meta['variant_of']=spec['variant_of'];variants.append(meta);rows.pop()
            original=next(r for r in rows if r['id']==spec['variant_of'])
            assert meta['geometry_sha256']==original['geometry_sha256']
            assert meta['sockets']==original['sockets'] and meta['collision_parts']==original['collision_parts']
            ctx.scene['Metadata']=json.dumps(meta)
        sh.light_scene(ctx.scene)
        ctx.scene.render.resolution_x=1000;ctx.scene.render.resolution_y=700
        sh.render(ctx.scene,OUT/(ctx.id+'_overview.png'))
        x,y=spec['guide'][10];tx,ty=spec['guide'][32]
        sh.render(ctx.scene,OUT/(ctx.id+'_eye.png'),(x,y,ctx.ground(x,y)+5),(tx,ty,ctx.ground(tx,ty)+3))
        sh.render(ctx.scene,OUT/(ctx.id+'_top.png'),(0,0,450),(0,0,0),310)
    stem='gate_a_sources' if args.gate=='A' else 'batch2_sources'
    (OUT/(stem+'.json')).write_text(json.dumps(rows,indent=2))
    (HERE/(stem+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
    if variants:
        (OUT/'batch2_variants.json').write_text(json.dumps(variants,indent=2))
        (HERE/'batch2_variants.json').write_text(json.dumps(variants,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('BurnedPlainsBatch2_GateA.blend' if args.gate=='A' else 'BurnedPlainsBatch2.blend')))
    print('SOURCE_CHECKS',json.dumps([{k:r[k] for k in ['id','triangles','objects','collision_parts','road_length','road_range','road_rise','source_checks']} for r in rows]))


if __name__=='__main__':main()
