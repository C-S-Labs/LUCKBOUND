--!strict
-- HOW THE PLAYER'S BODY MOVES: clips, blending and the procedural layer.
--
-- LocomotionController decides where the character goes; this file makes
-- the body read naturally while it does. It is presentation only and never
-- changes a speed or a position. Every rule is in AnimationCore; the clips
-- are Content/Animations/Player.luau.
--
-- WHAT PLAYS. Ground movement is a blend, not a switch: idle, walk and run
-- tracks all play and are weighted by speed (and, once all four directional
-- clips of a gait exist, by direction). Air, landings, rolls and the jump's
-- take-off sit on top. Each slot with no clip falls back to the stock Roblox
-- asset from the character's Animate script, bent by the procedural layer:
--   * STRAFE: legs turn toward the movement, the upper body counter-turns,
--     and moving backward runs the forward clip in reverse;
--   * LEAN into acceleration and turns; BANK into curves;
--   * HEAD turns toward the lock-on target or where the camera looks;
--   * LANDING dip, soft or hard;
--   * ROLL tumble, forward / backward / left / right RELATIVE TO FACING.
-- The procedural layer bends Motor6D.C0, which is drawn on this client
-- only; clips replicate to every player. Filling the slots is what makes
-- the polish visible to everyone.
--
-- The roll's look -- faint afterimages and a small camera widen -- lives
-- here too, toned down on the owner's first walk (2026-09-28).

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local AnimationCore = require(Root.Core.AnimationCore)
local GameConfig = require(Root.Core.GameConfig)
local PlayerAnimations = require(Root.Content.Animations.Player)

local CharacterAnimator = {}

-- Built-in client sounds: the same files Roblox's default character sounds
-- use, so they exist in every place with no upload.
local SOUND_RUNNING = "rbxasset://sounds/action_footsteps_plastic.mp3"
local SOUND_JUMP = "rbxasset://sounds/action_jump.mp3"
local SOUND_LAND = "rbxasset://sounds/action_jump_land.mp3"

-- Weights below this count as off (a track at exactly 0 can misreport).
local MIN_WEIGHT = 1e-3

type Layer = { Track: AnimationTrack, Weight: number }

type Rig = {
	Character: Model,
	Humanoid: Humanoid,
	Root: BasePart,
	Animator: Animator,
	-- Looping ground/air layers, by key; missing keys have no asset.
	Layers: { [string]: Layer },
	-- One-shot clips, by slot name.
	OneShots: { [string]: AnimationTrack },
	-- Whether each gait has all four directional clips.
	DirectionalWalk: boolean,
	DirectionalRun: boolean,
	RootJoint: Motor6D?,
	RootC0: CFrame,
	Waist: Motor6D?,
	WaistC0: CFrame,
	Neck: Motor6D?,
	NeckC0: CFrame,
	Running: Sound?,
	Jump: Sound?,
	Land: Sound?,
}

local rig: Rig? = nil
local generatedIds: () -> { [string]: string }

-- DEV: slot overrides set live with /animslot, so a freshly uploaded clip
-- can be tried in Play without editing Content/Animations/Player.luau.
-- Cleared on rejoin; the content file is what ships.
local overrides: { [string]: string } = {}

-- Smoothed procedural state.
local legYaw = 0
local leanPitch = 0
local leanBank = 0
local headYaw = 0
local headPitch = 0
local direction = { Forward = 1, Backward = 0, Left = 0, Right = 0 }
local lastForwardSpeed = 0
local lastFacingYaw: number? = nil
local landKind = "NONE"
local landedAt = -math.huge

-- The current roll: "ROLL" / "BACKSTEP" / "AIRDASH", its direction relative
-- to facing ("FORWARD" / "BACKWARD" / "LEFT" / "RIGHT"), and whether a clip
-- is playing it (then the procedural layer stays out of the way).
local rollKind: string? = nil
local rollRelative = "FORWARD"
local rollHasClip = false
-- Turns the body from the clip's direction onto the true one (diagonals).
local rollYaw = 0
local rollStartedAt = 0
local rollDuration = 1
local fovBase: number? = nil

-- === setup ===========================================================

