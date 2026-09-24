--!strict
-- THE SKY TRAFFIC round the Crossroads.
--
-- The server (HubV2.buildSky) places the props and marks each with Wander and
-- the band it may use. Here, per client, every one flies its own course:
--
--   * it heads for a waypoint in its band, then picks another -- usually
--     onward round the hub, sometimes doubling back, sometimes straight across;
--   * its speed drifts between its limits, so no two keep pace;
--   * IT TURNS LIKE ITS SIZE (owner, 2026-09-24: "larger moving props should
--     have larger turning radius"): heading changes at most speed / radius,
--     and the radius grows with the prop -- a skiff darts, a whale or a carrier
--     swings round in a wide arc and never pivots on the spot;
--   * IT LOOKS AHEAD ("test what's in front of it before the prop is there ...
--     reroute it before it gets there"): a sphere its own size is swept along
--     its path -- far enough to cover its turning arc -- against the real hub
--     meshes, the Engine and the backdrop islands, and anything in the way
--     turns it early, sideways and up. There is no no-fly zone: it may cross
--     the hub when the way is clear;
--   * it keeps clear of every other prop by a clearance scaled to both sizes;
--   * THE BIG SHIPS DOCK: now and then one picks a backdrop island, comes
--     alongside its edge, slows, holds a while, and sails on.
--
-- Client-side decoration: each player's sky moves on its own. Props the
-- device's graphics level hides (Detail, see HubEffects) are skipped.

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)

local SkyTraffic = {}

local CLEARANCE = 18 -- studs kept between two props
local SCAN_EVERY = 0.15 -- seconds between one prop's path checks
local MAX_CAST = 1000 -- Roblox refuses a shapecast longer than 1024 studs
local BIG = 45 -- a prop this big (half its diagonal) is a big ship and may dock
local TURN_PER_SIZE = 3 -- turning radius = this x the prop's half-diagonal
local TURN_MIN, TURN_MAX = 12, 320

type Rock = { Part: BasePart, Pos: Vector3, Radius: number }
type Flyer = {
	Part: BasePart,
	Pos: Vector3,
	Dir: Vector3, -- unit heading; turns no faster than Speed / TurnRadius
	Target: Vector3,
	Speed: number,
	SpeedGoal: number,
	NextSpeedChange: number,
	Radius: number,
	TurnRadius: number,
	Band: { Centre: Vector3, RMin: number, RMax: number, YMin: number, YMax: number, SMin: number, SMax: number },
	Faces: boolean,
	Bob: number,
	Phase: number,
	Yaw: number,
	Bank: number,
	Rng: Random,
	Subs: { any },
	BestDist: number,
	StuckFor: number,
	Avoid: Vector3,
	ScanIn: number,
	Mode: string, -- "fly" | "dock" | "docked"
	NextDock: number,
	DockUntil: number,
	DockHeading: Vector3,
}

local rocks: { Rock } = {}
local castParams = RaycastParams.new()
castParams.FilterType = Enum.RaycastFilterType.Include
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include

local function blocked(p: Vector3, r: number): boolean
	return #Workspace:GetPartBoundsInRadius(p, r, overlapParams) > 0
end

local function angleOf(f: Flyer, p: Vector3): number
	return math.atan2(p.Z - f.Band.Centre.Z, p.X - f.Band.Centre.X)
end

local function waypoint(f: Flyer, fromAngle: number): Vector3
	local b = f.Band
	local roll = f.Rng:NextNumber()
	local turn
	if roll < 0.15 then
		turn = math.pi + f.Rng:NextNumber(-0.6, 0.6) -- straight across, over or through the hub
	elseif roll < 0.3 then
		turn = -f.Rng:NextNumber(0.4, 1.2) -- doubling back (in a wide arc, for a big one)
	else
		turn = f.Rng:NextNumber(0.3, 1.1)
	end
	local a = fromAngle + turn * (if f.Phase > 0 then 1 else -1)
	-- never a point inside something: a waypoint there can only be circled
	local p = b.Centre
	for _ = 1, 10 do
		local r = f.Rng:NextNumber(b.RMin, b.RMax)
		p = Vector3.new(b.Centre.X + math.cos(a) * r, f.Rng:NextNumber(b.YMin, b.YMax), b.Centre.Z + math.sin(a) * r)
		if not blocked(p, f.Radius + CLEARANCE) then
			break
		end
		a += f.Rng:NextNumber(0.2, 0.6)
	end
	f.BestDist, f.StuckFor = math.huge, 0
	return p
end

-- A berth beside a backdrop island: at its edge, on the side facing the ship,
-- a little below its top, and clear of it.
local function berth(f: Flyer): (Vector3?, Vector3?)
	local best, bestD = nil, math.huge
	for _, rock in rocks do
		local d = (rock.Pos - f.Pos).Magnitude
		if d < bestD then
			best, bestD = rock, d
		end
	end
	if not best then
		return nil, nil
	end
	local rock = best :: Rock
	local out = Vector3.new(f.Pos.X - rock.Pos.X, 0, f.Pos.Z - rock.Pos.Z)
	out = if out.Magnitude > 1 then out.Unit else Vector3.xAxis
	local reach = math.max(rock.Part.Size.X, rock.Part.Size.Z) * 0.5
	for k = 0, 6 do
		local dir = CFrame.Angles(0, (k % 2 == 0 and 1 or -1) * math.ceil(k / 2) * 0.35, 0):VectorToWorldSpace(out)
		local spot = rock.Pos + dir * (reach + f.Radius * 0.6) + Vector3.new(0, rock.Part.Size.Y * 0.12, 0)
		if not blocked(spot, f.Radius * 0.8) then
			-- moored side-on to the island
			return spot, dir:Cross(Vector3.yAxis)
		end
	end
	return nil, nil
end

-- Turn `dir` toward `want` by at most `maxAngle` radians. Heading in the
-- horizontal plane is rate-limited (that is the turning circle); climb and
-- dive blend freely, since pitch is small.
local function turnToward(dir: Vector3, want: Vector3, maxAngle: number): Vector3
	local flatD = Vector3.new(dir.X, 0, dir.Z)
	local flatW = Vector3.new(want.X, 0, want.Z)
	if flatW.Magnitude < 1e-3 then
		return dir
	end
	if flatD.Magnitude < 1e-3 then
		flatD = flatW
	end
	local a0 = math.atan2(flatD.Z, flatD.X)
	local a1 = math.atan2(flatW.Z, flatW.X)
	local delta = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
	local a = a0 + math.clamp(delta, -maxAngle, maxAngle)
	local y = dir.Y + (want.Unit.Y - dir.Y) * math.min(1, maxAngle * 2)
	local h = math.sqrt(math.max(0, 1 - y * y))
	return Vector3.new(math.cos(a) * h, y, math.sin(a) * h)
end

function SkyTraffic.init(): ()
	task.spawn(function()
		local hub = Workspace:WaitForChild(Constants.NAMES.CROSSROADS, 60)
		if not hub then
			return
		end
		local sky = hub:WaitForChild("Sky", 30)
		if not sky then
			return
		end
		task.wait(2) -- let HubEffects mark what this device hides

		-- what a prop must not fly into: the hub's pieces, the Engine, the islands
		local solids: { Instance } = {}
		local v2 = hub:FindFirstChild("CrossroadsV2")
		if v2 then
			table.insert(solids, v2)
		end
		local engine = hub:FindFirstChild(Constants.NAMES.FATE_ENGINE)
		if engine then
			table.insert(solids, engine)
		end

		local flyers: { Flyer } = {}
		for _, d in sky:GetChildren() do
			if not d:IsA("BasePart") then
				continue
			end
			if d:GetAttribute("Backdrop") then
				table.insert(rocks, { Part = d, Pos = d.Position, Radius = math.max(d.Size.X, d.Size.Z) * 0.5 })
				table.insert(solids, d)
			elseif d:GetAttribute("Wander") and d.LocalTransparencyModifier < 1 then
				local r = d:GetAttribute("WanderRadius") :: Vector2
				local h = d:GetAttribute("WanderHeight") :: Vector2
				local s = d:GetAttribute("WanderSpeed") :: Vector2
				local rng = Random.new((d:GetAttribute("WanderSeed") :: number?) or 1)
				local size = d.Size.Magnitude * 0.5
				local a = rng:NextNumber(0, math.pi * 2)
				local f: Flyer = {
					Part = d,
					Pos = d.Position,
					Dir = Vector3.new(math.cos(a), 0, math.sin(a)),
					Target = d.Position,
					Speed = rng:NextNumber(s.X, s.Y),
					SpeedGoal = rng:NextNumber(s.X, s.Y),
					NextSpeedChange = rng:NextNumber(4, 12),
					Radius = size,
					TurnRadius = math.clamp(size * TURN_PER_SIZE, TURN_MIN, TURN_MAX),
					Band = { Centre = d:GetAttribute("WanderCentre") :: Vector3, RMin = r.X, RMax = r.Y,
						YMin = h.X, YMax = h.Y, SMin = s.X, SMax = s.Y },
					Faces = d:GetAttribute("WanderFaces") == true,
					Bob = (d:GetAttribute("WanderBob") :: number?) or 0,
					Phase = if rng:NextNumber() < 0.3 then -rng:NextNumber(0.1, 6) else rng:NextNumber(0.1, 6),
					Yaw = rng:NextNumber(0, math.pi * 2),
					Bank = 0,
					Rng = rng,
					Subs = {},
					BestDist = math.huge,
					StuckFor = 0,
					Avoid = Vector3.zero,
					ScanIn = rng:NextNumber(0, SCAN_EVERY),
					Mode = "fly",
					NextDock = rng:NextNumber(30, 90),
					DockUntil = 0,
					DockHeading = Vector3.new(math.cos(a), 0, math.sin(a)),
				}
				for _, c in d:GetChildren() do
					if c:IsA("BasePart") and c:GetAttribute("SubKind") then
						table.insert(f.Subs, {
							Part = c,
							Kind = c:GetAttribute("SubKind"),
							Offset = c:GetAttribute("SubOffset") :: Vector3,
							Hinge = c:GetAttribute("SubHinge") :: Vector3,
							Axis = c:GetAttribute("SubAxis") :: Vector3,
							Amp = (c:GetAttribute("SubAmp") :: number?) or 0.3,
							Rate = (c:GetAttribute("SubRate") :: number?) or 1,
							Phase = ((c:GetAttribute("SubPhase") :: number?) or 0) + rng:NextNumber(0, 1),
							Alpha = c.Transparency,
						})
					end
				end
				table.insert(flyers, f)
			end
		end
		castParams.FilterDescendantsInstances = solids
		overlapParams.FilterDescendantsInstances = solids
		for _, f in flyers do
			f.Target = waypoint(f, angleOf(f, f.Pos))
		end
		print(string.format("[SkyTraffic] %d flyer(s), %d island(s), %d solid group(s)", #flyers, #rocks, #solids))

		local elapsed = 0
		RunService.Heartbeat:Connect(function(dt)
			elapsed += dt
			dt = math.min(dt, 0.1)
			for i, f in flyers do
				-- DOCKING: big ships only, now and then
				if f.Radius >= BIG and f.Faces then
					if f.Mode == "fly" then
						f.NextDock -= dt
						if f.NextDock <= 0 then
							local spot, heading = berth(f)
							if spot then
								f.Mode, f.Target, f.DockHeading = "dock", spot, heading :: Vector3
								f.BestDist, f.StuckFor = math.huge, 0
							else
								f.NextDock = f.Rng:NextNumber(20, 40)
							end
						end
					elseif f.Mode == "docked" and elapsed >= f.DockUntil then
						f.Mode = "fly"
						f.NextDock = f.Rng:NextNumber(60, 140)
						f.Target = waypoint(f, angleOf(f, f.Pos))
					end
				end

				-- speed drifts toward a goal that itself changes now and then
				f.NextSpeedChange -= dt
				if f.NextSpeedChange <= 0 then
					f.SpeedGoal = f.Rng:NextNumber(f.Band.SMin, f.Band.SMax)
					f.NextSpeedChange = f.Rng:NextNumber(5, 15)
				end
				local to = f.Target - f.Pos
				local goal = f.SpeedGoal
				if f.Mode == "dock" then
					goal = math.min(goal, math.max(3, to.Magnitude * 0.4)) -- ease in to the berth
				elseif f.Mode == "docked" then
					goal = 0
				end
				f.Speed += (goal - f.Speed) * math.min(1, dt * 0.4)

				if f.Mode == "fly" then
					if to.Magnitude < f.BestDist - 1 then
						f.BestDist, f.StuckFor = to.Magnitude, 0
					else
						f.StuckFor += dt
					end
					-- a big turner counts as arrived from further out: it cannot
					-- tighten its circle onto a point
					if to.Magnitude < math.max(40, f.TurnRadius * 0.8) or f.StuckFor > 8 then
						f.Target = waypoint(f, angleOf(f, f.Pos) + (if f.StuckFor > 8 then math.pi * 0.5 else 0))
						to = f.Target - f.Pos
					end
				elseif f.Mode == "dock" then
					if to.Magnitude < 6 then
						f.Mode = "docked"
						f.DockUntil = elapsed + f.Rng:NextNumber(12, 25)
					elseif to.Magnitude < f.BestDist - 1 then
						f.BestDist, f.StuckFor = to.Magnitude, 0
					else
						f.StuckFor += dt
						if f.StuckFor > 12 then -- could not get in: give up, sail on
							f.Mode = "fly"
							f.NextDock = f.Rng:NextNumber(30, 60)
							f.Target = waypoint(f, angleOf(f, f.Pos))
						end
					end
				end

				local steer = if to.Magnitude > 0.01 then to.Unit else f.Dir

				-- LOOK AHEAD, far enough to cover this prop's turning arc: sweep a
				-- sphere of its size along its heading; anything in the way turns
				-- it early, sideways and up.
				f.ScanIn -= dt
				if f.ScanIn <= 0 and f.Mode ~= "docked" then
					f.ScanIn = SCAN_EVERY
					f.Avoid = Vector3.zero
					local reach = math.min(math.max(f.Speed, 8) * 3 + f.TurnRadius * 1.5 + f.Radius, MAX_CAST)
					local r = math.clamp(f.Radius * 0.7, 2, 200)
					local hit = Workspace:Spherecast(f.Pos - f.Dir * r * 0.5, r, f.Dir * reach, castParams)
					if hit then
						local urgency = 1 - math.clamp(hit.Distance / reach, 0, 1)
						local side = hit.Normal - f.Dir * hit.Normal:Dot(f.Dir)
						if side.Magnitude < 0.1 then
							side = f.Dir:Cross(Vector3.yAxis)
						end
						f.Avoid = (side.Unit + Vector3.yAxis * 0.6).Unit * (0.5 + urgency * 2.5)
						-- if the waypoint is behind the obstacle, choose another now
						if urgency > 0.4 and f.Mode == "fly" then
							local toTarget = f.Target - f.Pos
							if toTarget.Magnitude > MAX_CAST then
								toTarget = toTarget.Unit * MAX_CAST -- only the stretch that matters now
							end
							if toTarget.Magnitude > 1 and Workspace:Spherecast(f.Pos, r, toTarget, castParams) then
								f.Target = waypoint(f, angleOf(f, f.Pos) + math.pi * 0.35)
							end
						end
					end
				end
				steer += f.Avoid

				-- and keep clear of each other
				for j, o in flyers do
					if j ~= i then
						local away = f.Pos - o.Pos
						local d = away.Magnitude
						local need = f.Radius + o.Radius + CLEARANCE
						if d < need + 30 and d > 0.01 then
							steer += away.Unit * 2.5 * (1 - math.clamp((d - need) / 30, 0, 1))
						end
					end
				end

				-- THE TURNING CIRCLE: heading swings at most Speed / TurnRadius per
				-- second. A standing ship (docked) does not turn at all.
				local maxTurn = math.max(f.Speed, 1) / f.TurnRadius * dt
				local prevDir = f.Dir
				if steer.Magnitude > 1e-3 then
					f.Dir = turnToward(f.Dir, steer.Unit, maxTurn)
				end
				f.Pos += f.Dir * f.Speed * dt

				local bob = math.sin(elapsed * 0.5 + f.Phase) * f.Bob
				local at = f.Pos + Vector3.new(0, bob, 0)
				local cf
				if f.Faces then
					local fwd = Vector3.new(f.Dir.X, 0, f.Dir.Z)
					if f.Mode == "docked" then
						fwd = f.DockHeading
					end
					if fwd.Magnitude < 1e-3 then
						fwd = Vector3.xAxis
					end
					-- bank into the turn, by how hard it is turning
					local yawRate = prevDir:Cross(f.Dir).Y / math.max(dt, 1e-3)
					f.Bank += (math.clamp(yawRate * 0.8, -0.3, 0.3) - f.Bank) * math.min(1, dt * 1.5)
					f.DockHeading = f.DockHeading:Lerp(fwd.Unit, math.min(1, dt * 0.5))
					-- the imported meshes' noses point along -X: a quarter turn
					-- lines them up with lookAt's forward
					cf = CFrame.lookAt(at, at + f.DockHeading) * CFrame.Angles(0, -math.pi / 2, 0) * CFrame.Angles(f.Bank, 0, 0)
				else
					f.Yaw += dt * 0.05 * (if f.Phase > 0 then 1 else -1)
					cf = CFrame.new(at) * CFrame.Angles(0, f.Yaw, 0)
				end
				f.Part.CFrame = cf

				-- the moving pieces: propellers spin, fins and flukes swing about
				-- their joints, flames and lift crystals flicker
				for _, s in f.Subs do
					local rel = CFrame.new(s.Offset)
					if s.Kind == "Spin" or s.Kind == "Flap" then
						local spin = if f.Mode == "docked" then 0.2 else 1 -- propellers idle at a berth
						local angle = if s.Kind == "Spin"
							then elapsed * s.Rate * spin + s.Phase
							else math.sin(elapsed * s.Rate * math.pi * 2 + s.Phase) * s.Amp
						rel = CFrame.new(s.Hinge) * CFrame.fromAxisAngle(s.Axis, angle) * CFrame.new(s.Offset - s.Hinge)
					elseif s.Kind == "Flicker" then
						s.Part.Transparency = s.Alpha + 0.35 * (0.5 + 0.5 * math.sin(elapsed * s.Rate * math.pi * 2 + s.Phase))
					end
					s.Part.CFrame = cf * rel
				end
			end
		end)
	end)
end

return SkyTraffic
