--!strict
-- MOVEMENT RULES: one state machine for everything a player does to get
-- around -- walk, sprint, jump, sprint-jump, air jump, dash -- plus the hook
-- a weapon move uses to hold movement still. No Roblox in here.
--
-- SCOPE, AND IT IS DELIBERATELY NARROW. A player has movement; an item has
-- combat (docs/PLAYER_ABILITIES.md §0). Damage, reach, hitboxes, i-frames and
-- animations belong to the ITEM that grants them, and none of them may appear
-- in this file. What this file DOES own is the contract a weapon move talks
-- to: the movement mode it can read, and `lock` / `unlock` to root, slow or
-- pin the player for the length of a swing (docs/PLAYER_ABILITIES.md §6).
--
-- THE MODES. `mode()` derives exactly one of them from the state:
--   LOCKED  a weapon move holds movement (its lock decides what is still allowed)
--   DASH    a dash is in flight
--   GROUND  on the floor (walking or sprinting -- sprint is a flag, not a mode)
--   AIR     off the floor (jumping, falling, sprint-jump carry)
-- The mode is never stored, so it can never disagree with the timers.
--
-- WHY A PURE CORE FOR SOMETHING THE CLIENT OWNS ANYWAY. Roblox movement is
-- client-authoritative by construction: the server cannot stop a character
-- running or dashing. What it CAN do is refuse outcomes, and those are guarded
-- where they happen (roll distance, expedition entry, and later hit
-- resolution in CombatCore). What this core buys is that stamina, the jump
-- budget, the coyote window, the dash cooldown and the lock rules are
-- testable, which a Humanoid.StateChanged handler is not.

local LocomotionCore = {}

--- A fresh movement state. `now` seeds the timers so that a state created
--- mid-session does not think it has been airborne since the epoch.
function LocomotionCore.newState(config: any, now: number): any
	return {
		Stamina = config.Locomotion.StaminaMax,
		Sprinting = false,
		-- Stamina does not refill before this time: after running dry (so the
		-- player cannot tap sprint at 0 forever) and briefly after a dash.
		RegenBlockedUntil = 0,
		AirJumpsUsed = 0,
		-- The ground jump is a budget of one too, tracked separately from the
		-- air jumps: without it, a ground jump inside the coyote window could
		-- be spent twice before the character has physically left the floor.
		GroundJumpSpent = false,
		-- Set by a ground jump taken while sprinting; cleared on landing. While
		-- it holds, the character keeps a little more than sprint speed in the
		-- air, which is what makes the jump longer.
		SprintJumping = false,
		Grounded = true,
		LastGroundedAt = now,
		LastAirJumpAt = 0,
		DashEndsAt = 0,
		DashReadyAt = 0,
		AirDashesUsed = 0,
		-- nil, or the active weapon lock (see `lock`).
		Lock = nil,
	}
end

--- The one movement mode this state is in right now. See the header.
function LocomotionCore.mode(state: any, now: number): string
	if state.Lock and now < state.Lock.Until then
		return "LOCKED"
	end
	if now < state.DashEndsAt then
		return "DASH"
	end
	return if state.Grounded then "GROUND" else "AIR"
end

--- The active lock, or nil once it has run out.
local function activeLock(state: any, now: number): any
	local lock = state.Lock
	if lock and now < lock.Until then
		return lock
	end
	return nil
end

--- Can a sprint START right now? Deliberately stricter than "is sprinting":
--- a sprint already running continues to the floor, but a new one needs
--- headroom, so sprint does not become a stutter at low stamina.
function LocomotionCore.canStartSprint(state: any, now: number, config: any): boolean
	local lock = activeLock(state, now)
	if lock and not lock.AllowSprint then
		return false
	end
	if now < state.RegenBlockedUntil then
		return false
	end
	return state.Stamina > config.Locomotion.StaminaSprintFloor
end

