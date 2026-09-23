--!strict
-- The scenario atmospheres' effects (Content/Atmospheres), drawn round the
-- map the player is on. AmbienceController draws the sky, haze, grade, cloud
-- sea and motes; this draws everything that should come OUT OF SOMETHING
-- (owner playtests, 2026-09-23):
--
--   LIGHTS    each scenario's light prop mounted on the map's own spire and
--             tower tops (found by scanning the chunks), pulsing there --
--             not the whole screen, which read as taking damage
--   FLYERS    each scenario's flying props roaming the whole map between
--             random waypoints, in bands above the crowns or below the keels,
--             so nothing ever passes through a chunk
--   LIGHTNING (Stormhawk) frequent, erratic, forked strikes on lightning rods
--             on the spire tips
--   and the atmosphere blocks: Weather, Dome, Plumes (from wrecks), Aurora
--   (from prisms), Debris, Canopy, drifting Floes/Pods, optional chunk Tint.
--
-- Props come from ReplicatedStorage.LuckboundProps by name (atm_*; built by
-- assets/source/worlds/sky_citadel/build_sky_citadel_atmosphere_props.py). A
-- prop not imported yet is simply not drawn -- one warning names them.
-- Client-only scenery: nothing here collides or replicates.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local AtmosphereEffects = {}

-- Per scenario: the light on the spires, the flyers, and how they behave.
local SCENARIO = {
	LOCKDOWN = { Light = "atm_alarm_beacon", Glow = Color3.fromRGB(255, 60, 70), Shape = "Beat", Period = 1.6,
		Flyer = "atm_security_probe", Count = 8, Size = 7, Speed = 26, Beams = true },
	SIEGE = { Light = "atm_signal_fire", Glow = Color3.fromRGB(255, 140, 60), Shape = "Flicker", Period = 0.4,
		Flyer = "atm_raider_glider", Count = 6, Size = 12, Speed = 38 },
	STORMHAWK = { Light = "atm_lightning_rod", Glow = Color3.fromRGB(200, 220, 255), Shape = "Strike",
		Flyer = "atm_stormhawk", Count = 4, Size = 34, Speed = 44, Lightning = true },
	RIME = { Light = "atm_frost_lantern", Glow = Color3.fromRGB(150, 220, 255), Shape = "Sine", Period = 5,
		Flyer = "atm_ice_wisp", Count = 8, Size = 5, Speed = 12, Drift = "atm_ice_floe", DriftSize = 32 },
	RECLAIMED = { Light = "atm_glow_bloom", Glow = Color3.fromRGB(255, 190, 110), Shape = "Sine", Period = 4,
		Flyer = "atm_moth", Count = 12, Size = 7, Speed = 14, Drift = "atm_seed_pod", DriftSize = 12 },
	AETHER_SURGE = { Light = "atm_aether_node", Glow = Color3.fromRGB(190, 140, 255), Shape = "Sine", Period = 3,
		Flyer = "atm_aether_wisp", Count = 14, Size = 4, Speed = 18 },
	UNMOORING = { Light = "atm_stabilizer_beacon", Glow = Color3.fromRGB(120, 200, 255), Shape = "Flicker",
		Period = 0.6, Flyer = "atm_repair_drone", Count = 7, Size = 6, Speed = 20 },
}

local folder: Folder? = nil
local conns: { RBXScriptConnection } = {}
local grade: ColorCorrectionEffect? = nil
local baseBrightness: number? = nil
local tinted: { [BasePart]: Color3 } = {}
local missing: { [string]: boolean } = {}
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

--- An atmosphere prop by name, scaled so its longest side is `size`; nil (and
--- noted) when the library does not have it yet.
local function prop(name: string, size: number, parent: Instance): BasePart?
	local lib = ReplicatedStorage:FindFirstChild("LuckboundProps")
	local src = lib and lib:FindFirstChild(name, true)
	if not (src and src:IsA("BasePart")) then
		missing[name] = true
		return nil
	end
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

-- ---- The map: its extent and its spire tops -----------------------------------------

type Map = { Stage: Instance?, Centre: Vector3, Min: Vector3, Max: Vector3, Floor: number, Tips: { Vector3 } }

