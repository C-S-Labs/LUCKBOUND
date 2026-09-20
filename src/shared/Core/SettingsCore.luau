--!strict
-- PLAYER SETTINGS: the schema, the defaults, and the validator.
--
-- Settings are stored on the profile and therefore arrive from a DataStore,
-- which makes them exactly as untrusted as anything a client sends: a stored
-- value can be from an older build, a hand-edited test profile, or a client
-- that sent nonsense before this validator existed. So every read goes
-- through `sanitise`, and every write through `validate`.
--
-- Adding a setting is one row in SPEC. The settings panel draws itself from
-- that table -- it has no list of its own.

local Result = require(script.Parent.Result)

local SettingsCore = {}

-- Kinds: "number" clamps to Min/Max, "boolean" coerces nothing and rejects
-- anything that is not a boolean, "option" must be one of Options.
SettingsCore.SPEC = {
	{
		Id = "MusicVolume",
		Label = "Music",
		Kind = "number",
		Default = 0.6,
		Min = 0,
		Max = 1,
		Step = 0.05,
		Order = 1,
	},
	{
		Id = "SfxVolume",
		Label = "Effects",
		Kind = "number",
		Default = 0.8,
		Min = 0,
		Max = 1,
		Step = 0.05,
		Order = 2,
	},
	{
		Id = "UiScale",
		Label = "Interface size",
		Kind = "number",
		Default = 1,
		Min = 0.8,
		Max = 1.4,
		Step = 0.05,
		Order = 3,
	},
	{
		-- THE ACCESSIBILITY SWITCH, and it is not decoration. Everything the
		-- hub UI does is a tween, the hub itself breathes, and the roll builds
		-- for up to seven seconds. ReduceMotion shortens every UI tween to
		-- near zero and stops the loading camera's drift; it does NOT shorten
		-- the roll reveal, because that is the game rather than the chrome.
		Id = "ReduceMotion",
		Label = "Reduce motion",
		Kind = "boolean",
		Default = false,
		Order = 4,
	},
	{
		Id = "ScreenShake",
		Label = "Screen shake",
		Kind = "boolean",
		Default = true,
		Order = 5,
	},
	{
		-- Someone else's Mythic is a full-screen announcement. On a busy
		-- server that is either the best thing about the game or the worst,
		-- and which one it is turns out to be a matter of taste.
		Id = "ShowGlobalAnnouncements",
		Label = "Others' rolls",
		Kind = "boolean",
		Default = true,
		Order = 6,
	},
	{
		Id = "AutoHideMenu",
		Label = "Start with menu hidden",
		Kind = "boolean",
		Default = false,
		Order = 7,
	},
}

local function specById(id: string): any?
	for _, entry in SettingsCore.SPEC do
		if entry.Id == id then
			return entry
		end
	end
	return nil
end

SettingsCore.specById = specById

--- Settings in panel order.
function SettingsCore.ordered(): { any }
	local list = {}
	for _, entry in SettingsCore.SPEC do
		table.insert(list, entry)
	end
	table.sort(list, function(a, b)
		return a.Order < b.Order
	end)
	return list
end

function SettingsCore.defaults(): { [string]: any }
	local out = {}
	for _, entry in SettingsCore.SPEC do
		out[entry.Id] = entry.Default
	end
	return out
end

--- Validates one setting. Returns Result.ok(coercedValue) or an error.
function SettingsCore.validate(id: any, value: any): any
	if type(id) ~= "string" then
		return Result.err("setting id must be a string")
	end

	local entry = specById(id)
	if not entry then
		return Result.err(`unknown setting '{id}'`)
	end

	if entry.Kind == "boolean" then
		if type(value) ~= "boolean" then
			return Result.err(`setting '{id}' expects a boolean`)
		end
		return Result.ok(value)
	end

	if entry.Kind == "number" then
		if type(value) ~= "number" or value ~= value then
			-- value ~= value catches NaN, which clamps to itself and would
			-- otherwise be stored and then fed to a Tween.
			return Result.ok(entry.Default)
		end
		return Result.ok(math.clamp(value, entry.Min, entry.Max))
	end

	return Result.err(`setting '{id}' has an unhandled kind '{tostring(entry.Kind)}'`)
end

--- Takes anything at all and returns a complete, valid settings table.
--- Unknown keys are dropped, bad values fall back to their default, and
--- missing keys are filled in.
function SettingsCore.sanitise(stored: any): { [string]: any }
	local out = SettingsCore.defaults()
	if type(stored) ~= "table" then
		return out
	end
	for id, value in stored do
		local result = SettingsCore.validate(id, value)
		if result.ok then
			out[id] = result.value
		end
	end
	return out
end

return SettingsCore
