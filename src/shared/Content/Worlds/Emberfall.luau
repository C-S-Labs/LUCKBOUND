--!strict
return {
	Id = "EMBERFALL",
	Name = "Emberfall",
	Rarity = "RARE",
	RollWeight = 700,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		AmbientColor = Color3.fromHex("6B2A18"),
		FogColor = Color3.fromHex("C4471F"),
		FogEnd = 600,
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
