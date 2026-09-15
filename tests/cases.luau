-- LUCKBOUND test suite. Run: python3 tests/build_suite.py && luau tests/generated_suite.luau

local Constants = __require("Constants")
local GameConfig = __require("GameConfig")
local FateCore = __require("FateCore")
local ProgressionCore = __require("ProgressionCore")
local ProfileSchema = __require("ProfileSchema")
local EventCore = __require("EventCore")
local WeightedRandom = __require("WeightedRandom")
local Schema = __require("Schema")
local Worlds = __require("Worlds")
local Crossroads = __require("Crossroads")
local UITheme = __require("UITheme")

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

	for _, id in { "VERDANT_VALLEY", "EMBERFALL", "SKY_CITADEL", "ASTRAL_REACH" } do
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
	check("phase gating excludes Phase 3 content", #FateCore.buildPool(Worlds, 1) == 4,
		string.format("%d worlds enabled at phase 1", #FateCore.buildPool(Worlds, 1)))
	check("THE_UNKNOWN enters the pool at phase 3", #FateCore.buildPool(Worlds, 3) == 5)

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

	local partial = { SchemaVersion = 1, FatePoints = 500 }
	local filled, applied = ProfileSchema.migrate(partial, now)
	check("missing fields are backfilled", filled.RollHistory ~= nil and filled.Stats ~= nil)
	check("backfill preserves existing values", filled.FatePoints == 500)
	check("no migrations run for a current-version profile", applied == 0)

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

	check("all five Master Spec districts are present", #Crossroads.Districts == 5,
		string.format("got %d", #Crossroads.Districts))

	local byId = {}
	for _, d in Crossroads.Districts do byId[d.Id] = d end
	for _, id in { "HALL_OF_LEGENDS", "DISCOVERY_ARCHIVE", "EXPEDITION_GATE",
		"TRAINING_GROUNDS", "GLOBAL_OBSERVATORY" } do
		check(string.format("district %s exists", id), byId[id] ~= nil)
	end

	-- Master Spec §3 / Blueprint §2.1 compass placement. Roblox is Y-up, so
	-- the compass is the X/Z plane: NORTH = -Z, EAST = +X, SOUTH = +Z, WEST = -X.
	local anchors = GameConfig.HubLayout.Anchors
	check("Hall of Legends is north (-Z)", anchors.HALL_OF_LEGENDS.Z < 0)
	check("Discovery Archive is east (+X)", anchors.DISCOVERY_ARCHIVE.X > 0)
	check("Expedition Gate is south (+Z)", anchors.EXPEDITION_GATE.Z > 0)
	check("Training Grounds is west (-X)", anchors.TRAINING_GROUNDS.X < 0)
	check("Global Observatory is the upper platform (+40Y)",
		anchors.GLOBAL_OBSERVATORY.Y == 40, tostring(anchors.GLOBAL_OBSERVATORY.Y))
	check("Fate Engine is at true centre",
		anchors.FATE_ENGINE.X == 0 and anchors.FATE_ENGINE.Y == 0 and anchors.FATE_ENGINE.Z == 0)

	-- Blueprint §7.3: positions are locked in one place, never re-derived.
	local everyZoneAnchored = true
	for _, d in Crossroads.Districts do
		if anchors[d.Id] == nil then everyZoneAnchored = false end
	end
	check("every zone has a named anchor in GameConfig.HubLayout", everyZoneAnchored)

	-- Blueprint §2.2 dimensions.
	check("Fate Engine platform is 24 stud radius, raised 3",
		Crossroads.FateEngine.PlatformRadius == 24 and Crossroads.FateEngine.PlatformRaise == 3)
	check("Fate Engine has 6 crystal shards",
		Crossroads.FateEngine.CrystalShards.Count == 6)
	check("Hall of Legends has 5 obelisk slots at 8 studs",
		byId.HALL_OF_LEGENDS.ObeliskSlots == 5 and byId.HALL_OF_LEGENDS.ObeliskHeight == 8)
	check("Discovery Archive interior is 20 stud diameter",
		byId.DISCOVERY_ARCHIVE.InteriorDiameter == 20)
	check("Training Grounds yard is 30x30",
		byId.TRAINING_GROUNDS.PlatformSize.X == 30 and byId.TRAINING_GROUNDS.PlatformSize.Z == 30)
	check("Training Grounds has 3 dummies plus a boss dummy",
		byId.TRAINING_GROUNDS.DummyCount == 3 and byId.TRAINING_GROUNDS.HasBossDummy)
	check("Observatory platform is 18 stud radius",
		byId.GLOBAL_OBSERVATORY.PlatformRadius == 18)
	check("hub is 120 studs across", Crossroads.Plaza.Diameter == 120)
	check("walkways are 8 studs wide, raised 2",
		Crossroads.Bridges.Width == 8 and Crossroads.Bridges.Raise == 2)
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
	check("spawn is offset from the Fate Engine, not on top of it",
		Crossroads.SpawnOffset.Z ~= 0 or Crossroads.SpawnOffset.X ~= 0)

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
	check("point light is range 24, brightness 3",
		portal.LightRange == 24 and portal.ActiveBrightness == 3)
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

	check("Fate Engine uses the rig at 1.5x", portal.FateEngineScale == 1.5)
	check("Expedition Gate uses the rig at 2x", portal.ExpeditionGateScale == 2.0)
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

	check("UITheme derives rarity colours from Constants, not its own table",
		UITheme.RarityColors.MYTHIC == Constants.RARITY.MYTHIC.Color)
	check("UITheme is frozen",
		(throws(function() UITheme.AccentGold = nil end)))
end

-- === 10. Biome lighting =============================================
group("Biome lighting (blueprint §3.3 / §4.3 / §5.3)")

do
	local vv, ef, ar = Worlds.VERDANT_VALLEY, Worlds.EMBERFALL, Worlds.ASTRAL_REACH

	for _, w in { vv, ef, ar } do
		check(string.format("%s declares Brightness and FogStart", w.Id),
			type(w.Environment.Brightness) == "number"
				and type(w.Environment.FogStart) == "number")
	end

	check("Verdant Valley is the brightest world", vv.Environment.Brightness == 2.5)
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

-- === summary ========================================================
print(string.format("\n%s\n%d passed, %d failed, %d total", string.rep("=", 60),
	passed, failed, passed + failed))

if failed > 0 then
	print("\nFAILURES:")
	for _, f in failures do print("  - " .. f) end
	error(string.format("%d test(s) failed", failed), 0)
end
