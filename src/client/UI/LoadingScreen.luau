--!strict
-- THE FIRST THING ANYONE SEES. Owner-directed (STATUS §4, "First-join intro
-- screen"), and its purpose is half technical: the hub is hundreds of
-- instances of authored art, and until they arrive the player is standing in
-- a half-built world with no explanation. This gives that wait a face, a
-- camera move, and a button that says when it is over.
--
-- WHAT IT DOES, IN ORDER:
--   1. Takes the camera before the character exists, so the player never sees
--      the inside of a partially replicated hub.
--   2. Flies a slow arc around each subject in Content/Hub/Cinematics, blurred
--      and crossfaded, behind the title.
--   3. Counts what has actually arrived and preloads what is on screen.
--   4. Lights its one button -- PLAY -- when the place is ready AND
--      GameConfig.Loading.MinimumSeconds
--      has passed -- never before, so a warm client still gets the intro, and
--      never later than MaximumSeconds, so a stalled one is not held hostage.
--
-- TWO RULES IT KEEPS:
--   * IT NEVER TRAPS A PLAYER. Every wait is bounded. If replication stalls,
--     PLAY lights anyway and says so.
--   * IT RESTORES WHAT IT TOOK. Camera type, blur, field of view and the
--     character's movement are all snapshotted and put back on PLAY -- the
--     same discipline ExpeditionController uses for biome lighting.

local ContentProvider = game:GetService("ContentProvider")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Cinematics = require(Root.Content.Hub.Cinematics)
local Net = require(Root.Core.Net)
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)

local UIKit = require(script.Parent.UIKit)

local LoadingScreen = {}

local player = Players.LocalPlayer

local gui: ScreenGui
local backdrop: Frame
local titleLabel: TextLabel
local captionLabel: TextLabel
local statusLabel: TextLabel
local progressFill: Frame
local playButton: TextButton

local blur: BlurEffect?
local camera: Camera
local savedFieldOfView: number?
local finished = false
local ready = false
local startedAt = 0

local listeners: { () -> () } = {}

--- Fires when the player presses PLAY. The hub animator and the roll UI use
--- it to hold their entrance until there is someone to see it.
function LoadingScreen.onFinished(fn: () -> ()): ()
	if finished then
		task.spawn(fn)
		return
	end
	table.insert(listeners, fn)
end

function LoadingScreen.isFinished(): boolean
	return finished
end

-- === the camera tour ================================================

--- Shots whose world is actually present. A shot naming a world declares a
--- dependency on geometry that only exists while someone is inside it, so it
--- is skipped rather than pointed at empty sky.
local function playableShots(): { any }
	local shots = {}
	for _, shot in Cinematics.Shots do
		if shot.WorldId == nil then
			table.insert(shots, shot)
		end
	end
	return shots
end

--- One slow arc. Returns when the shot's time is up or the screen is done.
local function playShot(shot: any, index: number)
	local loading = GameConfig.Loading
	local subject = shot.Subject
	local look = subject + shot.LookOffset

	-- Each shot starts from a different bearing so the tour does not read as
	-- one camera circling one building. Deterministic -- the golden angle
	-- rather than a random draw, because a loading screen that looks
	-- different every time reads as unstable, and because CLAUDE.md rule 6
	-- forbids math.random anyway.
	local startAngle = math.rad((index - 1) * 137.5)
	local sweep = math.rad(loading.ShotArcDegrees)

	captionLabel.Text = shot.Caption
	captionLabel.TextTransparency = 1
	UIKit.tween(captionLabel, UITheme.Motion.Slow, { TextTransparency = 0.25 })

	local elapsed = 0
	while elapsed < loading.ShotSeconds and not finished do
		local dt = RunService.RenderStepped:Wait()
		elapsed += dt

		-- STOP THE MOMENT PLAY IS PRESSED, BEFORE TOUCHING THE CAMERA.
		--
		-- This guard is the whole fix for a bug reported from the second
		-- Studio walk: "camera is still stuck". RenderStepped:Wait() returns
		-- mid-frame, so finish() could run WHILE this loop was suspended --
		-- releasing the camera to the player -- and then the next two lines
		-- would take it straight back and pin it to the tour's last position
		-- forever. The release lost a race it did not know it was in.
		if finished then
			return
		end

		-- THE CAMERA HAS TO BE TAKEN BACK EVERY FRAME WHILE LOADING. When the
		-- character spawns, Roblox's own camera script sets CameraType to
		-- Custom and starts following the humanoid -- which is why the first
		-- walk reported the camera "locked in place" partway through loading.
		-- It had not locked; it had been handed back. Re-acquiring
		-- CurrentCamera as well, because the engine can replace the camera
		-- object outright on spawn, leaving this module writing to an orphan.
		local live = Workspace.CurrentCamera
		if live and live ~= camera then
			camera = live
			camera.FieldOfView = loading.FieldOfView
		end
		if camera.CameraType ~= Enum.CameraType.Scriptable then
			camera.CameraType = Enum.CameraType.Scriptable
		end

		local t = elapsed / loading.ShotSeconds
		local angle = startAngle + sweep * t
		-- A gentle push in over the shot. Parallax is what makes a slow move
		-- read as a move rather than as a still frame.
		local radius = shot.Radius * (1 - loading.ShotDollyFraction * t)
		local position = subject
			+ Vector3.new(math.cos(angle) * radius, shot.Height, math.sin(angle) * radius)

		camera.CFrame = CFrame.lookAt(position, look)
	end

	if not finished then
		UIKit.tween(captionLabel, loading.ShotCrossfadeSeconds, { TextTransparency = 1 }, true)
	end
