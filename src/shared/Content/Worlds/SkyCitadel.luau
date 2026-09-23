--!strict
-- Epic tier. Added so onboarding can peak on an Epic rather than handing every
-- new player a guaranteed Mythic, which would permanently devalue the top tier
-- and the Fatebreak announcement that depends on it.
--
-- The Biome Blueprint drafts no Sky Citadel (its §7.4 lists it as a reserved
-- slot), so its art direction lives in docs/biomes/SKY_CITADEL.md instead: a white
-- futurist castle broken into floating islands -- needle spires with neon
-- halos, violet-roofed turrets, azure seams of light. Owner-directed
-- 2026-09-22.
--
-- ITS MAP IS A CHUNK KIT: Content/Chunks/SkyCitadel.luau, twenty-two pieces,
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
		-- SUNRISE ABOVE THE CLOUD SEA (chosen 2026-09-23). The citadel is white
		-- and futurist, and the one light that makes white architecture read
		-- as both clean and precious is a low sun: gold on every face that
		-- turns east, cool blue in every shadow, and a sky that runs from deep
		-- cobalt overhead to rose at the horizon.
		--
		-- It is also the one slot no other world holds. Verdant Valley is
		-- midday, Ethereal Scape is a white afternoon (15:00) and the brightest
		-- world by design, Emberfall is an ash-red dusk (18:00), Astral Reach
		-- is the void at midnight. Dusk here would have read as a paler
		-- Emberfall; full morning sun, as a second Ethereal Scape.
		AmbientColor = Color3.fromRGB(118, 124, 168),
		OutdoorAmbientColor = Color3.fromRGB(150, 150, 196),
		ColorShiftTop = Color3.fromRGB(255, 196, 140), -- sunlit faces go gold
		ColorShiftBottom = Color3.fromRGB(84, 104, 176), -- shadowed faces go blue
		-- Fog values are inert while the Atmosphere below exists (Roblox rule),
		-- and are kept only as the fallback look if it is ever removed.
		FogColor = Color3.fromRGB(236, 206, 196),
		FogStart = 400,
		FogEnd = 2600,
		Brightness = 2.6,
		ExposureCompensation = 0.15,
		ClockTime = 6.4,

		Atmosphere = {
			Density = 0.3,
			Offset = 0.12,
			Color = Color3.fromRGB(255, 212, 176), -- warm horizon band
			Decay = Color3.fromRGB(96, 104, 196), -- cobalt overhead
			Glare = 0.7,
			Haze = 1.4,
		},
		Sky = { SunAngularSize = 16, StarCount = 300 }, -- the last stars fading
		Bloom = { Intensity = 0.7, Size = 26, Threshold = 0.9 },
		SunRays = { Intensity = 0.1, Spread = 0.7 },
		Grade = {
			Brightness = 0.02,
			Contrast = 0.08,
			Saturation = 0.06,
			Tint = Color3.fromRGB(255, 246, 238),
		},

		-- Two layers, for parallax: a near, brighter, faster sea the islands
		-- hang just above, and a far, slower, bluer one that gives it depth.
		CloudSea = {
			{
				Depth = 150,
				Count = 70,
				Radius = 1600,
				Speed = 7,
				Heading = 80,
				SizeMin = 140,
				SizeMax = 340,
				Thickness = 0.26,
				Color = Color3.fromRGB(255, 232, 222),
				Transparency = 0.12,
			},
			{
				Depth = 380,
				Count = 50,
				Radius = 2400,
				Speed = 3,
				Heading = 80,
				SizeMin = 260,
				SizeMax = 560,
				Thickness = 0.2,
				Color = Color3.fromRGB(206, 196, 232),
				Transparency = 0.04,
			},
		},
		-- Sparse, slow, sunlit motes: high-altitude air catching the light.
		Motes = { Rate = 6, Lifetime = 9, Color = Color3.fromRGB(255, 236, 200), Size = 0.35, Speed = 3 },
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
