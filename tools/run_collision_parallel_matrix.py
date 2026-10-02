"""After G-K, run L's authored sample, then M's remaining-load worker sweep."""
import json
import time
from pathlib import Path
from run_asset_matrix import ROOT, OUTPUT, call, install, luau


def module(folder, name, path):
    source = (ROOT / path).read_text(encoding='utf-8')
    return '\n'.join([f'local m=Instance.new("ModuleScript") m.Name="{name}"',
                      f'm.Source=[======[{source}]======]', f'm.Parent={folder}'])


def main():
    while not (OUTPUT / 'asset_GHIK.json').exists():
        print('Waiting for G-K contributions before L and M.', flush=True)
        time.sleep(60)
    target = OUTPUT / 'asset_L.json'
    if not target.exists():
        code = 'local root=game.ReplicatedStorage.LuckboundAssetExperiment\n'
        code += module('root.Content', 'CollisionSamples', 'src/shared/Content/CollisionSamples.luau') + '\n'
        code += module('root.Util', 'CollisionProxySample', 'src/shared/Util/CollisionProxySample.luau') + '\n'
        code += module('root.Util', 'CollisionSampleTest', 'tests/collision_sample_studio.luau') + '\n'
        code += 'require(root.Util.CollisionSampleTest) return true'
        call(code)
        while True:
            status = call('''local root=game.ReplicatedStorage.LuckboundAssetExperiment
local r=require(root.Util.CollisionSampleTest).records()
return {Running=root:GetAttribute("CollisionSampleRunning"),Error=root:GetAttribute("CollisionSampleError"),Count=#r}''')
            if status.get('Error'):
                raise RuntimeError(status['Error'])
            print(f"L: {status['Count']}/48 sample builds", flush=True)
            if not status['Running']:
                break
            time.sleep(15)
        rows = [call('return game:GetService("HttpService"):JSONEncode(require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.CollisionSampleTest).records()[' + str(i) + '])') for i in range(1, status['Count'] + 1)]
        assert len(rows) == 48
        target.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    # Single-flight invariant checks use a real MeshPart + scheduler, not network timing.
    invariants = OUTPUT / 'asset_cache_invariants.json'
    if not invariants.exists():
        code = 'local root=game.ReplicatedStorage.LuckboundAssetExperiment\n'
        code += module('root.Util', 'AssetPreparationTest', 'tests/asset_preparation_studio.luau')
        code += '\nreturn game:GetService("HttpService"):JSONEncode(require(root.Util.AssetPreparationTest))'
        invariants.write_text(json.dumps(call(code), indent=2), encoding='utf-8')
    control = json.loads((OUTPUT / 'asset_ASSET_CONTROL.json').read_text(encoding='utf-8'))
    reference = {key + ':' + row.get('Atmosphere', ''): yaw for row in control for key, yaw in row['ArtYaws'].items()}
    # GHIK already measured worker=1. Preserve it; do not repeat its cohort.
    for workers in [2, 4, 6]:
        policy = {'Id': f'M{workers}', 'LocalTemplates': True, 'VisualFidelity': True,
                  'Cache': True, 'Prepare': 'Seed', 'Workers': workers}
        target = OUTPUT / ('asset_' + policy['Id'] + '.json')
        if target.exists():
            continue
        live=call('''local root=game.ReplicatedStorage:FindFirstChild("LuckboundAssetExperiment")
if not root then return {} end
local r=require(root.Util.GenerationBenchmark).records() local last=r.Records[#r.Records]
return {Mode=root:GetAttribute("AssetBenchmarkPolicy") or (last and last.AssetExperiment),Running=r.Running,Count=#r.Records}''')
        if live.get('Mode')==policy['Id'] and (live.get('Running') or live.get('Count')==30):
            print(policy['Id']+': resuming existing Studio run',flush=True)
        else:
            install(policy, reference)
        count = -1
        while True:
            status = call('''local root=game.ReplicatedStorage.LuckboundAssetExperiment
local r=require(root.Util.GenerationBenchmark).records()
return {Running=r.Running,Error=root:GetAttribute("BenchmarkError"),Count=#r.Records}''')
            if status.get('Error'):
                raise RuntimeError(status['Error'])
            if status['Count'] != count:
                count = status['Count']
                print(f"M{workers}: {count}/30 maps", flush=True)
            if not status['Running']:
                break
            time.sleep(15)
        rows = [call('return game:GetService("HttpService"):JSONEncode(require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.GenerationBenchmark).records().Records[' + str(i) + '])') for i in range(1, count + 1)]
        assert len(rows) == 30
        target.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print('L-M COMPLETE', flush=True)


if __name__ == '__main__':
    main()
