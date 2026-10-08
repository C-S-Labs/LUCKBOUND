"""Generate reconstructable transient exact-mesh Studio cook probe, no uploads."""
import json
from pathlib import Path
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')
data=json.loads((OUT/'gate_a_collision_payload.json').read_text())
meta={r['id']:r for r in json.loads((OUT/'gate_a_sources.json').read_text())}
code='local data=game:GetService("HttpService"):JSONDecode([=['+json.dumps(data,separators=(',',':'))+']=])\n'
code+='''
assert(game.PlaceId==0,"Use isolated Batch2ProductionReview only")
assert(not workspace:FindFirstChild("EmberfallBatch2GateCook"),"Inspect existing probe first")
local folder=Instance.new("Folder");folder.Name="EmberfallBatch2GateCook";folder.Parent=workspace
local service=game:GetService("AssetService")
folder:SetAttribute("Status","Cooking")
task.spawn(function()
 local ok,err=pcall(function()
  local offsets={EF_QUIET_HOLLOW_BEND=0,EF_RAISED_PASTURE_BEND=400,EF_LOW_SHOULDER_CLIMB=800}
  for i,p in data do
   local editable=service:CreateEditableMesh();assert(editable,"Mesh budget")
   local ids={};local lo=Vector3.new(math.huge,math.huge,math.huge);local hi=-lo
   for _,v in p.vertices do local q=Vector3.new(v[1],v[2],v[3]);lo=lo:Min(q);hi=hi:Max(q) end
   local center=(lo+hi)/2
   for k,v in p.vertices do ids[k]=editable:AddVertex(Vector3.new(v[1],v[2],v[3])-center) end
   for _,f in p.faces do editable:AddTriangle(ids[f[1]+1],ids[f[2]+1],ids[f[3]+1]) end
   local part=service:CreateMeshPartAsync(Content.fromObject(editable),{CollisionFidelity=Enum.CollisionFidelity[p.fidelity]})
   part.Name=p.chunk.."_"..i;part.Anchored=true;part.CanCollide=true;part.CanQuery=true
   part.CFrame=CFrame.new(10000+offsets[p.chunk],100,0)*CFrame.new(center)
   part.Color=Color3.fromRGB(25,145,164);part:SetAttribute("Chunk",p.chunk)
   part.Parent=folder
   assert(part.CollisionFidelity==Enum.CollisionFidelity[p.fidelity])
   editable:Destroy();folder:SetAttribute("Completed",i)
  end
 end)
 folder:SetAttribute("Status",if ok then "Ready" else "Failed")
 if not ok then folder:SetAttribute("Error",tostring(err)) end
end)
return {queued=#data,probe=folder:GetFullName()}
'''
(OUT/'gate_a_studio_cook.luau').write_text(code)
print('Generated exact collider cook',len(data))

import sys
sys.path.insert(0,'E:/BlenderAIProjects/Runtime/Emberfall_Batch1/inputs')
import edge_profile_contract as ec
samples=[]
for ident,row in meta.items():
    for socket in row['sockets']:
        for t in (-112,-64,-16,0,16,64,112):
            for inset in (1,4):
                x,z={'S':(t,128-inset),'N':(t,-128+inset),'W':(-128+inset,-t),'E':(128-inset,-t)}[socket['Id']]
                samples.append(dict(chunk=ident,x=x,z=z,height=socket['OffsetY']+ec.profile(socket['Kind'].split('_')[-1],t),edge=True))
    for x,y,z in row['guide'][::7]:samples.append(dict(chunk=ident,x=x,z=-y,height=z-.055,edge=False))
