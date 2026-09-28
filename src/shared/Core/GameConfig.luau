--!strict
-- EVERY tunable number in LUCKBOUND lives here. Build spec §6.
-- Rule: if a designer might want to change it, it belongs in this file.
-- A magic number inside a System is a spec violation.

local Freeze = require(script.Parent.Freeze)
local deepFreeze = Freeze.deep

-- === THE WORLD SCALE ===
-- Owner-directed 2026-09-21, after measuring the hub against a player.
--
-- The authored Crossroads shipped at Prefab.Scale 2.0, and at that scale the
-- shop counters stood 6.00 studs and the railings 6.70 against a character
-- that is about 5 studs tall. You could not see over either. Three
-- independent human-scale props agreed the set dressing was twice the size it
-- should be -- the delivery was measured against the BRIEF rather than
-- against a person, and the brief's stud assumption was off.
--
-- So the whole world is halved, through this one number. Every distance below
-- that positions something on or around the authored shell is derived from it,
-- and so are the two prefab scales in Content/Hub/Crossroads. The test suite
-- pins the coupling from the other end: the authored mesh's own measurements,
-- times the prefab scale, must equal the layout numbers here. Change this
-- alone and four tests fail by name.
--
-- 1.0 restores the world exactly as it shipped before this change.
local WORLD_SCALE = 0.5

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
		MaxRollDistance = 140 * WORLD_SCALE, -- studs from RollAnchor; scaled with the plinth
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
		PathLength = 8,
		-- How far a branch off a spare mouth runs before it dead-ends in a
		-- cap. Owner-directed 2026-09-23: an intersection whose side mouths
		-- are capped where they stand is not an intersection. 0 restores that.
		BranchLength = 2,
		-- How ChunkLoader finds which way a delivered mesh faces: a ray just
		-- inside each socket's mouth (Inset studs), cast from Height above the
		-- walk plane, must land within Tolerance of it. Visual only -- the
		-- layout and its randomness are decided before this runs.
		-- Tolerance 6: the kit reference puts the SKYWAY deck at 0..3.2, so 3
		-- sat on the edge of rejecting a correct turn.
		-- Inset 2: a bridge reaches the tile edge; an island deck usually stops
		-- short of it, so probing right at the edge is what separates them.
		SocketProbe = { Inset = 2, Height = 20, Tolerance = 6, EdgeMargin = 8 },
		-- No piece more than this many times per map (caps excepted), and never
		-- twice in a row. Owner-directed 2026-09-23: repeats read as messy.
		MaxRepeats = 2,

		-- === Scenario layer (build spec §7.3) ====================
		-- RESTORED 2026-09-23. This block was silently deleted by merge
		-- f9dec00 -- a conflict hunk resolved in favour of the other side --
		-- and nothing noticed, because ScenarioCore had no runtime caller and
		-- only the test suite read these. Schema.validateConfig now requires
		-- all three, so losing them again is a BOOT error rather than a
		-- crash 400 tests into a run.
		-- What HAPPENS in a chunk, decided separately from which chunk it is.
		-- Every number here is a pacing dial, which is exactly why none of
		-- them live in ScenarioCore.
		--
		-- How often Fate overrides ordinary weighting and picks from the rare
		-- band regardless of pacing. The brief asks for "uncommon enough to
		-- feel special"; at 6% a five-room run sees one about a quarter of the
		-- time, which is rare enough to be worth mentioning and common enough
		-- that players learn it exists. Set 0 to switch Fate intervention off.
		FateInterventionChance = 0.06,
		-- How many recent (chunk, scenario) PAIRS to remember when damping
		-- repeats. Pairs, not chunk ids: a place reappearing is fine when
		-- something different happens in it.
		ScenarioRecentMemory = 6,
		-- Fraction of the path after which the rare band unlocks and uncommon
		-- is favoured. Below it a run stays legible; above it, it escalates.
		ScenarioEscalateFrom = 0.4,
		-- The scenario layer draws from its own stream, offset well past the
		-- assembly attempts, so adding or removing a scenario can never shift
		-- which CHUNKS a seed picks. Keep it larger than AssemblyAttempts.
		ScenarioStreamOffset = 1000,
		-- Hang one SIDE pocket off a spare socket when a kit has one (Biome
		-- Blueprint §6). Off returns maps to exactly the critical path.
		IncludeSide = true,
		-- A layout can legitimately fail when the path folds back on itself;
		-- that is seed-dependent, so try a few before rejecting. 5 attempts
		-- succeeds ~98% of the time -- see docs/MODULAR_MAPS.md.
		-- 12 since §7.7 (2026-09-27): a blueprint map is bigger and collides more often.
		-- Only a FAILED attempt consumes another, so a seed that already built is unchanged.
		AssemblyAttempts = 12,

		-- ENTRY LIVES ON THE FATE ENGINE. Owner-directed 2026-09-21: the
		-- staircase up to the portal is not modelled yet, but the teleport
		-- and the biome scripts need testing now -- so the portal is
		-- enterable from the dais and the stairs become art rather than a
		-- blocker.
		--
		-- This is the direction STATUS already records ("the Engine portal is
		-- to become the way into biomes"), arriving early and without the
		-- "keep this biome?" step, which still needs a spec amendment.
		EntryAtEngine = true,
		-- A different key from ROLL: both prompts stand on the same dais and
		-- every ProximityPrompt defaults to E. Checked against
		-- Constants.HOTKEY_NAMES like every other key in content.
		EntryPromptKey = "F",

		EntryCooldownSeconds = 2.0,
		-- Studs from the Expedition Gate's portal plane. Generous, because the
		-- Gate platform is 290x240 and the prompt is the real affordance --
		-- this check exists to stop remote-spam from spawn, not to be precise.
		MaxEntryDistance = 260 * WORLD_SCALE,

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

		-- === EXPEDITIONS AS THEIR OWN SERVER ================================
		-- Owner-directed 2026-09-22 (build spec §7.2): entering the centre
		-- portal starts a NEW Roblox server for the expedition, and a party
		-- leader entering brings the whole party into that same server.
		--
		-- "AUTO" teleports on a live server and builds in place in Studio,
		-- where TeleportService cannot run -- so a Studio test still walks
		-- the whole loop, parties included, just without the hop.
		-- "TELEPORT" and "IN_PLACE" force one or the other.
		InstanceMode = "AUTO",
		-- The place the expedition server runs. 0 means THIS place: a
		-- reserved server of the hub's own place, which boots, sees it is a
		-- reserved server, and becomes an expedition host instead of a hub.
		-- One place file, one Rojo project, nothing extra to publish. Set a
		-- real place id here only if expeditions ever move to a place of
		-- their own in the same universe.
		InstancePlaceId = 0,
		-- The place players are sent back to. 0 means the place this server
		-- is running, which is right while hub and expedition share one.
		HubPlaceId = 0,
		-- How long the expedition's manifest lives in MemoryStore. Only has
		-- to outlast the teleport; generous so a slow hop never strands a
		-- party on a server that cannot find out what it is for.
		ManifestTtlSeconds = 900,
		-- How long a freshly booted expedition server keeps asking for its
		-- manifest before giving up and sending everyone home.
		ManifestWaitSeconds = 20,
		ManifestPollSeconds = 1,
		TeleportAttempts = 3,
		TeleportRetrySeconds = 1.5,
		-- Party members arrive a few studs apart rather than inside one
		-- another. Radius of the ring they are placed on.
		ArrivalSpreadStuds = 6,
	},

	-- === PARTIES =========================================================
	-- Owner-directed 2026-09-22. The roll stays personal; a party travels on
	-- its LEADER's roll, so everyone enters the same world, seed and map.
	Party = {
		Enabled = true,
		MaxSize = 4,
		-- An unanswered invite lapses rather than sitting in someone's list
		-- forever. Long enough to finish a roll reveal and answer.
		InviteExpirySeconds = 60,
		-- Spam guard on Party_Request, same fixed-window limiter as travel.
		RequestsPerMinute = 40,
		-- After an expedition, members come home in one teleport and the
		-- party is rebuilt when they land. A member who has not arrived
		-- within this long is no longer waited for.
		ReuniteWindowSeconds = 120,
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
		-- 32 -> 24. The doubling existed because the world was twice player
		-- scale: a 1150-stud hub needed a 2x walk to stay inside the budget,
		-- and at WORLD_SCALE that compensation comes off with it.
		--
		-- Not all the way to Roblox's 16, and the reason is Ethereal Scape:
		-- the biomes are authored at PLAY scale and were always correct, so
		-- they were sized against this number rather than against the
		-- oversized hub. Dropping to 16 would turn a 95-second traverse into
		-- 142 and make an authored map read as a hike. 24 keeps the hub brisk
		-- (8.3s centre to district, well inside the 20s budget) and leaves
		-- the biomes as they were designed.
		WalkSpeed = 24,
		MaxTraversalSeconds = 20, -- hard budget, asserted by test
	},

	-- Hub geometry. Biome Blueprint §2.1 and §7.3: named anchors live here and
	-- are never re-derived per script, so the axis mapping is confirmed once in
	-- Studio and locked. Roblox is Y-up, so "compass" is the X/Z plane:
	--   NORTH = -Z, SOUTH = +Z, EAST = +X, WEST = -X, UP = +Y.
	-- Visual detail (materials, palette, props) lives in Content/Hub/Crossroads.
	-- Client-side hub animation. These exist because the hub animator runs
	-- every frame on every player's machine, including the low-end phones the
	-- §6 checklist budgets for, and the first authored playtest already
	-- reported it "slightly choppy" in Studio on a desktop.
	Effects = {
		-- Beyond this, a part stops animating entirely. The hub is 1150 studs
		-- across and scenery reaches 4000, so most of what is tagged is off
		-- screen or a speck for most of the session.
		AnimationDistance = 700 * WORLD_SCALE,
		-- How often the distance check itself runs. Doing it per part per
		-- frame would cost more than the animation it is protecting.
		CullIntervalSeconds = 0.5,
		-- Size and Transparency are far more expensive to write than CFrame --
		-- a Size change on a MeshPart re-scales the mesh. 20 Hz is
		-- indistinguishable from 60 for a slow breath and a third of the work.
		SlowUpdateSeconds = 0.05,
	},

	HubLayout = {
		-- Read by Content/Hub/Crossroads so the authored mesh and the numbers
		-- that position things on it can never disagree about the scale.
		WorldScale = WORLD_SCALE,

		-- 1200 was one playtest ago. The owner's verdict on walking it was
		-- "much better, could be slightly smaller, perhaps just a tad" -- so
		-- 50 studs came off the diameter rather than a wholesale re-tune.
		HubDiameter = 1150 * WORLD_SCALE, -- playable extent
		VisualExtent = 4000 * WORLD_SCALE, -- how far scenery reaches; not walkable
		PlazaRingWidth = 200 * WORLD_SCALE,
		WalkwayWidth = 44 * WORLD_SCALE,
		-- 6 -> 1.5. The authored dais is only ~2 studs proud of the hub floor
		-- (its 4.21 raw thickness at Prefab.Scale), so walkways raised 6 ran
		-- OVER the top of it and buried the platform the Engine stands on --
		-- reported from the second authored playtest. The deck now sits just
		-- under the dais lip and the player steps up onto it.
		WalkwayRaise = 1.5 * WORLD_SCALE, -- studs above the lower plaza ring

		-- The invisible pad the Gate's ENTER prompt lives on, as a multiple of
		-- the portal's scale, and how far above the platform it floats.
		GateAnchorSpan = 8,
		GateAnchorLift = 2 * WORLD_SCALE,
		ProcessionalWidth = 72 * WORLD_SCALE, -- the Expedition Gate approach is wider
		-- 400, not 420: the plaza lost 25 studs of radius and a zone platform
		-- must not hang off the edge of the floor it stands on. Furthest
		-- platform edge is now 400 + 160 = 560 against a 575-stud plaza.
		ZoneRingRadius = 400 * WORLD_SCALE, -- centre of hub → centre of a compass zone

		-- THE CROSSROADS v2 (2026-09-23). Used when HUB_CROSSROADS_V2 is in the
		-- place; the old authored shell and the blockout remain the fallback.
		-- Positions come from Content/Hub/CrossroadsV2 (its districts sit at
		-- 218, not ZoneRingRadius, which still describes the old shell).
		V2 = {
			Enabled = true,
			DeckHeight = 0.5, -- a district's floor above the plaza
			SignLift = 34, -- a district's name, above its deck
			-- Labels in the new hub; the zone ids stay as they are.
			Names = {
				HALL_OF_LEGENDS = "Hall of Champions",
				DISCOVERY_ARCHIVE = "Archives",
				EXPEDITION_GATE = "Shop",
				TRAINING_GROUNDS = "Training Grounds",
			},
			Backdrop = {
				Count = 12,
				RadiusMin = 1150,
				RadiusMax = 1700,
				HeightMin = -260,
				HeightMax = 40,
				ScaleMin = 0.8,
				ScaleMax = 1.35,
			},
			-- THE SKY BEYOND (HUB_SKY). The cloud sea is the cloud props' own
			-- puffs as wide banks, in two drifting layers; the far range is the
			-- backdrop chunks again, huge and darkened, so the islands have a
			-- horizon behind them.
			CloudSea = {
				{
					Count = 30,
					Y = -340,
					RadiusMax = 2100,
					ScaleMin = 1.3,
					ScaleMax = 2.4,
					Drift = 0.004,
				},
				{
					Count = 12,
					Y = -250,
					RadiusMax = 1600,
					ScaleMin = 0.9,
					ScaleMax = 1.6,
					Drift = -0.006,
					Detail = 2,
				},
			},
			FarRange = {
				Count = 14,
				RadiusMin = 3200,
				RadiusMax = 4600,
				HeightMin = -520,
				HeightMax = -120,
				ScaleMin = 2.2,
				ScaleMax = 3.2,
				Tint = Color3.fromRGB(116, 104, 150),
			},
			Moon = {
				Azimuth = 40,
				Elevation = 26,
				Distance = 4200,
				Scale = 6.5,
				Color = Color3.fromRGB(240, 230, 252),
			},
			Planet = { Azimuth = 205, Elevation = 32, Distance = 4700, Scale = 5 },
			Ring = {
				Height = 430,
				Spin = 0.04,
				BeamFrom = 60,
				GlyphA = Color3.fromRGB(124, 245, 224),
				GlyphB = Color3.fromRGB(182, 131, 255),
			},
			-- Drawn at random per server. Detail: 1 on every device, 2 from
			-- medium graphics, 3 high only (extra copies step up one level).
			-- Speed is studs/second along the orbit.
			Docking = {
				BerthPadding = 2, -- keep the clearance box off the island face
				InitialDelayMin = 30,
				InitialDelayMax = 90,
				RetryDelayMin = 20,
				RetryDelayMax = 40,
				FailedApproachDelayMin = 30,
				FailedApproachDelayMax = 60,
				DepartureDelayMin = 60,
				DepartureDelayMax = 140,
				HoldMin = 12,
				HoldMax = 25,
				ArrivalDistance = 6,
				SlowdownRate = 0.4,
				StuckMinSeconds = 12,
				ApproachTurnRadians = math.pi,
			},
			Orbiters = {
				{
					Names = {
						"hubprop_ship_sloop",
						"hubprop_ship_cutter",
						"hubprop_ship_trawler",
						"hubprop_ship_cog",
						"hubprop_ship_yacht",
					},
					Min = 4,
					Max = 7,
					Detail = 1,
					RadiusMin = 360,
					RadiusMax = 620,
					HeightMin = -40,
					HeightMax = 90,
					SpeedMin = 22,
					SpeedMax = 38,
					Faces = true,
					Bob = 2,
				},
				{
					Names = { "hubprop_ship_galleon", "hubprop_ship_carrier" },
					CanDock = true,
					Min = 1,
					Max = 2,
					Detail = 2,
					-- above the hub and clear of the mountains' reach, so nothing boxes them in
					RadiusMin = 480,
					RadiusMax = 720,
					HeightMin = 200,
					HeightMax = 300,
					SpeedMin = 16,
					SpeedMax = 26,
					Faces = true,
					Bob = 3,
				},
				{
					Names = { "hubprop_sky_whale" },
					Min = 1,
					Max = 2,
					Detail = 2,
					RadiusMin = 480,
					RadiusMax = 820,
					HeightMin = -120,
					HeightMax = 40,
					SpeedMin = 15,
					SpeedMax = 25,
					Faces = true,
					Bob = 6,
					ScaleMin = 1,
					ScaleMax = 1.6,
				},
				{
					Names = { "hubprop_isle_shrine", "hubprop_isle_grove", "hubprop_isle_ruin" },
					Min = 4,
					Max = 6,
					Detail = 1,
					RadiusMin = 380,
					RadiusMax = 700,
					HeightMin = -90,
					HeightMax = 60,
					SpeedMin = 2,
					SpeedMax = 4,
					Bob = 3,
					ScaleMin = 0.9,
					ScaleMax = 1.5,
				},
				{
					Names = { "hubprop_cloud_a", "hubprop_cloud_b" },
					Min = 8,
					Max = 12,
					Detail = 2,
					RadiusMin = 330,
					RadiusMax = 900,
					HeightMin = -160,
					HeightMax = 120,
					SpeedMin = 3,
					SpeedMax = 6,
					ScaleMin = 0.8,
					ScaleMax = 2.2,
				},
				{
					Names = { "hubprop_crystal_cluster", "hubprop_waystone", "hubprop_rune_ring" },
					Min = 4,
					Max = 7,
					Detail = 2,
					RadiusMin = 330,
					RadiusMax = 600,
					HeightMin = -60,
					HeightMax = 100,
					SpeedMin = 3,
					SpeedMax = 6,
					Bob = 2,
				},
				{
					Names = { "hubprop_sky_lantern" },
					Min = 10,
					Max = 18,
					Detail = 3,
					RadiusMin = 320,
					RadiusMax = 500,
					HeightMin = 10,
					HeightMax = 110,
					SpeedMin = 3,
					SpeedMax = 5,
					Bob = 1.5,
				},
			},
		},

		Anchors = {
			FATE_ENGINE = Vector3.new(0, 0, 0),
			HALL_OF_LEGENDS = Vector3.new(0, 0, -400 * WORLD_SCALE), -- north
			DISCOVERY_ARCHIVE = Vector3.new(400 * WORLD_SCALE, 0, 0), -- east
			EXPEDITION_GATE = Vector3.new(0, 0, 400 * WORLD_SCALE), -- south
			TRAINING_GROUNDS = Vector3.new(-400 * WORLD_SCALE, 0, 0), -- west
		},

		-- WHERE PLAYERS ARRIVE. A RING AROUND THE ENGINE, not a single pad.
		--
		-- Owner-directed after the first authored walk. One spawn 250 studs
		-- down the processional meant every player began with the same long
		-- walk to the only interactive thing in the game; arriving at the
		-- Engine's edge puts them in front of it immediately, which is what
		-- the Master Spec's "first frame must contain the thing the game is
		-- about" was always after.
		--
		-- Radius clears the dais rather than guessing: the authored Platform
		-- is 46.9 studs across, so 34 stands a player just off its rim with
		-- room for several to arrive at once without stacking. Count is 8 so
		-- the ring covers the four walkway mouths AND the four diagonals --
		-- half arrive on a path, half on the open plaza, both walkable.
		--
		-- Height is above the deck, never inside it. At (0, 8, 250) the spawn
		-- once sat within the walkway's own volume, so Roblox ejected the
		-- character upward -- which is how a playtest began on top of a
		-- pillar. The pads do not collide, so the player simply drops the
		-- last couple of studs.
		SpawnRing = {
			Count = 8,
			-- ARRIVE OUTSIDE EVERY PROMPT'S REACH. Owner-directed 2026-09-21:
			-- a player was being offered ROLL before they had pressed PLAY,
			-- which both spoils the loading screen and skips the moment where
			-- a tutorial would explain what rolling IS.
			--
			-- 34 stood them on the dais rim, inside the Engine's prompt. This
			-- is well outside PromptActivationDistance (35 at WorldScale) and
			-- outside MaxRollDistance (70), so nothing is offered until they
			-- choose to walk in -- which is the room a first-join tutorial
			-- needs. It is still short of the districts at 200, so the Engine
			-- is what they are looking at.
			--
			-- Asserted against the prompt reach by test rather than written
			-- as a bare number, because the two must not drift.
			-- 110 -> 105: five studs in, asked for after the fourth walk. Still
			-- outside PromptActivationDistance (17.5) and MaxRollDistance
			-- (35), which is what the tests pin.
			Radius = 105,
			Height = 6 * WORLD_SCALE,
		},
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

		-- How long a rarity change takes to cross the rig. Snapping the whole
		-- portal to a new colour on one frame read as a texture swap rather
		-- than as the portal reacting -- reported from the fourth authored
		-- playtest. Long enough to see it travel, short enough not to lag the
		-- reveal it belongs to.
		RarityTweenSeconds = 1.6,

		-- THE ROLL RAMP. The rings wind up when you roll, hold while the
		-- result builds, then coast back down as the portal settles on the
		-- world you got. Before this the authored Engine had no reaction at
		-- all: HubEffects drives its rings off attributes and never read the
		-- State flag PortalRig sets, so the whole spin-up beat missed it.
		SpinBoostPeak = 5.5, -- multiplier on the idle rate at full wind-up
		SpinRampUpSeconds = 1.1, -- idle -> peak, as the roll begins
		SpinWindDownSeconds = 2.6,

		-- THE PORTAL TURNS TO FACE YOU, AND STOPS SOMEWHERE MEANINGFUL.
		--
		-- The rings spin about their own axle like a wheel. The portal ASSEMBLY
		-- -- both rings, the veil and the levitation core -- also turns about the
		-- vertical, so the aperture sweeps the hub instead of facing one way
		-- forever. Owner-directed after the third walk.
		--
		-- Matched to OuterRing's own SpinSpeed (0.22 rad/s) so the two read as
		-- one mechanism rather than two. It rides the same SpinBoost ramp the
		-- rings do, so a roll winds it up for free.
		YawIdleSpeed = 0.22,
		-- ...and where it is allowed to stop. Four slots, so the portal always
		-- comes to rest square to the hub -- facing a walkway, which is where a
		-- staircase up to it would have to land.
		YawSlots = 4, -- peak -> idle, as the result lands

		-- Halved with the world for the same inverse-square reason as the
		-- Engine's spotlight: a light that did not move away from a surface
		-- that came closer is a brighter light.
		IdleBrightness = 0.5,
		ActiveBrightness = 1.5,
		LightRange = 24 * WORLD_SCALE,

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
		FateEngineScale = 1.25 * WORLD_SCALE,
		ExpeditionGateScale = 8.0 * WORLD_SCALE,
	},

	Events = {
		-- Late joiners receive the active event snapshot plus this many recent
		-- announcements, so someone joining a live server sees what just happened.
		AnnouncementBufferSize = 8,
		AnnouncementBufferMaxAgeSeconds = 300,
		FatebreakDurationSeconds = 300, -- STARFALL, Master Spec §12

		-- === THE SKY LAYER ===
		-- How far an event's weather reaches. It used to emit from a
		-- one-stud part over the Fate Engine, so the motes fell on the dais
		-- and nowhere else -- the fifth walk reported the effect as being
		-- "only over the Fate Engine".
		--
		-- A ParticleEmitter emits across its part, so the part has to be the
		-- size of the thing being weathered: the whole plaza, with a margin
		-- so the edges are not obviously a square.
		SkySpanFactor = 1.35, -- multiple of HubLayout.HubDiameter
		SkyHeight = 260, -- studs above the plaza, before WORLD_SCALE
		-- Rate in content is written per-event as a feel ("a Starfall is
		-- heavier than a Veil"). Spreading the same rate over the whole plaza
		-- instead of one dais would make every event a drizzle, so the area
		-- carries its own multiplier and the content numbers keep meaning
		-- what they meant.
		SkyRateScale = 8,
		CrossServerTopic = "LUCKBOUND_Fatebreak_v1",
	},

	-- === GLOBAL SCARCITY ===
	-- The ledger that makes "only N will ever exist" true across every server.
	-- Its numbers are separate from Save's because its failure rules are the
	-- opposite: a save that cannot reach a DataStore carries on without
	-- persistence, and a CLAIM that cannot reach one must be refused.
	Ledger = {
		Enabled = true,
		-- Fewer retries than a save, and shorter. A claim happens inside a
		-- roll the player is watching resolve; spending 30 seconds retrying
		-- would hold the reveal open. Three quick attempts, then refuse.
		MaxRetries = 3,
		RetryBackoffSeconds = 0.5,
		-- FAIL CLOSED. If the ledger cannot be reached, no unique is granted.
		-- Setting this true would hand out unique items that were never
		-- counted, which is unrecoverable -- there is no way to take one back
		-- once it has been announced to every server in the game.
		GrantWhenUnavailable = false,
	},

	Save = {
		AutosaveIntervalSeconds = 60,
		SessionLockTimeoutSeconds = 30,
		-- A teleport hands the profile from one server to another. The old
		-- server releases the lock just before the hop, but the new one can
		-- still ask first -- so a held lock is waited on for this long before
		-- the session is given up as non-persisting.
		LockWaitSeconds = 12,
		LockPollSeconds = 1.5,
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
		PromptActivationDistance = 70 * WORLD_SCALE, -- reach scales with the world
	},

	-- === LEADERBOARD ==================================================
	-- Replaces Roblox's player list with one in the house style
	-- (client/UI/Leaderboard.luau). THE COLUMNS ARE DATA: adding a stat is
	-- one row here plus the server setting that Player attribute. No UI code
	-- changes. Source is "RANK" (position in the sorted list), "NAME"
	-- (display name), or the name of any Player attribute. Width is pixels;
	-- a Width of 0 means "take the space that is left" (use it once).
	Leaderboard = {
		Enabled = true,
		ToggleKey = "Tab", -- an Enum.KeyCode name
		StartOpen = true,
		-- The flavour name, explained by the count beside it ("4 players"),
		-- so a new player reads what the panel is without being told the lore.
		Title = "FATEBOUND",
		CountSingular = "player",
		CountPlural = "players",
		Width = 260,
		RowHeight = 30,
		MaxVisibleRows = 10,
		-- The attribute to sort by, highest first. nil sorts by display name,
		-- which is what "rank" means until a real stat exists.
		SortBy = nil :: string?,
		Columns = {
			{ Header = "#", Source = "RANK", Width = 34 },
			{ Header = "PLAYER", Source = "NAME", Width = 0 },
			-- e.g. { Header = "LVL", Source = "FateLevel", Width = 44 },
		},
	},

	-- === CHAT =========================================================
	-- A chat window in the house style (client/UI/ChatPanel.luau). It sits on
	-- TextChatService, so Roblox's filtering and moderation still apply; only
	-- the default window and input bar are hidden. Bubble chat is untouched.
	Chat = {
		Enabled = true,
		FocusKey = "Slash", -- an Enum.KeyCode name
		Width = 380,
		Height = 220,
		MaxMessages = 60,
		-- Idle seconds before the panel dims to let the world through.
		FadeAfterSeconds = 8,
		FadedTransparency = 0.75,
		MaxLength = 200,
		-- The top-bar button that shows and hides the window.
		ToggleGlyph = "💬",
	},

	-- === THE HUB MENU =================================================
	-- The side rail, its panels, and the travel network. Behaviour only --
	-- every colour, radius, pad and tween length is a UITheme token, so a
	-- restyle never touches a number here and a retune never touches a colour.
	--
	-- THE MENU EXISTS ONLY IN THE CROSSROADS. Owner-directed: an expedition
	-- is meant to be the game, not a screen with the game behind it. The rule
	-- is enforced in one pure function (HubMenuCore.isVisible) so the client
	-- and the server agree on what "in the hub" means.
	HubMenu = {
		Enabled = true,

		-- Pixels the rail sits below the vertical centre, to clear the chat
		-- window in the top-left corner (GameConfig.Chat).
		RailOffsetY = 90,

		-- Start collapsed on a phone. The rail plus an open panel is most of a
		-- portrait screen, and the owner's note was explicit: the HUB must not
		-- be overwhelming. On desktop the rail is a sliver of a wide screen, so
		-- it opens expanded and the arrow is there for anyone who disagrees.
		StartCollapsedOnTouch = true,
		StartCollapsedOnDesktop = false,

		-- Opening a second panel closes the first. Two panels open at once is
		-- the fastest way to turn a clean rail into screen noise.
		SinglePanel = true,

		-- The rail hides itself during a roll so the game's most important
		-- four seconds are not framed by a menu. It comes back when the result
		-- card does.
		HideDuringRoll = true,
		-- ...and this long after the reveal resolves, so the rail sliding back
		-- in does not race the card sliding out.
		RestoreDelaySeconds = 0.35,

		-- === TRAVEL ===
		-- THERE IS NO COOLDOWN. Owner-directed 2026-09-20: travel should be
		-- quick and effectively instantaneous. The only thing between pressing
		-- TRAVEL and arriving is the fade that hides the swap, and it is short
		-- enough to read as a cut rather than as a wait.
		--
		-- What remains is a rate limit, and it is not a cooldown wearing a
		-- different name: at 60 a minute a player pressing the button as fast
		-- as they can will never see it, while a script firing the remote in a
		-- loop will. It exists to stop remote spam, nothing else.
		TeleportFadeOutSeconds = 0.22,
		TeleportHoldSeconds = 0.06,
		TeleportFadeInSeconds = 0.28,
		-- Rule 5 -- the destination Id is the ONLY thing the client is allowed
		-- to choose, and it must name a district that exists in Content. A
		-- client that asks to travel while on an expedition is refused.
		TeleportRequestsPerMinute = 60,

		-- WHERE A TRAVELLER ACTUALLY LANDS. Content names a landing point per
		-- district; the server drops a ray from ProbeHeight above it and
		-- stands the player on whatever it hits, so an authored district whose
		-- deck is not at the height the content guessed still receives players
		-- correctly. If the ray hits nothing, the content point is used as-is
		-- and the server warns by name -- a silent fall through the world is
		-- the one outcome worth a log line.
		TeleportProbeHeight = 400,
		TeleportProbeDepth = 800,
		TeleportLandingClearance = 4,

		-- === THE LIVE TINT ===
		-- The menu leans toward the district you are standing in, and toward
		-- whatever event is happening to the sky. How far it leans is content
		-- (Content/Hub/Palettes); these are the mechanics.
		LiveTintEnabled = true,
		-- How close to a district's anchor counts as being IN it. The ring
		-- radius is 400 and the widest platform is 320, so 220 puts the
		-- boundary just outside the biggest deck: you are in a district when
		-- you are standing on it and for a few strides after, and on the open
		-- plaza you are in none of them.
		DistrictTintRadius = 220 * WORLD_SCALE,
		-- Checked on a timer, never per frame. Same reasoning as
		-- Effects.CullIntervalSeconds: a distance test that runs 60 times a
		-- second to answer a question that changes every thirty seconds is
		-- the kind of cost a phone pays for all session.
		DistrictPollSeconds = 0.5,
		-- Long. A tint that snaps reads as a glitch; one that takes most of a
		-- second reads as the room changing around you.
		TintTweenSeconds = 0.8,
	},

	-- === CODES ===
	Codes = {
		Enabled = true,
		MaxLength = 32,
		-- A code box is a brute-force surface. Six attempts a minute is
		-- generous for typing and useless for guessing.
		AttemptsPerMinute = 6,
	},

	-- === THE LOADING SCREEN ===
	-- Owner-directed 2026-09-18 (STATUS §4, "First-join intro screen"). Its
	-- purpose is as much technical as aesthetic: the hub is ~450 instances
	-- plus authored art, and the client currently spends that wait standing in
	-- a half-built world. This gives the wait a face and a Play button.
	Loading = {
		Enabled = true,

		-- Never flash. A player whose client is already warm still gets the
		-- title, the camera move and the music sting -- an intro that appears
		-- for 200ms reads as a bug, not as polish.
		MinimumSeconds = 3.5,
		-- ...and never trap. If replication stalls, the Play button lights up
		-- anyway rather than holding the player hostage to a count that may
		-- never complete.
		MaximumSeconds = 45, -- the v2 hub is several hundred meshes

		-- WHAT "LOADED" MEANS. Not a count -- a SETTLE.
		--
		-- This was `RequiredHubInstances = 380`, a guess at how many parts the
		-- hub has. The authored Crossroads builds 357, so the bar could only
		-- ever reach 94% and every player waited out the 25-second timeout and
		-- was told loading had "taken longer than usual". The number was wrong
		-- the day it was written and would have gone wrong again every time
		-- the hub changed.
		--
		-- Replication is now judged by its SHAPE instead: instances arrive,
		-- and then they stop arriving. When the descendant count has not moved
		-- for SettleSeconds, the hub is here -- however many parts it turns out
		-- to have. Nothing to retune when the art changes.
		MinimumHubInstances = 100, -- a sanity floor, not a target
		HubSettleSeconds = 1.0,
		HubPollSeconds = 0.2,
		PreloadBatchSize = 64,

		-- The camera tour behind the panel. One shot is a slow arc around a
		-- subject; the list of subjects is CONTENT (Content/Hub/Cinematics).
		ShotSeconds = 9.0,
		ShotCrossfadeSeconds = 1.2,
		-- Degrees of arc a single shot sweeps. 26 -> 52: at 26 over nine
		-- seconds the camera moved about three degrees a second, which the
		-- first Studio look reported as "locked in place". It should read as
		-- a drift, which means it has to be visible.
		ShotArcDegrees = 52,
		-- ...and a gentle push in over the shot, as a fraction of the radius.
		-- Parallax is what makes a slow move read as a move at all.
		ShotDollyFraction = 0.08,
		BlurSize = 18,
		-- Field of view, pulled in slightly from Roblox's 70 so the shots read
		-- as photographed rather than as gameplay.
		FieldOfView = 58,
	},

	-- === PLAYER MOVEMENT ===
	-- Movement only, and deliberately so. Owner-directed: combat, damage and
	-- every offensive stat belong to the ITEM that grants them (a sword model
	-- carries its own damage, effects, abilities and animations), never to the
	-- player. Nothing here may grow a damage number (a test pins it).
	--
	-- Every number the movement uses is here: the character runs on our own
	-- ControllerManager, not the default Humanoid physics, so nothing about how
	-- a player moves is Roblox's default (owner-directed 2026-09-28).
	--
	-- Client-applied, because Roblox movement is client-authoritative by
	-- construction. The server validates OUTCOMES (distance to the Fate
	-- Engine, expedition eligibility, and later hits) and never reads a
	-- client-supplied speed. See docs/PLAYER_ABILITIES.md.
	Locomotion = {
		-- === PROFILES ===
		-- The hub is for getting around; an expedition is for fighting. Same
		-- rules, different weight. Speeds are multipliers on Scale.WalkSpeed
		-- (the hub traversal budget owns that number and nothing forks it).
		-- The controller picks EXPEDITION while the character stands inside a
		-- loaded expedition stage, HUB otherwise.
		Profiles = {
			HUB = {
				SpeedScale = 1, -- 32 studs/s
				SprintMultiplier = 1.61, -- 24 -> ~38.6 (owner: +1.5 studs/s)
				-- Short on purpose: long ramps read as sliding on ice (owner's
				-- first Studio walk, 2026-09-28).
				AccelerationSeconds = 0.08,
				DecelerationSeconds = 0.05,
				-- Moving in the air steers at this fraction of ground control.
				AirControl = 0.8,
				-- Stamina is unlimited in the hub, and only there (owner,
				-- 2026-09-28): nothing costs anything.
				JumpStaminaCost = 0,
				RollStaminaCost = 0,
				SprintDrainPerSecond = 0,
				-- A hard landing slows you for this long (see HardLanding*).
				HardLandingRecoverySeconds = 0.12,
				AirDashStaminaCost = 0,
			},
			EXPEDITION = {
				-- The middle ground the owner asked for: heavier than the hub,
				-- lighter than a Souls game. ~22 walking, ~34 sprinting.
				SpeedScale = 0.7,
				SprintMultiplier = 1.59, -- 16.8 -> ~26.7 (owner: +1.5 studs/s)
				-- Weight comes from costs and the ramps, not from sliding.
				AccelerationSeconds = 0.12,
				DecelerationSeconds = 0.08,
				AirControl = 0.45,
				JumpStaminaCost = 10,
				RollStaminaCost = 22,
				SprintDrainPerSecond = 14,
				HardLandingRecoverySeconds = 0.3,
				AirDashStaminaCost = 18,
			},
		},

		-- === STAMINA ===
		-- One bar for everything: sprint, jump, roll now; attacks and blocks
		-- when weapons land. A challenge, not a punishment: any action can be
		-- STARTED on any stamina above zero (the cost may take the bar to
		-- zero), and running dry only costs a short breather.
		StaminaMax = 100,
		StaminaRegenPerSecond = 30, -- empty to full in ~3.3s
		-- Refill waits this long after any spend...
		StaminaRegenDelaySeconds = 0.45,
		-- ...and this long after the bar hits zero (the "exhausted" breather).
		StaminaExhaustedDelaySeconds = 1.1,
		-- A NEW sprint needs this much; a running sprint continues to zero.
		StaminaSprintFloor = 5,

		-- === JUMP ===
		-- One jump. The double jump is gone (owner, 2026-09-28). Height is
		-- unchanged from the old ground jump, so every gap the kits were built
		-- around stays crossable.
		JumpPower = 50, -- launch speed, studs/s
		-- A grace window after leaving a ledge in which the jump still counts
		-- as a ground jump. Every platformer has this and nobody notices it
		-- until it is missing.
		CoyoteTimeSeconds = 0.12,
		-- A jump pressed this long before landing fires on landing.
		JumpBufferSeconds = 0.12,
		-- Coming down faster than this (studs/s) is a hard landing: the body
		-- absorbs it and movement slows to HardLandingSpeedMultiplier for the
		-- profile's HardLandingRecoverySeconds. A normal jump lands at ~50,
		-- so only real drops count.
		HardLandingSpeed = 72,
		HardLandingSpeedMultiplier = 0.35,

		-- === ROLL ===
		-- The Souls verb, adapted: a committed roll with a direction, or a
		-- quick backstep when no direction is held. The movement half only:
		-- the invulnerable window is DECLARED here and read by the combat
		-- layer when it opens (RESERVED, docs/RESERVED.md).
		-- Slower and further after the owner's walk with the first clips
		-- (2026-09-28): a short, quick roll read as unrefined.
		RollDurationSeconds = 0.65,
		-- How far a roll travels, in studs; its speed follows the roll's shape
		-- (LocomotionCore.rollSpeedShape) and is worked out from this.
		RollDistanceStuds = 18, -- owner-tuned 2026-09-28
		RollRecoverySeconds = 0.12, -- after the roll, before the next action
		-- The body blends out of a roll clip into standing or running over
		-- this long, instead of dropping out of it (owner, 2026-09-28).
		RollExitBlendSeconds = 0.22,
		RollInvulnerableFrom = 0.05, -- seconds into the roll
		RollInvulnerableTo = 0.44,
		BackstepDurationSeconds = 0.32,
		BackstepSpeed = 26, -- ~8 studs
		BackstepInvulnerableFrom = 0.02,
		BackstepInvulnerableTo = 0.16,
		BackstepStaminaFraction = 0.6, -- of the profile's RollStaminaCost
		-- A roll pressed this long before the current one ends comes out the
		-- moment it can. Chaining rolls is the feel; mashing is not required.
		RollBufferSeconds = 0.2,

		-- === AIR DASH (the jump dash) ===
		-- Roll pressed in the air: a short horizontal burst the held way (or
		-- forward), holding height for its length, once per airtime.
		-- Movement only -- no invulnerable window. Owner, 2026-09-28.
		AirDashes = 1,
		-- Off the floor for less than this is not "in the air": a roll press
		-- then waits for the feet instead of becoming an air dash.
		AirDashMinAirSeconds = 0.12,
		AirDashSpeed = 52, -- studs/s
		AirDashDurationSeconds = 0.22, -- ~11.5 studs

		-- === ROLL LOOK ===
		-- A discrete burst of wind, not afterimages (owner, 2026-09-28): short
		-- streaks of air left behind where the move starts, gone in a moment.
		-- No ground ring (owner: too much). Used for the roll, backstep and
		-- air dash.
		RollWind = true,
		RollWindSeconds = 0.32,
		RollWindTransparency = 0.35, -- how solid a streak starts
		RollWindStreaks = 5,
		RollWindStreakLengthStuds = 7,
		RollWindStreakThickness = 0.12,
		-- The procedural roll while there is no clip for that direction: the
		-- body tumbles forward, backward or sideways, relative to facing,
		-- dipping this far at its lowest. Drawn locally; other players see
		-- the clip once one is filled in (Content/Animations/Player.luau).
		RollTumble = true,
		RollTumbleDropStuds = 0.9,
		-- The air dash's procedural lean toward its direction, in degrees.
		AirDashLeanDegrees = 28,
		-- The camera widens by this many degrees at the start of a roll and
		-- settles back over the roll.
		RollFovKickDegrees = 3,

		-- === SHOULDER CAMERA (our shift lock) ===
		-- Left Ctrl toggles it: the mouse locks to the centre, the camera
		-- sits over the right shoulder, and the character faces where the
		-- camera looks. Not Shift, which is sprint.
		ShoulderCameraOffset = 1.75, -- studs right

		-- === WEAPON LOCK ===
		-- The longest any weapon move may hold movement, however long it asks
		-- for. A forgotten unlock still hands control back.
		MaxLockSeconds = 2.5,

		-- === CONTROLLER ===
		-- How far below the hips the floor sensor looks; past this, airborne.
		GroundSearchDistance = 1.5,
		-- How often the controller re-checks HUB vs EXPEDITION.
		ProfileCheckSeconds = 0.5,
		-- After a jump the floor sensor still sees the floor for a frame or
		-- two; the character counts as airborne for this long regardless.
		JumpGroundIgnoreSeconds = 0.15,
		-- Ground acceleration during a roll: near-instant, so it bursts.
		RollAccelerationSeconds = 0.03,
		-- A stage's footprint is grown by this many studs when deciding
		-- whether the character stands inside it.
		StageMarginStuds = 20,
	},

	-- === CHARACTER ANIMATION ===
	-- How the body reads while it moves: gait blending, directional legs,
	-- lean, head look, landings, footsteps. Presentation only -- nothing here
	-- changes where a character goes or how fast. Rules in AnimationCore; the
	-- clips themselves are Content/Animations/Player.luau.
	CharacterAnimation = {
		-- Below this horizontal speed (studs/s) the body stands.
		IdleSpeed = 0.9,
		-- Walk -> run crossfade band, in studs/s. Above RunFrom the run clip
		-- starts to take over; by RunFull it has.
		RunFrom = 10,
		RunFull = 15,
		-- Speeds the clips were authored at, so playback follows the real
		-- speed without the feet sliding. Stock R15 values.
		WalkClipSpeed = 11,
		RunClipSpeed = 24,
		SprintClipSpeed = 30,
		-- Playback-rate clamp: past these a clip reads as sped-up footage.
		MinPlaybackRate = 0.55,
		MaxPlaybackRate = 1.7,
		-- Crossfades.
		FadeSeconds = 0.18,
		AirFadeSeconds = 0.1,
		-- Directional blend weights settle over this long, so a change of
		-- direction flows instead of snapping between clips.
		DirectionSmoothSeconds = 0.09,

		-- === PROCEDURAL FALLBACK (no directional clips yet) ===
		-- Strafing: the legs turn toward the movement (up to this far) while
		-- the upper body counter-turns to keep facing forward.
		MaxLegYawDegrees = 65,
		WaistCounterFraction = 0.85,
		LegYawSmoothSeconds = 0.1,
		-- Moving backward plays the forward clip in reverse once the move
		-- direction is this far behind (cosine of the angle, -1 = straight back).
		BackwardBelowCos = -0.25,

		-- === LEAN ===
		-- Into acceleration (pitch) and into turns (bank), in degrees.
		MaxLeanDegrees = 9,
		LeanPerAcceleration = 0.09, -- degrees per studs/s^2
		SprintLeanDegrees = 5, -- extra forward lean while sprinting
		MaxBankDegrees = 11,
		BankPerTurnRate = 2.4, -- degrees per rad/s, scaled by speed
		LeanSmoothSeconds = 0.12,

		-- === HEAD LOOK ===
		-- The head turns toward the lock-on target, or where the camera looks.
		HeadLook = true,
		MaxHeadYawDegrees = 55,
		MaxHeadPitchDegrees = 30,
		HeadSmoothSeconds = 0.14,

		-- === LANDING ===
		-- Fall speed (studs/s) above which a landing is shown at all, and the
		-- dip the body takes (studs) for a soft and a hard one.
		SoftLandingSpeed = 22,
		SoftLandingDipStuds = 0.35,
		HardLandingDipStuds = 1.0,
		LandingDipSeconds = 0.28,

		-- === TURN IN PLACE ===
		-- Standing and turning faster than this (rad/s) steps the feet.
		TurnInPlaceRate = 2.2,
		TurnInPlaceWeight = 0.55,

		-- === SOUNDS ===
		-- The Roblox client's built-in character sounds, played by us (the
		-- default sound script keys off the Humanoid state machine, which is
		-- off). The running loop's rate follows speed: at RunningSoundSpeed
		-- studs/s it plays at normal rate.
		Sounds = true,
		RunningSoundSpeed = 16,
		MaxRunningSoundRate = 2.2,
		RunningVolume = 0.35,
		JumpVolume = 0.4,
		LandVolume = 0.5,
	},

	-- === LOCK-ON ===
	-- Optional: everything plays without it. A target is any model the game
	-- tags with Constants.NAMES.LOCK_ON_TAG (the spawner tags it; the enemy
	-- asset is never edited). Over-the-shoulder camera while locked.
	LockOn = {
		Range = 90, -- studs, to acquire
		BreakRange = 120, -- studs, past this the lock drops
		-- Candidates must sit within this angle of the camera's look.
		MaxAngleRadians = math.rad(60),
		-- Score = angle weight x angle + distance / Range; lowest wins, so the
		-- thing you look at beats the thing that is merely close.
		AngleWeight = 2,
		-- Out of sight this long and the lock drops.
		LostSightSeconds = 1.5,
		-- The camera: behind and over the right shoulder.
		CameraDistance = 11,
		ShoulderOffset = 2.4, -- studs right
		ShoulderHeight = 2.2, -- studs above the root
		CameraLift = 1.6,
		-- How far toward the target the camera looks (0 = at the player).
		LookBias = 0.55,
		-- A tall target is aimed at no higher than this above the player's
		-- root, so a boss never pulls the camera into the sky.
		MaxAimHeight = 9,
		-- Seconds for the camera to close most of the gap; smooth, not floaty.
		CameraSmoothSeconds = 0.08,
		-- The camera never sits closer to the player than this after a wall
		-- pulls it in.
		CameraMinDistance = 3,
		-- Letting go of a lock eases the view back to the normal (or
		-- shoulder) camera over this long instead of snapping (owner, 2026-09-28).
		ReleaseBlendSeconds = 0.4,

		-- === SWITCHING TARGETS ===
		-- While locked, flick the mouse or the right stick sideways (or tap
		-- Next on touch) to move the lock one target that way.
		SwitchMousePixels = 60, -- sideways mouse travel that counts as a flick
		SwitchMouseWindowSeconds = 0.25, -- ...if it happens within this long
		SwitchStickThreshold = 0.7, -- right-stick X past this is a flick
		SwitchStickRest = 0.3, -- and it must return inside this before the next
		SwitchCooldownSeconds = 0.3, -- between two switches
		-- A candidate must sit at least this far to the side (in the camera's
		-- unit-direction space) to count as "that way", so two enemies stood
		-- almost in line do not flip-flop.
		SwitchMinOffset = 0.02,
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
		-- Space between catalogue pieces that cannot join on the observation line.
		TestChunkGap = 8,
		TestDurationSeconds = 3600,

		-- How fast /fly moves, in studs per second.
		FlySpeed = 120,
		-- The developer panel (UI/DevPanel): the key that opens it, how many
		-- output lines it keeps, and how many autocomplete rows it shows.
		PanelKey = "F4", -- an Enum.KeyCode name (a string: GameConfig loads headless)
		PanelLogLines = 120,
		-- The dev panel resizes from its corner grip, down to this floor.
		PanelMinWidth = 460,
		PanelMinHeight = 380,
		PanelSuggestions = 10,
		ChunkLabelHeight = 40, -- studs above a chunk's centre for its /chunks label
		-- Guard rails on /speed, so a typo does not launch the character into
		-- the skybox and require a rejoin.
		MinWalkSpeed = 1,
		MaxWalkSpeed = 500,

		-- /dummies: plain lock-on targets for testing lock-on and switching
		-- before any enemy spawns. An arc in front of the player.
		DummyDefaultCount = 3,
		DummyMaxCount = 6,
		DummyDistanceStuds = 30,
		DummySpacingStuds = 14,
		DummyHeightStuds = 8,

		LogEveryRoll = true,
	},

	-- A world's ambience (its Environment's Atmosphere, CloudSea, Motes and
	-- post-effects), drawn client-side by AmbienceController. The dials here are
	-- about the DEVICE, not the world: how much of the ambience to draw.
	Ambience = {
		-- Scale used when the player's graphics are on Automatic, which does not
		-- report what the engine chose. Middling, because the devices left on
		-- Automatic are mostly the phones this protects.
		AutomaticQuality = 0.6,
		-- The least a manual graphics level can scale ambience to. Level 1 still
		-- gets a thin sea rather than none: an empty void reads as a bug.
		QualityFloor = 0.3,
		-- How often cloud layers beyond the nearest are moved, per second. They
		-- are far away and slow, so full frame rate buys nothing visible.
		FarLayerHz = 20,

		-- AMBIENT SCENERY (CHUNK_AUTHORING.md convention 6): the props a kit
		-- ships apart from its pieces, placed and animated on each client.
		-- Scenario atmospheres (Content/Atmospheres): each run draws one from its
		-- seed, or keeps the world's own air. BaseWeight is the world's own share
		-- against 1 per profile (2 with seven profiles = 2 in 9 runs plain).
		-- /atmosphere forces one in Studio.
		Atmospheres = { Enabled = true, BaseWeight = 2 },
		Props = {
			-- On since Sky Citadel's structure-only meshes went live
			-- (2026-09-23). A world still on meshes with its props baked in
			-- must have no Content/Props file, or every crystal shows twice.
			Enabled = true,
			-- The quality scale a detail tier needs: tier 1 always, tier 2 on
			-- anything above low graphics, tier 3 only on high.
			TierMinQuality = { 0, 0.45, 0.8 },
			-- Props farther than this from the camera hold still. Nobody can
			-- see a crystal bob from a kilometre away, and moving it costs.
			AnimateRadius = 700,
			-- Motion per animation class (PropCore.ANIMS says which prop gets
			-- which). Periods in seconds, distances in studs, angles in
			-- radians. Deliberately small and slow: scenery, not spectacle.
			Float = { Amplitude = 0.8, Period = 8 },
			Hover = { Amplitude = 0.6, Period = 7, SpinPeriod = 40 },
			Spin = { Period = 90 },
			-- A hoop over the path only turns in its own plane, and slowly.
			Roll = { Period = 120 },
			Moored = { Amplitude = 0.35, Period = 6, Rock = 0.04 },
			Tumble = { Amplitude = 0.7, Period = 11, Rock = 0.15 },
			-- One lap of the flock. Bob must stay <= the generator's BIRD_BOB
			-- (0.6), the clearance every bird's circle was proven with.
			Bird = { Period = 36, Speed = 14, Bob = 0.5, Bank = 0.25 }, -- Speed: studs/s, same for every bird
			-- Map-wide gliders (skyrays). Reach: the fraction of the map's
			-- radius the circle breathes in and out by; Altitude: studs above
			-- the highest chunk floor, clear of every crown (Ethereal Scape's
			-- CROWN_TOP is 160); Spread: the flock's height band above that.
			Glide = {
				Period = 90,
				Speed = 16,
				Bob = 1.5,
				Bank = 0.2,
				Reach = 0.45,
				ReachPeriod = 70,
				Altitude = 172,
				Spread = 40,
			},
			-- A wingbeat: radians each way from the modelled pose, and seconds.
			Wing = { Amplitude = 0.45, Period = 0.7 },
			-- Banners rocking in the wind: radians each way about the centre.
			Sway = { Angle = 0.03, Period = 5 },
		},
	},
	-- Loot, fixtures and vault keys (build spec §7.5, owner-directed
	-- 2026-09-23). What drops is content (Content/LootPools); these are the
	-- rules around it.
	Loot = {
		-- Keys a player may hold of any one kind. Using one takes it to zero.
		MaxKeysPerKind = 1,
		-- Until bosses exist (still §7-excluded), "the boss is defeated" means
		-- a party member first stands in the arena. Turn off to make the key
		-- and the boss pool unreachable, as they will be until then.
		BossDefeatStandIn = true,
		-- Seconds between checks for someone standing in the arena, how much of
		-- the arena piece's width counts as "in it", and how far below its
		-- deck a player still counts (a jump off the edge does not).
		ArenaCheckSeconds = 0.5,
		ArenaRadiusFraction = 0.45,
		ArenaBelowStuds = 20,
		-- Prompts on chests and the vault.
		PromptDistance = 10,
		PromptHoldSeconds = 0.6,
		-- The server re-checks distance with this much slack for lag.
		PromptSlackStuds = 6,
		-- A locked vault says so at most this often per player.
		RefusalCooldownSeconds = 1,
		-- How opened and shimmering fixtures move (FixtureCore).
		Fixture = {
			LidAngle = 1.9, -- radians the lid swings back
			LidSeconds = 0.8,
			DoorTurns = 2, -- the vault's dial spins home twice
			DoorSeconds = 2.4,
			-- Studs it then slides back into the vault's dark tunnel (12 deep in
			-- the treasury): past its own 2.9 thickness, so it ends inside.
			DoorRecess = 6,
			DoorRecessSeconds = 1.5,
			PulsePeriod = 3.2, -- the forcefield's slow breath
			MinTransparency = 0.35,
			MaxTransparency = 0.7,
		},
	},
}

return deepFreeze(GameConfig)
