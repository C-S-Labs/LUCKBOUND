--!strict
-- SIGIL components (prototype): panel, button, tabs, notifier, tooltip, header,
-- Fate Engine, HUD, universal menu, title screen. Every colour comes from
-- SigilStyle and every component takes a config table, so screens compose these
-- instead of styling themselves. Shapes are constructed from thin lines, corner
-- brackets, diamonds and concentric rings rather than rounded rectangles.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Style = require(script.Parent.SigilStyle)

local Sigil = {}

local function mk(class: string, props: { [string]: any }, parent: Instance?): any
	local inst = Instance.new(class)
	for k, v in props do
		(inst :: any)[k] = v
	end
	inst.Parent = parent
	return inst
end

local function box(props: { [string]: any }, parent: Instance?): any
	local p = { BorderSizePixel = 0, BackgroundTransparency = 1 }
	for k, v in props do
		p[k] = v
	end
	return mk("Frame", p, parent)
end

local function tween(inst: Instance, dur: number, props: { [string]: any }, delay: number?): Tween
	local t = TweenService:Create(
		inst,
		TweenInfo.new(dur, Style.Ease, Enum.EasingDirection.Out, 0, false, delay or 0),
		props
	)
	t:Play()
	return t
end

--- Paints a property from a tone and keeps it in sync with Fate-state changes.
local function paint(inst: Instance, prop: string, tone: string)
	local function apply()
		(inst :: any)[prop] = Style.tone(tone)
	end
	apply()
	local c = Style.bind(apply)
	inst.Destroying:Once(function()
		c.Disconnect()
	end)
end

local function label(parent: Instance, cfg: { [string]: any }): TextLabel
	local l = mk("TextLabel", {
		BackgroundTransparency = 1,
		Text = cfg.text or "",
		Font = cfg.font or Style.Fonts.Body,
		TextSize = cfg.size or 14,
		TextColor3 = cfg.color or Style.TextHigh,
		TextXAlignment = cfg.align or Enum.TextXAlignment.Left,
		TextYAlignment = cfg.yalign or Enum.TextYAlignment.Center,
		TextWrapped = cfg.wrap or false,
		Size = cfg.sz or UDim2.fromScale(1, 1),
		Position = cfg.pos or UDim2.new(),
		AnchorPoint = cfg.anchor or Vector2.zero,
		RichText = false,
		AutomaticSize = cfg.auto or Enum.AutomaticSize.None,
	}, parent)
	if cfg.tone then
		paint(l, "TextColor3", cfg.tone)
	end
	return l
end

--- Small uppercase caption (WORLD VARIANT, RISK ...). Only for secondary info.
local function caption(
	parent: Instance,
	text: string,
	tone: string?,
	pos: UDim2?,
	sz: UDim2?
): TextLabel
	return label(parent, {
		text = string.upper(text),
		font = Style.Fonts.Label,
		size = 13,
		color = Style.TextMuted,
		tone = tone,
		pos = pos,
		sz = sz or UDim2.new(1, 0, 0, 14),
	})
end

--- A thin line that draws itself from its start edge. axis "x" or "y".
local function line(
	parent: Instance,
	props: { [string]: any },
	tone: string?,
	delay: number?,
	axis: string?
): any
	local f = box(props, parent)
	f.BackgroundTransparency = props.BackgroundTransparency or 0.3
	if tone then
		paint(f, "BackgroundColor3", tone)
	end
	local full: UDim2 = f.Size
	local from = if axis == "y"
		then UDim2.new(full.X.Scale, full.X.Offset, 0, 0)
		else UDim2.new(0, 0, full.Y.Scale, full.Y.Offset)
	f.Size = from
	tween(f, Style.Motion.Draw, { Size = full }, delay or 0)
	return f
end

local function fadeIn(l: TextLabel, delay: number)
	local target = l.TextTransparency
	l.TextTransparency = 1
	tween(l, Style.Motion.Normal, { TextTransparency = target }, delay)
end

-- ===================================================================
-- Rings and glyphs
-- ===================================================================

--- A circle outline (no fill). Radius is the size given, diameter in pixels or scale.
function Sigil.ring(
	parent: Instance,
	size: UDim2,
	tone: string,
	thickness: number?,
	transparency: number?
): any
	local r = box(
		{ AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = size },
		parent
	)
	mk("UICorner", { CornerRadius = UDim.new(1, 0) }, r)
	local s = mk("UIStroke", { Thickness = thickness or 1, Transparency = transparency or 0.5 }, r)
	paint(s, "Color", tone)
	return r
end

