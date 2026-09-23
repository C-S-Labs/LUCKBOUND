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
	-- RESERVED: see docs/RESERVED.md -- a per-world SKYBOX. Not the same as an
	-- event's `Sky` table, which is a temporary overlay SkyController reads.
	SkyId: string?,
	AmbientColor: Color3,
	OutdoorAmbientColor: Color3?,
	ColorShiftTop: Color3?,
	FogColor: Color3,
	FogStart: number,
	FogEnd: number,
	Brightness: number,
	ClockTime: number,
	-- AMBIENCE. Every block below is optional and read by AmbienceController on
	-- the client; AmbienceCore.validate checks them at boot. A world with none
	-- keeps plain Lighting. Where an Atmosphere is declared it OWNS the haze:
	-- Roblox ignores FogStart/FogEnd whenever an Atmosphere exists.
	ExposureCompensation: number?,
	ColorShiftBottom: Color3?,
	Atmosphere: {
		Density: number,
		Offset: number?,
		Color: Color3,
		Decay: Color3,
		Glare: number,
		Haze: number,
	}?,
	Sky: { SunAngularSize: number?, MoonAngularSize: number?, StarCount: number? }?,
	Bloom: { Intensity: number, Size: number, Threshold: number }?,
	SunRays: { Intensity: number, Spread: number }?,
	Grade: { Brightness: number, Contrast: number, Saturation: number, Tint: Color3 }?,
	-- Drifting layers of cloud under the map, wrapped around the camera so a
	-- few dozen puffs pave an endless sea. Counts scale with graphics quality.
	CloudSea: { CloudLayer }?,
	-- Studs below the walk plane no cloud may rise above. Required with a
	-- CloudSea; set it below the kit's deepest keel so clouds never touch the map.
	CloudCeiling: number?,
	-- Faint particles drifting past the camera. Rate scales with quality.
	Motes: { Rate: number, Lifetime: number, Color: Color3, Size: number, Speed: number }?,
}

export type CloudLayer = {
	Depth: number, -- studs below the walk plane
	Count: number, -- puffs at full quality
	Radius: number, -- half-width of the square the layer paves around the camera
	Speed: number, -- drift, studs per second
	Heading: number, -- drift direction, degrees, 0 = -Z
	SizeMin: number,
	SizeMax: number,
	Thickness: number, -- height as a fraction of width
	Color: Color3, -- lit tops
	Shade: Color3?, -- undersides; defaults to Color
	Billows: number?, -- puffs heaped on a cumulus at full quality; 0 = flat clouds
	Tufts: number?, -- small puffs on each billow's top at full quality (the cauliflower texture)
	-- Surface finish, one of AmbienceCore.CLOUD_MATERIALS; defaults to SmoothPlastic.
	Material: string?,
	-- Relative weights of the three cloud kinds; defaults to mostly cumulus.
	Mix: { Cumulus: number?, Stratus: number?, Wisp: number? }?,
	-- Keep near 0. Softness comes from the Atmosphere's haze over distance;
	-- see-through clouds show their inner shapes and read as bubbles.
	Transparency: number,
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
	-- RESERVED: see docs/RESERVED.md -- per-world music, blocked on audio.
	MusicId: string?,
	Enemies: { string },
	-- RESERVED: see docs/RESERVED.md -- the four below are blocked by build
	-- spec §7 (combat, items, discoveries) or by audio not existing yet.
	BossId: string?,
	LootTableId: string?,
	DiscoveryTableId: string?,
	-- RESERVED: see docs/RESERVED.md -- world modifiers, blocked by §7.
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
	-- Studs across the opening. Optional; when set, ChunkLoader's facing probe
	-- also checks the mouth is this wide, which is what tells two openings of
	-- different Kinds apart.
	Width: number?,
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
	-- Studs from the BOTTOM of the piece's bounding box up to its walking
	-- surface. ChunkLoader lifts the mesh by (SizeY/2 - GroundOffsetY) so the
	-- ground lands on the layout plane; nil means "the walk plane is the box
	-- centre", which is what every chunk meant before the field existed.
	GroundOffsetY: number?,
	-- Degrees, a quarter turn, applied to the MESH ONLY when it is placed.
	-- Corrects a kit whose authored "north" is not the layout's north; nil
	-- means the art already agrees. Never touches sockets or collision.
	MeshYawOffset: number?,
	-- Scenario compatibility (build spec §7.3): what can HAPPEN here, keyed by
	-- a scenario's Requires. Deliberately not universal -- a traversal
	-- challenge in a flat meadow is not a challenge. Required on PATH,
	-- COMBAT and SIDE; ENTRY and BOSS are never assigned a scenario.
	Supports: { [string]: boolean }?,
	-- RESERVED: see docs/RESERVED.md -- which spawn pools this chunk accepts,
	-- blocked by §7 (enemies). Declared per piece so a kit authored now does
	-- not need revisiting when population lands.
	EnemyTags: { string }?,
	-- AUTHORING ONLY, deliberately unread: free-text notes that make a kit
	-- legible to a human. Reading them from code would turn authoring notes
	-- into behaviour, which is exactly what Supports exists to prevent.
	Tags: { string }?,
}

--- A SCENARIO -- what happens inside a chunk, as opposed to what the chunk is.
--- Build spec §7.3. Centralised here with every other content shape rather
--- than typed locally in Content/Scenarios: Types.luau is the canonical
--- description of content, and one kind typing itself privately is how that
--- stops being true.
export type ScenarioBand = "ORDINARY" | "UNCOMMON" | "RARE"

export type ScenarioDefinition = {
	Id: string,
	Name: string,
	Band: ScenarioBand,
	Weight: number, -- relative within its band, not a percentage
	Requires: string, -- the Supports key a chunk must declare
	Roles: { string }?, -- nil = any role the assigner offers
	Notes: string?,
}

--- One room's assignment, as ScenarioCore returns it. ENTRY and BOSS carry no
--- scenario, so the scenario fields are optional by design rather than by
--- accident.
export type ScenarioStep = {
	Index: number,
	ChunkId: string,
	Role: ChunkRole,
	ScenarioId: string?,
	Band: ScenarioBand?,
	FateTouched: boolean,
}

export type ScenarioPlan = {
	WorldId: string,
	Seed: number?,
	Steps: { ScenarioStep },
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
	-- The map's walk plane, in world Y. What the client's ambience hangs its
	-- cloud sea below; on an expedition server there is nothing else to
	-- measure it from.
	FloorY: number,
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
