--!strict
-- World-scoped prop resolver used only by explicit generation experiments.
local PropRegistry = {}

function PropRegistry.new(folder: Instance): any
	local modules, cache = {}, {}
	for _, child in folder:GetChildren() do
		if child:IsA("ModuleScript") then
			local key = string.upper(child.Name):gsub("_", "")
			assert(modules[key] == nil, "ambiguous world prop module name")
			modules[key] = child
		end
	end
	local stats = { ModulesRequired = 0, Hits = 0, Misses = 0, Seconds = 0 }
	local registry = { Stats = stats }
	function registry:GetForWorld(worldId: string): any
		if cache[worldId] ~= nil then
			stats.Hits += 1
			return cache[worldId] or nil
		end
		stats.Misses += 1
		local started = os.clock()
		local module = modules[worldId:gsub("_", "")]
		local value = if module then require(module) else nil
		if value then
			assert(value.Id == worldId, "prop module/world mismatch")
			stats.ModulesRequired += 1
		end
		cache[worldId] = value or false
		stats.Seconds += os.clock() - started
		return value
	end
	return registry
end

return PropRegistry
