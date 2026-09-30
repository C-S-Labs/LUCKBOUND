--!strict
-- Temporary saved-collision approach probes at four yaws; destroys all clones.
-- Defaults to Refuge -> Shaded Grove. Optional VV_PAIR_IDS / VV_PAIR_KIND
-- select other measured paths; VV_PAIR_CHUNKS injects fresh disk metadata.
local root = game:GetService("ReplicatedStorage").Luckbound
local core = require(root.Util.ChunkCore)
local chunks = VV_PAIR_CHUNKS or require(root.Content.Chunks.VerdantValley)
local byId = {}
for _, chunk in chunks do
	byId[chunk.Id] = chunk
end
local ids = VV_PAIR_IDS or { "VV_ENTRY_WOODLAND_REFUGE", "VV_SHADED_GROVE" }
local refuge = byId[ids[1]]
local grove = byId[ids[2]]
local departure = refuge.Sockets[1]
for _, socket in refuge.Sockets do
	if socket.Kind == VV_PAIR_KIND or socket.Id == VV_PAIR_SOCKET then
		departure = socket
		break
	end
end
local kits = game:GetService("ServerStorage").LuckboundChunkKits
local holder = Instance.new("Folder")
holder.Name = "VV_PairProbe_Disposable"
holder.Parent = workspace
local base = Vector3.new(0, 10000, 0)
local function run()
	local report = {}
	for _, yaw in { 0, 90, 180, 270 } do
		local start = { X = 0, Y = 0, Z = 0, Yaw = yaw }
		local mouth = core.worldSocket(start, refuge, departure)
		local placed, arrival = core.placeAgainst(grove, mouth, 2)
		assert(placed and arrival)
		local neighbourSocket = core.worldSocket(placed, grove, arrival)
		assert(
			mouth.X == neighbourSocket.X
				and mouth.Z == neighbourSocket.Z
				and mouth.Y == neighbourSocket.Y
		)
		local models = {}
		for _, item in { { chunk = refuge, placed = start }, { chunk = grove, placed = placed } } do
			local model = kits:FindFirstChild(item.chunk.CollisionTemplate, true):Clone()
			model:PivotTo(
				CFrame.new(base + Vector3.new(item.placed.X, item.placed.Y, item.placed.Z))
					* CFrame.Angles(
						0,
						core.yawRadians(item.placed.Yaw + item.chunk.MeshYawOffset),
						0
					)
			)
			for _, part in model:GetDescendants() do
				if part:IsA("BasePart") then
					part.CanQuery = true
					part.CanCollide = true
					part.Anchored = true
				end
			end
			model.Parent = holder
			table.insert(models, model)
		end
		game:GetService("RunService").Heartbeat:Wait()
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		params.FilterDescendantsInstances = models
		local outward = CFrame.Angles(0, core.yawRadians(mouth.Facing), 0).LookVector
		local across = Vector3.new(-outward.Z, 0, outward.X)
		local lateralExtent = math.min(departure.Width, arrival.Width) / 2 - 8
		local row = {
			firstChunk = refuge.Id,
			secondChunk = grove.Id,
			departure = departure.Id,
			kind = departure.Kind,
			yaw = yaw,
			neighbourYaw = placed.Yaw,
			samples = {},
			passed = 0,
			total = 0,
		}
		for _, distance in { -40, -24, -12, -6, -2, 0, 2, 6, 12, 24, 40 } do
			for _, lateral in { -lateralExtent, -8, 0, 8, lateralExtent } do
				local point = base
					+ Vector3.new(mouth.X, mouth.Y, mouth.Z)
					+ outward * distance
					+ across * lateral
				local hit =
					workspace:Raycast(point + Vector3.new(0, 20, 0), Vector3.new(0, -40, 0), params)
				local ok = hit ~= nil
					and math.abs(hit.Position.Y - point.Y) <= 6
					and hit.Normal.Y >= 0.65
				row.total += 1
				if ok then
					row.passed += 1
				end
				table.insert(row.samples, {
					distance = distance,
					lateral = lateral,
					pass = ok,
					height = hit and hit.Position.Y - base.Y or false,
					normal = hit and hit.Normal.Y or false,
					part = hit and hit.Instance.Name or false,
				})
			end
		end
		table.insert(report, row)
		for _, model in models do
			model:Destroy()
		end
	end
	return report
end
local ok, result = pcall(run)
holder:Destroy()
if not ok then
	error(result)
end
return game:GetService("HttpService"):JSONEncode(result)
