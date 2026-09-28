--!strict
-- HOW THE BODY READS: the maths behind the character's animation, with no
-- Roblox in it. CharacterAnimator measures the character and applies what
-- this decides; every number comes from GameConfig.CharacterAnimation.
--
-- Presentation only. Nothing here changes where a character goes or how
-- fast -- that is LocomotionCore's. This file decides which clips play, how
-- strongly, how fast, and how the procedural layer bends the body: legs
-- toward a strafe, a lean into speed and turns, the head toward what the
-- player is looking at, a dip on landing, a tumble for a roll without a clip.
--
-- ANGLES. A move angle is measured from the character's facing: 0 is
-- straight ahead, +pi/2 is to the right, +-pi is straight back. Rotations
-- returned for the body are the Roblox convention: a positive yaw turns
-- left, a positive pitch tips the front up, a positive bank tips the top to
-- the left.

local AnimationCore = {}

local TAU = 2 * math.pi

local function clamp(x: number, lo: number, hi: number): number
	return math.max(lo, math.min(hi, x))
end

--- Wraps an angle into (-pi, pi].
function AnimationCore.wrap(angle: number): number
	local a = (angle + math.pi) % TAU
	if a <= 0 then
		a += TAU
	end
	return a - math.pi
end

--- Frame-rate independent smoothing: the fraction of the gap to close this
--- frame so that most of it is closed in `seconds`, whatever the frame time.
function AnimationCore.smoothAlpha(dt: number, seconds: number): number
	if seconds <= 0 then
		return 1
	end
	return 1 - math.exp(-dt / seconds)
end

--- A velocity split along the character's facing: (forward, right), in the
--- velocity's units. Facing is a flat direction (x, z), not necessarily unit.
function AnimationCore.localVelocity(
	facingX: number,
	facingZ: number,
	vx: number,
	vz: number
): (number, number)
	local length = math.sqrt(facingX * facingX + facingZ * facingZ)
	if length < 1e-6 then
		return 0, 0
	end
	local fx, fz = facingX / length, facingZ / length
	-- Right of a flat facing (fx, fz) is (-fz, fx).
	local forward = vx * fx + vz * fz
	local right = vx * -fz + vz * fx
	return forward, right
end

--- The move angle (see the header) of a local velocity.
function AnimationCore.moveAngle(forward: number, right: number): number
	if math.abs(forward) < 1e-6 and math.abs(right) < 1e-6 then
		return 0
	end
	return math.atan2(right, forward)
end

--- Four-way blend weights for directional clips, summing to 1:
--- { Forward, Backward, Left, Right }. A diagonal splits between its two
--- neighbours; a pure direction is all one clip.
function AnimationCore.directionalWeights(angle: number): { [string]: number }
	local c, s = math.cos(angle), math.sin(angle)
	local w = {
		Forward = math.max(0, c),
		Backward = math.max(0, -c),
		Right = math.max(0, s),
		Left = math.max(0, -s),
	}
	local total = w.Forward + w.Backward + w.Right + w.Left
	if total <= 1e-6 then
		return { Forward = 1, Backward = 0, Left = 0, Right = 0 }
	end
	for k, v in w do
		w[k] = v / total
	end
	return w
end

--- THE PROCEDURAL STRAFE, for when there are no directional clips. The
--- forward clip plays, the legs turn toward the movement, and moving mostly
--- backward plays the clip in reverse with the legs turned from behind.
--- Returns (reverse, legYaw) where legYaw is the Roblox yaw to apply to the
--- lower body (positive = left), clamped to MaxLegYawDegrees.
function AnimationCore.procedural(angle: number, config: any): (boolean, number)
	local tuning = config.CharacterAnimation
	local maxYaw = math.rad(tuning.MaxLegYawDegrees)
	local reverse = math.cos(angle) < tuning.BackwardBelowCos
	local legAngle = if reverse then AnimationCore.wrap(angle - math.pi) else angle
	-- A move to the right (positive angle) turns the legs right: negative yaw.
	return reverse, clamp(-legAngle, -maxYaw, maxYaw)
end

--- GAIT: how much of the run clip (vs the walk clip) at this speed, 0..1.
function AnimationCore.runBlend(speed: number, config: any): number
	local tuning = config.CharacterAnimation
	local span = tuning.RunFull - tuning.RunFrom
	if span <= 0 then
		return if speed >= tuning.RunFrom then 1 else 0
	end
	return clamp((speed - tuning.RunFrom) / span, 0, 1)
