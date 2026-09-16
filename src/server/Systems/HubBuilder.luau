--!strict
-- Procedurally generates The Crossroads into Workspace at runtime.
-- Biome Blueprint §2. Build spec T-112.
--
-- Contains NO art direction. Every colour, dimension and material comes from
-- Content/Hub/Crossroads; every position comes from GameConfig.HubLayout.
-- If you find yourself editing this file to change how something LOOKS, the
-- schema is missing a field and that is the bug.
--
-- Zone geometry is dispatched by `Kind`, so adding a sixth zone means adding a
-- data entry and (only if it is a genuinely new shape) one builder function.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Layout = require(Root.Content.Hub.Crossroads)
local PortalRig = require(Root.Util.PortalRig)

local HubBuilder = {}

local Anchors = GameConfig.HubLayout.Anchors

local function part(props: { [string]: any }, parent: Instance): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = props.CanCollide ~= false
	p.Material = props.Material or Layout.Theme.StoneMaterial
	p.Color = props.Color or Layout.Theme.Marble
	p.Size = props.Size or Vector3.one
	p.CFrame = props.CFrame or CFrame.new(props.Position or Vector3.zero)
	p.Name = props.Name or "Part"
	p.Transparency = props.Transparency or 0
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if props.Shape then
		p.Shape = props.Shape
	end
	p.Parent = parent
	return p
end

--- A TRUE cylinder -- `Part.Shape = Cylinder`, never a Part wearing a
--- `CylinderMesh`. Both halves of that distinction cost a playtest:
---
--- 1. **A CylinderMesh is VISUAL ONLY.** The part keeps its block collision
---    hull, so an invisible square corner juts out past every visible round
---    edge and the player is stopped by nothing they can see.
--- 2. **CylinderMesh's axis is Y; PartType.Cylinder's axis is X.** Every
---    caller here passes `(thickness, diameter, diameter)` -- the X
---    convention -- so the mesh version built a diameter-TALL column where a
---    thin disc was wanted. At the old 120-stud scale that was a 120-stud
---    wall; after the 10x rescale the plaza became a 1200-stud wall and the
---    hub had no floor at all. The player spawned on top of it.
---
--- Size keeps the `(thickness, diameter, diameter)` convention; the part is
--- rolled a quarter turn about Z so its local X axis points up.
local function cylinder(props: { [string]: any }, parent: Instance): Part
	local p = part(props, parent)
	p.Shape = Enum.PartType.Cylinder
	p.CFrame = p.CFrame * CFrame.Angles(0, 0, math.pi / 2)
	return p
end

--- Uses an authored mesh when the data supplies one. Returns nil so callers
--- fall through to primitives when it is absent or fails to load.
local function meshOrNil(meshId: string?, size: Vector3, cframe: CFrame, name: string, parent: Instance): BasePart?
	if not meshId then
		return nil
	end
	local p = Instance.new("MeshPart")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Parent = parent
	local ok, err = pcall(function()
		p.MeshId = meshId
	end)
	if not ok then
		warn(`[HubBuilder] mesh {meshId} failed for {name}: {err}; using primitive`)
		p:Destroy()
		return nil
	end
	return p
end

local function label(text: string, color: Color3, size: UDim2, parent: BasePart, maxDistance: number)
	local gui = Instance.new("BillboardGui")
	gui.Size = size
	gui.AlwaysOnTop = false
	gui.MaxDistance = maxDistance
	gui.Parent = parent

	local textLabel = Instance.new("TextLabel")
	textLabel.Size = UDim2.fromScale(1, 1)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = text
	textLabel.TextColor3 = color
	textLabel.TextScaled = true
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextStrokeTransparency = 0.4
	textLabel.Parent = gui
	return gui
end

-- === lighting ========================================================

