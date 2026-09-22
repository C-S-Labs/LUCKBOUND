--!strict
-- Deep-freeze a content or config table, so a System cannot mutate the data
-- it was handed. Three Core modules each carried a byte-identical private copy
-- of this -- Constants, GameConfig and UITheme -- which is the kind of
-- duplication that survives precisely because it is small enough to ignore.

local Freeze = {}

--- Freezes a table and everything reachable from it, returning the same table.
---
--- Guards against a table reachable by two paths -- UITheme reuses Constants'
--- rarity tables -- because freezing an already-frozen table raises.
function Freeze.deep<T>(t: T): T
	if table.isfrozen(t :: any) then
		return t
	end
	for _, v in pairs(t :: any) do
		if type(v) == "table" and not table.isfrozen(v) then
			Freeze.deep(v)
		end
	end
	return table.freeze(t :: any) :: T
end

return Freeze
