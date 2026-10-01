--!strict
-- Read-only production socket audit. Execute in Studio Server with optional
-- VV_AUDIT_CHUNKS override (fresh disk content) and VV_AUDIT_FIRST/LAST batch.
-- Disposable probes are isolated from gameplay and destroyed even on failure.
local root = game:GetService("ReplicatedStorage").Luckbound
local chunks = VV_AUDIT_CHUNKS or require(root.Content.Chunks.VerdantValley)
local props = require(root.Content.Props.VerdantValley)
local manifest = require(root.Content.AssetManifest)
local kits = game:GetService("ServerStorage").LuckboundChunkKits
local library = game:GetService("ReplicatedStorage").LuckboundProps
local workspace = game:GetService("Workspace")
local heartbeat = game:GetService("RunService").Heartbeat
local cfg = require(root.Core.GameConfig).Expedition.SocketProbe
local container = Instance.new("Folder")
container.Name = "VV_SocketAudit_Disposable"
container.Parent = workspace
local base = Vector3.new(0, 10000, 0)
local function rotation(yaw)
	return CFrame.Angles(0, -math.rad(yaw), 0)
end
local function query(instances)
	local p = RaycastParams.new()
	p.FilterType = Enum.RaycastFilterType.Include
	p.FilterDescendantsInstances = instances
	return p
end
local function probe(point, params, tolerance)
	local h =
		workspace:Raycast(base + point + Vector3.new(0, 80, 0), Vector3.new(0, -160, 0), params)
	if not h then
		return { hit = false, walk = false }
	end
	return {
		hit = true,
		walk = math.abs(h.Position.Y - base.Y - point.Y) <= tolerance and h.Normal.Y >= 0.65,
		y = h.Position.Y - base.Y,
		normal = h.Normal.Y,
		part = h.Instance.Name,
	}
