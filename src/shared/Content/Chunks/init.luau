--!strict
-- Chunk registry. Each module returns a LIST of chunks -- one file per world's
-- kit, since pieces are designed as a set and only make sense together.
-- Adding pieces means editing one file here. No System changes.

local Types = require(script.Parent.Parent.Core.Types)

local registry: { [string]: Types.ChunkDefinition } = {}

for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		for _, chunk in require(module) :: { Types.ChunkDefinition } do
			assert(registry[chunk.Id] == nil, `duplicate chunk Id: {chunk.Id}`)
			registry[chunk.Id] = chunk
		end
	end
end

return registry
