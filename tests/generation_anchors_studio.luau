--!strict
-- Real geometry, all quarter-turn transforms, bounded cache and cancellation.
local Factory = require(game.ReplicatedStorage.Luckbound.Util.GenerationAnchors)
local RunService = game:GetService("RunService")
local config = {
	AssetPreparationDiagnostics = true,
	DeferredAtmosphere = false,
	AtmosphereRayBudget = 128,
	AtmosphereCacheEntries = 2,
}
local cache = Factory.new(config)
local stage = Instance.new("Model")
stage.Name = "ProductionAnchorFixture"
stage.Parent = workspace
stage:SetAttribute("WorldId", "TEST")
local chunk = Instance.new("Model")
chunk:SetAttribute("ChunkId", "TEST")
chunk.Parent = stage
local floor = Instance.new("Part")
floor.Anchored = true
floor.Size = Vector3.new(160, 2, 80)
floor.Parent = chunk
local peak = Instance.new("Part")
peak.Anchored = true
peak.Size = Vector3.new(24, 60, 24)
peak.Parent = chunk
local floorY = 40000
local function pose(yaw: number)
	local centre = Vector3.new(yaw * 3, floorY, yaw * 2)
	local frame = CFrame.new(centre) * CFrame.Angles(0, -math.rad(yaw), 0)
	chunk:SetAttribute("Centre", centre)
	chunk:SetAttribute("Yaw", yaw)
	floor.CFrame = frame * CFrame.new(0, -1, 0)
	peak.CFrame = frame * CFrame.new(60, 30, 20)
	RunService.Heartbeat:Wait()
end
local passed = 0
local function check(ok: boolean, message: string)
	assert(ok, message)
	passed += 1
end
pose(0)
cache.scan(stage, floorY)
check(cache.stats().Counters.AtmosphereRaycasts == 1024, "cold queries")
for _, yaw in { 0, 90, 180, 270 } do
	pose(yaw)
	local before = cache.stats().Counters.AtmosphereRaycasts
	local warm = cache.scan(stage, floorY)
	local control = Factory.new(config).scan(stage, floorY)
	for _, field in { "Tips", "Path" } do
		assert(#warm[field] == #control[field], "anchor count differs")
		for index, point in warm[field] do
			assert((point - control[field][index]).Magnitude < 0.01, "transformed order differs")
		end
	end
	check(cache.stats().Counters.AtmosphereRaycasts == before, "warm geometry rediscovery")
end
for _, id in { "A", "B", "C" } do
	stage:SetAttribute("Atmosphere", id)
	cache.scan(stage, floorY)
end
check(cache.stats().Entries == 2, "cache cap/invalidation")
local gate = Instance.new("Part")
gate.Name = "EncounterGate"
gate.CanQuery = false
gate.Anchored = true
gate.Parent = chunk
local before = cache.stats().Counters.AtmosphereRaycasts
cache.scan(stage, floorY)
cache.scan(stage, floorY)
check(cache.stats().Counters.AtmosphereRaycasts == before + 2048, "dynamic gate cached")
local pending = cache.pending(stage, floorY)
check(pending.Pending and #pending.Tips == 0 and #pending.Path == 0, "pending client fallback")
local deferred = Factory.new({
	AssetPreparationDiagnostics = true,
	DeferredAtmosphere = true,
	AtmosphereRayBudget = 1,
	AtmosphereCacheEntries = 2,
})
check(deferred.scan(stage, floorY, function()
	return false
end) == nil, "stale completion")
stage:Destroy()
cache.clear()
check(cache.stats().Entries == 0, "lifecycle clear")
return { Passed = passed, Physics = "real Studio", Rotations = 4 }
