"""Compare measured control art orientation with authored hints; no new raycasts."""
import json
from run_asset_matrix import ROOT,OUTPUT,call,luau

def main():
    rows=json.loads((OUTPUT/'asset_ASSET_CONTROL.json').read_text(encoding='utf-8'))
    references={key+':'+row.get('Atmosphere',''):yaw for row in rows for key,yaw in row['ArtYaws'].items()}
    code='''local root=game.ReplicatedStorage.Luckbound
local chunks=require(root.Content.Chunks)
local runtime=require(root.Core.ChunkRuntimeCore)
local mismatches={} local missing=0 local checked=0
for key,yaw in REFERENCES do
 local id=string.match(key,"^(.-):") local chunk=runtime.lookup(chunks,id)
 checked+=1
 if chunk.MeshYawOffset==nil then missing+=1
 elseif chunk.MeshYawOffset~=yaw then table.insert(mismatches,{Key=key,Measured=yaw,Authored=chunk.MeshYawOffset}) end
end
return {Checked=checked,MissingHints=missing,Mismatches=mismatches}'''.replace('REFERENCES',luau(references))
    result=call(code)
    (OUTPUT/'generation_yaw_metadata_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__': main()
