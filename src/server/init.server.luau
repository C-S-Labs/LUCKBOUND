--!strict
-- The only Script on the server. Build spec §1.2 -- this order is fixed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")

local ExpeditionCore = require(Root.Core.ExpeditionCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Schema = require(Root.Util.Schema)
local Worlds = require(Root.Content.Worlds)
local AssetManifest = require(Root.Content.AssetManifest)
local Chunks = require(Root.Content.Chunks)
local Crossroads = require(Root.Content.Hub.Crossroads)
local Menu = require(Root.Content.Hub.Menu)
local Cinematics = require(Root.Content.Hub.Cinematics)
local Codes = require(Root.Content.Codes)

local Systems = script.Systems
local SaveSystem = require(Systems.SaveSystem)
local ProgressionSystem = require(Systems.ProgressionSystem)
local FateSystem = require(Systems.FateSystem)
local EventSystem = require(Systems.EventSystem)
local ExpeditionSystem = require(Systems.ExpeditionSystem)
local DebugSystem = require(Systems.DebugSystem)
local HubBuilder = require(Systems.HubBuilder)
local HubUISystem = require(Systems.HubUISystem)

-- Boot progress is printed at every stage. A server that stops partway now
-- names the step it stopped on, instead of going silent and leaving you to
-- guess -- which is what a yielding call in a system's init() looks like.
local TOTAL_STEPS = 12
local stepNumber = 0
local function step(name: string)
	stepNumber += 1
	print(`[LUCKBOUND] boot {stepNumber}/{TOTAL_STEPS}: {name}`)
end

-- 1. Fail fast on malformed content, before any player can arrive.
step("validating content")
Schema.validateAll(Worlds, GameConfig, Crossroads, Chunks, AssetManifest, Menu, Codes, Cinematics)

do
	local uploaded, placeholder = AssetManifest.summary()
	print(
		`[LUCKBOUND] assets: {uploaded} uploaded, {placeholder} placeholder (placeholders render as primitives)`
	)
end

-- The gap between "rollable" and "enterable", named out loud on every boot.
-- Sky Citadel is in the roll pool at 7% with no map of either kind, so a player who
-- rolls it reaches the Gate and is turned away. That is handled gracefully by
-- ExpeditionCore rather than crashing -- but it is debt, and debt that prints
-- itself at boot cannot quietly grow.
do
	local missing = ExpeditionCore.worldsWithoutMaps(Worlds, Chunks, GameConfig.CurrentPhase)
	if #missing > 0 then
		warn(
			`[LUCKBOUND] {#missing} rollable world(s) have no map and cannot be entered: `
				.. table.concat(missing, ", ")
		)
	end
end

-- 2. Remotes must exist before any system connects to them.
step("building remotes")
Net.buildRemotes()

-- 3-7. Systems, dependencies passed in. No system requires another at module
-- scope; circular requires are a hard error.
step("SaveSystem")
SaveSystem.init()
step("ProgressionSystem")
ProgressionSystem.init(SaveSystem)
step("EventSystem")
EventSystem.init()
step("FateSystem")
FateSystem.init(SaveSystem, ProgressionSystem, EventSystem)
-- ExpeditionSystem takes the slot build spec §1.2 reserved for WorldSystem.
-- It needs no reference to FateSystem: a player's destination is simply their
-- last roll, read out of the profile, so the two systems share data rather
-- than pointers and the boot order stays a straight line.
step("ExpeditionSystem")
ExpeditionSystem.init(SaveSystem, ProgressionSystem)
-- The hub menu's server half: travel, codes and settings. It takes
-- ExpeditionSystem only to ask one question -- "is this player in the hub?"
-- -- which is also the menu's entire visibility rule.
step("HubUISystem")
HubUISystem.init(SaveSystem, ProgressionSystem, ExpeditionSystem)
-- 8. Developer commands. Last of the systems on purpose: nothing above may
-- depend on it, so deleting it before launch breaks nothing.
step("DebugSystem")
DebugSystem.init(FateSystem, ExpeditionSystem)

-- 9. Hub. Generated from Content/Hub/Crossroads data, and skipped entirely if
-- Workspace already contains a hand-built Crossroads -- authored geometry
-- always wins over generated blockout.
step("building the Crossroads")
HubBuilder.build()
-- The Gate's prompt is bound AFTER the hub exists, because it attaches to
-- geometry HubBuilder creates.
ExpeditionSystem.bindGatePrompt()

-- 11. Player binding LAST, so nobody can arrive before systems are ready.
step("binding players")
--- The hub is 1150 studs across, so Roblox's default 16 studs/second would
--- make every trip a chore. GameConfig.Scale.WalkSpeed is the other half of
--- the traversal budget documented there -- changing hub size without changing
--- this breaks the budget.
local function applyMovement(character: Model)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if humanoid and humanoid:IsA("Humanoid") then
		humanoid.WalkSpeed = GameConfig.Scale.WalkSpeed
	end
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(applyMovement)
	if player.Character then
		task.spawn(applyMovement, player.Character)
	end

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

print(
	`[LUCKBOUND] server ready -- phase {GameConfig.CurrentPhase}, true RNG, `
		.. `{#GameConfig.Fate.OnboardingSequence}-roll onboarding, expeditions `
		.. (if GameConfig.Expedition.Enabled then "ENABLED" else "disabled")
)
