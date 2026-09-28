--!strict
-- PLAYER MOVEMENT: walk, sprint, jump, roll and backstep, on our own
-- character controller rather than Roblox's default Humanoid physics.
--
-- OWNER-DIRECTED 2026-09-28: every piece of how a player moves is ours. The
-- Humanoid's state machine is switched off (EvaluateStateMachine = false)
-- and a ControllerManager drives the character: this file tells it the
-- direction, speed and facing every frame, switches between its ground and
-- air controllers, and launches jumps itself. The stock Animate script is
-- switched off too; the same stock animation assets are played from here,
-- driven by our speed and mode, until LUCKBOUND has its own.
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
local UITheme = require(Root.Core.UITheme)

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

local wantsSprint = false
local jumpHeld = false
local controls: any = nil
local vitals: any = nil

-- Where the character faces: the move direction by default, the roll
-- direction during a roll, the lock-on target while one is held.
local facing = Vector3.new(0, 0, -1)
local rollDirection = Vector3.zero
local lockTarget: Vector3? = nil

-- === animation =======================================================
-- The stock assets, played by us. `tracks` is keyed walk/run/idle/jump/fall.

local tracks: { [string]: AnimationTrack } = {}
local playing: string? = nil

local function loadAnimations(character: Model, hum: Humanoid)
	tracks = {}
	playing = nil
	local animate = character:FindFirstChild("Animate")
	local animator = hum:FindFirstChildOfClass("Animator")
	if not animate or not animator then
		return
	end
	if animate:IsA("LocalScript") then
		animate.Enabled = false
	end
	for _, track in animator:GetPlayingAnimationTracks() do
		track:Stop(0)
	end

	local function load(key: string, folder: string)
		local holder = animate:FindFirstChild(folder)
		local asset = holder and holder:FindFirstChildOfClass("Animation")
		if asset then
			local track = animator:LoadAnimation(asset)
			track.Looped = key ~= "jump"
			tracks[key] = track
		end
	end
	load("idle", "idle")
	load("walk", "walk")
	load("run", "run")
	load("jump", "jump")
	load("fall", "fall")
end

local function playTrack(key: string, speed: number)
	local track = tracks[key]
	if not track then
		return
	end
	if playing ~= key then
		local fade = GameConfig.Locomotion.AnimFadeSeconds
		local current = playing and tracks[playing]
		if current then
			current:Stop(fade)
		end
		track:Play(fade)
		playing = key
	end
	track:AdjustSpeed(speed)
end

local function animate(mode: string, horizontalSpeed: number, now: number)
	local tune = GameConfig.Locomotion
	if mode == "AIR" then
		-- The jump pose for the rise, the fall loop after.
		if now - state.LastGroundedAt < tune.CoyoteTimeSeconds * 3 and state.JumpSpent then
			playTrack("jump", 1)
		else
			playTrack("fall", 1)
		end
	elseif horizontalSpeed < tune.AnimIdleSpeed then
		playTrack("idle", 1)
	elseif state.Sprinting or mode == "ROLL" then
		playTrack("run", horizontalSpeed / tune.AnimRunNominalSpeed)
	else
		playTrack("walk", horizontalSpeed / tune.AnimWalkNominalSpeed)
	end
end

-- === effects =========================================================

--- A burst of light at the feet on a roll. An ability nobody can see reads
--- as a physics glitch.
local function playBurstEffect(character: Model)
	if not GameConfig.Locomotion.RollEffect then
		return
	end
	local root = character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return
	end

	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(0, -2.6, 0)
	attachment.Parent = root

	local ring = Instance.new("ParticleEmitter")
	ring.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	ring.Color = ColorSequence.new(UITheme.AccentGold)
	ring.Lifetime = NumberRange.new(0.3, 0.5)
	ring.Rate = 0
	ring.Speed = NumberRange.new(8, 12)
	ring.SpreadAngle = Vector2.new(180, 180)
	ring.Size = NumberSequence.new(0.5)
	ring.Parent = attachment
	ring:Emit(14)

	-- Clean up after the longest particle can possibly live, never sooner.
	task.delay(1, function()
		attachment:Destroy()
	end)
end

-- === input ===========================================================

--- The held direction in world space, flat, from the platform's own input
--- (keyboard, stick or thumbstick) turned relative to the camera. Zero when
--- nothing is held.
local function moveDirection(): Vector3
	if not controls then
		return Vector3.zero
	end
	local raw: Vector3 = controls:GetMoveVector()
	if raw.Magnitude < 0.1 then
		return Vector3.zero
	end
	local camera = Workspace.CurrentCamera
	if not camera then
		return Vector3.zero
	end
	local look = camera.CFrame.LookVector
	local right = camera.CFrame.RightVector
	local forward = Vector3.new(look.X, 0, look.Z)
	local side = Vector3.new(right.X, 0, right.Z)
	if forward.Magnitude < 1e-3 or side.Magnitude < 1e-3 then
		return Vector3.zero
	end
	local world = forward.Unit * -raw.Z + side.Unit * raw.X
	if world.Magnitude < 1e-3 then
		return Vector3.zero
	end
	-- Keep analogue magnitude (a half-pushed stick walks slower), capped at 1.
	return world.Unit * math.min(raw.Magnitude, 1)
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
end

local function beginRoll(kind: string)
	local character = player.Character
	if not character then
		return
	end
	if kind == "ROLL" then
		local held = moveDirection()
		rollDirection = if held.Magnitude > 0 then held.Unit else facing
		facing = rollDirection
	else
		-- A backstep keeps facing forward and hops away from it.
		rollDirection = -facing
	end
	playBurstEffect(character)
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
	local wanted = LocomotionCore.profileFor(insideStage(root.Position))
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
	loadAnimations(character, found)
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

	local velocity = root.AssemblyLinearVelocity
	animate(mode, Vector3.new(velocity.X, 0, velocity.Z).Magnitude, now)

	if vitals then
		vitals.setStamina(
			LocomotionCore.staminaFraction(state, tuning),
			profileId == "EXPEDITION",
			now,
			dt
		)
	end
end

--- `deps` = { Vitals }. Called once PLAY is pressed.
function LocomotionController.init(deps: any): ()
	print("[Locomotion] init")
	vitals = deps and deps.Vitals

	local playerScripts = player:WaitForChild("PlayerScripts")
	local ok, module = pcall(function()
		return require(playerScripts:WaitForChild("PlayerModule") :: any)
	end)
	if ok and module then
		controls = module:GetControls()
	end

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

--- Where the lock-on target is, or nil. Set every frame by LockOnController;
--- while set, the character strafes facing it.
function LocomotionController.setLockTarget(position: Vector3?): ()
	lockTarget = position
end

return LocomotionController
