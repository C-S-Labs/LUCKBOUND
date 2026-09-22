--!strict
-- Boot-time content validation. Build spec T-107.
-- The server must refuse to start on malformed content: a prototype that boots
-- with silently broken data is worse than one that does not boot.

local Constants = require(script.Parent.Parent.Core.Constants)
local EventCore = require(script.Parent.Parent.Core.EventCore)

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
	MapPathLength = field("number", true),
	PrebuiltMap = field("table", true),
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
			if type(world.MapPathLength) == "number" and world.MapPathLength < 1 then
				table.insert(errors, `World '{key}': MapPathLength must be >= 1`)
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

	-- Expeditions as their own server, and parties (build spec §7.2).
	local mode = config.Expedition.InstanceMode
	if mode ~= "AUTO" and mode ~= "TELEPORT" and mode ~= "IN_PLACE" then
		table.insert(errors, `GameConfig.Expedition.InstanceMode must be AUTO, TELEPORT or IN_PLACE, got {tostring(mode)}`)
	end
	local party = config.Party
	if type(party) ~= "table" then
		table.insert(errors, "GameConfig.Party is missing")
	else
		-- A party of one is a player; two is the smallest party there is.
		if type(party.MaxSize) ~= "number" or party.MaxSize < 2 then
			table.insert(errors, `GameConfig.Party.MaxSize must be at least 2, got {tostring(party.MaxSize)}`)
		end
		if type(party.InviteExpirySeconds) ~= "number" or party.InviteExpirySeconds <= 0 then
			table.insert(errors, "GameConfig.Party.InviteExpirySeconds must be positive")
		end
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
		-- typeof, not type: Luau reports Vector3 as the native "vector" type,
		-- so type() can never identify a Roblox datatype. typeof() is the only
		-- correct test for one.
		if typeof(engine.AnchorSize) ~= "Vector3" then
			table.insert(
				errors,
				`hub: FateEngine.AnchorSize must be a Vector3, got {typeof(engine.AnchorSize)}`
			)
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
			-- Radius 0 is legal: a district may sit at the hub's centre and be
			-- reached by something other than a radial walkway.
			if type(district.Radius) ~= "number" or district.Radius < 0 then
				table.insert(errors, `{label} Radius must not be negative`)
			end
			if type(district.Kind) ~= "string" then
				table.insert(errors, `{label} is missing Kind (HubBuilder dispatches on it)`)
			end
			if district.Pillars ~= nil and (type(district.Pillars) ~= "number" or district.Pillars < 0) then
				table.insert(errors, `{label} Pillars must be >= 0`)
			end
			-- A ROUND platform is drawn from PlatformRadius, so declaring the
			-- shape without the radius would silently build nothing.
			if district.PlatformShape == "ROUND" then
				if type(district.PlatformRadius) ~= "number" or district.PlatformRadius <= 0 then
					table.insert(errors, `{label} is ROUND but has no positive PlatformRadius`)
				end
			end
		end
	end

	return #errors == 0, errors
end

