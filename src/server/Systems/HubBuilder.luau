--!strict
-- Builds the Crossroads from Content/Hub/Crossroads data. Build spec T-112.
--
-- Contains no art direction. Every colour, size and position comes from the
-- data file. If you want the hub to look different, edit the data -- if you
-- find yourself editing this file to change how something looks, the schema
-- is missing a field and that is the bug.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local Layout = require(Root.Content.Hub.Crossroads)

local HubBuilder = {}

local function part(props: { [string]: any }, parent: Instance): BasePart
	local p = Instance.new(props.Shape or "Part") :: BasePart
	p.Anchored = true
	p.CanCollide = props.CanCollide ~= false
	p.Material = props.Material or Layout.Theme.StoneMaterial
	p.Color = props.Color or Layout.Theme.Stone
	p.Size = props.Size or Vector3.one
	p.CFrame = props.CFrame or CFrame.new(props.Position or Vector3.zero)
	p.Name = props.Name or "Part"
	if props.Transparency then
		p.Transparency = props.Transparency
	end
	if props.Shape == "Part" and props.PartShape then
		(p :: Part).Shape = props.PartShape
	end
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

--- Uses a mesh when the data supplies one, primitives otherwise. This is the
--- seam that lets authored art replace blockout one piece at a time.
local function meshOrPrimitive(meshId: string?, size: Vector3, cframe: CFrame, name: string, parent: Instance): BasePart?
	if not meshId then
		return nil
	end
	local p = Instance.new("MeshPart")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Parent = parent
	-- MeshId is assigned last: setting it resizes the part, so Size is a hint.
	local ok, err = pcall(function()
		p.MeshId = meshId
	end)
	if not ok then
		warn(`[HubBuilder] mesh {meshId} failed to load for {name}: {err}; falling back to primitive`)
		p:Destroy()
		return nil
	end
	return p
end

local function positionFor(angleDegrees: number, radius: number, height: number): Vector3
	local rad = math.rad(angleDegrees)
	return Vector3.new(math.sin(rad) * radius, height, -math.cos(rad) * radius)
end

local function applyLighting()
	local theme = Layout.Theme
	Lighting.Ambient = theme.Ambient
	Lighting.OutdoorAmbient = theme.OutdoorAmbient
	Lighting.ClockTime = theme.ClockTime
	Lighting.Brightness = 2
	Lighting.FogColor = theme.FogColor
	Lighting.FogStart = theme.FogStart
	Lighting.FogEnd = theme.FogEnd

	local sky = Lighting:FindFirstChildOfClass("Sky") or Instance.new("Sky")
	sky.Parent = Lighting

	local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
	atmosphere.Density = 0.32
	atmosphere.Haze = 2
	atmosphere.Color = theme.SkyHorizon
	atmosphere.Decay = theme.SkyTop
	atmosphere.Parent = Lighting

	local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
	bloom.Intensity = 0.7
	bloom.Size = 24
	bloom.Threshold = 0.9
	bloom.Parent = Lighting
end

