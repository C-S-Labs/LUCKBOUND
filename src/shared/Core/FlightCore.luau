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
--   * (Round 2) EVERY class plans round the world's obstacles (backdrop islands,
--     the far range): vertical cylinders inflated by the creature's own size.
--     Waypoints and the legs between them avoid them, a look-ahead steers off
--     them, and a colossal may fly OVER the hub at an altitude that clears the
--     deck by its own extent (an overpass route: climb, cross level, descend).
--   * Colossals: a shared presence floor/ceiling (presenceStep), never none.
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

-- A world obstacle: a vertical cylinder (horizontal radius R, half height H);
-- a sphere is R == H. Positions are absolute.
export type Obstacle = { X: number, Y: number, Z: number, R: number, H: number }
export type RoutePoint = { X: number, Y: number, Z: number, Over: boolean, Under: boolean? }

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
	LocalCentre: { number }, -- assembly centre from the body origin, in the mesh frame (nose -X, left +Z, up +Y)
	Inflate: number, -- clearance kept from every obstacle: class-scaled body radius + margin
	Obstacles: { Obstacle }, -- shared list the driver fills (islands, far range)
	AvoidV: { number }, -- smoothed obstacle steer
	Neighbours: { any }?, -- every other flier (env.Others), for the hard stop
	Route: { RoutePoint }, -- waypoints queued after the current target (overpass legs)
	OverLeg: boolean, -- the current target is part of a hub overpass
	UnderLeg: boolean, -- ... or of a hub underpass (below the hub)
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
	RescueT: number, -- seconds since the progress check began
	RescueDist: number, -- distance flown since the progress check began
	CircleT: number, -- circling check window: seconds, turn flown, start point, strikes in a row
	CircleTurn: number,
	CircleX: number,
	CircleZ: number,
	CircleStrikes: number,
	Dbg: { [string]: number }, -- last step's steering inputs (read by the driver's debug switch)
	Rescues: number, -- times it was moved out of a dead end
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
	GlideBlend: number, -- 0 beating .. 1 coasting (smoothed)
	AccelN: number, -- forward acceleration / class Accel, -1..1 (smoothed)
	Flare: number, -- 0..1, high while landing or taking off
	PrevSpeed: number,
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

local function distTo(f: Flier, x: number, y: number, z: number): number
	local dx, dy, dz = x - f.X, y - f.Y, z - f.Z
	return math.sqrt(dx * dx + dy * dy + dz * dz)
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
	speedGoal: number,
	guard: boolean?
)
	local fl = f.Cfg.Flight
	local prof = f.Prof
	local rate = FlightCore.turnRate(f)
	local maxYaw = rate * dt
	local flat = math.sqrt(wx * wx + wz * wz)
	local yawBefore = f.Yaw
	local pitchBefore = f.Pitch
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
	if guard and f.Speed > 0 and f.Neighbours then
		-- never step INTO another creature either (their bodies' spheres)
		local nx, ny, nz = f.X + hx * f.Speed * dt, f.Y + hy * f.Speed * dt, f.Z + hz * f.Speed * dt
		for _, o in f.Neighbours do
			if o ~= f and o.Present then
				local need = f.Radius + o.Radius + fl.GuardMargin
				local d0 = distTo(o, f.X, f.Y, f.Z)
				local d1 = distTo(o, nx, ny, nz)
				if d1 < need and d1 < d0 then
					f.Speed = 0
					break
				end
			end
		end
	end
	if guard and f.Speed > 0 and #f.Obstacles > 0 then
		-- the last line of defence: never step INTO an obstacle (the body's own sphere
		-- against it). The creature hovers and turns away instead of clipping.
		local raw = -(f.Inflate - f.Radius)
		-- turning swings an off-centre body round its origin: no turn into an obstacle either
		local cx = f.LocalCentre
		if
			(cx[1] ~= 0 or cx[2] ~= 0 or cx[3] ~= 0)
			and FlightCore.blockedAt(f, f.X, f.Y, f.Z, raw)
		then
			local yawNew, pitchNew = f.Yaw, f.Pitch
			f.Yaw, f.Pitch = yawBefore, pitchBefore
			if not FlightCore.blockedAt(f, f.X, f.Y, f.Z, raw) then
				f.Yaw, f.Pitch = yawBefore, pitchBefore
			else
				f.Yaw, f.Pitch = yawNew, pitchNew
			end
			hx, hy, hz = FlightCore.heading(f)
		end
		local nx, ny, nz = f.X + hx * f.Speed * dt, f.Y + hy * f.Speed * dt, f.Z + hz * f.Speed * dt
		if
			FlightCore.blockedAt(f, nx, ny, nz, raw + fl.GuardMargin)
			and not FlightCore.blockedAt(f, f.X, f.Y, f.Z, raw)
		then
			f.Speed = 0
		end
	end
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

--- The lowest height (relative to the deck) the keep-out volume reaches: the
--- class's UnderDepth below the deck (the hub's underside plus the creature's own
--- extent), or unbounded when the class has none (it may not pass beneath).
local function floorOf(prof: Cfg): number
	local u = prof.UnderDepth
	if u == nil then
		return -math.huge
	end
	return -u
