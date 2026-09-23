--!strict
-- Draws a world's ambience on this client: its sky, atmosphere and grade, a
-- drifting sea of cloud under the map, and motes on the air. All of it is
-- read from the world's Environment (content); AmbienceCore decides the
-- numbers, this only turns them into Instances.
--
-- THE WORLD OWNS THE SCENE. In the finished game an expedition runs on its own
-- server (build spec §7.2), so there is no hub look to protect: whatever sky,
-- haze and post-effects Lighting holds are set aside and the world's replace
-- them outright. Setting them aside rather than destroying them is only for
-- Studio, where the map is built above the hub in the same server and /leave
-- has to hand the hub back looking like the hub.
--
-- Client-only by design. Lighting and a cloud sea are per-screen concerns;
-- nothing here replicates, and the server never pays for a cloud.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local AmbienceCore = require(Root.Core.AmbienceCore)
local GameConfig = require(Root.Core.GameConfig)

local AmbienceController = {}

-- Scene objects a world replaces. Anything of these classes directly under
-- Lighting is set aside on entry -- including the hub's Atmosphere, whose mere
-- existence makes Roblox ignore FogStart/FogEnd, which is how every world
-- used to wear the hub's purple haze.
local SCENE_CLASSES = {
	"Sky",
	"Atmosphere",
	"BloomEffect",
	"SunRaysEffect",
	"ColorCorrectionEffect",
	"BlurEffect",
	"DepthOfFieldEffect",
}

-- Lighting properties this controller writes that ExpeditionController's
-- tracked set does not, so it saves and restores them itself.
local EXTRA_PROPERTIES = { "ExposureCompensation", "ColorShift_Bottom" }

type Layer = {
	Def: any,
	Clouds: { any },
	-- Flat, parallel arrays so one BulkMoveTo moves the whole layer: every
	-- part, the cloud it belongs to, and its offset from that cloud's centre.
	Parts: { BasePart },
	Owner: { any },
	Offset: { any },
	DriftX: number,
	DriftZ: number,
}

local setAside: { { Instance: Instance, Parent: Instance? } } = {}
local created: { Instance } = {}
local savedProperties: { [string]: any } = {}
local layers: { Layer } = {}
local motesAnchor: BasePart? = nil
local stepper: RBXScriptConnection? = nil
local active = false
local random = Random.new()

--- 0..1: how much ambience this device draws, from the player's own graphics
--- setting. Read on entry; a mid-expedition change applies on the next one.
local function quality(): number
	local ok, level = pcall(function()
		return (UserSettings():GetService("UserGameSettings") :: any).SavedQualityLevel.Value
	end)
	return AmbienceCore.qualityScale(if ok then level else 0, GameConfig.Ambience)
end

local function make(className: string, props: { [string]: any }, parent: Instance): Instance
	local instance = Instance.new(className)
	for key, value in props do
		(instance :: any)[key] = value
	end
	instance.Parent = parent
	table.insert(created, instance)
	return instance
end

local function setAsideScene()
	for _, child in Lighting:GetChildren() do
		if table.find(SCENE_CLASSES, child.ClassName) then
			table.insert(setAside, { Instance = child, Parent = child.Parent })
			child.Parent = nil
		end
	end
end

local function buildScene(env: any)
	for _, property in EXTRA_PROPERTIES do
		savedProperties[property] = (Lighting :: any)[property]
	end
	-- Undeclared means neutral, not "whatever the hub had".
	Lighting.ExposureCompensation = env.ExposureCompensation or 0
	Lighting.ColorShift_Bottom = env.ColorShiftBottom or Color3.new(0, 0, 0)

	if env.Sky then
		make("Sky", {
			SunAngularSize = env.Sky.SunAngularSize or 21,
			MoonAngularSize = env.Sky.MoonAngularSize or 11,
			StarCount = env.Sky.StarCount or 3000,
		}, Lighting)
	end
	if env.Atmosphere then
		local a = env.Atmosphere
		make("Atmosphere", {
			Density = a.Density,
			Offset = a.Offset or 0,
			Color = a.Color,
			Decay = a.Decay,
			Glare = a.Glare,
			Haze = a.Haze,
		}, Lighting)
	end
	if env.Bloom then
		make("BloomEffect", {
			Intensity = env.Bloom.Intensity,
			Size = env.Bloom.Size,
			Threshold = env.Bloom.Threshold,
		}, Lighting)
	end
	if env.SunRays then
		make("SunRaysEffect", { Intensity = env.SunRays.Intensity, Spread = env.SunRays.Spread }, Lighting)
	end
	if env.Grade then
		make("ColorCorrectionEffect", {
			Brightness = env.Grade.Brightness,
			Contrast = env.Grade.Contrast,
			Saturation = env.Grade.Saturation,
			TintColor = env.Grade.Tint,
		}, Lighting)
	end
end

