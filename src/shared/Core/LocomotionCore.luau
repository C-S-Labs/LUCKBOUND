--!strict
-- MOVEMENT RULES: sprint stamina and the air jump, with no Roblox in them.
--
-- SCOPE, AND IT IS DELIBERATELY NARROW. Phase 1 player abilities are movement
-- and nothing else. Damage, reach, cooldowns, effects and animations belong to
-- the ITEM that grants them -- a sword model carries its own attributes and
-- its own script -- and none of them may appear in this file. If a future
-- ability needs a number from here, it is either movement (and belongs) or it
-- is combat (and belongs to the item). docs/PLAYER_ABILITIES.md holds the
-- planned ladder and which side of that line each rung falls on.
--
-- WHY A PURE CORE FOR SOMETHING THE CLIENT OWNS ANYWAY. Roblox movement is
-- client-authoritative by construction: the server cannot stop a character
-- running. What it CAN do is refuse outcomes, and the outcomes are already
-- guarded elsewhere (roll distance, expedition eligibility). What this core
-- buys is not security -- it is that stamina, the coyote window and the jump
-- budget are testable, which a Humanoid.StateChanged handler is not.

local LocomotionCore = {}

--- A fresh movement state. `now` seeds the timers so that a state created
--- mid-session does not think it has been airborne since the epoch.
function LocomotionCore.newState(config: any, now: number): any
	return {
		Stamina = config.Locomotion.StaminaMax,
		Sprinting = false,
		-- Sprint is refused until this time once stamina hits zero, so the
		-- player cannot tap the key at 0 forever.
		RegenBlockedUntil = 0,
		AirJumpsUsed = 0,
		-- The ground jump is a budget of one too, tracked separately from the
		-- air jumps: without it, a ground jump inside the coyote window could
		-- be spent twice before the character has physically left the floor.
		GroundJumpSpent = false,
		Grounded = true,
		LastGroundedAt = now,
		LastAirJumpAt = 0,
	}
end

--- Can a sprint START right now? Deliberately stricter than "is sprinting":
--- a sprint already running continues to the floor, but a new one needs
--- headroom, so sprint does not become a stutter at low stamina.
function LocomotionCore.canStartSprint(state: any, now: number, config: any): boolean
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

	local updated = {
		Stamina = state.Stamina,
		Sprinting = state.Sprinting,
		RegenBlockedUntil = state.RegenBlockedUntil,
		AirJumpsUsed = state.AirJumpsUsed,
		GroundJumpSpent = state.GroundJumpSpent,
		Grounded = input.Grounded,
		LastGroundedAt = state.LastGroundedAt,
		LastAirJumpAt = state.LastAirJumpAt,
	}

	-- === GROUND ===
	-- Landing refills the jump budget, and the moment of leaving the ground
	-- is remembered so the coyote window can be measured from it.
	-- Landing refills BOTH budgets. While airborne, LastGroundedAt keeps the
	-- moment the character left the floor, which is what the coyote window is
	-- measured from.
	if input.Grounded then
		updated.AirJumpsUsed = 0
		updated.GroundJumpSpent = false
		updated.LastGroundedAt = now
	end

	-- === SPRINT ===
	-- You must be MOVING to burn stamina. Holding the sprint key while stood
	-- still is not a sprint, and draining for it would teach players to let
	-- go of a key that costs nothing.
	local wantsSprint = input.WantsSprint and input.Moving
	local sprinting = false
	if wantsSprint then
		if state.Sprinting then
			sprinting = updated.Stamina > 0
		else
			sprinting = LocomotionCore.canStartSprint(state, now, config)
		end
	end

	if sprinting then
		updated.Stamina = math.max(0, updated.Stamina - tuning.StaminaDrainPerSecond * dt)
		if updated.Stamina <= 0 then
			sprinting = false
			updated.RegenBlockedUntil = now + tuning.StaminaRegenDelaySeconds
		end
	elseif now >= updated.RegenBlockedUntil then
		updated.Stamina =
			math.min(tuning.StaminaMax, updated.Stamina + tuning.StaminaRegenPerSecond * dt)
	end

	updated.Sprinting = sprinting
	return updated
end

--- The WalkSpeed this state implies. Base is GameConfig.Scale.WalkSpeed --
--- the hub traversal budget owns that number and sprint is a multiplier on
--- it, never a second speed to keep in step with it.
function LocomotionCore.targetSpeed(state: any, config: any): number
	if state.Sprinting then
		return config.Scale.WalkSpeed * config.Locomotion.SprintMultiplier
	end
	return config.Scale.WalkSpeed
end

--- Stamina as 0..1, for the ring under the sprint pip.
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
function LocomotionCore.jump(state: any, now: number, config: any): (any, string?)
	local kind = LocomotionCore.jumpKind(state, now, config)
	if kind == nil then
		return state, nil
	end

	local updated = table.clone(state)
	if kind == "AIR" then
		updated.AirJumpsUsed = state.AirJumpsUsed + 1
		updated.LastAirJumpAt = now
	else
		-- A ground jump inside the coyote window CONSUMES the ground jump:
		-- the window exists to forgive a late press, not to hand out a third
		-- jump to anyone who steps off an edge.
		updated.GroundJumpSpent = true
	end
	return updated, kind
end

return LocomotionCore