end

local function runTour()
	local shots = playableShots()
	if #shots == 0 then
		-- Content validation would have caught an empty shot list at boot, so
		-- this is the "every shot names an unloaded world" case. Hold a fixed
		-- frame rather than leaving the camera wherever it happened to be.
		camera.CFrame = CFrame.lookAt(Vector3.new(0, 400, 900), Vector3.new(0, 0, 0))
		return
	end

	local index = 1
	while not finished do
		playShot(shots[index], index)
		index += 1
		if index > #shots then
			index = 1
		end
	end
end

-- === readiness ======================================================

--- HAS THE PLACE ARRIVED? Two questions, both bounded.
---
--- Instance count is the honest one: the authored Crossroads is a known
--- number of parts (STATUS records 436 as the mobile baseline) and until they
--- have replicated there is nothing to look at. Preloading is the second: the
--- engine knows when the meshes and textures in view have finished streaming,
--- and PreloadAsync is the only way to ask.
local function countHub(): number
	local crossroads = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if not crossroads then
		return 0
	end
	return #crossroads:GetDescendants()
end

local preloadDone = false

local function preloadInBatches()
	local crossroads = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if not crossroads then
		preloadDone = true
		return
	end

	local queue: { Instance } = {}
	for _, descendant in crossroads:GetDescendants() do
		if descendant:IsA("MeshPart") or descendant:IsA("Decal") or descendant:IsA("Texture") then
			table.insert(queue, descendant)
		end
	end

	-- In batches, because PreloadAsync on several hundred meshes at once
	-- blocks this thread for as long as it takes and the progress bar would
	-- sit still through all of it.
	local batch: { Instance } = {}
	for _, instance in queue do
		table.insert(batch, instance)
		if #batch >= GameConfig.Loading.PreloadBatchSize then
			pcall(ContentProvider.PreloadAsync, ContentProvider, batch)
			batch = {}
			if finished then
				preloadDone = true
				return
			end
		end
	end
	if #batch > 0 then
		pcall(ContentProvider.PreloadAsync, ContentProvider, batch)
	end
	preloadDone = true
end

local function setReady(reason: string)
	if ready then
		return
	end
	ready = true
	statusLabel.Text = reason
	progressFill.Size = UDim2.fromScale(1, 1)
	UIKit.setEnabled(playButton, true)
	UIKit.tween(playButton, UITheme.Motion.Normal, { BackgroundColor3 = UITheme.AccentGold })
end

