--!strict
-- MOVEMENT RULES: one state machine for everything a player does to get
-- around -- walk, sprint, jump, roll, backstep -- plus the hook a weapon move
-- uses to hold movement still. No Roblox in here.
--
-- SCOPE, AND IT IS DELIBERATELY NARROW. A player has movement; an item has
-- combat (docs/PLAYER_ABILITIES.md §0). Damage, reach and hitboxes belong to
-- the ITEM that grants them. What this file owns is the contract a weapon
-- move talks to: the mode it can read, the roll's invulnerable window it can
-- ask about, and `lock` / `unlock` to root or slow the player for a swing
-- (docs/PLAYER_ABILITIES.md §6).
--
-- THE MODES. `mode()` derives exactly one of them from the state:
--   LOCKED  a weapon move holds movement (its lock decides what is allowed)
--   ROLL    a roll or backstep is in flight, recovery included
--   GROUND  on the floor (walking or sprinting -- sprint is a flag, not a mode)
--   AIR     off the floor
-- The mode is never stored, so it can never disagree with the timers.
--
-- PROFILES. The hub and an expedition run the same rules at different
-- weights (GameConfig.Locomotion.Profiles). `tuning()` flattens the shared
-- numbers and one profile into the table every other function takes, and is
-- the single place a Fate Tree upgrade will scale them.
--
-- WHY A PURE CORE FOR SOMETHING THE CLIENT OWNS ANYWAY. Roblox movement is
-- client-authoritative by construction. The server guards outcomes where
-- they happen. What this core buys is that stamina, the jump and roll rules
-- and the lock are testable, which a physics callback is not.

local LocomotionCore = {}

--- THE TUNING FOR ONE PROFILE. Shared numbers, then the profile's, then the
--- speeds resolved to studs/s against Scale.WalkSpeed.
---
--- `upgrades` is RESERVED (docs/RESERVED.md): the Fate Tree's movement and
--- stamina nodes, as { [field] = multiplier }. Applied last, to any number.
function LocomotionCore.tuning(config: any, profileId: string, upgrades: any?): any
	local shared = config.Locomotion
	local profile = shared.Profiles[profileId] or shared.Profiles.HUB
	local t = {}
	for key, value in shared do
		if key ~= "Profiles" then
			t[key] = value
		end
	end
	for key, value in profile do
		t[key] = value
	end
	t.ProfileId = if shared.Profiles[profileId] then profileId else "HUB"
	t.WalkSpeed = config.Scale.WalkSpeed * profile.SpeedScale
	t.SprintSpeed = t.WalkSpeed * profile.SprintMultiplier
	if upgrades then
		for key, multiplier in upgrades do
			if type(t[key]) == "number" and type(multiplier) == "number" then
				t[key] *= multiplier
			end
		end
	end
	return t
end

--- A fresh movement state. `now` seeds the timers so that a state created
--- mid-session does not think it has been airborne since the epoch.
function LocomotionCore.newState(t: any, now: number): any
	return {
		Stamina = t.StaminaMax,
		Sprinting = false,
		-- Stamina does not refill before this time.
		RegenBlockedUntil = 0,
		-- The jump is a budget of one per landing: without the flag, a jump
		-- inside the coyote window could be spent twice before the character
		-- has physically left the floor.
		JumpSpent = false,
		JumpBufferedUntil = 0,
		Grounded = true,
		LastGroundedAt = now,
		-- The current roll. RollKind is "ROLL" or "BACKSTEP" (nil = none);
		-- RollEndsAt is the end of the movement, RollRecoverUntil the end of
		-- the recovery after it.
		RollKind = nil,
		RollStartedAt = 0,
		RollEndsAt = 0,
		RollRecoverUntil = 0,
		-- Air dashes spent since leaving the floor (refilled on landing).
		AirDashesUsed = 0,
		-- A hard landing slows movement until this time (see `land`).
		LandRecoverUntil = 0,
		-- nil, or the active weapon lock (see `lock`).
		Lock = nil,
	}
