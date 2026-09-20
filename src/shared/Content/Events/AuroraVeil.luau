--!strict
-- AURORA VEIL -- weather, and nothing but weather.
--
-- This event exists to make an argument: if every event summons players, none
-- of them is an occasion. The Veil changes the sky, says so quietly, and asks
-- nothing of anybody.
--
-- It is also the worked example of the AMBIENT tier (docs/EVENTS.md §4.0).
-- The validator refuses an AMBIENT event that tries to open a rift or grant a
-- unique, so the tier is a rule rather than an intention.

return {
	Id = "AURORA_VEIL",
	Name = "Aurora Veil",
	Kind = "AURORA_VEIL",
	Tier = "AMBIENT",
	Scope = "SERVER",
	-- Below everything loud: a Veil running when a Starfall begins simply
	-- stops being the sky, and resumes being it if it outlives the Starfall.
	Priority = 5,
	DurationSeconds = 240,

	Announcement = {
		Text = "An aurora veils the Crossroads.",
		Rarity = "UNCOMMON",
	},

	Lighting = {
		Ambient = Color3.fromRGB(64, 78, 104),
		OutdoorAmbient = Color3.fromRGB(88, 112, 148),
		ColorShiftTop = Color3.fromRGB(96, 160, 190),
		FogColor = Color3.fromRGB(28, 38, 58),
		-- Brightness and ClockTime deliberately untouched: the hub's 4.5 was
		-- tuned so the plaza is readable, and an ambient event is not a good
		-- enough reason to spend that.
	},

	Sky = {
		Enabled = true,
		ParticleColor = Color3.fromRGB(150, 220, 255),
		-- A third of a Starfall's. It should be noticed, not watched.
		ParticleRate = 14,
		Tint = Color3.fromRGB(198, 222, 246),
		Saturation = 0.05,
		Contrast = 0.02,
	},
}
