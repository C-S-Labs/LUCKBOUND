--!strict
-- The scenario atmospheres' effect blocks (Content/Atmospheres): what the
-- base Environment cannot say. AmbienceController draws the sky, haze, grade,
-- cloud sea and motes; this draws the rest, so a scenario reads from the sky:
--
--   Weather       particle streams round the camera (snow, rain, embers, pollen)
--   Pulse         the colour grade beating, breathing or flickering
--   Flashes       lightning: brightness spikes, and bolts into the sea
--   Dome          a shield bubble over the map
--   Searchlights  beams sweeping up from below the islands
--   Plumes        far smoke columns on the horizon
--   Aurora        curtains of light high in the sky
--   Debris        fragments falling past the islands
--   Canopy        a storm roof of cloud above the map
--
-- Client-only scenery: nothing here collides or replicates. Every block is
-- optional; an Environment with none of them draws nothing.

local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local AtmosphereEffects = {}

local folder: Folder? = nil
local conns: { RBXScriptConnection } = {}
local grade: ColorCorrectionEffect? = nil
local baseBrightness = 0

local function part(props: { [string]: any }, parent: Instance): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in props do
		(p :: any)[k] = v
	end
	p.Parent = parent
	return p
end

local function vec(v: any, default: Vector3): Vector3
	return if typeof(v) == "Vector3" then v else default
end

local function col(v: any, default: Color3): Color3
	return if typeof(v) == "Color3" then v else default
end

local function num(v: any, default: number): number
	return if type(v) == "number" then v else default
end

-- ---- Weather: emitters on a box that follows the camera ------------------------

local function buildWeather(list: any, root: Instance)
	if type(list) ~= "table" or #list == 0 then
		return
	end
	local anchor = part({ Name = "WeatherAnchor", Transparency = 1, Size = Vector3.new(1, 1, 1) }, root)
	for _, w in list do
		local box = vec(w.Box, Vector3.new(160, 60, 160))
		local host = part({ Name = w.Name or "Weather", Transparency = 1, Size = box }, anchor)
		local e = Instance.new("ParticleEmitter")
		e.Name = w.Name or "Weather"
		e.Rate = num(w.Rate, 20)
		e.Lifetime = NumberRange.new(num(w.Lifetime, 6) * 0.7, num(w.Lifetime, 6))
		e.Speed = NumberRange.new(num(w.Speed, 4) * 0.7, num(w.Speed, 4))
		local size = num(w.Size, 0.3)
		local streak = num(w.Streak, 0)
		e.Size = NumberSequence.new(size)
		e.Color = ColorSequence.new(col(w.Color, Color3.new(1, 1, 1)))
		e.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.15, num(w.Transparency, 0.2)),
			NumberSequenceKeypoint.new(0.85, num(w.Transparency, 0.2)),
			NumberSequenceKeypoint.new(1, 1),
		})
		e.LightEmission = num(w.Emission, 0)
		local dir = vec(w.Direction, Vector3.new(0, -1, 0))
		e.Acceleration = dir.Unit * num(w.Speed, 4) * 0.3
		e.SpreadAngle = Vector2.new(num(w.Spread, 20), num(w.Spread, 20))
		e.EmissionDirection = if dir.Y >= 0 then Enum.NormalId.Top else Enum.NormalId.Bottom
		e.Shape = Enum.ParticleEmitterShape.Box
		e.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
		e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
		if streak > 0 then
			e.Orientation = Enum.ParticleOrientation.VelocityParallel
			e.Squash = NumberSequence.new(streak)
		end
		e.Parent = host
	end
	table.insert(conns, RunService.RenderStepped:Connect(function()
		local cam = Workspace.CurrentCamera
		if cam then
			anchor.CFrame = CFrame.new(cam.CFrame.Position)
			for _, c in anchor:GetChildren() do
				(c :: BasePart).CFrame = anchor.CFrame
			end
		end
	end))
