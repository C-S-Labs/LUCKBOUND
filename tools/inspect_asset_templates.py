"""Read-only inventory of local Studio visual templates and collision fidelity."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
code = '''local kits=game.ServerStorage:FindFirstChild("LuckboundChunkKits")
local root=game.ReplicatedStorage.Luckbound
local manifest=require(root.Content.AssetManifest)
local keys={}
local function add(chunk)
 if chunk.MeshParts then for _,p in chunk.MeshParts do local id=manifest.assetId(p.AssetKey) if id then keys[string.match(id,"%d+")]=p.AssetKey end end
 else local id=manifest.assetId(chunk.AssetKey) if id then keys[string.match(id,"%d+")]=chunk.AssetKey end end
 for _,room in chunk.AttachedRooms or {} do add(room) end
end
for _,chunk in require(root.Content.Chunks) do add(chunk) end
local rows={}
local count=0
if kits then for _,p in kits:GetDescendants() do
 if p:IsA("MeshPart") then count+=1 local key=keys[string.match(p.MeshId,"%d+")] if key then table.insert(rows,{Key=key,Path=p.Name,MeshId=p.MeshId,
 Size={p.Size.X,p.Size.Y,p.Size.Z},CanCollide=p.CanCollide,CanQuery=p.CanQuery,
 Fidelity=p.CollisionFidelity.Name}) end end
end end
return game:GetService("HttpService"):JSONEncode({MeshPartCount=count,Visuals=rows})'''
(root / '.tools/studio_request.json').write_text(json.dumps({
    'studio_id': 'b86afbd8-7330-46fd-a078-e6d1379be37f',
    'datamodel_type': 'Server', 'code': code}), encoding='utf-8')
