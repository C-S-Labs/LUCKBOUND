"""Focused Studio contracts; restores temporary sources, never saves/publishes.

The baseline loader is injected from git 714fa33, not maintained as a second module.
Long catalogue work runs asynchronously so MCP's per-request deadline is respected.
"""
import argparse
import json
import subprocess
import time

import verify_generation_migration as studio


def fixture(context, name, source, parent):
    return studio.code(context, 'local m=Instance.new("ModuleScript") m.Name="' + name +
                       '" m.Source=[======[' + source + ']======] m.Parent=' + parent +
                       ' local ok,result=pcall(require,m) m:Destroy() assert(ok,result) return result')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--invariants-only', action='store_true', help='reuse the completed catalogue; recheck only focused invariants')
    args = parser.parse_args()
    output = studio.OUT / 'generation_migration_contracts.json'
    if output.exists() and not args.invariants_only:
        print('Preserved completed focused contracts')
        return
    studio.play(False)
    try:
        studio.install()
        studio.play(True)
        time.sleep(5)
        results = json.loads(output.read_text()) if output.exists() else {}
        for name in ['asset_preparation_studio', 'generation_anchors_studio']:
            source = (studio.ROOT / f'tests/{name}.luau').read_text()
            results[name] = fixture('Server', name, source, 'game.ServerStorage')
            print(name, results[name], flush=True)
        source = (studio.ROOT / 'tests/atmosphere_late_update_studio.luau').read_text()
        results['atmosphere_late_update_studio'] = fixture(
            'Client', 'AtmosphereContractFixture', source,
            'game.Players.LocalPlayer.PlayerScripts.LuckboundClient.Controllers')
        if args.invariants_only:
            assert 'vv_catalogue' in results, 'complete catalogue first'
            output.write_text(json.dumps(results, indent=2), encoding='utf-8')
            return
        baseline = subprocess.run(['git', 'show', '714fa33:src/shared/Util/ChunkLoader.luau'],
                                  cwd=studio.ROOT, capture_output=True, text=True,
                                  encoding='utf-8', check=True).stdout
        source = (studio.ROOT / 'tests/chunk_loader_studio.luau').read_text()
        studio.code('Server', '''local status=Instance.new("StringValue") status.Name="CatalogueVerification" status.Parent=game.ServerStorage
task.spawn(function()
 local baseline=Instance.new("ModuleScript") baseline.Source=[======[''' + baseline + ''']======] baseline.Parent=game.ReplicatedStorage.Luckbound.Util
 local fixture=Instance.new("ModuleScript") fixture.Source=[======[''' + source + ''']======] fixture.Parent=game.ServerStorage
 local ok,result=pcall(function() return require(fixture).run(require(baseline)) end)
 fixture:Destroy() baseline:Destroy()
 status.Value=game:GetService("HttpService"):JSONEncode({Ok=ok,Result=result})
end) return true''')
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            length = studio.code('Server', 'return #game.ServerStorage.CatalogueVerification.Value')
            if length:
                # MCP truncates large strings; preserve raw geometry through bounded reads.
                fragments = [studio.code('Server', f'return {{Fragment=game.ServerStorage.CatalogueVerification.Value:sub({start},{start + 29999})}}')['Fragment']
                             for start in range(1, length + 1, 30000)]
                value = json.loads(''.join(fragments))
                assert value['Ok'], value['Result']
                results['vv_catalogue'] = value['Result']
                break
            time.sleep(1)
        else:
            raise TimeoutError('VV catalogue')
        output.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print('Full catalogue complete', flush=True)
    finally:
        studio.restore()
        print('Original Studio sources restored; no save/publish', flush=True)


if __name__ == '__main__':
    main()
