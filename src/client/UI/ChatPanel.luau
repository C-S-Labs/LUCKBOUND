--!strict
-- The chat window, in the house style. Replaces TextChatService's default
-- window and input bar -- NOT the chat itself. Messages still travel through
-- TextChatService, so Roblox's filtering, mutes and moderation all still
-- apply, and bubble chat is untouched. A place still on legacy chat keeps its
-- default window: this module only takes over when it can do so safely.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)
local UIKit = require(script.Parent.UIKit)

local ChatPanel = {}

local CONFIG = GameConfig.Chat
local INPUT_HEIGHT = 38

local player = Players.LocalPlayer
local panel: Frame
local log: ScrollingFrame
local box: TextBox
local count = 0
local openedListeners: { () -> () } = {}
local lastActivity = 0

local function hex(color: Color3): string
	return "#" .. color:ToHex()
end

--- Full opacity while anything is happening, dimmed once the chat goes
--- quiet, so it never sits as a solid slab over the world.
local function wake()
	lastActivity = os.clock()
	UIKit.tween(panel, UITheme.Motion.Quick, { BackgroundTransparency = UITheme.PanelTransparency })
	UIKit.tween(log, UITheme.Motion.Quick, { ScrollBarImageTransparency = 0 })
	for _, line in log:GetChildren() do
		if line:IsA("TextLabel") then
			UIKit.tween(line, UITheme.Motion.Quick, { TextTransparency = 0 })
		end
	end
end

local function fade()
	UIKit.tween(panel, UITheme.Motion.Slow, { BackgroundTransparency = 1 }, true)
	UIKit.tween(log, UITheme.Motion.Slow, { ScrollBarImageTransparency = 1 }, true)
	for _, line in log:GetChildren() do
		if line:IsA("TextLabel") then
			UIKit.tween(
				line,
				UITheme.Motion.Slow,
				{ TextTransparency = CONFIG.FadedTransparency },
				true
			)
		end
	end
end

local function addLine(text: string)
	count += 1
	local line = UIKit.label(log, text, 15)
	line.AutomaticSize = Enum.AutomaticSize.Y
	line.Size = UDim2.new(1, -UITheme.Space.SM, 0, 0)
	line.LayoutOrder = count
	line.TextStrokeTransparency = 0.7

	local lines = {}
	for _, child in log:GetChildren() do
		if child:IsA("TextLabel") then
			table.insert(lines, child)
		end
	end
	if #lines > CONFIG.MaxMessages then
		table.sort(lines, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		for i = 1, #lines - CONFIG.MaxMessages do
			lines[i]:Destroy()
		end
	end

	-- Stick to the bottom only if the reader was already there; scrolling up
	-- to reread something must not be yanked away by the next message.
	local atBottom = log.CanvasPosition.Y + log.AbsoluteWindowSize.Y
		>= log.AbsoluteCanvasSize.Y - 24
	task.defer(function()
		if atBottom then
			log.CanvasPosition = Vector2.new(0, log.AbsoluteCanvasSize.Y)
		end
	end)
	wake()
end

local function onMessage(message: TextChatMessage)
	local source = message.TextSource
	if source == nil then
		-- System messages (joins, command feedback) read as information.
		addLine(`<font color="{hex(UITheme.AccentCool)}">{message.Text}</font>`)
		return
	end
	local who = Players:GetPlayerByUserId(source.UserId)
	local name = if who then who.DisplayName else source.Name
	local nameColor = if source.UserId == player.UserId
		then UITheme.AccentGold
		else UITheme.TextSecondary
	addLine(`<font color="{hex(nameColor)}"><b>{name}</b></font>  {message.Text}`)
end

local function send()
	local text = box.Text
	box.Text = ""
	if text:match("^%s*$") then
		return
	end
	local channels = TextChatService:FindFirstChild("TextChannels")
	local general = channels and channels:FindFirstChild("RBXGeneral")
	if general and general:IsA("TextChannel") then
		task.spawn(function()
			local ok, err = pcall(general.SendAsync, general, text)
			if not ok then
				warn("[ChatPanel] send failed:", err)
			end
		end)
	end
end

local function build()
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundChat"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 3
	gui.Parent = player:WaitForChild("PlayerGui")

	panel = UIKit.surface(gui, "PANEL")
	panel.Name = "Panel"
	-- Top-left, under Roblox's top bar (IgnoreGuiInset is off). The hub rail
	-- sits low enough to clear it, and collapses when the chat opens.
	panel.Position = UDim2.fromOffset(UITheme.Space.MD, UITheme.Space.SM)
	panel.Size = UDim2.fromOffset(CONFIG.Width, CONFIG.Height)
	UITheme.pad(panel, UITheme.Space.SM)
	local constraint = Instance.new("UISizeConstraint")
	constraint.MaxSize = Vector2.new(CONFIG.Width, CONFIG.Height)
	constraint.Parent = panel

	log = Instance.new("ScrollingFrame")
	log.Name = "Log"
	log.BackgroundTransparency = 1
	log.BorderSizePixel = 0
	log.Size = UDim2.new(1, 0, 1, -(INPUT_HEIGHT + UITheme.Space.SM))
	log.AutomaticCanvasSize = Enum.AutomaticSize.Y
	log.CanvasSize = UDim2.new()
	log.ScrollBarThickness = 3
	log.ScrollBarImageColor3 = UITheme.AccentGold
	log.Parent = panel
	UIKit.list(log, UITheme.Space.XS)

	local inputFrame
	inputFrame, box = UIKit.textbox(panel, "Press / to chat", 15)
	inputFrame.AnchorPoint = Vector2.new(0, 1)
	inputFrame.Position = UDim2.fromScale(0, 1)
	inputFrame.Size = UDim2.new(1, 0, 0, INPUT_HEIGHT)
	box.TextTruncate = Enum.TextTruncate.AtEnd
	box:GetPropertyChangedSignal("Text"):Connect(function()
		if #box.Text > CONFIG.MaxLength then
			box.Text = box.Text:sub(1, CONFIG.MaxLength)
		end
	end)
	box.Focused:Connect(function()
		wake()
		for _, listener in openedListeners do
			task.spawn(listener)
		end
	end)
	box.FocusLost:Connect(function(enterPressed)
		if enterPressed then
			send()
		end
		wake()
	end)
	panel.MouseEnter:Connect(wake)
end

--- Fires whenever the player opens the chat to type.
function ChatPanel.onOpened(listener: () -> ()): ()
	table.insert(openedListeners, listener)
end

function ChatPanel.init(): ()
	if not CONFIG.Enabled or TextChatService.ChatVersion ~= Enum.ChatVersion.TextChatService then
		return
	end
	-- Hide the default window and bar; the service keeps running underneath.
	local window = TextChatService:FindFirstChildOfClass("ChatWindowConfiguration")
	local bar = TextChatService:FindFirstChildOfClass("ChatInputBarConfiguration")
	if window then
		window.Enabled = false
	end
	if bar then
		bar.Enabled = false
	end

	build()
	TextChatService.MessageReceived:Connect(onMessage)

	local focusKey = (Enum.KeyCode :: any)[CONFIG.FocusKey]
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.KeyCode == focusKey then
			-- Deferred, or the "/" that opened the box lands inside it.
			task.defer(function()
				box:CaptureFocus()
			end)
		end
	end)

	task.spawn(function()
		while panel.Parent do
			task.wait(1)
			if not box:IsFocused() and os.clock() - lastActivity > CONFIG.FadeAfterSeconds then
				if lastActivity > 0 then
					fade()
					lastActivity = 0
				end
			end
		end
	end)
	wake()
end

return ChatPanel