local function diamond(parent: Instance, px: number, tone: string, pos: UDim2): any
	local d = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = pos,
		Size = UDim2.fromOffset(px, px),
		Rotation = 45,
		BackgroundTransparency = 0,
	}, parent)
	paint(d, "BackgroundColor3", tone)
	return d
end

--- Ticks and diamonds spaced around a circle inside a square container.
local function orbit(
	parent: Instance,
	count: number,
	tone: string,
	tickLen: number,
	bigEvery: number
): any
	local o = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1, 1),
	}, parent)
	for i = 0, count - 1 do
		local a = math.rad(i * 360 / count)
		local pos = UDim2.fromScale(0.5 + 0.5 * math.sin(a), 0.5 - 0.5 * math.cos(a))
		if bigEvery > 0 and i % bigEvery == 0 then
			diamond(o, 5, tone, pos)
		else
			local t = box({
				AnchorPoint = Vector2.new(0.5, 0.5),
				Position = pos,
				Size = UDim2.fromOffset(1, tickLen),
				Rotation = i * 360 / count,
				BackgroundTransparency = 0.5,
			}, o)
			paint(t, "BackgroundColor3", tone)
		end
	end
	return o
end

--- Rotates `inst` at degrees/second (scaled by the live state's speed) until it is destroyed.
local function spin(inst: any, dps: number)
	local c = RunService.Heartbeat:Connect(function(dt)
		inst.Rotation = (inst.Rotation + dps * Style.accent().speed * dt) % 360
	end)
	inst.Destroying:Once(function()
		c:Disconnect()
	end)
end

-- ===================================================================
-- Panel
-- ===================================================================

--- Constructed panel: dark translucent body, hairline border, corner brackets,
--- one cut corner. cfg: size, position, title?, tone? ("system" | "fate" | "danger").
--- Returns { root, body, open(), close() }.
function Sigil.panel(parent: Instance, cfg: { [string]: any })
	local tone: string = cfg.tone or "system"
	local root = mk("CanvasGroup", {
		Name = cfg.name or "SigilPanel",
		BackgroundColor3 = Style.Void,
		BackgroundTransparency = 0.18,
		BorderSizePixel = 0,
		Size = cfg.size or UDim2.fromOffset(360, 240),
		Position = cfg.position or UDim2.new(),
		AnchorPoint = cfg.anchor or Vector2.zero,
		GroupTransparency = 1,
	}, parent)
	mk("UIGradient", {
		Color = ColorSequence.new(Style.Indigo, Style.Void),
		Rotation = 70,
		Transparency = NumberSequence.new(0.55, 0),
	}, root)
	local stroke = mk("UIStroke", { Thickness = 1, Transparency = 0.6 }, root)
	paint(stroke, "Color", tone)

	-- Faint inner rule inset from the edge: the "constructed" second layer.
	local inner = box({ Position = UDim2.fromOffset(5, 5), Size = UDim2.new(1, -10, 1, -10) }, root)
	mk("UIStroke", { Color = Style.Violet, Thickness = 1, Transparency = 0.86 }, inner)

	for _, c in { { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } } do
		local ax, ay = c[1], c[2]
		local h = box({
			AnchorPoint = Vector2.new(ax, ay),
			Position = UDim2.fromScale(ax, ay),
			Size = UDim2.fromOffset(16, 2),
			BackgroundTransparency = 0.1,
		}, root)
		local v = box({
			AnchorPoint = Vector2.new(ax, ay),
			Position = UDim2.fromScale(ax, ay),
			Size = UDim2.fromOffset(2, 16),
			BackgroundTransparency = 0.1,
		}, root)
		paint(h, "BackgroundColor3", tone)
		paint(v, "BackgroundColor3", tone)
	end
	-- Cut corner (top right): a diagonal hairline plus a Void wedge hiding the corner.
	local cut = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(1, -6, 0, 6),
		Size = UDim2.fromOffset(26, 1),
		Rotation = 45,
		BackgroundTransparency = 0.2,
	}, root)
	paint(cut, "BackgroundColor3", tone)

	local top = 12
	if cfg.title then
		caption(root, cfg.title, tone, UDim2.fromOffset(16, 12), UDim2.new(1, -60, 0, 14))
		line(root, {
			Position = UDim2.fromOffset(16, 30),
			Size = UDim2.new(1, -60, 0, 1),
			BackgroundTransparency = 0.6,
		}, tone, 0.1)
		top = 40
	end
	local body =
		box({ Position = UDim2.fromOffset(16, top), Size = UDim2.new(1, -32, 1, -top - 14) }, root)

	local api = { root = root, body = body }
	local rest = root.Position
	function api.open()
		root.Position = rest + UDim2.fromOffset(0, 10)
		tween(root, Style.Motion.Normal, { GroupTransparency = 0, Position = rest })
	end
	function api.close()
		local t = tween(
			root,
			Style.Motion.Fast,
			{ GroupTransparency = 1, Position = rest + UDim2.fromOffset(0, 6) }
		)
		t.Completed:Once(function()
			root.Position = rest
		end)
	end
	return api
