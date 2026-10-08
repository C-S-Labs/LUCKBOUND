"""Five-piece return-route probe using real ChunkCore, isolated from content."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ProductionGateReview')


def main():
    source = (ROOT/'src/shared/Util/ChunkCore.luau').read_text(encoding='utf8')
    source = source.replace('local WeightedRandom = require(script.Parent.WeightedRandom)', 'local WeightedRandom = {}')
    harness = '''
local function h(y)
 local t=math.clamp((y+384)/768,0,1)
 return 56*t*t*(3-2*t)
end
local centers={-256,0,0,0,256}
local defs={}
for i,y in centers do
 local incoming={Id="arrival",Kind="AREA_I_GATE_PROBE",OffsetX=0,OffsetZ=128,OffsetY=h(y-128)-h(y),Facing=180,Width=24}
 local bend=i==2 or i==4
 local outgoing={Id="departure",Kind="AREA_I_GATE_PROBE",OffsetX=if bend then 128 else 0,OffsetZ=if bend then 0 else -128,OffsetY=h(y+128)-h(y),Facing=if bend then 90 else 0,Width=24}
 defs[i]={Id="GATE_PROBE_"..i,Role="PATH",SizeX=256,SizeZ=256,Sockets={incoming,outgoing}}
end
local placed={{ChunkId=defs[1].Id,Role="PATH",X=0,Y=h(-256),Z=256,Yaw=0,Index=1}}
local connections={}
for i=2,5 do
 local open=Core.worldSocket(placed[i-1],defs[i-1],defs[i-1].Sockets[2])
 local p,s=Core.placeAgainst(defs[i],open,i)
 assert(p and s)
 local arrive=Core.worldSocket(p,defs[i],s)
 assert(math.abs(open.X-arrive.X)+math.abs(open.Y-arrive.Y)+math.abs(open.Z-arrive.Z)<1e-7)
 assert((open.Facing-arrive.Facing)%360==180)
 for j,q in placed do assert(not Core.overlaps(q,defs[j],p,defs[i])) end
 table.insert(placed,p)
 table.insert(connections,string.format('{"from":%d,"to":%d,"x":%.12f,"y":%.12f,"z":%.12f}',i-1,i,open.X,open.Y,open.Z))
end
local rows={}
for i,p in placed do
 table.insert(rows,string.format('{"index":%d,"x":%.12f,"y":%.12f,"z":%.12f,"yaw":%d,"source_center_y":%d,"bend":%s}',i,p.X,p.Y,p.Z,p.Yaw,centers[i],tostring(i==2 or i==4)))
end
print('{"placements":['..table.concat(rows,",")..'],"connections":['..table.concat(connections,",")..'],"source":"actual ChunkCore helpers; isolated review definitions"}')
'''
    OUT.mkdir(parents=True,exist_ok=True)
    script=OUT/'return_route_probe.luau'
    script.write_text('local Core=(function()\n'+source+'\nend)()\n'+harness,encoding='utf8')
    result=subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe',str(script)],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    data=json.loads(result.stdout)
    assert [p['yaw'] for p in data['placements']]==[0,0,90,90,180]
    assert data['placements'][0]['z']==data['placements'][-1]['z']
    (OUT/'return_layout.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    print('RETURN_ROUTE_SOCKET_PROBE_PASS',json.dumps(data['placements']))


if __name__=='__main__':
    main()