local function applyLighting()
	local theme = Layout.Theme

	-- Technology is a place setting and is read-only at runtime in a live
	-- server. Attempted here so a fresh Studio place picks it up; set it in
	-- Studio (Lighting.Technology = Future) if this warns.
	pcall(function()
		Lighting.Technology = Enum.Technology.Future
	end)

	Lighting.GlobalShadows = true
	Lighting.Brightness = theme.Brightness
	Lighting.ExposureCompensation = theme.ExposureCompensation
	Lighting.Ambient = theme.Ambient
	Lighting.OutdoorAmbient = theme.OutdoorAmbient
	Lighting.ColorShift_Top = theme.ColorShiftTop
	Lighting.ColorShift_Bottom = theme.ColorShiftBottom
	Lighting.FogColor = theme.FogColor
	Lighting.FogStart = theme.FogStart
	Lighting.FogEnd = theme.FogEnd
	Lighting.ClockTime = theme.ClockTime
	Lighting.EnvironmentDiffuseScale = 1
	Lighting.EnvironmentSpecularScale = 1

	local sky = Lighting:FindFirstChildOfClass("Sky") or Instance.new("Sky")
	sky.StarCount = 3000
	sky.Parent = Lighting

	local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
	atmosphere.Density = 0.3
	atmosphere.Haze = 2
	atmosphere.Color = theme.ColorShiftTop
	atmosphere.Decay = theme.FogColor
	atmosphere.Parent = Lighting

	local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
	bloom.Intensity = 0.7
	bloom.Size = 24
	bloom.Threshold = 0.9
	bloom.Parent = Lighting
end

-- === centre: Fate Engine =============================================

local function buildFateEngine(parent: Instance): Model
	local cfg = Layout.FateEngine
	local base = Anchors.FATE_ENGINE

	local engine = Instance.new("Model")
	engine.Name = Constants.NAMES.FATE_ENGINE
	engine.Parent = parent

	-- Raised marble platform with a radial rune inlay.
	cylinder({
		Name = "Platform",
		Size = Vector3.new(cfg.PlatformRaise, cfg.PlatformRadius * 2, cfg.PlatformRadius * 2),
		Position = base + Vector3.new(0, cfg.PlatformRaise / 2, 0),
		Color = cfg.PlatformColor,
		Material = cfg.PlatformMaterial,
	}, engine)

	local inlay = Instance.new("Folder")
	inlay.Name = "RuneInlay"
	inlay.Parent = engine
	for i = 1, cfg.RuneInlayCount do
		local angle = (i - 1) / cfg.RuneInlayCount * math.pi * 2
		part({
			Name = `Inlay{i}`,
			Size = Vector3.new(0.6, 0.12, cfg.PlatformRadius * 0.85),
			CFrame = CFrame.new(base + Vector3.new(0, cfg.PlatformRaise + 0.02, 0))
				* CFrame.Angles(0, angle, 0)
				* CFrame.new(0, 0, -cfg.PlatformRadius * 0.45),
			Color = cfg.RuneInlayColor,
			Material = Enum.Material.Neon,
			CanCollide = false,
		}, inlay)
	end

	-- The Engine is the shared PortalRig at 1.5x. Blueprint §2.2.
	if not meshOrNil(
		cfg.MeshId,
		Vector3.new(cfg.PlatformRadius, 40, cfg.PlatformRadius),
		CFrame.new(base + Vector3.new(0, 20, 0)),
		"EngineMesh",
		engine
	) then
		PortalRig.build({
			Name = "EngineRig",
			Position = base + Vector3.new(0, cfg.PlatformRaise, 0),
			Scale = cfg.PortalScale,
			Rarity = cfg.IdleRarity,
			PlinthMaterial = Enum.Material.Marble,
			OuterMaterial = Enum.Material.Basalt,
		}, engine)
	end

	-- Six free-floating crystal shards, slow independent rotation.
	local shardCfg = cfg.CrystalShards
	local shards = Instance.new("Folder")
	shards.Name = "CrystalShards"
	shards.Parent = engine

	local shardRng = Random.new(Layout.FloatingIslands.Seed)
	for i = 1, shardCfg.Count do
		local angle = (i - 1) / shardCfg.Count * math.pi * 2
		local height = shardRng:NextNumber(shardCfg.MinHeight, shardCfg.MaxHeight)
		local shard = part({
			Name = `Shard{i}`,
			Size = Vector3.new(shardCfg.Size, shardCfg.Size * 2.4, shardCfg.Size),
			CFrame = CFrame.new(base + Vector3.new(
				math.cos(angle) * shardCfg.OrbitRadius,
				height,
				math.sin(angle) * shardCfg.OrbitRadius
			)) * CFrame.Angles(
				shardRng:NextNumber(-0.4, 0.4),
				shardRng:NextNumber(0, math.pi * 2),
				shardRng:NextNumber(-0.4, 0.4)
			),
			Color = Constants.RARITY[cfg.IdleRarity].Color,
			Material = shardCfg.Material,
			CanCollide = false,
			Transparency = 0.35,
		}, shards)
		shard:SetAttribute("SpinSpeed", shardRng:NextNumber(shardCfg.SpinSpeedMin, shardCfg.SpinSpeedMax))
		shard:SetAttribute("IsFeaturedShard", true)
	end

	-- Warm gold spotlight from above. Blueprint §2.2.
	local spotAnchor = part({
		Name = "SpotAnchor",
		Size = Vector3.new(2, 2, 2),
		Position = base + Vector3.new(0, cfg.SpotLight.Height, 0),
		Transparency = 1,
		CanCollide = false,
	}, engine)

	local spot = Instance.new("SpotLight")
	spot.Color = cfg.SpotLight.Color
	spot.Brightness = cfg.SpotLight.Brightness
	spot.Range = cfg.SpotLight.Range
	spot.Angle = cfg.SpotLight.Angle
	spot.Face = Enum.NormalId.Bottom
	spot.Parent = spotAnchor

	-- The part the server measures roll distance from. FateSystem depends on
	-- this name, so it exists whether or not a mesh replaced the rig.
	local anchor = part({
		Name = Constants.NAMES.ROLL_ANCHOR,
		Size = cfg.AnchorSize,
		Position = base + Vector3.new(0, cfg.AnchorHeight, 0),
		Transparency = 1,
		CanCollide = false,
	}, engine)
	anchor:SetAttribute("IsRollAnchor", true)

	-- ProximityPrompt over a bespoke keybind: blueprint §2.2 calls it the
	-- clearer mobile affordance, and it handles keyboard, gamepad and touch
	-- natively. The client listens for Triggered; the server still validates
	-- distance and cooldown independently (build spec §3.4).
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "RollPrompt"
	prompt.ActionText = "ROLL"
	prompt.ObjectText = "Fate Engine"
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = anchor

	engine.PrimaryPart = anchor
	return engine
