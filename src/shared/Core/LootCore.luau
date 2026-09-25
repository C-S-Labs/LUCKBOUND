--!strict
-- The pure half of loot (build spec §7.5): what a pool yields, for whom.
--
-- WHAT IS DECIDED HERE AND WHAT IS NOT. The owner set the SHAPE on 2026-09-23
-- -- "everyone gets different loot from all drops, whether it be chests,
-- vaults, or bosses" -- and deferred the CONTENTS until the loot pools are
-- built. So the machinery is real and tested, and every pool ships with an
-- empty Entries list: a chest opens, every party member gets their own roll,
-- and the roll is empty until a designer fills the pool. Filling one is a
-- content edit (Content/LootPools/<World>.luau), never a code change.
--
-- PURE: no Roblox types, no Random -- the caller's System owns the stream
-- (AGENTS.md rule 6) and passes a function returning [0, 1).

local LootCore = {}

export type Entry = {
	ItemId: string, -- UPPER_SNAKE; what the item IS is not decided yet (§7.5)
	Weight: number,
	Min: number?, -- count range, default 1..1
	Max: number?,
}

export type Pool = {
	Id: string,
	WorldId: string,
	Rolls: number, -- draws per player per opening
	Entries: { Entry },
}

export type Drop = { ItemId: string, Count: number }

--- One player's share of one opening: Rolls weighted draws from the pool.
--- An empty pool yields an empty list, which is a valid, expected result.
function LootCore.roll(pool: Pool, nextNumber: () -> number): { Drop }
	local drops: { Drop } = {}
	local total = 0
	for _, e in pool.Entries do
		total += e.Weight
	end
	if total <= 0 then
		return drops
	end
	for _ = 1, pool.Rolls do
		local pick = nextNumber() * total
		for _, e in pool.Entries do
			pick -= e.Weight
			if pick < 0 then
				local lo, hi = e.Min or 1, e.Max or e.Min or 1
				local count = lo + math.floor(nextNumber() * (hi - lo + 1))
				table.insert(drops, { ItemId = e.ItemId, Count = math.min(count, hi) })
				break
			end
		end
	end
	return drops
end

--- Everyone's share: each member rolls on their OWN stream, so two players
--- at the same chest get different loot (owner, 2026-09-23). Keyed by UserId.
function LootCore.rollForAll(
	pool: Pool,
	userIds: { number },
	streamFor: (userId: number) -> () -> number
): { [number]: { Drop } }
	local out: { [number]: { Drop } } = {}
	for _, userId in userIds do
		out[userId] = LootCore.roll(pool, streamFor(userId))
	end
	return out
end

return LootCore
