--!strict
-- Studio-only fixed-layout adapter. Uses production AssetPreparation + ChunkLoader.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
	return
end
local RS = game:GetService("ReplicatedStorage")
local SS = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local AssetService = game:GetService("AssetService")
local data: any = require(RS.EmberfallWalkthroughData)
local scenery: any = require(RS.EmberfallSceneryData)
local Root = RS:WaitForChild("Luckbound")
local Preparation = require(Root.Util.AssetPreparation)
local Loader = require(Root.Util.ChunkLoader)
local origin = Vector3.new(20000, 1000, 0)
workspace:SetAttribute("EmberfallWalkthroughStatus", "Loading exact authored assets")
local kits = SS:FindFirstChild("LuckboundChunkKits")
assert(kits, "Real chunk-kit storage missing")
local templates = Instance.new("Folder")
templates.Name = "EmberfallWalkthroughTemplates"
templates.Parent = kits
local byKey = {}
for _, record in data.assets do
	byKey[record.key] = record
end
local failures = {}
local queue = {}
for _, record in data.assets do
	if record.role == "collision" then
		table.insert(queue, record)
	end
end
for _, chunk in data.kit do
	local model = Instance.new("Model")
	model.Name = chunk.CollisionTemplate
	model.WorldPivot = CFrame.identity
	model.Parent = templates
end
local cursor, completed, workers = 0, 0, 6
for _ = 1, workers do
	task.spawn(function()
		while cursor < #queue do
			cursor += 1
			local record = queue[cursor]
			local ok, err = pcall(function()
				assert(data.ids[record.key], "Missing mesh ID: " .. record.key)
				local p = AssetService:CreateMeshPartAsync(
					data.ids[record.key],
					{ CollisionFidelity = Enum.CollisionFidelity[record.fidelity] }
				)
				p.Name = record.key
				p.Size = Vector3.new(unpack(record.size))
				p.CFrame = CFrame.new(unpack(record.center))
				p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, true, true, false
				p.Transparency = 1
				p.Parent = templates[data.kit[record.chunk].CollisionTemplate]
			end)
			if not ok then
				table.insert(failures, tostring(err))
			end
			completed += 1
		end
	end)
