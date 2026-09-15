--!strict
-- Shows the ROLL prompt near the Fate Engine and turns input into a request.
-- Build spec T-114. Works on keyboard, gamepad and touch.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)

local ProximityController = {}

local player = Players.LocalPlayer
local inRange = false
local locked = false -- true while a reveal is playing

local onRangeChanged: ((boolean) -> ())? = nil

local function anchor(): BasePart?
	local crossroads = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	local engine = crossroads and crossroads:FindFirstChild(Constants.NAMES.FATE_ENGINE)
	local a = engine and engine:FindFirstChild(Constants.NAMES.ROLL_ANCHOR)
	return if a and a:IsA("BasePart") then a else nil
end

local function requestRoll()
	if not inRange or locked then
		return
	end
	-- Deliberately no payload: the server decides everything. Build spec §3.4.1.
	Net.get("Fate_RequestRoll"):FireServer()
end

--- Called by the reveal UI so a player cannot queue rolls mid-animation.
function ProximityController.setLocked(value: boolean): ()
	locked = value
	if onRangeChanged then
		onRangeChanged(inRange and not locked)
	end
end

function ProximityController.bindPrompt(fn: (boolean) -> ()): ()
	onRangeChanged = fn
end

function ProximityController.init(): ()
	ContextActionService:BindAction("LuckboundRoll", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			requestRoll()
		end
		return Enum.ContextActionResult.Pass
	end, false, Enum.KeyCode.E, Enum.KeyCode.ButtonA)

	RunService.Heartbeat:Connect(function()
		local a = anchor()
		local character = player.Character
		local hrp = character and character:FindFirstChild("HumanoidRootPart")

		local nowInRange = false
		if a and hrp and hrp:IsA("BasePart") then
			nowInRange = (hrp.Position - a.Position).Magnitude <= GameConfig.UI.PromptActivationDistance
		end

		if nowInRange ~= inRange then
			inRange = nowInRange
			if onRangeChanged then
				onRangeChanged(inRange and not locked)
			end
		end
	end)
end

ProximityController.requestRoll = requestRoll

return ProximityController
