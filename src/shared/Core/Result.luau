--!strict
-- Expected-failure convention. Reserve error() for programmer mistakes.

local Result = {}

function Result.ok<T>(value: T)
	return { ok = true :: true, value = value }
end

function Result.err(message: string)
	return { ok = false :: false, err = message }
end

return Result
