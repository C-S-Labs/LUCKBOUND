--!strict
-- THE VITALS BARS: stamina today; health and weapon charge join it when
-- weapons land, as more rows built by the same `bar` function.
--
-- House style, not a new one: a panel-coloured track with the theme's stroke
-- and full rounding, a gold fill lit by the panel gradient, amber when low.
-- Behind the fill sits a pale "lag" bar that holds the old value for a beat
-- and then drains down to the new one, so a spend reads as a chunk taken
-- out rather than a number changing -- the one Souls detail worth copying.
--
-- Visibility follows the profile: in the hub the bar fades in only when
-- stamina is spent (a lobby should not look like a survival game); in an
-- expedition it stays up, because there stamina is the fight.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local UITheme = require(Root.Core.UITheme)

local Vitals = {}

-- Geometry, in pixels. Sits where the old sprint pip sat, under the roll
-- prompt and clear of the expedition toast.
local BAR_WIDTH = 280
local BAR_HEIGHT = 8
local BOTTOM_MARGIN = 26
-- Seconds the lag bar holds the old value before draining, and how long the
-- drain takes.
local LAG_HOLD_SECONDS = 0.35
local LAG_DRAIN_SECONDS = 0.45
-- Below this fraction the fill turns amber.
local LOW_FRACTION = 0.25

type Bar = {
	Track: Frame,
	Fill: Frame,
	Lag: Frame,
	Stroke: UIStroke,
	Value: number,
	LagValue: number,
	LagHoldUntil: number,
	Shown: boolean,
}

local gui: ScreenGui? = nil
local stamina: Bar? = nil

local function tweenInfo(seconds: number): TweenInfo
	return TweenInfo.new(seconds, UITheme.Motion.EaseStyle, UITheme.Motion.EaseDirection)
end

--- One bar. `order` stacks bars upward from the bottom (0 = lowest), so
--- health can sit above stamina without either knowing about the other.
local function bar(name: string, order: number, fillColor: Color3): Bar
	local track = Instance.new("Frame")
	track.Name = name
	track.AnchorPoint = Vector2.new(0.5, 1)
	track.Position =
		UDim2.new(0.5, 0, 1, -(BOTTOM_MARGIN + order * (BAR_HEIGHT + UITheme.Space.SM)))
	track.Size = UDim2.fromOffset(BAR_WIDTH, BAR_HEIGHT)
	track.BackgroundColor3 = UITheme.PanelColor
	track.BackgroundTransparency = 1
	track.BorderSizePixel = 0
	track.ClipsDescendants = true
	track.Parent = gui
	UITheme.corner(track, UDim.new(1, 0))
	local stroke = UITheme.stroke(track, nil, 1)
	stroke.Transparency = 1

	local lag = Instance.new("Frame")
	lag.Name = "Lag"
	lag.Size = UDim2.fromScale(1, 1)
	lag.BackgroundColor3 = UITheme.TextPrimary
	lag.BackgroundTransparency = 1
	lag.BorderSizePixel = 0
	lag.Parent = track
	UITheme.corner(lag, UDim.new(1, 0))

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = fillColor
	fill.BackgroundTransparency = 1
	fill.BorderSizePixel = 0
	fill.Parent = track
	UITheme.corner(fill, UDim.new(1, 0))
	UITheme.gradient(fill, 0.22)

	return {
		Track = track,
		Fill = fill,
		Lag = lag,
		Stroke = stroke,
		Value = 1,
		LagValue = 1,
		LagHoldUntil = 0,
		Shown = false,
	}
end

local function setShown(b: Bar, shown: boolean)
	if b.Shown == shown then
		return
	end
	b.Shown = shown
	local seconds = if shown then UITheme.Motion.Quick else UITheme.Motion.Slow
	local info = tweenInfo(seconds)
	TweenService:Create(b.Track, info, {
		BackgroundTransparency = if shown then UITheme.PanelTransparency + 0.2 else 1,
	}):Play()
	TweenService:Create(b.Stroke, info, {
		Transparency = if shown then UITheme.StrokeTransparency + 0.1 else 1,
	}):Play()
	TweenService:Create(b.Fill, info, { BackgroundTransparency = if shown then 0 else 1 }):Play()
	TweenService:Create(b.Lag, info, { BackgroundTransparency = if shown then 0.55 else 1 }):Play()
end

local function setValue(b: Bar, fraction: number, now: number, dt: number, fillColor: Color3)
	fraction = math.clamp(fraction, 0, 1)
	if fraction < b.Value then
		-- A spend: the lag bar keeps the old value for a beat.
		if b.LagValue < b.Value then
			b.LagValue = b.Value
		end
		b.LagHoldUntil = now + LAG_HOLD_SECONDS
	end
	b.Value = fraction

	if fraction >= b.LagValue then
		b.LagValue = fraction
	elseif now >= b.LagHoldUntil then
		b.LagValue = math.max(fraction, b.LagValue - dt / LAG_DRAIN_SECONDS)
	end

	b.Fill.Size = UDim2.fromScale(fraction, 1)
	b.Lag.Size = UDim2.fromScale(b.LagValue, 1)
	b.Fill.BackgroundColor3 = if fraction < LOW_FRACTION then UITheme.AccentWarn else fillColor
end

function Vitals.init(): ()
	local screen = Instance.new("ScreenGui")
	screen.Name = "LuckboundVitals"
	screen.ResetOnSpawn = false
	screen.IgnoreGuiInset = true
	screen.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screen.DisplayOrder = -1
	screen.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	gui = screen

	stamina = bar("Stamina", 0, UITheme.AccentGold)
end

--- Called every frame by the movement controller. `alwaysShown` is true in
--- an expedition; in the hub the bar shows only while stamina is spent.
function Vitals.setStamina(fraction: number, alwaysShown: boolean, now: number, dt: number): ()
	local b = stamina
	if not b then
		return
	end
	setValue(b, fraction, now, dt, UITheme.AccentGold)
	setShown(b, alwaysShown or fraction < 0.999 or b.LagValue > fraction + 1e-3)
end

return Vitals
