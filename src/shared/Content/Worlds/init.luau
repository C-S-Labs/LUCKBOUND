--!strict
-- World registry. Adding a world = adding one file here and one line below.
-- No System changes. Build spec §1 prime directive.

local Types = require(script.Parent.Parent.Core.Types)

local registry: { [string]: Types.WorldDefinition } = {}

for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		local world = require(module) :: Types.WorldDefinition
		assert(registry[world.Id] == nil, `duplicate world Id: {world.Id}`)
		registry[world.Id] = world
	end
end

return registry
