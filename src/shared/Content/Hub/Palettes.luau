--!strict
-- WHAT THE UI LOOKS LIKE RIGHT NOW, AS DATA.
--
-- `UITheme` is the design system: fixed tokens, one definition per colour.
-- This file is the *live* layer on top of it — how far the menu's surfaces
-- lean toward the district you are standing in, and toward whatever event is
-- currently happening to the sky.
--
-- THE RULE THIS FILE MUST NOT BREAK: tint the surfaces, never the semantics.
--
-- Gold means "press this". The seven rarity colours are a contract (Biome
-- Blueprint §1.1) and mean exactly one thing each. Teal means "designed, not
-- yet built" on the rail. None of those may move, or the menu teaches the
-- player something false — and two of them collide with authored district
-- colours if you let them: the Discovery Archive's accent IS the rail's teal,
-- and the Hall of Legends' accent IS the gold. So a district only ever moves
-- the SURFACE tokens, and `ThemeCore` is what enforces it.
--
-- Strength is how far a surface leans toward the tint, 0..1 -- but it is a
-- HUE shift, not a fade: ThemeCore holds each surface's own brightness, so
-- the menu changes colour without getting lighter, and the text on it stays
-- as readable as it was. That is what lets these numbers be interesting
-- rather than timid. The stroke is the exception and mixes straight, because
-- nothing is read against a 1px edge and it is the part that reads best.

local Crossroads = require(script.Parent.Crossroads)

-- The authored district colours, by Id. Taken from Content/Hub/Crossroads
-- rather than restated, so the menu cannot drift from the geometry: repaint a
-- district and its menu tint follows. A district with no entry here simply
-- does not tint.
local function districtColor(id: string): Color3?
	for _, district in Crossroads.Districts do
		if district.Id == id then
			return district.Color
		end
	end
	return nil
end

local Palettes = {
	-- === WHERE YOU ARE ================================================
	-- Strength per district rather than one global number, because the
	-- authored colours are not equally strong: the Archive's deep teal
	-- carries at a lower lerp than the Training Grounds' neutral grey, which
	-- barely reads at all until it is pushed.
	Districts = {
		{
			Id = "FATE_ENGINE",
			-- The centre is the base look. The Engine is where the game's own
			-- colour comes from -- the rarity on the portal -- and a tint here
			-- would compete with it.
			Tint = nil,
			Strength = 0,
		},
		{
			Id = "HALL_OF_LEGENDS",
			Tint = districtColor("HALL_OF_LEGENDS"),
			Strength = 0.10, -- marble, and it lightens fast
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Tint = districtColor("DISCOVERY_ARCHIVE"),
			Strength = 0.12,
		},
		{
			Id = "EXPEDITION_GATE",
			Tint = districtColor("EXPEDITION_GATE"),
			Strength = 0.16, -- basalt, close to the base already
		},
		{
			Id = "TRAINING_GROUNDS",
			Tint = districtColor("TRAINING_GROUNDS"),
			Strength = 0.14,
		},
	},

	-- === WHAT IS HAPPENING ============================================
	-- Keyed by an event's Kind. An event with no entry here does not tint the
	-- menu at all, which is the right default: a new event type should have
	-- to opt IN to repainting the interface.
	--
	-- These are stronger than a district, because an event is news. They are
	-- still the quietest thing on screen during one: when the sky cracks,
	-- that is the moment, and a menu that also goes full aurora is competing
	-- with it.
	Events = {
		{
			Kind = "FATEBREAK",
			Tint = Color3.fromRGB(255, 122, 26), -- Mythic orange, the Starfall
			Strength = 0.28,
		},
		{
			Kind = "STARFALL",
			Tint = Color3.fromRGB(255, 122, 26),
			Strength = 0.28,
		},
		{
			-- Declared before it exists, deliberately -- the same reason build
			-- spec §4 reserves remote names. When the Catalyst Star lands it
			-- should find its palette already here rather than invent one.
			Kind = "CATALYST_STAR",
			Tint = Color3.fromRGB(150, 236, 255), -- cold starlight, not a rarity colour
			-- The strongest tint in the file, as the rarest event in the game
			-- should be. It is safe at this strength only because ThemeCore
			-- shifts HUE and holds brightness: mixed naively, 0.35 toward
			-- starlight took a raised row from 5.06:1 to under 3:1 and would
			-- have been clawed back by the contrast clamp, so content would
			-- have been asking for something that never rendered.
			Strength = 0.35,
		},
	},
}

return Palettes