end

-- === zone builders, dispatched by Kind ===============================

local function buildPlatform(zone: any, centre: Vector3, parent: Instance)
	if meshOrNil(zone.MeshId, zone.PlatformSize, CFrame.new(centre), "ZoneMesh", parent) then
		return
	end

	-- A ROUND zone gets a disc, not a box. The Observatory previously got
	-- BOTH -- a box from here and a cylinder from its own builder, one buried
	-- inside the other -- because the shape was implied by which builder ran
	-- rather than declared in the data.
	if zone.PlatformShape == "ROUND" then
		cylinder({
			Name = "Platform",
			Size = Vector3.new(
				zone.PlatformSize.Y,
				zone.PlatformRadius * 2,
				zone.PlatformRadius * 2
			),
			Position = centre,
			Color = zone.Color,
			Material = zone.PlatformMaterial,
		}, parent)
		return
	end

	part({
		Name = "Platform",
		Size = zone.PlatformSize,
		Position = centre,
		Color = zone.Color,
	}, parent)
end

local function buildAmphitheatre(zone: any, centre: Vector3, parent: Instance)
	-- Semicircular tiered seating facing a row of obelisks. Blueprint §2.2.
	for tier = 1, zone.TierCount do
		local radius = 16 + tier * 6
		local segments = 14
		for i = 0, segments do
			-- Half-circle only: seating faces the obelisk row.
			local angle = math.pi + (i / segments) * math.pi
			part({
				Name = `Tier{tier}_Seat{i}`,
				Size = Vector3.new(5, 1.6, 4),
				CFrame = CFrame.new(centre + Vector3.new(
					math.cos(angle) * radius,
					zone.PlatformSize.Y / 2 + tier * 1.6,
					math.sin(angle) * radius
				)) * CFrame.Angles(0, -angle, 0),
				Color = zone.Color,
				Material = Enum.Material.Marble,
			}, parent)
		end
	end

	local obelisks = Instance.new("Folder")
	obelisks.Name = "Obelisks"
	obelisks.Parent = parent

	for slot = 1, zone.ObeliskSlots do
		local offset = (slot - (zone.ObeliskSlots + 1) / 2) * 9
		local obelisk = part({
			Name = `Obelisk{slot}`,
			Size = Vector3.new(3, zone.ObeliskHeight, 3),
			Position = centre + Vector3.new(offset, zone.PlatformSize.Y / 2 + zone.ObeliskHeight / 2, -6),
			Color = zone.Color,
			Material = Enum.Material.Marble,
		}, obelisks)
		obelisk:SetAttribute("WorldFirstSlot", slot)

		part({
			Name = `ObeliskCap{slot}`,
			Size = Vector3.new(3.4, 0.6, 3.4),
			Position = obelisk.Position + Vector3.new(0, zone.ObeliskHeight / 2, 0),
			Color = zone.Accent,
			Material = Enum.Material.Neon,
			CanCollide = false,
		}, obelisks)

		-- Empty until a World First is claimed (Master Spec §13).
		label("—", zone.Accent, UDim2.fromScale(6, 2), obelisk, 180)

		-- Cool white, so legends read as museum pieces against warm ambient.
		local spot = Instance.new("SpotLight")
		spot.Color = zone.SpotColor
		spot.Brightness = 3
		spot.Range = 28
		spot.Angle = 45
		spot.Face = Enum.NormalId.Top
		spot.Parent = obelisk
	end
