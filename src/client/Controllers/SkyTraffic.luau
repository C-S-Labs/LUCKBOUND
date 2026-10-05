--!strict
-- THE SKY TRAFFIC round the Crossroads: a thin client driver over Core/FlightCore.
--
-- The server (HubV2.buildSky) places the props and the creatures and marks each
-- with Wander and the band it may use (creatures also carry SkyClass, the class
-- profile in GameConfig.HubLayout.V2.SkyLife that says how that kind of thing
-- flies, and SkyCanLand). Here, per client, every one flies its own course:
--
--   * FlightCore owns the kinematics: a creature ALWAYS travels forward
--     (velocity is heading * speed -- no sideways translation, no instant yaw),
--     turns no faster than its size allows, eases off before a tight turn and
--     banks into it; it keeps out of a hub cylinder scaled to its class;
--   * this driver adds what needs the real world: a look-ahead sweep of a
--     sphere its own size against the hub's meshes, the Engine and the backdrop
--     islands (anything in the way turns it early, sideways and up), separation
--     scaled by both bodies, and landing spots on the backdrop islands for the
--     species that may land;
--   * it animates the moving pieces (Spin, Flap, Flicker, Pulse), chained
--     (a tail follows the body, a wing tip its wing) and by gait (flap rate rises
--     with speed and climb, glides between beats, breathing while perched, lean
--     with the bank);
--   * it throttles: a creature far from the camera updates at its class's
--     UpdateHz, one that is away (colossals come and go) costs nothing.
--
-- Client-side decoration: each player's sky moves on its own. Props the
-- device's graphics level hides (Detail, see HubEffects) are skipped.

local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local FlightCore = require(Root.Core.FlightCore)

local life: any = GameConfig.HubLayout.V2.SkyLife
local driverCfg = life.Driver
local gaitCfg = life.Gait
local perchCfg = life.Perch

local SkyTraffic = {}

type Rock = { Part: BasePart, Pos: Vector3, Radius: number }
type Sub = {
	Part: BasePart,
	Kind: string,
	Offset: Vector3,
	Hinge: Vector3,
	Axis: Vector3,
	Amp: number,
	Rate: number,
	Phase: number, -- effective: a chained part's follows its parent's, lagged
	Lag: number,
	Gait: string,
	Chain: Sub?,
	Alpha: number,
	BaseSize: Vector3,
	Acc: CFrame, -- this part's hinge motion composed on its chain (rebuilt every update)
}
type Flyer = {
	Part: BasePart,
	Core: FlightCore.Flier,
	Faces: boolean,
	Bob: number,
	Spin: number, -- slow turn of a prop that does not face its heading
	Yaw: number,
	TimeOffset: number,
	Subs: { Sub },
	ScanIn: number,
	Accum: number,
	Parked: boolean,
	Env: { [string]: any },
}

local rocks: { Rock } = {}
local castParams = RaycastParams.new()
castParams.FilterType = Enum.RaycastFilterType.Include
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include
local perchParams = RaycastParams.new()
perchParams.FilterType = Enum.RaycastFilterType.Include

local function blocked(x: number, y: number, z: number, r: number): boolean
	return #Workspace:GetPartBoundsInRadius(Vector3.new(x, y, z), r, overlapParams) > 0
end

