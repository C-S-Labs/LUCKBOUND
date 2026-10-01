--!strict
-- LOCK-ON: an optional target lock with an over-the-shoulder camera.
--
-- Owner-directed 2026-09-28: the game plays fully without it, and it must
-- not require changing any enemy. A target is any Model or BasePart the game
-- has tagged with Constants.NAMES.LOCK_ON_TAG; the spawner adds the tag (the
-- /showboss preview does today), so the enemy asset never knows lock-on
-- exists. The aim point is the target's bounding-box centre, measured once
-- when the lock is taken, so a rig with no PrimaryPart or named parts works.
--
-- Input: middle mouse, R3 on a gamepad, a Lock button on touch. Press to
-- lock the best target in view; press again to release.
--
-- While locked the camera sits behind and over the right shoulder, looking
-- past the player toward the target, and the character strafes facing it
-- (LocomotionController.setLockTarget). Every rule -- which target, when to
-- drop -- is in LockOnCore; this file measures and draws.

local CollectionService = game:GetService("CollectionService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local LockOnCore = require(Root.Core.LockOnCore)
local UITheme = require(Root.Core.UITheme)

local LockOnController = {}

local player = Players.LocalPlayer
local locomotion: any = nil

local target: Instance? = nil
-- The aim point in the target's own pivot space, fixed at lock time.
local aimOffset = CFrame.identity
local outOfSightSeconds = 0
local cameraCFrame: CFrame? = nil
local marker: BillboardGui? = nil

local function pivotOf(instance: Instance): CFrame?
	if instance:IsA("Model") then
		return instance:GetPivot()
	elseif instance:IsA("BasePart") then
		return instance.CFrame
	end
	return nil
end

local function centreOf(instance: Instance): Vector3?
	if instance:IsA("Model") then
		local box = instance:GetBoundingBox()
		return box.Position
	elseif instance:IsA("BasePart") then
		return instance.Position
	end
	return nil
end

local function aimPoint(instance: Instance): Vector3?
	local pivot = pivotOf(instance)
	if not pivot then
		return nil
	end
	return (pivot * aimOffset).Position
end

local function playerRoot(): BasePart?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		return root
	end
	return nil
end

--- Nothing solid between the camera and the point?
local function cameraIgnore(ignore: { Instance }): { Instance }
	local result = table.clone(ignore)
	for _, boundary in CollectionService:GetTagged(Constants.NAMES.CHUNK_BOUNDARY_TAG) do
		table.insert(result, boundary)
	end
	return result
end

local function visible(from: Vector3, to: Vector3, ignore: { Instance }): boolean
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = cameraIgnore(ignore)
	return Workspace:Raycast(from, to - from, params) == nil
end

-- === the marker ======================================================
-- A small gold diamond on the target: one glance says what is locked.

local function showMarker(instance: Instance?)
	if marker then
		marker:Destroy()
		marker = nil
	end
	if not instance then
		return
	end
	local adornee: Instance? = if instance:IsA("Model") then instance.PrimaryPart else instance
	if instance:IsA("Model") and not adornee then
		adornee = instance:FindFirstChildWhichIsA("BasePart", true)
	end
	if not adornee or not adornee:IsA("BasePart") then
		return
	end

	local gui = Instance.new("BillboardGui")
	gui.Name = "LuckboundLockOnMarker"
	gui.Size = UDim2.fromOffset(18, 18)
	gui.AlwaysOnTop = true
	gui.LightInfluence = 0
	gui.Adornee = adornee
	-- Offset from the adornee to the aim point, so the diamond sits where
	-- the camera aims rather than wherever the part happens to be.
	local aim = aimPoint(instance)
	if aim then
		gui.StudsOffsetWorldSpace = aim - adornee.Position
	end

	local diamond = Instance.new("Frame")
	diamond.AnchorPoint = Vector2.new(0.5, 0.5)
	diamond.Position = UDim2.fromScale(0.5, 0.5)
	diamond.Size = UDim2.fromOffset(10, 10)
	diamond.Rotation = 45
	diamond.BackgroundColor3 = UITheme.AccentGold
	diamond.BorderSizePixel = 0
	diamond.Parent = gui
	UITheme.stroke(diamond, UITheme.BackgroundColor, 2)

	gui.Parent = player:WaitForChild("PlayerGui")
	marker = gui
end

-- === taking and dropping =============================================

-- The camera's ease back after a release: where it was when the lock let
-- go, and when. nil = not easing.
local releaseFrom: CFrame? = nil
local releaseStartedAt = 0

--- Drops the lock. `ease` hands the view back smoothly (a player's release,
--- a lock that broke); without it the view snaps (a new character).
local function release(ease: boolean?)
	local camera0 = Workspace.CurrentCamera
	if ease and target and camera0 then
		releaseFrom = camera0.CFrame
		releaseStartedAt = os.clock()
	else
		releaseFrom = nil
	end
	if target and UserInputService.TouchEnabled then
		ContextActionService:UnbindAction("LuckboundLockNext")
	end
	target = nil
	cameraCFrame = nil
	outOfSightSeconds = 0
	showMarker(nil)
	if locomotion then
		locomotion.setLockTarget(nil)
	end
	local camera = Workspace.CurrentCamera
	if camera and camera.CameraType == Enum.CameraType.Scriptable then
		camera.CameraType = Enum.CameraType.Custom
	end
	-- Hand the mouse back (the shoulder camera re-captures it next frame if on).
	UserInputService.MouseBehavior = Enum.MouseBehavior.Default
end

--- Every tagged thing in the world, measured from the camera.
local function measure(camera: Camera, root: BasePart): { any }
	local look = camera.CFrame.LookVector
	local right = camera.CFrame.RightVector
	local candidates = {}
	for _, tagged in CollectionService:GetTagged(Constants.NAMES.LOCK_ON_TAG) do
		if tagged:IsDescendantOf(Workspace) then
			local centre = centreOf(tagged)
			if centre then
				local toTarget = centre - camera.CFrame.Position
				local unit = if toTarget.Magnitude > 1e-3 then toTarget.Unit else look
				table.insert(candidates, {
					Instance = tagged,
					Centre = centre,
					Distance = (centre - root.Position).Magnitude,
					AngleRadians = math.acos(math.clamp(look:Dot(unit), -1, 1)),
					-- How far right of the camera's centre line, for switching.
					Side = right:Dot(unit),
					Visible = visible(
						camera.CFrame.Position,
						centre,
						{ player.Character :: Instance, tagged }
					),
				})
			end
		end
	end
	return candidates
end

local lastSwitchAt = 0

--- Takes (or moves) the lock onto a measured candidate.
local function lockOnto(candidate: any, camera: Camera)
	local first = target == nil
	target = candidate.Instance
	local pivot = pivotOf(candidate.Instance)
	aimOffset = if pivot then pivot:ToObjectSpace(CFrame.new(candidate.Centre)) else CFrame.identity
	outOfSightSeconds = 0
	if first then
		cameraCFrame = camera.CFrame
	end
	showMarker(candidate.Instance)
	if first and UserInputService.TouchEnabled then
		ContextActionService:BindAction("LuckboundLockNext", function(_, inputState)
			if inputState == Enum.UserInputState.Begin then
				LockOnController.switch(1)
			end
			return Enum.ContextActionResult.Pass
		end, true)
		ContextActionService:SetTitle("LuckboundLockNext", "Next")
	end
end

local function acquire()
	local root = playerRoot()
	local camera = Workspace.CurrentCamera
	if not root or not camera then
		return
	end
	local best = LockOnCore.pick(measure(camera, root), GameConfig)
	if best then
		lockOnto(best, camera)
	end
end

--- Moves the lock one target to the right (1) or left (-1), if there is one.
function LockOnController.switch(direction: number): ()
	local held = target
	local root = playerRoot()
	local camera = Workspace.CurrentCamera
	local now = os.clock()
	if not held or not root or not camera then
		return
	end
	if now - lastSwitchAt < GameConfig.LockOn.SwitchCooldownSeconds then
		return
	end

	local candidates = measure(camera, root)
	local currentSide = 0
	for _, c in candidates do
		if c.Instance == held then
			currentSide = c.Side
		end
	end
	local others = {}
	for _, c in candidates do
		if c.Instance ~= held then
			c.Offset = c.Side - currentSide
			table.insert(others, c)
		end
	end

	local nextTarget = LockOnCore.switch(others, direction, GameConfig)
	if nextTarget then
		lastSwitchAt = now
		lockOnto(nextTarget, camera)
	end
end

local function toggle()
	if target then
		release(true)
	else
		acquire()
	end
end

-- === the camera ======================================================

--- THE EASE BACK. The default camera has already run this frame and put
--- the view where it wants it; this blends from where the lock left the view
--- toward that, so letting go flows back to the normal (or shoulder) view
--- the way taking a lock flows in. The default camera reads its own last
--- CFrame next frame, so the blend converges instead of fighting it.
local function easeBack()
	local from = releaseFrom
	local camera = Workspace.CurrentCamera
	if not from or not camera then
		return
	end
	local seconds = GameConfig.LockOn.ReleaseBlendSeconds
	local t = if seconds > 0 then math.clamp((os.clock() - releaseStartedAt) / seconds, 0, 1) else 1
	if t >= 1 then
		releaseFrom = nil
		return
	end
	-- Ease out: quick to leave the lock's framing, gentle to settle.
	local eased = 1 - (1 - t) ^ 3
	camera.CFrame = from:Lerp(camera.CFrame, eased)
end

local function update(dt: number)
	local held = target
	if not held then
		easeBack()
		return
	end
	local root = playerRoot()
	local camera = Workspace.CurrentCamera
	local aim = aimPoint(held)
	if not root or not camera or not aim then
		release()
		return
	end

	local distance = (aim - root.Position).Magnitude
	local ignore = { player.Character :: Instance, held }
	if visible(camera.CFrame.Position, aim, ignore) then
		outOfSightSeconds = 0
	else
		outOfSightSeconds += dt
	end
	local tagged = held:IsDescendantOf(Workspace)
		and CollectionService:HasTag(held, Constants.NAMES.LOCK_ON_TAG)
	if LockOnCore.shouldBreak(distance, outOfSightSeconds, tagged, GameConfig) then
		release(true)
		return
	end

	locomotion.setLockTarget(aim)

	local tuning = GameConfig.LockOn
	local aimAt =
		Vector3.new(aim.X, LockOnCore.aimHeight(aim.Y, root.Position.Y, GameConfig), aim.Z)

	-- The shoulder: above the root, a little to the right of the line from
	-- the player to the target.
	local flat = Vector3.new(aimAt.X - root.Position.X, 0, aimAt.Z - root.Position.Z)
	local forward = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local right = forward:Cross(Vector3.yAxis)
	local shoulder = root.Position
		+ Vector3.yAxis * tuning.ShoulderHeight
		+ right * tuning.ShoulderOffset

	local back = (aimAt - shoulder)
	local backDir = if back.Magnitude > 1e-3 then back.Unit else forward
	local wanted = shoulder - backDir * tuning.CameraDistance + Vector3.yAxis * tuning.CameraLift

	-- A wall between the shoulder and the camera pulls the camera in.
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = cameraIgnore(ignore)
	local hit = Workspace:Raycast(shoulder, wanted - shoulder, params)
	if hit then
		local pulled = (hit.Position - shoulder).Magnitude - 0.5
		local fullLength = (wanted - shoulder).Magnitude
		local length = math.max(pulled, tuning.CameraMinDistance)
		wanted = shoulder + (wanted - shoulder).Unit * math.min(length, fullLength)
	end

	local lookAt = shoulder:Lerp(aimAt, tuning.LookBias)
	local goal = CFrame.lookAt(wanted, lookAt)
	local alpha = LockOnCore.smoothAlpha(dt, tuning.CameraSmoothSeconds)
	cameraCFrame = if cameraCFrame then cameraCFrame:Lerp(goal, alpha) else goal

	camera.CameraType = Enum.CameraType.Scriptable
	camera.CFrame = cameraCFrame :: CFrame
	-- The mouse is captured while locked: the camera does not use it, and
	-- Roblox only reports mouse Delta for a captured mouse, which the
	-- target-switch flick needs (found on the owner's walk, 2026-09-28).
	UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
end

--- `deps` = { Locomotion }. Called once PLAY is pressed, after movement.
function LockOnController.init(deps: any): ()
	locomotion = deps.Locomotion

	ContextActionService:BindAction("LuckboundLockOn", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			toggle()
		end
		return Enum.ContextActionResult.Pass
	end, true, Enum.UserInputType.MouseButton3, Enum.KeyCode.ButtonR3)
	ContextActionService:SetTitle("LuckboundLockOn", "Lock")

	-- SWITCHING: a sideways flick of the mouse or right stick while locked.
	-- The locked camera ignores both, so neither gesture is taken from
	-- anything else. Touch gets a Next button while locked (see lockOnto).
	local tuning = GameConfig.LockOn
	local mouseTravel = 0
	local mouseTravelStarted = 0
	local stickArmed = true
	local lastMouseX: number? = nil
	UserInputService.InputChanged:Connect(function(input, processed)
		if processed or not target then
			return
		end
		if input.UserInputType == Enum.UserInputType.MouseMovement then
			local now = os.clock()
			if now - mouseTravelStarted > tuning.SwitchMouseWindowSeconds then
				mouseTravel = 0
				mouseTravelStarted = now
			end
			-- Delta when the mouse is captured; the change in position if
			-- something released it, so the flick works either way.
			local dx = input.Delta.X
			if dx == 0 and lastMouseX then
				dx = input.Position.X - lastMouseX
			end
			lastMouseX = input.Position.X
			mouseTravel += dx
			local direction = LockOnCore.flick(mouseTravel, tuning.SwitchMousePixels)
			if direction ~= 0 then
				mouseTravel = 0
				LockOnController.switch(direction)
			end
		elseif input.KeyCode == Enum.KeyCode.Thumbstick2 then
			local x = input.Position.X
			if math.abs(x) < tuning.SwitchStickRest then
				stickArmed = true
			elseif stickArmed then
				local direction = LockOnCore.flick(x, tuning.SwitchStickThreshold)
				if direction ~= 0 then
					stickArmed = false
					LockOnController.switch(direction)
				end
			end
		end
	end)

	-- A new character (death, respawn, teleport) starts unlocked.
	player.CharacterAdded:Connect(function()
		release(false)
	end)

	-- After the default camera has run, so ours is the one that shows.
	RunService:BindToRenderStep("LuckboundLockOn", Enum.RenderPriority.Camera.Value + 1, update)
	print("[LockOn] ready: middle mouse / R3 to lock (needs a target: /dummies or /showboss)")
end

return LockOnController
