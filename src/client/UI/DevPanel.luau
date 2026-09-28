--!strict
-- THE DEVELOPER PANEL. Testing tooling, not a feature: it exists only when
-- GameConfig.Debug.AllowCommands is on, and every SERVER command it sends is
-- still permission-checked by Systems/DebugSystem.
--
-- Everything is drawn from the registry (Content/DevCommands), so a new entry
-- there appears here -- in its category tab, with a picker per argument and
-- its presets -- with no change to this file. Everything is CLICKABLE:
--   * category tabs down the left
--   * a card per command: every choice argument opens a list of its live
--     values (world ids, events, the chunks of the map you are on...), number
--     arguments offer their quick values, presets run in one click
--   * the command bar autocompletes names AND argument values (Core/DevCore):
--     click a suggestion or press Tab; Up/Down walk the suggestions, or your
--     history when there are none; Enter runs
--   * the output log shows every reply, client and server, green or red
-- Open with GameConfig.Debug.PanelKey (F4) or the DEV button, or /panel.
--
-- Built entirely from UIKit/UITheme, like every other screen, so it reads as
-- the same game.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local DevCommands = require(Root.Content.DevCommands)
local DevCore = require(Root.Core.DevCore)
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)

local DebugCommands = require(script.Parent.Parent.Controllers.DebugCommands)
local UIKit = require(script.Parent.UIKit)

local DevPanel = {}

local player = Players.LocalPlayer
local S = UITheme.Space

local WIDTH, HEIGHT = 680, 600
local TAB_WIDTH = 150
local LOG_HEIGHT = 150
local ROW = 30

local gui: ScreenGui
local window: Frame
local bar: TextBox
local suggestFrame: Frame
local cardsFrame: ScrollingFrame
local tabsFrame: ScrollingFrame
local logFrame: ScrollingFrame
local tabButtons: { [string]: TextButton } = {}
local currentCategory = DevCommands.Categories[1].Id

local history: { string } = {}
local historyAt = 0
local suggestions: { DevCore.Suggestion } = {}
local highlighted = 0
local logCount = 0

-- === small builders =================================================

local function chip(parent: Instance, text: string, style: string?, onClick: () -> ()): TextButton
	local b = UIKit.button(parent, text, style, onClick)
	b.TextSize = 13
	b.TextTruncate = Enum.TextTruncate.AtEnd
	b.Size = UDim2.fromOffset(120, 28)
	return b
end

local function grid(parent: Instance, cell: Vector2?): Frame
	local holder = Instance.new("Frame")
	holder.BackgroundTransparency = 1
	holder.AutomaticSize = Enum.AutomaticSize.Y
	holder.Size = UDim2.new(1, 0, 0, 0)
	holder.Parent = parent
	local layout = Instance.new("UIGridLayout")
	local c = cell or Vector2.new(124, 28)
	layout.CellSize = UDim2.fromOffset(c.X, c.Y)
	layout.CellPadding = UDim2.fromOffset(S.XS, S.XS)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = holder
	return holder
end

local function scroller(parent: Instance): ScrollingFrame
	local f = Instance.new("ScrollingFrame")
	f.BackgroundTransparency = 1
	f.BorderSizePixel = 0
	f.ScrollBarThickness = 4
	f.ScrollBarImageColor3 = UITheme.AccentGold
	f.AutomaticCanvasSize = Enum.AutomaticSize.Y
	f.CanvasSize = UDim2.new()
	f.ScrollingDirection = Enum.ScrollingDirection.Y
	f.Parent = parent
	return f
end

-- === the log ========================================================