local function readMap(stageName: string?, centre: Vector3): Map
	local floorY = centre.Y
	local map: Map = { Stage = nil, Centre = centre, Min = centre - Vector3.new(300, 0, 300),
		Max = centre + Vector3.new(300, 0, 300), Floor = floorY, Tips = {} }
	local stages = Workspace:FindFirstChild("ExpeditionStage")
	local stage = stages and stageName and stages:FindFirstChild(stageName)
	if not stage then
		return map
	end
	map.Stage = stage
	local minX, minZ, maxX, maxZ = math.huge, math.huge, -math.huge, -math.huge
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	for _, chunk in stage:GetChildren() do
		local c = chunk:GetAttribute("Centre")
		if typeof(c) == "Vector3" then
			minX, maxX = math.min(minX, c.X - 128), math.max(maxX, c.X + 128)
			minZ, maxZ = math.min(minZ, c.Z - 128), math.max(maxZ, c.Z + 128)
			-- scan the chunk from above: its high points are its spire and tower tops
			params.FilterDescendantsInstances = { chunk }
			local hits = {}
			for gx = -116, 116, 12 do
				for gz = -116, 116, 12 do
					local r = Workspace:Raycast(Vector3.new(c.X + gx, floorY + 175, c.Z + gz), Vector3.new(0, -140, 0), params)
					if r and r.Position.Y > floorY + 35 then
						table.insert(hits, r.Position)
					end
				end
			end
			table.sort(hits, function(a, b)
				return a.Y > b.Y
			end)
			local picked = 0
			for _, h in hits do
				local clear = true
				for _, t in map.Tips do
					if (Vector3.new(t.X, 0, t.Z) - Vector3.new(h.X, 0, h.Z)).Magnitude < 26 then
						clear = false
						break
					end
				end
				if clear then
					table.insert(map.Tips, h)
					picked += 1
					if picked >= 3 then
						break
					end
				end
			end
		end
	end
	if minX < math.huge then
		map.Min = Vector3.new(minX, floorY, minZ)
		map.Max = Vector3.new(maxX, floorY, maxZ)
		map.Centre = Vector3.new((minX + maxX) / 2, floorY, (minZ + maxZ) / 2)
	end
	return map
end

local function randomIn(map: Map, rng: Random, y: number, pad: number?): Vector3
	local p = pad or 0
	return Vector3.new(rng:NextNumber(map.Min.X - p, map.Max.X + p), y, rng:NextNumber(map.Min.Z - p, map.Max.Z + p))
end

