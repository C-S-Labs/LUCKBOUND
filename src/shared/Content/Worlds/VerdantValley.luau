--!strict
return {
	Id = "VERDANT_VALLEY",
	Name = "Verdant Valley",
	Rarity = "COMMON",
	RollWeight = 5000,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Biome Blueprint §3.3: soft midday, dappled canopy light.
		AmbientColor = Color3.fromRGB(90, 100, 70),
		OutdoorAmbientColor = Color3.fromRGB(120, 130, 100),
		ColorShiftTop = Color3.fromRGB(150, 170, 120),
		FogColor = Color3.fromRGB(180, 200, 160),
		FogStart = 100,
		FogEnd = 400,
		Brightness = 2.5,
		ClockTime = 13,
	},
	MusicId = nil,
	Enemies = { "MOSS_SLIME", "FOREST_WOLF", "THORN_GOBLIN", "ELDER_TREANT" },
	BossId = "ROOTBOUND_GUARDIAN",
	LootTableId = "LOOT_VERDANT",
	DiscoveryTableId = "DISC_VERDANT",
	Modifiers = { "NORMAL", "NIGHT" },
	-- Blueprint §3.5: modifiers re-tint this world rather than building
	-- separate geometry. This is the reference example every other world's
	-- ModifierOverrides table should follow.
	ModifierOverrides = {
		NIGHT = {
			AmbientColor = Color3.fromRGB(26, 36, 24), -- #1A2418
			FogColor = Color3.fromRGB(40, 52, 44),
			FogEnd = 260,
			Brightness = 0.9,
			ClockTime = 1,
			ParticleId = "FIREFLIES", -- replaces daytime pollen motes
		},
	},
	DurationSeconds = 720,
	RecommendedPower = 1,
	Flavor = "Green and patient. Something old is still growing here.",
}
