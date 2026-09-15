--!strict
-- Pure roll logic. No Roblox globals, no player objects, no side effects --
-- so it is unit-testable headlessly and there is exactly one place where the
-- question "what did the player roll?" is answered.
--
-- FateSystem (server) owns the plumbing: rate limits, distance checks,
-- persistence, remotes. This file owns the decision.

local WeightedRandom = require(script.Parent.Parent.Util.WeightedRandom)

local FateCore = {}

export type RollOutcome = {
	WorldId: string,
	RollNumber: number,
	IsScripted: boolean, -- true => came from the onboarding sequence, not RNG
}

--- Worlds eligible for the roll pool at the current phase.
function FateCore.buildPool(worlds: { [string]: any }, currentPhase: number): { any }
	local pool = {}
	for _, world in worlds do
		if world.EnabledInPhase <= currentPhase then
			table.insert(pool, world)
		end
	end
	-- Stable order: pool iteration must not depend on hash ordering, or two
	-- servers with the same seed would produce different results.
	table.sort(pool, function(a, b)
		return a.Id < b.Id
	end)
	return pool
end

--- The weight a world actually carries in this draw.
---
--- With config.Fate.FateInfluencesOdds = false (the default, and the design
--- intent: the roll is TRUE RNG) this returns the flat weight and the player's
--- profile is not consulted at all.
function FateCore.effectiveWeight(world: any, profile: any, config: any): number
	local overrides = config.Fate.PrototypeWeights
	local base: number
	if config.CurrentPhase == 1 and overrides and overrides[world.Id] then
		base = overrides[world.Id]
	else
		base = world.RollWeight
	end

	if not config.Fate.FateInfluencesOdds then
		return base -- true RNG: nothing about the player changes this number
	end

	-- Dormant Master Spec §4 ladder. Unreachable while the flag is false.
	local bonus = math.min(
		(profile.FateLevel or 0) * config.Fate.WeightBonusPerLevel,
		config.Fate.WeightBonusCap
	)
	return base * (1 + bonus)
end

--- The scripted world for this roll, or nil once onboarding is exhausted.
--- Onboarding is indexed by TotalRolls, so it survives rejoins.
function FateCore.scriptedWorldId(profile: any, config: any): string?
	local sequence = config.Fate.OnboardingSequence
	local index = (profile.TotalRolls or 0) + 1
	if index <= #sequence then
		return sequence[index]
	end
	return nil
end

function FateCore.isOnboarding(profile: any, config: any): boolean
	return (profile.TotalRolls or 0) < #config.Fate.OnboardingSequence
end

--- Decides a roll. `nextNumber` returns [0,1) and is the only randomness source.
function FateCore.roll(
	worlds: { [string]: any },
	profile: any,
	config: any,
	nextNumber: () -> number
): RollOutcome
	local rollNumber = (profile.TotalRolls or 0) + 1

	local scripted = FateCore.scriptedWorldId(profile, config)
	if scripted then
		assert(worlds[scripted], `onboarding sequence names unknown world {scripted}`)
		return { WorldId = scripted, RollNumber = rollNumber, IsScripted = true }
	end

	local pool = FateCore.buildPool(worlds, config.CurrentPhase)
	assert(#pool > 0, "roll pool is empty -- check EnabledInPhase against CurrentPhase")

	local picked = WeightedRandom.pick(pool, function(world)
		return FateCore.effectiveWeight(world, profile, config)
	end, nextNumber)

	assert(picked, "weighted pick returned nil -- every world had non-positive weight")
	return { WorldId = picked.Id, RollNumber = rollNumber, IsScripted = false }
end

--- How long this player's next expedition should last. Onboarding expeditions
--- are short so the scripted arc fits inside the first few minutes.
function FateCore.expeditionDuration(world: any, profile: any, config: any): number
	if FateCore.isOnboarding(profile, config) then
		return config.Fate.OnboardingExpeditionSeconds
	end
	return world.DurationSeconds or config.Expedition.DefaultDurationSeconds
end

return FateCore