-- Flight bands: over every crown (the kit's crowns reach 160 above the deck),
-- or under every keel (96 below it). A flyer never leaves its band.
local function band(map: Map, rng: Random, low: boolean): number
	return if low then map.Floor - rng:NextNumber(115, 170) else map.Floor + rng:NextNumber(178, 250)
end

-- ---- Lights on the spires ----------------------------------------------------------

local function buildLights(cfg: any, map: Map, root: Instance, lights: { any })
	if not cfg or not cfg.Light then
		return
	end
	for _, tip in map.Tips do
		local p = prop(cfg.Light, 5, root)
		if not p then
			return
		end
		p.CFrame = CFrame.new(tip + Vector3.new(0, p.Size.Y / 2 - 0.3, 0))
		local glow = part({ Name = "Glow", Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Color = cfg.Glow,
			Size = Vector3.new(1.4, 1.4, 1.4), CFrame = CFrame.new(tip + Vector3.new(0, p.Size.Y * 0.75, 0)),
			Transparency = 0.2 }, root)
		local l = Instance.new("PointLight")
		l.Color = cfg.Glow
		l.Range = 40
		l.Brightness = 2
		l.Parent = glow
		table.insert(lights, { Glow = glow, Light = l, Phase = math.random() * 10, Tip = tip + Vector3.new(0, p.Size.Y, 0) })
	end
end

local function lightLevel(shape: string, t: number, period: number, phase: number): number
	local x = ((t + phase) % period) / period
	if shape == "Beat" then
		return math.max(0, 1 - x * 3)
	elseif shape == "Flicker" then
		return 0.55 + 0.45 * math.noise(t * 6 + phase, phase)
	end
	return 0.5 + 0.5 * math.sin(x * 2 * math.pi)
end

-- ---- Flyers ------------------------------------------------------------------------

type Mover = { Part: BasePart, Pos: Vector3, Vel: Vector3, Target: Vector3, Low: boolean, Speed: number,
	Beam: BasePart?, Wobble: number }

local function newMover(p: BasePart, map: Map, rng: Random, low: boolean, speed: number): Mover
	local y = band(map, rng, low)
	local pos = randomIn(map, rng, y, 40)
	return { Part = p, Pos = pos, Vel = Vector3.new(rng:NextNumber(-1, 1), 0, rng:NextNumber(-1, 1)).Unit * speed,
		Target = randomIn(map, rng, band(map, rng, low), 40), Low = low, Speed = speed * rng:NextNumber(0.75, 1.25),
		Beam = nil, Wobble = rng:NextNumber(0, 10) }
end

local function stepMover(m: Mover, map: Map, rng: Random, dt: number)
	local to = m.Target - m.Pos
	if to.Magnitude < 25 then
		m.Target = randomIn(map, rng, band(map, rng, m.Low), 40)
		to = m.Target - m.Pos
	end
	-- steer: turn the velocity toward the waypoint a little each frame
	local want = to.Unit * m.Speed
	m.Vel = m.Vel:Lerp(want, math.clamp(dt * 0.6, 0, 1))
	m.Pos += m.Vel * dt
	local fwd = if m.Vel.Magnitude > 0.1 then m.Vel.Unit else Vector3.new(1, 0, 0)
	local bank = math.clamp(fwd:Cross(to.Unit).Y * 2, -0.5, 0.5)
	-- the meshes are nose-along-+X; lookAt faces -Z, so turn them a quarter
	m.Part.CFrame = CFrame.lookAt(m.Pos, m.Pos + fwd) * CFrame.Angles(0, math.rad(90), 0) * CFrame.Angles(bank, 0, 0)
end

local function buildFlyers(cfg: any, map: Map, root: Instance, rng: Random, movers: { Mover }, beamColour: Color3)
	if not cfg or not cfg.Flyer then
		return
	end
	for i = 1, cfg.Count do
		local p = prop(cfg.Flyer, cfg.Size, root)
		if not p then
			return
		end
		local m = newMover(p, map, rng, cfg.Low == true or (not cfg.Beams and i % 3 == 0), cfg.Speed)
		if cfg.Beams then
			-- a scanning beam out of the probe's lens, down onto the map: slim,
			-- each its own width and shade
			m.Beam = part({
				Name = "ScanBeam",
				Material = Enum.Material.Neon,
				Color = beamColour:Lerp(Color3.fromRGB(255, 150, 90), rng:NextNumber(0, 0.4)),
				Transparency = rng:NextNumber(0.55, 0.75),
				Size = Vector3.new(rng:NextNumber(0.5, 1.4), 1, rng:NextNumber(0.5, 1.4)),
			}, root)
		end
		table.insert(movers, m)
	end
end

-- ---- Lightning --------------------------------------------------------------------

local function bolt(from: Vector3, to: Vector3, rng: Random, root: Instance, colour: Color3, width: number, out: { BasePart })
	local steps = 9
	local prev = from
	for i = 1, steps do
		local f = i / steps
		local p = from:Lerp(to, f)
		if i < steps then
			p += Vector3.new(rng:NextNumber(-22, 22), rng:NextNumber(-6, 6), rng:NextNumber(-22, 22)) * (1 - f * 0.5)
		end
		table.insert(out, part({ Name = "Bolt", Material = Enum.Material.Neon, Color = colour,
			Size = Vector3.new(width, width, (p - prev).Magnitude + width), CFrame = CFrame.lookAt((prev + p) / 2, p) }, root))
		-- a fork now and then, running off and dying out
		if i > 2 and i < steps - 1 and rng:NextNumber() < 0.3 then
			local fork = p + Vector3.new(rng:NextNumber(-60, 60), -rng:NextNumber(30, 90), rng:NextNumber(-60, 60))
			table.insert(out, part({ Name = "Fork", Material = Enum.Material.Neon, Color = colour,
				Size = Vector3.new(width * 0.5, width * 0.5, (fork - p).Magnitude), CFrame = CFrame.lookAt((p + fork) / 2, fork) },
				root))
		end
		prev = p
	end
end

-- ---- The rest of the atmosphere blocks ------------------------------------------------

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

local function buildDome(d: any, root: Instance, map: Map)
	if type(d) ~= "table" then
		return
	end
	-- panels, not a ball: a ball part is not drawn from inside
	local span = math.max(map.Max.X - map.Min.X, map.Max.Z - map.Min.Z)
	local R = math.max(num(d.Radius, 1100) * 0.6, span * 0.62)
	local centre = map.Centre + Vector3.new(0, -150, 0)
	local mat = if d.Material == "ForceField" then Enum.Material.ForceField else Enum.Material.Neon
	local rings, segs = 8, 28
	for i = 0, rings - 1 do
		local e0, e1 = i / rings * math.pi / 2, (i + 1) / rings * math.pi / 2
		local em = (e0 + e1) / 2
		local rr = R * math.cos(em)
		for j = 0, segs - 1 do
			local a = (j + 0.5) / segs * 2 * math.pi
			local pos = centre + Vector3.new(math.cos(a) * rr, R * math.sin(em), math.sin(a) * rr)
			part({ Name = "DomePanel", Material = mat, Color = col(d.Color, Color3.fromRGB(255, 64, 76)),
				Transparency = num(d.Transparency, 0.86),
				Size = Vector3.new(2 * math.pi * rr / segs * 1.05, R * (e1 - e0) * 1.03, 1),
				CFrame = CFrame.lookAt(pos, centre) }, root)
		end
	end
	for i = 1, 6 do
		local py = prop("atm_dome_pylon", 60, root)
		if py then
			local a = i / 6 * 2 * math.pi
			py.CFrame = CFrame.new(centre + Vector3.new(math.cos(a) * R * 0.97, 30, math.sin(a) * R * 0.97))
		end
	end
end

local function buildPlumes(pl: any, root: Instance, map: Map, rng: Random)
	if type(pl) ~= "table" then
		return
	end
	for i = 1, num(pl.Count, 5) do
		-- wrecks lie OUTSIDE the map, down in the cloud, burning
		local a = i / num(pl.Count, 5) * 2 * math.pi + rng:NextNumber(-0.3, 0.3)
		local r = math.max(map.Max.X - map.Min.X, map.Max.Z - map.Min.Z) * 0.5 + rng:NextNumber(180, 420)
		local base = map.Centre + Vector3.new(math.cos(a) * r, -110, math.sin(a) * r)
		local wreck = prop(if i % 2 == 0 then "atm_wreck_stern" else "atm_burning_wreck", 60, root)
		if wreck then
			wreck.CFrame = CFrame.new(base) * CFrame.Angles(0, a, math.rad(rng:NextNumber(-15, 15)))
			local fire = Instance.new("Fire")
			fire.Size = 25
			fire.Heat = 20
			fire.Parent = wreck
		end
		local h, w = num(pl.Height, 900) * 0.7, num(pl.Width, 150) * 0.45
		for k = 0, 8 do
			local f = k / 8
			local s = w * (0.5 + f * 1.6)
			part({ Name = "Plume", Shape = Enum.PartType.Ball, Size = Vector3.new(s, s, s),
				CFrame = CFrame.new(base + Vector3.new(f * h * 0.3, 12 + f * h, f * h * 0.1)),
				Material = if k == 0 then Enum.Material.Neon else Enum.Material.SmoothPlastic,
				Color = if k == 0 then col(pl.Glow, Color3.fromRGB(255, 132, 60))
					else col(pl.Color, Color3.fromRGB(92, 86, 92)):Lerp(col(pl.Shade, Color3.fromRGB(54, 50, 58)), f),
				Transparency = 0.1 + f * 0.55 }, root)
		end
	end
end

local function buildAurora(au: any, root: Instance, map: Map)
	if type(au) ~= "table" then
		return
	end
	local items = {}
	for i = 1, num(au.Count, 3) do
		local c = part({ Name = "Aurora", Material = Enum.Material.Neon,
			Color = col(au.Color, Color3.fromRGB(168, 118, 255)):Lerp(col(au.Tip, Color3.fromRGB(110, 236, 255)), i / 4),
			Transparency = num(au.Transparency, 0.5), Size = Vector3.new(num(au.Length, 1900) * 0.5, num(au.Drop, 240), 3) },
			root)
		table.insert(items, { Curtain = c, Prism = prop("atm_aurora_prism", 26, root), Angle = i * 2.1 })
	end
	local started = os.clock()
	table.insert(conns, RunService.Heartbeat:Connect(function()
		local t = (os.clock() - started) * num(au.Speed, 0.2)
		for i, it in items do
			local cf = CFrame.new(map.Centre + Vector3.new(0, 260 + math.sin(t + i) * 20, 0))
				* CFrame.Angles(0, it.Angle + math.sin(t * 0.5 + i) * 0.2, 0) * CFrame.new(0, 0, 320 + i * 90)
			it.Curtain.CFrame = cf
			if it.Prism then
				it.Prism.CFrame = cf * CFrame.new(-it.Curtain.Size.X / 2, 0, 0) * CFrame.Angles(0, t, 0)
			end
		end
	end))
end

local function buildDebris(db: any, root: Instance, map: Map, rng: Random)
	if type(db) ~= "table" then
		return
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = if map.Stage then { map.Stage } else {}
	local pool = {}
	for _ = 1, 12 do
		local s = rng:NextNumber(num(db.SizeMin, 3), num(db.SizeMax, 14))
		local p = prop("atm_falling_masonry", s, root)
		if not p then
			break
		end
		table.insert(pool, { Part = p, Y = -1e9, X = 0, Z = 0 })
	end
	for i = 1, 3 do
		local r = prop("atm_broken_ring", 28, root)
		if r then
			r.CFrame = CFrame.new(randomIn(map, rng, map.Floor - 130 - i * 15, 60)) * CFrame.Angles(math.rad(20 * i), i, 0)
		end
	end
	local speed, spin, rate = num(db.Speed, 28), math.rad(num(db.Spin, 70)), num(db.Rate, 2.5)
	local acc = 0
	table.insert(conns, RunService.Heartbeat:Connect(function(dt)
		acc += dt * rate
		for _, d in pool do
			if d.Y < map.Floor - 600 and acc >= 1 then
				acc -= 1
				-- only where nothing of the map is below: debris never falls through a chunk
				for _ = 1, 6 do
					local p = randomIn(map, rng, map.Floor + 60, 80)
					if not Workspace:Raycast(p, Vector3.new(0, -700, 0), params) then
						d.X, d.Z, d.Y = p.X, p.Z, p.Y
						break
					end
				end
			end
			if d.Y > map.Floor - 600 then
				d.Y -= speed * dt
				d.Part.CFrame = CFrame.new(d.X, d.Y, d.Z) * CFrame.Angles(os.clock() * spin, os.clock() * spin * 0.7, 0)
			end
		end
	end))
end

local function buildCanopy(list: any, root: Instance, map: Map)
	if type(list) ~= "table" then
		return
	end
	local rng = Random.new(11)
	for _, layer in list do
		for _ = 1, num(layer.Count, 12) do
			local s = rng:NextNumber(num(layer.SizeMin, 400), num(layer.SizeMax, 700))
			part({ Name = "Canopy", Shape = Enum.PartType.Ball, Size = Vector3.new(s, s * 0.22, s * 0.8),
				CFrame = CFrame.new(randomIn(map, rng, map.Floor + num(layer.Height, 520), 400)),
				Color = col(layer.Color, Color3.fromRGB(70, 76, 92)), Material = Enum.Material.SmoothPlastic,
				Transparency = num(layer.Transparency, 0.1) }, root)
		end
	end
end

local function applyTint(env: any, map: Map)
	for p, c in tinted do
		if p.Parent then
			p.Color = c
		end
	end
	table.clear(tinted)
	if not AtmosphereEffects.tintEnabled or typeof(env.ColorShiftTop) ~= "Color3" or not map.Stage then
		return
	end
	local tint = Color3.new(1, 1, 1):Lerp(env.ColorShiftTop, 0.35)
	for _, d in (map.Stage :: Instance):GetDescendants() do
		if d:IsA("MeshPart") then
			tinted[d] = d.Color
			d.Color = tint
		end
	end
end

-- ---- Enter / leave ------------------------------------------------------------------

local last: { Env: any, Centre: Vector3, Stage: string?, Id: string? }? = nil

--- Draws the atmosphere round the map. `atmosphereId` names the scenario
--- (Content/Atmospheres key), nil for the world's own air.
function AtmosphereEffects.enter(env: any, centre: Vector3, stageName: string?, atmosphereId: string?)
	AtmosphereEffects.leave()
	if type(env) ~= "table" then
		return
	end
	last = { Env = env, Centre = centre, Stage = stageName, Id = atmosphereId }
	table.clear(missing)
	local root = Instance.new("Folder")
	root.Name = "LuckboundAtmosphere"
	root.Parent = Workspace
	folder = root
	local rng = Random.new()
	local map = readMap(stageName, centre)
	local cfg = atmosphereId and SCENARIO[atmosphereId]

	buildWeather(env.Weather, root)
	buildDome(env.Dome, root, map)
	buildPlumes(env.Plumes, root, map, rng)
	buildAurora(env.Aurora, root, map)
	buildDebris(env.Debris, root, map, rng)
	buildCanopy(env.Canopy, root, map)
	applyTint(env, map)

	local lights, movers = {}, {}
	buildLights(cfg, map, root, lights)
	buildFlyers(cfg, map, root, rng, movers, if cfg then cfg.Glow else Color3.new(1, 0, 0))
	if cfg and cfg.Drift then
		for i = 1, 6 do
			local p = prop(cfg.Drift, cfg.DriftSize, root)
			if p then
				table.insert(movers, newMover(p, map, rng, i % 2 == 0, 6))
			end
		end
	end

	-- lightning: the flash is on the screen only for the instant of the strike
	local flashes = env.Flashes
	local strikes = cfg and cfg.Lightning and type(flashes) == "table"
	if strikes then
		local g = Instance.new("ColorCorrectionEffect")
		g.Name = "LuckboundLightning"
		g.Parent = Lighting
		grade = g
	end
	baseBrightness = Lighting.Brightness
	local bolts: { BasePart } = {}
	local boltUntil, nextStrike, restrike = 0, os.clock() + 1, 0
	local started = os.clock()

	table.insert(conns, RunService.Heartbeat:Connect(function(dt)
		local t = os.clock() - started
		for _, m in movers do
			stepMover(m, map, rng, dt)
			if m.Beam then
				-- the beam hangs from the lens and sweeps as the probe moves
				local len = math.max(40, m.Pos.Y - map.Floor + 10)
				local tilt = CFrame.Angles(math.sin(t * 0.9 + m.Wobble) * 0.35, 0, math.cos(t * 0.7 + m.Wobble) * 0.35)
				m.Beam.Size = Vector3.new(m.Beam.Size.X, len, m.Beam.Size.Z)
				m.Beam.CFrame = CFrame.new(m.Pos + Vector3.new(0, -2, 0)) * tilt * CFrame.new(0, -len / 2, 0)
			end
		end
		if cfg then
			for _, l in lights do
				local v = if cfg.Shape == "Strike" then 0.15 else lightLevel(cfg.Shape, t, cfg.Period or 3, l.Phase)
				l.Light.Brightness = 0.5 + v * 3
				l.Glow.Transparency = 0.7 - v * 0.6
			end
		end
		if strikes then
			local now = os.clock()
			local colour = col(flashes.Color, Color3.fromRGB(210, 222, 255))
			if now >= nextStrike or (restrike > 0 and now >= boltUntil + 0.06) then
				for _, b in bolts do
					b:Destroy()
				end
				table.clear(bolts)
				if restrike > 0 then
					restrike -= 1
				else
					restrike = rng:NextInteger(0, 2) -- a strike flickers 1-3 times
					nextStrike = now + rng:NextNumber(0.6, 3.2)
				end
				for _ = 1, rng:NextInteger(1, 3) do
					local target = if #lights > 0 then lights[rng:NextInteger(1, #lights)].Tip
						else randomIn(map, rng, map.Floor, 0)
					bolt(target + Vector3.new(rng:NextNumber(-120, 120), 650, rng:NextNumber(-120, 120)), target, rng, root,
						colour, rng:NextNumber(1.5, 3), bolts)
					local pl = Instance.new("PointLight")
					pl.Range = 90
					pl.Brightness = 10
					pl.Color = colour
					pl.Parent = bolts[#bolts]
				end
				boltUntil = now + rng:NextNumber(0.05, 0.12)
			end
			local lit = now < boltUntil
			Lighting.Brightness = (baseBrightness :: number) + (if lit then num(flashes.Brightness, 2.5) else 0)
			if grade then
				grade.Brightness = if lit then 0.18 else 0
				grade.TintColor = if lit then Color3.new(1, 1, 1):Lerp(colour, 0.3) else Color3.new(1, 1, 1)
			end
			if not lit and restrike == 0 and #bolts > 0 and now > boltUntil + 0.15 then
				for _, b in bolts do
					b:Destroy()
				end
				table.clear(bolts)
			end
		end
	end))

	if next(missing) then
		local names = {}
		for n in missing do
			table.insert(names, n)
		end
		table.sort(names)
		warn(`[AtmosphereEffects] not in LuckboundProps yet (import sky_citadel_atmosphere_props.fbx): {table.concat(names, ", ")}`)
	end
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
		AtmosphereEffects.enter(last.Env, last.Centre, last.Stage, last.Id)
	end
	return if on then "chunk tint ON (MeshPart.Color from the atmosphere)" else "chunk tint OFF"
end

return AtmosphereEffects
