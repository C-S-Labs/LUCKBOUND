--!strict
-- Scenario atmospheres per world, keyed by world Id. Each module holds a
-- world's Profiles: overrides of its Environment (AmbienceCore.overlay), one
-- of which a run may draw from its seed (AmbienceCore.pickAtmosphere).

local registry: { [string]: any } = {}

for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		local set = require(module) :: any
		assert(registry[set.Id] == nil, `duplicate atmospheres for world: {set.Id}`)
		registry[set.Id] = set
	end
end

return registry
