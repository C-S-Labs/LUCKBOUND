--!strict
-- Real-engine differential sampling. Complements, never replaces, a player walk.
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local Root = script.Parent.Parent
local Runtime = require(Root.Core.ChunkRuntimeCore)
local ChunkCore = require(Root.Util.ChunkCore)
local Check = {}

function Check.sample(built: any, layout: any, profile: any)
	local entryParams = RaycastParams.new()
	entryParams.FilterType = Enum.RaycastFilterType.Include
	entryParams.FilterDescendantsInstances = { built.Model }
	entryParams.RespectCanCollide = true
	local entryOrigin = built.EntryPosition + Vector3.new(0, 32, 0)
	local initial = Workspace:Raycast(entryOrigin, Vector3.new(0, -1024, 0), entryParams)
	profile.EntrySupportBeforeHeartbeat = if initial then initial.Position.Y else false
	local started = os.clock()
	RunService.Heartbeat:Wait()
	profile.PhysicsObservationDelaySeconds = os.clock() - started
	local settled = Workspace:Raycast(entryOrigin, Vector3.new(0, -1024, 0), entryParams)
	profile.EntrySupportAfterHeartbeat = if settled then settled.Position.Y else false
	local _, definitions = Runtime.expand(layout, require(Root.Content.Chunks))
	local samples = {}
	for _, folder in built.Model:GetChildren() do
		local id = folder:GetAttribute("ChunkId")
		local chunk = id and definitions[id]
		if not chunk then
			continue
		end
		local centre = folder:GetAttribute("Centre")
		local frame = CFrame.new(centre)
			* CFrame.Angles(0, ChunkCore.yawRadians(folder:GetAttribute("Yaw")), 0)
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		params.FilterDescendantsInstances = { folder }
		params.RespectCanCollide = true
		local row = {}
		local function cast(x: number, z: number)
			local origin = frame:PointToWorldSpace(Vector3.new(x, chunk.SizeY + 32, z))
			local hit = Workspace:Raycast(origin, Vector3.new(0, -chunk.SizeY - 512, 0), params)
			table.insert(
				row,
				if hit then math.round((hit.Position.Y - centre.Y) * 1000) / 1000 else false
			)
			local body = Workspace:Blockcast(
				CFrame.new(origin),
				Vector3.new(2, 4, 2),
				Vector3.new(0, -chunk.SizeY - 512, 0),
				params
			)
			table.insert(
				row,
				if body then math.round((body.Position.Y - centre.Y) * 1000) / 1000 else false
			)
		end
		for x = -4, 4 do
			for z = -4, 4 do
				cast(chunk.SizeX * x / 10, chunk.SizeZ * z / 10)
			end
		end
		for _, socket in chunk.Sockets or {} do
			cast(socket.OffsetX, socket.OffsetZ)
			cast(socket.OffsetX * 0.96, socket.OffsetZ * 0.96)
		end
		if profile.CollisionDense then
			for x = -10, 10 do
				for z = -64, 64 do
					cast(x * 2, z * 2)
				end
			end
			for z = -100, 100, 25 do
				for _, height in { 2, 5 } do
					local origin = frame:PointToWorldSpace(Vector3.new(-128, height, z))
					local direction = frame:VectorToWorldSpace(Vector3.new(256, 0, 0))
					local hit = Workspace:Raycast(origin, direction, params)
					table.insert(row, if hit then math.round(hit.Distance * 1000) / 1000 else false)
				end
			end
		end
		samples[tostring(folder:GetAttribute("Index")) .. ":" .. id] = row
	end
	profile.CollisionSamples = samples
end

return Check