--- Validates the chunk library and cross-checks every AssetKey against the
--- manifest. A chunk naming a missing asset is the same class of bug as an
--- onboarding sequence naming a missing world -- catch it at boot.
function Schema.validateChunks(chunks: { [string]: any }, manifest: any): (boolean, { string })
	local errors = {}
	local VALID_ROLES =
		{ ENTRY = true, PATH = true, COMBAT = true, SIDE = true, BOSS = true }
	local QUARTER = { [0] = true, [90] = true, [180] = true, [270] = true }

	local perWorld: { [string]: { [string]: number } } = {}

	for key, chunk in chunks do
		local label = `Chunk '{key}'`

		if chunk.Id ~= key then
			table.insert(errors, `{label}: Id is '{tostring(chunk.Id)}' -- must match its registry key`)
		end
		if not VALID_ROLES[chunk.Role] then
			table.insert(errors, `{label}: unknown Role '{tostring(chunk.Role)}'`)
		end
		if type(chunk.WorldId) ~= "string" then
			table.insert(errors, `{label}: missing WorldId`)
		end
		if type(chunk.Weight) ~= "number" or chunk.Weight <= 0 then
			table.insert(errors, `{label}: Weight must be positive`)
		end
		for _, dim in { "SizeX", "SizeY", "SizeZ" } do
			if type(chunk[dim]) ~= "number" or chunk[dim] <= 0 then
				table.insert(errors, `{label}: {dim} must be positive`)
			end
		end

		-- GroundOffsetY is optional -- absent means "the walk plane is the
		-- bounding-box centre", which is what every chunk meant before the
		-- field existed. Present, it must be INSIDE the piece: a walk plane
		-- outside its own bounding box would float the chunk off the layout
		-- plane by however wrong the number is, silently.
		if chunk.GroundOffsetY ~= nil then
			if type(chunk.GroundOffsetY) ~= "number" then
				table.insert(errors, `{label}: GroundOffsetY must be a number`)
			elseif
				type(chunk.SizeY) == "number"
				and (chunk.GroundOffsetY < 0 or chunk.GroundOffsetY > chunk.SizeY)
			then
				table.insert(
					errors,
					`{label}: GroundOffsetY {chunk.GroundOffsetY} is outside the piece (SizeY {chunk.SizeY})`
				)
			end
		end

		if not manifest.exists(chunk.AssetKey) then
			table.insert(
				errors,
				`{label}: AssetKey '{tostring(chunk.AssetKey)}' is not in the asset manifest`
			)
		end

		-- Supports is the scenario-compatibility gate. A placeable chunk with
		-- none supports nothing, so the generator would have no room to fill
		-- and the piece would be walked through empty. ENTRY and BOSS are
		-- exempt: neither is ever assigned a scenario.
		if chunk.Role == "PATH" or chunk.Role == "COMBAT" or chunk.Role == "SIDE" then
			if type(chunk.Supports) ~= "table" then
				table.insert(errors, `{label}: {chunk.Role} chunks need a Supports table`)
			else
				local any = false
				for _, v in chunk.Supports do
					if v then
						any = true
					end
				end
				if not any then
					table.insert(errors, `{label}: Supports declares nothing, so no scenario can be placed here`)
				end
			end
		end

		if type(chunk.Sockets) ~= "table" or #chunk.Sockets == 0 then
			table.insert(errors, `{label}: has no sockets, so nothing can connect to it`)
		else
			local seen = {}
			for _, socket in chunk.Sockets do
				if seen[socket.Id] then
					table.insert(errors, `{label}: duplicate socket id '{socket.Id}'`)
				end
				seen[socket.Id] = true
				if not QUARTER[socket.Facing] then
					table.insert(
						errors,
						`{label}: socket '{socket.Id}' Facing must be 0, 90, 180 or 270 (got {tostring(socket.Facing)})`
					)
				end
			end

			-- Anything on the critical path needs a way in AND a way out.
			if (chunk.Role == "PATH" or chunk.Role == "COMBAT") and #chunk.Sockets < 2 then
				table.insert(errors, `{label}: {chunk.Role} chunks need at least 2 sockets, or the path dead-ends`)
			end
		end

		if type(chunk.WorldId) == "string" then
			perWorld[chunk.WorldId] = perWorld[chunk.WorldId] or {}
			local counts = perWorld[chunk.WorldId]
			counts[chunk.Role] = (counts[chunk.Role] or 0) + 1
		end
	end

	-- A world with pieces must have a complete kit, or assembly always fails.
	for worldId, counts in perWorld do
		for _, role in { "ENTRY", "BOSS" } do
			if (counts[role] or 0) == 0 then
				table.insert(errors, `world '{worldId}' has chunks but no {role} chunk`)
			end
		end
		if (counts.PATH or 0) + (counts.COMBAT or 0) == 0 then
			table.insert(errors, `world '{worldId}' has no PATH or COMBAT chunks`)
		end

		-- A SIDE pocket hangs off a socket the critical path did not spend,
		-- and the path spends two per piece -- one to arrive, one to leave.
		-- So a kit whose pieces all have two sockets has no spare socket on
		-- any seed, and its SIDE pieces validate, pass every other test and
		-- are never once placed. That is exactly what happened to Verdant
		-- Valley's Fern Hollow. Refuse it at boot instead: a declared pocket
		-- that cannot be reached is a content bug, not a quiet no-op.
		if (counts.SIDE or 0) > 0 then
			local hasSpare = false
			for _, chunk in chunks do
				if chunk.WorldId == worldId and type(chunk.Sockets) == "table" and #chunk.Sockets >= 3 then
					hasSpare = true
				end
			end
			if not hasSpare then
				table.insert(
					errors,
					`world '{worldId}' declares a SIDE chunk but no chunk has 3+ sockets, `
						.. `so the critical path spends every socket and the pocket can never attach`
				)
			end
		end
	end

	return #errors == 0, errors
