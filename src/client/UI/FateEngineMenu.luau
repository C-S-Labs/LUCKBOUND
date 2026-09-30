--!strict
-- THE FATE ENGINE MENU (SIGIL): the main menu. Opens anywhere in the
-- Crossroads from the emblem (bottom-right) or GameConfig.HubMenu.FateEngineHotkey.
--
-- HUB state: the Engine at the centre, every menu except Codes and Settings
-- (those live in the universal menu) orbiting it.
-- ROLL state: pressing the core condenses the outer sigil and expands the
-- inner one, where the roll happens. FATE decides the biome (modifiers are not
-- implemented yet); the player never picks a destination.
--
-- OPENING builds the sigil in stages: each layer rises from below and settles
-- outward, then paths draw from the core to each entry and the labels arrive.
-- CLOSING plays the same thing in reverse.
--
-- Rolling is still proximity-gated: the server validates distance
-- (build spec §3.4) and loosening that is a spec amendment, not a UI change.

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local ProximityController = require(script.Parent.Parent.Controllers.ProximityController)
local HubMenu = require(script.Parent.HubMenu)
local Sigil = require(script.Parent.Sigil.Sigil)
local Style = require(script.Parent.Sigil.SigilStyle)

local FateEngineMenu = {}

-- Orbiting entries. Panel ids are HubMenu's; Archive has no panel yet.
local NODES = {
	{ text = "Fate Tree", panel = "SKILLS", ticks = 72, squares = 5 },
	{ text = "Rebirth", panel = "REBIRTH", ticks = 54, squares = 3 },
	{ text = "Shop", panel = "SHOP", ticks = 60, squares = 4 },
	{ text = "Archive", panel = nil, ticks = 48, squares = 4 },
	{ text = "Party", panel = "PARTY", ticks = 66, squares = 6 },
}
local SCENE = 620
-- CanvasGroups clip to their bounds, so each group is PAD times larger than
-- the sigil drawn inside it.
local PAD = 1.16
local NODE_RADIUS = 0.36
-- Paths run from the core ring's edge to just short of each entry, so they never
-- cross the centre text.
local CORE_RADIUS = 0.12
local PATH_GAP = 0.04
local PATH_LENGTH = NODE_RADIUS - CORE_RADIUS - PATH_GAP
local PATH_MID = CORE_RADIUS + PATH_LENGTH / 2
-- Seconds: one layer's rise, the gap between layers, and the close pace.
local RISE = 0.8
local STAGGER = 0.16
local CLOSE_TOTAL = 1.1
-- Hover/press colour changes: eased, never stepped.
local HOVER = TweenInfo.new(0.28, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)

local gui: ScreenGui
local menuOpen = false
local closing = false
local content: Frame? = nil
local teardown: (() -> ())? = nil

local function tw(
	inst: Instance,
	seconds: number,
	props: { [string]: any },
	delay: number?,
	style: Enum.EasingStyle?
): Tween
	local t = TweenService:Create(
		inst,
		TweenInfo.new(seconds, style or Style.Ease, Enum.EasingDirection.Out, 0, false, delay or 0),
		props
	)
	t:Play()
	return t
end

local function text(
	parent: Instance,
	str: string,
	size: number,
	color: Color3,
	font: Enum.Font
): TextLabel
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Text = str
	l.TextSize = size
	l.TextColor3 = color
	l.Font = font
	l.Parent = parent
	return l
end

local function square(
	parent: Instance,
	size: number,
	rotation: number,
	tone: string,
	transparency: number
)
	local sq = Instance.new("Frame")
	sq.BackgroundTransparency = 1
	sq.AnchorPoint = Vector2.new(0.5, 0.5)
	sq.Position = UDim2.fromScale(0.5, 0.5)
	sq.Size = UDim2.fromScale(size, size)
	sq.Rotation = rotation
	sq.Parent = parent
	local st = Instance.new("UIStroke")
	st.Color = Style.tone(tone)
	st.Transparency = transparency
	st.Parent = sq
end

