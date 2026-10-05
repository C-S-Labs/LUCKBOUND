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
local CreatureMotionCore = require(Root.Core.CreatureMotionCore)

local life: any = GameConfig.HubLayout.V2.SkyLife
local driverCfg = life.Driver
local gaitCfg = life.Gait
local perchCfg = life.Perch
local motionCfg = life.Motion

local SkyTraffic = {}

type Rock = { Part: BasePart, Pos: Vector3, Radius: number }
-- the world's obstacles for FlightCore (islands and the far range), shared by every flyer
local obstacles: { FlightCore.Obstacle } = {}
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
	M: CreatureMotionCore.Part?, -- layered motion state (Flap, Pulse, Flicker)
	SpineIdx: number?, -- 1 = the root segment of the creature's spine (serpent / eel locomotion)
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
	Body: CreatureMotionCore.Body,
	MC: any, -- this class's motion profile
	RefRate: number, -- beat rate of the main wing (0: none)
	Spine: CreatureMotionCore.Spine?, -- serpent / eel locomotion: the segments follow the head's trail
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
		local presenceGroup: { FlightCore.Flier } = {}
		local cores: { FlightCore.Flier } = {} -- every flier's core, for the hard stop between bodies
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
						SpineIdx = c:GetAttribute("SubSpine") :: number?,
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
					-- a chained part's beat follows its parent's, lagged behind it, plus its own offset
					sub.Phase = up.Phase + sub.Phase - sub.Lag
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
			for i, sub in list do
				if sub.Kind ~= "Spin" then
					local limit = sub.Part:GetAttribute("SubLimit") :: Vector2?
					sub.M = CreatureMotionCore.newPart(
						sub.Kind,
						sub.Gait,
						sub.Amp,
						sub.Rate,
						sub.Phase,
						sub.Lag,
						{ sub.Axis.X, sub.Axis.Y, sub.Axis.Z },
						{ sub.Offset.X, sub.Offset.Y, sub.Offset.Z },
						{ sub.Hinge.X, sub.Hinge.Y, sub.Hinge.Z },
						i * 1.618 + d.Size.X * 0.01,
						if limit then { limit.X, limit.Y } else nil
					)
				end
			end
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
			elseif d:GetAttribute("FarRange") then
				-- the far range: not solid to the look-ahead, but an obstacle to the planner
				table.insert(obstacles, {
					X = d.Position.X,
					Y = d.Position.Y,
					Z = d.Position.Z,
					R = math.sqrt(d.Size.X ^ 2 + d.Size.Z ^ 2) * 0.5 * driverCfg.ObstacleShape,
					H = d.Size.Y * 0.5 * driverCfg.ObstacleShape,
				})
			elseif d:GetAttribute("Backdrop") then
				table.insert(obstacles, {
					X = d.Position.X,
					Y = d.Position.Y,
					Z = d.Position.Z,
					R = math.sqrt(d.Size.X ^ 2 + d.Size.Z ^ 2) * 0.5 * driverCfg.ObstacleShape,
					H = d.Size.Y * 0.5 * driverCfg.ObstacleShape,
				})
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
				local centreAttr = d:GetAttribute("SkyCentre") :: Vector3?
				local core = FlightCore.spawn(
					life,
					class,
					(d:GetAttribute("SkyRadius") :: number?) or d.Size.Magnitude * 0.5,
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
					d:GetAttribute("SkyCanLand") == true,
					if centreAttr then { centreAttr.X, centreAttr.Y, centreAttr.Z } else nil
				)
				core.Obstacles = obstacles
				local subs = gatherSubs(d)
				local refRate = 0
				for _, sub in subs do
					if sub.M and sub.M.WingLike then
						refRate = sub.Rate
						break
					end
				end
				-- serpent / eel: the segments in order, their arc lengths from the head (Offset.X
				-- runs back along the body), and the wave the server set out
				local spine: CreatureMotionCore.Spine? = nil
				local wavelength = d:GetAttribute("SpineWavelength") :: number?
				if wavelength then
					local ordered: { Sub } = {}
					for _, sub in subs do
						if sub.SpineIdx then
							table.insert(ordered, sub)
						end
					end
					table.sort(ordered, function(first, second)
						return (first.SpineIdx :: number) < (second.SpineIdx :: number)
					end)
					if #ordered >= 2 then
						local arcs: { number } = {}
						for i, sub in ordered do
							sub.SpineIdx = i
							table.insert(arcs, sub.Offset.X)
						end
						local sc = motionCfg.Spine
						spine = CreatureMotionCore.newSpine(
							arcs,
							wavelength,
							(d:GetAttribute("SpineAmp") :: number?) or 0,
							(d:GetAttribute("SpineRate") :: number?) or 0.1,
							d:GetAttribute("SpinePlane") == "vertical",
							sc.HeadAmp,
							sc.StepsPerWave,
							sc.Margin
						)
						local hx0, hy0, hz0 = FlightCore.heading(core)
						CreatureMotionCore.seedTrail(
							spine.Trail,
							d.Position.X,
							d.Position.Y,
							d.Position.Z,
							hx0,
							hy0,
							hz0
						)
					end
				end
				local f: Flyer = {
					Part = d,
					Core = core,
					Faces = d:GetAttribute("WanderFaces") == true,
					Bob = (d:GetAttribute("WanderBob") :: number?) or 0,
					Spin = if core.Circ > 0 then 1 else -1,
					Yaw = rng:NextNumber(0, math.pi * 2),
					TimeOffset = rng:NextNumber(0, 10),
					Subs = subs,
					Body = CreatureMotionCore.newBody(),
					MC = motionCfg.Classes[class] or motionCfg.Classes.SMALL,
					RefRate = refRate,
					Spine = spine,
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
				table.insert(cores, core)
				core.Neighbours = cores
				FlightCore.pickWaypoint(core, f.Env, nil)
			end
		end
		for _, d in sky:GetChildren() do
			adopt(d)
		end
		castParams.FilterDescendantsInstances = solids
		overlapParams.FilterDescendantsInstances = solids
		for _, f in flyers do
			FlightCore.relocate(f.Core) -- never start inside an island
			FlightCore.pickWaypoint(f.Core, f.Env, nil)
			if f.Core.Prof.Presence then
				table.insert(presenceGroup, f.Core)
			end
		end
		-- exactly Floor..Ceiling colossals at once: the extra ones a server spawns wait their turn
		FlightCore.presenceStep(presenceGroup, 0)
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
			local body = f.Body
			CreatureMotionCore.updateBody(body, core, dt, f.MC, motionCfg, f.RefRate)
			local at = Vector3.new(core.X, core.Y + body.Heave, core.Z)
			local cf
			if f.Faces then
				local hx, hy, hz = FlightCore.heading(core)
				-- the imported meshes' noses point along -X: a quarter turn lines
				-- them up with lookAt's forward. Bank rolls about the nose; the
				-- beat's pitch (nose up) is about the mesh's Z.
				cf = CFrame.lookAt(at, at + Vector3.new(hx, hy, hz))
					* CFrame.Angles(0, -math.pi / 2, 0)
					* CFrame.Angles(-core.Bank, 0, 0)
					* CFrame.Angles(0, 0, -body.PitchOff)
			else
				at += Vector3.new(0, math.sin(elapsed * 0.5 + f.TimeOffset) * f.Bob, 0)
				f.Yaw += dt * 0.05 * f.Spin
				cf = CFrame.new(at) * CFrame.Angles(0, f.Yaw, 0)
			end
			local sp = f.Spine
			if sp and f.Faces then
				-- the head leads on its trail and sways with the wave; the whole body (and every
				-- part hung off it) moves with it
				local hx, hy, hz = FlightCore.heading(core)
				local tr = sp.Trail
				if not CreatureMotionCore.pushTrail(tr, at.X, at.Y, at.Z) then
					CreatureMotionCore.seedTrail(tr, at.X, at.Y, at.Z, hx, hy, hz) -- it was moved, not flown
					CreatureMotionCore.pushTrail(tr, at.X, at.Y, at.Z)
				end
				CreatureMotionCore.solveSpine(sp, at.X, at.Y, at.Z, elapsed + f.TimeOffset)
				local head = Vector3.new(sp.PX[1], sp.PY[1], sp.PZ[1])
				cf = CFrame.lookAt(head, head + Vector3.new(sp.TX[1], sp.TY[1], sp.TZ[1]))
					* CFrame.Angles(0, -math.pi / 2, 0)
					* CFrame.Angles(-core.Bank, 0, 0)
					* CFrame.Angles(0, 0, -body.PitchOff)
			end
			f.Part.CFrame = cf
			local cfInv = if sp then cf:Inverse() else cf

			-- the moving pieces, parents first (chain rule: acc = parent.acc * hinge)
			local t = elapsed + f.TimeOffset
			for _, s in f.Subs do
				local hinge = CFrame.identity
				local m = s.M
				if m == nil then
					hinge = hingeAbout(s.Hinge, s.Axis, t * s.Rate + s.Phase)
				else
					CreatureMotionCore.stepPart(
						m,
						body,
						if s.Chain then s.Chain.M else nil,
						dt,
						f.MC,
						motionCfg
					)
					if s.Kind == "Flap" then
						hinge = hingeAbout(s.Hinge, s.Axis, m.Angle)
					elseif s.Kind == "Flicker" then
						s.Part.Transparency = s.Alpha + gaitCfg.FlickerDepth * m.Flick
					elseif s.Kind == "Pulse" then
						s.Part.Size = s.BaseSize * m.Scale
					end
				end
				local acc = if s.Chain then s.Chain.Acc * hinge else hinge
				local segAt = s.SpineIdx
				if sp and segAt then
					-- a spine segment sits on the trail, oriented by the path (parts hung on it
					-- inherit this pose through Acc, as for any chained part)
					local o = segAt + 1
					local pos = Vector3.new(sp.PX[o], sp.PY[o], sp.PZ[o])
					local frame = CFrame.lookAt(
						pos,
						pos + Vector3.new(sp.TX[o], sp.TY[o], sp.TZ[o])
					) * CFrame.Angles(0, -math.pi / 2, 0)
					acc = cfInv
						* (frame * CFrame.new(0, s.Offset.Y, s.Offset.Z))
						* CFrame.new(s.Offset):Inverse()
				end
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

			-- colossals: at least Floor are always here, never more than Ceiling
			FlightCore.presenceStep(presenceGroup, dt)
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
				env.Others = cores

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