end

local function activeLock(state: any, now: number): any
	local lock = state.Lock
	if lock and now < lock.Until then
		return lock
	end
	return nil
end

--- The one movement mode this state is in right now. See the header.
function LocomotionCore.mode(state: any, now: number): string
	if activeLock(state, now) then
		return "LOCKED"
	end
	if state.RollKind and now < state.RollRecoverUntil then
		return "ROLL"
	end
	return if state.Grounded then "GROUND" else "AIR"
end

--- Is the player inside a roll's invulnerable window? RESERVED
--- (docs/RESERVED.md): the combat layer asks this when it resolves a hit.
--- Nothing here acts on it.
function LocomotionCore.isInvulnerable(state: any, now: number, t: any): boolean
	if not state.RollKind or state.RollKind == "AIRDASH" then
		-- The air dash is movement only: no invulnerable window.
		return false
	end
	local into = now - state.RollStartedAt
	if state.RollKind == "BACKSTEP" then
		return into >= t.BackstepInvulnerableFrom and into < t.BackstepInvulnerableTo
	end
	return into >= t.RollInvulnerableFrom and into < t.RollInvulnerableTo
end

--- Spend stamina. Any action may START on any stamina above zero; the cost
--- may take the bar to zero, which buys the longer exhausted breather.
local function spend(updated: any, cost: number, now: number, t: any)
	if cost <= 0 then
		return
	end
	updated.Stamina = math.max(0, updated.Stamina - cost)
	local delay = if updated.Stamina <= 0
		then t.StaminaExhaustedDelaySeconds
		else t.StaminaRegenDelaySeconds
	updated.RegenBlockedUntil = math.max(updated.RegenBlockedUntil, now + delay)
end

local function hasStaminaFor(state: any, cost: number): boolean
	return cost <= 0 or state.Stamina > 0
end

--- Can a sprint START right now? Stricter than "is sprinting": a sprint
--- already running continues to the floor, but a new one needs headroom, so
--- sprint does not become a stutter at low stamina.
function LocomotionCore.canStartSprint(state: any, now: number, t: any): boolean
	local lock = activeLock(state, now)
	if lock and not lock.AllowSprint then
		return false
	end
	if now < state.RegenBlockedUntil and state.Stamina <= 0 then
		return false
	end
	return state.Stamina > t.StaminaSprintFloor
end

--- CAN THE PLAYER ROLL RIGHT NOW? Returns (ok, reason). The reason is for
--- tests and the dev panel, never shown to a player.
function LocomotionCore.canRoll(state: any, now: number, t: any): (boolean, string?)
	local lock = activeLock(state, now)
	if lock and not lock.AllowRoll then
		return false, "locked"
	end
	if state.RollKind and now < state.RollRecoverUntil then
		return false, "rolling"
	end
	if not LocomotionCore.onFloor(state, now, t) then
		-- In the air the roll button is the AIR DASH, once per airtime.
		if (state.AirDashesUsed or 0) >= t.AirDashes then
			return false, "airborne"
		end
		if not hasStaminaFor(state, t.AirDashStaminaCost) then
			return false, "stamina"
		end
		return true, nil
	end
	if not hasStaminaFor(state, t.RollStaminaCost) then
		return false, "stamina"
	end
	return true, nil
end

local function startRoll(state: any, now: number, kind: string, t: any): any
	local updated = table.clone(state)
	local duration, cost, recovery
	if kind == "AIRDASH" then
		-- No recovery: the dash hands straight back to the fall.
		duration, cost, recovery = t.AirDashDurationSeconds, t.AirDashStaminaCost, 0
		updated.AirDashesUsed = (state.AirDashesUsed or 0) + 1
	elseif kind == "BACKSTEP" then
		duration = t.BackstepDurationSeconds
		cost = t.RollStaminaCost * t.BackstepStaminaFraction
		recovery = t.RollRecoverySeconds
	else
		duration, cost, recovery = t.RollDurationSeconds, t.RollStaminaCost, t.RollRecoverySeconds
	end
	spend(updated, cost, now, t)
	updated.RollKind = kind
	updated.RollStartedAt = now
	updated.RollEndsAt = now + duration
	updated.RollRecoverUntil = now + duration + recovery
	updated.Sprinting = false
	return updated
