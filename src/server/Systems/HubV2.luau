--!strict
-- THE CROSSROADS v2 (2026-09-23), built around the untouched Fate Engine.
--
-- Art: assets/source/hub/crossroads/ (Blender), imported as
--   ServerStorage.LuckboundPrefabs.HUB_CROSSROADS_V2  -- platform, levitator, four districts
--   ServerStorage.LuckboundPrefabs.HUB_ANIMATED        -- every part that moves
--   ServerStorage.LuckboundPrefabs.HUB_BACKDROP_V2     -- three floating-mountain chunks
--   ReplicatedStorage.LuckboundProps.HUB_ORBITERS      -- ships, isles, clouds, the whale
-- Placement: Content/Hub/CrossroadsV2 (generated from the Blender layout).
--
-- THE IMPORTER TURNED THE MODEL 180 DEGREES (north landed at +Z, as it did for
-- the old hub), and the turn is baked into each mesh. So every piece goes to
-- its layout centre with a half turn about its own vertical axis, which puts
-- the geometry back the way it was designed.
--
-- The hub pieces are the same in every server. The backdrop and the orbiters
-- are drawn at random per server; orbiters carry a Detail level (1-3) that the
-- client compares with its graphics quality, so low-end devices show fewer.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local V2 = require(Root.Content.Hub.CrossroadsV2)

local HubV2 = {}

local HALF_TURN = CFrame.Angles(0, math.pi, 0)
local cfg = GameConfig.HubLayout.V2

local function template(folderName: string, container: Instance?, name: string): MeshPart?
	local model = container and container:FindFirstChild(folderName)
	local found = model and model:FindFirstChild(name, true)
	return if found and found:IsA("MeshPart") then found else nil
end

-- A walkable piece needs a collision hull that follows the mesh. Default
-- fidelity would fill every arch and doorway, and CollisionFidelity cannot be
-- set on a clone at run time -- so walkable pieces are made fresh from their
-- MeshId at PreciseConvexDecomposition, as ChunkLoader does for biome chunks.
local function walkable(src: MeshPart): MeshPart
	local ok, made = pcall(function()
		return AssetService:CreateMeshPartAsync(src.MeshID, {
			CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
		})
	end)
	if ok and made then
		made.Name = src.Name
		made.Size = src.Size
		made.Color = src.Color
		made.Material = src.Material
		return made
	end
	warn(`[HubV2] {src.Name}: precise collision failed to build; using the imported hull`)
	return src:Clone()
end

local function place(p: BasePart, centre: Vector3, collide: boolean, parent: Instance)
	p.Anchored = true
	p.CanCollide = collide
	p.CanTouch = false
	p.CanQuery = collide
	p.CastShadow = true
	p.CFrame = CFrame.new(centre) * HALF_TURN
	p.Parent = parent
end

-- How the game animates each kind (HubEffects reads these attributes).
local KIND_ATTRS: { [string]: { [string]: any } } = {
	Spin = { SpinSpeed = 0.5, SpinAxis = "Y" },
	Bob = { BobStuds = 1.2, BobSeconds = 4.5 },
	SpinBob = { SpinSpeed = 0.7, SpinAxis = "Y", BobStuds = 0.8, BobSeconds = 3.6 },
	Flicker = { PulseAlphaMin = 0, PulseAlphaMax = 0.35, PulseSeconds = 0.5 },
}

--- Builds the hub pieces and the animated parts. Returns nil when the art is
--- not in the place (no Rojo, missing file), and HubBuilder falls back.
function HubV2.build(hub: Instance, origin: Vector3): Model?
	local prefabs = ServerStorage:FindFirstChild(Constants.NAMES.PREFABS_FOLDER)
	if not (prefabs and prefabs:FindFirstChild("HUB_CROSSROADS_V2")) then
		return nil
	end
	local model = Instance.new("Model")
	model.Name = "CrossroadsV2"
	model.Parent = hub

	local placed, missing = 0, {}
	for name, info in V2.Pieces do
		local src = template("HUB_CROSSROADS_V2", prefabs, name)
		if not src then
			table.insert(missing, name)
			continue
		end
		-- The levitator hangs under everything and is never stood on.
		local collide = name ~= "HUB_LEVITATOR"
		local p = if collide then walkable(src) else src:Clone()
		place(p, origin + info.Centre, collide, model)
		placed += 1
	end

	local moving = Instance.new("Folder")
	moving.Name = "Animated"
	moving.Parent = model
	for name, info in V2.Animated do
		local src = template("HUB_ANIMATED", prefabs, name)
		if not src then
			table.insert(missing, name)
			continue
		end
		local p = src:Clone()
		place(p, origin + info.Centre, false, moving)
		local attrs = KIND_ATTRS[info.Kind]
		if attrs then
			for k, v in attrs do
				p:SetAttribute(k, v)
			end
		end
		-- Wares turn slowly on their stands; nothing on a counter should spin fast.
		if string.find(name, "^anim_ware_") then
			p:SetAttribute("SpinSpeed", 0.35)
			p:SetAttribute("BobStuds", 0.25)
		end
		placed += 1
	end
	if #missing > 0 then
		warn(`[HubV2] {#missing} part(s) not in the imported files: {table.concat(missing, ", ", 1, math.min(#missing, 8))}`)
	end
	print(`[HubV2] Crossroads v2: {placed} parts placed`)
	return model
