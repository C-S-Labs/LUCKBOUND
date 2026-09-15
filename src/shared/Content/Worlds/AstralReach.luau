--!strict
return {
	Id = "ASTRAL_REACH",
	Name = "Astral Reach",
	Rarity = "MYTHIC",
	RollWeight = 45,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Biome Blueprint §5.3: no fog in the traditional sense -- void-black
		-- and a dense nebula skybox do the edge-hiding work fog does elsewhere.
		AmbientColor = Color3.fromRGB(30, 20, 55),
		OutdoorAmbientColor = Color3.fromRGB(40, 28, 70),
		ColorShiftTop = Color3.fromRGB(91, 62, 142),
		FogColor = Color3.fromRGB(13, 11, 26),
		FogStart = 200,
		FogEnd = 650,
		Brightness = 1.8,
		ClockTime = 0,
	},
	MusicId = nil,
	Enemies = { "STARLING", "VOID_WISP", "ASTRAL_KNIGHT", "GRAVITY_BEAST" },
	BossId = "STAR_EATER",
	LootTableId = "LOOT_ASTRAL",
	DiscoveryTableId = "DISC_ASTRAL",
	Modifiers = { "NORMAL", "CORRUPTED", "INVASION" },
	DurationSeconds = 720,
	RecommendedPower = 30,
	Flavor = "You are very far from the Crossroads. The stars are closer than the ground.",
}
