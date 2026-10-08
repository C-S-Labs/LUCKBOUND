"""Bounded socket/yaw probe using the actual ChunkCore; no production changes."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path('E:/BlenderAIProjects/Runtime/Emberfall_ModularityReview')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/shared/Util/ChunkCore.luau').read_text(encoding='utf8')
    # These numerical helpers never call WeightedRandom. Preserve their source
    # exactly; supply only the unused dependency outside the Roblox environment.
    source = source.replace('local WeightedRandom = require(script.Parent.WeightedRandom)', 'local WeightedRandom = {}')
    harness = '''
local function socket(id, z, y, facing)
 return {Id=id,Kind="AREA_I_REVIEW",OffsetX=0,OffsetY=y,OffsetZ=z,Facing=facing,Width=24}
end
local function hill(y)
 local t=math.clamp((y+384)/768,0,1)
 return 56*t*t*(3-2*t)
end
local defs={}
for i, y in {-256,0,256} do
 local north=socket("forward",-128,hill(y+128)-hill(y),0)
 local south=socket("back",128,hill(y-128)-hill(y),180)
 defs[i]={Id="REVIEW_"..i,Role="PATH",SizeX=256,SizeZ=256,
 Sockets=if i==2 then {north,south} else {south,north}}
end
local p={{ChunkId=defs[1].Id,Role="PATH",Index=1,X=0,Y=hill(-256),Z=256,Yaw=0}}
for i=2,3 do
 local previous=defs[i-1]
 local exit=previous.Sockets[2]
 local open=Core.worldSocket(p[i-1],previous,exit)
 local placed, consumed=Core.placeAgainst(defs[i],open,i)
 assert(placed and consumed)
 local joined=Core.worldSocket(placed,defs[i],consumed)
 assert(math.abs(open.X-joined.X)+math.abs(open.Y-joined.Y)+math.abs(open.Z-joined.Z)<1e-8)
 assert((open.Facing-joined.Facing)%360==180)
 assert(not Core.overlaps(p[i-1],previous,placed,defs[i]))
 table.insert(p,placed)
end
local lines={}
for i,v in p do
 table.insert(lines,string.format('{"index":%d,"x":%.12f,"y":%.12f,"z":%.12f,"yaw":%d}',i,v.X,v.Y,v.Z,v.Yaw))
end
local expected={{7,-117},{135,11},{7,139},{-121,11}}
for i,yaw in {0,90,180,270} do
 local v={X=7,Y=3,Z=11,Yaw=yaw}
 local s=socket("check",-128,13,0)
 local w=Core.worldSocket(v,defs[1],s)
 assert(w.Y==16 and w.Facing==yaw)
 assert(w.X==expected[i][1] and w.Z==expected[i][2])
 assert(Core.yawRadians(yaw)==-math.rad(yaw))
end
print('{"source":"actual ChunkCore.placeAgainst/worldSocket/overlaps/yawRadians",'..
 '"placements":['..table.concat(lines,",")..'],"quarter_turns_checked":[0,90,180,270],"socket_pairs":2}')
'''
    script = OUT / 'socket_probe.luau'
    script.write_text('local Core=(function()\n' + source + '\nend)()\n' + harness, encoding='utf8')
    result = subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe', str(script)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert [p['yaw'] for p in data['placements']] == [0, 180, 0]
    (OUT / 'socket_layout.json').write_text(json.dumps(data, indent=2), encoding='utf8')
    print(json.dumps(data))


if __name__ == '__main__':
    main()
