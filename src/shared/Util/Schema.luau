--!strict
-- Boot-time content validation. Build spec T-107.
-- The server must refuse to start on malformed content: a prototype that boots
-- with silently broken data is worse than one that does not boot.

local Constants = require(script.Parent.Parent.Core.Constants)

local Schema = {}

type FieldSpec = { kind: string, optional: boolean? }

local function field(kind: string, optional: boolean?): FieldSpec
	return { kind = kind, optional = optional }
end

local WORLD_SPEC: { [string]: FieldSpec } = {
	Id = field("string"),
	Name = field("string"),
	Rarity = field("rarity"),
	RollWeight = field("number"),
	EnabledInPhase = field("number"),
	Environment = field("table"),
	MusicId = field("string", true),
	Enemies = field("table"),
	BossId = field("string", true),
	LootTableId = field("string", true),
	DiscoveryTableId = field("string", true),
	Modifiers = field("table"),
	ModifierOverrides = field("table", true),
	DurationSeconds = field("number"),
	RecommendedPower = field("number"),
	Flavor = field("string"),
}

local function validateOne(
	definition: any,
	spec: { [string]: FieldSpec },
	label: string,
	errors: { string }
): ()
	if type(definition) ~= "table" then
		table.insert(errors, `{label}: expected a table, got {type(definition)}`)
		return
	end

	for key, rule in spec do
		local value = definition[key]

		if value == nil then
			if not rule.optional then
				table.insert(errors, `{label}: missing required field '{key}'`)
			end
			continue
		end

		if rule.kind == "rarity" then
			if type(value) ~= "string" or Constants.RARITY[value] == nil then
				table.insert(errors, `{label}: field '{key}' is not a known rarity (got {tostring(value)})`)
			end
		elseif type(value) ~= rule.kind then
			table.insert(
				errors,
				`{label}: field '{key}' expected {rule.kind}, got {type(value)}`
			)
		end
	end

	for key in definition do
		if spec[key] == nil then
			table.insert(errors, `{label}: unexpected field '{key}' -- amend the spec or remove it`)
		end
	end
end

--- Validates the world registry. Returns ok, errors.
function Schema.validateWorlds(worlds: { [string]: any }): (boolean, { string })
	local errors = {}
	local count = 0

	for key, world in worlds do
		count += 1
		validateOne(world, WORLD_SPEC, `World '{key}'`, errors)

		if type(world) == "table" then
			if world.Id ~= key then
				table.insert(errors, `World '{key}': Id field is '{tostring(world.Id)}' -- must match its registry key`)
			end
			if type(world.RollWeight) == "number" and world.RollWeight < 0 then
				table.insert(errors, `World '{key}': RollWeight must not be negative`)
			end
			if type(world.EnabledInPhase) == "number" and world.EnabledInPhase < 1 then
				table.insert(errors, `World '{key}': EnabledInPhase must be >= 1`)
			end
		end
	end

	if count == 0 then
		table.insert(errors, "world registry is empty")
	end

	return #errors == 0, errors
end

--- Cross-checks config against content. Catches the class of bug where a
--- config references content that does not exist -- an onboarding sequence
--- naming a deleted world would otherwise fail at a player's first roll.
function Schema.validateConfig(config: any, worlds: { [string]: any }): (boolean, { string })
	local errors = {}

	for index, worldId in config.Fate.OnboardingSequence do
		if not worlds[worldId] then
			table.insert(
				errors,
				`GameConfig.Fate.OnboardingSequence[{index}] names unknown world '{worldId}'`
			)
		end
	end

	if config.Fate.PrototypeWeights then
		for worldId in config.Fate.PrototypeWeights do
			if not worlds[worldId] then
				table.insert(errors, `GameConfig.Fate.PrototypeWeights names unknown world '{worldId}'`)
			end
		end
	end

	local enabled = 0
	for _, world in worlds do
		if type(world) == "table" and (world.EnabledInPhase or 99) <= config.CurrentPhase then
			enabled += 1
		end
	end
	if enabled == 0 then
		table.insert(errors, `no world has EnabledInPhase <= CurrentPhase ({config.CurrentPhase}) -- roll pool would be empty`)
	end

	return #errors == 0, errors
