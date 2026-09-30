--!strict
-- The expedition rifts (build spec §7.8): the ENTRANCE (the way home, always
-- open) and the EXIT (materialises where the boss fell). Built on the SERVER;
-- animated on the CLIENT by RiftController, from RiftCore's curves.
--
-- THE SPLIT. The authored mesh (assets/source/portals/, imported by the owner
-- as a prefab) is the SHAPE. This file adds what a mesh cannot carry -- the
-- light, the motes, the flowing ribbons -- and paints the parts, so the same
-- meshes serve a calm entrance and an exit that opens in five seconds.
--
-- A rift with NO prefab still builds: a blockout of the same named parts, so
-- the game never has a missing door. It has no fragments or lips, which the
-- controller tolerates: every part is looked up by name and may be absent.
--
-- A SEALED EXIT IS INVISIBLE BY CONSTRUCTION. It is built with every part
-- fully transparent and every effect off, so a client that has not yet run
-- RiftController (or never will) cannot see the door before the boss falls.
--
-- ORIENTATION. The tear lies in the model's local X (width) and Y (height)
-- plane and is thin along Z: players come and go along Z. Verify this at the
-- Studio import and correct it with the prefab's YawDegrees, not in code.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local PrefabLoader = require(Root.Util.PrefabLoader)

local RiftRig = {}

export type Config = {
	Name: string,
	Kind: string, -- "ENTRANCE" | "EXIT"
	-- Where the tear's tip stands: a point ON the walk surface.
	Position: Vector3,
	-- Which way the rift faces, about the vertical.
	Yaw: number?,
	-- The entrance takes the biome's rarity colour; the exit ignores this.
	RarityKey: string?,
}

-- Every part the code drives by name. A prefab missing one still builds (the
-- rest stands) but says so, rather than going quietly flat.
local CONTRACT = { "Scar", "ScarGlow", "RiftCore", "RiftMid", "RiftHalo", "Debris", "LightAnchor" }

-- Parts painted with the rift's colour. Neon emits at full Color, so the raw
-- colour blows out; it goes through `neon` first (GameConfig.Portal.NeonTint).
local TINTED_PREFIXES = { "ScarGlow", "RiftCore", "RiftMid", "RiftHalo", "Edge", "FragGem" }