--- Advances the model one frame. Pure: returns a NEW state.
---
--- `input` = { WantsSprint, Moving, Grounded, Now }
function LocomotionCore.step(state: any, dt: number, input: any, config: any): any
	local tuning = config.Locomotion
	local now = input.Now

	local updated = table.clone(state)
	updated.Grounded = input.Grounded

	-- === GROUND ===
	-- Landing refills every budget. While airborne, LastGroundedAt keeps the
	-- moment the character left the floor, which is what the coyote window is
	-- measured from.
	if input.Grounded then
		updated.AirJumpsUsed = 0
		updated.AirDashesUsed = 0
		updated.GroundJumpSpent = false
		updated.SprintJumping = false
		updated.LastGroundedAt = now
	end

	-- === LOCK ===
	-- A lock that has run out is dropped here, so nothing downstream has to
	-- ask whether a stale lock still counts.
	local lock = activeLock(updated, now)
	updated.Lock = lock

	-- === SPRINT ===
	-- You must be MOVING to burn stamina. Holding the sprint key while stood
	-- still is not a sprint, and draining for it would teach players to let
	-- go of a key that costs nothing.
	local wantsSprint = input.WantsSprint and input.Moving and not (lock and not lock.AllowSprint)
	local sprinting = false
	if wantsSprint then
		if state.Sprinting then
			sprinting = updated.Stamina > 0
		else
			sprinting = LocomotionCore.canStartSprint(updated, now, config)
		end
	end

	-- A dash already paid for itself; sprinting through one does not also drain.
	local dashing = now < updated.DashEndsAt
	if sprinting and not dashing then
		updated.Stamina = math.max(0, updated.Stamina - tuning.StaminaDrainPerSecond * dt)
		if updated.Stamina <= 0 then
			sprinting = false
			updated.RegenBlockedUntil = now + tuning.StaminaRegenDelaySeconds
		end
	elseif not sprinting and now >= updated.RegenBlockedUntil then
		updated.Stamina =
			math.min(tuning.StaminaMax, updated.Stamina + tuning.StaminaRegenPerSecond * dt)
	end

	updated.Sprinting = sprinting
	return updated
end

--- The WalkSpeed this state implies. Base is GameConfig.Scale.WalkSpeed --
--- the hub traversal budget owns that number and every other speed here is a
--- multiplier on it, never a second speed to keep in step with it.
---
--- `now` is optional so older callers that only care about sprint still
--- work; without it a lock is read as if it were still running.
function LocomotionCore.targetSpeed(state: any, config: any, now: number?): number
	local tuning = config.Locomotion
	local base = config.Scale.WalkSpeed

	local lock = if now then activeLock(state, now) else state.Lock
	if lock then
		return base * lock.SpeedMultiplier
	end

	if state.Sprinting then
		local speed = base * tuning.SprintMultiplier
		if state.SprintJumping and not state.Grounded then
			speed *= tuning.SprintJumpCarry
		end
		return speed
	end
	return base
end

--- Stamina as 0..1, for the pip.
function LocomotionCore.staminaFraction(state: any, config: any): number
	local max = config.Locomotion.StaminaMax
	if max <= 0 then
		return 1
	end
	return math.clamp(state.Stamina / max, 0, 1)
end

--- WHAT DOES PRESSING JUMP DO RIGHT NOW? Returns "GROUND", "AIR" or nil.
---
--- The coyote window is the interesting part: for a moment after walking off
--- an edge the FIRST press is still the ground jump, so stepping off a
--- walkway and jumping does not silently spend the air jump. Every platformer
--- has this and nobody notices it until it is missing.
function LocomotionCore.jumpKind(state: any, now: number, config: any): string?
	local tuning = config.Locomotion

	local lock = activeLock(state, now)
	if lock and not lock.AllowJump then
		return nil
	end

	if state.GroundJumpSpent then
		-- A character is still reported as grounded for a frame or two after
		-- its own jump. Without this the second of those frames would spend
		-- the air jump on what the player felt as one press.
		if state.Grounded then
			return nil
		end
	elseif state.Grounded or now - state.LastGroundedAt <= tuning.CoyoteTimeSeconds then
		return "GROUND"
	end

	if state.AirJumpsUsed >= tuning.AirJumps then
		return nil
	end

	if now - state.LastAirJumpAt < tuning.AirJumpCooldownSeconds then
		-- One input frame must not spend two jumps.
		return nil
	end

	return "AIR"
end

