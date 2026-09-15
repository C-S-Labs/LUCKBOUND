--!strict
-- The Crossroads, described as DATA. Biome Blueprint §2.
--
-- THIS FILE IS THE ART-DIRECTION DIAL. HubBuilder reads it and builds
-- geometry; it holds no art direction of its own. Changing how the hub looks
-- means editing numbers and colours here.
--
-- Positions come from GameConfig.HubLayout.Anchors, not from this file, per
-- blueprint §7.3: the axis mapping is confirmed once in Studio and locked in
-- one place rather than re-derived per script.
--
-- THE MESH SEAM: every swappable piece carries an optional MeshId. While nil
-- the builder generates primitives; set it to an asset id and the builder uses
-- the mesh at the same position, scale and pivot. Authored art replaces
-- blockout one piece at a time, with no flag day.

local GameConfig = require(script.Parent.Parent.Parent.Core.GameConfig)

local Layout = GameConfig.HubLayout

local Theme = {
	-- Blueprint §2.3 verbatim.
	Ambient = Color3.fromRGB(40, 35, 60),
	OutdoorAmbient = Color3.fromRGB(55, 48, 80),
	ColorShiftTop = Color3.fromRGB(90, 70, 140),
	ColorShiftBottom = Color3.fromRGB(30, 25, 50),
	FogColor = Color3.fromRGB(30, 25, 50),
	FogStart = 150,
	FogEnd = 500,
	Brightness = 2,
	ExposureCompensation = 0,
	ClockTime = 22,

	-- Hub materials and accents.
	Marble = Color3.fromRGB(226, 221, 234),
	MarbleTrim = Color3.fromRGB(230, 178, 74), -- AccentGold, matches UITheme
	Plaza = Color3.fromRGB(58, 52, 76),
	Walkway = Color3.fromRGB(78, 70, 98),
	TorchLight = Color3.fromRGB(255, 176, 92),
	EngineSpot = Color3.fromRGB(255, 200, 120), -- blueprint §2.2

	StoneMaterial = Enum.Material.Marble,
	PlazaMaterial = Enum.Material.Slate,
}

