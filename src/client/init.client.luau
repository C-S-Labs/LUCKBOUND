--!strict
-- The only LocalScript. Build spec T-117.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
-- Wait for the server to publish remotes before any controller binds to them.
Root:WaitForChild("Net")

local Controllers = script.Controllers
local UI = script.UI

local HubEffects = require(Controllers.HubEffects)
local SkyTraffic = require(Controllers.SkyTraffic)
local StateController = require(Controllers.StateController)
local ProximityController = require(Controllers.ProximityController)
local ExpeditionController = require(Controllers.ExpeditionController)
local PartyController = require(Controllers.PartyController)
local FixtureController = require(Controllers.FixtureController)
local RiftController = require(Controllers.RiftController)
local LocomotionController = require(Controllers.LocomotionController)
local LockOnController = require(Controllers.LockOnController)
local EventController = require(Controllers.EventController)
local ThemeController = require(Controllers.ThemeController)
local SkyController = require(Controllers.SkyController)
local SettingsController = require(Controllers.SettingsController)
local DebugCommands = require(Controllers.DebugCommands)
local DevPanel = require(UI.DevPanel)
local LightningController = require(Controllers.LightningController)
local FateRoll = require(UI.FateRoll)
local GlobalAnnouncements = require(UI.GlobalAnnouncements)
local Leaderboard = require(UI.Leaderboard)
local ChatPanel = require(UI.ChatPanel)
local ExpeditionHud = require(UI.ExpeditionHud)
local HubMenu = require(UI.HubMenu)
local LoadingScreen = require(UI.LoadingScreen)
local Vitals = require(UI.Vitals)
local FateHud = require(UI.FateHud)
local UniversalMenu = require(UI.UniversalMenu)
local FateEngineMenu = require(UI.FateEngineMenu)
local SigilShowcase = require(UI.Sigil.SigilShowcase)
SigilShowcase.init() -- dev-only style board, F8 toggles; see docs/WORKLOG.md

-- FIRST, BEFORE ANYTHING DRAWS. The loading screen takes the camera and holds
-- the character while the hub replicates, so the player never sees a
-- half-built Crossroads (STATUS §4, "First-join intro screen"). Everything
-- below it builds behind the curtain.
LoadingScreen.init()
-- The C&S Labs ident plays over the loading screen and dissolves into it once
-- the hub is ready. LoadingScreen skips itself when passing through from a run
-- (isFinished), so the ident does too.
if not LoadingScreen.isFinished() and require(Root.Core.GameConfig).StudioIntro.Enabled then
	require(UI.CSIntro).play({ ready = LoadingScreen.isReady })
end

StateController.init()
-- Settings before the screens they affect: it adopts any ScreenGui that
-- already exists and watches for the rest, so a panel built later is scaled
-- the moment it appears.
SettingsController.init()
HubEffects.init()
SkyTraffic.init()
LightningController.init()
ProximityController.init()
-- The HUD before the controller: the controller fires state immediately to
-- every listener, so a HUD that subscribes afterwards would miss nothing --
-- but a player rejoining mid-expedition gets the banner without a frame gap.
ExpeditionHud.init()
ExpeditionController.init()
-- Chests, the vault and forcefields move on each client (build spec §7.5).
FixtureController.init()
RiftController.init()
-- Before the menu, which draws the party panel from it.
PartyController.init()
-- The live palette, before any screen is built: EventController holds what is
-- happening to the world, ThemeController turns that plus where the player is
-- standing into the colours the menu paints with. A widget built afterwards
-- registers itself and is painted on the spot.
EventController.init()
ThemeController.init()
-- The sky reads the same event state the menu tint does, so the two can never
-- disagree about which event is running.
SkyController.init()
FateRoll.init()
GlobalAnnouncements.init()
-- House-style player list and chat window, in place of the Roblox defaults.
Leaderboard.init()
ChatPanel.init()
-- The hub menu after the roll UI: it subscribes to FateRoll's rolling signal
-- so it can get out of the way during a reveal.
HubMenu.init()
UniversalMenu.init()
FateEngineMenu.init()
-- Opening the chat folds the rail away: both live on the left edge.
ChatPanel.onOpened(HubMenu.collapse)
-- Movement waits for PLAY: the camera tour is not the moment to hand the
-- player a character. (The controller also honours the loading screen's
-- WalkSpeed-0 hold as a multiplier, so an early start would not break it.)
LoadingScreen.onFinished(function()
	Vitals.init()
	FateHud.init()
	LocomotionController.init({ Vitals = Vitals })
	LockOnController.init({ Locomotion = LocomotionController })
end)

-- Last: developer tooling must never be load-bearing for anything above it.
DebugCommands.init()
DevPanel.init()

print("[LUCKBOUND] client ready")
