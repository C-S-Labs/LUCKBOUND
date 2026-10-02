"""Additional ES client diagnostic; preserves all completed benchmark cohorts."""
import json
import time
from run_asset_matrix import ROOT, OUTPUT, call, install
from run_final_validation import client
from measure_server_boot import play


def main():
    target=OUTPUT/'asset_entry_replication_diagnostic.json'
    if target.exists():
        if json.loads(target.read_text()).get('Server'):
            print('Preserved entry diagnostic')
            return
        target.rename(OUTPUT/'asset_entry_replication_interrupted.json')
    play(True)
    time.sleep(4)
    client('require(game.ReplicatedStorage.Luckbound.Core.Net).get("Player_Ready"):FireServer() return true')
    for _ in range(30):
        if call('local p=game.Players:GetPlayers()[1] return p and p.Character~=nil'):
            break
        time.sleep(1)
    controls=json.loads((OUTPUT/'asset_ASSET_CONTROL.json').read_text())
    reference={key+':'+row.get('Atmosphere',''):yaw for row in controls for key,yaw in row['ArtYaws'].items()}
    path='src/shared/Util/GenerationBenchmark.luau'
    source=(ROOT/path).read_text().replace('for _, worldId in config.Worlds do','for _, worldId in {"ETHEREAL_SCAPE"} do').replace('< GameConfig.ChunkRuntime.StreamTimeoutSeconds','< 12')
    install({'Id':'ENTRY_DIAGNOSTIC','LocalTemplates':True,'VisualFidelity':True,
             'Cache':True,'Prepare':'Seed','Workers':6},reference,stage='F',run=False,source_overrides={path:source})
    setup=call('''local root=game.ReplicatedStorage.LuckboundAssetExperiment
local cfg=require(root.Core.GameConfig)
local bench=require(root.Util.GenerationBenchmark)
local expedition=require(root.Util.ExpeditionSystem)
local loot=require(game.ServerScriptService.LuckboundServer.Systems.LootSystem)
local deps=expedition.benchmarkDependencies(loot)
deps.FloorY=cfg.Expedition.StageOrigin.Y
deps.player=game.Players:GetPlayers()[1]
deps.placePlayer=expedition.benchmarkPlace
deps.AssetPolicy={Id="ENTRY_DIAGNOSTIC",LocalTemplates=true,VisualFidelity=true,Cache=true,Prepare="Seed",Workers=6}
deps.ReferenceYaws=REFERENCE
deps.verify=function(built,layout,profile)
 profile.EntryParts={}
 local entry=built.Model:FindFirstChild("0_ES_ENTRY")
 for _,part in entry:GetDescendants() do
  if part:IsA("MeshPart") then
   table.insert(profile.EntryParts,{Name=part.Name,Transparency=part.Transparency,CanCollide=part.CanCollide,Position={part.Position.X,part.Position.Y,part.Position.Z}})
  end
 end
 built.Model:SetAttribute("EntryDiagnosticReady",true)
end
task.spawn(function() local ok,err=pcall(bench.run,"F",deps,1,{1}) if not ok then root:SetAttribute("BenchmarkError",tostring(err)) end end)
return true'''.replace('REFERENCE',__import__('run_asset_matrix').luau(reference)))
    for _ in range(30):
        state=call('local r=game.ReplicatedStorage.LuckboundAssetExperiment local m=workspace:FindFirstChild("GenerationBenchmark") return {Ready=(m and m:GetAttribute("EntryDiagnosticReady"))==true,Error=r:GetAttribute("BenchmarkError") or ""}')
        assert not state.get('Error'),state
        if state.get('Ready'): break
        time.sleep(1)
    assert state.get('Ready'),state
    time.sleep(2)
    observed=client('''local model=workspace:FindFirstChild("GenerationBenchmark") assert(model,"diagnostic map absent")
local parts={} local entry=model:FindFirstChild("0_ES_ENTRY") assert(entry)
for _,part in entry:GetDescendants() do
 if part:IsA("MeshPart") then table.insert(parts,{Name=part.Name,Transparency=part.Transparency,CanCollide=part.CanCollide,Position={part.Position.X,part.Position.Y,part.Position.Z}}) end
end
return game:GetService("HttpService"):JSONEncode({Parts=parts,StreamingEnabled=workspace.StreamingEnabled,StreamingMode=model.ModelStreamingMode.Name})''')
    for _ in range(30):
        row=call('return game:GetService("HttpService"):JSONEncode(require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.GenerationBenchmark).records().Records[1])')
        if row: break
        time.sleep(1)
    assert row,'diagnostic did not finish'
    target.write_text(json.dumps({'Server':row,'Client':observed},indent=2),encoding='utf-8')
    play(False)
    print('Entry replication diagnostic saved')


if __name__=='__main__': main()
