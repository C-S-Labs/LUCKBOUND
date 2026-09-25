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
local Fixtures = require(Root.Content.Fixtures)
local BossPreviews = require(Root.Content.BossPreviews)

local DebugSystem = {}

local FateSystem
local ExpeditionSystem
local EventSystem
local LedgerSystem
local LootSystem

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

--- /showboss <id> [height] -- put a boss PREVIEW (Content/BossPreviews) in the nearest boss arena, facing you,
--- playing its idle (or held pose). Aesthetic check only: no health, no AI. /clearboss removes it.
local function nearestArena(from: Vector3): Vector3?
	local best, bestD = nil, math.huge
	for _, inst in workspace:GetDescendants() do
		if inst:GetAttribute("Role") == "BOSS" then
			local c = inst:GetAttribute("Centre")
			if typeof(c) == "Vector3" and (c - from).Magnitude < bestD then
				best, bestD = c, (c - from).Magnitude
			end
		end
	end
	return best
end

local function groundBelow(p: Vector3, ignore: { Instance }): Vector3
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(p + Vector3.new(0, 300, 0), Vector3.new(0, -800, 0), params)
	return if hit then hit.Position else p
end

COMMANDS.clearboss = function(_player: Player, _args: { string }): (boolean, string)
	local old = workspace:FindFirstChild("BossPreview")
	if old then
		old:Destroy()
		return true, "boss preview removed"
	end
	return false, "no boss preview to remove"
end

COMMANDS.showboss = function(player: Player, args: { string }): (boolean, string)
	local id = args[1] and string.lower(args[1])
	local def = id and BossPreviews[id]
	if not def then
		local ids = {}
		for key in BossPreviews do
			table.insert(ids, key)
		end
		table.sort(ids)
		return false, "usage: /showboss <id> [height in studs] -- " .. table.concat(ids, ", ")
	end
	local lib = game:GetService("ServerStorage"):FindFirstChild("LuckboundBosses")
	local template = lib and lib:FindFirstChild(def.Model, true)
	if not template or not template:IsA("Model") then
		return false,
			`model '{def.Model}' not found in ServerStorage.LuckboundBosses (save it to assets/rbxm/bosses/{def.Model}.rbxmx)`
	end
	local root = player.Character
		and player.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then
		return false, "no character"
	end
	COMMANDS.clearboss(player, {})

	local model = (template :: Model):Clone()
	model.Name = "BossPreview"
	-- Size by target HEIGHT in studs, not a factor: FBX imports arrive at unpredictable scales.
	local tall = tonumber(args[2]) or def.Tall
	local _, bbox = model:GetBoundingBox()
	if tall and tall > 0 and bbox.Y > 1e-3 then
		model:ScaleTo(model:GetScale() * tall / bbox.Y)
	end
	local scale = tall
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			part.Anchored = true
			part.CanCollide = false
			-- colours come from the FBX's baked vertex colours; glow meshes (*Glow) glow
			if string.find(part.Name, "Glow") then
				part.Material = Enum.Material.Neon
				part.Color = def.GlowColor or Color3.fromRGB(110, 235, 255)
			else
				part.Material = Enum.Material.SmoothPlastic
				part.Color = Color3.new(1, 1, 1) -- white so the vertex colours show true
			end
		end
	end

	local arena = nearestArena(root.Position)
	local spot = if arena then arena else root.Position + root.CFrame.LookVector * 40
	local ignore: { Instance } = { model }
	if player.Character then
		table.insert(ignore, player.Character)
	end
	local ground = groundBelow(spot, ignore)
	local faceTo = Vector3.new(root.Position.X, ground.Y, root.Position.Z)
	local pivot = CFrame.lookAt(
		ground,
		if (faceTo - ground).Magnitude > 1 then faceTo else ground + Vector3.new(0, 0, -1)
	)
	local _, size = model:GetBoundingBox()
	local bottom = model:GetPivot().Position.Y
		- (select(1, model:GetBoundingBox()).Position.Y - size.Y / 2)
	model:PivotTo(pivot + Vector3.new(0, bottom + (def.Height or 0), 0))
	model.Parent = workspace

	local animId = def.Pose or def.Idle
	if animId and animId ~= "" then
		local controller = model:FindFirstChildWhichIsA("AnimationController", true)
			or model:FindFirstChildWhichIsA("Humanoid", true)
		if not controller then
			controller = Instance.new("AnimationController")
			controller.Parent = model
		end
		local animator = (controller :: Instance):FindFirstChildOfClass("Animator")
			or Instance.new("Animator")
		animator.Parent = controller
		local anim = Instance.new("Animation")
		anim.AnimationId = animId
		local track = (animator :: Animator):LoadAnimation(anim)
		track.Looped = def.Pose == nil
		track:Play()
		if def.Pose then
			task.delay(0.05, function()
				track:AdjustSpeed(0)
			end)
		end
	end
	local where = if arena then "in the boss arena" else "in front of you (no boss arena nearby)"
	local anim = if animId and animId ~= ""
		then "idle playing"
		else "rest pose (no Idle id set in BossPreviews)"
	return true, `{id} shown {where} {scale} studs tall; {anim}. /clearboss to remove`
