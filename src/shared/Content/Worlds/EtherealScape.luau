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
	-- Three connective pieces between arrival and the vault. Sized so walking
	-- stays a minority of the 300 seconds -- asserted by test.
	MapPathLength = 3,
	RecommendedPower = 3,
	Flavor = "Above the weather, and nothing casts a shadow. The ground is a courtesy, and it ends.",
}
