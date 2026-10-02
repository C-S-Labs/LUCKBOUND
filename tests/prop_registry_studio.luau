--!strict
-- Exercise actual ModuleScript require/cache behavior, including absent worlds.
local root = game.ReplicatedStorage.LuckboundGenerationExperiment
local Registry = require(root.Util.PropRegistry)
local expected = require(game.ReplicatedStorage.Luckbound.Content.Props)
-- The privileged MCP setup prepares fresh modules with execution markers.
local folder = root.Content.PropRegistryInvariantFixture
local registry = Registry.new(folder)
local before = collectgarbage("count")
local set = registry:GetForWorld("SKY_CITADEL")
local after = collectgarbage("count")
assert(set.Id == "SKY_CITADEL" and registry.Stats.ModulesRequired == 1)
assert(folder.SkyCitadel:GetAttribute("InitializedForTest") == true)
assert(folder.VerdantValley:GetAttribute("InitializedForTest") == nil)
assert(folder.EtherealScape:GetAttribute("InitializedForTest") == nil)
assert(registry:GetForWorld("SKY_CITADEL") == set, "cache identity changed")
assert(registry.Stats.Hits == 1 and registry.Stats.Misses == 1)
assert(registry:GetForWorld("NO_SUCH_WORLD") == nil)
assert(registry:GetForWorld("NO_SUCH_WORLD") == nil)
assert(
	registry.Stats.ModulesRequired == 1 and registry.Stats.Misses == 2 and registry.Stats.Hits == 2
)
local function equal(a: any, b: any)
	assert(type(a) == type(b), "definition type changed")
	if type(a) == "table" then
		for key, value in a do
			equal(value, b[key])
		end
		for key in b do
			assert(a[key] ~= nil, "definition field missing")
		end
	else
		assert(a == b, "definition value changed")
	end
end
equal(set, expected.SKY_CITADEL)
local result = {
	Passed = 9,
	ModulesRequired = registry.Stats.ModulesRequired,
	CacheHits = registry.Stats.Hits,
	CacheMisses = registry.Stats.Misses,
	SkyCitadelRequireHeapDeltaKb = after - before,
	Note = "live Lua heap delta includes require allocations and concurrent VM activity",
}
folder:Destroy()
return result
