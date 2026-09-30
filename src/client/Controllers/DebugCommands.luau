--!strict
-- Developer commands, client half. Testing tooling, not a feature.
--
-- WHAT RUNS WHERE is decided by the registry (Content/DevCommands), one entry
-- per command. A command lives on whichever side already has authority over
-- what it changes:
--   CLIENT -- this file's CLIENT table: your own character's movement and
--             CFrame (Roblox gives the client ownership of its own rig), your
--             camera, and what this client draws (overlays, props, clock)
--   SERVER -- Systems/DebugSystem: rolls, entry, loot, health, events. The
--             client only ASKS; the server checks who is asking.
--
-- Every registry entry is registered as a TextChatCommand, so Roblox's chat
-- autocompletes the names; the dev panel (UI/DevPanel) runs the same entries
-- through DebugCommands.run and autocompletes argument values too
-- (Core/DevCore). That requires TextChatService (the modern chat); a place on
-- the legacy chat still gets the panel, and a warning.

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")
local TextChatService = game:GetService("TextChatService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local BossPreviews = require(Root.Content.BossPreviews)
local Constants = require(Root.Core.Constants)
local DevCommands = require(Root.Content.DevCommands)
local DevCore = require(Root.Core.DevCore)
local Events = require(Root.Content.Events)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)

local DebugCommands = {}

local player = Players.LocalPlayer