local function buildCloudSea(env: any, floorY: number, scale: number, folder: Instance)
	for _, def in env.CloudSea or {} do
		local count = AmbienceCore.scaledCount(def.Count, scale)
		local clouds = AmbienceCore.layoutClouds(def, count, scale, function()
			return random:NextNumber()
		end)
		local shade = def.Shade or def.Color
		local layer: Layer =
			{ Def = def, Clouds = clouds, Parts = {}, Owner = {}, Offset = {}, DriftX = 0, DriftZ = 0 }
		for _, cloud in clouds do
			-- Built once: a cloud's heading never changes, only where it is.
			cloud.Rot = CFrame.Angles(0, cloud.Yaw, 0)
			for _, piece in cloud.Parts do
				local part = Instance.new("Part")
				part.Name = `Cloud{cloud.Style}`
				part.Anchored = true
				part.CanCollide = false
				part.CanQuery = false
				part.CanTouch = false
				part.CastShadow = false
				part.Material = Enum.Material.SmoothPlastic
				-- Lit billows take the layer's colour, the base its underside
				-- shade: that one gradient is most of what reads as volume.
				part.Color = def.Color:Lerp(shade, piece.Shade)
				part.Transparency = math.clamp(def.Transparency + piece.Fade, 0, 0.95)
				part.Size = Vector3.new(piece.Width, piece.Height, piece.Length)
				-- A SpecialMesh sphere takes the part's non-uniform size, so each
				-- piece is a soft ellipsoid rather than a ball or a block.
				local mesh = Instance.new("SpecialMesh")
				mesh.MeshType = Enum.MeshType.Sphere
				mesh.Parent = part
				part.CFrame = CFrame.new(cloud.X + piece.DX, floorY - def.Depth + cloud.Y + piece.DY, cloud.Z + piece.DZ)
					* CFrame.Angles(0, cloud.Yaw, 0)
				part.Parent = folder
				table.insert(layer.Parts, part)
				table.insert(layer.Owner, cloud)
				table.insert(layer.Offset, piece)
			end
		end
		table.insert(layers, layer)
	end
end

local function buildMotes(env: any, scale: number, folder: Instance)
	local m = env.Motes
	if not m then
		return
	end
	local anchor = Instance.new("Part")
	anchor.Name = "Motes"
	anchor.Anchored = true
	anchor.CanCollide = false
	anchor.CanQuery = false
	anchor.CanTouch = false
	anchor.Transparency = 1
	anchor.Size = Vector3.new(160, 60, 160)
	anchor.Parent = folder
	local emitter = Instance.new("ParticleEmitter")
	emitter.Shape = Enum.ParticleEmitterShape.Box
	emitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	emitter.Rate = m.Rate * scale
	emitter.Lifetime = NumberRange.new(m.Lifetime * 0.6, m.Lifetime)
	emitter.Speed = NumberRange.new(m.Speed * 0.5, m.Speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Color = ColorSequence.new(m.Color)
	emitter.LightEmission = 1
	emitter.Size = NumberSequence.new(m.Size)
	emitter.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.2, 0.3),
		NumberSequenceKeypoint.new(0.8, 0.3),
		NumberSequenceKeypoint.new(1, 1),
	})
	emitter.Parent = anchor
	motesAnchor = anchor
end

--- One frame: every layer drifts, and every puff is shown at the copy of
--- itself nearest the camera. BulkMoveTo, because a sea is a hundred parts
--- moving every frame and that is exactly what it exists for.
local function step(dt: number, floorY: number)
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local focus = camera.CFrame.Position
	for _, layer in layers do
		local def = layer.Def
		local heading = math.rad(def.Heading)
		layer.DriftX += math.sin(heading) * def.Speed * dt
		layer.DriftZ -= math.cos(heading) * def.Speed * dt
		-- Wrap each CLOUD's centre once, then hang its pieces off it, so a
		-- cluster crosses the seam whole instead of splitting in two.
		local centres = {}
		for _, cloud in layer.Clouds do
			centres[cloud] = Vector3.new(
				focus.X + AmbienceCore.wrap(cloud.X + layer.DriftX - focus.X, def.Radius),
				floorY - def.Depth + cloud.Y,
				focus.Z + AmbienceCore.wrap(cloud.Z + layer.DriftZ - focus.Z, def.Radius)
			)
		end
		local cframes = table.create(#layer.Parts)
		for i, cloud in layer.Owner do
			local centre = centres[cloud]
			local piece = layer.Offset[i]
			cframes[i] = CFrame.new(centre.X + piece.DX, centre.Y + piece.DY, centre.Z + piece.DZ) * cloud.Rot
		end
		Workspace:BulkMoveTo(layer.Parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
	end
	if motesAnchor then
		motesAnchor.CFrame = CFrame.new(focus)
	end
end

--- Draws a world's ambience. floorY is the map's walk plane (from the
--- expedition payload); the cloud sea hangs below it.
function AmbienceController.enter(env: any, floorY: number)
	AmbienceController.leave()
	if type(env) ~= "table" then
		return
	end
	active = true
	local scale = quality()
	setAsideScene()
	buildScene(env)

	local folder = make("Folder", { Name = "LuckboundAmbience" }, Workspace)
	buildCloudSea(env, floorY, scale, folder)
	buildMotes(env, scale, folder)
	if #layers > 0 or motesAnchor then
		stepper = RunService.RenderStepped:Connect(function(dt)
			step(dt, floorY)
		end)
	end
end

--- Removes everything enter() made and hands back what it set aside. Safe to
--- call when nothing is active.
function AmbienceController.leave()
	if not active then
		return
	end
	active = false
	if stepper then
		stepper:Disconnect()
		stepper = nil
	end
	for i = #created, 1, -1 do
		created[i]:Destroy()
	end
	table.clear(created)
	table.clear(layers)
	motesAnchor = nil
	for _, entry in setAside do
		-- Something may have destroyed it meanwhile (an event ending while the
		-- player was away); a destroyed instance's Parent is locked and
		-- assigning it throws, which would abort the rest of the restore.
		pcall(function()
			entry.Instance.Parent = entry.Parent
		end)
	end
	table.clear(setAside)
	for property, value in savedProperties do
		(Lighting :: any)[property] = value
	end
	table.clear(savedProperties)
end

return AmbienceController
