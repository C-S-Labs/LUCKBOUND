--!strict
-- THE FLIGHT OF THE SKY CREATURES: the pure half of SkyTraffic.
--
-- No Roblox types, so it runs headless (tests, sweeps). All numbers are plain
-- x/y/z scalars. Every tunable lives in GameConfig.HubLayout.V2.SkyLife and is
-- passed in as `cfg`; nothing here is a per-species special case -- a creature
-- is its CLASS profile plus its own body radius.
--
-- THE RULES (owner, 2026-10-05):
--   * A creature ALWAYS travels forward. Its position changes only by
--     heading * speed * dt: velocity IS heading * speed, there is no sideways
--     translation and no instant yaw. Heading (yaw and pitch) turns no faster
--     than a rate set by the creature's size and current speed.
--   * It slows before a tight turn: a slower creature turns on a tighter
--     radius (radius scales with the square of speed / cruise speed), so the
--     driver eases the speed goal down as the heading error grows.
--   * Bank comes from how hard it is turning, not from steering directly.
--   * Clearance is by SCALE: every class keeps out of a cylinder about the hub
--     axis (HubClearance), below a roof (OverheadMinY above the deck). Small
--     classes may cross over the hub; the big ones never come near it.
--   * Landing is for the small and medium only (a perch state machine:
--     fly -> approach -> land -> perch -> takeoff -> fly); colossals never.
--
-- Random numbers come from the Random the caller owns (never math.random).

local FlightCore = {}

export type Rng = any
export type Cfg = any

export type Band = {
	Cx: number,
	Cy: number, -- the deck: where OverheadMinY is measured from
	Cz: number,
	RMin: number,
	RMax: number,
	YMin: number, -- absolute heights
	YMax: number,
	SMin: number,
	SMax: number,
}

export type PerchSpot = { X: number, Y: number, Z: number, FaceYaw: number }

export type Flier = {
	Cfg: Cfg,
	Class: string,
	Prof: Cfg,
	Rng: Rng,
	Band: Band,
	Radius: number,
	TurnRadius: number,
	CanLand: boolean,
	Roofed: boolean, -- true when climbing over the keep-out is possible for this class
	X: number,
	Y: number,
	Z: number,
	Yaw: number,
	Pitch: number,
	Speed: number,
	SpeedGoal: number,
	NextSpeedChange: number,
	Bank: number,
	YawRate: number,
	Circ: number, -- preferred circulation, +1 or -1
	TX: number,
	TY: number,
	TZ: number,
	BestDist: number,
	StuckFor: number,
	Mode: string, -- fly | approach | land | perch | takeoff
	ModeTime: number,
	Perch: PerchSpot?,
	PerchCooldown: number,
	HoldFor: number,
	AX: number, -- approach point
	AY: number,
	AZ: number,
	Present: boolean,
	PresenceLeft: number,
	-- gait outputs (read by the driver)
	GaitClock: number,
	FlapAmp: number,
	Gliding: boolean,
	GaitLeft: number,
	Idle: number,
	BankNorm: number,
	Warp: number,
}

local EPS = 1e-6
local TWO_PI = math.pi * 2

local function wrap(a: number): number
	return (a + math.pi) % TWO_PI - math.pi
end

local function clamp(v: number, lo: number, hi: number): number
	return math.max(lo, math.min(hi, v))
end

local function approach(v: number, goal: number, step: number): number
	return v + clamp(goal - v, -step, step)
end

local function rangeOf(rng: Rng, lo: number, hi: number): number
	if hi <= lo then
		return lo
	end
	return rng:NextNumber(lo, hi)
end

-- ---------------------------------------------------------------- kinematics

--- Unit heading (the direction of travel).
function FlightCore.heading(f: Flier): (number, number, number)
	local cp = math.cos(f.Pitch)
	return cp * math.cos(f.Yaw), math.sin(f.Pitch), cp * math.sin(f.Yaw)
end

