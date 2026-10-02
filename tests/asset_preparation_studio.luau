--!strict
-- Real Roblox scheduling, server ownership and MeshPart clones; injected API latency only.
local Preparation = require(game.ReplicatedStorage.Luckbound.Util.AssetPreparation)
local passed = 0
local function check(condition: boolean, message: string)
	assert(condition, message)
	passed += 1
end
local config = { AssetPreparationWorkers = 3, AssetPreparationDiagnostics = true }
local manifest = {
	assetId = function(key)
		return "rbxassetid://" .. tostring(string.byte(key))
	end,
}
local calls, active, maximum = 0, 0, 0
local fidelity = {}
local fail = false
local owner = Preparation.new(manifest, config, {
	Kits = Instance.new("Folder"),
	CreateMesh = function(_id, requested)
		calls += 1
		active += 1
		maximum = math.max(maximum, active)
		table.insert(fidelity, requested)
		task.wait()
		active -= 1
		if fail then
			error("injected preparation failure")
		end
		return Instance.new("MeshPart")
	end,
})
local first = owner:clone("A", "VISUAL_ONLY")
check(first.ok and calls == 1, "first preparation")
local second = owner:clone("A", "VISUAL_ONLY")
check(second.ok and calls == 1 and first.value ~= second.value, "second clones cache")
check(
	first.value.Size == second.value.Size and first.value.Color == second.value.Color,
	"clone configuration"
)
check(fidelity[1] == Enum.CollisionFidelity.Box, "visual requested precise")
check(
	owner.Storage.Parent == game.ServerStorage and not owner.Storage:IsDescendantOf(workspace),
	"ownership replicates/participates in physics"
)
first.value:Destroy()
second.value:Destroy()
local remaining = 2
local results = {}
for index = 1, 2 do
	task.spawn(function()
		results[index] = owner:prepare("B", "AUTHORITATIVE_MESH_COLLISION")
		remaining -= 1
	end)
end
while remaining > 0 do
	task.wait()
end
check(calls == 2 and results[1].value == results[2].value, "single flight")
check(owner:stats().InFlightDeduplications == 1, "flight count")
check(fidelity[2] == Enum.CollisionFidelity.PreciseConvexDecomposition, "authoritative fidelity")
owner:prepare("A", "AUTHORITATIVE_MESH_COLLISION")
check(calls == 3, "authoritative reused visual-only preparation")
fail = true
check(not owner:prepare("C", "VISUAL_ONLY").ok, "failure result")
fail = false
check(owner:prepare("C", "VISUAL_ONLY").ok, "failure poisoned retry")
local requests = {}
for _, key in { "D", "E", "F", "G", "H", "I", "J", "D" } do
	table.insert(requests, { Key = key, Role = "AUTHORITATIVE_MESH_COLLISION" })
end
local before = calls
check(
	owner:prepareMany(requests).ok and calls == before + 7,
	"working queue deduplication/completion"
)
check(maximum == 3 and owner:stats().MaximumActiveWorkers == 3, "worker bound")
fail = true
check(not owner:prepareMany({
	{ Key = "K", Role = "VISUAL_ONLY" },
	{ Key = "L", Role = "VISUAL_ONLY" },
}).ok, "error queue did not finish")
check(owner:stats().ActiveWorkers == 0, "worker error leaked slot")
fail = false
check(owner:prepare("K", "VISUAL_ONLY").ok, "queue error retry")
owner:destroy()
check(owner.Storage.Parent == nil and not owner:prepare("M", "VISUAL_ONLY").ok, "owner teardown")

local kits = game.ServerStorage:FindFirstChild("LuckboundChunkKits")
local authored = kits and kits:FindFirstChildWhichIsA("MeshPart", true)
assert(authored, "real authored fixture unavailable")
local localCalls = 0
local localOwner = Preparation.new(
	{
		assetId = function()
			return authored.MeshId
		end,
	},
	config,
	{
		Kits = kits,
		CreateMesh = function()
			localCalls += 1
			return Instance.new("MeshPart")
		end,
	}
)
local cloned = localOwner:clone("LOCAL", "VISUAL_ONLY")
check(cloned.ok and localCalls == 0, "authored visual resolution")
check(cloned.value.MeshId == authored.MeshId and cloned.value ~= authored, "authored mesh identity")
check(
	localOwner:prepare("LOCAL", "AUTHORITATIVE_MESH_COLLISION").ok and localCalls == 1,
	"authoritative imported Default hull accepted"
)
local proxy = Instance.new("Model")
proxy.Name = "ProductionProxyFixture"
proxy.Parent = kits
check(not localOwner:hasProxy({ CollisionTemplate = proxy.Name }), "empty proxy accepted")
local floor = Instance.new("Part")
floor.Parent = proxy
check(localOwner:hasProxy({ CollisionTemplate = proxy.Name }), "authored proxy not recognized")
proxy:Destroy()
cloned.value:Destroy()
localOwner:destroy()

