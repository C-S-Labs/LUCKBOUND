"""Cold module/content-ready measurements in isolated clones, separate from entry timers.

This does not restart the live server or initialize gameplay Systems. Full server
boot is preserved from console logs; this experiment measures its content phase.
"""
import json
from run_asset_matrix import OUTPUT, call

CODE = '''local original=game.ReplicatedStorage.Luckbound
local stats=game:GetService("Stats")
local rows={}
for repeatIndex=1,5 do
 for _,mode in {"MANIFEST","WORLD_VIEW"} do
  local root=original:Clone()
  root.Name="LuckboundContentBootExperiment"
  root.Parent=game.ReplicatedStorage
  local memory=stats:GetTotalMemoryUsageMb()
  local heap=collectgarbage("count")
  local started=os.clock()
  local manifest=require(root.Content.AssetManifest)
  local manifestSeconds=os.clock()-started
  local loaded={}
  local names={worlds="Worlds",chunks="Chunks",props="Props",fixtures="Fixtures",lootPools="LootPools",codes="Codes",events="Events",scenarios="Scenarios"}
  for key,name in names do loaded[key]=require(root.Content[name]) end
  loaded.config=require(root.Core.GameConfig)
  loaded.manifest=manifest
  loaded.animations=require(root.Content.Animations.Player)
  for key,name in {hub="Crossroads",menu="Menu",cinematics="Cinematics",palettes="Palettes"} do loaded[key]=require(root.Content.Hub[name]) end
  local beforeValidation=os.clock()
  require(root.Util.Schema).validateAll(loaded)
  local validationSeconds=os.clock()-beforeValidation
  local viewSeconds=0
  local viewAssets=0
  if mode=="WORLD_VIEW" then
   local viewStarted=os.clock()
   local registryModule=game.ReplicatedStorage.LuckboundAssetExperiment.Util.AssetRegistry:Clone()
   registryModule.Parent=root.Util
   local view=require(registryModule).new(manifest,loaded.chunks):GetWorld("VERDANT_VALLEY")
   for _ in view do viewAssets+=1 end
   viewSeconds=os.clock()-viewStarted
  end
  table.insert(rows,{Repeat=repeatIndex,Mode=mode,ManifestRequireSeconds=manifestSeconds,
   ContentReadySeconds=os.clock()-started,ValidationSeconds=validationSeconds,
   WorldViewSeconds=viewSeconds,WorldViewAssets=viewAssets,
   MemoryDeltaMb=stats:GetTotalMemoryUsageMb()-memory,LuaHeapDeltaKb=collectgarbage("count")-heap})
  root:Destroy()
  task.wait()
 end
end
return game:GetService("HttpService"):JSONEncode(rows)'''


def main():
    target = OUTPUT / 'asset_content_boot.json'
    if target.exists():
        print('Preserved existing content boot results')
        return
    target.write_text(json.dumps(call(CODE), indent=2), encoding='utf-8')
    print('Saved 10 cold content-ready samples; gameplay Systems boot not replayed')


if __name__ == '__main__':
    main()