end

--- The scenario library, and that the chunk kits can actually host it.
---
--- Two failure modes, both silent without this: a scenario whose Requires key
--- no chunk declares can never be placed, and a Band or Weight typo quietly
--- removes a scenario from the draw. Neither shows up as an error at runtime;
--- the run is simply less varied than the content says it is.
function Schema.validateScenarios(
	scenarios: { [string]: any },
	chunks: { [string]: any }?
): (boolean, { string })
	local errors = {}
	local BANDS = { ORDINARY = true, UNCOMMON = true, RARE = true }

	for key, s in scenarios do
		local label = `Scenario '{key}'`
		if s.Id ~= key then
			table.insert(errors, `{label}: Id is '{tostring(s.Id)}' -- must match its registry key`)
		end
		if not BANDS[s.Band] then
			table.insert(errors, `{label}: unknown Band '{tostring(s.Band)}'`)
		end
		if type(s.Weight) ~= "number" or s.Weight <= 0 then
			table.insert(errors, `{label}: Weight must be positive`)
		end
		if type(s.Requires) ~= "string" or s.Requires == "" then
			table.insert(errors, `{label}: Requires must name a Supports key`)
		end
	end

	-- Every scenario must be reachable by SOMETHING, or it is content nobody
	-- will ever see.
	if chunks then
		for key, s in scenarios do
			if type(s.Requires) == "string" then
				local reachable = false
				for _, chunk in chunks do
					if type(chunk.Supports) == "table" and chunk.Supports[s.Requires] then
						reachable = true
					end
				end
				if not reachable then
					table.insert(
						errors,
						`Scenario '{key}': no chunk in any world declares Supports.{s.Requires}, so it can never be placed`
					)
				end
			end
		end
	end

	return #errors == 0, errors
end

--- Cross-checks how each world gets its map.
---
--- A world builds its map EITHER by assembling a chunk kit OR by cloning one
--- authored scene. Declaring both is not a richer world, it is an ambiguity:
--- something downstream would have to pick, and picking is exactly the second
--- competing architecture CLAUDE.md rule 1 exists to prevent. So it is a boot
--- error, not a warning.
function Schema.validateMaps(
	worlds: { [string]: any },
	chunks: { [string]: any },
	manifest: any
): (boolean, { string })
	local errors = {}

	local kitted: { [string]: boolean } = {}
	for _, chunk in chunks do
		if type(chunk.WorldId) == "string" then
			kitted[chunk.WorldId] = true
		end
	end

	for key, world in worlds do
		local prebuilt = type(world) == "table" and world.PrebuiltMap or nil
		if prebuilt == nil then
			continue
		end

		local label = `World '{key}' PrebuiltMap`

		if type(prebuilt) ~= "table" then
			table.insert(errors, `{label}: expected a table, got {type(prebuilt)}`)
			continue
		end

		if type(prebuilt.AssetKey) ~= "string" then
			table.insert(errors, `{label}: missing AssetKey`)
		elseif not manifest.exists(prebuilt.AssetKey) then
			table.insert(
				errors,
				`{label}: AssetKey '{prebuilt.AssetKey}' is not in the asset manifest`
			)
		end

		-- Scale is what makes an oversized authored scene walkable. A zero or
		-- negative one would collapse or invert the map, and Model:ScaleTo
		-- would not complain until a player was standing in it.
		if type(prebuilt.Scale) ~= "number" or prebuilt.Scale <= 0 then
			table.insert(errors, `{label}: Scale must be a positive number`)
		end

		if kitted[key] then
			table.insert(
				errors,
				`World '{key}' has BOTH a chunk kit and a PrebuiltMap -- pick one`
			)
		end

		-- MapPathLength only means something to the assembler. Left on a
		-- prebuilt world it reads as a live tuning knob that does nothing.
		if world.MapPathLength ~= nil then
			table.insert(
				errors,
				`World '{key}' is prebuilt, so MapPathLength does nothing -- remove it`
			)
		end
	end

	return #errors == 0, errors
