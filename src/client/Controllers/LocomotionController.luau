--!strict
-- PLAYER MOVEMENT: walk, sprint, jump, roll and backstep, on our own
-- character controller rather than Roblox's default Humanoid physics.
--
-- OWNER-DIRECTED 2026-09-28: every piece of how a player moves is ours. The
-- Humanoid's state machine is switched off (EvaluateStateMachine = false)
-- and a ControllerManager drives the character: this file tells it the
-- direction, speed and facing every frame, switches between its ground and
-- air controllers, and launches jumps itself. How the BODY reads while it
-- moves -- clips, blending, lean, head look, the roll's look, sounds -- is
-- CharacterAnimator's; this file only moves the character.
--
-- Player abilities are movement. Everything offensive -- damage, reach,
-- hit effects -- belongs to the item that grants it, and this controller
-- must never grow a branch that knows about one. Weapons talk to movement
-- through `mode`, `lock` and `unlock` (docs/PLAYER_ABILITIES.md §6).
--
-- EVERY RULE IS IN LocomotionCore. This file reads input, measures the
-- world, and applies what the core decides. A stamina bug found here is a
-- test that was missing there.
--
-- ON TRUST: Roblox movement is client-authoritative by construction. What
-- the server guards is outcomes -- roll distance, expedition entry, travel,
-- and later hits -- and those are guarded where they happen.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local LocomotionCore = require(Root.Core.LocomotionCore)
local AnimationCore = require(Root.Core.AnimationCore)
local CharacterAnimator = require(script.Parent.CharacterAnimator)

local LocomotionController = {}

local player = Players.LocalPlayer

local profileId = "HUB"
local tuning = LocomotionCore.tuning(GameConfig, profileId)
local state = LocomotionCore.newState(tuning, os.clock())
local nextProfileCheck = 0

local humanoid: Humanoid? = nil
local rootPart: BasePart? = nil
local manager: ControllerManager? = nil
local groundController: GroundController? = nil
local airController: AirController? = nil
local groundSensor: ControllerPartSensor? = nil
local groundIgnoreUntil = 0

-- Every body part but the root. Only the root collides: the body is drawn
-- over it, so a roll clip turning the torso through the floor cannot push
-- the physics about (that push was the camera shake on the owner's walk,
-- 2026-09-28). Re-applied every frame, because the Humanoid sets some of
-- them back.
local bodyParts: { BasePart } = {}

-- For landings: whether the last frame was grounded, and the downward
-- speed while airborne.
local wasGrounded = true
local airFallSpeed = 0

local wantsSprint = false
local jumpHeld = false
local vitals: any = nil

-- Where the character faces: the move direction by default, the roll
-- direction during a roll, the lock-on target while one is held.
local facing = Vector3.new(0, 0, -1)
local rollDirection = Vector3.zero
local lockTarget: Vector3? = nil
-- Our shift lock, toggled with Left Ctrl.
local shoulderCamera = false
-- Dev overrides (/moveprofile, /stamina): nil = normal behaviour.
local forcedProfile: string? = nil

-- === input ===========================================================

--- The held direction in world space, flat. Zero when nothing is held.
---
--- Read from Humanoid.MoveDirection, which the platform's own input scripts
--- (keyboard, stick, thumbstick) already fill in, camera-relative, on every
--- device. That is input only -- what the character DOES with it is ours.
--- Not the PlayerModule: a place is not guaranteed to have one, and waiting
--- for it once blocked this whole controller (2026-09-28).
local function moveDirection(): Vector3
	local hum = humanoid
	if not hum then
		return Vector3.zero
	end
	local raw = hum.MoveDirection
	local flat = Vector3.new(raw.X, 0, raw.Z)
	if flat.Magnitude < 0.1 then
		return Vector3.zero
	end
	-- Keep analogue magnitude (a half-pushed stick walks slower), capped at 1.
	return flat.Unit * math.min(flat.Magnitude, 1)
end

-- === actions =========================================================

local function launchJump(now: number)
	local root = rootPart
	if not root or not manager then
		return
	end
	groundIgnoreUntil = now + GameConfig.Locomotion.JumpGroundIgnoreSeconds
	manager.ActiveController = airController
	local velocity = root.AssemblyLinearVelocity
	root.AssemblyLinearVelocity = Vector3.new(velocity.X, tuning.JumpPower, velocity.Z)
	CharacterAnimator.onJump()
end

--- Is facing held by something other than the movement (the shoulder
--- camera or a lock-on)? Then a roll keeps facing and goes the way pressed;
--- otherwise the character turns to roll the way it is going.
local function facingHeld(): boolean
	return shoulderCamera or lockTarget ~= nil
end