end

--- Is the point inside the keep-out volume of this class? The volume is the
--- cylinder of radius HubClearance about the hub axis, from UnderDepth below the
--- deck (or far below) up to OverheadMinY above it. `padH` fattens it sideways
--- and `padV` up and down.
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
	local rel = y - cy
	return rel < prof.OverheadMinY + padV and rel > floorOf(prof) - padV
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
	local floor = cy + floorOf(prof) - pad
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
	-- the stretch of the leg inside the cylinder is a hit wherever it is below the roof and above the floor
	local t0, t1 = math.max(s0, 0), math.min(s1, 1)
	local y0 = ay + (by - ay) * t0
	local y1 = ay + (by - ay) * t1
	return math.min(y0, y1) < roof and math.max(y0, y1) > floor
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
	-- OVER THE ROOF: a creature that may cross the hub and is already above its roof only
	-- needs to stay up. An edge tangent here is ill-conditioned (it swings with every stud
	-- of travel near the axis and the creature spins chasing it), so the push is vertical only.
	if f.Roofed and d < c and f.Y >= cy + prof.OverheadMinY + vpad then
		return 0, fl.KeepOutClimb * fl.KeepOutWeight * fl.KeepOutFloor, 0, true
	end
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
	-- the creature's own comfort zone is scaled; the other body counts at its true size (scaling a
	-- big prop's radius too made every small creature flee isles and clouds across hundreds of studs)
	local need = f.Radius * f.Prof.SeparationScale + otherRadius
	local zone = need * fl.SeparationFalloff
	if d >= need + zone then
		return 0, 0, 0
	end
	local k = fl.SeparationStrength * (1 - clamp((d - need) / math.max(zone, EPS), 0, 1)) / d
	return dx * k, dy * k, dz * k
end

-- ---------------------------------------------------------------- obstacles

--- Is the point inside the obstacle fattened by `pad` (all round)?
function FlightCore.obstacleHitsPoint(
	o: Obstacle,
	x: number,
	y: number,
	z: number,
	pad: number
): boolean
	local dx, dz = x - o.X, z - o.Z
	local r = o.R + pad
	if dx * dx + dz * dz >= r * r then
		return false
	end
	return math.abs(y - o.Y) < o.H + pad
end

--- Does the straight segment a->b pass through the obstacle fattened by `pad`?
function FlightCore.obstacleHitsSegment(
	o: Obstacle,
	ax: number,
	ay: number,
	az: number,
	bx: number,
	by: number,
	bz: number,
	pad: number
): boolean
	local dx, dz = bx - ax, bz - az
	local ox, oz = ax - o.X, az - o.Z
	local r = o.R + pad
	local qa = dx * dx + dz * dz
	local t0, t1
	if qa < EPS then
		if ox * ox + oz * oz >= r * r then
			return false
		end
		t0, t1 = 0, 1
	else
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
		t0, t1 = math.max(s0, 0), math.min(s1, 1)
	end
	local y0 = ay + (by - ay) * t0
	local y1 = ay + (by - ay) * t1
	local h = o.H + pad
	return math.max(y0, y1) > o.Y - h and math.min(y0, y1) < o.Y + h
end

--- Where the creature's bounding sphere is centred, relative to its body origin
--- (a long creature whose body root is its head is centred well behind it).
local function centreOffset(f: Flier): (number, number, number)
	local c = f.LocalCentre
	if c[1] == 0 and c[2] == 0 and c[3] == 0 then
		return 0, 0, 0
	end
	local hx, hy, hz = FlightCore.heading(f)
	local flat = math.max(math.sqrt(hx * hx + hz * hz), EPS)
	local lx, lz = -hz / flat, hx / flat
	-- mesh -X is forward, +Z is left, +Y is up
	return -c[1] * hx + c[3] * lx, -c[1] * hy + c[2], -c[1] * hz + c[3] * lz
end

--- Is this point inside any obstacle, fattened by this creature's Inflate plus `extra`?
function FlightCore.blockedAt(f: Flier, x: number, y: number, z: number, extra: number): boolean
	local pad = f.Inflate + extra
	local ox, oy, oz = centreOffset(f)
	x, y, z = x + ox, y + oy, z + oz
	for _, o in f.Obstacles do
		if FlightCore.obstacleHitsPoint(o, x, y, z, pad) then
			return true
		end
	end
	return false
end

