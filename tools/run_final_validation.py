"""After measured M, validate the selected combination and live safe entry.

Preserves all earlier cohorts. Selection uses measured worst cold-map readiness
among query/visual-equivalent M policies; L is never included if queries differ.
"""
import json
import subprocess
import sys
import time
from run_asset_matrix import ROOT,OUTPUT,STUDIO,SEEDS,call,install,luau


def client(code):
    target=ROOT/'.tools/client_request.json'
    target.write_text(json.dumps({'studio_id':STUDIO,'datamodel_type':'Client','code':code}),encoding='utf-8')
    result=subprocess.run([sys.executable,str(ROOT/'tools/studio_mcp.py'),'execute_luau',
                           '--args-file',str(target)],cwd=ROOT,capture_output=True,text=True,check=True)
    value=json.loads(result.stdout)['result']
    if value.get('isError'): raise RuntimeError(value)
    content=value['content'][0]['text']
    try: value=json.loads(content)
    except json.JSONDecodeError: return content
    if isinstance(value,str): value=json.loads(value)
    return value


def fetch(root='LuckboundAssetExperiment'):
    state=call(f'''local root=game.ReplicatedStorage.{root}
local r=require(root.Util.GenerationBenchmark).records()
return {{Running=r.Running,Count=#r.Records,Error=root:GetAttribute("BenchmarkError")}}''')
    return state


def drain(label,target):
    count=-1
    while True:
        state=fetch()
        if state.get('Error'): raise RuntimeError(state['Error'])
        if state['Count']!=count:
            count=state['Count']
            print(f'{label}: {count}/30 maps',flush=True)
        if not state['Running']: break
        time.sleep(15)
    rows=[call('return game:GetService("HttpService"):JSONEncode(require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.GenerationBenchmark).records().Records['+str(i)+'])') for i in range(1,count+1)]
    assert len(rows)==30
    target.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    return rows