local function beginRoll(kind: string)
	local now = os.clock()
	local relative = "BACKWARD"
	local yaw = 0
	local duration = tuning.BackstepDurationSeconds
	if kind == "ROLL" or kind == "AIRDASH" then
		local held = moveDirection()
		rollDirection = if held.Magnitude > 0 then held.Unit else facing
		if not facingHeld() then
			facing = rollDirection
		end
		local forward, right =
			AnimationCore.localVelocity(facing.X, facing.Z, rollDirection.X, rollDirection.Z)
		relative = AnimationCore.rollDirection(forward, right)
		yaw = AnimationCore.rollYaw(forward, right)
		duration = if kind == "AIRDASH"
			then tuning.AirDashDurationSeconds
			else tuning.RollDurationSeconds
	else
		-- A backstep keeps facing forward and hops away from it.
		rollDirection = -facing
	end
	CharacterAnimator.onRoll(kind, relative, now, duration, rollDirection, yaw)
end

local function onJumpPressed()
	local now = os.clock()
	local updated, jumped = LocomotionCore.jump(state, now, tuning)
	state = updated
	if jumped then
		launchJump(now)
	end
end

local function onRollPressed()
	local now = os.clock()
	local updated, kind = LocomotionCore.roll(state, now, moveDirection().Magnitude > 0, tuning)
	state = updated
	if kind then
		beginRoll(kind)
	end
end

-- === the profile =====================================================

--- Inside a loaded expedition stage? Its bounding box, grown by a margin,
--- measured on the flat.
local function insideStage(position: Vector3): boolean
	local stages = Workspace:FindFirstChild(Constants.NAMES.EXPEDITION_STAGE)
	if not stages then
		return false
	end
	local margin = GameConfig.Locomotion.StageMarginStuds
	for _, stage in stages:GetChildren() do
		if stage:IsA("Model") and stage:GetAttribute("Seed") ~= nil then
			local box, size = stage:GetBoundingBox()
			local offset = box:PointToObjectSpace(position)
			if
				math.abs(offset.X) <= size.X / 2 + margin
				and math.abs(offset.Z) <= size.Z / 2 + margin
			then
				return true
			end
		end
	end
	return false
end

local function refreshProfile(now: number)
	local root = rootPart
	if now < nextProfileCheck or not root then
		return
	end
	nextProfileCheck = now + GameConfig.Locomotion.ProfileCheckSeconds
	local wanted = forcedProfile or LocomotionCore.profileFor(insideStage(root.Position))
	if wanted ~= profileId then
		profileId = wanted
		tuning = LocomotionCore.tuning(GameConfig, profileId)
		state.Stamina = math.min(state.Stamina, tuning.StaminaMax)
	end
end

-- === wiring ==========================================================

local function bindCharacter(character: Model)
	manager = nil
	local found = character:WaitForChild("Humanoid", 10)
	local root = character:WaitForChild("HumanoidRootPart", 10)
	if not found or not found:IsA("Humanoid") or not root or not root:IsA("BasePart") then
		return
	end
	humanoid = found
	rootPart = root

	-- The Humanoid's own movement stops here. It still owns health, the
	-- character's name plate and seats; it no longer decides how anyone
	-- moves. WalkSpeed is kept only as an outside multiplier (see step).
	found.EvaluateStateMachine = false
	found.WalkSpeed = GameConfig.Scale.WalkSpeed

	local sensor = Instance.new("ControllerPartSensor")
	sensor.Name = "LuckboundGroundSensor"
	sensor.SensorMode = Enum.SensorMode.Floor
	sensor.SearchDistance = found.HipHeight + GameConfig.Locomotion.GroundSearchDistance
	sensor.Parent = root

	local cm = Instance.new("ControllerManager")
	cm.Name = "LuckboundController"
	cm.RootPart = root
	cm.GroundSensor = sensor
	cm.BaseMoveSpeed = 0
	cm.BaseTurnSpeed = tuning.TurnRate

	local ground = Instance.new("GroundController")
	ground.GroundOffset = found.HipHeight
	ground.Parent = cm

	local air = Instance.new("AirController")
	-- Keep the jump's own momentum; steering is added on top of it.
	air.MaintainLinearMomentum = true
	air.Parent = cm

	cm.ActiveController = ground
	cm.Parent = character

	-- Death is the Humanoid's, not ours: hand it back its state machine so
	-- the character falls and respawns the way Roblox expects.
	found.HealthChanged:Connect(function(health)
		if health <= 0 and humanoid == found then
			humanoid = nil
			CharacterAnimator.unbind()
			cm:Destroy()
			found.EvaluateStateMachine = true
			found:ChangeState(Enum.HumanoidStateType.Dead)
		end
	end)

	manager = cm
	groundController = ground
	airController = air
	groundSensor = sensor
	facing = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z)
	if facing.Magnitude < 1e-3 then
		facing = Vector3.new(0, 0, -1)
	end
	facing = facing.Unit

	state = LocomotionCore.newState(tuning, os.clock())
	nextProfileCheck = 0
	wasGrounded, airFallSpeed = true, 0
	bodyParts = {}
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") and part ~= root then
			table.insert(bodyParts, part)
		end
	end
	character.DescendantAdded:Connect(function(part)
		if part:IsA("BasePart") and part ~= root then
			table.insert(bodyParts, part)
		end
	end)
	CharacterAnimator.bind(character, found, root)
