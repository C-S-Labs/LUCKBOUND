--!strict
-- The expedition banner: where you are, how long is left, and what happened
-- when it ended. Build spec §7.1.
--
-- Deliberately small. The roll is the moment this game rests on (Master Spec
-- §25) and an expedition HUD that competes with it would be the wrong call --
-- this sits at the top of the screen, states two facts, and gets out of the
-- way. Everything it draws is themed from UITheme and coloured from the rarity
-- table, so it needs no palette of its own.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local UITheme = require(Root.Core.UITheme)
local UIKit = require(script.Parent.UIKit)

local ExpeditionController = require(script.Parent.Parent.Controllers.ExpeditionController)
local EventController = require(script.Parent.Parent.Controllers.EventController)

local ExpeditionHud = {}

local player = Players.LocalPlayer
local gui: ScreenGui
local banner: Frame
local worldLabel: TextLabel
local timerLabel: TextLabel
local toast: TextLabel

local formatClock = UIKit.formatClock

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundExpedition"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = player:WaitForChild("PlayerGui")

	banner = Instance.new("Frame")
	banner.Name = "Banner"
	banner.AnchorPoint = Vector2.new(0.5, 0)
	banner.Position = UDim2.new(0.5, 0, 0, 18)
	-- THREE THINGS WANT THE TOP OF THE SCREEN: this banner, the live-event
	-- bar and a roll announcement. The event bar took the very top when it
	-- moved off the middle of the screen, so this steps down out of its way
	-- while one is running rather than sitting on top of it.
	EventController.onChanged(function(events)
		local shift = if #events > 0 then 60 else 0
		banner.Position = UDim2.new(0.5, 0, 0, 18 + shift)
	end)
	-- Scale-width with an offset cap, so it reads on a phone without becoming
	-- a stripe across a desktop monitor.
	banner.Size = UDim2.new(0.5, 0, 0, 62)
	banner.BackgroundColor3 = UITheme.BackgroundColor
	banner.BackgroundTransparency = 0.12
	banner.Visible = false
	banner.Parent = gui
	UITheme.corner(banner)

	local sizeConstraint = Instance.new("UISizeConstraint")
	sizeConstraint.MinSize = Vector2.new(240, 52)
	sizeConstraint.MaxSize = Vector2.new(460, 72)
	sizeConstraint.Parent = banner

	local bannerStroke = UITheme.stroke(banner, UITheme.AccentGold, 2)
	bannerStroke.Name = "RarityStroke"

	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, 16)
	padding.PaddingRight = UDim.new(0, 16)
	padding.PaddingTop = UDim.new(0, 8)
	padding.PaddingBottom = UDim.new(0, 8)
	padding.Parent = banner

	worldLabel = Instance.new("TextLabel")
	worldLabel.Name = "World"
	worldLabel.Size = UDim2.new(1, -86, 1, 0)
	worldLabel.BackgroundTransparency = 1
	worldLabel.Font = UITheme.LabelFont
	worldLabel.TextScaled = true
	worldLabel.TextXAlignment = Enum.TextXAlignment.Left
	worldLabel.TextColor3 = UITheme.TextPrimary
	worldLabel.Text = ""
	worldLabel.Parent = banner

	timerLabel = Instance.new("TextLabel")
	timerLabel.Name = "Timer"
	timerLabel.AnchorPoint = Vector2.new(1, 0.5)
	timerLabel.Position = UDim2.new(1, 0, 0.5, 0)
	timerLabel.Size = UDim2.fromOffset(82, 34)
	timerLabel.BackgroundTransparency = 1
	timerLabel.Font = UITheme.HeaderFont
	timerLabel.TextScaled = true
	timerLabel.TextXAlignment = Enum.TextXAlignment.Right
	timerLabel.TextColor3 = UITheme.TextSecondary
	timerLabel.Text = ""
	timerLabel.Parent = banner

	-- Refusals and end-of-run summaries. One line, centre-bottom, fades out.
	toast = Instance.new("TextLabel")
	toast.Name = "Toast"
	toast.AnchorPoint = Vector2.new(0.5, 1)
	toast.Position = UDim2.new(0.5, 0, 1, -130)
	toast.Size = UDim2.new(0.6, 0, 0, 34)
	toast.BackgroundTransparency = 1
	toast.Font = UITheme.BodyFont
	toast.TextScaled = true
	toast.TextColor3 = UITheme.TextPrimary
	toast.TextStrokeTransparency = 0.5
	toast.TextTransparency = 1
	toast.Text = ""
	toast.Parent = gui
end

local toastToken = 0

local function showToast(text: string)
	toastToken += 1
	local token = toastToken
	toast.Text = text
	toast.TextTransparency = 0
	toast.TextStrokeTransparency = 0.5

	task.delay(2.6, function()
		if token ~= toastToken then
			return
		end
		TweenService:Create(toast, TweenInfo.new(0.5), {
			TextTransparency = 1,
			TextStrokeTransparency = 1,
		}):Play()
	end)
end

function ExpeditionHud.init(): ()
	build()

	ExpeditionController.onChanged(function(state)
		if not state then
			banner.Visible = false
			return
		end

		local color = UITheme.rarityColor(state.Rarity)
		worldLabel.Text = string.upper(state.Name)
		worldLabel.TextColor3 = color
		;(banner:FindFirstChild("RarityStroke") :: UIStroke).Color = color
		banner.Visible = true
	end)

	ExpeditionController.onEnded = function(payload)
		if payload.Reason == "ABORTED" then
			if payload.Message then
				showToast(payload.Message)
			end
			return
		end
		if payload.Reason == "DIED" then
			showToast("You fell. The expedition ended.")
		elseif payload.FateAwarded > 0 then
			showToast(`Expedition complete  ·  +{payload.FateAwarded} Fate`)
		end
	end

	RunService.Heartbeat:Connect(function()
		if banner.Visible then
			timerLabel.Text = formatClock(ExpeditionController.remaining())
		end
	end)
end

ExpeditionHud.formatClock = formatClock

return ExpeditionHud
