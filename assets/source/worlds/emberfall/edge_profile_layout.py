"""Actual ChunkCore placement, frozen edge specs, alternate neighbours/rotations."""
import json
import subprocess
from pathlib import Path
from edge_profile_contract import SPECS,socket

ROOT=Path(__file__).resolve().parents[4]
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview')


def luau(value):
    if isinstance(value,dict): return '{'+','.join(k+'='+luau(v) for k,v in value.items())+'}'
    if isinstance(value,list): return '{'+','.join(luau(v) for v in value)+'}'
    return json.dumps(value)


def main():
    definitions={name:{'Id':name,'Role':'PATH','SizeX':256,'SizeZ':256,
                   'Sockets':[socket(name,s) for s in ('S','W','N','E') if s in spec]}
                 for name,spec in SPECS.items()}
    source=(ROOT/'src/shared/Util/ChunkCore.luau').read_text().replace(
        'local WeightedRandom = require(script.Parent.WeightedRandom)','local WeightedRandom = {}')
    harness='local defs='+luau(definitions)+'''
local results={}
local function run(label,names,yaw)
 local placed={{ChunkId=names[1],Role="PATH",X=0,Y=0,Z=0,Yaw=yaw,Index=1}}
 for i=2,#names do
  local before=defs[names[i-1]]
  local open=Core.worldSocket(placed[i-1],before,before.Sockets[#before.Sockets])
  local p,s=Core.placeAgainst(defs[names[i]],open,i)
  assert(p and s)
  local actual=Core.worldSocket(p,defs[names[i]],s)
  assert(math.abs(actual.X-open.X)+math.abs(actual.Y-open.Y)+math.abs(actual.Z-open.Z)<1e-7)
  assert((actual.Facing-open.Facing)%360==180)
  for j,q in placed do assert(not Core.overlaps(q,defs[names[j]],p,defs[names[i]])) end
  table.insert(placed,p)
 end
 local rows={}
 for i,p in placed do table.insert(rows,string.format('{"name":"%s","x":%.12f,"y":%.12f,"z":%.12f,"yaw":%d}',names[i],p.X,p.Y,p.Z,p.Yaw)) end
 table.insert(results,'"'..label..'":['..table.concat(rows,",")..']')
end
for _,a in {"A","A2"} do for _,yaw in {0,90,180,270} do for _,b in {"B1","B2","B3"} do
 run(a.."_"..yaw.."_"..b,{a,b},yaw)
end end end
run("rising_corner",{"A","B2","C"},0)
print("{"..table.concat(results,",").."}")
'''
    OUT.mkdir(parents=True,exist_ok=True)
    script=OUT/'frozen_profile_layout.luau'; script.write_text('local Core=(function()\n'+source+'\nend)()\n'+harness)
    result=subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe',str(script)],text=True,capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr)
    data=json.loads(result.stdout)
    (OUT/'layouts.json').write_text(json.dumps(data,indent=2))
    print('ACTUAL_CHUNKCORE_PASS',len(data),'layouts')


if __name__=='__main__': main()
