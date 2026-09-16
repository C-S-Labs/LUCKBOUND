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
	-- Fog must reach past the distant islands or the world looks boxed in --
	-- the blueprint's 150/500 was sized to a 120-stud hub.
	FogStart = 700,
	FogEnd = 4400,
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
		Thickness = 14,
		Color = Theme.Plaza,
		Material = Theme.PlazaMaterial,
		MeshId = nil,
	},

	-- Centre — Fate Engine. Blueprint §2.2.
	FateEngine = {
		Name = "FateEngine",
		-- 140 -> 120 with the rest of the de-scale. Must stay larger than the
		-- Engine's outer ring (OuterRingRadius * FateEngineScale = 54) or the
		-- rig overhangs the floor it stands on -- asserted by test.
		PlatformRadius = 120,
		PlatformRaise = 10,
		PlatformColor = Theme.Marble,
		PlatformMaterial = Enum.Material.Marble,
		RuneInlayCount = 16, -- radial groove pattern
		RuneInlayColor = Color3.fromRGB(124, 245, 224),

		PortalScale = GameConfig.Portal.FateEngineScale,
		-- The Engine cycles a "featured" rarity cosmetically; it is NOT the
		-- roll result and must never be read as a prediction.
		IdleRarity = "UNKNOWN",
		FeaturedCycleSeconds = 14,

		CrystalShards = {
			Count = 6,
			OrbitRadius = 100,
			MinHeight = 50,
			MaxHeight = 140,
			Size = 20,
			Material = Enum.Material.Glass,
			SpinSpeedMin = 0.2,
			SpinSpeedMax = 0.7,
		},

		SpotLight = {
			Color = Theme.EngineSpot,
			Brightness = 8,
			Range = 400,
			Angle = 80,
			Height = 300,
		},

		AnchorSize = Vector3.new(90, 1, 90),
		AnchorHeight = 12,
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
			PlatformSize = Vector3.new(320, 14, 250),
			Height = 8,
			Color = Theme.Marble,
			Accent = Theme.MarbleTrim,
			Pillars = 0,
			PillarHeight = 0,
			-- Blueprint §2.2: 5 initial obelisk slots, TUNABLE, grows over time.
			ObeliskSlots = 5,
			ObeliskHeight = 56,
			TierCount = 5,
			SpotColor = Color3.fromRGB(226, 236, 255), -- cool white, museum-lit
			MeshId = nil,
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Name = "Discovery Archive",
			Angle = 90,
			Radius = Layout.ZoneRingRadius,
			Kind = "ROTUNDA",
			PlatformSize = Vector3.new(210, 14, 210),
			Height = 8,
			Color = Color3.fromRGB(27, 75, 74), -- #1B4B4A deep teal
			Accent = Color3.fromRGB(124, 245, 224), -- #7CF5E0 cosmic trim
			Pillars = 8,
			PillarHeight = 95,
			InteriorDiameter = 155,
			DomeSegments = 7,
			ShelfRings = 4,
			ShelvesPerRing = 10,
			MeshId = nil,
		},
		{
			Id = "EXPEDITION_GATE",
			Name = "Expedition Gate",
			Angle = 180,
			Radius = Layout.ZoneRingRadius,
			Kind = "GATE",
			PlatformSize = Vector3.new(290, 14, 240),
			Height = 0,
			Color = Color3.fromRGB(48, 43, 64),
			Accent = Color3.fromRGB(158, 158, 158),
			Pillars = 6, -- torch pillars flanking the processional
			PillarHeight = 110,
			PortalScale = GameConfig.Portal.ExpeditionGateScale,
			MeshId = nil,
		},
		{
			Id = "TRAINING_GROUNDS",
			Name = "Training Grounds",
			Angle = 270,
			Radius = Layout.ZoneRingRadius,
			Kind = "YARD",
			PlatformSize = Vector3.new(235, 14, 235), -- blueprint §2.2: 30x30
			Height = 8,
			Color = Color3.fromRGB(107, 104, 98), -- #6B6862 neutral stone grey
			Accent = Theme.TorchLight,
			Pillars = 0,
			PillarHeight = 0,
			FenceHeight = 14,
			DummyCount = 3,
			HasBossDummy = true,
			TorchCount = 8,
			MeshId = nil,
		},
		{
			Id = "GLOBAL_OBSERVATORY",
			Name = "Global Observatory",
			Angle = 45,
			Radius = 0, -- directly above centre; reached by the spiral ramp
			Kind = "OBSERVATORY",
			PlatformSize = Vector3.new(240, 10, 240),
			Height = 140, -- blueprint §2.2: +40 studs Y
			PlatformRadius = 110,
			Color = Color3.fromRGB(16, 14, 24), -- near-black, sky reads clearly
			Accent = Color3.fromRGB(124, 245, 224),
			Pillars = 0,
			PillarHeight = 0,
			GlobeDiameter = 80,
			RampTurns = 2.5,
			RampWidth = 40,
			MeshId = nil,
		},
	},

	-- Decorative depth. Deterministic so every server shows one skyline.
	-- Non-walkable scenery. These extend to GameConfig.HubLayout.VisualExtent,
	-- far beyond the 1200-stud playable footprint: the world reads as several
	-- thousand studs across while every walk stays short.
	FloatingIslands = {
		Count = 40,
		MinRadius = 900,
		MaxRadius = 4000,
		MinHeight = -700,
		MaxHeight = 900,
		MinSize = 90,
		MaxSize = 420,
		Seed = 20260915,
		Color = Color3.fromRGB(42, 37, 58),
		MeshId = nil,
	},

	Bridges = {
		Width = Layout.WalkwayWidth,
		ProcessionalWidth = Layout.ProcessionalWidth,
		Thickness = 8,
		Raise = Layout.WalkwayRaise,
		-- Walkways run a little INTO the surfaces they join at both ends.
		-- Butting them edge to edge leaves a hairline seam that a character
		-- can catch on, and any float error turns it into a hole.
		Overlap = 10,
		Color = Theme.Walkway,
		Material = Theme.StoneMaterial,
	},
}

return Crossroads
