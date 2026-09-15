--!strict
-- Phase 3. Present so the roll pool, Discovery Book and UI are written against
-- a world that has no records -- the §10 mystery hook is a data flag, not a
-- special code path.
return {
	Id = "THE_UNKNOWN",
	Name = "???",
	Rarity = "UNKNOWN",
	RollWeight = 5,
	EnabledInPhase = 3,
	Environment = {
		SkyId = nil,
		AmbientColor = Color3.fromHex("000000"),
		FogColor = Color3.fromHex("FFFFFF"),
		FogEnd = 200,
		ClockTime = 12,
	},
	MusicId = nil,
	Enemies = {},
	BossId = nil,
	LootTableId = nil,
	DiscoveryTableId = nil,
	Modifiers = {},
	DurationSeconds = 720,
	RecommendedPower = 0,
	Flavor = "No records found.",
}
