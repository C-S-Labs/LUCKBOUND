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
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)
local UIKit = require(script.Parent.UIKit)

local Leaderboard = {}

local CONFIG = GameConfig.Leaderboard
local HEADER_HEIGHT = 34

local player = Players.LocalPlayer
local panel: Frame
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
	panel.Size = UDim2.fromOffset(
		CONFIG.Width,
		HEADER_HEIGHT + UITheme.Space.SM * 2 + visible * (CONFIG.RowHeight + gap)
	)
end

local function addRow(who: Player)
	if rows[who] then
		return
	end
	local frame = UIKit.surface(body, "RAISED")
	frame.Size = UDim2.new(1, 0, 0, CONFIG.RowHeight)
	local inner = Instance.new("Frame")
	inner.BackgroundTransparency = 1
	inner.Position = UDim2.fromOffset(UITheme.Space.SM, 0)
	inner.Size = UDim2.new(1, -UITheme.Space.SM * 2, 1, 0)
	inner.Parent = frame

	local texts = table.create(#CONFIG.Columns, "")
	local cells = layCells(inner, texts, 14)
	if who == player then
		-- You are gold, everyone else is white: find yourself at a glance.
		for _, cell in cells do
			cell.TextColor3 = UITheme.AccentGold
			cell.Font = UITheme.LabelFont
		end
	end
	cells[1].TextColor3 = if who == player then UITheme.AccentGold else UITheme.TextMuted

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
		row.conn:Disconnect()
		row.frame:Destroy()
		rows[who] = nil
		refresh()
	end
end

local function setOpen(value: boolean)
	open = value
	panel.Visible = value
end

local function build()
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundLeaderboard"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 4
	gui.Parent = player:WaitForChild("PlayerGui")

	panel = UIKit.surface(gui, "PANEL")
	panel.Name = "Panel"
	panel.AnchorPoint = Vector2.new(1, 0)
	panel.Position = UDim2.new(1, -UITheme.Space.MD, 0, UITheme.Space.MD)
	UITheme.pad(panel, UITheme.Space.SM)

	local header = Instance.new("Frame")
	header.BackgroundTransparency = 1
	header.Size = UDim2.new(1, 0, 0, HEADER_HEIGHT - UITheme.Space.SM)
	header.Parent = panel

	local title = UIKit.label(header, CONFIG.Title, 13, "ACCENT")
	title.Font = UITheme.HeaderFont
	title.Position = UDim2.fromOffset(UITheme.Space.SM, 0)
	title.Size = UDim2.new(1, -110, 0, 16)

	countLabel = UIKit.label(header, "0", 13, "MUTED")
	countLabel.AnchorPoint = Vector2.new(1, 0)
	countLabel.Position = UDim2.new(1, -UITheme.Space.SM, 0, 0)
	countLabel.Size = UDim2.fromOffset(100, 16)
	countLabel.TextXAlignment = Enum.TextXAlignment.Right

	local headings = Instance.new("Frame")
	headings.BackgroundTransparency = 1
	headings.Position = UDim2.fromOffset(UITheme.Space.SM, 16)
	headings.Size = UDim2.new(1, -UITheme.Space.SM * 2, 0, 12)
	headings.Parent = header
	local texts = {}
	for i, column in CONFIG.Columns do
		texts[i] = column.Header
	end
	layCells(headings, texts, 10, "MUTED")

	local divider = UIKit.divider(panel)
	divider.Position = UDim2.fromOffset(0, HEADER_HEIGHT - UITheme.Space.SM)

	body = Instance.new("ScrollingFrame")
	body.BackgroundTransparency = 1
	body.BorderSizePixel = 0
	body.Position = UDim2.fromOffset(0, HEADER_HEIGHT)
	body.Size = UDim2.new(1, 0, 1, -HEADER_HEIGHT)
	body.ScrollBarThickness = 3
	body.ScrollBarImageColor3 = UITheme.AccentGold
	body.Parent = panel
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
