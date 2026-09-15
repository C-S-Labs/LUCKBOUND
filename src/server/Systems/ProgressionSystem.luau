--!strict
-- Fate points and levels. Build spec T-110.
-- Fate is a progression and score stat. It does not buy better roll odds --
-- see FateCore.effectiveWeight and GameConfig.Fate.FateInfluencesOdds.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local ProgressionCore = require(Root.Core.ProgressionCore)

local ProgressionSystem = {}

local SaveSystem

function ProgressionSystem.init(saveSystem: any): ()
	SaveSystem = saveSystem
end

--- Grants Fate for a named reason from GameConfig.Progression.Rewards.
function ProgressionSystem.award(player: Player, reason: string): ()
	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	local points, level, leveledUp = ProgressionCore.award(profile, reason, GameConfig)
	local delta = points - profile.FatePoints

	profile.FatePoints = points
	profile.FateLevel = level
	SaveSystem.markDirty(player)

	Net.get("Progression_FateChanged"):FireClient(player, {
		FatePoints = points,
		FateLevel = level,
		Delta = delta,
		Reason = reason,
		LeveledUp = leveledUp,
		Progress = ProgressionCore.levelProgress(points, GameConfig),
	})
end

--- Records a roll in the profile. Called by FateSystem, which owns the
--- decision; this owns the bookkeeping.
function ProgressionSystem.recordRoll(player: Player, worldId: string, rarity: string): ()
	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	profile.TotalRolls += 1
	table.insert(profile.RollHistory, {
		WorldId = worldId,
		Rarity = rarity,
		Timestamp = os.time(),
	})

	local Constants = require(Root.Core.Constants)
	local current = Constants.RARITY[profile.Stats.DeepestRarity]
	local rolled = Constants.RARITY[rarity]
	if rolled and (not current or rolled.Order > current.Order) then
		profile.Stats.DeepestRarity = rarity
	end

	SaveSystem.markDirty(player)
end

function ProgressionSystem.snapshot(player: Player): any?
	local profile = SaveSystem.get(player)
	if not profile then
		return nil
	end
	return {
		FatePoints = profile.FatePoints,
		FateLevel = profile.FateLevel,
		TotalRolls = profile.TotalRolls,
		Progress = ProgressionCore.levelProgress(profile.FatePoints, GameConfig),
		RollHistory = profile.RollHistory,
		Stats = profile.Stats,
		Discoveries = profile.Discoveries,
	}
end

return ProgressionSystem