--- Does the straight leg a->b pass through any obstacle (fattened as above)?
function FlightCore.legBlocked(
	f: Flier,
	ax: number,
	ay: number,
	az: number,
	bx: number,
	by: number,
	bz: number,
	extra: number
): boolean
	local pad = f.Inflate + extra
	local ox, oy, oz = centreOffset(f)
	ax, ay, az, bx, by, bz = ax + ox, ay + oy, az + oz, bx + ox, by + oy, bz + oz
	for _, o in f.Obstacles do
		if FlightCore.obstacleHitsSegment(o, ax, ay, az, bx, by, bz, pad) then
			return true
		end
	end
	return false
end

--- Steering away from obstacles ahead: a vector (zero when the way is clear)
--- and whether anything threatens. The look-ahead covers this creature's
--- turning arc plus a share of the obstacle's own size; the way out is
--- sideways or over/under, whichever is shorter.
function FlightCore.obstacleSteer(f: Flier): (number, number, number, boolean)
	local av = f.Cfg.Avoid
	local pad = f.Inflate
	local hx, hy, hz = FlightCore.heading(f)
	local base = f.TurnRadius * av.TurnScale + math.max(f.Speed, f.Band.SMax * 0.5) * av.Lead
	local sx, sy, sz = 0.0, 0.0, 0.0
	local threat = false
	local sumW = 0.0
	local cox, coy, coz = centreOffset(f)
	local fX, fY, fZ = f.X + cox, f.Y + coy, f.Z + coz
	for _, o in f.Obstacles do
		local dx, dz = o.X - fX, o.Z - fZ
		local dh = math.sqrt(dx * dx + dz * dz)
		local reach = base + av.SizeScale * o.R
		if dh - (o.R + pad) > reach or math.abs(o.Y - fY) - (o.H + pad) > reach then
			continue
		end
		local hitS: number? = nil
		for k = 0, av.Samples do
			local s = reach * k / av.Samples
			if FlightCore.obstacleHitsPoint(o, fX + hx * s, fY + hy * s, fZ + hz * s, pad) then
				hitS = s
				break
			end
		end
		if hitS == nil then
			continue
		end
		threat = true
		local urgency = 1 - hitS / reach
		local qx, qy, qz = fX + hx * hitS, fY + hy * hitS, fZ + hz * hitS
		local qdx, qdz = qx - o.X, qz - o.Z
		local qd = math.sqrt(qdx * qdx + qdz * qdz)
		local escapeH = (o.R + pad) - qd
		local escapeV = (o.H + pad) - math.abs(qy - o.Y)
		local weight = av.Weight * (av.Floor + (1 - av.Floor) * urgency)
		sumW += weight
		if escapeV < escapeH * av.VerticalBias then
			local up = if qy >= o.Y then 1 else -1
			sy += up * weight
		else
			-- sideways: turn away from the side the obstacle's axis lies on
			local flat = math.max(math.sqrt(hx * hx + hz * hz), EPS)
			local lx, lz = -hz / flat, hx / flat -- left of the heading
			local side = dx * lx + dz * lz -- > 0: obstacle on the left
			local sgn
			if math.abs(side) < 1e-3 then
				sgn = f.Circ
			else
				sgn = if side > 0 then -1 else 1
			end
			sx += lx * sgn * weight
			sz += lz * sgn * weight
		end
		if dh < o.R + pad then
			-- already inside the fattened volume: push straight out
			local ux, uz = -dx / math.max(dh, EPS), -dz / math.max(dh, EPS)
			sx += ux * av.Weight
			sz += uz * av.Weight
		end
	end
	-- sandwiched (pushed both ways at once, so the sides cancel): turn back
	if threat and (sx * sx + sz * sz) < (sumW * av.PocketRatio) ^ 2 and sumW > 0 then
		sx -= hx * sumW
		sz -= hz * sumW
	end
	return sx, sy, sz, threat
end

-- ---------------------------------------------------------------- waypoints

local function angleOf(f: Flier): number
	return math.atan2(f.Z - f.Band.Cz, f.X - f.Band.Cx)
end

