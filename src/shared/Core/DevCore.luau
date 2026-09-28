--!strict
-- The pure half of the developer tools: parsing a command line, checking the
-- registry (Content/DevCommands), and autocompleting names AND argument
-- values. No Instances, so the headless suite tests all of it.
--
-- Argument values that depend on content or on the live map (world ids, the
-- chunks of the map you are on) come in as `sources`: a map of source name to
-- a list, or to a function returning one, so a live list is read at the moment
-- you type rather than when the panel was built.

local DevCore = {}

-- Every Source a registry argument may name. The client supplies each one
-- (Controllers/DebugCommands.sources); the registry test fails on any other.
DevCore.SOURCES = {
	WORLDS = true, -- rollable world ids
	EVENTS = true, -- Content/Events ids
	ATMOSPHERES = true, -- BASE, RANDOM and every scenario atmosphere id
	BOSSES = true, -- Content/BossPreviews ids
	KEYS = true, -- vault key ids
	LEDGERS = true, -- unique ledger ids
	DESTINATIONS = true, -- hub anchor aliases for /tp
	CHUNKS = true, -- the current map's chunks (live)
}

DevCore.SIDES = { CLIENT = true, SERVER = true }
DevCore.TYPES = { choice = true, number = true, text = true }

export type Suggestion = {
	Text: string?, -- the whole line to put in the bar, or nil for a hint only
	Label: string,
	Hint: string,
}

--- "/Roll  sky_citadel test" -> "roll", { "sky_citadel", "test" }.
function DevCore.parse(line: string): (string?, { string })
	local words = {}
	for word in string.gmatch(line, "%S+") do
		table.insert(words, word)
	end
	if #words == 0 then
		return nil, {}
	end
	local name = string.lower((string.gsub(table.remove(words, 1) :: string, "^/", "")))
	if name == "" then
		return nil, words
	end
	return name, words
end

function DevCore.index(registry: any): { [string]: any }
	local byName = {}
	for _, c in registry.Commands do
		byName[c.Name] = c
	end
	return byName
end

--- "/showboss <boss> [height]"
function DevCore.usage(command: any): string
	local parts = { "/" .. command.Name }
	for _, a in command.Args or {} do
		table.insert(parts, if a.Optional then `[{a.Name}]` else `<{a.Name}>`)
	end
	return table.concat(parts, " ")
end

--- The values an argument can take, if it is a choice (or its Suggest list).
function DevCore.options(arg: any, sources: { [string]: any }?): { string }
	if arg.Options then
		return arg.Options
	end
	if arg.Source and sources then
		local src = sources[arg.Source]
		if type(src) == "function" then
			local ok, list = pcall(src)
			return if ok and type(list) == "table" then list else {}
		end
		if type(src) == "table" then
			return src
		end
	end
	return arg.Suggest or {}
end

--- Checks a typed argument list against a command: missing required
--- arguments, and choices that are not one of the options (case-insensitive).
--- Returns nil when fine, else a message with the usage.
function DevCore.check(command: any, args: { string }, _sources: { [string]: any }?): string?
	for i, a in command.Args or {} do
		local v = args[i]
		if v == nil then
			if not a.Optional then
				return `missing <{a.Name}> -- {DevCore.usage(command)}`
			end
		elseif a.Type == "number" then
			if tonumber(v) == nil then
				return `<{a.Name}> must be a number -- {DevCore.usage(command)}`
			end
		elseif a.Type == "choice" and a.Options then
			local found = false
			for _, o in a.Options do
				if string.lower(o) == string.lower(v) then
					found = true
				end
			end
			if not found then
				return `<{a.Name}> must be one of {table.concat(a.Options, ", ")}`
			end
		end
	end
	return nil
end