end

--- /atmosphere <BASE | RANDOM | ID> -- force a scenario atmosphere (Content/
--- Atmospheres) on your current expedition at once, and on the next one.
--- RANDOM goes back to drawing from the seed. No argument lists the ids.
COMMANDS.atmosphere = function(player: Player, args: { string }): (boolean, string)
	return ExpeditionSystem.setAtmosphere(player, args[1] or "?")
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
--- skipping those would test a path the game does not have. `/enter <seed>`
--- rebuilds that exact map (every entry prints its seed) to compare a fix.
COMMANDS.enter = function(player: Player, args: { string }): (boolean, string)
	local seed = args[1] and tonumber(args[1])
	if args[1] and not seed then
		return false, "the seed must be a number"
	end
	return ExpeditionSystem.forceEnter(player, if seed then math.floor(seed) else nil)
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

-- === loot and vault keys (build spec §7.5) ============================
-- TEMPORARY testing tools (owner, 2026-09-23: "these will be removed later").
-- They change session state only -- nothing here edits content or config.

local function parseChance(arg: string?): (boolean, number?, string?)
	if arg == nil then
		return false, nil, nil
	end
	if string.lower(arg) == "reset" then
		return true, nil, nil
	end
	local n = tonumber(arg)
	if n == nil or n < 0 or n > 1 then
		return false, nil, "give a number from 0 to 1, or 'reset'"
	end
	return true, n, nil
end

--- /keychance <0-1 | reset> -- the vault key's drop chance, for this session.
COMMANDS.keychance = function(_player: Player, args: { string }): (boolean, string)
	local ok, n, err = parseChance(args[1])
	if not ok then
		return false, err or "usage: /keychance <0-1 | reset>"
	end
	LootSystem.setKeyChanceOverride(n)
	return true,
		if n
			then `vault key drop chance is now {n * 100}% (this session)`
			else "vault key drop chance back to content"
end

--- /vaultchance <0-1 | reset> -- how often the treasury (any piece holding a
--- vault) spawns, for maps built from now on.
COMMANDS.vaultchance = function(_player: Player, args: { string }): (boolean, string)
	local ok, n, err = parseChance(args[1])
	if not ok then
		return false, err or "usage: /vaultchance <0-1 | reset>"
	end
	local ids = {}
	for _, set in Fixtures do
		for chunkId, rows in set.Placements do
			for _, row in rows do
				if row.Kind == "VAULT" then
					ExpeditionSystem.setSpawnOverride(chunkId, n)
					table.insert(ids, chunkId)
					break
				end
			end
		end
	end
	table.sort(ids)
	return true,
		if n
			then `{table.concat(ids, ", ")} now spawns {n * 100}% of the time (next map on)`
			else `{table.concat(ids, ", ")} back to its own spawn chance`
end

--- /boss -- act as if you just defeated your map's boss (repeatable).
COMMANDS.boss = function(player: Player, _args: { string }): (boolean, string)
	return LootSystem.triggerBoss(player)
end

--- /givekey [KEY_ID] -- give yourself a vault key (the Sky Citadel one by default).
COMMANDS.givekey = function(player: Player, args: { string }): (boolean, string)
	local defs = LootSystem.keyDefinitions()
	local id = args[1] and string.upper(args[1]) or "SKY_CITADEL_VAULT_KEY"
	if not defs[id] then
		local ids = {}
		for key in defs do
			table.insert(ids, key)
		end
		table.sort(ids)
		return false, "usage: /givekey [KEY_ID] -- " .. table.concat(ids, ", ")
	end
	return LootSystem.giveKey(player, id)
end

--- /takekey -- remove every key you hold.
COMMANDS.takekey = function(player: Player, _args: { string }): (boolean, string)
	return LootSystem.takeKeys(player)
end

--- /keys -- the keys you hold, and any testing overrides in force.
COMMANDS.keys = function(player: Player, _args: { string }): (boolean, string)
	local held = {}
	for id, n in LootSystem.keysOf(player) do
		table.insert(held, `{id} x{n}`)
	end
	table.sort(held)
	local overrides = {}
	local kc = LootSystem.keyChanceOverride()
	if kc then
		table.insert(overrides, `key chance {kc * 100}%`)
	end
	for chunkId, n in ExpeditionSystem.spawnOverrides() do
		table.insert(overrides, `{chunkId} spawn {n * 100}%`)
	end
	return true,
		`keys: {if #held > 0 then table.concat(held, ", ") else "none"}`
			.. ` | overrides: {if #overrides > 0 then table.concat(overrides, ", ") else "none"}`
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
	ledgerSystem: any,
	lootSystem: any
): ()
	FateSystem = fateSystem
	ExpeditionSystem = expeditionSystem
	EventSystem = eventSystem
	LedgerSystem = ledgerSystem
	LootSystem = lootSystem

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
