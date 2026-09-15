--!strict
-- EVERY tunable number in LUCKBOUND lives here. Build spec §6.
-- Rule: if a designer might want to change it, it belongs in this file.
-- A magic number inside a System is a spec violation.

local function deepFreeze<T>(t: T): T
	-- Guard against a table reachable by two paths (UITheme reuses Constants'
	-- rarity tables): freezing an already-frozen table raises.
	if table.isfrozen(t :: any) then
		return t
	end
	for _, v in pairs(t :: any) do
		if type(v) == "table" and not table.isfrozen(v) then
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
		-- === TRUE RNG ===
		-- The roll is never weighted by player state. Fate is a progression and
		-- score stat; it does not buy better odds. After the scripted onboarding
		-- below, every roll is an honest draw over the enabled pool.
		--
		-- The weighting hook still exists in FateCore but is OFF. Flipping this
		-- to true re-enables the Master Spec §4 "influence your rolls" ladder.
		-- Do not flip it without an explicit design decision.
		FateInfluencesOdds = false,
		WeightBonusPerLevel = 0.04, -- inert while FateInfluencesOdds = false
		WeightBonusCap = 2.0, -- inert while FateInfluencesOdds = false

		-- === SCRIPTED ONBOARDING ===
		-- Rolls 1..#OnboardingSequence are forced, in order. The point is to show
		-- a new player the whole rarity ladder -- Common, Rare, Mythic -- inside
		-- their first few minutes, so that when true RNG takes over they already
		-- know what they are chasing. Roll #(n+1) onward is pure chance.
		OnboardingSequence = { "VERDANT_VALLEY", "EMBERFALL", "ASTRAL_REACH" },

		-- Onboarding expeditions are short so the scripted arc fits in ~5 minutes.
		-- Full-length expeditions begin once the sequence is exhausted.
		OnboardingExpeditionSeconds = 100,

		RollCooldownSeconds = 3.0, -- D-3
		MaxRollDistance = 30, -- studs from RollAnchor
		RollHistoryCap = 50, -- D-6

		-- Phase 1 pool weights, keyed by world Id. Used only while CurrentPhase
		-- is 1. Set to nil to use each world's canonical full-game RollWeight.
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

	-- Hub geometry. Biome Blueprint §2.1 and §7.3: named anchors live here and
	-- are never re-derived per script, so the axis mapping is confirmed once in
	-- Studio and locked. Roblox is Y-up, so "compass" is the X/Z plane:
	--   NORTH = -Z, SOUTH = +Z, EAST = +X, WEST = -X, UP = +Y.
	-- Visual detail (materials, palette, props) lives in Content/Hub/Crossroads.
	HubLayout = {
		HubDiameter = 120,
		PlazaRingWidth = 26,
		WalkwayWidth = 8,
		WalkwayRaise = 2, -- studs above the lower plaza ring
		ProcessionalWidth = 12, -- the Expedition Gate approach is wider
		ZoneRingRadius = 46, -- centre of hub → centre of a compass zone

		Anchors = {
			FATE_ENGINE = Vector3.new(0, 0, 0),
			HALL_OF_LEGENDS = Vector3.new(0, 0, -46), -- north
			DISCOVERY_ARCHIVE = Vector3.new(46, 0, 0), -- east
			EXPEDITION_GATE = Vector3.new(0, 0, 46), -- south
			TRAINING_GROUNDS = Vector3.new(-46, 0, 0), -- west
			GLOBAL_OBSERVATORY = Vector3.new(0, 40, 0), -- upper platform
		},

		SpawnAnchor = Vector3.new(0, 4, 34), -- south of centre, facing the Engine
	},

	-- Shared PortalRig. Biome Blueprint §1.3.
	Portal = {
		OuterRingRadius = 9,
		OuterRingThickness = 1.2,
		InnerRingRadius = 6.5,
		InnerRingThickness = 0.6,
		RingSegments = 28, -- segmented ring; see docs/BLUEPRINT_RECONCILIATION.md
		RuneCount = 8,
		PlinthDiameter = 14,
		PlinthHeight = 1.5,
		PlinthSides = 8, -- octagonal

		IdleParticleRate = 8,
		ActiveParticleRate = 40,
		SpinUpParticleRate = 200,
		ParticleLifetimeMin = 1.5,
		ParticleLifetimeMax = 3,

		IdleBrightness = 1,
		ActiveBrightness = 3,
		LightRange = 24,

		PlanePulseMin = 0.3,
		PlanePulseMax = 0.7,
		PlanePulseSeconds = 2.4,

		-- The single most important UX beat in the game (master spec §25,
		-- blueprint §1.3). Never make it instant.
		SpinUpSeconds = 2.5,
		IdleSpinSpeed = 0.15, -- rad/s
		SpinUpSpinSpeed = 3.2,

		FateEngineScale = 1.5, -- blueprint §2.2
		ExpeditionGateScale = 2.0, -- blueprint §2.2
	},

	Events = {
		-- Late joiners receive the active event snapshot plus this many recent
		-- announcements, so someone joining a live server sees what just happened.
		AnnouncementBufferSize = 8,
		AnnouncementBufferMaxAgeSeconds = 300,
		FatebreakDurationSeconds = 300, -- STARFALL, Master Spec §12
		CrossServerTopic = "LUCKBOUND_Fatebreak_v1",
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
