--!strict
-- Default profile shape and migrations. Pure, so both SaveSystem and the
-- tests use the same code path. Build spec §2.4.
--
-- Migration rule: never rename or repurpose a field. Add a new one, bump
-- CURRENT_SCHEMA_VERSION, add an entry to MIGRATIONS. Migrations must be pure
-- and idempotent.

local Constants = require(script.Parent.Constants)

local ProfileSchema = {}

ProfileSchema.CURRENT = Constants.CURRENT_SCHEMA_VERSION

function ProfileSchema.default(now: number): any
	return {
		SchemaVersion = ProfileSchema.CURRENT,
		FatePoints = 0,
		FateLevel = 1,
		TotalRolls = 0,
		RollHistory = {},
		Discoveries = {},
		Inventory = {},
		EquippedSlots = {},
		Stats = {
			ExpeditionsCompleted = 0,
			BossesDefeated = 0,
			DeepestRarity = "COMMON",
		},
		LastSeenAt = now,
		CreatedAt = now,
	}
end

-- MIGRATIONS[n] upgrades a profile from version n to version n+1.
ProfileSchema.MIGRATIONS = {} :: { [number]: (any) -> any }

--- Brings any stored profile up to the current schema version. Returns the
--- migrated profile and how many migrations ran.
function ProfileSchema.migrate(stored: any, now: number): (any, number)
	if type(stored) ~= "table" then
		return ProfileSchema.default(now), 0
	end

	local profile = stored
	local applied = 0
	local version = profile.SchemaVersion or 0

	while version < ProfileSchema.CURRENT do
		local step = ProfileSchema.MIGRATIONS[version]
		if not step then
			-- No path forward from this version. Refuse rather than silently
			-- serving a profile the systems will misread.
			error(
				`no migration from profile schema v{version} to v{version + 1}`
			)
		end
		profile = step(profile)
		version += 1
		profile.SchemaVersion = version
		applied += 1
	end

	-- Backfill any field added without a version bump during prototyping.
	local defaults = ProfileSchema.default(now)
	for key, value in defaults do
		if profile[key] == nil then
			profile[key] = value
		end
	end

	return profile, applied
end

--- Trims unbounded fields before a DataStore write. Build spec D-6.
function ProfileSchema.prune(profile: any, config: any): any
	local cap = config.Fate.RollHistoryCap
	local history = profile.RollHistory
	if #history > cap then
		local trimmed = {}
		for i = #history - cap + 1, #history do
			table.insert(trimmed, history[i])
		end
		profile.RollHistory = trimmed
	end
	return profile
end

return ProfileSchema
