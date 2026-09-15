--!strict
-- Server-wide banners and live-event display. Build spec T-116 and §4.1.
--
-- Handles BOTH paths, and the second is the one that is easy to forget:
--   Announce_Global  -- something just happened, you were here for it
--   Event_StateSync  -- you just arrived; here is what is already happening
--
-- A late joiner gets the active event with its real remaining time and a feed
-- of recent announcements carrying AgeSeconds, so the UI can show them faded
-- rather than pretending they are new.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)

local GlobalAnnouncements = {}

local player = Players.LocalPlayer
local gui: ScreenGui
local bannerHolder: Frame
local eventBar: Frame
local eventLabel: TextLabel
local eventTimer: TextLabel

local activeEvent: any = nil

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundAnnouncements"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 5
	gui.Parent = player:WaitForChild("PlayerGui")

	bannerHolder = Instance.new("Frame")
	bannerHolder.Name = "Banners"
	bannerHolder.AnchorPoint = Vector2.new(0.5, 0)
	bannerHolder.Position = UDim2.new(0.5, 0, 0, 12)
	bannerHolder.Size = UDim2.new(0.9, 0, 0, 260)
	bannerHolder.BackgroundTransparency = 1
	bannerHolder.Parent = gui

	local constraint = Instance.new("UISizeConstraint")
	constraint.MaxSize = Vector2.new(680, 260)
	constraint.Parent = bannerHolder

	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Vertical
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Padding = UDim.new(0, 6)
	layout.Parent = bannerHolder

	-- Persistent bar for an event that is currently running. Distinct from a
	-- transient banner: this stays until the event ends.
	eventBar = Instance.new("Frame")
	eventBar.Name = "ActiveEvent"
	eventBar.AnchorPoint = Vector2.new(0.5, 0)
	eventBar.Position = UDim2.new(0.5, 0, 0, 280)
	eventBar.Size = UDim2.fromOffset(340, 44)
	eventBar.BackgroundColor3 = Color3.fromHex("1A0F2E")
	eventBar.BackgroundTransparency = 0.1
	eventBar.Visible = false
	eventBar.Parent = gui

	local barCorner = Instance.new("UICorner")
	barCorner.CornerRadius = UDim.new(0, 10)
	barCorner.Parent = eventBar

	local barStroke = Instance.new("UIStroke")
	barStroke.Color = Color3.fromHex("A97BE8")
	barStroke.Thickness = 2
	barStroke.Parent = eventBar

	eventLabel = Instance.new("TextLabel")
	eventLabel.Size = UDim2.new(1, -90, 1, 0)
	eventLabel.Position = UDim2.fromOffset(12, 0)
	eventLabel.BackgroundTransparency = 1
	eventLabel.Font = Enum.Font.GothamBold
	eventLabel.TextSize = 16
	eventLabel.TextXAlignment = Enum.TextXAlignment.Left
	eventLabel.TextColor3 = Color3.fromHex("E8D9FF")
	eventLabel.Text = ""
	eventLabel.Parent = eventBar

	eventTimer = Instance.new("TextLabel")
	eventTimer.AnchorPoint = Vector2.new(1, 0.5)
	eventTimer.Position = UDim2.new(1, -12, 0.5, 0)
	eventTimer.Size = UDim2.fromOffset(72, 24)
	eventTimer.BackgroundTransparency = 1
	eventTimer.Font = Enum.Font.GothamBlack
	eventTimer.TextSize = 18
	eventTimer.TextXAlignment = Enum.TextXAlignment.Right
	eventTimer.TextColor3 = Color3.fromHex("F5C97B")
	eventTimer.Text = ""
	eventTimer.Parent = eventBar
end