end

--- PRESS ROLL. On the ground: a roll the held way (`hasDirection`) or a
--- backstep (none). In the air: an AIR DASH, once per airtime, the held way
--- or forward. Returns the new state and the kind started ("ROLL",
--- "BACKSTEP", "AIRDASH"), or nil. A press during a roll's last moments is
--- buffered, not dropped.
function LocomotionCore.roll(state: any, now: number, hasDirection: boolean, t: any): (any, string?)
	local airborne = not LocomotionCore.onFloor(state, now, t)
	local kind = if airborne then "AIRDASH" elseif hasDirection then "ROLL" else "BACKSTEP"
	-- NO QUEUE (owner, 2026-09-28): a press that cannot roll now -- during a
	-- roll, its recovery, a lock -- is ignored, not remembered. The next roll
	-- needs a fresh press after this one has fully finished.
	if not LocomotionCore.canRoll(state, now, t) then
		return state, nil
	end
	return startRoll(state, now, kind, t), kind
end

--- On the floor for rolling purposes: grounded, or off it for no longer than
--- AirDashMinAirSeconds (a bump mid-roll, the lip of a step). Such a moment
--- is not "in the air", so the press is a roll, never an air dash.
function LocomotionCore.onFloor(state: any, now: number, t: any): boolean
	-- An accepted jump is intentional airtime immediately, even before the
	-- floor sensor clears. Grace applies only to walking off a lip/bump.
	return state.Grounded
		or (not state.JumpSpent and now - state.LastGroundedAt <= t.AirDashMinAirSeconds)
end

--- WHAT DOES PRESSING JUMP DO RIGHT NOW? true if it jumps.
---
--- The coyote window: for a moment after walking off an edge the press is
--- still a jump, so stepping off a walkway and jumping is not silently lost.
function LocomotionCore.canJump(state: any, now: number, t: any): boolean
	local lock = activeLock(state, now)
	if lock and not lock.AllowJump then
		return false
	end
	if state.RollKind and now < state.RollRecoverUntil then
		return false
	end
	if state.JumpSpent then
		return false
	end
	if not (state.Grounded or now - state.LastGroundedAt <= t.CoyoteTimeSeconds) then
		return false
	end
	return hasStaminaFor(state, t.JumpStaminaCost)
end

--- PRESS JUMP. Returns the new state and whether it jumped. A press that
--- cannot jump yet (still falling, still rolling) is buffered briefly, so a
--- jump pressed a moment before landing is not eaten.
function LocomotionCore.jump(state: any, now: number, t: any): (any, boolean)
	if LocomotionCore.canJump(state, now, t) then
		local updated = table.clone(state)
		updated.JumpSpent = true
		updated.Grounded = false
		updated.JumpBufferedUntil = 0
		spend(updated, t.JumpStaminaCost, now, t)
		return updated, true
	end
	local updated = table.clone(state)
	updated.JumpBufferedUntil = now + t.JumpBufferSeconds
	return updated, false
end

