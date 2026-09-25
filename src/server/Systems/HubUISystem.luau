--!strict
-- THE SERVER SIDE OF THE HUB MENU: travel, codes and settings.
--
-- Everything the menu can ASK for lands here, and everything here follows the
-- same shape: the client names a thing by Id, this looks that Id up in
-- Content, and a pure Core decides whether it is allowed. No client-supplied
-- position, amount, cooldown or reward is ever read (CLAUDE.md rule 5) -- the
-- widest thing a client can say to this system is a destination Id and a
-- string of at most GameConfig.Codes.MaxLength characters.
--
-- WHY ONE SYSTEM FOR THREE PANELS. They share the rate limiter, the profile
-- handle and the "are you actually in the hub" test, and splitting them would
-- mean three copies of all three. When a panel grows a real economy -- the
-- shop will -- it gets its own system and this one keeps the menu's plumbing.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Codes = require(Root.Content.Codes)
local CodeCore = require(Root.Core.CodeCore)
local GameConfig = require(Root.Core.GameConfig)
local HubMenuCore = require(Root.Core.HubMenuCore)
local Menu = require(Root.Content.Hub.Menu)
local Net = require(Root.Core.Net)
local SettingsCore = require(Root.Core.SettingsCore)

local HubUISystem = {}

-- Dependencies are passed into init(). Build spec §1.2 / CLAUDE.md rule 7 --
-- no System requires another at module scope.
local SaveSystem: any
local ProgressionSystem: any
local ExpeditionSystem: any

type Limiter = { Count: number, WindowStartedAt: number }

local travelLimiter: { [number]: Limiter } = {}
local codeLimiter: { [number]: Limiter } = {}

--- A fixed-window rate limiter. Crude on purpose: it exists to make spam
--- pointless, not to be fair to the millisecond, and travel has no cooldown
--- for it to stand in for -- at 60 a minute a human pressing the button as
--- fast as they can never meets it.
local function allow(limiters: { [number]: Limiter }, userId: number, perMinute: number): boolean
	local now = os.clock()
	local state = limiters[userId]
	if not state or now - state.WindowStartedAt >= 60 then
		limiters[userId] = { Count = 1, WindowStartedAt = now }
		return true
	end
	if state.Count >= perMinute then
		return false
	end
	state.Count += 1
	return true
end

--- WHERE A TRAVELLER ACTUALLY LANDS.
---
--- Content states a landing point per district, but the authored Crossroads'
--- deck heights are a property of a mesh nobody here can measure -- the same
--- problem the mountain ring ran into (STATUS §4). So the point is treated as
--- a guess at the X/Z and a ray decides the Y: drop from ProbeHeight above
--- it, stand the player on whatever is hit.
---
--- If the ray hits nothing the content point is used unchanged and the server
--- warns by name. A silent fall through the world is the one outcome here
--- worth a log line.
local function groundedLanding(destination: any): Vector3
	local point = HubMenuCore.landingPoint(destination)
	local hub = GameConfig.HubMenu

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	-- Characters must not be landed on: arriving on someone's head is funny
	-- once and a bug report every time after.
	local filter: { Instance } = {}
	for _, player in Players:GetPlayers() do
		if player.Character then
			table.insert(filter, player.Character)
		end
	end
	params.FilterDescendantsInstances = filter
	params.IgnoreWater = true

	local from = Vector3.new(point.X, point.Y + hub.TeleportProbeHeight, point.Z)
	local hit = Workspace:Raycast(
		from,
		Vector3.new(0, -(hub.TeleportProbeHeight + hub.TeleportProbeDepth), 0),
		params
	)
	if not hit then
		warn(
			`[HubUI] no floor under landing for '{destination.Id}' -- using the content point as-is`
		)
		return point
	end

	return Vector3.new(point.X, hit.Position.Y + hub.TeleportLandingClearance, point.Z)
end

--- Moves the whole rig, and turns it to face the bearing the destination
--- names. PivotTo rather than setting the root part's CFrame, so no limb is
--- left behind for a frame -- the same reason ExpeditionSystem uses it.
local function placeCharacter(player: Player, position: Vector3, facingDegrees: number): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not character or not root or not root:IsA("BasePart") then
		return false
	end

	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid and humanoid.Health <= 0 then
		return false
	end

	-- Compass bearing to a Roblox yaw: GameConfig.HubLayout's mapping is
	-- NORTH = -Z, so a bearing of 0 looks along -Z, which is a yaw of 180.
	local yaw = math.rad(180 - facingDegrees);
	(character :: Model):PivotTo(CFrame.new(position) * CFrame.Angles(0, yaw, 0))
	return true
