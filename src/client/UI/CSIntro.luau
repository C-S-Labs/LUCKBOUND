--!strict
-- THE C&S LABS IDENT (prototype, isolated). Plays ONCE per fresh server join,
-- alongside real hub construction, never as a general loading screen. Not yet
-- wired to the loading flow: call CSIntro.play from the initial-join path when
-- the visuals are approved (see the callbacks on `play`).
--
-- The logo is ONE image (GameConfig.StudioIntro.LogoImageCandidates), shown as two
-- halves cropped at its vertical spine: the C is entirely left of it and the S
-- entirely right. The halves start apart and close together, reproducing the
-- supplied logo pixel for pixel. Nothing here redraws the C or the S.
--
-- Flow: pieces appear apart -> join -> pulse and a few sparks -> name appears
-- -> HOLD until `ready()` is true (never longer than needed, never an
-- unfinished hub) -> fade into the title screen, which carries BEGIN.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Sigil = require(script.Parent.Sigil.Sigil)
local Style = require(script.Parent.Sigil.SigilStyle)

local CSIntro = {}

local CONFIG = GameConfig.StudioIntro
local BLUE_WHITE = Color3.fromRGB(214, 238, 255)

local function tw(
	inst: Instance,
	seconds: number,
	props: { [string]: any },
	delay: number?,
	style: Enum.EasingStyle?,
	dir: Enum.EasingDirection?
): Tween
	local t = TweenService:Create(
		inst,
		TweenInfo.new(
			seconds,
			style or Enum.EasingStyle.Quint,
			dir or Enum.EasingDirection.Out,
			0,
			false,
			delay or 0
		),
		props
	)
	t:Play()
	return t
end

--- One half of the logo image: `right` false is the left half (the C).
local function half(parent: Instance, right: boolean): ImageLabel
	local px = CONFIG.LogoImagePx
	local p = Instance.new("ImageLabel")
	p.Name = if right then "S" else "C"
	p.BackgroundTransparency = 1
	p.Image = ""
	p.ImageRectOffset = Vector2.new(if right then px / 2 else 0, 0)
	p.ImageRectSize = Vector2.new(px / 2, px)
	p.ImageTransparency = 1
	p.AnchorPoint = Vector2.new(0.5, 0.5)
	p.Size = UDim2.fromScale(0.5, 1)
	p.Parent = parent
	return p
end

