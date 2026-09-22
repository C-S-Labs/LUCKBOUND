--!strict
-- Epic tier. Added so onboarding can peak on an Epic rather than handing every
-- new player a guaranteed Mythic, which would permanently devalue the top tier
-- and the Fatebreak announcement that depends on it.
--
-- The Biome Blueprint drafts no Sky Citadel (its §7.4 lists it as a reserved
-- slot), so its art direction lives in docs/SKY_CITADEL.md instead: a white
-- futurist castle broken into floating islands -- needle spires with neon
-- halos, violet-roofed turrets, azure seams of light. Owner-directed
-- 2026-09-22.
--
-- ITS MAP IS A CHUNK KIT: Content/Chunks/SkyCitadel.luau, twelve pieces,
-- connected by SKYWAY (connective) and ASCENT (arena-only). Every piece is a
-- PLACEHOLDER in the manifest, so the expedition builds as blockout until the
-- FBXs are uploaded.
--
-- Enemies, boss and loot tables are still empty -- the kit makes the world
-- enterable, not playable. The Environment below predates the art direction;
-- it happens to suit it (warm morning sun above the weather) and is left as-is
-- until a piece has been seen in Studio.
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
