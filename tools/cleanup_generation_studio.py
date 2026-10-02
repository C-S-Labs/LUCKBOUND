"""Remove only this experiment's scratch roots; verify original bootstrap source."""
import json
from run_asset_matrix import ROOT, OUTPUT
from measure_server_boot import code, play


def main():
    play(False)
    original=(ROOT/'.tools/studio_boot_original_source.luau').read_text(encoding='utf-8')
    actual=code('Edit','return game:GetService("HttpService"):JSONEncode(game.ServerScriptService.LuckboundServer.Source)')
    assert actual==original,'original bootstrap source differs; do not clean unrelated state'
    result=code('Edit','''local removed={}
for _,name in {"LuckboundGenerationExperiment","LuckboundAssetExperiment"} do
 local root=game.ReplicatedStorage:FindFirstChild(name)
 if root then table.insert(removed,name) root:Destroy() end
end
return {Removed=removed,BootstrapRestored=true,NoSaveOrPublish=true}''')
    (OUTPUT/'generation_studio_cleanup.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result)


if __name__=='__main__': main()
