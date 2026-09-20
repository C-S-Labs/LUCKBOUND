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
	-- Client-side hub animation. These exist because the hub animator runs
	-- every frame on every player's machine, including the low-end phones the
	-- §6 checklist budgets for, and the first authored playtest already
	-- reported it "slightly choppy" in Studio on a desktop.
	Effects = {
		-- Beyond this, a part stops animating entirely. The hub is 1150 studs
		-- across and scenery reaches 4000, so most of what is tagged is off
		-- screen or a speck for most of the session.
		AnimationDistance = 700,
		-- How often the distance check itself runs. Doing it per part per
		-- frame would cost more than the animation it is protecting.
		CullIntervalSeconds = 0.5,
		-- Size and Transparency are far more expensive to write than CFrame --
		-- a Size change on a MeshPart re-scales the mesh. 20 Hz is
		-- indistinguishable from 60 for a slow breath and a third of the work.
		SlowUpdateSeconds = 0.05,
	},

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
			Radius = 34,
			Height = 6,
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
		DistrictTintRadius = 220,
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
}

return deepFreeze(GameConfig)
