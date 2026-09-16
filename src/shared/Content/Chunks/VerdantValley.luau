--!strict
-- Verdant Valley chunk kit. Biome Blueprint §3.2 turned into modular pieces.
--
-- The blueprint's layout is a south-to-north progression:
--   ENTRY (Moss Slimes) → STREAM (Thorn Goblins) → MEADOW (Forest Wolves)
--   → GROVE (Elder Treants) → BOSS CLEARING (Rootbound Guardian)
-- with the HOLLOW as this world's optional side pocket (§6 checklist).
--
-- Sockets use a 48-stud grid so pieces meet cleanly. Facing is degrees:
-- 0 = -Z (north), 90 = +X, 180 = +Z (south), 270 = -X.
--
-- Every AssetKey is a PLACEHOLDER in the manifest today. That is deliberate:
-- the layout can be assembled, validated and tested before any mesh exists.

local function socket(id: string, kind: string, x: number, z: number, facing: number)
	return { Id = id, Kind = kind, OffsetX = x, OffsetY = 0, OffsetZ = z, Facing = facing }
end

local CHUNKS = {
	{
		Id = "VV_ENTRY",
		Role = "ENTRY" :: any,
		AssetKey = "VV_CHUNK_ENTRY",
		SizeX = 96,
		SizeZ = 96,
		Sockets = { socket("north", "PATH", 0, -48, 0) },
		Weight = 1,
		MaxPerLayout = 1,
		EnemyTags = { "MOSS_SLIME" },
		Tags = { "tutorial", "low-density" },
	},
	{
		Id = "VV_PATH_STRAIGHT",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_STRAIGHT",
		SizeX = 48,
		SizeZ = 96,
		Sockets = { socket("south", "PATH", 0, 48, 180), socket("north", "PATH", 0, -48, 0) },
		Weight = 40,
		EnemyTags = { "MOSS_SLIME", "FOREST_WOLF" },
	},
	{
		Id = "VV_PATH_BEND",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_BEND",
		SizeX = 96,
		SizeZ = 96,
		Sockets = { socket("south", "PATH", 0, 48, 180), socket("east", "PATH", 48, 0, 90) },
		Weight = 25,
		EnemyTags = { "MOSS_SLIME", "THORN_GOBLIN" },
		Tags = { "turn" },
	},
	{
		Id = "VV_STREAM",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_STREAM",
		SizeX = 144,
		SizeZ = 96,
		Sockets = { socket("south", "PATH", 0, 48, 180), socket("north", "PATH", 0, -48, 0) },
		Weight = 20,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "water", "path-choice" },
	},
	{
		Id = "VV_MEADOW",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MEADOW",
		SizeX = 192,
		SizeZ = 192,
		Sockets = {
			socket("south", "PATH", 0, 96, 180),
			socket("north", "PATH", 0, -96, 0),
			socket("west", "PATH", -96, 0, 270),
		},
		Weight = 30,
		MaxPerLayout = 2,
		EnemyTags = { "FOREST_WOLF" },
		Tags = { "open", "pack-combat" },
	},
	{
		Id = "VV_GROVE",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_GROVE",
		SizeX = 144,
		SizeZ = 144,
		Sockets = { socket("south", "PATH", 0, 72, 180), socket("north", "WIDE", 0, -72, 0) },
		Weight = 25,
		-- The only WIDE provider, and WIDE is what the arena accepts, so this
		-- is always the final piece before the boss -- Blueprint §3.2's
		-- "Elder Treants gate the approach to the boss clearing".
		MaxPerLayout = 1,
		EnemyTags = { "ELDER_TREANT", "FOREST_WOLF" },
		Tags = { "dense", "gate-to-boss" },
	},
	{
		Id = "VV_HOLLOW",
		Role = "SIDE" :: any,
		AssetKey = "VV_CHUNK_HOLLOW",
		SizeX = 96,
		SizeZ = 96,
		Sockets = { socket("east", "PATH", 48, 0, 90) },
		Weight = 100,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "optional", "risk-reward" },
	},
	{
		Id = "VV_BOSS_CLEARING",
		Role = "BOSS" :: any,
		AssetKey = "VV_CHUNK_BOSS_CLEARING",
		SizeX = 192,
		SizeZ = 192,
		-- WIDE only: the boss approach must come through a Grove, never a
		-- narrow footpath. Socket Kind is what enforces that.
		Sockets = { socket("south", "WIDE", 0, 96, 180) },
		Weight = 1,
		MaxPerLayout = 1,
		EnemyTags = {},
		Tags = { "arena" },
	},
}

local out = {}
for _, chunk in CHUNKS do
	local c = table.clone(chunk) :: any
	c.WorldId = "VERDANT_VALLEY"
	c.SizeY = 64
	table.insert(out, c)
end
return out
