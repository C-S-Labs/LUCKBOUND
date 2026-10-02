"""Drain baseline A, then run B-F in fresh module contexts and persist raw results.

Each paired cohort uses five spread seeds x three worlds x two repeats (30 maps).
The already-running larger baseline is retained separately, then filtered by the
same seeds/repeats for comparisons. Does not save/publish the place.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO = 'b86afbd8-7330-46fd-a078-e6d1379be37f'
SEEDS = [1, 997, 65537, 999983, 1704274940]
OUTPUT = ROOT / 'docs/benchmarks'
OUTPUT.mkdir(exist_ok=True)


def call(code):
    request = {'studio_id': STUDIO, 'datamodel_type': 'Server', 'code': code}
    target = ROOT / '.tools/matrix_request.json'
    target.write_text(json.dumps(request), encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'tools/studio_mcp.py'),
                             'execute_luau', '--args-file', str(target)],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    envelope = json.loads(result.stdout)['result']
    if envelope.get('isError'):
        raise RuntimeError(envelope)
    content = envelope['content'][0]['text']
    return json.loads(content)


def records(value):
    if isinstance(value, dict):
        return [value[key] for key in sorted(value, key=lambda key: int(key))]
    return value


def main():
    for stage in 'ABCDEF':
        if stage != 'A':
            call('''local old=game.ReplicatedStorage.LuckboundGenerationExperiment
local root=old:Clone()
old:Destroy()
root.Parent=game.ReplicatedStorage
root:SetAttribute("BenchmarkError", nil)
root:SetAttribute("BenchmarkStage", STAGE)
local benchmark=require(root.Util.GenerationBenchmark)
local expedition=require(root.Util.ExpeditionSystem)
local loot=require(game.ServerScriptService.LuckboundServer.Systems.LootSystem)
local dependencies=expedition.benchmarkDependencies(loot)
dependencies.FloorY=require(root.Core.GameConfig).Expedition.StageOrigin.Y
task.spawn(function()
 local ok,err=pcall(benchmark.run, STAGE, dependencies, 2, SEEDS)
 if not ok then root:SetAttribute("BenchmarkError", tostring(err)) end
end)
return true'''.replace('STAGE', json.dumps(stage)).replace('SEEDS', '{' + ','.join(map(str, SEEDS)) + '}'))
        previous = -1
        while True:
            status = call('''local root=game.ReplicatedStorage.LuckboundGenerationExperiment
local result=require(root.Util.GenerationBenchmark).records()
local last=result.Records[#result.Records]
return {Running=result.Running,Count=#result.Records,Error=root:GetAttribute("BenchmarkError"),Last=last}''')
            if status.get('Error'):
                raise RuntimeError(status['Error'])
            if status['Count'] != previous:
                previous = status['Count']
                last = status.get('Last', {})
                print(f"{stage}: {previous} maps, last {last.get('WorldId')} seed {last.get('Seed')}, playable {last.get('PlayableSeconds', 0):.3f}s", flush=True)
            if not status['Running']:
                break
            time.sleep(15)
        raw = call('return require(game.ReplicatedStorage.LuckboundGenerationExperiment.Util.GenerationBenchmark).records().Records')
        raw = records(raw)
        (OUTPUT / f'generation_studio_{stage}.json').write_text(json.dumps(raw, indent=2), encoding='utf-8')
        paired = [row for row in raw if row['Seed'] in SEEDS and row['Repeat'] <= 2]
        assert len(paired) == 30, (stage, len(paired))
        (OUTPUT / f'generation_paired_{stage}.json').write_text(json.dumps(paired, indent=2), encoding='utf-8')
        print(f"{stage}: saved {len(raw)} raw / {len(paired)} paired samples", flush=True)
    audit = call('return _G.GenerationBenchmarkAudit or {}')
    (OUTPUT / 'generation_yaw_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print('MATRIX COMPLETE', flush=True)


if __name__ == '__main__':
    main()