--- Plays the ident. `options.ready()` reports whether initial hub construction
--- is finished (defaults to true, so the prototype never waits); `onDone` fires
--- when the title screen is fully up; `onBegin` when the player presses BEGIN.
function CSIntro.play(options: {
	ready: (() -> boolean)?,
	onDone: (() -> ())?,
	onBegin: (() -> ())?,
	ownTitle: boolean?,
}?)
	local opts = options or {}
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundStudioIntro"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 200
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

	local bg = Instance.new("Frame")
	bg.Size = UDim2.fromScale(1, 1)
	bg.BackgroundColor3 = Style.Void
	bg.BorderSizePixel = 0
	bg.Parent = gui

	-- Barely-there blue/violet light. A single circle fading in bands visibly on
	-- a dark screen, so the glow is many nearly invisible circles of shrinking
	-- size: each adds a step too small to see, together they read as one soft
	-- pool, and they arrive one after another so the fade is smooth.
	local GLOW_LAYERS = 26
	for i = 1, GLOW_LAYERS do
		local d = CONFIG.LogoSize * (2.9 - (i - 1) * 0.075)
		local layer = Instance.new("Frame")
		layer.AnchorPoint = Vector2.new(0.5, 0.5)
		layer.Position = UDim2.fromScale(0.5, 0.45)
		layer.Size = UDim2.fromOffset(d, d)
		layer.BackgroundColor3 = Color3.fromRGB(46, 40, 112)
		layer.BackgroundTransparency = 1
		layer.BorderSizePixel = 0
		layer.Parent = bg
		local round = Instance.new("UICorner")
		round.CornerRadius = UDim.new(1, 0)
		round.Parent = layer
		tw(layer, 2.4, { BackgroundTransparency = 0.978 }, i * 0.05, Enum.EasingStyle.Sine)
	end

	local stage = Instance.new("Frame")
	stage.BackgroundTransparency = 1
	stage.AnchorPoint = Vector2.new(0.5, 0.5)
	stage.Position = UDim2.fromScale(0.5, 0.45)
	stage.Size = UDim2.fromOffset(CONFIG.LogoSize, CONFIG.LogoSize)
	stage.Parent = bg

	local whole = CONFIG.Mode == "WHOLE"
	local c = half(stage, false)
	local s = half(stage, true)
	if whole then
		-- One piece: the left "half" becomes the entire image.
		c.ImageRectOffset = Vector2.zero
		c.ImageRectSize = Vector2.zero -- zero means the whole image, whatever its size
		c.Size = UDim2.fromScale(0.9, 0.9)
		s.Visible = false
	end
	local sep = CONFIG.SeparationPx
	local rot = CONFIG.StartRotationDegrees
	-- Start apart and slightly turned: C up-left, S down-right, then close in
	-- along the spine. Rest positions are the two halves' own centres.
	local restC = if whole then UDim2.fromScale(0.5, 0.5) else UDim2.fromScale(0.25, 0.5)
	local restS = UDim2.fromScale(0.75, 0.5)
	if whole then
		c.Position = restC
	else
		c.Position = restC + UDim2.fromOffset(-sep, -sep * 0.4)
		s.Position = restS + UDim2.fromOffset(sep, sep * 0.4)
	end
	if not whole then
		c.Rotation = -rot
		s.Rotation = rot
	end

	tw(c, CONFIG.AppearSeconds, { ImageTransparency = 0 }, CONFIG.AppearAt, Enum.EasingStyle.Sine)
	tw(
		s,
		CONFIG.AppearSeconds,
		{ ImageTransparency = 0 },
		CONFIG.AppearAt + 0.12,
		Enum.EasingStyle.Sine
	)
	local joinC: Tween
	if whole then
		-- Fades in while easing up to full size; the lock effects fire when it lands.
		joinC = tw(
			c,
			CONFIG.AppearSeconds + CONFIG.JoinSeconds,
			{ Size = UDim2.fromScale(1, 1) },
			CONFIG.AppearAt,
			Enum.EasingStyle.Quart,
			Enum.EasingDirection.Out
		)
	else
		joinC = tw(
			c,
			CONFIG.JoinSeconds,
			{ Position = restC, Rotation = 0 },
			CONFIG.JoinAt,
			Enum.EasingStyle.Quart,
			Enum.EasingDirection.InOut
		)
		tw(
			s,
			CONFIG.JoinSeconds,
			{ Position = restS, Rotation = 0 },
			CONFIG.JoinAt,
			Enum.EasingStyle.Quart,
			Enum.EasingDirection.InOut
		)
	end

	local name = Instance.new("TextLabel")
	name.BackgroundTransparency = 1
	name.Text = table.concat(string.split(CONFIG.Tagline, ""), "\u{200A}")
	name.Font = Style.Fonts.Display
	name.TextSize = 14
	name.TextColor3 = Style.TextHigh
	name.TextTransparency = 1
	name.AnchorPoint = Vector2.new(0.5, 0)
	name.Position = UDim2.new(0.5, 0, 1, 40)
	name.Size = UDim2.fromOffset(CONFIG.LogoSize * 2.4, 24)
	name.Parent = stage

	-- WHICH IMAGE LOADS. A decal id, its image id and its thumbnail are three
	-- different URLs, and only the owner's Studio can say which one Roblox will
	-- serve. Try each in order and report the winner (or all failures) so the
	-- Output window says exactly what is wrong.
	task.spawn(function()
		local ContentProvider = game:GetService("ContentProvider")
		for _, url in CONFIG.LogoImageCandidates do
			-- Not fully transparent: the engine does not load an image it will
			-- never draw, which would fail every candidate instantly.
			local probe = Instance.new("ImageLabel")
			probe.Image = url
			probe.Size = UDim2.fromOffset(32, 32)
			probe.BackgroundTransparency = 1
			probe.ImageTransparency = 0.98
			probe.Parent = gui
			local deadline = os.clock() + 5
			while not probe.IsLoaded and os.clock() < deadline do
				task.wait(0.1)
			end
			local ok = probe.IsLoaded
			local status = ContentProvider:GetAssetFetchStatus(url)
			probe:Destroy()
			print(
				string.format(
					"[CSIntro] logo image %s: %s (%s)",
					url,
					if ok then "loaded" else "FAILED",
					tostring(status)
				)
			)
			if ok then
				c.Image = url
				s.Image = url
				return
			end
		end
		warn(
			"[CSIntro] none of GameConfig.StudioIntro.LogoImageCandidates loaded; upload the image (not the decal) and use its id."
		)
	end)

	local finished = false
	local function finish()
		if finished then
			return
		end
		finished = true
		if not opts.ownTitle then
			-- Default: the logo and words leave FIRST, then the dark background
			-- dissolves to reveal whatever title is already beneath (the loading
			-- screen's own), so the two are never visible together.
			local out = CONFIG.FadeSeconds * 0.45
			local rest = CONFIG.FadeSeconds * 0.65
			local lag = CONFIG.FadeSeconds * 0.35
			tw(bg, rest, { BackgroundTransparency = 1 }, lag, Enum.EasingStyle.Sine)
			for _, d in bg:GetDescendants() do
				if d:IsA("ImageLabel") then
					tw(d, out, { ImageTransparency = 1 }, 0, Enum.EasingStyle.Sine)
				elseif d:IsA("TextLabel") then
					tw(d, out, { TextTransparency = 1 }, 0, Enum.EasingStyle.Sine)
				elseif d:IsA("Frame") then
					tw(d, out, { BackgroundTransparency = 1 }, 0, Enum.EasingStyle.Sine)
				end
			end
			task.delay(CONFIG.FadeSeconds, function()
				gui:Destroy()
				if opts.onDone then
					opts.onDone()
				end
			end)
			return
		end
		-- ownTitle: hand over to the prototype title screen while the ident dissolves.
		local title = Sigil.titleScreen(gui, {})
		title.root.BackgroundTransparency = 1
		local hidden: { GuiObject } = {}
		for _, d in title.root:GetDescendants() do
			if d:IsA("GuiObject") and d.Visible then
				d.Visible = false
				table.insert(hidden, d)
			end
		end
		tw(bg, CONFIG.FadeSeconds, { BackgroundTransparency = 1 }, 0, Enum.EasingStyle.Sine)
		for _, d in bg:GetDescendants() do
			if d:IsA("ImageLabel") then
				tw(d, CONFIG.FadeSeconds, { ImageTransparency = 1 }, 0, Enum.EasingStyle.Sine)
			elseif d:IsA("TextLabel") then
				tw(d, CONFIG.FadeSeconds, { TextTransparency = 1 }, 0, Enum.EasingStyle.Sine)
			elseif d:IsA("Frame") then
				tw(d, CONFIG.FadeSeconds, { BackgroundTransparency = 1 }, 0, Enum.EasingStyle.Sine)
			end
		end
		task.delay(CONFIG.FadeSeconds * 0.4, function()
			for _, d in hidden do
				d.Visible = true
			end
			tw(
				title.root,
				CONFIG.FadeSeconds,
				{ BackgroundTransparency = 0 },
				0,
				Enum.EasingStyle.Sine
			)
			Sigil.button(title.root, {
				text = "BEGIN",
				tone = "fate",
				size = UDim2.fromOffset(240, 52),
				anchor = Vector2.new(0.5, 0),
				position = UDim2.fromScale(0.5, 0.68),
				onClick = function()
					title.finish()
					if opts.onBegin then
						opts.onBegin()
					end
				end,
			})
		end)
		task.delay(CONFIG.FadeSeconds, function()
			bg:Destroy()
			if opts.onDone then
				opts.onDone()
			end
		end)
	end

	-- The moment they connect: a restrained blue-white pulse and a few sparks.
	joinC.Completed:Once(function()
		-- A hairline of light runs the spine where the halves met.
		local seam = Instance.new("Frame")
		seam.BorderSizePixel = 0
		seam.BackgroundColor3 = BLUE_WHITE
		seam.AnchorPoint = Vector2.new(0.5, 0.5)
		seam.Position = UDim2.fromScale(0.5, 0.5)
		seam.Size = UDim2.new(0, 2, 0, 0)
		seam.Parent = stage
		tw(seam, 0.5, { Size = UDim2.new(0, 2, 1, 0) }, 0, Enum.EasingStyle.Quad)
		tw(seam, 0.6, { BackgroundTransparency = 1 }, 0.45, Enum.EasingStyle.Sine)
		task.delay(1.2, function()
			seam:Destroy()
		end)
		local pulse = Sigil.ring(stage, UDim2.fromScale(0.55, 0.55), "system", 2, 0.2)
		pulse.UIStroke.Color = BLUE_WHITE
		tw(pulse, 0.9, { Size = UDim2.fromScale(1.35, 1.35) }, 0, Enum.EasingStyle.Sine)
		tw(pulse.UIStroke, 0.9, { Transparency = 1 }, 0, Enum.EasingStyle.Sine)
		task.delay(1, function()
			pulse:Destroy()
		end)
		local rng = Random.new()
		for i = 1, CONFIG.SparkCount do
			local a = (i / CONFIG.SparkCount) * math.pi * 2 + rng:NextNumber(-0.2, 0.2)
			local spark = Instance.new("Frame")
			spark.BorderSizePixel = 0
			spark.BackgroundColor3 = BLUE_WHITE
			spark.AnchorPoint = Vector2.new(0.5, 0.5)
			spark.Position = UDim2.fromScale(0.5, 0.5)
			spark.Size = UDim2.fromOffset(3, 3)
			spark.Rotation = 45
			spark.Parent = stage
			local r = CONFIG.LogoSize * rng:NextNumber(0.42, 0.62)
			tw(spark, 0.7, {
				Position = UDim2.new(0.5, math.cos(a) * r, 0.5, math.sin(a) * r),
				BackgroundTransparency = 1,
			}, 0, Enum.EasingStyle.Quad)
			task.delay(0.8, function()
				spark:Destroy()
			end)
		end
		-- The tagline: a hairline draws outward from the centre, then the words
		-- rise into place under it. (The image already spells LABS.)
		local rule = Instance.new("Frame")
		rule.BorderSizePixel = 0
		rule.BackgroundColor3 = Style.Violet
		rule.BackgroundTransparency = 0.3
		rule.AnchorPoint = Vector2.new(0.5, 0.5)
		rule.Position = UDim2.new(0.5, 0, 1, 20)
		rule.Size = UDim2.fromOffset(0, 1)
		rule.Parent = stage
		tw(
			rule,
			0.9,
			{ Size = UDim2.fromOffset(CONFIG.LogoSize * 1.9, 1) },
			0.1,
			Enum.EasingStyle.Quart
		)
		tw(
			name,
			0.9,
			{ TextTransparency = 0.05, Position = UDim2.new(0.5, 0, 1, 30) },
			0.5,
			Enum.EasingStyle.Quart
		)

		-- HOLD, then wait for the hub. Never stalls if it is already ready.
		task.delay(CONFIG.HoldSeconds, function()
			local ready = opts.ready
			while ready and not ready() do
				task.wait(0.1)
			end
			finish()
		end)
	end)
end

return CSIntro
