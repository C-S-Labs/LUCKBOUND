"""Read only the failed scratch map's entry tags; do not alter running suites."""
from run_asset_matrix import call
import json
print(json.dumps(call('''local map=workspace:FindFirstChild("GenerationBenchmark")
local rows={} if map then for _,child in map:GetChildren() do table.insert(rows,{Name=child.Name,Role=child:GetAttribute("Role"),Id=child:GetAttribute("ChunkId"),Index=child:GetAttribute("Index")}) end end
return {Map=map~=nil,Children=rows}''')))