--- `ageSeconds` > 0 means this is backfill for a late joiner: show it dimmed
--- and briefly, because they were not here for it.
local function showBanner(payload: any, ageSeconds: number)
	local rarity = Constants.RARITY[payload.Rarity] or Constants.RARITY.COMMON
	local isBackfill = ageSeconds > 2

	local banner = Instance.new("Frame")
	banner.Size = UDim2.new(1, 0, 0, if isBackfill then 34 else 46)
	banner.BackgroundColor3 = Color3.fromHex("140F28")
	banner.BackgroundTransparency = 1
	banner.LayoutOrder = -math.floor(os.clock() * 1000)
	banner.Parent = bannerHolder

	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, 8)
	c.Parent = banner

	local s = Instance.new("UIStroke")
	s.Color = rarity.Color
	s.Thickness = if isBackfill then 1 else 2
	s.Transparency = 1
	s.Parent = banner

	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, -20, 1, 0)
	label.Position = UDim2.fromOffset(10, 0)
	label.BackgroundTransparency = 1
	label.Font = if payload.Kind == "FATEBREAK" then Enum.Font.GothamBlack else Enum.Font.GothamBold
	label.TextSize = if isBackfill then 14 else 17
	label.TextColor3 = rarity.Color
	label.TextTransparency = 1
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextTruncate = Enum.TextTruncate.AtEnd
	label.Text = if isBackfill
		then `{payload.Text}   ({math.floor(ageSeconds)}s ago)`
		else payload.Text
	label.Parent = banner

	local fadeIn = TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local targetBg = if isBackfill then 0.45 else 0.12
	local targetText = if isBackfill then 0.35 else 0
	TweenService:Create(banner, fadeIn, { BackgroundTransparency = targetBg }):Play()
	TweenService:Create(label, fadeIn, { TextTransparency = targetText }):Play()
	TweenService:Create(s, fadeIn, { Transparency = if isBackfill then 0.5 else 0 }):Play()

	local hold = if isBackfill then 3 else GameConfig.UI.AnnouncementDurationSeconds
	task.delay(hold, function()
		local fadeOut = TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		TweenService:Create(banner, fadeOut, { BackgroundTransparency = 1 }):Play()
		TweenService:Create(label, fadeOut, { TextTransparency = 1 }):Play()
		TweenService:Create(s, fadeOut, { Transparency = 1 }):Play()
		task.wait(0.4)
		banner:Destroy()
	end)
end

local function formatClock(seconds: number): string
	local m = math.floor(seconds / 60)
	local s = math.floor(seconds % 60)
	return string.format("%d:%02d", m, s)
end

--- Drives the active-event bar from a snapshot. Counts down locally from
--- RemainingSeconds rather than a server timestamp, so a skewed client clock
--- cannot desync the display.
local function setActiveEvent(event: any?)
	activeEvent = event
	if not event then
		eventBar.Visible = false
		return
	end

	eventBar.Visible = true
	eventLabel.Text = event.Name
	local remaining = event.RemainingSeconds

	task.spawn(function()
		local thisEvent = event
		while activeEvent == thisEvent and remaining > 0 do
			eventTimer.Text = formatClock(remaining)
			task.wait(1)
			remaining -= 1
		end
		if activeEvent == thisEvent then
			eventBar.Visible = false
			activeEvent = nil
		end
	end)
end

function GlobalAnnouncements.init(): ()
	build()

	Net.get("Announce_Global").OnClientEvent:Connect(function(payload)
		showBanner(payload, payload.AgeSeconds or 0)
	end)

	-- The late-joiner path. Also fires whenever an event starts or expires,
	-- so the bar is always correct without its own bookkeeping.
	Net.get("Event_StateSync").OnClientEvent:Connect(function(snapshot)
		setActiveEvent(snapshot.ActiveEvents and snapshot.ActiveEvents[1] or nil)

		for _, announcement in snapshot.Announcements or {} do
			-- Skip anything the live path already showed this session.
			if (announcement.AgeSeconds or 0) > 2 then
				showBanner(announcement, announcement.AgeSeconds)
			end
		end
	end)
end

return GlobalAnnouncements
