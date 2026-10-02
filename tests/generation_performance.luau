--!strict
-- Headless invariants/CPU measurement; never a substitute for Studio entry time.
local ChunkCore = __require("ChunkCore")
local Chunks = __require("Chunks")
local Worlds = __require("Worlds")
local GameConfig = __require("GameConfig")
local ExpeditionCore = __require("ExpeditionCore")
local GenerationProfile = __require("GenerationProfile")
local ChunkDefinitionCache = __require("ChunkDefinitionCache")

local function signature(layout: any): string
	local parts = {}
	for _, p in layout.Chunks do
		table.insert(
			parts,
			string.format("%s:%s:%g:%g:%g:%g:%g", p.ChunkId, p.Role, p.X, p.Y, p.Z, p.Yaw, p.Index)
		)
	end
	return table.concat(parts, ";")
end

local baseline = {}
local checked = 0
for _, stage in { "A", "B", "C", "D", "E", "F" } do
	ChunkDefinitionCache.clear()
	for _, worldId in GameConfig.GenerationBenchmark.Worlds do
		local world = Worlds[worldId]
		for seed = 1, 1000 do
			local profile = GenerationProfile.new(stage)
			local started = os.clock()
			local ok, layout, attempts = ChunkCore.assembleWithRetry(Chunks, {
				WorldId = worldId,
				PathLength = ExpeditionCore.pathLengthFor(world, GameConfig),
				IncludeSide = GameConfig.Expedition.IncludeSide,
				BranchLength = GameConfig.Expedition.BranchLength,
				MaxRepeats = GameConfig.Expedition.MaxRepeats,
				Generation = world.Generation,
				Profile = profile,
			}, function(attempt)
				return ExpeditionCore.streamFor(seed, attempt)
			end, GameConfig.Expedition.AssemblyAttempts)
			local elapsed = os.clock() - started
			local result = tostring(ok)
				.. ":"
				.. tostring(attempts)
				.. ":"
				.. (if ok then signature(layout) else tostring(layout))
			local key = worldId .. ":" .. seed
			if stage == "A" then
				baseline[key] = result
			else
				assert(baseline[key] == result, stage .. " changed " .. key)
			end
			if ok then
				local valid, errors = ChunkCore.validateLayout(layout, Chunks)
				assert(valid, table.concat(errors, ";"))
				assert(
					layout.Chunks[1].Role == "ENTRY"
						and layout.Chunks[1].X == 0
						and layout.Chunks[1].Z == 0,
					"spawn anchor moved"
				)
			end
			checked += 1
			print(
				string.format(
					"%s,%s,%d,%.9f,%s,%d,%d,%d",
					stage,
					worldId,
					seed,
					elapsed,
					tostring(ok),
					attempts,
					profile.Counters.CandidateAttempts or 0,
					profile.Counters.OverlapComparisons or 0
				)
			)
		end
	end
end
print(
	"PASS "
		.. checked
		.. " seeded layouts: matching placements/retries/failures and independent overlap validation"
)
