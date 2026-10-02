--!strict
-- Real Studio physics checks for cache transforms, invalidation and cancellation.
-- Run through the Studio MCP server; this is deliberately not a physics shim.
local root = game.ReplicatedStorage.LuckboundGenerationExperiment
local fixture = root.Util.GenerationAnchors:Clone()
fixture.Name = "AnchorInvariantFixture"
fixture.Parent = root.Util
local Anchors = require(fixture)
local Profile = require(root.Util.GenerationProfile)
local RunService = game:GetService("RunService")
local stage = Instance.new("Model")
stage.Name = "GenerationAnchorTest"
stage:SetAttribute("WorldId", "TEST_WORLD")
stage.Parent = workspace
local chunk = Instance.new("Model")
chunk:SetAttribute("ChunkId", "TEST_CHUNK")
chunk.Parent = stage
local floorY = 40000
local floor = Instance.new("Part")
floor.Anchored = true
floor.Size = Vector3.new(160, 2, 80)
floor.Parent = chunk
local peak = Instance.new("Part")
peak.Anchored = true
peak.Size = Vector3.new(24, 60, 24)
peak.Parent = chunk
local function profile(stageId: string): any
	local value = Profile.new(stageId)
	value.RayBudget = require(root.Core.GameConfig).GenerationBenchmark.RayBudget
	return value
end
local function pose(yaw: number)
	local centre = Vector3.new(yaw * 3, floorY, yaw * 2)
	local frame = CFrame.new(centre) * CFrame.Angles(0, -math.rad(yaw), 0)
	chunk:SetAttribute("Centre", centre)
	chunk:SetAttribute("Yaw", yaw)
	floor.CFrame = frame * CFrame.new(0, -1, 0)
	peak.CFrame = frame * CFrame.new(60, 30, 20)
	RunService.Heartbeat:Wait()
end
local function equal(a: any, b: any)
	for _, name in { "Tips", "Path" } do
		assert(#a[name] == #b[name], name .. " count changed")
		for index, point in a[name] do
			assert((point - b[name][index]).Magnitude < 0.01, name .. " positions/order changed")
		end
	end
end
local passed = 0
local ok, err = pcall(function()
	pose(0)
	local cold = profile("F")
	Anchors.scan(stage, floorY, cold)
	assert(cold.Counters.AtmosphereRaycasts == 1024, "cold discovery count")
	passed += 1
	for _, yaw in { 0, 90, 180, 270 } do
		pose(yaw)
		local baseline = Anchors.scan(stage, floorY, profile("A"))
		local warm = profile("F")
		local cached = Anchors.scan(stage, floorY, warm)
		equal(baseline, cached)
		assert((warm.Counters.AtmosphereRaycasts or 0) == 0, "warm cache rediscovered geometry")
		passed += 1
	end
	stage:SetAttribute("Atmosphere", "CHANGED")
	local invalidated = profile("F")
	Anchors.scan(stage, floorY, invalidated)
	assert(invalidated.Counters.AtmosphereRaycasts == 1024, "asset profile failed to invalidate")
	passed += 1
	local gate = Instance.new("Part")
	gate.Name = "EncounterGate"
	gate.Anchored = true
	gate.CanQuery = false
	gate.Parent = chunk
	local dynamic = profile("F")
	Anchors.scan(stage, floorY, dynamic)
	assert(dynamic.Counters.AtmosphereRaycasts == 1024, "dynamic gate chunk cached")
	passed += 1
	local pending = Anchors.pending(stage, floorY)
	assert(
		pending.Pending and #pending.Tips == 0 and #pending.Path == 0,
		"pending anchors trigger fallback"
	)
	passed += 1
	local deferred = profile("E")
	deferred.RayBudget = 1
	local done, result = false, false
	task.spawn(function()
		result = Anchors.scan(stage, floorY, deferred)
		done = true
	end)
	stage:Destroy()
	while not done do
		RunService.Heartbeat:Wait()
	end
	assert(result == nil, "destroyed stage published anchors")
	passed += 1
end)
stage:Destroy()
fixture:Destroy()
assert(ok, tostring(err))
return { Passed = passed, Physics = "real Studio", Cache = "all four yaws and translated origins" }