--- Velocity. By construction heading * speed -- nothing else moves a flier.
function FlightCore.velocity(f: Flier): (number, number, number)
	local hx, hy, hz = FlightCore.heading(f)
	return hx * f.Speed, hy * f.Speed, hz * f.Speed
end

--- Heading change rate (rad/s) at the current speed. A radius of
--- TurnRadius at cruise speed; slower means a tighter turn, faster a wider one.
function FlightCore.turnRate(f: Flier): number
	local fl = f.Cfg.Flight
	local cruise = math.max(f.Band.SMax, EPS)
	local ratio = clamp(f.Speed / cruise, fl.TurnSpeedFloor, fl.TurnSpeedCeil)
	return cruise / (f.TurnRadius * ratio)
end

--- Highest turn rate this creature can reach (at its slowest flight speed).
local function maxTurnRate(f: Flier): number
	local fl = f.Cfg.Flight
	local cruise = math.max(f.Band.SMax, EPS)
	local lowest = math.max(f.Band.SMin * f.Prof.MinSpeedScale, EPS)
	local ratio = clamp(lowest / cruise, fl.TurnSpeedFloor, fl.TurnSpeedCeil)
	return cruise / (f.TurnRadius * ratio)
end

--- One step of motion: turn toward `want` (a direction, need not be unit) as
--- fast as the rate limit allows, ease speed toward `speedGoal`, move FORWARD.
function FlightCore.advance(
	f: Flier,
	dt: number,
	wx: number,
	wy: number,
	wz: number,
	speedGoal: number
)
	local fl = f.Cfg.Flight
	local prof = f.Prof
	local rate = FlightCore.turnRate(f)
	local maxYaw = rate * dt
	local flat = math.sqrt(wx * wx + wz * wz)
	local yawBefore = f.Yaw
	if flat > EPS then
		local delta = wrap(math.atan2(wz, wx) - f.Yaw)
		if math.abs(delta) > math.pi - fl.OppositeEpsilon then
			-- dead astern: commit to one side instead of flipping every frame
			delta = math.abs(delta) * f.Circ
		end
		f.Yaw = wrap(f.Yaw + clamp(delta, -maxYaw, maxYaw))
	end
	local wlen = math.sqrt(wx * wx + wy * wy + wz * wz)
	if wlen > EPS then
		local wantPitch = clamp(math.asin(clamp(wy / wlen, -1, 1)), -prof.MaxPitch, prof.MaxPitch)
		f.Pitch += clamp(
			wantPitch - f.Pitch,
			-maxYaw * fl.PitchRateScale,
			maxYaw * fl.PitchRateScale
		)
	end
	f.Pitch = clamp(f.Pitch, -prof.MaxPitch, prof.MaxPitch)
	f.Speed = math.max(0, approach(f.Speed, speedGoal, prof.Accel * dt))
	-- forward only
	local hx, hy, hz = FlightCore.heading(f)
	f.X += hx * f.Speed * dt
	f.Y += hy * f.Speed * dt
	f.Z += hz * f.Speed * dt
	-- bank follows the turn
	if dt > EPS then
		f.YawRate = wrap(f.Yaw - yawBefore) / dt
	end
	local norm = clamp(f.YawRate / math.max(maxTurnRate(f), EPS), -1, 1)
	f.BankNorm += (norm - f.BankNorm) * math.min(1, dt * fl.BankSmoothing)
	f.Bank = f.BankNorm * prof.MaxBank
end

-- ---------------------------------------------------------------- keep-out

--- Is the point inside the keep-out volume of this class? The volume is the
--- cylinder of radius HubClearance about the hub axis, from far below up to
--- OverheadMinY above the deck. `padH` fattens it sideways, `padV` upward.
function FlightCore.inKeepOut(
	prof: Cfg,
	cx: number,
	cy: number,
	cz: number,
	x: number,
	y: number,
	z: number,
	padH: number,
	padV: number
): boolean
	local c = prof.HubClearance
	if c <= 0 then
		return false
	end
	local dx, dz = x - cx, z - cz
	local r = c + padH
	if dx * dx + dz * dz >= r * r then
		return false
	end
	return (y - cy) < prof.OverheadMinY + padV
