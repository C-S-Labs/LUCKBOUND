--!strict
-- The scenario atmospheres' effect blocks (Content/Atmospheres): what the
-- base Environment cannot say. AmbienceController draws the sky, haze, grade,
-- cloud sea and motes; this draws the rest, and every effect COMES OUT OF
-- SOMETHING (owner playtest, 2026-09-23): an atmosphere prop from the prop
-- library (assets/source/worlds/sky_citadel/build_sky_citadel_atmosphere_props.py),
-- or a plain stand-in shape if that mesh has not been imported yet.
--
--   Weather       particle streams round the camera
--   Pulse         the colour grade beating, breathing or flickering
--   Flashes       lightning striking storm conductors round the map; circling stormhawks
--   Dome          a shield of panels, visible from inside, raised by pylons
--   Searchlights  beams from hovering security probes
--   Plumes        smoke rising from burning raider wrecks
--   Aurora        curtains streaming from floating aurora prisms
--   Debris        chunks of the citadel falling past; broken anti-grav rings
--   Canopy        a storm roof of cloud above the map
--   Drift         floating things a scenario leaves in the air (ice floes, seed pods)
--   Tint          (optional) a whole-chunk tint on the map's meshes (/tint)
--
-- Client-only scenery: nothing here collides or replicates.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local AtmosphereEffects = {}

local folder: Folder? = nil
local conns: { RBXScriptConnection } = {}
local grade: ColorCorrectionEffect? = nil
local baseBrightness: number? = nil
local tinted: { [BasePart]: Color3 } = {}
AtmosphereEffects.tintEnabled = false

local function num(v: any, d: number): number
	return if type(v) == "number" then v else d
end
local function col(v: any, d: Color3): Color3
	return if typeof(v) == "Color3" then v else d
end
local function vec(v: any, d: Vector3): Vector3
	return if typeof(v) == "Vector3" then v else d
end

local function part(props: { [string]: any }, parent: Instance): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	for k, v in props do
		(p :: any)[k] = v
	end
	p.Parent = parent
	return p
end

--- An atmosphere prop by name from the imported library, sized `size`
--- (longest side), or a stand-in shape when it has not been imported.
local function prop(name: string, size: number, fallback: { [string]: any }, parent: Instance): BasePart
	local lib = ReplicatedStorage:FindFirstChild("LuckboundProps")
	local src = lib and lib:FindFirstChild(name, true)
	if src and src:IsA("BasePart") then
		local p = src:Clone()
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		local s = p.Size
		p.Size = s * (size / math.max(s.X, s.Y, s.Z))
		p.Parent = parent
		return p
	end
	return part(fallback, parent)
end

local function ring(centre: Vector3, r: number, a: number, dy: number): Vector3
	return centre + Vector3.new(math.cos(a) * r, dy, math.sin(a) * r)
end

-- ---- Weather ----------------------------------------------------------------------

local function buildWeather(list: any, root: Instance)
	if type(list) ~= "table" or #list == 0 then
		return
	end
	local hosts = {}
	for _, w in list do
		local host = part({ Name = w.Name or "Weather", Transparency = 1, Size = vec(w.Box, Vector3.new(160, 60, 160)) }, root)
		local e = Instance.new("ParticleEmitter")
		e.Rate = num(w.Rate, 20)
		e.Lifetime = NumberRange.new(num(w.Lifetime, 6) * 0.7, num(w.Lifetime, 6))
		e.Speed = NumberRange.new(num(w.Speed, 4) * 0.7, num(w.Speed, 4))
		e.Size = NumberSequence.new(num(w.Size, 0.3))
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
		e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
		if num(w.Streak, 0) > 0 then
			e.Orientation = Enum.ParticleOrientation.VelocityParallel
			e.Squash = NumberSequence.new(num(w.Streak, 0))
		end
		e.Parent = host
		table.insert(hosts, host)
	end
	table.insert(conns, RunService.RenderStepped:Connect(function()
		local cam = Workspace.CurrentCamera
		if cam then
			for _, h in hosts do
				h.CFrame = CFrame.new(cam.CFrame.Position)
			end
		end
	end))
