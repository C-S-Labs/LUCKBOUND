--!strict
-- Server-authoritative developer commands. Testing tooling, not a feature.
--
-- ONLY the commands that must be server-side live here. Flying, walk speed and
-- teleporting are local effects the client already has authority over, so they
-- stay on the client (Controllers/DebugCommands) and cost no remote traffic.
-- What lands here is everything a client must not be trusted with: forcing a
-- roll result, entering an expedition without standing at the Gate, ending one.
--
-- THREE GATES, deliberately redundant:
--   1. GameConfig.Debug.AllowCommands -- no handler is even connected if false
--   2. Studio, or the place's creator -- checked per command, every time
--   3. the individual command's own flag (forced rolls have their own)
--
-- Gate 2 is the one that matters. A config flag left true by accident is a
-- mistake anyone can make; it should not by itself hand a stranger the ability
-- to roll themselves a Mythic on a live server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)
local Palettes = require(Root.Content.Hub.Palettes)

local DebugSystem = {}

local FateSystem
local ExpeditionSystem
local EventSystem

--- Who is allowed to run a command. Studio is the everyday case; the creator
--- check is what makes this safe to leave wired up on a published test place.
local function mayCommand(player: Player): boolean
	if not GameConfig.Debug.AllowCommands then
		return false
	end
	if RunService:IsStudio() then
		return true
	end
	-- A group-owned place has no single creator UserId to compare against, so
	-- it falls through to false rather than guessing at group ranks.
	if game.CreatorType == Enum.CreatorType.User and player.UserId == game.CreatorId then
		return true
	end
	return false
end

local function reply(player: Player, ok: boolean, text: string)
	Net.get("Debug_Reply"):FireClient(player, { Ok = ok, Text = text })
end

type Handler = (Player, { string }) -> (boolean, string)

local COMMANDS: { [string]: Handler } = {}

--- /roll <WORLD_ID> -- force the next destination.
--- With no argument, lists what you could have asked for, because typing a
--- world id from memory is exactly the sort of thing nobody should have to do.
COMMANDS.roll = function(player: Player, args: { string }): (boolean, string)
	local worldId = args[1]
	if not worldId then
		local ids = {}
		for id, world in Worlds do
			if world.EnabledInPhase <= GameConfig.CurrentPhase then
				table.insert(ids, id)
			end
		end
		table.sort(ids)
		return false, "usage: /roll <WORLD_ID> -- " .. table.concat(ids, ", ")
	end
	return FateSystem.forceRoll(player, string.upper(worldId))
end

--- /event <KIND> [SCOPE] [SECONDS] -- start a live event on this server.
---
--- THE ONLY WAY TO TEST A 1-IN-A-TRILLION EVENT. A Catalyst Star is supposed
--- to happen ten times in the life of the game; nobody can walk the sky it
--- produces by rolling for it. This starts one on demand so the lighting, the
--- menu tint and the announcement can actually be looked at.
---
--- It is a LOCAL event even when the scope says GLOBAL: this starts the event
--- on this server only, and deliberately does not publish cross-server, so a
--- test in Studio cannot crack the sky on a live place by accident.
COMMANDS.event = function(player: Player, args: { string }): (boolean, string)
	local kind = args[1]
	if not kind then
		local kinds = {}
		for _, entry in Palettes.Events do
			table.insert(kinds, entry.Kind)
		end
		table.sort(kinds)
		return false,
			"usage: /event <KIND> [GLOBAL|SERVER|BIOME] [seconds] -- tinted kinds: "
				.. table.concat(kinds, ", ")
	end

	local scope = string.upper(args[2] or "SERVER")
	if scope ~= "GLOBAL" and scope ~= "SERVER" and scope ~= "BIOME" then
		return false, "scope must be GLOBAL, SERVER or BIOME"
	end

	local duration = tonumber(args[3]) or GameConfig.Events.FatebreakDurationSeconds

	EventSystem.startLocal({
		Id = `DEBUG_{string.upper(kind)}_{os.time()}`,
		Kind = string.upper(kind),
		Name = string.upper(kind),
		Scope = scope,
		Priority = 0,
		Duration = duration,
		TriggeredBy = player.Name,
		Rarity = "MYTHIC",
	})

	return true, `started {string.upper(kind)} ({scope}) for {math.floor(duration)}s -- local server only`
end

--- /endevents -- stop every live event on this server at once.
--- The counterpart to /event: without it, testing the sky means waiting out
--- five minutes of Starfall before you can look at anything else.
COMMANDS.endevents = function(_player: Player, _args: { string }): (boolean, string)
	local ended = EventSystem.endAll()
	if ended == 0 then
		return false, "no events are running"
	end
	return true, `ended {ended} event(s)`
end

--- /enter -- start the expedition for your current destination, wherever you
--- are standing. The distance check is the thing being bypassed; everything
--- else (kit present, not already running, a slot free) still applies, because
--- skipping those would test a path the game does not have.
COMMANDS.enter = function(player: Player, _args: { string }): (boolean, string)
	return ExpeditionSystem.forceEnter(player)
end

--- /leave -- end the current expedition and go home. Counts as RETURNED, so
--- it awards Fate; use it to test the return path without waiting out a timer.
COMMANDS.leave = function(player: Player, _args: { string }): (boolean, string)
	if not ExpeditionSystem.isActive(player) then
		return false, "you are not on an expedition"
	end
	ExpeditionSystem.finish(player, "RETURNED")
	return true, "returned to the Crossroads"
end

function DebugSystem.handle(player: Player, name: any, args: any): ()
	if not mayCommand(player) then
		return -- silent: an unauthorised caller learns nothing
	end

	-- Every OnServerEvent handler validates argument type before use.
	-- FireServer can be called with anything at all.
	if type(name) ~= "string" then
		return
	end

	local cleanArgs: { string } = {}
	if type(args) == "table" then
		for _, value in args do
			if type(value) == "string" and #value <= 64 then
				table.insert(cleanArgs, value)
			end
			if #cleanArgs >= 8 then
				break
			end
		end
	end

	local handler = COMMANDS[string.lower(name)]
	if not handler then
		reply(player, false, `unknown command '{name}'`)
		return
	end

	local ok, text = handler(player, cleanArgs)
	print(`[Debug] {player.Name}: /{name} {table.concat(cleanArgs, " ")} -> {text}`)
	reply(player, ok, text)
end

function DebugSystem.init(fateSystem: any, expeditionSystem: any, eventSystem: any): ()
	FateSystem = fateSystem
	ExpeditionSystem = expeditionSystem
	EventSystem = eventSystem

	if not GameConfig.Debug.AllowCommands then
		print("[DebugSystem] commands disabled (GameConfig.Debug.AllowCommands)")
		return
	end

	Net.get("Debug_Command").OnServerEvent:Connect(function(player, name, args)
		DebugSystem.handle(player, name, args)
	end)

	local names = {}
	for name in COMMANDS do
		table.insert(names, "/" .. name)
	end
	table.sort(names)
	warn(
		`[DebugSystem] DEVELOPER COMMANDS ARE ON ({table.concat(names, " ")}) -- `
			.. "Studio or place creator only. Turn GameConfig.Debug.AllowCommands off before going public."
	)
end

DebugSystem.COMMANDS = COMMANDS
DebugSystem.mayCommand = mayCommand

return DebugSystem
