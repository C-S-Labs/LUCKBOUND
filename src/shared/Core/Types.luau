--!strict
-- LUCKBOUND canonical type definitions.
-- This file is the machine-readable copy of build spec §2 and is authoritative
-- over the prose if the two drift. Types only -- no runtime values live here.

export type RarityKey =
	"COMMON" | "UNCOMMON" | "RARE" | "EPIC" | "LEGENDARY" | "MYTHIC" | "UNKNOWN"

export type Rarity = {
	Key: RarityKey,
	Order: number,
	Display: string,
	Color: Color3,
	RevealDuration: number,
}

export type SlotName = "Weapon" | "Ability" | "Companion" | "Relic" | "Aura"
export type ItemType = SlotName

-- Extended for Biome Blueprint §1.2: each biome overrides the shared Lighting
-- baseline on expedition entry, which needs Brightness, FogStart and the
-- colour-shift pair that the original four fields could not express.
export type Environment = {
	SkyId: string?,
	AmbientColor: Color3,
	OutdoorAmbientColor: Color3?,
	ColorShiftTop: Color3?,
	FogColor: Color3,
	FogStart: number,
	FogEnd: number,
	Brightness: number,
	ClockTime: number,
}

--- Per-modifier palette overrides. Blueprint §3.5: modifiers re-tint a world
--- rather than building separate geometry.
export type ModifierOverride = {
	AmbientColor: Color3?,
	FogColor: Color3?,
	FogStart: number?,
	FogEnd: number?,
	Brightness: number?,
	ClockTime: number?,
	ParticleId: string?,
}

export type WorldDefinition = {
	Id: string,
	Name: string,
	Rarity: RarityKey,
	RollWeight: number, -- basis points of the full game; renormalised over the enabled pool
	EnabledInPhase: number,
	Environment: Environment,
	MusicId: string?,
	Enemies: { string },
	BossId: string?,
	LootTableId: string?,
	DiscoveryTableId: string?,
	Modifiers: { string },
	ModifierOverrides: { [string]: ModifierOverride }?,
	DurationSeconds: number,
	-- How many connective chunks sit between arrival and the boss arena for
	-- THIS world. nil falls back to GameConfig.Expedition.PathLength. It is
	-- content, not config: map size is a property of the world, and a world
	-- with a shorter expedition needs a shorter map or it becomes a corridor.
	MapPathLength: number?,
	RecommendedPower: number,
	Flavor: string,
}

export type EnemyDefinition = {
	Id: string,
	Name: string,
	Health: number,
	Damage: number,
	WalkSpeed: number,
	AttackRange: number,
	TelegraphSeconds: number,
	AttackCooldown: number,
	ModelId: string?,
	LootTableId: string?,
}

export type BossPhase = {
	HealthThreshold: number, -- fraction of max health at which this phase begins
	AttackIds: { string },
}

export type BossDefinition = {
	Id: string,
	Name: string,
	Health: number,
	Damage: number,
	Phases: { BossPhase },
	AttackIds: { string },
	ModelId: string?,
	LootTableId: string?,
	FateReward: number,
}

export type ItemDefinition = {
	Id: string,
	Name: string,
	Rarity: RarityKey,
	Type: ItemType,
	Damage: number?,
	AbilityId: string?,
	PassiveId: string?,
	Element: string?,
	VisualId: string?,
	WorldAffinity: string?,
	DiscoveryText: string,
}

export type DiscoveryDefinition = {
	Id: string,
	Name: string,
	Rarity: RarityKey,
	WorldAffinity: string?,
	FlavorText: string,
	IsSoulbound: boolean,
	IsHidden: boolean, -- true => Discovery Book shows "???" until first found
	FatebreakEventId: string?,
	OddsDenominator: number,
}

export type ModifierDefinition = {
	Id: string,
	Name: string,
	Description: string,
	EnemyHealthMultiplier: number,
	EnemyDamageMultiplier: number,
	LootQualityBonus: number,
	FateMultiplier: number,
}

-- Modular map chunks --------------------------------------------------------
-- Addendum §A4: procedural COMPOSITION, not procedural terrain. Variety comes
-- from arranging a bounded library of authored, pre-validated pieces rather
-- than generating unbounded landscape.

export type ChunkRole =
	"ENTRY" -- exactly one per layout; where the player arrives
	| "PATH" -- connective tissue
	| "COMBAT" -- encounter space
	| "SIDE" -- optional branch, off the critical path
	| "CAP" -- a dead end authored as one, closing an opening the path left unused
	| "BOSS" -- exactly one per layout; the destination

