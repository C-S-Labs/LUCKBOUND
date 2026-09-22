--!strict
-- Verdant Valley chunk kit. The WORLD's design -- what kinds of place it is
-- made of, what connects to what, and why -- is docs/biomes/VERDANT_VALLEY.md.
-- This file is only that design expressed as data.
--
-- Blueprint §3.2 describes a south-to-north progression (slimes, then goblins
-- at the water, wolves in the open, treants in the grove, the Guardian at the
-- end). That is the intended DIFFICULTY curve, not a fixed running order: the
-- assembler shuffles, and the only ordering the rules actually enforce is that
-- the arena is approached through a piece offering the Kind it accepts.
--
-- Sockets: Facing is degrees, 0 = -Z (north), 90 = +X, 180 = +Z (south),
-- 270 = -X. Offsets are local to the piece, before rotation.
--
-- SIZE: every piece is 256 x 256, owner-directed 2026-09-22, sockets at the
-- edge midpoints (+/-128). Bracketed by two iterations that missed: ~100 studs
-- read too tight to be a place, ~1024 so open the scatter vanished into it.
--
-- THE SIZES FOLLOW THE ART, NOT THE OTHER WAY ROUND. These are numbers in a
-- content file and the piece that reads correctly on the ground wins.
--
-- SizeY = 340 is PROVISIONAL and wrong for the delivered art, which measures
-- 42-77 studs tall. ChunkLoader forces mesh.Size, so a piece would be stretched
-- 5-7x vertically. Set per piece from measured geometry before any upload.
--
-- KIT SIZE: 12-16 distinct pieces is the target. The variety of a run is the
-- variety of the kit -- the assembler only shuffles what it is given -- and 8
-- starts to repeat itself.
--
-- A NEW KIND OF PLACE NEEDS NO PERMISSION. An earlier version of this header
-- said extra pieces should be "variants of existing roles, not new roles", and
-- that was wrong in a way worth naming: it read as "only build more meadows".
-- Role is a ROUTING concept -- it tells the assembler where a piece may go --
-- not a design one. Ruins, a waterfall and a mushroom glen can all be COMBAT
-- and be nothing alike, and the world is better for it.
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
		SizeX = 256,
		SizeZ = 256,
		Sockets = { socket("north", "PATH", 0, -128, 0) },
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
		SizeZ = 256,
		Sockets = { socket("south", "PATH", 0, 128, 180), socket("north", "PATH", 0, -128, 0) },
		Weight = 40,
		EnemyTags = { "MOSS_SLIME", "FOREST_WOLF" },
	},
	{
		Id = "VV_PATH_BEND",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_BEND",
		SizeX = 256,
		SizeZ = 256,
		Sockets = { socket("south", "PATH", 0, 128, 180), socket("east", "PATH", 128, 0, 90) },
		Weight = 25,
		EnemyTags = { "MOSS_SLIME", "THORN_GOBLIN" },
		Tags = { "turn" },
	},
	{
		Id = "VV_STREAM",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_STREAM",
		SizeX = 256,
		SizeZ = 256,
		Sockets = { socket("south", "PATH", 0, 128, 180), socket("north", "PATH", 0, -128, 0) },
		Weight = 20,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "water", "path-choice" },
	},
	{
		Id = "VV_MEADOW",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MEADOW",
		SizeX = 256,
		SizeZ = 256,
		Sockets = {
			socket("south", "PATH", 0, 128, 180),
			socket("north", "PATH", 0, -128, 0),
			socket("west", "PATH", -128, 0, 270),
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
		SizeX = 256,
		SizeZ = 256,
		Sockets = { socket("south", "PATH", 0, 128, 180), socket("north", "WIDE", 0, -128, 0) },
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
		SizeX = 256,
		SizeZ = 256,
		Sockets = { socket("east", "PATH", 128, 0, 90) },
		Weight = 100,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "optional", "risk-reward" },
	},
	{
		Id = "VV_BOSS_CLEARING",
		Role = "BOSS" :: any,
		AssetKey = "VV_CHUNK_BOSS_CLEARING",
		SizeX = 256,
		SizeZ = 256,
		-- WIDE only: the boss approach must come through a Grove, never a
		-- narrow footpath. Socket Kind is what enforces that.
		Sockets = { socket("south", "WIDE", 0, 128, 180) },
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
