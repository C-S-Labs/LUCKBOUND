--!strict
-- Shared GUI design system. Biome Blueprint §1.4.
-- Every ScreenGui pulls fonts, colours and radii from here so no screen
-- invents its own. Required before any Phase 2 UI is built.

local Constants = require(script.Parent.Constants)

local function deepFreeze<T>(t: T): T
	-- Guard against a table reachable by two paths (UITheme reuses Constants'
	-- rarity tables): freezing an already-frozen table raises.
	if table.isfrozen(t :: any) then
		return t
	end
	for _, v in pairs(t :: any) do
		if type(v) == "table" and not table.isfrozen(v) then
			deepFreeze(v)
		end
	end
	return table.freeze(t :: any) :: T
end

local rarityColors = {}
for key, rarity in Constants.RARITY do
	rarityColors[key] = rarity.Color
end

local UITheme = {
	HeaderFont = Enum.Font.GothamBlack,
	BodyFont = Enum.Font.Gotham,
	LabelFont = Enum.Font.GothamBold,

	BackgroundColor = Color3.fromRGB(18, 14, 30), -- deep cosmic purple-black
	BackgroundTransparency = 0.15,
	AccentGold = Color3.fromRGB(230, 178, 74), -- matches hub lighting
	StrokeColor = Color3.fromRGB(255, 255, 255),
	StrokeTransparency = 0.7,
	CornerRadius = UDim.new(0, 12),

	TextPrimary = Color3.fromRGB(245, 240, 255),
	TextSecondary = Color3.fromRGB(160, 152, 186),

	-- Same table as blueprint §1.1, derived from Constants so there is exactly
	-- one definition of a rarity colour in the codebase.
	RarityColors = rarityColors,

	-- === SURFACES =====================================================
	-- Three depths, and every panel in the game is one of them. Named after
	-- what they ARE rather than where they sit, so a screen cannot invent a
	-- fourth shade of purple by eye.
	PanelColor = Color3.fromRGB(24, 19, 40), -- a menu panel
	PanelTransparency = 0.08,
	RailColor = Color3.fromRGB(20, 16, 34), -- the collapsible side rail
	RailTransparency = 0.12,
	RaisedColor = Color3.fromRGB(34, 27, 55), -- a row or tile inside a panel
	RaisedTransparency = 0.05,
	ScrimColor = Color3.fromRGB(8, 6, 16), -- behind a modal, over the world
	ScrimTransparency = 0.45,

	-- The Crossroads' own light is gold on cosmic purple (Crossroads.Theme),
	-- and the hub UI is lit by the same two. AccentCool is the Discovery
	-- Archive's teal, used ONLY for informational state so that gold keeps
	-- meaning "this is the thing to press".
	AccentCool = Color3.fromRGB(124, 245, 224),
	AccentWarn = Color3.fromRGB(240, 132, 96),
	TextMuted = Color3.fromRGB(116, 110, 140),
	DividerColor = Color3.fromRGB(92, 82, 128),

	-- === RHYTHM =======================================================
	-- One spacing scale. A pad that is not on it is a mistake, not a choice.
	Space = { XS = 4, SM = 8, MD = 14, LG = 22, XL = 34 },
	RadiusSmall = UDim.new(0, 8),
	RadiusLarge = UDim.new(0, 18),

	-- Rail and panel geometry, in offset pixels, with the scale-width cap
	-- handled by a UISizeConstraint at the point of use. Phones get the
	-- minimum, desktops the maximum, and nothing in between has to be guessed.
	RailWidth = 68,
	RailWidthExpanded = 232,
	PanelMinWidth = 300,
	PanelMaxWidth = 560,

	-- === MOTION =======================================================
	-- Durations and easings live here so the whole UI accelerates the same
	-- way. Anything that moves reads from this table; a tween with a literal
	-- duration in it is the UI equivalent of a magic number in a System.
	--
	-- The numbers are short on purpose. A menu that takes 400ms to open feels
	-- expensive once and slow forever after.
	Motion = {
		Instant = 0.12,
		Quick = 0.18,
		Normal = 0.26,
		Slow = 0.42,
		-- Panels come in on Quint/Out: fast to arrive, unhurried to settle.
		EaseStyle = Enum.EasingStyle.Quint,
		EaseDirection = Enum.EasingDirection.Out,
		-- ...and leave on Quad/In, which is the reverse shape. Using one
		-- easing for both directions is what makes a menu feel rubbery.
		ExitStyle = Enum.EasingStyle.Quad,
		ExitDirection = Enum.EasingDirection.In,
		-- The rail's items stagger in by this much each, capped so a long
		-- list never turns into a queue.
		StaggerSeconds = 0.035,
		StaggerMaxItems = 10,
		-- How far a panel travels while fading in, in pixels.
		SlideOffset = 28,
	},
}

--- Applies the theme's corner radius to a GuiObject.
function UITheme.corner(parent: Instance, radius: UDim?): UICorner
	local c = Instance.new("UICorner")
	c.CornerRadius = radius or UITheme.CornerRadius
	c.Parent = parent
	return c
end

--- Applies a themed stroke. Pass a colour to override the default.
function UITheme.stroke(parent: Instance, color: Color3?, thickness: number?): UIStroke
	local s = Instance.new("UIStroke")
	s.Color = color or UITheme.StrokeColor
	s.Transparency = if color then 0 else UITheme.StrokeTransparency
	s.Thickness = thickness or 2
	s.Parent = parent
	return s
end

function UITheme.rarityColor(key: string): Color3
	return UITheme.RarityColors[key] or UITheme.RarityColors.COMMON
end

--- Applies the shared padding to a GuiObject. One argument pads all four
--- sides; the theme's spacing scale is the only source of the numbers.
function UITheme.pad(parent: Instance, amount: number?): UIPadding
	local px = amount or UITheme.Space.MD
	local p = Instance.new("UIPadding")
	p.PaddingTop = UDim.new(0, px)
	p.PaddingBottom = UDim.new(0, px)
	p.PaddingLeft = UDim.new(0, px)
	p.PaddingRight = UDim.new(0, px)
	p.Parent = parent
	return p
end

--- The vertical gradient every panel and rail wears: the theme's own colour,
--- lifted slightly at the top so a large flat surface has a direction of
--- light instead of reading as a rectangle of paint.
function UITheme.gradient(parent: Instance, lift: number?): UIGradient
	local amount = lift or 0.12
	local g = Instance.new("UIGradient")
	g.Rotation = 90
	g.Color = ColorSequence.new({
		-- A UIGradient MULTIPLIES the surface's colour, so 1 is "unchanged" and
		-- anything above it is ignored rather than brightening. The lift is
		-- therefore a darkening of the bottom, not a lightening of the top.
		ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
		ColorSequenceKeypoint.new(1, Color3.new(1 - amount, 1 - amount, 1 - amount)),
	})
	g.Parent = parent
	return g
end

return deepFreeze(UITheme)
