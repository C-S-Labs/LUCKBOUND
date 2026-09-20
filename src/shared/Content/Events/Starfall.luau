--!strict
-- STARFALL — the Fatebreak sky. Master Spec §12.
--
-- The event that already existed in code before events were content: a
-- Mythic roll alters reality everywhere for five minutes. Written out here as
-- data so it is authored the same way as everything that comes after it.

return {
	Id = "STARFALL",
	Name = "Starfall",
	-- Kind is what the menu palette and any effects match on; several events
	-- may share one. Id is what this event IS.
	Kind = "FATEBREAK",
	-- WORLD: the loudest tier, and the only one allowed to open a rift or
	-- grant a unique. See docs/EVENTS.md §4.0 -- the validator enforces it.
	Tier = "WORLD",
	Scope = "GLOBAL",
	Priority = 50,
	DurationSeconds = 300,

	Announcement = {
		-- {player} and {event} are the only substitutions. Keeping the set
		-- tiny means an announcement can never reference something the
		-- server does not have at hand.
		Text = "FATEBREAK! {player} has torn the sky. Reality has been altered.",
		Rarity = "MYTHIC",
	},

	-- Applied PER CLIENT and reverted exactly, the same discipline biome
	-- lighting follows (Biome Blueprint §6). Any property left out keeps the
	-- hub's own value, so an event may change only the two things it cares
	-- about without restating the whole Crossroads palette.
	Lighting = {
		Ambient = Color3.fromRGB(96, 62, 58),
		OutdoorAmbient = Color3.fromRGB(128, 78, 64),
		ColorShiftTop = Color3.fromRGB(196, 96, 40),
		FogColor = Color3.fromRGB(58, 28, 30),
		Brightness = 2.9,
		-- Not a full day-night move: the hub's 4.5 was tuned so the plaza is
		-- readable at all (STATUS §4), and an event that makes the floor
		-- disappear is not an improvement.
		ClockTime = 3.6,
	},

	-- The sky layer. Motes over the plaza and a colour-correction pass, both
	-- created and destroyed by the client that shows them.
	Sky = {
		Enabled = true,
		ParticleColor = Color3.fromRGB(255, 150, 60),
		ParticleRate = 40,
		Tint = Color3.fromRGB(255, 196, 170),
		Saturation = 0.08,
		Contrast = 0.04,
	},
}
