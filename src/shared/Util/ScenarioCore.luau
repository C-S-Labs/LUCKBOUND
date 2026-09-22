--!strict
-- Assigns a SCENARIO to each placed chunk in a layout. Brief §3/§5/§8,
-- build spec §7.3.
--
-- THE SEAM. ChunkCore decides WHERE pieces go and knows nothing about what
-- happens in them; this decides WHAT HAPPENS and knows nothing about geometry.
-- Both are pure and take a seeded stream, so a whole run's structure can be
-- generated and inspected in CI without Roblox -- which is the only reason the
-- pacing rules below are testable at all.
--
-- It reads a layout and returns plain data:
--   { Index, ChunkId, Role, ScenarioId, Band, FateTouched }
--
-- It spawns nothing. Turning a scenario into enemies, loot and props is
-- ENCOUNTER CONFIGURATION, which build spec §7 still excludes -- see §7.3 for
-- exactly where the line is drawn and why it is drawn there.

local WeightedRandom = require(script.Parent.WeightedRandom)

local ScenarioCore = {}

--- Roles that are never assigned a scenario: the arrival plaza, the arena,
--- and a cap (build spec §7.4), which is a sealed ending with no room in it.
--- Stated once because `assign` asks twice -- to count the assignable pieces
--- and then to walk them -- and the two answers disagreeing would shift every
--- step's pacing by one.
local function isDressing(role: string): boolean
	return role == "ENTRY" or role == "BOSS" or role == "CAP"
end

export type AssignOptions = {
	-- How often Fate overrides ordinary weighting entirely (brief §6).
	-- 0 disables it; the caller passes GameConfig rather than a literal.
	FateInterventionChance: number,
	-- How many recent (chunk, scenario) pairs to remember when avoiding
	-- repeats. Brief §8: track COMBINATIONS, not raw chunk ids.
	RecentMemory: number,
	-- Escalation: the last stretch of the path prefers higher-pressure bands.
	EscalateFrom: number, -- fraction of the path, 0..1
}

--- Which scenarios a given placed chunk could host at all.
--- Compatibility is deliberate, not universal -- brief §3.
function ScenarioCore.compatible(chunk: any, role: string, scenarios: { [string]: any }): { any }
	local out = {}
	local supports = chunk.Supports or {}
	for _, s in scenarios do
		local roleOk = false
		if s.Roles == nil then
			roleOk = true
		else
			for _, r in s.Roles do
				if r == role then
					roleOk = true
				end
			end
		end
		if roleOk and supports[s.Requires] then
			table.insert(out, s)
		end
	end
	-- Stable order: hash iteration must not change what a seed produces. The
	-- same lesson ChunkCore.libraryFor learned.
	table.sort(out, function(a, b)
		return a.Id < b.Id
	end)
	return out
end

-- Escalation shapes the BANDS a step will consider, not the scenarios. Early
-- steps stay ordinary so the player can read the place; later steps open up.
-- Brief §5: stable structure, weighted variation, rare variation.
local function bandMultiplier(band: string, progress: number, escalateFrom: number): number
	if band == "ORDINARY" then
		return 1
	end
	if progress < escalateFrom then
		-- Before the escalation point, uncommon is possible and rare is not.
		return if band == "UNCOMMON" then 0.5 else 0
	end
	return if band == "UNCOMMON" then 1.2 else 1
end

