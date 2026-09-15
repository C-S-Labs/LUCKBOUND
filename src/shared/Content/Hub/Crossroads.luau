--!strict
-- The Crossroads hub, described as DATA. Master Spec §3.
--
-- THIS FILE IS THE ART DIRECTION DIAL.
-- HubBuilder reads it and builds geometry. Changing how the hub looks means
-- editing numbers and colours here -- never touching HubBuilder. That is the
-- prime directive applied to the hub: systems reusable, content data.
--
-- THE MESH SEAM
-- Every district and prop carries an optional `MeshId`. While it is nil the
-- builder generates primitive geometry. Set it to a Roblox asset id and the
-- builder uses the mesh instead, keeping the same position, scale and pivot.
-- So commissioned or Blender-authored art drops in one line at a time, with no
-- rewrite and no flag day -- you can replace the Fate Engine alone and leave
-- everything else as blockout.

local Theme = {
	-- Master Spec §3: "deep blue/purple sky, warm gold lighting, floating
	-- islands, runes, crystals, particles, and a monumental Fate Engine."
	SkyTop = Color3.fromHex("1B1740"),
	SkyHorizon = Color3.fromHex("3D2E6B"),
	Ambient = Color3.fromHex("4A3F7A"),
	OutdoorAmbient = Color3.fromHex("2E2652"),
	SunColor = Color3.fromHex("F5C97B"), -- warm gold
	FogColor = Color3.fromHex("2A2350"),
	FogStart = 180,
	FogEnd = 1100,
	ClockTime = 20.5, -- dusk

	Stone = Color3.fromHex("5B5470"),
	StoneDark = Color3.fromHex("3A3550"),
	StoneLight = Color3.fromHex("7E7699"),
	Gold = Color3.fromHex("D9A441"),
	Rune = Color3.fromHex("8FD4FF"),
	Crystal = Color3.fromHex("A97BE8"),

	StoneMaterial = Enum.Material.Slate,
	AccentMaterial = Enum.Material.Neon,
}

-- Districts sit on the compass points named in Master Spec §3. Angle is
-- degrees clockwise from north; the builder converts to a position.
local DISTRICT_RADIUS = 120

local Crossroads = {
	Theme = Theme,

	SpawnOffset = Vector3.new(0, 4, 46), -- south of centre, facing the Engine

	CentralPlatform = {
		Radius = 62,
		Thickness = 8,
		Color = Theme.Stone,
		Material = Theme.StoneMaterial,
		MeshId = nil,
	},

	FateEngine = {
		Name = "FateEngine",
		Position = Vector3.new(0, 0, 0),
		BaseRadius = 16,
		Height = 54,
		RingCount = 3,
		RingThickness = 2.2,
		CoreSize = 11,
		CoreColor = Theme.Crystal,
		RingColor = Theme.Gold,
		RuneColor = Theme.Rune,
		SpinSpeeds = { 0.25, -0.4, 0.62 }, -- rad/s per ring, alternating
		-- The part the server measures roll distance from. Must exist.
		AnchorSize = Vector3.new(14, 1, 14),
		AnchorHeight = 4,
		MeshId = nil, -- ← the single highest-value place to drop real art
	},

	Districts = {
		{
			Id = "HALL_OF_LEGENDS",
			Name = "Hall of Legends",
			Angle = 0, -- north
			Radius = DISTRICT_RADIUS,
			PlatformSize = Vector3.new(56, 6, 44),
			Height = 6,
			Color = Theme.StoneLight,
			Accent = Theme.Gold,
			Pillars = 6,
			PillarHeight = 26,
			MeshId = nil,
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Name = "Discovery Archive",
			Angle = 90, -- east
			Radius = DISTRICT_RADIUS,
			PlatformSize = Vector3.new(48, 6, 48),
			Height = 2,
			Color = Theme.Stone,
			Accent = Theme.Rune,
			Pillars = 4,
			PillarHeight = 18,
			MeshId = nil,
		},
		{
			Id = "EXPEDITION_GATE",
			Name = "Expedition Gate",
			Angle = 180, -- south
			Radius = DISTRICT_RADIUS,
			PlatformSize = Vector3.new(52, 6, 40),
			Height = 0,
			Color = Theme.StoneDark,
			Accent = Theme.Crystal,
			Pillars = 2,
			PillarHeight = 34, -- a gateway, not a colonnade
			MeshId = nil,
		},
		{
			Id = "TRAINING_GROUNDS",
			Name = "Training Grounds",
			Angle = 270, -- west
			Radius = DISTRICT_RADIUS,
			PlatformSize = Vector3.new(58, 6, 58),
			Height = -2,
			Color = Theme.Stone,
			Accent = Theme.Gold,
			Pillars = 0,
			PillarHeight = 0,
			MeshId = nil,
		},
		{
			Id = "GLOBAL_OBSERVATORY",
			Name = "Global Observatory",
			Angle = 45,
			Radius = 74,
			PlatformSize = Vector3.new(40, 5, 40),
			Height = 58, -- Master Spec §3: "upper platform"
			Color = Theme.StoneLight,
			Accent = Theme.Rune,
			Pillars = 8,
			PillarHeight = 14,
			MeshId = nil,
		},
	},

	-- Floating islands scattered around the hub for depth. Purely decorative,
	-- deterministic so every server looks identical.
	FloatingIslands = {
		Count = 14,
		MinRadius = 190,
		MaxRadius = 420,
		MinHeight = -90,
		MaxHeight = 120,
		MinSize = 14,
		MaxSize = 46,
		Seed = 20260915,
		Color = Theme.StoneDark,
		MeshId = nil,
	},

	Bridges = {
		Width = 10,
		Thickness = 2,
		Color = Theme.Stone,
		Material = Theme.StoneMaterial,
	},
}

return Crossroads
