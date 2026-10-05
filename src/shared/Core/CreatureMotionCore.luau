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
	seed: number
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
		+ (if mc.ThrustGain > 0 then b.Burst * b.ThrustAmp * 0.6 else 0)
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
	s.Clock += dt * s.Rate * mc.RateScale * (1 + 0.3 * CreatureMotionCore.noise(
		b.Time * 0.2,
		s.Seed + 7
	))
	local amp = s.Amp * mc.AmpScale

	if kind == "Flap" then
		-- the force this segment feels: the body's, or its parent's, one tau later
		local rx, ry, rz = b.Drag, -b.Climb, b.Yaw
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
				wave = math.sin(TWO_PI * (b.Beat * s.Rate + s.PhaseCyc + wobble))
			else
				wave = math.sin(TWO_PI * (s.Clock + s.PhaseCyc))
			end
			angle = amp * gate * wave * noiseA
			local ig = mc.InertiaGain * (if gait == "Idle" then 0.4 else 1) -- a neck mostly looks, it hardly trails
			local fx, fy, fz = s.FX * ig, s.FY * ig, s.FZ * ig
			angle += amp * clamp(
				CreatureMotionCore.torque(s.AxX, s.AxY, s.AxZ, s.EX, s.EY, s.EZ, fx, fy, fz),
				-1.5,
				1.5
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

return CreatureMotionCore
