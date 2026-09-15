--!strict
-- Weighted selection over a pool. Build spec T-106.
-- Never uses math.random -- callers pass a nextNumber() closure (in production,
-- one wrapping a server-owned Random instance) so every roll is seedable,
-- auditable, and testable headlessly. Build spec §3.4.

local WeightedRandom = {}

export type NextNumber = () -> number -- returns [0,1)

--- Picks one entry from `pool`. `weightOf` maps an entry to its weight.
--- Weights need not be normalised. Entries with weight <= 0 are skipped.
--- Returns nil only if every entry has non-positive weight.
function WeightedRandom.pick<T>(pool: { T }, weightOf: (T) -> number, nextNumber: NextNumber): T?
	local total = 0
	for _, entry in pool do
		local w = weightOf(entry)
		if w > 0 then
			total += w
		end
	end

	if total <= 0 then
		return nil
	end

	local target = nextNumber() * total
	local cursor = 0

	for _, entry in pool do
		local w = weightOf(entry)
		if w > 0 then
			cursor += w
			if target < cursor then
				return entry
			end
		end
	end

	-- Floating-point drift only; return the last positive-weight entry.
	for i = #pool, 1, -1 do
		if weightOf(pool[i]) > 0 then
			return pool[i]
		end
	end
	return nil
end

--- Returns each entry's normalised probability. Used by tests and by the
--- debug UI that shows players their current odds.
function WeightedRandom.probabilities<T>(pool: { T }, weightOf: (T) -> number): { [T]: number }
	local total = 0
	for _, entry in pool do
		local w = weightOf(entry)
		if w > 0 then
			total += w
		end
	end

	local out: { [T]: number } = {}
	if total <= 0 then
		return out
	end

	for _, entry in pool do
		local w = weightOf(entry)
		out[entry] = if w > 0 then w / total else 0
	end
	return out
end

return WeightedRandom
