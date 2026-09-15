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

return deepFreeze(UITheme)
