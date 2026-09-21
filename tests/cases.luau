-- LUCKBOUND test suite. Run: python3 tests/build_suite.py && luau tests/generated_suite.luau

local Constants = __require("Constants")
local GameConfig = __require("GameConfig")
local FateCore = __require("FateCore")
local ProgressionCore = __require("ProgressionCore")
local ProfileSchema = __require("ProfileSchema")
local EventCore = __require("EventCore")
local Events = __require("Events")
local LedgerCore = __require("LedgerCore")
local WeightedRandom = __require("WeightedRandom")
local Schema = __require("Schema")
local Worlds = __require("Worlds")
local Crossroads = __require("Crossroads")
local UITheme = __require("UITheme")
local AssetManifest = __require("AssetManifest")
local ChunkCore = __require("ChunkCore")
local ExpeditionCore = __require("ExpeditionCore")
local Chunks = __require("Chunks")
local Menu = __require("Menu")
local Cinematics = __require("Cinematics")
local Codes = __require("Codes")
local HubMenuCore = __require("HubMenuCore")
local CodeCore = __require("CodeCore")
local SettingsCore = __require("SettingsCore")
local LocomotionCore = __require("LocomotionCore")
local ThemeCore = __require("ThemeCore")
local Palettes = __require("Palettes")
local EventCore = __require("EventCore")

-- === tiny harness ===================================================
local passed, failed = 0, 0
local failures = {}
local currentGroup = ""

local function group(name)
	currentGroup = name
	print("\n" .. name)
end

local function check(name, ok, detail)
	if ok then
		passed += 1
		print(string.format("  PASS  %s", name))
	else
		failed += 1
		local line = string.format("%s / %s%s", currentGroup, name, detail and (" -- " .. detail) or "")
		table.insert(failures, line)
		print(string.format("  FAIL  %s%s", name, detail and ("  -- " .. detail) or ""))
	end
end

local function throws(fn)
	local ok, err = pcall(fn)
	return not ok, tostring(err)
end

-- Deterministic PRNG so distribution tests are reproducible across runs.
local function lcg(seed)
	local state = seed % 2147483647
	if state <= 0 then state += 2147483646 end
	return function()
		state = (state * 16807) % 2147483647
		return (state - 1) / 2147483646
	end
end

local function profile(overrides)
	local p = ProfileSchema.default(1700000000)
	for k, v in overrides or {} do p[k] = v end
	return p
end

local function cfg(overrides)
	-- GameConfig is deep-frozen, so build a shallow-cloned override tree.
	local c = {}
	for k, v in GameConfig do
		if type(v) == "table" then
			local inner = {}
			for ik, iv in v do inner[ik] = iv end
			c[k] = inner
		else
			c[k] = v
		end
	end
	for k, v in overrides or {} do
		if type(v) == "table" and type(c[k]) == "table" then
			for ik, iv in v do c[k][ik] = iv end
		else
			c[k] = v
		end
	end
	return c
end

-- === 1. Content & config validation =================================
group("Schema validation")