end

-- ---- Lightning: strikes on storm conductors, and the stormhawks ---------------------

local function boltPath(from: Vector3, to: Vector3, rng: Random, root: Instance, color: Color3): { BasePart }
	local out = {}
	local steps = 8
	local prev = from
	for i = 1, steps do
		local f = i / steps
		local p = from:Lerp(to, f)
		if i < steps then
			p += Vector3.new(rng:NextNumber(-18, 18), 0, rng:NextNumber(-18, 18))
		end
		local len = (p - prev).Magnitude
		table.insert(out, part({
			Name = "Bolt",
			Material = Enum.Material.Neon,
			Color = color,
			Size = Vector3.new(4, 4, len),
			CFrame = CFrame.lookAt((prev + p) / 2, p),
		}, root))
		prev = p
	end
	return out
end

local function buildPulseAndFlashes(env: any, root: Instance, centre: Vector3)
	local pulse, flashes = env.Pulse, env.Flashes
	if type(pulse) ~= "table" and type(flashes) ~= "table" then
		return
	end
	local g = Instance.new("ColorCorrectionEffect")
	g.Name = "LuckboundAtmospherePulse"
	g.Parent = Lighting
	grade = g
	baseBrightness = Lighting.Brightness
	local rng = Random.new()
	-- storm conductors round the map: what the lightning strikes
	local targets: { Vector3 } = {}
	if type(flashes) == "table" and num(flashes.Bolts, 0) > 0 then
		for i = 1, 5 do
			local a = i / 5 * 2 * math.pi + 0.4
			local base = ring(centre, rng:NextNumber(260, 420), a, -60)
			local c = prop("atm_storm_conductor", 80, {
				Name = "StormConductor", Material = Enum.Material.Slate, Color = Color3.fromRGB(84, 92, 110),
				Size = Vector3.new(12, 80, 12),
			}, root)
			c.CFrame = CFrame.new(base + Vector3.new(0, 40, 0))
			table.insert(targets, base + Vector3.new(0, 80, 0))
		end
	end
	local started = os.clock()
	local nextFlash = os.clock() + 1.5
	local flashUntil = 0
	local bolts: { BasePart } = {}
	local light: PointLight? = nil
	table.insert(conns, RunService.RenderStepped:Connect(function()
		local t = os.clock() - started
		local tint = Color3.new(1, 1, 1)
		local bright = 0
		if type(pulse) == "table" then
			local x = (t % num(pulse.Period, 3)) / num(pulse.Period, 3)
			local v = if pulse.Shape == "Beat" then math.max(0, 1 - x * 4)
				elseif pulse.Shape == "Flicker" then (if math.noise(t * 3.1, 0.5) > 0.25 then 1 else 0)
				else 0.5 + 0.5 * math.sin(x * 2 * math.pi)
			v *= num(pulse.Amount, 0.2)
			tint = tint:Lerp(col(pulse.Tint, Color3.new(1, 1, 1)), math.clamp(v * 3, 0, 1))
			bright = -v * 0.15
		end
		if type(flashes) == "table" then
			local now = os.clock()
			if now >= nextFlash then
				flashUntil = now + math.max(0.25, num(flashes.Duration, 0.18))
				nextFlash = now + rng:NextNumber(num(flashes.IntervalMin, 4), num(flashes.IntervalMax, 10))
				if #targets > 0 then
					for _ = 1, math.max(1, num(flashes.Bolts, 1)) do
						local target = targets[rng:NextInteger(1, #targets)]
						for _, b in boltPath(target + Vector3.new(0, 700, 0), target, rng, root,
							col(flashes.Color, Color3.fromRGB(210, 222, 255))) do
							table.insert(bolts, b)
						end
						local l = Instance.new("PointLight")
						l.Range = 60
						l.Brightness = 8
						l.Color = col(flashes.Color, Color3.fromRGB(210, 222, 255))
						l.Parent = bolts[#bolts]
						light = l
					end
				end
			end
			if now < flashUntil then
				bright += 0.35
				tint = tint:Lerp(col(flashes.Color, Color3.fromRGB(210, 222, 255)), 0.45)
				Lighting.Brightness = (baseBrightness or 2) + num(flashes.Brightness, 2.5)
			else
				Lighting.Brightness = baseBrightness or Lighting.Brightness
				for _, b in bolts do
					b:Destroy()
				end
				table.clear(bolts)
				light = nil
			end
		end
		g.TintColor = tint
		g.Brightness = bright
	end))
	-- the raptor circling, when this is its storm
	if type(flashes) == "table" and num(flashes.Bolts, 0) > 0 then
		local hawks = {}
		for i = 1, 3 do
			local h = prop("atm_stormhawk", 40, {
				Name = "Stormhawk", Color = Color3.fromRGB(60, 64, 80), Size = Vector3.new(38, 4, 18),
			}, root)
			table.insert(hawks, { Part = h, Phase = i / 3 * 2 * math.pi, R = 180 + i * 90, Y = 120 + i * 40 })
		end
		table.insert(conns, RunService.Heartbeat:Connect(function()
			local t = os.clock() - started
			for _, hk in hawks do
				local a = hk.Phase + t * 0.12
				local p = ring(centre, hk.R, a, hk.Y + math.sin(t + hk.Phase) * 12)
				local ahead = ring(centre, hk.R, a + 0.05, hk.Y)
				hk.Part.CFrame = CFrame.lookAt(p, ahead) * CFrame.Angles(0, math.rad(90), math.rad(-18))
			end
		end))
	end
end

-- ---- Lockdown: the dome, its pylons, and the probes' searchlights -----------------------

local function buildDome(d: any, root: Instance, centre: Vector3)
	if type(d) ~= "table" then
		return
	end
	-- A ball part is not drawn from inside. The dome is PANELS -- thin slabs
	-- are drawn from both sides -- on a hemisphere, so it reads from the deck.
	local R = num(d.Radius, 1100)
	local colour = col(d.Color, Color3.fromRGB(255, 64, 76))
	local mat = if d.Material == "ForceField" then Enum.Material.ForceField else Enum.Material.Neon
	local rings, segs = 8, 24
	for i = 0, rings - 1 do
		local e0 = i / rings * math.pi / 2
		local e1 = (i + 1) / rings * math.pi / 2
		local em = (e0 + e1) / 2
		local rr = R * math.cos(em)
		local h = R * (e1 - e0) * 1.02
		local w = 2 * math.pi * rr / segs * 1.04
		for j = 0, segs - 1 do
			local a = (j + 0.5) / segs * 2 * math.pi
			local pos = centre + Vector3.new(math.cos(a) * rr, R * math.sin(em) - 200, math.sin(a) * rr)
			part({
				Name = "DomePanel",
				Material = mat,
				Color = colour,
				Transparency = num(d.Transparency, 0.86),
				Size = Vector3.new(w, h, 1),
				CFrame = CFrame.lookAt(pos, centre + Vector3.new(0, -200, 0)),
			}, root)
		end
	end
	for i = 1, 6 do
		local a = i / 6 * 2 * math.pi
		local py = prop("atm_dome_pylon", 60, {
			Name = "DomePylon", Material = Enum.Material.Metal, Color = Color3.fromRGB(70, 76, 88),
			Size = Vector3.new(10, 60, 10),
		}, root)
		py.CFrame = CFrame.new(ring(centre, R * 0.98, a, -200 + 30))
	end
end

local function buildSearchlights(s: any, root: Instance, centre: Vector3)
	if type(s) ~= "table" then
		return
	end
	local n = num(s.Count, 6)
	local items = {}
	for i = 1, n do
		local probe = prop("atm_security_probe", 9, {
			Name = "SecurityProbe", Shape = Enum.PartType.Ball, Material = Enum.Material.Metal,
			Color = Color3.fromRGB(70, 76, 88), Size = Vector3.new(5, 5, 5),
		}, root)
		local beam = part({
			Name = "Searchlight",
			Material = Enum.Material.Neon,
			Color = col(s.Color, Color3.fromRGB(255, 96, 104)),
			Transparency = 0.72,
			Size = Vector3.new(num(s.Width, 22) * 0.35, num(s.Length, 1500), num(s.Width, 22) * 0.35),
		}, root)
		table.insert(items, { Probe = probe, Beam = beam, Phase = i / n * 2 * math.pi })
	end
	local started = os.clock()
	local radius, length = num(s.Radius, 620) * 0.6, num(s.Length, 1500)
	local sweep, tilt = math.rad(num(s.Sweep, 14)), math.rad(num(s.Tilt, 24))
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = os.clock() - started
		for _, it in items do
			-- the probe drifts on its station; the beam leaves its lens and sweeps the sky
			local a = it.Phase + t * 0.05
			local base = ring(centre, radius, a, 40 + math.sin(t * 0.8 + it.Phase) * 6)
			it.Probe.CFrame = CFrame.new(base)
			local swing = math.sin(t * 0.4 + it.Phase * 3) * sweep
			local aim = CFrame.new(base) * CFrame.Angles(0, -a + swing, 0) * CFrame.Angles(0, 0, tilt)
			it.Beam.CFrame = aim * CFrame.new(0, 4 + length / 2, 0)
		end
	end))
end

-- ---- Siege: smoke from burning wrecks ------------------------------------------------

local function buildPlumes(pl: any, root: Instance, centre: Vector3)
	if type(pl) ~= "table" then
		return
	end
	local rng = Random.new(7)
	for i = 1, num(pl.Count, 5) do
		local a = i / num(pl.Count, 5) * 2 * math.pi + rng:NextNumber(-0.3, 0.3)
		local d = rng:NextNumber(num(pl.DistanceMin, 1300), num(pl.DistanceMax, 2300)) * 0.45
		local base = ring(centre, d, a, -90)
		local wreck = prop(if i % 2 == 0 then "atm_wreck_stern" else "atm_burning_wreck", 60, {
			Name = "Wreck", Material = Enum.Material.Wood, Color = Color3.fromRGB(158, 74, 52),
			Size = Vector3.new(60, 14, 16),
		}, root)
		wreck.CFrame = CFrame.new(base) * CFrame.Angles(0, a, math.rad(rng:NextNumber(-15, 15)))
		local h, w = num(pl.Height, 900) * 0.7, num(pl.Width, 150) * 0.45
		for k = 0, 8 do
			local f = k / 8
			local s = w * (0.5 + f * 1.6)
			part({
				Name = "Plume",
				Shape = Enum.PartType.Ball,
				Size = Vector3.new(s, s, s),
				CFrame = CFrame.new(base + Vector3.new(f * h * 0.3, 10 + f * h, f * h * 0.1)),
				Material = if k == 0 then Enum.Material.Neon else Enum.Material.SmoothPlastic,
				Color = if k == 0 then col(pl.Glow, Color3.fromRGB(255, 132, 60))
					else col(pl.Color, Color3.fromRGB(92, 86, 92)):Lerp(col(pl.Shade, Color3.fromRGB(54, 50, 58)), f),
				Transparency = 0.1 + f * 0.55,
			}, root)
		end
		local fire = Instance.new("Fire")
		fire.Size = 20
		fire.Heat = 18
		fire.Parent = wreck
	end
end

-- ---- Aether: curtains from prisms --------------------------------------------------

local function buildAurora(au: any, root: Instance, centre: Vector3)
	if type(au) ~= "table" then
		return
	end
	local items = {}
	for i = 1, num(au.Count, 3) do
		local c = part({
			Name = "Aurora",
			Material = Enum.Material.Neon,
			Color = col(au.Color, Color3.fromRGB(168, 118, 255)):Lerp(col(au.Tip, Color3.fromRGB(110, 236, 255)), i / 4),
			Transparency = num(au.Transparency, 0.5),
			Size = Vector3.new(num(au.Length, 1900) * 0.5, num(au.Drop, 240), 3),
		}, root)
		local pr = prop("atm_aurora_prism", 26, {
			Name = "AuroraPrism", Material = Enum.Material.Glass, Color = Color3.fromRGB(190, 150, 255),
			Size = Vector3.new(8, 24, 8),
		}, root)
		table.insert(items, { Curtain = c, Prism = pr, Angle = i * 2.1 })
	end
	local started = os.clock()
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = (os.clock() - started) * num(au.Speed, 0.2)
		for i, it in items do
			local y = num(au.Height, 420) * 0.55 + math.sin(t + i) * 20
			local cf = CFrame.new(centre + Vector3.new(0, y, 0)) * CFrame.Angles(0, it.Angle + math.sin(t * 0.5 + i) * 0.2, 0)
				* CFrame.new(0, 0, 320 + i * 90)
			it.Curtain.CFrame = cf
			-- the prism at the curtain's end, the light streaming out of it
			it.Prism.CFrame = cf * CFrame.new(-it.Curtain.Size.X / 2, 0, 0) * CFrame.Angles(0, t, 0)
		end
	end))