local Crossroads = {
	Theme = Theme,
	SpawnOffset = Layout.SpawnAnchor,

	-- Lower plaza ring the raised walkways sit above. Blueprint §2.1.
	Plaza = {
		Diameter = Layout.HubDiameter,
		Thickness = 4,
		Color = Theme.Plaza,
		Material = Theme.PlazaMaterial,
		MeshId = nil,
	},

	-- Centre — Fate Engine. Blueprint §2.2.
	FateEngine = {
		Name = "FateEngine",
		PlatformRadius = 24,
		PlatformRaise = 3,
		PlatformColor = Theme.Marble,
		PlatformMaterial = Enum.Material.Marble,
		RuneInlayCount = 12, -- radial groove pattern
		RuneInlayColor = Color3.fromRGB(124, 245, 224),

		PortalScale = GameConfig.Portal.FateEngineScale,
		-- The Engine cycles a "featured" rarity cosmetically; it is NOT the
		-- roll result and must never be read as a prediction.
		IdleRarity = "UNKNOWN",
		FeaturedCycleSeconds = 14,

		CrystalShards = {
			Count = 6,
			OrbitRadius = 17,
			MinHeight = 8,
			MaxHeight = 21,
			Size = 3.2,
			Material = Enum.Material.Glass,
			SpinSpeedMin = 0.2,
			SpinSpeedMax = 0.7,
		},

		SpotLight = {
			Color = Theme.EngineSpot,
			Brightness = 6,
			Range = 70,
			Angle = 70,
			Height = 46,
		},

		AnchorSize = Vector3.new(14, 1, 14),
		AnchorHeight = 4,
		MeshId = nil, -- ← highest-value place to drop authored art
	},

	-- Zones. Angle is degrees clockwise from north, kept for validation and
	-- for bridge maths; the authoritative position is GameConfig anchors.
	Districts = {
		{
			Id = "HALL_OF_LEGENDS",
			Name = "Hall of Legends",
			Angle = 0,
			Radius = Layout.ZoneRingRadius,
			Kind = "AMPHITHEATRE",
			PlatformSize = Vector3.new(56, 4, 44),
			Height = 2,
			Color = Theme.Marble,
			Accent = Theme.MarbleTrim,
			Pillars = 0,
			PillarHeight = 0,
			-- Blueprint §2.2: 5 initial obelisk slots, TUNABLE, grows over time.
			ObeliskSlots = 5,
			ObeliskHeight = 8,
			TierCount = 3,
			SpotColor = Color3.fromRGB(226, 236, 255), -- cool white, museum-lit
			MeshId = nil,
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Name = "Discovery Archive",
			Angle = 90,
			Radius = Layout.ZoneRingRadius,
			Kind = "ROTUNDA",
			PlatformSize = Vector3.new(26, 4, 26),
			Height = 2,
			Color = Color3.fromRGB(27, 75, 74), -- #1B4B4A deep teal
			Accent = Color3.fromRGB(124, 245, 224), -- #7CF5E0 cosmic trim
			Pillars = 8,
			PillarHeight = 14,
			InteriorDiameter = 20,
			DomeSegments = 5,
			ShelfRings = 3,
			ShelvesPerRing = 6,
			MeshId = nil,
		},
		{
			Id = "EXPEDITION_GATE",
			Name = "Expedition Gate",
			Angle = 180,
			Radius = Layout.ZoneRingRadius,
			Kind = "GATE",
			PlatformSize = Vector3.new(44, 4, 36),
			Height = 0,
			Color = Color3.fromRGB(48, 43, 64),
			Accent = Color3.fromRGB(158, 158, 158),
			Pillars = 6, -- torch pillars flanking the processional
			PillarHeight = 16,
			PortalScale = GameConfig.Portal.ExpeditionGateScale,
			MeshId = nil,
		},
		{
			Id = "TRAINING_GROUNDS",
			Name = "Training Grounds",
			Angle = 270,
			Radius = Layout.ZoneRingRadius,
			Kind = "YARD",
			PlatformSize = Vector3.new(30, 4, 30), -- blueprint §2.2: 30x30
			Height = 2,
			Color = Color3.fromRGB(107, 104, 98), -- #6B6862 neutral stone grey
			Accent = Theme.TorchLight,
			Pillars = 0,
			PillarHeight = 0,
			FenceHeight = 3,
			DummyCount = 3,
			HasBossDummy = true,
			TorchCount = 4,
			MeshId = nil,
		},
		{
			Id = "GLOBAL_OBSERVATORY",
			Name = "Global Observatory",
			Angle = 45,
			Radius = 0, -- directly above centre; reached by the spiral ramp
			Kind = "OBSERVATORY",
			PlatformSize = Vector3.new(36, 3, 36),
			Height = 40, -- blueprint §2.2: +40 studs Y
			PlatformRadius = 18,
			Color = Color3.fromRGB(16, 14, 24), -- near-black, sky reads clearly
			Accent = Color3.fromRGB(124, 245, 224),
			Pillars = 0,
			PillarHeight = 0,
			GlobeDiameter = 12,
			RampTurns = 1.5,
			RampWidth = 6,
			MeshId = nil,
		},
	},

	-- Decorative depth. Deterministic so every server shows one skyline.
	FloatingIslands = {
		Count = 14,
		MinRadius = 190,
		MaxRadius = 420,
		MinHeight = -90,
		MaxHeight = 120,
		MinSize = 14,
		MaxSize = 46,
		Seed = 20260915,
		Color = Color3.fromRGB(42, 37, 58),
		MeshId = nil,
	},

	Bridges = {
		Width = Layout.WalkwayWidth,
		ProcessionalWidth = Layout.ProcessionalWidth,
		Thickness = 2,
		Raise = Layout.WalkwayRaise,
		Color = Theme.Walkway,
		Material = Theme.StoneMaterial,
	},
}

return Crossroads