def main():
    assert((OUTPUT/'asset_M6.json').exists()),'M must finish before selection'
    controls=json.loads((OUTPUT/'asset_ASSET_CONTROL.json').read_text(encoding='utf-8'))
    reference={key+':'+row.get('Atmosphere',''):yaw for row in controls for key,yaw in row['ArtYaws'].items()}
    candidates={worker:json.loads((OUTPUT/f'asset_M{worker}.json').read_text(encoding='utf-8')) for worker in [2,4,6]}
    worker=min(candidates,key=lambda count:max(row['PlayableSeconds'] for row in candidates[count]))
    policy={'Id':'FINAL','LocalTemplates':True,'VisualFidelity':True,'Cache':True,'Prepare':'Seed','Workers':worker}
    (OUTPUT/'asset_selected_policy.json').write_text(json.dumps(policy,indent=2),encoding='utf-8')
    target=OUTPUT/'asset_FINAL.json'
    if not target.exists():
        install(policy,reference,stage='F')
        drain('FINAL',target)
    # Client-only invariant for late delivery: preserve actor instances/positions.
    testfile=OUTPUT/'atmosphere_late_update_invariants.json'
    if not testfile.exists():
        client('''local old=game.Players.LocalPlayer.PlayerScripts:FindFirstChild("AtmosphereExperimentTests")
if old then local m=old:FindFirstChild("AtmosphereEffects") if m then pcall(function() require(m).leave() end) end old:Destroy() end
local stage=workspace:FindFirstChild("AtmosphereLateUpdateFixture") if stage then stage:Destroy() end
local props=game.ReplicatedStorage:FindFirstChild("LuckboundProps")
if props then
 local folder=props:FindFirstChild("GenerationAtmosphereFixture") if folder then folder:Destroy() end
 for _,name in {"atm_security_probe","atm_alarm_beacon"} do
  local part=props:FindFirstChild(name)
  if part and part:IsA("Part") and part.Size==Vector3.new(2,2,2) then part:Destroy() end
 end
end
return true''')
        effects=(ROOT/'src/client/Controllers/AtmosphereEffects.luau').read_text(encoding='utf-8')
        test=(ROOT/'tests/atmosphere_late_update_studio.luau').read_text(encoding='utf-8')
        value=client('''local parent=Instance.new("Folder") parent.Name="AtmosphereExperimentTests" parent.Parent=game.Players.LocalPlayer.PlayerScripts
local effect=Instance.new("ModuleScript") effect.Name="AtmosphereEffects" effect.Source=[======['''+effects+''']======] effect.Parent=parent
local test=Instance.new("ModuleScript") test.Source=[======['''+test+''']======] test.Parent=parent
local result=require(test) parent:Destroy()
return game:GetService("HttpService"):JSONEncode(result)''')
        testfile.write_text(json.dumps(value,indent=2),encoding='utf-8')
    for mode in ['LIVE_CONTROL','LIVE_FINAL']:
        target=OUTPUT/f'asset_{mode}.json'
        if target.exists(): continue
        call('for _,model in workspace:GetChildren() do if model.Name=="GenerationBenchmark" then model:Destroy() end end return true')
        observer=(ROOT/'tests/generation_client_observer.luau').read_text(encoding='utf-8')
        client('''local old=game.Players.LocalPlayer.PlayerScripts:FindFirstChild("GenerationClientObserver") if old then pcall(function() require(old).stop() end) old:Destroy() end
local module=Instance.new("ModuleScript") module.Name="GenerationClientObserver" module.Source=[======['''+observer+''']======] module.Parent=game.Players.LocalPlayer.PlayerScripts
require(module)
require(game.ReplicatedStorage.Luckbound.Core.Net).get("Player_Ready"):FireServer()
return true''')
        time.sleep(3)
        live_policy={'Id':mode} if mode=='LIVE_CONTROL' else dict(policy,Id=mode)
        stage='A' if mode=='LIVE_CONTROL' else 'F'
        install(live_policy,None if mode=='LIVE_CONTROL' else reference,stage=stage,run=False)
        call('''local root=game.ReplicatedStorage.LuckboundAssetExperiment
local bench=require(root.Util.GenerationBenchmark)
local expedition=require(root.Util.ExpeditionSystem)
local loot=require(game.ServerScriptService.LuckboundServer.Systems.LootSystem)
local deps=expedition.benchmarkDependencies(loot)
deps.FloorY=require(root.Core.GameConfig).Expedition.StageOrigin.Y
assert(#game.Players:GetPlayers()==1,"single-player Studio validation required")
deps.player=game.Players:GetPlayers()[1]
assert(deps.player.Character,"character not ready")
deps.placePlayer=expedition.benchmarkPlace
deps.verify=require(root.Util.AssetGeometryCheck).sample
deps.AssetPolicy=POLICY
deps.ReferenceYaws=REFERENCE
task.spawn(function() local ok,err=pcall(bench.run,STAGE,deps,2,SEEDS) if not ok then root:SetAttribute("BenchmarkError",tostring(err)) end end)
return true'''.replace('POLICY',luau(live_policy)).replace('REFERENCE','nil' if mode=='LIVE_CONTROL' else luau(reference)).replace('STAGE',luau(stage)).replace('SEEDS',luau(SEEDS)))
        rows=drain(mode,target)
        observations=client('return game:GetService("HttpService"):JSONEncode(require(game.Players.LocalPlayer.PlayerScripts.GenerationClientObserver).records())')
        (OUTPUT/f'asset_{mode}_client.json').write_text(json.dumps(observations,indent=2),encoding='utf-8')
        client('local m=game.Players.LocalPlayer.PlayerScripts.GenerationClientObserver require(m).stop() m:Destroy() return true')
    print('FINAL AND LIVE ENTRY VALIDATION COMPLETE',flush=True)


if __name__=='__main__': main()
