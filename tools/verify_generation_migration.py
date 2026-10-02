"""Targeted real production-path cold/reuse verification, restoring every Edit source.

Never reruns A-M, publishes or saves. Runtime timing hooks exist only in temporary
Studio sources. Fresh Play per world resets the production template/yaw cache.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/benchmarks'
STUDIO=os.environ.get('LUCKBOUND_STUDIO_ID', 'b86afbd8-7330-46fd-a078-e6d1379be37f')
_installed = False
_geometry_created = False
FILES=['src/shared/Core/GameConfig.luau','src/shared/Util/AssetPreparation.luau',
       'src/shared/Util/ChunkAssetCore.luau','src/shared/Util/GenerationAnchors.luau',
       'src/shared/Util/ChunkLoader.luau','src/shared/Util/Schema.luau',
       'src/server/Systems/ExpeditionSystem.luau',
       'src/client/Controllers/AtmosphereEffects.luau',
       'src/client/Controllers/ExpeditionController.luau']


def rpc(tool,args):
    request=ROOT/'.tools/migration_request.json'
    request.write_text(json.dumps(args),encoding='utf-8')
    result=subprocess.run([sys.executable,str(ROOT/'tools/studio_mcp.py'),tool,'--args-file',str(request)],cwd=ROOT,capture_output=True,text=True,check=True)
    envelope=json.loads(result.stdout)['result']
    if envelope.get('isError'): raise RuntimeError(envelope)
    value=envelope['content'][0]['text']
    for _ in range(3):
        if not isinstance(value,str): break
        try: value=json.loads(value)
        except json.JSONDecodeError: break
    return value


def code(context,source): return rpc('execute_luau',{'studio_id':STUDIO,'datamodel_type':context,'code':source})
def play(start): return rpc('start_stop_play',{'studio_id':STUDIO,'is_start':start})


def parent(path):
    if '/server/' in path: return 'game.ServerScriptService.LuckboundServer.Systems'
    if '/client/' in path: return 'game.StarterPlayer.StarterPlayerScripts.LuckboundClient.Controllers'
    return 'game.ReplicatedStorage.Luckbound.'+('Core' if '/Core/' in path else 'Util')


HOOK='''
local verification = {Running=false,Records={}}
function verification.ready() return preparedAssets ~= nil end
function verification.run(worldId,seed,repeatIndex)
 assert(not verification.Running,"verification already running")
 verification.Running=true
 task.spawn(function()
  local ok,err=pcall(function()
   local player=Players:GetPlayers()[1] assert(player and player.Character,"player not ready")
   local rig=player.Character local hrp=rig:FindFirstChild("HumanoidRootPart") local home=rig:GetPivot()
   local before=preparedAssets:stats()
   verificationStarted=os.clock()
   local built=buildStage(worldId,seed,GameConfig.Expedition.StageOrigin,"ProductionGenerationVerification") assert(built,"generation failed")
   local collision=os.clock()-verificationStarted
   local group=newGroup(worldId,seed,built,nil,player.UserId,1)
   hrp:SetNetworkOwner(nil) hrp.AssemblyLinearVelocity=Vector3.zero hrp.AssemblyAngularVelocity=Vector3.zero
   assert(placeMember(player,group),"placement failed")
   local placed=os.clock()-verificationStarted local groundedFrames=0
   local humanoid=rig:FindFirstChildOfClass("Humanoid")
   local deadline=os.clock()+GameConfig.ChunkRuntime.StreamTimeoutSeconds
   while os.clock()<deadline and groundedFrames<2 do
    RunService.Heartbeat:Wait()
    if humanoid.FloorMaterial~=Enum.Material.Air then groundedFrames+=1 else groundedFrames=0 end
   end
   local grounded=os.clock()-verificationStarted
   local deadline=os.clock()+30
   while group.Anchors and group.Anchors.Pending and os.clock()<deadline do RunService.Heartbeat:Wait() end
   local complete=os.clock()-verificationStarted
   local after=preparedAssets:stats() local delta={}
   for key,value in after do if type(value)=="number" then delta[key]=value-(before[key] or 0) end end
   local row={WorldId=worldId,Seed=seed,Repeat=repeatIndex,LayoutSolvedSeconds=verificationLayout,
    AssetsPreparedSeconds=verificationAssets,CollisionReadySeconds=collision,PlayerPlacedSeconds=placed,
    PlayerGroundedSeconds=grounded,CompletionSeconds=complete,Grounded=groundedFrames>=2,
    AtmosphereReady=not(group.Anchors and group.Anchors.Pending),WorkingSetSize=verificationWorkingSet,
    Counters=delta,Cache=after,MemoryMb=game:GetService("Stats"):GetTotalMemoryUsageMb()}
   row.Geometry=require(Root.Util.ProductionGeometryVerification).sample(built.Stage,verificationSolvedLayout,Chunks,built.FloorY)
   table.insert(verification.Records,row)
   verification.ReadyForClient=true
   task.wait(4)
   ExpeditionSystem.finish(player,"DIED") rig:PivotTo(home) hrp.AssemblyLinearVelocity=Vector3.zero hrp:SetNetworkOwnershipAuto()
  end)
  if not ok then verification.Error=tostring(err) end
  verification.Running=false
 end)
end
local endpoint=Instance.new("BindableFunction") endpoint.Name="ProductionGenerationVerification" endpoint.Parent=game.ServerStorage
endpoint.OnInvoke=function(action,a,b,c)
 if action=="ready" then return verification.ready() end
 if action=="run" then verification.run(a,b,c) return true end
 if action=="state" then return {Running=verification.Running,Count=#verification.Records,Error=verification.Error or "",Ready=verification.ReadyForClient==true} end
 if action=="observed" then verification.ReadyForClient=false return true end
 if action=="row" then return game:GetService("HttpService"):JSONEncode(verification.Records[a]) end
end
'''


def install():
    global _installed, _geometry_created
    backups={}
    for path in FILES:
        name=Path(path).stem; target=parent(path)
        backups[path]=code('Edit',f'local m={target}:FindFirstChild("{name}") return {{Exists=m~=nil,Source=if m then m.Source else ""}}')
    (ROOT/'.tools/migration_source_backups.json').write_text(json.dumps(backups),encoding='utf-8')
    _installed = True
    for path in FILES:
        source=(ROOT/path).read_text(encoding='utf-8')
        if path.endswith('GameConfig.luau'): source=source.replace('AssetPreparationDiagnostics = false','AssetPreparationDiagnostics = true')
        if path.endswith('ExpeditionSystem.luau'):
            source=source.replace('local ExpeditionSystem = {}','local ExpeditionSystem = {}\nlocal verificationStarted,verificationLayout,verificationAssets,verificationWorkingSet,verificationSolvedLayout')
            source=source.replace('layout.Atmosphere = (atmosphereFor(worldId, seed))','layout.Atmosphere = (atmosphereFor(worldId, seed))\nverificationLayout=os.clock()-(verificationStarted or os.clock())\nverificationSolvedLayout=layout')
            source=source.replace('local preparation = ChunkLoader.prepare(layout, Chunks, preparedAssets)','local preparation, workingSet = ChunkLoader.prepare(layout, Chunks, preparedAssets)\nverificationWorkingSet=workingSet\nverificationAssets=os.clock()-(verificationStarted or os.clock())')
            source=source.replace('\nreturn ExpeditionSystem\n',HOOK+'\nreturn ExpeditionSystem\n')
        if path.endswith('ExpeditionController.luau'):
            source=source.replace('\nreturn ExpeditionController\n', '\nlocal endpoint=Instance.new("BindableFunction") endpoint.Name="ProductionClientVerification" endpoint.Parent=game.Players.LocalPlayer.PlayerScripts endpoint.OnInvoke=function() local a=active return {Active=a~=nil,StageName=if a then a.StageName else "",Pending=if a and a.Anchors then a.Anchors.Pending==true else false} end\nreturn ExpeditionController\n')
        name=Path(path).stem
        code('Edit' ,f'local p={parent(path)} local m=p:FindFirstChild("{name}") or Instance.new("ModuleScript") m.Name="{name}" m.Source=[======[{source}]======] m.Parent=p return true')
    geometry=(ROOT/'tests/generation_geometry_studio.luau').read_text()
    code('Edit','assert(not game.ReplicatedStorage.Luckbound.Util:FindFirstChild("ProductionGeometryVerification"),"temporary fixture name already in use") local m=Instance.new("ModuleScript") m.Name="ProductionGeometryVerification" m.Source=[======['+geometry+']======] m.Parent=game.ReplicatedStorage.Luckbound.Util return true')
    _geometry_created = True


def restore():
    global _installed, _geometry_created
    if not _installed: return
    play(False)
    backups=json.loads((ROOT/'.tools/migration_source_backups.json').read_text())
    for path,backup in backups.items():
        name=Path(path).stem
        source=backup['Source']
        mutation=f'm.Source=[======[{source}]======]' if backup['Exists'] else 'm:Destroy()'
        code('Edit',f'local m={parent(path)}:FindFirstChild("{name}") if m then {mutation} end return true')
    if _geometry_created:
        code('Edit','local m=game.ReplicatedStorage.Luckbound.Util:FindFirstChild("ProductionGeometryVerification") if m then m:Destroy() end return true')
        _geometry_created = False
    for path,backup in backups.items():
        name=Path(path).stem
        current=code('Edit',f'local m={parent(path)}:FindFirstChild("{name}") return {{Exists=m~=nil,Source=if m then m.Source else ""}}')
        assert current==backup,path+' not restored'
    _installed = False


def main():
    OUT.mkdir(exist_ok=True)
    target=OUT/'generation_migration_studio.json'
    if target.exists(): print('Preserved completed targeted verification'); return
    play(False)
    rows=[]; invariant_results={}; client_rows=[]
    try:
        install()
        for world in ['VERDANT_VALLEY','SKY_CITADEL','ETHEREAL_SCAPE']:
            play(True); time.sleep(3)
            code('Client','require(game.ReplicatedStorage.Luckbound.Core.Net).get("Player_Ready"):FireServer() return true')
            for _ in range(30):
                if code('Server','local p=game.Players:GetPlayers()[1] local v=game.ServerStorage:FindFirstChild("ProductionGenerationVerification") return {Ready=p~=nil and p.Character~=nil and v~=nil and v:Invoke("ready")}')['Ready']: break
                time.sleep(1)
            else: raise RuntimeError('production initialization timed out')
            if not invariant_results:
                for name in ['asset_preparation_studio','generation_anchors_studio']:
                    source=(ROOT/f'tests/{name}.luau').read_text()
                    invariant_results[name]=code('Server','local m=Instance.new("ModuleScript") m.Source=[======['+source+']======] m.Parent=game.ServerStorage local result=require(m) m:Destroy() return result')
                (OUT/'generation_migration_invariants.json').write_text(json.dumps(invariant_results,indent=2),encoding='utf-8')
            for repeat in [1,2]:
                code('Server',f'game.ServerStorage.ProductionGenerationVerification:Invoke("run","{world}",1,{repeat}) return true')
                while True:
                    state=code('Server','return game.ServerStorage.ProductionGenerationVerification:Invoke("state")')
                    if state['Error']: raise RuntimeError(state['Error'])
                    if state['Count']>=repeat and state['Ready']:
                        observed=code('Client','return game.Players.LocalPlayer.PlayerScripts.ProductionClientVerification:Invoke()')
                        client_rows.append(dict(WorldId=world,Repeat=repeat,**observed))
                        code('Server','game.ServerStorage.ProductionGenerationVerification:Invoke("observed") return true')
                    if not state['Running']: break
                    time.sleep(1)
                row=code('Server',f'return game.ServerStorage.ProductionGenerationVerification:Invoke("row",{repeat})')
                rows.append(row)
                (OUT/'generation_migration_progress.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
                print(world,repeat,round(row['PlayerGroundedSeconds'],3),'s',row['Counters'].get('CreateMeshPartAsyncCalls',0),'API calls',flush=True)
            play(False)
        target.write_text(json.dumps(rows,indent=2),encoding='utf-8')
        (OUT/'generation_migration_client.json').write_text(json.dumps(client_rows,indent=2),encoding='utf-8')
    finally:
        restore()
        print('Original Studio sources restored; no save/publish',flush=True)


if __name__=='__main__': main()