end

--- The skyline and the traffic: random per server.
function HubV2.buildSky(hub: Instance, origin: Vector3)
	local prefabs = ServerStorage:FindFirstChild(Constants.NAMES.PREFABS_FOLDER)
	local props = ReplicatedStorage:FindFirstChild("LuckboundProps")
	local rng = Random.new()
	local sky = Instance.new("Folder")
	sky.Name = "Sky"
	sky.Parent = hub

	-- Backdrop: floating mountains in a ring, each a random chunk, turn, size and height.
	local chunks = {}
	for name in V2.Backdrop do
		local src = template("HUB_BACKDROP_V2", prefabs, name)
		if src then
			table.insert(chunks, src)
		end
	end
	if #chunks > 0 then
		local b = cfg.Backdrop
		for i = 1, b.Count do
			local src = chunks[rng:NextInteger(1, #chunks)]
			local p = src:Clone()
			local s = rng:NextNumber(b.ScaleMin, b.ScaleMax)
			p.Size = src.Size * s
			local a = (i + rng:NextNumber(-0.35, 0.35)) / b.Count * math.pi * 2
			local r = rng:NextNumber(b.RadiusMin, b.RadiusMax)
			p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
			p.CFrame = CFrame.new(origin + Vector3.new(math.cos(a) * r, rng:NextNumber(b.HeightMin, b.HeightMax), math.sin(a) * r))
				* CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
			p.Parent = sky
		end
	end

	-- Orbiters: which ones, how many, and at what detail level.
	local lib = props and props:FindFirstChild("HUB_ORBITERS")
	if not lib then
		warn("[HubV2] LuckboundProps.HUB_ORBITERS missing -- no orbiters")
		return
	end
	local n = 0
	for _, entry in cfg.Orbiters do
		local names = entry.Names
		local count = rng:NextInteger(entry.Min, entry.Max)
		for k = 1, count do
			local src = lib:FindFirstChild(names[rng:NextInteger(1, #names)], true)
			if not (src and src:IsA("BasePart")) then
				continue
			end
			local p = src:Clone()
			p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
			local s = rng:NextNumber(entry.ScaleMin or 1, entry.ScaleMax or 1)
			p.Size = src.Size * s
			local radius = rng:NextNumber(entry.RadiusMin, entry.RadiusMax)
			local height = origin.Y + rng:NextNumber(entry.HeightMin, entry.HeightMax)
			local phase = rng:NextNumber(0, math.pi * 2)
			p.CFrame = CFrame.new(origin + Vector3.new(math.cos(phase) * radius, height - origin.Y, math.sin(phase) * radius))
			p:SetAttribute("OrbitCentre", origin)
			p:SetAttribute("OrbitRadius", radius)
			p:SetAttribute("OrbitHeight", height)
			p:SetAttribute("OrbitPhase", phase)
			-- Speed in radians/second: about the same stud speed at any radius,
			-- some flying the other way round.
			local dir = if rng:NextNumber() < 0.3 then -1 else 1
			p:SetAttribute("OrbitSpeed", dir * rng:NextNumber(entry.SpeedMin, entry.SpeedMax) / radius)
			-- Ships' noses point along the imported -X, so a quarter turn faces
			-- them along their path; the reverse way round needs the opposite.
			p:SetAttribute("OrbitYaw", if entry.Faces then (if dir > 0 then 90 else -90) else rng:NextNumber(0, 360))
			p:SetAttribute("OrbitBob", entry.Bob or 0)
			-- 1 always shown, 2 medium graphics and up, 3 high only.
			p:SetAttribute("Detail", if k == 1 then entry.Detail else math.min(3, entry.Detail + (k > 2 and 1 or 0)))
			p.Parent = sky
			n += 1
		end
	end
	print(`[HubV2] sky: {#chunks > 0 and cfg.Backdrop.Count or 0} backdrop chunk(s), {n} orbiter(s)`)
end

return HubV2
