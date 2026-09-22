--!strict
-- Verdant Valley chunk kit. The WORLD's design -- what kinds of place it is
-- made of, what connects to what, and why -- is docs/biomes/VERDANT_VALLEY.md.
-- This file is only that design expressed as data.
--
-- DELIVERED 2026-09-22: 11 pieces, all uploaded, all measured. Every number
-- below was READ OFF THE DELIVERED GEOMETRY rather than typed by hand --
-- footprints and heights from the .rbxmx MeshPart sizes, openings and skirt
-- depths from the source FBX vertex data. That is the point: the art leads and
-- the data follows it.
--
-- Blueprint §3.2 describes a south-to-north progression (slimes, then goblins
-- at the water, wolves in the open, treants in the grove, the Guardian at the
-- end). That is the intended DIFFICULTY curve, not a fixed running order: the
-- assembler shuffles, and the only ordering the rules enforce is that the arena
-- is approached through a piece offering the Kind it accepts.
--
-- Sockets: Facing is degrees, 0 = -Z (north), 90 = +X, 180 = +Z (south),
-- 270 = -X. Offsets are local to the piece, before rotation. Every piece is
-- 256 x 256, so every opening sits at an edge midpoint, +/-128.
--
-- THE GROVE IS MISSING. 11 pieces arrived, not 12 -- it exceeded Roblox's
-- 10,000-triangle cap at 14,448 and did not make the upload. It was the only
-- piece offering WIDE, so on its own that would leave the arena unreachable and
-- every assembly failing. WIDE now sits on RUINS, WATERFALL and RIDGE_OVERLOOK.
--
-- That is not a workaround, it is the fix that was already owed: a Kind offered
-- by exactly one piece is a gate AND the same map every seed. Three providers
-- keeps the gate -- the arena is still only ever approached deliberately -- and
-- lets the approach differ per run. docs/biomes/VERDANT_VALLEY.md §3.
--
-- GroundOffsetY is studs from the BOTTOM of the piece's bounding box up to the
-- walking surface, so the loader can land the ground on the layout plane rather
-- than the bounding-box centre. It is the skirt depth: 4 on every piece except
-- the Fern Hollow, which sits 6 deep because it is a sunken place.

-- SUPPORTS is the scenario-compatibility gate (brief §3, build spec §7.3):
-- what can HAPPEN here, as opposed to what this place IS. Deliberately not
-- universal -- a traversal challenge in a flat meadow is not a challenge, and
-- a mini-boss in a corridor is not an arena. The generator intersects this
-- with Content/Scenarios, so a new scenario reaches every compatible chunk
-- without touching one of them.

local function socket(id: string, kind: string, x: number, z: number, facing: number)
	return { Id = id, Kind = kind, OffsetX = x, OffsetY = 0, OffsetZ = z, Facing = facing }
end

local NORTH, SOUTH, EAST, WEST = 0, 180, 90, 270
local H = 128 -- half the 256 footprint: every opening is an edge midpoint

