"""Generate a bounded transient Studio collider probe; no uploads/asset IDs."""
import json
import math
from pathlib import Path
from edge_profile_contract import height,grid,surface

OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_EdgeProfileReview')


def main():
    poses=json.loads((OUT/'layouts.json').read_text())['rising_corner']
    patches=[]
    for row in poses:
        name=row['name']
        for ty in range(-128,128,8):
            for tx in range(-128,128,8):
                if not ((name=='A' and ty==120) or (name=='B2' and (ty==-128 or tx==120)) or (name=='C' and ty==-128)):continue
                quad=[(tx,height(name,tx,ty),-ty),(tx+8,height(name,tx+8,ty),-ty),
                      (tx+8,height(name,tx+8,ty+8),-ty-8),(tx,height(name,tx,ty+8),-ty-8)]
                for tri in ((0,1,2),(0,2,3)):
                    vertices=[quad[i] for i in tri];vertices += [(x,y-4,z) for x,y,z in vertices]
                    center=[(min(v[i] for v in vertices)+max(v[i] for v in vertices))/2 for i in range(3)]
                    relative=[[round(v[i]-center[i],7) for i in range(3)] for v in vertices]
                    faces=((0,1,2),(5,4,3),(0,3,4),(0,4,1),(1,4,5),(1,5,2),(2,5,3),(2,3,0))
                    patches.append({'name':name,'center':center,'vertices':relative,'faces':[[i+1 for i in f] for f in faces],'pose':row})
    samples=[]
    for join in (0,1):
        center=(0,128) if join==0 else (128,256)
        for s in (-112,-64,-16,0,16,64,112):
            for d in (-4,-1,-.05,.05,1,4):
                x,y=(s,128+d) if join==0 else (128+d,256+s)
                samples.append([x,y])
    code='-- Isolated collision cook/raycast probe. No persistent mesh IDs.\nlocal data=game:GetService("HttpService"):JSONDecode([=['+json.dumps({'patches':patches,'samples':samples},separators=(',',':'))+']=])\n'
    code+='''
assert(not workspace:FindFirstChild("EmberfallEdgeProfileProbe"),"Existing probe must be inspected first")
local folder=Instance.new("Folder");folder.Name="EmberfallEdgeProfileProbe";folder.Parent=workspace
local service=game:GetService("AssetService")
local start=os.clock()
for i,p in data.patches do
 local editable=service:CreateEditableMesh();assert(editable,"Mesh budget")
 local ids={}
 for k,v in p.vertices do ids[k]=editable:AddVertex(Vector3.new(v[1],v[2],v[3])) end
 for _,f in p.faces do editable:AddTriangle(ids[f[1]],ids[f[2]],ids[f[3]]) end
 local part=service:CreateMeshPartAsync(Content.fromObject(editable),{CollisionFidelity=Enum.CollisionFidelity.Hull})
 part.Name=p.name.."_"..i;part.Anchored=true;part.CanCollide=true;part.CanQuery=true
 part.Color=Color3.fromRGB(25,145,164)
 part.CFrame=CFrame.new(10000+p.pose.x,100+p.pose.y,p.pose.z)*CFrame.Angles(0,-math.rad(p.pose.yaw),0)*CFrame.new(table.unpack(p.center))
 part.Parent=folder
 assert(part.CollisionFidelity==Enum.CollisionFidelity.Hull)
end
local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Include;params.FilterDescendantsInstances={folder};params.RespectCanCollide=true
local results={}
for _,q in data.samples do
 local hit=workspace:Raycast(Vector3.new(10000+q[1],250,-q[2]),Vector3.new(0,-220,0),params)
 table.insert(results,{x=q[1],y=q[2],height=if hit then hit.Position.Y-100 else nil,hit=hit~=nil,part=if hit then hit.Instance.Name else "NONE"})
end
return {parts=#data.patches,seconds=os.clock()-start,raycasts=results,folder=folder:GetFullName(),fidelity="Hull"}
'''
    (OUT/'studio_collision_probe.luau').write_text(code)
    print('BOUNDED_STUDIO_PROBE',len(patches),'closed source patches')


if __name__=='__main__':main()