--- The overpass the creature may take across the hub: climb to a level above the
--- roof BEFORE the keep-out edge, cross it level, leave on the far side. With
--- `under` the mirror image: sink below the hub's underside (UnderDepth, which
--- includes the creature's own extent) and cross beneath it. Returns the route
--- (entry, exit, then the target beyond) or nil when it is not possible from
--- here (not enough room to be there in time, or a leg blocked).
local function planPass(f: Flier, under: boolean): { RoutePoint }?
	local b, prof, fl, rng = f.Band, f.Prof, f.Cfg.Flight, f.Rng
	local chance = if under then (prof.UnderpassChance or 0) else (prof.OverpassChance or 0)
	if chance <= 0 then
		return nil
	end
	local pad = fl.WaypointPad
	local level
	if under then
		if prof.UnderDepth == nil then
			return nil
		end
		level = b.Cy - prof.UnderDepth - pad - fl.KeepOutRoofMargin * 2
		if level < b.YMin then
			return nil
		end
	else
		if not f.Roofed then
			return nil
		end
		level = b.Cy + prof.OverheadMinY + pad + fl.KeepOutRoofMargin * 2
		if level > b.YMax then
			return nil
		end
	end
	local edge = prof.HubClearance + pad + fl.KeepOutMargin
	local dx, dz = f.X - b.Cx, f.Z - b.Cz
	local d = math.sqrt(dx * dx + dz * dz)
	if d < EPS then
		return nil
	end
	-- the entry sits outside the edge by the creature's own turning room
	local entryR = edge + f.TurnRadius * fl.OverpassLead
	local slope = math.tan(f.Prof.MaxPitch * fl.OverpassPitchUse)
	-- the first try enters from where the creature is; later ones from other bearings, so a
	-- crowded sky (islands in the way at this level) still leaves a lane
	for try = 1, fl.PassTries do
		local a0 = if try == 1 then math.atan2(dz, dx) else rng:NextNumber(0, TWO_PI)
		local ux, uz = math.cos(a0), math.sin(a0)
		local ex, ez = b.Cx + ux * entryR, b.Cz + uz * entryR
		local run = math.sqrt((ex - f.X) ^ 2 + (ez - f.Z) ^ 2)
		local climb
		if under then
			climb = math.max(0, f.Y - level)
		else
			climb = math.max(0, level - f.Y)
		end
		if (try == 1 and d < entryR) or climb > run * slope * fl.PassSlack then
			continue
		end
		-- the far side: exit at the same level, then a band point beyond it
		local a = math.atan2(-uz, -ux) + rng:NextNumber(-fl.PassSpread, fl.PassSpread)
		local fx, fz = b.Cx + math.cos(a) * entryR, b.Cz + math.sin(a) * entryR
		local r = rangeOf(rng, b.RMin, b.RMax)
		local tx, tz = b.Cx + math.cos(a) * r, b.Cz + math.sin(a) * r
		local ty = rangeOf(rng, b.YMin, b.YMax)
		local descent = math.sqrt((tx - fx) ^ 2 + (tz - fz) ^ 2)
		if math.abs(level - ty) > descent * slope then
			ty = level + clamp(ty - level, -descent, descent) * 0.2
		end
		ty = clamp(ty, b.YMin, b.YMax)
		local y = if under then math.min(level, f.Y) else math.max(level, f.Y)
		if
			not (
				FlightCore.blockedAt(f, tx, ty, tz, fl.WaypointPad)
				or FlightCore.segmentHitsKeepOut(
					prof,
					b.Cx,
					b.Cy,
					b.Cz,
					f.X,
					f.Y,
					f.Z,
					ex,
					y,
					ez,
					pad
				)
				or FlightCore.legBlocked(f, f.X, f.Y, f.Z, ex, y, ez, fl.LegPad)
				or FlightCore.legBlocked(f, fx, y, fz, tx, ty, tz, fl.LegPad)
				or FlightCore.legBlocked(f, ex, y, ez, fx, y, fz, fl.LegPad)
			)
		then
			return {
				{ X = ex, Y = y, Z = ez, Over = true, Under = under },
				{ X = fx, Y = y, Z = fz, Over = true, Under = under },
				{ X = tx, Y = ty, Z = tz, Over = false },
			}
		end
	end
	return nil
end

--- Make the next route point (if any) the current target. True if one was used.
local function takeRoutePoint(f: Flier): boolean
	local nxt = table.remove(f.Route, 1)
	if nxt then
		f.TX, f.TY, f.TZ = nxt.X, nxt.Y, nxt.Z
		f.OverLeg = nxt.Over and not nxt.Under
		f.UnderLeg = nxt.Under == true
		f.BestDist, f.StuckFor = math.huge, 0
		return true
	end
	f.OverLeg = false
	f.UnderLeg = false
	return false
end