end

--- Validates the hub layout data. The hub is content like anything else, and
--- a malformed district would otherwise surface as a silently missing platform.
function Schema.validateHub(hub: any): (boolean, { string })
	local errors = {}

	if type(hub) ~= "table" then
		return false, { "hub layout is not a table" }
	end

	if type(hub.Theme) ~= "table" then
		table.insert(errors, "hub: missing Theme")
	end
	-- The Engine is the shared PortalRig at a scale; ring geometry lives in
	-- GameConfig.Portal, not here. Blueprint §1.3 / §2.2.
	if type(hub.FateEngine) ~= "table" then
		table.insert(errors, "hub: missing FateEngine")
	else
		local engine = hub.FateEngine
		if type(engine.AnchorSize) ~= "userdata" and type(engine.AnchorSize) ~= "table" then
			table.insert(errors, "hub: FateEngine.AnchorSize must be a Vector3")
		end
		if type(engine.PlatformRadius) ~= "number" or engine.PlatformRadius <= 0 then
			table.insert(errors, "hub: FateEngine.PlatformRadius must be positive")
		end
		if type(engine.PortalScale) ~= "number" or engine.PortalScale <= 0 then
			table.insert(errors, "hub: FateEngine.PortalScale must be positive")
		end
		if type(engine.CrystalShards) ~= "table" then
			table.insert(errors, "hub: FateEngine.CrystalShards must be a table")
		elseif type(engine.CrystalShards.Count) ~= "number" or engine.CrystalShards.Count < 1 then
			table.insert(errors, "hub: FateEngine.CrystalShards.Count must be >= 1")
		end
	end

	if type(hub.Districts) ~= "table" or #hub.Districts == 0 then
		table.insert(errors, "hub: Districts is empty")
	else
		local seen = {}
		for index, district in hub.Districts do
			local label = `hub: district #{index}`
			if type(district.Id) ~= "string" then
				table.insert(errors, `{label} is missing Id`)
			elseif seen[district.Id] then
				table.insert(errors, `{label} duplicates Id '{district.Id}'`)
			else
				seen[district.Id] = true
			end
			if type(district.Name) ~= "string" or district.Name == "" then
				table.insert(errors, `{label} needs a display Name`)
			end
			if type(district.Angle) ~= "number" or district.Angle < 0 or district.Angle >= 360 then
				table.insert(errors, `{label} Angle must be in [0, 360)`)
			end
			-- Radius 0 is legal: the Observatory sits directly above centre and
			-- is reached by the spiral ramp rather than a radial walkway.
			if type(district.Radius) ~= "number" or district.Radius < 0 then
				table.insert(errors, `{label} Radius must not be negative`)
			end
			if type(district.Kind) ~= "string" then
				table.insert(errors, `{label} is missing Kind (HubBuilder dispatches on it)`)
			end
			if district.Pillars ~= nil and (type(district.Pillars) ~= "number" or district.Pillars < 0) then
				table.insert(errors, `{label} Pillars must be >= 0`)
			end
		end
	end

	return #errors == 0, errors
end

--- Runs every check. Raises on failure -- called first in bootstrap.
function Schema.validateAll(worlds: { [string]: any }, config: any, hub: any?): ()
	local allErrors = {}

	local _, worldErrors = Schema.validateWorlds(worlds)
	for _, e in worldErrors do
		table.insert(allErrors, e)
	end

	local _, configErrors = Schema.validateConfig(config, worlds)
	for _, e in configErrors do
		table.insert(allErrors, e)
	end

	if hub ~= nil then
		local _, hubErrors = Schema.validateHub(hub)
		for _, e in hubErrors do
			table.insert(allErrors, e)
		end
	end

	if #allErrors > 0 then
		error(
			"LUCKBOUND content validation failed:\n  - " .. table.concat(allErrors, "\n  - "),
			0
		)
	end
end

return Schema