local function watchProgress()
	local loading = GameConfig.Loading
	task.spawn(preloadInBatches)

	-- REPLICATION IS JUDGED BY ITS SHAPE, NOT BY A COUNT. Instances arrive,
	-- then they stop arriving. Waiting for a specific number meant guessing
	-- how many parts the hub has -- and the guess was 380 against a hub that
	-- builds 357, so the bar stuck at 94% and every player was told loading
	-- had taken longer than usual. Watching it settle needs no number and
	-- survives the art changing.
	local lastCount = -1
	local settledFor = 0

	while not ready and not finished do
		local elapsed = os.clock() - startedAt
		local arrived = countHub()

		if arrived == lastCount and arrived >= loading.MinimumHubInstances then
			settledFor += loading.HubPollSeconds
		else
			settledFor = 0
		end
		lastCount = arrived

		-- Two halves: the hub showing up at all, then it holding still. The
		-- bar reaches 1 exactly when replication has settled, so it never
		-- sits full while the screen refuses to open -- the single most
		-- annoying thing a loading bar can do.
		local arrivalProgress = math.clamp(arrived / loading.MinimumHubInstances, 0, 1) * 0.5
		local settleProgress = math.clamp(settledFor / loading.HubSettleSeconds, 0, 1) * 0.5
		local replicated = arrivalProgress + settleProgress
		local timeProgress = math.clamp(elapsed / loading.MinimumSeconds, 0, 1)

		local shown = math.min(replicated, timeProgress)
		UIKit.tween(progressFill, UITheme.Motion.Normal, { Size = UDim2.fromScale(shown, 1) })
		statusLabel.Text = string.format("Building the Crossroads…  %d%%", math.floor(shown * 100))

		local replicationDone = settledFor >= loading.HubSettleSeconds
		if elapsed >= loading.MaximumSeconds then
			setReady("Taking longer than usual — you can go in now.")
		elseif replicationDone and preloadDone and elapsed >= loading.MinimumSeconds then
			setReady("Ready.")
		end

		task.wait(loading.HubPollSeconds)
	end
end

-- === taking and giving back =========================================

--- Only reached if a character somehow exists while the screen is up -- a
--- respawn, or Players.CharacterAutoLoads being turned back on. The normal
--- first join has no character at all until PLAY is pressed.
local function holdCharacter(character: Model)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if humanoid and humanoid:IsA("Humanoid") then
		if finished then
			return
		end
		-- The player is looking at a camera tour, not at their character. A
		-- character that can walk off during it arrives at PLAY somewhere
		-- other than where the hub put them.
		humanoid.WalkSpeed = 0
		humanoid.JumpPower = 0
	end
end

local function releaseCharacter()
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.WalkSpeed = GameConfig.Scale.WalkSpeed
		humanoid.UseJumpPower = true
		humanoid.JumpPower = GameConfig.Locomotion.JumpPower
	end
end

--- HANDS THE CAMERA BACK TO THE PLAYER.
---
--- WHY THIS DOES NOT RESTORE WHAT IT SAVED. It used to write back the
--- CameraType captured at init -- and on a FIRST join that capture happens
--- before Roblox's own camera system has started, when CurrentCamera.CameraType
--- is still `Fixed`. So the screen faithfully restored `Fixed`, and a Fixed
--- camera does not follow anybody. It looked exactly like the camera was
--- still stuck, and it only happened on the first load: after a respawn the
--- camera script had already set `Custom`, so the saved value was right by
--- accident. Reported from the third Studio walk, with precisely that clue --
--- "resetting the character fixed it".
---
--- Gameplay wants `Custom`. That is not a value worth preserving from a
--- moment before the game had started, so it is simply asserted.
---
--- Restoring CameraType is also not enough on its own: while the tour held
--- the camera as Scriptable, the camera script never got to point it at
--- anything, and `Custom` with no CameraSubject sits where it was left. The
--- subject has to be named, and the character may not have finished loading
--- when PLAY is pressed -- hence the retry.
local function pointCameraAtCharacter(): boolean
	local live = Workspace.CurrentCamera
	if not live then
		return false
	end
	camera = live
	camera.FieldOfView = savedFieldOfView or 70

	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		return false
	end

	camera.CameraSubject = humanoid
	camera.CameraType = Enum.CameraType.Custom
	return true
end

local function releaseCamera()
	if pointCameraAtCharacter() then
		return
	end

	-- No character yet. Keep trying briefly rather than leaving the player
	-- looking at a frozen frame -- and bounded, so a character that never
	-- arrives does not leave a thread spinning for the session.
	task.spawn(function()
		for _ = 1, 40 do
			task.wait(0.1)
			if pointCameraAtCharacter() then
				return
			end
		end
		warn("[LoadingScreen] gave up handing the camera back -- no humanoid arrived")
	end)
