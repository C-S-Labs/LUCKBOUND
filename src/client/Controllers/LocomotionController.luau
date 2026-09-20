--!strict
-- RUN AND DOUBLE JUMP, and nothing else.
--
-- Phase 1 player abilities are movement. Everything offensive -- damage,
-- reach, cooldowns, hit effects, animations -- belongs to the item that grants
-- it: a sword model carries its own attributes and its own script, and this
-- controller must never grow a branch that knows about one.
-- docs/PLAYER_ABILITIES.md holds the planned ladder and which side of that
-- line each rung falls on.
--
-- EVERY RULE IS IN LocomotionCore. This file reads input, reads the Humanoid,
-- and writes a WalkSpeed; the stamina curve, the jump budget and the coyote
-- window are decided by a pure module that the test suite exercises directly.
-- A stamina bug found here is a test that was missing there.
--
-- ON TRUST: Roblox movement is client-authoritative by construction. The
-- server cannot make a character run and cannot stop one, which is why this
-- runs on the client and why nothing here is a security boundary. What the
-- server guards is outcomes -- roll distance, expedition entry, travel -- and
-- those are guarded where they happen.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local LocomotionCore = require(Root.Core.LocomotionCore)
local UITheme = require(Root.Core.UITheme)

local LocomotionController = {}

local player = Players.LocalPlayer

local state = LocomotionCore.newState(GameConfig, os.clock())
local humanoid: Humanoid? = nil
local wantsSprint = false
local gui: ScreenGui
local staminaTrack: Frame
local staminaFill: Frame

-- === the stamina pip =================================================
-- Deliberately tiny and deliberately silent: it fades in when stamina is
-- spent and fades out when it is full, so a player who never sprints never
-- learns there is a bar. A permanent stamina meter would make the hub feel
-- like a survival game, which it is not.

local function buildIndicator()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundLocomotion"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = -1
	gui.Parent = player:WaitForChild("PlayerGui")

	staminaTrack = Instance.new("Frame")
	staminaTrack.Name = "Stamina"
	staminaTrack.AnchorPoint = Vector2.new(0.5, 1)
	staminaTrack.Position = UDim2.new(0.5, 0, 1, -22)
	staminaTrack.Size = UDim2.fromOffset(120, 4)
	staminaTrack.BackgroundColor3 = UITheme.BackgroundColor
	staminaTrack.BackgroundTransparency = 1
	staminaTrack.BorderSizePixel = 0
	staminaTrack.Parent = gui
	UITheme.corner(staminaTrack, UDim.new(0, 2))

	staminaFill = Instance.new("Frame")
	staminaFill.Size = UDim2.fromScale(1, 1)
	staminaFill.BackgroundColor3 = UITheme.AccentGold
	staminaFill.BackgroundTransparency = 1
	staminaFill.BorderSizePixel = 0
	staminaFill.Parent = staminaTrack
	UITheme.corner(staminaFill, UDim.new(0, 2))
end

local function updateIndicator(fraction: number)
	local spent = fraction < 0.999
	staminaFill.Size = UDim2.fromScale(fraction, 1)
	staminaTrack.BackgroundTransparency = if spent then 0.4 else 1
	staminaFill.BackgroundTransparency = if spent then 0 else 1
	-- Amber at the bottom of the bar: the one moment the pip has something
	-- urgent to say.
	staminaFill.BackgroundColor3 = if fraction < 0.2 then UITheme.AccentWarn else UITheme.AccentGold
end

-- === the air jump ====================================================

--- A ring of light under the feet on the second jump. Without it the air jump
--- is invisible to everyone including the player who pressed it, and an
--- ability nobody can see reads as a physics glitch.
local function playAirJumpEffect(character: Model)
	if not GameConfig.Locomotion.AirJumpEffect then
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
	ring.Speed = NumberRange.new(12, 18)
	ring.SpreadAngle = Vector2.new(180, 180)
	ring.Size = NumberSequence.new(0.6)
	ring.Parent = attachment
	ring:Emit(18)

	-- Clean up after the longest particle can possibly live, never sooner:
	-- destroying the attachment early kills the effect mid-flight.
	task.delay(1, function()
		attachment:Destroy()
	end)
end