-- === output ==========================================================
-- Replies go to the Output window, the chat AND every listener (the dev
-- panel's log). Output alone was invisible in a running client, so a command
-- that failed and one that was never registered looked identical.
local listeners: { (string, boolean) -> () } = {}

--- The panel subscribes here to show every reply, client or server.
function DebugCommands.onOutput(fn: (string, boolean) -> ()): ()
	table.insert(listeners, fn)
end

local function emit(text: string, ok: boolean)
	print(`[cmd] {text}`)
	local channels = TextChatService:FindFirstChild("TextChannels")
	local general = channels and channels:FindFirstChild("RBXGeneral")
	if general and general:IsA("TextChannel") then
		pcall(function()
			general:DisplaySystemMessage(`[cmd] {text}`)
		end)
	end
	for _, fn in listeners do
		task.spawn(fn, text, ok)
	end
end

local function say(text: string)
	emit(text, true)
end

local function fail(text: string)
	emit(text, false)
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

-- === the current map =================================================
-- ChunkLoader builds Workspace.ExpeditionStage.<stage> (WorldId, Seed) with a
-- folder per chunk (Index, ChunkId, Role, Centre, Blockout).

local function currentStage(): Instance?
	local stages = Workspace:FindFirstChild(Constants.NAMES.EXPEDITION_STAGE)
	if not stages then
		return nil
	end
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local best, bestD = nil, math.huge
	for _, stage in stages:GetChildren() do
		if stage:GetAttribute("Seed") ~= nil then
			local d = 0
			if root and root:IsA("BasePart") and stage:IsA("Model") then
				d = (stage:GetPivot().Position - root.Position).Magnitude
			end
			if d < bestD then
				best, bestD = stage, d
			end
		end
	end
	return best
end

type ChunkInfo = {
	Index: number,
	Id: string,
	Role: string,
	Centre: Vector3,
	Blockout: boolean,
}

local function currentChunks(): { ChunkInfo }
	local out: { ChunkInfo } = {}
	local stage = currentStage()
	if not stage then
		return out
	end
	for _, folder in stage:GetDescendants() do
		local id = folder:GetAttribute("ChunkId")
		local centre = folder:GetAttribute("Centre")
		if type(id) == "string" and typeof(centre) == "Vector3" then
			local index = folder:GetAttribute("Index")
			table.insert(out, {
				Index = if type(index) == "number"
					then index
					else tonumber(string.match(folder.Name, "^(%d+)_")) or 0,
				Id = id,
				Role = tostring(folder:GetAttribute("Role") or "?"),
				Centre = centre,
				Blockout = folder:GetAttribute("Blockout") == true,
			})
		end
	end
	table.sort(out, function(a, b)
		return a.Index < b.Index
	end)
	return out
end

-- === noclip ============================================================

local noclip: RBXScriptConnection? = nil

local function toggleNoclip()
	if noclip then
		noclip:Disconnect()
		noclip = nil
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if root and root:IsA("BasePart") then
			root.CanCollide = true
		end
		say("noclip OFF")
		return
	end
	-- Stepped runs before physics: the humanoid re-enables collision on its
	-- parts, so it has to be switched off every frame.
	noclip = RunService.Stepped:Connect(function()
		local character = player.Character
		if not character then
			return
		end
		for _, part in character:GetDescendants() do
			if part:IsA("BasePart") and part.CanCollide then
				part.CanCollide = false
			end
		end
	end)
	say("noclip ON")
end

-- === chunk overlay ======================================================

local overlay: Folder? = nil

local ROLE_COLOURS: { [string]: Color3 } = {
	ENTRY = Color3.fromRGB(120, 220, 140),
	PATH = Color3.fromRGB(150, 180, 230),
	COMBAT = Color3.fromRGB(240, 120, 100),
	MINIBOSS = Color3.fromRGB(240, 170, 80),
	BOSS = Color3.fromRGB(230, 80, 200),
	SIDE = Color3.fromRGB(210, 210, 120),
	CAP = Color3.fromRGB(160, 160, 160),
	BACKDROP = Color3.fromRGB(110, 110, 130),
}
local BLOCKOUT_COLOUR = Color3.fromRGB(255, 60, 60)

local function setOverlay(on: boolean)
	if overlay then
		overlay:Destroy()
		overlay = nil
	end
	if not on then
		say("chunk overlay OFF")
		return
	end
	local list = currentChunks()
	if #list == 0 then
		fail("no map loaded -- /enter first")
		return
	end
	local Chunks = require(Root.Content.Chunks) :: any
	local holder = Instance.new("Folder")
	holder.Name = "LuckboundChunkOverlay"
	for _, c in list do
		local def = Chunks[c.Id]
		local colour = if c.Blockout
			then BLOCKOUT_COLOUR
			else (ROLE_COLOURS[c.Role] or Color3.new(1, 1, 1))
		local anchor = Instance.new("Part")
		anchor.Anchored = true
		anchor.CanCollide = false
		anchor.CanQuery = false
		anchor.CanTouch = false
		anchor.Transparency = 1
		anchor.Size = Vector3.new((def and def.SizeX) or 256, 4, (def and def.SizeZ) or 256)
		anchor.CFrame = CFrame.new(c.Centre)
		anchor.Parent = holder
		local box = Instance.new("SelectionBox")
		box.Adornee = anchor
		box.Color3 = colour
		box.LineThickness = 0.6
		box.Parent = anchor
		local tag = Instance.new("BillboardGui")
		tag.Adornee = anchor
		tag.AlwaysOnTop = true
		tag.Size = UDim2.fromOffset(260, 44)
		tag.StudsOffsetWorldSpace = Vector3.new(0, GameConfig.Debug.ChunkLabelHeight, 0)
		tag.Parent = anchor
		local text = Instance.new("TextLabel")
		text.BackgroundTransparency = 1
		text.Size = UDim2.fromScale(1, 1)
		text.Font = Enum.Font.GothamBold
		text.TextScaled = true
		text.TextStrokeTransparency = 0.3
		text.TextColor3 = colour
		text.Text = `#{c.Index} {c.Id}\n{c.Role}{if c.Blockout then " - BLOCKOUT" else ""}`
		text.Parent = tag
	end
	holder.Parent = Workspace
	overlay = holder
	say(`chunk overlay ON ({#list} chunks; red = blockout)`)
end

-- === stats overlay ======================================================

local statsGui: ScreenGui? = nil
local statsConn: RBXScriptConnection? = nil

local function setStats(on: boolean)
	if statsConn then
		statsConn:Disconnect()
		statsConn = nil
	end
	if statsGui then
		statsGui:Destroy()
		statsGui = nil
	end
	if not on then
		say("stats OFF")
		return
	end
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundStats"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 60
	local label = Instance.new("TextLabel")
	label.BackgroundColor3 = Color3.new(0, 0, 0)
	label.BackgroundTransparency = 0.45
	label.Position = UDim2.new(0.5, -160, 0, 6)
	label.Size = UDim2.fromOffset(320, 24)
	label.Font = Enum.Font.Code
	label.TextSize = 14
	label.TextColor3 = Color3.new(1, 1, 1)
	label.Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	statsGui = gui
	local frames, since = 0, os.clock()
	statsConn = RunService.RenderStepped:Connect(function()
		frames += 1
		local now = os.clock()
		if now - since >= 0.5 then
			local fps = frames / (now - since)
			frames, since = 0, now
			label.Text = string.format(
				"%d fps  %d ms  %d MB  %d inst",
				fps,
				math.floor(player:GetNetworkPing() * 2000),
				math.floor(Stats:GetTotalMemoryUsageMb()),
				Stats.InstanceCount
			)
		end
	end)
	say("stats ON")
end

-- === props ==============================================================

local hiddenProps: Instance? = nil

local function setProps(on: boolean)
	if on then
		if hiddenProps then
			hiddenProps.Parent = Workspace
			hiddenProps = nil
			say("props shown")
		else
			say("props are already shown")
		end
		return
	end
	local folder = Workspace:FindFirstChild("LuckboundProps")
	if not folder then
		fail("no props drawn right now")
		return
	end
	folder.Parent = nil
	hiddenProps = folder
	say("props hidden (/props on brings them back)")
end

-- === argument sources (DevCore.SOURCES) ================================

local function sorted(t: { string }): { string }
	table.sort(t)
	return t
end

local SOURCES: { [string]: any } = {
	WORLDS = function()
		local ids = {}
		for id, world in Worlds do
			if world.EnabledInPhase <= GameConfig.CurrentPhase then
				table.insert(ids, id)
			end
		end
		return sorted(ids)
	end,
	EVENTS = function()
		local ids = {}
		for id in Events do
			table.insert(ids, id)
		end
		return sorted(ids)
	end,
	ATMOSPHERES = function()
		local ids = {}
		local ok, Atmospheres = pcall(require, Root.Content.Atmospheres)
		if ok then
			for _, set in Atmospheres :: any do
				for id in set.Profiles or {} do
					if not table.find(ids, id) then
						table.insert(ids, id)
					end
				end
			end
		end
		sorted(ids)
		table.insert(ids, 1, "RANDOM")
		table.insert(ids, 1, "BASE")
		return ids
	end,
	BOSSES = function()
		local ids = {}
		for id in BossPreviews do
			table.insert(ids, id)
		end
		return sorted(ids)
	end,
	KEYS = function()
		local ids = {}
		for _, world in Worlds do
			local key = world.Loot and world.Loot.VaultKey
			if key then
				table.insert(ids, key.Id)
			end
		end
		return sorted(ids)
	end,
	LEDGERS = function()
		local ids = {}
		for _, def in Events do
			if def.Unique then
				table.insert(ids, def.Unique.LedgerId)
			end
		end
		return sorted(ids)
	end,
	DESTINATIONS = function()
		local ids = {}
		for alias in DESTINATIONS do
			table.insert(ids, alias)
		end
		return sorted(ids)
	end,
	CHUNKS = function()
		local ids = {}
		for _, c in currentChunks() do
			table.insert(ids, `{c.Index}`)
		end
		return ids
	end,
}

--- For the panel and autocomplete: source name -> list (or function).
function DebugCommands.sources(): { [string]: any }
	return SOURCES
end

--- A chunk index as the panel's picker shows it: "#3 ES_TEMPLE_GATE_A (COMBAT)".
function DebugCommands.describeChunk(index: string): string
	for _, c in currentChunks() do
		if `{c.Index}` == index then
			return `#{c.Index} {c.Id} ({c.Role})`
		end
	end
	return index
end

-- === CLIENT commands (registry Side = "CLIENT") ========================

local function onOff(v: string?): boolean
	return v == nil or string.lower(v) ~= "off"
end

local panelToggle: (() -> ())? = nil
local panelClear: (() -> ())? = nil

--- The panel hands in its toggle and clear so /panel and /clear reach it.
function DebugCommands.bindPanel(toggle: () -> (), clear: () -> ()): ()
	panelToggle, panelClear = toggle, clear
end

local CLIENT: { [string]: ({ string }) -> () } = {}

CLIENT.fly = function()
	toggleFly()
end
CLIENT.noclip = function()
	toggleNoclip()
end
-- Movement testing. The controller is required here, not at module scope,
-- so developer tooling never becomes load-bearing for movement.
local function locomotion(): any
	return require(script.Parent.LocomotionController)
end
CLIENT.moveprofile = function(args)
	local choice = args[1] and string.lower(args[1])
	if choice == nil then
		say(`movement profile is {locomotion().profile()}`)
		return
	end
	if choice == "auto" then
		locomotion().forceProfile(nil)
		say("movement profile follows where you stand (hub / expedition stage)")
	elseif choice == "hub" or choice == "expedition" then
		locomotion().forceProfile(string.upper(choice))
		say(`movement profile forced to {string.upper(choice)} -- /moveprofile auto to undo`)
	else
		fail("usage: /moveprofile <hub|expedition|auto>")
	end
end
CLIENT.stamina = function(args)
	local state = locomotion().get()
	if not args[1] then
		say(`stamina {math.floor(state.Stamina + 0.5)}`)
		return
	end
	local value = tonumber(args[1])
	if not value then
		fail(`'{args[1]}' is not a number`)
		return
	end
	locomotion().setStamina(math.clamp(value, 0, 100) / 100)
	say(`stamina set to {math.clamp(value, 0, 100)}%`)
end
CLIENT.animslot = function(args)
	local animator = require(script.Parent.CharacterAnimator)
	if not args[1] then
		for _, line in animator.describeSlots() do
			say(line)
		end
		return
	end
	-- A slot alone describes that slot; clearing needs an explicit "".
	if not args[2] then
		local wanted = string.lower(args[1])
		for _, line in animator.describeSlots() do
			if string.lower(string.match(line, "^[^:]+") or "") == wanted then
				say(line)
				return
			end
		end
		fail(`unknown slot '{args[1]}' (/animslot lists them all)`)
		return
	end
	local id = args[2]
	if id == '""' then
		id = ""
	end
	local ok, message = animator.overrideSlot(args[1], id)
	if ok then
		say(message)
	else
		fail(message)
	end
end
CLIENT.speed = function(args)
	setSpeed(args[1])
end
CLIENT.tp = function(args)
	teleport(args[1])
end
CLIENT.where = function()
	local character = player.Character
	if not character then
		fail("no character yet")
		return
	end
	local pivot = character:GetPivot()
	say(string.format("%.0f, %.0f, %.0f", pivot.X, pivot.Y, pivot.Z))
end
CLIENT.worlds = function()
	local ids = {}
	for id, world in Worlds do
		if world.EnabledInPhase <= GameConfig.CurrentPhase then
			table.insert(ids, `{id} [{world.Rarity}]`)
		end
	end
	say(table.concat(sorted(ids), ", "))
end
CLIENT.seed = function()
	local stage = currentStage()
	if not stage then
		fail("no map loaded")
		return
	end
	local seed = stage:GetAttribute("Seed")
	say(`{stage:GetAttribute("WorldId")} seed {seed} -- /enter {seed} replays it`)
end
CLIENT.chunks = function(args)
	setOverlay(if args[1] then onOff(args[1]) else overlay == nil)
end
CLIENT.chunklist = function()
	local list = currentChunks()
	if #list == 0 then
		fail("no map loaded")
		return
	end
	local roles: { [string]: number } = {}
	local lines = {}
	for _, c in list do
		roles[c.Role] = (roles[c.Role] or 0) + 1
		table.insert(lines, `#{c.Index} {c.Id}{if c.Blockout then " [BLOCKOUT]" else ""}`)
	end
	local counts = {}
	for role, n in roles do
		table.insert(counts, `{role} {n}`)
	end
	say(`{#list} chunks ({table.concat(sorted(counts), ", ")}): {table.concat(lines, " | ")}`)
end
CLIENT.chunktp = function(args)
	local want = args[1]
	for _, c in currentChunks() do
		if `{c.Index}` == want or string.upper(c.Id) == string.upper(want) then
			local character = player.Character
			if not character then
				fail("no character yet")
				return
			end
			character:PivotTo(CFrame.new(c.Centre + Vector3.new(0, 20, 0)))
			say(`teleported to #{c.Index} {c.Id} ({c.Role})`)
			return
		end
	end
	fail(`no chunk '{want}' on this map -- /chunklist`)
end
CLIENT.tint = function(args)
	say(require(script.Parent.AtmosphereEffects).setTint(onOff(args[1])))
end
CLIENT.props = function(args)
	setProps(onOff(args[1]))
end
CLIENT.clock = function(args)
	local hour = tonumber(args[1])
	if not hour then
		say(`clock is {string.format("%.1f", Lighting.ClockTime)}`)
		return
	end
	Lighting.ClockTime = math.clamp(hour, 0, 24)
	say(`clock {Lighting.ClockTime} (local only; a sky system may set it back)`)
end
CLIENT.stats = function(args)
	setStats(if args[1] then onOff(args[1]) else statsGui == nil)
end
CLIENT.assets = function()
	local list = currentChunks()
	if #list == 0 then
		fail("no map loaded")
		return
	end
	local missing = {}
	for _, c in list do
		if c.Blockout then
			table.insert(missing, `#{c.Index} {c.Id}`)
		end
	end
	if #missing == 0 then
		say(`all {#list} chunks drew their meshes`)
	else
		fail(
			`{#missing}/{#list} chunks are BLOCKOUT (no uploaded AssetId in AssetManifest): `
				.. table.concat(missing, ", ")
		)
	end
end
CLIENT.panel = function()
	if panelToggle then
		panelToggle()
	else
		fail("the dev panel is not loaded")
	end
end
CLIENT.clear = function()
	if panelClear then
		panelClear()
	end
end
CLIENT.help = function()
	local byCat: { [string]: { string } } = {}
	for _, c in DevCommands.Commands do
		byCat[c.Category] = byCat[c.Category] or {}
		table.insert(byCat[c.Category], "/" .. c.Name)
	end
	for _, cat in DevCommands.Categories do
		if byCat[cat.Id] then
			say(`{cat.Label}: {table.concat(byCat[cat.Id], " ")}`)
		end
	end
	say(`{GameConfig.Debug.PanelKey} or the DEV button opens the panel`)
end

DebugCommands.CLIENT = CLIENT

-- === running a command ==================================================

local byName = DevCore.index(DevCommands)

--- Runs a registry command by name, from chat or the panel. Required
--- arguments and literal choices are checked here, so a typo is explained
--- before anything is sent.
function DebugCommands.run(name: string, args: { string }): ()
	local command = byName[string.lower(name)]
	if not command then
		fail(`unknown command /{name} -- /help`)
		return
	end
	local problem = DevCore.check(command, args, SOURCES)
	if problem then
		fail(problem)
		return
	end
	if command.Side == "CLIENT" then
		local handler = CLIENT[command.Name]
		if not handler then
			fail(`/{command.Name} has no client handler`)
			return
		end
		local ok, err = pcall(handler, args)
		if not ok then
			fail(`/{command.Name} errored: {err}`)
		end
	else
		Net.get("Debug_Command"):FireServer(command.Name, args)
	end
end

--- Runs a whole typed line ("/roll SKY_CITADEL test").
function DebugCommands.runLine(line: string): ()
	local name, args = DevCore.parse(line)
	if name then
		DebugCommands.run(name, args)
	end
end

function DebugCommands.init(): ()
	if not GameConfig.Debug.AllowCommands then
		return
	end

	-- a CLIENT entry with no handler is a button that does nothing
	for _, c in DevCommands.Commands do
		if c.Side == "CLIENT" and not CLIENT[c.Name] then
			warn(`[DebugCommands] registry lists CLIENT /{c.Name} but there is no handler`)
		end
	end

	if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
		local folder = TextChatService:WaitForChild("TextChatCommands")
		for _, c in DevCommands.Commands do
			local command = Instance.new("TextChatCommand")
			command.Name = `Luckbound{c.Name}`
			command.PrimaryAlias = `/{c.Name}`
			command.AutocompleteVisible = true
			command.Parent = folder
			command.Triggered:Connect(function(_source, text)
				local _, args = DevCore.parse(text)
				DebugCommands.run(c.Name, args)
			end)
		end
	else
		warn(
			"[DebugCommands] this place uses the legacy chat, so slash commands cannot be "
				.. "registered -- the dev panel still works. Set TextChatService.ChatVersion "
				.. "to TextChatService to type them in chat."
		)
	end

	Net.get("Debug_Reply").OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and type(payload.Text) == "string" then
			emit(payload.Text, payload.Ok == true)
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

	say(`developer commands ready -- /help, or {GameConfig.Debug.PanelKey} for the panel`)
end

DebugCommands.DESTINATIONS = DESTINATIONS

return DebugCommands
