--!strict
-- The shared Expedition Gate component. Biome Blueprint §1.3.
--
-- ONE rig, instanced per use with a config table and reskinned by rarity
-- colour only. Never hand-duplicated per biome -- the Fate Engine (1.5x) and
-- the Expedition Gate (2x) are the same rig at different scales, and every
-- future world portal is too.
--
-- DEVIATION FROM THE BLUEPRINT, deliberate: §1.3 specifies the rings as CSG
-- tori (large cylinder minus smaller cylinder). Runtime SubtractAsync is slow,
-- can fail, and a cylinder minus a cylinder yields an annulus rather than a
-- torus anyway. These rings are built from GameConfig.Portal.RingSegments
-- wedge-free segments arranged radially -- visually equivalent, no CSG cost,
-- and it works identically on mobile. Swap in an authored mesh via MeshId when
-- real art arrives.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)

local PortalRig = {}

export type Config = {
	Name: string,
	Position: Vector3,
	Scale: number,
	Rarity: string,
	PlinthMaterial: Enum.Material,
	OuterMaterial: Enum.Material,
	MeshId: string?,
}

local function makePart(name: string, parent: Instance): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanCollide = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

--- Builds one ring out of radial segments. `axisCFrame` is the ring's centre
--- and orientation; the ring lies in that CFrame's XY plane.
local function buildRing(
	parent: Instance,
	name: string,
	radius: number,
	thickness: number,
	color: Color3,
	material: Enum.Material,
	axisCFrame: CFrame
): Model
	local ring = Instance.new("Model")
	ring.Name = name
	-- The ring rotates about ITS OWN centre, so the centre travels with it.
	-- Rotating about the world origin instead would send the segments into
	-- orbit around (0,0,0) -- correct-looking only for a rig at the origin.
	ring:SetAttribute("Center", axisCFrame)
	ring.Parent = parent

	local segments = GameConfig.Portal.RingSegments
	-- Chord length between adjacent segment centres, so segments meet cleanly.
	local segmentLength = 2 * radius * math.sin(math.pi / segments) * 1.06

	for i = 1, segments do
		local angle = (i - 1) / segments * math.pi * 2
		local offset = CFrame.Angles(0, 0, angle) * CFrame.new(radius, 0, 0) * CFrame.Angles(0, 0, math.pi / 2)
		local segment = makePart(`Segment{i}`, ring)
		segment.Size = Vector3.new(thickness, segmentLength, thickness)
		segment.Color = color
		segment.Material = material
		segment.CFrame = axisCFrame * offset
	end

	return ring
end

