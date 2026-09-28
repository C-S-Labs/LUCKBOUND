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

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local AnimationCore = require(Root.Core.AnimationCore)
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)
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

-- The current roll: its direction relative to facing, "BACKSTEP", or nil.
local rollKind: string? = nil
local rollStartedAt = 0
local rollDuration = 1
local nextGhostAt = 0
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

	local set = PlayerAnimations
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
	landKind, landedAt = kind, now
	playOneShot(if kind == "HARD" then "LandHard" else "LandSoft")
	local r = rig
	if r and r.Land then
		r.Land.Volume = GameConfig.CharacterAnimation.LandVolume
			* (if kind == "HARD" then 1 else 0.6)
		r.Land:Play()
	end
end

--- A roll starting. `relative` is "FORWARD" / "BACKWARD" / "LEFT" /
--- "RIGHT" (the roll's direction against facing) or "BACKSTEP".
function CharacterAnimator.onRoll(relative: string, now: number, duration: number): ()
	rollKind, rollStartedAt, rollDuration = relative, now, math.max(duration, 1e-3)
	nextGhostAt = 0
	local slot = if relative == "BACKSTEP"
		then "Backstep"
		else "Roll" .. string.sub(relative, 1, 1) .. string.lower(string.sub(relative, 2))
	-- A clip for this direction replaces the procedural tumble.
	if playOneShot(slot, duration) then
		rollKind = relative .. "_CLIP"
	end

	local camera = Workspace.CurrentCamera
	local kick = GameConfig.Locomotion.RollFovKickDegrees
	if camera and kick > 0 then
		fovBase = fovBase or camera.FieldOfView
		camera.FieldOfView = (fovBase :: number) + kick
	end
end

-- === the roll's look =================================================

--- One afterimage: a faint copy of every visible part, left in place.
local function dropGhost(character: Model)
	local tune = GameConfig.Locomotion
	local folder = Instance.new("Folder")
	folder.Name = "LuckboundRollGhost"
	local info =
		TweenInfo.new(tune.RollGhostFadeSeconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") and part.Transparency < 1 and part.Name ~= "HumanoidRootPart" then
			local ok, copy = pcall(function()
				return part:Clone()
			end)
			if ok and copy then
				for _, child in copy:GetChildren() do
					if not child:IsA("SpecialMesh") then
						child:Destroy()
					end
				end
				copy.Anchored = true
				copy.CanCollide = false
				copy.CanQuery = false
				copy.CanTouch = false
				copy.CastShadow = false
				copy.Material = Enum.Material.Neon
				copy.Color = UITheme.AccentGold
				copy.Transparency = tune.RollGhostTransparency
				if copy:IsA("MeshPart") then
					copy.TextureID = ""
				end
				copy.CFrame = part.CFrame
				copy.Parent = folder
				TweenService:Create(copy, info, { Transparency = 1 }):Play()
			end
		end
	end
	folder.Parent = Workspace
	task.delay(tune.RollGhostFadeSeconds + 0.1, function()
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

	local rolling = ctx.Mode == "ROLL"
	local airborne = ctx.Mode == "AIR"
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
		local progress = (now - rollStartedAt) / rollDuration
		if kind == "BACKSTEP" then
			-- A short hop back: the body leans away and dips.
			local arc = math.sin(math.clamp(progress, 0, 1) * math.pi)
			tumblePitch = 0.3 * arc
			tumbleDip = 0.4 * arc
		elseif GameConfig.Locomotion.RollTumble and not string.find(kind, "_CLIP", 1, true) then
			tumblePitch, tumbleBank, tumbleDip = AnimationCore.tumble(kind, progress, GameConfig)
		end
		if GameConfig.Locomotion.RollGhosts and now >= nextGhostAt then
			nextGhostAt = now + GameConfig.Locomotion.RollGhostIntervalSeconds
			dropGhost(r.Character)
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
			CFrame.Angles(0, legYaw, 0)
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

return CharacterAnimator