local function log(text: string, ok: boolean)
	if not logFrame then
		return
	end
	logCount += 1
	local line = UIKit.label(logFrame, text, 13, if ok then "PRIMARY" else nil)
	line.TextColor3 = if ok then UITheme.TextPrimary else UITheme.AccentWarn
	line.AutomaticSize = Enum.AutomaticSize.Y
	line.Size = UDim2.new(1, -S.SM, 0, 0)
	line.LayoutOrder = logCount
	local lines = {}
	for _, child in logFrame:GetChildren() do
		if child:IsA("TextLabel") then
			table.insert(lines, child)
		end
	end
	table.sort(lines, function(a, b)
		return a.LayoutOrder < b.LayoutOrder
	end)
	for i = 1, #lines - GameConfig.Debug.PanelLogLines do
		lines[i]:Destroy()
	end
	task.defer(function()
		logFrame.CanvasPosition = Vector2.new(0, math.max(0, logFrame.AbsoluteCanvasSize.Y))
	end)
end

local function clearLog()
	for _, child in logFrame:GetChildren() do
		if child:IsA("TextLabel") then
			child:Destroy()
		end
	end
end

-- === running ========================================================

local function runLine(line: string)
	line = string.gsub(line, "^%s+", "")
	if line == "" then
		return
	end
	if string.sub(line, 1, 1) ~= "/" then
		line = "/" .. line
	end
	log("> " .. line, true)
	if history[#history] ~= line then
		table.insert(history, line)
	end
	historyAt = #history + 1
	DebugCommands.runLine(line)
end

local function runCommand(command: any, args: { string })
	local line = "/" .. command.Name
	if #args > 0 then
		line ..= " " .. table.concat(args, " ")
	end
	runLine(line)
end

-- === autocomplete ===================================================

local function hideSuggestions()
	suggestFrame.Visible = false
	suggestions = {}
	highlighted = 0
end

local function drawSuggestions()
	for _, child in suggestFrame:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	if #suggestions == 0 then
		suggestFrame.Visible = false
		return
	end
	for i, sug in suggestions do
		local row = Instance.new("TextButton")
		row.AutoButtonColor = false
		row.BorderSizePixel = 0
		row.Text = ""
		row.LayoutOrder = i
		row.Size = UDim2.new(1, 0, 0, 26)
		row.BackgroundColor3 = if i == highlighted then UITheme.AccentGold else UITheme.RaisedColor
		row.BackgroundTransparency = if i == highlighted then 0.55 else 1
		row.ZIndex = 21
		row.Parent = suggestFrame
		UITheme.corner(row, UITheme.RadiusSmall)
		local left = UIKit.label(row, sug.Label, 14, if sug.Text then "PRIMARY" else "MUTED")
		left.Position = UDim2.fromOffset(S.SM, 0)
		left.Size = UDim2.new(0.55, 0, 1, 0)
		left.TextTruncate = Enum.TextTruncate.AtEnd
		left.TextWrapped = false
		left.ZIndex = 22
		local right = UIKit.label(row, sug.Hint, 12, "MUTED")
		right.Position = UDim2.new(0.55, S.SM, 0, 0)
		right.Size = UDim2.new(0.45, -S.SM * 2, 1, 0)
		right.TextTruncate = Enum.TextTruncate.AtEnd
		right.TextWrapped = false
		right.ZIndex = 22
		row.Activated:Connect(function()
			if sug.Text then
				bar.Text = sug.Text
				bar.CursorPosition = #bar.Text + 1
				bar:CaptureFocus()
			end
		end)
	end
	suggestFrame.Visible = true
end

local function refreshSuggestions()
	suggestions = DevCore.complete(
		bar.Text,
		DevCommands,
		DebugCommands.sources(),
		GameConfig.Debug.PanelSuggestions
	)
	highlighted = if #suggestions > 0 then 1 else 0
	drawSuggestions()
end

local function accept(): boolean
	local sug = suggestions[highlighted]
	if sug and sug.Text then
		bar.Text = sug.Text
		bar.CursorPosition = #bar.Text + 1
		return true
	end
	return false
end

-- === command cards ==================================================

local function valueLabel(arg: any, value: string?): string
	if value == nil then
		return if arg.Optional then "(none)" else "choose..."
	end
	if arg.Source == "CHUNKS" then
		return DebugCommands.describeChunk(value)
	end
	return value
end

local function buildCard(command: any, order: number)
	local card = UIKit.surface(cardsFrame, "RAISED")
	card.AutomaticSize = Enum.AutomaticSize.Y
	card.Size = UDim2.new(1, -S.SM, 0, 0)
	card.LayoutOrder = order
	UITheme.pad(card, S.SM)
	UIKit.list(card, S.XS)

	local title = UIKit.label(
		card,
		`/{command.Name}  <font color="#{UITheme.TextMuted:ToHex()}" size="12">{string.lower(
			command.Side
		)}  {DevCore.usage(command)}</font>`,
		16,
		"ACCENT"
	)
	title.Size = UDim2.new(1, 0, 0, 20)
	title.LayoutOrder = 1

	local summary = UIKit.label(card, command.Summary, 13, "SECONDARY")
	summary.AutomaticSize = Enum.AutomaticSize.Y
	summary.Size = UDim2.new(1, 0, 0, 0)
	summary.LayoutOrder = 2

	local values: { [number]: string? } = {}
	local args = command.Args or {}

	for i, arg in args do
		local row = Instance.new("Frame")
		row.BackgroundTransparency = 1
		row.AutomaticSize = Enum.AutomaticSize.Y
		row.Size = UDim2.new(1, 0, 0, ROW)
		row.LayoutOrder = 2 + i
		row.Parent = card
		UIKit.list(row, S.XS)

		local line = Instance.new("Frame")
		line.BackgroundTransparency = 1
		line.Size = UDim2.new(1, 0, 0, ROW)
		line.LayoutOrder = 1
		line.Parent = row

		local name =
			UIKit.label(line, arg.Name .. (if arg.Optional then " (opt)" else ""), 13, "MUTED")
		name.Size = UDim2.new(0, 110, 1, 0)
		name.TextWrapped = false

		local drawer = grid(row)
		drawer.LayoutOrder = 2
		drawer.Visible = false

		if arg.Type == "choice" then
			local pick: TextButton
			pick = UIKit.button(line, valueLabel(arg, nil), "GHOST", function()
				if drawer.Visible then
					drawer.Visible = false
					return
				end
				for _, child in drawer:GetChildren() do
					if child:IsA("GuiButton") then
						child:Destroy()
					end
				end
				local opts = DevCore.options(arg, DebugCommands.sources())
				if arg.Optional then
					chip(drawer, "(none)", "GHOST", function()
						values[i] = nil
						pick.Text = valueLabel(arg, nil)
						drawer.Visible = false
					end)
				end
				if #opts == 0 then
					chip(drawer, "nothing available", "GHOST", function() end)
				end
				for _, opt in opts do
					chip(drawer, valueLabel(arg, opt), "GHOST", function()
						values[i] = opt
						pick.Text = valueLabel(arg, opt)
						drawer.Visible = false
					end)
				end
				drawer.Visible = true
			end)
			pick.TextSize = 13
			pick.TextTruncate = Enum.TextTruncate.AtEnd
			pick.Position = UDim2.fromOffset(114, 0)
			pick.Size = UDim2.new(1, -114, 1, 0)
		else
			local field, box = UIKit.textbox(line, arg.Type, 13)
			field.Position = UDim2.fromOffset(114, 0)
			field.Size = UDim2.new(1, -114, 1, 0)
			box.FocusLost:Connect(function()
				values[i] = if box.Text ~= "" then box.Text else nil
			end)
			if arg.Suggest then
				drawer.Visible = true
				for _, v in arg.Suggest do
					local c = chip(drawer, v, "GHOST", function()
						box.Text = v
						values[i] = v
					end)
					c.Size = UDim2.fromOffset(60, 26)
				end
			end
		end
	end

	-- presets: whole argument lists, run in one click
	local actions = grid(card, Vector2.new(110, 30))
	actions.LayoutOrder = 100
	for _, preset in command.Presets or {} do
		chip(actions, preset.Label, "GHOST", function()
			runCommand(command, preset.Args)
		end).Size =
			UDim2.fromOffset(110, 30)
	end
	local run = chip(
		actions,
		if #args > 0 then "Run" else "Run /" .. command.Name,
		if command.Danger then "DANGER" else "PRIMARY",
		function()
			local out = {}
			for i = 1, #args do
				local v = values[i]
				if v == nil then
					break -- optional arguments are trailing
				end
				table.insert(out, v)
			end
			runCommand(command, out)
		end
	)
	run.Size = UDim2.fromOffset(110, 30)
end

local function paintTabs()
	for catId, button in tabButtons do
		local on = catId == currentCategory
		button.BackgroundColor3 = if on then UITheme.AccentGold else UITheme.RaisedColor
		button.TextColor3 = if on then UITheme.BackgroundColor else UITheme.TextPrimary
	end
end

local function showCategory(id: string)
	currentCategory = id
	paintTabs()
	for _, child in cardsFrame:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	local n = 0
	for _, command in DevCommands.Commands do
		if command.Category == id then
			n += 1
			buildCard(command, n)
		end
	end
	cardsFrame.CanvasPosition = Vector2.zero
end

-- === window =========================================================

local function toggle()
	window.Visible = not window.Visible
	if window.Visible then
		showCategory(currentCategory) -- live lists (the map's chunks) refresh on open
	else
		hideSuggestions()
	end
end

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundDevPanel"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 50
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = player:WaitForChild("PlayerGui")

	local devButton = UIKit.button(gui, "DEV", "GHOST", toggle)
	devButton.TextSize = 13
	devButton.AnchorPoint = Vector2.new(1, 0)
	devButton.Position = UDim2.new(1, -S.MD, 0, S.SM)
	devButton.Size = UDim2.fromOffset(56, 30)

	window = UIKit.surface(gui, "PANEL")
	window.AnchorPoint = Vector2.new(1, 0)
	window.Position = UDim2.new(1, -S.MD, 0, 46)
	window.Size = UDim2.fromOffset(WIDTH, HEIGHT)
	window.Visible = false
	-- A floor, not a ceiling: the corner grip below lets the window grow.
	local limit = Instance.new("UISizeConstraint")
	limit.MinSize = Vector2.new(GameConfig.Debug.PanelMinWidth, GameConfig.Debug.PanelMinHeight)
	limit.Parent = window
	UITheme.pad(window, S.MD)

	-- header: drag it to move the window
	local header = Instance.new("Frame")
	header.BackgroundTransparency = 1
	header.Size = UDim2.new(1, 0, 0, 30)
	header.Parent = window
	local title = UIKit.label(header, "DEVELOPER", 18, "ACCENT")
	title.Size = UDim2.new(1, -90, 1, 0)
	title.Font = UITheme.HeaderFont
	local hint = UIKit.label(
		header,
		`{GameConfig.Debug.PanelKey} to toggle . drag to move . corner to resize`,
		12,
		"MUTED"
	)
	hint.Position = UDim2.fromOffset(130, 0)
	hint.Size = UDim2.new(1, -230, 1, 0)
	local close = UIKit.button(header, "Close", "GHOST", toggle)
	close.TextSize = 13
	close.AnchorPoint = Vector2.new(1, 0)
	close.Position = UDim2.fromScale(1, 0)
	close.Size = UDim2.fromOffset(70, 28)

	local dragFrom: Vector2? = nil
	local startPos: UDim2? = nil
	header.InputBegan:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			dragFrom = Vector2.new(input.Position.X, input.Position.Y)
			startPos = window.Position
		end
	end)
	UserInputService.InputChanged:Connect(function(input)
		if
			dragFrom
			and startPos
			and (
				input.UserInputType == Enum.UserInputType.MouseMovement
				or input.UserInputType == Enum.UserInputType.Touch
			)
		then
			local d = Vector2.new(input.Position.X, input.Position.Y) - dragFrom
			window.Position = startPos + UDim2.fromOffset(d.X, d.Y)
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			dragFrom = nil
		end
	end)

	-- Corner grip: drag the bottom-right corner to resize. The window is
	-- anchored top-right, so growing it wider also moves the right edge by
	-- the same amount, which keeps the grip under the cursor.
	local grip = Instance.new("TextButton")
	grip.Name = "ResizeGrip"
	grip.AutoButtonColor = false
	grip.BackgroundTransparency = 1
	grip.Text = "◢"
	grip.TextSize = 16
	grip.Font = UITheme.LabelFont
	grip.TextColor3 = UITheme.TextMuted
	grip.AnchorPoint = Vector2.new(1, 1)
	grip.Position = UDim2.new(1, S.MD - S.XS, 1, S.MD - S.XS)
	grip.Size = UDim2.fromOffset(20, 20)
	grip.ZIndex = 5
	grip.Parent = window
	grip.MouseEnter:Connect(function()
		grip.TextColor3 = UITheme.AccentGold
	end)
	grip.MouseLeave:Connect(function()
		grip.TextColor3 = UITheme.TextMuted
	end)

	local resizeFrom: Vector2? = nil
	local startSize: Vector2 = Vector2.zero
	local startRight: UDim2 = window.Position
	grip.InputBegan:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			resizeFrom = Vector2.new(input.Position.X, input.Position.Y)
			startSize = window.AbsoluteSize
			startRight = window.Position
		end
	end)
	UserInputService.InputChanged:Connect(function(input)
		if
			resizeFrom
			and (
				input.UserInputType == Enum.UserInputType.MouseMovement
				or input.UserInputType == Enum.UserInputType.Touch
			)
		then
			local viewport = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize
				or Vector2.new(WIDTH, HEIGHT)
			local d = Vector2.new(input.Position.X, input.Position.Y) - resizeFrom
			local w = math.clamp(startSize.X + d.X, GameConfig.Debug.PanelMinWidth, viewport.X)
			local h = math.clamp(startSize.Y + d.Y, GameConfig.Debug.PanelMinHeight, viewport.Y)
			window.Size = UDim2.fromOffset(w, h)
			window.Position = startRight + UDim2.fromOffset(w - startSize.X, 0)
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			resizeFrom = nil
		end
	end)

	-- the command bar
	local field
	field, bar = UIKit.textbox(window, "/command -- Tab completes, Enter runs, Up/Down history", 15)
	field.Position = UDim2.fromOffset(0, 36)
	field.Size = UDim2.new(1, -86, 0, 38)
	local go = UIKit.button(window, "Run", "PRIMARY", function()
		runLine(bar.Text)
		bar.Text = ""
	end)
	go.AnchorPoint = Vector2.new(1, 0)
	go.Position = UDim2.new(1, 0, 0, 36)
	go.Size = UDim2.fromOffset(78, 38)

	-- body: category tabs | command cards
	local top = 36 + 38 + S.SM
	tabsFrame = scroller(window)
	tabsFrame.Position = UDim2.fromOffset(0, top)
	tabsFrame.Size = UDim2.new(0, TAB_WIDTH, 1, -(top + LOG_HEIGHT + S.SM))
	UIKit.list(tabsFrame, S.XS)
	for i, cat in DevCommands.Categories do
		local b = UIKit.button(tabsFrame, cat.Label, "GHOST", function()
			showCategory(cat.Id)
		end)
		b.TextSize = 14
		b.LayoutOrder = i
		b.Size = UDim2.new(1, -S.SM, 0, 34)
		tabButtons[cat.Id] = b
		-- UIKit's hover-out tween restores the plain colour; put the selection back after it
		b.MouseLeave:Connect(function()
			task.delay(UITheme.Motion.Quick + 0.05, paintTabs)
		end)
	end

	cardsFrame = scroller(window)
	cardsFrame.Position = UDim2.fromOffset(TAB_WIDTH + S.SM, top)
	cardsFrame.Size = UDim2.new(1, -(TAB_WIDTH + S.SM), 1, -(top + LOG_HEIGHT + S.SM))
	UIKit.list(cardsFrame, S.SM)

	-- the output log
	local logBack = UIKit.surface(window, "RAISED")
	logBack.AnchorPoint = Vector2.new(0, 1)
	logBack.Position = UDim2.fromScale(0, 1)
	logBack.Size = UDim2.new(1, 0, 0, LOG_HEIGHT)
	logFrame = scroller(logBack)
	logFrame.Size = UDim2.new(1, -S.SM * 2, 1, -S.SM * 2)
	logFrame.Position = UDim2.fromOffset(S.SM, S.SM)
	UIKit.list(logFrame, 2)

	-- suggestions float over the body, under the bar
	suggestFrame = UIKit.surface(window, "RAISED")
	suggestFrame.Position = UDim2.fromOffset(0, 36 + 38 + 2)
	suggestFrame.Size = UDim2.new(1, -86, 0, 0)
	suggestFrame.AutomaticSize = Enum.AutomaticSize.Y
	suggestFrame.BackgroundTransparency = 0.04
	suggestFrame.ZIndex = 20
	suggestFrame.Visible = false
	UITheme.pad(suggestFrame, S.XS)
	UIKit.list(suggestFrame, 2)

	-- bar behaviour
	bar:GetPropertyChangedSignal("Text"):Connect(function()
		if bar:IsFocused() then
			refreshSuggestions()
		end
	end)
	bar.Focused:Connect(refreshSuggestions)
	bar.FocusLost:Connect(function(enter)
		if enter then
			runLine(bar.Text)
			bar.Text = ""
			hideSuggestions()
		else
			task.delay(0.2, function() -- let a click on a suggestion land first
				if not bar:IsFocused() then
					hideSuggestions()
				end
			end)
		end
	end)

	UserInputService.InputBegan:Connect(function(input, _processed)
		if
			input.KeyCode == (Enum.KeyCode :: any)[GameConfig.Debug.PanelKey]
			and not bar:IsFocused()
		then
			toggle()
			return
		end
		if not bar:IsFocused() then
			return
		end
		if input.KeyCode == Enum.KeyCode.Tab then
			if accept() then
				task.defer(function() -- the Tab itself lands in the box; take it back out
					bar.Text = string.gsub(bar.Text, "\t", "")
					bar.CursorPosition = #bar.Text + 1
				end)
			end
		elseif input.KeyCode == Enum.KeyCode.Down then
			if #suggestions > 0 then
				highlighted = highlighted % #suggestions + 1
				drawSuggestions()
			end
		elseif input.KeyCode == Enum.KeyCode.Up then
			if #suggestions > 0 and bar.Text ~= "" then
				highlighted = (highlighted - 2) % #suggestions + 1
				drawSuggestions()
			elseif #history > 0 then
				historyAt = math.max(1, historyAt - 1)
				bar.Text = history[historyAt]
				bar.CursorPosition = #bar.Text + 1
			end
		end
	end)

	DebugCommands.onOutput(log)
	DebugCommands.bindPanel(toggle, clearLog)
	showCategory(currentCategory)
end

function DevPanel.init(): ()
	if not GameConfig.Debug.AllowCommands then
		return
	end
	-- The same gate DebugSystem applies to every SERVER command: Studio, or the
	-- place's creator. Anyone else never sees the panel at all.
	local creator = game.CreatorType == Enum.CreatorType.User and player.UserId == game.CreatorId
	if not RunService:IsStudio() and not creator then
		return
	end
	build()
end

return DevPanel
