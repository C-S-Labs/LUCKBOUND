--!strict
-- THE CATALYST STAR — one of ten that will ever exist.
--
-- Owner-directed. The rarest thing in the game: when one is found, every
-- server is told, the hub reacts, and there are nine left forever.
--
-- `Unique` is what makes that true rather than decorative. It names a ledger
-- key and a cap, and LedgerSystem CLAIMS a number from a DataStore before
-- anything is announced -- because the cross-server channel that carries the
-- announcement cannot count, and announce-then-count issues eleven of ten.
-- See Core/LedgerCore.
--
-- The item that grants it does not exist yet: items are Phase 2 (build spec
-- §7). What exists is the event, the scarcity rule and the ledger, so that
-- whoever builds the item finds the hard part already solved and tested.

return {
	Id = "CATALYST_STAR",
	Name = "Catalyst Star",
	Kind = "CATALYST_STAR",
	Tier = "WORLD",
	Scope = "GLOBAL",
	-- Above Starfall: a Fatebreak happens; this happens ten times, ever.
	Priority = 100,
	DurationSeconds = 420,

	Unique = {
		LedgerId = "CATALYST_STAR",
		Cap = 10,
	},

	Announcement = {
		Text = "{player} has found a CATALYST STAR. {remaining} remain.",
		Rarity = "MYTHIC",
	},

	-- THE FINDER GETS THE ITEM. EVERYONE GETS THE EVENT. (docs/EVENTS.md §5.5)
	-- The Star belongs to whoever claimed it from the ledger; the sky, the
	-- rift and everything the rift yields are open to every player online for
	-- the duration. Scarcity and participation stop competing, and the player
	-- who found it is the reason everyone else is having a good night rather
	-- than the only one allowed through a door.
	OpenToEveryone = true,

	Lighting = {
		Ambient = Color3.fromRGB(68, 96, 118),
		OutdoorAmbient = Color3.fromRGB(96, 140, 168),
		ColorShiftTop = Color3.fromRGB(120, 200, 235),
		FogColor = Color3.fromRGB(26, 44, 62),
		Brightness = 3.1,
		ClockTime = 3.2,
	},

	Sky = {
		Enabled = true,
		ParticleColor = Color3.fromRGB(180, 240, 255),
		ParticleRate = 70,
		Tint = Color3.fromRGB(196, 232, 255),
		Saturation = 0.12,
		Contrast = 0.06,
	},
}
