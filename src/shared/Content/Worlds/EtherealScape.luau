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
-- the opposite of Emberfall's -- fog here is cloud, and cloud BRIGHTENS the
-- distance rather than hiding it. This is the brightest world in the game.
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
	-- Drafted, not yet built as EnemyDefinition content: build spec §7.6
	-- (enemy AI/combat) is reserved but not opened, and no world's Enemies
	-- list is populated yet -- Sky Citadel's is empty for the same reason.
	-- The roster is real design work, recorded ahead of the system that will
	-- read it: assets/source/enemies/ethereal_scape/ROSTER.md, and declared
	-- per piece as EnemyTags in Content/Chunks/EtherealScape.luau.
	Enemies = {},
	BossId = nil,
	LootTableId = nil,
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
