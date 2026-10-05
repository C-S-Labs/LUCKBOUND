--!strict
-- The pure half of the expedition rifts (build spec §7.8): how a rift moves.
-- RiftRig builds the parts and RiftController poses them every frame; this
-- file answers "how open is it, where has each fragment drifted to" and
-- nothing else. PURE: no Roblox types, so every curve is tested headlessly.
--
-- THE TWO RULES THE MOTION KEEPS
--   1. The lane in front of and behind the tear is EMPTY. Fragments only ever
--      move outward from their home and back (`fragmentOffset`), and fly in
--      from the sides (`gatherOffset`), so no frame puts rock in the path.
--   2. The tear's tip stays on the deck. The breath swells width and
--      thickness only; only the materialise opens the tear in height, and it
--      ends exactly at full height.

local RiftCore = {}

export type Phase = "SEALED" | "MATERIALISING" | "OPEN"

export type Materialise = {
	Seeds: number, -- 0..1: cracks glow, motes gather
	Gather: number, -- 0..1: fragments have flown in
	Height: number, -- 0..1: how far the tear has split open, tall
	Width: number, -- 0..1: ...and wide (lags the height, so it splits like a slit)
	Alpha: number, -- 0..1: how visible the shells are
	Bloom: number, -- 0..1..0: the one bright pulse
}

--- Smoothstep, clamped.
function RiftCore.ease(x: number): number
	local c = math.clamp(x, 0, 1)
	return c * c * (3 - 2 * c)
end

--- Progress through the window [from, to] (fractions of `seconds`), eased.
function RiftCore.window(elapsed: number, seconds: number, from: number, to: number): number
	if seconds <= 0 or to <= from then
		return if elapsed >= seconds then 1 else 0
	end
	return RiftCore.ease((elapsed / seconds - from) / (to - from))
end

--- What state a rift is in. The ENTRANCE is always open. The EXIT is sealed
--- until the server stamps OpenedAt (server time), then materialises, then is
--- open: derived from elapsed time, so a player who streams in late sees an
--- open rift already open, not opening.
function RiftCore.phaseFor(kind: string, openedAt: number?, now: number, cfg: any): (Phase, number)
	if kind == "ENTRANCE" then
		return "OPEN", 0
	end
	if openedAt == nil then
		return "SEALED", 0
	end
	local elapsed = math.max(0, now - openedAt)
	if elapsed >= cfg.MaterialiseSeconds then
		return "OPEN", elapsed
	end
	return "MATERIALISING", elapsed
end

--- Every 0..1 the materialise sequence needs, `elapsed` seconds in.
function RiftCore.materialise(elapsed: number, cfg: any): Materialise
	local secs = cfg.MaterialiseSeconds
	local p = cfg.Phases
	local split = RiftCore.window(elapsed, secs, p.Split[1], p.Split[2])
	local bloomT = RiftCore.window(elapsed, secs, p.Bloom[1], p.Bloom[2])
	return {
		Seeds = RiftCore.window(elapsed, secs, p.Seeds[1], p.Seeds[2]),
		Gather = RiftCore.window(elapsed, secs, p.Gather[1], p.Gather[2]),
		-- Tall first, wide a beat later: a slit before a tear.
		Height = split ^ 0.6,
		Width = (split ^ 0.6) * RiftCore.ease((split - 0.25) / 0.75),
		Alpha = split,
		-- One sine hump over the bloom window: 0 -> 1 -> 0.
		Bloom = math.sin(math.pi * bloomT),
	}
end

--- The slow swell of a rift's shells, a multiplier near 1. `phase` (radians)
--- de-syncs the layers so the tear ripples instead of pulsing as one.
function RiftCore.breath(t: number, phase: number, cfg: any): number
	return 1 + cfg.BreathAmount * math.sin(2 * math.pi * t / cfg.BreathSeconds + phase)
end

--- A fragment's drift from home, in the rift's own frame: (across, up).
--- `side` is +1 or -1, which side of the tear its home is on. The across
--- component is side * (>= 0): OUTWARD from the tear or zero, never toward
--- the lane in front of it. Tested for every t.
function RiftCore.fragmentOffset(t: number, index: number, side: number, cfg: any): (number, number)
	local w = cfg.FragmentSpeed
	local a = w * t + index * 1.7
	local across = side * cfg.FragmentDriftOut * (0.5 + 0.5 * math.sin(a))
	local up = cfg.FragmentBob * math.sin(a * 0.7 + index)
	return across, up
end

--- A fragment's tumble about its own centre (radians about X, Y, Z): a slow
--- wobble inside +/- cfg.FragmentTumble, different per fragment. Rock and gem
--- turn TOGETHER about the rock's centre, so the crystal stays set in it.
function RiftCore.fragmentTumble(t: number, index: number, cfg: any): (number, number, number)
	local a = cfg.FragmentSpeed * t * 0.6 + index * 2.3
	local k = cfg.FragmentTumble
	return k * math.sin(a), k * math.sin(a * 1.3 + 1.1), k * 0.6 * math.sin(a * 0.8 + 2.4)
end

--- Where a fragment is while flying in, relative to home: (across, up).
--- Starts far out to its own side and above, arrives exactly at (0, 0).
function RiftCore.gatherOffset(gather: number, side: number, cfg: any): (number, number)
	local remaining = 1 - RiftCore.ease(gather)
	return side * cfg.GatherDistance * 0.85 * remaining, cfg.GatherDistance * 0.5 * remaining
end

--- The point light: idle brightness, lifted by the bloom pulse.
function RiftCore.lightBrightness(bloom: number, cfg: any): number
	return cfg.IdleBrightness + (cfg.BloomBrightness - cfg.IdleBrightness) * bloom
end

--- A shell's transparency: its resting value, opened up by `alpha`.
function RiftCore.shellTransparency(rest: number, alpha: number): number
	return 1 - (1 - rest) * math.clamp(alpha, 0, 1)
end

return RiftCore
