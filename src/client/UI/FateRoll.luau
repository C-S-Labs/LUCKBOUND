--!strict
-- The roll: prompt, build-up, reveal, result card. Build spec T-115.
--
-- This is the most important UI in the game. Master Spec §25: if the player
-- does not want to roll again after a rare result, nothing else saves it.
--
-- PACING IS DATA. Build-up length comes from GameConfig.UI, reveal length and
-- colour from Constants.RARITY. A rarer result takes longer to resolve and
-- that escalation is the anticipation mechanic -- tune those numbers first
-- when the roll feels flat, before touching anything here.
--
-- The client is told the answer at the start of the build-up and simply
-- withholds it (build spec §3.4.5). A client that learns the answer late can
-- be made to reveal early; a client that decides the answer is an exploit.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)

local ProximityController = require(script.Parent.Parent.Controllers.ProximityController)

local FateRoll = {}

local player = Players.LocalPlayer
local gui: ScreenGui
local prompt: Frame
local overlay: Frame
local scrambleLabel: TextLabel
local card: Frame
local rolling = false

local function corner(parent: Instance, radius: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, radius)
	c.Parent = parent
	return c
end

local function stroke(parent: Instance, color: Color3, thickness: number)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.Parent = parent
	return s
end

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundFateRoll"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = player:WaitForChild("PlayerGui")

	-- === prompt =====================================================
	prompt = Instance.new("Frame")
	prompt.Name = "Prompt"
	prompt.AnchorPoint = Vector2.new(0.5, 1)
	prompt.Position = UDim2.new(0.5, 0, 1, -48)
	prompt.Size = UDim2.fromOffset(240, 62)
	prompt.BackgroundColor3 = Color3.fromHex("15122E")
	prompt.BackgroundTransparency = 0.15
	prompt.Visible = false
	prompt.Parent = gui
	corner(prompt, 14)
	stroke(prompt, Color3.fromHex("D9A441"), 2)

	local promptLabel = Instance.new("TextLabel")
	promptLabel.Name = "Label"
	promptLabel.Size = UDim2.fromScale(1, 1)
	promptLabel.BackgroundTransparency = 1
	promptLabel.Font = Enum.Font.GothamBold
	promptLabel.TextScaled = true
	promptLabel.TextColor3 = Color3.fromHex("F5E6C8")
	promptLabel.Text = if UserInputService.TouchEnabled then "TAP TO ROLL" else "[E]  ROLL"
	promptLabel.Parent = prompt

	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 12)
	padding.PaddingBottom = UDim.new(0, 12)
	padding.PaddingLeft = UDim.new(0, 16)
	padding.PaddingRight = UDim.new(0, 16)
	padding.Parent = promptLabel

	-- Touch players get a real button rather than a keyboard hint.
	if UserInputService.TouchEnabled then
		local button = Instance.new("TextButton")
		button.Size = UDim2.fromScale(1, 1)
		button.BackgroundTransparency = 1
		button.Text = ""
		button.Parent = prompt
		button.Activated:Connect(function()
			ProximityController.requestRoll()
		end)
	end

	-- === reveal overlay =============================================
	overlay = Instance.new("Frame")
	overlay.Name = "Overlay"
	overlay.Size = UDim2.fromScale(1, 1)
	overlay.BackgroundColor3 = Color3.fromHex("070614")
	overlay.BackgroundTransparency = 1
	overlay.Visible = false
	overlay.ZIndex = 10
	overlay.Parent = gui

	scrambleLabel = Instance.new("TextLabel")
	scrambleLabel.Name = "Scramble"
	scrambleLabel.AnchorPoint = Vector2.new(0.5, 0.5)
	scrambleLabel.Position = UDim2.fromScale(0.5, 0.45)
	scrambleLabel.Size = UDim2.new(0.9, 0, 0, 90)
	scrambleLabel.BackgroundTransparency = 1
	scrambleLabel.Font = Enum.Font.GothamBlack
	scrambleLabel.TextScaled = true
	scrambleLabel.TextTransparency = 1
	scrambleLabel.TextColor3 = Color3.fromHex("FFFFFF")
	scrambleLabel.Text = ""
	scrambleLabel.ZIndex = 11
	scrambleLabel.Parent = overlay

	-- === result card ================================================
	card = Instance.new("Frame")
	card.Name = "ResultCard"
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.Position = UDim2.fromScale(0.5, 0.5)
	card.Size = UDim2.new(0.86, 0, 0, 320)
	card.BackgroundColor3 = Color3.fromHex("110E26")
	card.BackgroundTransparency = 1
	card.Visible = false
	card.ZIndex = 12
	card.Parent = overlay
	corner(card, 20)

	local cardConstraint = Instance.new("UISizeConstraint")
	cardConstraint.MaxSize = Vector2.new(560, 360)
	cardConstraint.Parent = card

	local cardStroke = stroke(card, Color3.fromHex("FFFFFF"), 3)
	cardStroke.Name = "RarityStroke"
	cardStroke.Transparency = 1

	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Vertical
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Padding = UDim.new(0, 10)
	layout.Parent = card

	local cardPadding = Instance.new("UIPadding")
	cardPadding.PaddingTop = UDim.new(0, 24)
	cardPadding.PaddingBottom = UDim.new(0, 24)
	cardPadding.PaddingLeft = UDim.new(0, 20)
	cardPadding.PaddingRight = UDim.new(0, 20)
	cardPadding.Parent = card

	local function cardLabel(name: string, height: number, font: Enum.Font, order: number): TextLabel
		local l = Instance.new("TextLabel")
		l.Name = name
		l.Size = UDim2.new(1, 0, 0, height)
		l.BackgroundTransparency = 1
		l.Font = font
		l.TextScaled = true
		l.TextTransparency = 1
		l.TextColor3 = Color3.fromHex("FFFFFF")
		l.LayoutOrder = order
		l.ZIndex = 13
		l.Text = ""
		l.Parent = card
		return l
	end

	cardLabel("Rarity", 34, Enum.Font.GothamBold, 1)
	cardLabel("WorldName", 68, Enum.Font.GothamBlack, 2)

	local flavor = cardLabel("Flavor", 60, Enum.Font.Gotham, 3)
	flavor.TextScaled = false
	flavor.TextSize = 18
	flavor.TextWrapped = true
	flavor.TextColor3 = Color3.fromHex("C7BFE0")

	cardLabel("RollNumber", 22, Enum.Font.Gotham, 4)