local function startsWith(s: string, prefix: string): boolean
	return string.sub(string.lower(s), 1, #prefix) == string.lower(prefix)
end

--- Autocomplete for a command line. While the name is being typed: the
--- commands that start with it (then any that contain it). After the name: the
--- values of the argument being typed, each as the whole line to put back in
--- the bar. A number/text argument with nothing to offer gives one hint.
function DevCore.complete(
	line: string,
	registry: any,
	sources: { [string]: any }?,
	limit: number?
): { Suggestion }
	local max = limit or 12
	local out: { Suggestion } = {}
	local body = string.gsub(line, "^%s*/?", "")
	local trailing = string.match(line, "%s$") ~= nil
	local words = {}
	for word in string.gmatch(body, "%S+") do
		table.insert(words, word)
	end

	-- the command name
	if #words == 0 or (#words == 1 and not trailing) then
		local typed = string.lower(words[1] or "")
		local first, rest = {}, {}
		for _, c in registry.Commands do
			if startsWith(c.Name, typed) then
				table.insert(first, c)
			elseif typed ~= "" and string.find(c.Name, typed, 1, true) then
				table.insert(rest, c)
			end
		end
		for _, list in { first, rest } do
			for _, c in list do
				if #out >= max then
					return out
				end
				local spaced = if c.Args and #c.Args > 0 then " " else ""
				table.insert(
					out,
					{ Text = "/" .. c.Name .. spaced, Label = DevCore.usage(c), Hint = c.Summary }
				)
			end
		end
		return out
	end

	-- an argument
	local command = DevCore.index(registry)[string.lower(words[1])]
	if not command then
		return out
	end
	local done = if trailing then #words - 1 else #words - 2 -- arguments already finished
	local arg = (command.Args or {})[done + 1]
	if not arg then
		return out
	end
	local typed = if trailing then "" else words[#words]
	local head = { "/" .. command.Name }
	for i = 2, done + 1 do
		table.insert(head, words[i])
	end
	local prefix = table.concat(head, " ") .. " "
	for _, value in DevCore.options(arg, sources) do
		if #out >= max then
			break
		end
		if startsWith(value, typed) then
			local more = (command.Args or {})[done + 2] ~= nil
			table.insert(out, {
				Text = prefix .. value .. (if more then " " else ""),
				Label = value,
				Hint = arg.Name,
			})
		end
	end
	if #out == 0 and arg.Type ~= "choice" then
		local range = if arg.Min and arg.Max then ` ({arg.Min}-{arg.Max})` else ""
		table.insert(out, {
			Text = nil,
			Label = `<{arg.Name}>{range}`,
			Hint = (if arg.Optional then "optional " else "") .. arg.Type,
		})
	end
	return out
end

--- Everything wrong with a registry, as messages (empty when it is sound).
function DevCore.validate(registry: any): { string }
	local errors = {}
	local cats = {}
	for _, c in registry.Categories or {} do
		if type(c.Id) ~= "string" or type(c.Label) ~= "string" then
			table.insert(errors, "a category needs a string Id and Label")
		elseif cats[c.Id] then
			table.insert(errors, `duplicate category {c.Id}`)
		else
			cats[c.Id] = true
		end
	end
	local seen = {}
	for i, c in registry.Commands or {} do
		local at = `command #{i} ({tostring(c.Name)})`
		if type(c.Name) ~= "string" or not string.match(c.Name, "^[a-z][a-z0-9]*$") then
			table.insert(errors, `{at}: Name must be lower-case letters/digits`)
		elseif seen[c.Name] then
			table.insert(errors, `{at}: duplicate name`)
		else
			seen[c.Name] = true
		end
		if not cats[c.Category] then
			table.insert(errors, `{at}: unknown category {tostring(c.Category)}`)
		end
		if not DevCore.SIDES[c.Side] then
			table.insert(errors, `{at}: Side must be CLIENT or SERVER`)
		end
		if type(c.Summary) ~= "string" or c.Summary == "" then
			table.insert(errors, `{at}: needs a Summary`)
		end
		local optional = false
		for j, a in c.Args or {} do
			local aat = `{at} arg {j}`
			if type(a.Name) ~= "string" then
				table.insert(errors, `{aat}: needs a Name`)
			end
			if not DevCore.TYPES[a.Type] then
				table.insert(errors, `{aat}: Type must be choice, number or text`)
			end
			if
				a.Type == "choice"
				and not a.Options
				and not (a.Source and DevCore.SOURCES[a.Source])
			then
				table.insert(errors, `{aat}: a choice needs Options or a known Source`)
			end
			if a.Optional then
				optional = true
			elseif optional then
				table.insert(errors, `{aat}: a required argument after an optional one`)
			end
		end
		for _, pr in c.Presets or {} do
			if type(pr.Label) ~= "string" or type(pr.Args) ~= "table" then
				table.insert(errors, `{at}: a preset needs a Label and Args`)
			end
		end
	end
	return errors
end

return DevCore
