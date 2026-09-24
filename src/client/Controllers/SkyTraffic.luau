--!strict
-- THE SKY TRAFFIC round the Crossroads (owner, 2026-09-24: "the backdrop props
-- should all be independent, and move at varying speeds, perhaps even changing
-- directions ... avoid collisions with existing structures and other props").
--
-- The server (HubV2.buildSky) places the props and marks each with Wander and
-- the band it may use. Here, per client, every one flies its own course:
--
--   * it heads for a waypoint somewhere in its band, then picks another --
--     usually onward round the hub, sometimes doubling back;
--   * its speed drifts between its limits, so no two keep pace;
--   * it steers away from the hub (a keep-out cylinder round the whole
--     structure, levitator included), from every backdrop mountain and from
--     every other prop, by a clearance scaled to both their sizes;
--   * ships and the whale face the way they fly and bank into turns; isles,
--     clouds and crystals turn slowly on their own.
--
-- Client-side decoration, so each player's sky moves on its own; props the
-- device's graphics level hides (Detail, see HubEffects) are skipped.

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)

local SkyTraffic = {}

local HUB_KEEP_OUT = 320 -- studs from the hub centre: nothing flies inside this
local HUB_TOP, HUB_BOTTOM = 130, -300 -- the structure's vertical extent, levitator included
local CLEARANCE = 18 -- extra studs kept between any two things

type Flyer = {
	Part: BasePart,
	Pos: Vector3,
	Vel: Vector3,
	Target: Vector3,
	Speed: number,
	SpeedGoal: number,
	NextSpeedChange: number,
	Radius: number, -- its own size, for clearance
	Band: { Centre: Vector3, RMin: number, RMax: number, YMin: number, YMax: number, SMin: number, SMax: number },
	Faces: boolean,
	Bob: number,
	Phase: number,
	Yaw: number,
	Bank: number,
	Rng: Random,
}

local function waypoint(f: Flyer, fromAngle: number): Vector3
	local b = f.Band
	-- onward round the hub most of the time, now and then back the other way
	local turn = if f.Rng:NextNumber() < 0.18 then -f.Rng:NextNumber(0.4, 1.2) else f.Rng:NextNumber(0.3, 1.1)
	local a = fromAngle + turn * (if f.Phase > 0 then 1 else -1)
	local r = f.Rng:NextNumber(b.RMin, b.RMax)
	return Vector3.new(b.Centre.X + math.cos(a) * r, f.Rng:NextNumber(b.YMin, b.YMax), b.Centre.Z + math.sin(a) * r)
end