end

-- ---- Pulse and Flashes: the grade and the light, over time ---------------------

local function pulseValue(shape: string, t: number, period: number): number
	local x = (t % period) / period
	if shape == "Beat" then
		return math.max(0, 1 - x * 4) -- a hard beat, then quiet
	elseif shape == "Flicker" then
		return if math.noise(t * 3.1, 0.5) > 0.25 then 1 else 0
	end
	return 0.5 + 0.5 * math.sin(x * 2 * math.pi) -- Sine: breathing
end

local function buildPulseAndFlashes(env: any, root: Instance, centre: Vector3)
	local pulse, flashes = env.Pulse, env.Flashes
	if type(pulse) ~= "table" and type(flashes) ~= "table" then
		return
	end
	grade = Instance.new("ColorCorrectionEffect")
	local g = grade :: ColorCorrectionEffect
	g.Name = "LuckboundAtmospherePulse"
	g.Parent = Lighting
	baseBrightness = Lighting.Brightness
	local started = os.clock()
	local nextFlash = os.clock() + 2
	local flashUntil = 0
	local flashCfg = if type(flashes) == "table" then flashes else nil
	local bolts: { Part } = {}
	table.insert(conns, RunService.RenderStepped:Connect(function()
		local t = os.clock() - started
		local tint = Color3.new(1, 1, 1)
		if type(pulse) == "table" then
			local v = pulseValue(pulse.Shape or "Sine", t, num(pulse.Period, 3)) * num(pulse.Amount, 0.2)
			tint = Color3.new(1, 1, 1):Lerp(col(pulse.Tint, Color3.new(1, 1, 1)), math.clamp(v * 3, 0, 1))
			g.Brightness = -v * 0.15
		end
		if flashCfg then
			local now = os.clock()
			if now >= nextFlash then
				flashUntil = now + num(flashCfg.Duration, 0.18)
				nextFlash = now + math.random() * (num(flashCfg.IntervalMax, 10) - num(flashCfg.IntervalMin, 4))
					+ num(flashCfg.IntervalMin, 4)
				for _ = 1, num(flashCfg.Bolts, 0) do
					local a = math.random() * 2 * math.pi
					local d = 500 + math.random() * 900
					local x, z = centre.X + math.cos(a) * d, centre.Z + math.sin(a) * d
					local h = 700
					local b = part({
						Name = "Bolt",
						Material = Enum.Material.Neon,
						Color = col(flashCfg.Color, Color3.new(0.85, 0.9, 1)),
						Size = Vector3.new(3, h, 3),
						CFrame = CFrame.new(x, centre.Y + h / 2 - 350, z) * CFrame.Angles(0, 0, math.rad(math.random(-8, 8))),
					}, root)
					table.insert(bolts, b)
				end
			end
			if now < flashUntil then
				Lighting.Brightness = baseBrightness + num(flashCfg.Brightness, 2.5)
				tint = tint:Lerp(col(flashCfg.Color, Color3.new(0.85, 0.9, 1)), 0.5)
			else
				Lighting.Brightness = baseBrightness
				for _, b in bolts do
					b:Destroy()
				end
				table.clear(bolts)
			end
		end
		g.TintColor = tint
	end))
end

-- ---- Set pieces in the sky ------------------------------------------------------

local function buildDome(d: any, root: Instance, centre: Vector3)
	if type(d) ~= "table" then
		return
	end
	local r = num(d.Radius, 1100)
	part({
		Name = "Dome",
		Shape = Enum.PartType.Ball,
		Size = Vector3.new(r * 2, r * 2, r * 2),
		CFrame = CFrame.new(centre),
		Material = if d.Material == "ForceField" then Enum.Material.ForceField else Enum.Material.Neon,
		Color = col(d.Color, Color3.fromRGB(255, 64, 76)),
		Transparency = num(d.Transparency, 0.86),
	}, root)