end

--- Does the straight segment a->b pass through the (padded) keep-out?
function FlightCore.segmentHitsKeepOut(
	prof: Cfg,
	cx: number,
	cy: number,
	cz: number,
	ax: number,
	ay: number,
	az: number,
	bx: number,
	by: number,
	bz: number,
	pad: number
): boolean
	local c = prof.HubClearance
	if c <= 0 then
		return false
	end
	local r = c + pad
	local roof = cy + prof.OverheadMinY + pad
	local dx, dz = bx - ax, bz - az
	local ox, oz = ax - cx, az - cz
	local qa = dx * dx + dz * dz
	if qa < EPS then
		return FlightCore.inKeepOut(prof, cx, cy, cz, ax, ay, az, pad, pad)
	end
	local qb = 2 * (ox * dx + oz * dz)
	local qc = ox * ox + oz * oz - r * r
	local disc = qb * qb - 4 * qa * qc
	if disc <= 0 then
		return false
	end
	local root = math.sqrt(disc)
	local s0 = (-qb - root) / (2 * qa)
	local s1 = (-qb + root) / (2 * qa)
	if s1 < 0 or s0 > 1 then
		return false
	end
	-- the stretch of the leg inside the cylinder is a hit wherever it is below the roof
	local t0, t1 = math.max(s0, 0), math.min(s1, 1)
	local y0 = ay + (by - ay) * t0
	local y1 = ay + (by - ay) * t1
	return math.min(y0, y1) < roof
end

--- Steering away from the keep-out: a vector (zero when nothing is near).
--- Turns the creature along the volume's edge (keeping its own circulation),
--- and over it for classes that can clear the roof. Starts early enough for
--- the creature's turning circle, so the edge is never crossed.
function FlightCore.keepOutSteer(
	f: Flier,
	cx: number,
	cy: number,
	cz: number
): (number, number, number, boolean)
	local prof = f.Prof
	local fl = f.Cfg.Flight
	local c = prof.HubClearance
	if c <= 0 then
		return 0, 0, 0, false
	end
	local margin = fl.KeepOutMargin
		+ fl.KeepOutTurnScale * f.TurnRadius
		+ fl.KeepOutLead * math.max(f.Speed, f.Band.SMax)
	local hx, hy, hz = FlightCore.heading(f)
	local px, py, pz = f.X + hx * margin, f.Y + hy * margin, f.Z + hz * margin
	local vpad = fl.KeepOutRoofMargin
	local here = FlightCore.inKeepOut(prof, cx, cy, cz, f.X, f.Y, f.Z, margin, vpad)
	local ahead = FlightCore.inKeepOut(prof, cx, cy, cz, px, py, pz, margin * 0.5, vpad)
	if not (here or ahead) then
		return 0, 0, 0, false
	end
	local dx, dz = f.X - cx, f.Z - cz
	local d = math.sqrt(dx * dx + dz * dz)
	local ux, uz
	if d < EPS then
		ux, uz = math.cos(f.Yaw), math.sin(f.Yaw)
	else
		ux, uz = dx / d, dz / d
	end
	-- along the edge, in the direction we are already circulating
	local side = ux * hz - uz * hx
	if math.abs(side) < 1e-3 then
		side = f.Circ
	end
	local sgn = if side >= 0 then 1 else -1
	local tx, tz = -uz * sgn, ux * sgn
	local depth = clamp((c + margin - d) / math.max(margin, EPS), 0, 1)
	local push = fl.KeepOutPush * depth
	local sx = tx + ux * push
	local sz = tz + uz * push
	local sy = 0.0
	if f.Roofed then
		local roof = cy + prof.OverheadMinY
		if f.Y < roof + fl.KeepOutRoofMargin then
			sy = fl.KeepOutClimb
		end
	end
	local weight = fl.KeepOutWeight * (fl.KeepOutFloor + (1 - fl.KeepOutFloor) * depth)
	return sx * weight, sy * weight, sz * weight, true