end

--- The hub menu: panels and travel destinations. Two classes of bug are
--- worth failing a boot over -- a panel the rail cannot draw (no label, no
--- order) and a destination that names an anchor the hub does not have, which
--- would teleport a player to (0, 0, 0) and look like a physics bug rather
--- than like bad data.
function Schema.validateHubMenu(menu: any, config: any): (boolean, { string })
	local errors = {}

	if type(menu) ~= "table" then
		return false, { "hub menu: expected a table" }
	end

	local VALID_STATUS = { LIVE = true, PREVIEW = true }

	local seenPanel = {}
	local seenOrder = {}
	for index, panel in menu.Panels or {} do
		local label = `hub menu panel #{index}`
		for _, key in { "Id", "Label", "Glyph", "Summary" } do
			if type(panel[key]) ~= "string" then
				table.insert(errors, `{label}: '{key}' must be a string`)
			end
		end
		if type(panel.Order) ~= "number" then
			table.insert(errors, `{label}: 'Order' must be a number`)
		elseif seenOrder[panel.Order] then
			table.insert(errors, `{label}: duplicate Order {panel.Order}`)
		else
			seenOrder[panel.Order] = true
		end
		if panel.Hotkey ~= nil and not Constants.HOTKEY_NAMES[panel.Hotkey] then
			table.insert(
				errors,
				`{label}: Hotkey '{tostring(panel.Hotkey)}' is not in Constants.HOTKEY_NAMES`
			)
		end
		if not VALID_STATUS[panel.Status] then
			table.insert(errors, `{label}: Status must be LIVE or PREVIEW, got {tostring(panel.Status)}`)
		end
		if type(panel.Id) == "string" then
			if seenPanel[panel.Id] then
				table.insert(errors, `{label}: duplicate panel Id '{panel.Id}'`)
			end
			seenPanel[panel.Id] = true
		end
	end

	if next(seenPanel) == nil then
		table.insert(errors, "hub menu: no panels defined")
	end

	-- The name that started all this. Indexing Enum.KeyCode with a name it
	-- does not have raises, so a typo here is an error on every keystroke
	-- rather than a shortcut that quietly does nothing.
	if menu.CollapseHotkey ~= nil and not Constants.HOTKEY_NAMES[menu.CollapseHotkey] then
		table.insert(
			errors,
			`hub menu: CollapseHotkey '{tostring(menu.CollapseHotkey)}' is not in Constants.HOTKEY_NAMES`
		)
	end

	local anchors = config.HubLayout.Anchors
	local seenDestination = {}
	for index, destination in menu.Destinations or {} do
		local label = `hub menu destination #{index}`
		if type(destination.Id) ~= "string" then
			table.insert(errors, `{label}: 'Id' must be a string`)
		elseif seenDestination[destination.Id] then
			table.insert(errors, `{label}: duplicate destination Id '{destination.Id}'`)
		else
			seenDestination[destination.Id] = true
		end

		if type(destination.AnchorId) ~= "string" or anchors[destination.AnchorId] == nil then
			table.insert(
				errors,
				`{label}: AnchorId '{tostring(destination.AnchorId)}' is not in GameConfig.HubLayout.Anchors`
			)
		elseif typeof(destination.Anchor) ~= "Vector3" then
			table.insert(errors, `{label}: 'Anchor' must be a Vector3`)
		elseif destination.Anchor ~= anchors[destination.AnchorId] then
			-- The Anchor field is a convenience copy. If it ever drifts from
			-- the anchor it names, the menu and the hub disagree about where
			-- a district IS, and the menu wins -- silently.
			table.insert(errors, `{label}: 'Anchor' does not match Anchors.{destination.AnchorId}`)
		end

		if typeof(destination.Landing) ~= "Vector3" then
			table.insert(errors, `{label}: 'Landing' must be a Vector3`)
		end
		if type(destination.Facing) ~= "number" then
			table.insert(errors, `{label}: 'Facing' must be a number`)
		end
	end

	if next(seenDestination) == nil then
		table.insert(errors, "hub menu: no travel destinations defined")
	end

	return #errors == 0, errors
end