local function open()
	if menuOpen then
		return
	end
	menuOpen = true
	closing = false

	local root = Instance.new("Frame")
	root.Name = "FateEngineMenu"
	root.Size = UDim2.fromScale(1, 1)
	root.BackgroundColor3 = Style.Void
	root.BackgroundTransparency = 1
	root.BorderSizePixel = 0
	root.Parent = gui
	content = root
	tw(root, 0.6, { BackgroundTransparency = 0.3 })

	-- Header sits in a group so the whole thing fades as one.
	local headerGroup = Instance.new("CanvasGroup")
	headerGroup.BackgroundTransparency = 1
	headerGroup.Position = UDim2.new(0, 60, 0, 30)
	headerGroup.Size = UDim2.new(1, -120, 0, 84)
	headerGroup.GroupTransparency = 1
	headerGroup.Parent = root
	local header = Sigil.header(headerGroup, {
		title = "Fate Engine",
		label = "Fate interface",
		tone = "fate",
		onClose = FateEngineMenu.close,
	})
	header.Size = UDim2.fromScale(1, 1)
	tw(headerGroup, 0.7, { GroupTransparency = 0 }, 0.2)

	local scene = Instance.new("Frame")
	scene.BackgroundTransparency = 1
	scene.AnchorPoint = Vector2.new(0.5, 0.5)
	scene.Position = UDim2.fromScale(0.5, 0.5)
	scene.Size = UDim2.fromOffset(SCENE, SCENE)
	scene.Parent = root

	local function sz(size: number): UDim2
		return UDim2.fromScale(size * PAD, size * PAD)
	end
	local function group(parent: Instance, size: number): (CanvasGroup, Frame)
		local g = Instance.new("CanvasGroup")
		g.BackgroundTransparency = 1
		g.AnchorPoint = Vector2.new(0.5, 0.5)
		g.Position = UDim2.fromScale(0.5, 0.5)
		g.Size = sz(size)
		g.Parent = parent
		local space = Instance.new("Frame")
		space.BackgroundTransparency = 1
		space.AnchorPoint = Vector2.new(0.5, 0.5)
		space.Position = UDim2.fromScale(0.5, 0.5)
		space.Size = UDim2.fromScale(1 / PAD, 1 / PAD)
		space.Parent = g
		return g, space
	end

	-- OUTER SIGIL, in four layers so it can assemble one after another.
	local outerRoot = Instance.new("Frame")
	outerRoot.BackgroundTransparency = 1
	outerRoot.AnchorPoint = Vector2.new(0.5, 0.5)
	outerRoot.Position = UDim2.fromScale(0.5, 0.5)
	outerRoot.Size = UDim2.fromScale(1, 1)
	outerRoot.Parent = scene

	local g1, s1 = group(outerRoot, 1) -- outer rings and ticks
	Sigil.ring(s1, UDim2.fromScale(1, 1), "system", 1, 0.5)
	Sigil.ring(s1, UDim2.fromScale(0.96, 0.96), "system", 1, 0.85)
	Sigil.spin(Sigil.orbit(s1, 96, "fate", 7, 24), 4)

	local g2, s2 = group(outerRoot, 1) -- middle ring
	local mid = Instance.new("Frame")
	mid.BackgroundTransparency = 1
	mid.AnchorPoint = Vector2.new(0.5, 0.5)
	mid.Position = UDim2.fromScale(0.5, 0.5)
	mid.Size = UDim2.fromScale(NODE_RADIUS * 2, NODE_RADIUS * 2)
	mid.Parent = s2
	Sigil.ring(mid, UDim2.fromScale(1, 1), "fate", 1, 0.35)
	Sigil.spin(Sigil.orbit(mid, 48, "system", 5, 12), -7)
	Sigil.ring(s2, UDim2.fromScale(0.5, 0.5), "system", 1, 0.6)

	local g3, s3 = group(outerRoot, 1) -- fanned squares and the core ring
	-- Two counter-rotating fans plus a small orbit of diamonds, so the centre
	-- is always moving. Every layer turns at its own rate.
	local function holder(size: number): Frame
		local h = Instance.new("Frame")
		h.BackgroundTransparency = 1
		h.AnchorPoint = Vector2.new(0.5, 0.5)
		h.Position = UDim2.fromScale(0.5, 0.5)
		h.Size = UDim2.fromScale(size, size)
		h.Parent = s3
		return h
	end
	local fanA = holder(0.36)
	local fanB = holder(0.3)
	for k = 0, 3 do
		square(fanA, 1, k * 22.5, "fate", 0.7)
		square(fanB, 1, k * 22.5 + 11, "system", 0.75)
	end
	Sigil.spin(fanA, 7)
	Sigil.spin(fanB, -11)
	local satellites = holder(0.44)
	Sigil.ring(satellites, UDim2.fromScale(1, 1), "fate", 1, 0.8)
	Sigil.spin(Sigil.orbit(satellites, 3, "fate", 4, 1), 22)
	Sigil.ring(s3, UDim2.fromScale(0.24, 0.24), "fate", 2, 0.15)

	local g4, s4 = group(outerRoot, 1) -- paths and entry nodes
	local stages = { g1, g2, g3, g4 }

	-- Status line under the scene (hints, "not built yet", roll notes).
	local readout = text(scene, "", 20, Style.TextMuted, Style.Fonts.Label)
	readout.AnchorPoint = Vector2.new(0.5, 0)
	readout.Position = UDim2.new(0.5, 0, 1, 6)
	readout.Size = UDim2.fromOffset(SCENE, 26)

	local enterSub: ((any, number) -> ())? = nil
	local labels: { TextLabel } = {}
	local hits: { TextButton } = {}
	local paths: { Frame } = {}
	local pathMid: { UDim2 } = {}
	for i, node in NODES do
		local deg = (i - 1) * 360 / #NODES - 90
		local a = math.rad(deg)

		-- The path from the core out to this entry: drawn, not faded.
		local path = Instance.new("Frame")
		path.BorderSizePixel = 0
		path.BackgroundColor3 = Style.tone("fate")
		path.BackgroundTransparency = 0.5
		-- Rotation pivots on the frame's centre, so the path is centred on the
		-- midpoint between core and entry and grows from the core outward.
		path.AnchorPoint = Vector2.new(0.5, 0.5)
		path.Position = UDim2.fromScale(0.5, 0.5)
		pathMid[i] = UDim2.fromScale(0.5 + PATH_MID * math.cos(a), 0.5 + PATH_MID * math.sin(a))
		path.Rotation = deg
		path.Size = UDim2.new(0, 0, 0, 1)
		path.Parent = s4
		paths[i] = path

		local hit = Instance.new("TextButton")
		hit.BackgroundTransparency = 1
		hit.Text = ""
		hit.AnchorPoint = Vector2.new(0.5, 0.5)
		hit.Position =
			UDim2.fromScale(0.5 + NODE_RADIUS * math.cos(a), 0.5 + NODE_RADIUS * math.sin(a))
		hit.Size = UDim2.fromOffset(46, 46)
		hit.Parent = s4
		local d = Sigil.diamond(hit, 12, "fate", UDim2.fromScale(0.5, 0.5))
		Sigil.ring(hit, UDim2.fromScale(1, 1), "fate", 1, 0.5)

		local l = text(scene, string.upper(node.text), 20, Style.TextHigh, Style.Fonts.Label)
		l.AnchorPoint = Vector2.new(0.5, 0.5)
		l.Position = UDim2.new(0.5 + 0.5 * math.cos(a), 0, 0.5 + 0.5 * math.sin(a), 0)
		l.Size = UDim2.fromOffset(160, 26)
		l.TextTransparency = 1
		labels[i] = l
		hits[i] = hit

		-- Each entry breathes: a ring leaves it every few seconds, staggered so
		-- the set never pulses in unison.
		task.spawn(function()
			task.wait(1.5 + i * 0.5)
			while root.Parent do
				if hit.Active and hit.Parent then
					local p = Sigil.ring(hit, UDim2.fromScale(1, 1), "fate", 1, 0.4)
					tw(p, 1.8, { Size = UDim2.fromScale(1.9, 1.9) }, 0, Enum.EasingStyle.Sine)
					tw(p.UIStroke, 1.8, { Transparency = 1 }, 0, Enum.EasingStyle.Sine)
					task.delay(1.9, function()
						p:Destroy()
					end)
				end
				task.wait(3.2)
			end
		end)

		hit.MouseEnter:Connect(function()
			-- The path to the hovered entry lights; the others dim back.
			for n, other in paths do
				tw(
					other,
					0.3,
					{ BackgroundTransparency = if n == i then 0.05 else 0.8 },
					0,
					Enum.EasingStyle.Sine
				)
			end
			tw(d, 0.28, { Size = UDim2.fromOffset(17, 17) }, 0, Enum.EasingStyle.Sine)
			TweenService:Create(l, HOVER, { TextColor3 = Style.tone("fate") }):Play()
		end)
		hit.MouseLeave:Connect(function()
			for _, other in paths do
				tw(other, 0.4, { BackgroundTransparency = 0.5 }, 0, Enum.EasingStyle.Sine)
			end
			tw(d, 0.28, { Size = UDim2.fromOffset(12, 12) }, 0, Enum.EasingStyle.Sine)
			TweenService:Create(l, HOVER, { TextColor3 = Style.TextHigh }):Play()
		end)
		hit.MouseButton1Down:Connect(function()
			TweenService:Create(l, HOVER, { TextColor3 = Style.tone("system") }):Play()
		end)
		hit.Activated:Connect(function()
			if node.panel then
				if enterSub then
					enterSub(node, i)
				end
			else
				readout.Text = node.text .. " is not built yet."
			end
		end)
	end

	-- INNER SIGIL (roll state): collapsed and invisible until the core is pressed.
	local inner, spaceI = group(scene, 0.3)
	inner.GroupTransparency = 1
	inner.Visible = false
	Sigil.ring(spaceI, UDim2.fromScale(1, 1), "fate", 2, 0.2)
	Sigil.ring(spaceI, UDim2.fromScale(0.9, 0.9), "system", 1, 0.6)
	Sigil.spin(Sigil.orbit(spaceI, 60, "fate", 6, 10), 9)
	local rune = Instance.new("Frame")
	rune.BackgroundTransparency = 1
	rune.AnchorPoint = Vector2.new(0.5, 0.5)
	rune.Position = UDim2.fromScale(0.5, 0.5)
	rune.Size = UDim2.fromScale(0.72, 0.72)
	rune.Parent = spaceI
	Sigil.ring(rune, UDim2.fromScale(1, 1), "system", 1, 0.4)
	Sigil.spin(Sigil.orbit(rune, 24, "system", 8, 6), -14)
	for k = 0, 5 do
		square(rune, 0.5, k * 15, if k % 2 == 0 then "fate" else "system", 0.6)
	end
	Sigil.ring(spaceI, UDim2.fromScale(0.3, 0.3), "fate", 2, 0.1)
	local core = text(spaceI, "ROLL\nFATE", 22, Style.tone("fate"), Style.Fonts.Display)
	core.Size = UDim2.fromScale(0.3, 0.3)
	core.Position = UDim2.fromScale(0.35, 0.35)

	local biome = text(scene, "BIOME  -  decided by Fate", 20, Style.TextHigh, Style.Fonts.Label)
	biome.Position = UDim2.new(0.5, -240, 1, 4)
	biome.Size = UDim2.fromOffset(480, 26)
	biome.TextTransparency = 1
	local mods =
		text(scene, "MODIFIERS  -  not yet available", 18, Style.TextMuted, Style.Fonts.Label)
	mods.Position = UDim2.new(0.5, -240, 1, 34)
	mods.Size = UDim2.fromOffset(480, 24)
	mods.TextTransparency = 1

	-- Return sits directly under the sigil's readouts, where the eye already is.
	local returnGroup = Instance.new("CanvasGroup")
	returnGroup.BackgroundTransparency = 1
	returnGroup.Position = UDim2.new(0.5, -95, 1, 70)
	returnGroup.Size = UDim2.fromOffset(190, 46)
	returnGroup.GroupTransparency = 1
	returnGroup.Visible = false
	returnGroup.Parent = scene
	local back = Sigil.button(
		returnGroup,
		{ text = "Return", tone = "system", size = UDim2.fromScale(1, 1) }
	)

	-- The core's word, inside the ring, breathing. It stands in for a prompt.
	local hint = text(scene, "FATE\nENGINE", 19, Style.tone("fate"), Style.Fonts.Display)
	hint.AnchorPoint = Vector2.new(0.5, 0.5)
	hint.Position = UDim2.fromScale(0.5, 0.5)
	hint.Size = UDim2.fromOffset(138, 138)
	hint.BackgroundColor3 = Style.Void
	hint.BackgroundTransparency = 1
	hint.TextTransparency = 1
	local disc = Instance.new("UICorner")
	disc.CornerRadius = UDim.new(1, 0)
	disc.Parent = hint
	-- The word shimmers between gold and pale, slowly, so the centre reads as live.
	local shimmer = TweenService:Create(
		hint,
		TweenInfo.new(2.2, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{
			TextColor3 = Color3.fromRGB(255, 240, 204),
		}
	)
	shimmer:Play()
	task.spawn(function()
		-- Pulse rings leave the core every couple of seconds while the hub
		-- state is showing.
		task.wait(1.6)
		while root.Parent do
			if hint.Visible and hint.TextTransparency < 0.9 then
				local p = Sigil.ring(s3, UDim2.fromScale(0.24, 0.24), "fate", 2, 0.3)
				tw(p, 2.2, { Size = UDim2.fromScale(0.62, 0.62) }, 0, Enum.EasingStyle.Sine)
				tw(p.UIStroke, 2.2, { Transparency = 1 }, 0, Enum.EasingStyle.Sine)
				task.delay(2.3, function()
					p:Destroy()
				end)
			end
			task.wait(2.4)
		end
	end)

	-- ASSEMBLY. Layers start low and small, then rise into place one after
	-- another; paths draw outward; labels arrive last. `on = false` reverses it.
	local low = UDim2.fromScale(0.5, 0.64)
	local function play(on: boolean)
		local n = #stages
		for i, g in stages do
			local delay = if on then (i - 1) * STAGGER else (n - i) * 0.1
			tw(g, if on then RISE else 0.55, {
				GroupTransparency = if on then 0 else 1,
				Position = if on then UDim2.fromScale(0.5, 0.5) else low,
				Size = if on then sz(1) else sz(0.7),
			}, delay)
		end
		for i, path in paths do
			local delay = if on then 0.55 + i * 0.07 else 0
			tw(path, if on then 0.6 else 0.3, {
				Size = if on then UDim2.new(PATH_LENGTH, 0, 0, 1) else UDim2.new(0, 0, 0, 1),
				Position = if on
					then pathMid[i]
					else UDim2.fromScale(
						0.5 + CORE_RADIUS * math.cos(math.rad((i - 1) * 360 / #NODES - 90)),
						0.5 + CORE_RADIUS * math.sin(math.rad((i - 1) * 360 / #NODES - 90))
					),
			}, delay)
		end
		for i, l in labels do
			local delay = if on then 0.8 + i * 0.07 else 0
			tw(
				l,
				if on then 0.45 else 0.25,
				{ TextTransparency = if on then 0 else 1 },
				delay,
				Enum.EasingStyle.Sine
			)
		end
		tw(hint, 0.5, {
			TextTransparency = if on then 0 else 1,
			BackgroundTransparency = if on then 0.25 else 1,
		}, if on then 1.2 else 0, Enum.EasingStyle.Sine)
	end
	for _, g in stages do
		g.GroupTransparency = 1
		g.Position = low
		g.Size = sz(0.7)
	end
	play(true)

	-- Shared by the roll state and every sub-sigil: the hub sigil condenses to
	-- its core (labels, paths and entries fade), or springs back.
	local function condense(on: boolean)
		returnGroup.Visible = true
		tw(
			returnGroup,
			0.5,
			{ GroupTransparency = if on then 0 else 1 },
			if on then 0.6 else 0,
			Enum.EasingStyle.Sine
		)
		if not on then
			task.delay(0.5, function()
				if returnGroup.Parent and returnGroup.GroupTransparency >= 0.99 then
					returnGroup.Visible = false
				end
			end)
		end
		for _, h in hits do
			h.Active = not on
		end
		tw(hint, 0.4, {
			TextTransparency = if on then 1 else 0,
			BackgroundTransparency = if on then 1 else 0.25,
		}, 0, Enum.EasingStyle.Sine)
		readout.Text = ""
		tw(
			outerRoot,
			1.0,
			{ Size = if on then UDim2.fromScale(0.5, 0.5) else UDim2.fromScale(1, 1) }
		)
		for _, g in stages do
			tw(g, 0.8, { GroupTransparency = if on then 0.8 else 0 })
		end
		for _, l in labels do
			tw(l, 0.5, { TextTransparency = if on then 1 else 0 }, 0, Enum.EasingStyle.Sine)
		end
		for _, p in paths do
			tw(p, 0.6, { BackgroundTransparency = if on then 1 else 0.5 })
		end
	end

	local function setRoll(on: boolean)
		condense(on)
		for _, l in ipairs({ biome, mods }) do
			tw(
				l,
				0.5,
				{ TextTransparency = if on then 0 else 1 },
				if on then 0.7 else 0,
				Enum.EasingStyle.Sine
			)
		end
		if on then
			inner.Visible = true
			tw(inner, 1.0, { Size = sz(0.95), GroupTransparency = 0 }, 0.15)
		else
			tw(inner, 0.8, { Size = sz(0.3), GroupTransparency = 1 })
		end
	end

	-- Two invisible hit areas share the centre: one opens the roll state, the
	-- other (only live in it) rolls.
	local function centreButton(): TextButton
		local b = Instance.new("TextButton")
		b.BackgroundTransparency = 1
		b.Text = ""
		b.AnchorPoint = Vector2.new(0.5, 0.5)
		b.Position = UDim2.fromScale(0.5, 0.5)
		b.Size = UDim2.fromOffset(120, 120)
		b.ZIndex = 5
		b.Parent = scene
		return b
	end
	local openRoll = centreButton()
	local doRoll = centreButton()
	doRoll.Visible = false

	-- SUB-SIGILS. An entry condenses the hub sigil to its core, then a sigil of
	-- its own expands with that entry's panel drawn inside the ring. The panel
	-- content is HubMenu's (re-parented), so real content lands with the
	-- system, not with this menu.
	local subGroup: CanvasGroup? = nil
	local subHost: Frame? = nil
	local inSub = false

	enterSub = function(node: any, index: number)
		if inSub then
			return
		end
		inSub = true
		openRoll.Visible = false
		condense(true)

		local g, sp = group(scene, 0.4)
		g.GroupTransparency = 1
		subGroup = g
		Sigil.ring(sp, UDim2.fromScale(1, 1), "fate", 2, 0.2)
		Sigil.ring(sp, UDim2.fromScale(0.94, 0.94), "system", 1, 0.6)
		local dir = if index % 2 == 0 then -1 else 1
		Sigil.spin(Sigil.orbit(sp, node.ticks, "fate", 6, node.ticks // 6), 5 * dir)
		local h = Instance.new("Frame")
		h.BackgroundTransparency = 1
		h.AnchorPoint = Vector2.new(0.5, 0.5)
		h.Position = UDim2.fromScale(0.5, 0.5)
		h.Size = UDim2.fromScale(0.9, 0.9)
		h.Parent = sp
		for k = 0, node.squares - 1 do
			square(h, 1, k * (90 / node.squares), if k % 2 == 0 then "fate" else "system", 0.82)
		end
		Sigil.spin(h, -4 * dir)
		tw(g, 1.0, { Size = sz(1), GroupTransparency = 0 }, 0.15)

		local host = Instance.new("Frame")
		host.BackgroundTransparency = 1
		host.AnchorPoint = Vector2.new(0.5, 0.5)
		host.Position = UDim2.fromScale(0.5, 0.5)
		host.Size = UDim2.fromOffset(440, 360)
		host.Parent = scene
		subHost = host
		task.delay(0.8, function()
			if inSub and host.Parent then
				HubMenu.openIn(node.panel, host)
			end
		end)
	end

	local function leaveSub()
		if not inSub then
			return
		end
		inSub = false
		HubMenu.release()
		local g = subGroup
		if g then
			tw(g, 0.8, { Size = sz(0.4), GroupTransparency = 1 })
			task.delay(0.9, function()
				g:Destroy()
			end)
			subGroup = nil
		end
		if subHost then
			subHost:Destroy()
			subHost = nil
		end
		condense(false)
		openRoll.Visible = true
	end

	openRoll.Activated:Connect(function()
		openRoll.Visible = false
		doRoll.Visible = true
		setRoll(true)
	end)
	back.Activated:Connect(function()
		if inSub then
			leaveSub()
			return
		end
		openRoll.Visible = true
		doRoll.Visible = false
		setRoll(false)
	end)
	-- Hover pauses the shimmer and eases the word to cyan; leaving eases it back
	-- to gold and resumes.
	openRoll.MouseEnter:Connect(function()
		shimmer:Cancel()
		TweenService:Create(hint, HOVER, { TextColor3 = Style.tone("system") }):Play()
	end)
	openRoll.MouseLeave:Connect(function()
		local settle = TweenService:Create(hint, HOVER, { TextColor3 = Style.tone("fate") })
		settle:Play()
		settle.Completed:Once(function()
			if hint.Parent and openRoll.Visible then
				shimmer:Play()
			end
		end)
	end)
	openRoll.MouseButton1Down:Connect(function()
		TweenService:Create(hint, HOVER, { TextColor3 = Style.TextHigh }):Play()
	end)
	doRoll.MouseEnter:Connect(function()
		TweenService:Create(core, HOVER, { TextColor3 = Style.tone("system") }):Play()
	end)
	doRoll.MouseLeave:Connect(function()
		TweenService:Create(core, HOVER, { TextColor3 = Style.tone("fate") }):Play()
	end)
	doRoll.MouseButton1Down:Connect(function()
		TweenService:Create(core, HOVER, { TextColor3 = Style.TextHigh }):Play()
	end)
	doRoll.Activated:Connect(function()
		if ProximityController.isInRange() then
			ProximityController.requestRoll()
			FateEngineMenu.close()
		else
			biome.Text = "Approach the Fate Engine to roll."
		end
	end)

	-- CLOSING: the assembly in reverse, then the menu is removed.
	teardown = function()
		HubMenu.release()
		if subGroup then
			tw(subGroup, 0.6, { GroupTransparency = 1 })
		end
		play(false)
		tw(inner, 0.6, { Size = sz(0.3), GroupTransparency = 1 })
		for _, l in ipairs({ biome, mods, readout }) do
			tw(l, 0.3, { TextTransparency = 1 })
		end
		tw(returnGroup, 0.3, { GroupTransparency = 1 })
		tw(headerGroup, 0.6, { GroupTransparency = 1 }, 0.3)
		tw(root, 0.6, { BackgroundTransparency = 1 }, 0.5)
		task.delay(CLOSE_TOTAL, function()
			root:Destroy()
			if content == root then
				content = nil
			end
			menuOpen = false
			closing = false
		end)
	end
end

function FateEngineMenu.close(): ()
	if not menuOpen or closing then
		return
	end
	closing = true
	if teardown then
		teardown()
		teardown = nil
	end
end

function FateEngineMenu.init(): ()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundFateEngineMenu"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = 8
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	HubMenu.follow(gui)

	local function toggle()
		if closing then
			return
		end
		if menuOpen then
			FateEngineMenu.close()
		else
			open()
		end
	end

	-- The always-available entry: a small orbiting emblem, bottom-right, with a
	-- name that slides out from behind it on hover.
	local dock = Instance.new("Frame")
	dock.Name = "FateEngineDock"
	dock.AnchorPoint = Vector2.new(1, 1)
	dock.Position = UDim2.new(1, -24, 1, -24)
	dock.Size = UDim2.fromOffset(280, 64)
	dock.BackgroundTransparency = 1
	dock.Parent = gui

	-- Clipped strip: its width grows leftward from the emblem, revealing the label.
	local strip = Instance.new("Frame")
	strip.AnchorPoint = Vector2.new(1, 0.5)
	strip.Position = UDim2.new(1, -56, 0.5, 0)
	strip.Size = UDim2.fromOffset(0, 48)
	strip.BackgroundColor3 = Style.Void
	strip.BackgroundTransparency = 0.25
	strip.BorderSizePixel = 0
	strip.ClipsDescendants = true
	strip.Parent = dock
	local edge = Instance.new("Frame")
	edge.AnchorPoint = Vector2.new(1, 0.5)
	edge.Position = UDim2.fromScale(1, 0.5)
	edge.Size = UDim2.new(0, 2, 1, 0)
	edge.BackgroundColor3 = Style.tone("fate")
	edge.BorderSizePixel = 0
	edge.Parent = strip
	local tag = text(strip, "FATE ENGINE", 16, Style.TextHigh, Style.Fonts.Label)
	tag.AnchorPoint = Vector2.new(1, 0.5)
	tag.Position = UDim2.new(1, 24, 0, 16)
	tag.Size = UDim2.fromOffset(150, 22)
	tag.TextXAlignment = Enum.TextXAlignment.Right
	tag.TextTransparency = 1
	-- The shortcut, small, under the name.
	local keyTag = text(
		strip,
		"PRESS " .. GameConfig.HubMenu.FateEngineHotkey .. " ANYWHERE",
		12,
		Style.TextMuted,
		Style.Fonts.Label
	)
	keyTag.AnchorPoint = Vector2.new(1, 0.5)
	keyTag.Position = UDim2.new(1, 24, 0, 35)
	keyTag.Size = UDim2.fromOffset(150, 14)
	keyTag.TextXAlignment = Enum.TextXAlignment.Right
	keyTag.TextTransparency = 1

	local emblem = Instance.new("TextButton")
	emblem.Name = "FateEngineEmblem"
	emblem.AnchorPoint = Vector2.new(1, 0.5)
	emblem.Position = UDim2.fromScale(1, 0.5)
	emblem.Size = UDim2.fromOffset(64, 64)
	emblem.BackgroundTransparency = 1
	emblem.Text = ""
	emblem.AutoButtonColor = false
	emblem.Parent = dock
	local ring = Sigil.ring(emblem, UDim2.fromScale(1, 1), "fate", 1, 0.35)
	local ringStroke: UIStroke = ring.UIStroke
	Sigil.ring(emblem, UDim2.fromScale(0.66, 0.66), "system", 1, 0.55)
	Sigil.spin(Sigil.orbit(emblem, 24, "fate", 4, 6), 10)
	Sigil.diamond(emblem, 8, "fate", UDim2.fromScale(0.5, 0.5))

	emblem.MouseEnter:Connect(function()
		tw(ringStroke, 0.35, { Transparency = 0, Thickness = 2 }, 0, Enum.EasingStyle.Sine)
		tw(strip, 0.45, { Size = UDim2.fromOffset(170, 48) })
		tw(tag, 0.45, { TextTransparency = 0, Position = UDim2.new(1, -14, 0, 16) }, 0.1)
		tw(keyTag, 0.45, { TextTransparency = 0, Position = UDim2.new(1, -14, 0, 35) }, 0.2)
	end)
	emblem.MouseLeave:Connect(function()
		tw(ringStroke, 0.35, { Transparency = 0.35, Thickness = 1 }, 0, Enum.EasingStyle.Sine)
		tw(tag, 0.25, { TextTransparency = 1, Position = UDim2.new(1, 24, 0, 16) })
		tw(keyTag, 0.25, { TextTransparency = 1, Position = UDim2.new(1, 24, 0, 35) })
		tw(strip, 0.35, { Size = UDim2.fromOffset(0, 48) }, 0.05)
	end)
	emblem.Activated:Connect(toggle)

	local key = (Enum.KeyCode :: any)[GameConfig.HubMenu.FateEngineHotkey]
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.KeyCode == key then
			toggle()
		end
	end)
end

return FateEngineMenu
