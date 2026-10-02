"""Read only recent real-player observations while the cohort continues."""
import json
from run_asset_matrix import call
print(json.dumps(call('''local r=require(game.ReplicatedStorage.LuckboundAssetExperiment.Util.GenerationBenchmark).records()
local rows={} for index=math.max(1,#r.Records-2),#r.Records do
 local p=r.Records[index] table.insert(rows,{World=p.WorldId,Seed=p.Seed,Ready=p.PlayableSeconds,
 MapReady=p.StructureSeconds,Grounded=p.PlayerGrounded,FinalY=p.PlayerFinalY,Placed=p.PlayerPlacedSeconds}) end
return {Running=r.Running,Count=#r.Records,Recent=rows}''')))
