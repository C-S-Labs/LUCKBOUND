--!strict
-- Verdant Valley chunk kit. Biome Blueprint §3.2 turned into modular pieces.
--
-- The blueprint's layout is a south-to-north progression:
--   ENTRY (Moss Slimes) → STREAM (Thorn Goblins) → MEADOW (Forest Wolves)
--   → GROVE (Elder Treants) → BOSS CLEARING (Rootbound Guardian)
-- with the HOLLOW as this world's optional side pocket (§6 checklist).
--
-- Sockets use a 256-stud grid so pieces meet cleanly. Facing is degrees:
-- 0 = -Z (north), 90 = +X, 180 = +Z (south), 270 = -X.
--
-- SCALE: pieces are sized against a 5-stud character and the hub's 1200-stud
-- footprint. The smallest connective piece is 256x512 -- about 51x102
-- character-heights -- so a corridor reads as a forest path rather than a
-- hallway. An expedition at path length 5 spans roughly 3000 studs end to end,
-- which is a walk of well under a minute at WalkSpeed 32.
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
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("north", "PATH", 0, -256, 0) },
		Weight = 1,
		MaxPerLayout = 1,
		EnemyTags = { "MOSS_SLIME" },
		Tags = { "tutorial", "low-density" },
	},
	{
		Id = "VV_PATH_STRAIGHT",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_STRAIGHT",
		SizeX = 256,
		SizeZ = 512,
		Sockets = { socket("south", "PATH", 0, 256, 180), socket("north", "PATH", 0, -256, 0) },
		Weight = 40,
		EnemyTags = { "MOSS_SLIME", "FOREST_WOLF" },
	},
	{
		Id = "VV_PATH_BEND",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_BEND",
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("south", "PATH", 0, 256, 180), socket("east", "PATH", 256, 0, 90) },
		Weight = 25,
		EnemyTags = { "MOSS_SLIME", "THORN_GOBLIN" },
		Tags = { "turn" },
	},
	{
		Id = "VV_STREAM",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_STREAM",
		SizeX = 768,
		SizeZ = 512,
		Sockets = { socket("south", "PATH", 0, 256, 180), socket("north", "PATH", 0, -256, 0) },
		Weight = 20,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "water", "path-choice" },
	},
	{
		Id = "VV_MEADOW",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MEADOW",
		SizeX = 1024,
		SizeZ = 1024,
		Sockets = {
			socket("south", "PATH", 0, 512, 180),
			socket("north", "PATH", 0, -512, 0),
			socket("west", "PATH", -512, 0, 270),
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
		SizeX = 768,
		SizeZ = 768,
		Sockets = { socket("south", "PATH", 0, 384, 180), socket("north", "WIDE", 0, -384, 0) },
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
		SizeX = 512,
		SizeZ = 512,
		Sockets = { socket("east", "PATH", 256, 0, 90) },
		Weight = 100,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "optional", "risk-reward" },
	},
	{
		Id = "VV_BOSS_CLEARING",
		Role = "BOSS" :: any,
		AssetKey = "VV_CHUNK_BOSS_CLEARING",
		SizeX = 1024,
		SizeZ = 1024,
		-- WIDE only: the boss approach must come through a Grove, never a
		-- narrow footpath. Socket Kind is what enforces that.
		Sockets = { socket("south", "WIDE", 0, 512, 180) },
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
	c.SizeY = 340
	table.insert(out, c)
end
return out