--- A connection point on a chunk. Two sockets may join only if their Kind
--- matches -- that is what stops a 4-stud footpath opening onto a cliff face.
--- Offset and Facing are LOCAL to the chunk, before it is rotated into place.
export type ChunkSocket = {
	Id: string,
	Kind: string, -- "PATH" | "WIDE" | "WATER" | ...
	OffsetX: number,
	OffsetY: number,
	OffsetZ: number,
	Facing: number, -- degrees: 0 = -Z (north), 90 = +X, 180 = +Z, 270 = -X
}

export type ChunkDefinition = {
	Id: string,
	WorldId: string,
	Role: ChunkRole,
	AssetKey: string, -- key into Content/AssetManifest
	SizeX: number, -- axis-aligned bounds, used for overlap rejection
	SizeY: number,
	SizeZ: number,
	Sockets: { ChunkSocket },
	Weight: number, -- selection weight within its Role
	MaxPerLayout: number?, -- nil = unlimited
	EnemyTags: { string }?, -- which spawn pools this chunk accepts
	Tags: { string }?,
}

--- One placed chunk in an assembled layout. Plain numbers, no Roblox types,
--- so assembly stays pure and unit-testable; the loader converts to CFrame.
export type PlacedChunk = {
	ChunkId: string,
	Role: ChunkRole,
	X: number,
	Y: number,
	Z: number,
	Yaw: number, -- 0 | 90 | 180 | 270
	Index: number, -- order along the critical path; 0 for side branches
}

export type Layout = {
	WorldId: string,
	Seed: number,
	Chunks: { PlacedChunk },
}

-- Player data ---------------------------------------------------------------

export type RollHistoryEntry = {
	WorldId: string,
	Rarity: RarityKey,
	Timestamp: number,
}

export type DiscoveryRecord = {
	FirstFoundAt: number,
	Count: number,
}

export type ItemInstance = {
	Uid: string,
	ItemId: string,
	RolledStats: { [string]: number }?,
}

export type ProfileStats = {
	ExpeditionsCompleted: number,
	BossesDefeated: number,
	DeepestRarity: RarityKey,
}

export type PlayerProfile = {
	SchemaVersion: number,
	FatePoints: number,
	FateLevel: number,
	TotalRolls: number,
	RollHistory: { RollHistoryEntry },
	Discoveries: { [string]: DiscoveryRecord },
	Inventory: { ItemInstance },
	EquippedSlots: { [string]: string },
	Stats: ProfileStats,
	LastSeenAt: number,
	CreatedAt: number,
}

-- Network payloads ----------------------------------------------------------

export type RollPayload = {
	WorldId: string,
	Name: string,
	Rarity: RarityKey,
	Flavor: string,
	IsTutorialRoll: boolean,
	RollNumber: number,
}

--- Sent on Expedition_Started. Carries everything the client needs to dress
--- the world locally: Environment is applied to Lighting BY THE CLIENT, so one
--- player's biome never bleeds onto another's screen (§6 checklist).
---
--- RemainingSeconds, never an absolute end time -- build spec §4.1 rule 4: a
--- client with a skewed clock still counts down correctly.
export type ExpeditionPayload = {
	WorldId: string,
	Name: string,
	Rarity: RarityKey,
	Flavor: string,
	Environment: Environment,
	DurationSeconds: number,
	RemainingSeconds: number,
	ServerNow: number,
	Seed: number,
	-- How the map was produced, in one human-readable line -- "6 chunks (0
	-- mesh, 6 blockout) attempt 1" or "prebuilt ES_ENVIRONMENT_FULL, 699 parts
	-- at 0.10 scale". A string rather than a chunk count because a prebuilt
	-- world has no chunks, and a field that means nothing for half the worlds
	-- is a field that gets misread.
	MapSummary: string,
}

export type ExpeditionEndPayload = {
	WorldId: string?,
	Reason: "COMPLETED" | "RETURNED" | "DIED" | "ABORTED",
	FateAwarded: number,
	-- Set only for the two refusals a legitimate player can hit -- no
	-- destination, or a world with no map at all. Every other refusal is an
	-- exploit guard and stays silent, per build spec §3.4.3.
	Message: string?,
}

export type AnnouncePayload = {
	Kind: "ROLL" | "FATEBREAK" | "WORLD_FIRST",
	Text: string,
	Rarity: RarityKey,
	PlayerName: string,
}

-- Result convention ---------------------------------------------------------

export type Result<T> = { ok: true, value: T } | { ok: false, err: string }

return {}