--- Redeemable codes. A code whose Id does not match its registry key is the
--- bug worth catching: redemption is RECORDED by Id, so a mismatch would let
--- the same code be redeemed twice under two names.
function Schema.validateCodes(codes: any): (boolean, { string })
	local errors = {}

	local seenText = {}
	for key, definition in codes do
		local label = `code '{key}'`
		if type(definition) ~= "table" then
			table.insert(errors, `{label}: expected a table`)
			continue
		end
		if definition.Id ~= key then
			table.insert(errors, `{label}: Id '{tostring(definition.Id)}' must match its registry key`)
		end
		if type(definition.Code) ~= "string" or definition.Code == "" then
			table.insert(errors, `{label}: 'Code' must be a non-empty string`)
		else
			local normalised = (string.upper(definition.Code):gsub("[^%w]", ""))
			if seenText[normalised] then
				table.insert(errors, `{label}: '{definition.Code}' collides with code '{seenText[normalised]}'`)
			end
			seenText[normalised] = key
		end
		if type(definition.Fate) ~= "number" or definition.Fate < 0 then
			table.insert(errors, `{label}: 'Fate' must be a non-negative number`)
		end
		if type(definition.Message) ~= "string" then
			table.insert(errors, `{label}: 'Message' must be a string`)
		end
		if definition.ExpiresAt ~= nil and type(definition.ExpiresAt) ~= "number" then
			table.insert(errors, `{label}: 'ExpiresAt' must be a number or nil`)
		end
	end

	return #errors == 0, errors
end

--- The loading screen's camera tour. A shot with a zero or negative radius
--- puts the camera inside its own subject, which renders as a grey screen --
--- indistinguishable, to a player, from the game failing to load at all.
function Schema.validateCinematics(cinematics: any, worlds: { [string]: any }): (boolean, { string })
	local errors = {}

	local shots = if type(cinematics) == "table" then cinematics.Shots else nil
	if type(shots) ~= "table" or #shots == 0 then
		return false, { "cinematics: no shots defined" }
	end

	local seen = {}
	for index, shot in shots do
		local label = `cinematic shot #{index}`
		if type(shot.Id) ~= "string" then
			table.insert(errors, `{label}: 'Id' must be a string`)
		elseif seen[shot.Id] then
			table.insert(errors, `{label}: duplicate shot Id '{shot.Id}'`)
		else
			seen[shot.Id] = true
		end
		if type(shot.Caption) ~= "string" then
			table.insert(errors, `{label}: 'Caption' must be a string`)
		end
		if typeof(shot.Subject) ~= "Vector3" then
			table.insert(errors, `{label}: 'Subject' must be a Vector3`)
		end
		if typeof(shot.LookOffset) ~= "Vector3" then
			table.insert(errors, `{label}: 'LookOffset' must be a Vector3`)
		end
		if type(shot.Radius) ~= "number" or shot.Radius <= 0 then
			table.insert(errors, `{label}: 'Radius' must be greater than zero`)
		end
		if type(shot.Height) ~= "number" then
			table.insert(errors, `{label}: 'Height' must be a number`)
		end
		if shot.WorldId ~= nil and worlds[shot.WorldId] == nil then
			table.insert(errors, `{label}: WorldId '{tostring(shot.WorldId)}' is not a known world`)
		end
	end

	return #errors == 0, errors
end