end

local function buildRotunda(zone: any, centre: Vector3, parent: Instance)
	local radius = zone.InteriorDiameter / 2
	local top = centre.Y + zone.PlatformSize.Y / 2

	for i = 1, zone.Pillars do
		local angle = (i - 1) / zone.Pillars * math.pi * 2
		part({
			Name = `Column{i}`,
			Size = Vector3.new(2.4, zone.PillarHeight, 2.4),
			Position = Vector3.new(
				centre.X + math.cos(angle) * radius,
				top + zone.PillarHeight / 2,
				centre.Z + math.sin(angle) * radius
			),
			Color = zone.Color,
		}, parent)
	end

	-- Stepped dome: each ring narrower and higher than the last.
	for segment = 1, zone.DomeSegments do
		local t = segment / zone.DomeSegments
		cylinder({
			Name = `Dome{segment}`,
			Size = Vector3.new(1.4, radius * 2 * (1 - t * 0.85), radius * 2 * (1 - t * 0.85)),
			Position = Vector3.new(centre.X, top + zone.PillarHeight + segment * 1.6, centre.Z),
			Color = zone.Color,
			CanCollide = false,
		}, parent)
	end

	-- Floating bookshelves: rings orbiting at different heights, cosmetic.
	local shelves = Instance.new("Folder")
	shelves.Name = "FloatingShelves"
	shelves.Parent = parent

	for ring = 1, zone.ShelfRings do
		local ringRadius = radius * (0.35 + ring * 0.18)
		local height = top + 3 + ring * 3.5
		for i = 1, zone.ShelvesPerRing do
			local angle = (i - 1) / zone.ShelvesPerRing * math.pi * 2
			local shelf = part({
				Name = `Shelf_R{ring}_{i}`,
				Size = Vector3.new(3.6, 0.5, 1.4),
				CFrame = CFrame.new(
					centre.X + math.cos(angle) * ringRadius,
					height,
					centre.Z + math.sin(angle) * ringRadius
				) * CFrame.Angles(0, -angle, 0),
				Color = zone.Accent,
				Material = Enum.Material.Neon,
				CanCollide = false,
				Transparency = 0.25,
			}, shelves)
			shelf:SetAttribute("OrbitRadius", ringRadius)
			shelf:SetAttribute("OrbitSpeed", 0.08 + ring * 0.04)
			shelf:SetAttribute("OrbitHeight", height)
			-- The client orbits these; it must not have to re-derive the
			-- zone centre from the layout.
			shelf:SetAttribute("OrbitCentre", Vector3.new(centre.X, height, centre.Z))
		end
	end

	local podium = part({
		Name = "Podium",
		Size = Vector3.new(3, 4, 3),
		Position = Vector3.new(centre.X, top + 2, centre.Z),
		Color = zone.Accent,
		Material = Enum.Material.Neon,
	}, parent)

	-- Phase 2 opens the Discovery Book here; the affordance exists now so the
	-- zone reads as interactive rather than decorative.
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "ArchivePrompt"
	prompt.ActionText = "Open Discovery Book"
	prompt.ObjectText = "Discovery Archive"
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Enabled = false -- Phase 2
	prompt.Parent = podium
