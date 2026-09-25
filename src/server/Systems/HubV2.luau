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
local function walkable(src: MeshPart): MeshPart?
	-- the imported copy is only a stand-in when this fails, so say so loudly
	local ok, made = pcall(function()
		return AssetService:CreateMeshPartAsync(src.MeshId, {
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
	warn(`[HubV2] {src.Name}: precise collision failed to build ({tostring(made)}); keeping the imported hull`)
	return nil
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
-- GLOW THAT LIGHTS (owner, 2026-09-24: "lanterns and glowing parts should emit
-- just a little bit of light"). A small PointLight on each glowing piece, by
-- name; colour from what it is. Kept short-ranged and dim: there are dozens.
local LIGHTS: { { string | Color3 | number } } = {
	{ "lamp_glow", Color3.fromRGB(124, 245, 224), 14, 0.9 },
	{ "brazier_flame", Color3.fromRGB(255, 160, 80), 22, 1.4 },
	{ "stall_lantern", Color3.fromRGB(255, 170, 90), 14, 1.0 },
	{ "engine_wisp", Color3.fromRGB(180, 150, 255), 18, 1.0 },
	{ "beacon_shard", Color3.fromRGB(147, 235, 255), 22, 1.2 },
	{ "keel_core_", Color3.fromRGB(147, 235, 255), 40, 1.2 },
	{ "obelisk_crystal", Color3.fromRGB(200, 170, 255), 14, 0.8 },
	{ "hall_heart", Color3.fromRGB(255, 170, 220), 26, 1.2 },
	{ "oculus_crystal", Color3.fromRGB(147, 235, 255), 26, 1.2 },
	{ "shop_coin", Color3.fromRGB(255, 210, 120), 24, 1.2 },
	{ "training_emblem", Color3.fromRGB(255, 160, 80), 18, 0.9 },
	{ "thruster_flame", Color3.fromRGB(147, 235, 255), 30, 1.4 },
	{ "__flame", Color3.fromRGB(255, 160, 80), 12, 0.9 },
	{ "__lift", Color3.fromRGB(147, 235, 255), 14, 0.7 },
	{ "__glow", Color3.fromRGB(124, 245, 224), 20, 1.0 },
}

local function addLight(p: BasePart)
	for _, l in LIGHTS do
		if string.find(p.Name, l[1] :: string, 1, true) then
			local light = Instance.new("PointLight")
			light.Color = l[2] :: Color3
			light.Range = l[3] :: number
			light.Brightness = l[4] :: number
			light.Shadows = false
			light.Parent = p
			return
		end
	end
end

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
	local pieceCount = 0
	for _ in V2.Pieces do
		pieceCount += 1
	end
	-- the loading screen waits for this many hub pieces before anything else
	model:SetAttribute("PieceCount", pieceCount)
	for name, info in V2.Pieces do
		local src = template("HUB_CROSSROADS_V2", prefabs, name)
		if not src then
			table.insert(missing, name)
			continue
		end
		-- The levitator hangs under everything and is never stood on.
		local collide = name ~= "HUB_LEVITATOR"
		-- SHOWN AT ONCE, SOLID LATER. The imported piece goes in straight
		-- away so the hub is never missing; the precise-collision copy is
		-- built in the background and swapped in when it is ready. Building
		-- it inline held the whole hub back (and hid it) while Roblox made
		-- six collision hulls one after another.
		local p = src:Clone()
		place(p, origin + info.Centre, collide, model)
		-- queryable even where not solid: sky props look ahead against it
		p.CanQuery = true
		if collide then
			task.spawn(function()
				local solid = walkable(src)
				if solid and p.Parent then
					place(solid, p.CFrame.Position, true, model)
					p:Destroy()
				end
			end)
		end
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
		addLight(p)
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
	-- A Model that is never streamed out: every client gets the whole sky, not
	-- just the side it spawned facing (the far side used to arrive late and
	-- sit still -- owner, 2026-09-24: "it favored one side over the other").
	local sky = Instance.new("Model")
	sky.Name = "Sky"
	sky.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
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
			-- not solid, but queryable: sky props steer round it and dock beside it
			p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, true, false
			p.CFrame = CFrame.new(origin + Vector3.new(math.cos(a) * r, rng:NextNumber(b.HeightMin, b.HeightMax), math.sin(a) * r))
				* CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
			p:SetAttribute("Backdrop", true)
			p.Parent = sky
		end
	end

	-- THE SKY BEYOND: cloud sea, far range, moon, planet, the ring overhead.
	HubV2.buildBeyond(sky, origin, prefabs, chunks, rng)

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
			-- WANDERERS, not orbiters (owner, 2026-09-24): each one is moved by
			-- the client's SkyTraffic on its own course, at its own changing
			-- speed, inside its band, steering clear of the hub, the backdrop
			-- and every other prop. The server only says where it may go.
			p:SetAttribute("Wander", true)
			p:SetAttribute("WanderCentre", origin)
			p:SetAttribute("WanderRadius", Vector2.new(entry.RadiusMin, entry.RadiusMax))
			p:SetAttribute("WanderHeight", Vector2.new(origin.Y + entry.HeightMin, origin.Y + entry.HeightMax))
			p:SetAttribute("WanderSpeed", Vector2.new(entry.SpeedMin, entry.SpeedMax))
			p:SetAttribute("WanderFaces", entry.Faces == true)
			p:SetAttribute("WanderBob", entry.Bob or 0)
			p:SetAttribute("WanderSeed", rng:NextInteger(1, 1e6))
			local _ = radius + height + phase
			-- 1 always shown, 2 medium graphics and up, 3 high only.
			p:SetAttribute("Detail", if k == 1 then entry.Detail else math.min(3, entry.Detail + (k > 2 and 1 or 0)))
			p.Parent = sky
			-- its moving pieces (propellers, flippers, flames), hung off the
			-- body; SkyTraffic moves them with it and animates each one
			for subName, sub in V2.OrbiterParts do
				if sub.Parent ~= src.Name then
					continue
				end
				local sp = lib:FindFirstChild(subName, true)
				if not (sp and sp:IsA("BasePart")) then
					continue
				end
				local q = sp:Clone()
				q.Anchored, q.CanCollide, q.CanQuery, q.CanTouch = true, false, false, false
				q.Size = sp.Size * s
				q:SetAttribute("Wander", true) -- so HubEffects leaves it to SkyTraffic
				q:SetAttribute("Detail", p:GetAttribute("Detail"))
				q:SetAttribute("SubKind", sub.Kind)
				q:SetAttribute("SubOffset", sub.Offset * s)
				q:SetAttribute("SubHinge", sub.Hinge * s)
				q:SetAttribute("SubAxis", sub.Axis)
				q:SetAttribute("SubAmp", sub.Amp)
				q:SetAttribute("SubRate", sub.Rate)
				q:SetAttribute("SubPhase", sub.Phase)
				q.CFrame = p.CFrame * CFrame.new(sub.Offset * s)
				q.Parent = p
				addLight(q)
			end
			n += 1
		end
	end
	print(`[HubV2] sky: {#chunks > 0 and cfg.Backdrop.Count or 0} backdrop chunk(s), {n} orbiter(s)`)
end

local function still(p: BasePart, cf: CFrame, parent: Instance)
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.CFrame = cf
	p.Parent = parent
end

--- The sky beyond the islands: the cloud sea, the far range, the moon, the
--- ringed planet and the celestial ring above the Engine.
function HubV2.buildBeyond(sky: Instance, origin: Vector3, prefabs: Instance?, chunks: { MeshPart }, rng: Random)
	local lib = prefabs and prefabs:FindFirstChild("HUB_SKY")
	local c = cfg
	if lib then
		-- the cloud sea: the cloud props' puffs as banks, in two drifting layers
		local banks = {}
		for _, n in { "hubsky_cloudbank_a", "hubsky_cloudbank_b", "hubsky_cloudbank_c" } do
			local b = lib:FindFirstChild(n, true)
			if b and b:IsA("MeshPart") then
				table.insert(banks, b)
			end
		end
		for _, layer in c.CloudSea do
			for _ = 1, (if #banks > 0 then layer.Count else 0) do
				local src = banks[rng:NextInteger(1, #banks)]
				local p = src:Clone()
				p.Size = src.Size * rng:NextNumber(layer.ScaleMin, layer.ScaleMax)
				local a, r = rng:NextNumber(0, math.pi * 2), math.sqrt(rng:NextNumber()) * layer.RadiusMax
				still(p, CFrame.new(origin + Vector3.new(math.cos(a) * r, layer.Y + rng:NextNumber(-20, 20), math.sin(a) * r))
					* CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), sky)
				p:SetAttribute("Drift", layer.Drift * rng:NextNumber(0.7, 1.3))
				p:SetAttribute("DriftSeed", rng:NextInteger(1, 1e6))
				p:SetAttribute("DriftCentre", origin)
				if layer.Detail then
					p:SetAttribute("Detail", layer.Detail)
				end
			end
		end
		-- the moon: a glowing disc through the haze
		local moon = lib:FindFirstChild("hubsky_moon", true)
		if moon and moon:IsA("MeshPart") then
			local m = c.Moon
			local p = moon:Clone()
			p.Size = moon.Size * m.Scale
			p.Material = Enum.Material.Neon
			p.Color = m.Color
			local az, el = math.rad(m.Azimuth), math.rad(m.Elevation)
			still(p, CFrame.new(origin + Vector3.new(math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el))
				* m.Distance), sky)
		end
		-- the ringed planet, low on the far horizon
		local planet = lib:FindFirstChild("hubsky_planet", true)
		if planet and planet:IsA("MeshPart") then
			local m = c.Planet
			local p = planet:Clone()
			p.Size = planet.Size * m.Scale
			local az, el = math.rad(m.Azimuth), math.rad(m.Elevation)
			still(p, CFrame.new(origin + Vector3.new(math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el))
				* m.Distance) * CFrame.Angles(0.2, 0.6, 0.15), sky)
		end
		-- the celestial ring above the Engine, its runes pulsing between colours
		-- the ring's heart: spokes and constellation turn with it, the star-core
		-- counter-turns, the two gyroscopes precess at their own rates
		local HEART = {
			hubsky_ring_spokes = { Spin = c.Ring.Spin },
			hubsky_ring_constellation = { Spin = c.Ring.Spin, Neon = true, Alpha = 0.3,
				A = c.Ring.GlyphA, B = c.Ring.GlyphB, Seconds = 14 },
			hubsky_ring_core = { Spin = -0.12, Neon = true, A = Color3.fromRGB(147, 235, 255),
				B = Color3.fromRGB(236, 220, 255), Seconds = 6 },
			hubsky_ring_gyro_a = { Spin = 0.22 },
			hubsky_ring_gyro_b = { Spin = -0.16 },
		}
		for n, h in HEART do
			local src = lib:FindFirstChild(n, true)
			if src and src:IsA("MeshPart") then
				local p = src:Clone()
				still(p, CFrame.new(origin + Vector3.new(0, c.Ring.Height, 0)), sky)
				p:SetAttribute("SkySpin", h.Spin)
				if h.Neon then
					p.Material = Enum.Material.Neon
					p.Transparency = h.Alpha or 0
					p.Color = h.A
					p:SetAttribute("SkyColorA", h.A)
					p:SetAttribute("SkyColorB", h.B)
					p:SetAttribute("SkyColorSeconds", h.Seconds)
				end
				if n == "hubsky_ring_core" then
					local light = Instance.new("PointLight")
					light.Color, light.Range, light.Brightness, light.Shadows = h.A, 60, 2, false
					light.Parent = p
				end
			end
		end
		-- a beam of light from above the Engine's portal up into the heart
		do
			local function anchorAt(y: number): Attachment
				local a = Instance.new("Part")
				a.Name = "HeartBeamAnchor"
				a.Size = Vector3.one
				a.Transparency = 1
				still(a, CFrame.new(origin + Vector3.new(0, y, 0)), sky)
				local att = Instance.new("Attachment")
				att.Parent = a
				return att
			end
			local beam = Instance.new("Beam")
			beam.Attachment0 = anchorAt(c.Ring.BeamFrom)
			beam.Attachment1 = anchorAt(c.Ring.Height - 20)
			beam.FaceCamera = true
			beam.LightEmission = 1
			beam.LightInfluence = 0
			beam.Width0, beam.Width1 = 4, 12
			beam.Color = ColorSequence.new(c.Ring.GlyphA, c.Ring.GlyphB)
			beam.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.25, 0.75),
				NumberSequenceKeypoint.new(1, 0.45),
			})
			beam.Parent = beam.Attachment0.Parent
		end
		for _, n in { "hubsky_ring", "hubsky_ring_glyphs" } do
			local src = lib:FindFirstChild(n, true)
			if src and src:IsA("MeshPart") then
				local p = src:Clone()
				still(p, CFrame.new(origin + Vector3.new(0, c.Ring.Height, 0)), sky)
				-- driven by SkyTraffic, not HubEffects: HubEffects skips anything
				-- beyond its animation distance, and the ring is 430 studs up
				p:SetAttribute("SkySpin", c.Ring.Spin)
				if n == "hubsky_ring_glyphs" then
					p.Material = Enum.Material.Neon
					p.Color = c.Ring.GlyphA
					p:SetAttribute("SkyColorA", c.Ring.GlyphA)
					p:SetAttribute("SkyColorB", c.Ring.GlyphB)
					p:SetAttribute("SkyColorSeconds", 9)
				end
			end
		end
	else
		warn("[HubV2] ServerStorage.LuckboundPrefabs.HUB_SKY missing -- no cloud sea, moon or ring")
	end
	-- the far range: the backdrop chunks again, huge and darkened, on the horizon
	local f = c.FarRange
	for i = 1, (if #chunks > 0 then f.Count else 0) do
		local src = chunks[rng:NextInteger(1, #chunks)]
		local p = src:Clone()
		p.Size = src.Size * rng:NextNumber(f.ScaleMin, f.ScaleMax)
		p.Color = f.Tint
		local a = (i + rng:NextNumber(-0.4, 0.4)) / f.Count * math.pi * 2
		local r = rng:NextNumber(f.RadiusMin, f.RadiusMax)
		still(p, CFrame.new(origin + Vector3.new(math.cos(a) * r, rng:NextNumber(f.HeightMin, f.HeightMax), math.sin(a) * r))
			* CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), sky)
	end
end

return HubV2
