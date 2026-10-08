--!strict
-- NON-PRODUCTION cost fixture; repeated accepted layouts, not canonical world design.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
	return
end
local HttpService = game:GetService("HttpService")
local benchmarkStart = os.clock()
local startedAt = workspace:GetServerTimeNow()
local groups = workspace:GetAttribute("EmberfallBenchmarkGroups") or 1
local parallelPreparation = workspace:GetAttribute("EmberfallBenchmarkParallel") == true
local timings = {}
local stageStart = os.clock()
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
	task.wait()
end
assert(#failures == 0, table.concat(failures, "\n"))
timings.collisionAcquisition = os.clock() - stageStart
stageStart = os.clock()
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
local visualRequests = {}
for _, record in data.assets do
	if record.role ~= "collision" and record.role ~= "scenery" then
		table.insert(visualRequests, { Key = record.key, Role = "VISUAL_ONLY" })
	end
end
if parallelPreparation then
	local result = assets:prepareMany(visualRequests)
	assert(result.ok, result.err)
else
	for _, request in visualRequests do
		local result = assets:prepare(request.Key, request.Role)
		assert(result.ok, result.err)
	end
end
timings.playablePreparation = os.clock() - stageStart
stageStart = os.clock()
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
	Loader.build(layout, walkthroughKit, origin, stages, "EmberfallScaleBenchmark", assets)
assert(
	loaded.FloorCount == 0 and loaded.UsedMeshes == 9,
	"Missing exact terrain; refusing a blockout walkthrough"
)
timings.firstChunkAssembly = os.clock() - stageStart
stageStart = os.clock()
local world = loaded.Model
world:SetAttribute("BenchmarkStartedAt", startedAt)
world:SetAttribute("NON_PRODUCTION", true)
world:SetAttribute("Groups", groups)
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
timings.playablePresentation = os.clock() - stageStart
local sceneryStart = os.clock()
local sceneryAssets = Preparation.new({
	assetId = function(key: string)
		return scenery.ids[key]
	end,
}, { AssetPreparationWorkers = workers, AssetPreparationDiagnostics = true })
local requests = {}
for _, record in scenery.records do
	table.insert(requests, { Key = record.key, Role = "VISUAL_ONLY" })
end
local preparationStart = os.clock()
if parallelPreparation then
	local result = sceneryAssets:prepareMany(requests)
	assert(result.ok, result.err)
end
timings.sceneryPreparation = os.clock() - preparationStart
local sceneryPlacementStart = os.clock()
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
timings.sceneryClonePlacement = os.clock() - sceneryPlacementStart
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
timings.firstSceneryTotal = os.clock() - sceneryStart
local uniqueBank = workspace:GetAttribute("EmberfallBenchmarkUniqueBank") == true
local uniqueAssets
local uniqueStart = os.clock()
if uniqueBank then
	local ids = require(RS.EmberfallBenchmarkUniqueScenery)
	uniqueAssets = Preparation.new({
		assetId = function(key)
			return ids[key]
		end,
	}, { AssetPreparationWorkers = workers, AssetPreparationDiagnostics = true })
	local result = uniqueAssets:prepareMany(requests)
	assert(result.ok, result.err)
end
timings.uniqueSceneryPreparation = os.clock() - uniqueStart
local extensionStart = os.clock()
local proxyParts = 0
for group = 2, groups do
	local offset = Vector3.new(((group - 1) % 2) * 2048, 0, math.floor((group - 1) / 2) * 2048)
	local extension = Loader.build(
		layout,
		walkthroughKit,
		origin + offset,
		world,
		"NON_PRODUCTION_Replica_" .. group,
		assets
	)
	assert(
		extension.FloorCount == 0 and extension.UsedMeshes == 9,
		"Proxy block lost authored terrain"
	)
	for _, mesh in extension.Model:GetDescendants() do
		if mesh:IsA("MeshPart") then
			mesh.CFrame *= CFrame.Angles(0, math.rad(data.importYaw), 0)
			mesh.Color = Color3.new(1, 1, 1)
		elseif mesh:IsA("BasePart") and mesh.Name:match("^Socket_") then
			mesh.Transparency = 1
			mesh.CanQuery = false
		end
	end
	local dressing = extras:Clone()
	dressing.Name = "NON_PRODUCTION_ReplicaPresentation_" .. group
	for _, mesh in dressing:GetDescendants() do
		if mesh:IsA("BasePart") then
			mesh.CFrame += offset
			if
				uniqueAssets
				and group > math.ceil(groups / 2)
				and mesh:GetAttribute("SceneryRole")
			then
				local result = uniqueAssets:clone(mesh.Name, "VISUAL_ONLY")
				assert(result.ok, result.err)
				local replacement = result.value
				replacement.Name = mesh.Name
				replacement.Size = mesh.Size
				replacement.CFrame = mesh.CFrame
				replacement.Anchored = true
				replacement.CanCollide = false
				replacement.CanQuery = false
				replacement.CanTouch = false
				replacement.DoubleSided = true
				replacement.Color = Color3.new(1, 1, 1)
				replacement:SetAttribute("SceneryRole", mesh:GetAttribute("SceneryRole"))
				replacement:SetAttribute("Triangles", mesh:GetAttribute("Triangles"))
				replacement.Parent = dressing
				mesh:Destroy()
			end
		end
	end
	dressing.Parent = extension.Model
	-- Later-half conservative object/physics uplift: actual accepted mesh shapes,
	-- additional independent visual objects and authored collision clones.
	if group > math.ceil(groups / 2) then
		local propSources = {}
		for _, record in data.assets do
			if record.role == "props" then
				table.insert(propSources, record)
			end
		end
		assert(#propSources > 0, "No real props available for structural cost proxy")
		local uplift = Instance.new("Folder")
		uplift.Name = "NON_PRODUCTION_StructuralDensity"
		uplift.Parent = extension.Model
		for _, row in data.rows do
			for i = 1, 20 do
				local record = propSources[if i <= 2 then i else #propSources]
				local result = assets:clone(record.key, "VISUAL_ONLY")
				assert(result.ok, result.err)
				local mesh = result.value
				mesh.Size = Vector3.new(unpack(record.size)) * 0.12
				mesh.CFrame = CFrame.new(
					origin
						+ offset
						+ Vector3.new(
							row.x + (i % 5 - 2) * 32,
							row.y + 8,
							row.z + (math.floor(i / 5) - 2) * 32
						)
				) * CFrame.Angles(0, math.rad(data.importYaw), 0)
				mesh.Anchored = true
				mesh.CanCollide = false
				mesh.CanQuery = false
				mesh.CanTouch = false
				mesh:SetAttribute("ProxyTriangles", record.triangles)
				mesh.Parent = uplift
				local collision = templates[data.kit[row.id].CollisionTemplate]
					:FindFirstChildWhichIsA("MeshPart")
					:Clone()
				collision.CFrame = mesh.CFrame
				collision.Parent = uplift
				proxyParts += 2
			end
		end
	end
end
timings.replicaAndStructuralAssembly = os.clock() - extensionStart
world.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
world:SetAttribute("CollisionParts", #queue)
world:SetAttribute("TerrainReady", true)
local counts =
	{ instances = 0, meshParts = 0, collisionMeshParts = 0, baseParts = 0, proxyParts = proxyParts }
for _, object in world:GetDescendants() do
	counts.instances += 1
	if object:IsA("BasePart") then
		counts.baseParts += 1
	end
	if object:IsA("MeshPart") then
		counts.meshParts += 1
		if object.CanCollide then
			counts.collisionMeshParts += 1
		end
	end
end
local visualTriangles, collisionTriangles = 0, 0
for _, record in data.assets do
	if record.role == "collision" then
		collisionTriangles += (record.triangles or 0) * groups
	elseif record.role ~= "scenery" then
		visualTriangles += (record.triangles or 0) * groups
	end
end
for _, record in scenery.records do
	visualTriangles += record.triangles * groups
end
for _, object in world:GetDescendants() do
	visualTriangles += (object:GetAttribute("ProxyTriangles") or 0)
end
counts.visualTriangles = visualTriangles
counts.authoredCollisionTriangles = collisionTriangles
counts.safetySegments = retainedOuterBoundaries * groups
counts.sceneryMeshParts = #scenery.records * groups
counts.sceneryGrassTriangles = 175263 * groups
timings.serverReady = os.clock() - benchmarkStart
local report = {
	groups = groups,
	chunks = groups * 9,
	parallelPreparation = parallelPreparation,
	timings = timings,
	counts = counts,
	playablePreparation = assets:stats(),
	sceneryPreparation = sceneryAssets:stats(),
	streamingEnabled = workspace.StreamingEnabled,

	persistent = true,
	editableMeshes = 0,
	uniqueCollisionAssets = #queue,
	uniqueBank = uniqueBank,
	uniquePreparation = if uniqueAssets then uniqueAssets:stats() else nil,
	uniqueVisualAssets = #visualRequests + #scenery.records,
}
world:SetAttribute("ServerReport", HttpService:JSONEncode(report))
world:SetAttribute("ExpectedMeshParts", counts.meshParts)
world:SetAttribute("ServerReady", true)
print("[EmberfallBenchmarkServer] " .. HttpService:JSONEncode(report))
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
		world:SetAttribute("PlayerReadyAt", workspace:GetServerTimeNow())
		world:SetAttribute("PlayerReadySeconds", os.clock() - benchmarkStart)
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
