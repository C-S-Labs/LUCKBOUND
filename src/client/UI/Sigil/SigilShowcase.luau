--!strict
-- Style-exploration board for the SIGIL visual language. Press F8 in Studio to
-- toggle it. It is a dev-only overlay: it touches no game state and the live UI
-- is untouched. Shows every prototype component plus the Fate-state retint.

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local Sigil = require(script.Parent.Sigil)
local Style = require(script.Parent.SigilStyle)

local SigilShowcase = {}

local function build(): ScreenGui
	local gui = Instance.new("ScreenGui")
	gui.Name = "SigilShowcase"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 90
	gui.Enabled = false
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

	local scrim = Instance.new("Frame")
	scrim.Size = UDim2.fromScale(1, 1)
	scrim.BackgroundColor3 = Style.Void
	scrim.BackgroundTransparency = 0.35
	scrim.BorderSizePixel = 0
	scrim.Parent = gui

	local hud = Sigil.hud(gui)
	hud.setHealth(0.72)
	hud.setStamina(0.55)
	hud.setFate(12)
	hud.setObjective("Reach the Sky Citadel")
	hud.setAbility("Aether Reap")

	local notifier = Sigil.notifier(gui)
	local tooltip = Sigil.tooltip(gui)
	Sigil.menu(gui, {
		{
			text = "Settings",
			onClick = function()
				notifier.push({ title = "System", body = "Settings would open here." })
			end,
		},
		{
			text = "Codes",
			onClick = function()
				notifier.push({ title = "System", body = "Codes would open here." })
			end,
		},
	})

	-- Full-screen menu composition (left): header, tabs, panel, buttons.
	local menu = Sigil.panel(gui, {
		size = UDim2.fromOffset(470, 430),
		position = UDim2.new(0, 60, 0.5, -215),
		tone = "fate",
		name = "MenuPanel",
	})
	Sigil.header(menu.body, {
		title = "Sky Citadel",
		label = "World variant",
		onClose = function()
			notifier.push({ title = "Menu", body = "Close pressed.", tone = "danger" })
		end,
	})
	Sigil.tabs(
		menu.body,
		{ labels = { "Travel", "Risk", "Party" }, position = UDim2.fromOffset(0, 92) }
	)
	local y = 140
	for _, spec in
		{
			{ "Embark", "fate", "Embark", "Begins the expedition. Gold marks a Fate decision." },
			{ "Discovery log", "system", "Discovery", "Cyan marks world and system information." },
			{ "Abandon run", "danger", "Risk", "Crimson is reserved for danger." },
		}
	do
		local b = Sigil.button(menu.body, {
			text = spec[1],
			tone = spec[2],
			position = UDim2.fromOffset(0, y),
			size = UDim2.new(1, 0, 0, 36),
			onClick = function()
				notifier.push({ title = spec[3], body = spec[4], tone = spec[2] })
			end,
		})
		tooltip.attach(b, spec[3], spec[4])
		y += 46
	end
	Sigil.panel(menu.body, {
		size = UDim2.new(1, 0, 0, 70),
		position = UDim2.fromOffset(0, y + 4),
		title = "Fate condition",
		tone = "system",
	}).open()

	-- Fate Engine (right).
	local engine = Sigil.engine(gui, {
		size = 540,
		position = UDim2.new(1, -340, 0.5, 0),
		options = { "Fortune", "Chaos", "Aether", "Ruin", "Legacy" },
	})

	-- State switcher (bottom centre).
	local bar = Instance.new("Frame")
	bar.BackgroundTransparency = 1
	bar.AnchorPoint = Vector2.new(0.5, 1)
	bar.Position = UDim2.new(0.5, 0, 1, -110)
	bar.Size = UDim2.fromOffset(500, 34)
	bar.Parent = gui
	local n = 0
	for name in Style.States do
		Sigil.button(bar, {
			text = name,
			size = UDim2.fromOffset(116, 30),
			position = UDim2.fromOffset(n * 128, 0),
			tone = "system",
			onClick = function()
				Style.setState(name)
			end,
		})
		n += 1
	end

	local title
	Sigil.button(gui, {
		text = "Replay title screen",
		size = UDim2.fromOffset(190, 30),
		anchor = Vector2.new(0, 1),
		position = UDim2.new(0, 60, 1, -20),
		onClick = function()
			title = Sigil.titleScreen(gui, {})
			for i = 1, 5 do
				task.delay(i * 0.5, function()
					title.setProgress(i / 5, i == 5 and "Ready" or "Aligning")
				end)
			end
			task.delay(3.4, title.finish)
		end,
	})

	menu.open()
	task.delay(0.5, function()
		notifier.push({
			title = "Discovery",
			body = "A rare Fate condition has been detected.",
			tone = "fate",
		})
	end)
	return gui
end

function SigilShowcase.init()
	local gui: ScreenGui? = nil
	UserInputService.InputBegan:Connect(function(input, processed)
		if processed or input.KeyCode ~= Enum.KeyCode.F8 then
			return
		end
		if gui then
			gui:Destroy()
			gui = nil
		else
			gui = build()
			gui.Enabled = true
		end
	end)
end

return SigilShowcase