end

-- ---- Unmooring: the citadel falling away ----------------------------------------------

local function buildDebris(db: any, root: Instance, centre: Vector3)
	if type(db) ~= "table" then
		return
	end
	local pool = {}
	for _ = 1, 12 do
		local s = math.random(num(db.SizeMin, 3) * 10, num(db.SizeMax, 14) * 10) / 10
		local p = prop("atm_falling_masonry", s, {
			Name = "Debris", Material = Enum.Material.Slate, Color = col(db.Color, Color3.fromRGB(206, 212, 224)),
			Size = Vector3.new(s, s * 0.6, s * 0.8),
		}, root)
		table.insert(pool, { Part = p, Y = -1e9, X = 0, Z = 0 })
	end
	for i = 1, 3 do
		local r = prop("atm_broken_ring", 28, {
			Name = "BrokenRing", Material = Enum.Material.Neon, Color = Color3.fromRGB(120, 200, 255),
			Size = Vector3.new(26, 3, 14),
		}, root)
		r.CFrame = CFrame.new(ring(centre, 240 + i * 80, i * 2.2, -30 + i * 25)) * CFrame.Angles(math.rad(20 * i), i, 0)
	end
	local radius, speed, spin, rate = num(db.Radius, 700) * 0.6, num(db.Speed, 28), math.rad(num(db.Spin, 70)),
		num(db.Rate, 2.5)
	local acc = 0
	table.insert(conns, RunService.Heartbeat:Connect(function(dt)
		acc += dt * rate
		for _, d in pool do
			if d.Y < centre.Y - 600 and acc >= 1 then
				acc -= 1
				local a = math.random() * 2 * math.pi
				local r = 120 + math.random() * radius
				d.X, d.Z, d.Y = centre.X + math.cos(a) * r, centre.Z + math.sin(a) * r, centre.Y + 60
			end
			if d.Y > centre.Y - 600 then
				d.Y -= speed * dt
				d.Part.CFrame = CFrame.new(d.X, d.Y, d.Z) * CFrame.Angles(os.clock() * spin, os.clock() * spin * 0.7, 0)
			end
		end
	end))