end

local function buildGate(zone: any, centre: Vector3, parent: Instance)
	local top = centre + Vector3.new(0, zone.PlatformSize.Y / 2, 0)

	-- The largest portal in the hub. Blueprint §2.2.
	PortalRig.build({
		Name = "GateRig",
		Position = top,
		Scale = zone.PortalScale,
		Rarity = "COMMON",
		PlinthMaterial = Enum.Material.Marble,
		OuterMaterial = Enum.Material.CorrodedMetal,
	}, parent)

	-- The part the ENTER prompt lives on, and the part the server measures
	-- entry distance from. Exactly the RollAnchor pattern from the Fate
	-- Engine, and for the same two reasons.
	--
	-- A ProximityPrompt measures from its parent part's ORIGIN. Hanging the
	-- prompt on the plinth meant measuring from the plinth's centre, and the
	-- plinth is wider than the prompt's reach -- so a player standing on it
	-- was already out of range. An anchor decouples "where the prompt is"
	-- from "how big the art is", which is what lets the rig be rebuilt in
	-- Blender at any size without breaking entry.
	local anchor = part({
		Name = Constants.NAMES.GATE_ANCHOR,
		Size = Vector3.new(
			zone.PortalScale * GameConfig.HubLayout.GateAnchorSpan,
			1,
			zone.PortalScale * GameConfig.HubLayout.GateAnchorSpan
		),
		Position = top
			+ Vector3.new(0, GameConfig.Portal.MaxPlinthHeight + GameConfig.HubLayout.GateAnchorLift, 0),
		Transparency = 1,
		CanCollide = false,
	}, parent)
	anchor:SetAttribute("IsGateAnchor", true)

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "EnterPrompt"
	prompt.ActionText = "ENTER"
	prompt.ObjectText = "Expedition Gate"
	prompt.HoldDuration = 0.5
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Enabled = GameConfig.Expedition.Enabled
	prompt.Parent = anchor

	-- Processional walkway with flanking torch pillars: deliberately the most
	-- dramatic sightline in the hub, visible from the Fate Engine.
	local torches = Instance.new("Folder")
	torches.Name = "TorchPillars"
	torches.Parent = parent

	local perSide = math.max(1, math.floor(zone.Pillars / 2))
	for side = -1, 1, 2 do
		for i = 1, perSide do
			local z = centre.Z - i * 11
			local pillar = part({
				Name = `Torch_{side}_{i}`,
				Size = Vector3.new(2.4, zone.PillarHeight, 2.4),
				Position = Vector3.new(
					centre.X + side * (GameConfig.HubLayout.ProcessionalWidth / 2 + 3),
					centre.Y + zone.PillarHeight / 2,
					z
				),
				Color = zone.Color,
			}, torches)

			local flame = part({
				Name = "Flame",
				Size = Vector3.new(1.6, 1.6, 1.6),
				Position = pillar.Position + Vector3.new(0, zone.PillarHeight / 2 + 0.8, 0),
				Color = Layout.Theme.TorchLight,
				Material = Enum.Material.Neon,
				CanCollide = false,
			}, torches)

			local flameLight = Instance.new("PointLight")
			flameLight.Color = Layout.Theme.TorchLight
			flameLight.Brightness = 2
			flameLight.Range = 22
			flameLight.Parent = flame
		end
	end
end