--- Spends a jump. Returns the new state and the kind spent (nil if the press
--- did nothing, which is a legitimate outcome and not an error).
---
--- A jump out of a dash ends the dash: jumping is the one way to cancel a
--- dash early, so a dash off a ledge can still be saved.
function LocomotionCore.jump(state: any, now: number, config: any): (any, string?)
	local kind = LocomotionCore.jumpKind(state, now, config)
	if kind == nil then
		return state, nil
	end

	local updated = table.clone(state)
	if now < updated.DashEndsAt then
		updated.DashEndsAt = now
	end
	if kind == "AIR" then
		updated.AirJumpsUsed = state.AirJumpsUsed + 1
		updated.LastAirJumpAt = now
	else
		-- A ground jump inside the coyote window CONSUMES the ground jump:
		-- the window exists to forgive a late press, not to hand out a third
		-- jump to anyone who steps off an edge.
		updated.GroundJumpSpent = true
		updated.SprintJumping = state.Sprinting
	end
	return updated, kind
end

--- The upward speed a jump of this kind launches at, in studs/s. A sprint
--- jump goes a little higher as well as further; an air jump is a recovery,
--- noticeably less than a full jump.
function LocomotionCore.jumpVelocity(state: any, kind: string, config: any): number
	local tuning = config.Locomotion
	if kind == "AIR" then
		return tuning.JumpPower * tuning.AirJumpPower
	end
	if state.SprintJumping then
		return tuning.JumpPower * tuning.SprintJumpPower
	end
	return tuning.JumpPower
end

--- CAN THE PLAYER DASH RIGHT NOW? Returns (ok, reason). The reason is for
--- tests and the dev panel, never shown to a player.
function LocomotionCore.canDash(state: any, now: number, config: any): (boolean, string?)
	local tuning = config.Locomotion

	local lock = activeLock(state, now)
	if lock and not lock.AllowDash then
		return false, "locked"
	end
	if now < state.DashEndsAt then
		return false, "dashing"
	end
	if now < state.DashReadyAt then
		return false, "cooldown"
	end
	if not state.Grounded and state.AirDashesUsed >= tuning.AirDashes then
		return false, "airborne"
	end
	if state.Stamina < tuning.DashStaminaCost then
		return false, "stamina"
	end
	return true, nil
end

--- Spends a dash. Returns the new state and whether it happened. Direction
--- and physics are the controller's job; this decides only whether, when and
--- for how long.
---
--- Invulnerability frames are NOT here. A dodge is a combat ability wearing
--- movement's clothes (PLAYER_ABILITIES.md §4): the combat layer reads the
--- dash window from `mode()` == "DASH" and decides for itself what it is
--- worth.
function LocomotionCore.dash(state: any, now: number, config: any): (any, boolean)
	if not LocomotionCore.canDash(state, now, config) then
		return state, false
	end

	local tuning = config.Locomotion
	local updated = table.clone(state)
	updated.Stamina = state.Stamina - tuning.DashStaminaCost
	updated.DashEndsAt = now + tuning.DashDurationSeconds
	updated.DashReadyAt = now + tuning.DashCooldownSeconds
	updated.RegenBlockedUntil =
		math.max(state.RegenBlockedUntil, now + tuning.DashRegenPauseSeconds)
	if not state.Grounded then
		updated.AirDashesUsed = state.AirDashesUsed + 1
	end
	return updated, true
end

--- THE WEAPON HOOK. A weapon move locks movement for its own length:
---
---   spec = {
---     DurationSeconds,   -- how long; clamped to Locomotion.MaxLockSeconds
---     SpeedMultiplier?,  -- 0 roots the player, 1 leaves speed alone; default 0
---     AllowJump?, AllowDash?, AllowSprint?,  -- default false
---     Source?,           -- who asked (a move id), for the dev panel
---   }
---
--- The clamp is the point: a weapon script that forgets to unlock, or asks
--- for an hour, still hands movement back. A new lock replaces the old one
--- rather than stacking, because a combo is one move after another, never two
--- at once.
function LocomotionCore.lock(state: any, now: number, spec: any, config: any): any
	local tuning = config.Locomotion
	local duration = math.clamp(spec.DurationSeconds or 0, 0, tuning.MaxLockSeconds)
	local updated = table.clone(state)
	updated.Lock = {
		Until = now + duration,
		SpeedMultiplier = math.clamp(spec.SpeedMultiplier or 0, 0, 1),
		AllowJump = spec.AllowJump == true,
		AllowDash = spec.AllowDash == true,
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

return LocomotionCore