end

local SCRAMBLE_POOL = { "?", "?", "?", "*", "#", "@", "%", "&" }

--- Build-up: the destination scrambles while the machine spins up. The player
--- already knows a result is coming but not what it is.
local function playBuildup(duration: number)
	local names = {}
	for _, world in Worlds do
		table.insert(names, world.Name)
	end
	table.sort(names)

	scrambleLabel.TextTransparency = 0
	local elapsed = 0
	local nextFlip = 0

	while elapsed < duration do
		local dt = RunService.RenderStepped:Wait()
		elapsed += dt

		if elapsed >= nextFlip then
			-- Flips accelerate as the reveal approaches.
			local progress = elapsed / duration
			local interval = 0.12 - progress * 0.08
			nextFlip = elapsed + math.max(interval, 0.03)

			if progress < 0.55 then
				scrambleLabel.Text = names[math.random(1, #names)]
			else
				local scrambled = {}
				for _ = 1, math.random(4, 9) do
					table.insert(scrambled, SCRAMBLE_POOL[math.random(1, #SCRAMBLE_POOL)])
				end
				scrambleLabel.Text = table.concat(scrambled)
			end
		end
	end
end

local function showCard(payload: any, rarity: any)
	scrambleLabel.TextTransparency = 1
	card.Visible = true

	local rarityLabel = card:FindFirstChild("Rarity") :: TextLabel
	local worldLabel = card:FindFirstChild("WorldName") :: TextLabel
	local flavorLabel = card:FindFirstChild("Flavor") :: TextLabel
	local rollLabel = card:FindFirstChild("RollNumber") :: TextLabel
	local cardStroke = card:FindFirstChild("RarityStroke") :: UIStroke

	rarityLabel.Text = string.upper(rarity.Display)
	rarityLabel.TextColor3 = rarity.Color
	worldLabel.Text = payload.Name
	worldLabel.TextColor3 = rarity.Color
	flavorLabel.Text = payload.Flavor
	rollLabel.Text = if payload.IsTutorialRoll
		then "GUIDED ROLL"
		else `ROLL #{payload.RollNumber}`
	rollLabel.TextColor3 = Color3.fromHex("8B84A8")
	cardStroke.Color = rarity.Color

	local info = TweenInfo.new(0.45, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
	TweenService:Create(card, info, { BackgroundTransparency = 0.05 }):Play()
	TweenService:Create(cardStroke, info, { Transparency = 0 }):Play()

	for order, label in { rarityLabel, worldLabel, flavorLabel, rollLabel } do
		task.delay(0.06 * order, function()
			TweenService:Create(label, info, { TextTransparency = 0 }):Play()
		end)
	end
end

local function hideAll()
	local info = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	TweenService:Create(overlay, info, { BackgroundTransparency = 1 }):Play()
	TweenService:Create(card, info, { BackgroundTransparency = 1 }):Play()

	local cardStroke = card:FindFirstChild("RarityStroke") :: UIStroke
	TweenService:Create(cardStroke, info, { Transparency = 1 }):Play()

	for _, child in card:GetChildren() do
		if child:IsA("TextLabel") then
			TweenService:Create(child, info, { TextTransparency = 1 }):Play()
		end
	end

	task.wait(0.35)
	overlay.Visible = false
	card.Visible = false
end

local function onRollResult(payload: any)
	if rolling then
		return
	end
	rolling = true
	ProximityController.setLocked(true)

	local rarity = Constants.RARITY[payload.Rarity]
	local revealDuration = payload.RevealDuration or rarity.RevealDuration

	overlay.Visible = true
	TweenService:Create(
		overlay,
		TweenInfo.new(0.3, Enum.EasingStyle.Quad),
		{ BackgroundTransparency = 0.25 }
	):Play()

	-- Build-up scales with rarity: the total wait before the answer is
	-- GameConfig.UI.RollBuildupSeconds plus the rarity's own reveal duration,
	-- so a Mythic keeps you waiting noticeably longer than a Common.
	playBuildup(GameConfig.UI.RollBuildupSeconds + revealDuration)

	showCard(payload, rarity)
	task.wait(GameConfig.UI.ResultCardHoldSeconds)
	hideAll()

	rolling = false
	ProximityController.setLocked(false)
end

function FateRoll.init(): ()
	build()

	ProximityController.bindPrompt(function(visible)
		prompt.Visible = visible
	end)

	Net.get("Fate_RollResult").OnClientEvent:Connect(function(payload)
		task.spawn(onRollResult, payload)
	end)
end

return FateRoll