local function buildYard(zone: any, centre: Vector3, parent: Instance)
	local half = zone.PlatformSize.X / 2
	local top = centre.Y + zone.PlatformSize.Y / 2

	-- Low fencing, no roof: visibly the practical zone, not a mystical one.
	for side = 1, 4 do
		local angle = (side - 1) * math.pi / 2
		part({
			Name = `Fence{side}`,
			Size = Vector3.new(zone.PlatformSize.X, zone.FenceHeight, 0.6),
			CFrame = CFrame.new(centre + Vector3.new(0, top - centre.Y + zone.FenceHeight / 2, 0))
				* CFrame.Angles(0, angle, 0)
				* CFrame.new(0, 0, -half),
			Color = zone.Color,
		}, parent)
	end

	-- Static dummy rigs only. Blueprint §2.2 wants them to respond to attack
	-- input, but combat is explicitly excluded from Phase 1 (build spec §7),
	-- so these are geometry and an attribute for Phase 2 to find. No combat
	-- behaviour is attached here.
	local dummies = Instance.new("Folder")
	dummies.Name = "TargetDummies"
	dummies.Parent = parent

	for i = 1, zone.DummyCount do
		local offset = (i - (zone.DummyCount + 1) / 2) * 7
		local dummy = part({
			Name = `TargetDummy{i}`,
			Size = Vector3.new(2.4, 6, 2.4),
			Position = centre + Vector3.new(offset, top - centre.Y + 3, -half + 6),
			Color = Color3.fromRGB(150, 128, 96),
			Material = Enum.Material.WoodPlanks,
		}, dummies)
		dummy:SetAttribute("IsTrainingDummy", true)
		dummy:SetAttribute("Phase", 2)
	end

	if zone.HasBossDummy then
		local boss = part({
			Name = "BossDummy",
			Size = Vector3.new(5, 10, 5),
			Position = centre + Vector3.new(0, top - centre.Y + 5, half - 7),
			Color = Color3.fromRGB(96, 84, 70),
			Material = Enum.Material.WoodPlanks,
		}, dummies)
		boss:SetAttribute("IsTrainingDummy", true)
		boss:SetAttribute("IsBossDummy", true)
		boss:SetAttribute("Phase", 2)
		label("Practice Target", zone.Accent, UDim2.fromScale(10, 2), boss, 140)
	end

	for i = 1, zone.TorchCount do
		local angle = (i - 1) / zone.TorchCount * math.pi * 2
		local torch = part({
			Name = `PracticeTorch{i}`,
			Size = Vector3.new(1, 4, 1),
			Position = centre + Vector3.new(
				math.cos(angle) * (half - 2),
				top - centre.Y + 2,
				math.sin(angle) * (half - 2)
			),
			Color = zone.Color,
		}, parent)

		local light = Instance.new("PointLight")
		light.Color = Layout.Theme.TorchLight
		light.Brightness = 1.6
		light.Range = 18
		light.Parent = torch
	end
end

