--!strict
-- API contract shim for the real ChunkLoader, run by check_chunk_loader.py.
-- Yaw transforms, parenting, model pivots and destruction are implemented here;
-- raycast results are controlled inputs, not a substitute for Studio physics.
local nativePrint = print
local print = function(...) end
local warn = function(...) end

local oldVectorIndex = __v3meta.__index
__v3meta.__index = function(v, key)
	if key == "Unit" then
		local magnitude = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
		return Vector3.new(v.X / magnitude, v.Y / magnitude, v.Z / magnitude)
	end
	return oldVectorIndex(v, key)
end
function Color3.fromHSV(h, s, v)
	local i = math.floor(h * 6)
	local f = h * 6 - i
	local p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
	local colors = { { v, t, p }, { q, v, p }, { p, v, t }, { p, q, v }, { t, p, v }, { v, p, q } }
	return Color3.new(table.unpack(colors[i % 6 + 1]))
end
local CFrame = {}
local frameMeta = {}
local function frame(position, yaw)
	return setmetatable({ Position = position, yaw = yaw }, frameMeta)
end
function CFrame.new(x, y, z)
	return frame(if typeof(x) == "Vector3" then x else Vector3.new(x, y, z), 0)
end
function CFrame.Angles(x, y, z)
	assert(x == 0 and z == 0, "this contract shim supports yaw only")
	return frame(Vector3.zero, y)
end
frameMeta.__index = function(self, key)
	if key == "LookVector" then
		return Vector3.new(-math.sin(self.yaw), 0, -math.cos(self.yaw))
	end
	return frameMeta[key]
end
function frameMeta.VectorToWorldSpace(self, v)
	local c, s = math.cos(self.yaw), math.sin(self.yaw)
	return Vector3.new(c * v.X + s * v.Z, v.Y, -s * v.X + c * v.Z)
end
function frameMeta.Inverse(self)
	local inverse = frame(Vector3.zero, -self.yaw)
	inverse.Position = inverse:VectorToWorldSpace(self.Position * -1)
	return inverse
end
frameMeta.__mul = function(a, b)
	return frame(a.Position + a:VectorToWorldSpace(b.Position), a.yaw + b.yaw)
end
local UDim2 = {
	fromScale = function(x, y)
		return { x, y }
	end,
}
local RaycastParams = {
	new = function()
		return {}
	end,
}
local objects, calls, failedId, probeHeight, upload = {}, {}, nil, nil, true
local methods = {}
local instanceMeta = {}
instanceMeta.__index = function(o, k)
	if methods[k] then
		return methods[k]
	end
	if k == "Position" then
		return o.props.CFrame.Position
	end
	return o.props[k]
end
instanceMeta.__newindex = function(o, k, v)
	if k == "Parent" then
		local previous = o.props.Parent
		if previous then
			local index = table.find(previous.children, o)
			if index then
				table.remove(previous.children, index)
			end
		end
		if v then
			table.insert(v.children, o)
		end
	end
	o.props[k] = v
end
local Instance = {}
function Instance.new(class)
	local o = setmetatable({
		props = { ClassName = class, Name = class, CFrame = CFrame.new(), Size = Vector3.one },
		children = {},
		attributes = {},
		destroyed = false,
	}, instanceMeta)
	table.insert(objects, o)
	return o
end
function methods.IsA(o, class)
	return o.ClassName == class
		or (class == "BasePart" and (o.ClassName == "MeshPart" or o.ClassName == "Part"))
end
function methods.SetAttribute(o, k, v)
	o.attributes[k] = v
end
function methods.GetAttribute(o, k)
	return o.attributes[k]
end
function methods.FindFirstChild(o, name, recursive)
	for _, child in o.children do
		if child.Name == name then
			return child
		end
		if recursive then
			local found = child:FindFirstChild(name, true)
			if found then
				return found
			end
		end
	end
	return nil
end
function methods.Destroy(o)
	for _, child in table.clone(o.children) do
		child:Destroy()
	end
	o.Parent = nil
	o.destroyed = true
end
function methods.PivotTo(o, target)
	local delta = target * o.WorldPivot:Inverse()
	local function move(root)
		for _, child in root.children do
			if child:IsA("BasePart") then
				child.CFrame = delta * child.CFrame
			end
			move(child)
		end
	end
	move(o)
	o.WorldPivot = target