--- Creates the rig. Returns the model; animation state lives in attributes so
--- both server and client can read it without another module.
function PortalRig.build(config: Config, parent: Instance): Model
	local cfg = GameConfig.Portal
	local scale = config.Scale
	local rarity = Constants.RARITY[config.Rarity] or Constants.RARITY.COMMON
	local color = rarity.Color

	local model = Instance.new("Model")
	model.Name = config.Name
	model:SetAttribute("Rarity", config.Rarity)
	model:SetAttribute("State", "Idle")
	model:SetAttribute("Scale", scale)
	model.Parent = parent

	local base = config.Position

	-- PLINTH HEIGHT IS CAPPED, and that is a gameplay constraint rather than
	-- an art one. At the Gate's scale an uncapped 1.5-stud plinth stands 18
	-- studs tall -- higher than a Roblox character can jump -- so the portal
	-- became a walled-off monument nobody could reach. Width still scales;
	-- only the step up is capped, so the rig reads as monumental AND is
	-- something you can walk onto.
	local plinthHeight = math.min(cfg.PlinthHeight * scale, cfg.MaxPlinthHeight)

	-- Base plinth: octagonal, blueprint §1.3.
	--
	-- `Shape = Cylinder`, NOT a Part wearing a CylinderMesh. A CylinderMesh is
	-- visual only -- the part keeps its square collision hull, so the corners
	-- block a player standing somewhere that looks like open floor. This was
	-- reported from a playtest as "I cannot walk near the portal, the mesh is
	-- too large but not visible".
	--
	-- PartType.Cylinder's axis is X, so the part is rolled a quarter turn to
	-- stand it up and its Size is (height, diameter, diameter).
	local plinth = makePart("Plinth", model)
	plinth.Size = Vector3.new(plinthHeight, cfg.PlinthDiameter * scale, cfg.PlinthDiameter * scale)
	plinth.Shape = Enum.PartType.Cylinder
	plinth.CFrame = CFrame.new(base + Vector3.new(0, plinthHeight / 2, 0))
		* CFrame.Angles(0, 0, math.pi / 2)
	plinth.Material = config.PlinthMaterial
	plinth.Color = Color3.fromRGB(196, 190, 208)
	plinth.CanCollide = true
	plinth.CastShadow = true
	-- Blueprint §1.3 calls for an octagonal plinth. A true octagon needs CSG or
	-- a mesh; this is a cylinder standing in for it, and is the first thing an
	-- authored plinth mesh should replace. PlinthSides is carried in config so
	-- the intent is not lost.

	-- The outer ring's BOTTOM sits on the plinth's top, so the arch springs
	-- from the floor the player is standing on rather than hovering above it.
	local ringHeight = base + Vector3.new(0, cfg.OuterRingRadius * scale + plinthHeight, 0)
	local axis = CFrame.new(ringHeight)

	local outer = buildRing(
		model,
		"OuterRing",
		cfg.OuterRingRadius * scale,
		cfg.OuterRingThickness * scale,
		Color3.fromRGB(64, 58, 78),
		config.OuterMaterial,
		axis
	)
	outer:SetAttribute("SpinSpeed", 1)

	local inner = buildRing(
		model,
		"InnerRing",
		cfg.InnerRingRadius * scale,
		cfg.InnerRingThickness * scale,
		color,
		Enum.Material.Neon,
		axis
	)
	inner:SetAttribute("SpinSpeed", -1.4)

	-- PortalPlane: the fabric players walk through.
	local plane = makePart("PortalPlane", model)
	plane.Size = Vector3.new(cfg.InnerRingRadius * 2 * scale, cfg.InnerRingRadius * 2 * scale, 0.4)
	plane.CFrame = axis
	plane.Material = Enum.Material.ForceField
	plane.Color = color
	plane.Transparency = cfg.PlanePulseMax
	local planeMesh = Instance.new("SpecialMesh")
	planeMesh.MeshType = Enum.MeshType.Sphere
	planeMesh.Scale = Vector3.new(1, 1, 0.08)
	planeMesh.Parent = plane

	-- RuneRing: 8 plates at the base. Geometric glyphs only -- blueprint §7.2
	-- notes generated lettering is unreliable, so these carry no text.
	local runes = Instance.new("Folder")
	runes.Name = "RuneRing"
	runes.Parent = model
	for i = 1, cfg.RuneCount do
		local angle = (i - 1) / cfg.RuneCount * math.pi * 2
		local rune = makePart(`Rune{i}`, runes)
		rune.Size = Vector3.new(2.2 * scale, 0.3 * scale, 3.4 * scale)
		rune.Material = Enum.Material.Slate
		rune.Color = Color3.fromRGB(88, 82, 104)
		rune.CFrame = CFrame.new(base + Vector3.new(0, plinthHeight + 0.2 * scale, 0))
			* CFrame.Angles(0, angle, 0)
			* CFrame.new(0, 0, -(cfg.PlinthDiameter / 2 - 1.4) * scale)

		local glyph = makePart(`Glyph{i}`, runes)
		glyph.Size = Vector3.new(1.1 * scale, 0.12 * scale, 1.1 * scale)
		glyph.Material = Enum.Material.Neon
		glyph.Color = color
		glyph.Transparency = 0.25
		glyph.CFrame = rune.CFrame * CFrame.new(0, 0.22 * scale, 0) * CFrame.Angles(0, math.pi / 4, 0)
	end

	local emitterAttachment = Instance.new("Attachment")
	emitterAttachment.Name = "EmitterAttachment"
	emitterAttachment.WorldPosition = ringHeight
	emitterAttachment.Parent = plane

	local particles = Instance.new("ParticleEmitter")
	particles.Name = "PortalParticles"
	particles.Rate = cfg.IdleParticleRate
	particles.Lifetime = NumberRange.new(cfg.ParticleLifetimeMin, cfg.ParticleLifetimeMax)
	particles.Color = ColorSequence.new(color)
	particles.Speed = NumberRange.new(2, 5)
	particles.SpreadAngle = Vector2.new(18, 18)
	particles.Size = NumberSequence.new(0.6 * scale)
	particles.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.2, 0.2),
		NumberSequenceKeypoint.new(1, 1),
	})
	particles.EmissionDirection = Enum.NormalId.Top
	particles.Acceleration = Vector3.new(0, 6, 0)
	particles.Parent = emitterAttachment

	local light = Instance.new("PointLight")
	light.Name = "PortalLight"
	light.Color = color
	light.Range = cfg.LightRange * scale
	light.Brightness = cfg.IdleBrightness
	light.Parent = plane

	model.PrimaryPart = plinth
	return model
end

--- Reskins an existing rig to a different rarity. Blueprint §1.3: portals are
--- reskinned by colour, never rebuilt.
function PortalRig.setRarity(model: Model, rarityKey: string): ()
	local rarity = Constants.RARITY[rarityKey]
	if not rarity then
		return
	end
	model:SetAttribute("Rarity", rarityKey)

	local inner = model:FindFirstChild("InnerRing")
	if inner then
		for _, segment in inner:GetChildren() do
			if segment:IsA("BasePart") then
				segment.Color = rarity.Color
			end
		end
	end

	local plane = model:FindFirstChild("PortalPlane")
	if plane and plane:IsA("BasePart") then
		plane.Color = rarity.Color
		local light = plane:FindFirstChild("PortalLight")
		if light and light:IsA("PointLight") then
			light.Color = rarity.Color
		end
		local attachment = plane:FindFirstChild("EmitterAttachment")
		local particles = attachment and attachment:FindFirstChild("PortalParticles")
		if particles and particles:IsA("ParticleEmitter") then
			particles.Color = ColorSequence.new(rarity.Color)
		end
	end

	local runes = model:FindFirstChild("RuneRing")
	if runes then
		for _, child in runes:GetChildren() do
			if child:IsA("BasePart") and child.Name:match("^Glyph") then
				child.Color = rarity.Color
			end
		end
	end
