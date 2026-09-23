--!strict
-- The pure half of vault keys (build spec §7.5). Owner-directed 2026-09-23:
--
--   * A world's key drops from its boss, at the world's DropChance (20% for
--     Sky Citadel), and ONLY in a map that actually has a vault in it.
--   * One roll per party. If it drops, every member present gets one.
--   * Keys are kept: saved to the profile, carried home, brought back.
--   * At most one of each kind of key per player (GameConfig.Loot
--     .MaxKeysPerKind). Using it takes it back to zero.
--   * World modifiers will move the drop chance (a hypothetical "Shattered"
--     modifier at -5% turns 20% into 15%) but never the vault's own spawn
--     chance. Modifiers are still build spec §7-excluded; the SLOT is here so
--     they can plug in without touching this file (docs/RESERVED.md).
--
-- PURE: profile tables in, answers out.

local KeyCore = {}

--- The drop chance after modifiers: base plus every modifier's
--- KeyChanceDelta, clamped to [0, 1]. `modifiers` is empty until world
--- modifiers exist.
function KeyCore.dropChance(base: number, modifiers: { any }?): number
	local chance = base
	for _, m in modifiers or {} do
		chance += (m.KeyChanceDelta or 0)
	end
	return math.clamp(chance, 0, 1)
end

--- Whether a map offers its world's key at all: only if some placed piece
--- has a VAULT fixture. `chunkIds` are the pieces in the map; `fixtures` is
--- the world's Content/Fixtures set (or nil).
function KeyCore.mapHasVault(chunkIds: { string }, fixtures: any?): boolean
	if not fixtures then
		return false
	end
	for _, chunkId in chunkIds do
		for _, row in fixtures.Placements[chunkId] or {} do
			if row.Kind == "VAULT" then
				return true
			end
		end
	end
	return false
end

--- How many of this key the player holds.
function KeyCore.count(keys: { [string]: number }?, keyId: string): number
	return (keys and keys[keyId]) or 0
end

--- Gives one key, up to the cap. Returns true if the count changed -- a
--- player already holding one keeps exactly one.
function KeyCore.grant(keys: { [string]: number }, keyId: string, cap: number): boolean
	local have = keys[keyId] or 0
	if have >= cap then
		return false
	end
	keys[keyId] = have + 1
	return true
end

--- Uses one key. Returns false, and changes nothing, if there is none.
function KeyCore.spend(keys: { [string]: number }, keyId: string): boolean
	local have = keys[keyId] or 0
	if have <= 0 then
		return false
	end
	keys[keyId] = if have - 1 > 0 then have - 1 else nil
	return true
end

return KeyCore
