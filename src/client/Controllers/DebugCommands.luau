--!strict
-- Developer chat commands. Testing tooling, not a feature.
--
-- THE SPLIT, and it is not arbitrary: a command lives on whichever side
-- already has authority over what it changes.
--
--   HERE (client)  /fly /speed /tp /where /worlds /help
--       Your own character's velocity, walk speed and CFrame are already
--       yours -- Roblox gives the client network ownership of its own rig.
--       Routing these through the server would add a remote round trip to
--       change something the client is going to change anyway.
--
--   SERVER (DebugSystem)  /roll /enter /leave /atmosphere /event /endevents /ledger
--                         /keychance /vaultchance /boss /givekey /takekey /keys
--                         (the last six are temporary loot testing tools)
--       Roll results, expedition entry and Fate awards. The client must not
--       be trusted with any of them, debug build or not -- an exploiter does
--       not care that a flag was meant for testing.
--
-- Commands are registered as TextChatCommand instances, so Roblox's own chat
-- autocompletes them and they behave like every other slash command. That
-- requires TextChatService (the modern chat); a place still on the legacy
-- chat gets a clear warning instead of silent nothing.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextChatService = game:GetService("TextChatService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)

local DebugCommands = {}

local player = Players.LocalPlayer

-- === output ==========================================================
-- Replies go to BOTH the Output window and the chat, and the second half was
-- missing for a long time. Output is where the rest of the diagnostics live,
-- which is right in Studio -- but in a running client nobody can see it, so a
-- command that failed and a command that was never registered looked
-- identical: nothing happened. That is exactly how /event went unnoticed.
--
-- DisplaySystemMessage rather than SendAsync: this is the game answering the
-- player, not the player saying something to the server.
local function say(text: string)
	print(`[cmd] {text}`)

	local channels = TextChatService:FindFirstChild("TextChannels")
	local general = channels and channels:FindFirstChild("RBXGeneral")
	if general and general:IsA("TextChannel") then
		pcall(function()
			general:DisplaySystemMessage(`[cmd] {text}`)
		end)
	end
end

-- === flight ==========================================================

local flying = false
local flyConnection: RBXScriptConnection? = nil
local flyVelocity: LinearVelocity? = nil
local flyAttachment: Attachment? = nil

local function stopFlying()
	flying = false
	if flyConnection then
		flyConnection:Disconnect()
		flyConnection = nil
	end
	if flyVelocity then
		flyVelocity:Destroy()
		flyVelocity = nil
	end
	if flyAttachment then
		flyAttachment:Destroy()
		flyAttachment = nil
	end
end

local function startFlying(): boolean
	local character = player.Character
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not hrp or not hrp:IsA("BasePart") or not humanoid then
		return false
	end

	-- NO PlatformStand. The obvious way to stop the humanoid fighting the
	-- constraint is to set it, but PlatformStand makes the rig go limp and
	-- tip over -- you fly face-down. A LinearVelocity with an effectively
	-- infinite MaxForce already wins against gravity and against the
	-- humanoid's own movement force, so the humanoid can be left alone: it
	-- stays upright, keeps AutoRotate, and just plays its falling animation.

	local attachment = Instance.new("Attachment")
	attachment.Name = "LuckboundFlyAttachment"
	attachment.Parent = hrp
	flyAttachment = attachment

	-- LinearVelocity, not the deprecated BodyVelocity. A zero vector holds
	-- position against gravity, which is what makes hovering free.
	local velocity = Instance.new("LinearVelocity")
	velocity.Name = "LuckboundFly"
	velocity.Attachment0 = attachment
	velocity.MaxForce = math.huge
	velocity.RelativeTo = Enum.ActuatorRelativeTo.World
	velocity.VectorVelocity = Vector3.zero
	velocity.Parent = hrp
	flyVelocity = velocity

	flying = true

	flyConnection = RunService.RenderStepped:Connect(function()
		if not flying or not velocity.Parent then
			return
		end
		local camera = Workspace.CurrentCamera
		if not camera then
			return
		end

		-- Camera-relative, read from raw input. Humanoid.MoveDirection would be
		-- simpler and would work on touch, but it is zero while airborne on
		-- keyboard, which is the whole time you are flying.
		local move = Vector3.zero
		local cf = camera.CFrame
		if UserInputService:IsKeyDown(Enum.KeyCode.W) then
			move += cf.LookVector
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.S) then
			move -= cf.LookVector
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.D) then
			move += cf.RightVector
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.A) then
			move -= cf.RightVector
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.Space) then
			move += Vector3.yAxis
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) then
			move -= Vector3.yAxis
		end

		velocity.VectorVelocity = if move.Magnitude > 0
			then move.Unit * GameConfig.Debug.FlySpeed
			else Vector3.zero
	end)

	return true