end

--- The playback rate that makes a clip authored at `clipSpeed` match
--- `speed`, clamped so it never reads as sped-up footage.
function AnimationCore.playbackRate(speed: number, clipSpeed: number, config: any): number
	local tuning = config.CharacterAnimation
	if clipSpeed <= 0 then
		return 1
	end
	return clamp(speed / clipSpeed, tuning.MinPlaybackRate, tuning.MaxPlaybackRate)
end

--- LEAN: (pitch, bank) in radians for the whole body. Leans forward into
--- acceleration (and a little more while sprinting), back when braking, and
--- banks into a turn in proportion to how fast it is going.
---
--- `forwardAcceleration` is along the facing, studs/s^2. `yawRate` is the
--- facing's turn rate, rad/s, positive = turning left. `speedFraction` is
--- speed over the profile's run speed, 0..1+.
function AnimationCore.lean(
	forwardAcceleration: number,
	yawRate: number,
	speedFraction: number,
	sprinting: boolean,
	config: any
): (number, number)
	local tuning = config.CharacterAnimation
	local maxLean = tuning.MaxLeanDegrees
	local leanDegrees = clamp(forwardAcceleration * tuning.LeanPerAcceleration, -maxLean, maxLean)
	if sprinting then
		leanDegrees += tuning.SprintLeanDegrees
	end
	-- Leaning forward tips the front DOWN: a negative pitch.
	local pitch = -math.rad(clamp(leanDegrees, -maxLean, maxLean + tuning.SprintLeanDegrees))
	local bankDegrees = clamp(
		yawRate * tuning.BankPerTurnRate * clamp(speedFraction, 0, 1),
		-tuning.MaxBankDegrees,
		tuning.MaxBankDegrees
	)
	return pitch, math.rad(bankDegrees)
end

--- HEAD LOOK: (yaw, pitch) in radians for the neck, from a direction given
--- in the torso's own space (x right, y up, -z forward). Clamped, and zero
--- for anything behind the head, so the head never snaps round.
function AnimationCore.headLook(x: number, y: number, z: number, config: any): (number, number)
	local tuning = config.CharacterAnimation
	if -z <= 0.05 then
		return 0, 0
	end
	local yaw = math.atan2(-x, -z)
	local horizontal = math.sqrt(x * x + z * z)
	local pitch = math.atan2(y, horizontal)
	local maxYaw = math.rad(tuning.MaxHeadYawDegrees)
	local maxPitch = math.rad(tuning.MaxHeadPitchDegrees)
	return clamp(yaw, -maxYaw, maxYaw), clamp(pitch, -maxPitch, maxPitch)
end

--- LANDING: "NONE", "SOFT" or "HARD", from the downward speed at impact.
--- The hard threshold is the movement rule's (Locomotion.HardLandingSpeed),
--- so the body's reaction and the slowdown never disagree.
function AnimationCore.landing(fallSpeed: number, config: any): string
	if fallSpeed >= config.Locomotion.HardLandingSpeed then
		return "HARD"
	elseif fallSpeed >= config.CharacterAnimation.SoftLandingSpeed then
		return "SOFT"
	end
	return "NONE"
end

--- The landing dip (studs down) `elapsed` seconds after a landing of `kind`:
--- down fast, back up smoothly, zero once LandingDipSeconds has passed.
function AnimationCore.landingDip(kind: string, elapsed: number, config: any): number
	local tuning = config.CharacterAnimation
	local depth = if kind == "HARD"
		then tuning.HardLandingDipStuds
		elseif kind == "SOFT" then tuning.SoftLandingDipStuds
		else 0
	local duration = tuning.LandingDipSeconds
	if depth <= 0 or elapsed < 0 or elapsed >= duration then
		return 0
	end
	local t = elapsed / duration
	-- Peak at 20% of the way through: an impact, then a recovery.
	local shape = if t < 0.2 then t / 0.2 else 1 - (t - 0.2) / 0.8
	return depth * math.sin(shape * math.pi / 2)
end