end

local function refuseTravel(player: Player, destinationId: any, reason: string): ()
	Net.get("Hub_TravelResult"):FireClient(player, {
		Ok = false,
		DestinationId = destinationId,
		Reason = reason,
	})
end

function HubUISystem.travel(player: Player, payload: any): ()
	if not allow(travelLimiter, player.UserId, GameConfig.HubMenu.TeleportRequestsPerMinute) then
		return -- silent, like the roll cooldown: a refused spammer is told nothing
	end

	local destinationId = if type(payload) == "table" then payload.DestinationId else nil
	if type(destinationId) ~= "string" then
		refuseTravel(player, nil, "Unknown destination.")
		return
	end

	local decision = HubMenuCore.canTravel(Menu, {
		DestinationId = destinationId,
		OnExpedition = ExpeditionSystem.isActive(player),
		-- The server does not track a "rolling" flag per player: the roll's
		-- own cooldown already refuses a second roll, and a player who travels
		-- mid-reveal simply sees their result land somewhere else. Named here
		-- so the field's absence is a decision rather than an omission.
		Rolling = false,
	}, GameConfig)

	if not decision.ok then
		refuseTravel(player, destinationId, decision.err)
		return
	end

	local destination = decision.value
	local landed = placeCharacter(player, groundedLanding(destination), destination.Facing)
	if not landed then
		refuseTravel(player, destinationId, "You cannot travel right now.")
		return
	end

	Net.get("Hub_TravelResult"):FireClient(player, {
		Ok = true,
		DestinationId = destination.Id,
		Reason = nil,
	})
end

function HubUISystem.redeem(player: Player, payload: any): ()
	local remote = Net.get("Code_Result")

	if not allow(codeLimiter, player.UserId, GameConfig.Codes.AttemptsPerMinute) then
		remote:FireClient(player, { Ok = false, Message = "Slow down a moment." })
		return
	end

	local profile = SaveSystem.get(player)
	if not profile then
		remote:FireClient(player, { Ok = false, Message = "Still loading your profile." })
		return
	end

	local input = if type(payload) == "table" then payload.Code else nil
	local decision = CodeCore.redeem(Codes, profile, input, os.time(), GameConfig)
	if not decision.ok then
		remote:FireClient(player, { Ok = false, Message = decision.err })
		return
	end

	local reward = decision.value
	CodeCore.record(profile, reward.Id, os.time())
	SaveSystem.markDirty(player)
	ProgressionSystem.grant(player, reward.Fate, "CodeRedeemed")

	remote:FireClient(player, {
		Ok = true,
		Message = reward.Message,
		Fate = reward.Fate,
		CodeId = reward.Id,
	})
end

function HubUISystem.updateSetting(player: Player, payload: any): ()
	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	local id = if type(payload) == "table" then payload.Id else nil
	local value = if type(payload) == "table" then payload.Value else nil

	local decision = SettingsCore.validate(id, value)
	if not decision.ok then
		-- Silent. A client sending an unknown setting is either an old build
		-- or someone poking at the remote; neither is worth a message back.
		return
	end

	if type(profile.Settings) ~= "table" then
		profile.Settings = SettingsCore.defaults()
	end
	profile.Settings[id] = decision.value
	SaveSystem.markDirty(player)
end

function HubUISystem.init(saveSystem: any, progressionSystem: any, expeditionSystem: any): ()
	SaveSystem = saveSystem
	ProgressionSystem = progressionSystem
	ExpeditionSystem = expeditionSystem

	Net.get("Hub_RequestTravel").OnServerEvent:Connect(function(player, payload)
		HubUISystem.travel(player, payload)
	end)

	Net.get("Code_Redeem").OnServerEvent:Connect(function(player, payload)
		HubUISystem.redeem(player, payload)
	end)

	Net.get("Settings_Update").OnServerEvent:Connect(function(player, payload)
		HubUISystem.updateSetting(player, payload)
	end)

	Players.PlayerRemoving:Connect(function(player)
		travelLimiter[player.UserId] = nil
		codeLimiter[player.UserId] = nil
	end)
end

return HubUISystem