--- Advances the model one frame. Pure: returns a NEW state plus what fired
--- this frame, so the controller can act on a buffered press:
---   events = { Jumped: boolean, Rolled: string? }
---
--- `input` = { WantsSprint, Moving, Grounded, HasDirection, Now }
function LocomotionCore.step(state: any, dt: number, input: any, t: any): (any, any)
	local now = input.Now
	local events = { Jumped = false, Rolled = nil :: string? }

	local updated = table.clone(state)
	updated.Grounded = input.Grounded

	-- === GROUND ===
	-- Landing refills the jump. While airborne, LastGroundedAt keeps the
	-- moment the character left the floor, which the coyote window measures from.
	if input.Grounded then
		updated.JumpSpent = false
		updated.AirDashesUsed = 0
		updated.LastGroundedAt = now
	end

	-- === LOCK and ROLL expiry ===
	updated.Lock = activeLock(updated, now)
	if updated.RollKind and now >= updated.RollRecoverUntil then
		updated.RollKind = nil
	end

	-- === BUFFERED JUMP ===
	if
		not events.Rolled
		and updated.JumpBufferedUntil > 0
		and now <= updated.JumpBufferedUntil
		and LocomotionCore.canJump(updated, now, t)
	then
		updated.JumpSpent = true
		updated.Grounded = false
		updated.JumpBufferedUntil = 0
		spend(updated, t.JumpStaminaCost, now, t)
		events.Jumped = true
	end

	-- === SPRINT ===
	-- You must be MOVING to burn stamina, and you cannot sprint mid-roll.
	local lock = updated.Lock
	local rolling = updated.RollKind ~= nil
	local wantsSprint = input.WantsSprint
		and input.Moving
		and not rolling
		and not (lock and not lock.AllowSprint)
	local sprinting = false
	if wantsSprint then
		if state.Sprinting then
			sprinting = updated.Stamina > 0
		else
			sprinting = LocomotionCore.canStartSprint(updated, now, t)
		end
	end

	if sprinting then
		-- Only on the ground: a sprint-jump keeps its speed without paying
		-- for the airtime.
		if updated.Grounded then
			updated.Stamina = math.max(0, updated.Stamina - t.SprintDrainPerSecond * dt)
			updated.RegenBlockedUntil =
				math.max(updated.RegenBlockedUntil, now + t.StaminaRegenDelaySeconds)
			if updated.Stamina <= 0 then
				sprinting = false
				updated.RegenBlockedUntil = now + t.StaminaExhaustedDelaySeconds
			end
		end
	elseif now >= updated.RegenBlockedUntil then
		updated.Stamina = math.min(t.StaminaMax, updated.Stamina + t.StaminaRegenPerSecond * dt)
	end

	updated.Sprinting = sprinting
	return updated, events
end

--- The speed this state moves at, in studs/s. During a roll this is the
--- roll's own speed; during recovery, a crawl; under a lock, the lock's
--- multiplier of walking speed.
function LocomotionCore.targetSpeed(state: any, now: number, t: any): number
	local lock = activeLock(state, now)
	if lock then
		return t.WalkSpeed * lock.SpeedMultiplier
	end
	if state.RollKind then
		if now < state.RollEndsAt then
			if state.RollKind == "AIRDASH" then
				return t.AirDashSpeed
			end
			if state.RollKind == "BACKSTEP" then
				return t.BackstepSpeed
			end
			local progress = (now - state.RollStartedAt) / (state.RollEndsAt - state.RollStartedAt)
			return LocomotionCore.rollPeakSpeed(t) * LocomotionCore.rollSpeedShape(progress)
		end
		if now < state.RollRecoverUntil then
			return 0
		end
	end
	local speed = if state.Sprinting then t.SprintSpeed else t.WalkSpeed
	if now < (state.LandRecoverUntil or 0) then
		speed *= t.HardLandingSpeedMultiplier
	end
	return speed
end

--- A LANDING at `fallSpeed` studs/s downward. A hard one (past
--- HardLandingSpeed) slows movement for the profile's recovery time: a real
--- drop costs a beat, a normal jump costs nothing. Returns the new state and
--- whether it was hard.
function LocomotionCore.land(state: any, now: number, fallSpeed: number, t: any): (any, boolean)
	if fallSpeed < t.HardLandingSpeed or t.HardLandingRecoverySeconds <= 0 then
		return state, false
	end
	local updated = table.clone(state)
	updated.LandRecoverUntil = now + t.HardLandingRecoverySeconds
	return updated, true
end