--- The live palette layer. Two classes of bug are worth a failed boot: a
--- district tint naming a district that does not exist (which would simply
--- never appear, silently), and a strength outside 0..1 (which would push the
--- menu past the colour it was leaning toward and out the other side).
---
--- What is NOT checked here is contrast -- that is enforced at resolve time
--- by ThemeCore rather than refused at boot, because a too-strong tint should
--- degrade to a duller one rather than stop the server.
function Schema.validatePalettes(palettes: any, menu: any): (boolean, { string })
	local errors = {}

	if type(palettes) ~= "table" then
		return false, { "palettes: expected a table" }
	end

	local known = {}
	for _, destination in menu.Destinations do
		known[destination.Id] = true
	end

	local seenDistrict = {}
	for index, entry in palettes.Districts or {} do
		local label = `palette district #{index}`
		if type(entry.Id) ~= "string" then
			table.insert(errors, `{label}: 'Id' must be a string`)
		elseif not known[entry.Id] then
			table.insert(errors, `{label}: '{entry.Id}' is not a district the menu knows`)
		elseif seenDistrict[entry.Id] then
			table.insert(errors, `{label}: duplicate district '{entry.Id}'`)
		else
			seenDistrict[entry.Id] = true
		end

		if type(entry.Strength) ~= "number" or entry.Strength < 0 or entry.Strength > 1 then
			table.insert(errors, `{label}: 'Strength' must be between 0 and 1`)
		end
		if entry.Tint ~= nil and typeof(entry.Tint) ~= "Color3" then
			table.insert(errors, `{label}: 'Tint' must be a Color3 or nil`)
		end
		if entry.Tint == nil and entry.Strength ~= 0 then
			-- A strength with nothing to lean toward is a half-finished edit,
			-- and it reads as "this district is deliberately untinted" to
			-- everyone who comes after.
			table.insert(errors, `{label}: has a Strength but no Tint -- set Strength to 0`)
		end
	end

	local seenKind = {}
	for index, entry in palettes.Events or {} do
		local label = `palette event #{index}`
		if type(entry.Kind) ~= "string" then
			table.insert(errors, `{label}: 'Kind' must be a string`)
		elseif seenKind[entry.Kind] then
			table.insert(errors, `{label}: duplicate event kind '{entry.Kind}'`)
		else
			seenKind[entry.Kind] = true
		end
		if typeof(entry.Tint) ~= "Color3" then
			table.insert(errors, `{label}: 'Tint' must be a Color3`)
		end
		if type(entry.Strength) ~= "number" or entry.Strength < 0 or entry.Strength > 1 then
			table.insert(errors, `{label}: 'Strength' must be between 0 and 1`)
		end
	end

	return #errors == 0, errors
end

--- Live events. The rules here are the ones that turn docs/EVENTS.md's tier
--- system from an intention into something the boot refuses to violate.
---
--- The one worth the most: an event may only write lighting properties that
--- EventCore.LIGHTING_PROPERTIES names, because that list is also what the
--- client snapshots and restores. An event writing anything else would leave
--- it changed after the event ended -- an aurora that leaves the fog green
--- until the player rejoins.
function Schema.validateEvents(events: any, worlds: { [string]: any }): (boolean, { string })
	local errors = {}

	local TIERS = { AMBIENT = true, MODIFIER = true, WORLD = true }
	local count = 0

	for key, event in events do
		count += 1
		local label = `Event '{key}'`

		if type(event) ~= "table" then
			table.insert(errors, `{label}: expected a table`)
			continue
		end

		if event.Id ~= key then
			table.insert(errors, `{label}: Id '{tostring(event.Id)}' must match its registry key`)
		end
		for _, field in { "Name", "Kind" } do
			if type(event[field]) ~= "string" then
				table.insert(errors, `{label}: '{field}' must be a string`)
			end
		end

		if not TIERS[event.Tier] then
			table.insert(errors, `{label}: Tier must be AMBIENT, MODIFIER or WORLD (got {tostring(event.Tier)})`)
		end
		if not EventCore.isValidScope(event.Scope) then
			table.insert(errors, `{label}: Scope must be GLOBAL, SERVER or BIOME (got {tostring(event.Scope)})`)
		end
		if event.Scope == "BIOME" then
			if type(event.WorldId) ~= "string" or worlds[event.WorldId] == nil then
				table.insert(errors, `{label}: a BIOME event must name a world that exists`)
			end
		elseif event.WorldId ~= nil then
			table.insert(errors, `{label}: only a BIOME event may name a WorldId`)
		end

		if type(event.Priority) ~= "number" then
			table.insert(errors, `{label}: 'Priority' must be a number`)
		end
		if type(event.DurationSeconds) ~= "number" or event.DurationSeconds <= 0 then
			table.insert(errors, `{label}: 'DurationSeconds' must be greater than zero`)
		end

		-- === THE TIER RULES (docs/EVENTS.md §4.0) ===
		if event.Tier ~= "WORLD" then
			if event.Unique ~= nil then
				table.insert(errors, `{label}: only a WORLD event may grant a unique`)
			end
			if event.Rift ~= nil then
				table.insert(errors, `{label}: only a WORLD event may open a rift`)
			end
		end
		if event.Tier == "AMBIENT" and event.Modifiers ~= nil then
			table.insert(
				errors,
				`{label}: an AMBIENT event changes the sky and nothing else -- use MODIFIER`
			)
		end

		if event.Unique ~= nil then
			if type(event.Unique.LedgerId) ~= "string" then
				table.insert(errors, `{label}: Unique.LedgerId must be a string`)
			end
			if type(event.Unique.Cap) ~= "number" or event.Unique.Cap < 1 then
				table.insert(errors, `{label}: Unique.Cap must be at least 1`)
			end
		end

		if type(event.Announcement) ~= "table" then
			table.insert(errors, `{label}: 'Announcement' must be a table`)
		else
			if type(event.Announcement.Text) ~= "string" then
				table.insert(errors, `{label}: Announcement.Text must be a string`)
			else
				-- A placeholder nobody substitutes reaches the player as raw
				-- braces, which is the sort of thing that ships.
				for placeholder in string.gmatch(event.Announcement.Text, "{(%w+)}") do
					if placeholder ~= "player" and placeholder ~= "event" and placeholder ~= "remaining" then
						table.insert(
							errors,
							`{label}: Announcement.Text uses unknown placeholder '{placeholder}'`
						)
					end
				end
			end
			if
				event.Announcement.Rarity ~= nil
				and Constants.RARITY[event.Announcement.Rarity] == nil
			then
				table.insert(errors, `{label}: Announcement.Rarity is not a known rarity`)
			end
		end

		if event.Lighting ~= nil then
			if type(event.Lighting) ~= "table" then
				table.insert(errors, `{label}: 'Lighting' must be a table`)
			else
				for field in event.Lighting do
					if EventCore.LIGHTING_PROPERTIES[field] == nil then
						table.insert(
							errors,
							`{label}: Lighting.'{field}' is not a property anything restores -- `
								.. `add it to EventCore.LIGHTING_PROPERTIES or remove it`
						)
					end
				end
			end
		end

		if event.Sky ~= nil then
			if type(event.Sky) ~= "table" then
				table.insert(errors, `{label}: 'Sky' must be a table`)
			elseif event.Sky.Enabled and typeof(event.Sky.ParticleColor) ~= "Color3" then
				table.insert(errors, `{label}: Sky.ParticleColor must be a Color3`)
			end
		end
	end

	if count == 0 then
		table.insert(errors, "event registry is empty")
	end

	return #errors == 0, errors
