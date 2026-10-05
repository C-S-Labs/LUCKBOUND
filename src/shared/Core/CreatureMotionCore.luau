--!strict
-- THE LAYERED MOTION OF THE SKY CREATURES: the pure animation maths behind
-- SkyTraffic. No Roblox types, so it runs headless (tests). Every number comes
-- from GameConfig.HubLayout.V2.SkyLife.Motion (per class); nothing is per species.
--
-- The layers (docs/design/SKY_ECOSYSTEM_CONTRACT.md 6, item 3):
--   1. THE BEAT. Wing-like parts (a Flight part hinged about the body's long axis)
--      follow an asymmetric stroke: a fast downstroke, a slower upstroke, a held
--      and partly raised pose while gliding, flared wider while landing or taking
--      off. The stroke runs on the flier's beat clock (FlightCore.GaitClock),
--      which counts beats of a part whose Rate is 1 Hz. Each part has its own
--      small phase and amplitude noise, so wings are never in lock-step.
--   2. THE BODY. Heave and pitch are locked to the beat (lift on the downstroke),
--      nose up in the landing flare. The driver adds them to the body's pose; the
--      flight itself (velocity == heading * speed) is untouched.
--   3. INERTIA. Every loose part (tail, neck, tendril, streamer) feels a force from
--      the body: drag backward, acceleration, climbing, turning. The force reaches
--      each segment one FollowTau later than the segment it hangs from
--      (follow-the-leader), and turns into a hinge angle by the torque rule
--      (axis . (lever x force)), so the same code swings a tail, a trailing
--      tendril and a drooping head the right way round.
--   4. LOOK. Idle-gait parts (neck, head) also lead into the turn and the climb.
--      Legs (Idle parts that hang below their hinge) are tucked at rest and
--      extend toward a landing and on the perch; they dangle a little while hovering.
--   5. PULSE. Jelly-like bells pulse in thrust bursts tied to acceleration and
--      speed (Gait Thrust); every pulsing part also kicks with acceleration.
--   6. AMBIENT. Everything else breathes on its own noise-modulated clock, always.
--   7. LIMITS. A part's sidecar `limit` [min, max] (radians) soft-clamps the final hinge
--      angle of a Flap part, so a tendril or a wing never swings through the body.
--   8. SPINE (serpents, eels). Segments are NOT hinge-chained sines: each sits on the
--      trail the head has travelled, with a travelling wave added perpendicular to the
--      path. The head itself sways with the wave (contract 7, item 4). See newSpine.

local CreatureMotionCore = {}

export type Body = {
	Time: number,
	Beat: number, -- the flier's beat clock
	Idle: number, -- 1 when perched
	Glide: number, -- 0 beating .. 1 coasting
	Flare: number,
	Yaw: number, -- -1..1, turning right positive
	Climb: number, -- -1..1
	Accel: number, -- -1..1
	Speed: number, -- 0..1 of cruise
	PrevPitch: number,
	ThrustPhase: number,
	ThrustAmp: number,
	Burst: number, -- 0..1 current pulse
	Drag: number,
	WingGate: number,
	Heave: number, -- studs, add to the body's height
	PitchOff: number, -- rad, nose up positive
	SDrag: number, -- Drag, Climb and Yaw low-passed by the class's InputTau (what loose parts feel)
	SClimb: number,
	SYaw: number,
}

export type Part = {
	Kind: string,
	Gait: string,
	Amp: number,
	Rate: number,
	PhaseCyc: number, -- cycles
	Lag: number,
	AxX: number,
	AxY: number,
	AxZ: number,
	EX: number, -- lever: the part's centre from its hinge
	EY: number,
	EZ: number,
	WingLike: boolean,
	LegLike: boolean,
	Seed: number,
	HasLimit: boolean,
	LimLo: number, -- the sidecar `limit` (radians), when HasLimit
	LimHi: number,
	Clock: number,
	FX: number, -- the force this segment feels (follow-the-leader)
	FY: number,
	FZ: number,
	-- outputs
	Angle: number,
	Scale: number,
	Flick: number,
}

local TWO_PI = math.pi * 2

local function clamp(v: number, lo: number, hi: number): number
	return math.max(lo, math.min(hi, v))
end

--- The wing stroke at phase `p` (cycles): -1 raised .. +1 lowered. The downstroke
--- takes the fraction `down` of the cycle (fast), the upstroke the rest (slow);
--- both ends are smooth.
function CreatureMotionCore.flapShape(p: number, down: number): number
	local u = p - math.floor(p)
	if u < down then
		return -math.cos(math.pi * u / down)
	end
	return math.cos(math.pi * (u - down) / (1 - down))
end

--- Rate of change of the stroke per cycle, scaled so the fastest point is 1.
function CreatureMotionCore.flapSlope(p: number, down: number): number
	local u = p - math.floor(p)
	local top = math.pi / math.min(down, 1 - down)
	if u < down then
		return (math.pi / down) * math.sin(math.pi * u / down) / top
	end
	return -(math.pi / (1 - down)) * math.sin(math.pi * (u - down) / (1 - down)) / top
end

--- A burst: a sharp contraction (0 -> 1 in a quarter cycle) and a slow recoil.
function CreatureMotionCore.burstShape(p: number): number
	local u = p - math.floor(p)
	if u < 0.25 then
		return math.sin(math.pi * 0.5 * u / 0.25)
	end
	local k = (u - 0.25) / 0.75
	return (1 - k) * (1 - k)
end

--- Smooth deterministic noise in -1..1 (two incommensurate waves).
function CreatureMotionCore.noise(t: number, seed: number): number
	return 0.6 * math.sin(TWO_PI * t * 0.37 + seed * 12.9898)
		+ 0.4 * math.sin(TWO_PI * t * 0.91 + seed * 78.233)
end

--- A first-order lag: `prev` moves toward `target` with time constant `tau`.
function CreatureMotionCore.follow(prev: number, target: number, dt: number, tau: number): number
	if tau <= 1e-6 then
		return target
	end
	return prev + (target - prev) * (1 - math.exp(-dt / tau))
end

--- Soft clamp of `x` into [lo, hi]: untouched inside, then smoothly saturating over
--- the last `knee` fraction (0..0.5) of the range at each end, never beyond it.
function CreatureMotionCore.softLimit(x: number, lo: number, hi: number, knee: number): number
	if hi < lo then
		lo, hi = hi, lo
	end
	local range = hi - lo
	if range <= 1e-9 then
		return lo
	end
	local m = range * clamp(knee, 0, 0.5)
	if m <= 1e-9 then
		return clamp(x, lo, hi)
	end
	if x > hi - m then
		return hi - m + m * (1 - math.exp(-(x - (hi - m)) / m))
	elseif x < lo + m then
		return lo + m - m * (1 - math.exp(-((lo + m) - x) / m))
	end
	return x
end

--- Hinge angle (per unit of force) that a force `F` on a part at lever `e` produces
--- about `axis`: axis . (e x F) / |e|.
function CreatureMotionCore.torque(
	ax: number,
	ay: number,
	az: number,
	ex: number,
	ey: number,
	ez: number,
	fx: number,
	fy: number,
	fz: number
): number
	local len = math.sqrt(ex * ex + ey * ey + ez * ez)
	if len < 1e-3 then
		return 0
	end
	local cx = ey * fz - ez * fy
	local cy = ez * fx - ex * fz
	local cz = ex * fy - ey * fx
	return (ax * cx + ay * cy + az * cz) / len
end

function CreatureMotionCore.newBody(): Body
	return {
		Time = 0,
		Beat = 0,
		Idle = 0,
		Glide = 0,
		Flare = 0,
		Yaw = 0,
		Climb = 0,
		Accel = 0,
		Speed = 0,
		PrevPitch = 0,
		ThrustPhase = 0,
		ThrustAmp = 0,
		Burst = 0,
		Drag = 0,
		WingGate = 1,
		Heave = 0,
		PitchOff = 0,
		SDrag = 0,
		SClimb = 0,
		SYaw = 0,
	}
end

--- A part's state from its sidecar row. `phase` and `lag` are radians (the
--- effective phase of a chained part already follows its parent's).
function CreatureMotionCore.newPart(
	kind: string,
	gait: string,
	amp: number,
	rate: number,
	phase: number,
	lag: number,
	axis: { number },
	offset: { number },
	hinge: { number },
	seed: number,
	limit: { number }?
): Part
	local ax, ay, az = axis[1], axis[2], axis[3]
	local len = math.sqrt(ax * ax + ay * ay + az * az)
	if len < 1e-3 then
		ax, ay, az, len = 1, 0, 0, 1
	end
	ax, ay, az = ax / len, ay / len, az / len
	local ex, ey, ez = offset[1] - hinge[1], offset[2] - hinge[2], offset[3] - hinge[3]
	local wing = kind == "Flap" and gait == "Flight" and math.abs(ax) >= 0.6
	-- a leg: an Idle part that swings about the vertical and hangs below its hinge
	local leg = kind == "Flap"
		and gait == "Idle"
		and math.abs(ay) >= 0.7
		and ey < -0.5 * math.abs(ex)
	return {
		Kind = kind,
		Gait = gait,
		Amp = amp,
		Rate = rate,
		PhaseCyc = phase / TWO_PI,
		Lag = lag,
		AxX = ax,
		AxY = ay,
		AxZ = az,
		EX = ex,
		EY = ey,
		EZ = ez,
		WingLike = wing,
		LegLike = leg,
		Seed = seed,
		HasLimit = limit ~= nil and #limit >= 2,
		LimLo = if limit then math.min(limit[1], limit[2] or limit[1]) else 0,
		LimHi = if limit then math.max(limit[1], limit[2] or limit[1]) else 0,
		Clock = 0,
		FX = 0,
		FY = 0,
		FZ = 0,
		Angle = 0,
		Scale = 1,
		Flick = 0,
	}
end

--- Body-level update from a flier (FlightCore.Flier) after FlightCore.tick and
--- FlightCore.gait. `refRate` is the beat rate of the creature's main wing (0 if
--- it has none); `radius` its body radius; `mc` the class motion profile and
--- `motion` the whole Motion table.
function CreatureMotionCore.updateBody(
	b: Body,
	f: any,
	dt: number,
	mc: any,
	motion: any,
	refRate: number
)
	b.Time += dt
	b.Beat = f.GaitClock
	b.Idle = f.Idle
	b.Glide = f.GlideBlend
	b.Flare = f.Flare
	b.Yaw = f.BankNorm
	b.Accel = f.AccelN
	local cruise = math.max(f.Band.SMax, 1e-6)
	b.Speed = clamp(f.Speed / cruise, 0, 1.5)
	local pitchRate = if dt > 1e-6 then (f.Pitch - b.PrevPitch) / dt else 0
	b.PrevPitch = f.Pitch
	b.Climb = clamp(
		(pitchRate / motion.PitchRef) * 0.7
			+ (math.sin(f.Pitch) / math.max(f.Prof.MaxPitch, 1e-3)) * 0.3,
		-1,
		1
	)
	b.WingGate = (1 - b.Idle) * (1 + (mc.GlideHold - 1) * b.Glide)
	-- thrust bursts: faster and stronger with speed and acceleration
	local accelPos = math.max(0, b.Accel)
	b.ThrustPhase += dt * mc.ThrustHz * (0.4 + b.Speed * 0.8 + accelPos * 1.5)
	b.ThrustAmp = clamp(0.35 + 0.65 * clamp(accelPos * 2 + b.Speed * 0.5, 0, 1), 0, 1)
	b.Burst = CreatureMotionCore.burstShape(b.ThrustPhase)
	b.Drag = motion.DragSpeed * b.Speed
		+ b.Accel * 0.8
		+ (if mc.ThrustGain > 0 then b.Burst * b.ThrustAmp * (mc.BurstDrag or 0.6) else 0)
	-- what loose parts feel is low-passed (a colossal's tendrils never whip)
	local tau = mc.InputTau or 0
	b.SDrag = CreatureMotionCore.follow(b.SDrag, b.Drag, dt, tau)
	b.SClimb = CreatureMotionCore.follow(b.SClimb, b.Climb, dt, tau)
	b.SYaw = CreatureMotionCore.follow(b.SYaw, b.Yaw, dt, tau)
	-- heave and pitch, locked to the beat
	if refRate > 0 then
		local p = b.Beat * refRate
		local heaveMax = math.min(mc.HeaveScale * f.Radius, mc.HeaveMax)
		b.Heave = heaveMax * CreatureMotionCore.flapShape(p, mc.DownFrac) * b.WingGate
		b.PitchOff = mc.PitchBeat * CreatureMotionCore.flapSlope(p, mc.DownFrac) * b.WingGate
	else
		b.Heave, b.PitchOff = 0, 0
	end
	b.PitchOff += mc.FlareAmp * 0.6 * b.Flare
end

--- Advance one part (parents first). `parent` is the part it is chained to, if any.
--- Sets Angle (Flap), Scale (Pulse) and Flick (Flicker).
function CreatureMotionCore.stepPart(
	s: Part,
	b: Body,
	parent: Part?,
	dt: number,
	mc: any,
	motion: any
)
	local kind, gait = s.Kind, s.Gait
	if kind == "Spin" then
		return
	end
	-- a pulse with no amplitude is static: a rigid shell never breathes or kicks
	if kind == "Pulse" and s.Amp <= 0 then
		s.Scale = 1
		return
	end
	local idleGate = math.max(b.Idle, mc.IdleInFlight)
	local gate = 1.0
	if gait == "Flight" then
		gate = b.WingGate
	elseif gait == "Idle" then
		gate = idleGate
	end
	local noiseA = 1 + mc.NoiseAmp * CreatureMotionCore.noise(b.Time * mc.NoiseHz, s.Seed)
	local wobble = mc.NoiseAmp
		* 0.15
		* CreatureMotionCore.noise(b.Time * mc.NoiseHz * 1.7, s.Seed + 3)
	-- ambient clock, never exactly regular
	local loose = kind == "Flap" and not s.WingLike
	local looseRate = if loose then (mc.LooseRate or 1) else 1
	s.Clock += dt * s.Rate * mc.RateScale * looseRate * (1 + 0.3 * CreatureMotionCore.noise(
		b.Time * 0.2,
		s.Seed + 7
	))
	local amp = s.Amp * mc.AmpScale * (if loose then (mc.LooseAmp or 1) else 1)

	if kind == "Flap" then
		-- the force this segment feels: the body's, or its parent's, one tau later
		local rx, ry, rz = b.Drag, -b.Climb, b.Yaw
		if (mc.InputTau or 0) > 0 then
			rx, ry, rz = b.SDrag, -b.SClimb, b.SYaw -- low-passed by updateBody
		end
		if parent then
			rx, ry, rz = parent.FX, parent.FY, parent.FZ
		end
		local tau = mc.FollowTau * (1 + s.Lag)
		s.FX = CreatureMotionCore.follow(s.FX, rx, dt, tau)
		s.FY = CreatureMotionCore.follow(s.FY, ry, dt, tau)
		s.FZ = CreatureMotionCore.follow(s.FZ, rz, dt, tau)

		local angle = 0.0
		if s.WingLike then
			local stroke =
				CreatureMotionCore.flapShape(b.Beat * s.Rate + s.PhaseCyc + wobble, mc.DownFrac)
			-- lift costs effort: the downstroke is driven harder than the recovery
			if stroke > 0 then
				stroke *= mc.DownPower or 1
			end
			local flare = 1 + mc.FlareAmp * b.Flare
			local held = mc.GlideBias * b.Glide + mc.ClimbBias * math.max(0, b.Climb)
			angle = motion.StrokeSign
				* amp
				* ((stroke * noiseA * flare * b.WingGate) - held * (1 - b.Idle))
		elseif gait == "Turn" then
			angle = amp * s.FZ
		else
			local wave
			if gait == "Flight" then
				wave = math.sin(TWO_PI * (b.Beat * s.Rate * looseRate + s.PhaseCyc + wobble))
			else
				wave = math.sin(TWO_PI * (s.Clock + s.PhaseCyc))
			end
			angle = amp * gate * wave * noiseA
			local ig = mc.InertiaGain * (if gait == "Idle" then 0.4 else 1) -- a neck mostly looks, it hardly trails
			local fx, fy, fz = s.FX * ig, s.FY * ig, s.FZ * ig
			angle += amp * clamp(
				CreatureMotionCore.torque(s.AxX, s.AxY, s.AxZ, s.EX, s.EY, s.EZ, fx, fy, fz),
				-(mc.InertiaMax or 1.5),
				mc.InertiaMax or 1.5
			)
			if gait == "Idle" then
				-- lead into the turn and the climb
				local look = CreatureMotionCore.torque(
					s.AxX,
					s.AxY,
					s.AxZ,
					s.EX,
					s.EY,
					s.EZ,
					0,
					b.Climb * 0.5,
					-b.Yaw
				)
				angle += amp * mc.LookGain * clamp(look, -1.5, 1.5) * idleGate
				if s.LegLike then
					-- tucked at rest, forward (negative) toward a landing and on the perch
					angle -= amp * mc.LegExtend * (math.max(b.Flare, b.Idle) + mc.HoverDangle * (1 - clamp(
						b.Speed,
						0,
						1
					)) * (1 - b.Idle))
				end
			end
		end
		if s.HasLimit then
			angle = CreatureMotionCore.softLimit(angle, s.LimLo, s.LimHi, motion.LimitKnee or 0.25)
		end
		s.Angle = angle
	elseif kind == "Pulse" then
		local breath = math.sin(TWO_PI * (s.Clock + s.PhaseCyc))
		local accelPos = math.max(0, b.Accel)
		local v = breath * gate * noiseA + mc.AccelKick * accelPos
		if gait == "Thrust" or (gait == "Flight" and mc.ThrustGain > 0) then
			v = breath * 0.4 + mc.ThrustGain * b.ThrustAmp * b.Burst + mc.AccelKick * accelPos
		end
		s.Scale = 1 + s.Amp * mc.AmpScale * v
	elseif kind == "Flicker" then
		local wave = math.sin(TWO_PI * (s.Clock + s.PhaseCyc))
		local g = if gait == "Flight" then (1 - b.Idle) else gate
		s.Flick = g * (0.5 + 0.5 * wave)
	end
end

-- ------------------------------------------------------------------ SPINE
-- Serpent / eel locomotion (docs/design/SKY_ECOSYSTEM_CONTRACT.md 7, item 4).
-- The body root (the head) is the leader. A TRAIL of the head's positions,
-- sampled by distance, is the path every segment follows; segment i sits at arc
-- length S[i] from the head along that path AFTER a travelling wave has been
-- added perpendicular to it (amplitude growing toward the tail). The head is on
-- the wave too, so it sways and yaws or pitches with the body. Because the arc
-- length is measured along the displaced curve, the spacing between segments
-- never changes (nothing opens at a bend) and the tail follows turn arcs.

export type Trail = {
	Step: number, -- a point is stored each time the head has moved this far
	Max: number, -- total length kept
	X: { number }, -- stored points, newest first
	Y: { number },
	Z: { number },
	Length: number, -- path length stored
}

export type Spine = {
	N: number, -- segments (the head is extra)
	S: { number }, -- arc length of each segment from the head
	Length: number, -- S of the last segment
	Lambda: number, -- wavelength, studs
	Amp: number, -- tail amplitude, studs
	Rate: number, -- Hz
	Vertical: boolean, -- wave in the vertical plane (else lateral)
	HeadAmp: number, -- fraction of Amp at the head
	Trail: Trail,
	-- outputs: index 1 is the head, index i + 1 segment i
	PX: { number },
	PY: { number },
	PZ: { number },
	TX: { number }, -- unit tangent, pointing the way the creature travels
	TY: { number },
	TZ: { number },
}

--- A spine from the arc length of each segment (root first), the wave
--- (wavelength and tail amplitude in studs, rate in Hz), the plane and the head's
--- share of the amplitude. `stepsPerWave` sets how finely the trail is sampled.
function CreatureMotionCore.newSpine(
	arcs: { number },
	wavelength: number,
	amp: number,
	rate: number,
	vertical: boolean,
	headAmp: number,
	stepsPerWave: number,
	margin: number
): Spine
	local last = 0.0
	local minGap = math.huge
	for i, a in arcs do
		last = math.max(last, a)
		minGap = math.min(minGap, a - (arcs[i - 1] or 0))
	end
	local step = math.max(math.min(wavelength / math.max(stepsPerWave, 4), minGap * 0.5), 1)
	local sp: Spine = {
		N = #arcs,
		S = table.clone(arcs),
		Length = last,
		Lambda = math.max(wavelength, 1),
		Amp = amp,
		Rate = rate,
		Vertical = vertical,
		HeadAmp = headAmp,
		Trail = {
			Step = step,
			Max = (last + amp * 2) * math.max(margin, 1) + step * 2,
			X = {},
			Y = {},
			Z = {},
			Length = 0,
		},
		PX = {},
		PY = {},
		PZ = {},
		TX = {},
		TY = {},
		TZ = {},
	}
	for i = 1, #arcs + 1 do
		sp.PX[i], sp.PY[i], sp.PZ[i] = 0, 0, 0
		sp.TX[i], sp.TY[i], sp.TZ[i] = 1, 0, 0
	end
	return sp
end

--- Lay the trail out straight behind the head, which stands at (hx, hy, hz)
--- heading (dx, dy, dz) (a unit vector): where a creature begins or has just
--- arrived with nothing behind it yet.
function CreatureMotionCore.seedTrail(
	tr: Trail,
	hx: number,
	hy: number,
	hz: number,
	dx: number,
	dy: number,
	dz: number
)
	table.clear(tr.X)
	table.clear(tr.Y)
	table.clear(tr.Z)
	local n = math.ceil(tr.Max / tr.Step)
	for k = 1, n do
		tr.X[k], tr.Y[k], tr.Z[k] =
			hx - dx * tr.Step * k, hy - dy * tr.Step * k, hz - dz * tr.Step * k
	end
	tr.Length = n * tr.Step
end

--- Record the head's position. Returns false when the head has jumped further
--- than the whole trail (it was moved, not flown): the caller seeds it afresh.
function CreatureMotionCore.pushTrail(tr: Trail, hx: number, hy: number, hz: number): boolean
	local n = #tr.X
	if n == 0 then
		tr.X[1], tr.Y[1], tr.Z[1] = hx, hy, hz
		return true
	end
	local dx, dy, dz = hx - tr.X[1], hy - tr.Y[1], hz - tr.Z[1]
	local d = math.sqrt(dx * dx + dy * dy + dz * dz)
	if d > tr.Max then
		return false
	end
	if d >= tr.Step then
		-- a long step is stored as the points a straight run would have left
		local k = math.floor(d / tr.Step)
		local ux, uy, uz = dx / d, dy / d, dz / d
		for _ = 1, k do
			table.insert(tr.X, 1, tr.X[1] + ux * tr.Step)
			table.insert(tr.Y, 1, tr.Y[1] + uy * tr.Step)
			table.insert(tr.Z, 1, tr.Z[1] + uz * tr.Step)
		end
		tr.Length += tr.Step * k
		-- drop what is older than the trail needs
		local keep = math.ceil(tr.Max / tr.Step)
		while #tr.X > keep do
			table.remove(tr.X)
			table.remove(tr.Y)
			table.remove(tr.Z)
			tr.Length -= tr.Step
		end
	end
	return true
end

local function unit(
	x: number,
	y: number,
	z: number,
	fx: number,
	fy: number,
	fz: number
): (number, number, number)
	local m = math.sqrt(x * x + y * y + z * z)
	if m < 1e-9 then
		return fx, fy, fz
	end
	return x / m, y / m, z / m
end

--- Place the head and every segment for time `t`. The head stands at (hx, hy, hz)
--- (its unswayed path position). Results are written to the spine's PX.. TZ arrays.
function CreatureMotionCore.solveSpine(sp: Spine, hx: number, hy: number, hz: number, t: number)
	local tr = sp.Trail
	-- the raw path: the head, then the stored trail up to what is needed
	local px, py, pz, u = { hx }, { hy }, { hz }, { 0.0 }
	local need = sp.Length * 1.25 + sp.Amp * 2 + tr.Step
	for k = 1, #tr.X do
		local n = #px
		local dx, dy, dz = tr.X[k] - px[n], tr.Y[k] - py[n], tr.Z[k] - pz[n]
		local d = math.sqrt(dx * dx + dy * dy + dz * dz)
		if d < 1e-6 then
			continue
		end
		px[n + 1], py[n + 1], pz[n + 1], u[n + 1] = tr.X[k], tr.Y[k], tr.Z[k], u[n] + d
		if u[n + 1] >= need then
			break
		end
	end
	local n = #px
	if n < 2 then
		-- nothing behind the head yet: a straight tail the way the last tangent pointed
		px[2], py[2], pz[2], u[2] =
			hx - sp.TX[1] * need, hy - sp.TY[1] * need, hz - sp.TZ[1] * need, need
		n = 2
	end
	-- tangents of the raw path (pointing the way the head went) and the wave's normals
	local qx, qy, qz = {}, {}, {}
	local ang = TWO_PI * sp.Rate * t
	local prevNx, prevNy, prevNz = 0.0, 0.0, 1.0
	for k = 1, n do
		local a, b = math.max(k - 1, 1), math.min(k + 1, n)
		local tx, ty, tz =
			unit(px[a] - px[b], py[a] - py[b], pz[a] - pz[b], sp.TX[1], sp.TY[1], sp.TZ[1])
		-- lateral: horizontal and perpendicular to the path; vertical: perpendicular to both
		local h = math.sqrt(tx * tx + tz * tz)
		local lx, ly, lz
		if h < 1e-4 then
			lx, ly, lz = prevNx, prevNy, prevNz
		else
			lx, ly, lz = tz / h, 0, -tx / h
		end
		local nx, ny, nz = lx, ly, lz
		if sp.Vertical then
			nx, ny, nz = ty * lz - tz * ly, tz * lx - tx * lz, tx * ly - ty * lx
			if ny < 0 then
				nx, ny, nz = -nx, -ny, -nz
			end
		end
		prevNx, prevNy, prevNz = lx, ly, lz
		local env = sp.HeadAmp + (1 - sp.HeadAmp) * clamp(u[k] / math.max(sp.Length, 1e-6), 0, 1)
		local w = sp.Amp * env * math.sin(ang - TWO_PI * u[k] / sp.Lambda)
		qx[k], qy[k], qz[k] = px[k] + nx * w, py[k] + ny * w, pz[k] + nz * w
	end
	-- arc length along the DISPLACED curve, and its tangents
	local d = { 0.0 }
	for k = 2, n do
		d[k] = d[k - 1]
			+ math.sqrt((qx[k] - qx[k - 1]) ^ 2 + (qy[k] - qy[k - 1]) ^ 2 + (qz[k] - qz[k - 1]) ^ 2)
	end
	local ux, uy, uz = {}, {}, {}
	for k = 1, n do
		local a, b = math.max(k - 1, 1), math.min(k + 1, n)
		ux[k], uy[k], uz[k] =
			unit(qx[a] - qx[b], qy[a] - qy[b], qz[a] - qz[b], sp.TX[1], sp.TY[1], sp.TZ[1])
	end
	sp.PX[1], sp.PY[1], sp.PZ[1] = qx[1], qy[1], qz[1]
	sp.TX[1], sp.TY[1], sp.TZ[1] = ux[1], uy[1], uz[1]
	local k = 1
	for i = 1, sp.N do
		local s = sp.S[i]
		while k < n - 1 and d[k + 1] < s do
			k += 1
		end
		local span = d[k + 1] - d[k]
		local f = if span > 1e-9 then clamp((s - d[k]) / span, 0, 1) else 0
		local o = i + 1
		sp.PX[o] = qx[k] + (qx[k + 1] - qx[k]) * f
		sp.PY[o] = qy[k] + (qy[k + 1] - qy[k]) * f
		sp.PZ[o] = qz[k] + (qz[k + 1] - qz[k]) * f
		sp.TX[o], sp.TY[o], sp.TZ[o] = unit(
			ux[k] + (ux[k + 1] - ux[k]) * f,
			uy[k] + (uy[k + 1] - uy[k]) * f,
			uz[k] + (uz[k + 1] - uz[k]) * f,
			ux[k],
			uy[k],
			uz[k]
		)
	end
end

return CreatureMotionCore