local function buildFateEngine(parent: Instance)
	local cfg = Layout.FateEngine
	local engine = Instance.new("Model")
	engine.Name = Constants.NAMES.FATE_ENGINE
	engine.Parent = parent

	local base = cfg.Position

	if not meshOrPrimitive(cfg.MeshId, Vector3.new(cfg.BaseRadius * 2, cfg.Height, cfg.BaseRadius * 2),
		CFrame.new(base + Vector3.new(0, cfg.Height / 2, 0)), "EngineMesh", engine) then

		-- Plinth
		part({
			Name = "Plinth",
			Shape = "Part",
			PartShape = Enum.PartType.Cylinder,
			Size = Vector3.new(6, cfg.BaseRadius * 2.4, cfg.BaseRadius * 2.4),
			CFrame = CFrame.new(base + Vector3.new(0, 3, 0)) * CFrame.Angles(0, 0, math.rad(90)),
			Color = Layout.Theme.StoneDark,
		}, engine)

		-- Rings. Each spins at its own speed, alternating direction, so the
		-- silhouette reads as a machine rather than a decoration.
		local rings = Instance.new("Folder")
		rings.Name = "Rings"
		rings.Parent = engine

		for i = 1, cfg.RingCount do
			local t = i / cfg.RingCount
			local ring = part({
				Name = `Ring{i}`,
				Shape = "Part",
				PartShape = Enum.PartType.Cylinder,
				Size = Vector3.new(cfg.RingThickness, cfg.BaseRadius * 2 * (1.5 - t * 0.5), cfg.BaseRadius * 2 * (1.5 - t * 0.5)),
				CFrame = CFrame.new(base + Vector3.new(0, 14 + (i - 1) * 12, 0))
					* CFrame.Angles(0, 0, math.rad(90)),
				Color = cfg.RingColor,
				Material = Enum.Material.Metal,
				CanCollide = false,
			}, rings)
			ring:SetAttribute("SpinSpeed", cfg.SpinSpeeds[i] or 0.3)
		end

		-- Core: the thing that flashes on a roll.
		local core = part({
			Name = "Core",
			Shape = "Part",
			PartShape = Enum.PartType.Ball,
			Size = Vector3.new(cfg.CoreSize, cfg.CoreSize, cfg.CoreSize),
			Position = base + Vector3.new(0, cfg.Height * 0.55, 0),
			Color = cfg.CoreColor,
			Material = Enum.Material.Neon,
			CanCollide = false,
		}, engine)

		local light = Instance.new("PointLight")
		light.Color = cfg.CoreColor
		light.Brightness = 4
		light.Range = 90
		light.Parent = core
	end

	-- The anchor the server measures roll distance from. Always present,
	-- mesh or not -- FateSystem depends on it by name.
	local anchor = part({
		Name = Constants.NAMES.ROLL_ANCHOR,
		Size = cfg.AnchorSize,
		Position = base + Vector3.new(0, cfg.AnchorHeight, 0),
		Transparency = 1,
		CanCollide = false,
		Color = Layout.Theme.Gold,
	}, engine)
	anchor:SetAttribute("IsRollAnchor", true)

	engine.PrimaryPart = anchor
end

local function buildDistrict(district: any, parent: Instance)
	local model = Instance.new("Model")
	model.Name = district.Id
	model.Parent = parent

	local centre = positionFor(district.Angle, district.Radius, district.Height)

	if not meshOrPrimitive(district.MeshId, district.PlatformSize, CFrame.new(centre), "DistrictMesh", model) then
		part({
			Name = "Platform",
			Size = district.PlatformSize,
			Position = centre,
			Color = district.Color,
		}, model)

		-- Pillars around the edge, or a gateway pair when Pillars == 2.
		for i = 1, district.Pillars do
			local angle = (i - 1) / math.max(district.Pillars, 1) * math.pi * 2
			if district.Pillars == 2 then
				angle = (i - 1) * math.pi + math.pi / 2
			end
			local offset = Vector3.new(
				math.cos(angle) * (district.PlatformSize.X / 2 - 4),
				district.PillarHeight / 2 + district.PlatformSize.Y / 2,
				math.sin(angle) * (district.PlatformSize.Z / 2 - 4)
			)
			part({
				Name = `Pillar{i}`,
				Size = Vector3.new(4, district.PillarHeight, 4),
				Position = centre + offset,
				Color = district.Color,
			}, model)

			part({
				Name = `PillarGlow{i}`,
				Size = Vector3.new(4.4, 1.2, 4.4),
				Position = centre + offset + Vector3.new(0, district.PillarHeight / 2, 0),
				Color = district.Accent,
				Material = Enum.Material.Neon,
				CanCollide = false,
			}, model)
		end
	end

	-- Every district is labelled, so a tester can name where they are without
	-- being told. Master Spec §20's success criterion depends on it.
	local sign = part({
		Name = "Sign",
		Size = Vector3.new(district.PlatformSize.X * 0.7, 6, 1),
		Position = centre + Vector3.new(0, district.PlatformSize.Y / 2 + 10, 0),
		Transparency = 1,
		CanCollide = false,
	}, model)

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromScale(24, 5)
	gui.AlwaysOnTop = false
	gui.MaxDistance = 320
	gui.Parent = sign

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = district.Name
	label.TextColor3 = district.Accent
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.TextStrokeTransparency = 0.4
	label.Parent = gui

	return centre
