--!strict
-- The only LocalScript. Build spec T-117.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
-- Wait for the server to publish remotes before any controller binds to them.
Root:WaitForChild("Net")

local Controllers = script.Controllers
local UI = script.UI

local HubEffects = require(Controllers.HubEffects)
local StateController = require(Controllers.StateController)
local ProximityController = require(Controllers.ProximityController)
local ExpeditionController = require(Controllers.ExpeditionController)
local LocomotionController = require(Controllers.LocomotionController)
local DebugCommands = require(Controllers.DebugCommands)
local FateRoll = require(UI.FateRoll)
local GlobalAnnouncements = require(UI.GlobalAnnouncements)
local ExpeditionHud = require(UI.ExpeditionHud)
local HubMenu = require(UI.HubMenu)
local LoadingScreen = require(UI.LoadingScreen)

-- FIRST, BEFORE ANYTHING DRAWS. The loading screen takes the camera and holds
-- the character while the hub replicates, so the player never sees a
-- half-built Crossroads (STATUS §4, "First-join intro screen"). Everything
-- below it builds behind the curtain.
LoadingScreen.init()

StateController.init()
HubEffects.init()
ProximityController.init()
-- The HUD before the controller: the controller fires state immediately to
-- every listener, so a HUD that subscribes afterwards would miss nothing --
-- but a player rejoining mid-expedition gets the banner without a frame gap.
ExpeditionHud.init()
ExpeditionController.init()
FateRoll.init()
GlobalAnnouncements.init()
-- The hub menu after the roll UI: it subscribes to FateRoll's rolling signal
-- so it can get out of the way during a reveal.
HubMenu.init()
-- Movement waits for PLAY. The loading screen holds the character at
-- WalkSpeed 0, and this controller writes WalkSpeed every frame -- starting it
-- early would simply undo the hold and let the player walk away from the
-- camera tour.
LoadingScreen.onFinished(function()
	LocomotionController.init()
end)

-- Last: developer tooling must never be load-bearing for anything above it.
DebugCommands.init()

print("[LUCKBOUND] client ready")