--- Choose the next waypoint inside the class band. Never a point inside the
--- keep-out, never a leg that cuts through it or through an obstacle (islands,
--- far range), inflated by the creature's own size. `env.Blocked(x, y, z, r)`
--- (the driver's real-geometry test) and `env.PlayerX/Y/Z` (for a close
--- approach) are optional. A colossal may instead plan an overpass of the hub.
function FlightCore.pickWaypoint(f: Flier, env: any?, extraAngle: number?)
	local b = f.Band
	local prof = f.Prof
	local fl = f.Cfg.Flight
	local rng = f.Rng
	local pad = fl.WaypointPad
	local blocked = if env then env.Blocked else nil
	f.Route = {}
	f.OverLeg = false
	f.UnderLeg = false
	local function pointOk(x: number, y: number, z: number): boolean
		if FlightCore.inKeepOut(prof, b.Cx, b.Cy, b.Cz, x, y, z, pad, pad) then
			return false
		end
		if FlightCore.blockedAt(f, x, y, z, pad) then
			return false
		end
		if blocked and blocked(x, y, z, f.Radius + fl.WaypointPad) then
			return false
		end
		return true
	end
	local function ok(x: number, y: number, z: number): boolean
		if not pointOk(x, y, z) then
			return false
		end
		if FlightCore.segmentHitsKeepOut(prof, b.Cx, b.Cy, b.Cz, f.X, f.Y, f.Z, x, y, z, pad) then
			return false
		end
		if FlightCore.legBlocked(f, f.X, f.Y, f.Z, x, y, z, fl.LegPad) then
			return false
		end
		return true
	end
	f.BestDist, f.StuckFor = math.huge, 0

	-- over the hub, for a creature big enough to need the altitude and high enough to manage it
	if rng:NextNumber() < (prof.OverpassChance or 0) then
		local route = planPass(f, false)
		if route then
			f.Route = route
			takeRoutePoint(f)
			return
		end
	end
	-- ... or beneath it, for a creature whose band reaches below the hub's underside
	if rng:NextNumber() < (prof.UnderpassChance or 0) then
		local route = planPass(f, true)
		if route then
			f.Route = route
			takeRoutePoint(f)
			return
		end
	end

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
	-- no clear leg: a clear point (the look-ahead steers the way there)
	for _ = 1, fl.WaypointTries do
		local r = rangeOf(rng, b.RMin, b.RMax)
		local aa = rng:NextNumber(0, TWO_PI)
		px = b.Cx + math.cos(aa) * r
		py = rangeOf(rng, b.YMin, b.YMax)
		pz = b.Cz + math.sin(aa) * r
		if pointOk(px, py, pz) then
			f.TX, f.TY, f.TZ = px, py, pz
			return
		end
	end
	-- nothing clear: straight on, as far as is clear, climbing a little
	local hx, _, hz = FlightCore.heading(f)
	local reach = f.TurnRadius * fl.FallbackReach
	for _, k in { 1, 0.6, 0.3, 0.1 } do
		local x, z = f.X + hx * reach * k, f.Z + hz * reach * k
		local y = clamp(f.Y + reach * k * fl.FallbackClimb, b.YMin, b.YMax)
		if pointOk(x, y, z) then
			f.TX, f.TY, f.TZ = x, y, z
			return
		end
	end
	f.TX, f.TY, f.TZ = f.X, f.Y, f.Z
end

--- Move a creature that starts inside an obstacle (or the keep-out) to a
--- clear place in its band, so it never begins inside an island.
function FlightCore.relocate(f: Flier)
	local b = f.Band
	local prof = f.Prof
	local fl = f.Cfg.Flight
	local function clear(x: number, y: number, z: number): boolean
		for _, o in f.Neighbours or {} do
			if
				o ~= f
				and o.Present
				and distTo(o, x, y, z) < f.Radius + o.Radius + fl.WaypointPad
			then
				return false
			end
		end
		return not FlightCore.blockedAt(f, x, y, z, fl.WaypointPad)
			and not FlightCore.inKeepOut(
				prof,
				b.Cx,
				b.Cy,
				b.Cz,
				x,
				y,
				z,
				fl.WaypointPad,
				fl.WaypointPad
			)
	end
	if clear(f.X, f.Y, f.Z) then
		return
	end
	for _ = 1, fl.RelocateTries do
		local a = f.Rng:NextNumber(0, TWO_PI)
		local r = rangeOf(f.Rng, b.RMin, b.RMax)
		local x, y, z =
			b.Cx + math.cos(a) * r, rangeOf(f.Rng, b.YMin, b.YMax), b.Cz + math.sin(a) * r
		if clear(x, y, z) then
			f.X, f.Y, f.Z = x, y, z
			return
		end
	end
	-- last resort: straight up to the top of the band
	f.Y = b.YMax
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
	canLand: boolean?,
	centre: { number }?
): Flier
	local base = cfg.Classes[class]
	-- the keep-out and the overpass roof grow with the creature's own extent
	local prof = base
	if
		(base.HubClearanceExtentScale or 0) > 0
		or (base.OverheadExtentScale or 0) > 0
		or (base.UnderExtentScale or 0) > 0
	then
		prof = setmetatable({
			HubClearance = base.HubClearance + radius * (base.HubClearanceExtentScale or 0),
			OverheadMinY = base.OverheadMinY + radius * (base.OverheadExtentScale or 0),
			UnderDepth = if base.UnderDepth ~= nil
				then base.UnderDepth + radius * (base.UnderExtentScale or 0)
				else nil,
		}, { __index = base })
	end
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
		LocalCentre = centre or { 0, 0, 0 },
		Inflate = radius * (base.AvoidRadiusScale or 1) + (base.AvoidMargin or 0),
		Obstacles = {},
		Route = {},
		AvoidV = { 0, 0, 0 },
		OverLeg = false,
		UnderLeg = false,
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
		RescueT = 0,
		RescueDist = 0,
		CircleT = 0,
		CircleTurn = 0,
		CircleX = x,
		CircleZ = z,
		CircleStrikes = 0,
		Dbg = {},
		Rescues = 0,
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
		GlideBlend = 0,
		AccelN = 0,
		Flare = 0,
		PrevSpeed = 0,
	}
	f.PrevSpeed = f.Speed
	local pr = prof.Presence
	if pr then
		-- a creature that comes and goes (see presenceStep): present to begin with
		f.PresenceLeft = rangeOf(rng, pr.PresentMin, pr.PresentMax)
	end
	-- never start already heading into the keep-out: if the start is near it,
	-- begin along its edge, in the creature's own circulation
	local _, _, _, near = FlightCore.keepOutSteer(f, band.Cx, band.Cy, band.Cz)
	if near then
		f.Yaw = wrap(math.atan2(z - band.Cz, x - band.Cx) + (math.pi / 2) * f.Circ)
	end
	return f
