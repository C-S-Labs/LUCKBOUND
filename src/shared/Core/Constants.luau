--!strict
-- Frozen enums and lookup tables. Build spec §2.1.
-- Nothing here is a tunable -- tunables live in GameConfig.

local Types = require(script.Parent.Types)

local function deepFreeze<T>(t: T): T
	for _, v in pairs(t :: any) do
		if type(v) == "table" then
			deepFreeze(v)
		end
	end
	return table.freeze(t :: any) :: T
end

local RARITY: { [string]: Types.Rarity } = {
	COMMON = {
		Key = "COMMON",
		Order = 1,
		Display = "Common",
		Color = Color3.fromHex("B8C4CE"),
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
		Color = Color3.fromHex("4EA8F0"),
		RevealDuration = 3.2,
	},
	EPIC = {
		Key = "EPIC",
		Order = 4,
		Display = "Epic",
		Color = Color3.fromHex("A96FE8"),
		RevealDuration = 3.8,
	},
	LEGENDARY = {
		Key = "LEGENDARY",
		Order = 5,
		Display = "Legendary",
		Color = Color3.fromHex("F2B23C"),
		RevealDuration = 4.5,
	},
	MYTHIC = {
		Key = "MYTHIC",
		Order = 6,
		Display = "Mythic",
		Color = Color3.fromHex("F0555B"),
		RevealDuration = 5.5,
	},
	UNKNOWN = {
		Key = "UNKNOWN",
		Order = 7,
		Display = "???",
		Color = Color3.fromHex("FFFFFF"),
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