end
local function run()
	local report = {
		chunks = {},
		inset = { 0, 2, 6, 12, 24, 40 },
		edgeMargin = cfg.EdgeMargin,
		limitations = {
			"Raycasts measure serialized query hulls; they do not establish visible triangles or character traversal.",
			"Solid prop queries inspect saved hulls; nonsolid/Sway are counted and retained.",
		},
	}
	for index = VV_AUDIT_FIRST or 1, VV_AUDIT_LAST or #chunks do
		local c = chunks[index]
		local hint = c.MeshYawOffset or 0
		local tolerance = c.SocketProbeTolerance or cfg.Tolerance
		local sourceName = "chunk_" .. string.lower(string.sub(c.Id, 4))
		if c.Id == "VV_CAP_TREASURE_HOLLOW" then
			sourceName = "chunk_side_treasure_hollow"
		end
		if c.Id == "VV_CAP_WARDENS_CLEARING" then
			sourceName = "chunk_side_wardens_clearing"
		end
		local source = kits:FindFirstChild(sourceName, true)
		assert(source and source:IsA("MeshPart"), c.Id .. " missing structure")
		assert(
			source.MeshId == manifest.assetId(c.AssetKey),
			c.Id .. " structure/manifest ID mismatch"
		)
		-- Runtime uses a freshly cooked precise hull, not the saved default hull.
		local terrain = game:GetService("AssetService"):CreateMeshPartAsync(source.MeshId, {
			CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
		})
		terrain.Name = source.Name
		terrain.Size = Vector3.new(c.SizeX, c.SizeY, c.SizeZ)
		terrain.Anchored = true
		terrain.CanCollide = false
		terrain.CanQuery = true
		terrain.Parent = container
		local tp = query({ terrain })
		local row = {
			id = c.Id,
			role = c.Role,
			meshId = source.MeshId,
			hint = hint,
			tolerance = tolerance,
			size = { c.SizeX, c.SizeY, c.SizeZ },
			template = c.CollisionTemplate,
			calibration = {},
			sockets = {},
			cardinal = {},
			props = { total = 0, solid = 0, sway = 0, nonsolid = 0 },
		}
		local bestScore = -math.huge
		local selected = hint
		local function setTerrain(yaw)
			terrain.CFrame = CFrame.new(base + Vector3.new(0, c.SizeY / 2 - c.GroundOffsetY, 0))
				* rotation(yaw)
			heartbeat:Wait()
		end
		for turn = 0, 3 do
			local yaw = (hint + turn * 90) % 360
			setTerrain(yaw)
			local score, centres = 0, 0
			local used = {}
			for _, s in c.Sockets do
				used[s.Facing] = true
				local mouth = Vector3.new(s.OffsetX, s.OffsetY, s.OffsetZ)
				local inward = Vector3.new(-s.OffsetX, 0, -s.OffsetZ).Unit
				local p = mouth + inward * cfg.Inset
				-- Match calibrateYaw: height tolerance only, no slope gate.
				local function deck(point)
					local hit = workspace:Raycast(
						base + point + Vector3.new(0, cfg.Height, 0),
						Vector3.new(0, -cfg.Height * 2, 0),
						tp
					)
					return hit and math.abs(hit.Position.Y - base.Y - mouth.Y) <= tolerance
				end
				if deck(p) then
					centres += 1
					score += 1
					local lateral = Vector3.new(-inward.Z, 0, inward.X)
						* (s.Width / 2 - cfg.EdgeMargin)
					if deck(p + lateral) and deck(p - lateral) then
						score += 10
					end
				end
			end
			for facing = 0, 270, 90 do
				if not used[facing] then
					local p = rotation(facing).LookVector * (c.SizeX / 2 - cfg.Inset)
					local h = workspace:Raycast(
						base + p + Vector3.new(0, cfg.Height, 0),
						Vector3.new(0, -cfg.Height * 2, 0),
						tp
					)
					if h and math.abs(h.Position.Y - base.Y) <= tolerance then
						score -= 5
					end
				end
			end
			table.insert(row.calibration, { offset = yaw, score = score, centreHits = centres })
			if score > bestScore then
				bestScore = score
				selected = yaw
			end
		end
		row.selected = selected
		setTerrain(selected)
		local template = kits:FindFirstChild(c.CollisionTemplate, true)
		assert(template and template:IsA("Model"), c.Id .. " missing collision")
		local collision = template:Clone()
		collision:PivotTo(CFrame.new(base) * rotation(selected))
		collision.Parent = container
		local count = 0
		for _, p in collision:GetDescendants() do
			if p:IsA("BasePart") then
				p.Anchored = true
				p.CanQuery = true
				p.CanCollide = true
				count += 1
			end
		end
		row.collisionParts = count
		local cp = query({ collision })
		local solid = Instance.new("Folder")
		solid.Parent = container
		for _, p in props.Placements[c.Id] do
			row.props.total += 1
			if p.Anim == "Sway" then
				row.props.sway += 1
			end
			if p.Collide then
				row.props.solid += 1
			else
				row.props.nonsolid += 1
			end
			local original = library:FindFirstChild(p.Prop, true)
			assert(original and original:IsA("BasePart"), c.Id .. " missing prop " .. p.Prop)
			if p.Collide then
				local clone = original:Clone()
				local r = p.R
				clone.Size = Vector3.new(unpack(p.S))
				clone.CFrame = CFrame.new(base)
					* CFrame.new(p.P[1], p.P[2], p.P[3], unpack(r))
					* rotation(selected)
				clone.Anchored = true
				clone.CanQuery = true
				clone.CanCollide = true
				clone.Parent = solid
			end
		end
		local sp = query({ solid })
		heartbeat:Wait()
		local function samples(mouth, inward, width)
			local across = Vector3.new(-inward.Z, 0, inward.X)
			local result = {}
			for _, depth in report.inset do
				for _, lateral in
					{ -width / 2 + cfg.EdgeMargin, -8, 0, 8, width / 2 - cfg.EdgeMargin }
				do
					local p = mouth + inward * depth + across * lateral
					local obstruction =
						workspace:Raycast(base + p + Vector3.new(0, 2, 0), Vector3.new(0, 5, 0), sp)
					local side = workspace:Raycast(
						base + p + Vector3.new(-2, 3, 0),
						Vector3.new(4, 0, 0),
						sp
					)
					table.insert(result, {
						depth = depth,
						lateral = lateral,
						terrain = probe(p, tp, tolerance),
						collision = probe(p, cp, tolerance),
						solidObstruction = (obstruction or side)
								and (obstruction or side).Instance.Name
							or false,
					})
				end
			end
			return result
		end
		for i, s in c.Sockets do
			local mouth = Vector3.new(s.OffsetX, s.OffsetY, s.OffsetZ)
			table.insert(row.sockets, {
				index = i,
				name = s.Id,
				kind = s.Kind,
				facing = s.Facing,
				layoutFacing = s.Facing,
				offset = { s.OffsetX, s.OffsetY, s.OffsetZ },
				width = s.Width,
				samples = samples(mouth, Vector3.new(-s.OffsetX, 0, -s.OffsetZ).Unit, s.Width),
			})
		end
		for facing = 0, 270, 90 do
			local inward = -rotation(facing).LookVector
			local edge = if facing % 180 == 0 then c.SizeZ / 2 else c.SizeX / 2
			table.insert(
				row.cardinal,
				{ facing = facing, samples = samples(-inward * edge, inward, 48) }
			)
		end
		table.insert(report.chunks, row)
		terrain:Destroy()
		collision:Destroy()
		solid:Destroy()
	end
	return report
end
local ok, result = pcall(run)
container:Destroy()
if not ok then
	error(result)
end
return game:GetService("HttpService"):JSONEncode(result)