end

-- ---- Drift: what floats in a scenario's air (Rime floes, Reclaimed pods) --------------

local DRIFT = {
	-- atmosphere id is not passed here; the Environment's own Weather names say
	-- which air this is, so drift keys off them
	SNOW = { Name = "atm_ice_floe", Size = 34, Count = 5, Color = Color3.fromRGB(150, 200, 230), Y = -40 },
	POLLEN = { Name = "atm_seed_pod", Size = 12, Count = 10, Color = Color3.fromRGB(118, 160, 86), Y = 30 },
}

local function driftFor(env: any): any
	for _, w in (if type(env.Weather) == "table" then env.Weather else {}) do
		local n = string.upper(tostring(w.Name or ""))
		if string.find(n, "SNOW") then
			return DRIFT.SNOW
		elseif string.find(n, "POLLEN") or string.find(n, "PETAL") or string.find(n, "SEED") then
			return DRIFT.POLLEN
		end
	end
	return nil
end

local function buildDrift(env: any, root: Instance, centre: Vector3)
	local d = driftFor(env)
	if not d then
		return
	end
	local items = {}
	for i = 1, d.Count do
		local p = prop(d.Name, d.Size, {
			Name = "Drift", Material = Enum.Material.Glass, Color = d.Color,
			Size = Vector3.new(d.Size, d.Size * 0.3, d.Size * 0.8),
		}, root)
		table.insert(items, { Part = p, A = i / d.Count * 2 * math.pi, R = 180 + (i % 3) * 110, Y = d.Y + (i % 4) * 25 })
	end
	local started = os.clock()
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = os.clock() - started
		for _, it in items do
			local a = it.A + t * 0.015
			it.Part.CFrame = CFrame.new(ring(centre, it.R, a, it.Y + math.sin(t * 0.5 + it.A) * 5))
				* CFrame.Angles(0, t * 0.05 + it.A, math.sin(t * 0.3 + it.A) * 0.05)
		end
	end))