end

local function buildSearchlights(s: any, root: Instance, centre: Vector3)
	if type(s) ~= "table" then
		return
	end
	local beams = {}
	local n = num(s.Count, 6)
	for i = 1, n do
		local b = part({
			Name = "Searchlight",
			Material = Enum.Material.Neon,
			Color = col(s.Color, Color3.fromRGB(255, 96, 104)),
			Transparency = 0.7,
			Size = Vector3.new(num(s.Width, 22), num(s.Length, 1500), num(s.Width, 22)),
		}, root)
		table.insert(beams, { Part = b, Phase = i / n * 2 * math.pi })
	end
	local started = os.clock()
	local radius, length = num(s.Radius, 620), num(s.Length, 1500)
	local sweep, tilt = math.rad(num(s.Sweep, 14)), math.rad(num(s.Tilt, 24))
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = os.clock() - started
		for _, beam in beams do
			local a = beam.Phase
			local base = centre + Vector3.new(math.cos(a) * radius, -150, math.sin(a) * radius)
			local swing = math.sin(t * 0.4 + beam.Phase * 3) * sweep
			local cf = CFrame.new(base) * CFrame.Angles(0, -a + swing, 0) * CFrame.Angles(0, 0, tilt)
			beam.Part.CFrame = cf * CFrame.new(0, length / 2, 0)
		end
	end))
end

local function buildPlumes(pl: any, root: Instance, centre: Vector3)
	if type(pl) ~= "table" then
		return
	end
	local rng = Random.new(7)
	for i = 1, num(pl.Count, 5) do
		local a = i / num(pl.Count, 5) * 2 * math.pi + rng:NextNumber(-0.3, 0.3)
		local d = rng:NextNumber(num(pl.DistanceMin, 1300), num(pl.DistanceMax, 2300))
		local x, z = centre.X + math.cos(a) * d, centre.Z + math.sin(a) * d
		local h, w = num(pl.Height, 900), num(pl.Width, 150)
		local steps = 7
		for k = 0, steps do
			local f = k / steps
			local s = w * (0.6 + f * 1.4)
			part({
				Name = "Plume",
				Shape = Enum.PartType.Ball,
				Size = Vector3.new(s, s, s),
				CFrame = CFrame.new(x + f * h * 0.25, centre.Y - 400 + f * h, z),
				Material = if k == 0 then Enum.Material.Neon else Enum.Material.SmoothPlastic,
				Color = if k == 0 then col(pl.Glow, Color3.fromRGB(255, 132, 60))
					else col(pl.Color, Color3.fromRGB(92, 86, 92)):Lerp(col(pl.Shade, Color3.fromRGB(54, 50, 58)), f),
				Transparency = 0.15 + f * 0.5,
			}, root)
		end
	end
end

local function buildAurora(au: any, root: Instance, centre: Vector3)
	if type(au) ~= "table" then
		return
	end
	local curtains = {}
	for i = 1, num(au.Count, 3) do
		local a = i * 1.9
		local c = part({
			Name = "Aurora",
			Material = Enum.Material.Neon,
			Color = col(au.Color, Color3.fromRGB(168, 118, 255)):Lerp(col(au.Tip, Color3.fromRGB(110, 236, 255)), i / 4),
			Transparency = num(au.Transparency, 0.5),
			Size = Vector3.new(num(au.Length, 1900), num(au.Drop, 240), 4),
		}, root)
		table.insert(curtains, { Part = c, Angle = a })
	end
	local started = os.clock()
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = (os.clock() - started) * num(au.Speed, 0.2)
		for i, c in curtains do
			local y = centre.Y + num(au.Height, 420) + math.sin(t + i) * 30
			c.Part.CFrame = CFrame.new(centre.X, y, centre.Z) * CFrame.Angles(0, c.Angle + math.sin(t * 0.5 + i) * 0.2, 0)
				* CFrame.new(0, 0, 400 + i * 120)
		end
	end))