end

-- ===================================================================
-- Button, tabs
-- ===================================================================

--- Text button with a left tick and an underline that draws on hover.
--- cfg: text, tone?, size?, position?, onClick?, disabled?
function Sigil.button(parent: Instance, cfg: { [string]: any }): any
	local tone: string = cfg.tone or "system"
	local b = mk("TextButton", {
		Name = "SigilButton",
		AutoButtonColor = false,
		Text = "",
		BorderSizePixel = 0,
		BackgroundTransparency = 0.92,
		Size = cfg.size or UDim2.new(1, 0, 0, 34),
		Position = cfg.position or UDim2.new(),
		AnchorPoint = cfg.anchor or Vector2.zero,
	}, parent)
	paint(b, "BackgroundColor3", tone)
	local tick = box({ Size = UDim2.new(0, 2, 1, 0), BackgroundTransparency = 0.3 }, b)
	paint(tick, "BackgroundColor3", tone)
	local txt = label(b, {
		text = cfg.text or "",
		font = Style.Fonts.Label,
		size = 17,
		color = Style.TextHigh,
		pos = UDim2.fromOffset(14, 0),
		sz = UDim2.new(1, -20, 1, 0),
	})
	local under = box({
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(0, 0, 0, 1),
		BackgroundTransparency = 0.2,
	}, b)
	paint(under, "BackgroundColor3", tone)
	if cfg.disabled then
		txt.TextTransparency = 0.6
	end
	b.MouseEnter:Connect(function()
		tween(under, Style.Motion.Normal, { Size = UDim2.new(1, 0, 0, 1) })
		tween(b, Style.Motion.Fast, { BackgroundTransparency = 0.82 })
		tween(txt, Style.Motion.Fast, { Position = UDim2.fromOffset(18, 0) })
	end)
	b.MouseLeave:Connect(function()
		tween(under, Style.Motion.Fast, { Size = UDim2.new(0, 0, 0, 1) })
		tween(b, Style.Motion.Normal, { BackgroundTransparency = 0.92 })
		tween(txt, Style.Motion.Fast, { Position = UDim2.fromOffset(14, 0) })
	end)
	b.Activated:Connect(function()
		if not cfg.disabled and cfg.onClick then
			cfg.onClick()
		end
	end)
	return b
end

--- Row of text tabs with a diamond marker that slides to the selection.
--- cfg: labels {string}, tone?, onSelect(index, label)?, width per tab via tabWidth.
function Sigil.tabs(parent: Instance, cfg: { [string]: any }): any
	local tone: string = cfg.tone or "system"
	local w: number = cfg.tabWidth or 110
	local root = box(
		{ Size = cfg.size or UDim2.new(1, 0, 0, 30), Position = cfg.position or UDim2.new() },
		parent
	)
	line(root, {
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 1),
		BackgroundTransparency = 0.8,
	}, tone, 0)
	local marker = diamond(root, 6, "fate", UDim2.new(0, w / 2, 1, 0))
	local buttons: { TextButton } = {}
	local function select(i: number)
		for n, tb in buttons do
			tween(tb, Style.Motion.Fast, { TextTransparency = if n == i then 0 else 0.45 })
		end
		tween(marker, Style.Motion.Normal, { Position = UDim2.new(0, (i - 0.5) * w, 1, 0) })
		if cfg.onSelect then
			cfg.onSelect(i, cfg.labels[i])
		end
	end
	for i, text in cfg.labels do
		local tb = mk("TextButton", {
			BackgroundTransparency = 1,
			Text = string.upper(text),
			Font = Style.Fonts.Label,
			TextSize = 15,
			TextColor3 = Style.TextHigh,
			TextTransparency = 0.45,
			Size = UDim2.new(0, w, 1, -4),
			Position = UDim2.fromOffset((i - 1) * w, 0),
		}, root)
		buttons[i] = tb
		tb.Activated:Connect(function()
			select(i)
		end)
	end
	select(1)
	return { root = root, select = select }
end

-- ===================================================================
-- Notifier and tooltip
-- ===================================================================