end
while completed < #queue do
	workspace:SetAttribute(
		"EmberfallWalkthroughStatus",
		string.format("Preparing exact collision %d/%d", completed, #queue)
	)
	task.wait(0.5)
end
assert(#failures == 0, table.concat(failures, "\n"))
local manifest = {
	assetId = function(key: string)
		return data.ids[key]
	end,
}
local assets = Preparation.new(
	manifest,
	{ AssetPreparationWorkers = workers, AssetPreparationDiagnostics = true },
	{ Kits = templates }
)
for _, record in data.assets do
	if record.role ~= "collision" and record.role ~= "scenery" then
		local r = assets:prepare(record.key, "VISUAL_ONLY")
		assert(r.ok, r.err)
	end
end
local layout: any = { WorldId = "EMBERFALL", Seed = 1, TestMode = true, Chunks = {} }
for i, row in data.rows do
	table.insert(layout.Chunks, {
		Index = i,
		ChunkId = row.id,
		Role = data.kit[row.id].Role,
		X = row.x,
		Y = row.y,
		Z = row.z,
		Yaw = row.yaw,
	})
end
-- The frozen source boundaries enclose individual pieces. Only the assembled
-- footprint's exposed edges are safety barriers in this fixed walkthrough.
local walkthroughKit = table.clone(data.kit)
local removedInteriorBoundaries = 0
local retainedOuterBoundaries = 0
for _, row in data.rows do
	local definition = table.clone(data.kit[row.id])
	local boundary = table.clone(definition.Boundary)
	boundary.Segments = {}
	local frame = CFrame.new(row.x, row.y, row.z) * CFrame.Angles(0, -math.rad(row.yaw), 0)
	for _, segment in definition.Boundary.Segments do
		local a, b = segment.A, segment.B
		local midpoint = Vector3.new((a[1] + b[1]) / 2, 0, (a[3] + b[3]) / 2)
		local normal = if math.abs(midpoint.X) > math.abs(midpoint.Z)
			then Vector3.new(math.sign(midpoint.X), 0, 0)
			else Vector3.new(0, 0, math.sign(midpoint.Z))
		local outside = frame:PointToWorldSpace(midpoint + normal * boundary.Thickness)
		local interior = false
		for _, neighbor in data.rows do
			if neighbor ~= row then
				local other = data.kit[neighbor.id]
				if
					math.abs(outside.X - neighbor.x) < other.SizeX / 2
					and math.abs(outside.Z - neighbor.z) < other.SizeZ / 2
				then
					interior = true
					break
				end
			end
		end
		if interior then
			removedInteriorBoundaries += 1
		else
			table.insert(boundary.Segments, segment)
			retainedOuterBoundaries += 1
		end
	end
	definition.Boundary = boundary
	walkthroughKit[row.id] = definition
end

local stages = workspace:FindFirstChild(Loader.STAGE_NAME) or Instance.new("Folder")
stages.Name = Loader.STAGE_NAME
stages.Parent = workspace
local loaded =
	Loader.build(layout, walkthroughKit, origin, stages, "EmberfallOwnerWalkthrough", assets)
assert(
	loaded.FloorCount == 0 and loaded.UsedMeshes == 9,
	"Missing exact terrain; refusing a blockout walkthrough"
)
local world = loaded.Model
world:SetAttribute("Origin", origin)
world:SetAttribute("Layout", data.layout)
world:SetAttribute("RemovedInteriorBoundaries", removedInteriorBoundaries)
world:SetAttribute("OuterBoundaryParts", retainedOuterBoundaries)
local folders = {}
for _, f in world:GetChildren() do
	local id = f:GetAttribute("ChunkId")
	if id then
		folders[id] = f
	end
end
for _, row in data.rows do
	local f = folders[row.id]
	local visual = f:FindFirstChild("Mesh")
	assert(visual and not visual.CanCollide and f.WalkCollision, "Authored collision proxy missing")
	visual.Color = Color3.new(1, 1, 1)
	visual:SetAttribute("BurnRole", "terrain")
	visual:SetAttribute("MeshAsset", data.ids[data.kit[row.id].AssetKey])
end
for _, marker in world:GetDescendants() do
	if marker:IsA("BasePart") and marker.Name:match("^Socket_") then
		marker.Transparency = 1
		marker.CanQuery, marker.CanTouch = false, false
	end
end
local extras = Instance.new("Folder")
extras.Name = "AssemblyPresentation"
extras.Parent = world
for _, record in data.assets do
	if record.role ~= "collision" and record.role ~= "terrain" and record.role ~= "scenery" then
		local result = assets:clone(record.key, "VISUAL_ONLY")
		assert(result.ok, result.err)
		local p = result.value
		p.Name = record.key
		p.Size = Vector3.new(unpack(record.size))
		p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
		p.Color = Color3.new(1, 1, 1)
		if record.role == "road" then
			p.Color = Color3.new(0.461356, 0.381092, 0.2717)
		end
		if record.role == "fire" then
			p.Color = Color3.new(0.906332, 0.537099, 0.151704)
		end
		if record.role == "grass" then
			local row
			for _, r in data.rows do
				if r.id == record.chunk then
					row = r
					break
				end
			end
			assert(row, "Walkthrough terrain has no layout row")
			p.CFrame = CFrame.new(origin + Vector3.new(row.x, row.y, row.z))
				* CFrame.Angles(0, -math.rad(row.yaw), 0)
				* CFrame.new(unpack(record.center))
			p.DoubleSided = true
			p:SetAttribute("BurnRole", "grass")
			p:SetAttribute("MeshAsset", data.ids[record.key])
		else
			p.CFrame = CFrame.new(origin + Vector3.new(unpack(record.center)))
			p:SetAttribute("AssemblyDerived", true)
			p:SetAttribute("NonPlayable", record.role == "scenery")
			if record.role == "smoke" then
				p.Transparency = 0.65
			end
			if record.role == "fire" then
				p.Material = Enum.Material.Neon
			end
		end
		p.Parent = extras
	end
end
-- Ordinary assembled scenery assets retain no client editable memory. Preparation
-- and immutable templates use the same production cache as the playable visuals.
local sceneryStart = os.clock()
local sceneryAssets = Preparation.new({
	assetId = function(key: string)
		return scenery.ids[key]
	end,
}, { AssetPreparationWorkers = workers, AssetPreparationDiagnostics = true })
for _, record in scenery.records do
	local result = sceneryAssets:clone(record.key, "VISUAL_ONLY")
	assert(result.ok, result.err)
	local p = result.value
	p.Name = record.key
	p.Size = Vector3.new(unpack(record.size))
	p.CFrame = CFrame.new(origin + Vector3.new(unpack(record.center)))
	p.Anchored = true
	p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
	p.DoubleSided = true
	p.Color = Color3.new(1, 1, 1)
	p:SetAttribute("NonPlayable", true)
	p:SetAttribute("SceneryRole", record.role)
	p:SetAttribute("Triangles", record.triangles)
	p.Parent = extras
end
world:SetAttribute("SceneryLoadSeconds", os.clock() - sceneryStart)
world:SetAttribute("SceneryMeshParts", #scenery.records)
world:SetAttribute("SceneryEditableMeshes", 0)
world:SetAttribute("SceneryRecolourSeconds", 0)
-- Roblox FBX import reverses local X/Z. Normalize each mesh about its own
-- bounding-box centre; authored centres, sockets and source geometry stay intact.
for _, mesh in world:GetDescendants() do
	if mesh:IsA("MeshPart") then
		mesh.CFrame *= CFrame.Angles(0, math.rad(data.importYaw), 0)
	end
end
world.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
world:SetAttribute("CollisionParts", #queue)
world:SetAttribute("TerrainReady", true)
workspace:SetAttribute("EmberfallWalkthroughStatus", "Preparing client burn appearance")
local spawnPosition = origin + Vector3.new(unpack(data.spawn))
local function spawnCharacter(character: Model)
	local root = character:WaitForChild("HumanoidRootPart", 30)
	if not root then
		return
	end
	task.wait(1)
	local params = RaycastParams.new()
	params.RespectCanCollide = true
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { world }
	local hit =
		workspace:Raycast(spawnPosition + Vector3.new(0, 100, 0), Vector3.new(0, -200, 0), params)
	assert(
		hit and hit.Instance:FindFirstAncestor("WalkCollision"),
		"Entry has no authored traversal collision"
	)
	character:PivotTo(
		CFrame.new(
			hit.Position + Vector3.new(0, 4, 0),
			origin + Vector3.new(unpack(data.route[25], 1, 3)) + Vector3.new(0, 4, 0)
		)
	)
	local player = Players:GetPlayerFromCharacter(character)
	if player then
		player:SetAttribute("EmberfallWalkthrough", true)
	end
end
local function join(player: Player)
	player.CharacterAdded:Connect(spawnCharacter)
	if player.Character then
		task.spawn(spawnCharacter, player.Character)
	end
end
Players.PlayerAdded:Connect(join)
for _, p in Players:GetPlayers() do
	join(p)
end
print(
	"[EmberfallWalkthrough] Layout1: nine exact terrains, 627 authored colliders; no fallback floors"
)