--- ROLL DIRECTION, relative to facing: "FORWARD", "BACKWARD", "LEFT" or
--- "RIGHT", whichever the roll's direction is closest to.
function AnimationCore.rollDirection(forward: number, right: number): string
	if math.abs(forward) >= math.abs(right) then
		return if forward >= 0 then "FORWARD" else "BACKWARD"
	end
	return if right >= 0 then "RIGHT" else "LEFT"
end

--- THE PROCEDURAL ROLL, for a direction with no clip: (pitch, bank, dip)
--- for the body at `progress` 0..1 through the roll. Forward tumbles the
--- front down through a full turn, backward the other way, and the sides
--- roll over the shoulder toward the side pressed.
function AnimationCore.tumble(
	direction: string,
	progress: number,
	config: any
): (number, number, number)
	local p = clamp(progress, 0, 1)
	-- Ease in and out, so the body gathers, turns, and lands upright.
	local eased = p * p * (3 - 2 * p)
	local turn = eased * TAU
	local dip = math.sin(p * math.pi) * config.Locomotion.RollTumbleDropStuds
	if direction == "FORWARD" then
		return -turn, 0, dip
	elseif direction == "BACKWARD" then
		return turn, 0, dip
	elseif direction == "LEFT" then
		return 0, turn, dip
	end
	return 0, -turn, dip
end

--- TURN IN PLACE: how strongly to step the feet (0..1) when standing still
--- and turning at `yawRate` rad/s.
function AnimationCore.turnInPlace(speed: number, yawRate: number, config: any): number
	local tuning = config.CharacterAnimation
	if speed >= tuning.IdleSpeed or math.abs(yawRate) < tuning.TurnInPlaceRate then
		return 0
	end
	return tuning.TurnInPlaceWeight
end

--- The running sound's playback rate at this speed: normal at
--- RunningSoundSpeed, faster with speed, capped.
function AnimationCore.runningSoundRate(speed: number, config: any): number
	local tuning = config.CharacterAnimation
	if tuning.RunningSoundSpeed <= 0 then
		return 1
	end
	return clamp(speed / tuning.RunningSoundSpeed, 0, tuning.MaxRunningSoundRate)
end

--- The slot names a directional gait needs, all or nothing.
AnimationCore.DIRECTIONS = { "Forward", "Backward", "Left", "Right" }

--- Is every directional slot of `gait` ("Walk" / "Run") filled?
function AnimationCore.hasDirectionalSet(set: { [string]: string }, gait: string): boolean
	for _, direction in AnimationCore.DIRECTIONS do
		local id = set[gait .. direction]
		if type(id) ~= "string" or id == "" then
			return false
		end
	end
	return true
end

--- The clip id for a slot, or nil when it is empty (fall back).
function AnimationCore.slot(set: { [string]: string }, name: string): string?
	local id = set[name]
	if type(id) == "string" and id ~= "" then
		return id
	end
	return nil
end

--- Boot-time check of the animation set (Schema.validateAll). Every known
--- slot must be present as a string, "" or an rbxassetid, and no unknown
--- slot may appear, so a typo cannot silently leave a clip unplayed.
AnimationCore.SLOTS = {
	"Idle",
	"WalkForward",
	"WalkBackward",
	"WalkLeft",
	"WalkRight",
	"RunForward",
	"RunBackward",
	"RunLeft",
	"RunRight",
	"Sprint",
	"JumpStart",
	"Rise",
	"Fall",
	"LandSoft",
	"LandHard",
	"RollForward",
	"RollBackward",
	"RollLeft",
	"RollRight",
	"Backstep",
	"TurnLeft",
	"TurnRight",
}

function AnimationCore.validateSet(set: any): (boolean, { string })
	local errors = {}
	if type(set) ~= "table" then
		return false, { "animations: the player's animation set is not a table" }
	end
	local known = {}
	for _, name in AnimationCore.SLOTS do
		known[name] = true
		local id = set[name]
		if type(id) ~= "string" then
			table.insert(errors, `animations: slot '{name}' is missing (use "" for none)`)
		elseif id ~= "" and not string.match(id, "^rbxassetid://%d+$") then
			table.insert(errors, `animations: slot '{name}' is not an rbxassetid:// id: '{id}'`)
		end
	end
	for name in set do
		if not known[name] then
			table.insert(errors, `animations: unknown slot '{tostring(name)}'`)
		end
	end
	return #errors == 0, errors
end

return AnimationCore
