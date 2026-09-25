--!strict
-- THE WIDGET LIBRARY. Every hub screen is built from these, so there is one
-- button in the game rather than one per panel.
--
-- The rule it exists to enforce: NO SCREEN INVENTS A NUMBER. Colour, radius,
-- padding, font and tween length all come from UITheme; behaviour numbers come
-- from GameConfig. A literal in a UI module is the same violation as a magic
-- number in a System (CLAUDE.md rule 4) -- it is just harder to spot, because
-- a slightly-wrong shade of purple does not throw.
--
-- It also owns the accessibility contract in one place: every tween goes
-- through UIKit.tween, which collapses to near-zero duration when the player
-- has turned Reduce Motion on. A tween built directly with TweenService would
-- quietly opt that player back in.

local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local UITheme = require(Root.Core.UITheme)

local StateController = require(script.Parent.Parent.Controllers.StateController)
local ThemeController = require(script.Parent.Parent.Controllers.ThemeController)

local UIKit = {}

-- Reduce Motion does not mean "no motion": a state change with no transition
-- at all is harder to follow, not easier. It means "short enough not to
-- swim".
local REDUCED_SECONDS = 0.05

--- Seconds as M:SS. Clamped at zero -- two copies of this existed and only
--- one clamped, so a countdown that overran rendered "-1:-30" in one place
--- and "0:00" in the other.
function UIKit.formatClock(seconds: number): string
	local whole = math.max(0, math.floor(seconds))
	return string.format("%d:%02d", whole // 60, whole % 60)
end

function UIKit.reduceMotion(): boolean
	return StateController.setting("ReduceMotion") == true
end

function UIKit.duration(seconds: number): number
	if UIKit.reduceMotion() then
		return math.min(seconds, REDUCED_SECONDS)
	end
	return seconds
end

--- The only tween in the hub UI. `exiting` picks the reverse easing, which is
--- what stops a panel feeling rubbery on the way out.
function UIKit.tween(
	object: Instance,
	seconds: number,
	properties: { [string]: any },
	exiting: boolean?
): Tween
	local motion = UITheme.Motion
	local info = TweenInfo.new(
		UIKit.duration(seconds),
		if exiting then motion.ExitStyle else motion.EaseStyle,
		if exiting then motion.ExitDirection else motion.EaseDirection
	)
	local tween = TweenService:Create(object, info, properties)
	tween:Play()
	return tween
end

--- A surface: the panel/rail/raised background with its corner, stroke and
--- gradient already on it.
---
--- Surfaces are the ONLY thing that carries the live tint (ThemeController).
--- Buttons deliberately keep a fixed raised colour: they own hover and press
--- states that tween their own background, and a tint arriving mid-hover
--- would fight those. The rail and panel behind them are what shift, which is
--- the whole effect anyway.
function UIKit.surface(parent: Instance, kind: string): Frame
	local frame = Instance.new("Frame")
	frame.BorderSizePixel = 0

	local token: string
	if kind == "RAIL" then
		token = "RailColor"
		frame.BackgroundTransparency = UITheme.RailTransparency
	elseif kind == "RAISED" then
		token = "RaisedColor"
		frame.BackgroundTransparency = UITheme.RaisedTransparency
	else
		token = "PanelColor"
		frame.BackgroundTransparency = UITheme.PanelTransparency
	end
	frame.BackgroundColor3 = (UITheme :: any)[token]

	frame.Parent = parent
	UITheme.corner(frame, if kind == "RAISED" then UITheme.RadiusSmall else UITheme.RadiusLarge)
	UITheme.gradient(frame)
	local stroke = UITheme.stroke(frame)
	stroke.Transparency = UITheme.StrokeTransparency

	ThemeController.register(frame, "BackgroundColor3", token)
	-- The stroke is the half that reads best: a 1px edge picking up the local
	-- colour says "this room" without repainting the room.
	ThemeController.register(stroke, "Color", "StrokeColor")

	return frame
end

--- A text label, themed. `role` is PRIMARY, SECONDARY, MUTED or ACCENT.
function UIKit.label(parent: Instance, text: string, size: number, role: string?): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Font = UITheme.BodyFont
	label.Text = text
	label.TextSize = size
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextWrapped = true
	label.RichText = true

	if role == "ACCENT" then
		label.TextColor3 = UITheme.AccentGold
		label.Font = UITheme.LabelFont
	elseif role == "SECONDARY" then
		label.TextColor3 = UITheme.TextSecondary
	elseif role == "MUTED" then
		label.TextColor3 = UITheme.TextMuted
	else
		label.TextColor3 = UITheme.TextPrimary
	end

	label.Parent = parent
	return label
end

--- A button with the hover, press and disabled states already wired, because
--- a button that does not react to a cursor is the single clearest tell that
--- a UI was not finished.
---
--- `style` is PRIMARY (gold fill), GHOST (stroke only) or DANGER.
function UIKit.button(
	parent: Instance,
	text: string,
	style: string?,
	onClick: (() -> ())?
): TextButton
	local button = Instance.new("TextButton")
	button.AutoButtonColor = false
	button.BorderSizePixel = 0
	button.Font = UITheme.LabelFont
	button.Text = text
	button.TextSize = 16
	button.Size = UDim2.new(1, 0, 0, 44)

	local base: Color3
	local hover: Color3
	if style == "PRIMARY" then
		base = UITheme.AccentGold
		hover = UITheme.AccentGold:Lerp(Color3.new(1, 1, 1), 0.18)
		button.TextColor3 = UITheme.BackgroundColor
	elseif style == "DANGER" then
		base = UITheme.AccentWarn
		hover = UITheme.AccentWarn:Lerp(Color3.new(1, 1, 1), 0.18)
		button.TextColor3 = UITheme.BackgroundColor
	else
		base = UITheme.RaisedColor
		hover = UITheme.RaisedColor:Lerp(UITheme.AccentGold, 0.16)
		button.TextColor3 = UITheme.TextPrimary
	end

	button.BackgroundColor3 = base
	button.Parent = parent
	UITheme.corner(button, UITheme.RadiusSmall)
	if style ~= "PRIMARY" and style ~= "DANGER" then
		UITheme.stroke(button)
	end

	button.MouseEnter:Connect(function()
		if button.Active then
			UIKit.tween(button, UITheme.Motion.Instant, { BackgroundColor3 = hover })
		end
	end)
	button.MouseLeave:Connect(function()
		UIKit.tween(button, UITheme.Motion.Quick, { BackgroundColor3 = base }, true)
	end)
	-- THE PRESS ANIMATION MUST RESTORE THE BUTTON'S OWN SIZE, NOT THE DEFAULT.
	--
	-- This released with the release tween hard-coded to UDim2.new(1, 0, 0, 44)
	-- -- the size the constructor happens to start with. Every caller that
	-- resizes its button afterwards (the travel rows are 104x38) therefore had
	-- it snap to full width on the first click and stay there, covering the
	-- label it sat next to. Reported from the first Studio walk of the menu,
	-- and visible in a screenshot as four rows of nothing but TRAVEL.
	--
	-- The resting size is captured at press time rather than at construction,
	-- so a button that is resized or re-laid out later still returns to
	-- wherever it currently belongs.
	local restingSize: UDim2? = nil

	local function press()
		if restingSize == nil then
			restingSize = button.Size
		end
		-- A press is a shrink, not a flash: it reads on a phone, where there
		-- is no cursor to show a hover in the first place.
		UIKit.tween(button, UITheme.Motion.Instant, {
			Size = (restingSize :: UDim2) - UDim2.fromOffset(0, 3),
		})
	end

	local function release()
		if restingSize == nil then
			return
		end
		UIKit.tween(button, UITheme.Motion.Quick, { Size = restingSize :: UDim2 })
		restingSize = nil
	end

	button.MouseButton1Down:Connect(press)
	button.MouseButton1Up:Connect(release)
	-- Dragging off a pressed button must also let it go, or it stays shrunk
	-- until the next click.
	button.MouseLeave:Connect(release)

	if onClick then
		button.Activated:Connect(function()
			if button.Active then
				onClick()
			end
		end)
	end

	return button
end

--- Greys a button out without hiding it, so a disabled action still explains
--- itself instead of vanishing.
function UIKit.setEnabled(button: TextButton, enabled: boolean): ()
	button.Active = enabled
	button.AutoButtonColor = false
	UIKit.tween(
		button,
		UITheme.Motion.Quick,
		{ BackgroundTransparency = if enabled then 0 else 0.55 }
	)
	button.TextTransparency = if enabled then 0 else 0.4
end

--- A vertical list layout with the theme's gap.
function UIKit.list(parent: Instance, gap: number?): UIListLayout
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Vertical
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Padding = UDim.new(0, gap or UITheme.Space.SM)
	layout.Parent = parent
	return layout
end

--- A horizontal rule.
function UIKit.divider(parent: Instance): Frame
	local line = Instance.new("Frame")
	line.BackgroundColor3 = UITheme.DividerColor
	line.BackgroundTransparency = 0.6
	line.BorderSizePixel = 0
	line.Size = UDim2.new(1, 0, 0, 1)
	line.Parent = parent
	return line
end

--- A labelled on/off switch.
function UIKit.toggle(
	parent: Instance,
	text: string,
	value: boolean,
	onChanged: (boolean) -> ()
): Frame
	local row = UIKit.surface(parent, "RAISED")
	row.Size = UDim2.new(1, 0, 0, 44)

	local label = UIKit.label(row, text, 15)
	label.Position = UDim2.fromOffset(UITheme.Space.MD, 0)
	label.Size = UDim2.new(1, -80, 1, 0)

	local track = Instance.new("TextButton")
	track.AnchorPoint = Vector2.new(1, 0.5)
	track.Position = UDim2.new(1, -UITheme.Space.MD, 0.5, 0)
	track.Size = UDim2.fromOffset(46, 24)
	track.Text = ""
	track.AutoButtonColor = false
	track.BorderSizePixel = 0
	track.BackgroundColor3 = if value then UITheme.AccentGold else UITheme.BackgroundColor
	track.Parent = row
	UITheme.corner(track, UDim.new(0, 12))

	local knob = Instance.new("Frame")
	knob.AnchorPoint = Vector2.new(0, 0.5)
	knob.Position = UDim2.new(0, if value then 24 else 3, 0.5, 0)
	knob.Size = UDim2.fromOffset(19, 19)
	knob.BackgroundColor3 = UITheme.TextPrimary
	knob.BorderSizePixel = 0
	knob.Parent = track
	UITheme.corner(knob, UDim.new(0, 10))

	local current = value
	track.Activated:Connect(function()
		current = not current
		UIKit.tween(track, UITheme.Motion.Quick, {
			BackgroundColor3 = if current then UITheme.AccentGold else UITheme.BackgroundColor,
		})
		UIKit.tween(knob, UITheme.Motion.Quick, {
			Position = UDim2.new(0, if current then 24 else 3, 0.5, 0),
		})
		onChanged(current)
	end)

	return row
end

--- A labelled slider. Drag or click anywhere on the track.
function UIKit.slider(
	parent: Instance,
	text: string,
	value: number,
	min: number,
	max: number,
	onChanged: (number) -> ()
): Frame
	local row = UIKit.surface(parent, "RAISED")
	row.Size = UDim2.new(1, 0, 0, 62)

	local label = UIKit.label(row, text, 15)
	label.Position = UDim2.fromOffset(UITheme.Space.MD, UITheme.Space.SM)
	label.Size = UDim2.new(1, -UITheme.Space.MD * 2, 0, 18)

	local readout = UIKit.label(row, "", 13, "MUTED")
	readout.Position = UDim2.new(1, -70, 0, UITheme.Space.SM)
	readout.Size = UDim2.fromOffset(56, 18)
	readout.TextXAlignment = Enum.TextXAlignment.Right

	local track = Instance.new("TextButton")
	track.Position = UDim2.new(0, UITheme.Space.MD, 0, 38)
	track.Size = UDim2.new(1, -UITheme.Space.MD * 2, 0, 8)
	track.Text = ""
	track.AutoButtonColor = false
	track.BorderSizePixel = 0
	track.BackgroundColor3 = UITheme.BackgroundColor
	track.Parent = row
	UITheme.corner(track, UDim.new(0, 4))

	local fill = Instance.new("Frame")
	fill.BackgroundColor3 = UITheme.AccentGold
	fill.BorderSizePixel = 0
	fill.Size = UDim2.fromScale((value - min) / math.max(max - min, 1e-6), 1)
	fill.Parent = track
	UITheme.corner(fill, UDim.new(0, 4))

	local function setFromScale(scale: number)
		scale = math.clamp(scale, 0, 1)
		local resolved = min + (max - min) * scale
		fill.Size = UDim2.fromScale(scale, 1)
		readout.Text = string.format("%d%%", math.round(scale * 100))
		onChanged(resolved)
	end

	readout.Text =
		string.format("%d%%", math.round((value - min) / math.max(max - min, 1e-6) * 100))

	local dragging = false
	local function updateFromInput(input: InputObject)
		local scale = (input.Position.X - track.AbsolutePosition.X)
			/ math.max(track.AbsoluteSize.X, 1)
		setFromScale(scale)
	end

	track.InputBegan:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			dragging = true
			updateFromInput(input)
		end
	end)
	track.InputChanged:Connect(function(input)
		if
			dragging
			and (
				input.UserInputType == Enum.UserInputType.MouseMovement
				or input.UserInputType == Enum.UserInputType.Touch
			)
		then
			updateFromInput(input)
		end
	end)
	track.InputEnded:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			dragging = false
		end
	end)

	return row
