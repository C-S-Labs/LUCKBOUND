--!strict
-- Explicit per-run experiment context; nil keeps production behavior.
local GenerationProfile = {}

function GenerationProfile.new(stage: string): any
	assert(string.find("ABCDEF", stage, 1, true) and #stage == 1, "invalid generation stage")
	return {
		Stage = stage,
		Started = os.clock(),
		Counters = {},
		Times = {},
	}
end

function GenerationProfile.count(profile: any?, name: string, amount: number?)
	if profile then
		profile.Counters[name] = (profile.Counters[name] or 0) + (amount or 1)
	end
end

function GenerationProfile.time(profile: any?, name: string, started: number)
	if profile then
		profile.Times[name] = (profile.Times[name] or 0) + os.clock() - started
	end
end

return GenerationProfile