do
	local ok, errs = Schema.validateWorlds(Worlds)
	check("real world content validates", ok, table.concat(errs, "; "))

	local okc, errsc = Schema.validateConfig(GameConfig, Worlds)
	check("real GameConfig validates against content", okc, table.concat(errsc, "; "))

	local bad = { BROKEN = { Id = "BROKEN", Name = "x", Rarity = "NOPE", RollWeight = 1,
		EnabledInPhase = 1, Environment = {}, Enemies = {}, Modifiers = {},
		DurationSeconds = 1, RecommendedPower = 1, Flavor = "" } }
	local okb, errsb = Schema.validateWorlds(bad)
	check("rejects unknown rarity", not okb and #errsb > 0, table.concat(errsb, "; "))

	local mismatch = {}
	for k, v in Worlds do mismatch[k] = v end
	mismatch.WRONG_KEY = Worlds.VERDANT_VALLEY
	local okm, errsm = Schema.validateWorlds(mismatch)
	check("rejects Id not matching registry key", not okm, table.concat(errsm, "; "))

	local missing = { X = { Id = "X" } }
	local okmi, errsmi = Schema.validateWorlds(missing)
	check("reports missing required fields", not okmi and #errsmi >= 5,
		string.format("%d errors", #errsmi))

	local badCfg = cfg({ Fate = { OnboardingSequence = { "DOES_NOT_EXIST" } } })
	local okcfg, errscfg = Schema.validateConfig(badCfg, Worlds)
	check("catches onboarding naming a missing world", not okcfg, table.concat(errscfg, "; "))

	local emptyPool = cfg({ CurrentPhase = 0 })
	local oke = Schema.validateConfig(emptyPool, Worlds)
	check("catches an empty roll pool", not oke)

	local raised = throws(function() Schema.validateAll(bad, GameConfig) end)
	check("validateAll raises on bad content (server refuses to boot)", raised)
end

-- === 2. Scripted onboarding =========================================
group("Scripted onboarding (15-roll arc)")

do
	local seq = GameConfig.Fate.OnboardingSequence
	check("onboarding is 15 rolls", #seq == 15, string.format("got %d", #seq))

	-- Every scripted roll must be forced regardless of the random stream.
	local allMatched = true
	local detail = ""
	for trial = 1, 120 do
		local p = profile()
		local rand = lcg(trial * 7919)
		for i = 1, #seq do
			local outcome = FateCore.roll(Worlds, p, GameConfig, rand)
			if outcome.WorldId ~= seq[i] or not outcome.IsScripted then
				allMatched = false
				detail = string.format("trial %d roll %d gave %s", trial, i, outcome.WorldId)
				break
			end
			p.TotalRolls += 1
		end
		if not allMatched then break end
	end
	check("all 15 rolls follow the scripted order, across 120 random streams", allMatched, detail)

	-- Count what the arc actually hands out.
	local counts = {}
	for _, id in seq do
		local rarity = Worlds[id].Rarity
		counts[rarity] = (counts[rarity] or 0) + 1
	end

	-- THE CORE GUARANTEE: a guaranteed Mythic would permanently devalue the
	-- top tier and the Fatebreak announcement that depends on it.
	check("onboarding NEVER hands out a Mythic", counts.MYTHIC == nil,
		string.format("found %d", counts.MYTHIC or 0))
	check("onboarding never hands out an Unknown", counts.UNKNOWN == nil)

	check("onboarding peaks on exactly one Epic", counts.EPIC == 1, tostring(counts.EPIC))
	check("the Epic is Sky Citadel", Worlds[seq[8]].Id == "SKY_CITADEL", seq[8])
	check("the Epic lands mid-arc, not at the end",
		seq[8] == "SKY_CITADEL" and #seq > 8)

	check("onboarding teaches Common, Rare and Epic",
		counts.COMMON and counts.RARE and counts.EPIC ~= nil)

	-- The arc must approximate real odds, or roll 16 feels like a punishment.
	local commonShare = counts.COMMON / #seq * 100
	local weights = GameConfig.Fate.PrototypeWeights
	local totalWeight = 0
	for _, w in weights do totalWeight += w end
	local trueCommonShare = weights.VERDANT_VALLEY / totalWeight * 100
	check("scripted Common rate is close to the true rate (no cliff at roll 16)",
		math.abs(commonShare - trueCommonShare) < 12,
		string.format("scripted %.1f%% vs true %.1f%%", commonShare, trueCommonShare))

	check("the arc ends on a Common so the handover is continuous",
		Worlds[seq[#seq]].Rarity == "COMMON", Worlds[seq[#seq]].Rarity)

	-- Rares must be spaced, not front-loaded into a parade.
	local longestCommonRun, run = 0, 0
	for _, id in seq do
		if Worlds[id].Rarity == "COMMON" then
			run += 1
			longestCommonRun = math.max(longestCommonRun, run)
		else
			run = 0
		end
	end
	check("no run of more than 3 Commons inside the arc", longestCommonRun <= 3,
		string.format("longest run %d", longestCommonRun))

	-- Indexed by TotalRolls, so it survives a rejoin mid-arc.
	local resumed = profile({ TotalRolls = 7 })
	local outcome = FateCore.roll(Worlds, resumed, GameConfig, lcg(1))
	check("onboarding resumes correctly after a rejoin", outcome.WorldId == seq[8] and outcome.IsScripted,
		outcome.WorldId)

	local done = profile({ TotalRolls = #seq })
	check("onboarding reports finished after the sequence", not FateCore.isOnboarding(done, GameConfig))
	check("roll 16 is no longer scripted",
		FateCore.roll(Worlds, done, GameConfig, lcg(5)).IsScripted == false)

	-- Only the opening tutorial rolls are shortened, not all 15.
	local fresh = profile()
	check("roll 1 gets a short tutorial expedition",
		FateCore.expeditionDuration(Worlds.VERDANT_VALLEY, fresh, GameConfig)
			== GameConfig.Fate.OnboardingExpeditionSeconds)

	local past = profile({ TotalRolls = GameConfig.Fate.ShortExpeditionRolls })
	check("later onboarding rolls run at full expedition length",
		FateCore.expeditionDuration(Worlds.VERDANT_VALLEY, past, GameConfig)
			== Worlds.VERDANT_VALLEY.DurationSeconds)

	local tutorialTotal = 0
	local p = profile()
	for i = 1, GameConfig.Fate.ShortExpeditionRolls do
		tutorialTotal += FateCore.expeditionDuration(Worlds[seq[i]], p, GameConfig)
		p.TotalRolls += 1
	end
	check("the tutorial expeditions still fit in ~5 minutes",
		tutorialTotal <= 330, string.format("%ds total", tutorialTotal))
end

-- === 3. TRUE RNG ====================================================
group("True RNG after onboarding")

do
	local done = profile({ TotalRolls = #GameConfig.Fate.OnboardingSequence })
	local N = 400000
	local counts = {}
	local rand = lcg(20260915)

	for _ = 1, N do
		local outcome = FateCore.roll(Worlds, done, GameConfig, rand)
		counts[outcome.WorldId] = (counts[outcome.WorldId] or 0) + 1
	end

	local weights = GameConfig.Fate.PrototypeWeights
	local totalWeight = 0
	for _, w in weights do totalWeight += w end

	local worstDrift, worstId = 0, ""
	for id, w in weights do
		local expected = w / totalWeight * 100
		local observed = (counts[id] or 0) / N * 100
		local drift = math.abs(observed - expected)
		print(string.format("        %-16s expected %6.2f%%  observed %6.2f%%  drift %.3fpp",
			id, expected, observed, drift))
		if drift > worstDrift then worstDrift, worstId = drift, id end
	end
	check("observed distribution within 0.5pp of configured weights", worstDrift < 0.5,
		string.format("worst %s at %.3fpp", worstId, worstDrift))

	-- THE CORE GUARANTEE: player state must not tilt the odds.
	local newbie = profile({ TotalRolls = 15, FateLevel = 1, FatePoints = 0 })
	local veteran = profile({ TotalRolls = 9999, FateLevel = 90, FatePoints = 500000 })
	local identical = true
	local a, b = lcg(4242), lcg(4242)
	for _ = 1, 50000 do
		if FateCore.roll(Worlds, newbie, GameConfig, a).WorldId
			~= FateCore.roll(Worlds, veteran, GameConfig, b).WorldId then
			identical = false
			break
		end
	end
	check("a level-90 player and a level-1 player draw identically (Fate does not tilt odds)", identical)

	for _, id in { "VERDANT_VALLEY", "ETHEREAL_SCAPE", "EMBERFALL", "SKY_CITADEL", "ASTRAL_REACH" } do
		check(string.format("weight for %s ignores Fate level", id),
			FateCore.effectiveWeight(Worlds[id], newbie, GameConfig)
				== FateCore.effectiveWeight(Worlds[id], veteran, GameConfig))
	end

	check("FateInfluencesOdds is off", GameConfig.Fate.FateInfluencesOdds == false)

	-- The dormant ladder still works if it is ever deliberately switched on.
	local tilted = cfg({ Fate = { FateInfluencesOdds = true } })
	check("the disabled weighting hook still functions when enabled",
		FateCore.effectiveWeight(Worlds.ASTRAL_REACH, veteran, tilted)
			> FateCore.effectiveWeight(Worlds.ASTRAL_REACH, newbie, tilted))

	-- Pool order must not depend on hash iteration order.
	local poolA = FateCore.buildPool(Worlds, 1)
	local poolB = FateCore.buildPool(Worlds, 1)
	local stable = #poolA == #poolB
	for i = 1, #poolA do
		if poolA[i].Id ~= poolB[i].Id then stable = false end
	end
	check("roll pool order is stable", stable)
	check("phase gating excludes Phase 3 content", #FateCore.buildPool(Worlds, 1) == 5,
		string.format("%d worlds enabled at phase 1", #FateCore.buildPool(Worlds, 1)))
	check("THE_UNKNOWN enters the pool at phase 3", #FateCore.buildPool(Worlds, 3) == 6)

	-- Epic must be commoner than Mythic, or the ladder is upside down.
	check("Epic is more likely than Mythic",
		weights.SKY_CITADEL > weights.ASTRAL_REACH,
		string.format("Epic %d vs Mythic %d", weights.SKY_CITADEL, weights.ASTRAL_REACH))
	check("prototype weights sum to 10000 so they read as percentages",
		totalWeight == 10000, tostring(totalWeight))
	check("Sky Citadel is Epic tier", Worlds.SKY_CITADEL.Rarity == "EPIC")

	-- Same seed, same results: rolls are auditable.
	local s1, s2 = lcg(777), lcg(777)
	local same = true
	for _ = 1, 1000 do
		if FateCore.roll(Worlds, done, GameConfig, s1).WorldId
			~= FateCore.roll(Worlds, done, GameConfig, s2).WorldId then same = false end
	end
	check("identical seeds produce identical rolls (auditable)", same)
end

-- === 4. WeightedRandom edge cases ===================================
group("WeightedRandom")

do
	local single = { { Id = "ONLY", w = 3 } }
	check("single-entry pool always returns that entry",
		WeightedRandom.pick(single, function(e) return e.w end, lcg(1)).Id == "ONLY")

	local zeros = { { w = 0 }, { w = 0 } }
	check("all-zero weights returns nil",
		WeightedRandom.pick(zeros, function(e) return e.w end, lcg(1)) == nil)

	local mixed = { { Id = "A", w = 0 }, { Id = "B", w = 5 } }
	local everA = false
	local r = lcg(99)
	for _ = 1, 5000 do
		if WeightedRandom.pick(mixed, function(e) return e.w end, r).Id == "A" then everA = true end
	end
	check("zero-weight entries are never picked", not everA)

	-- nextNumber returning exactly 0 and near-1 must both stay in bounds.
	local pool = { { Id = "A", w = 1 }, { Id = "B", w = 1 } }
	check("nextNumber() == 0 returns the first entry",
		WeightedRandom.pick(pool, function(e) return e.w end, function() return 0 end).Id == "A")
	check("nextNumber() near 1 stays in bounds",
		WeightedRandom.pick(pool, function(e) return e.w end, function() return 0.9999999 end) ~= nil)

	local probs = WeightedRandom.probabilities(pool, function(e) return e.w end)
	check("probabilities sum to 1", math.abs((probs[pool[1]] + probs[pool[2]]) - 1) < 1e-9)
end

-- === 5. Fate progression ============================================
group("Fate progression")

do
	check("level 1 costs nothing", ProgressionCore.pointsForLevel(1, GameConfig) == 0)

	local monotonic = true
	for level = 1, 99 do
		if ProgressionCore.pointsForLevel(level + 1, GameConfig)
			<= ProgressionCore.pointsForLevel(level, GameConfig) then monotonic = false end
	end
	check("level cost curve is strictly increasing", monotonic)

	local inverse = true
	local mismatchAt
	for level = 1, 100 do
		local pts = ProgressionCore.pointsForLevel(level, GameConfig)
		if ProgressionCore.levelForPoints(pts, GameConfig) ~= level then
			inverse = false
			mismatchAt = level
		end
	end
	check("levelForPoints inverts pointsForLevel at every level", inverse,
		mismatchAt and ("first mismatch at level " .. mismatchAt) or nil)

	check("level is capped at MaxLevel",
		ProgressionCore.levelForPoints(1e12, GameConfig) == GameConfig.Progression.MaxLevel)
	check("progress is 1 at max level",
		ProgressionCore.levelProgress(1e12, GameConfig) == 1)

	local mid = ProgressionCore.levelProgress(
		(ProgressionCore.pointsForLevel(5, GameConfig) + ProgressionCore.pointsForLevel(6, GameConfig)) // 2,
		GameConfig)
	check("progress between levels is in (0,1)", mid > 0 and mid < 1, tostring(mid))

	local p = profile()
	local pts, lvl = ProgressionCore.award(p, "BossDefeated", GameConfig)
	check("BossDefeated grants the configured Fate",
		pts == GameConfig.Progression.Rewards.BossDefeated, tostring(pts))
	check("award does not mutate the profile", p.FatePoints == 0)
	check("award returns a valid level", lvl >= 1)

	local raised = throws(function() ProgressionCore.award(p, "NotAReason", GameConfig) end)
	check("unknown reward reason raises", raised)

	-- The onboarding arc should visibly move the Fate bar, which is its point.
	local onboard = profile()
	local rewards = GameConfig.Progression.Rewards
	local earned = 3 * (rewards.ExpeditionCompleted + rewards.FirstTimeWorld) + 3 * rewards.BossDefeated
	check("completing onboarding produces a visible Fate gain",
		ProgressionCore.levelForPoints(earned, GameConfig) > 1,
		string.format("%d points -> level %d", earned,
			ProgressionCore.levelForPoints(earned, GameConfig)))
end

-- === 6. Profile persistence =========================================
group("Profile schema & migration")

do
	local now = 1700000000
	local fresh = ProfileSchema.default(now)
	check("new profile is at the current schema version",
		fresh.SchemaVersion == Constants.CURRENT_SCHEMA_VERSION)
	check("new profile starts at Fate level 1 with 0 points",
		fresh.FateLevel == 1 and fresh.FatePoints == 0 and fresh.TotalRolls == 0)

	local migrated = ProfileSchema.migrate(nil, now)
	check("nil stored data yields a default profile", migrated.SchemaVersion == ProfileSchema.CURRENT)

	local partial = { SchemaVersion = ProfileSchema.CURRENT, FatePoints = 500 }
	local filled, applied = ProfileSchema.migrate(partial, now)
	check("missing fields are backfilled", filled.RollHistory ~= nil and filled.Stats ~= nil)
	check("backfill preserves existing values", filled.FatePoints == 500)
	check("no migrations run for a current-version profile", applied == 0)

	-- v1 -> v2 added the hub menu's two fields. A v1 profile is what every
	-- existing tester's save IS, so this is the migration that actually runs
	-- in the wild rather than a hypothetical one.
	local legacy = { SchemaVersion = 1, FatePoints = 900, FateLevel = 4 }
	local upgraded, steps = ProfileSchema.migrate(legacy, now)
	check("a v1 profile migrates to the current version", upgraded.SchemaVersion == ProfileSchema.CURRENT)
	check("exactly one migration ran", steps == 1)
	check("the migration keeps what was there", upgraded.FatePoints == 900 and upgraded.FateLevel == 4)
	check("the migration adds RedeemedCodes", type(upgraded.RedeemedCodes) == "table")
	check("the migration adds a full settings table",
		type(upgraded.Settings) == "table" and upgraded.Settings.MusicVolume ~= nil)

	local future = { SchemaVersion = 99 }
	local f = ProfileSchema.migrate(future, now)
	check("a newer-than-known profile is left intact rather than reset", f.SchemaVersion == 99)

	local unmigratable = { SchemaVersion = 0 }
	local raised = throws(function() ProfileSchema.migrate(unmigratable, now) end)
	check("an unmigratable version raises instead of silently resetting", raised)

	-- Roll history is unbounded in memory and must be trimmed before writing.
	local big = ProfileSchema.default(now)
	for i = 1, 200 do
		table.insert(big.RollHistory, { WorldId = "VERDANT_VALLEY", Rarity = "COMMON", Timestamp = i })
	end
	ProfileSchema.prune(big, GameConfig)
	check("roll history is pruned to the cap",
		#big.RollHistory == GameConfig.Fate.RollHistoryCap, tostring(#big.RollHistory))
	check("pruning keeps the MOST RECENT entries",
		big.RollHistory[#big.RollHistory].Timestamp == 200
			and big.RollHistory[1].Timestamp == 200 - GameConfig.Fate.RollHistoryCap + 1)
end

-- === 7. Late joiners ================================================
group("Late-joiner visibility")

do
	local state = EventCore.newState()
	local t0 = 1700000000

	EventCore.startEvent(state, {
		Id = "STARFALL_1", Kind = "FATEBREAK", Name = "The Eternal Star",
		StartedAt = t0, EndsAt = t0 + 300, TriggeredBy = "Sgame1028",
	})

	-- A player joining 4 minutes into a 5 minute event.
	local late = EventCore.snapshot(state, t0 + 240, GameConfig)
	check("late joiner sees the in-progress event", #late.ActiveEvents == 1)
	check("late joiner gets the correct remaining time",
		late.ActiveEvents[1].RemainingSeconds == 60,
		tostring(late.ActiveEvents[1] and late.ActiveEvents[1].RemainingSeconds))
	check("late joiner gets elapsed time for animation sync",
		late.ActiveEvents[1].ElapsedSeconds == 240)
	check("late joiner learns who triggered it",
		late.ActiveEvents[1].TriggeredBy == "Sgame1028")

	-- After it ends, a joiner must NOT see a stale event.
	local after = EventCore.snapshot(state, t0 + 301, GameConfig)
	check("expired events disappear from the snapshot", #after.ActiveEvents == 0)
	check("expiry actually clears server state", next(state.ActiveEvents) == nil)

	local ended = EventCore.expire(EventCore.newState(), t0)
	check("expire on an empty state is safe", #ended == 0)

	-- Announcement buffer: a joiner should see what just happened.
	local s2 = EventCore.newState()
	for i = 1, 20 do
		EventCore.pushAnnouncement(s2, { Kind = "ROLL", Text = "roll " .. i,
			Rarity = "MYTHIC", PlayerName = "P" .. i, At = t0 + i }, t0 + i, GameConfig)
	end
	check("announcement buffer is capped",
		#s2.Announcements == GameConfig.Events.AnnouncementBufferSize,
		tostring(#s2.Announcements))
	check("buffer keeps the most recent announcements",
		s2.Announcements[#s2.Announcements].Text == "roll 20")

	local snap = EventCore.snapshot(s2, t0 + 20, GameConfig)
	check("late joiner receives the recent announcement feed",
		#snap.Announcements == GameConfig.Events.AnnouncementBufferSize)
	check("announcements carry age so the UI can fade them",
		snap.Announcements[1].AgeSeconds > 0)

	-- Stale announcements must age out, not follow players around forever.
	local old = EventCore.snapshot(s2, t0 + 20 + GameConfig.Events.AnnouncementBufferMaxAgeSeconds + 1, GameConfig)
	check("announcements older than the max age are dropped", #old.Announcements == 0)

	-- Two players joining at the same moment must see the same thing.
	local a = EventCore.snapshot(state, t0 + 100, GameConfig)
	local b = EventCore.snapshot(state, t0 + 100, GameConfig)
	check("snapshots are consistent between players",
		#a.ActiveEvents == #b.ActiveEvents and #a.Announcements == #b.Announcements)
	check("snapshot carries server time for clock-skew correction", a.ServerNow == t0 + 100)

	-- Concurrent events.
	local s3 = EventCore.newState()
	EventCore.startEvent(s3, { Id = "B", Kind = "FATEBREAK", Name = "B", StartedAt = t0, EndsAt = t0 + 100 })
	EventCore.startEvent(s3, { Id = "A", Kind = "FATEBREAK", Name = "A", StartedAt = t0, EndsAt = t0 + 200 })
	local multi = EventCore.snapshot(s3, t0 + 50, GameConfig)
	check("multiple concurrent events are all sent", #multi.ActiveEvents == 2)
	check("event order is stable", multi.ActiveEvents[1].Id == "A")

	local partial = EventCore.snapshot(s3, t0 + 150, GameConfig)
	check("only the still-running event survives",
		#partial.ActiveEvents == 1 and partial.ActiveEvents[1].Id == "A")
end

-- === 8. Hub layout data =============================================
group("Hub layout (the art-direction dial)")

do
	local ok, errs = Schema.validateHub(Crossroads)
	check("real hub layout validates", ok, table.concat(errs, "; "))

	check("all four hub districts are present", #Crossroads.Districts == 4,
		string.format("got %d", #Crossroads.Districts))

	local byId = {}
	for _, d in Crossroads.Districts do byId[d.Id] = d end
	for _, id in { "HALL_OF_LEGENDS", "DISCOVERY_ARCHIVE", "EXPEDITION_GATE",
		"TRAINING_GROUNDS" } do
		check(string.format("district %s exists", id), byId[id] ~= nil)
	end

	-- Master Spec §3 / Blueprint §2.1 compass placement. Roblox is Y-up, so
	-- the compass is the X/Z plane: NORTH = -Z, EAST = +X, SOUTH = +Z, WEST = -X.
	local anchors = GameConfig.HubLayout.Anchors
	check("Hall of Legends is north (-Z)", anchors.HALL_OF_LEGENDS.Z < 0)
	check("Discovery Archive is east (+X)", anchors.DISCOVERY_ARCHIVE.X > 0)
	check("Expedition Gate is south (+Z)", anchors.EXPEDITION_GATE.Z > 0)
	check("Training Grounds is west (-X)", anchors.TRAINING_GROUNDS.X < 0)
	check("Fate Engine is at true centre",
		anchors.FATE_ENGINE.X == 0 and anchors.FATE_ENGINE.Y == 0 and anchors.FATE_ENGINE.Z == 0)

	-- Blueprint §7.3: positions are locked in one place, never re-derived.
	local everyZoneAnchored = true
	for _, d in Crossroads.Districts do
		if anchors[d.Id] == nil then everyZoneAnchored = false end
	end
	check("every zone has a named anchor in GameConfig.HubLayout", everyZoneAnchored)

	-- Blueprint §2.2 proportions, rescaled for a 1200-stud hub. The blueprint's
	-- absolute numbers were relative to a 120-stud hub; what it was actually
	-- specifying is the RELATIONSHIPS, and those are what these assert.
	check("Fate Engine has 6 crystal shards",
		Crossroads.FateEngine.CrystalShards.Count == 6)
	check("Hall of Legends has 5 obelisk slots", byId.HALL_OF_LEGENDS.ObeliskSlots == 5)
	check("Training Grounds has 3 dummies plus a boss dummy",
		byId.TRAINING_GROUNDS.DummyCount == 3 and byId.TRAINING_GROUNDS.HasBossDummy)
	-- The plaza IS the playable diameter -- asserted as the relationship
	-- rather than as the literal 1150 it used to be, so a world rescale
	-- cannot leave the two disagreeing and still pass.
	check("the plaza is exactly the playable diameter the layout promises",
		Crossroads.Plaza.Diameter == GameConfig.HubLayout.HubDiameter,
		string.format("plaza %.0f, layout %.0f",
			Crossroads.Plaza.Diameter, GameConfig.HubLayout.HubDiameter))
	check("the gate processional is wider than a walkway",
		Crossroads.Bridges.ProcessionalWidth > Crossroads.Bridges.Width)

	-- === SCALE BUDGET =============================================
	-- A Roblox character is ~5 studs tall. The old hub was 24 characters
	-- across, which read as a room rather than a world.
	local CHAR = GameConfig.Scale.CharacterHeight
	-- 200 -> 100, and 40 -> 20, when the world was halved to player scale
	-- (GameConfig WORLD_SCALE). Both numbers were written against a hub that
	-- measured 230 characters across BECAUSE it was twice the size it should
	-- have been -- the counters stood 6 studs against a 5-stud player. So the
	-- old thresholds were really asking for 100 and 20 characters of honest
	-- space, and that is what they now ask for. The guard they exist to be is
	-- unchanged: the ORIGINAL hub was 24 characters across and read as a
	-- room, and 100 is still four times that.
	check("the hub reads as a world, not a room (>= 100 characters across)",
		Crossroads.Plaza.Diameter / CHAR >= 100,
		string.format("%.0f characters", Crossroads.Plaza.Diameter / CHAR))

	for _, d in Crossroads.Districts do
		check(string.format("%s is at least 20 characters across", d.Id),
			math.min(d.PlatformSize.X, d.PlatformSize.Z) / CHAR >= 20,
			string.format("%.0f", math.min(d.PlatformSize.X, d.PlatformSize.Z) / CHAR))
	end

	-- THE HARD BUDGET: no location may be more than MaxTraversalSeconds away.
	local speed = GameConfig.Scale.WalkSpeed
	local worstWalk, worstZone = 0, ""
	for _, d in Crossroads.Districts do
		local anchor = GameConfig.HubLayout.Anchors[d.Id]
		local flat = math.sqrt(anchor.X * anchor.X + anchor.Z * anchor.Z)
		local seconds = flat / speed
		if seconds > worstWalk then worstWalk, worstZone = seconds, d.Id end
	end
	check("no zone is more than the traversal budget away from the Fate Engine",
		worstWalk <= GameConfig.Scale.MaxTraversalSeconds,
		string.format("worst: %s at %.1fs (budget %ds)", worstZone, worstWalk,
			GameConfig.Scale.MaxTraversalSeconds))
	check("movement is faster than Roblox's 16 stud/s default, or the hub is a slog",
		speed > 16, tostring(speed))

	-- Scenery must reach well past anything walkable, or the world feels
	-- boxed in no matter how large the playable area is.
	check("scenery extends past the playable footprint",
		Crossroads.FloatingIslands.MaxRadius > GameConfig.HubLayout.HubDiameter,
		string.format("%d vs %d", Crossroads.FloatingIslands.MaxRadius,
			GameConfig.HubLayout.HubDiameter))
	check("fog reaches far enough to show the distant islands",
		Crossroads.Theme.FogEnd >= Crossroads.FloatingIslands.MaxRadius * 0.9,
		string.format("fog %d vs islands %d", Crossroads.Theme.FogEnd,
			Crossroads.FloatingIslands.MaxRadius))

	-- Geometry must not interpenetrate at the new scale.
	local engineR = Crossroads.FateEngine.PlatformRadius
	local ringR = GameConfig.HubLayout.ZoneRingRadius
	local tightest, tightestZone = math.huge, ""
	for _, d in Crossroads.Districts do
		if d.Height < 100 then
			local gap = ringR - engineR - math.max(d.PlatformSize.X, d.PlatformSize.Z) / 2
			if gap < tightest then tightest, tightestZone = gap, d.Id end
		end
	end
	check("zone platforms do not overlap the Fate Engine platform",
		tightest > 0, string.format("tightest gap: %s at %.0f studs", tightestZone, tightest))

	-- The rig has to grow with the platform or it is a speck on it.
	local engineRingR = GameConfig.Portal.OuterRingRadius * GameConfig.Portal.FateEngineScale
	check("the Fate Engine reads as monumental against its platform",
		engineRingR > engineR * 0.3 and engineRingR < engineR,
		string.format("ring %.0f vs platform %.0f", engineRingR, engineR))
	-- This assertion used to carry a `* 2` fudge factor and covered only the
	-- Engine. Both were wrong: the Gate is the larger rig, and at 12x its
	-- plinth was 84 studs in radius against a 70-stud prompt -- so a player
	-- standing ON the plinth was outside the prompt's range and the portal
	-- could not be used at all. The generalised version is in its own group
	-- below; this one stays as the Engine's specific case, without the fudge.
	check("the roll prompt reaches beyond the Engine's plinth",
		GameConfig.UI.PromptActivationDistance
			> GameConfig.Portal.PlinthDiameter * GameConfig.Portal.FateEngineScale * 0.5)
	check("the gate processional is wider than a walkway",
		Crossroads.Bridges.ProcessionalWidth > Crossroads.Bridges.Width)

	-- Every zone must have a builder, or HubBuilder asserts at boot.
	local KNOWN_KINDS = { AMPHITHEATRE = true, ROTUNDA = true, GATE = true,
		YARD = true, OBSERVATORY = true }
	local kindsOk = true
	local badKind
	for _, d in Crossroads.Districts do
		if not KNOWN_KINDS[d.Kind] then kindsOk = false badKind = d.Id end
	end
	check("every zone Kind has a builder", kindsOk, badKind)

	-- The mesh seam: every swappable piece must expose MeshId, or authored art
	-- cannot be dropped in without editing HubBuilder.
	local seamOk = Crossroads.FateEngine.MeshId == nil
		and Crossroads.Plaza.MeshId == nil
		and Crossroads.FloatingIslands.MeshId == nil
	for _, d in Crossroads.Districts do
		if rawget(d, "MeshId") ~= nil then seamOk = false end
	end
	check("every swappable piece exposes a MeshId seam (currently all blockout)", seamOk)

	check("floating islands are deterministic across servers",
		type(Crossroads.FloatingIslands.Seed) == "number")
	check("the spawn ring clears the Fate Engine's dais",
		GameConfig.HubLayout.SpawnRing.Radius > Crossroads.FateEngine.PlatformRadius,
		string.format("ring %d, dais %d",
			GameConfig.HubLayout.SpawnRing.Radius, Crossroads.FateEngine.PlatformRadius))

	-- Bad hub data must be caught at boot, like any other content.
	local broken = { Theme = {}, FateEngine = { PlatformRadius = 24 }, Districts = {} }
	local okb, errsb = Schema.validateHub(broken)
	check("rejects malformed hub data", not okb and #errsb >= 2, table.concat(errsb, "; "))

	-- Regression guard: this exact bug reached Studio. A Vector3 reports as
	-- "vector" under type(), so only typeof() can validate it.
	check("typeof() identifies a Vector3", typeof(Crossroads.FateEngine.AnchorSize) == "Vector3",
		typeof(Crossroads.FateEngine.AnchorSize))

	local badAnchor = {
		Theme = {},
		FateEngine = {
			AnchorSize = "not a vector",
			PlatformRadius = 24, PortalScale = 1.5, CrystalShards = { Count = 6 },
		},
		Districts = { Crossroads.Districts[1] },
	}
	local oka, errsa = Schema.validateHub(badAnchor)
	check("rejects a non-Vector3 AnchorSize", not oka, table.concat(errsa, "; "))

	local noKind = {
		Theme = {}, FateEngine = Crossroads.FateEngine,
		Districts = { { Id = "X", Name = "X", Angle = 0, Radius = 10 } },
	}
	local okk, errsk = Schema.validateHub(noKind)
	check("rejects a zone with no Kind", not okk, table.concat(errsk, "; "))

	local dupes = {
		Theme = {}, FateEngine = Crossroads.FateEngine,
		Districts = { Crossroads.Districts[1], Crossroads.Districts[1] },
	}
	local okd, errsd = Schema.validateHub(dupes)
	check("rejects duplicate district Ids", not okd, table.concat(errsd, "; "))
end

-- === 9. Portal rig & rarity contract ================================
group("PortalRig and the rarity colour contract")

do
	local portal = GameConfig.Portal
	check("outer ring is radius 9, thickness 1.2",
		portal.OuterRingRadius == 9 and portal.OuterRingThickness == 1.2)
	check("inner ring is radius 6.5, thickness 0.6",
		portal.InnerRingRadius == 6.5 and portal.InnerRingThickness == 0.6)
	check("rune ring has 8 plates", portal.RuneCount == 8)
	check("plinth is 14 studs across, 1.5 tall, octagonal",
		portal.PlinthDiameter == 14 and portal.PlinthHeight == 1.5 and portal.PlinthSides == 8)
	-- Range is a DISTANCE and scales with the world. Brightness does not --
	-- it moves the OTHER way, because a light that did not move away from a
	-- surface that came closer is a brighter light (inverse square). Both
	-- are asserted as relationships rather than as literals, so a rescale
	-- cannot leave a light reaching twice as far as the thing it lights.
	check("the point light reaches 24 studs at full world scale",
		portal.LightRange == 24 * GameConfig.HubLayout.WorldScale,
		string.format("range %.1f", portal.LightRange))

	check("...and the active flare is brighter than the idle glow, but not by much",
		portal.ActiveBrightness > portal.IdleBrightness
			and portal.ActiveBrightness <= portal.IdleBrightness * 4,
		string.format("idle %.2f, active %.2f", portal.IdleBrightness, portal.ActiveBrightness))
	check("active particle rate is 40", portal.ActiveParticleRate == 40)
	check("spin-up spikes particles to 200", portal.SpinUpParticleRate == 200)
	check("particle lifetime is 1.5-3s",
		portal.ParticleLifetimeMin == 1.5 and portal.ParticleLifetimeMax == 3)
	check("plane pulses between 0.3 and 0.7",
		portal.PlanePulseMin == 0.3 and portal.PlanePulseMax == 0.7)

	-- The single most important UX beat (master spec §25, blueprint §1.3).
	check("spin-up is 2.5s and never instant", portal.SpinUpSeconds == 2.5)
	check("spin-up spins faster than idle", portal.SpinUpSpinSpeed > portal.IdleSpinSpeed)
	check("the reveal can never beat the spin-up",
		math.max(GameConfig.UI.RollBuildupSeconds + Constants.RARITY.COMMON.RevealDuration,
			portal.SpinUpSeconds) >= portal.SpinUpSeconds)

	check("the gate is the larger portal", portal.ExpeditionGateScale > portal.FateEngineScale)

	-- Blueprint §1.1 is declared the single source of truth for rarity colour.
	local BLUEPRINT = {
		COMMON = "9E9E9E", RARE = "3E8EF7", EPIC = "B24BF3",
		MYTHIC = "FF7A1A", LEGENDARY = "FFD447", UNKNOWN = "7CF5E0",
	}
	for key, hex in BLUEPRINT do
		check(string.format("%s uses blueprint colour #%s", key, hex),
			Constants.RARITY[key].Color.hex == hex,
			tostring(Constants.RARITY[key].Color.hex))
	end

	-- Blueprint §4.1/§6: rarity colour is a UI/portal contract; biome palette
	-- is set dressing and must never bleed into it.
	check("Emberfall (Rare) carries the Rare colour, not fire orange",
		Constants.RARITY[Worlds.EMBERFALL.Rarity].Color.hex == "3E8EF7")
	check("Astral Reach (Mythic) carries Mythic orange",
		Constants.RARITY[Worlds.ASTRAL_REACH.Rarity].Color.hex == "FF7A1A")
	check("Verdant Valley (Common) carries Common grey",
		Constants.RARITY[Worlds.VERDANT_VALLEY.Rarity].Color.hex == "9E9E9E")
	-- Ethereal Scape is the WEAKEST test of this contract in the game, and it
	-- is worth naming: its meadows are mint green and Uncommon is green, so
	-- "portal colour came from the rarity table" and "portal colour came from
	-- the biome" would look the same on screen. It still has to hold.
	check("Ethereal Scape (Uncommon) carries the Uncommon colour",
		Constants.RARITY[Worlds.ETHEREAL_SCAPE.Rarity].Color.hex == "5FD97A")

	check("UITheme derives rarity colours from Constants, not its own table",
		UITheme.RarityColors.MYTHIC == Constants.RARITY.MYTHIC.Color)
	check("UITheme is frozen",
		(throws(function() UITheme.AccentGold = nil end)))
end

-- === 10. Biome lighting =============================================
group("Biome lighting (blueprint §3.3 / §4.3 / §5.3)")

do
	local vv, ef, ar = Worlds.VERDANT_VALLEY, Worlds.EMBERFALL, Worlds.ASTRAL_REACH
	local es = Worlds.ETHEREAL_SCAPE

	for _, w in { vv, ef, ar, es } do
		check(string.format("%s declares Brightness and FogStart", w.Id),
			type(w.Environment.Brightness) == "number"
				and type(w.Environment.FogStart) == "number")
	end

	check("Verdant Valley reads as soft midday", vv.Environment.Brightness == 2.5)
	-- Ethereal Scape stands above the cloud deck, so it is lit from every
	-- direction at once. If a brighter world is ever added, this is the
	-- assertion that will notice.
	check("Ethereal Scape is the brightest world in the game",
		es.Environment.Brightness == 3.0
			and es.Environment.Brightness > vv.Environment.Brightness
			and es.Environment.Brightness > ar.Environment.Brightness,
		tostring(es.Environment.Brightness))
	check("Ethereal Scape fog is cloud, so it reaches far rather than closing in",
		es.Environment.FogEnd >= 2000 and es.Environment.FogEnd > vv.Environment.FogEnd,
		string.format("FogEnd %d", es.Environment.FogEnd))
	check("Emberfall is the darkest (lava lights it locally)",
		ef.Environment.Brightness == 1.4
			and ef.Environment.Brightness < ar.Environment.Brightness
			and ef.Environment.Brightness < vv.Environment.Brightness)
	check("Emberfall fog is tightest (ash haze)",
		ef.Environment.FogEnd == 300 and ef.Environment.FogEnd < vv.Environment.FogEnd)
	check("Verdant Valley fog is soft, not oppressive",
		vv.Environment.FogStart == 100 and vv.Environment.FogEnd == 400)
	check("Astral Reach fog is sparse so void-black hides the edges",
		ar.Environment.FogEnd >= 600)

	-- Blueprint §3.5: modifiers re-tint, they do not build new geometry.
	check("Verdant Valley has ModifierOverrides", vv.ModifierOverrides ~= nil)
	check("Night modifier darkens rather than adding geometry",
		vv.ModifierOverrides.NIGHT.Brightness < vv.Environment.Brightness)
	check("Night swaps the ambient particle", vv.ModifierOverrides.NIGHT.ParticleId == "FIREFLIES")

	local declared = {}
	for _, m in vv.Modifiers do declared[m] = true end
	local overridesDeclared = true
	for key in vv.ModifierOverrides do
		if not declared[key] then overridesDeclared = false end
	end
	check("every ModifierOverride names a modifier the world declares", overridesDeclared)
end

-- === 11. Constants sanity ============================================
group("Constants")

do
	local orders = {}
	local uniqueOrders = true
	for key, rarity in Constants.RARITY do
		check(string.format("rarity %s knows its own key", key), rarity.Key == key)
		if orders[rarity.Order] then uniqueOrders = false end
		orders[rarity.Order] = key
	end
	check("rarity orders are unique", uniqueOrders)
	check("rarer results reveal for longer",
		Constants.RARITY.UNKNOWN.RevealDuration > Constants.RARITY.COMMON.RevealDuration)
	check("announce threshold is Mythic or above",
		Constants.ANNOUNCE_RARITY_ORDER >= Constants.RARITY.MYTHIC.Order)

	local frozen = throws(function() Constants.RARITY.COMMON.Order = 99 end)
	check("Constants are frozen against accidental mutation", frozen)
	check("GameConfig is frozen against accidental mutation",
		(throws(function() GameConfig.CurrentPhase = 3 end)))
end

-- === 12. Modular map chunks =========================================
group("Asset manifest & modular map assembly")

do
	-- Manifest ------------------------------------------------------
	local ok, errs = Schema.validateChunks(Chunks, AssetManifest)
	check("the real chunk library validates", ok, table.concat(errs, "; "))

	local uploaded, placeholder = AssetManifest.summary()
	check("manifest reports its status", uploaded + placeholder > 0,
		string.format("%d uploaded, %d placeholder", uploaded, placeholder))
	check("a placeholder resolves to nil so the loader falls back to primitives",
		AssetManifest.assetId("VV_CHUNK_ENTRY") == nil)
	check("an unknown key does not exist", not AssetManifest.exists("NOT_A_REAL_ASSET"))

	-- Every chunk must name an asset that exists, or the kit is broken.
	local everyAssetKnown = true
	local missing
	for id, c in Chunks do
		if not AssetManifest.exists(c.AssetKey) then
			everyAssetKnown = false
			missing = id .. " -> " .. tostring(c.AssetKey)
		end
	end
	check("every chunk's AssetKey is in the manifest", everyAssetKnown, missing)

	local badAsset = {
		X = { Id = "X", WorldId = "W", Role = "PATH", AssetKey = "NOPE",
			SizeX = 1, SizeY = 1, SizeZ = 1, Weight = 1,
			Sockets = { { Id = "a", Kind = "PATH", OffsetX = 0, OffsetY = 0, OffsetZ = 0, Facing = 0 },
				{ Id = "b", Kind = "PATH", OffsetX = 0, OffsetY = 0, OffsetZ = 1, Facing = 180 } } },
	}
	local okb, errsb = Schema.validateChunks(badAsset, AssetManifest)
	check("rejects a chunk naming an unknown asset", not okb, table.concat(errsb, "; "))

	local deadEnd = {
		D = { Id = "D", WorldId = "W", Role = "PATH", AssetKey = "VV_CHUNK_ENTRY",
			SizeX = 1, SizeY = 1, SizeZ = 1, Weight = 1,
			Sockets = { { Id = "a", Kind = "PATH", OffsetX = 0, OffsetY = 0, OffsetZ = 0, Facing = 0 } } },
	}
	local okd, errsd = Schema.validateChunks(deadEnd, AssetManifest)
	check("rejects a one-socket PATH chunk as a dead end", not okd, table.concat(errsd, "; "))

	local badFacing = {
		F = { Id = "F", WorldId = "W", Role = "ENTRY", AssetKey = "VV_CHUNK_ENTRY",
			SizeX = 1, SizeY = 1, SizeZ = 1, Weight = 1,
			Sockets = { { Id = "a", Kind = "PATH", OffsetX = 0, OffsetY = 0, OffsetZ = 0, Facing = 45 } } },
	}
	local okf, errsf = Schema.validateChunks(badFacing, AssetManifest)
	check("rejects an off-grid socket facing", not okf, table.concat(errsf, "; "))

	-- Assembly ------------------------------------------------------
	local lib = ChunkCore.libraryFor(Chunks, "VERDANT_VALLEY")
	check("Verdant Valley has an ENTRY chunk", lib.ENTRY and #lib.ENTRY == 1)
	check("Verdant Valley has a BOSS chunk", lib.BOSS and #lib.BOSS == 1)
	check("Verdant Valley has a SIDE pocket (§6 checklist)", lib.SIDE and #lib.SIDE >= 1)
	-- Pieces must be sized against the character, not against the old hub.
	local CHARH = GameConfig.Scale.CharacterHeight
	local smallest = math.huge
	local smallestId
	for id, c in Chunks do
		local m = math.min(c.SizeX, c.SizeZ)
		if m < smallest then smallest, smallestId = m, id end
	end
	check("the smallest map piece is at least 40 characters across",
		smallest / CHARH >= 40, string.format("%s at %.0f characters", smallestId, smallest / CHARH))

	check("Verdant Valley has connective pieces",
		(#(lib.PATH or {}) + #(lib.COMBAT or {})) >= 4,
		string.format("%d", #(lib.PATH or {}) + #(lib.COMBAT or {})))

	-- THE CORE QUESTION: can it actually build a map out of the pieces?
	local built, failed = 0, {}
	local roleSeen = {}
	for trial = 1, 300 do
		local okA, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 5 },
			function(a) return lcg(trial * 104729 + a * 7919) end, 5)
		if okA then
			built += 1
			for _, c in layout.Chunks do roleSeen[c.Role] = true end
			local okV, errV = ChunkCore.validateLayout(layout, Chunks)
			if not okV then
				table.insert(failed, "trial " .. trial .. ": " .. table.concat(errV, ", "))
			end
		end
	end
	check("assembles a map from the piece library on nearly every seed", built >= 285,
		string.format("%d/300 seeds produced a layout within 5 attempts", built))
	check("every assembled layout is collision-free with one entry and one boss",
		#failed == 0, failed[1])
	check("layouts contain entry, connective pieces and a boss arena",
		roleSeen.ENTRY and roleSeen.BOSS and (roleSeen.PATH or roleSeen.COMBAT))

	-- The arena approach must be the Grove every time -- it is the only WIDE
	-- provider, and WIDE is what the arena accepts. Blueprint §3.2.
	local approachAlwaysGrove = true
	for trial = 1, 60 do
		local okA, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 4 },
			function(a) return lcg(trial * 611953 + a) end, 5)
		if okA then
			local penultimate = layout.Chunks[#layout.Chunks - 1]
			if penultimate.ChunkId ~= "VV_GROVE" then approachAlwaysGrove = false end
		end
	end
	check("the Grove always gates the boss arena (emergent from socket Kinds)",
		approachAlwaysGrove)

	-- A reserved piece must never be spent mid-path.
	local groveOnlyOnce = true
	for trial = 1, 60 do
		local okA, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 6 },
			function(a) return lcg(trial * 15485863 + a) end, 5)
		if okA then
			local n = 0
			for _, c in layout.Chunks do
				if c.ChunkId == "VV_GROVE" then n += 1 end
			end
			if n ~= 1 then groveOnlyOnce = false end
		end
	end
	check("MaxPerLayout is respected", groveOnlyOnce)

	-- Determinism: the same seed must always produce the same map, so an
	-- expedition can be reproduced for debugging or exploit investigation.
	local okA, layoutA = ChunkCore.assemble(Chunks,
		{ WorldId = "VERDANT_VALLEY", PathLength = 2 }, lcg(2026))
	local okB, layoutB = ChunkCore.assemble(Chunks,
		{ WorldId = "VERDANT_VALLEY", PathLength = 2 }, lcg(2026))
	check("assembly is deterministic for a given seed", okA and okB)
	if okA and okB then
		local same = #layoutA.Chunks == #layoutB.Chunks
		for i = 1, #layoutA.Chunks do
			local a, b = layoutA.Chunks[i], layoutB.Chunks[i]
			if a.ChunkId ~= b.ChunkId or a.X ~= b.X or a.Z ~= b.Z or a.Yaw ~= b.Yaw then
				same = false
			end
		end
		check("identical seeds produce identical maps", same)
	end

	-- Different seeds should not all produce the same map.
	local shapes = {}
	for trial = 1, 60 do
		local okS, l = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 4 },
			function(a) return lcg(trial * 7919 + a) end, 5)
		if okS then
			local ids = {}
			for _, c in l.Chunks do table.insert(ids, c.ChunkId) end
			shapes[table.concat(ids, ">")] = true
		end
	end
	local distinct = 0
	for _ in shapes do distinct += 1 end
	check("different seeds produce different maps", distinct > 1,
		string.format("%d distinct layouts", distinct))

	-- Socket Kind is what stops a footpath opening onto the boss arena.
	local bossChunk = Chunks.VV_BOSS_CLEARING
	check("the boss arena only accepts a WIDE approach",
		bossChunk.Sockets[1].Kind == "WIDE", bossChunk.Sockets[1].Kind)
	check("the Grove is the only piece offering a WIDE exit",
		Chunks.VV_GROVE.Sockets[2].Kind == "WIDE")

	-- Geometry helpers ----------------------------------------------
	local placed = { X = 10, Y = 0, Z = 20, Yaw = 90 }
	local sock = { Id = "s", Kind = "PATH", OffsetX = 0, OffsetY = 0, OffsetZ = -48, Facing = 0 }
	local ws = ChunkCore.worldSocket(placed, nil, sock)
	check("a quarter turn rotates a socket offset correctly",
		ws.X == 58 and ws.Z == 20, string.format("(%d, %d)", ws.X, ws.Z))
	check("a quarter turn rotates a socket facing correctly", ws.Facing == 90, tostring(ws.Facing))

	local a = { X = 0, Y = 0, Z = 0, Yaw = 0 }
	local b = { X = 200, Y = 0, Z = 0, Yaw = 0 }
	local box = { SizeX = 96, SizeY = 10, SizeZ = 96 }
	check("distant chunks do not overlap", not ChunkCore.overlaps(a, box, b, box))
	check("stacked chunks do overlap", ChunkCore.overlaps(a, box, a, box))

	-- A kit missing a boss must fail cleanly, not error.
	local partial = { E = Chunks.VV_ENTRY }
	local okP, errP = ChunkCore.assemble(partial,
		{ WorldId = "VERDANT_VALLEY", PathLength = 2 }, lcg(1))
	check("an incomplete kit fails cleanly with a reason", not okP and type(errP) == "string", tostring(errP))

	local okU, errU = ChunkCore.assemble(Chunks,
		{ WorldId = "NO_SUCH_WORLD", PathLength = 2 }, lcg(1))
	check("an unknown world fails cleanly", not okU and type(errU) == "string", tostring(errU))

	-- An expedition must not be mostly walking. At WalkSpeed 32 and a 720s
	-- expedition, a path length of 5 spans ~4100 studs -- about 2 minutes of
	-- traverse, leaving roughly 10 for combat and exploration.
	do
		local okF, layoutF = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 5 },
			function(a) return lcg(104729 + a) end, 5)
		check("a path-length-5 expedition assembles", okF)
		if okF then
			local w, d = ChunkCore.footprint(layoutF)
			local span = math.max(w, d)
			local traverse = span / GameConfig.Scale.WalkSpeed
			local budget = GameConfig.Expedition.DefaultDurationSeconds
			check("an expedition is big enough to feel like a world",
				span > GameConfig.HubLayout.HubDiameter,
				string.format("%.0f studs vs a %d-stud hub", span, GameConfig.HubLayout.HubDiameter))
			check("walking is a minority of the expedition, not the whole thing",
				traverse < budget * 0.35,
				string.format("%.0fs traverse of a %ds expedition (%.0f%%)",
					traverse, budget, traverse / budget * 100))
		end
	end

	-- Retry reports how many attempts it needed, so a kit that is chronically
	-- hard to assemble is visible rather than silently slow.
	local okR, _, used = ChunkCore.assembleWithRetry(Chunks,
		{ WorldId = "VERDANT_VALLEY", PathLength = 3 },
		function(a) return lcg(99 + a) end, 5)
	check("retry reports its attempt count", okR and used >= 1 and used <= 5, tostring(used))
end

-- === 12b. Hub geometry a player can actually touch ==================
-- EVERY CHECK IN THIS GROUP IS A PLAYTEST REGRESSION. The 2026-09-16 Studio
-- pass found the hub had no floor, no complete paths, an unreachable portal
-- and a spawn point inside a walkway -- and all 276 tests were green. These
-- assert the relationships that were silently false.
group("Hub geometry a player can actually touch")

do
	local anchors = GameConfig.HubLayout.Anchors
	local portal = GameConfig.Portal

	-- Roblox's default JumpPower 50 against gravity 196.2 clears about 6.37
	-- studs. Anything a player must get on top of has to be under that.
	local JUMP_HEIGHT = 6.3

	local PORTALS = {
		{ Name = "Fate Engine", Scale = portal.FateEngineScale,
			Reach = GameConfig.UI.PromptActivationDistance },
		{ Name = "Expedition Gate", Scale = portal.ExpeditionGateScale,
			Reach = GameConfig.UI.PromptActivationDistance },
		-- The way home out of an expedition is the same rig at a smaller
		-- scale, and would fail the same way if nobody checked.
		{ Name = "Return portal", Scale = GameConfig.Expedition.ReturnPortalScale,
			Reach = GameConfig.Expedition.ReturnPromptDistance },
	}

	-- 1. A PROMPT MUST REACH THE EDGE OF ITS OWN PLINTH.
	-- ProximityPrompt distance is measured from its part's origin, so a plinth
	-- wider than the prompt's reach locks the player out while standing on it.
	for _, p in PORTALS do
		local plinthRadius = portal.PlinthDiameter * p.Scale * 0.5
		check(
			string.format("%s: the prompt reaches past its own plinth", p.Name),
			p.Reach > plinthRadius,
			string.format("reach %d vs plinth radius %.0f", p.Reach, plinthRadius)
		)
	end

	-- 2. A PLINTH MUST BE A STEP, NOT A WALL.
	for _, p in PORTALS do
		local height = math.min(portal.PlinthHeight * p.Scale, portal.MaxPlinthHeight)
		check(
			string.format("%s: the plinth can be jumped onto", p.Name),
			height < JUMP_HEIGHT,
			string.format("%.1f studs vs a %.1f-stud jump", height, JUMP_HEIGHT)
		)
	end
	check("the plinth height cap is what makes that true at any scale",
		portal.PlinthHeight * portal.ExpeditionGateScale > portal.MaxPlinthHeight,
		"the cap is inert -- it should be binding at the Gate's scale")

	-- 3. THE PLAZA IS A FLOOR, NOT A COLUMN.
	-- It was built as a Part wearing a CylinderMesh, whose axis is Y while
	-- every caller passed the X convention -- so the 1200-stud plaza became a
	-- 1200-stud-tall wall and the hub had no ground at all.
	check("the plaza is a disc, not a column",
		Crossroads.Plaza.Thickness < Crossroads.Plaza.Diameter * 0.1,
		string.format("%d thick vs %d across",
			Crossroads.Plaza.Thickness, Crossroads.Plaza.Diameter))

	-- 4. WALKWAYS MUST MEET THE PLATFORMS THEY SERVE.
	-- The half-extent along the APPROACH, not always X. Hall of Legends is
	-- 320x250 approached down -Z, so its near edge is 125 studs out, not 160;
	-- using X left a hole in the floor between walkway and platform.
	local worstGap, worstZone = math.huge, ""
	for _, d in Crossroads.Districts do
		local anchor = anchors[d.Id]
		local mag = math.sqrt(anchor.X * anchor.X + anchor.Z * anchor.Z)
		if mag > 1 then
			local dx, dz = anchor.X / mag, anchor.Z / mag
			local half = math.abs(dx) * d.PlatformSize.X / 2
				+ math.abs(dz) * d.PlatformSize.Z / 2
			-- Walkway runs from the Engine platform edge to the zone edge.
			local span = mag - half - Crossroads.FateEngine.PlatformRadius
			if span < worstGap then worstGap, worstZone = span, d.Id end
		end
	end
	check("every walkway has a positive span to cross",
		worstGap > 0, string.format("%s at %.0f studs", worstZone, worstGap))

	check("walkways overlap both ends rather than butting up to a seam",
		Crossroads.Bridges.Overlap > 0)

	-- 5. NOTHING HANGS OFF THE EDGE OF THE FLOOR.
	local plazaRadius = Crossroads.Plaza.Diameter / 2
	local worstOverhang, overhangZone = -math.huge, ""
	for _, d in Crossroads.Districts do
		local anchor = anchors[d.Id]
		local mag = math.sqrt(anchor.X * anchor.X + anchor.Z * anchor.Z)
		local far = mag + math.max(d.PlatformSize.X, d.PlatformSize.Z) / 2
		if far - plazaRadius > worstOverhang then
			worstOverhang, overhangZone = far - plazaRadius, d.Id
		end
	end
	check("no zone platform overhangs the plaza it stands on",
		worstOverhang <= 0,
		string.format("%s overhangs by %.0f studs", overhangZone, worstOverhang))

	-- 6. THE SPAWN POINTS ARE NOT INSIDE ANYTHING.
	-- At (0, 8, 250) the old single spawn sat within the processional
	-- walkway's own volume, so Roblox ejected the character upward -- which is
	-- how a playtest opened standing on top of a pillar. The ring inherits the
	-- rule: every pad must clear the deck it hangs over.
	local ring = GameConfig.HubLayout.SpawnRing
	local deckTop = GameConfig.HubLayout.WalkwayRaise + Crossroads.Bridges.Thickness / 2
	check("every spawn pad is above the walkway deck, not inside it",
		ring.Height > deckTop,
		string.format("pad Y %.0f vs deck top %.0f", ring.Height, deckTop))

	-- ...and inside the hub, not out over the plaza edge or off the world.
	check("the spawn ring is on the plaza, not out in space",
		ring.Radius < GameConfig.HubLayout.HubDiameter / 2,
		string.format("ring %d, plaza radius %d",
			ring.Radius, GameConfig.HubLayout.HubDiameter / 2))

	-- ENOUGH PADS TO COVER THE APPROACHES. Four walkways plus four diagonals:
	-- fewer than eight and some players arrive facing a direction with no
	-- path, which is a worse first frame than a short walk.
	check("there are enough spawn pads to cover every approach",
		ring.Count >= 8 and ring.Count % 4 == 0, tostring(ring.Count))

	-- 6b. THE HUB MUST BE LIT WELL ENOUGH TO READ.
	-- "Hub is very dark" was open from the first Studio session to the sixth.
	-- The cause was ClockTime 22 -- the sun below the horizon, so there was no
	-- key light for Brightness to raise, and raising it only blew out the neon.
	local theme = Crossroads.Theme
	check("the hub's key light is above the horizon",
		theme.ClockTime > 4 and theme.ClockTime < 20,
		string.format("ClockTime %.1f", theme.ClockTime))
	check("the hub is brighter than the darkest biome",
		theme.Brightness > Worlds.EMBERFALL.Environment.Brightness,
		string.format("hub %.1f vs Emberfall %.1f",
			theme.Brightness, Worlds.EMBERFALL.Environment.Brightness))
	local function lum(c) return (c.r or 0) + (c.g or 0) + (c.b or 0) end
	check("outdoor fill is brighter than indoor ambient",
		lum(theme.OutdoorAmbient) > lum(theme.Ambient),
		string.format("%d vs %d", lum(theme.OutdoorAmbient), lum(theme.Ambient)))

	-- 6c. THE CONTRACT PARTS OTHER SYSTEMS LOOK UP BY NAME.
	-- HubBuilder hands the hub over to authored geometry when it finds one,
	-- and that used to take the contract with it -- an artist naming a model
	-- "Crossroads" would silently switch off rolling and expedition entry.
	-- ensureContract now re-adds these; it keys off these names and this
	-- district, so a rename here must not go unnoticed.
	for _, key in { "CROSSROADS", "FATE_ENGINE", "ROLL_ANCHOR", "GATE_ANCHOR" } do
		check(string.format("Constants.NAMES.%s is defined", key),
			type(Constants.NAMES[key]) == "string" and #Constants.NAMES[key] > 0,
			tostring(Constants.NAMES[key]))
	end
	local hasGate = false
	for _, d in Crossroads.Districts do
		if d.Id == "EXPEDITION_GATE" then hasGate = true end
	end
	check("the EXPEDITION_GATE district exists (ensureContract asserts on it)", hasGate)

	-- 7. NOTHING MAY ENCIRCLE THE FATE ENGINE.
	-- The Global Observatory's spiral access was a 2.5-turn helix at radius
	-- 118, forty studs wide, so it occupied radius 98 to 138 -- while the
	-- Engine's own platform is radius 120. It wrapped the single most
	-- important object in the game in a wall of steps. Straightening it fixed
	-- the symptom; the district was cut entirely on 2026-09-17 because nobody
	-- could say what it was for.
	--
	-- The Engine's plaza must stay clear whatever is added back. Every
	-- district's platform has to leave the Engine's footprint alone.
	local engineR = Crossroads.FateEngine.PlatformRadius
	local encroaching = {}
	for _, d in Crossroads.Districts do
		local a = anchors[d.Id]
		local reach = math.sqrt(a.X * a.X + a.Z * a.Z)
			- math.max(d.PlatformSize.X, d.PlatformSize.Z) / 2
		if reach < engineR then
			table.insert(encroaching, d.Id)
		end
	end
	check("no district reaches into the Fate Engine's platform",
		#encroaching == 0, table.concat(encroaching, ", "))
end

-- === 13. Ethereal Scape =============================================
group("Ethereal Scape (the map-generation test biome)")

do
	local es = Worlds.ETHEREAL_SCAPE
	check("Ethereal Scape exists and is Uncommon", es ~= nil and es.Rarity == "UNCOMMON")
	check("it is rollable in phase 1", es.EnabledInPhase == 1)
	check("it is in the prototype weight table",
		GameConfig.Fate.PrototypeWeights.ETHEREAL_SCAPE ~= nil)
	check("Uncommon sits between Common and Rare in the ladder",
		Constants.RARITY.COMMON.Order < Constants.RARITY.UNCOMMON.Order
			and Constants.RARITY.UNCOMMON.Order < Constants.RARITY.RARE.Order)

	-- It is a TEST biome. Declaring enemies it does not have would be a lie
	-- the Phase 2 combat work would then have to discover.
	check("it declares no enemies, boss or loot -- combat is still Phase 2",
		#es.Enemies == 0 and es.BossId == nil and es.LootTableId == nil)
	check("its expedition is shorter than the 720s default",
		es.DurationSeconds < GameConfig.Expedition.DefaultDurationSeconds,
		string.format("%ds", es.DurationSeconds))

	-- The onboarding arc must actually hand it out, or a tester waits on a
	-- 15% draw to see the thing they are trying to test.
	local onboardingIndex
	for i, id in GameConfig.Fate.OnboardingSequence do
		if id == "ETHEREAL_SCAPE" then onboardingIndex = i end
	end
	check("onboarding guarantees it inside the first five rolls",
		onboardingIndex ~= nil and onboardingIndex <= 5, tostring(onboardingIndex))

	-- The map ------------------------------------------------------
	-- This world does not assemble a map. It ships one, because the delivered
	-- art is a COMPOSED traverse rather than a set of interchangeable pieces
	-- (see the comment on its PrebuiltMap). The chunk kit that used to live
	-- here was retired with the scene it never matched.
	check("Ethereal Scape declares a prebuilt map", type(es.PrebuiltMap) == "table")
	check("no chunk claims Ethereal Scape any more",
		not ExpeditionCore.hasKit(Chunks, "ETHEREAL_SCAPE"))
	check("its AssetKey is in the manifest",
		AssetManifest.exists(es.PrebuiltMap.AssetKey), tostring(es.PrebuiltMap.AssetKey))
	check("it declares no MapPathLength -- nothing would read it",
		es.MapPathLength == nil)

	-- MEASURED FROM THE DELIVERED FILE, assets/rbxm/maps/ES_ENVIRONMENT_FULL
	-- .rbxmx, not estimated. Re-delivered at Roblox scale 2026-09-17 after the
	-- first cut shipped ~10x oversized.
	--
	-- A RE-DELIVERY MEANS RE-MEASURING THESE. They are a snapshot of one file,
	-- and the previous set went stale the moment the modeller sent a new one.
	-- What they are for is the RELATIONSHIPS below -- none of these tests
	-- assert that a number is a particular number.
	local SCENE_TRAVERSE = 2277 -- studs, island 00 centre to island 07 centre
	local SMALLEST_ISLAND = 228 -- Island_00_Meadow, its widest axis
	local TEMPLE_DOOR_HEIGHT = 53 -- Temple_Entry_Jamb, floor to head
	local CHARACTER_HEIGHT = 5 -- what a Roblox R6 character actually is

	local scale = es.PrebuiltMap.Scale
	local walkSeconds = SCENE_TRAVERSE * scale / GameConfig.Scale.WalkSpeed
	print(string.format("        Ethereal Scape traverse: %.0f studs, %.0fs one way at scale %.2f",
		SCENE_TRAVERSE * scale, walkSeconds, scale))

	-- THE RELATIONSHIP THAT MATTERS, and the one a bad Scale breaks in the
	-- expensive direction. The first delivery walked 642 seconds against a
	-- 300-second expedition.
	check("the walk there and back fits inside the expedition with room to spare",
		walkSeconds * 2 < es.DurationSeconds * 0.75,
		string.format("%.0fs of %ds", walkSeconds * 2, es.DurationSeconds))

	-- ...and the other direction, which is how 0.1 failed its playtest: at
	-- some point an island stops being somewhere you arrive and becomes a
	-- stepping stone. A district platform in the hub is the yardstick, since
	-- that is the smallest space in the game a player is meant to stand around
	-- in.
	check("an island is at least as roomy as a hub district platform",
		SMALLEST_ISLAND * scale >= GameConfig.HubLayout.ZoneRingRadius * 0.4,
		string.format("%.0f studs across", SMALLEST_ISLAND * scale))

	-- THE SCALE SANITY CHECK THAT GENERALISES. Nothing a person walks through
	-- should be dozens of person-heights tall. The first delivery's doorway
	-- was 48; this catches that class of error without pinning a number.
	local doorHeights = TEMPLE_DOOR_HEIGHT * scale / CHARACTER_HEIGHT
	check("the temple doorway is grand, not absurd",
		doorHeights > 1.5 and doorHeights < 20,
		string.format("%.1f person-heights", doorHeights))

	-- Schema: the rules that keep the two routes from blurring -------
	local function mapErrors(world, chunks)
		local _, errs = Schema.validateMaps({ W = world }, chunks or {}, AssetManifest)
		return errs
	end
	check("the real content validates", #mapErrors(es) == 0, mapErrors(es)[1])
	check("a world cannot have both a kit and a prebuilt map",
		#mapErrors(es, { C = { WorldId = "W" } }) == 1,
		mapErrors(es, { C = { WorldId = "W" } })[1])

	local function variant(changes)
		local copy = {}
		for k, v in es do copy[k] = v end
		local pm = {}
		for k, v in es.PrebuiltMap do pm[k] = v end
		for k, v in changes do
			if k == "MapPathLength" then copy[k] = v else pm[k] = v end
		end
		copy.PrebuiltMap = pm
		return copy
	end
	check("an unknown AssetKey is a boot error",
		#mapErrors(variant({ AssetKey = "NO_SUCH_ASSET" })) == 1)
	check("a zero Scale is a boot error",
		#mapErrors(variant({ Scale = 0 })) == 1)
	check("a leftover MapPathLength is a boot error",
		#mapErrors(variant({ MapPathLength = 3 })) == 1)
end

-- === 14. Expedition entry ===========================================
group("Expedition entry (build spec §7.1)")

do
	local function withRolls(history)
		return profile({ RollHistory = history, TotalRolls = #history })
	end

	-- Destination ---------------------------------------------------
	check("a player who has never rolled has no destination",
		ExpeditionCore.destinationFrom(withRolls({})) == nil)
	check("the destination is the most recent roll",
		ExpeditionCore.destinationFrom(withRolls({
			{ WorldId = "VERDANT_VALLEY", Rarity = "COMMON", Timestamp = 1 },
			{ WorldId = "ETHEREAL_SCAPE", Rarity = "UNCOMMON", Timestamp = 2 },
		})) == "ETHEREAL_SCAPE")
	check("a malformed history entry does not crash the lookup",
		ExpeditionCore.destinationFrom(withRolls({ "not a table" })) == nil)

	-- The two ways a world gets a map --------------------------------
	check("Verdant Valley has a kit", ExpeditionCore.hasKit(Chunks, "VERDANT_VALLEY"))
	check("Ethereal Scape does not -- it ships one instead",
		not ExpeditionCore.hasKit(Chunks, "ETHEREAL_SCAPE"))
	check("Ethereal Scape is prebuilt",
		ExpeditionCore.hasPrebuiltMap(Worlds.ETHEREAL_SCAPE))
	check("Verdant Valley is not prebuilt",
		not ExpeditionCore.hasPrebuiltMap(Worlds.VERDANT_VALLEY))
	check("Sky Citadel has neither",
		not ExpeditionCore.hasKit(Chunks, "SKY_CITADEL")
			and not ExpeditionCore.hasPrebuiltMap(Worlds.SKY_CITADEL))

	-- BOTH routes count as having a map. This is the assertion that stops a
	-- prebuilt world being turned away at its own door -- the bug this seam
	-- would otherwise have shipped with.
	check("a prebuilt world has a map",
		ExpeditionCore.hasMap(Worlds.ETHEREAL_SCAPE, Chunks, "ETHEREAL_SCAPE"))
	check("a kitted world has a map",
		ExpeditionCore.hasMap(Worlds.VERDANT_VALLEY, Chunks, "VERDANT_VALLEY"))
	check("a world with neither has no map",
		not ExpeditionCore.hasMap(Worlds.SKY_CITADEL, Chunks, "SKY_CITADEL"))

	-- THE DEBT, ASSERTED. Three rollable worlds cannot be entered. This test
	-- is not here to be green forever -- it is here so the number is in the
	-- suite and someone has to look at it to change it.
	local missing = ExpeditionCore.worldsWithoutMaps(Worlds, Chunks, GameConfig.CurrentPhase)
	print(string.format("        rollable but not enterable: %s", table.concat(missing, ", ")))
	check("rollable-but-not-enterable worlds are reported, sorted",
		#missing == 3 and missing[1] == "ASTRAL_REACH" and missing[2] == "EMBERFALL"
			and missing[3] == "SKY_CITADEL",
		table.concat(missing, ", "))

	-- Map size and duration are content, with a config fallback ------
	-- No world overrides it today -- Ethereal Scape did until it became
	-- prebuilt -- but the override is still how a short world gets a short
	-- map, so it stays tested rather than quietly rotting.
	check("a world's own MapPathLength wins",
		ExpeditionCore.pathLengthFor({ MapPathLength = 3 }, GameConfig) == 3)
	check("a world without one falls back to config",
		ExpeditionCore.pathLengthFor(Worlds.VERDANT_VALLEY, GameConfig)
			== GameConfig.Expedition.PathLength)
	check("duration comes from the world",
		ExpeditionCore.durationFor(Worlds.ETHEREAL_SCAPE, GameConfig) == 300)

	-- Seeding: an expedition must be reproducible from its log line --
	local s1 = ExpeditionCore.seedFor(12345, 7, "ETHEREAL_SCAPE")
	local s2 = ExpeditionCore.seedFor(12345, 7, "ETHEREAL_SCAPE")
	check("the same player, roll and world always seed the same", s1 == s2)
	check("a different roll number seeds differently",
		s1 ~= ExpeditionCore.seedFor(12345, 8, "ETHEREAL_SCAPE"))
	check("a different player seeds differently",
		s1 ~= ExpeditionCore.seedFor(999, 7, "ETHEREAL_SCAPE"))
	check("a different world seeds differently",
		s1 ~= ExpeditionCore.seedFor(12345, 7, "VERDANT_VALLEY"))

	local inRange = true
	for userId = 1, 400 do
		for roll = 1, 5 do
			local seed = ExpeditionCore.seedFor(userId * 104729, roll, "ETHEREAL_SCAPE")
			if seed < 0 or seed >= 2147483647 or seed ~= math.floor(seed) then
				inRange = false
			end
		end
	end
	check("seeds stay whole and inside 2^31", inRange)

	-- Streams: reproducible per attempt, but each attempt is a new try ---
	local a1, a2 = ExpeditionCore.streamFor(s1, 1), ExpeditionCore.streamFor(s1, 1)
	local sameStream = true
	for _ = 1, 200 do
		if a1() ~= a2() then sameStream = false end
	end
	check("the same seed and attempt produce the same stream", sameStream)
	check("a retry does not replay the failed attempt",
		ExpeditionCore.streamFor(s1, 1)() ~= ExpeditionCore.streamFor(s1, 2)())

	-- END TO END: the same player rolling the same world twice must get the
	-- same map, and two different players must not.
	-- Verdant Valley, because determinism is a property of the ASSEMBLER and
	-- Ethereal Scape no longer goes near it.
	local function mapFor(userId, rollNumber)
		local seed = ExpeditionCore.seedFor(userId, rollNumber, "VERDANT_VALLEY")
		local okM, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "VERDANT_VALLEY", PathLength = 3 },
			function(att) return ExpeditionCore.streamFor(seed, att) end,
			GameConfig.Expedition.AssemblyAttempts)
		if not okM then return nil end
		local ids = {}
		for _, c in layout.Chunks do
			table.insert(ids, string.format("%s@%d,%d,%d", c.ChunkId, c.X, c.Z, c.Yaw))
		end
		return table.concat(ids, ">")
	end

	local mine = mapFor(555, 20)
	check("an expedition can be replayed exactly from its seed",
		mine ~= nil and mine == mapFor(555, 20))

	local distinct = {}
	for userId = 1, 40 do
		local m = mapFor(userId * 7919, 20)
		if m then distinct[m] = true end
	end
	local n = 0
	for _ in distinct do n += 1 end
	check("different players get different maps", n > 1, string.format("%d distinct", n))

	-- Timer ---------------------------------------------------------
	check("remaining counts down", ExpeditionCore.remaining(100, 300, 160) == 240)
	check("remaining never goes negative", ExpeditionCore.remaining(100, 300, 9999) == 0)

	-- Stage slots ---------------------------------------------------
	local occupied = {}
	check("the first slot is 1", ExpeditionCore.freeSlot(occupied, 4) == 1)
	occupied[1], occupied[2] = true, true
	check("occupied slots are skipped", ExpeditionCore.freeSlot(occupied, 4) == 3)
	occupied[3], occupied[4] = true, true
	check("a full server returns nil rather than stacking maps",
		ExpeditionCore.freeSlot(occupied, 4) == nil)

	local x, y, z = ExpeditionCore.stageOffset(3, 12000)
	check("stages are spaced apart so two maps cannot intersect",
		x == 24000 and y == 0 and z == 0, string.format("(%d,%d,%d)", x, y, z))
	check("stage spacing exceeds the widest layout a path length can produce",
		GameConfig.Expedition.StageSpacing > 8000)

	check("the entry chunk is findable", ExpeditionCore.entryChunk({
		Chunks = { { Role = "PATH", ChunkId = "A" }, { Role = "ENTRY", ChunkId = "B" } },
	}).ChunkId == "B")

	-- The entry decision, refusal by refusal -------------------------
	local rolled = withRolls({ { WorldId = "ETHEREAL_SCAPE", Rarity = "UNCOMMON", Timestamp = 1 } })

	-- A Lua table literal cannot carry "set this key to nil", and two of the
	-- cases below are precisely about a nil field. NONE is the stand-in.
	local NONE = {}
	local function decide(overrides)
		local opts = {
			Profile = rolled,
			Worlds = Worlds,
			Chunks = Chunks,
			Config = GameConfig,
			Now = 1000,
			LastEntryAt = nil,
			AlreadyActive = false,
			DistanceToGate = 10,
			FreeSlot = 1,
		}
		for k, v in overrides or {} do
			opts[k] = if v == NONE then nil else v
		end
		return ExpeditionCore.evaluateEntry(opts)
	end

	local allowed = decide()
	check("a player who has rolled a world with a map may enter",
		allowed.Allowed and allowed.WorldId == "ETHEREAL_SCAPE",
		tostring(allowed.Refusal))

	check("a player who has not rolled is refused",
		decide({ Profile = withRolls({}) }).Refusal == "NO_DESTINATION")
	check("a world with no map is refused at the door, not mid-assembly",
		decide({ Profile = withRolls({
			{ WorldId = "SKY_CITADEL", Rarity = "EPIC", Timestamp = 1 },
		}) }).Refusal == "NO_MAP")
	check("a destination that no longer exists is refused",
		decide({ Profile = withRolls({
			{ WorldId = "DELETED_WORLD", Rarity = "COMMON", Timestamp = 1 },
		}) }).Refusal == "UNKNOWN_WORLD")
	check("you cannot enter an expedition while on one",
		decide({ AlreadyActive = true }).Refusal == "ALREADY_IN_EXPEDITION")
	check("entry is rate limited", decide({ LastEntryAt = 999.5 }).Refusal == "COOLDOWN")
	check("the cooldown expires", decide({ LastEntryAt = 990 }).Allowed)
	check("you must be at the Gate",
		decide({ DistanceToGate = 5000 }).Refusal == "TOO_FAR")
	check("a missing Gate skips the distance check rather than failing shut",
		decide({ DistanceToGate = NONE }).Allowed)
	check("a full server refuses rather than overlapping maps",
		decide({ FreeSlot = NONE }).Refusal == "SERVER_FULL")

	local off = cfg({ Expedition = { Enabled = false } })
	check("the Phase 2 switch closes the door completely",
		decide({ Config = off }).Refusal == "DISABLED")

	-- The guards must be checked BEFORE anything that reads content, so a
	-- spamming client never reaches the assembler.
	check("cooldown outranks having no destination",
		decide({ Profile = withRolls({}), LastEntryAt = 999.5 }).Refusal == "COOLDOWN")

	-- Silence is the default, for the reason §3.4.3 gives about the roll.
	local spoken = {}
	for _, refusal in { "DISABLED", "NO_DESTINATION", "UNKNOWN_WORLD", "NO_MAP",
		"ALREADY_IN_EXPEDITION", "COOLDOWN", "TOO_FAR", "SERVER_FULL" } do
		if ExpeditionCore.refusalMessage(refusal) then table.insert(spoken, refusal) end
	end
	table.sort(spoken)
	check("only the two refusals a legitimate player can hit say anything",
		#spoken == 2 and spoken[1] == "NO_DESTINATION" and spoken[2] == "NO_MAP",
		table.concat(spoken, ", "))
end

-- === 20. The authored Fate Engine ===================================
group("The authored Fate Engine prefab")

do
	local engine = Crossroads.FateEngine
	local prefab = engine.Prefab

	check("the Engine declares a prefab", type(prefab) == "table")
	check("its AssetKey is in the manifest",
		AssetManifest.exists(prefab.AssetKey), tostring(prefab.AssetKey))
	check("its Scale is positive", type(prefab.Scale) == "number" and prefab.Scale > 0)

	-- MEASURED FROM assets/rbxm/prefabs/HUB_FATE_ENGINE.rbxmx as delivered.
	-- Studio's FBX importer landed it at 0.42x, uniformly. A re-delivery means
	-- re-measuring these; what the tests assert is the RELATIONSHIPS below,
	-- never that Scale is a particular number.
	local RAW_PLATFORM = 101.0 -- Platform, widest axis
	local RAW_PLINTH_H = 1.26 -- Plinth, height
	local RAW_OUTER = 48.48 -- OuterRing, widest axis

	local scale = prefab.Scale

	-- THE ONE THAT MATTERS. The dais is the floor players stand on, and the
	-- hub reserves exactly PlatformRadius for it -- walkways are cut to meet
	-- its edge (Bridges.Overlap). A prefab scaled wrong either floats short of
	-- its own walkways or overhangs the plaza.
	local platform = RAW_PLATFORM * scale
	check("the authored dais matches the platform radius the hub reserves",
		math.abs(platform - engine.PlatformRadius * 2) < engine.PlatformRadius * 0.05,
		string.format("%.1f studs against %d", platform, engine.PlatformRadius * 2))

	-- The plinth cap is a hard rule, not a proportion: a character jumps about
	-- 7 studs and the Gate once shipped an 18-stud plinth that walled off its
	-- own portal. Scale can violate it silently.
	local plinth = RAW_PLINTH_H * scale
	check("the authored plinth is still a step, not a wall",
		plinth <= GameConfig.Portal.MaxPlinthHeight + 0.5,
		string.format("%.2f studs", plinth))

	-- The rig must not overhang the floor it stands on -- the same assertion
	-- the generated rig has always had, applied to the authored one.
	check("the portal rig fits on its own dais",
		RAW_OUTER * scale < engine.PlatformRadius * 2,
		string.format("ring %.1f, dais %d", RAW_OUTER * scale, engine.PlatformRadius * 2))

	-- Every part the code drives by name needs a paint rule, or it stays the
	-- grey Roblox imports it as. Longest matching prefix wins, exactly as
	-- PrefabLoader resolves it.
	local styles = engine.PrefabStyles
	check("a paint table exists", type(styles) == "table")

	local contract = { "Platform", "Plinth", "OuterRing", "InnerRing", "PortalPlane" }
	for i = 1, 8 do
		table.insert(contract, `Rune{i}`)
		table.insert(contract, `Glyph{i}`)
	end
	for i = 1, 6 do
		table.insert(contract, `Shard{i}`)
	end
	for i = 1, 16 do
		table.insert(contract, `Inlay{i}`)
	end

	local unpainted = {}
	for _, name in contract do
		local matched = false
		for prefix in styles do
			if string.sub(name, 1, #prefix) == prefix then
				matched = true
				break
			end
		end
		if not matched then
			table.insert(unpainted, name)
		end
	end
	check("every contract part has a paint rule", #unpainted == 0,
		table.concat(unpainted, ", "))

	-- The counter-rotation is what makes the portal read as a mechanism
	-- rather than a wheel. Asserting the SIGNS, not the speeds.
	local outer = styles.OuterRing.Attributes.SpinSpeed
	local inner = styles.InnerRing.Attributes.SpinSpeed
	check("the rings counter-rotate", outer * inner < 0,
		string.format("outer %.2f, inner %.2f", outer, inner))

	check("the shards are tagged for the rarity cycle",
		styles.Shard.Attributes.IsFeaturedShard == true)

	-- TWO RINGS, NOT THREE. Owner-directed: the inner ring so nearly encases
	-- the portal that they read as one object, so ring 2 is the inner ring
	-- AND the aperture, turning as one against the outer frame.
	local plane = styles.PortalPlane.Attributes.SpinSpeed
	check("the aperture turns against the outer ring", plane ~= nil and plane * outer < 0,
		string.format("outer %.2f, plane %s", outer, tostring(plane)))

	-- Identical, not merely similar. Two nested discs at slightly different
	-- speeds slide against each other, which reads as one of them slipping
	-- rather than as a mechanism -- worse than either extreme.
	check("the aperture and the inner ring turn as ONE ring", plane == inner,
		string.format("plane %.2f, inner %.2f", plane, inner))

	-- SAME SPEED IS NOT ENOUGH -- SAME AXLE TOO. SpinAxis defaults to "Y", so
	-- a part given a ring's speed but no axis turns about the VERTICAL while
	-- the rings turn about their own Z. That looks exactly like "still not
	-- connected", and it is what the fourth walk was still seeing after the
	-- speeds were matched.
	check("everything in the portal assembly turns about the same axle", (function()
		local axis = styles.OuterRing.Attributes.SpinAxis
		for _, name in { "OuterRing", "InnerRing", "PortalPlane" } do
			local attributes = styles[name].Attributes
			if attributes.SpinSpeed ~= nil and attributes.SpinAxis ~= axis then
				return false
			end
		end
		return axis ~= nil
	end)())

	-- THE RINGS SPIN ABOUT THEIR OWN AXLE. A ring is thin along its own Z, so
	-- Z is the axle; spinning it about Y would tumble it end over end. Two
	-- playtests reported "no animation" while this was simply not set.
	check("both rings name Z as their spin axis",
		styles.OuterRing.Attributes.SpinAxis == "Z"
			and styles.InnerRing.Attributes.SpinAxis == "Z")

	-- SPIN SPEED IS A BAND, and both edges are bugs that shipped. Too slow
	-- (0.15 rad/s, 42s a revolution) read as "not animated" for two
	-- playtests; too fast (1.4 rad/s) read as "very very fast" on the third.
	-- Between 8 and 30 seconds a revolution is a machine idling.
	for _, name in { "OuterRing", "InnerRing", "Shard" } do
		local speed = math.abs(styles[name].Attributes.SpinSpeed)
		local seconds = math.pi * 2 / speed
		check(`{name} idles rather than racing or sitting still`,
			seconds >= 8 and seconds <= 30,
			string.format("%.2f rad/s = %.0fs per revolution", speed, seconds))
	end

	-- The crystals must not move as one. A single shared style entry is what
	-- made six of them read as machinery.
	check("the shards vary per crystal", type(styles.Shard.Vary) == "table"
		and (styles.Shard.Vary.SpinSpeed or 0) > 0)

	-- THE VEIL is the surface a player walks through, so it has to be
	-- walkable and it has to be the thing you look at.
	local veil = styles.PortalPlane
	check("the veil is non-colliding -- you walk through a portal",
		veil.CanCollide == false)
	-- VISIBILITY, not transparency. The first version of this test asserted
	-- Transparency < 0.35, which was a proxy that stopped meaning anything the
	-- moment the veil moved from ForceField to Neon -- an emissive surface at
	-- 0.45 reads far brighter than a shimmer at 0.2. Assert the two things
	-- that actually make it visible instead.
	check("the veil is emissive, so it reads against a dark hub",
		veil.Material == Enum.Material.Neon)
	check("the veil never fades far enough to vanish",
		veil.Attributes.PulseAlphaMax < 0.7,
		string.format("peaks at %.2f", veil.Attributes.PulseAlphaMax))

	-- The rings must not turn like a motor. Both carry a sway and a rate that
	-- breathes, which is what separates "suspended" from "bolted on".
	for _, name in { "OuterRing", "InnerRing" } do
		local attrs = styles[name].Attributes
		check(`{name} sways rather than turning perfectly true`,
			(attrs.WobbleDegrees or 0) > 0 and (attrs.SpinJitter or 0) > 0)
	end
	check("the veil has a breath of its own",
		veil.Attributes.PulseAlphaMin ~= nil)

	-- THE RINGS MUST NEST, AND STAY NESTED WHILE THEY MOVE. This has broken
	-- three times: a 6% veil pulse that grew it through its frame, mismatched
	-- wobble periods that swung the inner assembly out of the outer aperture,
	-- and a swell on the outer ring that shrank the hole the inner one sits
	-- in. Raw widths measured from the delivered mesh at Prefab.Scale; a
	-- re-delivery re-measures them.
	local RAW_OUTER, RAW_OUTER_TUBE = 48.48, 4.84
	local RAW_INNER, RAW_VEIL = 34.34, 32.82

	local function width(raw, style)
		return raw * scale * ((style and style.SizeScale) or 1)
			* (1 + ((style and style.Attributes and style.Attributes.PulseScale) or 0))
	end

	local aperture = width(RAW_OUTER, styles.OuterRing) - 2 * RAW_OUTER_TUBE * scale
	local innerW = width(RAW_INNER, styles.InnerRing)
	local veilW = width(RAW_VEIL, veil)

	-- The clearance floor scales with the world, because the ring does.
	check("the inner ring clears the outer aperture with room to sway",
		(aperture - innerW) / 2 > 1 * GameConfig.HubLayout.WorldScale,
		string.format("%.2f studs a side", (aperture - innerW) / 2))
	check("the veil sits inside the ring it fills",
		veilW < innerW, string.format("veil %.2f, ring %.2f", veilW, innerW))

	-- ...and the two rings must lean as ONE object. Different wobble periods
	-- is what let the inner assembly swing out through the outer one.
	check("both rings share a single sway",
		styles.OuterRing.Attributes.WobbleDegrees == styles.InnerRing.Attributes.WobbleDegrees
			and styles.OuterRing.Attributes.WobbleSeconds == styles.InnerRing.Attributes.WobbleSeconds)

	-- Nothing in the hub may use a built-in Roblox material. Owner-directed:
	-- their grain fights flat-shaded low-poly geometry, and Glass in
	-- particular is expensive on the phones the §6 checklist budgets for.
	local TEXTURED = {
		[Enum.Material.Marble] = "Marble",
		[Enum.Material.Slate] = "Slate",
		[Enum.Material.Basalt] = "Basalt",
		[Enum.Material.Metal] = "Metal",
		[Enum.Material.Glass] = "Glass",
	}
	local textured = {}
	for name, style in styles do
		if style.Material and TEXTURED[style.Material] then
			table.insert(textured, `{name} ({TEXTURED[style.Material]})`)
		end
	end
	check("no part of the Engine uses a textured Roblox material",
		#textured == 0, table.concat(textured, ", "))

	-- The frame must not emit, or it merges with the aperture it frames.
	check("the inner ring is matte so the veil reads as the light source",
		styles.InnerRing.Material ~= Enum.Material.Neon)

	-- THE ROLL RAMP. The portal winds up, holds while the result builds, and
	-- coasts down as the colour lands. Three relationships make that read as
	-- one gesture rather than three effects that happen to overlap.
	local portal = GameConfig.Portal
	check("rolling actually winds the portal up",
		portal.SpinBoostPeak > 1, string.format("%.1fx", portal.SpinBoostPeak))
	check("it snaps up and coasts down, not the reverse",
		portal.SpinRampUpSeconds < portal.SpinWindDownSeconds,
		string.format("up %.1fs, down %.1fs", portal.SpinRampUpSeconds, portal.SpinWindDownSeconds))
	-- The colour is the answer; it must arrive WHILE the rings are still
	-- slowing. Finishing after them would leave the portal sitting at rest on
	-- the wrong colour, which is worse than snapping.
	check("the colour lands before the rings finish slowing",
		portal.RarityTweenSeconds <= portal.SpinWindDownSeconds,
		string.format("colour %.1fs, wind-down %.1fs",
			portal.RarityTweenSeconds, portal.SpinWindDownSeconds))

	-- Performance: the animator runs every frame on every client, including
	-- the phones the §6 checklist budgets for.
	check("distant parts stop animating",
		GameConfig.Effects.AnimationDistance > 0
			and GameConfig.Effects.AnimationDistance < GameConfig.HubLayout.VisualExtent,
		string.format("%d studs", GameConfig.Effects.AnimationDistance))
	check("expensive properties are written below frame rate",
		GameConfig.Effects.SlowUpdateSeconds > 1 / 60,
		string.format("%.3fs", GameConfig.Effects.SlowUpdateSeconds))

	-- WALKWAYS MUST NOT BURY THE DAIS. The deck sits below the dais top, or
	-- it runs over the platform the Engine stands on and hides it -- which is
	-- what the second authored playtest reported.
	local daisTop = engine.PlatformRaise
	check("walkway decks sit below the dais they meet",
		GameConfig.HubLayout.WalkwayRaise < daisTop,
		string.format("deck %.1f against dais top %.1f",
			GameConfig.HubLayout.WalkwayRaise, daisTop))

	-- ...and must not bite so far in that there is no dais left to see.
	check("the walkway overlap leaves most of the dais visible",
		Crossroads.Bridges.Overlap < engine.PlatformRadius * 0.25,
		string.format("%d studs into a %d radius",
			Crossroads.Bridges.Overlap, engine.PlatformRadius))
end


-- === 21. The authored Crossroads shell ==============================
group("The authored Crossroads shell")

do
	local shell = Crossroads.Shell

	-- A LIGHT SOURCE DOES NOT MOVE. Owner-directed 2026-09-21 after seeing the
	-- market: the glow is right, the drifting is not -- a lamp that spins or
	-- bobs reads as a floating object rather than as a fixture. Colour
	-- animation (PulseAlpha) stays; anything that changes POSITION does not.
	--
	-- The Fate Engine's shards are deliberately out of scope: they orbit
	-- because they are part of a machine, not because they are a light.
	check("no lamp, lantern or finial moves", (function()
		local moving = {}
		for name, style in shell.Styles do
			local isFixture = string.find(name, "Lamp")
				or string.find(name, "Lantern")
				or string.find(name, "Finial")
				or string.find(name, "GatewayCrystals")
			local attributes = style.Attributes
			if isFixture and attributes then
				for _, key in { "SpinSpeed", "BobStuds", "BobSeconds", "WobbleDegrees", "WobbleSeconds" } do
					if attributes[key] ~= nil then
						table.insert(moving, `{name}.{key}`)
					end
				end
			end
		end
		return #moving == 0, table.concat(moving, ", ")
	end)())

	check("...but they still pulse, which is what makes them read as lit", (function()
		local lit = 0
		for name, style in shell.Styles do
			if
				(string.find(name, "Lamp") or string.find(name, "Lantern"))
				and style.Attributes
				and style.Attributes.PulseAlphaMax ~= nil
			then
				lit += 1
			end
		end
		return lit >= 2
	end)())
	local prefab = shell and shell.Prefab

	check("the hub declares a shell prefab", type(prefab) == "table")
	check(
		"its AssetKey is in the manifest",
		AssetManifest.exists(prefab.AssetKey),
		tostring(prefab.AssetKey)
	)

	-- MEASURED FROM assets/rbxm/prefabs/HUB_CROSSROADS.rbxmx AS DELIVERED.
	-- Studio's FBX importer halved it, uniformly. A re-delivery means
	-- re-measuring these four; what the tests assert is the RELATIONSHIPS
	-- below, never that Scale is a particular number.
	local RAW_RESERVE = 23.0 -- EngineReserve, width
	local RAW_WALKWAY_W = 22.0 -- Walkway_North, width
	local RAW_WALKWAY_T = 0.750031 -- Walkway_North, thickness
	local RAW_RING = 200.0 -- district centre to hub centre
	local RAW_PLAZA = 652.626648 -- Plaza, width
	local RAW_DECK = 7.0000267 -- District_Shop, thickness

	local scale = prefab.Scale
	check("its Scale is positive", type(scale) == "number" and scale > 0)

	-- THE ONE THAT MATTERS MOST. The authored reserve is the footprint the
	-- Fate Engine's dais lands on, and the hub cuts its walkways to exactly
	-- FateEngine.PlatformRadius. If the two disagree the player walks to the
	-- centre and finds a step, a gap, or a dais floating inside its own floor.
	check(
		"the authored Engine footprint matches the dais radius the hub reserves",
		math.abs(RAW_RESERVE * scale - Crossroads.FateEngine.PlatformRadius * 2) < 1,
		string.format(
			"%.2f studs against %d",
			RAW_RESERVE * scale,
			Crossroads.FateEngine.PlatformRadius * 2
		)
	)

	-- Three more independent dimensions that must all fall out of the SAME
	-- number. One agreeing measurement is a coincidence; four is a scale.
	check(
		"the authored walkways are the width the layout declares",
		math.abs(RAW_WALKWAY_W * scale - GameConfig.HubLayout.WalkwayWidth) < 1,
		string.format("%.2f against %d", RAW_WALKWAY_W * scale, GameConfig.HubLayout.WalkwayWidth)
	)
	check(
		"the authored walkway deck is the single low step the layout declares",
		math.abs(RAW_WALKWAY_T * scale - GameConfig.HubLayout.WalkwayRaise) < 0.25,
		string.format("%.2f against %.1f", RAW_WALKWAY_T * scale, GameConfig.HubLayout.WalkwayRaise)
	)
	check(
		"the authored districts stand on the compass ring the anchors use",
		math.abs(RAW_RING * scale - GameConfig.HubLayout.ZoneRingRadius) < 1,
		string.format("%.2f against %d", RAW_RING * scale, GameConfig.HubLayout.ZoneRingRadius)
	)

	-- THE FLOOR MUST REACH UNDER EVERYTHING THAT STANDS ON IT. A district
	-- platform hanging off the edge of the plaza is the bug the ZoneRingRadius
	-- comment in GameConfig records being fixed once already, and an authored
	-- plaza is a new chance to reintroduce it.
	-- Measured from the delivery, not from the blockout district table: the
	-- artist built the platforms larger than the brief asked, so the blockout
	-- sizes would understate exactly the number this is checking.
	local RAW_WIDEST_DECK = 200.0 -- District_Shop / District_Leaderboard, X
	local plazaRadius = RAW_PLAZA * scale / 2
	local furthest = GameConfig.HubLayout.ZoneRingRadius + RAW_WIDEST_DECK * scale / 2
	check(
		"the authored plaza reaches under the furthest district",
		plazaRadius > furthest,
		string.format("plaza radius %.1f, furthest edge %.1f", plazaRadius, furthest)
	)
	check(
		"the authored plaza covers the playable diameter the layout promises",
		plazaRadius * 2 >= GameConfig.HubLayout.HubDiameter,
		string.format("%.1f against %d", plazaRadius * 2, GameConfig.HubLayout.HubDiameter)
	)

	-- THE COMPASS CORRECTION. The delivery arrived with north at +Z while
	-- HubLayout.Anchors puts north at -Z. That is a rotation, and a rotation
	-- about the vertical only: a value that is not a quarter turn would mean
	-- the hub had been TILTED, which no importer setting can cause and which
	-- would put every district at a different height.
	check(
		"the compass correction is a quarter turn",
		prefab.YawDegrees % 90 == 0,
		tostring(prefab.YawDegrees)
	)

	-- Registration. The shell is placed from a named part rather than from
	-- the model pivot, and the part it names has to be one the contract
	-- guarantees is there -- otherwise the loader falls back to the pivot and
	-- the hub lands somewhere nobody predicted.
	check(
		"the shell registers from a part in its own contract",
		prefab.AnchorPart == "EngineReserve"
	)

	-- THE ENGINE'S DAIS MUST BE FLUSH WITH THE PATHS THAT MEET IT. The first
	-- authored walk asked for the two to be one continuous surface rather
	-- than a step, and the Offset that achieves it is derived from the
	-- walkway height -- so this pins the RESULT, which is what a player feels.
	local RAW_PLATFORM_TOP = 1.934 * GameConfig.HubLayout.WorldScale -- Platform top above the pivot
	local engineOffset = Crossroads.FateEngine.Prefab.Offset
	check("the Engine declares a placement offset", typeof(engineOffset) == "Vector3")

	-- ON THE PLAZA, NOT ON THE WALKWAYS. The first attempt put the dais flush
	-- with the four paths, which still left a step for anyone crossing the
	-- open plaza -- most of the approach angles, and the second walk said so.
	-- The plaza is Y 0, so the dais top must be too.
	local daisTop = RAW_PLATFORM_TOP + engineOffset.Y
	check(
		"the authored dais lands flush with the plaza, walkable from any angle",
		math.abs(daisTop) < 0.05,
		string.format("dais top %.3f", daisTop)
	)
	-- Approaching along a path is then a step DOWN, which is free. Stepping
	-- UP is the thing that catches, so the dais must never be the higher one.
	check(
		"arriving along a walkway is a step down onto the dais, never up",
		daisTop <= GameConfig.HubLayout.WalkwayRaise,
		string.format("dais %.3f vs walkway %.1f", daisTop, GameConfig.HubLayout.WalkwayRaise)
	)
	-- Only the height is corrected: nudging it sideways would walk the dais
	-- off the footprint the shell reserves for it.
	check("the Engine is only moved vertically", engineOffset.X == 0 and engineOffset.Z == 0)

	-- The deck height behaviour is placed from must match the art it is
	-- placed on. Derived here from the delivered platform rather than copied.
	local deck = RAW_DECK * scale
	check(
		"the declared deck height matches the authored platform",
		math.abs(shell.DeckHeight - deck) < 0.5,
		string.format("declared %d, measured %.2f", shell.DeckHeight, deck)
	)
end

do
	local shell = Crossroads.Shell
	local styles = shell.Styles
	check("a paint table exists", type(styles) == "table")

	-- Longest matching prefix wins, exactly as PrefabLoader.styleFor resolves
	-- it. Reimplemented here rather than imported because PrefabLoader needs
	-- Roblox services this suite does not have -- so if the two ever diverge,
	-- that is the thing to fix.
	local function resolve(name)
		local best, bestLength = nil, -1
		for prefix, style in styles do
			if #prefix > bestLength and string.sub(name, 1, #prefix) == prefix then
				best, bestLength = style, #prefix
			end
		end
		return best
	end

	-- Every part the loader is told to require must have a colour, or it
	-- stays the grey Roblox imports it as.
	local contract = {
		"Plaza",
		"EngineReserve",
		"Walkway_North",
		"Walkway_East",
		"Walkway_West",
		"Processional_South",
		"District_Leaderboard",
		"District_Archive",
		"District_Shop",
		"District_Training",
	}
	local unpainted = {}
	for _, name in contract do
		if not resolve(name) then
			table.insert(unpainted, name)
		end
	end
	check("every contract part has a paint rule", #unpainted == 0, table.concat(unpainted, ", "))

	-- THE FLOOR COLLIDES AND ITS TRIM DOES NOT. PrefabLoader turns collision
	-- OFF for every part by default and content turns it back on, which is
	-- the right way round -- but it means a missing entry is a hole in the
	-- world, and a careless prefix is a 1300-stud invisible lip.
	check("the authored plaza is solid ground", resolve("Plaza").CanCollide == true)
	check("the plaza's proud trim disc is not", resolve("PlazaRim").CanCollide ~= true)

	-- PREFIX RESOLUTION IS THE REAL RISK IN THIS TABLE, and it is silent when
	-- it goes wrong: a district's dressing inheriting the PLATFORM's entry
	-- would make banners and lanterns solid, and nothing would say so. These
	-- are the cases where one key is a prefix of another, including the
	-- `.001` suffixes the FBX export left on duplicated objects.
	-- EVERY WALKABLE SURFACE. A player walks the plaza, up a walkway, up a
	-- flight of stairs and onto a deck. Every step of that has to be solid, or
	-- the route simply ends -- and a route that ends is the one hub bug this
	-- project has already shipped twice.
	local mustBeSolid = {
		"Plaza",
		"Walkway_North",
		"Walkway_East",
		"Walkway_West",
		"Processional_South",
		"District_Leaderboard",
		"District_Archive",
		"District_Shop",
		"District_Training",
		"District_Training_YardFloor",
	}
	for _, district in { "Leaderboard", "Archive", "Shop", "Training" } do
		table.insert(mustBeSolid, `District_{district}_Stairs`)
		table.insert(mustBeSolid, `District_{district}_StairCheeks`)
		table.insert(mustBeSolid, `District_{district}_StairRails`)
	end
	local notSolid = {}
	for _, name in mustBeSolid do
		local style = resolve(name)
		if not style or style.CanCollide ~= true then
			table.insert(notSolid, name)
		end
	end
	check(
		"every surface on the walk from spawn to a district is solid",
		#notSolid == 0,
		table.concat(notSolid, ", ")
	)

	-- THE MESHES THAT MERGE MANY OBJECTS MUST NOT COLLIDE, and this is the
	-- assertion that would have caught the mistake that was nearly shipped
	-- here. All 225 parts arrive with empty PhysicsData, so Roblox builds
	-- their hulls at Default fidelity, which fills openings. A filled hull on
	-- any of these is an invisible wall across a route:
	--
	--   Walkways_Gateways              seals all four walkway mouths
	--   Processional_South_Guardians   seals the spawn approach
	--   Plaza_RimParapet               lays a slab across the whole floor
	--   District_Archive_Columns       fills the rotunda
	--   District_Shop_EntrancePylons   seals the market entrance
	--   District_Training_Wall         fills the yard
	--
	-- If one of these ever needs to stop a player, the answer is a
	-- CollisionFidelity on that entry -- never CanCollide on its own.
	local mustNotSeal = {
		"Walkways_Gateways",
		"Processional_South_Guardians",
		"Plaza_RimParapet",
		"Plaza_Obelisks",
		"District_Archive_Columns",
		"District_Archive_Balustrade",
		"District_Archive_Shelves",
		"District_Shop_EntrancePylons",
		"District_Shop_Columns",
		"District_Shop_StallStructures",
		"District_Training_Wall",
		"District_Training_DummyPosts",
		"District_Leaderboard_Seating",
		"District_Leaderboard_Balustrade",
	}
	local sealed = {}
	for _, name in mustNotSeal do
		local style = resolve(name)
		if style and style.CanCollide == true and not style.CollisionFidelity then
			table.insert(sealed, name)
		end
	end
	-- THESE NOW COLLIDE, AND MUST. The first pass left every one of them
	-- pass-through -- the safe half of a choice that could not be checked
	-- headlessly -- and the walk found the cost: players sank into platform
	-- flanks and walked through railings. They are solid now, and each
	-- carries an explicit fidelity, because a Default hull would seal the
	-- opening that makes it the shape it is.
	local mustBeSolidAndPrecise = {
		"District_Archive_Columns",
		"District_Shop_EntrancePylons",
		"District_Training_Wall",
		"Walkways_Gateways",
		"Processional_South_Guardians",
		"District_Leaderboard_Balustrade",
	}
	local notPrecise = {}
	for _, name in mustBeSolidAndPrecise do
		local style = resolve(name)
		if not style or style.CanCollide ~= true or not style.CollisionFidelity then
			table.insert(notPrecise, name)
		end
	end
	check(
		"structure a player leans on is solid, and precisely so",
		#notPrecise == 0,
		table.concat(notPrecise, ", ")
	)

	-- The skirt under each deck is what a player sinks into when it is
	-- missing, which is exactly what the walk reported.
	local sunk = {}
	for _, d in { "Leaderboard", "Archive", "Shop", "Training" } do
		local style = resolve(`District_{d}_Skirt`)
		if not style or style.CanCollide ~= true then
			table.insert(sunk, d)
		end
	end
	check("no district platform has a hollow flank", #sunk == 0, table.concat(sunk, ", "))

	-- THE KERBS MUST REACH WHAT THEY RUN TO. Authored from radius 60 while
	-- their walkway runs from 20, so every path had 40 studs of bare deck and
	-- the black edging stopped in mid-air short of the dais.
	local short = {}
	for _, key in { "Walkway_North_Edge", "Walkway_East_Edge", "Walkway_West_Edge", "Processional_South_Edge" } do
		local style = resolve(key)
		if
			not style
			or not style.ExtendInwardTo
			or style.ExtendInwardTo >= Crossroads.FateEngine.PlatformRadius
		then
			table.insert(short, key)
		end
	end
	check("every walkway kerb is extended to meet the dais", #short == 0, table.concat(short, ", "))

	check(
		"no merged or hollow mesh collides at Default fidelity",
		#sealed == 0,
		table.concat(sealed, ", ")
	)

	-- ...and the plain case: dressing must not inherit its platform's entry,
	-- including the `.001` suffixes the FBX export left on duplicates.
	local shouldNotCollide = {
		"District_Leaderboard_BannerCloth",
		"District_Archive_Dome.001",
		"District_Archive_TomeGlow",
		"District_Shop_DisplayGoods.017",
		"District_Shop_Signs",
		"District_Training_BannerCloth",
		"Walkways_Banners.010",
		"FloatingIsland3",
		"Backdrop_TreeCanopies",
		"EngineReserve",
	}
	local solid = {}
	for _, name in shouldNotCollide do
		local style = resolve(name)
		if not style or style.CanCollide == true then
			table.insert(solid, name)
		end
	end
	check(
		"no piece of dressing inherited its platform's collision",
		#solid == 0,
		table.concat(solid, ", ")
	)

	-- The marker exists to be measured from, never to be seen.
	check(
		"the Engine's reserved footprint is invisible",
		resolve("EngineReserve").Transparency == 1
	)

	-- Nothing in the hub may use a built-in Roblox material. Owner-directed
	-- 2026-09-18, and the same assertion the Engine's paint table carries --
	-- applied to a table twelve times its size, where eyeballing it is not a
	-- realistic check.
	local TEXTURED = {
		[Enum.Material.Marble] = "Marble",
		[Enum.Material.Slate] = "Slate",
		[Enum.Material.Basalt] = "Basalt",
		[Enum.Material.Metal] = "Metal",
		[Enum.Material.Glass] = "Glass",
		[Enum.Material.Sand] = "Sand",
		[Enum.Material.Grass] = "Grass",
		[Enum.Material.Wood] = "Wood",
		[Enum.Material.WoodPlanks] = "WoodPlanks",
		[Enum.Material.Concrete] = "Concrete",
		[Enum.Material.Brick] = "Brick",
		[Enum.Material.Cobblestone] = "Cobblestone",
		[Enum.Material.CorrodedMetal] = "CorrodedMetal",
	}
	local textured = {}
	for name, style in styles do
		if style.Material and TEXTURED[style.Material] then
			table.insert(textured, `{name} ({TEXTURED[style.Material]})`)
		end
	end
	check(
		"no part of the hub shell uses a textured Roblox material",
		#textured == 0,
		table.concat(textured, ", ")
	)
end

do
	-- THE EXPEDITION GATE HAS NO GATE, AND THAT IS ON PURPOSE.
	-- Owner-directed after the first authored walk: a "Verdant Valley / ENTER"
	-- prompt standing in the middle of the market is not where a biome gets
	-- entered. The authored hub therefore declares no gate anchor at all, and
	-- entry waits for the Fate Engine's portal.
	--
	-- This pins the DELIBERATE gap so it cannot be closed by accident -- if a
	-- future change puts a gate back on the market, this fails and asks why.
	check("the authored hub declares no Expedition Gate anchor",
		Crossroads.Shell.GateAnchorTop == nil)

	-- The district itself still exists in content: the EXPEDITION_GATE ->
	-- SHOP rename is a separate, still-ungated change.
	local ids = {}
	for _, d in Crossroads.Districts do
		ids[d.Id] = true
	end
	check("the district it belonged to is still declared", ids.EXPEDITION_GATE == true)
end

do
	-- THE HORIZON IS BUILT, NOT PLACED. Three attempts at scaling the
	-- delivered ring into position failed, because the distance from the hub
	-- to its nearest peak is a property of a mesh nothing here can measure --
	-- so every scale was a guess. Cloning one chunk around a circle makes
	-- distance a number, and a number is testable.
	local backdrop = Crossroads.Backdrop
	local ring = backdrop and backdrop.Ring

	check("the hub declares a horizon", type(ring) == "table")
	check("its AssetKey is in the manifest", AssetManifest.exists(backdrop.AssetKey), tostring(backdrop.AssetKey))
	check("the chunk it clones has a paint rule", backdrop.Styles[ring.Part] ~= nil, tostring(ring.Part))

	-- Measured from the delivered file: Backdrop_Mountain is 2048 studs
	-- across at Scale 1.0, so half of it reaches this far from a chunk centre.
	local CHUNK_HALF = 1024.0 * ring.Scale
	local plazaRadius = 652.626648 * Crossroads.Shell.Prefab.Scale / 2
	local near = ring.Radius - CHUNK_HALF
	local far = ring.Radius + CHUNK_HALF

	-- THE WHOLE POINT. Owner-directed: 500 to 1000 studs of clear sky between
	-- the crossroads edge and the mountains. This is the assertion the three
	-- failed scale attempts never had, because with a whole placed model
	-- there was no number to assert against.
	local gap = near - plazaRadius
	-- The owner asked for 500-1000 studs of clear sky when the hub was twice
	-- this size. The ASK is a proportion of the world, not an absolute, so it
	-- scales with it -- otherwise a half-size hub would demand the same
	-- absolute gap and push the horizon out of fog range.
	local clearMin = 500 * GameConfig.HubLayout.WorldScale
	local clearMax = 1000 * GameConfig.HubLayout.WorldScale
	check(
		string.format("the mountains stand %.0f-%.0f studs clear of the crossroads edge", clearMin, clearMax),
		gap >= clearMin and gap <= clearMax,
		string.format("%.0f studs of clear sky (near face %.0f, plaza %.0f)", gap, near, plazaRadius)
	)

	-- ...and clear of the hub's own ground skirt, which is what the ring was
	-- cutting through when it was merely clear of the plaza.
	local GROUND_RADIUS = 548.4949 * Crossroads.Shell.Prefab.Scale
	check(
		"the mountains stand clear of the hub's ground, not through it",
		near > GROUND_RADIUS,
		string.format("near face %.0f, ground radius %.0f", near, GROUND_RADIUS)
	)

	-- The far side must stay inside the fog or the range ends in a hard line.
	check(
		"the far side of the range fades rather than ending",
		far <= Crossroads.Theme.FogEnd,
		string.format("far face %.0f, fog %d", far, Crossroads.Theme.FogEnd)
	)

	-- CHUNKS MUST OVERLAP, or the horizon is a ring of separate lumps with
	-- sky between them. Arc length per chunk against the chunk's own width.
	local circumference = 2 * math.pi * ring.Radius
	local coverage = (ring.Count * CHUNK_HALF * 2) / circumference
	check(
		"there are enough chunks to form a continuous range",
		coverage >= 1.5,
		string.format("%.2fx coverage from %d chunks", coverage, ring.Count)
	)

	-- STANDING ON THE HUB'S GROUND. Derived the same way the shell's own
	-- ground plane is, so the two cannot drift apart silently.
	local SHELL_ANCHOR_Y = 34.7237511 -- EngineReserve centre, as delivered
	local shellGround = -(SHELL_ANCHOR_Y + Crossroads.Shell.Prefab.AnchorOffset.Y)
		* Crossroads.Shell.Prefab.Scale
	check(
		"the horizon stands on the same ground plane as the plaza",
		math.abs(ring.BaseY - shellGround) < 2,
		string.format("%.4f against %.4f in world studs", ring.BaseY, shellGround)
	)

	-- One skyline per server, like the floating islands. A horizon that
	-- reshuffles on every boot is a bug nobody would think to report.
	check("the horizon is deterministic across servers", type(ring.Seed) == "number")
	check(
		"the chunks are jittered so they do not read as copies",
		ring.YawJitterDegrees > 0 and ring.ScaleJitter > 0
	)
end


-- === 22. The portal's yaw, and the hub's animation budget ============
group("The portal turns, and the hub breathes")

do
	local cfg = GameConfig.Portal
	local styles = Crossroads.FateEngine.PrefabStyles

	-- THE ASSEMBLY TURNS AS ONE. Two rings, the veil, the clamps that hold
	-- the frame and the floating core. Not the plinth and not the glyphs --
	-- those are the base it turns above. Any one of these missing and the
	-- portal comes apart as it rotates.
	local missing = {}
	for _, name in { "OuterRing", "InnerRing", "PortalPlane", "RingFoot_Clamps", "LevitationCore" } do
		if not (styles[name] and styles[name].YawFollow) then
			table.insert(missing, name)
		end
	end
	check(
		"every part of the portal assembly turns with it",
		#missing == 0,
		table.concat(missing, ", ")
	)

	-- ...and nothing else does. A glyph or a shard picking this up would
	-- orbit the hub rather than spin, because the yaw is applied about the
	-- hub's axis and those parts are not on it.
	local strays = {}
	for name, style in styles do
		if
			style.YawFollow
			and name ~= "OuterRing"
			and name ~= "InnerRing"
			and name ~= "PortalPlane"
			and name ~= "RingFoot_Clamps"
			and name ~= "LevitationCore"
		then
			table.insert(strays, name)
		end
	end
	check("nothing off the portal's axis turns with it", #strays == 0, table.concat(strays, ", "))

	-- ONE MECHANISM, NOT TWO. The rings spin about their own axle and the
	-- assembly turns about the vertical; at different rates they read as two
	-- machines bolted together.
	check(
		"the portal turns at the same rate its rings spin",
		math.abs(cfg.YawIdleSpeed - math.abs(styles.OuterRing.Attributes.SpinSpeed)) < 0.01,
		string.format(
			"yaw %.2f, ring %.2f",
			cfg.YawIdleSpeed,
			styles.OuterRing.Attributes.SpinSpeed
		)
	)

	-- IT STOPS SQUARE TO THE HUB. Four slots, so the portal always comes to
	-- rest facing a walkway -- which is where a staircase up to it has to
	-- land. A count that does not divide the compass would leave it stopping
	-- at angles no path reaches.
	check("the portal stops on a quarter turn", cfg.YawSlots == 4, tostring(cfg.YawSlots))
	check("its slots divide the compass evenly", 360 % (360 / cfg.YawSlots) == 0)

	-- The yaw is applied about the WORLD vertical through the origin, which
	-- is only the Engine's own axis because the Engine sits there. This is
	-- the assumption that line rests on.
	local engine = GameConfig.HubLayout.Anchors.FATE_ENGINE
	check(
		"the Engine sits on the hub origin, which is what the yaw turns about",
		engine.X == 0 and engine.Z == 0,
		string.format("(%.1f, %.1f)", engine.X, engine.Z)
	)
end

do
	-- THE ANIMATION BUDGET. Spin, Bob and Wobble write a CFrame EVERY frame;
	-- transparency and size pulses run at GameConfig.Effects.SlowUpdateSeconds
	-- and cost almost nothing. The hub is meant to feel alive on a phone, so
	-- the expensive kind is capped and the cheap kind is not.
	--
	-- This counts STYLE KEYS rather than parts, which understates the real
	-- total -- a key like PlazaOuter_NE_Crystals paints one part, but the
	-- four-corner loop stamps four keys. It is still the number that moves
	-- when someone adds an animation, which is what a budget needs to catch.
	local perFrame, pulseOnly = {}, 0
	for name, style in Crossroads.Shell.Styles do
		local a = style.Attributes
		if a then
			if a.SpinSpeed or a.BobStuds or a.WobbleDegrees then
				table.insert(perFrame, name)
			elseif a.PulseAlphaMin or a.PulseScale then
				pulseOnly += 1
			end
		end
	end

	check(
		"the hub animates enough to feel alive",
		#perFrame + pulseOnly >= 20,
		string.format("%d per-frame, %d pulse-only", #perFrame, pulseOnly)
	)
	check(
		"...but not so much that a phone pays for it every frame",
		#perFrame <= 30,
		string.format("%d styles write a CFrame per frame", #perFrame)
	)

	-- Distance culling is what makes the rest affordable: a hub 1300 studs
	-- across would otherwise animate its far side for nobody.
	check(
		"animation is culled before it reaches the far side of the hub",
		GameConfig.Effects.AnimationDistance < GameConfig.HubLayout.HubDiameter,
		string.format(
			"cull %d, hub %d",
			GameConfig.Effects.AnimationDistance,
			GameConfig.HubLayout.HubDiameter
		)
	)
end

-- === the hub menu ===================================================
do
	group("The hub menu, as data")

	local ok, errors = Schema.validateHubMenu(Menu, GameConfig)
	check("the shipped menu validates", ok, table.concat(errors, "; "))

	local panels = HubMenuCore.panels(Menu)
	check("every panel the owner asked for exists", (function()
		local wanted = { "TRAVEL", "SHOP", "CODES", "SKILLS", "PARTY", "REBIRTH", "SETTINGS" }
		for _, id in wanted do
			if not HubMenuCore.panelById(Menu, id) then
				return false
			end
		end
		return true
	end)())

	-- The owner's order, 2026-09-20. Pinned because it is a deliberate
	-- grouping (get somewhere, get someone, progression, transactions,
	-- settings) and alphabetical or add-order drift would undo it silently.
	check("the rail is in the order the owner set", (function()
		local wanted = { "TRAVEL", "PARTY", "SKILLS", "REBIRTH", "SHOP", "CODES", "SETTINGS" }
		for index, id in wanted do
			if panels[index] == nil or panels[index].Id ~= id then
				return false
			end
		end
		return #panels == #wanted
	end)())

	check("panels come back in rail order", (function()
		for i = 2, #panels do
			if panels[i - 1].Order > panels[i].Order then
				return false
			end
		end
		return true
	end)())

	-- THE BUG THIS PREVENTS, which reached Studio: content named the collapse
	-- key "Backslash"; Roblox calls it "BackSlash". Indexing an Enum with a
	-- name it does not have RAISES rather than returning nil, so every
	-- keystroke threw and took the panel shortcuts down with it. Checking
	-- names against a list the suite can see turns that into a boot failure.
	check("every hotkey is a name Roblox actually has", (function()
		for _, panel in Menu.Panels do
			if panel.Hotkey ~= nil and not Constants.HOTKEY_NAMES[panel.Hotkey] then
				return false
			end
		end
		return Constants.HOTKEY_NAMES[Menu.CollapseHotkey] == true
	end)())

	check("the collapse key is BackSlash, with the capital S",
		Menu.CollapseHotkey == "BackSlash")

	check("a misspelled hotkey fails validation", (function()
		local broken = { Panels = {}, Destinations = Menu.Destinations, CollapseHotkey = "Backslash" }
		for _, panel in Menu.Panels do
			table.insert(broken.Panels, panel)
		end
		local ok = Schema.validateHubMenu(broken, GameConfig)
		return not ok
	end)())

	check("no two panels share a hotkey", (function()
		local seen = {}
		for _, panel in Menu.Panels do
			if panel.Hotkey then
				if seen[panel.Hotkey] then
					return false
				end
				seen[panel.Hotkey] = true
			end
		end
		return true
	end)())

	-- The rail is the thing the owner asked not to be overwhelming. A hard
	-- cap turns "do not add a tenth button" from taste into a failing build.
	check("the rail stays short enough to read at a glance", #panels <= 8,
		string.format("%d panels", #panels))

	check("sorting the result cannot reorder the content table", (function()
		local first = Menu.Panels[1].Id
		local copy = HubMenuCore.panels(Menu)
		table.sort(copy, function(a, b) return a.Order > b.Order end)
		return Menu.Panels[1].Id == first
	end)())

	-- === travel =====================================================
	local destinations = HubMenuCore.destinations(Menu)
	check("there are five destinations -- the Engine and the four districts",
		#destinations == 5, string.format("%d", #destinations))

	check("every destination names a real hub anchor", (function()
		for _, destination in destinations do
			if GameConfig.HubLayout.Anchors[destination.AnchorId] == nil then
				return false
			end
		end
		return true
	end)())

	check("every district in Content/Hub/Crossroads is reachable", (function()
		for _, district in Crossroads.Districts do
			if not HubMenuCore.destinationById(Menu, district.Id) then
				return false
			end
		end
		return true
	end)())

	check("landing points are offsets from the anchor, not absolute positions", (function()
		for _, destination in destinations do
			local point = HubMenuCore.landingPoint(destination)
			local expected = destination.Anchor + destination.Landing
			if point.X ~= expected.X or point.Y ~= expected.Y or point.Z ~= expected.Z then
				return false
			end
		end
		return true
	end)())

	-- A landing must not be so far from its anchor that the district it
	-- names is not the district you arrive in. Platforms run to 320 studs
	-- across, so half of that is the widest a landing can honestly be.
	check("a landing stays on the platform it names", (function()
		for _, destination in destinations do
			local landing = destination.Landing
			if math.sqrt(landing.X ^ 2 + landing.Z ^ 2) > 160 then
				return false
			end
		end
		return true
	end)())

	check("the Fate Engine's landing clears its dais", (function()
		local engine = HubMenuCore.destinationById(Menu, "FATE_ENGINE")
		local distance = math.sqrt(engine.Landing.X ^ 2 + engine.Landing.Z ^ 2)
		-- The authored Platform is ~47 studs across, so anything inside ~24
		-- would stand the player inside the dais geometry.
		return distance > 24
	end)())

	check("nobody arrives below the hub floor", (function()
		for _, destination in destinations do
			if destination.Landing.Y <= 0 then
				return false
			end
		end
		return true
	end)())

	-- SPAWNING OUT OF EVERY PROMPT'S REACH. Owner-directed: a player was
	-- offered ROLL before they had pressed PLAY. The spawn ring and the
	-- prompt reach must not drift back together, because the gap between
	-- them is where a first-join tutorial lives.
	check("nobody spawns inside the Fate Engine's prompt", (function()
		local spawn = GameConfig.HubLayout.SpawnRing.Radius
		return spawn > GameConfig.UI.PromptActivationDistance
	end)(), string.format("spawn %.0f, prompt reach %.0f",
		GameConfig.HubLayout.SpawnRing.Radius, GameConfig.UI.PromptActivationDistance))

	check("...nor inside the distance a roll is allowed from",
		GameConfig.HubLayout.SpawnRing.Radius > GameConfig.Fate.MaxRollDistance,
		string.format("spawn %.0f, roll reach %.0f",
			GameConfig.HubLayout.SpawnRing.Radius, GameConfig.Fate.MaxRollDistance))

	-- ...but still on the plaza, looking at the Engine, rather than out among
	-- the districts.
	check("...and still well inside the districts",
		GameConfig.HubLayout.SpawnRing.Radius < GameConfig.HubLayout.ZoneRingRadius,
		string.format("spawn %.0f, districts %.0f",
			GameConfig.HubLayout.SpawnRing.Radius, GameConfig.HubLayout.ZoneRingRadius))

	-- === the visibility rule ========================================
	check("the menu is visible in the hub", HubMenuCore.isVisible(nil, GameConfig))
	check("the menu is NOT visible on an expedition",
		not HubMenuCore.isVisible({ WorldId = "ETHEREAL_SCAPE" }, GameConfig))
	check("one config flag turns the whole menu off",
		not HubMenuCore.isVisible(nil, cfg({ HubMenu = { Enabled = false } })))

	-- === the reducer ================================================
	local state = HubMenuCore.newState(GameConfig, false)
	check("a desktop rail starts open", state.Collapsed == false)
	check("a touch rail starts collapsed",
		HubMenuCore.newState(GameConfig, true).Collapsed == GameConfig.HubMenu.StartCollapsedOnTouch)

	state = HubMenuCore.reduce(state, { Kind = "TOGGLE_PANEL", PanelId = "TRAVEL" }, GameConfig)
	check("toggling a panel opens it", state.OpenPanelId == "TRAVEL")

	state = HubMenuCore.reduce(state, { Kind = "TOGGLE_PANEL", PanelId = "SHOP" }, GameConfig)
	check("opening a second panel closes the first", state.OpenPanelId == "SHOP")

	state = HubMenuCore.reduce(state, { Kind = "TOGGLE_PANEL", PanelId = "SHOP" }, GameConfig)
	check("toggling the open panel closes it", state.OpenPanelId == nil)

	state = HubMenuCore.reduce(state, { Kind = "OPEN_PANEL", PanelId = "CODES" }, GameConfig)
	state = HubMenuCore.reduce(state, { Kind = "TOGGLE_COLLAPSE" }, GameConfig)
	check("collapsing the rail takes the panel with it",
		state.Collapsed and state.OpenPanelId == nil)

	state = HubMenuCore.reduce(state, { Kind = "TOGGLE_COLLAPSE" }, GameConfig)
	check("expanding again does not restore the panel", state.OpenPanelId == nil)

	state = HubMenuCore.reduce(state, { Kind = "OPEN_PANEL", PanelId = "TRAVEL" }, GameConfig)
	state = HubMenuCore.reduce(state, { Kind = "SET_VISIBLE", Visible = false }, GameConfig)
	check("leaving the hub closes whatever was open",
		state.Visible == false and state.OpenPanelId == nil)

	check("the reducer never mutates the state it was given", (function()
		local before = HubMenuCore.newState(GameConfig, false)
		HubMenuCore.reduce(before, { Kind = "OPEN_PANEL", PanelId = "SHOP" }, GameConfig)
		return before.OpenPanelId == nil
	end)())

	-- === travel authorisation =======================================
	local function request(overrides)
		local r = {
			DestinationId = "HALL_OF_LEGENDS",
			OnExpedition = false,
			Rolling = false,
		}
		for k, v in overrides or {} do r[k] = v end
		return r
	end

	check("a plain request is allowed", HubMenuCore.canTravel(Menu, request(), GameConfig).ok)

	check("a fabricated destination is refused by name", (function()
		local result = HubMenuCore.canTravel(Menu, request({ DestinationId = "MOON" }), GameConfig)
		return not result.ok and result.err == "Unknown destination."
	end)())

	check("a non-string destination is refused rather than resolved", (function()
		return not HubMenuCore.canTravel(Menu, request({ DestinationId = 5 }), GameConfig).ok
	end)())

	check("travel is refused on an expedition",
		not HubMenuCore.canTravel(Menu, request({ OnExpedition = true }), GameConfig).ok)

	check("travel is refused mid-roll",
		not HubMenuCore.canTravel(Menu, request({ Rolling = true }), GameConfig).ok)

	-- NO COOLDOWN, owner-directed. Travelling twice in a row is allowed, and
	-- the config must not grow a cooldown field by the back door -- a version
	-- of this that only removed the CHECK would leave the next session to
	-- find the number and wire it back up.
	check("travelling twice in a row is allowed",
		HubMenuCore.canTravel(Menu, request(), GameConfig).ok
			and HubMenuCore.canTravel(Menu, request(), GameConfig).ok)

	check("no travel cooldown exists to be checked",
		GameConfig.HubMenu.TeleportCooldownSeconds == nil
			and HubMenuCore.travelCooldownRemaining == nil)

	-- The rate limit is a spam guard, not a cooldown wearing another name: a
	-- player pressing the button as fast as they can must never meet it.
	check("the rate limit is far above what a human can press",
		GameConfig.HubMenu.TeleportRequestsPerMinute >= 30,
		string.format("%d/min", GameConfig.HubMenu.TeleportRequestsPerMinute))

	-- The fade covers the swap, so the player never sees the world change --
	-- and it is now the ONLY thing between pressing TRAVEL and arriving, so
	-- it has a ceiling as well as a floor.
	local timing = HubMenuCore.travelTiming(GameConfig)
	check("the travel fade is long enough to hide the swap",
		timing.FadeOut > 0 and timing.Total > timing.FadeOut)
	check("...and short enough to read as instant",
		timing.Total <= 0.75, string.format("%.2fs", timing.Total))
end

-- === the loading screen's shots =====================================
do
	group("The loading screen")

	local ok, errors = Schema.validateCinematics(Cinematics, Worlds)
	check("the shipped shot list validates", ok, table.concat(errors, "; "))

	check("there is more than one shot", #Cinematics.Shots > 1)

	-- A shot of a biome would be a shot of empty sky: expedition maps are
	-- built 20000 studs up and only while somebody is inside one. Until
	-- expeditions move to their own place, every shot must be a hub shot.
	check("every shot frames geometry that exists while loading", (function()
		for _, shot in Cinematics.Shots do
			if shot.WorldId ~= nil then
				return false
			end
		end
		return true
	end)())

	-- THE SHOTS ARE DISTANCES, SO THEY SCALE WITH THE WORLD. When they did
	-- not, the cameras stayed put while the hub halved underneath them and
	-- the loading screen framed empty sky with something small in the middle
	-- -- reported as "the background is not working".
	check("every shot frames the hub rather than empty sky", (function()
		local hub = GameConfig.HubLayout.HubDiameter
		for _, shot in Cinematics.Shots do
			-- Closer than four hub-widths (so the hub fills something of the
			-- frame) and further than a tenth of one (so it is not inside a
			-- building).
			if shot.Radius > hub * 4 or shot.Radius < hub * 0.1 then
				return false
			end
		end
		return true
	end)())

	check("no shot puts the camera inside its own subject", (function()
		for _, shot in Cinematics.Shots do
			if shot.Radius <= 0 or shot.Height <= 0 then
				return false
			end
		end
		return true
	end)())

	-- The tour must outlast the minimum hold, or a player on a warm client
	-- sees the first shot cut mid-move on the way to the Play button.
	check("one shot outlasts the minimum hold",
		GameConfig.Loading.ShotSeconds >= GameConfig.Loading.MinimumSeconds,
		string.format("shot %.1fs, hold %.1fs",
			GameConfig.Loading.ShotSeconds, GameConfig.Loading.MinimumSeconds))

	check("the screen can never trap a player",
		GameConfig.Loading.MaximumSeconds > GameConfig.Loading.MinimumSeconds)

	-- THE BUG THIS REPLACED. The screen waited for a fixed instance count --
	-- 380, guessed -- against a hub that builds 357. The bar could only ever
	-- reach 94%, so every player waited out the 25-second timeout and was
	-- told loading had "taken longer than usual". Waiting for replication to
	-- SETTLE needs no number and survives the art changing, and these assert
	-- the floor stays a floor rather than creeping back into a target.
	check("there is no fixed instance target to get wrong",
		GameConfig.Loading.RequiredHubInstances == nil)

	check("the instance floor is far below any hub the game would ship",
		GameConfig.Loading.MinimumHubInstances <= 200,
		string.format("%d", GameConfig.Loading.MinimumHubInstances))

	check("the settle window is longer than the poll that measures it",
		GameConfig.Loading.HubSettleSeconds > GameConfig.Loading.HubPollSeconds,
		string.format("settle %.2fs, poll %.2fs",
			GameConfig.Loading.HubSettleSeconds, GameConfig.Loading.HubPollSeconds))

	-- The timeout has to leave room for the settle to happen at all, or the
	-- screen would time out before it could ever succeed.
	check("the timeout allows for a minimum wait plus a settle",
		GameConfig.Loading.MaximumSeconds
			> GameConfig.Loading.MinimumSeconds + GameConfig.Loading.HubSettleSeconds)

	-- Reported from Studio as "the camera locks in place". At 26 degrees over
	-- nine seconds it moved about three degrees a second.
	check("a shot moves fast enough to be seen moving",
		GameConfig.Loading.ShotArcDegrees / GameConfig.Loading.ShotSeconds >= 4,
		string.format("%.1f deg/s",
			GameConfig.Loading.ShotArcDegrees / GameConfig.Loading.ShotSeconds))
end

-- === codes ==========================================================
do
	group("Redeemable codes")

	local ok, errors = Schema.validateCodes(Codes)
	check("the shipped code list validates", ok, table.concat(errors, "; "))

	check("case does not matter", CodeCore.normalise("LuckBound") == "LUCKBOUND")
	check("spaces and punctuation do not matter",
		CodeCore.normalise(" luck-bound ") == "LUCKBOUND")
	check("a non-string normalises to empty", CodeCore.normalise(nil) == "")

	local function freshProfile()
		return ProfileSchema.default(1700000000)
	end

	check("a valid code is accepted", CodeCore.redeem(Codes, freshProfile(), "luckbound", 1700000000, GameConfig).ok)

	check("the reward comes from content, never from the caller", (function()
		local result = CodeCore.redeem(Codes, freshProfile(), "LUCKBOUND", 1700000000, GameConfig)
		return result.ok and result.value.Fate == Codes.LAUNCH.Fate
	end)())

	check("an unknown code is refused", (function()
		local result = CodeCore.redeem(Codes, freshProfile(), "NOPE", 1700000000, GameConfig)
		return not result.ok and result.err == "That code is not valid."
	end)())

	check("an empty code asks for one", (function()
		local result = CodeCore.redeem(Codes, freshProfile(), "   ", 1700000000, GameConfig)
		return not result.ok and result.err == "Enter a code."
	end)())

	-- The cap is checked on the RAW string, so a megabyte of punctuation is
	-- refused before it is normalised rather than after.
	check("an oversized code is refused before it is processed", (function()
		local huge = string.rep("!", GameConfig.Codes.MaxLength + 1)
		return not CodeCore.redeem(Codes, freshProfile(), huge, 1700000000, GameConfig).ok
	end)())

	check("the same code cannot be redeemed twice", (function()
		local profile = freshProfile()
		local first = CodeCore.redeem(Codes, profile, "LUCKBOUND", 1700000000, GameConfig)
		CodeCore.record(profile, first.value.Id, 1700000000)
		local second = CodeCore.redeem(Codes, profile, "luck bound", 1700000000, GameConfig)
		return not second.ok and second.err == "You have already redeemed that code."
	end)())

	check("deciding does not write", (function()
		local profile = freshProfile()
		CodeCore.redeem(Codes, profile, "LUCKBOUND", 1700000000, GameConfig)
		return next(profile.RedeemedCodes) == nil
	end)())

	check("an expired code says so rather than 'not valid'", (function()
		local expired = {
			OLD = { Id = "OLD", Code = "OLDCODE", Fate = 10, Message = "hi", ExpiresAt = 100 },
		}
		local result = CodeCore.redeem(expired, freshProfile(), "OLDCODE", 200, GameConfig)
		return not result.ok and result.err == "That code has expired."
	end)())

	check("codes can be closed with one flag",
		not CodeCore.redeem(Codes, freshProfile(), "LUCKBOUND", 1700000000,
			cfg({ Codes = { Enabled = false } })).ok)

	check("a code grants Fate through the same maths as any other award", (function()
		local profile = freshProfile()
		local points, level = ProgressionCore.grant(profile, Codes.TESTER.Fate, GameConfig)
		return points == Codes.TESTER.Fate and level == ProgressionCore.levelForPoints(points, GameConfig)
	end)())

	check("a negative grant is a programmer error, not a refund",
		(throws(function()
			ProgressionCore.grant(freshProfile(), -50, GameConfig)
		end)))
end

-- === settings =======================================================
do
	group("Player settings")

	local defaults = SettingsCore.defaults()
	check("every setting in the spec has a default", (function()
		for _, entry in SettingsCore.SPEC do
			if defaults[entry.Id] == nil then
				return false
			end
		end
		return true
	end)())

	check("a number setting clamps rather than refusing",
		SettingsCore.validate("MusicVolume", 5).value == 1)
	check("...at both ends", SettingsCore.validate("MusicVolume", -3).value == 0)
	check("NaN falls back to the default rather than being stored",
		SettingsCore.validate("MusicVolume", 0 / 0).value == 0.6)
	check("a boolean setting refuses a number",
		not SettingsCore.validate("ReduceMotion", 1).ok)
	check("an unknown setting is refused",
		not SettingsCore.validate("GodMode", true).ok)
	check("a non-string id is refused", not SettingsCore.validate(7, true).ok)

	local sanitised = SettingsCore.sanitise({
		MusicVolume = 99,
		GodMode = true,
		ReduceMotion = "yes",
	})
	check("sanitising clamps what it can", sanitised.MusicVolume == 1)
	check("sanitising drops what it cannot", sanitised.GodMode == nil)
	check("sanitising replaces a bad value with its default",
		sanitised.ReduceMotion == false)
	check("sanitising fills in everything missing", (function()
		for _, entry in SettingsCore.SPEC do
			if sanitised[entry.Id] == nil then
				return false
			end
		end
		return true
	end)())
	check("anything at all can be sanitised", (function()
		return SettingsCore.sanitise("nonsense").MusicVolume == 0.6
	end)())

	check("a new profile carries valid settings", (function()
		local profile = ProfileSchema.default(1700000000)
		for _, entry in SettingsCore.SPEC do
			if profile.Settings[entry.Id] == nil then
				return false
			end
		end
		return true
	end)())
end

-- === movement =======================================================
do
	group("Player abilities: run and double jump")

	local function state()
		return LocomotionCore.newState(GameConfig, 0)
	end

	local function sprintFor(seconds, from)
		local s = from or state()
		local dt = 1 / 60
		local elapsed = 0
		while elapsed < seconds do
			s = LocomotionCore.step(s, dt, {
				WantsSprint = true,
				Moving = true,
				Grounded = true,
				Now = elapsed,
			}, GameConfig)
			elapsed += dt
		end
		return s, elapsed
	end

	check("a fresh state starts with full stamina",
		LocomotionCore.staminaFraction(state(), GameConfig) == 1)

	check("sprinting is faster than walking", (function()
		local s = sprintFor(0.5)
		return LocomotionCore.targetSpeed(s, GameConfig) > GameConfig.Scale.WalkSpeed
	end)())

	-- Sprint is a multiplier on the hub's traversal budget, never a second
	-- speed to keep in step with it.
	check("sprint speed is derived from the hub's walk speed", (function()
		local s = sprintFor(0.5)
		return LocomotionCore.targetSpeed(s, GameConfig)
			== GameConfig.Scale.WalkSpeed * GameConfig.Locomotion.SprintMultiplier
	end)())

	check("holding sprint while stood still costs nothing", (function()
		local s = LocomotionCore.step(state(), 1, {
			WantsSprint = true,
			Moving = false,
			Grounded = true,
			Now = 0,
		}, GameConfig)
		return s.Stamina == GameConfig.Locomotion.StaminaMax and not s.Sprinting
	end)())

	check("stamina drains while sprinting", (function()
		local s = sprintFor(2)
		return s.Stamina < GameConfig.Locomotion.StaminaMax
	end)())

	local drained = sprintFor(GameConfig.Locomotion.StaminaMax / GameConfig.Locomotion.StaminaDrainPerSecond + 0.5)
	check("a sprint ends when stamina runs out",
		drained.Stamina == 0 and not drained.Sprinting)

	check("you cannot restart a sprint the instant you run dry",
		not LocomotionCore.canStartSprint(drained, drained.RegenBlockedUntil - 0.1, GameConfig))

	check("stamina refills once the delay has passed", (function()
		local s = drained
		local now = s.RegenBlockedUntil + 0.001
		for _ = 1, 60 do
			s = LocomotionCore.step(s, 1 / 60, {
				WantsSprint = false,
				Moving = true,
				Grounded = true,
				Now = now,
			}, GameConfig)
			now += 1 / 60
		end
		return s.Stamina > 0
	end)())

	check("stamina never exceeds its maximum", (function()
		local s = state()
		for i = 1, 600 do
			s = LocomotionCore.step(s, 1 / 60, {
				WantsSprint = false,
				Moving = true,
				Grounded = true,
				Now = i / 60,
			}, GameConfig)
		end
		return s.Stamina == GameConfig.Locomotion.StaminaMax
	end)())

	check("a full drain takes the number of seconds the config says it does", (function()
		local seconds = GameConfig.Locomotion.StaminaMax / GameConfig.Locomotion.StaminaDrainPerSecond
		-- 8 seconds of sprint. Long enough to cross a district, short enough
		-- that it is a decision.
		return seconds >= 5 and seconds <= 12
	end)())

	-- === jumps ======================================================
	check("the first jump on the ground is the ground jump",
		LocomotionCore.jumpKind(state(), 0, GameConfig) == "GROUND")

	check("the second press in the air is the air jump", (function()
		local s, kind = LocomotionCore.jump(state(), 0, GameConfig)
		if kind ~= "GROUND" then return false end
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false, Now = 0.5,
		}, GameConfig)
		local _, second = LocomotionCore.jump(s, 0.5, GameConfig)
		return second == "AIR"
	end)())

	check("there is no third jump", (function()
		local s, _ = LocomotionCore.jump(state(), 0, GameConfig)
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false, Now = 0.5,
		}, GameConfig)
		local afterAir = select(1, LocomotionCore.jump(s, 0.5, GameConfig))
		local _, third = LocomotionCore.jump(afterAir, 1.5, GameConfig)
		return third == nil
	end)())

	check("one input frame cannot spend two jumps", (function()
		local s = state()
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false, Now = 1,
		}, GameConfig)
		-- Already past the coyote window, so the first press is the air jump.
		s.LastGroundedAt = 0
		local afterFirst, first = LocomotionCore.jump(s, 1, GameConfig)
		local _, second = LocomotionCore.jump(afterFirst, 1, GameConfig)
		return first == "AIR" and second == nil
	end)())

	check("landing gives the jumps back", (function()
		local s = state()
		s.AirJumpsUsed = GameConfig.Locomotion.AirJumps
		s.GroundJumpSpent = true
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = true, Now = 2,
		}, GameConfig)
		return s.AirJumpsUsed == 0 and s.GroundJumpSpent == false
	end)())

	-- THE COYOTE WINDOW. Walking off a walkway and jumping must spend the
	-- GROUND jump, not the air jump -- otherwise stepping off an edge
	-- silently costs the player their double jump.
	check("stepping off an edge still gets the ground jump", (function()
		local s = state()
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false,
			Now = GameConfig.Locomotion.CoyoteTimeSeconds * 0.5,
		}, GameConfig)
		return LocomotionCore.jumpKind(s, GameConfig.Locomotion.CoyoteTimeSeconds * 0.5, GameConfig) == "GROUND"
	end)())

	check("...but only for a moment", (function()
		local s = state()
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false,
			Now = GameConfig.Locomotion.CoyoteTimeSeconds * 3,
		}, GameConfig)
		return LocomotionCore.jumpKind(s, GameConfig.Locomotion.CoyoteTimeSeconds * 3, GameConfig) == "AIR"
	end)())

	check("the coyote window does not hand out an extra jump", (function()
		local s = state()
		s = LocomotionCore.step(s, 1 / 60, {
			WantsSprint = false, Moving = true, Grounded = false,
			Now = GameConfig.Locomotion.CoyoteTimeSeconds * 0.5,
		}, GameConfig)
		local afterGround = select(1, LocomotionCore.jump(s, GameConfig.Locomotion.CoyoteTimeSeconds * 0.5, GameConfig))
		local afterAir, kind = LocomotionCore.jump(afterGround, 0.4, GameConfig)
		local _, third = LocomotionCore.jump(afterAir, 1.0, GameConfig)
		return kind == "AIR" and third == nil
	end)())

	check("stepping does not mutate the state it was given", (function()
		local before = state()
		LocomotionCore.step(before, 1, {
			WantsSprint = true, Moving = true, Grounded = true, Now = 0,
		}, GameConfig)
		return before.Stamina == GameConfig.Locomotion.StaminaMax
	end)())

	-- PHASE SCOPE, PINNED. Movement abilities may not grow combat numbers:
	-- a sword carries its own damage, and the day this config has a damage
	-- field is the day that rule quietly broke.
	check("no player ability config carries a combat number", (function()
		for key in GameConfig.Locomotion do
			local lowered = string.lower(key)
			if string.find(lowered, "damage") or string.find(lowered, "attack")
				or string.find(lowered, "crit") or string.find(lowered, "dps") then
				return false
			end
		end
		return true
	end)())
end


-- === event scope and precedence =====================================
do
	group("Which event owns the sky")

	local function event(overrides)
		local e = {
			Id = "E1",
			Kind = "FATEBREAK",
			Name = "Test",
			Scope = "SERVER",
			Priority = 0,
			StartedAt = 1000,
			EndsAt = 2000,
		}
		for k, v in overrides or {} do e[k] = v end
		return e
	end

	check("no events means no dominant event", EventCore.dominant({}) == nil)

	check("one event owns the sky by default",
		EventCore.dominant({ event({}) }).Id == "E1")

	-- Scope outranks priority on purpose: a game-wide event is by definition
	-- the biggest news on screen, and a local event with a high number must
	-- not shout over something happening to every player in the game.
	check("a global event beats a server event", (function()
		local winner = EventCore.dominant({
			event({ Id = "LOCAL", Scope = "SERVER", Priority = 99 }),
			event({ Id = "WORLDWIDE", Scope = "GLOBAL", Priority = 0 }),
		})
		return winner.Id == "WORLDWIDE"
	end)())

	check("a server event beats a biome event", (function()
		local winner = EventCore.dominant({
			event({ Id = "BIOME", Scope = "BIOME", WorldId = "EMBERFALL", Priority = 50 }),
			event({ Id = "SERVER", Scope = "SERVER", Priority = 0 }),
		}, { WorldId = "EMBERFALL" })
		return winner.Id == "SERVER"
	end)())

	check("priority decides within a scope", (function()
		local winner = EventCore.dominant({
			event({ Id = "QUIET", Priority = 1 }),
			event({ Id = "LOUD", Priority = 9 }),
		})
		return winner.Id == "LOUD"
	end)())

	-- A tie broken by recency would flip the sky every time an equal event
	-- started somewhere, and a sky that changes for no visible reason reads
	-- as a bug rather than as an event.
	check("a tie goes to the event that has been running longest", (function()
		local winner = EventCore.dominant({
			event({ Id = "NEW", StartedAt = 1500 }),
			event({ Id = "OLD", StartedAt = 1000 }),
		})
		return winner.Id == "OLD"
	end)())

	check("a total tie is still deterministic", (function()
		local a = EventCore.dominant({ event({ Id = "B" }), event({ Id = "A" }) })
		local b = EventCore.dominant({ event({ Id = "A" }), event({ Id = "B" }) })
		return a.Id == b.Id and a.Id == "A"
	end)())

	-- A BIOME event is confined to its world. Someone standing in the hub
	-- must not get Emberfall's sky.
	check("a biome event is invisible outside its biome",
		EventCore.dominant({ event({ Scope = "BIOME", WorldId = "EMBERFALL" }) }, { WorldId = nil }) == nil)

	check("...and visible inside it",
		EventCore.dominant({ event({ Scope = "BIOME", WorldId = "EMBERFALL" }) },
			{ WorldId = "EMBERFALL" }) ~= nil)

	check("an unknown scope never owns the sky",
		EventCore.dominant({ event({ Scope = "EVERYWHERE" }) }) == nil)

	check("every scope the code accepts is one of the three",
		EventCore.isValidScope("GLOBAL") and EventCore.isValidScope("SERVER")
			and EventCore.isValidScope("BIOME") and not EventCore.isValidScope("WORLD")
			and not EventCore.isValidScope(nil))

	-- The snapshot is the only thing a client ever sees. A field missing
	-- from it may as well not exist on the server.
	check("the snapshot carries scope, world and priority", (function()
		local state = EventCore.newState()
		EventCore.startEvent(state, event({
			Scope = "BIOME", WorldId = "EMBERFALL", Priority = 3, EndsAt = 9999,
		}))
		local snap = EventCore.snapshot(state, 1000, GameConfig)
		local first = snap.ActiveEvents[1]
		return first.Scope == "BIOME" and first.WorldId == "EMBERFALL" and first.Priority == 3
	end)())
end

-- === the live palette ===============================================
do
	group("The live menu palette")

	local ok, errors = Schema.validatePalettes(Palettes, Menu)
	check("the shipped palettes validate", ok, table.concat(errors, "; "))

	local base = ThemeCore.base()

	check("the base palette is UITheme, untouched", (function()
		for _, token in ThemeCore.TINTABLE do
			if base[token] ~= UITheme[token] then
				return false
			end
		end
		return true
	end)())

	-- Every district, every event, and every combination of the two. This is
	-- the whole point of the resolver being pure: "what does the menu look
	-- like in the Archive during a Catalyst Star" is an assertion rather than
	-- a thing somebody has to stand in.
	local function everyContext()
		local contexts = { { DistrictId = nil, Event = nil } }
		for _, district in Palettes.Districts do
			table.insert(contexts, { DistrictId = district.Id, Event = nil })
			for _, e in Palettes.Events do
				table.insert(contexts, { DistrictId = district.Id, Event = { Kind = e.Kind } })
			end
		end
		for _, e in Palettes.Events do
			table.insert(contexts, { DistrictId = nil, Event = { Kind = e.Kind } })
		end
		return contexts
	end

	local contexts = everyContext()
	check("there is more than one palette to check", #contexts > 10,
		string.format("%d contexts", #contexts))

	-- RULE 1: only surfaces tint. Gold means "press this", teal means
	-- "designed, not built", and the seven rarity colours are a contract.
	-- The Archive's authored accent IS that teal and the Hall's IS that gold,
	-- so this is a live collision, not a hypothetical one.
	check("no palette moves a colour that carries a meaning", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			for _, token in { "AccentGold", "AccentCool", "AccentWarn",
				"TextPrimary", "TextSecondary", "TextMuted" } do
				if palette[token] ~= nil then
					return false -- a semantic token must not even appear
				end
			end
			for key in Constants.RARITY do
				if palette[key] ~= nil then
					return false
				end
			end
		end
		return true
	end)())

	check("the tintable list is exactly the surfaces", (function()
		local expected = { PanelColor = true, RailColor = true, RaisedColor = true,
			ScrimColor = true, StrokeColor = true }
		local count = 0
		for _, token in ThemeCore.TINTABLE do
			if not expected[token] then
				return false
			end
			count += 1
		end
		return count == 5
	end)())

	-- RULE 2: text stays readable. This is the test that matters most: a
	-- Catalyst Star tint that looks magnificent on a panel is also the thing
	-- that makes the Settings labels vanish, and nobody finds that by eye
	-- until a player cannot turn the music down.
	check("every palette keeps the faintest text readable", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			for _, token in { "PanelColor", "RailColor", "RaisedColor", "ScrimColor" } do
				local ratio = ThemeCore.contrast(UITheme.TextMuted, palette[token])
				if ratio < ThemeCore.CONTRAST_FLOOR then
					return false
				end
			end
		end
		return true
	end)())

	-- THE BASE THEME ITSELF MUST CLEAR THE FLOOR. This is what the contrast
	-- test found first: TextMuted shipped at 3.40:1 against a raised row,
	-- below AA, before any tint existed. Pinned here so it cannot drift back.
	check("the untinted theme is readable on every surface", (function()
		for _, text in { UITheme.TextMuted, UITheme.TextSecondary, UITheme.TextPrimary } do
			for _, surface in { UITheme.PanelColor, UITheme.RailColor, UITheme.RaisedColor } do
				if ThemeCore.contrast(text, surface) < ThemeCore.CONTRAST_FLOOR then
					return false
				end
			end
		end
		return true
	end)())

	-- Clearing the floor is not the same as not making things worse. A tint
	-- is allowed to cost a little readability; it is not allowed to eat the
	-- headroom the base design has.
	check("no tint costs more than a sixth of the base's readability", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			for _, token in { "PanelColor", "RailColor", "RaisedColor" } do
				local before = ThemeCore.contrast(UITheme.TextMuted, UITheme[token])
				local after = ThemeCore.contrast(UITheme.TextMuted, palette[token])
				if after < before * 0.84 then
					return false
				end
			end
		end
		return true
	end)())

	-- The contrast maths itself, against values with known answers, because a
	-- floor enforced by a broken ruler is worse than no floor.
	check("black on white is the maximum ratio",
		math.abs(ThemeCore.contrast(Color3.new(0, 0, 0), Color3.new(1, 1, 1)) - 21) < 0.01)
	check("a colour against itself is 1:1",
		math.abs(ThemeCore.contrast(UITheme.AccentGold, UITheme.AccentGold) - 1) < 1e-6)
	check("luminance is weighted, not averaged", (function()
		-- Green reads far brighter than blue at the same channel value. An
		-- averaging implementation would call these equal and pass palettes
		-- a player cannot read.
		local green = ThemeCore.luminance(Color3.new(0, 1, 0))
		local blue = ThemeCore.luminance(Color3.new(0, 0, 1))
		return green > blue * 5
	end)())

	-- A deliberately absurd palette: the clamp must save it rather than the
	-- author having to notice.
	check("an unreadable tint is clamped, not shipped", (function()
		local awful = {
			Districts = { { Id = "HALL_OF_LEGENDS", Tint = UITheme.TextMuted, Strength = 1 } },
			Events = {},
		}
		local palette = ThemeCore.resolve(awful, { DistrictId = "HALL_OF_LEGENDS" })
		return ThemeCore.contrast(UITheme.TextMuted, palette.PanelColor) >= ThemeCore.CONTRAST_FLOOR
	end)())

	-- RULE 3: the resolver is total. Anything can be asked of it.
	check("an unknown district resolves to the base palette", (function()
		local palette = ThemeCore.resolve(Palettes, { DistrictId = "ATLANTIS" })
		return palette.PanelColor == UITheme.PanelColor
	end)())
	check("an unknown event kind does not tint", (function()
		local palette = ThemeCore.resolve(Palettes, { Event = { Kind = "SOMETHING_NEW" } })
		return palette.PanelColor == UITheme.PanelColor
	end)())
	check("no context at all resolves to the base palette",
		ThemeCore.resolve(Palettes, {}).PanelColor == UITheme.PanelColor)

	check("the Fate Engine is deliberately untinted", (function()
		-- The centre is where the game's own colour comes from -- the rarity
		-- on the portal -- and a tint there would compete with it.
		local palette = ThemeCore.resolve(Palettes, { DistrictId = "FATE_ENGINE" })
		return palette.PanelColor == UITheme.PanelColor
	end)())

	check("standing in a district actually changes something", (function()
		local palette = ThemeCore.resolve(Palettes, { DistrictId = "DISCOVERY_ARCHIVE" })
		return palette.PanelColor ~= UITheme.PanelColor
	end)())

	check("an event beats standing still", (function()
		local plain = ThemeCore.resolve(Palettes, { DistrictId = "DISCOVERY_ARCHIVE" })
		local starfall = ThemeCore.resolve(Palettes,
			{ DistrictId = "DISCOVERY_ARCHIVE", Event = { Kind = "FATEBREAK" } })
		return plain.PanelColor ~= starfall.PanelColor and starfall.EventKind == "FATEBREAK"
	end)())

	-- Bounded drift: a tint may lean the menu, never redesign it. Without a
	-- ceiling, "subtle district colour" becomes a full reskin one content
	-- edit at a time.
	--
	-- The stroke has its own, looser ceiling. It is the part that is MEANT to
	-- speak -- a 1px edge going orange during a Starfall is the effect, not a
	-- defect -- and it is exempt from the contrast rule for the same reason:
	-- nothing is read against it. Surfaces lean; the edge speaks.
	local function drift(a, b)
		return math.sqrt((a.R - b.R) ^ 2 + (a.G - b.G) ^ 2 + (a.B - b.B) ^ 2)
	end

	check("no surface wanders far from the base", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			for _, token in ThemeCore.TINTABLE do
				if token ~= "StrokeColor" and drift(palette[token], UITheme[token]) > 0.35 then
					return false
				end
			end
		end
		return true
	end)())

	check("...and the stroke, while louder, is still bounded", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			if drift(palette.StrokeColor, UITheme.StrokeColor) > 0.6 then
				return false
			end
		end
		return true
	end)())

	-- THE INVARIANT THE WHOLE APPROACH RESTS ON. A surface takes the hue and
	-- keeps its own brightness, which is why contrast survives a tint at all.
	-- If this ever stops holding, every readability test above starts passing
	-- for the wrong reason.
	check("a tint changes a surface's colour but not its brightness", (function()
		for _, context in contexts do
			local palette = ThemeCore.resolve(Palettes, context)
			for _, token in { "PanelColor", "RailColor", "RaisedColor", "ScrimColor" } do
				local before = ThemeCore.luminance(UITheme[token])
				local after = ThemeCore.luminance(palette[token])
				if math.abs(after - before) > 0.005 then
					return false
				end
			end
		end
		return true
	end)())

	check("...and it really does change the colour", (function()
		-- Guarding the test above from passing trivially: a tint that did
		-- nothing at all would also preserve luminance perfectly.
		local palette = ThemeCore.resolve(Palettes,
			{ DistrictId = "DISCOVERY_ARCHIVE", Event = { Kind = "CATALYST_STAR" } })
		return drift(palette.PanelColor, UITheme.PanelColor) > 0.01
	end)())

	check("resolving twice gives the same answer", (function()
		local a = ThemeCore.resolve(Palettes, { DistrictId = "EXPEDITION_GATE" })
		local b = ThemeCore.resolve(Palettes, { DistrictId = "EXPEDITION_GATE" })
		return a.PanelColor == b.PanelColor and a.RailColor == b.RailColor
	end)())

	check("resolving does not mutate UITheme", (function()
		ThemeCore.resolve(Palettes, { DistrictId = "TRAINING_GROUNDS", Event = { Kind = "CATALYST_STAR" } })
		return UITheme.PanelColor == Color3.fromRGB(24, 19, 40)
	end)())

	-- === where am I standing ========================================
	local radius = GameConfig.HubMenu.DistrictTintRadius

	check("standing on a district's anchor is standing in it", (function()
		for _, destination in Menu.Destinations do
			if ThemeCore.districtAt(destination.Anchor, Menu, radius) ~= destination.Id then
				return false
			end
		end
		return true
	end)())

	check("height does not change which district you are in", (function()
		local hall = HubMenuCore.destinationById(Menu, "HALL_OF_LEGENDS")
		local aloft = hall.Anchor + Vector3.new(0, 90, 0)
		return ThemeCore.districtAt(aloft, Menu, radius) == "HALL_OF_LEGENDS"
	end)())

	check("the open plaza belongs to no district", (function()
		-- Halfway between the Engine and the Hall, on the diagonal: outside
		-- every district's reach.
		local point = Vector3.new(280, 0, -280)
		return ThemeCore.districtAt(point, Menu, radius) == nil
	end)())

	-- The radius must not be so wide that two districts overlap, or the menu
	-- would flicker between them on the boundary.
	check("no two districts overlap at the tint radius", (function()
		local anchors = {}
		for _, destination in Menu.Destinations do
			table.insert(anchors, destination.Anchor)
		end
		for i = 1, #anchors do
			for j = i + 1, #anchors do
				local dx = anchors[i].X - anchors[j].X
				local dz = anchors[i].Z - anchors[j].Z
				if math.sqrt(dx * dx + dz * dz) < radius then
					return false
				end
			end
		end
		return true
	end)())

	check("the tint radius covers the widest platform", (function()
		-- A player standing on the far edge of the biggest deck must still be
		-- in that district. Derived from the deck rather than from a literal,
		-- so it survives a world rescale -- which is exactly what caught it.
		local widest = 0
		for _, district in Crossroads.Districts do
			widest = math.max(widest, district.PlatformSize.X, district.PlatformSize.Z)
		end
		return radius > widest / 2
	end)())
end


-- === events as content ==============================================
do
	group("Events, authored as data")

	local ok, errors = Schema.validateEvents(Events, Worlds)
	check("the shipped events validate", ok, table.concat(errors, "; "))

	check("every tier has a worked example", (function()
		local seen = {}
		for _, event in Events do
			seen[event.Tier] = true
		end
		-- MODIFIER has no example yet and that is honest: nothing mechanical
		-- exists for one to modify until combat does.
		return seen.AMBIENT and seen.WORLD
	end)())

	-- THE RULE THAT PREVENTS AN AURORA FROM LEAVING THE FOG GREEN FOREVER.
	-- An event may only write lighting properties that something restores,
	-- and the list it is checked against is the same list the client
	-- snapshots. Three places agree about one list, by construction.
	check("no event writes a lighting property nobody restores", (function()
		for _, event in Events do
			for field in event.Lighting or {} do
				if EventCore.LIGHTING_PROPERTIES[field] == nil then
					return false
				end
			end
		end
		return true
	end)())

	check("the restore list and the content vocabulary are the same set", (function()
		local tracked = EventCore.trackedLighting()
		local count = 0
		for _ in EventCore.LIGHTING_PROPERTIES do
			count += 1
		end
		return #tracked == count
	end)())

	local function definition(overrides)
		local e = {
			Id = "TEST",
			Name = "Test",
			Kind = "TEST",
			Tier = "WORLD",
			Scope = "SERVER",
			Priority = 1,
			DurationSeconds = 60,
			Announcement = { Text = "{player} did a thing.", Rarity = "RARE" },
		}
		for k, v in overrides or {} do e[k] = v end
		return { TEST = e }
	end

	local function rejects(overrides)
		local passed = Schema.validateEvents(definition(overrides), Worlds)
		return not passed
	end

	check("a valid definition passes", (function()
		return (Schema.validateEvents(definition(), Worlds))
	end)())

	-- === the tier rules (docs/EVENTS.md §4.0) ===
	check("an AMBIENT event may not grant a unique",
		rejects({ Tier = "AMBIENT", Unique = { LedgerId = "X", Cap = 1 } }))
	check("an AMBIENT event may not open a rift",
		rejects({ Tier = "AMBIENT", Rift = { Enabled = true } }))
	check("a MODIFIER event may not open a rift either",
		rejects({ Tier = "MODIFIER", Rift = { Enabled = true } }))
	check("a WORLD event may do both", (function()
		return (Schema.validateEvents(
			definition({ Unique = { LedgerId = "X", Cap = 10 }, Rift = { Enabled = true } }),
			Worlds
		))
	end)())
	check("an unknown tier is refused", rejects({ Tier = "LOUD" }))

	-- === scope ===
	check("an unknown scope is refused", rejects({ Scope = "EVERYWHERE" }))
	check("a BIOME event must name a real world",
		rejects({ Scope = "BIOME", WorldId = "NOWHERE" }))
	check("a BIOME event naming a real world is fine", (function()
		return (Schema.validateEvents(
			definition({ Scope = "BIOME", WorldId = "EMBERFALL" }), Worlds))
	end)())
	check("only a BIOME event may name a world",
		rejects({ Scope = "GLOBAL", WorldId = "EMBERFALL" }))

	-- === announcements ===
	-- A placeholder nobody substitutes reaches the player as raw braces,
	-- which is exactly the sort of thing that ships.
	check("an unknown placeholder is refused",
		rejects({ Announcement = { Text = "{wizard} appears.", Rarity = "RARE" } }))
	check("the three known placeholders are allowed", (function()
		return (Schema.validateEvents(definition({
			Announcement = { Text = "{player} found {event}. {remaining} left.", Rarity = "RARE" },
		}), Worlds))
	end)())
	check("an unknown rarity is refused",
		rejects({ Announcement = { Text = "hi", Rarity = "SUPREME" } }))

	check("a lighting property outside the restore list is refused",
		rejects({ Lighting = { Ambient = Color3.fromRGB(1, 1, 1), GlobalShadows = true } }))
	check("a zero-length event is refused", rejects({ DurationSeconds = 0 }))

	-- Substitution itself, since the validator only checks the template.
	check("announcement placeholders are filled", (function()
		local text = EventCore.formatAnnouncement("{player} found {event}. {remaining} remain.", {
			Player = "Ada", Event = "Catalyst Star", Remaining = 9,
		})
		return text == "Ada found Catalyst Star. 9 remain."
	end)())

	check("a missing value does not leave braces on screen", (function()
		local text = EventCore.formatAnnouncement("{player} rolled.", {})
		return text == "Someone rolled."
	end)())

	-- The Catalyst Star's own shape, since it is the one the whole ledger
	-- exists for.
	check("the Catalyst Star is capped at ten, forever",
		Events.CATALYST_STAR.Unique.Cap == 10)
	check("...and it is open to everyone once it fires",
		Events.CATALYST_STAR.OpenToEveryone == true)
	check("...and it outranks the Fatebreak sky",
		Events.CATALYST_STAR.Priority > Events.STARFALL.Priority)
end

-- === the scarcity ledger ============================================
do
	group("Global scarcity: only ten will ever exist")

	local claimant = { UserId = 7, Name = "Ada" }

	check("an empty ledger grants number one", (function()
		local result = LedgerCore.claim(nil, 10, claimant, 1000)
		return result.ok and result.value.Claim.Number == 1
	end)())

	check("claims number sequentially", (function()
		local ledger: any = nil
		for expected = 1, 5 do
			local result = LedgerCore.claim(ledger, 10, claimant, 1000 + expected)
			if not result.ok or result.value.Claim.Number ~= expected then
				return false
			end
			ledger = result.value.Ledger
		end
		return true
	end)())

	-- THE WHOLE POINT. When the last one is gone it is gone, on every server,
	-- forever.
	check("the cap is absolute", (function()
		local ledger: any = nil
		for i = 1, 10 do
			ledger = LedgerCore.claim(ledger, 10, claimant, 1000 + i).value.Ledger
		end
		local eleventh = LedgerCore.claim(ledger, 10, claimant, 2000)
		return not eleventh.ok and eleventh.err == "EXHAUSTED"
	end)())

	-- UpdateAsync may call the transform more than once for a single claim,
	-- against a newer value each time. The answer has to be right every time,
	-- which means reading only the ledger it was handed.
	check("the transform is pure -- it never mutates what it was given", (function()
		local ledger = { Claims = { { Number = 1, UserId = 1, Name = "A", At = 0 } } }
		LedgerCore.claim(ledger, 10, claimant, 1000)
		return #ledger.Claims == 1
	end)())

	check("re-running the transform on the same input gives the same answer", (function()
		local ledger = { Claims = { { Number = 1, UserId = 1, Name = "A", At = 0 } } }
		local first = LedgerCore.claim(ledger, 10, claimant, 1000)
		local second = LedgerCore.claim(ledger, 10, claimant, 1000)
		return first.value.Claim.Number == second.value.Claim.Number
	end)())

	-- A malformed ledger must never LOSE claims: dropping one silently
	-- re-issues a unique item that already exists in the world.
	check("a ledger with claims keeps every one of them", (function()
		local messy = { Claims = {
			{ Number = 3, UserId = 3, Name = "C", At = 3 },
			{ Number = 1, UserId = 1, Name = "A", At = 1 },
			{ Number = 2, UserId = 2, Name = "B", At = 2 },
		} }
		local sane = LedgerCore.sanitise(messy)
		return #sane.Claims == 3 and sane.Claims[1].Number == 1 and sane.Claims[3].Number == 3
	end)())

	check("an unreadable ledger reads as empty rather than as corrupt", (function()
		return LedgerCore.issued(LedgerCore.sanitise("nonsense")) == 0
			and LedgerCore.issued(LedgerCore.sanitise(nil)) == 0
	end)())

	check("a claim missing its number is dropped, not trusted", (function()
		local ledger = LedgerCore.sanitise({ Claims = { { UserId = 1 }, { Number = 1, UserId = 2 } } })
		return #ledger.Claims == 1
	end)())

	check("a nonsense cap is refused rather than guessed", (function()
		return not LedgerCore.claim(nil, 0, claimant, 1000).ok
			and not LedgerCore.claim(nil, -5, claimant, 1000).ok
	end)())

	check("a claimant without a user id is refused",
		not LedgerCore.claim(nil, 10, { Name = "Nobody" }, 1000).ok)

	check("the claim records who and when", (function()
		local result = LedgerCore.claim(nil, 10, claimant, 1700000000)
		local claim = result.value.Claim
		return claim.UserId == 7 and claim.Name == "Ada" and claim.At == 1700000000
	end)())

	-- Scarcity nobody can see is a rumour. This is what the Hall displays.
	check("the public summary counts what is left", (function()
		local ledger: any = nil
		for i = 1, 3 do
			ledger = LedgerCore.claim(ledger, 10, claimant, 1000 + i).value.Ledger
		end
		local summary = LedgerCore.summary(ledger, 10)
		return summary.Issued == 3 and summary.Remaining == 7 and #summary.Claims == 3
	end)())

	check("remaining never goes negative", (function()
		local ledger = { Claims = {} }
		for i = 1, 12 do
			table.insert(ledger.Claims, { Number = i, UserId = i, Name = "x", At = i })
		end
		return LedgerCore.remaining(ledger, 10) == 0
	end)())
end

-- === summary ========================================================
print(string.format("\n%s\n%d passed, %d failed, %d total", string.rep("=", 60),
	passed, failed, passed + failed))

if failed > 0 then
	print("\nFAILURES:")
	for _, f in failures do print("  - " .. f) end
	error(string.format("%d test(s) failed", failed), 0)
end