end

--- The 2.5s spin-up. Blueprint §1.3: ring rotation, brightness ramp and a
--- particle spike, played BEFORE the destination banner. Never instant.
function PortalRig.playSpinUp(model: Model, rarityKey: string?): ()
	local cfg = GameConfig.Portal
	if rarityKey then
		PortalRig.setRarity(model, rarityKey)
	end
	model:SetAttribute("State", "SpinUp")

	local plane = model:FindFirstChild("PortalPlane")
	local light = plane and plane:FindFirstChild("PortalLight")
	local attachment = plane and plane:FindFirstChild("EmitterAttachment")
	local particles = attachment and attachment:FindFirstChild("PortalParticles")

	if particles and particles:IsA("ParticleEmitter") then
		particles.Rate = cfg.SpinUpParticleRate
	end

	if light and light:IsA("PointLight") then
		TweenService:Create(
			light,
			TweenInfo.new(cfg.SpinUpSeconds, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
			{ Brightness = cfg.ActiveBrightness * 3 }
		):Play()
	end

	task.delay(cfg.SpinUpSeconds, function()
		if model.Parent then
			PortalRig.setActive(model)
		end
	end)
end

--- Post-spin-up steady state: bright, walkable, active particle rate.
function PortalRig.setActive(model: Model): ()
	local cfg = GameConfig.Portal
	model:SetAttribute("State", "Active")

	local plane = model:FindFirstChild("PortalPlane")
	local light = plane and plane:FindFirstChild("PortalLight")
	local attachment = plane and plane:FindFirstChild("EmitterAttachment")
	local particles = attachment and attachment:FindFirstChild("PortalParticles")

	if particles and particles:IsA("ParticleEmitter") then
		particles.Rate = cfg.ActiveParticleRate
	end
	if light and light:IsA("PointLight") then
		TweenService:Create(light, TweenInfo.new(0.6), { Brightness = cfg.ActiveBrightness }):Play()
	end
end

function PortalRig.setIdle(model: Model): ()
	local cfg = GameConfig.Portal
	model:SetAttribute("State", "Idle")

	local plane = model:FindFirstChild("PortalPlane")
	local light = plane and plane:FindFirstChild("PortalLight")
	local attachment = plane and plane:FindFirstChild("EmitterAttachment")
	local particles = attachment and attachment:FindFirstChild("PortalParticles")

	if particles and particles:IsA("ParticleEmitter") then
		particles.Rate = cfg.IdleParticleRate
	end
	if light and light:IsA("PointLight") then
		TweenService:Create(light, TweenInfo.new(0.8), { Brightness = cfg.IdleBrightness }):Play()
	end
end

--- Drives ring rotation and the plane's pulse. Call once per rig; runs on
--- whichever side invokes it (the client, so animation is free of replication).
function PortalRig.animate(model: Model): RBXScriptConnection
	local cfg = GameConfig.Portal
	local rings = {}
	for _, name in { "OuterRing", "InnerRing" } do
		local ring = model:FindFirstChild(name)
		if ring then
			table.insert(rings, ring)
		end
	end

	local plane = model:FindFirstChild("PortalPlane")
	local elapsed = 0

	return RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		local state = model:GetAttribute("State")
		local speed = if state == "SpinUp" then cfg.SpinUpSpinSpeed else cfg.IdleSpinSpeed

		for _, ring in rings do
			local centre = ring:GetAttribute("Center") :: CFrame?
			if not centre then
				continue
			end
			local ringSpeed = (ring:GetAttribute("SpinSpeed") or 1) * speed
			-- The ring stands in its centre's XY plane, so it spins about that
			-- CFrame's Z axis. Conjugating by the centre keeps the rotation
			-- local to the ring wherever the rig sits in the world.
			local step = centre * CFrame.Angles(0, 0, ringSpeed * dt) * centre:Inverse()
			for _, segment in ring:GetChildren() do
				if segment:IsA("BasePart") then
					segment.CFrame = step * segment.CFrame
				end
			end
		end

		if plane and plane:IsA("BasePart") then
			local t = (math.sin(elapsed / cfg.PlanePulseSeconds * math.pi * 2) + 1) / 2
			plane.Transparency = cfg.PlanePulseMin + (cfg.PlanePulseMax - cfg.PlanePulseMin) * t
		end
	end)
end

return PortalRig
