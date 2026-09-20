--!strict
-- Pure Fate progression maths. Build spec §2.4 / GameConfig.Progression.
--
-- Fate does NOT buy better odds (see FateCore.effectiveWeight). It is a
-- progression and score stat: it gates features, titles and Fatebreak
-- eligibility, and it is what the onboarding sequence exists to grow.

local ProgressionCore = {}

--- Total points required to have reached `level`. Level 1 costs 0.
function ProgressionCore.pointsForLevel(level: number, config: any): number
	if level <= 1 then
		return 0
	end
	return math.floor(config.Progression.BaseCost * (level - 1) ^ config.Progression.Exponent)
end

--- The level a given point total corresponds to.
function ProgressionCore.levelForPoints(points: number, config: any): number
	local maxLevel = config.Progression.MaxLevel
	-- Monotonic curve, so a linear scan upward is correct and cheap at these
	-- magnitudes. Kept simple deliberately: this runs once per Fate award.
	local level = 1
	while level < maxLevel and points >= ProgressionCore.pointsForLevel(level + 1, config) do
		level += 1
	end
	return level
end

--- Progress toward the next level, for the UI bar. Returns 1 at max level.
function ProgressionCore.levelProgress(points: number, config: any): number
	local level = ProgressionCore.levelForPoints(points, config)
	if level >= config.Progression.MaxLevel then
		return 1
	end
	local floorPts = ProgressionCore.pointsForLevel(level, config)
	local ceilPts = ProgressionCore.pointsForLevel(level + 1, config)
	if ceilPts <= floorPts then
		return 1
	end
	return (points - floorPts) / (ceilPts - floorPts)
end

--- Applies a Fate award to a profile copy. Returns the new point total, new
--- level, and whether a level-up occurred. Does not mutate `profile`.
function ProgressionCore.award(
	profile: any,
	reason: string,
	config: any
): (number, number, boolean)
	local amount = config.Progression.Rewards[reason]
	assert(amount, `unknown Fate reward reason: {reason}`)

	local newPoints = (profile.FatePoints or 0) + amount
	local newLevel = ProgressionCore.levelForPoints(newPoints, config)
	return newPoints, newLevel, newLevel > (profile.FateLevel or 1)
end

--- Applies a Fate award of an EXPLICIT amount. Same maths as `award`, for the
--- cases where the amount belongs to the content rather than to a reward
--- reason -- a redeemable code carries its own value, and inventing a
--- GameConfig reward row per code would put content in the config file.
--- Negative amounts are refused: taking Fate away is not a reward, and if it
--- ever becomes a mechanic it needs its own function and its own floor rules.
function ProgressionCore.grant(
	profile: any,
	amount: number,
	config: any
): (number, number, boolean)
	assert(type(amount) == "number" and amount >= 0, `Fate grant must be a non-negative number, got {tostring(amount)}`)

	local newPoints = (profile.FatePoints or 0) + amount
	local newLevel = ProgressionCore.levelForPoints(newPoints, config)
	return newPoints, newLevel, newLevel > (profile.FateLevel or 1)
end

return ProgressionCore