end

--- Put an arriving creature in the OUTER part of its band (SpawnOuter..1 of the
--- way out) at a random bearing, flying along the edge (never inside the keep-out or an obstacle).
function FlightCore.enter(f: Flier)
	local b = f.Band
	local fl = f.Cfg.Flight
	local a, x, z, y, r = 0.0, 0.0, 0.0, 0.0, 0.0
	for _ = 1, fl.RelocateTries do
		a = f.Rng:NextNumber(0, TWO_PI)
		r = rangeOf(f.Rng, b.RMin + (b.RMax - b.RMin) * (f.Prof.SpawnOuter or 1), b.RMax)
		x = b.Cx + math.cos(a) * r
		z = b.Cz + math.sin(a) * r
		y = rangeOf(f.Rng, b.YMin, b.YMax)
		if not FlightCore.blockedAt(f, x, y, z, fl.WaypointPad) then
			break
		end
	end
	f.X, f.Y, f.Z = x, y, z
	-- tangent to the circle: along the edge, in its circulation
	f.Yaw = wrap(a + (math.pi / 2) * f.Circ)
	f.Pitch = 0
	f.Speed = rangeOf(f.Rng, b.SMin, b.SMax)
	f.PrevSpeed = f.Speed
	f.Mode = "fly"
	f.Perch = nil
	f.BankNorm, f.Bank, f.YawRate = 0, 0, 0
	FlightCore.relocate(f)
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