--- Assigns a scenario to every non-ENTRY, non-BOSS chunk in a layout.
---
--- ENTRY and BOSS are left alone on purpose: arrival should be calm enough to
--- get your bearings, and the arena is already the largest thing in the run.
--- Giving either a scenario would be the generator competing with the pacing
--- the layout already has.
function ScenarioCore.assign(
	layout: any,
	chunks: { [string]: any },
	scenarios: { [string]: any },
	options: AssignOptions,
	nextNumber: () -> number
): (boolean, any)
	-- VALIDATE THE OPTIONS BEFORE TOUCHING THEM.
	--
	-- `nextNumber() < options.FateInterventionChance` against a nil dial threw
	-- "attempt to compare number < nil" and took the whole test suite down
	-- with it -- ~430 checks never ran and no summary printed. A generator
	-- that crashes on bad configuration is worse than one that refuses it:
	-- the crash hides every result after it.
	--
	-- Returned as (false, message) rather than a Result table because that is
	-- this module pair's established contract -- ChunkCore.assemble uses the
	-- same shape and ExpeditionSystem already branches on it. Introducing a
	-- second failure convention at one call site would be the duplication the
	-- Result pattern exists to avoid.
	for _, key in { "FateInterventionChance", "RecentMemory", "EscalateFrom" } do
		if type((options :: any)[key]) ~= "number" then
			return false,
				`ScenarioCore: options.{key} must be a number (got {typeof((options :: any)[key])}) -- `
					.. `these live in GameConfig.Expedition and Schema.validateConfig requires them`
		end
	end

	local steps = {}
	local recent: { string } = {}
	local lastScenario: string? = nil

	local assignable = 0
	for _, placed in layout.Chunks do
		if not isDressing(placed.Role) then
			assignable += 1
		end
	end

	local seen = 0
	for _, placed in layout.Chunks do
		if isDressing(placed.Role) then
			table.insert(steps, {
				Index = placed.Index,
				ChunkId = placed.ChunkId,
				Role = placed.Role,
				ScenarioId = nil,
				Band = nil,
				FateTouched = false,
			})
			continue
		end

		seen += 1
		local progress = if assignable > 1 then (seen - 1) / (assignable - 1) else 1
		local chunk = chunks[placed.ChunkId]
		if not chunk then
			return false, `layout names unknown chunk '{placed.ChunkId}'`
		end

		local pool = ScenarioCore.compatible(chunk, placed.Role, scenarios)
		if #pool == 0 then
			return false,
				`chunk '{placed.ChunkId}' supports no scenario for role {placed.Role} -- `
					.. `every placeable chunk needs at least one, or its rooms are empty`
		end

		-- Fate may override ordinary weighting entirely and pick from the rare
		-- band regardless of pacing. Brief §6: uncommon enough to feel special.
		local fate = nextNumber() < options.FateInterventionChance

		-- "Not the same scenario twice running" is a HARD rule, not a weight.
		-- It was a weight once, and the fallback below quietly reinstated the
		-- repeat it had just excluded -- 10 back-to-back pairs in 300 runs.
		-- Anything that must always hold belongs in the pool, not the weights.
		local function build(useFate: boolean, useRecency: boolean, allowRepeat: boolean)
			local out = {}
			for _, s in pool do
				if s.Id == lastScenario and not allowRepeat then
					continue
				end
				local weight = s.Weight
				if useFate then
					weight = if s.Band == "RARE" then s.Weight else 0
				else
					weight *= bandMultiplier(s.Band, progress, options.EscalateFrom)
					-- Damp a (chunk, scenario) PAIR seen recently -- the
					-- repetition a player actually notices. A place reappearing
					-- is fine when something different happens in it.
					if useRecency then
						local pair = `{placed.ChunkId}:{s.Id}`
						for _, r in recent do
							if r == pair then
								weight *= 0.15
							end
						end
					end
				end
				if weight > 0 then
					table.insert(out, { Scenario = s, Weight = weight })
				end
			end
			return out
		end

		-- Relax in order of how much each rule is worth, never past the hard
		-- one. The last resort -- allowing a repeat -- is reachable only by a
		-- chunk that supports exactly one scenario, which the schema permits
		-- and a kit should avoid.
		local candidates = build(fate, true, false)
		if #candidates == 0 and fate then
			fate = false
			candidates = build(false, true, false)
		end
		if #candidates == 0 then
			candidates = build(false, false, false)
		end
		if #candidates == 0 then
			candidates = build(false, false, true)
		end

		local pickedEntry = WeightedRandom.pick(candidates, function(c)
			return c.Weight
		end, nextNumber)
		if not pickedEntry then
			return false, `no scenario could be picked for '{placed.ChunkId}'`
		end
		local picked = pickedEntry.Scenario

		table.insert(steps, {
			Index = placed.Index,
			ChunkId = placed.ChunkId,
			Role = placed.Role,
			ScenarioId = picked.Id,
			Band = picked.Band,
			FateTouched = fate,
		})

		lastScenario = picked.Id
		table.insert(recent, `{placed.ChunkId}:{picked.Id}`)
		while #recent > options.RecentMemory do
			table.remove(recent, 1)
		end
	end

	return true, { WorldId = layout.WorldId, Seed = layout.Seed, Steps = steps }
end

--- How many of each band a plan contains. The pacing check a human would do by
--- eye, as a number a test can assert on.
function ScenarioCore.bandCounts(plan: any): { [string]: number }
	local counts = { ORDINARY = 0, UNCOMMON = 0, RARE = 0 }
	for _, step in plan.Steps do
		if step.Band then
			counts[step.Band] = (counts[step.Band] or 0) + 1
		end
	end
	return counts
end

return ScenarioCore