end

local function finish()
	if finished then
		return
	end
	finished = true

	local fade = UIKit.tween(backdrop, UITheme.Motion.Slow, { BackgroundTransparency = 1 })
	for _, child in gui:GetDescendants() do
		if child:IsA("TextLabel") or child:IsA("TextButton") then
			UIKit.tween(child, UITheme.Motion.Normal, { TextTransparency = 1 }, true)
		end
		if child:IsA("GuiObject") and child ~= backdrop then
			UIKit.tween(child, UITheme.Motion.Normal, { BackgroundTransparency = 1 }, true)
		end
	end

	if blur then
		TweenService:Create(blur, TweenInfo.new(UITheme.Motion.Slow), { Size = 0 }):Play()
	end

	-- ASK FOR A CHARACTER. Nobody has one until now: the server holds every
	-- spawn until this arrives (build spec §4, Player_Ready), so the player
	-- cannot have been standing in the hub behind the screen.
	Net.get("Player_Ready"):FireServer()

	releaseCamera()
	releaseCharacter()

	-- The belt to releaseCamera's braces: by now the tour has certainly
	-- stopped, so whatever it may have written last frame is undone.
	task.defer(releaseCamera)

	-- And if the character arrives AFTER Play was pressed -- a slow spawn, or
	-- a respawn on the way in -- the camera needs pointing at it then too.
	player.CharacterAdded:Connect(function(character)
		local humanoid = character:WaitForChild("Humanoid", 10)
		if humanoid and humanoid:IsA("Humanoid") then
			local live = Workspace.CurrentCamera
			if live then
				live.CameraSubject = humanoid
				live.CameraType = Enum.CameraType.Custom
			end
		end
	end)

	fade.Completed:Once(function()
		gui:Destroy()
		if blur then
			blur:Destroy()
			blur = nil
		end
	end)

	for _, fn in listeners do
		task.spawn(fn)
	end
	listeners = {}
end

