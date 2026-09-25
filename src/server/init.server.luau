--!strict
-- The only Script on the server. Build spec §1.2 -- this order is fixed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")

local Constants = require(Root.Core.Constants)
local ExpeditionCore = require(Root.Core.ExpeditionCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Schema = require(Root.Util.Schema)
local Worlds = require(Root.Content.Worlds)
local AssetManifest = require(Root.Content.AssetManifest)
local Chunks = require(Root.Content.Chunks)
local Props = require(Root.Content.Props)
local Fixtures = require(Root.Content.Fixtures)
local LootPools = require(Root.Content.LootPools)
local Crossroads = require(Root.Content.Hub.Crossroads)
local Menu = require(Root.Content.Hub.Menu)
local Cinematics = require(Root.Content.Hub.Cinematics)
local Codes = require(Root.Content.Codes)
local Palettes = require(Root.Content.Hub.Palettes)
local Events = require(Root.Content.Events)
local Scenarios = require(Root.Content.Scenarios)

local Systems = script.Systems
local SaveSystem = require(Systems.SaveSystem)
local ProgressionSystem = require(Systems.ProgressionSystem)
local FateSystem = require(Systems.FateSystem)
local EventSystem = require(Systems.EventSystem)
local ExpeditionSystem = require(Systems.ExpeditionSystem)
local DebugSystem = require(Systems.DebugSystem)
local HubBuilder = require(Systems.HubBuilder)
local HubUISystem = require(Systems.HubUISystem)
local LedgerSystem = require(Systems.LedgerSystem)
local PartySystem = require(Systems.PartySystem)
local LootSystem = require(Systems.LootSystem)
local ChunkAutoKit = require(Systems.ChunkAutoKit)

-- Boot progress is printed at every stage. A server that stops partway now
-- names the step it stopped on, instead of going silent and leaving you to
-- guess -- which is what a yielding call in a system's init() looks like.
local TOTAL_STEPS = 15
local stepNumber = 0
local function step(name: string)
	stepNumber += 1
	print(`[LUCKBOUND] boot {stepNumber}/{TOTAL_STEPS}: {name}`)
end

-- 0. WHAT IS THIS SERVER FOR? Build spec §7.2. A reserved server with no
-- owner is an expedition instance a hub opened; everything else is a hub.
-- Stated on the shared root before anything else, so every client can read
-- it before it builds a single screen -- the loading screen and the menu
-- both behave differently on an expedition server.
local isExpeditionServer =
	ExpeditionCore.isExpeditionServer(game.PrivateServerId, game.PrivateServerOwnerId)
Root:SetAttribute(
	Constants.SERVER_KIND_ATTRIBUTE,
	if isExpeditionServer then Constants.SERVER_KIND_EXPEDITION else Constants.SERVER_KIND_HUB
)

-- 1a. Drop-in chunk kits: a world whose only kit is a delivered .rbxmx in
-- assets/rbxm/chunks/<world>/ is measured and registered here, BEFORE
-- validation, so a bad drop is caught by the same checks as a typed kit.
step("drop-in chunk kits")
ChunkAutoKit.load(Chunks, Worlds, AssetManifest)

-- 1. Fail fast on malformed content, before any player can arrive.
step("validating content")
Schema.validateAll({
	worlds = Worlds,
	config = GameConfig,
	hub = Crossroads,
	chunks = Chunks,
	manifest = AssetManifest,
	menu = Menu,
	codes = Codes,
	cinematics = Cinematics,
	palettes = Palettes,
	events = Events,
	scenarios = Scenarios,
	props = Props,
	fixtures = Fixtures,
	lootPools = LootPools,
})

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
-- The ledger before the events that claim from it. Global scarcity is the one
-- thing in the game that cannot be recovered if it is got wrong once, so the
-- system that guards it comes up before anything can ask it a question.
step("LedgerSystem")
LedgerSystem.init()
step("EventSystem")
EventSystem.init(LedgerSystem)
step("FateSystem")
FateSystem.init(SaveSystem, ProgressionSystem, EventSystem)
-- ExpeditionSystem takes the slot build spec §1.2 reserved for WorldSystem.
-- It needs no reference to FateSystem: a player's destination is simply their
-- last roll, read out of the profile, so the two systems share data rather
-- than pointers and the boot order stays a straight line.
-- Parties before expeditions: the portal asks PartySystem who is coming,
-- and PartySystem needs nothing from anyone.
step("PartySystem")
PartySystem.init()
-- Loot, fixtures and vault keys (build spec §7.5). Before ExpeditionSystem,
-- which hands it every map it builds.
step("LootSystem")
LootSystem.init(SaveSystem)
step("ExpeditionSystem")
ExpeditionSystem.init(SaveSystem, ProgressionSystem, PartySystem, LootSystem)
-- The hub menu's server half: travel, codes and settings. It takes
-- ExpeditionSystem only to ask one question -- "is this player in the hub?"
-- -- which is also the menu's entire visibility rule.
step("HubUISystem")
HubUISystem.init(SaveSystem, ProgressionSystem, ExpeditionSystem)
-- 8. Developer commands. Last of the systems on purpose: nothing above may
-- depend on it, so deleting it before launch breaks nothing.
step("DebugSystem")
DebugSystem.init(FateSystem, ExpeditionSystem, EventSystem, LedgerSystem, LootSystem)

-- 9. Hub. Generated from Content/Hub/Crossroads data, and skipped entirely if
-- Workspace already contains a hand-built Crossroads -- authored geometry
-- always wins over generated blockout.
step("building the Crossroads")
HubBuilder.build()
-- The Gate's prompt is bound AFTER the hub exists, because it attaches to
-- geometry HubBuilder creates. An expedition server has no way onward: it
-- reads its manifest and builds the one map it exists for instead.
if isExpeditionServer then
	ExpeditionSystem.startHost()
else
	ExpeditionSystem.bindGatePrompt()
end

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

-- NOBODY SPAWNS UNTIL THEY PRESS PLAY.
--
-- With CharacterAutoLoads true, a joining player stands in the hub while the
-- loading screen is still up: they were being offered the Fate Engine's ROLL
-- prompt before they had pressed anything, which spoils the screen and skips
-- the moment a tutorial would use. Owner-directed 2026-09-21.
--
-- The client says when it is ready (Player_Ready, build spec §4). A second
-- one is ignored, so the remote cannot be used as a free respawn.
Players.CharacterAutoLoads = false

local spawned: { [number]: boolean } = {}

-- WHAT THE CLIENT REPLICATES AROUND WHILE IT HAS NO CHARACTER.
--
-- Holding the spawn until PLAY has a consequence that is easy to miss: with
-- StreamingEnabled, Roblox streams the world around the player's CHARACTER,
-- and a player who has none is a player nothing streams to. The loading
-- screen would then fly its camera around a hub that never arrives -- which
-- is what the fourth walk reported, both as an empty background and as the
-- screen timing out with "taking longer than usual".
--
-- ReplicationFocus is the documented answer: a part the server names as the
-- centre of that player's interest. Pointed at the hub, the Crossroads
-- streams in while they watch the tour, and clearing it when they spawn
-- hands the job back to their character.
--
-- It is harmless when streaming is off, which is why it is set unconditionally
-- rather than behind a check on a property a place file can change without
-- anybody here knowing.
local function loadingFocus(): BasePart
	local existing = Workspace:FindFirstChild("LuckboundLoadingFocus")
	if existing and existing:IsA("BasePart") then
		return existing
	end

	local focus = Instance.new("Part")
	focus.Name = "LuckboundLoadingFocus"
	focus.Anchored = true
	focus.CanCollide = false
	focus.CanQuery = false
	focus.CanTouch = false
	focus.Transparency = 1
	focus.Size = Vector3.one
	focus.Position = GameConfig.HubLayout.Anchors.FATE_ENGINE
	focus.Parent = Workspace
	return focus
end

local function onPlayerAdded(player: Player)
	-- Before anything else: give them somewhere to replicate around, so the
	-- hub is arriving while the loading screen plays.
	player.ReplicationFocus = loadingFocus()

	player.CharacterAdded:Connect(function(character)
		-- Their character is the focus from here; the hub part was only ever
		-- a stand-in for not having one.
		player.ReplicationFocus = nil
		applyMovement(character)
	end)
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

Net.get("Player_Ready").OnServerEvent:Connect(function(player)
	if spawned[player.UserId] then
		return
	end
	spawned[player.UserId] = true
	player:LoadCharacter()
end)

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(function(player)
	SaveSystem.release(player)
	spawned[player.UserId] = nil
end)

-- Anyone who joined while the above was still wiring up.
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end

print(
	`[LUCKBOUND] {if isExpeditionServer then "expedition" else "hub"} server ready -- phase {GameConfig.CurrentPhase}, true RNG, `
		.. `{#GameConfig.Fate.OnboardingSequence}-roll onboarding, expeditions `
		.. (if GameConfig.Expedition.Enabled then "ENABLED" else "disabled")
)
