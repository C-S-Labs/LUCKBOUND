--!strict
-- The roll. Build spec §3 and T-111.
--
-- TRUE RNG. The result is an honest weighted draw and nothing about the player
-- tilts it. The only exception is the scripted onboarding sequence, which is
-- explicit, finite, and visible to the player as a tutorial.
--
-- This module owns plumbing and guards. FateCore owns the decision.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local FateCore = require(Root.Core.FateCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)

local FateSystem = {}

local SaveSystem
local ProgressionSystem
local EventSystem

-- Server-owned randomness. Never math.random: this instance is the single
-- auditable source for every roll on this server.
local rng = Random.new()
local function nextNumber(): number
	return rng:NextNumber()
end

local lastRollAt: { [number]: number } = {}

local function rollAnchor(): BasePart?
	local crossroads = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	local engine = crossroads and crossroads:FindFirstChild(Constants.NAMES.FATE_ENGINE)
	local anchor = engine and engine:FindFirstChild(Constants.NAMES.ROLL_ANCHOR)
	return if anchor and anchor:IsA("BasePart") then anchor else nil
end

--- Returns true if the player may roll right now. Failures are silent by
--- design (build spec §3.4.3): telling a client where the boundary is tells
--- an exploiter where the boundary is.
local function mayRoll(player: Player): boolean
	local now = os.clock()
	local last = lastRollAt[player.UserId]
	if last and now - last < GameConfig.Fate.RollCooldownSeconds then
		return false
	end

	local anchor = rollAnchor()
	if anchor then
		local character = player.Character
		local hrp = character and character:FindFirstChild("HumanoidRootPart")
		if not hrp or not hrp:IsA("BasePart") then
			return false
		end
		if (hrp.Position - anchor.Position).Magnitude > GameConfig.Fate.MaxRollDistance then
			return false
		end
	end

	return true
end

function FateSystem.requestRoll(player: Player, ...: any): ()
	-- The client sends nothing. A payload means a tampered client.
	if select("#", ...) > 0 then
		warn(`[FateSystem] {player.Name} sent arguments with Fate_RequestRoll; discarded`)
		return
	end

	if not mayRoll(player) then
		return
	end

	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	lastRollAt[player.UserId] = os.clock()

	local outcome = FateCore.roll(Worlds, profile, GameConfig, nextNumber)
	local world = Worlds[outcome.WorldId]
	local rarity = Constants.RARITY[world.Rarity]

	ProgressionSystem.recordRoll(player, world.Id, world.Rarity)

	if GameConfig.Debug.LogEveryRoll then
		print(
			string.format(
				"[Roll] %s (%d) -> %s [%s]%s",
				player.Name,
				player.UserId,
				world.Id,
				world.Rarity,
				if outcome.IsScripted then " (onboarding)" else ""
			)
		)
	end

	Net.get("Fate_RollResult"):FireClient(player, {
		WorldId = world.Id,
		Name = world.Name,
		Rarity = world.Rarity,
		Flavor = world.Flavor,
		IsTutorialRoll = outcome.IsScripted,
		RollNumber = outcome.RollNumber,
		RevealDuration = rarity.RevealDuration,
		ExpeditionSeconds = FateCore.expeditionDuration(world, profile, GameConfig),
	})

	-- A scripted onboarding roll is not an achievement and must never be
	-- announced: the whole server would see three identical "Mythic!" banners
	-- every time a new player joins, and the signal would mean nothing.
	if not outcome.IsScripted and rarity.Order >= Constants.ANNOUNCE_RARITY_ORDER then
		EventSystem.announce({
			Kind = "ROLL",
			Text = `{player.Name} rolled {world.Name}!`,
			Rarity = world.Rarity,
			PlayerName = player.Name,
		})
	end
end

function FateSystem.init(saveSystem: any, progressionSystem: any, eventSystem: any): ()
	SaveSystem = saveSystem
	ProgressionSystem = progressionSystem
	EventSystem = eventSystem

	Net.get("Fate_RequestRoll").OnServerEvent:Connect(function(player, ...)
		FateSystem.requestRoll(player, ...)
	end)

	Players.PlayerRemoving:Connect(function(player)
		lastRollAt[player.UserId] = nil
	end)
end

return FateSystem