local CHUNKS = {
	{
		Id = "VV_ENTRY",
		Role = "ENTRY" :: any,
		AssetKey = "VV_CHUNK_ENTRY",
		SizeY = 60.40,
		GroundOffsetY = 4,
		-- The delivered art opens SOUTH, so the path grows south from here.
		-- The data used to say north; the art is harder to change than a
		-- number, so the number moved.
		Sockets = { socket("south", "PATH", 0, H, SOUTH) },
		Weight = 1,
		MaxPerLayout = 1,
		EnemyTags = { "MOSS_SLIME" },
		Tags = { "tutorial", "low-density" },
	},
	{
		Id = "VV_PATH_STRAIGHT",
		Role = "PATH" :: any,
		AssetKey = "VV_CHUNK_PATH_STRAIGHT",
		SizeY = 50.20,
		GroundOffsetY = 4,
		Sockets = { socket("north", "PATH", 0, -H, NORTH), socket("south", "PATH", 0, H, SOUTH) },
		Supports = { Combat = true, Traversal = true, Ambush = true },
		Weight = 40,
		EnemyTags = { "MOSS_SLIME", "FOREST_WOLF" },
	},
	{
		Id = "VV_MEADOW_A",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MEADOW_A",
		SizeY = 52.90,
		GroundOffsetY = 4,
		Sockets = { socket("north", "PATH", 0, -H, NORTH), socket("south", "PATH", 0, H, SOUTH) },
		Supports = { Combat = true, MiniBoss = true, Treasure = true, Ambush = true },
		Weight = 30,
		EnemyTags = { "FOREST_WOLF" },
		Tags = { "open", "pack-combat" },
	},
	{
		Id = "VV_MEADOW_B",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MEADOW_B",
		SizeY = 46.20,
		GroundOffsetY = 4,
		-- East-west rather than north-south, so it turns the path.
		Sockets = { socket("west", "PATH", -H, 0, WEST), socket("east", "PATH", H, 0, EAST) },
		Supports = { Combat = true, MiniBoss = true, Ambush = true, Shrine = true },
		Weight = 30,
		EnemyTags = { "FOREST_WOLF" },
		Tags = { "open", "pack-combat" },
	},
	{
		Id = "VV_STREAM_CROSSING",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_STREAM_CROSSING",
		SizeY = 49.55,
		GroundOffsetY = 4,
		Sockets = { socket("north", "PATH", 0, -H, NORTH), socket("south", "PATH", 0, H, SOUTH) },
		Supports = { Combat = true, Traversal = true, Ambush = true, Event = true },
		Weight = 20,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "water", "path-choice" },
	},
	{
		Id = "VV_MUSHROOM_GLEN",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_MUSHROOM_GLEN",
		SizeY = 46.20,
		GroundOffsetY = 4,
		-- A bend: arrives one way, leaves at a right angle.
		Sockets = { socket("west", "PATH", -H, 0, WEST), socket("south", "PATH", 0, H, SOUTH) },
		Supports = { Combat = true, Shrine = true, Event = true, Secret = true, Puzzle = true },
		Weight = 18,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN", "MOSS_SLIME" },
		Tags = { "turn", "strange" },
	},
	{
		Id = "VV_FERN_HOLLOW",
		-- COMBAT, not SIDE. It was authored as this world's optional pocket
		-- (Blueprint §6) and cannot be one: every delivered piece has exactly
		-- TWO openings, the critical path spends both -- one to arrive, one to
		-- leave -- so no seed ever has a spare socket to hang a branch off.
		-- An optional branch needs a piece with THREE openings, and this kit
		-- has none. Schema.validateChunks now refuses that combination rather
		-- than letting a SIDE piece validate and never appear.
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_FERN_HOLLOW",
		SizeY = 54.90,
		-- Sunken, so the skirt is 6 deep rather than 4.
		GroundOffsetY = 6,
		Sockets = { socket("north", "PATH", 0, -H, NORTH), socket("east", "PATH", H, 0, EAST) },
		Supports = { Combat = true, Puzzle = true, Treasure = true, Secret = true, Ambush = true },
		Weight = 100,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN" },
		Tags = { "enclosed", "risk-reward" },
	},

	-- === The three arena approaches ==============================
	-- Each offers WIDE, which only the boss accepts, so each is reserved for
	-- the last step before the arena and never spent mid-path. Which one a run
	-- gets is the seed's choice.
	{
		Id = "VV_RUINS",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_RUINS",
		SizeY = 46.20,
		GroundOffsetY = 4,
		Sockets = { socket("west", "PATH", -H, 0, WEST), socket("north", "WIDE", 0, -H, NORTH) },
		Supports = { Combat = true, Puzzle = true, Treasure = true, MiniBoss = true, Secret = true, Event = true },
		Weight = 25,
		MaxPerLayout = 1,
		EnemyTags = { "THORN_GOBLIN", "ELDER_TREANT" },
		Tags = { "gate-to-boss", "ruin" },
	},
	{
		Id = "VV_WATERFALL",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_WATERFALL",
		SizeY = 49.55,
		GroundOffsetY = 4,
		Sockets = { socket("south", "PATH", 0, H, SOUTH), socket("east", "WIDE", H, 0, EAST) },
		Supports = { Combat = true, Traversal = true, Secret = true, Shrine = true, Event = true },
		Weight = 25,
		MaxPerLayout = 1,
		EnemyTags = { "FOREST_WOLF", "ELDER_TREANT" },
		Tags = { "gate-to-boss", "landmark" },
	},
	{
		Id = "VV_RIDGE_OVERLOOK",
		Role = "COMBAT" :: any,
		AssetKey = "VV_CHUNK_RIDGE_OVERLOOK",
		SizeY = 47.20,
		GroundOffsetY = 4,
		Sockets = { socket("west", "PATH", -H, 0, WEST), socket("east", "WIDE", H, 0, EAST) },
		Supports = { Combat = true, Traversal = true, Ambush = true, Shrine = true, MiniBoss = true },
		Weight = 25,
		MaxPerLayout = 1,
		EnemyTags = { "ELDER_TREANT" },
		Tags = { "gate-to-boss", "high-ground" },
	},

	{
		Id = "VV_BOSS_CLEARING",
		Role = "BOSS" :: any,
		AssetKey = "VV_CHUNK_BOSS_CLEARING",
		SizeY = 69.12,
		GroundOffsetY = 4,
		-- WIDE only: the approach must come through a piece that offers it,
		-- never a narrow footpath. Socket Kind is what enforces that.
		Sockets = { socket("south", "WIDE", 0, H, SOUTH) },
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
	-- Every delivered piece is 256 x 256 on the ground. Height is per piece
	-- and set above from the measured MeshPart.
	c.SizeX = 256
	c.SizeZ = 256
	table.insert(out, c)
end
return out