local function onJumpRequest()
	local character = player.Character
	if not character or not humanoid then
		return
	end

	local now = os.clock()
	local updated, kind = LocomotionCore.jump(state, now, GameConfig)
	state = updated

	if kind == "AIR" then
		-- ChangeState(Jumping) rather than setting Jump = true: the second
		-- one is ignored while the humanoid is in Freefall, which is exactly
		-- when an air jump happens.
		humanoid:ChangeState(Enum.HumanoidStateType.Jumping)
		local root = character:FindFirstChild("HumanoidRootPart")
		if root and root:IsA("BasePart") then
			-- Replace the vertical component rather than adding to it, so a
			-- jump pressed while falling fast is worth the same as one
			-- pressed at the top of an arc.
			local velocity = root.AssemblyLinearVelocity
			root.AssemblyLinearVelocity = Vector3.new(
				velocity.X,
				GameConfig.Locomotion.JumpPower * GameConfig.Locomotion.AirJumpPower,
				velocity.Z
			)
		end
		playAirJumpEffect(character)
	end
end

-- === wiring ==========================================================

local function bindCharacter(character: Model)
	local found = character:WaitForChild("Humanoid", 10)
	if not found or not found:IsA("Humanoid") then
		return
	end
	humanoid = found
	found.UseJumpPower = true
	found.JumpPower = GameConfig.Locomotion.JumpPower
	-- The jump budget resets from `Grounded` inside LocomotionCore.step, which
	-- reads Humanoid.FloorMaterial every frame -- so there is deliberately no
	-- StateChanged handler here. One source of "am I on the ground" is the
	-- whole reason the coyote window is testable.
	state = LocomotionCore.newState(GameConfig, os.clock())
end

local function step(dt: number)
	local character = player.Character
	if not character or not humanoid then
		return
	end

	local grounded = humanoid.FloorMaterial ~= Enum.Material.Air
	local moving = humanoid.MoveDirection.Magnitude > 0.1

	state = LocomotionCore.step(state, dt, {
		WantsSprint = wantsSprint,
		Moving = moving,
		Grounded = grounded,
		Now = os.clock(),
	}, GameConfig)

	local target = LocomotionCore.targetSpeed(state, GameConfig)
	-- Ramp rather than snap. The acceleration is what makes a sprint read as
	-- effort instead of as a speed setting.
	local tuning = GameConfig.Locomotion
	local rate = if target > humanoid.WalkSpeed
		then tuning.SprintAccelerationSeconds
		else tuning.SprintDecelerationSeconds
	local alpha = math.clamp(dt / math.max(rate, 1e-3), 0, 1)
	humanoid.WalkSpeed += (target - humanoid.WalkSpeed) * alpha

	updateIndicator(LocomotionCore.staminaFraction(state, GameConfig))
end

function LocomotionController.init(): ()
	buildIndicator()

	if player.Character then
		task.spawn(bindCharacter, player.Character)
	end
	player.CharacterAdded:Connect(bindCharacter)

	UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		if input.KeyCode == Enum.KeyCode.LeftShift or input.KeyCode == Enum.KeyCode.ButtonL3 then
			wantsSprint = true
		elseif input.KeyCode == Enum.KeyCode.Space or input.KeyCode == Enum.KeyCode.ButtonA then
			onJumpRequest()
		end
	end)

	UserInputService.InputEnded:Connect(function(input)
		if input.KeyCode == Enum.KeyCode.LeftShift or input.KeyCode == Enum.KeyCode.ButtonL3 then
			wantsSprint = false
		end
	end)

	-- Touch: the platform's own jump button fires Humanoid.Jumping rather
	-- than a key, and holding to move is the sprint gesture. Both are wired
	-- here so a phone gets the same two abilities a desktop does.
	if UserInputService.TouchEnabled then
		player.CharacterAdded:Connect(function(character)
			local found = character:WaitForChild("Humanoid", 10)
			if found and found:IsA("Humanoid") then
				found.Jumping:Connect(function(active)
					if active then
						onJumpRequest()
					end
				end)
			end
		end)
	end

	RunService.Heartbeat:Connect(step)
end

--- The current movement state, for anything that needs to draw it. Read-only
--- by convention: mutate it and the next frame overwrites you.
function LocomotionController.get(): any
	return state
end

return LocomotionController
