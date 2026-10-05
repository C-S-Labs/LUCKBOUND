--!strict
-- Optional portal placements, one data module per world (build spec §7.8).
-- { Id = WORLD_ID, Entrance/Exit = { Chunk = CHUNK_ID, Offset = Vector3 } }.
-- Offset is in the chunk's local frame; absent placements use ENTRY/BOSS centres.

local registry: { [string]: any } = {}
for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		local placements = require(module) :: any
		assert(
			registry[placements.Id] == nil,
			`duplicate portal placements for world: {placements.Id}`
		)
		registry[placements.Id] = placements
	end
end
return registry