end

--- Push away from another creature, scaled by both bodies.
function FlightCore.separation(
	f: Flier,
	otherRadius: number,
	dx: number,
	dy: number,
	dz: number
): (number, number, number)
	local fl = f.Cfg.Flight
	local d = math.sqrt(dx * dx + dy * dy + dz * dz)
	if d < EPS then
		return 0, 0, 0
	end
	local need = (f.Radius + otherRadius) * f.Prof.SeparationScale
	local zone = need * fl.SeparationFalloff
	if d >= need + zone then
		return 0, 0, 0
	end
	local k = fl.SeparationStrength * (1 - clamp((d - need) / math.max(zone, EPS), 0, 1)) / d
	return dx * k, dy * k, dz * k
end

-- ---------------------------------------------------------------- waypoints

local function angleOf(f: Flier): number
	return math.atan2(f.Z - f.Band.Cz, f.X - f.Band.Cx)
end

--- Choose the next waypoint inside the class band. Never a point inside the
--- keep-out, never a leg that cuts through it. `env.Blocked(x, y, z, r)` (the
--- driver's real-geometry test) and `env.PlayerX/Y/Z` (for a close approach)
--- are optional.
function FlightCore.pickWaypoint(f: Flier, env: any?, extraAngle: number?)
	local b = f.Band
	local prof = f.Prof
	local fl = f.Cfg.Flight
	local rng = f.Rng
	local pad = fl.WaypointPad
	local blocked = if env then env.Blocked else nil
	local function ok(x: number, y: number, z: number): boolean
		if FlightCore.inKeepOut(prof, b.Cx, b.Cy, b.Cz, x, y, z, pad, pad) then
			return false
		end
		if FlightCore.segmentHitsKeepOut(prof, b.Cx, b.Cy, b.Cz, f.X, f.Y, f.Z, x, y, z, pad) then
			return false
		end
		if blocked and blocked(x, y, z, f.Radius + fl.WaypointPad) then
			return false
		end
		return true
	end
	f.BestDist, f.StuckFor = math.huge, 0

	-- a close pass over the player, for the classes that do that
	if env and env.PlayerX and prof.CloseApproach > 0 and rng:NextNumber() < prof.CloseApproach then
		for _ = 1, fl.WaypointTries do
			local a = rng:NextNumber(0, TWO_PI)
			local r = rng:NextNumber(0, prof.CloseRadius)
			local x = env.PlayerX + math.cos(a) * r
			local z = env.PlayerZ + math.sin(a) * r
			local y = math.max(
				env.PlayerY + rangeOf(rng, prof.CloseHeightMin, prof.CloseHeightMax),
				b.Cy + prof.OverheadMinY + pad
			)
			if y >= b.YMin and y <= b.YMax + prof.CloseHeightMax and ok(x, y, z) then
				f.TX, f.TY, f.TZ = x, y, z
				return
			end
		end
	end

	local from = angleOf(f) + (extraAngle or 0)
	local roll = rng:NextNumber()
	local turn
	if roll < fl.AcrossChance then
		turn = math.pi + rng:NextNumber(-fl.AcrossSpread, fl.AcrossSpread)
	elseif roll < fl.AcrossChance + fl.BackChance then
		turn = -rng:NextNumber(fl.BackMin, fl.BackMax)
	else
		turn = rng:NextNumber(fl.OnwardMin, fl.OnwardMax)
	end
	local a = from + turn * f.Circ
	local px, py, pz = b.Cx, f.Y, b.Cz
	for _ = 1, fl.WaypointTries do
		local r = rangeOf(rng, b.RMin, b.RMax)
		px = b.Cx + math.cos(a) * r
		py = rangeOf(rng, b.YMin, b.YMax)
		pz = b.Cz + math.sin(a) * r
		if ok(px, py, pz) then
			f.TX, f.TY, f.TZ = px, py, pz
			return
		end
		a += rng:NextNumber(fl.RetryAngleMin, fl.RetryAngleMax) * f.Circ
	end
	-- nothing clear: onward along the outside of the band, which always is
	local fa = angleOf(f) + fl.FallbackAngle * f.Circ
	f.TX = b.Cx + math.cos(fa) * b.RMax
	f.TY = clamp(f.Y, b.YMin, b.YMax)
	f.TZ = b.Cz + math.sin(fa) * b.RMax
end

-- ---------------------------------------------------------------- creation

--- A new flier of `class` with body radius `radius`, somewhere in `band`.
--- `x, y, z, yaw` are its start; the first heading is `yaw`, level.
function FlightCore.spawn(
	cfg: Cfg,
	class: string,
	radius: number,
	rng: Rng,
	band: Band,
	x: number,
	y: number,
	z: number,
	yaw: number,
	canLand: boolean?
): Flier
	local prof = cfg.Classes[class]
	local f: Flier = {
		Cfg = cfg,
		Class = class,
		Prof = prof,
		Rng = rng,
		Band = band,
		Radius = radius,
		TurnRadius = clamp(radius * prof.TurnRadiusScale, prof.TurnRadiusMin, prof.TurnRadiusMax),
		CanLand = canLand == true and prof.PerchChance > 0,
		Roofed = prof.OverheadMinY <= (band.YMax - band.Cy),
		X = x,
		Y = y,
		Z = z,
		Yaw = yaw,
		Pitch = 0,
		Speed = rangeOf(rng, band.SMin, band.SMax),
		SpeedGoal = rangeOf(rng, band.SMin, band.SMax),
		NextSpeedChange = rangeOf(rng, cfg.Flight.SpeedChangeMin, cfg.Flight.SpeedChangeMax),
		Bank = 0,
		YawRate = 0,
		Circ = if rng:NextNumber() < cfg.Flight.CounterChance then -1 else 1,
		TX = x,
		TY = y,
		TZ = z,
		BestDist = math.huge,
		StuckFor = 0,
		Mode = "fly",
		ModeTime = 0,
		Perch = nil,
		PerchCooldown = rangeOf(rng, cfg.Perch.InitialDelayMin, cfg.Perch.InitialDelayMax),
		HoldFor = 0,
		AX = x,
		AY = y,
		AZ = z,
		Present = true,
		PresenceLeft = 0,
		GaitClock = rng:NextNumber(0, TWO_PI),
		FlapAmp = 1,
		Gliding = false,
		GaitLeft = rangeOf(rng, prof.FlapMin, prof.FlapMax),
		Idle = 0,
		BankNorm = 0,
		Warp = 1,
	}
	local pr = prof.Presence
	if pr then
		-- a creature that comes and goes: start present or absent at random
		f.Present = rng:NextNumber() < pr.StartPresent
		f.PresenceLeft = if f.Present
			then rangeOf(rng, pr.PresentMin, pr.PresentMax)
			else rangeOf(rng, pr.AbsentMin, pr.AbsentMax)
	end
	-- never start already heading into the keep-out: if the start is near it,
	-- begin along its edge, in the creature's own circulation
	local _, _, _, near = FlightCore.keepOutSteer(f, band.Cx, band.Cy, band.Cz)
	if near then
		f.Yaw = wrap(math.atan2(z - band.Cz, x - band.Cx) + (math.pi / 2) * f.Circ)
	end
	return f
end

--- Put an arriving creature on the outer edge of its band, flying inward
--- along the edge (never inside the keep-out).
function FlightCore.enter(f: Flier)
	local b = f.Band
	local a = f.Rng:NextNumber(0, TWO_PI)
	f.X = b.Cx + math.cos(a) * b.RMax
	f.Z = b.Cz + math.sin(a) * b.RMax
	f.Y = rangeOf(f.Rng, b.YMin, b.YMax)
	-- tangent to the circle: along the edge, in its circulation
	f.Yaw = wrap(a + (math.pi / 2) * f.Circ)
	f.Pitch = 0
	f.Speed = rangeOf(f.Rng, b.SMin, b.SMax)
	f.Mode = "fly"
	f.Perch = nil
	f.BankNorm, f.Bank, f.YawRate = 0, 0, 0
	FlightCore.pickWaypoint(f, nil, nil)
end

-- ---------------------------------------------------------------- perching

--- Begin a landing at `spot`. The caller has already checked the spot is a
--- real surface and clear (a driver concern). Returns false (and does nothing)
--- for a creature that may not land.
function FlightCore.beginPerch(f: Flier, spot: PerchSpot): boolean
	if not f.CanLand or f.Mode ~= "fly" then
		return false
	end
	local pc = f.Cfg.Perch
	local dist = math.max(pc.ApproachDistance, f.TurnRadius * pc.ApproachTurns)
	local fx, fz = math.cos(spot.FaceYaw), math.sin(spot.FaceYaw)
	f.Perch = spot
	f.AX = spot.X - fx * dist
	f.AZ = spot.Z - fz * dist
	f.AY = spot.Y + dist * math.tan(pc.ApproachSlope)
	f.Mode, f.ModeTime = "approach", 0
	f.BestDist, f.StuckFor = math.huge, 0
	return true
end

local function endPerchAttempt(f: Flier, env: any?)
	f.Mode, f.ModeTime = "fly", 0
	f.Perch = nil
	f.PerchCooldown = rangeOf(f.Rng, f.Cfg.Perch.RetryDelayMin, f.Cfg.Perch.RetryDelayMax)
	FlightCore.pickWaypoint(f, env, nil)
end

-- ---------------------------------------------------------------- the tick

local function distTo(f: Flier, x: number, y: number, z: number): number
	local dx, dy, dz = x - f.X, y - f.Y, z - f.Z
	return math.sqrt(dx * dx + dy * dy + dz * dz)
end

--- Presence: colossals come and go over long cycles. Returns true while the
--- creature is present.
local function tickPresence(f: Flier, dt: number): boolean
	local pr = f.Prof.Presence
	if not pr then
		return true
	end
	f.PresenceLeft -= dt
	if f.PresenceLeft <= 0 then
		if f.Present then
			f.Present = false
			f.PresenceLeft = rangeOf(f.Rng, pr.AbsentMin, pr.AbsentMax)
		else
			f.Present = true
			f.PresenceLeft = rangeOf(f.Rng, pr.PresentMin, pr.PresentMax)
			FlightCore.enter(f)
		end
	end
	return f.Present
end

--- One simulation step.
--- env (all optional): AvoidX/Y/Z (the driver's look-ahead steer), SepX/Y/Z
--- (summed FlightCore.separation), Blocked, PlayerX/Y/Z, FindPerch(f).
function FlightCore.tick(f: Flier, dt: number, env: any)
	if not tickPresence(f, dt) then
		return
	end
	local fl = f.Cfg.Flight
	local pc = f.Cfg.Perch
	local prof = f.Prof
	local b = f.Band
	f.ModeTime += dt
	local mode = f.Mode

	if mode == "perch" then
		local spot = f.Perch :: PerchSpot
		f.Speed = 0
		f.Yaw = wrap(
			f.Yaw + clamp(wrap(spot.FaceYaw - f.Yaw), -pc.PerchTurnRate * dt, pc.PerchTurnRate * dt)
		)
		f.Pitch = approach(f.Pitch, 0, pc.PerchTurnRate * dt)
		f.YawRate = 0
		f.BankNorm += (0 - f.BankNorm) * math.min(1, dt * fl.BankSmoothing)
		f.Bank = f.BankNorm * prof.MaxBank
		f.HoldFor -= dt
		if f.HoldFor <= 0 then
			f.Mode, f.ModeTime = "takeoff", 0
		end
		return
	end

	local wx, wy, wz = 0.0, 0.0, 0.0
	local goal = f.SpeedGoal
	local sepX, sepY, sepZ = env.SepX or 0, env.SepY or 0, env.SepZ or 0

	if mode == "takeoff" then
		local spot = f.Perch :: PerchSpot
		local cp = math.cos(pc.TakeoffPitch)
		wx, wy, wz =
			math.cos(spot.FaceYaw) * cp, math.sin(pc.TakeoffPitch), math.sin(spot.FaceYaw) * cp
		goal = b.SMin
		if f.ModeTime >= pc.TakeoffSeconds then
			f.Mode, f.ModeTime = "fly", 0
			f.Perch = nil
			f.PerchCooldown = rangeOf(f.Rng, pc.CooldownMin, pc.CooldownMax)
			FlightCore.pickWaypoint(f, env, nil)
		end
		FlightCore.advance(f, dt, wx, wy, wz, goal)
		return
	end

	if mode == "approach" or mode == "land" then
		local spot = f.Perch :: PerchSpot
		local tx, ty, tz = f.AX, f.AY, f.AZ
		if mode == "land" then
			tx, ty, tz = spot.X, spot.Y, spot.Z
		end
		local d = distTo(f, tx, ty, tz)
		if d < f.BestDist - 1 then
			f.BestDist, f.StuckFor = d, 0
		else
			f.StuckFor += dt
		end
		if f.StuckFor > pc.AbortSeconds then
			endPerchAttempt(f, env)
			return
		end
		if mode == "approach" then
			goal = b.SMin * pc.ApproachSpeedScale
			if d < math.max(pc.ArriveRadius, f.TurnRadius * pc.ArriveTurnScale) then
				-- lined up with the perch? if not, think again rather than snap round
				local lx, lz = spot.X - f.X, spot.Z - f.Z
				local off = math.abs(wrap(math.atan2(lz, lx) - f.Yaw))
				if off > pc.AlignMax then
					endPerchAttempt(f, env)
					return
				end
				f.Mode, f.ModeTime, f.BestDist, f.StuckFor = "land", 0, math.huge, 0
			end
		else
			goal = clamp(d * pc.LandSpeedGain, pc.LandSpeedMin, b.SMin * pc.ApproachSpeedScale)
			if d < pc.SnapDistance then
				f.X, f.Y, f.Z = spot.X, spot.Y, spot.Z
				f.Speed = 0
				f.Mode, f.ModeTime = "perch", 0
				f.HoldFor = rangeOf(f.Rng, pc.HoldMin, pc.HoldMax)
				return
			end
		end
		wx, wy, wz = tx - f.X, ty - f.Y, tz - f.Z
		local len = math.sqrt(wx * wx + wy * wy + wz * wz)
		if len > EPS then
			wx, wy, wz = wx / len + sepX, wy / len + sepY, wz / len + sepZ
		end
		FlightCore.advance(f, dt, wx, wy, wz, goal)
		return
	end

	-- FLY: speed drifts toward a goal that itself changes now and then
	f.NextSpeedChange -= dt
	if f.NextSpeedChange <= 0 then
		f.SpeedGoal = rangeOf(f.Rng, b.SMin, b.SMax)
		f.NextSpeedChange = rangeOf(f.Rng, fl.SpeedChangeMin, fl.SpeedChangeMax)
	end
	f.PerchCooldown -= dt
	local tx, ty, tz = f.TX - f.X, f.TY - f.Y, f.TZ - f.Z
	local to = math.sqrt(tx * tx + ty * ty + tz * tz)
	if to < f.BestDist - 1 then
		f.BestDist, f.StuckFor = to, 0
	else
		f.StuckFor += dt
	end
	-- a big turner counts as arrived from further out: it cannot tighten its
	-- circle onto a point
	if
		to < math.max(prof.ArriveMin, f.TurnRadius * fl.ArriveTurnScale)
		or f.StuckFor > fl.StuckSeconds
	then
		local perched = false
		if
			f.CanLand
			and f.PerchCooldown <= 0
			and env.FindPerch
			and f.Rng:NextNumber() < prof.PerchChance
		then
			local spot = env.FindPerch(f)
			if spot then
				perched = FlightCore.beginPerch(f, spot)
			end
			if not perched then
				f.PerchCooldown = rangeOf(f.Rng, pc.RetryDelayMin, pc.RetryDelayMax)
			end
		end
		if perched then
			return
		end
		FlightCore.pickWaypoint(f, env, if f.StuckFor > fl.StuckSeconds then math.pi * 0.5 else 0)
		tx, ty, tz = f.TX - f.X, f.TY - f.Y, f.TZ - f.Z
		to = math.sqrt(tx * tx + ty * ty + tz * tz)
	end
	if to > 0.01 then
		wx, wy, wz = tx / to, ty / to, tz / to
	else
		wx, wy, wz = FlightCore.heading(f)
	end

	local kx, ky, kz, threatened = FlightCore.keepOutSteer(f, b.Cx, b.Cy, b.Cz)
	wx += (env.AvoidX or 0) + sepX + kx
	wy += (env.AvoidY or 0) + sepY + ky
	wz += (env.AvoidZ or 0) + sepZ + kz

	-- ease off before a tight turn: the heading error sets the speed goal
	local flat = math.sqrt(wx * wx + wz * wz)
	local err = 0.0
	if flat > EPS then
		err = math.abs(wrap(math.atan2(wz, wx) - f.Yaw))
	end
	local slow = clamp(err / fl.SlowAngle, 0, 1)
	if threatened then
		slow = 1
	end
	goal = math.max(goal * (1 - slow * (1 - prof.MinSpeedScale)), b.SMin * prof.MinSpeedScale)
	FlightCore.advance(f, dt, wx, wy, wz, goal)
end

-- ---------------------------------------------------------------- throttling

--- Seconds between simulation updates for a creature `distance` studs from the
--- camera: every frame (0) while inside its class's ActivationRadius, a slow
--- fixed rate beyond it.
function FlightCore.updateInterval(prof: Cfg, distance: number): number
	if distance <= prof.ActivationRadius then
		return 0
	end
	return 1 / prof.UpdateHz
end

-- ---------------------------------------------------------------- gait

--- Advance the animation state. Outputs on the flier: GaitClock (a time that
--- runs faster with speed and climb), FlapAmp (1 beating .. floor when gliding),
--- Idle (1 while perched), BankNorm (-1..1, already maintained by advance).
function FlightCore.gait(f: Flier, dt: number)
	local g = f.Cfg.Gait
	local prof = f.Prof
	local perched = f.Mode == "perch"
	local cruise = math.max(f.Band.SMax, EPS)
	local climb = math.max(0, math.sin(f.Pitch))
	local warp = prof.BeatScale * (1 + g.SpeedGain * (f.Speed / cruise - 1) + g.ClimbGain * climb)
	f.Warp = clamp(warp, g.BeatMin * prof.BeatScale, g.BeatMax * prof.BeatScale)
	f.GaitClock += dt * f.Warp

	-- glide schedule: flap a while, maybe coast a while
	f.GaitLeft -= dt
	if f.GaitLeft <= 0 then
		if f.Gliding then
			f.Gliding = false
			f.GaitLeft = rangeOf(f.Rng, prof.FlapMin, prof.FlapMax)
		elseif f.Rng:NextNumber() < prof.GlideChance then
			f.Gliding = true
			f.GaitLeft = rangeOf(f.Rng, prof.GlideMin, prof.GlideMax)
		else
			f.GaitLeft = rangeOf(f.Rng, prof.FlapMin, prof.FlapMax)
		end
	end
	local busy = f.Mode == "approach" or f.Mode == "land" or f.Mode == "takeoff"
	local ampGoal = 1.0
	if perched then
		ampGoal = 0
	elseif f.Gliding and not busy then
		ampGoal = g.GlideAmpFloor
	end
	f.FlapAmp += (ampGoal - f.FlapAmp) * math.min(1, dt * g.AmpSmoothing)
	local idleGoal = if perched then 1 else 0
	f.Idle += (idleGoal - f.Idle) * math.min(1, dt * g.IdleSmoothing)
end

return FlightCore
