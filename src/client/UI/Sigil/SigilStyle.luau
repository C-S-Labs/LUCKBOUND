--!strict
-- SIGIL: the LUCKBOUND UI visual language (prototype). Tokens only, no Instances.
-- Colour carries meaning: gold = Fate/progression/decision, cyan = world and
-- system information, crimson = danger. Everything a component paints comes
-- from here, so a Fate state can retint the whole interface by changing one
-- table. Not wired to the live UI yet (see SigilShowcase).

export type Accent = {
	fate: Color3,
	system: Color3,
	danger: Color3,
	speed: number, -- multiplier for ambient motion (ring spin, pulses)
}

local Style = {
	-- Environment: near-black through muted violet.
	Void = Color3.fromRGB(7, 6, 14),
	Deep = Color3.fromRGB(13, 11, 28),
	Indigo = Color3.fromRGB(28, 24, 62),
	Violet = Color3.fromRGB(96, 84, 150),

	-- Text.
	TextHigh = Color3.fromRGB(236, 232, 250),
	TextMuted = Color3.fromRGB(150, 144, 184),

	-- Fonts: wide display face for titles, clean face for reading, small caps labels.
	Fonts = {
		Display = Enum.Font.Michroma,
		Body = Enum.Font.BuilderSans,
		Label = Enum.Font.BuilderSansBold,
	},

	-- Motion (seconds). Restrained: fades, drawn lines, expanding rings.
	Motion = { Fast = 0.14, Normal = 0.28, Draw = 0.5, Slow = 0.9 },
	Ease = Enum.EasingStyle.Quint,

	-- Fate / world reactivity. Each state is only an accent override.
	States = {
		NORMAL = {
			fate = Color3.fromRGB(232, 184, 92),
			system = Color3.fromRGB(110, 214, 240),
			danger = Color3.fromRGB(190, 52, 64),
			speed = 1,
		},
		CHAOTIC = {
			fate = Color3.fromRGB(240, 150, 78),
			system = Color3.fromRGB(150, 170, 255),
			danger = Color3.fromRGB(190, 52, 64),
			speed = 2.2,
		},
		AETHER = {
			fate = Color3.fromRGB(222, 236, 255),
			system = Color3.fromRGB(150, 236, 255),
			danger = Color3.fromRGB(190, 52, 64),
			speed = 1.3,
		},
		DANGER = {
			fate = Color3.fromRGB(236, 132, 70),
			system = Color3.fromRGB(196, 130, 120),
			danger = Color3.fromRGB(224, 62, 58),
			speed = 1.6,
		},
	} :: { [string]: Accent },
}

local current: Accent = Style.States.NORMAL
local listeners: { () -> () } = {}

function Style.accent(): Accent
	return current
end

--- Colour for a tone name: "fate" | "system" | "danger".
function Style.tone(name: string): Color3
	return (current :: any)[name] or current.system
end

--- Switches the live accent set and repaints every bound component.
function Style.setState(name: string)
	current = Style.States[name] or Style.States.NORMAL
	for _, fn in listeners do
		fn()
	end
end

--- Registers a repaint callback; the returned table's Disconnect removes it.
function Style.bind(fn: () -> ()): { Disconnect: () -> () }
	table.insert(listeners, fn)
	return {
		Disconnect = function()
			local i = table.find(listeners, fn)
			if i then
				table.remove(listeners, i)
			end
		end,
	}
end

return Style