--- The way up to the Observatory.
---
--- IT NO LONGER SPIRALS AROUND THE FATE ENGINE. The previous version ran a
--- 2.5-turn helix at radius 118, forty studs wide, so it occupied radius
--- 98-138 -- and the Engine's own platform is radius 120. It wrapped the
--- single most important object in the game in a wall of steps and blocked
--- the walk up to it. The first Studio playtest reported exactly that.
---
--- This is one straight processional on the Observatory's OWN bearing: 45
--- degrees, the empty diagonal between the Hall and the Archive. It crosses
--- no walkway, because those run at 0/90/180/270. It passes over the Engine
--- platform only in its final few studs, by which point it is 137 studs up
--- and clear of the rig's 111-stud crown.
local function buildObservatoryApproach(zone: any, centre: Vector3, parent: Instance)
	local cfg = zone.Approach

	-- District Angle is degrees clockwise from north, and north is -Z.
	local bearing = math.rad(zone.Angle)
	local dir = Vector3.new(math.sin(bearing), 0, -math.cos(bearing))

	-- The plaza's top face: it is centred at -Thickness/2, so its surface is
	-- y = 0 by construction. Derived rather than written as 0, so moving the
	-- plaza moves the stair with it.
	local plazaTop = -Layout.Plaza.Thickness / 2 + Layout.Plaza.Thickness / 2
	local deckTop = centre.Y + zone.PlatformSize.Y / 2

	-- Both ends drop by half the deck thickness, so the WALKING SURFACE meets
	-- the plaza and the Observatory floor -- not the part's centre line.
	local sink = Vector3.new(0, cfg.Thickness / 2, 0)
	local bottom = dir * cfg.StartRadius + Vector3.new(0, plazaTop, 0) - sink
	local top = dir * cfg.EndRadius + Vector3.new(0, deckTop, 0) - sink

	local delta = top - bottom
	local length = delta.Magnitude

	local approach = Instance.new("Folder")
	approach.Name = "Approach"
	approach.Parent = parent

	local deck = part({
		Name = "Deck",
		Size = Vector3.new(cfg.Width, cfg.Thickness, length),
		CFrame = CFrame.lookAt(bottom + delta / 2, top),
		Color = zone.Color,
		Material = Enum.Material.Slate,
	}, approach)

	-- Balustrades. Non-colliding on purpose: they exist so the drop reads as a
	-- drop, and a decorative rail must never become the reason a player cannot
	-- get onto their own staircase.
	for side = -1, 1, 2 do
		part({
			Name = `Rail{side}`,
			Size = Vector3.new(cfg.RailThickness, cfg.RailHeight, length),
			CFrame = deck.CFrame
				* CFrame.new(side * (cfg.Width / 2), cfg.RailHeight / 2, 0),
			Color = zone.Accent,
			Material = Enum.Material.Marble,
			CanCollide = false,
			Transparency = 0.35,
		}, approach)
	end

	-- Piers, so 145 studs of stair does not appear to float. Also
	-- non-colliding: they are under the deck and nothing should catch on them.
	for i = 1, cfg.PierCount do
		local t = i / (cfg.PierCount + 1)
		local at = bottom + delta * t
		local height = at.Y - plazaTop
		if height > 1 then
			part({
				Name = `Pier{i}`,
				Size = Vector3.new(cfg.PierWidth, height, cfg.PierWidth),
				Position = Vector3.new(at.X, plazaTop + height / 2, at.Z),
				Color = zone.Color,
				Material = Enum.Material.Slate,
				CanCollide = false,
			}, approach)
		end
	end
end

local function buildObservatory(zone: any, centre: Vector3, parent: Instance)
	-- The deck itself is built by buildPlatform, which reads PlatformShape.

	-- Translucent orrery representing the server. Fatebreaks flare this.
	local globe = part({
		Name = "Orrery",
		Shape = Enum.PartType.Ball,
		Size = Vector3.new(zone.GlobeDiameter, zone.GlobeDiameter, zone.GlobeDiameter),
		Position = centre + Vector3.new(0, zone.GlobeDiameter / 2 + 3, 0),
		Color = zone.Accent,
		Material = Enum.Material.Glass,
		Transparency = 0.55,
		CanCollide = false,
	}, parent)
	globe:SetAttribute("IsOrrery", true)
	globe:SetAttribute("SpinSpeed", 0.12)

	local core = Instance.new("PointLight")
	core.Color = zone.Accent
	core.Brightness = 3
	core.Range = 40
	core.Parent = globe

	buildObservatoryApproach(zone, centre, parent)
end

local ZONE_BUILDERS: { [string]: (any, Vector3, Instance) -> () } = {
	AMPHITHEATRE = buildAmphitheatre,
	ROTUNDA = buildRotunda,
	GATE = buildGate,
	YARD = buildYard,
	OBSERVATORY = buildObservatory,
}

-- === assembly ========================================================

local function buildWalkway(zone: any, centre: Vector3, parent: Instance)
	local bridges = Layout.Bridges
	local flat = Vector3.new(centre.X, 0, centre.Z)
	if flat.Magnitude < 1 then
		return -- Observatory sits above centre; the ramp serves it instead.
	end

	local dir = flat.Unit

	-- HALF-EXTENT ALONG THE APPROACH, not always X. Hall of Legends is
	-- 360x280 and is approached down -Z, so its near edge is 140 studs out,
	-- not 180 -- using X left a 40-stud hole in the floor between the walkway
	-- and the platform. The Expedition Gate had a 30-stud one for the same
	-- reason. Projecting the platform's extents onto the approach direction
	-- gets it right for every zone, including any future diagonal.
	local half = math.abs(dir.X) * zone.PlatformSize.X / 2
		+ math.abs(dir.Z) * zone.PlatformSize.Z / 2

	-- Walkway tops must MEET the surfaces they join, or every trip ends in a
	-- step the player has to jump. Both ends are computed from the top face of
	-- what they land on, and the deck is sloped between them.
	local engineTop = Layout.FateEngine.PlatformRaise
	local zoneTop = centre.Y + zone.PlatformSize.Y / 2
	local deck = bridges.Thickness / 2

	-- Overlap both ends slightly so there is no hairline seam to catch on.
	local inner = dir * (Layout.FateEngine.PlatformRadius - bridges.Overlap)
	local outer = flat - dir * (half - bridges.Overlap)
	inner = Vector3.new(inner.X, engineTop - deck, inner.Z)
	outer = Vector3.new(outer.X, zoneTop - deck, outer.Z)

	local delta = outer - inner
	local length = delta.Magnitude
	if length < 1 then
		return
	end

	local width = if zone.Kind == "GATE" then bridges.ProcessionalWidth else bridges.Width

	part({
		Name = `Walkway_{zone.Id}`,
		Size = Vector3.new(width, bridges.Thickness, length),
		CFrame = CFrame.lookAt(inner + delta / 2, outer),
		Color = bridges.Color,
		Material = bridges.Material,
	}, parent)
