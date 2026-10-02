"""Measure real Studio server startup after other suites finish, restoring edit source.

Temporary timing only, plus J's metadata view. Never saves/publishes the place,
never rewrites a repository production bootstrap, never replays A-F. Run last.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from run_asset_matrix import ROOT, OUTPUT, STUDIO


def rpc(tool, arguments):
    target=ROOT/'.tools/boot_request.json'
    target.write_text(json.dumps(arguments),encoding='utf-8')
    result=subprocess.run([sys.executable,str(ROOT/'tools/studio_mcp.py'),tool,
                           '--args-file',str(target)],cwd=ROOT,capture_output=True,text=True,check=True)
    envelope=json.loads(result.stdout)['result']
    if envelope.get('isError'): raise RuntimeError(envelope)
    value=envelope['content'][0]['text']
    for _ in range(3):
        if not isinstance(value,str): break
        try: value=json.loads(value)
        except json.JSONDecodeError: break
    return value


def code(context,source):
    return rpc('execute_luau',{'studio_id':STUDIO,'datamodel_type':context,'code':source})


def play(start):
    return rpc('start_stop_play',{'studio_id':STUDIO,'is_start':start})


def main():
    target=OUTPUT/'asset_server_boot.json'
    if target.exists():
        print('Preserved real server boot results')
        return
    assert((OUTPUT/'asset_M6.json').exists()),'finish asset/collision/parallel suite first'
    play(False)
    time.sleep(2)
    original=code('Edit','return game:GetService("HttpService"):JSONEncode(game.ServerScriptService.LuckboundServer.Source)')
    assert isinstance(original,str) and 'AssetManifest.summary()' in original
    (ROOT/'.tools/studio_boot_original_source.luau').write_text(original,encoding='utf-8')
    instrumented=original.replace('--!strict','--!strict\nlocal benchmarkBootStarted=os.clock()',1)
    instrumented=instrumented.replace('\tstepNumber += 1','\tstepNumber += 1\n\tRoot:SetAttribute("BenchmarkBootStep" .. tostring(stepNumber),os.clock()-benchmarkBootStarted)',1)
    injection='''if Root:GetAttribute("BenchmarkBootMode")=="J" then
 local library=require(game.ReplicatedStorage.LuckboundGenerationExperiment.Util.AssetRegistry)
 local started=os.clock()
 library.BootRegistry=library.new(AssetManifest,Chunks)
 local view=library.BootRegistry:GetWorld("VERDANT_VALLEY")
 local count=0 for _ in view do count+=1 end
 Root:SetAttribute("BenchmarkWorldViewSeconds",os.clock()-started)
 Root:SetAttribute("BenchmarkWorldViewAssets",count)
end
Root:SetAttribute("BenchmarkContentReadySeconds",os.clock()-benchmarkBootStarted)
'''
    needle='do\n\tlocal uploaded, placeholder = AssetManifest.summary()'
    assert needle in instrumented
    instrumented=instrumented.replace(needle,injection+needle,1)
    instrumented+='\nRoot:SetAttribute("BenchmarkBootReadySeconds",os.clock()-benchmarkBootStarted)\n'
    registry=(ROOT/'src/shared/Util/AssetRegistry.luau').read_text(encoding='utf-8')
    rows=[]
    try:
        code('Edit','''local root=game.ReplicatedStorage.LuckboundGenerationExperiment
local module=root.Util:FindFirstChild("AssetRegistry") or Instance.new("ModuleScript")
module.Name="AssetRegistry" module.Source=[======['''+registry+''']======] module.Parent=root.Util
game.ServerScriptService.LuckboundServer.Source=[======['''+instrumented+''']======]
return true''')
        for repeat in range(1,6):
            for mode in ['A','J']:
                code('Edit','game.ReplicatedStorage.Luckbound:SetAttribute("BenchmarkBootMode",'+json.dumps(mode)+') return true')
                play(True)
                deadline=time.monotonic()+180
                while True:
                    time.sleep(3)
                    row=code('Server','''local root=game.ReplicatedStorage.Luckbound
return {Ready=root:GetAttribute("BenchmarkBootReadySeconds"),ContentReady=root:GetAttribute("BenchmarkContentReadySeconds"),
 WorldViewSeconds=root:GetAttribute("BenchmarkWorldViewSeconds"),WorldViewAssets=root:GetAttribute("BenchmarkWorldViewAssets"),
 TotalMemoryMb=game:GetService("Stats"):GetTotalMemoryUsageMb(),LuaHeapKb=collectgarbage("count")}''')
                    if row.get('Ready') is not None: break
                    if time.monotonic()>deadline: raise RuntimeError('server boot did not reach ready')
                row.update(Mode=mode,Repeat=repeat)
                rows.append(row)
                print(f"Boot {mode} repeat {repeat}: {row['Ready']:.3f}s, content {row['ContentReady']:.4f}s",flush=True)
                play(False)
                time.sleep(2)
        target.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    finally:
        try: play(False)
        except Exception: pass
        time.sleep(2)
        code('Edit','game.ServerScriptService.LuckboundServer.Source=[======['+original+']======]\ngame.ReplicatedStorage.Luckbound:SetAttribute("BenchmarkBootMode",nil) return true')
        restored=code('Edit','return game:GetService("HttpService"):JSONEncode(game.ServerScriptService.LuckboundServer.Source)')
        assert restored==original,'bootstrap source restoration failed'
        print('Original Studio bootstrap restored; place not saved/published.',flush=True)


if __name__=='__main__': main()
