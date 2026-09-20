--!strict
-- WHAT COLOUR IS THE MENU RIGHT NOW? Pure, so the answer is testable for
-- every place a player can stand and everything that can happen to the sky.
--
-- `UITheme` holds the fixed design tokens. `Content/Hub/Palettes` holds how
-- far those tokens lean toward a district or an event. This resolves the two
-- into the palette the UI paints with, and it is the only thing allowed to.
--
-- THE THREE RULES IT ENFORCES, so that no screen has to remember them:
--
--   1. ONLY SURFACES TINT. Gold, teal and the seven rarity colours are
--      meanings, not decoration. TINTABLE below is the complete list of what
--      may move, and a test asserts every other token is byte-identical in
--      every palette this can produce.
--   2. TEXT STAYS READABLE. Every resolved palette is checked against the
--      contrast floor before it is handed out -- an event palette that would
--      make Settings unreadable is clamped, not shipped.
--   3. ONE EVENT OWNS THE LOOK. Precedence is EventCore.dominant's job; this
--      takes the winner and nothing else.

local UITheme = require(script.Parent.UITheme)

local ThemeCore = {}

-- The complete set of tokens a district or an event may move. Everything else
-- in UITheme is a meaning and is copied through untouched.
local TINTABLE = {
	"PanelColor",
	"RailColor",
	"RaisedColor",
	"ScrimColor",
	"StrokeColor",
}

ThemeCore.TINTABLE = table.freeze(TINTABLE)

-- WCAG's own numbers. 4.5:1 is the AA floor for body text, and the menu's
-- smallest type (13px labels, TextMuted on a raised row) is body text by any
-- honest reading of that spec.
ThemeCore.CONTRAST_FLOOR = 4.5

local function channelLuminance(channel: number): number
	if channel <= 0.03928 then
		return channel / 12.92
	end
	return ((channel + 0.055) / 1.055) ^ 2.4
end

--- Relative luminance, 0..1. The sRGB formula, not a naive average: a naive
--- one would call gold and teal equally bright and pass palettes a player
--- cannot read.
function ThemeCore.luminance(color: Color3): number
	return 0.2126 * channelLuminance(color.R)
		+ 0.7152 * channelLuminance(color.G)
		+ 0.0722 * channelLuminance(color.B)
end

--- Contrast ratio between two colours, 1..21.
function ThemeCore.contrast(a: Color3, b: Color3): number
	local la = ThemeCore.luminance(a)
	local lb = ThemeCore.luminance(b)
	local lighter = math.max(la, lb)
	local darker = math.min(la, lb)
	return (lighter + 0.05) / (darker + 0.05)
end

local function toLinear(channel: number): number
	return channelLuminance(channel)
end

local function toGamma(channel: number): number
	if channel <= 0.0031308 then
		return channel * 12.92
	end
	return 1.055 * channel ^ (1 / 2.4) - 0.055
end

--- A STRAIGHT MIX, for things that carry no text. The stroke uses this: a 1px
--- edge is allowed to brighten, because nothing has to be read against it.
local function mix(base: Color3, tint: Color3?, strength: number): Color3
	if tint == nil or strength <= 0 then
		return base
	end
	return base:Lerp(tint, math.clamp(strength, 0, 1))
end

--- A HUE SHIFT THAT KEEPS THE BRIGHTNESS. This is the one piece of real
--- colour maths in the file, and it exists because of a measurement:
---
--- A plain mix toward a district colour LIGHTENS the surface, and the menu's
--- faintest text sits only ~5:1 above that surface to begin with. Mixing 20%
--- toward starlight took a raised row from 5.06:1 to 2.96:1 -- unreadable --
--- so every interesting tint would have been clawed back by the contrast
--- clamp, and what content asked for would not be what rendered.
---
--- Preserving luminance fixes the cause rather than the symptom: the surface
--- takes the district's HUE and keeps its own brightness, so contrast is
--- essentially unchanged and the clamp becomes a backstop that rarely fires.
--- It is also the better look -- the menu stays dark and shifts colour,
--- rather than fading toward whatever it is standing next to.
local function tintPreservingLuminance(base: Color3, tint: Color3?, strength: number): Color3
	if tint == nil or strength <= 0 then
		return base
	end

	local alpha = math.clamp(strength, 0, 1)
	local baseLinear = { toLinear(base.R), toLinear(base.G), toLinear(base.B) }
	local tintLinear = { toLinear(tint.R), toLinear(tint.G), toLinear(tint.B) }

	local mixed = {
		baseLinear[1] + (tintLinear[1] - baseLinear[1]) * alpha,
		baseLinear[2] + (tintLinear[2] - baseLinear[2]) * alpha,
		baseLinear[3] + (tintLinear[3] - baseLinear[3]) * alpha,
	}

	local baseLuminance = 0.2126 * baseLinear[1] + 0.7152 * baseLinear[2] + 0.0722 * baseLinear[3]
	local mixedLuminance = 0.2126 * mixed[1] + 0.7152 * mixed[2] + 0.0722 * mixed[3]

	if mixedLuminance > 0 then
		local scale = baseLuminance / mixedLuminance
		mixed[1] *= scale
		mixed[2] *= scale
		mixed[3] *= scale
	end

	return Color3.new(
		toGamma(math.clamp(mixed[1], 0, 1)),
		toGamma(math.clamp(mixed[2], 0, 1)),
		toGamma(math.clamp(mixed[3], 0, 1))
	)