--- Rotates a joint's C0 by `rotation` in its PARENT part's space, with an
--- optional offset, so R15 and R6 (whose C0s carry different built-in
--- rotations) bend the same way.
local function bend(base: CFrame, rotation: CFrame, offset: Vector3?): CFrame
	return CFrame.new(base.Position + (offset or Vector3.zero)) * rotation * base.Rotation
end

local function findJoint(character: Model, predicate: (Motor6D) -> boolean): Motor6D?
	for _, d in character:GetDescendants() do
		if d:IsA("Motor6D") and predicate(d) then
			return d
		end
	end
	return nil
end

local function makeSound(parent: Instance, id: string, volume: number, looped: boolean): Sound
	local sound = Instance.new("Sound")
	sound.SoundId = id
	sound.Volume = volume
	sound.Looped = looped
	sound.RollOffMaxDistance = 80
	sound.Parent = parent
	return sound
end

local function loadTrack(
	animator: Animator,
	id: string,
	priority: Enum.AnimationPriority,
	looped: boolean
): AnimationTrack?
	local asset = Instance.new("Animation")
	asset.AnimationId = id
	local ok, track = pcall(function()
		return animator:LoadAnimation(asset)
	end)
	if not ok or not track then
		warn(`[CharacterAnimator] could not load {id}: {track}`)
		return nil
	end
	track.Priority = priority
	track.Looped = looped
	return track
end

--- The stock asset id in the character's Animate script for a folder
--- (idle, walk, run, jump, fall), or nil.
local function stockId(animate: Instance?, folder: string): string?
	local holder = animate and animate:FindFirstChild(folder)
	local asset = holder and holder:FindFirstChildOfClass("Animation")
	if asset and asset.AnimationId ~= "" then
		return asset.AnimationId
	end
	return nil
end

-- GENERATED CLIPS (tools/gen_player_anims.py), synced by Rojo into
-- ReplicatedStorage.LuckboundAnimations as KeyframeSequences. In Studio each
-- is registered for a temporary id so it plays with no upload, in any slot
-- the content file leaves "". Outside Studio registration is refused and
-- the slot falls back as before -- a clip ships by being saved to Roblox
-- and pasted into Content/Animations/Player.luau.
local generated: { [string]: string }? = nil

generatedIds = function(): { [string]: string }
	if generated then
		return generated
	end
	local found: { [string]: string } = {}
	generated = found
	local folder = ReplicatedStorage:FindFirstChild("LuckboundAnimations")
	if not folder or not RunService:IsStudio() then
		return found
	end
	for _, sequence in folder:GetChildren() do
		if sequence:IsA("KeyframeSequence") and table.find(AnimationCore.SLOTS, sequence.Name) then
			local ok, id = pcall(function()
				return KeyframeSequenceProvider:RegisterKeyframeSequence(sequence)
			end)
			if ok and type(id) == "string" then
				found[sequence.Name] = id
			else
				warn(`[CharacterAnimator] could not register generated clip {sequence.Name}: {id}`)
			end
		end
	end
	return found
end