-- === build ==========================================================

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundLoading"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	-- Above everything. It is the only screen in the game that is allowed to
	-- be.
	gui.DisplayOrder = 100
	gui.Parent = player:WaitForChild("PlayerGui")

	-- A dark wash rather than a solid fill: the camera tour is the background
	-- and must stay legible through it, but white text on an unblurred hub is
	-- not readable at any size.
	backdrop = Instance.new("Frame")
	backdrop.Size = UDim2.fromScale(1, 1)
	backdrop.BackgroundColor3 = UITheme.BackgroundColor
	backdrop.BackgroundTransparency = 0.35
	backdrop.BorderSizePixel = 0
	backdrop.Parent = gui

	-- The vignette: the same wash again, gradient-faded, so the edges of the
	-- screen are darker than the middle and the title sits in a pool of
	-- light. Two frames is cheaper than an image and cannot fail to load.
	local vignette = Instance.new("Frame")
	vignette.Size = UDim2.fromScale(1, 1)
	vignette.BackgroundColor3 = Color3.new(0, 0, 0)
	vignette.BackgroundTransparency = 0.25
	vignette.BorderSizePixel = 0
	vignette.Parent = backdrop

	local vignetteGradient = Instance.new("UIGradient")
	vignetteGradient.Rotation = 90
	vignetteGradient.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.2),
		NumberSequenceKeypoint.new(0.5, 1),
		NumberSequenceKeypoint.new(1, 0.1),
	})
	vignetteGradient.Parent = vignette

	titleLabel = UIKit.label(backdrop, "LUCKBOUND", 64)
	titleLabel.Font = UITheme.HeaderFont
	titleLabel.AnchorPoint = Vector2.new(0.5, 1)
	titleLabel.Position = UDim2.fromScale(0.5, 0.44)
	titleLabel.Size = UDim2.new(0.9, 0, 0, 74)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Center
	titleLabel.TextColor3 = UITheme.TextPrimary

	local titleGradient = Instance.new("UIGradient")
	titleGradient.Rotation = 90
	titleGradient.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, UITheme.TextPrimary),
		ColorSequenceKeypoint.new(1, UITheme.AccentGold),
	})
	titleGradient.Parent = titleLabel

	local tagline = UIKit.label(backdrop, "Roll the world. Walk what you get.", 18, "SECONDARY")
	tagline.AnchorPoint = Vector2.new(0.5, 0)
	tagline.Position = UDim2.fromScale(0.5, 0.45)
	tagline.Size = UDim2.new(0.9, 0, 0, 24)
	tagline.TextXAlignment = Enum.TextXAlignment.Center

	-- The caption names the place on screen. It is what makes the tour read
	-- as a tour of somewhere rather than as a screensaver.
	captionLabel = UIKit.label(backdrop, "", 15, "MUTED")
	captionLabel.AnchorPoint = Vector2.new(0, 1)
	captionLabel.Position = UDim2.new(0, UITheme.Space.XL, 1, -UITheme.Space.XL)
	captionLabel.Size = UDim2.fromOffset(420, 22)

	local controls = Instance.new("Frame")
	controls.AnchorPoint = Vector2.new(0.5, 0)
	controls.Position = UDim2.fromScale(0.5, 0.56)
	controls.Size = UDim2.new(0.5, 0, 0, 100)
	controls.BackgroundTransparency = 1
	controls.Parent = backdrop

	local controlsConstraint = Instance.new("UISizeConstraint")
	controlsConstraint.MinSize = Vector2.new(260, 100)
	controlsConstraint.MaxSize = Vector2.new(420, 100)
	controlsConstraint.Parent = controls

	local track = Instance.new("Frame")
	track.Size = UDim2.new(1, 0, 0, 4)
	track.BackgroundColor3 = UITheme.RaisedColor
	track.BorderSizePixel = 0
	track.Parent = controls
	UITheme.corner(track, UDim.new(0, 2))

	progressFill = Instance.new("Frame")
	progressFill.Size = UDim2.fromScale(0, 1)
	progressFill.BackgroundColor3 = UITheme.AccentGold
	progressFill.BorderSizePixel = 0
	progressFill.Parent = track
	UITheme.corner(progressFill, UDim.new(0, 2))

	statusLabel = UIKit.label(controls, "Building the Crossroads…", 13, "MUTED")
	statusLabel.Position = UDim2.fromOffset(0, 12)
	statusLabel.Size = UDim2.new(1, 0, 0, 18)
	statusLabel.TextXAlignment = Enum.TextXAlignment.Center

	playButton = UIKit.button(controls, "PLAY", "PRIMARY", function()
		if ready then
			finish()
		end
	end)
	playButton.Position = UDim2.fromOffset(0, 44)
	playButton.Size = UDim2.new(1, 0, 0, 48)
	playButton.TextSize = 20
	UIKit.setEnabled(playButton, false)

	-- PLAY IS THE ONLY BUTTON. Owner-directed 2026-09-20: an EXIT that can
	-- only kick you back to the app's home screen is a button whose best
	-- outcome is leaving, and a title screen offering one thing is a
	-- stronger screen than one offering a choice nobody wants to make.
	-- If anything ever joins it here, it should be something a player
	-- arrives WANTING -- not a way out.
end

function LoadingScreen.init(): ()
	if not GameConfig.Loading.Enabled then
		finished = true
		return
	end

	startedAt = os.clock()
	camera = Workspace.CurrentCamera
	-- FieldOfView IS worth keeping: it is a real value set by the place, not
	-- a placeholder from before the camera system started. CameraType is
	-- deliberately not saved -- see releaseCamera.
	savedFieldOfView = camera.FieldOfView

	build()

	camera.CameraType = Enum.CameraType.Scriptable
	camera.FieldOfView = GameConfig.Loading.FieldOfView

	-- The blur is what turns hub geometry into a backdrop. It is a Lighting
	-- effect the client owns and destroys, never a server one -- the same
	-- rule biome lighting follows (Biome Blueprint §6).
	local effect = Instance.new("BlurEffect")
	effect.Size = GameConfig.Loading.BlurSize
	effect.Parent = Lighting
	blur = effect

	if player.Character then
		task.spawn(holdCharacter, player.Character)
	end
	player.CharacterAdded:Connect(holdCharacter)

	task.spawn(runTour)
	task.spawn(watchProgress)
end

return LoadingScreen
