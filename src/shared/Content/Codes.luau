--!strict
-- REDEEMABLE CODES, AS DATA. Adding one is one row; no System changes.
--
-- A code grants Fate points directly rather than naming a reason out of
-- GameConfig.Progression.Rewards, because a code's value is the whole point of
-- the code and lives with it. `CodeCore` owns every rule about whether a
-- redemption is allowed; this file owns only what exists.
--
-- CASE AND SPACING DO NOT MATTER. CodeCore normalises input before comparing,
-- so "luck bound" and "LUCKBOUND" are the same code -- a player retyping a
-- code off a video should not fail on a space.
--
-- ExpiresAt is a Unix timestamp or nil for "never". A code that has expired
-- stays in this file rather than being deleted: deleting it turns a clear
-- "that code has expired" into a confusing "that code is not valid".

local Codes = {
	LAUNCH = {
		Id = "LAUNCH",
		Code = "LUCKBOUND",
		Fate = 150,
		Message = "Welcome to the Crossroads.",
		ExpiresAt = nil,
	},
	FIRSTROLL = {
		Id = "FIRSTROLL",
		Code = "FATEENGINE",
		Fate = 100,
		Message = "The Engine remembers you.",
		ExpiresAt = nil,
	},
	TESTER = {
		Id = "TESTER",
		Code = "EARLYFATE",
		Fate = 500,
		Message = "For walking it before anyone else.",
		ExpiresAt = nil,
	},
}

return Codes
