--!strict
-- LOCK-ON RULES: which target a press picks, and when a lock drops. No
-- Roblox in here; the controller measures, this decides.
--
-- Lock-on is optional (owner, 2026-09-28): everything plays without it. A
-- target is anything the game has tagged with Constants.NAMES.LOCK_ON_TAG,
-- so an enemy asset never has to know lock-on exists.

local LockOnCore = {}

--- Picks the best target from measured candidates, or nil.
---
---   candidates = { { Id, Distance, AngleRadians, Visible }, ... }
---
--- AngleRadians is the angle between the camera's look and the direction to
--- the candidate. Lowest score wins: AngleWeight x angle + distance / Range,
--- so the thing you are looking at beats the thing that is merely close.
function LockOnCore.pick(candidates: { any }, config: any): any?
	local tuning = config.LockOn
	local best, bestScore = nil, math.huge
	for _, c in candidates do
		if
			c.Visible
			and c.Distance <= tuning.Range
			and c.AngleRadians <= tuning.MaxAngleRadians
		then
			local score = tuning.AngleWeight * c.AngleRadians + c.Distance / tuning.Range
			if score < bestScore then
				best, bestScore = c, score
			end
		end
	end
	return best
end

--- Should a held lock drop? `outOfSightSeconds` is how long the target has
--- been continuously hidden. Returns (drop, reason).
function LockOnCore.shouldBreak(
	distance: number,
	outOfSightSeconds: number,
	stillTagged: boolean,
	config: any
): (boolean, string?)
	local tuning = config.LockOn
	if not stillTagged then
		return true, "gone"
	end
	if distance > tuning.BreakRange then
		return true, "range"
	end
	if outOfSightSeconds >= tuning.LostSightSeconds then
		return true, "sight"
	end
	return false, nil
end

--- The height the camera aims at: the target's centre, but never more than
--- MaxAimHeight above the player's root, so a boss does not pull the camera
--- into the sky.
function LockOnCore.aimHeight(targetY: number, playerY: number, config: any): number
	return math.min(targetY, playerY + config.LockOn.MaxAimHeight)
end

--- Frame-rate independent smoothing factor for a lerp: closes most of the
--- gap in `smoothSeconds`, whatever the frame time.
function LockOnCore.smoothAlpha(dt: number, smoothSeconds: number): number
	if smoothSeconds <= 0 then
		return 1
	end
	return 1 - math.exp(-dt / smoothSeconds)
end

return LockOnCore
