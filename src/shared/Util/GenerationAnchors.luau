--!strict
-- Server-owned bounded cache of chunk-local presentation samples.
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local GenerationAnchors = {}
function GenerationAnchors.new(config: any): any
	local owner = {}
	local samples: { [string]: any } = {}
	local order = {}
	local counters = {}
	local function count(name: string)
		if config.AssetPreparationDiagnostics then
			counters[name] = (counters[name] or 0) + 1
		end
	end

	function owner.clear()
		table.clear(samples)
		table.clear(order)
	end

	function owner.stats(): any
		local entries, sampleCount = 0, 0
		for _, list in samples do
			entries += 1
			sampleCount += #list
		end
		return { Entries = entries, Samples = sampleCount, Counters = table.clone(counters) }
	end

	function owner.pending(stage: Instance, floorY: number): any
		local minX, minZ, maxX, maxZ = math.huge, math.huge, -math.huge, -math.huge
		for _, chunk in stage:GetChildren() do
			local c = chunk:GetAttribute("Centre")
			if typeof(c) == "Vector3" then
				minX, maxX = math.min(minX, c.X - 128), math.max(maxX, c.X + 128)
				minZ, maxZ = math.min(minZ, c.Z - 128), math.max(maxZ, c.Z + 128)
			end
		end
		if minX == math.huge then
			return nil
		end
		return {
			Tips = {},
			Path = {},
			Pending = true,
			Min = Vector3.new(minX, floorY, minZ),
			Max = Vector3.new(maxX, floorY, maxZ),
		}
	end

	-- Discover on the server, where streaming does not hide remote chunks.
	-- Tips hold peak lights; Path holds patrol/ground-effect locations.
	function owner.scan(stage: Instance, floorY: number, current: (() -> boolean)?): any
		local queried = 0
		local tips, path = {}, {}
		local minX, minZ, maxX, maxZ = math.huge, math.huge, -math.huge, -math.huge
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		local function far(list: { Vector3 }, p: Vector3, gap: number): boolean
			for _, q in list do
				if (Vector3.new(q.X - p.X, 0, q.Z - p.Z)).Magnitude < gap then
					return false
				end
			end
			return true
		end
		for _, chunk in stage:GetChildren() do
			local c = chunk:GetAttribute("Centre")
			if typeof(c) ~= "Vector3" then
				continue
			end
			minX, maxX = math.min(minX, c.X - 128), math.max(maxX, c.X + 128)
			minZ, maxZ = math.min(minZ, c.Z - 128), math.max(maxZ, c.Z + 128)
			params.FilterDescendantsInstances = { chunk }
			local frame = CFrame.new(c)
				* CFrame.Angles(0, -math.rad(chunk:GetAttribute("Yaw") or 0), 0)
			local key = table.concat({
				tostring(stage:GetAttribute("WorldId")),
				tostring(chunk:GetAttribute("ChunkId")),
				tostring(stage:GetAttribute("Atmosphere")),
				tostring(chunk:GetAttribute("ArtYawOffset")),
				tostring(chunk:GetAttribute("AssetKey")),
				tostring(chunk:GetAttribute("Blockout")),
				tostring(chunk:GetAttribute("WalkCollisionPieces")),
				tostring(c.Y - floorY),
			}, ":")
			-- Encounter gates can move after boss completion. Their physics state is
			-- runtime information, so this chunk remains on the discovery path.
			local static = chunk:FindFirstChild("EncounterGate") == nil
			local cached = if static then samples[key] else nil
			local grid = {}
			if cached then
				count("AnchorCacheHits")
				for _, sample in cached do
					table.insert(grid, {
						Position = frame:PointToWorldSpace(sample.Position),
						Normal = frame:VectorToWorldSpace(sample.Normal),
					})
				end
				-- Recover the original world-grid acquisition order before the legacy
				-- height sort. Otherwise equal-height decks change greedy anchor picks
				-- when one cached definition is reused at a different quarter turn.
				table.sort(grid, function(a, b)
					return if a.Position.X == b.Position.X
						then a.Position.Z < b.Position.Z
						else a.Position.X < b.Position.X
				end)
			else
				count("AnchorCacheMisses")
				for gx = -124, 124, 8 do
					for gz = -124, 124, 8 do
						count("AtmosphereRaycasts")
						queried += 1
						if
							config.DeferredAtmosphere
							and queried % config.AtmosphereRayBudget == 0
						then
							RunService.Heartbeat:Wait()
							if stage.Parent == nil or (current and not current()) then
								return nil
							end
						end
						local r = Workspace:Raycast(
							Vector3.new(c.X + gx, floorY + 400, c.Z + gz),
							Vector3.new(0, -800, 0),
							params
						)
						if r then
							table.insert(grid, r)
						end
					end
				end
				if static then
					local localSamples = {}
					for _, hit in grid do
						table.insert(localSamples, {
							Position = frame:PointToObjectSpace(hit.Position),
							Normal = frame:VectorToObjectSpace(hit.Normal),
						})
					end
					if not samples[key] then
						table.insert(order, key)
					end
					samples[key] = localSamples
					while #order > config.AtmosphereCacheEntries do
						samples[table.remove(order, 1)] = nil
					end
				end
			end
			-- peaks: highest first; a peak stands clear of anything higher nearby
			table.sort(grid, function(a, b)
				return a.Position.Y > b.Position.Y
			end)
			local picked = {}
			for _, r in grid do
				local h = r.Position
				if #picked >= 6 then
					break
				end
				local deck = math.abs(h.Y - floorY) < 8
				if not deck and r.Normal.Y > 0.6 and far(picked, h, 40) and far(tips, h, 30) then
					table.insert(picked, h)
					table.insert(tips, h)
				end
			end
			-- the walkway: level surfaces at the walk plane
			local mine = {}
			for _, r in grid do
				local h = r.Position
				if math.abs(h.Y - floorY) < 8 and r.Normal.Y > 0.9 and far(mine, h, 28) then
					table.insert(mine, h)
					table.insert(path, h)
				end
			end
		end
		if minX == math.huge then
			return nil
		end
		if stage.Parent == nil or (current and not current()) then
			return nil
		end
		return {
			Tips = tips,
			Path = path,
			Min = Vector3.new(minX, floorY, minZ),
			Max = Vector3.new(maxX, floorY, maxZ),
		}
	end

	return owner
end

return GenerationAnchors