--- Called by LocomotionController once it has taken the character over.
function CharacterAnimator.bind(character: Model, hum: Humanoid, root: BasePart): ()
	CharacterAnimator.unbind()

	local animator = hum:FindFirstChildOfClass("Animator")
	if not animator then
		animator = Instance.new("Animator")
		animator.Parent = hum
	end
	assert(animator)

	-- The stock Animate script keys off the Humanoid state machine, which
	-- is off; its assets are still the fallback for every empty slot.
	local animate = character:FindFirstChild("Animate")
	if animate and animate:IsA("LocalScript") then
		animate.Enabled = false
	end
	for _, track in animator:GetPlayingAnimationTracks() do
		track:Stop(0)
	end

	local layers: { [string]: Layer } = {}
	local function layer(key: string, id: string?, priority: Enum.AnimationPriority)
		if not id then
			return
		end
		local track = loadTrack(animator, id, priority, true)
		if track then
			track:Play(0, MIN_WEIGHT, 1)
			layers[key] = { Track = track, Weight = MIN_WEIGHT }
		end
	end

	-- The shipped set; generated clips fill its empty slots (Studio only);
	-- live /animslot overrides go on top.
	local set = table.clone(PlayerAnimations)
	for name, id in generatedIds() do
		if not AnimationCore.slot(set, name) then
			set[name] = id
		end
	end
	for name, id in overrides do
		set[name] = id
	end
	local directionalWalk = AnimationCore.hasDirectionalSet(set, "Walk")
	local directionalRun = AnimationCore.hasDirectionalSet(set, "Run")

	layer(
		"Idle",
		AnimationCore.slot(set, "Idle") or stockId(animate, "idle"),
		Enum.AnimationPriority.Idle
	)
	if directionalWalk then
		for _, d in AnimationCore.DIRECTIONS do
			layer(
				"Walk" .. d,
				AnimationCore.slot(set, "Walk" .. d),
				Enum.AnimationPriority.Movement
			)
		end
	else
		layer(
			"Walk",
			AnimationCore.slot(set, "WalkForward") or stockId(animate, "walk"),
			Enum.AnimationPriority.Movement
		)
	end
	if directionalRun then
		for _, d in AnimationCore.DIRECTIONS do
			layer("Run" .. d, AnimationCore.slot(set, "Run" .. d), Enum.AnimationPriority.Movement)
		end
	else
		layer(
			"Run",
			AnimationCore.slot(set, "RunForward") or stockId(animate, "run"),
			Enum.AnimationPriority.Movement
		)
	end
	layer("Sprint", AnimationCore.slot(set, "Sprint"), Enum.AnimationPriority.Movement)
	layer(
		"Rise",
		AnimationCore.slot(set, "Rise") or stockId(animate, "jump"),
		Enum.AnimationPriority.Movement
	)
	layer(
		"Fall",
		AnimationCore.slot(set, "Fall") or stockId(animate, "fall"),
		Enum.AnimationPriority.Movement
	)

	local oneShots: { [string]: AnimationTrack } = {}
	for _, name in
		{
			"JumpStart",
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
	do
		local id = AnimationCore.slot(set, name)
		if id then
			local track = loadTrack(animator, id, Enum.AnimationPriority.Action, false)
			if track then
				oneShots[name] = track
			end
		end
	end

	-- The joints the procedural layer bends. R15: LowerTorso.Root, Waist,
	-- Neck. R6: RootJoint and Neck (no waist, so no counter-turn).
	local rootJoint = findJoint(character, function(m)
		return m.Part0 == root
	end)
	local waist = findJoint(character, function(m)
		return m.Name == "Waist"
	end)
	local neck = findJoint(character, function(m)
		return m.Name == "Neck"
	end)

	local tune = GameConfig.CharacterAnimation
	rig = {
		Character = character,
		Humanoid = hum,
		Root = root,
		Animator = animator,
		Layers = layers,
		OneShots = oneShots,
		DirectionalWalk = directionalWalk,
		DirectionalRun = directionalRun,
		RootJoint = rootJoint,
		RootC0 = if rootJoint then rootJoint.C0 else CFrame.identity,
		Waist = waist,
		WaistC0 = if waist then waist.C0 else CFrame.identity,
		Neck = neck,
		NeckC0 = if neck then neck.C0 else CFrame.identity,
		Running = if tune.Sounds
			then makeSound(root, SOUND_RUNNING, tune.RunningVolume, true)
			else nil,
		Jump = if tune.Sounds then makeSound(root, SOUND_JUMP, tune.JumpVolume, false) else nil,
		Land = if tune.Sounds then makeSound(root, SOUND_LAND, tune.LandVolume, false) else nil,
	}

	legYaw, leanPitch, leanBank, headYaw, headPitch = 0, 0, 0, 0, 0
	direction = { Forward = 1, Backward = 0, Left = 0, Right = 0 }
	lastForwardSpeed = 0
	lastFacingYaw = nil
	landKind, landedAt = "NONE", -math.huge
	rollKind = nil
end

--- Puts every joint back and stops everything (death, respawn).
function CharacterAnimator.unbind(): ()
	local r = rig
	if not r then
		return
	end
	if r.RootJoint then
		r.RootJoint.C0 = r.RootC0
	end
	if r.Waist then
		r.Waist.C0 = r.WaistC0
	end
	if r.Neck then
		r.Neck.C0 = r.NeckC0
	end
	for _, l in r.Layers do
		l.Track:Stop(0)
	end
	if r.Running then
		r.Running:Stop()
	end
	local camera = Workspace.CurrentCamera
	if camera and fovBase then
		camera.FieldOfView = fovBase
	end
	fovBase = nil
	rig = nil
end

-- === events ==========================================================

local function playOneShot(name: string, duration: number?): boolean
	local r = rig
	local track = r and r.OneShots[name]
	if not track then
		return false
	end
	local fade = GameConfig.CharacterAnimation.AirFadeSeconds
	track:Play(fade, 1, 1)
	-- Fit the clip to the move's own length, whatever it was authored at.
	if duration and duration > 0 and track.Length > 0 then
		track:AdjustSpeed(track.Length / duration)
	end
	return true
end

function CharacterAnimator.onJump(): ()
	playOneShot("JumpStart")
	local r = rig
	if r and r.Jump then
		r.Jump:Play()
	end
end

--- A landing at `fallSpeed` studs/s downward.
function CharacterAnimator.onLand(fallSpeed: number, now: number): ()
	local kind = AnimationCore.landing(fallSpeed, GameConfig)
	if kind == "NONE" then
		return
	end
	-- A landing clip carries its own absorb; the procedural dip stands down
	-- so the body does not drop twice.
	local clip = playOneShot(if kind == "HARD" then "LandHard" else "LandSoft")
	landKind, landedAt = if clip then "NONE" else kind, now
	local r = rig
	if r and r.Land then
		r.Land.Volume = GameConfig.CharacterAnimation.LandVolume
			* (if kind == "HARD" then 1 else 0.6)
		r.Land:Play()
	end
end

--- Title-cases a direction for a slot name: "FORWARD" -> "Forward".
local function slotDirection(relative: string): string
	return string.sub(relative, 1, 1) .. string.lower(string.sub(relative, 2))
end

local burstWind: (BasePart, Vector3) -> ()

--- A roll, backstep or air dash starting. `kind` is "ROLL" / "BACKSTEP" /
--- "AIRDASH"; `relative` its direction against facing; `worldDirection`
--- the way it actually goes, for the wind.
function CharacterAnimator.onRoll(
	kind: string,
	relative: string,
	now: number,
	duration: number,
	worldDirection: Vector3
): ()
	rollKind, rollRelative = kind, relative
	rollStartedAt, rollDuration = now, math.max(duration, 1e-3)
	local slot = if kind == "BACKSTEP"
		then "Backstep"
		elseif kind == "AIRDASH" then "AirDash" .. slotDirection(relative)
		else "Roll" .. slotDirection(relative)
	-- A clip for this move replaces the procedural layer.
	rollHasClip = playOneShot(slot, duration)

	local r = rig
	if r and GameConfig.Locomotion.RollWind then
		burstWind(r.Root, worldDirection)
	end

	local camera = Workspace.CurrentCamera
	local kick = GameConfig.Locomotion.RollFovKickDegrees
	if camera and kick > 0 then
		fovBase = fovBase or camera.FieldOfView
		camera.FieldOfView = (fovBase :: number) + kick
	end
end

-- === the roll's look =================================================

-- A pale, faintly blue white: air, not light. Kept apart from gold, which
-- the game uses for things to press.
local WIND_COLOR = Color3.fromRGB(226, 238, 255)

local function windPart(size: Vector3, cf: CFrame, transparency: number): Part
	local part = Instance.new("Part")
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.ForceField
	part.Color = WIND_COLOR
	part.Transparency = transparency
	part.Size = size
	part.CFrame = cf
	return part
end

--- A DISCRETE BURST OF WIND where the move starts: short streaks of air
--- left behind along the way it goes, stretching out and fading within
--- RollWindSeconds. Owner, 2026-09-28: instead of afterimages; no ground ring.
burstWind = function(root: BasePart, worldDirection: Vector3)
	local tune = GameConfig.Locomotion
	local seconds = tune.RollWindSeconds
	local flat = Vector3.new(worldDirection.X, 0, worldDirection.Z)
	local dir = if flat.Magnitude > 1e-3
		then flat.Unit
		else Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z).Unit
	local right = dir:Cross(Vector3.yAxis)
	local centre = root.Position

	local folder = Instance.new("Folder")
	folder.Name = "LuckboundRollWind"
	local fade = TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

	-- Streaks spread across the body's width and height, staggered front to
	-- back so they read as a gust rather than a row of sticks.
	local count = tune.RollWindStreaks
	local length = tune.RollWindStreakLengthStuds
	local thick = tune.RollWindStreakThickness
	for i = 1, count do
		local f = (i - 1) / math.max(count - 1, 1) -- 0..1 across
		local across = (f - 0.5) * 2.4
		local height = -1.6 + ((i * 0.618) % 1) * 3.0
		local back = 0.8 + ((i * 0.382) % 1) * 1.6
		local at = centre + Vector3.new(0, height, 0) + right * across - dir * back
		local streak = windPart(
			Vector3.new(thick, thick, length * 0.35),
			CFrame.lookAt(at, at + dir),
			tune.RollWindTransparency
		)
		streak.Parent = folder
		local tail = at - dir * length * 0.6
		TweenService:Create(streak, fade, {
			Size = Vector3.new(thick * 0.3, thick * 0.3, length),
			CFrame = CFrame.lookAt(tail, tail + dir),
			Transparency = 1,
		}):Play()
	end

	folder.Parent = Workspace
	task.delay(seconds + 0.1, function()
		folder:Destroy()
	end)