local function isTinted(name: string): boolean
	for _, prefix in TINTED_PREFIXES do
		if string.sub(name, 1, #prefix) == prefix then
			return true
		end
	end
	return false
end

local function neon(color: Color3): Color3
	local tint = GameConfig.Portal.NeonTint
	return Color3.new(color.R * tint, color.G * tint, color.B * tint)
end

--- The colour a rift wears: the exit is always crimson, the entrance is the
--- biome's rarity.
function RiftRig.colorFor(kind: string, rarityKey: string?): Color3
	if kind == "EXIT" then
		return GameConfig.Rift.ExitColor
	end
	local rarity = rarityKey and Constants.RARITY[rarityKey]
	return if rarity then rarity.Color else Constants.RARITY.COMMON.Color
end

local function restTransparency(name: string): number
	local cfg = GameConfig.Rift
	if string.sub(name, 1, 8) == "RiftHalo" then
		return cfg.HaloTransparency
	elseif string.sub(name, 1, 7) == "RiftMid" then
		return cfg.MidTransparency
	elseif string.sub(name, 1, 8) == "RiftCore" then
		return cfg.CoreTransparency
	elseif string.sub(name, 1, 8) == "ScarGlow" then
		return 0.15
	elseif string.sub(name, 1, 4) == "Edge" then
		return 0.1
	end
	return 0
end

local function styles(): { [string]: any }
	local rock = Color3.fromRGB(70, 62, 92)
	local function tinted(name: string)
		return {
			Material = Enum.Material.Neon,
			CanCollide = false,
			Attributes = { RestTransparency = restTransparency(name) },
		}
	end
	return {
		Scar = {
			Color = Color3.fromRGB(46, 40, 60),
			Material = Enum.Material.Slate,
			CanCollide = false,
		},
		ScarGlow = tinted("ScarGlow"),
		RiftCore = tinted("RiftCore"),
		RiftMid = tinted("RiftMid"),
		RiftHalo = tinted("RiftHalo"),
		Edge = tinted("Edge"),
		FragGem = tinted("FragGem"),
		FragRock = { Color = rock, Material = Enum.Material.Slate, CanCollide = false },
		Debris = { Color = rock, Material = Enum.Material.Slate, CanCollide = false },
		LightAnchor = { Transparency = 1, CanCollide = false },
	}
end

local function blockPart(name: string, size: Vector3, cframe: CFrame, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.CanCollide = false
	part.CanTouch = false
	part.CanQuery = false
	part.Material = Enum.Material.SmoothPlastic
	part.Parent = parent
	return part
end

--- The stand-in used when no prefab is delivered: the same named parts as flat
--- glowing slabs. No fragments, no lips -- enough to be a door.
local function buildBlockout(config: Config, base: CFrame, parent: Instance): Model
	local dims = GameConfig.Rift.Blockout[config.Kind]
	local model = Instance.new("Model")
	model.Name = config.Name
	model.Parent = parent

	local h, w, t = dims.Height, dims.Width, dims.Thickness
	local centre = base * CFrame.new(0, h / 2 + 0.05, 0)

	local scar = blockPart(
		"Scar",
		Vector3.new(0.12, dims.ScarRadius * 1.4, dims.ScarRadius * 1.4),
		base * CFrame.new(0, 0.06, 0) * CFrame.Angles(0, 0, math.pi / 2),
		model
	)
	local shape = scar :: any
	shape.Shape = Enum.PartType.Cylinder
	scar.Color = Color3.fromRGB(46, 40, 60)
	scar.Material = Enum.Material.Slate

	local specs = {
		{
			"ScarGlow",
			Vector3.new(0.02, dims.ScarRadius * 0.9, dims.ScarRadius * 0.9),
			base * CFrame.new(0, 0.13, 0) * CFrame.Angles(0, 0, math.pi / 2),
		},
		{ "RiftCore", Vector3.new(w * 0.5, h * 0.86, t * 0.4), centre },
		{ "RiftMid", Vector3.new(w * 0.78, h * 0.94, t * 0.7), centre },
		{ "RiftHalo", Vector3.new(w * 1.05, h, t), centre },
	}
	for _, spec in specs do
		local part = blockPart(spec[1], spec[2], spec[3], model)
		part.Material = Enum.Material.Neon
		if spec[1] == "ScarGlow" then
			(part :: any).Shape = Enum.PartType.Cylinder
		end
		part:SetAttribute("RestTransparency", restTransparency(spec[1]))
	end
	-- Debris is a required part; an empty one keeps the contract whole.
	local debris = blockPart(
		"Debris",
		Vector3.one * 0.2,
		base * CFrame.new(dims.ScarRadius * 0.6, 0.1, 0),
		model
	)
	debris.Transparency = 1
	local anchor = blockPart("LightAnchor", Vector3.one * 0.4, centre, model)
	anchor.Transparency = 1
	model.PrimaryPart = scar
	return model
end

local function paint(rig: Model, color: Color3)
	local lit = neon(color)
	for _, d in rig:GetDescendants() do
		if d:IsA("BasePart") and isTinted(d.Name) then
			d.Color = lit
		end
	end
	local light = rig:FindFirstChild("RiftLight", true)
	if light and light:IsA("PointLight") then
		light.Color = color
	end
	for _, d in rig:GetDescendants() do
		if d:IsA("ParticleEmitter") or d:IsA("Beam") then
			d.Color = ColorSequence.new(color)
		end
	end
	rig:SetAttribute("RiftColor", color)
end

--- Reskins an existing rift. Rifts are recoloured, never rebuilt.
function RiftRig.setColor(rig: Model, color: Color3): ()
	paint(rig, color)
end

--- The light, the motes, the ribbons and the bloom burst. Created here, on
--- the server, so they replicate; RiftController only turns them up and down.
function RiftRig.attachEffects(rig: Model, color: Color3): ()
	local cfg = GameConfig.Rift
	local anchor = rig:FindFirstChild("LightAnchor")
	local core = rig:FindFirstChild("RiftCore")
	if not (anchor and anchor:IsA("BasePart")) then
		return
	end

	if not anchor:FindFirstChild("RiftLight") then
		local light = Instance.new("PointLight")
		light.Name = "RiftLight"
		light.Range = cfg.LightRange
		light.Brightness = cfg.IdleBrightness
		light.Color = color
		light.Parent = anchor
	end

	local emit = anchor:FindFirstChild("MoteAttachment")
	if not emit then
		local a = Instance.new("Attachment")
		a.Name = "MoteAttachment"
		a.Parent = anchor
		emit = a
	end
	if not emit:FindFirstChild("RiftMotes") then
		local motes = Instance.new("ParticleEmitter")
		motes.Name = "RiftMotes"
		motes.Rate = cfg.MoteRate
		motes.Lifetime = NumberRange.new(2, 4)
		motes.Speed = NumberRange.new(0.5, 2)
		motes.SpreadAngle = Vector2.new(180, 180)
		motes.Acceleration = Vector3.new(0, 1.5, 0)
		motes.LightEmission = 1
		motes.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0),
			NumberSequenceKeypoint.new(0.3, 0.35),
			NumberSequenceKeypoint.new(1, 0),
		})
		motes.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.25, 0.2),
			NumberSequenceKeypoint.new(1, 1),
		})
		motes.Color = ColorSequence.new(color)
		motes.Parent = emit
	end
	if not emit:FindFirstChild("RiftBurst") then
		local burst = Instance.new("ParticleEmitter")
		burst.Name = "RiftBurst"
		burst.Rate = 0
		burst.Enabled = false
		burst.Lifetime = NumberRange.new(1.2, 2.4)
		burst.Speed = NumberRange.new(6, 16)
		burst.SpreadAngle = Vector2.new(180, 180)
		burst.LightEmission = 1
		burst.Drag = 2
		burst.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.6),
			NumberSequenceKeypoint.new(1, 0),
		})
		burst.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0),
			NumberSequenceKeypoint.new(1, 1),
		})
		burst.Color = ColorSequence.new(color)
		burst.Parent = emit
	end

	-- Ribbons: beams laid up the tear, curving out and back. They flow
	-- because the flow texture scrolls (TextureSpeed); the controller sways
	-- their ends.
	if core and core:IsA("BasePart") and not core:FindFirstChild("RibbonA1") then
		local halfW, halfH = core.Size.X / 2, core.Size.Y / 2
		for i = 1, cfg.RibbonCount do
			local side = if i % 2 == 0 then -1 else 1
			local lift = ((i - 1) / math.max(1, cfg.RibbonCount - 1)) * 0.3
			local a0 = Instance.new("Attachment")
			a0.Name = `RibbonA{i}`
			a0.Position = Vector3.new(side * halfW * 0.6, -halfH * (0.75 - lift), 0)
			a0.Parent = core
			local a1 = Instance.new("Attachment")
			a1.Name = `RibbonB{i}`
			a1.Position = Vector3.new(-side * halfW * 0.6, halfH * (0.75 - lift), 0)
			a1.Parent = core
			local beam = Instance.new("Beam")
			beam.Name = `Ribbon{i}`
			beam.Attachment0 = a0
			beam.Attachment1 = a1
			beam.Segments = 16
			beam.CurveSize0 = side * halfW * 2.4
			beam.CurveSize1 = -side * halfW * 2.4
			beam.Width0 = cfg.RibbonWidth
			beam.Width1 = cfg.RibbonWidth * 0.4
			beam.LightEmission = 1
			beam.FaceCamera = true
			beam.Color = ColorSequence.new(color)
			beam.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.2, 0.35),
				NumberSequenceKeypoint.new(0.8, 0.35),
				NumberSequenceKeypoint.new(1, 1),
			})
			if cfg.FlowTexture ~= "" then
				beam.Texture = cfg.FlowTexture
				beam.TextureMode = Enum.TextureMode.Stretch
				beam.TextureSpeed = cfg.FlowTextureSpeed * (if side > 0 then 1 else -1)
				beam.TextureLength = 4
			end
			beam.Parent = core
		end
	end
