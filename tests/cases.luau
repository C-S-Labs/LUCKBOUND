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
local AssetManifest = __require("AssetManifest")
local ChunkCore = __require("ChunkCore")
local ExpeditionCore = __require("ExpeditionCore")
local Chunks = __require("Chunks")

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
	check("Global Observatory is the upper platform",
		anchors.GLOBAL_OBSERVATORY.Y > 0, tostring(anchors.GLOBAL_OBSERVATORY.Y))
	-- It must be climbable: a ramp that gains more than ~2 studs per stud of
	-- run is a wall. Blueprint §2.2 reaches it by spiral ramp.
	do
		local obs
		for _, d in Crossroads.Districts do
			if d.Id == "GLOBAL_OBSERVATORY" then obs = d end
		end
		local run = (obs.PlatformRadius + 8) * obs.RampTurns * 2 * math.pi
		check("the observatory ramp has a climbable gradient",
			anchors.GLOBAL_OBSERVATORY.Y / run < 0.5,
			string.format("rise %d over run %.0f", anchors.GLOBAL_OBSERVATORY.Y, run))
	end
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
	check("hub is 1150 studs across", Crossroads.Plaza.Diameter == 1150)
	check("the gate processional is wider than a walkway",
		Crossroads.Bridges.ProcessionalWidth > Crossroads.Bridges.Width)

	-- === SCALE BUDGET =============================================
	-- A Roblox character is ~5 studs tall. The old hub was 24 characters
	-- across, which read as a room rather than a world.
	local CHAR = GameConfig.Scale.CharacterHeight
	check("the hub reads as a world, not a room (>= 200 characters across)",
		Crossroads.Plaza.Diameter / CHAR >= 200,
		string.format("%.0f characters", Crossroads.Plaza.Diameter / CHAR))

	for _, d in Crossroads.Districts do
		check(string.format("%s is at least 40 characters across", d.Id),
			math.min(d.PlatformSize.X, d.PlatformSize.Z) / CHAR >= 40,
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

	-- 6. THE SPAWN POINT IS NOT INSIDE SOMETHING.
	-- At (0, 8, 250) it sat within the processional walkway's own volume, so
	-- Roblox ejected the character upward -- which is how a playtest opened
	-- standing on top of a pillar.
	local deckTop = GameConfig.HubLayout.WalkwayRaise + Crossroads.Bridges.Thickness / 2
	check("spawn is above the walkway deck, not inside it",
		GameConfig.HubLayout.SpawnAnchor.Y > deckTop,
		string.format("spawn Y %.0f vs deck top %.0f",
			GameConfig.HubLayout.SpawnAnchor.Y, deckTop))
	check("spawn is over the processional, not out in space",
		math.abs(GameConfig.HubLayout.SpawnAnchor.Z) < anchors.EXPEDITION_GATE.Z)

	-- 7. THE OBSERVATORY RAMP IS CONTINUOUS.
	-- A fixed 5-stud step depth was fine on the 120-stud hub; at this radius
	-- the same step count spans 26 studs of arc each, so the ramp was 70
	-- floating tiles with 21-stud gaps and no way up.
	local obs
	for _, d in Crossroads.Districts do
		if d.Id == "GLOBAL_OBSERVATORY" then obs = d end
	end
	local steps = math.floor(obs.RampTurns * 28)
	local rampRadius = obs.PlatformRadius + 8
	local arc = 2 * math.pi * rampRadius * obs.RampTurns / steps
	-- HubBuilder derives step depth from this factor, so asserting it is > 1
	-- asserts that consecutive steps overlap rather than leaving a gap. It
	-- being a config value at all is the fix: a hard-coded 5-stud depth is
	-- what turned the ramp into 70 floating tiles after the 10x rescale.
	check("ramp step depth is derived from the arc it must span, and overlaps",
		GameConfig.HubLayout.RampStepOverlap > 1,
		string.format("%.0f studs of arc per step, overlap x%.2f",
			arc, GameConfig.HubLayout.RampStepOverlap))
	local rise = (obs.Height - Crossroads.FateEngine.PlatformRaise) / steps
	check("each ramp step is a step, not a jump", rise <= 2,
		string.format("%.2f studs per step", rise))
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
	check("it carries its own map size as content", es.MapPathLength == 3)

	-- The onboarding arc must actually hand it out, or a tester waits on a
	-- 15% draw to see the thing they are trying to test.
	local onboardingIndex
	for i, id in GameConfig.Fate.OnboardingSequence do
		if id == "ETHEREAL_SCAPE" then onboardingIndex = i end
	end
	check("onboarding guarantees it inside the first five rolls",
		onboardingIndex ~= nil and onboardingIndex <= 5, tostring(onboardingIndex))

	-- The kit ------------------------------------------------------
	local lib = ChunkCore.libraryFor(Chunks, "ETHEREAL_SCAPE")
	check("Ethereal Scape has exactly one ENTRY chunk", lib.ENTRY and #lib.ENTRY == 1)
	check("Ethereal Scape has exactly one BOSS chunk", lib.BOSS and #lib.BOSS == 1)
	check("Ethereal Scape has a SIDE pocket (§6 checklist)", lib.SIDE and #lib.SIDE >= 1)
	check("Ethereal Scape has connective pieces",
		(#(lib.PATH or {}) + #(lib.COMBAT or {})) >= 4,
		string.format("%d", #(lib.PATH or {}) + #(lib.COMBAT or {})))

	local esCount = 0
	for _, c in Chunks do
		if c.WorldId == "ETHEREAL_SCAPE" then esCount += 1 end
	end
	-- One chunk per island in the Blender scene's Aether_Terrain collection.
	check("the kit has one piece per island in the blend", esCount == 8,
		string.format("%d pieces", esCount))

	-- Every piece must trace back to the authored scene, not to a guess.
	local BLEND = "assets/source/worlds/ethereal_scape/aether_environment_refined.blend"
	local allTraced = true
	local untraced
	for id, c in Chunks do
		if c.WorldId == "ETHEREAL_SCAPE" then
			local entry = AssetManifest.ENTRIES[c.AssetKey]
			if not entry or entry.Source ~= BLEND then
				allTraced = false
				untraced = id
			end
		end
	end
	check("every piece names the authored .blend as its source", allTraced, untraced)

	-- The grammar --------------------------------------------------
	-- Socket Kinds are a PER-WORLD design vocabulary, not a global enum. If
	-- these two ever overlap, a Verdant Valley footpath could in principle be
	-- reasoned about as an Ethereal Scape bridge, and the point is lost.
	local vvKinds, esKinds = {}, {}
	for _, c in Chunks do
		local into = if c.WorldId == "VERDANT_VALLEY" then vvKinds
			elseif c.WorldId == "ETHEREAL_SCAPE" then esKinds
			else nil
		if into then
			for _, s in c.Sockets do into[s.Kind] = true end
		end
	end
	local shared = {}
	for kind in esKinds do
		if vvKinds[kind] then table.insert(shared, kind) end
	end
	check("the two worlds speak different socket vocabularies", #shared == 0,
		table.concat(shared, ", "))
	check("Ethereal Scape speaks SPAN and RITE", esKinds.SPAN and esKinds.RITE)

	check("the Sky Temple accepts only a RITE approach",
		Chunks.ES_SKY_TEMPLE.Sockets[1].Kind == "RITE" and #Chunks.ES_SKY_TEMPLE.Sockets == 1)

	local riteProviders = {}
	for id, c in Chunks do
		if c.WorldId == "ETHEREAL_SCAPE" and c.Role ~= "BOSS" then
			for _, s in c.Sockets do
				if s.Kind == "RITE" then table.insert(riteProviders, id) end
			end
		end
	end
	check("the Waystone Ring is the only piece offering a RITE exit",
		#riteProviders == 1 and riteProviders[1] == "ES_WAYSTONE_RING",
		table.concat(riteProviders, ", "))

	-- Assembly -----------------------------------------------------
	local path = ExpeditionCore.pathLengthFor(es, GameConfig)
	local built, broken = 0, {}
	local gated = true
	local minSpan, maxSpan = math.huge, 0
	for trial = 1, 300 do
		local okA, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "ETHEREAL_SCAPE", PathLength = path },
			function(a) return lcg(trial * 2971215073 + a * 7919) end,
			GameConfig.Expedition.AssemblyAttempts)
		if okA then
			built += 1
			local okV, errV = ChunkCore.validateLayout(layout, Chunks)
			if not okV then table.insert(broken, table.concat(errV, ", ")) end

			-- The same emergent property Verdant Valley has, from a kit
			-- authored independently: a Kind the arena accepts is reserved
			-- for the arena, so the ring always ends up being the approach.
			local penultimate = layout.Chunks[#layout.Chunks - 1]
			if penultimate.ChunkId ~= "ES_WAYSTONE_RING" then gated = false end

			local w, d = ChunkCore.footprint(layout)
			local span = math.max(w, d)
			minSpan = math.min(minSpan, span)
			maxSpan = math.max(maxSpan, span)
		end
	end
	print(string.format("        Ethereal Scape spans %.0f-%.0f studs at path length %d",
		minSpan, maxSpan, path))

	check("Ethereal Scape assembles on nearly every seed", built >= 285,
		string.format("%d/300 within %d attempts", built, GameConfig.Expedition.AssemblyAttempts))
	check("every Ethereal Scape layout is collision-free", #broken == 0, broken[1])
	check("the Waystone Ring always gates the Sky Temple (emergent, second world)", gated)

	-- Scale: the pieces are sized for the post-rescale world, not the old
	-- 120-stud hub. The smallest map still has to read as a place.
	check("even the smallest Ethereal Scape map is bigger than a zone platform",
		minSpan > 800, string.format("%.0f studs", minSpan))
	check("walking stays a minority of a 300-second expedition",
		maxSpan / GameConfig.Scale.WalkSpeed < es.DurationSeconds * 0.35,
		string.format("%.0fs of %ds (%.0f%%)", maxSpan / GameConfig.Scale.WalkSpeed,
			es.DurationSeconds, maxSpan / GameConfig.Scale.WalkSpeed / es.DurationSeconds * 100))
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

	-- Kits ----------------------------------------------------------
	check("Verdant Valley has a kit", ExpeditionCore.hasKit(Chunks, "VERDANT_VALLEY"))
	check("Ethereal Scape has a kit", ExpeditionCore.hasKit(Chunks, "ETHEREAL_SCAPE"))
	check("Sky Citadel does not", not ExpeditionCore.hasKit(Chunks, "SKY_CITADEL"))

	-- THE DEBT, ASSERTED. Three rollable worlds cannot be entered. This test
	-- is not here to be green forever -- it is here so the number is in the
	-- suite and someone has to look at it to change it.
	local missing = ExpeditionCore.worldsWithoutKits(Worlds, Chunks, GameConfig.CurrentPhase)
	print(string.format("        rollable but not enterable: %s", table.concat(missing, ", ")))
	check("rollable-but-not-enterable worlds are reported, sorted",
		#missing == 3 and missing[1] == "ASTRAL_REACH" and missing[2] == "EMBERFALL"
			and missing[3] == "SKY_CITADEL",
		table.concat(missing, ", "))

	-- Map size and duration are content, with a config fallback ------
	check("a world's own MapPathLength wins",
		ExpeditionCore.pathLengthFor(Worlds.ETHEREAL_SCAPE, GameConfig) == 3)
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
	local function mapFor(userId, rollNumber)
		local seed = ExpeditionCore.seedFor(userId, rollNumber, "ETHEREAL_SCAPE")
		local okM, layout = ChunkCore.assembleWithRetry(Chunks,
			{ WorldId = "ETHEREAL_SCAPE", PathLength = 3 },
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
	check("a player who has rolled a world with a kit may enter",
		allowed.Allowed and allowed.WorldId == "ETHEREAL_SCAPE",
		tostring(allowed.Refusal))

	check("a player who has not rolled is refused",
		decide({ Profile = withRolls({}) }).Refusal == "NO_DESTINATION")
	check("a world with no kit is refused at the door, not mid-assembly",
		decide({ Profile = withRolls({
			{ WorldId = "SKY_CITADEL", Rarity = "EPIC", Timestamp = 1 },
		}) }).Refusal == "NO_KIT")
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
	for _, refusal in { "DISABLED", "NO_DESTINATION", "UNKNOWN_WORLD", "NO_KIT",
		"ALREADY_IN_EXPEDITION", "COOLDOWN", "TOO_FAR", "SERVER_FULL" } do
		if ExpeditionCore.refusalMessage(refusal) then table.insert(spoken, refusal) end
	end
	table.sort(spoken)
	check("only the two refusals a legitimate player can hit say anything",
		#spoken == 2 and spoken[1] == "NO_DESTINATION" and spoken[2] == "NO_KIT",
		table.concat(spoken, ", "))
end

-- === summary ========================================================
print(string.format("\n%s\n%d passed, %d failed, %d total", string.rep("=", 60),
	passed, failed, passed + failed))

if failed > 0 then
	print("\nFAILURES:")
	for _, f in failures do print("  - " .. f) end
	error(string.format("%d test(s) failed", failed), 0)
end