end

-- === the frame =======================================================

local function setWeight(key: string, target: number, alpha: number, rate: number?)
	local r = rig
	local l = r and r.Layers[key]
	if not l then
		return
	end
	l.Weight += (target - l.Weight) * alpha
	l.Track:AdjustWeight(math.max(l.Weight, MIN_WEIGHT), 0)
	if rate then
		l.Track:AdjustSpeed(rate)
	end
end

--- Every frame, from LocomotionController.
---
---   ctx = {
---     Now, Mode ("GROUND"/"AIR"/"ROLL"/"LOCKED"), Sprinting, Grounded,
---     RollMoving, LookAt: Vector3? (lock-on target; nil = camera),
---   }
function CharacterAnimator.update(ctx: any, dt: number): ()
	local r = rig
	if not r or not r.Root.Parent then
		return
	end
	local tune = GameConfig.CharacterAnimation
	local now = ctx.Now
	local root = r.Root

	-- === measure ===
	local velocity = root.AssemblyLinearVelocity
	local look = root.CFrame.LookVector
	local forwardSpeed, rightSpeed =
		AnimationCore.localVelocity(look.X, look.Z, velocity.X, velocity.Z)
	local speed = math.sqrt(forwardSpeed * forwardSpeed + rightSpeed * rightSpeed)
	local angle = AnimationCore.moveAngle(forwardSpeed, rightSpeed)

	local facingYaw = math.atan2(-look.X, -look.Z)
	local yawRate = if lastFacingYaw and dt > 0
		then AnimationCore.wrap(facingYaw - lastFacingYaw) / dt
		else 0
	lastFacingYaw = facingYaw
	local acceleration = if dt > 0 then (forwardSpeed - lastForwardSpeed) / dt else 0
	lastForwardSpeed = forwardSpeed

	-- An air dash is a roll in the rules but reads as airborne to the body.
	local airDash = rollKind == "AIRDASH" and ctx.RollMoving
	local rolling = ctx.Mode == "ROLL" and not airDash
	local airborne = ctx.Mode == "AIR" or airDash
	local blend = AnimationCore.smoothAlpha(dt, tune.FadeSeconds)
	local airBlend = AnimationCore.smoothAlpha(dt, tune.AirFadeSeconds)

	-- === ground blend ===
	local moving = math.clamp(speed / tune.IdleSpeed, 0, 1)
	local run = AnimationCore.runBlend(speed, GameConfig)
	local ground = if airborne or rolling then 0 else 1
	local sprinting = ctx.Sprinting and r.Layers.Sprint ~= nil

	-- Direction weights settle rather than snap.
	local targetDir = AnimationCore.directionalWeights(angle)
	local dirAlpha = AnimationCore.smoothAlpha(dt, tune.DirectionSmoothSeconds)
	for k, v in targetDir do
		direction[k] += (v - direction[k]) * dirAlpha
	end

	local reverse, targetLegYaw = AnimationCore.procedural(angle, GameConfig)
	local walkRate = AnimationCore.playbackRate(speed, tune.WalkClipSpeed, GameConfig)
	local runRate = AnimationCore.playbackRate(speed, tune.RunClipSpeed, GameConfig)
	local sign = if reverse then -1 else 1

	-- Turning on the spot steps the feet with a little walk.
	local turning = if ground > 0 then AnimationCore.turnInPlace(speed, yawRate, GameConfig) else 0
	local walkWeight = ground * moving * (1 - run)
	local runWeight = ground * moving * run * (if sprinting then 0 else 1)

	setWeight("Idle", ground * (1 - moving) * (1 - turning), blend)
	if r.DirectionalWalk then
		for _, d in AnimationCore.DIRECTIONS do
			setWeight("Walk" .. d, walkWeight * direction[d], blend, walkRate)
		end
	else
		setWeight(
			"Walk",
			walkWeight + ground * turning,
			blend,
			if turning > 0 and moving < 1 then 0.8 else walkRate * sign
		)
	end
	if r.DirectionalRun then
		for _, d in AnimationCore.DIRECTIONS do
			setWeight("Run" .. d, runWeight * direction[d], blend, runRate)
		end
	else
		setWeight("Run", runWeight, blend, runRate * sign)
	end
	setWeight(
		"Sprint",
		if sprinting then ground * moving else 0,
		blend,
		AnimationCore.playbackRate(speed, tune.SprintClipSpeed, GameConfig)
	)

	-- === air ===
	local rising = airborne and velocity.Y > 0
	setWeight("Rise", if rising then 1 else 0, airBlend)
	setWeight("Fall", if airborne and not rising then 1 else 0, airBlend)

	-- === procedural: legs ===
	-- Only while the fallback strafe is in use and the feet are on the floor.
	local strafeLegs = not (if run > 0.5 then r.DirectionalRun else r.DirectionalWalk)
	local wantLegYaw = if strafeLegs and ground > 0 and moving > 0.5 then targetLegYaw else 0
	legYaw += (wantLegYaw - legYaw) * AnimationCore.smoothAlpha(dt, tune.LegYawSmoothSeconds)

	-- === procedural: lean ===
	local runSpeed = math.max(tune.RunClipSpeed, 1e-3)
	local wantPitch, wantBank = 0, 0
	if ground > 0 then
		wantPitch, wantBank =
			AnimationCore.lean(acceleration, yawRate, speed / runSpeed, ctx.Sprinting, GameConfig)
	end
	local leanAlpha = AnimationCore.smoothAlpha(dt, tune.LeanSmoothSeconds)
	leanPitch += (wantPitch - leanPitch) * leanAlpha
	leanBank += (wantBank - leanBank) * leanAlpha

	-- === procedural: landing dip ===
	local dip = AnimationCore.landingDip(landKind, now - landedAt, GameConfig)

	-- === procedural: roll ===
	local tumblePitch, tumbleBank, tumbleDip = 0, 0, 0
	local kind = rollKind
	if kind and ctx.RollMoving then
		local progress = math.clamp((now - rollStartedAt) / rollDuration, 0, 1)
		local arc = math.sin(progress * math.pi)
		if rollHasClip then
			-- The clip is the whole move.
		elseif kind == "BACKSTEP" then
			-- A short hop back: the body leans away and dips.
			tumblePitch = 0.3 * arc
			tumbleDip = 0.4 * arc
		elseif kind == "AIRDASH" then
			-- A lean into the dash's direction, relative to facing.
			local lean = math.rad(GameConfig.Locomotion.AirDashLeanDegrees) * arc
			if rollRelative == "FORWARD" then
				tumblePitch = -lean
			elseif rollRelative == "BACKWARD" then
				tumblePitch = lean
			elseif rollRelative == "LEFT" then
				tumbleBank = lean
			else
				tumbleBank = -lean
			end
		elseif GameConfig.Locomotion.RollTumble then
			tumblePitch, tumbleBank, tumbleDip =
				AnimationCore.tumble(rollRelative, progress, GameConfig)
		end
	elseif kind and not rolling then
		rollKind = nil
	end

	-- The camera eases back from its kick over the roll.
	local camera = Workspace.CurrentCamera
	if camera and fovBase then
		local base = fovBase :: number
		if kind and ctx.RollMoving then
			local progress = math.clamp((now - rollStartedAt) / rollDuration, 0, 1)
			camera.FieldOfView = base + GameConfig.Locomotion.RollFovKickDegrees * (1 - progress)
		else
			camera.FieldOfView = base
			fovBase = nil
		end
	end

	-- === apply to the joints ===
	if r.RootJoint then
		r.RootJoint.C0 = bend(
			r.RootC0,
			CFrame.Angles(0, legYaw + (if kind and ctx.RollMoving then rollYaw else 0), 0)
				* CFrame.Angles(leanPitch + tumblePitch, 0, leanBank + tumbleBank),
			Vector3.new(0, -(dip + tumbleDip), 0)
		)
	end
	if r.Waist then
		r.Waist.C0 = bend(r.WaistC0, CFrame.Angles(0, -legYaw * tune.WaistCounterFraction, 0))
	end

	-- === head look ===
	local neck = r.Neck
	local torso = neck and neck.Part0
	if neck and torso and tune.HeadLook then
		local lookAt: Vector3? = ctx.LookAt
		local head = neck.Part1
		local from = if head then head.Position else root.Position
		local dirWorld = if lookAt
			then lookAt - from
			elseif camera then camera.CFrame.LookVector
			else Vector3.zero
		local wantYaw, wantPitch2 = 0, 0
		if dirWorld.Magnitude > 1e-3 and not rolling then
			-- In the torso's space, ignoring the bend this frame is about to
			-- add to the neck itself.
			local d = torso.CFrame:VectorToObjectSpace(dirWorld.Unit)
			wantYaw, wantPitch2 = AnimationCore.headLook(d.X, d.Y, d.Z, GameConfig)
		end
		local headAlpha = AnimationCore.smoothAlpha(dt, tune.HeadSmoothSeconds)
		headYaw += (wantYaw - headYaw) * headAlpha
		headPitch += (wantPitch2 - headPitch) * headAlpha
		neck.C0 = bend(r.NeckC0, CFrame.Angles(0, headYaw, 0) * CFrame.Angles(headPitch, 0, 0))
	end

	-- === sounds ===
	local running = r.Running
	if running then
		local audible = ground > 0 and ctx.Grounded and speed > tune.IdleSpeed
		if audible then
			running.PlaybackSpeed = AnimationCore.runningSoundRate(speed, GameConfig)
			if not running.IsPlaying then
				running:Play()
			end
		elseif running.IsPlaying then
			running:Stop()
		end
	end