end

-- ---- Canopy ----------------------------------------------------------------------

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
				Transparency = num(layer.Transparency, 0.1),
			}, root)
		end
	end
end

-- ---- Tint: a whole-chunk colour on the map's meshes (/tint to test) -------------------

local function applyTint(env: any, stageName: string?)
	for p, c in tinted do
		if p.Parent then
			p.Color = c
		end
	end
	table.clear(tinted)
	if not AtmosphereEffects.tintEnabled or typeof(env.ColorShiftTop) ~= "Color3" then
		return
	end
	local stages = Workspace:FindFirstChild("ExpeditionStage")
	local stage = stages and stageName and stages:FindFirstChild(stageName)
	if not stage then
		return
	end
	local tint = Color3.new(1, 1, 1):Lerp(env.ColorShiftTop, 0.35)
	for _, d in stage:GetDescendants() do
		if d:IsA("MeshPart") then
			tinted[d] = d.Color
			d.Color = tint
		end
	end
end

--- Draws every effect block the Environment carries, centred on `centre`
--- (the map). Replaces whatever a previous call drew.
local last: { Env: any, Centre: Vector3, Stage: string? }? = nil

function AtmosphereEffects.enter(env: any, centre: Vector3, stageName: string?)
	AtmosphereEffects.leave()
	last = { Env = env, Centre = centre, Stage = stageName }
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
	buildDrift(env, root, centre)
	buildCanopy(env.Canopy, root, centre)
	applyTint(env, stageName)
end

function AtmosphereEffects.leave()
	for _, c in conns do
		c:Disconnect()
	end
	table.clear(conns)
	if baseBrightness then
		Lighting.Brightness = baseBrightness
		baseBrightness = nil
	end
	if grade then
		grade:Destroy()
		grade = nil
	end
	for p, c in tinted do
		if p.Parent then
			p.Color = c
		end
	end
	table.clear(tinted)
	if folder then
		folder:Destroy()
		folder = nil
	end
end

--- /tint: turn the whole-chunk tint on or off and redraw the current air.
function AtmosphereEffects.setTint(on: boolean): string
	AtmosphereEffects.tintEnabled = on
	if last then
		AtmosphereEffects.enter(last.Env, last.Centre, last.Stage)
	end
	return if on then "chunk tint ON (MeshPart.Color from the atmosphere)" else "chunk tint OFF"
end

return AtmosphereEffects
