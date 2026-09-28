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
local function visible(from: Vector3, to: Vector3, ignore: { Instance }): boolean
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
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

local function release()
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
end

local function acquire()
	local root = playerRoot()
	local camera = Workspace.CurrentCamera
	if not root or not camera then
		return
	end
	local look = camera.CFrame.LookVector

	local candidates = {}
	for _, tagged in CollectionService:GetTagged(Constants.NAMES.LOCK_ON_TAG) do
		if tagged:IsDescendantOf(Workspace) then
			local centre = centreOf(tagged)
			if centre then
				local toTarget = centre - camera.CFrame.Position
				local angle = if toTarget.Magnitude > 1e-3
					then math.acos(math.clamp(look:Dot(toTarget.Unit), -1, 1))
					else 0
				table.insert(candidates, {
					Instance = tagged,
					Centre = centre,
					Distance = (centre - root.Position).Magnitude,
					AngleRadians = angle,
					Visible = visible(
						camera.CFrame.Position,
						centre,
						{ player.Character :: Instance, tagged }
					),
				})
			end
		end
	end

	local best = LockOnCore.pick(candidates, GameConfig)
	if not best then
		return
	end
	target = best.Instance
	local pivot = pivotOf(best.Instance)
	aimOffset = if pivot then pivot:ToObjectSpace(CFrame.new(best.Centre)) else CFrame.identity
	outOfSightSeconds = 0
	cameraCFrame = camera.CFrame
	showMarker(best.Instance)
end

local function toggle()
	if target then
		release()
	else
		acquire()
	end
end

-- === the camera ======================================================

local function update(dt: number)
	local held = target
	if not held then
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
		release()
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
	params.FilterDescendantsInstances = ignore
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

	-- A new character (death, respawn, teleport) starts unlocked.
	player.CharacterAdded:Connect(release)

	-- After the default camera has run, so ours is the one that shows.
	RunService:BindToRenderStep("LuckboundLockOn", Enum.RenderPriority.Camera.Value + 1, update)
end

return LockOnController