end

--- Builds a rift standing on `config.Position`. Returns the model, or nil only
--- if it could not even be blocked out (which is a programmer error).
function RiftRig.build(config: Config, parent: Instance): Model
	local prefabCfg = if config.Kind == "EXIT"
		then GameConfig.Rift.ExitPrefab
		else GameConfig.Rift.EntrancePrefab
	local base = CFrame.new(config.Position) * CFrame.Angles(0, config.Yaw or 0, 0)
	local color = RiftRig.colorFor(config.Kind, config.RarityKey)

	local built = PrefabLoader.build({
		AssetKey = prefabCfg.AssetKey,
		Scale = prefabCfg.Scale,
		YawDegrees = prefabCfg.YawDegrees,
		-- Register the tear's ground origin from the asymmetric Scar mesh.
		AnchorPart = "Scar",
		AnchorOffset = prefabCfg.AnchorOffset,
		Styles = styles(),
	}, CONTRACT, base, parent, config.Name)

	local model: Model
	if built then
		model = built.Model
		if #built.Missing > 0 then
			warn(
				`[RiftRig] {prefabCfg.AssetKey} is missing {#built.Missing} contract part(s): `
					.. table.concat(built.Missing, ", ")
			)
		end
		local scar = model:FindFirstChild("Scar", true)
		if scar and scar:IsA("BasePart") then
			model.PrimaryPart = scar
		end
	else
		warn(`[RiftRig] no prefab '{prefabCfg.AssetKey}'; drawing a blockout {config.Kind}`)
		model = buildBlockout(config, base, parent)
	end

	-- Animate a complete rig when it streams in, including its effect anchors.
	model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	model:SetAttribute("RiftKind", config.Kind)
	model:SetAttribute("GroundPosition", config.Position)
	paint(model, color)
	RiftRig.attachEffects(model, color)
	-- Resting look, so an open rift reads correctly even before (or without)
	-- RiftController; a sealed exit overrides it just below.
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			local rest = d:GetAttribute("RestTransparency")
			if type(rest) == "number" then
				d.Transparency = rest
			end
		end
	end

	if config.Kind == "EXIT" then
		RiftRig.seal(model)
	end
	CollectionService:AddTag(model, Constants.NAMES.RIFT_TAG)
	return model
