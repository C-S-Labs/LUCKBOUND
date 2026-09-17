--!strict
-- Ethereal Scape. The Uncommon tier, and the project's first world built from
-- authored art rather than invented numbers.
--
-- SOURCE OF TRUTH FOR THE PALETTE is the Blender scene
-- assets/source/worlds/ethereal_scape/aether_environment_refined.blend, whose
-- materials are: Aether Mint Grass, Pale Gold Soil, Golden Path, Cloud White,
-- Cloudstone, Deep Teal Leaves, Indigo Leaves, Temple Ivory, Temple Gold,
-- Sky Crystal, Portal Glow. Everything below is chosen to light THAT, not to
-- invent a look the meshes then have to live with.
--
-- The scene is a sky temple standing above the cloud deck: gold-rimmed meadow
-- islands, bridges between them, and nothing underneath. So the lighting is
-- the opposite of Emberfall's -- fog here is cloud, and cloud BRIGHTENS the
-- distance rather than hiding it. This is the brightest world in the game.
--
-- THIS IS A TESTING BIOME. Enemies, boss and loot tables are deliberately
-- empty: it exists to prove that rolling a world, walking through its portal
-- and generating its map all work. Combat content is not its job and adding
-- some would make it a worse test.
return {
	Id = "ETHEREAL_SCAPE",
	Name = "Ethereal Scape",
	Rarity = "UNCOMMON",
	RollWeight = 2500,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Cool ivory ambient: the light is bounced off cloud, so it arrives
		-- from everywhere and almost nothing casts a hard shadow.
		AmbientColor = Color3.fromRGB(120, 132, 140),
		OutdoorAmbientColor = Color3.fromRGB(150, 162, 170),
		ColorShiftTop = Color3.fromRGB(214, 226, 236), -- Cloud White
		-- Fog is the cloud deck. It is nearly white and starts far out, so
		-- neighbouring islands stay readable -- you must be able to see the
		-- next island to want to cross to it.
		FogColor = Color3.fromRGB(222, 232, 240),
		FogStart = 300,
		FogEnd = 2200,
		Brightness = 3.0, -- above the weather; brighter than Verdant Valley
		ClockTime = 15,
	},
	MusicId = nil,
	-- Empty ON PURPOSE. See the header: this world is the map-generation test
	-- rig, and Phase 2 combat has not been built.
	Enemies = {},
	BossId = nil,
	LootTableId = nil,
	DiscoveryTableId = nil,
	Modifiers = { "NORMAL" },
	-- Shorter than the 720s default (build spec D-7 already flags 720 as
	-- probably too long). A test biome you walk through in five minutes tells
	-- you whether generation works; twelve minutes of standing in it does not.
	DurationSeconds = 300,
	-- NO MapPathLength: this world does not assemble a map from chunks. It
	-- ships one, below.
	--
	-- WHY THIS WORLD IS PREBUILT AND VERDANT VALLEY IS NOT
	-- The delivered art is a COMPOSED traverse, not a set of interchangeable
	-- pieces. Its eight islands climb monotonically (y 354 -> 761), each of
	-- the six bridges is cut to its own gap, every bridge landing is authored
	-- as a matched pair naming the two islands it joins, and the islands grow
	-- toward the temple (1030x813 -> 1932x1535). Shuffle them and all four of
	-- those break at once. The socket grammar is not wrong -- this art simply
	-- is not modular, and pretending otherwise would mean re-authoring it.
	--
	-- A world declares EITHER a chunk kit OR a PrebuiltMap, never both;
	-- Schema.validateMaps enforces that, because two ways to build one world's
	-- map is exactly the second competing architecture CLAUDE.md forbids.
	PrebuiltMap = {
		-- Names the AssetManifest entry, which names the Rojo-synced model.
		AssetKey = "ES_ENVIRONMENT_FULL",
		-- The scene was modelled against the R6 proxy in its Scale_Reference
		-- collection, and that proxy is ~10x a real R6 character (59.6 studs
		-- tall against 5). Everything else in the scene agrees with the proxy
		-- rather than with Roblox: doorways 24 studs, trees 11, waystones 12,
		-- a 1028-stud walk end to end. So the scene is internally consistent
		-- and uniformly oversized, and one number fixes all of it.
		--
		-- PROVISIONAL until someone walks it. 0.1 puts the traverse at ~64
		-- seconds one way at the default WalkSpeed, which fits inside the
		-- 300-second expedition with room for detours.
		Scale = 0.1,
	},
	RecommendedPower = 3,
	Flavor = "Above the weather, and nothing casts a shadow. The ground is a courtesy, and it ends.",
}
