--!strict
-- The player list, in the house style. Replaces Roblox's CoreGui one.
--
-- THE COLUMNS ARE DATA (GameConfig.Leaderboard.Columns). A column reads
-- either a built-in ("RANK", "NAME") or any Player attribute, and a row
-- redraws whenever one of its player's attributes changes. So a new stat is
-- the server setting an attribute plus one config row. This file does not
-- change.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local GuiService = game:GetService("GuiService")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)
local UIKit = require(script.Parent.UIKit)
local Sigil = require(script.Parent.Sigil.Sigil)
local Style = require(script.Parent.Sigil.SigilStyle)

local Leaderboard = {}

local CONFIG = GameConfig.Leaderboard
local HEADER_HEIGHT = 44

local player = Players.LocalPlayer
local gui: ScreenGui
local panel: GuiObject
local menu: Frame? = nil
local menuFor: Player? = nil
local body: ScrollingFrame
local countLabel: TextLabel
local open = CONFIG.StartOpen
local rows: { [Player]: { frame: Frame, cells: { TextLabel }, conn: RBXScriptConnection } } = {}

--- Lays a row of cells across `parent` using the column widths. A Width of 0
--- takes whatever the fixed columns leave.
local function layCells(
	parent: Instance,
	texts: { string },
	size: number,
	role: string?
): { TextLabel }
	local fixed = 0
	for _, column in CONFIG.Columns do
		fixed += column.Width
	end
	local cells = {}
	local x = 0
	for i, column in CONFIG.Columns do
		local cell = UIKit.label(parent, texts[i], size, role)
		cell.TextWrapped = false
		cell.TextTruncate = Enum.TextTruncate.AtEnd
		if column.Width == 0 then
			cell.Size = UDim2.new(1, -fixed, 1, 0)
			cell.Position = UDim2.new(0, x, 0, 0)
		else
			cell.Size = UDim2.new(0, column.Width, 1, 0)
			cell.Position = UDim2.new(0, x, 0, 0)
		end
		cells[i] = cell
		x += column.Width
	end
	-- Anything after the flex column is pushed right by the flex width.
	local afterFlex = false
	for i, column in CONFIG.Columns do
		if afterFlex then
			cells[i].Position += UDim2.new(1, -fixed, 0, 0)
			cells[i].TextXAlignment = Enum.TextXAlignment.Right
		end
		if column.Width == 0 then
			afterFlex = true
		end
	end
	return cells
end

local function cellText(source: string, who: Player, rank: number): string
	if source == "RANK" then
		return tostring(rank)
	elseif source == "NAME" then
		return who.DisplayName
	end
	local value = who:GetAttribute(source)
	return if value == nil then "-" else tostring(value)
end

local function sortedPlayers(): { Player }
	local list = Players:GetPlayers()
	local key = CONFIG.SortBy
	table.sort(list, function(a, b)
		if key then
			local va, vb = tonumber(a:GetAttribute(key)) or 0, tonumber(b:GetAttribute(key)) or 0
			if va ~= vb then
				return va > vb
			end
		end
		return a.DisplayName:lower() < b.DisplayName:lower()
	end)
	return list
end