end

--- Hides every part and silences every effect. The exit is built like this and
--- stays like this until `open`: a door that is not there yet must not be
--- visible to a client that is not yet animating it.
function RiftRig.seal(rig: Model): ()
	rig:SetAttribute("OpenedAt", nil)
	rig:SetAttribute("State", "Sealed")
	for _, d in rig:GetDescendants() do
		if d:IsA("BasePart") then
			d.Transparency = 1
		elseif d:IsA("ParticleEmitter") or d:IsA("Beam") or d:IsA("PointLight") then
			d.Enabled = false
		end
	end
end

--- Starts the materialise. `OpenedAt` is SERVER time: every client derives
--- the same progress from it, and a late arrival sees the door already open.
function RiftRig.open(rig: Model): ()
	if rig:GetAttribute("State") ~= "Sealed" then
		return
	end
	rig:SetAttribute("State", "Materialising")
	rig:SetAttribute("OpenedAt", Workspace:GetServerTimeNow())
	task.delay(GameConfig.Rift.MaterialiseSeconds, function()
		if rig.Parent then
			rig:SetAttribute("State", "Open")
		end
	end)
end

--- True once the exit has finished materialising.
function RiftRig.isOpen(rig: Model): boolean
	return rig:GetAttribute("State") == "Open" or rig:GetAttribute("RiftKind") == "ENTRANCE"
end

return RiftRig
