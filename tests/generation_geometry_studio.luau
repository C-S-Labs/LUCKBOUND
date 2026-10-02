--!strict
-- Real-engine differential sampling. Complements, never replaces, a player walk.
local Workspace = game:GetService("Workspace")
local Root = game.ReplicatedStorage.Luckbound
local Runtime = require(Root.Core.ChunkRuntimeCore)
local ChunkCore = require(Root.Util.ChunkCore)
local Check = {}

function Check.sample(stage: Model, layout: any, chunks: any, _floorY: number): any
	local built = { Model = stage }
	local _, definitions = Runtime.expand(layout, chunks)
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

		samples[tostring(folder:GetAttribute("Index")) .. ":" .. id] = row
	end

	local visual, yaws = {}, {}
	for _, folder in stage:GetChildren() do
		local id = folder:GetAttribute("ChunkId")
		if id then
			yaws[id] = folder:GetAttribute("ArtYawOffset")
			for _, part in folder:GetDescendants() do
				if part:IsA("MeshPart") and part.Transparency < 1 then
					visual[id .. ":" .. part.Name] = {
						MeshId = part.MeshId,
						TextureID = part.TextureID,
						Material = part.Material.Name,
						Color = { part.Color.R, part.Color.G, part.Color.B },
						Size = { part.Size.X, part.Size.Y, part.Size.Z },
					}
				end
			end
		end
	end
	return { CollisionSamples = samples, VisualSignatures = visual, ArtYaws = yaws }
end

return Check
