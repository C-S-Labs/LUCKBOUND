"""Write a Studio MCP request file without shell quoting Luau source."""
import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('operation', choices=['inspect', 'install', 'refresh', 'start', 'status', 'run', 'results'])
parser.add_argument('--stage', default='A')
args = parser.parse_args()
studio_id = 'b86afbd8-7330-46fd-a078-e6d1379be37f'
request = {'studio_id': studio_id, 'datamodel_type': 'Edit'}
if args.operation == 'inspect':
    request['code'] = '''local root = game.ReplicatedStorage:FindFirstChild("Luckbound")
return {root = root ~= nil, loader = root and #root.Util.ChunkLoader.Source,
core = root and #root.Util.ChunkCore.Source, chunks = root and #root.Content.Chunks:GetChildren(),
props = game.ReplicatedStorage:FindFirstChild("LuckboundProps") ~= nil}'''
elif args.operation in {'install', 'refresh'}:
    code = ['assert(game.ReplicatedStorage:FindFirstChild("LuckboundGenerationExperiment") == nil, "experiment exists")',
            'local root = game.ReplicatedStorage.Luckbound:Clone()',
            'root.Name = "LuckboundGenerationExperiment"',
            'root.Parent = game.ReplicatedStorage']
    if args.operation == 'refresh':
        request['datamodel_type'] = 'Server'
        code = ['local root = game.ReplicatedStorage.LuckboundGenerationExperiment']
    files = ['src/shared/Core/GameConfig.luau', 'src/shared/Util/ChunkCore.luau',
             'src/shared/Util/ChunkLoader.luau', 'src/shared/Util/GenerationProfile.luau',
             'src/shared/Util/ChunkDefinitionCache.luau', 'src/shared/Util/PropRegistry.luau',
             'src/shared/Util/GenerationAnchors.luau', 'src/shared/Util/GenerationBenchmark.luau',
             'src/server/Systems/ExpeditionSystem.luau']
    for path in files:
        source = (root / path).read_text(encoding='utf-8')
        source = source.replace('ReplicatedStorage:WaitForChild("Luckbound")',
                                'ReplicatedStorage:WaitForChild("LuckboundGenerationExperiment")')
        name = Path(path).stem
        folder = 'root.Util' if '/Util/' in path or '/Systems/' in path else 'root.Core'
        code += [f'do local folder = {folder}',
                 f'local module = folder:FindFirstChild("{name}") or Instance.new("ModuleScript")',
                 f'module.Name = "{name}"', f'module.Source = [======[{source}]======]',
                 'module.Parent = folder end']
    code.append('return "isolated experiment installed; original Luckbound untouched"')
    request['code'] = '\n'.join(code)
elif args.operation == 'start':
    request = {'studio_id': studio_id, 'is_start': True}
else:
    request['datamodel_type'] = 'Server'
    base = 'local root = game.ReplicatedStorage.LuckboundGenerationExperiment\nlocal benchmark = require(root.Util.GenerationBenchmark)\n'
    if args.operation == 'run':
        code = '''local expedition = require(root.Util.ExpeditionSystem)
local loot = require(game.ServerScriptService.LuckboundServer.Systems.LootSystem)
local dependencies = expedition.benchmarkDependencies(loot)
dependencies.FloorY = 20000
task.spawn(function()
 local ok, err = pcall(benchmark.run, STAGE, dependencies)
 if not ok then root:SetAttribute("BenchmarkError", tostring(err)) end
end)
return "started stage " .. STAGE'''.replace('STAGE', json.dumps(args.stage))
        request['code'] = base + code
    elif args.operation == 'status':
        request['code'] = base + 'local results = benchmark.records()\nreturn {Error = root:GetAttribute("BenchmarkError"), Running = results.Running, Count = #results.Records, Last = results.Records[#results.Records]}'
    else:
        request['code'] = base + 'return {Error = root:GetAttribute("BenchmarkError"), Results = benchmark.records()}'
target = root / '.tools/studio_request.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(request), encoding='utf-8')
