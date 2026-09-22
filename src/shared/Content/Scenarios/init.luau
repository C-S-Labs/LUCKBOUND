--!strict
-- SCENARIO LIBRARY -- what can HAPPEN in a chunk, as opposed to what a chunk
-- IS. Procedural Biome Design Brief §4; build spec §7.3.
--
-- THE SEPARATION THIS EXISTS FOR
-- A chunk is physical space. A scenario is the gameplay placed inside it. The
-- same Ridge Overlook can be an ambush on one run, a shrine on another and a
-- treasure room on a third -- so twelve pieces of geometry produce far more
-- than twelve experiences, and new content arrives without new art.
--
-- Adding a scenario = adding one entry here. No System changes, and no chunk
-- has to know it exists: a chunk declares WHAT IT CAN SUPPORT and the
-- generator intersects that with this library.
--
-- WEIGHTS are relative within a pacing band, not percentages.
--
-- PACING BANDS (brief §5: structured randomness, not pure randomness)
--   ORDINARY  the backbone -- most rooms, most runs
--   UNCOMMON  texture -- a run usually has one or two
--   RARE      the reason a run is worth telling someone about
--
-- REQUIRES is the compatibility gate, checked against a chunk's Supports
-- table. Deliberately NOT "every scenario fits every chunk" (brief §3): a
-- traversal challenge in a flat meadow is not a challenge, and a mini-boss in
-- a corridor is not an arena.

export type Scenario = {
	Id: string,
	Name: string,
	Band: "ORDINARY" | "UNCOMMON" | "RARE",
	Weight: number,
	Requires: string, -- the Supports key a chunk must declare
	-- Roles this scenario may be placed on. ENTRY and BOSS are excluded from
	-- everything by default: arrival should be calm and the arena is already
	-- the biggest thing in the run.
	Roles: { string }?,
	Notes: string?,
}

local PATH_AND_COMBAT = { "PATH", "COMBAT", "SIDE" }

local SCENARIOS: { Scenario } = {
	{
		Id = "NORMAL_COMBAT",
		Name = "Skirmish",
		Band = "ORDINARY",
		Weight = 100,
		Requires = "Combat",
		Roles = PATH_AND_COMBAT,
		Notes = "The backbone. Standard enemies, straightforward reward.",
	},
	{
		Id = "TRAVERSAL",
		Name = "Crossing",
		Band = "ORDINARY",
		Weight = 45,
		Requires = "Traversal",
		Roles = PATH_AND_COMBAT,
		Notes = "Movement and platforming using the chunk itself. Needs real verticality.",
	},
	{
		Id = "TREASURE",
		Name = "Cache",
		Band = "ORDINARY",
		Weight = 40,
		Requires = "Treasure",
		Roles = PATH_AND_COMBAT,
		Notes = "Reward-focused, optional risk.",
	},
	{
		Id = "ELITE_COMBAT",
		Name = "Elite",
		Band = "UNCOMMON",
		Weight = 55,
		Requires = "Combat",
		Roles = PATH_AND_COMBAT,
		Notes = "Stronger enemies, a modifier, or environmental pressure.",
	},
	{
		Id = "PUZZLE",
		Name = "Mechanism",
		Band = "UNCOMMON",
		Weight = 40,
		Requires = "Puzzle",
		Roles = PATH_AND_COMBAT,
		Notes = "Sequence, observation, timing or spatial logic. Wants an enclosed space.",
	},
	{
		Id = "AMBUSH",
		Name = "Ambush",
		Band = "UNCOMMON",
		Weight = 35,
		Requires = "Ambush",
		Roles = PATH_AND_COMBAT,
		Notes = "The room changes once the player commits. Needs a point of no return.",
	},
	{
		Id = "SHRINE",
		Name = "Shrine",
		Band = "UNCOMMON",
		Weight = 30,
		Requires = "Shrine",
		Roles = PATH_AND_COMBAT,
		Notes = "A meaningful choice or blessing. Should feel like a pause.",
	},
	{
		Id = "MINI_BOSS",
		Name = "Mini-boss",
		Band = "RARE",
		Weight = 30,
		Requires = "MiniBoss",
		Roles = { "COMBAT" },
		Notes = "Contained, high intensity. Only in a piece with arena space.",
	},
	{
		Id = "SECRET",
		Name = "Secret",
		Band = "RARE",
		Weight = 25,
		Requires = "Secret",
		Roles = PATH_AND_COMBAT,
		Notes = "A hidden route, interaction or optional space.",
	},
	{
		Id = "FATE_EVENT",
		Name = "Fate Intervention",
		Band = "RARE",
		Weight = 20,
		Requires = "Event",
		Roles = PATH_AND_COMBAT,
		Notes = "The room's rules change. Brief §6 -- this is where Luckbound's "
			.. "identity reaches past the loot roll and decides what a PLACE is.",
	},
}

local registry: { [string]: Scenario } = {}
for _, s in SCENARIOS do
	assert(registry[s.Id] == nil, `duplicate scenario Id: {s.Id}`)
	registry[s.Id] = s
end

return registry