end

local function lerp(base: Color3, tint: Color3?, strength: number, token: string): Color3
	if token == "StrokeColor" then
		return mix(base, tint, strength)
	end
	return tintPreservingLuminance(base, tint, strength)
end

local function findDistrict(palettes: any, districtId: string?): any?
	if districtId == nil then
		return nil
	end
	for _, entry in palettes.Districts do
		if entry.Id == districtId then
			return entry
		end
	end
	return nil
end

local function findEvent(palettes: any, kind: string?): any?
	if kind == nil then
		return nil
	end
	for _, entry in palettes.Events do
		if entry.Kind == kind then
			return entry
		end
	end
	return nil
end

--- The untinted palette: UITheme's own values, in the shape a resolved one
--- has. Every caller gets a full table, so no screen has to fall back.
function ThemeCore.base(): { [string]: any }
	local palette = {}
	for _, token in TINTABLE do
		palette[token] = (UITheme :: any)[token]
	end
	palette.Source = "BASE"
	palette.DistrictId = nil
	palette.EventKind = nil
	return palette
end

--- RESOLVE. `context` = { DistrictId, Event } where Event is the dominant
--- event (EventCore.dominant's return) or nil.
---
--- An event is applied ON TOP of the district rather than instead of it, so
--- standing in the Archive during a Starfall reads as the Archive during a
--- Starfall. The event goes last because it is the louder statement and must
--- not be diluted by wherever the player happens to be standing.
function ThemeCore.resolve(palettes: any, context: any): { [string]: any }
	local palette = ThemeCore.base()

	local district = findDistrict(palettes, context.DistrictId)
	if district and district.Tint then
		for _, token in TINTABLE do
			palette[token] = lerp(palette[token], district.Tint, district.Strength, token)
		end
		palette.Source = "DISTRICT"
		palette.DistrictId = district.Id
	end

	local eventKind = if context.Event then context.Event.Kind else nil
	local event = findEvent(palettes, eventKind)
	if event and event.Tint then
		for _, token in TINTABLE do
			palette[token] = lerp(palette[token], event.Tint, event.Strength, token)
		end
		palette.Source = "EVENT"
		palette.EventKind = event.Kind
	end

	return ThemeCore.enforceContrast(palette)
end

--- THE SAFETY NET. Walks the tinted surfaces back toward the base until the
--- menu's smallest text clears the floor against every one of them.
---
--- It exists because the failure it prevents is invisible to whoever authors
--- a palette: a Catalyst Star tint that looks magnificent on a panel is also
--- the thing that makes the Settings labels vanish, and nobody notices until
--- a player cannot turn the music down. Clamping rather than rejecting keeps
--- a bad number a cosmetic problem instead of a crash.
function ThemeCore.enforceContrast(palette: { [string]: any }): { [string]: any }
	local text = UITheme.TextMuted -- the faintest text the menu draws

	for _, token in TINTABLE do
		if token ~= "StrokeColor" then
			-- A stroke carries no text, so it is exempt: clamping it would
			-- throw away the part of the tint that reads best.
			local surface = palette[token]
			local steps = 0
			while ThemeCore.contrast(text, surface) < ThemeCore.CONTRAST_FLOOR and steps < 20 do
				surface = surface:Lerp((UITheme :: any)[token], 0.2)
				steps += 1
			end
			palette[token] = surface
		end
	end

	return palette
end

--- Which district a position belongs to, by nearest anchor within its reach.
--- Pure so the boundaries are testable: "standing here shows the Archive" is
--- an assertion, not something to be walked to.
---
--- Returns nil outside every district's radius, which resolves to the base
--- palette -- the open plaza is nobody's district.
function ThemeCore.districtAt(position: Vector3, menu: any, radius: number): string?
	local closestId: string? = nil
	local closest = math.huge

	for _, destination in menu.Destinations do
		local anchor = destination.Anchor
		-- Horizontal distance only. A player on a walkway 20 studs above the
		-- plaza is still in the same district, and counting Y would flicker
		-- the menu every time they climbed a step.
		local dx = position.X - anchor.X
		local dz = position.Z - anchor.Z
		local distance = math.sqrt(dx * dx + dz * dz)
		if distance < closest then
			closest = distance
			closestId = destination.Id
		end
	end

	if closest > radius then
		return nil
	end
	return closestId
end

return ThemeCore
