--!strict
-- Frozen enums and lookup tables. Build spec §2.1.
-- Nothing here is a tunable -- tunables live in GameConfig.

local Types = require(script.Parent.Types)

local Freeze = require(script.Parent.Freeze)
local deepFreeze = Freeze.deep

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
		GATE_ANCHOR = "GateAnchor",
		EXPEDITION_STAGE = "ExpeditionStage",

		-- A prebuilt map is a Model synced into ServerStorage by Rojo, named for
		-- its AssetManifest key. Inside it, two named parts are the whole
		-- contract between art and code -- the same trick the hub plays with
		-- RollAnchor and GateAnchor, and for the same reason: the modeller can
		-- rebuild everything around them without touching a line of Luau.
		MAPS_FOLDER = "LuckboundMaps",
		-- Authored hub props, same idea as MAPS_FOLDER but for pieces of the
		-- Crossroads rather than whole worlds.
		PREFABS_FOLDER = "LuckboundPrefabs",
		-- Drop-in chunk kits: assets/rbxm/chunks/<world>/*.rbxmx, synced to
		-- ServerStorage. See server/Systems/ChunkAutoKit.
		CHUNK_KITS_FOLDER = "LuckboundChunkKits",
		MAP_ENTRY_ANCHOR = "EntryAnchor",
		MAP_RETURN_ANCHOR = "ReturnAnchor",
	},

	-- KEYBOARD SHORTCUT NAMES CONTENT MAY USE.
	--
	-- This list exists because of a bug that reached Studio: content named the
	-- collapse key "Backslash", Roblox's KeyCode is "BackSlash", and indexing
	-- an Enum with a name it does not have RAISES rather than returning nil.
	-- So every keypress threw, the handler died before it reached the panel
	-- shortcuts, and the output filled with the same error twice a second.
	--
	-- Validating against a list the test suite can see turns that into a boot
	-- failure with the offending name in it. Add a name here when content
	-- needs it, and check it against the real Enum first.
	HOTKEY_NAMES = {
		A = true, B = true, C = true, D = true, E = true, F = true, G = true,
		H = true, I = true, J = true, K = true, L = true, M = true, N = true,
		O = true, P = true, Q = true, R = true, S = true, T = true, U = true,
		V = true, W = true, X = true, Y = true, Z = true,
		Zero = true, One = true, Two = true, Three = true, Four = true,
		Five = true, Six = true, Seven = true, Eight = true, Nine = true,
		-- The capital S is not a typo and is the whole reason this table
		-- exists.
		BackSlash = true,
		Slash = true,
		LeftBracket = true,
		RightBracket = true,
		Semicolon = true,
		Quote = true,
		Comma = true,
		Period = true,
		Minus = true,
		Equals = true,
		Tab = true,
		Insert = true,
		Home = true,
		End = true,
		PageUp = true,
		PageDown = true,
	},

	DATASTORE = {
		PROFILE_STORE = "LUCKBOUND_Profiles_v1",
		KEY_PREFIX = "player_",
		-- THE SCARCITY LEDGER. Separate store from profiles on purpose: it is
		-- the one piece of data in the game that is about the GAME rather
		-- than about a player, it must never be wiped with a profile, and it
		-- is written by a different code path with different failure rules
		-- (LedgerSystem fails closed; SaveSystem fails open).
		LEDGER_STORE = "LUCKBOUND_Ledger_v1",
		LEDGER_PREFIX = "unique_",
		-- MemoryStore, not DataStore: an expedition manifest only has to live
		-- as long as a teleport. Keyed by the reserved server's
		-- PrivateServerId, which the destination server can read about itself
		-- -- so nothing the manifest says ever passes through a client.
		EXPEDITION_MANIFESTS = "LUCKBOUND_Expeditions_v1",
		-- Who was in whose party, written by an expedition server as it sends
		-- a party home, read by the hub server they land on. Keyed by UserId.
		PARTY_REUNITE = "LUCKBOUND_PartyReunite_v1",
	},
	-- Attribute on ReplicatedStorage.Luckbound saying what this server is
	-- for, set first thing at boot so every client can read it before any
	-- screen is built.
	SERVER_KIND_ATTRIBUTE = "ServerKind",
	SERVER_KIND_HUB = "HUB",
	SERVER_KIND_EXPEDITION = "EXPEDITION",

	-- v2 added RedeemedCodes and Settings, for the hub menu's Codes and
	-- Settings panels. ProfileSchema.MIGRATIONS[1] fills both in.
	-- v3 added Keys, the vault keys a player carries (build spec §7.5).
	-- ProfileSchema.MIGRATIONS[2] fills it in.
	CURRENT_SCHEMA_VERSION = 3,
}

return deepFreeze(Constants)
