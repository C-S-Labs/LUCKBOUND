--!strict
-- Loot pool registry, keyed by pool Id (build spec §7.5). Each module returns
-- a list of pools; a world names the ones it uses in its Loot block.

local registry: { [string]: any } = {}

for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		for _, pool in require(module) :: any do
			assert(registry[pool.Id] == nil, `duplicate loot pool: {pool.Id}`)
			registry[pool.Id] = pool
		end
	end
end

return registry