-- A landing spot on a backdrop island: the top surface (a real downward ray),
-- on a flat enough patch, never near the hub, on the side the creature is
-- already flying toward.
local function findPerch(core: FlightCore.Flier, bodyHeight: number): FlightCore.PerchSpot?
	local nearest: { Rock } = {}
	for _, rock in rocks do
		local dx, dz = rock.Pos.X - core.Band.Cx, rock.Pos.Z - core.Band.Cz
		if math.sqrt(dx * dx + dz * dz) >= perchCfg.MinHubDistance then
			table.insert(nearest, rock)
		end
	end
	table.sort(nearest, function(a, b)
		return (a.Pos - Vector3.new(core.X, core.Y, core.Z)).Magnitude
			< (b.Pos - Vector3.new(core.X, core.Y, core.Z)).Magnitude
	end)
	for i = 1, math.min(#nearest, perchCfg.Tries) do
		local rock = nearest[i]
		local part = rock.Part
		local lx = core.Rng:NextNumber(-1, 1) * part.Size.X * 0.5 * perchCfg.Inset
		local lz = core.Rng:NextNumber(-1, 1) * part.Size.Z * 0.5 * perchCfg.Inset
		local above = part.CFrame:PointToWorldSpace(Vector3.new(lx, 0, lz))
		local top =
			Vector3.new(above.X, part.Position.Y + part.Size.Y * 0.5 + perchCfg.CastHeight, above.Z)
		perchParams.FilterDescendantsInstances = { part }
		local hit = Workspace:Raycast(
			top,
			Vector3.new(0, -(part.Size.Y + perchCfg.CastHeight * 2), 0),
			perchParams
		)
		if hit and hit.Normal.Y >= perchCfg.NormalMinY then
			return {
				X = hit.Position.X,
				Y = hit.Position.Y + bodyHeight * perchCfg.RestLiftScale,
				Z = hit.Position.Z,
				FaceYaw = math.atan2(hit.Position.Z - core.Z, hit.Position.X - core.X),
			}
		end
	end
	return nil
end

-- A moving piece's hinge motion about its joint, as a CFrame in the body's space.
local function hingeAbout(hinge: Vector3, axis: Vector3, angle: number): CFrame
	if axis.Magnitude < 1e-3 then
		axis = Vector3.xAxis
	end
	return CFrame.new(hinge) * CFrame.fromAxisAngle(axis, angle) * CFrame.new(-hinge)
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
		task.wait(driverCfg.SettleSeconds) -- let HubEffects mark what this device hides

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
		-- the cloud sea turns slowly round the hub, each bank at its own pace
		-- Each bank keeps its layer's direction but has its own character: its
		-- pace swells and slackens on its own cycle, it eases in and out from the
		-- hub, rises and sinks a little, and turns slowly on the spot.
		local drifters: { any } = {}
		-- the celestial ring and its runes
		local spinners: { any } = {}
		local adopted: { [Instance]: boolean } = {}

		-- A creature or prop's moving pieces, in chain order (a parent before the
		-- parts that ride on it).
		local function gatherSubs(d: BasePart): { Sub }
			local byName: { [string]: Sub } = {}
			local chainOf: { [string]: string } = {}
			local list: { Sub } = {}
			for _, c in d:GetChildren() do
				if c:IsA("BasePart") and c:GetAttribute("SubKind") then
					local sub: Sub = {
						Part = c,
						Kind = c:GetAttribute("SubKind") :: string,
						Offset = c:GetAttribute("SubOffset") :: Vector3,
						Hinge = c:GetAttribute("SubHinge") :: Vector3,
						Axis = c:GetAttribute("SubAxis") :: Vector3,
						Amp = (c:GetAttribute("SubAmp") :: number?) or 0.3,
						Rate = (c:GetAttribute("SubRate") :: number?) or 1,
						Phase = (c:GetAttribute("SubPhase") :: number?) or 0,
						Lag = (c:GetAttribute("SubLag") :: number?) or 0,
						Gait = (c:GetAttribute("SubGait") :: string?) or "Always",
						Chain = nil,
						Alpha = c.Transparency,
						BaseSize = c.Size,
						Acc = CFrame.identity,
					}
					byName[c.Name] = sub
					local chain = c:GetAttribute("SubChain")
					if type(chain) == "string" then
						chainOf[c.Name] = chain
					end
					table.insert(list, sub)
				end
			end
			-- resolve chains, and order parents first
			local depth: { [Sub]: number } = {}
			local function depthOf(sub: Sub, guard: number): number
				if depth[sub] then
					return depth[sub]
				end
				local parent = chainOf[sub.Part.Name]
				local up = if parent then byName[parent] else nil
				local dd = 0
				if up and guard < 16 then
					sub.Chain = up
					dd = depthOf(up, guard + 1) + 1
					-- a chained part's beat follows its parent's, lagged behind it
					sub.Phase = up.Phase - sub.Lag
				end
				depth[sub] = dd
				return dd
			end
			for _, sub in list do
				depthOf(sub, 0)
			end
			table.sort(list, function(a, b)
				return depth[a] < depth[b]
			end)
			return list
		end

		-- ONE PROP, CREATURE OR ISLAND, whenever it arrives. Called for everything
		-- already here and again for anything that streams in later, so a late
		-- arrival flies (or is steered round) like the rest instead of sitting still.
		local function adopt(d: Instance)
			if adopted[d] or not d:IsA("BasePart") then
				return
			end
			adopted[d] = true
			if d:GetAttribute("SkySpin") then
				table.insert(spinners, {
					Part = d,
					Base = d.CFrame,
					Rate = d:GetAttribute("SkySpin") :: number,
					A = d:GetAttribute("SkyColorA"),
					B = d:GetAttribute("SkyColorB"),
					Seconds = (d:GetAttribute("SkyColorSeconds") :: number?) or 9,
				})
			elseif d:GetAttribute("Drift") then
				if d.LocalTransparencyModifier < 1 then
					local centre = d:GetAttribute("DriftCentre") :: Vector3
					local rel = d.Position - centre
					local r = Random.new((d:GetAttribute("DriftSeed") :: number?) or 1)
					table.insert(drifters, {
						Part = d,
						Centre = centre,
						Rate = d:GetAttribute("Drift") :: number,
						Angle = math.atan2(rel.Z, rel.X),
						Radius = Vector3.new(rel.X, 0, rel.Z).Magnitude,
						Y = rel.Y,
						Rot = d.CFrame.Rotation,
						Yaw = 0,
						-- its own cycles
						PacePeriod = r:NextNumber(40, 110),
						PaceAmp = r:NextNumber(0.3, 0.7),
						InPeriod = r:NextNumber(60, 160),
						InAmp = r:NextNumber(15, 55),
						UpPeriod = r:NextNumber(25, 70),
						UpAmp = r:NextNumber(3, 10),
						YawRate = r:NextNumber(-0.012, 0.012),
						Phase = r:NextNumber(0, math.pi * 2),
					})
				end
			elseif d:GetAttribute("Backdrop") then
				table.insert(
					rocks,
					{ Part = d, Pos = d.Position, Radius = math.max(d.Size.X, d.Size.Z) * 0.5 }
				)
				table.insert(solids, d)
				castParams.FilterDescendantsInstances = solids
				overlapParams.FilterDescendantsInstances = solids
			elseif d:GetAttribute("Wander") and d.LocalTransparencyModifier < 1 then
				local r = d:GetAttribute("WanderRadius") :: Vector2
				local h = d:GetAttribute("WanderHeight") :: Vector2
				local s = d:GetAttribute("WanderSpeed") :: Vector2
				local centre = d:GetAttribute("WanderCentre") :: Vector3
				local rng = Random.new((d:GetAttribute("WanderSeed") :: number?) or 1)
				local class = (d:GetAttribute("SkyClass") :: string?) or "PROP"
				local a = rng:NextNumber(0, math.pi * 2)
				local core = FlightCore.spawn(
					life,
					class,
					d.Size.Magnitude * 0.5,
					rng,
					{
						Cx = centre.X,
						Cy = centre.Y,
						Cz = centre.Z,
						RMin = r.X,
						RMax = r.Y,
						YMin = h.X,
						YMax = h.Y,
						SMin = s.X,
						SMax = s.Y,
					},
					d.Position.X,
					d.Position.Y,
					d.Position.Z,
					a,
					d:GetAttribute("SkyCanLand") == true
				)
				local f: Flyer = {
					Part = d,
					Core = core,
					Faces = d:GetAttribute("WanderFaces") == true,
					Bob = (d:GetAttribute("WanderBob") :: number?) or 0,
					Spin = if core.Circ > 0 then 1 else -1,
					Yaw = rng:NextNumber(0, math.pi * 2),
					TimeOffset = rng:NextNumber(0, 10),
					Subs = gatherSubs(d),
					ScanIn = rng:NextNumber(0, driverCfg.ScanSeconds),
					Accum = 0,
					Parked = false,
					Env = {},
				}
				f.Env.Blocked = blocked
				f.Env.FindPerch = function(c: FlightCore.Flier)
					return findPerch(c, d.Size.Y)
				end
				table.insert(flyers, f)
				FlightCore.pickWaypoint(core, f.Env, nil)
			end
		end
		for _, d in sky:GetChildren() do
			adopt(d)
		end
		castParams.FilterDescendantsInstances = solids
		overlapParams.FilterDescendantsInstances = solids
		for _, f in flyers do
			FlightCore.pickWaypoint(f.Core, f.Env, nil)
		end
		sky.ChildAdded:Connect(function(d)
			task.wait(driverCfg.AdoptSeconds) -- let its moving pieces arrive with it
			adopt(d)
		end)
		print(
			string.format(
				"[SkyTraffic] %d flyer(s), %d island(s), %d solid group(s)",
				#flyers,
				#rocks,
				#solids
			)
		)

		local localPlayer = Players.LocalPlayer
		local elapsed = 0

		-- hang a flyer's body and its pieces at its current pose
		local function place(f: Flyer, dt: number)
			local core = f.Core
			local at = Vector3.new(core.X, core.Y, core.Z)
			local cf
			if f.Faces then
				local hx, hy, hz = FlightCore.heading(core)
				-- the imported meshes' noses point along -X: a quarter turn lines
				-- them up with lookAt's forward. Bank rolls about the nose.
				cf = CFrame.lookAt(at, at + Vector3.new(hx, hy, hz))
					* CFrame.Angles(0, -math.pi / 2, 0)
					* CFrame.Angles(-core.Bank, 0, 0)
			else
				at += Vector3.new(0, math.sin(elapsed * 0.5 + f.TimeOffset) * f.Bob, 0)
				f.Yaw += dt * 0.05 * f.Spin
				cf = CFrame.new(at) * CFrame.Angles(0, f.Yaw, 0)
			end
			f.Part.CFrame = cf

			-- the moving pieces: flap, spin, flicker, pulse; chained, gaited
			local t = elapsed + f.TimeOffset
			for _, s in f.Subs do
				-- how much this gait lets the piece move right now
				local gate = 1
				local g = s.Gait
				if g == "Flight" then
					gate = core.FlapAmp
				elseif g == "Idle" then
					gate = core.Idle
				elseif g == "Turn" then
					gate = math.abs(core.BankNorm)
				end
				-- the phase clock: a Flight beat runs on the creature's own
				-- speed- and climb-driven clock, everything else on real time
				local clock = if g == "Flight" then core.GaitClock / (math.pi * 2) else t
				local wave = math.sin(clock * s.Rate * math.pi * 2 + s.Phase)
				local hinge = CFrame.identity
				if s.Kind == "Spin" then
					hinge = hingeAbout(s.Hinge, s.Axis, t * s.Rate + s.Phase)
				elseif s.Kind == "Flap" then
					local angle = if g == "Turn" then core.BankNorm * s.Amp else wave * s.Amp * gate
					hinge = hingeAbout(s.Hinge, s.Axis, angle)
				elseif s.Kind == "Flicker" then
					s.Part.Transparency = s.Alpha + gaitCfg.FlickerDepth * gate * (0.5 + 0.5 * wave)
				elseif s.Kind == "Pulse" then
					s.Part.Size = s.BaseSize * (1 + s.Amp * wave * gate)
				end
				local acc = if s.Chain then s.Chain.Acc * hinge else hinge
				s.Acc = acc
				s.Part.CFrame = cf * acc * CFrame.new(s.Offset)
			end
		end

		local function park(f: Flyer)
			local away = CFrame.new(0, driverCfg.HiddenY, 0)
			f.Part.CFrame = away
			for _, s in f.Subs do
				s.Part.CFrame = away
			end
			f.Parked = true
		end

		RunService.Heartbeat:Connect(function(rawDt)
			elapsed += rawDt
			local dt = math.min(rawDt, driverCfg.MaxDt)
			for _, c in drifters do
				local pace = 1
					+ math.sin(elapsed * math.pi * 2 / c.PacePeriod + c.Phase) * c.PaceAmp
				c.Angle -= c.Rate * pace * dt
				c.Yaw += c.YawRate * dt
				local r = c.Radius
					+ math.sin(elapsed * math.pi * 2 / c.InPeriod + c.Phase) * c.InAmp
				local y = c.Y
					+ math.sin(elapsed * math.pi * 2 / c.UpPeriod + c.Phase * 1.7) * c.UpAmp
				c.Part.CFrame = CFrame.new(
					c.Centre + Vector3.new(math.cos(c.Angle) * r, y, math.sin(c.Angle) * r)
				) * CFrame.Angles(0, c.Yaw, 0) * c.Rot
			end
			for _, s in spinners do
				s.Part.CFrame = s.Base * CFrame.Angles(0, elapsed * s.Rate, 0)
				if s.A and s.B then
					local t = (math.sin(elapsed * math.pi * 2 / s.Seconds) + 1) / 2
					s.Part.Color = (s.A :: Color3):Lerp(s.B :: Color3, t)
				end
			end

			local camera = Workspace.CurrentCamera
			local camPos = if camera then camera.CFrame.Position else Vector3.zero
			-- where the local player is, for the small classes' close passes
			local playerPos: Vector3? = nil
			local character = if localPlayer then localPlayer.Character else nil
			local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
			if root and root:IsA("BasePart") then
				playerPos = root.Position
			end

			for i, f in flyers do
				local core = f.Core
				local prof = core.Prof
				f.Accum += rawDt
				local dist = (Vector3.new(core.X, core.Y, core.Z) - camPos).Magnitude
				local interval = FlightCore.updateInterval(prof, dist)
				if f.Accum < interval then
					continue
				end
				-- a throttled creature takes a longer step, never a bigger jump than that
				local step = math.min(f.Accum, math.max(driverCfg.MaxDt, interval * 1.5))
				f.Accum = 0

				local env = f.Env
				local band = core.Band
				-- the local player, only while they are near the hub
				if
					playerPos
					and (playerPos.X - band.Cx) ^ 2 + (playerPos.Z - band.Cz) ^ 2 < life.HubRadius ^ 2
				then
					env.PlayerX, env.PlayerY, env.PlayerZ = playerPos.X, playerPos.Y, playerPos.Z
				else
					env.PlayerX, env.PlayerY, env.PlayerZ = nil, nil, nil
				end

				-- LOOK AHEAD, far enough to cover this creature's turning arc: sweep a
				-- sphere of its size along its heading; anything in the way turns it
				-- early, sideways and up. Not while it is landing or perched.
				f.ScanIn -= step
				if core.Mode == "fly" and core.Present then
					if f.ScanIn <= 0 then
						f.ScanIn = driverCfg.ScanSeconds
						env.AvoidX, env.AvoidY, env.AvoidZ = 0, 0, 0
						local hx, hy, hz = FlightCore.heading(core)
						local dir = Vector3.new(hx, hy, hz)
						local pos = Vector3.new(core.X, core.Y, core.Z)
						local reach = math.min(
							math.max(core.Speed, 8) * driverCfg.ScanReachSeconds
								+ core.TurnRadius * driverCfg.ScanTurnScale
								+ core.Radius,
							driverCfg.MaxCast
						)
						local r = math.clamp(
							core.Radius * driverCfg.ScanSphereScale,
							driverCfg.ScanSphereMin,
							driverCfg.ScanSphereMax
						)
						local hit =
							Workspace:Spherecast(pos - dir * r * 0.5, r, dir * reach, castParams)
						if hit then
							local urgency = 1 - math.clamp(hit.Distance / reach, 0, 1)
							local side = hit.Normal - dir * hit.Normal:Dot(dir)
							if side.Magnitude < 0.1 then
								side = dir:Cross(Vector3.yAxis)
							end
							local avoid = (side.Unit + Vector3.yAxis * driverCfg.AvoidClimb).Unit
								* (driverCfg.AvoidBase + urgency * driverCfg.AvoidGain)
							env.AvoidX, env.AvoidY, env.AvoidZ = avoid.X, avoid.Y, avoid.Z
							-- if the waypoint is behind the obstacle, choose another now
							if urgency > driverCfg.AvoidReplanUrgency then
								local toTarget = Vector3.new(core.TX, core.TY, core.TZ) - pos
								if toTarget.Magnitude > driverCfg.MaxCast then
									toTarget = toTarget.Unit * driverCfg.MaxCast -- only the stretch that matters now
								end
								if
									toTarget.Magnitude > 1
									and Workspace:Spherecast(pos, r, toTarget, castParams)
								then
									FlightCore.pickWaypoint(
										core,
										env,
										math.pi * driverCfg.ReplanAngle
									)
								end
							end
						end
					end
				else
					env.AvoidX, env.AvoidY, env.AvoidZ = 0, 0, 0
				end

				-- and keep clear of each other, by both bodies' sizes
				local sx, sy, sz = 0, 0, 0
				for j, o in flyers do
					if j ~= i and o.Core.Present then
						local oc = o.Core
						local ax, ay, az = FlightCore.separation(
							core,
							oc.Radius,
							core.X - oc.X,
							core.Y - oc.Y,
							core.Z - oc.Z
						)
						sx += ax
						sy += ay
						sz += az
					end
				end
				env.SepX, env.SepY, env.SepZ = sx, sy, sz

				FlightCore.tick(core, step, env)
				if not core.Present then
					if not f.Parked then
						park(f)
					end
					continue
				end
				f.Parked = false
				FlightCore.gait(core, step)
				place(f, step)
			end
		end)
	end)
end

return SkyTraffic
