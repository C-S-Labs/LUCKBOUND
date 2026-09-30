--!strict
-- THE FATE READOUT, SIGIL style: a small ring holding the Fate level, with a
-- hairline progress bar beside it. Gold, because it is progression. Always on
-- screen; fed by StateController like the old header in HubMenu (which goes
-- away when the hub menu is rebuilt).

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local StateController = require(script.Parent.Parent.Controllers.StateController)
local Sigil = require(script.Parent.Sigil.Sigil)
local Style = require(script.Parent.Sigil.SigilStyle)

local FateHud = {}

local RING = 88
local BAR_WIDTH = 230

function FateHud.init(): ()
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundFateHud"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = -1
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

	local root = Instance.new("Frame")
	root.BackgroundTransparency = 1
	root.Position = UDim2.fromOffset(24, 64)
	root.Size = UDim2.fromOffset(RING + 16 + BAR_WIDTH, RING)
	root.Parent = gui

	local ringBox = Instance.new("Frame")
	ringBox.BackgroundTransparency = 1
	ringBox.Size = UDim2.fromOffset(RING, RING)
	ringBox.Parent = root
	Sigil.ring(ringBox, UDim2.fromScale(1, 1), "fate", 1, 0.2)
	Sigil.ring(ringBox, UDim2.fromScale(0.78, 0.78), "fate", 1, 0.75)

	local level = Instance.new("TextLabel")
	level.BackgroundTransparency = 1
	level.Size = UDim2.fromScale(1, 1)
	level.Font = Style.Fonts.Display
	level.TextSize = 28
	level.TextColor3 = Style.tone("fate")
	level.Text = "1"
	level.Parent = ringBox

	local caption = Instance.new("TextLabel")
	caption.BackgroundTransparency = 1
	caption.Position = UDim2.fromOffset(RING + 16, RING / 2 - 26)
	caption.Size = UDim2.fromOffset(BAR_WIDTH, 20)
	caption.Font = Style.Fonts.Label
	caption.TextSize = 17
	caption.TextColor3 = Style.TextMuted
	caption.TextXAlignment = Enum.TextXAlignment.Left
	caption.Text = "FATE"
	caption.Parent = root

	local track = Instance.new("Frame")
	track.BackgroundColor3 = Style.Violet
	track.BackgroundTransparency = 0.6
	track.BorderSizePixel = 0
	track.Position = UDim2.fromOffset(RING + 16, RING / 2 + 2)
	track.Size = UDim2.fromOffset(BAR_WIDTH, 4)
	track.Parent = root
	local fill = Instance.new("Frame")
	fill.BackgroundColor3 = Style.tone("fate")
	fill.BorderSizePixel = 0
	fill.Size = UDim2.fromScale(0, 1)
	fill.Parent = track

	StateController.onChanged(function(snapshot)
		level.Text = tostring(snapshot.FateLevel)
		local color = Style.tone("fate")
		level.TextColor3 = color
		fill.BackgroundColor3 = color
		TweenService:Create(fill, TweenInfo.new(Style.Motion.Slow, Style.Ease), {
			Size = UDim2.fromScale(math.clamp(snapshot.Progress or 0, 0, 1), 1),
		}):Play()
	end)
end

return FateHud