local function refresh()
	local list = sortedPlayers()
	for rank, who in list do
		local row = rows[who]
		if row then
			row.frame.LayoutOrder = rank
			for i, column in CONFIG.Columns do
				row.cells[i].Text = cellText(column.Source, who, rank)
			end
		end
	end
	countLabel.Text = `{#list} {if #list == 1 then CONFIG.CountSingular else CONFIG.CountPlural}`
	local visible = math.min(#list, CONFIG.MaxVisibleRows)
	local gap = UITheme.Space.XS
	body.CanvasSize = UDim2.fromOffset(0, #list * (CONFIG.RowHeight + gap))
	panel.Size =
		UDim2.fromOffset(CONFIG.Width + 32, HEADER_HEIGHT + 30 + visible * (CONFIG.RowHeight + gap))
end

-- === the player menu ================================================
-- Click a row for the same actions Roblox's own list offers. Every action is
-- Roblox's own prompt (SetCore / InspectPlayerFromUserId), so the player
-- confirms each one in the standard dialog and nothing here can friend or
-- block anyone by itself.

local MENU_WIDTH = 180
local MENU_BUTTON_HEIGHT = 34

local function closeMenu()
	if menu then
		menu:Destroy()
		menu = nil
		menuFor = nil
	end
end

local function prompt(core: string, who: Player)
	closeMenu()
	local ok, err = pcall(StarterGui.SetCore, StarterGui, core, who)
	if not ok then
		warn(`[Leaderboard] {core} failed:`, err)
	end
end

local function isBlocked(who: Player): boolean
	local ok, ids = pcall(StarterGui.GetCore, StarterGui, "GetBlockedUserIds")
	if ok and type(ids) == "table" then
		return table.find(ids, who.UserId) ~= nil
	end
	return false
end

local function openMenu(who: Player, row: Frame)
	if menuFor == who then
		closeMenu()
		return
	end
	closeMenu()
	menuFor = who

	-- A clear layer over the screen: any click outside the menu closes it.
	local scrim = Instance.new("TextButton")
	scrim.Name = "PlayerMenu"
	scrim.BackgroundTransparency = 1
	scrim.Text = ""
	scrim.Size = UDim2.fromScale(1, 1)
	scrim.ZIndex = 10
	scrim.Parent = gui
	scrim.Activated:Connect(closeMenu)
	menu = scrim :: any

	local card = UIKit.surface(scrim, "PANEL")
	card.ZIndex = 11
	card.AnchorPoint = Vector2.new(1, 0)
	-- Beside the leaderboard, level with the row that was clicked.
	card.Position =
		UDim2.fromOffset(panel.AbsolutePosition.X - UITheme.Space.SM, row.AbsolutePosition.Y)
	card.Size = UDim2.fromOffset(MENU_WIDTH, 0)
	card.AutomaticSize = Enum.AutomaticSize.Y
	UITheme.pad(card, UITheme.Space.SM)
	UIKit.list(card, UITheme.Space.XS)

	local name = UIKit.label(card, who.DisplayName, 15, "ACCENT")
	name.Size = UDim2.new(1, 0, 0, 18)
	name.ZIndex = 12
	local handle = UIKit.label(card, `@{who.Name}`, 12, "MUTED")
	handle.Size = UDim2.new(1, 0, 0, 16)
	handle.LayoutOrder = 1
	handle.ZIndex = 12

	local order = 2
	local function action(text: string, style: string?, onClick: () -> ())
		local b = UIKit.button(card, text, style, onClick)
		b.Size = UDim2.new(1, 0, 0, MENU_BUTTON_HEIGHT)
		b.TextSize = 14
		b.LayoutOrder = order
		b.ZIndex = 12
		order += 1
	end

	if who ~= player then
		-- IsFriendsWith yields, so its button arrives a moment after the rest
		-- rather than holding the whole menu back.
		local friendSlot = order
		order += 1
		task.spawn(function()
			local ok, friends = pcall(player.IsFriendsWith, player, who.UserId)
			if menuFor ~= who or not card.Parent then
				return
			end
			local saved = order
			order = friendSlot
			if ok and friends then
				action("Unfriend", "GHOST", function()
					prompt("PromptUnfriend", who)
				end)
			else
				action("Add Friend", "PRIMARY", function()
					prompt("PromptSendFriendRequest", who)
				end)
			end
			order = saved
		end)
	end
	action("View Avatar", "GHOST", function()
		closeMenu()
		pcall(GuiService.InspectPlayerFromUserId, GuiService, who.UserId)
	end)
	if who ~= player then
		if isBlocked(who) then
			action("Unblock", "GHOST", function()
				prompt("PromptUnblockPlayer", who)
			end)
		else
			action("Block", "DANGER", function()
				prompt("PromptBlockPlayer", who)
			end)
		end
	end
end

local function addRow(who: Player)
	if rows[who] then
		return
	end
	local frame = Instance.new("Frame")
	frame.BackgroundColor3 = Style.Indigo
	frame.BackgroundTransparency = 0.85
	frame.BorderSizePixel = 0
	frame.Size = UDim2.new(1, 0, 0, CONFIG.RowHeight)
	frame.Parent = body
	local tick = Instance.new("Frame")
	tick.BackgroundColor3 = Style.tone(if who == player then "fate" else "system")
	tick.BackgroundTransparency = if who == player then 0.1 else 0.7
	tick.BorderSizePixel = 0
	tick.Size = UDim2.new(0, 2, 1, 0)
	tick.Parent = frame
	local inner = Instance.new("Frame")
	inner.BackgroundTransparency = 1
	inner.Position = UDim2.fromOffset(UITheme.Space.SM, 0)
	inner.Size = UDim2.new(1, -UITheme.Space.SM * 2, 1, 0)
	inner.Parent = frame

	local texts = table.create(#CONFIG.Columns, "")
	local cells = layCells(inner, texts, 16)
	if who == player then
		-- You are gold, everyone else is white: find yourself at a glance.
		for _, cell in cells do
			cell.TextColor3 = Style.tone("fate")
			cell.Font = Style.Fonts.Label
		end
	end
	cells[1].TextColor3 = if who == player then Style.tone("fate") else Style.TextMuted

	-- The whole row is the click target, with a gold edge on hover so it
	-- reads as something to press.
	local hit = Instance.new("TextButton")
	hit.BackgroundTransparency = 1
	hit.Text = ""
	hit.Size = UDim2.fromScale(1, 1)
	hit.ZIndex = 3
	hit.Parent = frame
	hit.MouseEnter:Connect(function()
		UIKit.tween(frame, UITheme.Motion.Instant, { BackgroundTransparency = 0.6 })
	end)
	hit.MouseLeave:Connect(function()
		UIKit.tween(frame, UITheme.Motion.Quick, { BackgroundTransparency = 0.85 }, true)
	end)
	hit.Activated:Connect(function()
		openMenu(who, frame)
	end)

	rows[who] = {
		frame = frame,
		cells = cells,
		conn = who.AttributeChanged:Connect(refresh),
	}
	refresh()
end

local function removeRow(who: Player)
	local row = rows[who]
	if row then
		if menuFor == who then
			closeMenu()
		end
		row.conn:Disconnect()
		row.frame:Destroy()
		rows[who] = nil
		refresh()
	end
end

local function setOpen(value: boolean)
	open = value
	panel.Visible = value
	if not value then
		closeMenu()
	end
end

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundLeaderboard"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 4
	gui.Parent = player:WaitForChild("PlayerGui")

	local sigilPanel = Sigil.panel(gui, {
		name = "Panel",
		tone = "system",
		size = UDim2.fromOffset(CONFIG.Width + 32, 100),
		anchor = Vector2.new(1, 0),
		position = UDim2.new(1, -UITheme.Space.MD, 0, UITheme.Space.MD),
	})
	panel = sigilPanel.root
	sigilPanel.open()
	local content = sigilPanel.body

	local header = Instance.new("Frame")
	header.BackgroundTransparency = 1
	header.Size = UDim2.new(1, 0, 0, HEADER_HEIGHT)
	header.Parent = content

	local title = UIKit.label(header, CONFIG.Title, 15, "ACCENT")
	title.Font = Style.Fonts.Display
	title.TextColor3 = Style.tone("fate")
	title.Position = UDim2.fromOffset(UITheme.Space.SM, 0)
	title.Size = UDim2.new(1, -110, 0, 20)

	countLabel = UIKit.label(header, "0", 15, "MUTED")
	countLabel.AnchorPoint = Vector2.new(1, 0)
	countLabel.Position = UDim2.new(1, -UITheme.Space.SM, 0, 0)
	countLabel.Size = UDim2.fromOffset(100, 16)
	countLabel.TextXAlignment = Enum.TextXAlignment.Right

	local headings = Instance.new("Frame")
	headings.BackgroundTransparency = 1
	headings.Position = UDim2.fromOffset(UITheme.Space.SM, 22)
	headings.Size = UDim2.new(1, -UITheme.Space.SM * 2, 0, 14)
	headings.Parent = header
	local texts = {}
	for i, column in CONFIG.Columns do
		texts[i] = column.Header
	end
	layCells(headings, texts, 12, "MUTED")

	local divider = Instance.new("Frame")
	divider.BackgroundColor3 = Style.Violet
	divider.BackgroundTransparency = 0.7
	divider.BorderSizePixel = 0
	divider.Position = UDim2.fromOffset(0, HEADER_HEIGHT - 2)
	divider.Size = UDim2.new(1, 0, 0, 1)
	divider.Parent = content

	body = Instance.new("ScrollingFrame")
	body.BackgroundTransparency = 1
	body.BorderSizePixel = 0
	body.Position = UDim2.fromOffset(0, HEADER_HEIGHT + 4)
	body.Size = UDim2.new(1, 0, 1, -HEADER_HEIGHT - 4)
	body.ScrollBarThickness = 3
	body.ScrollBarImageColor3 = Style.tone("system")
	body.Parent = content
	UIKit.list(body, UITheme.Space.XS)
end

function Leaderboard.init(): ()
	if not CONFIG.Enabled then
		return
	end
	-- SetCoreGuiEnabled can fail for a frame while CoreGui boots.
	task.spawn(function()
		for _ = 1, 10 do
			if
				pcall(StarterGui.SetCoreGuiEnabled, StarterGui, Enum.CoreGuiType.PlayerList, false)
			then
				return
			end
			task.wait(0.5)
		end
	end)

	build()
	for _, who in Players:GetPlayers() do
		addRow(who)
	end
	Players.PlayerAdded:Connect(addRow)
	Players.PlayerRemoving:Connect(removeRow)
	setOpen(open)

	local toggleKey = (Enum.KeyCode :: any)[CONFIG.ToggleKey]
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.KeyCode == toggleKey then
			setOpen(not open)
		end
	end)
end

return Leaderboard