--- Stack of slide-in notifications. push{ title, body, tone?, duration? }.
function Sigil.notifier(gui: Instance): any
	local stack = box({
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -16, 0, 64),
		Size = UDim2.fromOffset(280, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
	}, gui)
	mk("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, stack)
	local api = {}
	function api.push(cfg: { [string]: any })
		local tone: string = cfg.tone or "system"
		local slot = box({ Size = UDim2.new(1, 0, 0, 58) }, stack)
		local card = mk("CanvasGroup", {
			BackgroundColor3 = Style.Void,
			BackgroundTransparency = 0.15,
			BorderSizePixel = 0,
			Size = UDim2.fromScale(1, 1),
			Position = UDim2.fromOffset(40, 0),
			GroupTransparency = 1,
		}, slot)
		local edge = box({ Size = UDim2.new(0, 2, 1, 0), BackgroundTransparency = 0.1 }, card)
		paint(edge, "BackgroundColor3", tone)
		local s = mk("UIStroke", { Thickness = 1, Transparency = 0.75 }, card)
		paint(s, "Color", tone)
		caption(card, cfg.title or "", tone, UDim2.fromOffset(14, 8))
		label(card, {
			text = cfg.body or "",
			size = 13,
			color = Style.TextHigh,
			pos = UDim2.fromOffset(14, 24),
			sz = UDim2.new(1, -20, 0, 28),
			wrap = true,
			yalign = Enum.TextYAlignment.Top,
		})
		tween(card, Style.Motion.Normal, { Position = UDim2.new(), GroupTransparency = 0 })
		line(card, {
			AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.fromScale(0, 1),
			Size = UDim2.new(1, 0, 0, 1),
		}, tone, 0.2)
		task.delay(cfg.duration or 4, function()
			if card.Parent then
				local t = tween(
					card,
					Style.Motion.Normal,
					{ Position = UDim2.fromOffset(40, 0), GroupTransparency = 1 }
				)
				t.Completed:Once(function()
					slot:Destroy()
				end)
			end
		end)
	end
	return api
end

--- One shared tooltip that follows the cursor. attach(guiObject, title, body).
function Sigil.tooltip(gui: Instance): any
	local tip = mk("CanvasGroup", {
		BackgroundColor3 = Style.Void,
		BackgroundTransparency = 0.1,
		BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.XY,
		Size = UDim2.fromOffset(0, 0),
		GroupTransparency = 1,
		ZIndex = 50,
		Visible = false,
	}, gui)
	mk("UISizeConstraint", { MaxSize = Vector2.new(260, 400) }, tip)
	mk("UIPadding", {
		PaddingTop = UDim.new(0, 8),
		PaddingBottom = UDim.new(0, 9),
		PaddingLeft = UDim.new(0, 12),
		PaddingRight = UDim.new(0, 12),
	}, tip)
	local st = mk("UIStroke", { Thickness = 1, Transparency = 0.6 }, tip)
	paint(st, "Color", "fate")
	mk("UIListLayout", { Padding = UDim.new(0, 3), SortOrder = Enum.SortOrder.LayoutOrder }, tip)
	local title = caption(tip, "", "fate", nil, UDim2.new(0, 0, 0, 14))
	title.AutomaticSize = Enum.AutomaticSize.X
	local body = label(tip, {
		text = "",
		size = 13,
		wrap = true,
		sz = UDim2.new(0, 0, 0, 0),
		auto = Enum.AutomaticSize.XY,
	})
	local api = {}
	local c = UserInputService.InputChanged:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseMovement then
			local p = UserInputService:GetMouseLocation()
			tip.Position = UDim2.fromOffset(p.X + 16, p.Y + 18)
		end
	end)
	tip.Destroying:Once(function()
		c:Disconnect()
	end)
	function api.attach(target: GuiObject, t: string, b: string)
		target.MouseEnter:Connect(function()
			title.Text = string.upper(t)
			body.Text = b
			tip.Visible = true
			tween(tip, Style.Motion.Fast, { GroupTransparency = 0 }, 0.25)
		end)
		target.MouseLeave:Connect(function()
			tip.GroupTransparency = 1
			tip.Visible = false
		end)
	end
	return api
end

-- ===================================================================
-- Full-screen menu header
-- ===================================================================