end

--- Runs every check. Raises on failure -- called first in bootstrap.
function Schema.validateAll(
	worlds: { [string]: any },
	config: any,
	hub: any?,
	chunks: { [string]: any }?,
	manifest: any?,
	menu: any?,
	codes: any?,
	cinematics: any?,
	palettes: any?,
	events: any?,
	scenarios: any?
): ()
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

	if scenarios ~= nil then
		local _, scenarioErrors = Schema.validateScenarios(scenarios, chunks)
		for _, e in scenarioErrors do
			table.insert(allErrors, e)
		end
	end

	if chunks ~= nil and manifest ~= nil then
		local _, chunkErrors = Schema.validateChunks(chunks, manifest)
		for _, e in chunkErrors do
			table.insert(allErrors, e)
		end

		local _, mapErrors = Schema.validateMaps(worlds, chunks, manifest)
		for _, e in mapErrors do
			table.insert(allErrors, e)
		end
	end

	if menu ~= nil then
		local _, menuErrors = Schema.validateHubMenu(menu, config)
		for _, e in menuErrors do
			table.insert(allErrors, e)
		end
	end

	if codes ~= nil then
		local _, codeErrors = Schema.validateCodes(codes)
		for _, e in codeErrors do
			table.insert(allErrors, e)
		end
	end

	if cinematics ~= nil then
		local _, cinematicErrors = Schema.validateCinematics(cinematics, worlds)
		for _, e in cinematicErrors do
			table.insert(allErrors, e)
		end
	end

	if palettes ~= nil and menu ~= nil then
		local _, paletteErrors = Schema.validatePalettes(palettes, menu)
		for _, e in paletteErrors do
			table.insert(allErrors, e)
		end
	end

	if events ~= nil then
		local _, eventErrors = Schema.validateEvents(events, worlds)
		for _, e in eventErrors do
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