end

local function buildFloatingIslands(parent: Instance)
	local cfg = Layout.FloatingIslands
	local rng = Random.new(cfg.Seed) -- deterministic: one skyline per server
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

--- Builds the hub if absent. Idempotent: a place that already contains a
--- hand-built Crossroads is left alone, so authored geometry always wins.
function HubBuilder.build(): Model
	local existing = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if existing then
		print("[HubBuilder] Crossroads already in Workspace; leaving it alone")
		return existing :: Model
	end

	applyLighting()

	local hub = Instance.new("Model")
	hub.Name = Constants.NAMES.CROSSROADS

	-- Lower plaza ring the raised walkways sit above.
	cylinder({
		Name = "Plaza",
		Size = Vector3.new(Layout.Plaza.Thickness, Layout.Plaza.Diameter, Layout.Plaza.Diameter),
		Position = Vector3.new(0, -Layout.Plaza.Thickness / 2, 0),
		Color = Layout.Plaza.Color,
		Material = Layout.Plaza.Material,
	}, hub)

	buildFateEngine(hub)

	local zones = Instance.new("Folder")
	zones.Name = "Zones"
	zones.Parent = hub

	for _, zone in Layout.Districts do
		local anchor = Anchors[zone.Id]
		assert(anchor, `HubLayout.Anchors is missing an entry for zone '{zone.Id}'`)
		local centre = anchor + Vector3.new(0, zone.Height, 0)

		local model = Instance.new("Model")
		model.Name = zone.Id
		model.Parent = zones

		buildPlatform(zone, centre, model)

		local builder = ZONE_BUILDERS[zone.Kind]
		assert(builder, `no builder for zone Kind '{zone.Kind}' (zone {zone.Id})`)
		builder(zone, centre, model)

		local sign = part({
			Name = "Sign",
			Size = Vector3.new(4, 1, 1),
			Position = centre + Vector3.new(0, zone.PlatformSize.Y / 2 + 12, 0),
			Transparency = 1,
			CanCollide = false,
		}, model)
		-- Every zone is labelled so a tester can name where they are without
		-- being told. Master Spec §20's success criterion depends on it.
		label(zone.Name, zone.Accent, UDim2.fromScale(24, 5), sign, 320)

		buildWalkway(zone, centre, hub)
	end

	buildFloatingIslands(hub)

	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "SpawnLocation"
	spawn.Anchored = true
	spawn.Size = Vector3.new(12, 1, 12)
	spawn.Transparency = 0.6
	spawn.Color = Layout.Theme.MarbleTrim
	spawn.Material = Enum.Material.Neon
	spawn.TopSurface = Enum.SurfaceType.Smooth
	-- Spawn faces the Fate Engine: a new player's first frame must contain the
	-- thing the game is about.
	spawn.CFrame = CFrame.lookAt(
		Layout.SpawnOffset,
		Vector3.new(0, Layout.SpawnOffset.Y, 0)
	)
	spawn.Parent = hub

	hub.Parent = Workspace
	print(`[HubBuilder] built Crossroads: {#Layout.Districts} zones, {#hub:GetDescendants()} instances`)
	return hub
end

return HubBuilder
