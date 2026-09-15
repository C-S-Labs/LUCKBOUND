--!strict
return {
	Id = "ASTRAL_REACH",
	Name = "Astral Reach",
	Rarity = "MYTHIC",
	RollWeight = 45,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		AmbientColor = Color3.fromHex("2A2050"),
		FogColor = Color3.fromHex("6B4FC4"),
		FogEnd = 1400,
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
