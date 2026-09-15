--!strict
return {
	Id = "VERDANT_VALLEY",
	Name = "Verdant Valley",
	Rarity = "COMMON",
	RollWeight = 5000,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		AmbientColor = Color3.fromHex("8FB98A"),
		FogColor = Color3.fromHex("C9E4C0"),
		FogEnd = 900,
		ClockTime = 14,
	},
	MusicId = nil,
	Enemies = { "MOSS_SLIME", "FOREST_WOLF", "THORN_GOBLIN", "ELDER_TREANT" },
	BossId = "ROOTBOUND_GUARDIAN",
	LootTableId = "LOOT_VERDANT",
	DiscoveryTableId = "DISC_VERDANT",
	Modifiers = { "NORMAL", "NIGHT" },
	DurationSeconds = 720,
	RecommendedPower = 1,
	Flavor = "Green and patient. Something old is still growing here.",
}