end

--- DEV: override one slot live ("" clears the override) and rebuild the
--- character's tracks. Returns (ok, message) for the dev command.
function CharacterAnimator.overrideSlot(name: string, id: string): (boolean, string)
	-- Typed by hand, a slot name's case should not matter.
	local found: string? = nil
	for _, slot in AnimationCore.SLOTS do
		if string.lower(slot) == string.lower(name) then
			found = slot
		end
	end
	if not found then
		return false, `unknown slot '{name}' (see /animslot with no arguments)`
	end
	name = found
	if id ~= "" then
		if string.match(id, "^%d+$") then
			id = "rbxassetid://" .. id
		end
		if not string.match(id, "^rbxassetid://%d+$") then
			return false, `'{id}' is not an animation id (a number, or rbxassetid://number)`
		end
		overrides[name] = id
	else
		overrides[name] = nil
	end
	local r = rig
	if r then
		CharacterAnimator.bind(r.Character, r.Humanoid, r.Root)
	end
	return true,
		if id == ""
			then `{name}: back to the shipped slot`
			else `{name} = {id} (live only; paste it into Content/Animations/Player.luau to keep it)`
end

--- DEV: every slot and where it currently comes from, for /animslot.
function CharacterAnimator.describeSlots(): { string }
	local lines = {}
	for _, name in AnimationCore.SLOTS do
		local source = if overrides[name]
			then `override {overrides[name]}`
			elseif AnimationCore.slot(PlayerAnimations, name) then `clip {PlayerAnimations[name]}`
			elseif generatedIds()[name] then "generated (Studio preview)"
			else "fallback"
		table.insert(lines, `{name}: {source}`)
	end
	return lines
end

return CharacterAnimator
