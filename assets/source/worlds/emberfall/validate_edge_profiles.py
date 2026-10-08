"""Small deterministic source-mesh/profile validator; not runtime terrain repair."""
import hashlib
import json
import math
from pathlib import Path
from edge_profile_contract import SPECS,DEPTH,TOLERANCE,corner_heights,edge,socket,surface,raw_height

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview')
HERE=Path(__file__).resolve().parent


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def validate(name, payload):
    spec=SPECS[name]; corner_heights(spec)
    assert payload['footprint']==[256,256]
    assert payload['sockets']==[socket(name,s) for s in ('S','W','N','E') if s in spec]
    for key,step in (('visual',4),('collision',8)):
        n=256//step+1;assert len(payload[key])==n*n
        assert abs(surface(payload[key],step,0,0))<TOLERANCE
        for i,(x,y,z) in enumerate(payload[key]):
            assert x==-128+(i%n)*step and y==-128+(i//n)*step
    error=0
    for side in ('S','W','N','E'):
        if side not in spec: continue
        for s in range(-128,129,4):
            x,y={'S':(s,-128),'N':(s,128),'W':(-128,s),'E':(128,s)}[side]
            for key,step in (('visual',4),('collision',8)):
                delta=abs(surface(payload[key],step,x,y)-(edge(spec,side,s)-raw_height(name,0,0)))
                error=max(error,delta)
                assert delta<=TOLERANCE,(name,side,key,s,delta)
    return error


def pose_point(p,x,y,h):
    angle=-math.radians(p['yaw']); c,s=round(math.cos(angle)),round(math.sin(angle))
    return (p['x']+c*x-s*y,-p['z']+s*x+c*y,p['y']+h)


def local_point(p,x,y):
    angle=math.radians(p['yaw']); c,s=round(math.cos(angle)),round(math.sin(angle))
    dx,dy=x-p['x'],y+p['z']
    return c*dx-s*dy,s*dx+c*dy


def run(payloads,layouts):
    source_checks={name:validate(name,p) for name,p in payloads.items()}
    rows=[]
    for label,placements in layouts.items():
        for a,b in zip(placements,placements[1:]):
            sa=payloads[a['name']]['sockets'][-1]; sb=payloads[b['name']]['sockets'][0]
            assert sa['Kind']==sb['Kind']
            center=pose_point(a,sa['OffsetX'],-sa['OffsetZ'],sa['OffsetY'])
            center_b=pose_point(b,sb['OffsetX'],-sb['OffsetZ'],sb['OffsetY'])
            assert max(abs(x-y) for x,y in zip(center,center_b))<=TOLERANCE
            side=sa['Id']; gaps={}; collision_visual=0
            for key,step in (('visual',4),('collision',8)):
                gaps[key]=0
                for s in range(-128,129,2):
                    x,y={'S':(s,-128),'N':(s,128),'W':(-128,s),'E':(128,s)}[side]
                    wx,wy,_=pose_point(a,x,y,0); bx,by=local_point(b,wx,wy)
                    assert max(abs(bx),abs(by))<=128+TOLERANCE
                    ha=surface(payloads[a['name']][key],step,x,y)+a['y']
                    hb=surface(payloads[b['name']][key],step,bx,by)+b['y']
                    gaps[key]=max(gaps[key],abs(ha-hb))
                assert gaps[key]<=TOLERANCE,(label,gaps)
            rows.append({'layout':label,'from':a['name'],'to':b['name'],
                         'rotations':[a['yaw'],b['yaw']],'stations':129,
                         'max_visual_gap_studs':gaps['visual'],'max_collision_gap_studs':gaps['collision'],
                         'bespoke_edits':0,'pass':True})
    deviations={}
    for name,p in payloads.items():
        value=0
        for y in range(-128,129,4):
            for x in range(-128,129,4):
                if min(128-abs(x),128-abs(y))<=DEPTH:
                    value=max(value,abs(surface(p['visual'],4,x,y)-surface(p['collision'],8,x,y)))
        deviations[name]=value
        assert value<.35,(name,'collision approximation',value)
    # A/C touch a third corner on the rising turn. No averaging is permitted.
    poses=layouts['rising_corner']; points=[pose_point(p,*local_point(p,128,128),
              surface(payloads[p['name']]['visual'],4,*local_point(p,128,128))) for p in poses]
    corner_gap=max(p[2] for p in points)-min(p[2] for p in points)
    assert corner_gap<=TOLERANCE,points
    import copy
    failures=[]
    for kind in ('visual','collision','socket'):
        damaged=copy.deepcopy(payloads['B2'])
        if kind=='socket': damaged['sockets'][0]['Width']=25
        else: damaged[kind][0][2]+=.25
        try: validate('B2',damaged)
        except AssertionError: failures.append(kind)
    bad=dict(SPECS['B2']); bad['E']=('CREST',42)
    try: corner_heights(bad)
    except ValueError: failures.append('corner')
    assert len(failures)==4
    return {'tolerance_studs':TOLERANCE,'source_profile_max_error':source_checks,
            'joins':rows,'three_way_corner_gap_studs':corner_gap,
            'max_visual_collision_approximation_in_authored_band':deviations,
            'negative_controls_rejected':failures,'source_mesh_sha256':{n:fingerprint(p) for n,p in payloads.items()},
            'layout_specific_vertex_edits':0,'production_systems_modified':False}


def main():
    payloads=json.loads((OUT/'source_meshes.json').read_text())
    report=run(payloads,json.loads((OUT/'layouts.json').read_text()))
    for p in (OUT/'validation.json',HERE/'edge_profile_report.json'):
        existing=json.loads(p.read_text()) if p.exists() else {}
        p.write_text(json.dumps({**existing,**report},indent=2))
    print('FROZEN_EDGE_COLLISION_PASS',len(report['joins']),'joins; max gap',max(r['max_visual_gap_studs'] for r in report['joins']))


if __name__=='__main__': main()
