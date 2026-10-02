--!strict
-- Production scan algorithm with experimental budgeted work and local sample reuse.
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local GenerationProfile = require(script.Parent.GenerationProfile)
local GenerationAnchors = {}
local samples: { [string]: any } = {}

function GenerationAnchors.clear()
	table.clear(samples)
end

function GenerationAnchors.stats(): any
	local entries, count = 0, 0
	for _, list in samples do
		entries += 1
		count += #list
	end
	return { Entries = entries, Samples = count, SerializedFloat64PayloadBytes = count * 6 * 8 }
end

function GenerationAnchors.pending(stage: Instance, floorY: number): any
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

function GenerationAnchors.scan(stage: Instance, floorY: number, profile: any?): any
	local started = os.clock()
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
		local frame = CFrame.new(c) * CFrame.Angles(0, -math.rad(chunk:GetAttribute("Yaw") or 0), 0)
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
		local cached = if static and profile and profile.Stage == "F" then samples[key] else nil
		local grid = {}
		if cached then
			GenerationProfile.count(profile, "AnchorCacheHits")
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
			GenerationProfile.count(profile, "AnchorCacheMisses")
			for gx = -124, 124, 8 do
				for gz = -124, 124, 8 do
					GenerationProfile.count(profile, "AtmosphereRaycasts")
					if
						profile
						and profile.Stage >= "E"
						and (profile.Counters.AtmosphereRaycasts % profile.RayBudget == 0)
					then
						RunService.Heartbeat:Wait()
						if stage.Parent == nil then
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
			if static and profile and profile.Stage == "F" then
				local localSamples = {}
				for _, hit in grid do
					table.insert(localSamples, {
						Position = frame:PointToObjectSpace(hit.Position),
						Normal = frame:VectorToObjectSpace(hit.Normal),
					})
				end
				samples[key] = localSamples
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
	GenerationProfile.time(profile, "AtmosphereAnchors", started)
	return {
		Tips = tips,
		Path = path,
		Min = Vector3.new(minX, floorY, minZ),
		Max = Vector3.new(maxX, floorY, maxZ),
	}
end

return GenerationAnchors
