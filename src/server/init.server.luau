--!strict
-- The only Script on the server. Build spec §1.2 -- this order is fixed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")

local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Schema = require(Root.Util.Schema)
local Worlds = require(Root.Content.Worlds)
local Crossroads = require(Root.Content.Hub.Crossroads)

local Systems = script.Systems
local SaveSystem = require(Systems.SaveSystem)
local ProgressionSystem = require(Systems.ProgressionSystem)
local FateSystem = require(Systems.FateSystem)
local EventSystem = require(Systems.EventSystem)
local HubBuilder = require(Systems.HubBuilder)

-- 1. Fail fast on malformed content, before any player can arrive.
Schema.validateAll(Worlds, GameConfig, Crossroads)

-- 2. Remotes must exist before any system connects to them.
Net.buildRemotes()

-- 3-7. Systems, dependencies passed in. No system requires another at module
-- scope; circular requires are a hard error.
SaveSystem.init()
ProgressionSystem.init(SaveSystem)
EventSystem.init()
FateSystem.init(SaveSystem, ProgressionSystem, EventSystem)

-- 8. Hub. Generated from Content/Hub/Crossroads data, and skipped entirely if
-- Workspace already contains a hand-built Crossroads -- authored geometry
-- always wins over generated blockout.
HubBuilder.build()

-- 9. Player binding LAST, so nobody can arrive before systems are ready.
local function onPlayerAdded(player: Player)
	SaveSystem.load(player)

	local snapshot = ProgressionSystem.snapshot(player)
	if snapshot then
		Net.get("Profile_Loaded"):FireClient(player, snapshot)
	end

	-- Hand the joining player the current state of the world, including any
	-- event already in progress. Build spec §4.1.
	EventSystem.syncTo(player)
end

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(function(player)
	SaveSystem.release(player)
end)

-- Anyone who joined while the above was still wiring up.
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end

print(`[LUCKBOUND] server ready -- phase {GameConfig.CurrentPhase}, true RNG, {#GameConfig.Fate.OnboardingSequence}-roll onboarding`)