--- Header for a full-screen menu: orbit glyph, small label, display title,
--- a rule that draws itself across, and a ring close button.
--- cfg: title, label?, tone?, onClose?
function Sigil.header(parent: Instance, cfg: { [string]: any }): any
	local tone: string = cfg.tone or "fate"
	local root =
		box({ Size = UDim2.new(1, 0, 0, 84), Position = cfg.position or UDim2.new() }, parent)
	local glyph = box({ Position = UDim2.fromOffset(0, 14), Size = UDim2.fromOffset(46, 46) }, root)
	Sigil.ring(glyph, UDim2.fromScale(1, 1), tone, 1, 0.3)
	Sigil.ring(glyph, UDim2.fromScale(0.55, 0.55), "system", 1, 0.5)
	local o = orbit(glyph, 12, tone, 4, 0)
	spin(o, 18)
	diamond(glyph, 6, tone, UDim2.fromScale(0.5, 0.5))
	local lbl = caption(
		root,
		cfg.label or "",
		"system",
		UDim2.fromOffset(62, 12),
		UDim2.new(1, -120, 0, 14)
	)
	local ttl = label(root, {
		text = string.upper(cfg.title or ""),
		font = Style.Fonts.Display,
		size = 32,
		color = Style.TextHigh,
		pos = UDim2.fromOffset(62, 28),
		sz = UDim2.new(1, -120, 0, 34),
	})
	fadeIn(lbl, 0.25)
	fadeIn(ttl, 0.35)
	line(root, {
		Position = UDim2.new(0, 0, 1, -6),
		Size = UDim2.new(1, 0, 0, 1),
		BackgroundTransparency = 0.5,
	}, tone, 0.1)
	if cfg.onClose then
		local x = mk("TextButton", {
			AnchorPoint = Vector2.new(1, 0),
			Position = UDim2.new(1, 0, 0, 16),
			Size = UDim2.fromOffset(38, 38),
			BackgroundTransparency = 1,
			Text = "",
			AutoButtonColor = false,
		}, root)
		local r = Sigil.ring(x, UDim2.fromScale(1, 1), "system", 1, 0.5)
		label(x, {
			text = "x",
			font = Style.Fonts.Label,
			size = 16,
			align = Enum.TextXAlignment.Center,
			tone = "system",
		})
		x.MouseEnter:Connect(function()
			tween(r.UIStroke, Style.Motion.Fast, { Transparency = 0 })
		end)
		x.MouseLeave:Connect(function()
			tween(r.UIStroke, Style.Motion.Normal, { Transparency = 0.5 })
		end)
		x.Activated:Connect(cfg.onClose)
	end
	return root
end

-- ===================================================================
-- Fate Engine
-- ===================================================================