end

local function toggleFly()
	if flying then
		stopFlying()
		say("flight OFF")
	elseif startFlying() then
		say(`flight ON -- WASD to move, Space up, Shift down, {GameConfig.Debug.FlySpeed} studs/s`)
	else
		say("cannot fly: no character yet")
	end
end

-- === walk speed ======================================================

local function setSpeed(raw: string?)
	local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		say("no character yet")
		return
	end

	if not raw then
		say(`walk speed is {humanoid.WalkSpeed} (default {GameConfig.Scale.WalkSpeed})`)
		return
	end

	local value = tonumber(raw)
	if not value then
		say(`'{raw}' is not a number`)
		return
	end

	-- Clamped rather than rejected: a typo should not require a rejoin.
	local clamped = math.clamp(value, GameConfig.Debug.MinWalkSpeed, GameConfig.Debug.MaxWalkSpeed)
	humanoid.WalkSpeed = clamped
	if clamped ~= value then
		say(`walk speed {clamped} (clamped from {value})`)
	else
		say(`walk speed {clamped}`)
	end
end

-- === teleport ========================================================

--- Short aliases for the hub anchors. Typing GLOBAL_OBSERVATORY to check a
--- sightline is the sort of friction that stops you checking it.
local DESTINATIONS: { [string]: string } = {
	engine = "FATE_ENGINE",
	fate = "FATE_ENGINE",
	gate = "EXPEDITION_GATE",
	hall = "HALL_OF_LEGENDS",
	archive = "DISCOVERY_ARCHIVE",
	training = "TRAINING_GROUNDS",
	spawn = "SPAWN",
}

local function teleport(where: string?)
	local character = player.Character
	if not character or not character.PrimaryPart then
		say("no character yet")
		return
	end

	if not where then
		local names = {}
		for alias in DESTINATIONS do
			table.insert(names, alias)
		end
		table.sort(names)
		say("usage: /tp <" .. table.concat(names, "|") .. ">")
		return
	end

	local key = DESTINATIONS[string.lower(where)]
	if not key then
		say(`unknown destination '{where}'`)
		return
	end

	-- The spawn is a ring now, so /tp spawn aims at its southern pad -- the
	-- one a player walking in from the processional would have used.
	local ring = GameConfig.HubLayout.SpawnRing
	local target = if key == "SPAWN"
		then Vector3.new(0, ring.Height, ring.Radius)
		else GameConfig.HubLayout.Anchors[key]
	if not target then
		say(`no anchor for '{key}'`)
		return
	end

	-- Arrive ABOVE the anchor and drop. Anchors are floor-level points, and
	-- materialising inside a platform is how the spawn bug started.
	character:PivotTo(CFrame.new(target + Vector3.new(0, 20, 0)))
	say(`teleported to {key}`)
end

-- === registration ====================================================

local function register(alias: string, description: string, handler: ({ string }) -> ())
	local command = Instance.new("TextChatCommand")
	command.Name = `Luckbound{alias}`
	command.PrimaryAlias = `/{alias}`
	command.AutocompleteVisible = true
	command.Parent = TextChatService:WaitForChild("TextChatCommands")

	command.Triggered:Connect(function(_source, text)
		local args = {}
		for word in string.gmatch(text, "%S+") do
			table.insert(args, word)
		end
		table.remove(args, 1) -- drop the alias itself
		handler(args)
	end)

	return description
end

local HELP: { string } = {}

--- Sends a server-side command. The client never decides the outcome; it only
--- asks, and DebugSystem checks who is asking.
local function remote(name: string, args: { string })
	Net.get("Debug_Command"):FireServer(name, args)
end