verify='local samples=game:GetService("HttpService"):JSONDecode([=['+json.dumps(samples,separators=(',',':'))+']=])\n'
verify+='''
local folder=workspace.EmberfallBatch2GateCook;assert(folder:GetAttribute("Status")=="Ready")
local offsets={EF_QUIET_HOLLOW_BEND=0,EF_RAISED_PASTURE_BEND=400,EF_LOW_SHOULDER_CLIMB=800}
local basis={};for _,p in folder:GetChildren() do basis[p]=CFrame.new(10000+offsets[p:GetAttribute("Chunk")],100,0):ToObjectSpace(p.CFrame) end
local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Include;params.FilterDescendantsInstances={folder};params.RespectCanCollide=true
local results={}
for _,yaw in {0,90} do
 for p,cf in basis do p.CFrame=CFrame.new(10000+offsets[p:GetAttribute("Chunk")],100,0)*CFrame.Angles(0,math.rad(yaw),0)*cf end
 task.wait(.2)
 local misses=0;local edgeError=0;local interiorError=0;local failures={}
 for _,q in samples do
  local frame=CFrame.new(10000+offsets[q.chunk],100,0)*CFrame.Angles(0,math.rad(yaw),0)
  local pos=frame:PointToWorldSpace(Vector3.new(q.x,q.height,q.z))
  local hit=workspace:Raycast(pos+Vector3.new(0,50,0),Vector3.new(0,-100,0),params)
  if not hit then misses+=1;table.insert(failures,q) else
   local delta=math.abs(hit.Position.Y-pos.Y)
   if q.edge then edgeError=math.max(edgeError,delta) else interiorError=math.max(interiorError,delta) end
   if q.edge and delta>.01 then table.insert(failures,{chunk=q.chunk,x=q.x,z=q.z,error=delta}) end
  end
 end
 table.insert(results,{yaw=yaw,rays=#samples,misses=misses,edgeError=edgeError,interiorError=interiorError,failures=failures})
end
for p,cf in basis do p.CFrame=CFrame.new(10000+offsets[p:GetAttribute("Chunk")],100,0)*cf end
return results
'''
(OUT/'gate_a_studio_verify.luau').write_text(verify)
walk='local data=game:GetService("HttpService"):JSONDecode([=['+json.dumps(list(meta.values()),separators=(',',':'))+']=])\n'
walk+='''
local player=game:GetService("Players").LocalPlayer;local character=player.Character
assert(character and character:FindFirstChildOfClass("ControllerManager"),"Normal movement controller must be ready")
local humanoid=character:FindFirstChildOfClass("Humanoid");local root=character.HumanoidRootPart
local offsets={EF_QUIET_HOLLOW_BEND=0,EF_RAISED_PASTURE_BEND=400,EF_LOW_SHOULDER_CLIMB=800}
local run=game:GetService("RunService")
workspace:SetAttribute("EmberfallBatch2WalkStatus","Running")
task.spawn(function()
 local results={}
 for _,row in data do
  local guide=row.guide;local base=Vector3.new(10000+offsets[row.id],100,0)
  local start=base+Vector3.new(guide[3][1],guide[3][3]+3.1,-guide[3][2])
  character:PivotTo(CFrame.new(start));root.AssemblyLinearVelocity=Vector3.zero;task.wait(.6)
  local initial=root.Position;local index=4;local started=os.clock();local lowest=humanoid.Health
  run:BindToRenderStep("EmberfallBatch2WalkInput",Enum.RenderPriority.Input.Value+1,function()
   local point=guide[index];local destination=base+Vector3.new(point[1],point[3],-point[2])
   local delta=destination-root.Position;local flat=Vector3.new(delta.X,0,delta.Z)
   if flat.Magnitude<3 and index<#guide-2 then index+=1 end
   humanoid:Move(if flat.Magnitude>.01 then flat.Unit else Vector3.zero,false)
  end)
  while os.clock()-started<22 and index<#guide-2 and humanoid.Health>0 do task.wait(.15);lowest=math.min(lowest,humanoid.Health) end
  run:UnbindFromRenderStep("EmberfallBatch2WalkInput");humanoid:Move(Vector3.zero,false)
  table.insert(results,{chunk=row.id,seconds=os.clock()-started,waypoint=index,total=#guide,completed=index>=#guide-2,displacement=(root.Position-initial).Magnitude,health=lowest,position={root.Position.X,root.Position.Y,root.Position.Z}})
  workspace:SetAttribute("EmberfallBatch2WalkResult",game:GetService("HttpService"):JSONEncode(results))
 end
 workspace:SetAttribute("EmberfallBatch2WalkStatus","Finished")
end)
return "Actual ControllerManager traversal queued; input only, no scripted translation after each source start"
'''
(OUT/'gate_a_studio_walk.luau').write_text(walk)