--- Presence: colossals come and go, but as a GROUP: at least `Floor` are always
--- present and never more than `Ceiling` (the profile's Presence). With Floor ==
--- Ceiling == 1 there is exactly one at all times: when it has been here long
--- enough it is REPLACED (it leaves as another arrives, never zero, never two).
--- The driver calls this once per step with every creature of the class. Extra
--- ones present at the start (a server spawns more than it shows) are sent away
--- at once. Returns the number present afterwards.
function FlightCore.presenceStep(group: { Flier }, dt: number): number
	local present = 0
	local pr: any = nil
	for _, f in group do
		if f.Present then
			present += 1
		end
		if not pr then
			pr = f.Prof.Presence
		end
	end
	if not pr then
		return present
	end
	local function absentOnes(): { Flier }
		local list = {}
		for _, f in group do
			if not f.Present then
				table.insert(list, f)
			end
		end
		return list
	end
	local function leave(f: Flier)
		f.Present = false
		f.PresenceLeft = rangeOf(f.Rng, pr.AbsentMin, pr.AbsentMax)
		present -= 1
	end
	local function arrive(f: Flier)
		f.Present = true
		f.PresenceLeft = rangeOf(f.Rng, pr.PresentMin, pr.PresentMax)
		FlightCore.enter(f)
		present += 1
	end
	-- never more than the ceiling, even at the start
	while present > pr.Ceiling do
		local here = {}
		for _, f in group do
			if f.Present then
				table.insert(here, f)
			end
		end
		-- a random one goes
		leave(here[math.floor(here[1].Rng:NextNumber(0, #here)) + 1] or here[1])
	end
	for _, f in group do
		f.PresenceLeft -= dt
		if f.PresenceLeft > 0 then
			continue
		end
		if f.Present then
			local others = absentOnes()
			if #others > 0 then
				-- swap: this one leaves as another arrives, the count never changes
				leave(f)
				arrive(others[math.floor(f.Rng:NextNumber(0, #others)) + 1] or others[1])
			elseif present > pr.Floor then
				leave(f)
			else
				f.PresenceLeft = rangeOf(f.Rng, pr.PresentMin, pr.PresentMax)
			end
		elseif present < pr.Ceiling then
			arrive(f)
		else
			f.PresenceLeft = rangeOf(f.Rng, pr.AbsentMin, pr.AbsentMax) * 0.1
		end
	end
	-- the floor is never broken: bring one back at once if need be
	if present < pr.Floor then
		for _, f in group do
			if not f.Present and present < pr.Floor then
				arrive(f)
			end
		end
	end
	return present
end

--- How long a creature may make no progress toward its waypoint before it is called stuck:
--- StuckSeconds plus StuckTurnScale x the time one turn radius takes at its speed (a colossal
--- needs minutes to come round, and must not give up on a leg while it is turning).
local function stuckLimit(f: Flier): number
	local fl = f.Cfg.Flight
	return fl.StuckSeconds + fl.StuckTurnScale * f.TurnRadius / math.max(f.Speed, f.Band.SMin, 1)
end

--- One simulation step.
--- env (all optional): AvoidX/Y/Z (the driver's look-ahead steer), SepX/Y/Z
--- (summed FlightCore.separation), Blocked, PlayerX/Y/Z, FindPerch(f).
function FlightCore.tick(f: Flier, dt: number, env: any)
	if not f.Present then
		return
	end
	local fl = f.Cfg.Flight
	local pc = f.Cfg.Perch
	local prof = f.Prof
	local b = f.Band
	f.Neighbours = env.Others
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
	-- DEAD-END RESCUE: a flier that has made almost no headway for a long window (wedged
	-- between obstacles, or crawling in a pocket) re-enters at the edge of its band
	f.RescueT += dt
	f.RescueDist += f.Speed * dt
	if f.RescueT >= fl.RescueSeconds then
		local flown = f.RescueDist
		f.RescueT, f.RescueDist = 0, 0
		if flown < b.SMin * fl.RescueSeconds * fl.RescueSpeedFrac then
			FlightCore.enter(f)
			f.Rescues += 1
			return
		end
	end
	-- NO ENDLESS CIRCLES: several turns while getting nowhere means the creature is orbiting
	-- something it cannot reach (a waypoint inside its turning circle, a steer it cannot
	-- satisfy). Choose again; if that fails twice running, re-enter at the band's edge.
	f.CircleT += dt
	f.CircleTurn += math.abs(f.YawRate) * dt
	if f.CircleT >= fl.CircleSeconds then
		local nx, nz = f.X - f.CircleX, f.Z - f.CircleZ
		local net = math.sqrt(nx * nx + nz * nz)
		local span = fl.CircleSpan * math.max(f.TurnRadius, fl.CircleSpanMin)
		local circling = f.CircleTurn > fl.CircleTurns * TWO_PI and net < span
		f.CircleT, f.CircleTurn, f.CircleX, f.CircleZ = 0, 0, f.X, f.Z
		if circling then
			f.CircleStrikes += 1
			if f.CircleStrikes >= 2 then
				f.CircleStrikes = 0
				FlightCore.enter(f)
				f.Rescues += 1
				return
			end
			FlightCore.pickWaypoint(f, env, math.pi * 0.5)
		else
			f.CircleStrikes = 0
		end
	end
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
		to
			< math.max(
				prof.ArriveMin,
				f.TurnRadius * fl.ArriveTurnScale,
				f.Speed / math.max(maxTurnRate(f), EPS) * fl.ArriveRadiusScale
			)
		or f.StuckFor > stuckLimit(f)
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
		if not takeRoutePoint(f) then
			FlightCore.pickWaypoint(f, env, if f.StuckFor > stuckLimit(f) then math.pi * 0.5 else 0)
		end
		tx, ty, tz = f.TX - f.X, f.TY - f.Y, f.TZ - f.Z
		to = math.sqrt(tx * tx + ty * ty + tz * tz)
	end
	if to > 0.01 then
		wx, wy, wz = tx / to, ty / to, tz / to
	else
		wx, wy, wz = FlightCore.heading(f)
	end

	local kx, ky, kz, threatened = FlightCore.keepOutSteer(f, b.Cx, b.Cy, b.Cz)
	if f.UnderLeg then
		-- crossing beneath the hub: no swerve while low enough
		local floor = b.Cy - (prof.UnderDepth or math.huge) - fl.KeepOutRoofMargin
		if f.Y <= floor then
			kx, ky, kz, threatened = 0, 0, 0, false
		elseif threatened then
			f.UnderLeg = false
			f.Route = {}
			FlightCore.pickWaypoint(f, env, 0)
		end
	end
	if f.OverLeg then
		-- crossing the hub overhead: no sideways swerve while high enough; if the
		-- climb fell short, give the overpass up and go round like everyone else
		local roof = b.Cy + prof.OverheadMinY + fl.KeepOutRoofMargin
		if f.Y >= roof then
			kx, ky, kz, threatened = 0, 0, 0, false
		elseif threatened then
			f.OverLeg = false
			f.Route = {}
			FlightCore.pickWaypoint(f, env, 0)
		end
	end
	-- the obstacle steer is smoothed in time: a creature turning away must not
	-- flicker between "ahead is blocked" and "ahead is clear" every step
	local rx, ry, rz, obstructed = FlightCore.obstacleSteer(f)
	local av = f.Cfg.Avoid
	local hold = math.max(f.TurnRadius / math.max(f.Speed, f.Band.SMin, 1), 0.5) * av.HoldScale
	local v = f.AvoidV
	if obstructed then
		local a = 1 - math.exp(-dt / (hold * av.RiseScale))
		v[1] += (rx - v[1]) * a
		v[2] += (ry - v[2]) * a
		v[3] += (rz - v[3]) * a
	else
		local k = math.exp(-dt / hold)
		v[1], v[2], v[3] = v[1] * k, v[2] * k, v[3] * k
	end
	local ox, oy, oz = v[1], v[2], v[3]
	if obstructed then
		-- the raw steer keeps flipping sides while the smoothed one stays small: it is
		-- wedged between two obstacles it cannot pass, so it turns back the way it came
		local rawMag = math.sqrt(rx * rx + rz * rz)
		local keptMag = math.sqrt(ox * ox + oz * oz)
		if rawMag > 0 and keptMag < rawMag * av.PocketRatio then
			local hx, _, hz = FlightCore.heading(f)
			ox -= hx * rawMag
			oz -= hz * rawMag
		end
	end
	if obstructed or ox * ox + oy * oy + oz * oz > av.ActiveSteer ^ 2 then
		threatened = true
	end
	-- BAND LEASH: past its band's outer edge a creature is drawn back in (avoiding things pushes
	-- it outward, and nothing else ever brings it home; far out it meets the far range)
	local lx, lz = f.X - b.Cx, f.Z - b.Cz
	local ld = math.sqrt(lx * lx + lz * lz)
	local lstart = b.RMax * (1 + fl.LeashStart)
	if ld > lstart then
		local pull = clamp((ld - lstart) / math.max(b.RMax * fl.LeashRange, EPS), 0, 1)
			* fl.LeashWeight
		wx -= lx / ld * pull
		wz -= lz / ld * pull
	end
	wx += (env.AvoidX or 0) + sepX + kx + ox
	wy += (env.AvoidY or 0) + sepY + ky + oy
	wz += (env.AvoidZ or 0) + sepZ + kz + oz

	-- ease off before a tight turn: the heading error sets the speed goal
	local flat = math.sqrt(wx * wx + wz * wz)
	local err = 0.0
	if flat > EPS then
		err = math.abs(wrap(math.atan2(wz, wx) - f.Yaw))
	end
	local dbg = f.Dbg
	dbg.Err = err
	dbg.Keep = math.sqrt(kx * kx + ky * ky + kz * kz)
	dbg.Sep = math.sqrt(sepX * sepX + sepY * sepY + sepZ * sepZ)
	dbg.Look = math.sqrt((env.AvoidX or 0) ^ 2 + (env.AvoidY or 0) ^ 2 + (env.AvoidZ or 0) ^ 2)
	dbg.Obs = math.sqrt(ox * ox + oy * oy + oz * oz)
	dbg.To = to
	dbg.Threat = if threatened then 1 else 0
	local slow = clamp(err / fl.SlowAngle, 0, 1)
	if threatened then
		slow = 1
	end
	goal = math.max(goal * (1 - slow * (1 - prof.MinSpeedScale)), b.SMin * prof.MinSpeedScale)
	FlightCore.advance(f, dt, wx, wy, wz, goal, true)
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
	local glideGoal = if f.Gliding and not busy and not perched then 1 else 0
	f.GlideBlend += (glideGoal - f.GlideBlend) * math.min(1, dt * g.AmpSmoothing)
	local idleGoal = if perched then 1 else 0
	f.Idle += (idleGoal - f.Idle) * math.min(1, dt * g.IdleSmoothing)
	-- acceleration (forward, signed) as a fraction of what the class can do
	local acc = (f.Speed - f.PrevSpeed) / math.max(dt, EPS)
	f.PrevSpeed = f.Speed
	local accN = clamp(acc / math.max(prof.Accel, EPS), -1, 1)
	f.AccelN += (accN - f.AccelN) * math.min(1, dt * g.AccelSmoothing)
	-- landing and takeoff flare
	local flareGoal = 0.0
	if f.Mode == "land" or f.Mode == "takeoff" then
		flareGoal = 1
	elseif f.Mode == "approach" then
		flareGoal = g.ApproachFlare
	end
	f.Flare += (flareGoal - f.Flare) * math.min(1, dt * g.FlareSmoothing)
end

return FlightCore
