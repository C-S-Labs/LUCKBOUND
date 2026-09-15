--!strict
-- The only LocalScript. Build spec T-117.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
-- Wait for the server to publish remotes before any controller binds to them.
Root:WaitForChild("Net")

local Controllers = script.Controllers
local UI = script.UI

local StateController = require(Controllers.StateController)
local ProximityController = require(Controllers.ProximityController)
local FateRoll = require(UI.FateRoll)
local GlobalAnnouncements = require(UI.GlobalAnnouncements)

StateController.init()
ProximityController.init()
FateRoll.init()
GlobalAnnouncements.init()

print("[LUCKBOUND] client ready")
