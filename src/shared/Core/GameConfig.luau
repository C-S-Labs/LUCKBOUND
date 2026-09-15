--!strict
-- EVERY tunable number in LUCKBOUND lives here. Build spec §6.
-- Rule: if a designer might want to change it, it belongs in this file.
-- A magic number inside a System is a spec violation.

local function deepFreeze<T>(t: T): T
	for _, v in pairs(t :: any) do
		if type(v) == "table" then
			deepFreeze(v)
		end
	end
	return table.freeze(t :: any) :: T
end

local GameConfig = {
	-- Gates content by phase. Worlds with EnabledInPhase > CurrentPhase are
	-- excluded from the roll pool without being deleted. Bump to 2 / 3 to
	-- light up Phase 2 and 3 content.
	CurrentPhase = 1,

	Fate = {
		RollCooldownSeconds = 3.0, -- D-3
		MaxRollDistance = 30, -- studs from RollAnchor
		WeightBonusPerLevel = 0.04, -- D-5: +4% weighting per Fate level...
		WeightBonusCap = 2.0, -- ...capped at +200%
		ForceTutorialFirstRoll = true, -- D-2
		RollHistoryCap = 50, -- D-6

		-- D-1: Phase 1 override weights, keyed by world Id. When CurrentPhase
		-- is 1 these replace the world's own RollWeight. Set to nil to use the
		-- canonical full-game weights instead.
		PrototypeWeights = {
			VERDANT_VALLEY = 7500,
			EMBERFALL = 2000,
			ASTRAL_REACH = 500,
		},
	},

	Progression = {
		-- Fate points required to reach level n is BaseCost * n ^ Exponent.
		BaseCost = 100,
		Exponent = 1.35,
		MaxLevel = 100,

		Rewards = {
			ExpeditionCompleted = 25,
			BossDefeated = 60,
			DiscoveryFound = 15,
			FirstTimeWorld = 40,
		},
	},

	Expedition = {
		-- D-7: PDF §6 says 12 minutes. Flagged as likely too long for a
		-- proof-of-concept tester; revisit before Phase 2 playtests.
		DefaultDurationSeconds = 720,
		ReturnGraceSeconds = 10,
	},

	Save = {
		AutosaveIntervalSeconds = 60,
		SessionLockTimeoutSeconds = 30,
		MaxRetries = 5,
		RetryBackoffSeconds = 2,
	},

	UI = {
		-- D-4: reveal pacing. The highest-leverage numbers in Phase 1.
		-- Per-rarity durations come from Constants.RARITY[..].RevealDuration;
		-- these shape the build-up around them.
		RollBuildupSeconds = 1.2,
		ResultCardHoldSeconds = 4.0,
		AnnouncementDurationSeconds = 6.0,
		PromptActivationDistance = 12,
	},

	Debug = {
		-- Never ship true. Lets a developer force a specific roll result.
		AllowForcedRolls = false,
		LogEveryRoll = true,
	},
}

return deepFreeze(GameConfig)