end
local Workspace = Instance.new("Workspace")
function methods.Raycast(o, origin, direction, params)
	table.insert(calls, {
		origin = origin,
		direction = direction,
		filter = params.FilterDescendantsInstances[1].ClassName,
	})
	return if probeHeight then { Position = Vector3.new(origin.X, probeHeight, origin.Z) } else nil
end
local AssetService = {}
function AssetService.CreateMeshPartAsync(self, id, options)
	table.insert(calls, { asset = id, collision = options.CollisionFidelity.Name })
	if id == failedId then
		error("controlled mesh-load failure")
	end
	return Instance.new("MeshPart")
end
local ReplicatedStorage = {
	FindFirstChild = function()
		return nil
	end, -- absent prop library; no fabricated templates
	WaitForChild = function()
		return {}
	end,
}
local RunService = {
	Heartbeat = { Wait = function() end },
}
local tags = {}
local CollectionService = {
	AddTag = function(self, object, tag)
		tags[object] = tags[object] or {}
		tags[object][tag] = true
	end,
}
local game = {
	GetService = function(self, name)
		return ({
			AssetService = AssetService,
			ReplicatedStorage = ReplicatedStorage,
			RunService = RunService,
			Workspace = Workspace,
			CollectionService = CollectionService,
			ServerStorage = Instance.new("Folder"), -- empty library exercises safe collider fallback
		})[name]
	end,
}
local Manifest = __require("AssetManifest")
Manifest.assetId = function(key)
	return if upload then key else nil
end
Manifest.isUploaded = function(key)
	return upload
end

-- LOADER_FACTORIES --

local function rounded(n)
	return math.round(n * 1e6) / 1e6
end
local function encode(value)
	if typeof(value) == "Vector3" then
		return { rounded(value.X), rounded(value.Y), rounded(value.Z) }
	end
	if typeof(value) == "Color3" then
		return { rounded(value.R), rounded(value.G), rounded(value.B) }
	end
	if type(value) == "number" then
		return rounded(value)
	end
	if type(value) ~= "table" then
		return value
	end
	if value.props then
		return value.Name
	end
	local out = {}
	for k, v in value do
		out[k] = encode(v)
	end
	return out
