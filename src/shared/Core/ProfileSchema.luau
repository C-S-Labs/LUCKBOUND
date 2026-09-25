--!strict
-- Default profile shape and migrations. Pure, so both SaveSystem and the
-- tests use the same code path. Build spec §2.4.
--
-- Migration rule: never rename or repurpose a field. Add a new one, bump
-- CURRENT_SCHEMA_VERSION, add an entry to MIGRATIONS. Migrations must be pure
-- and idempotent.

local Constants = require(script.Parent.Constants)
local SettingsCore = require(script.Parent.SettingsCore)

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
		-- Code id -> the timestamp it was redeemed at. A map rather than a
		-- list, because the only question ever asked of it is "has this one
		-- been used", and a list answers that in O(n) for no benefit.
		RedeemedCodes = {},
		-- Vault keys carried between expeditions (build spec §7.5): key Id ->
		-- how many, never more than GameConfig.Loot.MaxKeysPerKind. Kept
		-- apart from Inventory, which is still §7-excluded and unshaped.
		Keys = {},
		Settings = SettingsCore.defaults(),
		LastSeenAt = now,
		CreatedAt = now,
	}
end

-- MIGRATIONS[n] upgrades a profile from version n to version n+1.
ProfileSchema.MIGRATIONS = {
	-- v1 -> v2: the hub menu arrived, and with it two new fields. Both are
	-- additive; nothing is renamed or repurposed, per the rule at the top of
	-- this file. Sanitising the settings rather than assigning the defaults
	-- means a v1 profile that somehow already carried a Settings table keeps
	-- whatever of it is valid.
	[1] = function(profile: any): any
		profile.RedeemedCodes = profile.RedeemedCodes or {}
		profile.Settings = SettingsCore.sanitise(profile.Settings)
		return profile
	end,
	-- v2 -> v3: vault keys (build spec §7.5). Additive; a profile that somehow
	-- already had a Keys table keeps only its well-formed entries.
	[2] = function(profile: any): any
		local keys = {}
		if type(profile.Keys) == "table" then
			for id, n in profile.Keys do
				if type(id) == "string" and type(n) == "number" and n >= 1 then
					keys[id] = math.floor(n)
				end
			end
		end
		profile.Keys = keys
		return profile
	end,
} :: { [number]: (any) -> any }

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
