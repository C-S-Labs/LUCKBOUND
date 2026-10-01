--!strict
-- Ethereal Scape. The Uncommon tier.
--
-- SOURCE OF TRUTH FOR THE PALETTE is the Blender scene
-- assets/source/worlds/ethereal_scape/aether_environment_refined.blend, whose
-- materials are: Aether Mint Grass, Pale Gold Soil, Golden Path, Cloud White,
-- Cloudstone, Deep Teal Leaves, Indigo Leaves, Temple Ivory, Temple Gold,
-- Sky Crystal, Portal Glow. Everything below is chosen to light THAT, not to
-- invent a look the meshes then have to live with.
--
-- The world is a sky temple standing above the cloud deck: gold-rimmed meadow
-- islands, bridges between them, and nothing underneath. So the lighting is
-- cloud haze stays luminous at the horizon. Owner-directed twilight now
-- replaces the earlier brightest-afternoon treatment (2026-10-01).
--
-- AMENDMENT 2026-09-26, owner-directed: SUPERSEDES the PrebuiltMap decision.
-- This world shipped as a single composed, hand-authored traverse -- the
-- original header (kept in git history) called it a deliberate no-combat
-- map-generation test rig, Enemies/BossId/LootTableId empty on purpose. That
-- is no longer the shape of this world: it now declares a 30-piece CHUNK KIT
-- (docs/biomes/ETHEREAL_SCAPE.md, Content/Chunks/EtherealScape.luau) --
-- the same kind of deliverable as Sky Citadel and Verdant Valley -- and opens
-- a drafted enemy roster (assets/source/enemies/ethereal_scape/ROSTER.md).
-- The original scene stays in the repo as the palette's source of truth and
-- art reference; it is simply no longer what the world loads.
-- `Schema.validateMaps` enforces a world declares a chunk kit or a
-- PrebuiltMap, never both, so this change removes PrebuiltMap and adds
-- MapPathLength in the same edit.
return {
	Id = "ETHEREAL_SCAPE",
	Name = "Ethereal Scape",
	Rarity = "UNCOMMON",
	RollWeight = 2500,
	EnabledInPhase = 1,
	Environment = {
		SkyId = nil,
		-- Orange-purple twilight: apricot horizon, violet sky and readable ivory.
		AmbientColor = Color3.fromRGB(113, 101, 148),
		OutdoorAmbientColor = Color3.fromRGB(139, 126, 170),
		ColorShiftTop = Color3.fromRGB(255, 186, 139),
		ColorShiftBottom = Color3.fromRGB(89, 83, 143),
		FogColor = Color3.fromRGB(226, 230, 244),
		FogStart = 450,
		FogEnd = 2600,
		Brightness = 2.0,
		ExposureCompensation = -0.06,
		ClockTime = 18.35,
		Atmosphere = {
			Density = 0.31,
			Offset = 0.15,
			Color = Color3.fromRGB(250, 190, 167),
			Decay = Color3.fromRGB(111, 82, 167),
			Glare = 0.18,
			Haze = 1.6,
		},
		Sky = { SunAngularSize = 10, MoonAngularSize = 6, StarCount = 220 },
		Bloom = { Intensity = 0.22, Size = 24, Threshold = 1.2 },
		SunRays = { Intensity = 0.035, Spread = 0.75 },
		Grade = {
			Brightness = 0.015,
			Contrast = 0.075,
			Saturation = -0.06,
			Tint = Color3.fromRGB(246, 232, 255),
		},
		-- Sparse upper-air veils: whole-map coverage, phased fade and relocation.
		Ribbons = {
			Count = 8,
			HeightMin = 420,
			HeightMax = 620,
			Margin = 600,
			LengthMin = 1000,
			LengthMax = 2000,
			WidthMin = 80,
			WidthMax = 135,
			PeriodMin = 55,
			PeriodMax = 90,
			ActiveFraction = 0.78,
			FadeFraction = 0.24,
			Opacity = 0.30,
			Drift = 32,
			Ripple = 14,
			Color = Color3.fromRGB(198, 167, 255),
			Tip = Color3.fromRGB(231, 176, 206),
			Texture = "rbxasset://textures/particles/smoke_main.dds",
		},
		-- Slow pearl cloud banks beneath the keels, leaving combat sightlines open.
		CloudCeiling = 160,
		CloudSea = {
			{
				Depth = 320,
				Count = 11,
				Radius = 1900,
				Speed = 3,
				Heading = 70,
				SizeMin = 180,
				SizeMax = 380,
				Thickness = 0.22,
				VerticalSpread = 180,
				Wander = 24,
				WanderPeriod = 75,
				Meshes = { "hubsky_cloudbank_a", "hubsky_cloudbank_b", "hubsky_cloudbank_c" },
				Billows = 4,
				Tufts = 1,
				Mix = { Cumulus = 0.65, Stratus = 0.35 },
				Color = Color3.fromRGB(237, 211, 226),
				Shade = Color3.fromRGB(158, 137, 193),
				Transparency = 0,
			},
			{
				Depth = 740,
				Count = 8,
				Radius = 2700,
				Speed = 1.2,
				Heading = 95,
				SizeMin = 380,
				SizeMax = 720,
				Thickness = 0.13,
				VerticalSpread = 320,
				Wander = 40,
				WanderPeriod = 110,
				Meshes = { "hubsky_cloudbank_a", "hubsky_cloudbank_b", "hubsky_cloudbank_c" },
				Billows = 1,
				Tufts = 0,
				Mix = { Stratus = 1 },
				Color = Color3.fromRGB(201, 188, 222),
				Shade = Color3.fromRGB(135, 123, 174),
				Transparency = 0,
			},
		},
		Motes = {
			Rate = 6,
			Lifetime = 8,
			Color = Color3.fromRGB(224, 213, 255),
			Size = 0.18,
			Speed = 1.2,
		},
	},
	MusicId = nil,
	-- Drafted, not yet built as EnemyDefinition content: build spec §7.6
	-- (enemy AI/combat) is reserved but not opened, and no world's Enemies
	-- list is populated yet -- Sky Citadel's is empty for the same reason.
	-- The roster is real design work, recorded ahead of the system that will
	-- read it: assets/source/enemies/ethereal_scape/ROSTER.md, and declared
	-- per piece as EnemyTags in Content/Chunks/EtherealScape.luau.
	Enemies = {},
	BossId = nil,
	LootTableId = nil,
	-- Same generic party key roll and vault contract as Sky Citadel (§7.5).
	Loot = {
		Chest = "ES_CHEST",
		Vault = "ES_VAULT",
		Boss = "ES_BOSS",
		VaultKey = {
			Id = "ETHEREAL_SCAPE_VAULT_KEY",
			Name = "Ethereal Scape Vault Key",
			DropChance = 0.20,
		},
	},
	DiscoveryTableId = nil,
	Modifiers = { "NORMAL" },
	-- Shorter than the 720s default (build spec D-7 already flags 720 as
	-- probably too long).
	DurationSeconds = 300,
	-- 36-piece hybrid kit, path length 5 -- matches Verdant Valley; retune once a
	-- piece has been walked. See Content/Chunks/EtherealScape.luau.
	MapPathLength = 5,
	-- Build spec §7.7 universal generation (owner-directed 2026-09-27): every
	-- junction mouth is filled; a branch grows up to BranchLength pieces and then
	-- ENDS -- in a miniboss arena (one per map), a side pocket, or a dead-end cap.
	-- Miniboss arenas are never the boss arena: the Sanctum still ends the critical
	-- path. Backdrop pieces (cloud banks, drifting isles, a spire) ring the map.
	Generation = {
		BranchLength = 2,
		Minibosses = 1,
		MaxSides = 2,
		Backdrop = 18,
		-- Owner 2026-09-27 walk: "3/4 enemy fighting chunks for a 30 piece map is
		-- a little underwhelming". ~40% of the ordinary pieces are fights, so the
		-- count grows with the map (ChunkCore favours COMBAT until it is met).
		CombatShare = 0.4,
	},
	RecommendedPower = 3,
	Flavor = "Above the weather, and nothing casts a shadow. The ground is a courtesy, and it ends.",
}
