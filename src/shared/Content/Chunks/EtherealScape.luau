--!strict
-- Ethereal Scape chunk kit. The first kit authored FROM art rather than ahead
-- of it: every piece maps one-to-one onto an island in
-- assets/source/worlds/ethereal_scape/aether_environment_refined.blend, whose
-- Aether_Terrain collection holds exactly eight (Island_00 .. Island_07, each
-- a Meadow + GoldRim + Underside). Exporting that scene island by island
-- produces this kit; the AssetKey comments record which island is which.
--
-- === THE SOCKET GRAMMAR IS DIFFERENT HERE, ON PURPOSE ===
-- Verdant Valley speaks PATH/WIDE. Ethereal Scape speaks SPAN/RITE:
--
--   SPAN  a bridge between two floating islands. Connective tissue.
--   RITE  the approach to the temple. The Vault accepts nothing else, and
--         the Waystone Ring is the only piece that offers one.
--
-- So the Waystone Ring always becomes the final piece before the Sky Temple,
-- for exactly the same reason the Grove always gates Verdant Valley's arena:
-- a Kind the arena accepts is reserved for the arena. Two worlds, two
-- vocabularies, one rule -- which is the point. See docs/MODULAR_MAPS.md.
--
-- SCALE: the 256-stud grid from MODULAR_MAPS.md. The smallest piece is
-- 256x512, about 51x102 character-heights. The blend carries an R6 rig in its
-- Scale_Reference collection precisely so this stays honest across the
-- Blender -> Roblox boundary: 1 metre = 1 stud, R6 = 5 studs tall.
--
-- Every AssetKey is PLACEHOLDER until the islands are uploaded. The loader
-- falls back to labelled primitives, which is what makes this kit testable
-- today -- and what makes the blockout readable enough to verify generation
-- by eye before any mesh exists.
--
-- NO EnemyTags: Ethereal Scape declares no enemies (see the world file). This
-- is the map-generation test biome, not a combat biome.

local function socket(id: string, kind: string, x: number, z: number, facing: number)
	return { Id = id, Kind = kind, OffsetX = x, OffsetY = 0, OffsetZ = z, Facing = facing }
end

local CHUNKS = {
	{
		Id = "ES_ARRIVAL_SHELF",
		Role = "ENTRY" :: any,
		AssetKey = "ES_CHUNK_ARRIVAL_SHELF", -- Island_00 + Spawn_Column x4
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("north", "SPAN", 0, -256, 0) },
		Weight = 1,
		MaxPerLayout = 1,
		Tags = { "arrival", "safe" },
	},
	{
		Id = "ES_SPAN_STRAIGHT",
		Role = "PATH" :: any,
		AssetKey = "ES_CHUNK_SPAN_STRAIGHT", -- Island_01 + Path_Bridge
		SizeX = 256,
		SizeZ = 512,
		Sockets = { socket("south", "SPAN", 0, 256, 180), socket("north", "SPAN", 0, -256, 0) },
		Weight = 40,
		Tags = { "bridge" },
	},
	{
		Id = "ES_SPAN_BEND",
		Role = "PATH" :: any,
		AssetKey = "ES_CHUNK_SPAN_BEND", -- Island_02 + Bridge_Abutment
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("south", "SPAN", 0, 256, 180), socket("east", "SPAN", 256, 0, 90) },
		Weight = 25,
		Tags = { "bridge", "turn" },
	},
	{
		Id = "ES_DRIFT_SHOAL",
		Role = "COMBAT" :: any,
		AssetKey = "ES_CHUNK_DRIFT_SHOAL", -- Island_03 + Crystal_00..04
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("south", "SPAN", 0, 256, 180), socket("north", "SPAN", 0, -256, 0) },
		Weight = 30,
		MaxPerLayout = 2,
		Tags = { "crystal", "open" },
	},
	{
		Id = "ES_MIRROR_TERRACE",
		Role = "COMBAT" :: any,
		AssetKey = "ES_CHUNK_MIRROR_TERRACE", -- Island_04, the widest meadow
		SizeX = 768,
		SizeZ = 768,
		Sockets = {
			socket("south", "SPAN", 0, 384, 180),
			socket("north", "SPAN", 0, -384, 0),
			socket("west", "SPAN", -384, 0, 270),
		},
		Weight = 26,
		MaxPerLayout = 1,
		Tags = { "open", "three-way" },
	},
	{
		Id = "ES_WAYSTONE_RING",
		Role = "COMBAT" :: any,
		AssetKey = "ES_CHUNK_WAYSTONE_RING", -- Island_05 + Waystone_00..06
		SizeX = 768,
		SizeZ = 512,
		-- The ONLY piece offering a RITE exit, and RITE is the only Kind the
		-- Vault accepts. That one fact makes the seven waystones the temple
		-- approach on every seed, without the generator knowing they exist.
		Sockets = { socket("south", "SPAN", 0, 256, 180), socket("north", "RITE", 0, -256, 0) },
		Weight = 24,
		MaxPerLayout = 1,
		Tags = { "waystones", "gate-to-boss" },
	},
	{
		Id = "ES_STILL_ALCOVE",
		Role = "SIDE" :: any,
		AssetKey = "ES_CHUNK_STILL_ALCOVE", -- Island_06 + SatelliteDetail_Cairn
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("east", "SPAN", 256, 0, 90) },
		Weight = 100,
		MaxPerLayout = 1,
		Tags = { "optional", "quiet" },
	},
	{
		Id = "ES_SKY_TEMPLE",
		Role = "BOSS" :: any,
		AssetKey = "ES_CHUNK_SKY_TEMPLE", -- Island_07 + Sky_Temple + Portal_L/R
		SizeX = 768,
		SizeZ = 768,
		-- RITE only. A bridge cannot open onto the temple steps.
		Sockets = { socket("south", "RITE", 0, 384, 180) },
		Weight = 1,
		MaxPerLayout = 1,
		Tags = { "arena", "temple" },
	},
}

local out = {}
for _, chunk in CHUNKS do
	local c = table.clone(chunk) :: any
	c.WorldId = "ETHEREAL_SCAPE"
	-- Thinner than Verdant Valley's 340: these are floating shelves with an
	-- Underside mesh, not ground cut out of a landscape.
	c.SizeY = 220
	table.insert(out, c)
end
return out