end

local function buildBridge(from: Vector3, to: Vector3, parent: Instance)
	local cfg = Layout.Bridges
	local delta = to - from
	local length = delta.Magnitude
	if length < 1 then
		return
	end
	part({
		Name = "Bridge",
		Size = Vector3.new(cfg.Width, cfg.Thickness, length),
		CFrame = CFrame.lookAt(from + delta / 2, to) * CFrame.new(0, 0, 0),
		Color = cfg.Color,
		Material = cfg.Material,
	}, parent)
end

local function buildFloatingIslands(parent: Instance)
	local cfg = Layout.FloatingIslands
	-- Deterministic: every server renders an identical skyline.
	local rng = Random.new(cfg.Seed)
	local folder = Instance.new("Folder")
	folder.Name = "FloatingIslands"
	folder.Parent = parent

	for i = 1, cfg.Count do
		local angle = rng:NextNumber() * math.pi * 2
		local radius = rng:NextNumber(cfg.MinRadius, cfg.MaxRadius)
		local size = rng:NextNumber(cfg.MinSize, cfg.MaxSize)
		part({
			Name = `Island{i}`,
			Size = Vector3.new(size, size * 0.4, size * rng:NextNumber(0.7, 1.3)),
			Position = Vector3.new(
				math.cos(angle) * radius,
				rng:NextNumber(cfg.MinHeight, cfg.MaxHeight),
				math.sin(angle) * radius
			),
			Color = cfg.Color,
			CanCollide = false,
		}, folder)
	end
end

--- Builds the hub if it is not already present. Idempotent: a place that
--- already has a hand-built Crossroads in Workspace is left alone, so
--- authored geometry always wins over generated blockout.
function HubBuilder.build(): Model?
	local existing = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if existing then
		print("[HubBuilder] Crossroads already present in Workspace; leaving it alone")
		return existing :: Model
	end

	applyLighting()

	local hub = Instance.new("Model")
	hub.Name = Constants.NAMES.CROSSROADS

	local centre = part({
		Name = "CentralPlatform",
		Shape = "Part",
		PartShape = Enum.PartType.Cylinder,
		Size = Vector3.new(
			Layout.CentralPlatform.Thickness,
			Layout.CentralPlatform.Radius * 2,
			Layout.CentralPlatform.Radius * 2
		),
		CFrame = CFrame.new(0, -Layout.CentralPlatform.Thickness / 2, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Color = Layout.CentralPlatform.Color,
		Material = Layout.CentralPlatform.Material,
	}, hub)

	buildFateEngine(hub)

	local districts = Instance.new("Folder")
	districts.Name = "Districts"
	districts.Parent = hub

	for _, district in Layout.Districts do
		local districtCentre = buildDistrict(district, districts)
		-- The Observatory is reached from above, not by a ground bridge.
		if district.Height < 30 then
			local inner = Vector3.new(districtCentre.X, district.Height, districtCentre.Z).Unit
				* Layout.CentralPlatform.Radius
			buildBridge(
				Vector3.new(inner.X, district.Height, inner.Z),
				Vector3.new(districtCentre.X, district.Height, districtCentre.Z),
				hub
			)
		end
	end

	buildFloatingIslands(hub)

	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "SpawnLocation"
	spawn.Anchored = true
	spawn.CanCollide = true
	spawn.Size = Vector3.new(12, 1, 12)
	spawn.Position = Layout.SpawnOffset
	spawn.Transparency = 0.6
	spawn.Color = Layout.Theme.Gold
	spawn.Material = Enum.Material.Neon
	spawn.TopSurface = Enum.SurfaceType.Smooth
	-- Spawn faces the Fate Engine: a new player's first frame must contain the
	-- thing the game is about. Master Spec §20.
	spawn.CFrame = CFrame.lookAt(Layout.SpawnOffset, Vector3.new(0, Layout.SpawnOffset.Y, 0))
	spawn.Parent = hub

	hub.PrimaryPart = centre
	hub.Parent = Workspace

	print(`[HubBuilder] built Crossroads with {#Layout.Districts} districts`)
	return hub
end

return HubBuilder
