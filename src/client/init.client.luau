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
local FateRoll = require(UI.FateRoll)
local GlobalAnnouncements = require(UI.GlobalAnnouncements)
local ExpeditionHud = require(UI.ExpeditionHud)

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

print("[LUCKBOUND] client ready")