end

local function step(dt: number)
	local hum = humanoid
	local root = rootPart
	local cm = manager
	if not hum or not root or not cm or not root.Parent then
		return
	end

	local now = os.clock()
	refreshProfile(now)
	for _, part in bodyParts do
		if part.CanCollide then
			part.CanCollide = false
		end
	end

	-- The platform's jump input (Space, A, the touch button) all land on
	-- Humanoid.Jump. Read it on the press edge, then clear it.
	local jumpInput = hum.Jump
	if jumpInput and not jumpHeld then
		onJumpPressed()
	end
	jumpHeld = jumpInput

	local sensed = groundSensor and groundSensor.SensedPart ~= nil
	local grounded = (sensed == true) and now >= groundIgnoreUntil
	local held = moveDirection()
	local moving = held.Magnitude > 0

	local updated, events = LocomotionCore.step(state, dt, {
		WantsSprint = wantsSprint,
		Moving = moving,
		Grounded = grounded,
		Now = now,
	}, tuning)
	state = updated
	if events.Jumped then
		launchJump(now)
	end
	if events.Rolled then
		beginRoll(events.Rolled)
	end

	local mode = LocomotionCore.mode(state, now)

	-- Outside multiplier: the loading screen holds a character at WalkSpeed
	-- 0, and the /speed dev command scales it. Neither needs to know this
	-- controller exists.
	local outside = hum.WalkSpeed / GameConfig.Scale.WalkSpeed
	local speed = LocomotionCore.targetSpeed(state, now, tuning) * outside

	-- === direction and facing ===
	local direction: Vector3
	if LocomotionCore.rollMoving(state, now) then
		direction = rollDirection
	elseif mode == "ROLL" then
		direction = Vector3.zero
	else
		direction = held
		if moving then
			-- Locked on and not sprinting: strafe, still facing the target.
			local target = lockTarget
			if not (target and not state.Sprinting) then
				facing = held.Unit
			end
		end
	end
	-- Shoulder camera (our shift lock): face where the camera looks.
	local camera = Workspace.CurrentCamera
	if shoulderCamera and not lockTarget and mode ~= "ROLL" and camera then
		local look = camera.CFrame.LookVector
		local flat = Vector3.new(look.X, 0, look.Z)
		if flat.Magnitude > 1e-3 then
			facing = flat.Unit
		end
	end
	local target = lockTarget
	if target and mode ~= "ROLL" and not state.Sprinting then
		local toTarget = Vector3.new(target.X - root.Position.X, 0, target.Z - root.Position.Z)
		if toTarget.Magnitude > 1e-3 then
			facing = toTarget.Unit
		end
	end

	cm.MovingDirection = direction
	cm.FacingDirection = facing
	cm.BaseMoveSpeed = speed
	cm.BaseTurnSpeed = tuning.TurnRate

	local ground = groundController
	local air = airController
	if ground then
		local rolling = LocomotionCore.rollMoving(state, now)
		ground.AccelerationTime = if rolling
			then GameConfig.Locomotion.RollAccelerationSeconds
			else tuning.AccelerationSeconds
		ground.DecelerationTime = tuning.DecelerationSeconds
	end
	if air then
		air.MoveSpeedFactor = tuning.AirControl
	end
	if now >= groundIgnoreUntil then
		cm.ActiveController = if sensed then ground else air
	end

	-- The air dash drives the body directly: straight along its direction at
	-- full speed, holding height. The air controller's steering is too soft
	-- for a burst, and gravity would bend it into an arc.
	if state.RollKind == "AIRDASH" and LocomotionCore.rollMoving(state, now) then
		root.AssemblyLinearVelocity = rollDirection * speed
	end

	-- === landings ===
	-- The downward speed is sampled every airborne frame, because on the
	-- landing frame itself the floor has already stopped the fall.
	local velocity = root.AssemblyLinearVelocity
	if not grounded then
		airFallSpeed = math.max(0, -velocity.Y)
	elseif not wasGrounded then
		state = LocomotionCore.land(state, now, airFallSpeed, tuning)
		CharacterAnimator.onLand(airFallSpeed, now)
		airFallSpeed = 0
	end
	wasGrounded = grounded

	CharacterAnimator.update({
		Now = now,
		Mode = mode,
		Sprinting = state.Sprinting,
		Grounded = grounded,
		RollMoving = LocomotionCore.rollMoving(state, now),
		LookAt = lockTarget,
	}, dt)

	-- The shoulder camera's half: re-applied every frame, because the default
	-- camera resets the mouse behaviour whenever it likes. The lock-on camera
	-- owns the view while a lock is held.
	if shoulderCamera and not lockTarget then
		UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
		hum.CameraOffset = Vector3.new(GameConfig.Locomotion.ShoulderCameraOffset, 0, 0)
	elseif hum.CameraOffset ~= Vector3.zero then
		hum.CameraOffset = Vector3.zero
		UserInputService.MouseBehavior = Enum.MouseBehavior.Default
	end

	if vitals then
		vitals.setStamina(LocomotionCore.staminaFraction(state, tuning), now, dt)
		vitals.setHealth(if hum.MaxHealth > 0 then hum.Health / hum.MaxHealth else 1, now, dt)
	end