end

--- A "not built yet" strip. Every PREVIEW panel wears one, because a designed
--- screen with placeholder data and no label is indistinguishable from a
--- broken screen with real data.
function UIKit.previewBadge(parent: Instance, text: string): Frame
	local badge = Instance.new("Frame")
	badge.BackgroundColor3 = UITheme.AccentCool
	badge.BackgroundTransparency = 0.82
	badge.BorderSizePixel = 0
	badge.Size = UDim2.new(1, 0, 0, 34)
	badge.Parent = parent
	UITheme.corner(badge, UITheme.RadiusSmall)

	local stroke = UITheme.stroke(badge, UITheme.AccentCool, 1)
	stroke.Transparency = 0.5

	local label = UIKit.label(badge, text, 13)
	label.TextColor3 = UITheme.AccentCool
	label.Size = UDim2.new(1, -UITheme.Space.MD * 2, 1, 0)
	label.Position = UDim2.fromOffset(UITheme.Space.MD, 0)
	label.TextXAlignment = Enum.TextXAlignment.Center

	return badge
end

--- Fades a frame in from `SlideOffset` pixels below its resting place.
--- Everything that appears in the hub UI appears this way.
function UIKit.revealFrom(frame: GuiObject, restingPosition: UDim2, delay: number?): ()
	local offset = UITheme.Motion.SlideOffset
	frame.Position = restingPosition + UDim2.fromOffset(0, offset)
	frame.BackgroundTransparency = 1
	frame.Visible = true

	task.delay(UIKit.duration(delay or 0), function()
		if frame.Parent then
			UIKit.tween(frame, UITheme.Motion.Normal, {
				Position = restingPosition,
				BackgroundTransparency = UITheme.PanelTransparency,
			})
		end
	end)
end

return UIKit
