--!strict
-- Frozen enums and lookup tables. Build spec §2.1.
-- Nothing here is a tunable -- tunables live in GameConfig.

local Types = require(script.Parent.Types)

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

-- Colours are the Biome Blueprint §1.1 table, which declares itself the single
-- source of truth for rarity across UI, portals, particles and loot glows.
-- Adopted verbatim; the earlier prototype palette is superseded.
--
-- UNCOMMON is not in that table (it lists six tiers, we carry seven). Its
-- colour below is carried over from the prototype palette and is the one value
-- here NOT blueprint-sanctioned -- flagged for sign-off, see docs/BLUEPRINT_RECONCILIATION.md.
--
-- Order is unchanged from build spec §2.1. The blueprint lists its rows
-- Common/Rare/Epic/Mythic/Legendary, which would rank Legendary above Mythic,
-- but its own §5.4 makes Astral Reach (the top prototype world) Mythic, and
-- master spec §4 puts The Void (Mythic) rarer than Astral Realm (Legendary).
-- So row order there is presentation, not ranking, and Order stands.
local RARITY: { [string]: Types.Rarity } = {
	COMMON = {
		Key = "COMMON",
		Order = 1,
		Display = "Common",
		Color = Color3.fromHex("9E9E9E"),
		RevealDuration = 2.5,
	},
	UNCOMMON = {
		Key = "UNCOMMON",
		Order = 2,
		Display = "Uncommon",
		Color = Color3.fromHex("5FD97A"),
		RevealDuration = 2.8,
	},
	RARE = {
		Key = "RARE",
		Order = 3,
		Display = "Rare",
		Color = Color3.fromHex("3E8EF7"),
		RevealDuration = 3.2,
	},
	EPIC = {
		Key = "EPIC",
		Order = 4,
		Display = "Epic",
		Color = Color3.fromHex("B24BF3"),
		RevealDuration = 3.8,
	},
	LEGENDARY = {
		Key = "LEGENDARY",
		Order = 5,
		Display = "Legendary",
		Color = Color3.fromHex("FFD447"),
		RevealDuration = 4.5,
	},
	MYTHIC = {
		Key = "MYTHIC",
		Order = 6,
		Display = "Mythic",
		Color = Color3.fromHex("FF7A1A"),
		RevealDuration = 5.5,
	},
	UNKNOWN = {
		Key = "UNKNOWN",
		Order = 7,
		Display = "???",
		Color = Color3.fromHex("7CF5E0"),
		RevealDuration = 7.0,
	},
}

local Constants = {
	RARITY = RARITY,

	-- Rarity at or above which a roll is announced to the whole server.
	ANNOUNCE_RARITY_ORDER = RARITY.MYTHIC.Order,

	SLOTS = { "Weapon", "Ability", "Companion", "Relic", "Aura" },

	-- Folder and instance names the code relies on existing.
	NAMES = {
		ROOT = "Luckbound",
		NET_FOLDER = "Net",
		CROSSROADS = "Crossroads",
		FATE_ENGINE = "FateEngine",
		ROLL_ANCHOR = "RollAnchor",
		EXPEDITION_STAGE = "ExpeditionStage",
	},

	DATASTORE = {
		PROFILE_STORE = "LUCKBOUND_Profiles_v1",
		KEY_PREFIX = "player_",
	},

	CURRENT_SCHEMA_VERSION = 1,
}

return deepFreeze(Constants)