end

--- `deps` = { Vitals }. Called once PLAY is pressed.
function LocomotionController.init(deps: any): ()
	print("[Locomotion] init")
	vitals = deps and deps.Vitals

	-- A failure here would otherwise leave the character on Roblox's default
	-- movement with no sign anything went wrong: say so, loudly, either way.
	local function bindLoud(character: Model)
		local bound, err = pcall(bindCharacter, character)
		if not bound then
			warn(`[Locomotion] controller FAILED to bind; default movement is running: {err}`)
		elseif manager then
			print(`[Locomotion] controller bound (profile {profileId})`)
		else
			warn("[Locomotion] controller did not bind: no Humanoid or HumanoidRootPart")
		end
	end
	if player.Character then
		task.spawn(bindLoud, player.Character)
	end
	player.CharacterAdded:Connect(bindLoud)

	UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		if input.KeyCode == Enum.KeyCode.LeftShift or input.KeyCode == Enum.KeyCode.ButtonL3 then
			wantsSprint = true
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if input.KeyCode == Enum.KeyCode.LeftShift or input.KeyCode == Enum.KeyCode.ButtonL3 then
			wantsSprint = false
		end
	end)

	-- Bound through ContextActionService so a phone gets an on-screen button.
	ContextActionService:BindAction("LuckboundRoll", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			onRollPressed()
		end
		return Enum.ContextActionResult.Pass
	end, true, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)
	ContextActionService:SetTitle("LuckboundRoll", "Roll")

	-- Our shift lock. Left Ctrl, because Shift is sprint.
	ContextActionService:BindAction("LuckboundShoulderCamera", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			shoulderCamera = not shoulderCamera
		end
		return Enum.ContextActionResult.Pass
	end, false, Enum.KeyCode.LeftControl)

	RunService.Heartbeat:Connect(step)
end

--- The current movement state, for anything that needs to draw it. Read-only
--- by convention: mutate it and the next frame overwrites you.
function LocomotionController.get(): any
	return state
end

--- The current movement mode: "GROUND", "AIR", "ROLL" or "LOCKED".
--- RESERVED (docs/RESERVED.md): read by the weapon layer once it exists.
function LocomotionController.mode(): string
	return LocomotionCore.mode(state, os.clock())
end

--- THE WEAPON HOOK. A weapon move holds movement for its own length; see
--- LocomotionCore.lock for the spec. RESERVED (docs/RESERVED.md): no weapon
--- calls it yet.
function LocomotionController.lock(spec: any): ()
	state = LocomotionCore.lock(state, os.clock(), spec, tuning)
end

--- Releases a weapon lock early. RESERVED alongside `lock`.
function LocomotionController.unlock(): ()
	state = LocomotionCore.unlock(state)
end

--- DEV: force a movement profile ("HUB" / "EXPEDITION"), or nil for the
--- normal inside-a-stage rule. For /moveprofile.
function LocomotionController.forceProfile(id: string?): ()
	forcedProfile = id
	nextProfileCheck = 0
end

--- DEV: set stamina to a fraction of the bar. For /stamina.
function LocomotionController.setStamina(fraction: number): ()
	state.Stamina = math.clamp(fraction, 0, 1) * tuning.StaminaMax
end

--- The active profile id, for the dev panel.
function LocomotionController.profile(): string
	return profileId
end

--- Where the lock-on target is, or nil. Set every frame by LockOnController;
--- while set, the character strafes facing it.
function LocomotionController.setLockTarget(position: Vector3?): ()
	lockTarget = position
end

return LocomotionController
