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

export type AnnouncePayload = {
	Kind: "ROLL" | "FATEBREAK" | "WORLD_FIRST",
	Text: string,
	Rarity: RarityKey,
	PlayerName: string,
}

-- Result convention ---------------------------------------------------------

export type Result<T> = { ok: true, value: T } | { ok: false, err: string }

return {}
