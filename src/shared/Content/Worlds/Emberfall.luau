--!strict
return {
	Id = "EMBERFALL",
	Name = "Emberfall",
	Rarity = "RARE",
	RollWeight = 700,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Biome Blueprint §4.3: darker than Verdant Valley -- lava provides
		-- localised light instead of even ambient. Tighter, ash-haze fog.
		AmbientColor = Color3.fromRGB(60, 30, 25),
		OutdoorAmbientColor = Color3.fromRGB(70, 36, 28),
		ColorShiftTop = Color3.fromRGB(120, 50, 30),
		FogColor = Color3.fromRGB(50, 20, 15),
		FogStart = 60,
		FogEnd = 300,
		Brightness = 1.4,
		ClockTime = 18,
	},
	MusicId = nil,
	Enemies = { "CINDERLING", "MAGMA_HOUND", "ASHEN_KNIGHT", "FLAME_WRAITH" },
	BossId = "IGNIVAR_MOLTEN_KING",
	LootTableId = "LOOT_EMBERFALL",
	DiscoveryTableId = "DISC_EMBERFALL",
	Modifiers = { "NORMAL", "ECLIPSE", "NIGHTMARE" },
	DurationSeconds = 720,
	RecommendedPower = 12,
	Flavor = "The ash never settles. Nothing here has finished burning.",
}
