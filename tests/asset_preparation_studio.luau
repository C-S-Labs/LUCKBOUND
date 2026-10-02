--!strict
-- Real scheduler/BindableEvent and MeshPart clones; no network timing in this invariant test.
local root = game.ReplicatedStorage.LuckboundAssetExperiment
local Preparation = require(root.Util.AssetPreparation)
local Profile = require(root.Util.GenerationProfile)
local count = 0
local received = {}
local cache = Preparation.new({
	assetId = function()
		return "rbxassetid://1"
	end,
}, { Cache = true, VisualFidelity = true }, function(_, fidelity)
	count += 1
	task.wait()
	local part = Instance.new("MeshPart")
	table.insert(received, fidelity)
	return part
end)
local profile = Profile.new("A")
local pending = 2
local templates = {}
for index = 1, 2 do
	task.spawn(function()
		templates[index] = cache:load("ASSET_A", true, profile)
		pending -= 1
	end)
end
while pending > 0 do
	task.wait()
end
assert(count == 1 and templates[1] == templates[2], "single-flight did not deduplicate")
assert(profile.Counters.InFlightDeduplications == 1, "missing flight counter")
assert(received[1] == Enum.CollisionFidelity.Box, "visual fidelity policy failed")
local authoritative = cache:load("ASSET_A", false, profile)
assert(count == 2 and authoritative ~= templates[1], "authoritative request reused visual cook")
assert(
	received[2] == Enum.CollisionFidelity.PreciseConvexDecomposition,
	"critical collision downgraded"
)
local model = Instance.new("Model")
local first =
	cache:place("ASSET_A", Vector3.new(3, 4, 5), CFrame.new(10, 20, 30), model, true, profile)
local second =
	cache:place("ASSET_A", Vector3.new(6, 7, 8), CFrame.new(40, 50, 60), model, true, profile)
assert(
	first ~= second and first.Size == Vector3.new(3, 4, 5) and second.Size == Vector3.new(6, 7, 8),
	"clone placement mutated template"
)
assert(templates[1].Parent == nil, "canonical template was parented into map")
model:Destroy()
cache:destroy()
local failed = Preparation.new({
	assetId = function()
		return "rbxassetid://1"
	end,
}, { Cache = true }, function()
	error("expected asset failure")
end)
assert(failed:load("FAIL", false, profile) == nil, "failure must permit loader fallback")
assert(failed:load("FAIL", false, profile) == nil, "failure left an in-flight lock")
failed:destroy()
return { Passed = 9, CreateCalls = count, Counters = profile.Counters }