end

local function buildDebris(db: any, root: Instance, centre: Vector3)
	if type(db) ~= "table" then
		return
	end
	local pool = {}
	for i = 1, 14 do
		local s = math.random(num(db.SizeMin, 3) * 10, num(db.SizeMax, 14) * 10) / 10
		table.insert(pool, {
			Part = part({
				Name = "Debris",
				Size = Vector3.new(s, s * 0.6, s * 0.8),
				Color = col(db.Color, Color3.fromRGB(206, 212, 224)),
				Material = Enum.Material.Slate,
				CFrame = CFrame.new(centre + Vector3.new(0, -2000, 0)),
			}, root),
			Y = -1e9,
		})
	end
	local radius, speed, spin = num(db.Radius, 700), num(db.Speed, 28), math.rad(num(db.Spin, 70))
	local rate = num(db.Rate, 2.5)
	local acc = 0
	table.insert(conns, RunService.Heartbeat:Connect(function(dt)
		acc += dt * rate
		for _, d in pool do
			if d.Y < centre.Y - 700 and acc >= 1 then
				acc -= 1
				local a = math.random() * 2 * math.pi
				local r = math.random() * radius
				d.X, d.Z, d.Y = centre.X + math.cos(a) * r, centre.Z + math.sin(a) * r, centre.Y + 120
			end
			if d.Y > centre.Y - 700 then
				d.Y -= speed * dt
				d.Part.CFrame = CFrame.new(d.X, d.Y, d.Z) * CFrame.Angles(os.clock() * spin, os.clock() * spin * 0.7, 0)
			end
		end
	end))
end

local function buildCanopy(list: any, root: Instance, centre: Vector3)
	if type(list) ~= "table" then
		return
	end
	local rng = Random.new(11)
	for _, layer in list do
		for _ = 1, num(layer.Count, 12) do
			local a = rng:NextNumber(0, 2 * math.pi)
			local r = rng:NextNumber(0, num(layer.Radius, 2000))
			local s = rng:NextNumber(num(layer.SizeMin, 400), num(layer.SizeMax, 700))
			part({
				Name = "Canopy",
				Shape = Enum.PartType.Ball,
				Size = Vector3.new(s, s * 0.22, s * 0.8),
				CFrame = CFrame.new(centre.X + math.cos(a) * r, centre.Y + num(layer.Height, 520), centre.Z + math.sin(a) * r),
				Color = col(layer.Color, Color3.fromRGB(70, 76, 92)),
				Material = Enum.Material.SmoothPlastic,
				Transparency = num(layer.Transparency, 0.1),
			}, root)
		end
	end
end

--- Draws every effect block the Environment carries, centred on `centre`
--- (the map). Replaces whatever a previous call drew.
function AtmosphereEffects.enter(env: any, centre: Vector3)
	AtmosphereEffects.leave()
	if type(env) ~= "table" then
		return
	end
	local root = Instance.new("Folder")
	root.Name = "LuckboundAtmosphere"
	root.Parent = Workspace
	folder = root
	buildWeather(env.Weather, root)
	buildPulseAndFlashes(env, root, centre)
	buildDome(env.Dome, root, centre)
	buildSearchlights(env.Searchlights, root, centre)
	buildPlumes(env.Plumes, root, centre)
	buildAurora(env.Aurora, root, centre)
	buildDebris(env.Debris, root, centre)
	buildCanopy(env.Canopy, root, centre)
end

function AtmosphereEffects.leave()
	for _, c in conns do
		c:Disconnect()
	end
	table.clear(conns)
	if grade then
		Lighting.Brightness = baseBrightness ~= 0 and baseBrightness or Lighting.Brightness
		grade:Destroy()
		grade = nil
	end
	if folder then
		folder:Destroy()
		folder = nil
	end
end

return AtmosphereEffects
