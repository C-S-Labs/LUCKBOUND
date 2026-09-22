--!strict
-- Verdant Valley chunk kit. Biome Blueprint §3.2 turned into modular pieces.
--
-- The blueprint's layout is a south-to-north progression:
--   ENTRY (Moss Slimes) → STREAM (Thorn Goblins) → MEADOW (Forest Wolves)
--   → GROVE (Elder Treants) → BOSS CLEARING (Rootbound Guardian)
-- with the HOLLOW as this world's optional side pocket (§6 checklist).
--
-- Sockets: Facing is degrees, 0 = -Z (north), 90 = +X, 180 = +Z (south),
-- 270 = -X. Offsets are local to the piece, before rotation.
--
-- SIZE: every piece is 256 x 256, owner-directed 2026-09-22. One size for the
-- whole kit, so the modeller has one number to build against rather than a
-- table of eight. It is about 51 character-heights across -- the middle ground
-- between two iterations that came back at ~100 studs (too tight to read as a
-- place) and ~1024 (so open the scatter disappeared into it). Sockets sit at
-- the edge midpoints, +/-128.
--
-- THE SIZES FOLLOW THE ART, NOT THE OTHER WAY ROUND. These are numbers in a
-- content file; the piece that reads correctly on the ground wins. If the
-- modeller comes back saying 256 is wrong, change it here -- that is the whole
-- reason it lives in content.
--
-- SizeY = 340 is provisional and applies to every piece. Height is deliberately
-- unconstrained in docs/CHUNK_AUTHORING.md, so this gets set from the measured
-- geometry when the first piece arrives.
--
-- KIT SIZE: this file declares 8 pieces, one per role in the Blueprint's
-- progression. The authoring target is 12-16 (owner-directed 2026-09-22) --
-- the variety of a run is the variety of the kit, and 8 starts to repeat
-- itself. Extra pieces arrive as VARIANTS of these roles, not new roles:
-- several meadows, several groves, weighted so one is common and another rare.
-- Entries get added here as each piece is authored; nothing speculative, since
-- a declared chunk with no art is a piece the blockout draws and nobody meant.
--
-- FIRST DELIVERY is 4 pieces -- ENTRY, PATH_STRAIGHT, GROVE, BOSS_CLEARING --
-- which is the smallest set that assembles into a complete walkable map. The
-- WIDE reservation means the Grove has to be among them: it is the only piece
-- offering the exit the arena accepts.
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