--- The centrepiece: concentric rings, orbiting ticks, radial option nodes and a
--- central trigger. Choosing a node selects a Fate option; the centre rolls.
--- Visual only: the roll outcome is decided server-side (the caller supplies it).
--- cfg: size (px), options {string}, onSelect(i)?, onRoll(selected, finish)?
--- onRoll receives finish(), which the caller invokes when the result arrives.
function Sigil.engine(parent: Instance, cfg: { [string]: any }): any
	local S: number = cfg.size or 420
	local options: { string } = cfg.options or {}
	local root = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = cfg.position or UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(S, S),
	}, parent)

	Sigil.ring(root, UDim2.fromScale(1, 1), "system", 1, 0.55)
	Sigil.ring(root, UDim2.fromScale(0.94, 0.94), "system", 1, 0.85)
	local outer = orbit(root, 72, "fate", 6, 18)
	spin(outer, 6)
	local midHolder = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(0.72, 0.72),
	}, root)
	Sigil.ring(midHolder, UDim2.fromScale(1, 1), "fate", 1, 0.35)
	local midOrbit = orbit(midHolder, 36, "system", 4, 12)
	spin(midOrbit, -10)
	Sigil.ring(root, UDim2.fromScale(0.5, 0.5), "system", 1, 0.7)
	local core = Sigil.ring(root, UDim2.fromScale(0.34, 0.34), "fate", 2, 0.15)

	local selected = 1
	local nodes: { any } = {}
	local readout = label(root, {
		text = "",
		font = Style.Fonts.Display,
		size = 11,
		tone = "fate",
		align = Enum.TextXAlignment.Center,
		anchor = Vector2.new(0.5, 0.5),
		pos = UDim2.fromScale(0.5, 0.455),
		sz = UDim2.fromScale(0.3, 0.06),
	})
	local sub = caption(
		root,
		"Roll Fate",
		"system",
		UDim2.fromScale(0.35, 0.51),
		UDim2.fromScale(0.3, 0.05)
	)
	sub.TextXAlignment = Enum.TextXAlignment.Center

	local function choose(i: number)
		selected = i
		readout.Text = string.upper(options[i] or "")
		for n, nd in nodes do
			tween(nd.dot, Style.Motion.Fast, {
				BackgroundTransparency = if n == i then 0 else 0.7,
				Size = if n == i then UDim2.fromOffset(12, 12) else UDim2.fromOffset(8, 8),
			})
			tween(nd.text, Style.Motion.Fast, { TextTransparency = if n == i then 0 else 0.45 })
		end
		if cfg.onSelect then
			cfg.onSelect(i)
		end
	end

	-- Options sit on the middle ring, labels pushed radially outward.
	for i, name in options do
		local a = math.rad((i - 1) * 360 / #options - 90 + 180 / #options)
		local pos = UDim2.fromScale(0.5 + 0.36 * math.cos(a), 0.5 + 0.36 * math.sin(a))
		local hit = mk("TextButton", {
			BackgroundTransparency = 1,
			Text = "",
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = pos,
			Size = UDim2.fromOffset(34, 34),
		}, root)
		local dot = diamond(hit, 8, "fate", UDim2.fromScale(0.5, 0.5))
		dot.BackgroundTransparency = 0.7
		local lp = UDim2.fromScale(0.5 + 0.45 * math.cos(a), 0.5 + 0.45 * math.sin(a))
		local text = label(root, {
			text = string.upper(name),
			font = Style.Fonts.Label,
			size = 14,
			color = Style.TextHigh,
			align = Enum.TextXAlignment.Center,
			anchor = Vector2.new(0.5, 0.5),
			pos = lp,
			sz = UDim2.fromOffset(90, 14),
		})
		text.TextTransparency = 0.45
		hit.Activated:Connect(function()
			choose(i)
		end)
		hit.MouseEnter:Connect(function()
			tween(dot, Style.Motion.Fast, { Size = UDim2.fromOffset(12, 12) })
		end)
		hit.MouseLeave:Connect(function()
			if selected ~= i then
				tween(dot, Style.Motion.Fast, { Size = UDim2.fromOffset(8, 8) })
			end
		end)
		nodes[i] = { dot = dot, text = text }
	end

	local rolling = false
	local api = { root = root }
	function api.roll()
		if rolling then
			return
		end
		rolling = true
		sub.Text = "ALIGNING"
		-- Pulse rings expand outward in sequence.
		for k = 0, 2 do
			task.delay(k * 0.3, function()
				local p = Sigil.ring(root, UDim2.fromScale(0.34, 0.34), "fate", 2, 0.2)
				tween(p, 1.1, { Size = UDim2.fromScale(1.25, 1.25) })
				tween(p.UIStroke, 1.1, { Transparency = 1 })
				task.delay(1.2, function()
					p:Destroy()
				end)
			end)
		end
		tween(core.UIStroke, 0.3, { Thickness = 5, Transparency = 0 })
		local t0 = os.clock()
		local c = RunService.Heartbeat:Connect(function(dt)
			outer.Rotation += 240 * dt
			midOrbit.Rotation -= 360 * dt
		end)
		local function finish()
			c:Disconnect()
			tween(core.UIStroke, 0.6, { Thickness = 2, Transparency = 0.15 })
			sub.Text = "ROLL FATE"
			rolling = false
		end
		if cfg.onRoll then
			cfg.onRoll(selected, finish)
		else
			task.delay(math.max(0, 1.6 - (os.clock() - t0)), finish)
		end
	end
	local trigger = mk("TextButton", {
		BackgroundTransparency = 1,
		Text = "",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(0.34, 0.34),
	}, root)
	mk("UICorner", { CornerRadius = UDim.new(1, 0) }, trigger)
	trigger.Activated:Connect(api.roll)
	trigger.MouseEnter:Connect(function()
		tween(core.UIStroke, Style.Motion.Fast, { Transparency = 0, Thickness = 3 })
	end)
	trigger.MouseLeave:Connect(function()
		if not rolling then
			tween(core.UIStroke, Style.Motion.Normal, { Transparency = 0.15, Thickness = 2 })
		end
	end)
	choose(1)
	return api
end

-- ===================================================================
-- Gameplay HUD
-- ===================================================================

local function thinBar(
	parent: Instance,
	pos: UDim2,
	w: number,
	h: number,
	tone: string,
	name: string
): any
	local track = box({
		Position = pos,
		Size = UDim2.fromOffset(w, h),
		BackgroundColor3 = Style.Void,
		BackgroundTransparency = 0.4,
	}, parent)
	local fill = box({ Size = UDim2.fromScale(1, 1), BackgroundTransparency = 0.05 }, track)
	paint(fill, "BackgroundColor3", tone)
	local cap = diamond(track, h + 3, tone, UDim2.new(1, 0, 0.5, 0))
	caption(track, name, nil, UDim2.fromOffset(0, -14), UDim2.new(1, 0, 0, 12))
	return {
		set = function(f: number)
			f = math.clamp(f, 0, 1)
			tween(fill, Style.Motion.Fast, { Size = UDim2.fromScale(f, 1) })
			tween(cap, Style.Motion.Fast, { Position = UDim2.new(f, 0, 0.5, 0) })
		end,
	}
end

--- Minimal run HUD: vitals bottom-left, Fate ring top-left, objective top-centre,
--- ability diamond bottom-centre. Returns setters.
function Sigil.hud(gui: Instance): any
	local root = box({ Name = "SigilHud", Size = UDim2.fromScale(1, 1) }, gui)
	local health = thinBar(root, UDim2.new(0, 28, 1, -64), 240, 4, "danger", "Vitality")
	local stamina = thinBar(root, UDim2.new(0, 28, 1, -36), 170, 3, "system", "Stamina")

	local fate = box({ Position = UDim2.fromOffset(24, 22), Size = UDim2.fromOffset(46, 46) }, root)
	Sigil.ring(fate, UDim2.fromScale(1, 1), "fate", 1, 0.25)
	Sigil.ring(fate, UDim2.fromScale(0.78, 0.78), "fate", 1, 0.75)
	local lvl = label(fate, {
		text = "1",
		font = Style.Fonts.Display,
		size = 14,
		tone = "fate",
		align = Enum.TextXAlignment.Center,
	})
	caption(root, "Fate", "fate", UDim2.fromOffset(78, 34), UDim2.fromOffset(60, 14))

	local objLabel =
		caption(root, "Objective", "system", UDim2.new(0.5, -160, 0, 20), UDim2.fromOffset(320, 14))
	objLabel.TextXAlignment = Enum.TextXAlignment.Center
	local obj = label(root, {
		text = "",
		size = 14,
		align = Enum.TextXAlignment.Center,
		pos = UDim2.new(0.5, -160, 0, 36),
		sz = UDim2.fromOffset(320, 20),
	})
	line(root, {
		Position = UDim2.new(0.5, -90, 0, 60),
		Size = UDim2.fromOffset(180, 1),
		BackgroundTransparency = 0.7,
	}, "system", 0.3)

	local slot = box({
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -34),
		Size = UDim2.fromOffset(46, 46),
	}, root)
	local sq = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(34, 34),
		Rotation = 45,
	}, slot)
	local ss = mk("UIStroke", { Thickness = 1, Transparency = 0.3 }, sq)
	paint(ss, "Color", "fate")
	local ability = label(root, {
		text = "",
		font = Style.Fonts.Label,
		size = 11,
		color = Style.TextMuted,
		align = Enum.TextXAlignment.Center,
		anchor = Vector2.new(0.5, 0),
		pos = UDim2.new(0.5, 0, 1, -28),
		sz = UDim2.fromOffset(160, 14),
	})
	ability.Text = ""

	return {
		root = root,
		setHealth = health.set,
		setStamina = stamina.set,
		setFate = function(n: number)
			lvl.Text = tostring(n)
		end,
		setObjective = function(t: string)
			obj.Text = t
		end,
		setAbility = function(t: string)
			ability.Text = string.upper(t)
		end,
	}
