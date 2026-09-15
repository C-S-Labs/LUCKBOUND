--!strict
-- Epic tier. Added so onboarding can peak on an Epic rather than handing every
-- new player a guaranteed Mythic, which would permanently devalue the top tier
-- and the Fatebreak announcement that depends on it.
--
-- ⚠️ DATA ONLY. The Biome Blueprint drafts no Sky Citadel (its §7.4 lists it as
-- a reserved slot with no blueprint written). Enemies, boss and loot tables are
-- empty, and the Environment values below are invented rather than
-- blueprint-sanctioned. Phase 1 never enters a world, so this is sufficient
-- today; it needs a real biome before Phase 2 makes worlds enterable.
return {
	Id = "SKY_CITADEL",
	Name = "Sky Citadel",
	Rarity = "EPIC",
	RollWeight = 400, -- canonical full-game weight, build spec §3.1
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Deliberately the brightest world in the prototype: you are above the
		-- weather, in open sun. Reads as a relief against Emberfall's ash and
		-- Astral Reach's void.
		AmbientColor = Color3.fromRGB(140, 160, 200),
		OutdoorAmbientColor = Color3.fromRGB(170, 185, 215),
		ColorShiftTop = Color3.fromRGB(255, 235, 190),
		FogColor = Color3.fromRGB(225, 235, 250),
		FogStart = 150,
		FogEnd = 700,
		Brightness = 3,
		ClockTime = 7,
	},
	MusicId = nil,
	Enemies = {},
	BossId = nil,
	LootTableId = nil,
	DiscoveryTableId = nil,
	Modifiers = { "NORMAL", "NIGHT" },
	DurationSeconds = 720,
	RecommendedPower = 20,
	Flavor = "Nothing above you but sun. The clouds are somewhere below the floor.",
}