--- THE ROLL'S SPEED OVER ITS LENGTH, as a fraction of its peak, at
--- `progress` 0..1. It follows the clip: a gentler start while the body
--- gathers, full speed through the tumble, easing off as it comes up. A flat
--- speed read as a burst before the roll began (owner, 2026-09-28).
function LocomotionCore.rollSpeedShape(progress: number): number
	local p = math.clamp(progress, 0, 1)
	local function smooth(a: number, b: number, x: number): number
		local u = math.clamp((x - a) / (b - a), 0, 1)
		return u * u * (3 - 2 * u)
	end
	if p < 0.22 then
		return 0.45 + 0.55 * smooth(0, 0.22, p)
	elseif p < 0.62 then
		return 1
	end
	return 1 - 0.7 * smooth(0.62, 1, p)
end

--- The shape's average over the roll, measured once: what turns a distance
--- into a peak speed.
local SHAPE_MEAN = (function()
	local total, steps = 0, 400
	for i = 0, steps - 1 do
		total += LocomotionCore.rollSpeedShape((i + 0.5) / steps)
	end
	return total / steps
end)()

--- The peak speed that carries a roll exactly RollDistanceStuds.
function LocomotionCore.rollPeakSpeed(t: any): number
	return t.RollDistanceStuds / (t.RollDurationSeconds * SHAPE_MEAN)
end

--- Is the roll still moving the character (as opposed to recovering)?
function LocomotionCore.rollMoving(state: any, now: number): boolean
	return state.RollKind ~= nil and now < state.RollEndsAt
end

--- Stamina as 0..1, for the bar.
function LocomotionCore.staminaFraction(state: any, t: any): number
	local max = t.StaminaMax
	if max <= 0 then
		return 1
	end
	return math.clamp(state.Stamina / max, 0, 1)
end

--- THE WEAPON HOOK. A weapon move locks movement for its own length:
---
---   spec = {
---     DurationSeconds,   -- how long; clamped to MaxLockSeconds
---     SpeedMultiplier?,  -- 0 roots the player, 1 leaves speed alone; default 0
---     AllowJump?, AllowRoll?, AllowSprint?,  -- what it can cancel into; default false
---     Source?,           -- who asked (a move id), for the dev panel
---   }
---
--- The clamp is the point: a weapon script that forgets to unlock, or asks
--- for an hour, still hands movement back. A new lock replaces the old one
--- rather than stacking: a combo is one move after another, never two at once.
function LocomotionCore.lock(state: any, now: number, spec: any, t: any): any
	local duration = math.clamp(spec.DurationSeconds or 0, 0, t.MaxLockSeconds)
	local updated = table.clone(state)
	updated.Lock = {
		Until = now + duration,
		SpeedMultiplier = math.clamp(spec.SpeedMultiplier or 0, 0, 1),
		AllowJump = spec.AllowJump == true,
		AllowRoll = spec.AllowRoll == true,
		AllowSprint = spec.AllowSprint == true,
		Source = spec.Source,
	}
	return updated
end

--- Releases the lock early (a move that ended or was cancelled).
function LocomotionCore.unlock(state: any): any
	if state.Lock == nil then
		return state
	end
	local updated = table.clone(state)
	updated.Lock = nil
	return updated
end

--- TURNING: rotates a flat direction (x, z) toward a target direction by at
--- most `maxRadians`, keeping it unit length. Returns the new (x, z).
function LocomotionCore.turnToward(
	x: number,
	z: number,
	targetX: number,
	targetZ: number,
	maxRadians: number
): (number, number)
	local current = math.atan2(z, x)
	local target = math.atan2(targetZ, targetX)
	local delta = (target - current + math.pi) % (2 * math.pi) - math.pi
	local angle = current + math.clamp(delta, -maxRadians, maxRadians)
	return math.cos(angle), math.sin(angle)
end

--- Which profile applies: EXPEDITION inside a loaded stage, HUB otherwise.
--- Kept here so the rule is one line anyone can test.
function LocomotionCore.profileFor(insideStage: boolean): string
	return if insideStage then "EXPEDITION" else "HUB"
end

return LocomotionCore
