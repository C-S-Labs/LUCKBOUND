"""Continue after A-F; never restarts or overwrites that matrix.

Fresh module context per policy, five paired seeds x three worlds x two repeats.
The cache is cold at policy start and retained across seeds/repeats. Source and
query controls are captured before cheaper visual collision is enabled.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/benchmarks'
STUDIO = 'b86afbd8-7330-46fd-a078-e6d1379be37f'
SEEDS = [1, 997, 65537, 999983, 1704274940]
POLICIES = [
    {'Id': 'ASSET_CONTROL'},
    {'Id': 'G', 'LocalTemplates': True},
    {'Id': 'H', 'VisualFidelity': True},
    {'Id': 'I', 'Cache': True},
    {'Id': 'J', 'WorldRegistry': True},
    {'Id': 'K_SEED', 'Cache': True, 'Prepare': 'Seed', 'Workers': 1},
    {'Id': 'K_WORLD', 'Cache': True, 'Prepare': 'World', 'Workers': 1},
    {'Id': 'GHIK', 'LocalTemplates': True, 'VisualFidelity': True,
     'Cache': True, 'Prepare': 'Seed', 'Workers': 1},
]
FILES = ['src/shared/Core/GameConfig.luau', 'src/shared/Util/ChunkCore.luau',
         'src/shared/Util/ChunkLoader.luau', 'src/shared/Util/GenerationProfile.luau',
         'src/shared/Util/ChunkDefinitionCache.luau', 'src/shared/Util/PropRegistry.luau',
         'src/shared/Util/GenerationAnchors.luau', 'src/shared/Util/GenerationBenchmark.luau',
         'src/shared/Util/AssetPreparation.luau', 'src/shared/Util/AssetRegistry.luau',
         'src/shared/Util/AssetGeometryCheck.luau', 'src/server/Systems/ExpeditionSystem.luau']


def call(code):
    request = ROOT / '.tools/asset_request.json'
    request.write_text(json.dumps({'studio_id': STUDIO, 'datamodel_type': 'Server',
                                  'code': code}), encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'tools/studio_mcp.py'),
                             'execute_luau', '--args-file', str(request)], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    envelope = json.loads(result.stdout)['result']
    if envelope.get('isError'):
        raise RuntimeError(envelope)
    content = envelope['content'][0]['text']
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return content
    if isinstance(value, str):
        value = json.loads(value)
    return value


def luau(value):
    if isinstance(value, dict):
        return '{' + ','.join('[' + json.dumps(k) + ']=' + luau(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '{' + ','.join(map(luau, value)) + '}'
    return json.dumps(value)


def install(policy, reference, stage='A', run=True, source_overrides=None):
    code = ['local old=game.ReplicatedStorage:FindFirstChild("LuckboundAssetExperiment")',
            'if old then old:Destroy() end',
            'local root=game.ReplicatedStorage.Luckbound:Clone()',
            'root.Name="LuckboundAssetExperiment"', 'root.Parent=game.ReplicatedStorage']
    for path in FILES:
        source = (source_overrides or {}).get(path, (ROOT / path).read_text(encoding='utf-8')).replace(
            'ReplicatedStorage:WaitForChild("Luckbound")',
            'ReplicatedStorage:WaitForChild("LuckboundAssetExperiment")')
        name = Path(path).stem
        folder = 'root.Core' if '/Core/' in path else 'root.Util'
        code += [f'do local folder={folder}',
                 f'local module=folder:FindFirstChild("{name}") or Instance.new("ModuleScript")',
                 f'module.Name="{name}"', f'module.Source=[======[{source}]======]',
                 'module.Parent=folder end']
    code += ['local bench=require(root.Util.GenerationBenchmark)',
             'root:SetAttribute("AssetBenchmarkPolicy",' + luau(policy['Id']) + ')',
             'local expedition=require(root.Util.ExpeditionSystem)',
             'local loot=require(game.ServerScriptService.LuckboundServer.Systems.LootSystem)',
             'local deps=expedition.benchmarkDependencies(loot)',
             'deps.FloorY=require(root.Core.GameConfig).Expedition.StageOrigin.Y',
             'deps.verify=require(root.Util.AssetGeometryCheck).sample',
             'deps.AssetPolicy=' + luau(policy),
             'deps.ReferenceYaws=' + (luau(reference) if reference else 'nil')]
    if run:
        code += ['task.spawn(function() local ok,err=pcall(bench.run,' + luau(stage) + ',deps,2,' + luau(SEEDS) + ')',
                 'if not ok then root:SetAttribute("BenchmarkError",tostring(err)) end end)']
    code.append('return true')
    return call('\n'.join(code))


def main():
    while not (OUTPUT / 'generation_paired_F.json').exists():
        print('Waiting for preserved A-F matrix to complete.', flush=True)
        time.sleep(60)
    reference = {}
    for policy in POLICIES:
        target = OUTPUT / ('asset_' + policy['Id'] + '.json')
        if target.exists():
            rows = json.loads(target.read_text(encoding='utf-8'))
            print(policy['Id'] + ': preserved existing results', flush=True)
        else:
            live = call('''local root=game.ReplicatedStorage:FindFirstChild("LuckboundAssetExperiment")
if not root then return {Exists=false} end
local r=require(root.Util.GenerationBenchmark).records()
local last=r.Records[#r.Records]
return {Exists=true,Running=r.Running,Count=#r.Records,Mode=root:GetAttribute("AssetBenchmarkPolicy") or (last and last.AssetExperiment)}''')
            if live.get('Mode') == policy['Id'] and (live.get('Running') or live.get('Count') == 30):
                print(policy['Id'] + ': resuming existing Studio run', flush=True)
            else:
                install(policy, reference)
            count = -1
            while True:
                state = call('''local root=game.ReplicatedStorage.LuckboundAssetExperiment
local r=require(root.Util.GenerationBenchmark).records()
return {Running=r.Running,Count=#r.Records,Error=root:GetAttribute("BenchmarkError")}''')
                if state.get('Error'):
                    raise RuntimeError(state['Error'])
                if state['Count'] != count:
                    count = state['Count']
                    print(f"{policy['Id']}: {count}/30 maps", flush=True)
                if not state['Running']:
                    break
                time.sleep(15)
            rows = []
            for index in range(1, count + 1):
                rows.append(call('return game:GetService("HttpService"):JSONEncode(require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.GenerationBenchmark).records().Records[' + str(index) + '])'))
            assert len(rows) == 30
            target.write_text(json.dumps(rows, indent=2), encoding='utf-8')
            print(policy['Id'] + ': saved raw results', flush=True)
        if policy['Id'] == 'ASSET_CONTROL':
            for row in rows:
                for key, yaw in row['ArtYaws'].items():
                    reference[key + ':' + row.get('Atmosphere', '')] = yaw
    print('ASSET MATRIX G-K COMPLETE; L collision sample and M remain separate.', flush=True)


if __name__ == '__main__':
    main()
