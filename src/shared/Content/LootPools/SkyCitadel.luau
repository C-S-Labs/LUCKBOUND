--!strict
-- Sky Citadel's loot pools (build spec §7.5).
--
-- EMPTY ON PURPOSE. The owner deferred what drops until the loot pools are
-- designed (2026-09-23); the machinery around them is live. Every opening
-- already rolls each party member's own share from these -- today that share
-- is nothing. To fill a pool, add rows to Entries:
--
--   { ItemId = "SOME_ITEM", Weight = 10, Min = 1, Max = 3 }
--
-- and nothing else changes. What an ItemId IS (an inventory item, currency,
-- a cosmetic) is the open question, recorded in docs/RESERVED.md.
return {
	{
		Id = "SC_CHEST",
		WorldId = "SKY_CITADEL",
		Rolls = 1,
		Entries = {},
	},
	{
		Id = "SC_VAULT",
		WorldId = "SKY_CITADEL",
		Rolls = 3, -- a vault is the big one
		Entries = {},
	},
	{
		Id = "SC_BOSS",
		WorldId = "SKY_CITADEL",
		Rolls = 2,
		Entries = {},
	},
}
