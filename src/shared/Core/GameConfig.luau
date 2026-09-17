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
		-- Rolls 1..#OnboardingSequence are forced, in order. Roll #(n+1) onward
		-- is pure chance, forever.
		--
		-- Two rules shape this sequence:
		--
		-- 1. IT NEVER HANDS OUT A MYTHIC. A guaranteed top tier devalues the
		--    top tier permanently, and the Fatebreak announcement (§12) depends
		--    on Mythic meaning something. The arc peaks on Epic at roll 8;
		--    Astral Reach must be earned from honest odds.
		--
		-- 2. IT APPROXIMATES THE REAL ODDS. Counted out, this is 9 Common,
		--    1 Uncommon, 4 Rare, 1 Epic -- 60/7/27/7 against true RNG's
		--    60/15/15/7/3. A front-loaded parade of rares followed by a wall of
		--    Commons would make roll 16 feel like a punishment. Ending on a
		--    Common means the handover is continuous: the player has already
		--    felt what normal is.
		--
		-- The valleys are the point. Rares land at 3, 6, 11 and 14 with Commons
		-- between them, so each one reads as a lift rather than an entitlement.
		--
		-- Slot 5 is Ethereal Scape (Uncommon), added when that world was. It
		-- does three things at once: it teaches the second rung of the ladder,
		-- it guarantees every player SEES the map-generation test biome inside
		-- the first minute instead of waiting on a 15% draw, and it drops the
		-- scripted Common share from 66.7% to 60.0% -- which is exactly the
		-- true rate, so the handover at roll 16 is now seamless rather than
		-- merely close. The arc still peaks on Epic at roll 8 and still never
		-- hands out a Mythic; D-9 is extended, not reversed.
		OnboardingSequence = {
			"VERDANT_VALLEY", -- 1  Common -- tutorial
			"VERDANT_VALLEY", -- 2  Common -- establish the baseline
			"EMBERFALL", -- 3  Rare   -- first lift
			"VERDANT_VALLEY", -- 4  Common -- back to normal, so 5 reads as a lift
			"ETHEREAL_SCAPE", -- 5  UNCOMMON -- the small lift; teaches tier 2
			"EMBERFALL", -- 6  Rare   -- rare is real, not a fluke
			"VERDANT_VALLEY", -- 7  Common
			"SKY_CITADEL", -- 8  EPIC   -- the peak of the arc
			"VERDANT_VALLEY", -- 9  Common
			"VERDANT_VALLEY", -- 10 Common
			"EMBERFALL", -- 11 Rare
			"VERDANT_VALLEY", -- 12 Common
			"VERDANT_VALLEY", -- 13 Common
			"EMBERFALL", -- 14 Rare   -- last lift before the handover
			"VERDANT_VALLEY", -- 15 Common -- end on baseline, so roll 16 is continuous
		},

		-- Only the first few rolls are a genuine tutorial, so only those get
		-- short expeditions. The rest of the onboarding arc runs at full length
		-- -- 15 short expeditions would be a different game.
		ShortExpeditionRolls = 3,
		OnboardingExpeditionSeconds = 100,

		RollCooldownSeconds = 3.0, -- D-3
		MaxRollDistance = 140, -- studs from RollAnchor; scaled with the plinth
		RollHistoryCap = 50, -- D-6

		-- Phase 1 pool weights, keyed by world Id. Used only while CurrentPhase
		-- is 1. Set to nil to use each world's canonical full-game RollWeight.
		-- Sums to 10000, so these read directly as percentages:
		-- Common 60%, Uncommon 15%, Rare 15%, Epic 7%, Mythic 3%.
		--
		-- Adding a fifth world forced a renormalisation -- the set has to keep
		-- summing to 10000 or the numbers stop reading as percentages. The
		-- 5 points came off Verdant Valley (70 -> 60) and Emberfall (20 -> 15)
		-- rather than off the top tiers, because Epic and Mythic rates are the
		-- ones a player forms an opinion about and they are unchanged.
		PrototypeWeights = {
			VERDANT_VALLEY = 6000,
			ETHEREAL_SCAPE = 1500,
			EMBERFALL = 1500,
			SKY_CITADEL = 700,
			ASTRAL_REACH = 300,
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
		-- THE PHASE 2 SWITCH. Build spec §7 excludes expedition entry from
		-- Phase 1; this flag is the amendment that opens it (spec §7.1), and
		-- turning it off returns the game to Phase 1 behaviour exactly -- the
		-- Gate's prompt disappears and Expedition_RequestEnter is dropped.
		Enabled = true,

		-- D-7: PDF §6 says 12 minutes. Flagged as likely too long for a
		-- proof-of-concept tester; revisit before Phase 2 playtests. A world
		-- may override it (WorldDefinition.DurationSeconds) and Ethereal Scape
		-- does, at 300.
		DefaultDurationSeconds = 720,
		ReturnGraceSeconds = 10,

		-- Generated maps are built high above the hub rather than beside it.
		-- The hub's scenery reaches HubLayout.VisualExtent (4000 studs) in the
		-- X/Z plane, so anything at ground level would be visible from the
		-- Crossroads; 20000 studs up is out of every sightline and out of fog
		-- range in both directions.
		StageOrigin = Vector3.new(0, 20000, 0),
		-- Concurrent expeditions are spaced along +X. Wider than any layout
		-- can span (a path-length-8 map is ~6000 studs) with room to spare.
		StageSpacing = 12000,
		MaxConcurrent = 12,

		-- Default map size. A world overrides it with MapPathLength.
		PathLength = 5,
		-- A layout can legitimately fail when the path folds back on itself;
		-- that is seed-dependent, so try a few before rejecting. 5 attempts
		-- succeeds ~98% of the time -- see docs/MODULAR_MAPS.md.
		AssemblyAttempts = 5,

		EntryCooldownSeconds = 2.0,
		-- Studs from the Expedition Gate's portal plane. Generous, because the
		-- Gate platform is 290x240 and the prompt is the real affordance --
		-- this check exists to stop remote-spam from spawn, not to be precise.
		MaxEntryDistance = 260,

		-- Blockout geometry for a chunk whose mesh is still PLACEHOLDER.
		FloorThickness = 8,
		RimHeight = 10,
		RimThickness = 6,
		SocketMarkerHeight = 26,
		SpawnHeight = 10, -- above a chunk floor, when placing the character

		TimerSyncSeconds = 5,
		-- The return portal on the arrival chunk. Small: it is a door home,
		-- not a monument, and it must not upstage the Sky Temple.
		ReturnPortalScale = 3.0,
		-- Must exceed the return plinth's radius (PlinthDiameter * scale / 2)
		-- or the way home is unusable from on top of it -- the same mistake
		-- the Expedition Gate shipped with. Asserted by test.
		ReturnPromptDistance = 40,
	},

	-- === WORLD SCALE ===
	-- A Roblox character is about 5 studs tall and walks 16 studs/second by
	-- default. Those two numbers decide everything here.
	--
	-- THE BUDGET. Traversal must stay under ~20 seconds to any hub location.
	-- Measured centre-to-centre:
	--
	--   hub Ø    zone r    @16      @32      @40
	--     120        42    2.6s     1.3s     1.1s   (the old hub -- 24 chars across)
	--    1200       420   26.2s    13.1s    10.5s   <- chosen
	--    2000       700   43.8s    21.9s    17.5s
	--    4000      1400   87.5s    43.8s    35.0s   (unwalkable at any sane speed)
	--
	-- So the PLAYABLE footprint is 1200 studs and movement is doubled to 32.
	-- The world still READS as 4000+ studs across, because the floating
	-- islands and skybox extend far past anything you can walk to. Big world,
	-- short walks -- they are separate numbers and must not be conflated.
	--
	-- Centre-to-centre overstates the real walk: from the edge of the Fate
	-- Engine platform to the edge of a zone is about 140 studs, roughly 4.4s.
	Scale = {
		CharacterHeight = 5, -- reference only; Roblox R15 is ~5 studs
		WalkSpeed = 32, -- doubled from Roblox's default 16
		MaxTraversalSeconds = 20, -- hard budget, asserted by test
	},

	-- Hub geometry. Biome Blueprint §2.1 and §7.3: named anchors live here and
	-- are never re-derived per script, so the axis mapping is confirmed once in
	-- Studio and locked. Roblox is Y-up, so "compass" is the X/Z plane:
	--   NORTH = -Z, SOUTH = +Z, EAST = +X, WEST = -X, UP = +Y.
	-- Visual detail (materials, palette, props) lives in Content/Hub/Crossroads.
	HubLayout = {
		-- 1200 was one playtest ago. The owner's verdict on walking it was
		-- "much better, could be slightly smaller, perhaps just a tad" -- so
		-- 50 studs came off the diameter rather than a wholesale re-tune.
		HubDiameter = 1150, -- playable extent
		VisualExtent = 4000, -- how far scenery reaches; not walkable
		PlazaRingWidth = 200,
		WalkwayWidth = 44,
		-- 6 -> 1.5. The authored dais is only ~2 studs proud of the hub floor
		-- (its 4.21 raw thickness at Prefab.Scale), so walkways raised 6 ran
		-- OVER the top of it and buried the platform the Engine stands on --
		-- reported from the second authored playtest. The deck now sits just
		-- under the dais lip and the player steps up onto it.
		WalkwayRaise = 1.5, -- studs above the lower plaza ring

		-- The invisible pad the Gate's ENTER prompt lives on, as a multiple of
		-- the portal's scale, and how far above the platform it floats.
		GateAnchorSpan = 8,
		GateAnchorLift = 2,
		ProcessionalWidth = 72, -- the Expedition Gate approach is wider
		-- 400, not 420: the plaza lost 25 studs of radius and a zone platform
		-- must not hang off the edge of the floor it stands on. Furthest
		-- platform edge is now 400 + 160 = 560 against a 575-stud plaza.
		ZoneRingRadius = 400, -- centre of hub → centre of a compass zone

		Anchors = {
			FATE_ENGINE = Vector3.new(0, 0, 0),
			HALL_OF_LEGENDS = Vector3.new(0, 0, -400), -- north
			DISCOVERY_ARCHIVE = Vector3.new(400, 0, 0), -- east
			EXPEDITION_GATE = Vector3.new(0, 0, 400), -- south
			TRAINING_GROUNDS = Vector3.new(-400, 0, 0), -- west
		},

		-- ON the processional, not inside it. At (0, 8, 250) the spawn sat
		-- within the walkway's own volume, so Roblox ejected the character
		-- upward -- which is how a playtest began on top of a pillar. Y is now
		-- clear of the deck and the SpawnLocation does not collide, so the
		-- player simply drops the last couple of studs onto the walkway.
		SpawnAnchor = Vector3.new(0, 14, 250), -- south of centre, facing the Engine
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

		-- A HARD CEILING ON THE STEP UP, in studs, regardless of scale.
		-- A Roblox character jumps about 7 studs; the Gate's uncapped plinth
		-- stood 18 and walled the portal off completely. Width still scales
		-- with the rig, so it stays monumental -- only the step is capped.
		MaxPlinthHeight = 3,

		IdleParticleRate = 8,
		ActiveParticleRate = 40,
		SpinUpParticleRate = 200,
		ParticleLifetimeMin = 1.5,
		ParticleLifetimeMax = 3,

		-- HOW HARD THE NEON IS DRIVEN. Roblox's Neon material emits at the
		-- part's full Color and bloom amplifies it, so a rarity colour applied
		-- raw blows out into a halo that swallows the mesh detail behind it --
		-- reported from the first authored playtest. Tinting the colour down
		-- before it reaches a Neon part keeps the hue and gives the geometry
		-- back. Transparency would not work here: Neon ignores it.
		NeonTint = 0.55,

		IdleBrightness = 1,
		ActiveBrightness = 3,
		LightRange = 24,

		PlanePulseMin = 0.3,
		PlanePulseMax = 0.7,
		PlanePulseSeconds = 2.4,

		-- The single most important UX beat in the game (master spec §25,
		-- blueprint §1.3). Never make it instant.
		SpinUpSeconds = 2.5,
		-- 0.15 was one revolution every 42 SECONDS. On the blockout's 28 visible
		-- segments that read as a slow hum; on an authored ring, which is
		-- near rotationally symmetric, it is invisible -- the first playtest
		-- of the authored Engine reported it as "static, non moving".
		-- 0.6 is a revolution every 10s: clearly turning, still not a fan.
		IdleSpinSpeed = 0.6, -- rad/s
		SpinUpSpinSpeed = 3.2,

		-- The blueprint's 1.5x/2.0x were relative to a 120-stud hub; the RATIO
		-- is what it was specifying, and that is preserved (the gate is still
		-- the larger).
		--
		-- Reduced from 9.0/12.0 after the first playtest: "structures now
		-- shifted to be a bit too large". The binding constraint is no longer
		-- taste, though -- it is reach. A plinth is PlinthDiameter * scale
		-- across, and the prompt on it only reaches
		-- UI.PromptActivationDistance, so any scale above 10 puts the edge of
		-- the plinth outside its own prompt's range. Asserted by test, for
		-- every portal in the hub rather than just the Engine.
		-- 6.0 -> 1.25 when the authored Engine was re-tuned to ~4.5x player
		-- height. The blockout is a STAND-IN for the authored rig, so it has
		-- to be the same size: 9 * 1.25 = an 11.25-stud ring radius, against
		-- the authored ring's 11.25. A place with no Rojo now looks
		-- proportionally like the real thing rather than like a different
		-- game -- and the platform the walkways meet is the same either way.
		FateEngineScale = 1.25,
		ExpeditionGateScale = 8.0,
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
		PromptActivationDistance = 70, -- the plinth alone is ~126 studs across
	},

	Debug = {
		-- === DEVELOPER COMMANDS -- NEVER SHIP EITHER OF THESE TRUE ===
		--
		-- Both are ON for the current testing phase, at the owner's request,
		-- and both are belt-and-braces gated at the point of use: DebugSystem
		-- additionally requires RunService:IsStudio() or the place creator, so
		-- flipping these on a live place still does not hand commands to a
		-- stranger. Turn them off before the place is public anyway -- defence
		-- in depth is not a reason to leave the front door open.
		AllowCommands = true,
		AllowForcedRolls = true,

		-- How fast /fly moves, in studs per second.
		FlySpeed = 120,
		-- Guard rails on /speed, so a typo does not launch the character into
		-- the skybox and require a rejoin.
		MinWalkSpeed = 1,
		MaxWalkSpeed = 500,

		LogEveryRoll = true,
	},
}

return deepFreeze(GameConfig)