-- Integration exercises the production loader's final collision/query/touch flags.
local loader = require(game.ReplicatedStorage.Luckbound.Util.ChunkLoader)
local integrationCalls = {}
local integrationOwner = Preparation.new(manifest, config, {
	Kits = kits,
	CreateMesh = function(id, requested)
		integrationCalls[id] = requested
		return Instance.new("MeshPart")
	end,
})
local collision = Instance.new("Model")
collision.Name = "ProductionCollisionContractFixture"
local collisionPart = Instance.new("Part")
collisionPart.Parent = collision
collision.Parent = kits
local empty = Instance.new("Model")
empty.Name = "ProductionEmptyCollisionFixture"
empty.Parent = kits
local uncloneable = collision:Clone()
uncloneable.Name = "ProductionUnavailableCollisionFixture"
uncloneable.Archivable = false
uncloneable.Parent = kits
local hasProxy = integrationOwner.hasProxy
integrationOwner.hasProxy = function(self, chunk)
	-- Simulate the authored template becoming uncloneable after validation.
	return chunk.Id == "UNAVAILABLE" or hasProxy(self, chunk)
end
local definitions = {
	PROXY = { Id = "PROXY", AssetKey = "P", CollisionTemplate = collision.Name },
	MULTIPART = {
		Id = "MULTIPART",
		AssetKey = "ASSEMBLY",
		MeshParts = {
			{
				AssetKey = "T",
				SizeX = 16,
				SizeY = 8,
				SizeZ = 16,
				OffsetX = 0,
				OffsetY = 0,
				OffsetZ = 0,
			},
			{
				AssetKey = "V",
				SizeX = 4,
				SizeY = 2,
				SizeZ = 4,
				OffsetX = 0,
				OffsetY = 8,
				OffsetZ = 0,
				CanCollide = false,
			},
		},
	},
	EMPTY = { Id = "EMPTY", AssetKey = "X", CollisionTemplate = empty.Name },
	UNAVAILABLE = { Id = "UNAVAILABLE", AssetKey = "Z", CollisionTemplate = uncloneable.Name },
}
local layout = { WorldId = "CONTRACT_FIXTURE", Seed = 1, Chunks = {} }
for index, id in { "PROXY", "MULTIPART", "EMPTY", "UNAVAILABLE" } do
	local definition = definitions[id]
	definition.WorldId, definition.Role, definition.Sockets = layout.WorldId, "PATH", {}
	definition.SizeX, definition.SizeY, definition.SizeZ = 16, 8, 16
	table.insert(
		layout.Chunks,
		{ Index = index, ChunkId = id, Role = "PATH", X = index * 32, Y = 0, Z = 0, Yaw = 0 }
	)
end
check(loader.prepare(layout, definitions, integrationOwner).ok, "integration preparation")
local holder = Instance.new("Folder")
holder.Parent = workspace
local built = loader.build(
	layout,
	definitions,
	Vector3.new(0, 40000, 0),
	holder,
	"Contract",
	integrationOwner
)
local found = {}
for _, folder in built.Model:GetChildren() do
	found[folder:GetAttribute("ChunkId")] = folder
end
local visual = found.PROXY.Mesh
check(
	not visual.CanCollide and not visual.CanQuery and not visual.CanTouch,
	"authored proxy visual semantics"
)
local collider = found.PROXY.WalkCollision:FindFirstChildWhichIsA("BasePart", true)
check(
	collider.CanCollide and collider.CanQuery and not collider.CanTouch,
	"authored collision semantics"
)
local terrain, decoration = found.MULTIPART.Mesh.T, found.MULTIPART.Mesh.V
check(terrain.CanCollide and terrain.CanQuery and terrain.CanTouch, "authoritative semantics")
check(
	not decoration.CanCollide and not decoration.CanQuery and not decoration.CanTouch,
	"multipart visual semantics"
)
check(
	integrationCalls[manifest.assetId("V")] == Enum.CollisionFidelity.Box,
	"visual-only multipart precise"
)
check(
	integrationCalls[manifest.assetId("T")] == Enum.CollisionFidelity.PreciseConvexDecomposition,
	"terrain fidelity"
)
check(
	found.EMPTY.Mesh.CanCollide
		and integrationCalls[manifest.assetId("X")]
			== Enum.CollisionFidelity.PreciseConvexDecomposition,
	"empty proxy lost authoritative fallback"
)
check(
	found.UNAVAILABLE.Mesh.CanCollide and found.UNAVAILABLE:FindFirstChild("WalkCollision") == nil,
	"proxy clone failure lost collision"
)
check(
	integrationCalls[manifest.assetId("Z")] == Enum.CollisionFidelity.PreciseConvexDecomposition,
	"proxy failure did not prepare precise fallback"
)
holder:Destroy()
collision:Destroy()
empty:Destroy()
uncloneable:Destroy()
integrationOwner:destroy()
return {
	Passed = passed,
	WorkerMaximum = maximum,
	Engine = "real Studio scheduler/instances",
	SyntheticFailures = 3,
}
