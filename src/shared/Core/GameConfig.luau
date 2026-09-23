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
		AssemblyAttempts = 5,

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
		MaximumSeconds = 25,

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

	-- === PLAYER ABILITIES, PHASE 1 ===
	-- Movement only, and deliberately so. Owner-directed: combat, damage and
	-- every offensive stat belong to the ITEM that grants them (a sword model
	-- carries its own damage, effects, abilities and animations), never to the
	-- player. Nothing here may grow a damage number.
	--
	-- These are client-applied, because Roblox movement is client-authoritative
	-- by construction -- the server cannot make a character run without the
	-- client agreeing. The server's defence is the same one it already uses for
	-- rolls: it validates OUTCOMES (distance to the Fate Engine, expedition
	-- eligibility) and never reads a client-supplied speed. See
	-- docs/PLAYER_ABILITIES.md for the planned ladder beyond these two.
	Locomotion = {
		-- Base is GameConfig.Scale.WalkSpeed (32) -- the hub traversal budget
		-- owns that number and this must not fork it.
		SprintMultiplier = 1.55, -- 32 -> 49.6
		SprintAccelerationSeconds = 0.25, -- ramp, so it reads as effort
		SprintDecelerationSeconds = 0.4,

		-- Stamina exists to make sprinting a decision instead of a walk speed.
		-- Full drain is 8s of sprint; a full refill is 6s of not sprinting.
		StaminaMax = 100,
		StaminaDrainPerSecond = 12.5,
		StaminaRegenPerSecond = 16.6,
		-- You cannot re-start a sprint the instant you run dry; you have to let
		-- it breathe. Without this the player taps sprint forever at 0.
		StaminaRegenDelaySeconds = 0.8,
		StaminaSprintFloor = 5,

		-- Roblox's own default JumpPower, restated here because two places
		-- need to restore it (the loading screen releases the character it
		-- froze, and the air jump multiplies it) and neither may guess.
		JumpPower = 50,

		-- === DOUBLE JUMP ===
		-- Two jumps total (the ground jump plus one), which is the whole
		-- feature. A third is not a tuning change -- it is a movement game.
		AirJumps = 1,
		AirJumpPower = 0.85, -- multiplier on the humanoid's JumpPower
		-- A grace window after leaving a ledge in which the FIRST jump is
		-- still the ground jump. Every platformer has this and nobody notices
		-- it until it is missing.
		CoyoteTimeSeconds = 0.12,
		-- Stops one input frame from spending both jumps at once.
		AirJumpCooldownSeconds = 0.2,
		-- Fires a small ring effect under the feet on the air jump, so the
		-- second jump is legible to the player and to anyone watching.
		AirJumpEffect = true,
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
			Bird = { Period = 36, Bob = 0.5, Bank = 0.25 },
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
