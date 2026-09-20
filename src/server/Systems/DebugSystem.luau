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
local Events = require(Root.Content.Events)

local DebugSystem = {}

local FateSystem
local ExpeditionSystem
local EventSystem
local LedgerSystem

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

--- /event <ID> -- start an authored event from Content/Events.
---
--- THE ONLY WAY TO TEST A 1-IN-A-TRILLION EVENT. A Catalyst Star should
--- happen ten times in the life of the game; nobody can walk the sky it
--- produces by rolling for it. This starts one on demand so the lighting, the
--- sky layer, the menu tint and the announcement can actually be looked at.
---
--- A unique event started this way STILL CLAIMS FROM THE LEDGER, deliberately:
--- testing the sky must not be a way to mint an eleventh Star. Use a
--- non-unique event to test the visuals, and expect /event CATALYST_STAR to
--- refuse once ten exist.
COMMANDS.event = function(player: Player, args: { string }): (boolean, string)
	local id = args[1] and string.upper(args[1])
	if not id then
		local ids = {}
		for key, definition in Events do
			table.insert(ids, `{key} ({definition.Tier})`)
		end
		table.sort(ids)
		return false, "usage: /event <ID> -- " .. table.concat(ids, ", ")
	end

	local result = EventSystem.trigger(id, player)
	if not result.ok then
		return false, `could not start {id}: {result.err}`
	end
	return true, `started {id} ({result.value.Scope}) for {math.floor(result.value.Duration)}s`
end

--- /ledger [ID] -- how many of a unique have ever been claimed, and by whom.
--- The scarcity is the feature; being able to see it is how you know the
--- ledger is working before ten of them are gone.
COMMANDS.ledger = function(_player: Player, args: { string }): (boolean, string)
	local id = args[1] and string.upper(args[1])
	if not id then
		local ids = {}
		for _, definition in Events do
			if definition.Unique then
				table.insert(ids, definition.Unique.LedgerId)
			end
		end
		table.sort(ids)
		if #ids == 0 then
			return false, "no event grants a unique"
		end
		return false, "usage: /ledger <ID> -- " .. table.concat(ids, ", ")
	end

	local cap = 0
	for _, definition in Events do
		if definition.Unique and definition.Unique.LedgerId == id then
			cap = definition.Unique.Cap
		end
	end
	if cap == 0 then
		return false, `no event grants '{id}'`
	end

	local summary = LedgerSystem.summary(id, cap)
	if not summary.ok then
		return false, `ledger unavailable ({summary.err}) -- no unique can be granted here`
	end

	local lines = { `{summary.value.Issued} of {summary.value.Cap} claimed` }
	for _, claim in summary.value.Claims do
		table.insert(lines, `#{claim.Number} {claim.Name}`)
	end
	return true, table.concat(lines, " | ")
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

function DebugSystem.init(
	fateSystem: any,
	expeditionSystem: any,
	eventSystem: any,
	ledgerSystem: any
): ()
	FateSystem = fateSystem
	ExpeditionSystem = expeditionSystem
	EventSystem = eventSystem
	LedgerSystem = ledgerSystem

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
