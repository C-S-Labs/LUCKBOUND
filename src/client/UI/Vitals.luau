--!strict
-- THE VITALS BARS, in the SIGIL style (docs/PLAYER_UI.md; owner 2026-09-28:
-- health above stamina, always on screen). Same API as before -- init,
-- setStamina, setHealth -- so LocomotionController is untouched.
--
-- Thin hairline tracks with a diamond cap on the fill. Health is danger
-- (crimson), stamina is system (cyan) and turns fate-amber when low. A pale
-- "lag" bar holds the old value for a beat then drains, so a spend reads as a
-- chunk taken out. Weapon charge joins later as another row from `bar`.

local Players = game:GetService("Players")

local Style = require(script.Parent.Sigil.SigilStyle)

local Vitals = {}

local BAR_WIDTH = 480
local HEALTH_HEIGHT = 9
local STAMINA_HEIGHT = 6
local BOTTOM_MARGIN = 30
local ROW_GAP = 26
local LAG_HOLD_SECONDS = 0.35
local LAG_DRAIN_SECONDS = 0.45
local LOW_FRACTION = 0.25

type Bar = {
	Fill: Frame,
	Lag: Frame,
	Cap: Frame,
	Tone: string,
	Value: number,
	LagValue: number,
	LagHoldUntil: number,
}

local gui: ScreenGui? = nil
local stamina: Bar? = nil
local health: Bar? = nil

local function bar(name: string, row: number, height: number, tone: string): Bar
	local track = Instance.new("Frame")
	track.Name = name
	track.AnchorPoint = Vector2.new(0.5, 1)
	track.Position = UDim2.new(0.5, 0, 1, -(BOTTOM_MARGIN + row * ROW_GAP))
	track.Size = UDim2.fromOffset(BAR_WIDTH, height)
	track.BackgroundColor3 = Style.Void
	track.BackgroundTransparency = 0.35
	track.BorderSizePixel = 0
	track.Parent = gui
	local edge = Instance.new("UIStroke")
	edge.Color = Style.Violet
	edge.Transparency = 0.7
	edge.Thickness = 1
	edge.Parent = track

	local lag = Instance.new("Frame")
	lag.Name = "Lag"
	lag.Size = UDim2.fromScale(1, 1)
	lag.BackgroundColor3 = Style.TextHigh
	lag.BackgroundTransparency = 0.55
	lag.BorderSizePixel = 0
	lag.Parent = track

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = Style.tone(tone)
	fill.BorderSizePixel = 0
	fill.Parent = track

	local cap = Instance.new("Frame")
	cap.Name = "Cap"
	cap.AnchorPoint = Vector2.new(0.5, 0.5)
	cap.Position = UDim2.fromScale(1, 0.5)
	cap.Size = UDim2.fromOffset(height + 5, height + 5)
	cap.Rotation = 45
	cap.BackgroundColor3 = Style.tone(tone)
	cap.BorderSizePixel = 0
	cap.Parent = track

	local caption = Instance.new("TextLabel")
	caption.BackgroundTransparency = 1
	caption.Text = string.upper(name)
	caption.Font = Style.Fonts.Label
	caption.TextSize = 15
	caption.TextColor3 = Style.TextMuted
	caption.TextXAlignment = Enum.TextXAlignment.Left
	caption.Position = UDim2.fromOffset(0, -20)
	caption.Size = UDim2.new(1, 0, 0, 16)
	caption.Parent = track

	return {
		Fill = fill,
		Lag = lag,
		Cap = cap,
		Tone = tone,
		Value = 1,
		LagValue = 1,
		LagHoldUntil = 0,
	}
end

local function setValue(b: Bar, fraction: number, now: number, dt: number, lowTone: string?)
	fraction = math.clamp(fraction, 0, 1)
	if fraction < b.Value then
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

	local tone = if lowTone and fraction < LOW_FRACTION then lowTone else b.Tone
	local color = Style.tone(tone)
	b.Fill.Size = UDim2.fromScale(fraction, 1)
	b.Lag.Size = UDim2.fromScale(b.LagValue, 1)
	b.Cap.Position = UDim2.fromScale(fraction, 0.5)
	b.Fill.BackgroundColor3 = color
	b.Cap.BackgroundColor3 = color
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

	stamina = bar("Stamina", 0, STAMINA_HEIGHT, "system")
	health = bar("Vitality", 1, HEALTH_HEIGHT, "danger")
end

--- Called every frame by the movement controller.
function Vitals.setStamina(fraction: number, now: number, dt: number): ()
	local b = stamina
	if b then
		setValue(b, fraction, now, dt, "fate")
	end
end

--- Called every frame by the movement controller, from the Humanoid.
function Vitals.setHealth(fraction: number, now: number, dt: number): ()
	local b = health
	if b then
		setValue(b, fraction, now, dt, nil)
	end
end

return Vitals