function DebugCommands.init(): ()
	if not GameConfig.Debug.AllowCommands then
		return
	end

	if TextChatService.ChatVersion ~= Enum.ChatVersion.TextChatService then
		warn(
			"[DebugCommands] this place uses the legacy chat, so slash commands "
				.. "cannot be registered. Set TextChatService.ChatVersion to "
				.. "TextChatService in Studio to enable /fly, /speed, /tp and /roll."
		)
		return
	end

	table.insert(
		HELP,
		register("fly", "toggle flight", function()
			toggleFly()
		end)
	)
	table.insert(
		HELP,
		register("speed", "/speed <n> -- set walk speed", function(args)
			setSpeed(args[1])
		end)
	)
	table.insert(
		HELP,
		register("tp", "/tp <place> -- jump to a hub anchor", function(args)
			teleport(args[1])
		end)
	)

	table.insert(
		HELP,
		register("roll", "/roll <WORLD_ID> -- force a destination", function(args)
			remote("roll", args)
		end)
	)
	table.insert(
		HELP,
		register(
			"enter",
			"/enter [seed] -- enter your destination from anywhere; a seed replays that map",
			function(args)
				remote("enter", args)
			end
		)
	)
	table.insert(
		HELP,
		register("leave", "end the current expedition", function()
			remote("leave", {})
		end)
	)

	-- THE EVENT COMMANDS. These existed on the server for two sessions and
	-- were never registered here, so typing /event sent a chat message and
	-- nothing else -- which looked exactly like "events do not trigger".
	-- A server command with no client alias is not a command.
	table.insert(
		HELP,
		register("event", "/event <ID> -- start a live event", function(args)
			remote("event", args)
		end)
	)
	table.insert(
		HELP,
		register(
			"atmosphere",
			"/atmosphere <ID|BASE|RANDOM> -- force a scenario atmosphere",
			function(args)
				remote("atmosphere", args)
			end
		)
	)
	table.insert(
		HELP,
		register("tint", "/tint <on|off> -- tint the map's meshes by the atmosphere", function(args)
			local on = string.lower(args[1] or "on") ~= "off"
			print("[cmd] " .. require(script.Parent.AtmosphereEffects).setTint(on))
		end)
	)
	table.insert(
		HELP,
		register("endevents", "stop every live event", function()
			remote("endevents", {})
		end)
	)
	table.insert(
		HELP,
		register("ledger", "/ledger <ID> -- how many uniques are left", function(args)
			remote("ledger", args)
		end)
	)

	-- LOOT AND VAULT KEYS (build spec §7.5) -- temporary testing tools.
	table.insert(
		HELP,
		register("keychance", "/keychance <0-1|reset> -- vault key drop chance", function(args)
			remote("keychance", args)
		end)
	)
	table.insert(
		HELP,
		register("vaultchance", "/vaultchance <0-1|reset> -- treasury spawn chance", function(args)
			remote("vaultchance", args)
		end)
	)
	table.insert(
		HELP,
		register("boss", "act as if you defeated this map's boss", function()
			remote("boss", {})
		end)
	)
	table.insert(
		HELP,
		register(
			"showboss",
			"/showboss <id> [scale] -- preview a boss in the nearest boss arena (idle)",
			function(args)
				remote("showboss", args)
			end
		)
	)
	table.insert(
		HELP,
		register("clearboss", "remove the boss preview", function()
			remote("clearboss", {})
		end)
	)
	table.insert(
		HELP,
		register("givekey", "/givekey [KEY_ID] -- give yourself a vault key", function(args)
			remote("givekey", args)
		end)
	)
	table.insert(
		HELP,
		register("takekey", "remove your vault keys", function()
			remote("takekey", {})
		end)
	)
	table.insert(
		HELP,
		register("keys", "your keys and any testing overrides", function()
			remote("keys", {})
		end)
	)

	table.insert(
		HELP,
		register("worlds", "list rollable world ids", function()
			local ids = {}
			for id, world in Worlds do
				if world.EnabledInPhase <= GameConfig.CurrentPhase then
					table.insert(ids, `{id} [{world.Rarity}]`)
				end
			end
			table.sort(ids)
			say(table.concat(ids, ", "))
		end)
	)

	table.insert(
		HELP,
		register("where", "print your position", function()
			local character = player.Character
			local pivot = character and character:GetPivot()
			if pivot then
				say(string.format("%.0f, %.0f, %.0f", pivot.X, pivot.Y, pivot.Z))
			end
		end)
	)

	register("help", "list commands", function()
		say("commands: " .. table.concat(HELP, "  |  "))
	end)

	Net.get("Debug_Reply").OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and type(payload.Text) == "string" then
			say((if payload.Ok then "" else "FAILED: ") .. payload.Text)
		end
	end)

	-- Flight constraints live on the character, so a respawn destroys them and
	-- would otherwise leave `flying` true with nothing driving it.
	player.CharacterAdded:Connect(function()
		if flying then
			stopFlying()
			say("flight OFF (respawned)")
		end
	end)

	say("developer commands ready -- /help")
end

DebugCommands.DESTINATIONS = DESTINATIONS

return DebugCommands
