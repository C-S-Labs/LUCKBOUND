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

--- Records the outcome, tells the player, and announces it if it deserves it.
--- The one place a roll result becomes real, so a forced developer roll and an
--- honest one cannot drift apart in what they write or what they send.
local function deliver(player: Player, profile: any, world: any, outcome: any, forced: boolean): ()
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
				if forced then " (FORCED)" elseif outcome.IsScripted then " (onboarding)" else ""
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
	--
	-- A FORCED roll is not an achievement either, for a stronger reason: a
	-- developer typing /roll ASTRAL_REACH must not fire a Fatebreak banner at
	-- everyone. Same rule, same line.
	if not outcome.IsScripted and not forced and rarity.Order >= Constants.ANNOUNCE_RARITY_ORDER then
		EventSystem.announce({
			Kind = "ROLL",
			Text = `{player.Name} rolled {world.Name}!`,
			Rarity = world.Rarity,
			PlayerName = player.Name,
		})
	end
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
	deliver(player, profile, Worlds[outcome.WorldId], outcome, false)
end

--- DEVELOPER TOOL. Forces a specific world, skipping the onboarding sequence,
--- the cooldown and the distance check -- all three exist to constrain
--- players, and this is not a player path.
---
--- It is inert unless GameConfig.Debug.AllowForcedRolls is true, and the
--- caller (DebugSystem) checks who is asking before it ever gets here. The
--- result still goes through `deliver`, so a forced roll is recorded, logged
--- and sent exactly like a real one -- which is the whole point: it has to
--- exercise the real path to be worth testing with.
function FateSystem.forceRoll(player: Player, worldId: string): (boolean, string)
	if not GameConfig.Debug.AllowForcedRolls then
		return false, "forced rolls are disabled (GameConfig.Debug.AllowForcedRolls)"
	end

	local world = Worlds[worldId]
	if not world then
		return false, `unknown world '{worldId}'`
	end

	local profile = SaveSystem.get(player)
	if not profile then
		return false, "no profile loaded yet"
	end

	deliver(player, profile, world, {
		WorldId = world.Id,
		RollNumber = (profile.TotalRolls or 0) + 1,
		IsScripted = false,
	}, true)

	return true, `forced {world.Name} [{world.Rarity}]`
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