end

-- ===================================================================
-- Universal menu
-- ===================================================================

--- Small ring in the top-right that opens a short list of universal functions
--- (Settings, Codes...). items: { {text, onClick} }.
function Sigil.menu(gui: Instance, items: { { [string]: any } }): any
	local btn = mk("TextButton", {
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -16, 0, 16),
		Size = UDim2.fromOffset(38, 38),
		BackgroundTransparency = 1,
		Text = "",
		AutoButtonColor = false,
	}, gui)
	local r = Sigil.ring(btn, UDim2.fromScale(1, 1), "system", 1, 0.45)
	Sigil.ring(btn, UDim2.fromScale(0.4, 0.4), "fate", 1, 0.3)
	diamond(btn, 4, "fate", UDim2.fromScale(0.5, 0.5))
	local panel = Sigil.panel(gui, {
		size = UDim2.fromOffset(200, 24 + #items * 38 + 24),
		anchor = Vector2.new(1, 0),
		position = UDim2.new(1, -16, 0, 62),
		title = "System",
	})
	panel.root.Visible = false
	for i, it in items do
		Sigil.button(panel.body, {
			text = it.text,
			position = UDim2.fromOffset(0, (i - 1) * 38),
			size = UDim2.new(1, 0, 0, 32),
			onClick = it.onClick,
		})
	end
	local open = false
	btn.Activated:Connect(function()
		open = not open
		if open then
			panel.root.Visible = true
			panel.open()
		else
			panel.close()
			task.delay(Style.Motion.Fast, function()
				if not open then
					panel.root.Visible = false
				end
			end)
		end
		tween(r.UIStroke, Style.Motion.Fast, { Transparency = if open then 0 else 0.45 })
	end)
	return { button = btn, panel = panel }
end

-- ===================================================================
-- Title / loading screen
-- ===================================================================

--- Full-screen title: slow ring pulses, spaced display wordmark, a progress line.
--- Returns { root, setProgress(f), finish() }.
function Sigil.titleScreen(gui: Instance, cfg: { [string]: any }?): any
	local c = cfg or {}
	local root = box({
		Name = "SigilTitle",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Style.Void,
		BackgroundTransparency = 0,
		ZIndex = 100,
		Active = true,
	}, gui)
	mk("UIGradient", {
		Color = ColorSequence.new(Style.Indigo, Style.Void),
		Rotation = 90,
		Transparency = NumberSequence.new(0.4, 0),
	}, root)
	local stage = box({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.46),
		Size = UDim2.fromOffset(300, 300),
	}, root)
	Sigil.ring(stage, UDim2.fromScale(0.5, 0.5), "fate", 1, 0.3)
	local o = orbit(stage, 48, "system", 5, 12)
	spin(o, 5)

	local alive = true
	task.spawn(function()
		while alive and root.Parent do
			local p = Sigil.ring(stage, UDim2.fromScale(0.5, 0.5), "system", 1, 0.4)
			tween(p, 3.2, { Size = UDim2.fromScale(2.4, 2.4) })
			tween(p.UIStroke, 3.2, { Transparency = 1 })
			task.delay(3.3, function()
				p:Destroy()
			end)
			task.wait(1.6 / Style.accent().speed)
		end
	end)

	local word = table.concat(string.split("LUCKBOUND", ""), "\u{200A}\u{200A}")
	local title = label(root, {
		text = word,
		font = Style.Fonts.Display,
		size = 44,
		color = Style.TextHigh,
		align = Enum.TextXAlignment.Center,
		anchor = Vector2.new(0.5, 0.5),
		pos = UDim2.fromScale(0.5, 0.46),
		sz = UDim2.fromOffset(700, 60),
	})
	fadeIn(title, 0.5)
	local tag = caption(
		root,
		c.tagline or "Bound to fate",
		"fate",
		UDim2.new(0.5, -150, 0.46, 40),
		UDim2.fromOffset(300, 14)
	)
	tag.TextXAlignment = Enum.TextXAlignment.Center
	fadeIn(tag, 1)

	local track = box({
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0.8, 0),
		Size = UDim2.fromOffset(280, 1),
		BackgroundColor3 = Style.Violet,
		BackgroundTransparency = 0.6,
	}, root)
	local fill = box({ Size = UDim2.fromScale(0, 1), BackgroundTransparency = 0 }, track)
	paint(fill, "BackgroundColor3", "fate")
	local status = caption(
		root,
		"Aligning",
		"system",
		UDim2.new(0.5, -140, 0.8, 10),
		UDim2.fromOffset(280, 14)
	)
	status.TextXAlignment = Enum.TextXAlignment.Center

	local api = { root = root }
	function api.setProgress(f: number, text: string?)
		tween(fill, Style.Motion.Normal, { Size = UDim2.fromScale(math.clamp(f, 0, 1), 1) })
		if text then
			status.Text = string.upper(text)
		end
	end
	function api.finish()
		alive = false
		local t = tween(root, Style.Motion.Slow, { BackgroundTransparency = 1 })
		for _, d in root:GetDescendants() do
			if d:IsA("TextLabel") then
				tween(d, Style.Motion.Slow, { TextTransparency = 1 })
			elseif d:IsA("Frame") then
				tween(d, Style.Motion.Slow, { BackgroundTransparency = 1 })
			elseif d:IsA("UIStroke") then
				tween(d, Style.Motion.Slow, { Transparency = 1 })
			end
		end
		t.Completed:Once(function()
			root:Destroy()
			if c.onDone then
				c.onDone()
			end
		end)
	end
	return api
end

-- Shared drawing helpers, exposed so composed screens (the Fate Engine menu)
-- build from the same glyph vocabulary.
Sigil.diamond = diamond
Sigil.orbit = orbit
Sigil.spin = spin
Sigil.caption = caption

return Sigil