local function angleOf(f: Flyer, p: Vector3): number
	return math.atan2(p.Z - f.Band.Centre.Z, p.X - f.Band.Centre.X)
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

		local flyers: { Flyer } = {}
		local rocks: { { Pos: Vector3, Radius: number } } = {}
		for _, d in sky:GetChildren() do
			if not d:IsA("BasePart") then
				continue
			end
			if d:GetAttribute("Backdrop") then
				-- a mountain: keep clear of its bulk (a sphere a little inside its box)
				table.insert(rocks, { Pos = d.Position, Radius = math.max(d.Size.X, d.Size.Z) * 0.55 })
			elseif d:GetAttribute("Wander") and d.LocalTransparencyModifier < 1 then
				local r = d:GetAttribute("WanderRadius") :: Vector2
				local h = d:GetAttribute("WanderHeight") :: Vector2
				local s = d:GetAttribute("WanderSpeed") :: Vector2
				local rng = Random.new((d:GetAttribute("WanderSeed") :: number?) or 1)
				local f: Flyer = {
					Part = d,
					Pos = d.Position,
					Vel = Vector3.zero,
					Target = d.Position,
					Speed = rng:NextNumber(s.X, s.Y),
					SpeedGoal = rng:NextNumber(s.X, s.Y),
					NextSpeedChange = rng:NextNumber(4, 12),
					Radius = d.Size.Magnitude * 0.5,
					Band = { Centre = d:GetAttribute("WanderCentre") :: Vector3, RMin = r.X, RMax = r.Y,
						YMin = h.X, YMax = h.Y, SMin = s.X, SMax = s.Y },
					Faces = d:GetAttribute("WanderFaces") == true,
					Bob = (d:GetAttribute("WanderBob") :: number?) or 0,
					Phase = if rng:NextNumber() < 0.3 then -rng:NextNumber(0.1, 6) else rng:NextNumber(0.1, 6),
					Yaw = rng:NextNumber(0, math.pi * 2),
					Bank = 0,
					Rng = rng,
				}
				f.Target = waypoint(f, angleOf(f, f.Pos))
				table.insert(flyers, f)
			end
		end
		print(string.format("[SkyTraffic] %d flyer(s), %d backdrop obstacle(s)", #flyers, #rocks))

		local elapsed = 0
		RunService.Heartbeat:Connect(function(dt)
			elapsed += dt
			dt = math.min(dt, 0.1)
			for i, f in flyers do
				-- speed drifts toward a goal that itself changes now and then
				f.NextSpeedChange -= dt
				if f.NextSpeedChange <= 0 then
					f.SpeedGoal = f.Rng:NextNumber(f.Band.SMin, f.Band.SMax)
					f.NextSpeedChange = f.Rng:NextNumber(5, 15)
				end
				f.Speed += (f.SpeedGoal - f.Speed) * math.min(1, dt * 0.3)

				local to = f.Target - f.Pos
				if to.Magnitude < 40 then
					f.Target = waypoint(f, angleOf(f, f.Pos))
					to = f.Target - f.Pos
				end
				local steer = to.Unit * f.Speed

				-- keep out of the hub's cylinder
				local flat = Vector3.new(f.Pos.X - f.Band.Centre.X, 0, f.Pos.Z - f.Band.Centre.Z)
				local keep = HUB_KEEP_OUT + f.Radius
				if flat.Magnitude < keep + 60 and f.Pos.Y < f.Band.Centre.Y + HUB_TOP + f.Radius
					and f.Pos.Y > f.Band.Centre.Y + HUB_BOTTOM - f.Radius then
					local push = 1 - math.clamp((flat.Magnitude - keep) / 60, 0, 1)
					steer += flat.Unit * f.Speed * 3 * push
				end
				-- keep clear of the mountains
				for _, rock in rocks do
					local away = f.Pos - rock.Pos
					local d = away.Magnitude
					local need = rock.Radius + f.Radius + CLEARANCE
					if d < need + 80 then
						steer += away.Unit * f.Speed * 3 * (1 - math.clamp((d - need) / 80, 0, 1))
					end
				end
				-- and of each other
				for j, o in flyers do
					if j ~= i then
						local away = f.Pos - o.Pos
						local d = away.Magnitude
						local need = f.Radius + o.Radius + CLEARANCE
						if d < need + 30 and d > 0.01 then
							steer += away.Unit * f.Speed * 2.5 * (1 - math.clamp((d - need) / 30, 0, 1))
						end
					end
				end

				local want = if steer.Magnitude > 0.01 then steer.Unit * f.Speed else f.Vel
				f.Vel = f.Vel:Lerp(want, math.min(1, dt * 0.8))
				f.Pos += f.Vel * dt

				local bob = math.sin(elapsed * 0.5 + f.Phase) * f.Bob
				local at = f.Pos + Vector3.new(0, bob, 0)
				local cf
				if f.Faces and f.Vel.Magnitude > 0.5 then
					local fwd = Vector3.new(f.Vel.X, 0, f.Vel.Z)
					local turnRate = if fwd.Magnitude > 0.01 then fwd.Unit:Cross(want.Unit).Y else 0
					f.Bank += (math.clamp(turnRate * 1.5, -0.3, 0.3) - f.Bank) * math.min(1, dt * 1.5)
					-- the imported meshes' noses point along -X: a quarter turn
					-- lines them up with lookAt's forward
					cf = CFrame.lookAt(at, at + (if fwd.Magnitude > 0.01 then fwd else Vector3.new(1, 0, 0)))
						* CFrame.Angles(0, -math.pi / 2, 0) * CFrame.Angles(f.Bank, 0, 0)
				else
					f.Yaw += dt * 0.05 * (if f.Phase > 0 then 1 else -1)
					cf = CFrame.new(at) * CFrame.Angles(0, f.Yaw, 0)
				end
				f.Part.CFrame = cf
			end
		end)
	end)
end

return SkyTraffic