end
local function equal(a, b)
	if type(a) ~= type(b) then
		return false
	end
	if type(a) ~= "table" then
		return a == b
	end
	for k, v in a do
		if not equal(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end
local origin = Vector3.new(103, 207, -311)
local function run(factory, chunk, yaw, testMode, mode, repeatChunk)
	objects, calls = {}, {}
	Workspace.children = {}
	upload = mode ~= "placeholder"
	failedId = if mode == "failure" then chunk.AssetKey else nil
	probeHeight = if mode == "deck" then origin.Y else nil
	local loader = factory()
	local placements =
		{ { ChunkId = chunk.Id, Role = chunk.Role, X = 32, Y = 0, Z = 48, Yaw = yaw, Index = 1 } }
	if repeatChunk then
		table.insert(placements, {
			ChunkId = chunk.Id,
			Role = chunk.Role,
			X = 640,
			Y = 16,
			Z = -512,
			Yaw = (yaw + 90) % 360,
			Index = 2,
		})
	end
	local result = loader.build({
		WorldId = chunk.WorldId,
		Seed = 17,
		TestMode = testMode,
		Atmosphere = if mode == "recolour" then "SIEGE" else nil,
		Chunks = placements,
	}, { [chunk.Id] = chunk }, origin, Workspace, "ContractStage")
	local function snapshot(o)
		local properties = {}
		for k, v in o.props do
			if k ~= "Parent" then
				properties[k] = encode(v)
			end
		end
		local children = {}
		for _, child in o.children do
			table.insert(children, snapshot(child))
		end
		return { properties = properties, attributes = encode(o.attributes), children = children }
	end
	return {
		model = snapshot(result.Model),
		entry = encode(result.EntryPosition),
		returnPosition = encode(result.ReturnPosition),
		used = result.UsedMeshes,
		floors = result.FloorCount,
		calls = encode(calls),
	},
		result
end

local compared = 0
for _, world in { "VERDANT_VALLEY", "SKY_CITADEL", "ETHEREAL_SCAPE" } do
	local count = 0
	for _, chunk in __require("Chunks") do
		if chunk.WorldId ~= world then
			continue
		end
		-- Exercise every content entry through the legacy path, including ES
		-- entries that now use multipart art. Actual assemblies are checked below.
		chunk = table.clone(chunk)
		chunk.MeshParts = nil
		chunk.Boundary = nil
		chunk.AttachedRooms = nil
		count += 1
		for yaw = 0, 270, 90 do
			for _, testMode in { false, true } do
				for _, mode in { "mesh", "placeholder", "failure", "deck", "recolour" } do
					local old = run(oldFactory, chunk, yaw, testMode, mode, true)
					local new = run(newFactory, chunk, yaw, testMode, mode, true)
					assert(
						equal(old, new),
						`{world} {chunk.Id} yaw {yaw}, test {testMode}, {mode}: legacy behavior changed`
					)
					local missing = mode == "placeholder" or mode == "failure"
					assert(new.used == (if missing then 0 else 2))
					assert(new.floors == (if missing then 2 else 0))
					compared += 1
				end
			end
		end
	end
	nativePrint(
		`PASS: {world}: {count} single-mesh chunks match the pre-multipart loader at every yaw`
	)
end
local multipart = table.clone(__require("Chunks").ES_SANCTUM)
for yaw = 0, 270, 90 do
	local _, result = run(newFactory, multipart, yaw, false, "mesh", false)
	assert(result.UsedMeshes == 1 and result.FloorCount == 0)
	local group = result.Model.children[1].children[1]
	assert(group:IsA("Model") and #group.children == #multipart.MeshParts)
	local meshFrame = CFrame.new(
		origin + Vector3.new(32, multipart.SizeY / 2 - multipart.GroundOffsetY, 48)
	) * CFrame.Angles(0, -math.rad(yaw + multipart.MeshYawOffset), 0)
	for index, part in multipart.MeshParts do
		local expected = meshFrame * CFrame.new(part.OffsetX, part.OffsetY, part.OffsetZ)
		local actual = group.children[index].CFrame
		assert(equal(encode(expected), encode(actual)), `multipart alignment changed at yaw {yaw}`)
		assert(group.children[index].Size == Vector3.new(part.SizeX, part.SizeY, part.SizeZ))
		assert(group.children[index].CanCollide == (part.CanCollide ~= false))
		if part.CanCollide == false then
			assert(
				group.children[index].CanQuery == false and group.children[index].CanTouch == false
			)
		end
	end
	for _, call in calls do
		if call.filter then
			assert(call.filter == "Model")
		end
	end
end
-- Fail the second component after the grounds have loaded: no partial model survives.
local savedCreate = AssetService.CreateMeshPartAsync
AssetService.CreateMeshPartAsync = function(self, id, options)
	if id == multipart.MeshParts[2].AssetKey then
		error("controlled second-component failure")
	end
	return savedCreate(self, id, options)
end
local _, fallback = run(newFactory, multipart, 90, false, "mesh", false)
assert(fallback.UsedMeshes == 0 and fallback.FloorCount == 1)
for _, o in objects do
	assert(o.ClassName ~= "MeshPart" or o.destroyed, "partial multipart mesh survived fallback")
end
AssetService.CreateMeshPartAsync = savedCreate
local shrine = __require("Chunks").ES_CAP_SEALED_SHRINE
for yaw = 0, 270, 90 do
	local _, result = run(newFactory, shrine, yaw, false, "mesh", true)
	assert(#result.Model.children == 4, "two shrines must own two separate dependent rooms")
	for _, folder in result.Model.children do
		local portals = 0
		for _, child in folder.children do
			if child.Name == "RoomPortalTrigger" then
				portals += 1
				assert(
					child.CanCollide == false and child.CanTouch == true and child.Transparency == 1
				)
				local centre = folder:GetAttribute("Centre")
				local frame = CFrame.new(centre)
					* CFrame.Angles(0, -math.rad(folder:GetAttribute("Yaw")), 0)
				local localZ = if folder:GetAttribute("ParentChunkIndex") then 105 else 24
				assert(
					equal(encode(child.CFrame), encode(frame * CFrame.new(0, 12, localZ))),
					"portal yaw must match actual geometry"
				)
				assert(child:GetAttribute("Arrival") ~= nil)
			elseif child.Name == "SafetyBoundaries" then
				assert(tags[child][__require("Constants").NAMES.CHUNK_BOUNDARY_TAG])
				for _, wall in child.children do
					assert(
						wall.CanCollide
							and wall.Transparency == 1
							and not wall.CanTouch
							and wall.Size.Y >= 64
					)
				end
			end
		end
		assert(portals == 1, "each source and destination must have one trigger")
	end
end
nativePrint(
	"PASS: conditional room pairs and rotated portal positions at four yaws; tagged 64-stud boundaries"
)
nativePrint(
	`PASS: {compared} legacy differential cases; multipart alignment at four yaws; atomic component failure`
)
